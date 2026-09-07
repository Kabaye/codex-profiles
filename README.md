# Codex routing rules

Four mutually exclusive local Codex routing presets. Reviewed on **2026-09-06**, against the **0.153.4** source/catalog and current official documentation. Account/client metadata and the live smoke test remain the authority for an installed machine.

| Profile | Initial root | Visible root models | Delegated work | Open child cap | Memory models |
|---|---|---|---|---:|---|
| [lite](lite/install-lite.md) | Terra medium | **Terra + Luna only** | Luna Max only | 1 | Luna / Luna |
| [x5](x5/install-x5.md) | Sol xhigh | Normal account catalog | Luna Max only | 4 | Luna / Luna |
| [x20](x20/install-x20.md) | Astra high | Normal account catalog | Sol high only | 4 | Codex/provider defaults |
| [x20-work](x20-work/install-x20-work.md) | Sol xhigh; manual Astra root available | Normal account catalog | Luna Max by default; Sol high after explicit personal-task declaration | 4 | Luna / Luna |

`lite` is intentionally restricted. Its installation generates `models-lite.json` by filtering the **real** Codex model metadata down to `gpt-5.6-terra` and `gpt-5.6-luna`; it does not manufacture capabilities. Terra Medium is the default root and Luna Max is the only child model. GPT-5.6 Sol and GPT-6/Astra must not be visible in this profile.

The other three profiles use the normal account/provider model catalog. The user's root model/effort selection is authoritative: runtime routing never changes it.

`x20-work` has one explicit switch. Every unmarked objective uses Luna Max for delegation. If the user explicitly says that the current objective is personal (for example, `это личная задача`), Codex acknowledges that once and may use the pinned Sol High worker for that objective and its direct follow-ups. A new unrelated objective resets to Luna-first. The profile never infers personal mode from repository context, task difficulty, or the selected root model. Selecting Astra changes only the root and never activates Sol or Astra children automatically.

`x20` is quality-first and intentionally simple: Astra High is the root for hard reasoning, architecture, difficult debugging, integration and final acceptance; Sol High is the only delegated worker for substantial implementation, exploration, ordinary debugging, tests/builds/logs and tool-heavy execution. There is no Astra child role. Astra xhigh/max remains a manual root escalation for unusually difficult sessions.

For `x5`, `x20` and `x20-work`, the technical child cap is **4**, but normal routing should use zero to two. A third or fourth child is for genuinely independent workstreams with clear ownership and real parallel benefit, not for filling slots.

## Install, migrate, remove

Read [installation and migration](docs/install.md) before choosing a profile. `lite` additionally requires its [profile-specific catalog step](lite/install-lite.md). Python **3.11+**, standard library only, is required for the role helper, catalog filter and validation. No package installation is performed by these scripts.

The role helper installs native roles plus pinned `default`/`worker`/`explorer` compatibility aliases. It removes stale **owned** roles on a profile switch and refuses collisions or unreviewed edits. Config and AGENTS.md remain explicit, reviewable manual merges. The lite file retains its existing Russian communication/Git/workspace rules outside the routing markers.

Use [removal](docs/remove.md) to undo the active profile without deleting unrelated configuration or custom catalogs. The four profile-specific install/remove pages point to the same procedure, preventing drift.

## Policy, evidence and validation

- [Routing/effort matrix and usage policy](docs/routing-policy.md)
- [Technical findings, sources and limitations](docs/research-2026-09-06.md)
- [Adversarial review and local smoke tests](docs/verification.md)

```sh
python scripts/validate.py
python -m unittest discover -s tests -v
```

For `lite`, also validate the generated restricted catalog as shown in `lite/install-lite.md`.

**Limits:** role pins and a filtered catalog are stronger than prompting, but this is not a security or spending firewall. Configuration precedence, separate Codex processes, unsupported clients, or organizational policy can change effective behavior. Verify the selector and actual child model/effort in native session metadata. If the expected restrictions cannot be established, do not treat the profile as successfully installed.

The separate local Astra history/Skills playbook is not part of this routing repository.
