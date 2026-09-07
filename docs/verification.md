# Verification and adversarial review

## Static test status

The repository's Python test suite and validator cover profile switching, role pins, nested-agent disabling, collision handling, rollback, model metadata and catalog rules. A previous baseline passed on 2026-09-06 before the latest routing changes. The suite has been updated for the new policy, but this environment cannot execute a fresh checkout of the GitHub repository, so the current revision still requires a local rerun:

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
| Worker model pin keeps an incompatible inherited effort | Every native role pins both model and effort | Backend/account acceptance needs live verification |
| Full-history spawn silently inherits root | Omitted/`all` forks are forbidden; named role required | Behavioral rule, not a tool-schema restriction |
| x20 burns xhigh/max on trivial work | Astra High is the default; xhigh/max remain manual root choices | User may manually choose a higher effort |
| x20 recreates an Astra child | Only the Sol High role is installed in x20 | Verify stale role cleanup on migration |
| x20-work guesses that a task is personal | Personal mode requires an explicit user declaration | Behavioral rule; verify live |
| x20-work ignores `это личная задача` | Rules require one acknowledgement and prefer Sol High for substantial delegated work | Requires live behavior verification |
| A new unrelated objective accidentally stays personal | Personal mode is scoped to the current objective/direct follow-ups | Objective boundaries are behavioral |
| Parallelism merely multiplies work | Cap is 1 in lite and 4 elsewhere; normal routing uses 0–2, with 3–4 only for independent work | Requires behavioral observation |
| Old worker remains after switching | Ownership-based role synchronization covers all profile directions | Unknown/modified files stop for review |

## Required local smoke tests

1. **lite:** confirm the selector shows exactly Terra + Luna, initial root is Terra Medium, and delegated work is Luna Max.
2. **x5:** verify up to four Luna children can be opened, but normal routing does not create 3–4 without independent work.
3. **x20-work:** verify unmarked work delegates to Luna; after `это личная задача`, substantial delegated work uses Sol High. Confirm the effective child cap is 4.
4. **x20:** verify Astra High is the initial root, only `sol_worker` is installed for delegation, and the effective child cap is 4. No Astra child role should remain.
5. On x5/x20/x20-work, confirm the normal account catalog is active. On lite, confirm the intentional Terra+Luna catalog is active.
6. Confirm simple questions/tiny edits do not cause pointless delegation and root/workers do not duplicate the same work.

Record client version, selected home/profile, effective config, actual model/effort and result. If any required pin or catalog restriction cannot be verified, treat installation as incomplete rather than silently substituting another model.
