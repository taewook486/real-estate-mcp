"""Specification tests for AppSettings configuration validation.

These tests define the expected behavior for centralized configuration
management using Pydantic Settings.

Requirements:
- REQ-CONFIG-001: Centralized configuration class
- REQ-CONFIG-002: Fail-fast validation at startup
- REQ-CONFIG-003: Clear error messages with setup instructions
- REQ-CONFIG-005: Support for optional settings with fallback logic
"""

import os
from typing import Any

import pytest
from pydantic import ValidationError

# ---------------------------------------------------------------------------
# TASK-001: AppSettings class existence and basic fields tests (RED)
# ---------------------------------------------------------------------------


class TestAppSettingsExists:
    """Tests for AppSettings class existence and import."""

    def test_app_settings_class_can_be_imported(self) -> None:
        """AppSettings class should be importable from config_validator."""
        from real_estate.config_validator import AppSettings  # noqa: F401

        assert True  # Import succeeded

    def test_app_settings_is_pydantic_settings_subclass(self) -> None:
        """AppSettings should inherit from pydantic_settings.BaseSettings."""
        from pydantic_settings import BaseSettings

        from real_estate.config_validator import AppSettings

        assert issubclass(AppSettings, BaseSettings)


class TestAppSettingsBasicFields:
    """Tests for basic field definitions in AppSettings."""

    def test_app_settings_has_data_go_kr_api_key_field(self) -> None:
        """AppSettings should have data_go_kr_api_key field."""
        from real_estate.config_validator import AppSettings

        # Get field info from model
        fields = AppSettings.model_fields
        assert "data_go_kr_api_key" in fields

    def test_app_settings_has_onbid_api_key_field(self) -> None:
        """AppSettings should have onbid_api_key field (optional)."""
        from real_estate.config_validator import AppSettings

        fields = AppSettings.model_fields
        assert "onbid_api_key" in fields

    def test_app_settings_has_odcloud_api_key_field(self) -> None:
        """AppSettings should have odcloud_api_key field (optional)."""
        from real_estate.config_validator import AppSettings

        fields = AppSettings.model_fields
        assert "odcloud_api_key" in fields

    def test_app_settings_has_odcloud_service_key_field(self) -> None:
        """AppSettings should have odcloud_service_key field (optional)."""
        from real_estate.config_validator import AppSettings

        fields = AppSettings.model_fields
        assert "odcloud_service_key" in fields

    def test_app_settings_loads_from_environment(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """AppSettings should load values from environment variables."""
        monkeypatch.setenv("DATA_GO_KR_API_KEY", "test-api-key-123")

        from real_estate.config_validator import AppSettings

        settings = AppSettings()
        assert settings.data_go_kr_api_key == "test-api-key-123"

    def test_app_settings_loads_from_dotenv_file(
        self, tmp_path: Any, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """AppSettings should load values from .env file."""
        # Create a temporary .env file
        env_file = tmp_path / ".env"
        env_file.write_text("DATA_GO_KR_API_KEY=dotenv-key-456\n")

        # Clear any existing environment variable to test .env file loading
        monkeypatch.delenv("DATA_GO_KR_API_KEY", raising=False)

        from real_estate.config_validator import AppSettings

        # Pass explicit env_file path to ensure the temp .env is loaded
        settings = AppSettings(_env_file=str(env_file))
        assert settings.data_go_kr_api_key == "dotenv-key-456"


# ---------------------------------------------------------------------------
# TASK-003: Required field validation tests (RED)
# ---------------------------------------------------------------------------


class TestRequiredFieldValidation:
    """Tests for required field validation with clear error messages."""

    def test_missing_data_go_kr_api_key_raises_validation_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Missing DATA_GO_KR_API_KEY should raise ValidationError."""

        from real_estate.config_validator import AppSettings

        monkeypatch.delenv("DATA_GO_KR_API_KEY", raising=False)

        # Use _env_file=None to prevent loading from .env file
        with pytest.raises(ValidationError):
            AppSettings(_env_file=None)

    def test_empty_data_go_kr_api_key_raises_validation_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Empty DATA_GO_KR_API_KEY should raise ValidationError."""

        from real_estate.config_validator import AppSettings

        monkeypatch.setenv("DATA_GO_KR_API_KEY", "")

        with pytest.raises(ValidationError):
            AppSettings(_env_file=None)

    def test_validation_error_includes_variable_name(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """ValidationError message should include the field name."""

        from real_estate.config_validator import AppSettings

        monkeypatch.delenv("DATA_GO_KR_API_KEY", raising=False)

        with pytest.raises(ValidationError) as exc_info:
            AppSettings(_env_file=None)

        error_message = str(exc_info.value)
        # Pydantic uses lowercase field name in error message
        assert "data_go_kr_api_key" in error_message.lower()

    def test_validation_error_includes_setup_instructions(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """ValidationError message should include setup instructions when key is empty."""

        from real_estate.config_validator import AppSettings

        # Set empty string to trigger custom validator
        monkeypatch.setenv("DATA_GO_KR_API_KEY", "")

        with pytest.raises(ValidationError) as exc_info:
            AppSettings(_env_file=None)

        error_message = str(exc_info.value)
        # Our custom validator includes setup instructions
        assert "https://apis.data.go.kr" in error_message


# ---------------------------------------------------------------------------
# TASK-005: Optional fields and fallback tests (RED)
# ---------------------------------------------------------------------------


class TestOptionalFieldsWithFallback:
    """Tests for optional fields with fallback logic."""

    def test_onbid_api_key_defaults_to_none(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """ONBID_API_KEY should default to None if not set."""
        from real_estate.config_validator import AppSettings

        monkeypatch.setenv("DATA_GO_KR_API_KEY", "test-key")
        monkeypatch.delenv("ONBID_API_KEY", raising=False)

        settings = AppSettings()
        assert settings.onbid_api_key is None

    def test_get_onbid_key_returns_onbid_key_when_set(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """get_onbid_key() should return ONBID_API_KEY when set."""
        from real_estate.config_validator import AppSettings

        monkeypatch.setenv("DATA_GO_KR_API_KEY", "data-key")
        monkeypatch.setenv("ONBID_API_KEY", "onbid-key")

        settings = AppSettings()
        assert settings.get_onbid_key() == "onbid-key"

    def test_get_onbid_key_falls_back_to_data_go_kr_key(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """get_onbid_key() should fall back to DATA_GO_KR_API_KEY when ONBID_API_KEY is not set."""
        from real_estate.config_validator import AppSettings

        monkeypatch.setenv("DATA_GO_KR_API_KEY", "data-key")
        monkeypatch.delenv("ONBID_API_KEY", raising=False)

        settings = AppSettings()
        assert settings.get_onbid_key() == "data-key"

    def test_get_odcloud_auth_returns_api_key_mode_when_set(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """get_odcloud_auth() should return ('authorization', ODCLOUD_API_KEY) when set."""
        from real_estate.config_validator import AppSettings

        monkeypatch.setenv("DATA_GO_KR_API_KEY", "data-key")
        monkeypatch.setenv("ODCLOUD_API_KEY", "odcloud-api-key")
        monkeypatch.delenv("ODCLOUD_SERVICE_KEY", raising=False)

        settings = AppSettings()
        mode, key = settings.get_odcloud_auth()
        assert mode == "authorization"
        assert key == "odcloud-api-key"

    def test_get_odcloud_auth_falls_back_to_service_key(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """get_odcloud_auth() should fall back to ('serviceKey', ODCLOUD_SERVICE_KEY)."""
        from real_estate.config_validator import AppSettings

        monkeypatch.setenv("DATA_GO_KR_API_KEY", "data-key")
        monkeypatch.delenv("ODCLOUD_API_KEY", raising=False)
        monkeypatch.setenv("ODCLOUD_SERVICE_KEY", "service-key")

        settings = AppSettings()
        mode, key = settings.get_odcloud_auth()
        assert mode == "serviceKey"
        assert key == "service-key"

    def test_get_odcloud_auth_falls_back_to_data_go_kr_key(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """get_odcloud_auth() should fall back to DATA_GO_KR_API_KEY when no ODCLOUD key."""
        from real_estate.config_validator import AppSettings

        monkeypatch.setenv("DATA_GO_KR_API_KEY", "data-key")
        monkeypatch.delenv("ODCLOUD_API_KEY", raising=False)
        monkeypatch.delenv("ODCLOUD_SERVICE_KEY", raising=False)

        settings = AppSettings()
        mode, key = settings.get_odcloud_auth()
        assert mode == "serviceKey"
        assert key == "data-key"

    def test_get_odcloud_auth_priority_order(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """get_odcloud_auth() should prioritize ODCLOUD_API_KEY > SERVICE_KEY > DATA_GO_KR."""
        from real_estate.config_validator import AppSettings

        # All keys set - should prefer ODCLOUD_API_KEY
        monkeypatch.setenv("DATA_GO_KR_API_KEY", "data-key")
        monkeypatch.setenv("ODCLOUD_API_KEY", "api-key")
        monkeypatch.setenv("ODCLOUD_SERVICE_KEY", "service-key")

        settings = AppSettings()
        mode, key = settings.get_odcloud_auth()
        assert mode == "authorization"
        assert key == "api-key"

        # ODCLOUD_API_KEY not set - should use ODCLOUD_SERVICE_KEY
        monkeypatch.delenv("ODCLOUD_API_KEY", raising=False)
        settings2 = AppSettings()
        mode2, key2 = settings2.get_odcloud_auth()
        assert mode2 == "serviceKey"
        assert key2 == "service-key"


# ---------------------------------------------------------------------------
# REFACTOR: Additional tests for get_settings() helper
# ---------------------------------------------------------------------------


class TestGetSettingsHelper:
    """Tests for the global get_settings() helper function."""

    def test_get_settings_returns_app_settings_instance(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """get_settings() should return an AppSettings instance."""
        import real_estate.config_validator as config_module

        # Reset the global settings
        config_module._settings = None
        monkeypatch.setenv("DATA_GO_KR_API_KEY", "test-key")

        settings = config_module.get_settings()
        assert isinstance(settings, config_module.AppSettings)

        # Cleanup
        config_module._settings = None

    def test_get_settings_returns_singleton(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """get_settings() should return the same instance on multiple calls."""
        import real_estate.config_validator as config_module

        # Reset the global settings
        config_module._settings = None
        monkeypatch.setenv("DATA_GO_KR_API_KEY", "test-key")

        settings1 = config_module.get_settings()
        settings2 = config_module.get_settings()
        assert settings1 is settings2

        # Cleanup
        config_module._settings = None
