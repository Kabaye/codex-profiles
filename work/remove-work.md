# Remove `work`

Complete removal uses the same lifecycle manager as every other profile:

```powershell
python scripts/manage_profile.py remove --dry-run
python scripts/manage_profile.py remove
```

This removes the active repository-owned profile state from the selected Codex home, including config keys, the `codex-profiles` AGENTS block, manifest-owned roles and any active repo-specific lite catalog. Unrelated configuration and unrelated role files such as `sol-advisor.toml` are preserved.

To switch from `work` to another profile, do **not** remove first. Run the destination install directly, for example:

```powershell
python scripts/manage_profile.py install strict-common
```

See the shared [removal procedure](../docs/remove.md).
