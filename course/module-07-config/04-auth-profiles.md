# Auth Profiles

Your Gateway needs credentials to talk to LLM providers, and those credentials need to be stored securely, rotated when they expire, and fall back gracefully when one set fails. In this lesson we'll cover the two authentication models (OAuth and API keys), credential storage, rotation, and multi-profile setups.

---

## Two Auth Models

OpenClaw supports two fundamentally different ways to authenticate with model providers:

| Model | How it works | Best for |
|-------|-------------|----------|
| **API Key** | Static secret string sent with every request | Most providers (OpenAI, Google, Mistral, etc.) |
| **OAuth** | Token exchange flow — short-lived access tokens refreshed automatically | Anthropic (subscription-based access) |

```mermaid
graph LR
    subgraph API_KEY["API Key Flow"]
        K1["You"] -->|"set env var<br/>or config"| K2["Gateway"]
        K2 -->|"Authorization: Bearer sk-..."| K3["Provider API"]
    end

    subgraph OAUTH["OAuth Flow"]
        O1["You"] -->|"openclaw models auth"| O2["Browser"]
        O2 -->|"authorize"| O3["Provider"]
        O3 -->|"tokens"| O4["Gateway"]
        O4 -->|"access token<br/>(auto-refreshed)"| O5["Provider API"]
    end
```

---

## API Key Authentication

### Setting Up API Keys

The simplest approach — get a key from your provider's dashboard and tell OpenClaw about it:

**Option 1: Environment Variable (Recommended)**

```bash
# In your shell profile (~/.zshrc, ~/.bashrc)
export ANTHROPIC_API_KEY="sk-ant-api03-..."
export OPENAI_API_KEY="sk-..."
export GOOGLE_AI_API_KEY="AIza..."
```

OpenClaw auto-detects standard env var names. No config needed.

**Option 2: Config File (with env var reference)**

```json5
{
  models: {
    providers: {
      anthropic: {
        apiKey: "${ANTHROPIC_API_KEY}"   // References the env var
      }
    }
  }
}
```

**Option 3: Config File (inline — not recommended)**

```json5
{
  models: {
    providers: {
      anthropic: {
        apiKey: "sk-ant-api03-actual-key-here"   // Stored in plain text!
      }
    }
  }
}
```

> **Key Takeaway:** Never store API keys directly in config files that might be committed to version control. Use environment variables or a secret manager.

### Auto-Detected Environment Variables

| Provider | Variable | Format |
|----------|----------|--------|
| Anthropic | `ANTHROPIC_API_KEY` | `sk-ant-...` |
| OpenAI | `OPENAI_API_KEY` | `sk-...` |
| Google AI | `GOOGLE_AI_API_KEY` | `AIza...` |
| Google Vertex | `GOOGLE_APPLICATION_CREDENTIALS` | Path to JSON credentials file |
| OpenRouter | `OPENROUTER_API_KEY` | `sk-or-...` |
| Mistral | `MISTRAL_API_KEY` | String |
| Groq | `GROQ_API_KEY` | `gsk_...` |
| AWS Bedrock | `AWS_ACCESS_KEY_ID` + `AWS_SECRET_ACCESS_KEY` | Standard AWS creds |

---

## OAuth Authentication

### The Anthropic OAuth Flow

Anthropic supports an OAuth-based authentication called the **setup-token flow**. Instead of managing API keys, you authenticate through your Anthropic account (like logging into a website):

```bash
openclaw models auth anthropic
```

This command:
1. Opens your browser to Anthropic's authorization page
2. You log in and approve access
3. Tokens are returned and saved locally
4. The Gateway uses these tokens for API calls
5. Tokens auto-refresh when they expire

### Where OAuth Tokens Are Stored

```
~/.openclaw/agents/<agentId>/agent/auth-profiles.json
```

This file contains:

```json5
{
  "anthropic": {
    "accessToken": "eyJ...",
    "refreshToken": "rt_...",
    "expiresAt": "2026-03-15T10:30:00Z",
    "accountId": "acct_...",
    "profile": "default"
  }
}
```

