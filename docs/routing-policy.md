# Routing, effort and usage policy

This matrix is the **chosen repository policy**, not an experimentally proven optimum. Runtime instructions remain short; the rationale belongs here. [Evidence and technical boundaries](research-2026-09-06.md).

## Defaults and invariants

| Profile | Installation root | Worker roles | Escalation | Open children |
|---|---|---|---|---:|
| lite | User's current model/effort | Luna Max only | Hard decisions return to existing root | 1 |
| x5 | Sol xhigh | Luna Max only | Same root; no more expensive child | 2 |
| x20 | Astra medium | Sol high; Astra high | One justified Astra child; root effort only manually selected | 2 |
| x20-work | Sol xhigh; manual Astra root available | Luna Max only under either root | Same selected root; no phrase/unlock | 2 |

`R` means the **current user-selected root at its current effort**, not an instruction to switch back to an installation default. `L` = Luna Max, `S` = Sol High, `A` = Astra High. Root model selection remains unrestricted by this repository's catalog. Child models outside a profile's listed roles are forbidden by policy. Explicit role files pin both model and effort. Tiny tasks should not create a worker in any profile.

## Decision matrix

| Task | lite | x5 | x20 | x20-work |
|---|---|---|---|---|
| Simple question | R | R | R, no Max escalation | R |
| Tiny edit | R | R | R | R |
| Normal implementation | R or one useful L workstream | R contract + L execution | S for bounded work; R if tightly coupled | R contract + L execution |
| Repository exploration | L if substantial | L | S; A only for hard semantic questions | L |
| Tool-heavy work/logs | L | L | S, including a worthwhile serial log/test loop | L |
| Browser/computer work | L operations, R decisions | L operations, R decisions | S for repeatable operations; R/A for difficult visual reasoning | L operations, current R decisions |
| Ordinary debugging | R/L owner | L evidence/fix, R decisions | S reproduction/fix | L evidence/fix, R decisions |
| Difficult debugging | L evidence, R hypothesis | L evidence, R hypothesis | R or one A workstream; stop superseded S owner | L evidence, current R reasoning |
| Architecture/design | R | R | R; A only for a distinct consequential question | Current R |
| Deep research | L source collection, R synthesis | L source collection, R synthesis | S collection, R synthesis; A for hard independent reasoning | L collection, current R synthesis |
| Independent verification | Fresh read-only L when useful | Fresh read-only L when useful | Usually R/S; fresh A for named high-consequence risk | Fresh read-only L; R acceptance |
| Tests/builds | Existing owner, no new agent just to wait | Existing L owner | Existing S owner; avoid rerunning unchanged checks in A | Existing L owner |
| Release/deployment | Authorized runbook only; R/L | Authorized L operations, R acceptance | Authorized S operations; A not a routine release supervisor | Authorized L operations, R acceptance |
| Extreme reasoning problem | Current R; no different child | Current R; manual root choice | Current R; manual high/xhigh/max session may help | User chooses root; no automatic switch or child upgrade |

These are default assignments, not a requirement to delegate every task in a row. A dependent serial task can stay in R when handing it off would add more cost than it removes. Conversely, a long, bounded execution loop can benefit from S even when R waits: context isolation and less expensive execution are legitimate benefits beyond parallelism.

## Effort choice and evidence

Astra medium is a deliberate startup setting for x20, **not** the bundled 0.153.4 default (which is low). Medium has promising firsthand evidence, but no broad controlled consensus. Sol High is an explicit execution-policy choice: bounded workers are not being asked to repeat the coordinator's full architecture analysis. Astra High is the one stronger worker role. A failed task caused by missing permissions or broken fixtures is not evidence for higher effort.

For a difficult session, the user can select High, then xhigh/max when the remaining reasoning justifies the cost. A root's effort is not dynamically changed by these instruction files. No automatic Max worker is installed. If the pinned Astra High worker cannot settle a problem, return its evidence to the selected root; do not quietly change its effort or claim that a per-spawn override defeats the role pin.

Do not infer that Max always wastes usage: in some coding evaluations Astra Max used fewer tokens and cost about the same per task as Sol Max. Nor does this prove Max is optimal for ordinary questions, deterministic builds or every research task. Measure completed, accepted work including retries and review, not a single response or token price.

## Usage and context budget

Prefer zero/one child. A second open child must reduce wall-clock time on independent work or address a consequential independent verification need. At most one Astra child is a **behavioral policy**, not a per-model backend quota. Never create three agents for the same question and call agreement independent verification.

Use a named native role and explicit `fork_turns = "none"`, with a self-contained evidence packet. A minimal positive integer string is an exception when recent context is indispensable. Never omit the parameter or use `"all"`. Keep the root's requirements and decisions separate from raw logs; keep decisive evidence available through file references.

Model downgrades happen between coherent assignments, not after every phase. Reuse an owner through its fix/test loop. On a justified Sol-to-Astra escalation, stop the old owner and transfer hypotheses, tried fixes, checks and unresolved questions. After a hard decision, new independent execution may return to Sol; do not pay for repeated context reconstruction merely to display an economical model name.

API prices and benchmark dollar equivalents are **not subscription quota multipliers**. Exact relative x5/x20/work quota consumption is not established here. Record observed model/effort, elapsed time, user corrections, acceptance failures, total tokens where available and the actual usage UI separately. Work history and personal history should not be merged to manufacture one average optimum.
