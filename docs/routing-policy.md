# Routing, effort and usage policy

This matrix is the **chosen repository policy**, not an experimentally proven optimum. Runtime instructions remain short; the rationale belongs here. [Evidence and technical boundaries](research-2026-09-06.md).

## Defaults and invariants

| Profile | Installation root | Visible models | Worker roles | Escalation | Open children |
|---|---|---|---|---|---:|
| lite | Terra medium | Terra + Luna only | Luna Max only | Stay on Terra/Luna; no Sol/Astra | 1 |
| x5 | Sol xhigh | Normal catalog | Luna Max only | Same root; no more expensive child | 2 |
| x20 | Astra medium | Normal catalog | Sol high; Astra high | One justified Astra child; root effort only manually selected | 2 |
| x20-work | Sol xhigh; manual Astra root available | Normal catalog | Luna Max by default; Sol high after explicit personal-task declaration | Keep stronger reasoning in selected root; no Astra worker | 2 |

`R` means the **current user-selected root at its current effort**. `L` = Luna Max, `S` = Sol High, `A` = Astra High. Explicit role files pin both model and effort. Tiny tasks should not create a worker in any profile.

For `lite`, the root selector is intentionally restricted to **Terra and Luna**. Terra Medium is the installation default. Sol 5.6 and GPT-6/Astra are absent from the profile and must not be used. Every delegated task is Luna Max.

For `x20-work`, `L` is always the default delegated path. Personal mode is entered only when the user explicitly states that the current objective is personal, for example `это личная задача`. Codex acknowledges that once; then `S` is preferred for substantial delegated work for that objective and its direct follow-ups. A new unrelated objective resets to `L`. Repository context, paths, task content, difficulty, and selecting Astra do not activate personal mode.

## Decision matrix

| Task | lite | x5 | x20 | x20-work |
|---|---|---|---|---|
| Simple question | R (normally Terra Medium) | R | R, no Max escalation | R |
| Tiny edit | R | R | R | R |
| Normal implementation | R or one useful L workstream | R contract + L execution | S for bounded work; R if tightly coupled | Default: L. Explicit personal mode: S. |
| Repository exploration | L if substantial; R synthesizes | L | S; A only for hard semantic questions | Default: L. Explicit personal mode: S when substantial. |
| Tool-heavy work/logs | L | L | S, including a worthwhile serial log/test loop | Default: L. Explicit personal mode: S for the quality-critical path. |
| Browser/computer work | L operations, R decisions | L operations, R decisions | S for repeatable operations; R/A for difficult visual reasoning | Default: L operations. Explicit personal mode: S for substantial execution; current R makes hard decisions. |
| Ordinary debugging | R/L owner | L evidence/fix, R decisions | S reproduction/fix | Default: L. Explicit personal mode: S. |
| Difficult debugging | L gathers evidence; Terra root reasons | L evidence, R hypothesis | R or one A workstream; stop superseded S owner | Default: L + current R reasoning. Explicit personal mode: S evidence/fix + current R reasoning. |
| Architecture/design | Terra root | R | R; A only for a distinct consequential question | Current R; worker only for bounded supporting work. |
| Deep research | L source collection, Terra root synthesis | L source collection, R synthesis | S collection, R synthesis; A for hard independent reasoning | Default: L collection. Explicit personal mode: S for substantial delegated analysis; R synthesizes. |
| Independent verification | Fresh read-only L when useful | Fresh read-only L when useful | Usually R/S; fresh A for named high-consequence risk | Default: fresh L. Explicit personal mode: fresh read-only S for a consequential named risk. |
| Tests/builds | Existing owner | Existing L owner | Existing S owner; avoid rerunning unchanged checks in A | Existing owner; do not create S merely to wait for a build. |
| Release/deployment | Authorized runbook only; Terra/Luna | Authorized L operations, R acceptance | Authorized S operations; A not a routine release supervisor | Authorized operations only; default L, explicit personal mode may use S. |
| Extreme reasoning problem | Terra root; user may manually raise Terra effort, but Sol/Astra remain unavailable | Current R; manual root choice | Current R; manual high/xhigh/max session may help | User chooses root; no automatic root switch or Astra child. |

These are default assignments, not a requirement to delegate every task in a row. A dependent serial task can stay in R when handing it off would add more cost than it removes.

## Effort choice and evidence

Terra Medium is both the bundled 0.153.4 default for Terra and the chosen `lite` startup setting. `lite` preserves Terra's real supported reasoning levels in its filtered catalog, so the user may manually raise Terra effort for an unusually hard task without gaining access to Sol or Astra.

Astra Medium is the deliberate startup setting for `x20`, while Sol High is the normal bounded execution worker. Astra High is the stronger worker role reserved for a consequential reasoning-heavy workstream or verification need. No profile automatically turns every task into a Max tree.

For a difficult `x20` session, the user can select High, then xhigh/max when the remaining reasoning justifies the cost. A root's effort is not dynamically changed by these instruction files. If the pinned Astra High worker cannot settle a problem, return its evidence to the selected root rather than silently changing its effort.

## Usage and context budget

Prefer zero/one child. A second open child must reduce wall-clock time on independent work or address a consequential independent verification need. At most one Astra child in `x20` is a **behavioral policy**, not a per-model backend quota.

Use a named native role and explicit `fork_turns = "none"`, with a self-contained evidence packet. A minimal positive integer string is an exception when recent context is indispensable. Never omit the parameter or use `"all"`.

In `lite`, the filtered catalog is part of the usage policy: Terra handles the root task and Luna handles all delegated execution. There is no hidden escalation path to Sol or Astra.

In `x20-work`, do not bounce the same personal workstream between Luna and Sol after the explicit personal declaration; Sol owns the quality-critical delegated path until that objective ends. A new unrelated objective resets to Luna-first unless the user explicitly marks it personal too.

API prices and benchmark dollar equivalents are **not subscription quota multipliers**. Exact relative x5/x20/work quota consumption is not established here. Record observed model/effort, elapsed time, user corrections, acceptance failures, total tokens where available and the actual usage UI separately.
