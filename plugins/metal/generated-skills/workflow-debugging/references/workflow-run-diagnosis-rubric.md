# Workflow Run Diagnosis Rubric

Use this rubric to decide where a workflow issue should be fixed after you have read MCP-backed run evidence.

## Core Rule

Do not choose a fix surface until you have:

1. Read run evidence from `get_workflow_run` and, for suspect steps, `get_workflow_run_step`.
2. Answered the user's direct behavior question if possible.
3. Reached for the skill references for the suspect step type. When the MCP evidence and references still cannot explain the behavior, escalate to Metal (see When Evidence Is Insufficient) rather than guessing.

If run evidence cannot be obtained, follow the Connection section in `SKILL.md` and stop rather than inventing workaround-based analysis.

## Hang Triage

When the user's report sounds like hanging, stuck, or stalled:

1. Start with run status, `currentStepId`, step timestamps, and step error from `get_workflow_run`.
2. If the MCP tools themselves error or are missing, follow Connection in `SKILL.md` before assigning blame to workflow logic.
3. If the question depends on whether the saved definition changed since the run, compare the run's `workflowVersion` against the live definition from `get_workflow` before choosing a fix surface.

## Standard Diagnosis Shape

For a run investigation, answer with:

1. Observed run status and workflow version.
2. Decisive step or finalization phase.
3. Direct cause shown by evidence.
4. Artifacts, document files, and first-class output records produced.
5. Whether the live workflow definition differs from the run version.
6. Fix surface and why it belongs there.

## Primary Fix Surfaces

Each surface below is identified by its signals. When the run evidence and the skill references cannot explain the behavior, the cause likely sits in Metal's platform rather than the workflow definition; escalate (see When Evidence Is Insufficient) instead of guessing.

### 1. Workflow definition or step prompt

Choose this when the run shows the workflow asked for the wrong thing, omitted key context, used bad variables, or encoded workflow-specific instructions that caused the behavior.

Common signals:

- The step prompt itself is wrong, vague, or missing required context.
- The step references the wrong variable or previous step output.
- A completion step behaves badly but its issue is clearly in the configured prompt or system prompt.
- The issue appears isolated to one workflow rather than systemic across many workflows.
- A deterministic validator or render gate rejected output for workflow-specific rule wording, thresholds, or artifact policy.

Read next:

- The run-captured step `definition` from `get_workflow_run_step`, then the saved definition from `get_workflow_step`.
- If the workflow is global and managed by version control, it cannot be edited through the building API (a 403 "managed by version control").

### 2. Agent prompt or agent configuration

Choose this when the problem is agentic and systemic, or when the configured agent's instructions or its tool set are the likely cause.

Common signals:

- The agent made a bad search or matching decision even though the workflow step prompt looked reasonable.
- The same style of failure would likely recur across workflows using the same built-in agent.
- The issue looks like poor tool choice, poor citation behavior, or bad agent operating procedure.
- The step is clearly an agent step and the failure does not look specific to one workflow prompt.

### 3. Tool implementation or tool response shaping

Choose this when the workflow used the right tool, but the tool behavior, matching logic, returned data, schema, or error handling looks wrong.

Common signals:

- The transcript clearly shows the relevant tool call, but the arguments or returned data imply bad matching or lookup logic.
- A behavioral question like "did it try a fuzzy provider-record match?" points to specific tool-call evidence.
- The tool returned data that misled the agent or step.
- The problem looks reusable across callers of the same tool.

Custom-tool note:

- If the tool is absent from the current Metal tool catalog, treat it as a custom tool or adapter before assigning the fix to a shared Metal tool.

### 4. Workflow runner or execution code

Choose this when the symptom implicates orchestration rather than prompt or tool quality.

Common signals:

- Wrong step sequencing.
- Status transition bugs.
- Resource resolution issues.
- Template rendering issues.
- Iterator dispatch or hydration issues.
- Human-in-loop pause/resume problems.
- Artifact or document handling problems.
- Evidence shows sound workflow logic and faulty execution state.

