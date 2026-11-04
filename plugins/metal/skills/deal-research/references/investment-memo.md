# Reading an investment memo

An investment memo (IC memo or deal memo) is an internal document that a deal team writes for its investment committee to argue for or against an investment. It mixes narrative (thesis, market, risks) with a financial summary: historical results, projections, valuation and a returns analysis. It is usually a PDF or Word document, sometimes a slide export.

A memo's company figures are second-hand. They come from the CIM, the QoE, the statements or the deal team's own model. When the memo names its source, weight the figure by that source (see the source table in SKILL.md). When it does not, say that the memo does not give one.

## How a memo differs

- Projection-heavy: the financial summary usually pairs a few historical years with a multi-year projection. Getting the split between actual and projected periods right is the most important discipline for this document. Never report a projected year as an actual.
- Scenario cases: memos often show more than one projection: Base, Management, Downside or Upside, or a Sponsor case against a Management case. Name the case for every projected figure you report.
- Reported and adjusted: like a CIM or QoE, a memo often quotes Adjusted or Pro Forma EBITDA next to reported EBITDA. Keep them apart.
- Returns and valuation: memos lead with entry and exit multiples, purchase price, enterprise value, IRR, MOIC and a sources and uses table. These describe the deal, not the company. Do not mix them into the company's financials.

## Metrics to look for

- Revenue, EBITDA, Adjusted EBITDA (Adjusted, Pro Forma, Normalized, Run-Rate), gross profit and gross margin, net income, COGS.
- Capex, and maintenance and growth capex when the memo splits them.
- Total debt or net debt: the target's existing debt. The post-LBO pro forma debt in the sources and uses or capital structure table is the deal's financing, not the company's current debt.
- Net working capital, when a schedule shows the total.
- ARR, common in software memos.

## Type-specific rules

- Period labels: "A" is an actual. An in-progress year marked "E" is an estimate. Forward "P", "F" or "Proj" years are forecasts.
- Scenarios: when the user does not name a case, lead with the base or management case and say which case it is. Give other cases only as alternatives, labeled. Do not mix cases within one series.
- Scale per table: a financial-summary table and a returns table can use different scales.
- Narrative restatements ("Adjusted EBITDA of $33M in FY2024E, growing to $45M by FY2026") are secondary; cite the financial summary table.
- Returns figures: report IRR, MOIC, entry and exit multiples or purchase price only when the user asks, as the deal team's underwriting case.

## Examples

A "Financial Summary" table on page 7, footnote "$ in millions":

| ($M) | FY2022A | FY2023A | FY2024E | FY2025P |
|---|---|---|---|---|
| Revenue | 120.4 | 138.9 | 152.0 | 171.0 |
| Adj. EBITDA | 24.1 | 29.5 | 33.4 | 39.8 |
| Adj. EBITDA Margin | 20.0% | 21.2% | 22.0% | 23.3% |

Report: "The IC memo shows FY2023 Adj. EBITDA of $29.5M (21.2% margin), an FY2024 estimate of $33.4M and an FY2025 projection of $39.8M (Financial Summary, p.7, $ in millions)." FY2024E is an estimate and FY2025P is a forecast.

A Word memo with a "Historical & Projected Financials" table, note "USD thousands", columns 2023A and 2024P, revenue 42,100 and 50,500, EBITDA 8,400 and 11,200. Report 2023 revenue of $42.1M and EBITDA of $8.4M as actuals, and the 2024 figures as projections. Cite the table or section name, and the page or block that `get_document` returns.

A scenario table on page 11 for FY2025, "$ in millions":

| ($M) FY2025 | Management Case | Downside Case |
|---|---|---|
| Revenue | 171.0 | 154.0 |
| Adj. EBITDA | 39.8 | 31.0 |

Report: "The memo's Management Case projects FY2025 Adj. EBITDA of $39.8M; its Downside Case projects $31.0M (p.11)."
