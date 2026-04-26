---
name: triage-pr-review
description: Use after a PR has accumulated review activity from any source (Codex via request-codex-review, a Claude self-review, a human reviewer leaving comments, etc.) to decide what to do with the findings. Reads the project's PR review policy from CLAUDE.md to determine calibration vs delegated phase. In calibration phase, summarizes findings and stops — the human reads raw output. In delegated phase, applies trivials within a strict allowlist, replies "applied" on the comment, pushes back on findings that don't apply (with quoted code + reason), escalates judgment calls, and appends deferred items to docs/followups.md. Never auto-fixes auth/billing/Stripe/security findings regardless of who flagged them. Auto-trigger when a PR has fresh review activity and Claude has just finished writing the code under review.
---

# triage-pr-review

Reviewer-agnostic triage for PR review findings. Works on Codex output, a Claude self-review, or a human reviewer's comments — gathers everything fresh, applies the project's calibration policy, and reports.

## When to use

- Right after `request-codex-review` returns and the project is past the calibration phase.
- When a teammate has left review comments and you (Claude) are deciding what to do with them.
- When a CI bot or other reviewer has posted findings.

Do NOT use this skill in the calibration phase to "decide what to fix" — the whole point of calibration is for the human to read raw findings and grade reviewer quality. The skill respects this and stops at "summarize" when the project is in calibration.

## Quick start

```text
Triage PR #N's review.
```

Five steps below — silent gather, then a structured report.

## Step 1 — Read the project policy

Find the repo root's `CLAUDE.md`. Locate the section titled "PR review workflow" (or any heading carrying calibration / delegated / triage rules). Extract three things:

