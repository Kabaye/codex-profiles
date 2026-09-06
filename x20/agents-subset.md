<!-- codex-routing-rules:begin -->
## Agent routing — x20

- The root model and effort selected by the user are authoritative. Profile defaults apply at installation, not as an instruction to switch a running root. Never change the root model/effort, enable Fast/Ultra, or alter configuration merely because a task seems difficult.
- Installation default: **GPT-6 Astra / medium**. Use the root for synthesis, ambiguous reasoning, architecture, integration and final acceptance. This is a starting policy to validate on real tasks, not a claim that medium is universally optimal.
- `sol_worker` is pinned to **GPT-5.6 Sol / high** for bounded implementation, repository exploration, deterministic tool-heavy execution, logs and ordinary tests/builds. Delegate a substantial serial execution loop too when isolating noisy context or reducing expensive root work outweighs the handoff.
- `astra_worker` is pinned to **GPT-6 Astra / high** for a coherent workstream whose hard reasoning, state/concurrency interactions, difficult debugging, complex visual/computer work or high-consequence independent verification justifies it. Choose by the unresolved risk, not file count or the words "important" and "research".
- Do not blindly offload all tool use to Sol: difficult end-to-end coding or visual work may be more efficient on Astra with fewer retries. Keep tightly coupled work in the root when decomposition would lose essential context.
- Escalate a bounded Sol assignment to `astra_worker` when concrete evidence shows the remaining difficulty is reasoning, not a missing tool, permission, test fixture or requirement. Stop/close the previous owner and transfer its evidence; never run both on the same assignment. Avoid repeated blind retries.
- Use a fresh `astra_worker` verifier only for a named, consequential risk that tests or a cheaper review do not adequately cover. It receives requirements, diff and test evidence, not the implementer's conclusion as ground truth. Otherwise use root acceptance or a Sol verifier.
- High/xhigh/max root effort can be selected manually for a difficult session. Do not pretend text instructions change the active root effort. Pinned worker efforts cannot be escalated with a spawn override. There is no automatic Max worker or Ultra/Fast default.
- Once a hard decision is resolved, close the expensive assignment. Subsequent independent execution may use Sol; keep an existing Astra owner if switching would cost more context and rework than it saves. Do not repeatedly respawn for each phase.
- At most **two open subagent threads**. Usually zero or one; only one Astra child at a time as a routing policy. A second thread must have distinct ownership and actual parallel value. No Luna or other delegated models in this profile.
- Default/worker/explorer compatibility aliases are pinned to Sol High; deliberately use the named roles. If a required pin is unavailable, continue in the existing root and report the limitation rather than changing models silently.

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
