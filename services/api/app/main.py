"""PipMora Phase 1 API: educational analytics and simulated trading only."""
import os, secrets
from contextlib import asynccontextmanager
from datetime import datetime,timezone,timedelta,date
from decimal import Decimal
from typing import Literal
from fastapi import FastAPI, Depends, HTTPException, Response, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from sqlalchemy.orm import Session
from sqlalchemy import select
from .db import engine, Base, get_db
from . import models as m
from .security import hash_password,verify_password,current_user,issue_session,set_cookie,token_digest,COOKIE,email_reset,trusted_origin
from .market import PAIRS,FRAMES,SCENARIO,REPLAY_BARS,candles,indicators,quote
from .analytics import analytics,pnl_usd,rounded

UTC=timezone.utc
D=Decimal

def iso(dt):
    if dt is None:return None
    return (dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt).isoformat()

def seed(db):
    for symbol in PAIRS:
        if not db.get(m.Instrument,symbol):
            a,b=symbol.split("/");db.add(m.Instrument(symbol=symbol,base_currency=a,quote_currency=b,label=f"{a} / {b}"))
    # Build clearly synthetic economic examples, including a previous release.
    if db.query(m.EconomicEvent).count()==0:
        patterns=[("US CPI", "United States","USD","HIGH"),("ECB Rate Decision","Euro Area","EUR","HIGH"),("Non-Farm Payrolls","United States","USD","HIGH"),("UK GDP","United Kingdom","GBP","MEDIUM"),("US PMI","United States","USD","MEDIUM"),("Japan Retail Sales","Japan","JPY","LOW"),("Swiss PPI","Switzerland","CHF","LOW"),("AU Unemployment","Australia","AUD","MEDIUM"),("Fed Interest Rate Decision","United States","USD","HIGH")]
        base=datetime.now(UTC).replace(hour=12,minute=30,second=0,microsecond=0)
        for i,(name,country,currency,impact) in enumerate(patterns):
            when=base+timedelta(days=i+1)
            db.add(m.EconomicEvent(name=name,country=country,currency=currency,release_at=when,impact=impact,previous=None,forecast=None,actual=None,source="SYNTHETIC DEMO"))
        old=m.EconomicEvent(name="Synthetic US CPI exercise",country="United States",currency="USD",release_at=base-timedelta(days=10),impact="HIGH",previous="2.4%",forecast="2.5%",actual="2.7%",source="SYNTHETIC DEMO")
        db.add(old);db.flush()
        db.add(m.EconomicRelease(event_id=old.id,release_at=old.release_at,actual=old.actual,forecast=old.forecast,previous=old.previous,source="SYNTHETIC DEMO"))
    db.commit()

@asynccontextmanager
async def lifespan(app):
    # SQLite dev convenience; PostgreSQL production schema is managed by Alembic.
    if engine.url.get_backend_name()=="sqlite": Base.metadata.create_all(bind=engine)
    try:
        with next_session() as db: seed(db)
    except Exception:
        # Surface schema/connection errors to operators instead of silently serving broken APIs.
        raise
    yield

from contextlib import contextmanager
@contextmanager
def next_session():
    from .db import SessionLocal
    db=SessionLocal()
    try:yield db
    finally:db.close()

app=FastAPI(title="PipMora API",description="Educational Forex intelligence with reproducible simulated prices. No real-money execution.",version="0.1.0",lifespan=lifespan)
app.add_middleware(CORSMiddleware,allow_origins=os.getenv("FRONTEND_ORIGIN","http://localhost:3000").split(","),allow_credentials=True,allow_methods=["GET","POST","PATCH","DELETE"],allow_headers=["Content-Type","Accept"])

@app.middleware("http")
async def origin_protection(request:Request,call_next):
    if request.method not in ("GET","HEAD","OPTIONS"):
        if request.headers.get("sec-fetch-site")=="cross-site":return Response("Untrusted origin",status_code=403)
        try:trusted_origin(request)
        except HTTPException:return Response("Untrusted origin",status_code=403)
    return await call_next(request)

class RegisterIn(BaseModel):
    model_config=ConfigDict(str_strip_whitespace=True)
    email: EmailStr
    name: str=Field(min_length=2,max_length=120)
    password: str=Field(min_length=12,max_length=128)
class LoginIn(BaseModel):
    email:EmailStr
    password:str
