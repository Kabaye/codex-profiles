# Codex routing rules

Four mutually exclusive local Codex routing presets. Reviewed on **2026-09-06**, against the **0.153.4** source/catalog and current official documentation. Account/client metadata and the live smoke test remain the authority for an installed machine.

| Profile | Initial root | Delegated work | Open child cap | Memory models |
|---|---|---|---:|---|
| [lite](lite/install-lite.md) | Preserve the user's selection | Luna Max only | 1 | Luna / Luna |
| [x5](x5/install-x5.md) | Sol xhigh | Luna Max only | 2 | Luna / Luna |
| [x20](x20/install-x20.md) | Astra medium | Sol high; Astra high for justified difficult work | 2 | Codex/provider defaults |
| [x20-work](x20-work/install-x20-work.md) | Sol xhigh | Luna Max only, even under a manually selected Astra root | 2 | Luna / Luna |

All profiles use the **normal model catalog**, without manufacturing capabilities or hiding available root models. The user's model/effort selection is authoritative: runtime routing never changes it. `x20-work` has no trigger phrases, authorization marker or costly worker unlock protocol.

`x20` is quality-first, not an always-Max tree. Astra handles reasoning and synthesis; coherent execution can use Sol. Hard debugging, state interactions or consequential independent verification can justify a bounded Astra High worker. A difficult end-to-end task may stay on Astra when splitting it would lose quality or cost more retries. These choices are an explicit starting policy, not a benchmark-proven universal optimum.

## Install, migrate, remove

Read [installation and migration](docs/install.md) before choosing a profile. Python **3.11+**, standard library only, is required for the role helper and validation. No package installation is performed by these scripts.

The helper installs native roles plus pinned `default`/`worker`/`explorer` compatibility aliases. It removes stale **owned** roles on a profile switch and refuses collisions or unreviewed edits. Config and AGENTS.md remain explicit, reviewable manual merges. The lite file retains its existing Russian communication/Git/workspace rules outside the routing markers.

Use [removal](docs/remove.md) to undo the active profile without deleting unrelated configuration or custom catalogs. The four profile-specific install/remove pages point to the same procedure, preventing drift.

## Policy, evidence and validation

- [Routing/effort matrix and usage policy](docs/routing-policy.md)
- [Technical findings, sources and limitations](docs/research-2026-09-06.md)
- [Adversarial review and local smoke tests](docs/verification.md)

```sh
python scripts/validate.py
python -m unittest discover -s tests -v
```

**Limits:** role pins are stronger than prompting, but this is not a model-spend firewall. A full-history/unnamed spawn, other custom/project/plugin roles, config precedence, separate Codex processes or unsupported clients can bypass a prompt policy. Verify the effective model/effort in native session metadata. If strict compliance cannot be established, do not delegate. No claim is made that these presets were executed on your computer or validated against your account quota.

The separate local Astra history/Skills playbook is not part of this routing repository.
