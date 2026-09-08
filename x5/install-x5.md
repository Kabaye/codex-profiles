# Install `x5`

Use the shared profile lifecycle. Installing `x5` automatically replaces older repository-owned routing state; do not manually remove another profile first.

```powershell
python scripts/manage_profile.py install x5 --dry-run
python scripts/manage_profile.py install x5
```

Expected profile state:

- default root: GPT-5.6 Sol / xhigh;
- delegated model: GPT-5.6 Luna / max;
- open child cap: 4;
- normal account/provider model catalog;
- empty Multi-Agent V2 mode hint;
- experimental context management enabled.

Unrelated config and unrelated native roles are preserved. Exact repository legacy artifacts are cleaned automatically; modified collisions stop for review.

After installation, fully restart Codex and open a new thread.

See the shared [installation/switching procedure](../docs/install.md) and [verification](../docs/verification.md).
