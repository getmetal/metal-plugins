---
name: dashboard-building
description: "Use when a user wants to create or change a Metal canvas dashboard or its widgets through the Metal MCP: choosing a widget type and data source, writing a Python script widget, chart or table _output, or an HTML widget fragment."
---

# Metal Dashboard Building

Before starting, read [Safety and confirmation](../../references/safety.md) and apply it throughout this task.

A Metal canvas dashboard is a free-standing dashboard of widgets. Each widget has a type, a data source, a title and a position on a 12-column grid. This skill says how to choose the type and data source, what to confirm with the user, and how to add and edit widgets with the Metal dashboard tools. The output contracts that the tool schemas do not carry are in the references.

## What the dashboard tools reach

- The tools work on canvas dashboards only. Deal, company, list, fund and other entity dashboards can't be read or changed here. Tell the user to edit those in Metal.
- A canvas widget renders without an entity. A script's `input["context"]` holds the org, user and dashboard IDs and no deal, company or list ID. Data is org-wide unless the widget narrows it.
- Find a dashboard with `list_dashboards`. Create one with `create_dashboard`; it is private to the creator unless `isPublic` is true. `update_dashboard` changes the name, description, automatic refresh and org-wide visibility, never the widgets.
- `get_dashboard` lists each widget's `widgetId`, `type`, `title`, `dataSourceType` and agent prompt. It does not return grid positions. Every widget write (`add_dashboard_widget`, `update_dashboard_widget`, `reorder_dashboard_widgets`, `remove_dashboard_widget`) returns the full layout with `col`, `row`, `width` and `height`.
- No tool previews a widget before it is saved, sets a widget's style mode, or changes a widget's type or data source in place. If the user asks for one of these, say so.

## Widget types and data sources

| `widgetType` | Allowed `dataSource` |
|---|---|
| `TABLE`, `BAR_CHART`, `LINE_CHART`, `PIE_CHART`, `COMPOSED_CHART` | `agent`, `script` |
| `HTML` | `agent`, `script`, `static` |
| `LIST` | `resourceList` only |

`get_dashboard` reports the stored data source as `dataSourceType`: `AGENT` is `agent`, `DASHBOARD_DATA` is `script`, `STATIC` is `static`, and `RESOURCE_LIST` is `resourceList`.

Make two separate choices on the merits: the form, then how the data resolves.

**Form.** Use a native chart or table type when the answer is a chart or a table, so the renderer owns axes, legend, sorting and number formatting. Use `HTML` for narrative, a mixed or bespoke layout, KPI tiles, clickable record lists and task or workflow buttons. Native types are first-class, not a fallback. A user who names a shape ("bar chart", "table") is asking for that native type.

**Data behavior.**

- `script`: a Python script reads Metal through the SDK and computes the output on every render. Use it when the data is reachable from the SDK and the transformation is deterministic: filter, join, aggregate, arithmetic. SDK data includes Metal records, financial metrics, enrichment observations, and a connected CRM's native objects through the mapping-free CRM methods. A missing CRM field mapping is not a reason to use `agent`.
- `agent`: at render time Metal's widget-data agent gathers the data, which can include web search and Metal records, reasons over it and fills the widget. Use it for open-web data (news, funding rounds, market data, competitor moves, filings) and for judgment (rank by a fuzzy criterion, classify, summarize, explain). A script has no web access. An agent widget can also drive a native chart or table, for example a ranked "most at risk" table.
- `resourceList` with `LIST`: shows one existing Metal list as-is, with its own columns, paging and interactions. Nothing is computed. If the user wants the list filtered, aggregated, combined or shown with other columns, use a script `TABLE` that reads the list's entries instead.
- `static`: an HTML render script that runs asynchronously; the widget serves its last rendered output, and `refresh_dashboard_widget` starts a new render. It has no data controls. Prefer `script` unless the user asks for a static widget.

You author the structure. Don't refuse an agent widget because you can't reach the web now, don't ship a one-time snapshot instead, and never invent data to fill a widget.

