# Korea Real Estate MCP - Architecture Overview

## 아키텍처 개요

Korea Real Estate MCP는 Model Context Protocol (MCP) 기반의 파이썬 서버로, 한국 부동산 데이터를 제공하는 17개의 도구를 노출합니다. 이 시스템은 계층형 아키텍처를 따르며 안정성과 확장성을 우선시합니다.

## 핵심 아키텍처 원칙

### 1. 계층형 분리 (Layered Separation)

시스템은 명확한 계층으로 분리되어 있습니다:

- **Transport Layer**: MCP 프로토콜 처리 (stdio/HTTP)
- **Tool Layer**: 17개 비즈니스 도구
- **Parser Layer**: XML/JSON 응답 변환
- **Helper Layer**: 공통 유틸리티 및 검증
- **Network Layer**: HTTP 클라이언트 및 재시도
- **Cache Layer**: TTL 기반 응답 캐싱

각 계층은 하위 계층에만 의존하며, 상위 계층으로부터 독립적입니다.

### 2. 단일 책임 원칙 (Single Responsibility)

각 모듈은 명확히 정의된 단일 책임을 가집니다:

- **server.py**: MCP 서버 진입점 및 라우팅
- **tools/**: 비즈니스 로직 구현
- **parsers/**: 데이터 변환 전담
- **helpers/**: 공통 기능 제공
- **cache_manager.py**: 캐싱 전략 관리

### 3. 의존성 역전 (Dependency Inversion)

고수준 모듈(tool)은 저수준 모듈(network)의 구체적 구현에 의존하지 않고, 추상화된 인터페이스(_fetch_xml/_fetch_json)를 통해 통신합니다.

## 시스템 경계 (System Boundaries)

### 내부 경계 (Internal Boundaries)

1. **MCP Server Boundary**: FastMCP 프레임워크로 정의됨
2. **Tool Layer Boundary**: @mcp.tool() 데코레이터로 정의됨
3. **Parser Boundary**: XML/JSON → Dict 변환
4. **Cache Boundary**: APICache 클래스로 캡슐화됨

### 외부 경계 (External Boundaries)

1. **Client Boundary**: Claude Desktop 또는 웹 클라이언트
2. **API Boundary**: 공공데이터포털, 온비드, 청약홈 API
3. **Auth Boundary**: OAuth 2.0 토큰 검증 (auth_server.py)

## 디자인 패턴 (Design Patterns)

### 1. Tool Runner Pattern

모든 도구는 `_run_trade_tool()`, `_run_rent_tool()` 헬퍼를 통해 실행됩니다:

```python
def _run_trade_tool(
    region_code: str,
    year_month: str,
    api_url_template: str,
    parser_func: Callable,
) -> dict[str, Any]:
```

이 패턴은 다음을 보장합니다:
- 일관된 입력 검증
- 표준화된 오류 처리
- 통일된 응답 형식

### 2. Circuit Breaker Pattern

네트워크 계층은 실패 격리를 위해 Circuit Breaker 패턴을 구현합니다:

```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10)
)
async def _fetch_xml(url: str) -> tuple[str | None, dict[str, Any] | None]:
```

### 3. Cache-Aside Pattern

캐시는 Cache-Aside 패턴을 따릅니다:

1. 캐시 확인
2. 캐시 미스시 API 호출
3. 성공 응답만 캐싱
4. TTL 기반 만료

### 4. Strategy Pattern

파서는 Strategy Pattern을 사용합니다:

- **trade_parser.py**: 매매가 XML 파싱 전략
- **rent_parser.py**: 전월세가 XML 파싱 전략
- **onbid_parser.py**: 온비드 XML 파싱 전략

각 파서는 공통 인터페이스를 구현하며, 도구는 필요에 따라 전략을 선택합니다.

## 데이터 흐름 패턴

### 1. 요청 처리 흐름

```
Client Request
    ↓
Transport Layer (stdio/HTTP)
    ↓
MCP Tool Registration (@mcp.tool())
    ↓
Tool Execution
    ↓
Helper Validation (validate_region_code, validate_year_month)
    ↓
Network Layer (_fetch_xml/_fetch_json with retry)
    ↓
Cache Layer (check cache → fetch → store)
    ↓
Parser Layer (XML/JSON → Dict)
    ↓
Response Formatting
    ↓
Client Response
```

### 2. 오류 처리 흐름

```
Error Detection
    ↓
Error Classification (6 types)
    ↓
Error Response Generation
    ↓
Client Notification
```

## 비기능적 요구사항 (Non-Functional Requirements)

### 1. 성능 (Performance)

- **캐싱**: TTL 5분으로 API 호출 최소화
- **비동기 처리**: asyncio로 높은 처리량
- **연결 풀링**: httpx 비동기 연결 풀 활용

### 2. 신뢰성 (Reliability)

- **재시도 메커니즘**: 최대 3회 재시도, 지수 백오프
- **Circuit Breaker**: 연속 실패시 요청 중단
- **안전한 XML 파싱**: defusedxml로 XXE 공격 방지

### 3. 보안 (Security)

- **입력 검증**: 모든 입력을 Pydantic으로 사전 검증
- **API 키 관리**: 환경 변수로 키 저장
- **OAuth 2.0**: 토큰 기반 인증

### 4. 유지보수성 (Maintainability)

- **모듈화**: 명확한 계층과 책임 분리
- **테스트 커버리지**: 87.33% 커버리지
- **구조화된 로깅**: structlog로 문맥 정보 포함

## 기술적 제약사항

### 1. MCP 프로토콜 제약

- FastMCP 프레임워크 사용 필수
- @mcp.tool() 데코레이터로 도구 등록
- 표준 JSON 응답 형식 준수

### 2. API 제약

- 공공데이터포털 일일 호출 제한 준수
- XML 응답 형식 처리 필수
- 요청 파라미터 검증 필수

### 3. 캐싱 제약

- 최대 100개 항목 캐싱
- TTL 5분 초과 불가
- 성공 응답만 캐싱

## 확장성 고려사항

### 1. 새로운 도구 추가

다음 단계로 새 도구를 추가할 수 있습니다:
1. tools/ 디렉토리에 새 모듈 생성
2. @mcp.tool() 데코레이터로 함수 등록
3. 필요한 파서 전략 구현
4. 테스트 추가

### 2. 새로운 데이터 소스 연동

다음 단계로 새 API를 연동할 수 있습니다:
1. _helpers/에 새 fetch 함수 추가
2. 전용 파서 구현
3. 캐시 키 생성 로직 업데이트
4. 통합 테스트 추가

### 3. 전송 계층 확장

현재 stdio와 HTTP를 지원하지만, WebSocket 등 다른 전송 계층으로 확장 가능합니다.

## 아키텍처 다이어그램

```
┌─────────────────────────────────────────────────────────────┐
│                     Clients                                  │
│  (Claude Desktop, Web Browser, ChatGPT)                     │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                  Transport Layer                             │
│  ┌──────────────────┐      ┌──────────────────┐            │
│  │  stdio (Desktop) │      │  HTTP (Web)      │            │
│  └──────────────────┘      └──────────────────┘            │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                   MCP Server (FastMCP)                      │
│  ┌─────────────────────────────────────────────────┐       │
│  │              Tool Registry                      │       │
│  │  (17 tools: trade, rent, subscription, onbid)  │       │
│  └────────────────────┬────────────────────────────┘       │
└────────────────────────┼────────────────────────────────────┘
                         │
         ┌───────────────┴───────────────┐
         ▼                               ▼
┌──────────────────────┐    ┌──────────────────────────┐
│   Helper Layer       │    │    Cache Layer           │
│  ┌────────────────┐  │    │  ┌────────────────────┐ │
│  │  Validation    │  │    │  │  APICache (TTL)    │ │
│  │  Error Handler │  │    │  │  Max 100 items     │ │
│  └────────────────┘  │    │  └────────────────────┘ │
└───────────┬──────────┘    └───────────┬──────────────┘
            │                           │
            └───────────┬───────────────┘
                        ▼
         ┌──────────────────────────────┐
         │      Network Layer           │
         │  ┌────────────────────────┐  │
         │  │  HTTP Client (httpx)   │  │
         │  │  Retry (tenacity)      │  │
         │  └────────────────────────┘  │
         └──────────────┬───────────────┘
                        │
                        ▼
         ┌──────────────────────────────┐
         │      External APIs           │
         │  - MOLIT (공공데이터포털)    │
         │  - Onbid (온비드)            │
         │  - Applyhome (청약홈)       │
         └──────────────────────────────┘
```

## 아키텍처 결정 기록 (ADR)

### ADR-001: FastMCP 선택

**결정**: MCP 프로토콜 구현을 위해 FastMCP (mcp[cli]) 선택

**근거**:
- 공식 Python MCP 구현
- 데코레이터 기반 간편한 도구 정의
- stdio/HTTP 자동 지원
- Claude Desktop 호환성 보장

**대안**: TypeScript MCP SDK, Go MCP 구현

### ADR-002: TTL 캐싱 전략

**결정**: 5분 TTL, 최대 100항목 캐싱 전략 선택

**근거**:
- 부동산 데이터는 5분内 변동성 낮음
- 일일 API 호출 제준 준수
- 메모리 사용량 제어

**대안**: 무제한 캐싱, 데이터베이스 캐싱

### ADR-003: 동기/비동기 혼합 사용

**결정**: MCP 도구는 비동기로, 내부 헬퍼는 동기/비동기 혼합 사용

**근거**:
- FastMCP가 비동기 도구 지원
- 기존 동기 코드와의 호환성
- 필요한 부분만 비동기로 최적화

**대안**: 전체 비동기, 전체 동기
