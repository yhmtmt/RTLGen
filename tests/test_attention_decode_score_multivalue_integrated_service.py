import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import npu.eval.probe_attention_decode_score_multivalue_integrated_service as probe_module
from npu.eval.probe_attention_decode_score_multivalue_integrated_service import (
    COMPACT_REPORT_MAX_BYTES,
    COMPACT_REPORT_MAX_LINES,
    DEFAULT_CASES,
    REPORT_EXCLUSIONS,
    _workload_contract,
    _workload_expected_counts,
    _selected_scale_point,
    build_report,
    validate_report,
)
from npu.rtlgen.gen_attention_decode_score_multivalue_service import generate
from npu.sim.perf.attention_exact_partial import pack_numerators, partial_stream_from_blocks


def _iverilog_available() -> bool:
    return bool(shutil.which("iverilog") and shutil.which("vvp"))


_EXACT_RESULT_RE = re.compile(
    r"RESULT cmd=(\d+) head=(\d+) slice=(\d+) last=(\d+) max=(-?\d+) sum=(\d+) value=([0-9a-fA-F]+)"
)


def _case(
    *,
    case_id: str,
    cluster_count: int,
    packet_w: int,
    banks: int,
    arb_mode: str,
    locality_burst_max: int = 2,
    req_queue_depth: int = 2,
    resp_queue_depth: int = 2,
    bank_queue_depth: int = 2,
    read_latency: int = 2,
) -> dict:
    return {
        "case_id": case_id,
        "cluster_count": cluster_count,
        "packet_w": packet_w,
        "banks": banks,
        "req_queue_depth": req_queue_depth,
        "resp_queue_depth": resp_queue_depth,
        "bank_queue_depth": bank_queue_depth,
        "read_latency": read_latency,
        "arb_mode": arb_mode,
        "locality_burst_max": locality_burst_max,
    }


def test_multivalue_service_generator_manifest(tmp_path: Path) -> None:
    config = {
        "top_name": "attention_decode_score_multivalue_service_smoke",
        "attention_decode_score_multivalue_service": {
            "cluster_count": 4,
            "max_blocks": 16,
            "packet_w": 256,
            "banks": 8,
            "req_queue_depth": 3,
            "resp_queue_depth": 2,
            "bank_queue_depth": 3,
            "read_latency": 3,
            "arb_mode": "locality_first_bounded",
            "locality_burst_max": 3,
            "score_scale_lanes_per_cycle": 1,
            "value_memory_backend": "behavioral",
        },
    }
    generate(config, tmp_path)
    manifest = json.loads(
        (tmp_path / "attention_decode_score_multivalue_service_manifest.json").read_text(encoding="utf-8")
    )
    macro_manifest = json.loads((tmp_path / "macro_manifest.json").read_text(encoding="utf-8"))
    assert manifest["semantic_profile"] == "decode_m1x8_shared_score_16x8d_value_iterdiv_onchip_service_v1"
    assert manifest["result_mode"] == "normalized"
    assert manifest["result_value_bits_per_beat"] == 320
    assert manifest["cluster_count"] == 4
    assert manifest["packet_w"] == 256
    assert manifest["banks"] == 8
    assert manifest["arb_mode"] == "locality_first_bounded"
    assert manifest["shared_result_egress"] == "single_ready_valid_round_robin_hold_reg_v2"
    assert manifest["shared_result_egress_initiation_interval"] == 1
    assert manifest["shared_result_egress_stall_semantics"] == "stable_until_handshake"
    assert manifest["response_metadata_guard"] == "single_outstanding_per_cluster_v1"
    assert manifest["submodule_manifests"]["multivalue_cluster"]["result_beats_per_command"] == 16
    assert macro_manifest["manifest_params"]["score_bank_macro_count"] == 224
    assert macro_manifest["manifest_params"]["value_memory_backend"] == "behavioral"
    assert macro_manifest["manifest_params"]["value_memory_promotable"] is False


def test_multivalue_service_generator_exact_partial_manifest_and_ports(tmp_path: Path) -> None:
    config = {
        "top_name": "attention_decode_score_multivalue_service_exact_partial_c1",
        "attention_decode_score_multivalue_service": {
            "cluster_count": 1,
            "max_blocks": 16,
            "packet_w": 128,
            "banks": 4,
            "req_queue_depth": 2,
            "resp_queue_depth": 2,
            "bank_queue_depth": 2,
            "read_latency": 1,
            "arb_mode": "round_robin",
            "locality_burst_max": 2,
            "score_scale_lanes_per_cycle": 1,
            "result_mode": "exact_partial",
            "head_id_bits": 5,
            "value_memory_backend": "behavioral",
        },
    }
    generate(config, tmp_path)

    manifest = json.loads(
        (tmp_path / "attention_decode_score_multivalue_service_manifest.json").read_text(encoding="utf-8")
    )
    macro_manifest = json.loads((tmp_path / "macro_manifest.json").read_text(encoding="utf-8"))
    rtl = (tmp_path / "top.v").read_text(encoding="utf-8")

    assert (
        manifest["semantic_profile"]
        == "decode_m1x8_shared_score_16x8d_value_exact_partial_onchip_service_v1"
    )
    assert manifest["result_mode"] == "exact_partial"
    assert manifest["head_id_bits"] == 5
    assert manifest["result_value_bits_per_beat"] == 328
    assert (
        manifest["submodule_manifests"]["multivalue_cluster"]["semantic_profile"]
        == "decode_m1x8_shared_score_16x8d_value_exact_partial_v1"
    )
    assert manifest["submodule_manifests"]["multivalue_cluster"]["result_mode"] == "exact_partial"
    assert (
        manifest["submodule_manifests"]["multivalue_cluster"]["result_value_bits_per_beat"] == 328
    )
    assert macro_manifest["manifest_params"]["result_mode"] == "exact_partial"
    assert macro_manifest["manifest_params"]["head_id_bits"] == 5
    assert macro_manifest["manifest_params"]["result_value_bits_per_beat"] == 328
    assert "input  wire [4:0] cluster_command_head_id" in rtl
    assert "output wire [4:0] cluster_result_head_id" in rtl
    assert "output wire [4:0] shared_result_head_id" in rtl
    assert "output wire [327:0] shared_result_value" in rtl


