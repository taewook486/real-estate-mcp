# Implementation Plan: SPEC-CONFIG-004

## Overview

환경 변수 설정 검증 레이어를 구현하여 분산된 검증 로직을 중앙 집중화하고 Fail-fast 원칙을 적용합니다.

## Priority Milestones

### Primary Goal: Core Implementation

1. **Create `config_validator.py` Module**
   - Define `AppSettings` class using Pydantic Settings
   - Implement field validators for API keys
   - Add clear error messages with setup instructions
   - Support required vs optional configuration

2. **Integrate with Existing Code**
   - Update `_helpers.py` to use centralized settings
   - Refactor `_check_api_key()` to use `AppSettings`
   - Refactor `_check_onbid_api_key()` to use `AppSettings`
   - Refactor `_check_odcloud_key()` to use `AppSettings`

3. **Startup Validation Hook**
   - Validate settings on module import
   - Provide clear error output for missing configuration
   - Log configuration status on startup

### Secondary Goal: Testing & Documentation

1. **Unit Tests**
   - Test `AppSettings` with valid configuration
   - Test `AppSettings` with missing required fields
   - Test fallback behavior for optional fields

2. **Integration Tests**
   - Test MCP tools with mocked settings
   - Test error handling with invalid configuration

## Technical Approach

### Architecture

```
src/real_estate/
├── config_validator.py      # NEW: Centralized settings
│   └── class AppSettings    # Pydantic Settings class
└── mcp_server/
    └── _helpers.py          # MODIFIED: Use AppSettings
```

### AppSettings Class Design

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Required API keys
    data_go_kr_api_key: str  # Required

    # Optional API keys with fallback logic
    onbid_api_key: str | None = None
    odcloud_api_key: str | None = None
    odcloud_service_key: str | None = None

    def validate_data_go_kr(self) -> None:
        """Validate DATA_GO_KR_API_KEY is set and non-empty."""
        if not self.data_go_kr_api_key:
            raise ValueError(
                "DATA_GO_KR_API_KEY is required. "
                "Get your key from https://apis.data.go.kr"
            )

    def get_onbid_key(self) -> str:
        """Get Onbid API key with fallback to DATA_GO_KR_API_KEY."""
        return self.onbid_api_key or self.data_go_kr_api_key

    def get_odcloud_auth(self) -> tuple[str, str]:
        """Get odcloud authentication mode and key."""
        # Priority: ODCLOUD_API_KEY > ODCLOUD_SERVICE_KEY > DATA_GO_KR_API_KEY
        ...
```

### Migration Strategy

1. Create new `config_validator.py` module
2. Add unit tests for `AppSettings`
3. Update `_helpers.py` to import and use `AppSettings`
4. Deprecate individual `_check_*_api_key()` functions
5. Update all tool files to use centralized settings

## Dependencies

### Existing Dependencies
- `pydantic-settings>=2.0.0` - Already installed

### No New Dependencies Required

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Breaking existing behavior | Maintain backward-compatible function signatures |
| Circular imports | Use lazy import pattern in `_helpers.py` |
| Missing env file | Provide clear error message with setup instructions |

## File Changes Summary

| File | Action | Description |
|------|--------|-------------|
| `src/real_estate/config_validator.py` | CREATE | New centralized settings module |
| `src/real_estate/mcp_server/_helpers.py` | MODIFY | Use AppSettings for validation |
| `tests/test_config_validator.py` | CREATE | Unit tests for settings |
