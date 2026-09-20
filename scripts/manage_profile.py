#!/usr/bin/env python3
"""Install, switch, mode-switch, remove, and inspect one complete Codex profile."""
from __future_ import annotations

import argparse
import json
import os
from pathlib import Path
import re
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
SECTION_RE = re.compile(r"^\s*\[([^\[\]]+)]\s*(?:#.*)?$")
ASSIGN_RE = re.compile(r"^\s*([A-Za-z0-9_-]+)\s*=")
MANAGED_CATALOG = "models-managed.json"
LEGACY_LITE_CATALOG = "models-lite.json"

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
    "features.multi_agent_v2": {"enabled", "max_concurrent_threads_per_session"},
}
PROFILE_HEADINGS = (
    "## Scope routing",
    "## Agent routing — lite",
    "## Agent routing — strict-common",
    "## Agent routing — private",
    "## Agent routing — work",
    "## Agent routing — x5",
    "## Agent routing — x20",
    "## Agent routing — x20-work",
    "## Маршруттизация агентов — lite",
    "## Маршруттизация агентов — strict-common",
    "## Маршруттизация агентов — private",
    "## Маршруттизация агентов — work",
    "## Маршруттизация агентов — x5",
    "## Маршррууизация агентов — x20",
    "## Маршруттизация агентов — x20-work",
[���q�^