---
id: "SPEC-CACHE-007"
version: "1.0.0"
status: "completed"
created: "2026-02-26"
updated: "2026-02-27"
author: "MoAI"
priority: "medium"
domain: "CACHE"
---

# SPEC-CACHE-007: API 응답 캐싱 시스템 (API Response Caching System)

## HISTORY

| 버전 | 날짜 | 변경사항 | 작성자 |
|------|------|----------|--------|
| 1.0.0 | 2026-02-26 | 초기 작성 | MoAI |

## 요약

공공데이터포털 API 응답을 메모리에 캐싱하여 반복 요청 시 응답 속도를 개선하고 API 호출 횟수를 줄입니다. TTL(Time-To-Live) 기반 캐시 만료로 데이터 최신성을 보장합니다.

## 배경

현재 상황:
- 동일한 지역/날짜에 대한 반복 조회 시 매번 API 호출 발생
- API 호출은 네트워크 지연으로 인해 1-3초 소요
- 일일 API 호출 한도 존재 (서비스별 상이)
- SPEC-CACHE-003에서 지역코드 캐싱은 구현되었으나 API 응답 캐싱은 미구현
- SPEC-NETWORK-001에서 네트워크 신뢰성 구현 완료

## 이해관계자

- **최종 사용자**: 빠른 응답 속도 기대
- **운영자**: API 호출 한도 관리 효율성
- **API 제공자**: 호출 부하 감소

## 요구사항 (EARS)

### 환경 (Environment)

- 공공데이터포털 API 엔드포인트: `apis.data.go.kr`, `api.odcloud.kr`, `openapi.onbid.co.kr`
- 기존 구현: `tenacity`, `structlog` 설치됨
- 의존성: SPEC-NETWORK-001 (네트워크 신뢰성) 구현 완료

### 가정 (Assumptions)

- 부동산 거래 데이터는 실시간으로 변경되지 않음 (월 단위 업데이트)
- 5분 TTL은 데이터 최신성과 성능의 적절한 균형
- 메모리 사용량 증가는 허용 가능한 수준
- 캐시는 프로세스 내 메모리에 저장 (분산 캐시 불필요)

### 요구사항 (Requirements)

#### REQ-CACHE-001: TTL 기반 캐시 구현
**Ubiquitous**: 시스템은 API 응답을 TTL(Time-To-Live) 기반으로 캐싱해야 한다.

#### REQ-CACHE-002: 캐시 키 생성
**Event-Driven**: **WHEN** API 요청이 발생하면 **THEN** 시스템은 URL과 파라미터를 조합한 고유 캐시 키를 생성해야 한다.

#### REQ-CACHE-003: 캐시 조회 및 반환
**State-Driven**: **IF** 캐시된 응답이 존재하고 만료되지 않았으면 **THEN** 시스템은 API 호출 없이 캐시된 응답을 반환해야 한다.

#### REQ-CACHE-004: 캐시 갱신
**Event-Driven**: **WHEN** 캐시 미스가 발생하면 **THEN** 시스템은 API를 호출하고 응답을 캐시에 저장해야 한다.

#### REQ-CACHE-005: 캐시 통계 (Optional)
**Optional**: **Where possible**, 시스템은 캐시 적중률 및 메모리 사용량을 로깅해야 한다.

### 명세 (Specifications)

| 항목 | 값 |
|------|-----|
| 신규 파일 | `src/real_estate/cache_manager.py` |
| 사용 라이브러리 | `cachetools>=5.5.0` (새로 추가) |
| 캐시 구현 | `cachetools.TTLCache` |
| 기본 TTL | 300초 (5분) |
| 최대 캐시 크기 | 100개 항목 |
| 캐시 키 생성 | URL + 정렬된 파라미터 해시 |

## 비기능 요구사항

- **성능**: 캐시 적중 시 응답 시간 10ms 이내
- **메모리**: 캐시로 인한 메모리 증가 50MB 이내
- **일관성**: TTL 만료 후 최신 데이터 조회 보장
- **투명성**: 기존 API 인터페이스 변경 없음

## 의존성

- Python 3.12+
- cachetools>=5.5.0 (새로 추가)
- SPEC-NETWORK-001 (이미 구현됨)

## 위험 분석

| 위험 | 확률 | 영향 | 완화 전략 |
|------|------|------|----------|
| 메모리 부족 | 낮음 | 중간 | 최대 캐시 크기 제한 |
| 오래된 데이터 반환 | 낮음 | 중간 | 적절한 TTL 설정 |
| 캐시 무효화 누락 | 낮음 | 낮음 | TTL 자동 만료 활용 |
| 동시성 문제 | 낮음 | 중간 | 스레드 안전 캐시 사용 |
