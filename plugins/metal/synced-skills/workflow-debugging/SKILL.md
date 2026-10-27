---
name: workflow-debugging
description: Applies when a user provides a Metal workflow run ID or asks why an existing run behaved as it did, including failures, missing tool calls, artifacts, outputs, approval state, or definition drift; it is read-only, while workflow edits and run actions belong to workflow-building and running-workflows.
---

# Metal Workflow Debugging

Use this skill when the user provides a run ID or asks a runtime-behavior question. Answer the user's direct behavior question from MCP run evidence first, then locate the fix surface. Conclusions about run or live-definition behavior require MCP-backed evidence.

This skill is read-only. It never calls building tools, `run_workflow`, `review_workflow_hitl_step` (the tool that approves or rejects a run paused at `AWAITING_APPROVAL`), or `rerun_workflow_run_from_step` (which creates a new run from a terminal one rather than inspecting it, and is a natural temptation once a failing step is identified). Workflow edits route to the `workflow-building` skill; resolving inputs, starting a run, and rerunning one route to the `running-workflows` skill.

## Connection

- This skill operates through a connected Metal MCP. If more than one Metal MCP is connected, pick one for the task and do not mix them.
- Servers differ by tool surface, not workflow tool behavior: a server that exposes org-selection tools (`get_orgs`, `select_org`, `get_current_org`) serves multiple orgs; a server without them is bound to a single org.
- On a single-org server: if tools are missing or fail to connect, the Metal MCP may not be connected, may be disabled for the org, or the user may be authed against a different org. Ask the user to confirm before concluding anything is broken, and direct them to re-auth when access looks wrong. If tools work but a workflow or run cannot be found, a not-found response can be a policy denial: the workflow exists but is out of the current org's access scope. Ask the user to confirm org access before concluding the workflow does not exist.
- On a multi-org server: every workflow tool fails with "missing org context" until an org is bound with `select_org` (find it with `get_orgs`, verify with `get_current_org`). The binding can expire mid-conversation; the same error later means re-select, not a broken connection. Access-policy gates are broadly bypassed on this server, so a not-found response usually means the wrong org is bound or the resource genuinely does not exist.
- Never proceed against an org the thread has not confirmed; this includes the org passed to `select_org`.

## Evidence Gathering

The evidence ladder, narrowest sufficient rung first:

1. `list_workflow_runs` finds runs. Filter with `resourceType: "workflow"` plus `resourceId` for one workflow's runs, `statuses`, and created-time bounds. Pages return up to 50 items.
2. `get_workflow_run` is the run-level surface: `dryRun`, summary status, input, resource refs, step summaries, outputs, citations. Inspect `dryRun` at the start of every diagnosis. `view` accepts `overview`, `steps`, `outputs`, `errors`, `failures`, `artifacts`, `citations`, or `full`. `view: "failures"` is a triage view: it returns failed steps but silently caps each iterator's failed-item details at 50 with no continuation cursor. Page `iteratorItems` when completeness matters.
3. `get_workflow_run_step` is the step-level surface: run-captured step definition, outputs, transcript, tool calls, HITL state, iterator items, execute-code evidence. `view` accepts `overview`, `outputs`, `transcript`, `toolCalls`, `artifacts`, `errors`, `iteratorItems`, `hitl`, `execution`, or `full`. Use `itemIndex` plus `childStepId` to drill into one iterator item's child step.
4. `get_workflow` and `get_workflow_step` when diagnosis depends on the saved definition, prompt text, step configuration, or trigger/input/output setup. `get_workflow` returns a compact projection with safe scalar reasoning and tuning fields, previews, and summarized connection and skill data. Use `get_workflow_step` for the full safe saved step before a field-sensitive conclusion; it redacts secret fields and secret-like string values, so never present a redacted prompt or config as the literal stored value. Run evidence carries its own `workflowVersion`; compare it against the live workflow `version` when drift between the run and the current definition matters.

Response mechanics:

- A branch-arm child outside an iterator is read by its own `stepId` on both step-level tools, including arms nested in arms. A child inside an iterator uses the enclosing iterator `stepId` plus `childStepId`; add `itemIndex` for runtime evidence.
- Large text fields arrive as truncated previews. When `truncated` is true, follow the attached `expandInstructions` verbatim instead of guessing field paths. See the `workflow-building` skill reference `mcp-run-evidence.md` for the read views, the projection and paging interface (`fieldPath`, `cursor`, `limitItems`, `limitChars`), and definition-drift comparison.
- Artifacts, documents, and output records expose run metadata such as IDs, names, content types, sizes, timestamps, and sometimes signed URLs. Treat metadata as enough for presence, naming, count, and type conclusions. Inspect file contents only when the evidence includes an accessible URL or the user provides the artifact.
- Treat `resultPreview` as potentially sensitive because it does not currently receive the structural secret scrubbing used by expansion. Prefer pageable `outputs.results` for reporting. It is a complete but scrubbed JSON projection; concatenate its `cursor` and `limitChars` pages before decoding, and do not present redacted values as literal stored values. Tool-call arguments are also scrubbed in previews, views, and expansions. `outputs.result.content` is only the display-oriented text or structured-content view, not the authoritative full map.

