# Verification and adversarial review

## Static test status

The repository's Python tests and validator cover both routing policy and the **unified profile lifecycle**: canonical profile/alias naming, profile switching, config replacement, AGENTS replacement, role pins, manifest validation, preservation of unrelated state, no persistent backups, nested-agent disabling, collision handling, in-process rollback, model metadata, catalog rules, the required empty Multi-Agent V2 mode hint and experimental context management.

On 2026-09-09, the current revision passed the static validator and all 31 synthetic lifecycle tests on disposable Codex homes:

```text
python scripts/validate.py
python -m unittest discover -s tests -v
```

## Adversarial cases addressed

| Failure case | Design response | Boundary |
|---|---|---|
| Switching profiles leaves the current profile block in `AGENTS.md` | `manage_profile.py install PROFILE` replaces the existing `codex-profiles` block with exactly one destination block | Unmarked user-authored instructions remain outside lifecycle ownership |
| Switching profiles leaves the current workers/aliases | The ownership manifest drives exact role synchronization to the destination worker and generated `profile-*` aliases | Unknown or modified collisions stop for review |
| Switching from `lite` leaves its non-routing communication/workspace rules | The complete `lite` instruction file is inside the managed profile markers | Unmarked user-authored instructions remain outside lifecycle ownership |
| Switching profiles leaves old config values | Unified lifecycle removes/replaces profile-owned model, agent, memory, context and Multi-Agent V2 keys before applying the destination fragment | Unrelated custom `model_catalog_json` is not deleted silently; conflicting custom catalogs stop for review |
| Switching away from `lite` leaves the restricted catalog active | Lifecycle removes the profile-owned catalog reference and repository-specific `models-lite.json` | Effective higher-priority config still needs live inspection |
| Lifecycle creates unwanted backups | Profile and role managers create no persistent backup files/directories; tests assert `profile-backups` and `backups` are absent | Rollback is best-effort and only uses bytes held in the current process |
| Unrelated native roles are destroyed during cleanup | Only manifest-owned files are removed; unrelated roles such as `sol-advisor.toml` remain | A custom role deliberately using a reserved profile role name is a collision and stops |
| Codex injects an effort-dependent `<multi_agent_mode>` that blocks or changes profile delegation | Every profile requires `features.multi_agent_v2.multi_agent_mode_hint_text = ""`; validator/tests reject missing or non-empty hints and reject profile-owned `enabled` forcing | Effective config precedence and fresh-thread runtime behavior must still be checked |
| Experimental context management is missing in one profile | Validator requires `features.context_management.experimental_mode = true` in all four configs | Effective local config precedence must still be checked |
| lite still exposes Sol or Astra | `models-lite.json` is built from real metadata and validated to contain exactly Terra + Luna | Configuration precedence must be checked live |
| lite starts on Luna or another root | Config pins Terra Medium as the initial root | User can manually select Luna or another Terra effort inside the restricted catalog |
| lite delegates to Terra/Sol/Astra | Native and generated alias roles remain pinned to Luna Max; routing forbids other child models | Verify actual child metadata in a live thread |
| Worker model pin keeps an incompatible inherited effort | Every native role pins both model and effort | Backend/account acceptance needs live verification |
| Full-history spawn silently inherits root | Omitted/`all` forks are forbidden; named role required | Behavioral rule, not a tool-schema restriction |
| private burns xhigh/max on trivial work | Astra High is the default; xhigh/max remain manual root choices | User may manually choose a higher effort |
| private creates an Astra child | Only the Sol High role is part of the private profile | Verify the installed role set on a disposable home |
| work guesses that a task is personal | Personal mode requires an explicit user declaration | Behavioral rule; verify live |
| work ignores `это личная задача` | Rules require one acknowledgement and prefer Sol High for substantial delegated work | Requires live behavior verification |
| A new unrelated objective accidentally stays personal | Personal mode is scoped to the current objective/direct follow-ups | Objective boundaries are behavioral |
| Parallelism merely multiplies work | Cap is 1 in lite and 4 elsewhere; normal routing uses 0–2, with 3–4 only for independent work | Requires behavioral observation |

## Required lifecycle smoke test

On a disposable/test Codex home, verify the actual switch sequence:

```powershell
python scripts/manage_profile.py install work --dry-run
python scripts/manage_profile.py install work
python scripts/manage_profile.py status
python scripts/manage_profile.py install private
python scripts/manage_profile.py status
python scripts/manage_profile.py remove
python scripts/manage_profile.py status
```

Before the first install, add one unrelated test role and unrelated TOML/AGENTS text. After the switch and removal, confirm those unrelated values remain while the previously active profile's managed rules/roles do not. Also confirm no `~/.codex/profiles/profile-backups/` or `~/.codex/profiles/backups/` directory was created.

The repository's synthetic test `tests/test_manage_profile.py` covers this exact lifecycle without touching the real Codex home.

## Required live routing smoke tests

1. **All profiles:** inspect effective config after restart and confirm both `features.multi_agent_v2.multi_agent_mode_hint_text = ""` and `features.context_management.experimental_mode = true` are active. Do not infer success merely from repository templates.
2. **All profiles:** use a **new thread** after restart. Where native trace/debug metadata exposes prompt annotations, verify that Codex did not inject the built-in explicit-request-only or proactive `<multi_agent_mode>` developer message. Existing threads may legitimately retain an older generated message in their history.
3. **All profiles:** use a task with two clearly independent, substantial workstreams and do **not** explicitly say “use sub-agents”. Verify that delegation is governed by the profile's `AGENTS.md` policy rather than blocked solely because the user omitted an explicit delegation command. A profile may still choose zero workers when the work is serial, tiny or not worth handing off.
4. **lite:** confirm the selector shows exactly Terra + Luna, initial root is Terra Medium, and any delegated work is Luna Max with at most one open child.
5. **strict-common:** verify up to four Luna children can be opened, but normal routing does not create 3–4 without independent work.
6. **work:** verify unmarked work delegates to Luna when delegation is useful; after `это личная задача`, substantial delegated work uses Sol High. Confirm the effective child cap is 4. A large personal task with two independent repositories is a useful regression case: the root should be free to delegate without requiring a second user phrase such as “use agents”.
7. **private:** verify Astra High is the initial root, only `sol_worker` is installed for delegation, and the effective child cap is 4. No Astra child role should remain.
8. On strict-common/private/work, confirm the normal account catalog is active. On lite, confirm the intentional Terra+Luna catalog is active.
9. Confirm simple questions/tiny edits do not cause pointless delegation and root/workers do not duplicate the same work.

Record client version, selected home/profile, effective config, actual model/effort and result. If any required pin, catalog restriction, empty mode hint, context-management setting or lifecycle cleanup cannot be verified, treat installation as incomplete rather than silently substituting behavior.
