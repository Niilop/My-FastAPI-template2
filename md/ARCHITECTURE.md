# Implemented architecture

This describes the template as it exists. Proposed additions belong in [plans](plans/README.md) until implemented.

## Components and request flow

```text
Browser: React + TypeScript
  -> /api/* through Vite (development) or Nginx (Docker)
  -> FastAPI routes (proxy removes /api)
  -> service functions
  -> SQLAlchemy session
  -> external PostgreSQL

FastAPI BackgroundTasks -> job service -> separate database session
```

Development uses frontend port 5173 and backend port 8000. `make dev` checks setup and starts both servers with shared shutdown; Vite proxies API calls to the local backend. In Docker, Nginx serves the built frontend and proxies to the backend service. Compose's optional `ui` profile enables the frontend. Database migrations are a separate step before normal application startup.

| Location | Responsibility |
| --- | --- |
| [backend/main.py](../backend/main.py) | App creation, router registration, CORS, liveness and readiness |
| [backend/api/endpoints/](../backend/api/endpoints/) | HTTP validation, dependencies, authentication and ownership checks |
| [backend/services/](../backend/services/) | Authentication helpers, item persistence, example and job logic |
| [backend/core/](../backend/core/) | Settings, engine/session configuration, rate limiter |
| [backend/models/](../backend/models/) | SQLAlchemy models and Pydantic request/response schemas |
| [backend/alembic/](../backend/alembic/) | Versioned database changes |
| [frontend/src/App.tsx](../frontend/src/App.tsx) | Routes and protected-page composition |
| [frontend/src/api/](../frontend/src/api/) | Fetch wrapper, response types, API error handling |
| [frontend/src/auth/](../frontend/src/auth/) | In-memory session, authenticated requests, route guard |
| [frontend/src/pages/](../frontend/src/pages/) | Overview, registration/login, account, item CRUD |
| [tests/](../tests/) and [frontend/tests/](../frontend/tests/) | Backend tests and browser tests |
| [scripts/](../scripts/) and [Makefile](../Makefile) | Safe setup, local server supervision, checks, isolated smoke orchestration |
| [frontend/e2e/](../frontend/e2e/) and [compose.smoke.yaml](../compose.smoke.yaml) | Real browser-to-database test with disposable PostgreSQL and production app images |

## Data and authorization

- `User` has many `Item` and `BackgroundJob` records. SQLAlchemy relationships cascade deletes when deleting a user through the ORM; foreign keys do not declare database-level `ON DELETE CASCADE`.
- `Item` stores `id`, `owner_id`, `title`, `description`, and timestamps. Routes derive the owner from the authenticated user. Reads, lists, updates, and deletes filter by that owner. Missing and foreign-owned items return 404.
- `BackgroundJob` stores its owner, type, status, result, error, and timestamps. Job status lookup is owner-scoped.
- Registration hashes passwords with Argon2. Login returns an expiring HS256 JWT identifying the user. Protected requests validate the token and look up that user in the database.
- The frontend keeps its token in React state. Reloading signs the user out; a 401 clears the matching session. Signing out locally does not revoke an issued token.

The item example can become private notes or collections. Shared domain data needs its own models and write permissions; user-owned records may reference it.

## Persistence and contracts

`get_db` supplies a session per request. Services commit mutations; the dependency closes the session. Background jobs open their own session rather than retaining a request session. ORM models define storage; Pydantic schemas define the HTTP contract. Frontend interfaces mirror that contract manually and do not validate responses at runtime.

Alembic history starts at `0001_core`. `0002_items` converts the former CSV catalog into items, preserving record identity and descriptive fields while dropping file paths and profiling metadata. See the [migration compatibility notes](../README.md#project-layout) before using an older database.

## Current limits

- Background tasks run inside the API process. They have no durable queue, automatic retry, or recovery after process termination.
- Rate limits use process-local memory. Multiple workers would need shared rate-limit storage for consistent enforcement.
- Persistent login, refresh tokens, password reset, email verification, and administrative roles are not implemented.
- `/health` checks process liveness; `/ready` checks a database query, not migration status.
- Most browser tests mock the API for focused UI coverage. A separate CI smoke job tests real registration, login, persistence, item CRUD, and ownership through Nginx, FastAPI, and PostgreSQL. It does not attempt exhaustive end-to-end coverage.

These are extension points to assess for a concrete product, not an automatic backlog for the template.
