"""Health routes for the scaffold API."""

from __future__ import annotations

import json

from control_plane.api.deps import get_settings


def register_health_routes(app) -> None:
    settings = get_settings()

    def health_handler(_method: str, _path: str, _params: dict[str, str], _body: bytes):
        body = json.dumps(
            {
                "status": "ok",
                "service": settings.app_name,
                "version": settings.app_version,
            }
        ).encode("utf-8")
        return 200, {"Content-Type": "application/json"}, body

    app.add_route("GET", "/healthz", health_handler)
