import {test,expect} from '@playwright/test';
import {resolve} from 'node:path';
import {pathToFileURL} from 'node:url';

const pairs=['EURUSD','GBPUSD','USDJPY','USDCHF','AUDUSD','EURGBP'];

test('public homepage shows a genuine 5-decimal absolute change and switches live chart pairs',async({page})=>{
  await page.route('https://biquote.io/api/**',async route=>{
    const url=new URL(route.request().url());
    let data:unknown;
    if(url.pathname.endsWith('/ohlc')){
      const jpy=url.pathname.includes('/USDJPY/');
      data={bars:[{isOpen:true,open:jpy?158.12345:1.08500}]};
    }else if(url.pathname==='/api/latest'){
      data=Object.fromEntries(pairs.map(code=>[code,{
        symbol:code,
        mid:code==='USDJPY'?158.12372:1.08527,
        stale:false,marketState:'open',timestamp:new Date().toISOString(),
        source:'MT5 test feed'
      }]));
    }else{
      await route.fulfill({status:404,body:'{}'});return;
    }
    await route.fulfill({status:200,contentType:'application/json',headers:{'access-control-allow-origin':'*'},body:JSON.stringify(data)});
  });
  // Third-party scripts are blocked for deterministic testing; their config is
  // still asserted to use the selected TradingView symbol.
  await page.route('https://s3.tradingview.com/**',route=>route.fulfill({status:200,contentType:'application/javascript',body:''}));
  const url=pathToFileURL(resolve(process.cwd(),'../../site/index.html')).href;
  await page.goto(url,{waitUntil:'domcontentloaded'});
  const eur=page.locator('[data-symbol="EURUSD"]');
  await expect(eur.locator('.precise-rate')).toHaveText('1.08527');
  await expect(eur.locator('.precise-change')).toHaveText('+0.00027');
  await expect(page.locator('[data-symbol="USDJPY"] .precise-change')).toHaveText('+0.00027');

  await page.locator('[data-symbol="USDJPY"]').click();
  await expect(page.locator('#heroPairSelect')).toHaveValue('USDJPY');
  await expect(page.locator('#heroPairTitle')).toContainText('USD/JPY');
  await expect.poll(()=>page.locator('#heroLiveWidget script').textContent()).toContain('FX:USDJPY|1D');

  await page.locator('#heroPairSelect').selectOption('GBPUSD');
  await expect(page.locator('#heroPairTitle')).toContainText('GBP/USD');
  await expect.poll(()=>page.locator('#heroLiveWidget script').textContent()).toContain('FX:GBPUSD|1D');
});

test('missing live provider quotes show no fabricated price',async({page})=>{
  await page.route('https://biquote.io/**',route=>route.abort());
  await page.route('https://s3.tradingview.com/**',route=>route.abort());
  await page.goto(pathToFileURL(resolve(process.cwd(),'../../site/index.html')).href,{waitUntil:'domcontentloaded'});
  await expect(page.locator('#preciseTickerStatus')).toContainText('unavailable');
  await expect(page.locator('[data-symbol="EURUSD"] .precise-rate')).toHaveText('—');
  await expect(page.locator('[data-symbol="EURUSD"] .precise-change')).toHaveText('—');
});
