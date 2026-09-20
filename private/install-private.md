# Install `private`

Use the shared profile lifecycle. Installing `private` replaces the currently managed profile state; do not manually remove another profile first.

Default install is native `solo`:

```powershell
python scripts/manage_profile.py install private --dry-run
python scripts/manage_profile.py install private
```

Install directly in selective `team` mode:

```powershell
python scripts/manage_profile.py install private --mode team --dry-run
python scripts/manage_profile.py install private --mode team
```

Expected base state:

- default root: GPT-6 Astra / high;
- root model and effort remain user-selectable at runtime;
- experimental context management enabled;
- `models-managed.json` rebuilt from the current client's model metadata with Luna patched to Multi-Agent V2;
- provider/Codex memory defaults retained.

In `solo`, the repository installs no custom worker TOMLs, no child cap, no proactive routing block, and no `multi_agent_mode_hint_text`; explicit user-requested subagents remain native Codex behavior.

In `team`, the repository installs only `luna-worker.toml` and `sol-worker.toml`, sets the open-child cap to 2, and enables selective routing: Luna Max for cheap/simple/mechanical/well-specified bounded work and Sol High for substantial bounded implementation or non-trivial debugging. The root owns architecture, hard reasoning, integration, verification, and final acceptance. No automatic reviewer is added.

Installation deletes every existing top-level `agents/*.toml` file in the selected Codex home and writes no persistent backup.

After installation, fully restart Codex and open a new thread.

See the shared [installation/switching procedure](../docs/install.md) and [verification](../docs/verification.md).
