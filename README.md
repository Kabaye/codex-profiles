# Codex profiles

Local Codex routing presets with an explicit separation between the **root profile** and the **agent mode**.

## Profiles and modes

| Profile | Default root | Default mode | Team workers | Team child cap |
|---|---|---|---|---:|
| `lite` | GPT-5.6 Terra medium | fixed team | GPT-5.6 Luna Max | 1 |
| `strict-common` | GPT-6 Sol xhigh | fixed team | GPT-6 Luna Max | 4 |
| `private` | GPT-6 Astra xhigh | **solo** | GPT-6 Luna Max + GPT-6 Sol xhigh | 2 |
| `work` | GPT-6 Sol xhigh | **solo** | GPT-6 Luna Max; GPT-6 Sol xhigh only in explicit personal lane | 2 |

The user's current root model and effort are authoritative. `work` does **not** restrict the root selector: the user may manually select Astra or another available root, and routing never changes that selection.

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

- normally keep the task in the root;
- normally use zero or one worker;
- at most two open child threads for `private` and `work`;
- every delegated spawn explicitly names `luna_worker` or `sol_worker`;
- no generated `default`, `worker`, or `explorer` aliases exist;
- no automatic reviewer is added; an independent reviewer is used only when the user explicitly requests one, while the root verifies delegated work and owns final acceptance.

`private/team` is **Sol-first for delegated implementation**. GPT-6 Sol xhigh handles substantial implementation, debugging, workflow/state changes, business or financial logic, contracts, migrations, cross-component behavior, adaptive UI work, and uncertain complexity. GPT-6 Luna Max is reserved for clearly mechanical, low-risk work with a settled specification; bounded scope or a small file count alone does not make a task a Luna task. If a Luna assignment grows materially, the root must reassess the model before continuing.

`work/team` uses GPT-6 Luna Max for ordinary work objectives. GPT-6 Sol xhigh becomes available only when the user explicitly marks the current objective as personal, for example `это личная задача`. In that personal lane, delegated implementation becomes Sol-first and Luna is restricted to clearly mechanical, low-risk work. That declaration applies only to the current coherent objective and direct follow-ups. Selecting Astra as the root does not activate the personal lane.

## Model catalog

`private`, `work`, and `strict-common` use the native Codex model catalog. GPT-6 Sol and GPT-6 Luna already advertise Multi-Agent V2 natively, so these profiles do not create or reference a custom catalog.

Only `lite` keeps a generated `models-managed.json` because it intentionally filters the visible model list to GPT-5.6 Terra + GPT-5.6 Luna and applies the legacy Luna V2 compatibility override.

For offline/testing lite installs:

```powershell
python scripts/manage_profile.py install lite --models PATH_TO_CAPTURED_MODELS_JSON
```

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
python scripts/validate.py --profile lite --managed-catalog $HOME\.codex\models-managed.json
```

See:

- [installation and switching](docs/install.md)
- [routing policy](docs/routing-policy.md)
- [verification](docs/verification.md)
- [removal](docs/remove.md)
