'use client';

import {useEffect,useRef,useState} from 'react';

export const PAIRS=['EURUSD','GBPUSD','USDJPY','USDCHF','AUDUSD','EURGBP'] as const;
export type Code=(typeof PAIRS)[number];
export function labelFor(code:Code){return code.slice(0,3)+'/'+code.slice(3);}
type Tick={symbol:string;mid:number;marketState?:string;stale?:boolean;timestamp?:string;source?:string};
type Candle={open:number;isOpen?:boolean};
const API='https://biquote.io/api';
const fmt=(n:number)=>n.toFixed(5);
const good=(n:number)=>Number.isFinite(n)&&n>0;

export default function PreciseForexTicker(){
 const [ticks,setTicks]=useState<Record<string,Tick>>({});
 const [opens,setOpens]=useState<Record<string,number>>({});
 const [message,setMessage]=useState('Loading indicative Forex prices…');
 const running=useRef(false),blockedUntil=useRef(0);
 useEffect(()=>{
  let active=true;
  const get=async(url:string)=>{
   const ac=new AbortController(),timer=setTimeout(()=>ac.abort(),9000);
   try{
    const res=await fetch(url,{cache:'no-store',signal:ac.signal});
    if(res.status===429){blockedUntil.current=Date.now()+60000;throw Error('Rate limit');}
    if(!res.ok)throw Error('HTTP '+res.status);
    return await res.json() as unknown;
   }finally{clearTimeout(timer);}
  };
  const daily=async()=>{
   if(Date.now()<blockedUntil.current)return;
   const updates:Record<string,number>={};
   await Promise.all(PAIRS.map(async code=>{
    try{
     const data=await get(API+'/'+code+'/ohlc?interval=1d&limit=2') as {bars?:Candle[]};
     if(!Array.isArray(data.bars))return;
     const bar=data.bars.find(x=>x.isOpen)||data.bars[0];
     if(bar&&good(Number(bar.open)))updates[code]=Number(bar.open);
    }catch{/* No fabricated fallback */}
   }));
   if(active)setOpens(v=>({...v,...updates}));
  };
  const latest=async()=>{
   if(!active||running.current||document.hidden||Date.now()<blockedUntil.current)return;
   running.current=true;
   try{
    const qs=PAIRS.map(s=>'symbols='+encodeURIComponent(s)).join('&');
    const data=await get(API+'/latest?'+qs);
    const candidate=Array.isArray(data)?Object.fromEntries(data.map((t:Tick)=>[t.symbol,t])):data;
    if(!candidate||typeof candidate!=='object')throw Error('Invalid feed');
    const incoming:Record<string,Tick>={};
    for(const code of PAIRS){
     const t=(candidate as Record<string,Tick>)[code];
     if(t&&good(Number(t.mid)))incoming[code]={...t,mid:Number(t.mid)};
    }
    if(!Object.keys(incoming).length)throw Error('No valid prices');
    if(active){setTicks(v=>({...v,...incoming}));setMessage('MT5 indicative FX quotes · updates every 15s');}
   }catch{
    if(active){setMessage('Quote feed unavailable · retrying');setTicks(v=>Object.fromEntries(Object.entries(v).map(([k,t])=>[k,{...t,stale:true}])));}
   }finally{running.current=false;}
  };
  void daily().then(latest);
  const t1=window.setInterval(()=>void latest(),15000),t2=window.setInterval(()=>void daily(),20*60*1000);
  const resume=()=>{if(!document.hidden){void daily();void latest();}};
  document.addEventListener('visibilitychange',resume);
  return ()=>{active=false;window.clearInterval(t1);window.clearInterval(t2);document.removeEventListener('visibilitychange',resume);};
 },[]);
 return <div className="provider-home-ticker" aria-label="Provider-supplied Forex prices with five-decimal changes">
  <div className="precise-ticker"><div className="precise-ticker-track" role="group" aria-label="Select currency for main chart">
   {PAIRS.map(code=>{
    const tick=ticks[code],opened=opens[code];
    const age=tick?Date.parse(tick.timestamp||''):NaN;
    const fresh=Boolean(tick&&tick.marketState==='open'&&tick.stale===false&&Number.isFinite(age)&&Date.now()-age<300000&&Date.now()-age> -90000);
    const delta=fresh&&good(opened)?tick.mid-opened:null;
    return <button key={code} type="button" className="precise-ticker-item" onClick={()=>window.dispatchEvent(new CustomEvent('pipmora:pair-select',{detail:{code}}))}
      title={'Select '+labelFor(code)+' · '+(tick?.source||'biquote.io MT5')}>
      <span className="precise-pair">{labelFor(code)}</span>
      <span className="precise-rate">{tick&&good(tick.mid)?fmt(tick.mid):'—'}</span>
      <span className={'precise-change '+(delta===null?'':delta>=0?'up':'down')}>
       {delta===null?'—':(delta>=0?'+':'−')+fmt(Math.abs(delta))}
      </span>
      <span className={'precise-market-state '+(fresh?'is-live':'')}>
       {!tick?'Unavailable':fresh?'LIVE':tick.marketState==='closed'?'Closed':'Stale'}
      </span>
    </button>;
   })}
  </div></div>
  <p className="provider-home-source">{message} · Changes shown to 5 decimal places against provider daily open · <a href="https://biquote.io/docs/" target="_blank" rel="noopener noreferrer">biquote.io MT5</a> · Feeds may differ</p>
 </div>;
}
