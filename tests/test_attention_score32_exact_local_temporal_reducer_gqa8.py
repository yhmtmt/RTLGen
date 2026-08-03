import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.eval.probe_attention_score32_exact_local_temporal_reducer_gqa8 import build_report
from npu.rtlgen.gen_attention_score32_exact_local_temporal_reducer_gqa8 import generate
from npu.rtlgen.gen_attention_score32_online_state_merge import (
    FACTORED_H33_L64_MUL_EXACT,
    LEGACY_MONOLITHIC_LUT_EXACT,
)


def _rtl_tools_available() -> bool:
    return bool(shutil.which("iverilog") and shutil.which("vvp") and shutil.which("verilator"))


def _tool(name: str) -> str:
    path = shutil.which(name)
    if path:
        return path
    fallback = Path("/oss-cad-suite/bin") / name
    if fallback.exists():
        return str(fallback)
    raise RuntimeError(f"required tool unavailable: {name}")


def _config_path(producers: int) -> Path:
    return (
        REPO_ROOT
        / "runs"
        / "designs"
        / "npu_blocks"
        / f"attention_score32_exact_local_temporal_reducer_gqa8_p{producers}_w8"
        / "config.json"
    )


def _load_config(producers: int) -> dict[str, object]:
    return json.loads(_config_path(producers).read_text(encoding="utf-8"))