## Confirm before adding

A wrong guess ships a broken widget. Before `add_dashboard_widget`, every item below must be confirmed. Before an edit, confirm each item the change touches. Ask about all unfilled items in one message; don't fill some silently.

1. **The data and its exact key.** "Revenue" can mean revenue, ARR, net revenue or growth; "deals" can mean all deals, active deals or the user's deals. For a metric or observation, check the key against the valid key lists that `get_sdk_method` returns for `get_metric_series` and `get_observation`. A wrong key returns nothing and raises no error.
2. **Data behavior.** Unless the user already chose, ask: "Should this widget show exact, reproducible data using fixed filters and calculations, or use AI to research, interpret, rank or summarize the data?" Recommend one and say why, then wait for a direct answer.
3. **Form.** Which chart type, a table, an HTML layout, or a `LIST`.
4. **Title and placement.** Default to the next free row when the user doesn't care.

Rules for the behavior question:

- A precise filter ("active deals by stage") supports a recommendation for exact data but does not confirm it. An open-web or judgment request ("recent news", "rank risky deals") supports a recommendation for AI but does not confirm it.
- "Go", "ship it", silence or an unrelated reply is not an answer to the behavior question. Never say that silence will accept your recommendation.
- Skip the question when the user already stated the behavior ("make it exact", "use AI research", "no AI") or asked to show an existing list as-is.
- Talk to the user about exact data and AI-assisted data, not `script` and `agent`, unless they ask for implementation details.
- Don't read business data to decide the form, filters or labels before the behavior is confirmed. Reading SDK method documentation with `list_sdk_methods` and `get_sdk_method` is fine at any time.
- For an existing widget, never change the data source without the user's explicit consent. When the current source can't do what the user asks, explain why and ask before you remove and re-add it.

## Add a widget

1. Get the `dashboardId` from `list_dashboards` or `create_dashboard`. Call `get_dashboard` and check that a similar widget does not already exist.
2. Confirm the items above.
3. Author the widget for its data source:
   - **script:** write the script as `references/script-widgets.md` describes. Its `_output` follows `references/chart-table-output.md` for a chart or table, or `references/html-widgets.md` for `HTML`. Find SDK methods with `list_sdk_methods` and confirm each request and response shape with `get_sdk_method` before you use it.
   - **agent chart or table:** write a `prompt` that says what to fetch, how to filter, rank or compute it, which columns or series to show, the units, and what to show when nothing matches.
   - **agent HTML:** write the `prompt` and also pass `widgetCode`, a skeleton fragment with empty states and no real data (see `references/html-widgets.md`). The server validates it and stores it as the widget's approved template; the render-time agent keeps that structure and fills in the data. Without `widgetCode` there is no template to keep.
   - **LIST:** find the list with `list_lists` (filter by `resourceType`) and confirm it with `get_list`. Ask the user when several lists match. Use the ID from `get_list` for the list the user confirmed.
   - **static:** write a render script that assigns `_output = {"widgetCode": "<fragment>"}` (see `references/html-widgets.md`).
4. Call `add_dashboard_widget` with `dashboardId`, `title`, `widgetType`, `dataSource` and the field for that source: `script`, `prompt` (plus `widgetCode` for agent HTML), or `resourceListId`. Omit `col` and `row` to place it on the next free row. The default size is 6 by 4 cells, or 12 by 6 for `LIST`.
5. For a `static` widget, call `refresh_dashboard_widget` so it renders.
6. Check the result with `get_dashboard_widget` (see below).
7. Tell the user in one sentence what you added, and which data controls you wired up, if any.

### What the server checks when you save

