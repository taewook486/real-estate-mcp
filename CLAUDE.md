# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MCP server exposing Korea's MOLIT (국토교통부) real estate transaction API to Claude Desktop. The server wraps XML endpoints from `apis.data.go.kr`, `api.odcloud.kr`, and `openapi.onbid.co.kr`, providing 14+ tools for querying apartment, officetel, villa, single-house, commercial trade/rent data, APT subscription info, and public auction (공매) bid results.

Requires `DATA_GO_KR_API_KEY` from [공공데이터포털](https://www.data.go.kr) in a `.env` file at the project root.

## Commands

```bash
# Run all tests (requires .env with valid key, or monkeypatched key)
uv run pytest

# Run a single test file
uv run pytest tests/mcp_server/test_apartment_trades.py

# Run a single test by name
uv run pytest tests/mcp_server/test_apartment_trades.py::TestParseAptTrades::test_normal_response_returns_items

# Lint + format (auto-fix)
uv run ruff check --fix && uv run ruff format

# Type check
uv run pyright

# Security scan
uv run bandit -c pyproject.toml -r src/

# Start MCP Inspector for interactive testing
uv run mcp dev src/real_estate/mcp_server/server.py
```

## Architecture

All MCP logic lives in a single file: [src/real_estate/mcp_server/server.py](src/real_estate/mcp_server/server.py).

**Request flow for any trade/rent tool:**
1. `_check_api_key()` — guard: fails fast if env var is missing
2. `_build_url()` — constructs URL with `serviceKey` embedded directly (not via httpx params, to avoid double URL-encoding)
3. `_fetch_xml()` — async HTTP GET via httpx with 15s timeout
4. Parser function (`_parse_*`) — parses defusedxml, filters cancelled deals (`cdealType == "O"`), returns `(items, error_code)`
5. `_build_trade_summary()` / `_build_rent_summary()` — computes median/min/max statistics
6. Returns standardised dict: `{total_count, items, summary}` or `{error, message}`

**Shared helpers for both trade and rent flows:**
- `_run_trade_tool(base_url, parser, ...)` — wires steps 1–5 for sale tools
- `_run_rent_tool(base_url, parser, ...)` — same for lease/rent tools

**Region code resolution** ([src/real_estate/data/region_code.py](src/real_estate/data/region_code.py)):
- Loads `src/real_estate/resources/region_codes.txt` (tab-separated: 10-digit code, name, status)
- `get_region_code` tool must be called first; returns the 5-digit `LAWD_CD` used by all trade/rent tools
- Gu/gun-level rows (last 5 digits `00000`) are preferred as the canonical match

**Additional tool groups (beyond trade/rent):**
- `get_apt_subscription_info` / `get_apt_subscription_results` — APT 청약 from `api.odcloud.kr`
- `get_public_auction_items` — onbid 공매 bid results from `apis.data.go.kr/B010003`
- `get_onbid_thing_info_list` — onbid item list from `openapi.onbid.co.kr`
- `get_onbid_*_code_info` / `get_onbid_addr*_info` — onbid code/address lookup from `openapi.onbid.co.kr`

These tools use the same `_run_trade_tool` / `_run_rent_tool` pattern but hit different base URLs. The `_ONBID_*` and `_ODCLOUD_*` URL constants are defined at the top of server.py.

**Key design constraints:**
- Prices are in 만원 (10,000 KRW) units, field suffix `_10k`
- `jeonse_ratio_pct` is always `null` from rent tools; callers compute it from trade and rent medians
- Villa/row-house rent is available via `get_villa_rent` (`RTMSDataSvcRHRent`)
- Commercial trade parser uses different field names (`building_type`, `building_use`, `building_ar`) vs residential tools (`unit_name`, `area_sqm`)

## Testing Conventions

Tests use `respx` to mock `httpx` calls — the real API is never called in unit tests. Each tool has its own test file under `tests/mcp_server/`. Coverage threshold is 80% (enforced by pytest-cov). `asyncio_mode = "auto"` is set so async tests require no extra decorator.
