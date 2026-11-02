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

    def test_shared_policy_is_composed_once_in_both_profiles_and_modes(self):
        shared = (ROOT / "shared" / "AGENTS.md").read_text(encoding="utf-8").strip()
        self.assertNotIn("terra_computer", shared)
        self.assertIn("prefer one active worker", shared)
        self.assertIn("at most two delegated jobs", shared)
        for source in ("profiles/private/AGENTS.md", "profiles/work/AGENTS.md", "modes/solo/AGENTS.md", "modes/team/AGENTS.md"):
            with self.subTest(source=source):
                self.assertNotIn("terra_computer", (ROOT / source).read_text(encoding="utf-8"))

        for mode in ("solo", "team"):
            work = instructions.desired_docs("work", mode)
            private = instructions.desired_docs("private", mode)
            for policy in (work["AGENTS.md"], private["AGENTS.md"]):
                with self.subTest(mode=mode, policy=policy[:80]):
                    self.assertEqual(policy.count(shared), 1)
                    self.assertNotIn("terra_computer", policy)
                    self.assertEqual(policy.count(instructions.BEGIN), 1)
                    self.assertEqual(policy.count(instructions.END), 1)
            self.assertNotIn("work-code", private["AGENTS.md"])
            for docs in (work, private):
                self.assertIsNone(docs["WORK.md"])
                self.assertIsNone(docs["PRIVATE.md"])

    def test_work_native_routing_uses_generic_team_source(self):
        source = (ROOT / "modes" / "team" / "AGENTS.md").read_text(encoding="utf-8")
        work_policy = instructions.desired_docs("work", "team")["AGENTS.md"]
        shared = (ROOT / "shared" / "AGENTS.md").read_text(encoding="utf-8").strip()
        self.assertIn(source.strip(), work_policy)
        self.assertIn("`sol_worker` for", work_policy)
        self.assertIn("`luna_worker` for", work_policy)
        self.assertIn(shared, work_policy)
        self.assertIn("work-scout", work_policy)
        self.assertNotIn("work-scout", source)
        self.assertNotIn("terra_computer", source)

    def test_shared_fragment_rejects_managed_markers(self):
        from tempfile import TemporaryDirectory
        from unittest.mock import patch
        with TemporaryDirectory() as tmp:
            shared_file = Path(tmp) / "shared" / "AGENTS.md"
            shared_file.parent.mkdir()
            shared_file.write_text(instructions.BEGIN + "\ninvalid", encoding="utf-8")
            data = profile_sources.load(ROOT)
            data["profiles"] = {"work": {"solo": {"config": [], "roles": [], "instructions": {"AGENTS.md": ["shared/AGENTS.md"]}}}}
            import json
            (Path(tmp) / "manifest.json").write_text(json.dumps(data), encoding="utf-8")
            with patch.object(instructions, "ROOT", Path(tmp)):
                with self.assertRaisesRegex(ValueError, "unmarked fragments"):
                    instructions.desired_docs("work", "solo")


if __name__ == "__main__":
    unittest.main()
