# Install lite

`lite` intentionally exposes only **GPT-5.6 Terra** and **GPT-5.6 Luna**. Terra Medium is the default root; every delegated agent is Luna Max. GPT-5.6 Sol and GPT-6/Astra must not remain visible after installation.

Start with the shared [installation and migration procedure](../docs/install.md): make backups, remove/comment an older routing-owned `model_catalog_json` while reading the real model metadata, and check the actual Codex version/account.

## 1. Capture the real model catalog

From the repository root in PowerShell:

```powershell
$codexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $HOME ".codex" }
$tempModels = Join-Path ([System.IO.Path]::GetTempPath()) "codex-models-full.json"
(codex debug models | Out-String) | Set-Content -Path $tempModels -Encoding utf8
```

If your Codex version exposes model metadata differently, use its supported equivalent. Do not invent missing models or reasoning levels.

## 2. Build the restricted catalog

```powershell
$liteCatalog = Join-Path $codexHome "models-lite.json"
python scripts/filter_lite_catalog.py $tempModels $liteCatalog
python scripts/validate.py --profile lite --models $tempModels --lite-catalog $liteCatalog
```

The filter preserves the real Terra/Luna model records exactly and only removes every other model. It refuses to continue unless the source catalog contains `gpt-5.6-terra` with `medium` and `gpt-5.6-luna` with `max`.

## 3. Merge the lite config

Use [config.toml](config.toml) as the merge template. Replace the example `model_catalog_json` path with the actual absolute path printed/used above. On the default Windows home it looks like:

```toml
model = "gpt-5.6-terra"
model_reasoning_effort = "medium"
model_catalog_json = "C:/Users/YOUR_USER/.codex/models-lite.json"
```

Keep the `[agents]` and `[memories]` values from the template. Do not replace unrelated user configuration.

## 4. Install the Luna worker roles

```powershell
python scripts/manage_roles.py install lite --dry-run
python scripts/manage_roles.py install lite
```

For the first migration from an old repository-managed worker set, use `--adopt-legacy` only after reviewing the old files, as described in the shared procedure.

## 5. Update AGENTS.md and restart

Replace only the marked routing block with [agents-subset.md](agents-subset.md), preserving the unrelated Russian communication/Git/workspace rules. Fully restart Codex and open a new thread.

The final selector must show only Terra and Luna. Terra Medium must be the initial root. A delegated smoke test must resolve to Luna Max. If Sol or Astra is still visible, stop and inspect configuration precedence instead of treating the profile as successfully installed.
