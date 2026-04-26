---
name: request-codex-review
description: Use after Claude opens a PR to have Codex review the diff and post findings back to the PR. Verifies the Codex CLI is current before delegating; briefs the codex:codex-rescue agent so Codex itself never tries to access GitHub from inside its sandbox; posts a single structured comment with the standard AI-disclaimer prefix; verifies the comment landed before reporting success. Auto-trigger when Claude has just pushed a branch and run `gh pr create` (or after Spencer / a teammate has opened a PR you're about to review).
---

# request-codex-review

Run a Codex code review against a specific PR and post the findings back to it. Returns when the review comment is verified live on the PR; does not triage — that's `triage-pr-review`'s job.

## When to use

- Right after `gh pr create` — Claude just opened a PR and wants Codex's independent take before any human reviews it.
- After a teammate's PR is opened and you (Claude) want to delegate review rather than do it yourself.
- Re-run is allowed: a second invocation just adds a second Codex comment. `triage-pr-review` always picks the most recent.

Do NOT use this skill for general "review my code" requests outside of a PR context — for that, use `/codex:review` directly against working-tree state.

## Modes

The skill runs in **standard** mode by default. **Adversarial** mode is an opt-in stance change for PRs where you want Codex to challenge the design itself, not just hunt defects.

| Mode | When to use | Codex's stance |
|---|---|---|
| **standard** (default) | Implementation of a locked PRD; scaffolding; small/mechanical PRs; anything where the design has already been grilled | Defects, scope contradictions, security, framework correctness, a11y. Mention if a design choice is good. |
| **adversarial** | PRs that lock in load-bearing architecture (data model, API shape, async pattern, auth flow); PRDs that didn't get fully grilled; anywhere being wrong is expensive to undo | Challenge the chosen approach itself. Question assumptions, tradeoffs, real-world failure modes. Implementation defects are last priority. |

Trigger adversarial explicitly: invoke as `request-codex-review adversarial` (or `--adversarial`, or any user phrasing like *"adversarial review of PR #N"* / *"have Codex argue with the design"*). If the user doesn't say so, run standard.

Most v1 marketplace PRs (auth wiring, UI primitives, table CRUD) should run standard. Adversarial earns its keep on PRs like the Gateway invoke loop, the Stripe Connect cost model, or the daily-rollup state machine — places where a wrong choice means a rewrite.

## Quick start

```text
Claude has opened PR #N on <repo>. Invoke request-codex-review.
```

The skill walks through five steps below silently and reports a one-paragraph summary at the end with the posted comment URL.

## Step 1 — Preflight (verify Codex CLI is current)

The Codex plugin's defaults can drift past the installed CLI binary, producing opaque "model not supported" or "requires a newer version" errors that look like auth failures. Catch this in 2 seconds before delegating, instead of after a 10-minute agent run.

Try the plugin's own setup command first:

```bash
/codex:setup --json
```

If that's not available or returns insufficient detail, fall back to:

```bash
codex --version
npm view @openai/codex version
```

If installed < latest, upgrade:

```bash
npm i -g @openai/codex@latest
```

**Windows EBUSY during upgrade** — `codex.exe` or the bundled `rg.exe` is locked. Common causes (in order of likelihood):

1. Codex Desktop app is running. Tell the user to fully quit it (system tray → Quit, not just close window). Retry.
2. A stale `node` process running `app-server-broker.mjs` from a prior `codex:codex-rescue` run. Find via `Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like "*app-server-broker*" }` and `Stop-Process` the PID. Retry.
3. Windows Defender holding a persistent handle. Reboot.

Never loop the upgrade attempt past 2 retries — surface the cause and ask the user to reboot.

## Step 2 — Gather context (silent)

Don't narrate these; gather then report.

```bash
gh pr view <PR#> --json number,title,body,baseRefName,headRefName,headRefOid,baseRefOid,additions,deletions,changedFiles,files
git fetch origin <branch>
git checkout <branch>
git diff <baseRefOid>..<headRefOid> > /tmp/pr<#>.diff
```

Also read:

- The implementing PRD if the PR description references one — typically `docs/prds/<slug>.md`.
- The repo's `CLAUDE.md` — especially any "Locked v1 decisions", "Things to never do", and "PR review workflow" sections. These define what's in/out of scope so Codex doesn't flag intentional omissions.
- For foundation/auth/security/migration PRs, read the **full** changed files (not just diff hunks). A diff hunk doesn't show the surrounding context Codex needs to spot, e.g., a missing RLS policy or a misplaced auth guard.

## Step 3 — Delegate to `codex:codex-rescue` with the locked briefing

This is the section that previously failed. Codex's sandbox cannot reach a private GitHub repo — but the rescue agent (running outside that sandbox) can. The agent must do the git/gh work; Codex itself only analyzes the diff text we hand it.

Invoke the agent with this brief structure:

> **You misunderstood this last time, so to be explicit:** Codex itself does NOT run `git` or `gh`. Those calls happen *outside* the sandbox in your own shell. Codex's only job is to analyze a diff/code I hand it as text and return review findings. You then post those findings to the PR via `gh` from your own shell.
>
> **The flow:**
> 1. You (rescue agent, in your shell) check out the branch and capture the diff (already done above; just reference the gathered text).
> 2. You feed the gathered diff + full files + scope context to Codex via the codex-companion runtime as a single prompt. Wait for Codex to finish in-process — do not fire-and-forget.
> 3. You (in your shell) post the findings to the PR via `gh pr review <PR#> --comment --body "..."` and verify the count went up.
>
> **Codex's prompt should include (standard mode — default):**
> - The PR's stated scope (in/out per the PRD).
> - The repo's locked decisions and "things to never do" from `CLAUDE.md`.
> - Specific focus areas: correctness, security (auth/env/secrets), framework correctness (Next.js / Drizzle / Supabase / etc. as relevant), schema/migration hygiene, accessibility, scope contradictions vs PRD/CLAUDE.md.
> - Instruction to ground every finding with `file:line` and a short code quote.
> - Codex can call out good things, but priority is finding issues.
>
> **Adversarial mode override (only when explicitly invoked — see Modes section).** Replace the focus-areas bullet above with this paragraph at the top of Codex's prompt, verbatim, and reorder priorities:
>
> > "Position this as a challenge review. Question the chosen implementation, design decisions, tradeoffs, and assumptions — this is not a stricter pass over implementation defects. For each significant choice, ask: is this the right approach? What assumption does it depend on? Where does it break under real-world conditions (concurrent users, host-header forgery, malicious input, partial failures, deployment-environment differences, schema drift over time)? If the approach is sound, say so explicitly in one line at the end — but the body is for challenges. Default stance is skepticism."
>
> Then list focus areas in this order: (1) design / approach, (2) assumptions, (3) failure modes under real conditions, (4) security, (5) framework correctness, (6) schema / migration hygiene, (7) scope contradictions vs PRD/CLAUDE.md, (8) implementation defects last. Tell Codex **not** to list things that are good — adversarial reviews don't dilute with positive callouts.
>
> **Output requirements:**
> - Body must be prefixed with the literal string `**Codex review (delegated by Claude Code):**` — this is the AI disclaimer the triage skill uses to recognize the comment.
> - **Do NOT triage / filter / soften** Codex's findings. Pass everything verbatim. If Codex says something dumb, that's useful signal too.
> - Comment-only review: do not call `--approve` or `--request-changes`. Don't push code, don't merge.
>
> **Verify before returning:**
> Run `gh pr view <PR#> --json reviews,comments --jq '{reviews:(.reviews|length), comments:(.comments|length)}'` before and after posting. Confirm the count increased. If it didn't, the post failed — debug and retry. Don't claim success silently.

## Step 4 — Verify

After the rescue agent returns, independently confirm:

```bash
gh pr view <PR#> --json reviews,comments --jq '.comments[-1] | {body_starts_with: (.body[:60]), author: .author.login, url: .url}'
```

The body should start with `**Codex review (delegated by Claude Code):**`. If the most recent comment doesn't, the post didn't go through — re-invoke the agent or surface the error.

## Step 5 — Report

One paragraph:
- Finding count + severity mix (HIGH / MEDIUM / LOW / NOTE).
- The 1-2 most important findings as a heads-up (do not triage; just flag).
- The posted comment URL.
- Whether triage should run now (delegated phase) or human should read raw first (calibration phase) — read this from the project `CLAUDE.md` to make the recommendation.

## Failure modes

- **Stale CLI** (most common): opaque "model not supported" or "requires newer Codex" errors. → Run preflight (Step 1).
- **Codex sandbox 404 on private repo**: Codex itself tried to call GitHub. → The rescue agent was briefed wrong; re-brief making the boundary explicit (Step 3 wording).
- **Windows EBUSY during upgrade**: a process is holding the binary. → Quit Codex Desktop, kill `app-server-broker.mjs`, reboot if needed (Step 1).
- **Codex returns no findings**: a valid outcome — clean code, or scope was so narrow there was nothing to flag. Still post the AI-disclaimer comment with "No findings — review complete" so the PR has a record that review ran.
- **`gh pr review --comment` fails** with permission error: confirm `gh auth status` and that the user can comment on the repo. Don't attempt to bypass.

## What this skill does NOT do

- Triage. That's `triage-pr-review`. The two are separated so the human can read Codex's raw output first when in calibration phase.
- Approve/request-changes. Always comment-only.
- Push code, merge, or modify the working tree.
- OAuth/API key configuration of any kind.
