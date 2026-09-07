# Installation and migration

Install one profile at a time. This procedure targets the reviewed **Codex 0.153.4** behavior. The supplied `config.toml` files are merge fragments, never replacements for the user's whole config. See [technical evidence](research-2026-09-06.md) and [smoke tests](verification.md).

## 1. Identify and preserve the real setup

Close active Codex threads before changing role files. Run `codex --version` and `python --version`; the helpers require Python 3.11+. Do not automatically install software or update a managed work client.

Resolve the actual Codex home: explicit `--home`, otherwise `CODEX_HOME`, otherwise the documented `~/.codex` default. Desktop/CLI/IDE environments can differ, so check the one you are actually changing.

Make private, timestamped backups of the existing `config.toml`, `AGENTS.md` and affected role files. Record the original values of every key to be changed. Do not copy credentials, auth files, session history or entire databases. Do not commit these backups.

Inspect active configuration layers, selected profiles, project `.codex/config.toml`, project agent files and any managed/plugin overrides. Do not remove organizational restrictions, permissions, sandbox policy or unrelated settings merely to make a preset work.

## 2. Validate real model metadata

If `model_catalog_json` currently points to a catalog created by an older version of this repository, back up the line and temporarily remove/comment it before running the model inspection. Do not clear an administrator's or unrelated custom catalog without understanding why it exists.

Capture the actual model metadata from the installed account/client. When supported:

```powershell
(codex debug models | Out-String) | Set-Content -Path PATH_TO_CAPTURED_MODELS_JSON -Encoding utf8
python scripts/validate.py --profile x20 --models PATH_TO_CAPTURED_MODELS_JSON
```

Replace `x20` with the destination profile. The validator checks only the models/efforts required by that profile. An unrecognized metadata format is a stop; do not invent entries or rewrite capabilities to make validation pass.

## 3. Catalog policy differs by profile

### lite

`lite` intentionally uses a **restricted catalog** containing only:

- `gpt-5.6-terra` — default root at `medium`;
- `gpt-5.6-luna` — only delegated model, pinned to `max`.

Follow [lite/install-lite.md](../lite/install-lite.md) to generate `models-lite.json` from the **real** captured catalog using `scripts/filter_lite_catalog.py`. The filter preserves the original Terra/Luna records and removes every other model. GPT-5.6 Sol and GPT-6/Astra must not remain visible after restart.

### x5, x20, x20-work

These profiles use the normal account/provider model catalog. Remove only a routing-owned `model_catalog_json` left by another profile. Preserve unrelated or managed catalogs and resolve conflicts explicitly.

## 4. Merge the destination config

Merge `PROFILE/config.toml` into the existing file, updating keys in their existing tables. Do not append duplicate `[agents]` or `[memories]` tables. Place root-level model settings before table headers.

Remove only obsolete settings introduced by an older routing profile, such as its routing-owned catalog line, legacy `features.multi_agent` / `features.multi_agent_v2` fields, or conflicting old agent defaults. Preserve unrelated feature settings.

The child-thread cap is **1 for lite and 4 for x5/x20/x20-work**, counting open children and excluding the root. Four is a ceiling; normal routing should use zero to two children and reserve the third/fourth for genuinely independent work.

Root defaults:

| Profile | Default root |
|---|---|
| lite | `gpt-5.6-terra` / `medium` |
| x5 | `gpt-5.6-sol` / `xhigh` |
| x20 | `gpt-6-astra` / `high` |
| x20-work | `gpt-5.6-sol` / `xhigh` |

For `lite`, the `model_catalog_json` path must point to the generated `models-lite.json`. For the other profiles, no routing-owned custom catalog is used.

For `lite`, `x5`, and `x20-work`, merge the two Luna memory-model keys from the profile template. These select memory models, not a memory reasoning effort. For `x20`, retain Codex/provider memory defaults and remove only old routing-owned extraction/consolidation overrides.

## 5. Synchronize native roles

Preview first, substituting the chosen profile:

```powershell
python scripts/manage_roles.py install x20 --dry-run
python scripts/manage_roles.py install x20
```

For the first migration from old repository-managed role files, add `--adopt-legacy` only after reviewing those files. Use `--home` for an explicitly separate Codex home.

The helper owns the profile's native workers and three compatibility aliases: `default`, `worker`, `explorer`. Aliases use the profile's default worker model/effort. Unknown collisions, modified/missing owned files, unsafe paths and stale locks stop the operation for review.

The helper manages roles only. It does not edit `config.toml`, `AGENTS.md`, model catalogs, credentials or memory data.

## 6. Replace the routing instruction block

In the real global `AGENTS.md`, replace the previous routing block with the marked block from the destination `agents-subset.md`:

```text
<!-- codex-routing-rules:begin -->
...destination routing block...
<!-- codex-routing-rules:end -->
```

Preserve unrelated instructions. The lite file also contains its Russian communication, Git and workspace rules outside these markers; keep or merge them intentionally instead of deleting them with the routing block.

## 7. Restart and test a fresh thread

Fully restart the relevant client and begin a **new** thread. Verify the selector, current root and actual child model/effort using native metadata rather than a worker's self-description. Follow [verification.md](verification.md).

For `lite`, the selector must show **only Terra and Luna**, with Terra Medium as the initial root. For the other profiles, the normal catalog should remain available unless another legitimate configuration restricts it.

If effective configuration, account entitlement or client behavior prevents the required routing from being verified, do not silently substitute another model. Treat installation as incomplete and report the mismatch.
