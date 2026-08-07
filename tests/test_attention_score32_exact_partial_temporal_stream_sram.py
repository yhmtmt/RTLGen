import json
from pathlib import Path
import shutil
import subprocess

import pytest

from npu.rtlgen.gen_attention_score32_exact_partial_temporal_stream_sram import (
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


def _config() -> dict:
    return {
        "top_name": "attention_score32_exact_partial_temporal_stream_sram",
        "attention_score32_exact_partial_temporal_stream_sram": {
            "heads": 32,
            "value_slices": 16,
            "head_id_bits": 5,
            "fifo_depth": 4,
            "exp_scale_impl": "factored_h33_l64_mul_exact",
            "keep_hierarchy": True,
        },
    }


def test_manifest_macro_mapping_and_lint(tmp_path: Path) -> None:
    config = _config()
    generate(config, tmp_path)
    manifest = json.loads(
        (
            tmp_path
            / "attention_score32_exact_partial_temporal_stream_sram_manifest.json"
        ).read_text(encoding="utf-8")
    )
    macros = json.loads((tmp_path / "macro_manifest.json").read_text(encoding="utf-8"))
    rtl = (tmp_path / "top.v").read_text(encoding="utf-8")

    assert manifest["logical_state"]["entries"] == 512
    assert manifest["logical_state"]["bits_per_entry"] == 394
    assert manifest["physical_state"]["banks"] == 8
    assert manifest["physical_state"]["macros_per_bank"] == 13
    assert manifest["physical_state"]["macro_count"] == 104
    assert manifest["physical_state"]["pad_bits"] == 22
    assert manifest["persistent_state_inferred_as_flops"] is False
    assert manifest["access_schedule"]["macro_read_response_latency_cycles"] == 1
    assert macros["blackboxes"] == ["fakeram45_64x32"]
    assert macros["manifest_params"]["macro_count"] == 104
    assert macros["additional_lefs"] == [
        "/orfs/flow/platforms/nangate45/lef/fakeram45_64x32.lef"
    ]
    assert macros["additional_libs"] == [
        "/orfs/flow/platforms/nangate45/lib/fakeram45_64x32.lib"
    ]
    assert "state_global_max_q [0:" not in rtl
    assert "fakeram45_64x32 u_state_mem" in rtl
    assert "for (bank_i = 0; bank_i < BANKS" in rtl
    assert "for (lane_i = 0; lane_i < LANES" in rtl

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
            "--top-module",
            str(config["top_name"]),
            str(tmp_path / "top.v"),
            "npu/rtl/fakeram45_64x32_blackbox.v",
        ],
        capture_output=True,
        text=True,
        timeout=240,
    )
    assert lint.returncode == 0, lint.stderr


def test_invalid_fifo_depth_rejected(tmp_path: Path) -> None:
    config = _config()
    config["attention_score32_exact_partial_temporal_stream_sram"]["fifo_depth"] = 3
    with pytest.raises(SystemExit, match="power of two"):
        generate(config, tmp_path)
