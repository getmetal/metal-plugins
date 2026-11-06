# Querying stored document tables

Use `list_document_tables` with `documentId` from document discovery. Copy the
selected `tableId`; a sheet title or position also works. When a large document
returns only identity and size for later tables, request that table explicitly
with `tableId` rather than assuming it has no columns or rows. Summary-only
documents may need the [original-file route](original-files.md) instead.

`query_document_table` takes `documentId`, `tableId`, optional `columns`,
`filters`, `sort`, `groupBy`, `aggregates`, `limit` and `offset`.

- Columns are case-insensitive header names, zero-based index strings or Excel
  letters. Use actual headers from the table, not names inferred from prose.
- Each filter is `{column, op, value? , values?}`. Filters are ANDed. Operators
  are `eq`, `ne`, `contains`, `in`, `gt`, `gte`, `lt`, `lte`, `between`, `empty`
  and `notEmpty`. Use `values` for `in` and `[low, high]` for inclusive
  `between`; use `value` for the other comparisons.
- Sort keys are `{column, desc?}`. Aggregates are `{fn, column?}`, where `fn`
  is `count`, `sum`, `avg`, `median`, `min` or `max`. `count` without a column
  counts rows. At most 20 filters, sort keys, group columns and aggregates each
  are accepted. Group results are bounded to 200 groups; report that limit
  when a complete group enumeration matters.
- Rows default to 50 per call, at most 500. Use `offset` while
  `pagination.hasMore` is true; `limit: 0` requests aggregates without rows.
  Aggregates cover matching rows, not just the returned row page.
- Numeric parsing removes currency symbols, separators, percent signs and
  trailing multiples. `12.5%` is parsed as `12.5`, not `0.125`; retain the
  source's units and do not apply list-cell percentage rules to it. Values that
  fail numeric/date parsing are skipped by those comparisons and aggregates;
  report the used/skipped counts when they affect the answer.
- Cite `document.sourceLink` with the table title and returned 1-based row
  numbers. A sampled profile or a truncated cell does not establish absence
  from the full source.
