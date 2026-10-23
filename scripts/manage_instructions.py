"""Owned instruction blocks and optional named OpenCode agents; no runtime launcher."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import tempfile

import manage_roles

ROOT = Path(__file__).resolve().parents[1]
BEGIN = "<!-- codex-profiles:begin -->"
END = "<!-- codex-profiles:end -->"
CONFIG_BEGIN = "<!-- codex-config:begin -->"
CONFIG_END = "<!-- codex-config:end -->"
DOCS = ("AGENTS.md", "WORK.md", "PRIVATE.md")
STATE = "instructions-state.json"
AGENT_NAMES = {"work-scout", "work-code"}


def normalize(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def digest(value: str | dict) -> str:
    data = normalize(value).encode() if isinstance(value, str) else json.dumps(
        value, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    ).encode()
    return hashlib.sha256(data).hexdigest()


def block(text: str, begin: str = BEGIN, end: str = END) -> str | None:
    text = normalize(text)
    if begin not in text and end not in text:
        return None
    if text.count(begin) != 1 or text.count(end) != 1:
        raise ValueError("Duplicate or incomplete instruction markers; review the document")
    start, stop = text.index(begin), text.index(end)
    if stop < start:
        raise ValueError("Instruction end marker precedes begin marker")
    return text[start:stop + len(end)]


def replace_block(text: str, desired: str | None) -> str:
    """Keep unmanaged prose; put our block immediately after the config block."""
    text = normalize(text)
    previous = block(text)
    if previous is not None:
        text = text.replace(previous, "", 1)
    # Validate the other manager's boundaries without interpreting its contents.
    shared = block(text, CONFIG_BEGIN, CONFIG_END)
    if desired is not None:
        if shared is not None:
            stop = text.index(CONFIG_END) + len(CONFIG_END)
            text = text[:stop].rstrip() + "\n\n" + desired + "\n\n" + text[stop:].lstrip("\n")
        else:
            text = text.rstrip() + ("\n\n" if text.strip() else "") + desired
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text + ("\n" if text else "")


def metadata(profile: str, mode: str) -> str:
    return (
        f"{BEGIN}\n"
        f"- Active root profile: `{profile}`; agent mode: `{mode}`.\n"
        "- Use the user-selected root model and effort.\n"
        f"{END}"
    )


def desired_docs(profile: str | None, mode: str | None) -> dict[str, str | None]:
    if profile is None:
        return dict.fromkeys(DOCS)
    selected = manage_roles.normalize_mode(profile, mode)
    return {
        "AGENTS.md": metadata(profile, selected),
        "WORK.md": block((ROOT / "work" / "agents-subset.md").read_text(encoding="utf-8")),
        "PRIVATE.md": block((ROOT / "private" / "agents-subset.md").read_text(encoding="utf-8")),
    }


def load_state(home: Path) -> dict | None:
    path = home / "profiles" / STATE
    manage_roles.regular(path)
    if not path.exists():
        return None
    state = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(state, dict) or state.get("version") != 1:
        raise ValueError("Unknown instruction ownership state")
    profile = state.get("profile")
    if profile is not None:
        manage_roles.normalize_mode(profile, state.get("mode"))
    owned = state.get("owned")
    if not isinstance(owned, dict) or not set(owned) <= set(DOCS):
        raise ValueError("Unsafe document in instruction ownership state")
    opencode = state.get("opencode")
    if opencode is not None:
        if (not isinstance(opencode, dict) or not isinstance(opencode.get("path"), str)
                or not Path(opencode["path"]).is_absolute()
                or not isinstance(opencode.get("owned"), dict)
                or not set(opencode["owned"]) <= AGENT_NAMES):
            raise ValueError("Unsafe OpenCode ownership state")
    for sha in list(owned.values()) + list((opencode or {}).get("owned", {}).values()):
        if not isinstance(sha, str) or not re.fullmatch("[0-9a-f]{64}", sha):
            raise ValueError("Invalid instruction ownership hash")
    return state


def _read(path: Path) -> bytes | None:
    manage_roles.directory(path.parent)
    manage_roles.regular(path)
    return path.read_bytes() if path.exists() else None


def prepare(
    home: Path,
    profile: str | None,
    mode: str | None,
    *,
    opencode_config: Path | None = None,
    clean_legacy_agents=None,
    legacy_blocks=None,
) -> dict:
    """Preflight every owned block before writing any file; state never holds providers."""
    home = Path(os.path.abspath(home.expanduser()))
    state = load_state(home)
    desired = desired_docs(profile, mode)
    old: dict[Path, bytes | None] = {}
    target: dict[Path, bytes | None] = {}
    owned = {}
    for name in DOCS:
        path = home / name
        raw = _read(path)
        old[path] = raw
        text = raw.decode("utf-8-sig") if raw is not None else ""
        current = block(text)
        previous_sha = (state or {}).get("owned", {}).get(name)
        if previous_sha is not None and (current is None or digest(current) != previous_sha):
            raise ValueError(f"Managed instruction block changed or missing; review it before proceeding: {name}")
        if previous_sha is None and current is not None:
            # Without a baseline, only exact published legacy blocks are safe
            # to migrate. A marker alone is not proof that user edits are owned.
            known = legacy_blocks() if name == "AGENTS.md" and legacy_blocks is not None else []
            if current != desired[name] and current not in known:
                raise ValueError(f"Unowned instruction block collision: {name}")
        if name == "AGENTS.md" and current is None and clean_legacy_agents is not None:
            text = clean_legacy_agents(text)
        result = replace_block(text, desired[name])
        target[path] = result.encode("utf-8") if result else None
        if desired[name] is not None:
            owned[name] = digest(desired[name])

    previous_opencode = (state or {}).get("opencode")
    opencode_state = previous_opencode
    if opencode_config is not None:
        path = Path(os.path.abspath(opencode_config.expanduser()))
        if path in target or path == home / "config.toml" or path == home / "profiles" / STATE:
            raise ValueError("OpenCode path collides with Codex managed files")
        if previous_opencode is not None and Path(previous_opencode["path"]) != path:
            raise ValueError("Another OpenCode config is already owned; remove its named agents first")
        raw = _read(path)
        if raw is None:
            raise ValueError("--opencode-config must name an existing JSON config")
        data = json.loads(raw.decode("utf-8-sig"))
        if not isinstance(data, dict) or not isinstance(data.get("agent", {}), dict):
            raise ValueError("OpenCode config must contain an object and optional agent object")
        definitions = json.loads((ROOT / "work" / "opencode-agents.json").read_text(encoding="utf-8"))["agent"]
        agents = data.get("agent", {})
        prior_owned = (previous_opencode or {}).get("owned", {})
        for name, sha in prior_owned.items():
            if name not in agents or digest(agents[name]) != sha:
                raise ValueError(f"Managed OpenCode agent changed or missing; review it: {name}")
        for name, definition in definitions.items():
            if name in agents and name not in prior_owned and agents[name] != definition:
                raise ValueError(f"Unowned OpenCode agent collision: {name}")
        old[path] = raw
        if profile is None:
            for name in prior_owned:
                agents.pop(name, None)
            opencode_state = None
        else:
            agents.update(definitions)
            data["agent"] = agents
            opencode_state = {"path": str(path), "owned": {name: digest(value) for name, value in definitions.items()}}
        encoded = (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        # A removal without ownership must not rewrite an unrelated config.
        target[path] = encoded if profile is not None or prior_owned else raw

    manifest = home / "profiles" / STATE
    old[manifest] = _read(manifest)
    state_data = {"version": 1, "profile": profile, "mode": mode, "owned": owned}
    if opencode_state is not None:
        state_data["opencode"] = opencode_state
    target[manifest] = (
        (json.dumps(state_data, ensure_ascii=False, indent=2) + "\n").encode()
        if owned or opencode_state is not None else None
    )
    return {"old": old, "target": target, "files": [str(path.relative_to(home)) if path.is_relative_to(home) else str(path)
            for path in target if old[path] != target[path]]}


def write(path: Path, data: bytes | None) -> None:
    if data is None:
        path.unlink(missing_ok=True)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=".codex-instructions-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def commit(plan: dict) -> None:
    for path, raw in plan["old"].items():
        if _read(path) != raw:
            raise ValueError("Instruction or OpenCode config changed during preflight; retry")
    changed = [path for path in plan["target"] if plan["old"][path] != plan["target"][path]]
    try:
        for path in changed:
            write(path, plan["target"][path])
    except Exception:
        for path in changed:
            try:
                write(path, plan["old"][path])
            except OSError:
                pass
        raise


def status(home: Path) -> dict:
    state = load_state(home)
    if state is None:
        return {"managed": False, "changed_blocks": [], "opencode": None}
    changed = []
    for name, sha in state["owned"].items():
        raw = _read(home / name)
        current = block(raw.decode("utf-8-sig")) if raw is not None else None
        if current is None or digest(current) != sha:
            changed.append(name)
    return {"managed": True, "changed_blocks": changed,
            "opencode": state.get("opencode", {}).get("path")}
