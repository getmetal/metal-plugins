# Workflow Tools And Connections

Use this reference when building direct Tool steps or when an Agent step needs connection-mounted tools. Tool names with their input schemas, and connection names with their option schemas, come from `list_workflow_building_options` (kinds `tools` and `connections`); this reference covers the behavior those values cannot express. Agent-native tools are in `agents.md`.

## Tool Steps

A Tool step executes one registered public tool or custom tool selected in the workflow definition.

- The building tools accept Tool `Input` only as a string template. The rendered string parses as JSON or wraps as `{ "input": "<rendered text>" }`. Saved visual-builder definitions can contain object input; omit `input` on a same-type update to preserve that stored object because the building tools cannot create or replace it in object form.
- A tool's exact field requirements come from its `inputSchema` in `list_workflow_building_options` kind `tools`. Render structured arguments as JSON.
- Per-user Outlook tools and connection-seeded PitchBook tools cannot run as direct Tool steps. Authoring returns `unsupported_tool`; use an Agent step with the connection. Other connection tools can run directly only when the `tools` catalog also lists them.

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
