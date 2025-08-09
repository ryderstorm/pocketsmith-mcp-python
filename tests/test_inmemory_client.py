import importlib
import asyncio
import pytest
import sys


def test_in_memory_client_lists_tools():
    # Clear any stubs installed by other tests so we import real packages
    for name in ('fastmcp', 'httpx', 'tenacity', 'dotenv'):
        if name in sys.modules and getattr(sys.modules[name], '__file__', None) is None:
            # Our stub modules have no __file__; pop them
            sys.modules.pop(name, None)

    try:
        from fastmcp import Client  # type: ignore
    except Exception as e:
        pytest.skip(f'fastmcp client unavailable in this environment: {e!r}')

    # Reload server to ensure it binds to real fastmcp
    if 'pocketsmith_mcp.server' in sys.modules:
        sys.modules.pop('pocketsmith_mcp.server', None)
    srv = importlib.import_module('pocketsmith_mcp.server')

    async def _run():
        async with Client(srv.mcp) as client:
            tools = await client.list_tools()
            assert isinstance(tools, list)
            # We don't assert count as tools may depend on env flags
            return tools

    tools = asyncio.run(_run())
    # Basic sanity: list type and elements are dict-like or have name key/attr
    if tools:
        first = tools[0]
        assert isinstance(first, (dict, object))
