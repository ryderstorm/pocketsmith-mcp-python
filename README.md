## PocketSmith MCP

Developer-friendly MCP server for the PocketSmith API. Curated tools are layered on top of the OpenAPI-generated tools to provide LLM-friendly operations (accounts, transactions, summaries, etc.).

This repo is optimized for fast feedback using Astral tooling:
- Ruff for linting and formatting
- Ty for type checking (pre-release)
- pre-commit for Git hooks
- python-dotenv for environment management

---

## Prerequisites
- Python 3.11+
- uv (https://docs.astral.sh/uv/)

## Setup
1) Install dependencies (uv will create/manage the venv):

```bash
uv sync
```

2) Copy the example env and set your auth (choose ONE auth form):

```bash
cp .env.example .env
$EDITOR .env
```

Environment variables supported:
- POCKETSMITH_ACCESS_TOKEN (OAuth2 bearer token)
- POCKETSMITH_DEVELOPER_KEY (developer key)

The server will load_dotenv() on import, so a local .env is honored.

## Common tasks (Justfile)
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

## Project layout
- main.py — MCP server initialization, shared HTTP client, and curated tools
- reference/openapi.json — PocketSmith OpenAPI spec
- Justfile — common tasks
- .pre-commit-config.yaml — hooks for Ruff/Ty
- pyproject.toml — project + tooling configuration
- .env.example — example environment variables

## Troubleshooting
- Ensure .env is present or environment vars are exported in your shell.
- Confirm Python 3.11+ with `python --version`.
- If Ty errors on callability, avoid calling decorated tools internally; use internal helper functions (already done for transactions).
