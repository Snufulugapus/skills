---
name: to-prd
description: Synthesize the current conversation into a Product Requirements Document committed as a file in the repo. Use after a design discussion (often following /grill-me) when decisions are resolved and you're ready to lock in the spec for a feature, RC, or task.
---

Synthesize the preceding conversation into a PRD. Do not interview the user — the conversation already happened. If it didn't, say so and stop.

# Procedure

1. **Check context depth.** Scan the conversation. If it lacks concrete decisions about the problem, solution, rough module boundaries, or scope, stop and suggest the user run `/grill-me` first. Do not try to interview inline.

2. **Explore the codebase.** Use Explore / Glob / Grep to understand current state: what already exists, what needs to change, what patterns to reuse. No user input required for this step.

3. **Sketch modules.** Identify the major modules affected or introduced. Prefer deep modules (substantial functionality behind simple, testable interfaces) over shallow wrappers. Share the sketch in one message and confirm with the user before writing.

4. **Find project conventions.** Read the project's `CLAUDE.md` (and any nested ones). Look for stated conventions about where PRDs live, how they're named, and any project-specific template additions. If nothing is documented, ask the user once.

5. **Write the PRD file.** Use the template below. No file paths, no code snippets — they rot. Keep implementation decisions at the module/interface level.

6. **Stop.** Do not open GitHub issues, create branches, commit, or push. The user controls git.

# Template

```markdown
# <Feature name>

## Problem Statement
One paragraph from the user's perspective. What's broken or missing, and why does it matter?

## Solution
One paragraph describing the user-facing resolution. What will exist after this ships?

## User Stories
Numbered list in "As a [actor], I want [feature], so that [benefit]" format. Cover the happy path and material edge cases.

1. As a ..., I want ..., so that ...
2. ...

## Implementation Decisions
Module boundaries, interfaces, schema or API contracts, architectural choices. Reference existing patterns where relevant. No file paths, no code.

## Testing Decisions
How to verify this works end-to-end. Which modules need coverage. Reference prior testing patterns in the codebase.

## Out of Scope
Explicitly excluded functionality. Things someone might expect but this spec is not addressing.

## Further Notes
Additional context, open questions flagged for later, links to related material.
```
