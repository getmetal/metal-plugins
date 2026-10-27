#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Build the release zip that a claude.ai admin uploads.

The zip holds the plugin directory's contents at its root, so
.claude-plugin/plugin.json is at the top of the archive. Entries are sorted
and carry a fixed timestamp, so the same tree always gives the same bytes.

  python3 scripts/package.py                 build dist/metal-<version>.zip
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
    dist.mkdir(parents=True, exist_ok=True)
    target = dist / f"{PLUGIN_NAME}-{version}.zip"
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in plugin_files(layout.plugin):
            info = zipfile.ZipInfo(path.relative_to(layout.plugin).as_posix(), FIXED_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, path.read_bytes())
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--print-version", action="store_true")
    parser.add_argument("--print-tag", action="store_true")
    parser.add_argument("--dist", type=Path, default=REPO / "dist")
    args = parser.parse_args()

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
    print(build(layout, args.dist))
    return 0


if __name__ == "__main__":
    sys.exit(main())
