"""Generate and validate the public OpenAI upload from the shared plugin source.

Builds are offline. OAuth discovery was checked on 2026-11-09: Metal advertises
DCR and S256 at /.well-known/oauth-authorization-server; its protected resource
also points to an authorization server that advertises DCR. Let discovery supply
the endpoints and scopes instead of copying them into another configuration.
"""

from __future__ import annotations

import json
import stat
import zipfile
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit

from plugin_repo import CODEX_LINKS, ICON, LICENSE_SPDX, Layout, check_all

SCHEMAS = Path(__file__).with_name("schemas")
SCHEMA_BASE = "https://agent-plugins.org/schemas/1.0.0/"
CONTENT_DIRS = {"skills", "references", "assets"}
CONTENT_FILES = {"README.md", "LICENSE"}
OAUTH = {"com.openai": {"auth": {"type": "oauth", "client": {"mode": "dcr"}}}}
CATEGORIES = [
    "Business & Operations", "Communication", "Creativity", "Data & Analytics",
    "Developer Tools", "Education & Research", "Entertainment", "Finance",
    "Healthcare", "Other", "Productivity", "Scientific Research", "Security", "Travel",
]


def text_field(limit: int) -> dict:
    return {
        "type": "string", "minLength": 1, "maxLength": limit, "pattern": r"\S",
        "not": {"pattern": r"[\x00-\x1f\x7f\u2028\u2029]"},
    }


# The portable plugin schema treats client extensions as opaque. These are the
# additional listing constraints documented by OpenAI's submission reference.
INTERFACE_SCHEMA = {
    "type": "object",
    "required": [
        "displayName", "shortDescription", "longDescription", "developerName", "category",
        "capabilities", "logo", "composerIcon", *CODEX_LINKS,
    ],
    "properties": {
        "displayName": text_field(30),
        "shortDescription": text_field(30),
        "longDescription": {"type": "string", "minLength": 1, "maxLength": 4000, "pattern": r"\S"},
        "developerName": text_field(80),
        "category": {"enum": CATEGORIES},
        "capabilities": {"type": "array", "maxItems": 20, "items": text_field(120)},
        **{key: {"type": "string", "pattern": "^https://", "maxLength": 1024} for key in CODEX_LINKS},
        **{key: {"type": "string", "pattern": r"^\./"} for key in ("logo", "composerIcon", "logoDark", "composerIconDark")},
        "defaultPrompt": {
            "oneOf": [text_field(128), {"type": "array", "maxItems": 3, "uniqueItems": True, "items": text_field(128)}],
        },
        "brandColor": {"type": "string", "pattern": "^#[0-9a-fA-F]{6}$"},
        "brandColorDark": {"type": "string", "pattern": "^#[0-9a-fA-F]{6}$"},
    },
    "additionalProperties": False,
}


def json_bytes(value: dict) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def manifests(layout: Layout, release_notes: str | None) -> tuple[dict, dict]:
    codex = json.loads(layout.codex_manifest.read_text(encoding="utf-8"))
    claude = json.loads(layout.claude_manifest.read_text(encoding="utf-8"))
    for source in (codex, claude):
        if any(key in source for key in ("apps", "hooks", "extensions")):
            raise ValueError("Review apps, hooks or extensions in the source manifest before public packaging")
    if release_notes is not None and not release_notes.strip():
        raise ValueError("release notes must not be blank")
    extension = {"interface": codex["interface"]}
    if release_notes is not None:
        extension["publication"] = {"release_notes": release_notes}
    plugin = {
        "$schema": SCHEMA_BASE + "plugin.schema.json",
        **{key: codex[key] for key in ("name", "version", "description", "author", "repository")},
        "homepage": claude["homepage"],
        "license": LICENSE_SPDX,
        "extensions": {"com.openai": extension},
    }
    servers = json.loads(layout.mcp_config.read_text(encoding="utf-8"))["mcpServers"]
    mcp = {
        "$schema": SCHEMA_BASE + "mcp.schema.json",
        "mcpServers": {
            name: {"type": "streamable-http", "url": server["url"], "extensions": OAUTH}
            for name, server in servers.items()
        },
    }
    return plugin, mcp


def package_files(layout: Layout, release_notes: str | None = None) -> dict[str, bytes]:
    """Select only public content; keep compatibility manifests in the other ZIP."""
    errors = check_all(layout)
    if errors:
        raise ValueError("\n".join(errors))
    plugin, mcp = manifests(layout, release_notes)
    files = {"plugin.json": json_bytes(plugin), "mcp.json": json_bytes(mcp)}
    for path in sorted(layout.plugin.rglob("*")):
        relative = path.relative_to(layout.plugin)
        if relative.parts[0] not in CONTENT_DIRS and relative.as_posix() not in CONTENT_FILES:
            continue
        if any(part.startswith(".") or part == "__pycache__" for part in relative.parts):
            continue
        if path.is_symlink():
            raise ValueError(f"{path}: public upload must not contain symlinks")
        if path.is_file():
            files[relative.as_posix()] = path.read_bytes()
    return files


