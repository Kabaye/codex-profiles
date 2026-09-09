"""Unified profile lifecycle tests. Never touches the real Codex home."""
from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import tomllib
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import manage_profile as lifecycle
import manage_roles as roles


class UnifiedProfileLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name) / "codex-home"
        self.home.mkdir()

    def test_switch_and_remove_are_complete_but_preserve_unrelated_state(self):
        (self.home / "agents").mkdir()
        advisor = self.home / "agents" / "sol-advisor.toml"
        advisor.write_text('name = "sol_advisor"\n', encoding="utf-8")
        (self.home / "config.toml").write_text(
            'unrelated_top = "keep"\n'
            '\n'
            '[agents]\n'
            'unrelated_agent_setting = "keep"\n'
            '\n'
            '[features]\n'
            'unrelated_feature = true\n',
            encoding="utf-8",
        )
        (self.home / "AGENTS.md").write_text("# My unrelated instructions\n", encoding="utf-8")

        first = lifecycle.apply(self.home, "work")
        self.assertEqual(first["profile"], "work")
        self.assertNotIn("backup", first)
        config = tomllib.loads((self.home / "config.toml").read_text(encoding="utf-8"))
        self.assertEqual(config["model"], "gpt-5.6-sol")
        self.assertEqual(config["model_reasoning_effort"], "xhigh")
        self.assertEqual(config["unrelated_top"], "keep")
        self.assertEqual(config["agents"]["unrelated_agent_setting"], "keep")
        self.assertTrue(config["features"]["unrelated_feature"])
        self.assertEqual(
            config["features"]["multi_agent_v2"],
            {"multi_agent_mode_hint_text": ""},
        )
        self.assertTrue(advisor.exists())

        second = lifecycle.apply(self.home, "private")
        self.assertEqual(second["profile"], "private")
        self.assertNotIn("backup", second)
        config = tomllib.loads((self.home / "config.toml").read_text(encoding="utf-8"))
        self.assertEqual(config["model"], "gpt-6-astra")
        self.assertEqual(config["model_reasoning_effort"], "high")
        self.assertNotIn("extract_model", config.get("memories", {}))
        self.assertEqual(config["agents"]["default_subagent_model"], "gpt-5.6-sol")
        self.assertEqual(config["agents"]["unrelated_agent_setting"], "keep")
        self.assertTrue(advisor.exists())
        self.assertEqual(
            {p.name for p in (self.home / "agents").glob("*.toml")},
            set(roles.desired_roles("private")) | {"sol-advisor.toml"},
        )
        agents_text = (self.home / "AGENTS.md").read_text(encoding="utf-8")
        self.assertEqual(agents_text.count(lifecycle.BEGIN), 1)
        self.assertEqual(agents_text.count(lifecycle.END), 1)
        self.assertIn("Agent routing — private", agents_text)
        self.assertNotIn("Agent routing — work", agents_text)
        self.assertIn("# My unrelated instructions", agents_text)

        removed = lifecycle.apply(self.home, None)
        self.assertIsNone(removed["profile"])
        self.assertNotIn("backup", removed)
        config = tomllib.loads((self.home / "config.toml").read_text(encoding="utf-8"))
        self.assertNotIn("model", config)
        self.assertNotIn("model_reasoning_effort", config)
        self.assertEqual(config["unrelated_top"], "keep")
        self.assertEqual(config["agents"], {"unrelated_agent_setting": "keep"})
        self.assertTrue(config["features"]["unrelated_feature"])
        self.assertEqual(config["features"].get("multi_agent_v2", {}), {})
        self.assertTrue(advisor.exists())
        self.assertEqual(
            {p.name for p in (self.home / "agents").glob("*.toml")},
            {"sol-advisor.toml"},
        )
        self.assertEqual(
            (self.home / "AGENTS.md").read_text(encoding="utf-8"),
            "# My unrelated instructions\n",
        )
        self.assertFalse((self.home / "profiles" / "profile-backups").exists())
        self.assertFalse((self.home / "profiles" / "backups").exists())

    def test_empty_remove_does_not_create_empty_config_or_agents_files(self):
        removed = lifecycle.apply(self.home, None)
        self.assertEqual(removed["files"], [])
        self.assertEqual(removed["roles"], [])
        self.assertFalse((self.home / "config.toml").exists())
        self.assertFalse((self.home / "AGENTS.md").exists())
        self.assertFalse((self.home / "profiles" / "profile-backups").exists())
        self.assertFalse((self.home / "profiles" / "backups").exists())

    def test_current_config_is_replaced_not_stacked(self):
        current = '''# codex-profiles: managed profile keys
model = "gpt-5.6-sol"
model_reasoning_effort = "xhigh"

[agents]
enabled = true
max_concurrent_threads_per_session = 4
default_subagent_model = "gpt-5.6-luna"
default_subagent_reasoning_effort = "max"
unrelated = "keep"

[features]
unrelated = true

[features.multi_agent_v2]
multi_agent_mode_hint_text = ""
tool_namespace = "keep"

[memories]
extract_model = "gpt-5.6-luna"
consolidation_model = "gpt-5.6-luna"
unrelated = "keep"
'''
        home = Path("C:/Users/test/.codex")
        result = lifecycle.build_config(current, "private", home)
        parsed = tomllib.loads(result)
        self.assertEqual(parsed["model"], "gpt-6-astra")
        self.assertEqual(parsed["model_reasoning_effort"], "high")
        self.assertNotIn("model_catalog_json", parsed)
        self.assertEqual(parsed["features"]["multi_agent_v2"]["multi_agent_mode_hint_text"], "")
        self.assertEqual(parsed["features"]["multi_agent_v2"]["tool_namespace"], "keep")
        self.assertEqual(parsed["agents"]["unrelated"], "keep")
        self.assertEqual(parsed["memories"]["unrelated"], "keep")

    def test_unrelated_custom_catalog_is_preserved(self):
        with self.assertRaisesRegex(ValueError, "Unrelated model_catalog_json"):
            lifecycle.build_config(
                'model_catalog_json = "D:/company/custom-models.json"\n',
                "private",
                self.home,
            )

    def test_lite_entire_instruction_file_is_profile_owned(self):
        text = (lifecycle.ROOT / "lite" / "agents-subset.md").read_text(encoding="utf-8").strip()
        self.assertTrue(text.startswith(lifecycle.BEGIN))
        self.assertTrue(text.endswith(lifecycle.END))
        self.assertEqual(text.count(lifecycle.BEGIN), 1)
        self.assertEqual(text.count(lifecycle.END), 1)

    def test_profile_pages_use_only_unified_lifecycle(self):
        for profile in lifecycle.PROFILES:
            for operation in ("install", "remove"):
                with self.subTest(profile=profile, operation=operation):
                    page = lifecycle.ROOT / profile / f"{operation}-{profile}.md"
                    text = page.read_text(encoding="utf-8")
                    self.assertIn("scripts/manage_profile.py", text)
                    self.assertNotIn("scripts/manage_roles.py", text)


if __name__ == "__main__":
    unittest.main()
