"""API Response Caching System (SPEC-CACHE-007).

This module provides TTL-based caching for API responses to:
- Reduce response time for repeated requests
- Reduce API call count to stay within daily limits
- Ensure data freshness through TTL expiration

Features:
- TTL-based cache with configurable expiration (default: 300s / 5 minutes)
- Maximum cache size limit (default: 100 items)
- Thread-safe cache operations using cachetools.TTLCache
- Cache statistics tracking (hits, misses, hit rate)
- Integration with existing _fetch_xml and _fetch_json helpers
"""

from __future__ import annotations

import hashlib
import urllib.parse
from dataclasses import dataclass
from typing import Any

import structlog
from cachetools import TTLCache

from real_estate.mcp_server._helpers import _fetch_json, _fetch_xml

# Configure structured logging
logger = structlog.get_logger()

# @MX:NOTE: Default cache configuration for API responses
# REQ-CACHE-001: TTL-based cache with 5-minute default expiration
# @MX:SPEC: SPEC-CACHE-007
DEFAULT_TTL = 300  # 5 minutes in seconds
DEFAULT_MAXSIZE = 100  # Maximum number of cached items


def generate_cache_key(url: str, params: dict[str, Any] | None = None) -> str:
    """Generate a unique cache key from URL and parameters.

    REQ-CACHE-002: Cache key is generated from URL + sorted parameters.

    The cache key is created by:
    1. Combining URL with sorted parameters
    2. Creating a SHA-256 hash for consistent length

    Args:
        url: The API endpoint URL
        params: Optional dictionary of request parameters

    Returns:
        A unique string key for cache lookup

    Example:
        >>> key1 = generate_cache_key("https://api.example.com", {"a": "1", "b": "2"})
        >>> key2 = generate_cache_key("https://api.example.com", {"b": "2", "a": "1"})
        >>> key1 == key2  # Order doesn't matter
        True
    """
    if params is None:
        key_input = url
    else:
        # Sort parameters to ensure consistent ordering
        sorted_params = urllib.parse.urlencode(sorted(params.items()))
        key_input = f"{url}?{sorted_params}"

    # Create hash for consistent key length
    return hashlib.sha256(key_input.encode()).hexdigest()


@dataclass
class CacheStats:
    """Statistics for cache performance monitoring."""

    hits: int = 0
    misses: int = 0

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate (0.0 to 1.0)."""
        total = self.hits + self.misses
        if total == 0:
            return 0.0
        return self.hits / total


class APICache:
    """TTL-based cache for API responses.

    REQ-CACHE-001: TTL-based cache implementation using cachetools.TTLCache.

    This class wraps cachetools.TTLCache with additional features:
    - Statistics tracking (hits, misses, hit rate)
    - Type-safe interface for cached responses
    - Thread-safe operations

    Attributes:
        ttl: Time-to-live in seconds for cached entries
        maxsize: Maximum number of entries in cache

    Example:
        >>> cache = APICache(ttl=300, maxsize=100)
        >>> cache.set("key", {"data": "value"})
        >>> cache.get("key")
        {'data': 'value'}
    """

    def __init__(self, ttl: float = DEFAULT_TTL, maxsize: int = DEFAULT_MAXSIZE) -> None:
        """Initialize the cache with specified TTL and maxsize.

        Args:
            ttl: Time-to-live in seconds (default: 300)
            maxsize: Maximum number of cached items (default: 100)
        """
        self._ttl = ttl
        self._maxsize = maxsize
        self._cache: TTLCache[str, tuple[Any, dict[str, Any] | None]] = TTLCache(
            maxsize=maxsize, ttl=ttl
        )
        self._stats = CacheStats()

    @property
    def ttl(self) -> float:
        """Get the TTL for this cache."""
        return self._ttl

    @property
    def maxsize(self) -> int:
        """Get the maximum size of this cache."""
        return self._maxsize

    def get(self, key: str) -> tuple[Any, dict[str, Any] | None] | None:
        """Get a cached response by key.

        Args:
            key: The cache key to look up

        Returns:
            The cached (response, error) tuple, or None if not found/expired
        """
        try:
            result = self._cache[key]
            self._stats.hits += 1
            return result
        except KeyError:
            self._stats.misses += 1
            return None

    def set(self, key: str, value: tuple[Any, dict[str, Any] | None]) -> None:
        """Store a response in the cache.

        Args:
            key: The cache key
            value: The (response, error) tuple to cache
        """
        self._cache[key] = value

    def delete(self, key: str) -> None:
        """Delete a cached entry.

        Args:
            key: The cache key to delete
        """
        try:
            del self._cache[key]
        except KeyError:
            pass  # Key doesn't exist, that's fine

    def clear(self) -> None:
        """Clear all cached entries."""
        self._cache.clear()

    def has(self, key: str) -> bool:
        """Check if a key exists in cache and is not expired.

        Args:
            key: The cache key to check

        Returns:
            True if key exists and is valid, False otherwise
        """
        try:
            _ = self._cache[key]  # noqa: SIM104
            return True
        except KeyError:
            return False

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with hits, misses, hit_rate, and size
        """
        return {
            "hits": self._stats.hits,
            "misses": self._stats.misses,
            "hit_rate": self._stats.hit_rate,
            "size": len(self._cache),
        }


