# Verification and adversarial review

## Static test status

The repository's Python test suite and validator cover profile switching, role pins, nested-agent disabling, collision handling, rollback, model metadata and catalog rules. A previous 23-test baseline passed on 2026-09-06 before the latest Terra-first `lite` catalog change. The suite has been updated for the new policy, but this environment cannot execute a fresh checkout of the GitHub repository, so the current revision still requires a local rerun:

```text
python scripts/validate.py
python -m unittest discover -s tests -v
```

For a real `lite` installation also run the profile-specific metadata/catalog validation from `lite/install-lite.md`.

## Adversarial cases addressed

| Failure case | Design response | Boundary |
|---|---|---|
| lite still exposes Sol or Astra | `models-lite.json` is built from real metadata and validated to contain exactly Terra + Luna | Configuration precedence must be checked live |
| lite starts on Luna or another root | Config pins Terra Medium as the initial root | User can manually select Luna or another Terra effort inside the restricted catalog |
| lite delegates to Terra/Sol/Astra | Native/default compatibility roles remain pinned to Luna Max; routing forbids other child models | Verify actual child metadata in a live thread |
| lite fabricates model capabilities | Filter copies the real Terra/Luna records unchanged and only removes other entries | Source metadata must be captured from the real client/account |
| Worker model pin keeps an incompatible inherited effort | Every native role pins both model and effort | Backend/account acceptance needs live verification |
| Full-history spawn silently inherits root | Omitted/`all` forks are forbidden; named role required | Behavioral rule, not a tool-schema restriction |
| x20 burns Max on a trivial edit | No Max worker/default; no automatic root change | User may manually select Max |
| x20 never benefits from Astra | Astra Medium root plus Astra High eligibility for hard work | Routing quality requires representative tasks |
| x20-work guesses that a task is personal | Personal mode requires an explicit user declaration; repo/path/context/difficulty/root model must not activate it | Behavioral rule; verify live |
| x20-work ignores `это личная задача` | Rules require a one-time acknowledgement and prefer pinned Sol High for substantial delegated work | Requires live behavior verification |
| A new unrelated objective accidentally stays personal | Personal mode is scoped to the current objective/direct follow-ups; unrelated work resets to Luna-first | Objective boundaries are behavioral |
| Selecting Astra root silently upgrades every child | Root selection and personal-mode activation are independent; default aliases remain Luna | External overrides can still change behavior |
| Root/children duplicate work | One owner, distinct verification question, no parallel same assignment | Requires behavioral observation |
| Parallelism merely multiplies work | Open-child cap 1/2; no slot-filling; one Astra-child policy in x20 | One-Astra limit is behavioral |
| Old worker remains after switching | Ownership-based role synchronization covers all profile directions | Unknown/modified files stop for review |

## Required local smoke tests

Use a fresh thread and tiny, read-only tasks in a disposable project. Inspect native activity/session metadata, not a worker's self-description.

1. **lite:** capture the full real catalog, generate `models-lite.json`, and run `python scripts/validate.py --profile lite --models FULL.json --lite-catalog models-lite.json`. Restart Codex. Confirm the selector shows exactly **Terra and Luna**, never Sol/Astra. Confirm the initial root is `gpt-5.6-terra` / `medium`. Spawn one explicit `luna_worker` with `fork_turns = "none"` and verify `gpt-5.6-luna` / `max` while the root stays Terra.
2. **x20-work:** run an unmarked objective and verify delegated work stays Luna Max. Then start a new objective with `это личная задача`; verify Codex acknowledges it once and substantial delegated work resolves to `gpt-5.6-sol` / `high`. A direct follow-up stays personal; a new unrelated unmarked objective returns to Luna.
3. **x20:** verify one bounded Sol High workstream. Separately verify the Astra High role resolves correctly with a small role-validation task. Do not use Max merely to test a model pin.
4. Inspect the effective child-thread cap (1 for lite, 2 otherwise), available roles, child `agents.enabled` and relevant project overrides.
5. On x5/x20/x20-work, confirm the normal account catalog is not hidden by a routing-owned lite catalog. On lite, confirm the opposite: the intentional Terra+Luna catalog is active.
6. Confirm simple questions/tiny edits do not cause pointless delegation and that root/worker ownership does not duplicate the same work.

Record client version, selected home/profile, effective config, actual model/effort and result. If any required pin or catalog restriction cannot be verified, treat installation as incomplete rather than silently substituting another model.
