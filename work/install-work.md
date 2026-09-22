# Install `work`

Use the shared profile lifecycle. Installing `work` replaces the currently managed profile state; do not manually remove another profile first.

Default install is native `solo`:

```powershell
python scripts/manage_profile.py install work --dry-run
python scripts/manage_profile.py install work
```

Install directly in selective `team` mode:

```powershell
python scripts/manage_profile.py install work --mode team --dry-run
python scripts/manage_profile.py install work --mode team
```

Expected base state:

- default root: GPT-5.6 Sol / xhigh;
- Astra or another available root remains manually selectable; routing never changes the selected root;
- experimental context management enabled;
- Luna used for memory extraction/consolidation;
- `models-managed.json` rebuilt from the current client's model metadata with Luna patched to Multi-Agent V2.

In `solo`, the repository installs no custom worker TOMLs, no child cap, no proactive routing block, and no `multi_agent_mode_hint_text`; explicit user-requested subagents remain native Codex behavior.

In `team`, the repository installs only `luna-worker.toml` and `sol-worker.toml` and sets the open-child cap to 2. Ordinary work delegation uses Luna Max only. Sol High becomes available only after the user explicitly marks the current objective as personal, for example `это личная задача`; in that personal lane delegated implementation is Sol-first, while Luna Max is restricted to clearly mechanical, low-risk work with a settled specification. Bounded scope alone does not qualify personal work for Luna, and a Luna assignment that materially expands must be reclassified before continuing. The personal lane applies only to that coherent objective and direct follow-ups. Selecting Astra as root does not activate it.

Installation deletes every existing top-level `agents/*.toml` file in the selected Codex home and writes no persistent backup.

After installation, fully restart Codex and open a new thread.

See the shared [installation/switching procedure](../docs/install.md) and [verification](../docs/verification.md).
