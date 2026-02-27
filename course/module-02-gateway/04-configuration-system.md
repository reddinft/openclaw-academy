# Configuration System

OpenClaw's behavior is controlled by a single configuration file: `~/.openclaw/openclaw.json`. Despite the `.json` extension, it's actually **JSON5** — which means you get comments, trailing commas, and unquoted keys. This one file controls everything: channels, models, agents, tools, logging, security.

Let's understand how it works, how it's validated, and how to fix it when things go wrong.

---

## JSON5: Why Not Plain JSON?

JSON is great for machines. It's terrible for humans editing config files. JSON5 fixes the worst pain points:

| Feature | JSON | JSON5 |
|---------|------|-------|
| Comments | No | Yes (`//` and `/* */`) |
| Trailing commas | No | Yes |
| Unquoted keys | No | Yes (when valid identifiers) |
| Single-quoted strings | No | Yes |
| Multi-line strings | No | Yes (backslash continuation) |

Here's what a real OpenClaw config looks like:

```json5
{
  // Model configuration
  agents: {
    defaults: {
      model: "anthropic/claude-sonnet-4-6",
    },
  },

  // Channel setup
  channels: {
    telegram: {
      botToken: "123456:ABC-DEF...",
      dmPolicy: "pairing",
    },
    whatsapp: {
      dmPolicy: "pairing",
      allowFrom: ["+15555550123"],
    },
  },

  // Logging
  logging: {
    level: "info",
    consoleLevel: "info",
  },
}
```

Comments let you document *why* a setting exists. Trailing commas let you reorder lines without syntax errors. It's a small thing that makes daily config editing much less frustrating.

---

## Config File Location and Loading

### Default location

```
~/.openclaw/openclaw.json
```

### Override with environment variables

| Variable | Purpose |
|----------|---------|
| `OPENCLAW_CONFIG_PATH` | Full path to config file |
| `OPENCLAW_STATE_DIR` | Base state directory (config at `$OPENCLAW_STATE_DIR/openclaw.json`) |
| `OPENCLAW_HOME` | Home directory for internal paths |
| `OPENCLAW_PROFILE` | Named profile (uses `openclaw-<profile>.json`) |

### Loading order

When the Gateway starts:

1. Resolve config path (env vars, then default)
2. Read the file as JSON5
3. Validate against the TypeBox schema
4. Apply auto-migrations for legacy keys
5. Merge environment variable overrides
6. Freeze the resolved config

If **validation fails**, the Gateway refuses to start and tells you to run `openclaw doctor`.

---

## Config Schema (TypeBox)

The config schema isn't a loose convention — it's a **TypeBox definition** that generates both TypeScript types and runtime validation. This means:

- Every field has a defined type, default, and description
- Invalid configs are caught at startup (not at runtime when something breaks)
- The schema is the single source of truth for what's configurable

### Top-level sections

```json5
{
  agents: { /* ... */ },      // Agent definitions, defaults, models
  channels: { /* ... */ },    // Channel configs (telegram, whatsapp, etc.)
  bindings: [ /* ... */ ],    // Route messages to agents
  tools: { /* ... */ },       // Tool policy, elevated, sandbox tools
  logging: { /* ... */ },     // File + console log settings
  gateway: { /* ... */ },     // Port, auth, TLS, control UI
  session: { /* ... */ },     // Session store path, thread bindings
  messages: { /* ... */ },    // Queue mode, debounce, prefixes
  browser: { /* ... */ },     // Browser automation settings
  memory: { /* ... */ },      // Memory backend (builtin, QMD)
  cron: { /* ... */ },        // Scheduled jobs
  broadcast: { /* ... */ },   // Multi-agent broadcast groups
}
```

### Field defaults

All fields are optional — OpenClaw uses safe defaults when omitted. This is a design principle: a minimal config should work:

```json5
{
  // This is a valid, working config.
  // Uses pairing for DMs, default model, no channels.
  agents: {
    defaults: {
      model: "anthropic/claude-sonnet-4-6",
    },
  },
}
```

