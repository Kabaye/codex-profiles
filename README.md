# Codex Profiles

Root models, Sol/Luna roles and native delegation instructions. [codex-config](https://github.com/Kabaye/codex-config) owns common rules, account policy, browser/Computer Use policy, Terra and skill installation.

## Files and assembly

```text
manifest.json                   Source lists, order, destinations and role selection
shared/
  config.toml                   Root defaults, context management, 60-second Code Mode wait
  AGENTS.md                     Worker reuse and delegation limits
  agents/
    sol-worker.toml             Sol 6.1 / high
    luna-worker.toml            Luna 6 / high
profiles/
  private/AGENTS.md             Private profile metadata
  work/
    AGENTS.md                   Work profile and corporate routing in both modes
    opencode-agents.json         Optional named OpenCode agents
modes/
  solo/
    config.toml                 Native delegation with 30–60 second agent waits
    AGENTS.md                   Solo instructions
  team/
    config.toml                 Two workers, empty native hint, 30–60 second agent waits
    AGENTS.md                   Sol/Luna routing and assignment instructions
scripts/                        Read the manifest and apply its files
tests/                         Isolated lifecycle checks
```

**Profile** means the computer's environment: `private` or `work`. **Mode** controls native Sol/Luna delegation: `solo` installs neither, `team` installs both. Their role definitions are shared across profiles. Corporate routing belongs to the Work profile and is present in both modes. Terra is installed independently by codex-config in both profiles and remains available in either native mode. Role files describe workers; they do not start them.

Open `profiles.private.team` in **manifest.json** to see the complete Private Team recipe. Each recipe declares:

- `config`: TOML files to merge in the listed order into `$CODEX_HOME/config.toml`.
- `instructions`: destination filenames and the ordered Markdown parts for each.
- `roles`: role files to copy into `$CODEX_HOME/agents/codex-profiles/`, retaining their filenames. The destination directory is declared by `roles_directory`.

The scripts read this recipe. Models, effort, mode settings, instruction text and source selection come from files. Historical migration fingerprints and ownership checks remain implementation details.

## Manual Private Team installation

1. Combine `shared/config.toml` and `modes/team/config.toml`. Merge their keys into the existing `$CODEX_HOME/config.toml`, preserving unrelated settings and any root model/effort you selected.
2. Concatenate `profiles/private/AGENTS.md`, `shared/AGENTS.md` and `modes/team/AGENTS.md` in that order. Put the result in the `codex-profiles` block of `$CODEX_HOME/AGENTS.md`, preserving the separate `codex-config` block and user text. The begin/end markers are declared in the manifest.
3. Copy the two declared Sol/Luna files from `shared/agents/` to `$CODEX_HOME/agents/codex-profiles/`. Terra lives separately in `$CODEX_HOME/agents/codex-config/`.

These are the same inputs the manager uses. No Python execution is needed to obtain their settings or instructions. When switching to Solo manually, remove the former Team-only keys and Sol/Luna role files and apply the Solo wait settings. Restart Codex and use a new chat to load changed role/config definitions.

| Profile | Global `AGENTS.md` |
| --- | --- |
| `private` | Private profile + common rules + selected native mode |
| `work` | Work profile including corporate routing + common rules + selected native mode |

All instructions are assembled into global `AGENTS.md`. **codex-config** includes account/access rules directly, with path conditions for personal projects on work computers. Neither manager installs separate `WORK.md` or `PRIVATE.md` policies. Migration removes former managed sidecar blocks while preserving user prose. Every source list is visible in the manifest.

Both profiles and modes use a 60-second default Code Mode execution wait. Native agent waits default to 60 seconds, with a 30-second minimum; completion or new activity can return earlier. Command polling follows the common 30–60 second blocking-wait rule in **codex-config**. These settings control waiting, not command execution deadlines, and do not enable Code Mode or change Solo/Team selection.

Root owns architecture, implementation, integration and final acceptance. In Team, root handles sequential native work and routine research, data collection, calculations and checks directly. Workers receive complete, substantial, independent deliverables that can progress in parallel with root's own implementation. Sol/Luna selection applies after deciding to delegate. Common instructions prefer reusing workers and one active assignment when delegating, with at most two delegated jobs excluding root. Team also sets the native cap to two and an empty native mode hint; its source file supplies routing. Workers have nested delegation disabled.

Universal browser/Computer Use rules and the Terra role are defined only in codex-config. Each manager owns its named folder under `agents/`; Codex discovers roles recursively. Profile operations preserve the config folder and custom roles.

For work tasks, OpenCode Luna and Cursor Auto Cost are equal primary executors in both modes. Aim for approximately **50/50 by count of new unpinned bounded assignments**, not by tokens, spend or runtime. Alternate the initial route using available task-plan history and record the executor. When there is no history, either route may start; do not always start with OpenCode. An explicit user-selected route takes precedence.

Corrections and technical continuations keep their executor and count as the same assignment. Do not run both executors on the same assignment or split/rerun work just to balance the ratio. The policy uses the available task history; it is not an account-wide scheduling service or a promise of an exact ratio across unrelated chats. Optional Code Fast scouting is separate from implementation-route balancing, and the common limit of two delegated jobs remains in effect.

Automatic Cursor assignments use `--model "auto-smart[optimize_for=cost]"` (Auto Cost), with Max Mode off and `exploreSubagentModel=inherit`; verify Cost before launch and stop/report if unavailable. Cursor no longer needs a quota-exhaustion prerequisite for initial selection. Only explicit quota exhaustion of the selected primary route permits fallback to native Codex under its native delegation instructions; authentication, network, tool, context and validation failures do not. Record quota fallback separately from the initial route. Native Luna uses high in both profiles. Corporate OpenCode model selection is separate from native role definitions.

Invoke the installed `opencode` and `cursor-agent` commands directly by name from PATH, without absolute launcher paths or additional wrappers; the Work profile contains the invocation examples.

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

Install and mode changes update `agents/codex-profiles/` and migrate verified former flat role files. Unrelated roles and the config namespace remain. Instruction-only sync does not update models, role effort or role ownership. Installed profile/mode and ownership hashes live under `$CODEX_HOME/profiles/`.

For an older flat installation, update codex-config first and run `../codex-config/manage.ps1 sync-roles -DryRun`, then `../codex-config/manage.ps1 sync-roles`. This moves Terra into `agents/codex-config/`. Apply the current native mode with `scripts/manage_profile.py mode team` or `mode solo` to move Sol/Luna into `agents/codex-profiles/` and release old Terra ownership. Modified flat files stop migration for review. Both managers coordinate role writes through the same short-lived `.agent-roles.lock`.

Optional OpenCode integration: pass `--opencode-config "$HOME/.config/opencode/opencode.json"` to install, mode, sync or remove. The file must already contain valid JSON. Only the named agents declared in the manifest's `opencode_agents` source are managed; providers, secrets and unrelated agents remain. Omitting the option leaves OpenCode untouched.

Modified owned instruction blocks or named OpenCode agents stop writes for review. Removal deletes owned settings and blocks, preserving unrelated content. Runtime writes roll back on failure; no permanent backup is created. Omitting a previously managed OpenCode path during removal retains its ownership record for later explicit removal.

## Validation

```powershell
python -X utf8 scripts/validate.py
python -X utf8 -m unittest discover -s tests -v
```

Tests use temporary homes and synthetic configs, including manual-versus-script assembly checks. Optional model metadata validation: `python -X utf8 scripts/validate.py --profile work --models PATH_TO_MODELS_JSON`. Static checks do not establish model entitlement, quota behavior or actual GUI tools.
