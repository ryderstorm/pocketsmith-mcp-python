# pocketsmith-mcp-python

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
[![PyPI](https://img.shields.io/pypi/v/pocketsmith-mcp.svg)](https://pypi.org/project/pocketsmith-mcp/)
[![Build](https://github.com/ryderstorm/pocketsmith-mcp-python/actions/workflows/ci.yml/badge.svg)](https://github.com/ryderstorm/pocketsmith-mcp-python/actions/workflows/ci.yml)
[![CodeRabbit Pull Request Reviews](https://img.shields.io/coderabbit/prs/github/ryderstorm/pocketsmith-mcp-python?utm_source=oss&utm_medium=github&utm_campaign=ryderstorm%2Fpocketsmith-mcp-python&labelColor=171717&color=FF570A&label=CodeRabbit+Reviews)](https://coderabbit.ai)

Developer-friendly MCP server for the PocketSmith API. Curated tools are layered on top of the OpenAPI-generated tools to provide LLM-friendly operations (accounts, transactions, summaries, etc.).

This repo is optimized for fast feedback using Astral tooling:

- Ruff for linting and formatting
- Ty for type checking (pre-release)
- pre-commit for Git hooks
- python-dotenv for environment management

---

## Prerequisites

- Python 3.11+
- uv (<https://docs.astral.sh/uv/>)

## Setup

1. Install dependencies (uv will create/manage the venv):

    ```bash
    uv sync
    ```

2. Copy the example env and set your auth (choose ONE auth form):

    ```bash
    cp .env.example .env
    $EDITOR .env
    ```

Environment variables supported:

- POCKETSMITH_ACCESS_TOKEN (OAuth2 bearer token)
- POCKETSMITH_DEVELOPER_KEY (developer key)
- POCKETSMITH_WRITE_MODE (optional: 1/true/yes/on to indicate write mode; default off)
- POCKETSMITH_INCLUDE_AUTOTOOLS (optional: 1/true/yes/on to include all auto-generated OpenAPI tools; default off)

The server will load_dotenv() on import, so a local .env is honored.

Defaults and modes:

- By default, the server starts in read-only mode and exposes only curated read tools. This keeps the surface area small and safe for LLMs.
- To include the full set of OpenAPI-generated tools (which may include write-capable endpoints), set `POCKETSMITH_INCLUDE_AUTOTOOLS=1`.
- `POCKETSMITH_WRITE_MODE=1` only toggles the runtime indicator/logging and does not automatically expose write tools; tool exposure is controlled by `POCKETSMITH_INCLUDE_AUTOTOOLS`.

### Common tasks (Justfile)

With just installed, run any of these recipes:

```bash
just            # show all tasks
just run        # import check (verifies server loads)
just lint       # Ruff lint (no changes)
just fix        # Ruff lint with --fix
just format     # Ruff formatter
just type       # Ty type check
just hooks-install  # install pre-commit hooks
just hooks-run      # run all hooks across repo
just inspector      # launch MCP Inspector UI with randomized ports
```

Under the hood these use uv run so they execute inside the project environment.

## Lint, format, and type-check

- Ruff configuration is in pyproject.toml under [tool.ruff].
- Ty configuration is under [tool.ty.rules].

Manual commands:

```bash
uv run ruff format .
uv run ruff check .
uv run ty check .
```

Note: Ty is pre-release and may change. Current CLI: ty check.

## Git hooks (pre-commit)

This repo uses pre-commit to run Ruff and Ty on commit/push.

Install hooks once:

```bash
uv run pre-commit install -t pre-commit -t pre-push
```

Run hooks on all files:

```bash
uv run pre-commit run --all-files
```

## Run the MCP server

The entry point runs the MCP server via main.py:

```bash
uv run python -m main
```

If no auth variables are set, the server still starts but API calls will likely be unauthorized.

## Inspect / debug with MCP Inspector

Quick start (UI) via Just:

```bash
just inspector
```

CLI example (no UI), listing tools:

```bash
npx @modelcontextprotocol/inspector --cli uv run python main.py --method tools/list
```

CLI examples (no UI), calling tools:

```bash
npx @modelcontextprotocol/inspector --cli uv run python main.py --method tools/call --tool-name toolname

npx @modelcontextprotocol/inspector --cli uv run python main.py --method tools/call --tool-name toolname --tool-arg param=value
```

<!-- Badges -->

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
[![PyPI](https://img.shields.io/pypi/v/pocketsmith-mcp.svg)](https://pypi.org/project/pocketsmith-mcp/)
[![Build](https://github.com/ryderstorm/pocketsmith_mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/ryderstorm/pocketsmith_mcp/actions)

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

## Project layout

- pocketsmith_mcp/ — installable package with server and entry point
  - __main__.py — console entry (python -m pocketsmith_mcp)
  - server.py — MCP server initialization, shared HTTP client, curated tools
  - data/openapi.json — bundled PocketSmith OpenAPI spec (packaged)
- main.py — legacy root entry kept for local dev; package entry is preferred
- reference/openapi.json — legacy location; package uses bundled data
- Justfile — common tasks
- .pre-commit-config.yaml — hooks for Ruff/Ty
- pyproject.toml — project + tooling configuration
- .env.example — example environment variables

## Tool Catalog (Curated)

Only curated, read-only tools are exposed by default. Enable auto-generated
OpenAPI tools with `POCKETSMITH_INCLUDE_AUTOTOOLS=1`.

- Note on `user_id`: For many curated tools, `user_id` is optional. When
  omitted, the server will automatically resolve it using `GET /me` and use the
  current authenticated user's id. You can still pass an explicit `user_id` for
  multi-user/admin scenarios.

- users
  - me()
    - Get the authorised user (GET /me).

- accounts
  - get_accounts(user_id?: int)
  - get_account_overview(account_id: int)
  - get_account_raw(account_id: int)

- transactions
  - list_transactions(user_id?: int, start_date?: str, end_date?: str, updated_since?: str, uncategorised?: int, type?: "debit"|"credit", needs_review?: int)
  - get_transaction(transaction_id: int)

- categories
  - list_categories(user_id?: int)
  - get_category(category_id: int)
  - get_category_rules(category_id: int)
  - list_category_transactions(category_id: int, start_date?: str, end_date?: str, page?: int)
  - category_spend_summary(category_id: int, start_date: str, end_date: str)

- reports
  - top_spending_categories(user_id?: int, start_date: str, end_date: str, limit?: int = 10)
  - top_spending_payees(user_id?: int, start_date: str, end_date: str, limit?: int = 10)
  - monthly_spend_trend(user_id?: int, start_date: str, end_date: str, group_by?: "total"|"category"|"payee")

- utilities
  - auth_check() → { ok, status, rate_limit, user_id }

Examples (CLI via MCP Inspector):

```bash
npx @modelcontextprotocol/inspector --cli \
  uv run python main.py --method tools/call --tool-name get_accounts
```

```bash
npx @modelcontextprotocol/inspector --cli \
  --param start_date 2025-01-01 --param end_date 2025-03-31 \
  uv run python main.py --method tools/call --tool-name top_spending_categories
```

```bash
npx @modelcontextprotocol/inspector --cli \
  --param start_date 2025-01-01 --param end_date 2025-03-31 \
  uv run python main.py --method tools/call --tool-name top_spending_payees
```

```bash
npx @modelcontextprotocol/inspector --cli \
  --param start_date 2025-01-01 --param end_date 2025-03-31 --param group_by total \
  uv run python main.py --method tools/call --tool-name monthly_spend_trend
```

### Examples: end-to-end curated workflows

1. Identify top category, then inspect its transactions

```bash
# A. Top categories in Q1 2025
npx @modelcontextprotocol/inspector --cli \
  --param start_date 2025-01-01 --param end_date 2025-03-31 \
  uv run python main.py --method tools/call --tool-name top_spending_categories

# B. List transactions for a chosen category (replace <category_id>)
npx @modelcontextprotocol/inspector --cli \
  --param category_id <category_id> \
  --param start_date 2025-01-01 --param end_date 2025-03-31 \
  uv run python main.py --method tools/call --tool-name list_category_transactions

# C. Optionally, refine by date range or review flag
npx @modelcontextprotocol/inspector --cli \
  --param start_date 2025-01-01 --param end_date 2025-03-31 --param needs_review 1 \
  uv run python main.py --method tools/call --tool-name list_category_transactions
```

1. Quick auth check, then list accounts and categories

```bash
# A. Verify token and see rate limits
npx @modelcontextprotocol/inspector --cli \
  uv run python main.py --method tools/call --tool-name auth_check

# B. List accounts (auto-resolves user)
npx @modelcontextprotocol/inspector --cli \
  uv run python main.py --method tools/call --tool-name get_accounts

# C. List categories (auto-resolves user)
npx @modelcontextprotocol/inspector --cli \
  uv run python main.py --method tools/call --tool-name list_categories
```

## Troubleshooting

- Ensure .env is present or environment vars are exported in your shell.
- Confirm Python 3.11+ with `python --version`.
- If Ty errors on callability, avoid calling decorated tools internally; use internal helper functions (already done for transactions).

## Design Notes for Contributors

- user_id auto-resolution
  - Many curated tools accept an optional `user_id`. When omitted, `_resolve_user_id` calls `GET /me` and returns the integer `id`.
  - If `/me` does not return a valid integer id, `_resolve_user_id` raises `RuntimeError`.
  - This improves UX for single-user/chat contexts, while still allowing explicit `user_id` for admin/multi-user cases.

- Internal helpers vs decorated tools
  - Curated tools do not call other decorated tools directly. Instead, internal helpers like `_fetch_transactions` and `_fetch_category_transactions` are used to keep type-checkers (Ty) happy and avoid nested tool invocation.

- Env flags and surface area
  - `POCKETSMITH_WRITE_MODE` only toggles a runtime indicator; it does not expose write-capable tools by itself.
  - `POCKETSMITH_INCLUDE_AUTOTOOLS` controls exposure of all OpenAPI-generated tools. By default, only curated read-only tools are exposed to keep the surface small and safe.
