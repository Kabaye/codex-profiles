<!-- codex-profiles:begin -->
## Agent routing — strict-common

- The user-selected root model/effort always wins; installation defaults to **GPT-6.1 Sol / xhigh**. Do not switch the root, enable Fast/Ultra, or modify settings based on task difficulty.
- Delegation is proactive when genuinely useful. Use **only `luna_worker` (GPT-6 Luna / max)** for every child, regardless of root selection; never override its effort or spawn an unpinned alias (`default`, `worker`, `explorer`).
- Usually keep the task in root or use up to two workers; **at most four open child threads**. Use a third/fourth only for independent, worthwhile workstreams. Small or tightly coupled work stays in root. A verifier is another Luna worker with read-only scope.
- Each spawn explicitly selects `luna_worker`, `fork_turns = "none"`, and a self-contained goal, ownership, interfaces, constraints, evidence and acceptance checks. Only when essential may recent turns be passed using the smallest positive numeric string; never use `"all"` or omit the parameter.
- Assign implementation, repair and tests to one owner; reuse that owner for related fixes. Delegation replaces, not duplicates, root/peer work. Parallel writers need disjoint ownership and must not collide in shared Git/build/state; creating worktrees requires permission.
- Workers handle routine decisions; return **DECISION REQUIRED** with evidence and a recommendation for material contract, architecture, security, integrity or compatibility choices. Root retains architecture, hard reasoning, integration and final acceptance; inspect diffs and high-risk checks without rerunning everything.
- No nested delegation, including launching another Codex. Use native waits instead of polling and close completed threads to free open-thread capacity. Production writes, pushes, migrations and deployments still require user authorization or an approved runbook; routing never bypasses sandbox or approval policy.
<!-- codex-profiles:end -->
