# HTML widgets

An `HTML` widget's `widgetCode` is an HTML or SVG fragment that Metal renders in a sandboxed iframe. This file is the fragment contract. It applies to all three HTML data sources:

- **script:** the script bakes every value into the fragment and assigns `_output = {"widgetCode": fragment}` each render. Don't pass `widgetCode` to `add_dashboard_widget` or `update_dashboard_widget` for a script widget; the server rejects it.
- **agent:** you pass a skeleton `widgetCode` with the `prompt`. It becomes the approved template, and on each render the widget-data agent fills it with real data. Write the layout with empty states. Don't put real data in it, don't invent values, and leave out record links and action buttons (see below).
- **static:** the render script assigns `_output = {"widgetCode": fragment}`. Nothing validates a static fragment, so it must meet this contract on its own.

Use a native chart or table type instead when the answer is a chart or a table (see `references/chart-table-output.md`).

## The fragment contract

The server checks these rules on agent `widgetCode` at add and update, and on script output at save and render.

- **Fragment only.** No `<!doctype>`, `<html>`, `<head>`, `<body>` or `<meta>`, and no `<iframe>`, `<object>`, `<embed>`, `<form>` or `<base>`. Emit one root element, such as `<section>`, with an inline `<style>` and the markup.
- **At most 2,000,000 bytes.** Include only the rows, series and fields the widget shows, never whole fetched records.
- **No live data.** The fragment runs offline. These names fail the check wherever they appear in the fragment, including prose and comments: `window.parent`, `window.top`, `parent.` or `top.` followed by `postMessage`, `location`, `frames`, `opener`, `document` or `window`, `fetch(`, `XMLHttpRequest`, `WebSocket`, `EventSource`, `localStorage`, `sessionStorage`, `indexedDB`.
- **Approved libraries only.** `<script src>`, `<link href>`, `<img src>`, SVG `<image href>`, `srcset`, CSS `@import` and CSS `url(...)` may load only from these prefixes:
  - `https://cdn.jsdelivr.net/npm/chart.js` (Chart.js: charts)
  - `https://cdn.jsdelivr.net/npm/gridjs/` (Grid.js: dense or filterable tables)
  - `https://cdn.jsdelivr.net/npm/mermaid/` (Mermaid: declarative diagrams)
  - `https://cdn.jsdelivr.net/npm/d3@7`
  - `https://cdn.jsdelivr.net/npm/topojson-client@3`
  - `https://cdn.jsdelivr.net/npm/world-atlas@`
  - `https://cdn.jsdelivr.net/npm/us-atlas@`

  Images may also use a `data:` URI; scripts and stylesheets may not. Default to plain HTML and inline SVG; use a library only when it clearly helps.
- **Script widgets only:** the server also checks the syntax of each inline `<script>` block.
- **Escape dynamic text.** Run `html.escape(value)` (and `html.escape(value, quote=True)` in attributes) on every string from an API or a user before you put it in the fragment. An unescaped `&` or `<` breaks the render or injects markup.
- **Close every tag.** A truncated tag renders as garbage or swallows the markup after it.
- **Don't use `position: fixed`.** Use the grid-cell pattern below.

## Links

Two kinds of link exist, and they don't mix.

- **Outbound link:** a plain `<a href="https://...">`. The host opens `https:` and `mailto:` links in a new tab. The check rejects `http://` and protocol-relative `//` links. A `javascript:` or `data:` link, or an app path such as `/deals/123`, is dead. A `#fragment` link jumps inside the widget.
- **Record link:** for a Metal record, use the `data-metal-*` attributes below. An `href` can't reach an app page from inside the iframe.

In a script or static widget, put real absolute URLs from a tool or SDK result in `href`. If you have no URL, show the source as plain text, not a placeholder link.

## Record links

Whenever a script or static widget shows a specific deal, company, workflow run, document, activity, task, fund, limited partner, fundraising process or person, make it clickable by default. Skip it only for values that are not one record: totals, aggregates, groupings and decorative text.

Put the attributes on a `<button type="button">` or a real `<a href>` with visible text or an `aria-label`, so keyboard users can activate it. A bare `<div>`, `<li>` or table row can't be activated from the keyboard. Don't write navigation yourself with `onclick`, `window.location` or `postMessage`.

