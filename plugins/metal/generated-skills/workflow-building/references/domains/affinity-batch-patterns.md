# Affinity Batch Patterns

Load this only when the workflow targets Affinity: an Affinity import, batch write, or editable approval flow over Affinity operations. The generic editable-review and approval-handoff contract is in `../human-review.md`; this pack covers only Affinity specifics. If the `affinity-api-docs` skill is available, use it for API guidance. Otherwise rely on the current tool descriptions and input schemas plus `affinity_get_fields`; fetch both global and list-specific fields when applicable, and never guess field names, IDs, choices, or payload shapes.

## Affinity Tools

- `affinity_prepare_review_payload`: projects provider operations into field-level review items.
- `affinity_validate_operations`: validates operations against the write contract before review.
- `affinity_entity_write`: the collapse-aware writer. It collapses approved field fragments back into operations, preferring each field's `value.review.editedValue`. With `dryRun: true`, it returns the ordered Affinity v1 call sequence in `calls` without calling Affinity.

## Create-Only Writes

Affinity writes create records and nothing else. Both `affinity_prepare_review_payload` and `affinity_entity_write` reject any operation whose action is not `create` ("action must be 'create' (Affinity writes do not support updates)"), and `entityType` is limited to `organization`, `opportunity`, `person`, and `note`. There is no update path through these tools, so a workflow that needs to change an existing Affinity record needs a different surface.

## Wiring

Follow the prepare-review to write pattern in `../human-review.md`: build operations, validate with `affinity_validate_operations`, project through `affinity_prepare_review_payload`, route the output through the human review step, and post `humanInLoopState.approvedPayload` to `affinity_entity_write`. Editability is decided by the prepare-review adapter from live field metadata returned by `affinity_get_fields`. A field that allows multiple values is read-only before any per-type rule applies. Builtin operation keys are judged separately from list fields: `name`, `domain`, `content`, `first_name`, and `last_name` are text-editable when the proposed value is a string, and every other builtin key, `list_id` and ID arrays included, is read-only.

## Dry Run

For preflight or testing, call `affinity_entity_write` with boolean `dryRun: true`. It parses and collapses the operation envelopes, then returns the planned Affinity v1 calls without sending them. Omit `dryRun` or set it to `false` only for the approved live write.
