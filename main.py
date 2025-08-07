import json
import os
from collections import defaultdict
from typing import Any, Dict, List, Optional
from pathlib import Path

import httpx
from fastmcp import FastMCP
from dotenv import load_dotenv


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
    ref_path = Path(__file__).parent / 'reference' / 'openapi.json'
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
_headers: dict = build_headers()
_client: httpx.AsyncClient = httpx.AsyncClient(base_url=_base_url, headers=_headers)

# Expose the combined server
mcp: FastMCP = FastMCP.from_openapi(
    openapi_spec=_spec,
    client=_client,
    name='PocketSmith MCP',
)


@mcp.tool(tags={'curated', 'users'})
async def me(user_id: int) -> dict:
    """Get the current user by ID.

    Note: PocketSmith API does not expose a /me endpoint; you must provide
    your own user_id. The token/key must authorize access to that user.
    """
    resp = await _client.get(f'/users/{user_id}')
    resp.raise_for_status()
    return resp.json()


@mcp.tool(tags={'curated', 'accounts'})
async def get_accounts(user_id: int) -> List[dict]:
    """List all accounts for the given user."""
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


@mcp.tool(tags={'curated', 'transactions'})
async def list_transactions(
    user_id: int,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    updated_since: Optional[str] = None,
    uncategorised: Optional[int] = None,
    type: Optional[str] = None,
    needs_review: Optional[int] = None,
) -> List[dict]:
    """List user transactions with common filters.

    Dates should be YYYY-MM-DD. updated_since should be ISO8601.
    """
    return await _fetch_transactions(
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        updated_since=updated_since,
        uncategorised=uncategorised,
        tx_type=type,
        needs_review=needs_review,
    )


@mcp.tool(tags={'curated', 'reports', 'transactions'})
async def summarize_spending(
    user_id: int,
    start_date: str,
    end_date: str,
    group_by: str = 'category',
) -> List[dict]:
    """Summarize spending over a period.

    group_by: "category" or "payee".
    Returns list of {group, total, count} sorted by absolute total desc.
    """
    txns = await _fetch_transactions(user_id=user_id, start_date=start_date, end_date=end_date)

    groups: dict[str, dict[str, Any]] = defaultdict(lambda: {'total': 0.0, 'count': 0})
    for t in txns:
        amt = t.get('amount') or t.get('amount_cents')
        # Normalize amount
        if isinstance(amt, (int, float)):
            amount = float(amt)
        elif isinstance(amt, str):
            try:
                amount = float(amt)
            except ValueError:
                continue
        else:
            continue

        if group_by == 'payee':
            key = t.get('payee') or t.get('payee_name') or t.get('merchant') or '(unknown)'
        else:
            cat = t.get('category') or {}
            key = (cat or {}).get('title') if isinstance(cat, dict) else None
            key = key or t.get('category_name') or '(uncategorised)'

        g = groups[str(key)]
        g['total'] += amount
        g['count'] += 1

    result = [{'group': k, 'total': v['total'], 'count': v['count']} for k, v in groups.items()]
    result.sort(key=lambda x: abs(x['total']), reverse=True)
    return result


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


def main() -> None:
    # Run the MCP server
    mcp.run()


if __name__ == '__main__':
    main()
