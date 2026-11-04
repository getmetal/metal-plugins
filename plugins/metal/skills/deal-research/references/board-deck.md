# Reading a board deck

A board deck is a presentation prepared for a company's board of directors. It reviews performance, strategic initiatives and results against plan. It is usually a PowerPoint deck or a PDF exported from slides. It is management's own view reported to its directors: not marketing, but not independent (see SKILL.md).

## How a board deck differs

- KPI-forward: the headline metrics are often operating KPIs (ARR, customer counts, retention) next to revenue and EBITDA.
- Actual against plan: slides routinely show actuals beside budget or plan and the prior year. Lead with the actual.
- Chart-heavy: results often appear only as bar or line charts with value callouts. Read those slides with `get_document_page`.
- Adjusted figures: management often presents Adjusted EBITDA. Keep it apart from reported EBITDA.

## Metrics to look for

- Revenue: total revenue, net revenue, sales.
- EBITDA: reported EBITDA.
- Adjusted EBITDA: Adjusted, Pro Forma, Normalized or Run-Rate EBITDA.
- Gross profit and gross margin.
- Net income.
- ARR, common in software board decks.
- Capex, when a financial-summary slide shows it.
- Total debt or net debt, when a balance-sheet or liquidity slide shows it.

Other KPIs (headcount, NPS, pipeline, logo counts), initiative status and valuation figures are not financial metrics. Report them only when the user asks, and keep them apart from the financials.

## Type-specific rules

- Scale per slide: a KPI slide and a financials slide can use different scales. Read the axis label, table header or slide footnote ("$ in millions", "$M", "All figures in 000s").
- Actual against budget columns: report the actual as the figure for the period. Report a budget or plan only as the plan, or as the variance to actual when the question is about performance against plan. A budget for a period that already has an actual is not a second value for that period.
- Plan slides: a slide that shows only next year's targets ("FY2025 Plan") gives forecasts. Report them as management's plan, not as results.
- Period labels: "Actuals" or "A" is an actual. "Budget", "Plan", "B" or a current-period estimate is an estimate. A future projection is a forecast. LTM or TTM is a trailing period; give its end date. YTD is year to date.
- Use the deck date to fix which period the deck reports.

## Examples

Slide 6, "Q4 & FY2024 Financial Results", footnote "$ in millions":

| ($M) | FY2024 Actual | FY2024 Budget | FY2023 Actual |
|---|---|---|---|
| Revenue | 88.4 | 85.0 | 72.1 |
| Adj. EBITDA | 19.2 | 18.0 | 14.6 |
| Adj. EBITDA Margin | 21.7% | 21.2% | 20.2% |

Report: "The FY2024 board deck shows revenue of $88.4M against a $85.0M budget, and Adj. EBITDA of $19.2M (21.7% margin) against $18.0M budgeted (slide 6, $ in millions)." The budget appears only as the comparison.

Slide 9, an ARR bar chart for 2021 to 2024 with the axis "ARR ($M)" and no table. Read it with `get_document_page` and report the bars as approximate chart readings (about $31M, $44M, $58M and $71M).

Slide 14, "FY2025 Plan", "$ in millions", with the bullets "Revenue target: $102M" and "Adjusted EBITDA target: ~$24M (~24% margin)". Report: "Management's FY2025 plan targets revenue of $102M and Adjusted EBITDA of about $24M (slide 14)."
