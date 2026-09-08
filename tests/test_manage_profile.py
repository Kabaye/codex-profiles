"""Unified profile lifecycle tests. Never touches the real Codex home."""
from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import tomllib
import unittest
from unittest.mock import patch

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

        first = lifecycle.apply(self.home, "x20-work")
        self.assertEqual(first["profile"], "x20-work")
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

        second = lifecycle.apply(self.home, "x20")
        self.assertEqual(second["profile"], "x20")
        config = tomllib.loads((self.home / "config.toml").read_text(encoding="utf-8"))
        self.assertEqual(config["model"], "gpt-6-astra")
        self.assertEqual(config["model_reasoning_effort"], "high")
        self.assertNotIn("extract_model", config.get("memories", {}))
        self.assertEqual(config["agents"]["default_subagent_model"], "gpt-5.6-sol")
        self.assertEqual(config["agents"]["unrelated_agent_setting"], "keep")
        self.assertTrue(advisor.exists())
        self.assertEqual(
            {p.name for p in (self.home / "agents").glob("*.toml")},
            set(roles.desired_roles("x20")) | {"sol-advisor.toml"},
        )
        agents_text = (self.home / "AGENTS.md").read_text(encoding="utf-8")
        self.assertEqual(agents_text.count(lifecycle.BEGIN), 1)
        self.assertEqual(agents_text.count(lifecycle.END), 1)
        self.assertIn("Agent routing — x20", agents_text)
        self.assertNotIn("Agent routing — x20-work", agents_text)
        self.assertIn("# My unrelated instructions", agents_text)

        removed = lifecycle.apply(self.home, None)
        self.assertIsNone(removed["profile"])
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

    def test_legacy_config_is_replaced_not_stacked(self):
        legacy = '''model = "gpt-5.6-sol"
model_reasoning_effort = "high"
model_catalog_json = "C:/Users/test/.codex/models.json"

[agents]
enabled = true
max_concurrent_threads_per_session = 2
default_subagent_model = "gpt-5.6-luna"
default_subagent_reasoning_effort = "max"
unrelated = "keep"

[features]
multi_agent = true
unrelated = true

[features.multi_agent_v2]
enabled = true
max_concurrent_threads_per_session = 2
multi_agent_mode_hint_text = "old"
tool_namespace = "keep"

[memories]
extract_model = "gpt-5.6-luna"
consolidation_model = "gpt-5.6-luna"
unrelated = "keep"
'''
        home = Path("C:/Users/test/.codex")
        result = lifecycle.build_config(legacy, "x20-work", home)
        parsed = tomllib.loads(result)
        self.assertEqual(parsed["model"], "gpt-5.6-sol")
        self.assertEqual(parsed["model_reasoning_effort"], "xhigh")
        self.assertNotIn("model_catalog_json", parsed)
        self.assertNotIn("multi_agent", parsed["features"])
        self.assertNotIn("enabled", parsed["features"]["multi_agent_v2"])
        self.assertNotIn("max_concurrent_threads_per_session", parsed["features"]["multi_agent_v2"])
        self.assertEqual(parsed["features"]["multi_agent_v2"]["multi_agent_mode_hint_text"], "")
        self.assertEqual(parsed["features"]["multi_agent_v2"]["tool_namespace"], "keep")
        self.assertEqual(parsed["agents"]["unrelated"], "keep")
        self.assertEqual(parsed["memories"]["unrelated"], "keep")

    def test_unrelated_custom_catalog_is_not_deleted_as_legacy(self):
        with self.assertRaisesRegex(ValueError, "Unrelated model_catalog_json"):
            lifecycle.build_config(
                'model_catalog_json = "D:/company/custom-models.json"\n',
                "x20",
                self.home,
            )

    def test_exact_legacy_role_can_be_removed_without_an_install_manifest(self):
        raw = b'name = "sol_worker"\nmodel = "legacy-fixture"\n'
        (self.home / "agents").mkdir()
        target = self.home / "agents" / "sol-worker.toml"
        target.write_bytes(raw)
        with patch.dict(roles.LEGACY, {"sol-worker.toml": {roles.git_blob(raw)}}):
            result = roles.manage(self.home, None, adopt_legacy=True)
        self.assertIn("sol-worker.toml", result["changed_roles"])
        self.assertFalse(target.exists())

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
