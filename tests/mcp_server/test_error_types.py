"""Tests for MCP tool error response standardization.

This test module verifies the error_types module which provides:
- ErrorType enum for categorizing errors
- ErrorResponse dataclass for standardized error responses
- Helper functions for creating common error responses
"""

from __future__ import annotations

import pytest


class TestErrorTypeEnum:
    """Tests for ErrorType enum."""

    def test_error_type_has_config_error(self) -> None:
        """ErrorType should include config_error for environment variable issues."""
        from real_estate.mcp_server.error_types import ErrorType

        assert hasattr(ErrorType, "CONFIG_ERROR")
        assert ErrorType.CONFIG_ERROR.value == "config_error"

    def test_error_type_has_invalid_input(self) -> None:
        """ErrorType should include invalid_input for validation failures."""
        from real_estate.mcp_server.error_types import ErrorType

        assert hasattr(ErrorType, "INVALID_INPUT")
        assert ErrorType.INVALID_INPUT.value == "invalid_input"

    def test_error_type_has_network_error(self) -> None:
        """ErrorType should include network_error for API connection issues."""
        from real_estate.mcp_server.error_types import ErrorType

        assert hasattr(ErrorType, "NETWORK_ERROR")
        assert ErrorType.NETWORK_ERROR.value == "network_error"

    def test_error_type_has_api_error(self) -> None:
        """ErrorType should include api_error for external API error responses."""
        from real_estate.mcp_server.error_types import ErrorType

        assert hasattr(ErrorType, "API_ERROR")
        assert ErrorType.API_ERROR.value == "api_error"

    def test_error_type_has_parse_error(self) -> None:
        """ErrorType should include parse_error for data parsing failures."""
        from real_estate.mcp_server.error_types import ErrorType

        assert hasattr(ErrorType, "PARSE_ERROR")
        assert ErrorType.PARSE_ERROR.value == "parse_error"

    def test_error_type_has_internal_error(self) -> None:
        """ErrorType should include internal_error for unexpected errors."""
        from real_estate.mcp_server.error_types import ErrorType

        assert hasattr(ErrorType, "INTERNAL_ERROR")
        assert ErrorType.INTERNAL_ERROR.value == "internal_error"

    def test_error_type_count(self) -> None:
        """ErrorType should have exactly 6 error types as per SPEC."""
        from real_estate.mcp_server.error_types import ErrorType

        assert len(list(ErrorType)) == 6


class TestErrorResponse:
    """Tests for ErrorResponse dataclass."""

    def test_error_response_basic_fields(self) -> None:
        """ErrorResponse should have error, message, and suggestion fields."""
        from real_estate.mcp_server.error_types import ErrorResponse, ErrorType

        response = ErrorResponse(
            error=ErrorType.INVALID_INPUT,
            message="Invalid parameter value",
            suggestion="Please provide a valid value",
        )

        assert response.error == ErrorType.INVALID_INPUT
        assert response.message == "Invalid parameter value"
        assert response.suggestion == "Please provide a valid value"

    def test_error_response_to_dict(self) -> None:
        """ErrorResponse should be convertible to dict for MCP tool returns."""
        from real_estate.mcp_server.error_types import ErrorResponse, ErrorType

        response = ErrorResponse(
            error=ErrorType.CONFIG_ERROR,
            message="API key not set",
            suggestion="Set the DATA_GO_KR_API_KEY environment variable",
        )

        result = response.to_dict()

        assert isinstance(result, dict)
        assert result["error"] == "config_error"
        assert result["message"] == "API key not set"
        assert result["suggestion"] == "Set the DATA_GO_KR_API_KEY environment variable"

    def test_error_response_to_dict_with_extra_fields(self) -> None:
        """ErrorResponse should support additional fields for extensibility."""
        from real_estate.mcp_server.error_types import ErrorResponse, ErrorType

        response = ErrorResponse(
            error=ErrorType.API_ERROR,
            message="API returned error",
            suggestion="Check API documentation",
            code="RATE_LIMIT_EXCEEDED",
            retry_after=60,
        )

        result = response.to_dict()

        assert result["error"] == "api_error"
        assert result["message"] == "API returned error"
        assert result["suggestion"] == "Check API documentation"
        assert result["code"] == "RATE_LIMIT_EXCEEDED"
        assert result["retry_after"] == 60

    def test_error_response_string_error_type(self) -> None:
        """ErrorResponse should accept both ErrorType enum and string for error."""
        from real_estate.mcp_server.error_types import ErrorResponse

        # Using string for backward compatibility
        response = ErrorResponse(
            error="validation_error",  # type: ignore[arg-type]
            message="Invalid input",
            suggestion="Check your input",
        )

        result = response.to_dict()
        assert result["error"] == "validation_error"


