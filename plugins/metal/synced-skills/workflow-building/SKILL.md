---
name: workflow-building
description: Applies when a Metal workflow definition, step configuration, input or output contract, trigger, or template-backed document step must be inspected or changed through the Metal MCP; starting or acting on a run belongs to running-workflows, and read-only run diagnosis belongs to workflow-debugging.
---

# Metal Workflow Building

This skill is a reference for Metal workflow definitions, run evidence, execution code, and template-backed document outputs. The central building concern is the runtime contract: what workflow inputs resolve to, what each step emits, and what downstream steps consume.

For run-behavior diagnosis from a run ID, use the `workflow-debugging` skill. Workflow edits route back here.

## Connection

- This skill operates through a connected Metal MCP. If more than one Metal MCP is connected, pick one for the task and do not mix them.
- Servers differ by tool surface, not workflow tool behavior: a server that exposes org-selection tools (`get_orgs`, `select_org`, `get_current_org`) serves multiple orgs; a server without them is bound to a single org.
- On a single-org server: if tools are missing or fail to connect, the Metal MCP may not be connected, may be disabled for the org, or the user may be authed against a different org. Ask the user to confirm before concluding anything is broken, and direct them to re-auth when access looks wrong. If tools work but a workflow or run cannot be found or run, a not-found response can be a policy denial: the workflow exists but is out of the current org's access scope. Ask the user to confirm org access before concluding the workflow does not exist.
- On a multi-org server: every workflow tool fails with "missing org context" until an org is bound with `select_org` (find it with `get_orgs`, verify with `get_current_org`). The binding can expire mid-conversation; the same error later means re-select, not a broken connection. Access-policy gates are broadly bypassed on this server, so a not-found response usually means the wrong org is bound or the resource genuinely does not exist.
- Never proceed against an org the thread has not confirmed; this includes the org passed to `select_org`.

## Metal MCP Tools

Read tools: `list_workflows`, `get_workflow`, `get_workflow_step`, `list_workflow_runs`, `get_workflow_run`, and `get_workflow_run_step`.

Building tools: `create_workflow`, `update_workflow_details`, `configure_workflow_input`, `configure_workflow_trigger`, `configure_workflow_output`, `add_workflow_step`, `update_workflow_step`, `delete_workflow_step`, and `move_workflow_step`.

Run tool: `run_workflow` creates a workflow run and accepts the per-run `dryRun` value. Use the `running-workflows` skill for run-mode selection, input resolution, verification of the returned mode, and monitoring.

Run-action tool: `review_workflow_hitl_step` resolves a run paused at `AWAITING_APPROVAL` by approving or rejecting its review items. Like `run_workflow`, it is mutative, not an inspection tool; call it only on explicit user intent and confirm before submitting. Review authority follows reviewer assignment (see `references/human-review.md`).

Rerun tool: `rerun_workflow_run_from_step` creates a new run from a terminal one. It reuses the source input with the workflow's current definition, so an edit made after the source run can change step IDs or invalidate the saved path. Each call creates a run; after an ambiguous failure, check `list_workflow_runs` before retrying. The source must be terminal, every preceding top-level step must be `COMPLETED`, and preceding siblings in the selected branch arm must be `COMPLETED` or `SKIPPED`. The target can be a top-level step or a descendant of the branch path recorded by the source run. A step in an untaken arm is not a valid target, and iterator children cannot be targeted. See Branch in `references/step-types.md` for seed behavior, and use the `running-workflows` skill to start and monitor the rerun.

- `get_workflow` returns a compact workflow projection with compact step projections. `get_workflow_step` returns the full safe saved step definition and is the source for complete prompt text after secret scrubbing. It redacts secret fields and secret-like string values; never present a redacted prompt or config as the literal stored value.
- `list_workflow_building_options` returns the org-valid catalog of agents, models, tools, connections, and step options. Use target-aware `promptTemplateVariables` before writing a prompt or template, and use `iteratorSources` before setting an iterator source, except for an iterator inside a branch arm, which that kind cannot target. Never guess catalog values or source expressions.
- Large text fields arrive as truncated previews. When `truncated` is true, follow the attached `expandInstructions` verbatim instead of guessing field paths. See `references/mcp-run-evidence.md` for the read views, the projection and paging interface, and definition-drift comparison.
- Building rejections carry `details: [{field, message, code, candidates}]`. Fix the named field. Treat `candidates` as bounded, context-specific repair hints that may be absent, partial, ranked, or differently scoped from the authoring catalog. Code `concurrent_update` means re-read the workflow and re-apply the change.
- See `references/building-tools.md` for per-tool purposes, write pipeline behavior, warning codes, and error semantics.

### Warnings Envelope

Every building write returns the outstanding `warnings` plus one of two shapes. `add_workflow_step`, `update_workflow_step`, and `move_workflow_step` return `{step, expandableFields?, warnings}`, where `step` is normally the affected step in the compact shape `workflow.steps[]` carries. A committed write can return `step: null` when the response cannot project the saved step. Every other write returns `{workflow, warnings}`, where `workflow` is the compact updated projection `get_workflow` returns, not the full workflow document. This envelope is the validation surface; there is no separate validator or verification script.

