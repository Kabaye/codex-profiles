"""Isolated namespaces and verified migration from former flat role installs."""
from pathlib import Path
import json
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import manage_profile as lifecycle
import manage_roles as roles


class RoleOwnershipTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name) / "home"

    def snapshot(self):
        return {str(p.relative_to(self.home)): p.read_bytes()
                for p in self.home.rglob("*") if p.is_file()}

    def config_role(self, raw=b'name = "terra_computer"\n'):
        path = self.home / "agents" / "codex-config" / "terra-computer.toml"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        state = self.home / "codex-config" / "roles-state.json"
        state.parent.mkdir(exist_ok=True)
        state.write_text(json.dumps({"version": 1, "owned": {
            "codex-config/terra-computer.toml": roles.digest(raw)}}), encoding="utf-8")
        return path, state

    def legacy_install(self, terra=False):
        agents = self.home / "agents"
        agents.mkdir(parents=True)
        files = roles.desired_roles("private", "team")
        if terra:
            files["terra-computer.toml"] = b'name = "terra_computer"\n# legacy\n'
        for name, data in files.items():
            (agents / name).write_bytes(data)
        state = self.home / "profiles" / "roles-state.json"
        state.parent.mkdir()
        state.write_text(json.dumps({"version": 2, "profile": "private", "mode": "team",
            "owned": {name: roles.digest(data) for name, data in files.items()}}), encoding="utf-8")
        return state

    def test_config_and_custom_roles_survive_modes_and_profile_removal(self):
        shared, state = self.config_role()
        custom = self.home / "agents" / "custom-advisor.toml"
        custom.write_bytes(b'name = "custom_advisor"\n')
        preserved = {p: p.read_bytes() for p in (shared, state, custom)}
        for mode in ("team", "solo", "team"):
            roles.manage(self.home, "private", mode=mode)
            for path, raw in preserved.items():
                self.assertEqual(path.read_bytes(), raw)
            owned = roles.load_state(self.home / "profiles" / "roles-state.json")["owned"]
            self.assertEqual(set(owned), {"codex-profiles/sol-worker.toml", "codex-profiles/luna-worker.toml"}
                             if mode == "team" else set())
        roles.manage(self.home, None)
        for path, raw in preserved.items():
            self.assertEqual(path.read_bytes(), raw)
        self.assertFalse((self.home / "agents" / "codex-profiles").exists())

    def test_legacy_native_roles_move_without_duplicate_copies(self):
        self.legacy_install()
        roles.manage(self.home, "private", mode="team")
        agents = self.home / "agents"
        self.assertEqual(list(agents.glob("*.toml")), [])
        self.assertEqual({p.name for p in (agents / "codex-profiles").glob("*.toml")},
                         {"sol-worker.toml", "luna-worker.toml"})
        self.assertEqual(roles.load_state(self.home / "profiles" / "roles-state.json")["version"], 3)

    def test_legacy_shared_role_requires_config_handoff_before_any_write(self):
        manifest = self.legacy_install(terra=True)
        before = self.snapshot()
        actions = [lambda: roles.manage(self.home, None),
                   lambda: roles.manage(self.home, "private", mode="solo"),
                   lambda: roles.manage(self.home, "work", mode="team", dry_run=True),
                   lambda: lifecycle.apply(self.home, "private", mode="team")]
        for action in actions:
            with self.assertRaisesRegex(ValueError, "codex-config sync-roles"):
                action()
            self.assertEqual(self.snapshot(), before)

        shared, config_state = self.config_role()
        (self.home / "agents" / "terra-computer.toml").unlink()
        preserved = {p: p.read_bytes() for p in (shared, config_state)}
        roles.manage(self.home, "private", mode="solo")
        self.assertEqual(roles.load_state(manifest)["owned"], {})
        roles.manage(self.home, "private", mode="team")
        roles.manage(self.home, None)
        for path, raw in preserved.items():
            self.assertEqual(path.read_bytes(), raw)

    def test_native_changes_do_not_inspect_foreign_roles_or_state(self):
        shared, state = self.config_role()
        shared.write_bytes(b"locally edited foreign role\n")
        state.write_bytes(b"invalid foreign state\n")
        roles.manage(self.home, "private", mode="team")
        roles.manage(self.home, "private", mode="solo")
        self.assertEqual(shared.read_bytes(), b"locally edited foreign role\n")
        self.assertEqual(state.read_bytes(), b"invalid foreign state\n")

    def test_unowned_nested_destination_collision_refuses(self):
        target = self.home / "agents" / "codex-profiles" / "sol-worker.toml"
        target.parent.mkdir(parents=True)
        target.write_bytes(b"unrelated user role\n")
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, "Unmanaged role collision"):
            roles.manage(self.home, "private", mode="team")
        self.assertEqual(self.snapshot(), before)

    def test_modified_flat_owned_role_refuses_migration(self):
        self.legacy_install()
        path = self.home / "agents" / "sol-worker.toml"
        path.write_bytes(path.read_bytes() + b"# user edit\n")
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, "changed or missing"):
            roles.manage(self.home, "private", mode="team")
        self.assertEqual(self.snapshot(), before)

    def test_migration_failure_restores_flat_roles_and_state(self):
        self.legacy_install()
        before = self.snapshot()
        original = roles.atomic_write
        writes = 0

        def fail_once(path, data):
            nonlocal writes
            writes += 1
            if writes == 2:
                raise OSError("injected migration failure")
            original(path, data)

        with patch.object(roles, "atomic_write", side_effect=fail_once):
            with self.assertRaisesRegex(OSError, "injected"):
                roles.manage(self.home, "private", mode="team")
        self.assertEqual(self.snapshot(), before)

    def test_shared_role_lock_blocks_both_dry_run_and_writes(self):
        self.home.mkdir()
        lock = self.home / ".agent-roles.lock"
        lock.mkdir()
        for dry_run in (True, False):
            with self.assertRaisesRegex(ValueError, "Another role operation"):
                roles.manage(self.home, "private", mode="team", dry_run=dry_run)
        self.assertTrue(lock.is_dir())
        self.assertEqual(self.snapshot(), {})

    @unittest.skipUnless(os.name == "nt", "Windows junction check")
    def test_namespace_junction_cannot_redirect_profile_writes(self):
        import _winapi
        outside = Path(self.tmp.name) / "outside"
        outside.mkdir()
        sentinel = outside / "fixture.toml"
        sentinel.write_bytes(b"preserve outside role\n")
        agents = self.home / "agents"
        agents.mkdir(parents=True)
        _winapi.CreateJunction(str(outside), str(agents / "codex-profiles"))
        with self.assertRaisesRegex(ValueError, "Linked directory"):
            roles.manage(self.home, "private", mode="team")
        self.assertEqual(list(outside.iterdir()), [sentinel])
        self.assertEqual(sentinel.read_bytes(), b"preserve outside role\n")

    def test_owner_state_rejects_escaping_or_foreign_paths(self):
        manifest = self.legacy_install()
        for name in ("../outside.toml", "codex-config/terra-computer.toml", "codex-profiles/../sol-worker.toml"):
            manifest.write_text(json.dumps({"version": 3, "profile": "private", "mode": "team",
                "owned": {name: "0" * 64}}), encoding="utf-8")
            before = self.snapshot()
            with self.assertRaisesRegex(ValueError, "Unsafe filename or hash"):
                roles.manage(self.home, "private", mode="team")
            self.assertEqual(self.snapshot(), before)


if __name__ == "__main__":
    unittest.main()
