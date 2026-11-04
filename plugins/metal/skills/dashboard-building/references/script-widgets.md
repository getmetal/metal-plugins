# Script widgets

A script widget (`dataSource: "script"`, stored as `DASHBOARD_DATA`) is a Python script that runs in a restricted interpreter each time the widget renders. It reads Metal through the injected `metal` SDK object and assigns `_output`, and optionally `_citations` and `_parameters`.

The `metal-sdk-scripts` skill covers the Metal SDK and `run_metal_sdk_query`. A widget script runs in a different runtime: it gets a widget `input`, can declare data controls, can read source files, allows more imports, and has its own limits (below). A script that works in `run_metal_sdk_query` is not proof that it works as a widget. When `run_metal_sdk_query` is available, it is still a quick way to check one method's real response shape before you write the widget.

## Globals

- `metal`: the read-only Metal SDK client. The method set is closed. Find methods with `list_sdk_methods` and read each one with `get_sdk_method` (signature, route, response contract, examples) before you call it. Never invent a method name. If no method fits, stop and tell the user.
- `input`: a dict with three keys.
  - `input["context"]`: on a canvas dashboard, `orgId`, `userId` and `dashboardId`. It carries no deal, company, list, fund, person or task ID.
  - `input["placement"]`: the widget's own placement (title, type, layout). Rarely needed.
  - `input["parameters"]`: the viewer's current data-control selections, keyed by parameter `id`. It is empty on the first render. Read it with `input.get("parameters") or {}` and fall back to each control's `default`.
- `json`, `datetime`, `math`, `statistics`: already imported.
- `MetalAPIError`: the error type SDK calls raise, available for `except MetalAPIError`.

## What the script assigns

- `_output` (required): the shape for the widget type. Charts and tables follow `references/chart-table-output.md`. `HTML` is `{"widgetCode": "<fragment>"}` with a non-empty fragment that meets `references/html-widgets.md`; the server also checks the syntax of its inline JavaScript. A script that doesn't set `_output` fails.
- `_citations` (optional): a top-level list, not inside `_output`. It fills the widget header's source list. Build it with `metal.citations.collect(*objects, extra=None)`: pass every SDK result you used, and it gathers the `citations` lists those results carry, such as resolved metric and observation points. Add other sources with `extra=[{"type": "webResult", "title": "...", "url": "..."}]`. An entry without a `title` is dropped, and only the first 64 are kept. When the widget has no source, set `_citations = []`; never invent one. A file read with `metal.open_file` or `metal.get_file_bytes` is added to `collect()` automatically.
- `_parameters` (optional): a top-level list of data controls, not inside `_output` and not named `parameters`. See Data controls.

`_output`, `_citations` and `_parameters` must be JSON-serializable. Convert `Decimal` with `float()` or `str()`, `datetime` and `date` with `.isoformat()`, and `set` with `list()`.

## Scope on a canvas dashboard

The script runs with org-wide access and no entity. Query across the org by default. When the user names a company, deal or list, put its ID, taken from a tool result, into the query, or offer a `select` control built from real records. If the user asked for one entity and the ID is missing, render an empty state rather than silently showing org-wide data.

## Data controls

Add data controls by default whenever the widget shows a collection or series from a method that supports filtering, search, sorting or paging. A widget is a tool the viewer operates; "show my deals" should still come back searchable and paged when the method allows it. Tell the user which controls you added. Skip controls for a single value or a fixed visual.

Derive the controls from the method's parameters (read them with `get_sdk_method`), not from the domain:

| What the method accepts | Control `kind` |
|---|---|
| Free-text query | `search` |
| Equality or `in` on a categorical field | `select` (one value) or `multiselect` (several) |
| Date range | `dateRange` |
| Numeric range | `numberRange` |
| Sort options | `select` of sort fields |
| Offset paging (`page` and `limit`, or an offset) | `pagination` |
| A filter the other kinds can't express | `advancedQuery` |

