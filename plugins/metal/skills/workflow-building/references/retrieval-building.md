# Workflow Retrieval Building

Use this reference when building workflows that retrieve source-backed data, prepare draft data for structuring, inspect files, or extract KPI, financial, tracker, or other metric payloads.

## Retrieval Handoff

For tool-heavy retrieval that must become structured data, declare an `outputSchema` on the retrieval agent step; the schema is enforced at run time and the validated payload lands at `results.structured`. `structured-output.md` covers the schema rules and enforcement contract.

The retrieval agent should gather source-backed facts, inspect files with tools, record coverage and limitations, and fill the schema only with source-backed values.

## Retrieval Prompt Shape

Source retrieval prompts should separate these responsibilities:

- Discovery: enumerate and search candidate files, folders, entities, and nearby source categories.
- Shortlist: choose likely exact-period files, budget/model files, source exports, and comparison sources before extraction.
- Inspection: read or upload every shortlisted source with the required tool for its file type.
- Extraction: record only source-backed values, source periods, units, calculations, and caveats.
- Absence proof: do not mark a field missing until the relevant exact-period source category and comparison or budget source category have been checked when present.
- Final output: return draft JSON or structured text with source file coverage, not just extracted values.

When the prompt interpolates an id or a name from inputs or prior steps, state the resource type around it ("the Company with id `{{ .Input.company.id }}`"); see `template-syntax.md`.

Search snippets are discovery evidence only. They are not enough to prove exact values, prove absence, or support `found: true` values when the underlying file can be read or uploaded.

## Retrieval Tool Rules

Prompts commonly need explicit tool rules when the source corpus contains documents or files:

- For every shortlisted `.xlsx`, `.xls`, or `.csv`, require `sandbox_upload_data_entity` followed by `sandbox_exec`. Search excerpts are never sufficient for a spreadsheet when the file can be parsed.
- Shortlist spreadsheet files when file names, folder paths, metadata, or search excerpts indicate they could contain exact-period actuals, budget, quota, forecast, target, prior-year, variance, CRM, pipeline, operating, board analysis, or financial model data.
- For every shortlisted PDF or deck that supports a `found: true` value, require `get_document` around the relevant section. If `get_document` is unavailable, incomplete, or does not expose the needed section, require `sandbox_upload_data_entity` plus `sandbox_exec` with a suitable extraction tool.
- If a required upload, document read, or parse fails, record the failure in source coverage and do not use that source for `found: true` values.

The tool names above are agent-native tools, not Tool-step tools. `sandbox_upload_data_entity`, `sandbox_exec`, and `get_document` are all private, and kind `tools` lists only public tools eligible for a direct Tool step, so none of the three ever appears in that catalog and its absence says nothing. Confirm them against the agent's own toolbelt in `agents.md` instead, and reserve kind `tools` for tools a Tool step will execute.

When useful, ask the retrieval step to use an `inspectionMethod` field such as `enumerated_only`, `search_excerpt_only`, `get_document`, `sandbox_parsed`, `get_document_and_sandbox`, `upload_failed`, `parse_failed`, or `get_document_failed`. Downstream structuring steps can then gate values by source inspection quality.

## Period And Entity Gates

When explicit workflow inputs identify the selected entity, period, or run scope, prompts must treat those inputs as authoritative. Do not infer those values from a template file name, source file name, board deck title, upload name, or "most recent available" file.

Nearby-period, quarter-to-date, year-to-date, forecast, snapshot, or proxy data can be useful context. Keep it in notes, summary, or source coverage unless the source explicitly defines it as the requested field for the requested period.

## Structured Metric Outputs

For KPI, metric, financial, or tracker-style outputs, keep numeric values parseable:

- Put the raw numeric value in `value`.
- Put the unit in `unit`.
- Put the basis in `valueType`, such as `actual`, `budget`, `calculated`, `source_reported`, or `not_found`.
- Put the source period in `sourcePeriod`.
- Put explanations, caveats, and rejected proxy values in `notes`.

Do not put dollar signs, commas, percent signs, scale suffixes, formulas, source periods, or prose in numeric value fields. Use a consistent missing-value sentinel such as `not_found` or the exact wording the user requested.

Compact `sourceFiles` coverage usually includes file name, data entity ID, file type, period covered, relevance, inspection method, and key findings.

## Structuring Rules

The retrieval prompt should require the structured payload to:

- Carry only source-backed facts.
- Reject values from weak source coverage such as `search_excerpt_only`, `enumerated_only`, failed uploads, failed parses, or failed document reads.
- Respect the entity and period gate from workflow inputs.
- Fill all metric slots, including missing values with the agreed sentinel.
- Preserve source coverage and retrieval limitations in a summary when the schema provides one.

Use `{{ (index .Steps "<retrievalStepId>").text }}` for retrieval text. Use `{{ toJSON (index .Steps "<stepId>").results.structured }}` when embedding structured JSON into later prompts.
