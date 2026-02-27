# macOS Deployment

Running OpenClaw on macOS means running it as a proper system service — not a terminal process you have to babysit. In this lesson, you'll learn how to set up OpenClaw as a launchd daemon, handle the macOS-specific gotchas around sleep, TCC permissions, PATH, and log rotation, and keep the gateway updated.

This is the deployment pattern for Mac Mini servers, MacBook always-on setups, and the macOS companion app.

---

## launchd: The macOS Service Manager

On macOS, background services run via **launchd** — Apple's init system. OpenClaw installs itself as a LaunchAgent (per-user daemon) that starts automatically at login and restarts if it crashes.

### Install the Daemon

The easiest way:

```bash
openclaw onboard --install-daemon
```

This creates a plist file at:

```
~/Library/LaunchAgents/ai.openclaw.gateway.plist
```

### Manual plist

If you need more control, here's the structure of the plist:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>ai.openclaw.gateway</string>

  <key>ProgramArguments</key>
  <array>
    <string>/opt/homebrew/Cellar/node@24/24.14.0/bin/node</string>
    <string>/Users/you/.npm-global/lib/node_modules/openclaw/dist/index.js</string>
    <string>gateway</string>
  </array>

  <key>EnvironmentVariables</key>
  <dict>
    <key>HOME</key>
    <string>/Users/you</string>
    <key>PATH</key>
    <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin</string>
    <key>NODE_ENV</key>
    <string>production</string>
  </dict>

  <key>KeepAlive</key>
  <true/>

  <key>RunAtLoad</key>
  <true/>

  <key>StandardOutPath</key>
  <string>/Users/you/.openclaw/logs/gateway.log</string>

  <key>StandardErrorPath</key>
  <string>/Users/you/.openclaw/logs/gateway.err</string>
</dict>
</plist>
```

### Start / Stop / Restart

```bash
# Load and start
launchctl load ~/Library/LaunchAgents/ai.openclaw.gateway.plist

# Stop
launchctl stop ai.openclaw.gateway

# Start (after stop)
launchctl start ai.openclaw.gateway

# Unload (fully remove)
launchctl unload ~/Library/LaunchAgents/ai.openclaw.gateway.plist
```

> **Key Takeaway:** Always use `launchctl stop` + wait 2 seconds + `launchctl start` instead of trying to "restart." There's no native restart command for LaunchAgents. Wait at least 15 seconds after start before testing.

---

## The PATH Problem

LaunchAgents run with a minimal PATH — typically just `/usr/bin:/bin:/usr/sbin:/sbin`. Your Homebrew tools, NVM Node, and custom binaries won't be found unless you explicitly set PATH in the plist.

### Solution: Bake PATH into EnvironmentVariables

```xml
<key>EnvironmentVariables</key>
<dict>
  <key>PATH</key>
  <string>/opt/homebrew/bin:/Users/you/.local/bin:/usr/local/bin:/usr/bin:/bin</string>
</dict>
```

Include every directory that contains binaries your skills need:
- `/opt/homebrew/bin` — Homebrew tools
- `~/.local/bin` — GitHub release binaries
- `~/.npm-global/bin` — Global npm packages
- `~/go/bin` — Go binaries

### Why Not `launchctl setenv`?

If your plist has its own `EnvironmentVariables` block, **it completely overrides** `launchctl setenv`. The two don't merge. This is the single most confusing macOS gotcha:

```bash
# This does NOTHING for a LaunchAgent with its own EnvironmentVariables:
launchctl setenv MY_SECRET "hunter2"
```

Always bake environment variables directly into the plist:

```bash
/usr/libexec/PlistBuddy -c \
  "Add :EnvironmentVariables:MY_SECRET string $VALUE" \
  ~/Library/LaunchAgents/ai.openclaw.gateway.plist
```

Then reload:

```bash
launchctl unload ~/Library/LaunchAgents/ai.openclaw.gateway.plist
launchctl load ~/Library/LaunchAgents/ai.openclaw.gateway.plist
```

---

## Preventing Sleep with caffeinate

macOS default power settings are designed for laptops, not servers. The default `sleep` value can put the whole machine to sleep after an hour of idle — which silently drops every incoming message.

### The Fix

Create a separate LaunchAgent for `caffeinate`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.openclaw.caffeinate</string>

  <key>ProgramArguments</key>
  <array>
    <string>/usr/bin/caffeinate</string>
    <string>-s</string>
    <string>-i</string>
  </array>

  <key>KeepAlive</key>
  <true/>

  <key>RunAtLoad</key>
  <true/>
</dict>
</plist>
```

| Flag | Purpose |
|------|---------|
| `-s` | Prevent idle system sleep on AC power |
| `-i` | Prevent idle sleep |

No admin rights needed. `KeepAlive: true` means launchd restarts it if it ever exits. The display still sleeps (screen off), but the machine stays running.

### Verify It's Working

```bash
pmset -g assertions | grep caffeinate
```

If you see a caffeinate assertion, your machine won't sleep. Also check:

```bash
pmset -g | grep "^ *sleep"
```

If it shows anything other than `0`, your daemon has been silently dropping messages during sleep windows.

---

## TCC Permissions (Transparency, Consent, and Control)

macOS ties file access permissions to the **exact binary path** — not the process name, not the user, the path. This has serious implications for OpenClaw:

### The Problem

