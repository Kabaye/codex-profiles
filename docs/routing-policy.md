# Routing policy

The repository separates **root selection** from **agent mode**.

## Matrix

| Profile | Root default | Mode | Delegation |
|---|---|---|---|
| `lite` | Terra medium | fixed team | GPT-6 Luna Max, cap 1 |
| `strict-common` | GPT-6 Sol xhigh | fixed team | GPT-6 GPT-6 Luna Max, cap 4 |
| `private` | Astra xhigh | solo default | native Codex; team: GPT-6 GPT-6 Luna Max + GPT-6 Sol xhigh, cap 2 |
| `work` | GPT-6 Sol xhigh | solo default | native Codex; team: GPT-6 GPT-6 Luna Max, plus GPT-6 Sol xhigh only in explicit personal lane, cap 2 |

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

- delegated implementation is Sol-first;
- `sol_worker` = GPT-6 Sol / xhigh for substantial implementation, non-trivial debugging, workflow/state changes, business or financial logic, API/contracts, migrations, cross-component behavior, adaptive UI behavior, or uncertain complexity;
- `luna_worker` = GPT-6 Luna / **max** only for clearly mechanical, low-risk work with a settled specification and no meaningful business logic, workflow/state semantics, contracts, migrations, or cross-component behavior;
- bounded scope or a small file count does not by itself qualify work for Luna; when uncertain, use Sol or keep the work in the root;
- if Luna work materially expands in complexity or risk, reassess before continuing; owner reuse never overrides model suitability.
- root = architecture, material ambiguity, hard reasoning, integration, verification, and final acceptance.

### Work team

For ordinary work objectives, only GPT-6 Luna Max is a delegated path.

The GPT-6 Sol xhigh path is enabled only after an explicit statement that the current objective is personal, such as `это личная задача`. Do not infer that state from repository, path, task difficulty, content, or selected root model. The declaration applies to the current coherent objective and direct follow-ups; a new unrelated objective returns to the ordinary Luna-only work lane.

In that explicit personal lane:

- delegated implementation is Sol-first;
- GPT-6 Sol xhigh handles substantial implementation, non-trivial debugging, workflow/state changes, business or financial logic, API/contracts, migrations, cross-component behavior, adaptive UI behavior, and uncertain complexity;
- GPT-6 Luna Max is limited to clearly mechanical, low-risk work with a settled specification and no meaningful business logic, workflow/state semantics, contracts, migrations, or cross-component behavior;
- bounded scope alone never makes a task a Luna task;
- when a Luna assignment materially expands, reassess the model before continuing; owner reuse never overrides model suitability.

## Catalog policy

`private`, `work`, and `strict-common` use the native Codex model catalog. GPT-6 Sol and GPT-6 Luna are natively Multi-Agent V2, so no compatibility catalog override is installed for these profiles.

`lite` alone uses `models-managed.json`, regenerated from `codex debug models --bundled`. It filters the catalog to GPT-5.6 Terra + GPT-5.6 Luna and retains the legacy Luna V2 compatibility override. A private/work mode switch does not involve model-catalog state.

## Verification ownership

Workers verify their own bounded implementation as needed, but final acceptance stays with the root. Do not spawn a separate reviewer automatically. Independent review is used only when the user explicitly requests it.
