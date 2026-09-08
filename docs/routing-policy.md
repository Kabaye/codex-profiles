# Routing, effort and usage policy

This matrix is the **chosen repository policy**, not an experimentally proven optimum. Runtime instructions remain short; the rationale belongs here. [Evidence and technical boundaries](research-2026-09-06.md).

## Defaults and invariants

| Profile | Installation root | Visible models | Worker roles | Open children |
|---|---|---|---|---:|
| lite | Terra medium | Terra + Luna only | Luna Max only | 1 |
| x5 | Sol xhigh | Normal catalog | Luna Max only | 4 |
| x20 | Astra high | Normal catalog | Sol high only | 4 |
| x20-work | Sol xhigh; manual Astra root available | Normal catalog | Luna Max by default; Sol high after explicit personal-task declaration | 4 |

`R` means the **current user-selected root at its current effort**. `L` = Luna Max. `S` = Sol High. Explicit role files pin both model and effort. Tiny tasks should not create a worker in any profile.

All four profiles set:

```toml
[features.multi_agent_v2]
multi_agent_mode_hint_text = ""
```

The empty configured hint is intentional. Current Codex can otherwise inject an effort-dependent `<multi_agent_mode>` developer message: ordinary non-Ultra reasoning may become explicit-request-only, while Ultra may receive built-in proactive guidance. These presets instead keep the delegation trigger under the applicable `AGENTS.md` policy so changing root effort does not silently change routing semantics. The profiles do **not** set `features.multi_agent_v2.enabled = true` merely to force a V2 backend; the override controls mode guidance only.

For `lite`, the root selector is intentionally restricted to **Terra and Luna**. Terra Medium is the installation default. Sol 5.6 and GPT-6/Astra are absent from the profile and must not be used. Every delegated task is Luna Max.

For `x20-work`, `L` is always the default delegated path. Personal mode is entered only when the user explicitly states that the current objective is personal, for example `это личная задача`. Codex acknowledges that once; then `S` is preferred for substantial delegated work for that objective and its direct follow-ups. A new unrelated objective resets to `L`. Repository context, paths, task content, difficulty, and selecting Astra do not activate personal mode.

For `x5`, `x20` and `x20-work`, **4 is a ceiling, not a target**. Normal routing uses zero to two children. A third or fourth child is justified only for genuinely independent workstreams with clear ownership and real parallel value.

## Decision matrix

| Task | lite | x5 | x20 | x20-work |
|---|---|---|---|---|
| Simple question | R (normally Terra Medium) | R | R | R |
| Tiny edit | R | R | R | R |
| Normal implementation | R or one useful L workstream | R contract + L execution | R contract + S execution | Default: L. Personal: S. |
| Repository exploration | L if substantial; R synthesizes | L | S | Default: L. Personal: S when substantial. |
| Tool-heavy work/logs | L | L | S | Default: L. Personal: S for the quality-critical path. |
| Browser/computer work | L operations, R decisions | L operations, R decisions | S for bounded execution; R handles hard visual reasoning | Default: L operations. Personal: S for substantial execution. |
| Ordinary debugging | R/L owner | L evidence/fix, R decisions | S reproduction/fix; R accepts | Default: L. Personal: S. |
| Difficult debugging | L gathers evidence; Terra root reasons | L evidence, R hypothesis | R owns hard reasoning; S may reproduce/fix bounded parts | Default: L + current R reasoning. Personal: S evidence/fix + current R reasoning. |
| Architecture/design | Terra root | R | R | Current R; worker only for bounded supporting work. |
| Deep research | L collection, Terra root synthesis | L collection, R synthesis | S collection/execution, R synthesis | Default: L collection. Personal: S for substantial delegated analysis. |
| Independent verification | Fresh read-only L when useful | Fresh read-only L when useful | R or fresh read-only S for a named risk | Default: fresh L. Personal: fresh read-only S for a consequential named risk. |
| Tests/builds | Existing owner | Existing L owner | Existing S owner | Existing owner; do not create another worker merely to wait. |
| Release/deployment | Authorized runbook only; Terra/Luna | Authorized L operations, R acceptance | Authorized S operations, R acceptance | Authorized operations only; default L, explicit personal mode may use S. |
| Extreme reasoning problem | Terra root; user may manually raise Terra effort | Current R; manual root choice | Astra root; user may manually raise to xhigh/max | User chooses root; no automatic root switch. |

These are default assignments, not a requirement to delegate every task in a row. A dependent serial task can stay in `R` when handing it off would add more cost or context loss than it removes. Conversely, the user should not need to add a second phrase such as “use agents” when the applicable profile itself says delegation is useful; the empty mode hint prevents Codex's built-in effort policy from silently imposing that extra gate.

## Why Sol High workers instead of Sol xhigh

Workers receive **bounded, well-scoped assignments**: implementation, repository exploration, ordinary debugging, tests, logs, or tool-heavy execution. They are not supposed to redo the root's architecture and decomposition. For that shape of work, High is the default because it preserves strong reasoning while avoiding the extra latency/usage of xhigh on every delegated task.

Use xhigh at the **root** when the whole objective needs deeper reasoning. In `x20`, difficult reasoning stays with Astra High and the user can manually raise the Astra root to xhigh/max. In `x20-work`, Sol xhigh is already the installation root, so hard reasoning can stay there while Sol High workers execute bounded pieces. This keeps role separation clear: stronger root reasoning, efficient strong workers.

This is a routing policy, not a claim that Sol xhigh can never outperform High. If repeated real tasks show a bounded worker category that materially benefits from xhigh, add evidence before creating another permanent role.

## Effort choice

Terra Medium is both the bundled 0.153.4 default for Terra and the chosen `lite` startup setting. `lite` preserves Terra's real supported reasoning levels in its filtered catalog, so the user may manually raise Terra effort for an unusually hard task without gaining access to Sol or Astra.

`x5` and `x20-work` use Sol xhigh as their installation root. `x20` uses Astra High as its quality-first default. Astra xhigh/max is a manual escalation for unusually difficult sessions; routing never raises the active root effort automatically.

No profile automatically creates Max/xhigh workers.

## Usage and context budget

Use a named native role and explicit `fork_turns = "none"`, with a self-contained evidence packet. A minimal positive integer string is an exception when recent context is indispensable. Never omit the parameter or use `"all"`.

In `lite`, the filtered catalog is part of the usage policy: Terra handles the root task and Luna handles all delegated execution. There is no hidden escalation path to Sol or Astra.

In `x20`, Astra High owns the hard reasoning path and Sol High owns delegated execution. There is no Astra child role. Avoid creating multiple Sol workers for dependent phases of one workstream; reuse the same owner through its fix/test loop.

In `x20-work`, do not bounce the same personal workstream between Luna and Sol after the explicit personal declaration; Sol owns the quality-critical delegated path until that objective ends. A new unrelated objective resets to Luna-first unless the user explicitly marks it personal too.

API prices and benchmark dollar equivalents are **not subscription quota multipliers**. Exact relative quota consumption is not established here. Measure accepted completed work, retries, user corrections, elapsed time and observed usage rather than assuming a universal multiplier.
