# FastAPI Template

A FastAPI backend with PostgreSQL, authentication, a small CRUD example, and a React + TypeScript frontend. Python 3.12+ dependencies use uv; the frontend uses Node 24 and npm.

- Registration and login by email or username, Argon2 password hashing, expiring JWTs.
- SQLAlchemy models and Alembic migrations.
- User-owned items with a title, description, timestamps, and paginated CRUD endpoints.
- Rate limits on registration, login, item writes, and background job submission.
- A route/service example and an in-process background job example.
- Liveness and database readiness endpoints, configurable CORS, automated tests.

## Development context

The [md/](md/README.md) folder contains the project context, implemented architecture, development workflow, current status, decisions, and an implementation-plan template. Start there when adapting this repository to a new project or handing work between developers and AI agents. Root [AGENTS.md](AGENTS.md) directs coding agents to that context and explains what to keep updated.

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

Open <http://localhost:5173>. Vite forwards `/api/*` requests to the backend on port 8000, so no CORS change is needed. The UI includes registration/login, protected account and items pages, create/edit/delete forms, and the example endpoint. Tokens stay in memory; reloading the page signs you out. See [frontend/README.md](frontend/README.md) for configuration, structure, and browser tests.

## Configuration

The backend reads the repository-root `.env` regardless of the working directory. Environment variables override it. See [.env.example](.env.example) for the full configuration.

| Setting | Default / requirement |
| --- | --- |
| `DATABASE_URL` | Required; `postgresql+psycopg://user:password@host:5432/database` |
| `SECRET_KEY` | Required; random secret of at least 32 bytes |
| `DEBUG` | `false` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` |
| `CORS_ORIGINS` | Empty; explicit comma-separated URLs or a JSON array |

JWT signing uses HS256. Keep `.env` out of Git. Existing `postgresql://` URLs are normalized to use psycopg 3. URL-encode special characters in database credentials.

## Docker

The backend installs from `uv.lock`; the frontend builds from `frontend/package-lock.json` and is served by unprivileged Nginx. Compose runs the backend; the UI is an optional profile. Application data lives in PostgreSQL.

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
| POST | `/items` | Create an item (201) |
| GET | `/items` | Current user's items and total count; `limit` (1–100, default 20), `offset` (default 0) |
| GET | `/items/{item_id}` | Read an owned item |
| PUT | `/items/{item_id}` | Replace an owned item's title and description |
| DELETE | `/items/{item_id}` | Delete an owned item (204) |
| GET | `/health` | Process liveness |
| GET | `/ready` | Database connectivity (503 on failure) |

Item writes accept JSON with `title` (1–255 characters after trimming) and optional `description` (up to 5,000 characters, default empty). `PUT` replaces both fields; omitting `description` clears it. The server assigns the owner from the signed-in user; clients cannot supply or change it. Missing items and other users' items both return 404. Lists return `{ "items": [...], "total": 0 }`, ordered by newest ID first.

Background jobs use FastAPI's in-process tasks and a separate database session. They are suitable for short tasks; process termination can leave jobs pending or running. Add a durable queue when your application needs retries or recovery. Rate limits use process-local memory; configure shared storage before deploying multiple workers. The included Nginx proxy limits request bodies to 1 MiB. `/ready` checks database connectivity, not migration status.

Items demonstrate private data ownership, not a universal data model. Rename and extend the example for notes, saved collections, or planned sets. Shared data (such as an admin-ingested music catalog) should have its own models and write permissions; users can reference shared records from their private collections. File storage and expensive analysis belong in separate features when needed.

## Project layout

```text
backend/
  api/endpoints/    HTTP routes and dependencies
  core/            Settings, database sessions, rate limiting
  models/          ORM models and request/response schemas
  services/        Authentication, item CRUD, background jobs
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

**Upgrading from the CSV template:** run `alembic upgrade head` using the command above. Migration `0002_items` converts existing catalog entries to items, preserving IDs, owners, names as titles, descriptions, and timestamps. It drops stored file paths and CSV profiling metadata. Back up those fields first if needed; downgrading recreates them with empty values. Existing files and Docker upload volumes are left untouched, but the app no longer uses them. Remove obsolete `DATA_DIR`, `MAX_UPLOAD_BYTES`, `MAX_DATASETS_PER_USER`, and `CLIENT_MAX_BODY_SIZE` settings from local configuration.

**Older migration compatibility:** `0001_core` replaced the original pre-cleanup migration history. Do not apply or stamp that baseline over an installation from before the cleanup. Those databases need a separate migration/export plan; their password hashes and tokens are not compatible with the current authentication setup. Checking out these changes does not modify any existing database.

## Checks

```bash
uv sync --all-packages --locked
uv run --no-sync ruff check .
uv run --no-sync ruff format --check .
uv run --no-sync pytest
```

Backend tests use isolated SQLite databases, with no running API or external services. They cover ownership, validation, pagination, and migration data preservation. CI also checks migration upgrade, schema consistency, and downgrade on PostgreSQL. The frontend has separate build, lint, and browser checks:

```bash
cd frontend
npm ci
npm run lint
npm run build
npx playwright install chromium
npm test
```

Authentication follows the libraries used in [FastAPI's security guide](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/); container dependency installation follows [uv's Docker guide](https://docs.astral.sh/uv/guides/integration/docker/).