class ProfileIn(BaseModel):
    name:str=Field(min_length=2,max_length=120)
    theme:Literal["light","dark"]="dark"
    timezone:str=Field(max_length=70,default="UTC")
class ForgotIn(BaseModel):email:EmailStr
class ResetIn(BaseModel):token:str; password:str=Field(min_length=12,max_length=128)
class PositionIn(BaseModel):
    symbol:Literal["EUR/USD","GBP/USD","USD/JPY","USD/CHF","AUD/USD","EUR/GBP"]
    side:Literal["BUY","SELL"]
    units:float=Field(gt=0,le=1000000)
    stop_loss:float=Field(gt=0)
    take_profit:float=Field(gt=0)
    reasoning:str=Field(default="",max_length=4000)
    strategy:str=Field(default="",max_length=80)
    conditions:str=Field(default="",max_length=2000)
    replay_session_id:int|None=None
class ManualTradeIn(BaseModel):
    symbol:Literal["EUR/USD","GBP/USD","USD/JPY","USD/CHF","AUD/USD","EUR/GBP"]
    side:Literal["BUY","SELL"]
    units:float=Field(gt=0,le=1000000)
    entry:float=Field(gt=0);exit:float=Field(gt=0)
    stop_loss:float|None=None;take_profit:float|None=None
    opened_at:datetime|None=None;closed_at:datetime|None=None
    notes:str=Field(default="",max_length=4000)
    strategy:str=Field(default="",max_length=80)
    conditions:str=Field(default="",max_length=2000)
class NotesIn(BaseModel):notes:str=Field(max_length=4000);strategy:str=Field(default="",max_length=80)
class CoachIn(BaseModel):question:str=Field(min_length=3,max_length=1000);trade_id:int|None=None
class AdvanceIn(BaseModel):steps:int=Field(default=1,ge=1,le=20)
class ContactIn(BaseModel):name:str=Field(min_length=2,max_length=120);email:EmailStr;message:str=Field(min_length=10,max_length=3000)

def pub_user(u,db):
    p=db.get(m.Preference,u.id)
    return {"id":u.id,"email":u.email,"name":u.name,"created_at":iso(u.created_at),"theme":p.theme if p else "dark","timezone":p.timezone if p else "UTC"}

@app.get("/api/health")
def health():return {"status":"ok","service":"PipMora API","mode":"SIMULATED"}

@app.post("/api/auth/register",status_code=201)
def register(body:RegisterIn,response:Response,db:Session=Depends(get_db)):
    if db.query(m.User).filter_by(email=str(body.email).lower()).first():raise HTTPException(409,"Email already registered")
    u=m.User(email=str(body.email).lower(),name=body.name,password_hash=hash_password(body.password));db.add(u);db.flush()
    db.add(m.Preference(user_id=u.id));db.add(m.DemoAccount(user_id=u.id))
    raw=issue_session(db,u);db.commit();set_cookie(response,raw)
    return pub_user(u,db)

@app.post("/api/auth/login")
def login(body:LoginIn,response:Response,db:Session=Depends(get_db)):
    u=db.query(m.User).filter_by(email=str(body.email).lower()).first()
    if not u or not verify_password(u.password_hash,body.password):raise HTTPException(401,"Invalid email or password")
    raw=issue_session(db,u);db.commit();set_cookie(response,raw);return pub_user(u,db)

@app.post("/api/auth/logout")
def logout(request:Request,response:Response,db:Session=Depends(get_db)):
    raw=request.cookies.get(COOKIE)
    if raw:
        s=db.query(m.Session).filter_by(token_hash=token_digest(raw)).first()
        if s:s.revoked=True;db.commit()
    response.delete_cookie(COOKIE,path="/");return {"ok":True}

@app.get("/api/auth/me")
def me(u:m.User=Depends(current_user),db:Session=Depends(get_db)):
    return pub_user(u,db)

