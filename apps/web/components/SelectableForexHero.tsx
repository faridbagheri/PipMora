'use client';

import {useEffect,useState} from 'react';
import ProviderForexWidget from './ProviderForexWidget';
import {PAIRS,type Code,labelFor} from './PreciseForexTicker';

export default function SelectableForexHero(){
 const [pair,setPair]=useState<Code>('EURUSD');
 useEffect(()=>{
  const select=(e:Event)=>{
   const code=(e as CustomEvent<{code?:string}>).detail?.code;
   if(code && PAIRS.some(p=>p===code))setPair(code as Code);
  };
  window.addEventListener('pipmora:pair-select',select);
  return ()=>window.removeEventListener('pipmora:pair-select',select);
 },[]);
 return <div className="provider-home-hero">
  <div className="provider-home-label">
   <strong>{labelFor(pair)} · Provider market chart</strong>
   <div className="hero-pair-controls">
    <label htmlFor="homeForexPair">Currency pair</label>
    <select id="homeForexPair" value={pair} onChange={e=>setPair(e.target.value as Code)} aria-label="Select Forex chart currency pair">
     {PAIRS.map(code=><option key={code} value={code}>{labelFor(code)}</option>)}
    </select>
   </div>
  </div>
  <ProviderForexWidget variant="symbol" pair={labelFor(pair) as 'EUR/USD'|'GBP/USD'|'USD/JPY'|'USD/CHF'|'AUD/USD'|'EUR/GBP'} height={360}/>
  <p className="hero-chart-source"><a href={'https://www.tradingview.com/symbols/'+pair+'/'} target="_blank" rel="noopener noreferrer">{labelFor(pair)} chart</a> by TradingView. Chart quotes can differ from the indicative ticker feed.</p>
 </div>;
}
