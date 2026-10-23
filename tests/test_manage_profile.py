"""Unified profile/mode lifecycle tests. Never touches the real Codex home."""
from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
import json
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
    def install(self, profile: str, *, mode: str | None = None, dry_run: bool = False):
        return lifecycle.apply(
            self.home,
            profile,
            mode=mode,
            dry_run=dry_run,
        )

    def change_mode(self, mode: str):
        args = ["manage_profile.py", "--home", str(self.home), "mode", mode]
        with patch.object(sys, "argv", args), redirect_stdout(StringIO()):
            self.assertEqual(lifecycle.main(), 0)

    def state(self) -> dict:
        return json.loads(
            (self.home / "profiles" / "roles-state.json").read_text(encoding="utf-8")
        )

    def config(self) -> dict:
        return tomllib.loads((self.home / "config.toml").read_text(encoding="utf-8"))

    def role_names(self) -> set[str]:
        agents = self.home / "agents"
        return {path.name for path in agents.glob("*.toml")} if agents.exists() else set()

    def test_install_collapses_whitespace_before_managed_top_level_block(self):
        self.home.mkdir()
        managed_catalog = (self.home / lifecycle.MANAGED_CATALOG).as_posix()
        (self.home / "config.toml").write_text(
            "mcp_oauth_callback_port = 18000\n"
            "   \n"
            "\t\n"
            "\n"
            "# codex-profiles: managed profile keys\n"
            'model = "gpt-5.6-sol"\n'
            'model_reasoning_effort = "xhigh"\n'
            f'model_catalog_json = "{managed_catalog}"\n'
            "\n",
            encoding="utf-8",
        )

        self.install("work")
        text = (self.home / "config.toml").read_text(encoding="utf-8")

        self.assertIn(
            "mcp_oauth_callback_port = 18000\n\n"
            "# codex-profiles: managed profile keys\n"
            'model = "gpt-6.1-sol"\n'
            'model_reasoning_effort = "xhigh"\n',
            text,
        )
        self.assertNotIn("\n \n", text)
        self.assertNotIn("\n\t\n", text)
        self.assertNotIn("model_catalog_json", text)

        before = text
        self.install("work")
        self.assertEqual(
            before,
            (self.home / "config.toml").read_text(encoding="utf-8"),
        )

    def test_private_and_work_install_default_to_native_solo(self):
        for profile in ("private", "work"):
            with self.subTest(profile=profile), tempfile.TemporaryDirectory() as raw:
                self.home = Path(raw) / "home"
                result = self.install(profile)
                self.assertEqual(result["mode"], "solo")
                self.assertEqual(self.state()["mode"], "solo")
                self.assertEqual(self.state()["owned"], {})
                self.assertEqual(self.role_names(), set())

                config = self.config()
                self.assertNotIn("agents", config)
                self.assertNotIn("multi_agent_v2", config.get("features", {}))
                self.assertNotIn("model_catalog_json", config)
                self.assertIn(f"`{profile}`; agent mode: `solo`", (self.home / "AGENTS.md").read_text())
                for name in ("WORK.md", "PRIVATE.md"):
                    self.assertEqual((self.home / name).is_file(), profile == "work")
                self.assertFalse((self.home / lifecycle.MANAGED_CATALOG).exists())

    def test_private_team_switch_adds_only_explicit_luna_and_sol_roles(self):
        self.install("private")
        self.assertFalse((self.home / lifecycle.MANAGED_CATALOG).exists())

        team = lifecycle.apply(
            self.home,
            "private",
            mode="team",
        )
        self.assertEqual(team["mode"], "team")
        self.assertEqual(
            self.role_names(),
            {"luna-worker.toml", "sol-worker.toml"},
        )
        self.assertEqual(
            self.config()["agents"],
            {"enabled": True, "max_concurrent_threads_per_session": 3},
        )
        self.assertEqual(
            self.config()["features"]["multi_agent_v2"],
            {"multi_agent_mode_hint_text": ""},
        )
        agents_text = (self.home / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("luna_worker", agents_text)
        self.assertIn("sol_worker", agents_text)
        self.assertNotIn("three open child threads", agents_text)
        self.assertIn("Sol-first", agents_text)
        self.assertIn("Independent review only when the user explicitly requests one.", agents_text)
        self.assertNotIn("profile-default", agents_text)
        self.assertFalse((self.home / lifecycle.MANAGED_CATALOG).exists())

        solo = lifecycle.apply(
            self.home,
            "private",
            mode="solo",
        )
        self.assertEqual(solo["mode"], "solo")
        self.assertEqual(self.role_names(), set())
        self.assertIn("agent mode: `solo`", (self.home / "AGENTS.md").read_text())
        self.assertNotIn("agents", self.config())
        self.assertNotIn("multi_agent_v2", self.config().get("features", {}))
        self.assertFalse((self.home / lifecycle.MANAGED_CATALOG).exists())

    def test_work_team_routes_opencode_with_quota_fallbacks(self):
        self.install("work", mode="team")
        text = (self.home / "WORK.md").read_text(encoding="utf-8")
        self.assertIn("work-scout", text)
        self.assertIn("luna_worker", text)
        self.assertIn("work-code", text)
        self.assertNotIn("это личная задача", text)
        self.assertNotIn("sol_worker", text)
        self.assertIn("Use the user-selected root model and effort", text)
        self.assertIn("Cloud quota-exhaustion", text)
        self.assertIn("Independent review only when the user explicitly requests one.", text)
        self.assertEqual(
            self.config()["agents"],
            {"enabled": True, "max_concurrent_threads_per_session": 3},
        )
        self.assertEqual(
            self.role_names(),
            {"luna-worker.toml", "sol-worker.toml"},
        )

    def test_install_team_directly_and_then_switch_profile_defaults_back_to_solo(self):
        self.install("private", mode="team")
        self.assertEqual(self.state()["mode"], "team")
        self.install("work")
        self.assertEqual(self.state()["profile"], "work")
        self.assertEqual(self.state()["mode"], "solo")
        self.assertEqual(self.role_names(), set())

    def test_mode_refresh_preserves_selected_root_and_updates_team_artifacts(self):
        self.install("private", mode="team")
        (self.home / "config.toml").write_text(
            'model = "gpt-6.1-sol"\n'
            'model_reasoning_effort = "high"\n'
            'unrelated_top = "keep"\n'
            '[agents]\n'
            'enabled = true\n'
            'max_concurrent_threads_per_session = 2\n',
            encoding="utf-8",
        )
        worker_path = self.home / "agents" / "sol-worker.toml"
        worker_path.write_bytes(worker_path.read_bytes() + b"# former version\n")
        agents_path = self.home / "AGENTS.md"

        for mode in ("team", "solo", "team"):
            with self.subTest(mode=mode):
                self.change_mode(mode)
                config = self.config()
                self.assertEqual(config["model"], "gpt-6.1-sol")
                self.assertEqual(config["model_reasoning_effort"], "high")
                self.assertEqual(config["unrelated_top"], "keep")
                self.assertEqual(self.state()["mode"], mode)
                if mode == "team":
                    self.assertEqual(
                        config["agents"],
                        {"enabled": True, "max_concurrent_threads_per_session": 3},
                    )
                    self.assertEqual(
                        worker_path.read_bytes(),
                        roles.desired_roles("private", "team")["sol-worker.toml"],
                    )
                    self.assertIn("agent mode: `team`", agents_path.read_text(encoding="utf-8"))
                else:
                    self.assertNotIn("agents", config)
                    self.assertEqual(self.role_names(), set())
                    self.assertIn("agent mode: `solo`", agents_path.read_text(encoding="utf-8"))

    def test_explicit_reinstall_applies_profile_root_defaults(self):
        self.install("private", mode="team")
        config_path = self.home / "config.toml"
        config_path.write_text(
            config_path.read_text(encoding="utf-8")
            .replace('model = "gpt-6-astra"', 'model = "gpt-6.1-sol"')
            .replace('model_reasoning_effort = "xhigh"', 'model_reasoning_effort = "high"'),
            encoding="utf-8",
        )

        self.install("private", mode="team")

        self.assertEqual(self.config()["model"], "gpt-6-astra")
        self.assertEqual(self.config()["model_reasoning_effort"], "xhigh")

    def test_retired_lite_installed_state_switches_to_work(self):
        self.home.mkdir()
        agents = self.home / "agents"
        agents.mkdir()
        data = roles.desired_roles("private", "team")["luna-worker.toml"]
        (agents / "luna-worker.toml").write_bytes(data)
        control = self.home / "profiles"
        control.mkdir()
        (control / "roles-state.json").write_text(
            json.dumps(
                {
                    "version": 2,
                    "profile": "lite",
                    "mode": "team",
                    "owned": {"luna-worker.toml": roles.digest(data)},
                }
            ),
            encoding="utf-8",
        )
        catalog = self.home / lifecycle.MANAGED_CATALOG
        catalog.write_text("synthetic former lite catalog", encoding="utf-8")
        (self.home / lifecycle.LEGACY_LITE_CATALOG).write_text(
            "synthetic legacy catalog", encoding="utf-8"
        )
        (self.home / "config.toml").write_text(
            f'model_catalog_json = "{catalog.as_posix()}"\n'
            'model = "gpt-6-luna"\n',
            encoding="utf-8",
        )
        (self.home / "AGENTS.md").write_text(
            "<!-- codex-profiles:begin -->\n"
            "## Lite — маршрутизация\n"
            "Old lite rules\n"
            "<!-- codex-profiles:end -->\n",
            encoding="utf-8",
        )

        self.assertEqual(lifecycle._state(self.home)["profile"], "lite")
        # Synthetic legacy fixture is explicitly supplied as a known published block.
        legacy_block = lifecycle._extract_marked((self.home / "AGENTS.md").read_text(encoding="utf-8"))
        with patch.object(lifecycle, "_known_instruction_blocks", return_value=[legacy_block]):
            result = self.install("work", mode="team")
        self.assertEqual(result["profile"], "work")
        self.assertEqual(self.state()["profile"], "work")
        self.assertEqual(self.role_names(), {"luna-worker.toml", "sol-worker.toml"})
        self.assertFalse(catalog.exists())
        self.assertFalse((self.home / lifecycle.LEGACY_LITE_CATALOG).exists())
        self.assertNotIn("model_catalog_json", self.config())
        self.assertNotIn("Old lite rules", (self.home / "AGENTS.md").read_text())

    def test_unrelated_custom_catalog_is_refused(self):
        self.home.mkdir()
        custom = self.home / "custom-models.json"
        custom.write_text("{}", encoding="utf-8")
        (self.home / "config.toml").write_text(
            f'model_catalog_json = "{custom.as_posix()}"\n',
            encoding="utf-8",
         )
        with self.assertRaisesRegex(ValueError, "Unrelated model_catalog_json"):
            self.install("private")
        self.assertEqual(
            tomllib.loads((self.home / "config.toml").read_text(encoding="utf-8"))[
                "model_catalog_json"
            ],
            custom.as_posix(),
        )

    def test_legacy_catalogs_and_alias_roles_are_cleaned_on_install(self):
        self.home.mkdir()
        legacy = self.home / "models.json"
        old_lite = self.home / "models-lite.json"
        legacy.write_text("legacy", encoding="utf-8")
        old_lite.write_text("legacy-lite", encoding="utf-8")
        (self.home / "config.toml").write_text(
            f'model_catalog_json = "{legacy.as_posix()}"\n',
            encoding="utf-8",
         )
        agents = self.home / "agents"
        agents.mkdir()
        for name in ("profile-default.toml", "profile-worker.toml", "profile-explorer.toml"):
            (agents / name).write_text('name = "default"\n', encoding="utf-8")

        self.install("private")
        self.assertFalse(legacy.exists())
        self.assertFalse(old_lite.exists())
        self.assertEqual(self.role_names(), set())
        self.assertFalse((self.home / lifecycle.MANAGED_CATALOG).exists())

    def test_remove_cleans_managed_catalog_and_preserves_unrelated_text(self):
        self.home.mkdir()
        (self.home / "config.toml").write_text(
            'unrelated_top = "keep"\n',
            encoding="utf-8",
        )
        (self.home / "AGENTS.md").write_text(
            "# unrelated instructions\n",
            encoding="utf-8",
        )
        self.install("private", mode="team")
        lifecycle.apply(
            self.home,
            None,
        )
        config = tomllib.loads((self.home / "config.toml").read_text(encoding="utf-8"))
        self.assertEqual(config["unrelated_top"], "keep")
        self.assertNotIn("model", config)
        self.assertNotIn("model_catalog_json", config)
        self.assertFalse((self.home / lifecycle.MANAGED_CATALOG).exists())
        self.assertEqual(
            (self.home / "AGENTS.md").read_text(encoding="utf-8").strip(),
            "# unrelated instructions",
        )
        self.assertFalse((self.home / "profiles" / "roles-state.json").exists())

    def test_mode_switch_does_not_require_managed_catalog(self):
        self.install("private")
        self.assertFalse((self.home / lifecycle.MANAGED_CATALOG).exists())
        result = lifecycle.apply(
            self.home,
            "private",
            mode="team",
        )
        self.assertEqual(result["mode"], "team")
        self.assertFalse((self.home / lifecycle.MANAGED_CATALOG).exists())

    def test_dry_run_does_not_write(self):
        result = self.install("private", dry_run=True)
        self.assertEqual(result["mode"], "solo")
        self.assertFalse(self.home.exists())


if __name__ == "__main__":
    unittest.main()
