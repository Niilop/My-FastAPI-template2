# Development workflow

## Environment and setup

Follow the root [setup instructions](../README.md#local-development) and [frontend guide](../frontend/README.md). Use Python 3.12+ through `uv` and Node 24 with npm. The maintainer's environment is Linux/WSL2, with PostgreSQL and Redis containers in `~/code/devstack`; that location is not required on other machines, and this application does not use Redis.

Use a dedicated database, configure `.env`, and run migrations before starting the backend. Start the backend and frontend in separate terminals. Do not overwrite an existing `.env` during setup. Repository-root settings are loaded independently of the backend's working directory; the frontend proxy override lives in `frontend/.env.local`.

## Implementing a change

1. Check the working tree and read the relevant context and code. Confirm what already exists.
2. For substantial work, define the outcome, scope, and acceptance checks in a [plan](plans/TEMPLATE.md). Record unresolved choices without treating them as approved requirements.
3. Follow the existing route → service → model structure. Add and register routes in `create_app`; preserve authentication and owner filtering on private resources.
4. For schema changes, create and inspect an Alembic migration. Consider existing records, defaults, constraints, and what a downgrade can actually restore. Do not rewrite already applied migrations.
5. Keep Pydantic schemas, frontend API types, forms, and request examples consistent when contracts change.
6. Run checks appropriate to the changed behavior. Update relevant context and leave a concise handoff when work finishes or pauses.

Use standard-library functionality and existing packages before adding dependencies. Python public functions need type hints; Ruff controls Python style. Frontend code uses TypeScript, ESLint, and Prettier. Keep business-specific additions in the new project rather than expanding this template speculatively.

## Validation

Run Python checks from the repository root after `uv sync --all-packages --locked`:

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

For changes across the API, UI, or proxy, also exercise the real application: register, sign in, create/edit/delete an item, and check that a second user cannot access it. Documentation-only changes normally need link/path checks and `git diff --check`, not a new application test suite.

## Common development issues

- Frontend unavailable on 5173: check that Vite or the Docker `ui` service is running and the port is available.
- UI loads but API calls fail: check FastAPI on 8000, its database configuration, and the Vite/Nginx upstream. Container `localhost` refers to that container.
- Database connection succeeds but requests fail on missing tables: check migration status; `/ready` alone does not verify the schema.
- Reload loses login: expected with the current in-memory session design.

## Finishing or handing off

Record changed behavior, relevant check results, unresolved issues, and the next step in the active plan. Keep [STATUS.md](STATUS.md) short and link to that plan or PR. Update architecture and decisions only when those facts changed. Do not record credentials or full command output; store concise evidence and references.
