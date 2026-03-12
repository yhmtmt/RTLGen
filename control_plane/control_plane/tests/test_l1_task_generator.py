"""Layer 1 task generation coverage."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from control_plane.db import create_all
from control_plane.models.enums import WorkItemState
from control_plane.models.work_items import WorkItem
from control_plane.services.l1_task_generator import Layer1SweepGenerateRequest, generate_l1_sweep_task


def _write_example_repo(repo_root: Path) -> tuple[str, str]:
    config_path = repo_root / "examples" / "config_softmax_rowwise_int8.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        json.dumps(
            {
                "version": "1.1",
                "operations": [
                    {
                        "type": "softmax_rowwise",
                        "module_name": "softmax_rowwise_int8_r4",
                        "operand": "logits",
                        "options": {
                            "impl": "shift_exp",
                            "row_elems": 4,
                            "max_shift": 7,
                            "accum_bits": 16,
                            "output_scale": 127,
                        },
                    }
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    sweep_path = repo_root / "runs" / "designs" / "activations" / "sweeps" / "nangate45_softmax_rowwise_v1.json"
    sweep_path.parent.mkdir(parents=True, exist_ok=True)
    sweep_path.write_text(
        json.dumps(
            {
                "flow_params": {
                    "CLOCK_PERIOD": [6.0],
                    "CORE_UTILIZATION": [45],
                },
                "tag_prefix": "softmax_rowwise_ng45_v1",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return (
        str(config_path.relative_to(repo_root)),
        str(sweep_path.relative_to(repo_root)),
    )


def test_generate_l1_sweep_task_creates_ready_work_item() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        config_path, sweep_path = _write_example_repo(repo_root)
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            result = generate_l1_sweep_task(
                session,
                Layer1SweepGenerateRequest(
                    repo_root=str(repo_root),
                    sweep_path=sweep_path,
                    config_paths=[config_path],
                    platform="nangate45",
                    out_root="runs/designs/activations",
                    requested_by="@tester",
                    source_commit="abc123",
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            assert result.status == "applied"
            assert work_item.task_type == "l1_sweep"
            assert work_item.state == WorkItemState.READY
            assert work_item.source_mode == "config"
            assert [command["name"] for command in work_item.command_manifest] == [
                "build_generator",
                "run_sweep",
                "build_runs_index",
                "validate",
            ]
            assert "--skip_existing" in work_item.command_manifest[1]["run"]
            assert work_item.command_manifest[3]["run"] == "python3 scripts/validate_runs.py --skip_eval_queue"
            assert work_item.expected_outputs == [
                "runs/designs/activations/softmax_rowwise_int8_r4_wrapper/metrics.csv",
                "runs/index.csv",
            ]
            payload = work_item.task_request.request_payload
            assert payload["layer"] == "layer1"
            assert payload["task"]["inputs"]["sweeps"] == [sweep_path]
            assert payload["task"]["inputs"]["required_submodules"] == ["third_party/cacti"]
            assert payload["handoff"]["pr_body_fields"]["queue_item_id"] == result.item_id


def test_generate_l1_sweep_task_upserts_existing_item() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        config_path, sweep_path = _write_example_repo(repo_root)
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            first = generate_l1_sweep_task(
                session,
                Layer1SweepGenerateRequest(
                    repo_root=str(repo_root),
                    sweep_path=sweep_path,
                    config_paths=[config_path],
                    platform="nangate45",
                    out_root="runs/designs/activations",
                    item_id="l1_demo_softmax",
                    title="Layer1 demo",
                    requested_by="@tester",
                ),
            )
            second = generate_l1_sweep_task(
                session,
                Layer1SweepGenerateRequest(
                    repo_root=str(repo_root),
                    sweep_path=sweep_path,
                    config_paths=[config_path],
                    platform="nangate45",
                    out_root="runs/designs/activations",
                    item_id="l1_demo_softmax",
                    title="Layer1 demo updated",
                    requested_by="@tester2",
                ),
            )

            assert first.status == "applied"
            assert second.status == "applied"
            work_item = session.query(WorkItem).filter_by(item_id="l1_demo_softmax").one()
            assert work_item.task_request.title == "Layer1 demo updated"
            assert work_item.task_request.requested_by == "@tester2"
