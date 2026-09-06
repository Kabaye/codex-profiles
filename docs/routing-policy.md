# Routing, effort and usage policy

This matrix is the **chosen repository policy**, not an experimentally proven optimum. Runtime instructions remain short; the rationale belongs here. [Evidence and technical boundaries](research-2026-09-06.md).

## Defaults and invariants

| Profile | Installation root | Worker roles | Escalation | Open children |
|---|---|---|---|---:|
| lite | User's current model/effort | Luna Max only | Hard decisions return to existing root | 1 |
| x5 | Sol xhigh | Luna Max only | Same root; no more expensive child | 2 |
| x20 | Astra medium | Sol high; Astra high | One justified Astra child; root effort only manually selected | 2 |
| x20-work | Sol xhigh; manual Astra root available | Luna Max by default; Sol high after explicit personal-task declaration | Keep stronger reasoning in selected root; no Astra worker | 2 |

`R` means the **current user-selected root at its current effort**, not an instruction to switch back to an installation default. `L` = Luna Max, `S` = Sol High, `A` = Astra High. Root model selection remains unrestricted by this repository's catalog. Explicit role files pin both model and effort. Tiny tasks should not create a worker in any profile.

For `x20-work`, `L` is always the default delegated path. Personal mode is entered only when the user explicitly states that the current objective is personal, for example `это личная задача`. Codex acknowledges that once; then `S` is preferred for substantial delegated work for that objective and its direct follow-ups. A new unrelated objective resets to `L`. Repository context, paths, task content, difficulty, and selecting Astra do not activate personal mode.

## Decision matrix

| Task | lite | x5 | x20 | x20-work |
|---|---|---|---|---|
| Simple question | R | R | R, no Max escalation | R |
| Tiny edit | R | R | R | R |
| Normal implementation | R or one useful L workstream | R contract + L execution | S for bounded work; R if tightly coupled | Default: L. Explicit personal mode: S. |
| Repository exploration | L if substantial | L | S; A only for hard semantic questions | Default: L. Explicit personal mode: S when substantial. |
| Tool-heavy work/logs | L | L | S, including a worthwhile serial log/test loop | Default: L. Explicit personal mode: S for the quality-critical path. |
| Browser/computer work | L operations, R decisions | L operations, R decisions | S for repeatable operations; R/A for difficult visual reasoning | Default: L operations. Explicit personal mode: S for substantial execution; current R makes hard decisions. |
| Ordinary debugging | R/L owner | L evidence/fix, R decisions | S reproduction/fix | Default: L. Explicit personal mode: S. |
| Difficult debugging | L evidence, R hypothesis | L evidence, R hypothesis | R or one A workstream; stop superseded S owner | Default: L + current R reasoning. Explicit personal mode: S evidence/fix + current R reasoning. |
| Architecture/design | R | R | R; A only for a distinct consequential question | Current R; worker only for bounded supporting work. |
| Deep research | L source collection, R synthesis | L source collection, R synthesis | S collection, R synthesis; A for hard independent reasoning | Default: L collection. Explicit personal mode: S for substantial delegated analysis; R synthesizes. |
| Independent verification | Fresh read-only L when useful | Fresh read-only L when useful | Usually R/S; fresh A for named high-consequence risk | Default: fresh L. Explicit personal mode: fresh read-only S for a consequential named risk. |
| Tests/builds | Existing owner, no new agent just to wait | Existing L owner | Existing S owner; avoid rerunning unchanged checks in A | Existing owner; do not create S merely to wait for a build. |
| Release/deployment | Authorized runbook only; R/L | Authorized L operations, R acceptance | Authorized S operations; A not a routine release supervisor | Authorized operations only; default L, explicit personal mode may use S. |
| Extreme reasoning problem | Current R; no different child | Current R; manual root choice | Current R; manual high/xhigh/max session may help | User chooses root; no automatic root switch or Astra child. |

These are default assignments, not a requirement to delegate every task in a row. A dependent serial task can stay in R when handing it off would add more cost than it removes. Conversely, a long, bounded execution loop can benefit from S even when R waits: context isolation and stronger execution can be legitimate benefits beyond parallelism.

## Effort choice and evidence

Astra medium is a deliberate startup setting for x20, **not** the bundled 0.153.4 default (which is low). Medium has promising firsthand evidence, but no broad controlled consensus. Sol High is an explicit execution-policy choice: bounded workers are not being asked to repeat the coordinator's full architecture analysis. Astra High is the one stronger worker role in x20. A failed task caused by missing permissions or broken fixtures is not evidence for higher effort.

For a difficult session, the user can select High, then xhigh/max when the remaining reasoning justifies the cost. A root's effort is not dynamically changed by these instruction files. No automatic Max worker is installed. If the pinned Astra High worker in x20 cannot settle a problem, return its evidence to the selected root; do not quietly change its effort or claim that a per-spawn override defeats the role pin.

Do not infer that Max always wastes usage: in some coding evaluations Astra Max used fewer tokens and cost about the same per task as Sol Max. Nor does this prove Max is optimal for ordinary questions, deterministic builds or every research task. Measure completed, accepted work including retries and review, not a single response or token price.

## Usage and context budget

Prefer zero/one child. A second open child must reduce wall-clock time on independent work or address a consequential independent verification need. At most one Astra child in x20 is a **behavioral policy**, not a per-model backend quota. Never create three agents for the same question and call agreement independent verification.

Use a named native role and explicit `fork_turns = "none"`, with a self-contained evidence packet. A minimal positive integer string is an exception when recent context is indispensable. Never omit the parameter or use `"all"`. Keep the root's requirements and decisions separate from raw logs; keep decisive evidence available through file references.

Model changes happen between coherent assignments, not after every phase. Reuse an owner through its fix/test loop. In `x20-work`, do not bounce the same personal workstream between Luna and Sol after the explicit personal declaration; Sol owns the quality-critical delegated path until that objective ends. A new unrelated objective resets to Luna-first unless the user explicitly marks it personal too.

API prices and benchmark dollar equivalents are **not subscription quota multipliers**. Exact relative x5/x20/work quota consumption is not established here. Record observed model/effort, elapsed time, user corrections, acceptance failures, total tokens where available and the actual usage UI separately. Work history and personal history should not be merged to manufacture one average optimum.
