# Korea Real Estate MCP

[English](README.md) | [한국어](README-ko.md)

Ask Claude about Korean apartment prices — powered by MOLIT's open API.
Provides 14+ tools for querying apartment, officetel, villa, single-house, and commercial trade/rent data, apartment subscriptions, and public auctions.

## Supported Tools

- [x] Apartment trade / rent (`get_apartment_trades`, `get_apartment_rent`)
- [x] Officetel trade / rent (`get_officetel_trades`, `get_officetel_rent`)
- [x] Villa / multi-family housing trade / rent (`get_villa_trades`, `get_villa_rent`)
- [x] Single-house / multi-household trade / rent (`get_single_house_trades`, `get_single_house_rent`)
- [x] Commercial building trades (`get_commercial_trade`)
- [x] Apartment subscription notices / results (`get_apt_subscription_info`, `get_apt_subscription_results`)
- [x] Onbid public auction bid results (`get_public_auction_items`)
- [x] Onbid item lookup (`get_onbid_thing_info_list`)
- [x] Onbid code / address lookup (`get_onbid_*_code_info`, `get_onbid_addr*_info`)
- [x] Region code lookup (`get_region_code`)

## New Features (v1.1.0)

### Network Reliability
- **Exponential Backoff Retry**: 최대 3회 재시도, 초기 1초/최대 8초 지연
- **Circuit Breaker**: 연속 5회 실패 시 일시적 호출 차단 (30초 대기)
- **Connection Quality Logging**: 10초 초과 응답 시 자동 로깅

### Configuration Management
- **Centralized Validation**: Pydantic Settings 기반 환경 변수 관리
- **Fail-fast**: 시작 시점에서 모든 필수 환경 변수 검증
- **Clear Error Messages**: 변수명, 설명, 설정 방법 포함된 상세 오류 안내

### Standardized Error Handling
- **6 Error Types**: config_error, invalid_input, network_error, api_error, parse_error, internal_error
- **User-Friendly Suggestions**: 각 오류 유형별 해결 제안 제공

### Performance Optimization
- **API Response Caching**: 5분 TTL, 최대 100개 항목 메모리 캐시
- **Input Validation**: 지역코드/날짜 형식 사전 검증으로 불필요한 API 호출 감소

## Prerequisites

- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- API key from [공공데이터포털](https://www.data.go.kr) — apply for the services below:
  - 국토교통부_아파트 매매 실거래가 자료
  - 국토교통부_아파트 전월세 자료
  - 국토교통부_오피스텔 매매 신고 자료
  - 국토교통부_오피스텔 전월세 자료
  - 국토교통부_연립다세대 매매 실거래가 자료
  - 국토교통부_연립다세대 전월세 실거래가 자료
  - 국토교통부_단독/다가구 매매 실거래가 자료
  - 국토교통부_단독/다가구 전월세 자료
  - 국토교통부_상업용건물(오피스) 매매 신고 자료
  - 한국자산관리공사_온비드 캠코공매물건 조회서비스
  - 한국자산관리공사_온비드 이용기관 공매물건 조회서비스
  - 한국자산관리공사_온비드 코드 조회서비스
  - 청약홈 APT 공고 (ApplyhomeInfoSvc, ApplyhomeStatSvc)

> For parsing API specs in hwp or docx format, see [Common Utils Guide](docs/guide-common-utils.md)

## Quick Start: Claude Desktop (stdio)

The fastest way to get started — the server runs as a child process of Claude Desktop.

1. Clone this repository locally.

    ```bash
    git clone <repository_url>
    cd real-estate-mcp
    ```

1. Open the Claude Desktop config file.

    ```bash
    open "$HOME/Library/Application Support/Claude/claude_desktop_config.json"
    ```

1. Add the entry below under `mcpServers`.

    ```json
    {
      "mcpServers": {
        "real-estate": {
          "command": "uv",
          "args": [
            "run",
            "--directory", "/path/to/real-estate-mcp",
            "python", "src/real_estate/mcp_server/server.py"
          ],
          "env": {
            "DATA_GO_KR_API_KEY": "your_api_key_here"
          }
        }
      }
    }
    ```

1. Restart Claude Desktop.
   Setup is complete when you can see the `real-estate` server in the tool list.

1. For better responses, create a **Project** in Claude Desktop and paste [resources/custom-instructions-ko.md](resources/custom-instructions-ko.md) into the **Project Instructions** tab.

## Connect with Other Clients

For HTTP mode, other clients, or per-service API key configuration, see the docs below.

| Client | Transport | Guide |
|--------|-----------|-------|
| Claude Desktop | stdio / HTTP | [docs/setup-claude-desktop.md](docs/setup-claude-desktop.md) |
| Claude (web) | HTTP only | [docs/setup-claude-web.md](docs/setup-claude-web.md) |
| Claude CLI | stdio / HTTP | [docs/setup-claude-cli.md](docs/setup-claude-cli.md) |
| Codex CLI | stdio / HTTP | [docs/setup-codex-cli.md](docs/setup-codex-cli.md) |
| ChatGPT (web) | HTTP only | [docs/setup-chatgpt-web.md](docs/setup-chatgpt-web.md) |
| Docker (HTTP + Caddy) | HTTP | [docs/setup-docker.md](docs/setup-docker.md) |
| OAuth (public access) | — | [docs/setup-oauth.md](docs/setup-oauth.md) |
