#!/usr/bin/env python3
"""Static preset checks; optionally validate source or generated model metadata."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import tomllib

import manage_roles

ROOT = Path(__file__).resolve().parents[1]
BEGIN = "<!-- codex-profiles:begin -->"
END = "<!-- codex-profiles:end -->"

ROOTS = {
    "strict-common": ("gpt-6.1-sol", "xhigh"),
    "private": ("gpt-6-astra", "xhigh"),
    "work": ("gpt-6.1-sol", "xhigh"),
}
TEAM_ROLES = {
    "strict-common": {"luna_worker": ("gpt-6-luna", "max")},
    "private": {
        "luna_worker": ("gpt-6-luna", "max"),
        "sol_worker": ("gpt-6.1-sol", "xhigh"),
    },
    "work": {
        "luna_worker": ("gpt-6-luna", "max"),
        "sol_worker": ("gpt-6.1-sol", "xhigh"),
    },
}

def _catalog_errors(
    catalog: dict,
    required: set[tuple[str, str]],
) -> list[str]:
    errors: list[str] = []
    models = catalog.get("models") if isinstance(catalog, dict) else None
    if not isinstance(models, list) or not all(
        isinstance(model, dict) and isinstance(model.get("slug"), str)
        for model in models
    ):
        return ["Unrecognized metadata: expected models[] with slug"]
    index = {model["slug"]: model for model in models}
    if len(index) != len(models):
        errors.append("Duplicate model slugs in metadata")
    for slug, effort in sorted(required):
        levels = index.get(slug, {}).get("supported_reasoning_levels", [])
        supported = (
            {item.get("effort") for item in levels if isinstance(item, dict)}
            if isinstance(levels, list)
            else set()
        )
        if effort not in supported:
            errors.append(f"Model metadata does not confirm {slug} / {effort}")
    return errors


def validate(
    root: Path = ROOT,
    catalog: dict | None = None,
    profile: str | None = None,
) -> list[str]:
    errors: list[str] = []
    required: set[tuple[str, str]] = set()
    if profile is not None and profile not in ROOTS:
        return [f"Unknown profile: {profile}"]

    def check(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    check((root / "scripts" / "manage_profile.py").is_file(), "unified profile lifecycle manager missing")
    check(set(ROOTS) == set(manage_roles.PROFILES), "public profile registry drift")

    for name, (root_model, root_effort) in ROOTS.items():
        config = tomllib.loads((root / name / "config.toml").read_text(encoding="utf-8"))
        check(
            config.get("model") == root_model
            and config.get("model_reasoning_effort") == root_effort,
            f"{name}: root pin drift",
        )
        check(
            config.get("features", {}).get("context_management")
            == {"experimental_mode": True},
            f"{name}: experimental context management drift",
        )
        if name in manage_roles.MODE_PROFILES:
            check("agents" not in config, f"{name}: base config must leave native agents untouched in solo")
            check(
                "multi_agent_v2" not in config.get("features", {}),
                f"{name}: base config must not suppress native multi-agent mode in solo",
            )
        else:
            expected_cap = 4
            check(
                config.get("agents")
                == {"enabled": True, "max_concurrent_threads_per_session": expected_cap},
                f"{name}: fixed team agent cap drift",
            )
            check(
                config.get("features", {}).get("multi_agent_v2")
                == {"multi_agent_mode_hint_text": ""},
                f"{name}: fixed team multi-agent hint drift",
            )
        expected_memories = {
            "strict-common": {
                "extract_model": "gpt-6-luna",
                "consolidation_model": "gpt-6-luna",
            },
            "private": {},
            "work": {
                "extract_model": "gpt-6-luna",
                "consolidation_model": "gpt-6-luna",
            },
        }[name]
        check(config.get("memories", {}) == expected_memories, f"{name}: memory routing drift")

        actual_roles: dict[str, tuple[str, str]] = {}
        for path in (root / name / "agents").glob("*.toml"):
            role = tomllib.loads(path.read_text(encoding="utf-8"))
            role_name = role.get("name")
            check(role_name not in actual_roles, f"{name}: duplicate role {role_name}")
            actual_roles[role_name] = (
                role.get("model"),
                role.get("model_reasoning_effort"),
            )
            check(
                bool(role.get("description")) and bool(role.get("developer_instructions")),
                f"{name}: incomplete role {role_name}",
            )
            check(
                role.get("agents", {}).get("enabled") is False,
                f"{name}: nested delegation enabled",
            )
        check(actual_roles == TEAM_ROLES[name], f"{name}: unexpected/missing team role")

        team_files = set(manage_roles.desired_roles(name, "team", root))
        expected_files = {
            "luna-worker.toml"
        } | ({"sol-worker.toml"} if name in {"private", "work"} else set())
        check(team_files == expected_files, f"{name}: explicit team role files drift")
        check(
            not any(filename.startswith("profile-") for filename in team_files),
            f"{name}: generated routing aliases must not exist",
        )
        if name in manage_roles.MODE_PROFILES:
            check(
                manage_roles.desired_roles(name, "solo", root) == {},
                f"{name}: solo must install no custom roles",
            )

        text = (root / name / "agents-subset.md").read_text(encoding="utf-8")
        stripped = text.strip()
        check(
            text.count(BEGIN) == 1 and text.count(END) == 1,
            f"{name}: routing marker drift",
        )
        check(
            stripped.startswith(BEGIN) and stripped.endswith(END),
            f"{name}: profile instructions exist outside the managed lifecycle block",
        )
        check('fork_turns = "none"' in text, f"{name}: explicit bounded fork policy missing")
        if name in {"private", "work"}:
            check("two open child threads" in text, f"{name}: team cap policy missing")
            check("automatic reviewer" in text, f"{name}: no-automatic-review policy missing")
            check("Sol-first" in text, f"{name}: Sol-first personal routing policy missing")
            check(
                "bounded or limited to a few files is not enough" in text,
                f"{name}: bounded-scope Luna guard missing",
            )
            check(
                "Owner reuse never overrides model suitability" in text,
                f"{name}: model reassessment policy missing",
            )
        for operation in ("install", "remove"):
            page = (root / name / f"{operation}-{name}.md").read_text(encoding="utf-8")
            check(f"../docs/{operation}.md" in page, f"{name}: {operation} procedure drift")
            check(
                "scripts/manage_profile.py" in page,
                f"{name}: {operation} does not use unified profile lifecycle",
            )
            check(
                "scripts/manage_roles.py" not in page,
                f"{name}: {operation} exposes obsolete roles-only lifecycle",
            )

        if profile is None or profile == name:
            required.add((root_model, root_effort))
            if name == "strict-common":
                required.add(("gpt-6-luna", "max"))
            elif name in {"private", "work"}:
                required.add(("gpt-6-luna", "max"))
                required.add(("gpt-6.1-sol", "xhigh"))

    if catalog is not None:
        errors.extend(_catalog_errors(catalog, required))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--models", type=Path, help="Unmodified JSON from `codex debug models --bundled`")
    parser.add_argument("--profile", choices=sorted(ROOTS), help="Limit live metadata requirements")
    args = parser.parse_args()
    try:
        raw = json.loads(args.models.read_text(encoding="utf-8-sig")) if args.models else None
        errors = validate(catalog=raw, profile=args.profile)
    except (OSError, ValueError, TypeError) as exc:
        parser.exit(1, f"Validation could not complete: {exc}\n")
    if errors:
        print("\n".join(errors))
        return 1
    print(
        "PASS: three static profiles"
        + (" and supplied model metadata" if raw else "")
    )
    print("Not a Codex runtime, account entitlement, quota or model-behavior test.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
