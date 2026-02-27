# Korea Real Estate MCP - Entry Points

## 진입점 개요

시스템은 3개의 주요 진입점을 제공합니다:
1. **MCP 서버 진입점**: Claude Desktop 및 웹 클라이언트용
2. **OAuth 인증 진입점**: HTTP 전송 모드용 토큰 관리
3. **테스트 진입점**: 개발 및 CI/CD용

---

## 1. MCP 서버 진입점

### 파일 위치
`src/real_estate/mcp_server/server.py`

### 함수 시그니처
```python
def main() -> None
```

### 실행 방식

#### stdio 모드 (Claude Desktop)
```bash
python -m real_estate.mcp_server.server
# 또는
uv run python -m real_estate.mcp_server.server
```

#### HTTP 모드 (웹 클라이언트)
```bash
python -m real_estate.mcp_server.server --transport http --host 127.0.0.1 --port 8000
# 또는
uv run python -m real_estate.mcp_server.server --transport http
```

### 파라미터

#### --transport
- **타입**: string (enum)
- **기본값**: "stdio"
- **옵션**: "stdio", "http"
- **용도**: MCP 전송 프로토콜 선택

```python
parser.add_argument(
    "--transport",
    choices=["stdio", "http"],
    default="stdio",
    help="Transport mode (default: stdio)"
)
```

#### --host
- **타입**: string
- **기본값**: "127.0.0.1"
- **용도**: HTTP 서버 호스트 주소 (HTTP 모드만)

```python
parser.add_argument(
    "--host",
    default="127.0.0.1",
    help="HTTP host (default: 127.0.0.1)"
)
```

#### --port
- **타입**: int
- **기본값**: 8000
- **용도**: HTTP 서버 포트 (HTTP 모드만)

```python
parser.add_argument(
    "--port",
    type=int,
    default=8000,
    help="HTTP port (default: 8000)"
)
```

### 초기화 프로세스

#### 1. 명령행 인자 파싱
```python
args = parser.parse_args()
```

#### 2. 전송 모드별 설정

##### stdio 모드
```python
if args.transport == "stdio":
    mcp.run()
```

**동작**:
- FastMCP가 stdio를 통해 MCP 메시지 수신
- JSON-RPC 프로토콜 처리
- 도구 등록 및 실행

##### HTTP 모드
```python
if args.transport == "http":
    import uvicorn
    from mcp.server.transport_security import TransportSecuritySettings

    # 호스트 및 포트 설정
    mcp.settings.host = args.host
    mcp.settings.port = args.port

    # 전송 보안 설정
    mcp.settings.transport_security = TransportSecuritySettings(
        enable_dns_rebinding_protection=False
    )

    # ASGI 앱 생성
    app = mcp.streamable_http_app()

    # Uvicorn 서버 시작
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        proxy_headers=True,
        forwarded_allow_ips=os.environ.get("FORWARDED_ALLOW_IPS", "127.0.0.1")
    )
```

**동작**:
- FastAPI 앱 생성
- HTTP → stdio 변환
- CORS 및 프록시 헤더 처리
- Uvicorn으로 비동기 서버 실행

### MCP 도구 등록

#### 자동 등록
```python
# tools/__init__.py에서 자동 로드
import real_estate.mcp_server.tools.trade      # 5개 매매 도구
import real_estate.mcp_server.tools.rent       # 4개 전월세 도구
import real_estate.mcp_server.tools.subscription  # 2개 청약 도구
import real_estate.mcp_server.tools.onbid      # 2개 온비드 도구
import real_estate.mcp_server.tools.finance    # 0개 (향후 확장용)
```

#### 수동 등록 (server.py)
```python
@mcp.tool()
def get_region_code(query: str) -> dict[str, Any]:
    """Convert region name to legal district code."""
    return search_region_code(query)

@mcp.tool()
def get_current_year_month() -> dict[str, str]:
    """Return current year-month in YYYYMM format."""
    from datetime import datetime, timezone
    now = datetime.now(tz=timezone.utc)
    return {"year_month": now.strftime("%Y%m")}
```

### 도구 리스트

#### 유틸리티 도구 (2개)
1. **get_region_code**: 지역명 → 지역코드 변환
2. **get_current_year_month**: 현재 연월 반환

#### 매매 도구 (5개)
1. **get_apartment_trades**: 아파트 매매가
2. **get_officetel_trades**: 오피스텔 매매가
3. **get_villa_trades**: 연립/빌라 매매가
4. **get_single_house_trades**: 단독/다가구 매매가
5. **get_commercial_trade**: 상업용 건물 매매가

#### 전월세 도구 (4개)
1. **get_apartment_rent**: 아파트 전월세가
2. **get_officetel_rent**: 오피스텔 전월세가
3. **get_villa_rent**: 연립/빌라 전월세가
4. **get_single_house_rent**: 단독/다가구 전월세가