def test_multivalue_service_generator_banked_4x16x64x32_macro_contract(tmp_path: Path) -> None:
    config = {
        "top_name": "attention_decode_score_multivalue_service_c2_p128_b4_q4_rl2_rr",
        "attention_decode_score_multivalue_service": {
            "cluster_count": 2,
            "max_blocks": 16,
            "packet_w": 128,
            "banks": 4,
            "req_queue_depth": 4,
            "resp_queue_depth": 4,
            "bank_queue_depth": 4,
            "read_latency": 2,
            "arb_mode": "round_robin",
            "locality_burst_max": 2,
            "score_scale_lanes_per_cycle": 1,
            "value_memory_backend": "macro_banked_4x16x64x32",
        },
    }
    generate(config, tmp_path)
    manifest = json.loads(
        (tmp_path / "attention_decode_score_multivalue_service_manifest.json").read_text(encoding="utf-8")
    )
    macro_manifest = json.loads((tmp_path / "macro_manifest.json").read_text(encoding="utf-8"))
    assert manifest["value_memory_backend"] == "macro_banked_4x16x64x32"
    assert manifest["value_memory_macro_count"] == 64
    assert manifest["total_macro_count"] == 176
    assert macro_manifest["manifest_params"]["value_memory_macro_count"] == 64
    assert macro_manifest["manifest_params"]["value_memory_macros_per_bank"] == 16
    assert macro_manifest["manifest_params"]["value_memory_macro_depth"] == 64
    assert macro_manifest["manifest_params"]["value_memory_logical_depth_per_bank"] == 64
    assert macro_manifest["manifest_params"]["value_memory_logical_depth_total"] == 256
    assert macro_manifest["manifest_params"]["value_memory_macro_overprovision_factor"] == 1
    assert (
        macro_manifest["manifest_params"]["value_memory_physical_contract"]
        == "banked_4x16x64x32_exact_capacity"
    )


def _service_exact_partial_expected() -> list[dict[str, int]]:
    workload = _workload_contract()
    beats = probe_module._cluster_beats(0, head_dim=int(workload["value_dim"]))
    score_rows = [[sum(query * keys[lane] for query, keys in block) for lane in range(8)] for block in beats]
    partials = partial_stream_from_blocks(
        command_id=0x4A21,
        head_id=3,
        score_rows=score_rows,
        value_blocks=probe_module._shared_value_matrices(),
    )
    return [
        {
            "command_id": int(beat.command_id),
            "head_id": int(beat.head_id),
            "slice": int(beat.slice_index),
            "last": int(bool(beat.last)),
            "global_max": int(beat.max_score),
            "exp_sum": int(beat.exp_sum),
            "value": int(pack_numerators(beat.numerators)),
        }
        for beat in partials
    ]


