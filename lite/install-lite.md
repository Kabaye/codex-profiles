# Install `lite`

Use the shared profile lifecycle. Do not manually stack or merge this profile over another Codex profile.

```powershell
python scripts/manage_profile.py install lite --dry-run
python scripts/manage_profile.py install lite
```

The manager automatically:

- removes/replaces older repository-owned profile state;
- installs the full managed `lite` AGENTS block;
- installs Luna Max worker/compatibility roles;
- sets Terra Medium as the default root;
- enables the profile's empty Multi-Agent V2 mode hint and experimental context management;
- runs `codex debug models` and builds `~/.codex/models-lite.json` containing only the real Terra and Luna records.

For offline/testing use captured metadata:

```powershell
python scripts/manage_profile.py install lite --models PATH_TO_CAPTURED_MODELS_JSON
```

After installation, fully restart Codex and open a new thread. The selector must expose only Terra and Luna, with Terra Medium as the initial root.

See the shared [installation/switching procedure](../docs/install.md) and [verification](../docs/verification.md).