# Global cache instance (singleton)
_cache_instance: APICache | None = None


def get_cache(ttl: float = DEFAULT_TTL, maxsize: int = DEFAULT_MAXSIZE) -> APICache:
    """Get the global cache instance, creating it if necessary.

    Args:
        ttl: Time-to-live in seconds (only used on first call)
        maxsize: Maximum cache size (only used on first call)

    Returns:
        The global APICache instance
    """
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = APICache(ttl=ttl, maxsize=maxsize)
        logger.info(
            "cache_initialized",
            ttl=ttl,
            maxsize=maxsize,
        )
    return _cache_instance


def reset_cache() -> None:
    """Reset the global cache instance.

    This is primarily useful for testing to ensure a clean state.
    """
    global _cache_instance
    _cache_instance = None


async def cached_fetch_xml(
    url: str, params: dict[str, Any] | None = None
) -> tuple[str | None, dict[str, Any] | None]:
    """Fetch XML data with caching.

    This wraps _fetch_xml with caching support:
    1. Check cache for existing response
    2. If cache hit, return cached response
    3. If cache miss, fetch from API and cache the result
    4. Never cache error responses

    Args:
        url: The API endpoint URL
        params: Optional request parameters

    Returns:
        Tuple of (xml_text, None) on success or (None, error_dict) on failure
    """
    cache = get_cache()
    cache_key = generate_cache_key(url, params)

    # Check cache first
    cached = cache.get(cache_key)
    if cached is not None:
        response, error = cached
        # Only return cached successful responses
        if error is None:
            logger.debug(
                "cache_hit",
                cache_key=cache_key[:16],
                url=url,
            )
            return response, error

    # Cache miss - fetch from API
    logger.debug(
        "cache_miss",
        cache_key=cache_key[:16],
        url=url,
    )

    response, error = await _fetch_xml(url)

    # Only cache successful responses
    if error is None and response is not None:
        cache.set(cache_key, (response, error))
        logger.debug(
            "response_cached",
            cache_key=cache_key[:16],
            url=url,
        )

    return response, error


async def cached_fetch_json(
    url: str,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> tuple[dict[str, Any] | list[Any] | None, dict[str, Any] | None]:
    """Fetch JSON data with caching.

    This wraps _fetch_json with caching support:
    1. Check cache for existing response
    2. If cache hit, return cached response
    3. If cache miss, fetch from API and cache the result
    4. Never cache error responses

    Args:
        url: The API endpoint URL
        params: Optional request parameters
        headers: Optional HTTP headers

    Returns:
        Tuple of (json_data, None) on success or (None, error_dict) on failure
    """
    cache = get_cache()
    cache_key = generate_cache_key(url, params)

    # Check cache first
    cached = cache.get(cache_key)
    if cached is not None:
        response, error = cached
        # Only return cached successful responses
        if error is None:
            logger.debug(
                "cache_hit",
                cache_key=cache_key[:16],
                url=url,
            )
            return response, error

    # Cache miss - fetch from API
    logger.debug(
        "cache_miss",
        cache_key=cache_key[:16],
        url=url,
    )

    response, error = await _fetch_json(url, headers)

    # Only cache successful responses
    if error is None and response is not None:
        cache.set(cache_key, (response, error))
        logger.debug(
            "response_cached",
            cache_key=cache_key[:16],
            url=url,
        )

    return response, error
