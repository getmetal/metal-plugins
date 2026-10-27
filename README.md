# metal-plugins

This repository holds the `metal` plugin and a `metal` marketplace for Claude and Codex. Installing the plugin connects the Metal MCP server at `https://mcp.metal.ai/mcp` and adds Metal's workflow skills. Each user signs in to Metal through the MCP server's OAuth flow. The repository contains no credentials.

## Install

Claude Code:

```sh
claude plugin marketplace add getmetal/metal-plugins
claude plugin install metal@metal
```

Codex:

```sh
codex plugin marketplace add getmetal/metal-plugins
codex plugin add metal@metal
```

The repository is private, so each user needs read access to it. A claude.ai admin can instead upload the release zip in Organization settings > Plugins & skills.

## Skills

| Skill | Use |
|---|---|
| `metal:workflow-building` | Inspect or change a workflow definition |
| `metal:running-workflows` | Start, rerun or approve a workflow run |
| `metal:workflow-debugging` | Diagnose why an existing run behaved as it did |

## Layout

| Path | Contents |
|---|---|
| `.claude-plugin/marketplace.json` | The Claude marketplace |
| `.agents/plugins/marketplace.json` | The Codex marketplace |
| `plugins/metal/.claude-plugin/plugin.json` | The Claude manifest |
| `plugins/metal/.codex-plugin/plugin.json` | The Codex manifest |
| `plugins/metal/.mcp.json` | The Metal MCP server, shared by both manifests |
| `plugins/metal/skills/` | Hand-written skills |
| `plugins/metal/generated-skills/` | Skills that the sync from `metal-backend` owns |
| `scripts/` | The repository checks and the release packager |

A sync from `metal-backend` will own `generated-skills/`. For now, the three workflow skills there are copies of metal-skills v3.0.8, renamed to match their `metal-backend` builtins. Each one records its source in its `metadata` frontmatter. Generated versions will replace them.

## Checks

```sh
python3 -m unittest discover -s scripts -p 'test_*.py'
python3 scripts/check.py
claude plugin validate --strict ./plugins/metal
claude plugin validate --strict .
```

`scripts/check.py` checks that:

- both manifests have the same name and version;
- both load the same skill directories and the same `.mcp.json`;
- `.mcp.json` holds only the Metal server;
- each skill's frontmatter uses only the keys that claude.ai accepts: `name`, `description`, `license`, `compatibility`, `metadata` and `allowed-tools`.

CI runs the same commands on every pull request.

## Releases

To release, set the same new `version` in both manifests and merge to `main`. CI then builds `metal-<version>.zip` and publishes it in a GitHub release tagged `metal--v<version>`. If that release already exists, CI does nothing. To build the zip locally, run `python3 scripts/package.py`. The zip holds the plugin directory's contents at its root.