Each entry is `{"id", "kind", "label", "options"?, "default"?}`. `select` and `multiselect` need `options`, a list of `{"value", "label"}`. An option `value` of `""` acts as an "All" choice. `pagination` also accepts `total` and `pageSize` as integers.

| `kind` | Value in `input["parameters"][id]` |
|---|---|
| `select` | the chosen `value` |
| `multiselect` | a list of chosen values |
| `dateRange` | `{"gte": "YYYY-MM-DD", "lte": "YYYY-MM-DD"}`, either bound may be missing |
| `numberRange` | `{"gte": number, "lte": number}`, either bound may be missing |
| `search` | a string |
| `advancedQuery` | the JSON object the viewer typed (or a string if it is not valid JSON) |
| `pagination` | the current page number, starting at 1 |

Rules:

- When the viewer changes a control, only this widget re-runs, with the new values in `input["parameters"]`. Unknown keys are ignored.
- Pass each selection into the SDK call so the server filters, searches and pages. Never fetch one page and filter or page it in Python: that works on a slice, not the result set. Filter in Python only for a dimension the method can't express, and don't page a set you filtered in Python.
- Keep the request's fixed scope in the query, not in a control. "My deals" is an owner filter in the script, not a control.
- Build `options` from real data: a taxonomy or enum method (such as `list_sectors`), or the distinct values in the results. A guessed value silently filters to nothing. If the values can't be listed cheaply, use `search` or `advancedQuery`.
- `pagination` is 1-based offset paging, so don't use it for cursor or `nextToken` methods. Without `total`, Next stays enabled. `pageSize` (default 25) only drives the "Page X of Y" display; keep it equal to the page size the script sends. Pass the page straight through to methods that take `page` and `limit`, or convert it with `offset = (page - 1) * page_size` for methods that take a skip or offset. Check which one the method takes with `get_sdk_method`.

Example: a paged, searchable deal table on a `TABLE` widget.

```python
PAGE_SIZE = 25
params = input.get("parameters") or {}
page = int(params.get("page") or 1)
text = (params.get("q") or "").strip()

body = {"sort": [{"field": "deal_updatedAt", "order": "desc"}, {"field": "deal_id", "order": "asc"}]}
if text:
    body["text"] = text
    body["fullText"] = True
result = metal.search_deals(query={"page": page, "limit": PAGE_SIZE}, body=body)
deals = result.get("data") or []

_output = {
    "columns": [
        {"key": "name", "label": "Deal"},
        {"key": "company", "label": "Company"},
        {"key": "updatedAt", "label": "Updated"},
    ],
    "rows": [
        {"id": d["id"], "companyId": d.get("companyId"), "name": d.get("name") or "", "updatedAt": d.get("updatedAt")}
        for d in deals
    ],
    "entityType": "deal",
}
_citations = []
_parameters = [
    {"id": "q", "kind": "search", "label": "Search"},
    {"id": "page", "kind": "pagination", "label": "Page", "total": result["metadata"]["totalCount"], "pageSize": PAGE_SIZE},
]
```

## Restricted runtime

