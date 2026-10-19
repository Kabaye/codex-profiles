<!-- codex-profiles:begin -->
## Agent routing — private team

- Root model/effort selected by the user is authoritative; installation defaults to **GPT-6 Astra / xhigh**. Routing never switches root.
- Delegate selectively: normally zero or one worker, **no more than two open child threads**. Implementation is **Sol-first**: `sol_worker` (**GPT-6.1 Sol / xhigh**) owns substantial work, debugging, state/workflow logic, contracts, migrations, cross-component changes and uncertain complexity.
- `luna_worker` (**GPT-6 Luna / max**) is for settled, low-risk mechanical work, exploration or routine checks only. A workstream being bounded or limited to a few files is not enough to choose Luna. Reassess if complexity increases; **Owner reuse never overrides model suitability**.
- Every spawn explicitly names `sol_worker` or `luna_worker` and `fork_turns = "none"`, with a self-contained goal, ownership, interfaces, constraints and checks. No `default`/`worker`/`explorer` aliases or nested delegation.
- Root owns architecture, hard decisions, integration and acceptance. Workers own complete non-overlapping workstreams, including fixes/tests; never duplicate work. No **automatic reviewer**: assign independent review only when the user explicitly requests one.
- Workers must not change routing/model settings or spawn children. Production writes, pushes, migrations and deployments still require existing user authorization or an approved runbook.
<!-- codex-profiles:end -->
