import importlib
import json
from importlib import resources


def test_import_package():
    mod = importlib.import_module('pocketsmith_mcp')
    assert mod is not None


def test_openapi_resource_present_and_parsable():
    # Validate that the packaged OpenAPI data file exists and is valid JSON
    data_path = resources.files('pocketsmith_mcp') / 'data' / 'openapi.json'
    assert data_path.is_file()
    content = data_path.read_text(encoding='utf-8')
    spec = json.loads(content)
    assert isinstance(spec, dict)
    # minimal sanity: OpenAPI top-level fields typically include 'openapi' or 'swagger'
    assert any(k in spec for k in ('openapi', 'swagger'))


def test_cli_entrypoint_exists():
    entry = importlib.import_module('pocketsmith_mcp.__main__')
    assert hasattr(entry, 'main') and callable(entry.main)
