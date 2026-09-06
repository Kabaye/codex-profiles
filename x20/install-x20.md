# Install x20

Follow the shared [installation and migration procedure](../docs/install.md) with profile `x20`. It covers backups, model metadata validation, role cleanup, config merging and live smoke tests. Do not install by copying only AGENTS.md.

Profile inputs: [config.toml](config.toml), [routing instructions](agents-subset.md), [worker files](agents).

Role installation, after the preflight:

```powershell
python scripts/manage_roles.py install x20
```

This command manages role files only; complete the shared config/AGENTS steps and restart Codex. It respects `CODEX_HOME`; use `--home` for an explicitly selected separate Codex home.
