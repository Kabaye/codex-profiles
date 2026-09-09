# Install `work`

Use the shared profile lifecycle. Installing `work` automatically replaces older repository-owned profile state; do not manually remove another profile first.

```powershell
python scripts/manage_profile.py install work --dry-run
python scripts/manage_profile.py install work
```

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

Unrelated config and unrelated native roles such as `sol-advisor.toml` are preserved. Exact repository legacy artifacts are cleaned automatically; modified collisions stop for review.

After installation, fully restart Codex and open a new thread.

See the shared [installation/switching procedure](../docs/install.md) and [verification](../docs/verification.md).
