# metal-plugins

This repository holds the `metal` plugin and a `metal` marketplace for Claude, Codex and ChatGPT. Installing the plugin connects the Metal MCP server at `https://mcp.metal.ai/mcp` and adds Metal's workflow skills. Each user signs in to Metal through the MCP server's OAuth flow. The repository contains no credentials.

## Install

The Claude, Codex and ChatGPT desktop apps are the supported surfaces. These steps follow each vendor's documentation; a full install guide, tested on each app, is in progress.

**Claude desktop app (chat and Cowork):** open Customize > Plugins, select Add > Add marketplace, and enter `getmetal/metal-plugins`. Add the Metal plugin, then open its Connectors tab and connect Metal.

**Codex:** add the marketplace and install the plugin. From a terminal:

```sh
codex plugin marketplace add getmetal/metal-plugins
codex plugin add metal@metal
```

**ChatGPT Business or Enterprise:** a workspace admin imports the marketplace in Admin > Plugins > Add > Import marketplace, and authorizes a GitHub account to read this public repository. ChatGPT marks a plugin that declares an MCP server as Desktop only, so the plugin works in the ChatGPT desktop app and not in ChatGPT on the web. See OpenAI's [plugin management](https://learn.chatgpt.com/docs/enterprise/plugin-management) page.

**Claude Code:**

```sh
claude plugin marketplace add getmetal/metal-plugins
claude plugin install metal@metal
```

**Claude organizations:** claude.ai's organization sync accepts only private or internal repositories, so an Owner cannot sync this repository directly. An Owner can upload the release zip in Organization settings > Plugins & skills, or sync a private marketplace repository that lists this plugin as its source.

Members who receive the plugin from an admin need no GitHub account. Each member signs in to Metal with their own account.

## Skills

| Skill | Use |
|---|---|
| `metal:org-skills` | Find and follow the organization's own skills in Metal's skill library |
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
| `plugins/metal/synced-skills/` | Skills that the sync from `metal-backend` owns |
| `scripts/` | The repository checks and the release packager |

A sync from `metal-backend` will own `synced-skills/`. For now, the three workflow skills there started as copies of metal-skills v3.0.8 (`7fa35e5`), renamed to match their `metal-backend` builtins. They were then corrected against `metal-backend` at `69795bf`. The domain packs in `workflow-building/references/domains/` mirror the builtin packs at that commit, with two MCP corrections: the `run_workflow` dry-run flag is `dryRun`, and only some field types stay read-only for a value of the wrong type. Versions translated from the builtins will replace these skills.

## Checks

```sh
python3 -m unittest discover -s scripts -p 'test_*.py'
python3 scripts/check.py
claude plugin validate --strict ./plugins/metal
claude plugin validate --strict .
python3 scripts/codex_install_check.py
```

`scripts/check.py` checks that:

- both manifests have the same name and version;
- both load the same skill directories and the same `.mcp.json`;
- `.mcp.json` holds only the Metal server;
- each skill's frontmatter uses only the keys that claude.ai accepts: `name`, `description`, `license`, `compatibility`, `metadata` and `allowed-tools`.

Codex has no validate command, so `scripts/codex_install_check.py` installs the plugin with the Codex CLI in a temporary `CODEX_HOME`. It renders the prompt Codex would send with `codex debug prompt-input`, and fails unless every skill in `skills/` and `synced-skills/` is listed there and `codex mcp list` has the Metal MCP server. It needs no credentials. It reads the prompt, not the plugin cache, because Codex copies the whole plugin into its cache, including skill directories its manifest does not list.

CI runs the same commands on every pull request, with Claude Code and Codex pinned.

## Releases

To release, set the same new `version` in both manifests and merge to `main`. CI then builds `metal-<version>.zip` and publishes it in a GitHub release tagged `metal--v<version>`. If that release already exists, CI does nothing. To build the zip locally, run `python3 scripts/package.py`. The zip holds the plugin directory's contents at its root.

## License

Apache License 2.0. See [LICENSE](LICENSE).
