# MCP Integration

The Model Context Protocol (MCP) is an open standard for connecting AI agents to external tool servers. Instead of baking every capability into the agent, MCP lets you wire in external services — databases, APIs, monitoring systems — as tool providers that the agent can discover and call at runtime.

OpenClaw supports MCP servers as first-class tool backends. In this lesson, you'll learn how MCP works, how to wire servers into OpenClaw, and how to use `mcporter` to manage them.

---

## What Is MCP?

MCP is a client-server protocol where:

- The **MCP server** exposes tools (functions the agent can call) and optionally resources (data the agent can read)
- The **MCP client** (OpenClaw) discovers available tools, presents them to the LLM, and routes tool calls to the server
- Communication happens over **stdio** (local processes) or **HTTP/SSE** (remote servers)

Think of it like a USB port for AI tools. Plug in any MCP server, and the agent immediately gains access to its capabilities.

```mermaid
flowchart LR
    A[User Message] --> B[OpenClaw Gateway]
    B --> C[LLM Provider]
    C -->|Tool Call| B
    B --> D[MCP Server A<br/>Database Tools]
    B --> E[MCP Server B<br/>Monitoring Tools]
    B --> F[MCP Server C<br/>Custom API]
    D -->|Result| B
    E -->|Result| B
    F -->|Result| B
    B -->|Response| A
```

> **Key Takeaway:** MCP separates "what tools exist" from "how the agent uses them." You can add capabilities by wiring in a server — no code changes to OpenClaw itself.

---

## MCP vs Skills vs Plugins

OpenClaw has three extension mechanisms. Understanding when to use each saves you time:

| Mechanism | What it is | Best for |
|-----------|-----------|----------|
| **Skill** | Markdown instructions in `SKILL.md` | Teaching the agent to use existing tools in new ways |
| **Plugin** | TypeScript module loaded in-process | Adding new Gateway features (channels, RPC, tools) |
| **MCP Server** | External process exposing tools via MCP | Connecting to external services, databases, APIs |

Rules of thumb:

- If you're teaching the agent a _workflow_ → **Skill**
- If you're adding a new _channel or gateway feature_ → **Plugin**
- If you're exposing an _external service's API_ → **MCP Server**
- If the tool server already exists as an MCP server → **MCP Server**

---

## Anatomy of an MCP Server

An MCP server is a standalone process that:

1. Receives a connection (stdio pipe or HTTP)
2. Advertises its available tools (name, description, parameters)
3. Waits for tool call requests
4. Executes the tool and returns results

Here's a minimal MCP server in Python (using the `mcp` package):

```python
from mcp.server import Server
from mcp.types import Tool, TextContent
import json

server = Server("weather-server")

@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="get_weather",
            description="Get current weather for a city",
            inputSchema={
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "City name"}
                },
                "required": ["city"],
            },
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "get_weather":
        city = arguments["city"]
        # In reality, call a weather API here
        return [TextContent(type="text", text=f"Weather in {city}: 22C, sunny")]

if __name__ == "__main__":
    import asyncio
    from mcp.server.stdio import stdio_server
    asyncio.run(stdio_server(server))
```

This server:
- Advertises one tool: `get_weather`
- Accepts a `city` parameter
- Returns weather data as text

---

## Wiring MCP Servers into OpenClaw

### Method 1: Direct Configuration

Add MCP servers to your `openclaw.json`:

```json5
{
  mcp: {
    servers: {
      "weather": {
        command: "python3",
        args: ["/path/to/weather_server.py"],
        env: {
          WEATHER_API_KEY: "your-key-here",
        },
      },
      "database": {
        command: "npx",
        args: ["-y", "@modelcontextprotocol/server-postgres"],
        env: {
          DATABASE_URL: "postgresql://user:pass@localhost/mydb",
        },
      },
    },
  },
}
```

Each server entry needs:

| Field | Description |
|-------|-------------|
| `command` | The executable to run |
| `args` | Command-line arguments |
| `env` | Environment variables passed to the server |

After adding the config, restart the gateway. OpenClaw spawns each server as a child process, connects via stdio, and discovers its tools.

### Method 2: HTTP/SSE Servers

For remote MCP servers, use the URL-based config:

```json5
{
  mcp: {
    servers: {
      "remote-tools": {
        url: "https://mcp.example.com/sse",
        headers: {
          Authorization: "Bearer your-token",
        },
      },
    },
  },
}
```

---

## mcporter: The MCP Manager CLI

`mcporter` is the CLI for managing MCP server lifecycles. It handles discovery, installation, health checking, and configuration.

### Install mcporter

```bash
npm i -g mcporter
```

### Common Commands

```bash
# List configured MCP servers
mcporter list

# Check server health
mcporter health weather

# Start a server manually (for testing)
mcporter start weather

# View server logs
mcporter logs weather

# Add a new server from a registry
mcporter add @modelcontextprotocol/server-filesystem

# Remove a server
mcporter remove weather
```

### Adding a Server with mcporter

```bash
mcporter add @modelcontextprotocol/server-postgres \
  --env DATABASE_URL="postgresql://user:pass@localhost/mydb" \
  --name "Production DB"
```

This:
1. Installs the npm package
2. Generates the config entry
3. Adds it to your `openclaw.json`

---

## Popular MCP Servers

The MCP ecosystem is growing fast. Here are servers commonly used with OpenClaw:

