# Install `lite`

Use the shared profile lifecycle. Do not manually stack or merge this profile over another Codex profile.

```powershell
python scripts/manage_profile.py install lite --dry-run
python scripts/manage_profile.py install lite
```

**Destructive role reset:** in the selected Codex home, installation deletes every existing top-level `agents/*.toml` file, including unrelated and custom roles, and writes no backup copy. It then writes only the `lite` roles. The scope is non-recursive; nested directories and non-TOML files are not deleted.

The manager automatically:

- replaces the currently managed profile state;
- installs the full managed `lite` AGENTS block;
- installs Luna Max worker and generated alias roles;
- sets Terra Medium as the default root;
- enables the profile's empty Multi-Agent V2 mode hint and experimental context management;
- runs `codex debug models` and builds `<selected-home>/models-lite.json` containing only the real Terra and Luna records.

After installation, the selected home's top-level `agents/*.toml` set must equal exactly the `lite` role set.

For offline/testing use captured metadata:

```powershell
python scripts/manage_profile.py install lite --models PATH_TO_CAPTURED_MODELS_JSON
```

After installation, fully restart Codex and open a new thread. The selector must expose only Terra and Luna, with Terra Medium as the initial root.

See the shared [installation/switching procedure](../docs/install.md) and [verification](../docs/verification.md).
