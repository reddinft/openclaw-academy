# Writing a Skill

Skills are the primary extension mechanism in OpenClaw. A skill is just a folder with a `SKILL.md` file that teaches the agent how to use a new capability. No compilation, no deployment pipeline, no approval process — write a markdown file, drop it in a directory, and the agent picks it up.

In this lesson, you'll write a skill from scratch, test it locally, and publish it to ClawHub.

---

## What Exactly Is a Skill?

A skill is **documentation for the LLM**. It tells the agent:

- What the capability is called
- When to use it
- What tools or commands to run
- How to handle the output

Most skills are pure markdown instructions. They don't register new tools — they teach the agent to use existing ones (like `exec`, `read`, `browser`) in specific ways.

> **Key Takeaway:** A skill is a prompt, not a plugin. It's instructions the agent reads at the start of each session. The better the instructions, the better the agent uses the capability.

---

## The SKILL.md Format

Every skill needs a `SKILL.md` file with YAML frontmatter and markdown instructions:

```markdown
---
name: weather-lookup
description: Look up current weather for any city using wttr.in
---

# Weather Lookup

When the user asks about weather for a location, run:

\```bash
curl -s "wttr.in/{city}?format=3"
\```

Replace `{city}` with the requested location. Report the result conversationally.

If the user doesn't specify a city, ask them which city they want.
```

That's it. That's a complete, working skill.

---

## Frontmatter Reference

The YAML frontmatter controls how OpenClaw loads and filters the skill:

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Unique identifier (lowercase, hyphens OK) |
| `description` | Yes | One-line summary shown in skill lists |
| `homepage` | No | URL shown as "Website" in the macOS Skills UI |
| `user-invocable` | No | `true` (default) exposes as a `/slash` command |
| `disable-model-invocation` | No | `true` hides from LLM prompt (slash-only) |
| `command-dispatch` | No | `tool` to bypass the model and call a tool directly |
| `command-tool` | No | Tool name for direct dispatch |
| `metadata` | No | JSON object for gating, install hints, and more |

### The metadata Object

The `metadata` field is where you declare requirements and gating rules. It must be a **single-line JSON object**:

```markdown
---
name: my-skill
description: Does something useful
metadata: {"openclaw": {"requires": {"bins": ["jq"], "env": ["MY_API_KEY"]}, "primaryEnv": "MY_API_KEY"}}
---
```

Here's what you can put in `metadata.openclaw`:

| Key | Purpose |
|-----|---------|
| `requires.bins` | All listed binaries must exist on PATH |
| `requires.anyBins` | At least one must exist on PATH |
| `requires.env` | Env vars that must be set (or provided in config) |
| `requires.config` | openclaw.json paths that must be truthy |
| `primaryEnv` | The main API key for this skill |
| `always` | `true` skips all other gates |
| `emoji` | Shown in the macOS Skills UI |
| `os` | Platform filter: `["darwin"]`, `["linux"]`, etc. |
| `install` | Array of installer specs (brew/node/go/download) |

---

## Where Skills Live

Skills are loaded from three places, in precedence order:

```
<workspace>/skills/      ← Highest priority (your workspace)
~/.openclaw/skills/      ← Managed/local skills (shared across agents)
bundled skills           ← Shipped with OpenClaw (lowest priority)
```

If the same skill name exists in multiple places, the highest-precedence copy wins.

### Multi-Agent Setups

In multi-agent configurations, each agent has its own workspace:

- **Per-agent skills** → `<workspace>/skills/` (only that agent sees them)
- **Shared skills** → `~/.openclaw/skills/` (all agents on the machine)
- **Extra dirs** → `skills.load.extraDirs` in config (lowest precedence)

---

## Step-by-Step: Build a Real Skill

Let's build a skill that generates commit messages from staged git changes.

### 1. Create the Directory

```bash
mkdir -p ~/.openclaw/workspace/skills/commit-helper
```

### 2. Write the SKILL.md

```markdown
---
name: commit-helper
description: Generate conventional commit messages from staged git changes
user-invocable: true
metadata: {"openclaw": {"requires": {"bins": ["git"]}}}
---

# Commit Helper

When the user invokes `/commit-helper` or asks you to write a commit message:

1. Run `git diff --cached --stat` to see what's staged
2. Run `git diff --cached` to see the actual changes
3. Analyze the changes and generate a commit message following
   Conventional Commits format:
   - `feat:` for new features
   - `fix:` for bug fixes
   - `docs:` for documentation
   - `refactor:` for restructuring
   - `chore:` for maintenance
4. Present the message and ask if the user wants to commit

If nothing is staged, tell the user to `git add` files first.

Keep the subject line under 72 characters. Add a body only if the
changes are complex enough to warrant explanation.
```

