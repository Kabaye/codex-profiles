<!-- codex-profiles:begin -->
## Agent routing — private

- The root model and effort selected by the user are authoritative. Profile defaults apply at installation, not as an instruction to switch a running root. Never change the root model/effort, enable Fast/Ultra, or alter configuration merely because a task seems difficult.
- Installation default: **GPT-6 Astra / high**. The root owns ambiguous reasoning, architecture, difficult debugging, integration and final acceptance.
- Delegation under this profile is proactive when useful: do not require a separate user phrase such as “use sub-agents” before spawning an allowed worker. Decide from the work itself whether a worthwhile bounded or parallel workstream exists.
- All delegated work uses `sol_worker`, pinned to **GPT-5.6 Sol / high**. Use it for substantial bounded implementation, repository exploration, ordinary debugging, deterministic tool-heavy execution, logs, tests and builds.
- Keep reasoning-heavy or tightly coupled work in the Astra root when handing it off would lose important context. If a Sol workstream exposes a genuinely hard reasoning problem, return the evidence to the root instead of escalating to another worker model.
- There is **no Astra worker** and no Luna worker in this profile. Astra xhigh/max is a manual root choice for unusually difficult sessions; routing never raises root effort automatically.
- Independent verification normally uses the Astra root or a fresh read-only Sol High assignment for a named risk. Do not create a second full implementation just to obtain agreement.
- At most **four open subagent threads**. Usually use zero to two. Use a third or fourth only for genuinely independent workstreams with clear ownership and real parallel value; never fill slots for their own sake.
- The generated `default` / `worker` / `explorer` aliases are pinned to Sol High; deliberately use `sol_worker`. If the required pin is unavailable, continue in the existing root and report the limitation rather than changing models silently.

## Ownership and coordination

- Assign one coherent workstream, including its implementation and fix/test loop, to one owner. Reuse that owner for follow-ups; change owner only when the responsibility materially changes.
- Delegation replaces work; the root and other workers must not repeat the same investigation or edit. A verifier checks a defined risk independently, not the entire task a second time.
- Every spawn must specify an allowed native role and `fork_turns = "none"`. Supply objective, ownership, interfaces, constraints, relevant evidence and acceptance checks in the handoff. Only when essential, use the smallest positive integer string for recent turns. Never omit `fork_turns` or use `"all"`; full-history inheritance can defeat model routing.
- Use no nested delegation, including spawning another Codex process as a workaround. Use native waits rather than busy polling. Close finished threads when they are no longer needed: the configured cap counts open child threads, not just workers currently using tools.
- Parallelize only independent work with an expected wall-clock or verification benefit. Writers need separate authorized worktrees or demonstrably disjoint ownership without shared Git, build or state collisions.
- Workers resolve ordinary implementation choices within their scope. Return `DECISION REQUIRED` for a material change to the agreed contract, architecture, security boundary, data integrity or backward compatibility; include evidence and a recommendation. Do not bounce routine choices back to the root.
- Production writes, pushes, migrations and deployments require the user's existing authorization or an applicable approved runbook. These routing rules never grant permissions or weaken sandbox/approval policies.
- The root inspects actual diffs and decisive acceptance evidence, reruns the highest-risk checks as appropriate, and reports unresolved gaps. Do not blindly repeat every passing command.

<!-- codex-profiles:end -->
