# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-02-27

### Added
- **Network Reliability**: 지수 백오프 재시도 메커니즘 및 Circuit Breaker 패턴 구현
  - 최대 3회 재시도, 초기 1초/최대 8초 지연
  - 연속 5회 실패 시 Circuit Breaker 트리거
  - 10초 초과 응답 시 연결 품질 로깅
- **Configuration Validation**: Pydantic Settings 기반 중앙 집중화 환경 변수 검증
  - AppSettings 클래스로 모든 환경 변수 관리
  - 시작 시점 검증 (Fail-fast 원칙)
  - 명확한 오류 메시지 및 설정 방법 안내
- **Standardized Error Responses**: 6가지 오류 유형 분류 및 해결 제안
  - config_error, invalid_input, network_error, api_error, parse_error, internal_error
  - 각 오류 유형별 사용자 친화적 해결 제안
- **API Response Caching**: TTL 기반 메모리 캐시로 응답 속도 개선
  - 5분 TTL, 최대 100개 항목 캐시
  - URL + 정렬된 파라미터 해시 기반 캐시 키 생성
  - 캐시 적중률 및 메모리 사용량 로깅 (선택적)
- **Input Validation**: 지역코드, 날짜 형식 사전 검증
  - 지역코드 유효성 검사 (길이, 숫자 확인)
  - 날짜 형식 YYYYMM 검증
  - 불필요한 API 호출 감소

### Changed
- 기존 환경 변수 검증 함수를 `AppSettings` 클래스로 통합
- MCP 도구 오류 응답을 표준 형식(`error_types.py`)으로 통일
- 네트워크 호출에 재시도 및 Circuit Breaker 패턴 적용
- API 오류 코드 "22" (일일 한도 초과)에 대한 특별 처리 추가

### Improved
- **Test Coverage**: 84.66% → 87.33% (+2.67%)
  - 목표 85% 초과 달성
- **Integration Tests**: 전체 워크플로우 검증
  - `tests/integration/` 디렉토리 생성
  - 12개 통합 테스트 추가
- **Parser Tests**: XML/JSON 파싱 단위 테스트
  - `tests/parsers/` 디렉토리 생성
  - 9개 파서 테스트 추가
- **Configuration Tests**: 환경 변수 검증 테스트
  - `tests/config/` 디렉토리 생성
  - 7개 설정 테스트 추가

### Technical Details
- **New Dependencies**: `cachetools>=5.5.0`
- **New Modules**:
  - `src/real_estate/cache_manager.py` - API 응답 캐싱
  - `src/real_estate/config_validator.py` - 환경 변수 검증
  - `src/real_estate/mcp_server/error_types.py` - 표준 오류 타입
- **Test Statistics**:
  - Total tests: 370개 (모두 통과)
  - New tests: 77개 추가

### Security
- API 키 환경 변수 검증 강화
- 오류 메시지에서 민감 정보 제거

## [1.0.0] - Initial Release

- 한국 부동산 데이터 조회 MCP 서버 초기 릴리스
- 아파트, 오피스텔, 연립다세대, 단독주택, 상업용건물 매매/전월세 조회
- 아파트 청약 정보 조회
- 온비드 공매물건 조회
