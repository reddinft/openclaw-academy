# 🦞 OpenClaw Academy

A self-hosted "Udemy-style" course platform for deep-diving into OpenClaw's architecture and codebase.

**Single-user · Docker · Dark theme · Markdown-based content · Progress tracking · Quizzes**

> **Disclaimer:** This is a community educational resource. It is not officially affiliated with or endorsed by the OpenClaw project.

---

## Quick Start

```bash
# Clone the repo
git clone https://github.com/reddinft/openclaw-academy.git
cd openclaw-academy

# Start with Docker Compose
docker compose up -d

# Open in browser
open http://localhost:8080
```

## Development (without Docker)

```bash
# Install Python dependencies (Python 3.11+ recommended)
pip install -r requirements.txt

# Run the dev server (hot-reload)
COURSE_DIR=./course DATA_DIR=/tmp DB_PATH=/tmp/academy.db \
  python3 -m uvicorn app.main:app --reload --port 8080

# Open in browser
open http://localhost:8080
```

## Static Export (for Vercel / GitHub Pages)

```bash
# Export to dist/ directory
python3 scripts/export_static.py

# Preview locally
cd dist && python3 -m http.server 8090
open http://localhost:8090
```

## Course Structure

| # | Module | Lessons |
|---|--------|---------|
| 1 | OpenClaw Overview | 3 |
| 2 | Gateway Architecture | 4 |
| 3 | Channel System | 3 |
| 4 | Agent System | 4 |
| 5 | Skills & Hooks | 3 |
| 6 | Security Model | 3 |
| 7 | Configuration Deep Dive | 4 |
| 8 | Extending OpenClaw | 3 |
| 9 | Deployment Patterns | 3 |
| 10 | Case Study: Real-World Setup | 3 |

**Total:** 33 lessons + 10 quizzes, ~6.5 hours of content

## Authoring Content

Add/edit lessons in `course/module-XX-*/`:
- `meta.yaml` — module metadata + lesson list
- `NN-lesson-name.md` — lesson content (markdown)
- `quiz.yaml` — quiz questions

Content changes take effect immediately (no restart needed in dev mode).

See `course/module-01-overview/` for a complete example.

## Tech Stack

- **FastAPI** + **HTMX** + **Jinja2** — backend + reactive UI
- **mistune** — markdown rendering
- **highlight.js** — code syntax highlighting
- **Mermaid.js** — architecture diagrams from fenced blocks
- **aiosqlite** — progress tracking
- **Docker + Compose** — containerised deployment

## Files

```
openclaw-academy/
├── LICENSE              ← MIT (code)
├── LICENSE-CONTENT      ← CC-BY-SA 4.0 (course content)
├── NOTICES.md           ← Third-party attributions
├── README.md            ← This file
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── scripts/
│   └── export_static.py ← Static site generator
├── vercel.json          ← Vercel deployment config
├── app/
│   ├── main.py          ← FastAPI routes
│   ├── database.py      ← SQLite helpers
│   ├── content.py       ← Markdown/YAML loader
│   ├── templates/       ← Jinja2 HTML templates
│   └── static/          ← CSS + JS
└── course/
    ├── outline.md       ← Full course outline
    └── module-*/        ← Module content
```

---

## License

This project uses a **dual license**:

- **Code** (everything except `course/`): [MIT License](LICENSE)
- **Course content** (`course/` directory): [Creative Commons Attribution-ShareAlike 4.0 International](LICENSE-CONTENT)

You are free to:
- Use, modify, and distribute the code under the MIT license
- Share and adapt the course content, provided you give appropriate credit and distribute under the same CC-BY-SA 4.0 license

See [NOTICES.md](NOTICES.md) for full third-party attributions.

---

## Attribution

This platform teaches [OpenClaw](https://github.com/openclaw/openclaw) — an open-source personal AI assistant framework. We are grateful to the OpenClaw project and its contributors.

**OpenClaw** — Copyright 2025 Peter Steinberger — MIT License
https://github.com/openclaw/openclaw

---

## Contributing

PRs are welcome! Please note:

- **Code contributions** are accepted under the MIT license
- **Content contributions** (lessons, quizzes, course material) fall under **CC-BY-SA 4.0** — by submitting content, you agree your contribution will be licensed under CC-BY-SA 4.0
- Open an issue first for major changes so we can discuss the approach
- Keep lessons technically accurate and up to date with OpenClaw

---

_A community educational resource for OpenClaw_
