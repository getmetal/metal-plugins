# Script Patterns For run_metal_sdk_query

Each pattern is a complete script. Confirm every method, filter field and response key with `get_sdk_method` before you adapt one.

## Page a search by hand and aggregate

`paginate` can't send a request body, so page a `search_*` method yourself. This script counts deals by stage for deals closing on or after a date, and stops at a page budget it sets.

```python
# input: {"since": "2026-01-01T00:00:00Z", "maxPages": 10}
max_pages = input.get("maxPages", 10)
counts = {}
pages_read = 0
total_pages = 0
complete = False
while pages_read < max_pages:
    result = metal.search_deals(
        query={"page": pages_read + 1, "limit": 100},
        body={"filters": {"and": [{"field": "deal_closeDate", "operator": "gte", "value": input["since"]}]}},
    )
    pages_read += 1
    for deal in result["data"]:
        stage = deal.get("stage") or "UNSET"
        counts[stage] = counts.get(stage, 0) + 1
    total_pages = result["metadata"]["totalPages"]
    if pages_read >= total_pages:
        complete = True
        break

_output = {"countsByStage": counts, "pagesRead": pages_read, "totalPages": total_pages, "complete": complete}
```

- Read rows from `result["data"]` and totals from `result["metadata"]`; the search envelope is not unwrapped.
- Return `complete` so you can tell the user when the page budget cut the scan short.

## Read records by ID in one batch

```python
# input: {"dealIds": ["...", "..."]}  (1 to 20 IDs)
deals = metal.batch([{"name": "get_deal", "pathArgs": [deal_id]} for deal_id in input["dealIds"]])
_output = [{"id": d.get("id"), "name": d.get("name"), "stage": d.get("stage")} for d in deals]
_citations = metal.citations.collect(*deals)
```

- One missing ID fails the whole batch. Use this only when every ID came from a Metal response in this conversation.

## Handle missing records one by one

When some IDs may be stale or out of the user's access, call each one and keep going:

```python
# input: {"dealIds": [...]}  (at most 20 IDs; each is one call)
found = []
missing = []
for deal_id in input["dealIds"]:
    try:
        deal = metal.get_deal(deal_id)
    except Exception as exc:
        if hasattr(exc, "status") and exc.status == 404:
            missing.append(deal_id)
            continue
        raise
    found.append({"id": deal["id"], "name": deal.get("name")})

_output = {"found": found, "missing": missing}
```

- Report the missing IDs to the user as not found. Re-raise any other error; the run then fails.
