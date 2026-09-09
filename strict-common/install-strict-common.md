# Install `strict-common`

Use the shared profile lifecycle. Installing `strict-common` automatically replaces the currently managed profile state; do not manually remove another profile first.

```powershell
python scripts/manage_profile.py install strict-common --dry-run
python scripts/manage_profile.py install strict-common
```

**Destructive role reset:** in the selected Codex home, installation deletes every existing top-level `agents/*.toml` file, including unrelated and custom roles, and writes no backup copy. It then writes only the `strict-common` roles. The scope is non-recursive; nested directories and non-TOML files are not deleted.

Expected profile state:

- default root: GPT-5.6 Sol / xhigh;
- delegated model: GPT-5.6 Luna / max;
- open child cap: 4;
- normal account/provider model catalog;
- empty Multi-Agent V2 mode hint;
- experimental context management enabled.

Unrelated configuration outside this role-file scope is preserved. After installation, the selected home's top-level `agents/*.toml` set must equal exactly the `strict-common` role set.

After installation, fully restart Codex and open a new thread.

See the shared [installation/switching procedure](../docs/install.md) and [verification](../docs/verification.md).
