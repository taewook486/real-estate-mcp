from __future__ import annotations

import sys
from typing import Any

from real_estate.mcp_server import server


def test_main_http_defaults_to_localhost(monkeypatch: Any) -> None:
    monkeypatch.setattr(sys, "argv", ["server", "--transport", "http"])

    # Mock uvicorn.run to prevent actual server startup (must patch at module level)
    import uvicorn

    monkeypatch.setattr(uvicorn, "run", lambda *args, **kwargs: None)

    server.main()

    # HTTP mode: verify settings are configured correctly
    assert server.mcp.settings.host == "127.0.0.1"
    assert server.mcp.settings.port == 8000


def test_main_stdio_defaults_to_mcp_run(monkeypatch: Any) -> None:
    monkeypatch.setattr(sys, "argv", ["server"])

    calls: list[str] = []

    def _fake_run(*, transport: str | None = None) -> None:
        calls.append(transport or "stdio")

    monkeypatch.setattr(server.mcp, "run", _fake_run)

    server.main()

    # stdio mode: verify mcp.run() was called
    assert calls == ["stdio"]
