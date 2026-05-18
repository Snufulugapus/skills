---
name: skill-builder
description: Create a new Claude Code skill end-to-end (interview, draft, test, iterate) and then decide whether to publish it to my public skills repo. Use this whenever the user wants to create, build, write, scaffold, or make a new skill — including phrases like "new skill", "skill builder", "make a skill", "I want to write a skill", or any context where the user is starting work on a fresh skill. This wrapper bakes in the publish-or-private decision so it does not get forgotten.
---

# Skill Builder (with publish prompt)

This skill wraps Anthropic's official `skill-creator` with a final publish-or-private decision step. It does NOT replace skill-creator's behavior — it delegates to it entirely for the skill-writing process, then adds a single decision point at the end.

## Step 1: Delegate to the upstream skill-creator

Read the upstream skill-creator file at this path:

```
~/.claude/plugins/marketplaces/claude-plugins-official/plugins/skill-creator/skills/skill-creator/SKILL.md
```

If that exact path doesn't exist, locate it dynamically:

```bash
find ~/.claude/plugins -name "SKILL.md" -path "*skill-creator*" 2>/dev/null
```

If neither finds the file, tell the user the `claude-plugins-official` marketplace isn't installed (they can add it via `/plugin marketplace add anthropic/claude-plugins-official`) and stop here.

Once located, follow the upstream file's instructions completely to create the new skill. That file is the authoritative process — interview the user, draft the SKILL.md, set up test cases, run evals if appropriate, iterate. The new skill should be written to `~/.claude/skills/<skill-name>/SKILL.md` (Jak's user-level skills directory).

Do not summarize or skip steps from the upstream — follow it as written. The upstream covers everything from initial intent capture through description optimization, and the user benefits from the full process.

## Step 2: Publish prompt (after the skill is written and verified)

Once the new skill is fully written, tested to the user's satisfaction, and the user agrees it's done, ask exactly this question:

> Publish `<skill-name>` to `Snufulugapus/skills`? (y/n)

### If the user says yes:

1. Edit `~/.claude/skills/.gitignore` — append a new line `!/<skill-name>/` under the existing "Published skills" allowlist entries (preserve the existing allowlist; just add one line).
2. From `~/.claude/skills/`, run these commands in sequence:
   ```bash
   git add .gitignore <skill-name>/
   git commit -m "Publish: <skill-name>"
   git push
   ```
3. Confirm the push succeeded. Share the resulting URL with the user: `https://github.com/Snufulugapus/skills/tree/main/<skill-name>`.

### If the user says no:

Stop. Do nothing — the allowlist's deny-by-default rule keeps the new skill private automatically. Confirm to the user briefly: "Kept private. The skill works locally but isn't in the public repo."

### Special case: re-running on an existing skill

If the user invokes this skill on an *existing* skill (i.e., the upstream skill-creator's iteration loop on an already-written skill), the publish prompt still fires at the end. Treat it the same way — ask, and if yes, commit + push the updated skill.
