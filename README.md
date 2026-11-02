# Codex Profiles

Configures Codex root models, native agent roles and task routing for the **work** and **private** installations. The independent [codex-config](https://github.com/Kabaye/codex-config) manager owns shared instructions, account policy and skill installation; this repository owns only its own `codex-profiles` blocks and role/config keys.

## Runtime layout

| Installation | Instructions written under `$CODEX_HOME` | Default root |
| --- | --- | --- |
| `work` | `AGENTS.md`, `WORK.md`, `PRIVATE.md` | GPT-6.1 Sol / xhigh |
| `private` | One global `AGENTS.md` | GPT-6.1 Sol / xhigh |

On a work computer, `WORK.md` routes corporate tasks and `PRIVATE.md` routes personal tasks. Their routing sources are `work/agents-subset.md` and **`work/personal-agents-subset.md`**, respectively; the latter is independent of `private/agents-subset.md` used by the separate private installation. `scripts/manage_instructions.py` assembles the single shared GUI/budget fragment from `shared/agents-subset.md` into the applicable policy exactly once.

Root model/effort selected by the user remain authoritative. Running `mode` or `sync-instructions` preserves them; an explicit fresh `install` applies the profile defaults.

## Agent selection

| Mode | Installed native roles | Behavior |
| --- | --- | --- |
| `solo` (default) | `terra_computer` only | Native delegation; no automatic team routing |
| `team` | `terra_computer`, `luna_worker`, `sol_worker` | Delegate useful independent work using the selected policy |

**Prefer one active worker; allow up to two only when parallel work is worthwhile.** In `team`, the native cap is `agents.max_concurrent_threads_per_session = 2` excluding root. The shared instructions also cap the combined native/OpenCode/Cursor delegated jobs at two.

`terra_computer` uses `gpt-6.1-terra` / medium for live GUI work: screenshots, clicking, typing and scrolling. It is not a substitute for coding or normal web research. It requires a compatible Codex CLI, model entitlement and usable Browser/Computer Use tools; the configuration alone cannot supply tools or guarantee a model launch.

In `private/team`, Sol handles implementation and complex/debugging work; Luna uses GPT-6 Luna / medium for bounded mechanical work and checks. In `work/team`, OpenCode `work-code` with `litellm/global.openai.gpt-6-luna` handles bounded implementation, debugging and checks by default; the native Luna fallback remains at max for full work tasks. Optional read-only `work-scout` with `litellm/corp-code-fast` answers one unresolved path/symbol or local-fact question, within 16 steps and 120 seconds. Root verifies source claims and handles deeper flow/contract analysis, architecture and acceptance without automatically adding another corporate model. Scout evidence separates observations, inference, unread scope and unknowns; a missing result within a read range does not prove global absence. Reuse verified findings with their scope and provenance; read-only scouting does not establish implementation ability or lower total cost.

Each assignment defines owned paths, interfaces, acceptance criteria, permitted checks, a finite budget and a stop boundary. Budget scouting, implementation, retries, coordination and review together. Workers return changed paths, actual checks, remaining defects and session evidence or a partial result; root reviews source before assigning corrections. Workers cannot delegate, expand their assignment or silently renew budgets. Honor verification/access limits; never copy denied files to bypass access. Read current source before patching; a context mismatch permits one narrow reread and repair, then return partial evidence if it recurs.

Only explicit Cloud quota exhaustion permits fallback to native `luna_worker`, then only explicit native quota exhaustion permits Cursor. Authentication, network, context, tool or validation failures stop the failing route with evidence; do not change models, providers, SDK settings or permissions to hide them. Automatic Cursor jobs require `auto-smart[optimize_for=cost]` (Auto Cost), Max Mode off and `exploreSubagentModel=inherit`. Verify Cost before launch; if unavailable, stop and report. A different Cursor model requires an exact user request and stays on Cursor.

For stalled CLI jobs, inspect session terminal state and running tools; a live PID alone does not prove inference. Preserve evidence before stopping a finished job whose CLI will not drain, and identify its process by retained handle or PID, creation time, executable and workspace. Do not overlap jobs owning the same assignment. Distinguish model/transport latency, tool time, retries, review, queues and terminal drain when timestamps support it; leave unknown intervals unknown. Source review, a terminal answer and exit code zero do not prove runtime/test success; root checks the complete acceptance contract.

## Install, update, remove

Requires Python 3.11+ and the native Codex model catalog. Run in PowerShell 7 from the checkout:

```powershell
# Fresh installation; full install replaces all top-level agents/*.toml files
python -X utf8 scripts/manage_profile.py install work --dry-run
python -X utf8 scripts/manage_profile.py install work --mode team
# Or: install private / install private --mode team

# Switch team/solo, keeping the user-selected root model/effort
python -X utf8 scripts/manage_profile.py mode team --dry-run
python -X utf8 scripts/manage_profile.py mode team
python -X utf8 scripts/manage_profile.py mode solo
python -X utf8 scripts/manage_profile.py status

# Instructions only: leaves config.toml, role TOMLs, auth, MCP and root model intact
python -X utf8 scripts/manage_profile.py sync-instructions --dry-run
python -X utf8 scripts/manage_profile.py sync-instructions

# Uninstall only manager-owned settings and blocks
python -X utf8 scripts/manage_profile.py remove --dry-run
python -X utf8 scripts/manage_profile.py remove
```

The instruction-only sync **does not install new role TOMLs or change the native concurrency cap**. To activate a new role or cap, use a reviewed `mode` operation after a dry-run. Profile installation and mode changes deliberately replace the top-level role TOMLs; unrelated config and authorization data are preserved only as documented by the manager.

Optional OpenCode integration: pass `--opencode-config "$HOME/.config/opencode/opencode.json"` to the relevant install/sync/remove command. The file must already exist as valid JSON. Only the named `work-scout` and `work-code` definitions are managed; providers, secrets and unrelated agents remain intact. Omitting the option never edits OpenCode.

Managed instruction edits are hash-checked; unknown or modified blocks stop unsafe writes. Removal keeps `codex-config` blocks, unrelated user prose and unowned resources. A profile removed without its previously registered OpenCode path retains an ownership record for later explicit removal. Runtime rollback is transactional but no permanent backup is created.

After an update, **fully restart Codex and start a new chat**. Restart OpenCode if its named-agent definitions changed. Verify the actual effective model, GUI tool availability and permissions rather than assuming a TOML file proves runtime access.

## Validation

```powershell
python -X utf8 scripts/validate.py
python -X utf8 -m unittest discover -s tests -v
```

Tests use temporary homes and synthetic OpenCode configs; they do not edit your installed Codex. Optional model metadata validation: `python -X utf8 scripts/validate.py --profile work --models PATH_TO_MODELS_JSON`. Static checks cannot prove entitlement, actual quota behavior or that a child agent received GUI tools.
