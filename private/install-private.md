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

- default root: GPT-6 Astra / xhigh;
- root model and effort remain user-selectable at runtime;
- experimental context management enabled;
- native Codex model catalog; GPT-6 Sol/Luna are used without a compatibility override;
- provider/Codex memory defaults retained.

In `solo`, the repository installs no custom worker TOMLs, no child cap, no proactive routing block, and no `multi_agent_mode_hint_text`; explicit user-requested subagents remain native Codex behavior.

In `team`, the repository installs only `luna-worker.toml` and `sol-worker.toml`, sets the open-child cap to 2, and enables selective routing. Delegated implementation is Sol-first: GPT-6 Sol xhigh handles substantial implementation, debugging, workflow/state changes, business or financial logic, contracts, migrations, cross-component behavior, adaptive UI work, and uncertain complexity. GPT-6 Luna Max is only for clearly mechanical, low-risk work with a settled specification and no meaningful behavioral semantics; bounded scope alone is not sufficient. If Luna work materially expands, the root must reassess and move the remaining work to Sol or back to the root. The root owns architecture, hard reasoning, integration, verification, and final acceptance. No automatic reviewer is added.

Installation deletes every existing top-level `agents/*.toml` file in the selected Codex home and writes no persistent backup.

After installation, fully restart Codex and open a new thread.

See the shared [installation/switching procedure](../docs/install.md) and [verification](../docs/verification.md).
