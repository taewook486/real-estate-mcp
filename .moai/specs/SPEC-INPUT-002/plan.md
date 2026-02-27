# SPEC-INPUT-002: 구현 계획

## 개요

입력값 검증을 강화하고 사용자 친화적 에러 메시지를 제공합니다.

## 기술 스택

| 항목 | 기술 | 버전 |
|------|------|------|
| 언어 | Python | 3.12+ |
| 검증 | 내장 함수 | - |

## 작업 분해

### Phase 1: 검증 함수 구현

**파일**: `src/real_estate/mcp_server/_validators.py` (신규)

1. **`validate_lawd_code(code: str) -> ValidationResult`**
   - 5자리 숫자 형식 검증
   - region_codes.txt 기반 실제 존재 여부 확인

2. **`validate_deal_ymd(ymd: str) -> ValidationResult`**
   - YYYYMM 형식 검증 (정규표현식)
   - 200601 ~ 현재월 범위 검증

3. **`validate_pagination(page_no: int, num_of_rows: int) -> ValidationResult`**
   - 1 이상 정수 검증
   - 합리적 상한 (1000) 검증

### Phase 2: 에러 메시지 개선

**파일**: `src/real_estate/mcp_server/_helpers.py`

1. **API 에러 코드 매핑 확장**
   ```python
   _USER_FRIENDLY_ERRORS: dict[str, str] = {
       "03": "조회된 매매 내역이 없습니다.",
       "10": "API 요청 파라미터가 잘못되었습니다.",
       "22": "일일 조회 한도를 초과했습니다. 내일 00:00에 초기화됩니다.",
       "30": "등록되지 않은 API 키입니다.",
       "31": "API 키가 만료되었습니다.",
       # ... 기존 메시지
   }
   ```

### Phase 3: Tool 함수 수정

**파일**: `src/real_estate/mcp_server/tools/trade.py`, `rent.py`

1. **검증 호출 추가**
   - 각 tool 함수 시작부분에 검증 호출
   - 검증 실패 시 조기 반환

### Phase 4: 테스트 작성

**파일**: `tests/mcp_server/test_validators.py`

1. **지역코드 검증 테스트**
2. **날짜 검증 테스트**
3. **페이지 검증 테스트**
4. **에러 메시지 검증 테스트

## 구현 제약사항

1. **성능**: 검증은 10ms 이내에 완료
2. **호환성**: 기존 API 인터페이스 유지
3. **언어**: 오류 메시지는 한국어

## 검증 기준

- [ ] 검증 함수 구현 완료
- [ ] 에러 메시지 개선 완료
- [ ] Tool 함수에 검증 통합 완료
- [ ] 단위 테스트 통과 (최소 85% 커버리지)
- [ ] 기존 135개 테스트 통과
