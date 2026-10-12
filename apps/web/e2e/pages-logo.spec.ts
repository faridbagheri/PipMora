import {test,expect} from '@playwright/test';
import {resolve} from 'node:path';
import {pathToFileURL} from 'node:url';

/**
 * Regression: the PipMora SVG once rendered at its natural 1120px width, covering
 * the navigation and market ticker. Test the ACTUAL GitHub Pages HTML/CSS in Chromium.
 */
for(const entry of ['index.html','markets.html','lab.html']){
  for(const viewport of [{width:1440,height:900},{width:390,height:844}]){
    test('public '+entry+' keeps the top-left logo contained at '+viewport.width+'px',async({page})=>{
      await page.setViewportSize(viewport);
      // Embedded market widgets are third party; logo layout should not depend on them.
      await page.route('https://**/*',route=>route.abort());
      const file=pathToFileURL(resolve(process.cwd(),'../../site',entry)).href;
      await page.goto(file,{waitUntil:'domcontentloaded'});
      const header=page.locator('header').first();
      const logo=header.locator('img.pip-wordmark');
      await expect(logo).toBeVisible();
      await expect.poll(()=>logo.evaluate(img=>(img as HTMLImageElement).naturalWidth)).toBeGreaterThan(0);
      const hb=await header.boundingBox(),lb=await logo.boundingBox();
      expect(hb).not.toBeNull();
      expect(lb).not.toBeNull();
      if(!hb||!lb)return;
      expect(lb.width).toBeLessThanOrEqual(viewport.width<650?140:182);
      expect(lb.height).toBeLessThanOrEqual(viewport.width<650?44:56);
      expect(lb.y).toBeGreaterThanOrEqual(hb.y-2);
      expect(lb.y+lb.height).toBeLessThanOrEqual(hb.y+hb.height+2);
      expect(lb.x).toBeLessThan(viewport.width/3);
      // A logo must never visually overlap the market ticker or the hero content.
      if(entry==='index.html'){
        const ticker=await page.locator('.live-ticker-banner').boundingBox();
        if(ticker)expect(lb.y+lb.height).toBeLessThanOrEqual(ticker.y+2);
      }
    });
  }
}
