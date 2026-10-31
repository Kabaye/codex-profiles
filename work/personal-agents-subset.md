<!-- codex-profiles:begin -->
- Use the user-selected root model and effort.
- In `solo` mode, retain native Codex delegation behavior; do not apply the automatic team routes below. In `team` mode, delegate useful independent work through these routes.
- For live computer-use tasks requiring visual screen inspection and mouse/keyboard actions in a browser or desktop app, delegate the GUI portion to native `terra_computer` (GPT-6.1 Terra / medium) in both `solo` and `team`. This is the sole automatic specialist exception to the normal solo/team delegation rules. Keep the user-selected root model and its planning, authorization, integration, and final acceptance. Non-GUI implementation, analysis, CLI, API, and ordinary web research retain their existing routes.
- Delegate only when the Terra model is accessible and usable Computer Use/Browser tools and permissions are available to the parent session (Codex CLI 0.159.0+ for Terra). Have the specialist verify the actual UI outcome. If model, tools, or permissions are unavailable, report the blocker rather than silently asking Sol, Luna, OpenCode, or Cursor to click.
- Use `sol_worker` for implementation, debugging and complex or uncertain tasks (Sol-first).
- Use `luna_worker` for mechanical edits, exploration and routine checks; move growing complexity to Sol.
- Give each worker its own files and a self-contained task with interfaces, constraints and checks; use `fork_turns = "none"`.
- Workers complete their own assignment and checks directly; no nested delegation. Do not use OpenCode for these jobs.
- Root owns architecture, integration and final acceptance. Independent review only when the user explicitly requests one.
<!-- codex-profiles:end -->