def _service_exact_partial_testbench() -> str:
    workload = _workload_contract()
    value_dim = int(workload["value_dim"])
    blocks = probe_module._cluster_beats(0, head_dim=value_dim)
    flat_beats = [beat for block in blocks for beat in block]
    values = probe_module._shared_value_matrices()
    preload_entries = []
    for block_index, block in enumerate(values):
        for slice_index, matrix in enumerate(block):
            preload_entries.append(
                (
                    block_index,
                    slice_index,
                    probe_module._pack([lane for row in matrix for lane in row], 8),
                )
            )
    beat_init = "\n".join(
        f"    q_mem[{idx}] = {probe_module._signed_literal(q, 8)}; "
        f"k_mem[{idx}] = 64'h{probe_module._pack(keys, 8):016x}; "
        f"last_mem[{idx}] = 1'b{1 if ((idx + 1) % value_dim == 0) else 0};"
        for idx, (q, keys) in enumerate(flat_beats)
    )
    preload_init = "\n".join(
        f"    preload_addr_mem[{idx}] = 14'd{addr}; "
        f"preload_slice_mem[{idx}] = 4'd{value_slice}; "
        f"preload_matrix_mem[{idx}] = 512'h{matrix:0128x};"
        for idx, (addr, value_slice, matrix) in enumerate(preload_entries)
    )
    return f"""
`timescale 1ns/1ps
module tb;
  localparam integer TOTAL_BEATS = {len(flat_beats)};
  localparam integer TOTAL_PRELOAD = {len(preload_entries)};
  localparam integer TOTAL_RESULTS = 16;

  reg clk = 1'b0;
  reg rst_n = 1'b0;
  always #5 clk = ~clk;

  reg preload_done = 1'b0;
  reg [7:0] preload_index = 8'd0;
  reg command_sent = 1'b0;
  reg [15:0] beat_index = 16'd0;
  reg [4:0] result_seen = 5'd0;
  reg [31:0] cycle = 32'd0;

  reg signed [7:0] q_mem [0:TOTAL_BEATS-1];
  reg [63:0] k_mem [0:TOTAL_BEATS-1];
  reg last_mem [0:TOTAL_BEATS-1];
  reg [13:0] preload_addr_mem [0:TOTAL_PRELOAD-1];
  reg [3:0] preload_slice_mem [0:TOTAL_PRELOAD-1];
  reg [511:0] preload_matrix_mem [0:TOTAL_PRELOAD-1];

  reg preload_valid;
  wire preload_ready;
  reg [13:0] preload_addr;
  reg [3:0] preload_value_slice;
  reg [511:0] preload_matrix;

  reg [0:0] cluster_command_valid;
  wire [0:0] cluster_command_ready;
  reg [15:0] cluster_command_id;
  reg [14:0] cluster_command_block_count;
  reg [4:0] cluster_command_head_id;
  reg [31:0] cluster_command_score_multiplier;
  reg [5:0] cluster_command_score_shift;
  reg [0:0] cluster_input_valid;
  wire [0:0] cluster_input_ready;
  reg [0:0] cluster_input_last;
  reg [7:0] cluster_input_a;
  reg [63:0] cluster_input_b;
  wire [0:0] cluster_result_valid;
  wire [0:0] cluster_result_ready;
  wire [15:0] cluster_result_command_id;
  wire [31:0] cluster_result_global_max;
  wire [32:0] cluster_result_exp_sum;
  wire [4:0] cluster_result_head_id;
  wire [3:0] cluster_result_slice;
  wire [0:0] cluster_result_last;
  wire [327:0] cluster_result_value;
  wire shared_result_valid;
  reg shared_result_ready = 1'b1;
  wire [0:0] shared_result_cluster;
  wire [15:0] shared_result_command_id;
  wire [31:0] shared_result_global_max;
  wire [32:0] shared_result_exp_sum;
  wire [4:0] shared_result_head_id;
  wire [3:0] shared_result_slice;
  wire shared_result_last;
  wire [327:0] shared_result_value;
  wire [31:0] cluster_accepted_count;
  wire [31:0] cluster_completed_count;
  wire [31:0] cluster_cycle_count;
  wire [0:0] cluster_protocol_error;
  wire [7:0] transport_req_tag;
  wire [0:0] transport_wide_source;
  wire [7:0] transport_wide_tag;
  wire [13:0] transport_wide_addr;
  wire [3:0] transport_wide_value_slice;
  wire [0:0] transport_wide_valid;
  wire [0:0] reassembler_protocol_error;
  wire [31:0] router_injection_stall_cycles;
  wire [31:0] router_arbitration_contention_cycles;
  wire [31:0] router_response_block_cycles;
  wire [31:0] router_req_current_occupancy;
  wire [31:0] router_req_max_occupancy;
  wire [31:0] router_resp_current_occupancy;
  wire [31:0] router_resp_max_occupancy;
  wire [31:0] service_accepted_req_count;
  wire [31:0] service_emitted_resp_count;
  wire [31:0] service_bank_conflict_count;
  wire [31:0] service_response_block_cycles;
  wire [31:0] service_req_current_occupancy;
  wire [31:0] service_req_max_occupancy;
  wire [31:0] service_resp_current_occupancy;
  wire [31:0] service_resp_max_occupancy;
  wire [31:0] result_arbitration_contention_cycles;
  wire [31:0] result_egress_block_cycles;
  wire protocol_error;

  attention_decode_score_multivalue_service_exact_partial_probe dut (
    .clk(clk),
    .rst_n(rst_n),
    .preload_valid(preload_valid),
    .preload_ready(preload_ready),
    .preload_addr(preload_addr),
    .preload_value_slice(preload_value_slice),
    .preload_matrix(preload_matrix),
    .cluster_command_valid(cluster_command_valid),
    .cluster_command_ready(cluster_command_ready),
    .cluster_command_id(cluster_command_id),
    .cluster_command_block_count(cluster_command_block_count),
    .cluster_command_head_id(cluster_command_head_id),
    .cluster_command_score_multiplier(cluster_command_score_multiplier),
    .cluster_command_score_shift(cluster_command_score_shift),
    .cluster_input_valid(cluster_input_valid),
    .cluster_input_ready(cluster_input_ready),
    .cluster_input_last(cluster_input_last),
    .cluster_input_a(cluster_input_a),
    .cluster_input_b(cluster_input_b),
    .cluster_result_valid(cluster_result_valid),
    .cluster_result_ready(cluster_result_ready),
    .cluster_result_command_id(cluster_result_command_id),
    .cluster_result_global_max(cluster_result_global_max),
    .cluster_result_exp_sum(cluster_result_exp_sum),
    .cluster_result_head_id(cluster_result_head_id),
    .cluster_result_slice(cluster_result_slice),
    .cluster_result_last(cluster_result_last),
    .cluster_result_value(cluster_result_value),
    .shared_result_valid(shared_result_valid),
    .shared_result_ready(shared_result_ready),
    .shared_result_cluster(shared_result_cluster),
    .shared_result_command_id(shared_result_command_id),
    .shared_result_global_max(shared_result_global_max),
    .shared_result_exp_sum(shared_result_exp_sum),
    .shared_result_head_id(shared_result_head_id),
    .shared_result_slice(shared_result_slice),
    .shared_result_last(shared_result_last),
    .shared_result_value(shared_result_value),
    .cluster_accepted_count(cluster_accepted_count),
    .cluster_completed_count(cluster_completed_count),
    .cluster_cycle_count(cluster_cycle_count),
    .cluster_protocol_error(cluster_protocol_error),
    .transport_req_tag(transport_req_tag),
    .transport_wide_source(transport_wide_source),
    .transport_wide_tag(transport_wide_tag),
    .transport_wide_addr(transport_wide_addr),
    .transport_wide_value_slice(transport_wide_value_slice),
    .transport_wide_valid(transport_wide_valid),
    .reassembler_protocol_error(reassembler_protocol_error),
    .router_injection_stall_cycles(router_injection_stall_cycles),
    .router_arbitration_contention_cycles(router_arbitration_contention_cycles),
    .router_response_block_cycles(router_response_block_cycles),
    .router_req_current_occupancy(router_req_current_occupancy),
    .router_req_max_occupancy(router_req_max_occupancy),
    .router_resp_current_occupancy(router_resp_current_occupancy),
    .router_resp_max_occupancy(router_resp_max_occupancy),
    .service_accepted_req_count(service_accepted_req_count),
    .service_emitted_resp_count(service_emitted_resp_count),
    .service_bank_conflict_count(service_bank_conflict_count),
    .service_response_block_cycles(service_response_block_cycles),
    .service_req_current_occupancy(service_req_current_occupancy),
    .service_req_max_occupancy(service_req_max_occupancy),
    .service_resp_current_occupancy(service_resp_current_occupancy),
    .service_resp_max_occupancy(service_resp_max_occupancy),
    .result_arbitration_contention_cycles(result_arbitration_contention_cycles),
    .result_egress_block_cycles(result_egress_block_cycles),
    .protocol_error(protocol_error)
  );

  initial begin
{beat_init}
{preload_init}
    repeat (4) @(posedge clk);
    rst_n = 1'b1;
  end

  always @(*) begin
    preload_valid = rst_n && !preload_done;
    preload_addr = preload_done ? 14'd0 : preload_addr_mem[preload_index];
    preload_value_slice = preload_done ? 4'd0 : preload_slice_mem[preload_index];
    preload_matrix = preload_done ? 512'd0 : preload_matrix_mem[preload_index];

    cluster_command_valid = 1'b0;
    cluster_command_id = 16'h4A21;
    cluster_command_block_count = 15'd3;
    cluster_command_head_id = 5'd3;
    cluster_command_score_multiplier = 32'd1;
    cluster_command_score_shift = 6'd0;
    if (rst_n && preload_done && !command_sent) begin
      cluster_command_valid[0] = 1'b1;
    end

    cluster_input_valid = 1'b0;
    cluster_input_last = 1'b0;
    cluster_input_a = 8'd0;
    cluster_input_b = 64'd0;
    if (rst_n && command_sent && (beat_index < TOTAL_BEATS)) begin
      cluster_input_valid[0] = 1'b1;
      cluster_input_last[0] = last_mem[beat_index];
      cluster_input_a = q_mem[beat_index];
      cluster_input_b = k_mem[beat_index];
    end
  end

  always @(posedge clk) begin
    if (!rst_n) begin
      preload_done <= 1'b0;
      preload_index <= 8'd0;
      command_sent <= 1'b0;
      beat_index <= 16'd0;
      result_seen <= 5'd0;
      cycle <= 32'd0;
    end else begin
      cycle <= cycle + 32'd1;
      if (!preload_done && preload_valid && preload_ready) begin
        if (preload_index + 1 == TOTAL_PRELOAD) begin
          preload_done <= 1'b1;
        end else begin
          preload_index <= preload_index + 1'b1;
        end
      end
      if (!command_sent && cluster_command_valid[0] && cluster_command_ready[0]) begin
        command_sent <= 1'b1;
      end
      if (cluster_input_valid[0] && cluster_input_ready[0]) begin
        beat_index <= beat_index + 1'b1;
      end
      if (shared_result_valid && shared_result_ready) begin
        $display("RESULT cmd=%0d head=%0d slice=%0d last=%0d max=%0d sum=%0d value=%082x",
          shared_result_command_id,
          shared_result_head_id,
          shared_result_slice,
          shared_result_last,
          $signed(shared_result_global_max),
          shared_result_exp_sum,
          shared_result_value);
        result_seen <= result_seen + 1'b1;
        if (result_seen + 1 == TOTAL_RESULTS) begin
          $finish;
        end
      end
      if (cycle > 32'd20000) begin
        $display("TIMEOUT cycle=%0d", cycle);
        $fatal(1);
      end
    end
  end
endmodule
"""