- A warning is `{code, severity, path, refs, introduced, message}`.
- Severity is fixed per code: error, warning, or advisory. A finding blocks the write only when it is both error severity and introduced by this write.
- Pre-existing findings carry `introduced: false` and never block.
- Surface warnings and advisories to the user instead of silently dropping them.
- Re-check the outstanding warning set before declaring the workflow ready and get user acknowledgment for anything unresolved.
- See `references/building-tools.md` for the severity tiers and the full code list.

## Write Safety

- For a new Workflow request, create the default Restricted Workflow shell. For an existing Workflow request, edit the Workflow the user identified and preserve its Workflow ID. Never create a separate test or validation Workflow unless the user explicitly approves it.
- dryRun applies to Runs only. It does not create an isolated Workflow definition or authorize cloning the selected Workflow.
- When the selected Workflow is an organization Workflow with an enabled automatic trigger (`trigger.enabled`, or any enabled schedule), explain that the edit lands on the live definition and the next triggered run uses it. Ask before pausing a trigger.
- Treat create_workflow as new-resource creation. Do not use it as a testing substitute for an existing Workflow without explicit permission.
- Pause a trigger (`enabled: false`, or per schedule) when the user wants it configured but not yet running.
- Treat step deletion as destructive and require explicit user intent.

## Development Testing

Workflow building, editing, and iterative validation are development intent. Use the `running-workflows` skill for run-mode selection, authorization, and loop bounds. Use the `workflow-debugging` skill to qualify dry-run evidence. Dry-run testing does not change General Access or pause automatic triggers.

## Sources Of Truth

- Metal MCP evidence includes workflow definitions, step snapshots, run lists, run steps, outputs, tool calls, transcripts, errors, artifacts, and run documents.
- Workflow definition fields commonly needed for building are `id`, `version`, General Access (`visibility`), `deprecated`, trigger, `inputSchema`, `outputConfig`, step IDs, step types, and step inputs.
- Run evidence carries its own `workflowVersion`, step IDs, timestamps, outputs, artifacts, and errors. Older runs can reflect older workflow-definition versions.
- Iterator child steps, Generate Document steps, HITL steps, and work product template workflows often require both definition evidence and run-step evidence to understand their concrete runtime shape.

## Building Surfaces

| Surface | Typical contents |
| --- | --- |
| Workflow definition | Input schema, step ordering, step prompt, tool step input, `executeCode` config, `generateDocument.inputData`, output config, HITL review payload, iterator shape |
| Work product template | `inputSchema`, render script, output format, template asset behavior |
| Data access | Workflow input resources, platform/Egnyte/SharePoint discovery, attached files, sandbox uploads, agent usable connections |

Surface choice matters because prompts cannot reliably compensate for missing schema fields, missing persisted step outputs, or renderer limitations. File access also depends on the runtime path: workflow input file, attached data entity, prior artifact, and platform-discovered resource are separate paths.

## Step Interface Surfaces

Step interfaces form downstream contracts. Common contract fields include step type, agent selector, tool selector, prompt-like input, artifact filenames, top-level payload keys, structured output shape, template references, and human approval payload contract.

Exact downstream key paths are distinct:

- `.Steps["x"].text` is prior step text.
- `.Steps["x"].results.structured` is validated structured output from steps configured to emit it.
- `.Steps["x"].templateInputData` is work product template data produced by work product tooling.
- `.StepArtifacts["x"]` holds workflow artifacts for step `x`. There is no `.Steps["x"].artifacts`; artifacts are addressable only through the root `.StepArtifacts`.

Agent steps without an `outputSchema` expose human-readable text by default. With an `outputSchema`, an Agent step's `.text` compatibility field contains the serialized validated payload, while a Completion step's text can differ from its validated payload after coercion or reissue. Durable machine-readable consumers should read `results.structured`, normally through `toJSON`. Structured data comes from a declared `outputSchema` on an `agent`, `completion`, or `executeCode` step, a tool result, or a work product template data key.

## Building process

1. Confirm the connected org, then read the workflow with `get_workflow`. Read each touched step with `get_workflow_step` before editing it.
2. Classify the request by surface and load the relevant reference. Query `list_workflow_building_options` for every selector or target-aware expression the edit needs.
3. Trace the touched inputs, outputs, artifacts, template expressions, and downstream consumers. Preserve every interface the user did not ask to change.
4. Apply the smallest mutation to the user-selected Workflow. If it is an organization Workflow with enabled automatic triggers, explain before the first write that the next triggered run will use the edit, and ask before pausing any trigger. Provide full replacement content for a touched prompt-like field. For a same-type step config update, send only the fields the edit changes.
5. Inspect the response warnings. If a step write returns `step: null`, do not resend it. Read the workflow and touched step to verify the committed state.
6. Declare the workflow ready only after the user acknowledges any unresolved warnings.

## Core Building Rules

