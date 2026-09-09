#!/usr/bin/env python3
"""Manage only profile-owned Codex role files. Python 3.11+, no dependencies."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
import tomllib

ROOT = Path(__file__).resolve().parents[1]
PROFILES = {"lite": "luna", "strict-common": "luna", "private": "sol", "work": "luna"}
ALIASES = ("default", "worker", "explorer")
ROLE_FILES = {"luna-worker.toml", "sol-worker.toml"}
ALIAS_FILES = {f"profile-{name}.toml" for name in ALIASES}
OWNABLE = ROLE_FILES | ALIAS_FILES
RESERVED_NAMES = {"luna_worker", "sol_worker", *ALIASES}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def regular(path: Path) -> None:
    if path.is_symlink() or (path.exists() and not path.is_file()):
        raise ValueError(f"Not a regular, non-symlink file: {path}")


def directory(path: Path) -> None:
    # Reject symlinked ancestors too. Junctions need an OS-specific review on Windows.
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


def alias_bytes(base: bytes, name: str) -> bytes:
    text = base.replace(b"\r\n", b"\n").decode("utf-8")
    alias, count = re.subn(r'^name = "[^"]+"$', f'name = "{name}"', text, count=1, flags=re.M)
    if count != 1:
        raise ValueError("Cannot derive a pinned profile role alias")
    return alias.encode()


def desired_roles(profile: str, root: Path = ROOT) -> dict[str, bytes]:
    if profile not in PROFILES:
        raise ValueError(f"Unknown profile: {profile}")
    result = {
        path.name: path.read_bytes().replace(b"\r\n", b"\n")
        for path in sorted((root / profile / "agents").glob("*.toml"))
    }
    base = result[f"{PROFILES[profile]}-worker.toml"]
    for name in ALIASES:
        result[f"profile-{name}.toml"] = alias_bytes(base, name)
    for filename, data in result.items():
        if filename not in OWNABLE:
            raise ValueError(f"Unexpected role filename: {filename}")
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
    if (
        not isinstance(state, dict)
        or state.get("version") != 1
        or state.get("profile") not in PROFILES
    ):
        raise ValueError("Unknown or malformed profile role state")
    owned = state.get("owned")
    if not isinstance(owned, dict) or not owned:
        raise ValueError("Missing profile role ownership manifest")
    for name, sha in owned.items():
        if (
            name not in OWNABLE
            or not isinstance(sha, str)
            or not re.fullmatch(r"[0-9a-f]{64}", sha)
        ):
            raise ValueError("Unsafe filename or hash in profile role state")
    return state


def manage(
    home: Path,
    profile: str | None,
    *,
    dry_run: bool = False,
    root: Path = ROOT,
) -> dict:
    """Synchronize canonical profile roles after a collision-safe preflight."""
    home = Path(os.path.abspath(home.expanduser()))
    agents = home / "agents"
    control = home / "profiles"
    manifest = control / "roles-state.json"
    lock = control / "roles.lock"
    for path in (home, agents, control, lock):
        directory(path)
    if lock.exists():
        raise ValueError("Another role operation may be active; review roles.lock before retrying")
    state = load_state(manifest)
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

    target = desired_roles(profile, root) if profile else {}
    for path in sorted(agents.glob("*.toml")) if agents.exists() else []:
        if path.name in current:
            continue
        regular(path)
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
                    "version": 1,
                    "profile": profile,
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
    report = {"profile": profile, "changed_roles": changes, "dry_run": dry_run}
    if dry_run or (not changes and old_state == state_bytes):
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
    remove = subs.add_parser("remove")
    for command in (install, remove):
        command.add_argument("--home", type=Path, default=argparse.SUPPRESS)
        command.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        result = manage(
            args.home,
            getattr(args, "profile", None),
            dry_run=args.dry_run,
        )
    except (OSError, ValueError, KeyError, UnicodeError) as exc:
        parser.exit(1, f"No successful role update: {exc}\n")
    print(json.dumps(result, indent=2))
    print("Roles only. Complete the documented config/AGENTS merge and a fresh-thread smoke test.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
