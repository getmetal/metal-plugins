# Permissions And Run Policy

Use this reference when reasoning about who can see, run, or build a workflow, or when a workflow or run appears missing. The environment-and-connection guidance in the SKILL builds on this model. On a server with org-selection tools the caller acts as the Metal Team actor these clauses describe: visibility, authoring, and run-policy gates pass, and private-run read restrictions do not apply; HITL review authority is the exception (see `references/human-review.md`).

## General Access And Visibility

- General Access, stored as `visibility`, is the workflow-definition access boundary. New workflows default to Restricted (`private`). An existing workflow with missing visibility remains effectively public for compatibility.
- Public or missing visibility grants every same-org member definition read, discovery, and manual-run access. It does not grant edit access.
- A Restricted workflow is readable by its creator, a user or team in `sharedWith`, an org admin or owner, or the Metal Team. A Viewer share grants read and run access. An Editor share also grants edit access. A legacy share with missing access derives as Editor.
- `runVisibility` (`public` or `private`) governs who can read a new run, not who can start it. An explicit value is copied onto the run and can be overridden per run. When it is missing, the run derives the workflow's effective General Access at creation and records `visibilityInherited`.
- General Access, `runVisibility`, and `sharedWith` are set in the workflow builder UI; no building tool changes them. The one exception is `run_workflow`, which accepts a per-run `visibility` override for the run it starts. Route definition access and sharing changes to the UI.

## Authoring Policy

- The creator, a direct or team Editor, an org admin or owner, or the Metal Team can edit a same-org workflow through the building tools. Public General Access and Viewer shares are read-only. PowerUser has no blanket edit bypass.
- Internal autonomous callers, including workflow runs, cannot use the authoring surface.
- Source-managed global workflows and deprecated workflows reject authoring writes.

## Run Policy

- Anyone with definition read access can run a non-deprecated workflow manually.
- A deprecated workflow runs for nobody.
- Email, event, and webhook automation is paused only when `trigger.enabled` is explicitly `false`. Schedule automation is paused per schedule when that schedule's `enabled` is explicitly `false`. An absent or `true` value is enabled, and a pause does not block a manual run.
- Global workflows never fire automatically, regardless of their trigger and pause flags.

## Run Read Access

- For an organization run whose parent still exists, the run never reaches a wider audience than its parent workflow. A `public` run is readable by anyone who can access the workflow. Public runs whose parent was deleted and global workflow runs retain their compatibility list behavior.
- An explicitly `private` run triggered by a user is readable by that user (`triggeredBy`). A system-triggered private run falls back to workflow read access.
- An inherited private run follows the workflow audience. Historical runs are not rewritten when General Access changes.
- While a run is at `AWAITING_APPROVAL`, an active reviewer designated on the current human-review step can read the run even when normal run visibility would deny access. This applies to an eligible static reviewer or the assigned reviewer; an undesignated review step grants no extra read access.
- Metal Team and internal service callers have defined read bypasses.

## Not Found Can Mean Denied

A 404 from a workflow read or building tool can be a policy denial rather than a missing workflow: the workflow exists but is not accessible to the current org or actor. Building tools also return 404 for a workflow that exists but fails the org-building check. Confirm org access before concluding a workflow does not exist; see Connection in the SKILL and Error Semantics in `building-tools.md`. For a caller whose visibility gates are bypassed (a Metal Team actor on a server with org-selection tools), read a 404 as the wrong org bound or a genuinely missing workflow rather than a policy denial. A global workflow managed by version control returns 403 ("managed by version control") and cannot be edited through the API.
