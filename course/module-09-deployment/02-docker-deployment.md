# Docker deployment

Docker is optional for running OpenClaw. The direct Node.js install (macOS LaunchAgent, systemd on Linux) is simpler for most people. Docker earns its place when you need the same image to run identically across machines (reproducibility), want no Node version conflicts with other projects on the host (isolation), need to move to a new server by repointing the volume mounts (portability), or are running Gateway + Langfuse + other services together in one Compose file.

One thing to be clear about: the Gateway running in Docker is just the Gateway. The LLM models still run in the cloud. You're not trying to run Claude or GPT inside a container. Docker here means OpenClaw's control plane runs in a container; it still calls out to Anthropic/OpenAI over the internet.

---

## Quick start

From the OpenClaw repo root:

```bash
./docker-setup.sh
```

This script:
1. Builds the gateway image (`openclaw:local`)
2. Runs the onboarding wizard in a container
3. Prints optional provider setup hints
4. Starts the Gateway via Docker Compose
5. Generates a gateway token and writes it to `.env`

After it finishes:

```bash
# Open the control UI in your browser
open http://127.0.0.1:18789/
# Paste the token from .env into Settings → Token
```

---

## The Docker Compose file

The generated `docker-compose.yml` looks roughly like this:

```yaml
version: "3.8"

services:
  openclaw-gateway:
    image: openclaw:local
    restart: unless-stopped
    volumes:
      - ~/.openclaw:/home/node/.openclaw          # config + sessions
      - ~/.openclaw/workspace:/home/node/.openclaw/workspace  # agent workspace
    ports:
      - "127.0.0.1:18789:18789"                   # loopback only (secure default)
    environment:
      - NODE_ENV=production
      - OPENCLAW_GATEWAY_TOKEN=${OPENCLAW_GATEWAY_TOKEN}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      # Add your other API keys here

  openclaw-cli:
    image: openclaw:local
    volumes:
      - ~/.openclaw:/home/node/.openclaw
      - ~/.openclaw/workspace:/home/node/.openclaw/workspace
    profiles: ["cli"]   # only starts when you explicitly run it
    entrypoint: ["openclaw"]
```

---

## Volume mounts: what goes where

The two critical mounts are:

| Host path | Container path | What it holds |
|-----------|---------------|---------------|
| `~/.openclaw/` | `/home/node/.openclaw/` | Config (`openclaw.json`), sessions, channel credentials, skills |
| `~/.openclaw/workspace/` | `/home/node/.openclaw/workspace/` | Agent workspace (AGENTS.md, SOUL.md, memory, etc.) |

These mounts mean state persists outside the container. You can delete and recreate the container without losing sessions, paired channels, or workspace files.

> Permissions: the image runs as `node` (UID 1000). If you see `EACCES` errors on host volumes, fix ownership:
> ```bash
> sudo chown -R 1000:1000 ~/.openclaw
> ```

### Optional: persist the entire container home

If you want to keep caches (Playwright browsers, model downloads) across container recreation:

```bash
export OPENCLAW_HOME_VOLUME="openclaw_home"
./docker-setup.sh
```

This creates a named Docker volume mounted at `/home/node`, with the standard config/workspace bind mounts on top.

---

## Networking: loopback vs bridge

### Default: loopback binding

The default Compose config binds port 18789 to `127.0.0.1` (loopback) only:

```yaml
ports:
  - "127.0.0.1:18789:18789"
```

This means the Gateway is only reachable from the same machine. Secure by default, the Control UI isn't exposed to the network.

To access the Control UI from another machine, use an SSH tunnel:

```bash
# From your laptop, tunnel to the Docker host
ssh -L 18789:localhost:18789 user@docker-host
# Then open http://localhost:18789 on your laptop
```

### LAN / Tailnet binding

To expose the Gateway to your local network or Tailscale:

```yaml
ports:
  - "0.0.0.0:18789:18789"  # all interfaces (LAN)
```

Or configure via OpenClaw:

```bash
openclaw config set gateway.bind lan   # LAN
openclaw config set gateway.bind tailnet  # Tailscale IP only
```

