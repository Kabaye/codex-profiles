<!-- codex-routing-rules:begin -->
## Agent routing — x20-work

- The root model and effort selected by the user are authoritative. Profile defaults apply at installation, not as an instruction to switch a running root. Never change the root model/effort, enable Fast/Ultra, or alter configuration merely because a task seems difficult.
- Installation default: **GPT-5.6 Sol / xhigh**. Keep ordinary work usage controlled.
- The normal Codex model selector remains available. The user can select **GPT-6 Astra** as root directly; this requires no phrase, marker, separate authorization protocol or change to these rules.
- All delegated work uses `luna_worker`, pinned to **GPT-5.6 Luna / max**, even under an Astra root. No automatic Sol/Astra worker escalation is installed in this profile.
- Delegate well-scoped substantial implementation, exploration, browser operations, tests and other execution to Luna when useful. Keep trivial tasks and tightly coupled reasoning in the current root. Difficult decisions return to that root, whatever model the user selected.
- At most **two open subagent threads**; normally one. Never spend another worker just because a slot exists. Independent verification is fresh and read-only, also Luna Max.
- Default/worker/explorer compatibility aliases are pinned to Luna Max, but deliberately request `luna_worker`. If pinning is unavailable, keep work in the root. Do not use other custom roles to evade the policy.

## Ownership and coordination

- Assign one coherent workstream, including its implementation and fix/test loop, to one owner. Reuse that owner for follow-ups; change owner only when the responsibility or required model materially changes.
- Delegation replaces work; the root and other workers must not repeat the same investigation or edit. A verifier checks a defined risk independently, not the entire task a second time.
- Every spawn must specify an allowed native role and `fork_turns = "none"`. Supply objective, ownership, interfaces, constraints, relevant evidence and acceptance checks in the handoff. Only when essential, use the smallest positive integer string for recent turns. Never omit `fork_turns` or use `"all"`; full-history inheritance can defeat model routing.
- Use no nested delegation, including spawning another Codex process as a workaround. Use native waits rather than busy polling. Close finished threads when they are no longer needed: the configured cap counts open child threads, not just workers currently using tools.
- Parallelize only independent work with an expected wall-clock or verification benefit. Never fill slots for their own sake. Writers need separate authorized worktrees or demonstrably disjoint ownership without shared Git, build or state collisions.
- Workers resolve ordinary implementation choices within their scope. Return `DECISION REQUIRED` for a material change to the agreed contract, architecture, security boundary, data integrity or backward compatibility; include evidence and a recommendation. Do not bounce routine choices back to the root.
- Production writes, pushes, migrations and deployments require the user's existing authorization or an applicable approved runbook. These routing rules never grant permissions or weaken sandbox/approval policies.
- The root inspects actual diffs and decisive acceptance evidence, reruns the highest-risk checks as appropriate, and reports unresolved gaps. Do not blindly repeat every passing command.

<!-- codex-routing-rules:end -->