@app.post("/api/auth/forgot-password")
def forgot_password(body:ForgotIn,db:Session=Depends(get_db)):
    u=db.query(m.User).filter_by(email=str(body.email).lower()).first()
    message={"message":"If that email exists, a reset link will be sent when email delivery is configured."}
    if u:
        raw=secrets.token_urlsafe(40)
        db.add(m.PasswordReset(user_id=u.id,token_hash=token_digest(raw),expires_at=datetime.now(UTC)+timedelta(minutes=30)))
        db.commit()
        url=os.getenv("FRONTEND_ORIGIN","http://localhost:3000").split(",")[0]+"/reset-password?token="+raw
        if os.getenv("APP_ENV","development")=="development" and os.getenv("ENABLE_DEV_RESET_LINK","false")=="true":message["development_reset_link"]=url
        else:
            try:email_reset(u.email,url)
            except Exception:pass # Avoid leaking account status to unauthenticated clients.
    return message

@app.post("/api/auth/reset-password")
def reset_password(body:ResetIn,db:Session=Depends(get_db)):
    r=db.query(m.PasswordReset).filter_by(token_hash=token_digest(body.token),used=False).first()
    if not r or (r.expires_at.replace(tzinfo=UTC) if r.expires_at.tzinfo is None else r.expires_at)<datetime.now(UTC):raise HTTPException(400,"Invalid or expired reset link")
    u=db.get(m.User,r.user_id);u.password_hash=hash_password(body.password);r.used=True
    db.query(m.Session).filter_by(user_id=u.id).update({"revoked":True});db.commit()
    return {"message":"Password updated. Please log in."}

@app.patch("/api/profile")
def update_profile(body:ProfileIn,u:m.User=Depends(current_user),db:Session=Depends(get_db)):
    from zoneinfo import ZoneInfo,ZoneInfoNotFoundError
    try:ZoneInfo(body.timezone)
    except (ZoneInfoNotFoundError,ValueError):raise HTTPException(422,"Unknown timezone")
    p=db.get(m.Preference,u.id);u.name=body.name;p.theme=body.theme;p.timezone=body.timezone;db.commit()
    return pub_user(u,db)

@app.delete("/api/profile")
def delete_profile(response:Response,u:m.User=Depends(current_user),db:Session=Depends(get_db)):
    # Explicit deletions ensure privacy deletion works even on SQLite without enabled FK cascades.
    tid=[x.id for x in db.query(m.Trade.id).filter_by(user_id=u.id)]
    if tid:db.query(m.TradingNote).filter(m.TradingNote.trade_id.in_(tid)).delete(synchronize_session=False)
    for cls in (m.AIInsight,m.SimulatedOrder,m.TradingNote,m.Trade,m.Position,m.ReplaySession,m.DemoAccount,m.Session,m.PasswordReset,m.Preference):
        db.query(cls).filter_by(user_id=u.id).delete(synchronize_session=False)
    db.delete(u);db.commit();response.delete_cookie(COOKIE,path="/")
    return {"deleted":True}

@app.post("/api/contact",status_code=201)
def contact(body:ContactIn,db:Session=Depends(get_db)):
    db.add(m.ContactMessage(name=body.name,email=str(body.email),message=body.message));db.commit()
    return {"message":"Your message was received."}

@app.get("/api/markets/instruments")
def instruments():
    return [{"symbol":s,"base":s.split("/")[0],"quote":s.split("/")[1],"price":float(quote(s)),"source":"SYNTHETIC DEMONSTRATION"} for s in PAIRS]

@app.get("/api/markets/candles")
def market_candles(symbol:str="EUR/USD",timeframe:str="1h",limit:int=Query(160,ge=10,le=500)):
    if symbol not in PAIRS or timeframe not in FRAMES:raise HTTPException(422,"Unsupported pair/timeframe")
    rows=indicators(candles(symbol,timeframe,limit))
    return {"symbol":symbol,"timeframe":timeframe,"source":"SYNTHETIC DEMONSTRATION","is_live":False,"candles":rows}

@app.get("/api/markets/analysis")
def market_analysis(symbol:str="EUR/USD"):
    if symbol not in PAIRS:raise HTTPException(422,"Unsupported pair")
    r=indicators(candles(symbol,limit=100));last=r[-1];first=r[0]
    return {"symbol":symbol,"source":"SYNTHETIC DEMONSTRATION","price":last["close"],"change_pct":round((last["close"]/first["close"]-1)*100,3),"range":{"low":min(x["low"] for x in r[-24:]),"high":max(x["high"] for x in r[-24:])},"rsi14":last["rsi14"],"atr14":last["atr14"],"sma20":last["sma20"],"ema20":last["ema20"],"volatility_pct":last["volatility_pct"]}

