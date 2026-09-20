# Install `strict-common`

Use the shared profile lifecycle. Installing `strict-common` automatically replaces the currently managed profile state; do not manually remove another profile first.

```powershell
python scripts/manage_profile.py install strict-common --dry-run
python scripts/manage_profile.py install strict-common
```

Installation deletes every existing top-level `agents/*.toml` file in the selected Codex home, writes no persistent backup, and installs only the explicit Luna Max worker. There are no generated routing aliases.

Expected profile state:

- default root: GPT-5.6 Sol / xhigh;
- delegated model: GPT-5.6 Luna / max;
- fixed team routing with open child cap 4;
- `models-managed.json` generated from the current client's complete model catalog, with Luna patched to Multi-Agent V2;
- empty Multi-Agent V2 mode hint;
- experimental context management enabled.

After installation, fully restart Codex and open a new thread.

See the shared [installation/switching procedure](../docs/install.md) and [verification](../docs/verification.md).
