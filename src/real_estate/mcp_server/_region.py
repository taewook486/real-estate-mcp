"""Legal district code lookup and region/time tools for the MCP server.

This module provides:
- Memory caching for region codes (loaded once, reused)
- Structured JSON logging for API requests and errors
- Region code search functionality
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, TypedDict

import structlog

logger = structlog.get_logger()

REGION_FILE = Path(__file__).parent.parent / "resources" / "region_codes.txt"


class RegionMatch(TypedDict):
    """A single match result."""

    code: str  # Original 10-digit code
    name: str


class RegionResult(TypedDict, total=False):
    """Return type of search_region_code."""

    region_code: str  # 5-digit code for the API parameter
    full_name: str
    matches: list[RegionMatch]
    error: str
    message: str


# ---------------------------------------------------------------------------
# Memory cache for region codes
# ---------------------------------------------------------------------------

# Module-level cache for region rows
_region_rows_cache: list[tuple[str, str]] | None = None
_cache_load_time: float | None = None


def _load_region_rows() -> list[tuple[str, str]]:
    """Load (code, name) rows from the region code file with caching.

    The region codes are loaded once and cached in memory for subsequent calls.
    This reduces file I/O overhead and improves performance.

    Returns:
        List of (code, name) tuples for existing regions
    """
    global _region_rows_cache, _cache_load_time

    # Return cached data if available
    if _region_rows_cache is not None:
        logger.debug(
            "region_cache_hit",
            cache_age_seconds=time.time() - (_cache_load_time or 0),
            cached_rows=len(_region_rows_cache),
        )
        return _region_rows_cache

    start_time = time.time()
    rows: list[tuple[str, str]] = []

    try:
        with REGION_FILE.open(encoding="utf-8") as f:
            next(f)  # skip header
            for line in f:
                parts = line.rstrip("\n").split("\t")
                if len(parts) < 3:
                    continue
                code, name, status = parts[0], parts[1], parts[2]
                if status == "존재":
                    rows.append((code, name))

        # Cache the loaded rows
        _region_rows_cache = rows
        _cache_load_time = time.time()

        load_duration_ms = (time.time() - start_time) * 1000
        logger.info(
            "region_cache_loaded",
            rows_count=len(rows),
            load_duration_ms=load_duration_ms,
            file_path=str(REGION_FILE),
        )

    except FileNotFoundError as exc:
        logger.error(
            "region_file_not_found",
            file_path=str(REGION_FILE),
            error=str(exc),
        )
        raise

    return rows


def _to_api_code(ten_digit: str) -> str:
    """Convert 10-digit code to 5-digit API code."""
    return ten_digit[:5]


def _is_gu_gun(ten_digit: str) -> bool:
    """Check if code represents a gu/gun level (last 5 digits are 00000)."""
    return ten_digit[5:] == "00000"


def _reset_region_cache() -> None:
    """Reset the region cache (for testing)."""
    global _region_rows_cache, _cache_load_time
    _region_rows_cache = None
    _cache_load_time = None


def search_region_code(query: str) -> dict[str, Any]:
    """Convert a free-form region name to a legal district code.

    Args:
        query: Region name to search for (e.g., "마포구", "서울 마포구")

    Returns:
        Dictionary with region_code, full_name, matches on success
        Dictionary with error, message on failure
    """
    request_id = f"region_{int(time.time() * 1000) % 1000000:06d}"
    start_time = time.time()

    query = query.strip()
    if not query:
        logger.warning(
            "region_search_empty_query",
            request_id=request_id,
        )
        return {"error": "invalid_input", "message": "Region name must not be empty."}

    logger.info(
        "region_search_start",
        request_id=request_id,
        query=query,
    )

    try:
        rows = _load_region_rows()
    except FileNotFoundError:
        logger.error(
            "region_search_file_not_found",
            request_id=request_id,
            query=query,
            file_path=str(REGION_FILE),
        )
        return {"error": "file_not_found", "message": "Region code file not found."}

    tokens = query.split()
    matched = [(code, name) for code, name in rows if all(tok in name for tok in tokens)]

    if not matched:
        duration_ms = (time.time() - start_time) * 1000
        logger.info(
            "region_search_no_match",
            request_id=request_id,
            query=query,
            duration_ms=duration_ms,
        )
        return {
            "error": "no_match",
            "message": f"No region found for: {query}",
        }

    matched.sort(key=lambda x: (not _is_gu_gun(x[0]), x[0]))

    matches: list[RegionMatch] = [{"code": c, "name": n} for c, n in matched]

    gu_gun = [(c, n) for c, n in matched if _is_gu_gun(c)]
    best_code, best_name = gu_gun[0] if gu_gun else matched[0]

    duration_ms = (time.time() - start_time) * 1000
    logger.info(
        "region_search_success",
        request_id=request_id,
        query=query,
        region_code=_to_api_code(best_code),
        full_name=best_name,
        match_count=len(matches),
        duration_ms=duration_ms,
    )

    return {
        "region_code": _to_api_code(best_code),
        "full_name": best_name,
        "matches": matches,
    }