#### 청약 도구 (2개)
1. **get_apt_subscription_info**: 청약 공고 정보
2. **get_apt_subscription_results**: 청약 당첨 결과

#### 온비드 도구 (2개)
1. **get_public_auction_items**: 공매 입찰 결과
2. **get_onbid_thing_info_list**: 통합용도별 물건 목록

**총계**: 17개 도구

---

## 2. OAuth 인증 진입점

### 파일 위치
`src/real_estate/auth_server.py`

### FastAPI 앱 인스턴스
```python
app = FastAPI()
```

### 실행 방식

#### 직접 실행
```bash
# 개발 서버
uvicorn real_estate.auth_server:app --reload --host 127.0.0.1 --port 8001
```

#### MCP HTTP 모드와 통합
```bash
# OAuth 서버는 별도 포트에서 실행
# MCP 서버는 OAuth 서버에 토큰 검증 요청
```

### 엔드포인트

#### POST /oauth/token
**목적**: OAuth 2.0 액세스 토큰 발급

**요청 파라미터** (application/x-www-form-urlencoded):
- `grant_type`: "client_credentials" (필수)
- `client_id`: OAuth 클라이언트 ID (필수)
- `client_secret`: OAuth 클라이언트 시크릿 (필수)

**응답** (application/json):
```json
{
  "access_token": "hex_token_64_characters",
  "token_type": "bearer",
  "expires_in": 3600
}
```

**오류 응답**:
```json
{
  "detail": "invalid_client"
}
```

#### GET /oauth/verify
**목적**: 액세스 토큰 검증

**요청 헤더**:
- `Authorization`: Bearer {token}

**성공 응답**: 200 OK (빈 본문)

**오류 응답**: 401 Unauthorized
```json
{
  "detail": "invalid_token"
}
```

**토큰 유형**:
1. **레거시 hex 토큰**: 메모리 내 저장소에서 검증
2. **Auth0 토큰 (JWS/JWE)**: Auth0 userinfo 엔드포인트로 검증

#### GET /.well-known/oauth-protected-resource
**목적**: RFC 9728 MCP 리소스 서버 메타데이터

**응답** (application/json):
```json
{
  "resource": "https://example.com/mcp",
  "authorization_servers": ["https://your-domain.auth0.com"],
  "scopes_supported": [],
  "resource_documentation": "https://example.com"
}
```

#### GET /.well-known/oauth-authorization-server
**목적**: RFC 8414 인증 서버 메타데이터

**응답** (application/json):
```json
{
  "issuer": "https://example.com",
  "authorization_endpoint": "https://your-domain.auth0.com/authorize",
  "token_endpoint": "https://your-domain.auth0.com/oauth/token",
  "registration_endpoint": "https://your-domain.auth0.com/oidc/register",
  "grant_types_supported": ["authorization_code", "client_credentials"],
  "code_challenge_methods_supported": ["S256"],
  "token_endpoint_auth_methods_supported": ["client_secret_post"]
}
```

### 환경 변수

#### 필수
```bash
OAUTH_CLIENT_ID=your_client_id
OAUTH_CLIENT_SECRET=your_client_secret
```

#### 선택
```bash
PUBLIC_BASE_URL=https://your-domain.com
AUTH0_DOMAIN=your-domain.auth0.com
AUTH0_AUDIENCE=your_audience
OAUTH_TOKEN_TTL=3600
```

### 토큰 저장소

#### 메모리 내 저장소
```python
_tokens: dict[str, float]  # token → expiry_epoch
```

**특징**:
- 인메모리 저장 (프로세스 재시작시 소멸)
- TTL 기반 만료
- 단일 서버 환경에서만 작동

**확장 고려사항**:
- Redis 등 외부 저장소로 확장 가능
- 분산 환경에서는 공유 저장소 필요

---

## 3. 테스트 진입점

### 파일 위치
`tests/` 디렉토리

### 실행 방식

#### 전체 테스트
```bash
pytest
```

#### 커버리지 포함
```bash
pytest --cov=src/real_estate --cov-report=html
```

#### 특정 테스트 파일
```bash
pytest tests/mcp_server/tools/test_trade.py
```

#### 특정 테스트 함수
```bash
pytest tests/mcp_server/tools/test_trade.py::test_get_apartment_trades
```

### 테스트 구조

#### 단위 테스트
- **위치**: `tests/mcp_server/`
- **대상**: 개별 모듈 및 함수
- **목킹**: 내부 함수 및 외부 API

```python
def test_get_region_code():
    result = search_region_code("마포구")
    assert result["region_code"] == "11440"
```

#### 통합 테스트
- **위치**: `tests/integration/`
- **대상**: 여러 모듈 협력
- **목킹**: 외부 API만

```python
@pytest.mark.asyncio
async def test_trade_tool_flow():
    # 전체 흐름 테스트
    result = await get_apartment_trades("11440", "202401")
    assert result["success"] is True
```

