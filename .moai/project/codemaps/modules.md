# Korea Real Estate MCP - Module Descriptions

## 모듈 개요

시스템은 6개의 핵심 모듈로 구성됩니다. 각 모듈은 명확한 책임과 공용 인터페이스를 가집니다.

## 1. Transport Module

### 위치
`src/real_estate/mcp_server/transport/`

### 책임
MCP 프로토콜 전송 계층 처리

### 구성요소

#### stdio.py
- **목적**: Claude Desktop용 표준 입출력 전송
- **역할**: MCP stdio 프로토콜 구현
- **의존성**: FastMCP 프레임워크

#### http.py
- **목적**: 웹 클라이언트용 HTTP 전송
- **역할**: MCP HTTP 프로토콜 구현
- **의존성**: FastAPI, Uvicorn

### 공용 인터페이스
```python
def main(transport: str, host: str, port: int) -> None
```

### 데이터 모델
- 입력: MCP 프로토콜 메시지 (JSON-RPC)
- 출력: MCP 응답 (JSON-RPC)

### 통신 방식
- 동기 통신 (stdio)
- 비동기 통신 (HTTP)

---

## 2. Tool Module

### 위치
`src/real_estate/mcp_server/tools/`

### 책임
비즈니스 로직 실행 및 MCP 도구 등록

### 구성요소

#### trade.py
**목적**: 부동산 매매가 조회 도구

**제공 도구**:
- `get_apartment_trades`: 아파트 매매가
- `get_officetel_trades`: 오피스텔 매매가
- `get_villa_trades`: 연립/빌라 매매가
- `get_single_house_trades`: 단독/다가구 매매가
- `get_commercial_trade`: 상업용 건물 매매가

**공용 인터페이스**:
```python
@mcp.tool()
def get_{housing_type}_trades(
    region_code: str,
    year_month: str
) -> dict[str, Any]
```

**의존성**: _helpers._fetch_xml, parsers.trade_parser

#### rent.py
**목적**: 부동산 전월세가 조회 도구

**제공 도구**:
- `get_apartment_rent`: 아파트 전월세가
- `get_officetel_rent`: 오피스텔 전월세가
- `get_villa_rent`: 연립/빌라 전월세가
- `get_single_house_rent`: 단독/다가구 전월세가

**공용 인터페이스**:
```python
@mcp.tool()
def get_{housing_type}_rent(
    region_code: str,
    year_month: str
) -> dict[str, Any]
```

**의존성**: _helpers._fetch_xml, parsers.rent_parser

#### subscription.py
**목적**: 청약 정보 조회 도구

**제공 도구**:
- `get_apt_subscription_info`: 청약 공고 정보
- `get_apt_subscription_results`: 청약 당첨 결과

**공용 인터페이스**:
```python
@mcp.tool()
def get_apt_subscription_info(
    region_code: str | None = None,
    year: int | None = None,
    month: int | None = None
) -> dict[str, Any]

@mcp.tool()
def get_apt_subscription_results(
    region_code: str,
    year: int,
    month: int
) -> dict[str, Any]
```

**의존성**: _helpers._fetch_json

#### onbid.py
**목적**: 온비드 공매 정보 조회 도구

**제공 도구**:
- `get_public_auction_items`: 공매 물건 입찰 결과
- `get_onbid_thing_info_list`: 통합용도별 물건 목록

**공용 인터페이스**:
```python
@mcp.tool()
def get_public_auction_items(
    category_code: str,
    law_code: str | None = None,
    sort: str = "DESC"
) -> dict[str, Any]

@mcp.tool()
def get_onbid_thing_info_list(
    category_code: str,
    law_code: str | None = None,
    addr_cd: str | None = None
) -> dict[str, Any]
```

**의존성**: _helpers._fetch_json, parsers.onbid_parser

#### finance.py
**목적**: 부동산 금융 관련 도구 (향후 확장용)

**제공 도구**: 현재 비어있음

#### __init__.py
**목적**: MCP 서버 인스턴스 생성

**공용 인터페이스**:
```python
mcp = FastMCP("korea-real-estate")
```

### 데이터 모델

#### 요청 모델
```python
{
    "region_code": str,    # 5자리 지역 코드
    "year_month": str,     # YYYYMM 형식
    "year": int,           # 4자리 연도
    "month": int           # 1-12 월
}
```

