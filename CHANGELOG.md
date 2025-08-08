# Changelog

All notable changes to this project will be documented in this file.

## [v0.2.0] - 2025-08-07

### Added
- Curated reporting tools: `top_spending_categories`, `top_spending_payees`, `monthly_spend_trend`.
- `auth_check` utility tool for quick validation and rate-limit visibility.

### Changed
- Curated tools now auto-resolve `user_id` via `GET /me` when omitted:
  - `get_accounts`, `list_categories`, `list_transactions`,
    `top_spending_categories`, `top_spending_payees`, `monthly_spend_trend`.
- DRY refactor: introduced shared async helper `_resolve_user_id` and
  updated curated tools to use it.
- README Tool Catalog and examples updated to reflect optional `user_id`
  and to add end-to-end workflows.
- Added "Design Notes for Contributors" to README documenting
  `_resolve_user_id`, internal helpers, and env flags.

### Fixed
- `get_category_rules` now returns `[]` on HTTP 404 (no rules for category).
- Removed unsupported payees and scenarios curated tools (absent in OpenAPI spec).

### DevEx
- Integrated Ruff, Ty, pre-commit, and markdownlint setups.
- Added MCP Inspector usage docs and quick-start.

[v0.2.0]: https://example.com/releases/v0.2.0
