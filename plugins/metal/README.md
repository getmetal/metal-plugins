# Metal

The Metal plugin connects Claude or Codex to the Metal MCP server at `https://mcp.metal.ai/mcp`. You sign in to Metal through the server's OAuth flow when you first use a Metal tool.

## Install

In Claude Code, run:

```
/plugin install metal --marketplace getmetal/metal-plugins
```

The repository README covers the Claude desktop app, ChatGPT, Codex and releases.

## Skills

The plugin adds thirteen skills:

- `skill-library`: find and follow the user's, firm's and shared skills in Metal's skill library.
- `workflow-building`: inspect or change a workflow definition.
- `running-workflows`: start, rerun or approve a workflow run.
- `workflow-debugging`: diagnose why an existing run behaved as it did.
- `workflow-fixing`: fix a failed workflow run and check the fix with a dry run.
- `deal-research`: research a deal and read figures from deal documents, weighted by source.
- `working-with-lists`: save results as a list, change its columns, and add or update rows.
- `dashboard-building`: build or edit dashboard widgets, including script and HTML widgets.
- `metal-sdk-scripts`: write Python against the Metal SDK for SDK queries and dashboard scripts.
- `running-routines`: start a routine run, answer its questions and read its output.
- `working-with-tasks`: read, update and complete tasks.
- `working-with-ir-records`: explain funds, limited partners and fundraising processes.
- `metal-product-knowledge`: answer questions about Metal from its public docs.

## What the plugin runs, sends and fetches

The plugin has no hooks, scripts or local servers. It runs no code on your machine.

- **Metal MCP server.** The plugin's only connector is `https://mcp.metal.ai/mcp`. Tool calls and their arguments go to Metal, under your Metal account and your organization's permissions. The plugin stores no credentials. The OAuth flow holds your sign-in.
- **Metal docs.** The `metal-product-knowledge` skill tells the assistant to read public pages under [docs.metal.ai](https://docs.metal.ai) with its own web-fetch tool. It sends no user data there.
- **Dashboard and workflow HTML.** The `dashboard-building` and `workflow-building` skills tell the assistant which `https://cdn.jsdelivr.net/npm/` libraries Metal allows in HTML widgets and HTML workflow outputs. Metal's web app loads those libraries when it renders the HTML. The plugin itself fetches nothing from the CDN.

The skills are Markdown instructions. The Python examples in `metal-sdk-scripts` and `dashboard-building` run on Metal's servers through Metal's MCP tools, not on your machine.

## License

The plugin is licensed under the Apache License 2.0. See `LICENSE`.