def event_dict(e):
    relevant=[symbol for symbol in PAIRS if e.currency in symbol.split("/")]
    return {"id":e.id,"name":e.name,"country":e.country,"currency":e.currency,"release_at":iso(e.release_at),"impact":e.impact,"previous":e.previous,"forecast":e.forecast,"actual":e.actual,"pairs":relevant,"source":e.source}

@app.get("/api/calendar")
def calendar(day:date|None=None,currency:str|None=None,country:str|None=None,impact:str|None=None,db:Session=Depends(get_db)):
    q=db.query(m.EconomicEvent)
    if currency:q=q.filter(m.EconomicEvent.currency==currency.upper())
    if country:q=q.filter(m.EconomicEvent.country==country)
    if impact:q=q.filter(m.EconomicEvent.impact==impact.upper())
    if day:q=q.filter(m.EconomicEvent.release_at>=datetime.combine(day,datetime.min.time(),UTC),m.EconomicEvent.release_at<datetime.combine(day+timedelta(days=1),datetime.min.time(),UTC))
    return {"events":[event_dict(e) for e in q.order_by(m.EconomicEvent.release_at).limit(100).all()],"source":"SYNTHETIC DEMONSTRATION","timezone":"UTC"}

@app.get("/api/calendar/{event_id}")
def event_detail(event_id:int,db:Session=Depends(get_db)):
    e=db.get(m.EconomicEvent,event_id)
    if not e:raise HTTPException(404,"Event not found")
    releases=db.query(m.EconomicRelease).filter_by(event_id=e.id).order_by(m.EconomicRelease.release_at.desc()).all()
    return {**event_dict(e),"historical_releases":[{"at":iso(r.release_at),"previous":r.previous,"forecast":r.forecast,"actual":r.actual,"source":r.source} for r in releases]}


def position_dict(p):
    return {"id":p.id,"symbol":p.symbol,"side":p.side,"units":float(p.units),"entry":float(p.entry),"stop_loss":float(p.stop_loss),"take_profit":float(p.take_profit),"opened_at":iso(p.opened_at),"status":p.status,"reasoning":p.reasoning,"strategy":p.strategy,"conditions":p.conditions,"replay_session_id":p.replay_session_id}

def trade_dict(t):
    return {"id":t.id,"symbol":t.symbol,"side":t.side,"units":float(t.units),"entry":float(t.entry),"exit":float(t.exit),"stop_loss":float(t.stop_loss) if t.stop_loss is not None else None,"take_profit":float(t.take_profit) if t.take_profit is not None else None,"pnl_usd":float(t.pnl_usd),"risk_reward":float(t.risk_reward) if t.risk_reward is not None else None,"opened_at":iso(t.opened_at),"closed_at":iso(t.closed_at),"notes":t.notes,"strategy":t.strategy,"conditions":t.conditions,"source":t.source,"related_event_id":t.related_event_id}

def spread(symbol):return D("0.008") if symbol=="USD/JPY" else D("0.00008")
def slippage(symbol):return D("0.001") if symbol=="USD/JPY" else D("0.00001")
def executable(symbol,side,mid,opening):
    # Deterministic conservative cost: half spread plus one-tenth of a pip per side.
    sign=1 if ((side=="BUY") == opening) else -1
    return D(str(mid))+sign*(spread(symbol)/2+slippage(symbol))

def mid_for(p,db):
    if p.replay_session_id:
        r=db.get(m.ReplaySession,p.replay_session_id)
        if not r:raise HTTPException(404,"Replay session missing")
        return D(str(REPLAY_BARS[r.cursor]["close"]))
    return quote(p.symbol)

def check_triggers(p,bar):
    # Intrabar both-hit ambiguity resolved conservatively: stop takes precedence.
    if p.side=="BUY":
        if D(str(bar["low"]))<=p.stop_loss:return "STOP_LOSS",p.stop_loss
        if D(str(bar["high"]))>=p.take_profit:return "TAKE_PROFIT",p.take_profit
    else:
        if D(str(bar["high"]))>=p.stop_loss:return "STOP_LOSS",p.stop_loss
        if D(str(bar["low"]))<=p.take_profit:return "TAKE_PROFIT",p.take_profit
    return None,None

