/**
 * 调试脚本 - 截图查看页面内容
 */
const { chromium } = require('/opt/data/html-video/node_modules/.pnpm/playwright@1.60.0/node_modules/playwright');

async function debug() {
  const browser = await chromium.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });

  const context = await browser.newContext({
    userAgent: 'Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
    viewport: { width: 400, height: 800 },
  });

  const page = await context.newPage();

  // 方式1: 直接 POST
  console.error('[TEST 1] POST carInfoQuery.action');
  await page.goto('https://exp.szcport.cn:8282/NEWabl/carInfoQuery.action', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    postData: 'queryBean1.queryInput1=粤ADU0650&id=粤ADU0650',
    timeout: 30000,
  });
  await page.screenshot({ path: '/tmp/debug_post.png' });
  
  const html1 = await page.content();
  const code1 = html1.match(/<span id="hidden_pageindex">(-?\d+)<\/span>/);
  console.error(`  Return code: ${code1 ? code1[1] : 'null'}`);
  console.error(`  Page title: ${await page.title()}`);
  console.error(`  URL: ${page.url()}`);
  
  // 提取页面文本
  const text1 = await page.evaluate(() => document.body.innerText);
  console.error(`  Page text (first 500): ${text1.substring(0, 500)}`);

  // 方式2: GET 页面 + 点击查询按钮
  console.error('\n[TEST 2] GET 页面 + 点击查询');
  await page.goto('https://exp.szcport.cn:8282/NEWabl/carInfoQuery.action', {
    timeout: 30000,
  });
  
  // 填写表单
  await page.fill('#inputtext', '粤ADU0650');
  await page.fill('#openId', '粤ADU0650');
  
  // 点击查询按钮
  await page.click('#btn_query');
  await page.waitForTimeout(3000);
  
  await page.screenshot({ path: '/tmp/debug_click.png' });
  
  const html2 = await page.content();
  const code2 = html2.match(/<span id="hidden_pageindex">(-?\d+)<\/span>/);
  console.error(`  Return code: ${code2 ? code2[1] : 'null'}`);
  
  const text2 = await page.evaluate(() => document.body.innerText);
  console.error(`  Page text (first 500): ${text2.substring(0, 500)}`);

  // 方式3: 试试 carInfoQuery1.action
  console.error('\n[TEST 3] POST carInfoQuery1.action');
  await page.goto('https://exp.szcport.cn:8282/NEWabl/carInfoQuery1.action', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    postData: 'queryBean1.queryInput1=粤ADU0650&id=粤ADU0650',
    timeout: 30000,
  });
  await page.screenshot({ path: '/tmp/debug_query1.png' });
  
  const html3 = await page.content();
  const code3 = html3.match(/<span id="hidden_pageindex">(-?\d+)<\/span>/);
  console.error(`  Return code: ${code3 ? code3[1] : 'null'}`);
  
  const text3 = await page.evaluate(() => document.body.innerText);
  console.error(`  Page text (first 500): ${text3.substring(0, 500)}`);

  await browser.close();
}

debug().catch(err => {
  console.error(`[FATAL] ${err.message}`);
  process.exit(1);
});
