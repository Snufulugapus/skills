# Claude Code Skills

A collection of [Agent Skills](https://docs.claude.com/en/docs/claude-code/skills) I use with Claude Code.

## Install

Clone this repo into your Claude Code skills directory:

```
git clone https://github.com/Snufulugapus/skills ~/.claude/skills
```

(If you already have skills at `~/.claude/skills/`, clone elsewhere and copy the directories you want.)

## Planning & Design

- **grill-me** — Get relentlessly interviewed about a plan or design until every branch of the decision tree is resolved.
- **to-prd** — Synthesize the current conversation into a Product Requirements Document committed as a file in the repo. Pairs well with `grill-me`.

## Tooling & Setup

- **audit** — Full inventory of Claude Code config (plugins, MCP servers, agents, skills, commands, hooks) with update checks.

## Code Review

- **request-codex-review** — After Claude opens a PR, delegate an *adversarial* code review to the Codex CLI plugin and post findings back to the PR. Codex is briefed to challenge design choices, tradeoffs, and assumptions — not just hunt defects. Version-checks Codex first, briefs the rescue agent so Codex itself never tries to access GitHub from inside its sandbox, signs the comment with a `**Codex review (delegated by Claude Code):**` prefix.
- **triage-pr-review** — Reviewer-agnostic triage for PR review findings (Codex, Claude self-review, human reviewers). Reads the project's calibration policy from `CLAUDE.md`. In calibration phase, summarizes findings and stops. In delegated phase, applies trivials within a strict allowlist, pushes back on findings that don't apply (with quoted code + reason), escalates judgment calls, and tracks deferred items in `docs/followups.md`. Never auto-fixes auth/billing/Stripe/security findings.

## Content & Research

- **youtube-transcript** — Fetch the transcript of a YouTube video or Short (via `yt-dlp`) and load it into the conversation for summarization, quoting, or analysis.
