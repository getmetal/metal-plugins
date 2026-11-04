---
name: deal-research
description: Use when researching a deal or target in Metal, answering diligence questions, or reading and extracting figures from deal documents in Metal (CIM, teaser, QoE, financial statements, board deck, investment memo, data supplement, expert call).
---

# Deal Research

Every deal document has an author with an agenda. Read each document by asking who produced it and what outcome they want. Weight each claim by the incentives of its source, not by how polished or confident the document looks.

A deal corpus holds three kinds of material. Seller-produced materials are CIMs, teasers, management presentations and seller models. Independent evidence is buy-side QoE reports, audited financials and expert calls. Raw company files, such as data room trial balances and monthly P&Ls, sit between the two: company-produced but unpolished, useful for verification but not independent. Keep the three separate, and say which one supports each claim.

## How much to trust each source

| Material | Produced by | Purpose | Bias | Evidentiary weight | How to treat its claims |
|---|---|---|---|---|---|
| Teaser | Sell-side banker | Generate interest before the NDA | Pure marketing; anonymous, best-case framing | Lowest | Directional only. Never cite as fact |
| CIM / CIP | Sell-side banker with management | Sell the company after the NDA | Marketing document; add-backs and projections are seller-defined | Low for figures; medium for structural facts (segments, footprint, customers) | Treat all figures as seller claims; verify against buyer-side evidence |
| Process letter | Sell-side banker | Run the auction (timeline, bid instructions) | Administrative; creates time pressure | High for process facts | Use for IOI, LOI and bid dates and process rules |
| Management presentation | Management, with the banker | Deepen interest after the CIM | Marketing, in the operator's voice | Low to medium | Treat like the CIM |
| Seller financial model | Seller or banker | Justify the ask and projections | Built to support the seller's case | Low | Assumptions are claims; rebuild bottom-up before relying on it |
| QoE report | Accountant commissioned by the buyer, or by the seller (vendor QoE) | Validate earnings quality | Buy-side QoE is independent normalization; vendor QoE is done by an independent firm but seller-commissioned, so scope and framing can favor the seller | High when buy-side; medium for vendor QoE | Find the commissioning party and engagement scope first. Prefer buy-side QoE for Adjusted EBITDA; treat vendor QoE figures as better-documented seller claims. Compare against CIM add-backs and surface gaps |
| Audited financial statements | Independent auditor | Attest historical GAAP or IFRS results | Conservative, rules-based | High for historicals | Ground truth for historical revenue and net income; say nothing about adjusted figures |
| Expert call transcript | Independent expert through a network | Insight on the market or company | Opinion; quality varies, can be anecdotal | Medium | Corroborating evidence; triangulate across calls |
| Data room financials (trial balances, monthly P&Ls) | Company (raw) | Support diligence verification | Raw, but the seller selected the scope | Medium-high for the periods covered; corroborating, not independent | Basis for your own verification; check completeness and reconcile against independent evidence |
| IOI / LOI | Buyer, or seller summaries of bids | State price and terms | Negotiating instrument | High for deal terms | Use for valuation and structure context |

Two internal types are not in the table. A board deck is management reporting to its own board: not marketing, but not independent. An investment memo is a deal team's case to its investment committee: its figures are second-hand, so trace each one to the document it came from and weight that document.

## Reading seller materials

CIMs and teasers are marketing documents. That makes their figures claims, not facts. When a figure comes from a CIM, teaser, management presentation or seller model:

1. Attribute it to the seller. Write "The CIM reports Adj. EBITDA of $15.8M", never "Adj. EBITDA is $15.8M". Derived figures (growth rates, CAGRs, margins computed from seller figures) carry the same attribution.
2. Label seller adjustments as seller-defined. Add-backs are what the seller chose to add back. Scrutinize each one, such as owner compensation and "one-time" items that recur.
3. Present projections as the seller's case, with their stated assumptions, never as the expected outcome.
4. Cross-check against independent evidence (buy-side QoE, audited financials) and against raw data room financials (corroborating, not independent). When the numbers differ, give both and name the gap: "The CIM reports $15.8M Adj. EBITDA; the QoE supports $11.9M, a $3.9M gap driven by unsupported add-backs."
5. When no independent evidence exists, say so even when not asked. "No buy-side QoE yet" is itself a diligence fact.

## Synthesis loop

1. Frame the question: what decision does the answer inform (screen, IOI, diligence deep-dive)?
2. Gather seller materials, raw company files and independent evidence separately.
3. Weigh each claim with the table above.
4. Synthesize with attribution. Every figure carries its source. Gaps and contradictions between seller and buyer-side evidence are findings.

