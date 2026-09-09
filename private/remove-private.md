# Remove `private`

Complete removal uses the same lifecycle manager as every other profile:

```powershell
python scripts/manage_profile.py remove --dry-run
python scripts/manage_profile.py remove
```

This removes the active repository-owned profile state from the selected Codex home, including config keys, the `codex-profiles` AGENTS block, manifest-owned roles and any active repo-specific lite catalog. Removal preserves unrelated configuration and unmanaged roles created after installation.

To switch from `private` to another profile, do **not** remove first. Run the destination install directly, for example:

```powershell
python scripts/manage_profile.py install work
```

That destination install deletes every existing top-level `agents/*.toml` file in the selected Codex home, including unrelated/custom roles, writes no backup copy, then writes only the destination profile roles.

See the shared [removal procedure](../docs/remove.md).
