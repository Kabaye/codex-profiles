"""Unified profile/mode lifecycle tests. Never touches the real Codex home."""
from __future__ import annotations

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
        self.models = Path(self.tmp.name) / "models.json"
        self.models.write_text(
            json.dumps(
                {
                    "catalog_version": "synthetic",
                    "models": [
                        {
                            "slug": "gpt-6-astra",
                            "supported_reasoning_levels": [{"effort": "high"}],
                            "multi_agent_version": "v2",
                        },
                        {
                            "slug": "gpt-5.6-sol",
                            "supported_reasoning_levels": [
                                {"effort": "high"},
                                {"effort": "xhigh"},
                            ],
                            "multi_agent_version": "v2",
                        },
                        {
                            "slug": "gpt-5.6-terra",
                            "supported_reasoning_levels": [{"effort": "medium"}],
                            "multi_agent_version": "v2",
                        },
                        {
                            "slug": "gpt-5.6-luna",
                            "supported_reasoning_levels": [{"effort": "max"}],
                            "multi_agent_version": "v1",
                            "model_messages": {"instructions_template": "preserve me"},
                        },
                    ],
                }
            ),
            encoding="utf-8",
        )

    def install(self, profile: str, *, mode: str | None = None, dry_run: bool = False):
        return lifecycle.apply(
            self.home,
            profile,
            mode=mode,
            dry_run=dry_run,
            models=self.models,
        )

    def state(self) -> dict:
        return json.loads(
            (self.home / "profiles" / "roles-state.json").read_text(encoding="utf-8")
        )

    def config(self) -> dict:
        return tomllib.loads((self.home / "config.toml").read_text(encoding="utf-8"))

    def role_names(self) -> set[str]:
        agents = self.home / "agents"
        return {path.name for path in agents.glob("*.toml")} if agents.exists() else set()

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
                self.assertEqual(
                    config["model_catalog_json"],
                    (self.home / lifecycle.MANAGED_CATALOG).as_posix(),
                )
                self.assertFalse((self.home / "AGENTS.md").exists())

                catalog = json.loads(
                    (self.home / lifecycle.MANAGED_CATALOG).read_text(encoding="utf-8")
                )
                luna = next(model for model in catalog["models"] if model["slug"] == "gpt-5.6-luna")
                self.assertEqual(luna["multi_agent_version"], "v2")
                self.assertEqual(
                    luna["model_messages"]["instructions_template"],
                    "preserve me",
                )
                self.assertEqual(catalog["catalog_version"], "synthetic")

    def test_private_team_switch_adds_only_explicit_luna_and_sol_roles(self):
        self.install("private")
        before_catalog = (self.home / lifecycle.MANAGED_CATALOG).read_bytes()

        team = lifecycle.apply(
            self.home,
            "private",
            mode="team",
            refresh_catalog=False,
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
        self.assertIn("Luna / max", agents_text)
        self.assertIn("Sol / high", agents_text)
        self.assertIn("two open child threads", agents_text)
        self.assertNotIn("profile-default", agents_text)
        self.assertEqual(before_catalog, (self.home / lifecycle.MANAGED_CATALOG).read_bytes())

        solo = lifecycle.apply(
            self.home,
            "private",
            mode="solo",
            refresh_catalog=False,
        )
        self.assertEqual(solo["mode"], "solo")
        self.assertEqual(self.role_names(), set())
        self.assertFalse((self.home / "AGENTS.md").exists())
        self.assertNotIn("agents", self.config())
        self.assertNotIn("multi_agent_v2", self.config().get("features", {}))
        self.assertEqual(before_catalog, (self.home / lifecycle.MANAGED_CATALOG).read_bytes())

    def test_work_team_keeps_luna_default_and_explicit_personal_sol_lane(self):
        self.install("work", mode="team")
        text = (self.home / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("ordinary work objectives", text)
        self.assertIn("luna_worker", text)
        self.assertIn("это личная задача", text)
        self.assertIn("sol_worker", text)
        self.assertIn("Selecting Astra as root changes only the root", text)
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

    def test_lite_uses_same_managed_catalog_path_and_filters_models(self):
        self.install("lite")
        config = self.config()
        self.assertEqual(
            config["model_catalog_json"],
            (self.home / lifecycle.MANAGED_CATALOG).as_posix(),
        )
        self.assertEqual(config["agents"]["max_concurrent_threads_per_session"], 1)
        self.assertEqual(self.state()["mode"], "team")
        self.assertEqual(self.role_names(), {"luna-worker.toml"})

        catalog = json.loads(
            (self.home / lifecycle.MANAGED_CATALOG).read_text(encoding="utf-8")
        )
        self.assertEqual(
            {model["slug"] for model in catalog["models"]},
            {"gpt-5.6-terra", "gpt-5.6-luna"},
        )
        luna = next(model for model in catalog["models"] if model["slug"] == "gpt-5.6-luna")
        self.assertEqual(luna["multi_agent_version"], "v2")

    def test_strict_common_remains_fixed_team(self):
        self.install("strict-common")
        self.assertEqual(self.state()["mode"], "team")
        self.assertEqual(self.role_names(), {"luna-worker.toml"})
        self.assertEqual(self.config()["agents"]["max_concurrent_threads_per_session"], 4)
        with self.assertRaisesRegex(ValueError, "fixed team routing"):
            lifecycle.apply(
                self.home,
                "strict-common",
                mode="solo",
                models=self.models,
            )

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
        self.assertTrue((self.home / lifecycle.MANAGED_CATALOG).is_file())

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
            refresh_catalog=False,
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

    def test_mode_switch_requires_existing_managed_catalog(self):
        self.install("private")
        (self.home / lifecycle.MANAGED_CATALOG).unlink()
        with self.assertRaisesRegex(ValueError, "catalog is missing"):
            lifecycle.apply(
                self.home,
                "private",
                mode="team",
                refresh_catalog=False,
            )

    def test_dry_run_does_not_write(self):
        result = self.install("private", dry_run=True)
        self.assertEqual(result["mode"], "solo")
        self.assertFalse(self.home.exists())


if __name__ == "__main__":
    unittest.main()
