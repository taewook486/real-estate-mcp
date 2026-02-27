# Korea Real Estate MCP - Project Structure

## 디렉토리 구조

```
korea-real-estate-mcp/
├── .claude/                    # Claude Code 설정
│   ├── agents/                # 서브에이전트 정의
│   ├── commands/              # 슬래시 명령어
│   ├── hooks/                 # 이벤트 후크
│   ├── rules/                 # MoAI 규칙 및 워크플로우
│   └── skills/                # 스킬 정의
│
├── .moai/                     # MoAI 프로젝트 설정
│   ├── config/                # 설정 파일
│   │   └── sections/
│   │       ├── quality.yaml   # 품질 게이트 설정
│   │       ├── user.yaml      # 사용자 설정
│   │       └── language.yaml  # 언어 설정
│   ├── memory/                # 에이전트 메모리
│   ├── specs/                 # SPEC 문서
│   └── project/               # 프로젝트 문서 (이 파일)
│
├── src/real_estate/           # 메인 소스 코드
│   ├── mcp_server/            # MCP 서버 핵심
│   │   ├── server.py          # MCP 서버 진입점
│   │   ├── tools/             # 17개 MCP 도구
│   │   │   ├── __init__.py
│   │   │   ├── apt_trade.py       # 아파트 매매가
│   │   │   ├── apt_rent.py        # 아파트 전월세가
│   │   │   ├── multi_trade.py     # 다가구/다세대 매매가
│   │   │   ├── multi_rent.py      # 다가구/다세대 전월세가
│   │   │   ├── rowhouse_trade.py  # 연립/빌라 매매가
│   │   │   ├── rowhouse_rent.py   # 연립/빌라 전월세가
│   │   │   ├── single_trade.py    # 단독/다가구 매매가
│   │   │   ├── single_rent.py     # 단독/다가구 전월세가
│   │   │   ├── land_trade.py      # 토지 매매가
│   │   │   ├── rights_trade.py    # 분양권 매매가
│   │   │   ├── subscription_acceptance.py  # 청약 당첨률
│   │   │   ├── subscription_cutoff.py       # 청약 커트라인
│   │   │   ├── onbid_auction.py   # 온비드 공매 물건
│   │   │   ├── onbid_goods.py     # 온비드 물건 상세
│   │   │   ├── onbid_lawsuit.py   # 온비드 소송 정보
│   │   │   └── onbid_apartment.py # 온비드 아파트 정보
│   │   ├── parsers/           # XML 파서
│   │   │   ├── __init__.py
│   │   │   ├── trade_parser.py   # 매매가 파서
│   │   │   ├── rent_parser.py    # 전월세가 파서
│   │   │   └── onbid_parser.py   # 온비드 파서
│   │   ├── helpers/           # 헬퍼 함수
│   │   │   ├── __init__.py
│   │   │   ├── validation.py     # 입력 검증
│   │   │   └── error_handler.py  # 오류 처리
│   │   └── transport/          # 전송 계층
│   │       ├── __init__.py
│   │       ├── stdio.py          # stdio 전송 (Claude Desktop)
│   │       └── http.py           # HTTP 전송 (웹 클라이언트)
│   ├── common_utils/          # 공통 유틸리티
│   │   ├── hwp_parser.py      # HWP 파일 파서
│   │   ├── docx_parser.py     # DOCX 파일 파서
│   │   └── file_utils.py      # 파일 유틸리티
│   ├── cache_manager.py       # 캐시 관리자
│   ├── config_validator.py    # 설정 검증기
│   ├── auth_server.py         # OAuth 2.0 인증 서버
│   └── __init__.py
│
├── tests/                     # 테스트 스위트
│   ├── mcp_server/            # MCP 서버 단위 테스트
│   │   ├── tools/             # 도구 테스트
│   │   ├── parsers/           # 파서 테스트
│   │   ├── helpers/           # 헬퍼 테스트
│   │   └── transport/         # 전송 계층 테스트
│   ├── integration/           # 통합 테스트
│   ├── config/                # 설정 테스트
│   └── parsers/               # 파서 테스트
│
├── localdocs/                 # 로컬 문서
│   ├── backlog.*.md           # 백로그 항목
│   ├── plan.*.md              # 계획 문서
│   ├── learn.*.md             # 학습 노트
│   ├── worklog.*.md           # 작업 로그
│   └── refer.*.md             # 참고 자료
│
├── scripts/                   # 스크립트
│   └── setup_mcp.bat          # MCP 서버 시작 스크립트
│
├── docs/                      # 문서 (Nextra 기반)
│
├── pyproject.toml             # 프로젝트 설정 (uv)
├── pyproject.lock             # 의존성 락 파일
├── README.md                  # 프로젝트 README
├── CHANGELOG.md               # 변경 로그
├── CLAUDE.md                  # Claude Code 실행 지시문
└── run.bat                    # 실행 스크립트
```

