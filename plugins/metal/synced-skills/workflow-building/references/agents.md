# Workflow Agents

Use this reference when choosing an Agent step, writing exact agent tool instructions, or checking which tools and skills are native to a workflow-enabled agent. Agent, model, and connection selector values come from `list_workflow_building_options`; this reference covers the behavior those values cannot express.

## Agent Step Defaults

- The built-in Workflow Agent is the default general-purpose agent for steps that need tools, retrieval, files, source-backed reasoning, or artifact creation. Agent selector values are org-specific; query `list_workflow_building_options` kind `agents` for valid names and descriptions, and preserve exact inspected names in existing definitions.
- Specialized agents fit provider-specific or internal workflow roles.
- An agent step with an `outputSchema` emits validated structured output at `results.structured`; the schema is enforced at run time. `structured-output.md` covers the contract.

## Standard Agent Tools

Standard agents receive these platform-defined baseline tools in addition to their own native tools. They are not enumerated in the building catalog:

| Tool or group | Building use |
| --- | --- |
| `memory_store` | Store reusable information in agent memory |
| `memory_recall` | Retrieve information from agent memory |
| `wait` | Delay execution briefly |
| `group:vfs` | Read and write virtual files available to the agent runtime |
| `group:todo` | Track multi-step agent work inside the run |

## Workflow Agent

Default reach: general workflow work that needs tools, retrieval, files, source-backed reasoning, or artifact creation.

Native tools include `halt_workflow`, `create_output`, `get_document`, `download_image`, `download_pdf`, `platform_ls`, `resolve_folder_path`, `create_folder`, `move_data_entity`, `set_deal_folder`, `save_artifact_to_folder`, user and record tools (`group:users`, `group:records`), sandbox tools (`group:sandbox`), and the list tools below.

The `platform` connection is appended automatically for Agent steps unless disabled by saved configuration. Resource references in the step input do not infer strict-mode filters.

### Halting A Run

Use `halt_workflow` only when the step prompt states a halt condition and that condition holds. The Workflow Agent cannot invent a halt condition, and the call requires a non-empty user-facing `reason`.

`HALTED` is terminal. The runner persists the reason as `haltReason`, skips remaining steps and normal output finalization, and sends no completion email or chat notification on the halt path.

## Sandbox Artifact Tools

Sandbox-enabled agents can use:

| Tool | Building use |
| --- | --- |
| `sandbox_exec` | Run scripts or shell commands in the sandbox |
| `sandbox_upload_artifact` | Upload a workflow input file or prior-step artifact into the sandbox by filename |
| `sandbox_upload_data_entity` | Upload a platform data entity into the sandbox by ID |
| `sandbox_download` | Register a sandbox file as a workflow artifact |

Files created in the sandbox must pass through `sandbox_download` to persist beyond the step. User-visible deliverables must then pass through `create_output` using the exact artifact ID returned by `sandbox_download`.

`sandbox_upload_artifact` handles workflow input files and artifacts from prior steps. `sandbox_upload_data_entity` handles data entity IDs from workflow input, search results, list entries, or another workflow-available source; it accepts an exact absolute `sandbox_path` destination (used verbatim) in addition to the heuristic `path` directory argument. Sandbox upload uses these two tools; there is no `mount_file` or `mount_data_entity`.

## List Tools

The built-in Workflow Agent has four list read tools plus one narrow write:

| Tool | Building use |
| --- | --- |
| `browse_lists` | Find resource lists with optional filters |
| `get_list` | Get a list by ID, including column schema and metadata |
| `browse_list_entries` | Read list entries with optional filters and sorts |
| `export_list_entries` | Export matching list entries to a session artifact as JSON or CSV |
| `update_list_entry` | Update cell values on an existing entry, in place |

`export_list_entries` fits complete list contents. `browse_list_entries` fits previews or targeted entry inspection.

`update_list_entry` is the one list mutation an autonomous Agent step can perform, so an agent step pointed at a list can write to it without a Tool step and without a human review gate. Build the review gate deliberately when that matters. The tools that create or destroy list structure are not native: `create_list`, `add_list_entry`, and `delete_list_entry` need a direct Tool step or a custom agent surface.

## Loadable Skills

Workflow agents load skills by reading mounted instructions with `read()` when the prompt calls for procedural guidance, such as file-format helpers, financial-model builders, list and dashboard guides, or document-extraction skills. Name the skill in the prompt. There is no `skills` catalog kind; the loadable set is platform-defined.

Connection-provided skills can appear when a connection is mounted. For example, the platform connection can provide document-finding and search-troubleshooting guidance.

## Agent Step Config Fields

The agent step `config` accepts `agent`, `input`, `model`, `reasoningEffort`, `contextVariables`, `usableConnections`, and `disableAutoPlatformConnection` (`agent` and `input` are required). Agent model overrides must have `workflowAgentStepEligible` in the `models` catalog. Select `reasoningEffort` from that model's `supportedReasoningEfforts`; the step needs an effective model before reasoning effort can be set. A same-type update can set `reasoningEffort` without restating a saved model.

`update_workflow_step` merges: an omitted field keeps its current value, so an `input`-only update preserves `usableConnections` and the rest; clear a field with an explicit `null` (or `[]` for lists). The compact `get_workflow` projection includes Agent and Completion `reasoningEffort` plus safe scalar tuning fields. Use `get_workflow_step` for complete safe prompts, context variables, connection options, skills, resolvers, or a full type-changing replacement; secret fields and secret-like string values remain redacted. These fields are unavailable on the MCP authoring surface and reject as `unknown_field`: `skills`, `maxTurns`, `agentTimeoutSeconds`, `projectTimeoutSeconds`, `tokenBudget`, `compactionThreshold`, `compactionCeiling`, and `contextWindowTokens`. Use the visual builder or ask Metal about unsupported configuration; a merge update preserves stored values that the MCP cannot author.

`data-analysis-orchestrator.md` covers the Data Analysis Orchestrator agent and its work product tools.
