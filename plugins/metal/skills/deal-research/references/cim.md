# Reading a CIM

A Confidential Information Memorandum (CIM) or Confidential Information Presentation (CIP) is the seller's marketing book, written by the sell-side banker with management. The two names mean the same thing. Most CIMs are PDFs; some are PowerPoint decks or PDFs exported from slides. Every figure in it is a seller claim (see the source table in SKILL.md). A management presentation follows the same rules.

## Metrics to look for

- Revenue: total revenue, net revenue, sales.
- EBITDA: reported EBITDA.
- Adjusted EBITDA: Adj. EBITDA, Pro Forma EBITDA, Normalized EBITDA. The add-backs are seller-defined.
- Gross profit, in currency.
- Gross margin, a percentage.
- Net income: net income, net earnings, net profit.
- Total debt outstanding.
- ARR: annual recurring revenue.
- Capex: capital expenditures.
- COGS: cost of goods sold, cost of revenue, cost of sales.

## Where the figures are

Financial data is spread across the document, not only in one financials section. Check each of these before you say a figure is absent:

- the executive summary (headline revenue and EBITDA);
- the financial overview or performance section (detailed tables);
- appendices (pro forma financials, detailed projections);
- charts throughout (revenue trends, margin charts);
- footnotes and supplementary tables.

## Type-specific rules

- Slide-built CIMs: in a CIM exported from PowerPoint, Keynote or Google Slides, the financial pages are often bar charts with value callouts. The extracted text holds the numbers but not which year or metric each belongs to. Read those pages with `get_document_page` before you assign a value to a year. Do not report a number whose year and label you could not see.
- Annual over quarterly: when a table has quarterly and full-year columns, take the full-year column. Do not add the quarters.
- Consolidated over segment: multi-segment CIMs show revenue and EBITDA per segment and in total. Take the Total, Consolidated or Combined row. If the CIM shows only segments, say so; a sum you make is your derivation.
- Margins: use a stated EBITDA margin row as printed. Do not compute a margin from revenue and EBITDA unless asked, and label it if you do. If a stated margin does not match EBITDA divided by revenue, flag which figure looks wrong.
- Projections: the CIM usually extends past the last actual year. Give every forecast or estimate year its period label and present it as the seller's case.
- ARR: report ARR when the CIM states an ARR figure. When the CIM says revenue is entirely recurring ("100% recurring", "all subscription") but states no ARR, you may say that the CIM describes revenue as fully recurring. Do not assume revenue equals ARR without that statement.
- Conflicts: when one metric and year has different values in different places, prefer the financial statements, then summary tables, then narrative text, then charts. Name the other value if the gap matters.

## Examples

A "Historical Financial Summary" table on page 45, header "($ in millions)":

| ($ in millions) | 2021A | 2022A | 2023A | 2024E |
|---|---|---|---|---|
| Revenue | 85.2 | 102.4 | 118.7 | 135.0 |
| EBITDA | 21.3 | 28.6 | 33.5 | 40.5 |
| EBITDA Margin | 25.0% | 27.9% | 28.2% | 30.0% |

Report: "The CIM reports 2023 revenue of $118.7M and EBITDA of $33.5M (28.2% margin), and estimates 2024 revenue of $135.0M (Historical Financial Summary, p.45, $ in millions)." The 2024 column is an "E" column, so it is the seller's estimate. The margins come from the stated margin row, not from a calculation.

A bar chart on page 38 with the axis label "Revenue ($M)" and no table. Read the page image with `get_document_page`. Report: "A revenue chart in the CIM (p.38) shows about $45M in 2020 and about $92M in 2024; values are read from the chart." Chart readings are approximate, and a table elsewhere in the CIM outranks them.

A table with quarterly and full-year columns and no scale in the header:

| | Q1 2024 | Q2 2024 | Q3 2024 | Q4 2024 | FY 2024A |
|---|---|---|---|---|---|
| Revenue | 28,100,000 | 30,500,000 | 32,200,000 | 34,000,000 | 124,800,000 |

Report the FY 2024A figure: "The CIM reports FY2024 revenue of $124.8M (p.29)." The header states no scale, so the values are in units.
