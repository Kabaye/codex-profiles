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

    def test_live_gui_policy_is_composed_once_in_both_profiles_and_modes(self):
        shared = (ROOT / "shared" / "agents-subset.md").read_text(encoding="utf-8").strip()
        self.assertEqual(shared.count("terra_computer"), 1)
        self.assertIn("Prefer one active worker", shared)
        self.assertIn("at most two delegated jobs", shared)
        for source in ("work/agents-subset.md", "work/personal-agents-subset.md",
                       "private/agents-subset.md"):
            with self.subTest(source=source):
                self.assertNotIn("terra_computer", (ROOT / source).read_text(encoding="utf-8"))

        for mode in ("solo", "team"):
            work = instructions.desired_docs("work", mode)
            private = instructions.desired_docs("private", mode)
            for policy in (work["WORK.md"], work["PRIVATE.md"], private["AGENTS.md"]):
                with self.subTest(mode=mode, policy=policy[:80]):
                    self.assertEqual(policy.count(shared), 1)
                    self.assertEqual(policy.count("terra_computer"), 1)
                    self.assertEqual(policy.count(instructions.BEGIN), 1)
                    self.assertEqual(policy.count(instructions.END), 1)
            self.assertNotIn("terra_computer", work["AGENTS.md"])
            self.assertNotIn("work-code", private["AGENTS.md"])

    def test_work_personal_routing_has_independent_source(self):
        source = (ROOT / "work" / "personal-agents-subset.md").read_text(encoding="utf-8")
        work_personal = instructions.desired_docs("work", "team")["PRIVATE.md"]
        shared = (ROOT / "shared" / "agents-subset.md").read_text(encoding="utf-8").strip()
        self.assertIn("Use `sol_worker`", work_personal)
        self.assertIn("Use `luna_worker`", work_personal)
        self.assertIn(shared, work_personal)
        self.assertNotIn("work-scout", work_personal)
        self.assertNotIn("terra_computer", source)

    def test_shared_fragment_rejects_managed_markers(self):
        from tempfile import TemporaryDirectory
        from unittest.mock import patch
        with TemporaryDirectory() as tmp:
            shared_file = Path(tmp) / "shared" / "agents-subset.md"
            shared_file.parent.mkdir()
            shared_file.write_text(instructions.BEGIN + "\ninvalid", encoding="utf-8")
            with patch.object(instructions, "ROOT", Path(tmp)):
                with self.assertRaisesRegex(ValueError, "Shared agent routing"):
                    instructions.desired_docs("work", "solo")


if __name__ == "__main__":
    unittest.main()
