from pathlib import Path

from npu.eval.probe_decoder_producer_synth_boundary import (
    REPO_ROOT,
    find_infeasible_match,
    load_infeasible_registry,
    load_json,
    portable_metrics_row,
    probe_config,
)


REGISTRY = REPO_ROOT / "runs/knowledge/infeasible_designs.json"
NM2_CONFIG = REPO_ROOT / "runs/designs/npu_blocks/npu_fp16_cpp_nm2_producer/config_nm2_producer.json"


def test_infeasible_registry_matches_exact_known_timeout() -> None:
    registry = load_infeasible_registry(REGISTRY)
    config = load_json(NM2_CONFIG)

    match = find_infeasible_match(
        registry,
        config_path=NM2_CONFIG,
        config=config,
        platform="nangate45",
        top="npu_top",
        make_target="1_2_yosys",
    )

    assert match is None


def test_infeasible_registry_does_not_match_diagnostic_top_or_target() -> None:
    registry = load_infeasible_registry(REGISTRY)
    config = load_json(NM2_CONFIG)

    assert (
        find_infeasible_match(
            registry,
            config_path=NM2_CONFIG,
            config=config,
            platform="nangate45",
            top="gemm_compute_array",
            make_target="1_2_yosys",
        )
        is None
    )
    assert (
        find_infeasible_match(
            registry,
            config_path=NM2_CONFIG,
            config=config,
            platform="nangate45",
            top="npu_top",
            make_target="2_1_floorplan",
        )
        is None
    )


def test_probe_config_skips_known_infeasible_without_synth(tmp_path: Path) -> None:
    registry = [
        {
            "id": "test_infeasible",
            "reason": "test",
            "source_evidence": {
                "item_id": "l2_decoder_output_projection_producer_synth_boundary_v1_r2"
            },
            "match": {
                "config": "runs/designs/npu_blocks/npu_fp16_cpp_nm2_producer/config_nm2_producer.json",
                "platform": "nangate45",
                "top": "npu_top",
                "make_target": "1_2_yosys",
                "num_modules": 2,
            },
        }
    ]

    row = probe_config(
        NM2_CONFIG,
        sweep=REPO_ROOT / "runs/campaigns/npu/output_projection_producer_scale/sweeps/nangate45_synth_boundary.json",
        platform="nangate45",
        top="npu_top",
        make_target="1_2_yosys",
        out_root=tmp_path,
        timeout_seconds=1,
        stall_timeout_seconds=1,
        log_dir=tmp_path,
        infeasible_registry=registry,
    )

    assert row["status"] == "known_infeasible"
    assert row["synthesis"]["elapsed_seconds"] == 0.0
    assert row["known_infeasible"]["source_evidence"]["item_id"] == (
        "l2_decoder_output_projection_producer_synth_boundary_v1_r2"
    )


def test_infeasible_registry_matches_when_required_source_text_exists(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "npu/rtlgen/gen.py"
    source.parent.mkdir(parents=True)
    source.write_text("reg [65535:0] event_state;\n", encoding="utf-8")
    monkeypatch.setattr("npu.eval.probe_decoder_producer_synth_boundary.REPO_ROOT", tmp_path)

    registry = [
        {
            "id": "old_event_state_timeout",
            "match": {
                "config": "runs/designs/npu_blocks/npu_fp16_cpp_nm2_producer/config_nm2_producer.json",
                "platform": "nangate45",
                "top": "npu_top",
                "make_target": "1_2_yosys",
                "num_modules": 2,
            },
            "requires_repo_text": [
                {
                    "path": "npu/rtlgen/gen.py",
                    "contains": "event_state",
                }
            ],
        }
    ]
    config = load_json(NM2_CONFIG)
    config_path = tmp_path / "runs/designs/npu_blocks/npu_fp16_cpp_nm2_producer/config_nm2_producer.json"

    match = find_infeasible_match(
        registry,
        config_path=config_path,
        config=config,
        platform="nangate45",
        top="npu_top",
        make_target="1_2_yosys",
    )

    assert match is not None


def test_portable_metrics_row_prefers_repo_relative_work_result_for_external_result_path() -> None:
    row = portable_metrics_row(
        {
            "status": "ok",
            "result_path": "/orfs/flow/results/nangate45/demo/1_2_yosys.v",
            "work_result_json": "runs/designs/npu_blocks/demo/work/abcd/result.json",
            "synth_script_path": "/orfs/flow/scripts/synth.tcl",
        }
    )

    assert row["result_path"] == "runs/designs/npu_blocks/demo/work/abcd/result.json"
    assert row["work_result_json"] == "runs/designs/npu_blocks/demo/work/abcd/result.json"
    assert row["synth_script_path"] == ""
