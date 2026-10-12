# GitHub repository & deployment guide

The PipMora Phase 1 source is now published at
https://github.com/faridbagheri/PipMora.

The repository contains Next.js, FastAPI, database migrations, tests, CI,
Docker Compose, the public marketing preview and the Render deployment Blueprint.
CI tests and frontend build were confirmed passing after initial import.

## Public preview

Enable Pages via **Settings → Pages → Build and deployment → GitHub Actions**.
Then run **Public PipMora Preview** from Actions. Preview URL after successful
publication: https://faridbagheri.github.io/PipMora/.

## Full-stack website

Use `render.yaml` through Render Blueprints or the Docker Compose stack locally.
Read `docs/DEPLOYMENT.md`; public hosting and PostgreSQL require account setup
and potentially paid subscriptions. Do not commit `.env`, credentials or real
financial data.
