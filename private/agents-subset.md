<!-- codex-profiles:begin -->
## Agent routing — private team

- The current user-selected root model and effort are authoritative; installation defaults to **GPT-6 Astra / high** and routing never changes the root.
- Team mode uses selective delegation: keep work in the root by default, normally use zero or one worker, and never exceed **two open child threads**.
- Use `luna_worker` (**GPT-5.6 Luna / max**) for simple, mechanical, well-specified, repository-exploration, tool-heavy, test/build/log, or otherwise cheap bounded work.
- Use `sol_worker` (**GPT-5.6 Sol / high**) for substantial bounded implementation, non-trivial debugging, or work whose ambiguity/risk makes Luna a poor fit.
- Keep architecture, material ambiguity, hard reasoning, integration, worker verification, and final acceptance in the root. Do not add an automatic reviewer; an independent review is only for an explicit user request or a specifically identified risk that requires it.
- Every spawn must explicitly request `luna_worker` or `sol_worker` with `fork_turns = "none"` and a self-contained objective, ownership, interfaces, constraints, and acceptance checks. There are no `default` / `worker` / `explorer` routing aliases.
- Delegated work substitutes for root work; do not duplicate the same investigation or implementation. Reuse the same owner for its fix/test loop when practical.
- Workers never spawn children or change routing/model settings. Production writes, pushes, migrations, and deployments still require the user's existing authorization or an applicable runbook.

<!-- codex-profiles:end -->
