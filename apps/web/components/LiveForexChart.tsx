'use client';

import {useEffect,useRef} from 'react';

type SymbolCode='FX:EURUSD'|'FX:GBPUSD'|'FX:USDJPY';

export default function LiveForexChart({symbol}:{symbol:SymbolCode}){
  const container=useRef<HTMLDivElement>(null);
  const pair=symbol.split(':')[1];
  useEffect(()=>{
    const root=container.current;
    if(!root)return;
    // The TradingView widget owns this DOM subtree. Its feed is NOT PipMora's simulation feed.
    root.replaceChildren();
    const widget=document.createElement('div');
    widget.className='tradingview-widget-container__widget';
    widget.style.cssText='height:calc(100% - 32px);width:100%';
    root.appendChild(widget);
    const attribution=document.createElement('div');
    attribution.className='tradingview-widget-copyright';
    const link=document.createElement('a');
    link.href='https://www.tradingview.com/symbols/'+pair+'/';
    link.target='_blank';
    link.rel='noopener nofollow';
    link.textContent=pair.slice(0,3)+'/'+pair.slice(3)+' chart';
    attribution.append(link,document.createTextNode(' by TradingView'));
    root.appendChild(attribution);

    const script=document.createElement('script');
    script.type='text/javascript';
    script.async=true;
    script.src='https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js';
    script.textContent=JSON.stringify({
      autosize:true,symbol,interval:'60',timezone:'Etc/UTC',
      theme:'light',style:'1',locale:'en',withdateranges:true,
      hide_side_toolbar:true,hide_top_toolbar:false,
      allow_symbol_change:true,hide_legend:false,
      save_image:false,calendar:false,backgroundColor:'#ffffff',
      gridColor:'rgba(46,68,105,0.07)',
      support_host:'https://www.tradingview.com'
    });
    root.appendChild(script);
    return ()=>{root.replaceChildren()};
  },[pair,symbol]);
  return <div className="live-next-chart" aria-label={'TradingView chart for '+pair}>
    <div className="tradingview-widget-container" ref={container} style={{height:'100%',width:'100%'}} />
  </div>;
}
