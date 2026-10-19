"""Keep routing instructions short while retaining model/scope invariants."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
MARKER_START = "<!-- codex-profiles:begin -->"
MARKER_END = "<!-- codex-profiles:end -->"


class CompactRoutingInstructionsTests(unittest.TestCase):
    def test_size_and_markers(self):
        budgets = {
            "strict-common": 2400,
            "private": 1900,
            "work": 2200,
        }
        for profile, limit in budgets.items():
            with self.subTest(profile=profile):
                path = ROOT / profile / "agents-subset.md"
                source = path.read_text(encoding="utf-8")
                self.assertLessEqual(len(path.read_bytes()), limit)
                self.assertTrue(source.startswith(MARKER_START))
                self.assertTrue(source.rstrip().endswith(MARKER_END))
                self.assertEqual(source.count(MARKER_START), 1)
                self.assertEqual(source.count(MARKER_END), 1)
                self.assertIn('fork_turns = "none"', source)

    def test_lite_sources_are_retired(self):
        self.assertFalse((ROOT / "lite").exists())
        self.assertFalse((ROOT / "scripts/filter_lite_catalog.py").exists())

    def test_fixed_profiles_preserve_routing_contracts(self):
        strict = (ROOT / "strict-common/agents-subset.md").read_text(encoding="utf-8")
        for rule in ("GPT-6.1 Sol", "GPT-6 Luna / max", "four open child threads", "DECISION REQUIRED"):
            with self.subTest(profile="strict-common", rule=rule):
                self.assertIn(rule, strict)

    def test_work_and_private_personal_lanes(self):
        work = (ROOT / "work/agents-subset.md").read_text(encoding="utf-8")
        private = (ROOT / "private/agents-subset.md").read_text(encoding="utf-8")
        for rule in ("ordinary work objectives", "это личная задача", "luna_worker", "sol_worker", "Sol-first", "automatic reviewer", "only when the user explicitly requests one"):
            with self.subTest(profile="work", rule=rule):
                self.assertIn(rule, work)
        for rule in ("GPT-6 Astra", "Sol-first", "luna_worker", "sol_worker", "automatic reviewer", "only when the user explicitly requests one"):
            with self.subTest(profile="private", rule=rule):
                self.assertIn(rule, private)


if __name__ == "__main__":
    unittest.main()
