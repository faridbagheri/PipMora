"""Reproducible, conspicuously synthetic data. Never use for live execution."""
from datetime import datetime, timezone, timedelta
from math import sin, cos
from hashlib import sha256
from decimal import Decimal

PAIRS={"EUR/USD":1.08620,"GBP/USD":1.27380,"USD/JPY":149.150,"USD/CHF":0.88420,"AUD/USD":0.65430,"EUR/GBP":0.85230}
FRAMES={"15m":900,"1h":3600,"4h":14400,"1d":86400}
START=int(datetime(2026,1,1,tzinfo=timezone.utc).timestamp())

def number(seed: str):
    return int.from_bytes(sha256(seed.encode()).digest()[:8],"big")/2**64

def candle_at(symbol: str, timeframe: str, index: int):
    if symbol not in PAIRS or timeframe not in FRAMES: raise ValueError("Unsupported pair or timeframe")
    baseline=PAIRS[symbol]
    digits=3 if symbol=="USD/JPY" else 5
    unit=0.09 if digits==3 else 0.0009
    # Smooth synthetic close curve allows adjacent candles to connect precisely.
    def value(i):
        cycle=1.55*sin(i*0.067+number(symbol)*6)+0.9*sin(i*0.019+1.5)+0.7*cos(i*0.14)
        noise=(number(f"{symbol}:{timeframe}:{i}")-.5)*.65
        return baseline+unit*(cycle+noise)
    op=value(index-1); close=value(index)
    wick=unit*(.12+number(f"h:{symbol}:{timeframe}:{index}")*.8)
    low=min(op,close)-wick*.65
    high=max(op,close)+wick
    stamp=START+index*FRAMES[timeframe]
    return dict(time=datetime.fromtimestamp(stamp,timezone.utc).isoformat(),open=round(op,digits),high=round(high,digits),low=round(low,digits),close=round(close,digits))

def candles(symbol: str,timeframe: str="1h",limit: int=160,as_of: datetime|None=None):
    if symbol not in PAIRS or timeframe not in FRAMES: raise ValueError("Unsupported pair or timeframe")
    if not 10<=limit<=500: raise ValueError("Limit between 10 and 500")
    t=int((as_of or datetime.now(timezone.utc)).timestamp())
    last=max(2,(t-START)//FRAMES[timeframe])
    return [candle_at(symbol,timeframe,i) for i in range(max(1,last-limit+1),last+1)]

def quote(symbol): return Decimal(str(candles(symbol,limit=10)[-1]["close"]))

def indicators(data):
    closes=[r["close"] for r in data]
    sma=[];ema=[];rsi=[];atr=[];vol=[]
    gain=loss=0; avgtr=None; e=None
    for i,v in enumerate(closes):
        sma.append(round(sum(closes[i-19:i+1])/20,6) if i>=19 else None)
        e=v if e is None else v*(2/21)+e*(19/21)
        ema.append(round(e,6))
        if i==0:
            rsi.append(None); atr.append(None);vol.append(None);continue
        change=closes[i]-closes[i-1]
        gain= (gain*13+max(0,change))/14
        loss= (loss*13+max(0,-change))/14
        rsi.append(round(100-(100/(1+gain/loss)),2) if loss else (100 if gain else 50))
        c=data[i]; tr=max(c["high"]-c["low"],abs(c["high"]-closes[i-1]),abs(c["low"]-closes[i-1]))
        avgtr=tr if avgtr is None else (avgtr*13+tr)/14
        atr.append(round(avgtr,6))
        if i>=20:
            rets=[(closes[j]/closes[j-1]-1) for j in range(i-19,i+1)]
            avg=sum(rets)/len(rets)
            vol.append(round((sum((r-avg)**2 for r in rets)/len(rets))**.5*100,4))
        else: vol.append(None)
    return [{**r,"sma20":sma[i],"ema20":ema[i],"rsi14":rsi[i],"atr14":atr[i],"volatility_pct":vol[i]} for i,r in enumerate(data)]

SCENARIO={"id":"EURUSD_US_CPI_SYNTHETIC","title":"EUR/USD · simulated inflation release","symbol":"EUR/USD","release_index":56,"length":110,"start":"2026-06-12T08:00:00+00:00","description":"Entirely synthetic demonstration; not an actual CPI release or historical prices."}

def replay_candles():
    start=datetime.fromisoformat(SCENARIO["start"])
    # Deterministic scenario with an event volatility jump and a recoverable post-event pattern.
    rows=[]; previous=1.08520
    for i in range(SCENARIO["length"]):
        impulse=0.00007*sin(i*.41)+0.000025*cos(i*1.8)
        if i==56: impulse+=.0016
        if i==57: impulse-=.0008
        if i in (58,59): impulse-=.00023
        close=previous+impulse
        rows.append({"time":(start+timedelta(minutes=15*i)).isoformat(),"open":round(previous,5),"close":round(close,5),"high":round(max(previous,close)+.00012,5),"low":round(min(previous,close)-.00010,5)})
        previous=close
    return rows

REPLAY_BARS=replay_candles()
