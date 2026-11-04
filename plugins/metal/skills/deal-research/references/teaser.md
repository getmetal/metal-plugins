# Reading a teaser

A teaser is a short (usually 1 to 10 pages) pre-NDA deal summary that the company or its banker sends to generate interest. It is usually a PDF or a slide deck. It has the lowest evidentiary weight of any deal document: anonymous, best-case marketing (see the source table in SKILL.md).

Keep two questions apart. How accurately you read a figure depends on how clearly the teaser presents it; a clearly labeled table in a teaser reads as reliably as the same table in a CIM. How much the figure is worth as evidence does not change: it stays directional, and you attribute it to the teaser.

## How a teaser differs from a CIM

- Less detail: often one or two historical years, a current-year estimate and sometimes projections. A full P&L is rare; one line each for revenue and EBITDA is typical.
- Rounded figures, at a different precision from the financial statements.
- Seller-optimistic: adjusted and normalized metrics are common. Do not extrapolate from them.
- Period labels can be missing (see below).

## Metrics to look for

- Revenue: total revenue, net revenue, sales, recurring revenue.
- EBITDA: reported EBITDA.
- Adjusted EBITDA: Adj. EBITDA, Pro Forma EBITDA, Normalized EBITDA, Run-Rate EBITDA.
- Gross profit and gross margin.
- ARR, common in software teasers.
- Net income, when stated.

Valuation multiples (EV/EBITDA, revenue multiples), deal terms and management equity are not operating metrics. Report them only when the user asks for them, and keep them apart from the company's financials.

## Type-specific rules

- Missing period labels: a past year with no "A", "E" or "F" suffix is an actual. A figure described as an estimate, budget or target for the current year ("2024E", "Est.", "Budget") is an estimate. A future year is a forecast. "LTM", "TTM" or "Last Twelve Months" is a trailing period; give its end date. Say when you inferred a period label.
- Bullets and highlights: teasers often state metrics in bullets ("Revenue of $45M growing 30% YoY", "EBITDA: ~$12M"). Keep the year context from the bullet. Keep "~" or "c." as "about".
- EBITDA margin: a margin row under Adj. EBITDA is an EBITDA margin, not a gross margin.
- Duplicates: when a bullet and a table give the same metric and year, use the table and check that the bullet agrees.

## Examples

A "Financial Highlights" table on page 5, header "($ in millions)":

| | 2022A | 2023A | LTM 9/30/24 |
|---|---|---|---|
| Revenue | 38.4 | 45.2 | 51.6 |
| Gross Profit | 22.1 | 26.8 | 30.7 |
| Gross Margin | 57.6% | 59.3% | 59.5% |
| Adj. EBITDA | 9.1 | 11.3 | 13.2 |
| Adj. EBITDA Margin | 23.7% | 25.0% | 25.6% |

Report: "The teaser shows LTM revenue of $51.6M and Adj. EBITDA of $13.2M (25.6% margin) for the twelve months ended 9/30/24 (Financial Highlights, p.5, $ in millions). These are seller marketing figures with no independent support yet."

An "Investment Highlights" text box on slide 3 with no table:

- "$54M estimated 2024 revenue (30%+ YoY growth)"
- "~$14M Adjusted EBITDA; ~26% margin"
- "100% recurring revenue; ARR of $52M"

Report: "The teaser estimates 2024 revenue at $54M and Adjusted EBITDA at about $14M (about 26% margin), and states ARR of $52M (slide 3)." The revenue and EBITDA are estimates, not actuals.

A bar chart on slide 7 with the axis label "Revenue ($M)", 2020 to 2024, where the 2024 bar is lighter than the others. Read it with `get_document_page`. Report the bars as approximate chart readings, and say that the 2024 bar looks like an estimate because it is styled differently.
