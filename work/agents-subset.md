<!-- codex-profiles:begin -->
## Agent routing — work team

- Respect the current root model/effort; installation defaults to **GPT-6.1 Sol / xhigh**. **Selecting Astra as root changes only the root**, not task classification or child routing.
- Normally use zero or one worker; never exceed **two open child threads**. For **ordinary work objectives**, delegate only to `luna_worker` (**GPT-6 Luna / max**).
- Enable the personal lane **only** when the user explicitly marks this objective as personal (e.g. `это личная задача`). Never infer it from paths, topic, difficulty or root model. Acknowledge once; the lane covers this objective and direct follow-ups only.
- In that lane, implementation is **Sol-first**: use `sol_worker` (**GPT-6.1 Sol / xhigh**) for substantial implementation, debugging, workflow/state, business logic, contracts, migrations, cross-component changes or uncertain complexity. Reserve `luna_worker` for settled, low-risk mechanical tasks; being bounded or limited to a few files is not enough to select Luna. Reassess rising complexity; **Owner reuse never overrides model suitability**.
- Each spawn explicitly requests the permitted `luna_worker` or `sol_worker`, `fork_turns = "none"` and a self-contained objective, ownership, interfaces, constraints and checks. No `default`/`worker`/`explorer` aliases, duplicate investigations or nested delegation.
- Root retains architecture, ambiguous decisions, integration and final acceptance. No **automatic reviewer**; independent review only when the user explicitly requests one. Production writes, pushes, migrations and deployments still require existing authorization or an approved runbook; workers cannot change routing/model settings or spawn children.
<!-- codex-profiles:end -->