Run evidence supports conclusions about stored artifact and document metadata only. Content-level conclusions require separate backing-file or API inspection.

## Step-Type Playbooks

### Agent steps

Ask:

- What did the transcript show in the conversation?
- Which tool calls appear in `view: "toolCalls"` evidence?
- Did the agent's behavior match the step prompt?
- For a step with an output schema, did the transcript show a structured submission, a forced final submission turn, or a schema-validation failure? A validation failure points at a too-constraining or malformed schema, or a prompt that cannot support the required fields.
- Is the problem workflow-specific or systemic to the agent prompt and tooling?

### Completion steps

Ask:

- Is the prompt or system prompt itself the issue?
- Is the structured output schema too constraining or malformed?
- Is the behavior likely to be fixed by editing the workflow definition rather than by a Metal platform change?

### Tool steps

Ask:

- Did the tool run?
- What exact input did it receive?
- What exact output or error did it return?
- Does the bug live in lookup or matching logic, output shape, or step wiring?

### Iterator steps

Ask:

- Did the parent iterator materialize the expected item set?
- Did items fail across the set or only at specific indexes? Keep persisted `status` and `error` at item scope. A child summary with `executionStateAvailable: false` has no child-specific status, timing, halt reason, or error.
- Which child produced the decisive output or failure evidence? Use the child's results, transcript, tool calls, citations, and artifacts, plus `sourceStepId`, `itemIndex`, and `childStepId` when present. Check `errorPolicy`: `failFast` (default) fails the whole run on the first child failure, while `continue` skips failed items and keeps going.
- Is the issue in the child step prompt or in iterator orchestration?
- Did hydration of iterator items make the run look wrong?

### Human-in-loop steps

Ask:

- Did reviewer assignment or review metadata already explain the pause or failure?
- Did the run select the wrong reviewer, or did it skip assignment intentionally?
- Did `reviewPayloadInput` render an object with an `operations` array?
- Did downstream steps consume the approved payload rather than the reviewer-facing message?

### Generate-document steps

Ask:

- Did `generateDocument.inputData` or the filename template render incorrectly?
- Does the rendered input match the work product template `inputSchema`?
- Did the step produce `results.filename`, `results.s3Key`, and an output record, or did it fail at render time?
- Does the failure point to the upstream data-producing step, the template schema or script, or output finalization?

### Branch steps

The usual complaint is "the wrong half ran", so establish what the condition actually saw before reading the arms.

Ask:

- Which arm ran? The branch step's own `results.branch` is `"then"` or `"else"` and `results.decision` is the bool. Do not infer the arm from which children have output.
- Was the decision right given the inputs? Read the condition off the definition with `get_workflow_step`, then read each value it names from run evidence: `input.<key>` from the run's `input`, `steps["<id>"].results.structured.<key>` from that step's output, `steps["<id>"].items[].status` from the iterator's per-item evidence.
- If the branch step itself FAILED, the message names the cause. `branch condition must evaluate to a bool, got <type>` means the expression is not a predicate. `branch condition evaluation: no such key: <key>` means it read something absent: a step in an untaken arm (guard with `"<id>" in steps`), or an optional input the run did not supply (guard with `has(input.<key>)`). Authoring now blocks the unguarded arm read, so seeing it in a run points at a workflow saved before that rule, or at a guard that is present but does not actually cover the read it sits next to.
- A branch that never decided seeds no arm children at all, so both arms read `PENDING` rather than one of them `SKIPPED`, and every step under them looks like it is still waiting. Two arms pending under a branch that is FAILED, CANCELED, or halted is that shape, not a stuck run: diagnose the branch step, not its children. `SKIPPED` children mean a decision was persisted, by this branch or by an enclosing one: a branch sitting in an outer branch's untaken arm is itself `SKIPPED`, and its own unrecorded children read `SKIPPED` with it even though it never evaluated its condition.
- String equality is exact, so `== "Diligence"` does not match `"diligence"`. This is the trap that yields a defensible-looking wrong answer rather than an error; numeric comparison against a run value works with either an integer or a decimal literal, and the mismatched form that does not (`size(...) > 0.0`) is rejected at save time rather than reaching a run.
- Presence versus emptiness: `has(input.<key>)` is false only for an optional input the run omitted. A field that declares a default is always present, so `has()` on it is true even when the caller sent nothing.
- Downstream of the branch, a template reading a skipped arm's step renders the `<no value>` sentinel rather than failing, so a garbled prompt further on can be the real symptom of an arm you did not expect to skip.

