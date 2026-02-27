# SPEC-CACHE-003: 인수 기준

## 시나리오 기반 테스트

### Feature: 지역코드 캐싱

#### Scenario: 지역코드 캐싱
**Given** 서버가 시작됨
**When** 첫 번째 `get_region_code` 호출이 발생함
**Then** 파일에서 데이터를 로드하고 캐시에 저장함
**And** 두 번째 호출부터는 파일 읽기 없이 캐시된 데이터를 사용함

#### Scenario: 캐시 성능
**Given** 지역코드가 캐시된 상태
**When** 100회의 `get_region_code` 호출이 실행됨
**Then** 모든 호출이 10ms 이내에 완료됨
**And** 파일 읽기는 1회만 발생함

### Feature: 구조화 로깅

#### Scenario: 구조화 요청 로깅
**Given** 사용자가 아파트 매매 조회를 요청함
**When** 요청이 처리됨
**Then** JSON 형식 로그에 다음 필드가 포함됨:
```
{
  "timestamp": "2026-02-19T10:30:00Z",
  "level": "info",
  "tool_name": "get_apt_trades",
  "laumd_cd": "11110",
  "deal_ymd": "202601",
  "duration_ms": 1250,
  "status": "success"
}
```

#### Scenario: 오류 구조화 로깅
**Given** API 호출이 실패함
**When** 오류가 발생함
**Then** JSON 형식 로그에 다음 필드가 포함됨:
```
{
  "timestamp": "2026-02-19T10:30:00Z",
  "level": "error",
  "error_code": "22",
  "error_message": "daily limit exceeded",
  "stack_trace": "...",
  "tool_name": "get_apt_trades"
}
```

## 엣지 케이스 테스트

### Edge Case 1: 캐시 무효화
**Given** 지역코드가 캐시된 상태
**When** 테스트를 위해 캐시 클리어가 호출됨
**Then** 다음 요청에서 파일을 다시 읽음

### Edge Case 2: 로그 파일 회전
**Given** 장시간 서버 운영으로 로그 파일이 커짐
**When** 로그 회전이 발생함
**Then** JSON 로그 형식이 유지됨
**And** 로그 손실이 발생하지 않음

## 성능 기준

| 항목 | 기준 | 측정 방법 |
|------|------|----------|
| 캐시 적재 시간 | 100ms 이내 | 타이머 측정 |
| 캐시된 조회 시간 | 10ms 이내 | 타이머 측정 |
| 메모리 증가 | 20MB 이내 | 메모리 프로파일러 |
| 로그 오버헤드 | 5ms 이내 | 프로파일링 |

## 품질 기준 (TRUST 5)

| 항목 | 기준 |
|------|------|
| Tested | 신규 코드 85%+ 커버리지 |
| Readable | 명확한 필드명, JSON 표준 준수 |
| Unified | ruff formatting 통과 |
| Secured | 민감 정보 로깅 제외 |
| Trackable | Git 커밋 메시지 포맷 준수 |
