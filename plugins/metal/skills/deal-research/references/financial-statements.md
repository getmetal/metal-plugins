# Reading financial statements

A financial statement is an official historical record of a company's performance and position: an income statement (P&L), a balance sheet and a cash flow statement, or an internal reporting package or periodic financials that bundles them. Most arrive as Excel workbooks or PDFs.

Audited statements are independent ground truth for historical results. Unaudited internal statements and monthly P&Ls are company-produced: corroborating, not independent (see the source table in SKILL.md). Check for an auditor's report before you call a statement audited.

## How a financial statement differs

- Reported, not adjusted: statements rarely show an Adjusted EBITDA bridge. Report EBITDA only when the statement has a line labeled EBITDA. Do not build EBITDA from operating income and D&A unless the user asks, and label it as your derivation if you do.
- Three statements in one document: the income statement gives revenue through net income; the balance sheet gives assets, liabilities and debt; the cash flow statement gives capex and operating cash flow. Read all three when the question needs them.
- Periodic columns: internal packages are often monthly or quarterly with a fiscal-year total. Use the annual or LTM total.
- Workbooks: many statements are workbooks with one tab per statement. Read the statement or summary tabs before raw general-ledger exports. When available, `list_document_tables` and `query_document_table` read the sheets as rows; cite the sheet name and row.

## Metrics to look for

- Revenue: the top line of the income statement.
- COGS: cost of goods sold, cost of revenue, cost of sales.
- Gross profit, when the statement shows it as a subtotal.
- Gross margin, only when stated.
- EBITDA, only when the statement labels an EBITDA line.
- Net income: the bottom line.
- Total debt from the balance sheet, or net debt when the statement reports it.
- Capex: capital expenditures, or purchases of property and equipment, in the investing section of the cash flow statement.
- Net working capital, when a schedule shows the total.
- ARR, only when the statement states it.

Do not report balance-sheet sub-lines (receivables, inventory) as one of these metrics unless the user asks for them.

## Type-specific rules

- Scale per statement: a balance sheet and an income statement in one package can use different scales. Read each statement's header or column note ("$ in thousands", "($000s)", "USD millions").
- Signs: statements show negatives in parentheses or with a trailing minus. Report costs as costs, and a parenthesized bottom line as a net loss.
- Period end: use the statement date to fix the period. A fiscal year that does not end on December 31 keeps its stated year-end.
- Period labels: a completed fiscal year, or a past column with no qualifier, is an actual. "Budget" or "B" is a budget. Forward columns are forecasts. A trailing-twelve-months column is LTM; a year-to-date column is YTD; give their end dates.
- Monthly only: when a statement has only monthly columns, say that it presents no annual total. Do not add the months unless asked.
- Source preference: revenue, EBITDA and net income from the income statement; debt from the balance sheet; capex from the cash flow statement. Use a footnote or commentary figure only when no statement shows it.
- Consolidated over entity: take the consolidated total, not an individual entity or segment.

## Examples

An "Income Statement" sheet in `2024_Financials.xlsx`, note "($ in thousands)":

| (USD thousands) | FY2022 | FY2023 | FY2024 |
|---|---|---|---|
| Revenue | 42,100 | 48,900 | 55,400 |
| Cost of sales | (25,260) | (28,400) | (31,600) |
| Gross profit | 16,840 | 20,500 | 23,800 |
| Net income | 3,210 | 4,780 | 5,950 |

Report: "The FY2024 income statement shows revenue of $55.4M, gross profit of $23.8M and net income of $5.95M (2024_Financials.xlsx, Income Statement sheet, $ in thousands)." Cost of sales is a cost of $31.6M; the parentheses mark it as a deduction.

A PDF reporting package with a balance sheet on page 3 ("$ in millions") showing "Total debt 64.2" for FY2024, and a cash flow statement on page 4 showing "Purchases of property and equipment (12.7)". Report total debt of $64.2M (p.3) and FY2024 capex of $12.7M (p.4).

A one-page income statement, header "($ in thousands)", with a FY2023 bottom line of "Net loss (1,420)". Report a FY2023 net loss of $1.42M.