def perform_close(p,db,mid,kind="CLOSE",when=None):
    if p.status!="OPEN":raise HTTPException(409,"Position already closed")
    account=db.query(m.DemoAccount).filter_by(id=p.account_id,user_id=p.user_id).with_for_update().first()
    if not account:raise HTTPException(404,"Demo account missing")
    price=executable(p.symbol,p.side,mid,False)
    profit=pnl_usd(p.symbol,p.side,p.units,p.entry,price,quote("GBP/USD"))
    risk=abs(p.entry-p.stop_loss)
    rr=abs(p.take_profit-p.entry)/risk if risk else None
    p.status="CLOSED";account.balance+=profit
    record=m.Trade(user_id=p.user_id,position_id=p.id,symbol=p.symbol,side=p.side,units=p.units,entry=p.entry,exit=price,stop_loss=p.stop_loss,take_profit=p.take_profit,pnl_usd=profit,risk_reward=rr,opened_at=p.opened_at,closed_at=when or datetime.now(UTC),notes=p.reasoning,strategy=p.strategy,conditions=p.conditions,source="REPLAY" if p.replay_session_id else "DEMO")
    db.add(record);db.flush()
    db.add(m.SimulatedOrder(user_id=p.user_id,position_id=p.id,kind=kind,executed_price=price,executed_at=when or datetime.now(UTC),cost_usd=D("0")))
    return record

def auto_close_positions(db,user_id,replay_id=None,bar=None):
    q=db.query(m.Position).filter_by(user_id=user_id,status="OPEN",replay_session_id=replay_id)
    for p in q.with_for_update().all():
        if replay_id is None:
            # Examine only candles after entry: avoid hindsight exits on the entry bar.
            candidates=candles(p.symbol,"15m",500)
            start=p.opened_at.replace(tzinfo=UTC) if p.opened_at.tzinfo is None else p.opened_at
            candidates=[c for c in candidates if datetime.fromisoformat(c["time"])>start]
        else:candidates=[bar]
        for last in candidates:
            kind,level=check_triggers(p,last)
            if kind:
                perform_close(p,db,level,kind,datetime.fromisoformat(last["time"]) if replay_id else None)
                break
    db.commit()

def account_dict(a,db,u):
    positions=db.query(m.Position).filter_by(user_id=u.id,status="OPEN",replay_session_id=None).all()
    unrealized=sum((pnl_usd(p.symbol,p.side,p.units,p.entry,executable(p.symbol,p.side,quote(p.symbol),False),quote("GBP/USD")) for p in positions),D("0"))
    return {"balance":rounded(a.balance),"starting_balance":rounded(a.starting_balance),"equity":rounded(a.balance+unrealized),"unrealized_pnl":rounded(unrealized),"currency":"USD","source":"SIMULATED"}

@app.get("/api/trading/account")
def account(u:m.User=Depends(current_user),db:Session=Depends(get_db)):
    auto_close_positions(db,u.id)
    a=db.query(m.DemoAccount).filter_by(user_id=u.id).first()
    return account_dict(a,db,u)

@app.get("/api/trading/positions")
def positions(u:m.User=Depends(current_user),db:Session=Depends(get_db)):
    auto_close_positions(db,u.id)
    return [position_dict(p) for p in db.query(m.Position).filter_by(user_id=u.id,status="OPEN",replay_session_id=None).order_by(m.Position.opened_at.desc()).all()]

