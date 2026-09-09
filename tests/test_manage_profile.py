"""Unified profile lifecycle tests. Never touches the real Codex home."""
from __future__ import annotations

import itertools
import json
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
        self.models = Path(self.tmp.name) / "models.json"
        self.models.write_text(
            json.dumps(
                {
                    "models": [
                        {
                            "slug": "gpt-5.6-terra",
                            "supported_reasoning_levels": [{"effort": "medium"}],
                        },
                        {
                            "slug": "gpt-5.6-luna",
                            "supported_reasoning_levels": [{"effort": "max"}],
                        },
                    ]
                }
            ),
            encoding="utf-8",
        )

    def install(self, home: Path, profile: str):
        return lifecycle.apply(
            home,
            profile,
            models=self.models if profile == "lite" else None,
        )

    def assert_exact_profile(self, home: Path, profile: str):
        expected = tomllib.loads(
            (lifecycle.ROOT / profile / "config.toml").read_text(encoding="utf-8")
        )
        actual = tomllib.loads((home / "config.toml").read_text(encoding="utf-8"))
        self.assertEqual(actual["model"], expected["model"])
        self.assertEqual(actual["model_reasoning_effort"], expected["model_reasoning_effort"])
        self.assertEqual(actual["agents"], expected["agents"])
        self.assertEqual(actual["features"], expected["features"])
        self.assertEqual(actual.get("memories", {}), expected.get("memories", {}))
        if profile == "lite":
            self.assertEqual(
                actual.get("model_catalog_json"),
                (home / "models-lite.json").as_posix(),
            )
            self.assertTrue((home / "models-lite.json").is_file())
        else:
            self.assertNotIn("model_catalog_json", actual)
            self.assertFalse((home / "models-lite.json").exists())

        self.assertEqual(
            {path.name: path.read_bytes() for path in (home / "agents").glob("*.toml")},
            roles.desired_roles(profile),
        )
        state = json.loads((home / "profiles" / "roles-state.json").read_text())
        self.assertEqual(state["profile"], profile)
        agents_text = (home / "AGENTS.md").read_text(encoding="utf-8").strip()
        source_text = (lifecycle.ROOT / profile / "agents-subset.md").read_text(
            encoding="utf-8"
        ).strip()
        self.assertEqual(agents_text, source_text)

    def test_all_twelve_profile_switches_are_full_replacements(self):
        for before, after in itertools.permutations(lifecycle.PROFILES, 2):
            with self.subTest(before=before, after=after), tempfile.TemporaryDirectory() as tmp:
                home = Path(tmp) / "codex-home"
                self.install(home, before)
                extra = home / "agents" / "sol-advisor.toml"
                extra.write_text('name = "sol_advisor"\n', encoding="utf-8")
                self.install(home, after)
                self.assertFalse(extra.exists())
                self.assert_exact_profile(home, after)

    def test_reinstall_is_a_byte_exact_noop(self):
        self.install(self.home, "work")
        paths = (
            self.home / "config.toml",
            self.home / "AGENTS.md",
            self.home / "profiles" / "roles-state.json",
        )
        before = {path: path.read_bytes() for path in paths}
        before_roles = {
            path.name: path.read_bytes()
            for path in (self.home / "agents").glob("*.toml")
        }

        result = self.install(self.home, "work")

        self.assertEqual(result["files"], [])
        self.assertEqual(result["roles"], [])
        self.assertEqual(before, {path: path.read_bytes() for path in paths})
        self.assertEqual(
            before_roles,
            {
                path.name: path.read_bytes()
                for path in (self.home / "agents").glob("*.toml")
            },
        )

    def test_leaving_lite_reports_and_deletes_its_catalog(self):
        self.install(self.home, "lite")
        catalog = self.home / "models-lite.json"
        self.assertTrue(catalog.is_file())

        preview = lifecycle.apply(self.home, "work", dry_run=True)
        self.assertIn("models-lite.json", preview["files"])
        self.assertTrue(catalog.is_file())

        self.install(self.home, "work")
        self.assertFalse(catalog.exists())
        self.assertNotIn(
            "model_catalog_json",
            tomllib.loads((self.home / "config.toml").read_text(encoding="utf-8")),
        )

    def test_install_replaces_malformed_old_role_manifest(self):
        control = self.home / "profiles"
        control.mkdir(parents=True)
        (control / "roles-state.json").write_text("{broken", encoding="utf-8")
        (self.home / "agents").mkdir()
        (self.home / "agents" / "sol-advisor.toml").write_text(
            'name = "sol_advisor"\n', encoding="utf-8"
        )
        self.install(self.home, "work")

        self.assert_exact_profile(self.home, "work")

    def test_install_removes_all_legacy_profile_artifacts(self):
        legacy_catalog = self.home / "models.json"
        (self.home / "config.toml").write_text(
            f'''model = "gpt-6-astra"
model_reasoning_effort = "high"
model_catalog_json = "{legacy_catalog.as_posix()}"

[features]
multi_agent = true

[features.multi_agent_v2]
enabled = true
max_concurrent_threads_per_session = 2
''',
            encoding="utf-8",
        )
        (self.home / "AGENTS.md").write_text(
            '''<!-- codex-routing-rules:begin -->
## Agent routing — x20
stale routing
<!-- codex-routing-rules:end -->
''',
            encoding="utf-8",
        )
        agents = self.home / "agents"
        agents.mkdir()
        (agents / "astra-worker.toml").write_text('name = "astra_worker"\n')
        (agents / "routing-default.toml").write_text('name = "default"\n')
        legacy_catalog.write_text("legacy catalog\n", encoding="utf-8")
        (self.home / "models-lite.json").write_text("stale lite catalog\n")
        backups = self.home / "routing-rules" / "profile-backups" / "old"
        backups.mkdir(parents=True)
        (backups / "config.toml").write_text("stale backup\n")

        preview = lifecycle.apply(self.home, "work", dry_run=True)
        self.assertIn("models.json", preview["files"])
        self.assertIn("models-lite.json", preview["files"])
        self.assertIn("routing-rules/", preview["files"])

        self.install(self.home, "work")

        self.assert_exact_profile(self.home, "work")
        config = tomllib.loads((self.home / "config.toml").read_text(encoding="utf-8"))
        self.assertNotIn("multi_agent", config["features"])
        self.assertNotIn("enabled", config["features"]["multi_agent_v2"])
        self.assertNotIn(
            "max_concurrent_threads_per_session",
            config["features"]["multi_agent_v2"],
        )
        self.assertFalse(legacy_catalog.exists())
        self.assertFalse((self.home / "models-lite.json").exists())
        self.assertFalse((self.home / "routing-rules").exists())
        installed_agents = (self.home / "AGENTS.md").read_text(encoding="utf-8")
        self.assertNotIn("codex-routing-rules", installed_agents)
        self.assertNotIn("Agent routing — x20", installed_agents)

        with_trailing_instructions = lifecycle.build_agents(
            f'''{lifecycle.LEGACY_BEGIN}
## Agent routing — x20
stale routing
{lifecycle.LEGACY_END}

keep trailing unrelated instructions
''',
            "work",
        )
        self.assertNotIn("stale routing", with_trailing_instructions)
        self.assertIn("keep trailing unrelated instructions", with_trailing_instructions)

        with self.assertRaisesRegex(ValueError, "no matching end"):
            lifecycle.build_agents(
                f'''{lifecycle.LEGACY_BEGIN}
stale routing
keep ambiguous trailing instructions
''',
                "work",
            )

        scalar_legacy = tomllib.loads(
            lifecycle.build_config(
                "[features]\nmulti_agent_v2 = true\n",
                "work",
                self.home,
            )
        )
        self.assertEqual(
            scalar_legacy["features"]["multi_agent_v2"],
            {"multi_agent_mode_hint_text": ""},
        )

    def test_switch_and_remove_are_complete_and_install_replaces_all_roles(self):
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

        first = self.install(self.home, "work")
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
        self.assertFalse(advisor.exists())

        second = self.install(self.home, "private")
        self.assertEqual(second["profile"], "private")
        self.assertNotIn("backup", second)
        config = tomllib.loads((self.home / "config.toml").read_text(encoding="utf-8"))
        self.assertEqual(config["model"], "gpt-6-astra")
        self.assertEqual(config["model_reasoning_effort"], "high")
        self.assertNotIn("extract_model", config.get("memories", {}))
        self.assertEqual(config["agents"]["default_subagent_model"], "gpt-5.6-sol")
        self.assertEqual(config["agents"]["unrelated_agent_setting"], "keep")
        self.assertFalse(advisor.exists())
        self.assertEqual(
            {p.name for p in (self.home / "agents").glob("*.toml")},
            set(roles.desired_roles("private")),
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
        self.assertEqual(
            {p.name for p in (self.home / "agents").glob("*.toml")},
            set(),
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
