# Public deployment — PipMora Phase 1

## Option A — public preview with GitHub Pages

A standalone **synthetic, interactive public preview** lives in `site/index.html`. It is
not the full authenticated application.

1. Open the [repository Pages settings](https://github.com/faridbagheri/PipMora/settings/pages).
2. Under **Build and deployment**, set **Source → GitHub Actions** and save.
3. Open [Actions → Public PipMora Preview](https://github.com/faridbagheri/PipMora/actions/workflows/pages.yml).
4. Run the workflow from `main` and check the deployment succeeded.
5. Once GitHub confirms publication, share `https://faridbagheri.github.io/PipMora/`.

The default GitHub Actions token cannot enable Pages for a new repository. The workflow
therefore requires the repository owner to enable Pages once in Settings.

## Option B — full application with Render Blueprint

`render.yaml` defines the API service, Next.js frontend and managed PostgreSQL.
The Next.js server proxies `/api/*` to the API over Render's private network so that
session cookies remain first-party on the website domain. The FastAPI container applies
Alembic migrations at startup. The SQLAlchemy connection URI is normalized for psycopg3.

1. In Render, choose **New → Blueprint**, connect `faridbagheri/PipMora` and use `render.yaml`.
2. Review **paid plan costs** for two web services and PostgreSQL. Approve only if acceptable.
3. Confirm the frontend origin is injected into the API service's `FRONTEND_ORIGIN` and
   the backend private hostname and port into the web service's `API_INTERNAL_HOSTPORT`.
4. Configure SMTP variables (`SMTP_HOST`, `SMTP_FROM`, `SMTP_USER`, `SMTP_PASSWORD`,
   `SMTP_PORT`, `SMTP_TLS`) for password recovery before inviting real users.
5. Keep `APP_ENV=production`, `COOKIE_SECURE=true`, and `ENABLE_DEV_RESET_LINK=false`.
6. Verify public HTTPS, `/api/health`, signup, login, simulated trade opening/closing,
   journal persistence after refresh and evidence-backed AI Coach responses.

**No Render resources have been provisioned.** A connection and the owner's confirmation
of hosting costs are still needed. The public deployment is not production security
certified: undertake rate limiting, email verification, backup/restore testing,
GDPR and financial disclosures review, logging, monitoring and security assessment
before a broad launch.

## Local Docker run

From the repository root, copy `.env.example` to `.env`, set a strong
`POSTGRES_PASSWORD`, then run `docker compose up --build`. Open
`http://localhost:3000` and verify `http://localhost:3000/api/health`.
