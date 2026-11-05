---
name: working-with-lists
description: Use when the user wants to save results as a Metal list, create a list or change its columns, or read, add or update list rows, even if they do not say "list". Read it before create_list, add_list_entries or update_list_entry, because cell formats and write side effects are not in the schemas.
---

# Working with Metal Lists

A Metal list is a table of rows with typed columns. On a typed list, such as a company or deal list, each row is linked to one Metal record. On a custom list (`resourceType: "none"`), rows are not linked to records.

## What the tools can and cannot do

- **Find and read:** `list_lists` (filter by `resourceType`), `get_list` for the columns, `get_list_entries` for the rows.
- **Create and change:** `create_list`, `update_list` (name, description, primary key), `update_list_columns` (add, remove, rename), `add_list_entries`, `update_list_entry`.

These tools cannot delete a list or a row, filter or sort rows on the server, run AI enrichment, sync or refresh columns, share a list, or create a column that syncs a field from the linked record. They cannot create Score or Tags columns. When the user asks for one of these, tell them to do it in the Metal app. A list created here is private to the user until they share it in the app.

## Choose the list's resource type

- Use a typed list (`company`, `person`, `deal`, `dataEntity`, `activity`, `screening`, `limitedPartner`, `fundraisingProcess`, `fund`) when every row is an existing Metal record of that type. A `dataEntity` list holds documents, and every row must link a document.
- Use `none` when the rows are not Metal records, mix record types, or are the user's own data.

## Save results as a list

When the user asks to save companies, people or deals that you showed them, the list must show what they saw. `create_list` creates exactly the columns you pass, and no others.

1. Pick the resource type. Plan one column for each attribute you showed, in the same order, with the column type that fits the value (see Column types below).
2. Make the first column a `string` column that holds each row's name, such as "Company Name". These tools cannot create a column that reads the name from the linked record, so a typed list without this column shows no name on any row. On a `none` list, call this column `Name`; Metal shows a text column with that exact name as the row's name.
3. Call `create_list`. Keep the column IDs from its result. Cell values are keyed by column ID, not by column name.
4. Call `add_list_entries` with up to 1,000 rows per call. On a typed list, link each row to its record with `resourceId` and `resourceType`, copied from the search result where you found it. Write the record's name into the name column yourself.
5. Check `failed[]` in the result (see Partial failures), then read the rows with `get_list_entries` and tell the user how many rows were saved and which were not.

Never add a row to a company or person list without `resourceId`. Metal then tries to match the row to a record from its values, and it can create a new company or person record in the CRM. On a `none` list, omit `resourceId` and `resourceType`.

The name column is a copy. It does not change when the record is renamed.

## Column types

`create_list` and `update_list_columns` take `{name, type}`. The value format below is what `add_list_entries` and `update_list_entry` accept.

| `type` | Shown in Metal as | Write the cell as |
|---|---|---|
| `string` | Text | text |
| `number` | Number | a number, such as `1250000` |
| `boolean` | Checkbox | `true` or `false` |
| `date` | Date | an ISO 8601 date, such as `"2025-03-31"` |
| `currency` | Currency | `{"unit": "USD", "value": 1500000}`, where `unit` is a 3-letter ISO 4217 code and `value` is a number |
| `percentage` | Percentage | a fraction: `0.25` for 25% |
| `email` | Email | an email address |
| `url` | URL | a URL, such as `"https://example.com"` |
| `location` | Location | an object with any of `street1`, `street2`, `city`, `state`, `zip`, `country` and `position` (`{"lat", "lng"}`), such as `{"city": "Boston", "state": "MA", "country": "US"}` |
| `user-list` | Users | an array of Metal user IDs |

Two more column kinds use `type: "string"`:

- **List column** (a fixed set of choices): add `options`, such as `["High", "Medium", "Low"]`. Each cell takes one of the option labels.
- **Relationship column** (links each row to another record): add `foreignResourceType`. The valid targets depend on the list's resource type, and `create_list` lists them. On a typed list the link fills in from each row's record.

Formats that are easy to get wrong:

- A percentage is a fraction. `25` is stored as 2,500%.
- A currency `value` must be a number. `"$5M"` and `"5000000"` fail. Convert "$5M" to `5000000`.
- A date must be a calendar date. "Q4 2025" or "FY25" fails. Use the period-end date, such as `"2025-12-31"`, and tell the user you did.
- `null` clears a cell.