> **Important:** The `auth-profiles.json` file contains sensitive tokens. Ensure its permissions are restrictive: `chmod 600 auth-profiles.json`.

### Token Refresh

OAuth access tokens are short-lived (typically hours). OpenClaw handles refresh automatically:

```mermaid
sequenceDiagram
    participant GW as Gateway
    participant AUTH as Auth Store
    participant API as Anthropic API

    GW->>AUTH: Get access token
    AUTH-->>GW: Token (expired!)
    GW->>API: POST /oauth/token (refresh_token)
    API-->>GW: New access_token + refresh_token
    GW->>AUTH: Save updated tokens
    GW->>API: Call with new access_token
    API-->>GW: Response
```

If the refresh token itself expires (rare — typically months), you'll need to re-authenticate:

```bash
openclaw models auth anthropic --reauth
```

---

## Multiple Auth Profiles

You can configure multiple authentication profiles for the same provider — useful when you have personal and work accounts:

```json5
{
  models: {
    providers: {
      anthropic: {
        profiles: {
          personal: {
            apiKey: "${ANTHROPIC_PERSONAL_KEY}"
          },
          work: {
            apiKey: "${ANTHROPIC_WORK_KEY}"
          }
        },
        defaultProfile: "personal"
      }
    }
  }
}
```

### Per-Agent Credential Selection

Different agents can use different auth profiles:

```json5
{
  agents: {
    entries: {
      main: {
        authProfile: "personal"    // Uses personal Anthropic key
      },
      work: {
        authProfile: "work"        // Uses work Anthropic key
      }
    }
  }
}
```

### Per-Session Selection

You can even switch profiles mid-conversation (if allowed by the model allowlist):

```
/auth work       ← Switch to work credentials
/auth personal   ← Switch back to personal
```

---

## Fallback Authentication

When your primary credentials fail (expired, rate-limited, revoked), OpenClaw can fall back to alternative credentials:

```json5
{
  models: {
    providers: {
      anthropic: {
        // Primary: OAuth
        auth: "oauth",
        // Fallback: API key
        fallbackApiKey: "${ANTHROPIC_API_KEY}"
      }
    }
  }
}
```

### Fallback Flow

```mermaid
graph TD
    REQ["API Request"] --> OAUTH{OAuth token<br/>valid?}
    OAUTH -->|Yes| USE_OAUTH["Use OAuth token"]
    OAUTH -->|No| REFRESH{Refresh<br/>succeeds?}
    REFRESH -->|Yes| USE_REFRESH["Use refreshed token"]
    REFRESH -->|No| FALLBACK{Fallback<br/>API key set?}
    FALLBACK -->|Yes| USE_KEY["Use API key"]
    FALLBACK -->|No| FAIL["❌ Auth failed"]
```

This pattern — OAuth primary with API key fallback — gives you the convenience of OAuth (no key management, auto-refresh) with the reliability of a static key as a safety net.

---

## API Key Rotation

For API keys, rotation means replacing the old key with a new one. OpenClaw supports configuration-level rotation:

```json5
{
  models: {
    providers: {
      openai: {
        apiKey: "${OPENAI_API_KEY}",
        rotation: {
          enabled: true,
          // Check key validity on startup
          validateOnStartup: true,
          // Warn N days before expected expiry (if provider supports it)
          warnBeforeExpiryDays: 7
        }
      }
    }
  }
}
```

### Rotation Best Practices

| Practice | Why |
|----------|-----|
| Use env vars, not inline keys | Rotate by changing the env var, not the config file |
| Set up key expiry alerts | Provider dashboards usually support this |
| Have a fallback key ready | Generate a spare key before rotating |
| Rotate in off-hours | If something goes wrong, you want to be available to fix it |
| Test after rotation | Run `openclaw models status --probe` to verify |

### Rotation Workflow

```bash
# 1. Generate new key in provider dashboard

# 2. Update env var
export OPENAI_API_KEY="sk-new-key-here"

# 3. Verify it works
openclaw models status --probe

# 4. Revoke old key in provider dashboard

# 5. Restart Gateway to pick up new env var
openclaw restart
```

