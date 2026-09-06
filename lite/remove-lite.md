# Remove lite

Follow the shared [removal procedure](../docs/remove.md). Remove only routing-owned settings and the marked routing block; preserve unrelated instructions, credentials, catalogs and memory data.

```powershell
python scripts/manage_roles.py remove
```

The command removes the currently managed role set, not a guessed set based on this page's name. It refuses to remove modified managed files. It does not edit config.toml or AGENTS.md. For a profile change, use the destination profile's install procedure instead of stacking profiles.
