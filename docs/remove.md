# Removal and rollback

For a **profile switch**, follow the destination [installation procedure](install.md): it synchronizes owned roles, defaults, memory keys and the single routing block. Do not stack profiles or run four unrelated removal scripts.

For complete removal, close active Codex sessions, inspect the installation notes/backups and preview:

```powershell
python scripts/manage_roles.py remove --dry-run
python scripts/manage_roles.py remove
```

Use `--home` for a separate home, or let the helper honor `CODEX_HOME`. It removes only the files owned by the current role manifest and only when their hashes still match. Modified/missing roles or unmanaged collisions require manual review. Unrelated native roles remain. Backups remain; legacy roles are **not** silently resurrected.

Delete only the marked routing block in global `AGENTS.md`. Preserve all unrelated instructions, including the lite Russian/Git/workspace preface. If removing an old, unmarked installation directly, use its original file and your backup to identify the exact routing paragraphs first.

Review these keys against the recorded pre-install state:

| Location | Routing-owned keys to restore/remove when still owned |
|---|---|
| Top level | `model`, `model_reasoning_effort` when the profile set them; lite sets neither |
| `[agents]` | `enabled`, `max_concurrent_threads_per_session`, `default_subagent_model`, `default_subagent_reasoning_effort` |
| `[memories]` | `extract_model`, `consolidation_model` when the profile set them |

Do not overwrite later user edits. Restore a previous value only when it is the intended non-routing baseline; otherwise remove the still-owned override. If your backup is itself an old routing installation, blindly restoring it reinstates that old profile rather than uninstalling routing. Treat that as an explicit rollback choice, not the default removal action.

The migration removed old routing-owned feature/catalog overrides. Full rollback may restore those from the reviewed backup, but ordinary uninstall should not reactivate a restrictive legacy catalog. Never delete arbitrary `models.json`, auth, Skills, memory data, session storage or project configuration. Empty table headers may be removed after their owned keys are removed.

Restart Codex and open a new thread. Check that no obsolete routing instructions, worker registrations or project overrides remain. Without this preset, Codex's own defaults apply; the old Luna-only child policy is no longer promised.
