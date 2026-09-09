#!/usr/bin/env python3
"""Static preset checks; optionally validate real model metadata and the lite catalog."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import tomllib

import manage_roles

ROOT = Path(__file__).resolve().parents[1]
BEGIN = "<!-- codex-profiles:begin -->"
END = "<!-- codex-profiles:end -->"
EXPECTED = {
    "lite": ("gpt-5.6-terra", "medium", "gpt-5.6-luna", "max", 1,
             {"luna_worker": ("gpt-5.6-luna", "max")}),
    "strict-common": ("gpt-5.6-sol", "xhigh", "gpt-5.6-luna", "max", 4,
           {"luna_worker": ("gpt-5.6-luna", "max")}),
    "private": ("gpt-6-astra", "high", "gpt-5.6-sol", "high", 4,
            {"sol_worker": ("gpt-5.6-sol", "high")}),
    "work": ("gpt-5.6-sol", "xhigh", "gpt-5.6-luna", "max", 4,
                 {"luna_worker": ("gpt-5.6-luna", "max"), "sol_worker": ("gpt-5.6-sol", "high")}),
}
LITE_MODELS = {"gpt-5.6-terra", "gpt-5.6-luna"}
EXPECTED_FEATURES = {
    "multi_agent_v2": {"multi_agent_mode_hint_text": ""},
    "context_management": {"experimental_mode": True},
}
CANONICAL_ALIASES = {f"profile-{name}.toml" for name in manage_roles.ALIASES}


def _catalog_errors(catalog: dict, required: set[tuple[str, str]], exact_slugs: set[str] | None = None) -> list[str]:
    errors: list[str] = []
    models = catalog.get("models") if isinstance(catalog, dict) else None
    if not isinstance(models, list) or not all(isinstance(m, dict) and isinstance(m.get("slug"), str) for m in models):
        return ["Unrecognized metadata: expected models[] with slug; never invent or repair capabilities"]
    index = {m["slug"]: m for m in models}
    if len(index) != len(models):
        errors.append("Duplicate model slugs in metadata")
    if exact_slugs is not None and set(index) != exact_slugs:
        errors.append(f"Catalog must contain exactly: {', '.join(sorted(exact_slugs))}")
    for slug, effort in sorted(required):
        levels = index.get(slug, {}).get("supported_reasoning_levels", [])
        supported = {x.get("effort") for x in levels if isinstance(x, dict)} if isinstance(levels, list) else set()
        if effort not in supported:
            errors.append(f"Model metadata does not confirm {slug} / {effort}")
    return errors


def validate_lite_catalog(catalog: dict) -> list[str]:
    return _catalog_errors(
        catalog,
        {("gpt-5.6-terra", "medium"), ("gpt-5.6-luna", "max")},
        exact_slugs=LITE_MODELS,
    )


def validate(root: Path = ROOT, catalog: dict | None = None, profile: str | None = None) -> list[str]:
    errors, required = [], set()
    if profile is not None and profile not in EXPECTED:
        return [f"Unknown profile: {profile}"]

    def check(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    check((root / "scripts" / "manage_profile.py").is_file(), "unified profile lifecycle manager missing")
    check(set(EXPECTED) == set(manage_roles.PROFILES), "public profile registry drift")
    for legacy_profile in manage_roles.LEGACY_PROFILES:
        check(not (root / legacy_profile).exists(), f"legacy public profile directory remains: {legacy_profile}")

    for p, (model, effort, child, child_eff, cap, roles) in EXPECTED.items():
        config = tomllib.loads((root / p / "config.toml").read_text(encoding="utf-8"))
        check(config.get("model") == model and config.get("model_reasoning_effort") == effort, f"{p}: root pin drift")
        catalog_path = config.get("model_catalog_json")
        if p == "lite":
            normalized = catalog_path.replace("\\", "/") if isinstance(catalog_path, str) else ""
            check(normalized.endswith("/models-lite.json"), "lite: restricted models-lite.json catalog is required")
        else:
            check(catalog_path is None, f"{p}: custom catalog hides root choices")
        check(config.get("features", {}) == EXPECTED_FEATURES,
              f"{p}: profile-managed feature drift (empty multi-agent mode hint + experimental context management required)")
        agents = config.get("agents", {})
        check(agents == {"enabled": True, "max_concurrent_threads_per_session": cap,
                         "default_subagent_model": child, "default_subagent_reasoning_effort": child_eff},
              f"{p}: agent defaults/cap drift")
        check(config.get("memories", {}) == ({} if p == "private" else {
            "extract_model": "gpt-5.6-luna", "consolidation_model": "gpt-5.6-luna"}),
              f"{p}: memory routing drift")
        if profile is None or profile == p:
            required.add((model, effort))
            required.add((child, child_eff))
        actual = {}
        for path in (root / p / "agents").glob("*.toml"):
            role = tomllib.loads(path.read_text(encoding="utf-8"))
            name = role.get("name")
            check(name not in actual, f"{p}: duplicate role {name}")
            actual[name] = (role.get("model"), role.get("model_reasoning_effort"))
            check(bool(role.get("description")) and bool(role.get("developer_instructions")), f"{p}: incomplete role {name}")
            check(role.get("agents", {}).get("enabled") is False, f"{p}: nested delegation enabled")
            if profile is None or profile == p:
                required.add(actual[name])
        check(actual == roles, f"{p}: unexpected/missing worker or effort")
        generated = set(manage_roles.desired_roles(p, root))
        check(CANONICAL_ALIASES.issubset(generated), f"{p}: canonical compatibility aliases missing")
        check(not any(name.startswith("routing-") for name in generated),
              f"{p}: legacy alias exposed as a new install target")

        text = (root / p / "agents-subset.md").read_text(encoding="utf-8")
        stripped = text.strip()
        check(text.count(BEGIN) == 1 and text.count(END) == 1, f"{p}: routing marker drift")
        check(stripped.startswith(BEGIN) and stripped.endswith(END),
              f"{p}: profile instructions exist outside the managed lifecycle block")
        check('fork_turns = "none"' in text, f"{p}: explicit bounded fork policy missing")
        check("SOL_XHIGH_AGENTS_EXPLICITLY_REQUESTED" not in text, f"{p}: stale authorization gate")

        for operation in ("install", "remove"):
            page = (root / p / f"{operation}-{p}.md").read_text(encoding="utf-8")
            check(f"../docs/{operation}.md" in page, f"{p}: {operation} procedure drift")
            check("scripts/manage_profile.py" in page, f"{p}: {operation} does not use unified profile lifecycle")
            check("scripts/manage_roles.py" not in page, f"{p}: {operation} exposes obsolete roles-only lifecycle")

    if catalog is not None:
        errors.extend(_catalog_errors(catalog, required))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--models", type=Path, help="Unmodified JSON from `codex debug models`")
    parser.add_argument("--lite-catalog", type=Path, help="Generated models-lite.json; must contain exactly Terra and Luna")
    parser.add_argument("--profile", choices=sorted(EXPECTED), help="Limit live metadata requirements to one profile")
    args = parser.parse_args()
    try:
        catalog = json.loads(args.models.read_text(encoding="utf-8-sig")) if args.models else None
        errors = validate(catalog=catalog, profile=args.profile)
        if args.lite_catalog:
            lite_catalog = json.loads(args.lite_catalog.read_text(encoding="utf-8-sig"))
            errors.extend(validate_lite_catalog(lite_catalog))
    except (OSError, ValueError, TypeError) as exc:
        parser.exit(1, f"Validation could not complete: {exc}\n")
    if errors:
        print("\n".join(errors))
        return 1
    print("PASS: four static profiles" + (" and supplied model metadata" if catalog or args.lite_catalog else ""))
    print("Not a Codex runtime, account entitlement, quota or model-behavior test.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
