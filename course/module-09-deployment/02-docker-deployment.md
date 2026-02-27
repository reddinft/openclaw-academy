# Docker Deployment

Docker gives you a containerized, reproducible OpenClaw environment. It's ideal for VPS hosting, team setups, and environments where you don't want to manage Node.js installations directly. In this lesson, you'll learn how to run the Gateway in Docker, configure volumes and networking, and manage the container lifecycle.

---

## When to Use Docker

| Use case | Docker? |
|----------|---------|
| VPS / cloud server (Hetzner, DigitalOcean, etc.) | Yes |
| Team-shared Gateway | Yes |
| Isolated, reproducible environment | Yes |
| Local dev on your own machine | Probably not — native install is simpler |
| Agent sandboxing only (host Gateway) | Docker for sandbox, not for Gateway |

> **Key Takeaway:** Docker is _optional_ for the Gateway itself. Agent sandboxing uses Docker too, but that doesn't require the Gateway to run in a container. Two separate concerns.

---

## Quick Start

From the OpenClaw repository root:

```bash
./docker-setup.sh
```

This script:
1. Builds the gateway image
2. Runs the onboarding wizard
3. Generates a gateway token and writes it to `.env`
4. Starts the gateway via Docker Compose

After it finishes, open `http://127.0.0.1:18789/` and paste the token into the Control UI.

---

## The Docker Compose File

Here's what a production `docker-compose.yml` looks like:

```yaml
services:
  openclaw-gateway:
    image: ${OPENCLAW_IMAGE:-openclaw:local}
    build: .
    restart: unless-stopped
    env_file:
      - .env
    environment:
      - HOME=/home/node
      - NODE_ENV=production
      - TERM=xterm-256color
      - OPENCLAW_GATEWAY_BIND=${OPENCLAW_GATEWAY_BIND:-lan}
      - OPENCLAW_GATEWAY_PORT=${OPENCLAW_GATEWAY_PORT:-18789}
      - OPENCLAW_GATEWAY_TOKEN=${OPENCLAW_GATEWAY_TOKEN}
    volumes:
      - ${OPENCLAW_CONFIG_DIR:-~/.openclaw}:/home/node/.openclaw
      - ${OPENCLAW_WORKSPACE_DIR:-~/.openclaw/workspace}:/home/node/.openclaw/workspace
    ports:
      - "127.0.0.1:${OPENCLAW_GATEWAY_PORT:-18789}:18789"
    command:
      [
        "node", "dist/index.js", "gateway",
        "--bind", "${OPENCLAW_GATEWAY_BIND:-lan}",
        "--port", "${OPENCLAW_GATEWAY_PORT:-18789}",
        "--allow-unconfigured",
      ]

  openclaw-cli:
    image: ${OPENCLAW_IMAGE:-openclaw:local}
    build: .
    profiles: ["cli"]
    env_file:
      - .env
    environment:
      - HOME=/home/node
    volumes:
      - ${OPENCLAW_CONFIG_DIR:-~/.openclaw}:/home/node/.openclaw
      - ${OPENCLAW_WORKSPACE_DIR:-~/.openclaw/workspace}:/home/node/.openclaw/workspace
    entrypoint: ["node", "dist/index.js"]
```

---

## Environment Variables

Create a `.env` file (never commit this):

```bash
OPENCLAW_IMAGE=openclaw:local
OPENCLAW_GATEWAY_TOKEN=change-me-now          # openssl rand -hex 32
OPENCLAW_GATEWAY_BIND=lan
OPENCLAW_GATEWAY_PORT=18789

OPENCLAW_CONFIG_DIR=/home/you/.openclaw
OPENCLAW_WORKSPACE_DIR=/home/you/.openclaw/workspace
```

