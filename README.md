# Claude Code Skills

A collection of [Agent Skills](https://docs.claude.com/en/docs/claude-code/skills) I use with Claude Code.

Several of the engineering skills below are adopted (verbatim) from [mattpocock/skills](https://github.com/mattpocock/skills). Credit to Matt for the design — see his repo for the rationale and the rest of his pipeline.

## Install

Clone this repo into your Claude Code skills directory:

```
git clone https://github.com/Snufulugapus/skills ~/.claude/skills
```

(If you already have skills at `~/.claude/skills/`, clone elsewhere and copy the directories you want.)

## Engineering

The engineering skills are designed to work as a pipeline: **`grill-with-docs` → `to-prd` → `to-issues` → `tdd`**. Per-repo bootstrap via `setup-matt-pocock-skills` is required before the chain works end-to-end.

- **setup-matt-pocock-skills** — Per-repo bootstrap. Scaffolds `docs/agents/{issue-tracker,triage-labels,domain}.md` and an `## Agent skills` block in `CLAUDE.md`/`AGENTS.md`. Run once per repo before using the rest of the engineering stack. *(from mattpocock/skills)*
- **grill-with-docs** — Grilling session that challenges your plan against the existing domain model, sharpens terminology, and updates `CONTEXT.md` + ADRs inline as decisions crystallise. *(from mattpocock/skills)*
- **to-prd** — Synthesize the current conversation into a PRD and publish it to the project issue tracker with a `ready-for-agent` label. No interview — just synthesizes what you've already discussed. *(from mattpocock/skills)*
- **to-issues** — Break a plan, spec, or PRD into independently-grabbable issues using tracer-bullet vertical slices. *(from mattpocock/skills)*
- **tdd** — Test-driven development with a red-green-refactor loop. Builds features or fixes bugs one vertical slice at a time. Bundled docs: deep-modules, interface-design, mocking, refactoring, tests. *(from mattpocock/skills)*
- **diagnose** — Disciplined diagnosis loop for hard bugs and performance regressions: reproduce → minimise → hypothesise → instrument → fix → regression-test. *(from mattpocock/skills)*
- **prototype** — Build a throwaway prototype to flesh out a design — runnable terminal app for state/business-logic questions, or several radically different UI variations toggleable from one route. *(from mattpocock/skills)*
- **improve-codebase-architecture** — Find deepening opportunities in a codebase, informed by the domain language in `CONTEXT.md` and the decisions in `docs/adr/`. Run every few days on active projects. *(from mattpocock/skills)*
- **request-codex-review** — After Claude opens a PR, delegate a code review to the Codex CLI plugin and post findings back to the PR. Version-checks Codex first, briefs the rescue agent so Codex itself never tries to access GitHub from inside its sandbox, signs the comment with a `**Codex review (delegated by Claude Code):**` prefix. Defaults to a standard defects + scope review; supports an opt-in **adversarial** mode that has Codex challenge design choices and assumptions instead — useful for PRs that lock in load-bearing architecture, but overkill for routine implementation work.
- **triage-pr-review** — Reviewer-agnostic triage for PR review findings (Codex, Claude self-review, human reviewers). Reads the project's calibration policy from `CLAUDE.md`. In calibration phase, summarizes findings and stops. In delegated phase, applies trivials within a strict allowlist, pushes back on findings that don't apply (with quoted code + reason), escalates judgment calls, and tracks deferred items in `docs/followups.md`. Never auto-fixes auth/billing/Stripe/security findings.

## Productivity

- **grill-me** — Get relentlessly interviewed about a plan or design until every branch of the decision tree is resolved. Use for non-code work; for code work, prefer `grill-with-docs`. *(from mattpocock/skills)*
- **handoff** — Compact the current conversation into a handoff document so another agent can continue the work. *(from mattpocock/skills)*

## Tooling & Setup

- **audit** — Full inventory of Claude Code config (plugins, MCP servers, agents, skills, commands, hooks) with update checks.

## Content & Research

- **youtube-transcript** — Fetch the transcript of a YouTube video or Short (via `yt-dlp`) and load it into the conversation for summarization, quoting, or analysis.
