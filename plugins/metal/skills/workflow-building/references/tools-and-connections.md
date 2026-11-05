# Workflow Tools And Connections

Use this reference when building direct Tool steps or when an Agent step needs connection-mounted tools. Tool names with their input schemas, and connection names with their option schemas, come from `list_workflow_building_options` (kinds `tools` and `connections`); this reference covers the behavior those values cannot express. Agent-native tools are in `agents.md`.

## Tool Steps

A Tool step executes one registered public tool or custom tool selected in the workflow definition.

- The building tools accept Tool `input` as an object or as a string. Prefer an object: each string leaf is a Go template rendered on its own, and arrays, objects, numbers, and booleans keep their JSON types. A string input is rendered whole, then parsed as JSON or wrapped as `{ "input": "<rendered text>" }`. Custom tools receive string leaves in printed form, so wrap a structured value with `toJSON`.
- A tool's exact field requirements come from its `inputSchema` in `list_workflow_building_options` kind `tools`.
- Per-user Outlook tools and connection-seeded PitchBook tools cannot run as direct Tool steps; use an Agent step with the connection. `get_document_page` cannot run as a Tool step either, because it returns the page only as an image; use an Agent step. `http_request` runs only through `call_tool_with_secrets` from an Agent step, and the chat scheduling tools (`schedule_create`, `schedule_list`, `schedule_delete`) run only inside a chat session. Authoring returns `unsupported_tool` for all of these. Other connection tools can run directly only when the `tools` catalog also lists them.

### Tool Step Outputs

- `OutputMap` keys become fields under the step results object.
- A non-empty tool text output is available as step text and as `results.text` when the tool does not already return a `text` field.
- JSON custom-tool outputs merge into the step results object; non-JSON custom-tool output can appear as `results.json` and `results.text`.
- Reference Tool step results with `{{ (index .Steps "<toolStepId>").results.<field> }}`, or embed full results with `{{ toJSON (index .Steps "<toolStepId>").results }}`.
- Terminal provider-write Tool steps can be intentionally side-effect-only: the intended result is the external write rather than a value a later step reads. The coherence checker does not flag that shape, so a final CRM write step needs no downstream consumer to be correct.

## Connections

Workflow-capable connections mount selected connection tools into an Agent step's run. `list_workflow_building_options` kind `connections` returns each connection's `tools` and `authModel`, plus `toolNamePrefix` on a user-configured MCP connection and `optionsSchema` on a first-party one. No entry carries both of those last two: the prefix exists only for MCP servers, the options schema only for registry connections. `connections[*].tools` describes the tools a connection mounts into an Agent step. Kind `tools` is a separate catalog of public and custom tools eligible for direct Tool steps; the two lists are not equivalent.

- The `platform` connection is appended automatically for Agent steps unless the step sets `disableAutoPlatformConnection: true`, which is an authorable field on this surface. Listing `platform` explicitly in `usableConnections` also suppresses the automatic append.
- Resource input fields do not imply strict provider filtering. Strict filtering applies only when an explicit `platform` connection config enables `strict_mode`.
- User-configured MCP tools use generated names shaped `{snake_cased server name}_mcp_{toolName}`, so a server called "SEC EDGAR" yields `sec_edgar_mcp_<toolName>`. Preserve inspected MCP names exactly rather than deriving them.
- Not every chat connection is workflow-available. Confirm availability through the `connections` catalog, the workflow definition, or run evidence when a prompt depends on a connection.
- Discover dynamic tool and connection additions through both catalogs instead of hard-coding provider names. Verify native Agent tools against `agents.md`, connection-mounted tools against `connections[*].tools`, and direct Tool steps against the `tools` catalog.

## Handoff Contracts

- Render structured tool arguments as JSON.
- Exact tool output keys are required for downstream references.
- Keep provider writes separated from review and approval when human confirmation is required; see `human-review.md`.
