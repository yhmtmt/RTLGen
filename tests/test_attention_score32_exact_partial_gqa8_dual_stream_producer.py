import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.eval.probe_attention_score32_exact_partial_gqa8_dual_stream_producer import build_report, compact_report
from npu.rtlgen.gen_attention_score32_exact_partial_gqa8_dual_stream_producer import generate

_FAKERAM_MODEL = """
module fakeram45_2048x39 (
    output wire [38:0] rd_out, input wire [10:0] addr_in,
    input wire we_in, input wire [38:0] wd_in, input wire [38:0] w_mask_in,
    input wire clk, input wire ce_in
);
  reg [38:0] mem [0:2047];
  reg [10:0] addr_q;
  reg [38:0] rd_out_q;
  integer idx;
  initial begin
    addr_q = 0;
    rd_out_q = 0;
    for (idx = 0; idx < 2048; idx = idx + 1) mem[idx] = 0;
  end
  always @(posedge clk) begin
    rd_out_q <= mem[addr_q];
    if (ce_in) begin
      if (we_in) begin
        for (idx = 0; idx < 39; idx = idx + 1) begin
          if (w_mask_in[idx]) mem[addr_in][idx] <= wd_in[idx];
        end
      end
      addr_q <= addr_in;
    end
  end
  assign rd_out = rd_out_q;
endmodule
"""


def test_compact_report_replaces_equivalence_rows_with_digests() -> None:
    rows = [{"command_id": 1, "head_id": 2, "value": [3, 4]}]
    report = compact_report({"passed": True, "observed_rows": rows, "expected_rows": rows})

    assert "observed_rows" not in report
    assert "expected_rows" not in report
    assert report["observed_rows_count"] == 1
    assert report["expected_rows_count"] == 1
    assert report["observed_rows_sha256"] == report["expected_rows_sha256"]
    assert report["equivalence_evidence_policy"] == "structured_compare_then_commit_counts_and_sha256"


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


def _config_path(name: str = "config.json") -> Path:
    return (
        REPO_ROOT
        / "runs"
        / "designs"
        / "npu_blocks"
        / "attention_score32_exact_partial_gqa8_dual_stream_producer_b8"
        / name
    )


def _load_config(name: str = "config.json") -> dict[str, object]:
    return json.loads(_config_path(name).read_text(encoding="utf-8"))


