# Workflow Building Tools

Use this reference when applying workflow changes through the Metal MCP building tools or interpreting their responses.

## Tool Surface

| Tool | Purpose |
| --- | --- |
| `create_workflow` | Create a Restricted workflow shell |
| `update_workflow_details` | Name, description, section |
| `configure_workflow_input` | Input fields and their required/optional presence |
| `configure_workflow_trigger` | How the workflow starts |
| `configure_workflow_output` | Output sections and notification settings |
| `add_workflow_step` | Insert a step: top-level, iterator child, or branch arm |
| `update_workflow_step` | Edit a step's type and config |
| `delete_workflow_step` | Remove a step |
| `move_workflow_step` | Reorder within a level |
| `list_workflow_building_options` | Org-valid catalog values |

Every mutative tool returns the outstanding warning set plus one of two shapes. `add_workflow_step`, `update_workflow_step`, and `move_workflow_step` return `{step, expandableFields?, warnings}`, where `step` is normally the affected step in the same compact shape `workflow.steps[]` carries. A mutation can commit successfully and return `step: null` when the response cannot project the saved step. Preserve the warnings, do not retry the write, and verify the result with `get_workflow` and `get_workflow_step`. Every other mutative tool returns `{workflow, warnings}` with the compact projection `get_workflow` returns: `create_workflow`, `update_workflow_details`, `delete_workflow_step`, and the three `configure_workflow_*` tools. The warnings are workflow-wide, so one may name a step the write never touched. Both projections carry previews rather than complete step configs; read a step with `get_workflow_step` when exact safe configuration matters.

The building surface is narrower than the builder UI: `update_workflow_details` covers only name, description, and section. Workflow fields such as `evalInstructions` (Evaluation Instructions) and `visibility`/`runVisibility`/`sharedWith` cannot be set through these tools; they are set in the builder UI.

## Write Pipeline Behavior

- Re-submitting an unchanged configuration is a no-op: it succeeds without persisting or bumping the version.
- Real writes bump the workflow version. Writes compare-and-set on the loaded version; a concurrent edit surfaces as code `concurrent_update`, meaning re-read the workflow and re-apply the change instead of clobbering the other writer.
- Payloads are strict. Unknown fields are path-specific `unknown_field` errors, not silently dropped. Fields unavailable on this MCP authoring surface, such as `maxTurns`, completion `metadata`, and inline iterator children, are rejected. Branch arms are the exception: `then` and `else` are inline step arrays on the branch config, and that is how a branch is authored.
- Step `type` and `config` correspondence is enforced server-side.
- `update_workflow_step` with the step type unchanged merges `config` field by field: an omitted field keeps its current value, an explicit `null` clears it (`null` on a required field is a 400 `required`), and a provided value replaces the whole value. `[]` and `null` both clear list fields; arrays and objects (`usableConnections`, `contextVariables`, `inputFiles`, `outputFiles`) set-or-keep as units, never deep-merged. Send only the fields to change; round-tripping the full config is unnecessary. Every omitted field keeps its current value, including completion tuning such as `temperature` or `maxTokens` and fields unavailable on this MCP surface such as `maxTurns`.
- Changing a step's `type` through `update_workflow_step` is a full replace: provide the complete config of the new type. Nothing merges across types, and fields unavailable on this MCP surface do not carry over.
- Trigger-type switches are destructive to provisioned resources: switching away from `email` or `webhook` deletes the inbound address or webhook endpoint, and switching back provisions fresh. Staying on the same type keeps the linked resource. An email prefix conflict surfaces as `address_in_use` on `trigger.emailPrefix`. Switching away from schedule deletes its schedules (ids, per-schedule triggerers, static input); switching back mints new schedule ids.
- Authoring mutations are never retried automatically: they carry no idempotency keys, so a transport error or 5xx can arrive after a committed mutation. Before retrying or repairing a failed-looking write, re-read `get_workflow` and the touched steps with `get_workflow_step` to see what actually persisted. This matters most for `add_workflow_step` and trigger-provisioning writes, where a blind resend duplicates a step or provisions a second trigger resource.
- A failed write attempts to roll back trigger resources and authorization changes created before persistence. After any ambiguous failure, reread the workflow before retrying.
- A successful response means the workflow write committed even if later cleanup or an inbound-address display rename did not complete. Do not retry a successful authoring response.
- A structural step error that predates an unrelated write can surface as a non-blocking `preexisting_step_invalidity` warning.

## Warning Severity And Blocking

The coherence checker runs on every write and classifies each finding by a fixed severity derived from its code.

