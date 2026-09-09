# Installation and switching

Use one lifecycle for all four profiles. Installing a profile means **switching the complete repository-owned routing setup** to that profile; do not layer one profile on top of another.

The supported command surface is:

```powershell
python scripts/manage_profile.py install PROFILE --dry-run
python scripts/manage_profile.py install PROFILE
```

where `PROFILE` is one of:

- `lite`
- `strict-common`
- `private`
- `work`

The helper requires Python 3.11+ and uses only the standard library.

## 1. Close Codex and identify the correct home

Fully close the Codex client whose configuration you are changing.

The helper resolves Codex home in this order:

1. `--home PATH` when explicitly supplied;
2. `CODEX_HOME`;
3. `~/.codex`.

Desktop, CLI and IDE installations can use different homes. Do not assume they are identical.

For a separate home:

```powershell
python scripts/manage_profile.py --home C:\path\to\.codex install work --dry-run
python scripts/manage_profile.py --home C:\path\to\.codex install work
```

## 2. Always preview first

Example:

```powershell
python scripts/manage_profile.py install work --dry-run
```

The preview reports the profile, files and role filenames that would change. Review the selected Codex home carefully: installation deletes every existing top-level `agents/*.toml` file there, including unrelated and custom roles.

## 3. Install or switch

Example:

```powershell
python scripts/manage_profile.py install work
```

This is both the **install** and **switch** operation between `lite`, `strict-common`, `private`, and `work`.

The active ownership manifest is stored at `<selected-home>/profiles/roles-state.json`, and generated aliases use the `profile-*.toml` prefix. The lifecycle accepts only the four profile identifiers listed above, the `codex-profiles` managed marker namespace, and this manifest and alias layout.

The role reset applies to the **selected Codex home** resolved in step 1. It is non-recursive and covers exactly the TOML files directly under `<selected-home>/agents/`. Nested directories and non-TOML files are outside this deletion scope.

The lifecycle performs these operations as one profile transition:

### `config.toml`

It removes/replaces profile-owned keys from an older profile and installs the destination values while preserving unrelated keys in the same TOML tables.

Managed current keys include:

- top-level `model` and `model_reasoning_effort`;
- profile-owned `model_catalog_json` when entering/leaving `lite`;
- `[agents]` defaults and open-child cap;
- `[features.multi_agent_v2] multi_agent_mode_hint_text`;
- `[features.context_management] experimental_mode`;
- profile-owned `[memories]` model selectors.

An unrelated custom `model_catalog_json` is **not** silently removed. If one is active and conflicts with a destination profile, installation stops for explicit review.

All four current profiles set:

```toml
[features.multi_agent_v2]
multi_agent_mode_hint_text = ""
```

The profiles intentionally do not force `multi_agent_v2.enabled = true`. The empty custom hint suppresses Codex's effort-dependent built-in `<multi_agent_mode>` message so the active profile's `AGENTS.md` decides when to delegate.

All four also set:

```toml
[features.context_management]
experimental_mode = true
```

### `AGENTS.md`

The manager removes the existing `codex-profiles` marked block and installs exactly one destination block.

All current profile instructions are fully profile-owned inside:

```text
<!-- codex-profiles:begin -->
...
<!-- codex-profiles:end -->
```

That includes the full `lite` instruction set, so switching away from `lite` no longer leaves its communication/workspace rules behind.

### Native roles

Installation first deletes every existing top-level `<selected-home>/agents/*.toml` file. This includes profile-owned, unmanaged, unrelated, and custom role files such as `sol-advisor.toml`. It does not preserve or adopt any existing role file.

It then writes only the destination profile's required roles from this set:

- `luna-worker.toml`;
- `sol-worker.toml`;
- generated `profile-default.toml`;
- generated `profile-worker.toml`;
- generated `profile-explorer.toml`.

After a successful install, the selected home's top-level `agents` directory contains only the destination profile roles. The ownership manifest records that final set.

Modified or missing roles from the previous installation and a malformed previous `profiles/roles-state.json` do not block `install PROFILE`; installation treats them as disposable old profile artifacts and replaces the manifest. Unsafe links, non-regular files, and an active operation lock still stop the operation. The separate `remove` command remains manifest-validated and fail-closed.

Installation also deletes artifacts left by the historical `x5`, `x20`, and `x20-work` layouts: the marked `codex-routing-rules` instruction block (including its old routing heading), old profile-only feature keys, the top-level `routing-rules/` state/backups directory, and `models.json` when the active catalog reference identifies it as the old profile-owned catalog. An unmarked routing heading or unmatched marker remains a pre-write safety stop because it has no reliable boundary from unrelated instructions.

### `lite` model catalog

When installing `lite`, the manager captures:

```powershell
codex debug models
```

and creates `<selected-home>/models-lite.json` containing only the **real** Terra and Luna records. It refuses to manufacture missing models or efforts.

For offline/testing installation, provide previously captured metadata:

```powershell
python scripts/manage_profile.py install lite --models PATH_TO_CAPTURED_MODELS_JSON
```

Switching away from `lite` removes the repository-specific `models-lite.json` and its profile-owned config reference.

## 4. No persistent backups

The lifecycle intentionally creates **no backup files or backup directories**, including for custom roles deleted from the selected home's top-level `agents` directory. No backup copy is written anywhere.

If a write fails during the current process, it keeps the pre-operation bytes only in memory and attempts an immediate rollback. Nothing is written under `profile-backups`, `backups`, or another persistent backup location.

This is deliberate. Use `--dry-run` before changing a profile to inspect the destructive role reset. If an existing custom role is needed elsewhere, move or recreate it outside this install operation before proceeding; the lifecycle does not retain a copy.

## 5. Restart and verify

After any install or switch:

1. fully restart Codex;
2. open a **new thread**;
3. run:

```powershell
python scripts/manage_profile.py status
python scripts/validate.py
python -m unittest discover -s tests -v
```

Then perform the relevant live smoke tests from [verification.md](verification.md).

Existing threads may retain old developer/context instructions, so they are not valid evidence that a newly installed profile is broken.

## Profile expectations

| Profile | Default root | Delegated model | Open child cap | Catalog |
|---|---|---|---:|---|
| `lite` | Terra medium | Luna max | 1 | Terra + Luna only |
| `strict-common` | Sol xhigh | Luna max | 4 | Normal account catalog |
| `private` | Astra high | Sol high | 4 | Normal account catalog |
| `work` | Sol xhigh | Luna max default; Sol high in explicit personal mode | 4 | Normal account catalog |

If the effective local configuration, account entitlement, organizational policy or client behavior prevents these expectations from being verified, treat the installation as incomplete rather than silently substituting another model or routing policy.
