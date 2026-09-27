# 001 — Final template development and CI polish

- Status: complete
- Updated: 2026-09-27
- Branch / PR: `chore/template-finalization`, [PR #5](https://github.com/Niilop/My-FastAPI-template2/pull/5)

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
- [x] Full-stack smoke passes locally and in CI, using disposable data and preserving failure evidence.
- [x] Smoke resources are cleaned up after success and failure.
- [x] Dependency update configuration covers the manifests and groups routine updates without automatic merging.
- [x] Documentation and existing checks pass.

## Implementation steps

- [x] Inspect the merged baseline and the current test/development setup.
- [x] Add command helpers and focused checks for their failure cases.
- [x] Add isolated smoke stack, browser scenario, and CI job.
- [x] Add dependency maintenance configuration.
- [x] Validate and update docs, decisions, and status; open one PR.

## Validation results

| Check | Result |
| --- | --- |
| `make check-backend` | 46 tests pass after the port-restart review fix; Ruff lint and formatting pass |
| Port-restart regression | Real-socket test reproduced failure before the fix; restart after TIME_WAIT and rejection of active listeners both pass with address reuse |
| Frontend lint, formatting, production build | Pass |
| Existing desktop/mobile browser suite in Docker | 14 tests pass |
| `make smoke` | Real registration, login, persistence, CRUD, and cross-user isolation pass |
| Smoke cleanup | No test containers/networks left after a failed run or successful run |
| Fresh copy in `/tmp` with disposable PostgreSQL | Setup and existing-env preservation pass; migration preflight rejects an unmigrated DB; `make migrate` succeeds; both servers/proxy and Ctrl+C cleanup pass on alternate ports |
| Compose and YAML syntax | Pass |
| GitHub CI | Backend on Python 3.12/3.14, frontend, and full-stack smoke pass on implementation commit `9bc93ee`; [run](https://github.com/Niilop/My-FastAPI-template2/actions/runs/36329427110) |
| Documentation | 53 local links/anchors and whitespace checks pass |

## Handoff

Implementation and validation are complete; PR #5 is ready for user review and merge. No schema changes or runtime dependencies were added. Custom development ports allow several copied projects to run without changing source files. An artifact mount permission issue found in the first smoke run was corrected before the passing run. After merging, use the template initialization checklist for the next project; no implementation work remains in this plan.
