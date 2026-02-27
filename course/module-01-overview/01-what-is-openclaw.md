# What is OpenClaw?

OpenClaw is a self-hosted, multi-channel AI assistant gateway: your own AI running on your hardware, connected to the messaging apps you already use, talking to whichever LLM you configure.

Think of it as the operating system for a personal AI assistant. It handles the plumbing so you can focus on what your assistant actually does.

---

## The one-sentence pitch

> OpenClaw lets you chat with an LLM from WhatsApp, Telegram, Discord, iMessage, or any other channel — all managed from a single Gateway running on your own machine.

---

## Concepts at a glance

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

## Why self-hosted?

Most AI assistants are cloud services: your messages leave your device, get processed on someone else's server, and the responses come back. OpenClaw keeps that pipeline on your hardware:

- Messages flow from your channels to your Gateway to your chosen LLM provider. No third party sees your conversation history.
- You pick the model, the tools, the channels, the persona.
- The Gateway runs as a daemon (launchd/systemd), so it's available even when you're not at your computer.
- Adding capabilities means writing a Skill. No approval process, no plugin store.

> **Note:** OpenClaw is _not_ the LLM itself. It doesn't run models locally (unless you configure a local provider like Ollama). It's the control plane that connects channels to LLM APIs.

---

## What OpenClaw is not

It's not a cloud service (unless you deploy it to a VPS), and it doesn't provide models — it calls OpenAI, Anthropic, Ollama, and others. It's also not a chatbot builder; this is a personal assistant, not a product you'd hand to other people. Multi-tenant platforms, coding IDEs — none of that. It's a single-user (or small trusted group) gateway.

---

## The lobster way

The tagline "the lobster way" means running your own infrastructure — building your own shell rather than renting someone else's. You own the stack.

---

## Supported channels

OpenClaw connects to a wide set of messaging surfaces.

Built-in:
- WhatsApp (via Baileys Web API)
- Telegram (via grammY)
- Discord (via Carbon)
- Slack (via Bolt)
- Google Chat
- Signal
- iMessage (macOS, via BlueBubbles)
- Microsoft Teams
- Matrix
- IRC
- Mattermost (plugin)
- WebChat (built-in browser UI)
- macOS menu bar app
- and more via plugins

Nodes (companion devices, distinct from channels):
- iOS
- Android

> **Tip:** You don't need to enable all channels. Start with just Telegram or WhatsApp, then add more as needed.

---

## Supported LLM providers

OpenClaw talks to any of these model providers:

- Anthropic (Claude Sonnet, Haiku, Opus)
- OpenAI (GPT-4.1, GPT-5, o3, Codex)
- Gemini (via Google AI or Vertex)
- Ollama (local models)
- OpenRouter (600+ models via one API)
- Mistral, Qwen, GLM, MiniMax, Venice, Bedrock, and more
- LiteLLM proxy (for unified multi-provider routing)

You can configure multiple providers and switch between them per-session, per-channel, or on the fly with `/model`.

---

## The installation footprint

OpenClaw is a Node.js package installed globally:

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

## The workspace

Your agent's home is the workspace directory:

```
~/.openclaw/workspace/
├── AGENTS.md     ← Operating instructions + memory
├── SOUL.md       ← Persona, tone, boundaries
├── TOOLS.md      ← Tool notes (SSH hosts, API keys doc, etc.)
├── USER.md       ← Notes about the user
├── IDENTITY.md   ← Agent name, emoji, vibe
└── skills/       ← Custom skills (optional)
```

These files are injected into the agent's context at the start of each session. Edit them and the behavior changes on the next session reset. You'll find yourself tweaking these often.

---

## How it feels

From your perspective:

1. You message your Telegram bot (or WhatsApp number, or Discord DM)
2. OpenClaw receives it, routes it to the right agent session
3. The agent processes it — potentially calling tools (run shell commands, browse web, read files)
4. The response streams back to you in the chat

It feels like talking to a capable assistant who lives in your pocket and has access to your computer.

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

The next lesson covers the architecture: how all the pieces fit together.
