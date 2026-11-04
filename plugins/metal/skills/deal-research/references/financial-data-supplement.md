# Reading a financial data supplement

A financial data supplement gives more detailed financial information than the primary statements: data books, fact books, KPI supplements, supporting schedules and backup financials, often with an earnings release or a financial statement. Most are Excel workbooks or PDFs with dense schedule tables. Weight it like the statements it supports (see SKILL.md): company-produced unless an auditor or independent party prepared it.

## How a data supplement differs

- Segment- and breakdown-heavy: supplements split revenue and profit by segment, product, geography or channel, often without a single income statement. The company-level figure is still the goal. Taking one segment as the company total is the most common error with this document type.
- Many periods: data books often show long quarterly histories with annual totals. Use the fiscal-year totals and the most recent LTM.
- KPI-dense: supplements include operating KPIs next to the financials.
- Spreadsheet-first: the best source is usually one or two summary tabs. Raw data tabs come last. When available, `list_document_tables` and `query_document_table` read the sheets as rows; cite the sheet name and row.

## Metrics to look for

- Revenue: consolidated total revenue, net revenue or sales.
- COGS.
- Gross profit and gross margin.
- EBITDA and Adjusted EBITDA, reported and adjusted, when stated.
- Net income.
- ARR, when stated.
- Capex, when a schedule shows it.
- Total debt or net debt, when a capitalization schedule shows it.
- Net working capital, when a schedule shows the total.

## Type-specific rules

- Consolidated over segment: take the Total, Consolidated, Companywide or All segments row. Report a single segment only when the user asks for it, or when no total exists; then name the segment.
- No total: do not add segments yourself unless the schedule has no total and you have every segment. If you add them, say so and list the parts.
- Scale per schedule: a revenue schedule and a capitalization schedule can use different scales.
- Annual over quarterly: use quarterly figures only when no annual total exists for the metric. An annual total is not LTM; an LTM column is not a fiscal year.
- Period labels: a completed fiscal year, or a column with no qualifier, is an actual. "Budget" or "B" is a budget; forward columns are forecasts; LTM and YTD columns need their end dates.
- Duplicates: when the same metric and year appear on several tabs, use the consolidated tab.

## Examples

`Q4_2024_DataBook.xlsx` has segment tabs ("North America", "EMEA") and a "Consolidated" tab, note "($ in millions)":

| ($M) Consolidated | FY2023 | FY2024 |
|---|---|---|
| Total revenue | 410.2 | 468.7 |
| Adjusted EBITDA | 92.4 | 108.5 |
| Adjusted EBITDA margin | 22.5% | 23.2% |

Report: "The Q4 2024 data book shows FY2024 total revenue of $468.7M and Adjusted EBITDA of $108.5M (23.2% margin) (Consolidated tab, $ in millions)." Do not use the North America or EMEA tabs for company totals.

A capitalization schedule on page 7, "($ in thousands)", with "Total debt 128,400" and "Net debt 96,200" for FY2024. Report both, labeled: total debt of $128.4M and net debt of $96.2M.

A revenue schedule on page 4, "($ in millions)", with Software 60.0 and Services 28.0 for FY2024 and no Total row. Report: "The supplement shows FY2024 revenue by segment only: Software $60.0M and Services $28.0M (p.4). Their sum, $88.0M, is my calculation; the supplement prints no total."
