"""Specification tests for API response caching system (SPEC-CACHE-007).

These tests define the expected behavior for:
- REQ-CACHE-001: TTL-based cache implementation
- REQ-CACHE-002: Cache key generation from URL + parameters
- REQ-CACHE-003: Cache hit (return cached response when valid)
- REQ-CACHE-004: Cache miss (fetch from API and cache the response)
- REQ-CACHE-005: Cache statistics logging (optional)
"""

import time
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# The cache_manager module does not exist yet - these imports will fail initially
# This is intentional for TDD RED phase


class TestCacheKeyGeneration:
    """Tests for REQ-CACHE-002: Cache key generation."""

    def test_generate_cache_key_simple_url(self) -> None:
        """Cache key should be generated from URL."""
        from real_estate.cache_manager import generate_cache_key

        key = generate_cache_key("https://api.example.com/data")
        assert isinstance(key, str)
        assert len(key) > 0

    def test_generate_cache_key_with_params(self) -> None:
        """Cache key should include URL and sorted parameters."""
        from real_estate.cache_manager import generate_cache_key

        key1 = generate_cache_key(
            "https://api.example.com/data",
            {"region": "11440", "date": "202501"},
        )
        key2 = generate_cache_key(
            "https://api.example.com/data",
            {"date": "202501", "region": "11440"},  # Different order
        )
        # Same parameters in different order should produce same key
        assert key1 == key2

    def test_generate_cache_key_different_urls(self) -> None:
        """Different URLs should produce different cache keys."""
        from real_estate.cache_manager import generate_cache_key

        key1 = generate_cache_key("https://api.example.com/data1")
        key2 = generate_cache_key("https://api.example.com/data2")
        assert key1 != key2

    def test_generate_cache_key_different_params(self) -> None:
        """Different parameters should produce different cache keys."""
        from real_estate.cache_manager import generate_cache_key

        key1 = generate_cache_key(
            "https://api.example.com/data",
            {"region": "11440"},
        )
        key2 = generate_cache_key(
            "https://api.example.com/data",
            {"region": "11110"},
        )
        assert key1 != key2

    def test_generate_cache_key_no_params(self) -> None:
        """Cache key should work with no parameters."""
        from real_estate.cache_manager import generate_cache_key

        key = generate_cache_key("https://api.example.com/data", None)
        assert isinstance(key, str)
        assert len(key) > 0


class TestTTLCacheBehavior:
    """Tests for REQ-CACHE-001: TTL-based cache implementation."""

    def test_cache_initialization_default_settings(self) -> None:
        """Cache should initialize with default TTL and maxsize."""
        from real_estate.cache_manager import APICache

        cache = APICache()
        assert cache.ttl == 300  # 5 minutes default
        assert cache.maxsize == 100  # 100 items default

    def test_cache_initialization_custom_settings(self) -> None:
        """Cache should accept custom TTL and maxsize."""
        from real_estate.cache_manager import APICache

        cache = APICache(ttl=600, maxsize=50)
        assert cache.ttl == 600
        assert cache.maxsize == 50

    def test_cache_set_and_get(self) -> None:
        """Cache should store and retrieve values."""
        from real_estate.cache_manager import APICache

        cache = APICache()
        cache.set("test_key", {"data": "test_value"})

        result = cache.get("test_key")
        assert result == {"data": "test_value"}

    def test_cache_get_nonexistent_key(self) -> None:
        """Getting nonexistent key should return None."""
        from real_estate.cache_manager import APICache

        cache = APICache()
        result = cache.get("nonexistent_key")
        assert result is None

    def test_cache_delete(self) -> None:
        """Cache should support deleting entries."""
        from real_estate.cache_manager import APICache

        cache = APICache()
        cache.set("test_key", {"data": "test_value"})
        cache.delete("test_key")

        result = cache.get("test_key")
        assert result is None

    def test_cache_clear(self) -> None:
        """Cache should support clearing all entries."""
        from real_estate.cache_manager import APICache

        cache = APICache()
        cache.set("key1", {"data": "value1"})
        cache.set("key2", {"data": "value2"})
        cache.clear()

        assert cache.get("key1") is None
        assert cache.get("key2") is None

    def test_cache_maxsize_enforcement(self) -> None:
        """Cache should evict oldest entries when maxsize is reached."""
        from real_estate.cache_manager import APICache

        cache = APICache(ttl=300, maxsize=3)
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        cache.set("key4", "value4")  # Should evict key1

        # key1 should be evicted (oldest)
        assert cache.get("key1") is None
        assert cache.get("key2") is not None
        assert cache.get("key3") is not None
        assert cache.get("key4") is not None


