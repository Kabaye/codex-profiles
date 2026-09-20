# Remove `strict-common`

Complete removal uses the shared lifecycle manager:

```powershell
python scripts/manage_profile.py remove --dry-run
python scripts/manage_profile.py remove
```

This removes repository-owned config keys, the managed `codex-profiles` AGENTS block when present, manifest-owned roles, `profiles/roles-state.json`, and `models-managed.json`. Historical repository-owned catalog/routing artifacts are cleaned when safely identified. Unrelated configuration and unmanaged roles created after installation are preserved.

To switch from `strict-common` to another profile, do **not** remove first. Install the destination directly, for example:

```powershell
python scripts/manage_profile.py install private
```

The destination install performs the complete profile replacement, rebuilds `models-managed.json`, and resets the top-level managed role set without creating a persistent backup.

See the shared [removal procedure](../docs/remove.md).
