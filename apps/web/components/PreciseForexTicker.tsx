'use client';

import {useEffect,useRef,useState} from 'react';

export const PAIRS=['EURUSD','GBPUSD','USDJPY','USDCHF','AUDUSD','EURGBP'] as const;
export type Code=(typeof PAIRS)[number];
export function labelFor(code:Code){return code.slice(0,3)+'/'+code.slice(3);}

type Tick={symbol:string;mid:number;marketState?:string;stale?:boolean;timestamp?:string;source?:string};
type Candle={open:number;isOpen?:boolean};
type Hub={start():Promise<void>;stop():Promise<void>;invoke(name:string,pairs:readonly string[]):Promise<void>;
 on(name:string,cb:(tick:Tick|Tick[])=>void):void;onreconnecting(cb:()=>void):void;
 onreconnected(cb:()=>void):void;onclose(cb:()=>void):void};
type HubBuilder={withUrl(url:string):HubBuilder;withAutomaticReconnect():HubBuilder;build():Hub};
type SignalR={HubConnectionBuilder:new()=>HubBuilder};

const API='https://biquote.io/api';
const good=(value:number)=>Number.isFinite(value)&&value>0;
const fmt=(value:number)=>value.toFixed(5);

export default function PreciseForexTicker(){
 const [quotes,setQuotes]=useState<Record<string,Tick>>({});
 const [opens,setOpens]=useState<Record<string,number>>({});
 const [now,setNow]=useState(0);
 const [paused,setPaused]=useState(false);
 const running=useRef(false),streaming=useRef(false),blockedUntil=useRef(0);
 useEffect(()=>{
  let active=true;
  let hub:Hub|null=null;
  const get=async(url:string):Promise<unknown>=>{
   const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),8000);
   try{
    const response=await fetch(url,{cache:'no-store',signal:controller.signal});
    if(response.status===429){
     const seconds=Number(response.headers.get('Retry-After'));
     blockedUntil.current=Date.now()+(good(seconds)?seconds:60)*1000;
     throw Error('Rate limit');
    }
    if(!response.ok)throw Error('HTTP '+response.status);
    return await response.json() as unknown;
   }finally{clearTimeout(timer);}
  };
  const accept=(candidate:Tick|undefined)=>{
   if(!candidate||!PAIRS.some(x=>x===candidate.symbol)||!good(Number(candidate.mid)))return;
   if(active)setQuotes(v=>({...v,[candidate.symbol]:{...candidate,mid:Number(candidate.mid)}}));
  };
  const daily=async()=>{
   if(Date.now()<blockedUntil.current)return;
   const changes:Record<string,number>={};
   await Promise.all(PAIRS.map(async code=>{
    try{
     const data=await get(API+'/'+code+'/ohlc?interval=1d&limit=2') as {bars?:Candle[]};
     if(!Array.isArray(data.bars))return;
     const bar=data.bars.find(x=>x.isOpen)||data.bars[0];
     if(bar&&good(Number(bar.open)))changes[code]=Number(bar.open);
    }catch{/* Unknown day open is never fabricated. */}
   }));
   if(active)setOpens(v=>({...v,...changes}));
  };
  const poll=async()=>{
   if(!active||document.hidden||streaming.current||running.current||Date.now()<blockedUntil.current)return;
   running.current=true;
   try{
    const query=PAIRS.map(code=>'symbols='+encodeURIComponent(code)).join('&');
    const result=await get(API+'/latest?'+query);
    const mapped=Array.isArray(result)?Object.fromEntries((result as Tick[]).map(x=>[x.symbol,x])):result;
    if(!mapped||typeof mapped!=='object')throw Error('Invalid quote response');
    const batch=mapped as Record<string,Tick>;
    for(const code of PAIRS)accept(batch[code]);
   }catch{
    // One connection failure does not imply a price movement.
    if(!streaming.current&&active)setQuotes(v=>Object.fromEntries(Object.entries(v).map(([k,t])=>[k,{...t,stale:true}])));
   }finally{running.current=false;}
  };
  const connect=async()=>{
   try{
    let lib=(window as Window & {signalR?:SignalR}).signalR;
    if(!lib){
     const tag=document.createElement('script');
     tag.src='https://cdnjs.cloudflare.com/ajax/libs/microsoft-signalr/8.0.0/signalr.min.js';
     tag.async=true;
     await new Promise<void>((resolve,reject)=>{tag.onload=()=>resolve();tag.onerror=()=>reject(Error('Stream client unavailable'));document.head.append(tag);});
     lib=(window as Window & {signalR?:SignalR}).signalR;
    }
    if(!lib||!active)return;
    const connection=hub=new lib.HubConnectionBuilder().withUrl('https://biquote.io/hubs/tick').withAutomaticReconnect().build();
    connection.on('ReceiveTick',value=>accept(Array.isArray(value)?value[0]:value));
    connection.onreconnecting(()=>{streaming.current=false;});
    connection.onreconnected(()=>{if(active)void connection.invoke('Subscribe',PAIRS).then(()=>{streaming.current=true;}).catch(()=>{streaming.current=false;});});
    connection.onclose(()=>{streaming.current=false;});
    await connection.start();
    if(!active){await connection.stop();return;}
    await connection.invoke('Subscribe',PAIRS);
    streaming.current=true;
   }catch{streaming.current=false;} // REST keeps refreshing every second.
  };
  void daily().then(poll);
  void connect();
  const second=window.setInterval(()=>{if(active){setNow(Date.now());if(!streaming.current)void poll();}},1000);
  const opensInterval=window.setInterval(()=>{void daily();},20*60*1000);
  const visibility=()=>{if(!document.hidden){void daily();void poll();}};
  document.addEventListener('visibilitychange',visibility);
  return ()=>{
   active=false;streaming.current=false;
   window.clearInterval(second);window.clearInterval(opensInterval);
   document.removeEventListener('visibilitychange',visibility);
   if(hub)void hub.stop().catch(()=>{});
  };
 },[]);

 return <div className="provider-home-ticker" aria-label="Scrolling Forex currency prices and five-decimal changes">
  <div className="precise-ticker">
   <div className={"precise-ticker-track"+(paused?" ticker-stopped":"")} role="group" aria-label="Choose a currency pair for the chart">
    {[...PAIRS,...PAIRS].map((code,index)=>{
     const duplicated=index>=PAIRS.length,tick=quotes[code],opened=opens[code];
     const timestamp=tick?Date.parse(tick.timestamp||''):NaN;
     const fresh=Boolean(tick&&tick.marketState==='open'&&tick.stale===false&&Number.isFinite(timestamp)&&now-timestamp<300000&&now-timestamp> -90000);
     const change=fresh&&good(opened)?tick.mid-opened:null;
     return <button key={code+'-'+index} data-symbol={duplicated?undefined:code} data-clone-symbol={duplicated?code:undefined}
      tabIndex={duplicated?-1:undefined} aria-hidden={duplicated?true:undefined}
      type="button" className="precise-ticker-item"
      title={labelFor(code)+' · '+(!tick?'Price unavailable':tick.marketState==='closed'?'Market closed':fresh?'Current quote':'Last known quote')}
      onClick={()=>{setPaused(true);window.dispatchEvent(new CustomEvent('pipmora:pair-select',{detail:{code}}));}}>
      <span className="precise-pair">{labelFor(code)}</span>
      <span className="precise-rate">{tick&&good(tick.mid)?fmt(tick.mid):'—'}</span>
      <span className={'precise-change '+(change===null?'':change>=0?'up':'down')}>
       {change===null?'—':(change>=0?'+':'−')+fmt(Math.abs(change))}
      </span>
      <span className={"precise-percent "+(change===null?"":change>=0?"up":"down")} aria-label="Session percentage change">
       {change===null?"—":"("+(change>=0?"+":"−")+(Math.abs(change/opened)*100).toFixed(2)+"%)"}
      </span>
     </button>;
    })}
   </div>
  </div>
  <p className="ticker-credit"><a href="https://biquote.io/docs/" target="_blank" rel="noopener noreferrer">Forex prices by biquote.io</a></p>
 </div>;
}