#### 응답 모델
```python
{
    "success": bool,
    "data": list[dict] | None,
    "summary": dict | None,
    "error": dict | None,
    "count": int
}
```

---

## 3. Parser Module

### 위치
`src/real_estate/mcp_server/parsers/`

### 책임
XML/JSON 응답을 구조화된 딕셔너리로 변환

### 구성요소

#### trade_parser.py
**목적**: 매매가 XML 파싱

**공용 인터페이스**:
```python
def parse_trade_response(xml_text: str) -> dict[str, Any]
```

**파싱 로직**:
1. XML을 딕셔너리로 변환 (xmltodict)
2. 항목 추출 및 필드 매핑
3. 데이터 타입 변환 (가격: str → int)
4. 요약 통계 계산

**의존성**: xmltodict

#### rent_parser.py
**목적**: 전월세가 XML 파싱

**공용 인터페이스**:
```python
def parse_rent_response(xml_text: str) -> dict[str, Any]
```

**파싱 로직**:
1. XML을 딕셔너리로 변환
2. 임대유형별 필드 매핑 (전세/월세)
3. 보증금 및 월세 정규화
4. 요약 통계 계산

**의존성**: xmltodict

#### onbid_parser.py
**목적**: 온비드 XML 파싱

**공용 인터페이스**:
```python
def parse_onbid_response(xml_text: str) -> dict[str, Any]
```

**파싱 로직**:
1. XML을 딕셔너리로 변환
2. 공매 물건 필드 매핑
3. 가격 정보 포맷팅
4. 위치 정보 추출

**의존성**: xmltodict

### 데이터 모델

#### 파싱 전 (XML)
```xml
<response>
  <header>
    <resultCode>00</resultCode>
  </header>
  <body>
    <items>
      <item>
        <거래금액>100,000</거래금액>
        <년>2024</년>
        <월>1</월>
      </item>
    </items>
  </body>
</response>
```

#### 파싱 후 (Dict)
```python
{
    "success": True,
    "data": [
        {
            "price": 100000,
            "year": 2024,
            "month": 1
        }
    ],
    "summary": {
        "count": 1,
        "avg_price": 100000
    }
}
```

---

## 4. Helper Module

### 위치
`src/real_estate/mcp_server/_helpers.py`

### 책임
공통 유틸리티 함수 제공

### 구성요소

#### 네트워크 함수
```python
async def _fetch_xml(
    url: str
) -> tuple[str | None, dict[str, Any] | None]

async def _fetch_json(
    url: str,
    headers: dict[str, str] | None = None
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]
```

**기능**:
- HTTP GET 요청 실행
- 재시도 메커니즘 (최대 3회)
- 타임아웃 처리 (10초)
- 오류 응답 포맷팅

**의존성**: httpx, tenacity

#### 검증 함수
```python
def validate_region_code(region_code: str) -> bool

def validate_year_month(year_month: str) -> bool

def validate_year(year: int) -> bool

def validate_month(month: int) -> bool
```

**기능**:
- 입력 파라미터 형식 검증
- 비즈니스 규칙 검증 (년도 범위, 월 범위)
- False 반환시 상세 오류 메시지 포함

**의존성**: 없음 (순수 함수)

#### 오류 처리 함수
```python
def create_error_response(
    error_type: str,
    message: str
) -> dict[str, Any]
```

**지원 오류 타입**:
1. `VALIDATION_ERROR`: 입력 검증 실패
2. `API_ERROR`: API 호출 실패
3. `PARSE_ERROR`: 응답 파싱 실패
4. `NETWORK_ERROR`: 네트워크 오류
5. `AUTH_ERROR`: 인증 실패
6. `UNKNOWN_ERROR`: 알 수 없는 오류

#### 지역 코드 검색
```python
def search_region_code(query: str) -> dict[str, Any]
```

**기능**:
- 자유형식 지역명 검색
- 5자리 법정동 코드 반환
- 퍼지 매칭 지원

**의존성**: 내장 지역 코드 데이터베이스

---

## 5. Cache Module

### 위치
`src/real_estate/cache_manager.py`

### 책임
API 응답 캐싱 및 TTL 관리

### 구성요소

#### APICache 클래스
```python
class APICache:
    def __init__(self, ttl: float = 300, maxsize: int = 100)
    def get(self, key: str) -> tuple[Any, dict | None] | None
    def set(self, key: str, value: tuple[Any, dict | None]) -> None
    def delete(self, key: str) -> None
    def clear(self) -> None
    def has(self, key: str) -> bool
    def get_stats(self) -> dict[str, Any]
```