- Imports are limited to `_strptime`, `collections`, `concurrent`, `csv`, `datetime`, `decimal`, `docx`, `html`, `io`, `itertools`, `json`, `math`, `openpyxl`, `pptx`, `re`, `statistics`, `time`. Any other import fails the render. `csv`, `docx`, `io`, `openpyxl` and `pptx` are there to parse files read with `metal.open_file`. Use `html.escape` for every dynamic string in a fragment.
- Builtins are a closed list: `abs`, `all`, `any`, `bool`, `bytearray`, `bytes`, `chr`, `dict`, `divmod`, `enumerate`, `filter`, `float`, `format`, `frozenset`, `hasattr`, `hash`, `int`, `isinstance`, `issubclass`, `iter`, `len`, `list`, `map`, `max`, `min`, `next`, `ord`, `pow`, `print`, `range`, `repr`, `reversed`, `round`, `set`, `slice`, `sorted`, `str`, `sum`, `tuple`, `zip`. `type`, `getattr`, `setattr`, `super`, `object`, `property`, `staticmethod`, `classmethod`, `vars`, `dir`, `globals`, `locals`, `hex`, `bin`, `open`, `exec` and `eval` are not available. Use `isinstance` instead of `type`, `.get()` or `hasattr` instead of `getattr`, and plain functions and dicts instead of classes.
- The exceptions you can name in `except` are `BaseException`, `Exception`, `ArithmeticError`, `ZeroDivisionError`, `OverflowError`, `FloatingPointError`, `LookupError`, `KeyError`, `IndexError`, `AttributeError`, `ValueError`, `TypeError`, `RuntimeError`, `StopIteration`, `StopAsyncIteration`, `NotImplementedError`, and `MetalAPIError`. Naming any other exception raises `NameError` at the moment it fires, so the guard fails on the case it was written for.
- Depending on the runtime, the script is checked before any line runs, and the render fails on: an attribute whose name starts with `_` (such as `obj._name`), a name, argument, import alias or definition that starts with `__`, a `from x import _y` import, or a disallowed import. Single-underscore names such as `_output` and `_unwrap` are fine.
- There is no file, socket or subprocess access. Everything goes through `metal`.

## Limits

| Limit | Widget script |
|---|---|
| Script size | 1 MiB |
| SDK calls per render | 250 |
| SDK response bytes per render | 32 MiB |
| `_output` size (JSON) | 4 MiB |
| Execution time per render | 50 seconds |
| One SDK call | 30 seconds |
| One source file | 64 MiB |

These are guards against runaway scripts and sit far above what a normal widget uses. Keep renders fast and narrow anyway: fetch what the widget shows, not the whole org, and avoid many large calls in series. For a large result set, page with the method's own `page` and `limit` parameters and add a `pagination` control. Don't use `metal.paginate`, `metal.batch` or `metal.stream_to_workspace` in a widget script: they are not part of the widget contract and not every widget runtime has them.

## Where displayed values come from

Read every number and fact the widget shows through the SDK's data-read methods. They return the same values Metal's built-in widgets show, so the widget agrees with the rest of Metal.

- Financial metrics (revenue, EBITDA, margins, ARR): `metal.get_metric_series` for one series, `metal.resolve_metric_series` for date-range or candidate filtering.
- Enrichment facts (employee count, sector, founding year, website, ownership): `metal.get_observation` for one fact, `metal.batch_observations` for several.
- Each resolved point carries its value and sources. Show `point["displayValue"]`, falling back to `point["selected"]["value"]`, and pass the points to `metal.citations.collect`. Read each point's unit (such as `unitFactor`) from the response instead of assuming raw dollars; confirm the field names with `get_sdk_method`.
- Don't read displayed values off record fields such as a company's `enrichedValues` or a deal's `financials` or `intelligence`. Those snapshots drop zero and empty values and disagree with the built-in widgets. Use `get_companies_by_id` and `get_deal` for identity and links only.

### Valid keys

Metric and observation keys are a fixed registry. A wrong key (`foundedYear` instead of `founded`) returns nothing and raises nothing.

- `get_sdk_method` with `get_metric_series` returns the valid metric keys; with `get_observation` it returns the valid observation keys. Answer "which metrics are available?" from those lists, never from memory or from an example.
- To see which fields one record has populated, read the keys (not the values) of `enrichedValues` from `get_companies_by_id` or `get_deal`.

## Reading source files

`metal.open_file(data_entity_id)` returns a byte stream and `metal.get_file_bytes(data_entity_id)` returns the bytes of a file the viewer can open. Neither appears in `list_sdk_methods`, but both work in widget scripts. Supported types: `xlsx`, `xlsm`, `docx`, `pptx`, `pptm`, `html`, `htm`, `csv`, `tsv`, `txt`, `md`, `json`. Any other type, including `pdf` and legacy `xls`, raises an error. For a PDF, read the extracted text with `list_excerpts` instead.

