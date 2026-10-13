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
  await page.route('https://cdnjs.cloudflare.com/ajax/libs/microsoft-signalr/**',route=>route.fulfill({status:200,contentType:'application/javascript',body:''}));
  // Third-party scripts are blocked for deterministic testing; their config is
  // still asserted to use the selected TradingView symbol.
  await page.route('https://s3.tradingview.com/**',route=>route.fulfill({status:200,contentType:'application/javascript',body:''}));
  const url=pathToFileURL(resolve(process.cwd(),'../../site/index.html')).href;
  await page.goto(url,{waitUntil:'domcontentloaded'});
  const eur=page.locator('[data-symbol="EURUSD"]');
  await expect(eur.locator('.precise-rate')).toHaveText('1.08527');
  await expect(eur.locator('.precise-change')).toHaveText('+0.00027');
  await expect(eur.locator('.precise-percent')).toHaveText('(+0.02%)');
  await expect(page.locator('[data-clone-symbol="EURUSD"] .precise-percent')).toHaveText('(+0.02%)');
  await expect(page.locator('.precise-ticker-item')).toHaveCount(12);
  await expect.poll(()=>eur.evaluate(el=>getComputedStyle(el.parentElement!).animationName)).toContain('pipmora-forex-scroll');
  await expect(page.locator('.precise-market-state')).toHaveCount(0);
  await expect(page.locator('[data-symbol="USDJPY"] .precise-change')).toHaveText('+0.00027');

  // Focus pauses the ticker animation, preserving click stability and keyboard access.
  await page.locator('[data-symbol="USDJPY"]').focus();
  await expect.poll(()=>page.locator('[data-symbol="USDJPY"]').evaluate(el=>getComputedStyle(el.parentElement!).animationPlayState)).toBe('paused');
  await page.locator('[data-symbol="USDJPY"]').click();
  await expect(page.locator('.precise-ticker-track')).toHaveClass(/ticker-stopped/);
  await expect(page.locator('#heroPairSelect')).toHaveValue('USDJPY');
  await expect(page.locator('#heroPairTitle')).toContainText('USD/JPY');
  await expect.poll(()=>page.locator('#heroLiveWidget script').textContent()).toContain('FX:USDJPY|1D');

  await page.locator('#heroPairSelect').selectOption('GBPUSD');
  await expect(page.locator('#heroPairTitle')).toContainText('GBP/USD');
  await expect.poll(()=>page.locator('.precise-ticker-track').evaluate(el=>getComputedStyle(el).animationPlayState)).toBe('paused');
  await expect.poll(()=>page.locator('#heroLiveWidget script').textContent()).toContain('FX:GBPUSD|1D');
});

test('missing live provider quotes show no fabricated price',async({page})=>{
  await page.route('https://cdnjs.cloudflare.com/ajax/libs/microsoft-signalr/**',route=>route.fulfill({status:200,contentType:'application/javascript',body:''}));
  await page.route('https://biquote.io/**',route=>route.abort());
  await page.route('https://s3.tradingview.com/**',route=>route.abort());
  await page.goto(pathToFileURL(resolve(process.cwd(),'../../site/index.html')).href,{waitUntil:'domcontentloaded'});
  await expect(page.locator('#preciseTickerStatus')).toContainText('unavailable');
  await expect(page.locator('[data-symbol="EURUSD"] .precise-rate')).toHaveText('—');
  await expect(page.locator('[data-symbol="EURUSD"] .precise-change')).toHaveText('—');
});


test('price updates from new real quote samples at one-second fallback cadence',async({page})=>{
  let seen=0;
  await page.route('https://cdnjs.cloudflare.com/ajax/libs/microsoft-signalr/**',route=>route.fulfill({status:200,contentType:'application/javascript',body:''}));
  await page.route('https://s3.tradingview.com/**',route=>route.fulfill({status:200,contentType:'application/javascript',body:''}));
  await page.route('https://biquote.io/api/**',route=>{
    const path=new URL(route.request().url()).pathname;
    const payload=path.endsWith('/ohlc')?{bars:[{isOpen:true,open:1.08500}]}:
      Object.fromEntries(pairs.map(symbol=>[symbol,{symbol,mid:++seen<2?1.08527:1.08529,
        marketState:'open',stale:false,timestamp:new Date().toISOString()}]));
    return route.fulfill({status:200,contentType:'application/json',headers:{'access-control-allow-origin':'*'},body:JSON.stringify(payload)});
  });
  await page.goto(pathToFileURL(resolve(process.cwd(),'../../site/index.html')).href,{waitUntil:'domcontentloaded'});
  const delta=page.locator('[data-symbol="EURUSD"] .precise-change');
  await expect(delta).toHaveText('+0.00027');
  await expect(delta).toHaveText('+0.00029',{timeout:7000});
});


test('all public page footers link to the requested social and contact channels', async({page})=>{
  await page.route('https://**/*',route=>route.abort());
  for(const file of ['index.html','markets.html','lab.html']){
    await page.goto(pathToFileURL(resolve(process.cwd(),'../../site',file)).href,{waitUntil:'domcontentloaded'});
    const links=page.locator('footer .pm-socials a');
    await expect(links).toHaveCount(3);
    await expect(links.nth(0)).toHaveAttribute('href','https://www.linkedin.com/in/farid-bagheri-a67355ba');
    await expect(links.nth(1)).toHaveAttribute('href','mailto:Farid.bagheri8989@gmail.com');
    await expect(links.nth(2)).toHaveAttribute('href','https://faridbagheri.github.io/');
    await expect(links.nth(0)).toHaveAttribute('aria-label',/LinkedIn/);
  }
});
