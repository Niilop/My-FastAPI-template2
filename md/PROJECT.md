# Project context

## Current purpose

This repository is a reusable FastAPI and React starter. It provides working authentication, persistence, a small private-item CRUD example, and development checks. It does not yet define a downstream product.

## Users and first deliverable

- Current users: developers starting a web application.
- Deliverable: a runnable backend and frontend whose examples can be renamed or replaced.
- Downstream product and end users: not specified. Replace this section when creating a project.

## Included scope

- Registration, login, current-user lookup, and protected frontend routes.
- PostgreSQL persistence with SQLAlchemy and Alembic migrations.
- Private items with a title, description, ownership, and timestamps.
- A public request example and a short in-process background job example.
- Local development, Docker images, and automated backend/frontend checks.

## Boundaries

Keep the starter small. Uploads, scraping, audio processing, shared catalogs, billing, and other product features are not implemented requirements. Add them only when the new project calls for them. The item model demonstrates ownership; it is not a requirement that every future record belong to a user.

## Constraints

- Python dependencies and tooling use `uv`; frontend dependencies use npm.
- Keep PostgreSQL external to the application Compose file. Redis is not currently required.
- Secrets and environment-specific values stay outside tracked files.
- Preserve authorization boundaries and review migrations when adapting examples.

## Questions to answer for a new project

- What problem does the product solve, and for whom?
- What is the smallest useful first release, and what is explicitly deferred?
- Which data is private, shared, or writable only by administrators or workers?
- What work runs in a request, and what needs durable background processing?
- Where will it run, and what operational constraints matter?
