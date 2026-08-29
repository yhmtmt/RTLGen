"""Layer 1 task generation coverage."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import tempfile
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from control_plane.clock import utcnow
from control_plane.db import create_all
from control_plane.models.artifacts import Artifact
from control_plane.models.enums import RunStatus, WorkItemState
from control_plane.models.runs import Run
from control_plane.models.task_requests import TaskRequest
from control_plane.models.work_items import WorkItem
from control_plane.services.dependency_gate import refresh_all_blocked_items
from control_plane.services.l1_task_generator import (
    Layer1ConfigTarget,
    Layer1SweepGenerateRequest,
    Layer1TaskGenerationError,
    _multivalue_cluster_binary_fsm_profile,
    _read_config_target,
    _resolve_required_complete_ppa_rows,
    _synth_only_targets,
    _validate_requested_expected_outputs,
    _validate_replacement_sweep_isolation,
    generate_l1_sweep_task,
)


@pytest.mark.parametrize("value", [True, "three", "03", -1])
def test_required_complete_ppa_rows_rejects_malformed_values(value: object) -> None:
    with pytest.raises(
        Layer1TaskGenerationError,
        match="required_complete_ppa_rows must be a non-negative integer",
    ):
        _resolve_required_complete_ppa_rows({"required_complete_ppa_rows": value})


def test_requested_expected_outputs_reject_noncanonical_sweep_root() -> None:
    with pytest.raises(Layer1TaskGenerationError, match="check --out-root"):
        _validate_requested_expected_outputs(
            requested_entry={
                "expected_outputs": [
                    "runs/designs/noc/router_wrapper/metrics.csv",
                ]
            },
            generated_outputs=[
                "runs/designs/noc/router_wrapper/router_wrapper/metrics.csv",
            ],
        )


def test_requested_expected_outputs_allow_additional_diagnostics() -> None:
    _validate_requested_expected_outputs(
        requested_entry={
            "expected_outputs": [
                "runs/designs/noc/router_wrapper/metrics.csv",
            ]
        },
        generated_outputs=[
            "runs/designs/noc/router_wrapper/metrics.csv",
            "runs/designs/noc/router_wrapper/timing_debug_report.md",
        ],
    )


def test_replacement_sweep_requires_revision_specific_artifact_identity(tmp_path: Path) -> None:
    sweep_path = "retry.json"
    (tmp_path / sweep_path).write_text(
        json.dumps({"flow_params": {"CLOCK_PERIOD": [1.0]}}),
        encoding="utf-8",
    )

    with pytest.raises(Layer1TaskGenerationError, match="must isolate evaluator work artifacts"):
        _validate_replacement_sweep_isolation(
            repo_root=tmp_path,
            sweep_path=sweep_path,
            requested_entry={
                "item_id": "demo_r2",
                "revision": {"supersedes_item_ids": ["demo"]},
            },
        )


def test_replacement_sweep_accepts_base_or_per_mode_artifact_identity(tmp_path: Path) -> None:
    entry = {
        "item_id": "demo_r2",
        "revision": {"supersedes_item_ids": ["demo"]},
    }
    base_path = "base.json"
    (tmp_path / base_path).write_text(
        json.dumps(
            {
                "flow_params": {
                    "CLOCK_PERIOD": [1.0],
                    "FLOW_VARIANT": ["demo_r2"],
                }
            }
        ),
        encoding="utf-8",
    )
    _validate_replacement_sweep_isolation(
        repo_root=tmp_path,
        sweep_path=base_path,
        requested_entry=entry,
    )

    modes_path = "modes.json"
    (tmp_path / modes_path).write_text(
        json.dumps(
            {
                "flow_params": {"CLOCK_PERIOD": [1.0]},
                "mode_compare": {
                    "modes": [
                        {"param_overrides": {"FLOW_VARIANT": "demo_r2_flat"}},
                        {"param_overrides": {"FLOW_VARIANT": "demo_r2_hier"}},
                    ]
                },
            }
        ),
        encoding="utf-8",
    )
    _validate_replacement_sweep_isolation(
        repo_root=tmp_path,
        sweep_path=modes_path,
        requested_entry=entry,
    )


def test_synth_only_target_keeps_prerequisite_make_target_commands() -> None:
    target = Layer1ConfigTarget(
        design_kind="block",
        design_name="demo",
        expected_metrics_path="runs/designs/demo/metrics.csv",
        expected_report_paths=["runs/designs/demo/timing.md"],
        additional_expected_outputs=["runs/designs/demo/macro/metrics.csv"],
        commands=[
            {"name": "harden_macro", "run": "tool --make_target generate_abstract"},
            {"name": "run_block_sweep", "run": "sweep --make_target 1_2_yosys"},
            {"name": "extract_timing", "run": "extract timing"},
        ],
    )

    result = _synth_only_targets([target], make_target="1_2_yosys")

    assert [command["name"] for command in result[0].commands] == [
        "harden_macro",
        "run_block_sweep",
    ]
    assert result[0].expected_report_paths == []
    assert result[0].additional_expected_outputs == ["runs/designs/demo/macro/metrics.csv"]


def test_read_config_target_builds_shared_sram_adapter_remote_commands(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    design_dir = repo_root / "runs/designs/npu_blocks/attention_shared_sram_read_group_adapter_w256_s2"
    design_dir.mkdir(parents=True)
    config_path = design_dir / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "top_name": design_dir.name,
                "attention_shared_sram_read_group_adapter_ppa_harness": {
                    "beat_width": 256,
                    "group_slots": 2,
                    "groups": 64,
                },
            }
        ),
        encoding="utf-8",
    )
    config_rel = str(config_path.relative_to(repo_root))
    target = _read_config_target(
        config_path,
        repo_root=repo_root,
        config_rel=config_rel,
        out_root="runs/designs/npu_blocks",
        make_target=None,
    )
    assert target.design_name == design_dir.name
    assert target.expected_metrics_path == f"runs/designs/npu_blocks/{design_dir.name}/metrics.csv"
    assert [command["name"] for command in target.commands] == [
        "generate_attention_shared_sram_read_group_adapter_ppa_harness_rtl",
        "check_attention_shared_sram_read_group_adapter_ppa_guard",
        "run_block_sweep",
        "extract_attention_shared_sram_read_group_adapter_ppa_harness_timing_paths",
    ]
    assert "gen_attention_shared_sram_read_group_adapter_ppa_harness.py" in target.commands[0]["run"]
    assert "check_attention_shared_sram_read_group_adapter_ppa_guard.py" in target.commands[1]["run"]
    assert "--top attention_shared_sram_read_group_adapter_w256_s2" in target.commands[2]["run"]


def test_read_config_target_records_memory_noc_timing_path_identity(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    design_dir = repo_root / "runs/designs/noc/endpoint"
    design_dir.mkdir(parents=True)
    config_path = design_dir / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "version": "1.1",
                "operands": [
                    {
                        "name": "flit",
                        "bit_width": 256,
                        "signed": False,
                        "kind": "int",
                    }
                ],
                "operations": [
                    {
                        "type": "l1_memory_noc_primitive",
                        "module_name": "noc_endpoint",
                        "operand": "flit",
                        "options": {"primitive": "sram_packet_endpoint"},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    target = _read_config_target(
        config_path,
        repo_root=repo_root,
        config_rel=str(config_path.relative_to(repo_root)),
        out_root="runs/designs/noc",
        make_target=None,
    )

    assert [command["name"] for command in target.commands] == [
        "build_generator",
        "run_sweep",
        "extract_l1_memory_noc_primitive_timing_paths",
    ]
    assert target.expected_report_paths == [
        "runs/designs/noc/noc_endpoint_wrapper/timing_debug_report.md"
    ]
    assert "--design-dir runs/designs/noc/noc_endpoint_wrapper" in target.commands[2]["run"]


def test_read_config_target_builds_shared_sram_k_round_scheduler_commands(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    design_dir = repo_root / "runs/designs/npu_blocks/attention_shared_sram_k_round_scheduler_b17_w17"
    design_dir.mkdir(parents=True)
    config_path = design_dir / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "top_name": design_dir.name,
                "attention_shared_sram_k_round_scheduler_ppa_harness": {
                    "banks": 17,
                    "words_per_group": 128,
                    "dimension_groups": 8,
                    "dimensions_per_group": 16,
                },
            }
        ),
        encoding="utf-8",
    )
    config_rel = str(config_path.relative_to(repo_root))
    target = _read_config_target(
        config_path,
        repo_root=repo_root,
        config_rel=config_rel,
        out_root="runs/designs/npu_blocks",
        make_target=None,
    )
    assert target.design_name == design_dir.name
    assert target.expected_metrics_path == f"runs/designs/npu_blocks/{design_dir.name}/metrics.csv"
    assert [command["name"] for command in target.commands] == [
        "generate_attention_shared_sram_k_round_scheduler_ppa_harness_rtl",
        "check_attention_shared_sram_k_round_scheduler_ppa_guard",
        "run_block_sweep",
        "extract_attention_shared_sram_k_round_scheduler_ppa_harness_timing_paths",
    ]
    assert "gen_attention_shared_sram_k_round_scheduler_ppa_harness.py" in target.commands[0]["run"]
    assert "check_attention_shared_sram_k_round_scheduler_ppa_guard.py" in target.commands[1]["run"]
    assert "--top attention_shared_sram_k_round_scheduler_b17_w17" in target.commands[2]["run"]


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


def _write_second_softmax_config(repo_root: Path) -> str:
    config_path = repo_root / "examples" / "config_softmax_rowwise_int8_r8.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        json.dumps(
            {
                "version": "1.1",
                "operations": [
                    {
                        "type": "softmax_rowwise",
                        "module_name": "softmax_rowwise_int8_r8",
                        "operand": "logits",
                        "options": {
                            "impl": "shift_exp",
                            "row_elems": 8,
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
    return str(config_path.relative_to(repo_root))


def _write_bf16_recip_norm_config(repo_root: Path) -> str:
    config_path = repo_root / "examples" / "config_bf16_recip_norm.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        json.dumps(
            {
                "version": "1.1",
                "operands": [
                    {
                        "name": "weights",
                        "dimensions": 1,
                        "bit_width": 16,
                        "signed": False,
                        "kind": "int",
                    }
                ],
                "operations": [
                    {
                        "type": "bf16_recip_norm",
                        "module_name": "bf16_recip_norm_r4",
                        "operand": "weights",
                        "options": {
                            "row_elems": 4,
                            "q_frac_bits": 10,
                            "sum_bits": 24,
                            "reciprocal_bits": 12,
                            "reciprocal_lut_bucket_shift": 4,
                        },
                    }
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return str(config_path.relative_to(repo_root))


def _write_score_tie_rank_config(repo_root: Path) -> str:
    config_path = repo_root / "examples" / "config_score_tie_rank.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        json.dumps(
            {
                "version": "1.1",
                "operands": [
                    {
                        "name": "scores",
                        "dimensions": 1,
                        "bit_width": 16,
                        "signed": False,
                        "kind": "int",
                    }
                ],
                "operations": [
                    {
                        "type": "score_tie_rank",
                        "module_name": "score_tie_rank_r4_s16_l16",
                        "operand": "scores",
                        "options": {
                            "row_elems": 4,
                            "score_bits": 16,
                            "logit_bits": 16,
                            "logit_signed": True,
                        },
                    }
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return str(config_path.relative_to(repo_root))


def _write_logit_rank_config(repo_root: Path) -> str:
    config_path = repo_root / "examples" / "config_logit_rank.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        json.dumps(
            {
                "version": "1.1",
                "operands": [
                    {
                        "name": "logits",
                        "dimensions": 1,
                        "bit_width": 16,
                        "signed": True,
                        "kind": "int",
                    }
                ],
                "operations": [
                    {
                        "type": "logit_rank",
                        "module_name": "logit_rank_r4_l16_k2",
                        "operand": "logits",
                        "options": {
                            "row_elems": 4,
                            "logit_bits": 16,
                            "top_k": 2,
                            "logit_signed": True,
                        },
                    }
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return str(config_path.relative_to(repo_root))


def _write_candidate_stream_merge_fifo_config(repo_root: Path) -> str:
    config_path = repo_root / "examples" / "config_candidate_stream_merge_fifo.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        json.dumps(
            {
                "version": "1.1",
                "operands": [
                    {
                        "name": "candidate_logits",
                        "dimensions": 1,
                        "bit_width": 16,
                        "signed": True,
                        "kind": "int",
                    }
                ],
                "operations": [
                    {
                        "type": "candidate_stream_merge_fifo",
                        "module_name": "candidate_stream_merge_fifo_k2_l16_t8_d2",
                        "operand": "candidate_logits",
                        "options": {
                            "top_k": 2,
                            "logit_bits": 16,
                            "token_id_bits": 8,
                            "fifo_depth_groups": 2,
                            "counter_bits": 16,
                            "logit_signed": True,
                        },
                    }
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return str(config_path.relative_to(repo_root))


def _write_attention_kv_tile_config(repo_root: Path) -> str:
    config_path = repo_root / "examples" / "config_attention_kv_tile.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        json.dumps(
            {
                "version": "1.1",
                "operands": [
                    {
                        "name": "kv_fragment",
                        "dimensions": 1,
                        "bit_width": 4,
                        "signed": True,
                        "kind": "int",
                    }
                ],
                "operations": [
                    {
                        "type": "attention_kv_tile",
                        "module_name": "attention_kv_tile_hd8_kv4_l4_b16",
                        "operand": "kv_fragment",
                        "options": {
                            "head_dim": 8,
                            "kv_bits": 4,
                            "lanes": 4,
                            "stream_bytes_per_cycle": 16,
                            "accum_bits": 24,
                            "counter_bits": 16,
                            "signed_inputs": True,
                        },
                    }
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return str(config_path.relative_to(repo_root))


def _init_git_repo(repo_root: Path) -> str:
    origin_root = repo_root.parent / "origin.git"
    subprocess.run(["git", "init", "--bare", str(origin_root)], check=True, capture_output=True, text=True)
    subprocess.run(["git", "-C", str(repo_root), "init"], check=True, capture_output=True, text=True)
    subprocess.run(["git", "-C", str(repo_root), "config", "user.email", "tester@example.com"], check=True, capture_output=True, text=True)
    subprocess.run(["git", "-C", str(repo_root), "config", "user.name", "Tester"], check=True, capture_output=True, text=True)
    subprocess.run(["git", "-C", str(repo_root), "add", "."], check=True, capture_output=True, text=True)
    subprocess.run(["git", "-C", str(repo_root), "commit", "-m", "test repo"], check=True, capture_output=True, text=True)
    subprocess.run(["git", "-C", str(repo_root), "remote", "add", "origin", str(origin_root)], check=True, capture_output=True, text=True)
    subprocess.run(["git", "-C", str(repo_root), "push", "-u", "origin", "HEAD:master"], check=True, capture_output=True, text=True)
    result = subprocess.run(["git", "-C", str(repo_root), "rev-parse", "HEAD"], check=True, capture_output=True, text=True)
    return result.stdout.strip()


def _commit_repo_changes(repo_root: Path, message: str) -> str:
    subprocess.run(["git", "-C", str(repo_root), "add", "-A"], check=True, capture_output=True, text=True)
    subprocess.run(["git", "-C", str(repo_root), "commit", "-m", message], check=True, capture_output=True, text=True)
    subprocess.run(["git", "-C", str(repo_root), "push", "origin", "HEAD:master"], check=True, capture_output=True, text=True)
    result = subprocess.run(["git", "-C", str(repo_root), "rev-parse", "HEAD"], check=True, capture_output=True, text=True)
    return result.stdout.strip()


def _make_l1_request(**kwargs: object) -> Layer1SweepGenerateRequest:
    kwargs.setdefault("update_proposal_files", False)
    return Layer1SweepGenerateRequest(**kwargs)


def _copy_fixture_file(*, src_repo_root: Path, dst_repo_root: Path, rel_path: str) -> None:
    src = src_repo_root / rel_path
    dst = dst_repo_root / rel_path
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def _prepare_checked_in_multivalue_service_repo(repo_root: Path) -> tuple[str, str, str, str]:
    src_repo_root = Path(__file__).resolve().parents[3]
    proposal_rel = "docs/proposals/prop_l1_decoder_attention_decode_score_multivalue_service_pnr_v1"
    c1_config_rel = (
        "runs/designs/npu_blocks/attention_decode_score_multivalue_service_c1_p128_b4_q4_rl2_rr/config.json"
    )
    c1_macro_rel = (
        "runs/designs/npu_blocks/attention_decode_score_multivalue_service_c1_p128_b4_q4_rl2_rr/macro_manifest.json"
    )
    c1_sweep_rel = (
        "runs/campaigns/npu/decode_score_multivalue_service_v1/sweeps/"
        "nangate45_decode_score_multivalue_service_c1_p128_b4_q4_rl2_rr_3000.json"
    )
    c2_config_rel = (
        "runs/designs/npu_blocks/attention_decode_score_multivalue_service_c2_p128_b4_q4_rl2_rr/config.json"
    )
    c2_macro_rel = (
        "runs/designs/npu_blocks/attention_decode_score_multivalue_service_c2_p128_b4_q4_rl2_rr/macro_manifest.json"
    )
    c2_sweep_rel = (
        "runs/campaigns/npu/decode_score_multivalue_service_v1/sweeps/"
        "nangate45_decode_score_multivalue_service_c2_p128_b4_q4_rl2_rr_3700.json"
    )

    shutil.copytree(src_repo_root / proposal_rel, repo_root / proposal_rel)
    for rel_path in (c1_config_rel, c1_macro_rel, c1_sweep_rel, c2_config_rel, c2_macro_rel, c2_sweep_rel):
        _copy_fixture_file(src_repo_root=src_repo_root, dst_repo_root=repo_root, rel_path=rel_path)
    return c1_config_rel, c1_sweep_rel, c2_config_rel, c2_sweep_rel


def _seed_materialized_dependency(
    session: Session,
    *,
    repo_root: Path,
    item_id: str,
    layer: str,
    task_type: str,
    source_commit: str,
    artifact_kind: str,
    expected_output_rel: str | None = None,
) -> WorkItem:
    task_request = TaskRequest(
        request_key=f"test:{item_id}",
        source="test",
        requested_by="@tester",
        title=item_id,
        description=item_id,
        layer=layer,
        flow="openroad",
        priority=1,
        request_payload={},
        source_commit=source_commit,
    )
    session.add(task_request)
    session.flush()
    work_item = WorkItem(
        work_item_key=f"test:{item_id}",
        task_request_id=task_request.id,
        item_id=item_id,
        layer=layer,
        flow="openroad",
        platform="nangate45",
        task_type=task_type,
        state=WorkItemState.MERGED,
        priority=1,
        source_mode="config" if layer == "layer1" else "src_verilog",
        input_manifest={},
        command_manifest=[],
        expected_outputs=[expected_output_rel] if expected_output_rel else [],
        acceptance_rules=[],
        source_commit=source_commit,
    )
    session.add(work_item)
    session.flush()
    run = Run(
        run_key=f"test:{item_id}:run",
        work_item_id=work_item.id,
        attempt=1,
        executor_type="internal_worker",
        status=RunStatus.SUCCEEDED,
        started_at=utcnow(),
        completed_at=utcnow(),
        checkout_commit=source_commit,
        result_summary="ok",
        result_payload={},
    )
    session.add(run)
    session.flush()

    decision_rel = f"control_plane/shadow_exports/review/{item_id}/decision.json"
    review_rel = f"control_plane/shadow_exports/review/{item_id}/review_package.json"
    queue_rel = f"control_plane/shadow_exports/review/{item_id}/evaluated.json"
    for rel_path, contents in (
        (decision_rel, "{}\n"),
        (review_rel, "{}\n"),
        (
            queue_rel,
            json.dumps({"task": {"expected_outputs": [expected_output_rel] if expected_output_rel else []}}, indent=2) + "\n",
        ),
    ):
        path = repo_root / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contents, encoding="utf-8")
    if expected_output_rel:
        expected_output_path = repo_root / expected_output_rel
        expected_output_path.parent.mkdir(parents=True, exist_ok=True)
        expected_output_path.write_text("status,metric\nok,1\n", encoding="utf-8")

    for kind, rel_path in (
        (artifact_kind, decision_rel),
        ("review_package", review_rel),
        ("queue_snapshot", queue_rel),
    ):
        session.add(
            Artifact(
                run_id=run.id,
                kind=kind,
                storage_mode="repo",
                path=rel_path,
                sha256="test",
                metadata_={},
            )
        )
    if expected_output_rel:
        session.add(
            Artifact(
                run_id=run.id,
                kind="expected_output",
                storage_mode="repo",
                path=expected_output_rel,
                sha256="test",
                metadata_={},
            )
        )
    session.flush()
    return work_item


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


def _write_example_dense_gemm_tile_repo(repo_root: Path) -> tuple[str, str]:
    design_dir = repo_root / "runs" / "designs" / "npu_blocks" / "npu_dense_gemm_tile_fp16_4x4_k1_p1"
    design_dir.mkdir(parents=True, exist_ok=True)
    config_path = design_dir / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "version": "0.1",
                "top_name": "dense_gemm_tile_fp16_4x4_k1_p1",
                "dense_gemm_tile": {
                    "module_name": "dense_gemm_tile_fp16_4x4_k1_p1",
                    "precision": "fp16",
                    "array_m": 4,
                    "array_n": 4,
                    "k_unroll": 1,
                    "pipeline_stages": 1,
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    sweep_path = repo_root / "runs" / "campaigns" / "npu" / "dense_gemm_tile_v1" / "sweeps" / "nangate45_dense_tile_hier.json"
    sweep_path.parent.mkdir(parents=True, exist_ok=True)
    sweep_path.write_text(
        json.dumps(
            {
                "flow_params": {
                    "CLOCK_PERIOD": [10.0],
                    "DIE_AREA": ["0 0 1200 1200"],
                    "CORE_AREA": ["50 50 1150 1150"],
                    "SYNTH_HIERARCHICAL": [1],
                    "SYNTH_KEEP_MODULES": ["dense_gemm_tile_fp16_4x4_k1_p1 gemm_mac_fp16_ieee"],
                },
                "tag_prefix": "npu_dense_gemm_tile_v1",
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


def _write_example_dense_gemm_tile_stream_repo(repo_root: Path) -> tuple[str, str]:
    design_dir = repo_root / "runs" / "designs" / "npu_blocks" / "dense_gemm_tile_stream_int8_16x8"
    design_dir.mkdir(parents=True, exist_ok=True)
    config_path = design_dir / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "version": "0.1",
                "top_name": "dense_gemm_tile_stream_int8_16x8",
                "dense_gemm_tile_stream": {
                    "precision": "int8",
                    "array_m": 16,
                    "array_n": 8,
                    "accum_bits": 32,
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    sweep_path = (
        repo_root
        / "runs"
        / "campaigns"
        / "npu"
        / "dense_gemm_tile_stream_int8_v1"
        / "sweeps"
        / "nangate45_dense_gemm_tile_stream_int8.json"
    )
    sweep_path.parent.mkdir(parents=True, exist_ok=True)
    sweep_path.write_text(
        json.dumps(
            {
                "flow_params": {"CLOCK_PERIOD": [10.0], "PLACE_DENSITY": [0.35]},
                "tag_prefix": "dense_gemm_tile_stream_int8",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return str(config_path.relative_to(repo_root)), str(sweep_path.relative_to(repo_root))


def _write_example_noc_segmented_mesh_router_bare_repo(repo_root: Path) -> tuple[str, str]:
    design_dir = repo_root / "runs" / "designs" / "npu_blocks" / "noc_router_node5_bare"
    design_dir.mkdir(parents=True, exist_ok=True)
    config_path = design_dir / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "top_name": "noc_segmented_mesh_router_node5",
                "segmented_mesh_router_bare": {
                    "node": 5,
                    "x_coord": 1,
                    "y_coord": 1,
                    "data_bits": 256,
                    "virtual_channels": 4,
                    "fifo_depth": 4,
                    "ports": 5,
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    sweep_path = (
        repo_root
        / "runs"
        / "campaigns"
        / "noc"
        / "router_bare_v1"
        / "sweeps"
        / "nangate45.json"
    )
    sweep_path.parent.mkdir(parents=True, exist_ok=True)
    sweep_path.write_text(
        json.dumps(
            {
                "flow_params": {
                    "CLOCK_PERIOD": [1.8],
                    "CORE_UTILIZATION": [50],
                    "FLOW_VARIANT": ["router_node5_bare_v1"],
                },
                "tag_prefix": "router_node5_bare_v1",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return str(config_path.relative_to(repo_root)), str(sweep_path.relative_to(repo_root))


def _write_example_noc_segmented_mesh4x4_direct_repo(repo_root: Path) -> tuple[str, str]:
    design_dir = repo_root / "runs" / "designs" / "npu_blocks" / "noc_mesh4x4_direct"
    design_dir.mkdir(parents=True, exist_ok=True)
    config_path = design_dir / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "top_name": "noc_segmented_mesh4x4_functional",
                "segmented_mesh4x4_direct": {
                    "nodes": 16,
                    "ports_per_router": 5,
                    "data_bits": 256,
                    "virtual_channels": 4,
                    "fifo_depth": 4,
                    "debug_counters": False,
                    "top_level_pin_count": 8962,
                    "pin_pitch_bound_um": 1.12,
                    "die_side_um": 3200,
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    sweep_path = (
        repo_root
        / "runs"
        / "campaigns"
        / "noc"
        / "mesh4x4_direct_v1"
        / "sweeps"
        / "nangate45.json"
    )
    sweep_path.parent.mkdir(parents=True, exist_ok=True)
    sweep_path.write_text(
        json.dumps(
            {
                "flow_params": {
                    "CLOCK_PERIOD": [2.0],
                    "DIE_AREA": ["0 0 3200 3200"],
                    "CORE_AREA": ["50 50 3150 3150"],
                    "PLACE_DENSITY": [0.45],
                    "FLOW_VARIANT": ["mesh4x4_direct_v1"],
                },
                "tag_prefix": "mesh4x4_direct_v1",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return str(config_path.relative_to(repo_root)), str(sweep_path.relative_to(repo_root))


def _write_example_dual_stream_composed_repo(repo_root: Path) -> tuple[str, str]:
    design_dir = repo_root / "runs" / "designs" / "npu_blocks" / "attention_dual_stream_composed_smoke"
    design_dir.mkdir(parents=True, exist_ok=True)
    config_path = design_dir / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "top_name": "attention_dual_stream_composed_smoke",
                "attention_dual_stream_composed": {
                    "streams": 2,
                    "array_m": 2,
                    "array_n": 2,
                    "k_unroll": 1,
                    "softmax_row_elems": 4,
                    "softmax_accum_bits": 16,
                    "reciprocal_bits": 10,
                    "value_bits": 6,
                    "value_lanes": 4,
                    "partials": 4,
                    "partials_per_cycle": 2,
                    "stream_buffer_bits": 128,
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    sweep_path = (
        repo_root
        / "runs"
        / "campaigns"
        / "npu"
        / "attention_dual_stream_composed_v1"
        / "sweeps"
        / "nangate45_dual_stream_composed_hier.json"
    )
    sweep_path.parent.mkdir(parents=True, exist_ok=True)
    sweep_path.write_text(
        json.dumps(
            {
                "flow_params": {
                    "CLOCK_PERIOD": [10.0],
                    "DIE_AREA": ["0 0 1200 1200"],
                    "CORE_AREA": ["50 50 1150 1150"],
                    "SYNTH_HIERARCHICAL": [1],
                    "SYNTH_KEEP_MODULES": [
                        "int8_mac_s8s8_acc24 attention_softmax_weight_int8_r8_acc24_recip_q10_like"
                    ],
                },
                "tag_prefix": "attention_dual_stream_composed_v1",
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


def _write_example_attention_command_dispatch_repo(repo_root: Path) -> tuple[str, str]:
    design_dir = repo_root / "runs" / "designs" / "npu_blocks" / "attention_command_dispatch_smoke"
    design_dir.mkdir(parents=True, exist_ok=True)
    config_path = design_dir / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "top_name": "attention_command_dispatch_smoke",
                "attention_command_dispatch": {
                    "clusters": 8,
                    "queue_depth": 16,
                    "tile_id_bits": 12,
                    "wave_id_bits": 8,
                    "base_token_bits": 14,
                    "max_inflight_per_cluster": 4,
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    sweep_path = (
        repo_root
        / "runs"
        / "campaigns"
        / "npu"
        / "attention_command_dispatch_v1"
        / "sweeps"
        / "nangate45_attention_command_dispatch_frontier.json"
    )
    sweep_path.parent.mkdir(parents=True, exist_ok=True)
    sweep_path.write_text(
        json.dumps(
            {
                "flow_params": {
                    "CLOCK_PERIOD": [1.0],
                    "CORE_UTILIZATION": [40],
                    "PLACE_DENSITY": [0.45],
                },
                "tag_prefix": "attention_command_dispatch_frontier",
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


def _write_example_attention_score32_exact_local_temporal_reducer_physical_harness_repo(
    repo_root: Path,
) -> tuple[str, str]:
    design_dir = (
        repo_root
        / "runs"
        / "designs"
        / "npu_blocks"
        / "attention_score32_exact_local_temporal_reducer_physical_harness_p53_reducer_w8"
    )
    design_dir.mkdir(parents=True, exist_ok=True)
    config_path = design_dir / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "top_name": "attention_score32_exact_local_temporal_reducer_physical_harness_p53_reducer_w8",
                "attention_score32_exact_local_temporal_reducer_physical_harness": {
                    "producers": 53,
                    "mode": "reducer",
                    "waves": 8,
                },
                "report_links": {
                    "proposal_id": "prop_l1_decoder_attention_score32_local_temporal_reducer_v1",
                    "proposal_path": "docs/proposals/prop_l1_decoder_attention_score32_local_temporal_reducer_v1/proposal.json",
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    sweep_path = (
        repo_root
        / "runs"
        / "campaigns"
        / "npu"
        / "attention_score32_local_temporal_reducer_v1"
        / "sweeps"
        / "nangate45_attention_score32_local_temporal_reducer_physical_harness_boundary.json"
    )
    sweep_path.parent.mkdir(parents=True, exist_ok=True)
    sweep_path.write_text(
        json.dumps(
            {
                "tag_prefix": "attention_score32_local_temporal_reducer_physical_harness_boundary_v1",
                "flow_params": {
                    "CLOCK_PERIOD": [8.0, 10.0],
                    "DIE_AREA": ["0 0 2200 2200"],
                    "CORE_AREA": ["80 80 2120 2120"],
                    "PLACE_DENSITY": [0.35],
                    "SYNTH_HIERARCHICAL": [1],
                },
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


def _write_example_attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_repo(
    repo_root: Path,
) -> tuple[str, str]:
    design_dir = (
        repo_root
        / "runs"
        / "designs"
        / "npu_blocks"
        / "attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p53_reducer_w8"
    )
    design_dir.mkdir(parents=True, exist_ok=True)
    config_path = design_dir / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "top_name": "attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p53_reducer_w8",
                "attention_score32_exact_local_temporal_reducer_gqa8_physical_harness": {
                    "producers": 53,
                    "mode": "reducer",
                    "waves": 8,
                },
                "report_links": {
                    "proposal_id": "prop_l1_decoder_attention_score32_local_temporal_reducer_gqa8_v1",
                    "proposal_path": "docs/proposals/prop_l1_decoder_attention_score32_local_temporal_reducer_gqa8_v1/proposal.json",
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    sweep_path = (
        repo_root
        / "runs"
        / "campaigns"
        / "npu"
        / "attention_score32_local_temporal_reducer_gqa8_v1"
        / "sweeps"
        / "nangate45_attention_score32_local_temporal_reducer_gqa8_physical_harness_boundary.json"
    )
    sweep_path.parent.mkdir(parents=True, exist_ok=True)
    sweep_path.write_text(
        json.dumps(
            {
                "tag_prefix": "attention_score32_local_temporal_reducer_gqa8_physical_harness_boundary_v1",
                "flow_params": {
                    "CLOCK_PERIOD": [8.0, 10.0],
                    "DIE_AREA": ["0 0 2200 2200"],
                    "CORE_AREA": ["80 80 2120 2120"],
                    "PLACE_DENSITY": [0.35],
                    "SYNTH_HIERARCHICAL": [1],
                },
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


def _write_macro_attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_repo(
    repo_root: Path,
) -> tuple[str, str]:
    design_name = (
        "attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_"
        "p53_reducer_factored_hier_folded_mersenne_macro_w8"
    )
    top_name = design_name
    design_dir = repo_root / "runs" / "designs" / "npu_blocks" / design_name
    design_dir.mkdir(parents=True, exist_ok=True)
    config_path = design_dir / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "top_name": top_name,
                "attention_score32_exact_local_temporal_reducer_gqa8_physical_harness": {
                    "producers": 53,
                    "mode": "reducer",
                    "waves": 8,
                    "exp_scale_impl": "factored_h33_l64_mul_exact",
                    "pair_node_impl": "folded_sharedscale_mersenne_exact",
                    "keep_hierarchy": True,
                },
                "macro_hardening": {
                    "enabled": True,
                    "clock_period": 10.0,
                    "clock_port": "clk",
                    "place_density": 0.55,
                    "flow_variant": "base",
                    "die_area": "0 0 330 330",
                    "core_area": "10 10 320 320",
                    "pair_node_macro_id": "attention_score32_exact_local_temporal_reducer_gqa8_pair_node_ng45_r7",
                    "temporal_merge_macro_id": (
                        "attention_score32_exact_local_temporal_reducer_gqa8_temporal_merge_ng45_r7"
                    ),
                    "bundle_design_id": "attention_score32_exact_local_temporal_reducer_gqa8_macro_bundle_ng45_r7",
                    "bundle_manifest_path": f"runs/designs/npu_blocks/{design_name}/macro_manifest.json",
                    "pair_node_manifest_params": {
                        "macro_role": "pair_node",
                        "macro_eval_excludes_io_pads": True,
                    },
                    "temporal_merge_manifest_params": {
                        "macro_role": "temporal_merge",
                        "macro_eval_excludes_io_pads": True,
                    },
                    "bundle_manifest_params": {
                        "pair_node_instance_count": 52,
                        "temporal_merge_instance_count": 1,
                    },
                },
                "report_links": {
                    "proposal_id": "prop_l1_decoder_attention_score32_local_temporal_reducer_gqa8_v1",
                    "proposal_path": "docs/proposals/prop_l1_decoder_attention_score32_local_temporal_reducer_gqa8_v1/proposal.json",
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    sweep_path = (
        repo_root
        / "runs"
        / "campaigns"
        / "npu"
        / "attention_score32_local_temporal_reducer_gqa8_v1"
        / "sweeps"
        / "nangate45_attention_score32_local_temporal_reducer_gqa8_physical_harness_boundary_factored_hier_folded_mersenne_macro_r7.json"
    )
    sweep_path.parent.mkdir(parents=True, exist_ok=True)
    sweep_path.write_text(
        json.dumps(
            {
                "tag_prefix": (
                    "attention_score32_local_temporal_reducer_gqa8_physical_harness_"
                    "boundary_factored_hier_folded_mersenne_macro_v1_r7"
                ),
                "flow_params": {
                    "CLOCK_PERIOD": [10.0, 15.0],
                    "DIE_AREA": ["0 0 3500 3500"],
                    "CORE_AREA": ["80 80 3420 3420"],
                    "PLACE_DENSITY": [0.55],
                    "SYNTH_HIERARCHICAL": [1],
                    "SYNTH_ARGS": ["-noshare"],
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return str(config_path.relative_to(repo_root)), str(sweep_path.relative_to(repo_root))


def _write_example_attention_schedule_wrapper_repo(repo_root: Path) -> tuple[str, str]:
    design_dir = repo_root / "runs" / "designs" / "npu_blocks" / "attention_dual_stream_schedule_wrapper_smoke_c2"
    design_dir.mkdir(parents=True, exist_ok=True)
    config_path = design_dir / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "top_name": "attention_dual_stream_schedule_wrapper_smoke_c2",
                "attention_dual_stream_schedule_wrapper": {
                    "clusters": 2,
                    "queue_depth": 8,
                    "tile_id_bits": 16,
                    "wave_id_bits": 12,
                    "base_token_bits": 18,
                    "max_inflight_per_cluster": 2,
                    "cluster_service_cycles": 4,
                    "datapath": {
                        "streams": 2,
                        "array_m": 2,
                        "array_n": 2,
                        "k_unroll": 1,
                        "mac_accum_bits": 32,
                        "softmax_row_elems": 4,
                        "softmax_score_bits": 32,
                        "softmax_weight_bits": 16,
                        "softmax_input_frac_bits": 28,
                        "softmax_accum_bits": 40,
                        "reciprocal_bits": 16,
                        "softmax_reciprocal_lut_bucket_shift": 20,
                        "value_bits": 8,
                        "value_lanes": 4,
                        "partials": 4,
                        "partials_per_cycle": 1,
                        "stream_buffer_bits": 256,
                        "equivalence_hash": False,
                        "softmax_pipeline_stages": 1,
                        "softmax_impl": "exp_lut_div",
                        "semantic_profile": "score32_exp_lut_div",
                    },
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    sweep_path = (
        repo_root
        / "runs"
        / "campaigns"
        / "npu"
        / "attention_dual_stream_schedule_wrapper_v1"
        / "sweeps"
        / "nangate45_attention_dual_stream_schedule_wrapper_score32_exp_lut.json"
    )
    sweep_path.parent.mkdir(parents=True, exist_ok=True)
    sweep_path.write_text(
        json.dumps(
            {
                "flow_params": {
                    "CLOCK_PERIOD": [10.0],
                    "DIE_AREA": ["0 0 2500 2500"],
                    "CORE_AREA": ["50 50 2450 2450"],
                    "PLACE_DENSITY": [0.35],
                    "SYNTH_HIERARCHICAL": [1],
                },
                "tag_prefix": "attention_dual_stream_schedule_wrapper_score32_exp_lut",
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


def _write_example_attention_separated_cluster_repo(repo_root: Path) -> tuple[str, str]:
    design_dir = repo_root / "runs" / "designs" / "npu_blocks" / "attention_separated_cluster_p4_c1"
    design_dir.mkdir(parents=True, exist_ok=True)
    config_path = design_dir / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "top_name": "attention_separated_cluster_p4_c1",
                "attention_separated_cluster": {
                    "producer_count": 4,
                    "consumer_count": 1,
                    "row_elems": 8,
                    "head_dim": 8,
                    "value_dim": 8,
                    "score_bits": 32,
                    "weight_bits": 16,
                    "input_frac_bits": 28,
                    "exp_bucket_shift": 20,
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    sweep_path = (
        repo_root
        / "runs"
        / "campaigns"
        / "npu"
        / "attention_separated_cluster_v1"
        / "sweeps"
        / "nangate45_attention_separated_cluster.json"
    )
    sweep_path.parent.mkdir(parents=True, exist_ok=True)
    sweep_path.write_text(
        json.dumps(
            {
                "flow_params": {"CLOCK_PERIOD": [10.0], "PLACE_DENSITY": [0.35]},
                "tag_prefix": "attention_separated_cluster",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return str(config_path.relative_to(repo_root)), str(sweep_path.relative_to(repo_root))


def _write_example_attention_two_pass_stream_repo(repo_root: Path) -> tuple[str, str]:
    design_dir = repo_root / "runs" / "designs" / "npu_blocks" / "attention_two_pass_stream_d2"
    design_dir.mkdir(parents=True, exist_ok=True)
    config_path = design_dir / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "top_name": "attention_two_pass_stream_d2",
                "attention_two_pass_stream": {"max_blocks": 16384, "div_lanes_per_cycle": 2},
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    sweep_path = (
        repo_root
        / "runs"
        / "campaigns"
        / "npu"
        / "attention_two_pass_stream_v1"
        / "sweeps"
        / "nangate45_attention_two_pass_stream.json"
    )
    sweep_path.parent.mkdir(parents=True, exist_ok=True)
    sweep_path.write_text(
        json.dumps(
            {
                "flow_params": {"CLOCK_PERIOD": [10.0], "PLACE_DENSITY": [0.35]},
                "tag_prefix": "attention_two_pass_stream",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return str(config_path.relative_to(repo_root)), str(sweep_path.relative_to(repo_root))


def _write_example_attention_score_bank_proxy_repo(repo_root: Path) -> tuple[str, str]:
    design_dir = repo_root / "runs" / "designs" / "npu_blocks" / "attention_score_bank_proxy_16kx256"
    design_dir.mkdir(parents=True, exist_ok=True)
    config_path = design_dir / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "top_name": "attention_score_bank_proxy_16kx256",
                "attention_score_bank_proxy": {
                    "logical_depth": 16384,
                    "logical_width": 256,
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (design_dir / "macro_manifest.json").write_text("{}\n", encoding="utf-8")
    sweep_path = (
        repo_root
        / "runs"
        / "campaigns"
        / "npu"
        / "attention_score_bank_proxy_v1"
        / "sweeps"
        / "nangate45_attention_score_bank_proxy.json"
    )
    sweep_path.parent.mkdir(parents=True, exist_ok=True)
    sweep_path.write_text(
        json.dumps(
            {
                "flow_params": {"CLOCK_PERIOD": [10.0], "PLACE_DENSITY": [0.4]},
                "tag_prefix": "attention_score_bank_proxy",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return str(config_path.relative_to(repo_root)), str(sweep_path.relative_to(repo_root))


def _write_example_attention_decode_score_local_cluster_repo(repo_root: Path) -> tuple[str, str]:
    design_dir = (
        repo_root
        / "runs"
        / "designs"
        / "npu_blocks"
        / "attention_decode_score_local_cluster_int8_m1x8_iterdiv"
    )
    design_dir.mkdir(parents=True)
    config_path = design_dir / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "top_name": "attention_decode_score_local_cluster_int8_m1x8_iterdiv",
                "attention_decode_score_local_cluster": {
                    "max_blocks": 16384,
                    "array_n": 8,
                    "divider_impl": "iterative_restoring",
                },
            }
        ),
        encoding="utf-8",
    )
    sweep_path = (
        repo_root
        / "runs"
        / "campaigns"
        / "npu"
        / "decode_score_local_cluster_v1"
        / "sweeps"
        / "nangate45_decode_score_local_cluster.json"
    )
    sweep_path.parent.mkdir(parents=True)
    sweep_path.write_text(
        json.dumps({"parameters": {"CLOCK_PERIOD": [10], "PLACE_DENSITY": [0.35]}}),
        encoding="utf-8",
    )
    return str(config_path.relative_to(repo_root)), str(sweep_path.relative_to(repo_root))


def _write_example_attention_decode_score_multivalue_cluster_repo(repo_root: Path) -> tuple[str, str]:
    design_dir = (
        repo_root
        / "runs"
        / "designs"
        / "npu_blocks"
        / "attention_decode_score_multivalue_cluster_int8_m1x8_iterdiv"
    )
    design_dir.mkdir(parents=True)
    config_path = design_dir / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "top_name": "attention_decode_score_multivalue_cluster_int8_m1x8_iterdiv",
                "attention_decode_score_multivalue_cluster": {
                    "max_blocks": 16384,
                    "array_n": 8,
                    "value_slices_per_block": 16,
                    "divider_impl": "iterative_restoring",
                },
            }
        ),
        encoding="utf-8",
    )
    sweep_path = (
        repo_root
        / "runs"
        / "campaigns"
        / "npu"
        / "decode_score_multivalue_cluster_v1"
        / "sweeps"
        / "nangate45_decode_score_multivalue_cluster.json"
    )
    sweep_path.parent.mkdir(parents=True)
    sweep_path.write_text(
        json.dumps({"parameters": {"CLOCK_PERIOD": [10], "PLACE_DENSITY": [0.35]}}),
        encoding="utf-8",
    )
    return str(config_path.relative_to(repo_root)), str(sweep_path.relative_to(repo_root))


def _write_example_attention_decode_score_multivalue_service_repo(repo_root: Path) -> tuple[str, str]:
    design_dir = (
        repo_root
        / "runs"
        / "designs"
        / "npu_blocks"
        / "attention_decode_score_multivalue_service_c2_p128_b4_q4_rl2_rr"
    )
    design_dir.mkdir(parents=True)
    config_path = design_dir / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "top_name": "attention_decode_score_multivalue_service_c2_p128_b4_q4_rl2_rr",
                "attention_decode_score_multivalue_service": {
                    "cluster_count": 2,
                    "max_blocks": 16,
                    "packet_w": 128,
                    "banks": 4,
                    "req_queue_depth": 4,
                    "resp_queue_depth": 4,
                    "bank_queue_depth": 4,
                    "read_latency": 2,
                    "arb_mode": "round_robin",
                    "locality_burst_max": 2,
                    "score_scale_lanes_per_cycle": 1,
                    "value_memory_backend": "macro_banked_4x16x64x32",
                },
            }
        ),
        encoding="utf-8",
    )
    (design_dir / "macro_manifest.json").write_text("{}\n", encoding="utf-8")
    sweep_path = (
        repo_root
        / "runs"
        / "campaigns"
        / "npu"
        / "decode_score_multivalue_service_v1"
        / "sweeps"
        / "nangate45_decode_score_multivalue_service_c2_p128_b4_q4_rl2_rr_3700.json"
    )
    sweep_path.parent.mkdir(parents=True)
    sweep_path.write_text(
        json.dumps(
            {
                "flow_params": {
                    "CLOCK_PERIOD": [10],
                    "PLACE_DENSITY": [0.4],
                    "SYNTH_HIERARCHICAL": [1],
                    "SYNTH_MEMORY_MAX_BITS": [65536],
                }
            }
        ),
        encoding="utf-8",
    )
    return str(config_path.relative_to(repo_root)), str(sweep_path.relative_to(repo_root))


def _write_attention_decode_score_multivalue_cluster_targeted_binary_config(
    repo_root: Path,
) -> str:
    design_dir = (
        repo_root
        / "runs"
        / "designs"
        / "npu_blocks"
        / "attention_decode_score_multivalue_cluster_int8_m1x8_iterdiv"
    )
    design_dir.mkdir(parents=True, exist_ok=True)
    config_path = design_dir / "config_targeted_binary_fsm.json"
    config_path.write_text(
        json.dumps(
            {
                "top_name": "attention_decode_score_multivalue_cluster_int8_m1x8_iterdiv",
                "attention_decode_score_multivalue_cluster": {
                    "max_blocks": 16384,
                    "array_n": 8,
                    "value_slices": 16,
                    "divider_impl": "iterative_restoring",
                    "score_scale_lanes_per_cycle": 1,
                    "fsm_encoding": "binary",
                },
            }
        ),
        encoding="utf-8",
    )
    return str(config_path.relative_to(repo_root))


def _write_attention_decode_score_multivalue_cluster_explicit_onehot_config(
    repo_root: Path,
) -> str:
    design_dir = (
        repo_root
        / "runs"
        / "designs"
        / "npu_blocks"
        / "attention_decode_score_multivalue_cluster_int8_m1x8_iterdiv"
    )
    design_dir.mkdir(parents=True, exist_ok=True)
    config_path = design_dir / "config_explicit_onehot_fsm.json"
    config_path.write_text(
        json.dumps(
            {
                "top_name": "attention_decode_score_multivalue_cluster_int8_m1x8_iterdiv",
                "attention_decode_score_multivalue_cluster": {
                    "max_blocks": 16384,
                    "array_n": 8,
                    "value_slices": 16,
                    "divider_impl": "iterative_restoring",
                    "score_scale_lanes_per_cycle": 1,
                    "fsm_encoding": "explicit_onehot",
                },
            }
        ),
        encoding="utf-8",
    )
    return str(config_path.relative_to(repo_root))


def _write_attention_decode_score_multivalue_cluster_8ns_bridge_sweep(repo_root: Path) -> str:
    sweep_path = (
        repo_root
        / "runs"
        / "campaigns"
        / "npu"
        / "decode_score_multivalue_cluster_v1"
        / "sweeps"
        / "nangate45_decode_score_multivalue_cluster_8ns_proxy_die_2500.json"
    )
    sweep_path.parent.mkdir(parents=True, exist_ok=True)
    sweep_path.write_text(
        json.dumps(
            {
                "flow_params": {
                    "TAG": ["decode_score_multivalue_cluster_v1_8ns_bridge"],
                    "FLOW_VARIANT": ["decode_score_multivalue_cluster_v1_8ns_bridge"],
                    "CLOCK_PERIOD": [8],
                },
                "mode_compare": {
                    "modes": [
                        {
                            "name": "proxy_die_2500",
                            "use_macro": True,
                            "param_overrides": {
                                "DIE_AREA": "0 0 2500 2500",
                                "CORE_AREA": "50 50 2450 2450",
                            },
                        }
                    ]
                },
            }
        ),
        encoding="utf-8",
    )
    return str(sweep_path.relative_to(repo_root))


def _write_attention_decode_score_multivalue_cluster_binary_fsm_8ns_v3_sweep(repo_root: Path) -> str:
    sweep_path = (
        repo_root
        / "runs"
        / "campaigns"
        / "npu"
        / "decode_score_multivalue_cluster_v1"
        / "sweeps"
        / "nangate45_decode_score_multivalue_cluster_8ns_binary_fsm_v3.json"
    )
    sweep_path.parent.mkdir(parents=True, exist_ok=True)
    sweep_path.write_text(
        json.dumps(
            {
                "flow_params": {
                    "TAG": ["decode_score_multivalue_cluster_v1_8ns_binary_fsm"],
                    "FLOW_VARIANT": ["decode_score_multivalue_cluster_v1_8ns_binary_fsm_v3"],
                    "CLOCK_PERIOD": [8],
                    "SYNTH_HIERARCHICAL": [1],
                    "SYNTH_MEMORY_MAX_BITS": [65536],
                    "PLACE_DENSITY": [0.4],
                    "SYNTH_ARGS": ["-nofsm"],
                },
                "mode_compare": {
                    "modes": [
                        {
                            "name": "proxy_die_2500",
                            "use_macro": True,
                            "param_overrides": {
                                "DIE_AREA": "0 0 2500 2500",
                                "CORE_AREA": "50 50 2450 2450",
                            },
                        }
                    ]
                },
            }
        ),
        encoding="utf-8",
    )
    return str(sweep_path.relative_to(repo_root))


def _write_attention_decode_score_multivalue_cluster_binary_fsm_8ns_v4_sweep(repo_root: Path) -> str:
    sweep_path = (
        repo_root
        / "runs"
        / "campaigns"
        / "npu"
        / "decode_score_multivalue_cluster_v1"
        / "sweeps"
        / "nangate45_decode_score_multivalue_cluster_8ns_binary_fsm_v4.json"
    )
    sweep_path.parent.mkdir(parents=True, exist_ok=True)
    sweep_path.write_text(
        json.dumps(
            {
                "flow_params": {
                    "TAG": ["decode_score_multivalue_cluster_v1_8ns_binary_fsm"],
                    "FLOW_VARIANT": ["decode_score_multivalue_cluster_v1_8ns_binary_fsm_v4"],
                    "CLOCK_PERIOD": [8],
                    "SYNTH_HIERARCHICAL": [1],
                    "SYNTH_MEMORY_MAX_BITS": [65536],
                    "PLACE_DENSITY": [0.4],
                    "SYNTH_ARGS": ["-nofsm"],
                },
                "mode_compare": {
                    "modes": [
                        {
                            "name": "proxy_die_2500",
                            "use_macro": True,
                            "param_overrides": {
                                "DIE_AREA": "0 0 2500 2500",
                                "CORE_AREA": "50 50 2450 2450",
                            },
                        }
                    ]
                },
            }
        ),
        encoding="utf-8",
    )
    return str(sweep_path.relative_to(repo_root))


def _write_attention_decode_score_multivalue_cluster_targeted_binary_fsm_8ns_sweep(
    repo_root: Path,
) -> str:
    sweep_path = (
        repo_root
        / "runs"
        / "campaigns"
        / "npu"
        / "decode_score_multivalue_cluster_v1"
        / "sweeps"
        / "nangate45_decode_score_multivalue_cluster_8ns_targeted_binary_fsm_v1.json"
    )
    sweep_path.parent.mkdir(parents=True, exist_ok=True)
    sweep_path.write_text(
        json.dumps(
            {
                "tag_prefix": "decode_score_multivalue_cluster_v1_8ns_targeted_binary_fsm",
                "flow_params": {
                    "TAG": ["decode_score_multivalue_cluster_v1_8ns_targeted_binary_fsm"],
                    "FLOW_VARIANT": [
                        "decode_score_multivalue_cluster_v1_8ns_targeted_binary_fsm_v1"
                    ],
                    "CLOCK_PERIOD": [8],
                    "SYNTH_HIERARCHICAL": [1],
                    "SYNTH_MEMORY_MAX_BITS": [65536],
                    "PLACE_DENSITY": [0.4],
                },
                "mode_compare": {
                    "modes": [
                        {
                            "name": "proxy_die_2500",
                            "use_macro": True,
                            "param_overrides": {
                                "DIE_AREA": "0 0 2500 2500",
                                "CORE_AREA": "50 50 2450 2450",
                            },
                        }
                    ]
                },
            }
        ),
        encoding="utf-8",
    )
    return str(sweep_path.relative_to(repo_root))


def _write_attention_decode_score_multivalue_cluster_explicit_onehot_fsm_8ns_sweep(
    repo_root: Path,
) -> str:
    sweep_path = (
        repo_root
        / "runs"
        / "campaigns"
        / "npu"
        / "decode_score_multivalue_cluster_v1"
        / "sweeps"
        / "nangate45_decode_score_multivalue_cluster_8ns_explicit_onehot_fsm_v1.json"
    )
    sweep_path.parent.mkdir(parents=True, exist_ok=True)
    sweep_path.write_text(
        json.dumps(
            {
                "tag_prefix": "decode_score_multivalue_cluster_v1_8ns_explicit_onehot_fsm",
                "flow_params": {
                    "TAG": ["decode_score_multivalue_cluster_v1_8ns_explicit_onehot_fsm"],
                    "FLOW_VARIANT": [
                        "decode_score_multivalue_cluster_v1_8ns_explicit_onehot_fsm_v1"
                    ],
                    "CLOCK_PERIOD": [8],
                    "SYNTH_HIERARCHICAL": [1],
                    "SYNTH_MEMORY_MAX_BITS": [65536],
                    "PLACE_DENSITY": [0.4],
                },
                "mode_compare": {
                    "modes": [
                        {
                            "name": "proxy_die_2500",
                            "use_macro": True,
                            "param_overrides": {
                                "DIE_AREA": "0 0 2500 2500",
                                "CORE_AREA": "50 50 2450 2450",
                            },
                        }
                    ]
                },
            }
        ),
        encoding="utf-8",
    )
    return str(sweep_path.relative_to(repo_root))


def _write_example_attention_decode_score_multivalue_gqa_group_repo(
    repo_root: Path,
) -> tuple[str, str]:
    design_dir = (
        repo_root
        / "runs"
        / "designs"
        / "npu_blocks"
        / "attention_decode_score_multivalue_gqa_group_int8_m1x8_iterdiv"
    )
    design_dir.mkdir(parents=True)
    config_path = design_dir / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "top_name": "attention_decode_score_multivalue_gqa_group_int8_m1x8_iterdiv",
                "attention_decode_score_multivalue_gqa_group": {
                    "max_blocks": 16384,
                    "array_n": 8,
                    "value_slices": 16,
                    "divider_impl": "iterative_restoring",
                    "score_scale_lanes_per_cycle": 1,
                    "query_heads_per_kv": 8,
                },
            }
        ),
        encoding="utf-8",
    )
    (design_dir / "macro_manifest.json").write_text(
        json.dumps({"manifest_params": {"score_bank_macro_count": 448}}),
        encoding="utf-8",
    )
    sweep_path = (
        repo_root
        / "runs"
        / "campaigns"
        / "npu"
        / "decode_score_multivalue_gqa_group_v1"
        / "sweeps"
        / "nangate45_decode_score_multivalue_gqa_group.json"
    )
    sweep_path.parent.mkdir(parents=True)
    sweep_path.write_text(
        json.dumps({"parameters": {"CLOCK_PERIOD": [10], "PLACE_DENSITY": [0.35]}}),
        encoding="utf-8",
    )
    return str(config_path.relative_to(repo_root)), str(sweep_path.relative_to(repo_root))


def _write_example_attention_decode_score_multivalue_gqa_array_repo(
    repo_root: Path,
) -> tuple[str, str]:
    design_dir = (
        repo_root
        / "runs"
        / "designs"
        / "npu_blocks"
        / "attention_decode_score_multivalue_gqa_array_g2_int8_m1x8_iterdiv"
    )
    design_dir.mkdir(parents=True)
    config_path = design_dir / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "top_name": "attention_decode_score_multivalue_gqa_array_g2_int8_m1x8_iterdiv",
                "attention_decode_score_multivalue_gqa_array": {
                    "max_blocks": 16384,
                    "array_n": 8,
                    "value_slices": 16,
                    "divider_impl": "iterative_restoring",
                    "score_scale_lanes_per_cycle": 1,
                    "query_heads_per_kv": 8,
                    "group_count": 2,
                },
            }
        ),
        encoding="utf-8",
    )
    (design_dir / "macro_manifest.json").write_text(
        json.dumps({"manifest_params": {"score_bank_macro_count": 896}}),
        encoding="utf-8",
    )
    sweep_path = (
        repo_root
        / "runs"
        / "campaigns"
        / "npu"
        / "decode_score_multivalue_gqa_array_g2_v1"
        / "sweeps"
        / "nangate45_decode_score_multivalue_gqa_array_g2.json"
    )
    sweep_path.parent.mkdir(parents=True)
    sweep_path.write_text(
        json.dumps({"parameters": {"CLOCK_PERIOD": [10], "PLACE_DENSITY": [0.4]}}),
        encoding="utf-8",
    )
    return str(config_path.relative_to(repo_root)), str(sweep_path.relative_to(repo_root))


def _write_example_attention_decode_score_multivalue_gqa_group_lanes2_repo(
    repo_root: Path,
) -> str:
    design_dir = (
        repo_root
        / "runs"
        / "designs"
        / "npu_blocks"
        / "attention_decode_score_multivalue_gqa_group_lanes2_int8_m1x8_iterdiv"
    )
    design_dir.mkdir(parents=True)
    config_path = design_dir / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "version": "0.1",
                "top_name": "attention_decode_score_multivalue_gqa_group_lanes2_int8_m1x8_iterdiv",
                "attention_decode_score_multivalue_gqa_group": {
                    "max_blocks": 16384,
                    "array_n": 8,
                    "value_slices": 16,
                    "divider_impl": "iterative_restoring",
                    "score_scale_lanes_per_cycle": 1,
                    "query_heads_per_kv": 8,
                    "parallel_query_head_lanes": 2,
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (design_dir / "macro_manifest.json").write_text(
        json.dumps({"manifest_params": {"score_bank_macro_count": 112}}, indent=2) + "\n",
        encoding="utf-8",
    )
    return str(config_path.relative_to(repo_root))


def _write_attention_decode_score_multivalue_gqa_lanes2_macro_hier_placement_sweep(repo_root: Path) -> str:
    sweep_path = (
        repo_root
        / "runs"
        / "campaigns"
        / "npu"
        / "decode_score_multivalue_gqa_folded_lanes_v1"
        / "sweeps"
        / "nangate45_decode_score_multivalue_gqa_lanes2_macro_hier_placement_compare_3550.json"
    )
    sweep_path.parent.mkdir(parents=True, exist_ok=True)
    sweep_path.write_text(
        json.dumps(
            {
                "tag_prefix": "decode_score_multivalue_gqa_lanes2_macro_hier_placement_compare_3550_v1",
                "flow_params": {
                    "TAG": ["decode_score_multivalue_gqa_lanes2_macro_hier_placement_compare_3550_v1"],
                    "FLOW_VARIANT": ["decode_score_multivalue_gqa_lanes2_macro_hier_placement_compare_3550_v1"],
                    "CLOCK_PERIOD": [10],
                    "PLACE_DENSITY": [0.4],
                    "SYNTH_HIERARCHICAL": [1],
                    "SYNTH_MEMORY_MAX_BITS": [65536],
                },
                "mode_compare": {
                    "modes": [
                        {
                            "name": "flattened_wrapper",
                            "use_macro": True,
                            "param_overrides": {
                                "SYNTH_HIERARCHICAL": 0,
                                "DIE_AREA": "0 0 3550 3550",
                                "CORE_AREA": "50 50 3500 3500",
                            },
                        },
                        {
                            "name": "hierarchical_macro",
                            "use_macro": True,
                            "param_overrides": {
                                "SYNTH_HIERARCHICAL": 1,
                                "DIE_AREA": "0 0 3550 3550",
                                "CORE_AREA": "50 50 3500 3500",
                            },
                        },
                    ]
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return str(sweep_path.relative_to(repo_root))


def _write_example_attention_hbm_replay_controller_repo(repo_root: Path) -> tuple[str, str]:
    design_dir = repo_root / "runs" / "designs" / "npu_blocks" / "attention_hbm_replay_controller_smoke"
    design_dir.mkdir(parents=True, exist_ok=True)
    config_path = design_dir / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "top_name": "attention_hbm_replay_controller_smoke",
                "attention_hbm_replay_controller": {
                    "channel_count": 4,
                    "burst_bytes": 64,
                    "row_span_bursts": 4,
                    "row_miss_penalty_cycles": 8,
                    "request_overhead_cycles": 2,
                    "scheduler_gap_cycles": 1,
                    "outstanding": 8,
                    "address_bits": 32,
                    "row_id_bits": 16,
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    sweep_path = (
        repo_root
        / "runs"
        / "campaigns"
        / "npu"
        / "attention_hbm_replay_controller_v1"
        / "sweeps"
        / "nangate45_attention_hbm_replay_controller_frontier.json"
    )
    sweep_path.parent.mkdir(parents=True, exist_ok=True)
    sweep_path.write_text(
        json.dumps(
            {
                "flow_params": {
                    "CLOCK_PERIOD": [1.0],
                    "CORE_UTILIZATION": [40],
                    "PLACE_DENSITY": [0.45],
                },
                "tag_prefix": "attention_hbm_replay_controller_frontier",
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


def _write_second_attention_hbm_replay_controller_repo(repo_root: Path) -> str:
    design_dir = repo_root / "runs" / "designs" / "npu_blocks" / "attention_hbm_replay_controller_c16_q32"
    design_dir.mkdir(parents=True, exist_ok=True)
    config_path = design_dir / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "top_name": "attention_hbm_replay_controller_c16_q32",
                "attention_hbm_replay_controller": {
                    "channel_count": 16,
                    "burst_bytes": 64,
                    "row_span_bursts": 4,
                    "row_miss_penalty_cycles": 8,
                    "request_overhead_cycles": 2,
                    "scheduler_gap_cycles": 1,
                    "outstanding": 16,
                    "address_bits": 32,
                    "row_id_bits": 16,
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return str(config_path.relative_to(repo_root))


def _write_example_llama7b_rmsnorm_phase3_physical_repo(repo_root: Path) -> tuple[str, str]:
    design_dir = repo_root / "runs" / "designs" / "npu_blocks" / "llama7b_rmsnorm_phase3_bounded_l16_ng45"
    design_dir.mkdir(parents=True, exist_ok=True)
    config_path = design_dir / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "top_name": "llama7b_rmsnorm_phase3_bounded_l16_ng45",
                "llama7b_rmsnorm": {
                    "lanes": 16,
                },
                "report_links": {
                    "proposal_id": "prop_l1_decoder_llama7b_rmsnorm_phase3_bounded_physical_v1",
                    "proposal_path": (
                        "docs/proposals/"
                        "prop_l1_decoder_llama7b_rmsnorm_phase3_bounded_physical_v1/proposal.json"
                    ),
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    sweep_path = (
        repo_root
        / "runs"
        / "campaigns"
        / "npu"
        / "llama7b_rmsnorm_phase3_physical_v1"
        / "sweeps"
        / "nangate45_llama7b_rmsnorm_phase3_bounded_l16.json"
    )
    sweep_path.parent.mkdir(parents=True, exist_ok=True)
    sweep_path.write_text(
        json.dumps(
            {
                "tag_prefix": "llama7b_rmsnorm_phase3_bounded_l16_ng45_v1",
                "flow_params": {
                    "CLOCK_PERIOD": [16.0, 20.0],
                    "DIE_AREA": ["0 0 5200 5200"],
                    "CORE_AREA": ["120 120 5080 5080"],
                    "PLACE_DENSITY": [0.3],
                    "SYNTH_HIERARCHICAL": [1],
                },
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


def _write_second_attention_command_dispatch_repo(repo_root: Path) -> str:
    design_dir = repo_root / "runs" / "designs" / "npu_blocks" / "attention_command_dispatch_c16_q32"
    design_dir.mkdir(parents=True, exist_ok=True)
    config_path = design_dir / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "top_name": "attention_command_dispatch_c16_q32",
                "attention_command_dispatch": {
                    "clusters": 16,
                    "queue_depth": 32,
                    "tile_id_bits": 12,
                    "wave_id_bits": 8,
                    "base_token_bits": 14,
                    "max_inflight_per_cluster": 4,
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return str(config_path.relative_to(repo_root))


def _write_second_attention_score32_exact_local_temporal_reducer_physical_harness_repo(repo_root: Path) -> str:
    design_dir = (
        repo_root
        / "runs"
        / "designs"
        / "npu_blocks"
        / "attention_score32_exact_local_temporal_reducer_physical_harness_p54_source_only_w8"
    )
    design_dir.mkdir(parents=True, exist_ok=True)
    config_path = design_dir / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "top_name": "attention_score32_exact_local_temporal_reducer_physical_harness_p54_source_only_w8",
                "attention_score32_exact_local_temporal_reducer_physical_harness": {
                    "producers": 54,
                    "mode": "source_only",
                    "waves": 8,
                },
                "report_links": {
                    "proposal_id": "prop_l1_decoder_attention_score32_local_temporal_reducer_v1",
                    "proposal_path": "docs/proposals/prop_l1_decoder_attention_score32_local_temporal_reducer_v1/proposal.json",
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return str(config_path.relative_to(repo_root))


def _write_second_attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_repo(repo_root: Path) -> str:
    design_dir = (
        repo_root
        / "runs"
        / "designs"
        / "npu_blocks"
        / "attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p54_source_only_w8"
    )
    design_dir.mkdir(parents=True, exist_ok=True)
    config_path = design_dir / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "top_name": "attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p54_source_only_w8",
                "attention_score32_exact_local_temporal_reducer_gqa8_physical_harness": {
                    "producers": 54,
                    "mode": "source_only",
                    "waves": 8,
                },
                "report_links": {
                    "proposal_id": "prop_l1_decoder_attention_score32_local_temporal_reducer_gqa8_v1",
                    "proposal_path": "docs/proposals/prop_l1_decoder_attention_score32_local_temporal_reducer_gqa8_v1/proposal.json",
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return str(config_path.relative_to(repo_root))


def _write_example_attention_score32_exact_root_finalizer_repo(repo_root: Path) -> tuple[str, str]:
    design_dir = repo_root / "runs" / "designs" / "npu_blocks" / "attention_score32_exact_root_finalizer_smoke_l4"
    design_dir.mkdir(parents=True, exist_ok=True)
    config_path = design_dir / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "top_name": "attention_score32_exact_root_finalizer_smoke_l4",
                "attention_score32_exact_root_finalizer": {
                    "value_slices": 16,
                    "head_id_bits": 5,
                    "divider_lanes": 4,
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    sweep_path = (
        repo_root
        / "runs"
        / "campaigns"
        / "npu"
        / "attention_score32_exact_root_finalizer_v1"
        / "sweeps"
        / "nangate45_attention_score32_exact_root_finalizer_lane_firstpass.json"
    )
    sweep_path.parent.mkdir(parents=True, exist_ok=True)
    sweep_path.write_text(
        json.dumps(
            {
                "tag_prefix": "attention_score32_exact_root_finalizer_lane_firstpass_v1",
                "flow_params": {
                    "CLOCK_PERIOD": [8.0],
                    "DIE_AREA": ["0 0 1000 1000"],
                    "CORE_AREA": ["50 50 950 950"],
                    "PLACE_DENSITY": [0.3, 0.5],
                    "SYNTH_HIERARCHICAL": [1],
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return str(config_path.relative_to(repo_root)), str(sweep_path.relative_to(repo_root))


def _write_example_attention_score32_exact_partial_tree_repo(repo_root: Path) -> tuple[str, str]:
    design_dir = repo_root / "runs" / "designs" / "npu_blocks" / "attention_score32_exact_partial_tree_smoke_c4_r2"
    design_dir.mkdir(parents=True, exist_ok=True)
    config_path = design_dir / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "top_name": "attention_score32_exact_partial_tree_smoke_c4_r2",
                "attention_score32_exact_partial_tree": {
                    "clusters": 4,
                    "radix": 2,
                    "value_slices": 16,
                    "head_id_bits": 5,
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    sweep_path = (
        repo_root
        / "runs"
        / "campaigns"
        / "npu"
        / "attention_score32_exact_partial_tree_v1"
        / "sweeps"
        / "nangate45_attention_score32_exact_partial_tree_cluster_firstpass.json"
    )
    sweep_path.parent.mkdir(parents=True, exist_ok=True)
    sweep_path.write_text(
        json.dumps(
            {
                "tag_prefix": "attention_score32_exact_partial_tree_cluster_firstpass_v1",
                "flow_params": {
                    "CLOCK_PERIOD": [8.0],
                    "DIE_AREA": ["0 0 2500 2500"],
                    "CORE_AREA": ["50 50 2450 2450"],
                    "PLACE_DENSITY": [0.3, 0.5],
                    "SYNTH_HIERARCHICAL": [1],
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return str(config_path.relative_to(repo_root)), str(sweep_path.relative_to(repo_root))


def _write_example_attention_score32_exact_partial_tree_folded_mersenne_repo(repo_root: Path) -> tuple[str, str]:
    design_dir = (
        repo_root
        / "runs"
        / "designs"
        / "npu_blocks"
        / "attention_score32_exact_partial_tree_folded_mersenne_smoke_c4_r2"
    )
    design_dir.mkdir(parents=True, exist_ok=True)
    config_path = design_dir / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "top_name": "attention_score32_exact_partial_tree_folded_mersenne_smoke_c4_r2",
                "attention_score32_exact_partial_tree": {
                    "clusters": 4,
                    "radix": 2,
                    "value_slices": 16,
                    "head_id_bits": 5,
                    "exp_scale_impl": "factored_h33_l64_mul_exact",
                    "pair_node_impl": "folded_sharedscale_mersenne_exact",
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    sweep_path = (
        repo_root
        / "runs"
        / "campaigns"
        / "npu"
        / "attention_score32_exact_partial_tree_folded_mersenne_v1"
        / "sweeps"
        / "nangate45_attention_score32_exact_partial_tree_folded_mersenne_cluster_v1.json"
    )
    sweep_path.parent.mkdir(parents=True, exist_ok=True)
    sweep_path.write_text(
        json.dumps(
            {
                "tag_prefix": "attention_score32_exact_partial_tree_folded_mersenne_cluster_v1",
                "flow_params": {
                    "CLOCK_PERIOD": [8.0],
                    "DIE_AREA": ["0 0 2500 2500"],
                    "CORE_AREA": ["50 50 2450 2450"],
                    "IO_PLACER_H": ["metal3 metal5"],
                    "IO_PLACER_V": ["metal4 metal6"],
                    "PLACE_DENSITY": [0.3],
                    "PLACE_PINS_ARGS": ["-min_distance 1"],
                    "SYNTH_HIERARCHICAL": [1],
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return str(config_path.relative_to(repo_root)), str(sweep_path.relative_to(repo_root))


def _write_example_attention_score32_exact_partial_pair_merge_folded_repo(
    repo_root: Path,
) -> tuple[str, str]:
    design_dir = (
        repo_root
        / "runs"
        / "designs"
        / "npu_blocks"
        / "attention_score32_exact_partial_pair_merge_sharedscale_factored_l1"
    )
    design_dir.mkdir(parents=True, exist_ok=True)
    config_path = design_dir / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "top_name": "attention_score32_exact_partial_pair_merge_sharedscale_factored_l1",
                "attention_score32_exact_partial_pair_merge_folded": {
                    "value_slices": 16,
                    "head_id_bits": 5,
                    "exp_scale_impl": "factored_h33_l64_mul_exact",
                    "lane_parallelism": 1,
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    sweep_path = (
        repo_root
        / "runs"
        / "campaigns"
        / "npu"
        / "attention_score32_exact_partial_pair_merge_sharedscale_v1"
        / "sweeps"
        / "nangate45_attention_score32_exact_partial_pair_merge_sharedscale_factored_l1.json"
    )
    sweep_path.parent.mkdir(parents=True, exist_ok=True)
    sweep_path.write_text(
        json.dumps(
            {
                "tag_prefix": "attention_score32_exact_partial_pair_merge_sharedscale_v1",
                "flow_params": {
                    "CLOCK_PERIOD": [8.0],
                    "DIE_AREA": ["0 0 1500 1500"],
                    "CORE_AREA": ["50 50 1450 1450"],
                    "PLACE_DENSITY": [0.3],
                    "SYNTH_HIERARCHICAL": [1],
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return str(config_path.relative_to(repo_root)), str(sweep_path.relative_to(repo_root))


def _write_example_attention_score32_exact_partial_pair_merge_folded_mersenne_repo(
    repo_root: Path,
) -> tuple[str, str]:
    design_dir = (
        repo_root
        / "runs"
        / "designs"
        / "npu_blocks"
        / "attention_score32_exact_partial_pair_merge_sharedscale_factored_mersenne_l1"
    )
    design_dir.mkdir(parents=True, exist_ok=True)
    config_path = design_dir / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "top_name": "attention_score32_exact_partial_pair_merge_sharedscale_factored_mersenne_l1",
                "attention_score32_exact_partial_pair_merge_folded": {
                    "value_slices": 16,
                    "head_id_bits": 5,
                    "exp_scale_impl": "factored_h33_l64_mul_exact",
                    "scale_divider_impl": "mersenne24_correction2_exact",
                    "lane_parallelism": 1,
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    sweep_path = (
        repo_root
        / "runs"
        / "campaigns"
        / "npu"
        / "attention_score32_exact_partial_pair_merge_sharedscale_mersenne_v1"
        / "sweeps"
        / "nangate45_attention_score32_exact_partial_pair_merge_sharedscale_factored_mersenne_l1.json"
    )
    sweep_path.parent.mkdir(parents=True, exist_ok=True)
    sweep_path.write_text(
        json.dumps(
            {
                "tag_prefix": "attention_score32_exact_partial_pair_merge_sharedscale_mersenne_v1",
                "flow_params": {
                    "CLOCK_PERIOD": [8.0],
                    "DIE_AREA": ["0 0 1500 1500"],
                    "CORE_AREA": ["50 50 1450 1450"],
                    "PLACE_DENSITY": [0.3],
                    "SYNTH_HIERARCHICAL": [1],
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return str(config_path.relative_to(repo_root)), str(sweep_path.relative_to(repo_root))


def _write_example_attention_score32_exact_finalized_tree_repo(repo_root: Path) -> tuple[str, str]:
    design_dir = repo_root / "runs" / "designs" / "npu_blocks" / "attention_score32_exact_finalized_tree_smoke_c16_r2_l4"
    design_dir.mkdir(parents=True, exist_ok=True)
    config_path = design_dir / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "top_name": "attention_score32_exact_finalized_tree_smoke_c16_r2_l4",
                "attention_score32_exact_finalized_tree": {
                    "clusters": 16,
                    "radix": 2,
                    "value_slices": 16,
                    "head_id_bits": 5,
                    "divider_lanes": 4,
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    sweep_path = (
        repo_root
        / "runs"
        / "campaigns"
        / "npu"
        / "attention_score32_exact_finalized_tree_v1"
        / "sweeps"
        / "nangate45_attention_score32_exact_finalized_tree_c16_lane_firstpass.json"
    )
    sweep_path.parent.mkdir(parents=True, exist_ok=True)
    sweep_path.write_text(
        json.dumps(
            {
                "tag_prefix": "attention_score32_exact_finalized_tree_c16_lane_firstpass_v1",
                "flow_params": {
                    "CLOCK_PERIOD": [8.0],
                    "DIE_AREA": ["0 0 2500 2500"],
                    "CORE_AREA": ["50 50 2450 2450"],
                    "PLACE_DENSITY": [0.3, 0.5],
                    "SYNTH_HIERARCHICAL": [1],
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return str(config_path.relative_to(repo_root)), str(sweep_path.relative_to(repo_root))


def _write_example_attention_score32_exact_banked_finalized_tree_repo(repo_root: Path) -> tuple[str, str]:
    design_dir = repo_root / "runs" / "designs" / "npu_blocks" / "attention_score32_exact_banked_finalized_tree_smoke_c16_r2_l8_b16"
    design_dir.mkdir(parents=True, exist_ok=True)
    config_path = design_dir / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "top_name": "attention_score32_exact_banked_finalized_tree_smoke_c16_r2_l8_b16",
                "attention_score32_exact_banked_finalized_tree": {
                    "clusters": 16,
                    "radix": 2,
                    "value_slices": 16,
                    "head_id_bits": 5,
                    "divider_lanes": 8,
                    "finalizer_banks": 16,
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    sweep_path = (
        repo_root
        / "runs"
        / "campaigns"
        / "npu"
        / "attention_score32_exact_banked_finalized_tree_v1"
        / "sweeps"
        / "nangate45_attention_score32_exact_banked_finalized_tree_c16_bank_firstpass.json"
    )
    sweep_path.parent.mkdir(parents=True, exist_ok=True)
    sweep_path.write_text(
        json.dumps(
            {
                "tag_prefix": "attention_score32_exact_banked_finalized_tree_c16_bank_firstpass_v1",
                "flow_params": {
                    "CLOCK_PERIOD": [8.0],
                    "DIE_AREA": ["0 0 2700 2700"],
                    "CORE_AREA": ["100 100 2600 2600"],
                    "PLACE_DENSITY": [0.3, 0.5],
                    "SYNTH_HIERARCHICAL": [1],
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return str(config_path.relative_to(repo_root)), str(sweep_path.relative_to(repo_root))


def _write_second_attention_score32_exact_partial_tree_repo(repo_root: Path) -> str:
    design_dir = repo_root / "runs" / "designs" / "npu_blocks" / "attention_score32_exact_partial_tree_smoke_c16_r2"
    design_dir.mkdir(parents=True, exist_ok=True)
    config_path = design_dir / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "top_name": "attention_score32_exact_partial_tree_smoke_c16_r2",
                "attention_score32_exact_partial_tree": {
                    "clusters": 16,
                    "radix": 2,
                    "value_slices": 16,
                    "head_id_bits": 5,
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return str(config_path.relative_to(repo_root))


def _write_second_attention_score32_exact_root_finalizer_repo(repo_root: Path) -> str:
    design_dir = repo_root / "runs" / "designs" / "npu_blocks" / "attention_score32_exact_root_finalizer_smoke_l8"
    design_dir.mkdir(parents=True, exist_ok=True)
    config_path = design_dir / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "top_name": "attention_score32_exact_root_finalizer_smoke_l8",
                "attention_score32_exact_root_finalizer": {
                    "value_slices": 16,
                    "head_id_bits": 5,
                    "divider_lanes": 8,
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return str(config_path.relative_to(repo_root))


def _write_second_attention_score32_exact_finalized_tree_repo(repo_root: Path) -> str:
    design_dir = repo_root / "runs" / "designs" / "npu_blocks" / "attention_score32_exact_finalized_tree_smoke_c16_r2_l8"
    design_dir.mkdir(parents=True, exist_ok=True)
    config_path = design_dir / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "top_name": "attention_score32_exact_finalized_tree_smoke_c16_r2_l8",
                "attention_score32_exact_finalized_tree": {
                    "clusters": 16,
                    "radix": 2,
                    "value_slices": 16,
                    "head_id_bits": 5,
                    "divider_lanes": 8,
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return str(config_path.relative_to(repo_root))


def _write_second_attention_score32_exact_banked_finalized_tree_repo(repo_root: Path) -> str:
    design_dir = repo_root / "runs" / "designs" / "npu_blocks" / "attention_score32_exact_banked_finalized_tree_smoke_c16_r2_l8_b32"
    design_dir.mkdir(parents=True, exist_ok=True)
    config_path = design_dir / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "top_name": "attention_score32_exact_banked_finalized_tree_smoke_c16_r2_l8_b32",
                "attention_score32_exact_banked_finalized_tree": {
                    "clusters": 16,
                    "radix": 2,
                    "value_slices": 16,
                    "head_id_bits": 5,
                    "divider_lanes": 8,
                    "finalizer_banks": 32,
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return str(config_path.relative_to(repo_root))


def _write_third_attention_score32_exact_banked_finalized_tree_repo(repo_root: Path) -> str:
    design_dir = repo_root / "runs" / "designs" / "npu_blocks" / "attention_score32_exact_banked_finalized_tree_smoke_c16_r2_l8_b59"
    design_dir.mkdir(parents=True, exist_ok=True)
    config_path = design_dir / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "top_name": "attention_score32_exact_banked_finalized_tree_smoke_c16_r2_l8_b59",
                "attention_score32_exact_banked_finalized_tree": {
                    "clusters": 16,
                    "radix": 2,
                    "value_slices": 16,
                    "head_id_bits": 5,
                    "divider_lanes": 8,
                    "finalizer_banks": 59,
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return str(config_path.relative_to(repo_root))


def _write_fourth_attention_score32_exact_banked_finalized_tree_repo(repo_root: Path) -> str:
    design_dir = repo_root / "runs" / "designs" / "npu_blocks" / "attention_score32_exact_banked_finalized_tree_smoke_c16_r2_l8_b64"
    design_dir.mkdir(parents=True, exist_ok=True)
    config_path = design_dir / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "top_name": "attention_score32_exact_banked_finalized_tree_smoke_c16_r2_l8_b64",
                "attention_score32_exact_banked_finalized_tree": {
                    "clusters": 16,
                    "radix": 2,
                    "value_slices": 16,
                    "head_id_bits": 5,
                    "divider_lanes": 8,
                    "finalizer_banks": 64,
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return str(config_path.relative_to(repo_root))


def _copy_checked_in_attention_score32_exact_finalizer_bank_control_repo(
    repo_root: Path,
) -> tuple[list[str], str, str, str, str]:
    checked_in_root = Path(__file__).resolve().parents[3]
    config_paths = [
        "runs/designs/npu_blocks/attention_score32_exact_finalizer_bank_control_l8_b1/config.json",
        "runs/designs/npu_blocks/attention_score32_exact_finalizer_bank_control_l8_b4/config.json",
        "runs/designs/npu_blocks/attention_score32_exact_finalizer_bank_control_l8_b8/config.json",
        "runs/designs/npu_blocks/attention_score32_exact_finalizer_bank_control_l8_b16/config.json",
        "runs/designs/npu_blocks/attention_score32_exact_finalizer_bank_control_l8_b32/config.json",
        "runs/designs/npu_blocks/attention_score32_exact_finalizer_bank_control_l8_b59/config.json",
    ]
    sweep_path = (
        "runs/campaigns/npu/attention_score32_exact_finalizer_bank_control_v1/sweeps/"
        "nangate45_attention_score32_exact_finalizer_bank_control_lane8_firstpass.json"
    )
    proposal_dir = "docs/proposals/prop_l1_decoder_attention_score32_exact_finalizer_bank_control_ppa_v1"
    copy_paths = [
        *config_paths,
        sweep_path,
        f"{proposal_dir}/proposal.json",
        f"{proposal_dir}/evaluation_requests.json",
    ]
    for relative_path in copy_paths:
        source_path = checked_in_root / relative_path
        dest_path = repo_root / relative_path
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, dest_path)
    return (
        config_paths,
        sweep_path,
        "prop_l1_decoder_attention_score32_exact_finalizer_bank_control_ppa_v1",
        proposal_dir,
        "l1_decoder_attention_score32_exact_finalizer_bank_control_ppa_v1_r2",
    )



def test_generate_l1_sweep_task_creates_ready_work_item() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        config_path, sweep_path = _write_example_repo(repo_root)
        source_commit = _init_git_repo(repo_root)
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            with patch(
                "control_plane.services.l1_task_generator._image_provided_l1_runtime_deps_available",
                return_value=False,
            ):
                result = generate_l1_sweep_task(
                    session,
                    _make_l1_request(
                        repo_root=str(repo_root),
                        sweep_path=sweep_path,
                        config_paths=[config_path],
                        platform="nangate45",
                        out_root="runs/designs/activations",
                        requested_by="@tester",
                        source_commit=source_commit,
                        abstraction_layer="circuit_block",
                    ),
                )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            assert result.status == "applied"
            assert work_item.task_type == "l1_sweep"
            assert work_item.state == WorkItemState.DISPATCH_PENDING
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
            assert "--force_gen" in work_item.command_manifest[1]["run"]
            assert "--skip_existing" in work_item.command_manifest[1]["run"]
            assert work_item.command_manifest[1]["run"].startswith(
                "export PATH=/oss-cad-suite/bin:$PATH && python3 scripts/run_sweep.py "
            )
            assert work_item.command_manifest[3]["run"] == "python3 scripts/validate_runs.py --skip_eval_queue"
            assert work_item.expected_outputs == [
                "runs/designs/activations/softmax_rowwise_int8_r4_wrapper/metrics.csv",
            ]
            payload = work_item.task_request.request_payload
            assert payload["layer"] == "layer1"
            assert payload["source_requirement"]["required_sha"] == source_commit
            assert payload["source_requirement"]["required_ref"] == "origin/master"
            assert payload["source_requirement"]["requires_daemon_restart"] is True
            assert payload["generation_source_identity"] == {
                "version": 1,
                "declared_source_commit": source_commit,
                "repo_head_sha": source_commit,
                "relation": "exact",
                "proof": "generator_worktree_head_exact",
                "clean": True,
            }
            assert payload["task"]["inputs"]["sweeps"] == [sweep_path]
            assert payload["task"]["acceptance"][0] == (
                "Each generated wrapper metrics.csv contains at least one status=ok row for the queued sweep"
            )
            assert payload["task"]["inputs"]["required_submodules"] == [
                "third_party/nlohmann_json",
                "third_party/cacti",
            ]
            assert payload["developer_loop"]["abstraction"] == {"layer": "circuit_block"}
            assert payload["handoff"]["pr_body_fields"]["queue_item_id"] == result.item_id


def test_generate_l1_sweep_task_rejects_mismatched_generation_worktree() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        config_path, sweep_path = _write_example_repo(repo_root)
        source_commit = _init_git_repo(repo_root)
        mismatch_file = repo_root / "HEAD_ONLY.txt"
        mismatch_file.write_text("mismatch\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(repo_root), "add", "HEAD_ONLY.txt"], check=True, capture_output=True, text=True)
        subprocess.run(
            ["git", "-C", str(repo_root), "commit", "-m", "local head drift"],
            check=True,
            capture_output=True,
            text=True,
        )
        head_commit = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            try:
                generate_l1_sweep_task(
                    session,
                    _make_l1_request(
                        repo_root=str(repo_root),
                        sweep_path=sweep_path,
                        config_paths=[config_path],
                        platform="nangate45",
                        out_root="runs/designs/activations",
                        requested_by="@tester",
                        source_commit=source_commit,
                    ),
                )
            except Layer1TaskGenerationError as exc:
                message = str(exc)
                assert "exact-generation worktree" in message
                assert source_commit in message
                assert head_commit in message
                assert "Regenerate the item from a checkout whose HEAD exactly matches the declared source commit." in message
            else:
                raise AssertionError("expected Layer1TaskGenerationError for mismatched generation worktree")


def test_generate_l1_sweep_task_rejects_tracked_dirty_generation_worktree() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        config_path, sweep_path = _write_example_repo(repo_root)
        source_commit = _init_git_repo(repo_root)
        tracked_file = repo_root / config_path
        tracked_file.write_text(tracked_file.read_text(encoding="utf-8") + "\n", encoding="utf-8")
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            try:
                generate_l1_sweep_task(
                    session,
                    _make_l1_request(
                        repo_root=str(repo_root),
                        sweep_path=sweep_path,
                        config_paths=[config_path],
                        platform="nangate45",
                        out_root="runs/designs/activations",
                        requested_by="@tester",
                        source_commit=source_commit,
                    ),
                )
            except Layer1TaskGenerationError as exc:
                message = str(exc)
                assert "clean exact-generation worktree" in message
                assert "git status --porcelain is not empty" in message
                assert f" M {config_path}" in message or f"M {config_path}" in message
                assert "Commit, stash, or remove tracked and untracked changes" in message
            else:
                raise AssertionError("expected Layer1TaskGenerationError for tracked dirty generation worktree")


def test_generate_l1_sweep_task_rejects_untracked_generation_worktree() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        config_path, sweep_path = _write_example_repo(repo_root)
        source_commit = _init_git_repo(repo_root)
        untracked_rel = "examples/untracked_probe.json"
        (repo_root / untracked_rel).write_text('{"probe": true}\n', encoding="utf-8")
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            try:
                generate_l1_sweep_task(
                    session,
                    _make_l1_request(
                        repo_root=str(repo_root),
                        sweep_path=sweep_path,
                        config_paths=[config_path],
                        platform="nangate45",
                        out_root="runs/designs/activations",
                        requested_by="@tester",
                        source_commit=source_commit,
                    ),
                )
            except Layer1TaskGenerationError as exc:
                message = str(exc)
                assert "clean exact-generation worktree" in message
                assert "git status --porcelain is not empty" in message
                assert f"?? {untracked_rel}" in message
                assert "Commit, stash, or remove tracked and untracked changes" in message
            else:
                raise AssertionError("expected Layer1TaskGenerationError for untracked generation worktree")


def test_generate_l1_sweep_task_uses_boundary_metrics_acceptance() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        config_path, sweep_path = _write_example_repo(repo_root)
        source_commit = _init_git_repo(repo_root)
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            with patch(
                "control_plane.services.l1_task_generator._image_provided_l1_runtime_deps_available",
                return_value=False,
            ):
                result = generate_l1_sweep_task(
                    session,
                    _make_l1_request(
                        repo_root=str(repo_root),
                        sweep_path=sweep_path,
                        config_paths=[config_path],
                        platform="nangate45",
                        out_root="runs/designs/activations",
                        requested_by="@tester",
                        source_commit=source_commit,
                        objective="Measure physical boundary and accept timing/flow failures as boundary evidence",
                    ),
                )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            assert "allow non-ok metrics" in work_item.acceptance_rules[0]
            assert "flow_failed" in work_item.acceptance_rules[0]
            assert work_item.task_request.request_payload["task"]["acceptance"] == work_item.acceptance_rules


def test_generate_l1_sweep_task_uses_acceptance_notes_for_boundary_evidence() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        config_path, sweep_path = _write_example_repo(repo_root)
        source_commit = _init_git_repo(repo_root)
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            with patch(
                "control_plane.services.l1_task_generator._image_provided_l1_runtime_deps_available",
                return_value=False,
            ):
                result = generate_l1_sweep_task(
                    session,
                    _make_l1_request(
                        repo_root=str(repo_root),
                        sweep_path=sweep_path,
                        config_paths=[config_path],
                        platform="nangate45",
                        out_root="runs/designs/activations",
                        requested_by="@tester",
                        source_commit=source_commit,
                        objective="Measure frontier behavior across throughput settings for review.",
                        acceptance_notes=(
                            "Treat both ok and failed rows as explicit boundary evidence "
                            "when flow_failed appears."
                        ),
                    ),
                )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            assert "allow non-ok metrics" in work_item.acceptance_rules[0]
            assert "flow_failed" in work_item.acceptance_rules[0]
            assert (
                work_item.task_request.request_payload["task"]["metadata"]["acceptance_notes"]
                == "Treat both ok and failed rows as explicit boundary evidence when flow_failed appears."
            )
            assert work_item.task_request.request_payload["task"]["acceptance"] == work_item.acceptance_rules


def test_generate_l1_sweep_task_requeues_failed_item_on_upsert() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        config_path, sweep_path = _write_example_repo(repo_root)
        source_commit = _init_git_repo(repo_root)
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            result = generate_l1_sweep_task(
                session,
                _make_l1_request(
                    repo_root=str(repo_root),
                    sweep_path=sweep_path,
                    config_paths=[config_path],
                    platform="nangate45",
                    out_root="runs/designs/activations",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="circuit_block",
                ),
            )
            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            work_item.state = WorkItemState.FAILED
            work_item.assigned_machine_key = "eval-daemon-old"
            work_item.queue_snapshot_path = "runs/eval_queue/openroad/failed/l1_demo.json"
            session.commit()

            generate_l1_sweep_task(
                session,
                _make_l1_request(
                    repo_root=str(repo_root),
                    sweep_path=sweep_path,
                    config_paths=[config_path],
                    platform="nangate45",
                    out_root="runs/designs/activations",
                    requested_by="@tester2",
                    source_commit=source_commit,
                    abstraction_layer="circuit_block",
                ),
            )

            session.refresh(work_item)
            assert work_item.state == WorkItemState.DISPATCH_PENDING
            assert work_item.assigned_machine_key is None
            assert work_item.queue_snapshot_path is None


def test_generate_l1_sweep_task_expands_expected_outputs_for_multi_trial_items() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        config_path, sweep_path = _write_example_repo(repo_root)
        source_commit = _init_git_repo(repo_root)
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            result = generate_l1_sweep_task(
                session,
                _make_l1_request(
                    repo_root=str(repo_root),
                    sweep_path=sweep_path,
                    config_paths=[config_path],
                    platform="nangate45",
                    out_root="runs/designs/activations/softmax_rowwise_int8_r4_wrapper",
                    item_id="l1_seedvariance_demo_r1",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="circuit_block",
                    trial_count=3,
                    seed_start=100,
                    stop_after_failures=3,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            assert work_item.expected_outputs == [
                "runs/designs/activations/softmax_rowwise_int8_r4_wrapper/trials/trial_001/softmax_rowwise_int8_r4_wrapper/metrics.csv",
                "runs/designs/activations/softmax_rowwise_int8_r4_wrapper/trials/trial_002/softmax_rowwise_int8_r4_wrapper/metrics.csv",
                "runs/designs/activations/softmax_rowwise_int8_r4_wrapper/trials/trial_003/softmax_rowwise_int8_r4_wrapper/metrics.csv",
            ]


def test_generate_l1_sweep_task_run_sweep_command_includes_all_wrapper_configs() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        config_path, sweep_path = _write_example_repo(repo_root)
        second_config_path = _write_second_softmax_config(repo_root)
        source_commit = _init_git_repo(repo_root)
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            result = generate_l1_sweep_task(
                session,
                _make_l1_request(
                    repo_root=str(repo_root),
                    sweep_path=sweep_path,
                    config_paths=[config_path, second_config_path],
                    platform="nangate45",
                    out_root="runs/designs/activations",
                    item_id="l1_demo_softmax_multi_config",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="circuit_block",
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            run_sweep = work_item.command_manifest[1]["run"]
            assert f"--configs {config_path} {second_config_path} " in run_sweep
            assert work_item.expected_outputs == [
                "runs/designs/activations/softmax_rowwise_int8_r4_wrapper/metrics.csv",
                "runs/designs/activations/softmax_rowwise_int8_r8_wrapper/metrics.csv",
            ]


def test_generate_l1_sweep_task_supports_bf16_recip_norm_wrapper_config() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        _, sweep_path = _write_example_repo(repo_root)
        config_path = _write_bf16_recip_norm_config(repo_root)
        source_commit = _init_git_repo(repo_root)
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            result = generate_l1_sweep_task(
                session,
                _make_l1_request(
                    repo_root=str(repo_root),
                    sweep_path=sweep_path,
                    config_paths=[config_path],
                    platform="nangate45",
                    out_root="runs/designs/activations",
                    item_id="l1_demo_bf16_recip_norm",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="circuit_block",
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            assert result.status == "applied"
            assert work_item.expected_outputs == [
                "runs/designs/activations/bf16_recip_norm_r4_wrapper/metrics.csv",
            ]


def test_generate_l1_sweep_task_supports_score_tie_rank_wrapper_config() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        _, sweep_path = _write_example_repo(repo_root)
        config_path = _write_score_tie_rank_config(repo_root)
        source_commit = _init_git_repo(repo_root)
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            result = generate_l1_sweep_task(
                session,
                _make_l1_request(
                    repo_root=str(repo_root),
                    sweep_path=sweep_path,
                    config_paths=[config_path],
                    platform="nangate45",
                    out_root="runs/designs/activations",
                    item_id="l1_demo_score_tie_rank",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="circuit_block",
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            assert result.status == "applied"
            assert work_item.expected_outputs == [
                "runs/designs/activations/score_tie_rank_r4_s16_l16_wrapper/metrics.csv",
            ]


def test_generate_l1_sweep_task_supports_logit_rank_wrapper_config() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        _, sweep_path = _write_example_repo(repo_root)
        config_path = _write_logit_rank_config(repo_root)
        source_commit = _init_git_repo(repo_root)
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            result = generate_l1_sweep_task(
                session,
                _make_l1_request(
                    repo_root=str(repo_root),
                    sweep_path=sweep_path,
                    config_paths=[config_path],
                    platform="nangate45",
                    out_root="runs/designs/activations",
                    item_id="l1_demo_logit_rank",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="circuit_block",
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            assert result.status == "applied"
            assert work_item.expected_outputs == [
                "runs/designs/activations/logit_rank_r4_l16_k2_wrapper/metrics.csv",
            ]


def test_generate_l1_sweep_task_supports_candidate_stream_merge_fifo_wrapper_config() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        _, sweep_path = _write_example_repo(repo_root)
        config_path = _write_candidate_stream_merge_fifo_config(repo_root)
        source_commit = _init_git_repo(repo_root)
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            result = generate_l1_sweep_task(
                session,
                _make_l1_request(
                    repo_root=str(repo_root),
                    sweep_path=sweep_path,
                    config_paths=[config_path],
                    platform="nangate45",
                    out_root="runs/designs/activations",
                    item_id="l1_demo_candidate_stream_merge_fifo",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="candidate_stream_merge_fifo",
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            assert result.status == "applied"
            assert work_item.expected_outputs == [
                "runs/designs/activations/candidate_stream_merge_fifo_k2_l16_t8_d2_wrapper/metrics.csv",
            ]


def test_generate_l1_sweep_task_supports_attention_kv_tile_wrapper_config() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        _, sweep_path = _write_example_repo(repo_root)
        config_path = _write_attention_kv_tile_config(repo_root)
        source_commit = _init_git_repo(repo_root)
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            result = generate_l1_sweep_task(
                session,
                _make_l1_request(
                    repo_root=str(repo_root),
                    sweep_path=sweep_path,
                    config_paths=[config_path],
                    platform="nangate45",
                    out_root="runs/designs/activations",
                    item_id="l1_demo_attention_kv_tile",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="decoder_attention_kv_tile",
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            assert result.status == "applied"
            assert work_item.expected_outputs == [
                "runs/designs/activations/attention_kv_tile_hd8_kv4_l4_b16_wrapper/metrics.csv",
            ]


def test_generate_l1_sweep_task_records_requested_item_in_proposal_evaluation_requests() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        config_path, sweep_path = _write_example_repo(repo_root)
        proposal_dir = repo_root / "docs" / "proposals" / "prop_l1_demo_v1"
        proposal_dir.mkdir(parents=True, exist_ok=True)
        (proposal_dir / "proposal.json").write_text(
            json.dumps({"proposal_id": "prop_l1_demo_v1", "abstraction_layer": "circuit_block"}, indent=2) + "\n",
            encoding="utf-8",
        )
        (proposal_dir / "evaluation_requests.json").write_text(
            json.dumps({"proposal_id": "prop_l1_demo_v1", "source_commit": "", "requested_items": []}, indent=2) + "\n",
            encoding="utf-8",
        )
        source_commit = _init_git_repo(repo_root)
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            try:
                generate_l1_sweep_task(
                    session,
                    _make_l1_request(
                        repo_root=str(repo_root),
                        sweep_path=sweep_path,
                        config_paths=[config_path],
                        platform="nangate45",
                        out_root="runs/designs/activations",
                        item_id="l1_demo_softmax_proposal_r1",
                        requested_by="@tester",
                        source_commit=source_commit,
                        proposal_id="prop_l1_demo_v1",
                        proposal_path="docs/proposals/prop_l1_demo_v1",
                        abstraction_layer="circuit_block",
                        make_target="1_2_yosys",
                        acceptance_notes="Accept flow_failed rows as explicit boundary evidence.",
                        update_proposal_files=True,
                    ),
                )
            except Layer1TaskGenerationError as exc:
                assert "clean exact-generation worktree" in str(exc)
            else:
                raise AssertionError("expected Layer1TaskGenerationError")

            assert session.query(WorkItem).count() == 0
            assert session.query(TaskRequest).count() == 0
            staged_request = json.loads(
                (proposal_dir / "evaluation_requests.json").read_text(encoding="utf-8")
            )["requested_items"][0]
            assert staged_request["make_target"] == "1_2_yosys"

            clean_commit = _commit_repo_changes(repo_root, "commit l1 proposal metadata fixture")
            result = generate_l1_sweep_task(
                session,
                _make_l1_request(
                    repo_root=str(repo_root),
                    sweep_path=sweep_path,
                    config_paths=[config_path],
                    platform="nangate45",
                    out_root="runs/designs/activations",
                    item_id="l1_demo_softmax_proposal_r1",
                    requested_by="@tester",
                    source_commit=clean_commit,
                    proposal_id="prop_l1_demo_v1",
                    proposal_path="docs/proposals/prop_l1_demo_v1",
                    abstraction_layer="circuit_block",
                    acceptance_notes="Accept flow_failed rows as explicit boundary evidence.",
                    update_proposal_files=False,
                ),
            )
            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            assert work_item.task_request.request_payload["developer_loop"]["evaluation"][
                "mode"
            ] == "synth_prefilter"

        assert result.status == "applied"
        evaluation_requests = json.loads((proposal_dir / "evaluation_requests.json").read_text(encoding="utf-8"))
        assert evaluation_requests["source_commit"] == source_commit
        assert evaluation_requests["requested_items"] == [
            {
                "item_id": "l1_demo_softmax_proposal_r1",
                "task_type": "l1_sweep",
                "objective": (
                    "Run a Layer1 nangate45 OpenROAD sweep for 1 configs using "
                    "nangate45_softmax_rowwise_v1.json and record lightweight design metrics for comparison."
                ),
                "evaluation_mode": "synth_prefilter",
                "make_target": "1_2_yosys",
                "abstraction_layer": "circuit_block",
                "comparison_role": "",
                "paired_baseline_item_id": "",
                "depends_on_item_ids": [],
                "requires_merged_inputs": False,
                "requires_materialized_refs": False,
                "acceptance_notes": "Accept flow_failed rows as explicit boundary evidence.",
                "status": "pending",
            }
        ]
        for name in (
            "proposal.json",
            "evaluation_requests.json",
            "promotion_decision.json",
            "promotion_result.json",
            "README.md",
            "analysis_report.md",
        ):
            assert (proposal_dir / name).exists()


def test_generate_l1_sweep_task_can_refresh_db_without_updating_proposal_files() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        config_path, sweep_path = _write_example_repo(repo_root)
        proposal_dir = repo_root / "docs" / "proposals" / "prop_l1_demo_v1"
        proposal_dir.mkdir(parents=True, exist_ok=True)
        (proposal_dir / "proposal.json").write_text(
            json.dumps({"proposal_id": "prop_l1_demo_v1", "abstraction_layer": "circuit_block"}, indent=2) + "\n",
            encoding="utf-8",
        )
        evaluation_requests_path = proposal_dir / "evaluation_requests.json"
        evaluation_requests_path.write_text(
            json.dumps(
                {
                    "proposal_id": "prop_l1_demo_v1",
                    "source_commit": "previous",
                    "requested_items": [],
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        before = evaluation_requests_path.read_text(encoding="utf-8")
        source_commit = _init_git_repo(repo_root)
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            result = generate_l1_sweep_task(
                session,
                _make_l1_request(
                    repo_root=str(repo_root),
                    sweep_path=sweep_path,
                    config_paths=[config_path],
                    platform="nangate45",
                    out_root="runs/designs/activations",
                    item_id="l1_demo_softmax_proposal_r1",
                    requested_by="@tester",
                    source_commit=source_commit,
                    proposal_id="prop_l1_demo_v1",
                    proposal_path="docs/proposals/prop_l1_demo_v1",
                    abstraction_layer="circuit_block",
                    update_proposal_files=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            assert result.status == "applied"
            assert work_item.source_commit == source_commit
            assert work_item.task_request.source_commit == source_commit
            assert work_item.task_request.request_payload["developer_loop"]["proposal_id"] == "prop_l1_demo_v1"

        assert evaluation_requests_path.read_text(encoding="utf-8") == before


def test_generate_l1_sweep_task_rejects_db_creation_when_proposal_upsert_dirties_worktree() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        config_path, sweep_path = _write_example_repo(repo_root)
        proposal_dir = repo_root / "docs" / "proposals" / "prop_l1_dirty_generation_guard_v1"
        proposal_dir.mkdir(parents=True, exist_ok=True)
        (proposal_dir / "proposal.json").write_text(
            json.dumps({"proposal_id": "prop_l1_dirty_generation_guard_v1", "abstraction_layer": "circuit_block"}, indent=2) + "\n",
            encoding="utf-8",
        )
        source_commit = _init_git_repo(repo_root)
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            try:
                generate_l1_sweep_task(
                    session,
                    _make_l1_request(
                        repo_root=str(repo_root),
                        sweep_path=sweep_path,
                        config_paths=[config_path],
                        platform="nangate45",
                        out_root="runs/designs/activations",
                        item_id="l1_demo_dirty_generation_guard_r1",
                        requested_by="@tester",
                        source_commit=source_commit,
                        proposal_id="prop_l1_dirty_generation_guard_v1",
                        proposal_path="docs/proposals/prop_l1_dirty_generation_guard_v1",
                        update_proposal_files=True,
                    ),
                )
            except Layer1TaskGenerationError as exc:
                message = str(exc)
                assert "clean exact-generation worktree" in message
                assert "git status --porcelain is not empty" in message
                assert "docs/proposals/prop_l1_dirty_generation_guard_v1/" in message
            else:
                raise AssertionError("expected Layer1TaskGenerationError")

            assert session.query(WorkItem).count() == 0
            assert session.query(TaskRequest).count() == 0
            assert (proposal_dir / "evaluation_requests.json").exists()


def test_generate_l1_sweep_task_succeeds_after_committed_rerun_without_proposal_updates() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        config_path, sweep_path = _write_example_repo(repo_root)
        proposal_dir = repo_root / "docs" / "proposals" / "prop_l1_dirty_generation_guard_v1"
        proposal_dir.mkdir(parents=True, exist_ok=True)
        (proposal_dir / "proposal.json").write_text(
            json.dumps({"proposal_id": "prop_l1_dirty_generation_guard_v1", "abstraction_layer": "circuit_block"}, indent=2) + "\n",
            encoding="utf-8",
        )
        source_commit = _init_git_repo(repo_root)
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            try:
                generate_l1_sweep_task(
                    session,
                    _make_l1_request(
                        repo_root=str(repo_root),
                        sweep_path=sweep_path,
                        config_paths=[config_path],
                        platform="nangate45",
                        out_root="runs/designs/activations",
                        item_id="l1_demo_dirty_generation_guard_r1",
                        requested_by="@tester",
                        source_commit=source_commit,
                        proposal_id="prop_l1_dirty_generation_guard_v1",
                        proposal_path="docs/proposals/prop_l1_dirty_generation_guard_v1",
                        update_proposal_files=True,
                    ),
                )
            except Layer1TaskGenerationError:
                pass
            else:
                raise AssertionError("expected initial Layer1TaskGenerationError")

            clean_commit = _commit_repo_changes(repo_root, "commit l1 proposal upsert artifacts")
            result = generate_l1_sweep_task(
                session,
                _make_l1_request(
                    repo_root=str(repo_root),
                    sweep_path=sweep_path,
                    config_paths=[config_path],
                    platform="nangate45",
                    out_root="runs/designs/activations",
                    item_id="l1_demo_dirty_generation_guard_r1",
                    requested_by="@tester",
                    source_commit=clean_commit,
                    proposal_id="prop_l1_dirty_generation_guard_v1",
                    proposal_path="docs/proposals/prop_l1_dirty_generation_guard_v1",
                    update_proposal_files=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            assert result.status == "applied"
            assert work_item.source_commit == clean_commit
            assert work_item.task_request.request_payload["generation_source_identity"] == {
                "version": 1,
                "declared_source_commit": clean_commit,
                "repo_head_sha": clean_commit,
                "relation": "exact",
                "proof": "generator_worktree_head_exact",
                "clean": True,
            }


def test_generate_l1_sweep_task_inherits_proposal_dependencies_and_starts_blocked() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        config_path, sweep_path = _write_example_repo(repo_root)
        item_id = "l1_demo_dependent_pnr_v1"
        dependency_item_id = "l2_demo_equivalence_v1"
        proposal_dir = repo_root / "docs" / "proposals" / "prop_l1_dependent_v1"
        proposal_dir.mkdir(parents=True, exist_ok=True)
        (proposal_dir / "proposal.json").write_text(
            json.dumps(
                {"proposal_id": "prop_l1_dependent_v1", "abstraction_layer": "circuit_block"},
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (proposal_dir / "evaluation_requests.json").write_text(
            json.dumps(
                {
                    "proposal_id": "prop_l1_dependent_v1",
                    "requested_items": [
                        {
                            "item_id": item_id,
                            "task_type": "l1_sweep",
                            "evaluation_mode": "frontier_followup",
                            "abstraction_layer": "circuit_block",
                            "comparison_role": "candidate_pnr",
                            "paired_baseline_item_id": "l1_demo_baseline_pnr_v1",
                            "depends_on_item_ids": [dependency_item_id],
                            "requires_merged_inputs": True,
                            "requires_materialized_refs": True,
                            "expected_result": {
                                "direction": "measure_candidate_ppa",
                                "reason": "Run PPA only after equivalence evidence is merged.",
                            },
                        }
                    ],
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        source_commit = _init_git_repo(repo_root)
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            result = generate_l1_sweep_task(
                session,
                _make_l1_request(
                    repo_root=str(repo_root),
                    sweep_path=sweep_path,
                    config_paths=[config_path],
                    platform="nangate45",
                    out_root="runs/designs/activations",
                    item_id=item_id,
                    requested_by="@tester",
                    source_commit=source_commit,
                    proposal_id="prop_l1_dependent_v1",
                    proposal_path="docs/proposals/prop_l1_dependent_v1",
                    update_proposal_files=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            payload = work_item.task_request.request_payload
            assert work_item.state == WorkItemState.BLOCKED
            assert payload["developer_loop"]["evaluation"] == {
                "mode": "frontier_followup",
                "expected_direction": "measure_candidate_ppa",
                "expected_reason": "Run PPA only after equivalence evidence is merged.",
                "trial_policy": {"trial_count": 1, "seed_start": 0, "stop_after_failures": 1},
            }
            assert payload["developer_loop"]["comparison"] == {
                "role": "candidate_pnr",
                "paired_baseline_item_id": "l1_demo_baseline_pnr_v1",
            }
            assert payload["developer_loop"]["dependencies"] == {
                "item_ids": [dependency_item_id],
                "requires_merged_inputs": True,
                "requires_materialized_refs": True,
            }


def test_generate_l1_sweep_task_explicit_dependencies_create_blocked_item_without_proposal_metadata() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        config_path, sweep_path = _write_example_repo(repo_root)
        source_commit = _init_git_repo(repo_root)
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            result = generate_l1_sweep_task(
                session,
                _make_l1_request(
                    repo_root=str(repo_root),
                    sweep_path=sweep_path,
                    config_paths=[config_path],
                    platform="nangate45",
                    out_root="runs/designs/activations",
                    item_id="l1_demo_explicit_dependency_v1",
                    requested_by="@tester",
                    source_commit=source_commit,
                    depends_on_item_ids=["l2_missing_equivalence_v1"],
                    requires_merged_inputs=True,
                    requires_materialized_refs=True,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            assert work_item.state == WorkItemState.BLOCKED
            assert work_item.task_request.request_payload["developer_loop"]["dependencies"] == {
                "item_ids": ["l2_missing_equivalence_v1"],
                "requires_merged_inputs": True,
                "requires_materialized_refs": True,
            }


def test_generate_l1_sweep_task_starts_dispatch_pending_when_dependency_is_merged_and_materialized() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        config_path, sweep_path = _write_example_repo(repo_root)
        source_commit = _init_git_repo(repo_root)
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            _seed_materialized_dependency(
                session,
                repo_root=repo_root,
                item_id="l2_demo_equivalence_v1",
                layer="layer2",
                task_type="l2_campaign",
                source_commit=source_commit,
                artifact_kind="decision_proposal",
                expected_output_rel="runs/campaigns/l2_demo_equivalence_v1/summary.csv",
            )
            session.commit()
            source_commit = _commit_repo_changes(repo_root, "commit seeded dependency artifacts")

            result = generate_l1_sweep_task(
                session,
                _make_l1_request(
                    repo_root=str(repo_root),
                    sweep_path=sweep_path,
                    config_paths=[config_path],
                    platform="nangate45",
                    out_root="runs/designs/activations",
                    item_id="l1_demo_dependency_satisfied_v1",
                    requested_by="@tester",
                    source_commit=source_commit,
                    depends_on_item_ids=["l2_demo_equivalence_v1"],
                    requires_merged_inputs=True,
                    requires_materialized_refs=True,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            assert work_item.state == WorkItemState.DISPATCH_PENDING
            assert work_item.task_request.request_payload["developer_loop"]["dependencies"] == {
                "item_ids": ["l2_demo_equivalence_v1"],
                "requires_merged_inputs": True,
                "requires_materialized_refs": True,
            }


def test_generate_l1_sweep_task_auto_discovers_proposal_for_existing_item() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        config_path, _ = _write_example_attention_decode_score_multivalue_cluster_repo(repo_root)
        sweep_path = _write_attention_decode_score_multivalue_cluster_8ns_bridge_sweep(repo_root)
        proposal_dir = repo_root / "docs" / "proposals" / "prop_decoder_attention_decode_score_multivalue_cluster_llama7b_v1"
        proposal_dir.mkdir(parents=True)
        item_id = "l1_decoder_attention_decode_score_multivalue_cluster_pnr_8ns_v2"
        required_entry = {
            "item_id": item_id,
            "task_type": "l1_sweep",
            "objective": "Re-run the shared-score multivalue cluster at 8 ns for the 2.5 mm die / 2.4 mm square core bridge evidence.",
            "evaluation_mode": "frontier_followup",
            "abstraction_layer": "decoder_attention_decode_score_multivalue_cluster",
            "comparison_role": "shared_score_multivalue_cluster_pnr",
            "depends_on_item_ids": ["l2_decoder_attention_decode_score_multivalue_cluster_equivalence_llama7b_v1"],
            "requires_merged_inputs": True,
            "requires_materialized_refs": True,
            "expected_result": {
                "direction": "measure_shared_score_multivalue_cluster_ppa",
                "reason": "Collect the missing 8 ns Nangate45 evidence in 2.5 mm envelope while keeping current vectorless metrics as bounded frontier evidence.",
            },
            "config_paths": [
                "runs/designs/npu_blocks/attention_decode_score_multivalue_cluster_int8_m1x8_iterdiv/config.json"
            ],
            "sweep_path": "runs/campaigns/npu/decode_score_multivalue_cluster_v1/sweeps/"
            "nangate45_decode_score_multivalue_cluster_8ns_proxy_die_2500.json",
            "status": "pending_implementation_merge",
        }
        (proposal_dir / "proposal.json").write_text(
            json.dumps(
                {
                    "proposal_id": "prop_decoder_attention_decode_score_multivalue_cluster_llama7b_v1",
                    "required_evaluations": [required_entry],
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (proposal_dir / "evaluation_requests.json").write_text(
            json.dumps(
                {
                    "proposal_id": "prop_decoder_attention_decode_score_multivalue_cluster_llama7b_v1",
                    "source_commit": "",
                    "requested_items": [required_entry],
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        source_commit = _init_git_repo(repo_root)
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            result = generate_l1_sweep_task(
                session,
                _make_l1_request(
                    repo_root=str(repo_root),
                    sweep_path=sweep_path,
                    config_paths=[config_path],
                    platform="nangate45",
                    out_root="runs/designs/activations",
                    item_id=item_id,
                    requested_by="@tester",
                    source_commit=source_commit,
                    # No proposal fields provided; auto-discovery should infer proposal linkage.
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=item_id).one()
            payload = work_item.task_request.request_payload["developer_loop"]
            assert work_item.state == WorkItemState.BLOCKED
            assert payload["proposal_id"] == "prop_decoder_attention_decode_score_multivalue_cluster_llama7b_v1"
            assert (
                payload["proposal_path"]
                == "docs/proposals/prop_decoder_attention_decode_score_multivalue_cluster_llama7b_v1"
            )
            assert payload["dependencies"] == {
                "item_ids": ["l2_decoder_attention_decode_score_multivalue_cluster_equivalence_llama7b_v1"],
                "requires_merged_inputs": True,
                "requires_materialized_refs": True,
            }
            assert payload["evaluation"] == {
                "mode": "frontier_followup",
                "expected_direction": "measure_shared_score_multivalue_cluster_ppa",
                "expected_reason": (
                    "Collect the missing 8 ns Nangate45 evidence in 2.5 mm envelope while keeping "
                    "current vectorless metrics as bounded frontier evidence."
                ),
                "trial_policy": {"trial_count": 1, "seed_start": 0, "stop_after_failures": 1},
            }

        assert result.status == "applied"


def test_generate_l1_sweep_task_strips_placeholder_requested_items_from_template() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        config_path, sweep_path = _write_example_repo(repo_root)
        template_dir = repo_root / "docs" / "proposals" / "_template"
        template_dir.mkdir(parents=True, exist_ok=True)
        (template_dir / "evaluation_requests.json").write_text(
            json.dumps(
                {
                    "proposal_id": "prop_example_v1",
                    "source_commit": "git-sha",
                    "requested_items": [
                        {
                            "item_id": "example_item_id",
                            "task_type": "l2_campaign",
                            "objective": "balanced",
                            "candidate_id": "cand_example_v1_r1",
                        }
                    ],
                },
                indent=2,
            ) + "\n",
            encoding="utf-8",
        )
        source_commit = _init_git_repo(repo_root)
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            try:
                generate_l1_sweep_task(
                    session,
                    _make_l1_request(
                        repo_root=str(repo_root),
                        sweep_path=sweep_path,
                        config_paths=[config_path],
                        platform="nangate45",
                        out_root="runs/designs/activations",
                        item_id="l1_demo_softmax_template_r1",
                        requested_by="@tester",
                        source_commit=source_commit,
                        proposal_id="prop_l1_template_v1",
                        proposal_path="docs/proposals/prop_l1_template_v1",
                        abstraction_layer="circuit_block",
                        update_proposal_files=True,
                    ),
                )
            except Layer1TaskGenerationError as exc:
                assert "clean exact-generation worktree" in str(exc)
            else:
                raise AssertionError("expected Layer1TaskGenerationError")

            assert session.query(WorkItem).count() == 0
            assert session.query(TaskRequest).count() == 0

            clean_commit = _commit_repo_changes(repo_root, "commit l1 template proposal fixture")
            result = generate_l1_sweep_task(
                session,
                _make_l1_request(
                    repo_root=str(repo_root),
                    sweep_path=sweep_path,
                    config_paths=[config_path],
                    platform="nangate45",
                    out_root="runs/designs/activations",
                    item_id="l1_demo_softmax_template_r1",
                    requested_by="@tester",
                    source_commit=clean_commit,
                    proposal_id="prop_l1_template_v1",
                    proposal_path="docs/proposals/prop_l1_template_v1",
                    abstraction_layer="circuit_block",
                    update_proposal_files=False,
                ),
            )

        assert result.status == "applied"
        proposal_dir = repo_root / "docs" / "proposals" / "prop_l1_template_v1"
        evaluation_requests = json.loads((proposal_dir / "evaluation_requests.json").read_text(encoding="utf-8"))
        assert evaluation_requests["requested_items"] == [
            {
                "item_id": "l1_demo_softmax_template_r1",
                "task_type": "l1_sweep",
                "objective": (
                    "Run a Layer1 nangate45 OpenROAD sweep for 1 configs using "
                    "nangate45_softmax_rowwise_v1.json and record lightweight design metrics for comparison."
                ),
                "evaluation_mode": "measurement_only",
                "abstraction_layer": "circuit_block",
                "comparison_role": "",
                "paired_baseline_item_id": "",
                "depends_on_item_ids": [],
                "requires_merged_inputs": False,
                "requires_materialized_refs": False,
                "status": "pending",
            }
        ]


def test_generate_l1_sweep_task_omits_runtime_submodules_when_image_provides_deps() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        config_path, sweep_path = _write_example_repo(repo_root)
        source_commit = _init_git_repo(repo_root)
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            with patch(
                "control_plane.services.l1_task_generator._image_provided_l1_runtime_deps_available",
                return_value=True,
            ):
                result = generate_l1_sweep_task(
                    session,
                    _make_l1_request(
                        repo_root=str(repo_root),
                        sweep_path=sweep_path,
                        config_paths=[config_path],
                        platform="nangate45",
                        out_root="runs/designs/activations",
                        item_id="l1_demo_softmax_image_deps",
                        title="Layer1 demo image deps",
                        requested_by="@tester",
                        source_commit=source_commit,
                    ),
                )

            assert result.status == "applied"
            work_item = session.get(WorkItem, result.work_item_id)
            assert work_item is not None
            payload = work_item.task_request.request_payload
            assert payload["task"]["inputs"]["required_submodules"] == []


def test_generate_l1_sweep_task_upserts_existing_item() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        config_path, sweep_path = _write_example_repo(repo_root)
        source_commit = _init_git_repo(repo_root)
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            first = generate_l1_sweep_task(
                session,
                _make_l1_request(
                    repo_root=str(repo_root),
                    sweep_path=sweep_path,
                    config_paths=[config_path],
                    platform="nangate45",
                    out_root="runs/designs/activations",
                    item_id="l1_demo_softmax",
                    title="Layer1 demo",
                    requested_by="@tester",
                    source_commit=source_commit,
                ),
            )
            second = generate_l1_sweep_task(
                session,
                _make_l1_request(
                    repo_root=str(repo_root),
                    sweep_path=sweep_path,
                    config_paths=[config_path],
                    platform="nangate45",
                    out_root="runs/designs/activations",
                    item_id="l1_demo_softmax",
                    title="Layer1 demo updated",
                    requested_by="@tester2",
                    source_commit=source_commit,
                ),
            )

            assert first.status == "applied"
            assert second.status == "applied"
            work_item = session.query(WorkItem).filter_by(item_id="l1_demo_softmax").one()
            assert work_item.task_request.title == "Layer1 demo updated"
            assert work_item.task_request.requested_by == "@tester2"


def test_generate_l1_sweep_task_preserves_running_item_on_upsert_even_when_new_dependencies_are_unsatisfied() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        config_path, sweep_path = _write_example_repo(repo_root)
        source_commit = _init_git_repo(repo_root)
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            result = generate_l1_sweep_task(
                session,
                _make_l1_request(
                    repo_root=str(repo_root),
                    sweep_path=sweep_path,
                    config_paths=[config_path],
                    platform="nangate45",
                    out_root="runs/designs/activations",
                    item_id="l1_demo_running_v1",
                    requested_by="@tester",
                    source_commit=source_commit,
                ),
            )
            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            work_item.state = WorkItemState.RUNNING
            work_item.assigned_machine_key = "eval-a"
            session.commit()

            generate_l1_sweep_task(
                session,
                _make_l1_request(
                    repo_root=str(repo_root),
                    sweep_path=sweep_path,
                    config_paths=[config_path],
                    platform="nangate45",
                    out_root="runs/designs/activations",
                    item_id="l1_demo_running_v1",
                    requested_by="@tester2",
                    source_commit=source_commit,
                    depends_on_item_ids=["l2_missing_equivalence_v1"],
                    requires_merged_inputs=True,
                    requires_materialized_refs=True,
                ),
            )

            session.refresh(work_item)
            assert work_item.state == WorkItemState.RUNNING
            assert work_item.assigned_machine_key == "eval-a"
            assert work_item.task_request.requested_by == "@tester2"
            assert work_item.task_request.request_payload["developer_loop"]["dependencies"]["item_ids"] == [
                "l2_missing_equivalence_v1"
            ]


def test_generate_l1_sweep_task_preserves_merged_item_on_upsert() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        config_path, sweep_path = _write_example_repo(repo_root)
        source_commit = _init_git_repo(repo_root)
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            result = generate_l1_sweep_task(
                session,
                _make_l1_request(
                    repo_root=str(repo_root),
                    sweep_path=sweep_path,
                    config_paths=[config_path],
                    platform="nangate45",
                    out_root="runs/designs/activations",
                    item_id="l1_demo_merged_v1",
                    requested_by="@tester",
                    source_commit=source_commit,
                ),
            )
            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            work_item.state = WorkItemState.MERGED
            session.commit()

            generate_l1_sweep_task(
                session,
                _make_l1_request(
                    repo_root=str(repo_root),
                    sweep_path=sweep_path,
                    config_paths=[config_path],
                    platform="nangate45",
                    out_root="runs/designs/activations",
                    item_id="l1_demo_merged_v1",
                    title="Layer1 merged item updated",
                    requested_by="@tester2",
                    source_commit=source_commit,
                    depends_on_item_ids=["l2_missing_equivalence_v1"],
                    requires_merged_inputs=True,
                    requires_materialized_refs=True,
                ),
            )

            session.refresh(work_item)
            assert work_item.state == WorkItemState.MERGED
            assert work_item.task_request.title == "Layer1 merged item updated"


def test_generate_l1_sweep_task_supports_integrated_npu_block_configs() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        config_path, sweep_path = _write_example_block_repo(
            repo_root,
            mode_compare=False,
            synth_hierarchical=1,
        )
        source_commit = _init_git_repo(repo_root)
        proposal_dir = repo_root / "docs" / "developer_loop" / "prop_l1_npu_nm1_sigmoid_vec_enable_v1"
        proposal_dir.mkdir(parents=True, exist_ok=True)
        (proposal_dir / "proposal.json").write_text(
            json.dumps({"proposal_id": "prop_l1_npu_nm1_sigmoid_vec_enable_v1", "abstraction_layer": "architecture_block"}, indent=2) + "\n",
            encoding="utf-8",
        )
        source_commit = _commit_repo_changes(repo_root, "commit proposal metadata fixture")
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            result = generate_l1_sweep_task(
                session,
                _make_l1_request(
                    repo_root=str(repo_root),
                    sweep_path=sweep_path,
                    config_paths=[config_path],
                    platform="nangate45",
                    out_root="runs/designs/npu_blocks",
                    requested_by="@tester",
                    source_commit=source_commit,
                    proposal_id="prop_l1_npu_nm1_sigmoid_vec_enable_v1",
                    proposal_path="docs/developer_loop/prop_l1_npu_nm1_sigmoid_vec_enable_v1",
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            assert result.status == "applied"
            assert work_item.task_type == "l1_sweep"
            assert work_item.state == WorkItemState.DISPATCH_PENDING
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
                "--out_root runs/designs/npu_blocks "
                "--skip_existing"
            )
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {"layer": "architecture_block"}


def test_generate_l1_sweep_task_supports_dense_gemm_tile_configs() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        config_path, sweep_path = _write_example_dense_gemm_tile_repo(repo_root)
        source_commit = _init_git_repo(repo_root)
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            result = generate_l1_sweep_task(
                session,
                _make_l1_request(
                    repo_root=str(repo_root),
                    sweep_path=sweep_path,
                    config_paths=[config_path],
                    platform="nangate45",
                    out_root="runs/campaigns/npu/dense_gemm_tile_v1",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="architecture_block",
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            assert result.status == "applied"
            assert [command["name"] for command in work_item.command_manifest] == [
                "build_generator",
                "generate_dense_gemm_tile_rtl",
                "check_dense_gemm_tile_guard",
                "run_block_sweep",
                "build_runs_index",
                "validate",
            ]
            assert work_item.command_manifest[1]["run"] == (
                "export PATH=/oss-cad-suite/bin:$PATH && "
                "python3 npu/rtlgen/gen_dense_gemm_tile.py "
                "--config runs/designs/npu_blocks/npu_dense_gemm_tile_fp16_4x4_k1_p1/config.json "
                "--out runs/designs/npu_blocks/npu_dense_gemm_tile_fp16_4x4_k1_p1/verilog"
            )
            assert work_item.command_manifest[2]["run"] == (
                "python3 npu/eval/check_dense_gemm_tile_guard.py "
                "--design-dir runs/designs/npu_blocks/npu_dense_gemm_tile_fp16_4x4_k1_p1"
            )
            assert "--top dense_gemm_tile_fp16_4x4_k1_p1" in work_item.command_manifest[3]["run"]
            assert "--out_root runs/campaigns/npu/dense_gemm_tile_v1" in work_item.command_manifest[3]["run"]
            assert work_item.expected_outputs == [
                "runs/campaigns/npu/dense_gemm_tile_v1/npu_dense_gemm_tile_fp16_4x4_k1_p1/metrics.csv"
            ]
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "architecture_block"
            }


def test_generate_l1_sweep_task_supports_dense_gemm_tile_stream_configs() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        config_path, sweep_path = _write_example_dense_gemm_tile_stream_repo(repo_root)
        source_commit = _init_git_repo(repo_root)
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            result = generate_l1_sweep_task(
                session,
                _make_l1_request(
                    repo_root=str(repo_root),
                    sweep_path=sweep_path,
                    config_paths=[config_path],
                    platform="nangate45",
                    out_root="runs/designs/npu_blocks",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="decoder_attention_operational_dense_tile",
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            assert [command["name"] for command in work_item.command_manifest] == [
                "generate_dense_gemm_tile_stream_rtl",
                "run_block_sweep",
                "extract_dense_gemm_tile_stream_timing_paths",
                "build_runs_index",
                "validate",
            ]
            assert "gen_dense_gemm_tile_stream.py" in work_item.command_manifest[0]["run"]
            assert "--top dense_gemm_tile_stream_int8_16x8" in work_item.command_manifest[1]["run"]
            assert work_item.expected_outputs == [
                "runs/designs/npu_blocks/dense_gemm_tile_stream_int8_16x8/metrics.csv",
                "runs/designs/npu_blocks/dense_gemm_tile_stream_int8_16x8/timing_debug_report.md",
            ]


def test_generate_l1_sweep_task_supports_bare_noc_router_config() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        config_path, sweep_path = _write_example_noc_segmented_mesh_router_bare_repo(repo_root)
        source_commit = _init_git_repo(repo_root)
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            result = generate_l1_sweep_task(
                session,
                _make_l1_request(
                    repo_root=str(repo_root),
                    sweep_path=sweep_path,
                    config_paths=[config_path],
                    platform="nangate45",
                    out_root="runs/designs/npu_blocks",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="architecture_block",
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            assert [command["name"] for command in work_item.command_manifest] == [
                "stage_noc_segmented_mesh_router_bare_rtl",
                "check_noc_segmented_mesh_router_bare_guard",
                "run_block_sweep",
                "extract_noc_segmented_mesh_router_bare_timing_paths",
                "build_runs_index",
                "validate",
            ]
            assert "--top noc_segmented_mesh_router_node5" in work_item.command_manifest[2]["run"]
            assert "--isolate_flow_variant" in work_item.command_manifest[2]["run"]
            assert work_item.expected_outputs == [
                "runs/designs/npu_blocks/noc_router_node5_bare/metrics.csv",
                "runs/designs/npu_blocks/noc_router_node5_bare/timing_debug_report.md",
            ]


def test_checked_in_bare_router_requires_all_three_complete_ppa_rows() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        source_root = Path(__file__).resolve().parents[3]
        proposal_rel = "docs/proposals/prop_l1_segmented_xy_router_node5_bare_ppa_v1"
        config_rel = "runs/designs/npu_blocks/noc_segmented_mesh_router_node5_bare/config.json"
        sweep_rel = (
            "runs/campaigns/noc/l1_segmented_xy_mesh_router/sweeps/"
            "nangate45_node5_bare_v1.json"
        )
        shutil.copytree(source_root / proposal_rel, repo_root / proposal_rel)
        _copy_fixture_file(src_repo_root=source_root, dst_repo_root=repo_root, rel_path=config_rel)
        _copy_fixture_file(src_repo_root=source_root, dst_repo_root=repo_root, rel_path=sweep_rel)
        source_commit = _init_git_repo(repo_root)
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            result = generate_l1_sweep_task(
                session,
                _make_l1_request(
                    repo_root=str(repo_root),
                    sweep_path=sweep_rel,
                    config_paths=[config_rel],
                    platform="nangate45",
                    out_root="runs/designs/npu_blocks",
                    item_id="l1_segmented_xy_router_node5_bare_ppa_v1",
                    proposal_id="prop_l1_segmented_xy_router_node5_bare_ppa_v1",
                    proposal_path=f"{proposal_rel}/proposal.json",
                    source_commit=source_commit,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            task = work_item.task_request.request_payload["task"]
            assert task["metadata"]["required_complete_ppa_rows"] == 3
            assert "exactly 3 distinct status=ok param_hash rows" in task["acceptance"][0]


def test_generate_l1_sweep_task_supports_direct_noc_mesh_config() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        config_path, sweep_path = _write_example_noc_segmented_mesh4x4_direct_repo(repo_root)
        source_commit = _init_git_repo(repo_root)
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            result = generate_l1_sweep_task(
                session,
                _make_l1_request(
                    repo_root=str(repo_root),
                    sweep_path=sweep_path,
                    config_paths=[config_path],
                    platform="nangate45",
                    out_root="runs/designs/npu_blocks",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="architecture_block",
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            assert [command["name"] for command in work_item.command_manifest] == [
                "stage_noc_segmented_mesh4x4_direct_rtl",
                "check_noc_segmented_mesh4x4_direct_guard",
                "run_block_sweep",
                "check_noc_segmented_mesh4x4_direct_physical",
                "extract_noc_segmented_mesh4x4_direct_timing_paths",
                "build_runs_index",
                "validate",
            ]
            assert "--top noc_segmented_mesh4x4_functional" in work_item.command_manifest[2]["run"]
            assert "--isolate_flow_variant" in work_item.command_manifest[2]["run"]
            assert work_item.expected_outputs == [
                "runs/designs/npu_blocks/noc_mesh4x4_direct/metrics.csv",
                "runs/designs/npu_blocks/noc_mesh4x4_direct/physical_hierarchy_report.json",
                "runs/designs/npu_blocks/noc_mesh4x4_direct/timing_debug_report.md",
            ]


def test_generate_l1_sweep_task_supports_attention_dual_stream_composed_configs() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        config_path, sweep_path = _write_example_dual_stream_composed_repo(repo_root)
        source_commit = _init_git_repo(repo_root)
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            result = generate_l1_sweep_task(
                session,
                _make_l1_request(
                    repo_root=str(repo_root),
                    sweep_path=sweep_path,
                    config_paths=[config_path],
                    platform="nangate45",
                    out_root="runs/designs/npu_blocks",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="decoder_attention_dual_stream_composed_datapath",
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            assert result.status == "applied"
            assert [command["name"] for command in work_item.command_manifest] == [
                "build_generator",
                "generate_attention_dual_stream_composed_rtl",
                "check_attention_dual_stream_composed_guard",
                "run_block_sweep",
                "extract_attention_dual_stream_timing_paths",
                "build_runs_index",
                "validate",
            ]
            assert work_item.command_manifest[1]["run"] == (
                "export PATH=/oss-cad-suite/bin:$PATH && "
                "python3 npu/rtlgen/gen_attention_dual_stream_composed.py "
                "--config runs/designs/npu_blocks/attention_dual_stream_composed_smoke/config.json "
                "--out runs/designs/npu_blocks/attention_dual_stream_composed_smoke/verilog"
            )
            assert work_item.command_manifest[2]["run"] == (
                "python3 npu/eval/check_attention_dual_stream_composed_guard.py "
                "--design-dir runs/designs/npu_blocks/attention_dual_stream_composed_smoke"
            )
            assert "--top attention_dual_stream_composed_smoke" in work_item.command_manifest[3]["run"]
            assert work_item.command_manifest[4]["run"] == (
                "python3 npu/eval/extract_openroad_timing_summary.py "
                "--design-dir runs/designs/npu_blocks/attention_dual_stream_composed_smoke "
                "--out runs/designs/npu_blocks/attention_dual_stream_composed_smoke/timing_debug_report.md "
                "--max-paths 8"
            )
            assert work_item.expected_outputs == [
                "runs/designs/npu_blocks/attention_dual_stream_composed_smoke/metrics.csv",
                "runs/designs/npu_blocks/attention_dual_stream_composed_smoke/timing_debug_report.md",
            ]
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_attention_dual_stream_composed_datapath"
            }


def test_generate_l1_sweep_task_supports_attention_command_dispatch_configs() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        config_path, sweep_path = _write_example_attention_command_dispatch_repo(repo_root)
        source_commit = _init_git_repo(repo_root)
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            result = generate_l1_sweep_task(
                session,
                _make_l1_request(
                    repo_root=str(repo_root),
                    sweep_path=sweep_path,
                    config_paths=[config_path],
                    platform="nangate45",
                    out_root="runs/designs/npu_blocks",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="decoder_attention_command_dispatch_control",
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            assert result.status == "applied"
            assert [command["name"] for command in work_item.command_manifest] == [
                "generate_attention_command_dispatch_rtl",
                "check_attention_command_dispatch_guard",
                "run_block_sweep",
                "extract_attention_command_dispatch_timing_paths",
                "build_runs_index",
                "validate",
            ]
            assert work_item.command_manifest[0]["run"] == (
                "export PATH=/oss-cad-suite/bin:$PATH && "
                "python3 npu/rtlgen/gen_attention_command_dispatch.py "
                "--config runs/designs/npu_blocks/attention_command_dispatch_smoke/config.json "
                "--out runs/designs/npu_blocks/attention_command_dispatch_smoke/verilog"
            )
            assert work_item.command_manifest[1]["run"] == (
                "python3 npu/eval/check_attention_command_dispatch_guard.py "
                "--design-dir runs/designs/npu_blocks/attention_command_dispatch_smoke"
            )
            assert "--top attention_command_dispatch_smoke" in work_item.command_manifest[2]["run"]
            assert work_item.command_manifest[3]["run"] == (
                "python3 npu/eval/extract_openroad_timing_summary.py "
                "--design-dir runs/designs/npu_blocks/attention_command_dispatch_smoke "
                "--out runs/designs/npu_blocks/attention_command_dispatch_smoke/timing_debug_report.md "
                "--max-paths 8"
            )
            assert work_item.expected_outputs == [
                "runs/designs/npu_blocks/attention_command_dispatch_smoke/metrics.csv",
                "runs/designs/npu_blocks/attention_command_dispatch_smoke/timing_debug_report.md",
            ]
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_attention_command_dispatch_control"
            }


def test_generate_l1_sweep_task_supports_attention_score32_exact_root_finalizer_configs() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        config_path, sweep_path = _write_example_attention_score32_exact_root_finalizer_repo(repo_root)
        source_commit = _init_git_repo(repo_root)
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            result = generate_l1_sweep_task(
                session,
                _make_l1_request(
                    repo_root=str(repo_root),
                    sweep_path=sweep_path,
                    config_paths=[config_path],
                    platform="nangate45",
                    out_root="runs/designs/npu_blocks",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="architecture_block",
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            assert [command["name"] for command in work_item.command_manifest] == [
                "generate_attention_score32_exact_root_finalizer_rtl",
                "check_attention_score32_exact_root_finalizer_guard",
                "run_block_sweep",
                "extract_attention_score32_exact_root_finalizer_timing_paths",
                "build_runs_index",
                "validate",
            ]
            assert work_item.command_manifest[0]["run"] == (
                "export PATH=/oss-cad-suite/bin:$PATH && "
                "python3 npu/rtlgen/gen_attention_score32_exact_root_finalizer.py "
                "--config runs/designs/npu_blocks/attention_score32_exact_root_finalizer_smoke_l4/config.json "
                "--out runs/designs/npu_blocks/attention_score32_exact_root_finalizer_smoke_l4/verilog"
            )
            assert work_item.command_manifest[1]["run"] == (
                "python3 npu/eval/check_attention_score32_exact_root_finalizer_guard.py "
                "--design-dir runs/designs/npu_blocks/attention_score32_exact_root_finalizer_smoke_l4 "
                "--config runs/designs/npu_blocks/attention_score32_exact_root_finalizer_smoke_l4/config.json"
            )
            assert "--top attention_score32_exact_root_finalizer_smoke_l4" in work_item.command_manifest[2]["run"]
            assert work_item.command_manifest[3]["run"] == (
                "python3 npu/eval/extract_openroad_timing_summary.py "
                "--design-dir runs/designs/npu_blocks/attention_score32_exact_root_finalizer_smoke_l4 "
                "--out runs/designs/npu_blocks/attention_score32_exact_root_finalizer_smoke_l4/timing_debug_report.md "
                "--max-paths 8"
            )
            assert work_item.expected_outputs == [
                "runs/designs/npu_blocks/attention_score32_exact_root_finalizer_smoke_l4/metrics.csv",
                "runs/designs/npu_blocks/attention_score32_exact_root_finalizer_smoke_l4/timing_debug_report.md",
            ]
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "architecture_block"
            }


def test_generate_l1_sweep_task_supports_attention_score32_exact_partial_tree_configs() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        config_path, sweep_path = _write_example_attention_score32_exact_partial_tree_repo(repo_root)
        source_commit = _init_git_repo(repo_root)
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            result = generate_l1_sweep_task(
                session,
                _make_l1_request(
                    repo_root=str(repo_root),
                    sweep_path=sweep_path,
                    config_paths=[config_path],
                    platform="nangate45",
                    out_root="runs/designs/npu_blocks",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="architecture_block",
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            assert [command["name"] for command in work_item.command_manifest] == [
                "generate_attention_score32_exact_partial_tree_rtl",
                "check_attention_score32_exact_partial_tree_guard",
                "run_block_sweep",
                "extract_attention_score32_exact_partial_tree_timing_paths",
                "build_runs_index",
                "validate",
            ]
            assert work_item.command_manifest[0]["run"] == (
                "export PATH=/oss-cad-suite/bin:$PATH && "
                "python3 npu/rtlgen/gen_attention_score32_exact_partial_tree.py "
                "--config runs/designs/npu_blocks/attention_score32_exact_partial_tree_smoke_c4_r2/config.json "
                "--out runs/designs/npu_blocks/attention_score32_exact_partial_tree_smoke_c4_r2/verilog"
            )
            assert work_item.command_manifest[1]["run"] == (
                "python3 npu/eval/check_attention_score32_exact_partial_tree_guard.py "
                "--design-dir runs/designs/npu_blocks/attention_score32_exact_partial_tree_smoke_c4_r2 "
                "--config runs/designs/npu_blocks/attention_score32_exact_partial_tree_smoke_c4_r2/config.json "
                "--sweep runs/campaigns/npu/attention_score32_exact_partial_tree_v1/sweeps/"
                "nangate45_attention_score32_exact_partial_tree_cluster_firstpass.json"
            )
            assert "--top attention_score32_exact_partial_tree_smoke_c4_r2" in work_item.command_manifest[2]["run"]
            assert work_item.command_manifest[3]["run"] == (
                "python3 npu/eval/extract_openroad_timing_summary.py "
                "--design-dir runs/designs/npu_blocks/attention_score32_exact_partial_tree_smoke_c4_r2 "
                "--out runs/designs/npu_blocks/attention_score32_exact_partial_tree_smoke_c4_r2/timing_debug_report.md "
                "--max-paths 8"
            )
            assert work_item.expected_outputs == [
                "runs/designs/npu_blocks/attention_score32_exact_partial_tree_smoke_c4_r2/metrics.csv",
                "runs/designs/npu_blocks/attention_score32_exact_partial_tree_smoke_c4_r2/timing_debug_report.md",
            ]
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "architecture_block"
            }


def test_generate_l1_sweep_task_supports_attention_score32_exact_partial_tree_folded_mersenne_configs() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        config_path, sweep_path = _write_example_attention_score32_exact_partial_tree_folded_mersenne_repo(repo_root)
        source_commit = _init_git_repo(repo_root)
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            result = generate_l1_sweep_task(
                session,
                _make_l1_request(
                    repo_root=str(repo_root),
                    sweep_path=sweep_path,
                    config_paths=[config_path],
                    platform="nangate45",
                    out_root="runs/designs/npu_blocks",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="architecture_block",
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            assert work_item.command_manifest[1]["run"] == (
                "python3 npu/eval/check_attention_score32_exact_partial_tree_guard.py "
                "--design-dir runs/designs/npu_blocks/attention_score32_exact_partial_tree_folded_mersenne_smoke_c4_r2 "
                "--config runs/designs/npu_blocks/attention_score32_exact_partial_tree_folded_mersenne_smoke_c4_r2/config.json "
                "--sweep runs/campaigns/npu/attention_score32_exact_partial_tree_folded_mersenne_v1/sweeps/"
                "nangate45_attention_score32_exact_partial_tree_folded_mersenne_cluster_v1.json"
            )
            assert work_item.expected_outputs == [
                "runs/designs/npu_blocks/attention_score32_exact_partial_tree_folded_mersenne_smoke_c4_r2/metrics.csv",
                "runs/designs/npu_blocks/attention_score32_exact_partial_tree_folded_mersenne_smoke_c4_r2/timing_debug_report.md",
            ]


def test_generate_l1_sweep_task_supports_attention_score32_exact_partial_pair_merge_folded_configs() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        config_path, sweep_path = _write_example_attention_score32_exact_partial_pair_merge_folded_repo(repo_root)
        source_commit = _init_git_repo(repo_root)
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            result = generate_l1_sweep_task(
                session,
                _make_l1_request(
                    repo_root=str(repo_root),
                    sweep_path=sweep_path,
                    config_paths=[config_path],
                    platform="nangate45",
                    out_root="runs/designs/npu_blocks",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="architecture_block",
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            assert [command["name"] for command in work_item.command_manifest] == [
                "generate_attention_score32_exact_partial_pair_merge_folded_rtl",
                "check_attention_score32_exact_partial_pair_merge_folded_guard",
                "run_block_sweep",
                "extract_attention_score32_exact_partial_pair_merge_folded_timing_paths",
                "build_runs_index",
                "validate",
            ]
            assert work_item.command_manifest[0]["run"] == (
                "export PATH=/oss-cad-suite/bin:$PATH && "
                "python3 npu/rtlgen/gen_attention_score32_exact_partial_pair_merge_folded.py "
                "--config "
                "runs/designs/npu_blocks/attention_score32_exact_partial_pair_merge_sharedscale_factored_l1/config.json "
                "--out "
                "runs/designs/npu_blocks/attention_score32_exact_partial_pair_merge_sharedscale_factored_l1/verilog"
            )
            assert (
                "--sweep runs/campaigns/npu/attention_score32_exact_partial_pair_merge_sharedscale_v1/sweeps/"
                "nangate45_attention_score32_exact_partial_pair_merge_sharedscale_factored_l1.json"
                in work_item.command_manifest[1]["run"]
            )
            assert "--top attention_score32_exact_partial_pair_merge_sharedscale_factored_l1" in (
                work_item.command_manifest[2]["run"]
            )
            assert work_item.expected_outputs == [
                "runs/designs/npu_blocks/attention_score32_exact_partial_pair_merge_sharedscale_factored_l1/metrics.csv",
                "runs/designs/npu_blocks/attention_score32_exact_partial_pair_merge_sharedscale_factored_l1/"
                "timing_debug_report.md",
            ]


def test_generate_l1_sweep_task_supports_attention_score32_exact_partial_pair_merge_folded_mersenne_configs() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        config_path, sweep_path = _write_example_attention_score32_exact_partial_pair_merge_folded_mersenne_repo(
            repo_root
        )
        source_commit = _init_git_repo(repo_root)
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)
        with Session(engine) as session:
            result = generate_l1_sweep_task(
                session,
                _make_l1_request(
                    repo_root=str(repo_root),
                    sweep_path=sweep_path,
                    config_paths=[config_path],
                    platform="nangate45",
                    out_root="runs/designs/npu_blocks",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="architecture_block",
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            assert work_item.command_manifest[0]["run"] == (
                "export PATH=/oss-cad-suite/bin:$PATH && "
                "python3 npu/rtlgen/gen_attention_score32_exact_partial_pair_merge_folded.py "
                "--config "
                "runs/designs/npu_blocks/attention_score32_exact_partial_pair_merge_sharedscale_factored_mersenne_l1/config.json "
                "--out "
                "runs/designs/npu_blocks/attention_score32_exact_partial_pair_merge_sharedscale_factored_mersenne_l1/verilog"
            )
            assert (
                "--sweep runs/campaigns/npu/attention_score32_exact_partial_pair_merge_sharedscale_mersenne_v1/sweeps/"
                "nangate45_attention_score32_exact_partial_pair_merge_sharedscale_factored_mersenne_l1.json"
                in work_item.command_manifest[1]["run"]
            )
            assert "--top attention_score32_exact_partial_pair_merge_sharedscale_factored_mersenne_l1" in (
                work_item.command_manifest[2]["run"]
            )
            assert work_item.expected_outputs == [
                "runs/designs/npu_blocks/attention_score32_exact_partial_pair_merge_sharedscale_factored_mersenne_l1/metrics.csv",
                "runs/designs/npu_blocks/attention_score32_exact_partial_pair_merge_sharedscale_factored_mersenne_l1/"
                "timing_debug_report.md",
            ]


def _normalize_requested_item(item: dict[str, object]) -> dict[str, object]:
    ignored = {
        "status",
        "notes",
        "merged_pr_number",
        "merge_commit",
        "merged_utc",
    }
    return {key: value for key, value in item.items() if key not in ignored}


def test_exact_partial_pair_merge_sharedscale_proposal_and_evaluation_requests_match() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    proposal_dir = (
        repo_root
        / "docs"
        / "proposals"
        / "prop_l1_decoder_attention_score32_exact_partial_pair_merge_sharedscale_ppa_v1"
    )
    proposal = json.loads((proposal_dir / "proposal.json").read_text(encoding="utf-8"))
    evaluation_requests = json.loads((proposal_dir / "evaluation_requests.json").read_text(encoding="utf-8"))

    assert evaluation_requests["proposal_id"] == proposal["proposal_id"]
    assert [_normalize_requested_item(item) for item in evaluation_requests["requested_items"]] == [
        _normalize_requested_item(item) for item in proposal["required_evaluations"]
    ]
    assert evaluation_requests["requested_items"][0]["priority"] == 95
    assert evaluation_requests["requested_items"][0]["comparison_role"] == (
        "exact_partial_pair_merge_sharedscale_anchor"
    )


def test_exact_partial_pair_merge_sharedscale_mersenne_proposal_and_evaluation_requests_match() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    proposal_dir = (
        repo_root
        / "docs"
        / "proposals"
        / "prop_l1_decoder_attention_score32_exact_partial_pair_merge_sharedscale_mersenne_ppa_v1"
    )
    proposal = json.loads((proposal_dir / "proposal.json").read_text(encoding="utf-8"))
    evaluation_requests = json.loads((proposal_dir / "evaluation_requests.json").read_text(encoding="utf-8"))

    assert evaluation_requests["proposal_id"] == proposal["proposal_id"]
    assert [_normalize_requested_item(item) for item in evaluation_requests["requested_items"]] == [
        _normalize_requested_item(item) for item in proposal["required_evaluations"]
    ]
    assert evaluation_requests["requested_items"][0]["priority"] == 96
    assert evaluation_requests["requested_items"][0]["comparison_role"] == (
        "exact_partial_pair_merge_sharedscale_mersenne_vs_generic"
    )


def test_generate_l1_sweep_task_supports_attention_score32_exact_banked_finalized_tree_configs() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        config_path, sweep_path = _write_example_attention_score32_exact_banked_finalized_tree_repo(repo_root)
        proposal_dir = (
            repo_root
            / "docs"
            / "proposals"
            / "prop_l1_decoder_attention_score32_exact_banked_finalized_tree_c16_bank_ppa_v1"
        )
        proposal_dir.mkdir(parents=True, exist_ok=True)
        item_id = "l1_decoder_attention_score32_exact_banked_finalized_tree_c16_bank_ppa_v1"
        (proposal_dir / "proposal.json").write_text(
            json.dumps(
                {
                    "proposal_id": "prop_l1_decoder_attention_score32_exact_banked_finalized_tree_c16_bank_ppa_v1",
                    "abstraction_layer": "architecture_block",
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (proposal_dir / "evaluation_requests.json").write_text(
            json.dumps(
                {
                    "proposal_id": "prop_l1_decoder_attention_score32_exact_banked_finalized_tree_c16_bank_ppa_v1",
                    "requested_items": [
                        {
                            "item_id": item_id,
                            "task_type": "l1_sweep",
                            "evaluation_mode": "frontier_followup",
                            "abstraction_layer": "architecture_block",
                            "comparison_role": "exact_banked_finalized_tree_c16_bank_anchor",
                            "priority": 94,
                            "expected_result": {
                                "direction": "measure_exact_banked_finalized_tree_c16_bank_cost",
                                "reason": "Use the merged banked wrapper to compare sub-wrap, wrap-free, and power-of-two bank counts.",
                            },
                        }
                    ],
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        source_commit = _init_git_repo(repo_root)
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            result = generate_l1_sweep_task(
                session,
                _make_l1_request(
                    repo_root=str(repo_root),
                    sweep_path=sweep_path,
                    config_paths=[config_path],
                    platform="nangate45",
                    out_root="runs/designs/npu_blocks",
                    item_id=item_id,
                    requested_by="@tester",
                    source_commit=source_commit,
                    proposal_id="prop_l1_decoder_attention_score32_exact_banked_finalized_tree_c16_bank_ppa_v1",
                    proposal_path=str(proposal_dir.relative_to(repo_root)),
                    update_proposal_files=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            assert work_item.priority == 94
            assert [command["name"] for command in work_item.command_manifest] == [
                "generate_attention_score32_exact_banked_finalized_tree_rtl",
                "check_attention_score32_exact_banked_finalized_tree_guard",
                "run_block_sweep",
                "extract_attention_score32_exact_banked_finalized_tree_timing_paths",
                "build_runs_index",
                "validate",
            ]
            assert work_item.command_manifest[0]["run"] == (
                "export PATH=/oss-cad-suite/bin:$PATH && "
                "python3 npu/rtlgen/gen_attention_score32_exact_banked_finalized_tree.py "
                "--config runs/designs/npu_blocks/attention_score32_exact_banked_finalized_tree_smoke_c16_r2_l8_b16/config.json "
                "--out runs/designs/npu_blocks/attention_score32_exact_banked_finalized_tree_smoke_c16_r2_l8_b16/verilog"
            )
            assert work_item.command_manifest[1]["run"] == (
                "python3 npu/eval/check_attention_score32_exact_banked_finalized_tree_guard.py "
                "--design-dir runs/designs/npu_blocks/attention_score32_exact_banked_finalized_tree_smoke_c16_r2_l8_b16 "
                "--config runs/designs/npu_blocks/attention_score32_exact_banked_finalized_tree_smoke_c16_r2_l8_b16/config.json "
                "--sweep runs/campaigns/npu/attention_score32_exact_banked_finalized_tree_v1/sweeps/"
                "nangate45_attention_score32_exact_banked_finalized_tree_c16_bank_firstpass.json"
            )
            assert "--top attention_score32_exact_banked_finalized_tree_smoke_c16_r2_l8_b16" in work_item.command_manifest[2]["run"]
            assert work_item.command_manifest[3]["run"] == (
                "python3 npu/eval/extract_openroad_timing_summary.py "
                "--design-dir runs/designs/npu_blocks/attention_score32_exact_banked_finalized_tree_smoke_c16_r2_l8_b16 "
                "--out runs/designs/npu_blocks/attention_score32_exact_banked_finalized_tree_smoke_c16_r2_l8_b16/timing_debug_report.md "
                "--max-paths 8"
            )
            assert work_item.expected_outputs == [
                "runs/designs/npu_blocks/attention_score32_exact_banked_finalized_tree_smoke_c16_r2_l8_b16/metrics.csv",
                "runs/designs/npu_blocks/attention_score32_exact_banked_finalized_tree_smoke_c16_r2_l8_b16/timing_debug_report.md",
            ]
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "architecture_block"
            }


def test_generate_l1_sweep_task_supports_attention_hbm_replay_controller_configs() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        config_path, sweep_path = _write_example_attention_hbm_replay_controller_repo(repo_root)
        source_commit = _init_git_repo(repo_root)
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            result = generate_l1_sweep_task(
                session,
                _make_l1_request(
                    repo_root=str(repo_root),
                    sweep_path=sweep_path,
                    config_paths=[config_path],
                    platform="nangate45",
                    out_root="runs/designs/npu_blocks",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="decoder_attention_hbm_replay_controller",
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            assert result.status == "applied"
            assert [command["name"] for command in work_item.command_manifest] == [
                "generate_attention_hbm_replay_controller_rtl",
                "check_attention_hbm_replay_controller_guard",
                "run_block_sweep",
                "extract_attention_hbm_replay_controller_timing_paths",
                "build_runs_index",
                "validate",
            ]
            assert work_item.command_manifest[0]["run"] == (
                "export PATH=/oss-cad-suite/bin:$PATH && "
                "python3 npu/rtlgen/gen_attention_hbm_replay_controller.py "
                "--config runs/designs/npu_blocks/attention_hbm_replay_controller_smoke/config.json "
                "--out runs/designs/npu_blocks/attention_hbm_replay_controller_smoke/verilog"
            )
            assert work_item.command_manifest[1]["run"] == (
                "python3 npu/eval/check_attention_hbm_replay_controller_guard.py "
                "--design-dir runs/designs/npu_blocks/attention_hbm_replay_controller_smoke"
            )
            assert "--top attention_hbm_replay_controller_smoke" in work_item.command_manifest[2]["run"]
            assert work_item.command_manifest[3]["run"] == (
                "python3 npu/eval/extract_openroad_timing_summary.py "
                "--design-dir runs/designs/npu_blocks/attention_hbm_replay_controller_smoke "
                "--out runs/designs/npu_blocks/attention_hbm_replay_controller_smoke/timing_debug_report.md "
                "--max-paths 8"
            )
            assert work_item.expected_outputs == [
                "runs/designs/npu_blocks/attention_hbm_replay_controller_smoke/metrics.csv",
                "runs/designs/npu_blocks/attention_hbm_replay_controller_smoke/timing_debug_report.md",
            ]
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_attention_hbm_replay_controller"
            }
            assert "allow non-ok metrics" in work_item.acceptance_rules[0]
            assert "flow_failed" in work_item.acceptance_rules[0]


def test_generate_l1_sweep_task_supports_multi_attention_hbm_replay_controller_configs() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        config_path, sweep_path = _write_example_attention_hbm_replay_controller_repo(repo_root)
        second_config_path = _write_second_attention_hbm_replay_controller_repo(repo_root)
        source_commit = _init_git_repo(repo_root)
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            result = generate_l1_sweep_task(
                session,
                _make_l1_request(
                    repo_root=str(repo_root),
                    sweep_path=sweep_path,
                    config_paths=[config_path, second_config_path],
                    platform="nangate45",
                    out_root="runs/designs/npu_blocks",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="decoder_attention_hbm_replay_controller",
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            assert [command["name"] for command in work_item.command_manifest] == [
                "generate_attention_hbm_replay_controller_rtl_attention_hbm_replay_controller_smoke",
                "check_attention_hbm_replay_controller_guard_attention_hbm_replay_controller_smoke",
                "run_block_sweep_attention_hbm_replay_controller_smoke",
                "extract_attention_hbm_replay_controller_timing_paths_attention_hbm_replay_controller_smoke",
                "generate_attention_hbm_replay_controller_rtl_attention_hbm_replay_controller_c16_q32",
                "check_attention_hbm_replay_controller_guard_attention_hbm_replay_controller_c16_q32",
                "run_block_sweep_attention_hbm_replay_controller_c16_q32",
                "extract_attention_hbm_replay_controller_timing_paths_attention_hbm_replay_controller_c16_q32",
                "build_runs_index",
                "validate",
            ]
            assert "attention_hbm_replay_controller_smoke/config.json" in work_item.command_manifest[0]["run"]
            assert "attention_hbm_replay_controller_c16_q32/config.json" in work_item.command_manifest[4]["run"]
            assert work_item.expected_outputs == [
                "runs/designs/npu_blocks/attention_hbm_replay_controller_smoke/metrics.csv",
                "runs/designs/npu_blocks/attention_hbm_replay_controller_smoke/timing_debug_report.md",
                "runs/designs/npu_blocks/attention_hbm_replay_controller_c16_q32/metrics.csv",
                "runs/designs/npu_blocks/attention_hbm_replay_controller_c16_q32/timing_debug_report.md",
            ]
            assert "allow non-ok metrics" in work_item.acceptance_rules[0]
            assert "flow_failed" in work_item.acceptance_rules[0]


def test_generate_l1_sweep_task_supports_llama7b_rmsnorm_phase3_block_config() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        config_path, sweep_path = _write_example_llama7b_rmsnorm_phase3_physical_repo(repo_root)
        source_commit = _init_git_repo(repo_root)
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
                    source_commit=source_commit,
                    abstraction_layer="llama7b_rmsnorm_phase3",
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            assert result.status == "applied"
            assert [command["name"] for command in work_item.command_manifest] == [
                "generate_llama7b_rmsnorm_rtl",
                "check_llama7b_rmsnorm_phase3_physical_guard",
                "lint_llama7b_rmsnorm_phase3_rtl",
                "run_block_sweep",
                "extract_llama7b_rmsnorm_phase3_timing_paths",
                "build_runs_index",
                "validate",
            ]
            assert work_item.command_manifest[0]["run"] == (
                "export PATH=/oss-cad-suite/bin:$PATH && "
                "python3 npu/rtlgen/gen_llama7b_rmsnorm.py "
                "--config runs/designs/npu_blocks/llama7b_rmsnorm_phase3_bounded_l16_ng45/config.json "
                "--out runs/designs/npu_blocks/llama7b_rmsnorm_phase3_bounded_l16_ng45/verilog"
            )
            assert work_item.command_manifest[1]["run"] == (
                "python3 npu/eval/check_llama7b_rmsnorm_phase3_physical_guard.py "
                "--design-dir runs/designs/npu_blocks/llama7b_rmsnorm_phase3_bounded_l16_ng45"
            )
            assert work_item.command_manifest[2]["run"] == (
                "export PATH=/oss-cad-suite/bin:$PATH && "
                "verilator --lint-only -Wall -Wno-fatal "
                "runs/designs/npu_blocks/llama7b_rmsnorm_phase3_bounded_l16_ng45/verilog/top.v"
            )
            assert "--top llama7b_rmsnorm_phase3_bounded_l16_ng45" in work_item.command_manifest[3]["run"]
            assert work_item.command_manifest[4]["run"] == (
                "python3 npu/eval/extract_openroad_timing_summary.py "
                "--design-dir runs/designs/npu_blocks/llama7b_rmsnorm_phase3_bounded_l16_ng45 "
                "--out runs/designs/npu_blocks/llama7b_rmsnorm_phase3_bounded_l16_ng45/timing_debug_report.md "
                "--max-paths 8"
            )
            assert work_item.expected_outputs == [
                "runs/designs/npu_blocks/llama7b_rmsnorm_phase3_bounded_l16_ng45/metrics.csv",
                "runs/designs/npu_blocks/llama7b_rmsnorm_phase3_bounded_l16_ng45/timing_debug_report.md",
            ]
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "llama7b_rmsnorm_phase3"
            }


def test_generate_l1_sweep_task_supports_attention_schedule_wrapper_configs() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        config_path, sweep_path = _write_example_attention_schedule_wrapper_repo(repo_root)
        source_commit = _init_git_repo(repo_root)
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            result = generate_l1_sweep_task(
                session,
                _make_l1_request(
                    repo_root=str(repo_root),
                    sweep_path=sweep_path,
                    config_paths=[config_path],
                    platform="nangate45",
                    out_root="runs/designs/npu_blocks",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="decoder_attention_dual_stream_schedule_wrapper",
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            assert result.status == "applied"
            assert [command["name"] for command in work_item.command_manifest] == [
                "generate_attention_dual_stream_schedule_wrapper_rtl",
                "check_attention_dual_stream_schedule_wrapper_guard",
                "run_block_sweep",
                "extract_attention_dual_stream_schedule_wrapper_timing_paths",
                "build_runs_index",
                "validate",
            ]
            assert work_item.command_manifest[0]["run"] == (
                "export PATH=/oss-cad-suite/bin:$PATH && "
                "python3 npu/rtlgen/gen_attention_dual_stream_schedule_wrapper.py "
                "--config runs/designs/npu_blocks/attention_dual_stream_schedule_wrapper_smoke_c2/config.json "
                "--out runs/designs/npu_blocks/attention_dual_stream_schedule_wrapper_smoke_c2/verilog"
            )
            assert work_item.command_manifest[1]["run"] == (
                "python3 npu/eval/check_attention_dual_stream_schedule_wrapper_guard.py "
                "--design-dir runs/designs/npu_blocks/attention_dual_stream_schedule_wrapper_smoke_c2"
            )
            assert "--top attention_dual_stream_schedule_wrapper_smoke_c2" in work_item.command_manifest[2]["run"]
            assert work_item.command_manifest[3]["run"] == (
                "python3 npu/eval/extract_openroad_timing_summary.py "
                "--design-dir runs/designs/npu_blocks/attention_dual_stream_schedule_wrapper_smoke_c2 "
                "--out runs/designs/npu_blocks/attention_dual_stream_schedule_wrapper_smoke_c2/timing_debug_report.md "
                "--max-paths 8"
            )
            assert work_item.expected_outputs == [
                "runs/designs/npu_blocks/attention_dual_stream_schedule_wrapper_smoke_c2/metrics.csv",
                "runs/designs/npu_blocks/attention_dual_stream_schedule_wrapper_smoke_c2/timing_debug_report.md",
            ]
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_attention_dual_stream_schedule_wrapper"
            }


def test_generate_l1_sweep_task_supports_attention_separated_cluster_configs() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        config_path, sweep_path = _write_example_attention_separated_cluster_repo(repo_root)
        source_commit = _init_git_repo(repo_root)
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            result = generate_l1_sweep_task(
                session,
                _make_l1_request(
                    repo_root=str(repo_root),
                    sweep_path=sweep_path,
                    config_paths=[config_path],
                    platform="nangate45",
                    out_root="runs/designs/npu_blocks",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="decoder_attention_separated_cluster",
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            assert result.status == "applied"
            assert [command["name"] for command in work_item.command_manifest] == [
                "generate_attention_separated_cluster_rtl",
                "check_attention_separated_cluster_guard",
                "run_block_sweep",
                "extract_attention_separated_cluster_timing_paths",
                "build_runs_index",
                "validate",
            ]
            assert "gen_attention_separated_cluster.py" in work_item.command_manifest[0]["run"]
            assert "check_attention_separated_cluster_guard.py" in work_item.command_manifest[1]["run"]
            assert "--top attention_separated_cluster_p4_c1" in work_item.command_manifest[2]["run"]
            assert work_item.expected_outputs == [
                "runs/designs/npu_blocks/attention_separated_cluster_p4_c1/metrics.csv",
                "runs/designs/npu_blocks/attention_separated_cluster_p4_c1/timing_debug_report.md",
            ]


def test_generate_l1_sweep_task_supports_attention_two_pass_stream_configs() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        config_path, sweep_path = _write_example_attention_two_pass_stream_repo(repo_root)
        source_commit = _init_git_repo(repo_root)
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            result = generate_l1_sweep_task(
                session,
                _make_l1_request(
                    repo_root=str(repo_root),
                    sweep_path=sweep_path,
                    config_paths=[config_path],
                    platform="nangate45",
                    out_root="runs/designs/npu_blocks",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="decoder_attention_two_pass_stream",
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            assert [command["name"] for command in work_item.command_manifest] == [
                "generate_attention_two_pass_stream_rtl",
                "check_attention_two_pass_stream_guard",
                "run_block_sweep",
                "extract_attention_two_pass_stream_timing_paths",
                "build_runs_index",
                "validate",
            ]
            assert "gen_attention_two_pass_stream.py" in work_item.command_manifest[0]["run"]
            assert "check_attention_two_pass_stream_guard.py" in work_item.command_manifest[1]["run"]
            assert "--top attention_two_pass_stream_d2" in work_item.command_manifest[2]["run"]
            assert work_item.expected_outputs == [
                "runs/designs/npu_blocks/attention_two_pass_stream_d2/metrics.csv",
                "runs/designs/npu_blocks/attention_two_pass_stream_d2/timing_debug_report.md",
            ]


def test_generate_l1_sweep_task_supports_attention_score_bank_proxy_configs() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        config_path, sweep_path = _write_example_attention_score_bank_proxy_repo(repo_root)
        source_commit = _init_git_repo(repo_root)
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            result = generate_l1_sweep_task(
                session,
                _make_l1_request(
                    repo_root=str(repo_root),
                    sweep_path=sweep_path,
                    config_paths=[config_path],
                    platform="nangate45",
                    out_root="runs/designs/npu_blocks",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="decoder_attention_score_bank_proxy",
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            assert [command["name"] for command in work_item.command_manifest] == [
                "generate_attention_score_bank_proxy_rtl",
                "run_block_sweep",
                "extract_attention_score_bank_proxy_timing_paths",
                "build_runs_index",
                "validate",
            ]
            assert "gen_attention_score_bank_proxy.py" in work_item.command_manifest[0]["run"]
            assert "--top attention_score_bank_proxy_16kx256" in work_item.command_manifest[1]["run"]
            assert "--macro_manifest runs/designs/npu_blocks/attention_score_bank_proxy_16kx256/macro_manifest.json" in work_item.command_manifest[1]["run"]
            assert work_item.expected_outputs == [
                "runs/designs/npu_blocks/attention_score_bank_proxy_16kx256/metrics.csv",
                "runs/designs/npu_blocks/attention_score_bank_proxy_16kx256/timing_debug_report.md",
            ]


def test_generate_l1_sweep_task_supports_attention_decode_score_local_cluster_configs() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        config_path, sweep_path = _write_example_attention_decode_score_local_cluster_repo(repo_root)
        source_commit = _init_git_repo(repo_root)
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            result = generate_l1_sweep_task(
                session,
                _make_l1_request(
                    repo_root=str(repo_root),
                    sweep_path=sweep_path,
                    config_paths=[config_path],
                    platform="nangate45",
                    out_root="runs/designs/npu_blocks",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="decoder_attention_decode_score_local_cluster",
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            assert [command["name"] for command in work_item.command_manifest] == [
                "generate_attention_decode_score_local_cluster_rtl",
                "check_attention_decode_score_local_cluster_guard",
                "run_block_sweep",
                "extract_attention_decode_score_local_cluster_timing_paths",
                "build_runs_index",
                "validate",
            ]
            assert "gen_attention_decode_score_local_cluster.py" in work_item.command_manifest[0]["run"]
            assert "check_attention_decode_score_local_cluster_guard.py" in work_item.command_manifest[1]["run"]
            assert "--top attention_decode_score_local_cluster_int8_m1x8_iterdiv" in work_item.command_manifest[2]["run"]
            assert (
                "--macro_manifest runs/designs/npu_blocks/"
                "attention_decode_score_local_cluster_int8_m1x8_iterdiv/macro_manifest.json"
                in work_item.command_manifest[2]["run"]
            )
            assert work_item.expected_outputs == [
                "runs/designs/npu_blocks/attention_decode_score_local_cluster_int8_m1x8_iterdiv/metrics.csv",
                "runs/designs/npu_blocks/attention_decode_score_local_cluster_int8_m1x8_iterdiv/timing_debug_report.md",
            ]


def test_generate_l1_sweep_task_supports_attention_decode_score_multivalue_cluster_configs() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        config_path, sweep_path = _write_example_attention_decode_score_multivalue_cluster_repo(repo_root)
        source_commit = _init_git_repo(repo_root)
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            result = generate_l1_sweep_task(
                session,
                _make_l1_request(
                    repo_root=str(repo_root),
                    sweep_path=sweep_path,
                    config_paths=[config_path],
                    platform="nangate45",
                    out_root="runs/designs/npu_blocks",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="decoder_attention_decode_score_multivalue_cluster",
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            assert [command["name"] for command in work_item.command_manifest] == [
                "generate_attention_decode_score_multivalue_cluster_rtl",
                "check_attention_decode_score_multivalue_cluster_guard",
                "run_block_sweep",
                "extract_attention_decode_score_multivalue_cluster_timing_paths",
                "build_runs_index",
                "validate",
            ]
            assert "gen_attention_decode_score_multivalue_cluster.py" in work_item.command_manifest[0]["run"]
            assert "check_attention_decode_score_multivalue_cluster_guard.py" in work_item.command_manifest[1]["run"]
            assert (
                "--config runs/designs/npu_blocks/"
                "attention_decode_score_multivalue_cluster_int8_m1x8_iterdiv/config.json"
                in work_item.command_manifest[1]["run"]
            )
            assert "--top attention_decode_score_multivalue_cluster_int8_m1x8_iterdiv" in work_item.command_manifest[2]["run"]
            assert (
                "--macro_manifest runs/designs/npu_blocks/"
                "attention_decode_score_multivalue_cluster_int8_m1x8_iterdiv/macro_manifest.json"
                in work_item.command_manifest[2]["run"]
            )
            assert work_item.expected_outputs == [
                "runs/designs/npu_blocks/attention_decode_score_multivalue_cluster_int8_m1x8_iterdiv/metrics.csv",
                "runs/designs/npu_blocks/attention_decode_score_multivalue_cluster_int8_m1x8_iterdiv/timing_debug_report.md",
            ]


def test_generate_l1_sweep_task_supports_attention_decode_score_multivalue_service_configs() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        config_path, sweep_path = _write_example_attention_decode_score_multivalue_service_repo(repo_root)
        source_commit = _init_git_repo(repo_root)
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            result = generate_l1_sweep_task(
                session,
                _make_l1_request(
                    repo_root=str(repo_root),
                    sweep_path=sweep_path,
                    config_paths=[config_path],
                    platform="nangate45",
                    out_root="runs/designs/npu_blocks",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="decoder_attention_decode_score_multivalue_service",
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            assert [command["name"] for command in work_item.command_manifest] == [
                "generate_attention_decode_score_multivalue_service_rtl",
                "check_attention_decode_score_multivalue_service_guard",
                "run_block_sweep",
                "check_attention_decode_score_multivalue_service_physical",
                "extract_attention_decode_score_multivalue_service_timing_paths",
                "build_runs_index",
                "validate",
            ]
            assert "gen_attention_decode_score_multivalue_service.py" in work_item.command_manifest[0]["run"]
            assert "check_attention_decode_score_multivalue_service_guard.py" in work_item.command_manifest[1]["run"]
            assert (
                "--config runs/designs/npu_blocks/"
                "attention_decode_score_multivalue_service_c2_p128_b4_q4_rl2_rr/config.json"
                in work_item.command_manifest[1]["run"]
            )
            assert "--top attention_decode_score_multivalue_service_c2_p128_b4_q4_rl2_rr" in work_item.command_manifest[2]["run"]
            assert (
                "--macro_manifest runs/designs/npu_blocks/"
                "attention_decode_score_multivalue_service_c2_p128_b4_q4_rl2_rr/macro_manifest.json"
                in work_item.command_manifest[2]["run"]
            )
            assert "check_attention_decode_score_multivalue_service_physical.py" in work_item.command_manifest[3]["run"]
            assert work_item.expected_outputs == [
                "runs/designs/npu_blocks/attention_decode_score_multivalue_service_c2_p128_b4_q4_rl2_rr/metrics.csv",
                "runs/designs/npu_blocks/attention_decode_score_multivalue_service_c2_p128_b4_q4_rl2_rr/timing_debug_report.md",
            ]


def test_multivalue_service_pnr_proposal_keeps_c2_gated_on_c1_dependency() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    proposal_dir = (
        repo_root
        / "docs"
        / "proposals"
        / "prop_l1_decoder_attention_decode_score_multivalue_service_pnr_v1"
    )
    proposal = json.loads((proposal_dir / "proposal.json").read_text(encoding="utf-8"))
    evaluation_requests = json.loads((proposal_dir / "evaluation_requests.json").read_text(encoding="utf-8"))

    c1_item_id = "l1_decoder_attention_decode_score_multivalue_service_c1_p128_b4_q4_rl2_rr_pnr_v1"
    service_dep_id = "l2_decoder_attention_decode_score_multivalue_integrated_service_llama7b_v1_r1"
    proposal_by_id = {entry["item_id"]: entry for entry in proposal["required_evaluations"]}
    request_by_id = {entry["item_id"]: entry for entry in evaluation_requests["requested_items"]}

    c2_proposal = proposal_by_id["l1_decoder_attention_decode_score_multivalue_service_c2_p128_b4_q4_rl2_rr_pnr_v1"]
    c2_request = request_by_id["l1_decoder_attention_decode_score_multivalue_service_c2_p128_b4_q4_rl2_rr_pnr_v1"]

    assert c2_proposal["status"] == "conditional_follow_on"
    assert c2_request["status"] == "conditional_follow_on"
    assert c2_proposal["depends_on_item_ids"] == [service_dep_id, c1_item_id]
    assert c2_request["depends_on_item_ids"] == [service_dep_id, c1_item_id]
    assert c1_item_id in (proposal_dir / "design_brief.md").read_text(encoding="utf-8")


def test_multivalue_service_pnr_proposal_adds_explicit_c1_route_recovery_retry() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    proposal_dir = (
        repo_root
        / "docs"
        / "proposals"
        / "prop_l1_decoder_attention_decode_score_multivalue_service_pnr_v1"
    )
    proposal = json.loads((proposal_dir / "proposal.json").read_text(encoding="utf-8"))
    evaluation_requests = json.loads((proposal_dir / "evaluation_requests.json").read_text(encoding="utf-8"))
    design_brief = (proposal_dir / "design_brief.md").read_text(encoding="utf-8")

    base_item_id = "l1_decoder_attention_decode_score_multivalue_service_c1_p128_b4_q4_rl2_rr_pnr_v1"
    retry_item_id = "l1_decoder_attention_decode_score_multivalue_service_c1_p128_b4_q4_rl2_rr_pnr_v1_r4"
    retry_sweep = (
        "runs/campaigns/npu/decode_score_multivalue_service_v1/sweeps/"
        "nangate45_decode_score_multivalue_service_c1_p128_b4_q4_rl2_rr_3600.json"
    )
    base_sweep = (
        "runs/campaigns/npu/decode_score_multivalue_service_v1/sweeps/"
        "nangate45_decode_score_multivalue_service_c1_p128_b4_q4_rl2_rr_3000.json"
    )

    proposal_by_id = {entry["item_id"]: entry for entry in proposal["required_evaluations"]}
    request_by_id = {entry["item_id"]: entry for entry in evaluation_requests["requested_items"]}
    base_proposal = proposal_by_id[base_item_id]
    retry_proposal = proposal_by_id[retry_item_id]
    base_request = request_by_id[base_item_id]
    retry_request = request_by_id[retry_item_id]

    assert base_proposal["sweep_path"] == base_sweep
    assert base_request["sweep_path"] == base_sweep
    assert retry_proposal["sweep_path"] == retry_sweep
    assert retry_request["sweep_path"] == retry_sweep
    assert retry_proposal["prior_item_ids"] == [base_item_id + "_r3"]
    assert retry_request["prior_item_ids"] == [base_item_id + "_r3"]
    assert "does not claim a new area frontier" in retry_proposal["expected_result"]["reason"]
    assert "does not claim a new area frontier" in retry_request["expected_result"]["reason"]
    assert "only eligible if r3 fails to produce acceptable routed evidence" in retry_proposal["expected_result"]["reason"]
    assert "only eligible if r3 fails to produce acceptable routed evidence" in retry_request["expected_result"]["reason"]
    assert "route_recovery_sensitivity" in retry_proposal["comparison_role"]
    assert retry_proposal["status"] == "conditional_follow_on"
    assert retry_request["status"] == "conditional_follow_on"
    assert "3.6 mm" in design_brief
    assert "3.5 mm" in design_brief
    assert "not an area-frontier replacement" in design_brief
    assert "r2" in design_brief
    assert "r3" in design_brief
    assert "r4" in design_brief
    assert "acceptable routed evidence" in design_brief


def test_exact_root_finalizer_lane_ppa_proposal_is_pending_merge_with_all_lane_configs() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    proposal_dir = (
        repo_root
        / "docs"
        / "proposals"
        / "prop_l1_decoder_attention_score32_exact_root_finalizer_lane_ppa_v1"
    )
    proposal = json.loads((proposal_dir / "proposal.json").read_text(encoding="utf-8"))
    evaluation_requests = json.loads((proposal_dir / "evaluation_requests.json").read_text(encoding="utf-8"))

    item_id = "l1_decoder_attention_score32_exact_root_finalizer_lane_ppa_v1"
    expected_configs = [
        "runs/designs/npu_blocks/attention_score32_exact_root_finalizer_l1/config.json",
        "runs/designs/npu_blocks/attention_score32_exact_root_finalizer_l2/config.json",
        "runs/designs/npu_blocks/attention_score32_exact_root_finalizer_l4/config.json",
        "runs/designs/npu_blocks/attention_score32_exact_root_finalizer_l8/config.json",
    ]
    expected_sweep = (
        "runs/campaigns/npu/attention_score32_exact_root_finalizer_v1/sweeps/"
        "nangate45_attention_score32_exact_root_finalizer_lane_firstpass.json"
    )
    proposal_entry = {entry["item_id"]: entry for entry in proposal["required_evaluations"]}[item_id]
    request_entry = {entry["item_id"]: entry for entry in evaluation_requests["requested_items"]}[item_id]

    assert proposal["abstraction_layer"] == "architecture_block"
    assert proposal_entry["status"] == "pending_implementation_merge"
    assert request_entry["status"] == "pending_implementation_merge"
    assert proposal_entry["configs"] == expected_configs
    assert request_entry["configs"] == expected_configs
    assert proposal_entry["sweep_path"] == expected_sweep
    assert request_entry["sweep_path"] == expected_sweep
    assert "isolated finalizer baseline" in proposal_entry["notes"]


def test_exact_partial_tree_cluster_ppa_proposal_is_pending_merge_with_all_cluster_configs() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    proposal_dir = (
        repo_root
        / "docs"
        / "proposals"
        / "prop_l1_decoder_attention_score32_exact_partial_tree_cluster_ppa_v1"
    )
    proposal = json.loads((proposal_dir / "proposal.json").read_text(encoding="utf-8"))
    evaluation_requests = json.loads((proposal_dir / "evaluation_requests.json").read_text(encoding="utf-8"))

    item_id = "l1_decoder_attention_score32_exact_partial_tree_cluster_ppa_v1"
    expected_configs = [
        "runs/designs/npu_blocks/attention_score32_exact_partial_tree_c2_r2/config.json",
        "runs/designs/npu_blocks/attention_score32_exact_partial_tree_c4_r2/config.json",
        "runs/designs/npu_blocks/attention_score32_exact_partial_tree_c8_r2/config.json",
        "runs/designs/npu_blocks/attention_score32_exact_partial_tree_c16_r2/config.json",
    ]
    expected_sweep = (
        "runs/campaigns/npu/attention_score32_exact_partial_tree_v1/sweeps/"
        "nangate45_attention_score32_exact_partial_tree_cluster_firstpass.json"
    )
    proposal_entry = {entry["item_id"]: entry for entry in proposal["required_evaluations"]}[item_id]
    request_entry = {entry["item_id"]: entry for entry in evaluation_requests["requested_items"]}[item_id]

    assert proposal["abstraction_layer"] == "architecture_block"
    assert proposal_entry["status"] == "pending_implementation_merge"
    assert request_entry["status"] == "pending_implementation_merge"
    assert proposal_entry["configs"] == expected_configs
    assert request_entry["configs"] == expected_configs
    assert proposal_entry["sweep_path"] == expected_sweep
    assert request_entry["sweep_path"] == expected_sweep
    assert "Boundary evidence is valid here" in proposal_entry["notes"]


def test_exact_partial_tree_factored_cluster_ppa_proposal_is_pending_merge_with_all_cluster_configs() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    proposal_dir = (
        repo_root
        / "docs"
        / "proposals"
        / "prop_l1_decoder_attention_score32_exact_partial_tree_factored_cluster_ppa_v1"
    )
    proposal = json.loads((proposal_dir / "proposal.json").read_text(encoding="utf-8"))
    evaluation_requests = json.loads((proposal_dir / "evaluation_requests.json").read_text(encoding="utf-8"))

    item_id = "l1_decoder_attention_score32_exact_partial_tree_factored_cluster_ppa_v1"
    expected_configs = [
        "runs/designs/npu_blocks/attention_score32_exact_partial_tree_factored_c2_r2/config.json",
        "runs/designs/npu_blocks/attention_score32_exact_partial_tree_factored_c4_r2/config.json",
        "runs/designs/npu_blocks/attention_score32_exact_partial_tree_factored_c8_r2/config.json",
        "runs/designs/npu_blocks/attention_score32_exact_partial_tree_factored_c16_r2/config.json",
    ]
    expected_sweep = (
        "runs/campaigns/npu/attention_score32_exact_partial_tree_factored_v2/sweeps/"
        "nangate45_attention_score32_exact_partial_tree_factored_cluster_retry_r2.json"
    )
    proposal_entry = {entry["item_id"]: entry for entry in proposal["required_evaluations"]}[item_id]
    request_entry = {entry["item_id"]: entry for entry in evaluation_requests["requested_items"]}[item_id]

    assert proposal["abstraction_layer"] == "architecture_block"
    assert proposal_entry["status"] == "pending_implementation_merge"
    assert request_entry["status"] == "pending_implementation_merge"
    assert proposal_entry["configs"] == expected_configs
    assert request_entry["configs"] == expected_configs
    assert proposal_entry["sweep_path"] == expected_sweep
    assert request_entry["sweep_path"] == expected_sweep
    assert "Revision-safe retry on new config/output identities only" in proposal_entry["notes"]


def test_exact_partial_tree_folded_mersenne_cluster_ppa_proposal_is_pending_merge_with_all_cluster_configs() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    proposal_dir = (
        repo_root
        / "docs"
        / "proposals"
        / "prop_l1_decoder_attention_score32_exact_partial_tree_folded_mersenne_cluster_ppa_v1"
    )
    proposal = json.loads((proposal_dir / "proposal.json").read_text(encoding="utf-8"))
    evaluation_requests = json.loads((proposal_dir / "evaluation_requests.json").read_text(encoding="utf-8"))

    item_id = "l1_decoder_attention_score32_exact_partial_tree_folded_mersenne_cluster_ppa_v1"
    expected_configs = [
        "runs/designs/npu_blocks/attention_score32_exact_partial_tree_folded_mersenne_c2_r2/config.json",
        "runs/designs/npu_blocks/attention_score32_exact_partial_tree_folded_mersenne_c4_r2/config.json",
        "runs/designs/npu_blocks/attention_score32_exact_partial_tree_folded_mersenne_c8_r2/config.json",
        "runs/designs/npu_blocks/attention_score32_exact_partial_tree_folded_mersenne_c16_r2/config.json",
    ]
    expected_sweep = (
        "runs/campaigns/npu/attention_score32_exact_partial_tree_folded_mersenne_v1/sweeps/"
        "nangate45_attention_score32_exact_partial_tree_folded_mersenne_cluster_v1.json"
    )
    proposal_entry = {entry["item_id"]: entry for entry in proposal["required_evaluations"]}[item_id]
    request_entry = {entry["item_id"]: entry for entry in evaluation_requests["requested_items"]}[item_id]

    assert proposal["abstraction_layer"] == "architecture_block"
    assert proposal_entry["status"] == "pending_implementation_merge"
    assert request_entry["status"] == "pending_implementation_merge"
    assert proposal_entry["configs"] == expected_configs
    assert request_entry["configs"] == expected_configs
    assert proposal_entry["sweep_path"] == expected_sweep
    assert request_entry["sweep_path"] == expected_sweep
    assert "direct 328-bit leaf/root pins" in proposal_entry["notes"]


def test_exact_finalized_tree_c16_lane_ppa_proposal_is_pending_merge_with_all_lane_configs() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    proposal_dir = (
        repo_root
        / "docs"
        / "proposals"
        / "prop_l1_decoder_attention_score32_exact_finalized_tree_c16_lane_ppa_v1"
    )
    proposal = json.loads((proposal_dir / "proposal.json").read_text(encoding="utf-8"))
    evaluation_requests = json.loads((proposal_dir / "evaluation_requests.json").read_text(encoding="utf-8"))

    item_id = "l1_decoder_attention_score32_exact_finalized_tree_c16_lane_ppa_v1"
    expected_configs = [
        "runs/designs/npu_blocks/attention_score32_exact_finalized_tree_c16_r2_l1/config.json",
        "runs/designs/npu_blocks/attention_score32_exact_finalized_tree_c16_r2_l2/config.json",
        "runs/designs/npu_blocks/attention_score32_exact_finalized_tree_c16_r2_l4/config.json",
        "runs/designs/npu_blocks/attention_score32_exact_finalized_tree_c16_r2_l8/config.json",
    ]
    expected_sweep = (
        "runs/campaigns/npu/attention_score32_exact_finalized_tree_v1/sweeps/"
        "nangate45_attention_score32_exact_finalized_tree_c16_lane_firstpass.json"
    )
    proposal_entry = {entry["item_id"]: entry for entry in proposal["required_evaluations"]}[item_id]
    request_entry = {entry["item_id"]: entry for entry in evaluation_requests["requested_items"]}[item_id]

    assert proposal["abstraction_layer"] == "architecture_block"
    assert proposal_entry["status"] == "pending_implementation_merge"
    assert request_entry["status"] == "pending_implementation_merge"
    assert proposal_entry["configs"] == expected_configs
    assert request_entry["configs"] == expected_configs
    assert proposal_entry["sweep_path"] == expected_sweep
    assert request_entry["sweep_path"] == expected_sweep
    assert "non-additive PPA" in proposal["hypothesis"]
    assert "full decoder composition remain unclosed" in proposal_entry["notes"]


def test_exact_banked_finalized_tree_c16_bank_ppa_proposal_preserves_v1_infeasibility_and_stages_r2() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    proposal_dir = (
        repo_root
        / "docs"
        / "proposals"
        / "prop_l1_decoder_attention_score32_exact_banked_finalized_tree_c16_bank_ppa_v1"
    )
    proposal = json.loads((proposal_dir / "proposal.json").read_text(encoding="utf-8"))
    evaluation_requests = json.loads((proposal_dir / "evaluation_requests.json").read_text(encoding="utf-8"))

    v1_item_id = "l1_decoder_attention_score32_exact_banked_finalized_tree_c16_bank_ppa_v1"
    r2_item_id = "l1_decoder_attention_score32_exact_banked_finalized_tree_c16_bank_ppa_v1_r2"
    expected_r2_configs = [
        "runs/designs/npu_blocks/attention_score32_exact_banked_finalized_tree_factored_c16_r2_l8_b59/config.json",
        "runs/designs/npu_blocks/attention_score32_exact_banked_finalized_tree_factored_c16_r2_l8_b64/config.json",
    ]
    expected_sweep = (
        "runs/campaigns/npu/attention_score32_exact_banked_finalized_tree_factored_v2/sweeps/"
        "nangate45_attention_score32_exact_banked_finalized_tree_factored_c16_bank_retry_r2.json"
    )
    proposal_entries = {entry["item_id"]: entry for entry in proposal["required_evaluations"]}
    request_entries = {entry["item_id"]: entry for entry in evaluation_requests["requested_items"]}
    proposal_v1 = proposal_entries[v1_item_id]
    proposal_r2 = proposal_entries[r2_item_id]
    request_v1 = request_entries[v1_item_id]
    request_r2 = request_entries[r2_item_id]
    revision_record = {entry["revision"]: entry for entry in proposal["revision_record"]}

    assert proposal["abstraction_layer"] == "architecture_block"
    assert revision_record["v1"]["status"] == "conclusive"
    assert revision_record["r2"]["status"] == "conclusive"
    assert revision_record["r3"]["status"] == "pending"
    assert proposal_v1["status"] == "conclusive"
    assert request_v1["status"] == "conclusive"
    assert proposal_v1["superseded_by_item_id"] == r2_item_id
    assert request_v1["superseded_by_item_id"] == r2_item_id
    assert proposal_r2["priority"] == 94
    assert request_r2["priority"] == 94
    assert proposal_r2["status"] == "conclusive"
    assert request_r2["status"] == "conclusive"
    assert proposal_r2["configs"] == expected_r2_configs
    assert request_r2["configs"] == expected_r2_configs
    assert proposal_r2["sweep_path"] == expected_sweep
    assert request_r2["sweep_path"] == expected_sweep
    assert "flat c16 tree plus ordered banked finalizer composition still overran the evaluator tool envelope" in proposal["hypothesis"]
    assert "12120396 KiB and 12237088 KiB" in proposal_r2["notes"]
    assert "prop_l1_decoder_attention_score32_exact_finalizer_bank_control_ppa_v1" in revision_record["r3"]["notes"]


def test_exact_finalizer_bank_control_ppa_proposal_revisions_preserve_v1_bootstrap_failure_and_stage_r2() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    proposal_dir = (
        repo_root
        / "docs"
        / "proposals"
        / "prop_l1_decoder_attention_score32_exact_finalizer_bank_control_ppa_v1"
    )
    proposal = json.loads((proposal_dir / "proposal.json").read_text(encoding="utf-8"))
    evaluation_requests = json.loads((proposal_dir / "evaluation_requests.json").read_text(encoding="utf-8"))

    v1_item_id = "l1_decoder_attention_score32_exact_finalizer_bank_control_ppa_v1"
    r2_item_id = "l1_decoder_attention_score32_exact_finalizer_bank_control_ppa_v1_r2"
    expected_configs = [
        "runs/designs/npu_blocks/attention_score32_exact_finalizer_bank_control_l8_b1/config.json",
        "runs/designs/npu_blocks/attention_score32_exact_finalizer_bank_control_l8_b4/config.json",
        "runs/designs/npu_blocks/attention_score32_exact_finalizer_bank_control_l8_b8/config.json",
        "runs/designs/npu_blocks/attention_score32_exact_finalizer_bank_control_l8_b16/config.json",
        "runs/designs/npu_blocks/attention_score32_exact_finalizer_bank_control_l8_b32/config.json",
        "runs/designs/npu_blocks/attention_score32_exact_finalizer_bank_control_l8_b59/config.json",
    ]
    expected_sweep = (
        "runs/campaigns/npu/attention_score32_exact_finalizer_bank_control_v1/sweeps/"
        "nangate45_attention_score32_exact_finalizer_bank_control_lane8_firstpass.json"
    )
    proposal_entries = {entry["item_id"]: entry for entry in proposal["required_evaluations"]}
    request_entries = {entry["item_id"]: entry for entry in evaluation_requests["requested_items"]}
    revision_record = {entry["revision"]: entry for entry in proposal["revision_record"]}
    proposal_v1 = proposal_entries[v1_item_id]
    request_v1 = request_entries[v1_item_id]
    proposal_r2 = proposal_entries[r2_item_id]
    request_r2 = request_entries[r2_item_id]

    assert proposal["abstraction_layer"] == "architecture_block"
    assert revision_record["v1"]["status"] == "conclusive"
    assert revision_record["v1"]["reason"] == "cli_import_bootstrap_failure_before_generation"
    assert revision_record["r2"]["status"] == "pending"
    assert proposal["direct_comparison"]["candidate"] == r2_item_id
    assert proposal_v1["status"] == "conclusive"
    assert request_v1["status"] == "conclusive"
    assert proposal_v1["superseded_by_item_id"] == r2_item_id
    assert request_v1["superseded_by_item_id"] == r2_item_id
    assert "ModuleNotFoundError" in proposal_v1["notes"]
    assert proposal_r2["status"] == "pending_implementation_merge"
    assert request_r2["status"] == "pending_implementation_merge"
    assert proposal_r2["configs"] == expected_configs
    assert request_r2["configs"] == expected_configs
    assert proposal_r2["sweep_path"] == expected_sweep
    assert request_r2["sweep_path"] == expected_sweep
    assert "One-density first pass only." in proposal_r2["notes"]


def test_generate_l1_sweep_task_checked_in_service_requests_gate_and_refresh_release() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        c1_config_path, c1_sweep_path, c2_config_path, c2_sweep_path = _prepare_checked_in_multivalue_service_repo(repo_root)
        source_commit = _init_git_repo(repo_root)
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        service_dep_id = "l2_decoder_attention_decode_score_multivalue_integrated_service_llama7b_v1_r1"
        c1_item_id = "l1_decoder_attention_decode_score_multivalue_service_c1_p128_b4_q4_rl2_rr_pnr_v1"
        c2_item_id = "l1_decoder_attention_decode_score_multivalue_service_c2_p128_b4_q4_rl2_rr_pnr_v1"

        with Session(engine) as session:
            c1_result = generate_l1_sweep_task(
                session,
                _make_l1_request(
                    repo_root=str(repo_root),
                    sweep_path=c1_sweep_path,
                    config_paths=[c1_config_path],
                    platform="nangate45",
                    out_root="runs/designs/npu_blocks",
                    item_id=c1_item_id,
                    requested_by="@tester",
                    source_commit=source_commit,
                ),
            )
            c1_item = session.query(WorkItem).filter_by(item_id=c1_result.item_id).one()
            assert c1_item.state == WorkItemState.BLOCKED
            assert c1_item.task_request.request_payload["developer_loop"]["dependencies"] == {
                "item_ids": [service_dep_id],
                "requires_merged_inputs": True,
                "requires_materialized_refs": True,
            }

            _seed_materialized_dependency(
                session,
                repo_root=repo_root,
                item_id=service_dep_id,
                layer="layer2",
                task_type="l2_campaign",
                source_commit=source_commit,
                artifact_kind="decision_proposal",
                expected_output_rel="runs/campaigns/integrated_service/summary.csv",
            )
            session.commit()

            c2_result = generate_l1_sweep_task(
                session,
                _make_l1_request(
                    repo_root=str(repo_root),
                    sweep_path=c2_sweep_path,
                    config_paths=[c2_config_path],
                    platform="nangate45",
                    out_root="runs/designs/npu_blocks",
                    item_id=c2_item_id,
                    requested_by="@tester",
                    source_commit=source_commit,
                ),
            )
            c2_item = session.query(WorkItem).filter_by(item_id=c2_result.item_id).one()
            assert c2_item.state == WorkItemState.BLOCKED
            assert c2_item.task_request.request_payload["developer_loop"]["dependencies"] == {
                "item_ids": [service_dep_id, c1_item_id],
                "requires_merged_inputs": True,
                "requires_materialized_refs": True,
            }

            released = refresh_all_blocked_items(session, repo_root=repo_root)
            session.commit()
            session.refresh(c1_item)
            session.refresh(c2_item)
            assert released == [c1_item_id]
            assert c1_item.state == WorkItemState.DISPATCH_PENDING
            assert c2_item.state == WorkItemState.BLOCKED

            c1_item.state = WorkItemState.MERGED
            c1_metrics_rel = (
                "runs/designs/npu_blocks/attention_decode_score_multivalue_service_c1_p128_b4_q4_rl2_rr/metrics.csv"
            )
            c1_promotion_rel = f"control_plane/shadow_exports/review/{c1_item_id}/promotion.json"
            c1_review_rel = f"control_plane/shadow_exports/review/{c1_item_id}/review_package.json"
            c1_queue_rel = f"control_plane/shadow_exports/review/{c1_item_id}/evaluated.json"
            for rel_path, contents in (
                (c1_promotion_rel, "{}\n"),
                (c1_review_rel, "{}\n"),
                (c1_queue_rel, json.dumps({"task": {"expected_outputs": [c1_metrics_rel]}}, indent=2) + "\n"),
                (c1_metrics_rel, "status,metric\nok,1\n"),
            ):
                path = repo_root / rel_path
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(contents, encoding="utf-8")
            c1_run = Run(
                run_key=f"test:{c1_item_id}:run",
                work_item_id=c1_item.id,
                attempt=1,
                executor_type="internal_worker",
                status=RunStatus.SUCCEEDED,
                started_at=utcnow(),
                completed_at=utcnow(),
                checkout_commit=source_commit,
                result_summary="ok",
                result_payload={},
            )
            session.add(c1_run)
            session.flush()
            for kind, rel_path in (
                ("promotion_proposal", c1_promotion_rel),
                ("review_package", c1_review_rel),
                ("queue_snapshot", c1_queue_rel),
                ("expected_output", c1_metrics_rel),
            ):
                session.add(
                    Artifact(
                        run_id=c1_run.id,
                        kind=kind,
                        storage_mode="repo",
                        path=rel_path,
                        sha256="test",
                        metadata_={},
                    )
                )
            session.commit()

            released = refresh_all_blocked_items(session, repo_root=repo_root)
            session.commit()
            session.refresh(c2_item)
            assert released == [c2_item_id]
            assert c2_item.state == WorkItemState.DISPATCH_PENDING


def test_generate_l1_sweep_task_adds_bridge_checker_for_exact_8ns_multivalue_cluster_item() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        config_path, _ = _write_example_attention_decode_score_multivalue_cluster_repo(repo_root)
        sweep_path = _write_attention_decode_score_multivalue_cluster_8ns_bridge_sweep(repo_root)
        source_commit = _init_git_repo(repo_root)
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            result = generate_l1_sweep_task(
                session,
                _make_l1_request(
                    repo_root=str(repo_root),
                    sweep_path=sweep_path,
                    config_paths=[config_path],
                    platform="nangate45",
                    out_root="runs/designs/npu_blocks",
                    item_id="l1_decoder_attention_decode_score_multivalue_cluster_pnr_8ns_v2",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="decoder_attention_decode_score_multivalue_cluster",
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            assert "check_attention_decode_score_multivalue_cluster_8ns_bridge" in [
                command["name"] for command in work_item.command_manifest
            ]
            assert (
                "python3 npu/eval/check_attention_decode_score_multivalue_cluster_8ns_bridge.py "
                "--metrics-path runs/designs/npu_blocks/attention_decode_score_multivalue_cluster_int8_m1x8_iterdiv/metrics.csv"
                in [command["run"] for command in work_item.command_manifest]
            )


def test_generate_l1_sweep_task_does_not_apply_v4_checker_to_legacy_v3_identity() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        config_path, _ = _write_example_attention_decode_score_multivalue_cluster_repo(repo_root)
        sweep_path = _write_attention_decode_score_multivalue_cluster_binary_fsm_8ns_v3_sweep(repo_root)
        source_commit = _init_git_repo(repo_root)
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            result = generate_l1_sweep_task(
                session,
                _make_l1_request(
                    repo_root=str(repo_root),
                    sweep_path=sweep_path,
                    config_paths=[config_path],
                    platform="nangate45",
                    out_root="runs/designs/npu_blocks",
                    item_id="l1_decoder_attention_decode_score_multivalue_cluster_pnr_binary_fsm_8ns_v3",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="decoder_attention_decode_score_multivalue_cluster",
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            assert "check_attention_decode_score_multivalue_cluster_binary_fsm" not in [
                command["name"] for command in work_item.command_manifest
            ]


def test_generate_l1_sweep_task_adds_binary_fsm_checker_for_retry_8ns_multivalue_cluster_item_r4() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        config_path, _ = _write_example_attention_decode_score_multivalue_cluster_repo(repo_root)
        sweep_path = _write_attention_decode_score_multivalue_cluster_binary_fsm_8ns_v4_sweep(repo_root)
        source_commit = _init_git_repo(repo_root)
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            result = generate_l1_sweep_task(
                session,
                _make_l1_request(
                    repo_root=str(repo_root),
                    sweep_path=sweep_path,
                    config_paths=[config_path],
                    platform="nangate45",
                    out_root="runs/designs/npu_blocks",
                    item_id="l1_decoder_attention_decode_score_multivalue_cluster_pnr_binary_fsm_8ns_v3_r4",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="decoder_attention_decode_score_multivalue_cluster",
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            checker_command_names = [command["name"] for command in work_item.command_manifest]
            assert checker_command_names.count("check_attention_decode_score_multivalue_cluster_binary_fsm") == 1
            assert (
                "python3 npu/eval/check_attention_decode_score_multivalue_cluster_binary_fsm.py "
                "--metrics-path runs/designs/npu_blocks/attention_decode_score_multivalue_cluster_int8_m1x8_iterdiv/metrics.csv "
                "--diagnostic-out runs/designs/npu_blocks/attention_decode_score_multivalue_cluster_int8_m1x8_iterdiv/binary_fsm_diagnostic.json "
                "--profile v4_nofsm"
                in [command["run"] for command in work_item.command_manifest]
            )
            assert (
                "runs/designs/npu_blocks/"
                "attention_decode_score_multivalue_cluster_int8_m1x8_iterdiv/"
                "binary_fsm_diagnostic.json"
                in work_item.expected_outputs
            )


def test_generate_l1_sweep_task_adds_targeted_binary_fsm_retry_profile_and_diagnostic() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        config_path = _write_attention_decode_score_multivalue_cluster_targeted_binary_config(
            repo_root
        )
        sweep_path = (
            _write_attention_decode_score_multivalue_cluster_targeted_binary_fsm_8ns_sweep(
                repo_root
            )
        )
        source_commit = _init_git_repo(repo_root)
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            result = generate_l1_sweep_task(
                session,
                _make_l1_request(
                    repo_root=str(repo_root),
                    sweep_path=sweep_path,
                    config_paths=[config_path],
                    platform="nangate45",
                    out_root="runs/designs/npu_blocks",
                    item_id=(
                        "l1_decoder_attention_decode_score_multivalue_cluster_pnr_"
                        "targeted_binary_fsm_8ns_v1_r1"
                    ),
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="decoder_attention_decode_score_multivalue_cluster",
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            checker_commands = [
                command
                for command in work_item.command_manifest
                if command["name"] == "check_attention_decode_score_multivalue_cluster_binary_fsm"
            ]
            assert len(checker_commands) == 1
            assert checker_commands[0]["run"].endswith(
                "--diagnostic-out runs/designs/npu_blocks/"
                "attention_decode_score_multivalue_cluster_int8_m1x8_iterdiv/"
                "targeted_binary_fsm_diagnostic.json --profile targeted_binary"
            )
            assert (
                "runs/designs/npu_blocks/"
                "attention_decode_score_multivalue_cluster_int8_m1x8_iterdiv/"
                "targeted_binary_fsm_diagnostic.json"
                in work_item.expected_outputs
            )


def test_generate_l1_sweep_task_adds_explicit_onehot_retry_profile_and_diagnostic() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        config_path = _write_attention_decode_score_multivalue_cluster_explicit_onehot_config(
            repo_root
        )
        sweep_path = (
            _write_attention_decode_score_multivalue_cluster_explicit_onehot_fsm_8ns_sweep(
                repo_root
            )
        )
        source_commit = _init_git_repo(repo_root)
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            result = generate_l1_sweep_task(
                session,
                _make_l1_request(
                    repo_root=str(repo_root),
                    sweep_path=sweep_path,
                    config_paths=[config_path],
                    platform="nangate45",
                    out_root="runs/designs/npu_blocks",
                    item_id=(
                        "l1_decoder_attention_decode_score_multivalue_cluster_pnr_"
                        "explicit_onehot_fsm_8ns_v1_r2"
                    ),
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="decoder_attention_decode_score_multivalue_cluster",
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            checker_commands = [
                command
                for command in work_item.command_manifest
                if command["name"] == "check_attention_decode_score_multivalue_cluster_explicit_onehot"
            ]
            run_block_sweep = next(
                command
                for command in work_item.command_manifest
                if command["name"] == "run_block_sweep"
            )
            assert len(checker_commands) == 1
            assert run_block_sweep["run"] == (
                "export PATH=/oss-cad-suite/bin:$PATH && "
                "python3 npu/synth/run_block_sweep.py "
                "--design_dir runs/designs/npu_blocks/"
                "attention_decode_score_multivalue_cluster_int8_m1x8_iterdiv "
                "--platform nangate45 "
                "--top attention_decode_score_multivalue_cluster_int8_m1x8_iterdiv "
                "--sweep runs/campaigns/npu/decode_score_multivalue_cluster_v1/sweeps/"
                "nangate45_decode_score_multivalue_cluster_8ns_explicit_onehot_fsm_v1.json "
                "--out_root runs/designs/npu_blocks "
                "--macro_manifest runs/designs/npu_blocks/"
                "attention_decode_score_multivalue_cluster_int8_m1x8_iterdiv/"
                "macro_manifest.json "
                "--skip_existing"
            )
            assert (
                "--config runs/designs/npu_blocks/"
                "attention_decode_score_multivalue_cluster_int8_m1x8_iterdiv/"
                "config_explicit_onehot_fsm.json"
                in next(
                    command["run"]
                    for command in work_item.command_manifest
                    if command["name"] == "check_attention_decode_score_multivalue_cluster_guard"
                )
            )
            assert checker_commands[0]["run"].endswith(
                "--diagnostic-out runs/designs/npu_blocks/"
                "attention_decode_score_multivalue_cluster_int8_m1x8_iterdiv/"
                "explicit_onehot_fsm_diagnostic.json --profile explicit_onehot"
            )
            assert (
                "runs/designs/npu_blocks/"
                "attention_decode_score_multivalue_cluster_int8_m1x8_iterdiv/"
                "explicit_onehot_fsm_diagnostic.json"
                in work_item.expected_outputs
            )


def test_binary_fsm_retry_profile_requires_exact_config_and_sweep() -> None:
    targeted_item_id = (
        "l1_decoder_attention_decode_score_multivalue_cluster_pnr_"
        "targeted_binary_fsm_8ns_v1_r1"
    )
    targeted_config = (
        "runs/designs/npu_blocks/"
        "attention_decode_score_multivalue_cluster_int8_m1x8_iterdiv/"
        "config_targeted_binary_fsm.json"
    )
    targeted_sweep = (
        "runs/campaigns/npu/decode_score_multivalue_cluster_v1/sweeps/"
        "nangate45_decode_score_multivalue_cluster_8ns_targeted_binary_fsm_v1.json"
    )

    assert (
        _multivalue_cluster_binary_fsm_profile(
            item_id=targeted_item_id,
            sweep_path=targeted_sweep,
            config_paths=[targeted_config],
        ).name
        == "targeted_binary"
    )
    assert (
        _multivalue_cluster_binary_fsm_profile(
            item_id=targeted_item_id,
            sweep_path=targeted_sweep,
            config_paths=[
                "runs/designs/npu_blocks/"
                "attention_decode_score_multivalue_cluster_int8_m1x8_iterdiv/config.json"
            ],
        )
        is None
    )
    assert (
        _multivalue_cluster_binary_fsm_profile(
            item_id=targeted_item_id,
            sweep_path=(
                "runs/campaigns/npu/decode_score_multivalue_cluster_v1/sweeps/"
                "nangate45_decode_score_multivalue_cluster_8ns_binary_fsm_v4.json"
            ),
            config_paths=[targeted_config],
        )
        is None
    )

    explicit_item_id = (
        "l1_decoder_attention_decode_score_multivalue_cluster_pnr_"
        "explicit_onehot_fsm_8ns_v1_r2"
    )
    explicit_config = (
        "runs/designs/npu_blocks/"
        "attention_decode_score_multivalue_cluster_int8_m1x8_iterdiv/"
        "config_explicit_onehot_fsm.json"
    )
    explicit_sweep = (
        "runs/campaigns/npu/decode_score_multivalue_cluster_v1/sweeps/"
        "nangate45_decode_score_multivalue_cluster_8ns_explicit_onehot_fsm_v1.json"
    )
    assert (
        _multivalue_cluster_binary_fsm_profile(
            item_id=explicit_item_id,
            sweep_path=explicit_sweep,
            config_paths=[explicit_config],
        ).name
        == "explicit_onehot"
    )
    assert (
        _multivalue_cluster_binary_fsm_profile(
            item_id=explicit_item_id,
            sweep_path=explicit_sweep,
            config_paths=[targeted_config],
        )
        is None
    )


def test_generate_l1_sweep_task_adds_lanes2_macro_hier_placement_checker() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        config_path = _write_example_attention_decode_score_multivalue_gqa_group_lanes2_repo(repo_root)
        sweep_path = _write_attention_decode_score_multivalue_gqa_lanes2_macro_hier_placement_sweep(repo_root)
        proposal_dir = repo_root / "docs" / "proposals" / "prop_decoder_attention_decode_score_multivalue_gqa8_group_llama7b_v1"
        proposal_dir.mkdir(parents=True)
        item_id = "l1_decoder_attention_decode_score_multivalue_gqa8_folded_lanes2_macro_placement_v1"
        baseline_item_id = "l1_decoder_attention_decode_score_multivalue_gqa8_folded_lanes2_pnr_v1"
        equivalence_item_id = "l2_decoder_attention_decode_score_multivalue_gqa8_folded_lane_equivalence_llama7b_v1"
        required_entry = {
            "item_id": item_id,
            "task_type": "l1_sweep",
            "objective": "Diagnose folded GQA8 lane2 physical placement failure at the 3.55 mm die with macro-preserving hierarchy comparison, retaining failed rows as explicit boundary evidence.",
            "evaluation_mode": "frontier_followup",
            "abstraction_layer": "decoder_attention_decode_score_multivalue_gqa_folded_lane",
            "comparison_role": "gqa8_folded_lanes2_macro_placement",
            "paired_baseline_item_id": baseline_item_id,
            "depends_on_item_ids": [equivalence_item_id],
            "requires_merged_inputs": True,
            "requires_materialized_refs": True,
            "expected_result": {
                "direction": "diagnose_gqa8_folded_lanes2_macro_hierarchy_placement",
                "reason": "Disentangle placement feasibility from flattening policy while keeping macros explicit.",
            },
            "config_paths": [
                "runs/designs/npu_blocks/attention_decode_score_multivalue_gqa_group_lanes2_int8_m1x8_iterdiv/config.json"
            ],
            "sweep_path": "runs/campaigns/npu/decode_score_multivalue_gqa_folded_lanes_v1/sweeps/"
            "nangate45_decode_score_multivalue_gqa_lanes2_macro_hier_placement_compare_3550.json",
            "status": "pending_implementation_merge",
        }
        (proposal_dir / "proposal.json").write_text(
            json.dumps(
                {
                    "proposal_id": "prop_decoder_attention_decode_score_multivalue_gqa8_group_llama7b_v1",
                    "required_evaluations": [required_entry],
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (proposal_dir / "evaluation_requests.json").write_text(
            json.dumps(
                {
                    "proposal_id": "prop_decoder_attention_decode_score_multivalue_gqa8_group_llama7b_v1",
                    "source_commit": "",
                    "requested_items": [required_entry],
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        equivalence_artifact_path = (
            repo_root / "control_plane" / "shadow_exports" / "l2_decisions" / f"{equivalence_item_id}.json"
        )
        equivalence_artifact_path.parent.mkdir(parents=True)
        equivalence_artifact_path.write_text("{}\n", encoding="utf-8")

        source_commit = _init_git_repo(repo_root)
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            equivalence_request = TaskRequest(
                request_key=f"test:{equivalence_item_id}",
                source="test",
                requested_by="@tester",
                title="Merged folded-lane equivalence",
                description="",
                layer="layer2",
                flow="openroad",
                priority=1,
                request_payload={},
            )
            baseline_request = TaskRequest(
                request_key=f"test:{baseline_item_id}",
                source="test",
                requested_by="@tester",
                title="Unmerged lane2 physical baseline",
                description="",
                layer="layer1",
                flow="openroad",
                priority=1,
                request_payload={},
            )
            session.add_all([equivalence_request, baseline_request])
            session.flush()
            equivalence_item = WorkItem(
                work_item_key=f"test:{equivalence_item_id}",
                task_request_id=equivalence_request.id,
                item_id=equivalence_item_id,
                layer="layer2",
                flow="openroad",
                platform="nangate45",
                task_type="l2_campaign",
                state=WorkItemState.MERGED,
                priority=1,
                input_manifest={},
                command_manifest=[],
                expected_outputs=[],
                acceptance_rules=[],
            )
            baseline_item = WorkItem(
                work_item_key=f"test:{baseline_item_id}",
                task_request_id=baseline_request.id,
                item_id=baseline_item_id,
                layer="layer1",
                flow="openroad",
                platform="nangate45",
                task_type="l1_sweep",
                state=WorkItemState.AWAITING_REVIEW,
                priority=1,
                input_manifest={},
                command_manifest=[],
                expected_outputs=[],
                acceptance_rules=[],
            )
            session.add_all([equivalence_item, baseline_item])
            session.flush()
            equivalence_run = Run(
                run_key=f"test:{equivalence_item_id}:run",
                work_item_id=equivalence_item.id,
                attempt=1,
                executor_type="internal_worker",
                status=RunStatus.SUCCEEDED,
                started_at=utcnow(),
                completed_at=utcnow(),
                checkout_commit=source_commit,
                result_summary="equivalence merged",
                result_payload={},
            )
            session.add(equivalence_run)
            session.flush()
            session.add(
                Artifact(
                    run_id=equivalence_run.id,
                    kind="decision_proposal",
                    storage_mode="repo",
                    path=str(equivalence_artifact_path.relative_to(repo_root)),
                    sha256="test",
                    metadata_={},
                )
            )
            session.flush()

            result = generate_l1_sweep_task(
                session,
                _make_l1_request(
                    repo_root=str(repo_root),
                    sweep_path=sweep_path,
                    config_paths=[config_path],
                    platform="nangate45",
                    out_root="runs/designs/npu_blocks",
                    item_id=item_id,
                    requested_by="@tester",
                    source_commit=source_commit,
                    # Proposal linkage should be auto-discovered from local required_evaluations.
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            assert baseline_item.state == WorkItemState.AWAITING_REVIEW
            assert work_item.state == WorkItemState.DISPATCH_PENDING
            command_names = [command["name"] for command in work_item.command_manifest]
            assert "check_attention_decode_score_multivalue_gqa_lanes2_macro_hier_placement" in command_names
            assert (
                "python3 npu/eval/check_attention_decode_score_multivalue_gqa_lanes2_macro_hier_placement.py "
                "--metrics-path runs/designs/npu_blocks/"
                "attention_decode_score_multivalue_gqa_group_lanes2_int8_m1x8_iterdiv/metrics.csv "
                "--out runs/designs/npu_blocks/"
                "attention_decode_score_multivalue_gqa_group_lanes2_int8_m1x8_iterdiv/"
                "mode_compare_lanes2_placement_diag.json"
                in [command["run"] for command in work_item.command_manifest]
            )
            sweep_command = work_item.command_manifest[2]["run"]
            assert "--make_target 3_5_place_dp" in sweep_command
            assert (
                "runs/designs/npu_blocks/"
                "attention_decode_score_multivalue_gqa_group_lanes2_int8_m1x8_iterdiv/"
                "mode_compare_lanes2_placement_diag.json"
                in work_item.expected_outputs
            )

            dev_loop = work_item.task_request.request_payload["developer_loop"]
            assert dev_loop["proposal_path"] == "docs/proposals/prop_decoder_attention_decode_score_multivalue_gqa8_group_llama7b_v1"
            assert dev_loop["proposal_id"] == "prop_decoder_attention_decode_score_multivalue_gqa8_group_llama7b_v1"
            assert dev_loop["comparison"]["role"] == "gqa8_folded_lanes2_macro_placement"
            assert (
                dev_loop["comparison"]["paired_baseline_item_id"]
                == "l1_decoder_attention_decode_score_multivalue_gqa8_folded_lanes2_pnr_v1"
            )
            assert dev_loop["dependencies"]["item_ids"] == [
                equivalence_item_id,
            ]
            assert dev_loop["evaluation"]["expected_direction"] == (
                "diagnose_gqa8_folded_lanes2_macro_hierarchy_placement"
            )
            assert (
                dev_loop["evaluation"]["expected_reason"]
                == "Disentangle placement feasibility from flattening policy while keeping macros explicit."
            )

        assert result.status == "applied"


def test_generate_l1_sweep_task_supports_attention_decode_score_multivalue_gqa_group_configs() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        config_path, sweep_path = _write_example_attention_decode_score_multivalue_gqa_group_repo(
            repo_root
        )
        source_commit = _init_git_repo(repo_root)
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            result = generate_l1_sweep_task(
                session,
                _make_l1_request(
                    repo_root=str(repo_root),
                    sweep_path=sweep_path,
                    config_paths=[config_path],
                    platform="nangate45",
                    out_root="runs/designs/npu_blocks",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="decoder_attention_decode_score_multivalue_gqa_group",
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            assert [command["name"] for command in work_item.command_manifest] == [
                "generate_attention_decode_score_multivalue_gqa_group_rtl",
                "check_attention_decode_score_multivalue_gqa_group_guard",
                "run_block_sweep",
                "extract_attention_decode_score_multivalue_gqa_group_timing_paths",
                "build_runs_index",
                "validate",
            ]
            assert (
                "gen_attention_decode_score_multivalue_gqa_group.py"
                in work_item.command_manifest[0]["run"]
            )
            assert (
                "check_attention_decode_score_multivalue_gqa_group_guard.py"
                in work_item.command_manifest[1]["run"]
            )
            sweep_command = work_item.command_manifest[2]["run"]
            assert (
                "--top attention_decode_score_multivalue_gqa_group_int8_m1x8_iterdiv"
                in sweep_command
            )
            assert (
                "--macro_manifest runs/designs/npu_blocks/"
                "attention_decode_score_multivalue_gqa_group_int8_m1x8_iterdiv/macro_manifest.json"
                in sweep_command
            )
            assert "--skip_existing" in sweep_command
            assert work_item.expected_outputs == [
                "runs/designs/npu_blocks/attention_decode_score_multivalue_gqa_group_int8_m1x8_iterdiv/metrics.csv",
                "runs/designs/npu_blocks/attention_decode_score_multivalue_gqa_group_int8_m1x8_iterdiv/"
                "timing_debug_report.md",
            ]


def test_generate_l1_sweep_task_supports_attention_decode_score_multivalue_gqa_array_configs() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        config_path, sweep_path = _write_example_attention_decode_score_multivalue_gqa_array_repo(
            repo_root
        )
        source_commit = _init_git_repo(repo_root)
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            result = generate_l1_sweep_task(
                session,
                _make_l1_request(
                    repo_root=str(repo_root),
                    sweep_path=sweep_path,
                    config_paths=[config_path],
                    platform="nangate45",
                    out_root="runs/designs/npu_blocks",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="decoder_attention_decode_score_multivalue_gqa_array",
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            assert [command["name"] for command in work_item.command_manifest] == [
                "generate_attention_decode_score_multivalue_gqa_array_rtl",
                "check_attention_decode_score_multivalue_gqa_array_guard",
                "run_block_sweep",
                "extract_attention_decode_score_multivalue_gqa_array_timing_paths",
                "build_runs_index",
                "validate",
            ]
            assert "gen_attention_decode_score_multivalue_gqa_array.py" in work_item.command_manifest[0][
                "run"
            ]
            assert "check_attention_decode_score_multivalue_gqa_array_guard.py" in work_item.command_manifest[
                1
            ]["run"]
            sweep_command = work_item.command_manifest[2]["run"]
            assert (
                "--top attention_decode_score_multivalue_gqa_array_g2_int8_m1x8_iterdiv"
                in sweep_command
            )
            assert (
                "--macro_manifest runs/designs/npu_blocks/"
                "attention_decode_score_multivalue_gqa_array_g2_int8_m1x8_iterdiv/macro_manifest.json"
                in sweep_command
            )
            assert work_item.expected_outputs == [
                "runs/designs/npu_blocks/"
                "attention_decode_score_multivalue_gqa_array_g2_int8_m1x8_iterdiv/metrics.csv",
                "runs/designs/npu_blocks/"
                "attention_decode_score_multivalue_gqa_array_g2_int8_m1x8_iterdiv/"
                "timing_debug_report.md",
            ]


def test_generate_l1_sweep_task_supports_multi_attention_command_dispatch_configs() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        config_path, sweep_path = _write_example_attention_command_dispatch_repo(repo_root)
        second_config_path = _write_second_attention_command_dispatch_repo(repo_root)
        source_commit = _init_git_repo(repo_root)
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            result = generate_l1_sweep_task(
                session,
                _make_l1_request(
                    repo_root=str(repo_root),
                    sweep_path=sweep_path,
                    config_paths=[config_path, second_config_path],
                    platform="nangate45",
                    out_root="runs/designs/npu_blocks",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="decoder_attention_command_dispatch_control",
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            assert [command["name"] for command in work_item.command_manifest] == [
                "generate_attention_command_dispatch_rtl_attention_command_dispatch_smoke",
                "check_attention_command_dispatch_guard_attention_command_dispatch_smoke",
                "run_block_sweep_attention_command_dispatch_smoke",
                "extract_attention_command_dispatch_timing_paths_attention_command_dispatch_smoke",
                "generate_attention_command_dispatch_rtl_attention_command_dispatch_c16_q32",
                "check_attention_command_dispatch_guard_attention_command_dispatch_c16_q32",
                "run_block_sweep_attention_command_dispatch_c16_q32",
                "extract_attention_command_dispatch_timing_paths_attention_command_dispatch_c16_q32",
                "build_runs_index",
                "validate",
            ]
            assert "attention_command_dispatch_smoke/config.json" in work_item.command_manifest[0]["run"]
            assert "attention_command_dispatch_c16_q32/config.json" in work_item.command_manifest[4]["run"]
            assert work_item.expected_outputs == [
                "runs/designs/npu_blocks/attention_command_dispatch_smoke/metrics.csv",
                "runs/designs/npu_blocks/attention_command_dispatch_smoke/timing_debug_report.md",
                "runs/designs/npu_blocks/attention_command_dispatch_c16_q32/metrics.csv",
                "runs/designs/npu_blocks/attention_command_dispatch_c16_q32/timing_debug_report.md",
            ]


def test_generate_l1_sweep_task_supports_multi_attention_score32_exact_local_temporal_reducer_physical_harness_configs() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        config_path, sweep_path = _write_example_attention_score32_exact_local_temporal_reducer_physical_harness_repo(
            repo_root
        )
        second_config_path = _write_second_attention_score32_exact_local_temporal_reducer_physical_harness_repo(
            repo_root
        )
        source_commit = _init_git_repo(repo_root)
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            result = generate_l1_sweep_task(
                session,
                _make_l1_request(
                    repo_root=str(repo_root),
                    sweep_path=sweep_path,
                    config_paths=[config_path, second_config_path],
                    platform="nangate45",
                    out_root="runs/designs/npu_blocks",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="decoder_attention_score32_local_temporal_reducer",
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            assert [command["name"] for command in work_item.command_manifest] == [
                "generate_attention_score32_exact_local_temporal_reducer_physical_harness_rtl_"
                "attention_score32_exact_local_temporal_reducer_physical_harness_p53_reducer_w8",
                "check_attention_score32_exact_local_temporal_reducer_physical_harness_guard_"
                "attention_score32_exact_local_temporal_reducer_physical_harness_p53_reducer_w8",
                "run_block_sweep_attention_score32_exact_local_temporal_reducer_physical_harness_p53_reducer_w8",
                "extract_attention_score32_exact_local_temporal_reducer_physical_harness_timing_paths_"
                "attention_score32_exact_local_temporal_reducer_physical_harness_p53_reducer_w8",
                "generate_attention_score32_exact_local_temporal_reducer_physical_harness_rtl_"
                "attention_score32_exact_local_temporal_reducer_physical_harness_p54_source_only_w8",
                "check_attention_score32_exact_local_temporal_reducer_physical_harness_guard_"
                "attention_score32_exact_local_temporal_reducer_physical_harness_p54_source_only_w8",
                "run_block_sweep_attention_score32_exact_local_temporal_reducer_physical_harness_p54_source_only_w8",
                "extract_attention_score32_exact_local_temporal_reducer_physical_harness_timing_paths_"
                "attention_score32_exact_local_temporal_reducer_physical_harness_p54_source_only_w8",
                "build_runs_index",
                "validate",
            ]
            assert (
                "gen_attention_score32_exact_local_temporal_reducer_physical_harness.py"
                in work_item.command_manifest[0]["run"]
            )
            assert "attention_score32_exact_local_temporal_reducer_physical_harness_p53_reducer_w8/config.json" in (
                work_item.command_manifest[0]["run"]
            )
            assert (
                "check_attention_score32_exact_local_temporal_reducer_physical_harness_guard.py"
                in work_item.command_manifest[1]["run"]
            )
            assert "attention_score32_exact_local_temporal_reducer_physical_harness_p54_source_only_w8/config.json" in (
                work_item.command_manifest[4]["run"]
            )
            assert (
                "--top attention_score32_exact_local_temporal_reducer_physical_harness_p53_reducer_w8"
                in work_item.command_manifest[2]["run"]
            )
            assert (
                "--top attention_score32_exact_local_temporal_reducer_physical_harness_p54_source_only_w8"
                in work_item.command_manifest[6]["run"]
            )
            assert work_item.command_manifest[3]["run"] == (
                "python3 npu/eval/extract_openroad_timing_summary.py "
                "--design-dir runs/designs/npu_blocks/"
                "attention_score32_exact_local_temporal_reducer_physical_harness_p53_reducer_w8 "
                "--out runs/designs/npu_blocks/"
                "attention_score32_exact_local_temporal_reducer_physical_harness_p53_reducer_w8/"
                "timing_debug_report.md "
                "--max-paths 8"
            )
            assert work_item.command_manifest[7]["run"] == (
                "python3 npu/eval/extract_openroad_timing_summary.py "
                "--design-dir runs/designs/npu_blocks/"
                "attention_score32_exact_local_temporal_reducer_physical_harness_p54_source_only_w8 "
                "--out runs/designs/npu_blocks/"
                "attention_score32_exact_local_temporal_reducer_physical_harness_p54_source_only_w8/"
                "timing_debug_report.md "
                "--max-paths 8"
            )
            assert work_item.expected_outputs == [
                "runs/designs/npu_blocks/"
                "attention_score32_exact_local_temporal_reducer_physical_harness_p53_reducer_w8/metrics.csv",
                "runs/designs/npu_blocks/"
                "attention_score32_exact_local_temporal_reducer_physical_harness_p53_reducer_w8/"
                "timing_debug_report.md",
                "runs/designs/npu_blocks/"
                "attention_score32_exact_local_temporal_reducer_physical_harness_p54_source_only_w8/metrics.csv",
                "runs/designs/npu_blocks/"
                "attention_score32_exact_local_temporal_reducer_physical_harness_p54_source_only_w8/"
                "timing_debug_report.md",
            ]


def test_generate_l1_sweep_task_supports_multi_attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_configs() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        config_path, sweep_path = _write_example_attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_repo(
            repo_root
        )
        second_config_path = _write_second_attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_repo(
            repo_root
        )
        source_commit = _init_git_repo(repo_root)
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            result = generate_l1_sweep_task(
                session,
                _make_l1_request(
                    repo_root=str(repo_root),
                    sweep_path=sweep_path,
                    config_paths=[config_path, second_config_path],
                    platform="nangate45",
                    out_root="runs/designs/npu_blocks",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="decoder_attention_score32_local_temporal_reducer_gqa8",
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            assert [command["name"] for command in work_item.command_manifest] == [
                "generate_attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_rtl_"
                "attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p53_reducer_w8",
                "check_attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_guard_"
                "attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p53_reducer_w8",
                "run_block_sweep_attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p53_reducer_w8",
                "extract_attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_timing_paths_"
                "attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p53_reducer_w8",
                "generate_attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_rtl_"
                "attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p54_source_only_w8",
                "check_attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_guard_"
                "attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p54_source_only_w8",
                "run_block_sweep_attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p54_source_only_w8",
                "extract_attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_timing_paths_"
                "attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p54_source_only_w8",
                "build_runs_index",
                "validate",
            ]
            assert (
                "gen_attention_score32_exact_local_temporal_reducer_gqa8_physical_harness.py"
                in work_item.command_manifest[0]["run"]
            )
            assert "attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p53_reducer_w8/config.json" in (
                work_item.command_manifest[0]["run"]
            )
            assert (
                "check_attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_guard.py"
                in work_item.command_manifest[1]["run"]
            )
            assert "attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p54_source_only_w8/config.json" in (
                work_item.command_manifest[4]["run"]
            )
            assert (
                "--top attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p53_reducer_w8"
                in work_item.command_manifest[2]["run"]
            )
            assert (
                "--top attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p54_source_only_w8"
                in work_item.command_manifest[6]["run"]
            )
            assert work_item.command_manifest[3]["run"] == (
                "python3 npu/eval/extract_openroad_timing_summary.py "
                "--design-dir runs/designs/npu_blocks/"
                "attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p53_reducer_w8 "
                "--out runs/designs/npu_blocks/"
                "attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p53_reducer_w8/"
                "timing_debug_report.md "
                "--max-paths 8"
            )
            assert work_item.command_manifest[7]["run"] == (
                "python3 npu/eval/extract_openroad_timing_summary.py "
                "--design-dir runs/designs/npu_blocks/"
                "attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p54_source_only_w8 "
                "--out runs/designs/npu_blocks/"
                "attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p54_source_only_w8/"
                "timing_debug_report.md "
                "--max-paths 8"
            )
            assert work_item.expected_outputs == [
                "runs/designs/npu_blocks/"
                "attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p53_reducer_w8/metrics.csv",
                "runs/designs/npu_blocks/"
                "attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p53_reducer_w8/"
                "timing_debug_report.md",
                "runs/designs/npu_blocks/"
                "attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p54_source_only_w8/metrics.csv",
                "runs/designs/npu_blocks/"
                "attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p54_source_only_w8/"
                "timing_debug_report.md",
            ]


def test_generate_l1_sweep_task_adds_macro_hardening_for_gqa8_folded_mersenne_macro_config() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        config_path, sweep_path = _write_macro_attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_repo(
            repo_root
        )
        source_commit = _init_git_repo(repo_root)
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            result = generate_l1_sweep_task(
                session,
                _make_l1_request(
                    repo_root=str(repo_root),
                    sweep_path=sweep_path,
                    config_paths=[config_path],
                    platform="nangate45",
                    out_root="runs/designs/npu_blocks",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="decoder_attention_score32_local_temporal_reducer_gqa8",
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            assert [command["name"] for command in work_item.command_manifest] == [
                "generate_attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_rtl",
                "check_attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_guard",
                "harden_attention_score32_exact_local_temporal_reducer_gqa8_pair_node_macro",
                "harden_attention_score32_exact_local_temporal_reducer_gqa8_temporal_merge_macro",
                "build_attention_score32_exact_local_temporal_reducer_gqa8_macro_manifest",
                "run_block_sweep",
                "extract_attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_timing_paths",
                "build_runs_index",
                "validate",
            ]
            assert "pre_synth_compute.py" in work_item.command_manifest[2]["run"]
            assert (
                "--module "
                "attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_"
                "p53_reducer_factored_hier_folded_mersenne_macro_w8__reducer__local_reducer__pair_node"
                in work_item.command_manifest[2]["run"]
            )
            assert (
                "--module "
                "attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_"
                "p53_reducer_factored_hier_folded_mersenne_macro_w8__reducer__temporal_merge"
                in work_item.command_manifest[3]["run"]
            )
            assert "--manifest_param macro_eval_excludes_io_pads=true" in work_item.command_manifest[2]["run"]
            assert "--manifest_param macro_eval_excludes_io_pads=true" in work_item.command_manifest[3]["run"]
            assert "build_composite_macro_manifest.py" in work_item.command_manifest[4]["run"]
            assert "--platform nangate45" in work_item.command_manifest[4]["run"]
            assert "--manifest-param pair_node_instance_count=52" in work_item.command_manifest[4]["run"]
            assert (
                "--macro_manifest runs/designs/npu_blocks/"
                "attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_"
                "p53_reducer_factored_hier_folded_mersenne_macro_w8/macro_manifest.json"
                in work_item.command_manifest[5]["run"]
            )
            assert work_item.expected_outputs == [
                "runs/designs/npu_blocks/"
                "attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_"
                "p53_reducer_factored_hier_folded_mersenne_macro_w8/metrics.csv",
                "runs/designs/npu_blocks/"
                "attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_"
                "p53_reducer_factored_hier_folded_mersenne_macro_w8/timing_debug_report.md",
                "runs/designs/npu_macros/"
                "attention_score32_exact_local_temporal_reducer_gqa8_pair_node_ng45_r7/metrics.csv",
                "runs/designs/npu_macros/"
                "attention_score32_exact_local_temporal_reducer_gqa8_temporal_merge_ng45_r7/metrics.csv",
            ]


def test_generate_l1_sweep_task_supports_multi_attention_score32_exact_root_finalizer_configs() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        config_path, sweep_path = _write_example_attention_score32_exact_root_finalizer_repo(repo_root)
        second_config_path = _write_second_attention_score32_exact_root_finalizer_repo(repo_root)
        source_commit = _init_git_repo(repo_root)
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            result = generate_l1_sweep_task(
                session,
                _make_l1_request(
                    repo_root=str(repo_root),
                    sweep_path=sweep_path,
                    config_paths=[config_path, second_config_path],
                    platform="nangate45",
                    out_root="runs/designs/npu_blocks",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="architecture_block",
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            assert [command["name"] for command in work_item.command_manifest] == [
                "generate_attention_score32_exact_root_finalizer_rtl_attention_score32_exact_root_finalizer_smoke_l4",
                "check_attention_score32_exact_root_finalizer_guard_attention_score32_exact_root_finalizer_smoke_l4",
                "run_block_sweep_attention_score32_exact_root_finalizer_smoke_l4",
                "extract_attention_score32_exact_root_finalizer_timing_paths_attention_score32_exact_root_finalizer_smoke_l4",
                "generate_attention_score32_exact_root_finalizer_rtl_attention_score32_exact_root_finalizer_smoke_l8",
                "check_attention_score32_exact_root_finalizer_guard_attention_score32_exact_root_finalizer_smoke_l8",
                "run_block_sweep_attention_score32_exact_root_finalizer_smoke_l8",
                "extract_attention_score32_exact_root_finalizer_timing_paths_attention_score32_exact_root_finalizer_smoke_l8",
                "build_runs_index",
                "validate",
            ]
            assert "attention_score32_exact_root_finalizer_smoke_l4/config.json" in work_item.command_manifest[0]["run"]
            assert "attention_score32_exact_root_finalizer_smoke_l8/config.json" in work_item.command_manifest[4]["run"]
            assert work_item.expected_outputs == [
                "runs/designs/npu_blocks/attention_score32_exact_root_finalizer_smoke_l4/metrics.csv",
                "runs/designs/npu_blocks/attention_score32_exact_root_finalizer_smoke_l4/timing_debug_report.md",
                "runs/designs/npu_blocks/attention_score32_exact_root_finalizer_smoke_l8/metrics.csv",
                "runs/designs/npu_blocks/attention_score32_exact_root_finalizer_smoke_l8/timing_debug_report.md",
            ]


def test_generate_l1_sweep_task_emits_commands_for_each_attention_score32_exact_partial_tree_config() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        config_path, sweep_path = _write_example_attention_score32_exact_partial_tree_repo(repo_root)
        second_config_path = _write_second_attention_score32_exact_partial_tree_repo(repo_root)
        source_commit = _init_git_repo(repo_root)
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            result = generate_l1_sweep_task(
                session,
                _make_l1_request(
                    repo_root=str(repo_root),
                    sweep_path=sweep_path,
                    config_paths=[config_path, second_config_path],
                    platform="nangate45",
                    out_root="runs/designs/npu_blocks",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="architecture_block",
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            assert [command["name"] for command in work_item.command_manifest] == [
                "generate_attention_score32_exact_partial_tree_rtl_attention_score32_exact_partial_tree_smoke_c4_r2",
                "check_attention_score32_exact_partial_tree_guard_attention_score32_exact_partial_tree_smoke_c4_r2",
                "run_block_sweep_attention_score32_exact_partial_tree_smoke_c4_r2",
                "extract_attention_score32_exact_partial_tree_timing_paths_attention_score32_exact_partial_tree_smoke_c4_r2",
                "generate_attention_score32_exact_partial_tree_rtl_attention_score32_exact_partial_tree_smoke_c16_r2",
                "check_attention_score32_exact_partial_tree_guard_attention_score32_exact_partial_tree_smoke_c16_r2",
                "run_block_sweep_attention_score32_exact_partial_tree_smoke_c16_r2",
                "extract_attention_score32_exact_partial_tree_timing_paths_attention_score32_exact_partial_tree_smoke_c16_r2",
                "build_runs_index",
                "validate",
            ]
            assert "attention_score32_exact_partial_tree_smoke_c4_r2/config.json" in work_item.command_manifest[0]["run"]
            assert "attention_score32_exact_partial_tree_smoke_c16_r2/config.json" in work_item.command_manifest[4]["run"]
            assert work_item.expected_outputs == [
                "runs/designs/npu_blocks/attention_score32_exact_partial_tree_smoke_c4_r2/metrics.csv",
                "runs/designs/npu_blocks/attention_score32_exact_partial_tree_smoke_c4_r2/timing_debug_report.md",
                "runs/designs/npu_blocks/attention_score32_exact_partial_tree_smoke_c16_r2/metrics.csv",
                "runs/designs/npu_blocks/attention_score32_exact_partial_tree_smoke_c16_r2/timing_debug_report.md",
            ]


def test_generate_l1_sweep_task_emits_commands_for_each_attention_score32_exact_finalized_tree_config() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        config_path, sweep_path = _write_example_attention_score32_exact_finalized_tree_repo(repo_root)
        second_config_path = _write_second_attention_score32_exact_finalized_tree_repo(repo_root)
        source_commit = _init_git_repo(repo_root)
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            result = generate_l1_sweep_task(
                session,
                _make_l1_request(
                    repo_root=str(repo_root),
                    sweep_path=sweep_path,
                    config_paths=[config_path, second_config_path],
                    platform="nangate45",
                    out_root="runs/designs/npu_blocks",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="architecture_block",
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            assert [command["name"] for command in work_item.command_manifest] == [
                "generate_attention_score32_exact_finalized_tree_rtl_attention_score32_exact_finalized_tree_smoke_c16_r2_l4",
                "check_attention_score32_exact_finalized_tree_guard_attention_score32_exact_finalized_tree_smoke_c16_r2_l4",
                "run_block_sweep_attention_score32_exact_finalized_tree_smoke_c16_r2_l4",
                "extract_attention_score32_exact_finalized_tree_timing_paths_attention_score32_exact_finalized_tree_smoke_c16_r2_l4",
                "generate_attention_score32_exact_finalized_tree_rtl_attention_score32_exact_finalized_tree_smoke_c16_r2_l8",
                "check_attention_score32_exact_finalized_tree_guard_attention_score32_exact_finalized_tree_smoke_c16_r2_l8",
                "run_block_sweep_attention_score32_exact_finalized_tree_smoke_c16_r2_l8",
                "extract_attention_score32_exact_finalized_tree_timing_paths_attention_score32_exact_finalized_tree_smoke_c16_r2_l8",
                "build_runs_index",
                "validate",
            ]
            assert "attention_score32_exact_finalized_tree_smoke_c16_r2_l4/config.json" in work_item.command_manifest[0]["run"]
            assert "attention_score32_exact_finalized_tree_smoke_c16_r2_l8/config.json" in work_item.command_manifest[4]["run"]
            assert work_item.expected_outputs == [
                "runs/designs/npu_blocks/attention_score32_exact_finalized_tree_smoke_c16_r2_l4/metrics.csv",
                "runs/designs/npu_blocks/attention_score32_exact_finalized_tree_smoke_c16_r2_l4/timing_debug_report.md",
                "runs/designs/npu_blocks/attention_score32_exact_finalized_tree_smoke_c16_r2_l8/metrics.csv",
                "runs/designs/npu_blocks/attention_score32_exact_finalized_tree_smoke_c16_r2_l8/timing_debug_report.md",
            ]


def test_generate_l1_sweep_task_emits_commands_for_each_attention_score32_exact_banked_finalized_tree_config() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        config_path, sweep_path = _write_example_attention_score32_exact_banked_finalized_tree_repo(repo_root)
        second_config_path = _write_second_attention_score32_exact_banked_finalized_tree_repo(repo_root)
        third_config_path = _write_third_attention_score32_exact_banked_finalized_tree_repo(repo_root)
        fourth_config_path = _write_fourth_attention_score32_exact_banked_finalized_tree_repo(repo_root)
        source_commit = _init_git_repo(repo_root)
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            result = generate_l1_sweep_task(
                session,
                _make_l1_request(
                    repo_root=str(repo_root),
                    sweep_path=sweep_path,
                    config_paths=[config_path, second_config_path, third_config_path, fourth_config_path],
                    platform="nangate45",
                    out_root="runs/designs/npu_blocks",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="architecture_block",
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            assert [command["name"] for command in work_item.command_manifest] == [
                "generate_attention_score32_exact_banked_finalized_tree_rtl_attention_score32_exact_banked_finalized_tree_smoke_c16_r2_l8_b16",
                "check_attention_score32_exact_banked_finalized_tree_guard_attention_score32_exact_banked_finalized_tree_smoke_c16_r2_l8_b16",
                "run_block_sweep_attention_score32_exact_banked_finalized_tree_smoke_c16_r2_l8_b16",
                "extract_attention_score32_exact_banked_finalized_tree_timing_paths_attention_score32_exact_banked_finalized_tree_smoke_c16_r2_l8_b16",
                "generate_attention_score32_exact_banked_finalized_tree_rtl_attention_score32_exact_banked_finalized_tree_smoke_c16_r2_l8_b32",
                "check_attention_score32_exact_banked_finalized_tree_guard_attention_score32_exact_banked_finalized_tree_smoke_c16_r2_l8_b32",
                "run_block_sweep_attention_score32_exact_banked_finalized_tree_smoke_c16_r2_l8_b32",
                "extract_attention_score32_exact_banked_finalized_tree_timing_paths_attention_score32_exact_banked_finalized_tree_smoke_c16_r2_l8_b32",
                "generate_attention_score32_exact_banked_finalized_tree_rtl_attention_score32_exact_banked_finalized_tree_smoke_c16_r2_l8_b59",
                "check_attention_score32_exact_banked_finalized_tree_guard_attention_score32_exact_banked_finalized_tree_smoke_c16_r2_l8_b59",
                "run_block_sweep_attention_score32_exact_banked_finalized_tree_smoke_c16_r2_l8_b59",
                "extract_attention_score32_exact_banked_finalized_tree_timing_paths_attention_score32_exact_banked_finalized_tree_smoke_c16_r2_l8_b59",
                "generate_attention_score32_exact_banked_finalized_tree_rtl_attention_score32_exact_banked_finalized_tree_smoke_c16_r2_l8_b64",
                "check_attention_score32_exact_banked_finalized_tree_guard_attention_score32_exact_banked_finalized_tree_smoke_c16_r2_l8_b64",
                "run_block_sweep_attention_score32_exact_banked_finalized_tree_smoke_c16_r2_l8_b64",
                "extract_attention_score32_exact_banked_finalized_tree_timing_paths_attention_score32_exact_banked_finalized_tree_smoke_c16_r2_l8_b64",
                "build_runs_index",
                "validate",
            ]
            assert "attention_score32_exact_banked_finalized_tree_smoke_c16_r2_l8_b16/config.json" in work_item.command_manifest[0]["run"]
            assert "attention_score32_exact_banked_finalized_tree_smoke_c16_r2_l8_b32/config.json" in work_item.command_manifest[4]["run"]
            assert "attention_score32_exact_banked_finalized_tree_smoke_c16_r2_l8_b59/config.json" in work_item.command_manifest[8]["run"]
            assert "attention_score32_exact_banked_finalized_tree_smoke_c16_r2_l8_b64/config.json" in work_item.command_manifest[12]["run"]
            assert work_item.expected_outputs == [
                "runs/designs/npu_blocks/attention_score32_exact_banked_finalized_tree_smoke_c16_r2_l8_b16/metrics.csv",
                "runs/designs/npu_blocks/attention_score32_exact_banked_finalized_tree_smoke_c16_r2_l8_b16/timing_debug_report.md",
                "runs/designs/npu_blocks/attention_score32_exact_banked_finalized_tree_smoke_c16_r2_l8_b32/metrics.csv",
                "runs/designs/npu_blocks/attention_score32_exact_banked_finalized_tree_smoke_c16_r2_l8_b32/timing_debug_report.md",
                "runs/designs/npu_blocks/attention_score32_exact_banked_finalized_tree_smoke_c16_r2_l8_b59/metrics.csv",
                "runs/designs/npu_blocks/attention_score32_exact_banked_finalized_tree_smoke_c16_r2_l8_b59/timing_debug_report.md",
                "runs/designs/npu_blocks/attention_score32_exact_banked_finalized_tree_smoke_c16_r2_l8_b64/metrics.csv",
                "runs/designs/npu_blocks/attention_score32_exact_banked_finalized_tree_smoke_c16_r2_l8_b64/timing_debug_report.md",
            ]


def test_generate_l1_sweep_task_supports_attention_score32_exact_finalizer_bank_control_configs() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        config_paths, sweep_path, proposal_id, proposal_path, item_id = (
            _copy_checked_in_attention_score32_exact_finalizer_bank_control_repo(repo_root)
        )
        source_commit = _init_git_repo(repo_root)
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            result = generate_l1_sweep_task(
                session,
                _make_l1_request(
                    repo_root=str(repo_root),
                    sweep_path=sweep_path,
                    config_paths=config_paths,
                    platform="nangate45",
                    out_root="runs/designs/npu_blocks",
                    item_id=item_id,
                    requested_by="@tester",
                    source_commit=source_commit,
                    proposal_id=proposal_id,
                    proposal_path=proposal_path,
                    update_proposal_files=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            assert result.status == "applied"
            assert work_item.priority == 95
            assert [command["name"] for command in work_item.command_manifest] == [
                "generate_attention_score32_exact_finalizer_bank_control_rtl_attention_score32_exact_finalizer_bank_control_l8_b1",
                "check_attention_score32_exact_finalizer_bank_control_guard_attention_score32_exact_finalizer_bank_control_l8_b1",
                "run_block_sweep_attention_score32_exact_finalizer_bank_control_l8_b1",
                "extract_attention_score32_exact_finalizer_bank_control_timing_paths_attention_score32_exact_finalizer_bank_control_l8_b1",
                "generate_attention_score32_exact_finalizer_bank_control_rtl_attention_score32_exact_finalizer_bank_control_l8_b4",
                "check_attention_score32_exact_finalizer_bank_control_guard_attention_score32_exact_finalizer_bank_control_l8_b4",
                "run_block_sweep_attention_score32_exact_finalizer_bank_control_l8_b4",
                "extract_attention_score32_exact_finalizer_bank_control_timing_paths_attention_score32_exact_finalizer_bank_control_l8_b4",
                "generate_attention_score32_exact_finalizer_bank_control_rtl_attention_score32_exact_finalizer_bank_control_l8_b8",
                "check_attention_score32_exact_finalizer_bank_control_guard_attention_score32_exact_finalizer_bank_control_l8_b8",
                "run_block_sweep_attention_score32_exact_finalizer_bank_control_l8_b8",
                "extract_attention_score32_exact_finalizer_bank_control_timing_paths_attention_score32_exact_finalizer_bank_control_l8_b8",
                "generate_attention_score32_exact_finalizer_bank_control_rtl_attention_score32_exact_finalizer_bank_control_l8_b16",
                "check_attention_score32_exact_finalizer_bank_control_guard_attention_score32_exact_finalizer_bank_control_l8_b16",
                "run_block_sweep_attention_score32_exact_finalizer_bank_control_l8_b16",
                "extract_attention_score32_exact_finalizer_bank_control_timing_paths_attention_score32_exact_finalizer_bank_control_l8_b16",
                "generate_attention_score32_exact_finalizer_bank_control_rtl_attention_score32_exact_finalizer_bank_control_l8_b32",
                "check_attention_score32_exact_finalizer_bank_control_guard_attention_score32_exact_finalizer_bank_control_l8_b32",
                "run_block_sweep_attention_score32_exact_finalizer_bank_control_l8_b32",
                "extract_attention_score32_exact_finalizer_bank_control_timing_paths_attention_score32_exact_finalizer_bank_control_l8_b32",
                "generate_attention_score32_exact_finalizer_bank_control_rtl_attention_score32_exact_finalizer_bank_control_l8_b59",
                "check_attention_score32_exact_finalizer_bank_control_guard_attention_score32_exact_finalizer_bank_control_l8_b59",
                "run_block_sweep_attention_score32_exact_finalizer_bank_control_l8_b59",
                "extract_attention_score32_exact_finalizer_bank_control_timing_paths_attention_score32_exact_finalizer_bank_control_l8_b59",
                "build_runs_index",
                "validate",
            ]
            assert work_item.command_manifest[0]["run"] == (
                "export PATH=/oss-cad-suite/bin:$PATH && "
                "python3 npu/rtlgen/gen_attention_score32_exact_finalizer_bank_control.py "
                "--config runs/designs/npu_blocks/attention_score32_exact_finalizer_bank_control_l8_b1/config.json "
                "--out runs/designs/npu_blocks/attention_score32_exact_finalizer_bank_control_l8_b1/verilog"
            )
            assert work_item.command_manifest[1]["run"] == (
                "python3 npu/eval/check_attention_score32_exact_finalizer_bank_control_guard.py "
                "--design-dir runs/designs/npu_blocks/attention_score32_exact_finalizer_bank_control_l8_b1 "
                "--config runs/designs/npu_blocks/attention_score32_exact_finalizer_bank_control_l8_b1/config.json "
                "--sweep runs/campaigns/npu/attention_score32_exact_finalizer_bank_control_v1/sweeps/"
                "nangate45_attention_score32_exact_finalizer_bank_control_lane8_firstpass.json"
            )
            assert work_item.command_manifest[2]["run"] == (
                "export PATH=/oss-cad-suite/bin:$PATH && "
                "python3 npu/synth/run_block_sweep.py "
                "--design_dir runs/designs/npu_blocks/attention_score32_exact_finalizer_bank_control_l8_b1 "
                "--platform nangate45 --top attention_score32_exact_finalizer_bank_control_l8_b1 "
                "--sweep runs/campaigns/npu/attention_score32_exact_finalizer_bank_control_v1/sweeps/"
                "nangate45_attention_score32_exact_finalizer_bank_control_lane8_firstpass.json "
                "--out_root runs/designs/npu_blocks --skip_existing"
            )
            assert work_item.command_manifest[3]["run"] == (
                "python3 npu/eval/extract_openroad_timing_summary.py "
                "--design-dir runs/designs/npu_blocks/attention_score32_exact_finalizer_bank_control_l8_b1 "
                "--out runs/designs/npu_blocks/attention_score32_exact_finalizer_bank_control_l8_b1/timing_debug_report.md "
                "--max-paths 8"
            )
            assert work_item.command_manifest[20]["run"] == (
                "export PATH=/oss-cad-suite/bin:$PATH && "
                "python3 npu/rtlgen/gen_attention_score32_exact_finalizer_bank_control.py "
                "--config runs/designs/npu_blocks/attention_score32_exact_finalizer_bank_control_l8_b59/config.json "
                "--out runs/designs/npu_blocks/attention_score32_exact_finalizer_bank_control_l8_b59/verilog"
            )
            assert work_item.command_manifest[21]["run"] == (
                "python3 npu/eval/check_attention_score32_exact_finalizer_bank_control_guard.py "
                "--design-dir runs/designs/npu_blocks/attention_score32_exact_finalizer_bank_control_l8_b59 "
                "--config runs/designs/npu_blocks/attention_score32_exact_finalizer_bank_control_l8_b59/config.json "
                "--sweep runs/campaigns/npu/attention_score32_exact_finalizer_bank_control_v1/sweeps/"
                "nangate45_attention_score32_exact_finalizer_bank_control_lane8_firstpass.json"
            )
            assert work_item.command_manifest[22]["run"] == (
                "export PATH=/oss-cad-suite/bin:$PATH && "
                "python3 npu/synth/run_block_sweep.py "
                "--design_dir runs/designs/npu_blocks/attention_score32_exact_finalizer_bank_control_l8_b59 "
                "--platform nangate45 --top attention_score32_exact_finalizer_bank_control_l8_b59 "
                "--sweep runs/campaigns/npu/attention_score32_exact_finalizer_bank_control_v1/sweeps/"
                "nangate45_attention_score32_exact_finalizer_bank_control_lane8_firstpass.json "
                "--out_root runs/designs/npu_blocks --skip_existing"
            )
            assert work_item.command_manifest[23]["run"] == (
                "python3 npu/eval/extract_openroad_timing_summary.py "
                "--design-dir runs/designs/npu_blocks/attention_score32_exact_finalizer_bank_control_l8_b59 "
                "--out runs/designs/npu_blocks/attention_score32_exact_finalizer_bank_control_l8_b59/timing_debug_report.md "
                "--max-paths 8"
            )
            assert work_item.command_manifest[24]["run"] == "python3 scripts/build_runs_index.py"
            assert work_item.command_manifest[25]["run"] == "python3 scripts/validate_runs.py --skip_eval_queue"
            assert work_item.expected_outputs == [
                "runs/designs/npu_blocks/attention_score32_exact_finalizer_bank_control_l8_b1/metrics.csv",
                "runs/designs/npu_blocks/attention_score32_exact_finalizer_bank_control_l8_b1/timing_debug_report.md",
                "runs/designs/npu_blocks/attention_score32_exact_finalizer_bank_control_l8_b4/metrics.csv",
                "runs/designs/npu_blocks/attention_score32_exact_finalizer_bank_control_l8_b4/timing_debug_report.md",
                "runs/designs/npu_blocks/attention_score32_exact_finalizer_bank_control_l8_b8/metrics.csv",
                "runs/designs/npu_blocks/attention_score32_exact_finalizer_bank_control_l8_b8/timing_debug_report.md",
                "runs/designs/npu_blocks/attention_score32_exact_finalizer_bank_control_l8_b16/metrics.csv",
                "runs/designs/npu_blocks/attention_score32_exact_finalizer_bank_control_l8_b16/timing_debug_report.md",
                "runs/designs/npu_blocks/attention_score32_exact_finalizer_bank_control_l8_b32/metrics.csv",
                "runs/designs/npu_blocks/attention_score32_exact_finalizer_bank_control_l8_b32/timing_debug_report.md",
                "runs/designs/npu_blocks/attention_score32_exact_finalizer_bank_control_l8_b59/metrics.csv",
                "runs/designs/npu_blocks/attention_score32_exact_finalizer_bank_control_l8_b59/timing_debug_report.md",
            ]
            dev_loop = work_item.task_request.request_payload["developer_loop"]
            assert dev_loop["abstraction"] == {"layer": "architecture_block"}
            assert dev_loop["proposal_id"] == proposal_id
            assert dev_loop["proposal_path"] == proposal_path
            assert work_item.task_request.request_payload["handoff"]["pr_body_fields"]["queue_item_id"] == item_id


def test_generate_l1_sweep_task_emits_commands_for_each_integrated_block_config() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        config_path, sweep_path = _write_example_block_repo(
            repo_root,
            mode_compare=False,
            synth_hierarchical=1,
        )
        second_design_dir = repo_root / "runs" / "designs" / "npu_blocks" / "npu_fp16_cpp_nm2_sigmoidcmp"
        second_design_dir.mkdir(parents=True, exist_ok=True)
        second_config_path = second_design_dir / "config_nm2_sigmoid.json"
        second_config_path.write_text(
            json.dumps(
                {
                    "version": "0.1",
                    "top_name": "npu_top",
                    "mmio_addr_width": 12,
                    "compute": {
                        "enabled": True,
                        "gemm": {"mac_type": "fp16", "lanes": 1, "accum_width": 16, "num_modules": 2},
                        "vec": {"lanes": 1, "ops": ["add", "mul", "relu", "sigmoid"]},
                    },
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        second_config_rel = str(second_config_path.relative_to(repo_root))
        source_commit = _init_git_repo(repo_root)
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            result = generate_l1_sweep_task(
                session,
                _make_l1_request(
                    repo_root=str(repo_root),
                    sweep_path=sweep_path,
                    config_paths=[config_path, second_config_rel],
                    platform="nangate45",
                    out_root="runs/designs/npu_blocks",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="architecture_block",
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            assert [command["name"] for command in work_item.command_manifest] == [
                "build_generator",
                "generate_block_rtl_npu_fp16_cpp_nm1_sigmoidcmp",
                "run_block_sweep_npu_fp16_cpp_nm1_sigmoidcmp",
                "generate_block_rtl_npu_fp16_cpp_nm2_sigmoidcmp",
                "run_block_sweep_npu_fp16_cpp_nm2_sigmoidcmp",
                "build_runs_index",
                "validate",
            ]
            joined_commands = "\n".join(command["run"] for command in work_item.command_manifest)
            assert "--config runs/designs/npu_blocks/npu_fp16_cpp_nm1_sigmoidcmp/config_nm1_sigmoid.json " in joined_commands
            assert "--config runs/designs/npu_blocks/npu_fp16_cpp_nm2_sigmoidcmp/config_nm2_sigmoid.json " in joined_commands
            assert "--design_dir runs/designs/npu_blocks/npu_fp16_cpp_nm1_sigmoidcmp " in joined_commands
            assert "--design_dir runs/designs/npu_blocks/npu_fp16_cpp_nm2_sigmoidcmp " in joined_commands
            assert joined_commands.count("--out_root runs/designs/npu_blocks ") == 2
            assert work_item.expected_outputs == [
                "runs/designs/npu_blocks/npu_fp16_cpp_nm1_sigmoidcmp/metrics.csv",
                "runs/designs/npu_blocks/npu_fp16_cpp_nm2_sigmoidcmp/metrics.csv",
            ]


def test_generate_l1_sweep_task_rejects_flattened_architecture_block_sweeps() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        config_path, sweep_path = _write_example_block_repo(repo_root)
        source_commit = _init_git_repo(repo_root)
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            try:
                generate_l1_sweep_task(
                    session,
                    _make_l1_request(
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
        source_commit = _init_git_repo(repo_root)
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            result = generate_l1_sweep_task(
                session,
                _make_l1_request(
                    repo_root=str(repo_root),
                    sweep_path=sweep_path,
                    config_paths=[config_path],
                    platform="nangate45",
                    out_root="runs/designs/npu_blocks",
                    requested_by="@tester",
                    source_commit=source_commit,
                    proposal_id="prop_l1_npu_nm1_sigmoid_vec_enable_v1",
                    proposal_path="docs/developer_loop/prop_l1_npu_nm1_sigmoid_vec_enable_v1/proposal.json",
                    make_target="1_1_yosys_canonicalize",
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            assert "--make_target 1_1_yosys_canonicalize" in work_item.command_manifest[2]["run"]
            assert work_item.expected_outputs == [
                "runs/designs/npu_blocks/npu_fp16_cpp_nm1_sigmoidcmp/metrics.csv",
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
        source_commit = _init_git_repo(repo_root)
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            result = generate_l1_sweep_task(
                session,
                _make_l1_request(
                    repo_root=str(repo_root),
                    sweep_path=sweep_path,
                    config_paths=[config_path],
                    platform="nangate45",
                    out_root="runs/designs/npu_blocks",
                    requested_by="@tester",
                    source_commit=source_commit,
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
        source_commit = _init_git_repo(repo_root)
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with patch("control_plane.services.l1_task_generator._resolve_source_commit", return_value="deadbeefcafefeed") as mock_resolve:
            with patch(
                "control_plane.services.l1_task_generator.build_generation_source_identity",
                return_value={
                    "version": 1,
                    "declared_source_commit": "deadbeefcafefeed",
                    "repo_head_sha": "deadbeefcafefeed",
                    "relation": "exact",
                    "proof": "generator_worktree_head_exact",
                    "clean": True,
                },
            ) as mock_identity:
                with Session(engine) as session:
                    result = generate_l1_sweep_task(
                        session,
                        _make_l1_request(
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
                    mock_resolve.assert_called_once()
                    mock_identity.assert_called_once()


def test_generate_l1_sweep_task_accepts_explicit_hierarchical_architecture_block_sweeps() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        config_path, sweep_path = _write_example_block_repo(repo_root, mode_compare=False, synth_hierarchical=1)
        source_commit = _init_git_repo(repo_root)
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            result = generate_l1_sweep_task(
                session,
                _make_l1_request(
                    repo_root=str(repo_root),
                    sweep_path=sweep_path,
                    config_paths=[config_path],
                    platform="nangate45",
                    out_root="runs/designs/npu_blocks",
                    requested_by="@tester",
                    source_commit=source_commit,
                    proposal_id="prop_l1_npu_nm1_sigmoid_vec_enable_v1",
                    proposal_path="docs/developer_loop/prop_l1_npu_nm1_sigmoid_vec_enable_v1",
                    abstraction_layer="architecture_block",
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            assert result.status == "applied"
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {"layer": "architecture_block"}


def test_generate_l1_sweep_task_rejects_disabled_hierarchy_in_explicit_param_sets() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        config_path, sweep_path = _write_example_block_repo(repo_root, mode_compare=False)
        sweep_file = repo_root / sweep_path
        sweep_file.write_text(
            json.dumps(
                {
                    "flow_param_sets": [
                        {
                            "CLOCK_PERIOD": 10.0,
                            "DIE_AREA": "0 0 1500 1500",
                            "CORE_AREA": "50 50 1450 1450",
                            "SYNTH_HIERARCHICAL": 0,
                        }
                    ],
                    "tag_prefix": "npu_fp16_nm1_sigmoidcmp",
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        _init_git_repo(repo_root)
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            try:
                generate_l1_sweep_task(
                    session,
                    _make_l1_request(
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
                assert "architecture_block sweeps must keep hierarchy" in str(exc)
            else:
                raise AssertionError("expected Layer1TaskGenerationError for disabled hierarchy")


def test_generate_l1_sweep_task_rejects_invalid_explicit_source_commit() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        config_path, sweep_path = _write_example_repo(repo_root)
        _init_git_repo(repo_root)
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            try:
                generate_l1_sweep_task(
                    session,
                    _make_l1_request(
                        repo_root=str(repo_root),
                        sweep_path=sweep_path,
                        config_paths=[config_path],
                        platform="nangate45",
                        out_root="runs/designs/activations",
                        requested_by="@tester",
                        source_commit="badbadbad",
                    ),
                )
            except Layer1TaskGenerationError as exc:
                assert "provided source_commit does not resolve to a commit" in str(exc)
            else:
                raise AssertionError("expected Layer1TaskGenerationError")


def test_generate_l1_sweep_task_rejects_source_commit_not_pushed_to_origin() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        config_path, sweep_path = _write_example_repo(repo_root)
        _init_git_repo(repo_root)
        extra = repo_root / "LOCAL_ONLY.txt"
        extra.write_text("local only\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(repo_root), "add", "LOCAL_ONLY.txt"], check=True, capture_output=True, text=True)
        subprocess.run(["git", "-C", str(repo_root), "commit", "-m", "local only"], check=True, capture_output=True, text=True)
        local_only_commit = subprocess.run(["git", "-C", str(repo_root), "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            try:
                generate_l1_sweep_task(
                    session,
                    _make_l1_request(
                        repo_root=str(repo_root),
                        sweep_path=sweep_path,
                        config_paths=[config_path],
                        platform="nangate45",
                        out_root="runs/designs/activations",
                        requested_by="@tester",
                        source_commit=local_only_commit,
                    ),
                )
            except Layer1TaskGenerationError as exc:
                assert "not reachable from origin" in str(exc)
            else:
                raise AssertionError("expected Layer1TaskGenerationError")


def test_generate_l1_sweep_task_rejects_implicit_source_commit_when_head_not_pushed_to_origin() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        config_path, sweep_path = _write_example_repo(repo_root)
        _init_git_repo(repo_root)
        extra = repo_root / "LOCAL_ONLY.txt"
        extra.write_text("local only\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(repo_root), "add", "LOCAL_ONLY.txt"], check=True, capture_output=True, text=True)
        subprocess.run(["git", "-C", str(repo_root), "commit", "-m", "local only"], check=True, capture_output=True, text=True)
        local_only_commit = subprocess.run(["git", "-C", str(repo_root), "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            try:
                generate_l1_sweep_task(
                    session,
                    _make_l1_request(
                        repo_root=str(repo_root),
                        sweep_path=sweep_path,
                        config_paths=[config_path],
                        platform="nangate45",
                        out_root="runs/designs/activations",
                        requested_by="@tester",
                    ),
                )
            except Layer1TaskGenerationError as exc:
                message = str(exc)
                assert "resolved repo HEAD source_commit is not reachable from origin" in message
                assert local_only_commit in message
            else:
                raise AssertionError("expected Layer1TaskGenerationError")


def test_generate_l1_sweep_task_accepts_implicit_source_commit_from_pushed_head() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        config_path, sweep_path = _write_example_repo(repo_root)
        source_commit = _init_git_repo(repo_root)
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            result = generate_l1_sweep_task(
                session,
                _make_l1_request(
                    repo_root=str(repo_root),
                    sweep_path=sweep_path,
                    config_paths=[config_path],
                    platform="nangate45",
                    out_root="runs/designs/activations",
                    requested_by="@tester",
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            assert result.status == "applied"
            assert work_item.source_commit == source_commit
            assert work_item.task_request.source_commit == source_commit
            assert work_item.task_request.request_payload["generation_source_identity"] == {
                "version": 1,
                "declared_source_commit": source_commit,
                "repo_head_sha": source_commit,
                "relation": "exact",
                "proof": "generator_worktree_head_exact",
                "clean": True,
            }
