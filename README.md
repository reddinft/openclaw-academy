# 🦞 OpenClaw Academy

A free, open-source course platform for learning [OpenClaw](https://github.com/openclaw/openclaw) — the self-hosted AI agent framework.

**10 modules · 33 lessons · Quizzes · Progress tracking · Dark theme · Runs in Docker**

→ **Live demo:** https://openclaw-academy.fly.dev/  
→ **Patches welcome** — see [Contributing](#contributing)

> **Disclaimer:** Community educational resource. Not officially affiliated with the OpenClaw project.

---

## Quick Start (Docker)

```bash
git clone https://github.com/reddinft/openclaw-academy.git
cd openclaw-academy
docker compose up -d
open http://localhost:8080
```

That's it. No database setup, no env vars, no build step.

## Development (without Docker)

```bash
git clone https://github.com/reddinft/openclaw-academy.git
cd openclaw-academy

pip install -r requirements.txt

COURSE_DIR=./course DB_PATH=/tmp/academy.db \
  python3 -m uvicorn app.main:app --reload --port 8080

open http://localhost:8080
```

Requires Python 3.11+.

---

## Course Content

| # | Module | Lessons | Status |
|---|--------|---------|--------|
| 1 | OpenClaw Overview | 3 | ✅ Complete |
| 2 | Gateway Architecture | 4 | ✅ Complete |
| 3 | Channel System | 3 | ✅ Complete |
| 4 | Agent System | 4 | ✅ Complete |
| 5 | Skills & Hooks | 3 | ✅ Complete |
| 6 | Security Model | 3 | ✅ Complete |
| 7 | Configuration Deep Dive | 4 | 🚧 Stub — help wanted |
| 8 | Extending OpenClaw | 3 | 🚧 Stub — help wanted |
| 9 | Deployment Patterns | 3 | ✅ Complete |
| 10 | Case Study: Real-World Setup | 3 | 🚧 Stub — help wanted |

Modules 7, 8, and 10 are stubs. **We'd love PRs filling these in.**

---

## Contributing

PRs are very welcome — especially for:

- **Filling in stub modules** (7, 8, 10) — see `course/module-07-config/`, `module-08-extending/`, `module-10-case-study/`
- **Fixing factual errors** as OpenClaw evolves
- **Adding "From the Trenches" sidebars** — real-world gotchas and incident stories
- **New modules** — suggest via issue first
- **Bug fixes** in the platform code

See [CONTRIBUTING.md](CONTRIBUTING.md) for full guidelines.

---

## Authoring Content

Content lives in `course/module-XX-name/`:

```
module-02-gateway/
├── meta.yaml           ← title, description, lesson order
├── 01-gateway-daemon.md
├── 02-websocket-protocol.md
└── quiz.yaml           ← questions + answers
```

See `course/module-01-overview/` as the reference example. Content changes take effect immediately in dev mode — no restart needed.

---

## Tech Stack

| Layer | Choice |
|-------|--------|
| Backend | FastAPI + Python 3.12 |
| Frontend | HTMX + Jinja2 (no JS bundle) |
| Styling | Custom CSS, dark theme |
| Code highlighting | highlight.js (CDN) |
| Diagrams | Mermaid.js (CDN) |
| Progress DB | SQLite via aiosqlite |
| Analytics | GoatCounter + server-side middleware |
| Deployment | Docker + Fly.io (Sydney) |

---

## Self-Hosting on Fly.io

```bash
# Install flyctl
curl -fsSL https://fly.io/install.sh | sh

# Authenticate
flyctl auth login

# Create app + persistent volume
flyctl apps create openclaw-academy --org personal
flyctl volumes create academy_data --region syd --size 1 --app openclaw-academy --yes

# Deploy
flyctl deploy --remote-only
```

The included `fly.toml` targets Sydney (`syd`) and uses `auto_stop_machines = "stop"` so the app sleeps when idle — keeping it free tier friendly.

---

## Project Structure

```
openclaw-academy/
├── LICENSE              ← MIT (code)
├── LICENSE-CONTENT      ← CC-BY-SA 4.0 (course content)
├── CONTRIBUTING.md      ← How to contribute
├── Dockerfile
├── docker-compose.yml
├── fly.toml             ← Fly.io deployment config
├── requirements.txt
├── app/
│   ├── main.py          ← FastAPI routes + /stats page
│   ├── database.py      ← SQLite progress tracking
│   ├── content.py       ← Markdown/YAML loader
│   ├── analytics.py     ← Server-side hit logging + bot detection
│   ├── templates/       ← Jinja2 HTML templates
│   └── static/          ← CSS + JS
└── course/
    ├── outline.md
    └── module-*/
```

---

## License

**Dual licensed:**

- **Code** (`app/`, `Dockerfile`, etc.): [MIT License](LICENSE)
- **Course content** (`course/`): [CC-BY-SA 4.0](LICENSE-CONTENT)

Content contributions are accepted under CC-BY-SA 4.0. By submitting a content PR, you agree your contribution will be licensed under those terms.

---

## Attribution

This platform teaches [OpenClaw](https://github.com/openclaw/openclaw) by Peter Steinberger — MIT License.

---

*Built by [Redditech](https://reddi.tech) · Deployed by an AI agent · Sydney, Australia*
