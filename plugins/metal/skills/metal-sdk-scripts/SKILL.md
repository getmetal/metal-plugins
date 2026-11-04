---
name: metal-sdk-scripts
description: "Use when a Metal task needs a read-only Python script run through the Metal MCP's run_metal_sdk_query tool: joins, aggregations or bounded batch reads that would take many separate Metal tool calls. Covers method discovery, the script contract, limits, errors, pagination and batches."
---

# Metal SDK Scripts

`run_metal_sdk_query` runs a short Python script inside Metal. The script gets a `metal` object whose methods read the user's Metal data, and returns one compact JSON result. Use it to join, filter or aggregate data that would otherwise take many separate tool calls. This skill says when to use it, how to find methods, what the script may do, and how to stay inside its limits.

## When the tool is missing

`run_metal_sdk_query` exists only when the organization has programmatic queries turned on in its Metal settings and the connection's token carries the `read:programmatic` scope. `list_sdk_methods` and `get_sdk_method` can be present without it, because dashboard work also uses them.

If `run_metal_sdk_query` is not in your tool list:

- Do the task with the regular Metal tools when a reasonable number of calls covers it.
- Otherwise tell the user that programmatic queries are not available on their Metal connection.
- Don't work around it. Don't run SDK code in a dashboard widget, a workflow step or this client's own sandbox to get the same effect.

## When to use a script

- Prefer a dedicated Metal tool for a simple lookup, such as one company or one search.
- Use a script when the answer needs several dependent reads, a join across record types, or a count, sum or grouping over many records.
- Use a script when several independent reads can go in one `metal.batch` call instead of many tool calls.
- Return only the answer: the counts, the summary, the few rows the user asked for. Don't return raw collections.

## Find methods before you write

The method set is closed. A script can call only the methods `list_sdk_methods` returns.

1. Call `list_sdk_methods` with a `query`. The match is a case-insensitive substring of the method's name, signature, one-line description, HTTP method and path. Try a resource word such as `deal`, `company` or `observation`. Results come 20 per page by default, at most 50 with `pageSize`; page with `page` while `hasMore` is true.
2. Call `get_sdk_method` with the method `name` for every method you plan to call. Its `reference` gives the signature, which arguments go in `query=` and which in `body=`, the response envelope, enums and usage notes. Write field names from the reference, not from the method name.
3. If a method has no reference (`documented` is false), run a first script that returns one sample record in `_output`, then adapt to the real shape. Don't guess a response shape.

## The script contract

- Globals: `metal`, `input` (the `input` object you pass to the tool, or `{}`), and the modules `json`, `math` and `statistics`.
- Assign a JSON-serializable value to `_output`. A script that doesn't set it fails. `NaN` and infinity are not valid JSON, so guard divisions and empty `statistics` inputs.
- Optionally assign `_citations`, a list of objects. `metal.citations.collect(*responses, extra=None)` gathers the `citations` lists from SDK responses and removes duplicates.
- Pass record IDs and parameters through `input`, not by pasting them into the script.
- `print` output is discarded. Put anything you need to see in `_output`.

The runner rejects these before the script runs:

- Imports outside `collections`, `datetime`, `decimal`, `html`, `itertools`, `json`, `math`, `re`, `statistics` and `time`. Import `datetime` yourself; it is not pre-bound.
- Any attribute that starts with `_`, including dunders, and any name that starts with `_` other than `_`, `_output` and `_citations`. Name helper functions without a leading underscore.
- `.format()` and `.format_map()`. Use f-strings.

Builtins are limited. `open`, `getattr`, `setattr`, `type` and class definitions are not available. Use `isinstance` and `hasattr`, and plain functions, dicts and lists.

## Calling methods

```python
deal = metal.get_deal(input["dealId"])
companies = metal.list_companies(query={"page": 1, "limit": 50})
page = metal.search_deals(query={"page": 1, "limit": 100}, body={"filters": {"and": [{"field": "deal_closeDate", "operator": "gte", "value": "2026-01-01T00:00:00Z"}]}})
same_deal = metal.call_method("get_deal", input["dealId"])
```

- Path arguments are positional, in the order the reference gives. IDs are 24-character hex strings; pass them as `str`.
- `query=` holds query-string parameters. Keys whose value is `None` are dropped.
- `body=` holds the request body of a POST method, such as the `search_*` methods.
- A response that is exactly `{"data": ...}` is unwrapped to its `data`. A response with other top-level keys keeps its envelope. For example, `search_deals` returns `{"data": [...], "metadata": {...}}`: read rows from `result["data"]` and totals from `result["metadata"]`. Never iterate the envelope itself.
- `metal.available_methods()` lists the callable methods from inside a script.

## Limits

| Limit | Value | What happens |
|---|---|---|
| Script size | 64 KiB | The tool rejects the call |
| `input` size | 64 KiB, serialized | The tool rejects the call |
| SDK calls | 20 per run; a batch of N calls counts as N | The call that would pass 20 raises an error |
| SDK response bytes | 2 MiB, cumulative across all calls | The call that would pass it raises an error |
| One SDK call or batch | The runner waits at most 10 seconds for its response | The call fails |
| Output | 512 KiB for serialized `_output` plus `_citations` | The run fails with an output-size error |
| Script execution | 25 seconds | The run fails with a timeout error |
| Whole request | 60 seconds | The tool returns a timeout error |

These limits shape the script:

- Filter on the server. Pass filters in `body=` or `query=` rather than fetching a broad list and filtering in Python.
- Plan the call budget before you write a loop. Twenty calls is twenty pages, or one batch of twenty reads, not both.
- When a task needs more than one run can do, split it into several runs with narrower filters, or tell the user what the bound covered.

