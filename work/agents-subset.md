<!-- codex-profiles:begin -->
- Use the user-selected root model and effort.
- Delegate useful independent work, with up to three open child threads.
- For ordinary work objectives, use `luna_worker`.
- Enable the personal lane when the user explicitly says `это личная задача`; keep it for that objective and direct follow-ups.
- In the personal lane, use `sol_worker` for implementation, debugging and complex or uncertain tasks (Sol-first), and `luna_worker` for mechanical edits, exploration and routine checks.
- Give each worker its own files and a self-contained task with interfaces, constraints and checks; use `fork_turns = "none"`.
- Root owns architecture, integration and final acceptance. Independent review only when the user explicitly requests one.
<!-- codex-profiles:end -->
