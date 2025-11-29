"""Utility helpers to call the local MCP finance server from smolagents tools."""
from __future__ import annotations

import asyncio
import json
import logging
import sys
import threading
from contextlib import AsyncExitStack
from pathlib import Path
from typing import Any, Dict, Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = logging.getLogger(__name__)

_DEFAULT_SERVER_PATH = Path(__file__).resolve().parents[1] / "server" / "main.py"


class MCPFinanceSession:
    """Manage a long-lived connection to the finance MCP server."""

    def __init__(self, server_path: Optional[Path] = None, command: Optional[str] = None) -> None:
        self._server_path = Path(server_path or _DEFAULT_SERVER_PATH)
        self._command = command or sys.executable
        self._session: Optional[ClientSession] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._started = False
        self._ready_event = threading.Event()
        self._shutdown_event: Optional[asyncio.Event] = None
        self._lifecycle_future = None

    @property
    def server_path(self) -> Path:
        return self._server_path

    def set_server_path(self, new_path: Path) -> None:
        resolved = Path(new_path).resolve()
        if resolved == self._server_path:
            return
        self.close()
        self._server_path = resolved

    def _ensure_started(self) -> None:
        if self._started:
            return
        with self._lock:
            if self._started:
                return
            if not self._server_path.exists():
                raise FileNotFoundError(f"MCP server not found at {self._server_path}")
            self._loop = asyncio.new_event_loop()
            self._thread = threading.Thread(target=self._loop.run_forever, daemon=True)
            self._thread.start()
            self._ready_event.clear()
            self._lifecycle_future = asyncio.run_coroutine_threadsafe(
                self._session_lifecycle(), self._loop
            )
            self._ready_event.wait()
            self._started = True
            logger.debug("Connected to MCP server at %s", self._server_path)

    async def _session_lifecycle(self) -> None:
        try:
            async with AsyncExitStack() as stack:
                params = StdioServerParameters(command=self._command, args=[str(self._server_path)])
                stdio_transport = await stack.enter_async_context(stdio_client(params))
                stdio_read, stdio_write = stdio_transport
                self._session = await stack.enter_async_context(ClientSession(stdio_read, stdio_write))
                await self._session.initialize()
                self._shutdown_event = asyncio.Event()
                self._ready_event.set()
                await self._shutdown_event.wait()
        except Exception:
            self._ready_event.set()
            raise
        finally:
            self._session = None
            self._shutdown_event = None

    async def _async_call_tool(self, tool_name: str, parameters: Dict[str, Any]) -> str:
        assert self._session is not None
        result = await self._session.call_tool(tool_name, parameters)
        if not result.content:
            return "Tool returned no content."
        chunks: list[str] = []
        for item in result.content:
            text = getattr(item, "text", None)
            if text:
                chunks.append(text)
                continue
            as_json = getattr(item, "json", None)
            if as_json is not None:
                chunks.append(json.dumps(as_json, indent=2))
        return "\n".join(chunks).strip()

    def call_tool(self, tool_name: str, parameters: Dict[str, Any]) -> str:
        self._ensure_started()
        assert self._loop is not None
        future = asyncio.run_coroutine_threadsafe(
            self._async_call_tool(tool_name, parameters), self._loop
        )
        return future.result()

    async def _async_signal_shutdown(self) -> None:
        if self._shutdown_event is not None and not self._shutdown_event.is_set():
            self._shutdown_event.set()

    def close(self) -> None:
        if not self._started:
            return
        with self._lock:
            if not self._started:
                return
            assert self._loop is not None
            future = asyncio.run_coroutine_threadsafe(self._async_signal_shutdown(), self._loop)
            future.result()
            if self._lifecycle_future is not None:
                self._lifecycle_future.result()
            self._loop.call_soon_threadsafe(self._loop.stop)
            if self._thread is not None:
                self._thread.join(timeout=5)
            self._loop = None
            self._thread = None
            self._lifecycle_future = None
            self._started = False
            logger.debug("Disconnected from MCP server")


def _resolve_default_path() -> Path:
    return _DEFAULT_SERVER_PATH


_SESSION: Optional[MCPFinanceSession] = None


def configure_session(server_path: Optional[str | Path] = None) -> None:
    """Configure (or reconfigure) the shared MCP session."""
    global _SESSION
    path = Path(server_path).resolve() if server_path else _resolve_default_path()
    if _SESSION is None:
        _SESSION = MCPFinanceSession(path)
    else:
        _SESSION.set_server_path(path)


def get_session() -> MCPFinanceSession:
    global _SESSION
    if _SESSION is None:
        _SESSION = MCPFinanceSession(_resolve_default_path())
    return _SESSION


def shutdown_session() -> None:
    global _SESSION
    if _SESSION is not None:
        _SESSION.close()
        _SESSION = None


import atexit

atexit.register(shutdown_session)
