# Workflow Inputs And Resources

Use this reference when building workflow input fields, prompts, iterator sources, or output templates that read workflow inputs or resource-list items. Resource inputs render as resolved objects, not raw IDs: `resolveTemplateResources` replaces each submitted ID with the full object before any step runs.

## Input Schema Shape

Flat input fields are the expected building model. Each visible input field has a name, a type, an optional default, and an optional input form widget.

Input fields apply to every trigger type; a schedule's static `input` is validated against them.

Each field is `required` or `optional`. A required field must be supplied when a run is created, from the run form, the API, MCP, chat, or a schedule save, and a value of `""`, `null`, or an empty array does not count. `false`, `0`, and `{}` do. Omitting `presence` keeps an existing field's setting and starts a new field required.

Run creation enforces the presence a workflow actually stores, which is not always the presence `effectiveInputSchema` reports. The stored list is written only when a write says something about presence: the workflow already declared one, or the request sets `presence` on at least one field. A `configure_workflow_input` call that sets it on no field leaves a never-declared workflow undeclared, and such a workflow keeps accepting an omission that `effectiveInputSchema` reports as `required`, because an undeclared schema is served a derived baseline rather than a stored list. Set `presence` explicitly on the fields that matter and the served contract and the enforced one are the same.

A `default` does not make a field optional. Defaults fill absent keys only, so a caller sending `""` for a defaulted field keeps the blank and still fails the check. Required plus a real default means "omit it to get the default, send it blank and be rejected", which is a useful contract.

Three shapes are rejected at save time, all of them a required field no run could satisfy:

- A blank default (`""`, `[]`, `null`). Omitting the field yields the blank, so give it a non-blank default, drop the default, or mark it optional.
- Required with no non-blank default on an email, event, or webhook trigger (`required_without_default`). Nothing fills a form on a triggered run, so every run would be rejected.
- Required while a stored schedule's static `input` leaves it unsatisfied (`schedule_input_gap`), either by omitting a key no non-blank default would fill or by supplying it blank. That schedule would be rejected on its next fire, so set a value on the schedule, give the field a non-blank default, or mark it optional.

An optional field left unsupplied renders as empty in a step template rather than the literal `<no value>`. A branch condition sees it differently on purpose: the key is absent there, so `has(input.<key>)` is false, which is how a condition distinguishes "the run supplied nothing" from "the run supplied a blank". A field that declares a default is always present in both places, because the default fills the key first.

`effectiveInputSchema`, on `get_workflow`, is how you read presence back. Each entry carries `key`, `type`, `presence`, `default`, and `source`, plus the `label`, `widget`, and `description` a caller needs to render or explain the field: `author` for a declared field, `trigger` for a key the trigger injects, and `manual` for a stand-in nothing injects, which a caller must supply by hand. Trigger and manual entries are always optional, since they are absent by design on a manual run. Presence itself is stored as the schema's top-level required list rather than per field, and a stored list is served back verbatim: the trigger never relaxes it, so a declared-required field still reads `required` on an email trigger. The trigger and the field's default decide presence only for a workflow that never declared a list. A trigger change that would contradict a declared required field is rejected at save time, by the trigger and schedule shapes above, instead of being quietly re-derived.

On an email, event, or webhook trigger nothing fills a form, so a declared field must carry a non-blank default or be optional, and its value acts as a named constant a step can reference instead of a literal buried in a prompt. Those triggers also supply their own run context keys, which arrive undeclared and cannot be used as field names: declaring one is rejected as `trigger_context_collision`, because the producer would overwrite it on every triggered run.

Input field selectors come from `list_workflow_building_options` kind `inputFieldTypes`. Each entry carries `name`, `description`, `multiSelect`, and `fields`; each resource field carries `name`, `type`, `description`, and `optional`. Derive cardinality and resolved access paths from that response. A resource-typed field submits an ObjectID hex at run time; a field whose returned `multiSelect` is true submits an array of hex IDs. `dataEntityMulti` is the current multi-select example, not a permanent uniqueness rule. Runtime resolution adds `_resourceType`, which is intentionally absent from the catalog's `fields`.

Defaults apply only when the run input omits the field. A submitted blank value, false boolean, zero number, empty object, or empty array remains the submitted value.

Do not name a workflow input `item`: iterator child steps reserve `.Input.item` for the active iterator item, and declaring a field with that key is rejected as `reserved_key`.

## Resolution Rules

