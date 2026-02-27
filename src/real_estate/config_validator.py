"""Centralized configuration validation using Pydantic Settings.

This module provides a unified configuration management system that:
- Loads settings from environment variables and .env files
- Validates required settings at startup (fail-fast)
- Provides clear error messages with setup instructions
- Supports optional settings with fallback logic

Requirements:
- REQ-CONFIG-001: Centralized configuration class
- REQ-CONFIG-002: Fail-fast validation at startup
- REQ-CONFIG-003: Clear error messages with setup instructions
- REQ-CONFIG-005: Support for optional settings with fallback logic
"""

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """Centralized application settings with validation.

    This class manages all API keys and configuration values required
    by the real estate data collection system. Settings are loaded from
    environment variables and .env files with automatic validation.

    Attributes:
        data_go_kr_api_key: Required API key for data.go.kr APIs.
        onbid_api_key: Optional API key for Onbid APIs (falls back to data_go_kr_api_key).
        odcloud_api_key: Optional API key for odcloud authentication.
        odcloud_service_key: Optional service key for odcloud APIs.

    Example:
        >>> settings = AppSettings()  # Loads from .env or environment
        >>> api_key = settings.data_go_kr_api_key
        >>> onbid_key = settings.get_onbid_key()
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Required API keys
    data_go_kr_api_key: str  # Required - will raise ValidationError if missing

    # Optional API keys with fallback logic
    onbid_api_key: str | None = None
    odcloud_api_key: str | None = None
    odcloud_service_key: str | None = None

    @field_validator("data_go_kr_api_key")
    @classmethod
    def validate_data_go_kr_api_key(cls, v: str) -> str:
        """Validate that DATA_GO_KR_API_KEY is set and non-empty.

        Args:
            v: The value of data_go_kr_api_key from environment or .env.

        Returns:
            The validated API key string.

        Raises:
            ValueError: If the API key is empty or not set.

        Example:
            >>> # With DATA_GO_KR_API_KEY set to "my-key"
            >>> settings = AppSettings()
            >>> settings.data_go_kr_api_key
            'my-key'
        """
        if not v or not v.strip():
            raise ValueError(
                "DATA_GO_KR_API_KEY is required for accessing data.go.kr APIs. "
                "Get your API key from https://apis.data.go.kr and set it in your "
                ".env file or environment variables."
            )
        return v

    def get_onbid_key(self) -> str:
        """Get Onbid API key with fallback to DATA_GO_KR_API_KEY.

        Returns the ONBID_API_KEY if set, otherwise falls back to
        DATA_GO_KR_API_KEY for API calls that support the data.go.kr key.

        Returns:
            The Onbid API key (either ONBID_API_KEY or DATA_GO_KR_API_KEY).

        Example:
            >>> # With only DATA_GO_KR_API_KEY set
            >>> settings = AppSettings()
            >>> settings.get_onbid_key()
            'data-go-kr-key'

            >>> # With ONBID_API_KEY also set
            >>> settings = AppSettings()
            >>> settings.get_onbid_key()
            'onbid-key'
        """
        return self.onbid_api_key or self.data_go_kr_api_key

    def get_odcloud_auth(self) -> tuple[str, str]:
        """Get odcloud authentication mode and key.

        Returns the appropriate authentication method for odcloud APIs.
        Priority: ODCLOUD_API_KEY > ODCLOUD_SERVICE_KEY > DATA_GO_KR_API_KEY

        Returns:
            A tuple of (auth_mode, key) where:
            - auth_mode is "authorization" for ODCLOUD_API_KEY
            - auth_mode is "serviceKey" for ODCLOUD_SERVICE_KEY or DATA_GO_KR_API_KEY

        Example:
            >>> # With ODCLOUD_API_KEY set
            >>> settings = AppSettings()
            >>> mode, key = settings.get_odcloud_auth()
            >>> mode
            'authorization'

            >>> # With only DATA_GO_KR_API_KEY set
            >>> mode, key = settings.get_odcloud_auth()
            >>> mode
            'serviceKey'
        """
        if self.odcloud_api_key:
            return ("authorization", self.odcloud_api_key)
        if self.odcloud_service_key:
            return ("serviceKey", self.odcloud_service_key)
        return ("serviceKey", self.data_go_kr_api_key)


# Global settings instance for convenience
_settings: AppSettings | None = None


def get_settings() -> AppSettings:
    """Get the global AppSettings instance.

    Returns:
        The global AppSettings instance, creating it if necessary.

    Example:
        >>> settings = get_settings()
        >>> api_key = settings.data_go_kr_api_key
    """
    global _settings
    if _settings is None:
        _settings = AppSettings()
    return _settings
