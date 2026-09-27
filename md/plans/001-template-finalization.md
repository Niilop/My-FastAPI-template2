# 001 — Final template development and CI polish

- Status: active
- Updated: 2026-09-27
- Branch: `chore/template-finalization`

## Goal

Make a fresh template copy easy to start, exercise the real application in CI, and keep dependencies maintained through reviewable update PRs.

## Scope

- Make commands for setup, local servers, migrations, checks, and an isolated full-stack smoke test.
- Safe environment initialization and shutdown of both development servers together.
- Browser registration, login, item CRUD, and cross-user isolation against real Nginx, FastAPI, and PostgreSQL in Docker.
- Weekly grouped dependency updates for uv, npm, GitHub Actions, and Docker.
- Update development context and setup documentation. The user has already enabled GitHub's template setting.
- No new application features or runtime dependencies; no migrations against the developer's database during validation.

## Acceptance checks

- [x] Setup creates a secret for a new `.env` and never overwrites an existing one.
- [x] Development command starts both servers, reports missing setup, and stops both on interruption or child failure.
- [x] Make exposes documented migration and validation commands.
- [ ] Full-stack smoke passes locally and in CI, using disposable data and preserving failure evidence.
- [x] Smoke resources are cleaned up after success and failure.
- [x] Dependency update configuration covers the manifests and groups routine updates without automatic merging.
- [x] Documentation and existing checks pass.

## Implementation steps

- [x] Inspect the merged baseline and the current test/development setup.
- [x] Add command helpers and focused checks for their failure cases.
- [x] Add isolated smoke stack, browser scenario, and CI job.
- [x] Add dependency maintenance configuration.
- [ ] Validate and update docs, decisions, and status; open one PR.

## Validation results

| Check | Result |
| --- | --- |
| `make check-backend` | 44 tests pass; Ruff lint and formatting pass |
| Frontend lint, formatting, production build | Pass |
| Existing desktop/mobile browser suite in Docker | 14 tests pass |
| `make smoke` | Real registration, login, persistence, CRUD, and cross-user isolation pass |
| Smoke cleanup | No test containers/networks left after a failed run or successful run |
| Fresh copy in `/tmp` with disposable PostgreSQL | Setup and existing-env preservation pass; migration preflight rejects an unmigrated DB; `make migrate` succeeds; both servers/proxy and Ctrl+C cleanup pass on alternate ports |
| Compose and YAML syntax | Pass |
| GitHub CI | Pending PR |

## Handoff

Implementation is ready for PR validation. No schema changes or runtime dependencies were added. Custom development ports allow several copied projects to run without changing source files. An artifact mount permission issue found in the first smoke run was corrected before the passing run. Next step: confirm CI on the PR.
