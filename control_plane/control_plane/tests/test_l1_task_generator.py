"""Layer 1 task generation coverage."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from control_plane.db import create_all
from control_plane.models.enums import WorkItemState
from control_plane.models.work_items import WorkItem
from control_plane.services.l1_task_generator import (
    Layer1SweepGenerateRequest,
    Layer1TaskGenerationError,
    generate_l1_sweep_task,
)


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


def _write_example_block_repo(
    repo_root: Path,
    *,
    mode_compare: bool = True,
    synth_hierarchical: int | None = None,
) -> tuple[str, str]:
    design_dir = repo_root / "runs" / "designs" / "npu_blocks" / "npu_fp16_cpp_nm1_sigmoidcmp"
    design_dir.mkdir(parents=True, exist_ok=True)
    config_path = design_dir / "config_nm1_sigmoid.json"
    config_path.write_text(
        json.dumps(
            {
                "version": "0.1",
                "top_name": "npu_top",
                "mmio_addr_width": 12,
                "compute": {
                    "enabled": True,
                    "gemm": {"mac_type": "fp16", "lanes": 1, "accum_width": 16},
                    "vec": {"lanes": 1, "ops": ["add", "mul", "relu", "sigmoid"]},
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    flow_params = {
        "CLOCK_PERIOD": [10.0],
        "DIE_AREA": ["0 0 1500 1500"],
        "CORE_AREA": ["50 50 1450 1450"],
    }
    if synth_hierarchical is not None:
        flow_params["SYNTH_HIERARCHICAL"] = [synth_hierarchical]
    sweep_payload = {
        "flow_params": flow_params,
        "tag_prefix": "npu_fp16_nm1_sigmoidcmp",
    }
    if mode_compare:
        sweep_payload["mode_compare"] = True

    sweep_path = design_dir / "sweep_compare_33.json"
    sweep_path.write_text(
        json.dumps(sweep_payload, indent=2) + "\n",
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
                    abstraction_layer="circuit_block",
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
            assert work_item.command_manifest[0]["run"] == (
                "export PATH=/oss-cad-suite/bin:$PATH && "
                "cmake -S . -B build && cmake --build build --target rtlgen"
            )
            assert "--skip_existing" in work_item.command_manifest[1]["run"]
            assert work_item.command_manifest[1]["run"].startswith(
                "export PATH=/oss-cad-suite/bin:$PATH && python3 scripts/run_sweep.py "
            )
            assert work_item.command_manifest[3]["run"] == "python3 scripts/validate_runs.py --skip_eval_queue"
            assert work_item.expected_outputs == [
                "runs/designs/activations/softmax_rowwise_int8_r4_wrapper/metrics.csv",
                "runs/index.csv",
            ]
            payload = work_item.task_request.request_payload
            assert payload["layer"] == "layer1"
            assert payload["task"]["inputs"]["sweeps"] == [sweep_path]
            assert payload["task"]["inputs"]["required_submodules"] == [
                "third_party/nlohmann_json",
                "third_party/cacti",
            ]
            assert payload["developer_loop"]["abstraction"] == {"layer": "circuit_block"}
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


def test_generate_l1_sweep_task_supports_integrated_npu_block_configs() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        config_path, sweep_path = _write_example_block_repo(repo_root)
        proposal_dir = repo_root / "docs" / "developer_loop" / "prop_l1_npu_nm1_sigmoid_vec_enable_v1"
        proposal_dir.mkdir(parents=True, exist_ok=True)
        (proposal_dir / "proposal.json").write_text(
            json.dumps({"proposal_id": "prop_l1_npu_nm1_sigmoid_vec_enable_v1", "abstraction_layer": "architecture_block"}, indent=2) + "\n",
            encoding="utf-8",
        )
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
                    out_root="runs/designs/npu_blocks",
                    requested_by="@tester",
                    source_commit="sig123",
                    proposal_id="prop_l1_npu_nm1_sigmoid_vec_enable_v1",
                    proposal_path="docs/developer_loop/prop_l1_npu_nm1_sigmoid_vec_enable_v1",
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            assert result.status == "applied"
            assert work_item.task_type == "l1_sweep"
            assert work_item.state == WorkItemState.READY
            assert [command["name"] for command in work_item.command_manifest] == [
                "build_generator",
                "generate_block_rtl",
                "run_block_sweep",
                "build_runs_index",
                "validate",
            ]
            assert work_item.command_manifest[0]["run"] == (
                "export PATH=/oss-cad-suite/bin:$PATH && "
                "cmake -S . -B build && cmake --build build --target rtlgen"
            )
            assert work_item.command_manifest[1]["run"] == (
                "export PATH=/oss-cad-suite/bin:$PATH && "
                "python3 npu/rtlgen/gen.py "
                "--config runs/designs/npu_blocks/npu_fp16_cpp_nm1_sigmoidcmp/config_nm1_sigmoid.json "
                "--out runs/designs/npu_blocks/npu_fp16_cpp_nm1_sigmoidcmp/verilog"
            )
            assert work_item.command_manifest[2]["run"] == (
                "export PATH=/oss-cad-suite/bin:$PATH && "
                "python3 npu/synth/run_block_sweep.py "
                "--design_dir runs/designs/npu_blocks/npu_fp16_cpp_nm1_sigmoidcmp "
                "--platform nangate45 "
                "--top npu_top "
                "--sweep runs/designs/npu_blocks/npu_fp16_cpp_nm1_sigmoidcmp/sweep_compare_33.json "
                "--skip_existing"
            )
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {"layer": "architecture_block"}

def test_generate_l1_sweep_task_rejects_flattened_architecture_block_sweeps() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        config_path, sweep_path = _write_example_block_repo(repo_root)
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            try:
                generate_l1_sweep_task(
                    session,
                    Layer1SweepGenerateRequest(
                        repo_root=str(repo_root),
                        sweep_path=sweep_path,
                        config_paths=[config_path],
                        platform="nangate45",
                        out_root="runs/designs/npu_blocks",
                        requested_by="@tester",
                        abstraction_layer="architecture_block",
                    ),
                )
            except Layer1TaskGenerationError as exc:
                assert "architecture_block sweeps must not use mode_compare/flat_nomacro" in str(exc)
            else:
                raise AssertionError("expected Layer1TaskGenerationError for flattened architecture_block sweep")


def test_generate_l1_sweep_task_supports_make_target_for_integrated_blocks() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        config_path, sweep_path = _write_example_block_repo(repo_root)
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
                    out_root="runs/designs/npu_blocks",
                    requested_by="@tester",
                    source_commit="sig123",
                    proposal_id="prop_l1_npu_nm1_sigmoid_vec_enable_v1",
                    proposal_path="docs/developer_loop/prop_l1_npu_nm1_sigmoid_vec_enable_v1/proposal.json",
                    make_target="1_1_yosys_canonicalize",
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            assert "--make_target 1_1_yosys_canonicalize" in work_item.command_manifest[2]["run"]
            assert work_item.expected_outputs == [
                "runs/designs/npu_blocks/npu_fp16_cpp_nm1_sigmoidcmp/metrics.csv",
                "runs/index.csv",
            ]
            assert work_item.task_request.request_payload["developer_loop"]["evaluation"]["mode"] == "synth_prefilter"


def test_generate_l1_sweep_task_accepts_hierarchical_architecture_block_sweeps() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        config_path, sweep_path = _write_example_block_repo(
            repo_root,
            mode_compare=False,
            synth_hierarchical=1,
        )
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
                    out_root="runs/designs/npu_blocks",
                    requested_by="@tester",
                    source_commit="sig123",
                    abstraction_layer="architecture_block",
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            assert result.status == "applied"
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "architecture_block"
            }
            assert "--sweep runs/designs/npu_blocks/npu_fp16_cpp_nm1_sigmoidcmp/sweep_compare_33.json" in work_item.command_manifest[2]["run"]


def test_generate_l1_sweep_task_defaults_source_commit_from_repo_head() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        config_path, sweep_path = _write_example_repo(repo_root)
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with patch("control_plane.services.l1_task_generator.subprocess.run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=["git", "-C", str(repo_root), "rev-parse", "HEAD"],
                returncode=0,
                stdout="deadbeefcafefeed\n",
                stderr="",
            )
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
                    ),
                )

                work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
                assert work_item.source_commit == "deadbeefcafefeed"
                assert work_item.task_request.source_commit == "deadbeefcafefeed"
                mock_run.assert_called_once()


def test_generate_l1_sweep_task_accepts_explicit_hierarchical_architecture_block_sweeps() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        config_path, sweep_path = _write_example_block_repo(repo_root, mode_compare=False, synth_hierarchical=1)
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
                    out_root="runs/designs/npu_blocks",
                    requested_by="@tester",
                    source_commit="sig123",
                    proposal_id="prop_l1_npu_nm1_sigmoid_vec_enable_v1",
                    proposal_path="docs/developer_loop/prop_l1_npu_nm1_sigmoid_vec_enable_v1",
                    abstraction_layer="architecture_block",
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            assert result.status == "applied"
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {"layer": "architecture_block"}
