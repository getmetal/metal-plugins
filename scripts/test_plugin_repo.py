"""Tests for the repository checks and the release packager.

Each failure test copies the real repository into a temporary directory,
breaks one thing, and asserts the check reports that thing. Run with
`python3 -m unittest discover -s scripts -p 'test_*.py'`.
"""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path

import package
from plugin_repo import REPO, Layout, check_all, plugin_version, release_tag


class RepoFixture(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        for name in ("plugins", ".claude-plugin", ".agents"):
            shutil.copytree(REPO / name, self.tmp / name)
        shutil.copy(REPO / "LICENSE", self.tmp / "LICENSE")
        self.layout = Layout(self.tmp)
        self.skill_md = self.layout.plugin / "synced-skills" / "workflow-debugging" / "SKILL.md"

    def edit_json(self, path: Path, change) -> None:
        data = json.loads(path.read_text(encoding="utf-8"))
        change(data)
        path.write_text(json.dumps(data), encoding="utf-8")

    def replace(self, path: Path, old: str, new: str) -> None:
        text = path.read_text(encoding="utf-8")
        self.assertIn(old, text)
        path.write_text(text.replace(old, new, 1), encoding="utf-8")

    def assert_error(self, fragment: str) -> None:
        errors = check_all(self.layout)
        self.assertTrue(any(fragment in e for e in errors), f"no error containing {fragment!r} in {errors}")


class RepositoryTest(RepoFixture):
    def test_repository_passes(self) -> None:
        self.assertEqual(check_all(Layout()), [])

    def test_fixture_passes_before_changes(self) -> None:
        self.assertEqual(check_all(self.layout), [])


class ManifestTest(RepoFixture):
    def test_versions_must_agree(self) -> None:
        self.edit_json(self.layout.codex_manifest, lambda m: m.update(version="9.9.9"))
        self.assert_error("differs from the Claude manifest")

    def test_version_must_be_semver(self) -> None:
        self.edit_json(self.layout.claude_manifest, lambda m: m.update(version="latest"))
        self.assert_error("version must be MAJOR.MINOR.PATCH")

    def test_name_must_be_metal(self) -> None:
        self.edit_json(self.layout.claude_manifest, lambda m: m.update(name="other"))
        self.assert_error("name must be 'metal'")

    def test_codex_must_list_both_skill_roots(self) -> None:
        self.edit_json(self.layout.codex_manifest, lambda m: m.update(skills="./skills/"))
        self.assert_error("skills must list exactly")

    def test_claude_must_add_synced_skills(self) -> None:
        self.edit_json(self.layout.claude_manifest, lambda m: m.pop("skills"))
        self.assert_error("skills must add exactly")

    def test_claude_must_not_declare_mcp_servers(self) -> None:
        self.edit_json(self.layout.claude_manifest, lambda m: m.update(mcpServers="./.mcp.json"))
        self.assert_error("mcpServers must be left out")

    def test_codex_must_name_mcp_config(self) -> None:
        self.edit_json(self.layout.codex_manifest, lambda m: m.pop("mcpServers"))
        self.assert_error("mcpServers must be './.mcp.json'")


class McpConfigTest(RepoFixture):
    def test_credentials_are_rejected(self) -> None:
        self.edit_json(self.layout.mcp_config, lambda c: c["mcpServers"]["metal"].update(headers={"Authorization": "Bearer x"}))
        self.assert_error(".mcp.json: must be exactly")

    def test_other_url_is_rejected(self) -> None:
        self.edit_json(self.layout.mcp_config, lambda c: c["mcpServers"]["metal"].update(url="https://staging.example/mcp"))
        self.assert_error(".mcp.json: must be exactly")


class MarketplaceTest(RepoFixture):
    def test_claude_source_must_be_plugin_path(self) -> None:
        self.edit_json(self.layout.claude_marketplace, lambda m: m["plugins"][0].update(source="./elsewhere"))
        self.assert_error("plugins must hold one entry 'metal' with source")

    def test_codex_source_must_be_plugin_path(self) -> None:
        self.edit_json(self.layout.codex_marketplace, lambda m: m["plugins"][0]["source"].update(path="./elsewhere"))
        self.assert_error("source must be the local path")

    def test_codex_entry_needs_policy(self) -> None:
        self.edit_json(self.layout.codex_marketplace, lambda m: m["plugins"][0].pop("policy"))
        self.assert_error("needs policy.installation")

    def test_marketplace_name_must_be_metal(self) -> None:
        self.edit_json(self.layout.codex_marketplace, lambda m: m.update(name="other"))
        self.assert_error("name must be 'metal'")


class SkillTest(RepoFixture):
    def test_frontmatter_key_outside_allow_list(self) -> None:
        self.replace(self.skill_md, "\n---\n", "\nversion: 3.0.8\n---\n")
        self.assert_error("frontmatter key 'version' is not one claude.ai accepts")

    def test_nested_metadata_lines_are_not_keys(self) -> None:
        self.replace(self.skill_md, "\n---\n", "\nmetadata:\n  version: 3.0.8\n---\n")
        self.assertEqual(check_all(self.layout), [])

    def test_name_must_match_directory(self) -> None:
        self.replace(self.skill_md, "name: workflow-debugging", "name: debugging")
        self.assert_error("must match its directory")

    def test_description_required(self) -> None:
        self.replace(self.skill_md, "description: Applies", "description:\nx: Applies")
        self.assert_error("description must be 1 to")

    def test_legacy_name_in_body(self) -> None:
        with self.skill_md.open("a", encoding="utf-8") as f:
            f.write("\nSee metal-workflow-building for edits.\n")
        self.assert_error("'metal-workflow-building' is a metal-skills name")

    def test_legacy_name_in_description(self) -> None:
        self.replace(self.skill_md, "belong to workflow-building", "belong to metal-workflow-building")
        self.assert_error(":3: 'metal-workflow-building' is a metal-skills name")

    def test_legacy_name_in_metadata(self) -> None:
        self.replace(self.skill_md, "\n---\n", "\nmetadata:\n  source: metal-skills skills/metal-workflow-debugging\n---\n")
        self.assert_error(":5: 'metal-workflow-debugging' is a metal-skills name")

    def test_broken_reference(self) -> None:
        self.replace(self.skill_md, "references/workflow-run-diagnosis-rubric.md", "references/missing.md")
        self.assert_error("broken reference 'references/missing.md'")

    def test_sibling_reference_must_name_its_skill(self) -> None:
        with self.skill_md.open("a", encoding="utf-8") as f:
            f.write("\nSee `references/building-tools.md` for the error codes.\n")
        self.assert_error("'references/building-tools.md' exists only in workflow-building; name that skill on the same line")

    def test_sibling_reference_that_names_its_skill_passes(self) -> None:
        with self.skill_md.open("a", encoding="utf-8") as f:
            f.write("\nSee the `workflow-building` skill's `references/building-tools.md` for the error codes.\n")
        self.assertEqual(check_all(self.layout), [])

    def test_duplicate_name_across_roots(self) -> None:
        shutil.copytree(self.skill_md.parent, self.layout.plugin / "skills" / "workflow-debugging")
        self.assert_error("skill name also used by")

    def test_skill_outside_a_skill_root(self) -> None:
        stray = self.layout.plugin / "synced-skills" / "workflow-debugging" / "nested" / "SKILL.md"
        stray.parent.mkdir()
        stray.write_text("---\nname: nested\ndescription: x\n---\n", encoding="utf-8")
        self.assert_error("does not load")

    def test_missing_skill_root(self) -> None:
        shutil.rmtree(self.layout.plugin / "skills")
        self.assert_error("skill directory missing")

    def test_top_level_bin(self) -> None:
        (self.layout.plugin / "bin").mkdir()
        self.assert_error("top-level bin/")


class LicenseTest(RepoFixture):
    def test_plugin_license_must_exist(self) -> None:
        (self.layout.plugin / "LICENSE").unlink()
        self.assert_error("missing; installs carry only the plugin folder")

    def test_plugin_license_must_match_root(self) -> None:
        (self.layout.plugin / "LICENSE").write_text("MIT License\n", encoding="utf-8")
        self.assert_error("must be identical to the repository LICENSE")

    def test_root_license_must_exist(self) -> None:
        (self.tmp / "LICENSE").unlink()
        self.assert_error("LICENSE: missing")

    def test_claude_manifest_names_the_license(self) -> None:
        self.edit_json(self.layout.claude_manifest, lambda m: m.pop("license"))
        self.assert_error("license must be 'Apache-2.0'")


class PackageTest(RepoFixture):
    def test_zip_has_plugin_root_at_top(self) -> None:
        (self.layout.plugin / "synced-skills" / ".DS_Store").write_bytes(b"x")
        target = package.build(self.layout, self.tmp / "dist")
        self.assertEqual(target.name, f"metal-{plugin_version(self.layout)}.zip")
        with zipfile.ZipFile(target) as archive:
            names = archive.namelist()
        self.assertIn(".claude-plugin/plugin.json", names)
        self.assertIn(".mcp.json", names)
        self.assertIn("synced-skills/workflow-debugging/SKILL.md", names)
        self.assertFalse(any(".DS_Store" in n for n in names))
        self.assertFalse(any(n.startswith("plugins/") for n in names))

    def test_zip_is_reproducible(self) -> None:
        first = package.build(self.layout, self.tmp / "a").read_bytes()
        second = package.build(self.layout, self.tmp / "b").read_bytes()
        self.assertEqual(first, second)

    def test_release_tag(self) -> None:
        self.assertEqual(release_tag("1.2.3"), "metal--v1.2.3")

    def test_version_requires_agreeing_manifests(self) -> None:
        self.edit_json(self.layout.codex_manifest, lambda m: m.update(version="9.9.9"))
        with self.assertRaises(ValueError):
            plugin_version(self.layout)


if __name__ == "__main__":
    unittest.main()
