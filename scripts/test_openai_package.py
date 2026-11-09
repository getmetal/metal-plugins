"""Exercise the generated upload, damaged archives, and the packaging CLI."""

from __future__ import annotations

import json
import subprocess
import sys
import warnings
import zipfile
from pathlib import Path

import openai_package
import package
from plugin_repo import ICON, REPO, plugin_version
from test_plugin_repo import RepoFixture


class OpenAIPackageTest(RepoFixture):
    def contents(self, notes: str | None = None) -> dict[str, bytes]:
        path = package.build_openai(self.layout, self.tmp / "dist", notes)
        with zipfile.ZipFile(path) as archive:
            return {name: archive.read(name) for name in archive.namelist()}

    def test_upload_reuses_shared_content_and_metadata(self) -> None:
        files = self.contents()
        plugin = json.loads(files["plugin.json"])
        codex = json.loads(self.layout.codex_manifest.read_bytes())
        for field in ("name", "version", "description", "author", "repository"):
            self.assertEqual(plugin[field], codex[field])
        self.assertEqual(plugin["extensions"]["com.openai"]["interface"], codex["interface"])
        for source in self.layout.plugin.rglob("*"):
            relative = source.relative_to(self.layout.plugin)
            if source.is_file() and (relative.parts[0] in {"skills", "references", "assets"} or str(relative) in {"README.md", "LICENSE"}):
                self.assertEqual(files[relative.as_posix()], source.read_bytes())
        self.assertIn("references/safety.md", files)
        self.assertIn(ICON[2:], files)
        self.assertEqual(set(plugin), {"$schema", "name", "version", "description", "author", "repository", "homepage", "license", "extensions"})

    def test_oauth_declares_dcr_and_leaves_discovery_to_the_client(self) -> None:
        mcp = json.loads(self.contents()["mcp.json"])
        self.assertEqual(mcp["$schema"], "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json")
        self.assertEqual(mcp["mcpServers"], {
            "metal": {
                "type": "streamable-http", "url": "https://mcp.metal.ai/mcp",
                "extensions": {"com.openai": {"auth": {"type": "oauth", "client": {"mode": "dcr"}}}},
            },
        })

    def test_review_metadata_is_absent_until_prepared(self) -> None:
        extension = json.loads(self.contents()["plugin.json"])["extensions"]["com.openai"]
        self.assertEqual(set(extension), {"interface"})

    def test_release_notes_are_preserved_exactly(self) -> None:
        notes = '## Changes\n\n* Quotes " and café; literal $() and `backticks`.\n'
        extension = json.loads(self.contents(notes)["plugin.json"])["extensions"]["com.openai"]
        self.assertEqual(extension["publication"], {"release_notes": notes})
        self.assertNotIn("review", extension)

    def test_blank_notes_fail_before_writing_a_zip(self) -> None:
        with self.assertRaisesRegex(ValueError, "release notes must not be blank"):
            self.contents(" \n")
        self.assertFalse((self.tmp / "dist").exists())

    def test_archive_name_and_bytes_are_reproducible(self) -> None:
        first = package.build_openai(self.layout, self.tmp / "a", "Release notes\n")
        second = package.build_openai(self.layout, self.tmp / "b", "Release notes\n")
        self.assertEqual(first.name, f"metal-openai-{plugin_version(self.layout)}.zip")
        self.assertEqual(first.read_bytes(), second.read_bytes())
        with zipfile.ZipFile(first) as archive:
            self.assertEqual(archive.namelist(), sorted(archive.namelist()))
            self.assertTrue(all(info.date_time == package.FIXED_TIME for info in archive.infolist()))

    def test_upload_excludes_compatibility_and_unrelated_files(self) -> None:
        for name in (".env", ".app.json", "unrelated.txt", "skills/.DS_Store", "assets/.token"):
            (self.layout.plugin / name).write_text("not public")
        files = self.contents()
        self.assertNotIn(".claude-plugin/plugin.json", files)
        self.assertNotIn(".codex-plugin/plugin.json", files)
        self.assertNotIn(".mcp.json", files)
        self.assertFalse(any("not public" in data.decode("utf-8", errors="ignore") for data in files.values()))

    def test_original_bundle_and_source_are_unchanged(self) -> None:
        before = package.build(self.layout, self.tmp / "before").read_bytes()
        source = self.layout.codex_manifest.read_bytes()
        self.contents("Shared notes\n")
        self.assertEqual(self.layout.codex_manifest.read_bytes(), source)
        self.assertEqual(package.build(self.layout, self.tmp / "after").read_bytes(), before)

    def test_declared_apps_and_hooks_require_explicit_review(self) -> None:
        for key in ("apps", "hooks", "extensions"):
            with self.subTest(key=key):
                original = self.layout.codex_manifest.read_bytes()
                self.edit_json(self.layout.codex_manifest, lambda m: m.update({key: {}}))
                with self.assertRaisesRegex(ValueError, "before public packaging"):
                    self.contents()
                self.layout.codex_manifest.write_bytes(original)

    def test_symlinked_content_is_rejected(self) -> None:
        external = self.tmp / "outside.txt"
        external.write_text("private content")
        (self.layout.plugin / "assets" / "linked.txt").symlink_to(external)
        with self.assertRaisesRegex(ValueError, "must not contain symlinks"):
            self.contents()

    def test_openai_listing_limits_are_checked(self) -> None:
        for key, value in (("displayName", "x" * 31), ("longDescription", "x" * 4001), ("category", "not a category"), ("capabilities", ["x"] * 21), ("developerName", "two\nlines")):
            with self.subTest(key=key):
                original = self.layout.codex_manifest.read_bytes()
                self.edit_json(self.layout.codex_manifest, lambda m: m["interface"].update({key: value}))
                with self.assertRaisesRegex(ValueError, key):
                    self.contents()
                self.layout.codex_manifest.write_bytes(original)

    def test_https_prefix_alone_does_not_pass_url_validation(self) -> None:
        for manifest, field in ((self.layout.claude_manifest, "supportUrl"), (self.layout.codex_manifest, "supportURL")):
            if manifest == self.layout.codex_manifest:
                self.edit_json(manifest, lambda m: m["interface"].update({field: "https://"}))
            else:
                self.edit_json(manifest, lambda m: m.update({field: "https://"}))
        with self.assertRaisesRegex(ValueError, "public HTTPS URL"):
            self.contents()

    def test_saved_archive_detects_lost_shared_reference_and_added_files(self) -> None:
        files = self.contents()
        files.pop("references/safety.md")
        files["hooks/run.sh"] = b"not allowed"
        path = package.write_zip(self.tmp / "damaged.zip", files)
        errors = openai_package.validate_archive(path, self.layout)
        self.assertTrue(any("missing ['references/safety.md']" in error for error in errors), errors)
        self.assertTrue(any("hooks/run.sh" in error for error in errors), errors)

    def test_saved_archive_detects_metadata_drift_and_credentials(self) -> None:
        files = self.contents()
        plugin = json.loads(files["plugin.json"])
        plugin["version"] = "9.9.9"
        files["plugin.json"] = openai_package.json_bytes(plugin)
        mcp = json.loads(files["mcp.json"])
        mcp["mcpServers"]["metal"]["extensions"]["com.openai"]["auth"]["client"]["clientSecret"] = "secret"
        files["mcp.json"] = openai_package.json_bytes(mcp)
        path = package.write_zip(self.tmp / "damaged.zip", files)
        errors = openai_package.validate_archive(path, self.layout)
        self.assertTrue(any("plugin.json: differs" in error for error in errors), errors)
        self.assertTrue(any("no embedded credentials" in error for error in errors), errors)

    def test_portable_schema_rejects_unsupported_fields(self) -> None:
        files = self.contents()
        mcp = json.loads(files["mcp.json"])
        mcp["mcpServers"]["metal"]["command"] = "bad"
        files["mcp.json"] = openai_package.json_bytes(mcp)
        errors = openai_package.validate_files(files, self.layout)
        self.assertTrue(any("not valid under any of the given schemas" in error for error in errors), errors)

    def test_saved_archive_detects_duplicate_paths(self) -> None:
        path = package.build_openai(self.layout, self.tmp / "dist")
        with zipfile.ZipFile(path, "a") as archive, warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            archive.writestr("LICENSE", b"duplicate")
        self.assertIn("OpenAI ZIP contains duplicate paths", openai_package.validate_archive(path, self.layout))


