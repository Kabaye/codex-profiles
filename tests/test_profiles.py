"""Synthetic filesystem/metadata tests. Never touches the real Codex home."""
from __future__ import annotations

import itertools
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import tomllib
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import manage_roles as roles
import manage_profile as lifecycle
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

    def seed_legacy_state(self, home: Path, legacy_profile: str) -> str:
        canonical = roles.LEGACY_PROFILES[legacy_profile]
        agents = home / "agents"
        agents.mkdir(parents=True)
        owned = {}
        for filename, data in roles.desired_roles(canonical).items():
            old_name = filename.replace("profile-", "routing-", 1)
            (agents / old_name).write_bytes(data)
            owned[old_name] = roles.digest(data)
        control = home / "routing-rules"
        control.mkdir()
        (control / "roles-state.json").write_text(
            json.dumps({"version": 1, "profile": legacy_profile, "owned": owned}),
            encoding="utf-8",
        )
        return canonical

    def test_static_profiles(self):
        self.assertEqual(presets.validate(), [])

    def test_only_canonical_profiles_and_aliases_are_install_targets(self):
        self.assertEqual(set(roles.PROFILES), {"lite", "strict-common", "private", "work"})
        for profile in roles.PROFILES:
            filenames = set(roles.desired_roles(profile))
            self.assertFalse(any(name.startswith("routing-") for name in filenames))
            self.assertTrue({
                "profile-default.toml",
                "profile-worker.toml",
                "profile-explorer.toml",
            }.issubset(filenames))
        for legacy_profile in roles.LEGACY_PROFILES:
            with self.subTest(legacy_profile=legacy_profile):
                with self.assertRaisesRegex(ValueError, "Unknown profile"):
                    roles.desired_roles(legacy_profile)

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
                    if filename.startswith("profile-"):
                        self.assertEqual((role["model"], role["model_reasoning_effort"]), expected[2:4])

    def test_all_legacy_profile_states_migrate_to_canonical_state_and_aliases(self):
        for legacy_profile in roles.LEGACY_PROFILES:
            with self.subTest(legacy_profile=legacy_profile), tempfile.TemporaryDirectory() as tmp:
                home = Path(tmp) / "codex-home"
                canonical = self.seed_legacy_state(home, legacy_profile)
                result = roles.manage(home, canonical)
                self.assertTrue(result["migrated_legacy_state"])
                self.assertEqual(
                    {p.name: p.read_bytes() for p in (home / "agents").glob("*.toml")},
                    roles.desired_roles(canonical),
                )
                state = json.loads((home / "profiles" / "roles-state.json").read_text())
                self.assertEqual(state["profile"], canonical)
                self.assertFalse((home / "routing-rules").exists())

    def test_legacy_profile_state_can_be_removed_without_reinstall(self):
        canonical = self.seed_legacy_state(self.home, "x20-work")
        self.assertEqual(canonical, "work")
        result = roles.manage(self.home, None)
        self.assertTrue(result["migrated_legacy_state"])
        self.assertEqual(self.snapshot(), {})
        self.assertFalse((self.home / "routing-rules").exists())
        self.assertFalse((self.home / "profiles").exists())

    def test_static_alias_allowlist_covers_and_adopts_every_historical_worker_blob(self):
        objects = subprocess.run(
            ["git", "-C", str(roles.ROOT), "rev-list", "--objects", "--all"],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        ).stdout.splitlines()
        historical_workers = {
            line.split(" ", 1)[0]
            for line in objects
            if " " in line
            and line.split(" ", 1)[1].replace("\\", "/").endswith(
                ("/agents/luna-worker.toml", "/agents/sol-worker.toml", "/agents/astra-worker.toml")
            )
        }
        self.assertTrue(historical_workers)
        known_worker_blobs = set().union(
            *(roles.LEGACY.get(filename, set()) for filename in roles.ROLE_FILES),
            *(lifecycle.KNOWN_ROLE_BLOBS.get(filename, set()) for filename in roles.ROLE_FILES),
        )
        self.assertLessEqual(historical_workers, known_worker_blobs)
        for worker_blob in historical_workers:
            base = subprocess.run(
                ["git", "-C", str(roles.ROOT), "cat-file", "blob", worker_blob],
                check=True,
                capture_output=True,
            ).stdout
            for alias_name in roles.ALIASES:
                with self.subTest(worker_blob=worker_blob, alias=alias_name), tempfile.TemporaryDirectory() as tmp:
                    alias = roles.alias_bytes(base, alias_name)
                    legacy_name = f"routing-{alias_name}.toml"
                    self.assertIn(
                        roles.git_blob(alias),
                        roles.HISTORICAL_ALIAS_BLOBS[legacy_name],
                    )
                    home = Path(tmp) / "codex-home"
                    agents = home / "agents"
                    agents.mkdir(parents=True)
                    target = agents / legacy_name
                    target.write_bytes(alias)
                    result = roles.manage(home, None, adopt_legacy=True)
                    self.assertIn(target.name, result["changed_roles"])
                    self.assertFalse(target.exists())

    def test_current_and_legacy_manifests_together_stop_for_review(self):
        self.seed_legacy_state(self.home, "x20")
        current = self.home / "profiles"
        current.mkdir()
        (current / "roles-state.json").write_text("{}", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Both current and legacy"):
            self.install()

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
        target = self.home / "agents" / "sol-worker.toml"
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
        control = self.home / "profiles"
        control.mkdir(parents=True)
        (control / "roles-state.json").write_text(json.dumps({
            "version": 1, "profile": "private", "owned": {"../config.toml": "0" * 64}}))
        with self.assertRaisesRegex(ValueError, "Unsafe"):
            self.install()

    def test_bad_state_types_refused(self):
        control = self.home / "profiles"
        control.mkdir(parents=True)
        for state in ([], {}, {"version": 1, "profile": "private", "owned": []}):
            (control / "roles-state.json").write_text(json.dumps(state))
            with self.assertRaises(ValueError):
                self.install()

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

    def test_explicit_legacy_adoption_and_crlf_cleanup(self):
        raw = b'name = "sol_worker"\nmodel = "legacy-fixture"\n'
        with patch.dict(roles.LEGACY, {"sol-worker.toml": {roles.git_blob(raw)}}):
            (self.home / "agents").mkdir(parents=True)
            (self.home / "agents" / "sol-worker.toml").write_bytes(raw.replace(b"\n", b"\r\n"))
            with self.assertRaisesRegex(ValueError, "adopt-legacy"):
                self.install("lite")
            result = self.install("lite", adopt_legacy=True)
            self.assertEqual(self.snapshot(), roles.desired_roles("lite"))
            self.assertNotIn("backup", result)
            roles.manage(self.home, None)
            self.assertFalse((self.home / "agents" / "sol-worker.toml").exists())

    def test_adoption_does_not_accept_lookalike(self):
        (self.home / "agents").mkdir(parents=True)
        (self.home / "agents" / "sol-worker.toml").write_text('name = "sol_worker"\n# edited\n')
        with self.assertRaisesRegex(ValueError, "collision"):
            self.install("lite", adopt_legacy=True)

    def test_modified_legacy_alias_is_not_adopted(self):
        (self.home / "agents").mkdir(parents=True)
        data = roles.desired_roles("private")["profile-default.toml"] + b"# edited\n"
        (self.home / "agents" / "routing-default.toml").write_bytes(data)
        with self.assertRaisesRegex(ValueError, "collision"):
            self.install("lite", adopt_legacy=True)

    def test_ordinary_write_failure_rolls_back(self):
        self.install("private")
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