## Run Statuses

| Status | Meaning | Terminal |
| --- | --- | --- |
| `QUEUED` | Created and waiting to execute | No |
| `PENDING` | Step-level initial status and a valid `list_workflow_runs` filter value; runs move `QUEUED` to `RUNNING` without resting at a run-level `PENDING` | No |
| `RUNNING` | Actively executing a step | No |
| `AWAITING_APPROVAL` | Paused at a human approval step | No |
| `COMPLETED` | All steps and finalization completed | Yes |
| `FAILED` | A step failed or finalization failed | Yes |
| `CANCELED` | A user canceled the run | Yes |
| `REJECTED` | A human approval step is rejected | Yes |
| `HALTED` | An executing step requested a clean stop through `halt_workflow`; see `haltReason` | Yes |
| `SKIPPED` | Step-only, like `PENDING` above: a child of a branch arm that was not taken, or anything under one. Runs never carry it | Yes (as a step) |

Typical paths:

- Happy path: `QUEUED` to `RUNNING` to `COMPLETED`.
- Human approval path: `RUNNING` to `AWAITING_APPROVAL` to `RUNNING` after approval, then `COMPLETED`.
- Rejection path: `AWAITING_APPROVAL` to `REJECTED`.
- Failure path: any non-terminal status to `FAILED`.
- Halt path: an executing step calls `halt_workflow` under an explicit halt condition, and the run becomes terminal `HALTED`.

If a run looks stuck, start with run status, `currentStepId`, step timestamps, and step error. If the MCP tools themselves fail or disappear, follow Connection before assigning blame to workflow logic.

## Run Provenance

- Use `triggerType` to identify whether a run started through manual, email, event, schedule, or webhook execution. For scheduled runs, `scheduleId` identifies the schedule that fired.
- Do not infer scheduled origin from `triggeredBy`; automatic triggers can attribute runs to a configured triggerer.
- Treat `attempt` only as a weak ordinal. It can be caller-supplied, failed-run retries can increment it, and reruns commonly reset it to 1. Establish rerun lineage from the rerun mutation response's `sourceWorkflowRunId` or other explicit evidence.
- `originType: "deal_action"` identifies a run created from a deal action.
- Inspect diagnostic `error` and human-readable `errorReason` together. The projection exposes the former as `errorPreview` and the latter directly.
- For `HALTED`, report the projected run or step `haltReason`. Metal completes the halt without dispatching later steps and skips normal success output rendering and completion notifications.
- Run citations, output files, text outputs, and document files expose `sourceStepId` when the producer can be resolved. Iterator-produced evidence also exposes `itemIndex` and `childStepId`; use all three coordinates to identify the repeated child execution.

## Dry-Run Evidence

State the run's `dryRun` value near the start of the diagnosis. When it is true:

- Read-only operations executed normally.
- Annotation-gated writes did not execute. A typed dry-run result proves deserialization and declared struct-tag validation only; execute-time business rules remain untested. Absence of `validation` identifies the typed path. `validation: "echoed"` proves non-execution and argument echoing, not input validation or provider acceptance.
- Authorization and provider-side validation for each skipped write remain untested. Successful live reads remain evidence for those read operations. Trigger delivery, provider-created IDs, and downstream behavior that needs real write responses also remain untested.
- User-facing lifecycle, chat, and approval notifications were suppressed. Persistent run state, artifacts, output records, and completion post-processing can still be created. An unannotated write tool can execute normally. A human-review step can still persist `AWAITING_APPROVAL`.
- A downstream failure can result from a missing real write response or ID; establish that from step evidence instead of assuming it.
- Dry-run control flow can diverge from non-dry execution. For example, gated `halt_workflow` does not register the halt, so the terminal status can differ from a live run.

For a dry-run diagnosis, report observed typed and echo-only calls plus only the evidence gaps material to the conclusion. This skill remains read-only. A requested reproduction routes to `running-workflows` and follows its Run Mode rules.

## Step Evidence By Step Type

