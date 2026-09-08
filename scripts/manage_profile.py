#!/usr/bin/env python3
"""Install, switch, remove, and inspect one complete Codex routing profile."""
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
BEGIN = "<!-- codex-routing-rules:begin -->"
END = "<!-- codex-routing-rules:end -->"
MANAGED_COMMENT = "# codex-routing-rules: managed profile keys"
SECTION_RE = re.compile(r"^\s*\[([^\[\]]+)\]\s*(?:#.*)?$")
ASSIGN_RE = re.compile(r"^\s*([A-Za-z0-9_-]+)\s*=")

OWNED_KEYS = {
    "": {"model", "model_reasoning_effort"},
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
    "features.multi_agent_v2": {
        "enabled",
        "max_concurrent_threads_per_session",
    },
}
KNOWN_ROLE_BLOBS = {
    "luna-worker.toml": {
        "c960e0e34ffbc1ee40fdbf73cc6635af1dab60fb",
        "5dcea4f991890b0103b4f5446395eb80d61df477",
        "6a65f3b4b2d5fc13f05273cf2cb86240fcdac19d",
        "c6c010c844e362bd436eada5e2daaaf11f292b70",
    },
    "sol-worker.toml": {
        "46bca9c72b0c4e5817e3a6de4c8c70121e158bb8",
        "4c3154ffc6e748219c2a229f924bf07c1714c846",
        "7a9e47d62df4c4990f1ab6158abb9273a7129bf3",
        "a14cbe6178b2d959a4a93e74fa215680d81371b6",
    },
    "astra-worker.toml": {
        "a41a60779a1e8b912bd9367d8ac395f2252fbd5c",
    },
}
LEGACY_HEADINGS = (
    "## Scope routing",
    "## Agent routing — lite",
    "## Agent routing — x5",
    "## Agent routing — x20",
    "## Agent routing — x20-work",
    "## Маршрутизация агентов — lite",
    "## Маршрутизация агентов — x5",
    "## Маршрутизация агентов — x20",
    "## Маршрутизация агентов — x20-work",
)


def _normalize(text: str) -> str:
    return text.replace("\r\n", "\n")


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=".routing-profile-", dir=path.parent)
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


def _remove_managed_assignments(text: str, *, include_legacy: bool, remove_catalog: bool) -> str:
    remove = {section: set(keys) for section, keys in OWNED_KEYS.items()}
    if remove_catalog:
        remove.setdefault("", set()).add("model_catalog_json")
    if include_legacy:
        for section, keys in LEGACY_KEYS.items():
            remove.setdefault(section, set()).update(keys)

    current = ""
    out: list[str] = []
    for line in _normalize(text).splitlines():
        match = SECTION_RE.match(line)
        if match:
            current = match.group(1).strip()
            out.append(line)
            continue
        if line.strip() == MANAGED_COMMENT:
            continue
        assignment = ASSIGN_RE.match(line)
        if assignment and assignment.group(1) in remove.get(current, set()):
            continue
        out.append(line)
    return "\n".join(out).rstrip() + "\n"


def _insert_managed_assignments(text: str, desired: dict[str, dict[str, object]]) -> str:
    lines = _normalize(text).rstrip("\n").splitlines()

    top = desired.get("", {})
    if top:
        first_header = next((i for i, line in enumerate(lines) if SECTION_RE.match(line)), len(lines))
        prefix, suffix = lines[:first_header], lines[first_header:]
        while prefix and prefix[-1] == "":
            prefix.pop()
        additions = [MANAGED_COMMENT] + [f"{key} = {_render(value)}" for key, value in top.items()]
        lines = prefix + ([""] if prefix else []) + additions + [""] + suffix

    for section, values in desired.items():
        if section == "" or not values:
            continue
        additions = [MANAGED_COMMENT] + [f"{key} = {_render(value)}" for key, value in values.items()]
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


def _desired_config(profile: str, home: Path) -> dict[str, dict[str, object]]:
    source = tomllib.loads((ROOT / profile / "config.toml").read_text(encoding="utf-8"))
    if profile == "lite":
        source["model_catalog_json"] = (home / "models-lite.json").as_posix()
    return _flatten(source)


def _routing_catalog(value: object, home: Path) -> bool:
    if not isinstance(value, str) or not value:
        return False
    normalized = value.replace("\\", "/")
    home_norm = home.as_posix().rstrip("/").lower()
    lowered = normalized.lower()
    return (
        lowered.endswith("/models-lite.json")
        or (lowered.endswith("/models.json") and lowered.startswith(home_norm))
    )


def build_config(text: str, profile: str | None, home: Path, *, previous_profile: str | None = None) -> str:
    parsed = tomllib.loads(text) if text.strip() else {}
    catalog = parsed.get("model_catalog_json")
    routing_catalog = _routing_catalog(catalog, home) or previous_profile == "lite"
    if catalog is not None and not routing_catalog:
        if profile is not None:
            raise ValueError(
                "Unrelated model_catalog_json is active. Resolve that catalog explicitly before "
                "installing a routing profile; it will not be deleted as legacy state."
            )
        remove_catalog = False
    else:
        remove_catalog = catalog is not None

    cleaned = _remove_managed_assignments(
        text,
        include_legacy=True,
        remove_catalog=remove_catalog or profile == "lite",
    )
    if profile is None:
        if cleaned.strip():
            tomllib.loads(cleaned)
        return cleaned
    return _insert_managed_assignments(cleaned, _desired_config(profile, home))


