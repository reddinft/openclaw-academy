# macOS deployment

Your Mac is where most people start with OpenClaw, and for good reason: Node.js is already there, your development environment is there, and the tools you use every day are there. Running the Gateway on your Mac means your agent has access to your filesystem, your camera, AppleScript, and the macOS companion app's full capabilities.

This lesson covers getting OpenClaw installed, running as a background service, and staying running reliably.

---

## Node.js version requirements

OpenClaw requires Node.js 22 or higher. Some channel libraries (particularly WhatsApp's Baileys) depend on features in Node 22, so older versions won't work.

Don't use Bun as the Gateway runtime. Bun is flagged as incompatible for stable WhatsApp/Telegram Gateway operation. Use Node.

Check what you have:

```bash
node --version
# Should show v22.x.x or higher
```

If you're on an older version, use [nvm](https://github.com/nvm-sh/nvm) or [Homebrew](https://brew.sh):

```bash
# Via Homebrew
brew install node@24
brew link node@24

# Via nvm
nvm install 24
nvm use 24
nvm alias default 24
```

---

## Installing OpenClaw

```bash
npm install -g openclaw@latest
```

Or with pnpm (preferred if you use pnpm for other projects):

```bash
pnpm add -g openclaw@latest
```

Verify:

```bash
openclaw --version
```

The install puts `openclaw` in your global npm bin path. Everything lives in:

```
~/.openclaw/
├── openclaw.json        ← main config
├── workspace/           ← default agent workspace
├── agents/              ← session transcripts
├── credentials/         ← channel auth (WhatsApp session, etc.)
└── skills/              ← managed skills
```

---

## Running onboarding

The fastest path to a working setup:

```bash
openclaw onboard --install-daemon
```

The wizard walks you through:
1. Model provider auth (API keys)
2. Channel setup (Telegram is fastest — just paste your bot token)
3. Gateway token generation
4. LaunchAgent installation (auto-start on login)

If you want to skip the wizard and configure manually, you can, but the wizard is worth running at least once.

---

## LaunchAgent setup for auto-start

On macOS, background services run as LaunchAgents (user-level, start on login) or LaunchDaemons (system-level, start on boot). OpenClaw uses a LaunchAgent so it runs as you, with access to your home directory.

### Installing the LaunchAgent

```bash
openclaw gateway install
```

This creates `~/Library/LaunchAgents/bot.molt.gateway.plist` and loads it.

To verify it loaded:

```bash
launchctl list | grep molt
# Should show: 0  -  bot.molt.gateway
```

### Starting, stopping, and restarting

```bash
# Start
launchctl kickstart -k gui/$UID/bot.molt.gateway

# Stop
launchctl bootout gui/$UID/bot.molt.gateway

# Load (if not currently loaded)
launchctl bootstrap gui/$UID ~/Library/LaunchAgents/bot.molt.gateway.plist
```

> From the docs: the safer restart sequence (avoids issues if `openclaw` isn't in the launchd PATH) is:
> ```bash
> launchctl stop bot.molt.gateway && sleep 2 && launchctl start bot.molt.gateway
> ```

### Checking status

```bash
openclaw gateway status

# Or check logs directly
openclaw logs --follow
```

### The LaunchAgent plist

If you want to inspect or manually edit it:

```bash
cat ~/Library/LaunchAgents/bot.molt.gateway.plist
```

Key fields:
- `RunAtLoad: true` — starts when the plist is loaded (login)
- `KeepAlive: true` — relaunches if the process crashes
- `EnvironmentVariables` — injects API keys and PATH into the process

---

## Keeping it running: sleep prevention

The Gateway needs a network connection to send and receive messages. When your Mac sleeps, the network drops, channels disconnect, and messages queue up until the machine wakes.

For a desktop Mac (Mac Mini, iMac) or a MacBook kept plugged in: System Settings → Battery → Prevent Mac from sleeping automatically when the display is off. Or disable sleep entirely for the adapter.

For a MacBook you actually carry around: `caffeinate` prevents sleep while running:

```bash
# Keep network alive while caffeinate runs (not useful for LaunchAgent)
caffeinate -s -w $(pgrep -f "openclaw gateway")
```

Honestly, for a MacBook, design your channels to handle reconnects gracefully rather than trying to prevent sleep entirely. OpenClaw does this automatically with exponential backoff, and the Gateway reconnects within seconds of waking.

### What happens on reconnect

When the Mac wakes:
1. Channels detect disconnection (or get a connection error)
2. Each channel plugin starts reconnecting with exponential backoff
3. Telegram long polling resumes — any messages received while asleep are processed immediately
4. WhatsApp WebSocket re-establishes — pending messages are delivered
5. Discord and Slack WebSockets reconnect — messages received while disconnected depend on the platform's delivery guarantees

The LaunchAgent's `KeepAlive: true` handles process crashes. The channels handle network drops. Both are automatic.

---

## The macOS companion app

The [OpenClaw macOS companion app](https://openclaw.ai/download) adds:

- Menu bar status and controls
- macOS TCC permissions management (Notifications, Camera, Screen Recording, Accessibility, Microphone)
- Canvas (agent-driven visual workspace)
- iMessage access via AppleScript
- `system.run` for executing commands in a trusted context

The companion app can run or attach to the Gateway. In Local mode (default), it uses the same LaunchAgent you installed above. You don't need the app for basic functionality, but if you want Camera, Screen Recording, or iMessage, you need it.

---

## Updating OpenClaw

```bash
npm install -g openclaw@latest
openclaw gateway restart
```

Or the two-step safe restart:

```bash
npm install -g openclaw@latest
launchctl stop bot.molt.gateway && sleep 2 && launchctl start bot.molt.gateway
```

Check the current version:

```bash
openclaw --version
```

OpenClaw follows a rolling release. Breaking changes are documented in the changelog. Running `openclaw doctor` after an update catches config schema issues:

```bash
openclaw doctor
# If it finds issues: openclaw doctor --fix
```

---

## Troubleshooting

### Gateway won't start

```bash
openclaw gateway status
openclaw doctor --non-interactive
openclaw logs --follow
```

### LaunchAgent not loading

```bash
# Unload and reload
launchctl bootout gui/$UID ~/Library/LaunchAgents/bot.molt.gateway.plist
launchctl bootstrap gui/$UID ~/Library/LaunchAgents/bot.molt.gateway.plist
```

### Port conflict (18789 already in use)

```bash
lsof -i :18789
# Kill the conflicting process, or change the Gateway port in config
```

### "node not found" in launchd

The LaunchAgent runs in a minimal environment. If you installed Node via nvm, the launchd process may not find it. Fix by adding the full path to `EnvironmentVariables.PATH` in the plist, or use the Homebrew Node (which installs to `/opt/homebrew/bin/node` and is always in the PATH).

---

## Exercise

1. Run `node --version`. If you're below v22, upgrade.
2. Run `openclaw --version`. Confirm it's installed.
3. Run `openclaw gateway status`. Is the Gateway running?
4. Run `launchctl list | grep molt`. Is the LaunchAgent loaded?
5. Stop and start the Gateway manually using `launchctl`. Watch the logs reconnect.

---

In the next lesson, we'll cover Docker deployment — the containerised path that makes OpenClaw reproducible and portable.
