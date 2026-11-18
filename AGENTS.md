# metal-plugins

This repository holds the public `metal` plugin for Claude and Codex: the `metal:*` skills, the Metal MCP server config, and the marketplaces that list them. `README.md` describes the layout, the checks and the release process. Read it before you edit here.

`CLAUDE.md` is a symlink to this file.

## Bump the version in every plugin change

Users get a change only when a new version is released. CI publishes a release when a push to `main` carries a manifest version that has no release yet. If the version is already released, CI does nothing, so the change stays unreleased however long it sits on `main`.

- In every pull request that changes a file under `plugins/metal/`, bump the patch version in the same pull request. Do not leave the bump for a later release pull request. Skills, skill references, `.mcp.json` and manifest fields all count.
- Set the same version in both manifests: `plugins/metal/.claude-plugin/plugin.json` and `plugins/metal/.codex-plugin/plugin.json`. `scripts/check.py` fails if they differ.
- Pick the version that follows the latest release. Run `gh release list --limit 1` and add one to its patch number. If another pull request takes that version before yours merges, rebase and bump again.
- After the merge, check that the `release` job of the `Check and release` workflow published `metal--v<version>`, and include the release link in your report.
- A change outside `plugins/metal/`, such as `scripts/`, `README.md` or CI, does not need a bump unless it changes what the release ZIPs contain.

This rule exists because #23, #25 and #26 merged without a bump, and their changes did not reach users until a separate release pull request bumped the version.

## Checks

Run the checks listed in `README.md` under "Checks" before you push. CI runs the same commands on every pull request.
