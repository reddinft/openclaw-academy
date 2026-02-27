# End-to-end message flow

Let's trace a single message — "What's the weather like in Sydney?" — from the moment you type it to the moment you get a response. Concrete examples beat abstract explanations.

---

## The setup

- You're messaging via Telegram
- Your agent is running on a Mac Mini
- The LLM is Claude Sonnet 4.6 (Anthropic)
- A weather skill is loaded that adds a `get_weather` tool

---

## Full flow diagram

```mermaid
sequenceDiagram
    participant You as 📱 You (Telegram)
    participant TG as Telegram Servers
    participant GM as grammY (Gateway)
    participant GW as Gateway Core
    participant SS as Session Store
    participant AG as Agent Runtime
    participant AN as Anthropic API
    participant WT as Weather Tool

    You->>TG: "What's the weather like in Sydney?"
    TG->>GM: Webhook / Long Poll update
    GM->>GW: InboundMessage {text, sender, chat}
    GW->>GW: Check sender allowlist/pairing
    GW->>SS: Find/create session for this DM
    SS-->>GW: Session {transcript, tokenCount}
    GW->>AG: Start agent turn {message, session}
    
    Note over AG: Inject workspace files<br/>(AGENTS.md, SOUL.md, etc.)
    
    AG->>AN: POST /messages {system, messages, tools:[get_weather]}
    AN-->>AG: {tool_call: {name:"get_weather", input:{location:"Sydney"}}}
    AG->>WT: Execute get_weather({location:"Sydney"})
    WT-->>AG: {temp:22, condition:"Partly cloudy", humidity:65}
    AG->>AN: POST /messages (with tool result)
    AN-->>AG: "It's 22°C and partly cloudy in Sydney right now..."
    
    AG->>SS: Append turn to JSONL transcript
    AG->>GW: Response text ready
    GW->>GM: Send reply
    GM->>TG: sendMessage API call
    TG->>You: "It's 22°C and partly cloudy in Sydney..."
```

---

## Step 1: You send a message

You type in Telegram and hit send. Telegram's servers receive the message and deliver it to your bot.

---

## Step 2: Delivery to Gateway

Telegram delivers the message via one of two mechanisms.

With long polling (the default in most setups):
```
Gateway → Telegram: "any updates since offset X?"
Telegram → Gateway: [update: message from user 821071206]
```

With a webhook (faster, requires HTTPS endpoint):
```
Telegram → Gateway: POST /webhook {update: message...}
```

grammY handles this transparently. Either way, the Gateway receives a structured `Update` object.

---

## Step 3: Channel Manager processes it

The Telegram channel plugin:

1. Validates the update (is it a message? from whom?)
2. Checks the allowlist: Is `821071206` in `channels.telegram.allowFrom`?
   - If not: sends a pairing code and drops the message
3. Wraps it in OpenClaw's `InboundMessage` format:

```javascript
{
  text: "What's the weather like in Sydney?",
  sender: "telegram:821071206",
  chat: "telegram:dm:821071206",
  channel: "telegram",
  timestamp: 1709042400000,
  media: null
}
```

4. Marks the inbound content as untrusted. The LLM prompt will have this message wrapped in safety markers to prevent prompt injection.

---

## Step 4: Session lookup

The Gateway determines the session key based on `dmScope`. With the default `main` scope:

```
session key: "agent:main:main"
```

The Session Store looks up `~/.openclaw/agents/main/sessions/sessions.json`:
- Found: loads the existing session ID
- Not found: creates a new session

It then loads (or starts) the JSONL transcript file for this session — every previous message and tool call in this conversation.

---

## Step 5: Agent turn begins

The Agent Runtime starts a new turn with:

```javascript
{
  session: { id: "ses_xyz", tokenCount: 12543 },
  message: { role: "user", content: "What's the weather like in Sydney?" },
  tools: [...all registered tools...],
}
```

On the first turn of a new session, the workspace files (AGENTS.md, SOUL.md, TOOLS.md, USER.md, IDENTITY.md) are prepended to the system prompt. This is called bootstrap injection.

The system prompt looks something like:

```
<system>
[AGENTS.md content]
[SOUL.md content]
[TOOLS.md content]
[USER.md content]

## Available Skills
<available_skills>
  <skill name="weather">Get weather forecasts...</skill>
  ...
</available_skills>

## Current Date & Time
Time zone: Australia/Sydney
...
</system>
```