class TestCacheExpiration:
    """Tests for TTL-based cache expiration."""

    def test_cache_entry_expires_after_ttl(self) -> None:
        """Cache entry should expire after TTL seconds."""
        from real_estate.cache_manager import APICache

        # Use very short TTL for testing
        cache = APICache(ttl=0.1, maxsize=10)
        cache.set("test_key", {"data": "test_value"})

        # Should be present immediately
        assert cache.get("test_key") is not None

        # Wait for TTL to expire
        time.sleep(0.15)

        # Should be expired now
        assert cache.get("test_key") is None

    def test_cache_entry_not_expired_before_ttl(self) -> None:
        """Cache entry should not expire before TTL seconds."""
        from real_estate.cache_manager import APICache

        cache = APICache(ttl=5.0, maxsize=10)
        cache.set("test_key", {"data": "test_value"})

        # Should still be present after short delay
        time.sleep(0.1)
        assert cache.get("test_key") is not None


class TestCacheHitMiss:
    """Tests for REQ-CACHE-003 and REQ-CACHE-004: Cache hit/miss scenarios."""

    def test_cache_hit_returns_cached_data(self) -> None:
        """Cache hit should return cached data without API call."""
        from real_estate.cache_manager import APICache

        cache = APICache()
        cached_data = {"items": [{"id": 1}], "total_count": 1}
        cache.set("test_key", cached_data)

        result = cache.get("test_key")
        assert result == cached_data

    def test_cache_miss_returns_none(self) -> None:
        """Cache miss should return None."""
        from real_estate.cache_manager import APICache

        cache = APICache()
        result = cache.get("nonexistent_key")
        assert result is None

    def test_cache_has_key(self) -> None:
        """Cache should report if key exists and is valid."""
        from real_estate.cache_manager import APICache

        cache = APICache()
        assert cache.has("test_key") is False

        cache.set("test_key", {"data": "value"})
        assert cache.has("test_key") is True

    def test_cache_has_expired_key_returns_false(self) -> None:
        """has() should return False for expired keys."""
        from real_estate.cache_manager import APICache

        cache = APICache(ttl=0.1, maxsize=10)
        cache.set("test_key", {"data": "value"})

        # Should be present initially
        assert cache.has("test_key") is True

        # Wait for expiration
        time.sleep(0.15)

        # Should return False for expired key
        assert cache.has("test_key") is False


class TestCacheStatistics:
    """Tests for REQ-CACHE-005: Cache statistics (optional)."""

    def test_cache_stats_tracks_hits(self) -> None:
        """Cache should track hit count."""
        from real_estate.cache_manager import APICache

        cache = APICache()
        cache.set("key1", "value1")

        # Generate some hits
        cache.get("key1")
        cache.get("key1")
        cache.get("key1")

        stats = cache.get_stats()
        assert stats["hits"] == 3

    def test_cache_stats_tracks_misses(self) -> None:
        """Cache should track miss count."""
        from real_estate.cache_manager import APICache

        cache = APICache()

        # Generate some misses
        cache.get("nonexistent1")
        cache.get("nonexistent2")

        stats = cache.get_stats()
        assert stats["misses"] == 2

    def test_cache_stats_tracks_size(self) -> None:
        """Cache should track current size."""
        from real_estate.cache_manager import APICache

        cache = APICache()
        assert cache.get_stats()["size"] == 0

        cache.set("key1", "value1")
        assert cache.get_stats()["size"] == 1

        cache.set("key2", "value2")
        assert cache.get_stats()["size"] == 2

    def test_cache_stats_hit_rate(self) -> None:
        """Cache should calculate hit rate."""
        from real_estate.cache_manager import APICache

        cache = APICache()
        cache.set("key1", "value1")

        # 3 hits, 1 miss = 75% hit rate
        cache.get("key1")
        cache.get("key1")
        cache.get("key1")
        cache.get("nonexistent")

        stats = cache.get_stats()
        assert stats["hit_rate"] == 0.75


class TestGlobalCacheInstance:
    """Tests for global cache instance."""

    def test_get_cache_returns_singleton(self) -> None:
        """get_cache should return the same cache instance."""
        from real_estate.cache_manager import get_cache

        cache1 = get_cache()
        cache2 = get_cache()
        assert cache1 is cache2

    def test_get_cache_custom_settings(self) -> None:
        """get_cache should accept custom TTL and maxsize on first call."""
        from real_estate.cache_manager import get_cache, reset_cache

        # Reset to ensure fresh state
        reset_cache()

        cache = get_cache(ttl=600, maxsize=50)
        assert cache.ttl == 600
        assert cache.maxsize == 50