A finding blocks the write only when it is both error severity and introduced by this write, meaning it is absent from the pre-write finding set. Finding identity is normalized to step IDs, so inserting, moving, or deleting a step does not make a pre-existing finding on a shifted sibling look freshly introduced. Blockers come back as HTTP 400 `details`; every other finding rides in `warnings`. Pre-existing findings carry `introduced: false` and never block.

Three severity tiers:

- error: decided from the document and the Go `text/template` engine (parse failure, function arity, step existence, run order, scope, declared input or output schema). Definitely broken. Blocks when introduced.
- warning: depends on a hand-maintained catalog that mirrors workflow execution and can lag it, so the finding may be a false positive on a key the run really exposes. Never blocks.
- advisory: observational or quality. Never blocks. An unknown future code defaults to warning.

Error codes (block when introduced by the write):

- `template_syntax`: a template-rendered field does not parse.
- `invalid_function_arity`: `step`, `iteratorResults`, or `iteratorSummaries` is called with the wrong argument count.
- `missing_step_reference`: the referenced step does not exist.
- `forward_step_reference`: the reference targets a later-running step or itself; it renders empty.
- `invalid_step_path`: the path is not addressable on that step type or is not declared in the step's output schema.
- `scope_violation`: an iterator child is referenced outside its iterator, or iterator context is used outside child templates.
- `unknown_input_reference`: an `.Input` key is not a declared field, trigger context, or context variable.
- `invalid_input_path`: a sub-path on a scalar input, which has no sub-fields.
- `trigger_context_mismatch`: the reference uses trigger context the current trigger type does not supply.
- `condition_syntax`: a branch condition is not parseable CEL, or it addresses a step in a form the reference graph cannot be read from. Two such forms: `steps[<computed key>]` instead of a string literal, and the dot form `steps.<stepId>`. CEL selects fields off the step map happily, so a dot-form read of a misspelled, skipped, or other-arm step compiles clean and fails only once the run reaches the branch. Write `steps["<stepId>"]`.
- `cross_branch_reference`: a reference into the sibling arm of a shared branch ancestor. Only one arm ever runs, so it always renders empty.
- `unguarded_condition_step_reference`: a branch condition reads a step inside an arm the condition does not itself sit in. A skipped step is an absent map key, so CEL raises `no such key` and fails the run instead of reading empty. Guard it with `"<stepId>" in steps`, which clears the finding for that step.

Warning codes (advise, never block):

- `unrecognized_step_path`: a step-output key absent from the hand-maintained addressable-path catalog. That catalog mirrors workflow execution and can lag it, so this may be a false positive on a key the run exposes.
- `execute_code_input_shape`: an `executeCode` step's rendered `input` skeleton does not decode as a single JSON value, which the runtime's render validation would reject. It is a warning rather than an error because an action that emits a JSON fragment, or renders empty, makes the skeleton a false positive.

Advisory codes (never block):

- `context_variable_shadowing`: an iterator context variable shadows a workflow input key.
- `empty_section_content`: an output section resolves to no content.
- `citations_unavailable`: citations requested from a step type that cannot produce them.
- `trigger_paused`: an automatic trigger is configured but explicitly paused, so it will not fire. This reports stored state, not a defect; do not clear it by re-enabling the trigger unless the user asks.
- `text_reference_to_structured_step`: a template reads `.text` or `results.text` from an Agent or Completion step with an `outputSchema`; use `results.structured` for the typed payload because Completion text can differ after coercion or reissue.
- `empty_iterator`: an iterator step has no child steps.
- `conditional_step_reference`: a *template* reference from outside a branch into one of its arms. Legal; it renders empty only when that arm was not taken. This is what the builder's variable picker marks "may be empty". The same reference made from a branch condition is the error-severity `unguarded_condition_step_reference` instead, because a condition cannot survive the absent key.

Surface advisory warnings to the user rather than dropping them. A terminal side-effect step whose output nothing reads is a normal shape, not a finding: the checker does not flag it. Re-check the outstanding warning set before declaring the workflow ready and get acknowledgment for anything unresolved.

## Error Semantics

