# PipMora

**AI-Powered Forex Intelligence & Learning Platform**  
*Understand the Market. Learn from Every Trade.*

PipMora is an educational, full-stack Forex research and paper-trading MVP. It combines a simulated market workspace, fictional economic calendar, journal-driven trading analytics, historical-style replay, and an evidence-based AI Coach. The application does **not** execute real-money orders, connect to broker accounts, provide investment recommendations, or guarantee performance. Trading simulations, analytics, and the backend market-data service use **synthetic demonstration data**. The public website and Next.js `/live-charts` page separately embed **TradingView-supplied Forex charts** for EUR/USD, GBP/USD, and USD/JPY. Those third-party charts are not used for fills, user-account calculations, or AI Coach evidence.

## Phase 1 features

- Responsive marketing website with product, pricing, contact, legal and risk pages, and original editable SVG wordmark.
- Database-backed registration, login, logout, reset-password workflow, Argon2id hashing, revocable HttpOnly sessions, profile preferences and deletion.
- Private dashboard: market watch, scheduled events, virtual balance, realized P/L, recent trading insights and quick actions.
- Six synthetic Forex pairs and OHLC charts with candlestick/line modes, timeframes, panning/zooming, SMA20, EMA20, RSI14, ATR14 and sample volatility.
- Currency/date/country/impact-filterable economic calendar; events and values are explicitly fictional and not scraped from financial providers.
- Persistent paper-trading accounts, simulated BUY/SELL positions, stops, targets, execution spreads and slippage, margin checks, closing orders and journal reconciliation.
- Journal with automatic closed trades, manual trade entry, editable notes, strategy tags and filters.
- Calculated P/L, win rate, average win/loss, profit factor, maximum drawdown, reward/risk and per-pair analytics; insufficient sample warnings.
- Evidence-based PipMora AI Coach with persistent reviews and offline rule mode; optional OpenAI-compatible LLM endpoint with only structured trade facts.
- One synthetic, look-ahead-safe market replay with incremental candles, a gated macro event, simulated positions and journal handoff.
- Docker Compose, initial Alembic migration, API documentation at `/docs`, and GitHub Actions tests and frontend build.

## Live Forex charts (separate from demo trading)

- Public GitHub Pages market view: [site/markets.html](site/markets.html) (`https://faridbagheri.github.io/PipMora/markets.html`).
- Next.js market view: `/live-charts`; the homepage also embeds EUR/USD and GBP/USD charts.
- Uses the official TradingView Advanced Chart embed with provider attribution. Forex feeds are described as real-time by TradingView, subject to data availability, symbol/venue, and the visitor's connection. If the third-party script is blocked, users can open the TradingView symbol links.
- Embeds require internet access; no data is downloaded into PipMora's database or sent to the paper-trading engine. The synthetic market ticker and demo account positions remain **explicitly labeled synthetic**. Do not confuse third-party market charts with the simulator's execution rate.

## Architecture

```text
apps/web              Next.js 15, React 19, TypeScript, custom responsive CSS
services/api/app      FastAPI, SQLAlchemy 2, Argon2id, Pydantic 2
services/api/tests    Pytest integration & financial calculation tests
database/migrations   Versioned Alembic PostgreSQL/SQLite migration
.github/workflows     Automated backend tests, migrations, frontend checks
docker-compose.yml    PostgreSQL 16 + API + Next.js
```

Requests from the browser use `credentials: include` and are authorized by secure opaque session cookies. Records are filtered by authenticated user ID. The backend alone calculates financial outcomes and persists all private records.

## Local installation

Requirements: Python 3.12+, Node.js 22+, npm, and optionally Docker Compose.

**Option A: Docker (PostgreSQL, API and website):**

```bash
cp .env.example .env
# Change POSTGRES_PASSWORD in .env to a unique local secret.
docker compose up --build
```

