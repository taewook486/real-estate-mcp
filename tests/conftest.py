"""Shared pytest fixtures and configuration for the test suite."""

import pytest


@pytest.fixture(autouse=True)
def reset_settings_cache() -> None:
    """Reset settings cache before each test to ensure isolation.

    This fixture is automatically applied to all tests to ensure
    that the cached AppSettings instance is cleared between tests,
    allowing each test to have a clean configuration state.
    """
    try:
        from real_estate.mcp_server._helpers import _reset_settings_cache

        _reset_settings_cache()
        yield
        _reset_settings_cache()
    except ImportError:
        # Skip reset if _helpers module cannot be imported (e.g., missing mcp package)
        # This allows config_validator tests to run independently
        yield


@pytest.fixture(autouse=True)
def reset_cache() -> None:
    """Reset API cache before each test to ensure isolation.

    This fixture is automatically applied to all tests to ensure
    that the global cache instance is cleared between tests,
    allowing each test to have a clean cache state.
    """
    try:
        from real_estate.cache_manager import reset_cache as _reset_cache

        _reset_cache()
        yield
        _reset_cache()
    except ImportError:
        # Skip reset if cache_manager module cannot be imported
        yield
