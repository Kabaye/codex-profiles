# Removal and rollback

For a **profile switch**, follow the destination [installation procedure](install.md): it synchronizes roles, defaults, catalog policy, memory keys, experimental context management and the single routing block. Do not stack profiles.

For complete removal, close active Codex sessions, inspect the installation notes/backups and preview:

```powershell
python scripts/manage_roles.py remove --dry-run
python scripts/manage_roles.py remove
```

Use `--home` for a separate home, or let the helper honor `CODEX_HOME`. It removes only the role files owned by the current manifest and only when their hashes still match. Unrelated native roles and backups remain.

Delete only the marked routing block in global `AGENTS.md`. Preserve all unrelated instructions, including the lite Russian/Git/workspace preface.

Review these keys against the recorded pre-install state:

| Location | Routing-owned keys to restore/remove when still owned |
|---|---|
| Top level | `model`, `model_reasoning_effort`; for lite also `model_catalog_json` |
| `[agents]` | `enabled`, `max_concurrent_threads_per_session`, `default_subagent_model`, `default_subagent_reasoning_effort` |
| `[features.context_management]` | `experimental_mode` |
| `[memories]` | `extract_model`, `consolidation_model` when the profile set them |

All four profiles currently set `features.context_management.experimental_mode = true`. Profile switches keep it enabled because every destination profile requires it. On complete removal, restore the pre-install value or remove the still-owned setting if there was no prior value. Preserve unrelated feature keys.

Do not overwrite later user edits. Restore a previous value only when it is the intended non-routing baseline; otherwise remove the still-owned override.

## Extra lite cleanup

`lite` creates a restricted `models-lite.json` containing only Terra and Luna. After confirming that `config.toml` no longer points to it, that **specific profile-generated file** may be removed. Do not delete an unrelated custom catalog or generic `models.json` merely because it exists.

Switching away from `lite` should also remove its routing-owned `model_catalog_json` so the destination profile can use the normal account/provider catalog.

Restart Codex and open a new thread. After complete removal, Codex's own model catalog/defaults and any remaining user-managed feature settings apply unless another configuration intentionally restricts them.
