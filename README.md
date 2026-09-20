# Codex profiles

Local Codex routing presets with an explicit separation between the **root profile** and the **agent mode**.

## Profiles and modes

| Profile | Default root | Default mode | Team workers | Team child cap |
|---|---|---|---|---:|
| `lite` | Terra medium | fixed team | Luna Max | 1 |
| `strict-common` | Sol xhigh | fixed team | Luna Max | 4 |
| `private` | Astra high | **solo** | Luna Max + Sol High | 2 |
| `work` | Sol xhigh | **solo** | Luna Max; Sol High only in explicit personal lane | 2 |

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
- no automatic reviewer is added; the root verifies delegated work and owns final acceptance.

`private/team` uses Luna Max for cheap/simple/mechanical/well-specified bounded work and Sol High for substantial bounded implementation or non-trivial debugging.

`work/team` uses Luna Max for ordinary work objectives. Sol High becomes available only when the user explicitly marks the current objective as personal, for example `это личная задача`. That declaration applies only to the current coherent objective and direct follow-ups. Selecting Astra as the root does not activate the personal lane.

## Managed model catalog

Every profile installation captures the current client's real metadata with:

```powershell
codex debug models
```

and writes:

```text
~/.codex/models-managed.json
```

The catalog preserves the captured records and top-level metadata, with one intentional compatibility override:

```json
"gpt-5.6-luna": {
  "multi_agent_version": "v2"
}
```

Luna remains pinned to **Max** wherever this repository delegates to it.

For `lite`, the same generated catalog is additionally filtered to Terra + Luna only. For the other profiles, the complete captured catalog is retained.

The catalog is rebuilt on `install`; changing only `solo`/`team` reuses the existing generated snapshot. Fully restart Codex after an install or mode switch because the client can retain the previous catalog/configuration snapshot until restart.

For offline/testing installs, pass captured metadata explicitly:

```powershell
python scripts/manage_profile.py install private --models PATH_TO_CAPTURED_MODELS_JSON
```

## Lifecycle

Preview and install a profile:

```powershell
python scripts/manae_profile.py install private --dry-run
python scripts/manage_profile.py install private
```

Install directly into team mode:

```powershell
python scripts/manage_profile.py install private --mode team
python scripts/manage_profile.py install work --mode team
```

Switch `private` or `work` without reinstalling the root profile or rebuilding the catalog:

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
python scripts/validate.py --profile private --managed-catalog $HOME\.codex\models-managed.json
```

See:

- [installation and switching](docs/install.md)
- [routing policy](docs/routing-policy.md)
- [verification](docs/verification.md)
- [removal](docs/remove.md)
