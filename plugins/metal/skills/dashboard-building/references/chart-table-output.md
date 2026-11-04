# Chart and table `_output`

A script widget of type `BAR_CHART`, `LINE_CHART`, `PIE_CHART`, `COMPOSED_CHART` or `TABLE` assigns one of the shapes below to `_output`. The server checks `_output` against the widget's type, not against anything the script declares, and refuses to save a script whose output fails the check. An agent widget of these types gets the same shape from the render-time agent, so its `prompt` only needs to describe the data.

An `HTML` widget needs `_output = {"widgetCode": "<fragment>"}` instead (see `references/html-widgets.md`). A `{columns, rows}` table or a chart object returned from an `HTML` widget is rejected, and so is a fragment returned from a chart or table widget.

## Charts

```python
_output = {
    "chartType": "bar",
    "data": [
        {"name": "Q1", "revenue": 1200000, "ebitda": 180000},
        {"name": "Q2", "revenue": 1340000, "ebitda": 220000},
    ],
    "xAxis": {"dataKey": "name", "label": "Quarter"},
    "series": [
        {"type": "bar", "dataKey": "revenue", "label": "Revenue"},
        {"type": "bar", "dataKey": "ebitda", "label": "EBITDA"},
    ],
}
```

- `chartType`, `data` and `series` are required.
- `chartType` must match the widget type: `bar` for `BAR_CHART`, `line` for `LINE_CHART`, `pie` for `PIE_CHART`, `composed` for `COMPOSED_CHART`.
- `data` is a list of row objects, one per category or slice. Give numeric values as numbers, not strings.
- Each `series` item needs `type` and `dataKey`, and may have `label`, `color`, `axisId`, `stackId` and `rendererProps`. `type` must be `bar` on a bar chart, `line` on a line chart, `pie` on a pie chart, and `bar` or `line` on a composed chart. Point each `dataKey` at a key that every `data` row has.
- `xAxis` may have `dataKey` and `label`. `dataKey` names the category key on each row. Without it the renderer reads each row's `label` key. A pie chart does not use `xAxis`.
- The only top-level keys allowed are `chartType`, `data`, `xAxis`, `yAxes` and `series`, plus `nameKey`, `showLegend`, `innerRadius` and `outerRadius` on a pie chart. Any other key fails the check. For example, `yAxisId` is not a valid top-level key; use `yAxes` and `axisId`.
- Charts have no percent or currency formatting on ticks or tooltips. Give a percentage as a whole number (`18` for 18%) and put the unit in the axis or series label. Y-axis ticks at or above 1,000,000 are shown in compact form, such as `1.2M`.

### Pie charts

Set `chartType` to `pie`, give each row a `name` (the slice label), and point the series `dataKey` at the numeric value. Optional keys: `nameKey` to read the slice label from another key, `showLegend` (default true), `innerRadius` (default 36, a donut; 0 for a full pie) and `outerRadius`.

### Composed charts with two y-axes

A `COMPOSED_CHART` can show an absolute value on one axis and a rate on the other.

- Give each series a distinct `axisId`, such as `left` and `right`. The renderer creates the axes.
- To label the axes, also add a top-level `yAxes` list of `{id, label}` items whose `id` matches the series `axisId`. Items may also have `dataKey` and `rendererProps`.
- For a single axis, omit `axisId` on every series and omit `yAxes`.

```python
_output = {
    "chartType": "composed",
    "data": [
        {"period": "FY22", "revenue": 1100000, "margin": 16},
        {"period": "FY23", "revenue": 1240000, "margin": 18},
        {"period": "FY24", "revenue": 1500000, "margin": 21},
    ],
    "xAxis": {"dataKey": "period", "label": "Fiscal Year"},
    "yAxes": [
        {"id": "left", "label": "Revenue ($)"},
        {"id": "right", "label": "EBITDA Margin (%)"},
    ],
    "series": [
        {"type": "bar", "dataKey": "revenue", "label": "Revenue", "axisId": "left"},
        {"type": "line", "dataKey": "margin", "label": "EBITDA Margin", "axisId": "right"},
    ],
}
```

## Tables

```python
_output = {
    "columns": [
        {"key": "year", "label": "Year", "type": "string", "sortable": True},
        {"key": "revenue", "label": "Revenue", "type": "currency"},
        {"key": "ebitdaMargin", "label": "EBITDA Margin", "type": "percent"},
    ],
    "rows": [
        {"year": "2024", "revenue": 142000000, "ebitdaMargin": 0.197},
    ],
}
```

