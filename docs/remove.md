# Removal

Preview and remove through `scripts/manage_profile.py`:

```powershell
python -X utf8 scripts/manage_profile.py remove --dry-run
python -X utf8 scripts/manage_profile.py remove
```

Removal validates ownership, clears the `codex-profiles` blocks from `AGENTS.md`, `WORK.md` and `PRIVATE.md`, and deletes only documents that then contain no text. The `codex-config` blocks and all unrelated user prose remain. Changed/missing owned blocks stop removal before any write. Block hashes ignore changes made by the other instruction manager.

Full removal also cleans profile-owned root/config/cap/hint/context/memory/catalog settings, recorded roles, role state, and historical recognized routing artifacts. It does not delete unmanaged roles created after installation. A solo role manifest can own an empty role set. An unowned legacy `agents.max_threads` is refused for explicit review.

If named OpenCode agents were installed, pass the same exact config path to remove their owned definitions:

```powershell
python -X utf8 scripts/manage_profile.py remove --opencode-config "$HOME/.config/opencode/opencode.json" --dry-run
python -X utf8 scripts/manage_profile.py remove --opencode-config "$HOME/.config/opencode/opencode.json"
```

The config must already exist as valid JSON. Only hash-matching `work-scout` / `work-code` definitions are removed. Provider/global settings and other agents retain their values. Without the explicit path, OpenCode is untouched and its ownership record remains in `profiles/instructions-state.json` for later explicit cleanup. Running `remove --opencode-config PATH` again can finish that cleanup after the Codex profile has already been removed.

No persistent backup is created; rollback bytes exist only during the operation. Fully restart Codex and begin a new chat after removal, and restart OpenCode if its definitions changed. `status` reports null active profile/mode once the profile is removed, and separately reports any retained instruction/OpenCode ownership state.
