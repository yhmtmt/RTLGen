"""CLI coverage for process-completions defaults."""

from __future__ import annotations

from unittest.mock import patch

from control_plane.cli import process_completions


def test_process_completions_cli_does_not_force_local_host_by_default() -> None:
    captured: dict[str, object] = {}

    def _fake_create_all(_engine: object) -> None:
        return None

    class _SessionFactory:
        def __call__(self) -> "_SessionFactory":
            return self

        def __enter__(self) -> None:
            return None

        def __exit__(self, exc_type, exc, tb) -> bool:
            return False

    def _fake_process_completed_items(_session: object, request: object) -> list[object]:
        captured["host"] = getattr(request, "host")
        return []

    with (
        patch.object(process_completions, "build_engine", return_value=object()),
        patch.object(process_completions, "create_all", side_effect=_fake_create_all),
        patch.object(process_completions, "build_session_factory", return_value=_SessionFactory()),
        patch.object(process_completions, "process_completed_items", side_effect=_fake_process_completed_items),
    ):
        rc = process_completions.main(
            [
                "--database-url",
                "sqlite+pysqlite:///:memory:",
                "--repo-root",
                "/tmp/repo",
            ]
        )

    assert rc == 0
    assert captured["host"] is None
