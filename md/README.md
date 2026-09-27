# Development context

This folder is shared context for maintainers and coding agents. It describes the current system and provides a place to plan work and hand it off. It is useful without any particular AI tool; agents that do not automatically read the root `AGENTS.md` should be directed there at the start of a session.

| File | What belongs here | Update when |
| --- | --- | --- |
| [PROJECT.md](PROJECT.md) | Product goal, users, scope, constraints, open product questions | The intended product changes |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Implemented components, data relationships, request flows, limitations | The system structure changes |
| [DEVELOPMENT.md](DEVELOPMENT.md) | Development workflow, commands, validation, troubleshooting | The way work is done changes |
| [STATUS.md](STATUS.md) | Current work, active plan links, blockers, next step | Substantial work finishes or pauses |
| [DECISIONS.md](DECISIONS.md) | Significant choices, reasons, consequences, superseded choices | A consequential decision is made |
| [plans/](plans/README.md) | Scoped implementation plans with acceptance checks and results | A substantial task needs tracking |

The root [README](../README.md) remains the setup and API reference. Link to existing explanations instead of maintaining duplicate versions. Source code and configuration establish implemented behavior; these documents explain intent and should be corrected when they disagree.

## Starting a project from this template

1. Replace the template purpose in `PROJECT.md` with the new project's goal, users, first deliverable, and boundaries. Mark unanswered questions explicitly rather than guessing.
2. Review `ARCHITECTURE.md` against what you keep. Update it as examples become real domain models; do not describe planned services as already existing.
3. Review `DEVELOPMENT.md` and root `AGENTS.md` for the team's actual environment. Machine-specific paths are examples, not requirements for every contributor.
4. Replace the template status in `STATUS.md` with the project's starting state and next step. Keep inherited decisions only while they still apply.
5. Create the first plan from `plans/TEMPLATE.md` when there is an agreed feature to implement, and link it from `STATUS.md`.

Keep the existing migration history unless a separate, explicit migration reset is part of the new project's setup. Copying the template does not establish that an existing database can be discarded.

## Keeping context useful

Update the affected documents in the same change as the implementation. A typo fix does not require updates across this folder. For a handoff, write only enough for the next developer to identify the current state, remaining work, and evidence. Mark assumptions, proposals, and blocked work clearly. Git retains previous versions; `STATUS.md` should remain a current snapshot.