`get_list_entries` returns cells in the same formats, except that a date comes back as an RFC3339 timestamp and a relationship cell carries the linked record's name.

## Users columns

A users cell holds user IDs, never names or emails.

- Resolve each person with `search_users`. When the user means themselves, use `get_current_user`.
- Treat a name as resolved only when one user clearly matches. When several match, ask the user which one, for example by email.
- If no user matches, leave the cell unset and tell the user.
- A write replaces the whole cell. To add a teammate to a cell that already has people, read the row with `get_list_entries`, then write the existing IDs plus the new one.

## Relationship cells

`get_list` lists relationship columns in `relationshipColumnIds`.

- Resolve the linked record with its search tool, such as `search_companies` or `search_deals`. Never pass a name, and never make up an ID.
- Write the cell as `{"reference": {"id": "<record ID>", "type": "<type>"}}`. `type` is the column's `foreignResourceType`, such as `company`, `deal`, `limited_partner` or `fundraising_process`.
- On a typed list, omit the cell to keep the link that came from the row's record. On a `none` list, `{"isNull": true}` clears the link.
- If no record matches, leave the cell unset and tell the user.

## Partial failures

`add_list_entries` returns `created` and `failed`. Each `failed` item has the `index` of the row in the entries you sent and an `error`. Rows that are not in `failed` were saved.

- Each error names the column and the format it expected, for example `invalid value for column Revenue: ... expected {"unit": "USD", "value": 1500000}`. Only the first problem in a row is reported, so a fixed row can fail again on another column.
- Fix and resend only the failed rows. Never resend the whole batch: a row linked to a record that is already on the list fails with `resource already exists in list`, and a row without a record is added a second time.
- A record can be on a list only once. On a list with a primary key, a duplicate key fails with `duplicate_pk: <value>`.
- Tell the user which rows were not saved and why, in their terms.

`update_list_entry` changes one row. A value in the wrong format fails the whole call.

## Updating rows

1. Find the row's entry ID with `get_list_entries`. An entry ID is not the record's ID.
2. Pass only the cells whose value changes, keyed by column ID.

### Mapped cells write back to the record

A list created in the Metal app can have mapped columns: in `get_list`, a column with a `mapping` that is not in `relationshipColumnIds`. Updating a mapped cell can change the linked deal, company, person or other record, and through a CRM integration the CRM too. Before you update a mapped cell:

1. Tell the user the record, the field, its current value and the new value, and that the change goes to the record and the CRM, not only to the list.
2. Wait for the user to confirm.
3. Update one row per confirmation, unless the user approved a set of rows by name.

Relationship cells never write back.

## Changing columns

- Call `get_list` first. A list created in the Metal app already has a name column, so do not add a second one.
- `update_list_columns` adds, removes and renames columns by column ID, in one call. Renames are applied first.
- Removing a column deletes its values from every row. Confirm with the user before you remove a column that has values.
- A column's type cannot be changed. Replacing it means removing the column and its values, then adding a new one. Confirm that with the user first.
- On a `none` list, a primary key (`pkColumnId`) on a `string`, `email` or `url` column rejects duplicate values. It can be set or changed only while the list has no rows.

## Reading lists

- Find a list with `list_lists`. When several lists match the user's words, ask which one.
- `get_list_entries` returns up to 50 rows per page. Pass `nextToken` from the previous page until no token comes back.
- These tools cannot filter rows. To answer "which rows have revenue over $50M", read every page and filter the rows yourself. Say how many rows you read.

## Handling errors

Read the error before you retry. Never resend an unchanged call after an invalid-input error, because the rejection will repeat.

- **`invalid column type`:** the type is not in the Column types table. Score and Tags columns are created in the Metal app.
- **`options require type string` or `relationship columns require type string`:** set `type` to `string`.
- **`foreignResourceType ... is not valid on a ... list`:** the error lists the valid targets for that list type.
- **`invalid value for column <name>`:** convert the value to the format the error names.
- **`does not match any enum option`:** use one of the labels the error lists, or ask the user.
- **`user ... not found in this org` or `invalid user id`:** resolve the person again with `search_users`.
- **`the list may have been created, but the response was empty`:** check `list_lists` for the list before you call `create_list` again, so you do not create it twice.

Never type a list, column, entry, record or user ID from memory. Copy it from a tool result.