class TestErrorResponseHelpers:
    """Tests for error response helper functions."""

    def test_make_config_error(self) -> None:
        """make_config_error should create standardized config error response."""
        from real_estate.mcp_server.error_types import ErrorType, make_config_error

        result = make_config_error("DATA_GO_KR_API_KEY")

        assert result["error"] == ErrorType.CONFIG_ERROR.value
        assert "DATA_GO_KR_API_KEY" in result["message"]
        assert "environment variable" in result["suggestion"].lower()

    def test_make_invalid_input_error(self) -> None:
        """make_invalid_input_error should create standardized validation error."""
        from real_estate.mcp_server.error_types import ErrorType, make_invalid_input_error

        result = make_invalid_input_error(
            field="page_no",
            reason="must be >= 1",
            example="1",
        )

        assert result["error"] == ErrorType.INVALID_INPUT.value
        assert "page_no" in result["message"]
        assert result["suggestion"] is not None

    def test_make_network_error(self) -> None:
        """make_network_error should create standardized network error response."""
        from real_estate.mcp_server.error_types import ErrorType, make_network_error

        result = make_network_error("Connection timed out")

        assert result["error"] == ErrorType.NETWORK_ERROR.value
        assert "timed out" in result["message"].lower()
        assert "try again" in result["suggestion"].lower()

    def test_make_api_error(self) -> None:
        """make_api_error should create standardized API error response."""
        from real_estate.mcp_server.error_types import ErrorType, make_api_error

        result = make_api_error(
            code="03",
            message="No records found",
        )

        assert result["error"] == ErrorType.API_ERROR.value
        assert result["code"] == "03"
        assert "No records found" in result["message"]

    def test_make_parse_error(self) -> None:
        """make_parse_error should create standardized parse error response."""
        from real_estate.mcp_server.error_types import ErrorType, make_parse_error

        result = make_parse_error("XML", "Invalid format")

        assert result["error"] == ErrorType.PARSE_ERROR.value
        assert "XML" in result["message"]
        assert result["suggestion"] is not None

    def test_make_internal_error(self) -> None:
        """make_internal_error should create standardized internal error response."""
        from real_estate.mcp_server.error_types import ErrorType, make_internal_error

        result = make_internal_error("Unexpected null value")

        assert result["error"] == ErrorType.INTERNAL_ERROR.value
        assert "unexpected" in result["message"].lower()
        assert result["suggestion"] is not None


class TestExceptionToErrorResponse:
    """Tests for exception_to_error_response function."""

    def test_file_not_found_to_parse_error(self) -> None:
        """FileNotFoundError should be converted to parse_error."""
        from real_estate.mcp_server.error_types import (
            ErrorType,
            exception_to_error_response,
        )

        exc = FileNotFoundError("test.docx")
        result = exception_to_error_response(exc, context="docx_parser")

        assert result["error"] == ErrorType.PARSE_ERROR.value
        assert "test.docx" in result["message"]

    def test_value_error_to_invalid_input(self) -> None:
        """ValueError should be converted to invalid_input."""
        from real_estate.mcp_server.error_types import (
            ErrorType,
            exception_to_error_response,
        )

        exc = ValueError("Invalid format")
        result = exception_to_error_response(exc, context="parameter validation")

        assert result["error"] == ErrorType.INVALID_INPUT.value
        assert "Invalid format" in result["message"]

    def test_generic_exception_to_internal_error(self) -> None:
        """Generic exceptions should be converted to internal_error."""
        from real_estate.mcp_server.error_types import (
            ErrorType,
            exception_to_error_response,
        )

        exc = RuntimeError("Something went wrong")
        result = exception_to_error_response(exc)

        assert result["error"] == ErrorType.INTERNAL_ERROR.value

    def test_exception_with_context(self) -> None:
        """Exception context should be included in the error message."""
        from real_estate.mcp_server.error_types import exception_to_error_response

        exc = ValueError("Bad value")
        result = exception_to_error_response(exc, context="parsing HWP file")

        assert "parsing HWP file" in result["message"] or "HWP" in result["message"]


class TestErrorResponseIntegration:
    """Integration tests for error response usage patterns."""

    def test_error_response_as_mcp_return_value(self) -> None:
        """ErrorResponse should be usable as MCP tool return value."""
        from real_estate.mcp_server.error_types import ErrorResponse, ErrorType

        # Simulate MCP tool returning an error
        def mock_mcp_tool(page_no: int) -> dict[str, object]:
            if page_no < 1:
                return ErrorResponse(
                    error=ErrorType.INVALID_INPUT,
                    message="page_no must be >= 1",
                    suggestion="Use a positive page number starting from 1",
                ).to_dict()
            return {"data": "success"}

        result = mock_mcp_tool(0)
        assert "error" in result
        assert result["error"] == "invalid_input"

        result = mock_mcp_tool(1)
        assert result["data"] == "success"

    def test_error_response_preserves_original_error_code(self) -> None:
        """ErrorResponse should preserve API error codes for debugging."""
        from real_estate.mcp_server.error_types import ErrorType, make_api_error

        # Simulating existing pattern from onbid.py
        result = make_api_error(
            code="03",
            message="No trade records found",
        )

        assert result["error"] == ErrorType.API_ERROR.value
        assert result["code"] == "03"  # Original API code preserved

    def test_error_response_with_korean_message(self) -> None:
        """ErrorResponse should support Korean messages for user-facing errors."""
        from real_estate.mcp_server.error_types import ErrorResponse, ErrorType

        response = ErrorResponse(
            error=ErrorType.INVALID_INPUT,
            message="페이지 번호는 1 이상이어야 합니다",
            suggestion="1 이상의 숫자를 입력해 주세요",
        )

        result = response.to_dict()
        assert "1 이상" in result["message"]
