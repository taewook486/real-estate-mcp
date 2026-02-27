---
id: "SPEC-CONFIG-004"
version: "1.0.0"
status: "completed"
created: "2026-02-26"
updated: "2026-02-27"
author: "MoAI"
priority: "high"
domain: "CONFIG"
---

# SPEC-CONFIG-004: 환경 변수 설정 검증 레이어 (Configuration Validation Layer)

## HISTORY

| 버전 | 날짜 | 변경사항 | 작성자 |
|------|------|----------|--------|
| 1.0.0 | 2026-02-26 | 초기 작성 | MoAI |

## 요약

분산된 환경 변수 검증 로직을 중앙 집중화하여 설정 오류를 사전에 방지하고 명확한 오류 메시지를 제공합니다. Pydantic Settings를 활용한 타입 안전 설정 관리 시스템을 구축합니다.

## 배경

현재 `_check_api_key()`, `_check_onbid_api_key()`, `_check_odcloud_key()` 등의 함수가 개별적으로 환경 변수를 검증하고 있어 다음과 같은 문제가 있습니다:
- 검증 로직이 분산되어 유지보수가 어려움
- 설정 오류 발생 시 명확한 오류 메시지 부족
- 런타임이 아닌 시작 시점에 검증 필요 (Fail-fast 원칙)
- 중복 코드로 인한 일관성 부족

## 이해관계자

- **최종 사용자**: 명확한 설정 오류 안내 기대
- **운영자**: 환경 변수 설정 오류 디버깅 효율성 필요
- **개발자**: 통합된 설정 관리 패턴 필요

## 요구사항 (EARS)

### 환경 (Environment)

- 시스템은 `DATA_GO_KR_API_KEY`, `ONBID_API_KEY`, `ODCLOUD_API_KEY`, `ODCLOUD_SERVICE_KEY` 환경 변수를 사용
- 현재 `pydantic-settings>=2.0.0`이 이미 설치됨
- 각 MCP 도구 모듈에서 개별적으로 환경 변수 검증 수행

### 가정 (Assumptions)

- 환경 변수는 애플리케이션 시작 시점에 로드됨
- 필수 환경 변수가 누락된 경우 즉시 실패하는 것이 바람직함
- 사용자는 명확한 오류 메시지를 통해 설정 방법을 이해할 수 있음

### 요구사항 (Requirements)

#### REQ-CONFIG-001: 중앙 집중화된 설정 클래스
**Ubiquitous**: 시스템은 모든 환경 변수를 단일 `AppSettings` 클래스에서 관리해야 한다.

#### REQ-CONFIG-002: 시작 시점 검증 (Fail-fast)
**Event-Driven**: **WHEN** 모듈이 로드되면 **THEN** 시스템은 모든 필수 환경 변수의 유효성을 검증해야 한다.

#### REQ-CONFIG-003: 명확한 오류 메시지
**State-Driven**: **IF** 필수 환경 변수가 누락되거나 유효하지 않으면 **THEN** 시스템은 변수명, 설명, 설정 방법을 포함한 상세 오류 메시지를 제공해야 한다.

#### REQ-CONFIG-004: 개별 검증 함수 대체
**Event-Driven**: **WHEN** 중앙 설정 클래스가 구현되면 **THEN** 기존 `_check_api_key()`, `_check_onbid_api_key()`, `_check_odcloud_key()` 함수는 설정 클래스를 사용하도록 리팩터링되어야 한다.

#### REQ-CONFIG-005: 선택적 설정 지원 (Optional)
**Optional**: **Where possible**, 시스템은 선택적 환경 변수에 대한 기본값을 제공해야 한다.

### 명세 (Specifications)

| 항목 | 값 |
|------|-----|
| 신규 파일 | `src/real_estate/config_validator.py` |
| 사용 라이브러리 | `pydantic-settings>=2.0.0` (기존 설치됨) |
| 설정 클래스 | `AppSettings` (BaseSettings 상속) |
| 필수 환경 변수 | `DATA_GO_KR_API_KEY` |
| 선택적 환경 변수 | `ONBID_API_KEY`, `ODCLOUD_API_KEY`, `ODCLOUD_SERVICE_KEY` |
| 대체 파일 | `_helpers.py` (기존 검증 함수 리팩터링) |

## 비기능 요구사항

- **성능**: 설정 로드 시간 10ms 이내
- **호환성**: 기존 API 인터페이스 변경 없음
- **테스트 가능성**: 모의 환경 변수로 테스트 가능
- **보안**: 민감한 API 키는 로그에 출력되지 않음

## 의존성

- Python 3.12+
- pydantic-settings>=2.0.0 (기존 설치됨)

## 위험 분석

| 위험 | 확률 | 영향 | 완화 전략 |
|------|------|------|----------|
| 기존 코드와의 호환성 문제 | 중간 | 중간 | 점진적 마이그레이션 및 테스트 |
| Pydantic v2 문법 차이 | 낮음 | 낮음 | 공식 문서 참조 |
| 순환 import 가능성 | 낮음 | 중간 | 지연 import 패턴 사용 |