def _extract_marked(text: str) -> str:
    normalized = _normalize(text)
    start = normalized.find(BEGIN)
    stop = normalized.find(END)
    if start < 0 or stop < start:
        raise ValueError("Profile routing file has no single managed marker block")
    stop += len(END)
    if normalized.find(BEGIN, start + len(BEGIN)) >= 0 or normalized.find(END, stop) >= 0:
        raise ValueError("Profile routing file has duplicate marker blocks")
    return normalized[start:stop].strip()


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
            timeout=20,
        )
    except (OSError, subprocess.SubprocessError):
        return []
    commits = list(dict.fromkeys(line.strip() for line in proc.stdout.splitlines() if line.strip()))
    blocks: list[str] = []
    for commit in commits:
        for profile, path in zip(PROFILES, paths):
            try:
                shown = subprocess.run(
                    ["git", "-C", str(ROOT), "show", f"{commit}:{path}"],
                    check=True,
                    capture_output=True,
                    text=True,
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
                continue
            if profile == "lite":
                lines = normalized.splitlines()
                index = next(
                    (
                        i
                        for i, line in enumerate(lines)
                        if line.startswith("## ")
                        and ("routing" in line.lower() or "маршрутизац" in line.lower())
                    ),
                    None,
                )
                if index is not None:
                    blocks.append("\n".join(lines[index:]).strip())
            else:
                blocks.append(normalized)
    return list(dict.fromkeys(blocks))


def build_agents(text: str, profile: str | None) -> str:
    normalized = _normalize(text)
    marked = re.compile(
        rf"(?:^|\n)[ \t]*{re.escape(BEGIN)}.*?{re.escape(END)}[ \t]*(?=\n|$)",
        re.S,
    )
    normalized = marked.sub("\n", normalized)

    for block in sorted(_git_history_blocks(), key=len, reverse=True):
        normalized = normalized.replace(block, "")

    for heading in LEGACY_HEADINGS:
        if heading in normalized:
            raise ValueError(
                f"Modified legacy routing section remains in AGENTS.md ({heading!r}); "
                "review/remove that old repository-owned block once, then retry"
            )

    normalized = re.sub(r"\n{3,}", "\n\n", normalized).strip()
    if profile is not None:
        block = _extract_marked((ROOT / profile / "agents-subset.md").read_text(encoding="utf-8"))
        normalized = f"{normalized}\n\n{block}" if normalized else block
    return normalized.rstrip() + "\n"


def _filter_lite_catalog(catalog: dict) -> bytes:
    allowed = ("gpt-5.6-terra", "gpt-5.6-luna")
    required_effort = {"gpt-5.6-terra": "medium", "gpt-5.6-luna": "max"}
    models = catalog.get("models") if isinstance(catalog, dict) else None
    if not isinstance(models, list):
        raise ValueError("Expected Codex model metadata with models[]")
    by_slug: dict[str, dict] = {}
    for model in models:
        if not isinstance(model, dict) or not isinstance(model.get("slug"), str):
            raise ValueError("Unrecognized model metadata; refusing to manufacture entries")
        slug = model["slug"]
        if slug in by_slug:
            raise ValueError(f"Duplicate model slug: {slug}")
        by_slug[slug] = model
    filtered = []
    for slug in allowed:
        model = by_slug.get(slug)
        if model is None:
            raise ValueError(f"Required lite model is unavailable: {slug}")
        levels = model.get("supported_reasoning_levels")
        supported = (
            {level.get("effort") for level in levels if isinstance(level, dict)}
            if isinstance(levels, list)
            else set()
        )
        if required_effort[slug] not in supported:
            raise ValueError(f"Metadata does not confirm {slug} / {required_effort[slug]}")
        filtered.append(model)
    result = dict(catalog)
    result["models"] = filtered
    return (json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def _lite_catalog(models: Path | None) -> bytes:
    if models is not None:
        return _filter_lite_catalog(json.loads(models.read_text(encoding="utf-8-sig")))
    try:
        proc = subprocess.run(
            ["codex", "debug", "models"],
            check=True,
            capture_output=True,
            text=True,
            timeout=60,
        )
    except FileNotFoundError as exc:
        raise ValueError("Codex executable not found; pass --models with captured model metadata") from exc
    except subprocess.CalledProcessError as exc:
        raise ValueError(f"`codex debug models` failed: {exc.stderr.strip()}") from exc
    return _filter_lite_catalog(json.loads(proc.stdout))


def _prepare_legacy_role_adoption(home: Path) -> None:
    for filename, blobs in KNOWN_ROLE_BLOBS.items():
        manage_roles.LEGACY.setdefault(filename, set()).update(blobs)

    agents = home / "agents"
    if not agents.exists():
        return
    for path in agents.glob("routing-*.toml"):
        try:
            role = tomllib.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, UnicodeError, tomllib.TOMLDecodeError):
            continue
        alias = path.stem.removeprefix("routing-")
        if alias not in manage_roles.ALIASES or role.get("name") != alias:
            continue
        if role.get("agents", {}).get("enabled") is not False:
            continue
        pair = (role.get("model"), role.get("model_reasoning_effort"))
        if pair not in {
            ("gpt-5.6-luna", "max"),
            ("gpt-5.6-sol", "high"),
            ("gpt-5.6-sol", "xhigh"),
            ("gpt-6-astra", "high"),
        }:
            continue
        data = path.read_bytes()
        manage_roles.LEGACY.setdefault(path.name, set()).add(manage_roles.git_blob(data))


def _apply_text(path: Path, text: str) -> None:
    if text.strip():
        _atomic_write(path, text.encode("utf-8"))
    elif path.exists():
        path.unlink()


def apply(
    home: Path,
    profile: str | None,
    *,
    dry_run: bool = False,
    models: Path | None = None,
) -> dict:
    home = Path(os.path.abspath(home.expanduser()))
    config_path = home / "config.toml"
    agents_path = home / "AGENTS.md"
    config_text = config_path.read_text(encoding="utf-8-sig") if config_path.exists() else ""
    agents_text = agents_path.read_text(encoding="utf-8-sig") if agents_path.exists() else ""

    manifest = home / "routing-rules" / "roles-state.json"
    role_state = manage_roles.load_state(manifest)
    previous_profile = role_state.get("profile") if role_state else None
    new_config = build_config(config_text, profile, home, previous_profile=previous_profile)
    new_agents = build_agents(agents_text, profile)
    catalog_bytes = _lite_catalog(models) if profile == "lite" else None
    catalog_path = home / "models-lite.json"

    _prepare_legacy_role_adoption(home)
    role_plan = manage_roles.manage(
        home,
        profile,
        adopt_legacy=True,
        dry_run=True,
        root=ROOT,
    )

    current_config = config_path.read_bytes() if config_path.exists() else None
    desired_config = new_config.encode("utf-8") if new_config.strip() else None
    current_agents = agents_path.read_bytes() if agents_path.exists() else None
    desired_agents = new_agents.encode("utf-8") if new_agents.strip() else None

    changes = []
    if desired_config != current_config:
        changes.append("config.toml")
    if desired_agents != current_agents:
        changes.append("AGENTS.md")
    if profile == "lite" and catalog_bytes != (catalog_path.read_bytes() if catalog_path.exists() else None):
        changes.append("models-lite.json")
    if profile is None and catalog_path.exists():
        changes.append("models-lite.json")

    report = {
        "profile": profile,
        "dry_run": dry_run,
        "files": changes,
        "roles": role_plan["changed_roles"],
    }
    if dry_run:
        return report

    # Keep only an in-process rollback snapshot. Nothing is persisted as a backup.
    old = {
        config_path: current_config,
        agents_path: current_agents,
        catalog_path: catalog_path.read_bytes() if catalog_path.exists() else None,
    }
    try:
        _apply_text(config_path, new_config)
        _apply_text(agents_path, new_agents)
        if profile == "lite":
            assert catalog_bytes is not None
            _atomic_write(catalog_path, catalog_bytes)
        elif catalog_path.exists():
            catalog_path.unlink()
        manage_roles.manage(
            home,
            profile,
            adopt_legacy=True,
            dry_run=False,
            root=ROOT,
        )
    except Exception:
        for path, data in old.items():
            try:
                if data is None:
                    if path.exists():
                        path.unlink()
                else:
                    _atomic_write(path, data)
            except OSError:
                pass
        raise
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--home",
        type=Path,
        default=Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex"),
    )
    sub = parser.add_subparsers(dest="command", required=True)
    install = sub.add_parser("install", help="Switch the complete routing lifecycle to PROFILE")
    install.add_argument("profile", choices=PROFILES)
    install.add_argument(
        "--models",
        type=Path,
        help="Captured `codex debug models` JSON (needed for offline lite install)",
    )
    remove = sub.add_parser("remove", help="Remove all repository-owned routing profile artifacts")
    status = sub.add_parser("status", help="Show the active managed profile")
    for command in (install, remove):
        command.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    try:
        if args.command == "status":
            manifest = args.home.expanduser() / "routing-rules" / "roles-state.json"
            state = manage_roles.load_state(manifest)
            print(json.dumps({"profile": state.get("profile") if state else None}, indent=2))
            return 0
        profile = args.profile if args.command == "install" else None
        result = apply(
            args.home,
            profile,
            dry_run=args.dry_run,
            models=getattr(args, "models", None),
        )
    except (OSError, ValueError, KeyError, UnicodeError, json.JSONDecodeError) as exc:
        parser.exit(1, f"No successful profile migration: {exc}\n")

    print(json.dumps(result, indent=2))
    if not args.dry_run:
        print("Restart Codex completely and start a new thread.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
