# Metal

The Metal plugin connects Claude or Codex to the Metal MCP server at `https://mcp.metal.ai/mcp`. You sign in to Metal through the server's OAuth flow when you first use a Metal tool.

The plugin adds twelve skills:

- `skill-library`: find and follow the user's, firm's and shared skills in Metal's skill library.
- `workflow-building`: inspect or change a workflow definition.
- `running-workflows`: start, rerun or approve a workflow run.
- `workflow-debugging`: diagnose why an existing run behaved as it did.
- `workflow-fixing`: fix a failed workflow run and check the fix with a dry run.
- `deal-research`: research a deal and read figures from deal documents, weighted by source.
- `dashboard-building`: build or edit dashboard widgets, including script and HTML widgets.
- `metal-sdk-scripts`: write Python against the Metal SDK for SDK queries and dashboard scripts.
- `running-routines`: start a routine run, answer its questions and read its output.
- `working-with-tasks`: read, update and complete tasks.
- `working-with-ir-records`: explain funds, limited partners and fundraising processes.
- `metal-product-knowledge`: answer questions about Metal from its public docs.

The repository README covers installation and releases. The plugin is licensed under the Apache License 2.0; see `LICENSE`.
