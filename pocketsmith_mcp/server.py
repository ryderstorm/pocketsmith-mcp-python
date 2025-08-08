import json
import os
from collections import defaultdict
from typing import Any, Dict, List, Optional
from datetime import datetime
from pathlib import Path
import sys

import httpx
from fastmcp import FastMCP
from dotenv import load_dotenv


def _parse_amount(transaction: dict) -> Optional[float]:
    """Parse amount from transaction, handling various formats safely."""
    amt = transaction.get('amount') or transaction.get('amount_cents')
    try:
        return float(amt) if isinstance(amt, (int, float, str)) else None
    except (ValueError, TypeError):
        return None


def build_headers() -> dict:
    """Construct authentication headers from environment variables.

    Supports either:
    - OAuth2 access token via POCKETSMITH_ACCESS_TOKEN -> Authorization: Bearer ...
    - Developer key via POCKETSMITH_DEVELOPER_KEY -> X-Developer-Key: ...
    """
    headers: dict[str, str] = {}

    access_token = os.getenv('POCKETSMITH_ACCESS_TOKEN')
    developer_key = os.getenv('POCKETSMITH_DEVELOPER_KEY')

    if access_token:
        headers['Authorization'] = f'Bearer {access_token}'
    elif developer_key:
        headers['X-Developer-Key'] = developer_key
    else:
        # No auth provided; many endpoints will fail without auth
        print(
            '[PocketSmith MCP] Warning: No POCKETSMITH_ACCESS_TOKEN or '
            'POCKETSMITH_DEVELOPER_KEY set; API calls may be unauthorized.'
        )

    # API recommends JSON
    headers.setdefault('Accept', 'application/json')
    headers.setdefault('Content-Type', 'application/json')
    return headers


def load_openapi_spec() -> dict:
    """Load the OpenAPI spec.

    Try packaged resource first (pocketsmith_mcp.data.openapi.json),
    then fall back to repository path reference/openapi.json.
    """
    # 1) Try packaged resource (modern importlib.resources API)
    try:
        import importlib.resources as res

        files = res.files('pocketsmith_mcp.data')
        openapi_path = files / 'openapi.json'
        with openapi_path.open('r', encoding='utf-8') as f:
            return json.load(f)
    except (ImportError, FileNotFoundError, AttributeError):
        pass

    ref_path = Path(__file__).parent.parent / 'reference' / 'openapi.json'
    with ref_path.open('r', encoding='utf-8') as f:
        return json.load(f)


def detect_base_url(openapi_spec: dict) -> str:
    try:
        servers = openapi_spec.get('servers') or []
        if servers and isinstance(servers, list):
            url = servers[0].get('url')
            if isinstance(url, str) and url:
                return url
    except Exception:
        pass
    # Fallback to documented production URL
    return 'https://api.pocketsmith.com/v2'


"""PocketSmith MCP server with curated tools.

We generate tools from the OpenAPI spec and add curated, LLM-friendly tools
that simplify common workflows.
"""

# Initialize OpenAPI-driven server and shared HTTP client at import time so we
# can register curated tools using decorators.
_spec: dict = load_openapi_spec()
_base_url: str = detect_base_url(_spec)
load_dotenv()

# Duplicate auth warning removed (already handled in build_headers())

# Read/write mode: default to READ-ONLY unless explicitly enabled
_WRITE_MODE = os.getenv('POCKETSMITH_WRITE_MODE', '').lower() in {'1', 'true', 'yes', 'on'}
print(f'PocketSmith MCP mode: {"write" if _WRITE_MODE else "read-only"}', file=sys.stderr)
_headers: dict = build_headers()
_client: httpx.AsyncClient = httpx.AsyncClient(base_url=_base_url, headers=_headers)

# Server initialization
# Control inclusion of auto-generated OpenAPI tools via env flag (default: off)
_INCLUDE_AUTOTOOLS = os.getenv('POCKETSMITH_INCLUDE_AUTOTOOLS', '').lower() in {
    '1',
    'true',
    'yes',
    'on',
}

if _INCLUDE_AUTOTOOLS:
    # Full surface (read + write according to API), useful for power users
    mcp: FastMCP = FastMCP.from_openapi(
        openapi_spec=_spec,
        client=_client,
        name='PocketSmith MCP',
    )
else:
    # Curated-only surface (read-only by design)
    mcp = FastMCP(name='PocketSmith MCP')


