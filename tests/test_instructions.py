"""Instruction ownership and explicit OpenCode merges in temporary homes only."""
from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import manage_instructions as instructions
import manage_profile as lifecycle


class InstructionLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name) / "home"
        self.home.mkdir()

    def install(self, profile="work", mode="team", **kwargs):
        return lifecycle.apply(self.home, profile, mode=mode, **kwargs)

    def snapshot(self):
        return {str(path.relative_to(self.home)): path.read_bytes()
                for path in self.home.rglob("*") if path.is_file()}

    def config_block(self, name="AGENTS.md", value="shared"):
        return f"{instructions.CONFIG_BEGIN}\n<!-- codex-config:source {name} -->\n{value}\n{instructions.CONFIG_END}"

    def opencode(self, agents=None):
        path = Path(self.tmp.name) / "opencode.json"
        path.write_text(json.dumps({
            "provider": {"synthetic": {"options": {"apiKey": "{env:TEST_ONLY_KEY}"}}},
            "permission": {"bash": "ask"}, "model": "unchanged/model",
            "agent": agents if agents is not None else {"existing": {"model": "keep/model"}},
        }), encoding="utf-8")
        return path

    def test_only_work_profile_splits_instruction_documents_in_both_modes(self):
        for profile in ("private", "work"):
            for mode in ("solo", "team"):
                with self.subTest(profile=profile, mode=mode):
                    self.install(profile, mode)
                    expected = set(instructions.DOCS) if profile == "work" else {"AGENTS.md"}
                    self.assertEqual({p.name for p in self.home.glob("*.md")}, expected)
                    home_text = (self.home / "AGENTS.md").read_text()
                    self.assertIn(f"`{profile}`; agent mode: `{mode}`", home_text)
                    self.assertNotIn("work-code", home_text)
                    self.assertEqual("sol_worker" in home_text, profile == "private")
                    for name in (("WORK.md", "PRIVATE.md") if profile == "work" else ("AGENTS.md",)):
                        text = (self.home / name).read_text()
                        self.assertIn("In `solo` mode, retain native Codex delegation behavior", text)
                        self.assertIn("In `team` mode, delegate useful independent work", text)
                    if profile == "private":
                        self.assertNotIn("WORK.md", home_text)
                        self.assertNotIn("PRIVATE.md", home_text)
                        self.assertNotIn("work-scout", home_text)

    def test_block_order_preserves_config_and_user_prose_in_both_manager_orders(self):
        # Config first, profiles second.
        for name in instructions.DOCS:
            (self.home / name).write_text("user prefix\n\n" + self.config_block(name) + "\n\nuser suffix\n")
        self.install()
        for name in instructions.DOCS:
            path = self.home / name
            text = path.read_text()
            self.assertIn(self.config_block(name), text)
            self.assertIn("user prefix", text)
            self.assertIn("user suffix", text)
            self.assertLess(text.index(instructions.CONFIG_END), text.index(instructions.BEGIN))
            # The other manager updates its own block and user text changes too.
            path.write_text(text.replace("shared", "new shared").replace("user suffix", "new suffix"))
        lifecycle.sync_instructions(self.home)
        self.assertEqual(instructions.status(self.home)["changed_blocks"], [])
        for name in instructions.DOCS:
            self.assertIn("new shared", (self.home / name).read_text())
            self.assertIn("new suffix", (self.home / name).read_text())
        # Profiles first, config later, as produced by an independent manager.
        for name in instructions.DOCS:
            path = self.home / name
            own = instructions.block(path.read_text())
            path.write_text("user prefix\n\n" + own + "\n\n" + self.config_block(name) + "\n\nuser suffix\n")
        lifecycle.sync_instructions(self.home)
        for name in instructions.DOCS:
            text = (self.home / name).read_text()
            self.assertLess(text.index(instructions.CONFIG_END), text.index(instructions.BEGIN))
            self.assertIn("user suffix", text)

    def test_sync_preserves_root_config_roles_and_role_state_byte_for_byte(self):
        self.install()
        config = self.home / "config.toml"
        config.write_text(config.read_text().replace('model = "gpt-6.1-sol"', 'model = "user-selected"')
                          + '\n[mcp_servers.synthetic]\nurl = "http://example.invalid"\n')
        (self.home / "agents" / "sol-worker.toml").write_text("user edited role; sync must not inspect or overwrite\n")
        (self.home / "agents" / "custom.toml").write_text("custom role\n")
        auth = self.home / "auth.json"
        auth.write_text('{"synthetic": "test data"}')
        before = self.snapshot()
        lifecycle.sync_instructions(self.home)
        self.assertEqual(before, self.snapshot())

    def test_sync_migrates_legacy_agents_without_touching_any_other_file(self):
        self.install("private", "solo")
        (self.home / "profiles" / instructions.STATE).unlink()
        legacy = next(value for value in lifecycle._git_history_blocks() if value.startswith(instructions.BEGIN))
        (self.home / "AGENTS.md").write_text("user\n\n" + legacy)
        (self.home / "WORK.md").unlink(missing_ok=True)
        (self.home / "PRIVATE.md").unlink(missing_ok=True)
        before = self.snapshot()
        result = lifecycle.sync_instructions(self.home)
        self.assertEqual(result["profile"], "private")
        self.assertEqual(result["mode"], "solo")
        after = self.snapshot()
        for name, data in before.items():
            if name != "AGENTS.md":
                self.assertEqual(after[name], data)
        self.assertIn("user", (self.home / "AGENTS.md").read_text())
        self.assertNotIn(legacy, (self.home / "AGENTS.md").read_text())

    def seed_previous_split_private(self):
        """Reproduce the previously published private layout with recorded ownership."""
        self.install("private", "team")
        previous = {
            "AGENTS.md": instructions.metadata("private", "team"),
            "WORK.md": instructions.block((instructions.ROOT / "work/agents-subset.md").read_text()),
            "PRIVATE.md": instructions.block((instructions.ROOT / "private/agents-subset.md").read_text()),
        }
        for name, content in previous.items():
            (self.home / name).write_text(content + "\n", encoding="utf-8")
        state = instructions.load_state(self.home)
        state["owned"] = {name: instructions.digest(value) for name, value in previous.items()}
        (self.home / "profiles" / instructions.STATE).write_text(json.dumps(state), encoding="utf-8")

    def test_private_sync_migrates_recorded_split_layout_without_changing_settings_or_roles(self):
        self.seed_previous_split_private()
        before = self.snapshot()
        result = lifecycle.sync_instructions(self.home)
        self.assertEqual(result["profile"], "private")
        self.assertEqual(result["mode"], "team")
        after = self.snapshot()
        changed = {"AGENTS.md", "WORK.md", "PRIVATE.md", "profiles/" + instructions.STATE}
        for name, data in before.items():
            if Path(name).as_posix() not in changed:
                self.assertEqual(after[name], data)
        self.assertIn("sol_worker", (self.home / "AGENTS.md").read_text())
        self.assertFalse((self.home / "WORK.md").exists())
        self.assertFalse((self.home / "PRIVATE.md").exists())
        self.assertEqual(set(instructions.load_state(self.home)["owned"]), {"AGENTS.md"})
        self.assertEqual(instructions.status(self.home)["changed_blocks"], [])
        settled = self.snapshot()
        lifecycle.sync_instructions(self.home)
        self.assertEqual(self.snapshot(), settled)

    def test_private_migration_preserves_foreign_blocks_and_user_prose_in_sidecars(self):
        self.seed_previous_split_private()
        for name in instructions.DOCS:
            path = self.home / name
            path.write_text("user prefix\n\n" + self.config_block(name) + "\n\n"
                            + path.read_text() + "\nuser suffix\n")
        lifecycle.sync_instructions(self.home)
        for name in instructions.DOCS:
            text = (self.home / name).read_text()
            self.assertIn(self.config_block(name), text)
            self.assertIn("user prefix", text)
            self.assertIn("user suffix", text)
            if name == "AGENTS.md":
                self.assertIn("sol_worker", text)
                self.assertLess(text.index(instructions.CONFIG_END), text.index(instructions.BEGIN))
            else:
                self.assertNotIn(instructions.BEGIN, text)

    def test_private_migration_refuses_edited_sidecar_before_any_write(self):
        self.seed_previous_split_private()
        path = self.home / "WORK.md"
        path.write_text(path.read_text().replace("work-code", "user-edited-route"))
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, "instruction block changed"):
            lifecycle.sync_instructions(self.home)
        self.assertEqual(self.snapshot(), before)

    def test_private_sync_preserves_unmanaged_sidecars(self):
        self.install("private", "solo")
        for name in ("WORK.md", "PRIVATE.md"):
            (self.home / name).write_text("unmanaged user document\n")
        before = self.snapshot()
        lifecycle.sync_instructions(self.home)
        self.assertEqual(self.snapshot(), before)

    def test_unowned_modified_legacy_block_is_not_adopted(self):
        self.install()
        (self.home / "profiles" / instructions.STATE).unlink()
        path = self.home / "AGENTS.md"
        path.write_text(instructions.BEGIN + "\nuser-customized old route\n" + instructions.END)
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, "Unowned instruction block collision"):
            lifecycle.sync_instructions(self.home)
        self.assertEqual(before, self.snapshot())

    def test_modified_owned_block_refuses_sync_install_and_remove_before_any_write(self):
        for name in instructions.DOCS:
            with self.subTest(name=name):
                self.home = Path(self.tmp.name) / name.replace(".md", "")
                self.install()
                path = self.home / name
                path.write_text(path.read_text().replace(instructions.BEGIN, instructions.BEGIN + "\nuser edit", 1))
                before = self.snapshot()
                for action in (lambda: lifecycle.sync_instructions(self.home), lambda: self.install(),
                               lambda: lifecycle.apply(self.home, None)):
                    with self.assertRaisesRegex(ValueError, "instruction block changed"):
                        action()
                    self.assertEqual(before, self.snapshot())

    def test_remove_only_owned_blocks_preserves_other_manager_and_user_text(self):
        self.install()
        for name in instructions.DOCS:
            path = self.home / name
            path.write_text(self.config_block(name) + "\n\n" + path.read_text() + "\nuser added\n")
        lifecycle.apply(self.home, None)
        for name in instructions.DOCS:
            text = (self.home / name).read_text()
            self.assertIn(self.config_block(name), text)
            self.assertIn("user added", text)
            self.assertNotIn(instructions.BEGIN, text)
        self.assertFalse((self.home / "profiles" / instructions.STATE).exists())

    def test_remove_deletes_empty_sidecars(self):
        self.install()
        lifecycle.apply(self.home, None)
        self.assertFalse(any((self.home / name).exists() for name in instructions.DOCS))

    def test_sync_dry_run_and_cli_keep_all_bytes(self):
        self.install()
        before = self.snapshot()
        args = ["manage_profile.py", "--home", str(self.home), "sync-instructions", "--dry-run"]
        with patch.object(sys, "argv", args), redirect_stdout(StringIO()):
            self.assertEqual(lifecycle.main(), 0)
        self.assertEqual(before, self.snapshot())

    def test_sync_requires_installed_profile(self):
        with self.assertRaisesRegex(ValueError, "Install a supported managed profile"):
            lifecycle.sync_instructions(self.home)
        self.assertEqual(self.snapshot(), {})

    def test_opencode_merge_and_removal_preserve_providers_globals_other_agents(self):
        path = self.opencode()
        original = json.loads(path.read_text())
        self.install(opencode_config=path)
        merged = json.loads(path.read_text())
        for key in ("provider", "permission", "model"):
            self.assertEqual(merged[key], original[key])
        self.assertEqual(merged["agent"]["existing"], original["agent"]["existing"])
        self.assertEqual(set(merged["agent"]), {"existing", "work-code", "work-scout"})
        stored = (self.home / "profiles" / instructions.STATE).read_text()
        self.assertNotIn("apiKey", stored)
        self.assertNotIn("provider", stored)
        self.assertNotIn("TEST_ONLY_KEY", stored)
        before = path.read_bytes()
        lifecycle.sync_instructions(self.home, opencode_config=path)
        self.assertEqual(before, path.read_bytes())
        lifecycle.apply(self.home, None, opencode_config=path)
        self.assertEqual(json.loads(path.read_text()), original)

    def test_opencode_not_touched_without_explicit_path(self):
        path = self.opencode()
        self.install(opencode_config=path)
        before = path.read_bytes()
        lifecycle.sync_instructions(self.home)
        lifecycle.apply(self.home, None)
        self.assertEqual(path.read_bytes(), before)
        self.assertIsNotNone(instructions.load_state(self.home)["opencode"])
        lifecycle.apply(self.home, None, opencode_config=path)
        self.assertNotIn("work-code", json.loads(path.read_text())["agent"])

    def test_opencode_unowned_or_modified_named_agent_refuses_update(self):
        path = self.opencode({"work-scout": {"model": "user/model"}})
        original = path.read_bytes()
        with self.assertRaisesRegex(ValueError, "Unowned OpenCode agent collision"):
            self.install(opencode_config=path)
        self.assertEqual(path.read_bytes(), original)
        self.assertEqual(self.snapshot(), {})
        path = self.opencode()
        self.install(opencode_config=path)
        data = json.loads(path.read_text())
        data["agent"]["work-code"]["model"] = "user/model"
        path.write_text(json.dumps(data))
        before = self.snapshot()
        for action in (lambda: lifecycle.sync_instructions(self.home, opencode_config=path),
                       lambda: lifecycle.apply(self.home, None, opencode_config=path)):
            with self.assertRaisesRegex(ValueError, "Managed OpenCode agent changed"):
                action()
            self.assertEqual(before, self.snapshot())

    def test_opencode_dry_run_and_missing_path(self):
        path = self.opencode()
        original = path.read_bytes()
        self.install(opencode_config=path, dry_run=True)
        self.assertEqual(path.read_bytes(), original)
        self.assertEqual(self.snapshot(), {})
        with self.assertRaisesRegex(ValueError, "existing JSON"):
            self.install(opencode_config=Path(self.tmp.name) / "absent.json")

    def test_instruction_write_failure_rolls_back_full_lifecycle(self):
        self.install()
        before = self.snapshot()
        real = instructions.write
        calls = 0

        def fail_once(path, data):
            nonlocal calls
            calls += 1
            if calls == 1:
                raise OSError("injected instruction failure")
            real(path, data)

        with patch.object(instructions, "write", side_effect=fail_once):
            with self.assertRaisesRegex(OSError, "injected"):
                self.install("private", "solo")
        self.assertEqual(before, self.snapshot())

    def test_owned_legacy_cap_is_migrated_to_canonical_key(self):
        self.install()
        path = self.home / "config.toml"
        path.write_text(path.read_text().replace("max_concurrent_threads_per_session", "max_threads"))
        self.install()
        text = path.read_text()
        self.assertIn("max_concurrent_threads_per_session = 3", text)
        self.assertNotIn("max_threads", text)

    def test_unowned_legacy_cap_is_preserved_by_refusal(self):
        path = self.home / "config.toml"
        path.write_text("[agents]\nmax_threads = 5\n")
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, "Unowned legacy"):
            self.install()
        self.assertEqual(before, self.snapshot())


