# metal-plugins

This repository holds the `metal` plugin and a `metal` marketplace for Claude, Codex and ChatGPT. Installing the plugin connects the Metal MCP server at `https://mcp.metal.ai/mcp` and adds skills for working with Metal: deal research, lists, dashboards, workflows, routines, tasks, investor-relations records, Metal's docs and the user's Metal skill library. Each user signs in to Metal through the MCP server's OAuth flow. The repository contains no credentials.

## Install

**Claude desktop app (Chat and Cowork):** open Customize > Plugins, select + Add > Add marketplace, enter `getmetal/metal-plugins` and keep Sync automatically on. Add the Metal plugin, then open its Connectors tab and connect Metal. Each member installs the plugin for their own account.

**ChatGPT desktop app (Work mode or Codex):** a workspace admin opens Admin > Plugins > Add > Import marketplace and enters `https://github.com/getmetal/metal-plugins`, leaving Path empty. Review the import and installation policy; members then install Metal from the Plugins directory. For personal testing, add this repository as a marketplace in the desktop app. See [OpenAI's GitHub import documentation](https://learn.chatgpt.com/docs/enterprise/plugin-management) and [local marketplace documentation](https://developers.openai.com/plugins/build/plugins). Git-imported plugins that declare MCP servers can be marked Desktop only; check the plugin's supported surfaces in your client. This repository's install check verifies Codex CLI loading, not Chat-mode tool access.

**Command line:**

```sh
claude plugin marketplace add getmetal/metal-plugins
claude plugin install metal@metal
codex plugin marketplace add getmetal/metal-plugins
codex plugin add metal@metal
```

Workspace import uses the admin's authorized GitHub account. Each member connects their own Metal account when prompted.

## Skills

| Skill | Use |
|---|---|
| `metal:skill-library` | Find and follow the user's, firm's and shared skills in Metal's skill library |
| `metal:workflow-building` | Inspect or change a workflow definition |
| `metal:running-workflows` | Start, rerun or approve a workflow run |
| `metal:workflow-debugging` | Diagnose why an existing run behaved as it did |
| `metal:workflow-fixing` | Fix a failed workflow run and check the fix with a dry run |
| `metal:deal-research` | Research a deal and read figures from deal documents, weighted by source |
| `metal:working-with-lists` | Save results as a list, change its columns, and add or update rows |
| `metal:dashboard-building` | Build or edit dashboard widgets, including script and HTML widgets |
| `metal:metal-sdk-scripts` | Write Python against the Metal SDK for SDK queries and dashboard scripts |
| `metal:running-routines` | Start a routine run, answer its questions and read its output |
| `metal:working-with-tasks` | Read, update and complete tasks |
| `metal:working-with-ir-records` | Explain funds, limited partners and fundraising processes |
| `metal:metal-product-knowledge` | Answer questions about Metal from its public docs |

## Layout

| Path | Contents |
|---|---|
| `.claude-plugin/marketplace.json` | The Claude marketplace |
| `.agents/plugins/marketplace.json` | The Codex marketplace |
| `plugins/metal/.claude-plugin/plugin.json` | The Claude manifest |
| `plugins/metal/.codex-plugin/plugin.json` | The Codex manifest |
| `plugins/metal/.mcp.json` | The Metal MCP server, shared by both manifests |
| `plugins/metal/skills/` | The skills |
| `scripts/` | The repository checks and the release packager |

## Checks

```sh
python3 -m unittest discover -s scripts -p 'test_*.py'
python3 scripts/check.py
claude plugin validate --strict ./plugins/metal
claude plugin validate --strict .
python3 scripts/codex_install_check.py
```

`scripts/check.py` checks that both manifests agree on name, version, skill directories and MCP config, that `.mcp.json` holds only the Metal server, that skill frontmatter uses only keys claude.ai accepts, and that the icon and listing fields are set. It also checks README skill inventories, packaged Markdown links, shared safety guidance, and structural patterns for non-public identifiers and access details. These checks supplement manual disclosure review and a full-history secret scan.

Codex has no validate command, so `scripts/codex_install_check.py` installs the plugin with the Codex CLI in a temporary `CODEX_HOME`. It renders the prompt Codex would send with `codex debug prompt-input`, and fails unless every skill in `skills/` is listed there and `codex mcp list` has the Metal MCP server. It needs no credentials. It reads the prompt, not the plugin cache, because Codex copies the whole plugin into its cache, including skill directories its manifest does not list.

CI runs the same commands on every pull request, with Claude Code and Codex pinned.

## Releases

To release, set the same new `version` in both manifests and merge to `main`. CI then builds `metal-<version>.zip` and publishes it in a GitHub release tagged `metal--v<version>`. If that release already exists, CI does nothing. To build the zip locally, run `python3 scripts/package.py`. The zip holds the plugin directory's contents at its root.

## License

Apache License 2.0. See [LICENSE](LICENSE).
