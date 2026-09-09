# Remove `lite`

Complete removal uses the same lifecycle manager as every other profile:

```powershell
python scripts/manage_profile.py remove --dry-run
python scripts/manage_profile.py remove
```

This removes the active repository-owned profile state, including the full managed `lite` AGENTS block, Luna worker and generated alias roles, profile-owned config keys and the repository-specific `models-lite.json` catalog. Unrelated configuration and unrelated role files are preserved.

To switch from `lite` to another profile, do **not** remove first. Run the destination install directly, for example:

```powershell
python scripts/manage_profile.py install work
```

The switch removes the restricted lite catalog/reference and restores the destination profile's normal catalog policy automatically.

See the shared [removal procedure](../docs/remove.md).
