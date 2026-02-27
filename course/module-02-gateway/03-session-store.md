# Session store

Sessions are how OpenClaw remembers who you are and what you talked about. Each conversation gets its own session — a unique key, a transcript file on disk, and metadata tracking token counts and timestamps.

This isn't a database. It's a disciplined set of files that the Gateway reads and writes directly.

---

## What is a session?

A session is the unit of **conversation continuity**. Every time you send a message from a particular chat (a Telegram DM, a Discord channel, a WhatsApp group), OpenClaw maps it to a session:

- A **unique session key** — a string that identifies this conversation
- A **JSONL transcript file** — every message, tool call, and tool result, in order
- **Metadata** — token counts, creation time, last updated timestamp, channel origin

Sessions don't expire automatically. A conversation you had six months ago is still accessible if the transcript is intact.

---

## Session key format

Session keys follow a structured format:

```
agent:<agentId>:<mainKey>
```

The `mainKey` part encodes the channel, the type of conversation, and the participant ID:

```
telegram:dm:821071206          ← Telegram DM from user 821071206
telegram:group:-1001234567890  ← Telegram group
discord:channel:123456789      ← Discord channel
whatsapp:dm:+15555550123       ← WhatsApp DM
```

So a full session key looks like:

```
agent:main:telegram:dm:821071206
```

This means: agent `main`, Telegram DM, peer `821071206`.

> **Multi-agent note:** With multiple agents, the `agentId` part changes. If you have an agent called `work`, its DMs become `agent:work:telegram:dm:821071206`. Sessions are never shared between agents — isolation is built into the key.

---

## DM scope: controlling the main session

The `dmScope` setting controls how direct messages are keyed. This is a powerful lever.

| `dmScope` | Session key for DMs | Effect |
|-----------|--------------------|-|
| `main` (default) | `agent:<id>:main` | All DMs share one session. Consistent memory regardless of which channel you message from. |
| `channel` | `agent:<id>:<channel>:dm:<peer>` | Per-channel isolation |
| `peer` | `agent:<id>:peer:<peer>` | Per-sender isolation (same sender across different channels = same session) |
| `channel-peer` | `agent:<id>:<channel>:dm:<peer>` | Per-channel and per-sender (fully isolated) |

The default `main` scope means your Telegram DM and your WhatsApp DM both read from the same session. Usually what you want — the agent has continuous memory regardless of which app you message from.

Configure it in your `openclaw.json`:

```json5
{
  agents: {
    defaults: {
      session: {
        dmScope: "main"   // main | channel | peer | channel-peer
      }
    }
  }
}
```

---

## Where sessions live on disk

All session data lives under `~/.openclaw/`:

```
~/.openclaw/
└── agents/
    └── main/
        └── sessions/
            ├── sessions.json          ← Session registry (key → session ID + metadata)
            └── <SessionId>.jsonl      ← Conversation transcript (one message per line)
```

### The session registry (`sessions.json`)

A JSON file mapping session keys to session IDs and metadata:

```json
{
  "agent:main:main": {
    "sessionId": "ses_abc123",
    "sessionKey": "agent:main:main",
    "createdAt": "2026-01-15T10:00:00Z",
    "updatedAt": "2026-02-27T08:30:00Z",
    "tokenCount": 48523,
    "channel": "telegram"
  }
}
```

The Gateway looks up this registry every time a message arrives to find the right transcript file.

### The transcript (`<SessionId>.jsonl`)

Each line in the `.jsonl` file is one event in the conversation:

```jsonl
{"role":"user","content":"What's the weather in Sydney?","timestamp":"2026-02-27T08:30:00.000Z"}
{"role":"assistant","content":[{"type":"tool_use","id":"toolu_01","name":"get_weather","input":{"location":"Sydney"}}],"timestamp":"2026-02-27T08:30:01.000Z"}
{"role":"user","content":[{"type":"tool_result","tool_use_id":"toolu_01","content":"{\"temp\":22}"}],"timestamp":"2026-02-27T08:30:02.000Z"}
{"role":"assistant","content":"It's 22°C in Sydney right now.","timestamp":"2026-02-27T08:30:03.000Z"}
```

JSONL (JSON Lines) is one JSON object per line, plain text. You can read it with any text editor, `cat`, or `jq`.

---

## Session lifecycle

### Creation

