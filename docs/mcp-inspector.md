# Using MCP Inspector with the PocketSmith FastMCP Server

This guide shows how to inspect and debug this Python FastMCP server using the official MCP Inspector (an npx tool).

References:

- MCP Inspector repo/docs: <https://github.com/modelcontextprotocol/inspector>

## Prerequisites

- Node.js 18+ (for npx)
- Python 3.11+ (this repo)
- Your PocketSmith API credentials via env vars:
  - POCKETSMITH_ACCESS_TOKEN or
  - POCKETSMITH_DEVELOPER_KEY

Tip (macOS/dev): export your env vars in the same shell before starting the server or pass them via the Inspector with -e.

## Quick Start (Just)

Fastest way to launch Inspector and this server together:

```bash
just inspector
```

This starts the Inspector UI on randomized ports and runs the MCP server via stdio using uv. The chosen ports are printed to stderr.

## Quick Start (UI)

1. Start MCP Inspector UI (opens <http://localhost:6274>):

   ```bash
   npx @modelcontextprotocol/inspector
   ```

   The proxy prints a one-time Session token and a URL with the token prefilled. Open that URL.

2. Connect via stdio to this server:
   - In the Inspector UI, choose transport "stdio".
   - Command: `python`
   - Args: `main.py`
   - Env (set as needed):
     - `POCKETSMITH_ACCESS_TOKEN=...` or `POCKETSMITH_DEVELOPER_KEY=...`

   Alternatively, pass args in the URL (helpful for repeat runs):
   - `http://localhost:6274/?transport=stdio&serverCommand=python&serverArgs=main.py`

3. Explore your server
   - List tools, call tools, view resources, prompts, logs, and JSON-RPC traffic.

## Quick Start (CLI)

You can drive the server and call methods directly via CLI (no UI):

- Launch inspector CLI pointing at your stdio server entry:

  ```bash
  npx @modelcontextprotocol/inspector --cli python main.py
  ```

- Pass env variables to the server via Inspector (-e can be repeated):

  ```bash
  npx @modelcontextprotocol/inspector -e POCKETSMITH_ACCESS_TOKEN=$POCKETSMITH_ACCESS_TOKEN --cli python main.py
  ```

- List tools:

  ```bash
  npx @modelcontextprotocol/inspector --cli python main.py --method tools/list
  ```

- Call a tool (example: get_accounts):

  ```bash
  npx @modelcontextprotocol/inspector --cli python main.py \
    --method tools/call \
    --tool-name get_accounts \
    --tool-arg user_id=12345
  ```

Notes:

- Use `--` to separate Inspector flags from server args if needed.

  ```bash
  npx @modelcontextprotocol/inspector -e POCKETSMITH_DEVELOPER_KEY=$POCKETSMITH_DEVELOPER_KEY -- python main.py
  ```

## Running with uv (optional)

If you prefer uv (detected via uv.lock):

- UI mode:

  ```bash
  npx @modelcontextprotocol/inspector uv run python main.py
  ```

- CLI mode:

  ```bash
  npx @modelcontextprotocol/inspector --cli uv run python main.py
  ```

## Sample config (multiple servers)

You can store presets in a JSON config and select them in the UI or CLI.

`config.json` example:

```json
{
  "mcpServers": {
    "pocketsmith-mcp": {
      "command": "python",
      "args": ["main.py"],
      "env": {
        "POCKETSMITH_ACCESS_TOKEN": "${POCKETSMITH_ACCESS_TOKEN}"
      }
    }
  }
}
```

- Use with UI:

  ```bash
  npx @modelcontextprotocol/inspector --config config.json --server pocketsmith-mcp
  ```

- Use with CLI:

  ```bash
  npx @modelcontextprotocol/inspector --cli --config config.json --server pocketsmith-mcp --method tools/list
  ```

## Ports, host, and security

- Default UI port is 6274; proxy defaults to localhost-only.
- To change ports:

  ```bash
  CLIENT_PORT=8080 SERVER_PORT=9000 npx @modelcontextprotocol/inspector
  ```

- Do not disable auth in normal use. For trusted localhost-only dev only:

  ```bash
  DANGEROUSLY_OMIT_AUTH=true npx @modelcontextprotocol/inspector
  ```

- If binding to all interfaces (not recommended), ensure your network is trusted:

  ```bash
  HOST=0.0.0.0 npx @modelcontextprotocol/inspector
  ```

## Environment variables required by this server

This server reads auth headers from env:

- `POCKETSMITH_ACCESS_TOKEN` -> Authorization: Bearer ...
- `POCKETSMITH_DEVELOPER_KEY` -> X-Developer-Key: ...

Set them either in your shell or pass through Inspector with `-e` flags.

## Troubleshooting

- If the UI can’t connect, verify the session token and URL match and that your browser wasn’t already open to a stale token.
- If auth calls fail, confirm one of the PocketSmith env vars is set and valid for the target `user_id`.
- For CLI issues, start with listing tools to confirm basic connectivity:

  ```bash
  npx @modelcontextprotocol/inspector --cli python main.py --method tools/list
  ```

- Increase timeouts if calling long-running tools:

  ```text
  http://localhost:6274/?MCP_SERVER_REQUEST_TIMEOUT=20000
  ```

## Why stdio here?

This server uses FastMCP with `mcp.run()` which defaults to stdio transport. The Inspector can launch your Python entrypoint (main.py) and speak MCP over stdio without additional wiring.

---

```bash
just inspector
```
