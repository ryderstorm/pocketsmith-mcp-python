import importlib


def test_import_package():
    mod = importlib.import_module('pocketsmith_mcp')
    assert mod is not None


def test_server_exports():
    server = importlib.import_module('pocketsmith_mcp.server')
    # basic sanity checks without starting anything
    assert hasattr(server, 'mcp')
    assert isinstance(server._spec, dict)
    assert isinstance(server._base_url, str)