### Execute-code steps

Ask:

- Did the rendered `Input` produce the expected JSON object, and did declared `inputFiles` upload?
- What were `results.exitCode`, `results.stderr`, and stdout? `view: "execution"` shows the script, rendered input, effective file declarations, and runtime paths.
- Did the effective `inputFiles` show the expected `filename` or `dataEntityId` and sandbox `path` after template rendering, and did the rendered `workingDirectory` in the execution audit match expectations?
- Do two items' outputs look identical (same values, same cells)? Iterator children share one sandbox filesystem, so a constant path is last-writer-wins: a child can overwrite a sibling's file and read the wrong item's data. Output labels can still look correct because a script may rewrite them to the item's own configured filename; compare values, effective inputFiles paths, and item start times before trusting the numbers.
- Did declared `outputFiles` publish, or did a glob match zero or more than 25 files?
- If the user expected a UI file, did the matching `outputFiles` entry set `createOutput: true`, and did the step produce `results.outputIds` that appear in `outputs.outputFiles`?
- With an `outputSchema`, did stdout parse as a single JSON value matching the schema?

Failure order is input render, then input-file upload, then script execution. A step with `outputSchema` next parses stdout as JSON, attempts coercion, and validates the schema. Output-file publishing runs after structured-output validation.

### Completed run with no desired artifact

Ask:

- Did the run complete because the workflow intentionally skipped rendering after a validation or decision gate?
- Did the step publish no artifacts because `outputFiles` was empty or conditional output paths selected a non-matching branch?
- Did the step create raw artifacts but omit first-class Output records because `createOutput` was false?
- Did the final output summary mention a file that `outputs.outputFiles` does not contain?

Treat this as a run-result diagnosis, not an infrastructure failure, unless a step error or finalization error says otherwise.

### Validator false positives and false negatives

Ask:

- What did the model or code actually output?
- Which validator rule rejected or accepted it?
- Does the rejected text satisfy the source skill intent despite missing a brittle keyword, phrase, or shape?
- Does the accepted text contain deal-killer or gating language that should have failed?

Choose the workflow definition or step implementation when the validator belongs to one workflow. Choose a shared tool or Metal platform fix only when the behavior is reused across workflows.

## Behavioral Questions Come First

If the user asks a narrow behavioral question, answer it directly from run evidence before escalating to root cause.

Examples:

- "Did step 2 try to find Metal Industries with a fuzzy provider-record match?"
- "Did the agent ever call the search tool?"
- "Did the resolver assign anyone?"

Prefer statements like:

- "Yes, the step transcript shows step 2 calling the provider search tool with ..."
- "No, the step never attempted a provider lookup; it stayed on the platform connection ..."

Only after answering that question should you decide where the fix belongs.

## When Evidence Is Insufficient

If you cannot justify a fix surface yet:

- Say what is missing.
- Avoid speculative root-cause claims.
- If the missing evidence is the run evidence itself, follow Connection in `SKILL.md` and stop rather than inventing workaround-based analysis.
- When the run evidence and these references cannot explain the behavior, the cause might be in Metal's platform rather than the workflow definition.