@mcp.tool(tags={'curated', 'users'})
async def me() -> dict:
    """Get the authorised user (GET /me)."""
    resp = await _client.get('/me')
    resp.raise_for_status()
    return resp.json()


# -----------------------
# Small whitelist of raw GET wrappers (read-only)
# -----------------------


@mcp.tool(tags={'curated', 'accounts', 'read'})
async def get_account_raw(account_id: int) -> dict:
    """Fetch the raw account payload by ID (GET /accounts/{id})."""
    resp = await _client.get(f'/accounts/{account_id}')
    resp.raise_for_status()
    return resp.json()


@mcp.tool(tags={'curated', 'transactions', 'read'})
async def get_transaction(transaction_id: int) -> dict:
    """Fetch a single transaction by ID (GET /transactions/{id})."""
    resp = await _client.get(f'/transactions/{transaction_id}')
    resp.raise_for_status()
    return resp.json()


# -----------------------
# Utilities / Auth
# -----------------------


@mcp.tool(tags={'curated', 'utilities', 'read'})
async def auth_check() -> dict:
    """Check API auth by fetching the given user id; returns status and rate-limit.

    Response shape: { ok, status, rate_limit: {limit, remaining, reset}, user_id }
    """
    resp = await _client.get('/me')
    ok = 200 <= resp.status_code < 300
    rate = {
        'limit': resp.headers.get('X-Rate-Limit-Limit'),
        'remaining': resp.headers.get('X-Rate-Limit-Remaining'),
        'reset': resp.headers.get('X-Rate-Limit-Reset'),
    }
    out = {
        'ok': ok,
        'status': resp.status_code,
        'rate_limit': rate,
        'user_id': resp.json().get('id'),
    }
    if ok:
        return out
    # If not ok, raise for status to surface error details to client
    resp.raise_for_status()
    return out


# -----------------------
# Accounts
# -----------------------


@mcp.tool(tags={'curated', 'accounts'})
async def get_accounts(user_id: Optional[int] = None) -> List[dict]:
    """List all accounts for the given user.

    If user_id is not provided, it will be resolved automatically via GET /me.
    """
    user_id = await _resolve_user_id(user_id)
    resp = await _client.get(f'/users/{user_id}/accounts')
    resp.raise_for_status()
    return resp.json()


@mcp.tool(tags={'curated', 'accounts'})
async def get_account_overview(account_id: int) -> dict:
    """Return a concise overview for an account.

    Combines key fields into a compact structure suitable for chat.
    """
    resp = await _client.get(f'/accounts/{account_id}')
    resp.raise_for_status()
    acc = resp.json()

    # Best-effort extraction of common fields
    overview = {
        'id': acc.get('id'),
        'name': acc.get('name') or acc.get('title'),
        'currency': acc.get('currency_code') or acc.get('currency'),
        'current_balance': acc.get('current_balance') or acc.get('balance'),
        'institution': (acc.get('institution') or {}).get('name')
        if isinstance(acc.get('institution'), dict)
        else None,
        'type': acc.get('type'),
        'archived': acc.get('archived'),
    }
    return overview


# -----------------------
# Transactions
# -----------------------


@mcp.tool(tags={'curated', 'transactions'})
async def list_transactions(
    user_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    updated_since: Optional[str] = None,
    uncategorised: Optional[int] = None,
    type: Optional[str] = None,
    needs_review: Optional[int] = None,
) -> List[dict]:
    """List user transactions with common filters.

    Dates should be YYYY-MM-DD. updated_since should be ISO8601.

    If user_id is not provided, it will be resolved automatically via GET /me.
    """
    user_id = await _resolve_user_id(user_id)

    return await _fetch_transactions(
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        updated_since=updated_since,
        uncategorised=uncategorised,
        tx_type=type,
        needs_review=needs_review,
    )


async def _fetch_transactions(
    user_id: int,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    updated_since: Optional[str] = None,
    uncategorised: Optional[int] = None,
    tx_type: Optional[str] = None,
    needs_review: Optional[int] = None,
) -> List[dict]:
    """Internal helper to fetch transactions without going through the tool wrapper.

    Kept separate so curated tools can call it without invoking a decorated FunctionTool.
    """
    params: Dict[str, Any] = {}
    if start_date:
        params['start_date'] = start_date
    if end_date:
        params['end_date'] = end_date
    if updated_since:
        params['updated_since'] = updated_since
    if uncategorised is not None:
        params['uncategorised'] = uncategorised
    if tx_type in ('debit', 'credit'):
        params['type'] = tx_type
    if needs_review is not None:
        params['needs_review'] = needs_review

    resp = await _client.get(f'/users/{user_id}/transactions', params=params)
    resp.raise_for_status()
    return resp.json()


