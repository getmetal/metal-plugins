# Workflow Output Sections

Use this reference when building output sections, output templates, final run output, citations, or completion notification conditions.

## Output Schema Rendering

Workflow output schema is a JSON Schema object with top-level properties for run output sections. Fields can use `x-template` to pull step results into the final output. `x-template` values use the same Go template syntax as prompts and tool inputs.

Common `x-template` forms:

- Text output: `{{ (index .Steps "step-id").text }}`
- Structured field: `{{ (index .Steps "step-id").results.structured.fieldName }}`
- Citations JSON: `{{ toJSON (index .Steps "step-id").citations }}`
- Iterator summary: range over raw iterator `items` when structured child output, citations, status, error, index, or original input matters. Child structured output is under `stepOutputs[childStepId].results.structured`, for example `{{ toJSON (index (index $item.stepOutputs "child-step-id").results "structured") }}` inside a `range`.

The rendered template string is coerced to the declared JSON type. The schema root must render to an object, and a missing required output property fails the run during finalization; a schema render failure also fails the run. Run output defaults to `{"status":"completed"}` when there is no output schema, or when the schema produces nothing because every `x-template` field resolves empty.

## Section Display Rules

- Each section key must match a top-level property in the output schema.
- A configured title renders as the section header. An omitted title leaves a configured section untitled.
- Section `type` is `text` or `html`; an omitted type defaults to `text`.
- No sections means no in-app output section display.
- If run output contains top-level keys not listed in sections, the frontend appends them after configured sections with auto-formatted titles.

### HTML Sections

An HTML section consumes a self-contained HTML or SVG fragment. Instruct the emitting step to follow the authoring validator's contract:

- Omit document shells such as `doctype`, `html`, `head`, `body`, and `meta`, and omit `iframe`, `object`, `embed`, `form`, and `base` tags.
- Do not use `fetch`, `XMLHttpRequest`, `WebSocket`, `EventSource`, or browser storage (`localStorage`, `sessionStorage`, `indexedDB`).
- Do not reference `window.parent`, `window.top`, or `parent.`/`top.` members (`postMessage`, `location`, `frames`, `opener`, `document`, `window`). The capability checks are textual pattern matches, so these tokens trip validation even inside strings or comments.
- Do not emit the literal `</approved_template>` closing tag; it is a reserved resolver sentinel.
- Load remote resources only from the approved https-only CDN prefixes under `https://cdn.jsdelivr.net/npm/`: `chart.js`, `gridjs/`, `mermaid/`, `d3@7`, `topojson-client@3`, and `world-atlas@`. The check covers script `src`, link `href`, `src`/`srcset`/`href`/`xlink:href` attributes, and CSS `@import`/`url()`; http and protocol-relative URLs are rejected.
- Keep the fragment under 2,000,000 bytes.

Finalization extracts a surrounding Markdown code fence or document shell before validation. The validator provides best-effort authoring feedback; the frontend sandboxed iframe and CSP enforce isolation. When validation fails, finalization clears that section's output and records the validation message in its `error`; the run still completes.

The run projection normalizes each `outputs.sections[].type` to `text` or `html`. It preserves configured titles, including an empty title; it generates a title only for a section synthesized from an unconfigured output key or output-schema property. Inspect `outputs.sections[].error` when a completed run contains an empty or degraded HTML section.

## Output Templates

The advanced output template path is useful when output needs structured fields, custom markdown, `toJSON`, iterator ranges, or non-default step references.

`Include citations` adds a citations field only when checked. If citations are needed in a custom output template, render them explicitly with `{{ toJSON (index .Steps "step-id").citations }}`. The run projection decodes citation arrays stored through JSON or BSON and assigns the configured citation source step to each projected citation.

## Finalization

- At finalization the run separates `Documents` (from generateDocument steps) from `Artifacts`, dedupes both by `bucket:key`, and drops empty references.
- Execute-code files become user-visible run files only when a declared `outputFiles` entry has `createOutput: true`; those IDs are collected from step `results.outputIds`.
- Token `usage` is appended to the final output as a top-level key only when the output schema declares `usage` or allows additional properties; otherwise it is stripped.

## Completion Notifications

Email completion notification conditions are Go templates that must render to a boolean. Prefer a structured completion step as the notification gate:

```text
{{ (index .Steps "notification-gate").results.structured.shouldNotify }}
```

If the condition renders `false`, the workflow run still completes and persists output, but the completion notification is skipped. Render or parse errors also skip the notification. The condition parses with `strconv.ParseBool`, so `true`, `false`, `1`, `0`, `t`, and `f` all work, and an empty or unset condition defaults to sending. A completion notification needs a user `triggeredBy` as its recipient; a run with no user trigger does not send one.

## Template Contracts

- Match each section key to a top-level schema property.
- `index .Steps` is the stable step-reference form because step IDs often contain hyphens.
- `toJSON` preserves citations and structured data embedded into output templates.
- Raw iterator `items` preserve structured child output, citations, status, error, index, and original item data. Read child structured output at `stepOutputs[childStepId].results.structured`; `iteratorResults` does not preserve it.
- Output sections alone do not create durable file outputs. Agent-generated user-visible files need `sandbox_download` and `create_output`; execute-code user-visible files need declared `outputFiles` with `createOutput: true`.