Open [http://localhost:3000](http://localhost:3000) for the website and [http://localhost:8000/docs](http://localhost:8000/docs) for the API. PostgreSQL uses a persistent named volume. The API container runs Alembic migrations before launching.

**Option B: Development without Docker (SQLite fallback):**

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r services/api/requirements.txt
# From the repository root; default DATABASE_URL is SQLite.
PYTHONPATH=services/api uvicorn app.main:app --reload --port 8000
# Second terminal:
cd apps/web
npm install
npm run dev
```

In local SQLite mode the API creates tables for convenience. Use `alembic upgrade head` for managed database creation, particularly with PostgreSQL. Environment variables are listed in `.env.example`. The browser calls the website's `/api` routes, which forward to FastAPI using `API_INTERNAL_HOSTPORT` (Docker/Render) or `API_PROXY_URL` (local development); `NEXT_PUBLIC_API_URL` is normally left empty.

> Password recovery: The development reset link is exposed only when `APP_ENV=development` and `ENABLE_DEV_RESET_LINK=true`; configure SMTP before any public deployment and set those flags to production/false. In production, do not expose reset tokens in API responses.

## Tests

```bash
pip install -r services/api/requirements.txt
python -m pytest services/api/tests -q
cd apps/web && npm install && npm run lint && npm run build
```

A browser end-to-end smoke test is also configured under `apps/web/e2e/phase1.spec.ts`. GitHub Actions provisions temporary FastAPI and Next.js servers with Chromium, runs signup → market/calendar exploration → simulated trade → journal → AI Coach → analytics, and publishes failure diagnostics. To run locally, install Playwright (`npx playwright install chromium`), start the API and web servers, then run `cd apps/web && npm run test:e2e`.

The integration suite covers registration, simulated trade opening/closing, journal persistence across login, AI review evidence, account deletion, password reset, manual JPY-to-USD P/L conversion, unauthorized replay access and replay data cutoff. Browser end-to-end automation is configured in GitHub Actions; PostgreSQL concurrency/load testing and security penetration testing remain follow-up work.

## Public GitHub preview and full-stack hosting

The public interactive product preview (`site/index.html`) is separate from the
full Next.js / FastAPI / PostgreSQL application. Once repository Pages is enabled
(Settings → Pages → Source: GitHub Actions), the preview deploy workflow can publish
it to `https://faridbagheri.github.io/PipMora/`. The preview displays only synthetic
example data and does not provide accounts or database-backed trades. Its [interactive trading lab](site/lab.html) demonstrates simulated orders, replay, journal, and rule-based coaching. Lab activity is held only in each visitor's browser local storage and must not be presented as the authenticated application.

The complete application has a `render.yaml` Blueprint with two services and a
managed PostgreSQL database. It uses a same-origin Next.js `/api` gateway to keep
browser authentication cookies on the website's own origin. **Render has not been
provisioned.** Deploying the application requires authorizing a hosting account,
reviewing paid resource costs, and configuring SMTP and security controls. See
[`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) for exact instructions.

## Deployment

Use the included `render.yaml` Blueprint for two Docker web services and managed PostgreSQL, or equivalent infrastructure. The browser should call relative `/api/*` paths (leave `NEXT_PUBLIC_API_URL` empty); the Next.js server forwards the requests over the hosting provider's private network using `API_INTERNAL_HOSTPORT`. Set a production `FRONTEND_ORIGIN`, `APP_ENV=production`, `COOKIE_SECURE=true` and `ENABLE_DEV_RESET_LINK=false`. Apply `alembic upgrade head` before starting the API and configure SMTP for password recovery. Public infrastructure has not been provisioned, and deploy costs and legal/security controls must be reviewed first.

The Compose file is a local proof-of-deployment setup, **not** an Internet-hardened production reference: add TLS, backups, observability, rate limits, secrets management, privacy-policy review, automated end-to-end tests, and regulatory assessment before launch. Do not enable an external LLM unless you understand its data-processing implications.

## Data fidelity & modeling assumptions

Price data comes from a reproducible mathematical generator, **not** an FX data vendor; no actual central bank release data is included. The calendar is synthetic and purposely omits unavailable forecast/actual figures. Fixed conservative spread and slippage are modeled on orders. Spot trade result is converted into USD for the six defined pairs; this is a learning simulator, not a brokerage-grade pricing and margin engine. Replay scenario data is synthetic and future bars/events are intentionally hidden. Historical observations do not predict future performance.

## Responsible AI

Without `AI_EXTERNAL_ENABLED=true` and a backend `AI_API_KEY`, the coach returns grounded deterministic explanations with an explicit rule-based mode label. If configured for an external OpenAI-compatible endpoint, the backend supplies the already-computed calculations and relevant recorded context, keeps API credentials server-side, and falls back safely to rule mode if external inference fails. No automatic investment signals or orders are implemented.

## Roadmap (not yet implemented)

Real licensed market-data integrations, validated economic-release history, advanced strategies and model-based coaching, richer scenario libraries, multilingual interfaces, and deeper performance segmentation are future phases. Payment processing, brokerage execution, and any regulated financial functionality remain outside this MVP pending separate authorization and legal review.

## Risk statement

PipMora is strictly educational and analytical in Phase 1. Foreign exchange and leverage can lead to substantial losses. Synthetic trading results cannot predict investment returns or reproduce all real market conditions.

## License

All rights reserved pending a licensing decision by the project owner (see `LICENSE`).
