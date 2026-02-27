# Korea Real Estate MCP - Dependencies

## 의존성 그래프 개요

시스템은 3계층 의존성 구조를 따릅니다:
1. **외부 의존성**: PyPI 패키지 및 시스템 라이브러리
2. **내부 모듈 의존성**: 프로젝트 내 모듈 간 의존성
3. **API 의존성**: 외부 API 서비스

---

## 1. 외부 패키지 의존성 (PyPI)

### 핵심 프레임워크

#### mcp[cli] >= 1.0.0
- **용도**: MCP 프로토콜 구현
- **핵심 모듈**: FastMCP
- **사용 위치**: tools/__init__.py, server.py
- **의존성 타입**: 런타임 필수
- **라이선스**: MIT

```python
from real_estate.mcp_server import mcp

@mcp.tool()
def my_tool():
    pass
```

#### fastapi >= 0.128.0
- **용도**: HTTP 전송 계층 웹 프레임워크
- **핵심 모듈**: FastAPI, Form, HTTPException, Request
- **사용 위치**: transport/http.py, auth_server.py
- **의존성 타입**: 런타임 필수 (HTTP 모드)
- **라이선스**: MIT

```python
from fastapi import FastAPI, Form

app = FastAPI()

@app.post("/oauth/token")
async def token(grant_type: str = Form(...)):
    pass
```

#### uvicorn >= 0.30.0
- **용도**: ASGI 서버
- **사용 위치**: server.py (HTTP 모드 실행)
- **의존성 타입**: 런타임 필수 (HTTP 모드)
- **라이선스**: BSD

```python
import uvicorn

uvicorn.run(app, host="127.0.0.1", port=8000)
```

### 데이터 처리

#### pydantic >= 2.0.0
- **용도**: 데이터 검증 및 직렬화
- **핵심 모듈**: BaseModel, Field
- **사용 위치**: 모든 입력 검증
- **의존성 타입**: 런타임 필수
- **라이선스**: MIT

```python
from pydantic import BaseModel, Field

class Request(BaseModel):
    region_code: str = Field(..., pattern=r'^\d{5}$')
```

