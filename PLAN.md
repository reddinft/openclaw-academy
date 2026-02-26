# OpenClaw Academy — Project Plan

_Self-hosted "Udemy-style" course platform for deep-diving into OpenClaw architecture and codebase._

---

## Overview

A lightweight, single-user, self-hosted web training app that teaches OpenClaw internals through structured modules, code walkthroughs, architecture diagrams, and interactive quizzes. Runs entirely in Docker.

---

## Tech Stack

| Layer         | Choice                    | Rationale                                                                                 |
|---------------|---------------------------|-------------------------------------------------------------------------------------------|
| Backend       | **FastAPI** (Python 3.12) | Async, fast, minimal. Matches our image-gen-studio pattern. Great for small-footprint apps |
| Frontend      | **HTMX + Jinja2**         | No JavaScript bundle hell. Server-side rendering with reactive updates. Simple to maintain |
| Styling       | **Custom CSS (dark)**     | Tailored dark theme, no Tailwind overhead for this scale                                   |
| Code highlight| **Highlight.js**          | CDN-loaded, zero-build syntax highlighting for JSON, TypeScript, YAML, bash               |
| Diagrams      | **Mermaid.js**            | CDN-loaded, renders architecture diagrams from fenced code blocks                          |
| Progress DB   | **SQLite** (via aiosqlite)| Zero-ops, single file, perfect for single-user. Progress, quiz scores, notes               |
| Content       | **Markdown files**        | Human-editable, Git-friendly, parsed server-side with `markdown-it` (Python: `mistune`)   |
| Containers    | **Docker + Compose**      | Reproducible, volume-mounted content for easy editing                                      |

### Why NOT bigger platforms?

- **Moodle / Open edX**: Extreme overkill. Hundreds of MB images, complex DB setup, multi-user systems
- **CourseLit / Pupilfirst**: React-based, heavier build toolchain, overkill for single user
- **MkDocs / Docusaurus**: Great for docs but lack progress tracking, quizzes, interactive exercises
- **Custom FastAPI + HTMX**: Perfect fit — we control everything, minimal deps, consistent with existing stack

---

## Architecture

```
Browser
  │
  ▼
FastAPI (port 8080)
  ├── GET /                     → course index
  ├── GET /module/{id}          → module overview
  ├── GET /module/{id}/lesson/{lid} → lesson content (markdown rendered)
  ├── POST /progress            → mark lesson complete (HTMX)
  ├── POST /quiz/submit         → check quiz answers (HTMX)
  ├── GET /api/progress         → JSON progress summary
  └── Static files (/static/)

SQLite (progress.db)
  ├── lessons (id, module_id, completed, completed_at, notes)
  └── quiz_attempts (id, lesson_id, score, answers_json, attempted_at)

Content Layer (volume-mounted)
  course/
    module-01-overview/
      meta.yaml           ← title, description, order, lessons[]
      01-what-is-openclaw.md
      02-architecture-overview.md
      quiz.yaml           ← questions, answers, explanations
    module-02-gateway/
      ...
```

---

## Data Model

### SQLite Schema

```sql
CREATE TABLE lessons (
    id TEXT PRIMARY KEY,           -- e.g. "m01-l01"
    module_id TEXT NOT NULL,       -- e.g. "module-01-overview"
    lesson_slug TEXT NOT NULL,     -- e.g. "what-is-openclaw"
    completed INTEGER DEFAULT 0,
    completed_at TEXT,             -- ISO timestamp
    notes TEXT                     -- user notes (future feature)
);

CREATE TABLE quiz_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quiz_id TEXT NOT NULL,         -- e.g. "m01-quiz"
    score INTEGER NOT NULL,
    total INTEGER NOT NULL,
    answers_json TEXT NOT NULL,    -- JSON array of user answers
    attempted_at TEXT NOT NULL
);
```

---

## Content Authoring Format

### Module meta.yaml

```yaml
id: module-01-overview
title: "OpenClaw Overview"
description: "What OpenClaw is, how it works end-to-end, and how to think about it."
order: 1
icon: "🦞"
lessons:
  - slug: what-is-openclaw
    title: "What is OpenClaw?"
    file: 01-what-is-openclaw.md
    duration_min: 10
  - slug: architecture-overview
    title: "Architecture Overview"
    file: 02-architecture-overview.md
    duration_min: 15
  - slug: first-run-walkthrough
    title: "First Run Walkthrough"
    file: 03-first-run.md
    duration_min: 8
quiz_file: quiz.yaml
```

### Lesson Markdown