## Finding the evidence in Metal

The server instructions and the tool descriptions cover search mechanics. These points are not in them:

- Weigh a document by what it is, not by its `documentType`. A vendor QoE and a buy-side QoE share one type, and catalog metadata is not proof. Confirm the type, the author and, for a QoE, the commissioning party from the document itself.
- For a type the user names, call `get_document_types` and match its names and synonyms. If no type matches, search content for the user's phrasing instead.
- `search_deals` has no sector filter. For deals in a sector, find the companies with `search_company_taxonomy` and `list_companies` (or `search_companies`), then pass their IDs as `companyIds` to `search_deals`. Also run `search_screenings` with `sector` or `subsector`, because a screened CIM can exist without a deal record.
- For a sector question that expects full coverage, page through `list_companies` until `hasMore` is false. Companies already in context are not the full set. A document search finds only companies that own matching documents.
- No MCP tool resolves a folder name. `folderIds` matches a folder and its subfolders; `rootFolderIds` matches a top-level workspace. A document's `folderPath` is its folder IDs joined by dots, top folder first, so you can reuse an ID from a document known to sit in that folder. Otherwise search without a folder filter and tell the user.
- When a search finds nothing, drop the filters you added yourself one at a time, but keep filters the user asked for. Say what you searched before you report absence.
- A document whose `status` is other than `INDEXED`, for example `ERROR` or a `RUNNING_` state, can be missing from search results. Tell the user it is not in the answer.

### Deals and deal intelligence

- Status and stage labels differ per organization. Call `get_deal_status_and_stages` before you filter `search_deals` by `status` or `stage`, and prefer the organization's labels.
- `get_deal` without `fields` returns the full record, including `intelligence`. `search_deals` omits intelligence unless `fields` includes `intelligence` or `responseMode` is `full`.
- `intelligence` is a research summary written by Metal's research workflows, dated `researchedAt`. It holds `analysis`, `investmentThesis`, `macroContext`, `outcome` (`type` is `active`, `won`, `lost` or `passed`, with `explanation`), `keyDecisions` (each a `decision` with its `reasoning`), and `keyMetrics`. Newer records add `looks`, one per separate look at the company, with `role`, `outcome` (which can also be `withdrawn`), `passReason`, `valuation` and `icMilestones`.
- Each `keyMetrics` entry has `field`, `value`, `currency`, `unitFactor`, `periodType`, `periodEnd`, an optional `citation` (`document` ID and `page`) and `outcomeWeight`. A higher `outcomeWeight` means the metric weighed more in past outcomes for this firm; prioritize those metrics when you evaluate a similar deal. A metric cited to a CIM page is still a CIM figure: weight it by the table above, and verify it on that page with `get_document_page`. Older metrics can lack a period or citation; treat them as unverified.
- Use `keyDecisions` across several deals to find the firm's patterns: what made it advance or pass, and which factors recur. Patterns from a few deals are directional, not definitive. Flag where the current deal falls outside the range of the firm's past deals.
- Only quote intelligence the tools return. Do not fill a missing field from your own reasoning. The MCP cannot write deal intelligence.

### CIM screenings

