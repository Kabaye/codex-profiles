# Install `work`

Use the shared profile lifecycle. Installing `work` automatically replaces the currently managed profile state; do not manually remove another profile first.

```powershell
python scripts/manage_profile.py install work --dry-run
python scripts/manage_profile.py install work
```

**Destructive role reset:** in the selected Codex home, installation deletes every existing top-level `agents/*.toml` file, including unrelated and custom roles, and writes no backup copy. It then writes only the `work` roles. The scope is non-recursive; nested directories and non-TOML files are not deleted.

Expected profile state:

- default root: GPT-5.6 Sol / xhigh;
- Astra remains manually selectable as root;
- delegated model: Luna Max by default;
- after explicit `это личная задача`, substantial delegated work may use Sol High;
- open child cap: 4;
- normal account/provider model catalog;
- empty Multi-Agent V2 mode hint;
- experimental context management enabled.

The personal declaration selects the Sol-vs-Luna delegated path; it is not a second permission gate for whether agents may be spawned at all.

Unrelated configuration outside this role-file scope is preserved. After installation, the selected home's top-level `agents/*.toml` set must equal exactly the `work` role set.

After installation, fully restart Codex and open a new thread.

See the shared [installation/switching procedure](../docs/install.md) and [verification](../docs/verification.md).
