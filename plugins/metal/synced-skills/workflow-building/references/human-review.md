# Workflow Human Review

Use this reference when a workflow includes a human approval step: editable review, review payloads, the approved-payload contract, or post-approval writes. This file owns the provider-neutral contract; provider-specific tool names and editability rules live in the `domains/` packs.

## Editable Review Meaning

Editable review is selection-based review with optional inline edits for review items that declare an editable capability. Reviewers select or unselect review items, and editable items can also receive reviewer-provided values.

Two review shapes exist:

- Whole-operation review: one review item per provider operation. Reviewers select or drop entire operations.
- Field-level review: each writable field on a create or update operation becomes its own review item, grouped under its parent operation. Reviewers select or drop individual fields; a locked field stays non-toggleable while any sibling field in the same operation group is selected.

Both shapes flow through the same path. The UI renders the shape it finds in `humanInLoopState.items`.

## The Prepare-Review To Write Pattern

Field-level editable review is the right default for CRM writeback. The mistake it prevents: an agent step that emits a whole-operation `reviewPayloadInput` with one item per create or update, so reviewers can only accept or reject the whole operation and cannot inline-fix a wrong picklist, a typo'd number, or a mis-resolved reference. Routing through a provider prepare-review tool is what makes individual fields editable.

Three-step wiring, provider-neutral:

1. Agent build step: produce the authoritative provider operations, then call the provider's prepare-review tool and return that tool's output as the `operations` array. Do not hand-write field fragments, and do not return a whole-operation envelope when the provider supports field-level review. Validate operations against the write contract first when the provider has a validate tool.
2. Human review step: `reviewPayloadInput` is the prepare tool's output. The UI renders one editable row per writable field. Editable fields accept inline reviewer values; locked fields stay non-toggleable.
3. Post or write step: feed `humanInLoopState.approvedPayload` to the provider's collapse-aware write tool. It collapses selected field fragments back into a normal provider operation, preferring each field's `value.review.editedValue` over the agent's value; the agent's original value is preserved for audit.

The exact prepare-review, validate, and write tool names, and a provider's editability rules, live in that provider's pack under `domains/`. When a provider has no prepare-review tool, fall back to whole-operation review.

## Payload Contract

The review payload (`reviewPayloadInput`) renders to a top-level object with an `operations` array. Each operation carries durable `value` data and reviewer-facing `display` context:

```json
{
  "operations": [
    {
      "id": "op1",
      "value": { "referenceId": "op1", "action": "create", "objectType": "Account", "fields": { "Name": "Example Corp" } },
      "display": { "title": "Create Account: Example Corp", "facts": [ { "label": "Action", "value": "Create" } ] }
    }
  ]
}
```

- `id` is stable and unique within the payload.
- `value` is the durable provider-operation value (or generic object) that approval preserves.
- `display` is reviewer-facing context only. `display.facts` is an array of rows, not an object keyed by label; every row needs a non-empty `label` and `value` (use `"-"` for an absent optional value, or omit the row).

