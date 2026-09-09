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

The preview reports the profile, files and role filenames that would change.

If the preflight reports an unknown or modified collision, stop and review it. The manager deliberately refuses to delete unknown files merely because their names resemble a routing role.

## 3. Install or switch

Example:

```powershell
python scripts/manage_profile.py install work
```

This is both the **install** and **switch** operation. There is no separate migration sequence required between `lite`, `strict-common`, `private`, and `work`.

The active ownership manifest is stored at `~/.codex/profiles/roles-state.json`, and generated compatibility aliases use the `profile-*.toml` prefix. A valid prior-generation manifest, marker block, profile identifier or alias filename is normalized during the same transition. Those legacy identifiers are migration inputs only, never supported `install PROFILE` values. If current and legacy manifests both exist, the manager stops for review instead of guessing which state owns the files.

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

Known historical routing keys such as scalar `features.multi_agent`, scalar `features.multi_agent_v2`, old V2 `enabled`/thread-cap recipes, old worker defaults and old repository model catalogs are cleaned during migration.

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

The manager removes any existing marked routing block and installs exactly one destination block.

It also scans the local Git history of this repository for exact older **unmarked** `agents-subset.md` versions and removes those exact historical routing blocks during migration. This is important for older installs made before the marker format existed.

If an old unmarked block was manually edited and no longer exactly matches repository history, the manager stops instead of guessing how much user text to delete. Remove/reconcile that modified legacy section once, then rerun the command.

All current profile instructions are fully profile-owned inside:

```text
<!-- codex-profiles:begin -->
...
<!-- codex-profiles:end -->
```

That includes the full `lite` instruction set, so switching away from `lite` no longer leaves its communication/workspace rules behind.

### Native roles

The manager calls the role lifecycle with exact-legacy adoption enabled.

It removes/replaces repository-owned:

- `luna-worker.toml`;
- `sol-worker.toml`;
- historical `astra-worker.toml`;
- generated `profile-default.toml`;
- generated `profile-worker.toml`;
- generated `profile-explorer.toml`.

Exact historical worker blobs shipped by this repository can be migrated automatically. Modified lookalikes are not silently deleted.

Unrelated role files, for example `sol-advisor.toml`, remain untouched unless they collide by a reserved routing role name.

### `lite` model catalog

When installing `lite`, the manager captures:

```powershell
codex debug models
```

and creates `~/.codex/models-lite.json` containing only the **real** Terra and Luna records. It refuses to manufacture missing models or efforts.

For offline/testing installation, provide previously captured metadata:

```powershell
python scripts/manage_profile.py install lite --models PATH_TO_CAPTURED_MODELS_JSON
```

Switching away from `lite` removes the repository-specific `models-lite.json` and its profile-owned config reference.

## 4. No persistent backups

The lifecycle intentionally creates **no backup files or backup directories**.

If a write fails during the current process, it keeps the pre-operation bytes only in memory and attempts an immediate rollback. Nothing is written under `profile-backups`, `backups`, or another persistent backup location.

This is deliberate. Use `--dry-run` before changing a profile if you want to inspect the transition first.

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