1. **Phase.** Is the current PR in calibration or delegated phase? Most projects encode this as a PR-number rule (e.g., `agent_platform`'s "PRs #1 and #2 calibration; PR #3 onward delegated"). Compare the active PR number against the rule.
2. **Always-escalate carve-outs.** What findings must never be auto-applied even if trivial? Default carve-outs if `CLAUDE.md` is silent: anything touching auth, billing, Stripe, anything labeled as a security concern.
3. **Followups format.** Does the project have `docs/followups.md`? If yes, read its format. If no, you'll create one in delegated phase using the standard template (see Step 5).

If `CLAUDE.md` has no PR review section at all, **default to calibration phase** as the safe path. Never auto-apply without an explicit project policy.

## Step 2 — Pull review activity from the PR

Reviewer-agnostic — collect from all three GitHub surfaces:

```bash
# Top-level issue comments (where Codex's structured comment lives, plus any human top-level comments)
gh api repos/<owner>/<repo>/issues/<PR#>/comments

# PR-level reviews (formal review submissions with the optional body comment)
gh pr view <PR#> --json reviews

# Inline review comments (line-anchored — humans typically use these for nits)
gh api repos/<owner>/<repo>/pulls/<PR#>/comments
```

De-dup by `id` across the three surfaces (GitHub returns some items in multiple endpoints).

**Skip prior triage replies.** Comments authored by the triage skill are recognizable by the suffix `— Claude Code triage` on the body. Filter those out so re-runs don't recurse on their own past replies.

**Parse each remaining item into a finding:**

- `id` — for replying later.
- `source` — `codex` if body starts with `**Codex review (delegated by Claude Code):**`; otherwise the comment's author login (`@spencer`, `@jakkitts`, etc.).
- `severity` — labeled in the body (`HIGH`/`MEDIUM`/`LOW`/`NOTE`) or `UNCLASSIFIED` if not.
- `location` — file path and line if grounded; otherwise null.
- `description` — the finding text.
- `suggested_fix` — if present.

For Codex's structured comment specifically: parse the numbered list inside the body — each line is a separate finding.

## Step 3 — Calibration phase path

In calibration phase, the human is the audience.

1. Render a table to the human:

   | Severity | Source | Area | Headline |
   |---|---|---|---|
   | HIGH | codex | auth | open redirect via `next` param |
   | … | … | … | … |

2. Do NOT apply anything.
3. Do NOT push back.
4. Do NOT defer.
5. Append the AI disclaimer to your summary: `— Claude Code triage (calibration phase, no auto-actions)`.

Then stop. The human reads, decides, and either course-corrects or invokes the skill explicitly with "go ahead and triage."

## Step 4 — Delegated phase path

For each finding, choose ONE of four buckets:

### Auto-apply

Only if **all** of these are true:

- The fix falls in the trivial allowlist:
  - typos in strings or comments
  - lint errors (unused imports, unused vars)
  - missing TypeScript types where the inferred type is correct
  - obvious null/undefined guards (`if (x) ...` around a deref)
  - simple a11y attributes (`aria-busy`, `role="alert"`, `aria-describedby`, `htmlFor`)
  - schema field default value or nullable adjustment that's clearly safe
- The fix is small (≤ ~10 lines), local (one file or trivially mirrored), and does not change runtime behavior beyond what the finding describes.
- The finding is NOT in the always-escalate carve-outs (Step 1, item 2).
- The finding came from a bot (Codex, CI). Human-authored "trivial" findings still default to escalate — see special handling below.

If yes:

1. Apply the change in code.
2. Run the project's typecheck (typically `pnpm --filter web typecheck` or whatever the repo uses).
3. If typecheck fails, ROLL BACK and switch this finding to "escalate" instead. Don't ship a half-fix.
4. Reply on the originating comment:

   ```text
   **Applied in <commit-sha>.** <one-line description of the fix>

   — Claude Code triage
   ```

### Push back

If you've read the code and the finding genuinely doesn't apply:

1. Reply on the originating comment:

   ```text
   **Pushing back.** Quote of the relevant code:

       <quoted lines>

   <Why the concern doesn't hold — be specific. If you're hand-wavy, escalate instead.>

   — Claude Code triage
   ```

2. Do NOT mark resolved. The reviewer (or the human) may want to debate.

**Hand-wavy disagreement is a flag.** If you can't articulate the why with quoted code, escalate instead.

### Escalate

For everything else — and unconditionally for these:

- logic changes
- API shape changes
- anything touching auth, billing, Stripe (regardless of severity)
- anything Codex flagged as a security concern
- anything where the right answer involves trade-offs the human should make

In the final report (Step 6), surface:

- One-line summary of the finding.
- Quoted finding text + location.
- Your tentative recommendation (apply / don't / refactor / defer / talk it out).
- A specific question for the human.

Do NOT apply anything in the escalate bucket. Do NOT reply on the comment yet — the human's answer goes there.

### Defer

If the finding is real but legitimately out of this PR's scope:

1. Append a line to `docs/followups.md` in the project's documented format (or this default if none exists):

   ```markdown
   - `[severity] PR#<#> — <area> — <description> (<why deferred>).`
   ```

2. If `docs/followups.md` doesn't exist yet, create it with this scaffold:

   ```markdown
   # Follow-ups

   Lightweight queue of items raised in PR review (or surfaced during implementation) that we deliberately deferred. Anything here should land in a future PR — most often when a related PRD touches the same area.

   Format: one bullet per item. `[severity] PR# — area — description (why deferred).`

   ## Open

   <!-- new items append here -->

   ## Closed

   _None yet — items move here when shipped, with the PR number that closed them._
   ```

3. Reply on the originating comment:

   ```text
   Tracked in `docs/followups.md` (PR <#>) — <one-line reason for defer>

   — Claude Code triage
   ```

### Special handling for human-authored comments

If `source` is a real human (not `codex` or a bot), the default bucket is **escalate** unless the requested change is unambiguously trivial AND the human's comment reads as a drive-by nit ("typo here", "add the missing semicolon"). Humans rarely leave low-context drive-by comments — when they do leave nits, they're usually paired with bigger thoughts. Default to surfacing rather than auto-applying.

## Step 5 — Commit + push

All auto-applied fixes from a single triage run go into ONE commit:

- If all findings came from Codex: title `Address Codex review on PR #<#>`.
- If mixed sources: title `Address PR #<#> review`.
- Body: a one-line summary per applied / pushed-back / escalated / deferred bucket. Include commit-trailing `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>`.

If `docs/followups.md` was edited in the same run, bundle that change into the same commit (don't make a separate followups commit unless explicitly asked).

Push to the PR branch.

## Step 6 — Final report to the human

Render this table:

| Severity | Source | Finding | Decision | Where |
|---|---|---|---|---|
| HIGH | codex | open redirect via `next` | applied | `7a1ab06` |
| MEDIUM | codex | duplicate package name | escalated | (question below) |
| LOW | @spencer | a11y label missing | escalated | (question below) |
| NOTE | codex | radius token comment drift | deferred | `docs/followups.md` |

Then list the **escalations** with:
- Quoted finding.
- Recommendation.
- Question for the human.

End with the commit URL (if anything was applied) and the PR URL.

## Failure modes

- **No review activity found.** Tell the human; suggest `request-codex-review` first or wait for a reviewer. Don't fabricate findings.
- **Multiple Codex review comments (re-runs).** Use the most recent. Skip the older ones — they may be stale.
- **Mixed sources with conflicting opinions** (Codex says fix, human says don't): always defer to the human. Add the conflict to the escalations list.
- **`CLAUDE.md` has no PR review section.** Fall back to calibration phase. Never auto-apply without an explicit project policy.
- **Typecheck fails after auto-apply.** Roll back the trivial fix; switch that finding to escalate. Don't ship half-applied changes.
- **The PR branch has been updated since the review was posted.** Findings may now be stale. Note this in the final report and ask the human whether to proceed or re-request review.

## What this skill does NOT do

- Run reviews. That's `request-codex-review` (for Codex) or just write the review inline (for Claude self-review).
- Approve or request-changes the PR. Comment-only.
- Push code changes outside the auto-apply allowlist.
- Auto-fix anything in the always-escalate carve-outs (auth, billing, Stripe, security), no matter how trivial it looks.
- Make architectural decisions. Those always escalate.
