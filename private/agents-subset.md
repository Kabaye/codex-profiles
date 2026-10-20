<!-- codex-profiles:begin -->
- Use the user-selected root model and effort.
- Delegate useful independent work, with up to three open child threads.
- Use `sol_worker` for implementation, debugging and complex or uncertain tasks (Sol-first).
- Use `luna_worker` for mechanical edits, exploration and routine checks; move growing complexity to Sol.
- Give each worker its own files and a self-contained task with interfaces, constraints and checks; use `fork_turns = "none"`.
- Root owns architecture, integration and final acceptance. Independent review only when the user explicitly requests one.
<!-- codex-profiles:end -->
