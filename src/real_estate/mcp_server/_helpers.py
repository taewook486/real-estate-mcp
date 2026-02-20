"""Shared helpers, URL constants, and tool runners for the MCP server.

This module provides:
- Network resilience: exponential backoff retry, circuit breaker pattern
- Structured logging: JSON-formatted logs with request tracking
- Connection monitoring: response time tracking and degradation alerts
"""

from __future__ import annotations

import os
import statistics
import time
import urllib.parse
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any
from uuid import uuid4

import httpx
import structlog
from defusedxml.ElementTree import ParseError as XmlParseError
from defusedxml.ElementTree import fromstring as xml_fromstring
from tenacity import (
    AsyncRetrying,
    RetryError,
    stop_after_attempt,
    wait_exponential,
)

# Configure structured logging
logger = structlog.get_logger()

# ---------------------------------------------------------------------------
# API base URLs
# ---------------------------------------------------------------------------

_APT_TRADE_URL = "https://apis.data.go.kr/1613000/RTMSDataSvcAptTrade/getRTMSDataSvcAptTrade"
_APT_RENT_URL = "https://apis.data.go.kr/1613000/RTMSDataSvcAptRent/getRTMSDataSvcAptRent"
_OFFI_TRADE_URL = "https://apis.data.go.kr/1613000/RTMSDataSvcOffiTrade/getRTMSDataSvcOffiTrade"
_OFFI_RENT_URL = "https://apis.data.go.kr/1613000/RTMSDataSvcOffiRent/getRTMSDataSvcOffiRent"
_VILLA_TRADE_URL = "https://apis.data.go.kr/1613000/RTMSDataSvcRHTrade/getRTMSDataSvcRHTrade"
_VILLA_RENT_URL = "https://apis.data.go.kr/1613000/RTMSDataSvcRHRent/getRTMSDataSvcRHRent"
_SINGLE_TRADE_URL = "https://apis.data.go.kr/1613000/RTMSDataSvcSHTrade/getRTMSDataSvcSHTrade"
_SINGLE_RENT_URL = "https://apis.data.go.kr/1613000/RTMSDataSvcSHRent/getRTMSDataSvcSHRent"
_COMMERCIAL_TRADE_URL = "https://apis.data.go.kr/1613000/RTMSDataSvcNrgTrade/getRTMSDataSvcNrgTrade"

_ODCLOUD_BASE_URL = "https://api.odcloud.kr/api"
_APT_SUBSCRIPTION_INFO_PATH = "/15101046/v1/uddi:14a46595-03dd-47d3-a418-d64e52820598"

_APPLYHOME_STAT_BASE_URL = "https://api.odcloud.kr/api/ApplyhomeStatSvc/v1"

_ONBID_BID_RESULT_LIST_URL = (
    "http://apis.data.go.kr/B010003/OnbidCltrBidRsltListSrvc/getCltrBidRsltList"
)
_ONBID_BID_RESULT_DETAIL_URL = (
    "http://apis.data.go.kr/B010003/OnbidCltrBidRsltDtlSrvc/getCltrBidRsltDtl"
)

_ONBID_THING_INFO_LIST_URL = (
    "http://openapi.onbid.co.kr/openapi/services/ThingInfoInquireSvc/getUnifyUsageCltr"
)

_ONBID_CODE_INFO_BASE_URL = "http://openapi.onbid.co.kr/openapi/services/OnbidCodeInfoInquireSvc"
_ONBID_CODE_TOP_URL = f"{_ONBID_CODE_INFO_BASE_URL}/getOnbidTopCodeInfo"
_ONBID_CODE_MIDDLE_URL = f"{_ONBID_CODE_INFO_BASE_URL}/getOnbidMiddleCodeInfo"
_ONBID_CODE_BOTTOM_URL = f"{_ONBID_CODE_INFO_BASE_URL}/getOnbidBottomCodeInfo"
_ONBID_ADDR1_URL = f"{_ONBID_CODE_INFO_BASE_URL}/getOnbidAddr1Info"
_ONBID_ADDR2_URL = f"{_ONBID_CODE_INFO_BASE_URL}/getOnbidAddr2Info"
_ONBID_ADDR3_URL = f"{_ONBID_CODE_INFO_BASE_URL}/getOnbidAddr3Info"
_ONBID_DTL_ADDR_URL = f"{_ONBID_CODE_INFO_BASE_URL}/getOnbidDtlAddrInfo"

