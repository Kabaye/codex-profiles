"""Terra's global GUI role and independent per-installation routing sources."""
from __future__ import annotations

from pathlib import Path
import sys
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import manage_instructions as instructions
import manage_roles as roles


class TerraComputerRoutingTests(unittest.TestCase):
    def test_shared_role_in_both_profiles_and_modes(self):
        for profile in ("work", "private"):
            for mode in ("solo", "team"):
                with self.subTest(profile=profile, mode=mode):
                    selected = roles.desired_roles(profile, mode)
                    expected = {"terra-computer.toml"}
                    if mode == "team":
                        expected |= {"luna-worker.toml", "sol-worker.toml"}
                    self.assertEqual(set(selected), expected)
                    terra = tomllib.loads(selected["terra-computer.toml"].decode("utf-8"))
                    self.assertEqual(terra["name"], "terra_computer")
                    self.assertEqual(terra["model"], "gpt-6.1-terra")
                    self.assertEqual(terra["model_reasoning_effort"], "medium")
                    self.assertIs(terra["agents"]["enabled"], False)

    def test_live_gui_policy_in_both_installations(self):
        work = instructions.desired_docs("work", "solo")
        private = instructions.desired_docs("private", "solo")
        self.assertIn("terra_computer", work["WORK.md"])
        self.assertIn("terra_computer", work["PRIVATE.md"])
        self.assertIn("terra_computer", private["AGENTS.md"])
        self.assertNotIn("work-code", private["AGENTS.md"])

    def test_work_personal_routing_has_independent_source(self):
        expected = instructions.block(
            (ROOT / "work" / "personal-agents-subset.md").read_text(encoding="utf-8")
        )
        work_personal = instructions.desired_docs("work", "team")["PRIVATE.md"]
        self.assertEqual(work_personal, expected)
        self.assertIsNotNone(work_personal)
        self.assertNotIn("work-scout", work_personal)


if __name__ == "__main__":
    unittest.main()
