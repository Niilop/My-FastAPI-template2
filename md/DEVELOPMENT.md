# Development workflow

## Environment and setup

Follow the root [setup instructions](../README.md#local-development) and [frontend guide](../frontend/README.md). Use Python 3.12+ through `uv` and Node 24 with npm. The maintainer's environment is Linux/WSL2, with PostgreSQL and Redis containers in `~/code/devstack`; that location is not required on other machines, and this application does not use Redis.

Use `make setup` to install locked dependencies and create a private `.env` with a generated secret, preserving an existing file. Configure a dedicated database, run `make migrate`, then `make dev` to start both servers. The dev helper checks settings, occupied ports, and migration revision, and stops both servers together. Separate `make backend` and `make frontend` commands are also available. Repository-root settings are loaded independently of the backend's working directory; the frontend proxy override lives in `frontend/.env.local`. The combined dev command intentionally selects the local API.

## Implementing a change

1. Check the working tree and read the relevant context and code. Confirm what already exists.
2. For substantial work, define the outcome, scope, and acceptance checks in a [plan](plans/TEMPLATE.md). Record unresolved choices without treating them as approved requirements.
3. Follow the existing route → service → model structure. Add and register routes in `create_app`; preserve authentication and owner filtering on private resources.
4. For schema changes, create and inspect an Alembic migration. Consider existing records, defaults, constraints, and what a downgrade can actually restore. Do not rewrite already applied migrations.
5. Keep Pydantic schemas, frontend API types, forms, and request examples consistent when contracts change.
6. Run checks appropriate to the changed behavior. Update relevant context and leave a concise handoff when work finishes or pauses.

Use standard-library functionality and existing packages before adding dependencies. Python public functions need type hints; Ruff controls Python style. Frontend code uses TypeScript, ESLint, and Prettier. Keep business-specific additions in the new project rather than expanding this template speculatively.

## Validation

`make check` runs both suites below; `make check-backend` and `make check-frontend` run one side. Run Python checks from the repository root after `uv sync --all-packages --locked`:

```bash
uv run --no-sync ruff check .
uv run --no-sync ruff format --check .
uv run --no-sync pytest
```

Run frontend checks from `frontend/` after `npm ci`:

```bash
npm run lint
npm run format:check
npm run build
npm test
```

`npm run build` includes TypeScript checking. Playwright requires Chromium and its system libraries; installation options are in the [frontend guide](../frontend/README.md#checks). Ask before installing system/global packages. If browser launch fails because the environment lacks libraries, report that limit separately from application failures.

Backend tests use isolated SQLite databases. Browser tests intercept API requests. Changes to migrations or database-specific behavior also need PostgreSQL validation. Against a **disposable test database only**, check upgrade, `alembic check`, downgrade, and upgrade again; include data preservation checks when transforming records. Never run a destructive migration test against a developer's working database. CI's exact commands are in [ci.yml](../.github/workflows/ci.yml).

For changes across the API, UI, or proxy, run `make smoke`: it builds an isolated Docker stack, applies migrations to a disposable database, and tests real registration, login, item CRUD, persistence, and cross-user isolation. It publishes no ports, reads no local `.env`, and cleans up its containers and data. Failure traces/screenshots and service logs go to `frontend/test-results/smoke/`; CI uploads them on failure. See the [smoke guide](../README.md#full-stack-smoke-test). Documentation-only changes normally need link/path checks and `git diff --check`, not a new application test suite.

Weekly Dependabot PRs group minor/patch updates by ecosystem, with separate Python/npm security groups. Major updates remain separate and require compatibility review. No automatic merging is configured. See the [maintenance guide](../README.md#dependency-maintenance).

## Common development issues

- Frontend unavailable on 5173: check that Vite or the Docker `ui` service is running and the port is available.
- UI loads but API calls fail: check FastAPI on 8000, its database configuration, and the Vite/Nginx upstream. Container `localhost` refers to that container.
- Database connection succeeds but requests fail on missing tables: check migration status; `/ready` alone does not verify the schema.
- Reload loses login: expected with the current in-memory session design.

## Finishing or handing off

Record changed behavior, relevant check results, unresolved issues, and the next step in the active plan. Keep [STATUS.md](STATUS.md) short and link to that plan or PR. Update architecture and decisions only when those facts changed. Do not record credentials or full command output; store concise evidence and references.
