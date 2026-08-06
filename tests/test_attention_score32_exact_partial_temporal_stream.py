import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.eval.probe_attention_score32_exact_partial_temporal_stream import build_report
from npu.rtlgen.gen_attention_score32_exact_partial_temporal_stream import generate


def _config() -> dict[str, object]:
    path = (
        REPO_ROOT
        / "runs"
        / "designs"
        / "npu_blocks"
        / "attention_score32_exact_partial_temporal_stream_h32_f4"
        / "config.json"
    )
    return json.loads(path.read_text(encoding="utf-8"))


def _tool(name: str) -> str:
    path = shutil.which(name)
    if path:
        return path
    fallback = Path("/oss-cad-suite/bin") / name
    if fallback.exists():
        return str(fallback)
    pytest.skip(f"{name} unavailable")


def test_manifest_and_verilator_lint(tmp_path: Path) -> None:
    config = _config()
    generate(config, tmp_path)
    manifest = json.loads(
        (tmp_path / "attention_score32_exact_partial_temporal_stream_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    assert manifest["semantic_profile"] == "score32_exact_partial_temporal_stream_v1"
    assert manifest["max_window_count"] == 16384
    assert manifest["fifo_depth"] == 4
    assert manifest["fail_closed_protocol_error"] is True
    assert manifest["remaining_abstractions"] == [
        "upstream_service_command_metadata_binding",
        "service_to_temporal_reducer_clock_domain_crossing",
        "downstream_full_context_final_normalizer",
        "physical_sram_macro_mapping_for_persistent_state",
        "physical_ppa",
    ]
    assert manifest["submodule_manifests"]["pair_merge"]["exp_scale_impl"] == (
        "factored_h33_l64_mul_exact"
    )
    result = subprocess.run(
        [
            _tool("verilator"),
            "--lint-only",
            "-Wno-WIDTHEXPAND",
            "-Wno-WIDTHTRUNC",
            "--top-module",
            str(config["top_name"]),
            str(tmp_path / "top.v"),
        ],
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert result.returncode == 0, result.stderr


def test_ideal_stream_matches_reference() -> None:
    report = build_report(config=_config())
    assert report["passed"] is True
    assert report["observed_rows"] == report["expected_rows"]
    assert report["summary"]["input_accepted"] == 96
    assert report["summary"]["merge_completed"] == 64
    assert report["summary"]["emitted"] == 32
    assert report["summary"]["completed_heads"] == 2
    assert report["summary"]["protocol_error"] == 0


def test_fifo_and_output_pressure_preserve_exact_results() -> None:
    report = build_report(config=_config(), stress_interfaces=True)
    assert report["passed"] is True
    assert report["observed_rows"] == report["expected_rows"]
    assert report["summary"]["fifo_full_stalls"] > 0
    assert report["summary"]["output_stalls"] > 0
    assert report["summary"]["protocol_error"] == 0


def test_order_violation_fails_closed_without_output() -> None:
    report = build_report(config=_config(), order_violation=True)
    assert report["passed"] is True
    assert report["summary"]["protocol_error"] == 1
    assert report["summary"]["emitted"] == 0
    assert report["summary"]["completed_heads"] == 0


def test_invalid_fifo_depth_is_rejected(tmp_path: Path) -> None:
    config = _config()
    config["attention_score32_exact_partial_temporal_stream"]["fifo_depth"] = 3
    with pytest.raises(SystemExit, match="power of two"):
        generate(config, tmp_path)
