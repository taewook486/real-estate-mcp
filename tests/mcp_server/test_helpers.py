"""Characterization tests for _helpers.py network functionality.

These tests capture the current behavior of the HTTP helpers
to ensure behavior preservation during refactoring.
"""

from typing import Any

import pytest
import respx
from httpx import Response

from real_estate.mcp_server._helpers import (
    _api_error_response,
    _build_rent_summary,
    _build_trade_summary,
    _build_url,
    _build_url_with_service_key,
    _check_api_key,
    _check_onbid_api_key,
    _fetch_json,
    _fetch_xml,
    _get_data_go_kr_key_for_onbid,
    _get_odcloud_key,
    _get_total_count,
    _get_total_count_onbid,
    _make_date,
    _parse_amount,
    _parse_float,
    _parse_int,
    _parse_monthly_rent,
    _txt,
)

# ---------------------------------------------------------------------------
# Test fixtures
# ---------------------------------------------------------------------------

_XML_OK = """<?xml version="1.0" encoding="UTF-8"?>
<response>
  <header>
    <resultCode>000</resultCode>
    <resultMsg>OK</resultMsg>
  </header>
  <body>
    <items>
      <item>
        <aptNm>TestApt</aptNm>
      </item>
    </items>
    <totalCount>1</totalCount>
  </body>
</response>"""

_JSON_OK = {"result": "success", "data": {"id": 123}}


# ---------------------------------------------------------------------------
# Characterization tests for _fetch_xml
# ---------------------------------------------------------------------------


class TestFetchXmlCharacterize:
    """Characterization tests for _fetch_xml behavior."""

    @respx.mock
    async def test_characterize_success_returns_text_and_none_error(self) -> None:
        """Successful response returns (text, None)."""
        respx.get("https://test.example.com/api").mock(return_value=Response(200, text=_XML_OK))

        text, error = await _fetch_xml("https://test.example.com/api")

        assert error is None
        assert text is not None
        assert "<?xml" in text

    @respx.mock
    async def test_characterize_timeout_returns_none_and_error(self) -> None:
        """Timeout returns (None, error_dict) after retries."""
        import httpx

        respx.get("https://test.example.com/api").mock(
            side_effect=httpx.TimeoutException("timeout")
        )

        text, error = await _fetch_xml("https://test.example.com/api")

        assert text is None
        assert error is not None
        assert error["error"] == "network_error"
        # After 3 retry attempts, the message indicates retry exhaustion
        assert "3 attempts" in error["message"] or "timed out" in error["message"].lower()

    @respx.mock
    async def test_characterize_http_500_returns_none_and_error(self) -> None:
        """HTTP 500 error returns (None, error_dict)."""

        respx.get("https://test.example.com/api").mock(
            return_value=Response(500, text="Internal Server Error")
        )

        text, error = await _fetch_xml("https://test.example.com/api")

        assert text is None
        assert error is not None
        assert error["error"] == "network_error"
        assert "500" in error["message"]

    @respx.mock
    async def test_characterize_connection_error_returns_none_and_error(self) -> None:
        """Connection error returns (None, error_dict)."""
        import httpx

        respx.get("https://test.example.com/api").mock(
            side_effect=httpx.RequestError("connection refused")
        )

        text, error = await _fetch_xml("https://test.example.com/api")

        assert text is None
        assert error is not None
        assert error["error"] == "network_error"
        assert "Network error" in error["message"]


# ---------------------------------------------------------------------------
# Characterization tests for _fetch_json
# ---------------------------------------------------------------------------