async def _resolve_user_id(user_id: Optional[int]) -> int:
    """Resolve the effective user_id, calling GET /me if not provided.

    Raises RuntimeError if /me does not return an integer id.
    """
    if user_id is not None:
        return user_id
    me_resp = await _client.get('/me')
    me_resp.raise_for_status()
    me_body = me_resp.json() or {}
    resolved = me_body.get('id')
    if not isinstance(resolved, int):
        raise RuntimeError('Unable to resolve user_id from /me response')
    return resolved


# -----------------------
# Categories
# -----------------------


@mcp.tool(tags={'curated', 'categories', 'read'})
async def list_categories(user_id: Optional[int] = None) -> List[dict]:
    """List all categories for a user.

    If user_id is not provided, it will be resolved automatically via GET /me.
    """
    user_id = await _resolve_user_id(user_id)
    resp = await _client.get(f'/users/{user_id}/categories')
    resp.raise_for_status()
    return resp.json()


@mcp.tool(tags={'curated', 'categories', 'read'})
async def get_category(category_id: int) -> dict:
    """Get category details by ID."""
    resp = await _client.get(f'/categories/{category_id}')
    resp.raise_for_status()
    return resp.json()


@mcp.tool(tags={'curated', 'categories', 'read'})
async def get_category_rules(category_id: int) -> List[dict]:
    """List rules for a category (if any)."""
    resp = await _client.get(f'/categories/{category_id}/category_rules')
    # Some categories may have no rules; the API may return 404 in that case.
    if resp.status_code == 404:
        return []
    resp.raise_for_status()
    return resp.json()


