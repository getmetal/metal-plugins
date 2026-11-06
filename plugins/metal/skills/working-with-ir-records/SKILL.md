---
name: working-with-ir-records
description: Use for Metal investor-relations records (funds, limited partners, prospects and fundraising processes) and how they relate to companies and people. Covers answering questions about an IR or fundraising pipeline, explaining which records an investor, advisor or intermediary needs, and updating an LP.
---

# Working with Metal IR Records

Before starting, read [Safety and confirmation](../../references/safety.md) and apply it throughout this task.

Metal's investor-relations (IR) model has five record types. Choose by the role a record plays in the fundraise, not by the noun the user happened to use.

The Metal tools can read all five and can update a limited partner. They cannot create a fund, limited partner or fundraising process. When a record is missing, explain which records the user needs and tell them to create them in the Metal app.

## The records and their roles

- **Fund:** one of the firm's own funds being raised or managed. Find it with `search_funds`, read it with `get_fund`.
- **Limited Partner (LP):** an investor or prospect relationship: the institution, family office or individual whose capital a fund is pursuing or has closed. An LP does not imply a commitment. It belongs in Metal from first identification, while the prospect is still being qualified. Find it with `search_limited_partners`, read it with `get_limited_partner`.
- **Fundraising Process:** one LP pursuing one fund. This is the pipeline opportunity. It carries the status and stage, the target, soft-circled and committed amounts, probability, and notes for that raise. A fundraising process always has an LP. Pipeline state never lives on the LP itself, so an LP evaluating two funds has two processes, and a re-approach after a pass is a new process. Find it with `search_fundraising_processes`, read it with `get_fundraising_process`.
- **Company and Person:** the firm's universe of organizations and people. In an IR workflow they represent intermediaries and contacts, not the investor relationship.

An LP's `funds` field is derived from its fundraising processes. To see an LP's commitments to specific funds, search processes with `limitedPartnerIds`.

## Customer terminology

Users rarely say "limited partner". Map their words to the records:

- "prospect", "investor", "account", "allocator": a Limited Partner, plus a Fundraising Process once it enters a fund's pipeline.
- "advisor", "consultant", "placement agent", "wealth manager", "intermediary": a Company and its People. The LP's source fields link the Company.
- The firm's own pipeline names and status or stage labels: a fundraising process status or stage. Read the firm's configured labels with `get_fundraising_status_and_stages` rather than assuming them.

## Intermediaries are Companies and People, linked by source fields

An advisor, consultant, placement agent, wealth manager or bank that introduces or represents prospects is a Company (the firm) with People (the individual advisors). It is not the LP. The relationship is kept on the LP through its origination fields:

- `sourceType`: how the relationship started, such as `placement_agent`, `consultant` or `existing_lp_referral`. The `update_limited_partner` schema lists every value.
- `sourceCompany`: `{"id": ..., "type": ...}` pointing at the intermediary's Company. When an existing investor made the referral, point it at that LP and set `type` to `limited_partner`. `type` defaults to `company`.

Fundraising processes also carry source fields and source contacts. You can read them and filter on `sourceContactIds`, but the Metal tools cannot change them.

## An organization can be both a Company and an LP

The two record types are not exclusive. When one organization is both part of the firm's company universe and an investing prospect, such as a corporate LP or a tracked company that also invests, keep the Company record for organization context and an LP record for the investor relationship. Link them by calling `update_limited_partner` with `company` set to the Company's ID. `clearCompany: true` unlinks it; never send both.

Only an LP can enter a fundraising process. Whenever the organization is a prospect, it needs an LP record, however complete its Company record is.

## Placeholder LPs for unidentified prospects

When the prospective investor is not yet identified, such as an advisor's unnamed client or an unnamed family office, the firm should still track it. The pattern is a placeholder LP named for what is known, the same way a project-named deal stands in before its target company is known.

- LP names are unique within the organization, so each placeholder needs a distinct name. Renaming an LP to a name another LP holds fails.
- Once the identity surfaces, rename and complete the placeholder with `update_limited_partner` instead of asking for a new LP.
- Never block pipeline entry on learning the investor's identity, and never put the intermediary in place of the missing investor.

## Explaining which records the user needs

When the user asks how to track an investor, prospect, advisor or fund, lay out the full record chain their workflow needs instead of classifying the one noun they asked about. A pipeline entry is never a single record: it is an LP plus a fundraising process, with intermediaries and contacts linked around them.

Search first. Tell the user which records already exist and which are missing. For an advisor-led prospect whose identity is not yet known, the complete pattern is:

1. A **Company** for the advisory firm, and **People** for the individual advisors.
2. A **placeholder LP** for the prospective underlying client.
3. A **Fundraising Process** pairing that LP with the fund. This is the record that enters the pipeline.
4. **Source fields** on the LP pointing back to the intermediary firm.

Tell the user to create the missing records in the Metal app. Once an LP exists, you can set its source fields, Company link and contacts with `update_limited_partner`.

## Answering pipeline questions

- Resolve funds, LPs, people and users to IDs before you filter: `search_funds`, `search_limited_partners`, `search_people`, `search_users`.
- Filter processes by `status` or `stage` with the firm's configured labels from `get_fundraising_status_and_stages`. A label matches only processes that carry it. An uppercase internal value such as `ACTIVE` matches every label mapped to it.
- For time in stage, set `stageChangedBefore`. Records that predate stage-change tracking never match that filter, so say so when the count matters.
- Tags are defined per organization. Resolve a tag label with `list_fund_tags`, `list_limited_partner_tags` or `list_fundraising_process_tags` before you pass `tagIds`.

## Updating an LP

Read the LP with `get_limited_partner` first. Pass only the fields that change; an omitted field is left alone.

- `primaryContacts` and `consultantContacts` replace the whole list. Pass the full new list of person IDs from `search_people`.
- `tags` replaces the tag list. `addTags` and `removeTags` change it without dropping tags you did not read. Do not combine the two forms.
- Each `clear...` flag removes its field. Never send a value and its clear flag together.
- `type` and `sourceType` take only the values the schema lists.
- `funds` is read-only.

Never type an LP, company, person or fund ID from memory. Copy it from a tool result.
