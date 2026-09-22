# Verification

## Static checks

Run:

```powershell
python scripts/validate.py
python -m unittest discover -s tests -v
```

The tests cover:

- `private/work` defaulting to native `solo`;
- `solo ↔ team` switching without changing the root profile;
- team cap 2;
- explicit Luna Max / Sol High role pins;
- Sol-first delegated implementation in private/personal routing;
- Luna limited to clearly mechanical low-risk personal work;
- bounded scope not treated as sufficient Luna eligibility;
- model reassessment when a Luna assignment materially expands;
- absence of generated `default` / `worker` / `explorer` aliases;
- empty-role solo manifests;
- legacy v1 role-state compatibility;
- destructive top-level role reset on install;
- fail-closed managed-role removal;
- no persistent backup directories;
- `models-managed.json` generation;
- preservation of captured model metadata;
- Luna `multi_agent_version` patch to `v2`;
- `lite` Terra+Luna filtering;
- unrelated custom catalog refusal;
- legacy catalog cleanup;
- in-process rollback.

## Live smoke tests

After a full Codex restart and a new thread:

### Private solo

1. `python scripts/manage_profile.py install private`
2. confirm `status` reports `private / solo`;
3. confirm there are no repository role TOMLs;
4. confirm the effective config has no profile child cap and no profile `multi_agent_mode_hint_text`;
5. ask for a normal task without mentioning agents: repository policy should not proactively delegate;
6. explicitly ask Codex to use a subagent: native explicit-request behavior should remain available.

### Private team

1. `python scripts/manage_profile.py mode team`
2. restart Codex;
3. confirm only `luna_worker` and `sol_worker` are installed;
4. confirm effective child cap is 2;
5. give a clearly mechanical low-risk task with a settled specification and verify Luna Max can be selected;
6. give a bounded but behaviorally substantial implementation (for example workflow/state or cross-component UI behavior) and verify Sol High is selected despite the bounded scope;
7. start a mechanical Luna assignment, materially expand its scope, and verify the root reassesses the model before continuing;
8. verify the root performs integration/final acceptance and no automatic reviewer is spawned.

### Work team

1. install/switch to `work --mode team`;
2. verify an ordinary delegated work task uses Luna Max only;
3. manually selecting Astra as root must not change the delegated work lane;
4. explicitly state `это личная задача`;
5. verify the personal lane is Sol-first for delegated implementation and Luna is used only for clearly mechanical low-risk work;
6. verify a bounded but behaviorally substantial personal task routes to Sol High rather than Luna;
7. verify a Luna personal assignment that materially expands is reassessed before continuing;
8. start an unrelated objective without another personal declaration and verify the lane returns to ordinary Luna-only work.

### Managed catalog

Inspect `models-managed.json` after install:

- all non-lite captured model records remain present;
- Luna retains its captured metadata except `multi_agent_version = "v2"`;
- Luna Max remains in supported reasoning levels;
- `lite` contains exactly Terra and Luna.

Mode switching should leave the managed catalog bytes unchanged. Profile installation should rebuild it from the current client's `codex debug models --bundled` capture.

## Boundaries

Static tests do not prove account entitlement, subscription quota behavior, backend model realization, or that a future Codex client continues to honor the same catalog schema. Runtime metadata remains authoritative. If a pinned model/effort or required spawn control cannot be verified, fail that delegation closed rather than silently substituting another model.
