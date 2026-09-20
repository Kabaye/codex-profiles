# Removal

Preview:

```powershell
python scripts/manage_profile.py remove --dry-run
```

Remove:

```powershell
python scripts/manage_profile.py remove
```

Removal cleans repository-owned state from the selected Codex home:

- profile-owned root model/effort settings;
- repository-owned `model_catalog_json`;
- profile-owned agent settings and child cap;
- profile-owned `multi_agent_mode_hint_text`;
- experimental context-management setting installed by the profile;
- profile-owned memory model selectors;
- the `codex-profiles` `AGENTS.md` block;
- roles recorded in `profiles/roles-state.json`;
- `profiles/roles-state.json`;
- `models-managed.json`;
- historical `models-lite.json`;
- an old `models.json` only when the active catalog reference identifies it as profile-owned;
- historical `routing-rules/` state when safely identified.

A solo manifest can legitimately own zero role files. Removal still clears the profile/config/catalog state.

Unlike `install PROFILE`, removal does not delete arbitrary unmanaged top-level role TOMLs created after installation. It validates the ownership manifest and removes only recorded managed roles.

No persistent backups are created. Rollback bytes exist only in-process during the current operation.

To switch profiles, use `install PROFILE`; do not manually remove first.

After removal, fully restart Codex and open a new thread. `status` should report both `profile` and `mode` as `null`.
