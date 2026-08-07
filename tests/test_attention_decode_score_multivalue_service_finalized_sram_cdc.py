import json
from pathlib import Path
import shutil
import subprocess

import pytest

from npu.eval.probe_attention_decode_score_multivalue_service_finalized_cdc import (
    _config,
    build_report,
)
from npu.rtlgen.gen_attention_decode_score_multivalue_service_finalized_cdc import (
    generate,
)


def _tool(name: str) -> str:
    path = shutil.which(name)
    if path:
        return path
    fallback = Path("/oss-cad-suite/bin") / name
    if fallback.exists():
        return str(fallback)
    pytest.skip(f"{name} unavailable")


def _sram_config() -> dict:
    return _config(
        "attention_decode_score_multivalue_service_finalized_sram_cdc_c1",
        divider_lanes=8,
        temporal_state_backend="sram",
        service_value_memory_backend="macro_banked_4x16x64x32",
    )


def test_sram_backend_rtl_macro_manifest_and_lint(tmp_path: Path) -> None:
    config = _sram_config()
    generate(config, tmp_path)
    manifest = json.loads(
        (
            tmp_path
            / "attention_decode_score_multivalue_service_finalized_cdc_manifest.json"
        ).read_text(encoding="utf-8")
    )
    macros = json.loads((tmp_path / "macro_manifest.json").read_text(encoding="utf-8"))
    rtl = (tmp_path / "top.v").read_text(encoding="utf-8")
    counts = macros["manifest_params"]

    assert config[
        "attention_decode_score_multivalue_service_finalized_cdc"
    ]["temporal_state_backend"] == "sram"
    assert manifest["temporal_state_backend"] == "sram"
    assert manifest["submodule_manifests"]["service_temporal_cdc"][
        "temporal_state_backend"
    ] == "sram"
    assert counts["service_macro_count"] == 120
    assert counts["temporal_state_macro_count"] == 104
    assert counts["total_macro_count"] == 224
    assert macros["blackboxes"] == ["fakeram45_2048x39", "fakeram45_64x32"]
    assert macros["additional_lefs"] == [
        "/orfs/flow/platforms/nangate45/lef/fakeram45_2048x39.lef",
        "/orfs/flow/platforms/nangate45/lef/fakeram45_64x32.lef",
    ]
    assert macros["additional_libs"] == [
        "/orfs/flow/platforms/nangate45/lib/fakeram45_2048x39.lib",
        "/orfs/flow/platforms/nangate45/lib/fakeram45_64x32.lib",
    ]
    assert "fakeram45_64x32 u_state_mem" in rtl
    assert "state_global_max_q [0:STATE_SLOTS-1]" not in rtl
    assert "temporal_state_memory_request_count" in rtl

    lint = subprocess.run(
        [
            _tool("verilator"),
            "--lint-only",
            "-Wno-WIDTHEXPAND",
            "-Wno-WIDTHTRUNC",
            "-Wno-UNUSEDSIGNAL",
            "-Wno-UNDRIVEN",
            "-Wno-TIMESCALEMOD",
            "-Wno-SIDEEFFECT",
            "-Wno-LATCH",
            "-Wno-UNOPTFLAT",
            "-Wno-PINMISSING",
            "--top-module",
            str(config["top_name"]),
            str(tmp_path / "top.v"),
            "npu/rtl/fakeram45_2048x39_blackbox.v",
            "npu/rtl/fakeram45_64x32_blackbox.v",
        ],
        capture_output=True,
        text=True,
        timeout=240,
    )
    assert lint.returncode == 0, lint.stderr


def test_real_c1_sram_backend_finalized_equivalence() -> None:
    if not (shutil.which("iverilog") and shutil.which("vvp")):
        pytest.skip("iverilog/vvp unavailable")

    report = build_report(
        service_period_ns=10.0,
        temporal_period_ns=7.0,
        divider_lanes=8,
        temporal_state_backend="sram",
        service_value_memory_backend="macro_banked_4x16x64x32",
    )

    assert report["passed"] is True
    assert report["observed_rows"] == report["expected_rows"]
    assert len(report["observed_rows"]) == 16
    assert report["summary"]["stable"] == 1
    assert report["summary"]["state_requests"] == 64
    assert report["summary"]["state_reads"] == 32
    assert report["summary"]["state_responses"] == 32
    assert report["summary"]["state_writes"] == 32
    assert report["summary"]["state_error"] == 0
    assert report["summary"]["protocol_error"] == 0
    assert report["macro_manifest"]["manifest_params"]["total_macro_count"] == 224
