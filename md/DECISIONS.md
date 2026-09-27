# Architecture and development decisions

Record choices that future maintainers would otherwise have to rediscover: boundaries, ownership rules, important dependencies, or operational tradeoffs. Routine edits belong in Git history. Proposed decisions are not permission to implement them.

## D001 — Keep the starter domain-neutral

- Status: accepted template baseline.
- Decision: demonstrate private CRUD with a small item containing a title and description. Keep file processing and product-specific models out of the baseline.
- Reason: copied projects need an ownership example without inheriting an upload workflow or a particular product domain.
- Consequence: a new project should rename or replace items. Shared catalogs and user-owned collections can be separate models rather than forcing all data into items.

## D002 — Use in-memory browser sessions in the baseline

- Status: accepted template baseline.
- Decision: hold the bearer token in React state and clear the session on an authenticated 401.
- Reason: demonstrate authentication without adding persistent browser token storage or a refresh-token subsystem to the starter.
- Consequence: page reload signs the user out. A product that needs persistent login must design that flow explicitly; local sign-out alone does not revoke tokens.

## D003 — Keep the background example in-process

- Status: accepted template baseline.
- Decision: demonstrate a short FastAPI background task with a stored job record and a separate database session.
- Reason: show task submission and status lookup without requiring queue infrastructure in every copied project.
- Consequence: task execution is not durable. Long-running analysis or ingestion that needs retries and recovery requires a separate worker design.

## D004 — Isolate full-stack tests from development data

- Status: accepted.
- Date: 2026-09-27.
- Decision: run the same `make smoke` target locally and in CI, with production app images and a separate Compose file, network, and temporary PostgreSQL data.
- Reason: exercise the actual proxy, API contract, and persistence without relying on or mutating a developer's database. No host ports or local `.env` are used.
- Consequences: smoke tests require Docker and build a browser runner; initial runs are slower than mocked UI tests. Browser installation follows the locked Playwright version rather than a separately versioned browser image. Normal application migrations remain explicit.
- Reference: [finalization plan](plans/001-template-finalization.md).

## Adding a decision

Copy this outline, assign the next ID, and link it from a related plan when useful:

```markdown
## D00N — Short decision title

- Status: proposed | accepted | superseded by D00N
- Date: YYYY-MM-DD
- Context: the problem and relevant constraints.
- Decision: the choice and why it fits.
- Alternatives: meaningful options considered, if any.
- Consequences: costs, limitations, and follow-up work.
- References: related plan, code, issue, or PR.
```

When a choice changes, mark the old entry superseded and link the replacement. When copying the template, review whether these baseline decisions still apply.
