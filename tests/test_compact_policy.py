"""Keep routing instructions short while retaining model/scope invariants."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
MARKER_START = "<!-- codex-profiles:begin -->"
MARKER_END = "<!-- codex-profiles:end -->"


class CompactRoutingInstructionsTests(unittest.TestCase):
    def test_size_and_markers(self):
        budgets = {
            "private": 1900,
            "work": 3000,
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

    def test_work_and_private_routes(self):
        work = (ROOT / "work/agents-subset.md").read_text(encoding="utf-8")
        private = (ROOT / "private/agents-subset.md").read_text(encoding="utf-8")
        common_rules = (
            "Use the user-selected root model and effort",
            "luna_worker",
            "Independent review only when the user explicitly requests one.",
            "solo",
            "team",
            "no nested delegation",
        )
        for profile, source in (("private", private), ("work", work)):
            for rule in common_rules:
                with self.subTest(profile=profile, rule=rule):
                    self.assertIn(rule, source)
        for rule in ("work-scout", "work-code", "corp-code-fast", "corp-chat-max", "litellm/global.openai.gpt-6-luna", "Cursor", "quota"):
            with self.subTest(profile="work", rule=rule):
                self.assertIn(rule, work)
        self.assertIn("Sol-first", private)
        self.assertIn("sol_worker", private)
        self.assertNotIn("three", private)
        self.assertNotIn("private", work.lower())
        self.assertNotIn("personal", work.lower())
        self.assertNotIn("это личная задача", work)
        self.assertIn('opencode run --dir "REPO_PATH" --agent work-code --model litellm/global.openai.gpt-6-luna --format json "BOUNDED_TASK"', work)
        self.assertIn("installed Cursor CLI", work)
        self.assertIn("without wrappers", work)


if __name__ == "__main__":
    unittest.main()
