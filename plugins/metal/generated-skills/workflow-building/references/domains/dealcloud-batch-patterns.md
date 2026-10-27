# DealCloud Batch Patterns

Load this only when the workflow targets DealCloud: a DealCloud import, batch write, or editable approval flow over DealCloud operations. The generic editable-review and approval-handoff contract is in `../human-review.md`; this pack covers only DealCloud specifics. If the `dealcloud-api-docs` skill is available, use it for API guidance. Otherwise rely on the current tool descriptions and input schemas plus `dealcloud_get_entry_types`, `dealcloud_get_entry_type_fields`, and `dealcloud_get_choice_field_values`; never guess field names, IDs, choices, or payload shapes.

## DealCloud Tools

- `dealcloud_prepare_review_payload`: projects provider operations into field-level review items.
- `dealcloud_validate_operations`: validates operations against the write contract before review.
- `dealcloud_entity_write_v_2`: the collapse-aware writer. It collapses approved field fragments back into operations, preferring each field's `value.review.editedValue`. With `dryRun: true`, it returns dependency-tiered DealCloud Rows API payloads in `requests` without calling DealCloud.

## Wiring

Follow the prepare-review to write pattern in `../human-review.md`: build operations, validate with `dealcloud_validate_operations`, project through `dealcloud_prepare_review_payload`, route the output through the human review step, and post `humanInLoopState.approvedPayload` to `dealcloud_entity_write_v_2`.

## DealCloud Editability

The prepare-review adapter decides editability from field metadata. DealCloud specifics:

- Single-select choice fields are inline-editable as picklists whose option values are the numeric choice IDs. Fields sharing a choice set (cascading pairs such as Deal Status and Deal Stage) stay read-only, as do fields whose choice set the schema does not report.
- Any multi-select field is read-only whatever its type; that check runs before the per-type rules, so it also covers multi-select choice fields.
- Text fields are inline-editable, markup included. DealCloud has no separate HTML field type: markup lives in a text field, and only the reviewer-facing display value is tag-stripped and truncated, while the editable value carries the raw text.
- Reference, User, EntryListID, Binary, Counter, and Image fields are not inline-editable, because their raw values are entry references a reviewer cannot enumerate.

## Dry Run

For preflight or testing, call `dealcloud_entity_write_v_2` with boolean `dryRun: true`. It parses and collapses the operation envelopes, validates cross-references, orders dependency tiers, and returns the planned Rows API requests without sending them. Omit `dryRun` or set it to `false` only for the approved live write.
