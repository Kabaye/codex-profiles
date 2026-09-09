# Removal and rollback

Use the same lifecycle manager for complete removal that is used for installation and switching.

## Preview removal

Fully close Codex, then run:

```powershell
python scripts/manage_profile.py remove --dry-run
```

For a separate Codex home:

```powershell
python scripts/manage_profile.py --home C:\path\to\.codex remove --dry-run
```

The preview shows the repository-owned files/roles that would change.

## Remove the Codex profile

```powershell
python scripts/manage_profile.py remove
```

This removes repository-owned routing state from the selected Codex home in one lifecycle.

It cleans:

- profile-owned `model` / `model_reasoning_effort` values;
- profile-owned `model_catalog_json` from `lite` or historical repository catalogs;
- profile-owned `[agents]` defaults/caps;
- the empty `[features.multi_agent_v2] multi_agent_mode_hint_text` override;
- `[features.context_management] experimental_mode` installed by the profiles;
- profile-owned memory model selectors;
- the marked `AGENTS.md` profile block;
- exact historical unmarked routing blocks when they can be identified from repository Git history;
- all managed worker/compatibility role files;
- exact known legacy Luna/Sol/Astra worker files;
- the profile ownership manifest, including a valid prior-generation manifest after its owned files are verified;
- the repository-specific `models-lite.json` file.

Unrelated settings and unrelated role files are preserved.

For example, a custom `sol-advisor.toml` remains untouched unless it deliberately collides with a reserved routing role name.

## Modified legacy state

The manager intentionally distinguishes between:

- **exact repository-owned legacy artifacts** — safe to migrate/remove automatically;
- **modified or unknown lookalikes** — stop for review.

If an old unmarked `AGENTS.md` routing section was manually edited, the manager does not guess where user-authored content ends. Reconcile/remove that old section once, then rerun removal.

Likewise, a modified role file with a repository-owned filename is not deleted silently.

If both current and prior-generation ownership manifests exist, removal stops for review. This prevents an ambiguous manifest from claiming or deleting another manifest's files.

## No persistent backups

Removal creates **no backup files or backup directories**.

The process keeps the pre-operation bytes only in memory while it is running and attempts an immediate rollback if a write fails. Nothing is persisted under `profile-backups`, `backups`, or another backup location.

Use `--dry-run` when you want to inspect exactly what will be removed before running the real operation.

## Switching is not remove + install

To change profile, do **not** run a separate manual removal first. Simply run:

```powershell
python scripts/manage_profile.py install private
```

or another destination profile.

`install PROFILE` is a complete switch: it cleans older repository-owned routing state and replaces it with the destination profile while preserving unrelated configuration.

## Finish

After removal:

1. fully restart Codex;
2. start a new thread;
3. run:

```powershell
python scripts/manage_profile.py status
```

The managed profile should be `null`/absent. Codex's own defaults, normal model catalog, built-in multi-agent mode behavior and remaining user-managed settings then apply.