_ERROR_MESSAGES: dict[str, str] = {
    "03": "No trade records found for the specified region and period.",
    "10": "Invalid API request parameters.",
    "22": "Daily API request limit exceeded.",
    "30": "Unregistered API key.",
    "31": "API key has expired.",
}

# ---------------------------------------------------------------------------
# Network resilience configuration
# ---------------------------------------------------------------------------

# Retry configuration: max 3 attempts, exponential backoff (1s, 2s, 4s), max 8s
_RETRY_MAX_ATTEMPTS = 3
_RETRY_INITIAL_DELAY = 1.0  # seconds
_RETRY_MAX_DELAY = 8.0  # seconds

# Circuit breaker configuration: 5 failures trigger open, 30s recovery
_CIRCUIT_BREAKER_FAILURE_THRESHOLD = 5
_CIRCUIT_BREAKER_RECOVERY_TIMEOUT = 30.0  # seconds

# Connection quality threshold for logging
_SLOW_RESPONSE_THRESHOLD = 10.0  # seconds

# HTTP timeout configuration
_CONNECTION_TIMEOUT = 5.0  # seconds
_READ_TIMEOUT = 15.0  # seconds


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class CircuitBreaker:
    """Circuit breaker implementation for network resilience.

    Tracks failures and opens the circuit after threshold is reached.
    After recovery timeout, allows a test request (half-open state).
    """

    failure_threshold: int = _CIRCUIT_BREAKER_FAILURE_THRESHOLD
    recovery_timeout: float = _CIRCUIT_BREAKER_RECOVERY_TIMEOUT
    _failure_count: int = field(default=0, repr=False)
    _last_failure_time: float | None = field(default=None, repr=False)
    _state: CircuitState = field(default=CircuitState.CLOSED, repr=False)
    _last_notification_time: float | None = field(default=None, repr=False)

    def can_execute(self) -> tuple[bool, dict[str, Any] | None]:
        """Check if request can proceed.

        Returns:
            Tuple of (can_proceed, error_dict_if_blocked)
        """
        if self._state == CircuitState.CLOSED:
            return True, None

        if self._state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if self._last_failure_time is not None:
                elapsed = time.time() - self._last_failure_time
                if elapsed >= self.recovery_timeout:
                    self._state = CircuitState.HALF_OPEN
                    logger.info(
                        "circuit_breaker_half_open",
                        failure_count=self._failure_count,
                        recovery_timeout=self.recovery_timeout,
                    )
                    return True, None

            # Still in cooldown, notify user (at most once per 10 seconds)
            now = time.time()
            if self._last_notification_time is None or now - self._last_notification_time >= 10.0:
                self._last_notification_time = now
                logger.warning(
                    "circuit_breaker_open_user_notification",
                    message="API requests temporarily blocked due to repeated failures",
                    recovery_in_seconds=int(
                        self.recovery_timeout - (now - (self._last_failure_time or now))
                    ),
                )

            return False, {
                "error": "circuit_breaker_open",
                "message": (
                    "API requests are temporarily blocked due to repeated failures. "
                    "Please try again in a few moments."
                ),
            }

        # HALF_OPEN: allow one test request
        return True, None

    def record_success(self) -> None:
        """Record successful request, reset circuit if in half-open."""
        if self._state == CircuitState.HALF_OPEN:
            logger.info(
                "circuit_breaker_recovered",
                previous_failures=self._failure_count,
            )
        self._failure_count = 0
        self._state = CircuitState.CLOSED

    def record_failure(self) -> None:
        """Record failed request, potentially open circuit."""
        self._failure_count += 1
        self._last_failure_time = time.time()

        if self._state == CircuitState.HALF_OPEN:
            # Test request failed, open circuit again
            self._state = CircuitState.OPEN
            logger.warning(
                "circuit_breaker_reopened",
                failure_count=self._failure_count,
            )
        elif self._failure_count >= self.failure_threshold:
            self._state = CircuitState.OPEN
            logger.warning(
                "circuit_breaker_opened",
                failure_count=self._failure_count,
                threshold=self.failure_threshold,
                recovery_timeout=self.recovery_timeout,
            )

    @property
    def state(self) -> CircuitState:
        """Current circuit breaker state."""
        return self._state


