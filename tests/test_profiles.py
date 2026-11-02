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

    def test_private_and_work_solo_keep_only_shared_gui_role(self):
        for profile in ("private", "work"):
            with self.subTest(profile=profile):
                self.assertEqual(
                    set(roles.desired_roles(profile, "solo")),
                    {"terra-computer.toml"},
                )
                self.assertEqual(
                    set(roles.desired_roles(profile, "team")),
                    {"luna-worker.toml", "sol-worker.toml", "terra-computer.toml"},
                )

    def test_team_roles_are_identical_shared_bytes_for_both_profiles(self):
        private = roles.desired_roles("private", "team")
        self.assertEqual(private, roles.desired_roles("work", "team"))
        for filename, raw in private.items():
            self.assertEqual(raw, (roles.ROOT / "shared" / "agents" / filename).read_bytes().replace(b"\r\n", b"\n"))
        luna = tomllib.loads(private["luna-worker.toml"].decode("utf-8"))
        self.assertEqual((luna["model"], luna["model_reasoning_effort"]), ("gpt-6-luna", "high"))

    def test_install_solo_purges_existing_top_level_role_tomls(self):
        agents = self.home / "agents"
        agents.mkdir(parents=True)
        (agents / "sol-advisor.toml").write_text('name = "sol_advisor"\n')
        result = roles.manage(self.home, "private", mode="solo")
        self.assertIn("sol-advisor.toml", result["changed_roles"])
        self.assertEqual(set(self.snapshot()), {"terra-computer.toml"})
        state = json.loads((self.home / "profiles" / "roles-state.json").read_text())
        self.assertEqual(state["version"], 2)
        self.assertEqual(state["profile"], "private")
        self.assertEqual(state["mode"], "solo")
        self.assertEqual(
            state["owned"],
            {"terra-computer.toml": roles.digest(self.snapshot()["terra-computer.toml"])},
        )

    def test_team_then_solo_replaces_exact_role_set(self):
        roles.manage(self.home, "private", mode="team")
        self.assertEqual(
            set(self.snapshot()),
            {"luna-worker.toml", "sol-worker.toml", "terra-computer.toml"},
        )
        roles.manage(self.home, "private", mode="solo")
        self.assertEqual(set(self.snapshot()), {"terra-computer.toml"})

    def test_modified_owned_file_refuses_removal(self):
        roles.manage(self.home, "private", mode="team")
        target = self.home / "agents" / "sol-worker.toml"
        target.write_bytes(target.read_bytes() + b"# user edit\n")
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, "changed or missing"):
            roles.manage(self.home, None)
        self.assertEqual(before, self.snapshot())

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

    def test_validator_rejects_unsafe_manifest_source(self):
        root = Path(self.tmp.name) / "repo"
        shutil.copytree(
            presets.ROOT,
            root,
            ignore=shutil.ignore_patterns(".git", "temp", "__pycache__", "*.pyc"),
        )
        target = root / "manifest.json"
        data = json.loads(target.read_text(encoding="utf-8"))
        data["profiles"]["private"]["solo"]["config"] = ["../outside.toml"]
        target.write_text(json.dumps(data), encoding="utf-8")
        self.assertTrue(
            any(
                "Unsafe manifest source path" in error
                for error in presets.validate(root=root)
            )
        )

    def test_validator_reads_model_requirements_from_shared_sources(self):
        root = Path(self.tmp.name) / "repo"
        shutil.copytree(
            presets.ROOT, root,
            ignore=shutil.ignore_patterns(".git", "temp", "__pycache__", "*.pyc"),
        )
        config = root / "shared" / "config.toml"
        config.write_text(
            config.read_text(encoding="utf-8").replace('model = "gpt-6.1-sol"', 'model = "fixture-root"'),
            encoding="utf-8",
        )
        catalog = {"models": [
            {"slug": model, "supported_reasoning_levels": [{"effort": effort}]}
            for model, effort in (
                ("fixture-root", "xhigh"), ("gpt-6.1-sol", "high"),
                ("gpt-6-luna", "high"), ("gpt-6.1-terra", "high"),
            )
        ]}
        self.assertEqual(presets.validate(root=root, catalog=catalog), [])
        catalog["models"] = [model for model in catalog["models"] if model["slug"] != "fixture-root"]
        self.assertIn("Model metadata does not confirm fixture-root / xhigh", presets.validate(root=root, catalog=catalog))


if __name__ == "__main__":
    unittest.main()
