---
name: workflow-fixing
description: "Use when a Metal workflow run failed and the user wants the workflow fixed so it succeeds: diagnose the failure, make the smallest definition edit, and validate it with a dry run before any live run. For diagnosis without edits, use workflow-debugging."
---

# Metal Workflow Fixing

Before starting, read [Safety and confirmation](../../references/safety.md) and apply it throughout this task.

Use this skill when the user brings a failed run and wants the workflow fixed. The goal is a workflow definition that runs successfully, proven by a dry run before any live run.

This skill is a loop on top of three others. Read run evidence the way `workflow-debugging` says. Edit the definition the way `workflow-building` says: load it before the first edit and follow its Write Safety, Building process and Warnings Envelope sections. Start runs and reruns the way `running-workflows` says, including its Run Mode rules. For diagnosis without edits, use `workflow-debugging` alone.

## Evidence first

Before you change anything, read the run and the definition. Follow the `workflow-debugging` evidence ladder in its Evidence Gathering section:

1. `get_workflow_run` with `view: "failures"` to find the failed steps. Note the run's `dryRun` value.
2. `get_workflow_run_step` with `view: "errors"` for each failed step's full error.
3. `get_workflow` and `get_workflow_step` for the saved definition of each step you may touch.

State the root cause in one sentence before you write any edit. If several steps failed, analyze them together: one root cause can explain all of them, and one edit can fix them.

## The fix loop

1. **Diagnose.** State the root cause in one sentence.
2. **Fix.** Make the smallest definition change that addresses the root cause. You may add, update, move or delete steps, and change inputs, outputs and the trigger. Deleting a step is destructive and needs the user's explicit intent. Read the workflow with `get_workflow` and each touched step with `get_workflow_step` before you edit it.
3. **If the write is rejected for a field you didn't touch,** see the next section. Fix that field, then retry your edit. Don't stop at the first rejection.
4. **Validate with a dry run.** Choose a rerun or a new run as described in Rerun or new run, and set `dryRun: true`.
5. **If the dry run fails,** diagnose the new error, apply another fix and start another dry run. Show the user each result and ask whether to continue before the next attempt.
6. **If the dry run passes and the step that failed now succeeds,** tell the user what the dry run proved and what it left untested, as the `workflow-debugging` Dry-Run Evidence section describes. A dry run doesn't execute annotation-gated writes, so it can't confirm a fix that depends on a write executing or on its real response. Then ask whether the user wants a live run.
7. **After 3 failed fix attempts,** stop. Summarize what you tried and what still fails, and ask the user how to proceed.

## A rejection about a different field

Some checks run on the whole workflow, not on the field a write changes. `update_workflow_details`, `configure_workflow_input`, `configure_workflow_trigger`, `configure_workflow_output`, `add_workflow_step`, `update_workflow_step`, `delete_workflow_step` and `move_workflow_step` are each rejected when the workflow, as the write would leave it, has a blank name or a missing or invalid trigger. This holds even when the problem predates the write. A resubmitted write that changes nothing skips the check.

- A blank name is rejected on `name` with code `required`. Set a name with `update_workflow_details`.
- A missing or invalid trigger is rejected with a message about the trigger. Repair it with `configure_workflow_trigger`. The smallest valid trigger is `{"type": "manual"}`. If the workflow had an email, webhook, schedule or event trigger, ask the user before you change its type: switching away from email or webhook deletes the address or endpoint, and switching away from schedule deletes the schedules.
- Then retry your original edit.
- If the name is blank and the trigger is also missing or invalid, each repair write is rejected for the other problem. Tell the user that these tools can't repair this workflow.

Coherence findings work differently. A finding blocks a write only when it is error severity and the write introduced it. A finding that predates the write comes back in `warnings` with `introduced: false` and never blocks. See "Warning Severity And Blocking" in the `workflow-building` skill's `references/building-tools.md`.

## Rerun or new run

Both tools start a new run. Apply the `running-workflows` Run Mode rules to every call, and count each call against the run bound you set.

Use `rerun_workflow_run_from_step` with `dryRun: true` and the failed run's `workflowRunId` when all of these hold:

- Every top-level step before the target is `COMPLETED` in the failed run. Usually the target is the step that failed, or the earliest step your fix changed.
- The target is not a child of an iterator. To rerun inside an iterator, target the iterator step.
- Your edit didn't change any earlier step, its output shape or the target's step ID. Replacing a branch's arms gives the arm steps new IDs.

The rerun reuses the failed run's input and the outputs of the earlier steps, and runs the current definition from the target onward. A rerun of a dry run is always dry.

Otherwise, use `run_workflow` with `dryRun: true` and the failed run's original input. Read that input with `get_workflow_run` and `fieldPath: "input"`; `view: "overview"` also shows it.

## Live runs

- Never start a live run (`dryRun` false or omitted on `run_workflow`, or a rerun of a live run without `dryRun: true`) without the user's explicit approval for that run.
- A rerun can't turn a dry run into a live one. After you validated a fix on a dry run, the live check is a new `run_workflow` with `dryRun: false` and the original input.
- These tools can't retry the failed run itself. To run the whole workflow again, start a new `run_workflow` with the original input, or rerun from the first step.

## Scope

- Every definition surface is in scope: step prompts and configuration, inputs, outputs, the trigger, step order and step types.
- A step can't be set to or changed to `generateDocument`. See Retired Template Workflows in `workflow-building`.

## Voice

Describe problems and fixes in terms the user can see: step names, template expressions, input field names and output schemas. Don't describe platform internals. If you can't make progress, say what you tried and what still fails, then stop and let the user decide.

When the failure looks like a Metal platform issue rather than something the definition can fix, tell the user that, give the run ID, and suggest they report it to Metal support. Don't say "platform bug" or "escalate" without saying what the user can do.
