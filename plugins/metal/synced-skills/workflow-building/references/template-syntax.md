# Workflow Template Syntax

Use this reference when building workflow prompt templates, tool inputs, iterator sources, output templates, or notification conditions.

## Core Syntax

Workflow templates use Go `text/template` syntax with `{{ }}` delimiters.

Common forms:

- `{{ .Input.company.canonicalName }}` accesses workflow input data.
- `{{ (index .Steps "step-id").text }}` accesses prior step text.
- `{{ (index .Steps "step-id").results.structured.fieldName }}` accesses a structured field.
- `{{ toJSON (index .Steps "step-id").results.structured }}` embeds structured data as JSON.
- `{{ if .Input.includeDetails }}...{{ else }}...{{ end }}` branches on a value.
- `{{ range .Input.items }}...{{ end }}` iterates over a list.
- `{{ with .Input.company }}{{ .canonicalName }}{{ end }}` scopes into a value.
- `{{ index .Input.item "Header Name" }}` accesses a map key containing spaces or punctuation.

`index .Steps` is the stable step lookup form in prompts and output templates because step IDs often contain hyphens.

## Interpolated Ids And Names

Templates render before the agent reads the prompt, so a bare `{{ .Input.company.id }}` reaches the agent as an anonymous 24-character hex string with no type information. Untyped rendered ids get misrouted: run evidence shows an agent passing a rendered company id as a company name argument and halting on a failed lookup.

- State the resource type around every interpolated id or name: "the Company with id `{{ .Input.company.id }}`", "the CIM document with id `{{ (index .Steps "find-cim").results.structured.documentId }}`".
- Pair the id with a human-readable label from the same source when one exists: "the CIM document with id `{{ ...documentId }}` (`{{ ...documentName }}`)". Resolved input label fields per resource type are listed in `inputs-and-resources.md`: `canonicalName` for company, `firstName`/`lastName` for person, `name` for dataEntity, folder, and workspace.

## Template Context

Step templates render against a context with three primary roots:

- `.Input`: workflow inputs after resource resolution.
- `.Steps`: completed step outputs keyed by step ID.
- `.StepArtifacts`: workflow artifacts keyed by producing step ID.

Call `list_workflow_building_options` with kind `promptTemplateVariables` without `workflowId` for the generic step-type catalog; entries with `stepType` `(global)` are the workflow-level roots (such as `.Now` and `.TriggeredBy`). For a prompt or template in a specific workflow, pass `workflowId` plus the target: `stepId` for an existing step at any depth, `stepId` plus `childStepId` for an existing iterator child, `insertIndex` for a new top-level step, `stepId` plus `insertIndex` for a new child position under that iterator, or `stepId` plus `arm` plus `insertIndex` for a new position inside a branch arm (`arm` is required when `stepId` names a branch and `insertIndex` is given, and rejected when `stepId` is not a branch; targeting an existing branch step by `stepId` alone needs no `arm`). Use child index `0` to discover iterator item variables before adding the first child. The contextual result contains concrete in-scope expressions and value shapes for workflow inputs, trigger values, earlier producer outputs, and iterator item variables.

`.usage` is attached at runtime but is not a supported addressable path: a reference to it produces a non-blocking `unrecognized_step_path` warning, so do not rely on it.

Templates render with `missingkey=zero`. A missing *terminal* key renders the sentinel `<no value>` (not an empty string); dereferencing *through* a missing or non-object intermediate fails the run with a message naming the input and its actual shape (see `inputs-and-resources.md`). Avoid relying on missing data as a control signal unless the prompt explicitly handles the empty case.

Two carve-outs. A declared-optional input the run did not supply is seeded with an empty value, so `{{ .Input.<key> }}` on it renders as nothing rather than `<no value>`; dereferencing a sub-path on one still fails, with a message saying the field is optional and was not provided. And a step in a branch arm that was not taken never enters the context at all, so a reference to it renders the sentinel; a branch *condition* reading the same step is a run-time error instead (see `step-types.md`).

## Template Functions

The discoverable functions and their signatures come from `list_workflow_building_options` kind `promptTemplateFunctions`: `step`, `toJSON`, `pluck`, and `dateInZone`. Common uses:

- `toJSON` serializes a value to JSON. Use it when passing structured output to another step or rendering citations into output templates.
- `step` returns a step output map, for example `{{ (step "step-id").text }}`. Prefer `index .Steps` when consistency matters.
- `pluck` extracts one key from each map in a list, for example `{{ pluck "name" .Input.companies }}`.
- `dateInZone` formats a `time.Time` in an IANA timezone, for example `{{ dateInZone "2006-01-02" .Now "America/New_York" }}`.

`iteratorResults` and `iteratorSummaries` also execute at run time but the catalog does not advertise them; they are runtime helpers. The checker validates their call arity and that the referenced step is an iterator step (otherwise it emits an error-severity `invalid_step_path` finding). `iteratorResults` returns text-only iterator results; use it for simple summaries. `iteratorSummaries` is lossy; avoid it for new building.

## Step Output References

