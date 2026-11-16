"""Composed native profile/mode routing stays independent of universal config."""
from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import manage_instructions as instructions
import manage_roles as roles
import profile_sources


class ProfileRoutingTests(unittest.TestCase):
    def test_only_native_workers_are_selected_by_mode(self):
        for profile in ("work", "private"):
            for mode in ("solo", "team"):
                with self.subTest(profile=profile, mode=mode):
                    selected = roles.desired_roles(profile, mode)
                    expected = set()
                    if mode == "team":
                        expected |= {"luna-worker.toml", "sol-worker.toml"}
                    self.assertEqual(set(selected), expected)

    def test_native_delegation_policy_is_selected_only_in_team(self):
        team = (ROOT / "modes" / "team" / "AGENTS.md").read_text(encoding="utf-8").strip()
        self.assertFalse((ROOT / "shared" / "AGENTS.md").exists())
        team_rules = (
            "prefer one active worker", "at most two delegated jobs",
            "Use English for all subagent", "sol_worker", "luna_worker", "fork_turns",
            "Workers complete their assignment", "Independent review only",
        )
        for source in ("profiles/private/AGENTS.md", "profiles/work/AGENTS.md", "modes/solo/AGENTS.md", "modes/team/AGENTS.md"):
            with self.subTest(source=source):
                self.assertNotIn("terra_computer", (ROOT / source).read_text(encoding="utf-8"))

        for mode in ("solo", "team"):
            work = instructions.desired_docs("work", mode)
            private = instructions.desired_docs("private", mode)
            for policy in (work["AGENTS.md"], private["AGENTS.md"]):
                with self.subTest(mode=mode, policy=policy[:80]):
                    if mode == "team":
                        self.assertEqual(policy.count(team), 1)
                    for rule in team_rules:
                        self.assertEqual(rule in policy, mode == "team", rule)
                    self.assertNotIn("terra_computer", policy)
                    self.assertEqual(policy.count(instructions.BEGIN), 1)
                    self.assertEqual(policy.count(instructions.END), 1)
            self.assertNotIn("work-code", private["AGENTS.md"])
            for docs in (work, private):
                self.assertIsNone(docs["WORK.md"])
                self.assertIsNone(docs["PRIVATE.md"])

    def test_team_selects_profile_specific_primary_work_instruction(self):
        private_rule = "- Do the main work yourself."
        native_scope = "- On the native Codex route only (fallback for work tasks), do the main work yourself."
        for profile in ("work", "private"):
            for mode in ("solo", "team"):
                with self.subTest(profile=profile, mode=mode):
                    policy = instructions.desired_docs(profile, mode)["AGENTS.md"]
                    self.assertEqual(policy.count(private_rule), int(profile == "private" and mode == "team"))
                    self.assertEqual(policy.count(native_scope), int(profile == "work" and mode == "team"))

    def test_work_native_routing_preserves_corporate_and_common_team_rules(self):
        source = (ROOT / "modes" / "team" / "AGENTS.md").read_text(encoding="utf-8")
        work_policy = instructions.desired_docs("work", "team")["AGENTS.md"]
        self.assertIn(source.strip(), work_policy)
        self.assertIn("`sol_worker` for", work_policy)
        self.assertIn("`luna_worker` for", work_policy)
        self.assertEqual(work_policy.count("at most two delegated jobs"), 1)
        self.assertEqual(work_policy.count("Use English for all subagent"), 1)
        self.assertIn("work-scout", work_policy)
        self.assertIn("are equal primary routes", work_policy)
        self.assertIn("Only explicit quota exhaustion from the selected primary route permits fallback", work_policy)
        self.assertNotIn("work-scout", source)
        self.assertNotIn("terra_computer", source)

    def test_manifest_fragment_rejects_managed_markers(self):
        from tempfile import TemporaryDirectory
        from unittest.mock import patch
        with TemporaryDirectory() as tmp:
            fragment = Path(tmp) / "fragments" / "rules.md"
            fragment.parent.mkdir()
            fragment.write_text(instructions.BEGIN + "\ninvalid", encoding="utf-8")
            data = profile_sources.load(ROOT)
            data["profiles"] = {"work": {"solo": {"config": [], "roles": [], "instructions": {"AGENTS.md": ["fragments/rules.md"]}}}}
            import json
            (Path(tmp) / "manifest.json").write_text(json.dumps(data), encoding="utf-8")
            with patch.object(instructions, "ROOT", Path(tmp)):
                with self.assertRaisesRegex(ValueError, "unmarked fragments"):
                    instructions.desired_docs("work", "solo")


if __name__ == "__main__":
    unittest.main()
