from pathlib import Path
from unittest.mock import MagicMock, patch

from control_plane.services.run_index_exporter import RUNS_INDEX_FIELDNAMES, refresh_run_index


def test_refresh_run_index_uses_tracked_metrics_only(tmp_path: Path) -> None:
    script_path = tmp_path / "scripts" / "build_runs_index.py"
    script_path.parent.mkdir(parents=True)
    script_path.write_text("# placeholder\n", encoding="utf-8")
    index_path = tmp_path / "runs" / "index.csv"
    index_path.parent.mkdir(parents=True)
    index_path.write_text(",".join(RUNS_INDEX_FIELDNAMES) + "\n", encoding="utf-8")
    session = MagicMock()

    with patch("control_plane.services.run_index_exporter.subprocess.run") as run:
        result = refresh_run_index(session, repo_root=str(tmp_path))

    run.assert_called_once_with(
        ["python3", str(script_path), "--tracked-only"],
        cwd=str(tmp_path),
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.row_count == 0
    session.flush.assert_called_once_with()