### Key Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `OPENCLAW_GATEWAY_TOKEN` | Auth token for Control UI and API | Required |
| `OPENCLAW_GATEWAY_BIND` | Network bind (`local`, `lan`, `0.0.0.0`) | `lan` in Docker |
| `OPENCLAW_GATEWAY_PORT` | WebSocket port | `18789` |
| `OPENCLAW_CONFIG_DIR` | Host path for config + state | `~/.openclaw` |
| `OPENCLAW_WORKSPACE_DIR` | Host path for agent workspace | `~/.openclaw/workspace` |

---

## Volume Mounts: What Persists Where

Docker containers are ephemeral. All long-lived state must live on the host via volume mounts:

| Component | Container path | Host mount | Notes |
|-----------|---------------|------------|-------|
| Gateway config | `/home/node/.openclaw/` | `~/.openclaw/` | openclaw.json, tokens, auth |
| Workspace | `/home/node/.openclaw/workspace/` | `~/.openclaw/workspace/` | AGENTS.md, skills, etc. |
| WhatsApp session | `/home/node/.openclaw/` | `~/.openclaw/` | Preserves QR login |
| Logs | `/home/node/.openclaw/logs/` | `~/.openclaw/logs/` | Gateway + agent logs |
| External binaries | `/usr/local/bin/` | Docker image | Must be baked at build time |

> **Key Takeaway:** Anything installed at runtime (npm packages, apt packages, binaries) is lost when the container restarts. If a skill needs a binary, bake it into the Dockerfile.

---

## Baking Binaries into the Image

This is critical for production. If your skills depend on external binaries, install them at build time:

```dockerfile
FROM node:22-bookworm

# System packages
RUN apt-get update && apt-get install -y \
    socat jq curl \
    && rm -rf /var/lib/apt/lists/*

# Example: install a CLI binary from GitHub Releases
RUN curl -L https://github.com/example/tool/releases/latest/download/tool_Linux_x86_64.tar.gz \
  | tar -xz -C /usr/local/bin && chmod +x /usr/local/bin/tool

WORKDIR /app
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml .npmrc ./
COPY ui/package.json ./ui/package.json
COPY scripts ./scripts

RUN corepack enable
RUN pnpm install --frozen-lockfile

COPY . .
RUN pnpm build
RUN pnpm ui:install
RUN pnpm ui:build

ENV NODE_ENV=production
CMD ["node","dist/index.js"]
```

### Adding Binaries Later

When you add a new skill that needs a binary:

1. Update the Dockerfile
2. Rebuild: `docker compose build`
3. Restart: `docker compose up -d openclaw-gateway`

---

## Optional Enhancements

### Extra Host Mounts

Mount additional directories from the host:

```bash
export OPENCLAW_EXTRA_MOUNTS="$HOME/.codex:/home/node/.codex:ro,$HOME/github:/home/node/github:rw"
./docker-setup.sh
```

### Persist `/home/node` (Named Volume)

For caches, browser downloads, and tool state that should survive container recreation:

```bash
export OPENCLAW_HOME_VOLUME="openclaw_home"
./docker-setup.sh
```

### Extra System Packages

```bash
export OPENCLAW_DOCKER_APT_PACKAGES="ffmpeg build-essential"
./docker-setup.sh
```

---

## Channel Setup in Docker

Configure channels using the CLI container:

```bash
# WhatsApp (QR code scan)
docker compose run --rm openclaw-cli channels login

# Telegram (bot token)
docker compose run --rm openclaw-cli channels add --channel telegram --token "BOT_TOKEN"

# Discord (bot token)
docker compose run --rm openclaw-cli channels add --channel discord --token "BOT_TOKEN"
```

---

## Networking and Access

### Local Access Only (Recommended)

The default binds to `127.0.0.1` — only accessible from the host:

```yaml
ports:
  - "127.0.0.1:18789:18789"
```

Access from your laptop via SSH tunnel:

```bash
ssh -N -L 18789:127.0.0.1:18789 user@your-server
```

Then open `http://127.0.0.1:18789/` locally.

### LAN Access

