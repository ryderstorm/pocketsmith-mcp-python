# Common development tasks for PocketSmith MCP

# Default recipe
_default:
	@just --list

# Run a quick import check to ensure the server loads
run:
	uv run python -c "import main; print('PocketSmith MCP imported OK')"

# Lint (no changes)
lint:
	uv run ruff check .

# Lint and auto-fix
fix:
	uv run ruff check . --fix

# Format code
format:
	uv run ruff format .

# Type check with ty
type:
	uv run ty check .

# Install git hooks via pre-commit
hooks-install:
	uv run pre-commit install -t pre-commit -t pre-push

# Run all hooks on all files
hooks-run:
	uv run pre-commit run --all-files
