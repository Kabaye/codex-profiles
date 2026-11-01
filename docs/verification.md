# Verification

Run in PowerShell 7:

```powershell
python -X utf8 scripts/validate.py
python -X utf8 -m unittest discover -s tests -v
```

All lifecycle tests use temporary Codex homes and synthetic OpenCode JSON configs. They never read or mutate real global settings. Coverage includes both profiles × both modes, work's split and private's inline layouts, migration from split private with foreign-content preservation, manager block ordering/preservation in either installation order, owned-block hashes, edited-block refusal, removal of empty sidecars, safe instruction-only legacy migration, byte-identical root/config/auth/role preservation during sync, optional named OpenCode merge/removal with unrelated-value preservation and collision refusal, canonical cap migration, destructive full-install role reset, retired profile/catalog cleanup, and rollback.

## Integration smoke test

In a temporary home, install a profile to seed installed profile/mode, run each manager's instruction-only sync in both orders, and confirm:

1. work uses `AGENTS.md`, `WORK.md`, `PRIVATE.md`; private uses only `AGENTS.md`;
2. each active document has one config block followed by one profiles block;
3. changing either manager's block does not invalidate the other manager's ownership hashes;
4. unrelated user prose remains;
5. repeated sync is idempotent;
6. removing either manager leaves the other manager's content intact.

## Live activation smoke test

After full Codex restart and a new chat/thread, confirm `status` shows expected active profile/mode and no changed owned blocks. Inspect only nonsecret settings. In work, verify the home router selects `PRIVATE.md` automatically for a target under `$HOME/Projects/private` and `WORK.md` for a work target. In private, verify the complete personal policy is inline in `AGENTS.md`, independent of target path. In solo, automatic team routes stay inactive and native explicit delegation remains available; `terra-computer.toml` is the one installed specialist role. In team, it joins the Luna and Sol roles. Verify `agents.max_concurrent_threads_per_session = 2` in both work/team and private/team, and that the shared instruction prefers one active worker and allows at most two across native, OpenCode, and Cursor jobs.

In private/team, a substantive implementation uses native Sol and a routine bounded check uses native Luna. In work/team, source lookup uses the named read-only scout with corp-code-fast, current-code explanation uses the scout with corp-chat-max, and implementation uses named work-code with external Luna. Root accepts results, workers never delegate, and no independent review starts without user request.

After explicitly installing the OpenCode fragment and restarting OpenCode, inspect the named agents and effective permissions. A harmless attempted write/shell operation through `work-scout` must be denied; a focused source read/search must succeed, and env-file reads must be denied. Use bounded synthetic tasks to verify tool behavior. Do not induce real quota consumption to test fallback: inspect actual explicit quota errors when encountered, preserving the distinction from authentication/network/validation failures. Exact Cursor model requests must stay on Cursor.

For a live GUI smoke test, enable Browser/Computer Use, verify Codex CLI 0.159.0+ and Terra access, then request a harmless GUI navigation with screenshot verification. Check the subagent actually used `gpt-6.1-terra` with UI tools and never silently fell back to Sol. Validate that each rendered policy contains the shared `shared/agents-subset.md` fragment exactly once; the three profile-specific source files must contain no copies of the shared Terra rule. In work, verify that the personal sidecar uses `work/personal-agents-subset.md` and does not read the separate private profile's routing source.

Static checks establish source/lifecycle correctness. They do not prove service model realization, account entitlement, quota response behavior, or runtime enforcement by future client versions. Report live checks separately from static results.