| Server | Package | Tools |
|--------|---------|-------|
| Filesystem | `@modelcontextprotocol/server-filesystem` | Read/write files, search directories |
| PostgreSQL | `@modelcontextprotocol/server-postgres` | Query databases, list tables |
| GitHub | `@modelcontextprotocol/server-github` | Issues, PRs, repos, code search |
| Slack | `@modelcontextprotocol/server-slack` | Read channels, send messages |
| Brave Search | `@modelcontextprotocol/server-brave-search` | Web search |
| Memory | `@modelcontextprotocol/server-memory` | Persistent key-value storage |
| Puppeteer | `@modelcontextprotocol/server-puppeteer` | Browser automation |

### Example: Wiring GitHub + PostgreSQL

```json5
{
  mcp: {
    servers: {
      "github": {
        command: "npx",
        args: ["-y", "@modelcontextprotocol/server-github"],
        env: {
          GITHUB_PERSONAL_ACCESS_TOKEN: "ghp_...",
        },
      },
      "postgres": {
        command: "npx",
        args: ["-y", "@modelcontextprotocol/server-postgres"],
        env: {
          DATABASE_URL: "postgresql://localhost/analytics",
        },
      },
    },
  },
}
```

Now the agent can search GitHub issues **and** query your analytics database in the same conversation.

---

## Building Your Own MCP Server

### Python (recommended for data/API tools)

```bash
pip install mcp
```

Skeleton:

```python
from mcp.server import Server
from mcp.types import Tool, TextContent

server = Server("my-server")

@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="my_tool",
            description="Does something useful",
            inputSchema={
                "type": "object",
                "properties": {
                    "input": {"type": "string"}
                },
                "required": ["input"],
            },
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "my_tool":
        result = process(arguments["input"])
        return [TextContent(type="text", text=result)]

if __name__ == "__main__":
    import asyncio
    from mcp.server.stdio import stdio_server
    asyncio.run(stdio_server(server))
```

### TypeScript/Node.js

```bash
npm install @modelcontextprotocol/sdk
```

```typescript
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";

const server = new Server({
  name: "my-server",
  version: "1.0.0",
});

server.setRequestHandler("tools/list", async () => ({
  tools: [
    {
      name: "my_tool",
      description: "Does something useful",
      inputSchema: {
        type: "object",
        properties: { input: { type: "string" } },
        required: ["input"],
      },
    },
  ],
}));

server.setRequestHandler("tools/call", async (request) => {
  const { name, arguments: args } = request.params;
  if (name === "my_tool") {
    return { content: [{ type: "text", text: `Processed: ${args.input}` }] };
  }
});

const transport = new StdioServerTransport();
await server.connect(transport);
```

---

## MCP + Skills: The Power Combo

The most effective pattern is combining MCP servers with skills. The MCP server provides the tool; the skill teaches the agent _when and how_ to use it.

Example: You have an MCP server exposing a `query_langfuse` tool. A skill teaches the agent the workflow:

```markdown
---
name: insight-engine
description: Generate statistical insights from Langfuse observability data
metadata: {"openclaw": {"requires": {"env": ["LANGFUSE_PUBLIC_KEY"]}}}
---

# Insight Engine

When asked for system insights or performance reports:

1. Use `query_langfuse` to fetch recent traces (last 24h by default)
2. Analyze the data using Python statistics — never let the LLM aggregate
3. Present findings with citations to specific trace IDs
4. Format as a Notion-ready report if requested

Always show your statistical methodology. Never hallucinate numbers.
```

The MCP server handles the API call. The skill handles the workflow. Clean separation.

---

## Security Considerations

MCP servers run as external processes with their own permissions:

| Concern | Mitigation |
|---------|-----------|
| Secrets in config | Use environment variables, not inline strings. Reference 1Password or vault |
| Network access | Stdio servers are local-only by default. HTTP servers need auth |
| File access | Filesystem MCP server should be scoped to specific directories |
| Untrusted servers | Review server code before installing. Prefer official packages |
| Resource limits | Use `sandbox.docker` limits for agents calling MCP tools |

> **Key Takeaway:** An MCP server has whatever permissions its process has. If you run `server-filesystem` as root, the agent can read/write any file on the system. Scope access tightly.

---

## Troubleshooting

| Symptom | Likely cause |
|---------|-------------|
| Tools not appearing | Server didn't start — check `mcporter health` or gateway logs |
| "Tool not found" errors | Server crashed after startup — check stderr logs |
| Timeout on tool calls | Server is slow or hung — check for blocking I/O |
| Auth errors | Environment variables not passed — verify `env` block in config |
| Duplicate tool names | Two servers exposing same tool name — rename in config |

Check gateway logs for MCP connection status:

```bash
tail -f ~/.openclaw/logs/gateway.log | grep -i mcp
```

---

## Summary

| Concept | Details |
|---------|---------|
| **MCP** | Open protocol for AI tool servers |
| **Transport** | stdio (local) or HTTP/SSE (remote) |
| **Config** | `mcp.servers` in openclaw.json |
| **Manager** | `mcporter` CLI for lifecycle management |
| **Best combo** | MCP server (tool) + Skill (workflow instructions) |
| **Security** | Scope permissions, use env vars, review code |

---

## Exercise

1. Install the official filesystem MCP server and configure it in `openclaw.json` to give the agent read-only access to `~/Documents`:
   ```bash
   npx -y @modelcontextprotocol/server-filesystem ~/Documents
   ```
2. Test that the agent can list and read files from that directory
3. Write a skill that teaches the agent to use the filesystem tools to find and summarize markdown files
4. **Bonus:** Write a minimal MCP server in Python that exposes a single `get_uptime` tool returning the system uptime

---

This wraps up Module 8. You now know how to extend OpenClaw through skills, multi-agent routing, and MCP integration. In **Module 9**, we'll cover deployment patterns — getting OpenClaw running reliably on macOS, Docker, and Linux VPS.
