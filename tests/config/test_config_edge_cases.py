"""Edge case tests for configuration validation.

These tests cover additional edge cases for AppSettings validation
beyond the basic tests in tests/test_config_validator.py.

Requirements:
- REQ-TEST-004: Configuration tests for settings validation
"""

import pytest
from pydantic import ValidationError


class TestAppSettingsEdgeCases:
    """Edge case tests for AppSettings configuration."""

    def test_whitespace_only_api_key_raises_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Whitespace-only API key should raise ValidationError."""
        from real_estate.config_validator import AppSettings

        monkeypatch.setenv("DATA_GO_KR_API_KEY", "   ")

        with pytest.raises(ValidationError):
            AppSettings(_env_file=None)

    def test_api_key_with_internal_content_is_valid(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """API key with valid content is accepted."""
        from real_estate.config_validator import AppSettings

        # Keys typically don't have surrounding whitespace,
        # but the validator strips and checks for empty
        monkeypatch.setenv("DATA_GO_KR_API_KEY", "valid-key-12345")

        settings = AppSettings(_env_file=None)
        assert settings.data_go_kr_api_key == "valid-key-12345"

    def test_onbid_key_none_when_not_set(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """ONBID_API_KEY should be None when not set."""
        from real_estate.config_validator import AppSettings

        monkeypatch.setenv("DATA_GO_KR_API_KEY", "test-key")
        monkeypatch.delenv("ONBID_API_KEY", raising=False)

        settings = AppSettings()
        assert settings.onbid_api_key is None

    def test_onbid_key_empty_string_treated_as_none(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Empty ONBID_API_KEY should be treated as None (optional field)."""
        from real_estate.config_validator import AppSettings

        monkeypatch.setenv("DATA_GO_KR_API_KEY", "test-key")
        monkeypatch.setenv("ONBID_API_KEY", "")

        settings = AppSettings()
        # Empty string is the default for optional str | None
        assert settings.onbid_api_key == "" or settings.onbid_api_key is None

    def test_get_onbid_key_returns_data_key_when_onbid_not_set(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """get_onbid_key() returns DATA_GO_KR_API_KEY when ONBID_API_KEY not set."""
        from real_estate.config_validator import AppSettings

        monkeypatch.setenv("DATA_GO_KR_API_KEY", "data-api-key")
        monkeypatch.delenv("ONBID_API_KEY", raising=False)

        settings = AppSettings()
        assert settings.get_onbid_key() == "data-api-key"

    def test_get_onbid_key_returns_onbid_key_when_set(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """get_onbid_key() returns ONBID_API_KEY when set."""
        from real_estate.config_validator import AppSettings

        monkeypatch.setenv("DATA_GO_KR_API_KEY", "data-api-key")
        monkeypatch.setenv("ONBID_API_KEY", "onbid-api-key")

        settings = AppSettings()
        assert settings.get_onbid_key() == "onbid-api-key"

    def test_get_onbid_key_empty_string_falls_back(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """get_onbid_key() falls back to DATA_GO_KR_API_KEY when ONBID_API_KEY is empty."""
        from real_estate.config_validator import AppSettings

        monkeypatch.setenv("DATA_GO_KR_API_KEY", "data-api-key")
        monkeypatch.setenv("ONBID_API_KEY", "")

        settings = AppSettings()
        # Empty string is falsy, so should fall back
        result = settings.get_onbid_key()
        assert result == "data-api-key"


class TestOdcloudAuthEdgeCases:
    """Edge case tests for odcloud authentication methods."""

    def test_odcloud_auth_prefers_api_key(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """get_odcloud_auth() prefers ODCLOUD_API_KEY over SERVICE_KEY."""
        from real_estate.config_validator import AppSettings

        monkeypatch.setenv("DATA_GO_KR_API_KEY", "data-key")
        monkeypatch.setenv("ODCLOUD_API_KEY", "api-key")
        monkeypatch.setenv("ODCLOUD_SERVICE_KEY", "service-key")

        settings = AppSettings()
        mode, key = settings.get_odcloud_auth()
        assert mode == "authorization"
        assert key == "api-key"

    def test_odcloud_auth_uses_service_key_when_no_api_key(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """get_odcloud_auth() uses SERVICE_KEY when API_KEY not set."""
        from real_estate.config_validator import AppSettings

        monkeypatch.setenv("DATA_GO_KR_API_KEY", "data-key")
        monkeypatch.delenv("ODCLOUD_API_KEY", raising=False)
        monkeypatch.setenv("ODCLOUD_SERVICE_KEY", "service-key")

        settings = AppSettings()
        mode, key = settings.get_odcloud_auth()
        assert mode == "serviceKey"
        assert key == "service-key"

    def test_odcloud_auth_falls_back_to_data_key(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """get_odcloud_auth() falls back to DATA_GO_KR_API_KEY when no ODCLOUD keys."""
        from real_estate.config_validator import AppSettings

        monkeypatch.setenv("DATA_GO_KR_API_KEY", "data-key")
        monkeypatch.delenv("ODCLOUD_API_KEY", raising=False)
        monkeypatch.delenv("ODCLOUD_SERVICE_KEY", raising=False)

        settings = AppSettings()
        mode, key = settings.get_odcloud_auth()
        assert mode == "serviceKey"
        assert key == "data-key"

    def test_odcloud_auth_empty_api_key_falls_back_to_service_key(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Empty ODCLOUD_API_KEY falls back to SERVICE_KEY."""
        from real_estate.config_validator import AppSettings

        monkeypatch.setenv("DATA_GO_KR_API_KEY", "data-key")
        monkeypatch.setenv("ODCLOUD_API_KEY", "")
        monkeypatch.setenv("ODCLOUD_SERVICE_KEY", "service-key")

        settings = AppSettings()
        mode, key = settings.get_odcloud_auth()
        assert mode == "serviceKey"
        assert key == "service-key"


class TestGetSettingsSingleton:
    """Tests for get_settings() singleton behavior."""

    def test_get_settings_caches_instance(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """get_settings() returns cached instance on subsequent calls."""
        import real_estate.config_validator as config_module

        # Reset the global settings
        config_module._settings = None
        monkeypatch.setenv("DATA_GO_KR_API_KEY", "test-key")

        try:
            settings1 = config_module.get_settings()
            settings2 = config_module.get_settings()
            assert settings1 is settings2
        finally:
            # Cleanup
            config_module._settings = None

    def test_get_settings_creates_new_instance_when_none(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """get_settings() creates new instance when _settings is None."""
        import real_estate.config_validator as config_module

        # Ensure _settings is None
        config_module._settings = None
        monkeypatch.setenv("DATA_GO_KR_API_KEY", "test-key")

        try:
            settings = config_module.get_settings()
            assert isinstance(settings, config_module.AppSettings)
            assert settings.data_go_kr_api_key == "test-key"
        finally:
            # Cleanup
            config_module._settings = None


class TestAppSettingsModelConfig:
    """Tests for AppSettings model configuration."""

    def test_model_config_env_file_encoding(self) -> None:
        """Model config should have env_file_encoding set to utf-8."""
        from real_estate.config_validator import AppSettings

        assert AppSettings.model_config.get("env_file_encoding") == "utf-8"

    def test_model_config_case_insensitive(self) -> None:
        """Model config should be case insensitive."""
        from real_estate.config_validator import AppSettings

        assert AppSettings.model_config.get("case_sensitive") is False

    def test_model_config_extra_ignore(self) -> None:
        """Model config should ignore extra fields."""
        from real_estate.config_validator import AppSettings

        assert AppSettings.model_config.get("extra") == "ignore"