- **script:** the server runs the script once before it saves. A script that raises, sets no `_output`, or returns an `_output` that fails the check for its widget type is refused with the error and its details (error type, traceback, line), and nothing is saved. If verification is unavailable, report the gap and get the user's decision before persisting an unverified change.
- **agent HTML:** `widgetCode` is validated against the fragment contract on add and update. A fragment wrapped in `<html>` or `<body>` is unwrapped first.
- **static:** author the fragment to the same HTML contract and verify its output after refreshing. Until the first render finishes, the widget shows a generating placeholder.
- A successful save does not mean the data is right.

### Check the widget after saving

`get_dashboard_widget` resolves the widget and returns its `data`. It is the only way to see a widget's output through the MCP.

- Compare the values with what the user expects. An empty result is correct only when the filter should match nothing.
- `data.meta.status` of `generating` means the render is still running. Check again later.
- `data.meta.status` of `error` means the widget failed when it rendered. The MCP does not return the traceback. For a script widget, send the current script unchanged with `update_dashboard_widget`: a failing script is refused with the error details and nothing changes. A script that passes this check saves again unchanged.
- If you can't verify the data, say so. Don't claim a widget works because it saved.

## Edit a widget

1. Call `get_dashboard` to get the exact `widgetId`, `type` and `dataSourceType`.
2. Read the current source with `get_dashboard_widget_source`. It returns `script` for a script or static widget and `widgetCode` for an agent HTML widget that has a stored template. An agent chart or table has no source beyond its prompt, which `get_dashboard` shows. A `LIST` widget has no source.
3. Confirm each item the change touches.
4. Edit the source you just read. Don't rewrite it from memory or rebuild it from rendered output. `script` replaces the whole script, so send the complete edited script.
5. Call `update_dashboard_widget` with only the fields that change:

| Data source | Content fields | Notes |
|---|---|---|
| agent chart or table | `prompt` | |
| agent HTML | `prompt`, `widgetCode` | Changing `prompt` without `widgetCode` clears the stored template. To keep the design, pass both in one call. |
| script | `script` | Checked before save, as for add. |
| static | `script` | Follow the HTML contract. Call `refresh_dashboard_widget` afterwards. |
| resourceList | none | Title and geometry only. To show a different list, remove and re-add. |

Every widget accepts `title`, `col`, `row`, `width` and `height`. `prompt` and `script` can't be sent together. An empty string leaves a field unchanged, so a field can't be cleared.

6. Check the widget with `get_dashboard_widget`, as after an add.
7. Tell the user in one sentence what changed.

To change a widget's type or data source, remove it with `remove_dashboard_widget` and add a new one through the full add flow. When the user already confirmed the new data source, use it without reopening that choice. Call `remove_dashboard_widget` only when the user asks for the removal or agrees to it; removing a system widget is permanent.

When the user asks for a visual change only, change presentation and nothing else. Keep data calls, filters, calculations, sorting, limits, copy, links, `data-metal-*` attributes, `_citations` and `_parameters` as they are.

## Layout and dashboard settings

- Keep widgets inside the 12-column grid and avoid overlaps. Take current positions from the layout that the last widget write returned.
- Move or resize several widgets in one call with `reorder_dashboard_widgets`. Widgets you don't list keep their positions.
- Every layout write checks the version it read. If another edit landed in between, the write fails; call `get_dashboard` and try again.
- Make only the change the user asked for. Don't reorganize the dashboard on your own.

## References

- `references/chart-table-output.md`: the `_output` shapes for `BAR_CHART`, `LINE_CHART`, `PIE_CHART`, `COMPOSED_CHART` and `TABLE`, including entity tables.
- `references/script-widgets.md`: the script contract (`_output`, `_citations`, `_parameters`), data controls, the restricted runtime and its limits, finding SDK methods, valid keys, reading source files, raw CRM reads, and SDK pitfalls.
- `references/html-widgets.md`: the HTML fragment contract, approved libraries, record links, task and workflow buttons, workflow file previews, fitting a grid cell, and the theme variables a widget can use.

The `metal-sdk-scripts` skill covers the Metal SDK and `run_metal_sdk_query` in general. Widget scripts run in a different runtime with different limits; `references/script-widgets.md` lists the differences.
