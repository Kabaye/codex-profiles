<!-- codex-profiles:begin -->
## Agent routing — work team

- The current user-selected root model and effort are authoritative. Installation defaults to **GPT-5.6 Sol / xhigh**, but the user may select **GPT-6 Astra** (or another available root) directly; routing never changes it.
- Team mode uses selective delegation: keep work in the root by default, normally use zero or one worker, and never exceed **two open child threads**.
- For ordinary work objectives, delegated work uses only `luna_worker`, pinned to **GPT-5.6 Luna / max**.
- A personal lane is enabled only when the user explicitly states that the current objective is personal, for example: `это личная задача`. Do not infer it from repository, path, task content, difficulty, or root model. Acknowledge the declaration once; it applies to that coherent objective and direct follow-ups only.
- In the explicit personal lane, use `luna_worker` for simple/mechanical/well-specified bounded work and `sol_worker` (**GPT-5.6 Sol / high**) for substantial implementation or non-trivial debugging.
- Selecting Astra as root changes only the root and never activates the personal lane.
- Keep architecture, material ambiguity, hard reasoning, integration, worker verification, and final acceptance in the root. Do not add an automatic reviewer. Use an independent reviewer only when the user explicitly requests one.
- Every spawn must explicitly request `luna_worker` or, in the personal lane, `sol_worker`, with `fork_turns = "none"` and a self-contained objective, ownership, interfaces, constraints, and acceptance checks. There are no `default` / `worker` / `explorer` routing aliases.
- Delegated work substitutes for root work; do not duplicate the same investigation or implementation. Reuse the same owner for its fix/test loop when practical.
- Workers never spawn children or change routing/model settings. Production writes, pushes, migrations, and deployments still require the user's existing authorization or an applicable runbook.

<!-- codex-profiles:end -->
