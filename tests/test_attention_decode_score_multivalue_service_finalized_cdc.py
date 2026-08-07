import json
from pathlib import Path
import shutil
import subprocess

import pytest

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


def _config(*, divider_lanes: int = 8, result_mode: str = "exact_partial") -> dict:
    return {
        "top_name": "attention_decode_score_multivalue_service_finalized_cdc_c1",
        "attention_decode_score_multivalue_service_finalized_cdc": {
            "cdc_fifo_depth": 4,
            "divider_lanes": divider_lanes,
            "service": {
                "cluster_count": 1,
                "max_blocks": 16,
                "packet_w": 128,
                "banks": 2,
                "req_queue_depth": 2,
                "resp_queue_depth": 2,
                "bank_queue_depth": 2,
                "read_latency": 1,
                "arb_mode": "round_robin",
                "locality_burst_max": 2,
                "score_scale_lanes_per_cycle": 1,
                "result_mode": result_mode,
                "head_id_bits": 5,
                "value_memory_backend": "behavioral",
            },
            "temporal_stream": {
                "fifo_depth": 4,
                "exp_scale_impl": "factored_h33_l64_mul_exact",
                "keep_hierarchy": True,
            },
        },
    }


@pytest.mark.parametrize("divider_lanes", [1, 2, 4, 8])
def test_generator_manifest_latency_and_lint(
    divider_lanes: int,
    tmp_path: Path,
) -> None:
    config = _config(divider_lanes=divider_lanes)
    generate(config, tmp_path)
    manifest = json.loads(
        (
            tmp_path
            / "attention_decode_score_multivalue_service_finalized_cdc_manifest.json"
        ).read_text(encoding="utf-8")
    )
    rtl = (tmp_path / "top.v").read_text(encoding="utf-8")
    finalizer = manifest["submodule_manifests"]["root_finalizer"]

    assert manifest["divider_lanes"] == divider_lanes
    assert manifest["full_context_normalization_embodied"] is True
    assert manifest["output_interface"]["value_bits"] == 320
    assert manifest["finalizer_metadata_hold"]["capture"] == (
        "exactly_on_finalizer_input_handshake"
    )
    assert manifest["remaining_abstractions"] == [
        "persistent_state_sram_physical_mapping",
        "synchronizer_metastability_mtbf_and_library_cells",
        "external_hbm_dram",
        "physical_ppa",
    ]
    assert finalizer["divider_cycles_per_beat"] == (8 // divider_lanes) * 57
    assert finalizer["accept_interval_cycles_per_beat"] == (
        (8 // divider_lanes) * 57
    ) + 2
    assert "if (finalizer_input_fire_w)" in rtl
    assert "if (finalizer_output_fire_w)" in rtl
    assert "finalizer_out_slice_w != metadata_slice_q" in rtl

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
            str(Path("npu/rtl/fakeram45_2048x39_blackbox.v")),
        ],
        capture_output=True,
        text=True,
        timeout=240,
    )
    assert lint.returncode == 0, lint.stderr


def test_invalid_result_mode_and_divider_lanes_are_rejected(tmp_path: Path) -> None:
    with pytest.raises(SystemExit, match="exact_partial"):
        generate(_config(result_mode="normalized"), tmp_path)
    with pytest.raises(SystemExit, match="divider_lanes"):
        generate(_config(divider_lanes=3), tmp_path)
