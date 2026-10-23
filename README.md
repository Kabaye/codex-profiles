# Codex profiles

Builds routing instructions and native worker roles for `work` and `private` profiles. The current user-selected root model and effort remain authoritative.

## Instruction build

Runtime instructions are exactly three adjacent documents under `$CODEX_HOME`:

| Document | `codex-config` owns | `codex-profiles` owns |
|---|---|---|
| `AGENTS.md` | Common policy and short path-based router | Short active root profile / agent mode metadata |
| `WORK.md` | Work account policy | Work routing and quota fallback chain |
| `PRIVATE.md` | Personal account policy | Native Sol-first / Luna routing |

Both sidecars are installed for either root profile. The router selects the policy from the target repository path: `$HOME/Projects/private` uses `PRIVATE.md` automatically, including while the active root profile is `work`. No declaration phrase is required. Detailed routing stays out of home `AGENTS.md`.

Each manager replaces only its own marker block. The canonical order is the `codex-config` block followed by the `codex-profiles` block; unrelated user prose remains. Instruction state stores hashes of owned blocks, so another manager's changes do not invalidate ownership. Changed or missing owned blocks stop updates/removal before writes; review those changes explicitly.

## Modes and routing

Both profiles default to `solo`. Sidecars and active metadata exist in either mode.

| Mode | Behavior |
|---|---|
| `solo` | Native Codex delegation; no automatic profile team routing, custom roles, cap or mode-hint override |
| `team` | Automatic useful independent delegation through the selected sidecar; root owns architecture, integration and acceptance; review only on user request |

`private/team` uses native `sol_worker` for implementation, debugging and uncertain work, and native `luna_worker` for mechanical edits, exploration and routine checks. Workers cannot delegate. OpenCode is not used for these jobs.

`work/team` uses named OpenCode primary agents: `work-scout` with `litellm/corp-code-fast` for file lookup or `litellm/corp-chat-max` for current-code explanations, both read-only; `work-code` with `litellm/global.openai.gpt-6-luna` for implementation and checks. Only explicit Cloud quota exhaustion permits native `luna_worker`, then only explicit native quota exhaustion permits Cursor. Automatic Cursor jobs explicitly use `auto-smart[optimize_for=cost]` (Auto Cost), with Max Mode off and exploration inheriting the parent model. If unavailable, stop instead of choosing another model; a different Cursor model requires an exact user request. Network/authentication/validation failures do not advance this chain.

The native team cap is `agents.max_concurrent_threads_per_session = 3`, excluding the root. Work policy also bounds all open delegated CLI/native/Cursor jobs together because the native cap does not cover external processes. The native config key is documented in [official OpenAI documentation](https://learn.chatgpt.com/docs/agent-configuration/subagents#global-settings); `agents.max_threads` is a legacy alias. Full lifecycle commands migrate a previously owned alias; an unowned alias requires explicit review.

## Safe instruction-only activation

For an existing installed profile, use this path to preserve `config.toml`, root model/effort, MCP/auth settings, role files and role-state bytes:

```powershell
python -X utf8 scripts/manage_profile.py --home "$HOME/.codex" sync-instructions --dry-run
python -X utf8 scripts/manage_profile.py --home "$HOME/.codex" sync-instructions
```

The command reads the current installed profile/mode from `profiles/roles-state.json`. It updates only the three instruction documents and `profiles/instructions-state.json`. It can migrate an older managed home routing block. Install the matching instruction build from `codex-config` too so the common router and account policies are present.

Optionally merge the tracked [named OpenCode definitions](work/opencode-agents.json) into an **existing valid JSON** config by passing its exact path:

```powershell
python -X utf8 scripts/manage_profile.py --home "$HOME/.codex" sync-instructions --opencode-config "$HOME/.config/opencode/opencode.json" --dry-run
python -X utf8 scripts/manage_profile.py --home "$HOME/.codex" sync-instructions --opencode-config "$HOME/.config/opencode/opencode.json"
```

Only `agent.work-scout` and `agent.work-code` are owned. Providers, environment references, credentials, global permissions, other agents and model settings retain their values. Existing different definitions at those names are refused rather than overwritten. Scout permissions deny all tools except read/glob/grep, deny env-file reads, and deny writing, shell, task and skill tools. The initial scout has a 16-step budget; split larger investigations into focused questions. `work-code` denies task/skill delegation and inherits other user permissions. No provider or credential data is copied into managed state.

OpenCode is never read or changed when the path is omitted. To remove owned OpenCode agents, pass the same path to `remove`; omitting it retains their ownership record for later explicit cleanup. A changed owned definition requires review. JSONC and creation of an absent config are not supported.

After any update, fully restart Codex and start a new chat/thread; running sessions retain instruction snapshots. Restart OpenCode before using updated named agents. Live service permissions, model realization and quota responses still require runtime verification.

## Complete lifecycle

```powershell
python -X utf8 scripts/manage_profile.py install private --dry-run
python -X utf8 scripts/manage_profile.py install private --mode team
python -X utf8 scripts/manage_profile.py mode solo
python -X utf8 scripts/manage_profile.py mode team
python -X utf8 scripts/manage_profile.py status
python -X utf8 scripts/manage_profile.py remove --dry-run
python -X utf8 scripts/manage_profile.py remove
```

`install`, `mode` and `remove` also maintain the new instruction documents and accept `--opencode-config PATH`. Mode changes preserve the configured root model/effort; explicit installation applies profile defaults (private: GPT-6 Astra xhigh; work: GPT-6.1 Sol xhigh). Both use the native catalog.

Full `install` and `mode` retain the existing role-reset contract: every top-level `agents/*.toml` is deleted before writing the destination set. Team installs `luna-worker.toml` and `sol-worker.toml`; solo installs none. Use `sync-instructions` for instruction updates that must preserve unrelated roles. Removal validates recorded ownership and leaves unmanaged roles and prose intact. No persistent backup is created; rollback bytes exist only in process.

## Validation

No dependencies beyond Python 3.11+ and Git are required. Run checks in PowerShell 7:

```powershell
python -X utf8 scripts/validate.py
python -X utf8 -m unittest discover -s tests -v
```

Tests use temporary Codex homes and synthetic OpenCode configs, never the real global config. Optional native model metadata check:

```powershell
python -X utf8 scripts/validate.py --profile private --models PATH_TO_CAPTURED_MODELS_JSON
```

See [installation](docs/install.md), [routing](docs/routing-policy.md), [verification](docs/verification.md) and [removal](docs/remove.md).