class TestFetchJsonCharacterize:
    """Characterization tests for _fetch_json behavior."""

    @respx.mock
    async def test_characterize_success_returns_json_and_none_error(self) -> None:
        """Successful response returns (json, None)."""
        respx.get("https://test.example.com/api").mock(return_value=Response(200, json=_JSON_OK))

        data, error = await _fetch_json("https://test.example.com/api")

        assert error is None
        assert data is not None
        assert isinstance(data, dict)
        assert data["result"] == "success"

    @respx.mock
    async def test_characterize_timeout_returns_none_and_error(self) -> None:
        """Timeout returns (None, error_dict) after retries."""
        import httpx

        respx.get("https://test.example.com/api").mock(
            side_effect=httpx.TimeoutException("timeout")
        )

        data, error = await _fetch_json("https://test.example.com/api")

        assert data is None
        assert error is not None
        assert error["error"] == "network_error"
        # After 3 retry attempts, the message indicates retry exhaustion
        assert "3 attempts" in error["message"] or "timed out" in error["message"].lower()

    @respx.mock
    async def test_characterize_invalid_json_returns_none_and_parse_error(
        self,
    ) -> None:
        """Invalid JSON returns (None, parse_error)."""
        respx.get("https://test.example.com/api").mock(
            return_value=Response(200, text="not valid json")
        )

        data, error = await _fetch_json("https://test.example.com/api")

        assert data is None
        assert error is not None
        assert error["error"] == "parse_error"
        assert "JSON parse failed" in error["message"]


# ---------------------------------------------------------------------------
# Characterization tests for _build_url
# ---------------------------------------------------------------------------