# Global circuit breaker instance for MOLIT API
_molit_circuit_breaker = CircuitBreaker()


def _reset_circuit_breaker() -> None:
    """Reset the circuit breaker (for testing)."""
    global _molit_circuit_breaker
    _molit_circuit_breaker = CircuitBreaker()


# ---------------------------------------------------------------------------
# URL builders
# ---------------------------------------------------------------------------


def _build_url_with_service_key(base: str, service_key: str, params: dict[str, Any]) -> str:
    """Build a URL with a URL-encoded serviceKey embedded directly in the string."""
    encoded_key = urllib.parse.quote(service_key, safe="")
    encoded_params = urllib.parse.urlencode(params, doseq=True)
    if encoded_params:
        return f"{base}?serviceKey={encoded_key}&{encoded_params}"
    return f"{base}?serviceKey={encoded_key}"


def _build_url(base: str, region_code: str, year_month: str, num_of_rows: int) -> str:
    """Build a data.go.kr API URL with serviceKey embedded in the path."""
    api_key = os.getenv("DATA_GO_KR_API_KEY", "")
    encoded_key = urllib.parse.quote(api_key, safe="")
    return (
        f"{base}?serviceKey={encoded_key}"
        f"&LAWD_CD={region_code}&DEAL_YMD={year_month}"
        f"&numOfRows={num_of_rows}&pageNo=1"
    )


# ---------------------------------------------------------------------------
# HTTP helpers with network resilience
# ---------------------------------------------------------------------------


async def _fetch_xml(url: str) -> tuple[str | None, dict[str, Any] | None]:
    """Perform an async HTTP GET with retry and circuit breaker, return XML or error.

    Features:
    - Exponential backoff retry (max 3 attempts, 1s-8s delays)
    - Circuit breaker (opens after 5 failures, 30s recovery)
    - Connection quality monitoring (logs slow responses >10s)
    - Structured JSON logging for requests and errors

    Args:
        url: The URL to fetch

    Returns:
        Tuple of (xml_text, None) on success or (None, error_dict) on failure
    """
    # Check circuit breaker
    can_proceed, block_error = _molit_circuit_breaker.can_execute()
    if not can_proceed:
        return None, block_error

    request_id = str(uuid4())[:8]
    start_time = time.time()

    async def _do_fetch() -> str:
        """Internal fetch function for retry logic."""
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(_CONNECTION_TIMEOUT, read=_READ_TIMEOUT)
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.text

    try:
        # Use tenacity for exponential backoff retry
        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(_RETRY_MAX_ATTEMPTS),
            wait=wait_exponential(
                multiplier=_RETRY_INITIAL_DELAY,
                min=_RETRY_INITIAL_DELAY,
                max=_RETRY_MAX_DELAY,
            ),
            reraise=True,
        ):
            with attempt:
                logger.debug(
                    "http_request_start",
                    request_id=request_id,
                    url=url,
                    attempt=attempt.retry_state.attempt_number,
                )
                try:
                    xml_text = await _do_fetch()
                    duration_ms = (time.time() - start_time) * 1000

                    # Log slow responses
                    if duration_ms > _SLOW_RESPONSE_THRESHOLD * 1000:
                        logger.warning(
                            "connection_quality_degradation",
                            request_id=request_id,
                            url=url,
                            duration_ms=duration_ms,
                            threshold_ms=_SLOW_RESPONSE_THRESHOLD * 1000,
                        )

                    logger.info(
                        "http_request_success",
                        request_id=request_id,
                        url=url,
                        duration_ms=duration_ms,
                        status="success",
                    )

                    _molit_circuit_breaker.record_success()
                    return xml_text, None

                except httpx.TimeoutException as exc:
                    duration_ms = (time.time() - start_time) * 1000
                    logger.warning(
                        "http_request_timeout",
                        request_id=request_id,
                        url=url,
                        attempt=attempt.retry_state.attempt_number,
                        duration_ms=duration_ms,
                        error=str(exc),
                    )
                    raise

    except RetryError:
        # All retries exhausted
        duration_ms = (time.time() - start_time) * 1000
        _molit_circuit_breaker.record_failure()

        logger.error(
            "http_request_retry_exhausted",
            request_id=request_id,
            url=url,
            duration_ms=duration_ms,
            circuit_breaker_state=_molit_circuit_breaker.state.value,
        )

        return None, {
            "error": "network_error",
            "message": (
                f"API server timed out after {_RETRY_MAX_ATTEMPTS} attempts. "
                "Please try again later."
            ),
        }

    except httpx.TimeoutException:
        # Timeout after retries exhausted (when not caught by RetryError)
        duration_ms = (time.time() - start_time) * 1000
        _molit_circuit_breaker.record_failure()

        logger.error(
            "http_request_timeout_exhausted",
            request_id=request_id,
            url=url,
            duration_ms=duration_ms,
        )

        return None, {
            "error": "network_error",
            "message": (
                f"API server timed out after {_RETRY_MAX_ATTEMPTS} attempts. "
                "Please try again later."
            ),
        }

    except httpx.HTTPStatusError as exc:
        duration_ms = (time.time() - start_time) * 1000
        _molit_circuit_breaker.record_failure()

        logger.error(
            "http_request_http_error",
            request_id=request_id,
            url=url,
            status_code=exc.response.status_code,
            duration_ms=duration_ms,
        )

        return None, {
            "error": "network_error",
            "message": f"HTTP error: {exc.response.status_code}",
        }

    except httpx.RequestError as exc:
        duration_ms = (time.time() - start_time) * 1000
        _molit_circuit_breaker.record_failure()

        logger.error(
            "http_request_network_error",
            request_id=request_id,
            url=url,
            error=str(exc),
            duration_ms=duration_ms,
        )

        return None, {"error": "network_error", "message": f"Network error: {exc}"}

    # This should never be reached as all paths return, but satisfies type checker
    return None, {"error": "unknown_error", "message": "Unexpected error in fetch logic"}


