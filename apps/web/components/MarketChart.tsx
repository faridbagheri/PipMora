'use client';
import {useState} from 'react';
export type Bar={time:string;open:number;high:number;low:number;close:number;sma20?:number|null;ema20?:number|null;rsi14?:number|null};
export default function MarketChart({data,title='EUR/USD',height=300}:{data:Bar[];title?:string;height?:number}){
 const [count,setCount]=useState(70),[shift,setShift]=useState(0),[kind,setKind]=useState<'candles'|'line'>('candles'),[sma,setSma]=useState(true),[ema,setEma]=useState(false);
 const n=Math.min(count,data.length),end=Math.max(n,data.length-shift),visible=data.slice(end-n,end),w=860,h=height,top=22,bottom=h-36;
 const values=visible.flatMap(v=>[v.high,v.low]),lo=Math.min(...values,0),hi=Math.max(...values,0);
 // Avoid including zero in forex price range.
 const min=visible.length?Math.min(...visible.map(x=>x.low)):0,max=visible.length?Math.max(...visible.map(x=>x.high)):1,span=max-min||1;
 const y=(v:number)=>top+(max-v)/span*(bottom-top);
 const dx=w/Math.max(visible.length,1),path=(field:'close'|'sma20'|'ema20')=>visible.reduce((acc,v,i)=>{const value=v[field];return value==null?acc:acc+`${acc?' L':'M'} ${(i+.5)*dx} ${y(Number(value))}`},'');
 let dragging=0;
 return <div className="chart-frame"><div className="chart-top"><div><span className="chart-label">{title}</span><span className="chart-live">● SYNTHETIC DEMO</span></div><div className="chart-controls"><button className={kind==='candles'?'selected':''} onClick={()=>setKind('candles')}>Candles</button><button className={kind==='line'?'selected':''} onClick={()=>setKind('line')}>Line</button><button className={sma?'selected':''} onClick={()=>setSma(!sma)}>SMA</button><button className={ema?'selected':''} onClick={()=>setEma(!ema)}>EMA</button></div></div>
 {visible.length===0?<div className="empty-state">No candles available</div>:<svg className="financial-chart" viewBox={`0 0 ${w} ${h}`} role="img" aria-label={`${title} interactive ${kind} chart, synthetic demonstration prices`} onPointerDown={e=>{dragging=e.clientX;e.currentTarget.setPointerCapture(e.pointerId)}} onPointerUp={e=>{if(dragging){setShift(z=>Math.max(0,Math.min(data.length-n,z+Math.round((e.clientX-dragging)/12))));dragging=0}}}>
 {[0,.25,.5,.75,1].map((v,i)=><g key={i}><line x1="0" y1={top+v*(bottom-top)} x2={w} y2={top+v*(bottom-top)} stroke="var(--chart-grid)" strokeDasharray="4 6"/><text x={w-4} y={top+v*(bottom-top)-5} textAnchor="end" fontSize="12" fill="var(--muted)">{(max-span*v).toFixed(title==='USD/JPY'?3:5)}</text></g>)}
 {kind==='candles'?visible.map((v,i)=>{const x=(i+.5)*dx,green=v.close>=v.open,c=green?'#25cbb0':'#f2788e';return <g key={i}><line x1={x} x2={x} y1={y(v.high)} y2={y(v.low)} stroke={c} strokeWidth="1.2"/><rect x={x-Math.max(1,dx*.28)} y={Math.min(y(v.open),y(v.close))} width={Math.max(2,dx*.56)} height={Math.max(1.4,Math.abs(y(v.open)-y(v.close)))} rx=".4" fill={c}/></g>}):<path d={path('close')} stroke="#54a5ff" strokeWidth="2.4" fill="none"/>}
 {sma&&<path d={path('sma20')} stroke="#f2bf76" strokeWidth="1.9" fill="none"/>}{ema&&<path d={path('ema20')} stroke="#b18cff" strokeWidth="1.9" fill="none"/>}
 {visible.filter((_,i)=>i%Math.max(1,Math.floor(n/6))===0).map((v,i)=><text key={i} x={(visible.indexOf(v)+.5)*dx} y={h-7} fontSize="12" fill="var(--muted)">{new Date(v.time).toLocaleDateString('en-GB',{day:'numeric',month:'short'})}</text>)}
 </svg>}
 <div className="chart-footer"><span>Drag to pan · Scroll controls below</span><div className="chart-controls"><button onClick={()=>setShift(s=>Math.min(data.length-n,s+12))}>←</button><button onClick={()=>setShift(s=>Math.max(0,s-12))}>→</button><button onClick={()=>setCount(c=>Math.max(20,c-15))}>＋</button><button onClick={()=>setCount(c=>Math.min(200,c+15))}>－</button><button onClick={()=>{setCount(70);setShift(0)}}>Reset</button></div></div></div>
}