def schema_errors(instance: dict, schema: dict, where: str) -> list[str]:
    try:
        from jsonschema import Draft202012Validator
    except ImportError as exc:
        raise ValueError("Install the packaging dependencies: python3 -m pip install -r scripts/requirements.txt") from exc
    return [
        f"{where}{''.join('/' + str(part) for part in error.absolute_path)}: {error.message}"
        for error in Draft202012Validator(schema).iter_errors(instance)
    ]


def validate_files(files: dict[str, bytes], layout: Layout, release_notes: str | None = None) -> list[str]:
    errors = []
    expected = package_files(layout, release_notes)
    if files.keys() != expected.keys():
        errors.append(f"OpenAI ZIP inventory: missing {sorted(expected.keys() - files.keys())}, extra {sorted(files.keys() - expected.keys())}")
    for name in files.keys() & expected.keys():
        if files[name] != expected[name]:
            errors.append(f"{name}: differs from the shared source or generated metadata")
    documents = {}
    for name in ("plugin.json", "mcp.json"):
        try:
            documents[name] = json.loads(files[name])
        except (KeyError, ValueError, UnicodeDecodeError) as exc:
            errors.append(f"{name}: missing or invalid JSON ({exc})")
    if len(documents) != 2:
        return errors
    plugin, mcp = documents["plugin.json"], documents["mcp.json"]
    errors.extend(schema_errors(plugin, json.loads((SCHEMAS / "plugin.schema.json").read_text()), "plugin.json"))
    # The published Agent Plugins 1.0 MCP schema does not declare the per-server
    # OpenAI auth extension and rejects it. Validate the portable fields unchanged and
    # validate the documented OAuth extension separately, without weakening the
    # vendored schema or allowing arbitrary credentials/headers through it.
    portable_mcp = json.loads(json.dumps(mcp))
    servers = portable_mcp.get("mcpServers", {}) if isinstance(portable_mcp, dict) else {}
    if isinstance(servers, dict):
        for name, server in servers.items():
            if isinstance(server, dict) and server.pop("extensions", None) != OAUTH:
                errors.append(f"mcp.json/{name}: requires OAuth with DCR and no embedded credentials")
    errors.extend(schema_errors(portable_mcp, json.loads((SCHEMAS / "mcp.schema.json").read_text()), "mcp.json"))
    if not isinstance(plugin, dict):
        return errors
    extensions = plugin.get("extensions", {})
    extension = extensions.get("com.openai", {}) if isinstance(extensions, dict) else {}
    interface = extension.get("interface", {}) if isinstance(extension, dict) else {}
    errors.extend(schema_errors(interface, INTERFACE_SCHEMA, "plugin.json/interface"))
    if not isinstance(interface, dict):
        return errors
    for key in CODEX_LINKS:
        url = interface.get(key)
        if not isinstance(url, str):
            continue
        try:
            parsed = urlsplit(url)
            if parsed.scheme != "https" or not parsed.hostname or parsed.username is not None or parsed.password is not None or any(c.isspace() for c in url):
                raise ValueError("requires a public HTTPS URL without credentials or whitespace")
        except ValueError as exc:
            errors.append(f"plugin.json/interface/{key}: {exc}")
    for key in ("logo", "composerIcon", "logoDark", "composerIconDark"):
        if key not in interface:
            continue
        value = interface[key]
        if not isinstance(value, str) or not value.startswith("./") or ".." in PurePosixPath(value).parts or value[2:] not in files:
            errors.append(f"plugin.json/interface/{key}: must reference a contained file in the ZIP")
    # Current sources share the validated square PNG. New assets need an
    # explicit update to these checks rather than silently bypassing icon QA.
    for key in ("logo", "composerIcon"):
        if interface.get(key) != ICON:
            errors.append(f"plugin.json/interface/{key}: must reuse the shared icon {ICON}")
    return errors


def validate_archive(path: Path, layout: Layout, release_notes: str | None = None) -> list[str]:
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        errors = []
        if len(names) != len(set(names)):
            errors.append("OpenAI ZIP contains duplicate paths")
        if any(stat.S_ISLNK(info.external_attr >> 16) for info in archive.infolist()):
            errors.append("OpenAI ZIP contains symlinks")
        errors.extend(validate_files({name: archive.read(name) for name in names}, layout, release_notes))
        return errors
