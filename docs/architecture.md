# Phase 1 technical notes

## Data flow

Browser UI → credentialed HTTPS calls → FastAPI validation + opaque session check → SQLAlchemy/PostgreSQL → deterministic Python financial arithmetic → user journal and analytics → optional, grounded AI explanation.

Key tables: users, user_preferences, sessions, password_resets, instruments, market_candles, economic_events, economic_releases, demo_accounts, simulated_orders, positions, trades, trading_notes, ai_insights, replay_sessions, contact_messages.

SQLite is for local development. The Alembic migration enables PostgreSQL installation. User IDs scope all private reads and mutations. Python/Decimal executes financial arithmetic; AI does not.

## Safety constraints

The order entry price is the synthetic mid plus half a fixed spread and deterministic slippage. The close price is on the opposite side of the spread, with equivalent slippage. Spread assumptions are 0.8 pip for non-JPY and 0.8 pip for JPY pairs; slippage 0.1 pip per leg. No hidden backend fee. Maximum virtual margin usage is 30:1. Stop-loss and take-profit checks use candle high/low and resolve ambiguous both-hit bars against the trader. Economic event releases and replay candles are synthetic. Manual journal entries do not change cash balance.

These simplifications are explicit and do not model volume, gaps, counterparty risk, swap, financing, realistic market impact or liquidity. Do not compare these results to broker execution.

## Deployment checks

1. Configure DNS and TLS; use the exact browser origin in `FRONTEND_ORIGIN`.
2. Set HTTPS/secure cookie options and disable development reset-link responses.
3. Apply `alembic upgrade head`; verify PostgreSQL permissions and backups.
4. Run backend pytest, frontend lint/build and manual signup → demo trade → close → AI review → persistence acceptance checks.
5. Connect SMTP; configure rate limits, access logs, incident response and privacy/terms review.
6. Monitor container health and database storage. Never publish `.env` or API keys.
