# Routing policy
## Defaults

| Profile | Root default | Mode | Team routing |
|---|---|---|---|
| `private` | GPT-6 Astra xhigh | solo | Sol-first implementation; Luna for mechanical edits, exploration and checks |
| `work` | GPT-6.1 Sol xhigh | solo | Luna for work; Sol-first for explicitly personal tasks |

Use the user's selected root model and effort.
## Solo
Solo uses native Codex delegation. The profile installs its base settings and leaves custom roles, routing instructions and the child-thread cap to Codex.
## Team
- Delegate useful independent work, with up to three open child threads.
- Select the named `luna_worker` or `sol_worker` with `fork_turns = "none"`.
- Give each worker its own files, goal, interfaces, constraints and checks.
- Keep architecture, integration and final acceptance in the root.
- Assign independent review when the user explicitly requests it.
### Private
Use Sol for implementation, debugging and complex or uncertain tasks. Use Luna for mechanical edits, exploration and routine checks; move growing complexity to Sol.
### Work
Use Luna for ordinary work objectives. An explicit `это личная задача` enables the personal lane for the current objective and direct follow-ups, using the private Sol-first policy. A new unrelated objective uses ordinary work routing.
## Role configuration
Luna uses GPT-6 Luna / max; Sol uses GPT-6.1 Sol / xhigh. Each worker completes its assignment directly, performs focused checks and returns results to the root. Both profiles use the native Codex model catalog.
