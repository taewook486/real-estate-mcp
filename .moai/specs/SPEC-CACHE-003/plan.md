# SPEC-CACHE-003: 구현 계획

## 개요

지역코드 캐싱과 구조화 로깅을 도입하여 성능과 운영 효율성을 개선합니다.

## 기술 스택

| 항목 | 기술 | 버전 |
|------|------|------|
| 언어 | Python | 3.12+ |
| 로깅 | structlog | ^24.0.0 |

## 작업 분해

### Phase 1: 지역코드 캐싱

**파일**: `src/real_estate/mcp_server/_region.py`

1. **캐싱 방식 선택**
   - `functools.lru_cache` 사용 (권장)
   - 또는 모듈 레벨 전역 변수

2. **`_load_region_rows` 수정**
   - 캐싱 데코레이터 또는 캐시 확인 로직 추가

3. **캐시 무효화 (optional)**
   - 테스트용 캐시 클리어 함수

### Phase 2: 구조화 로깅

**파일**: `src/real_estate/mcp_server/_logging.py` (신규)

1. **structlog 설정**
   ```python
   import structlog

   structlog.configure(
       processors=[
           structlog.processors.TimeStamper(fmt="iso"),
           structlog.processors.JSONRenderer()
       ],
       logger_factory=structlog.PrintLoggerFactory(),
   )
   ```

2. **로그 유틸리티**
   - `get_logger(tool_name: str)`
   - `log_request(tool_name, params, duration, status)`
   - `log_error(tool_name, error)`

### Phase 3: 로깅 통합

**파일**: `src/real_estate/mcp_server/_helpers.py`, `tools/*.py`

1. **기존 logging을 structlog로 교체**
2. **요청 시작/종료 로그 추가**
3. **오류 발생 시 구조화 로그 추가**

### Phase 4: 테스트 작성

**파일**: `tests/mcp_server/test_caching.py`, `test_logging.py`

1. **캐싱 동작 테스트**
2. **로그 형식 테스트**
3. **메모리 사용량 테스트**

## 구현 제약사항

1. **성능**: 캐시 적재 100ms 이내
2. **메모리**: 20MB 이내 증가
3. **호환성**: 기존 로그와 병행

## 검증 기준

- [ ] structlog 라이브러리 추가 완료
- [ ] 지역코드 캐싱 구현 완료
- [ ] 구조화 로거 구현 완료
- [ ] 로깅 통합 완료
- [ ] 단위 테스트 통과
- [ ] 기존 135개 테스트 통과
