"""Static profile and role-manager tests."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import sys
import tempfile
import tomllib
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import manage_roles as roles
import validate as presets


class ProfileStaticTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name) / "codex-home"

    def snapshot(self):
        agents = self.home / "agents"
        return {path.name: path.read_bytes() for path in agents.glob("*.toml")} if agents.exists() else {}

    def test_static_profiles(self):
        self.assertEqual(presets.validate(), [])

    def test_private_and_work_solo_have_no_custom_roles(self):
        for profile in ("private", "work"):
            with self.subTest(profile=profile):
                self.assertEqual(roles.desired_roles(profile, "solo"), {})
                self.assertEqual(
                    set(roles.desired_roles(profile, "team")),
                    {"luna-worker.toml", "sol-worker.toml"},
                )

    def test_fixed_profiles_keep_explicit_luna_role_without_aliases(self):
        self.assertEqual(set(roles.desired_roles("lite")), {"luna-worker.toml"})
        self.assertEqual(set(roles.desired_roles("strict-common")), {"luna-worker.toml"})
        for profile in roles.PROFILES:
            for filename in roles.desired_roles(profile, "team"):
                self.assertFalse(filename.startswith("profile-"))

    def test_team_roles_pin_models_and_disable_nested_delegation(self):
        for profile in roles.PROFILES:
            with self.subTest(profile=profile):
                for filename, data in roles.desired_roles(profile, "team").items():
                    role = tomllib.loads(data.decode("utf-8"))
                    self.assertFalse(role["agents"]["enabled"])
                    if filename == "luna-worker.toml":
                        expected_model = "gpt-6-luna"
                        self.assertEqual(
                            (role["model"], role["model_reasoning_effort"]),
                            (expected_model, "max"),
                        )
                    elif filename == "sol-worker.toml":
                        self.assertEqual(
                            (role["model"], role["model_reasoning_effort"]),
                            ("gpt-6-sol", "xhigh"),
                        )

    def test_install_solo_purges_existing_top_level_role_tomls(self):
        agents = self.home / "agents"
        agents.mkdir(parents=True)
        (agents / "sol-advisor.toml").write_text('name = "sol_advisor"\n')
        result = roles.manage(self.home, "private", mode="solo")
        self.assertIn("sol-advisor.toml", result["changed_roles"])
        self.assertEqual(self.snapshot(), {})
        state = json.loads((self.home / "profiles" / "roles-state.json").read_text())
        self.assertEqual(state["version"], 2)
        self.assertEqual(state["profile"], "private")
        self.assertEqual(state["mode"], "solo")
        self.assertEqual(state["owned"], {})

    def test_team_then_solo_replaces_exact_role_set(self):
        roles.manage(self.home, "private", mode="team")
        self.assertEqual(
            set(self.snapshot()),
            {"luna-worker.toml", "sol-worker.toml"},
        )
        roles.manage(self.home, "private", mode="solo")
        self.assertEqual(self.snapshot(), {})

    def test_remove_accepts_solo_manifest_with_empty_owned_set(self):
        roles.manage(self.home, "private", mode="solo")
        result = roles.manage(self.home, None)
        self.assertEqual(result["changed_roles"], [])
        self.assertFalse((self.home / "profiles" / "roles-state.json").exists())

    def test_legacy_v1_manifest_is_read_as_team(self):
        control = self.home / "profiles"
        control.mkdir(parents=True)
        data = roles.desired_roles("private", "team")["sol-worker.toml"]
        agents = self.home / "agents"
        agents.mkdir()
        (agents / "sol-worker.toml").write_bytes(data)
        (control / "roles-state.json").write_text(
            json.dumps(
                {
                    "version": 1,
                    "profile": "private",
                    "owned": {"sol-worker.toml": roles.digest(data)},
                }
            ),
            encoding="utf-8",
        )
        state = roles.load_state(control / "roles-state.json")
        self.assertEqual(state["mode"], "team")

    def test_modified_owned_file_refuses_removal(self):
        roles.manage(self.home, "private", mode="team")
        target = self.home / "agents" / "sol-worker.toml"
        target.write_bytes(target.read_bytes() + b"# user edit\n")
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, "changed or missing"):
            roles.manage(self.home, None)
        self.assertEqual(before, self.snapshot())

    def test_dry_run_does_not_create_home(self):
        roles.manage(self.home, "private", mode="solo", dry_run=True)
        self.assertFalse(self.home.exists())

    def test_ordinary_write_failure_rolls_back_without_backup_directory(self):
        roles.manage(self.home, "private", mode="team")
        before = self.snapshot()
        state = (self.home / "profiles" / "roles-state.json").read_bytes()
        real_write = roles.atomic_write
        calls = 0

        def fail_once(path, data):
            nonlocal calls
            calls += 1
            if calls == 1:
                raise OSError("injected write failure")
            real_write(path, data)

        with patch.object(roles, "atomic_write", side_effect=fail_once):
            with self.assertRaisesRegex(OSError, "injected"):
                roles.manage(self.home, "work", mode="solo")
        self.assertEqual(before, self.snapshot())
        self.assertEqual(state, (self.home / "profiles" / "roles-state.json").read_bytes())
        self.assertFalse((self.home / "profiles" / "backups").exists())

    def test_managed_catalog_validation_requires_only_gpt6_luna_v2(self):
        catalog = {
            "models": [
                {
                    "slug": "gpt-6-luna",
                    "supported_reasoning_levels": [{"effort": "max"}],
                    "multi_agent_version": "v2",
                },
            ]
        }
        self.assertEqual(presets.validate_managed_catalog(catalog, "lite"), [])

        catalog["models"][0]["multi_agent_version"] = "v1"
        self.assertTrue(
            any("V2" in error or "v2" in error for error in presets.validate_managed_catalog(catalog, "lite"))
        )

        catalog["models"][0]["multi_agent_version"] = "v2"
        catalog["models"].append(
            {
                "slug": "gpt-5.6-terra",
                "supported_reasoning_levels": [{"effort": "medium"}],
            }
        )
        self.assertTrue(
            any("exactly" in error.lower() for error in presets.validate_managed_catalog(catalog, "lite"))
        )

    def test_validator_rejects_private_base_team_override(self):
        root = Path(self.tmp.name) / "repo"
        shutil.copytree(
            presets.ROOT,
            root,
            ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"),
        )
        target = root / "private" / "config.toml"
        target.write_text(
            target.read_text(encoding="utf-8")
            + '\n[agents]\nenabled = true\nmax_concurrent_threads_per_session = 2\n',
            encoding="utf-8",
        )
        self.assertTrue(
            any(
                error.startswith("private: base config must leave native agents untouched")
                for error in presets.validate(root=root)
            )
        )


if __name__ == "__main__":
    unittest.main()
