# Remove `lite`

Complete removal uses the same lifecycle manager as every other profile:

```powershell
python scripts/manage_profile.py remove --dry-run
python scripts/manage_profile.py remove
```

This removes the active repository-owned profile state, including the managed `lite` AGENTS block, explicit Luna role, profile-owned config keys, `profiles/roles-state.json`, and `models-managed.json`. Historical `models-lite.json` is also cleaned when present. Unrelated configuration and unmanaged roles created after installation are preserved.

To switch from `lite` to another profile, do **not** remove first. Install the destination directly, for example:

```powershell
python scripts/manage_profile.py install work
```

The destination install performs the profile replacement. Native-catalog profiles remove the lite custom catalog; reinstalling `lite` rebuilds its Luna-only catalog.

See the shared [removal procedure](../docs/remove.md).
