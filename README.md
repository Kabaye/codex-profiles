# Codex routing rules

Four mutually exclusive local Codex routing presets. Reviewed on **2026-09-08**, against the **0.153.4** source/catalog plus current Multi-Agent V2 source/tests and documentation. Account/client metadata and the live smoke test remain the authority for an installed machine.

| Profile | Initial root | Visible root models | Delegated work | Open child cap | Memory models |
|---|---|---|---|---:|---|
| [lite](lite/install-lite.md) | Terra medium | **Terra + Luna only** | Luna Max only | 1 | Luna / Luna |
| [x5](x5/install-x5.md) | Sol xhigh | Normal account catalog | Luna Max only | 4 | Luna / Luna |
| [x20](x20/install-x20.md) | Astra high | Normal account catalog | Sol high only | 4 | Codex/provider defaults |
| [x20-work](x20-work/install-x20-work.md) | Sol xhigh; manual Astra root available | Normal account catalog | Luna Max by default; Sol high after explicit personal-task declaration | 4 | Luna / Luna |

All four profiles set `[features.multi_agent_v2] multi_agent_mode_hint_text = ""`. The empty custom hint suppresses Codex's effort-dependent built-in `<multi_agent_mode>` developer message, so the applicable `AGENTS.md` profile decides when delegation is useful instead of non-Ultra efforts silently becoming explicit-request-only or Ultra silently changing to a separate built-in proactive policy. The profiles do not set `multi_agent_v2.enabled = true` merely to force a backend version.

All four profiles also explicitly enable Codex experimental context management with `[features.context_management] experimental_mode = true`. This is an intentional experimental setting and is separate from Memories/model routing.

`lite` is intentionally restricted. Its installation generates `models-lite.json` by filtering the **real** Codex model metadata down to `gpt-5.6-terra` and `gpt-5.6-luna`; it does not manufacture capabilities. Terra Medium is the default root and Luna Max is the only child model. GPT-5.6 Sol and GPT-6/Astra must not be visible in this profile.

The other three profiles use the normal account/provider model catalog. The user's root model/effort selection is authoritative: runtime routing never changes it.

`x20-work` has one explicit switch. Every unmarked objective uses Luna Max for delegation. If the user explicitly says that the current objective is personal (for example, `это личная задача`), Codex acknowledges that once and may use the pinned Sol High worker for that objective and its direct follow-ups. A new unrelated objective resets to Luna-first. The profile never infers personal mode from repository context, task difficulty, or the selected root model. Selecting Astra changes only the root and never activates Sol or Astra children automatically.

`x20` is quality-first and intentionally simple: Astra High is the root for hard reasoning, architecture, difficult debugging, integration and final acceptance; Sol High is the only delegated worker for substantial implementation, exploration, ordinary debugging, tests/builds/logs and tool-heavy execution. There is no Astra child role. Astra xhigh/max remains a manual root escalation for unusually difficult sessions.

For `x5`, `x20` and `x20-work`, the technical child cap is **4**, but normal routing should use zero to two. A third or fourth child is for genuinely independent workstreams with clear ownership and real parallel benefit, not for filling slots.

## One profile lifecycle

Use **one command surface for every profile**. Installing a profile means switching the whole routing setup to that profile; do not manually stack profiles.

```powershell
# Preview a switch
python scripts/manage_profile.py install x20-work --dry-run

# Install or switch to a profile
python scripts/manage_profile.py install x20-work

# Show the active managed profile
python scripts/manage_profile.py status

# Preview complete removal
python scripts/manage_profile.py remove --dry-run

# Remove all repository-owned profile artifacts
python scripts/manage_profile.py remove
```

Replace `x20-work` with `lite`, `x5`, or `x20` as needed. `lite` automatically captures `codex debug models` and builds the restricted Terra+Luna catalog; for offline/testing use `--models PATH_TO_CAPTURED_MODELS_JSON`.

`install PROFILE` first removes/replaces older **repository-owned routing state** and then installs the destination profile. It manages:

- routing-owned `config.toml` keys;
- the managed `AGENTS.md` profile block, including exact legacy unmarked blocks when Git history is available;
- native worker roles and generated `default` / `worker` / `explorer` aliases;
- stale historical Luna/Sol/Astra worker files that exactly match versions shipped by this repository;
- `models-lite.json` when entering or leaving `lite`.

Unrelated configuration and unrelated roles such as a custom `sol-advisor.toml` are preserved. A modified/unknown file that collides with a repository-owned role or a modified legacy AGENTS section is a **stop for review**, not something the manager deletes heuristically.

The lifecycle intentionally creates **no persistent backups**. It keeps only an in-process snapshot for best-effort rollback if a write fails during the current operation; no `profile-backups` or role `backups` directories are created.

After install/switch/remove, **fully restart Codex and start a new thread**. Old threads may retain old developer/context instructions.

Detailed behavior: [installation and switching](docs/install.md), [removal](docs/remove.md).

## Policy, evidence and validation

- [Routing/effort matrix and usage policy](docs/routing-policy.md)
- [Technical findings, sources and limitations](docs/research-2026-09-06.md)
- [Adversarial review and local smoke tests](docs/verification.md)

```sh
python scripts/validate.py
python -m unittest discover -s tests -v
```

**Limits:** role pins and a filtered catalog are stronger than prompting, but this is not a security or spending firewall. Configuration precedence, separate Codex processes, unsupported clients, organizational policy, or a client that ignores the empty mode-hint override can change effective behavior. Verify the selector, effective empty multi-agent mode hint, context-management setting and actual child model/effort in native session/config metadata. If the expected restrictions cannot be established, do not treat the profile as successfully installed.

The separate local Astra history/Skills playbook is not part of this routing repository.
