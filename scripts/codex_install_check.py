#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Install the plugin with the Codex CLI and check what Codex loads.

Codex has no validate command, so this installs the plugin from this
repository's marketplace into a temporary CODEX_HOME. It then renders the
prompt Codex would send to the model with `codex debug prompt-input` and
fails unless every skill the repository ships is listed there as
metal:<name>. It also fails unless `codex mcp list` has the Metal MCP server
from .mcp.json. It needs no Codex or Metal credentials.

Codex copies the whole plugin into its cache, so files in the cache do not
show which skills it loads. Only the rendered prompt does.

  python3 scripts/codex_install_check.py [CODEX COMMAND...]

The Codex command defaults to `codex`. CI passes a pinned `npx` command.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from plugin_repo import MARKETPLACE_NAME, MCP_CONFIG, PLUGIN_NAME, REPO, Layout

# One skill entry in the prompt's skill list: "- metal:<name>: <description> (file: ...)".
PROMPT_SKILL = re.compile(rf"^- {re.escape(PLUGIN_NAME)}:([a-z0-9-]+): ", re.MULTILINE)


def expected_skills(layout: Layout) -> set[str]:
    return {skill.name for root in layout.skill_roots() for skill in root.iterdir() if (skill / "SKILL.md").is_file()}


def prompt_skills(prompt_input: list[dict]) -> set[str]:
    """Return the plugin's skill names listed in Codex's rendered prompt."""
    names: set[str] = set()
    for item in prompt_input:
        for content in item.get("content") or []:
            text = content.get("text") or ""
            if "<skills_instructions>" in text:
                names.update(PROMPT_SKILL.findall(text))
    return names


def run(codex: list[str], args: list[str], home: Path) -> str:
    env = {**os.environ, "CODEX_HOME": str(home)}
    # Run from the empty home so no project instructions reach the prompt.
    result = subprocess.run([*codex, *args], env=env, cwd=home, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise SystemExit(f"`codex {' '.join(args)}` exited {result.returncode}:\n{result.stdout}{result.stderr}")
    return result.stdout


def check(codex: list[str], layout: Layout, home: Path) -> tuple[list[str], set[str]]:
    """Return the problems found and the plugin skills Codex loaded."""
    run(codex, ["plugin", "marketplace", "add", str(layout.root)], home)
    run(codex, ["plugin", "add", f"{PLUGIN_NAME}@{MARKETPLACE_NAME}"], home)

    errors = []
    expected = expected_skills(layout)
    loaded = prompt_skills(json.loads(run(codex, ["debug", "prompt-input"], home)))
    if not expected:
        errors.append("the repository ships no skills")
    for name in sorted(expected - loaded):
        errors.append(f"Codex did not load the skill {PLUGIN_NAME}:{name}")
    for name in sorted(loaded - expected):
        errors.append(f"Codex loaded {PLUGIN_NAME}:{name}, which the repository does not ship")

    servers = {s["name"]: s for s in json.loads(run(codex, ["mcp", "list", "--json"], home))}
    for name, config in MCP_CONFIG["mcpServers"].items():
        server = servers.get(name)
        if server is None:
            errors.append(f"Codex did not configure the MCP server {name!r}; it has {sorted(servers)}")
            continue
        url = (server.get("transport") or {}).get("url")
        if url != config["url"]:
            errors.append(f"Codex configured {name!r} with URL {url!r}, not {config['url']!r}")
        if not server.get("enabled"):
            errors.append(f"Codex configured {name!r} but it is disabled: {server.get('disabled_reason')}")

    return errors, loaded


def main() -> int:
    codex = sys.argv[1:] or ["codex"]
    with tempfile.TemporaryDirectory() as home:
        errors, loaded = check(codex, Layout(REPO), Path(home))
    for error in errors:
        print(error)
    if errors:
        return 1
    skills = ", ".join(f"{PLUGIN_NAME}:{name}" for name in sorted(loaded))
    print(f"Codex loaded {len(loaded)} skills ({skills}) and the MCP server(s) {', '.join(MCP_CONFIG['mcpServers'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
