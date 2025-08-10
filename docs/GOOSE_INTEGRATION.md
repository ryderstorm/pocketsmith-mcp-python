# Goose Integration

## Use with Goose (Desktop + CLI)

You can use this MCP server as a custom extension in Goose. Two recommended ways to run it from any folder:

- Use `uv --directory` to point at this repo when launching the server
- Or create a small shim script on your `$PATH` that wraps the command

### Goose Desktop (GUI)

1. Open Goose Desktop.
2. Click the gear icon → Advanced Settings → Add Custom Extension.
3. Fill the form as follows:
    - Type: `STDIO`
    - Command:
      - Option A (recommended, via uvx after install):

        ```bash
        uvx pocketsmith-mcp
        ```

      - Option B (portable shim for current repo before PyPI release): create a script, make it executable, and use its path as the command.

        ```bash
        # ~/.local/bin/pocketsmith-mcp (example location on macOS/Linux)
        #!/usr/bin/env bash
        MCP_DIR="/absolute/path/to/pocketsmith-mcp-python"
        exec uv run --directory "$MCP_DIR" python -m pocketsmith_mcp "$@"
        ```

        Then in Goose, set Command to:

        ```bash
        /absolute/path/to/pocketsmith-mcp-python/temp/pocketsmith-mcp
        ```

    - Environment Variables: add one of
      - `POCKETSMITH_ACCESS_TOKEN` = your bearer token, or
      - `POCKETSMITH_DEVELOPER_KEY` = your developer key
    - Timeout: e.g. `300` (default is fine)
    - Name/Description: e.g. “PocketSmith” — curated read-only tools

After saving, start a chat and Goose will load the extension and list the available tools. Try e.g. “Call get_accounts”.

Notes

- Using `python -m main` avoids relative path issues.
- `.env` in the project directory will be loaded automatically by `uv run` unless you disable env files. You can also supply env via Goose.
- To expose the full OpenAPI auto-tools temporarily, set `POCKETSMITH_INCLUDE_AUTOTOOLS=1` in the extension’s env config.

### Goose CLI alternatives

- One-off session with this extension:

  ```bash
  goose session --with-extension 'uvx pocketsmith-mcp'
  ```

- Web UI via CLI:

  ```bash
  goose web --open --with-extension 'uvx pocketsmith-mcp'
  ```

- If using the shim script:

  ```bash
  goose session --with-extension '/absolute/path/to/pocketsmith-mcp-python/temp/pocketsmith-mcp'
  ```
