---
name: running-routines
description: Use when the user asks to run, start or kick off a Metal Routine, or to run one on a note, email, file, record or pasted text, and to check a Routine run's status, answer its pending question or permission, or read its output.
---

# Running Metal Routines

A Metal Routine is a saved objective that Metal runs as its own Chat session. This skill covers one run from start to output: find the Routine, start it with the right input, check its status, answer what it asks, and read what it produced.

Creating or editing a Routine, and stopping a run, happen in the Metal app. No Metal tool does them.

## What a run sees

A run sees its Routine's objective and the input you pass to `start_routine_run`: `text` and `references`. It does not see this conversation. Put everything the run needs into that input.

## Start a run

1. **Find the Routine.** If the user gives a Metal Routine link, its path ends in `/routines/<routineId>`; use that ID. Otherwise call `list_routines` with `view: "mine"`, then with `view: "shared"`, and follow `cursor` in each view until you find it. Never ask the user for a Routine ID.
2. **More than one Routine could match the user's words?** Ask the user which one, by name, and end the turn. Start nothing.
3. **Call `get_routine` and read the objective before `start_routine_run`.** This step is required. The objective says what a run takes. Build `text` and `references` from it and from the conversation.
4. **Check `canRequestRun`.** If it is false, do not start. The Routine cannot be started by hand for this user, for example because it runs only on events. Tell the user, and give `routineUrl` when the response has one.
5. **If input that the objective requires is missing or ambiguous, ask the user here and wait for the answer before you call `start_routine_run`.** Do not start a run and expect it to collect the missing input.
6. **Call `start_routine_run`** with `routineId`, a new `requestId`, and the input.

### Build the input

- `text` carries the instructions and any pasted content the run needs, such as the body of a note or email. Write it so that someone with no access to this conversation can act on it.
- `references` attaches Metal records. Each entry is `{"resourceType": ..., "resource": <24-character hex ID>}`. The types are `document`, `company`, `deal`, `activity`, `task` and `data_entity`.
- A file found with `search_documents` or `get_document` is a `data_entity`. A company comes from `search_companies`, a deal from `search_deals`, a meeting or other interaction from `get_activities`, and a task from `list_tasks` or `search_tasks`.
- Copy every ID from a tool result. Never type one from memory. The same record cannot appear twice.
- The run needs `text`, `references`, or both. The serialized input must be at most 128 KiB.

## Ambiguous names: ask, every time

Starting the closer match and offering to run the other one is guessing, and a started run cannot be taken back.

| Thought | Reality |
|---|---|
| "One name matches the user's words exactly" | Another name also contains them. Ask. |
| "I'll run this one; they can tell me if they meant the other" | The run has already started. Ask first. |
| "I read both objectives and one fits better" | The user chooses, not you. Ask. |

## The requestId makes a start safe to retry

`requestId` is an identity that you generate, 1 to 128 characters. Use a fresh UUID for each run the user asks for.

- Keep the `requestId` and the exact input until you have a `runId`.
- If `start_routine_run` times out, errors without a clear answer, or you are not sure whether it started, call it again with the same `requestId`, `routineId`, `text` and `references`. Metal returns the original run instead of starting a second one.
- The same `requestId` with any change to the Routine or input fails with "Routine request identity was already used with different input". Do not change the input under an old ID.
- A new deliberate request from the user is a new run and needs a new `requestId`. Never generate a new ID only to retry an uncertain start.

## After the start

The receipt means Metal durably accepted the run. It does not mean the run finished. Report the `runId`, and `routineUrl` or `sessionUrl` when present. `sessionUrl` appears only after the run launches its Chat. Never build a Metal link yourself.

## Check status

Call `get_routine_run` with the `runId`. It returns the current state at once; it does not wait. To find a run without its ID, call `list_routine_runs` with `view: "mine"` and with `view: "shared"`. The mine view has separate attention, active and history sections, each with its own cursor.

`run.status` is one of:

- `starting` or `in_progress`: the run is working. Check again later, or tell the user it is still running.
- `needs_attention`: the run is waiting on a question or a permission. See `pendingRequests` below.
- `stopped`: the run is over. `terminal` is true, and `run.stopReason` says how it ended: `completed`, `incomplete`, `failed`, `skipped` or `user_stopped`. `run.failureCode` and `run.failureMessage` add detail when present.

`stopped` with a stop reason other than `completed` is not a success. Say how it ended.

## Answer a pending question or permission

A pending prompt is a decision that belongs to the user. Answer it only with the user's actual answer or decision. Never infer one from the objective, the conversation or what seems likely, and never answer one because the status is pending.

1. Read the prompt from `get_routine_run` `pendingRequests`. Each entry has its own `requestId`, a `kind`, and `supported` and `canRespond` flags.
2. If `supported` is false (`kind` is `secret_input` or `secret_approval`) or `canRespond` is false, you cannot answer it here. Send the user to the run's `sessionUrl`.
3. Show the user the question and its options, or the permission and the tool it names, and wait for their reply.
4. Call `respond_to_routine_run` with `runId`, the prompt's `requestId` (not the start `requestId`) and `kind`.

For a `question` prompt:

- Answer every question in the prompt. `answers` maps each question `id` to an object with both keys `optionIds` and `text`. Fill at least one of them; pass `"text": ""` or `"optionIds": []` for the one you do not use.
- Use only option `id` values from that question. A question whose `multiSelect` is false takes at most one option.
- `text` is at most 2000 characters.
- Do not pass `decision` with a question response.

For a `permission` prompt:

- `decision` is `approve` or `deny`, and covers only this one request. There is no standing approval. Do not pass `answers`.
- A permission prompt names the tool, not the full target of the action. If the user cannot tell what they are approving, send them to `sessionUrl` instead.

The response receipt means Metal accepted the answer. It does not mean the run resumed or finished. If the call times out or its outcome is uncertain, read `get_routine_run` before you send anything again. "Routine run is no longer actionable" means the run is no longer active or a stop was requested.

## Read the output

When `get_routine_run` shows `outputAvailable: true`, call `get_routine_run_output` with the `runId`.

- `content` is the run's stored result text, with `citations`. It is the run's original result, not later conversation in its Chat.
- The response holds at most `maxChars` characters, 6000 by default and 24000 at most. When `nextCursor` is present, call again with it as `cursor` to read the rest. If the call fails with "Stored output changed; restart without a cursor", read again from the start without `cursor`.
- `artifacts` lists files with `name`, `contentType`, `size` and a temporary `url`. Present each `url` to the user as a download link. The URLs expire after about one hour; read the output again to get fresh ones. If a file has no `url`, say the download is not available and give `sessionUrl` instead. Do not look for another way to reach the file.
- Status and output are separate. A run can be `stopped` with no stored output. Then explain how it ended and that it stored no result.
