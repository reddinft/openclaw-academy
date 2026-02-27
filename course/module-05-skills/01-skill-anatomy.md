# Skill Anatomy

Skills are how you teach your agent new tricks. They're self-contained packages of instructions + tools that get injected into the agent's context — like handing someone a reference card before they start a task.

In this lesson we'll crack open a skill and examine every piece.

---

## What Is a Skill?

A skill is a **directory** containing at minimum one file: `SKILL.md`. That file has YAML frontmatter (metadata) and Markdown body (instructions). When the agent loads the skill, the instructions become part of its system prompt and any registered tools become available.

> **Key Takeaway:** A skill = metadata (YAML frontmatter) + instructions (Markdown) + optional scripts and assets. That's it.

---

## The SKILL.md File

This is the heart of every skill. Let's look at a complete example — a weather skill:

```markdown
---
name: weather
description: Get current weather and forecasts for any location
read_when: "The user asks about weather, temperature, or forecasts"
metadata:
  {
    "openclaw": {
      "requires": {
        "env": ["WEATHER_API_KEY"],
        "bins": ["curl"]
      },
      "primaryEnv": "WEATHER_API_KEY",
      "homepage": "https://github.com/example/weather-skill",
      "emoji": "🌤️",
      "os": ["darwin", "linux"],
      "install": [
        { "type": "download", "url": "https://example.com/weather-cli" }
      ]
    }
  }
---

# Weather Skill

You can look up current weather conditions and forecasts.

## Tools

- **get_weather**: Fetch current conditions for a city or coordinates
- **get_forecast**: Fetch a multi-day forecast

## Usage Notes

- Always confirm the location with the user if ambiguous
- Prefer Celsius unless the user has indicated a preference for Fahrenheit
- Include humidity and wind when reporting conditions
```

Let's break down every piece.

---

## Frontmatter Fields

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Unique skill identifier (lowercase, hyphens OK) |
| `description` | Yes | One-line summary shown in skill listings |
| `read_when` | No | Natural-language condition for when the agent should load this skill |
| `metadata` | No | Nested object with OpenClaw-specific configuration |

### The `metadata.openclaw` Object

This is where you declare requirements, installation hints, and platform constraints:

```yaml
metadata:
  {
    "openclaw": {
      "requires": {
        "bins": ["ffmpeg", "curl"],
        "env": ["API_KEY"],
        "config": ["channels.telegram"]
      },
      "primaryEnv": "API_KEY",
      "homepage": "https://github.com/you/your-skill",
      "emoji": "🎯",
      "os": ["darwin", "linux", "win32"],
      "install": [
        { "type": "brew", "package": "ffmpeg" },
        { "type": "node", "package": "some-cli" }
      ]
    }
  }
```

| Nested Field | Purpose |
|-------------|---------|
| `requires.bins` | Binary executables that must be in `$PATH` |
| `requires.env` | Environment variables that must be set |
| `requires.config` | Config paths that must exist in `openclaw.json` |
| `primaryEnv` | The main API key env var (used by config UI) |
| `homepage` | Link to docs or repo |
| `emoji` | Display emoji in skill listings |
| `os` | Platform allowlist — `"darwin"`, `"linux"`, `"win32"` |
| `install` | Installer hints (brew, node, go, uv, download) |

---

## Gating: When Does a Skill Load?

Not every skill loads on every turn. OpenClaw uses two gating mechanisms:

### 1. Eligibility Gating (Hard Requirements)

If `requires` is specified, the skill only appears as eligible when all requirements are met:

```
requires.bins → checked via `which <binary>`
requires.env → checked via process.env
requires.config → checked via config path lookup
os → checked via process.platform
```

If any check fails, the skill is **invisible** — the agent never sees it.

### 2. `read_when` Gating (Soft / Contextual)

The `read_when` field is a natural-language hint injected into the `<available_skills>` block. The agent sees:

```xml
<available_skills>
  <skill name="weather">Get current weather and forecasts for any location
    Load when: The user asks about weather, temperature, or forecasts</skill>
  <skill name="spotify">Control Spotify playback
    Load when: The user asks about music, playlists, or Spotify</skill>
</available_skills>
```

The agent then decides whether to "read" the full skill instructions based on the current conversation. This keeps the system prompt lean — only relevant skill instructions are loaded.

> **Key Takeaway:** Eligibility gating is binary (requirements met or not). `read_when` gating is a soft hint — the model decides whether the skill is relevant to the current turn.

---

## The Markdown Body

Everything below the frontmatter `---` is the skill's instruction set. This gets injected into the agent's context when the skill is loaded.

Best practices for writing skill instructions:

| Do | Don't |
|----|-------|
| Be specific about tool names and parameters | Write vague "you can do things" instructions |
| Include usage examples | Assume the agent knows your API |
| Specify output formatting preferences | Leave output format ambiguous |
| Note edge cases and error handling | Ignore failure modes |
| Keep it under ~2000 tokens | Write a novel — context window is precious |

---

## Token Budget

Skills consume context window space. OpenClaw calculates the token impact deterministically:

```
Base cost:        ~195 characters (skill XML wrapper)
Per-skill entry:  ~97 characters (name, description in available_skills)
Instructions:     length of Markdown body (when loaded)
```

For a typical skill with a 500-character description and 1500-character instruction body, you're looking at ~2200 characters (~550 tokens). With 10 skills loaded, that's ~5500 tokens of context used before the conversation even starts.

---

## Skill Directory Structure

A skill can be more than just `SKILL.md`. Here's the full anatomy:

```
my-weather-skill/
├── SKILL.md           ← Required: metadata + instructions
├── handler.ts         ← Optional: tool handler (TypeScript)
├── assets/
│   ├── icons/         ← Optional: images, icons
│   └── templates/     ← Optional: prompt templates, configs
├── scripts/
│   ├── install.sh     ← Optional: post-install script
│   └── check.sh       ← Optional: health check
└── README.md          ← Optional: human-facing docs (not loaded by agent)
```

### Scripts

Scripts in the `scripts/` directory are lifecycle hooks:

| Script | When it runs |
|--------|-------------|
| `install.sh` | After `clawhub install` or manual placement |
| `check.sh` | During `openclaw skills check` health validation |
| `uninstall.sh` | Before removal |

### Assets

The `assets/` directory holds static files the skill might reference — icons for Canvas rendering, prompt templates, configuration snippets. These are available to the skill's tool handlers but are **not** automatically injected into the agent's context.

---

## A Real-World Example: The `oracle` Skill

Let's look at how a bundled skill is structured. The `oracle` skill lets the agent perform web searches:

```markdown
---
name: oracle
description: Search the web and fetch page content
read_when: "The user asks a question that requires current information, news, or web research"
metadata:
  {
    "openclaw": {
      "emoji": "🔮",
      "os": ["darwin", "linux", "win32"]
    }
  }
---

# Oracle — Web Search & Fetch

Use the `web_search` and `web_fetch` tools to find current information.

## Guidelines

- Search before guessing when the user asks about current events, prices, or recent news
- Fetch specific URLs when the user shares a link or you need detailed page content
- Summarize results concisely — don't dump raw HTML
- Cite sources with URLs when providing factual information
```

Notice how minimal it is — the tools (`web_search`, `web_fetch`) are registered by the Gateway core, not by the skill itself. The skill's job is just to provide **instructions** for when and how to use them.

---

## Configuring Skills via `openclaw.json`

Skills can be configured in your main config file:

```json5
{
  skills: {
    // Per-skill overrides
    entries: {
      weather: {
        enabled: true,
        apiKey: "wk_abc123",        // Injected as primaryEnv
        env: {
          WEATHER_UNITS: "metric"   // Extra env vars
        }
      },
      "risky-skill": {
        enabled: false              // Disable a specific skill
      }
    },
    // Loading options
    load: {
      extraDirs: ["/home/me/my-skills"],  // Additional search paths
      watch: true                          // Auto-reload on SKILL.md changes
    },
    // Only allow specific bundled skills
    allowBundled: ["oracle", "weather", "spotify"]
  }
}
```

---

## CLI: Managing Skills

```bash
# List all loaded skills
openclaw skills list

# Show details for a specific skill
openclaw skills info weather

# Check health (runs requires checks)
openclaw skills check

# Enable/disable
openclaw skills enable weather
openclaw skills disable risky-skill
```

---

## Summary

| Component | File | Purpose |
|-----------|------|---------|
| Metadata | SKILL.md frontmatter | Name, description, requirements, gating |
| Instructions | SKILL.md body | Agent-facing docs injected into context |
| Tools | handler.ts | Tool implementations (optional) |
| Assets | assets/ | Static files for tools |
| Scripts | scripts/ | Lifecycle hooks (install, check, uninstall) |
| Config | openclaw.json `skills.entries` | Per-skill overrides, env vars |

---

> **Exercise:** Create a minimal skill directory called `my-first-skill/` with a `SKILL.md` that:
> 1. Has a `name`, `description`, and `read_when` in the frontmatter
> 2. Requires one environment variable (make one up)
> 3. Has a Markdown body with instructions for a hypothetical tool
> 4. Place it in `~/.openclaw/workspace/skills/` and run `openclaw skills list` to verify it appears

---

In the next lesson, we'll explore **where skills live** — the three-tier loading system and what happens when skill names collide.
