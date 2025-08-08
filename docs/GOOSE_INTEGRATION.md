---
# Goose Integration Guide (Desktop)

This MCP server is Goose-ready. Use this guide to add it to Goose Desktop and verify basic tool invocation.

## Prerequisites
- Goose Desktop installed
- Python 3.11+
- uv installed

## Quick Start
1. Ensure env vars are set in your shell or via a .env file (either of):
   - POCKETSMITH_ACCESS_TOKEN
   - POCKETSMITH_DEVELOPER_KEY
2. Run the server locally to verify:
   - uv run python -m pocketsmith_mcp
3. In Goose Desktop:
   - Settings → Extensions → Add Custom Extension
   - Transport: stdio
   - Command: uv
   - Args:
     - run
     - --project
     - /absolute/path/to/pocketsmith-mcp-python
     - python
     - -m
     - pocketsmith_mcp
   - Save
4. Test in Goose chat:
   - Ask the assistant to list available MCP tools
   - Invoke a read-only tool (e.g., list accounts) to confirm connectivity

## Notes
- This MCP exposes curated read-only tools by default. Full OpenAPI tools may be enabled via environment flags (see README).
- For portability, create a small shell wrapper script that sets the working directory and invokes uv run as above.
- For CI or headless validation, use the in-memory client with fastmcp.Client against pocketsmith_mcp.server.mcp

## Troubleshooting
- If Goose cannot connect, open the server in Inspector to validate stdio:
  - uv run -q python -m pocketsmith_mcp --inspect
- Ensure POCKETSMITH_* auth variables are set for the Goose process environment.
- If using macOS, allow the app to run external processes in Security & Privacy if prompted.
