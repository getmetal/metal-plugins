# Data Analysis Orchestrator

Use this reference when a workflow uses the `Data Analysis Orchestrator` agent. Take the exact agent name from `list_workflow_building_options` kind `agents`.

## Agent Contract

- The orchestrator does not research, plan, fetch data, or call platform tools directly.
- Its declared tools are `spawn_subagent` and `download_file`, in addition to standard agent tools and mounted connections. Its only delegate is `Task Supervisor`.
- It delegates research through `spawn_subagent` with `agent: "Task Supervisor"`. The `input` holds the request summary, subject, prioritized sources, time periods, units, and other hard constraints.
- Only the connections passed in `connections: [{"name": "<available connection name>"}]` reach the delegate. Omitting the field does not inherit platform access.
- The platform connection is auto-appended to the orchestrator's own agent step like any other, and its tools are mounted on the orchestrator's belt. Only the agent's instructions keep platform work on the delegate path; nothing enforces it. Set `disableAutoPlatformConnection: true` on the step when you need that separation to be structural rather than prompt-deep.
- It presents the delegated findings with citations and limitations. It uses `download_file` for an existing requested file and claims creation only when the delegate returns a verified artifact.

## Agent File Attachments

Workflow agent file attachments are an agent-runtime concern.

- Resolved `dataEntity` and `dataEntityMulti` workflow inputs have file-shaped objects with `id`, `name`, and `fileExtension`.
- The workflow runner scans resolved inputs for that shape and stores the IDs on the agent context with `SetAttachedFiles`.
- `attachedFiles` is a special key inside the step's `contextVariables`, which is authorable here like any other context variable. The runner renders it, appends the resulting data entity ID or IDs to the same runtime attached-file list, and never stores it as an ordinary context variable.
- The workflow runtime resolves that list into file inputs with metadata and presigned URLs for the agent and file-aware tools.
