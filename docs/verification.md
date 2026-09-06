# Verification and adversarial review

## Executed in the authoring environment

On 2026-09-06, Python 3.13 ran:

```text
python scripts/validate.py
PASS: four static profiles

python -m unittest discover -s tests -v
Ran 23 tests ... OK
```

The 23 test methods include all **12 directed profile switches**, all four alias sets, model+effort pins, nested-tool config disabled, idempotent install/remove, a dry-run that does not create a home, unrelated-file preservation, reserved-name collisions, modified/missing owned-file refusal, unsafe manifests, locks, symlinks, explicit known-blob/CRLF adoption, and rollback after an injected write failure. Model metadata tests use **synthetic fixtures**, including missing effort, malformed schema, duplicate slugs and destination-specific entitlement requirements. They do not represent the user's live catalog.

The migration helper writes only native role files and its ownership/backup records. It does not parse-rewrite user TOML or erase AGENTS sections. The manual merge/removal instructions are part of the installation and were reviewed for symmetry.

## Adversarial cases addressed

| Failure case | Design response | Boundary |
|---|---|---|
| lite selects Astra root and inherits it in a worker | Named Luna Max role, pinned built-in aliases/defaults; explicit no-history fork | Other roles/project overrides must be checked live |
| Worker model pin keeps an incompatible inherited effort | Every native role pins both fields | Backend/account acceptance needs live metadata |
| Full-history spawn silently inherits root | Omitted/`all` forks forbidden; named role required | Behavioral rule, not a tool-schema restriction |
| x20 burns Max on a trivial edit | No Max worker/default; no automatic root change; tiny tasks stay root | The user may manually select Max |
| x20 never benefits from Astra | Astra Medium root plus explicit Astra High eligibility for hard work | Routing quality requires representative tasks |
| x20-work ordinary work automatically spends Sol | Luna stays the configured/default alias; Sol is a named role selected only for clearly personal objectives or an explicit user request | Personal/work classification is behavioral and must be observed live |
| x20-work personal task is forced through Luna | Pinned Sol High role is installed; personal routing prefers it for substantial delegated work | Requires the task to be clearly personal or the user to request Sol |
| Selecting Astra root silently upgrades every child | Root selection and child-role selection are independent; default aliases remain Luna | External overrides can still change effective behavior |
| Root/children duplicate work | One owner, distinct verification question, no parallel same assignment | Requires behavioral observation |
| Nested V2 delegation bypasses max_depth | Child `agents.enabled = false`, no nested-process workaround | Verify effective runtime config |
| Parallelism merely multiplies work | Open-child cap 1/2; no slot-filling; one Astra child policy in x20 | One-Astra limit is not a separate backend counter |
| Old worker remains after switching | Ownership-based synchronization, tested all 12 directions | Unknown/modified files stop for review |
| Removal deletes user settings/catalogs | Role-only helper; explicit owned-key/block removal | Manual changes need their original-value record |
| Fake slugs/efforts/capabilities | Exact known pins, live metadata validator, no generated catalog | Metadata alone is not backend entitlement |

## Required local smoke tests — NOT RUN here

Use a fresh thread and tiny, read-only tasks in a disposable project. Keep the selected root fixed. Inspect native activity/session metadata, not a worker's self-description.

1. In lite, manually choose an available non-Luna root. Ask for one `luna_worker` to inspect a small file with explicit `fork_turns = "none"`. Verify actual `gpt-5.6-luna` / `max` and unchanged root. Repeat a minimal named compatibility-role check if that role is exposed by the client.
2. In x20-work, first test ordinary work: with Sol root or manually selected Astra root, perform a small delegated read and verify the default path remains Luna Max. Then start a clearly personal objective (or explicitly request `sol_worker`) and verify a substantial delegated read resolves to `gpt-5.6-sol` / `high`. Confirm that selecting Astra alone does not switch the child to Sol and that no Astra child role is installed.
3. In x20, verify one bounded Sol High read. Separately check that the Astra High role resolves correctly with a small declared role-validation task. Do not use Max or a costly benchmark just to test a model pin.
4. Inspect the effective cap (1 lite, 2 others), available roles, child `agents.enabled` and relevant project overrides. Where safely testable, attempt one extra open child beyond the cap; rejection/queuing must not start an additional paid child. Do not mistake an idle-but-open thread for a freed slot.
5. Verify the normal root selector is no longer hidden by the old routing-owned catalog. A corporate restriction is not a defect to bypass. Confirm no stale Sol role in lite/x5, both Luna and Sol roles in x20-work, and no stale Luna role in x20.
6. Confirm a simple question/tiny edit does not trigger delegation, a hard x20 task can select Astra High for a distinct reasoning responsibility, and ordinary work never changes root/effort automatically. These are behavior tests; static string checks cannot prove them.

Record client version, selected home/profile, effective config, actual model/effort and result. If any pin or routing invariant cannot be verified, keep execution in the current root without delegation and report the mismatch. Do not silently downgrade to a different worker or claim a hard guarantee.
