<!-- codex-routing-rules:begin -->
## Agent routing — x20-work

- The root model and effort selected by the user are authoritative. Profile defaults apply at installation, not as an instruction to switch a running root. Never change the root model/effort, enable Fast/Ultra, or alter configuration merely because a task seems difficult.
- Installation default: **GPT-5.6 Sol / xhigh**. The normal Codex model selector remains available, so the user may select **GPT-6 Astra** as root directly. This needs no trigger phrase, marker or separate authorization protocol.
- This profile has two delegated-work paths:
  - **ordinary work / unclear context:** prefer `luna_worker`, pinned to **GPT-5.6 Luna / max**;
  - **personal objective or explicit request for stronger delegated execution:** prefer `sol_worker`, pinned to **GPT-5.6 Sol / high**.
- Treat an objective as personal only when the user says so or the current project/conversation context already establishes that fact clearly. Do not infer personal mode from task difficulty, root model, repository complexity or the mere selection of Astra. If the classification is unclear, stay on the work-safe Luna default.
- The user may explicitly request `sol_worker` for any objective. That instruction is sufficient; do not require an exact phrase. Conversely, a clearly personal objective does not need the user to repeat a special phrase on every follow-up while the same objective continues.
- For personal objectives, use Sol High for substantial implementation, repository exploration, debugging and verification when delegation is useful. Do not depend on Luna for the quality-critical path unless the user explicitly prefers the cheaper worker or Luna is clearly sufficient for a separate low-risk operational subtask.
- For ordinary work, keep Luna-first delegation. Sol High remains available when the user explicitly asks for it, but task complexity alone does not automatically spend the stronger worker.
- Selecting Astra as root changes only the root. It does not automatically turn children into Astra or Sol. This profile intentionally installs no Astra worker; if stronger reasoning is needed, keep it in the user-selected root and use Sol High for delegated execution when appropriate.
- At most **two open subagent threads**; normally one. Never spend another worker just because a slot exists. Independent verification must target a named risk and use a fresh read-only assignment.
- Default/worker/explorer compatibility aliases remain pinned to Luna Max, so accidental unnamed/default delegation stays economical. Deliberately request `luna_worker` or `sol_worker` according to the rules above. If the requested model pin cannot be verified, keep that work in the current root rather than silently substituting another worker.

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
