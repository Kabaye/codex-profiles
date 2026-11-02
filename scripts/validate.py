#!/usr/bin/env python3
"""Static preset checks; optionally validate source or generated model metadata."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import tomllib

import manage_profile
import manage_roles
import profile_sources

ROOT = Path(__file__).resolve().parents[1]
PROFILES = tuple(sorted(manage_roles.PROFILES))

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
    try:
        data = profile_sources.load(root)
    except (OSError, ValueError, UnicodeError) as exc:
        return [str(exc)]
    if profile is not None and profile not in data["profiles"]:
        return [f"Unknown profile: {profile}"]

    def check(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    check((root / "scripts" / "manage_profile.py").is_file(), "unified profile lifecycle manager missing")
    guide = root / "README.md"
    check(guide.is_file(), "profile lifecycle README missing")
    if guide.is_file():
        instructions = guide.read_text(encoding="utf-8")
        for command in ("install", "remove", "sync-instructions", "mode", "status"):
            check(
                f"scripts/manage_profile.py {command}" in instructions,
                f"README omits unified {command} lifecycle command",
            )

    for name, modes in data["profiles"].items():
        for mode, item in modes.items():
            label = f"{name}/{mode}"
            try:
                config = profile_sources.config(root, item)
                manage_profile.validate_config_keys(config)
                for values in manage_profile._flatten(config).values():
                    for value in values.values():
                        manage_profile._render(value)
                profile_sources.instructions(root, data, item)
                selected_roles = manage_roles.desired_roles(name, mode, root)
                pairs = set()
                for filename, raw in selected_roles.items():
                    role = tomllib.loads(raw.decode("utf-8"))
                    check(role["name"] == Path(filename).stem.replace("-", "_"),
                          f"{label}: role filename/name mismatch: {filename}")
                    pairs.add((role["model"], role["model_reasoning_effort"]))
                if "model" in config and "model_reasoning_effort" in config:
                    pairs.add((config["model"], config["model_reasoning_effort"]))
                if profile is None or profile == name:
                    required.update(pairs)
            except (OSError, ValueError, UnicodeError) as exc:
                errors.append(f"{label}: {exc}")
    try:
        opencode = json.loads(profile_sources.source_text(root, data["opencode_agents"]))
        check(isinstance(opencode, dict) and isinstance(opencode.get("agent"), dict),
              "OpenCode source must contain named agents")
    except (OSError, ValueError, UnicodeError) as exc:
        errors.append(f"OpenCode source: {exc}")

    if catalog is not None:
        errors.extend(_catalog_errors(catalog, required))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--models", type=Path, help="Unmodified JSON from `codex debug models --bundled`")
    parser.add_argument("--profile", choices=PROFILES, help="Limit live metadata requirements")
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
        "PASS: manifest profile recipes"
        + (" and supplied model metadata" if raw else "")
    )
    print("Not a Codex runtime, account entitlement, quota or model-behavior test.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