- Preserve the visible step interface unless the user asks to change it. Interface surfaces include step type, agent selector, tool selector, prompt-like input, artifact filenames, top-level payload keys, structured output shape, template references, and the human approval payload contract.
- When the user asks for the exact prompt and nothing else, fetch it with `get_workflow_step` and return only the prompt text without preamble, explanatory bullets, or an outer code fence.
- Prefer smaller responsibilities per step when a prompt is hard to reason about: separate decisioning from presentation, data validation from rendering, and safe write-plan generation from review-payload enrichment. Name the handoff contract between split steps.
- When a prompt interpolates an id or a name, state the resource type in the surrounding text: "the Company with id `{{ .Input.company.id }}`", not a bare `{{ .Input.company.id }}`. Pair the id with a human-readable label in parentheses when the same source carries one. Rendered templates otherwise hand the agent an anonymous hex string with no type information, which agents misroute, such as passing an id as a name argument.
- For new or changed model fields, call `list_workflow_building_options` with `models` and choose from the current catalog. Do not use any hard-coded or historical model as a default. Preserve existing workflow models unless the user asks for a model change or run evidence justifies it.
- Do not set, echo, or clear completion tuning fields such as `temperature` or `maxTokens` unless the user asks for that tuning change. `update_workflow_step` merges: omitted fields keep their current values, so send only the fields the edit is about and tuning fields stay untouched.
- Separate business inputs from runtime assets. Keep the visible input schema focused on user-provided business data, and model templates, fixtures, schemas, or other execution-only assets as explicit runtime file inputs or artifacts when the workflow needs them.
- Avoid embedding large templates or binary-like assets inside prompts or scripts. Prefer input files, artifacts, or compact deterministic code so the workflow definition stays inspectable and debuggable.
- Do not hide runtime files in encoded payloads inside prompts or scripts. This includes base64, gzip or zlib-compressed strings, hex blobs, marshal or pickle payloads, large string constants, and decoded `exec` or import patterns.
- When porting a local validator, template, or script, mount the file through workflow inputs, data entities, artifacts, or `inputFiles`, or write readable equivalent source code. Do not decode an embedded copy at run time.
- Keep debug data out of UI file outputs unless the user needs it as a deliverable. Prefer `results.structured` or execution evidence for intermediate reports, and use `outputFiles[].createOutput` only for files that should appear in the run Output tab.

## Evidence Fields

- Workflow ID, version, and step IDs.
- Relevant `inputSchema` and `outputConfig` snippets.
- Exact downstream template expression.
- Completed-run evidence for the happy path.
- Failed-run evidence for the failure mode.
- MCP-visible reproduction evidence for non-obvious execution behavior, plus the exact evidence gap to send to Metal when the skill cannot explain it.
- Template schema fields when work product rendering is involved.
- Compact contract shape: inputs, steps, produced fields, consumed fields, and failure modes.

## References

- `references/mcp-run-evidence.md`: read tools, views, the projection and paging interface, previews and expansion, result maps, provenance and iterator child state, versioning, and definition-drift comparison.
- `references/building-tools.md`: building tool surface, write pipeline behavior, the warning severity model and full code list, error semantics, and the building catalog.
- `references/step-types.md`: base step fields, per-step behavior, handoff surfaces, execute-code output, and iterator concurrency and error policy.
- `references/execute-code-runtime.md`: execute-code sandbox runtime, installed libraries, helper scripts, runtime paths, file staging, output publishing, and UI Output-record behavior.
- `references/template-syntax.md`: Go template mechanics, `index .Steps` versus `.Steps.<id>`, missing-key behavior, iterator source grammar, and the runtime-only iterator helpers.
- `references/inputs-and-resources.md`: building workflow inputs, resolved resource field shapes, resolution rules, iterator item access, and step-output iterator sources.
- `references/triggers.md`: manual, email, event, schedule, and webhook triggers, their config, provisioning side-effects, and input mappings.
- `references/permissions-and-run-policy.md`: General Access, shares, authoring access, run visibility, and run policy.
- `references/agents.md`: agent-native tools, the sandbox artifact lifecycle, the list read tools plus the one native list write, loadable skills, and agent step config fields.
- `references/tools-and-connections.md`: Tool step behavior and output mapping, and connection mounting behavior.
- `references/output-sections.md`: output schema rendering, output sections, citations, finalization, and completion notification conditions.
- `references/human-review.md`: human approval, editable and field-level review, the approved-payload contract, and post-approval writes. Read before building any review step.
- `references/retrieval-building.md`: source-backed retrieval, file inspection, evidence coverage, period/entity gates, and metric extraction.
- `references/structured-output.md`: load when building workflow `step.OutputSchema` usage, schema-backed downstream contracts, or reasoning about runtime schema enforcement.
- `references/generate-document.md`: Generate Document and work product template workflows.
- `references/data-analysis-orchestrator.md`: `Data Analysis Orchestrator` agent behavior, work product tools, and agent file attachments.
- `references/domains/`: provider-specific batch import, validation, review, and writeback playbooks (Salesforce, Affinity, DealCloud). Load a pack only when the workflow targets that provider.
