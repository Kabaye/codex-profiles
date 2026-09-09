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

Unlike `install PROFILE`, removal does not reset every top-level role file. It removes the roles owned by the active profile manifest. Any unmanaged role created after installation remains outside removal ownership.

## Remove the Codex profile

```powershell
python scripts/manage_profile.py remove
```

This removes repository-owned routing state from the selected Codex home in one lifecycle.

It cleans:

- profile-owned `model` / `model_reasoning_effort` values;
- profile-owned `model_catalog_json` from `lite`;
- profile-owned `[agents]` defaults/caps;
- the empty `[features.multi_agent_v2] multi_agent_mode_hint_text` override;
- `[features.context_management] experimental_mode` installed by the profiles;
- profile-owned memory model selectors;
- the `codex-profiles` marked `AGENTS.md` profile block;
- all managed worker and generated alias role files;
- the `profiles/roles-state.json` ownership manifest after its owned files are verified;
- the repository-specific `models-lite.json` file.

Unrelated settings are preserved. Unmanaged role files created after installation are also preserved by `remove`; note that `install PROFILE` would already have deleted any role files that existed before that installation.

## Modified managed state

A role recorded in `profiles/roles-state.json` must still match its recorded digest. A changed or missing managed role stops removal for review instead of being deleted or reconstructed. Unmanaged files remain outside the removal set.

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

`install PROFILE` is a complete switch: it replaces the current managed profile state with the destination profile while preserving unrelated configuration.

The switch is destructive for roles: it deletes every existing top-level `agents/*.toml` file in the selected Codex home, writes no backup copy, then writes only the destination profile roles.

## Finish

After removal:

1. fully restart Codex;
2. start a new thread;
3. run:

```powershell
python scripts/manage_profile.py status
```

The managed profile should be `null`/absent. Codex's own defaults, normal model catalog, built-in multi-agent mode behavior and remaining user-managed settings then apply.
