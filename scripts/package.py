#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Build the existing release ZIP, the OpenAI submission ZIP, or both.

The existing ZIP holds the plugin directory's contents at its root; the OpenAI
ZIP replaces the compatibility manifests with portable manifests. Entries are
sorted and carry a fixed timestamp, so the same inputs and build environment
produce the same bytes.

  python3 scripts/package.py                 build dist/metal-<version>.zip
  python3 scripts/package.py --format openai build dist/metal-openai-<version>.zip
  python3 scripts/package.py --format all --release-notes /path/to/notes.md
  python3 scripts/package.py --print-version print the plugin version
  python3 scripts/package.py --print-tag     print the release tag
"""

from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path

from plugin_repo import PLUGIN_NAME, REPO, Layout, check_all, plugin_version, release_tag

EXCLUDED_NAMES = {".DS_Store", "__pycache__"}
FIXED_TIME = (1980, 1, 1, 0, 0, 0)


def plugin_files(plugin: Path) -> list[Path]:
    return sorted(
        path
        for path in plugin.rglob("*")
        if path.is_file() and not EXCLUDED_NAMES.intersection(path.relative_to(plugin).parts)
    )


def build(layout: Layout, dist: Path) -> Path:
    version = plugin_version(layout)
    files = {path.relative_to(layout.plugin).as_posix(): path.read_bytes() for path in plugin_files(layout.plugin)}
    return write_zip(dist / f"{PLUGIN_NAME}-{version}.zip", files)


def write_zip(target: Path, files: dict[str, bytes]) -> Path:
    """Use the same order, timestamps and permissions for both formats."""
    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(name, FIXED_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, data)
    return target


def build_openai(layout: Layout, dist: Path, release_notes: str | None = None) -> Path:
    # The existing ZIP and version/tag queries still need only the standard library.
    import openai_package

    files = openai_package.package_files(layout, release_notes)
    target = dist / f"{PLUGIN_NAME}-openai-{plugin_version(layout)}.zip"
    errors = openai_package.validate_files(files, layout, release_notes)
    if errors:
        raise ValueError("\n".join(errors))
    write_zip(target, files)
    # Inspect the actual artifact, including the copied content, before returning it.
    errors = openai_package.validate_archive(target, layout, release_notes)
    if errors:
        target.unlink()
        raise ValueError("\n".join(errors))
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--print-version", action="store_true")
    parser.add_argument("--print-tag", action="store_true")
    parser.add_argument("--format", choices=("default", "openai", "all"), default="default")
    parser.add_argument("--release-notes", type=Path, help="UTF-8 file; also used as the GitHub release body in CI")
    parser.add_argument("--dist", type=Path, default=REPO / "dist")
    args = parser.parse_args()
    if args.release_notes is not None and args.format == "default":
        parser.error("--release-notes requires --format openai or all")

    layout = Layout()
    if args.print_version:
        print(plugin_version(layout))
        return 0
    if args.print_tag:
        print(release_tag(plugin_version(layout)))
        return 0

    errors = check_all(layout)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    try:
        notes = args.release_notes.read_text(encoding="utf-8") if args.release_notes is not None else None
        if args.format in {"openai", "all"}:
            print(build_openai(layout, args.dist, notes))
        if args.format in {"default", "all"}:
            print(build(layout, args.dist))
    except (OSError, ValueError) as exc:
        print(exc, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
