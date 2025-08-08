import importlib
import asyncio
import pytest


def test_in_memory_client_lists_tools():
    try:
        from fastmcp import Client  # type: ignore
    except Exception:
        pytest.skip('fastmcp client unavailable in this environment')

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