---

## Step 6: First LLM call

The agent calls Anthropic's Messages API:

```http
POST https://api.anthropic.com/v1/messages
Authorization: Bearer sk-ant-...
Content-Type: application/json

{
  "model": "claude-sonnet-4-6",
  "max_tokens": 8096,
  "system": "...",
  "messages": [
    {"role": "user", "content": "What's the weather like in Sydney?"}
  ],
  "tools": [
    {
      "name": "get_weather",
      "description": "Get current weather for a location",
      "input_schema": {"type": "object", "properties": {"location": {"type": "string"}}}
    }
  ]
}
```

Anthropic returns a tool call:

```json
{
  "stop_reason": "tool_use",
  "content": [
    {
      "type": "tool_use",
      "id": "toolu_01Abc...",
      "name": "get_weather",
      "input": {"location": "Sydney"}
    }
  ]
}
```

---

## Step 7: Tool execution

The Tool Engine receives the `get_weather` call. Based on tool policy:

- Sandboxed tools (exec): run in a restricted environment
- Skill tools: run their registered handler function

The weather skill calls its API and returns:

```json
{
  "location": "Sydney, NSW, AU",
  "temperature": 22,
  "feels_like": 20,
  "condition": "Partly cloudy",
  "humidity": 65,
  "wind_kph": 15
}
```

---

## Step 8: Second LLM call

The tool result is appended to the conversation and sent back to Anthropic:

```json
{
  "messages": [
    {"role": "user", "content": "What's the weather like in Sydney?"},
    {"role": "assistant", "content": [{"type": "tool_use", "name": "get_weather", ...}]},
    {"role": "user", "content": [{"type": "tool_result", "content": "{\"temperature\": 22, ...}"}]}
  ]
}
```

Claude now responds with text:

> "It's currently 22°C (feels like 20°C) and partly cloudy in Sydney. Humidity is sitting at 65% with a light 15 km/h breeze. A nice day to be out! ☀️🌤"

---

## Step 9: Transcript append

The completed turn is appended to the JSONL transcript:

```jsonl
{"role":"user","content":"What's the weather like in Sydney?","timestamp":"2026-02-27T..."}
{"role":"assistant","content":[{"type":"tool_use","name":"get_weather",...}],"timestamp":"..."}
{"role":"tool","content":[{"type":"tool_result","content":"{...}"}],"timestamp":"..."}
{"role":"assistant","content":"It's currently 22°C...","timestamp":"..."}
```

Token counts are updated in `sessions.json`.

---

## Step 10: Response delivery

The response goes back through the Channel Manager → grammY → Telegram API → your phone.

If block streaming is enabled, chunks appear as the model generates them. Otherwise (the default), the full response sends at once.

---

## What makes this fast?

There's no database query per turn — the transcript loads once per session and stays in memory. All components live in one Node process, so there are no service hops. Tool calls run on your machine, not a remote container. Responses can stream progressively if you have block streaming enabled.

---

## What could go wrong?

| Scenario | What happens |
|----------|-------------|
| Sender not on allowlist | Pairing code sent, message dropped |
| LLM API rate limited | Exponential backoff retry (configurable) |
| Tool execution fails | Error returned as tool result; agent decides next step |
| Context window full | Auto-compaction kicks in, older history summarized |
| Network disconnect | Channel reconnects with exponential backoff |
| Gateway crash | Daemon supervisor (launchd/systemd) restarts it |

---

## Summary

The full round-trip for a single message:

1. 📱 User → Telegram → Gateway (grammY long poll/webhook)
2. 🔒 Allowlist/pairing check
3. 📂 Session lookup (JSONL transcript)
4. 🤖 Agent turn: inject workspace context
5. ☁️ LLM API call (Anthropic/OpenAI/etc.)
6. 🔧 Tool calls (0 or more times)
7. 📝 Transcript append
8. 📱 Response → Telegram → User

Typical latency: **1–5 seconds** (dominated by LLM API time).

---

> **Exercise:** Look at your own session transcript. Open `~/.openclaw/agents/main/sessions/` and find the latest `.jsonl` file. Read through a few turns and notice how tool calls and tool results are structured.

---

The next module goes deep on the Gateway: the WebSocket control plane, session management, and how channels plug in.