- `data-metal-resource-type` (required): one of `deal`, `company`, `workflow`, `data_entity`, `fund`, `limited_partner`, `fundraising_process`, `person`, `activity`, `task`, or `workflow_file` (see Workflow file previews).
- `data-metal-resource-id` (required except for `workflow_file`): the record's 24-character ID. For `workflow` this is the run ID.
- `data-metal-workflow-id` (required for `workflow`): the workflow definition ID, the run's parent.
- `data-metal-page` (optional, `data_entity` only): the 1-based page to open in the previewer.
- `data-metal-title` (optional): the previewer heading for `data_entity` or `workflow_file`. It is not an accessible name.

`data_entity` opens the document previewer. `deal`, `company` and `workflow` open that record. `fund`, `limited_partner`, `fundraising_process`, `person`, `activity` and `task` open the record's detail page. Clicks do nothing only while someone is rearranging the dashboard layout.

Get each ID from a tool or SDK result; never use a placeholder. You can't test the click, so check the IDs before you save:

- For `data_entity`, use the file's ID: the `id` from `metal.get_data_entities_by_id`, or the `dataEntity` field of a `search_documents_documents_search` result. That result's own `id` is an excerpt ID and does not open a preview.
- For `fund`, `limited_partner`, `fundraising_process` and `person`, use the record's own `id` from the matching get or search method.
- For `activity`, use the activity's `id`; for `task`, the task's `id`. Never put a task ID under `activity` or the reverse; they are different records.

```python
row = (
    '<li><button type="button" class="record-link" '
    'data-metal-resource-type="deal" '
    f'data-metal-resource-id="{html.escape(deal["id"], quote=True)}">'
    f'{html.escape(deal.get("name") or "Untitled deal")}</button></li>'
)
```

Leave record links, task actions, workflow actions and file previews out of agent templates. The template is a skeleton, so the IDs would not be real.

## Task row actions

A script or static widget can let the viewer assign, complete or cancel a task in place. Metal shows the assignee picker and confirmation and makes the change; the widget only declares the button.

- `data-metal-action` (required): `task.assign`, `task.complete` or `task.cancel`. Any other value is ignored.
- `data-metal-task-id`: the task's ID. It may be omitted when the button sits inside an element with `data-metal-resource-type="task"` and `data-metal-resource-id`.

Put these on their own `<button type="button">`, not on the element that carries a record link; the action wins over the link. Don't write the change in widget JavaScript.

```html
<button type="button" data-metal-action="task.complete" data-metal-task-id="67b2c3d4e5f6a1b2c3d4e5f6">Complete</button>
```

When the user wants task management on a dashboard, use a script HTML widget, not an agent template.

## Workflow actions

A button with `data-metal-action="workflow.run"` and `data-metal-workflow-id` (the workflow definition ID, not a run ID) opens Metal's run dialog for that workflow. The viewer reviews the inputs and submits there; clicking the button does not start a run. Don't add input payloads or API calls.

```html
<button type="button" data-metal-action="workflow.run" data-metal-workflow-id="67c83a5b1d4e7f1a2b3c4d5e">Run analysis</button>
```

When you add a workflow action, check whether the dashboard already shows recent runs of that workflow. If not, offer once to add a script table of them. Don't promise that new runs appear immediately; the widget updates on the dashboard's refresh.

## Workflow file previews

To preview a file that a workflow run produced, use `data-metal-resource-type="workflow_file"` on a `<button type="button">` with visible text:

- `data-metal-run-id`: the owning run's 24-character ID.
- Exactly one selector, never both, not even with an empty value: `data-metal-output-id` with a registered file output's 24-character `id` (an output with `type: "file"`), or `data-metal-artifact-ref` with a recorded document or artifact's exact `bucket:key`.
- `data-metal-title` (optional): the preview heading.

Find them in `metal.get_workflow_run`: the run's `id`, file `outputs` with `id` and `type: "file"`, and `documents` or `artifacts` with `bucket` and `key`. Step artifacts can also sit in `steps[].artifacts`, `steps[].output.artifacts` and branch `children`. Copy identities exactly; don't trim, decode or normalize them.