**기능**:
- TTL 기반 캐싱 (기본 300초)
- 최대 항목 제한 (기본 100개)
- 캐시 통계 추� (hits, misses, hit_rate)
- 스레드 안전한 작업

**의존성**: cachetools.TTLCache

#### 캐시 키 생성
```python
def generate_cache_key(
    url: str,
    params: dict[str, Any] | None = None
) -> str
```

**기능**:
- URL + 정렬된 파라미터로 고유 키 생성
- SHA-256 해싱으로 일관된 키 길이 보장

#### 캐싱 래퍼
```python
async def cached_fetch_xml(
    url: str,
    params: dict[str, Any] | None = None
) -> tuple[str | None, dict[str, Any] | None]

async def cached_fetch_json(
    url: str,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None
) -> tuple[dict | list | None, dict[str, Any] | None]
```

**캐싱 전략**:
1. 캐시 확인
2. 캐시 히트시 즉시 반환
3. 캐시 미스시 API 호출
4. 성공 응답만 캐싱
5. TTL 만료시 자동 삭제

### 데이터 모델

#### 캐시 항목
```python
{
    "key": "sha256_hash",
    "value": (response_data, None),
    "expiry": timestamp
}
```

#### 캐시 통계
```python
{
    "hits": 150,
    "misses": 50,
    "hit_rate": 0.75,
    "size": 100
}
```

---

## 6. Auth Module

### 위치
`src/real_estate/auth_server.py`

### 책임
OAuth 2.0 토큰 발급 및 검증

### 구성요소

#### FastAPI 앱
```python
app = FastAPI()
```

#### 엔드포인트

##### 토큰 발급
```python
@app.post("/oauth/token")
async def token(
    grant_type: str = Form(...),
    client_id: str = Form(...),
    client_secret: str = Form(...)
) -> dict
```

**지원 그랜트 타입**:
- `client_credentials`: 클라이언트 자격 증명

**응답**:
```python
{
    "access_token": "hex_token",
    "token_type": "bearer",
    "expires_in": 3600
}
```

##### 토큰 검증
```python
@app.get("/oauth/verify")
async def verify(request: Request) -> dict
```

**검증 방식**:
1. Authorization 헤더에서 토큰 추출
2. Auth0 토큰 (JWS/JWE): userinfo 엔드포인트로 검증
3. 레거시 토큰 (hex): 메모리 내 저장소와 비교
4. 만료 확인

##### 메타데이터
```python
@app.get("/.well-known/oauth-protected-resource")
async def protected_resource_metadata() -> dict

@app.get("/.well-known/oauth-authorization-server")
async def oauth_metadata() -> dict
```

**목적**: RFC 9728, RFC 8414 준수 메타데이터 제공

### 데이터 모델

#### 토큰 저장소
```python
_tokens: dict[str, float]  # token → expiry_epoch
```

#### 환경 변수
```bash
OAUTH_CLIENT_ID=your_client_id
OAUTH_CLIENT_SECRET=your_client_secret
OAUTH_TOKEN_TTL=3600
AUTH0_DOMAIN=your_domain.auth0.com
AUTH0_AUDIENCE=your_audience
```

---

## 모듈 간 통신

### 동기 통신
- Tool → Helper: 함수 호출
- Helper → Network: 함수 호출
- Network → Parser: 함수 호출

### 비동기 통신
- Tool → Network: async/await
- Network → External API: async/await

### 오류 전파
```python
try:
    result = await some_operation()
    if error:
        return create_error_response("ERROR_TYPE", error_message)
except Exception as e:
    logger.error("operation_failed", error=str(e))
    return create_error_response("UNKNOWN_ERROR", str(e))
```

---

## 모듈 테스트 전략

### 단위 테스트
- 각 모듈 독립적으로 테스트
- 모의 객체 (mock)로 외부 의존성 대체
- 경계 조건 및 오류 케이스 포함

### 통합 테스트
- 여러 모듈이 함께 작동하는 시나리오 테스트
- 실제 API 호출은 HTTP 목킹 (respx)으로 대체
- 엔드투엔드 흐름 검증

### 테스트 커버리지
- 전체 커버리지: 87.33%
- 필수 모듈 커버리지: 85% 이상
