"""Instruction ownership and explicit OpenCode merges in temporary homes only."""
from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import manage_instructions as instructions
import manage_profile as lifecycle
import profile_sources


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

    def source_fixture(self, name, files):
        source = Path(self.tmp.name) / name
        source.mkdir()
        data = profile_sources.load(instructions.ROOT)
        (source / "manifest.json").write_text(json.dumps(data), encoding="utf-8")
        for filename, text in files.items():
            path = source / filename
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        return source

    def test_only_work_profile_splits_instruction_documents_in_both_modes(self):
        for profile in ("private", "work"):
            for mode in ("solo", "team"):
                with self.subTest(profile=profile, mode=mode):
                    self.install(profile, mode)
                    expected = set(instructions.DOCS) if profile == "work" else {"AGENTS.md"}
                    self.assertEqual({p.name for p in self.home.glob("*.md")}, expected)
                    home_text = (self.home / "AGENTS.md").read_text()
                    self.assertIn(f"Active root profile: `{profile}`.", home_text)
                    self.assertNotIn("agent mode:", home_text)
                    self.assertNotIn("work-code", home_text)
                    self.assertEqual("sol_worker" in home_text, profile == "private" and mode == "team")
                    for name in (("WORK.md", "PRIVATE.md") if profile == "work" else ("AGENTS.md",)):
                        text = (self.home / name).read_text()
                        self.assertNotIn("`solo`", text)
                        self.assertNotIn("`team`", text)
                        if mode == "solo":
                            for route in ("sol_worker", "luna_worker", "work-code", "work-scout", "Cursor"):
                                self.assertNotIn(route, text)
                        else:
                            self.assertIn("luna_worker", text)
                    if profile == "private":
                        self.assertNotIn("WORK.md", home_text)
                        self.assertNotIn("PRIVATE.md", home_text)
                        self.assertNotIn("work-scout", home_text)

    def test_solo_assembly_works_without_any_team_sources(self):
        source = self.source_fixture("solo-only-source", {
            "shared/AGENTS.md": "- Common specialist rule.\n",
            "profiles/private/AGENTS.md": "- Fixture profile private.\n",
            "profiles/work/AGENTS.md": "- Fixture profile work.\n- Fixture root rule.\n",
            "modes/solo/AGENTS.md": "- Native behavior fixture.\n",
        })
        with patch.object(instructions, "ROOT", source):
            for profile in ("private", "work"):
                with self.subTest(profile=profile):
                    docs = instructions.desired_docs(profile, "solo")
                    policies = (docs["WORK.md"], docs["PRIVATE.md"]) if profile == "work" else (docs["AGENTS.md"],)
                    for text in policies:
                        self.assertIn("Native behavior fixture.", text)
                        self.assertEqual(text.count("Common specialist rule."), 1)
                    if profile == "private":
                        self.assertIn("Fixture profile private.", docs["AGENTS.md"])
                        self.assertNotIn("Fixture root rule.", docs["AGENTS.md"])
                    else:
                        self.assertIn("Fixture profile work.", docs["AGENTS.md"])
                        self.assertIn("Fixture root rule.", docs["AGENTS.md"])

    def test_team_selects_generic_and_work_sources_without_reading_solo(self):
        source = self.source_fixture("team-only-source", {
            "shared/AGENTS.md": "- Common fixture rule.\n",
            "profiles/private/AGENTS.md": "- Profile fixture private.\n",
            "profiles/work/AGENTS.md": "- Profile fixture work.\n- Metadata fixture.\n",
            "modes/team/AGENTS.md": "- Generic fixture.\n",
            "profiles/work/team-agents-subset.md": "- Corporate fixture.\n",
        })
        generic = source / "modes" / "team" / "AGENTS.md"
        with patch.object(instructions, "ROOT", source):
            work = instructions.desired_docs("work", "team")
            private = instructions.desired_docs("private", "team")
            self.assertIn("Corporate fixture.", work["WORK.md"])
            self.assertNotIn("Generic fixture.", work["WORK.md"])
            self.assertIn("Generic fixture.", work["PRIVATE.md"])
            self.assertNotIn("Corporate fixture.", work["PRIVATE.md"])
            self.assertIn("Generic fixture.", private["AGENTS.md"])
            self.assertNotIn("Corporate fixture.", private["AGENTS.md"])
            self.assertIn("Profile fixture private.", private["AGENTS.md"])
            self.assertNotIn("Metadata fixture.", private["AGENTS.md"])
            self.assertIn("Metadata fixture.", work["AGENTS.md"])
            for text in (work["WORK.md"], work["PRIVATE.md"], private["AGENTS.md"]):
                self.assertEqual(text.count("Common fixture rule."), 1)
            generic.write_text(generic.read_text().replace("Generic fixture.", "Updated fixture."), encoding="utf-8")
            self.assertIn("Updated fixture.", instructions.desired_docs("private", "team")["AGENTS.md"])

    def test_git_history_recognizes_unowned_composed_block_after_source_moves(self):
        source = Path(self.tmp.name) / "historical-repo"
        (source / ".git").mkdir(parents=True)
        old_policy = f"{instructions.BEGIN}\n- Historical generic fixture.\n{instructions.END}"
        old_common = "- Historical shared fixture."
        published = old_policy.replace(instructions.BEGIN, f"{instructions.BEGIN}\n{old_common}", 1)
        published = published.replace(
            instructions.BEGIN,
            f"{instructions.BEGIN}\n- Active root profile: `private`.", 1,
        )
        sources = {"private/agents-subset.md": old_policy, "shared/agents-subset.md": old_common}

        def git(command, **kwargs):
            if command[3] == "log":
                self.assertIn("private/agents-subset.md", command)
                self.assertIn("team/agents-subset.md", command)
                return subprocess.CompletedProcess(command, 0, stdout="fixture-revision\n")
            path = command[4].split(":", 1)[1]
            if path not in sources:
                raise subprocess.CalledProcessError(128, command)
            return subprocess.CompletedProcess(command, 0, stdout=sources[path])

        lifecycle._git_history_blocks.cache_clear()
        self.addCleanup(lifecycle._git_history_blocks.cache_clear)
        (self.home / "AGENTS.md").write_text(published + "\n", encoding="utf-8")
        with patch.object(lifecycle, "ROOT", source), patch.object(lifecycle.shutil, "which", return_value="git"), \
                patch.object(lifecycle.subprocess, "run", side_effect=git):
            self.assertIn(published, lifecycle._known_instruction_blocks())
            plan = instructions.prepare(self.home, "private", "team", legacy_blocks=lifecycle._known_instruction_blocks)
            instructions.commit(plan)
        self.assertIn("sol_worker", (self.home / "AGENTS.md").read_text())
        self.assertNotIn("Historical generic fixture.", (self.home / "AGENTS.md").read_text())

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

    def seed_previous_split_private(self):
        """Reproduce the previously published private layout with recorded ownership."""
        self.install("private", "team")
        previous = {
            "AGENTS.md": (
                f"{instructions.BEGIN}\n- Active root profile: `private`; agent mode: `team`.\n"
                f"- Use the user-selected root model and effort.\n{instructions.END}"
            ),
            "WORK.md": instructions.BEGIN + "\n" + (instructions.ROOT / "profiles/work/team-agents-subset.md").read_text().strip() + "\n" + instructions.END,
            "PRIVATE.md": instructions.BEGIN + "\n" + (instructions.ROOT / "modes/team/AGENTS.md").read_text().strip() + "\n" + instructions.END,
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

class OpenCodeSourceTests(unittest.TestCase):
    def test_scout_has_enforced_deny_by_default_and_code_retains_inherited_permissions(self):
        data = profile_sources.load(instructions.ROOT)
        fragment = json.loads((instructions.ROOT / data["opencode_agents"]).read_text())
        self.assertEqual(set(fragment), {"agent"})
        self.assertEqual(set(fragment["agent"]), {"work-code", "work-scout"})
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
