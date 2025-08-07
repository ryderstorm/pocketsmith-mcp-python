import json
import os
from pathlib import Path

import httpx
from fastmcp import FastMCP


def build_headers() -> dict:
    """Construct authentication headers from environment variables.

    Supports either:
    - OAuth2 access token via POCKETSMITH_ACCESS_TOKEN -> Authorization: Bearer ...
    - Developer key via POCKETSMITH_DEVELOPER_KEY -> X-Developer-Key: ...
    """
    headers: dict[str, str] = {}

    access_token = os.getenv("POCKETSMITH_ACCESS_TOKEN")
    developer_key = os.getenv("POCKETSMITH_DEVELOPER_KEY")

    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"
    elif developer_key:
        headers["X-Developer-Key"] = developer_key
    else:
        # No auth provided; many endpoints will fail without auth
        print(
            "[PocketSmith MCP] Warning: No POCKETSMITH_ACCESS_TOKEN or "
            "POCKETSMITH_DEVELOPER_KEY set; API calls may be unauthorized."
        )

    # API recommends JSON
    headers.setdefault("Accept", "application/json")
    headers.setdefault("Content-Type", "application/json")
    return headers


def load_openapi_spec() -> dict:
    ref_path = Path(__file__).parent / "reference" / "openapi.json"
    with ref_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def detect_base_url(openapi_spec: dict) -> str:
    try:
        servers = openapi_spec.get("servers") or []
        if servers and isinstance(servers, list):
            url = servers[0].get("url")
            if isinstance(url, str) and url:
                return url
    except Exception:
        pass
    # Fallback to documented production URL
    return "https://api.pocketsmith.com/v2"


def main() -> None:
    spec = load_openapi_spec()
    base_url = detect_base_url(spec)
    headers = build_headers()

    client = httpx.AsyncClient(base_url=base_url, headers=headers)

    mcp = FastMCP.from_openapi(
        openapi_spec=spec,
        client=client,
        name="PocketSmith MCP",
    )

    # Run the MCP server
    mcp.run()


if __name__ == "__main__":
    main()
