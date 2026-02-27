# Implementation Plan: SPEC-CACHE-007

## Overview

API 응답 캐싱 시스템을 구현하여 반복 요청 시 응답 속도를 개선하고 API 호출 횟수를 최적화합니다.

## Priority Milestones

### Primary Goal: Core Implementation

1. **Add `cachetools` Dependency**
   - Update `pyproject.toml` with `cachetools>=5.5.0`
   - Run `uv sync` to install the package

2. **Create `cache_manager.py` Module**
   - Implement `APICache` class using `TTLCache`
   - Create cache key generation function
   - Implement cache wrapper for `_fetch_xml` and `_fetch_json`

3. **Integrate with Existing Code**
   - Wrap `_fetch_xml()` with caching layer
   - Wrap `_fetch_json()` with caching layer
   - Ensure cache bypass for non-cacheable requests

### Secondary Goal: Monitoring & Testing

1. **Cache Statistics**
   - Track cache hits and misses
   - Log cache statistics periodically
   - Expose cache stats for debugging

2. **Unit Tests**
   - Test cache hit scenario
   - Test cache miss and population
   - Test TTL expiration
   - Test cache key generation

## Technical Approach

### Architecture

```
src/real_estate/
├── cache_manager.py         # NEW: Cache management module
│   ├── class APICache
│   ├── function generate_cache_key()
│   └── function cached_fetch()
└── mcp_server/
    └── _helpers.py          # MODIFY: Use cached_fetch
```

### APICache Class Design

```python
from cachetools import TTLCache
from typing import Any, Callable
import hashlib
import structlog

logger = structlog.get_logger()

class APICache:
    """TTL-based cache for API responses.

    Uses cachetools.TTLCache for thread-safe caching with automatic expiration.
    """

    def __init__(
        self,
        maxsize: int = 100,
        ttl: float = 300.0,  # 5 minutes
    ):
        self._cache: TTLCache[str, Any] = TTLCache(
            maxsize=maxsize,
            ttl=ttl,
        )
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> tuple[Any | None, bool]:
        """Get value from cache.

        Returns:
            Tuple of (value, found) where found indicates cache hit
        """
        try:
            value = self._cache[key]
            self._hits += 1
            logger.debug("cache_hit", key=key[:16])
            return value, True
        except KeyError:
            self._misses += 1
            return None, False

    def set(self, key: str, value: Any) -> None:
        """Store value in cache."""
        self._cache[key] = value
        logger.debug("cache_set", key=key[:16], cache_size=len(self._cache))

    @property
    def stats(self) -> dict[str, Any]:
        """Return cache statistics."""
        total = self._hits + self._misses
        hit_rate = self._hits / total if total > 0 else 0.0
        return {
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": hit_rate,
            "size": len(self._cache),
            "maxsize": self._cache.maxsize,
        }


def generate_cache_key(url: str, params: dict[str, Any] | None = None) -> str:
    """Generate a unique cache key from URL and parameters.

    Uses SHA256 hash for consistent key length.
    """
    key_parts = [url]
    if params:
        # Sort params for consistent ordering
        sorted_params = sorted(params.items())
        key_parts.extend(f"{k}={v}" for k, v in sorted_params)

    key_string = "|".join(key_parts)
    return hashlib.sha256(key_string.encode()).hexdigest()


# Global cache instance
_api_cache = APICache()
```

### Integration Pattern

```python
# In _helpers.py

from real_estate.cache_manager import _api_cache, generate_cache_key

async def _fetch_xml(url: str) -> tuple[str | None, dict[str, Any] | None]:
    """Perform an async HTTP GET with caching, retry, and circuit breaker."""
    # Generate cache key
    cache_key = generate_cache_key(url)

    # Check cache first
    cached, found = _api_cache.get(cache_key)
    if found:
        logger.debug("cache_return", url=url)
        return cached, None

    # ... existing fetch logic ...

    # On success, cache the response
    if xml_text:
        _api_cache.set(cache_key, xml_text)

    return xml_text, error
```

### Cache Invalidation Strategy

- **TTL-based**: Automatic expiration after 5 minutes
- **Size-based**: LRU eviction when maxsize (100) reached
- **Manual**: Optional `clear_cache()` function for forced refresh

## Dependencies

### New Dependency
- `cachetools>=5.5.0` - To be added to pyproject.toml

### Existing Dependencies
- `structlog>=25.5.0` - For cache logging
- `tenacity>=9.1.2` - For retry logic (unchanged)

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Stale data | TTL set to 5 minutes for balance |
| Memory growth | LRU eviction with maxsize limit |
| Thread safety | cachetools.TTLCache is thread-safe |
| Cache key collision | SHA256 hash provides low collision rate |

## File Changes Summary

| File | Action | Description |
|------|--------|-------------|
| `pyproject.toml` | MODIFY | Add cachetools>=5.5.0 |
| `src/real_estate/cache_manager.py` | CREATE | Cache management module |
| `src/real_estate/mcp_server/_helpers.py` | MODIFY | Integrate caching |
| `tests/test_cache_manager.py` | CREATE | Cache unit tests |
