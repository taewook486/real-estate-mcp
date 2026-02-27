# Korea Real Estate MCP - Technology Stack

## 기술 스택 개요

### 핵심 기술
- **언어**: Python 3.12+
- **MCP 프레임워크**: FastMCP (mcp[cli] >= 1.0.0)
- **패키지 관리자**: uv 0.9.28+
- **웹 프레임워크**: FastAPI 0.128.0+
- **비동기 처리**: asyncio, Starlette
- **서버**: Uvicorn

### 데이터 처리
- **데이터 검증**: Pydantic 2.0+
- **XML 파싱**: lxml, defusedxml, xmltodict
- **HTTP 클라이언트**: httpx 0.28.0+
- **HTTP 목킹**: respx 0.22.0+ (테스트용)

### 신뢰성 및 성능
- **캐싱**: cachetools 5.5.0+ (TTL 기반 LRU 캐시)
- **재시도**: tenacity 9.1.2+ (지수 백오프)
- **로깅**: structlog 25.5.0+ (구조화된 로그)

### 테스트
- **테스트 프레임워크**: pytest 8.0.0+
- **비동기 테스트**: pytest-asyncio
- **커버리지**: pytest-cov
- **목킹**: pytest-mock

## 프레임워크 선택 근거

### Python 3.12+
**선택 이유**:
- 강력한 타입 힌트 지원으로 안정적인 코드 작성
- asyncio 성능 향상
- 풍부한 생태계 및 라이브러리 지원
- MCP 서버 표준 구현이 Python 기반으로 제공

**대안 고려 사항**:
- TypeScript: MCP 서버 구현 가능하나, Python 생태계가 더 성숙함
- Go: 높은 성능이나, 공공데이터포털 API 연동 라이브러리가 부족함

### FastMCP (mcp[cli])
**선택 이유**:
- MCP 프로토콜의 공식 Python 구현
- 데코레이터 기반의 간편한 도구 정의
- stdio 및 HTTP 전송 자동 지원
- Claude Desktop과의 호환성 보장

**핵심 기능**:
```python
@mcp.tool()
def get_apt_trade_prices(region_code: str, year: int, month: int) -> dict:
    """아파트 매매가 조회 도구"""
    ...
```

### FastAPI
**선택 이유**:
- 비동기 처리 지원으로 높은 성능
- 자동 API 문서 생성 (OpenAPI)
- Pydantic 기반 데이터 검증
- MCP HTTP 전송 계층 구현에 적합

**웹 서버 모드**:
- Claude Desktop 외에 웹 클라이언트에서도 MCP 서버 활용 가능
- RESTful API 엔드포인트 제공
- WebSocket 지원으로 실시간 통신 가능

### Pydantic 2.0
**선택 이유**:
- 런타임 데이터 검증 자동화
- 타입 힌트 기반 스키마 정의
- 직렬화/역직렬화 자동 처리
- FastAPI와의 완벽한 통합

**활용 예시**:
```python
class AptTradeRequest(BaseModel):
    region_code: str = Field(..., pattern=r'^\d{5}$')
    year: int = Field(..., ge=2006, le=2024)
    month: int = Field(..., ge=1, le=12)
```

### httpx
**선택 이유**:
- 동기 및 비동기 HTTP 클라이언트 지원
- HTTP/2 지원
- 요청/응답 후킹 기능
- 타임아웃 및 재시도 설정 유연성

**재시도 메커니즘**:
```python
async with httpx.AsyncClient() as client:
    response = await client.get(
        url,
        timeout=10.0,
        headers=headers
    )
```

### lxml + defusedxml
**선택 이유**:
- **lxml**: 빠른 XML 파싱 성능
- **defusedxml**: XML bomb 공격 방지 (보안)

**안전한 파싱**:
```python
from defusedxml.ElementTree import fromstring
root = fromstring(xml_data)
```

### cachetools
**선택 이유**:
- TTL 기반 캐싱 지원
- LRU (Least Recently Used) 알고리즘
- 메모리 사용량 제어 (최대 100개 항목)
- 경량구현으로 오버헤드 최소화

**캐시 설정**:
- TTL: 5분 (300초)
- 최대 항목: 100개
- 캐시 키: API 엔드포인트 + 요청 파라미터

### tenacity
**선택 이유**:
- 선언적 재시도 정의
- 지수 백오프 (Exponential Backoff)
- 최대 재시도 횟수 설정 (3회)
- 일시적 오류에 대한 탄력적 대응

**재시도 정책**:
```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10)
)
async def fetch_api(url: str) -> dict:
    ...
```

### structlog
**선택 이유**:
- 구조화된 로그 출력 (JSON 형식)
- 문맥 정보 자동 포함
- 로그 레벨별 필터링
- 프로덕션 환경 로그 분석 용이