@pytest.mark.skipif(not _rtl_tools_available(), reason="RTL tools unavailable")
def test_exact_partial_gqa8_dual_stream_producer_manifest_and_verilator_lint(tmp_path: Path) -> None:
    config = _load_config()
    generate(config, tmp_path / "rtl")
    fakeram_path = tmp_path / "fakeram45_2048x39.sv"
    fakeram_path.write_text(_FAKERAM_MODEL, encoding="utf-8")

    manifest = json.loads(
        (tmp_path / "rtl" / "attention_score32_exact_partial_gqa8_dual_stream_producer_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    assert manifest["streams"] == 2
    assert manifest["query_heads_per_stream"] == 8
    assert manifest["token_lanes_per_head"] == 8
    assert manifest["structural_score_macs_per_cycle"] == 128
    assert manifest["max_blocks"] == 8
    assert manifest["value_slices"] == 16
    assert manifest["head_id_bits"] == 5
    assert manifest["producer_result_mode"] == "exact_partial"
    assert manifest["checked_in_probe_defaults"] == {
        "heads": 8,
        "command_count": 1,
        "blocks_per_stream": 2,
        "head_dim": 3,
    }
    assert manifest["service_model"]["producer_block_workload_assumptions"] == {
        "command_block_count_range": [1, 8],
        "probe_command_count": 1,
        "per_wave_local_block_ceiling_per_stream": 2,
        "persistent_local_reducer_waves": 8,
        "probe_blocks_per_stream": 2,
        "probe_block_counts_per_stream": [2],
        "probe_blocks_per_stream_uniform": True,
        "probe_head_dim": 3,
        "probe_head_bases": [0],
        "probe_total_heads": 8,
        "probe_token_streams": 2,
        "multiple_head_groups_run_in_order": True,
        "head_base_alignment_bits": 3,
        "global_tile_tokens": 1024,
        "global_tile_token_blocks": 128,
        "per_datapath_group_commands_per_wave": 4,
        "worst_loaded_total_blocks_per_stream_per_datapath_per_wave": 5,
        "worst_loaded_two_block_commands_per_datapath_per_wave": 1,
    }
    assert manifest["remaining_abstractions"] == [
        "53or54_way_global_cluster_aggregation_open",
        "8_wave_persistent_state_open",
        "noc_sram_ppa_open",
    ]
    assert manifest["submodule_manifests"]["gqa_group"]["result_mode"] == "exact_partial"
    assert manifest["submodule_manifests"]["gqa_group"]["result_value_bits_per_beat"] == 328
    assert (
        manifest["submodule_manifests"]["gqa_group"]["submodule_manifests"]["multivalue_cluster"]["result_mode"]
        == "exact_partial"
    )
    assert manifest["submodule_manifests"]["merge"]["result_interface"] == "ready_valid_exact_partial_slice_stream"

    lint = subprocess.run(
        [
            _tool("verilator"),
            "--lint-only",
            "-Wno-WIDTHEXPAND",
            "-Wno-WIDTHTRUNC",
            "--top-module",
            str(config["top_name"]),
            str(tmp_path / "rtl" / "top.v"),
            str(fakeram_path),
        ],
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert lint.returncode == 0, lint.stderr


def test_exact_partial_gqa8_dual_stream_producer_rejects_too_small_max_blocks(tmp_path: Path) -> None:
    config = _load_config()
    config["attention_score32_exact_partial_gqa8_dual_stream_producer"]["max_blocks"] = 4
    with pytest.raises(SystemExit, match="max_blocks must be a power of two in \\[8, 16384\\]"):
        generate(config, tmp_path / "rtl")


@pytest.mark.skipif(not _rtl_tools_available(), reason="RTL tools unavailable")
def test_exact_partial_gqa8_dual_stream_producer_small_probe_matches_reference() -> None:
    report = build_report(config=_load_config())

    assert report["passed"] is True
    assert report["outputs"] == 128
    assert report["expected_outputs"] == 128
    assert report["commands"] == 1
    assert report["command_accept_count"] == 1
    assert report["command_complete_count"] == 1
    assert report["stream_command_accept_count"] == [1, 1]
    assert report["stream_complete_count"] == [1, 1]
    assert report["merge_complete_count"] == 128
    assert report["integrated_drain_cycles"] == 438
    assert report["result_stall_cycles"] == 64
    assert report["protocol_error"] is False
    assert report["stream_protocol_error"] == [False, False]
    assert report["merge_protocol_error"] is False
    assert report["observed_rows"] == report["expected_rows"]


@pytest.mark.skipif(not _rtl_tools_available(), reason="RTL tools unavailable")
def test_exact_partial_gqa8_dual_stream_producer_backpressure_and_skew_stress() -> None:
    report = build_report(
        config=_load_config(),
        heads=8,
        output_ready_pattern=(True, False, True, False, True, True, False, True, True, False, True, True, False, True),
    )

    assert report["passed"] is True
    assert report["outputs"] == 128
    assert report["commands"] == 1
    assert report["integrated_drain_cycles"] == 445
    assert report["command_accept_count"] == 1
    assert report["command_complete_count"] == 1
    assert report["merge_complete_count"] == 128
    assert report["result_stall_cycles"] == 71
    assert report["protocol_error"] is False
    assert report["stream_protocol_error"] == [False, False]
    assert report["merge_protocol_error"] is False


@pytest.mark.skipif(not _rtl_tools_available(), reason="RTL tools unavailable")
def test_exact_partial_gqa8_dual_stream_producer_full_heads32_probe() -> None:
    report = build_report(config=_load_config("config_heads32_native.json"))

    assert report["passed"] is True
    assert report["outputs"] == 512
    assert report["expected_outputs"] == 512
    assert report["commands"] == 4
    assert report["command_accept_count"] == 4
    assert report["command_complete_count"] == 4
    assert report["stream_command_accept_count"] == [4, 4]
    assert report["stream_complete_count"] == [4, 4]
    assert report["merge_complete_count"] == 512
    assert report["integrated_drain_cycles"] == 1736
    assert report["result_stall_cycles"] == 255
    assert report["protocol_error"] is False
    assert report["stream_protocol_error"] == [False, False]
    assert report["merge_protocol_error"] is False
    assert report["observed_rows"] == report["expected_rows"]


@pytest.mark.skipif(not _rtl_tools_available(), reason="RTL tools unavailable")
def test_exact_partial_gqa8_dual_stream_producer_llama_wave_probe() -> None:
    report = build_report(config=_load_config("config_llama_wave.json"))

    assert report["passed"] is True
    assert report["heads"] == 32
    assert report["commands"] == 5
    assert report["blocks_per_stream"] == 1
    assert report["head_dim"] == 128
    assert report["head_bases"] == [0, 8, 16, 24, 0]
    assert report["outputs"] == 640
    assert report["expected_outputs"] == 640
    assert report["interface_mode"] == "ideal"
    assert report["integrated_drain_cycles"] == 1681
    assert report["command_accept_count"] == 5
    assert report["command_complete_count"] == 5
    assert report["stream_command_accept_count"] == [5, 5]
    assert report["stream_complete_count"] == [5, 5]
    assert report["merge_complete_count"] == 640
    assert report["result_stall_cycles"] == 0
    assert report["llama_wave_reference_cycles"] == 986
    assert report["llama_wave_drain_delta_vs_986"] == 695
    assert report["protocol_error"] is False
    assert report["stream_protocol_error"] == [False, False]
    assert report["merge_protocol_error"] is False
    assert report["observed_rows"] == report["expected_rows"]


@pytest.mark.skipif(not _rtl_tools_available(), reason="RTL tools unavailable")
def test_exact_partial_gqa8_dual_stream_producer_llama_wave_worst4_probe() -> None:
    report = build_report(config=_load_config("config_llama_wave_worst4_group_major.json"))

    assert report["passed"] is True
    assert report["heads"] == 32
    assert report["commands"] == 4
    assert report["blocks_per_stream"] == 2
    assert report["block_counts_per_stream"] == [2, 1, 1, 1]
    assert report["head_dim"] == 128
    assert report["head_bases"] == [0, 8, 16, 24]
    assert report["outputs"] == 512
    assert report["expected_outputs"] == 512
    assert report["interface_mode"] == "ideal"
    assert report["integrated_drain_cycles"] == 1536
    assert report["command_accept_count"] == 4
    assert report["command_complete_count"] == 4
    assert report["stream_command_accept_count"] == [4, 4]
    assert report["stream_complete_count"] == [4, 4]
    assert report["merge_complete_count"] == 512
    assert report["result_stall_cycles"] == 0
    assert report["llama_wave_reference_cycles"] == 986
    assert report["llama_wave_drain_delta_vs_986"] == 550
    assert report["protocol_error"] is False
    assert report["stream_protocol_error"] == [False, False]
    assert report["merge_protocol_error"] is False
    assert report["observed_rows"] == report["expected_rows"]
