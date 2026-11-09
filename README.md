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
python3 -m pip install -r scripts/requirements.txt
python3 -m unittest discover -s scripts -p 'test_*.py'
python3 scripts/check.py
claude plugin validate --strict ./plugins/metal
claude plugin validate --strict .
python3 scripts/codex_install_check.py
```

`scripts/check.py` checks that both manifests agree on name, version, skill directories and MCP config, that `.mcp.json` holds only the Metal server, that skill frontmatter uses only keys claude.ai accepts, and that the icon and listing fields are set. It also checks README skill inventories, packaged Markdown links, shared safety guidance, and structural patterns for non-public identifiers and access details. These checks supplement manual disclosure review and a full-history secret scan.

Codex has no validate command, so `scripts/codex_install_check.py` installs the plugin with the Codex CLI in a temporary `CODEX_HOME`. It renders the prompt Codex would send with `codex debug prompt-input`, and fails unless every skill in `skills/` is listed there and `codex mcp list` has the Metal MCP server. It needs no credentials. It reads the prompt, not the plugin cache, because Codex copies the whole plugin into its cache, including skill directories its manifest does not list.

CI runs the same commands on every pull request, with Claude Code and Codex pinned.
It also builds and checks both release ZIP formats. OpenAI builds use the vendored
Agent Plugins 1.0 schemas and additional checks for OpenAI listing fields and OAuth.

## Releases

To release, set the same new `version` in both manifests and merge to `main`.
CI generates release notes once and publishes a GitHub release tagged
`metal--v<version>` with both artifacts:

- `metal-<version>.zip`: the existing plugin layout, including the Claude and Codex manifests.
- `metal-openai-<version>.zip`: the portable OpenAI upload, with generated root
  `plugin.json` and `mcp.json`, plus the shared skills, references, assets and license.

The OpenAI ZIP includes the same release-note text used as the GitHub release body.
If the version's release already exists, CI does nothing. Existing releases are
not changed or backfilled; bump both manifest versions for the next release.

Build locally after installing the dependencies above:

```sh
python3 scripts/package.py                         # Existing ZIP; standard library only
python3 scripts/package.py --format openai         # OpenAI ZIP, without release notes
python3 scripts/package.py --format all --release-notes /path/to/release-notes.md
```

Both formats put the plugin contents at the archive root. The OpenAI manifests
are generated from the existing source, not maintained as a second plugin copy.
OAuth uses DCR with discovery-provided endpoints and scopes; builds require no
network access, account credentials or OAuth registration.

The OpenAI build checks the saved archive's inventory, copied content, manifests,
listing limits and referenced files. It does not complete OpenAI's portal scans
or review. Test cases, a demo URL and reviewer access still need to be prepared
before submission; this build leaves missing review metadata absent. Reviewer
credentials belong only in the portal's secure fields. GitHub releases do not
submit or publish the plugin in OpenAI's directory. See
[OpenAI's submission and update process](https://developers.openai.com/plugins/deploy/submission).

## License

Apache License 2.0. See [LICENSE](LICENSE).
