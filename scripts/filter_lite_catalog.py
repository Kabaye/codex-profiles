#!/usr/bin/env python3
"""Create the lite model catalog by filtering real Codex model metadata."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ALLOWED = ("gpt-5.6-terra", "gpt-5.6-luna")
REQUIRED_EFFORT = {
    "gpt-5.6-terra": "medium",
    "gpt-5.6-luna": "max",
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Unmodified JSON output captured from `codex debug models`")
    parser.add_argument("output", type=Path, help="Destination models-lite.json")
    args = parser.parse_args()

    catalog = json.loads(args.input.read_text(encoding="utf-8-sig"))
    models = catalog.get("models") if isinstance(catalog, dict) else None
    if not isinstance(models, list):
        parser.exit(1, "Expected a JSON object with models[].\n")

    by_slug = {}
    for model in models:
        if not isinstance(model, dict) or not isinstance(model.get("slug"), str):
            parser.exit(1, "Unrecognized model metadata; refusing to manufacture entries.\n")
        slug = model["slug"]
        if slug in by_slug:
            parser.exit(1, f"Duplicate model slug in source catalog: {slug}\n")
        by_slug[slug] = model

    filtered = []
    for slug in ALLOWED:
        model = by_slug.get(slug)
        if model is None:
            parser.exit(1, f"Required lite model is unavailable: {slug}\n")
        levels = model.get("supported_reasoning_levels")
        supported = {
            level.get("effort")
            for level in levels
            if isinstance(level, dict)
        } if isinstance(levels, list) else set()
        effort = REQUIRED_EFFORT[slug]
        if effort not in supported:
            parser.exit(1, f"Source metadata does not confirm {slug} / {effort}\n")
        filtered.append(model)

    # Preserve the source catalog and model records exactly; only remove unwanted models.
    catalog["models"] = filtered
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {args.output} with: {', '.join(ALLOWED)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
