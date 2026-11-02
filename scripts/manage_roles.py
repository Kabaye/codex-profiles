#!/usr/bin/env python3
"""Manage profile roles in their own Codex agents directory. Python 3.11+."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
import tomllib

import profile_sources

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = profile_sources.load(ROOT)
PROFILES = set(MANIFEST["profiles"])
RETIRED_PROFILES = {"lite"}  # Recognize installed legacy state only for cleanup.
MODE_PROFILES = {name for name, modes in MANIFEST["profiles"].items() if len(modes) > 1}
MODES = {name for modes in MANIFEST["profiles"].values() for name in modes}
ROLE_FILES = profile_sources.role_files(MANIFEST)
ROLE_NAMESPACE = Path(MANIFEST["roles_directory"]).name
LEGACY_ROLE_FILES = {"luna-worker.toml", "sol-worker.toml"}
LEGACY_CONFIG_ROLE_FILES = {"terra-computer.toml"}  # Ownership handoff, never a current source.
LEGACY_ALIAS_FILES = {"profile-default.toml", "profile-worker.toml", "profile-explorer.toml"}
OWNABLE = ROLE_FILES | LEGACY_ROLE_FILES | LEGACY_CONFIG_ROLE_FILES | LEGACY_ALIAS_FILES


def normalize_mode(profile: str, mode: str | None, root: Path = ROOT) -> str:
    return profile_sources.recipe(profile_sources.load(root), profile, mode)[0]


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
    _, item = profile_sources.recipe(profile_sources.load(root), profile, mode)
    result = {
        Path(source).name: profile_sources.source_bytes(root, source)
        for source in item["roles"]
    }
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
    if not isinstance(state, dict) or state.get("profile") not in PROFILES | RETIRED_PROFILES:
        raise ValueError("Unknown or malformed profile role state")
    version = state.get("version")
    if version not in {1, 2, 3}:
        raise ValueError("Unknown or malformed profile role state")
    profile = state["profile"]
    if version == 1 or profile in RETIRED_PROFILES:
        mode = "team"  # Former lite installations had fixed team routing.
    else:
        mode = normalize_mode(profile, state.get("mode"))
    owned = state.get("owned")
    if not isinstance(owned, dict):
        raise ValueError("Missing profile role ownership manifest")
    if version == 1 and not owned:
        raise ValueError("Missing profile role ownership manifest")
    for name, sha in owned.items():
        valid_name = (
            name in OWNABLE if version < 3
            else isinstance(name, str) and name in {f"{ROLE_NAMESPACE}/{item}" for item in ROLE_FILES}
        )
        if (
            not valid_name
            or not isinstance(sha, str)
            or len(sha) != 64
            or any(ch not in "0123456789abcdef" for ch in sha)
        ):
            raise ValueError("Unsafe filename or hash in profile role state")
    return {"version": version, "profile": profile, "mode": mode, "owned": owned}


def verify_legacy_terra_handoff(home: Path) -> None:
    """A former profile-owned Terra must move before its old owner is released."""
    path = home / "codex-config" / "roles-state.json"
    directory(path.parent)
    regular(path)
    message = "Run codex-config sync-roles before transferring the legacy shared role"
    if not path.exists():
        raise ValueError(message)
    state = json.loads(path.read_text(encoding="utf-8"))
    sha = (state.get("owned", {}).get("codex-config/terra-computer.toml")
           if isinstance(state, dict) and isinstance(state.get("owned"), dict) else None)
    role_path = home / "agents" / "codex-config" / "terra-computer.toml"
    directory(role_path.parent)
    regular(role_path)
    if (not isinstance(state, dict) or state.get("version") != 1 or not isinstance(sha, str)
            or not re.fullmatch(r"[0-9a-f]{64}", sha)
            or not role_path.exists() or digest(role_path.read_bytes()) != sha
            or (home / "agents" / "terra-computer.toml").exists()):
        raise ValueError(message)


def manage(
    home: Path,
    profile: str | None,
    *,
    mode: str | None = None,
    dry_run: bool = False,
    root: Path = ROOT,
) -> dict:
    """Manage only this manifest's namespace and verified former flat roles."""
    home = Path(os.path.abspath(home.expanduser()))
    agents = home / "agents"
    role_dir = home / profile_sources.load(root)["roles_directory"]
    namespace = role_dir.name
    control = home / "profiles"
    legacy_control = home / "routing-rules"
    manifest = control / "roles-state.json"
    lock = control / "roles.lock"
    legacy_lock = legacy_control / "roles.lock"
    shared_lock = home / ".agent-roles.lock"
    for path in (home, agents, role_dir, control, legacy_control, lock, legacy_lock, shared_lock):
        directory(path)
    if lock.exists() or legacy_lock.exists() or shared_lock.exists():
        raise ValueError("Another role operation may be active; review roles.lock before retrying")

    selected_mode = normalize_mode(profile, mode, root) if profile is not None else None
    regular(manifest)
    state = load_state(manifest)
    legacy_terra = bool(state and set(state["owned"]) & LEGACY_CONFIG_ROLE_FILES)
    if legacy_terra:
        verify_legacy_terra_handoff(home)
    current: dict[str, bytes] = {}
    if state:
        for name, sha in state["owned"].items():
            if name in LEGACY_CONFIG_ROLE_FILES:
                continue
            path = agents / name
            regular(path)
            directory(path.parent)
            if not path.exists() or ((profile is None or "/" not in name) and digest(path.read_bytes()) != sha):
                raise ValueError(
                    f"Managed role changed or missing; review it before proceeding: {name}"
                )
            current[name] = path.read_bytes()

    sources = desired_roles(profile, selected_mode, root) if profile else {}
    target = {f"{namespace}/{name}": data for name, data in sources.items()}
    for path in sorted(role_dir.glob("*.toml")) if role_dir.exists() else []:
        name = f"{namespace}/{path.name}"
        regular(path)
        if name not in current and name in target:
            if path.read_bytes() != target[name]:
                raise ValueError(f"Unmanaged role collision: {path}")
            current[name] = path.read_bytes()
    # Migrate hand-copied legacy native files only when they are exact sources.
    for path in sorted(agents.glob("*.toml")) if agents.exists() else []:
        if path.name in current or path.name not in ROLE_FILES | LEGACY_ROLE_FILES | LEGACY_ALIAS_FILES:
            continue
        regular(path)
        if profile is not None and path.name in sources and path.read_bytes() == sources[path.name]:
            current[path.name] = path.read_bytes()
        else:
            raise ValueError(f"Unmanaged legacy role collision: {path}")

    changes = sorted(
        name
        for name in set(current) | set(target)
        if current.get(name) != target.get(name)
    )
    state_bytes = (
        (
            json.dumps(
                {
                    "version": 3,
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
    shared_locked = False
    try:
        shared_lock.mkdir()
        shared_locked = True
        if legacy_terra:
            verify_legacy_terra_handoff(home)
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
        role_dir.mkdir(parents=True, exist_ok=True)
        try:
            for name in sorted(changes, key=lambda name: name not in target):
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
        except Exception:
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
        if shared_locked:
            shared_lock.rmdir()
        if lock.exists():
            lock.rmdir()
        try:
            role_dir.rmdir()
        except OSError:
            pass
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