class TestCachedFetchIntegration:
    """Integration tests for cached fetch wrappers."""

    @pytest.mark.asyncio
    async def test_cached_fetch_xml_uses_cache(self) -> None:
        """cached_fetch_xml should use cache when available."""
        from real_estate.cache_manager import (
            cached_fetch_xml,
            generate_cache_key,
            get_cache,
            reset_cache,
        )

        reset_cache()
        cache = get_cache()

        # Pre-populate cache using the same key generation
        url = "https://api.example.com/test"
        cached_response = "<xml>cached</xml>"
        cache_key = generate_cache_key(url, None)
        cache.set(cache_key, (cached_response, None))

        # Should return cached response without making HTTP call
        result, error = await cached_fetch_xml(url)
        assert result == cached_response
        assert error is None

    @pytest.mark.asyncio
    async def test_cached_fetch_json_uses_cache(self) -> None:
        """cached_fetch_json should use cache when available."""
        from real_estate.cache_manager import (
            cached_fetch_json,
            generate_cache_key,
            get_cache,
            reset_cache,
        )

        reset_cache()
        cache = get_cache()

        # Pre-populate cache using the same key generation
        url = "https://api.example.com/test"
        cached_response = {"data": "cached"}
        cache_key = generate_cache_key(url, None)
        cache.set(cache_key, (cached_response, None))

        # Should return cached response without making HTTP call
        result, error = await cached_fetch_json(url)
        assert result == cached_response
        assert error is None

    @pytest.mark.asyncio
    async def test_cached_fetch_xml_cache_miss_fetches(self) -> None:
        """cached_fetch_xml should fetch from API on cache miss."""
        from real_estate.cache_manager import (
            cached_fetch_xml,
            generate_cache_key,
            get_cache,
            reset_cache,
        )

        reset_cache()

        url = "https://api.example.com/test"

        with patch("real_estate.cache_manager._fetch_xml") as mock_fetch:
            mock_fetch.return_value = ("<xml>fetched</xml>", None)

            result, error = await cached_fetch_xml(url)

            # Should have called the actual fetch
            mock_fetch.assert_called_once_with(url)
            assert result == "<xml>fetched</xml>"
            assert error is None

            # Result should now be cached using the generated key
            cache = get_cache()
            cache_key = generate_cache_key(url, None)
            cached = cache.get(cache_key)
            assert cached == ("<xml>fetched</xml>", None)

    @pytest.mark.asyncio
    async def test_cached_fetch_json_cache_miss_fetches(self) -> None:
        """cached_fetch_json should fetch from API on cache miss."""
        from real_estate.cache_manager import (
            cached_fetch_json,
            generate_cache_key,
            get_cache,
            reset_cache,
        )

        reset_cache()

        url = "https://api.example.com/test"

        with patch("real_estate.cache_manager._fetch_json") as mock_fetch:
            mock_fetch.return_value = ({"data": "fetched"}, None)

            result, error = await cached_fetch_json(url)

            # Should have called the actual fetch
            mock_fetch.assert_called_once_with(url, None)
            assert result == {"data": "fetched"}
            assert error is None

            # Result should now be cached using the generated key
            cache = get_cache()
            cache_key = generate_cache_key(url, None)
            cached = cache.get(cache_key)
            assert cached == ({"data": "fetched"}, None)

    @pytest.mark.asyncio
    async def test_cached_fetch_respects_circuit_breaker(self) -> None:
        """Cached fetch should still respect circuit breaker on cache miss."""
        from real_estate.cache_manager import cached_fetch_xml, reset_cache

        reset_cache()

        url = "https://api.example.com/test"

        with patch("real_estate.cache_manager._fetch_xml") as mock_fetch:
            mock_fetch.return_value = (
                None,
                {"error": "circuit_breaker_open", "message": "Blocked"},
            )

            result, error = await cached_fetch_xml(url)

            # Should return the circuit breaker error
            assert result is None
            assert error is not None
            assert error.get("error") == "circuit_breaker_open"

    @pytest.mark.asyncio
    async def test_cached_fetch_does_not_cache_errors(self) -> None:
        """Cached fetch should not cache error responses."""
        from real_estate.cache_manager import (
            cached_fetch_xml,
            generate_cache_key,
            get_cache,
            reset_cache,
        )

        reset_cache()

        url = "https://api.example.com/test"

        with patch("real_estate.cache_manager._fetch_xml") as mock_fetch:
            mock_fetch.return_value = (None, {"error": "network_error"})

            result, error = await cached_fetch_xml(url)

            # Should have returned the error
            assert result is None
            assert error is not None

            # Error should NOT be cached
            cache = get_cache()
            cache_key = generate_cache_key(url, None)
            cached = cache.get(cache_key)
            assert cached is None
