#!/usr/bin/env python3
"""Install, switch, mode-switch, remove, and inspect one complete Codex profile."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import tomllib

import manage_roles

ROOT = Path(__file__).resolve().parents[1]
PROFILES = tuple(sorted(manage_roles.PROFILES))
MODES = tuple(sorted(manage_roles.MODES))
BEGIN = "<!-- codex-profiles:begin -->"
END = "<!-- codex-profiles:end -->"
LEGACY_BEGIN = "<!-- codex-routing-rules:begin -->"
LEGACY_END = "<!-- codex-routing-rules:end -->"
MANAGED_COMMENT = "# codex-profiles: managed profile keys"
LEGACY_MANAGED_COMMENT = "# codex-routing-rules: managed profile keys"
SECTION_RE = re.compile(r"^\s*\[([^\[\]]+)\]\s*(?:#.*)?$")
ASSIGN_RE = re.compile(r"^\s*([A-Za-z0-9_-]+)\s*=")
MANAGED_CATALOG = "models-managed.json"
LEGACY_LITE_CATALOG = "models-lite.json"

OWNED_KEYS = {
    "": {"model", "model_reasoning_effort", "model_catalog_json"},
    "agents": {
        "enabled",
        "max_concurrent_threads_per_session",
        "default_subagent_model",
        "default_subagent_reasoning_effort",
    },
    "features.context_management": {"experimental_mode"},
    "features.multi_agent_v2": {"multi_agent_mode_hint_text"},
    "memories": {"extract_model", "consolidation_model"},
}
LEGACY_KEYS = {
    "features": {"multi_agent", "multi_agent_v2"},
    "features.multi_agent_v2": {"enabled", "max_concurrent_threads_per_session"},
}
PROFILE_HEADINGS = (
    "## Scope routing",
    "## Agent routing — lite",
    "## Agent routing — strict-common",
    "## Agent routing — private",
    "## Agent routing — private team",
    "## Agent routing — work",
    "## Agent routing — work team",
    "## Agent routing — x5",
    "## Agent routing — x20",
    "## Agent routing — x20-work",
    "## Маршрутизация агентов — lite",
    "## Маршрутизация агентов — strict-common",
    "## Маршрутизация агентов — private",
    "## Маршрутизация агентов — work",
    "## Маршрутизация агентов — x5",
    "## Маршрутизация агентов — x20",
    "## Маршрутизация агентов — x20-work",
)


def _normalize(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
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


def _render(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    raise ValueError(f"Unsupported managed TOML value: {value!r}")


def _flatten(data: dict) -> dict[str, dict[str, object]]:
    result: dict[str, dict[str, object]] = {"": {}}

    def visit(prefix: str, mapping: dict) -> None:
        for key, value in mapping.items():
            if isinstance(value, dict):
                visit(f"{prefix}.{key}" if prefix else key, value)
            else:
                result.setdefault(prefix, {})[key] = value

    for key, value in data.items():
        if isinstance(value, dict):
            visit(key, value)
        else:
            result[""][key] = value
    return result


def _prune_empty_managed_sections(text: str) -> str:
    lines = _normalize(text).splitlines()
    managed_sections = set(OWNED_KEYS) | set(LEGACY_KEYS)
    managed_sections.discard("")
    out: list[str] = []
    index = 0
    while index < len(lines):
        match = SECTION_RE.match(lines[index])
        if not match:
            out.append(lines[index])
            index += 1
            continue
        section = match.group(1).strip()
        end = index + 1
        while end < len(lines) and not SECTION_RE.match(lines[end]):
            end += 1
        body = lines[index + 1 : end]
        if section in managed_sections and not any(line.strip() for line in body):
            index = end
            continue
        out.extend(lines[index:end])
        index = end
    return "\n".join(out).rstrip() + ("\n" if out else "")


def _remove_managed_assignments(text: str, *, remove_catalog: bool) -> str:
    remove = {section: set(keys) for section, keys in OWNED_KEYS.items()}
    for section, keys in LEGACY_KEYS.items():
        remove.setdefault(section, set()).update(keys)
    if not remove_catalog:
        remove[""].discard("model_catalog_json")

    current_section = ""
    out: list[str] = []
    for line in _normalize(text).splitlines():
        match = SECTION_RE.match(line)
        if match:
            current_section = match.group(1).strip()
            out.append(line)
            continue
        if line.strip() in {MANAGED_COMMENT, LEGACY_MANAGED_COMMENT}:
            continue
        assignment = ASSIGN_RE.match(line)
        if assignment and assignment.group(1) in remove.get(current_section, set()):
            continue
        out.append(line)
    return _prune_empty_managed_sections("\n".join(out))


def _insert_managed_assignments(
    text: str, desired: dict[str, dict[str, object]]
) -> str:
    lines = _normalize(text).rstrip("\n").splitlines()

    top = desired.get("", {})
    if top:
        first_header = next(
            (i for i, line in enumerate(lines) if SECTION_RE.match(line)), len(lines)
        )
        prefix, suffix = lines[:first_header], lines[first_header:]
        while prefix and prefix[-1] == "":
            prefix.pop()
        additions = [MANAGED_COMMENT] + [
            f"{key} = {_render(value)}" for key, value in top.items()
        ]
        lines = prefix + ([""] if prefix else []) + additions + [""] + suffix

    for section, values in desired.items():
        if section == "" or not values:
            continue
        additions = [MANAGED_COMMENT] + [
            f"{key} = {_render(value)}" for key, value in values.items()
        ]
        header_index = None
        for index, line in enumerate(lines):
            match = SECTION_RE.match(line)
            if match and match.group(1).strip() == section:
                header_index = index
                break
        if header_index is None:
            while lines and lines[-1] == "":
                lines.pop()
            lines.extend(["", f"[{section}]", *additions])
            continue
        end = len(lines)
        for index in range(header_index + 1, len(lines)):
            if SECTION_RE.match(lines[index]):
                end = index
                break
        insertion = end
        while insertion > header_index + 1 and lines[insertion - 1] == "":
            insertion -= 1
        lines[insertion:insertion] = [*additions, ""]

    result = "\n".join(lines).rstrip() + "\n"
    tomllib.loads(result)
    return result


def _desired_config(
    profile: str, mode: str, home: Path
) -> dict[str, dict[str, object]]:
    source = tomllib.loads(
        (ROOT / profile / "config.toml").read_text(encoding="utf-8")
    )
    if profile == "lite":
        source["model_catalog_json"] = (home / MANAGED_CATALOG).as_posix()
    if profile in manage_roles.MODE_PROFILES:
        if mode == "team":
            source["agents"] = {
                "enabled": True,
                "max_concurrent_threads_per_session": 2,
            }
            features = source.setdefault("features", {})
            features["multi_agent_v2"] = {"multi_agent_mode_hint_text": ""}
        else:
            source.pop("agents", None)
            features = source.get("features")
            if isinstance(features, dict):
                features.pop("multi_agent_v2", None)
    return _flatten(source)


def _profile_catalog(value: object, home: Path) -> bool:
    if not isinstance(value, str) or not value:
        return False
    normalized = value.replace("\\", "/").lower()
    home_norm = home.as_posix().rstrip("/").lower()
    return normalized in {
        f"{home_norm}/{MANAGED_CATALOG}".lower(),
        f"{home_norm}/{LEGACY_LITE_CATALOG}".lower(),
        f"{home_norm}/models.json",
    }


def build_config(
    text: str,
    profile: str | None,
    home: Path,
    *,
    mode: str | None = None,
    previous_profile: str | None = None,
) -> str:
    parsed = tomllib.loads(text) if text.strip() else {}
    catalog = parsed.get("model_catalog_json")
    profile_catalog = _profile_catalog(catalog, home)
    if catalog is not None and not profile_catalog:
        if profile is not None:
            raise ValueError(
                "Unrelated model_catalog_json is active. Resolve that catalog explicitly "
                "before installing a Codex profile; it will not be deleted as profile-owned state."
            )
        remove_catalog = False
    else:
        remove_catalog = catalog is not None

    cleaned = _remove_managed_assignments(text, remove_catalog=remove_catalog)
    if profile is None:
        if cleaned.strip():
            tomllib.loads(cleaned)
        return cleaned

    selected_mode = manage_roles.normalize_mode(profile, mode)
    return _insert_managed_assignments(
        cleaned,
        _desired_config(profile, selected_mode, home),
    )


def _extract_marked(text: str) -> str:
    normalized = _normalize(text)
    start = normalized.find(BEGIN)
    stop = normalized.find(END)
    if start < 0 or stop < start:
        raise ValueError("Profile routing file has no single managed marker block")
    stop += len(END)
    if (
        normalized.find(BEGIN, start + len(BEGIN)) >= 0
        or normalized.find(END, stop) >= 0
    ):
        raise ValueError("Profile routing file has duplicate marker blocks")
    return normalized[start:stop].strip()


def _strip_marked_regions(text: str, begin: str, end: str) -> str:
    depth = 0
    kept: list[str] = []
    for line in _normalize(text).splitlines():
        marker = line.strip()
        if marker == begin:
            depth += 1
            continue
        if marker == end:
            if not depth:
                raise ValueError(f"Profile marker has no matching begin: {end}")
            depth -= 1
            continue
        if depth == 0:
            kept.append(line)
    if depth:
        raise ValueError(f"Profile marker has no matching end: {begin}")
    return "\n".join(kept)


def _git_history_blocks() -> list[str]:
    if not (ROOT / ".git").exists() or shutil.which("git") is None:
        return []
    paths = [f"{profile}/agents-subset.md" for profile in PROFILES]
    try:
        proc = subprocess.run(
            ["git", "-C", str(ROOT), "log", "--all", "--format=%H", "--", *paths],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=20,
        )
    except (OSError, subprocess.SubprocessError):
        return []
    commits = list(
        dict.fromkeys(line.strip() for line in proc.stdout.splitlines() if line.strip())
    )
    blocks: list[str] = []
    for commit in commits:
        for profile, path in zip(PROFILES, paths):
            try:
                shown = subprocess.run(
                    ["git", "-C", str(ROOT), "show", f"{commit}:{path}"],
                    check=True,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    timeout=10,
                ).stdout
            except (OSError, subprocess.SubprocessError):
                continue
            normalized = _normalize(shown).strip()
            if not normalized:
                continue
            if BEGIN in normalized and END in normalized:
                try:
                    blocks.append(_extract_marked(normalized))
                except ValueError:
                    pass
            else:
                blocks.append(normalized)
    return list(dict.fromkeys(blocks))


def build_agents(text: str, profile: str | None, *, mode: str | None = None) -> str:
    normalized = _normalize(text)
    for begin, end in ((BEGIN, END), (LEGACY_BEGIN, LEGACY_END)):
        normalized = _strip_marked_regions(normalized, begin, end)

    for block in sorted(_git_history_blocks(), key=len, reverse=True):
        normalized = normalized.replace(block, "")

    lines = normalized.splitlines()
    first_owned_heading = next(
        (
            index
            for index, line in enumerate(lines)
            if line.strip() in PROFILE_HEADINGS
        ),
        None,
    )
    if first_owned_heading is not None:
        raise ValueError(
            "Unmarked profile routing heading has no safe deletion boundary: "
            f"{lines[first_owned_heading].strip()}"
        )

    normalized = re.sub(r"\n{3,}", "\n\n", normalized).strip()
    install_block = False
    if profile is not None:
        selected_mode = manage_roles.normalize_mode(profile, mode)
        install_block = (
            profile not in manage_roles.MODE_PROFILES or selected_mode == "team"
        )
    if install_block:
        block = _extract_marked(
            (ROOT / profile / "agents-subset.md").read_text(encoding="utf-8")
        )
        normalized = f"{normalized}\n\n{block}" if normalized else block
    return normalized.rstrip() + ("\n" if normalized else "")


def _supported_efforts(model: dict) -> set[str]:
    levels = model.get("supported_reasoning_levels")
    if not isinstance(levels, list):
        return set()
    return {
        level.get("effort")
        for level in levels
        if isinstance(level, dict) and isinstance(level.get("effort"), str)
    }


def _managed_catalog_bytes(catalog: dict, profile: str) -> bytes:
    if profile != "lite":
        raise ValueError("Managed model catalog is only used by the lite profile")

    models = catalog.get("models") if isinstance(catalog, dict) else None
    if not isinstance(models, list):
        raise ValueError("Expected Codex model metadata with models[]")

    by_slug: dict[str, dict] = {}
    for model in models:
        if not isinstance(model, dict) or not isinstance(model.get("slug"), str):
            raise ValueError(
                "Unrecognized model metadata; refusing to manufacture entries"
            )
        slug = model["slug"]
        if slug in by_slug:
            raise ValueError(f"Duplicate model slug: {slug}")
        by_slug[slug] = dict(model)

    model = by_slug.get("gpt-6-luna")
    if model is None:
        raise ValueError("Required lite model is unavailable: gpt-6-luna")
    if "max" not in _supported_efforts(model):
        raise ValueError("Metadata does not confirm gpt-6-luna / max")
    if model.get("multi_agent_version") != "v2":
        raise ValueError("Metadata does not confirm gpt-6-luna Multi-Agent V2")

    result = dict(catalog)
    result["models"] = [model]
    return (json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def _capture_catalog(profile: str, models: Path | None) -> bytes:
    if models is not None:
        catalog = json.loads(models.read_text(encoding="utf-8-sig"))
        return _managed_catalog_bytes(catalog, profile)
    try:
        proc = subprocess.run(
            ["codex", "debug", "models", "--bundled"],
            check=True,
            capture_output=True,
            text=True,
            timeout=60,
        )
    except FileNotFoundError as exc:
        raise ValueError(
            "Codex executable not found; pass --models with captured model metadata"
        ) from exc
    except subprocess.CalledProcessError as exc:
        raise ValueError(
            f"`codex debug models --bundled` failed: {exc.stderr.strip()}"
        ) from exc
    return _managed_catalog_bytes(json.loads(proc.stdout), profile)


def _apply_text(path: Path, text: str) -> None:
    if text.strip():
        _atomic_write(path, text.encode("utf-8"))
    elif path.exists():
        path.unlink()


def apply(
    home: Path,
    profile: str | None,
    *,
    mode: str | None = None,
    dry_run: bool = False,
    models: Path | None = None,
    refresh_catalog: bool = True,
) -> dict:
    home = Path(os.path.abspath(home.expanduser()))
    config_path = home / "config.toml"
    agents_path = home / "AGENTS.md"
    catalog_path = home / MANAGED_CATALOG
    legacy_lite_path = home / LEGACY_LITE_CATALOG
    legacy_models_path = home / "models.json"

    config_text = (
        config_path.read_text(encoding="utf-8-sig") if config_path.exists() else ""
    )
    agents_text = (
        agents_path.read_text(encoding="utf-8-sig") if agents_path.exists() else ""
    )
    parsed_config = tomllib.loads(config_text) if config_text.strip() else {}
    configured_catalog = parsed_config.get("model_catalog_json")
    legacy_models_owned = (
        _profile_catalog(configured_catalog, home)
        and isinstance(configured_catalog, str)
        and configured_catalog.replace("\\", "/").lower().endswith("/models.json")
    )

    manifest = home / "profiles" / "roles-state.json"
    try:
        role_state = manage_roles.load_state(manifest)
    except (ValueError, UnicodeError, json.JSONDecodeError):
        if profile is None:
            raise
        role_state = None
    previous_profile = role_state.get("profile") if role_state else None

    selected_mode = (
        manage_roles.normalize_mode(profile, mode) if profile is not None else None
    )
    new_config = build_config(
        config_text,
        profile,
        home,
        mode=selected_mode,
        previous_profile=previous_profile,
    )
    new_agents = build_agents(agents_text, profile, mode=selected_mode)

    if profile == "lite":
        if refresh_catalog:
            catalog_bytes = _capture_catalog(profile, models)
        else:
            if not catalog_path.is_file():
                raise ValueError(
                    "Managed model catalog is missing; reinstall lite to rebuild it"
                )
            catalog_bytes = catalog_path.read_bytes()
    else:
        catalog_bytes = None

    role_plan = manage_roles.manage(
        home,
        profile,
        mode=selected_mode,
        dry_run=True,
        root=ROOT,
    )

    current_config = config_path.read_bytes() if config_path.exists() else None
    desired_config = new_config.encode("utf-8") if new_config.strip() else None
    current_agents = agents_path.read_bytes() if agents_path.exists() else None
    desired_agents = new_agents.encode("utf-8") if new_agents.strip() else None
    current_catalog = catalog_path.read_bytes() if catalog_path.exists() else None

    changes: list[str] = []
    if desired_config != current_config:
        changes.append("config.toml")
    if desired_agents != current_agents:
        changes.append("AGENTS.md")
    if catalog_bytes != current_catalog:
        changes.append(MANAGED_CATALOG)
    if legacy_lite_path.exists():
        changes.append(LEGACY_LITE_CATALOG)
    if legacy_models_owned and legacy_models_path.exists():
        changes.append("models.json")
    if role_plan.get("legacy_removed"):
        changes.append("routing-rules/")

    report = {
        "profile": profile,
        "mode": selected_mode,
        "dry_run": dry_run,
        "files": changes,
        "roles": role_plan["changed_roles"],
    }
    if dry_run:
        return report

    old: dict[Path, bytes | None] = {
        config_path: current_config,
        agents_path: current_agents,
        catalog_path: current_catalog,
        legacy_lite_path: (
            legacy_lite_path.read_bytes() if legacy_lite_path.exists() else None
        ),
    }
    if legacy_models_owned:
        old[legacy_models_path] = (
            legacy_models_path.read_bytes() if legacy_models_path.exists() else None
        )

    try:
        _apply_text(config_path, new_config)
        _apply_text(agents_path, new_agents)
        if catalog_bytes is None:
            catalog_path.unlink(missing_ok=True)
        else:
            _atomic_write(catalog_path, catalog_bytes)
        legacy_lite_path.unlink(missing_ok=True)
        if legacy_models_owned:
            legacy_models_path.unlink(missing_ok=True)

        manage_roles.manage(
            home,
            profile,
            mode=selected_mode,
            dry_run=False,
            root=ROOT,
        )
    except Exception:
        for path, data in old.items():
            try:
                if data is None:
                    path.unlink(missing_ok=True)
                else:
                    _atomic_write(path, data)
            except OSError:
                pass
        raise
    return report


def _state(home: Path) -> dict | None:
    return manage_roles.load_state(home.expanduser() / "profiles" / "roles-state.json")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--home",
        type=Path,
        default=Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex"),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    install = sub.add_parser(
        "install", help="Switch the complete routing lifecycle to PROFILE"
    )
    install.add_argument("profile", choices=PROFILES)
    install.add_argument("--mode", choices=MODES)
    install.add_argument(
        "--models",
        type=Path,
        help="Captured bundled model-catalog JSON for offline/testing lite installs",
    )
    install.add_argument("--dry-run", action="store_true")

    mode_cmd = sub.add_parser(
        "mode", help="Switch private/work between native solo and selective team"
    )
    mode_cmd.add_argument("mode", choices=MODES)
    mode_cmd.add_argument("--dry-run", action="store_true")

    remove = sub.add_parser(
        "remove", help="Remove all repository-owned Codex profile artifacts"
    )
    remove.add_argument("--dry-run", action="store_true")

    sub.add_parser("status", help="Show the active managed profile and mode")

    args = parser.parse_args()
    home = args.home.expanduser()

    try:
        if args.command == "status":
            state = _state(home)
            print(
                json.dumps(
                    {
                        "profile": state.get("profile") if state else None,
                        "mode": state.get("mode") if state else None,
                    },
                    indent=2,
                )
            )
            return 0

        if args.command == "mode":
            state = _state(home)
            if not state:
                raise ValueError("No managed profile is installed")
            profile = state["profile"]
            if profile not in manage_roles.MODE_PROFILES:
                raise ValueError(
                    f"{profile} has fixed team routing; mode switching is only supported for private/work"
                )
            result = apply(
                home,
                profile,
                mode=args.mode,
                dry_run=args.dry_run,
                refresh_catalog=False,
            )
        elif args.command == "install":
            result = apply(
                home,
                args.profile,
                mode=args.mode,
                dry_run=args.dry_run,
                models=args.models,
                refresh_catalog=True,
            )
        else:
            result = apply(
                home,
                None,
                dry_run=args.dry_run,
                refresh_catalog=False,
            )
    except (
        OSError,
        ValueError,
        KeyError,
        UnicodeError,
        json.JSONDecodeError,
        tomllib.TOMLDecodeError,
    ) as exc:
        parser.exit(1, f"No successful profile update: {exc}\n")

    print(json.dumps(result, indent=2))
    if not args.dry_run:
        print("Restart Codex completely and start a new thread.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
