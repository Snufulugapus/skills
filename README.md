# Snufulugapus / skills

My personal [Claude Code skills](https://code.claude.com/docs/en/skills). The engineering pipeline is adopted verbatim from [mattpocock/skills](https://github.com/mattpocock/skills); custom skills cover Codex-delegated PR review, config auditing, and content research.

## Install

Clone into your Claude Code skills directory:

```bash
git clone https://github.com/Snufulugapus/skills ~/.claude/skills
```

(If you already have skills there, clone elsewhere and copy the directories you want.)

## Layout

```
~/.claude/skills/
│
├─ Engineering pipeline (from mattpocock)
│   ├─ setup-matt-pocock-skills        per-repo bootstrap
│   ├─ grill-with-docs              ┐
│   ├─ to-prd                       │  the chain
│   ├─ to-issues                    │
│   └─ tdd                          ┘
│
├─ Other engineering (from mattpocock)
│   ├─ diagnose                        debug loop
│   ├─ prototype                       throwaway design
│   ├─ improve-codebase-architecture
│   └─ handoff                         context compaction
│
├─ PR review (mine)
│   ├─ request-codex-review
│   └─ triage-pr-review
│
├─ Productivity (from mattpocock)
│   └─ grill-me
│
└─ Tooling & Research (mine)
    ├─ audit
    └─ youtube-transcript
```

> Folders are flat on disk — Claude Code's user-skill loader only scans the top level of `~/.claude/skills/`. The groupings above are logical only, surfaced through this README.

---

## Engineering pipeline

The Matt Pocock skills are designed to work as a chain. Per-repo bootstrap via `setup-matt-pocock-skills` is required before the chain works end-to-end.

```
       setup-matt-pocock-skills          (once per repo)
                  │
                  ▼
  grill-with-docs ──▶ to-prd ──▶ to-issues ──▶ tdd
  ───────────────     ──────     ─────────     ───
  challenge plan,     PRD →      vertical      red → green
  update glossary     GH issue   slices        → refactor
  + ADRs              w/ label
```

| Skill | What it does |
|---|---|
| **setup-matt-pocock-skills** | Per-repo bootstrap. Scaffolds `docs/agents/{issue-tracker,triage-labels,domain}.md` and an `## Agent skills` block in `CLAUDE.md`. Run once per repo. |
| **grill-with-docs** | Grilling session that challenges your plan against the existing domain model, sharpens terminology, and updates `CONTEXT.md` + ADRs inline as decisions crystallise. |
| **to-prd** | Synthesize the current conversation into a PRD and publish to the project issue tracker with a `ready-for-agent` label. No interview — just synthesizes what's been discussed. |
| **to-issues** | Break a plan, spec, or PRD into independently-grabbable issues using tracer-bullet vertical slices. |
| **tdd** | Test-driven development with a red-green-refactor loop. One vertical slice at a time. Bundled docs: `deep-modules.md`, `interface-design.md`, `mocking.md`, `refactoring.md`, `tests.md`. |

## Other engineering

| Skill | What it does |
|---|---|
| **diagnose** | Disciplined diagnosis loop for hard bugs and performance regressions: reproduce → minimise → hypothesise → instrument → fix → regression-test. |
| **prototype** | Build a throwaway prototype to flesh out a design — runnable terminal app for state/business-logic questions, or several radically different UI variations toggleable from one route. |
| **improve-codebase-architecture** | Find deepening opportunities in a codebase, informed by the domain language in `CONTEXT.md` and the decisions in `docs/adr/`. Run every few days on active projects. |
| **handoff** | Compact the current conversation into a handoff document so another agent can continue the work. |

## PR review

| Skill | What it does |
|---|---|
| **request-codex-review** | After Claude opens a PR, delegate a code review to the Codex CLI plugin and post findings back to the PR. Version-checks Codex first, briefs the rescue agent so Codex itself never tries to access GitHub from inside its sandbox, signs the comment with a `**Codex review (delegated by Claude Code):**` prefix. Defaults to a standard defects + scope review; opt-in **adversarial** mode for PRs that lock in load-bearing architecture. |
| **triage-pr-review** | Reviewer-agnostic triage for PR review findings (Codex, Claude self-review, human reviewers). Reads the project's calibration policy from `CLAUDE.md`. In calibration phase, summarizes findings and stops. In delegated phase, applies trivials within a strict allowlist, pushes back on findings that don't apply (with quoted code + reason), escalates judgment calls, and tracks deferred items in `docs/followups.md`. Never auto-fixes auth/billing/Stripe/security findings. |

## Productivity

| Skill | What it does |
|---|---|
| **grill-me** | Get relentlessly interviewed about a plan or design until every branch of the decision tree is resolved. Use for non-code work; for code work, prefer `grill-with-docs`. |

## Tooling & research

| Skill | What it does |
|---|---|
| **audit** | Full inventory of Claude Code config (plugins, MCP servers, agents, skills, commands, hooks) with update checks. Supports `--skip-updates`, `--user-only`, `--verbose` flags. |
| **youtube-transcript** | Fetch the transcript of a YouTube video or Short (via `yt-dlp`) and load it into the conversation for summarization, quoting, or analysis. |

---

## Credits

The following skills are adopted **verbatim** from [mattpocock/skills](https://github.com/mattpocock/skills) — credit and rationale belong to Matt:

- Engineering pipeline: `setup-matt-pocock-skills`, `grill-with-docs`, `to-prd`, `to-issues`, `tdd`
- Other engineering: `diagnose`, `prototype`, `improve-codebase-architecture`, `handoff`
- Productivity: `grill-me`

See Matt's README for the design rationale and the rest of his pipeline.