Remove the `127.0.0.1:` prefix to expose on all interfaces:

```yaml
ports:
  - "18789:18789"
```

Make sure your firewall is configured and `OPENCLAW_GATEWAY_TOKEN` is strong.

---

## Agent Sandboxing (Host Gateway + Docker Tools)

Even with a native (non-Docker) gateway, you can sandbox agent tool execution in Docker containers:

```json5
{
  agents: {
    defaults: {
      sandbox: {
        mode: "non-main",
        scope: "agent",
        docker: {
          image: "openclaw-sandbox:bookworm-slim",
          network: "none",
          memory: "1g",
        },
      },
    },
  },
}
```

Build the sandbox image:

```bash
scripts/sandbox-setup.sh
```

This is separate from running the Gateway in Docker. The Gateway runs on the host; only tool execution is containerized.

---

## Permissions and EACCES

The Docker image runs as `node` (uid 1000). If you see permission errors:

```bash
# Linux host: fix ownership
sudo chown -R 1000:1000 ~/.openclaw ~/.openclaw/workspace
```

On macOS with Docker Desktop, file sharing handles this automatically for most paths.

---

## Health Checks

```bash
# Container health
docker compose exec openclaw-gateway \
  node dist/index.js health --token "$OPENCLAW_GATEWAY_TOKEN"

# View logs
docker compose logs -f openclaw-gateway

# Shell into the container
docker compose exec openclaw-gateway bash
```

---

## ClawDock Shell Helpers

For easier day-to-day management:

```bash
mkdir -p ~/.clawdock && curl -sL \
  https://raw.githubusercontent.com/openclaw/openclaw/main/scripts/shell-helpers/clawdock-helpers.sh \
  -o ~/.clawdock/clawdock-helpers.sh

echo 'source ~/.clawdock/clawdock-helpers.sh' >> ~/.zshrc && source ~/.zshrc
```

Then use: `clawdock-start`, `clawdock-stop`, `clawdock-dashboard`, `clawdock-logs`, etc.

---

## Docker Deployment Checklist

```
[ ] Clone OpenClaw repo
[ ] Create .env with strong OPENCLAW_GATEWAY_TOKEN
[ ] Set OPENCLAW_CONFIG_DIR and OPENCLAW_WORKSPACE_DIR
[ ] Bake required binaries into Dockerfile
[ ] Build: docker compose build
[ ] Run onboarding: docker compose run --rm openclaw-cli onboard
[ ] Start gateway: docker compose up -d openclaw-gateway
[ ] Verify: docker compose logs -f openclaw-gateway
[ ] Access Control UI: http://127.0.0.1:18789/ (via SSH tunnel if remote)
[ ] Configure channels: docker compose run --rm openclaw-cli channels login
[ ] Set up log rotation for container logs (Docker daemon level)
```

---

## Summary

| Topic | Key point |
|-------|-----------|
| **Quick start** | `./docker-setup.sh` handles everything |
| **Persistence** | Volume mounts for `~/.openclaw/` and workspace |
| **Binaries** | Bake into Dockerfile, not installed at runtime |
| **Networking** | Bind to `127.0.0.1` + SSH tunnel for security |
| **Channels** | Configure via `openclaw-cli` container |
| **Sandboxing** | Separate from Gateway Docker — host Gateway + Docker sandbox |
| **Permissions** | Container runs as uid 1000 (`node` user) |

---

## Exercise

1. Write a `docker-compose.yml` from scratch that runs OpenClaw with volume mounts for config and workspace
2. Add a Dockerfile section that installs `jq` and `curl` as baked-in binaries
3. Set up an SSH tunnel from your laptop to a remote Docker instance and access the Control UI
4. **Bonus:** Configure agent sandboxing with a separate sandbox image and `network: "none"`

---

In the next lesson, we'll cover **Linux VPS deployment** — systemd, nginx reverse proxy, Tailscale, and production hardening.
