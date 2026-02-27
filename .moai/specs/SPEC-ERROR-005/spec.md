---
id: "SPEC-ERROR-005"
version: "1.0.0"
status: "completed"
created: "2026-02-26"
updated: "2026-02-27"
author: "MoAI"
priority: "high"
domain: "ERROR"
---

# SPEC-ERROR-005: MCP 도구 오류 응답 구조화 (MCP Tool Error Response Structuring)

## HISTORY

| 버전 | 날짜 | 변경사항 | 작성자 |
|------|------|----------|--------|
| 1.0.0 | 2026-02-26 | 초기 작성 | MoAI |

## 요약

모든 MCP 도구의 오류 응답을 표준화된 구조로 통일하여 사용자 경험을 개선하고 디버깅 효율성을 높입니다. 오류 코드, 메시지, 해결 제안을 포함한 일관된 응답 형식을 제공합니다.

## 배경

현재 오류 응답 형식이 도구마다 다릅니다:
- 일부 도구는 `{"error": "type", "message": "..."}` 형식 사용
- 다른 도구는 `{"error": "type", "code": "...", "message": "..."}` 형식 사용
- `docx_parser`, `hwp_parser` 등의 유틸리티 모듈은 예외를 직접 발생시킴
- 사용자가 오류 원인을 파악하기 어렵고 해결 방법을 알 수 없음

## 이해관계자

- **최종 사용자**: 명확한 오류 메시지와 해결 방법 기대
- **개발자**: 일관된 오류 처리 패턴 필요
- **운영자**: 오류 로그 분석 효율성 필요

## 요구사항 (EARS)

### 환경 (Environment)

- MCP 도구들은 `src/real_estate/mcp_server/tools/` 디렉토리에 위치
- 파서 모듈들은 `src/real_estate/mcp_server/parsers/` 및 `src/real_estate/common_utils/`에 위치
- 현재 `structlog`가 설치되어 구조화 로깅 지원

### 가정 (Assumptions)

- 모든 MCP 도구는 `dict[str, Any]` 타입을 반환
- 오류 응답은 추가 필드를 포함할 수 있음 (확장성)
- 사용자는 AI 어시스턴트를 통해 도구를 사용하므로 명확한 오류 메시지가 중요

### 요구사항 (Requirements)

#### REQ-ERROR-001: 표준 오류 응답 형식
**Ubiquitous**: 시스템은 모든 MCP 도구 오류 응답에 대해 표준화된 형식을 사용해야 한다.

표준 형식:
```json
{
  "error": "<error_type>",
  "message": "<human_readable_message>",
  "suggestion": "<actionable_solution>"
}
```

#### REQ-ERROR-002: 오류 유형 분류
**State-Driven**: **IF** 오류가 발생하면 **THEN** 시스템은 오류를 다음 유형 중 하나로 분류해야 한다:
- `config_error`: 환경 변수 설정 문제
- `invalid_input`: 사용자 입력 검증 실패
- `network_error`: API 연결 문제
- `api_error`: 외부 API 오류 응답
- `parse_error`: 데이터 파싱 실패
- `internal_error`: 예상치 못한 내부 오류

#### REQ-ERROR-003: 해결 제안 포함
**Event-Driven**: **WHEN** 오류 응답을 반환하면 **THEN** 시스템은 사용자가 취할 수 있는 구체적인 해결 제안을 포함해야 한다.

#### REQ-ERROR-004: 유틸리티 모듈 예외 변환
**Event-Driven**: **WHEN** 파서 모듈(`docx_parser`, `hwp_parser`)에서 예외가 발생하면 **THEN** 시스템은 예외를 표준 오류 응답으로 변환해야 한다.

#### REQ-ERROR-005: 오류 로깅 (Optional)
**Optional**: **Where possible**, 시스템은 오류 발생 시 구조화된 로그를 기록해야 한다.

### 명세 (Specifications)

| 항목 | 값 |
|------|-----|
| 신규 파일 | `src/real_estate/mcp_server/error_types.py` |
| 대상 파일 | `tools/*.py`, `parsers/*.py`, `common_utils/docx_parser.py`, `common_utils/hwp_parser.py` |
| 오류 유형 | `config_error`, `invalid_input`, `network_error`, `api_error`, `parse_error`, `internal_error` |
| 사용 라이브러리 | `structlog` (기존), `typing` |

## 비기능 요구사항

- **일관성**: 모든 도구가 동일한 오류 형식 사용
- **명확성**: 사용자가 이해하기 쉬운 메시지
- **실행 가능성**: 구체적인 해결 방법 제공
- **확장성**: 추가 필드 지원

## 의존성

- Python 3.12+
- structlog (기존 설치됨)

## 위험 분석

| 위험 | 확률 | 영향 | 완화 전략 |
|------|------|------|----------|
| 기존 오류 처리 로직 변경 영향 | 중간 | 중간 | 점진적 마이그레이션 |
| 메시지 번역 필요 | 낮음 | 낮음 | 한국어 메시지 우선 |
| 예외 처리 누락 | 중간 | 낮음 | 포괄적인 예외 캐치 패턴 |
