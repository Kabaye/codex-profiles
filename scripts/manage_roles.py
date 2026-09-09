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
LEGACY_PROFILES = {"x5": "strict-common", "x20": "private", "x20-work": "work"}
ALIASES = ("default", "worker", "explorer")
ROLE_FILES = {"luna-worker.toml", "sol-worker.toml", "astra-worker.toml"}
ALIAS_FILES = {f"profile-{name}.toml" for name in ALIASES}
LEGACY_ALIAS_FILES = {f"routing-{name}.toml" for name in ALIASES}
CANONICAL_OWNABLE = ROLE_FILES | ALIAS_FILES
OWNABLE = CANONICAL_OWNABLE | LEGACY_ALIAS_FILES
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
# Immutable Git blob hashes for aliases generated from every known historical
# Luna/Sol/Astra worker blob. This keeps manifestless migration exact even in a
# shallow clone or source export where the old worker contents are unavailable.
HISTORICAL_ALIAS_BLOBS = {
    "routing-default.toml": {
        "038d31627ad2f7dc81c54d2c2e0038caa43382b3",
        "c95d3e5fdacb1015e393fe091c68563cd01d25df",
        "c823621777f01be23c045003398ae04bcd20d0b5",
        "e149cb5c80ab272498bf6529d35a8a0b14c85315",
        "2d1fae8b81ae8fbc283d3cd877735a0f6133c11b",
        "c93bec1efce1f84327d8a3069533c7ee22c727f1",
        "6f68e8700a19c73fd8e7cb9a1d16813723e384fb",
        "2813c8ce2cec9c7dac4b3b3b15f0057e0d6dcb8b",
        "c9b2fde74bed48e6c79aaba93ec6f7b80abbd83b",
        "882f430bba0d9351977af22b20c10a38eed21046",
    },
    "routing-worker.toml": {
        "4019b39202a044dcde4c065e29f9a6d6cdd2ef86",
        "c2c9e3edeeea7b5fbf383ede52eb6baad801642c",
        "81abef6d788c816577f257f47789eb491397712c",
        "39a0f339e011789a7ff1432bf439978ce155af84",
        "740b68a849ad8629752f835efab5d7aa6b828937",
        "54da141272e171791faaeabd7fbcb04eeea16a63",
        "899abb1b63eb781a15c5d389f068b4060331d7d5",
        "51d4b05d036f8eee2660416282c85c33a7ba4f6d",
        "a66bc66b709dfd0998b2365abb020424b01d8f31",
        "d9f26c136b89fffe727c00586b07b83e2ad5c350",
    },
    "routing-explorer.toml": {
        "64d6271ce7e192f33f7a6e66cc15b9242a76510c",
        "12074f1e2cf0869872968bb57b700d6bb711fb48",
        "292b190e3213af66fdb678260ea762023e60a366",
        "6651fef82499cb5ee620436ab3d7b1643a8fd2fb",
        "d7d23e8ca73133c387bbae40c5250420f9afab61",
        "716f8876b08994bca3d8567b6c4b55b1f1cc1def",
        "280151b87d7034c3bb10aba3e82c30178b85c4c2",
        "64255c3d55b9974f6fbcd6ac5c68e7998d9ac9a5",
        "201d5b07c53a7bf42479ee130875ac91bc4c9b77",
        "37828d07757ae529826c6877d6de579876bc5dc7",
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
        raise ValueError("Cannot derive a pinned compatibility role")
    return alias.encode()


def desired_roles(profile: str, root: Path = ROOT) -> dict[str, bytes]:
    if profile not in PROFILES:
        raise ValueError(f"Unknown profile: {profile}")
    result = {p.name: p.read_bytes().replace(b"\r\n", b"\n") for p in sorted((root / profile / "agents").glob("*.toml"))}
    base = result[f"{PROFILES[profile]}-worker.toml"]
    for name in ALIASES:
        result[f"profile-{name}.toml"] = alias_bytes(base, name)
    for filename, data in result.items():
        if filename not in OWNABLE:
            raise ValueError(f"Unexpected role filename: {filename}")
        role = tomllib.loads(data.decode("utf-8"))
        if not all(role.get(k) for k in ("name", "description", "model", "model_reasoning_effort", "developer_instructions")):
            raise ValueError(f"Incomplete pinned role: {filename}")
        if role.get("agents", {}).get("enabled") is not False:
            raise ValueError(f"Nested delegation must be disabled: {filename}")
    return result


def prepare_legacy_alias_adoption(root: Path = ROOT) -> None:
    """Recognize only exact aliases derivable from repository profile roles."""
    for filename, blobs in HISTORICAL_ALIAS_BLOBS.items():
        LEGACY.setdefault(filename, set()).update(blobs)
    for profile in PROFILES:
        for filename, data in desired_roles(profile, root).items():
            if not filename.startswith("profile-"):
                continue
            legacy_name = filename.replace("profile-", "routing-", 1)
            LEGACY.setdefault(legacy_name, set()).add(git_blob(data))


def load_state(path: Path, *, allow_legacy: bool = False) -> dict | None:
    regular(path)
    if not path.exists():
        return None
    state = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(state, dict) or state.get("version") != 1:
        raise ValueError("Unknown or malformed profile role state")
    raw_profile = state.get("profile")
    if raw_profile not in PROFILES:
        if not allow_legacy or raw_profile not in LEGACY_PROFILES:
            raise ValueError("Unknown or malformed profile role state")
        state = dict(state)
        state["profile"] = LEGACY_PROFILES[raw_profile]
        state["legacy_profile"] = raw_profile
    owned = state.get("owned")
    if not isinstance(owned, dict) or not owned:
        raise ValueError("Missing profile role ownership manifest")
    allowed_files = OWNABLE if allow_legacy else CANONICAL_OWNABLE
    for name, sha in owned.items():
        if name not in allowed_files or not isinstance(sha, str) or not re.fullmatch(r"[0-9a-f]{64}", sha):
            raise ValueError("Unsafe filename or hash in profile role state")
    return state


def discover_state(home: Path) -> tuple[Path, dict | None, bool]:
    """Return the one active manifest and normalize legacy profile names."""
    manifest = home / "profiles" / "roles-state.json"
    legacy_manifest = home / "routing-rules" / "roles-state.json"
    regular(manifest)
    regular(legacy_manifest)
    if manifest.exists() and legacy_manifest.exists():
        raise ValueError(
            "Both current and legacy profile ownership states exist; review them before retrying"
        )
    if manifest.exists():
        return manifest, load_state(manifest), False
    if legacy_manifest.exists():
        return legacy_manifest, load_state(legacy_manifest, allow_legacy=True), True
    return manifest, None, False


def manage(home: Path, profile: str | None, *, adopt_legacy: bool = False, dry_run: bool = False,
           root: Path = ROOT) -> dict:
    """Preflight before writes and roll back ordinary I/O failures in-process.

    No persistent backups are created. This is not a security boundary or a
    crash-atomic multi-file transaction. Close Codex and stop concurrent config
    edits first. The manifest never owns config/AGENTS/data.
    """
    home = Path(os.path.abspath(home.expanduser()))
    agents = home / "agents"
    control, legacy_control = home / "profiles", home / "routing-rules"
    manifest, legacy_manifest = control / "roles-state.json", legacy_control / "roles-state.json"
    lock, legacy_lock = control / "roles.lock", legacy_control / "roles.lock"
    for p in (home, agents, control, legacy_control, lock, legacy_lock):
        directory(p)
    if lock.exists() or legacy_lock.exists():
        raise ValueError("Another role operation may be active; review roles.lock before retrying")
    state_path, state, legacy_state = discover_state(home)
    current: dict[str, bytes] = {}
    if state:
        for name, sha in state["owned"].items():
            p = agents / name
            regular(p)
            if not p.exists() or digest(p.read_bytes()) != sha:
                raise ValueError(f"Managed role changed or missing; review it before proceeding: {name}")
            current[name] = p.read_bytes()

    target = desired_roles(profile, root) if profile else {}
    prepare_legacy_alias_adoption(root)
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
    old_state = state_path.read_bytes() if state_path.exists() else None
    report = {
        "profile": profile,
        "changed_roles": changes,
        "dry_run": dry_run,
        "migrated_legacy_state": legacy_state,
    }
    if dry_run or (not changes and not legacy_state and old_state == state_bytes):
        return report
    control.mkdir(parents=True, exist_ok=True)
    legacy_control.mkdir(parents=True, exist_ok=True)
    lock.mkdir()
    legacy_lock_created = False
    try:
        legacy_lock.mkdir()  # Also excludes the previous repository installer.
        legacy_lock_created = True
        # Recheck the snapshot after acquiring the lock.
        if (state_path.read_bytes() if state_path.exists() else None) != old_state:
            raise ValueError("Ownership state changed during preflight; retry")
        other_manifest = legacy_manifest if state_path == manifest else manifest
        if other_manifest.exists():
            raise ValueError("A second profile ownership state appeared during preflight; retry")
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
            if legacy_manifest.exists():
                legacy_manifest.unlink()
        except OSError:
            # Restore the original bytes immediately; do not create persistent backups.
            for name in changes:
                if name in current:
                    atomic_write(agents / name, current[name])
                elif (agents / name).exists():
                    (agents / name).unlink()
            for candidate in (manifest, legacy_manifest):
                if candidate != state_path and candidate.exists():
                    candidate.unlink()
            if old_state is not None:
                state_path.parent.mkdir(parents=True, exist_ok=True)
                atomic_write(state_path, old_state)
            elif state_path.exists():
                state_path.unlink()
            raise
    finally:
        if legacy_lock_created and legacy_lock.exists():
            legacy_lock.rmdir()
        if lock.exists():
            lock.rmdir()
        for candidate in (legacy_control, control if profile is None else None):
            if candidate is not None:
                try:
                    candidate.rmdir()
                except OSError:
                    pass
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
