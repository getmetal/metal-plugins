# Data Analysis Orchestrator

Use this reference when a workflow uses the `Data Analysis Orchestrator` agent or when an upstream agent step produces data for a work product template.

Write that agent name exactly as `Data Analysis Orchestrator`, spaces and capitals included. Authoring is lenient and accepts a normalized form such as `data-analysis-orchestrator`, then stores whatever you sent, but the coherence checker compares the stored string exactly when it decides whether a step may produce `templateInputData`. A step saved under the hyphenated spelling still runs and still produces the data, while every downstream `.templateInputData` reference collects an `unrecognized_step_path` warning claiming it renders empty. Take the exact name from `list_workflow_building_options` kind `agents`.

## Agent Contract

- The orchestrator selects a template, gathers template data through tools or delegation, validates the data, generates the file, and generates the summary.
- The orchestrator does not research, plan, fetch data, or call platform tools directly.
- The default path delegates research to Task Supervisor. Task Supervisor handles decomposition and source-specific research, then the orchestrator assembles the captured findings with `template_assemble_data` and the current `since_unix_ms` scope.
- The direct extraction path only applies when the user explicitly asks for Code Interpreter or CI and attached files are available. That path uses `template_extract_data`, then validation and rendering continue through the same work product data contract. If extraction fails, the orchestrator asks for guidance rather than silently switching to delegation.
- The platform connection is auto-appended to the orchestrator's own agent step like any other, and its tools are mounted on the orchestrator's belt. Only the agent's instructions keep platform work on the delegate path; nothing enforces it. Set `disableAutoPlatformConnection: true` on the step when you need that separation to be structural rather than prompt-deep.
- After validation passes, the orchestrator must call `template_generate_file` and then `template_generate_summary` with the returned bucket, key, and filename before responding.
- The orchestrator's declared toolbelt is the whole `work_product` group plus `spawn_subagent`, `download_image`, and `download_pdf`, on top of the standard agent tools. The group expands every tool registered to `work_product`, currently the `template_*` tools, including `template_prepare_inputs`. That tool is on the belt even though the agent's own instructions omit it from the enumerated path. Treat the prompt's list as operating guidance, not an enforced capability boundary, and read the run's tool calls to establish what happened.

## Work Product Data Contract

- `template_extract_data` and `template_assemble_data` (the orchestrator's documented path) and `template_prepare_inputs` (on its belt, off that path) all persist template input data under `work_product_data_<templateId>`.
- `template_validate_inputs` validates the stored data and does not merge or modify it.
- `template_generate_file` renders from the same stored data.
- After an agent step finishes, the workflow runner checks the agent context for the selected work product template ID, reads `work_product_data_<templateId>`, and writes it to step results as `templateInputData`.
- The workflow template context promotes that value, so downstream steps can read `(index .Steps "<agentStepId>").templateInputData`.
- Assistant prose, tool summaries, citations, and ordinary context variables do not become `templateInputData` unless a work product tool writes the canonical key.

## Two-Step Pattern

Standard two-step pattern when an agent populates a work product template and a later `generateDocument` step renders it:

1. Agent step runs `Data Analysis Orchestrator`, selects the template, gathers or assembles data, validates it, and leaves the final template object in `templateInputData`.
2. Generate Document step sets `inputData` to the upstream value with `toJSON` and renders the referenced template.

Keep the template ID, the agent-produced `templateInputData`, and the Generate Document `templateId` aligned. If any part points at a different template, validation and rendering can diverge.

## Agent File Attachments

Workflow agent file attachments are an agent-runtime concern, not a Generate Document input mechanism.

- Resolved `dataEntity` and `dataEntityMulti` workflow inputs have file-shaped objects with `id`, `name`, and `fileExtension`.
- The workflow runner scans resolved inputs for that shape and stores the IDs on the agent context with `SetAttachedFiles`.
- `attachedFiles` is a special key inside the step's `contextVariables`, which is authorable here like any other context variable. The runner renders it, appends the resulting data entity ID or IDs to the same runtime attached-file list, and never stores it as an ordinary context variable.
- The workflow runtime resolves that list into file inputs with metadata and presigned URLs for the agent and file-aware tools.
- Attached files do not add file bytes, data entity URLs, or extra fields to `templateInputData`.
