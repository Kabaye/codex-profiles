"""Synthetic filesystem/metadata tests. Never touches the real Codex home."""
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


class ProfileTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name) / "codex-home"

    def install(self, profile="private", **kwargs):
        return roles.manage(self.home, profile, **kwargs)

    def snapshot(self):
        return {p.name: p.read_bytes() for p in (self.home / "agents").glob("*.toml")}

    def test_static_profiles(self):
        self.assertEqual(presets.validate(), [])

    def test_only_current_profiles_and_aliases_are_install_targets(self):
        self.assertEqual(set(roles.PROFILES), {"lite", "strict-common", "private", "work"})
        for profile in roles.PROFILES:
            filenames = set(roles.desired_roles(profile))
            self.assertTrue({
                "profile-default.toml",
                "profile-worker.toml",
                "profile-explorer.toml",
            }.issubset(filenames))
        with self.assertRaisesRegex(ValueError, "Unknown profile"):
            roles.desired_roles("unsupported")

    def test_profiles_suppress_builtin_multi_agent_mode_without_forcing_v2(self):
        for profile in roles.PROFILES:
            with self.subTest(profile=profile):
                config = tomllib.loads(
                    (presets.ROOT / profile / "config.toml").read_text(encoding="utf-8")
                )
                multi_agent_v2 = config["features"]["multi_agent_v2"]
                self.assertEqual(multi_agent_v2, {"multi_agent_mode_hint_text": ""})
                self.assertNotIn("enabled", multi_agent_v2)

    def test_validator_rejects_multi_agent_mode_hint_drift(self):
        root = Path(self.tmp.name) / "repo"
        shutil.copytree(
            presets.ROOT,
            root,
            ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"),
        )
        target = root / "work" / "config.toml"
        text = target.read_text(encoding="utf-8")
        target.write_text(
            text.replace('multi_agent_mode_hint_text = ""',
                         'multi_agent_mode_hint_text = "explicit-only"', 1),
            encoding="utf-8",
        )
        self.assertTrue(any(
            error.startswith("work: profile-managed feature drift")
            for error in presets.validate(root=root)
        ))

    def test_all_profiles_aliases_pin_both_model_and_effort(self):
        for profile in roles.PROFILES:
            with self.subTest(profile=profile):
                expected = presets.EXPECTED[profile]
                for filename, data in roles.desired_roles(profile).items():
                    role = tomllib.loads(data.decode())
                    self.assertFalse(role["agents"]["enabled"])
                    if filename.startswith("profile-"):
                        self.assertEqual((role["model"], role["model_reasoning_effort"]), expected[2:4])

    def test_install_idempotent(self):
        self.install()
        before = self.snapshot()
        result = self.install()
        self.assertEqual(result["changed_roles"], [])
        self.assertNotIn("backup", result)
        self.assertEqual(before, self.snapshot())

    def test_remove_idempotent(self):
        self.install()
        roles.manage(self.home, None)
        self.assertEqual(roles.manage(self.home, None)["changed_roles"], [])

    def test_role_lifecycle_creates_no_backup_directories(self):
        self.install("work")
        self.install("private")
        roles.manage(self.home, None)
        self.assertFalse((self.home / "profiles" / "backups").exists())

    def test_dry_run_does_not_create_home(self):
        self.install(dry_run=True)
        self.assertFalse(self.home.exists())

    def test_install_purges_all_role_tomls_but_preserves_other_files(self):
        (self.home / "agents").mkdir(parents=True)
        other = self.home / "agents" / "specialist.toml"
        other.write_text('name = "independent_specialist"\n')
        broken = self.home / "agents" / "broken.toml"
        broken.write_text("not valid TOML = [\n")
        note = self.home / "agents" / "README.txt"
        note.write_text("keep\n")
        for filename in ("config.toml", "AGENTS.md", "models.json", "auth.json"):
            (self.home / filename).write_text("sentinel: not installer-owned\n")
        result = self.install()
        self.assertIn("specialist.toml", result["changed_roles"])
        self.assertIn("broken.toml", result["changed_roles"])
        self.assertFalse(other.exists())
        self.assertFalse(broken.exists())
        self.assertEqual(note.read_text(), "keep\n")
        roles.manage(self.home, None)
        self.assertEqual(note.read_text(), "keep\n")
        for filename in ("config.toml", "AGENTS.md", "models.json", "auth.json"):
            self.assertEqual((self.home / filename).read_text(), "sentinel: not installer-owned\n")

    def test_install_replaces_unmanaged_profile_filename(self):
        (self.home / "agents").mkdir(parents=True)
        (self.home / "agents" / "sol-worker.toml").write_text('name = "mine"\n')
        result = self.install()
        self.assertIn("sol-worker.toml", result["changed_roles"])
        self.assertEqual(self.snapshot(), roles.desired_roles("private"))

    def test_install_purges_unmanaged_role_name(self):
        (self.home / "agents").mkdir(parents=True)
        (self.home / "agents" / "my-default.toml").write_text('name = "default"\n')
        result = self.install()
        self.assertIn("my-default.toml", result["changed_roles"])
        self.assertEqual(self.snapshot(), roles.desired_roles("private"))

    def test_dry_run_reports_role_purge_without_writing(self):
        (self.home / "agents").mkdir(parents=True)
        extra = self.home / "agents" / "sol-advisor.toml"
        extra.write_text('name = "sol_advisor"\n')
        result = self.install("work", dry_run=True)
        self.assertIn("sol-advisor.toml", result["changed_roles"])
        self.assertTrue(extra.exists())

    def test_modified_owned_file_is_replaced_on_switch(self):
        self.install()
        target = self.home / "agents" / "sol-worker.toml"
        target.write_bytes(target.read_bytes() + b"# user edit\n")
        self.install("lite")
        self.assertEqual(self.snapshot(), roles.desired_roles("lite"))

    def test_modified_owned_file_refuses_removal(self):
        self.install()
        target = self.home / "agents" / "sol-worker.toml"
        target.write_bytes(target.read_bytes() + b"# user edit\n")
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, "changed or missing"):
            roles.manage(self.home, None)
        self.assertEqual(before, self.snapshot())

    def test_missing_owned_file_is_replaced_on_switch(self):
        self.install()
        (self.home / "agents" / "sol-worker.toml").unlink()
        self.install("lite")
        self.assertEqual(self.snapshot(), roles.desired_roles("lite"))

    def test_unsafe_manifest_is_replaced_on_install(self):
        control = self.home / "profiles"
        control.mkdir(parents=True)
        (control / "roles-state.json").write_text(json.dumps({
            "version": 1, "profile": "private", "owned": {"../config.toml": "0" * 64}}))
        self.install()
        self.assertEqual(self.snapshot(), roles.desired_roles("private"))

    def test_bad_state_types_are_replaced_on_install(self):
        control = self.home / "profiles"
        control.mkdir(parents=True)
        for state in ([], {}, {"version": 1, "profile": "private", "owned": []}):
            (control / "roles-state.json").write_text(json.dumps(state))
            self.install()
            self.assertEqual(self.snapshot(), roles.desired_roles("private"))

    def test_bad_state_type_refuses_removal(self):
        control = self.home / "profiles"
        control.mkdir(parents=True)
        (control / "roles-state.json").write_text("[]")
        with self.assertRaises(ValueError):
            roles.manage(self.home, None)

    def test_active_lock_refused(self):
        (self.home / "profiles" / "roles.lock").mkdir(parents=True)
        with self.assertRaisesRegex(ValueError, "active"):
            self.install()

    def test_symlinked_roles_directory_refused(self):
        self.home.mkdir()
        outside = Path(self.tmp.name) / "outside"
        outside.mkdir()
        try:
            (self.home / "agents").symlink_to(outside, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("Symlink creation unavailable on this OS")
        with self.assertRaisesRegex(ValueError, "Linked directory"):
            self.install()

    def test_symlinked_role_file_refused(self):
        (self.home / "agents").mkdir(parents=True)
        outside = Path(self.tmp.name) / "outside.toml"
        outside.write_text('name = "outside"\n')
        try:
            (self.home / "agents" / "sol-worker.toml").symlink_to(outside)
        except (OSError, NotImplementedError):
            self.skipTest("Symlink creation unavailable on this OS")
        with self.assertRaisesRegex(ValueError, "regular"):
            self.install()
        self.assertEqual(outside.read_text(), 'name = "outside"\n')

    def test_ordinary_write_failure_rolls_back(self):
        self.install("private")
        extra = self.home / "agents" / "aaa-extra.toml"
        extra.write_text('name = "extra"\n')
        before = self.snapshot()
        state = (self.home / "profiles" / "roles-state.json").read_bytes()
        real_write = roles.atomic_write
        calls = 0

        def fail_once(path, data):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError("injected write failure")
            real_write(path, data)

        with patch.object(roles, "atomic_write", side_effect=fail_once):
            with self.assertRaisesRegex(OSError, "injected"):
                self.install("lite")
        self.assertEqual(before, self.snapshot())
        self.assertTrue(extra.exists())
        self.assertEqual(state, (self.home / "profiles" / "roles-state.json").read_bytes())
        self.assertFalse((self.home / "profiles" / "roles.lock").exists())
        self.assertFalse((self.home / "profiles" / "backups").exists())

    def test_synthetic_model_metadata_supported_and_missing_effort(self):
        catalog = {"models": [
            {"slug": "gpt-6-astra", "supported_reasoning_levels": [{"effort": e} for e in ("medium", "high")]},
            {"slug": "gpt-5.6-sol", "supported_reasoning_levels": [{"effort": e} for e in ("high", "xhigh")]},
            {"slug": "gpt-5.6-terra", "supported_reasoning_levels": [{"effort": "medium"}]},
            {"slug": "gpt-5.6-luna", "supported_reasoning_levels": [{"effort": "max"}]},
        ]}
        self.assertEqual(presets.validate(catalog=catalog), [])
        catalog["models"][-1]["supported_reasoning_levels"] = []
        self.assertTrue(any("gpt-5.6-luna / max" in e for e in presets.validate(catalog=catalog)))

    def test_lite_metadata_does_not_require_sol_or_astra_entitlement(self):
        catalog = {"models": [
            {"slug": "gpt-5.6-terra", "supported_reasoning_levels": [{"effort": "medium"}]},
            {"slug": "gpt-5.6-luna", "supported_reasoning_levels": [{"effort": "max"}]},
        ]}
        self.assertEqual(presets.validate(catalog=catalog, profile="lite"), [])
        self.assertEqual(presets.validate_lite_catalog(catalog), [])
        with_sol = {"models": catalog["models"] + [
            {"slug": "gpt-5.6-sol", "supported_reasoning_levels": [{"effort": "high"}]}
        ]}
        self.assertTrue(presets.validate_lite_catalog(with_sol))
        self.assertTrue(presets.validate(catalog=catalog, profile="private"))

    def test_malformed_metadata_rejected(self):
        for catalog in ({}, {"models": [{}]}, {"models": "not a list"}, []):
            self.assertTrue(presets.validate(catalog=catalog))

    def test_duplicate_model_metadata_rejected(self):
        catalog = {"models": [{"slug": "gpt-6-astra"}, {"slug": "gpt-6-astra"}]}
        self.assertTrue(any("Duplicate" in e for e in presets.validate(catalog=catalog)))


if __name__ == "__main__":
    unittest.main()