class OpenCodeSourceTests(unittest.TestCase):
    def test_scout_has_enforced_deny_by_default_and_code_retains_inherited_permissions(self):
        fragment = json.loads((instructions.ROOT / "work" / "opencode-agents.json").read_text())
        self.assertEqual(set(fragment), {"agent"})
        self.assertEqual(set(fragment["agent"]), instructions.AGENT_NAMES)
        scout = fragment["agent"]["work-scout"]
        code = fragment["agent"]["work-code"]
        self.assertEqual(scout["mode"], "primary")
        self.assertEqual(scout["model"], "litellm/corp-code-fast")
        self.assertEqual(scout["steps"], 16)
        permission = scout["permission"]
        self.assertEqual(permission["*"], "deny")
        self.assertEqual(permission["read"]["*"], "allow")
        self.assertEqual(permission["read"]["**/.env.*"], "deny")
        for tool in ("write", "edit", "bash", "shell", "task", "skill"):
            self.assertEqual(permission[tool], "deny")
        for tool in ("glob", "grep"):
            self.assertEqual(permission[tool], "allow")
        self.assertEqual(code["model"], "litellm/global.openai.gpt-6-luna")
        self.assertEqual(code["mode"], "primary")
        self.assertEqual(code["permission"], {"task": "deny", "skill": "deny"})


if __name__ == "__main__":
    unittest.main()
