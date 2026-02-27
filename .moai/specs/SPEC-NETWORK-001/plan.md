# SPEC-NETWORK-001: 구현 계획

## 개요

네트워크 연결 신뢰성을 높이기 위한 재시도 메커니즘과 Circuit Breaker 패턴을 구현합니다.

## 기술 스택

| 항목 | 기술 | 버전 |
|------|------|------|
| 언어 | Python | 3.12+ |
| HTTP 클라이언트 | httpx | 기존 사용 |
| 재시트 라이브러리 | tenacity | ^9.0.0 |

## 작업 분해

### Phase 1: 재시도 메커니즘 구현

**파일**: `src/real_estate/mcp_server/_helpers.py`

1. **tenacity 라이브러리 추가**
   ```bash
   uv add tenacity
   ```

2. **재시도 데코레이터 구현**
   - 초기 지연: 1초
   - 백오프 배수: 2
   - 최대 지연: 8초
   - 최대 시도: 3회
   - 재시트 가능 예외: `httpx.TimeoutException`, `httpx.ConnectError`, `httpx.RemoteProtocolError`

3. **`_fetch_xml` 함수 수정**
   - `@retry` 데코레이터 추가
   - 재시트 로깅 추가

### Phase 2: Circuit Breaker 구현

1. **CircuitBreaker 클래스 생성**
   - 상태: CLOSED, OPEN, HALF_OPEN
   - 실패 임계값: 5회
   - 복구 대기 시간: 30초

2. **API 호출 래핑**
   - Circuit Breaker 상태 확인
   - OPEN 시 즉시 실패 반환
   - HALF_OPEN 시 시도 호출

### Phase 3: 테스트 작성

**파일**: `tests/mcp_server/test_network_retry.py`

1. **재시트 테스트**
   - 일시적 네트워크 오류 복구 시나리오
   - 최대 재시트 초과 시나리오

2. **Circuit Breaker 테스트**
   - 연속 실패 시 OPEN 전환
   - 복구 후 CLOSED 전환
   - HALF_OPEN 상태 동작

### Phase 4: 통합 테스트

1. **기존 테스트와의 호환성 확인**
2. **성능 영향 측정**

## 구현 제약사항

1. **호환성**: 기존 `_fetch_xml` 함수 시그니처 유지
2. **성능**: 재시트로 인한 총 요청 시간 30초 초과 금지
3. **로깅**: 모든 재시트와 상태 변화를 로그에 기록

## 롤백 계획

- 구현 전 `_helpers.py` 백업
- 문제 발생 시 즉시 롤백 가능
- 기능 플래그로 활성화/비활성화 가능 고려

## 검증 기준

- [ ] tenacity 라이브러리 추가 완료
- [ ] 재시트 데코레이터 구현 완료
- [ ] Circuit Breaker 클래스 구현 완료
- [ ] 단위 테스트 통과 (최소 80% 커버리지)
- [ ] 기존 135개 테스트 통과
- [ ] 성능 기준 충족 (30초 이내)
