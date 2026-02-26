# What is OpenClaw?

OpenClaw is a **self-hosted, multi-channel AI assistant gateway** — your own personal AI that runs on your hardware, connects to the messaging apps you already use, and talks to any LLM provider you configure.

Think of it as the _operating system_ for a personal AI assistant: it handles the plumbing so you can focus on what your assistant actually does.

---

## The One-Sentence Pitch

> **OpenClaw lets you chat with an LLM from WhatsApp, Telegram, Discord, iMessage, or any other channel — all managed from a single Gateway running on your own machine.**

---

## Key Concepts at a Glance

| Concept | What it is |
|---------|-----------|
| **Gateway** | The long-running daemon (Node.js process) that owns all connections |
| **Channel** | A messaging surface: Telegram, WhatsApp, Discord, Signal, etc. |
| **Agent** | The LLM-backed AI running inside the Gateway |
| **Session** | A conversation context (per DM, per group, per channel) |
| **Skill** | A bundled capability (tool set + instructions) loaded by the agent |
| **Node** | A companion device (iPhone, Android, macOS app) that connects to the Gateway |
| **Workspace** | The directory containing your agent's files (AGENTS.md, SOUL.md, etc.) |

---

## Why Self-Hosted?

Most AI assistants are cloud services: your messages leave your device, get processed on someone else's server, and responses come back. OpenClaw is different:

- **Privacy**: messages flow from your channels → your Gateway → your chosen LLM provider. No third-party sees your conversation history.
- **Control**: you pick the model, the tools, the channels, the persona.
- **Always-on**: the Gateway runs as a daemon (launchd/systemd), so it's running even when you're asleep.
- **Extensible**: you write Skills to add new capabilities. No approval process, no plugin store.

> **Note:** OpenClaw is _not_ the LLM itself. It doesn't run models locally (unless you configure a local provider like Ollama). It's the control plane that connects channels to LLM APIs.

---

## What OpenClaw Is Not

- ❌ Not a cloud service (unless you deploy it to a VPS)
- ❌ Not a model provider (it calls OpenAI, Anthropic, Ollama, etc.)
- ❌ Not a chatbot builder (it's a personal assistant, not a product for others)
- ❌ Not a multi-tenant platform (designed for single-user or small trusted groups)
- ❌ Not a coding IDE (though it can use coding agents like Pi)

---

## The Lobster Way 🦞

The tagline "the lobster way" refers to running your own infrastructure — being the lobster that builds its own shell rather than renting someone else's. It's a philosophy of ownership, control, and self-sufficiency.

---

## Supported Channels

OpenClaw connects to a surprisingly wide set of messaging surfaces:

**Core channels** (built-in):
- WhatsApp (via Baileys Web API)
- Telegram (via grammY)
- Discord (via Carbon)
- Slack (via Bolt)
- Google Chat
- Signal
- iMessage (macOS, via AppleScript)
- Microsoft Teams
- Matrix
- IRC
- Mattermost (plugin)
- WebChat (built-in browser UI)
- macOS menu bar app
- iOS node
- Android node

> **Tip:** You don't need to enable all channels. Start with just Telegram or WhatsApp, then add more as needed.

---

## Supported LLM Providers

OpenClaw talks to any of these model providers:

- **Anthropic** (Claude Sonnet, Haiku, Opus)
- **OpenAI** (GPT-4.1, GPT-5, o3, Codex)
- **Gemini** (via Google AI or Vertex)
- **Ollama** (local models)
- **OpenRouter** (600+ models via one API)
- **Mistral**, **Qwen**, **GLM**, **MiniMax**, **Venice**, **Bedrock**, and more
- **LiteLLM** proxy (for unified multi-provider routing)

You can configure multiple providers and switch between them per-session, per-channel, or on the fly with `/model`.

---

## The Installation Footprint

OpenClaw is a **Node.js package** installed globally:

```bash
npm install -g openclaw@latest
# or
pnpm add -g openclaw@latest
```

The Gateway is a single long-running Node process. It:
- Uses ~50-200MB RAM depending on active channels
- Stores state in `~/.openclaw/`
- Runs as a launchd/systemd user service

No Docker required for basic use (though Docker is supported). No database server. No Kubernetes. Just Node + config.

---

## The Workspace

Your agent's "home" is the workspace directory:

```
~/.openclaw/workspace/
├── AGENTS.md     ← Operating instructions + memory
├── SOUL.md       ← Persona, tone, boundaries
├── TOOLS.md      ← Tool notes (SSH hosts, API keys doc, etc.)
├── USER.md       ← Notes about the user
├── IDENTITY.md   ← Agent name, emoji, vibe
└── skills/       ← Custom skills (optional)
```

These files are injected into the agent's context at the start of each session. **Editing them changes how the agent behaves immediately** (on the next session reset).

---

## How it Feels

From the user's perspective:

1. You message your Telegram bot (or WhatsApp number, or Discord DM)
2. OpenClaw receives it, routes it to the right agent session
3. The agent processes it — potentially calling tools (run shell commands, browse web, read files)
4. The response streams back to you in the chat

It feels like talking to a very capable assistant who lives in your pocket and has access to your computer.

---

## Summary

| What | Details |
|------|---------|
| **What it is** | Self-hosted AI assistant gateway |
| **Runtime** | Node.js ≥22, runs on macOS/Linux/Windows (WSL2) |
| **Config** | `~/.openclaw/openclaw.json` (JSON5 format) |
| **Daemon** | launchd (macOS), systemd (Linux) |
| **State** | `~/.openclaw/` (sessions, pairing, auth) |
| **Models** | Any provider via config |
| **Channels** | 15+ messaging surfaces |

In the next lesson, we'll look at the **architecture** — how all the pieces fit together.
