# Workflow Step Types

This reference covers workflow step behavior and handoff surfaces. Existing selectors, prompt fields, output shape, artifact filenames, template references, and review payload contracts are downstream dependency surfaces.

## Step Shape

Every step carries `id`, `name`, and `type`. A legacy top-level `timeoutSeconds` can appear in a saved or read projection, but the building tools do not author it and the runner does not enforce it. Tool and execute-code timeouts are configuration-specific. Tool omission uses the tool or runner default; execute-code accepts 1 through 600 seconds and uses the sandbox default when omitted. Zero does not mean unlimited. Agent, completion, and execute-code steps can also carry an `outputSchema`.

## Agent

Agent steps run a workflow-capable agent with tools, connections, and a prompt-like `Input`.

- The built-in Workflow Agent is the default general-purpose agent when the step needs tool use, retrieval, file inspection, API work, reasoning over source material, or artifact creation. Agent selector values are org-specific; query `list_workflow_building_options` kind `agents` for valid names and descriptions, and preserve exact inspected names in existing definitions.
- Specialized agents fit provider-specific or internal workflow roles.
- Agent steps use the agent-configured model unless `model` overrides it. Select an override from models with `workflowAgentStepEligible` in `list_workflow_building_options` kind `models`.
- `reasoningEffort` requires an effective step model. Select a value from that model's `supportedReasoningEfforts`. A same-type update can set `reasoningEffort` without restating a model when the saved step already has one.
- Agent steps surface `results.text`, `results.structured` only when the step has an `outputSchema`, `results.outputIds` when the agent creates outputs, and `results.templateInputData` for the Data Analysis Orchestrator. With an `outputSchema`, `results.text` and the top-level `.text` compatibility field contain the serialized validated payload, including when the transcript has no final prose or ends with prose after submission. Typed consumers should read `results.structured`, normally through `toJSON`.
- An agent step's `outputSchema` is enforced at run time through a structured-submission tool and a resolution ladder that fails the step loudly when no schema-valid output can be resolved; `structured-output.md` covers the contract.
- For sandbox-generated user-visible files, the prompt must require `sandbox_download` and then `create_output` with the artifact ID returned by `sandbox_download`.

## Completion

Completion steps make a single LLM call over `Prompt` and optional structured output.

- Completion steps fit normalization, classification, validation, and notification gates that are their own responsibility; steps that need tool use emit structured output directly through an agent-step `outputSchema`.
- They surface `results.text` and `results.finishReason`, plus `results.structured` when the step has an `outputSchema`.
- Completion `reasoningEffort` accepts a value from the selected model's `supportedReasoningEfforts` in `list_workflow_building_options` kind `models`.
- With an `outputSchema`, completion text can differ from `results.structured` after coercion or reissue. Typed consumers should read `results.structured`, normally through `toJSON`.
- When consuming agent output, reference the agent text with `{{ (index .Steps "<agentStepId>").text }}`.
- When consuming prior structured output, embed it with `{{ toJSON (index .Steps "<priorStepId>").results.structured }}`.

## Tool

Tool steps execute one registered tool directly.

- The building tools accept Tool `Input` only as a string template. Render structured arguments as a JSON string.
- For a string: if the rendered string parses as JSON, the tool receives that JSON object; otherwise the tool receives `{ "input": "<rendered text>" }`.
- Saved visual-builder and runtime definitions can contain object input, which the runner supports but the building tools cannot create or replace. On a same-type update, omit `input` to preserve an existing object. Supplying `input` replaces it with the authorable string form.
- A tool's `inputSchema` comes from `list_workflow_building_options` kind `tools`.

## Execute Code

Execute-code steps run declared Python code in the sandbox with rendered JSON input and declared file inputs or outputs.

