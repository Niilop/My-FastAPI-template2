# FastAPI Template

A FastAPI backend with PostgreSQL, authentication, file uploads, and a React + TypeScript frontend. Python 3.12+ dependencies use uv; the frontend uses Node 24 and npm.

- Registration and login by email or username, Argon2 password hashing, expiring JWTs.
- SQLAlchemy models and Alembic migrations.
- Per-user CSV catalog with bounded uploads and generated filenames.
- Rate limits on registration, login, uploads, and background job submission.
- A route/service example and an in-process background job example.
- Liveness and database readiness endpoints, configurable CORS, automated tests.

## Local development

Run commands from the repository root. Install [uv](https://docs.astral.sh/uv/getting-started/installation/) if needed, then:

```bash
uv sync --all-packages
cp .env.example .env
uv run --no-sync python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Paste the generated value into `SECRET_KEY` in `.env`. Set `DATABASE_URL` to a **dedicated, empty database** in your PostgreSQL instance (for example, in `~/code/devstack`). PostgreSQL extensions and Redis are not required. The repository does not start another database server.

```bash
uv run --no-sync alembic -c backend/alembic.ini upgrade head
uv run --no-sync uvicorn backend.main:app --reload
```

Open <http://127.0.0.1:8000/docs> to try the API. Registration requires a password of 12–128 characters and a username of 3–100 letters, digits, dots, underscores, or hyphens. Login uses form fields `username` and `password`; `username` can contain either the username or email.

To install only backend dependencies, use `uv sync --package backend`. Use `uv sync --all-packages` to include the Python development tools.

Start the frontend in another terminal:

```bash
cd frontend
npm ci
npm run dev
```

Open <http://localhost:5173>. Vite forwards `/api/*` requests to the backend on port 8000, so no CORS change is needed. The UI includes registration/login, protected account and dataset pages, CSV uploads/catalog browsing, and the example endpoint. Tokens stay in memory; reloading the page signs you out. See [frontend/README.md](frontend/README.md) for configuration, structure, and browser tests.

## Configuration

The backend reads the repository-root `.env` regardless of the working directory. Environment variables override it. See [.env.example](.env.example) for the full configuration.

| Setting | Default / requirement |
| --- | --- |
| `DATABASE_URL` | Required; `postgresql+psycopg://user:password@host:5432/database` |
| `SECRET_KEY` | Required; random secret of at least 32 bytes |
| `DEBUG` | `false` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` |
| `CORS_ORIGINS` | Empty; explicit comma-separated URLs or a JSON array |
| `DATA_DIR` | Repository `data/` directory |
| `MAX_UPLOAD_BYTES` | `10485760` (10 MiB) |
| `MAX_DATASETS_PER_USER` | `10` |

JWT signing uses HS256. Keep `.env` out of Git. Existing `postgresql://` URLs are normalized to use psycopg 3. URL-encode special characters in database credentials.

## Docker

The backend installs from `uv.lock`; the frontend builds from `frontend/package-lock.json` and is served by unprivileged Nginx. Compose runs the backend; the UI is an optional profile. Uploaded files live in a named volume.

Set `.env`'s `DATABASE_URL` to an address reachable **from the container**. For a host-published devstack database, use `host.docker.internal` instead of `localhost` (the host-gateway mapping is included). Ensure that PostgreSQL's published port is reachable from that Docker network. Alternatively, attach the backend to your devstack network and use its database service hostname.

```bash
docker compose build
docker compose run --rm backend alembic -c backend/alembic.ini upgrade head
docker compose up -d
# Include the React frontend on port 5173:
docker compose --profile ui up --build -d
```

Migrations are an explicit deployment step. Run them once before starting new application processes. The image does not enable hot reload.

## API

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/auth/register` | Create user (201) |
| POST | `/auth/login` | Issue bearer token |
| GET | `/auth/me` | Current user |
| POST | `/example/` | Public route/service example |
| POST | `/example/async` | Authenticated background example (202) |
| GET | `/jobs/{job_id}` | Current user's job status/result |
| POST | `/data/upload` | Upload UTF-8 CSV as multipart `file`, `name`, optional `description` (201) |
| GET | `/data/catalog` | Current user's datasets |
| GET | `/data/count` | Dataset quota usage |
| GET | `/health` | Process liveness |
| GET | `/ready` | Database connectivity (503 on failure) |

`GET /data/` remains an alias for the catalog. CSV metadata includes row count, column count, column names, and empty-value counts. Files must have unique nonempty headers and consistent row widths. Server filesystem paths are excluded from API responses.

Background jobs use FastAPI's in-process tasks and a separate database session. They are suitable for short tasks; process termination can leave jobs pending or running. Add a durable queue when your application needs retries or recovery. Rate limits use process-local memory; configure shared storage before deploying multiple workers. Put request-body limits at your reverse proxy as well: upload limits are enforced after multipart parsing and while copying the file. `/ready` checks database connectivity, not migration status.

## Project layout

```text
backend/
  api/endpoints/    HTTP routes and dependencies
  core/            Settings, database sessions, rate limiting
  models/          ORM models and request/response schemas
  services/        Authentication, CSV processing, background jobs
  alembic/         Schema migrations
  main.py          App factory and health endpoints
frontend/src/      React pages, routing, session state, and API client
frontend/tests/    Desktop and mobile browser tests
tests/             Isolated automated tests and REST client examples
```

Add models in `backend/models/database.py`, request/response schemas in `schemas.py`, business logic in `services/`, and routers in `api/endpoints/`. Register new routers in `create_app()`.

```bash
uv run --no-sync alembic -c backend/alembic.ini revision --autogenerate -m "describe change"
uv run --no-sync alembic -c backend/alembic.ini upgrade head
```

Review generated migrations before applying them.

**Migration compatibility:** this cleanup replaces the old migration history with `0001_core`, intended for new databases. Do not apply or stamp it over an existing installation. Existing data needs a separate, reviewed migration/export plan; previous password hashes and tokens are not compatible with the new authentication setup. No existing database is modified by checking out these changes.

## Checks

```bash
uv sync --all-packages --locked
uv run --no-sync ruff check .
uv run --no-sync ruff format --check .
uv run --no-sync pytest
```

Backend tests use isolated SQLite databases and temporary upload directories, with no running API or external services. CI also checks migration upgrade, schema consistency, and downgrade on PostgreSQL. The frontend has separate build, lint, and browser checks:

```bash
cd frontend
npm ci
npm run lint
npm run build
npx playwright install chromium
npm test
```

Authentication follows the libraries used in [FastAPI's security guide](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/); container dependency installation follows [uv's Docker guide](https://docs.astral.sh/uv/guides/integration/docker/).
