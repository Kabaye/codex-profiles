# Routing policy

Common rules belong to `codex-config`. In work, its target-path router selects the two policy sidecars: `$HOME/Projects/private` uses personal policy and other targets use work policy. Private keeps its personal account policy and native routing inline in `AGENTS.md`, with no path selection. The active root profile controls default root settings; the active agent mode controls whether automatic routes apply. Preserve the user's selected root model and effort in either scope.

## Solo and team

Solo keeps native Codex delegation behavior. Automatic team routes do not apply. The work sidecars remain installed; private keeps its single-file layout.

Team delegates useful independent tasks. Give each worker bounded ownership, interfaces, constraints and checks; use `fork_turns = "none"` for native workers. Root owns architecture, integration and final acceptance. Independent review requires an explicit user request. Workers perform their own work and checks without nested delegation.

## Work

| Assignment | Named agent | Explicit model |
|---|---|---|
| File lookup / source discovery, read-only | OpenCode `work-scout` | `litellm/corp-code-fast` |
| Current-code explanations / flow tracing, read-only | OpenCode `work-scout` | `litellm/corp-chat-max` |
| Implementation / debugging / checks | OpenCode `work-code` | `litellm/global.openai.gpt-6-luna` |
| Explicit Cloud quota exhaustion | Native `luna_worker` | GPT-6 Luna / max |
| Explicit native quota exhaustion | Cursor | `auto-smart[optimize_for=cost]` (Auto Cost); a different model requires an exact user request |

Example invocation shapes (replace the quoted assignment with a bounded task):

```powershell
opencode run --agent work-scout --model litellm/corp-code-fast "Locate the assigned source entry points"
opencode run --agent work-scout --model litellm/corp-chat-max "Explain the assigned current-code flow with evidence"
opencode run --agent work-code --model litellm/global.openai.gpt-6-luna "Implement and verify the assigned change"
agent --print --workspace "REPO_PATH" --model "auto-smart[optimize_for=cost]" --output-format stream-json "BOUNDED_TASK"
```

Automatic Cursor jobs use explicit Auto Cost, with Max Mode off and `exploreSubagentModel=inherit`. Check the local selection is Cost before launching. If that mode is unavailable, stop and report instead of substituting bare `auto`, `default`, Balance/Intelligence or a named model. A different model requires an exact user request. The installed CLI accepted the explicit selector and displayed Auto Cost during an empty interactive launch; no inference prompt was sent. Router modes are described in [Cursor documentation](https://prod.cursor.com/docs/cursor-router).

Scout uses deny-by-default tool permissions, read/glob/grep only, env-file read denies, and a 16-step initial bound. Allow 120 seconds per scout question, stop stalled CLI jobs and return partial evidence. Split larger scouting questions. Validate evidence before root acceptance. Authentication, network, context, tool or validation errors do not advance the quota chain. Exact user-chosen Cursor models stay on Cursor. Keep at most three open delegated jobs across CLI/native/Cursor combined, excluding root.

## Private

Use native `sol_worker` (GPT-6.1 Sol / xhigh) for implementation, debugging and complex or uncertain tasks (Sol-first). Use native `luna_worker` (GPT-6 Luna / max) for mechanical edits, exploration and routine checks; move growing complexity to Sol. Do not use OpenCode for these jobs. The native concurrency bound is configured in TOML rather than duplicated in the private instructions.
