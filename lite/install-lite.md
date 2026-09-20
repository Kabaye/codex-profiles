# Install `lite`

Use the shared profile lifecycle. Do not manually stack or merge this profile over another Codex profile.

```powershell
python scripts/manage_profile.py install lite --dry-run
python scripts/manage_profile.py install lite
```

Installation fully replaces the repository-managed routing state for the selected Codex home. It deletes every existing top-level `agents/*.toml` file, writes no persistent backup, and installs only the explicit `luna-worker.toml` role. There are no generated `default`, `worker`, or `explorer` aliases.

The manager also:

- sets Terra Medium as the default root;
- keeps fixed team routing with a one-child cap;
- enables the empty Multi-Agent V2 mode hint and experimental context management;
- captures the current client's `codex debug models` metadata;
- writes `<selected-home>/models-managed.json`, patches Luna to Multi-Agent V2, and filters the model list to Terra + Luna.

For offline/testing use captured metadata:

```powershell
python scripts/manage_profile.py install lite --models PATH_TO_CAPTURED_MODELS_JSON
```

After installation, fully restart Codex and open a new thread. The selector must expose only Terra and Luna, with Terra Medium as the initial root.

See the shared [installation/switching procedure](../docs/install.md) and [verification](../docs/verification.md).