---

## Credential Storage Security

### Where Credentials Live

| Credential type | Stored at | Format |
|----------------|-----------|--------|
| API keys (env var) | Shell environment | Not persisted by OpenClaw |
| API keys (config) | `~/.openclaw/openclaw.json` | JSON5 |
| OAuth tokens | `~/.openclaw/agents/<id>/agent/auth-profiles.json` | JSON |
| Channel tokens | Config or env vars | Varies |
| Pairing tokens | `~/.openclaw/credentials/<channel>-allowFrom.json` | JSON |

### Security Checklist

| Check | Command | Expected |
|-------|---------|----------|
| Config file permissions | `ls -la ~/.openclaw/openclaw.json` | `-rw-------` (600) |
| Auth profiles permissions | `ls -la ~/.openclaw/agents/main/agent/auth-profiles.json` | `-rw-------` (600) |
| No keys in git | `grep -r "sk-" ~/.openclaw/` | Only in non-committed files |
| State dir permissions | `ls -la ~/.openclaw/` | `drwx------` (700) |

Run the security audit to check all of these automatically:

```bash
openclaw security audit --check permissions
```

---

## Integration Patterns

### 1Password / Secret Manager Integration

While OpenClaw doesn't directly integrate with secret managers, you can use them via env vars:

```bash
# 1Password CLI
export ANTHROPIC_API_KEY=$(op read "op://Personal/Anthropic/api-key")

# AWS Secrets Manager
export OPENAI_API_KEY=$(aws secretsmanager get-secret-value \
  --secret-id openai-key --query SecretString --output text)
```

Set these in your shell profile or systemd/launchd service definition.

### Per-Environment Configs

Use `$include` with environment-specific credential files:

```json5
// openclaw.json
{
  models: {
    providers: { $include: "./providers-${ENVIRONMENT}.json5" }
  }
}
```

```json5
// providers-production.json5
{
  anthropic: { apiKey: "${ANTHROPIC_PROD_KEY}" },
  openai: { apiKey: "${OPENAI_PROD_KEY}" }
}
```

---

## Troubleshooting Auth Issues

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| 401 on every request | Invalid or missing API key | Check `openclaw models status --probe` |
| 401 after working fine | Key rotated or revoked | Re-generate key, update env var |
| OAuth token won't refresh | Refresh token expired | Run `openclaw models auth <provider> --reauth` |
| "No credentials found" | Env var not set in daemon context | Check launchd/systemd env; use `openclaw doctor` |
| Works in CLI, fails in daemon | Shell env vars not available to daemon | Set env vars in service definition |
| Rate limited (429) | Too many requests with one key | Set up failover to a different provider/key |

---

## Summary

| Concept | Details |
|---------|---------|
| **API keys** | Static secrets — set via env vars or config |
| **OAuth** | Token exchange — `openclaw models auth <provider>` |
| **Token storage** | `~/.openclaw/agents/<id>/agent/auth-profiles.json` |
| **Auto-refresh** | OAuth tokens refreshed transparently |
| **Fallback auth** | OAuth primary → API key fallback |
| **Multiple profiles** | Personal/work keys per agent |
| **Rotation** | Update env var → probe → revoke old key |
| **Security** | File permissions 600, no keys in git |

---

> **Exercise:**
> 1. Run `openclaw models status --probe` — are all your providers authenticated?
> 2. If you're using inline API keys in your config, migrate them to environment variables.
> 3. Check the permissions on your credential files: `ls -la ~/.openclaw/agents/main/agent/`. Fix any that are too permissive.
> 4. If you use Anthropic, try the OAuth flow: `openclaw models auth anthropic`. Compare the experience to API key auth.

---

That wraps up Module 7. You now have a thorough understanding of OpenClaw's configuration system — from JSON5 syntax to model failover to credential management. In the next module, we'll explore **extending OpenClaw** with custom channels, tools, and integrations.