Standard markdown with these extensions:
- Fenced code blocks with language tags → syntax highlighted
- ` ```mermaid ` blocks → rendered as diagrams
- `> **Note:**` blockquotes → styled callouts
- `> **Warning:**` blockquotes → warning callouts
- `> **Exercise:**` blockquotes → hands-on exercise blocks

### Quiz YAML

```yaml
id: m01-quiz
title: "Module 1 Quiz"
passing_score: 70
questions:
  - id: q1
    text: "What is the primary role of the OpenClaw Gateway?"
    type: single_choice
    options:
      - id: a
        text: "A message broker that routes between LLM providers"
      - id: b
        text: "The control plane that owns all messaging surfaces and sessions"
      - id: c
        text: "A browser automation framework"
    correct: b
    explanation: "The Gateway is the single long-lived control plane that owns provider connections, sessions, and tool execution."
```

---

## Feature List

### MVP (v1.0)

- [x] Course index with module cards + progress rings
- [x] Module overview page with lesson list
- [x] Lesson viewer with rendered markdown
- [x] Syntax highlighting (JS, Python, TypeScript, JSON, YAML, bash)
- [x] Mermaid diagram rendering
- [x] Progress tracking (mark complete, persist to SQLite)
- [x] Multi-choice quizzes with immediate feedback
- [x] Quiz score tracking
- [x] Dark theme, readable typography
- [x] Docker + docker-compose.yml
- [x] Volume-mounted content (edit markdown, refresh browser)
- [x] Module 1 content fully written

### Nice-to-Have (v2.0)

- [ ] User notes per lesson (textarea, saved to SQLite)
- [ ] Keyboard navigation (j/k for lessons, n/p for modules)
- [ ] Search across all lesson content
- [ ] Code copy buttons
- [ ] Print/export lesson as PDF
- [ ] Progress export (JSON dump)
- [ ] Lesson timer (reading time counter)
- [ ] "Related lessons" cross-linking
- [ ] Admin mode to reset progress
- [ ] Table of contents sidebar per lesson

---

## Course Structure (10 Modules)

| # | Module | Lessons | Est. Time |
|---|--------|---------|-----------|
| 1 | OpenClaw Overview | 3 | ~33 min |
| 2 | Gateway Architecture | 4 | ~45 min |
| 3 | Channel System | 3 | ~35 min |
| 4 | Agent System | 4 | ~50 min |
| 5 | Skills & Hooks | 3 | ~35 min |
| 6 | Security Model | 3 | ~40 min |
| 7 | Configuration Deep Dive | 4 | ~45 min |
| 8 | Extending OpenClaw | 3 | ~40 min |
| 9 | Deployment Patterns | 3 | ~35 min |
| 10| Case Study: Our Setup | 3 | ~40 min |

**Total:** 33 lessons, ~6.5 hours of content

---

## Estimated Effort

| Phase | Task | Est. |
|-------|------|------|
| Setup | Project scaffold, Docker, FastAPI app | 2h |
| Module 1 | Full content, diagrams, quiz | 3h |
| Modules 2–5 | Content (4 modules × 2.5h avg) | 10h |
| Modules 6–10 | Content (5 modules × 2h avg) | 10h |
| Polish | CSS, UX, bug fixes | 2h |
| **Total** | | **~27h** |

---

## Docker Setup

The app runs on port `8080` internally, mapped to `8080` on the host.
Content lives in `./course/` (bind-mounted read-only for production, read-write for authoring).
SQLite lives in a named volume for persistence across restarts.

```bash
# Start
docker compose up -d

# View logs
docker compose logs -f

# Edit content (no restart needed — content is hot-reloaded)
vim course/module-01-overview/01-what-is-openclaw.md

# Stop
docker compose down
```

---

## File Layout

```
openclaw-academy/
├── PLAN.md                     ← This file
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── app/
│   ├── main.py                 ← FastAPI app entrypoint
│   ├── database.py             ← SQLite helpers (aiosqlite)
│   ├── content.py              ← Markdown + YAML course loader
│   ├── templates/
│   │   ├── base.html
│   │   ├── index.html          ← Course home
│   │   ├── module.html         ← Module overview
│   │   ├── lesson.html         ← Lesson viewer
│   │   └── quiz.html           ← Quiz page
│   └── static/
│       ├── css/style.css
│       └── js/app.js
└── course/
    ├── outline.md              ← Human-readable full outline
    ├── module-01-overview/
    │   ├── meta.yaml
    │   ├── 01-what-is-openclaw.md
    │   ├── 02-architecture-overview.md
    │   ├── 03-first-run.md
    │   └── quiz.yaml
    ├── module-02-gateway/
    │   └── meta.yaml           ← stub
    └── ...
```

---

_A community educational resource for OpenClaw — 2026_
