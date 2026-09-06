# Installation and migration

Install one profile at a time. This procedure targets the reviewed **Codex 0.153.4** behavior, not every older client. The supplied `config.toml` is a merge fragment, never a replacement for the user's whole config. See [technical evidence](research-2026-09-06.md) and [smoke tests](verification.md).

## 1. Identify and preserve the real setup

Close active Codex threads before changing role files. Run `codex --version` and `python --version`; the helper requires Python 3.11+. Do not automatically install software or update a managed work client.

Resolve the actual Codex home: explicit `--home`, otherwise `CODEX_HOME`, otherwise the documented `~/.codex` default. Check the desktop/CLI/IDE environment separately; they can use different configuration. The commands below run from this repository root.

Make private, timestamped backups of the existing `config.toml`, `AGENTS.md` and affected role files. Record the original values of every key to be changed. Do not copy credentials, auth files, session history or entire databases. Do not commit these backups. Keep personal and work homes separate.

Inspect effective configuration layers, selected profiles, project `.codex/config.toml`, project agent files and any plugin/managed overrides. Unknown role overrides require review. Do not remove organizational model restrictions, permissions, sandbox policy or unrelated settings to make this preset work.

## 2. Validate real models without manufacturing a catalog

If the existing `model_catalog_json` points to a catalog created by an older version of **this repository**, back up the line and temporarily remove/comment that line. Keep the file itself. Do not clear an administrator's or unrelated custom catalog; resolve that conflict before installation.

Capture `codex debug models` from the actual installed account, using a private scratch directory. Save its JSON output unchanged and validate it:

```powershell
python scripts/validate.py
python scripts/validate.py --profile x20 --models PATH_TO_CAPTURED_MODELS_JSON
```

Replace `x20` with the destination profile and the path placeholder with the real captured file path. If this client's command/output differs, discover its supported metadata interface instead of inventing entries or JSON fields. The validator expects `models[]`, `slug` and `supported_reasoning_levels[].effort`; an unrecognized format is a stop, not an invitation to rewrite capabilities. With `--profile`, live metadata requirements cover only that destination: installing lite does not require Astra entitlement. Without it, all four profiles are checked.

Never set `supported_reasoning_levels`, `multi_agent_version`, context sizes or model visibility in a copied catalog to claim support. These presets do not generate `models.json`. Catalog presence does not prove backend entitlement; the smoke test is still required. Do not silently substitute another worker when a required pin is unavailable.

## 3. Merge the destination config

Merge the destination `PROFILE/config.toml` into the existing file, updating keys in their existing tables. Do not append duplicate `[agents]` or `[memories]` tables. Place root-level `model` and `model_reasoning_effort` before table headers.

Remove only settings introduced by an old routing profile:

- The old routing-owned `model_catalog_json` line; leave its former file archived.
- Legacy routing-owned `features.multi_agent` and `features.multi_agent_v2` fields (`enabled`, `multi_agent_mode_hint_text`, `max_concurrent_threads_per_session`). Preserve unrelated feature settings and remove empty headers only when appropriate.
- Old routing-owned role registrations or conflicting `agents.max_threads`/`max_depth` settings. Do not use `max_depth` as a V2 nesting guarantee.

The new `agents.max_concurrent_threads_per_session` value is **1 for lite, 2 otherwise**, counting open children and excluding the root. Do not carry over the old root-plus-two value `3`.

For `lite`, preserve the user's current root model and effort; normal selection replaces the old Luna-only restriction. For `x5` and `x20-work`, installation defaults are Sol xhigh. For `x20`, they are Astra medium. A later manual model/effort selection is authoritative; routing must not switch it back.

For `lite`, `x5`, `x20-work`, merge the two Luna memory model keys. These pin **memory models, not memory reasoning effort**. Internal memory jobs are distinct from task subagents. Do not enable memory collection or change retention/persistence as a side effect. For `x20`, remove only old routing-owned extraction/consolidation overrides and retain Codex/provider defaults and unrelated memory settings.

## 4. Synchronize native roles

Preview first, substituting the chosen profile:

```powershell
python scripts/manage_roles.py install x20 --dry-run
python scripts/manage_roles.py install x20
```

For the first migration from the old repository files, add `--adopt-legacy` to both commands **after reviewing those files**. The helper accepts only known old blob hashes (or line-ending-only CRLF copies), archives their original bytes, and removes stale roles. Edited lookalikes are not adopted. For an explicitly separate home, append `--home "ACTUAL_CODEX_HOME"`.

The helper owns the profile's native workers and three derived compatibility aliases: `default`, `worker`, `explorer`. Aliases use the default worker's same model/effort and instructions, not new specialties. Their files are named `routing-default.toml`, `routing-worker.toml`, `routing-explorer.toml`.

Ownership and SHA-256 hashes are recorded in `routing-rules/roles-state.json` under the selected Codex home. Old owned files are archived under `routing-rules/backups/`. Unmanaged collisions, changed/missing owned files, symlinks/junctions and invalid ownership state stop the operation. Review them manually; do not delete unknown files to bypass the check.

The helper does not edit config or AGENTS, discover every project/plugin role, enforce account spending, or provide crash-atomic multi-file changes. Close Codex and avoid concurrent edits. A normal write failure triggers best-effort rollback; a process/OS failure may require the archived files and installation notes. Stale `roles.lock` must be reviewed, not blindly removed.

## 5. Replace the routing instruction block

In the real global `AGENTS.md`, replace the previous profile's routing/model restrictions with the marked block from the destination `agents-subset.md`:

```text
<!-- codex-routing-rules:begin -->
...destination routing block...
<!-- codex-routing-rules:end -->
```

On first migration, the old block is unmarked: identify it from the old file, remove its routing restrictions and authorization phrases, and preserve all unrelated instructions. Later switches replace exactly one marked block. Check project instructions for contradictory older routing rules; do not silently rewrite unrelated project policy.

The lite file also retains its original Russian communication, Git and workspace instructions **outside** the markers. Merge these only when intended and do not duplicate existing copies. Removal of routing must not remove those unrelated preferences. Do not install the research report or the Astra playbook into AGENTS.md.

## 6. Restart and test a fresh thread

Fully restart the relevant client and begin a **new** thread, not a resumed pre-migration thread. Verify the normal selector, current root and actual child model/effort using native metadata. Follow [verification.md](verification.md). A worker claiming its own model is not evidence.

If a project/config override, unsupported client, missing entitlement or full-history behavior prevents verified pinning, keep that task in the user-selected root without delegation. Record the limitation. Installation is not complete merely because the helper exited successfully.