| Step type | Main run evidence |
| --- | --- |
| `agent` | Results-map preview plus `toolCallSummary` on the run detail; complete scrubbed results JSON via `outputs.results`; transcript and flattened tool-call evidence with scrubbed arguments; citations; artifact metadata. Structured output only when the step has an output schema |
| `completion` | Complete results-map preview, including text and finish reason; pageable results JSON via `outputs.results`; structured output only when the step has an output schema |
| `tool` | Complete arbitrary tool result-map preview and pageable `outputs.results` JSON; rendered input on the run-captured step `definition` |
| `iterator` | `iteratorSummary` totals on the run detail; per-item index, input, status, error, and child-step outputs via `view: "iteratorItems"`; single-item drill-down via `itemIndex` plus `childStepId` |
| `humanInLoop` | `hitlSummary` on the run detail; payload, reviewer-facing items, summary, and `approvedReviewItemIds` via `view: "hitl"` |
| `generateDocument` | Rendered document metadata in run `outputs.documentFiles` and the step's filename and output fields |
| `executeCode` | Script, rendered input, effective `inputFiles`, expected `outputFiles` declarations, and paths via `view: "execution"`; stdout, stderr, and return code in transcript message parts; actual files in `outputs.outputFiles`, `outputs.documentFiles`, or `view: "artifacts"` as appropriate |
| `branch` | `results.branch` (`"then"` or `"else"`) and `results.decision` (the bool) on the branch step itself; once a decision is persisted the untaken arm's children are recorded `SKIPPED` with no output, and a branch that never decided leaves both arms `PENDING` |

Steps with a declared `outputSchema` are held to it at run time. Agent steps submit through an injected structured-submission tool, visible in `transcript` and `toolCalls` evidence, sometimes with a final forced submission turn; completion steps validate with coercion and one re-issue. A step that cannot produce schema-valid output fails loudly rather than passing unvalidated output downstream, so a schema-validation step failure points at the output schema or the step prompt, not at silent data corruption.

Common failure locations:

- Prompt or definition issue: wrong input variable, wrong step reference, vague instructions, bad handoff contract, bad output schema, wrong output section template.
- Agent issue: reasonable workflow prompt but poor tool choice, bad search strategy, missing file handling, missing citations, or missing artifact export.
- Tool issue: the right tool runs, but arguments, lookup logic, returned data, or tool error behavior looks wrong.
- Execution issue: evidence points to template rendering, resource resolution, iterator item handling, HITL pause/resume, artifact collection, or output finalization rather than a prompt/tool problem.

Workflow templates use Go `text/template` syntax; a missing terminal key renders the sentinel `<no value>` (not empty), so a reference typo can silently surface as `<no value>`, while dereferencing through a missing or non-object intermediate fails the run. Template syntax, input and resource access, step types, and structured output contracts are documented in the `workflow-building` skill references; load those when a diagnosis turns on exact template or input forms.

## Iterator Debugging

Iterator steps materialize source data into items and run child steps per item.

- Confirm the iterator source path matches the source type: data entity, resource list entries, structured output array, or HITL approved operations.
- Confirm the referenced step runs before the iterator.
- Confirm structured-output iterator sources target an array field.
- Confirm child prompts use `.Input.item` unless the workflow sets a custom context variable.
- Use `view: "failures"` or step `view: "errors"` for triage only; each iterator's failed-item list is capped at 50 with no continuation. For exhaustive diagnosis, page `view: "iteratorItems"` or `fieldPath: "iterator.items"` and inspect every item's `status` and `error` before blaming a downstream summarizer.
- Keep status and error at item scope. A child summary with `executionStateAvailable: false` omits child status, timing, halt reason, and error because the run does not persist child-specific execution state. Attribute a child through its results, transcript, tool calls, citations, artifacts, and provenance coordinates.

## Human Approval Debugging

Human approval steps pause the run at `AWAITING_APPROVAL`. On approval the run continues; on rejection the run becomes `REJECTED` and no later steps execute.

- Check whether the run status is `AWAITING_APPROVAL`, `REJECTED`, `FAILED`, or resumed.
- Check reviewer assignment and review metadata in the step's `hitl` evidence.
- Check whether `reviewPayloadInput` rendered an object with an `operations` array of review envelopes.
- Check whether downstream steps read `humanInLoopState.approvedPayload` rather than the reviewer-facing message.
- For editable review, check whether approval submitted field edits and whether edited values appear at `approvedPayload.operations[*].value.review.editedValue`.
- If downstream writes ignore reviewer edits, inspect the provider write or collapse step that converts selected field fragments into write operations.

Review payload and editable-review contracts are documented in the `workflow-building` skill reference `human-review.md`.

## Output And Notification Debugging

