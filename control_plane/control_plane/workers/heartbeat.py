"""Lease heartbeat helpers for the internal worker loop."""

from __future__ import annotations

from dataclasses import dataclass, field
import threading
import time
from typing import Any

from sqlalchemy.orm import sessionmaker

from control_plane.services.lease_service import heartbeat_lease


@dataclass
class LeaseHeartbeatPump:
    session_factory: sessionmaker
    lease_token: str
    heartbeat_seconds: int = 30
    extend_seconds: int = 1800
    _thread: threading.Thread | None = field(init=False, default=None)
    _stop_event: threading.Event = field(init=False, default_factory=threading.Event)
    _lock: threading.Lock = field(init=False, default_factory=threading.Lock)
    _progress: dict[str, Any] | None = field(init=False, default=None)
    _last_error: str | None = field(init=False, default=None)

    def start(self) -> None:
        if self._thread is not None:
            return
        self._thread = threading.Thread(target=self._run, name=f"lease-heartbeat-{self.lease_token}", daemon=True)
        self._thread.start()

    def update_progress(self, progress: dict[str, Any]) -> None:
        with self._lock:
            self._progress = progress

    def stop(self) -> str | None:
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=self.heartbeat_seconds + 1)
        return self._last_error

    def _current_progress(self) -> dict[str, Any] | None:
        with self._lock:
            if self._progress is None:
                return None
            return dict(self._progress)

    def _run(self) -> None:
        while not self._stop_event.wait(self.heartbeat_seconds):
            try:
                with self.session_factory() as session:
                    heartbeat_lease(
                        session,
                        lease_token=self.lease_token,
                        extend_seconds=self.extend_seconds,
                        progress=self._current_progress(),
                    )
            except Exception as exc:  # pragma: no cover - best effort background reporting
                self._last_error = str(exc)
                break