Metal resolves the file as the viewer on click, so a viewer without access to the run can't open it. Never embed a signed URL. There is no generic file preview by URL or name; if you have only a URL or a filename, show plain text instead of a button. Don't combine a preview button with a task or workflow action.

## Fitting the grid cell

A dashboard widget renders into a fixed-size cell and does not grow with its content. Content taller than the cell must scroll inside the widget, with headers pinned. `height: 100%` and `100vh` on the root don't work here. Use this pattern:

```html
<section id="root">
  <style>
    #root { position: absolute; inset: 0; display: flex; flex-direction: column; color: var(--metal-widget-text); }
    #root h3 { margin: 0; font-size: inherit; }
    #root .widget-header { flex: 0 0 auto; padding: 12px 16px; border-bottom: 1px solid var(--metal-widget-border); }
    #root .widget-body { flex: 1 1 0; min-height: 0; overflow-y: auto; overflow-x: hidden; margin: 0; padding: 8px 16px; list-style: none; }
    #root .muted { color: var(--metal-widget-muted-text); }
  </style>
  <header class="widget-header"><h3>Recent activity</h3></header>
  <ol class="widget-body"><li class="muted">No recent activity</li></ol>
</section>
```

`position: absolute; inset: 0` fills the cell. `flex: 0 0 auto` keeps the header at its natural height. `flex: 1 1 0; min-height: 0; overflow-y: auto` lets the body take the rest and scroll; without `min-height: 0` the body overflows the cell instead. A single chart or tile uses the same root with one `flex: 1 1 0; min-height: 0` child. For Chart.js, set `responsive: true` and `maintainAspectRatio: false`, and put the `<canvas>` in that child.

## Theme variables

Which CSS variables exist depends on the widget's style mode. The Metal MCP can't set a style mode, so every HTML widget added through it has none.

**No style mode (every widget added through the MCP).** The frame defines only these variables, with light and dark values:

`--metal-widget-surface`, `--metal-widget-panel`, `--metal-widget-muted-surface`, `--metal-widget-text`, `--metal-widget-muted-text`, `--metal-widget-subtle-text`, `--metal-widget-border`, `--metal-widget-border-strong`, `--metal-widget-primary`, `--metal-widget-primary-text`.

- Use these for text, surfaces, borders and accents so the widget follows light and dark mode. A literal color does not change with the theme.
- `--ds-*` tokens and the `metal.tokens` JavaScript helper do not exist in this frame. A `var(--ds-...)` resolves to nothing, and a call to `metal.tokens` throws an error and can stop the widget's script.
- Chart.js labels don't inherit CSS. Read a variable in JavaScript with `getComputedStyle(document.documentElement).getPropertyValue("--metal-widget-muted-text")` and pass it to the chart's tick, legend, grid and tooltip colors. There is no categorical palette variable. For a multi-series chart, consider a native chart type, which colors its series itself.
- For an agent `widgetCode`, `add_dashboard_widget` and `update_dashboard_widget` return a warning for a `--metal-*` or `--ds-*` name that neither set defines. The warning does not catch a valid `--ds-*` name in a widget with no style mode, so check that yourself.

**An existing widget with a style mode.** A widget created in Metal's editor can have style mode `system` or `custom`, and an MCP edit keeps it. `get_dashboard_widget` returns it as `data.html.styleMode`. Such a frame defines `--ds-*` tokens and the `metal.tokens` helper instead of the `--metal-widget-*` set. When you edit one, keep using the `--ds-*` names it already uses, keep its colors, type, borders and radii on those tokens, and don't add literal colors, font names, pixel font sizes or numeric font weights.

When you edit any existing widget, read `data.html.styleMode` first and use the variables its frame defines. Don't move a widget from one set to the other as a side effect of another change.

## Don'ts

- Don't emit a full document or a disallowed tag.
- Don't load from a URL outside the approved prefixes, and don't use the blocked browser names anywhere in the fragment.
- Don't link with `http://` or `//`, and don't link to app paths; use record links.
- Don't write navigation or mutations in widget JavaScript; declare `data-metal-*` attributes.
- Don't put an unescaped dynamic string in the markup.
- Don't return a `{columns, rows}` table or a chart object from an `HTML` widget.
- Don't assume data can be fetched when the widget is viewed; bake it in.
