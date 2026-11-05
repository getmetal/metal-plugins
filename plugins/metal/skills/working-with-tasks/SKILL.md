---
name: working-with-tasks
description: Use when the user wants to read, find, reassign, reschedule, complete, cancel or delete a Metal task (a next step or to-do with an assignee and a due date), even if they do not say "task". Read it before the first update_task call, because task fields carry distinctions the schemas cannot state.
---

# Working with Metal Tasks

A Metal task records what the team intends to do next on a record, who must do it, and when it is due. This skill covers reading and changing tasks that already exist.

The Metal tools cannot create a task. When the user asks for a new task, tell them to create it in the Metal app, and offer to draft its title, assignee, due date and related records.

## A task is forward-looking

An activity records what happened: a meeting, call or other interaction. A task records what the team intends to do next. Keep the two apart when you read and report:

- "Spoke to the CIO on Tuesday" is an activity, not a completed task. Look for it with `get_activities`, not with the task tools.
- Marking a task `completed` records that the team finished its own commitment. It is not evidence of contact with anyone. Do not report a completed task as a meeting or touchpoint.
- To change an activity's participants, linked records, privacy or custom fields, use `update_activity`, not `update_task`. No Metal tool changes an activity's subject or notes.

## The distinctions that matter

### Assignees do the work. Owners control access.

- **Assignees** (`assigneeIds` on a read) are the people responsible for doing the task. Unassigned is a real state. If the user names nobody, leave it empty rather than guess.
- **Owners** (`ownerIds`) control access and imply no responsibility for the work. Never tell a user that an owner is responsible for a task, and do not treat owners as a second assignee list.
- Metal adds each new assignee to the owners. Replacing the assignees does not remove anyone from the owners, so a previous assignee keeps access until removed with `removeOwners`.
- A task has at least one owner and at most 20 assignees.

### Priority 0 is a real value

Priority is `0` No priority, `1` Low, `2` Medium, `3` High, `4` Urgent. On `update_task`, `priority: 0` sets No priority, and omitting `priority` leaves it unchanged. Report `0` as "no priority", not as missing data.

### relatedResources is what the task exists to affect. createdFrom is what it exists because of.

- **`relatedResources`** are the records whose standing completing the task changes. Zero, one or several, of mixed type.
- **`createdFrom`** is the single proximate cause: the meeting, chat session or workflow run that prompted the task.

Never infer one from the other. An LP promises subscription documents in a meeting, and the team records "Chase subscription docs from Acme". Its `relatedResources` holds the fundraising process, because completing the task moves where that raise stands. Its `createdFrom` is the meeting activity, because that is where the commitment was made. A task can come from a meeting and be about a record the meeting never named.

`createdFrom` and the task's `origin` (`user`, `crm` or `agent`) are fixed. `update_task` cannot change them. A task that a workflow created has origin `agent`; there is no separate workflow origin.

### Tags are typed catalog IDs, not free text

A task's `tagIds` are IDs of the organization's task tags. No Metal tool lists or creates task tags, and task reads return tag IDs without their labels. You cannot turn a tag label into an ID. When the user wants a tag added by name, tell them to add it in the Metal app. A company, deal or other non-task tag ID is rejected.

### Completed is not canceled

`completed` means the work was done. `canceled` means it was abandoned. Canceled is not a quiet synonym for done, and reporting one as the other misstates the record. `in_review` marks work done pending a reviewer, and `blocked` marks work waiting on an outside dependency. Outstanding work is `open`, `in_progress`, `in_review` or `blocked`.

## Reading tasks

- **One task:** `get_task` with `taskId`.
- **Filters without text:** `list_tasks`. It filters by `statuses`, `priorities`, a due window (`dueBefore`, `dueAfter`), one related record (`relatedResourceType` plus `relatedResourceId`), and one source (`createdFromType` plus `createdFromId`). It cannot filter by assignee or owner.
- **Text or people:** `search_tasks`. `query` matches words in the title or description. It also filters by `assigneeIds`, `ownerIds`, `origins`, statuses, priorities, the due window and one related record. It cannot filter by `createdFrom`.

Common questions:

- **"What is overdue?"** Call `list_tasks` with `dueBefore` set to the current time as RFC3339 and `statuses: ["open", "in_progress", "in_review", "blocked"]`. Without the status filter, completed and canceled tasks with a past due date come back too.
- **"What is on my plate?"** Call `search_tasks` with `assigneeIds: ["me"]` and the outstanding statuses. This matches the assignee only. It does not return tasks the user created and assigned to someone else. Add `ownerIds: ["me"]` only when the user asks about tasks they own.
- **"What is open on this deal, fund or process?"** Pass `relatedResourceType` plus `relatedResourceId`. Both halves are required together; one alone is an error, not a wider search. Resolve the record first: `search_deals`, `search_companies`, `search_people`, `search_documents` (type `data_entity`), `get_activities`, `search_screenings`, `search_funds`, `search_limited_partners` or `search_fundraising_processes`.
- **"Which tasks came from this meeting?"** Call `list_tasks` with `createdFromType: "activity"` and the meeting's ID as `createdFromId`. A task created without an explicit source carries the chat session or workflow run that created it, so it is found by that ID (`session` or `workflow_run`), not by the meeting.
- **People:** resolve a named person to a user ID with `search_users`. `"me"` means the signed-in user.

Expect these behaviors of `list_tasks`:

- `dueBefore` is exclusive and `dueAfter` is inclusive. Both take RFC3339.
- Setting either one excludes tasks that have no due date. To see undated work, ask without a due filter.
- Results come back newest-created first, not due-next. Filter by the due window, then sort the returned tasks by `dueDate` yourself when the question is about what is due next.
- Pages carry no total count. Page through with `page` until no more tasks come back before you say you have them all. `search_tasks` does return `pagination.totalCount`.

If `get_task` returns an error for an ID you hold, the task may not exist or may be private to someone else. You cannot tell which. Do not tell the user it does not exist, and never present the tasks you could read as the complete set.

## Updating tasks

Read the task with `get_task` first. Pass only the fields whose value differs from what the task holds. An omitted field is left alone.

- **Starting work:** `status: "in_progress"`.
- **Finishing work:** `status: "completed"`. Use `canceled` for work that was abandoned.
- **Rescheduling:** `dueDate` as RFC3339 or `YYYY-MM-DD`.
- **Clearing a value:** use `clearDueDate`, `clearAssignees` or `clearDescription`. An empty `description` string leaves the description unchanged. Never pass both a value and its clear flag.
- **Reassigning:** `assigneeId` for one person or `assigneeIds` for several. Both replace the whole assignee list. To add or remove one person on a task with several assignees, read the task and pass the full new list in `assigneeIds`.
- **Linking records:** `addRelatedResources` adds links and keeps the existing ones, including links a person or the CRM importer added. `removeRelatedResources` removes the links matched by `type` and `id`. Do not send both in one call; make two calls.
- **Tags:** `addTags` and `removeTags` change the tags without dropping ones you did not read. `tags` replaces the whole list, and an empty list clears it. Do not combine `tags` with either delta field.

### Sharing and privacy

Task reads return `sharedWith` and `isPrivate`.

- `isPrivate: true` limits the task to its owners and the users or teams it is shared with. `isPrivate: false` makes it readable across the organization. Change it only when the user asks.
- `addSharedWith` grants access and keeps other shares. `removeSharedWith` revokes access for a user or team. `sharedWith` replaces the whole list, and an empty list clears every share. Omit all three to leave sharing alone.
- Each share entry is a `user` or `team` with `access` `viewer` or `editor`. An omitted `access` becomes `editor`.
- On a private task, only an owner or an editor can change the task or its sharing. A viewer can change sharing only on a public task. Public task content is editable by organization members.
- Choose permissions only from what the user said. Do not infer them.

## Deleting tasks

`delete_task` deletes a task permanently, and the deletion cannot be undone.

- Delete only when the user explicitly asks to delete that task.
- Read it with `get_task` first, show the user its title and due date, and get their confirmation for each task before you delete it.
- Never delete a task to tidy up, to replace it, or because it looks like a duplicate. A task that was abandoned can be set to `canceled` instead; offer that when it fits.

## Handling errors

Read the error before you retry; it names the field that was rejected. Never retry an unchanged call after an invalid-input error. The rejection will repeat.

- **`... must be provided together`:** you sent half of a type and ID pair. Send both, or neither.
- **`... cannot be combined with ...`, `... cannot both be set` or `... not both`:** you sent a replacing field with its add or remove form, or a value with its clear flag. Pick one.
- **`nothing to update`:** every field was empty. Decide what actually changes first.
- **`... not a valid id` or a not-found error on a linked record:** re-resolve the record with its search tool and copy the ID from the result.
- **`tags must reference task tags in the current organization`:** the tag ID is not a task tag in this organization.

Never type a task, user or record ID from memory. Copy it from a tool result.