### 3. Verify It Loaded

Start a new OpenClaw session (skills snapshot on session start):

```bash
openclaw agent --message "what skills do you have?"
```

Or check via the CLI:

```bash
openclaw skills list
```

Your skill should appear in the list. If it doesn't, check:

- Is the folder in the right location?
- Does `SKILL.md` have valid YAML frontmatter?
- Are the `requires` gates satisfied? (Is `git` on PATH?)

### 4. Test It

```bash
openclaw agent --message "use commit-helper to write me a commit message"
```

The agent should run the git commands and generate a message.

---

## Gating in Action

Gating prevents skills from loading when their requirements aren't met. This keeps the agent's context clean — no point injecting instructions for a tool that isn't installed.

Here's a more complex gating example:

```markdown
---
name: image-gen
description: Generate images via OpenAI DALL-E API
metadata: {"openclaw": {"requires": {"env": ["OPENAI_API_KEY"]}, "primaryEnv": "OPENAI_API_KEY", "emoji": "🎨", "install": [{"id": "node", "kind": "node", "package": "openai", "bins": ["openai"], "label": "Install OpenAI CLI"}]}}
---
```

This skill:
- Only loads if `OPENAI_API_KEY` is set (in env or config)
- Shows a paint palette emoji in the UI
- Offers a one-click Node.js install for the CLI dependency

---

## Config Overrides

You can enable/disable skills and inject environment variables via `~/.openclaw/openclaw.json`:

```json5
{
  skills: {
    entries: {
      "commit-helper": {
        enabled: true,
      },
      "image-gen": {
        enabled: true,
        apiKey: "sk-...",          // maps to primaryEnv
        env: {
          OPENAI_API_KEY: "sk-...", // explicit env injection
        },
      },
      "risky-skill": {
        enabled: false,             // completely disabled
      },
    },
  },
}
```

Rules:
- `enabled: false` blocks the skill even if it's installed
- `env` values are injected only if the variable isn't already set
- `apiKey` is a convenience shortcut for the `primaryEnv` variable
- Changes take effect on the next new session

---

## Publishing to ClawHub

ClawHub is the public skill registry. Once your skill works locally, you can share it with the community.

### Install the CLI

```bash
npm i -g clawhub
```

### Authenticate

```bash
clawhub login
```

This opens a browser flow. Your GitHub account must be at least one week old.

### Publish

```bash
clawhub publish ./skills/commit-helper \
  --slug commit-helper \
  --name "Commit Helper" \
  --version 1.0.0 \
  --tags latest
```

### Bulk Sync

If you have multiple skills, `sync` scans and publishes them all:

```bash
clawhub sync --all
```

Use `--dry-run` first to see what would be uploaded:

```bash
clawhub sync --all --dry-run
```

### Versioning

Each publish creates a semver version. Tags like `latest` point to a version. Update with:

```bash
clawhub publish ./skills/commit-helper \
  --slug commit-helper \
  --version 1.1.0 \
  --changelog "Added support for monorepo detection"
```

---

## The Token Budget

Every skill adds to the system prompt. The cost is deterministic:

```
total characters = 195 + Σ (97 + len(name) + len(description) + len(location))
```

Rough rule: each skill costs ~24 tokens + your field lengths. Twenty skills might add ~800 tokens. Keep descriptions concise.

---

## Security Notes

- Treat third-party skills as **untrusted code**. Read them before enabling.
- `env` and `apiKey` values inject into the host process for that agent turn — keep secrets out of prompts and logs.
- Prefer sandboxed runs for untrusted inputs.

---

## Summary

| Step | Command / Action |
|------|-----------------|
| Create skill dir | `mkdir -p <workspace>/skills/my-skill` |
| Write SKILL.md | Frontmatter + markdown instructions |
| Gate requirements | `metadata.openclaw.requires` (bins, env, config) |
| Test locally | `openclaw agent --message "use my skill"` |
| Configure in JSON | `skills.entries.<name>` in openclaw.json |
| Publish to ClawHub | `clawhub publish ./skills/my-skill --slug my-skill` |
| Bulk publish | `clawhub sync --all` |
| Install from ClawHub | `clawhub install <slug>` |
| Update all | `clawhub update --all` |

---

## Exercise

1. Create a workspace skill called `quick-note` that saves timestamped notes to a `~/notes/` directory using the `exec` tool
2. Add gating so the skill checks that the `~/notes/` directory exists (hint: use `requires.bins` isn't the right approach here — think about what you can check in the instructions themselves)
3. Test it in a local session
4. **Bonus:** Publish it to ClawHub with `clawhub publish`

---

In the next lesson, we'll look at **custom routing** — how to direct different channels and senders to different agents with different capabilities.