async def _fetch_json(
    url: str,
    headers: dict[str, str] | None = None,
) -> tuple[dict[str, Any] | list[Any] | None, dict[str, Any] | None]:
    """Perform an async HTTP GET with retry and circuit breaker, return JSON or error.

    Features:
    - Exponential backoff retry (max 3 attempts, 1s-8s delays)
    - Circuit breaker (opens after 5 failures, 30s recovery)
    - Connection quality monitoring (logs slow responses >10s)
    - Structured JSON logging for requests and errors

    Args:
        url: The URL to fetch
        headers: Optional HTTP headers

    Returns:
        Tuple of (json_data, None) on success or (None, error_dict) on failure
    """
    # Check circuit breaker
    can_proceed, block_error = _molit_circuit_breaker.can_execute()
    if not can_proceed:
        return None, block_error

    request_id = str(uuid4())[:8]
    start_time = time.time()

    async def _do_fetch() -> dict[str, Any] | list[Any]:
        """Internal fetch function for retry logic."""
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(_CONNECTION_TIMEOUT, read=_READ_TIMEOUT),
            headers=headers,
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()

    try:
        # Use tenacity for exponential backoff retry
        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(_RETRY_MAX_ATTEMPTS),
            wait=wait_exponential(
                multiplier=_RETRY_INITIAL_DELAY,
                min=_RETRY_INITIAL_DELAY,
                max=_RETRY_MAX_DELAY,
            ),
            reraise=True,
        ):
            with attempt:
                logger.debug(
                    "http_request_start",
                    request_id=request_id,
                    url=url,
                    attempt=attempt.retry_state.attempt_number,
                )
                try:
                    json_data = await _do_fetch()
                    duration_ms = (time.time() - start_time) * 1000

                    # Log slow responses
                    if duration_ms > _SLOW_RESPONSE_THRESHOLD * 1000:
                        logger.warning(
                            "connection_quality_degradation",
                            request_id=request_id,
                            url=url,
                            duration_ms=duration_ms,
                            threshold_ms=_SLOW_RESPONSE_THRESHOLD * 1000,
                        )

                    logger.info(
                        "http_request_success",
                        request_id=request_id,
                        url=url,
                        duration_ms=duration_ms,
                        status="success",
                    )

                    _molit_circuit_breaker.record_success()
                    return json_data, None

                except httpx.TimeoutException as exc:
                    duration_ms = (time.time() - start_time) * 1000
                    logger.warning(
                        "http_request_timeout",
                        request_id=request_id,
                        url=url,
                        attempt=attempt.retry_state.attempt_number,
                        duration_ms=duration_ms,
                        error=str(exc),
                    )
                    raise

    except RetryError:
        # All retries exhausted
        duration_ms = (time.time() - start_time) * 1000
        _molit_circuit_breaker.record_failure()

        logger.error(
            "http_request_retry_exhausted",
            request_id=request_id,
            url=url,
            duration_ms=duration_ms,
            circuit_breaker_state=_molit_circuit_breaker.state.value,
        )

        return None, {
            "error": "network_error",
            "message": (
                f"API server timed out after {_RETRY_MAX_ATTEMPTS} attempts. "
                "Please try again later."
            ),
        }

    except httpx.TimeoutException:
        # Timeout after retries exhausted (when not caught by RetryError)
        duration_ms = (time.time() - start_time) * 1000
        _molit_circuit_breaker.record_failure()

        logger.error(
            "http_request_timeout_exhausted",
            request_id=request_id,
            url=url,
            duration_ms=duration_ms,
        )

        return None, {
            "error": "network_error",
            "message": (
                f"API server timed out after {_RETRY_MAX_ATTEMPTS} attempts. "
                "Please try again later."
            ),
        }

    except httpx.HTTPStatusError as exc:
        duration_ms = (time.time() - start_time) * 1000
        _molit_circuit_breaker.record_failure()

        logger.error(
            "http_request_http_error",
            request_id=request_id,
            url=url,
            status_code=exc.response.status_code,
            duration_ms=duration_ms,
        )

        return None, {
            "error": "network_error",
            "message": f"HTTP error: {exc.response.status_code}",
        }

    except ValueError as exc:
        # JSON parse error - don't count against circuit breaker
        duration_ms = (time.time() - start_time) * 1000

        logger.error(
            "json_parse_error",
            request_id=request_id,
            url=url,
            error=str(exc),
            duration_ms=duration_ms,
        )

        return None, {"error": "parse_error", "message": f"JSON parse failed: {exc}"}

    except httpx.RequestError as exc:
        duration_ms = (time.time() - start_time) * 1000
        _molit_circuit_breaker.record_failure()

        logger.error(
            "http_request_network_error",
            request_id=request_id,
            url=url,
            error=str(exc),
            duration_ms=duration_ms,
        )

        return None, {"error": "network_error", "message": f"Network error: {exc}"}

    # This should never be reached as all paths return, but satisfies type checker
    return None, {"error": "unknown_error", "message": "Unexpected error in fetch logic"}


