# Remove `x20`

Complete removal uses the same lifecycle manager as every other profile:

```powershell
python scripts/manage_profile.py remove --dry-run
python scripts/manage_profile.py remove
```

This removes the active repository-owned profile state from the selected Codex home, including config keys, AGENTS routing instructions, managed/known-legacy roles and any repo-specific lite catalog left from an older switch. Unrelated configuration and unrelated role files are preserved.

To switch from `x20` to another profile, do **not** remove first. Run the destination install directly, for example:

```powershell
python scripts/manage_profile.py install x20-work
```

See the shared [removal procedure](../docs/remove.md).
