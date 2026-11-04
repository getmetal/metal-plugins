---
name: metal-product-knowledge
description: "Use when the user asks how to do something in Metal, what a Metal feature, screen or setting does, whether Metal supports a capability, or about the Metal API or MCP server. Answers come from the public docs at https://docs.metal.ai, read before answering."
---

# Metal Product Knowledge

Answer questions about the Metal product from Metal's public documentation at https://docs.metal.ai, not from prior knowledge. The docs hold the user guide under `/help`, the developer guides, the API reference and the MCP server docs.

## When to use

- The user asks how to do something in Metal: "How do I create a dashboard?", "How do I invite a teammate?"
- The user asks what a Metal feature, screen or setting does: "What is enrichment?", "What does the Active Pipeline show?"
- The user asks whether a capability, workflow step or integration is available: "Can a workflow send email?"
- A developer asks about the Metal API, its endpoints or the Metal MCP server.

Do not use it for:

- The user's own firm data, such as companies, deals, people, documents and funds. Use the Metal tools for that.
- Doing things in Metal. This skill finds and explains; it never runs workflows, edits records or changes data.
- Live failures ("it's broken"). Answer from the docs if they cover it, but this is not a substitute for Metal support.

## Read the docs

The Metal tools do not search the docs. Use this client's own web fetch tool.

1. Fetch the index at https://docs.metal.ai/llms.txt. It lists every page with its URL and a one-line summary. User-guide pages are under `https://docs.metal.ai/help/`.
2. Pick the pages whose summaries match the question. Every page is available as Markdown at its `.md` URL, as the index lists it, for example https://docs.metal.ai/help/investor-relations.md.
3. Read the matching page before you answer. A summary line in the index is not enough. When the question spans features, read each page it touches.
4. Answer from the page content and cite each page you used by its URL, without the `.md` suffix.
5. Never present remembered details as facts from the docs. If the pages you read do not answer the question, say the docs do not cover it.

If this client has no web fetch tool, or the docs cannot be reached, say that the official docs cannot be read from here. Point the user to https://docs.metal.ai/help, or to Metal support when the app itself has a problem. Do not answer documentation questions from memory: without the docs you cannot check them, and an ungrounded answer is worse than none.

## Capability questions

The docs explain how features work. They are not a complete catalog of what the user's organization can use. For whether a specific tool, workflow step, connection or integration is available, check the Metal tools that report it:

1. `list_workflow_building_options` with `kinds` such as `tools`, `connections`, `agents`, `models` or `events` lists the workflow-authoring values valid for the user's organization. It is the list of what a workflow step can use.
2. `get_workflow` and `get_workflow_step` show how a real workflow the user points to uses a capability.
3. `list_connected_mcp_tools` lists the outside MCP servers the user has connected in Metal, such as Databricks or S&P Capital IQ, and their tools.

Rules for the answer:

- Never tell the user a capability is unavailable because a docs page does not mention it. Absence from a page is not evidence of absence.
- When `list_workflow_building_options` covers the question, its omission of a capability means the capability is not available to workflows in the user's organization.
- Otherwise, when neither the docs nor these tools confirm the capability, say it could not be verified and name what you checked. Do not say it is unsupported.
- A limit that a docs page states plainly is settled. Report it as the docs state it and cite the page.
- Also do not invent a capability that a page only implies.

## Common mistakes

- Answering from memory without fetching a single page. The docs change; your memory lags.
- Answering from the index summary instead of reading the page.
- Denying a capability because the docs never mention it.
- Quoting the docs without citing the page URL.