@app.post("/api/trading/positions",status_code=201)
def open_position(body:PositionIn,u:m.User=Depends(current_user),db:Session=Depends(get_db)):
    a=db.query(m.DemoAccount).filter_by(user_id=u.id).with_for_update().first()
    if not a:raise HTTPException(404,"Account not found")
    if body.replay_session_id:
        r=db.query(m.ReplaySession).filter_by(id=body.replay_session_id,user_id=u.id).first()
        if not r:raise HTTPException(404,"Replay not found")
        if body.symbol!="EUR/USD":raise HTTPException(422,"Scenario uses EUR/USD")
        mid=D(str(REPLAY_BARS[r.cursor]["close"]))
        opened_at=datetime.fromisoformat(REPLAY_BARS[r.cursor]["time"])
    else:
        mid=quote(body.symbol);opened_at=datetime.now(UTC)
    price=executable(body.symbol,body.side,mid,True)
    stop=D(str(body.stop_loss));target=D(str(body.take_profit))
    if body.side=="BUY" and not(stop<price<target):raise HTTPException(422,"For BUY: stop-loss < entry < take-profit")
    if body.side=="SELL" and not(target<price<stop):raise HTTPException(422,"For SELL: take-profit < entry < stop-loss")
    units=D(str(body.units))
    usd_rate=D("1") if body.symbol.startswith("USD/") else (quote("EUR/USD") if body.symbol.startswith("EUR/") else quote(body.symbol) if body.symbol.endswith("/USD") else quote("GBP/USD"))
    required_margin=units*usd_rate/D("30")
    # Limit total open leverage across both replay and normal trades.
    held=D("0")
    for existing in db.query(m.Position).filter_by(user_id=u.id,status="OPEN"):
        rate=D("1") if existing.symbol.startswith("USD/") else (quote("EUR/USD") if existing.symbol.startswith("EUR/") else quote(existing.symbol) if existing.symbol.endswith("/USD") else quote("GBP/USD"))
        held+=existing.units*rate/D("30")
    if required_margin+held>a.balance:raise HTTPException(422,"Insufficient virtual margin (30:1 max leverage)")
    p=m.Position(user_id=u.id,account_id=a.id,replay_session_id=body.replay_session_id,symbol=body.symbol,side=body.side,units=units,entry=price,stop_loss=stop,take_profit=target,opened_at=opened_at,reasoning=body.reasoning,strategy=body.strategy,conditions=body.conditions)
    db.add(p);db.flush();db.add(m.SimulatedOrder(user_id=u.id,position_id=p.id,kind="OPEN",executed_price=price,executed_at=opened_at,cost_usd=D("0")));db.commit()
    return position_dict(p)

@app.post("/api/trading/positions/{position_id}/close")
def close_position(position_id:int,u:m.User=Depends(current_user),db:Session=Depends(get_db)):
    p=db.query(m.Position).filter_by(id=position_id,user_id=u.id).with_for_update().first()
    if not p:raise HTTPException(404,"Position not found")
    when=datetime.fromisoformat(REPLAY_BARS[db.get(m.ReplaySession,p.replay_session_id).cursor]["time"]) if p.replay_session_id else None
    row=perform_close(p,db,mid_for(p,db),when=when);db.commit();return trade_dict(row)

@app.get("/api/journal")
def journal(symbol:str|None=None,source:str|None=None,u:m.User=Depends(current_user),db:Session=Depends(get_db)):
    q=db.query(m.Trade).filter_by(user_id=u.id)
    if symbol:q=q.filter_by(symbol=symbol)
    if source:q=q.filter_by(source=source)
    return [trade_dict(t) for t in q.order_by(m.Trade.closed_at.desc()).limit(300).all()]

@app.post("/api/journal/manual",status_code=201)
def add_manual(body:ManualTradeIn,u:m.User=Depends(current_user),db:Session=Depends(get_db)):
    pl=pnl_usd(body.symbol,body.side,body.units,body.entry,body.exit,quote("GBP/USD"))
    rr=abs(D(str(body.take_profit if body.take_profit else body.exit))-D(str(body.entry)))/abs(D(str(body.entry))-D(str(body.stop_loss))) if body.stop_loss and D(str(body.entry))!=D(str(body.stop_loss)) else None
    now=datetime.now(UTC)
    entered=body.opened_at or now;closed=body.closed_at or now
    if entered.tzinfo is None:entered=entered.replace(tzinfo=UTC)
    if closed.tzinfo is None:closed=closed.replace(tzinfo=UTC)
    if closed<entered:raise HTTPException(422,"Close time cannot precede entry time")
    t=m.Trade(user_id=u.id,symbol=body.symbol,side=body.side,units=D(str(body.units)),entry=D(str(body.entry)),exit=D(str(body.exit)),stop_loss=D(str(body.stop_loss)) if body.stop_loss else None,take_profit=D(str(body.take_profit)) if body.take_profit else None,pnl_usd=pl,risk_reward=rr,opened_at=entered,closed_at=closed,notes=body.notes,strategy=body.strategy,conditions=body.conditions,source="MANUAL")
    db.add(t);db.commit();return trade_dict(t)

