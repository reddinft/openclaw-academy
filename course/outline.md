# OpenClaw Academy — Full Course Outline

## Module 1: OpenClaw Overview ✅ (complete)
*What OpenClaw is, how it works end-to-end, and how to think about the system.*

- Lesson 1: What is OpenClaw? — Concept, philosophy, supported channels/providers
- Lesson 2: Architecture Overview — Gateway, channels, agents, sessions, nodes
- Lesson 3: End-to-End Message Flow — Trace a message from phone to response
- Quiz: 7 questions

---

## Module 2: Gateway Architecture
*Deep dive into the control plane: WebSocket protocol, session management, connection lifecycle.*

- Lesson 1: The Gateway Daemon — launchd/systemd setup, startup, health
- Lesson 2: WebSocket Protocol — Wire format, request/response, events, idempotency
- Lesson 3: Session Store — Keys, JSONL transcripts, maintenance, pruning
- Lesson 4: Configuration System — openclaw.json schema, JSON5, validation, doctor
- Quiz: 6 questions

---

## Module 3: Channel System
*How messaging platforms connect and how messages flow in/out.*

- Lesson 1: Channel Plugin Architecture — How channels are structured as plugins
- Lesson 2: Telegram & WhatsApp — grammY vs Baileys, pairing, DM policy, group policy
- Lesson 3: Discord, Slack & Others — Carbon, Bolt, allowlists, channel routing
- Quiz: 5 questions

---

## Module 4: Agent System
*The AI runtime: LLM calls, tool execution, memory, compaction, multi-agent.*

- Lesson 1: Agent Lifecycle — Turn model, queue modes (steer/followup/collect), steering
- Lesson 2: Tool System — Tool policy, sandbox vs elevated, tool categories
- Lesson 3: Memory & Compaction — Context window, auto-compaction, memory flush
- Lesson 4: Multi-Agent Routing — Multiple agents, per-agent workspaces, routing rules
- Quiz: 6 questions

---

## Module 5: Skills & Hooks
*The extensibility system: skill loading, workspace files, hook system.*

- Lesson 1: Skill Anatomy — SKILL.md, scripts, assets, meta.yaml structure
- Lesson 2: Skill Loading — Bundled vs managed vs workspace skills, name conflicts
- Lesson 3: Hooks & Workspace Files — Hook system, HEARTBEAT.md, cron, webhooks
- Quiz: 5 questions

---

## Module 6: Security Model
*Trust boundaries, prompt injection defenses, elevated mode, sandboxing.*

- Lesson 1: Trust Hierarchy — Owner vs approved users vs untrusted inbound content
- Lesson 2: Prompt Injection Defenses — EXTERNAL_UNTRUSTED_CONTENT markers, sanitization
- Lesson 3: Tool Policy & Sandboxing — sandbox vs tool-policy vs elevated, what each means
- Quiz: 5 questions

---

## Module 7: Configuration Deep Dive
*The openclaw.json schema: every major block, key defaults, common patterns.*

- Lesson 1: Config Structure & Validation — JSON5 format, schema, openclaw doctor
- Lesson 2: Model Configuration — Providers, aliases, failover, model-by-channel
- Lesson 3: Agent Configuration — workspace, bootstrap, tools, compaction, session
- Lesson 4: Auth Profiles — OAuth vs API keys, rotation, fallbacks
- Quiz: 6 questions

---

## Module 8: Extending OpenClaw
*Writing skills, custom channel routing, MCP integration.*

- Lesson 1: Writing a Skill — SKILL.md format, tool registration, testing
- Lesson 2: Custom Routing — Multi-agent setups, channel routing rules
- Lesson 3: MCP Integration — Model Context Protocol, mcporter, server wiring
- Quiz: 5 questions

---

## Module 9: Deployment Patterns
*macOS launchd, Docker, systemd on Linux, VPS/cloud deployment.*

- Lesson 1: macOS Deployment — launchd plist, log rotation, PATH shims, updates
- Lesson 2: Docker Deployment — Official Docker image, environment vars, volumes
- Lesson 3: Linux/VPS Deployment — systemd service, nginx reverse proxy, Tailscale VPN
- Quiz: 5 questions

---

## Module 10: Case Study — Our Hybrid Setup
*How we built on top of OpenClaw: our config, skills, memory backend, and control plane.*

- Lesson 1: Our Architecture — Mac Mini setup, Tailscale mesh, pf firewall, QMD memory
- Lesson 2: Our Skills & Workflows — insight-engine, langfuse-backup, inbox-cleanup, and more
- Lesson 3: Lessons Learned — What worked, what didn't, tips from production use
- Quiz: 4 questions

---

**Total: 10 modules · 33 lessons · ~6.5 hours of content**

*Module 1 is fully written. Modules 2–10 are stubs awaiting content development.*