When a message arrives with no existing session:
1. Gateway generates a new `sessionId`
2. Creates an entry in `sessions.json`
3. Creates a new empty `.jsonl` file
4. First agent turn injects workspace bootstrap files (AGENTS.md, SOUL.md, etc.) into the system prompt

### Active use

Each turn:
1. Gateway reads the transcript into memory
2. Agent processes the turn (LLM call, tool calls)
3. New messages appended to the `.jsonl` file
4. Token count updated in `sessions.json`

Sessions are read from disk once per session and held in memory while active. There's no per-turn file I/O after the initial load.

### Compaction

When the transcript grows large enough to approach the model's context window limit, **auto-compaction** triggers:

1. A summary of the older history is written
2. Older messages are replaced with the summary in memory
3. The transcript on disk is updated with the compacted form
4. A `compaction` event is emitted on the WebSocket stream

Compaction is automatic and transparent. The agent keeps working; it just has summarized history instead of verbatim history.

Configure compaction behavior:

```json5
{
  agents: {
    defaults: {
      compaction: {
        mode: "safeguard",           // default | safeguard (chunked for long histories)
        reserveTokensFloor: 24000,   // minimum headroom before compaction triggers
        memoryFlush: {
          enabled: true,             // run a memory-flush turn before compacting
          softThresholdTokens: 6000,
          prompt: "Write any lasting notes to memory/YYYY-MM-DD.md; reply NO_REPLY if nothing to store."
        }
      }
    }
  }
}
```

The `memoryFlush` feature triggers a silent agent turn _before_ compaction, giving the agent a chance to write important information to its memory files before the history is summarized.

### Session commands

From any chat, you can manage sessions directly:

| Command | Effect |
|---------|--------|
| `/new` | Start a fresh session (creates a new session ID) |
| `/reset` | Clear the current session (keeps the key, empties the transcript) |
| `/sessions` | List available sessions |
| `/session <key>` | Switch to a different session |

---

## Inspecting sessions manually

Since sessions are plain files, you can inspect them directly:

```bash
# See all sessions for the main agent
ls ~/.openclaw/agents/main/sessions/

# Read the session registry
cat ~/.openclaw/agents/main/sessions/sessions.json | jq .

# Read a transcript (last 20 lines)
tail -20 ~/.openclaw/agents/main/sessions/<SessionId>.jsonl | jq .

# Count messages in a transcript
wc -l ~/.openclaw/agents/main/sessions/<SessionId>.jsonl

# Find all assistant messages
cat ~/.openclaw/agents/main/sessions/<SessionId>.jsonl | jq 'select(.role == "assistant") | .content'
```

---

## Session security and isolation

By default, sessions only include messages from approved senders. The Gateway's allowlist/pairing system ensures that only trusted senders can contribute to a session.

For group chats:
- Messages from non-approved members are filtered out before reaching the session
- The agent only sees messages from approved participants

For multi-agent setups, session isolation is enforced at the key level — there's no way for one agent's session to accidentally read another's transcript.

---

## Summary

| Concept | Detail |
|---------|--------|
| Session key | `agent:<agentId>:<mainKey>` — structured, deterministic |
| dmScope | Controls how DM keys are composed (default: `main` = all DMs share one session) |
| Storage | `~/.openclaw/agents/<id>/sessions/` — plain files, no database |
| Registry | `sessions.json` — key → sessionId + metadata |
| Transcript | `<SessionId>.jsonl` — one event per line |
| Compaction | Automatic when context window fills; optional memory-flush before compaction |

---

> **Exercise:** Explore your own session transcripts.
> 1. Run `ls ~/.openclaw/agents/main/sessions/` to see your session files
> 2. Run `cat ~/.openclaw/agents/main/sessions/sessions.json | python3 -m json.tool` to see the session registry
> 3. Pick a `.jsonl` file and open it — read a few lines and identify the `role` of each entry
> 4. Count how many turns are in your main session: `wc -l ~/.openclaw/agents/main/sessions/<id>.jsonl`
>
> **Bonus:** Use `jq` to extract just the assistant messages: `cat <file>.jsonl | jq -r 'select(.role=="assistant") | .content | if type == "string" then . else .[0].text // "tool_use" end'`

---

The next lesson covers the configuration system — what's in `openclaw.json`, how sections are organized, and how to validate your config with `openclaw doctor`.
