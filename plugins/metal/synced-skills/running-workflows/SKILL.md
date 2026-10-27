---
name: running-workflows
description: Applies when a user wants to start, test, validate, or reproduce a Metal workflow through the Metal MCP, rerun a terminal run from a selected step, or approve or reject a paused human-review step, including cases where declared inputs must first be resolved; read-only investigation of an existing run belongs to workflow-debugging.
---

# Metal Workflow Running

This skill is a reference for the caller side of running a Metal workflow: given a workflow's declared `inputSchema`, how to resolve real user-supplied values into a valid `run_workflow` payload, start the run, and report basic status. The central concern is turning the user's request into values that satisfy the workflow's complete declared schema.

For the resolved runtime shapes a workflow step sees *after* a resource input is resolved, use the `workflow-building` skill's `references/inputs-and-resources.md`. For diagnosing run behavior beyond a basic status check (failed steps, iterator drill-down, HITL state, definition drift), use the `workflow-debugging` skill.

## Connection

- This skill operates through a connected Metal MCP. If more than one Metal MCP is connected, pick one for the task and do not mix them.
- Servers differ by tool surface, not workflow tool behavior: a server that exposes org-selection tools (`get_orgs`, `select_org`, `get_current_org`) serves multiple orgs; a server without them is bound to a single org.
- On a single-org server: if tools are missing or fail to connect, the Metal MCP may not be connected, may be disabled for the org, or the user may be authed against a different org. Ask the user to confirm before concluding anything is broken, and direct them to re-auth when access looks wrong. If tools work but a workflow cannot be found or run, a not-found response can be a policy denial: the workflow exists but is out of the current org's access scope. Ask the user to confirm org access before concluding the workflow does not exist.
- On a multi-org server: every workflow tool fails with "missing org context" until an org is bound with `select_org` (find it with `get_orgs`, verify with `get_current_org`). The binding can expire mid-conversation; the same error later means re-select, not a broken connection. Access-policy gates are broadly bypassed on this server, so a not-found response usually means the wrong org is bound or the resource genuinely does not exist.
- Never proceed against an org the thread has not confirmed; this includes the org passed to `select_org`.

## Metal MCP Tools

Schema/discovery: `list_workflows`, `get_workflow` (fetch `inputSchema`; `overview`/`steps` when a `string`/`text` field's purpose isn't clear from its description alone).

Resolution: `search_companies` / `get_company` (`company`), `search_people` (`person`), `search_documents` / `get_document` (`dataEntity`, `dataEntityMulti`), `list_lists` / `get_list` / `get_list_entries` (`resourceList`). No workflow tool resolves `folder` or `workspace`; see `references/input-resolution.md`.

Run tool: `run_workflow` creates a run. Set its per-run `dryRun` value according to the Run Mode rules below. A dry run records and executes the workflow under dry-run policy; it is not a definition preview.

