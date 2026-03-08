"""Worker routes placeholder for Phase 1."""

from __future__ import annotations

import json


def register_worker_routes(app) -> None:
    def not_implemented(_method: str, _path: str, _params: dict[str, str], _body: bytes):
        body = json.dumps({"detail": "worker API not implemented in cp-004"}).encode("utf-8")
        return 501, {"Content-Type": "application/json"}, body

    app.add_route("GET", "/api/v1/workers", not_implemented)