#### lxml >= 5.0.0
- **용도**: 고성능 XML 파싱
- **사용 위치**: parsers/*.py
- **의존성 타입**: 런타임 필수
- **라이선스**: BSD

```python
from lxml import etree

root = etree.fromstring(xml_text)
```

#### defusedxml >= 0.7.1
- **용도**: 안전한 XML 파싱 (XXE 공격 방지)
- **사용 위치**: parsers/*.py
- **의존성 타입**: 런타임 필수 (보안)
- **라이선스**: Python-2.0

```python
from defusedxml.ElementTree import fromstring

root = fromstring(xml_text)
```

#### xmltodict >= 0.13.0
- **용도**: XML → 딕셔너리 변환
- **사용 위치**: parsers/*.py
- **의존성 타입**: 런타임 필수
- **라이선스**: MIT

```python
import xmltodict

data = xmltodict.parse(xml_text)
```

### 네트워킹

#### httpx >= 0.28.0
- **용도**: 동기/비동기 HTTP 클라이언트
- **핵심 모듈**: AsyncClient
- **사용 위치**: _helpers.py (_fetch_xml, _fetch_json)
- **의존성 타입**: 런타임 필수
- **라이선스**: Apache-2.0

```python
import httpx

async with httpx.AsyncClient() as client:
    response = await client.get(url, timeout=10.0)
```

#### respx >= 0.22.0
- **용도**: HTTP 목킹 (테스트용)
- **사용 위치**: tests/
- **의존성 타입**: 개발 의존성
- **라이선스**: Apache-2.0

```python
import respx

@respx.mock
def test_api_call():
    respx.get("https://api.example.com").mock(return_value=httpx.Response(200))
```

### 신뢰성

#### cachetools >= 5.5.0
- **용도**: TTL 기반 캐싱
- **핵심 모듈**: TTLCache
- **사용 위치**: cache_manager.py
- **의존성 타입**: 런타임 필수
- **라이선스**: MIT

```python
from cachetools import TTLCache

cache = TTLCache(maxsize=100, ttl=300)
```

#### tenacity >= 9.1.2
- **용도**: 재시도 메커니즘
- **핵심 모듈**: retry, stop_after_attempt, wait_exponential
- **사용 위치**: _helpers.py
- **의존성 타입**: 런타임 필수
- **라이선스**: Apache-2.0

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
async def fetch_api():
    pass
```

#### structlog >= 25.5.0
- **용도**: 구조화된 로깅
- **핵심 모듈**: get_logger
- **사용 위치**: 모든 모듈
- **의존성 타입**: 런타임 필수
- **라이선스**: Apache-2.0

```python
import structlog

logger = structlog.get_logger()
logger.info("api_call", url="https://api.example.com")
```

### 테스트

#### pytest >= 8.0.0
- **용도**: 테스트 프레임워크
- **의존성 타입**: 개발 의존성
- **라이선스**: MIT

```python
def test_function():
    assert result == expected
```

#### pytest-asyncio >= 0.23.0
- **용도**: 비동기 테스트 지원
- **의존성 타입**: 개발 의존성
- **라이선스**: Apache-2.0

```python
@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
    assert result is not None
```

#### pytest-cov >= 5.0.0
- **용도**: 커버리지 리포트
- **의존성 타입**: 개발 의존성
- **라이선스**: MIT

```bash
pytest --cov=src/real_estate --cov-report=html
```

#### pytest-mock >= 3.14.0
- **용도**: 목 객체 지원
- **의존성 타입**: 개발 의존성
- **라이선스**: MIT

```python
def test_with_mock(mocker):
    mock_func = mocker.patch('module.function')
    mock_func.return_value = 42
```

### 개발 도구

#### uv >= 0.9.28
- **용도**: 패키지 관리자
- **의존성 타입**: 빌드 의존성
- **라이선스**: MIT

```bash
uv sync
uv run python -m real_estate.mcp_server.server
```

#### ruff >= 0.8.0
- **용도**: 린팅 및 포맷팅
- **의존성 타입**: 개발 의존성
- **라이선스**: MIT

```bash
ruff check .
ruff format .
```

---

## 2. 내부 모듈 의존성

### 의존성 방향성

```
┌─────────────────────────────────────────────────────┐
│                  server.py                          │
│  (MCP Server Entry Point)                           │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│                   tools/                            │
│  (trade.py, rent.py, subscription.py, onbid.py)    │
└──────────────┬──────────────────────────────────────┘
               │
               ├──────────────────┬──────────────────┐
               ▼                  ▼                  ▼
    ┌──────────────────┐  ┌──────────────┐  ┌──────────────┐
    │   _helpers.py    │  │   parsers/   │  │cache_manager.│
    │  (network,       │  │ (trade_parser,│  │     py       │
    │   validation,    │  │  rent_parser,│  │  (caching)   │
    │   error_handler) │  │ onbid_parser)│  │              │
    └──────────────────┘  └──────────────┘  └──────────────┘
               │
               ▼
    ┌──────────────────────────────────────────────────┐
    │              External Libraries                  │
    │  (httpx, xmltodict, cachetools, tenacity, etc.)  │
    └──────────────────────────────────────────────────┘
```

### 모듈별 의존성

#### server.py
- **의존**: tools/*.py
- **의존성 타입**: 직접 가져오기 (import)

```python
import real_estate.mcp_server.tools.trade
import real_estate.mcp_server.tools.rent
import real_estate.mcp_server.tools.subscription
import real_estate.mcp_server.tools.onbid
```

#### tools/*.py
- **의존**: _helpers.py, parsers/*.py, cache_manager.py
- **의존성 타입**: 함수 호출

```python
from real_estate.mcp_server._helpers import (
    _fetch_xml,
    _fetch_json,
    validate_region_code,
    validate_year_month,
    create_error_response
)
from real_estate.mcp_server.parsers import trade_parser, rent_parser
from real_estate.cache_manager import cached_fetch_xml
```

#### parsers/*.py
- **의존**: xmltodict
- **의존성 타입**: 라이브러리 호출

```python
import xmltodict

def parse_trade_response(xml_text: str) -> dict[str, Any]:
    data = xmltodict.parse(xml_text)
    # 파싱 로직
```

#### _helpers.py
- **의존**: httpx, tenacity, structlog
- **의존성 타입**: 라이브러리 호출

```python
import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential
```

#### cache_manager.py
- **의존**: _helpers.py, cachetools, structlog
- **의존성 타입**: 함수 호출 + 라이브러리

```python
from real_estate.mcp_server._helpers import _fetch_xml, _fetch_json
from cachetools import TTLCache
import structlog
```

### 순환 의존성 방지

현재 시스템에는 순환 의존성이 없습니다. 의존성 방향성은 항상 상위 계층에서 하위 계층으로 흐릅니다.

---

## 3. API 의존성

### 공공데이터포털 API

#### 매매/전월세 API
- **기관**: 국토교통부 (MOLIT)
- **엔드포인트**: `https://api.odcloud.kr/api/Req/v1/*`
- **인증**: API 키 (디코딩)
- **형식**: XML
- **속도 제한**: 일일 1,000회 (무료)

#### 청약홈 API
- **기관**: 한국주택금융공사
- **엔드포인트**: `https://api.applyhome.co.kr/api/v1/*`
- **인증**: API 키 (Bearer 토큰)
- **형식**: JSON
- **속도 제한**: 일일 10,000회

### 온비드 API

#### 공매 물건 API
- **기관**: 한국자산관리공사 (KAMCO)
- **엔드포인트**: `https://www.onbid.co.kr/api/*`
- **인증**: 없음 (공개 API)
- **형식**: XML
- **속도 제한**: 없음

### API 통신 패턴

#### 요청 형식
```python
# 공공데이터포털
url = f"{base_url}?serviceKey={api_key}&LAWD_CD={region_code}&DEAL_YMD={year_month}"

# 청약홈
headers = {"Authorization": f"Bearer {token}"}
url = f"{base_url}?region_code={region_code}&year={year}&month={month}"

# 온비드
url = f"{base_url}?category_code={code}&law_code={law_code}"
```

#### 응답 처리
```python
# XML 응답
xml_text, error = await cached_fetch_xml(url)
if error:
    return create_error_response("API_ERROR", error["message"])
parsed = trade_parser.parse_trade_response(xml_text)

# JSON 응답
json_data, error = await cached_fetch_json(url, headers)
if error:
    return create_error_response("API_ERROR", error["message"])
```

---

## 4. 의존성 관리 전략

### 버전 고정 전략

#### 개발 환경
- **전략**: 최신 버전 사용 (>=)
- **목적**: 최신 기능 및 보안 패치 활용
- **파일**: pyproject.toml

```toml
[project.dependencies]
mcp = {version = ">=1.0.0", extras = ["cli"]}
fastapi = ">=0.128.0"
httpx = ">=0.28.0"
```

#### 프로덕션 환경
- **전략**: 정확한 버전 고정
- **목적**: 재현 가능한 빌드 보장
- **파일**: pyproject.lock

```toml
[[package]]
name = "mcp"
version = "1.0.0"
```

### 보안 업데이트

#### 취약점 스캔
```bash
# GitHub Dependabot 자동 스캔
# 또는 수동 확인
pip-audit
```

#### 업데이트 프로세스
1. 취약점 보고서 수신
2. 영향도 평가
3. 패치 버전 테스트
4. 프로덕션 배포

### 의존성 최소화

#### 불필요한 의존성 제거
- 사용하지 않는 패키지 주기적 검토
- 기능 중복시 단일 패키지 선택
- 경량 대안 우선 고려

#### 예시
- `requests` → `httpx` (비동기 지원)
- `json` → 내장 모듈
- `datetime` → 내장 모듈

---

## 5. 의존성 진단

### 의존성 분석 도구

#### pipdeptree
```bash
pip install pipdeptree
pipdeptree
```

#### pyproject-deps
```bash
pip install pyproject-deps
pyproject-deps
```

### 순환 의존성 감지

현재 프로젝트는 순환 의존성이 없습니다. 향후 모듈 추가 시 다음을 확인:

1. import 순환 확인
2. 타입 힌트 순환 회피 (typing.TYPE_CHECKING)
3. 인터페이스 분리로 결합도 감소

---

## 6. 성장에 따른 의존성 관리

### 새로운 기능 추가 시

1. **필수 패키지만 추가**: 최소한의 의존성 유지
2. **대안 평가**: 경량 패키지 우선
3. **라이선스 확인**: 호환 가능한 라이선스 선택
4. **보안 평가**: 활발히 유지보수되는 패키지 선택

### 의존성 제거 시

1. **사용하지 않는 import 제거**: 자동 도구 활용 (autoflake)
2. **기능 중복 제거**: 단일 패키지로 통합
3. **레거시 코드 정리**: 더 이상 필요 없는 패키지 삭제
