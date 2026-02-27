"""Standardized error response types for MCP tools.

This module provides a consistent error response structure across all MCP tools,
improving user experience and debugging efficiency.

Standard format:
    {
        "error": "<error_type>",
        "message": "<human_readable_message>",
        "suggestion": "<actionable_solution>"
    }

Error Types:
    - config_error: Environment variable configuration issues
    - invalid_input: User input validation failures
    - network_error: API connection problems
    - api_error: External API error responses
    - parse_error: Data parsing failures
    - internal_error: Unexpected internal errors

SPEC: SPEC-ERROR-005
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ErrorType(Enum):
    """Enumeration of standardized error types for MCP tools.

    Each error type represents a category of errors that can occur
    during MCP tool execution.
    """

    CONFIG_ERROR = "config_error"
    INVALID_INPUT = "invalid_input"
    NETWORK_ERROR = "network_error"
    API_ERROR = "api_error"
    PARSE_ERROR = "parse_error"
    INTERNAL_ERROR = "internal_error"


@dataclass
class ErrorResponse:
    """Standardized error response for MCP tools.

    This dataclass provides a consistent structure for error responses
    across all MCP tools, making it easier for users to understand
    errors and take corrective action.

    Attributes:
        error: The type of error (ErrorType enum or string for backward compatibility).
        message: Human-readable description of the error.
        suggestion: Actionable suggestion for resolving the error.
        **extra_fields: Additional fields for extensibility (e.g., API error codes).

    Example:
        >>> response = ErrorResponse(
        ...     error=ErrorType.INVALID_INPUT,
        ...     message="page_no must be >= 1",
        ...     suggestion="Use a positive page number starting from 1"
        ... )
        >>> response.to_dict()
        {'error': 'invalid_input', 'message': '...', 'suggestion': '...'}
    """

    error: ErrorType | str
    message: str
    suggestion: str
    _extra_fields: dict[str, Any] = field(default_factory=dict, repr=False)

    def __init__(
        self,
        error: ErrorType | str,
        message: str,
        suggestion: str,
        **extra_fields: Any,
    ) -> None:
        """Initialize ErrorResponse with error type, message, suggestion, and optional extra fields."""
        self.error = error
        self.message = message
        self.suggestion = suggestion
        self._extra_fields = extra_fields

    def to_dict(self) -> dict[str, Any]:
        """Convert ErrorResponse to a dictionary for MCP tool return values.

        Returns:
            Dictionary with error, message, suggestion, and any extra fields.
        """
        error_value = self.error.value if isinstance(self.error, ErrorType) else self.error
        result: dict[str, Any] = {
            "error": error_value,
            "message": self.message,
            "suggestion": self.suggestion,
        }
        result.update(self._extra_fields)
        return result


# ---------------------------------------------------------------------------
# Helper functions for creating common error responses
# ---------------------------------------------------------------------------


def make_config_error(env_var_name: str) -> dict[str, Any]:
    """Create a standardized configuration error response.

    Args:
        env_var_name: Name of the missing environment variable.

    Returns:
        Standardized error response dictionary.
    """
    return ErrorResponse(
        error=ErrorType.CONFIG_ERROR,
        message=f"Environment variable {env_var_name} is not set.",
        suggestion=f"Set the {env_var_name} environment variable before using this tool.",
    ).to_dict()


def make_invalid_input_error(
    field: str,
    reason: str,
    example: str | None = None,
) -> dict[str, Any]:
    """Create a standardized invalid input error response.

    Args:
        field: Name of the invalid field.
        reason: Description of why the input is invalid.
        example: Optional example of valid input.

    Returns:
        Standardized error response dictionary.
    """
    message = f"{field} {reason}"
    suggestion = f"Provide a valid value for {field}."
    if example:
        suggestion = f"Provide a valid value for {field}. Example: {example}"

    return ErrorResponse(
        error=ErrorType.INVALID_INPUT,
        message=message,
        suggestion=suggestion,
    ).to_dict()


def make_network_error(detail: str) -> dict[str, Any]:
    """Create a standardized network error response.

    Args:
        detail: Description of the network error.

    Returns:
        Standardized error response dictionary.
    """
    return ErrorResponse(
        error=ErrorType.NETWORK_ERROR,
        message=f"Network error: {detail}",
        suggestion="Please check your network connection and try again later.",
    ).to_dict()


def make_api_error(
    code: str,
    message: str,
    suggestion: str | None = None,
) -> dict[str, Any]:
    """Create a standardized API error response.

    Args:
        code: API error code.
        message: API error message.
        suggestion: Optional suggestion for resolving the error.

    Returns:
        Standardized error response dictionary with code preserved.
    """
    return ErrorResponse(
        error=ErrorType.API_ERROR,
        message=message,
        suggestion=suggestion or "Check the API documentation for error resolution.",
        code=code,
    ).to_dict()


def make_parse_error(format_name: str, detail: str) -> dict[str, Any]:
    """Create a standardized parse error response.

    Args:
        format_name: Name of the format being parsed (e.g., "XML", "JSON", "HWP").
        detail: Description of the parsing error.

    Returns:
        Standardized error response dictionary.
    """
    return ErrorResponse(
        error=ErrorType.PARSE_ERROR,
        message=f"{format_name} parse failed: {detail}",
        suggestion=f"Verify the {format_name} file is valid and not corrupted.",
    ).to_dict()


def make_internal_error(detail: str) -> dict[str, Any]:
    """Create a standardized internal error response.

    Args:
        detail: Description of the internal error.

    Returns:
        Standardized error response dictionary.
    """
    return ErrorResponse(
        error=ErrorType.INTERNAL_ERROR,
        message=f"Unexpected error: {detail}",
        suggestion="Please try again. If the problem persists, contact support.",
    ).to_dict()


# ---------------------------------------------------------------------------
# Exception conversion utilities
# ---------------------------------------------------------------------------


def exception_to_error_response(
    exc: Exception,
    context: str | None = None,
) -> dict[str, Any]:
    """Convert a Python exception to a standardized error response.

    This function maps common exception types to appropriate error types
    and generates user-friendly messages and suggestions.

    Args:
        exc: The exception to convert.
        context: Optional context about where the exception occurred.

    Returns:
        Standardized error response dictionary.
    """
    exc_message = str(exc)

    # FileNotFoundError -> parse_error (for file parsing utilities)
    if isinstance(exc, FileNotFoundError):
        filename = exc_message if exc_message else "file"
        return ErrorResponse(
            error=ErrorType.PARSE_ERROR,
            message=f"File not found: {filename}",
            suggestion="Verify the file path is correct and the file exists.",
        ).to_dict()

    # ValueError -> invalid_input (for validation failures)
    if isinstance(exc, ValueError):
        message = exc_message
        if context:
            message = f"{context}: {exc_message}"
        return ErrorResponse(
            error=ErrorType.INVALID_INPUT,
            message=message,
            suggestion="Check the input value and try again.",
        ).to_dict()

    # KeyError -> invalid_input (for missing required fields)
    if isinstance(exc, KeyError):
        key = exc_message if exc_message else "unknown"
        return ErrorResponse(
            error=ErrorType.INVALID_INPUT,
            message=f"Missing required field: {key}",
            suggestion="Ensure all required fields are provided.",
        ).to_dict()

    # TypeError -> internal_error (for type-related issues)
    if isinstance(exc, TypeError):
        return ErrorResponse(
            error=ErrorType.INTERNAL_ERROR,
            message=f"Type error: {exc_message}",
            suggestion="Please try again. If the problem persists, contact support.",
        ).to_dict()

    # Default: internal_error for unhandled exceptions
    message = exc_message
    if context:
        message = f"{context}: {exc_message}"

    return ErrorResponse(
        error=ErrorType.INTERNAL_ERROR,
        message=f"Unexpected error: {message}",
        suggestion="Please try again. If the problem persists, contact support.",
    ).to_dict()