class PackageCliTest(RepoFixture):
    def run_cli(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, str(REPO / "scripts/package.py"), *args], cwd=REPO, text=True, capture_output=True)

    def test_both_formats_share_the_version_and_use_the_supplied_notes(self) -> None:
        notes_path = self.tmp / "release notes.md"
        notes_path.write_text("## Shared notes\n\nLiteral `code` and $HOME.\n", encoding="utf-8")
        dist = self.tmp / "dist"
        result = self.run_cli("--format", "all", "--dist", str(dist), "--release-notes", str(notes_path))
        self.assertEqual(result.returncode, 0, result.stderr)
        version = plugin_version()
        self.assertEqual({p.name for p in dist.iterdir()}, {f"metal-{version}.zip", f"metal-openai-{version}.zip"})
        with zipfile.ZipFile(dist / f"metal-openai-{version}.zip") as archive:
            plugin = json.loads(archive.read("plugin.json"))
        self.assertEqual(plugin["extensions"]["com.openai"]["publication"]["release_notes"], notes_path.read_text())

    def test_missing_notes_file_fails_without_building(self) -> None:
        dist = self.tmp / "dist"
        result = self.run_cli("--format", "all", "--dist", str(dist), "--release-notes", str(self.tmp / "missing.md"))
        self.assertEqual(result.returncode, 1)
        self.assertIn("missing.md", result.stderr)
        self.assertFalse(dist.exists())

    def test_notes_cannot_be_silently_ignored_for_default_format(self) -> None:
        result = self.run_cli("--release-notes", "/unused.md")
        self.assertEqual(result.returncode, 2)
        self.assertIn("requires --format openai or all", result.stderr)