- `columns` and `rows` are required. The only other top-level key allowed is `entityType`.
- `columns` must not be empty. Each column needs a non-empty `key` and `label`, and may have `type` and `sortable`.
- `type` is one of `string`, `number`, `currency`, `percent`, `date`, `badge`, `link`, `boolean`.
- Every key on a row must be a declared column key. The only exceptions are the entity keys listed under Entity tables. An undeclared key fails the check.
- A cell value is a string, number, boolean or `None`. An object is allowed only in a `link` column, as `{"label": "...", "href": "..."}`. A list is not allowed in an ordinary cell.
- `currency` values are raw units: `15000` shows as $15K. For millions, use `type: "number"`, a label such as `Revenue ($M)`, and a pre-scaled number. Don't send `0.015` with a `($M)` label.
- `percent` values are fractions: `0.197` shows as 19.7%. A value above 1 or below -1 is read as a whole-number percent, so `19.7` also shows as 19.7%. Send a rate beyond 100% as a whole number (`150` for 150%); the fraction `1.5` shows as 1.5%.
- A `link` cell opens in a new tab. Its `href` can be an app path such as `/companies/<id>`, or an `https:`, `http:` or `mailto:` URL.

### Entity tables

Set `entityType` when each row is one Metal record and you have its real ID. The renderer then draws clickable badges, owner avatars and file previews. `entityType` is one of `company`, `data_entity`, `deal`, `project`, `expert_call`, `workflow_run`.

Use a plain table (no `entityType`) when rows are not records (years, periods, aggregates), or when you need sorting or `currency`, `percent`, `date` or `link` formatting on arbitrary columns. In an entity table, only the entity column keys below render specially. Money keys (`revenue`, `ebitda`, `adjustedEbitda`, `enterpriseValue`, `ev`, `committedAmount`, `softCircledAmount`, `targetCommitment`) render as currency on `company` and `deal` tables. Every other column renders as plain text: its `type` is ignored, an object shows as `[object Object]`, and `sortable` does nothing.

Two kinds of keys drive the entity cells:

- **Hidden row keys:** put them on every row and don't declare them as columns. The renderer reads them to build another cell; for example, the company `name` badge reads `id`.
- **Entity column keys:** declare a column with exactly this key. The cell renders only when the column exists.

| `entityType` | Hidden row keys | Entity column keys |
|---|---|---|
| `company` | `id` | `name` (company badge from `id`), `tags`, money keys |
| `deal` | `id`, `companyId`, `statusConfigId` or `externalStatus`, `stageConfigId` or `externalStage` | `name` (deal link from `id`), `company` (company badge from `companyId`), `status`, `stage`, `owners`, `assignees` or `sharedWith`, `similarityReason`, `updatedAt`, `size`, money keys |
| `project` | `id` | `name` (project link from `id`), `status`, `members`, `createdBy`, `createdAt`, `updatedAt` |
| `data_entity` | `id` | `name` (file preview from `id`), `documentType`, `documentDate`, `createdAt`, `updatedAt` |
| `expert_call` | `id`, `dataEntityId`, `intervieweeCompanyId` | `file` (file preview from `dataEntityId`), `company` (company badge from `intervieweeCompanyId`), `sentiment`, `callDate` |
| `workflow_run` | `id`, `workflowId` | `workflow` (run link from `workflowId` and `id`), `status`, `createdAt`, `completedAt` |

The check accepts these keys on a row without a declared column: `company`: `id`, `tags`; `deal`: `id`, `companyId`, `status`, `statusConfigId`, `externalStatus`, `stage`, `stageConfigId`, `externalStage`, `owners`, `assignees`, `sharedWith`, `similarityReason`; `project`: `id`, `members`, `createdBy`; `data_entity`: `id`; `expert_call`: `id`, `dataEntityId`, `intervieweeCompanyId`, `intervieweePersonId`, `intervieweeRole`, `matchReason`; `workflow_run`: `id`, `workflowId`. Of these, an entity column key such as `tags`, `status` or `owners` still shows only when you declare its column; without the column it disappears with no error.

- Every ID key is a flat ID string, not a nested object. For a `deal`, declare a `company` column and set the row's `companyId` from the company's `id`. A nested company object in a cell renders as an em dash and fails the check.
- Without `id` the label falls back to plain text that can't be clicked. If you don't have the record's real ID, don't set `entityType`; use a plain table with a `link` column (`{"label": name, "href": f"/companies/{id}"}`) instead.

Mistakes that pass the check but render wrong:

- Naming the label column `companyName` or `title` instead of the clickable key (`name`; `file` for `expert_call`; `workflow` for `workflow_run`).
- Declaring `id` as a column. It then prints the raw ID. Keep `id` on the rows and out of `columns`.
- Adding `link`, `currency` or `percent` columns, or `sortable`, to an entity table and expecting them to work.

```python
_output = {
    "columns": [
        {"key": "name", "label": "Name"},
        {"key": "sector", "label": "Sector"},
    ],
    "rows": [
        {"id": c["id"], "name": c.get("canonicalName") or "", "sector": sector}
        for c, sector in rows_with_sector
    ],
    "entityType": "company",
}
```

For a document or file table, read rows from `metal.search_documents_documents_search`. It returns one excerpt per matching page or section, with the parent file's ID in `dataEntity`. Deduplicate by `dataEntity` to get one row per file and use `dataEntity` as the row `id`; the result's own `id` is the excerpt's ID and does not open a preview. Confirm the response fields with `get_sdk_method` before you write the script.