You only add sections when you need to override defaults.

---

## Common Configuration Patterns

### Channels with DM policy

Every channel supports DM access control:

| Policy | Behavior |
|--------|----------|
| `pairing` (default) | Unknown senders get a one-time pairing code; you must approve |
| `allowlist` | Only senders in `allowFrom` can message |
| `open` | Anyone can message (requires `allowFrom: ["*"]`) |
| `disabled` | Ignore all DMs on this channel |

```json5
{
  channels: {
    telegram: {
      botToken: "...",
      dmPolicy: "pairing",    // Safe default
    },
    whatsapp: {
      dmPolicy: "allowlist",
      allowFrom: ["+15555550123", "+447700900456"],
    },
  },
}
```

### Group policy

| Policy | Behavior |
|--------|----------|
| `allowlist` (default) | Only groups in the configured allowlist |
| `open` | Allow all groups (mention-gating still applies) |
| `disabled` | Block all group messages |

### Model configuration

```json5
{
  agents: {
    defaults: {
      model: "anthropic/claude-sonnet-4-6",  // Primary model
    },
  },
  // Per-channel model overrides
  channels: {
    modelByChannel: {
      telegram: {
        "-1001234567890": "openai/gpt-4.1-mini",  // Cheap model for this group
      },
    },
  },
}
```

### Multi-agent with bindings

```json5
{
  agents: {
    list: [
      { id: "main", default: true, workspace: "~/.openclaw/workspace" },
      { id: "work", workspace: "~/.openclaw/workspace-work" },
    ],
  },
  bindings: [
    { agentId: "work", match: { channel: "slack", teamId: "T123456" } },
    // Everything else goes to main (default agent)
  ],
}
```

---

## Environment Variable Substitution

Some values support environment variable references:

```json5
{
  channels: {
    telegram: {
      botToken: "TELEGRAM_BOT_TOKEN",  // Resolved from env
    },
    discord: {
      token: "DISCORD_BOT_TOKEN",      // Resolved from env
    },
  },
}
```

For Telegram and Discord, the bot tokens can come from either the config file or environment variables. This is useful for:
- Keeping secrets out of config files
- Different tokens per deployment environment
- CI/CD automation

---

## Config Validation

The Gateway validates config at startup using the TypeBox schema. Here's what happens when validation fails:

```
$ openclaw gateway
ERROR: Config validation failed:
  - channels.telegram.botToken: Expected string, got number
  - agents.defaults.model: Unknown provider "antrhopic"

Run 'openclaw doctor' to diagnose and fix config issues.
```

The error messages include the exact path and what's wrong. Most issues are typos or leftover keys from older versions.

### Schema exploration

You can inspect the config schema:

```bash
# View the resolved config (with defaults filled in)
openclaw config get

# Check a specific section
openclaw config get agents

# View the schema itself
openclaw config schema
```

---

## openclaw doctor: The Config Healer

We covered `doctor` briefly in Lesson 1. Here's a deeper look at what it does specifically for configuration.

### Legacy key migrations

As OpenClaw evolves, config keys move and rename. Doctor handles the migration automatically:

```
$ openclaw doctor
i  Legacy config key found: routing.allowFrom
   -> Migrated to: channels.whatsapp.allowFrom

i  Legacy config key found: agent.model
   -> Migrated to: agents.defaults.model

   Config updated and saved.
```

Current migrations include:

| Legacy key | New location |
|-----------|-------------|
| `routing.allowFrom` | `channels.whatsapp.allowFrom` |
| `routing.groupChat.requireMention` | `channels.*.groups."*".requireMention` |
| `routing.queue` | `messages.queue` |
| `routing.bindings` | `bindings` |
| `routing.agents` | `agents.list` |
| `identity` | `agents.list[].identity` |
| `agent.model` | `agents.defaults.model` |
| `agent.*` (tools/sandbox) | `tools.*` |

The Gateway also auto-runs migrations on startup when it detects legacy format, so most users never need to run `doctor` manually for config issues. But doctor gives you visibility into what changed.

