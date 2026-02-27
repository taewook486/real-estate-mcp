# Implementation Plan: SPEC-ERROR-005

## Overview

MCP 도구의 오류 응답을 표준화하여 사용자 경험을 개선하고 디버깅 효율성을 높입니다.

## Priority Milestones

### Primary Goal: Core Implementation

1. **Create `error_types.py` Module**
   - Define `ErrorType` enum for error classification
   - Create `ErrorResponse` dataclass for standardized format
   - Implement `create_error_response()` helper function
   - Add predefined error templates for common scenarios

2. **Define Error Categories**
   ```
   config_error    - Environment variable issues
   invalid_input   - User input validation failures
   network_error   - API connection problems
   api_error       - External API error responses
   parse_error     - Data parsing failures
   internal_error  - Unexpected internal errors
   ```

3. **Create Error Templates**
   - `MISSING_API_KEY`: Configuration error with setup instructions
   - `INVALID_REGION_CODE`: Input validation with example
   - `NETWORK_TIMEOUT`: Network error with retry suggestion
   - `API_RATE_LIMITED`: API error with wait suggestion
   - `XML_PARSE_FAILED`: Parse error with data format info

### Secondary Goal: Migration

1. **Update MCP Tools**
   - `tools/trade.py`: Use standardized error responses
   - `tools/rent.py`: Use standardized error responses
   - `tools/subscription.py`: Use standardized error responses
   - `tools/onbid.py`: Use standardized error responses
   - `tools/finance.py`: Use standardized error responses

2. **Update Parsers**
   - `parsers/trade.py`: Convert exceptions to error responses
   - `parsers/rent.py`: Convert exceptions to error responses
   - `parsers/onbid.py`: Convert exceptions to error responses

3. **Update Utility Modules**
   - `common_utils/docx_parser.py`: Wrap exceptions
   - `common_utils/hwp_parser.py`: Wrap exceptions

## Technical Approach

### Architecture

```
src/real_estate/mcp_server/
├── error_types.py           # NEW: Error type definitions
│   ├── enum ErrorType
│   ├── dataclass ErrorResponse
│   └── function create_error_response()
├── _helpers.py              # MODIFY: Use error_types
└── tools/
    └── *.py                 # MODIFY: Standardized errors
```

### ErrorType Enum Design

```python
from enum import Enum

class ErrorType(str, Enum):
    CONFIG = "config_error"
    INPUT = "invalid_input"
    NETWORK = "network_error"
    API = "api_error"
    PARSE = "parse_error"
    INTERNAL = "internal_error"
```

### ErrorResponse Dataclass

```python
from dataclasses import dataclass, asdict
from typing import Any

@dataclass
class ErrorResponse:
    error: str
    message: str
    suggestion: str
    details: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        result = {
            "error": self.error,
            "message": self.message,
            "suggestion": self.suggestion,
        }
        if self.details:
            result["details"] = self.details
        return result
```

### Error Templates

```python
ERROR_TEMPLATES = {
    "missing_api_key": ErrorResponse(
        error=ErrorType.CONFIG,
        message="API 키가 설정되지 않았습니다.",
        suggestion="환경 변수 DATA_GO_KR_API_KEY를 설정하세요. "
                   "키는 https://apis.data.go.kr에서 발급받을 수 있습니다.",
    ),
    "invalid_region_code": ErrorResponse(
        error=ErrorType.INPUT,
        message="잘못된 지역코드 형식입니다.",
        suggestion="5자리 숫자로 된 지역코드를 입력하세요. "
                   "예: '11440' (마포구). get_region_code 도구로 올바른 코드를 확인할 수 있습니다.",
    ),
    # ... more templates
}
```

### Migration Pattern

Before:
```python
def _check_api_key() -> dict[str, Any] | None:
    if not os.getenv("DATA_GO_KR_API_KEY", ""):
        return {
            "error": "config_error",
            "message": "Environment variable DATA_GO_KR_API_KEY is not set.",
        }
    return None
```

After:
```python
def _check_api_key() -> dict[str, Any] | None:
    if not os.getenv("DATA_GO_KR_API_KEY", ""):
        return ERROR_TEMPLATES["missing_api_key"].to_dict()
    return None
```

## Dependencies

### Existing Dependencies
- `structlog>=25.5.0` - Already installed
- No new dependencies required

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Breaking existing error handling | Maintain backward-compatible dict format |
| Missing error scenarios | Create comprehensive error template catalog |
| Message consistency | Use centralized error templates |

## File Changes Summary

| File | Action | Description |
|------|--------|-------------|
| `src/real_estate/mcp_server/error_types.py` | CREATE | Error type definitions and templates |
| `src/real_estate/mcp_server/_helpers.py` | MODIFY | Use error_types module |
| `src/real_estate/mcp_server/tools/*.py` | MODIFY | Standardize error responses |
| `src/real_estate/mcp_server/parsers/*.py` | MODIFY | Convert exceptions to responses |
| `src/real_estate/common_utils/docx_parser.py` | MODIFY | Wrap exceptions |
| `src/real_estate/common_utils/hwp_parser.py` | MODIFY | Wrap exceptions |
| `tests/test_error_types.py` | CREATE | Unit tests for error module |
