# MCP Read Evidence And Projection

Use this reference when reading workflow definitions or run evidence through the Metal MCP read tools, or when a response arrives truncated and needs expansion. The building and debugging skills both rely on this model.

## Read Tools And Views

- `list_workflows`, `list_workflow_runs`: discovery. These tools use list pagination and do not accept `fieldPath`. `list_workflow_runs` filters on `resourceType` plus `resourceId`, `statuses`, `createdAfter`, and `createdBefore`, and pages up to 50 items.
- `get_workflow`, `get_workflow_step`: the saved definition. `get_workflow` returns compact step projections with safe scalar reasoning and tuning fields. `get_workflow_step` returns the full safe step definition and is the source for complete prompt text after secret scrubbing; it redacts secret fields and secret-like string values.
- `get_workflow_run`: run-level evidence. `view` accepts `overview`, `steps`, `outputs`, `errors`, `failures`, `artifacts`, `citations`, or `full`. `view: "failures"` returns failed steps plus at most 50 failed, canceled, rejected, or error-bearing items per iterator, with no continuation cursor. Use it for triage, then page the iterator items for completeness.
- `get_workflow_run_step`: step-level evidence. `view` accepts `overview`, `outputs`, `transcript`, `toolCalls`, `artifacts`, `errors`, `iteratorItems`, `hitl`, `execution`, or `full`. Use `itemIndex` plus `childStepId` to drill into one iterator item's child step.

Do not pass `view` and `fieldPath` together on the same call.

A branch-arm child outside an iterator is addressed by its own `stepId` on both step tools, including arms nested in arms. A branch-arm child inside an iterator remains an iterator child: use the enclosing iterator `stepId` plus `childStepId` for definition evidence, and add `itemIndex` for runtime evidence.

## Projection Interface

The four detail tools, `get_workflow`, `get_workflow_step`, `get_workflow_run`, and `get_workflow_run_step`, accept the same projection arguments for focused reads:

- `fieldPath`: a dot path into the response, for example `outputs.sections`, `transcript`, `iterator.items`, `input`, or `resourceRefs`. Returns just that field.
- `cursor`: an opaque cursor from a prior paged response.
- `limitItems`: page size for a collection field. Default 50.
- `limitChars`: character cap for a text field. Hard-capped at 100000.

An invalid `fieldPath` returns a `FieldPathError` carrying `validNearbyFieldPaths` and `validTopLevelFieldPaths` (capped at 25 suggestions), so a wrong path self-corrects on the next call.

## Previews And Expansion

Large text and JSON fields arrive as a preview object: `{text, contentType, truncated, originalLength, previewLength, expandInstructions}`. When `truncated` is true, follow the attached `expandInstructions` verbatim instead of guessing field paths; it is a ready-to-call follow-up (the right tool, ids, and `fieldPath`). Preview character budgets are 4000 by default, 1200 for short fields, and 8000 for long fields such as tool-call arguments.

Detail responses also carry an `expandableFields` array enumerating every expandable handle on that response, each with the tool and arguments to call.

## Result Maps And Display Content

A step summary builds `resultPreview` from the complete `results` map, but that preview does not currently receive the structural secret scrubbing applied to expansion. Treat it as potentially sensitive and do not repeat it in a report. Expand pageable `outputs.results` JSON to retrieve every result key in a scrubbed projection, including arbitrary Tool and HITL results and sibling fields such as `finishReason` or output IDs. Use `cursor` and `limitChars`, concatenate the returned text pages, then decode the complete JSON document. `limitItems` does not apply to this JSON-text field. The expansion is structurally complete but redacted, so do not present redacted values as literal stored values. Tool-call arguments are also scrubbed in previews, views, and expansions. `outputs.result.content` is a display-oriented convenience field that selects text or serialized structured output; it does not replace the complete results map.

## Provenance And Iterator Child State

Run citations, output files, text outputs, and document files can carry `sourceStepId`. Evidence produced inside an iterator also carries `itemIndex` and `childStepId`, which identify the repeated child execution that produced it. Runs also expose origin fields such as `scheduleId`, `originType`, and `attempt`. Treat `attempt` as a weak ordinal only: callers can supply it, retries can increment it, and reruns commonly reset it to 1. Establish rerun lineage from the rerun mutation response's `sourceWorkflowRunId` or other explicit surrounding evidence. The human-readable `errorReason` appears next to the diagnostic `errorPreview`.

Iterator items own their persisted status and error. A selected child summary sets `executionStateAvailable` to `false` and omits child status, timing, halt reason, and error when the run does not persist child-specific execution state. Use the item's status and error for item failure, then use the child's results, transcript, tool calls, citations, artifacts, and provenance coordinates for child attribution.

## Paging

Paged collection fields (`steps`, `citations`, `transcript`, `toolCalls`, iterator `items`) return a `page` object: `{fieldPath, limitItems, start, nextCursor, hasMore, total}`. Read the next page by passing `nextCursor` back as `cursor` with the same `fieldPath`.

## Versioning And Definition Drift

`get_workflow` and `get_workflow_step` accept a historical `version`. A run records the `workflowVersion` it executed at creation, and older runs can reflect older workflow-definition versions.

There is no diff tool. To check whether a run's behavior reflects the current definition, compare the run's captured `workflowVersion` against the live `get_workflow` version. When they differ and the drift matters, fetch the historical definition with the `version` argument and compare the relevant fields by hand.

## Artifacts Are Metadata, Plus A URL When One Exists

The read tools return artifact and document metadata: IDs, names, content types, sizes, and timestamps. A populated `url` is a current, time-boxed presigned download link. A missing URL is inconclusive: storage coordinates may be absent, the storage service may be unavailable, or presigning may have failed. Refresh the run or step evidence for a new URL before reporting availability as unknown. The read tools never inline file content; fetching content requires a separate request against a returned URL. Say so when a conclusion requires content-level inspection.

## Downloading A Run's Output Or Artifact File

To hand the user an actual file from a run rather than just describing it:

1. Locate the actual file record. Run or step `outputs.outputFiles` contains first-class Output files. `outputs.documentFiles` contains generated-document records. Step `view: "artifacts"` contains raw step artifacts. `execution.executeCode.outputFiles` contains expected or effective file declarations, not produced file records.
2. Read the actual record's `url` field. When present, it is a real presigned link, fetchable with a plain HTTP GET and no additional Metal authentication.
3. Treat the URL as time-boxed, not permanent. Fetch it while the conversation is active rather than caching it for later use, and re-fetch the run/step evidence for a fresh URL if enough time has passed that the old one may have expired.
4. When a record has no `url`, refresh the evidence once to request a new presign. If it remains absent, report download availability as unknown rather than claiming no stored file exists.
5. There is no MCP tool that returns file bytes inline. Getting the actual content is always a second request against the URL from step 2, separate from the MCP call that found it.
