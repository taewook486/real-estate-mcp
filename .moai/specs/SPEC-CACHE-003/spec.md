---
id: "SPEC-CACHE-003"
version: "1.0.0"
status: "draft"
created: "2026-02-19"
updated: "2026-02-19"
author: "MoAI"
priority: "low"
domain: "CACHE"
---

# SPEC-CACHE-003: 지역코드 캐싱 및 구조화 로깅 구현

## HISTORY

| 버전 | 날짜 | 변경사항 | 작성자 |
|------|------|----------|--------|
| 1.0.0 | 2026-02-19 | 초기 작성 | MoAI |

## 요약

지역코드 데이터를 메모리에 캐싱하여 불필요한 파일 I/O를 제거하고, 구조화된 JSON 로깅을 도입하여 운영 효율성을 높입니다.

## 배경

현재 `get_region_code` 호출 시마다 25,000행 이상의 region_codes.txt 파일을 읽고 있으며, 기존 로깅은 디버깅에 부족합니다.

## 이해관계자

- **운영자**: 효율적인 로그 분석 기대
- **개발자**: 디버깅 효율성 개선 필요

## 요구사항 (EARS)

### 환경 (Environment)

- 지역코드 파일: `src/real_estate/resources/region_codes.txt` (약 25,000행)
- 현재 구현: `get_region_code` 호출 시마다 파일 읽기 수행
- 로깅: 현재 print 문과 기본 logging만 사용

### 가정 (Assumptions)

- 지역코드 데이터는 세션 중 자주 변경되지 않음
- 메모리 사용량 증가는 무시할 수 있는 수준
- 구조화 로깅은 로그 분석 도구와 호환되어야 함

### 요구사항 (Requirements)

#### REQ-CACHE-001: 지역코드 캐싱
**Ubiquitous**: 시스템은 지역코드 데이터를 최초 1회만 로드하여 메모리에 캐싱해야 한다.

#### REQ-CACHE-002: 캐시 재사용
**State-Driven**: **IF** 캐시된 지역코드 데이터가 로드되어 있으면 **THEN** 파일 읽기를 건너뛰고 메모리 데이터를 사용해야 한다.

#### REQ-CACHE-003: 구조화 요청 로깅
**Event-Driven**: **WHEN** API 요청이 처리되면 **THEN** 시스템은 JSON 형식의 구조화 로그를 기록해야 한다.

#### REQ-CACHE-004: 구조화 오류 로깅
**Event-Driven**: **WHEN** 오류가 발생하면 **THEN** 시스템은 요청 ID, 타임스탬프, 오류 상세를 포함한 구조화 로그를 기록해야 한다.

#### REQ-CACHE-005: 메트릭 수집 (Optional)
**Optional**: **Where possible**, 시스템은 요청 처리 시간과 메모리 사용량을 메트릭으로 수집해야 한다.

### 명세 (Specifications)

| 항목 | 값 |
|------|-----|
| 대상 파일 | `src/real_estate/mcp_server/_region.py`, `_helpers.py` |
| 캐싱 | 모듈 레벨 전역 변수 또는 `functools.lru_cache` |
| 로깅 | `structlog` 라이브러리 사용, JSON 포맷 출력 |
| 로그 필드 | timestamp, level, request_id, tool_name, duration_ms, status |

## 비기능 요구사항

- **성능**: 캐시 적재 시간 100ms 이내
- **메모리**: 캐시로 인한 메모리 증가 20MB 이내
- **호환성**: 기존 로그 형식과 병행 가능

## 의존성

- structlog (새로 추가)

## 위험 분석

| 위험 | 확률 | 영향 | 완화 전략 |
|------|------|------|----------|
| 메모리 부족 | 낮음 | 낮음 | 캐시 크기 모니터링 |
| 로그 파일 크기 | 중간 | 낮음 | 로그 회전 설정 |
