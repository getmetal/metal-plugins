# Workflow Input Resolution

Use this reference when resolving a workflow's `inputSchema` fields into the `input` object `run_workflow` accepts. Fetch the schema with `get_workflow` before doing anything else. Resolution decisions come from each field's declared JSON Schema and resource selector, never from its name or description.

## Authoring selectors and runtime types

| Type | Category | Raw `run_workflow` value | Resolution tool | Multi-value? |
|---|---|---|---|---|
| `string` | scalar | JSON string | none; literal value | no |
| `text` | authoring selector | JSON string; saved as `type: "string"` with textarea UI metadata | none, literal value | no |
| `number` | scalar | JSON number | none; literal value | no |
| `boolean` | scalar | JSON boolean | none; literal value | no |
| `object` | scalar | JSON object, freeform | none; literal value | no |
| `array` | scalar | JSON array, freeform | none; literal value | no |
| `company` | resource | 24-char hex ObjectID | `search_companies` → `get_company` to confirm | no |
| `person` | resource | 24-char hex ObjectID | `search_people` | no |
| `dataEntity` | resource | 24-char hex ObjectID | `search_documents` → `get_document` to confirm | no |
| `dataEntityMulti` | resource | array of 24-char hex ObjectIDs | same as `dataEntity`, resolved per file | yes |
| `folder` | resource | 24-char hex ObjectID | none available in this MCP | no |
| `workspace` | resource | 24-char hex ObjectID | none available in this MCP | no |
| `resourceList` | resource | 24-char hex ObjectID | `list_lists` → `get_list` to confirm | no |

`text` is an authoring selector, not a separate runtime JSON type. Authoring stores it as a string field and records the textarea choice in `inputUiSchema`.

Among the current resource selectors, `dataEntityMulti` accepts an array and the others accept one ObjectID. A plain JSON `array` is not a resource selector even when its values look like IDs. It remains raw JSON and receives no resource validation, hydration, `_resourceType`, or automatic file attachment. `dataEntityMulti` validates and hydrates each data-entity ID and may attach those files to agent context.

## Resolve from the declared contract

**The field's declared schema decides the value shape and constraints, never its name or description.** A field named like a business entity can still be a plain string that expects the literal name. A resource selector requires an ObjectID even when its description is empty. Resolve from the declared contract, not from what the field sounds like it means.

## Presence

Each field is `required` or `optional`, and `get_workflow`'s `effectiveInputSchema` reports which alongside the field's `source`: `author` for a declared field, `trigger` for a key the trigger injects, and `manual` for a stand-in nothing injects that a caller must supply by hand. Trigger and manual entries are always optional, since they are absent by design on a manual run.

Supply every `required` entry after defaults are applied. A required field rejects a value that is missing, `""`, `null`, or an empty array; `false`, `0`, and `{}` satisfy presence but can still fail another schema constraint. An `optional` entry may be omitted, and omitting it is not the same as sending a blank: a workflow's branch conditions can tell those apart with `has(input.<key>)`, and its templates render an omitted optional as nothing rather than a `<no value>` sentinel. When the user has no value for an optional field, leave the key out rather than sending `""`.

## Defaults

A schema field can carry a `default` value of its own type, such as a `dataEntity` field pre-set to a runtime template asset. The run service applies defaults to absent keys before validation. A stored resource default is already part of the workflow contract and does not need caller-side re-resolution. An explicit blank or other submitted value is not replaced. A default does not make a field optional, and the two are independent: a required field with a real default means "omit it for the default; send it blank and validation uses the blank." Because the default fills the key, `has(input.<key>)` is true even when the run input omitted it. Leave a defaulted field out unless the user wants to override it. Resolve an override according to the field's declared resource selector.

## Scalar values and constraints

### `string` / `text`

Pass the user's literal text after checking all declared constraints. A field can restrict values with JSON Schema keywords such as `enum`, `pattern`, `format`, `minLength`, or `maxLength`. The description supplies intent, while the schema supplies enforceable constraints. Do not invent a date format, allowed value, or other restriction that the schema omits. Ask the user when the intended value remains unclear.

### `number`

Pass the user's value as a JSON number and enforce any declared numeric constraints, including minimum and maximum bounds. Ask when the intended value is not clear from the schema and context.

### `boolean`

Pass `true` or `false`. Apply any declared enum or other constraint, and ask when the intended value is unclear.

### `object` / `array`

Match declared `properties`, `required`, `items`, cardinality, and other constraints exactly. When the node is bare, the field is opaque: the caller either has the literal JSON from context or must ask the user. Never invent a nested shape that is not declared.

## Resource types resolved to an ObjectID

Every resource-typed field submits an ObjectID hex string (or, for `dataEntityMulti`, an array of them). Metal resolves the IDs after submission. This skill only finds the right IDs to submit; see the `workflow-building` skill's `references/inputs-and-resources.md` for the values a step receives.

### `company`

Call `search_companies` with the user's name or description. A single confident match: use its `id`. Multiple or zero matches: apply the shared ambiguity rule below.

### `person`

Call `search_people` with the user's name, title, or company context. Same match/no-match handling as `company`.

### `dataEntity`

Call `search_documents`. Use filter-only mode (`query: ""` plus `documentType` or `companyIds`) for requests such as "the latest CIM" or "all board decks," and content mode with a real `query` for "the file that mentions X." When precision matters, such as resolving one required document, confirm the candidate with `get_document` before submitting its `id`.

### `dataEntityMulti`

Resolve each file the same way as `dataEntity`, then submit the IDs as an array. Do not apply this resolution recipe to a plain `array`: a plain array is literal JSON and the run service does not validate or hydrate its values as data entities.

### `folder`

**No workflow tool resolves folder IDs.** Ask the user for a confirmed folder ObjectID. A workspace ID is not a folder fallback: folder validation rejects it and may return the workspace's `rootFolder` as a repair hint. Use that root-folder ID only after confirming it is the folder the user intends. If no folder ID is available, treat the input as blocked rather than deriving one from document metadata.

### `workspace`

No workflow tool resolves workspace IDs. Ask for a confirmed workspace ObjectID and treat the input as blocked otherwise. Do not submit a folder ID as a workspace fallback.

### `resourceList`

Call `list_lists`, optionally filtered by `resourceType` when the workflow context implies one, such as a company-scoped list. Confirm the candidate with `get_list` before submitting its `id`. This also surfaces the column schema when the workflow reads specific columns.

## Ambiguous, zero-match, or no-tool resolution

When resolution finds zero matches, multiple plausible matches, or no tool for a `folder` or `workspace`, do not guess or submit a best-effort ID. Present the candidates or evidence gap and ask the user to pick or supply the ID. Never submit an ID unless the evidence supports the user's intended resource; a wrong ID can fail the run or run successfully against the wrong company, document, or list.
