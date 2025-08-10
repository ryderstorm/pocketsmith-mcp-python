import time
import importlib


def test_parse_retry_after_seconds():
    srv = importlib.import_module('pocketsmith_mcp.server')
    assert srv._parse_retry_after('2') in (2.0, 2)


def test_parse_retry_after_http_date_future():
    srv = importlib.import_module('pocketsmith_mcp.server')
    # RFC 7231 IMF-fixdate, 1 minute in the future
    future = time.gmtime(time.time() + 60)
    http_date = time.strftime('%a, %d %b %Y %H:%M:%S GMT', future)
    val = srv._parse_retry_after(http_date)
    assert val is not None and val >= 0


def test_parse_retry_after_invalid():
    srv = importlib.import_module('pocketsmith_mcp.server')
    assert srv._parse_retry_after('not-a-date') is None
    assert srv._parse_retry_after(None) is None


essential_txn_cases = [
    ({'amount': 1}, 1.0),
    ({'amount': '2.5'}, 2.5),
    ({'amount_cents': 3}, 3.0),
    ({'amount': 0}, 0.0),          # numeric zero shouldn’t be treated as falsy
    ({'amount_cents': 0}, 0.0),    # zero cents should also parse to 0.0
    ({'amount': None}, None),
    ({}, None),
]


def test_parse_amount_various():
    srv = importlib.import_module('pocketsmith_mcp.server')
    for txn, expected in essential_txn_cases:
        assert srv._parse_amount(txn) == expected


def test_detect_base_url_prefers_spec_server():
    srv = importlib.import_module('pocketsmith_mcp.server')
    spec = {'servers': [{'url': 'https://example.invalid/v1'}]}
    assert srv.detect_base_url(spec) == 'https://example.invalid/v1'
