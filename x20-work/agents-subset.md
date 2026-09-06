<!-- codex-routing-rules:begin -->
## Agent routing — x20-work

- The root model and effort selected by the user are authoritative. Profile defaults apply at installation, not as an instruction to switch a running root. Never change the root model/effort, enable Fast/Ultra, or alter configuration merely because a task seems difficult.
- Installation default: **GPT-5.6 Sol / xhigh**. The normal Codex model selector remains available, so the user may select **GPT-6 Astra** as root directly.
- **Default delegated mode is always work-safe:** use `luna_worker`, pinned to **GPT-5.6 Luna / max**. Do not infer that an objective is personal from the repository, path, project name, conversation context, task content, task difficulty, root model, or the user's selection of Astra.
- Personal delegated mode is enabled only when the user explicitly states that the current objective is personal, for example: `это личная задача`. Natural-language equivalents are acceptable only when they explicitly say the objective is personal; do not infer this indirectly.
- When the user explicitly marks the objective as personal, immediately acknowledge it once with a short confirmation such as: `Понял: это личная задача. Для делегирования можно использовать Sol High.` Do not ask for another confirmation.
- After that acknowledgement, prefer `sol_worker`, pinned to **GPT-5.6 Sol / high**, for substantial delegated implementation, repository exploration, debugging, research, and verification where delegation is useful. Luna is not required for the quality-critical delegated path of that personal objective.
- Personal mode applies to the current coherent objective and its direct follow-ups. A new unrelated objective returns to the default Luna-first mode unless the user explicitly marks that new objective as personal too.
- Selecting Astra as root changes only the root. It does not activate personal mode and does not automatically turn children into Astra or Sol. This profile intentionally installs no Astra worker; stronger reasoning stays in the user-selected root.
- At most **two open subagent threads**; normally one. Never spend another worker just because a slot exists. Independent verification must target a named risk and use a fresh read-only assignment.
- Default/worker/explorer compatibility aliases remain pinned to Luna Max, so accidental unnamed/default delegation stays economical. In personal mode deliberately request `sol_worker`; otherwise deliberately request `luna_worker`. If the requested model pin cannot be verified, keep that work in the current root rather than silently substituting another worker.

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
