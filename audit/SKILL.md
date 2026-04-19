---
name: audit
description: Full inventory of Claude Code config (plugins, MCP servers, agents, skills, commands, hooks) with update checks
---

# Audit Claude Code Configuration

Produce a complete inventory of everything configured in Claude Code on this machine, then check for available updates where applicable.

The user may pass one or more of the following flags when invoking this skill — apply them as described:

- `--skip-updates` — skip Phase 2 entirely.
- `--user-only` — skip the project-scope inspection in Phase 1.
- `--verbose` — render Phase 3 in verbose mode (expand every plugin's internals, full tables per user/project category). Default is compact.

---

## Phase 1 — Inventory

Inspect these locations and collect what you find. Prefer the `Read` tool for JSON files; use Bash only for directory listings (`ls -la` so symlinks surface) and `python3 -c` if you truly need to parse JSON in the shell. Do not narrate the steps as you go — gather silently and report at the end.

**Probe hygiene (critical):** When checking for existence, never chain probes with `&&` — one missing dir will abort the chain and the harness will cancel *sibling* parallel Bash calls. One Bash call per probe, or append `|| true` / `2>/dev/null`.

**User scope** (`~/.claude/`):
- `settings.json` — extract `mcpServers`, `hooks`, and `enabledPlugins` blocks
- `plugins/known_marketplaces.json` — marketplaces registered on this machine (name + source URL + `installLocation`)
- `plugins/installed_plugins.json` — explicit plugin enablement registry; treat as advisory, not authoritative (single-plugin marketplaces activate via `known_marketplaces.json` even when this file is `{plugins: {}}`)
- `plugins/marketplaces/<name>/` — the actual plugin source lives here (**not** `plugins/cache/`). Two shapes:
  - **Single-plugin marketplace** — has `.claude-plugin/plugin.json` at the marketplace root. That *is* the plugin. Its `commands/`, `agents/`, `skills/`, `hooks/` live directly under the marketplace dir.
  - **Multi-plugin marketplace** — has `.claude-plugin/marketplace.json` listing `plugins[]`. Each plugin lives at `plugins/<plugin-name>/` with its own `.claude-plugin/plugin.json`. Only those present in `enabledPlugins` or `installed_plugins.json` count as active; report the rest as available-but-disabled.
- `commands/*.md` — user-level slash commands. Use `ls -la` to spot symlinks and resolve the target for the **Source** column. Read YAML frontmatter `description` if present, else first heading.
- `agents/*.md` — user-level subagents
- `skills/*/SKILL.md` — user-level skills

**Project scope** (`./` and `./.claude/` — only if they exist in the current working directory, and only if `--user-only` is not set):
- `./.claude/settings.json` and `./.claude/settings.local.json` — merge `hooks`, `mcpServers`, `enabledMcpjsonServers`
- `./.mcp.json` — project-level MCP server definitions (this is commonly the real source of active MCP servers, not user `settings.json`)
- Same `commands/`, `agents/`, `skills/` layout as user scope

Merge MCP servers across `~/.claude/settings.json`, `./.claude/settings.json`, `./.claude/settings.local.json`, and `./.mcp.json`, de-duping by name; note the source file in the Scope column.

**Per-plugin tallies** (for every active plugin — single-plugin marketplace root OR each enabled plugin under a multi-plugin marketplace):
- count `agents/*.md`, `skills/*/SKILL.md`, `commands/*.md`
- count hook entries: sum the `hooks` array entries across all events inside `hooks/hooks.json` (if present)

Store the **counts** for compact mode. When `--verbose`, also capture each entry's **name + one-line description** (from frontmatter `description`, or the first heading, or `plugin.json` for plugins) so the verbose tables can be rendered without a second pass.

For user/project level items, always record name + description regardless of mode — they're rendered in both.

---

## Phase 2 — Update checks

Skip this phase entirely if `--skip-updates` was passed.

**This phase is read-only.** Never run `git pull`, `git reset`, `npm install`, or anything else that mutates state — only `git fetch` and `npm view`.

**For each active plugin** (single-plugin marketplace root, or enabled plugin dir under a multi-plugin marketplace), run the snippet below as **one Bash tool call per plugin**, in parallel across plugins. Do not background with `&` inside a single shell — use separate Bash tool calls and let the harness parallelize them. Set the Bash tool's `timeout` parameter to `10000` (10s). **Do not use the shell `timeout` command** — it isn't present on macOS by default.

```bash
d="<plugin-dir-absolute-path>"
cd "$d" 2>/dev/null || { echo "status=failed reason=cd"; exit 0; }
# Resolve marketplace root — for multi-plugin layouts the plugin dir is two levels below it
root="$d"
if [ ! -d .git ] && [ ! -f .gcs-sha ]; then
  parent=$(cd ../.. 2>/dev/null && pwd)
  [ -n "$parent" ] && { [ -d "$parent/.git" ] || [ -f "$parent/.gcs-sha" ]; } && root="$parent"
fi
# CDN-managed tarball install (Claude Code fetches these via GCS, not git) — update via /plugin
[ -f "$root/.gcs-sha" ] && { echo "status=cdn reason=tarball-install root=$root"; exit 0; }
cd "$root" 2>/dev/null || { echo "status=failed reason=cd-root"; exit 0; }
[ -d .git ] || { echo "status=failed reason=no-git-dir"; exit 0; }
origin=$(git remote get-url origin 2>/dev/null) || { echo "status=failed reason=no-origin"; exit 0; }
git fetch --quiet origin 2>/dev/null || { echo "status=failed reason=fetch-error origin=$origin"; exit 0; }
upstream=$(git rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null)
if [ -z "$upstream" ]; then
  for c in origin/main origin/master; do
    git rev-parse --verify "$c" >/dev/null 2>&1 && upstream="$c" && break
  done
fi
[ -z "$upstream" ] && { echo "status=failed reason=no-upstream origin=$origin"; exit 0; }
behind=$(git rev-list --count "HEAD..$upstream" 2>/dev/null)
behind=${behind:-0}
echo "status=ok behind=$behind upstream=$upstream origin=$origin"
[ "$behind" -gt 0 ] && git log "HEAD..$upstream" --oneline -5
```

Properties this guarantees: never aborts on missing `.git`, missing `origin`, missing `origin/HEAD`, or empty rev-list output; emits a single parseable status line; falls back through `@{u}` → `origin/main` → `origin/master`. CDN-managed marketplaces (those with a `.gcs-sha` marker at the marketplace root — Claude Code installs GitHub-sourced marketplaces as tarball snapshots via GCS) are reported as `status=cdn` and are NOT treated as failures — they update through `/plugin marketplace update <name>`.

**For each MCP server** (from merged user + project + `.mcp.json` sources):
- If the command is `npx` and the args reference an npm package (e.g., `npx -y @scope/pkg`), run `npm view <package> version` (Bash tool timeout 10000) to get the latest published version. Note it alongside what's installed if resolvable.
- If the command is a local script or binary (absolute path, `node ./dist/...`, etc.), mark it `local — manual check required` and do not attempt to probe.

**Execution rules:**
- One Bash tool call per check; let the harness parallelize. Do not pack multiple `cd X && git ...` into one command.
- Set the Bash tool's `timeout` parameter to `10000` on each network call.
- If a check fails for any reason, mark that row `⚠️ check failed — <reason from status line>` and continue. **Never abort the whole audit because one check failed.**

---

## Phase 3 — Report

Default to **compact mode**. Emit **verbose mode** only when `--verbose` is present.

### Dashboard strip (both modes)

Render a fenced code block (three backticks, no language tag) containing a 3-line box. Monospace font + box-drawing characters keep it aligned:

```
┌─── CLAUDE CODE ─────────────────────────────────────────┐
│  <N> plugins  ·  <M> MCP  ·  <A> agents  ·  <S> skills  │
│  <C> commands  ·  <H> hooks  ·  <update-badge>          │
└─────────────────────────────────────────────────────────┘
```

Rules:
- In `--verbose` mode, the top banner reads `CLAUDE CODE · VERBOSE`.
- `<update-badge>` is `⚠ <N> updates available` when any exist, `✅ all up to date` when none, `— updates skipped` when `--skip-updates`.
- Counts: plugins = active plugins only (idle plugins don't count). agents / skills / commands / hooks = totals across user + project + all active plugins. MCP = merged across user + project + `.mcp.json`.
- Omit any `·`-separated segment whose count is 0 (e.g., if zero MCP servers, skip `0 MCP`). Keep the two-line interior; rewrap content as needed to keep the box visually balanced.
- Pad the right edge with spaces so the `│` closing characters align vertically.

### Compact mode (default)

#### `## Plugins`
One entry per active plugin, formatted as two lines:

```
<status-emoji> **<plugin-name>@<marketplace>** `v<version>` — <status-phrase>
   adds: <N> agent(s) · <N> skill(s) · <N> command(s) · <N> hook(s)
```

- Omit any zero-count contribution from the second line. If the plugin contributes nothing, drop the second line entirely.
- Status phrases: `up to date` / `N commits behind` / `CDN-managed` / `check failed`.
- When behind, append `· latest: *"<latest commit subject>"*` to the second line.
- Emojis: `✅` up to date · `🟡` behind · `📦` CDN-managed · `⚠` failed.

For each marketplace that has idle plugins, emit a trailing line:

```
📦 **<marketplace>** — <N> plugins idle (<M> enabled)
```

If no plugins are active anywhere, replace the section body with `*No plugins enabled.*`.

#### `## MCP Servers`
Render a table if any exist:

| Name | Scope | Installed | Latest | Status |

If none exist, emit the heading followed immediately by `*No MCP servers configured.*` — never an empty table.

#### `## User scope`
Definition list, one bullet per populated category:

- **Agents** — `name1`, `name2`
- **Commands** — `/cmd1`, `/cmd2`
- **Skills** — `skill1`, `skill2`
- **Hooks** — `<event> → <short-cmd>` · `<event> (<matcher>) → <short-cmd>`

Hook formatting: strip `${CLAUDE_PLUGIN_ROOT}` / absolute paths down to just the script basename.

If every category is empty:
```
## User scope
*No user-level agents, skills, commands, hooks, or MCP servers.*
```

If some are populated and some empty, render the bullets then append one italic trailer line listing the empty categories:
```
## User scope
- **Agents** — catchup
- **Commands** — /audit
- *No user-level skills or hooks.*
```

#### `## Project scope (<project-name>)`
Same pattern as User scope. Categories: **Hooks**, **Permissions** (count + source file), **MCP** (count + `.mcp.json` mention), **Agents**, **Skills**, **Commands**. Skip the section entirely if `--user-only` is set.

#### `## Permissions (user)`
One-line summary: `<N> allow rules · defaultMode: <mode> · dangerous-prompt skip: <on/off>`. Omit the section if the user settings has no permissions block.

#### `## Updates`
Only list rows that need attention:

- 🟡 **<plugin-name>** — N commits behind · `/plugin marketplace update <marketplace>`
- 🟡 **<mcp-server>** MCP — `<installed>` → `<latest>`

If nothing needs attention: `*All up to date.*`. If `--skip-updates`: `*Update check skipped.*`.

#### `## Notes`
Duplicates, shadowing, misconfigurations worth flagging. Omit the whole section if nothing worth noting. Do **not** include idle-marketplace nudges here — the Plugins section already surfaces those inline.

### Verbose mode (`--verbose`)

Same dashboard strip (header reads `CLAUDE CODE · VERBOSE`). Then:

#### `## Plugins`
One `### <status-emoji> <plugin>@<marketplace> v<version> — <status-phrase>` subheading per active plugin. Below each heading:

- Italic source line: `*<github-repo-or-local-path> · <git|CDN>-backed*`
- When behind, a `Pending: *<subject1> · <subject2> · ...*` line before the table
- A contributions table:

| Type | Name | Description |
|---|---|---|
| agent | ... | ... |
| skill | ... | ... |
| cmd | `/plugin:cmd` | ... |
| hook | <event> | `<script-basename>` |

For each marketplace with idle plugins:

```
### 📦 <marketplace> — <N> idle plugins
`name1`, `name2`, ... — enable via `/plugin`
```

#### `## MCP Servers`
Full table with Command column:

| Name | Scope | Command | Installed | Latest | Status |

Empty-state rule same as compact.

#### `## User scope`
Render one `###` subheading per populated category (Agents, Skills, Commands, Hooks, Permissions), each with an appropriate table:

- Agents / Skills / Commands: `Name | File | Description`
- Hooks: `Event | Matcher | Command`
- Permissions: one-line summary as in compact

Omit any subheading whose category is empty. Never render an empty table.

#### `## Project scope (<project-name>)`
Same as user scope — populated subsections only. Skip the whole section if `--user-only`.

#### `## Updates available`
Same content as compact, but expand each row with per-commit subjects when behind:

```
- 🟡 **<plugin>** — N commits behind · /plugin marketplace update <marketplace>
  - subject 1
  - subject 2
```

Empty-state same as compact.

#### `## Shadows / duplicates`
Broken out from Notes. Format: `<name> <type>: <path-A> (<scope-A>) shadows <path-B> (<scope-B>).`. Omit the section if none.

#### `## Recommendations`
1-4 actionable numbered items. If nothing notable, emit `*No recommendations at this time.*`.

---

## Style

- Tight, scannable, no fluff.
- Jump straight to the dashboard strip — no preamble like "Here is the audit…".
- No postamble asking if the user wants anything else.
- **Never render empty tables.** When a section has nothing to show, either (a) render the heading with an italic one-line note, or (b) omit the whole section — per the rules above.
- Use `✅` / `🟡` / `📦` / `⚠` / `—` consistently for status indicators.
- Bold plugin names (`**name@marketplace**`); inline-code for versions, paths, and command names; italic for empty-state notes and supplementary context lines (source, pending commits).
- Keep the dashboard strip width stable (box interior ~57 chars) so successive runs look consistent.
