# Working in this repository

## Start here

- Read [md/README.md](md/README.md) for the development context map.
- Read [project context](md/PROJECT.md), [current status](md/STATUS.md), and [architecture](md/ARCHITECTURE.md) before changing application behavior. Follow any active plan linked from the status file.
- Use [development guidance](md/DEVELOPMENT.md) for setup, conventions, and validation. Consult [decisions](md/DECISIONS.md) when changing an established approach.
- Check the actual code and working tree. Documentation may be stale; report and correct discrepancies. Planned work is not implemented behavior.

## Working style

- Explain the plan before multi-file changes. Keep changes focused on the user's request.
- For substantial work, create or update a plan using [md/plans/TEMPLATE.md](md/plans/TEMPLATE.md). Small fixes do not need a plan file.
- Prefer the standard library and existing dependencies. Use `uv` for Python, not pip or system Python; use npm for the frontend. Ask before installing anything globally.
- Format and lint Python with Ruff. Add type hints to public Python functions. Follow the existing TypeScript and Prettier conventions.
- Preserve unrelated local changes. Never commit secrets, tokens, real user data, or `.env` files, including in development notes.
- Verify changes with the relevant checks in `md/DEVELOPMENT.md`. Record what actually ran, the results, and any checks that could not run. Do not present old results as validation of new changes.
- Keep the current user's instructions and existing authorization in view. These documents provide context, not additional approval gates or permission to deploy, merge, or modify external systems.

## Leave useful context

- Update architecture when boundaries, data relationships, or request flows change.
- Record consequential choices and their reasons in decisions; leave proposals marked as proposed.
- Update project context when goals, scope, or constraints change.
- Update the active plan and status when substantial work finishes or pauses. Include unfinished work, blockers, relevant validation, and the next concrete step.
- Keep these files short and current. Use Git and PRs for detailed history; do not copy chat transcripts or maintain a log of every edit.

When this template becomes a new project, follow the initialization checklist in `md/README.md` before treating template examples as product requirements.