## 핵심 디렉토리 용도

### src/real_estate/mcp_server/
MCP 서버의 핵심 로직이 위치한 곳입니다.

**tools/**: 17개의 MCP 도구가 각각 별도 모듈로 구현되어 있습니다. 각 도구는 FastMCP 데코레이터로 정의되며, 공공데이터포털 API와 통신합니다.

**parsers/**: XML 응답을 파싱하는 전용 파서가 있습니다. trade_parser는 매매가, rent_parser는 전월세가, onbid_parser는 온비드 데이터를 처리합니다.

**helpers/**: 입력 검증(validation)과 표준 오류 처리(error_handler)를 담당합니다.

**transport/**: stdio(표준 입출력)와 HTTP 두 가지 전송 방식을 지원합니다. stdio는 Claude Desktop, HTTP는 웹 클라이언트용입니다.

### tests/
370개 이상의 테스트가 87.33% 커버리지로 구현되어 있습니다.

**mcp_server/**: 각 모듈별 단위 테스트가 있습니다.

**integration/**: 여러 모듈이 함께 작동하는 통합 테스트가 있습니다.

**config/**: 설정 로딩 및 검증 테스트가 있습니다.

### .moai/
MoAI 프레임워크 설정 및 SPEC 문서가 위치합니다.

**project/**: 프로젝트 문서(product.md, structure.md, tech.md)가 저장됩니다.

## 핵심 파일 위치

### 진입점
- **src/real_estate/mcp_server/server.py**: MCP 서버 메인 진입점
- **run.bat**: 윈도우용 실행 스크립트
- **scripts/setup_mcp.bat**: MCP 설치 스크립트

### 설정
- **pyproject.toml**: 프로젝트 의존성 및 도구 설정
- **.moai/config/sections/quality.yaml**: 품질 게이트 설정 (TDD 모드)
- **CLAUDE.md**: Claude Code 실행 지시문

### 문서
- **README.md**: 프로젝트 개요 및 설치 가이드
- **CHANGELOG.md**: 버전별 변경 내역
- **.moai/project/**: 프로젝트 구조, 기술 스택 문서

## 모듈 조직

### 계층 구조

```
┌─────────────────────────────────────────┐
│          Transport Layer                │
│  (stdio, HTTP)                          │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│          MCP Tools Layer                │
│  (17개 도구)                             │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│      Parser & Helper Layer              │
│  (XML 파서, 검증, 오류 처리)             │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│      Network & Cache Layer              │
│  (HTTP 클라이언트, 캐시 관리자)          │
└─────────────────────────────────────────┘
```

### 의존성 흐름

1. **Transport Layer**가 사용자 요청을 수신
2. **MCP Tools Layer**가 적절한 도구를 찾아 실행
3. **Helper Layer**가 입력을 검증하고 API 호출
4. **Parser Layer**가 XML 응답을 파싱
5. **Cache Layer**가 결과를 캐싱
6. **Transport Layer**가 결과를 반환

### 모듈 간 통신

- **동기 통신**: 함수 호출을 통한 직접 통신
- **비동기 지원**: FastAPI 기반으로 비동기 처리 가능
- **오류 전파**: 표준화된 예외 타입으로 오류 전달
- **캐시 공유**: CacheManager를 통해 전역 캐시 공유

## 테스트 구조

### 테스트 계층

1. **단위 테스트**: 각 모듈별 독립적 테스트
2. **통합 테스트**: 여러 모듈이 함께 작동하는 테스트
3. **설정 테스트**: 설정 로딩 및 검증 테스트

### 테스트 커버리지

- **전체 커버리지**: 87.33%
- **도구 테스트**: 17개 도구별 테스트 존재
- **파서 테스트**: XML 파싱 로직 테스트
- **헬퍼 테스트**: 검증 및 오류 처리 테스트

### 테스트 실행

```bash
# 전체 테스트 실행
pytest

# 커버리지 포함 실행
pytest --cov=src/real_estate --cov-report=html

# 특정 모듈 테스트
pytest tests/mcp_server/tools/test_apt_trade.py
```
