# Verification

Run in PowerShell 7:

```powershell
python -X utf8 scripts/validate.py
python -X utf8 -m unittest discover -s tests -v
```

All lifecycle tests use temporary Codex homes and synthetic OpenCode JSON configs. They never read or mutate real global settings. Coverage includes both profiles × both modes, three-document builds, manager block ordering/preservation in either installation order, owned-block hashes, edited-block refusal, removal of empty sidecars, safe instruction-only legacy migration, byte-identical root/config/auth/role preservation during sync, optional named OpenCode merge/removal with unrelated-value preservation and collision refusal, canonical cap migration, destructive full-install role reset, retired profile/catalog cleanup, and rollback.

## Integration smoke test

In a temporary home, install a profile to seed installed profile/mode, run each manager's instruction-only sync in both orders, and confirm:

1. exactly `AGENTS.md`, `WORK.md`, `PRIVATE.md` are runtime Markdown instructions;
2. each document has one config block followed by one profiles block;
3. changing either manager's block does not invalidate the other manager's ownership hashes;
4. unrelated user prose remains;
5. repeated sync is idempotent;
6. removing either manager leaves the other manager's content intact.

## Live activation smoke test

After full Codex restart and a new chat/thread, confirm `status` shows expected active profile/mode and no changed owned blocks. Inspect only nonsecret settings. Verify the home router selects `PRIVATE.md` automatically for a target under `$HOME/Projects/private`, even with active `work` root profile, and selects `WORK.md` for a work target. In solo, automatic team routes stay inactive and native explicit delegation remains available.

In private/team, a substantive implementation uses native Sol and a routine bounded check uses native Luna. In work/team, source lookup uses the named read-only scout with corp-code-fast, current-code explanation uses the scout with corp-chat-max, and implementation uses named work-code with external Luna. Root accepts results, workers never delegate, and no independent review starts without user request.

After explicitly installing the OpenCode fragment and restarting OpenCode, inspect the named agents and effective permissions. A harmless attempted write/shell operation through `work-scout` must be denied; a focused source read/search must succeed, and env-file reads must be denied. Use bounded synthetic tasks to verify tool behavior. Do not induce real quota consumption to test fallback: inspect actual explicit quota errors when encountered, preserving the distinction from authentication/network/validation failures. Exact Cursor model requests must stay on Cursor.

Static checks establish source/lifecycle correctness. They do not prove service model realization, account entitlement, quota response behavior, or runtime enforcement by future client versions. Report live checks separately from static results.
