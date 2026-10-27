# Salesforce Batch Patterns

Load this only when the workflow targets Salesforce: a Salesforce import, batch write, or editable approval flow over Salesforce operations. The generic editable-review and approval-handoff contract is in `../human-review.md`; this pack covers only Salesforce specifics. If the `salesforce-api-docs` skill is available, use it for API guidance. Otherwise rely on the current tool descriptions and input schemas plus `salesforce_list_objects` and `salesforce_describe_object`; never guess field names, IDs, choices, or payload shapes.

## Salesforce Tools

- `salesforce_prepare_review_payload`: projects provider operations into field-level review items.
- `salesforce_validate_operations`: validates operations against the write contract and returns a repair suggestion. Validate, repair, and re-validate before review.
- `salesforce_entity_write`: the collapse-aware writer. It collapses approved field fragments back into operations, preferring each field's `value.review.editedValue`. With `dryRun: true`, it returns the Salesforce Composite Graph request for `transactional` mode or the standard Composite request for `best_effort`, without calling Salesforce.
- `salesforce_upload_document`: attaches a file to a record's Files related list. This is the only way to put a file on a Salesforce record; see "Attaching Files" below.

## Safe Write Planning

Separate these concerns when the workflow is complex:

- Contact and account resolution.
- Duplicate detection.
- Structured safe operation normalization in a completion step, validated with `salesforce_validate_operations`.
- Review-payload enrichment through `salesforce_prepare_review_payload` when field-level review is supported.
- Reviewer summary generation.
- Posting the approved payload through `salesforce_entity_write`.

## Duplicate Detection

For create-vs-update decisions, account-scoped matching is often insufficient on its own.

Common safe pattern:

1. Resolve the target account.
2. Validate the batch with `salesforce_validate_operations`, which runs the org's active duplicate rules against every prospective create.
3. Resolve each `potential_duplicate` warning before submitting: reuse the matched record's ID when it is the same entity, hold the create back and say so in the summary when it is ambiguous, or surface the collision to the reviewer when the create is intentional.
4. Hold plausible duplicates for review instead of emitting the create.

Duplicate findings never set `valid: false`, so a batch carrying unresolved duplicates still validates, and an unresolved duplicate create fails at write time with `DUPLICATES_DETECTED`. A `duplicate_preflight_unavailable` warning means the rules could not be evaluated on that run, so the batch carries no duplicate signal at all. There is no `NOT_FOUND` duplicate result and no separate cross-account preflight call.

## Account Resolution

Prefer grounded fuzzy account matching over exact contiguous phrase matching. Useful tactics include token-based patterns, punctuation-insensitive matching, corporate suffix variation, and explicit alias mappings for recurring firm names.

## Attaching Files

A file body cannot travel through `salesforce_entity_write`. Its `fields` payload is model-emitted JSON, so putting a document on a record means `salesforce_upload_document`, not a `ContentVersion` operation in the writer.

Call it with `parent_record_id` plus exactly one source:

- `data_entity_id` for a platform file, such as the CIM or Teaser that arrived by email (typically `input.attachments[i]`).
- `artifact_id` for a file generated in this run, such as a PDF rendered by `executeCode` or fetched with `sandbox_download`. No intermediate save into the platform file tree is needed.

The record's `ContentDocumentLink` is created in the same call, so no linking step follows. Optional `filename` defaults to the source file's stored name, which is what carries the extension Salesforce reads the file type from. Optional `title` defaults to the source file's display name, so a platform file called "Q4 2025 CIM" stored as `q4-2025-cim.pdf` shows that title against a correctly typed `.pdf` download.

Deduplication is by title against the files already attached to that record. A re-run with an unchanged title returns the existing `contentDocumentId` with `alreadyExisted: true` and uploads nothing, which is what makes the step safe to retry. Two consequences for step design:

- To attach a genuinely new version of a same-named document, put a discriminator in the title, for example `Project_Falcon_Scorecard_2026-07-27.pdf`.
- The match is case-sensitive, so titles that differ only in case are treated as different files.

Step output carries `contentVersionId`, `contentDocumentId`, `alreadyExisted`, `title`, and `fileName`, which is enough for a downstream render step to report what landed. A fresh upload also carries `sizeBytes` and `contentType`; an `alreadyExisted` result omits both, because the tool did not read the file it matched and the source file's size would not describe the attachment on the record. On a wrong or file-incapable `parent_record_id` the step fails with an input error naming the id.

## Salesforce Editability

The prepare-review adapter decides editability from describe metadata. Beyond the generic editable types, Salesforce excludes from inline editing: `multipicklist` (multi-select) and `reference` fields, `id` and `address` fields, `base64`, and the types whose reviewer-visible value does not determine the raw one, including `anyType`, `location`, `encryptedstring`, `autonumber`, `complexvalue`, `combobox`, and `time`. A `picklist` is also excluded when describe reports no options or the proposed value is not one of them, and a string-family field (`string`, `url`, `email`, `phone`, `textarea`) when the proposed value is not a string.

## Reviewer Context And Failure Paths

If items are held back, exclude them from the operations payload, name them in the reviewer message with the reason, and include any grounded possible match. If the reviewed payload is invalid or empty because validation failed, signal that clearly rather than approving and posting an empty batch.

## Dry Run

For preflight or testing, call `salesforce_entity_write` with boolean `dryRun: true`. It parses and collapses the operation envelopes, validates the operation payload, and returns the planned Composite request without sending it. Omit `dryRun` or set it to `false` only for the approved live write.