For field-level review, each writable field becomes its own review item but still carries a provider-operation fragment in `value`, plus grouping metadata under `value.review`: `operationGroupId` (the parent operation's `referenceId`, unique in the batch), `granularity` and `fieldKey` (identify the field fragment), and `locked`. A fragment is not independently provider-valid until selected fragments collapse back into an operation at write time.

For generic, non-provider review, let structured upstream output be the source of truth and project each object into `operations[*]`; the upstream step normalizes business data and reviewer evidence into a stable object array.

## Review Items And Approval Submission

The runtime materializes `humanInLoopState.items` from the payload, one review item per `operations` entry. `len(operations)` must equal `len(items)`, or approval fails with "review items do not match resolved payload operations." A review item carries:

- `reviewItemId` (auto-assigned `item-<sourceIndex>`), `sourceIndex` (index into `operations`), `title`, `facts`, `groupLabel`.
- `operationGroupId`, `reviewGranularity`, `fieldKey`, and `locked` for field-level rows.
- `editable`: `{type, options, currentValue}` when the field is inline-editable.

The approval submission is `{approvedReviewItemIds: [...], fieldEdits: [{reviewItemId, value}]}`.

## Editable Field Types

Editability is decided by the provider's prepare-review adapter from describe metadata; a builder does not set it. A field is inline-editable only when its reviewer-visible value uniquely determines the raw provider value. There are five editable types, each with a strict value shape the submission must match:

- `text`: a string.
- `number`: a JSON number.
- `date`: an RFC3339 timestamp or a `YYYY-MM-DD` string.
- `boolean`: a JSON boolean.
- `picklist`: a string equal to one of `editable.options[].value`.

An approved edit writes the new value to the operation's `value.review.editedValue` and also re-seeds `items[].editable.currentValue`, so a reload shows the edited value rather than reverting to the agent's proposal.

## Approved Payload

`humanInLoopState.approvedPayload` is derived after approval, not a stored field: the runtime copies `payload` and replaces `operations` with the subset whose review items were approved, matched by each item's `sourceIndex`.

- Downstream writes consume `humanInLoopState.approvedPayload`, not the reviewer-facing message.
- For whole-operation review, `approvedPayload.operations` is the subset of approved operations.
- For field-level review, it contains only selected field fragments and omits any operation group with no approved field rows. Reviewer edits appear on those fragments as `value.review.editedValue`.
- Full review state stays in `humanInLoopState.items` and `approvedReviewItemIds` for the UI and audit.

## Approval Validation And Errors

Review submission is validated against the generated review state:

- Selected review item IDs must exist and must not duplicate; an edit targeting an unselected item is rejected ("fieldEdits references unselected review item id ...").
- Field-level review enforces locked-row selection within each operation group: a locked row in a group with any approved sibling must itself be approved, or the submission is rejected ("approvedReviewItemIds omits locked review item id ..."). A group with zero approved rows is dropped entirely, including its locked rows.
- Optional inline edits must target selected editable items and match the editable value shape above.
- Selected field fragments collapse into provider write operations after validation.

`locked` is a review-selection policy, not an authorization contract. Writers should not gate on `locked` rows; that is the review step's responsibility. A reviewer edit the provider ultimately rejects surfaces as a provider 4xx at write time.

## Review Message Shape

The approval message summarizes the batch, explains held-back items when they exist, and points the reviewer to the editable operations. It should not restate every operation or recreate the payload as markdown tables when the UI renders per-operation or per-field facts. Treat held-back items as reviewer context, not operations.

## Automatic Reviewer Assignment

A human approval step has no statically configured reviewer field on the building surface. The `humanInLoop.resolver` config (shown in the builder as "Assign reviewer automatically") runs a built-in reviewer-resolver agent before the pause to choose the approver. The agent is fixed; only its instruction is builder-configured. Build it through `add_workflow_step` or `update_workflow_step` as `humanInLoop.resolver` with an `input` instruction string.

Review authorization follows the assignment state:

- A plain HITL step without a resolver allows an authenticated actor who otherwise has permission to review the active run.
- A successful resolver assignment restricts review to the assigned active Metal user.
- A missing, failed, or stale resolver assignment allows an org admin or org owner to review. Metal Team does not receive this fallback.
- Resolver failure logs a warning and leaves the workflow paused without an assigned reviewer; it does not fail the workflow.

Approval notifications use a separate rule. An assigned active Metal user receives the notification. When the step has no assignment object, the run triggerer receives it if the triggerer is a user. A stale assignment has an assignment object but no valid notification recipient, so nobody receives the notification even though an org admin or owner can review.

Building documents this configuration and its safety semantics. Review actions and monitoring on a paused run belong to the `running-workflows` skill; run diagnosis stays read-only in `workflow-debugging`.