- `search_screenings` takes filters only. A non-empty `query` is rejected. Use `companyIds`, `dealIds`, `dataEntityIds` (from a CIM's document ID), `sector` or `subsector`; `sortBy` accepts `revenue` and `ebitda`, but there is no revenue or EBITDA range filter.
- `get_screening` with `includeFinancials: true` returns `extractedFinancials` (every figure read from the CIM) and `latestFinancials` (one figure per metric). Each row has `label`, `year`, `value`, `unitFactor`, `currency`, `periodType`, `periodEnd`, `metricType`, `margin` and a source citation. Apply `unitFactor` when you quote a value. `margin` and `percentage` values are decimals (0.25 is 25%). An empty `periodEnd` means December 31 of `year`. When the CIM states no EBITDA margin, Metal computes the `margin` on an EBITDA row from same-period revenue; check the CIM before you call a margin stated.
- `latestFinancials` takes the latest LTM figure; if there is none and the CIM is dated after June, the nearest estimate or forecast; otherwise the latest actual. So a "latest" EBITDA can be the seller's current-year estimate. Name the period type when you quote it.
- Every screening figure is still a CIM figure. Attribute it to the CIM, and verify material figures on the cited page.

### Reading a document

- `get_document` returns extracted text. `get_document_page` returns one physical page as an image, so a client that reads images can take values from a chart-only page, a slide whose numbers live in the layout, or a table whose column alignment the text lost. Use it for targeted pages, not whole documents. It needs a PDF, or a PDF that Metal made from the file (such as a converted PowerPoint). If it reports that the page needs a PDF rendition, use the extracted text and tell the user that the layout could not be checked.
- Page numbers for `get_document_page` are physical PDF pages. A printed page label can differ. Cite the page you verified.
- When available, `list_document_tables` and `query_document_table` read spreadsheet sheets and extracted PDF tables as rows. Use them for workbooks such as data books and trackers.

## Reading figures from deal documents

These rules apply to every financial document type. The type references below add what differs.

- Scale: read the scale from the table header, axis label or footnote ("$ in millions", "($000s)", "$M"). Resolve it per table, slide or statement, because two tables in one document can differ. Report the printed value with its scale ("$125.3M", from a "$ in millions" table). If you rescale or convert a value, say so. When no scale is stated, say that you assumed units.
- Currency: read the full header, including any prefix on the $ sign (€m is EUR, £m is GBP, US$m or $m is USD, C$m is CAD, A$m is AUD). Assume USD only when the document states no currency, and say so.
- Percentages and margins: report a margin only when the document states it. Do not compute a margin, CAGR or other unstated metric unless the user asks, and label any you compute as your derivation. An EBITDA margin row belongs to EBITDA; it is not gross margin.
- Negatives: parentheses ("(1,250)") or a trailing minus mean negative. Report COGS and expenses as costs, and a parenthesized bottom line as a net loss.
- Period labels: a plain past year or an "A" suffix is an actual. "E", "B", "Budget" or "Plan" is an estimate or budget. "F", "P" or "Proj" is a forecast. LTM or TTM is a trailing twelve months; give its end date ("LTM 9/30/24"). YTD is year to date; give its end date. For a fiscal year that does not end on December 31, give the year-end ("FY ended June 30, 2024").
- Granularity: prefer the annual or LTM figure. Use quarterly or monthly figures only when no annual figure exists, and say so. Do not add quarters to make a year unless asked.
- Consolidated over segment: take the Total, Consolidated or company-level row, not a segment, product or region. If only segments are given, say so; a sum you make yourself is a derivation.
- Reported over adjusted: keep reported EBITDA and Adjusted EBITDA apart. Adj. EBITDA, Pro Forma EBITDA, Normalized EBITDA and Run-Rate EBITDA are adjusted variants. Never call a reported figure adjusted, or the reverse.
- Conflicts within one document: prefer financial statements over summary tables, summary tables over narrative text, and narrative over charts. A value read from a chart is approximate; say so. An approximate figure ("~$12M", "c.$45M") stays approximate in your answer.
- Omit rather than misidentify. A figure under the wrong label is worse than a missing one.
- Cite every figure: document name, page or slide, and table or section name, with the link the tool returns (`sourceLink` or `sourceLinkMarkdown`).

## Document type references

Identify the type from the document itself (cover, author, structure). Then read the matching reference before you extract or interpret its figures:

| Document | Reference |
|---|---|
| CIM or CIP, management presentation | `references/cim.md` |
| Teaser | `references/teaser.md` |
| Quality of Earnings report (buy-side or vendor) | `references/qoe.md` |
| Financial statements, reporting package, periodic P&L | `references/financial-statements.md` |
| Board deck | `references/board-deck.md` |
| Investment memo (IC or deal memo) | `references/investment-memo.md` |
| Financial data supplement (data book, fact book, KPI supplement, supporting schedules) | `references/financial-data-supplement.md` |
| Expert call transcript | `references/expert-call.md` |

## Common mistakes

- Stating CIM or teaser figures as fact instead of seller claims.
- Dropping attribution in the summary or bottom line. The closing must keep "the CIM reports" and "the QoE supports". A figure attributed correctly mid-answer is still misstated if the bottom line upgrades it to fact.
- Comparing Adjusted EBITDA across deals without normalizing each seller's add-back policy.
- Repeating management projections as the expected case.
- Citing teaser metrics with any confidence. Teasers are anonymous marketing.
- Treating vendor QoE or raw data room files as independent verification. Only buy-side QoE and audited financials are independent.
- Ignoring the absence of independent evidence.
- Treating a single expert call as definitive instead of one input to triangulate.
- Quoting a screening's `latestFinancials` value without its period type.
