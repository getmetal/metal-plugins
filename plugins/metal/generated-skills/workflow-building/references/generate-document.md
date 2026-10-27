# Generate Document Workflows

Use this reference when a Metal workflow has a `generateDocument` step or when a user asks whether a DOCX/XLSX/PPTX template-backed output can change.

## Runtime Contract

- A `generateDocument` step renders `generateDocument.inputData` as a Go template, parses the result as JSON, fetches the referenced work product template, and calls the work product render API.
- `generateDocument` is render-only. It does not gather source data, resolve file IDs, or enrich missing fields.
- When the work product template's `outputFormat` is `xlsx` and it has an `originalS3Key`, the executor passes the uploaded workbook to the renderer, so the script fills that workbook rather than building one from scratch. DOCX and PPTX are built from the script.
- The raw stored runtime type permits an absent `generateDocument.outputFilename`, but the building tools require `templateId`, `inputData`, and `outputFilename` when creating a Generate Document step or changing another step to that type. `outputFilename` is a Go template for the generated filename.
- A same-type update can omit `outputFilename` to preserve a non-empty saved value. If the saved value is empty, the merged update fails the required-field check until the caller supplies it.
- The standard work product handoff is `{{ toJSON (index (index .Steps "<agentStepId>") "templateInputData") }}`.
- `templateInputData` appears when a work product tool stores data under `work_product_data_<templateId>` and the workflow runner promotes it into step results.
- Large `templateInputData` can be offloaded as `templateInputDataS3Ref`; the runner hydrates it back into template context before rendering `generateDocument.inputData`.
- Step output includes `results.filename`, `results.s3Key`, and `results.outputId` when Output record creation succeeds. The rendered document is stored as a workflow artifact and run document.
- If the upstream step completes without the expected render input, the rendered `inputData` fails to decode and the step fails with `failed to parse generateDocument inputData as JSON`, or, when it decodes but does not match the template, with an input-schema validation error from the render API. The similar-sounding `inputData is required for generateDocument steps and cannot be cleared` is an authoring rejection on a same-type update, never a run error.

## Data Handoff Patterns

Existing patterns for `generateDocument.inputData`:

- Work product handoff: point at `(index .Steps "<agentStepId>").templateInputData` when the upstream agent uses work product tools such as `template_extract_data`, `template_assemble_data`, or `template_prepare_inputs`.
- Structured-output handoff: point at `(index .Steps "<stepId>").results.structured` when a prior agent, completion, or executeCode step has an `OutputSchema` and emits the complete object expected by the template.

The structured-output path is useful when the producing step can create the full render input without work product tools. The object must already match the work product template schema.

## Template Schema And Script

- Treat the work product template `inputSchema` as a strict data contract. If `additionalProperties` is false, new keys require a schema update.
- A visual or layout change may require a Python render script change even when the workflow definition stays unchanged.
- A data shape change usually requires both schema and script updates, plus data-gathering instructions that populate the new field.
- `docx_automation_update_script` is unavailable on this MCP surface and cannot run as a workflow Tool step. Change that stored DOCX template through its owning interface or ask Metal for help; do not add it to a workflow definition.

## File And Image Inputs

- Helloween, the work product renderer, builds DOCX, PPTX, and XLSX. The script context provides `docx`, `pptx`, and `xlsx` helpers plus `json`, `datetime`, `re`, `copy`, `io`, and `download_image(url)` for public HTTP(S) image URLs.
- Template scripts may only import from `docx`, `pptx`, `openpyxl`, `pathlib`, `ast`, and `_strptime`; any other import raises `ImportError`. `io` and `download_image` are pre-bound names, not imports. `bytes` and `bytearray` are allowed builtins, so JSON-provided bytes can be passed to `bytes(...)`, while `getattr` and `type` are excluded. `base64` is not importable; prefer a URL field, a renderer-supported download shape, or `bytes(...)`.

## Stable Spreadsheets Without A Template

When no work product template exists and the workbook layout is structurally stable, prefer an agent step with a deterministic `openpyxl` script over a fragile template-file upload.

- Inspect the example workbook before building the prompt: sheet names, used ranges, merged cells, comments, formulas, column widths, row heights, styles, and fillable cells.
- Hardcode the workbook layout, styles, merges, number formats, and output filename logic in the script. The agent injects only prior-step structured data into the known cells.
- Use this script-backed approach when exact layout and downstream parseability matter. Use a template-backed `generateDocument` step when a work product template exists, or an uploaded example file when the layout changes often enough that recreating it in code is more fragile than filling an existing file.