def test_multivalue_service_exact_partial_smoke_matches_reference(tmp_path: Path) -> None:
    if not _iverilog_available():
        pytest.skip("iverilog/vvp unavailable")

    config = {
        "top_name": "attention_decode_score_multivalue_service_exact_partial_probe",
        "attention_decode_score_multivalue_service": {
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
            "result_mode": "exact_partial",
            "head_id_bits": 5,
            "value_memory_backend": "behavioral",
        },
    }
    generate(config, tmp_path)
    (tmp_path / "fakeram45_2048x39.v").write_text(probe_module._FAKERAM_MODEL, encoding="utf-8")
    (tmp_path / "tb.v").write_text(_service_exact_partial_testbench(), encoding="utf-8")

    compile_run = subprocess.run(
        [
            probe_module._tool("iverilog"),
            "-g2012",
            "-o",
            str(tmp_path / "simv"),
            str(tmp_path / "tb.v"),
            str(tmp_path / "fakeram45_2048x39.v"),
            str(tmp_path / "top.v"),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert compile_run.returncode == 0, compile_run.stderr

    sim_run = subprocess.run(
        [probe_module._tool("vvp"), str(tmp_path / "simv")],
        check=False,
        capture_output=True,
        text=True,
    )
    assert sim_run.returncode == 0, sim_run.stderr

    observed = [
        {
            "command_id": int(match.group(1)),
            "head_id": int(match.group(2)),
            "slice": int(match.group(3)),
            "last": int(match.group(4)),
            "global_max": int(match.group(5)),
            "exp_sum": int(match.group(6)),
            "value": int(match.group(7), 16),
        }
        for line in sim_run.stdout.splitlines()
        for match in [_EXACT_RESULT_RE.fullmatch(line.strip())]
        if match is not None
    ]
    assert observed == _service_exact_partial_expected(), sim_run.stdout


def test_integrated_service_default_cases_cover_requested_surface() -> None:
    assert len(DEFAULT_CASES) == 14
    assert {row["cluster_count"] for row in DEFAULT_CASES} >= {1, 2, 4, 8, 16, 32}
    assert {row["packet_w"] for row in DEFAULT_CASES} == {128, 256}
    assert {row["banks"] for row in DEFAULT_CASES} >= {4, 8, 16, 32}
    assert {row["arb_mode"] for row in DEFAULT_CASES} == {"round_robin", "locality_first_bounded"}
    fixed_resource = {
        row["case_id"]
        for row in DEFAULT_CASES
        if row["packet_w"] == 128 and row["banks"] == 4 and row["arb_mode"] == "round_robin"
    }
    assert fixed_resource == {
        "c1_p128_b4_rr",
        "c2_p128_b4_rr",
        "c4_p128_b4_rr",
        "c8_p128_b4_rr",
        "c16_p128_b4_rr",
        "c32_p128_b4_rr",
    }
    assert {"c32_p256_b32_q1_rr", "c32_p256_b32_rl6_rr"} <= {
        row["case_id"] for row in DEFAULT_CASES
    }


@pytest.mark.parametrize("packet_w", [128, 256])
def test_integrated_service_zero_contention_exact(packet_w: int) -> None:
    if not _iverilog_available():
        pytest.skip("iverilog/vvp unavailable")
    report = build_report(
        {
            "cases": [
                _case(
                    case_id=f"zero_{packet_w}",
                    cluster_count=1,
                    packet_w=packet_w,
                    banks=2 if packet_w == 128 else 8,
                    arb_mode="round_robin" if packet_w == 128 else "locality_first_bounded",
                    locality_burst_max=2 if packet_w == 128 else 3,
                    read_latency=1 if packet_w == 128 else 3,
                    req_queue_depth=2,
                    resp_queue_depth=2,
                    bank_queue_depth=2 if packet_w == 128 else 3,
                )
            ]
        }
    )
    case = report["cases"][0]
    assert report["decision"] == "pass"
    assert case["decision"] == "pass"
    assert case["integrated_service"]["exact_match"] is True
    assert case["integrated_service"]["no_protocol_errors"] is True
    assert case["integrated_service"]["cycle_bound_ok"] is True
    assert case["integrated_service"]["service_penalty_cycles"] >= 0
    assert case["integrated_service"]["result_count"] == 16
    assert case["integrated_service"]["request_count"] == 48
    assert case["integrated_service"]["wide_response_count"] == 48
    assert case["integrated_service"]["counters"]["bank_conflict_count"] == 0
    assert case["integrated_service"]["counters"]["shared_result"]["egress_block_cycles"] >= 0
    assert case["integrated_service"]["shared_result_egress"]["documented_initiation_interval"] == 1
    assert case["baseline_no_stall"]["score_hash"] == case["expected_hashes"]["score_hash"]
    assert case["baseline_no_stall"]["final_hash"] == case["expected_hashes"]["final_hash"]
    assert case["integrated_service"]["final_hash"] == case["expected_hashes"]["final_hash"]


@pytest.mark.parametrize(
    ("packet_w", "banks", "arb_mode", "locality_burst_max", "cluster_count"),
    [
        (128, 2, "round_robin", 2, 2),
        (256, 8, "locality_first_bounded", 3, 4),
    ],
)
def test_integrated_service_same_bank_contention_exact(
    packet_w: int,
    banks: int,
    arb_mode: str,
    locality_burst_max: int,
    cluster_count: int,
) -> None:
    if not _iverilog_available():
        pytest.skip("iverilog/vvp unavailable")
    report = build_report(
        {
            "cases": [
                _case(
                    case_id=f"contended_{packet_w}",
                    cluster_count=cluster_count,
                    packet_w=packet_w,
                    banks=banks,
                    arb_mode=arb_mode,
                    locality_burst_max=locality_burst_max,
                    req_queue_depth=2 if packet_w == 128 else 3,
                    resp_queue_depth=2,
                    bank_queue_depth=2 if packet_w == 128 else 3,
                    read_latency=2 if packet_w == 128 else 3,
                )
            ]
        }
    )
    case = report["cases"][0]
    assert report["decision"] == "pass"
    assert case["integrated_service"]["exact_match"] is True
    assert case["integrated_service"]["no_protocol_errors"] is True
    assert case["integrated_service"]["no_drop_duplicate_deadlock_timeout"] is True
    assert case["integrated_service"]["service_penalty_cycles"] >= 0
    assert case["integrated_service"]["counters"]["bank_conflict_count"] > 0
    assert case["integrated_service"]["counters"]["arbitration_contention_cycles"] > 0
    assert case["integrated_service"]["counters"]["shared_result"]["arbitration_contention_cycles"] >= 0
    assert case["integrated_service"]["counters"]["shared_result"]["egress_block_cycles"] > 0
    assert case["integrated_service"]["shared_result_egress"]["documented_initiation_interval"] == 1
    assert case["integrated_service"]["shared_result_egress"]["back_to_back_fire_seen"] is True
    assert case["integrated_service"]["counters"]["request_injection_stall_cycles"] >= 0
    assert case["integrated_service"]["service_counts"]["accepted_req_count"] == 48 * cluster_count
    assert case["integrated_service"]["service_counts"]["emitted_resp_count"] == 48 * cluster_count
    assert case["integrated_service"]["request_hash"] == case["expected_hashes"]["request_hash"]
    assert (
        case["integrated_service"]["wide_response_matrix_hash"]
        == case["expected_hashes"]["wide_response_matrix_hash"]
    )
    assert case["integrated_service"]["final_hash"] == case["expected_hashes"]["final_hash"]


def test_integrated_service_fixed_resource_scaling_pair() -> None:
    if not _iverilog_available():
        pytest.skip("iverilog/vvp unavailable")
    report = build_report(
        {
            "cases": [
                _case(
                    case_id="fixed_c1",
                    cluster_count=1,
                    packet_w=128,
                    banks=4,
                    arb_mode="round_robin",
                    locality_burst_max=2,
                    req_queue_depth=4,
                    resp_queue_depth=4,
                    bank_queue_depth=4,
                    read_latency=2,
                ),
                _case(
                    case_id="fixed_c2",
                    cluster_count=2,
                    packet_w=128,
                    banks=4,
                    arb_mode="round_robin",
                    locality_burst_max=2,
                    req_queue_depth=4,
                    resp_queue_depth=4,
                    bank_queue_depth=4,
                    read_latency=2,
                ),
            ]
        }
    )
    c1, c2 = report["cases"]
    assert report["decision"] == "pass"
    assert c1["config"]["packet_w"] == c2["config"]["packet_w"] == 128
    assert c1["config"]["banks"] == c2["config"]["banks"] == 4
    assert c1["config"]["req_queue_depth"] == c2["config"]["req_queue_depth"] == 4
    assert c1["config"]["resp_queue_depth"] == c2["config"]["resp_queue_depth"] == 4
    assert c1["config"]["bank_queue_depth"] == c2["config"]["bank_queue_depth"] == 4
    assert c1["config"]["read_latency"] == c2["config"]["read_latency"] == 2
    assert c1["config"]["arb_mode"] == c2["config"]["arb_mode"] == "round_robin"
    assert c2["integrated_service"]["completion_cycle"] >= c1["integrated_service"]["completion_cycle"]
    assert c2["integrated_service"]["service_penalty_cycles"] >= c1["integrated_service"]["service_penalty_cycles"]
    assert c2["integrated_service"]["counters"]["shared_result"]["egress_block_cycles"] > 0
    assert c2["integrated_service"]["shared_result_egress"]["back_to_back_fire_seen"] is True


def test_integrated_service_report_retains_linkage_and_summary() -> None:
    if not _iverilog_available():
        pytest.skip("iverilog/vvp unavailable")
    report = build_report(
        {"cases": [_case(case_id="linkage", cluster_count=2, packet_w=128, banks=4, arb_mode="round_robin")]},
        proposal_id="prop_l2_decoder_attention_decode_score_multivalue_integrated_service_llama7b_v1",
        proposal_path=(
            "docs/proposals/prop_l2_decoder_attention_decode_score_multivalue_integrated_service_llama7b_v1/proposal.json"
        ),
        depends_on_item_ids=["l2_decoder_attention_decode_score_multivalue_cluster_equivalence_llama7b_v1"],
    )
    assert report["model"] == "llm_decoder_attention_decode_score_multivalue_integrated_service_probe_v1"
    assert report["source_links"]["proposal_id"] == (
        "prop_l2_decoder_attention_decode_score_multivalue_integrated_service_llama7b_v1"
    )
    assert report["source_links"]["proposal_path"].endswith("/proposal.json")
    assert report["source_links"]["depends_on_item_ids"] == [
        "l2_decoder_attention_decode_score_multivalue_cluster_equivalence_llama7b_v1"
    ]
    assert report["summary"]["validated_case_count"] == 1
    assert report["summary"]["all_hash_gates_passed"] is True
    assert report["summary"]["all_protocol_gates_passed"] is True
    assert report["summary"]["all_count_gates_passed"] is True
    assert report["workload_contract"] == _workload_contract()
    assert report["selected_scale_point"]["arch_id"] == "decode_score_multivalue_integrated_service"
    assert report["selected_scale_point"]["case_id"] == "linkage"
    assert "not a performance or architectural ranking" in report["selected_scale_point"]["selection_basis"]
    assert report["report_contract"]["shape"] == "deduplicated_shared_artifact_identities_v1"
    assert (
        report["source_identities"]["generated_artifacts"]["shared_preload"]["entry_count"]
        == _workload_expected_counts()["preload_entry_count"]
    )
    case = report["cases"][0]
    assert "generated_manifests" not in case
    assert "preload" not in case
    assert set(case["source_refs"]) == {
        "shared_preload",
        "baseline_manifest",
        "integrated_manifest",
        "baseline_top",
        "integrated_top",
    }


def test_integrated_service_report_compact_size_gate_with_large_manifests(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _baseline_manifest(case: dict) -> dict:
        return {
            "semantic_profile": "decode_m1x8_multivalue_cluster_equivalence_v1",
            "cluster_count": int(case["cluster_count"]),
            "result_beats_per_command": 16,
            "debug_payload": "b" * 8192,
        }

    def _integrated_manifest(case: dict) -> dict:
        return {
            "semantic_profile": "decode_m1x8_shared_score_16x8d_value_iterdiv_onchip_service_v1",
            "cluster_count": int(case["cluster_count"]),
            "packet_w": int(case["packet_w"]),
            "banks": int(case["banks"]),
            "arb_mode": str(case["arb_mode"]),
            "shared_result_egress": "single_ready_valid_round_robin_hold_reg_v2",
            "shared_result_egress_initiation_interval": 1,
            "shared_result_egress_stall_semantics": "stable_until_handshake",
            "response_metadata_guard": "single_outstanding_per_cluster_v1",
            "submodule_manifests": {
                "multivalue_cluster": {
                    "result_beats_per_command": 16,
                }
            },
            "debug_payload": "i" * 8192,
        }

    def _fake_baseline(case: dict, expected_clusters: list[dict], values: list[list[list[list[int]]]]) -> dict:
        del values
        score_rows = [
            {"cluster": cluster, "addr": addr, "row": rows}
            for cluster, payload in enumerate(expected_clusters)
            for addr, rows in enumerate(payload["score_rows"])
        ]
        results = [
            {
                **row,
                "cycle": 80 + row["slice"],
                "protocol_error": False,
            }
            for payload in expected_clusters
            for row in payload["results"]
        ]
        cluster_count = int(case["cluster_count"])
        done_rows = {
            cluster: {
                "cycle": 100 + cluster,
                "accepted": 48,
                "completed": 16,
            }
            for cluster in range(cluster_count)
        }
        top_sha256 = hashlib.sha256(f"baseline:{cluster_count}".encode()).hexdigest()
        return {
            "score_rows": score_rows,
            "results": results,
            "done_rows": done_rows,
            "completion_cycle": 180 + cluster_count,
            "protocol_error": False,
            "manifest": _baseline_manifest(case),
            "top_sha256": top_sha256,
        }

    def _fake_integrated(case: dict, values: list[list[list[list[int]]]]) -> dict:
        cluster_count = int(case["cluster_count"])
        expected_clusters = [
            probe_module._cluster_expected(cluster, values)
            for cluster in range(cluster_count)
        ]
        score_rows = [
            {"cluster": cluster, "addr": addr, "row": rows}
            for cluster, payload in enumerate(expected_clusters)
            for addr, rows in enumerate(payload["score_rows"])
        ]
        request_rows = [
            {
                **row,
                "cycle": 20 + row["tag"],
            }
            for payload in expected_clusters
            for row in payload["request_records"]
        ]
        wide_rows = [
            {
                **row,
                "cycle": 40 + row["tag"],
                "protocol_error": False,
            }
            for payload in expected_clusters
            for row in payload["response_records"]
        ]
        results = [
            {
                **row,
                "cycle": 220 + row["slice"],
                "protocol_error": False,
            }
            for payload in expected_clusters
            for row in payload["results"]
        ]
        done_rows = {
            cluster: {
                "cycle": 240 + cluster,
                "accepted": 48,
                "completed": 16,
            }
            for cluster in range(cluster_count)
        }
        counter_rows = {
            cluster: {
                "input_stall_cycles": cluster,
                "input_starvation_cycles": 0,
                "result_egress_block_cycles": max(cluster_count - 1, 0),
                "request_count": 48,
                "wide_response_count": 48,
            }
            for cluster in range(cluster_count)
        }
        top_sha256 = hashlib.sha256(
            f"integrated:{json.dumps(case, sort_keys=True)}".encode()
        ).hexdigest()
        return {
            "score_rows": score_rows,
            "request_rows": request_rows,
            "wide_rows": wide_rows,
            "results": results,
            "done_rows": done_rows,
            "counter_rows": counter_rows,
            "shared": {
                "completion_cycle": 260 + cluster_count,
                "protocol_error": False,
                "router_injection_stall_cycles": cluster_count,
                "router_arbitration_contention_cycles": max(cluster_count - 1, 0),
                "router_response_block_cycles": cluster_count // 2,
                "router_req_current_occupancy": 0,
                "router_req_max_occupancy": min(cluster_count, int(case["req_queue_depth"]) + 1),
                "router_resp_current_occupancy": 0,
                "router_resp_max_occupancy": min(cluster_count, int(case["resp_queue_depth"]) + 1),
                "service_accepted_req_count": 48 * cluster_count,
                "service_emitted_resp_count": 48 * cluster_count,
                "service_bank_conflict_count": max(cluster_count - 1, 0),
                "service_response_block_cycles": cluster_count // 2,
                "service_req_current_occupancy": 0,
                "service_req_max_occupancy": min(cluster_count, int(case["bank_queue_depth"]) + 1),
                "service_resp_current_occupancy": 0,
                "service_resp_max_occupancy": min(cluster_count, int(case["resp_queue_depth"]) + 1),
                "result_arbitration_contention_cycles": max(cluster_count - 1, 0),
                "result_egress_block_cycles": max(cluster_count - 1, 0),
                "result_back_to_back_fire_seen": True,
            },
            "manifest": _integrated_manifest(case),
            "top_sha256": top_sha256,
        }

    monkeypatch.setattr(probe_module, "_run_baseline", _fake_baseline)
    monkeypatch.setattr(probe_module, "_run_integrated", _fake_integrated)

    report = build_report()
    rendered = json.dumps(report, indent=2, sort_keys=True)

    assert len(rendered.encode()) <= COMPACT_REPORT_MAX_BYTES
    assert len(rendered.splitlines()) <= COMPACT_REPORT_MAX_LINES
    assert "preload_entries" not in report
    assert "debug_payload" not in rendered
    assert all("generated_manifests" not in case for case in report["cases"])
    assert all("preload" not in case for case in report["cases"])
    assert report["source_identities"]["generated_artifacts"]["shared_preload"]["payload_elided"] is True
    assert all(
        row["result_beats_per_command"] == 16
        for row in report["source_identities"]["generated_artifacts"]["generated_manifests"]
    )


def test_integrated_service_report_workload_contract_rejects_128_as_active_context() -> None:
    report = {
        "version": 1,
        "model": "llm_decoder_attention_decode_score_multivalue_integrated_service_probe_v1",
        "decision": "pass",
        "diagnosis": {"decision": "multivalue_integrated_service_probe_passed"},
        "exclusions": REPORT_EXCLUSIONS,
        "report_contract": {
            "shape": "deduplicated_shared_artifact_identities_v1",
            "max_pretty_json_bytes": COMPACT_REPORT_MAX_BYTES,
            "max_pretty_json_lines": COMPACT_REPORT_MAX_LINES,
        },
        "workload_contract": {
            **_workload_contract(),
            "active_context_tokens": 128,
        },
        "source_identities": {
            "repo_commit": "deadbeef",
            "generated_artifacts": {
                "shared_preload": {
                    "artifact_id": "shared_preload_v1",
                    "entry_count": _workload_expected_counts()["preload_entry_count"],
                    "payload_elided": True,
                },
                "generated_manifests": [{"artifact_id": "m1", "result_beats_per_command": 16}],
                "generated_tops": [{"artifact_id": "t1"}],
            },
        },
        "selected_scale_point": {
            "selection_role": "representative_largest_available_scale_point",
            "selection_basis": "coverage representative only, not a performance or architectural ranking.",
            "case_id": "c1",
        },
        "summary": {
            "validated_case_count": 1,
            "all_hash_gates_passed": True,
            "all_protocol_gates_passed": True,
            "all_count_gates_passed": True,
        },
        "cases": [
            {
                "case_id": "c1",
                "decision": "pass",
                "source_refs": {
                    "shared_preload": "shared_preload_v1",
                    "baseline_manifest": "m1",
                    "integrated_manifest": "m1",
                    "baseline_top": "t1",
                    "integrated_top": "t1",
                },
                "baseline_no_stall": {"completion_cycle": 1},
                "integrated_service": {
                    "completion_cycle": 1,
                    "service_penalty_cycles": 0,
                    "exact_match": True,
                    "no_protocol_errors": True,
                    "no_drop_duplicate_deadlock_timeout": True,
                    "cycle_bound_ok": True,
                    "counters": {
                        "request_injection_stall_cycles": 0,
                        "arbitration_contention_cycles": 0,
                        "bank_conflict_count": 0,
                        "response_block_cycles": {"router": 0, "service": 0},
                        "shared_result": {"arbitration_contention_cycles": 0, "egress_block_cycles": 0},
                        "max_occupancy": {"router_req": 0, "router_resp": 0, "service_req": 0, "service_resp": 0},
                    },
                    "shared_result_egress": {"documented_initiation_interval": 1},
                },
                "gates": {"hash_gate_ok": True, "protocol_gate_ok": True, "count_gate_ok": True},
            }
        ],
    }

    with pytest.raises(ValueError, match="workload_contract mismatch"):
        validate_report(report)


def test_integrated_service_selected_scale_point_is_nominal_not_worst_penalty() -> None:
    reports = [
        {
            "case_id": "c32_nominal_rr",
            "config": {
                "cluster_count": 32,
                "packet_w": 256,
                "banks": 32,
                "req_queue_depth": 4,
                "resp_queue_depth": 4,
                "bank_queue_depth": 4,
                "read_latency": 2,
                "arb_mode": "round_robin",
            },
            "integrated_service": {
                "completion_cycle": 100,
                "service_penalty_cycles": 10,
                "counters": {
                    "shared_result": {"egress_block_cycles": 3},
                    "arbitration_contention_cycles": 4,
                    "bank_conflict_count": 5,
                },
            },
        },
        {
            "case_id": "c32_stress_q1",
            "config": {
                "cluster_count": 32,
                "packet_w": 256,
                "banks": 32,
                "req_queue_depth": 1,
                "resp_queue_depth": 1,
                "bank_queue_depth": 1,
                "read_latency": 2,
                "arb_mode": "round_robin",
            },
            "integrated_service": {
                "completion_cycle": 900,
                "service_penalty_cycles": 800,
                "counters": {
                    "shared_result": {"egress_block_cycles": 30},
                    "arbitration_contention_cycles": 40,
                    "bank_conflict_count": 50,
                },
            },
        },
    ]
    selected = _selected_scale_point(reports)
    assert selected["case_id"] == "c32_nominal_rr"
    assert selected["service_penalty_cycles"] == 10
    assert selected["selection_role"] == "representative_largest_nominal_scale_point"


def test_integrated_service_validate_report_rejects_incomplete_evidence() -> None:
    if not _iverilog_available():
        pytest.skip("iverilog/vvp unavailable")
    report = build_report(
        {"cases": [_case(case_id="validate", cluster_count=2, packet_w=128, banks=2, arb_mode="round_robin")]}
    )
    broken = json.loads(json.dumps(report))
    broken["decision"] = "fail"
    with pytest.raises(ValueError, match="decision must be pass"):
        validate_report(broken)

    broken = json.loads(json.dumps(report))
    broken["diagnosis"]["decision"] = "multivalue_integrated_service_probe_failed"
    with pytest.raises(ValueError, match="diagnosis must record a passed probe"):
        validate_report(broken)

    broken = json.loads(json.dumps(report))
    broken["summary"]["all_hash_gates_passed"] = False
    with pytest.raises(ValueError, match="summary must record all report gates as passed"):
        validate_report(broken)

    broken = json.loads(json.dumps(report))
    broken["exclusions"] = REPORT_EXCLUSIONS[:-1]
    with pytest.raises(ValueError, match="exclusions"):
        validate_report(broken)

    broken = json.loads(json.dumps(report))
    del broken["cases"][0]["integrated_service"]["counters"]["max_occupancy"]
    with pytest.raises(ValueError, match="incomplete counters"):
        validate_report(broken)

    broken = json.loads(json.dumps(report))
    broken["cases"][0]["integrated_service"]["service_penalty_cycles"] = -1
    with pytest.raises(ValueError, match="negative service penalty"):
        validate_report(broken)

    broken = json.loads(json.dumps(report))
    broken["cases"][0]["integrated_service"]["shared_result_egress"]["documented_initiation_interval"] = 2
    with pytest.raises(ValueError, match="shared_result egress II"):
        validate_report(broken)

    broken = json.loads(json.dumps(report))
    broken["cases"][0]["integrated_service"]["shared_result_egress"]["back_to_back_fire_seen"] = False
    with pytest.raises(ValueError, match="back-to-back evidence"):
        validate_report(broken)

    broken = json.loads(json.dumps(report))
    broken["preload_entries"] = []
    with pytest.raises(ValueError, match="elide preload payloads"):
        validate_report(broken)

    broken = json.loads(json.dumps(report))
    broken["source_identities"]["generated_artifacts"]["generated_manifests"][0]["result_beats_per_command"] = 0
    with pytest.raises(ValueError, match="finite positive result_beats_per_command"):
        validate_report(broken)

    broken = json.loads(json.dumps(report))
    broken["debug_payload"] = "x" * COMPACT_REPORT_MAX_BYTES
    with pytest.raises(ValueError, match="compact size gate"):
        validate_report(broken)
