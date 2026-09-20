#!/usr/bin/env python3
"""Install an exact Codex profile role set. Python 3.11+, no dependencies."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import tomllib

ROOT = Path(__file__).resolve().parents[1]
PROFILES = {"lite", "strict-common", "private", "work"}
MODE_PROFILES = {"private", "work"}
MODES = {"solo", "team"}
ROLE_FILES = {"luna-worker.toml", "sol-worker.toml"}
LEGACY_ALIAS_FILES = {"profile-default.toml", "profile-worker.toml", "profile-explorer.toml"}
OWNABLE = ROLE_FILES | LEGACY_ALIAS_FILES
RESERVED_NAMES = {"luna_worker", "sol_worker", "default", "worker", "explorer"}


def normalize_mode(profile: str, mode: str | None) -> str:
    if profile not in PROFILES:
        raise ValueError(f"Unknown profile: {profile}")
    if profile in MODE_PROFILES:
        selected = mode or "solo"
        if selected not in MODES:
            raise ValueError(f"Unknown mode for {profile}: {selected}")
        return selected
    if mode not in (None, "team"):
        raise ValueError(f"{profile} has fixed team routing; mode switching is only supported for private/work")
    return "team"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def regular(path: Path) -> None:
    if path.is_symlink() or (path.exists() and not path.is_file()):
        raise ValueError(f"Not a regular, non-symlink file: {path}")


def directory(path: Path) -> None:
    for part in (path, *path.parents):
        if part.is_symlink() or (hasattr(part, "is_junction") and part.is_junction()):
            raise ValueError(f"Linked directory requires manual review: {part}")
    if path.exists() and not path.is_dir():
        raise ValueError(f"Not a directory: {path}")


def atomic_write(path: Path, data: bytes) -> None:
    fd, name = tempfile.mkstemp(prefix=".codex-profile-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def desired_roles(profile: str, mode: str | None = None, root: Path = ROOT) -> dict[str, bytes]:
    selected = normalize_mode(profile, mode)
    if profile in MODE_PROFILES and selected == "solo":
        return {}
    result = {
        path.name: path.read_bytes().replace(b"\r\n", b"\n")
        for path in sorted((root / profile / "agents").glob("*.toml"))
    }
    expected = {
        "lite": {"luna-worker.toml"},
        "strict-common": {"luna-worker.toml"},
        "private": {"luna-worker.toml", "sol-worker.toml"},
        "work": {"luna-worker.toml", "sol-worker.toml"},
    }[profile]
    if set(result) != expected:
        raise ValueError(f"Unexpected role set for {profile}: {', '.join(sorted(result))}")
    for filename, data in result.items():
        role = tomllib.loads(data.decode("utf-8"))
        if not all(
            role.get(key)
            for key in (
                "name",
                "description",
                "model",
                "model_reasoning_effort",
                "developer_instructions",
            )
        ):
            raise ValueError(f"Incomplete pinned role: {filename}")
        if role.get("agents", {}).get("enabled") is not False:
            raise ValueError(f"Nested delegation must be disabled: {filename}")
    return result


def load_state(path: Path) -> dict | None:
    regular(path)
    if not path.exists():
        return None
    state = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(state, dict) or state.get("profile") not in PROFILES:
        raise ValueError("Unknown or malformed profile role state")
    version = state.get("version")
    if version not in {1, 2}:
        raise ValueError("Unknown or malformed profile role state")
    profile = state["profile"]
    if version == 1:
        mode = "team"
    else:
        mode = normalize_mode(profile, state.get("mode"))
    owned = state.get("owned")
    if not isinstance(owned, dict):
        raise ValueError("Missing profile role ownership manifest")
    if version == 1 and not owned:
        raise ValueError("Missing profile role ownership manifest")
    for name, sha in owned.items():
        if (
            name not in OWNABLE
            or not isinstance(sha, str)
            or len(sha) != 64
            or any(ch not in "0123456789abcdef" for ch in sha)
        ):
            raise ValueError("Unsafe filename or hash in profile role state")
    return {"version": version, "profile": profile, "mode": mode, "owned": owned}


def manage(
    home: Path,
    profile: str | None,
    *,
    mode: str | None = None,
    dry_run: bool = False,
    root: Path = ROOT,
) -> dict:
    """Replace all top-level role TOMLs on install; remove owned roles on uninstall."""
    home = Path(os.path.abspath(home.expanduser()))
    agents = home / "agents"
    control = home / "profiles"
    legacy_control = home / "routing-rules"
    manifest = control / "roles-state.json"
    lock = control / "roles.lock"
    legacy_lock = legacy_control / "roles.lock"
    for path in (home, agents, control, legacy_control, lock, legacy_lock):
        directory(path)
    if lock.exists() or legacy_lock.exists():
        raise ValueError("Another role operation may be active; review roles.lock before retrying")

    selected_mode = normalize_mode(profile, mode) if profile is not None else None
    regular(manifest)
    state = load_state(manifest) if profile is None else None
    current: dict[str, bytes] = {}
    if state:
        for name, sha in state["owned"].items():
            path = agents / name
            regular(path)
            if not path.exists() or digest(path.read_bytes()) != sha:
                raise ValueError(
                    f"Managed role changed or missing; review it before proceeding: {name}"
                )
            current[name] = path.read_bytes()

    target = desired_roles(profile, selected_mode, root) if profile else {}
    for path in sorted(agents.glob("*.toml")) if agents.exists() else []:
        if path.name in current:
            continue
        regular(path)
        if profile is not None:
            current[path.name] = path.read_bytes()
            continue
        role = tomllib.loads(path.read_text(encoding="utf-8-sig"))
        if path.name in OWNABLE or role.get("name") in RESERVED_NAMES:
            raise ValueError(f"Unmanaged role collision: {path}")

    changes = sorted(
        name
        for name in set(current) | set(target)
        if current.get(name) != target.get(name)
    )
    state_bytes = (
        (
            json.dumps(
                {
                    "version": 2,
                    "profile": profile,
                    "mode": selected_mode,
                    "owned": {name: digest(data) for name, data in sorted(target.items())},
                },
                indent=2,
            )
            + "\n"
        ).encode()
        if profile
        else None
    )
    old_state = manifest.read_bytes() if manifest.exists() else None
    legacy_removed = profile is not None and legacy_control.exists()
    report = {
        "profile": profile,
        "mode": selected_mode,
        "changed_roles": changes,
        "legacy_removed": legacy_removed,
        "dry_run": dry_run,
    }
    if dry_run or (not changes and old_state == state_bytes and not legacy_removed):
        return report

    control.mkdir(parents=True, exist_ok=True)
    lock.mkdir()
    try:
        if (manifest.read_bytes() if manifest.exists() else None) != old_state:
            raise ValueError("Ownership state changed during preflight; retry")
        for name, data in current.items():
            regular(agents / name)
            if (agents / name).read_bytes() != data:
                raise ValueError(f"Role changed during preflight: {name}")
        for name in target.keys() - current.keys():
            regular(agents / name)
            if (agents / name).exists():
                raise ValueError(f"Role appeared during preflight: {name}")
        agents.mkdir(parents=True, exist_ok=True)
        try:
            for name in changes:
                if name in target:
                    atomic_write(agents / name, target[name])
                else:
                    (agents / name).unlink()
            if state_bytes is not None:
                atomic_write(manifest, state_bytes)
            elif manifest.exists():
                manifest.unlink()
            if legacy_removed:
                resolved_legacy = legacy_control.resolve()
                resolved_home = home.resolve()
                if resolved_legacy == resolved_home or resolved_home not in resolved_legacy.parents:
                    raise ValueError("Legacy routing directory escapes the selected Codex home")
                shutil.rmtree(legacy_control)
        except OSError:
            for name in changes:
                if name in current:
                    atomic_write(agents / name, current[name])
                elif (agents / name).exists():
                    (agents / name).unlink()
            if old_state is not None:
                atomic_write(manifest, old_state)
            elif manifest.exists():
                manifest.unlink()
            raise
    finally:
        if lock.exists():
            lock.rmdir()
        if profile is None:
            try:
                control.rmdir()
            except OSError:
                pass
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--home",
        type=Path,
        default=Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex"),
    )
    subs = parser.add_subparsers(dest="command", required=True)
    install = subs.add_parser("install")
    install.add_argument("profile", choices=sorted(PROFILES))
    install.add_argument("--mode", choices=sorted(MODES))
    remove = subs.add_parser("remove")
    for command in (install, remove):
        command.add_argument("--home", type=Path, default=argparse.SUPPRESS)
        command.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        result = manage(
            args.home,
            getattr(args, "profile", None),
            mode=getattr(args, "mode", None),
            dry_run=args.dry_run,
        )
    except (OSError, ValueError, KeyError, UnicodeError) as exc:
        parser.exit(1, f"No successful role update: {exc}\n")
    print(json.dumps(result, indent=2))
    print("Roles only. Use manage_profile.py for the complete profile lifecycle.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
