<!-- codex-profiles:begin -->
## Agent routing — private team

- The current user-selected root model and effort are authoritative; installation defaults to **GPT-6 Astra / high** and routing never changes the root.
- Team mode uses selective delegation: keep work in the root by default, normally use zero or one worker, and never exceed **two open child threads**.
- Delegated implementation is **Sol-first**. Use `sol_worker` (**GPT-5.6 Sol / high**) for substantial implementation, non-trivial debugging, workflow/state changes, business or financial logic, API/contracts, migrations, cross-component behavior, adaptive UI behavior, or any work whose complexity is uncertain.
- Use `luna_worker` (**GPT-5.6 Luna / max**) only for clearly mechanical, low-risk work with an already-settled specification and no meaningful business logic, workflow/state semantics, contracts, migrations, or cross-component behavior; examples include repository exploration, straightforward local edits, repetitive transformations, and routine test/build/log execution. A workstream being bounded or limited to a few files is not enough to qualify it for Luna. When in doubt, use Sol or keep the work in the root.
- Keep architecture, material ambiguity, hard reasoning, integration, worker verification, and final acceptance in the root. Do not add an automatic reviewer. Use an independent reviewer only when the user explicitly requests one.
- Every spawn must explicitly request `luna_worker` or `sol_worker` with `fork_turns = "none"` and a self-contained objective, ownership, interfaces, constraints, and acceptance checks. There are no `default` / `worker` / `explorer` routing aliases.
- Delegated work substitutes for root work; do not duplicate the same investigation or implementation. Reuse the same owner only while the model remains suitable. If a Luna assignment materially expands in scope, behavioral complexity, risk, or required judgment, stop and reassess before continuing; move the remaining coherent workstream to Sol or back to the root. Owner reuse never overrides model suitability.
- Workers never spawn children or change routing/model settings. Production writes, pushes, migrations, and deployments still require the user's existing authorization or an applicable runbook.

<!-- codex-profiles:end -->
