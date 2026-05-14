from pathlib import Path

from npu.eval.probe_decoder_producer_synth_boundary import (
    REPO_ROOT,
    find_infeasible_match,
    load_infeasible_registry,
    load_json,
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

    assert match is not None
    assert match["id"] == "npu_fp16_nm2_producer_npu_top_yosys_timeout_20260513"


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
    registry = load_infeasible_registry(REGISTRY)

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