### Config file permissions

Doctor checks that `~/.openclaw/openclaw.json` isn't world-readable:

```
!  Config file is group/world readable (mode 644)
   -> Recommended: chmod 600 ~/.openclaw/openclaw.json
```

This matters because your config may contain API keys, bot tokens, and other secrets.

### Security warnings

Doctor flags dangerous configurations:

```
!  channels.whatsapp.dmPolicy is "open" — anyone can message your agent
   -> Consider "pairing" or "allowlist" for safety

!  gateway.auth.token is not set — local connections are unauthenticated
   -> Run: openclaw doctor --generate-gateway-token
```

---

## Config Hot Reload

You don't always need to restart the Gateway after changing config. Some changes take effect via:

### Gateway restart (in-place)

```bash
openclaw gateway restart
```

This does an in-place restart — the process reloads config without losing its PID or service supervisor connection.

### Config apply via tool

The agent itself can apply config changes:

```json5
// The gateway tool supports config operations
{ action: "config.apply", config: { /* ... */ } }
{ action: "config.patch", patch: { /* partial update */ } }
```

Both validate the config, write it, restart the Gateway, and send a wake signal.

---

## Common Misconfigurations

| Issue | Symptom | Fix |
|-------|---------|-----|
| Typo in model name | "Unknown model" error on first message | Check `agents.defaults.model` spelling |
| Missing bot token | Channel doesn't connect at startup | Add token to config or set env var |
| Wrong `allowFrom` format | Messages ignored silently | Telegram: `"tg:123456"`, WhatsApp: `"+15555550123"` |
| Legacy config keys | Gateway refuses to start | Run `openclaw doctor` |
| JSON syntax error | Parse error at startup | Check for missing commas, brackets |
| `open` DM policy without `allowFrom: ["*"]` | Confusing behavior | Add `allowFrom: ["*"]` or switch to `pairing` |

---

## A Complete Starter Config

Here's a real-world config for someone using Telegram + WhatsApp with Claude:

```json5
{
  // Agent setup
  agents: {
    defaults: {
      model: "anthropic/claude-sonnet-4-6",
      workspace: "~/.openclaw/workspace",
    },
  },

  // Channels
  channels: {
    telegram: {
      botToken: "123456789:ABCdefGHIjklMNOpqrsTUVwxyz",
      dmPolicy: "pairing",
      groups: {
        "*": { requireMention: true },
      },
    },
    whatsapp: {
      dmPolicy: "pairing",
      sendReadReceipts: true,
      groups: {
        "*": { requireMention: true },
      },
    },
  },

  // Logging
  logging: {
    level: "info",
    consoleStyle: "pretty",
  },

  // Message handling
  messages: {
    queue: "steer",  // Inject new messages into active turns
  },
}
```

> **Key Takeaway:** The config system is designed around progressive disclosure. Start with a minimal config (just a model name), then add sections as you need them. JSON5 makes it human-friendly, TypeBox validation catches mistakes at startup, and `openclaw doctor` fixes what it can automatically. When in doubt, `openclaw doctor` is always the right first step.

---

## Exercises

1. **Read your config**: Open `~/.openclaw/openclaw.json` and identify each section. Which channels are enabled? What model is configured? What DM policy is in use?

2. **Break it on purpose**: Add an invalid key (like `foo: "bar"`) to your config. Try starting the Gateway. What error do you get? Now run `openclaw doctor` — does it catch the issue?

3. **Explore the schema**: Run `openclaw config get` to see your resolved config with all defaults filled in. Compare it to your actual config file — notice how many defaults you're relying on without realizing it.

4. **Check permissions**: Run `ls -la ~/.openclaw/openclaw.json`. Is it world-readable? If so, fix it with `chmod 600`.

---

This wraps up Module 2 on Gateway Architecture. You now understand how the daemon runs, how clients communicate over WebSocket, how sessions persist to disk, and how configuration ties it all together. In Module 3, we'll dive into the **Channel System** — how OpenClaw connects to Telegram, WhatsApp, Discord, and beyond.
