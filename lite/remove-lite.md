# Remove lite

Follow the shared [removal procedure](../docs/remove.md). Preserve unrelated instructions, credentials, catalogs and memory data.

Remove the managed worker roles:

```powershell
python scripts/manage_roles.py remove --dry-run
python scripts/manage_roles.py remove
```

In `config.toml`, restore/remove the `lite`-owned values only if they still belong to this profile:

```toml
model = "gpt-5.6-terra"
model_reasoning_effort = "medium"
model_catalog_json = ".../models-lite.json"
```

Also restore/remove the `lite` values in `[agents]` and `[memories]` according to your pre-install backup. Delete only the marked routing block from `AGENTS.md`; keep the unrelated Russian communication/Git/workspace instructions.

After confirming that `model_catalog_json` no longer points to the lite catalog, you may remove the profile-generated `models-lite.json`. Do not delete another custom catalog or a generic `models.json` by name.

Restart Codex and open a new thread. The normal model catalog should return unless another user/project/managed configuration intentionally restricts it.
