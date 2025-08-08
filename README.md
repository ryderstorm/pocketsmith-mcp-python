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
- POCKETSMITH_WRITE_MODE (optional: 1/true/yes/on to indicate write mode; default off)
- POCKETSMITH_INCLUDE_AUTOTOOLS (optional: 1/true/yes/on to include all auto-generated OpenAPI tools; default off)

The server will load_dotenv() on import, so a local .env is honored.

Defaults and modes:

- By default, the server starts in read-only mode and exposes only curated read tools. This keeps the surface area small and safe for LLMs.
- To include the full set of OpenAPI-generated tools (which may include write-capable endpoints), set `POCKETSMITH_INCLUDE_AUTOTOOLS=1`.
- `POCKETSMITH_WRITE_MODE=1` only toggles the runtime indicator/logging and does not automatically expose write tools; tool exposure is controlled by `POCKETSMITH_INCLUDE_AUTOTOOLS`.

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

## Tool Catalog (Curated)

Only curated, read-only tools are exposed by default. Enable auto-generated
OpenAPI tools with `POCKETSMITH_INCLUDE_AUTOTOOLS=1`.

- users
  - me(user_id: int)
    - Get a user by id.

- accounts
  - get_accounts(user_id: int)
  - get_account_overview(account_id: int)
  - get_account_raw(account_id: int)

- transactions
  - list_transactions(user_id: int, start_date?: str, end_date?: str, category_id?: int, payee_id?: int, updated_since?: str, page?: int)
  - summarize_spending(user_id: int, start_date: str, end_date: str, group_by: str = "category")
  - get_transaction(transaction_id: int)

- categories
  - list_categories(user_id: int)
  - get_category(category_id: int)
  - get_category_rules(category_id: int)
  - list_category_transactions(category_id: int, start_date?: str, end_date?: str, page?: int)
  - category_spend_summary(category_id: int, start_date: str, end_date: str)

- reports
  - top_spending_categories(user_id: int, start_date: str, end_date: str, limit?: int = 10)
  - top_spending_payees(user_id: int, start_date: str, end_date: str, limit?: int = 10)
  - monthly_spend_trend(user_id: int, start_date: str, end_date: str, group_by?: "total"|"category"|"payee")

- payees
  - list_payees(user_id: int)
  - get_payee(payee_id: int)

- scenarios
  - list_account_scenarios(account_id: int)
  - get_scenario(scenario_id: int)

- utilities
  - auth_check(user_id: int) → { ok, status, rate_limit, user_id }

Examples (CLI via MCP Inspector):

```bash
npx @modelcontextprotocol/inspector --cli \
  --param user_id 12345 \
  uv run python main.py --method tools/call --name list_payees
```

```bash
npx @modelcontextprotocol/inspector --cli \
  --param user_id 12345 --param start_date 2025-01-01 --param end_date 2025-03-31 \
  uv run python main.py --method tools/call --name top_spending_categories
```

### Examples: end-to-end curated workflows

1. Identify top category, then inspect its transactions and payees

```bash
# A. Top categories in Q1 2025
npx @modelcontextprotocol/inspector --cli \
  --param user_id 12345 \
  --param start_date 2025-01-01 --param end_date 2025-03-31 \
  uv run python main.py --method tools/call --name top_spending_categories

# B. List transactions for a chosen category (replace <category_id>)
npx @modelcontextprotocol/inspector --cli \
  --param category_id <category_id> \
  --param start_date 2025-01-01 --param end_date 2025-03-31 \
  uv run python main.py --method tools/call --name list_category_transactions

# C. Fetch details for a payee from those transactions (replace <payee_id>)
npx @modelcontextprotocol/inspector --cli \
  --param payee_id <payee_id> \
  uv run python main.py --method tools/call --name get_payee
```

1. Quick auth check, then list accounts and scenarios

```bash
# A. Verify token and see rate limits
npx @modelcontextprotocol/inspector --cli \
  --param user_id 12345 \
  uv run python main.py --method tools/call --name auth_check

# B. List accounts (replace 12345)
npx @modelcontextprotocol/inspector --cli \
  --param user_id 12345 \
  uv run python main.py --method tools/call --name get_accounts

# C. Show scenarios for an account (replace <account_id>)
npx @modelcontextprotocol/inspector --cli \
  --param account_id <account_id> \
  uv run python main.py --method tools/call --name list_account_scenarios
```

## Troubleshooting
- Ensure .env is present or environment vars are exported in your shell.
- Confirm Python 3.11+ with `python --version`.
- If Ty errors on callability, avoid calling decorated tools internally; use internal helper functions (already done for transactions).
