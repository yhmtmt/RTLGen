"""Layer 2 generation CLI coverage."""

from __future__ import annotations

from control_plane.cli import generate_l2_campaign
from control_plane.services.l2_task_generator import Layer2TaskGenerateResult


class _SessionContext:
    def __enter__(self) -> object:
        return object()

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        return None


def test_generate_l2_campaign_cli_omitted_dependencies_remain_unspecified(monkeypatch) -> None:
    captured = {}

    monkeypatch.setattr(generate_l2_campaign, "build_engine", lambda _database_url: object())
    monkeypatch.setattr(generate_l2_campaign, "create_all", lambda _engine: None)
    monkeypatch.setattr(generate_l2_campaign, "build_session_factory", lambda _engine: _SessionContext)

    def fake_generate(_session: object, request: object) -> Layer2TaskGenerateResult:
        captured["depends_on_item_ids"] = request.depends_on_item_ids
        return Layer2TaskGenerateResult(
            item_id="l2_demo",
            status="applied",
            work_item_id="wi",
            task_request_id="tr",
        )

    monkeypatch.setattr(generate_l2_campaign, "generate_l2_campaign_task", fake_generate)

    result = generate_l2_campaign.main(
        [
            "--database-url",
            "sqlite+pysqlite:///:memory:",
            "--repo-root",
            "/tmp/repo",
            "--campaign-path",
            "runs/campaigns/demo/campaign.json",
            "--item-id",
            "l2_demo",
            "--no-auto-dispatch",
        ]
    )

    assert result == 0
    assert captured["depends_on_item_ids"] is None

