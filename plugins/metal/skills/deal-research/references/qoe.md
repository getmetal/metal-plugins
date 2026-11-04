# Reading a Quality of Earnings report

A Quality of Earnings (QoE or QofE) report is prepared by an accounting firm, or sometimes an internal finance team, during diligence. It normalizes a target's historical earnings: it strips out non-recurring, non-operating and owner-benefit items from reported EBITDA to show the underlying run-rate. It is usually a PDF, sometimes with Excel workpapers.

Before you weigh it, find who commissioned it and the engagement scope, usually in the cover letter or the scope section. A buy-side QoE is independent and is the preferred source for Adjusted EBITDA. A vendor QoE is seller-commissioned; treat its figures as better-documented seller claims (see the source table in SKILL.md).

## How a QoE differs from a CIM

CIM figures are the seller's. QoE figures are the diligence firm's reconciliation of them. For each period, a QoE usually shows:

- reported values (GAAP or management-reported);
- proposed adjustments, one line per adjustment;
- adjusted values (normalized, pro forma, or "Quality of Earnings").

Report both reported EBITDA and Adjusted EBITDA for each period the QoE shows them. EBITDA is the only metric with an adjusted view; for the other metrics, report the reported value. If the QoE proposes no adjustments, its "Adjusted EBITDA" is reported EBITDA; call it that.

## Metrics to look for

- Revenue, reported.
- EBITDA, reported or "as adjusted by management".
- Adjusted EBITDA: QoE-adjusted, also labeled "Quality of Earnings", "Pro Forma EBITDA" or "Normalized EBITDA".
- Gross profit and gross margin, reported.
- Net income, reported.
- COGS.
- Net working capital: usually a dedicated schedule with period-end values.
- Capex: total, and maintenance and growth capex when the QoE splits them.
- Debt: total debt, or net debt when reported.

## Where the figures are

Look first for the Adjusted EBITDA bridge and the QoE summary ("Summary of findings", "Summary of adjustments", "EBITDA adjustments", "Proposed adjustments"). Then the historical P&L, revenue by segment and the net working capital schedule. Then other schedules (balance sheet, cash flow, capex). In Excel workpapers, read the summary tabs ("EBITDA Bridge", "Adjustments", "QoE Summary") before raw general-ledger exports.

## Type-specific rules

- The bridge: report reported EBITDA and Adjusted EBITDA from the bridge for each period. The adjustment lines (owner compensation, legal fees) explain the gap; name the large ones when they matter to the question, and cite the bridge page.
- Check the arithmetic: for at least one period, add the listed adjustments to reported EBITDA and compare with Adjusted EBITDA. If they do not reconcile within rounding, say so.
- Compare with the CIM: when a CIM exists for the same company, set the QoE's Adjusted EBITDA against the CIM's and name the gap and the adjustments that drive it.
- LTM columns: QoE reports often add an LTM column ("LTM 9/30/24"). It is a trailing period, not a fiscal year; give its end date.
- Off-cycle balances: a working capital column dated inside a fiscal year (for example Sep-24) is a balance at that date, not a year-end balance.
- Budget columns ("Budget", "B") are estimates; projection columns are forecasts.
- Prefer the schedule over the narrative. A headline in the text ("Adjusted EBITDA of $13.9M for the LTM period") is a restatement; cite the schedule.
- Source preference: for EBITDA use the bridge; for revenue, COGS and gross profit use the P&L schedule.

## Examples

An Adjusted EBITDA bridge on page 12, header "($ in thousands)":

| | 2022A | 2023A | LTM 9/30/24 |
|---|---|---|---|
| Reported EBITDA | 8,420 | 11,050 | 12,780 |
| Owner compensation normalization | 1,200 | 1,200 | 900 |
| Non-recurring legal fees | 450 | - | 310 |
| One-time IT implementation | 780 | - | - |
| Adjusted EBITDA | 10,850 | 12,250 | 13,990 |
| Adjusted EBITDA Margin | 24.1% | 26.3% | 27.4% |

Check 2022: 8,420 + 1,200 + 450 + 780 = 10,850, which reconciles. Report: "The buy-side QoE supports LTM Adjusted EBITDA of $13.99M for the twelve months ended 9/30/24 (27.4% margin), against reported EBITDA of $12.78M; the largest adjustment is owner compensation of $0.9M (Adjusted EBITDA Bridge, p.12, $ in thousands)."

A net working capital schedule on page 24, header "($ in millions)", with columns Dec-22, Dec-23 and Sep-24 and a total row of 12.7, 14.5 and 16.1. Report the total row only, not accounts receivable or payable. Dec-22 and Dec-23 are year-end balances; Sep-24 is a balance at 9/30/24.

A capex schedule on page 31, header "($ in thousands)", with maintenance capex (620, 710, 740), growth capex (1,400, 2,200, 1,900) and total capex (2,020, 2,910, 2,640) for 2022A, 2023A and LTM 9/30/24. Report total capex, and give the maintenance and growth split when the question is about capital intensity.