> Never expose 18789 to the public internet without authentication. The default token-based auth is sufficient for Tailscale, but if you open it publicly, use a reverse proxy with TLS plus the gateway's token auth (or add a password via `gateway.auth.mode`).

### Host networking

For channels that need low-level network access (uncommon), you can use `network_mode: host`:

```yaml
services:
  openclaw-gateway:
    network_mode: host
```

This gives the container direct access to the host's network interfaces. Usually not needed.

---

## Using the CLI container

The `openclaw-cli` service runs one-off commands against the same config/workspace:

```bash
# Check gateway status
docker compose run --rm openclaw-cli gateway status

# Link WhatsApp (shows QR code)
docker compose run --rm openclaw-cli channels login --channel whatsapp

# Approve a pairing request
docker compose run --rm openclaw-cli pairing approve telegram <CODE>

# View logs
docker compose logs -f openclaw-gateway
```

---

## Multi-container setups: Gateway and services

One of Docker's best features is Compose files that bring up your whole stack. A useful pattern:

```yaml
version: "3.8"

services:
  openclaw-gateway:
    image: openclaw:local
    restart: unless-stopped
    volumes:
      - ~/.openclaw:/home/node/.openclaw
    ports:
      - "127.0.0.1:18789:18789"
    depends_on:
      - langfuse
    environment:
      - LANGFUSE_HOST=http://langfuse:3000
      - LANGFUSE_PUBLIC_KEY=${LANGFUSE_PUBLIC_KEY}
      - LANGFUSE_SECRET_KEY=${LANGFUSE_SECRET_KEY}

  langfuse:
    image: ghcr.io/langfuse/langfuse:latest
    ports:
      - "127.0.0.1:3000:3000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/langfuse
    depends_on:
      - db

  db:
    image: postgres:16
    volumes:
      - pgdata:/var/lib/postgresql/data
    environment:
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=langfuse

volumes:
  pgdata:
```

Now `openclaw gateway` and your Langfuse observability stack come up with a single `docker compose up -d`.

---

## Agent sandboxing in Docker

OpenClaw can run agent tool execution (the `exec` tool) inside isolated Docker containers, even when the Gateway itself isn't in Docker. This is the sandbox feature:

```json5
{
  agents: {
    defaults: {
      sandbox: {
        mode: "non-main",   // sandbox non-main sessions only
        scope: "agent",     // one container per agent
        docker: {
          image: "openclaw-sandbox:bookworm-slim",
          network: "none",  // no internet access in sandbox
          memory: "512m"
        }
      }
    }
  }
}
```

Build the sandbox image:

```bash
scripts/sandbox-setup.sh
```

This is separate from the Gateway container. It's a security boundary for tool execution, not a deployment choice.

---

## Updating the Gateway container

```bash
# Pull latest
docker build -t openclaw:local -f Dockerfile .
# Or: docker pull openclaw/openclaw:latest (if using published images)

# Restart the Gateway with the new image
docker compose up -d --force-recreate openclaw-gateway
```

Run `openclaw doctor` after updates to catch any config schema changes:

```bash
docker compose run --rm openclaw-cli doctor
```

---

## Troubleshooting

### Container exits immediately

```bash
docker compose logs openclaw-gateway
# Look for startup errors — usually a missing required config value
```

### Permission errors on volumes

```bash
# Fix ownership on the host
sudo chown -R 1000:1000 ~/.openclaw
```

### WhatsApp QR not appearing

The QR scan needs an interactive terminal:

```bash
docker compose run --rm -it openclaw-cli channels login --channel whatsapp
```

### Gateway is unreachable after container restart

Check the port binding and whether the old container is still running:

```bash
docker compose ps
docker compose down && docker compose up -d
```

---

## Exercise

1. If you have Docker installed, run `docker compose up -d` from an OpenClaw project directory and watch the Gateway come up in a container.
2. Use `docker compose run --rm openclaw-cli gateway status` to verify the container is healthy.
3. Think through it: you're moving your OpenClaw setup to a new server. What do you need to copy? (Hint: what's in the volumes?)

---

In the next lesson, we'll cover Linux VPS deployment, the right approach for an always-on server you can rely on.
