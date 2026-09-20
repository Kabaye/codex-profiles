# Routing policy

The repository separates **root selection** from **agent mode**.

## Matrix

| Profile | Root default | Mode | Delegation |
|---|---|---|---|
| `lite` | Terra medium | fixed team | Luna Max, cap 1 |
| `strict-common` | Sol xhigh | fixed team | Luna Max, cap 4 |
| `private` | Astra high | solo default | native Codex; team: Luna Max + Sol High, cap 2 |
| `work` | Sol xhigh | solo default | native Codex; team: Luna Max, plus Sol High only in explicit personal lane, cap 2 |

The user-selected root and effort are authoritative. In particular, `work` does not restrict the normal root selector; manually selecting Astra changes only the root.

## Solo

`private/work solo` installs no custom roles and no proactive routing block. It also installs no profile multi-agent hint or child cap. Subagents remain available through native Codex behavior when the user directly requests them.

## Team

Team is selective, not maximal:

- root-first by default;
- normally zero or one worker;
- maximum two open child threads per root session for `private/work`;
- delegated work substitutes for root work instead of duplicating it;
- every spawn explicitly names a role and uses `fork_turns = "none"`;
- no generated routing aliases;
- no automatic reviewer.

### Private team

- `luna_worker` = GPT-5.6 Luna / **max** for simple, mechanical, well-specified, exploration, tool-heavy, test/build/log, and other cheap bounded work.
- `sol_worker` = GPT-5.6 Sol / high for substantial bounded implementation, non-trivial debugging, or work where Luna is a poor fit.
- root = architecture, material ambiguity, hard reasoning, integration, verification, and final acceptance.

### Work team

For ordinary work objectives, only Luna Max is a delegated path.

The Sol High path is enabled only after an explicit statement that the current objective is personal, such as `это личная задача`. Do not infer that state from repository, path, task difficulty, content, or selected root model. The declaration applies to the current coherent objective and direct follow-ups; a new unrelated objective returns to the ordinary Luna-only work lane.

In that explicit personal lane:

- Luna Max handles simple/mechanical/well-specified bounded work.
- Sol High handles substantial implementation and non-trivial debugging.

## Catalog policy

All profiles use `models-managed.json`, regenerated from `codex debug models --bundled` on profile install.

The source catalog is preserved except for the intentional Luna override:

```json
"multi_agent_version": "v2"
```

For `lite`, the generated model list is then filtered to Terra + Luna. Luna delegated effort is always Max.

A mode switch reuses the existing managed catalog; it does not rebuild it.

## Verification ownership

Workers verify their own bounded implementation as needed, but final acceptance stays with the root. Do not spawn a separate reviewer automatically. Independent review is used only when the user explicitly requests it.
