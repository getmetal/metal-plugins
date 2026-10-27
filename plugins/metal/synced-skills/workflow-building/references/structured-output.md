# Workflow Structured Output

Use this reference when a step needs an `OutputSchema`, when building schema-backed downstream contracts, or when reasoning about how structured output is enforced at run time.

When building workflow `step.OutputSchema` JSON, follow the schema rules in this reference (see Output Schema Rules below) before creating or revising the schema. This applies only to workflow `step.OutputSchema`; keep workflow `inputSchema`, `outputConfig.schema`, `x-template` output sections, and work product template schemas in their own building paths.

## Enforcement Model

`agent`, `completion`, and `executeCode` steps accept an `OutputSchema`. When one is declared, the runner holds the step's output to it and the validated payload appears at `results.structured`. A step whose output cannot be made to satisfy its schema fails loudly; schema-invalid output never reaches `results.structured`.

Per step type:

- Agent steps: the engine injects a structured-submission tool. Submissions are validated in-loop and the last valid submission wins. At wrapup the runner resolves in order: an accepted submission, one forced submission turn, schema-validated extraction from the final message, then step failure.
- Completion steps: the response resolves through validate, coerce, one re-issue, then step failure.
- Execute-code steps: stdout must be a single JSON value; it is validated against the schema, with coercion attempted before failure. Without `OutputSchema`, stdout remains text even when it is valid JSON.

A single agent step with an `OutputSchema` is the standard shape when a step needs both tool use and validated structured output. A completion step fits when a normalization, classification, or gate decision is its own responsibility; `executeCode` fits when deterministic code can produce the payload.

## Coherence Contract

The coherence checker validates downstream `results.structured` references against the schema:

- Any reference to a step's `results.structured` requires a declared `outputSchema` on that step.
- `results.structured.<key>` requires `<key>` to be a declared top-level property, in root `properties` or inside a root `oneOf`/`anyOf` variant.
- Iterator `stepOutput` sources must target a declared array-typed key.

Declare every key downstream steps read. `additionalProperties` does not exempt a key from declaration.

## Handoff Key Paths

- Step text: `(index .Steps "<id>").text` (promoted from `results.text`).
- Validated structured output: `(index .Steps "<id>").results.structured` and `.results.structured.<key>`.
- Embedding structured output into a later prompt, tool input, or render input: `{{ toJSON (index .Steps "<id>").results.structured }}`, so JSON structure is not lost through string interpolation.

## Prompt Shape

The schema constrains shape; the prompt owns substance. Prompts for schema-bearing steps commonly include:

- Input context: exact workflow inputs and prior-step references, with every interpolated id or name prefixed by its resource type (see `template-syntax.md`).
- Task instructions: what to retrieve, inspect, calculate, or decide.
- Source rules: what counts as usable evidence and what must be rejected.
- Missing-value rules: the sentinel or default for values the step cannot support.
- Field semantics the schema cannot express: units, source periods, enum meanings, and which fields carry notes, coverage, or limitations.

When a prompt embeds schema JSON, keep the prompt-embedded schema and the step `OutputSchema` aligned.

## Output Schema Rules

Write standard JSON Schema. The runner validates the step's output against the full schema with a spec-compliant validator, so the keywords the schema carries are enforced at the step boundary. Keep root schemas as objects, and paste final schema JSON inline when the user needs the JSON.

### Persisted Keywords

The saved schema representation carries: `type` (single or type-union array), `description`, `properties`, `items`, `required`, `additionalProperties`, `enum`, `const`, `oneOf`, `anyOf`, `not`, `pattern`, `default`, `uniqueItems`, `minimum`, `maximum`, `minLength`, `minItems`, and `maxItems`.

Keywords outside that set are dropped when the schema is saved and never validate. Do not use: `$ref`, `$defs`, `definitions`, `allOf`, `format`, `exclusiveMinimum`, `exclusiveMaximum`, `multipleOf`, `maxLength`, `minProperties`, `maxProperties`, `patternProperties`.

### Structural Rules

- Top-level must be `{"type": "object"}`; downstream `results.structured.<key>` references and the coherence contract require object-rooted output.
- Declare every top-level key downstream steps reference.
- Every array includes an `items` schema.
- Prefer the simplest shape that expresses the contract. Composition and type unions validate, but a simpler schema gives the model less room to produce a valid-but-unintended variant.

### Constraint Keywords

Value constraints (`minimum`, `maximum`, `pattern`, `minLength`, `minItems`, `maxItems`, `uniqueItems`) are enforced at validation, but providers may not see them during generation: Anthropic generation strips value constraints from the generation-side schema and OpenAI runs non-strict. A constraint the model cannot infer from context surfaces as coercion, a retry, or a loud step failure rather than guiding generation.

- Use constraints to encode real contract requirements, not stylistic preferences.
- Restate load-bearing constraints in the prompt so the model can satisfy them during generation.
- Prefer `enum` and `description` for steering generation.
- Do not rely on `default`; validators ignore it.

### Inference From Examples

When inferring a schema from an example object:

- Strings to `string`; booleans to `boolean`; numbers to `number` (use `integer` for clearly integral fields).
- Objects to a fixed object with recursive `properties` and `required`.
- Arrays to `array` with `items` inferred from the first element; merge keys across all objects when an array holds objects.
- If an array is empty, ask the user for the item type before generating.
- Consider `enum` only when the allowed values are clear.

### Descriptions

Do not add `description` keys by default. Add them only when the user asks, supplies description text to preserve, or a field needs generation steering a name cannot carry, and keep them short.

### Schema Self-Check

Before relying on a schema, verify:

- Top-level is `type: "object"`.
- Every key downstream steps reference is declared as a top-level property.
- Every array has an `items` schema.
- Keys stay within the persisted keyword set; nothing depends on a keyword that is dropped on save.
- Constraints reflect real contract requirements and load-bearing ones are restated in the prompt.
- If the user did not ask for descriptions, no `description` keys appear beyond deliberate generation steering.
