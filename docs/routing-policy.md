# Routing policy

Common rules and target-path selection belong to `codex-config`; detailed routes below belong to the two `codex-profiles` sidecar blocks. `$HOME/Projects/private` selects private policy automatically. The active root profile controls default root settings; the active agent mode controls whether automatic routes apply. Preserve the user's selected root model and effort in either scope.

## Solo and team

Solo keeps native Codex delegation behavior. Both sidecars remain installed, but their automatic team routes do not apply.

Team delegates useful independent tasks. Give each worker bounded ownership, interfaces, constraints and checks; use `fork_turns = "none"` for native workers. Root owns architecture, integration and final acceptance. Independent review requires an explicit user request. Workers perform their own work and checks without nested delegation.

## Work

| Assignment | Named agent | Explicit model |
|---|---|---|
| File lookup / source discovery, read-only | OpenCode `work-scout` | `litellm/corp-code-fast` |
| Current-code explanations / flow tracing, read-only | OpenCode `work-scout` | `litellm/corp-chat-max` |
| Implementation / debugging / checks | OpenCode `work-code` | `litellm/global.openai.gpt-6-luna` |
| Explicit Cloud quota exhaustion | Native `luna_worker` | GPT-6 Luna / max |
| Explicit native quota exhaustion | Cursor | `auto` unless user selected an exact Cursor model |

Example invocation shapes (replace the quoted assignment with a bounded task):

```powershell
opencode run --agent work-scout --model litellm/corp-code-fast "Locate the assigned source entry points"
opencode run --agent work-scout --model litellm/corp-chat-max "Explain the assigned current-code flow with evidence"
opencode run --agent work-code --model litellm/global.openai.gpt-6-luna "Implement and verify the assigned change"
```

Scout uses deny-by-default tool permissions, read/glob/grep only, env-file read denies, and a 16-step initial bound. Allow 120 seconds per scout question, stop stalled CLI jobs and return partial evidence. Split larger scouting questions. Validate evidence before root acceptance. Authentication, network, context, tool or validation errors do not advance the quota chain. Exact user-chosen Cursor models stay on Cursor. Keep at most three open delegated jobs across CLI/native/Cursor combined, excluding root.

## Private

Use native `sol_worker` (GPT-6.1 Sol / xhigh) for implementation, debugging and complex or uncertain tasks (Sol-first). Use native `luna_worker` (GPT-6 Luna / max) for mechanical edits, exploration and routine checks; move growing complexity to Sol. Do not use OpenCode for these jobs. The native concurrency bound is configured in TOML rather than duplicated in the private instructions.
