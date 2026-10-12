"""Persisted domain data. Trades are append-only outcomes; notes remain editable."""
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import String, Integer, DateTime, ForeignKey, Numeric, Boolean, Text, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .db import Base

def now_utc(): return datetime.now(timezone.utc)

def money(): return mapped_column(Numeric(18, 6), default=Decimal("0"))

class User(Base):
    __tablename__="users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)

class Preference(Base):
    __tablename__="user_preferences"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id",ondelete="CASCADE"),primary_key=True)
    theme: Mapped[str] = mapped_column(String(10),default="dark")
    timezone: Mapped[str] = mapped_column(String(70),default="UTC")

class Session(Base):
    __tablename__="sessions"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id",ondelete="CASCADE"),index=True)
    token_hash: Mapped[str] = mapped_column(String(64),unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked: Mapped[bool] = mapped_column(Boolean,default=False)

class PasswordReset(Base):
    __tablename__="password_resets"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id",ondelete="CASCADE"))
    token_hash: Mapped[str] = mapped_column(String(64),unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used: Mapped[bool] = mapped_column(Boolean,default=False)

class Instrument(Base):
    __tablename__="instruments"
    symbol: Mapped[str] = mapped_column(String(12),primary_key=True)
    base_currency: Mapped[str] = mapped_column(String(3))
    quote_currency: Mapped[str] = mapped_column(String(3))
    label: Mapped[str] = mapped_column(String(80))

class MarketCandle(Base):
    __tablename__="market_candles"
    id: Mapped[int] = mapped_column(primary_key=True)
    symbol: Mapped[str] = mapped_column(ForeignKey("instruments.symbol"),index=True)
    timeframe: Mapped[str] = mapped_column(String(8))
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    open: Mapped[Decimal] = money()
    high: Mapped[Decimal] = money()
    low: Mapped[Decimal] = money()
    close: Mapped[Decimal] = money()
    source: Mapped[str] = mapped_column(String(20),default="DEMONSTRATION")
    __table_args__=(UniqueConstraint("symbol","timeframe","timestamp"),)

class EconomicEvent(Base):
    __tablename__="economic_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150))
    country: Mapped[str] = mapped_column(String(70))
    currency: Mapped[str] = mapped_column(String(3),index=True)
    release_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),index=True)
    impact: Mapped[str] = mapped_column(String(10))
    previous: Mapped[str | None] = mapped_column(String(40),nullable=True)
    forecast: Mapped[str | None] = mapped_column(String(40),nullable=True)
    actual: Mapped[str | None] = mapped_column(String(40),nullable=True)
    source: Mapped[str] = mapped_column(String(30),default="SYNTHETIC DEMO")

class EconomicRelease(Base):
    __tablename__="economic_releases"
    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("economic_events.id",ondelete="CASCADE"),index=True)
    release_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    actual: Mapped[str | None] = mapped_column(String(40))
    forecast: Mapped[str | None] = mapped_column(String(40))
    previous: Mapped[str | None] = mapped_column(String(40))
    source: Mapped[str] = mapped_column(String(30),default="SYNTHETIC DEMO")

class DemoAccount(Base):
    __tablename__="demo_accounts"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id",ondelete="CASCADE"),unique=True)
    balance: Mapped[Decimal] = mapped_column(Numeric(18,6),default=Decimal("10000"))
    starting_balance: Mapped[Decimal] = mapped_column(Numeric(18,6),default=Decimal("10000"))

class ReplaySession(Base):
    __tablename__="replay_sessions"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id",ondelete="CASCADE"),index=True)
    cursor: Mapped[int] = mapped_column(Integer,default=25)
    scenario: Mapped[str] = mapped_column(String(50),default="EURUSD_US_CPI_SYNTHETIC")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),default=now_utc)

class Position(Base):
    __tablename__="positions"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id",ondelete="CASCADE"),index=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("demo_accounts.id"))
    replay_session_id: Mapped[int | None] = mapped_column(ForeignKey("replay_sessions.id"),nullable=True)
    symbol: Mapped[str] = mapped_column(ForeignKey("instruments.symbol"))
    side: Mapped[str] = mapped_column(String(4))
    units: Mapped[Decimal] = money()
    entry: Mapped[Decimal] = money()
    stop_loss: Mapped[Decimal] = money()
    take_profit: Mapped[Decimal] = money()
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),default=now_utc)
    status: Mapped[str] = mapped_column(String(10),default="OPEN")
    reasoning: Mapped[str] = mapped_column(Text,default="")
    strategy: Mapped[str] = mapped_column(String(80),default="")
    conditions: Mapped[str] = mapped_column(Text,default="")
    __table_args__=(Index("idx_positions_user_status","user_id","status"),)

class SimulatedOrder(Base):
    __tablename__="simulated_orders"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id",ondelete="CASCADE"),index=True)
    position_id: Mapped[int] = mapped_column(ForeignKey("positions.id"),index=True)
    kind: Mapped[str] = mapped_column(String(10))
    executed_price: Mapped[Decimal] = money()
    executed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),default=now_utc)
    cost_usd: Mapped[Decimal] = money()

class Trade(Base):
    __tablename__="trades"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id",ondelete="CASCADE"),index=True)
    position_id: Mapped[int | None] = mapped_column(ForeignKey("positions.id"),unique=True,nullable=True)
    symbol: Mapped[str] = mapped_column(String(12))
    side: Mapped[str] = mapped_column(String(4))
    units: Mapped[Decimal] = money()
    entry: Mapped[Decimal] = money()
    exit: Mapped[Decimal] = money()
    stop_loss: Mapped[Decimal | None] = mapped_column(Numeric(18,6),nullable=True)
    take_profit: Mapped[Decimal | None] = mapped_column(Numeric(18,6),nullable=True)
    pnl_usd: Mapped[Decimal] = money()
    risk_reward: Mapped[Decimal | None] = mapped_column(Numeric(18,4),nullable=True)
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    closed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),default=now_utc)
    notes: Mapped[str] = mapped_column(Text,default="")
    strategy: Mapped[str] = mapped_column(String(80),default="")
    conditions: Mapped[str] = mapped_column(Text,default="")
    related_event_id: Mapped[int | None] = mapped_column(ForeignKey("economic_events.id"),nullable=True)
    source: Mapped[str] = mapped_column(String(10),default="DEMO")

class TradingNote(Base):
    __tablename__="trading_notes"
    id: Mapped[int] = mapped_column(primary_key=True)
    trade_id: Mapped[int] = mapped_column(ForeignKey("trades.id",ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id",ondelete="CASCADE"))
    content: Mapped[str] = mapped_column(Text,default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),default=now_utc)

class AIInsight(Base):
    __tablename__="ai_insights"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id",ondelete="CASCADE"),index=True)
    trade_id: Mapped[int | None] = mapped_column(ForeignKey("trades.id"),nullable=True)
    question: Mapped[str] = mapped_column(Text)
    answer: Mapped[str] = mapped_column(Text)
    mode: Mapped[str] = mapped_column(String(30))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),default=now_utc)

class ContactMessage(Base):
    __tablename__="contact_messages"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(320))
    message: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),default=now_utc)
