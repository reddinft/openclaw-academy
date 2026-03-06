# Contributing to OpenClaw Academy

Thanks for wanting to contribute. The academy is a community resource — every lesson that gets better or completed helps everyone learning OpenClaw.

---

## What we most need

### 🚧 Stub modules (highest priority)

Three modules are placeholder stubs. Pull requests that fill these in are very welcome:

- **Module 7 — Configuration Deep Dive** (`course/module-07-config/`)
  - Config file format (JSON5), schema validation, `openclaw doctor`
  - Model config, agent config, auth profiles
  
- **Module 8 — Extending OpenClaw** (`course/module-08-extending/`)
  - Writing a skill end-to-end
  - Custom routing by channel/sender
  - MCP server integration

- **Module 10 — Case Study** (`course/module-10-case-study/`)
  - Real-world multi-agent setup
  - Skills and governance in production
  - Lessons learned

### 📝 Content improvements

- Factual corrections as OpenClaw evolves (config keys change, APIs update)
- "From the Trenches" sidebars — short callouts with real incidents, gotchas, or war stories
- Better code examples and diagrams (Mermaid.js supported natively)
- Quiz questions for modules that are missing them

### 🐛 Platform bugs

- Issues with the FastAPI app, HTMX interactions, progress tracking
- Docker/deployment improvements
- Accessibility fixes

---

## How to write a lesson

Content lives in `course/module-XX-name/`. Each module has:

```
module-02-gateway/
├── meta.yaml           ← module metadata + lesson list
├── 01-gateway-daemon.md
├── 02-websocket-protocol.md
└── quiz.yaml           ← optional quiz
```

**meta.yaml format:**
```yaml
title: "Gateway Architecture"
description: "How the OpenClaw gateway daemon works under the hood."
order: 2
lessons:
  - slug: "gateway-daemon"
    title: "The Gateway Daemon"
  - slug: "websocket-protocol"
    title: "WebSocket Protocol"
```

**Lesson format (Markdown):**
- Use `##` for section headers (not `#` — that's the lesson title from meta.yaml)
- Code blocks with language tags: ` ```typescript `, ` ```json `, ` ```bash `
- Mermaid diagrams: ` ```mermaid `
- Keep lessons focused — 500–1500 words is the sweet spot
- Use **bold** sparingly (max 3–4 per section)
- Avoid AI writing patterns: no em-dash overuse, no "it's worth noting", no "in conclusion"

See `course/module-01-overview/01-what-is-openclaw.md` as the reference standard.

**Quiz format (quiz.yaml):**
```yaml
passing_score: 70
questions:
  - question: "What protocol does the gateway use for agent communication?"
    options:
      - "REST/HTTP"
      - "WebSocket"
      - "gRPC"
      - "MQTT"
    answer: 1   # 0-indexed
    explanation: "The gateway uses WebSocket for bidirectional real-time communication."
```

---

## Workflow

1. **Fork** the repo
2. **Open an issue first** for new modules or major changes — lets us coordinate
3. For small fixes (typos, factual corrections), just open a PR directly
4. **Test locally** with `docker compose up -d` or the dev server
5. Submit a **PR with a clear description** of what changed and why

---

## Content licensing

All course content (`course/` directory) is licensed under **CC-BY-SA 4.0**.

By submitting a content contribution, you agree your work will be published under CC-BY-SA 4.0. This means others can share and adapt it, provided they give credit and use the same license.

Code contributions (app/, templates, etc.) are MIT.

---

## Accuracy

OpenClaw evolves. If you notice a lesson is out of date:

- Check the [OpenClaw changelog](https://github.com/openclaw/openclaw/releases) for the relevant change
- Update the lesson and note in the PR which version introduced the change
- If unsure, open an issue flagging the discrepancy

---

*Questions? Open an issue or join the [OpenClaw Discord](https://discord.com/invite/clawd).*