- Resolution happens once at run start, before any step executes.
- An unresolvable resource input fails the run instead of passing through as a raw ID. Resource-list size truncation is the exception described under Resource Lists.
- Every resolved object carries a `_resourceType` field set to its canonical type, readable as `{{ .Input.<field>._resourceType }}`.
- Dereferencing *through* a missing or non-object intermediate (for example `.Input.company.foo.bar` when `company` is absent or a scalar) fails the run with a message naming the input and its actual shape. A missing *terminal* key (for example a leaf typo like `.Input.company.canonicalNam`) does not fail; under `missingkey=zero` it renders the sentinel `<no value>`, not an empty string.

## Access Contexts

Direct access works from any step: `{{ .Input.<field>.canonicalName }}`, `{{ .Input.<field>.name }}`, `{{ .Input.<field>._resourceType }}`.

Iterator item access works inside iterator child steps through `.Input.item` (and `.Input.<contextVariable>` when the iterator sets one). The item shape depends on the source type; see Resource Shapes and Iterator Sources.

## Resource Shapes

Resolved objects carry the fields below. Fields marked optional appear only when set.

### `company`

| Field | Type | Notes |
| --- | --- | --- |
| `id` | string | Company ObjectID hex |
| `canonicalName` | string | Primary name |
| `alternativeNames` | string | Comma-separated names, not an array |
| `externalReference` | string | JSON-serialized object, not a map |
| `companyType` | string | e.g. `portfolio`, `prospect` |
| `industry` | string | |
| `website` | string | |
| `description` | string | |
| `shortDescription` | string | |
| `location` | string | Headquarters |
| `sector` | string | |
| `subsector` | string | |
| `employeeCount` | any | Enriched metric value |
| `arr` | any | Enriched metric value; optional |
| `adjustedEbitda` | any | Enriched metric value; optional |
| `ebitda` | any | Enriched metric value; optional |
| `revenue` | any | Enriched metric value; optional |
| `lastValuation` | any | Enriched metric value |
| `totalMoneyRaised` | any | Enriched metric value |

The fields from `website` onward prefer enriched values and fall back to base company fields; each metric field is the value of an enriched metric.

### `person`

| Field | Type | Notes |
| --- | --- | --- |
| `id` | string | Person ObjectID hex |
| `firstName` | string | |
| `lastName` | string | |
| `email` | string | Work email |
| `personalEmail` | string | |
| `currentTitle` | string | |
| `currentCompanyName` | string | |
| `phoneNumber` | string | |
| `location` | object | `{city, state, country, postalCode, address, position: {lat, lng}}` |
| `linkedinUrl` | string | |
| `highestDegree` | string | |
| `company` | string | Company ObjectID hex; optional |
| `externalReference` | map | `{id, platform}`; optional |

`externalReference` is a map here, unlike the JSON string on `company`: `{{ .Input.<field>.externalReference.platform }}`.

The current `inputFieldTypes[].fields` catalog labels `person.location` as a string, but the resolved runtime value is the object above. Use the runtime shape when building templates and report the catalog mismatch to Metal if it blocks a workflow.

### `dataEntity`

| Field | Type | Notes |
| --- | --- | --- |
| `id` | string | DataEntity ObjectID hex |
| `name` | string | File name |
| `displayName` | string | |
| `fileExtension` | string | e.g. `.csv`, `.pdf` |
| `sourceType` | string | |
| `tags` | any | Tags array |
| `metadata` | any | Metadata object |
| `workspace` | string | Workspace hex; optional |
| `company` | string | Company hex; optional |
| `folderPath` | string | Dot-separated folder ObjectID path; optional |
| `folderIds` | []string | Folder ObjectIDs from `folderPath`; optional |

`dataEntity` is iterable as CSV or XLSX rows; see Iterator Sources.

### `dataEntityMulti`

An array of `dataEntity` objects (canonical type `dataEntity`). It has no dedicated iterator `sourceType`; iterate it with `sourceType: "array"` and `source: "input.<field>"` or `source: "{{ .Input.<field> }}"`. Access individual items with `{{ index .Input.<field> 0 }}` or `{{ (index .Input.<field> 0).name }}`. `list_workflow_building_options` kind `iteratorSources` returns that pairing for the field, described as "Selected data entities from `<field>`"; each item is the resolved data-entity object, with a scalar fallback wrapped under `value`.

### `folder`

| Field | Type | Notes |
| --- | --- | --- |
| `id` | string | Folder ObjectID hex |
| `name` | string | |
| `folderId` | string | Workspace ObjectID hex |
| `parentId` | string | Parent folder hex, empty string if root |
| `path` | string | Full folder path |

### `workspace`

| Field | Type | Notes |
| --- | --- | --- |
| `id` | string | Workspace ObjectID hex |
| `name` | string | |
| `source` | string | |
| `rootFolder` | string | Root folder ObjectID hex |
| `isPrivate` | bool | |
| `isPersonal` | bool | |
| `company` | string | Company hex; optional |