- `executeCode` fits deterministic code, file parsing, or a schema-normalized JSON stdout payload without agent tool turns.
- Structured output is opt in through `OutputSchema`; stdout must be a single JSON value, validated against the schema with coercion attempted before failure, before it appears at `results.structured`. Without `OutputSchema`, stdout remains text even when it is valid JSON.
- Runtime libraries, helper scripts, paths, and package-install limits are in `execute-code-runtime.md`.
- The script is literal Python, not a template. It reads rendered workflow input from the JSON file path in `sys.argv[1]`.
- `inputFiles[]` each carry exactly one of `filename` or `dataEntityId` (mutually exclusive) plus a required template-rendered `path` that must render to an absolute non-glob destination. `filename` resolves against attached workflow files and prior artifacts; `dataEntityId` stages a platform data entity by ID and must render to a 24-character hex ObjectID. Both selectors, `workingDirectory`, `outputFiles[].path`, and `outputFiles[].filename` are template-rendered. Prefer exact filenames; partial filename matching is only acceptable when known unique. `inputFiles[]` does not support glob patterns.
- When `inputFiles` are configured, the rendered `Input` must be a JSON object; an empty input is `{}`. The runner injects an `_inputFiles` array into that object, so `_inputFiles` is reserved.
- Iterator child execute-code steps receive an `_iterator` context (`itemIndex`, `stepId`, `childStepId`, `childStepIndex`) usable in execute-code working directory, input selector (`filename`, `dataEntityId`), input path, output path, and output filename templates.
- Files are published only through declared `outputFiles`. A glob `outputFiles[].path` expands after the script exits, sorts file matches, fails when it matches zero files or more than 25, and rejects a non-empty `filename`.
- `outputFiles[].createOutput: true` creates first-class run Output records that appear in the workflow run UI and records IDs in `results.outputIds`.
- Outputs: `results.text` and `results.textS3Ref` (stdout), `results.exitCode`, `results.stderr` and `results.stderrS3Ref`, and `results.sandbox`. The `execution.executeCode` audit block carries the script and rendered input (surfaced by `get_workflow_run_step` view `execution`).
- `workingDirectory` is template-renderable and must render to an absolute non-glob path; omitted, it defaults to `/home/sandbox`. `timeoutSeconds` is 1 to 600; Python only.

## Iterator

Iterator steps loop over a list and run child steps for each item.

Call `list_workflow_building_options` with kind `iteratorSources`, the workflow ID, and the iterator's existing `stepId` or new top-level `insertIndex` before setting `source` or `sourceType`. The catalog filters out later producers and returns the canonical source, source type, materialization behavior, and child item shape for the target position. It reaches only a top-level iterator, so an iterator inside a branch arm has to be configured from the grammar in `inputs-and-resources.md` instead.

Common source patterns:

- Data entity rows: `{{ .Input.<fieldName> }}`
- Resource list entries: `{{ .Input.<fieldName>.entries }}`
- Generic array: `input.<fieldName>` or `{{ .Input.<fieldName> }}` with `sourceType: "array"`
- Structured output array: `{{ .Steps.<stepId>.results.structured.<arrayKey> }}`
- HITL approved operations: `{{ .Steps.<hitlStepId>.humanInLoopState.approvedPayload.operations }}`

Child prompts access the active item through `.Input.item` (and through `.Input.<contextVariable>` if the iterator sets one; `contextVariable` defaults to `item`). The item shape depends on the source:

- A `dataEntity` row is a flat map keyed by column header with string cell values: `{{ .Input.item.<Header> }}` or `{{ index .Input.item "Column Name" }}`. There is no `.columns` and no `.value` wrapper.
- A `resourceList` entry exposes `.columns` (`{{ (index .Input.item.columns "Column Name").value }}`) and `.Input.item.resource` for the entry's resolved resource.
- A structured-output or generic array item is the object itself: `{{ .Input.item.<field> }}`.
- An HITL approved operation is a reviewed envelope `{id, value, display?}`: read the operation through `{{ .Input.item.value }}`.

Object items are accessed directly; primitive items are wrapped as `{ "value": <v> }`.

Iterator behavior:

- `concurrency` defaults to 6.
- Iterator children share the run's one sandbox filesystem and run concurrently, so every path a child reads or writes must be item-unique (for example the item's document ID or itemIndex). A constant path is last-writer-wins across items; execute-code-runtime.md covers the rule.
- `errorPolicy` is `failFast` (default; the first child failure fails the iterator and the run) or `continue` (failed items are skipped and iteration proceeds).
- The building tools do not expose `mode`; passing `mode` returns `unknown_field`. Omit it on same-type updates to preserve any saved visual-builder value.
- Iterator and `humanInLoop` steps cannot be iterator children: step validation rejects a nested iterator outright, so there is no nested-iterator shape to build. A `branch` can be an iterator child, but its arms are then restricted (see Branch).
- An iterator with no child steps completes with an empty result and logs a warning. `empty_iterator` is an authoring advisory, not a run-output code. An iterator with zero source items also completes.
- With `errorPolicy: "continue"`, the iterator and workflow can complete while failed items retain their failed status and error evidence.