- Use a file read when you need the file's structure: a named worksheet, a cell range, heading levels, slide notes. For a number Metal already extracted, use the metric and observation methods; a figure re-derived from a workbook can disagree with the rest of Metal.
- Check the type before you read. Take it from the file's `name` suffix and fall back to `fileExtension` only when `name` has none: a file converted to PDF can report `fileExtension` `pdf` while the stored bytes are still the original PPTX.
- Find the file through excerpt search: `metal.search_documents_documents_search` returns excerpts, each with its file's ID in `dataEntity`. Filter fields are schema-qualified (such as `dataEntity_company` or `dataEntity_documentType`); a bare `company` fails with `field <x> is not allowed`. Confirm the field names with `get_sdk_method`. Then load the file records with `metal.get_data_entities_by_id`.
- One page of excerpts can cover only a few files. Narrow the search, for example by document type, rather than paging through many results. If several files qualify, offer a `select` control instead of picking the first.
- Excerpt search finds only indexed files. Word an empty state as "no matching workbook was found", not "no workbook is attached".
- A file read counts against the SDK call budget. A failed read raises; let it fail visibly rather than render an empty widget.

## Raw CRM reads

To read a connected CRM's native objects and fields directly, without Metal's field mapping, use the mapping-free CRM methods. Each org's CRM is different, so discover the schema at run time and never hard-code an object ID, field `apiName` or choice value from an example.

1. Find the integration and its service type with `metal.get_integrations_by_service()`. The service decides which query method to use.
2. List the native objects with `metal.list_crm_objects(integration_id)`. Match on `name`.
3. Read the fields with `metal.describe_crm_object(integration_id, object_name)`. Use each field's `apiName` in filters, projections and when reading rows.
4. For a field with `hasChoices: true`, list its values with `metal.list_crm_field_choices(integration_id, field["id"])`. Never sample rows to discover values; that misses values with no records, which a breakdown must still show.
5. Query with the provider's method, such as `metal.query_dealcloud` or `metal.query_salesforce`. Read the query grammar with `get_sdk_method`.

- To count matches, send the filter with a limit of 1 and read the total the response reports. Don't load every row to count.
- A category breakdown is one count per choice value from step 4.
- `query_dealcloud` reports query errors as a result with an `error` key. Check `resp.get("error")` before reading results.
- A `dateRange` control sends plain `YYYY-MM-DD` values. For DealCloud, read the date-range rules in the `query_dealcloud` reference from `get_sdk_method` before you map them to a filter.
- Raw CRM rows carry no citations. Set `_citations = []` or pass an explicit `extra` source.
- Don't read integration or object IDs from `input["context"]`; discover them as above.

## SDK pitfalls

Each of these has shipped a broken or silently empty widget.

- **Schema-qualified field names.** In search and list bodies, every filter, sort and grouping field is the exact key from the method's field allowlist, such as `company_sector` or `deal_stage`, never the bare response attribute (`sector`, `stage`) and never a guessed key such as `deal_dealStage`. A wrong field fails with `field <x> is not allowed`.
- **Unwrap the response.** Most search and list methods return `{"data": [...], "metadata": {...}}`. Read rows with `resp.get("data") or []`; iterating the dict walks its string keys. Check each method's return shape with `get_sdk_method`.
- **No blanket `try`/`except`.** Never turn a failed read into an empty result. A widget that can't fetch its data must fail visibly; a swallowed error renders a blank widget that looks correct.
- **Closed SDK surface.** Don't invent methods. For a company's people, use `metal.get_people_by_company(company_id, ...)`.
- **`_output` must match the widget type.** See `references/chart-table-output.md` and `references/html-widgets.md`.
- **Escape every dynamic string** with `html.escape` before you put it in a fragment.
- **Dynamic org settings are data.** Status and stage labels differ per org; read them in the script on each render instead of copying them into the script.
- **Declare controls as `_parameters`.** A list assigned to `parameters` is ignored, and no controls appear.