async def _fetch_category_transactions(
    category_id: int,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> List[dict]:
    """Internal helper to fetch transactions for a category without tool wrapper."""
    params: Dict[str, Any] = {}
    if start_date:
        params['start_date'] = start_date
    if end_date:
        params['end_date'] = end_date
    resp = await _client.get(f'/categories/{category_id}/transactions', params=params)
    resp.raise_for_status()
    return resp.json()


@mcp.tool(tags={'curated', 'categories', 'transactions', 'read'})
async def list_category_transactions(
    category_id: int,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> List[dict]:
    """List transactions for a category with optional date range (YYYY-MM-DD)."""
    return await _fetch_category_transactions(category_id, start_date, end_date)


@mcp.tool(tags={'curated', 'reports', 'categories', 'read'})
async def category_spend_summary(
    category_id: int,
    start_date: str,
    end_date: str,
) -> dict:
    """Summarize spending for a single category over a period.

    Returns {category_id, total, count}.
    """
    txns = await _fetch_category_transactions(
        category_id=category_id, start_date=start_date, end_date=end_date
    )
    total = 0.0
    count = 0
    for t in txns:
        amount = _parse_amount(t)
        if amount is None:
            continue
        total += amount
        count += 1
    return {'category_id': category_id, 'total': total, 'count': count}


# -----------------------
# Curated Reports tools
# -----------------------


@mcp.tool(tags={'curated', 'reports', 'read'})
async def top_spending_categories(
    start_date: str,
    end_date: str,
    user_id: Optional[int] = None,
    limit: int = 10,
) -> List[dict]:
    """Top categories by absolute spend over a period.

    Returns list of {category, total, count} sorted by |total| desc.
    """
    user_id = await _resolve_user_id(user_id)
    txns = await _fetch_transactions(user_id, start_date=start_date, end_date=end_date)
    groups: Dict[str, Dict[str, Any]] = defaultdict(lambda: {'total': 0.0, 'count': 0})
    for t in txns:
        amt = t.get('amount') or t.get('amount_cents')
        try:
            amount = float(amt) if isinstance(amt, (int, float, str)) else None
        except ValueError:
            amount = None
        if amount is None:
            continue

        cat = t.get('category') or {}
        key = (cat or {}).get('title') if isinstance(cat, dict) else None
        key = key or t.get('category_name') or '(uncategorised)'

        g = groups[str(key)]
        g['total'] += amount
        g['count'] += 1

    result = [{'category': k, 'total': v['total'], 'count': v['count']} for k, v in groups.items()]
    result.sort(key=lambda x: abs(x['total']), reverse=True)
    return result[: max(0, limit)]


@mcp.tool(tags={'curated', 'reports', 'read'})
async def top_spending_payees(
    start_date: str,
    end_date: str,
    user_id: Optional[int] = None,
    limit: int = 10,
) -> List[dict]:
    """Top payees by absolute spend over a period.

    Returns list of {payee, total, count} sorted by |total| desc.
    """
    user_id = await _resolve_user_id(user_id)
    txns = await _fetch_transactions(user_id, start_date=start_date, end_date=end_date)
    groups: Dict[str, Dict[str, Any]] = defaultdict(lambda: {'total': 0.0, 'count': 0})
    for t in txns:
        amt = t.get('amount') or t.get('amount_cents')
        try:
            amount = float(amt) if isinstance(amt, (int, float, str)) else None
        except ValueError:
            amount = None
        if amount is None:
            continue

        key = t.get('payee') or t.get('payee_name') or t.get('merchant') or '(unknown)'
        g = groups[str(key)]
        g['total'] += amount
        g['count'] += 1

    result = [{'payee': k, 'total': v['total'], 'count': v['count']} for k, v in groups.items()]
    result.sort(key=lambda x: abs(x['total']), reverse=True)
    return result[: max(0, limit)]


@mcp.tool(tags={'curated', 'reports', 'read'})
async def monthly_spend_trend(
    start_date: str,
    end_date: str,
    group_by: str = 'total',
    user_id: Optional[int] = None,
) -> List[dict]:
    """Monthly spend trend between start_date and end_date.

    group_by: 'total' | 'category' | 'payee'
    - total: sum per YYYY-MM
    - category: sum per YYYY-MM per category
    - payee: sum per YYYY-MM per payee
    """
    user_id = await _resolve_user_id(user_id)
    txns = await _fetch_transactions(user_id, start_date=start_date, end_date=end_date)

    def month_key(s: Optional[str]) -> Optional[str]:
        if not s:
            return None
        try:
            return datetime.fromisoformat(s[:10]).strftime('%Y-%m')
        except Exception:
            return None

    if group_by == 'category':
        groups: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        for t in txns:
            m = month_key(t.get('date') or t.get('transaction_date') or t.get('created_at'))
            if not m:
                continue
            amount = _parse_amount(t)
            if amount is None:
                continue
            cat = t.get('category') or {}
            key = (cat or {}).get('title') if isinstance(cat, dict) else None
            key = key or t.get('category_name') or '(uncategorised)'
            groups[m][str(key)] += amount
        # flatten
        out: List[dict] = []
        for m, cats in groups.items():
            for k, total in cats.items():
                out.append({'month': m, 'category': k, 'total': total})
        out.sort(key=lambda x: (x['month'], -abs(x['total'])))
        return out

    if group_by == 'payee':
        groups2: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        for t in txns:
            m = month_key(t.get('date') or t.get('transaction_date') or t.get('created_at'))
            if not m:
                continue
            amount = _parse_amount(t)
            if amount is None:
                continue
            key = t.get('payee') or t.get('payee_name') or t.get('merchant') or '(unknown)'
            groups2[m][str(key)] += amount
        out2: List[dict] = []
        for m, payees in groups2.items():
            for k, total in payees.items():
                out2.append({'month': m, 'payee': k, 'total': total})
        out2.sort(key=lambda x: (x['month'], -abs(x['total'])))
        return out2

    # total per month
    totals: Dict[str, float] = defaultdict(float)
    for t in txns:
        m = month_key(t.get('date') or t.get('transaction_date') or t.get('created_at'))
        if not m:
            continue
        amt = t.get('amount') or t.get('amount_cents')
        try:
            amount = float(amt)
        except Exception:
            continue
        totals[m] += amount
    result = [{'month': m, 'total': total} for m, total in totals.items()]
    result.sort(key=lambda x: x['month'])
    return result


# -----------------------
# Scenarios
# -----------------------
# Note: The current OpenAPI spec only documents /scenarios/{id}/events.
# There are no documented endpoints for /accounts/{id}/scenarios or
# /scenarios/{id}. Curated scenario tools have been removed to avoid
# exposing non-existent endpoints.


# -----------------------
# Payees
# -----------------------
# Note: The OpenAPI spec does not include /payees or /users/{id}/payees paths.
# Curated payee tools have been removed to avoid exposing non-existent endpoints.


def main() -> None:
    # Run the MCP server
    mcp.run()


if __name__ == '__main__':
    main()
