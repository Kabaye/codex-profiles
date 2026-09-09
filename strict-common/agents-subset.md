<!-- codex-profiles:begin -->
## Agent routing — strict-common

- The root model and effort selected by the user are authoritative. Profile defaults apply at installation, not as an instruction to switch a running root. Never change the root model/effort, enable Fast/Ultra, or alter configuration merely because a task seems difficult.
- Installation default: **GPT-5.6 Sol / xhigh** for reasoning, architecture, decomposition, coordination, integration and acceptance.
- Delegation under this profile is proactive when useful: do not require a separate user phrase such as “use sub-agents” before spawning an allowed worker. Decide from the work itself whether a worthwhile independent handoff exists.
- All delegated work must use `luna_worker`, pinned to **GPT-5.6 Luna / max**. Never use another worker model or override its effort, including when the user selected another root.
- Delegate substantial, well-scoped implementation, exploration and tool-heavy execution when the handoff is worthwhile. Keep simple questions, tiny edits and tightly coupled reasoning in the root. Do not force every implementation through a worker.
- Luna executes the complete scoped workstream and its tests. Reasoning beyond Luna's assignment returns to the existing root; complexity does not authorize a more expensive child.
- At most **four open subagent threads**. Usually use zero to two. Use a third or fourth only for genuinely independent workstreams with clear ownership and real parallel value; never fill slots for their own sake. A verification job uses the same Luna pin in a fresh read-only assignment.
- The generated `default` / `worker` / `explorer` aliases are pinned to Luna Max, but deliberately request `luna_worker`. If the pin cannot be verified, keep the work in the selected root instead of spawning an unpinned agent.

## Ownership and coordination

- Assign one coherent workstream, including its implementation and fix/test loop, to one owner. Reuse that owner for follow-ups; change owner only when the responsibility or required model materially changes.
- Delegation replaces work; the root and other workers must not repeat the same investigation or edit. A verifier checks a defined risk independently, not the entire task a second time.
- Every spawn must specify an allowed native role and `fork_turns = "none"`. Supply objective, ownership, interfaces, constraints, relevant evidence and acceptance checks in the handoff. Only when essential, use the smallest positive integer string for recent turns. Never omit `fork_turns` or use `"all"`; full-history inheritance can defeat model routing.
- Use no nested delegation, including spawning another Codex process as a workaround. Use native waits rather than busy polling. Close finished threads when they are no longer needed: the configured cap counts open child threads, not just workers currently using tools.
- Parallelize only independent work with an expected wall-clock or verification benefit. Writers need separate authorized worktrees or demonstrably disjoint ownership without shared Git, build or state collisions.
- Workers resolve ordinary implementation choices within their scope. Return `DECISION REQUIRED` for a material change to the agreed contract, architecture, security boundary, data integrity or backward compatibility; include evidence and a recommendation. Do not bounce routine choices back to the root.
- Production writes, pushes, migrations and deployments require the user's existing authorization or an applicable approved runbook. These routing rules never grant permissions or weaken sandbox/approval policies.
- The root inspects actual diffs and decisive acceptance evidence, reruns the highest-risk checks as appropriate, and reports unresolved gaps. Do not blindly repeat every passing command.

<!-- codex-profiles:end -->
