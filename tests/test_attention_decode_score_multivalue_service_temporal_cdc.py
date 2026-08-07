import json
from pathlib import Path
import shutil
import subprocess

import pytest

from npu.rtlgen.gen_attention_decode_score_multivalue_service_temporal_cdc import (
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


def _config(*, cdc_depth: int = 4, result_mode: str = "exact_partial") -> dict:
    return {
        "top_name": "attention_decode_score_multivalue_service_temporal_cdc_c1",
        "attention_decode_score_multivalue_service_temporal_cdc": {
            "cdc_fifo_depth": cdc_depth,
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


@pytest.mark.parametrize("depth", [4, 8, 16])
def test_generator_manifest_and_lint(depth: int, tmp_path: Path) -> None:
    config = _config(cdc_depth=depth)
    generate(config, tmp_path)
    manifest = json.loads(
        (
            tmp_path
            / "attention_decode_score_multivalue_service_temporal_cdc_manifest.json"
        ).read_text(encoding="utf-8")
    )
    rtl = (tmp_path / "top.v").read_text(encoding="utf-8")

    assert manifest["result_mode"] == "exact_partial"
    assert manifest["cdc_contract"]["fifo_depth"] == depth
    assert manifest["cdc_contract"]["payload_bits"] == 464
    assert manifest["cdc_contract"]["synchronizers"] == (
        "two_flip_flop_gray_each_direction"
    )
    assert manifest["metadata_contract"]["release"] == (
        "terminal_service_beat_accepted_into_async_fifo"
    )
    assert manifest["remaining_abstractions"] == [
        "downstream_full_context_final_normalizer",
        "persistent_state_sram_physical_mapping",
        "metastability_mtbf_and_library_cell_implementation",
        "physical_ppa",
    ]
    assert '(* ASYNC_REG = "TRUE" *)' in rtl
    assert "reg [463:0] mem [0:DEPTH-1]" in rtl
    assert "mem[wr_bin_q[ADDR_W-1:0]] <= wr_data;" in rtl
    assert "service_to_cdc_fire_w && service_shared_result_last" in rtl
    assert "selected_service_command_id_w != service_shared_result_command_id" in rtl

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


def test_invalid_modes_and_depths_are_rejected(tmp_path: Path) -> None:
    with pytest.raises(SystemExit, match="exact_partial"):
        generate(_config(result_mode="normalized"), tmp_path)
    with pytest.raises(SystemExit, match="4, 8, or 16"):
        generate(_config(cdc_depth=2), tmp_path)