# ---------------------------------------------------------------------------
# API key helpers
# ---------------------------------------------------------------------------


def _check_api_key() -> dict[str, Any] | None:
    """Return an error dict if DATA_GO_KR_API_KEY is not set, else None."""
    if not os.getenv("DATA_GO_KR_API_KEY", ""):
        return {
            "error": "config_error",
            "message": "Environment variable DATA_GO_KR_API_KEY is not set.",
        }
    return None


def _get_data_go_kr_key_for_onbid() -> str:
    """Return the service key to use for Onbid APIs."""
    return os.getenv("ONBID_API_KEY", "") or os.getenv("DATA_GO_KR_API_KEY", "")


def _check_onbid_api_key() -> dict[str, Any] | None:
    """Return an error dict if Onbid API key is not set, else None."""
    if not _get_data_go_kr_key_for_onbid():
        return {
            "error": "config_error",
            "message": "Environment variable ONBID_API_KEY (or DATA_GO_KR_API_KEY) is not set.",
        }
    return None


def _get_odcloud_key() -> tuple[str, str]:
    """Return (mode, key) for odcloud authentication."""
    api_key = os.getenv("ODCLOUD_API_KEY", "")
    if api_key:
        return "authorization", api_key
    service_key = os.getenv("ODCLOUD_SERVICE_KEY", "")
    if service_key:
        return "serviceKey", service_key
    fallback_key = os.getenv("DATA_GO_KR_API_KEY", "")
    if fallback_key:
        return "serviceKey", fallback_key
    return "", ""