## Branch

Branch steps choose between two step lists. `condition` decides which one: `then` runs when it is true and `else` when it is false. Outside an iterator that decision is made once and held; inside one it is made per item (see the decision paragraph below).

`condition` is a single CEL expression that must evaluate to a bool. It is not a Go template: no `{{ }}`, and none of the template functions. Addressable identifiers:

- `input.<key>` for declared and trigger-supplied inputs.
- `steps["<stepId>"].text` and `steps["<stepId>"].results.structured.<key>` for any step that ran strictly before this branch. Only the bracketed string-literal form is accepted: a computed key and the dot form `steps.<stepId>` are both rejected at save time. Neither arm's own children are addressable, since neither has run when the condition is evaluated.
- `steps["<iteratorId>"].items` for a finished iterator's per-item entries, each with `.input`, `.stepOutputs`, `.status`, `.error`, `.index`. `.status` is an uppercase run status (`COMPLETED`, `FAILED`, `SKIPPED`).
- `now` (timestamp) and `triggeredBy` (the Metal user ID that started the run, empty when the run was system-triggered).
- Inside an iterator, the current item as both `input.item` and `input.<contextVariable>`, plus `iterator.itemIndex`. Prefer the declared context variable, since that is what the rest of that workflow's templates use.

CEL is typed, and how strict that is depends on where the value came from. A value the run supplies (`input.<key>`, a step's structured output) stays dynamic, so comparing it against either `5` or `5.0` works. A value CEL types statically gets no such latitude: `size(...)` is an `int`, so `size(x) > 0` is right while `size(x) > 0.0` has no matching overload and is rejected at save time. Prefer the plain integer literal. String comparison is exact, so `input.stage == "diligence"` does not match `"Diligence"`; use `lowerAscii` or `matches` for a looser test. Nothing coerces between a string and a number.

`has(input.<key>)` tests presence rather than emptiness: an optional input the run omitted is absent, so `has()` is false, while one supplied as `""` or `false` is present. A field that declares a default is always present, because the default fills the key before the condition is evaluated. `has()` accepts only a field selection, so `has(steps["x"])` is a parse error; to guard a step that may not have run, use map membership: `"x" in steps`.

Useful shapes:

- `size(steps["step_extract"].results.structured.contacts) > 0`
- `steps["step_ops"].results.structured.operations.exists(o, o.action == "create")`
- `steps["step_loop"].items.all(i, i.status == "COMPLETED")`
- `has(input.dryRun) && input.dryRun`

A branch outside an iterator decides once and keeps that decision. The arm is persisted before either side runs, under a write that lands only while the step carries no decision yet, so a redelivered event adopts the stored arm instead of evaluating again, and both arms' children are seeded from the stored arm. Do not read that as a pure expression, though: `now` is a live clock, and a branch inside an iterator is executed inline, deciding per item as that item runs, with no such fenced write. To branch on a judgement about unstructured content, put a completion step with an `outputSchema` before the branch and read its structured result in the condition.

Authoring the arms:

- `then` and `else` are inline arrays of steps on the branch config, so a whole branch with both arms is one `add_workflow_step` call. Each arm entry is `{type, name, config, outputSchema?}` with no `id`; the server mints those.
- After creation each arm child is addressable by its own step ID at any depth, including arms nested in arms: `update_workflow_step`, `move_workflow_step`, and `delete_workflow_step` all take the child's ID alone. `add_workflow_step` inserts into an arm with the branch's `stepId` plus `arm` set to `then` or `else`.
- A branch config always replaces as a whole value. Resending it mints new IDs for its arm steps, so every reference to an old arm ID breaks, and an arm left out of that resend is deleted rather than preserved. Editing an arm child by its own ID avoids both and leaves the rest of the branch alone; reserve the whole-config update for changing the condition or restructuring the arms deliberately.

Structural rules:

- At least one arm must be non-empty.
- Branch nesting is capped at depth 3, counted from the workflow root: a top-level branch is 1. An iterator neither adds a level nor resets the count, so a branch inside an iterator that itself sits in a depth-2 arm is depth 3, and a branch below that one is rejected. The cap bounds total tree complexity, not depth within one scope.
- Inside an iterator, directly or transitively, an arm may only hold `agent`, `completion`, `tool`, `generateDocument`, `executeCode`, and `branch`. `humanInLoop` would pause the run once per item, and `iterator` cannot be an iterator child at all.
- A structured-review `humanInLoop` step (one with `reviewPayloadInput`) is rejected in any arm, even outside an iterator. Plain approval steps are allowed in a top-level arm.
- Step IDs are unique across the whole tree, arms included.

Run surface:

- The branch step's own result is `results.branch` (`"then"` or `"else"`) and `results.decision` (the bool). There is no `results.reasoning`.
- The untaken arm's children are recorded `SKIPPED`, and anything below a skipped branch is unreachable rather than pending. Neither arm is seeded until the decision is persisted, so a branch that failed to evaluate leaves both arms pending instead.
- A skipped step is absent from the template context entirely. A template reference to one renders the `<no value>` sentinel; a *condition* reference to one is a run-time error that fails the branch step, which is why a condition reaching into a possibly-skipped subtree needs the `"x" in steps` guard. Authoring blocks the unguarded form, so this should only be reachable on a workflow saved before that rule.
- Two evaluation failures fail the step and the run, both with the offending step named: `branch condition must evaluate to a bool, got <type>` and `branch condition evaluation: no such key: <key>`.
- `rerun_workflow_run_from_step` treats the branch step and its arm children differently. Naming a step *inside* an arm carries the enclosing branch's recorded decision forward without re-evaluating the condition, re-enters that branch as running, and carries the untaken arm's records forward so downstream references into it still resolve. Naming the *branch itself* excludes it from the seed entirely, so the condition is evaluated fresh and may take the other arm this time. A rerun into an arm of a branch that has no prior run state, or none with a recorded decision, is rejected rather than guessed.

Authoring catches what it can decide from the expression alone, and the rest is left to the run:

- A result type the checker settles on as a non-bool is rejected when you save: `size(input.rows)` on its own, or a bare string. The check is deliberately one-sided, so anything still dynamic is accepted, and a bare `input.count` or `steps["x"].text` saves fine and only fails at run time with the bool message above. Compare explicitly rather than leaning on a value being truthy; CEL has no truthiness.
- A reference the condition makes into a branch arm it does not sit inside is an error, not an advisory, because an absent step is a missing key rather than an empty value. Add the `"<stepId>" in steps` guard and it clears; the checker exempts any step the expression membership-tests.

Coherence findings specific to conditions: `condition_syntax` (error) for an unparseable expression, a computed step key, or a dot-form `steps.<stepId>` read, `scope_violation` (error) for iterator context in a branch outside an iterator, `cross_branch_reference` (error) for a reference into the sibling arm, and `unguarded_condition_step_reference` (error) for an unguarded reference from a condition into an arm. The advisory `conditional_step_reference` covers the same reference shape made from a *template*, where an absent step renders empty and the run survives.

## Human Approval

Human approval steps pause for reviewer approval or rejection. Editable review payloads are selection-based and can include optional inline edits for review items that declare an editable capability.

- Structured review payloads must resolve to an object with an `operations` array.
- Downstream writes must consume `humanInLoopState.approvedPayload`, not the reviewer-facing message.
- For iterating approved operations after HITL, use `{{ .Steps.<hitlStepId>.humanInLoopState.approvedPayload.operations }}` and read the underlying operation through `{{ .Input.item.value }}` (each operation is a reviewed envelope `{id, value, display?}`).

`human-review.md` covers payload contracts and approval handoffs.

## Generate Document And Artifacts

Generate Document fits template-backed outputs when the workflow already has, or needs, a work product template render path. `generate-document.md` covers the data contract.

Generate Document outputs `results.filename`, `results.s3Key`, and `results.outputId` when Output record creation succeeds. The rendered document is also stored as a workflow artifact and run document.

Sandbox artifact generation fits custom DOCX, XLSX, PPTX, PDF, HTML, or similar files when the output is better produced by code inside an Agent or execute-code step. Agent-generated files must call `sandbox_download`, then `create_output` with the returned artifact ID. Execute-code files must be listed in `outputFiles`, and only entries with `createOutput: true` become first-class run Output records.

## Handoff Contracts

- Preserve visible dependency surfaces unless the user asks for a change.
- Put handoff instructions inside the prompt-like field that drives the step.
- `template-syntax.md` covers template paths and iterator source forms.
- `structured-output.md` covers `OutputSchema` contracts, runtime enforcement, and structured handoff key paths.