If the tool returns a capacity error with `retry_after`, wait that many seconds before you call it again.

## Pagination

Every page is one call against the 20-call budget.

- For a GET list method, `metal.paginate(name, *path_args, query=None, page_size=50, max_pages=100)` yields records across pages. It sends `page` and `limit`, follows a `nextCursor` when the response carries one, and stops when the response says there are no more pages or a page comes back short. Set `max_pages` to the calls you can spare, not the default. When `max_pages` runs out first, it raises an error.
- `paginate` sends no request body, so it can't page a POST `search_*` method. Page those yourself with `body=` and `query={"page": n, "limit": size}`, and stop at `metadata.totalPages` or the budget you set.
- Read each method's maximum `limit` from `get_sdk_method`. A larger page uses fewer calls but more of the 2 MiB response budget.
- Report whether the scan was complete. When the budget stopped it early, say how many records or pages it read and how many exist.

See `references/patterns.md` for a hand-paged search, a batch read and per-record error handling.

## Batches

`metal.batch` sends independent reads in one round trip:

```python
results = metal.batch([{"name": "get_deal", "pathArgs": [deal_id]} for deal_id in input["dealIds"]])
```

- Each item is a dict with `name` and, as needed, `pathArgs`, `query` and `body`.
- A batch holds 1 to 20 calls, and each call counts against the 20-call budget.
- Results come back unwrapped, one per call, in order.
- The calls run one after another, and the whole batch shares the 10-second wait. Keep slow calls out of large batches.
- The first failing call fails the whole batch, and the results of the calls before it are lost. Use a batch only for reads you expect to succeed. When some IDs may be missing, make separate calls and handle each error.
- Use a batch only for calls that don't depend on each other. Make dependent calls one after another.

## Errors

A failed SDK call raises an exception with a `.status` attribute (the HTTP status, or `None`) and a message that names the status. A runner limit, such as the call budget, raises the same kind of exception. Calling a method that doesn't exist raises an `AttributeError` that tells you to check the available methods.

The script can't import the SDK's error classes. Catch `Exception`, then read `exc.status` after `hasattr(exc, "status")`.

An uncaught SDK error reaches you with its message mainly when Metal rejected the request as invalid (status 400 or 422), the Metal SDK broker denied it, or the call budget, the response budget or the execution deadline stopped the call. Any other uncaught SDK error, such as a 404 or a call that passed the 10-second wait, reaches you only as a generic failure, without the status or message. Catch the errors you expect, such as a 404 for a missing record, and report them in `_output`:

```python
try:
    deal = metal.get_deal(deal_id)
except Exception as exc:
    if hasattr(exc, "status") and exc.status == 404:
        deal = None
    else:
        raise
```

Other script errors, such as a syntax error or a `KeyError`, come back with the message, an error `type` in `details`, and an `executionId`. Fix the script and run it again. Give the user the `executionId` only if you report a failure you can't fix.

## Reading the result

A successful call returns `data` (your `_output`), `citations` when the script set them, and `meta`. `meta.sdkCallCount` and `meta.sdkResponseBytes` show how much of the budget the run used; check them before you scale a script up.

## Connected MCP tools in a script

`query_mcp_tool` is an SDK method that calls a tool on an MCP server the user connected in Metal, such as a data warehouse. Use it in a script only when you need to combine that tool's results with Metal data or with other calls in one run. For a single call, use `call_connected_mcp_tool`.

```python
rows = metal.query_mcp_tool(input["connectionId"], "search_company", body={"arguments": {"domain": "acme.com"}})
```

- The path arguments are the connection ID and the tool name. Get both, and the tool's input schema, from `list_connected_mcp_tools`; its `connectionId` is the connection ID.
- Wrap the tool's arguments as `body={"arguments": {...}}`. A trailing positional argument is not sent.
- Metal calls only tools that the server marks read-only.
- The 10-second wait applies. A slow remote tool fails here even when `call_connected_mcp_tool` could finish it.
- The response holds the tool's `content` blocks. `isError` is present when the remote tool reported an error; report that content rather than retrying.

## Dashboard widget scripts are a different runtime

Dashboard widget scripts also get a `metal` object, and `list_sdk_methods` and `get_sdk_method` describe the methods for both. The runtime is different, so don't copy a script between them unchanged. The `dashboard-building` skill covers widget scripts.

| | `run_metal_sdk_query` | Widget script |
|---|---|---|
| `metal.<method>(...)`, `call_method`, `available_methods`, `citations.collect` | Yes | Yes |
| `paginate` | Yes | Only on some of Metal's widget backends; page by hand |
| `batch` with dicts | Yes | No |
| `get_file_bytes`, `open_file` | No | Yes |
| Error raised by a failed call | Exception with `.status` | `MetalAPIError` |
| SDK calls | 20 | 250 |
| Cumulative SDK responses | 2 MiB | 32 MiB |
| Output | 512 KiB | 4 MiB |
| Execution time | 25 seconds | 50 seconds |
| One SDK call | 10 seconds | 30 seconds |

`metal.stream_to_workspace` also exists in `run_metal_sdk_query`, but a script there can't open files and its sandbox is discarded after the run. Don't use it.

## Read-only and scoped to the user

- Every SDK method reads. No method creates, updates or deletes Metal data, and scripts have no filesystem, subprocess or network access. For a change, use the Metal tool that makes it, with the user's approval.
- A script runs as the signed-in user in their organization and sees only what that user can read.
- `metal.get_current_user()` and `metal.get_ctx_org()` return the user and organization the script runs as.