def _check_odcloud_key() -> dict[str, Any] | None:
    """Return an error dict if odcloud key is not set, else None."""
    mode, key = _get_odcloud_key()
    if not mode or not key:
        return {
            "error": "config_error",
            "message": (
                "Environment variable ODCLOUD_API_KEY "
                "(or ODCLOUD_SERVICE_KEY, or DATA_GO_KR_API_KEY) "
                "is not set."
            ),
        }
    return None


# ---------------------------------------------------------------------------
# Input validation helpers
# ---------------------------------------------------------------------------

# Path to region codes file
_REGION_CODES_FILE = Path(__file__).parent.parent / "resources" / "region_codes.txt"

# Cache for valid region codes (5-digit API codes)
_valid_lawd_codes_cache: set[str] | None = None


def _load_valid_lawd_codes() -> set[str]:
    """Load and cache valid 5-digit LAWD codes from region_codes.txt."""
    global _valid_lawd_codes_cache

    if _valid_lawd_codes_cache is not None:
        return _valid_lawd_codes_cache

    codes: set[str] = set()
    try:
        with _REGION_CODES_FILE.open(encoding="utf-8") as f:
            next(f)  # skip header
            for line in f:
                parts = line.rstrip("\n").split("\t")
                if len(parts) < 3:
                    continue
                code, _, status = parts[0], parts[1], parts[2]
                if status == "존재":
                    # Extract 5-digit API code
                    codes.add(code[:5])
    except FileNotFoundError:
        logger.warning(
            "region_codes_file_not_found",
            path=str(_REGION_CODES_FILE),
        )

    _valid_lawd_codes_cache = codes
    return codes


def validate_lawd_code(code: str) -> tuple[bool, dict[str, Any] | None]:
    """Validate a 5-digit LAWD code against the region codes file.

    Args:
        code: The 5-digit region code to validate

    Returns:
        Tuple of (is_valid, error_dict_if_invalid)
    """
    if not code:
        return False, {
            "error": "invalid_input",
            "message": "Region code must not be empty. Example: '11440' (Mapo-gu)",
        }

    if not code.isdigit() or len(code) != 5:
        return False, {
            "error": "invalid_input",
            "message": (
                f"Region code must be a 5-digit number. Got: '{code}'. Example: '11440' (Mapo-gu)"
            ),
        }

    valid_codes = _load_valid_lawd_codes()
    if code not in valid_codes:
        return False, {
            "error": "invalid_input",
            "message": (
                f"Region code '{code}' is not a valid legal district code. "
                "Use get_region_code tool to find the correct code."
            ),
        }

    return True, None


def validate_deal_ymd(ymd: str) -> tuple[bool, dict[str, Any] | None]:
    """Validate a date in YYYYMM format.

    Valid range: 2006-01 to current month (API data starts from January 2006).

    Args:
        ymd: The year-month string to validate

    Returns:
        Tuple of (is_valid, error_dict_if_invalid)
    """
    from datetime import datetime

    if not ymd:
        return False, {
            "error": "invalid_input",
            "message": "Year-month must not be empty. Example: '202501' (January 2025)",
        }

    if len(ymd) != 6 or not ymd.isdigit():
        return False, {
            "error": "invalid_input",
            "message": (
                f"Year-month must be in YYYYMM format. Got: '{ymd}'. "
                "Example: '202501' (January 2025)"
            ),
        }

    year = int(ymd[:4])
    month = int(ymd[4:])

    if month < 1 or month > 12:
        return False, {
            "error": "invalid_input",
            "message": (
                f"Month must be between 01 and 12. Got: '{month:02d}'. "
                "Example: '202501' (January 2025)"
            ),
        }

    # API data starts from January 2006
    min_year = 2006
    min_month = 1

    # Get current date for upper bound
    now = datetime.now()
    max_year = now.year
    max_month = now.month

    # Convert to comparable values
    input_val = year * 100 + month
    min_val = min_year * 100 + min_month
    max_val = max_year * 100 + max_month

    if input_val < min_val:
        return False, {
            "error": "invalid_input",
            "message": (
                f"Year-month must be 2006-01 or later. Got: '{ymd}'. "
                "The API provides data starting from January 2006."
            ),
        }

    if input_val > max_val:
        return False, {
            "error": "invalid_input",
            "message": (
                f"Year-month cannot be in the future. Got: '{ymd}'. "
                f"Current period: {max_year}{max_month:02d}"
            ),
        }

    return True, None


