#!/usr/bin/env python3
"""Manage only routing-owned Codex role files. Python 3.11+, no dependencies."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
import tomllib
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
PROFILES = {"lite": "luna", "x5": "luna", "x20": "sol", "x20-work": "luna"}
ALIASES = ("default", "worker", "explorer")
ROLE_FILES = {"luna-worker.toml", "sol-worker.toml", "astra-worker.toml"}
OWNABLE = ROLE_FILES | {f"routing-{name}.toml" for name in ALIASES}
RESERVED_NAMES = {"luna_worker", "sol_worker", "astra_worker", *ALIASES}
# Exact blobs shipped before this migration; never adopt a modified lookalike.
LEGACY = {
    "luna-worker.toml": {
        "c960e0e34ffbc1ee40fdbf73cc6635af1dab60fb",
        "5dcea4f991890b0103b4f5446395eb80d61df477",
    },
    "sol-worker.toml": {
        "46bca9c72b0c4e5817e3a6de4c8c70121e158bb8",
        "4c3154ffc6e748219c2a229f924bf07c1714c846",
    },
}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_blob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


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
    fd, name = tempfile.mkstemp(prefix=".routing-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def desired_roles(profile: str, root: Path = ROOT) -> dict[str, bytes]:
    if profile not in PROFILES:
        raise ValueError(f"Unknown profile: {profile}")
    result = {p.name: p.read_bytes() for p in sorted((root / profile / "agents").glob("*.toml"))}
    base = result[f"{PROFILES[profile]}-worker.toml"].decode("utf-8")
    for name in ALIASES:
        alias, count = re.subn(r'^name = "[^"]+"$', f'name = "{name}"', base, count=1, flags=re.M)
        if count != 1:
            raise ValueError("Cannot derive a pinned compatibility role")
        result[f"routing-{name}.toml"] = alias.encode()
    for filename, data in result.items():
        if filename not in OWNABLE:
            raise ValueError(f"Unexpected role filename: {filename}")
        role = tomllib.loads(data.decode("utf-8"))
        if not all(role.get(k) for k in ("name", "description", "model", "model_reasoning_effort", "developer_instructions")):
            raise ValueError(f"Incomplete pinned role: {filename}")
        if role.get("agents", {}).get("enabled") is not False:
            raise ValueError(f"Nested delegation must be disabled: {filename}")
    return result


def load_state(path: Path) -> dict | None:
    regular(path)
    if not path.exists():
        return None
    state = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(state, dict) or state.get("version") != 1 or state.get("profile") not in PROFILES:
        raise ValueError("Unknown or malformed routing role state")
    owned = state.get("owned")
    if not isinstance(owned, dict) or not owned:
        raise ValueError("Missing routing role ownership manifest")
    for name, sha in owned.items():
        if name not in OWNABLE or not isinstance(sha, str) or not re.fullmatch(r"[0-9a-f]{64}", sha):
            raise ValueError("Unsafe filename or hash in routing role state")
    return state


def manage(home: Path, profile: str | None, *, adopt_legacy: bool = False, dry_run: bool = False,
           root: Path = ROOT) -> dict:
    """Preflight before writes; archive previous roles and roll back ordinary I/O failures.

    Not a security boundary or crash-atomic multi-file transaction. Close Codex and
    stop concurrent config edits first. The manifest never owns config/AGENTS/data.
    """
    home = Path(os.path.abspath(home.expanduser()))
    agents, control = home / "agents", home / "routing-rules"
    manifest, lock = control / "roles-state.json", control / "roles.lock"
    for p in (home, agents, control, control / "backups", lock):
        directory(p)
    if lock.exists():
        raise ValueError("Another role operation may be active; review roles.lock before retrying")
    state = load_state(manifest)
    current: dict[str, bytes] = {}
    if state:
        for name, sha in state["owned"].items():
            p = agents / name
            regular(p)
            if not p.exists() or digest(p.read_bytes()) != sha:
                raise ValueError(f"Managed role changed or missing; review it before proceeding: {name}")
            current[name] = p.read_bytes()

    target = desired_roles(profile, root) if profile else {}
    for p in sorted(agents.glob("*.toml")) if agents.exists() else []:
        if p.name in current:
            continue
        regular(p)
        data = p.read_bytes()
        old_blob = git_blob(data)
        # Recognize line-ending-only Windows copies without accepting content edits.
        canonical_blob = git_blob(data.replace(b"\r\n", b"\n"))
        known = bool({old_blob, canonical_blob} & LEGACY.get(p.name, set()))
        if known and adopt_legacy:
            current[p.name] = data
            continue
        role = tomllib.loads(data.decode("utf-8-sig"))
        if p.name in OWNABLE or role.get("name") in RESERVED_NAMES:
            hint = " Use --adopt-legacy after reviewing the migration." if known and profile else ""
            raise ValueError(f"Unmanaged role collision: {p}.{hint}")

    changes = sorted(name for name in set(current) | set(target) if current.get(name) != target.get(name))
    state_bytes = (json.dumps({"version": 1, "profile": profile,
                              "owned": {n: digest(d) for n, d in sorted(target.items())}},
                             indent=2) + "\n").encode() if profile else None
    old_state = manifest.read_bytes() if manifest.exists() else None
    report = {"profile": profile, "changed_roles": changes, "dry_run": dry_run, "backup": None}
    if dry_run or (not changes and old_state == state_bytes):
        return report
    control.mkdir(parents=True, exist_ok=True)
    lock.mkdir()  # Excludes a second cooperating installer.
    try:
        # Recheck the snapshot after acquiring the lock.
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
        if current or old_state:
            backup_root = control / "backups"
            backup_root.mkdir(exist_ok=True)
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
            backup = backup_root / stamp
            backup.mkdir()
            for name, data in current.items():
                (backup / name).write_bytes(data)
            if old_state:
                (backup / "roles-state.json").write_bytes(old_state)
            report["backup"] = str(backup)
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
            # Preserve the original bytes, including line endings.
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
        lock.rmdir()
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--home", type=Path, default=Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex"))
    subs = parser.add_subparsers(dest="command", required=True)
    install = subs.add_parser("install")
    install.add_argument("profile", choices=sorted(PROFILES))
    install.add_argument("--adopt-legacy", action="store_true")
    remove = subs.add_parser("remove")
    for sub in (install, remove):
        sub.add_argument("--home", type=Path, default=argparse.SUPPRESS)
        sub.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        result = manage(args.home, getattr(args, "profile", None),
                        adopt_legacy=getattr(args, "adopt_legacy", False), dry_run=args.dry_run)
    except (OSError, ValueError, KeyError, UnicodeError) as exc:
        parser.exit(1, f"No successful role migration: {exc}\n")
    print(json.dumps(result, indent=2))
    print("Roles only. Complete the documented config/AGENTS merge and a fresh-thread smoke test.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