@pytest.mark.skipif(not _rtl_tools_available(), reason="RTL tools unavailable")
def test_local_temporal_reducer_gqa8_manifest_and_verilator_lint_p53(tmp_path: Path) -> None:
    config = _load_config(53)
    generate(config, tmp_path / "rtl")

    manifest = json.loads(
        (tmp_path / "rtl" / "attention_score32_exact_local_temporal_reducer_gqa8_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    assert manifest["producers"] == 53
    assert manifest["persistent_waves"] == 8
    assert manifest["exp_scale_impl"] == LEGACY_MONOLITHIC_LUT_EXACT
    assert manifest["query_heads_per_group"] == 8
    assert manifest["partial_payload_bits_per_beat"] == 328
    assert (
        manifest["result_interface"]
        == "local_exact_partial_gqa8_group_streams_to_128_beat_aggregate_after_8_waves"
    )
    assert (
        manifest["command_schedule_contract"]
        == "producer_compatible_head_major_slice_minor_stream_grouped_by_exact_8_wave_windows"
    )
    assert (
        manifest["wave_terminal_contract"]
        == "advance_only_on_validated_head_lane7_slice15_after_128_beats"
    )
    assert manifest["comparison_baseline_contract"] == "python_structured_gqa8_local_temporal_exact_partial_reference"
    assert manifest["remaining_abstractions"] == [
        "producer_to_local_reducer_structural_fan_in_open",
        "noc_sram_ppa_open",
        "global_c16_exact_reduction_open",
    ]
    assert manifest["checked_in_probe_defaults"] == {
        "heads": 16,
        "command_count": 2,
        "head_bases": [0, 8],
        "seed": 23,
    }
    assert manifest["service_model"]["beats_per_wave"] == 128
    assert manifest["service_model"]["beats_per_output_group"] == 128
    assert manifest["service_model"]["query_head_groups"] == 2
    assert manifest["submodule_manifests"]["local_reducer"]["producers"] == 53
    assert manifest["submodule_manifests"]["local_reducer"]["exp_scale_impl"] == LEGACY_MONOLITHIC_LUT_EXACT
    assert (
        manifest["submodule_manifests"]["local_reducer"]["submodule_manifests"]["pair_merge"]["exp_scale_impl"]
        == LEGACY_MONOLITHIC_LUT_EXACT
    )
    assert manifest["submodule_manifests"]["temporal_merge"]["exp_scale_impl"] == LEGACY_MONOLITHIC_LUT_EXACT
    assert manifest["submodule_manifests"]["temporal_merge"]["result_interface"] == (
        "ready_valid_exact_partial_slice_stream"
    )
    rtl = (tmp_path / "rtl" / "top.v").read_text(encoding="utf-8")
    assert "case (bucket)" in rtl

    lint = subprocess.run(
        [
            _tool("verilator"),
            "--lint-only",
            "-Wno-WIDTHEXPAND",
            "-Wno-WIDTHTRUNC",
            "--top-module",
            str(config["top_name"]),
            str(tmp_path / "rtl" / "top.v"),
        ],
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert lint.returncode == 0, lint.stderr


@pytest.mark.skipif(not _rtl_tools_available(), reason="RTL tools unavailable")
def test_local_temporal_reducer_gqa8_factored_exp_scale_propagates_and_removes_monolithic_lut(tmp_path: Path) -> None:
    config = _load_config(53)
    config["attention_score32_exact_local_temporal_reducer_gqa8"]["exp_scale_impl"] = FACTORED_H33_L64_MUL_EXACT
    generate(config, tmp_path / "rtl")

    manifest = json.loads(
        (tmp_path / "rtl" / "attention_score32_exact_local_temporal_reducer_gqa8_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    assert manifest["exp_scale_impl"] == FACTORED_H33_L64_MUL_EXACT
    assert manifest["submodule_manifests"]["local_reducer"]["exp_scale_impl"] == FACTORED_H33_L64_MUL_EXACT
    assert (
        manifest["submodule_manifests"]["local_reducer"]["submodule_manifests"]["pair_merge"]["exp_scale_impl"]
        == FACTORED_H33_L64_MUL_EXACT
    )
    assert manifest["submodule_manifests"]["temporal_merge"]["exp_scale_impl"] == FACTORED_H33_L64_MUL_EXACT

    rtl = (tmp_path / "rtl" / "top.v").read_text(encoding="utf-8")
    assert "case (bucket)" not in rtl
    assert rtl.count("case (bucket_hi)") == 2
    assert rtl.count("case (bucket_lo)") == 2
    assert "33'd4096: exp_lut = 24'd" not in rtl


def test_local_temporal_reducer_gqa8_rejects_invalid_producer_count(tmp_path: Path) -> None:
    config = _load_config(53)
    config["attention_score32_exact_local_temporal_reducer_gqa8"]["producers"] = 52
    with pytest.raises(SystemExit, match="producers must be exactly 53 or 54"):
        generate(config, tmp_path / "rtl")


@pytest.mark.skipif(not _rtl_tools_available(), reason="RTL tools unavailable")
def test_local_temporal_reducer_gqa8_probe_matches_reference_p53_ideal() -> None:
    report = build_report(config=_load_config(53))

    assert report["passed"] is True
    assert report["interface_mode"] == "ideal"
    assert (
        report["input_stream_contract"]
        == "gqa8_head_major_slice_minor_wave_serialized_compatible_with_existing_dual_stream_producer"
    )
    assert report["producers"] == 53
    assert report["commands"] == 2
    assert report["heads"] == 16
    assert report["head_bases"] == [0, 8]
    assert report["persistent_waves"] == 8
    assert report["per_group_counts"] == {"local_roots": 1024, "temporal_merges": 896, "outputs": 128}
    assert report["outputs"] == 256
    assert report["expected_outputs"] == 256
    assert report["local_root_completed_count"] == 2048
    assert report["temporal_merge_completed_count"] == 1792
    assert report["emitted_beat_count"] == 256
    assert report["completed_command_count"] == 2
    assert report["protocol_error"] is False
    assert report["group_contract_error"] is False
    assert report["local_tree_protocol_error"] is False
    assert report["temporal_merge_protocol_error"] is False
    assert report["source_links"]["proposal_id"] == "prop_l1_decoder_attention_score32_local_temporal_reducer_gqa8_v1"
    assert report["source_links"]["proposal_path"].endswith("/proposal.json")
    assert report["observed_rows"] == report["expected_rows"]


@pytest.mark.skipif(not _rtl_tools_available(), reason="RTL tools unavailable")
def test_local_temporal_reducer_gqa8_probe_matches_reference_p53_stress() -> None:
    report = build_report(config=_load_config(53), stress_interfaces=True)

    assert report["passed"] is True
    assert report["interface_mode"] == "stress"
    assert report["outputs"] == 256
    assert report["expected_outputs"] == 256
    assert report["completed_command_count"] == 2
    assert report["protocol_error"] is False
    assert report["group_contract_error"] is False
    assert report["local_tree_protocol_error"] is False
    assert report["temporal_merge_protocol_error"] is False
    assert report["ready_pattern_period"] > 1
    assert report["output_stall_cycles"] > 0
    assert report["observed_rows"] == report["expected_rows"]


@pytest.mark.skipif(not _rtl_tools_available(), reason="RTL tools unavailable")
def test_local_temporal_reducer_gqa8_probe_matches_reference_p54_ideal() -> None:
    report = build_report(config=_load_config(54))

    assert report["passed"] is True
    assert report["producers"] == 54
    assert report["commands"] == 2
    assert report["head_bases"] == [0, 8]
    assert report["outputs"] == 256
    assert report["expected_outputs"] == 256
    assert report["local_root_completed_count"] == 2048
    assert report["temporal_merge_completed_count"] == 1792
    assert report["emitted_beat_count"] == 256
    assert report["completed_command_count"] == 2
    assert report["protocol_error"] is False
    assert report["group_contract_error"] is False
    assert report["observed_rows"] == report["expected_rows"]


@pytest.mark.skipif(not _rtl_tools_available(), reason="RTL tools unavailable")
def test_local_temporal_reducer_gqa8_probe_matches_reference_p53_factored_ideal() -> None:
    config = _load_config(53)
    config["attention_score32_exact_local_temporal_reducer_gqa8"]["exp_scale_impl"] = FACTORED_H33_L64_MUL_EXACT
    report = build_report(config=config)

    assert report["passed"] is True
    assert report["producers"] == 53
    assert report["outputs"] == 256
    assert report["expected_outputs"] == 256
    assert report["completed_command_count"] == 2
    assert report["protocol_error"] is False
    assert report["group_contract_error"] is False
    assert report["local_tree_protocol_error"] is False
    assert report["temporal_merge_protocol_error"] is False
    assert report["observed_rows"] == report["expected_rows"]