def validate_pagination(num_of_rows: int) -> tuple[bool, dict[str, Any] | None]:
    """Validate pagination parameters.

    Args:
        num_of_rows: Number of rows per page

    Returns:
        Tuple of (is_valid, error_dict_if_invalid)
    """
    if num_of_rows < 1:
        return False, {
            "error": "invalid_input",
            "message": (f"num_of_rows must be at least 1. Got: {num_of_rows}. Example: 100"),
        }

    if num_of_rows > 1000:
        return False, {
            "error": "invalid_input",
            "message": (
                f"num_of_rows cannot exceed 1000. Got: {num_of_rows}. "
                "Use multiple requests for more data."
            ),
        }

    return True, None


# ---------------------------------------------------------------------------
# XML / data helpers
# ---------------------------------------------------------------------------


def _get_total_count(root: Any) -> int:
    """Extract totalCount from a parsed XML root element."""
    try:
        return int(root.findtext(".//totalCount") or "0")
    except ValueError:
        return 0


def _get_total_count_onbid(root: Any) -> int:
    """Extract total count from an Onbid ThingInfoInquireSvc XML response."""
    for tag in ("TotalCount", "totalCount", "totalcount"):
        raw = root.findtext(f".//{tag}")
        if raw:
            try:
                return int(raw)
            except ValueError:
                return 0
    return 0


def _txt(item: Any, tag: str) -> str:
    """Extract and strip text content from an XML element."""
    return (item.findtext(tag) or "").strip()


def _parse_amount(raw: str) -> int | None:
    """Parse a comma-formatted amount string to int. Returns None on failure."""
    try:
        return int(raw.replace(",", ""))
    except ValueError:
        return None


def _parse_float(raw: str) -> float:
    """Parse a string to float, returning 0.0 on failure."""
    try:
        return float(raw)
    except ValueError:
        return 0.0


def _parse_int(raw: str) -> int:
    """Parse a string to int, returning 0 on failure."""
    try:
        return int(raw)
    except ValueError:
        return 0


def _parse_monthly_rent(item: Any) -> int:
    """Parse monthlyRent field from an XML item. Empty or invalid values return 0."""
    monthly_rent_raw = _txt(item, "monthlyRent")
    if not monthly_rent_raw:
        return 0
    return _parse_amount(monthly_rent_raw) or 0


def _make_date(item: Any) -> str:
    """Construct a YYYY-MM-DD date string from dealYear/Month/Day elements."""
    year = _txt(item, "dealYear")
    month = _txt(item, "dealMonth").zfill(2)
    day = _txt(item, "dealDay").zfill(2)
    return f"{year}-{month}-{day}" if year else ""


