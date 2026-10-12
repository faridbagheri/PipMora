'use client';

import {useEffect,useRef} from 'react';

type Variant='ticker'|'overview'|'calendar'|'symbol'|'advanced';
type ForexPair='EUR/USD'|'GBP/USD'|'USD/JPY'|'USD/CHF'|'AUD/USD'|'EUR/GBP';
const PAIRS:ForexPair[]=['EUR/USD','GBP/USD','USD/JPY','USD/CHF','AUD/USD','EUR/GBP'];

function configFor(variant:Variant,pair:ForexPair):{script:string;settings:Record<string,unknown>;url:string;caption:string}{
  const symbol='FX:'+pair.replace('/','');
  const base={locale:'en',colorTheme:'light',width:'100%',height:'100%'};
  if(variant==='ticker')return {script:'ticker-tape',
    settings:{symbols:PAIRS.map(p=>({proName:'FX:'+p.replace('/',''),title:p})),showSymbolLogo:false,displayMode:'adaptive',isTransparent:false,colorTheme:'light',locale:'en'},
    url:'https://www.tradingview.com/markets/currencies/',caption:'Forex quotes'};
  if(variant==='overview')return {script:'market-overview',
    settings:{...base,dateRange:'1D',isTransparent:false,showFloatingTooltip:true,showChart:true,showSymbolLogo:false,
      tabs:[{title:'Major Forex',symbols:PAIRS.map(p=>({s:'FX:'+p.replace('/',''),d:p}))}]},
    url:'https://www.tradingview.com/markets/currencies/',caption:'Forex watchlist'};
  if(variant==='calendar')return {script:'events',
    settings:{...base,isTransparent:false,countryFilter:'us,eu,gb,jp,ch,au,ca',importanceFilter:'-1,0,1'},
    url:'https://www.tradingview.com/economic-calendar/',caption:'Economic calendar'};
  if(variant==='symbol')return {script:'symbol-overview',
    settings:{...base,symbols:[[pair,symbol+'|1D']],autosize:true,isTransparent:false,chartType:'area',changeMode:'price-and-percent',
      dateRanges:['1d|5','1m|30','3m|60','12m|1D','all|1M'],hideDateRanges:false,hideMarketStatus:false},
    url:'https://www.tradingview.com/symbols/'+pair.replace('/','')+'/',caption:pair+' price and chart'};
  return {script:'advanced-chart',
    settings:{symbol,autosize:true,interval:'60',timezone:'Etc/UTC',theme:'light',style:'1',locale:'en',
      withdateranges:true,hide_side_toolbar:true,hide_top_toolbar:false,allow_symbol_change:true,
      hide_legend:false,save_image:false,backgroundColor:'#fff',gridColor:'rgba(46,68,105,0.07)',support_host:'https://www.tradingview.com'},
    url:'https://www.tradingview.com/symbols/'+pair.replace('/','')+'/',caption:pair+' chart'};
}

/** Public provider widgets are read-only. Never use their DOM to calculate demo fills. */
export default function ProviderForexWidget({variant,pair='EUR/USD',height}:{variant:Variant;pair?:ForexPair;height?:number}){
  const container=useRef<HTMLDivElement>(null);
  useEffect(()=>{
    const target=container.current;
    if(!target)return;
    const cfg=configFor(variant,pair);
    target.replaceChildren();
    const targetWidget=document.createElement('div');
    targetWidget.className='tradingview-widget-container__widget';
    targetWidget.style.cssText='height:calc(100% - 30px);width:100%';
    target.appendChild(targetWidget);
    const copyright=document.createElement('div');
    copyright.className='tradingview-widget-copyright';
    const attribution=document.createElement('a');
    attribution.href=cfg.url;attribution.target='_blank';attribution.rel='noopener nofollow';
    attribution.textContent=cfg.caption;
    copyright.append(attribution,document.createTextNode(' by TradingView'));
    target.appendChild(copyright);
    const script=document.createElement('script');
    script.type='text/javascript';script.async=true;
    script.src='https://s3.tradingview.com/external-embedding/embed-widget-'+cfg.script+'.js';
    script.textContent=JSON.stringify(cfg.settings);
    script.onerror=()=>{
      const notice=document.createElement('p');
      notice.className='provider-widget-error';
      notice.textContent='Live data is currently unavailable. Open the TradingView source link below.';
      targetWidget.appendChild(notice);
    };
    target.appendChild(script);
    return ()=>target.replaceChildren();
  },[variant,pair]);
  return <div className={'provider-widget provider-widget-'+variant} style={{height:height??(variant==='ticker'?90:variant==='calendar'?550:variant==='advanced'?440:460)}}>
    <div className="tradingview-widget-container" ref={container} style={{height:'100%',width:'100%'}}/>
  </div>;
}