**로그 예시**:
```json
{
  "event": "api_call",
  "url": "https://api.odcloud.kr/api/...",
  "status_code": 200,
  "duration_ms": 150
}
```

### uv
**선택 이유**:
- 빠른 의존성 해석 (Rust로 작성됨)
- pyproject.toml 표준 지원
- 가상 환경 관리 통합
- pip보다 10-100배 빠른 속도

## 개발 환경 요구사항

### 시스템 요구사항
- **운영체제**: Windows 10+, macOS 12+, Linux (Ubuntu 20.04+)
- **Python**: 3.12 이상
- **메모리**: 4GB 이상 권장
- **디스크**: 500MB 이상 여유 공간

### 필수 도구
```bash
# Python 3.12 설치 확인
python --version

# uv 패키지 관리자 설치
pip install uv

# 프로젝트 의존성 설치
uv sync
```

### Claude Desktop 연동
```json
// claude_desktop_config.json
{
  "mcpServers": {
    "korea-real-estate": {
      "command": "uv",
      "args": [
        "--directory",
        "d:/project/real-estate-mcp",
        "run",
        "python",
        "-m",
        "real_estate.mcp_server.server"
      ]
    }
  }
}
```

### 환경 변수
```bash
# 공공데이터포털 API 키 (필수)
PUBLIC_DATA_API_KEY=your_api_key_here

# OAuth 2.0 설정 (선택)
OAUTH_CLIENT_ID=your_client_id
OAUTH_CLIENT_SECRET=your_client_secret
OAUTH_TOKEN_URL=https://auth.example.com/oauth/token

# 로그 레벨 (선택, 기본값: INFO)
LOG_LEVEL=INFO

# 캐시 TTL 초 (선택, 기본값: 300)
CACHE_TTL=300
```

## 빌드 및 배포 설정

### 로컬 개발
```bash
# 개발 서버 실행
uv run python -m real_estate.mcp_server.server

# 또는 배치 파일 사용
run.bat
```

### 테스트 실행
```bash
# 전체 테스트
uv run pytest

# 커버리지 리포트
uv run pytest --cov=src/real_estate --cov-report=html

# 특정 테스트
uv run pytest tests/mcp_server/tools/test_apt_trade.py
```

### 패키징
```bash
# PyPI 배포용 패키지 빌드
uv build

# 또는 pip 사용
pip install build
python -m build
```

### Docker 배포
```dockerfile
FROM python:3.12-slim

WORKDIR /app

# uv 설치
COPY pyproject.toml pyproject.lock ./
RUN pip install uv && uv sync --frozen

# 소스 코드 복사
COPY src/ ./src/

# 서버 실행
CMD ["uv", "run", "python", "-m", "real_estate.mcp_server.server"]
```

### CI/CD 통합
```yaml
# .github/workflows/test.yml
name: Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Install uv
        run: pip install uv
      - name: Install dependencies
        run: uv sync
      - name: Run tests
        run: uv run pytest --cov=src/real_estate
```

### 성능 최적화
- **비동기 처리**: FastAPI + Uvicorn으로 높은 처리량
- **캐싱**: TTL 5분 캐시로 중복 API 호출 방지
- **연결 풀링**: httpx의 비동기 연결 풀 활용
- **GC 튜닝**: Python 가비지 컬렉션 파라미터 최적화

### 보안 고려사항
- **API 키 관리**: 환경 변수로 API 키 저장 (소스 코드 미포함)
- **XML 파싱**: defusedxml로 XXE 공격 방지
- **입력 검증**: Pydantic으로 모든 입력 사전 검증
- **OAuth 2.0**: 안전한 토큰 기반 인증
- **속도 제한**: API 호출 속도 제한으로 과부하 방지

## 의존성 버전 정책

### 핵심 의존성
```
# MCP 및 웹 프레임워크
mcp[cli]>=1.0.0
fastapi>=0.128.0
uvicorn>=0.30.0

# 데이터 처리
pydantic>=2.0.0
lxml>=5.0.0
defusedxml>=0.7.1
xmltodict>=0.13.0

# 네트워킹
httpx>=0.28.0
respx>=0.22.0

# 신뢰성
cachetools>=5.5.0
tenacity>=9.1.2
structlog>=25.5.0

# 테스트
pytest>=8.0.0
pytest-asyncio>=0.23.0
pytest-cov>=5.0.0
pytest-mock>=3.14.0

# 개발 도구
uv>=0.9.28
ruff>=0.8.0
```

### 버전 고정 전략
- **개발**: 최신 버전 사용 (>=)
- **프로덕션**: pyproject.lock으로 정확한 버전 고정
- **보안 업데이트**: 취약점 발견 시 즉시 업그레이드