@app.patch("/api/journal/{trade_id}")
def edit_notes(trade_id:int,body:NotesIn,u:m.User=Depends(current_user),db:Session=Depends(get_db)):
    t=db.query(m.Trade).filter_by(id=trade_id,user_id=u.id).first()
    if not t:raise HTTPException(404,"Trade not found")
    t.notes=body.notes;t.strategy=body.strategy
    db.add(m.TradingNote(trade_id=t.id,user_id=u.id,content=body.notes));db.commit()
    return trade_dict(t)

@app.get("/api/analytics")
def trading_analytics(u:m.User=Depends(current_user),db:Session=Depends(get_db)):
    trades=db.query(m.Trade).filter_by(user_id=u.id).order_by(m.Trade.closed_at).all()
    return analytics(trades)

@app.get("/api/dashboard")
def dashboard(u:m.User=Depends(current_user),db:Session=Depends(get_db)):
    a=db.query(m.DemoAccount).filter_by(user_id=u.id).first()
    t=db.query(m.Trade).filter_by(user_id=u.id).order_by(m.Trade.closed_at.desc()).limit(5).all()
    all_t=db.query(m.Trade).filter_by(user_id=u.id).all()
    upcoming=db.query(m.EconomicEvent).filter(m.EconomicEvent.release_at>=datetime.now(UTC)).order_by(m.EconomicEvent.release_at).limit(4).all()
    return {"account":account_dict(a,db,u),"analytics":analytics(all_t),"recent_trades":[trade_dict(x) for x in t],"events":[event_dict(e) for e in upcoming],"markets":[{"symbol":s,"price":float(quote(s)),"source":"DEMO"} for s in PAIRS],"insight":"Record at least five closed trades to explore patterns." if len(all_t)<5 else f"Based on {len(all_t)} recorded trades, your win rate is {analytics(all_t)['win_rate']}%. Historical outcomes do not predict future performance."}

@app.post("/api/replay/sessions",status_code=201)
def replay_new(u:m.User=Depends(current_user),db:Session=Depends(get_db)):
    r=m.ReplaySession(user_id=u.id,cursor=25);db.add(r);db.commit();return replay_state(r,db)

def replay_state(r,db):
    # Strict cutoff: no future bars, indicator values or announcement actuals reach client.
    visible=REPLAY_BARS[:r.cursor+1]
    positions=db.query(m.Position).filter_by(replay_session_id=r.id,status="OPEN").all()
    return {"id":r.id,"scenario":SCENARIO,"cursor":r.cursor,"finished":r.cursor==len(REPLAY_BARS)-1,"candles":indicators(visible),"positions":[position_dict(p) for p in positions],"event":{"name":"Simulated US inflation surprise","release_index":56,"released":r.cursor>=56,"actual":"Synthetic scenario: above hypothetical forecast" if r.cursor>=56 else None},"source":"SYNTHETIC DEMONSTRATION"}

@app.get("/api/replay/sessions/{sid}")
def replay_get(sid:int,u:m.User=Depends(current_user),db:Session=Depends(get_db)):
    r=db.query(m.ReplaySession).filter_by(id=sid,user_id=u.id).first()
    if not r:raise HTTPException(404,"Replay not found")
    return replay_state(r,db)

@app.post("/api/replay/sessions/{sid}/advance")
def replay_advance(sid:int,body:AdvanceIn,u:m.User=Depends(current_user),db:Session=Depends(get_db)):
    r=db.query(m.ReplaySession).filter_by(id=sid,user_id=u.id).with_for_update().first()
    if not r:raise HTTPException(404,"Replay not found")
    until=min(r.cursor+body.steps,len(REPLAY_BARS)-1)
    for i in range(r.cursor+1,until+1):
        auto_close_positions(db,u.id,r.id,REPLAY_BARS[i])
    r.cursor=until;db.commit();return replay_state(r,db)

RULEBOOK={"rsi":"RSI is a momentum oscillator. Readings above 70 are often called overbought and below 30 oversold; neither guarantees a reversal.","atr":"ATR measures recent price-range volatility, not direction. Traders sometimes use it to contextualize risk distances.","moving average":"A moving average smooths prices; SMA weights observations equally while EMA weights newer observations more.","cpi":"Consumer Price Index measures changes in prices. Surprises can affect expectations about interest rates and currency volatility.","stop":"A stop-loss sets a planned exit threshold but cannot remove slippage or market risk.","leverage":"Leverage amplifies both gains and losses. PipMora's simulated margin cap is 30:1; this is not a recommended leverage level."}

