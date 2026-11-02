"""Manifest assembly stays equivalent to directly copying declared source files."""
from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import sys
import tempfile
import tomllib
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import manage_instructions as instructions
import manage_profile as lifecycle
import manage_roles as roles
import profile_sources


class ManifestAssemblyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "repo"
        self.root.mkdir()

    def write(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def manifest(self):
        return {
            "schema_version": 1,
            "markers": {"begin": instructions.BEGIN, "end": instructions.END},
            "opencode_agents": "optional/agents.json",
            "profiles": {"synthetic": {
                "custom": {"config": ["base.toml", "overrides.toml"],
                           "roles": ["roles/fixture-checker.toml"],
                           "instructions": {"NOTES.md": ["second.md", "first.md"]}},
                "unused": {"config": ["missing.toml"], "roles": ["missing-role.toml"],
                           "instructions": {"UNUSED.md": ["missing.md"]}},
            }},
        }

    def test_literal_copy_and_concatenation_match_every_published_recipe(self):
        data = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
        for profile, modes in data["profiles"].items():
            for mode, item in modes.items():
                with self.subTest(profile=profile, mode=mode):
                    raw_config = "\n".join((ROOT / name).read_text(encoding="utf-8") for name in item["config"])
                    generated = lifecycle.build_config("", profile, self.root / "home", mode=mode)
                    self.assertEqual(tomllib.loads(generated), tomllib.loads(raw_config))
                    expected_roles = {Path(name).name: (ROOT / name).read_bytes().replace(b"\r\n", b"\n")
                                      for name in item["roles"]}
                    self.assertEqual(roles.desired_roles(profile, mode), expected_roles)
                    docs = instructions.desired_docs(profile, mode)
                    for name, sources in item["instructions"].items():
                        expected = "\n".join((data["markers"]["begin"],
                                              *((ROOT / source).read_text(encoding="utf-8").strip() for source in sources),
                                              data["markers"]["end"]))
                        self.assertEqual(docs[name], expected)
                        self.assertEqual(docs[name].count(data["markers"]["begin"]), 1)
                        self.assertEqual(docs[name].count(data["markers"]["end"]), 1)
                    self.assertTrue(all(text is None for name, text in docs.items() if name not in item["instructions"]))

    def test_arbitrary_profile_mode_roles_documents_and_source_order_are_selected(self):
        self.write("manifest.json", json.dumps(self.manifest()))
        self.write("base.toml", 'model = "fixture-root"\nmodel_reasoning_effort = "high"\n')
        self.write("overrides.toml", '[agents]\nenabled = true\nmax_concurrent_threads_per_session = 9\n')
        self.write("first.md", "- First source.\n")
        self.write("second.md", "- Second source.\n")
        self.write("roles/fixture-checker.toml", 'name = "fixture_checker"\n'
                   'description = "Synthetic role"\nmodel = "fixture-model"\n'
                   'model_reasoning_effort = "high"\ndeveloper_instructions = "Fixture instructions"\n'
                   '[agents]\nenabled = false\n')
        self.assertEqual(roles.normalize_mode("synthetic", None, self.root), "custom")
        self.assertEqual(set(roles.desired_roles("synthetic", "custom", self.root)), {"fixture-checker.toml"})
        with patch.object(lifecycle, "ROOT", self.root), patch.object(instructions, "ROOT", self.root):
            config = tomllib.loads(lifecycle.build_config("", "synthetic", self.root / "home", mode="custom"))
            self.assertEqual(config["agents"]["max_concurrent_threads_per_session"], 9)
            docs = instructions.desired_docs("synthetic", "custom")
            self.assertEqual(docs["NOTES.md"], f"{instructions.BEGIN}\n- Second source.\n- First source.\n{instructions.END}")
            self.assertIsNone(docs["UNUSED.md"])
            self.write("second.md", "- Updated source.\n")
            self.assertIn("Updated source.", instructions.desired_docs("synthetic", "custom")["NOTES.md"])

    def test_manifest_rejects_unsafe_paths_and_recipe_shapes(self):
        original = self.manifest()
        for unsafe in ("../outside.toml", "/absolute.toml", "C:/outside.toml", "dir\\file.toml", "./base.toml"):
            with self.subTest(path=unsafe):
                data = copy.deepcopy(original)
                data["profiles"]["synthetic"]["custom"]["config"] = [unsafe]
                self.write("manifest.json", json.dumps(data))
                with self.assertRaisesRegex(ValueError, "Unsafe manifest source path"):
                    profile_sources.load(self.root)
        data = copy.deepcopy(original)
        data["profiles"]["synthetic"]["custom"]["roles"] = ["a/role.toml", "b/role.toml"]
        self.write("manifest.json", json.dumps(data))
        with self.assertRaisesRegex(ValueError, "Duplicate role destination"):
            profile_sources.load(self.root)
        data = copy.deepcopy(original)
        data["profiles"]["synthetic"]["custom"]["instructions"] = {"../AGENTS.md": ["first.md"]}
        self.write("manifest.json", json.dumps(data))
        with self.assertRaisesRegex(ValueError, "Unsafe manifest source path"):
            profile_sources.load(self.root)

    def test_sources_reject_links_and_directories(self):
        (self.root / "directory.md").mkdir()
        with self.assertRaisesRegex(ValueError, "regular file"):
            profile_sources.source_text(self.root, "directory.md")
        target = Path(self.tmp.name) / "outside.md"
        target.write_text("outside fixture", encoding="utf-8")
        link = self.root / "linked.md"
        try:
            link.symlink_to(target)
        except OSError as exc:
            self.skipTest(f"This Windows account cannot create test symlinks: {exc.winerror}")
        with self.assertRaisesRegex(ValueError, "Linked manifest source"):
            profile_sources.source_text(self.root, "linked.md")

    @unittest.skipUnless(os.name == "nt", "Windows junction check")
    def test_sources_reject_directory_junctions(self):
        import _winapi
        target = Path(self.tmp.name) / "outside"
        target.mkdir()
        (target / "fixture.md").write_text("outside fixture", encoding="utf-8")
        _winapi.CreateJunction(str(target), str(self.root / "linked-dir"))
        with self.assertRaisesRegex(ValueError, "Linked manifest source"):
            profile_sources.source_text(self.root, "linked-dir/fixture.md")


if __name__ == "__main__":
    unittest.main()
