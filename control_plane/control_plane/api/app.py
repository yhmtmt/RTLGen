"""Minimal dependency-free HTTP app for the control-plane scaffold."""

from __future__ import annotations

from dataclasses import dataclass
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import re
from typing import Callable, Dict, Iterable, Pattern, Tuple
from urllib.parse import urlparse

from control_plane.api.routes_github import register_github_routes
from control_plane.api.routes_health import register_health_routes
from control_plane.api.routes_leases import register_lease_routes
from control_plane.api.routes_queue import register_queue_routes
from control_plane.api.routes_runs import register_run_routes
from control_plane.api.routes_workers import register_worker_routes
from control_plane.config import Settings
from control_plane.logging import configure_logging

Handler = Callable[[str, str, dict[str, str], bytes], Tuple[int, Dict[str, str], bytes]]


@dataclass(frozen=True)
class Route:
    method: str
    path: str
    pattern: Pattern[str]
    handler: Handler


class SimpleAPIApp:
    def __init__(self) -> None:
        self._routes: list[Route] = []

    def add_route(self, method: str, path: str, handler: Handler) -> None:
        pattern = re.sub(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}", r"(?P<\1>[^/]+)", path)
        self._routes.append(
            Route(
                method=method.upper(),
                path=path,
                pattern=re.compile(rf"^{pattern}$"),
                handler=handler,
            )
        )

    def routes(self) -> Iterable[Route]:
        yield from sorted(self._routes, key=lambda route: (route.method, route.path))

    def handle(self, method: str, path: str, body: bytes = b"") -> Tuple[int, Dict[str, str], bytes]:
        for route in self._routes:
            if route.method != method.upper():
                continue
            match = route.pattern.match(path)
            if match is None:
                continue
            return route.handler(method.upper(), path, match.groupdict(), body)
        payload = json.dumps({"detail": "not found", "path": path}).encode("utf-8")
        return 404, {"Content-Type": "application/json"}, payload


def create_app() -> SimpleAPIApp:
    app = SimpleAPIApp()
    register_github_routes(app)
    register_health_routes(app)
    register_queue_routes(app)
    register_lease_routes(app)
    register_run_routes(app)
    register_worker_routes(app)
    return app


class _RequestHandler(BaseHTTPRequestHandler):
    app: SimpleAPIApp

    def _dispatch(self) -> None:
        parsed = urlparse(self.path)
        content_length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(content_length) if content_length > 0 else b""
        status, headers, payload = self.app.handle(self.command, parsed.path, body)
        self.send_response(status)
        for key, value in headers.items():
            self.send_header(key, value)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self) -> None:  # noqa: N802
        self._dispatch()

    def do_POST(self) -> None:  # noqa: N802
        self._dispatch()

    def log_message(self, format: str, *args: object) -> None:  # noqa: A003
        return


def serve(host: str, port: int) -> None:
    app = create_app()

    class BoundHandler(_RequestHandler):
        pass

    BoundHandler.app = app
    httpd = ThreadingHTTPServer((host, port), BoundHandler)
    httpd.serve_forever()


def main(argv: list[str] | None = None) -> int:
    import argparse

    settings = Settings.from_env()
    parser = argparse.ArgumentParser(description="Run the RTLGen control-plane scaffold API")
    parser.add_argument("--host", default=settings.host)
    parser.add_argument("--port", default=settings.port, type=int)
    args = parser.parse_args(argv)
    configure_logging(settings.log_level)
    serve(args.host, args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
