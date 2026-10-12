"""Financial arithmetic on verified user trades; avoid LLM arithmetic."""
from decimal import Decimal, ROUND_HALF_UP
from collections import defaultdict

CENT=Decimal(".01")
def rounded(x): return float(Decimal(str(x)).quantize(CENT, rounding=ROUND_HALF_UP))

def pnl_usd(symbol, side, units, entry, exit_price, gbpusd=Decimal("1.2738")):
    """P&L in USD; quote-to-USD conversion for six supported FX pairs."""
    units,entry,exit_price=map(lambda x:Decimal(str(x)),(units,entry,exit_price))
    signed=(exit_price-entry)*units*(1 if side=="BUY" else -1)
    quote=symbol.split("/")[1]
    if quote=="USD": return signed
    if symbol in ("USD/JPY","USD/CHF"):
        if exit_price<=0: raise ValueError("Invalid conversion rate")
        return signed/exit_price
    if symbol=="EUR/GBP": return signed*gbpusd
    raise ValueError("Unsupported instrument")

def analytics(trades):
    closed=sorted(trades,key=lambda t:t.closed_at)
    results=[float(t.pnl_usd) for t in closed]
    wins=[v for v in results if v>0]; losses=[v for v in results if v<0]
    gross_win=sum(wins); gross_loss=-sum(losses)
    balance=10000; peak=balance; max_dd=0; equity=[]
    for t,v in zip(closed,results):
        balance+=v;peak=max(balance,peak)
        max_dd=max(max_dd, (peak-balance)/peak*100 if peak>0 else 0)
        equity.append({"at":t.closed_at.isoformat(),"balance":round(balance,2),"pnl":round(v,2)})
    grouped=defaultdict(lambda:{"count":0,"pnl":0})
    for t,v in zip(closed,results):
        grouped[t.symbol]["count"]+=1;grouped[t.symbol]["pnl"]+=v
    rrs=[float(t.risk_reward) for t in closed if t.risk_reward is not None]
    return dict(total_trades=len(closed),win_rate=round(100*len(wins)/len(closed),1) if closed else 0,
       net_pnl=round(sum(results),2),average_win=round(gross_win/len(wins),2) if wins else 0,
       average_loss=round(sum(losses)/len(losses),2) if losses else 0,
       profit_factor=round(gross_win/gross_loss,2) if gross_loss else None,
       max_drawdown_pct=round(max_dd,2),average_risk_reward=round(sum(rrs)/len(rrs),2) if rrs else None,
       by_pair=[{"symbol":k,"trades":v["count"],"pnl":round(v["pnl"],2)} for k,v in sorted(grouped.items())],
       equity_curve=equity,insufficient_sample=len(closed)<5)
