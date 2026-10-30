---
name: org-skills
description: Applies when a task might follow a firm-specific process, template, checklist, rubric or house style, such as a memo, report or deck in the firm's format or branding, a recurring deliverable like an earnings email or board overview, a screening or diligence checklist, a tracker or dashboard update, or a recurring procedure like deal intake; check the organization's Metal skill library with list_skills, load a matching skill with get_skill, and follow it. Also applies when the user asks which skills exist. Creating or editing skills is only for an explicit request.
---

# Metal Org Skills

A Metal organization keeps its own skills in a skill library: the firm's procedures, templates, rubrics and house styles, written for Metal's in-app assistant. The Metal MCP server exposes that library through `list_skills`, `get_skill` and `get_skill_file`. This skill says when to check the library and how to use what you find.

## When to check the library

Check it once, before you start, when the task is one a firm may do its own way:

- writing a memo, one-pager, email or summary that may have a house format or template;
- a document, deck or report that may follow the firm's branding or style guide;
- a recurring deliverable, such as an earnings summary email, an investor brief or a board overview;
- screening, scoring or diligence that may follow a rubric or checklist;
- updating a tracker list or dashboard that the firm keeps in a set way;
- a recurring procedure, such as deal intake, a pipeline review or a weekly update;
- an analysis built on the firm's own data systems, where a skill may name the source or method to use;
- the user says "our process", "our template" or "how we do this", or names a skill;
- the user asks what skills exist.

Skip the check for a plain lookup, such as finding a company or reading a document, unless the user asks for the firm's way of doing it.

## Find a skill with list_skills

- Pass `query` with one or two distinctive words from the task, such as `memo`, `screening` or `intake`. The match is a case-insensitive substring of the name or description, not a semantic search. If the first word finds nothing, try another.
- Omit `query` to list every skill you can see.
- Results come 25 at a time by default; `limit` raises that to at most 100. When `pagination.hasMore` is true, page with `offset` before you conclude that no skill matches.
- Each result has a `name`, a `description` cut to 200 characters (`descriptionTruncated` is true when it was cut), a `visibility` of org-wide, private or shared, and the flags described under "Skill flags".
- Choose the skill whose description matches the task. If two fit equally, name both and ask the user which to use.
- If nothing matches, say that you checked the firm's skill library, and continue without it.

## Load a skill with get_skill

- Call `get_skill` with the exact `name`. A name resolves to the user's own skill first, then to a firm-wide skill of that name, then to a skill shared with the user.
- `content` is the skill's SKILL.md body. Follow it for the firm's process and format in this task.
- `companionFiles` lists the files bundled with the skill, each with a `path`. When `content` refers to one, read it with `get_skill_file`, passing the skill `name` and that `path`. A file over 1 MiB comes back cut, with `truncated` set to true.
- `assets` lists binary files. An asset has a `downloadUrl` when one could be created; the URL expires. Fetch an asset only when the skill's instructions need it.
- A skill whose content is over 96,000 characters can't be loaded. Tell the user that it is too large to load here.

## Skill flags

- `disableModelInvocation: true` means the firm wants the skill used only when a person asks for it. Don't apply it on your own. You may mention that it exists, and apply it when the user asks for it by name.
- `chainNext` names skills the author meant to follow this one. Load the next skill only when the task goes on to that step.
- `allowedTools` lists the tools the skill was written for in Metal's app. See the next section.

## Tools the skill names that you don't have

Org skills are written for Metal's in-app assistant, which has tools that this MCP server does not expose. A skill can tell you to call a tool by a name you don't have, or list one in `allowedTools`.

- Check each tool the skill names against the Metal tools available to you. Use a Metal tool in its place only when it does the same job. A similar name is not enough.
- When a step needs a tool you don't have, do the steps you can, and tell the user which step you skipped and why. Don't improvise a substitute that changes what the step produces.

## Creating or editing skills

`save_skill`, `add_skill_file` and `remove_skill_file` change the firm's library. Use them only when the user explicitly asks you to create or edit a skill, and read the skill with `get_skill` first.
