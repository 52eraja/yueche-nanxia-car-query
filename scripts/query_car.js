/**
 * 粤车南下来往港澳车辆备案信息查询 - Playwright 版本 v1.0
 * 使用 Playwright 模拟真实浏览器操作
 * 
 * 用法:
 *   node query_car.js 车牌号
 *   node query_car.js 车牌号 --json
 */

const { chromium } = require('/opt/data/html-video/node_modules/.pnpm/playwright@1.60.0/node_modules/playwright');

const args = process.argv.slice(2);
const jsonOutput = args.includes('--json');
const plate = args.find(a => !a.startsWith('--'));

if (!plate) {
  console.error('用法: node query_car.js 车牌号 [--json]');
  process.exit(1);
}

async function queryCar(plateNum) {
  const result = {
    plate: plateNum,
    source: 'szcport (Playwright)',
    registered: null,
    data: null,
  };

  const browser = await chromium.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });

  const context = await browser.newContext({
    userAgent: 'Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
    viewport: { width: 400, height: 800 },
  });

  const page = await context.newPage();

  try {
    console.error(`[INFO] 正在查询 ${plateNum} ...`);
    
    // 直接 POST 到查询接口
    await page.goto('https://exp.szcport.cn:8282/NEWabl/carInfoQuery.action', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      postData: `queryBean1.queryInput1=${encodeURIComponent(plateNum)}&id=${encodeURIComponent(plateNum)}`,
      timeout: 30000,
    });

    const html = await page.content();
    
    // 提取返回码（注意 HTML 中可能有换行）
    const codeMatch = html.match(/<span id="hidden_pageindex">\s*(-?\d+)\s*<\/span>/);
    const returnCode = codeMatch ? codeMatch[1] : null;
    result.returnCode = returnCode;

    // 提取表格数据
    const tdRegex = /<td[^>]*>([\s\S]*?)<\/td>/g;
    const cells = [];
    let tdMatch;
    while ((tdMatch = tdRegex.exec(html)) !== null) {
      const clean = tdMatch[1].replace(/<[^>]+>/g, '').trim();
      if (clean && clean !== '内地/香港车牌号码') {
        cells.push(clean);
      }
    }

    const noData = html.includes('无此数据');

    console.error(`[INFO] 返回码: ${returnCode}, 数据单元格: ${cells.length}`);

    if (returnCode === '0' && cells.length > 0) {
      result.registered = true;
      result.data = { raw_cells: cells };
      for (const cell of cells) {
        if (/^\d{8,}$/.test(cell)) result.data['备案编号'] = cell;
        else if (/粤/.test(cell) || /^[A-Z]{2}\d/.test(cell)) result.data['车牌号码'] = cell;
        else if (/^\d{4}-\d{2}-\d{2}/.test(cell)) result.data['备案有效期'] = cell;
      }
    } else if (returnCode === '1' || (returnCode === '0' && cells.length === 0) || noData) {
      result.registered = false;
    } else {
      // 等待后重试
      console.error('[INFO] 等待 2 秒后重试...');
      await page.waitForTimeout(2000);
      const html2 = await page.content();
      const codeMatch2 = html2.match(/<span id="hidden_pageindex">\s*(-?\d+)\s*<\/span>/);
      const returnCode2 = codeMatch2 ? codeMatch2[1] : null;
      result.returnCode = returnCode2 || returnCode;
      
      if (returnCode2 === '0') {
        const tdRegex2 = /<td[^>]*>([\s\S]*?)<\/td>/g;
        const cells2 = [];
        let tdMatch2;
        while ((tdMatch2 = tdRegex2.exec(html2)) !== null) {
          const clean = tdMatch2[1].replace(/<[^>]+>/g, '').trim();
          if (clean && clean !== '内地/香港车牌号码') cells2.push(clean);
        }
        if (cells2.length > 0) {
          result.registered = true;
          result.data = { raw_cells: cells2, note: '等待后获取到数据' };
        }
      }
    }

  } catch (error) {
    result.error = error.message;
    console.error(`[ERROR] ${error.message}`);
  } finally {
    await browser.close();
  }

  return result;
}

async function main() {
  const queryPlate = plate.replace(/[·\-\s]/g, '');
  const result = await queryCar(queryPlate);

  if (jsonOutput) {
    console.log(JSON.stringify(result, null, 2));
  } else {
    console.log(`\n📋 车牌：${result.plate}`);
    console.log(`🔍 数据源：深圳电子口岸（Playwright）`);
    console.log(`📊 返回码：${result.returnCode}`);
    
    if (result.error) {
      console.log(`\n❌ 查询出错：${result.error}`);
    } else if (result.registered === true && result.data) {
      console.log(`\n✅ 已备案`);
      for (const [k, v] of Object.entries(result.data)) {
        if (k !== 'raw_cells') console.log(`  ${k}：${v}`);
      }
    } else if (result.registered === false) {
      console.log(`\n❌ 未备案（无此数据）`);
    } else {
      console.log(`\n⚠️ 未知状态`);
    }
  }
}

main().catch(err => {
  console.error(`[FATAL] ${err.message}`);
  process.exit(1);
});
