# Installation and instruction activation

Use `scripts/manage_profile.py`. For an existing installed profile, prefer the instruction-only operation:

```powershell
python -X utf8 scripts/manage_profile.py --home "$HOME/.codex" sync-instructions --dry-run
python -X utf8 scripts/manage_profile.py --home "$HOME/.codex" sync-instructions
```

It reads installed profile/mode, builds adjacent `AGENTS.md`, `WORK.md`, `PRIVATE.md`, and records only owned block hashes. `config.toml`, roles, role state, MCP and auth files remain byte-identical. Install the corresponding `codex-config` instruction build as well. The home router selects `PRIVATE.md` for targets under `$HOME/Projects/private` automatically; the active root profile does not override target scope.

To install named OpenCode agents, explicitly supply an existing valid JSON config:

```powershell
python -X utf8 scripts/manage_profile.py sync-instructions --opencode-config "$HOME/.config/opencode/opencode.json" --dry-run
python -X utf8 scripts/manage_profile.py sync-instructions --opencode-config "$HOME/.config/opencode/opencode.json"
```

This merges only `work-scout` / `work-code`, retaining all other values. Different unowned names or edited owned definitions stop the operation. Omitting the option never touches OpenCode. There is no provider setup or credential capture in this repository.

For a fresh complete profile installation:

```powershell
python -X utf8 scripts/manage_profile.py install private --dry-run
python -X utf8 scripts/manage_profile.py install private
python -X utf8 scripts/manage_profile.py install work --mode team --dry-run
python -X utf8 scripts/manage_profile.py install work --mode team
```

Both profiles default to solo. **Complete installation and mode switching reset every top-level `agents/*.toml`.** This existing behavior is useful for deliberate profile/role replacement, but use `sync-instructions` for activation that must preserve local roles. An unrelated custom model catalog is refused.

Change mode while preserving root model/effort:

```powershell
python -X utf8 scripts/manage_profile.py mode team --dry-run
python -X utf8 scripts/manage_profile.py mode team
python -X utf8 scripts/manage_profile.py mode solo
```

Team enables native agents, sets `agents.max_concurrent_threads_per_session = 3` (excluding root), and sets `features.multi_agent_v2.multi_agent_mode_hint_text = ""`. A previously owned `agents.max_threads` alias is removed. Solo removes those overrides and custom roles; automatic routes are inactive while native delegation remains available. Both modes install both sidecars and short home metadata. Explicit install applies root defaults; mode and instruction sync preserve user selection.

Fully restart Codex and begin a new chat/thread after any update. Restart OpenCode after merging definitions. Then inspect `status` and run the repository checks documented in [verification](verification.md). Existing chats are not valid evidence of newly installed instructions.