Run-action tool: `review_workflow_hitl_step` resolves a run paused at `AWAITING_APPROVAL` by approving or rejecting its review items. It is mutative like `run_workflow`; call it only on explicit user direction and confirm before submitting. Review authority follows reviewer assignment (see the `workflow-building` skill's `references/human-review.md`).

Rerun tool: `rerun_workflow_run_from_step` starts a new run from a terminal one. Apply the same Run Mode rules as a new run. The optional `dryRun` override is set-only: `true` makes the rerun dry, while omission preserves the source run's mode. It cannot turn a dry source run into a non-dry rerun. The new run reuses the source input with the workflow's current definition. Every preceding top-level step must be `COMPLETED`; preceding siblings in the selected branch arm must be `COMPLETED` or `SKIPPED`. The target can be a top-level step or a descendant of the branch path recorded by the source run. A target in an untaken arm is not found, and iterator children cannot be targeted. A target inside a selected arm re-enters its enclosing branches with their recorded decisions and carries untaken-arm state forward; the target itself is not seeded. Targeting the branch step reevaluates its condition and may choose a different arm. On an ambiguous failure, check `list_workflow_runs` for a newly created run before retrying.

Status: `get_workflow_run` for status/output checks after a run starts; `get_workflow_run_step` with `view: "hitl"` to inspect a paused approval step before any review action.

## Run Mode

- dryRun: true controls one Run. It does not sandbox Workflow-definition edits, create a staging revision, or authorize a separate Workflow.
- Starting any run requires explicit user intent. An explicit dry-run request uses `dryRun: true`.
- Development and testing intent defaults to dry-run execution with `dryRun: true`.
- A direct user request to run a workflow for a real outcome authorizes one non-dry run with `dryRun: false`. Any other non-dry run requires explicit authorization for that specific run. Ask when a one-off request does not clearly indicate dry-run, development/testing, or real-outcome intent.
- Before the first run in an autonomous loop, establish a concrete maximum run count. If the request supplies no run count, ask for one. Count each `run_workflow` or `rerun_workflow_run_from_step` call that may have created a run, including successful or ambiguous calls. Input-validation rejections create no run, so do not count them.
- Announce the dry-run mode and run count once, then continue within the bound without per-run confirmation.
- If dry-run execution cannot validate the goal, explain why and request authorization for a specific non-dry run.
- For a dry run, verify `summary.dryRun` in the `run_workflow` response is true and `dryRun` in the `get_workflow_run` read-back is true; stop if either value is false or absent.
- Dry runs execute reads and persist run state, artifacts, output records, and completion post-processing. Annotation-gated tool calls and user-facing notifications are suppressed. An unannotated write tool can execute normally, so dry-run mode is not a blanket side-effect boundary.

## Process

1. **Confirm the workflow.** Use `list_workflows` to find it and `get_workflow` to fetch its `inputSchema`, `inputUiSchema`, `outputConfig`, and `accessHints`. If a field's purpose is not obvious from its schema and description, `get_workflow`'s `overview` or `steps` can supply context but cannot replace the declared contract. Treat access hints as separate signals. `accessHints.canExecute: false` is decisive, so do not call `run_workflow`. When `canExecute` is absent or null, run creation remains the permission gate. `isExecutable` reports deprecation state, not final manual-run permission: `false` means the workflow is deprecated and cannot run. Automatic dispatch also requires an organization workflow. To determine whether its automation is live, read `trigger.enabled`, or each schedule's `enabled` for a schedule trigger. Absent or `true` means enabled; only an explicit `false` pauses automation. A pause does not prevent a manual run.
2. **Resolve every input field.** Walk `inputSchema` field by field. The declared JSON type decides the raw value shape, and resource selectors require ObjectID values before `run_workflow` accepts them. Honor every declared constraint, including `enum`, `pattern`, `format`, numeric or length bounds, nested `properties`, and `items`. `effectiveInputSchema` reports each field's `presence`: supply every `required` entry and omit an `optional` one when the user has no value. Presence and defaults are independent. Omit a defaulted field when the user wants the default; the server fills absent keys before validation and does not replace a submitted value. An empty string, `null`, or an empty array does not satisfy a required field. `false`, `0`, and `{}` satisfy presence but can still fail another declared constraint. See `references/input-resolution.md` for the authoring selectors, runtime types, resolution steps, defaults, and ambiguity rule.
3. **Run.** Apply Run Mode, then call `run_workflow` with the resolved `input` object and chosen `dryRun` value, plus the optional `visibility` override (`public` or `private`) when the user wants this run's readability to differ from the workflow's default; see the `workflow-building` skill's `references/permissions-and-run-policy.md` for what run visibility governs. Report the run ID and that the run is asynchronous unless the returned status is already terminal. If input validation fails, repair against the returned `effectiveInputSchema`, which carries every input with its `source` and `presence`, including trigger keys and manual-run stand-ins the stored `inputSchema` knows nothing about; the `inputSchema`/`inputUiSchema` that ride along beside it are the stored shapes. Correct the field the structured error names and retry. Do not treat policy, not-found, rate-limit, or server errors as input-validation retries.
4. **Monitor and review.** The mutation response carries `feedback.pollAfterSeconds`, `feedback.nextActions`, and the stop condition for polling. Wait for the requested interval, call `get_workflow_run`, and evaluate the returned status against that stop condition. Poll responses do not carry another `feedback` object. In a dry-run loop, `AWAITING_APPROVAL` is intermediate: inspect the active step with `get_workflow_run_step` `view: "hitl"`, collect the evidence needed, then approve or reject it yourself according to the test case and continue polling. Do not return control merely because the run reached HITL, is still running, or needs another definition edit and rerun. Treat the rendered HITL as a user-facing acceptance surface: raw IDs, object strings, unreadable dates or money, excessive unchanged fields, misleading summaries, or unclear approve/reject choices fail the test. Fix the definition, start another dry run, and repeat until the stated acceptance criteria pass. Use the server's requested poll interval and a bounded wait loop; do not wait for another user prompt between ordinary run states. For a live run, require explicit user direction before `review_workflow_hitl_step`. Its mutation response supplies the next polling guidance, and another approval pause can follow.
5. **Report the outcome.** A dry-run test case is complete only when its asserted behavior has been inspected and every downstream dry-run step needed by that assertion has finished. Reaching HITL alone is completion only when HITL rendering is the stated test endpoint. Report the run mode and any dry-run limitations with status, run ID, `errorReason`, diagnostic error evidence, artifacts, output files, output sections, and supporting citations that matter to the request. For `HALTED`, report `haltReason` and explain that an executing step requested a clean stop through `halt_workflow`; later steps do not run, and the normal success output and notification path is skipped. A completed run can contain a degraded HTML output section: read `outputs.sections[].type` and inspect `outputs.sections[].error` when HTML validation cleared the content. For failed-step diagnosis, iterator drill-down, or definition drift, hand off to the `workflow-debugging` skill instead of diagnosing it here.

## Executing A Test Matrix

When given a structured test matrix (a set of scenarios, each with resolved inputs and expected outcomes), execute each scenario as a dry run in sequence. For each scenario:

1. Resolve the inputs per the scenario specification. Follow the input resolution rules in the Process section above.
2. Start a dry run with `dryRun: true`. Verify `summary.dryRun` in the response.
3. Monitor through completion, resolving HITL steps per the scenario's expected outcome (approve, reject, or edit). In a dry-run loop, own HITL resolution without user confirmation.
4. Record the run ID, terminal status, and any errors.
5. If the scenario has assertions (e.g., "output section X contains company name"), evaluate them against the run evidence from `get_workflow_run`.

After all scenarios complete, report a per-scenario pass/fail summary. Do not stop at the first failure -- run every scenario unless the user says otherwise.

If a dry run fails to start, repair against `effectiveInputSchema` and retry once. If it still fails, mark the scenario as "blocked" and move to the next one.

If a dry run hangs, apply the standard polling rules. On timeout, mark the scenario as "timeout" and move to the next one. Do not cancel the run.

## Core Rules

- A field's declared `type` in `inputSchema`, never its name or description, decides its runtime JSON shape. Resource selectors require ObjectIDs. Passing an ObjectID into a plain `string` field is as wrong as passing a literal name into a `company` field.
- Never guess or submit a best-effort ID for an ambiguous, zero-match, or unresolvable resource input. Ask the user. See the shared rule in `references/input-resolution.md`.
- Treat `folder` and `workspace` inputs as blocked when no ID is already in hand; no workflow tool browses or searches either type. Ask the user for the ID directly rather than inventing a workaround.
- Apply Run Mode to every new run and rerun.
- Apply every constraint present on the field's JSON Schema. Do not invent a constraint that the schema omits or infer one from the field name or description. Ask the user when the intended value remains ambiguous after reading the declared schema and workflow context.

## Lifecycle Actions Outside These Tools

The Metal app and workflow run API support actions this MCP does not expose:

- Retry a failed run.
- Rerun a completed, canceled, rejected, or halted run from the beginning.
- Cancel a nonterminal run.

Rerunning a terminal run *from a selected step* is the exception: `rerun_workflow_run_from_step` does expose that, and it is described above.

Route these actions to the Metal app. Do not imply that `run_workflow` or `review_workflow_hitl_step` can perform them, and do not invent MCP calls for them.

## References

- `references/input-resolution.md`: authoring selectors, runtime JSON types, resource resolution steps, and the shared ambiguity rule.
