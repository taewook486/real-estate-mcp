# SPEC-NETWORK-001: 인수 기준

## 시나리오 기반 테스트

### Feature: 네트워크 재시트 메커니즘

#### Scenario: 일시적 네트워크 오류 복구
**Given** 공공데이터포털 API가 일시적으로 응답하지 않음
**When** 사용자가 아파트 매매 조회를 요청함
**Then** 시스템은 최대 3회 재시트 후 성공 시 정상 응답을 반환함
**And** 재시트 횟수가 로그에 기록됨

#### Scenario: 최대 재시트 초과
**Given** 공공데이터포털 API가 지속적으로 응답하지 않음
**When** 사용자가 아파트 매매 조회를 요청함
**Then** 시스템은 3회 재시트 후 실패 응답을 반환함
**And** "API 서버에 연결할 수 없습니다" 메시지가 포함됨

### Feature: Circuit Breaker

#### Scenario: Circuit Breaker 활성화
**Given** API 호출이 연속 5회 실패함
**When** 6번째 호출이 시도됨
**Then** Circuit Breaker가 열리고 즉시 실패 응답을 반환함
**And** 사용자에게 "서비스 일시 중단" 메시지가 표시됨

#### Scenario: Circuit Breaker 복구
**Given** Circuit Breaker가 열린 상태
**When** 30초가 경과함
**Then** Circuit Breaker가 반열림 상태로 전환됨
**And** 다음 호출이 성공하면 정상 상태로 복구됨

#### Scenario: HALF_OPEN 상태에서의 추가 실패
**Given** Circuit Breaker가 HALF_OPEN 상태
**When** API 호출이 실패함
**Then** Circuit Breaker가 다시 OPEN 상태로 전환됨

## 엣지 케이스 테스트

### Edge Case 1: 혼합된 예외 타입
**Given** 네트워크 오류가 TimeoutException과 ConnectError로 번갈아 발생
**When** 재시트가 실행됨
**Then** 모든 예외 타입에 대해 재시트가 수행됨

### Edge Case 2: Circuit Breaker 동시 호출
**Given** Circuit Breaker가 OPEN 상태
**When** 여러 요청이 동시에 도착함
**Then** 모든 요청이 즉시 실패 응답을 받음
**And** 추가 API 호출이 발생하지 않음

### Edge Case 3: 재시트 간 API 회복
**Given** 첫 번째 요청이 실패함
**When** 두 번째 재시트 시점에 API가 회복됨
**Then** 성공 응답이 즉시 반환됨
**And** 추가 재시트는 수행되지 않음

## 성능 기준

| 항목 | 기준 | 측정 방법 |
|------|------|----------|
| 재시트 총 시간 | 30초 이내 | 타이머 측정 |
| Circuit Breaker 오버헤드 | 1ms 이내 | 프로파일링 |
| 메모리 증가 | 10MB 이내 | 메모리 프로파일러 |

## 품질 기준 (TRUST 5)

| 항목 | 기준 |
|------|------|
| Tested | 신규 코드 85%+ 커버리지 |
| Readable | 명확한 함수/변수명, 영문 주석 |
| Unified | ruff formatting 통과 |
| Secured | 타사 라이브러리 취약점 점검 |
| Trackable | Git 커밋 메시지 포맷 준수 |