## Resource Lists

`resourceList` resolves to list metadata plus an embedded `entries` array.

The resolver fetches entries in pages. When the embedded count reaches the 5,000 threshold and another page remains, it stops at that page boundary and logs a truncation warning without failing the run. Because it appends the page before checking the threshold, the embedded count can exceed 5,000. `entryCount` reports the embedded count, not the source total, and the payload has no truncation flag. Use list browsing for targeted reads and `export_list_entries` when a workflow needs complete contents from a large list.

| Field | Type | Notes |
| --- | --- | --- |
| `id` | string | ResourceList ObjectID hex |
| `name` | string | |
| `description` | string | |
| `resourceType` | string | The entries' resource type |
| `entryCount` | int | Number of embedded entries; can exceed the 5,000 stopping threshold by one fetched page |
| `isPrivate` | bool | |
| `entries` | []map | Entry objects, shape below |
| `createdAt` | time | Optional |
| `updatedAt` | time | Optional |
| `createdBy` | string | Creator user hex; optional |
| `owners` | []string | Owner hex strings; optional |

Resource list iterator source:

```json
{
  "source": "{{ .Input.<field>.entries }}",
  "sourceType": "resourceList"
}
```

Inside a resource-list iterator, `.Input.item` is the active entry, shaped `{id, addedAt, columns, resource}`.

- Column access: `{{ (index .Input.item.columns "Column Name").value }}`. Columns are keyed by display name, and each column value is a map `{type, value, isNull, enriched, source, sourceId}`.
- `.Input.item.resource` is the entry's resolved resource, shaped by the list's `resourceType`. `company`, `person`, and `dataEntity` use the same shapes as their input types. A list whose resource type has no resolver falls back to a raw `{id, type}` reference. `deal` and `activity` shapes:

`deal`: `id`, `name`, `projectName`, `owner`, `notes`, `size`, `status` (org-specific label, falling back to an internal enum such as `ACTIVE` or `MONITORING`), `stage` (org-specific label, falling back to an internal enum such as `SOURCED`, `MONITORING`, or `ON_PAUSE`), and optional `companyId`, `createdAt`, `updatedAt`, `startDate`, `closeDate`, `createdBy`.

`activity`: `id`, `subject`, `type`, and optional `startedAt`, `endedAt`, `createdAt`, `updatedAt`, `createdBy`, `dataEntity`, `participants` (array of `{id, type}`).

## Iterator Sources

| Source type | Saved source form |
| --- | --- |
| `dataEntity` | `{{ .Input.<field> }}` (parses `.csv` and `.xlsx` rows keyed by the header row) |
| `resourceList` | `{{ .Input.<field>.entries }}` |
| `array` | `input.<field>` or `{{ .Input.<field> }}` |
| `stepOutput` (structured) | `{{ .Steps.<stepId>.results.structured.<arrayKey> }}` |
| `stepOutput` (HITL) | `{{ .Steps.<hitlStepId>.humanInLoopState.approvedPayload.operations }}` |

An `array` source requires an input field that resolves to a list: an `array`-typed field or a resource type whose catalog entry has `multiSelect: true`, currently `dataEntityMulti`. A single-valued resource input is rejected with the error-severity `invalid_input_path` coherence finding, which is what blocks the write on this surface: authoring skips the iterator source-resolution check and leaves the judgement to the checker.

The item shape depends on the source:

- A `dataEntity` iterator item is a flat map keyed by the file's column headers, with string cell values: `{{ .Input.item.<Header> }}` or `{{ index .Input.item "Column Name" }}`. It has no `.columns` and no `.value` wrapper.
- A `resourceList` iterator item is an entry with `.columns` and `.resource` (above).
- An `array` or structured-output item is the object itself (`{{ .Input.item.<field> }}`); a primitive item is wrapped as `{ "value": <v> }` and read with `{{ .Input.item.value }}`.
- An HITL approved operation is a reviewed envelope `{id, value, display?}`; read the operation with `{{ .Input.item.value }}`.

For `stepOutput` sources, the referenced step must appear before the iterator. A structured-output source must target an array property in that step's `OutputSchema`. HITL approved operations use the approved-payload path and do not need a separate output schema.

Call `list_workflow_building_options` with kind `iteratorSources`, the workflow ID, and the iterator's existing `stepId` or new top-level `insertIndex` before setting `source` or `sourceType`. Use the returned canonical expression and item shape instead of deriving them from the input type.

That discovery only accepts a top-level iterator: an iterator inside a branch arm is rejected with "is not an iterator step", because the target resolves through its top-level ancestor, which is the branch. For one of those, take the pairing from the table above.
