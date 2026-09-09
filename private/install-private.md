# Install `private`

Use the shared profile lifecycle. Installing `private` automatically replaces the currently managed profile state; do not manually remove another profile first.

```powershell
python scripts/manage_profile.py install private --dry-run
python scripts/manage_profile.py install private
```

**Destructive role reset:** in the selected Codex home, installation deletes every existing top-level `agents/*.toml` file, including unrelated and custom roles, and writes no backup copy. It then writes only the `private` roles. The scope is non-recursive; nested directories and non-TOML files are not deleted.

Expected profile state:

- default root: GPT-6 Astra / high;
- delegated model: GPT-5.6 Sol / high only;
- no Astra worker role;
- open child cap: 4;
- normal account/provider model catalog;
- empty Multi-Agent V2 mode hint;
- experimental context management enabled;
- provider/Codex memory defaults retained.

Unrelated configuration outside this role-file scope is preserved. After installation, the selected home's top-level `agents/*.toml` set must equal exactly the `private` role set.

After installation, fully restart Codex and open a new thread.

See the shared [installation/switching procedure](../docs/install.md) and [verification](../docs/verification.md).
