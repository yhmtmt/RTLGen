import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.eval.probe_attention_score32_exact_local_temporal_reducer import build_report
from npu.rtlgen.gen_attention_score32_exact_local_temporal_reducer import generate


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
        / f"attention_score32_exact_local_temporal_reducer_p{producers}_w8"
        / "config.json"
    )


def _load_config(producers: int) -> dict[str, object]:
    return json.loads(_config_path(producers).read_text(encoding="utf-8"))


@pytest.mark.skipif(not _rtl_tools_available(), reason="RTL tools unavailable")
def test_local_temporal_reducer_manifest_and_verilator_lint_p53(tmp_path: Path) -> None:
    config = _load_config(53)
    generate(config, tmp_path / "rtl")

    manifest = json.loads(
        (tmp_path / "rtl" / "attention_score32_exact_local_temporal_reducer_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    assert manifest["producers"] == 53
    assert manifest["persistent_waves"] == 8
    assert manifest["partial_payload_bits_per_beat"] == 328
    assert manifest["comparison_baseline_contract"] == "python_structured_local_temporal_exact_partial_reference"
    assert manifest["remaining_abstractions"] == [
        "producer_fan_in_wiring_open",
        "noc_sram_ppa_open",
        "global_c16_exact_reduction_open",
    ]
    assert manifest["checked_in_probe_defaults"] == {"heads": 2, "command_count": 2, "seed": 23}
    assert manifest["submodule_manifests"]["local_reducer"]["producers"] == 53
    assert manifest["submodule_manifests"]["temporal_merge"]["result_interface"] == (
        "ready_valid_exact_partial_slice_stream"
    )

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


def test_local_temporal_reducer_rejects_invalid_producer_count(tmp_path: Path) -> None:
    config = _load_config(53)
    config["attention_score32_exact_local_temporal_reducer"]["producers"] = 52
    with pytest.raises(SystemExit, match="producers must be exactly 53 or 54"):
        generate(config, tmp_path / "rtl")


@pytest.mark.skipif(not _rtl_tools_available(), reason="RTL tools unavailable")
def test_local_temporal_reducer_probe_matches_reference_p53_ideal() -> None:
    report = build_report(config=_load_config(53))

    assert report["passed"] is True
    assert report["interface_mode"] == "ideal"
    assert report["producers"] == 53
    assert report["commands"] == 2
    assert report["persistent_waves"] == 8
    assert report["outputs"] == 32
    assert report["expected_outputs"] == 32
    assert report["local_root_completed_count"] == 256
    assert report["temporal_merge_completed_count"] == 224
    assert report["emitted_beat_count"] == 32
    assert report["completed_command_count"] == 2
    assert report["protocol_error"] is False
    assert report["local_tree_protocol_error"] is False
    assert report["temporal_merge_protocol_error"] is False
    assert report["source_links"]["proposal_id"] == "prop_l1_decoder_attention_score32_local_temporal_reducer_v1"
    assert report["source_links"]["proposal_path"].endswith("/proposal.json")
    assert report["observed_rows"] == report["expected_rows"]


@pytest.mark.skipif(not _rtl_tools_available(), reason="RTL tools unavailable")
def test_local_temporal_reducer_probe_matches_reference_p53_stress() -> None:
    report = build_report(config=_load_config(53), stress_interfaces=True)

    assert report["passed"] is True
    assert report["interface_mode"] == "stress"
    assert report["outputs"] == 32
    assert report["expected_outputs"] == 32
    assert report["completed_command_count"] == 2
    assert report["protocol_error"] is False
    assert report["local_tree_protocol_error"] is False
    assert report["temporal_merge_protocol_error"] is False
    assert report["output_stall_cycles"] > 0
    assert report["observed_rows"] == report["expected_rows"]


@pytest.mark.skipif(not _rtl_tools_available(), reason="RTL tools unavailable")
def test_local_temporal_reducer_probe_matches_reference_p54_ideal() -> None:
    report = build_report(config=_load_config(54))

    assert report["passed"] is True
    assert report["producers"] == 54
    assert report["commands"] == 2
    assert report["outputs"] == 32
    assert report["expected_outputs"] == 32
    assert report["local_root_completed_count"] == 256
    assert report["temporal_merge_completed_count"] == 224
    assert report["emitted_beat_count"] == 32
    assert report["completed_command_count"] == 2
    assert report["protocol_error"] is False
    assert report["observed_rows"] == report["expected_rows"]
