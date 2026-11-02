# Codex Profiles

Models, native roles and delegation instructions. [codex-config](https://github.com/Kabaye/codex-config) separately owns common rules, account policy and skill installation.

## Files and assembly

```text
manifest.json                   Source lists, order, destinations and role selection
shared/
  config.toml                   Root defaults: Sol 6.1 / xhigh, context management
  AGENTS.md                     Common GUI, reuse and delegation limits
  agents/
    sol-worker.toml             Sol 6.1 / high
    luna-worker.toml            Luna 6 / high
    terra-computer.toml          Terra 6.1 / high
profiles/
  private/AGENTS.md             Private profile metadata
  work/
    AGENTS.md                   Work profile and corporate routing in both modes
    opencode-agents.json         Optional named OpenCode agents
modes/
  solo/
    config.toml                 Native delegation; no mode overrides
    AGENTS.md                   Solo instructions
  team/
    config.toml                 Delegation enabled, two workers, empty native hint
    AGENTS.md                   Sol/Luna routing and assignment instructions
scripts/                        Read the manifest and apply its files
tests/                         Isolated lifecycle checks
```

**Profile** means the computer's environment: `private` or `work`. **Mode** controls only native Codex delegation: `solo` or `team`. Corporate routing belongs to the Work profile and is present in both modes. All three native role definitions are shared across profiles; Solo installs Terra only, Team all three. Role files describe workers; they do not start them.

Open `profiles.private.team` in **manifest.json** to see the complete Private Team recipe. Each recipe declares:

- `config`: TOML files to merge in the listed order into `$CODEX_HOME/config.toml`.
- `instructions`: destination filenames and the ordered Markdown parts for each.
- `roles`: role files to copy into `$CODEX_HOME/agents/`, retaining their filenames.

The scripts read this recipe. Models, effort, mode settings, instruction text and source selection come from files. Historical migration fingerprints and ownership checks remain implementation details.

## Manual Private Team installation

1. Combine `shared/config.toml` and `modes/team/config.toml`. Merge their keys into the existing `$CODEX_HOME/config.toml`, preserving unrelated settings and any root model/effort you selected.
2. Concatenate `profiles/private/AGENTS.md`, `shared/AGENTS.md` and `modes/team/AGENTS.md` in that order. Put the result in the `codex-profiles` block of `$CODEX_HOME/AGENTS.md`, preserving the separate `codex-config` block and user text. The begin/end markers are declared in the manifest.
3. Copy the three declared files from `shared/agents/` to `$CODEX_HOME/agents/`.

These are the same inputs the manager uses. No Python execution is needed to obtain their settings or instructions. When switching to Solo manually, remove the former Team-only keys and Sol/Luna role files; appending empty Solo config does not remove old settings. Restart Codex and use a new chat to load changed role/config definitions.

| Profile | Global `AGENTS.md` |
| --- | --- |
| `private` | Private profile + common rules + selected native mode |
| `work` | Work profile including corporate routing + common rules + selected native mode |

All delegation instructions are assembled into global `AGENTS.md`. The Work router installed by **codex-config** chooses `WORK.md` or `PRIVATE.md` only for account/access policy by project path. This manager adds no delegation blocks to those sidecars; migration removes its former sidecar blocks while preserving other managers and user prose. Every source list is visible in the manifest.

Common instructions prefer reusing workers and one active assignment, with at most two delegated jobs excluding root. Team also sets the native cap to two and an empty native mode hint; its source file supplies routing. Workers have nested delegation disabled. Terra requires actual model and Browser/Computer Use availability.

For work tasks, corporate routing uses OpenCode first with optional bounded scouting in both modes. Explicit Cloud quota exhaustion permits native Codex under its native delegation instructions, then explicit native quota exhaustion permits Cursor. Native Luna uses high in both profiles. Corporate OpenCode model selection is separate from native role definitions.

## Apply and remove

Requires Python 3.11+ and the native Codex model catalog. Run in PowerShell 7 from this checkout:

```powershell
# Explicit install applies shared root defaults; omitted --mode defaults to solo
python -X utf8 scripts/manage_profile.py install private --mode team --dry-run
python -X utf8 scripts/manage_profile.py install private --mode team
# For a work computer: install work --mode team

# Apply sources and select mode, preserving the user-selected root model/effort
python -X utf8 scripts/manage_profile.py mode team --dry-run
python -X utf8 scripts/manage_profile.py mode team
python -X utf8 scripts/manage_profile.py mode solo

# Instructions only: preserves config, role files and role state
python -X utf8 scripts/manage_profile.py sync-instructions --dry-run
python -X utf8 scripts/manage_profile.py sync-instructions
python -X utf8 scripts/manage_profile.py status

python -X utf8 scripts/manage_profile.py remove --dry-run
python -X utf8 scripts/manage_profile.py remove
```

Install and mode changes replace **all top-level `$CODEX_HOME/agents/*.toml` files**, including custom roles; review the dry-run. Instruction-only sync does not update models, role effort or config. Installed profile/mode and ownership hashes live under `$CODEX_HOME/profiles/`.

Optional OpenCode integration: pass `--opencode-config "$HOME/.config/opencode/opencode.json"` to install, mode, sync or remove. The file must already contain valid JSON. Only the named agents declared in the manifest's `opencode_agents` source are managed; providers, secrets and unrelated agents remain. Omitting the option leaves OpenCode untouched.

Modified owned instruction blocks or named OpenCode agents stop writes for review. Removal deletes owned settings and blocks, preserving unrelated content. Runtime writes roll back on failure; no permanent backup is created. Omitting a previously managed OpenCode path during removal retains its ownership record for later explicit removal.

## Validation

```powershell
python -X utf8 scripts/validate.py
python -X utf8 -m unittest discover -s tests -v
```

Tests use temporary homes and synthetic configs, including manual-versus-script assembly checks. Optional model metadata validation: `python -X utf8 scripts/validate.py --profile work --models PATH_TO_MODELS_JSON`. Static checks do not establish model entitlement, quota behavior or actual GUI tools.
