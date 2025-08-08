# Common development tasks for PocketSmith MCP

# Default recipe
_default:
	@just --list

# Run a quick import check to ensure the server loads
run:
	uv run python -c "import pocketsmith_mcp; print('PocketSmith MCP imported OK')"

# Run the MCP server via the package entry (stdio)
serve:
	uv run python -m pocketsmith_mcp

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

# Uses the same command as in docs/mcp-inspector.md, but picks random free
# localhost ports for CLIENT_PORT and SERVER_PORT to avoid conflicts.
# Note: DANGEROUSLY_OMIT_AUTH=true is for trusted local development only.
# Launch MCP Inspector with randomized ports (local dev)
inspector:
	#!/usr/bin/env -S uv run python
	import os
	import socket
	import sys
	from contextlib import closing

	def alloc_port() -> int:
		with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
			s.bind(('127.0.0.1', 0))
			return int(s.getsockname()[1])

	def pick_distinct_ports() -> tuple[int, int]:
		a = alloc_port()
		b = alloc_port()
		while b == a:
			b = alloc_port()
		return a, b

	def main() -> int:
		client_port, server_port = pick_distinct_ports()
		print(
			f'Starting MCP Inspector:\n  CLIENT_PORT={client_port}\n  SERVER_PORT={server_port}\n',
			file=sys.stderr,
			flush=True,
		)
		env = os.environ.copy()
		env['CLIENT_PORT'] = str(client_port)
		env['SERVER_PORT'] = str(server_port)
		env['DANGEROUSLY_OMIT_AUTH'] = 'true'
		cmd = [
			'npx',
			'@modelcontextprotocol/inspector',
			'uv',
			'run',
			'python',
			'-m',
			'pocketsmith_mcp',
		]
		os.execvpe(cmd[0], cmd, env)

	if __name__ == '__main__':
		raise SystemExit(main())
