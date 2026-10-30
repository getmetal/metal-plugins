"""Tests for the Codex install check, run against a fake `codex` command.

The fake behaves the way the real Codex CLI does: `plugin add` copies the
whole plugin into CODEX_HOME/plugins/cache/<marketplace>/<plugin>/<version>/,
and `debug prompt-input` lists only the skills in the directories that the
cached Codex manifest names. Each test breaks one thing in a copy of the
repository or in the fake's output.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

import codex_install_check
from plugin_repo import REPO, Layout

FAKE_CODEX = '''
import json, os, shutil, sys
from pathlib import Path
args = sys.argv[1:]
home = Path(os.environ["CODEX_HOME"])
state = home / "fake-marketplace"
cache = home / "plugins" / "cache" / "metal" / "metal"
if args[:3] == ["plugin", "marketplace", "add"]:
    state.write_text(args[3])
elif args[:2] == ["plugin", "add"]:
    plugin = Path(state.read_text()) / "plugins" / "metal"
    version = json.loads((plugin / ".codex-plugin" / "plugin.json").read_text())["version"]
    shutil.copytree(plugin, cache / version)
elif args[:2] == ["debug", "prompt-input"]:
    plugin = next(cache.iterdir())
    roots = json.loads((plugin / ".codex-plugin" / "plugin.json").read_text())["skills"]
    lines = [
        f"- metal:{skill.name}: a description (file: r1/{skill.name}/SKILL.md)"
        for root in roots
        for skill in sorted((plugin / root).iterdir())
        if (skill / "SKILL.md").is_file() and skill.name != os.environ.get("FAKE_HIDE_SKILL")
    ]
    text = "<skills_instructions>\\n## Skills\\n### Available skills\\n" + "\\n".join(lines) + "\\n</skills_instructions>"
    print(json.dumps([{"type": "message", "role": "developer", "content": [{"type": "input_text", "text": text}]}]))
elif args[:3] == ["mcp", "list", "--json"]:
    if os.environ.get("FAKE_FAIL_MCP_LIST"):
        print("boom", file=sys.stderr)
        sys.exit(2)
    servers = json.loads((next(cache.iterdir()) / ".mcp.json").read_text())["mcpServers"]
    print(json.dumps([{"name": n, "enabled": True, "transport": {"url": os.environ.get("FAKE_URL", s["url"])}} for n, s in servers.items()]))
else:
    sys.exit(f"unexpected arguments {args}")
'''


class CodexInstallCheckTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        fake = self.tmp / "fake_codex.py"
        fake.write_text(FAKE_CODEX, encoding="utf-8")
        self.codex = [sys.executable, str(fake)]
        self.home = self.tmp / "home"
        self.home.mkdir()
        self.repo = self.tmp / "repo"
        for name in ("plugins", ".claude-plugin", ".agents"):
            shutil.copytree(REPO / name, self.repo / name)
        self.layout = Layout(self.repo)

    def check(self, **env: str) -> list[str]:
        saved = {k: os.environ.get(k) for k in env}
        os.environ.update(env)
        try:
            errors, _ = codex_install_check.check(self.codex, self.layout, self.home)
            return errors
        finally:
            for k, v in saved.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v

    def test_complete_install_passes(self) -> None:
        self.assertEqual(self.check(), [])

    def test_expected_skills_come_from_the_repository(self) -> None:
        self.assertEqual(codex_install_check.expected_skills(Layout(REPO)), {"skill-library", "workflow-building", "running-workflows", "workflow-debugging"})

    def test_skill_directory_missing_from_codex_manifest_fails(self) -> None:
        # Codex still copies synced-skills/ into its cache, but it does not load it.
        manifest = self.layout.codex_manifest
        data = json.loads(manifest.read_text(encoding="utf-8"))
        data["skills"] = ["./skills/"]
        manifest.write_text(json.dumps(data), encoding="utf-8")
        self.assertEqual(
            self.check(),
            [
                "Codex did not load the skill metal:running-workflows",
                "Codex did not load the skill metal:workflow-building",
                "Codex did not load the skill metal:workflow-debugging",
            ],
        )

    def test_skill_missing_from_prompt_fails(self) -> None:
        self.assertEqual(self.check(FAKE_HIDE_SKILL="workflow-debugging"), ["Codex did not load the skill metal:workflow-debugging"])

    def test_wrong_mcp_url_fails(self) -> None:
        self.assertEqual(
            self.check(FAKE_URL="https://example.test/mcp"),
            ["Codex configured 'metal' with URL 'https://example.test/mcp', not 'https://mcp.metal.ai/mcp'"],
        )

    def test_failed_codex_command_stops_the_check(self) -> None:
        with self.assertRaises(SystemExit) as caught:
            self.check(FAKE_FAIL_MCP_LIST="1")
        self.assertIn("`codex mcp list --json` exited 2", str(caught.exception))

    def test_prompt_skills_reads_only_the_skill_list(self) -> None:
        prompt = [
            {"role": "user", "content": [{"type": "input_text", "text": "- metal:not-a-skill: user text"}]},
            {"role": "developer", "content": [{"type": "input_text", "text": "<skills_instructions>\n- metal:workflow-building: x (file: r1/a)\n- other:skill: y\n</skills_instructions>"}]},
        ]
        self.assertEqual(codex_install_check.prompt_skills(prompt), {"workflow-building"})


if __name__ == "__main__":
    unittest.main()
