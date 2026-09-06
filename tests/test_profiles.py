"""Synthetic filesystem/metadata tests. Never touches the real Codex home."""
from __future__ import annotations

import itertools
import json
from pathlib import Path
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

    def install(self, profile="x20", **kwargs):
        return roles.manage(self.home, profile, **kwargs)

    def snapshot(self):
        return {p.name: p.read_bytes() for p in (self.home / "agents").glob("*.toml")}

    def test_static_profiles(self):
        self.assertEqual(presets.validate(), [])

    def test_all_twelve_directed_switches_remove_stale_roles(self):
        for before, after in itertools.permutations(roles.PROFILES, 2):
            with self.subTest(before=before, after=after):
                self.install(before)
                self.install(after)
                self.assertEqual(self.snapshot(), roles.desired_roles(after))
                roles.manage(self.home, None)
                self.assertEqual(self.snapshot(), {})

    def test_all_profiles_aliases_pin_both_model_and_effort(self):
        for profile in roles.PROFILES:
            with self.subTest(profile=profile):
                expected = presets.EXPECTED[profile]
                for filename, data in roles.desired_roles(profile).items():
                    role = tomllib.loads(data.decode())
                    self.assertFalse(role["agents"]["enabled"])
                    if filename.startswith("routing-"):
                        self.assertEqual((role["model"], role["model_reasoning_effort"]), expected[2:4])

    def test_install_idempotent(self):
        self.install()
        before = self.snapshot()
        result = self.install()
        self.assertEqual(result["changed_roles"], [])
        self.assertIsNone(result["backup"])
        self.assertEqual(before, self.snapshot())

    def test_remove_idempotent(self):
        self.install()
        roles.manage(self.home, None)
        self.assertEqual(roles.manage(self.home, None)["changed_roles"], [])

    def test_dry_run_does_not_create_home(self):
        self.install(dry_run=True)
        self.assertFalse(self.home.exists())

    def test_unrelated_files_and_configuration_preserved(self):
        (self.home / "agents").mkdir(parents=True)
        other = self.home / "agents" / "specialist.toml"
        other.write_text('name = "independent_specialist"\n')
        for filename in ("config.toml", "AGENTS.md", "models.json", "auth.json"):
            (self.home / filename).write_text("sentinel: not installer-owned\n")
        self.install()
        roles.manage(self.home, None)
        self.assertEqual(other.read_text(), 'name = "independent_specialist"\n')
        for filename in ("config.toml", "AGENTS.md", "models.json", "auth.json"):
            self.assertEqual((self.home / filename).read_text(), "sentinel: not installer-owned\n")

    def test_unmanaged_filename_collision_refused(self):
        (self.home / "agents").mkdir(parents=True)
        (self.home / "agents" / "sol-worker.toml").write_text('name = "mine"\n')
        with self.assertRaisesRegex(ValueError, "collision"):
            self.install()

    def test_same_role_name_in_different_file_refused(self):
        (self.home / "agents").mkdir(parents=True)
        (self.home / "agents" / "my-default.toml").write_text('name = "default"\n')
        with self.assertRaisesRegex(ValueError, "collision"):
            self.install()

    def test_modified_owned_file_refuses_switch_and_removal(self):
        self.install()
        target = self.home / "agents" / "astra-worker.toml"
        target.write_bytes(target.read_bytes() + b"# user edit\n")
        before = self.snapshot()
        for profile in (None, "lite"):
            with self.assertRaisesRegex(ValueError, "changed or missing"):
                roles.manage(self.home, profile)
            self.assertEqual(before, self.snapshot())

    def test_missing_owned_file_refused(self):
        self.install()
        (self.home / "agents" / "sol-worker.toml").unlink()
        with self.assertRaisesRegex(ValueError, "changed or missing"):
            self.install("lite")

    def test_unsafe_manifest_filename_refused(self):
        control = self.home / "routing-rules"
        control.mkdir(parents=True)
        (control / "roles-state.json").write_text(json.dumps({
            "version": 1, "profile": "x20", "owned": {"../config.toml": "0" * 64}}))
        with self.assertRaisesRegex(ValueError, "Unsafe"):
            self.install()

    def test_bad_state_types_refused(self):
        control = self.home / "routing-rules"
        control.mkdir(parents=True)
        for state in ([], {}, {"version": 1, "profile": "x20", "owned": []}):
            (control / "roles-state.json").write_text(json.dumps(state))
            with self.assertRaises(ValueError):
                self.install()

    def test_active_lock_refused(self):
        (self.home / "routing-rules" / "roles.lock").mkdir(parents=True)
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

    def test_explicit_legacy_adoption_and_crlf_cleanup(self):
        # Synthetic known-blob fixture exercises the same whitelist path as legacy files.
        raw = b'name = "sol_worker"\nmodel = "legacy-fixture"\n'
        with patch.dict(roles.LEGACY, {"sol-worker.toml": {roles.git_blob(raw)}}):
            (self.home / "agents").mkdir(parents=True)
            (self.home / "agents" / "sol-worker.toml").write_bytes(raw.replace(b"\n", b"\r\n"))
            with self.assertRaisesRegex(ValueError, "adopt-legacy"):
                self.install("lite")
            result = self.install("lite", adopt_legacy=True)
            self.assertEqual(self.snapshot(), roles.desired_roles("lite"))
            self.assertEqual((Path(result["backup"]) / "sol-worker.toml").read_bytes(), raw.replace(b"\n", b"\r\n"))
            roles.manage(self.home, None)
            self.assertFalse((self.home / "agents" / "sol-worker.toml").exists())

    def test_adoption_does_not_accept_lookalike(self):
        (self.home / "agents").mkdir(parents=True)
        (self.home / "agents" / "sol-worker.toml").write_text('name = "sol_worker"\n# edited\n')
        with self.assertRaisesRegex(ValueError, "collision"):
            self.install("lite", adopt_legacy=True)

    def test_ordinary_write_failure_rolls_back(self):
        self.install("x20")
        before = self.snapshot()
        state = (self.home / "routing-rules" / "roles-state.json").read_bytes()
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
        self.assertEqual(state, (self.home / "routing-rules" / "roles-state.json").read_bytes())
        self.assertFalse((self.home / "routing-rules" / "roles.lock").exists())

    def test_synthetic_model_metadata_supported_and_missing_effort(self):
        catalog = {"models": [
            {"slug": "gpt-6-astra", "supported_reasoning_levels": [{"effort": e} for e in ("medium", "high")]},
            {"slug": "gpt-5.6-sol", "supported_reasoning_levels": [{"effort": e} for e in ("high", "xhigh")]},
            {"slug": "gpt-5.6-luna", "supported_reasoning_levels": [{"effort": "max"}]},
        ]}
        self.assertEqual(presets.validate(catalog=catalog), [])
        catalog["models"][-1]["supported_reasoning_levels"] = []
        self.assertTrue(any("gpt-5.6-luna / max" in e for e in presets.validate(catalog=catalog)))

    def test_lite_metadata_does_not_require_astra_entitlement(self):
        catalog = {"models": [{"slug": "gpt-5.6-luna", "supported_reasoning_levels": [{"effort": "max"}]}]}
        self.assertEqual(presets.validate(catalog=catalog, profile="lite"), [])
        self.assertTrue(presets.validate(catalog=catalog, profile="x20"))

    def test_malformed_metadata_rejected(self):
        for catalog in ({}, {"models": [{}]}, {"models": "not a list"}, []):
            self.assertTrue(presets.validate(catalog=catalog))

    def test_duplicate_model_metadata_rejected(self):
        catalog = {"models": [{"slug": "gpt-6-astra"}, {"slug": "gpt-6-astra"}]}
        self.assertTrue(any("Duplicate" in e for e in presets.validate(catalog=catalog)))


if __name__ == "__main__":
    unittest.main()
