"""Shared layout and checks for the metal-plugins repository.

Every path and rule the checker and the packager agree on lives here, so
the two cannot drift apart.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

PLUGIN_NAME = "metal"
MARKETPLACE_NAME = "metal"
PLUGIN_SOURCE = "./plugins/metal"

# Hand-written skills live in Claude's default skills/ directory. Skills that
# the Phase 2 sync owns live in synced-skills/, which only the sync writes.
HAND_WRITTEN_SKILLS = "./skills/"
SYNCED_SKILLS = "./synced-skills/"

MCP_CONFIG = {"mcpServers": {"metal": {"type": "http", "url": "https://mcp.metal.ai/mcp"}}}

# claude.ai rejects a skill whose frontmatter has any other key.
ALLOWED_FRONTMATTER_KEYS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}

# The Agent Skills limits for name and description.
SKILL_NAME = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
MAX_NAME_CHARS = 64
MAX_DESCRIPTION_CHARS = 1024

# The metal-skills names the copied skills were renamed from.
LEGACY_SKILL_NAME = re.compile(r"metal-workflow-[a-z-]+")

REFERENCE_MENTION = re.compile(r"references/[A-Za-z0-9_\-./]+")

VERSION = re.compile(r"^\d+\.\d+\.\d+$")


@dataclass
class Layout:
    root: Path = REPO

    @property
    def plugin(self) -> Path:
        return self.root / PLUGIN_SOURCE

    @property
    def claude_manifest(self) -> Path:
        return self.plugin / ".claude-plugin" / "plugin.json"

    @property
    def codex_manifest(self) -> Path:
        return self.plugin / ".codex-plugin" / "plugin.json"

    @property
    def mcp_config(self) -> Path:
        return self.plugin / ".mcp.json"

    @property
    def claude_marketplace(self) -> Path:
        return self.root / ".claude-plugin" / "marketplace.json"

    @property
    def codex_marketplace(self) -> Path:
        return self.root / ".agents" / "plugins" / "marketplace.json"

    def skill_roots(self) -> list[Path]:
        return [self.plugin / HAND_WRITTEN_SKILLS, self.plugin / SYNCED_SKILLS]


@dataclass
class Report:
    errors: list[str] = field(default_factory=list)

    def error(self, where: Path | str, message: str) -> None:
        self.errors.append(f"{where}: {message}")


def load_json(path: Path, report: Report) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        report.error(path, "missing")
    except json.JSONDecodeError as exc:
        report.error(path, f"invalid JSON: {exc}")
    return None


def plugin_version(layout: Layout | None = None) -> str:
    """Return the version both manifests agree on, or raise ValueError."""
    layout = layout or Layout()
    report = Report()
    check_manifests(layout, report)
    if report.errors:
        raise ValueError("\n".join(report.errors))
    return json.loads(layout.claude_manifest.read_text(encoding="utf-8"))["version"]


def release_tag(version: str) -> str:
    # The tag form `claude plugin tag` creates, so version ranges in other
    # plugins' dependencies resolve against it.
    return f"{PLUGIN_NAME}--v{version}"


def check_manifests(layout: Layout, report: Report) -> None:
    claude = load_json(layout.claude_manifest, report)
    codex = load_json(layout.codex_manifest, report)
    if claude is None or codex is None:
        return
    for path, manifest in ((layout.claude_manifest, claude), (layout.codex_manifest, codex)):
        if manifest.get("name") != PLUGIN_NAME:
            report.error(path, f"name must be {PLUGIN_NAME!r}")
        if not VERSION.match(str(manifest.get("version", ""))):
            report.error(path, "version must be MAJOR.MINOR.PATCH")
    if claude.get("version") != codex.get("version"):
        report.error(layout.codex_manifest, f"version {codex.get('version')!r} differs from the Claude manifest's {claude.get('version')!r}")

    # Claude always scans skills/ and adds the listed directories; Codex scans
    # only what it lists. Both must end up with the same skill roots.
    claude_skills = set(as_list(claude.get("skills"))) | {HAND_WRITTEN_SKILLS}
    codex_skills = set(as_list(codex.get("skills")))
    expected = {HAND_WRITTEN_SKILLS, SYNCED_SKILLS}
    if claude_skills != expected:
        report.error(layout.claude_manifest, f"skills must add exactly {SYNCED_SKILLS!r} to the default {HAND_WRITTEN_SKILLS!r}")
    if codex_skills != expected:
        report.error(layout.codex_manifest, f"skills must list exactly {sorted(expected)}")

    # Claude reads .mcp.json at the plugin root by default; Codex needs it named.
    if "mcpServers" in claude:
        report.error(layout.claude_manifest, "mcpServers must be left out so Claude reads .mcp.json")
    if codex.get("mcpServers") != "./.mcp.json":
        report.error(layout.codex_manifest, "mcpServers must be './.mcp.json'")


def check_mcp_config(layout: Layout, report: Report) -> None:
    # An exact match also keeps headers, tokens and other servers out.
    config = load_json(layout.mcp_config, report)
    if config is not None and config != MCP_CONFIG:
        report.error(layout.mcp_config, f"must be exactly {json.dumps(MCP_CONFIG)}")


def check_marketplaces(layout: Layout, report: Report) -> None:
    claude = load_json(layout.claude_marketplace, report)
    if claude is not None:
        if claude.get("name") != MARKETPLACE_NAME:
            report.error(layout.claude_marketplace, f"name must be {MARKETPLACE_NAME!r}")
        entries = claude.get("plugins") or []
        if [(e.get("name"), e.get("source")) for e in entries] != [(PLUGIN_NAME, PLUGIN_SOURCE)]:
            report.error(layout.claude_marketplace, f"plugins must hold one entry {PLUGIN_NAME!r} with source {PLUGIN_SOURCE!r}")

    codex = load_json(layout.codex_marketplace, report)
    if codex is not None:
        if codex.get("name") != MARKETPLACE_NAME:
            report.error(layout.codex_marketplace, f"name must be {MARKETPLACE_NAME!r}")
        entries = codex.get("plugins") or []
        if len(entries) != 1 or entries[0].get("name") != PLUGIN_NAME:
            report.error(layout.codex_marketplace, f"plugins must hold one entry {PLUGIN_NAME!r}")
        else:
            entry = entries[0]
            if entry.get("source") != {"source": "local", "path": PLUGIN_SOURCE}:
                report.error(layout.codex_marketplace, f"source must be the local path {PLUGIN_SOURCE!r}")
            policy = entry.get("policy") or {}
            if not policy.get("installation") or not policy.get("authentication") or not entry.get("category"):
                report.error(layout.codex_marketplace, "the entry needs policy.installation, policy.authentication and category")


def split_frontmatter(text: str) -> tuple[list[str], str] | None:
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---\n", 4)
    if end == -1:
        return None
    return text[4:end].splitlines(), text[end + 5 :]


def frontmatter_fields(lines: list[str]) -> dict[str, str]:
    """Read the top-level keys of a YAML frontmatter block.

    Nested lines, such as the entries of a metadata map, belong to the key
    above them and are not keys themselves.
    """
    fields: dict[str, str] = {}
    for line in lines:
        if not line.strip() or line[0] in " \t#":
            continue
        key, sep, value = line.partition(":")
        if sep:
            fields[key.strip()] = value.strip()
    return fields


def check_skills(layout: Layout, report: Report) -> None:
    seen: dict[str, Path] = {}
    skills = []
    for root in layout.skill_roots():
        if not root.is_dir():
            report.error(root, "skill directory missing")
            continue
        skills.extend(sorted(p for p in root.iterdir() if p.is_dir()))
    for skill in skills:
        check_skill(skill, skills, report)
        if skill.name in seen:
            report.error(skill, f"skill name also used by {seen[skill.name]}")
        seen[skill.name] = skill
    for stray in sorted(layout.plugin.rglob("SKILL.md")):
        if not any(stray.parent.parent == root for root in layout.skill_roots()):
            report.error(stray, "SKILL.md outside skills/<name>/ or synced-skills/<name>/ does not load")


def check_skill(skill: Path, skills: list[Path], report: Report) -> None:
    skill_md = skill / "SKILL.md"
    if not skill_md.is_file():
        report.error(skill, "missing SKILL.md")
        return
    parts = split_frontmatter(skill_md.read_text(encoding="utf-8"))
    if parts is None:
        report.error(skill_md, "must start with a --- frontmatter block")
        return
    lines, _ = parts
    fields = frontmatter_fields(lines)
    for key in sorted(set(fields) - ALLOWED_FRONTMATTER_KEYS):
        report.error(skill_md, f"frontmatter key {key!r} is not one claude.ai accepts ({', '.join(sorted(ALLOWED_FRONTMATTER_KEYS))})")
    name = fields.get("name", "")
    if name != skill.name:
        report.error(skill_md, f"name {name!r} must match its directory {skill.name!r}")
    if not SKILL_NAME.match(name) or len(name) > MAX_NAME_CHARS:
        report.error(skill_md, f"name must be lower-case kebab-case, at most {MAX_NAME_CHARS} characters")
    description = fields.get("description", "")
    if not description or len(description) > MAX_DESCRIPTION_CHARS:
        report.error(skill_md, f"description must be 1 to {MAX_DESCRIPTION_CHARS} characters")
    check_skill_text(skill, skills, report)


def check_skill_text(skill: Path, skills: list[Path], report: Report) -> None:
    for md in sorted(skill.rglob("*.md")):
        for lineno, line in enumerate(md.read_text(encoding="utf-8").splitlines(), 1):
            for legacy in LEGACY_SKILL_NAME.findall(line):
                report.error(f"{md}:{lineno}", f"{legacy!r} is a metal-skills name; use the plugin skill name")
            for mention in REFERENCE_MENTION.findall(line):
                check_reference(skill, skills, mention.rstrip("."), line, f"{md}:{lineno}", report)


def check_reference(skill: Path, skills: list[Path], path: str, line: str, where: str, report: Report) -> None:
    """A references/ path resolves in its own skill, or in a skill the line names.

    A model resolves a bare references/ path against the skill it is reading,
    so a path that exists only in another skill must name that skill.
    """
    if (skill / path).exists():
        return
    owners = [other.name for other in skills if other != skill and (other / path).exists()]
    if not owners:
        report.error(where, f"broken reference {path!r}")
    elif not any(re.search(rf"(?<![\w-]){re.escape(owner)}(?![\w-])", line) for owner in owners):
        report.error(where, f"{path!r} exists only in {', '.join(owners)}; name that skill on the same line")


def check_no_bin(layout: Layout, report: Report) -> None:
    # claude.ai rejects a plugin with a top-level bin/ directory.
    if (layout.plugin / "bin").exists():
        report.error(layout.plugin / "bin", "claude.ai rejects a plugin with a top-level bin/ directory")


def check_all(layout: Layout | None = None) -> list[str]:
    layout = layout or Layout()
    report = Report()
    check_manifests(layout, report)
    check_mcp_config(layout, report)
    check_marketplaces(layout, report)
    check_skills(layout, report)
    check_no_bin(layout, report)
    return report.errors


def as_list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    return list(value)  # type: ignore[arg-type]
