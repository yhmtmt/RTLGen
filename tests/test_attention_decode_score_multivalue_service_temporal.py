import json
from pathlib import Path
import shutil
import subprocess

import pytest

from npu.rtlgen.gen_attention_decode_score_multivalue_service_temporal import generate


def _tool(name: str) -> str:
    path = shutil.which(name)
    if path:
        return path
    fallback = Path("/oss-cad-suite/bin") / name
    if fallback.exists():
        return str(fallback)
    pytest.skip(f"{name} unavailable")


def _config(*, result_mode: str = "exact_partial") -> dict:
    return {
        "top_name": "attention_decode_score_multivalue_service_temporal_c2",
        "attention_decode_score_multivalue_service_temporal": {
            "service": {
                "cluster_count": 2,
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


def test_service_temporal_generator_manifest_ports_and_lint(tmp_path: Path) -> None:
    config = _config()
    generate(config, tmp_path)

    manifest = json.loads(
        (tmp_path / "attention_decode_score_multivalue_service_temporal_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    rtl = (tmp_path / "top.v").read_text(encoding="utf-8")

    assert manifest["semantic_profile"] == (
        "decode_score_multivalue_service_temporal_exact_partial_same_clock_v1"
    )
    assert manifest["clocking_contract"] == "same_clock_only"
    assert manifest["result_mode"] == "exact_partial"
    assert manifest["external_command_metadata"]["sequence_id_bits"] == 16
    assert manifest["external_command_metadata"]["logical_command_id_bits"] == 16
    assert manifest["external_command_metadata"]["window_index_bits"] == 14
    assert manifest["external_command_metadata"]["window_count_bits"] == 15
    assert manifest["remaining_abstractions"] == [
        "clock_domain_crossing",
        "downstream_full_context_final_normalizer",
        "persistent_state_sram_physical_mapping",
        "physical_ppa",
    ]
    assert (
        manifest["submodule_manifests"]["service"]["result_mode"] == "exact_partial"
    )
    assert (
        manifest["submodule_manifests"]["temporal_stream"]["semantic_profile"]
        == "score32_exact_partial_temporal_stream_v1"
    )

    assert "input  wire [31:0] cluster_logical_sequence_id" in rtl
    assert "input  wire [31:0] cluster_logical_command_id" in rtl
    assert "input  wire [27:0] cluster_window_index" in rtl
    assert "input  wire [29:0] cluster_window_count" in rtl
    assert "wire [CLUSTERS-1:0] command_open_w = ~metadata_valid_q" in rtl
    assert "metadata_valid_q[service_shared_result_cluster] <= 1'b0;" in rtl
    assert ".in_sequence_id(selected_sequence_id_w)" in rtl
    assert ".in_command_id(selected_logical_command_id_w)" in rtl

    result = subprocess.run(
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
            str(Path("npu/rtl/fakeram45_2048x39_blackbox.v")),
        ],
        capture_output=True,
        text=True,
        timeout=240,
    )
    assert result.returncode == 0, result.stderr


def test_service_temporal_rejects_non_exact_partial(tmp_path: Path) -> None:
    with pytest.raises(SystemExit, match="exact_partial"):
        generate(_config(result_mode="normalized"), tmp_path)