def coach_evidence(question,t,summary):
    q=question.lower()
    if t:
        out=[f"Trade #{t.id}: {t.side} {t.symbol}, {float(t.units):,.0f} units. Executed entry {float(t.entry):.5f}, exit {float(t.exit):.5f}; recorded result ${float(t.pnl_usd):+,.2f} (USD)."]
        if t.stop_loss is not None:out.append(f"Recorded stop-loss {float(t.stop_loss):.5f}, take-profit {float(t.take_profit):.5f}.")
        if t.notes:out.append(f"Your recorded reasoning: {t.notes[:400]}")
        if t.pnl_usd<0:out.append("The executed price moved against the position after costs. The recorded data alone does not establish why the market moved.")
        else:out.append("This recorded outcome does not establish a repeatable advantage.")
        out.append("Review entry criteria, position size, stop distance and whether the executed trade matched your plan. No future return is implied.")
        return " ".join(out)
    for term,answer in RULEBOOK.items():
        if term in q:return answer
    if summary["total_trades"]==0:return "I have no closed trades to review yet. Use Demo Trading or add a trade to your journal, then ask me about its risk, outcome or consistency."
    return f"Across {summary['total_trades']} recorded trades: win rate {summary['win_rate']}%, total P/L ${summary['net_pnl']:+,.2f}, maximum recorded drawdown {summary['max_drawdown_pct']}%. " +( "The sample is too small to infer a stable pattern." if summary["insufficient_sample"] else "These are historical sample metrics, not predictions.")

@app.post("/api/coach")
async def coach(body:CoachIn,u:m.User=Depends(current_user),db:Session=Depends(get_db)):
    trades=db.query(m.Trade).filter_by(user_id=u.id).order_by(m.Trade.closed_at.desc()).all()
    t=None
    if body.trade_id:
        t=next((item for item in trades if item.id==body.trade_id),None)
        if not t:raise HTTPException(404,"Trade not found")
    elif ("trade" in body.question.lower() or "last" in body.question.lower()) and trades:t=trades[0]
    summary=analytics(trades)
    result=coach_evidence(body.question,t,summary);mode="RULE_BASED_EVIDENCE"
    # Optional external provider receives only structured facts, never an untrusted browser-generated P/L.
    if os.getenv("AI_EXTERNAL_ENABLED","false").lower()=="true" and os.getenv("AI_API_KEY"):
        try:
            import httpx
            payload={"model":os.getenv("AI_MODEL","gpt-4.1-mini"),"temperature":0.2,"messages":[{"role":"system","content":"You are PipMora's educational Forex coach. Explain only the supplied facts, distinguish demo data, never forecast, guarantee profit, or recommend specific trades. Financial arithmetic is already calculated; do not recalculate."},{"role":"user","content":f"Question: {body.question}\nVerified evidence: {result}\nHistorical metrics: {summary['total_trades']} trades; win rate {summary['win_rate']}%, P/L ${summary['net_pnl']}."}]}
            async with httpx.AsyncClient(timeout=12) as client:
                res=await client.post(os.getenv("AI_BASE_URL","https://api.openai.com/v1").rstrip("/")+"/chat/completions",headers={"Authorization":"Bearer "+os.environ["AI_API_KEY"]},json=payload)
                res.raise_for_status();result=res.json()["choices"][0]["message"]["content"];mode="LLM_GROUNDED"
        except Exception: mode="RULE_BASED_FALLBACK"
    db.add(m.AIInsight(user_id=u.id,trade_id=t.id if t else None,question=body.question,answer=result,mode=mode));db.commit()
    return {"answer":result,"mode":mode,"trade_id":t.id if t else None,"sample_size":len(trades),"source":"RECORDED USER TRADES / SYNTHETIC DEMO PRICES"}

@app.get("/api/coach/history")
def coach_history(u:m.User=Depends(current_user),db:Session=Depends(get_db)):
    a=db.query(m.AIInsight).filter_by(user_id=u.id).order_by(m.AIInsight.created_at.desc()).limit(20).all()
    return [{"id":i.id,"question":i.question,"answer":i.answer,"mode":i.mode,"created_at":iso(i.created_at)} for i in a]
