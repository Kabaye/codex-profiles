#!/usr/bin/env python3
"""Static preset checks; optionally validate against unmodified live model metadata."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import tomllib

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {
    "lite": (None, None, "gpt-5.6-luna", "max", 1, {"luna_worker": ("gpt-5.6-luna", "max")}),
    "x5": ("gpt-5.6-sol", "xhigh", "gpt-5.6-luna", "max", 2, {"luna_worker": ("gpt-5.6-luna", "max")}),
    "x20": ("gpt-6-astra", "medium", "gpt-5.6-sol", "high", 2,
            {"sol_worker": ("gpt-5.6-sol", "high"), "astra_worker": ("gpt-6-astra", "high")}),
    "x20-work": ("gpt-5.6-sol", "xhigh", "gpt-5.6-luna", "max", 2, {"luna_worker": ("gpt-5.6-luna", "max")}),
}


def validate(root: Path = ROOT, catalog: dict | None = None, profile: str | None = None) -> list[str]:
    errors, required = [], set()
    if profile is not None and profile not in EXPECTED:
        return [f"Unknown profile: {profile}"]
    def check(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)
    for p, (model, effort, child, child_eff, cap, roles) in EXPECTED.items():
        config = tomllib.loads((root / p / "config.toml").read_text(encoding="utf-8"))
        check(config.get("model") == model and config.get("model_reasoning_effort") == effort, f"{p}: root pin drift")
        check("model_catalog_json" not in config, f"{p}: custom catalog hides root choices")
        check("features" not in config, f"{p}: legacy/experimental feature overrides")
        agents = config.get("agents", {})
        check(agents == {"enabled": True, "max_concurrent_threads_per_session": cap,
                         "default_subagent_model": child, "default_subagent_reasoning_effort": child_eff}, f"{p}: agent defaults/cap drift")
        check(config.get("memories", {}) == ({} if p == "x20" else {
            "extract_model": "gpt-5.6-luna", "consolidation_model": "gpt-5.6-luna"}), f"{p}: memory routing drift")
        if profile is None or profile == p:
            if model:
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
        text = (root / p / "agents-subset.md").read_text(encoding="utf-8")
        check(text.count("<!-- codex-routing-rules:begin -->") == 1 and
              text.count("<!-- codex-routing-rules:end -->") == 1, f"{p}: routing marker drift")
        check('fork_turns = "none"' in text, f"{p}: explicit bounded fork policy missing")
        check("SOL_XHIGH_AGENTS_EXPLICITLY_REQUESTED" not in text, f"{p}: stale authorization gate")
        for operation in ("install", "remove"):
            text = (root / p / f"{operation}-{p}.md").read_text(encoding="utf-8")
            check(f"../docs/{operation}.md" in text, f"{p}: {operation} procedure drift")
    if catalog is not None:
        models = catalog.get("models") if isinstance(catalog, dict) else None
        if not isinstance(models, list) or not all(isinstance(m, dict) and isinstance(m.get("slug"), str) for m in models):
            errors.append("Unrecognized metadata: expected models[] with slug; never invent or repair capabilities")
        else:
            index = {m["slug"]: m for m in models}
            check(len(index) == len(models), "Duplicate model slugs in metadata")
            for slug, effort in sorted(required):
                levels = index.get(slug, {}).get("supported_reasoning_levels", [])
                supported = {x.get("effort") for x in levels if isinstance(x, dict)} if isinstance(levels, list) else set()
                check(effort in supported, f"Live metadata does not confirm {slug} / {effort}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--models", type=Path, help="JSON from unmodified codex debug models")
    parser.add_argument("--profile", choices=sorted(EXPECTED), help="Limit live metadata requirements to one profile")
    args = parser.parse_args()
    try:
        catalog = json.loads(args.models.read_text(encoding="utf-8-sig")) if args.models else None
        errors = validate(catalog=catalog, profile=args.profile)
    except (OSError, ValueError, TypeError) as exc:
        parser.exit(1, f"Validation could not complete: {exc}\n")
    if errors:
        print("\n".join(errors))
        return 1
    print("PASS: four static profiles" + (" and supplied model/effort metadata" if catalog else ""))
    print("Not a Codex runtime, account entitlement, quota or model-behavior test.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
