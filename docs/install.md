# Installation, profile switching, and agent modes

Use `scripts/manage_profile.py` for the complete lifecycle.

## Profiles

Supported profiles:

- `lite`
- `strict-common`
- `private`
- `work`

`private` and `work` support `solo` and `team`. Their default is `solo`. `lite` and `strict-common` keep fixed team routing.

## Preview first

```powershell
python scripts/manage_profile.py install private --dry-run
python scripts/manage_profile.py install private --mode team --dry-run
```

For another Codex home:

```powershell
python scripts/manage_profile.py --home C:\path\to\.codex install work --dry-run
```

Installation deletes every existing top-level `agents/*.toml` file in the selected Codex home. No persistent backup is created.

## Install or switch profile

Default solo:

```powershell
python scripts/manage_profile.py install private
python scripts/manae_profile.py install work
```

Direct team install:

```powershell
python scripts/manage_profile.py install private --mode team
python scripts/manae_profile.py install work --mode team
```

`lite` and `strict-common` do not accept `--mode solo`.

Every install rebuilds `models-managed.json` from the current client's `codex debug models` output. The complete source metadata is preserved except that Luna's `multi_agent_version` is intentionally patched to `v2`. `lite` additionally filters the generated catalog to Terra + Luna.

Offline/testing:

```powershell
python scripts/manage_profile.py install private --models PATH_TO_CAPTURED_MODELS_JSON
```

## Switch only the agent mode

For an already installed `private` or `work` profile:

```powershell
python scripts/manage_profile.py mode team --dry-run
python scripts/manage_profile.py mode team

python scripts/manage_profile.py mode solo
```

A mode switch does not recapture model metadata. It reuses the installed `models-managed.json`.

### Solo contract

Solo removes repository-owned team routing:

- no custom worker TOMLs;
- no `codex-profiles` routing block;
- no profile `[agents]` cap/enable override;
- no profile `multi_agent_mode_hint_text`.

Codex retains its native multi-agent behavior, including explicit user-requested subagents.

### Team contract

For `private` and `work`, team installs:

```text
agents/luna-worker.toml
agents/sol-worker.toml
```

There are no generated `default`, `worker`, or `explorer` aliases.

Team adds:

```toml
[agents]
enabled = true
max_concurrent_threads_per_session = 2

[features.multi_agent_v2]
multi_agent_mode_hint_text = ""
```

The empty hint suppresses the built-in mode message so the installed team `AGENTS.md` policy controls proactive selective delegation.

## Other managed settings

All profiles keep experimental context management enabled. Root defaults and memory-model selectors are profile-owned. The user's manually selected root in a running session remains authoritative; the routing policy never switches it.

An unrelated active `model_catalog_json` is not silently replaced. Installation stops for explicit review unless the path is recognized as a repository-owned current or legacy catalog.

## Restart

After any install or mode switch:

1. fully restart Codex;
2. start a new thread;
1. run:

```powershell
python scripts/manage_profile.py status
python scripts/validate.py
python -m unittest discover -s tests -v
```

A custom model catalog and developer instructions can remain snapshotted by an already running app-server/thread, so old sessions are not valid verification of a new install.
