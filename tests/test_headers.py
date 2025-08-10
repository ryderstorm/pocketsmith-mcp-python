import importlib
import sys
import types


class _FastMCPStub:
    def __init__(self, name: str | None = None, *args, **kwargs):
        self._name = name or 'stub'

    @classmethod
    def from_openapi(cls, *args, **kwargs):
        return cls('stub-from-openapi')

    def tool(self, *args, **kwargs):
        def deco(f):
            return f

        return deco

    def run(self):
        return None


class _AsyncClientStub:
    def __init__(self, *args, **kwargs):
        # minimal attribute to be wrapped by _install_retries
        self.request = lambda *a, **k: None


def test_build_headers_access_token(monkeypatch):
    monkeypatch.delenv('POCKETSMITH_DEVELOPER_KEY', raising=False)
    monkeypatch.setenv('POCKETSMITH_ACCESS_TOKEN', 'abc123')
    # Provide minimal stubs to satisfy server import without real deps
    httpx_stub = types.ModuleType('httpx')
    httpx_stub.AsyncClient = _AsyncClientStub  # type: ignore[attr-defined]
    sys.modules['httpx'] = httpx_stub

    fastmcp_stub = types.ModuleType('fastmcp')
    fastmcp_stub.FastMCP = _FastMCPStub  # type: ignore[attr-defined]
    sys.modules['fastmcp'] = fastmcp_stub

    tenacity_stub = types.ModuleType('tenacity')
    tenacity_stub.AsyncRetrying = object  # type: ignore[attr-defined]
    tenacity_stub.retry_if_exception_type = lambda *a, **k: None  # type: ignore[attr-defined]
    tenacity_stub.stop_after_attempt = lambda *a, **k: None  # type: ignore[attr-defined]
    tenacity_stub.wait_exponential_jitter = lambda *a, **k: None  # type: ignore[attr-defined]
    sys.modules['tenacity'] = tenacity_stub

    dotenv_stub = types.ModuleType('dotenv')
    dotenv_stub.load_dotenv = lambda *a, **k: None  # type: ignore[attr-defined]
    sys.modules['dotenv'] = dotenv_stub
    # Reload to ensure env read fresh
    mod = importlib.import_module('pocketsmith_mcp.server')
    importlib.reload(mod)
    headers = mod.build_headers()
    assert headers['Authorization'].startswith('Bearer ')
    assert headers['Accept'] == 'application/json'
    assert headers['Content-Type'] == 'application/json'
    assert 'X-Developer-Key' not in headers

def test_build_headers_developer_key(monkeypatch):
    monkeypatch.delenv('POCKETSMITH_ACCESS_TOKEN', raising=False)
    monkeypatch.setenv('POCKETSMITH_DEVELOPER_KEY', 'devkey')
    httpx_stub = types.ModuleType('httpx')
    httpx_stub.AsyncClient = _AsyncClientStub  # type: ignore[attr-defined]
    sys.modules['httpx'] = httpx_stub

    fastmcp_stub = types.ModuleType('fastmcp')
    fastmcp_stub.FastMCP = _FastMCPStub  # type: ignore[attr-defined]
    sys.modules['fastmcp'] = fastmcp_stub

    tenacity_stub = types.ModuleType('tenacity')
    tenacity_stub.AsyncRetrying = object  # type: ignore[attr-defined]
    tenacity_stub.retry_if_exception_type = lambda *a, **k: None  # type: ignore[attr-defined]
    tenacity_stub.stop_after_attempt = lambda *a, **k: None  # type: ignore[attr-defined]
    tenacity_stub.wait_exponential_jitter = lambda *a, **k: None  # type: ignore[attr-defined]
    sys.modules['tenacity'] = tenacity_stub

    dotenv_stub = types.ModuleType('dotenv')
    dotenv_stub.load_dotenv = lambda *a, **k: None  # type: ignore[attr-defined]
    sys.modules['dotenv'] = dotenv_stub
    mod = importlib.import_module('pocketsmith_mcp.server')
    importlib.reload(mod)
    headers = mod.build_headers()
    assert headers['X-Developer-Key'] == 'devkey'


def test_build_headers_no_auth(monkeypatch, capsys):
    monkeypatch.delenv('POCKETSMITH_ACCESS_TOKEN', raising=False)
    monkeypatch.delenv('POCKETSMITH_DEVELOPER_KEY', raising=False)
    httpx_stub = types.ModuleType('httpx')
    httpx_stub.AsyncClient = _AsyncClientStub  # type: ignore[attr-defined]
    sys.modules['httpx'] = httpx_stub

    fastmcp_stub = types.ModuleType('fastmcp')
    fastmcp_stub.FastMCP = _FastMCPStub  # type: ignore[attr-defined]
    sys.modules['fastmcp'] = fastmcp_stub

    tenacity_stub = types.ModuleType('tenacity')
    tenacity_stub.AsyncRetrying = object  # type: ignore[attr-defined]
    tenacity_stub.retry_if_exception_type = lambda *a, **k: None  # type: ignore[attr-defined]
    tenacity_stub.stop_after_attempt = lambda *a, **k: None  # type: ignore[attr-defined]
    tenacity_stub.wait_exponential_jitter = lambda *a, **k: None  # type: ignore[attr-defined]
    sys.modules['tenacity'] = tenacity_stub

    dotenv_stub = types.ModuleType('dotenv')
    dotenv_stub.load_dotenv = lambda *a, **k: None  # type: ignore[attr-defined]
    sys.modules['dotenv'] = dotenv_stub
    mod = importlib.import_module('pocketsmith_mcp.server')
    importlib.reload(mod)
    _ = mod.build_headers()
    # Should print a warning to stdout/stderr; we don't assert output text here
    # to keep the test resilient, just ensure function returns defaults
    headers = mod.build_headers()
    assert headers['Accept'] == 'application/json'
    assert headers['Content-Type'] == 'application/json'
