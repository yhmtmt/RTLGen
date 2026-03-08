"""Configuration helpers for the control-plane scaffold."""

from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    app_name: str = "rtlgen-control-plane"
    app_version: str = "0.1.0"
    host: str = "127.0.0.1"
    port: int = 8080
    database_url: str = "postgresql://rtlgen:rtlgen@localhost:5432/rtlgen_control_plane"
    log_level: str = "INFO"

    @staticmethod
    def from_env() -> "Settings":
        return Settings(
            app_name=os.getenv("RTLCP_APP_NAME", "rtlgen-control-plane"),
            app_version=os.getenv("RTLCP_APP_VERSION", "0.1.0"),
            host=os.getenv("RTLCP_HOST", "127.0.0.1"),
            port=int(os.getenv("RTLCP_PORT", "8080")),
            database_url=os.getenv(
                "RTLCP_DATABASE_URL",
                "postgresql://rtlgen:rtlgen@localhost:5432/rtlgen_control_plane",
            ),
            log_level=os.getenv("RTLCP_LOG_LEVEL", "INFO"),
        )