### 테스트 설정

#### conftest.py
```python
import pytest

@pytest.fixture
def mock_api_key(monkeypatch):
    monkeypatch.setenv("PUBLIC_DATA_API_KEY", "test_key")

@pytest.fixture
def cache_reset():
    reset_cache()
    yield
    reset_cache()
```

### pytest.mark 데코레이터

#### asyncio
```python
@pytest.mark.asyncio
async def test_async_function():
    result = await async_operation()
    assert result is not None
```

#### parametrize
```python
@pytest.mark.parametrize("region_code,expected", [
    ("11440", True),
    ("11680", True),
    ("99999", False)
])
def test_region_code_validation(region_code, expected):
    assert validate_region_code(region_code) == expected
```

---

## 4. 진입점별 시나리오

### 시나리오 1: Claude Desktop 연동

1. **사용자**: Claude Desktop 시작
2. **Claude Desktop**: MCP 서버 프로세스 시작 (stdio 모드)
   ```json
   {
     "mcpServers": {
       "korea-real-estate": {
         "command": "uv",
         "args": [
           "--directory", "d:/project/real-estate-mcp",
           "run", "python", "-m", "real_estate.mcp_server.server"
         ]
       }
     }
   }
   ```
3. **MCP 서버**: 도구 등록 완료 신호 전송
4. **Claude**: get_region_code 도구 호출
5. **MCP 서버**: 지역 코드 반환
6. **Claude**: get_apartment_trades 도구 호출
7. **MCP 서버**: 매매 데이터 반환

### 시나리오 2: 웹 클라이언트 연동

1. **사용자**: 웹 브라우저에서 접속
2. **OAuth 서버**: 사용자 인증 (Auth0)
3. **OAuth 서버**: 액세스 토큰 발급
4. **웹 클라이언트**: MCP 서버에 HTTP 요청 (Bearer 토큰)
5. **MCP 서버**: /oauth/verify로 토큰 검증
6. **MCP 서버**: 도구 실행 및 응답 반환
7. **웹 클라이언트**: 사용자에게 결과 표시

### 시나리오 3: 개발 및 테스트

1. **개발자**: 코드 수정
2. **개발자**: pytest 실행
3. **pytest**: 370개 테스트 실행
4. **pytest**: 커버리지 리포트 생성
5. **개발자**: 실패한 테스트 확인 및 수정
6. **개발자**: 커밋 전 전체 테스트 통과 확인

---

## 5. 진입점 확장

### 새로운 진입점 추가

#### 커맨드 라인 도구
```python
# src/real_estate/cli.py
import typer

app = typer.Typer()

@app.command()
def search(query: str):
    """지역 코드 검색"""
    result = search_region_code(query)
    typer.echo(f"Region Code: {result['region_code']}")

if __name__ == "__main__":
    app()
```

#### 웹 대시보드
```python
# src/real_estate/dashboard.py
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    return """
    <html>
      <body>
        <h1>Korea Real Estate MCP Dashboard</h1>
      </body>
    </html>
    """
```

### 진입점 선택 가이드

| 진입점 | 사용 사례 | 장점 | 단점 |
|--------|-----------|------|------|
| stdio | Claude Desktop | 낮은 지연, 단순 설정 | 웹 접근 불가 |
| HTTP | 웹 클라이언트 | 다중 클라이언트, CORS 지원 | 추가 인증 필요 |
| CLI | 스크립트 자동화 | 빠른 프로토타이핑 | MCP 기능 미사용 |
| Dashboard | 시각화 | 사용자 친화적 | 별개 구현 필요 |

---

## 6. 진입점 모니터링

### 로깅

#### MCP 서버 로그
```python
import structlog

logger = structlog.get_logger()

logger.info(
    "server_started",
    transport=args.transport,
    host=args.host,
    port=args.port
)
```

#### OAuth 서버 로그
```python
logger.info(
    "token_issued",
    client_id=client_id,
    expires_in=expires_in
)
```

### 메트릭

#### 수집 항목
- 요청 수 (도구별)
- 응답 시간 (P50, P95, P99)
- 오류율 (오류 타입별)
- 캐시 적중률
- API 호출 수

#### 도구
- Prometheus (메트릭 수집)
- Grafana (대시보드)

---

## 7. 진입점 보안

### stdio 모드 보안
- **위협**: 로컬 프로세스 접근
- **완화**: 시스템 권한으로 제한

### HTTP 모드 보안
- **위협**: 네트워크 스니핑, CSRF
- **완화**:
  - HTTPS 적용 (프로덕션)
  - OAuth 2.0 토큰 검증
  - CORS 설정
  - 속도 제한

### OAuth 서버 보안
- **위협**: 토큰 탈취, 무단 액세스
- **완화**:
  - 짧은 TTL (1시간)
  - HTTPS 강제
  - 클라이언트 시크릿 보호
  - Auth0 토큰 검증
