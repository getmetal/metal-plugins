#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Check the plugin manifests, marketplaces, MCP config and skills.

Prints one `path: message` line per problem and exits nonzero if there is
any. Run as `python3 scripts/check.py` or `uv run scripts/check.py`.
"""

from __future__ import annotations

import sys

from plugin_repo import check_all


def main() -> int:
    errors = check_all()
    for error in errors:
        print(error)
    if errors:
        print(f"{len(errors)} problem(s) found", file=sys.stderr)
        return 1
    print("All checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