If you grant disk access to `/opt/homebrew/Cellar/node@24/24.14.0/bin/node` and then switch to `~/.nvm/versions/node/v24.14.0/bin/node`, macOS silently revokes all permissions. The gateway loses access to protected directories without any error message.

### The Rules

1. **Lock your plist to one Node binary path.** Don't switch between NVM and Homebrew.
2. **Grant permissions while sitting at the machine.** TCC prompts require interactive approval — no remote, no headless.
3. **After upgrading Node**, check if the binary path changed. Homebrew minor version bumps can change the Cellar path.

### Checking TCC Status

```bash
# See what has Full Disk Access
sqlite3 ~/Library/Application\ Support/com.apple.TCC/TCC.db \
  "SELECT client FROM access WHERE service='kTCCServiceSystemPolicyAllFiles'"
```

If your Node binary isn't listed, the gateway can't access protected directories.

### The macOS Companion App

The OpenClaw macOS app (`OpenClaw.app`) handles TCC differently — it requests permissions through the standard macOS approval flow. If you use the app, TCC is managed for you through System Settings > Privacy & Security.

The app provides:
- Menu bar gateway control
- Exec approvals (approve/deny tool execution)
- Camera, screen recording, and canvas access
- Deep links via `openclaw://` URL scheme

---

## Log Rotation

Gateway logs live at `~/.openclaw/logs/`:

```
~/.openclaw/logs/
├── gateway.log      ← stdout
└── gateway.err      ← stderr
```

These grow without bound unless you rotate them. macOS doesn't have logrotate by default, so you have two options:

### Option 1: newsyslog (built-in)

Create `/etc/newsyslog.d/openclaw.conf`:

```
# logfile                                      mode count size when  flags
/Users/you/.openclaw/logs/gateway.log          644  5     1024 *     J
/Users/you/.openclaw/logs/gateway.err          644  5     1024 *     J
```

This rotates when the file hits 1MB, keeps 5 archives, and compresses them (J = bzip2).

### Option 2: Cron + Manual Rotation

```bash
# Add to crontab -e:
0 0 * * * mv ~/.openclaw/logs/gateway.log ~/.openclaw/logs/gateway.log.$(date +\%Y\%m\%d) && launchctl stop ai.openclaw.gateway && sleep 2 && launchctl start ai.openclaw.gateway
```

---

## Updating OpenClaw

### Manual Update

```bash
npm update -g openclaw@latest
# Then restart the daemon:
launchctl stop ai.openclaw.gateway
sleep 2
launchctl start ai.openclaw.gateway
```

### Auto-Update

OpenClaw includes a built-in updater. Configure it in `openclaw.json`:

```json5
{
  system: {
    updates: {
      auto: true,
      channel: "stable",   // stable | beta | dev
    },
  },
}
```

Update channels:

| Channel | Description |
|---------|-------------|
| `stable` | Production releases, well-tested |
| `beta` | Pre-release features, mostly stable |
| `dev` | Bleeding edge, may break things |

Check current version and available updates:

```bash
openclaw version
openclaw update --check
```

---

## Non-Admin User Considerations

Running OpenClaw under a standard (non-admin) macOS account is good security practice but introduces friction:

| Issue | Workaround |
|-------|-----------|
| Can't `brew install` | Use static binaries from GitHub Releases → `~/.local/bin/` |
| Can't modify `/opt/homebrew` | Ask admin to install, or avoid Homebrew entirely |
| Can't change system settings | Use per-user LaunchAgents (don't need admin) |
| Some tools need admin | Document which tools need admin install (e.g., TTS engines) |

The strategy: keep the daemon user minimal. Install static binaries where possible. Only escalate to admin when absolutely necessary.

---

## Complete macOS Deployment Checklist

```
[ ] Install OpenClaw: npm install -g openclaw@latest
[ ] Run onboarding: openclaw onboard
[ ] Install daemon: openclaw onboard --install-daemon
[ ] Verify plist PATH includes all needed binary dirs
[ ] Bake API keys into plist EnvironmentVariables
[ ] Install caffeinate LaunchAgent
[ ] Verify sleep prevention: pmset -g assertions
[ ] Grant TCC permissions at the machine
[ ] Lock Node binary path (don't switch between NVM/Homebrew)
[ ] Set up log rotation (newsyslog or cron)
[ ] Configure auto-update channel
[ ] Test: send a message from each channel and verify response
```

---

## Summary

| Topic | Key point |
|-------|-----------|
| **Service manager** | launchd via `~/Library/LaunchAgents/` |
| **Install** | `openclaw onboard --install-daemon` |
| **Restart** | `launchctl stop` + sleep 2 + `launchctl start` |
| **PATH** | Bake into plist `EnvironmentVariables` |
| **Env vars** | PlistBuddy, not `launchctl setenv` |
| **Sleep** | `caffeinate -s -i` as a separate LaunchAgent |
| **TCC** | Lock binary path, grant permissions at the machine |
| **Logs** | `~/.openclaw/logs/`, rotate with newsyslog |
| **Updates** | `openclaw update` or auto-update in config |

---

## Exercise

1. Write a `caffeinate` LaunchAgent plist from scratch (don't copy-paste — understand each key)
2. Use `PlistBuddy` to add a test environment variable to your gateway plist, then verify it's visible inside the gateway process
3. Check your current `pmset -g` output and identify whether your machine would sleep during an overnight run
4. **Bonus:** Set up newsyslog rotation for gateway logs with a 7-day, 5MB limit

---

In the next lesson, we'll containerize everything with **Docker deployment**.