def _build_trade_summary(items: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute sale price summary statistics."""
    if not items:
        return {
            "median_price_10k": 0,
            "min_price_10k": 0,
            "max_price_10k": 0,
            "sample_count": 0,
        }
    prices = [it["price_10k"] for it in items]
    return {
        "median_price_10k": int(statistics.median(prices)),
        "min_price_10k": min(prices),
        "max_price_10k": max(prices),
        "sample_count": len(prices),
    }


def _build_rent_summary(items: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute lease/rent deposit summary statistics."""
    if not items:
        return {
            "median_deposit_10k": 0,
            "min_deposit_10k": 0,
            "max_deposit_10k": 0,
            "monthly_rent_avg_10k": 0,
            "jeonse_ratio_pct": None,
            "sample_count": 0,
        }
    deposits = [it["deposit_10k"] for it in items]
    rents = [it["monthly_rent_10k"] for it in items]
    return {
        "median_deposit_10k": int(statistics.median(deposits)),
        "min_deposit_10k": min(deposits),
        "max_deposit_10k": max(deposits),
        "monthly_rent_avg_10k": int(statistics.mean(rents)) if rents else 0,
        "jeonse_ratio_pct": None,
        "sample_count": len(deposits),
    }


def _api_error_response(error_code: str) -> dict[str, Any]:
    """Build a standardised API error response dict."""
    msg = _ERROR_MESSAGES.get(error_code, f"API error code: {error_code}")
    return {"error": "api_error", "code": error_code, "message": msg}


# ---------------------------------------------------------------------------
# Tool runners
# ---------------------------------------------------------------------------


async def _run_trade_tool(
    base_url: str,
    parser: Any,
    region_code: str,
    year_month: str,
    num_of_rows: int,
) -> dict[str, Any]:
    """Fetch, parse, and summarise a sale (trade) API response."""
    return await _run_molit_xml_tool(
        base_url=base_url,
        parser=parser,
        region_code=region_code,
        year_month=year_month,
        num_of_rows=num_of_rows,
        summary_builder=_build_trade_summary,
    )


async def _run_rent_tool(
    base_url: str,
    parser: Any,
    region_code: str,
    year_month: str,
    num_of_rows: int,
) -> dict[str, Any]:
    """Fetch, parse, and summarise a lease/rent API response."""
    return await _run_molit_xml_tool(
        base_url=base_url,
        parser=parser,
        region_code=region_code,
        year_month=year_month,
        num_of_rows=num_of_rows,
        summary_builder=_build_rent_summary,
    )


async def _run_molit_xml_tool(
    *,
    base_url: str,
    parser: Any,
    region_code: str,
    year_month: str,
    num_of_rows: int,
    summary_builder: Any,
) -> dict[str, Any]:
    """Shared execution flow for MOLIT trade/rent XML tools.

    Includes input validation to prevent API calls with invalid parameters.
    """
    # Input validation - check region code
    valid, validation_err = validate_lawd_code(region_code)
    if not valid:
        assert validation_err is not None
        return validation_err

    # Input validation - check year-month
    valid, validation_err = validate_deal_ymd(year_month)
    if not valid:
        assert validation_err is not None
        return validation_err

    # Input validation - check pagination
    valid, validation_err = validate_pagination(num_of_rows)
    if not valid:
        assert validation_err is not None
        return validation_err

    err = _check_api_key()
    if err:
        return err

    url = _build_url(base_url, region_code, year_month, num_of_rows)
    xml_text, fetch_err = await _fetch_xml(url)
    if fetch_err:
        return fetch_err
    assert xml_text is not None

    try:
        items, error_code = parser(xml_text)
    except XmlParseError as exc:
        return {"error": "parse_error", "message": f"XML parse failed: {exc}"}

    if error_code is not None:
        return _api_error_response(error_code)

    root = xml_fromstring(xml_text)
    return {
        "total_count": _get_total_count(root),
        "items": items,
        "summary": summary_builder(items),
    }


async def _run_onbid_code_info_tool(
    endpoint_url: str,
    params: dict[str, Any],
) -> dict[str, Any]:
    """Fetch and parse an OnbidCodeInfoInquireSvc response."""
    from real_estate.mcp_server.parsers.onbid import _parse_onbid_code_info_xml

    err = _check_onbid_api_key()
    if err:
        return err

    page_no = int(params.get("pageNo") or 1)
    num_of_rows = int(params.get("numOfRows") or 10)

    service_key = _get_data_go_kr_key_for_onbid()
    url = _build_url_with_service_key(endpoint_url, service_key, params)
    xml_text, fetch_err = await _fetch_xml(url)
    if fetch_err:
        return fetch_err
    assert xml_text is not None

    try:
        items, total_count, error_code, error_message = _parse_onbid_code_info_xml(xml_text)
    except XmlParseError as exc:
        return {"error": "parse_error", "message": f"XML parse failed: {exc}"}

    if error_code is not None:
        return {
            "error": "api_error",
            "code": error_code,
            "message": error_message or "Onbid API error",
        }

    return {
        "total_count": total_count,
        "items": items,
        "page_no": page_no,
        "num_of_rows": num_of_rows,
    }
