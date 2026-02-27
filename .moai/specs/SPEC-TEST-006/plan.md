# Implementation Plan: SPEC-TEST-006

## Overview

테스트 커버리지를 85% 이상으로 확장하고, 통합 테스트와 파서 테스트를 체계적으로 추가합니다.

## Priority Milestones

### Primary Goal: Test Structure Expansion

1. **Create Test Directory Structure**
   ```
   tests/
   ├── integration/          # NEW: End-to-end workflow tests
   │   ├── __init__.py
   │   ├── conftest.py
   │   ├── test_trade_workflow.py
   │   ├── test_rent_workflow.py
   │   └── test_onbid_workflow.py
   ├── parsers/              # NEW: Parser unit tests
   │   ├── __init__.py
   │   ├── test_trade_parser.py
   │   ├── test_rent_parser.py
   │   └── test_onbid_parser.py
   ├── config/               # NEW: Configuration tests
   │   ├── __init__.py
   │   └── test_config_validator.py
   └── ...existing tests
   ```

2. **Integration Tests**
   - `test_trade_workflow.py`: Full trade API workflow
   - `test_rent_workflow.py`: Full rent API workflow
   - `test_onbid_workflow.py`: Onbid API workflow

3. **Parser Tests**
   - `test_trade_parser.py`: Trade XML parsing
   - `test_rent_parser.py`: Rent XML parsing
   - `test_onbid_parser.py`: Onbid XML/JSON parsing

4. **Configuration Tests**
   - `test_config_validator.py`: AppSettings validation

### Secondary Goal: Coverage Improvement

1. **Identify Coverage Gaps**
   - Run coverage report to find uncovered lines
   - Focus on error handling paths
   - Add edge case tests

2. **Improve Existing Tests**
   - Add missing test cases for error paths
   - Improve test assertions
   - Add parametrized tests for variations

## Technical Approach

### Integration Test Pattern

```python
# tests/integration/test_trade_workflow.py
import pytest
import respx
from httpx import Response

@pytest.mark.asyncio
async def test_apartment_trade_workflow():
    """Test complete apartment trade data retrieval workflow."""
    # 1. Mock API response
    with respx.mock:
        respx.get("https://apis.data.go.kr/...").mock(
            return_value=Response(200, text=SAMPLE_XML_RESPONSE)
        )

        # 2. Call MCP tool
        result = await get_apartment_trade(
            region_code="11440",
            year_month="202501",
            num_of_rows=100
        )

        # 3. Verify response structure
        assert "items" in result
        assert "summary" in result
        assert "total_count" in result

        # 4. Verify data quality
        assert len(result["items"]) > 0
        assert result["summary"]["median_price_10k"] > 0
```

### Parser Test Pattern

```python
# tests/parsers/test_trade_parser.py
import pytest

def test_parse_apartment_trade_xml():
    """Test apartment trade XML parsing."""
    xml_text = load_sample_xml("sample_apartment_trade.xml")

    items, error_code = _parse_apartment_trade_xml(xml_text)

    assert error_code is None
    assert len(items) > 0
    assert items[0]["region_code"] == "11440"
    assert items[0]["price_10k"] > 0

def test_parse_trade_xml_with_error_code():
    """Test XML parsing with API error code."""
    xml_text = load_sample_xml("sample_error_03.xml")

    items, error_code = _parse_apartment_trade_xml(xml_text)

    assert error_code == "03"
    assert items == []
```

### Configuration Test Pattern

```python
# tests/config/test_config_validator.py
import pytest
from unittest.mock import patch

def test_app_settings_with_valid_config():
    """Test AppSettings with valid configuration."""
    with patch.dict(os.environ, {"DATA_GO_KR_API_KEY": "test-key"}):
        settings = AppSettings()
        assert settings.data_go_kr_api_key == "test-key"

def test_app_settings_missing_required():
    """Test AppSettings with missing required field."""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError) as exc_info:
            AppSettings()
        assert "DATA_GO_KR_API_KEY" in str(exc_info.value)
```

### Sample Test Data

```
tests/fixtures/
├── xml/
│   ├── sample_apartment_trade.xml
│   ├── sample_apartment_rent.xml
│   ├── sample_onbid_response.xml
│   └── sample_error_response.xml
└── json/
    ├── sample_odcloud_response.json
    └── sample_error_response.json
```

## Dependencies

### Existing Dependencies
- pytest>=8.0.0
- pytest-asyncio>=0.24.0
- pytest-cov>=6.0.0
- respx>=0.22.0

### No New Dependencies Required

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Flaky tests due to timing | Use deterministic mocking |
| Sample data becoming stale | Version control sample files |
| Long test execution time | Use pytest-xdist for parallel execution |

## File Changes Summary

| File | Action | Description |
|------|--------|-------------|
| `tests/integration/__init__.py` | CREATE | Integration test package |
| `tests/integration/conftest.py` | CREATE | Shared fixtures |
| `tests/integration/test_trade_workflow.py` | CREATE | Trade workflow tests |
| `tests/integration/test_rent_workflow.py` | CREATE | Rent workflow tests |
| `tests/integration/test_onbid_workflow.py` | CREATE | Onbid workflow tests |
| `tests/parsers/__init__.py` | CREATE | Parser test package |
| `tests/parsers/test_trade_parser.py` | CREATE | Trade parser tests |
| `tests/parsers/test_rent_parser.py` | CREATE | Rent parser tests |
| `tests/parsers/test_onbid_parser.py` | CREATE | Onbid parser tests |
| `tests/config/__init__.py` | CREATE | Config test package |
| `tests/config/test_config_validator.py` | CREATE | Config validation tests |
| `tests/fixtures/xml/*.xml` | CREATE | Sample XML files |
| `tests/fixtures/json/*.json` | CREATE | Sample JSON files |