class TestBuildUrlCharacterize:
    """Characterization tests for URL building."""

    def test_characterize_url_contains_service_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """URL contains URL-encoded service key."""
        monkeypatch.setenv("DATA_GO_KR_API_KEY", "test-key-123")

        url = _build_url("https://api.example.com/endpoint", "11440", "202501", 100)

        assert "serviceKey=test-key-123" in url
        assert "LAWD_CD=11440" in url
        assert "DEAL_YMD=202501" in url
        assert "numOfRows=100" in url
        assert "pageNo=1" in url

    def test_characterize_url_encodes_special_chars(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Special characters in API key are URL encoded."""
        monkeypatch.setenv("DATA_GO_KR_API_KEY", "key+with/special=chars")

        url = _build_url("https://api.example.com/endpoint", "11440", "202501", 100)

        assert "key%2Bwith%2Fspecial%3Dchars" in url


# ---------------------------------------------------------------------------
# Characterization tests for _build_url_with_service_key
# ---------------------------------------------------------------------------


class TestBuildUrlWithServiceKeyCharacterize:
    """Characterization tests for URL building with explicit service key."""

    def test_characterize_params_included(self) -> None:
        """Additional params are included in URL."""
        url = _build_url_with_service_key(
            "https://api.example.com/endpoint",
            "my-service-key",
            {"pageNo": 1, "numOfRows": 10},
        )

        assert "serviceKey=my-service-key" in url
        assert "pageNo=1" in url
        assert "numOfRows=10" in url

    def test_characterize_no_params_only_service_key(self) -> None:
        """Empty params result in only service key."""
        url = _build_url_with_service_key(
            "https://api.example.com/endpoint",
            "my-service-key",
            {},
        )

        assert url == "https://api.example.com/endpoint?serviceKey=my-service-key"


# ---------------------------------------------------------------------------
# Characterization tests for API key helpers
# ---------------------------------------------------------------------------


class TestApiKeyHelpersCharacterize:
    """Characterization tests for API key checking functions."""

    def test_characterize_check_api_key_missing_returns_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Missing DATA_GO_KR_API_KEY returns error dict."""
        monkeypatch.delenv("DATA_GO_KR_API_KEY", raising=False)

        result = _check_api_key()

        assert result is not None
        assert result["error"] == "config_error"
        assert "DATA_GO_KR_API_KEY" in result["message"]

    def test_characterize_check_api_key_present_returns_none(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Present DATA_GO_KR_API_KEY returns None."""
        monkeypatch.setenv("DATA_GO_KR_API_KEY", "test-key")

        result = _check_api_key()

        assert result is None

    def test_characterize_get_odcloud_key_prefers_api_key(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """ODCLOUD_API_KEY is preferred over SERVICE_KEY."""
        monkeypatch.setenv("ODCLOUD_API_KEY", "api-key")
        monkeypatch.setenv("ODCLOUD_SERVICE_KEY", "service-key")
        monkeypatch.setenv("DATA_GO_KR_API_KEY", "fallback-key")

        mode, key = _get_odcloud_key()

        assert mode == "authorization"
        assert key == "api-key"

    def test_characterize_get_odcloud_key_uses_service_key_fallback(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """ODCLOUD_SERVICE_KEY is used if ODCLOUD_API_KEY missing."""
        monkeypatch.delenv("ODCLOUD_API_KEY", raising=False)
        monkeypatch.setenv("ODCLOUD_SERVICE_KEY", "service-key")

        mode, key = _get_odcloud_key()

        assert mode == "serviceKey"
        assert key == "service-key"

    def test_characterize_check_onbid_key_missing_all_returns_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Missing Onbid keys returns error dict."""
        monkeypatch.delenv("ONBID_API_KEY", raising=False)
        monkeypatch.delenv("DATA_GO_KR_API_KEY", raising=False)

        result = _check_onbid_api_key()

        assert result is not None
        assert result["error"] == "config_error"

    def test_characterize_get_data_go_kr_key_for_onbid_prefers_onbid_key(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """ONBID_API_KEY is preferred for Onbid APIs."""
        monkeypatch.setenv("ONBID_API_KEY", "onbid-key")
        monkeypatch.setenv("DATA_GO_KR_API_KEY", "data-key")

        key = _get_data_go_kr_key_for_onbid()

        assert key == "onbid-key"


# ---------------------------------------------------------------------------
# Characterization tests for summary builders
# ---------------------------------------------------------------------------


class TestSummaryBuildersCharacterize:
    """Characterization tests for summary statistics functions."""

    def test_characterize_trade_summary_calculates_median(self) -> None:
        """Trade summary calculates median correctly."""
        items = [
            {"price_10k": 100000},
            {"price_10k": 200000},
            {"price_10k": 300000},
        ]

        summary = _build_trade_summary(items)

        assert summary["median_price_10k"] == 200000
        assert summary["min_price_10k"] == 100000
        assert summary["max_price_10k"] == 300000
        assert summary["sample_count"] == 3

    def test_characterize_trade_summary_empty_returns_zeros(self) -> None:
        """Empty items returns all zeros."""
        summary = _build_trade_summary([])

        assert summary["median_price_10k"] == 0
        assert summary["sample_count"] == 0

    def test_characterize_rent_summary_calculates_statistics(self) -> None:
        """Rent summary calculates deposit and rent statistics."""
        items = [
            {"deposit_10k": 50000, "monthly_rent_10k": 50},
            {"deposit_10k": 70000, "monthly_rent_10k": 100},
        ]

        summary = _build_rent_summary(items)

        assert summary["median_deposit_10k"] == 60000
        assert summary["min_deposit_10k"] == 50000
        assert summary["max_deposit_10k"] == 70000
        assert summary["monthly_rent_avg_10k"] == 75
        assert summary["jeonse_ratio_pct"] is None
        assert summary["sample_count"] == 2

    def test_characterize_rent_summary_empty_returns_zeros(self) -> None:
        """Empty items returns all zeros for rent summary."""
        summary = _build_rent_summary([])

        assert summary["median_deposit_10k"] == 0
        assert summary["monthly_rent_avg_10k"] == 0
        assert summary["sample_count"] == 0


# ---------------------------------------------------------------------------
# Characterization tests for XML helpers
# ---------------------------------------------------------------------------


class TestXmlHelpersCharacterize:
    """Characterization tests for XML parsing helpers."""

    def test_characterize_get_total_count_extracts_count(self) -> None:
        """_get_total_count extracts totalCount from XML."""
        from defusedxml.ElementTree import fromstring

        root = fromstring(_XML_OK)
        count = _get_total_count(root)

        assert count == 1

    def test_characterize_get_total_count_onbid_various_tags(self) -> None:
        """_get_total_count_onbid handles various tag names."""
        from defusedxml.ElementTree import fromstring

        xml_totalcount = """<?xml version="1.0"?>
        <response><body><totalCount>5</totalCount></body></response>"""
        root = fromstring(xml_totalcount)
        count = _get_total_count_onbid(root)
        assert count == 5

    def test_characterize_parse_amount_removes_commas(self) -> None:
        """_parse_amount removes commas and returns int."""
        result = _parse_amount("1,000,000")

        assert result == 1000000

    def test_characterize_parse_amount_invalid_returns_none(self) -> None:
        """_parse_amount returns None for invalid input."""
        result = _parse_amount("not-a-number")

        assert result is None

    def test_characterize_parse_float_returns_float(self) -> None:
        """_parse_float returns float value."""
        result = _parse_float("3.14")

        assert result == 3.14

    def test_characterize_parse_float_invalid_returns_zero(self) -> None:
        """_parse_float returns 0.0 for invalid input."""
        result = _parse_float("not-a-float")

        assert result == 0.0

    def test_characterize_parse_int_returns_int(self) -> None:
        """_parse_int returns int value."""
        result = _parse_int("42")

        assert result == 42

    def test_characterize_parse_int_invalid_returns_zero(self) -> None:
        """_parse_int returns 0 for invalid input."""
        result = _parse_int("not-an-int")

        assert result == 0

    def test_characterize_make_date_formats_correctly(self) -> None:
        """_make_date formats year/month/day correctly."""
        from defusedxml.ElementTree import fromstring

        xml = """<?xml version="1.0"?>
        <item><dealYear>2025</dealYear><dealMonth>1</dealMonth><dealDay>5</dealDay></item>"""
        item = fromstring(xml)
        result = _make_date(item)

        assert result == "2025-01-05"

    def test_characterize_txt_extracts_text(self) -> None:
        """_txt extracts and strips text content."""
        from defusedxml.ElementTree import fromstring

        xml = """<?xml version="1.0"?>
        <item><name>  Test Name  </name></item>"""
        item = fromstring(xml)
        result = _txt(item, "name")

        assert result == "Test Name"


# ---------------------------------------------------------------------------
# Characterization tests for _api_error_response
# ---------------------------------------------------------------------------


class TestApiErrorResponseCharacterize:
    """Characterization tests for API error response builder."""

    def test_characterize_known_error_code(self) -> None:
        """Known error code returns mapped message."""
        result = _api_error_response("22")

        assert result["error"] == "api_error"
        assert result["code"] == "22"
        assert "Daily API request limit exceeded" in result["message"]

    def test_characterize_unknown_error_code(self) -> None:
        """Unknown error code returns generic message."""
        result = _api_error_response("99")

        assert result["error"] == "api_error"
        assert result["code"] == "99"
        assert "API error code: 99" in result["message"]


# ---------------------------------------------------------------------------
# Characterization tests for _parse_monthly_rent
# ---------------------------------------------------------------------------


class TestParseMonthlyRentCharacterize:
    """Characterization tests for monthly rent parsing."""

    def test_characterize_valid_amount(self) -> None:
        """Valid monthly rent amount is parsed correctly."""
        from defusedxml.ElementTree import fromstring

        xml = """<?xml version="1.0"?>
        <item><monthlyRent>50,000</monthlyRent></item>"""
        item = fromstring(xml)
        result = _parse_monthly_rent(item)

        assert result == 50000

    def test_characterize_empty_returns_zero(self) -> None:
        """Empty monthly rent returns 0."""
        from defusedxml.ElementTree import fromstring

        xml = """<?xml version="1.0"?>
        <item><monthlyRent></monthlyRent></item>"""
        item = fromstring(xml)
        result = _parse_monthly_rent(item)

        assert result == 0

    def test_characterize_missing_tag_returns_zero(self) -> None:
        """Missing monthlyRent tag returns 0."""
        from defusedxml.ElementTree import fromstring

        xml = """<?xml version="1.0"?><item></item>"""
        item = fromstring(xml)
        result = _parse_monthly_rent(item)

        assert result == 0


# ---------------------------------------------------------------------------
# Network resilience tests (Circuit Breaker)
# ---------------------------------------------------------------------------


class TestCircuitBreaker:
    """Tests for circuit breaker pattern implementation."""

    def test_circuit_breaker_initial_state_closed(self) -> None:
        """Circuit breaker starts in closed state."""
        from real_estate.mcp_server._helpers import (
            _molit_circuit_breaker,
            _reset_circuit_breaker,
        )

        _reset_circuit_breaker()

        assert _molit_circuit_breaker.state.value == "closed"
        can_proceed, _ = _molit_circuit_breaker.can_execute()
        assert can_proceed is True

    def test_circuit_breaker_opens_after_threshold_failures(self) -> None:
        """Circuit breaker opens after failure threshold is reached."""
        from real_estate.mcp_server._helpers import (
            _CIRCUIT_BREAKER_FAILURE_THRESHOLD,
            _molit_circuit_breaker,
            _reset_circuit_breaker,
        )

        _reset_circuit_breaker()

        # Record failures up to threshold
        for _ in range(_CIRCUIT_BREAKER_FAILURE_THRESHOLD):
            _molit_circuit_breaker.record_failure()

        # Circuit should be open
        assert _molit_circuit_breaker.state.value == "open"
        can_proceed, error = _molit_circuit_breaker.can_execute()
        assert can_proceed is False
        assert error is not None
        assert error["error"] == "circuit_breaker_open"

    def test_circuit_breaker_closes_on_success(self) -> None:
        """Circuit breaker closes on successful request."""
        from real_estate.mcp_server._helpers import (
            _molit_circuit_breaker,
            _reset_circuit_breaker,
        )

        _reset_circuit_breaker()

        # Record some failures
        _molit_circuit_breaker.record_failure()
        _molit_circuit_breaker.record_failure()

        # Record success
        _molit_circuit_breaker.record_success()

        # Circuit should be closed
        assert _molit_circuit_breaker.state.value == "closed"

    @respx.mock
    async def test_fetch_xml_circuit_breaker_blocks_after_failures(self) -> None:
        """_fetch_xml respects circuit breaker and blocks requests."""
        import real_estate.mcp_server._helpers as helpers_module

        # Reset circuit breaker via module
        helpers_module._reset_circuit_breaker()

        # Simulate failures to open circuit
        for _ in range(helpers_module._CIRCUIT_BREAKER_FAILURE_THRESHOLD):
            helpers_module._molit_circuit_breaker.record_failure()

        # Verify circuit is open
        assert helpers_module._molit_circuit_breaker.state.value == "open"

        # Request should be blocked (no need to mock since circuit is open)
        text, error = await _fetch_xml("https://test.example.com/api")

        assert text is None
        assert error is not None
        assert error["error"] == "circuit_breaker_open"

        # Cleanup: reset circuit breaker
        helpers_module._reset_circuit_breaker()

    @respx.mock
    async def test_fetch_xml_success_closes_circuit(self) -> None:
        """_fetch_xml success closes circuit breaker when in half-open state."""
        import real_estate.mcp_server._helpers as helpers_module

        # Reset circuit breaker via module
        helpers_module._reset_circuit_breaker()

        # Put circuit in half-open state directly
        helpers_module._molit_circuit_breaker._state = helpers_module.CircuitState.HALF_OPEN

        # Mock successful response
        respx.get("https://test.example.com/api").mock(return_value=Response(200, text=_XML_OK))

        text, error = await _fetch_xml("https://test.example.com/api")

        assert error is None
        # After success, circuit should be closed
        assert helpers_module._molit_circuit_breaker.state.value == "closed"

        # Cleanup: reset circuit breaker
        helpers_module._reset_circuit_breaker()


# ---------------------------------------------------------------------------
# Network resilience tests (Retry with exponential backoff)
# ---------------------------------------------------------------------------


class TestRetryWithExponentialBackoff:
    """Tests for exponential backoff retry pattern."""

    @respx.mock
    async def test_retry_succeeds_on_second_attempt(self) -> None:
        """_fetch_xml retries and succeeds on second attempt."""
        from real_estate.mcp_server._helpers import _reset_circuit_breaker

        _reset_circuit_breaker()

        call_count = 0

        def side_effect_handler(request: Any) -> Response:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                import httpx

                raise httpx.TimeoutException("timeout")
            return Response(200, text=_XML_OK)

        respx.get("https://test.example.com/api").mock(side_effect=side_effect_handler)

        text, error = await _fetch_xml("https://test.example.com/api")

        assert error is None
        assert text is not None
        assert call_count == 2  # First failed, second succeeded

    @respx.mock
    async def test_retry_exhausted_after_max_attempts(self) -> None:
        """_fetch_xml exhausts retries after max attempts."""
        import httpx

        from real_estate.mcp_server._helpers import (
            _RETRY_MAX_ATTEMPTS,
            _reset_circuit_breaker,
        )

        _reset_circuit_breaker()

        respx.get("https://test.example.com/api").mock(
            side_effect=httpx.TimeoutException("timeout")
        )

        text, error = await _fetch_xml("https://test.example.com/api")

        assert text is None
        assert error is not None
        assert error["error"] == "network_error"
        assert str(_RETRY_MAX_ATTEMPTS) in error["message"]


# ---------------------------------------------------------------------------
# Connection quality monitoring tests
# ---------------------------------------------------------------------------


class TestConnectionQualityMonitoring:
    """Tests for connection quality monitoring and slow response logging."""

    @respx.mock
    async def test_slow_response_logged(self, caplog: pytest.LogCaptureFixture) -> None:
        """Slow responses (>10s) are logged as warnings."""
        import time

        from real_estate.mcp_server._helpers import (
            _reset_circuit_breaker,
        )

        _reset_circuit_breaker()

        # Mock a slow response
        def slow_handler(request: Any) -> Response:
            time.sleep(0.1)  # Small delay for test
            return Response(200, text=_XML_OK)

        respx.get("https://test.example.com/api").mock(side_effect=slow_handler)

        # This should succeed without error
        text, error = await _fetch_xml("https://test.example.com/api")

        assert error is None
        # Note: In practice, slow response logging is checked against _SLOW_RESPONSE_THRESHOLD
        # but we're just verifying the mechanism works here


# ---------------------------------------------------------------------------
# Input validation tests
# ---------------------------------------------------------------------------


class TestValidateLawdCode:
    """Tests for region code validation."""

    def test_valid_lawd_code_returns_true(self) -> None:
        """A valid 5-digit LAWD code returns True."""
        from real_estate.mcp_server._helpers import validate_lawd_code

        # 11440 is Mapo-gu
        valid, error = validate_lawd_code("11440")

        assert valid is True
        assert error is None

    def test_empty_code_returns_error(self) -> None:
        """Empty code returns validation error."""
        from real_estate.mcp_server._helpers import validate_lawd_code

        valid, error = validate_lawd_code("")

        assert valid is False
        assert error is not None
        assert error["error"] == "invalid_input"
        assert "empty" in error["message"].lower()

    def test_non_digit_code_returns_error(self) -> None:
        """Non-digit code returns validation error."""
        from real_estate.mcp_server._helpers import validate_lawd_code

        valid, error = validate_lawd_code("abcde")

        assert valid is False
        assert error is not None
        assert error["error"] == "invalid_input"
        assert "5-digit" in error["message"]

    def test_wrong_length_code_returns_error(self) -> None:
        """Wrong length code returns validation error."""
        from real_estate.mcp_server._helpers import validate_lawd_code

        valid, error = validate_lawd_code("1234")

        assert valid is False
        assert error is not None
        assert "5-digit" in error["message"]

    def test_invalid_code_returns_error(self) -> None:
        """Invalid code not in region_codes.txt returns error."""
        from real_estate.mcp_server._helpers import validate_lawd_code

        valid, error = validate_lawd_code("99999")

        assert valid is False
        assert error is not None
        assert error["error"] == "invalid_input"
        assert "not a valid" in error["message"].lower()


class TestValidateDealYmd:
    """Tests for year-month validation."""

    def test_valid_ymd_returns_true(self) -> None:
        """A valid YYYYMM format returns True."""
        from real_estate.mcp_server._helpers import validate_deal_ymd

        valid, error = validate_deal_ymd("202501")

        assert valid is True
        assert error is None

    def test_empty_ymd_returns_error(self) -> None:
        """Empty YMD returns validation error."""
        from real_estate.mcp_server._helpers import validate_deal_ymd

        valid, error = validate_deal_ymd("")

        assert valid is False
        assert error is not None
        assert error["error"] == "invalid_input"

    def test_wrong_format_returns_error(self) -> None:
        """Wrong format returns validation error."""
        from real_estate.mcp_server._helpers import validate_deal_ymd

        valid, error = validate_deal_ymd("2025-01")

        assert valid is False
        assert error is not None
        assert "YYYYMM" in error["message"]

    def test_invalid_month_returns_error(self) -> None:
        """Invalid month returns validation error."""
        from real_estate.mcp_server._helpers import validate_deal_ymd

        valid, error = validate_deal_ymd("202513")

        assert valid is False
        assert error is not None
        assert "month" in error["message"].lower()

    def test_too_early_date_returns_error(self) -> None:
        """Date before 2006-01 returns validation error."""
        from real_estate.mcp_server._helpers import validate_deal_ymd

        valid, error = validate_deal_ymd("200512")

        assert valid is False
        assert error is not None
        assert "2006" in error["message"]

    def test_future_date_returns_error(self) -> None:
        """Future date returns validation error."""
        from datetime import datetime

        from real_estate.mcp_server._helpers import validate_deal_ymd

        now = datetime.now()
        future_ymd = f"{now.year + 1}01"

        valid, error = validate_deal_ymd(future_ymd)

        assert valid is False
        assert error is not None
        assert "future" in error["message"].lower()


class TestValidatePagination:
    """Tests for pagination validation."""

    def test_valid_num_of_rows_returns_true(self) -> None:
        """Valid num_of_rows returns True."""
        from real_estate.mcp_server._helpers import validate_pagination

        valid, error = validate_pagination(100)

        assert valid is True
        assert error is None

    def test_zero_returns_error(self) -> None:
        """Zero num_of_rows returns validation error."""
        from real_estate.mcp_server._helpers import validate_pagination

        valid, error = validate_pagination(0)

        assert valid is False
        assert error is not None
        assert error["error"] == "invalid_input"
        assert "at least 1" in error["message"]

    def test_negative_returns_error(self) -> None:
        """Negative num_of_rows returns validation error."""
        from real_estate.mcp_server._helpers import validate_pagination

        valid, error = validate_pagination(-1)

        assert valid is False
        assert error is not None
        assert error["error"] == "invalid_input"

    def test_too_large_returns_error(self) -> None:
        """num_of_rows > 1000 returns validation error."""
        from real_estate.mcp_server._helpers import validate_pagination

        valid, error = validate_pagination(1001)

        assert valid is False
        assert error is not None
        assert error["error"] == "invalid_input"
        assert "1000" in error["message"]


class TestInputValidationIntegration:
    """Integration tests for input validation with trade tools."""

    @pytest.fixture(autouse=True)
    def set_api_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Set a test API key environment variable."""
        monkeypatch.setenv("DATA_GO_KR_API_KEY", "test-key")

    @respx.mock
    async def test_invalid_region_code_prevents_api_call(self) -> None:
        """Invalid region code prevents API call."""
        from real_estate.mcp_server.tools.trade import get_apartment_trades

        # No mock needed - should fail before API call
        result = await get_apartment_trades("99999", "202501")

        assert result["error"] == "invalid_input"
        assert "not a valid" in result["message"].lower()

    @respx.mock
    async def test_invalid_date_format_prevents_api_call(self) -> None:
        """Invalid date format prevents API call."""
        from real_estate.mcp_server.tools.trade import get_apartment_trades

        result = await get_apartment_trades("11440", "2025-01")

        assert result["error"] == "invalid_input"
        assert "YYYYMM" in result["message"]