- Workflow output schema uses `x-template` expressions to pull step results into final run output. Schema rendering failure fails the run during finalization.
- Each output section key must match a top-level output schema property. Unlisted top-level keys append after configured sections.
- Final run output defaults to `{"status":"completed"}` when there is no output schema or the schema renders nothing.
- A completed run can still lack the desired file. Distinguish a platform-level success from a validation-gated skip, an execute-code step with no declared `outputFiles`, an output glob that matched the wrong count, or files published as artifacts without first-class Output records.
- First-class run files come from `outputs.outputFiles`, generated-document records come from `outputs.documentFiles`, and raw step artifacts come from step `view: "artifacts"`. `execution.executeCode.outputFiles` is the expected or effective declaration, not proof that a file was produced. Use `results.outputIds` and actual output records to determine whether the UI should show an execute-code file.
- An invalid HTML section does not fail the run. Finalization clears that section's content and records the validation message at `outputs.sections[].error`; inspect it when a completed run has an empty or degraded section.
- The run projection normalizes each output section `type` to `text` or `html`, preserves a configured title including an empty title, and generates a title only for a synthesized section. Inspect these projected fields.
- Completion notification conditions are templates that must render to a boolean. If the condition renders false or errors, the run still completes and persists output but skips the notification.
- Evidence lives in the run detail `outputs` bundle and `outputConfig`.
- To hand the user a file rather than describing it, see `references/mcp-run-evidence.md`'s "Downloading A Run's Output Or Artifact File" section. A populated URL on an actual output, document, or artifact record is a time-boxed download link fetched outside the MCP call. A missing URL is inconclusive; refresh the evidence or report download availability as unknown.

## Diagnosis Rubric

Do not choose a fix surface until you have read the run evidence, answered the user's direct behavior question when possible, and inspected the relevant step prompt, tool call, output, error, or definition slice. The four fix surfaces:

- Workflow definition or step prompt: the workflow asked for the wrong thing, omitted context, used bad variables, or the issue is isolated to one workflow.
- Agent prompt or agent configuration: the failure is agentic and systemic, recurring across workflows that use the same built-in agent despite reasonable step prompts.
- Tool behavior or tool response shaping: the right tool runs but its arguments, matching logic, returned data, or error handling looks wrong, and the problem is reusable across callers.
- Workflow execution behavior: sequencing, template rendering, resource resolution, iterator dispatch, HITL pause/resume, artifact handling, or output finalization rather than prompt or tool quality.

Use `references/workflow-run-diagnosis-rubric.md` for the full rubric: signals per surface, the next MCP evidence to read, and step-type playbooks.

## Customer Quality Signals

When diagnosing a run, also surface evidence relevant to customer-perceived quality alongside the technical diagnosis:

- Citation coverage: did agent steps cite sources for factual claims?
- Output readability: are company names, financials, and dates human-readable in the final output?
- Completeness: did every configured output section render content?
- Hallucination signals: do structured output fields trace back to tool call results?

These signals do not change the fix surface diagnosis. They add a customer-quality dimension to the report. Evaluate the four quality axes directly: data grounding, output readability, completeness, and correctness.

## Response Rules

- Answer the narrow run question first.
- Use a stable diagnosis shape for run investigations: run mode (`dryRun`), observed status, decisive step, direct cause, artifacts or output records produced, whether the live definition differs from the run version, and the justified fix surface.
- Distinguish observed run evidence from proposed workflow changes.
- Cite the run step, tool call, artifact metadata, output field, or error that supports each conclusion.
- Say what evidence is missing when a fix surface is not justified yet. If run evidence cannot be obtained, stop and say diagnosis is blocked rather than inventing workaround-based analysis.
- If workflow evidence points to an external system lookup, hand off to the matching connector skill after the workflow diagnosis is established.

## Boundaries

- This skill never creates or updates workflow definitions, starts workflow runs, or performs run actions, in any environment.
- If the user wants to reproduce the behavior, start a run, or resolve its inputs, use the `running-workflows` skill.
- If the user asks how the workflow definition should change, use the `workflow-building` skill after answering the run behavior question.
- Definition-drift questions are answered by comparing the run's captured `workflowVersion` evidence against the live definition from `get_workflow`.

## References

- `references/workflow-run-diagnosis-rubric.md`: fix-surface rubric, signals, the next MCP evidence to read, and step-type playbooks.
- Template syntax, input and resource access, step types, workflow agents and tools, output sections, and HITL payload contracts: see the `workflow-building` skill references.

## When References Run Out

These references plus MCP run evidence explain most defects. When they cannot, the cause might be in Metal's platform rather than the workflow definition. One durable fact worth keeping: some global workflows are managed by version control and cannot be edited through the building API (a 403 "managed by version control").
