const { chromium } = require('/opt/data/html-video/node_modules/.pnpm/playwright@1.60.0/node_modules/playwright');

async function debug() {
  const browser = await chromium.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });
  const context = await browser.newContext({
    userAgent: 'Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36',
    viewport: { width: 400, height: 800 },
  });
  const page = await context.new_page();

  // 测试1: 直接 POST
  console.error('[TEST 1] POST carInfoQuery.action');
  const resp = await page.goto('https://exp.szcport.cn:8282/NEWabl/carInfoQuery.action', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    postData: 'queryBean1.queryInput1=FR497&id=FR497',
    timeout: 30000,
  });
  console.error('  Status:', resp ? resp.status() : 'null');
  
  const html = await page.content();
  const text = await page.evaluate(() => document.body.innerText);
  console.error('  Text:', text.substring(0, 300));
  
  const codeMatch = html.match(/<span id="hidden_pageindex">(-?\d+)<\/span>/);
  console.error('  PageIndex:', codeMatch ? codeMatch[1] : 'not found');
  
  // 保存完整 HTML
  const fs = require('fs');
  fs.writeFileSync('/tmp/debug_page.html', html);
  console.error('  HTML saved to /tmp/debug_page.html');

  // 测试2: 用 curl 对比
  console.error('\n[TEST 2] 尝试不同车牌格式');
  for (const plate of ['FR497', '粤FR497', '粤ZFR497']) {
    await page.goto('https://exp.szcport.cn:8282/NEWabl/carInfoQuery.action', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      postData: `queryBean1.queryInput1=${encodeURIComponent(plate)}&id=${encodeURIComponent(plate)}`,
      timeout: 30000,
    });
    const html2 = await page.content();
    const code2 = html2.match(/<span id="hidden_pageindex">(-?\d+)<\/span>/);
    const text2 = await page.evaluate(() => document.body.innerText);
    console.error(`  ${plate} -> code=${code2 ? code2[1] : 'null'}, text=${text2.substring(0, 100)}`);
  }

  await browser.close();
}

debug().catch(err => { console.error('[FATAL]', err.message); process.exit(1); });
