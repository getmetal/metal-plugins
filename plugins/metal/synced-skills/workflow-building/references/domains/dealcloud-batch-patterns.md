# DealCloud Batch Patterns

Load this only when the workflow targets DealCloud: a DealCloud import, batch write, or editable approval flow over DealCloud operations. The generic editable-review and approval-handoff contract is in `../human-review.md`; this pack covers only DealCloud specifics. If the `dealcloud-api-docs` skill is available, use it for API guidance. Otherwise rely on the current tool descriptions and input schemas plus `dealcloud_get_entry_types`, `dealcloud_get_entry_type_fields`, and `dealcloud_get_choice_field_values`; never guess field names, IDs, choices, or payload shapes.

## DealCloud Tools

- `dealcloud_prepare_review_payload`: projects provider operations into field-level review items.
- `dealcloud_validate_operations`: validates operations against the write contract before review.
- `dealcloud_entity_write_v_2`: the collapse-aware writer. It collapses approved field fragments back into operations, preferring each field's `value.review.editedValue`. In a run-level dry run (`dryRun: true` on the workflow run), the gate suppresses the write and returns dependency-tiered DealCloud Rows API payloads in `requests` instead, without calling DealCloud.

## Wiring

Follow the prepare-review to write pattern in `../human-review.md`: build operations, validate with `dealcloud_validate_operations`, project through `dealcloud_prepare_review_payload`, route the output through the human review step, and post `humanInLoopState.approvedPayload` to `dealcloud_entity_write_v_2`.

## DealCloud Editability And Review Scope

The prepare-review adapter decides editability from field metadata. Proposed-field review is the default. Set `reviewScope` to `allEditable` to add other supported writable fields. The tool reads current update values. Untouched supplemental fields never write, including fields with non-null current values.

DealCloud specifics:

- Single-select Choice fields use picklists whose option values are numeric Choice IDs.
- Multi-select Choice fields use `multiSelect` controls.
- Fields sharing a Choice set, such as cascading Deal Status and Deal Stage, stay read-only.
- Reference fields use `referenceList` only when the caller supplies 1 to 100 grounded `referenceOptions`. The UI does not search DealCloud.
- A proposed Text or Date field stays read-only when its value is not a string. A Choice value must normalize to a valid choice ID. A reference stays read-only when its value is malformed or carries an `@{ref.EntryId}` dependency.
- Text fields are inline-editable, markup included.
- User, EntryListID, Binary, Counter, and Image fields remain read-only.

## Dry Run

For preflight or testing, run the workflow in dry-run mode (`dryRun: true` on `run_workflow`). The run-level gate intercepts `dealcloud_entity_write_v_2`, which parses and collapses the operation envelopes, validates cross-references, orders dependency tiers, and returns the planned Rows API requests without sending them. There is no per-call dryRun input; the run flag is the only mechanism.