Reference a step's output with `(index .Steps "<stepId>")` and then the addressable path for that step type. Use target-aware `promptTemplateVariables` for the concrete expressions available at that workflow position. The canonical access forms:

- Prior step text: `{{ (index .Steps "<stepId>").text }}`
- Structured output: `{{ (index .Steps "<stepId>").results.structured }}` (or `.results.structured.fieldName`)
- Structured output as JSON: `{{ toJSON (index .Steps "<stepId>").results.structured }}`
- Artifacts: `{{ index .StepArtifacts "<stepId>" }}` (the root `.StepArtifacts`, not a `.Steps` sub-path)

When a downstream step needs machine-readable structured data, use `toJSON` instead of plain interpolation.

## HITL Review Payload Templates

Human approval `reviewPayloadInput` uses Go templates when structured upstream output needs a deterministic review envelope. Dynamic strings and objects should pass through `toJSON` so the rendered payload stays valid JSON.

The payload must render as JSON with an `operations` array. Each operation should contain a stable `id`, durable `value`, and reviewer-facing `display`.

`display.facts` must render as an array of rows shaped `{ "label": "...", "value": "..." }`. Every displayed fact row needs a non-empty `label` and non-empty `value`; use a fallback such as `"-"` for optional values or omit the row.

## Iterator Sources

Iterator source fields have stricter saved forms than normal prompt templates.

Call `list_workflow_building_options` with kind `iteratorSources`, `workflowId`, and the iterator's existing `stepId` or new top-level `insertIndex`. Use the returned source expression, source type, and item shape.

Discovery resolves the target against top-level steps only, so an iterator inside a branch arm cannot be targeted: its `stepId` is rejected with "is not an iterator step" because the top-level ancestor is the branch. Discover the sources against a top-level iterator, or read the grammar below, and set the arm-nested iterator's `source` and `sourceType` by hand.

- Data entity iterator source: `{{ .Input.<fieldName> }}`
- Resource list iterator source: `{{ .Input.<fieldName>.entries }}`
- Generic array iterator source: `input.<fieldName>` or `{{ .Input.<fieldName> }}` with `sourceType: "array"`
- Structured output iterator source: `{{ .Steps.<stepId>.results.structured.<arrayKey> }}`
- HITL approved operations iterator source: `{{ .Steps.<hitlStepId>.humanInLoopState.approvedPayload.operations }}`

For `stepOutput` sources, the referenced step must appear before the iterator. Normal structured-output sources must target an array field in the referenced step's `OutputSchema`. HITL approved operations use `humanInLoopState.approvedPayload.operations` and do not require a redundant output schema.

Inside iterator child prompts, read the active item through `.Input.item`. If `contextVariable` is set on the iterator, the same item is also available through that name.

- Structured output item: `{{ .Input.item.name }}`
- Primitive item wrapped by the iterator: `{{ .Input.item.value }}`
- Data entity row with a simple header: `{{ .Input.item.Company }}`
- Data entity row with spaces in the header: `{{ index .Input.item "Company Name" }}`
- Resource list item resource: `{{ .Input.item.resource.canonicalName }}`
- Resource list column: `{{ (index .Input.item.columns "Column Name").value }}`
- HITL approved operation envelope: `{{ .Input.item.value }}`
- Custom context variable example: `{{ .Input.company.canonicalName }}`

## Iterator Results After Completion

Raw `items` preserve child structured output, citations, status, error, index, and original item data.

Inside raw iterator `items`, child step outputs are keyed by child step ID and structured output lives under `results.structured`:

```text
{{ range $item := (index .Steps "iterator-step-id").items }}
{{ toJSON (index (index $item.stepOutputs "child-step-id").results "structured") }}
{{ end }}
```

`iteratorResults` only fits text-only summaries. `iteratorResults` drops structured output, citations, status, error, and item index.

## Tool Inputs

Tool step input is a string template. If the rendered string parses as JSON, the tool receives that JSON object. Otherwise, the tool receives `{ "input": "<rendered text>" }`.

JSON-rendering tool inputs fit tools that expect structured arguments:

```text
{
  "operations": {{ toJSON (index .Steps "approved-ops").results.structured.operations }}
}
```

## Output Templates And Notifications

Output section templates use the same syntax. Common forms:

- Text output: `{{ (index .Steps "step-id").text }}`
- Citations JSON: `{{ toJSON (index .Steps "step-id").citations }}`
- Iterator summary markdown: range over raw `items` or `iteratorResults` depending on the needed data.

Email notification conditions also use templates and must render to a boolean. Prefer a structured completion step as the notification gate:

```text
{{ (index .Steps "notification-gate").results.structured.shouldNotify }}
```

## Template Contracts

- `index .Steps` is the stable form in prompt-like templates and output templates.
- The special `.Steps.<stepId>...` saved form is for iterator source configuration.
- `toJSON` preserves structured handoffs.
- Preserve exact input names and casing.
- `item` is a reserved input name, not a discouraged one: iterators own `.Input.item`, and declaring a field with that key is rejected as `reserved_key`.
- State the resource type around interpolated ids and names, and pair ids with a human-readable label where one exists.
