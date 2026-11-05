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
import profile_sources


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
        agents = self.home / "agents" / "codex-profiles"
        return {path.name for path in agents.glob("*.toml")} if agents.exists() else set()

    def test_private_and_work_install_default_to_native_solo(self):
        for profile in ("private", "work"):
            with self.subTest(profile=profile), tempfile.TemporaryDirectory() as raw:
                self.home = Path(raw) / "home"
                result = self.install(profile)
                self.assertEqual(result["mode"], "solo")
                self.assertEqual(self.state()["mode"], "solo")
                self.assertEqual(set(self.state()["owned"]), set())
                self.assertEqual(self.role_names(), set())

                config = self.config()
                self.assertNotIn("agents", config)
                self.assertNotIn("multi_agent_v2", config.get("features", {}))
                self.assertNotIn("model_catalog_json", config)
                agents_text = (self.home / "AGENTS.md").read_text()
                self.assertIn(f"Active root profile: `{profile}`.", agents_text)
                self.assertNotIn("sol_worker", agents_text)
                self.assertNotIn("agent mode:", agents_text)
                for name in ("WORK.md", "PRIVATE.md"):
                    self.assertFalse((self.home / name).is_file())
                self.assertEqual("work-code" in agents_text, profile == "work")
                self.assertEqual("work-scout" in agents_text, profile == "work")
                self.assertFalse((self.home / lifecycle.MANAGED_CATALOG).exists())

    def test_private_team_switch_adds_only_luna_and_sol_roles(self):
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
            {"enabled": True, "max_concurrent_threads_per_session": 2},
        )
        self.assertEqual(
            self.config()["features"]["multi_agent_v2"],
            {"multi_agent_mode_hint_text": ""},
        )
        agents_text = (self.home / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("luna_worker", agents_text)
        self.assertIn("sol_worker", agents_text)
        self.assertNotIn("three open child threads", agents_text)
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
        self.assertNotIn("sol_worker", (self.home / "AGENTS.md").read_text())
        self.assertNotIn("agents", self.config())
        self.assertNotIn("multi_agent_v2", self.config().get("features", {}))
        self.assertFalse((self.home / lifecycle.MANAGED_CATALOG).exists())

    def test_work_both_modes_keep_corporate_route_and_only_team_adds_native_workers(self):
        for mode in ("solo", "team"):
            with self.subTest(mode=mode):
                self.home = Path(self.tmp.name) / mode
                self.install("work", mode=mode)
                text = (self.home / "AGENTS.md").read_text(encoding="utf-8")
                self.assertIn("OpenCode `work-code`", text)
                self.assertIn("Cursor Auto Cost are equal primary routes", text)
                self.assertIn("--model litellm/global.openai.gpt-6-luna", text)
                self.assertIn('cursor-agent --workspace "REPO_PATH" --model "auto-smart[optimize_for=cost]"', text)
                self.assertIn("Use read-only OpenCode `work-scout` with `--model litellm/corp-code-fast`", text)
                self.assertIn("scouting is optional", text)
                self.assertIn("Root handles deeper flow/contract analysis", text)
                self.assertNotIn("corp-chat-max", text)
                self.assertNotIn("implementation requires an explicit user request", text)
                self.assertIn("Use the user-selected root model and effort", text)
                self.assertIn("Only explicit quota exhaustion from the selected primary route permits fallback to native Codex under its native delegation instructions", text)
                self.assertIn("Initial Cursor selection requires no quota exhaustion", text)
                self.assertIn("Authentication, network, tool, context and validation failures are not quota", text)
                self.assertIn("Independent review only when the user explicitly requests one.", text)
                self.assertEqual("luna_worker" in text, mode == "team")
                self.assertEqual("sol_worker" in text, mode == "team")
                if mode == "team":
                    self.assertEqual(self.config()["agents"], {"enabled": True, "max_concurrent_threads_per_session": 2})
                    self.assertEqual(self.role_names(), {"luna-worker.toml", "sol-worker.toml"})
                else:
                    self.assertNotIn("agents", self.config())
                    self.assertEqual(self.role_names(), set())

    def test_mode_refresh_preserves_selected_root_and_updates_team_artifacts(self):
        self.install("private", mode="team")
        (self.home / "config.toml").write_text(
            'model = "gpt-6.1-sol"\n'
            'model_reasoning_effort = "high"\n'
            'unrelated_top = "keep"\n'
            '[agents]\n'
            'enabled = true\n'
            'max_concurrent_threads_per_session = 4\n',
            encoding="utf-8",
        )
        worker_path = self.home / "agents" / "codex-profiles" / "sol-worker.toml"
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
                        {"enabled": True, "max_concurrent_threads_per_session": 2},
                    )
                    self.assertEqual(
                        worker_path.read_bytes(),
                        roles.desired_roles("private", "team")["sol-worker.toml"],
                    )
                    self.assertIn("sol_worker", agents_path.read_text(encoding="utf-8"))
                else:
                    self.assertNotIn("agents", config)
                    self.assertEqual(self.role_names(), set())
                    self.assertNotIn("sol_worker", agents_path.read_text(encoding="utf-8"))

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

    def test_dry_run_does_not_write(self):
        result = self.install("private", dry_run=True)
        self.assertEqual(result["mode"], "solo")
        self.assertFalse(self.home.exists())

    def test_config_merges_common_and_selected_mode_source_values(self):
        source = Path(self.tmp.name) / "sources"
        for name in ("shared", "modes/solo", "modes/team"):
            (source / name).mkdir(parents=True)
        (source / "manifest.json").write_text(json.dumps(profile_sources.load(lifecycle.ROOT)), encoding="utf-8")
        (source / "shared" / "config.toml").write_text(
            'model = "fixture-root"\nmodel_reasoning_effort = "high"\n'
            '[features.context_management]\nexperimental_mode = true\n', encoding="utf-8"
        )
        (source / "modes" / "solo" / "config.toml").write_text("# Native defaults.\n", encoding="utf-8")
        team_source = source / "modes" / "team" / "config.toml"
        team_source.write_text(
            '[agents]\nenabled = true\n'
            'max_concurrent_threads_per_session = 7\n'
            '[features.multi_agent_v2]\nmulti_agent_mode_hint_text = "fixture hint"\n', encoding="utf-8"
        )
        with patch.object(lifecycle, "ROOT", source):
            for profile in ("private", "work"):
                with self.subTest(profile=profile):
                    config = tomllib.loads(lifecycle.build_config("", profile, self.home, mode="team"))
                    self.assertEqual(config["model"], "fixture-root")
                    self.assertEqual(config["model_reasoning_effort"], "high")
                    self.assertEqual(config["agents"]["max_concurrent_threads_per_session"], 7)
                    self.assertIs(config["features"]["context_management"]["experimental_mode"], True)
                    self.assertEqual(config["features"]["multi_agent_v2"]["multi_agent_mode_hint_text"], "fixture hint")
            team_source.write_text(team_source.read_text().replace("= 7", "= 5"), encoding="utf-8")
            refreshed = tomllib.loads(lifecycle.build_config("", "private", self.home, mode="team"))
            self.assertEqual(refreshed["agents"]["max_concurrent_threads_per_session"], 5)
            team_source.unlink()
            solo = tomllib.loads(lifecycle.build_config("", "work", self.home, mode="solo"))
            self.assertEqual(solo["model_reasoning_effort"], "high")
            self.assertNotIn("agents", solo)
            self.assertNotIn("multi_agent_v2", solo["features"])
            config_source = source / "shared" / "config.toml"
            config_source.write_text('unowned_setting = "fixture"\n' + config_source.read_text(), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "unsupported managed keys: unowned_setting"):
                lifecycle.build_config("", "work", self.home, mode="solo")


if __name__ == "__main__":
    unittest.main()
