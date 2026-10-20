# Codex profiles

Local Codex routing presets with an explicit separation between the **root profile** and the **agent mode**.

## Profiles and modes

| Profile | Default root | Default mode | Team workers | Team child cap |
|---|---|---|---|---:|
| `private` | GPT-6 Astra xhigh | **solo** | GPT-6 Luna Max + GPT-6.1 Sol xhigh | 3 |
| `work` | GPT-6.1 Sol xhigh | **solo** | GPT-6 Luna Max; GPT-6.1 Sol xhigh only in explicit personal lane | 3 |

Use the user's current root model and effort in both profiles.

### `solo`

`private` and `work` install in `solo` unless `--mode team` is supplied.

`solo` deliberately leaves Codex multi-agent behavior native:

- no profile routing block is installed into `AGENTS.md`;
- no custom worker TOMLs are installed;
- no profile `multi_agent_mode_hint_text` override is installed;
- no profile child-thread cap is installed.

Subagents therefore remain available through normal Codex behavior when the user explicitly asks for them. `solo` is not `agents.enabled = false`.

### `team`

`team` enables the repository's selective routing policy:

- delegate useful independent work, with up to three open child threads;
- select `luna_worker` or `sol_worker` and give each its own files and self-contained task;
- use `fork_turns = "none"`;
- keep architecture, integration and final acceptance in the root;
- assign independent review when the user explicitly requests it.

`private/team` is **Sol-first**: Sol handles implementation, debugging and complex or uncertain tasks. Luna handles mechanical edits, exploration and routine checks; growing complexity moves to Sol.

`work/team` uses Luna for ordinary work objectives. An explicit `это личная задача` enables the personal lane for that objective and direct follow-ups, using the same Sol-first policy as private.

## Global AGENTS.md

`codex-config` combines its shared `AGENTS.md` with `private/AGENTS.md` or `work/AGENTS.md` inside its own managed block in `$CODEX_HOME/AGENTS.md`.

In team mode, this repository adds the selected profile's `agents-subset.md` inside a separate `codex-profiles` block. Solo removes that routing block. Each manager preserves the other's block and unrelated user instructions.

Worker TOMLs are installed separately under `$CODEX_HOME/agents`; their developer instructions belong to the worker. The bot rules from `codex-config/bots/AGENTS.md` go to `$HOME/Projects/AGENTS.md` separately.

## Model catalog

`private` and `work` use the native Codex model catalog; no profile-specific catalog is generated. The retired `lite` profile is no longer installable. Switching from an older Lite installation to a supported profile removes its owned restricted catalog and roles.

## Lifecycle

Preview and install a profile:

```powershell
python scripts/manage_profile.py install private --dry-run
python scripts/manage_profile.py install private
```

Install directly into team mode:

```powershell
python scripts/manage_profile.py install private --mode team
python scripts/manage_profile.py install work --mode team
```

Switch `private` or `work` without reinstalling the root profile:

```powershell
python scripts/manage_profile.py mode team
python scripts/manage_profile.py mode solo
```

Mode updates preserve the configured root model and effort. An explicit `install PROFILE` applies that profile's defaults.

Show state:

```powershell
python scripts/manage_profile.py status
```

Remove repository-owned profile state:

```powershell
python scripts/manage_profile.py remove --dry-run
python scripts/manage_profile.py remove
```

`install PROFILE` is a complete profile switch. It deletes every existing top-level `agents/*.toml` file in the selected Codex home before writing the destination role set. In `private/work solo`, that destination role set is empty. Non-TOML files and unrelated configuration outside the repository-owned keys are preserved.

The ownership state is stored in `profiles/roles-state.json`. Version 2 records both `profile` and `mode`; an empty `owned` role set is valid for solo.

The lifecycle also removes historical `x5`/`x20`/`x20-work` routing artifacts, generated alias roles, old `models-lite.json`, and an old profile-owned `models.json` reference when identified safely.

No persistent backups are created. The managers keep only in-process bytes for best-effort rollback during the current operation.

After install, mode switch, or removal, fully restart Codex and start a new thread.

## Validation

```powershell
python scripts/validate.py
python -m unittest discover -s tests -v
```

Optional catalog checks:

```powershell
python scripts/validate.py --profile private --models PATH_TO_CAPTURED_MODELS_JSON
```

See:

- [installation and switching](docs/install.md)
- [routing policy](docs/routing-policy.md)
- [verification](docs/verification.md)
- [removal](docs/remove.md)