- Building rejections are HTTP 400 with `details: [{field, message, code, candidates}]`. Stable codes such as `unknown_agent`, `index_out_of_bounds`, `duplicate_key`, and the coherence finding codes, plus capped `candidates` echoes, make recovery mechanical: fix the named field using the echoed valid values.
- Not found (404, "Unable to find workflow") can be a policy denial: the workflow is out of the current org's access scope, not necessarily missing. See Connection in `SKILL.md`.
- Forbidden (403, "managed by version control") means a global workflow managed by version control. It cannot be edited via the API.
- `workflow_deprecated` (400): deprecated workflows reject building writes outright.
- A read-only MCP connection (scope `read:workflows` without `write:workflows`) can inspect workflows and call `list_workflow_building_options`, but every authoring write is rejected. When reads and catalog calls succeed while all writes fail on authorization, re-check the connection's granted scopes and reconnect with write access. Scope checks apply only on a single-org server; a server with org-selection tools bypasses OAuth scopes entirely, so uniform authoring-write failures there are policy or validation, not scope.

## The Building Catalog

`list_workflow_building_options` is the authoritative catalog for values available to the current org and target. Read it before choosing a selector; never guess. Rejection `candidates` are repair hints, not a second catalog. They can be absent, capped, ranked, or scoped differently from the proactive listing. Static enumerations such as input field types share their source, but dynamic org-scoped references do not guarantee full-catalog equality.

It takes `kinds[]` (required) and an optional `query` substring filter. Contextual catalogs also accept `workflowId` and one target position:

- `stepId` selects an existing step. Add `childStepId` to select an existing child under that iterator.
- `insertIndex` alone selects the top-level insertion position for a new step. For `promptTemplateVariables`, combine `stepId` with `insertIndex` to select a new child position under that iterator, including index `0` before the first child. Do not combine `childStepId` with `insertIndex`; `iteratorSources` also rejects `stepId` with `insertIndex`.
- `arm` names which side of a branch a position is in, and is required once `stepId` names a branch and `insertIndex` is given. Omitting it is rejected rather than defaulted.

The kinds:

- `agents`: agent step `config.agent` selector values (name, displayName, description, kind).
- `tools`: tool step `config.toolName` values, each with the `inputSchema` the step input must satisfy.
- `models`: model ids with aliases and token limits.
- `documentTemplates`: generateDocument `templateId` values, each with the `inputSchema` `inputData` must match.
- `connections`: agent step usable connections, each with its `optionsSchema`.
- `sections`: `update_workflow_details` `sectionKey` values.
- `events`: trigger `eventName` values and the filter fields each supports.
- `inputFieldTypes`: `configure_workflow_input` field selectors. Each entry carries `name`, `description`, `multiSelect`, and `fields`; each resource field carries `name`, `type`, `description`, and `optional`. Derive cardinality and resolved field access from the returned entry instead of maintaining a separate type list. Runtime resolution also adds `_resourceType`, which is intentionally absent from `fields`.
- `promptTemplateVariables`: without `workflowId`, returns the generic step-type catalog with placeholder step IDs; entries with `stepType` `(global)` are workflow roots such as `.Now`. With `workflowId` and a target position, returns concrete in-scope inputs, trigger values, earlier producer outputs, structured shapes, and iterator item variables. Use `stepId` plus `insertIndex` to inspect variables for a child before adding it, or `stepId` plus `arm` plus `insertIndex` for a position inside a branch arm: a step in an arm sees everything before the branch plus its own earlier arm siblings, never the sibling arm. Each contextual entry can include its concrete `expression`, `scope`, source IDs, `shape`, and `availability`: `always` for something every run supplies, `conditional` for a value that can be absent (a trigger-supplied input, or a step inside a branch arm), `opaque` where the shape is unknown, and `schema-derived` for a key read off a declared `outputSchema`. Read `availability` rather than assuming every offered variable is always populated.
- `promptTemplateFunctions`: the functions usable in step templates (`step`, `toJSON`, `pluck`, `dateInZone`) with signatures.
- `iteratorSources`: requires `workflowId` plus an existing iterator `stepId` or a new top-level `insertIndex`. `childStepId` is rejected outright (`childStepId is not valid for iteratorSources`), and so is `insertIndex` combined with `stepId`; `arm` is accepted and then silently ignored, because this kind's target is built without it. The target resolves through its top-level ancestor, so this kind reaches only a top-level iterator: an iterator inside a branch arm is rejected with "is not an iterator step" because that ancestor is the branch. For an arm-nested iterator, take the source grammar from `inputs-and-resources.md` instead. It returns target-valid canonical `source` and `sourceType` pairs with container shape, materialization behavior, and child item shape. Resource-list entries use `{{ .Input.<field>.entries }}`. Use the returned values instead of constructing sources by hand.

These references point to catalog kinds rather than enumerating values that are org-specific or change. When a write rejects a selector, use the catalog as the source of truth and treat any returned `candidates` as immediate repair hints.
