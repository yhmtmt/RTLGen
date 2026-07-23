#!/usr/bin/env python3
"""Probe integrated on-chip value service for multivalue decode-score clusters."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.rtlgen.gen_attention_decode_score_multivalue_cluster import generate as generate_cluster
from npu.rtlgen.gen_attention_decode_score_multivalue_service import generate as generate_service
from npu.sim.perf.attention_online import finalize_value, requantize_score_row, two_pass_stats
from npu.sim.perf.attention_separated import unpack_signed

JsonDict = dict[str, Any]

REPORT_EXCLUSIONS = [
    "physical_ppa",
    "hbm",
    "total_token_energy",
    "value_sram_macro_timing",
    "score_bank_macro_timing",
]

DEFAULT_CASES: list[JsonDict] = [
    {
        "case_id": "c1_p128_b4_rr",
        "cluster_count": 1,
        "packet_w": 128,
        "banks": 4,
        "req_queue_depth": 4,
        "resp_queue_depth": 4,
        "bank_queue_depth": 4,
        "read_latency": 2,
        "arb_mode": "round_robin",
        "locality_burst_max": 2,
    },
    {
        "case_id": "c2_p128_b4_rr",
        "cluster_count": 2,
        "packet_w": 128,
        "banks": 4,
        "req_queue_depth": 4,
        "resp_queue_depth": 4,
        "bank_queue_depth": 4,
        "read_latency": 2,
        "arb_mode": "round_robin",
        "locality_burst_max": 2,
    },
    {
        "case_id": "c4_p128_b4_rr",
        "cluster_count": 4,
        "packet_w": 128,
        "banks": 4,
        "req_queue_depth": 4,
        "resp_queue_depth": 4,
        "bank_queue_depth": 4,
        "read_latency": 2,
        "arb_mode": "round_robin",
        "locality_burst_max": 2,
    },
    {
        "case_id": "c8_p128_b4_rr",
        "cluster_count": 8,
        "packet_w": 128,
        "banks": 4,
        "req_queue_depth": 4,
        "resp_queue_depth": 4,
        "bank_queue_depth": 4,
        "read_latency": 2,
        "arb_mode": "round_robin",
        "locality_burst_max": 2,
    },
    {
        "case_id": "c16_p128_b4_rr",
        "cluster_count": 16,
        "packet_w": 128,
        "banks": 4,
        "req_queue_depth": 4,
        "resp_queue_depth": 4,
        "bank_queue_depth": 4,
        "read_latency": 2,
        "arb_mode": "round_robin",
        "locality_burst_max": 2,
    },
    {
        "case_id": "c32_p128_b4_rr",
        "cluster_count": 32,
        "packet_w": 128,
        "banks": 4,
        "req_queue_depth": 4,
        "resp_queue_depth": 4,
        "bank_queue_depth": 4,
        "read_latency": 2,
        "arb_mode": "round_robin",
        "locality_burst_max": 2,
    },
    {
        "case_id": "c8_p256_b8_rr",
        "cluster_count": 8,
        "packet_w": 256,
        "banks": 8,
        "req_queue_depth": 4,
        "resp_queue_depth": 4,
        "bank_queue_depth": 4,
        "read_latency": 2,
        "arb_mode": "round_robin",
        "locality_burst_max": 2,
    },
    {
        "case_id": "c8_p256_b8_locality",
        "cluster_count": 8,
        "packet_w": 256,
        "banks": 8,
        "req_queue_depth": 4,
        "resp_queue_depth": 4,
        "bank_queue_depth": 4,
        "read_latency": 2,
        "arb_mode": "locality_first_bounded",
        "locality_burst_max": 4,
    },
    {
        "case_id": "c16_p256_b16_rr",
        "cluster_count": 16,
        "packet_w": 256,
        "banks": 16,
        "req_queue_depth": 4,
        "resp_queue_depth": 4,
        "bank_queue_depth": 4,
        "read_latency": 2,
        "arb_mode": "round_robin",
        "locality_burst_max": 2,
    },
    {
        "case_id": "c16_p256_b16_locality",
        "cluster_count": 16,
        "packet_w": 256,
        "banks": 16,
        "req_queue_depth": 4,
        "resp_queue_depth": 4,
        "bank_queue_depth": 4,
        "read_latency": 2,
        "arb_mode": "locality_first_bounded",
        "locality_burst_max": 4,
    },
    {
        "case_id": "c32_p256_b32_rr",
        "cluster_count": 32,
        "packet_w": 256,
        "banks": 32,
        "req_queue_depth": 4,
        "resp_queue_depth": 4,
        "bank_queue_depth": 4,
        "read_latency": 2,
        "arb_mode": "round_robin",
        "locality_burst_max": 2,
    },
    {
        "case_id": "c32_p256_b32_locality",
        "cluster_count": 32,
        "packet_w": 256,
        "banks": 32,
        "req_queue_depth": 4,
        "resp_queue_depth": 4,
        "bank_queue_depth": 4,
        "read_latency": 2,
        "arb_mode": "locality_first_bounded",
        "locality_burst_max": 4,
    },
    {
        "case_id": "c32_p256_b32_q1_rr",
        "cluster_count": 32,
        "packet_w": 256,
        "banks": 32,
        "req_queue_depth": 1,
        "resp_queue_depth": 1,
        "bank_queue_depth": 1,
        "read_latency": 2,
        "arb_mode": "round_robin",
        "locality_burst_max": 2,
    },
    {
        "case_id": "c32_p256_b32_rl6_rr",
        "cluster_count": 32,
        "packet_w": 256,
        "banks": 32,
        "req_queue_depth": 4,
        "resp_queue_depth": 4,
        "bank_queue_depth": 4,
        "read_latency": 6,
        "arb_mode": "round_robin",
        "locality_burst_max": 2,
    },
]

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
  initial begin addr_q = 0; rd_out_q = 0; for (idx = 0; idx < 2048; idx = idx + 1) mem[idx] = 0; end
  always @(posedge clk) begin
    rd_out_q <= mem[addr_q];
    if (ce_in) begin
      if (we_in) for (idx = 0; idx < 39; idx = idx + 1)
        if (w_mask_in[idx]) mem[addr_in][idx] <= wd_in[idx];
      addr_q <= addr_in;
    end
  end
  assign rd_out = rd_out_q;
endmodule
"""

_BASE_SCORE_RE = re.compile(r"BASE_SWRITE cluster=(\d+) addr=(\d+) row=([0-9a-fA-F]+)")
_BASE_RESULT_RE = re.compile(
    r"BASE_RESULT cluster=(\d+) slice=(\d+) last=(\d+) id=(\d+) max=(-?\d+) sum=(\d+) value=([0-9a-fA-F]+) cycle=(\d+) error=(\d+)"
)
_BASE_DONE_RE = re.compile(r"BASE_DONE cluster=(\d+) cycle=(\d+) accepted=(\d+) completed=(\d+)")
_BASE_SUMMARY_RE = re.compile(r"BASE_SUMMARY completion_cycle=(\d+) protocol_error=(\d+)")

_INT_SCORE_RE = re.compile(r"INT_SWRITE cluster=(\d+) addr=(\d+) row=([0-9a-fA-F]+)")
_INT_REQ_RE = re.compile(r"INT_REQ cluster=(\d+) tag=(\d+) addr=(\d+) slice=(\d+) cycle=(\d+)")
_INT_WIDE_RE = re.compile(
    r"INT_WIDE cluster=(\d+) source=(\d+) tag=(\d+) addr=(\d+) slice=(\d+) cycle=(\d+) matrix=([0-9a-fA-F]+) proto=(\d+)"
)
_INT_RESULT_RE = re.compile(
    r"INT_RESULT cluster=(\d+) slice=(\d+) last=(\d+) id=(\d+) max=(-?\d+) sum=(\d+) value=([0-9a-fA-F]+) cycle=(\d+) error=(\d+)"
)
_INT_DONE_RE = re.compile(r"INT_DONE cluster=(\d+) cycle=(\d+) accepted=(\d+) completed=(\d+)")
_INT_COUNTER_RE = re.compile(
    r"INT_COUNTER cluster=(\d+) input_stall=(\d+) input_starve=(\d+) result_block=(\d+) req_count=(\d+) wide_count=(\d+)"
)
_INT_SHARED_RE = re.compile(
    r"INT_SHARED completion_cycle=(\d+) protocol_error=(\d+) router_inject=(\d+) arb=(\d+) router_resp_block=(\d+) "
    r"router_req_occ=(\d+) router_req_max=(\d+) router_resp_occ=(\d+) router_resp_max=(\d+) "
    r"service_req=(\d+) service_emit=(\d+) bank_conflict=(\d+) service_resp_block=(\d+) "
    r"service_req_occ=(\d+) service_req_max=(\d+) service_resp_occ=(\d+) service_resp_max=(\d+) "
    r"result_arb=(\d+) result_egress=(\d+) result_b2b=(\d+)"
)


def _tool(name: str) -> str:
    path = shutil.which(name)
    if path:
        return path
    fallback = Path("/oss-cad-suite/bin") / name
    if fallback.exists():
        return str(fallback)
    raise RuntimeError(f"required tool unavailable: {name}")


def _hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_head() -> str:
    run = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    return run.stdout.strip()


def _tool_version(name: str) -> str:
    binary = _tool(name)
    run = subprocess.run([binary, "-V"], capture_output=True, text=True, check=True)
    return run.stdout.splitlines()[0].strip() if run.stdout else run.stderr.splitlines()[0].strip()


def _signed_literal(value: int, bits: int) -> str:
    return f"-{bits}'sd{abs(value)}" if value < 0 else f"{bits}'sd{value}"


def _pack(values: list[int], bits: int) -> int:
    mask = (1 << bits) - 1
    return sum((int(value) & mask) << (index * bits) for index, value in enumerate(values))


def _shared_value_matrices() -> list[list[list[list[int]]]]:
    return [
        [
            [
                [((block * 37 + value_slice * 19 + row * 7 + lane * 3) % 255) - 127 for lane in range(8)]
                for row in range(8)
            ]
            for value_slice in range(16)
        ]
        for block in range(3)
    ]


def _cluster_beats(cluster_index: int, *, head_dim: int = 128) -> list[list[tuple[int, list[int]]]]:
    return [
        [
            (
                ((cluster_index * 23 + block * 17 + beat * 5) % 255) - 127,
                [
                    ((cluster_index * 41 + block * 31 + beat * 11 + lane * 13) % 255) - 127
                    for lane in range(8)
                ],
            )
            for beat in range(head_dim)
        ]
        for block in range(3)
    ]


def _raw_scores(block: list[tuple[int, list[int]]]) -> list[int]:
    return [sum(query * keys[lane] for query, keys in block) for lane in range(8)]


def _cluster_expected(cluster_index: int, values: list[list[list[list[int]]]]) -> JsonDict:
    beats = _cluster_beats(cluster_index)
    score_rows = [list(requantize_score_row(_raw_scores(block), multiplier=1, shift=0)) for block in beats]
    results: list[JsonDict] = []
    for value_slice in range(16):
        stats = two_pass_stats(score_rows, [values[block][value_slice] for block in range(len(values))])
        results.append(
            {
                "cluster": cluster_index,
                "slice": value_slice,
                "last": value_slice == 15,
                "command_id": 0x4A21 + cluster_index,
                "global_max": stats.max_score,
                "exp_sum": stats.exp_sum,
                "value": list(finalize_value(stats)),
            }
        )
    request_records = []
    response_records = []
    tag = 0
    for block in range(len(values)):
        for value_slice in range(16):
            matrix_hex = f"{_pack([lane for row in values[block][value_slice] for lane in row], 8):0128x}"
            request_records.append(
                {
                    "cluster": cluster_index,
                    "tag": tag,
                    "addr": block,
                    "slice": value_slice,
                }
            )
            response_records.append(
                {
                    "cluster": cluster_index,
                    "source": cluster_index,
                    "tag": tag,
                    "addr": block,
                    "slice": value_slice,
                    "matrix_hex": matrix_hex,
                }
            )
            tag += 1
    return {
        "beats": beats,
        "score_rows": score_rows,
        "results": results,
        "request_records": request_records,
        "response_records": response_records,
    }


def _preload_entries(values: list[list[list[list[int]]]]) -> list[JsonDict]:
    entries = []
    for block in range(len(values)):
        for value_slice in range(16):
            matrix_hex = f"{_pack([lane for row in values[block][value_slice] for lane in row], 8):0128x}"
            entries.append(
                {
                    "addr": block,
                    "slice": value_slice,
                    "matrix_hex": matrix_hex,
                    "matrix_hash": _hash(matrix_hex),
                }
            )
    return entries


def _cluster_config(top_name: str) -> JsonDict:
    return {
        "top_name": top_name,
        "attention_decode_score_multivalue_cluster": {
            "max_blocks": 16,
            "array_n": 8,
            "value_slices": 16,
            "divider_impl": "iterative_restoring",
            "score_scale_lanes_per_cycle": 1,
        },
    }


def _service_config(case: JsonDict, top_name: str) -> JsonDict:
    return {
        "top_name": top_name,
        "attention_decode_score_multivalue_service": {
            "cluster_count": int(case["cluster_count"]),
            "max_blocks": 16,
            "packet_w": int(case["packet_w"]),
            "banks": int(case["banks"]),
            "req_queue_depth": int(case["req_queue_depth"]),
            "resp_queue_depth": int(case["resp_queue_depth"]),
            "bank_queue_depth": int(case["bank_queue_depth"]),
            "read_latency": int(case["read_latency"]),
            "arb_mode": str(case["arb_mode"]),
            "locality_burst_max": int(case["locality_burst_max"]),
            "score_scale_lanes_per_cycle": 1,
        },
    }


def _baseline_testbench(*, top_name: str, cluster_count: int, values: list[list[list[list[int]]]]) -> str:
    total_beats = 3 * 128
    value_init = "\n".join(
        f"    value_mem[{addr * 16 + value_slice}] = 512'h{entry['matrix_hex']};"
        for addr in range(3)
        for value_slice, entry in enumerate(_preload_entries(values)[addr * 16 : (addr + 1) * 16])
    )
    per_cluster_decl: list[str] = []
    per_cluster_mem_init: list[str] = []
    per_cluster_drive: list[str] = []
    per_cluster_seq: list[str] = []
    per_cluster_log: list[str] = []
    per_cluster_done: list[str] = []
    last_indices = {127, 255, 383}

    for cluster in range(cluster_count):
        beats = [beat for block in _cluster_beats(cluster) for beat in block]
        beat_init = "\n".join(
            f"    q_mem_{cluster}[{idx}] = {_signed_literal(q, 8)}; k_mem_{cluster}[{idx}] = 64'h{_pack(keys, 8):016x};"
            for idx, (q, keys) in enumerate(beats)
        )
        last_cases = "\n".join(f"        {idx}: input_last[{cluster}] = 1'b1;" for idx in sorted(last_indices))
        per_cluster_decl.append(
            f"  reg signed [7:0] q_mem_{cluster} [0:TOTAL_BEATS-1];\n"
            f"  reg [63:0] k_mem_{cluster} [0:TOTAL_BEATS-1];\n"
            f"  reg [13:0] pending_addr_{cluster};\n"
            f"  reg [3:0] pending_slice_{cluster};\n"
            f"  integer pending_delay_{cluster};\n"
            f"  integer input_index_{cluster};"
        )
        per_cluster_mem_init.append(beat_init)
        per_cluster_drive.append(
            f"""    cluster_command_valid[{cluster}] = rst_n && !command_sent[{cluster}];
    cluster_input_valid[{cluster}] = rst_n && command_sent[{cluster}] && (input_index_{cluster} < TOTAL_BEATS);
    cluster_input_a[(8*{cluster}) +: 8] = (input_index_{cluster} < TOTAL_BEATS) ? q_mem_{cluster}[input_index_{cluster}] : 8'sd0;
    cluster_input_b[(64*{cluster}) +: 64] = (input_index_{cluster} < TOTAL_BEATS) ? k_mem_{cluster}[input_index_{cluster}] : 64'd0;
    input_last[{cluster}] = 1'b0;
    case (input_index_{cluster})
{last_cases}
      default: input_last[{cluster}] = 1'b0;
    endcase
"""
        )
        per_cluster_seq.append(
            f"""      if (cluster_command_valid[{cluster}] && cluster_command_ready[{cluster}]) begin
        command_sent[{cluster}] <= 1'b1;
      end
      if (cluster_input_valid[{cluster}] && cluster_input_ready[{cluster}]) begin
        input_index_{cluster} <= input_index_{cluster} + 1;
      end
      if (value_req_valid[{cluster}] && value_req_ready[{cluster}]) begin
        if (value_pending[{cluster}] || value_response_valid[{cluster}]) $fatal(1, "baseline multiple outstanding request cluster={cluster}");
        value_pending[{cluster}] <= 1'b1;
        pending_addr_{cluster} <= value_req_addr[(14*{cluster}) +: 14];
        pending_slice_{cluster} <= value_req_slice[(4*{cluster}) +: 4];
        pending_delay_{cluster} <= 1;
      end
      if (value_pending[{cluster}]) begin
        if (pending_delay_{cluster} == 0) begin
          value_pending[{cluster}] <= 1'b0;
          value_response_valid[{cluster}] <= 1'b1;
          value_response_addr[(14*{cluster}) +: 14] <= pending_addr_{cluster};
          value_response_slice[(4*{cluster}) +: 4] <= pending_slice_{cluster};
          value_response_matrix[(512*{cluster}) +: 512] <= value_mem[(pending_addr_{cluster} * 16) + pending_slice_{cluster}];
        end else begin
          pending_delay_{cluster} <= pending_delay_{cluster} - 1;
        end
      end
      if (value_response_valid[{cluster}] && value_response_ready[{cluster}]) begin
        value_response_valid[{cluster}] <= 1'b0;
      end
"""
        )
        per_cluster_log.append(
            f"""      if (u_cluster_{cluster}.score_write_valid && u_cluster_{cluster}.score_write_ready) begin
        $display("BASE_SWRITE cluster={cluster} addr=%0d row=%064x", u_cluster_{cluster}.score_write_addr, u_cluster_{cluster}.score_write_data);
      end
      if (cluster_result_valid[{cluster}] && cluster_result_ready[{cluster}]) begin
        $display("BASE_RESULT cluster={cluster} slice=%0d last=%0d id=%0d max=%0d sum=%0d value=%080x cycle=%0d error=%0d",
                 cluster_result_slice[(4*{cluster}) +: 4], cluster_result_last[{cluster}],
                 cluster_result_command_id[(16*{cluster}) +: 16], $signed(cluster_result_global_max[(32*{cluster}) +: 32]),
                 cluster_result_exp_sum[(33*{cluster}) +: 33], cluster_result_value[(320*{cluster}) +: 320], cycle, cluster_protocol_error[{cluster}]);
        result_count[{cluster}] <= result_count[{cluster}] + 1;
        if (cluster_result_last[{cluster}]) begin
          done[{cluster}] <= 1'b1;
          done_cycle[{cluster}] <= cycle;
          $display("BASE_DONE cluster={cluster} cycle=%0d accepted=%0d completed=%0d", cycle,
                   cluster_accepted_count[(32*{cluster}) +: 32], cluster_completed_count[(32*{cluster}) +: 32]);
        end
      end
"""
        )
        per_cluster_done.append(f"done[{cluster}]")

    instances = "\n".join(
        f"""  {top_name} u_cluster_{cluster} (
      .clk(clk), .rst_n(rst_n),
      .command_valid(cluster_command_valid[{cluster}]), .command_ready(cluster_command_ready[{cluster}]),
      .command_id(cluster_command_id[(16*{cluster}) +: 16]), .command_block_count(cluster_command_block_count[(15*{cluster}) +: 15]),
      .command_score_multiplier(cluster_command_score_multiplier[(32*{cluster}) +: 32]),
      .command_score_shift(cluster_command_score_shift[(6*{cluster}) +: 6]),
      .input_valid(cluster_input_valid[{cluster}]), .input_ready(cluster_input_ready[{cluster}]), .input_last(input_last[{cluster}]),
      .input_a(cluster_input_a[(8*{cluster}) +: 8]), .input_b(cluster_input_b[(64*{cluster}) +: 64]),
      .value_read_req_valid(value_req_valid[{cluster}]), .value_read_req_ready(value_req_ready[{cluster}]),
      .value_read_req_address(value_req_addr[(14*{cluster}) +: 14]), .value_read_req_slice(value_req_slice[(4*{cluster}) +: 4]),
      .value_response_valid(value_response_valid[{cluster}]), .value_response_ready(value_response_ready[{cluster}]),
      .value_response_address(value_response_addr[(14*{cluster}) +: 14]), .value_response_slice(value_response_slice[(4*{cluster}) +: 4]),
      .value_response_matrix(value_response_matrix[(512*{cluster}) +: 512]),
      .result_valid(cluster_result_valid[{cluster}]), .result_ready(cluster_result_ready[{cluster}]),
      .result_command_id(cluster_result_command_id[(16*{cluster}) +: 16]), .result_global_max(cluster_result_global_max[(32*{cluster}) +: 32]),
      .result_exp_sum(cluster_result_exp_sum[(33*{cluster}) +: 33]), .result_slice(cluster_result_slice[(4*{cluster}) +: 4]),
      .result_last(cluster_result_last[{cluster}]), .result_value(cluster_result_value[(320*{cluster}) +: 320]),
      .accepted_count(cluster_accepted_count[(32*{cluster}) +: 32]), .completed_count(cluster_completed_count[(32*{cluster}) +: 32]),
      .cycle_count(cluster_cycle_count[(32*{cluster}) +: 32]), .protocol_error(cluster_protocol_error[{cluster}])
  );"""
        for cluster in range(cluster_count)
    )
    return f"""`timescale 1ns/1ps
{_FAKERAM_MODEL}
module tb;
  localparam integer CLUSTERS = {cluster_count};
  localparam integer TOTAL_BEATS = {total_beats};
  reg clk = 1'b0;
  reg rst_n = 1'b0;
  reg [CLUSTERS-1:0] cluster_command_valid;
  wire [CLUSTERS-1:0] cluster_command_ready;
  reg [CLUSTERS*16-1:0] cluster_command_id;
  reg [CLUSTERS*15-1:0] cluster_command_block_count;
  reg [CLUSTERS*32-1:0] cluster_command_score_multiplier;
  reg [CLUSTERS*6-1:0] cluster_command_score_shift;
  reg [CLUSTERS-1:0] cluster_input_valid;
  wire [CLUSTERS-1:0] cluster_input_ready;
  reg [CLUSTERS-1:0] input_last;
  reg [CLUSTERS*8-1:0] cluster_input_a;
  reg [CLUSTERS*64-1:0] cluster_input_b;
  wire [CLUSTERS-1:0] value_req_valid;
  reg  [CLUSTERS-1:0] value_req_ready;
  wire [CLUSTERS*14-1:0] value_req_addr;
  wire [CLUSTERS*4-1:0] value_req_slice;
  reg  [CLUSTERS-1:0] value_response_valid;
  wire [CLUSTERS-1:0] value_response_ready;
  reg  [CLUSTERS*14-1:0] value_response_addr;
  reg  [CLUSTERS*4-1:0] value_response_slice;
  reg  [CLUSTERS*512-1:0] value_response_matrix;
  wire [CLUSTERS-1:0] cluster_result_valid;
  reg  [CLUSTERS-1:0] cluster_result_ready;
  wire [CLUSTERS*16-1:0] cluster_result_command_id;
  wire [CLUSTERS*32-1:0] cluster_result_global_max;
  wire [CLUSTERS*33-1:0] cluster_result_exp_sum;
  wire [CLUSTERS*4-1:0] cluster_result_slice;
  wire [CLUSTERS-1:0] cluster_result_last;
  wire [CLUSTERS*320-1:0] cluster_result_value;
  wire [CLUSTERS*32-1:0] cluster_accepted_count;
  wire [CLUSTERS*32-1:0] cluster_completed_count;
  wire [CLUSTERS*32-1:0] cluster_cycle_count;
  wire [CLUSTERS-1:0] cluster_protocol_error;
  reg [511:0] value_mem [0:(3*16)-1];
  reg [CLUSTERS-1:0] command_sent;
  reg [CLUSTERS-1:0] value_pending;
  reg [CLUSTERS-1:0] done;
  integer cycle;
  integer result_count [0:CLUSTERS-1];
  integer done_cycle [0:CLUSTERS-1];
  integer idx;
{chr(10).join(per_cluster_decl)}

  always #5 clk = ~clk;

{instances}

  always @* begin
    cluster_command_valid = {{CLUSTERS{{1'b0}}}};
    cluster_input_valid = {{CLUSTERS{{1'b0}}}};
    cluster_input_a = {{(CLUSTERS*8){{1'b0}}}};
    cluster_input_b = {{(CLUSTERS*64){{1'b0}}}};
    input_last = {{CLUSTERS{{1'b0}}}};
    value_req_ready = {{CLUSTERS{{1'b1}}}};
    cluster_result_ready = {{CLUSTERS{{1'b1}}}};
{chr(10).join(per_cluster_drive)}
  end

  always @(posedge clk) begin
    if (!rst_n) begin
      command_sent <= {{CLUSTERS{{1'b0}}}};
      value_pending <= {{CLUSTERS{{1'b0}}}};
      done <= {{CLUSTERS{{1'b0}}}};
      cycle <= 0;
      value_response_valid <= {{CLUSTERS{{1'b0}}}};
      value_response_addr <= {{(CLUSTERS*14){{1'b0}}}};
      value_response_slice <= {{(CLUSTERS*4){{1'b0}}}};
      value_response_matrix <= {{(CLUSTERS*512){{1'b0}}}};
      for (idx = 0; idx < CLUSTERS; idx = idx + 1) begin
        result_count[idx] <= 0;
        done_cycle[idx] <= 0;
      end
{chr(10).join(f"      input_index_{cluster} <= 0; pending_addr_{cluster} <= 0; pending_slice_{cluster} <= 0; pending_delay_{cluster} <= 0;" for cluster in range(cluster_count))}
    end else begin
      cycle <= cycle + 1;
{chr(10).join(per_cluster_seq)}
{chr(10).join(per_cluster_log)}
      if ({' && '.join(per_cluster_done)}) begin
        $display("BASE_SUMMARY completion_cycle=%0d protocol_error=%0d", cycle, |cluster_protocol_error);
        #1 $finish;
      end
      if (cycle > 30000) $fatal(1, "baseline timeout");
    end
  end

  initial begin
{value_init}
{chr(10).join(per_cluster_mem_init)}
    cluster_command_id = {{(CLUSTERS*16){{1'b0}}}};
    cluster_command_block_count = {{(CLUSTERS*15){{1'b0}}}};
    cluster_command_score_multiplier = {{(CLUSTERS*32){{1'b0}}}};
    cluster_command_score_shift = {{(CLUSTERS*6){{1'b0}}}};
    for (idx = 0; idx < CLUSTERS; idx = idx + 1) begin
      cluster_command_id[(16*idx) +: 16] = 16'h4a21 + idx[15:0];
      cluster_command_block_count[(15*idx) +: 15] = 15'd3;
      cluster_command_score_multiplier[(32*idx) +: 32] = 32'd1;
      cluster_command_score_shift[(6*idx) +: 6] = 6'd0;
    end
    repeat (3) @(posedge clk);
    @(negedge clk);
    rst_n = 1'b1;
  end
endmodule
"""


def _integrated_testbench(*, top_name: str, cluster_count: int, values: list[list[list[list[int]]]]) -> str:
    total_beats = 3 * 128
    source_w = max(1, (cluster_count - 1).bit_length())
    entries = _preload_entries(values)
    preload_init = "\n".join(
        f"    preload_addr_mem[{idx}] = 14'd{entry['addr']}; preload_slice_mem[{idx}] = 4'd{entry['slice']}; preload_matrix_mem[{idx}] = 512'h{entry['matrix_hex']};"
        for idx, entry in enumerate(entries)
    )
    per_cluster_drive: list[str] = []
    per_cluster_decl: list[str] = []
    per_cluster_mem_init: list[str] = []
    per_cluster_seq: list[str] = []
    per_cluster_log: list[str] = []
    per_cluster_done: list[str] = []
    last_indices = {127, 255, 383}

    for cluster in range(cluster_count):
        beats = [beat for block in _cluster_beats(cluster) for beat in block]
        beat_init = "\n".join(
            f"    q_mem_{cluster}[{idx}] = {_signed_literal(q, 8)}; k_mem_{cluster}[{idx}] = 64'h{_pack(keys, 8):016x};"
            for idx, (q, keys) in enumerate(beats)
        )
        last_cases = "\n".join(f"        {idx}: cluster_input_last[{cluster}] = 1'b1;" for idx in sorted(last_indices))
        per_cluster_decl.append(
            f"  reg signed [7:0] q_mem_{cluster} [0:TOTAL_BEATS-1];\n"
            f"  reg [63:0] k_mem_{cluster} [0:TOTAL_BEATS-1];\n"
            f"  integer input_index_{cluster};"
        )
        per_cluster_mem_init.append(beat_init)
        per_cluster_drive.append(
            f"""    cluster_command_valid[{cluster}] = rst_n && preload_done && !command_sent[{cluster}];
    cluster_input_valid[{cluster}] = rst_n && preload_done && command_sent[{cluster}] && (input_index_{cluster} < TOTAL_BEATS);
    cluster_input_a[(8*{cluster}) +: 8] = (input_index_{cluster} < TOTAL_BEATS) ? q_mem_{cluster}[input_index_{cluster}] : 8'sd0;
    cluster_input_b[(64*{cluster}) +: 64] = (input_index_{cluster} < TOTAL_BEATS) ? k_mem_{cluster}[input_index_{cluster}] : 64'd0;
    cluster_input_last[{cluster}] = 1'b0;
    case (input_index_{cluster})
{last_cases}
      default: cluster_input_last[{cluster}] = 1'b0;
    endcase
"""
        )
        per_cluster_seq.append(
            f"""      if (cluster_command_valid[{cluster}] && cluster_command_ready[{cluster}]) begin
        command_sent[{cluster}] <= 1'b1;
      end
      if (cluster_input_valid[{cluster}] && cluster_input_ready[{cluster}]) begin
        input_index_{cluster} <= input_index_{cluster} + 1;
      end
      if (command_sent[{cluster}] && (input_index_{cluster} < TOTAL_BEATS)) begin
        if (cluster_input_valid[{cluster}] && !cluster_input_ready[{cluster}]) begin
          input_stall_cycles[{cluster}] <= input_stall_cycles[{cluster}] + 1;
        end
        if (!cluster_input_valid[{cluster}] && cluster_input_ready[{cluster}]) begin
          input_starve_cycles[{cluster}] <= input_starve_cycles[{cluster}] + 1;
        end
      end
      if (cluster_result_valid[{cluster}] && !cluster_result_ready[{cluster}]) begin
        result_block_cycles[{cluster}] <= result_block_cycles[{cluster}] + 1;
      end
"""
        )
        per_cluster_log.append(
            f"""      if (dut.gen_cluster[{cluster}].u_cluster.score_write_valid && dut.gen_cluster[{cluster}].u_cluster.score_write_ready) begin
        $display("INT_SWRITE cluster={cluster} addr=%0d row=%064x",
                 dut.gen_cluster[{cluster}].u_cluster.score_write_addr,
                 dut.gen_cluster[{cluster}].u_cluster.score_write_data);
      end
      if (dut.src_req_valid[{cluster}] && dut.src_req_ready[{cluster}]) begin
        req_count[{cluster}] <= req_count[{cluster}] + 1;
        $display("INT_REQ cluster={cluster} tag=%0d addr=%0d slice=%0d cycle=%0d",
                 dut.transport_req_tag[(8*{cluster}) +: 8], dut.src_req_addr[(14*{cluster}) +: 14],
                 dut.src_req_value_slice[(4*{cluster}) +: 4], cycle);
      end
      if (dut.transport_wide_valid[{cluster}] && dut.cluster_value_resp_ready[{cluster}]) begin
        wide_count[{cluster}] <= wide_count[{cluster}] + 1;
        $display("INT_WIDE cluster={cluster} source=%0d tag=%0d addr=%0d slice=%0d cycle=%0d matrix=%0128x proto=%0d",
                 dut.transport_wide_source[({cluster}*{source_w}) +: {source_w}],
                 dut.transport_wide_tag[(8*{cluster}) +: 8], dut.transport_wide_addr[(14*{cluster}) +: 14],
                 dut.transport_wide_value_slice[(4*{cluster}) +: 4], cycle,
                 dut.cluster_value_resp_matrix[(512*{cluster}) +: 512], dut.reassembler_protocol_error[{cluster}]);
      end
"""
        )
        per_cluster_done.append(f"done[{cluster}]")

    return f"""`timescale 1ns/1ps
{_FAKERAM_MODEL}
module tb;
  localparam integer CLUSTERS = {cluster_count};
  localparam integer TOTAL_BEATS = {total_beats};
  localparam integer PRELOAD_COUNT = {len(entries)};
  reg clk = 1'b0;
  reg rst_n = 1'b0;
  reg preload_valid;
  wire preload_ready;
  reg [13:0] preload_addr;
  reg [3:0] preload_value_slice;
  reg [511:0] preload_matrix;
  reg [13:0] preload_addr_mem [0:PRELOAD_COUNT-1];
  reg [3:0] preload_slice_mem [0:PRELOAD_COUNT-1];
  reg [511:0] preload_matrix_mem [0:PRELOAD_COUNT-1];
  integer preload_index;
  reg preload_done;
  reg [CLUSTERS-1:0] cluster_command_valid;
  wire [CLUSTERS-1:0] cluster_command_ready;
  reg [CLUSTERS*16-1:0] cluster_command_id;
  reg [CLUSTERS*15-1:0] cluster_command_block_count;
  reg [CLUSTERS*32-1:0] cluster_command_score_multiplier;
  reg [CLUSTERS*6-1:0] cluster_command_score_shift;
  reg [CLUSTERS-1:0] cluster_input_valid;
  wire [CLUSTERS-1:0] cluster_input_ready;
  reg [CLUSTERS-1:0] cluster_input_last;
  reg [CLUSTERS*8-1:0] cluster_input_a;
  reg [CLUSTERS*64-1:0] cluster_input_b;
  wire [CLUSTERS-1:0] cluster_result_valid;
  wire [CLUSTERS-1:0] cluster_result_ready;
  wire [CLUSTERS*16-1:0] cluster_result_command_id;
  wire [CLUSTERS*32-1:0] cluster_result_global_max;
  wire [CLUSTERS*33-1:0] cluster_result_exp_sum;
  wire [CLUSTERS*4-1:0] cluster_result_slice;
  wire [CLUSTERS-1:0] cluster_result_last;
  wire [CLUSTERS*320-1:0] cluster_result_value;
  wire shared_result_valid;
  reg  shared_result_ready;
  wire [{source_w - 1}:0] shared_result_cluster;
  wire [15:0] shared_result_command_id;
  wire [31:0] shared_result_global_max;
  wire [32:0] shared_result_exp_sum;
  wire [3:0] shared_result_slice;
  wire shared_result_last;
  wire [319:0] shared_result_value;
  wire [CLUSTERS*32-1:0] cluster_accepted_count;
  wire [CLUSTERS*32-1:0] cluster_completed_count;
  wire [CLUSTERS*32-1:0] cluster_cycle_count;
  wire [CLUSTERS-1:0] cluster_protocol_error;
  wire [CLUSTERS*8-1:0] transport_req_tag;
  wire [CLUSTERS*{source_w}-1:0] transport_wide_source;
  wire [CLUSTERS*8-1:0] transport_wide_tag;
  wire [CLUSTERS*14-1:0] transport_wide_addr;
  wire [CLUSTERS*4-1:0] transport_wide_value_slice;
  wire [CLUSTERS-1:0] transport_wide_valid;
  wire [CLUSTERS-1:0] reassembler_protocol_error;
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
  wire protocol_error;
  reg [CLUSTERS-1:0] command_sent;
  reg [CLUSTERS-1:0] done;
  reg shared_result_block_active;
  reg shared_result_block_done;
  reg shared_result_block_competitor_seen;
  reg shared_result_back_to_back_seen;
  reg prev_shared_result_fire;
  reg blocked_payload_valid;
  integer cycle;
  integer idx;
  integer shared_result_block_cycles_left;
  integer done_cycle [0:CLUSTERS-1];
  integer req_count [0:CLUSTERS-1];
  integer wide_count [0:CLUSTERS-1];
  integer shared_result_count [0:CLUSTERS-1];
  integer input_stall_cycles [0:CLUSTERS-1];
  integer input_starve_cycles [0:CLUSTERS-1];
  integer result_block_cycles [0:CLUSTERS-1];
  reg [{source_w - 1}:0] blocked_cluster_q;
  reg [15:0] blocked_command_id_q;
  reg [31:0] blocked_global_max_q;
  reg [32:0] blocked_exp_sum_q;
  reg [3:0] blocked_slice_q;
  reg blocked_last_q;
  reg [319:0] blocked_value_q;
{chr(10).join(per_cluster_decl)}

  always #5 clk = ~clk;

  {top_name} dut (
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
    .cluster_result_slice(cluster_result_slice),
    .cluster_result_last(cluster_result_last),
    .cluster_result_value(cluster_result_value),
    .shared_result_valid(shared_result_valid),
    .shared_result_ready(shared_result_ready),
    .shared_result_cluster(shared_result_cluster),
    .shared_result_command_id(shared_result_command_id),
    .shared_result_global_max(shared_result_global_max),
    .shared_result_exp_sum(shared_result_exp_sum),
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
    .protocol_error(protocol_error)
  );

  always @* begin
    preload_valid = rst_n && !preload_done;
    preload_addr = preload_done ? 14'd0 : preload_addr_mem[preload_index];
    preload_value_slice = preload_done ? 4'd0 : preload_slice_mem[preload_index];
    preload_matrix = preload_done ? 512'd0 : preload_matrix_mem[preload_index];
    cluster_command_valid = {{CLUSTERS{{1'b0}}}};
    cluster_input_valid = {{CLUSTERS{{1'b0}}}};
    cluster_input_last = {{CLUSTERS{{1'b0}}}};
    cluster_input_a = {{(CLUSTERS*8){{1'b0}}}};
    cluster_input_b = {{(CLUSTERS*64){{1'b0}}}};
    shared_result_ready = 1'b1;
    if ((CLUSTERS > 1) && !shared_result_block_done &&
        (shared_result_block_active || shared_result_valid)) begin
      shared_result_ready = 1'b0;
    end
{chr(10).join(per_cluster_drive)}
  end

  always @(posedge clk) begin
    if (!rst_n) begin
      preload_index <= 0;
      preload_done <= 1'b0;
      command_sent <= {{CLUSTERS{{1'b0}}}};
      done <= {{CLUSTERS{{1'b0}}}};
      shared_result_block_active <= 1'b0;
      shared_result_block_done <= 1'b0;
      shared_result_block_competitor_seen <= 1'b0;
      shared_result_back_to_back_seen <= 1'b0;
      prev_shared_result_fire <= 1'b0;
      blocked_payload_valid <= 1'b0;
      cycle <= 0;
      shared_result_block_cycles_left <= 0;
      blocked_cluster_q <= {source_w}'d0;
      blocked_command_id_q <= 16'd0;
      blocked_global_max_q <= 32'd0;
      blocked_exp_sum_q <= 33'd0;
      blocked_slice_q <= 4'd0;
      blocked_last_q <= 1'b0;
      blocked_value_q <= 320'd0;
      for (idx = 0; idx < CLUSTERS; idx = idx + 1) begin
        done_cycle[idx] <= 0;
        req_count[idx] <= 0;
        wide_count[idx] <= 0;
        shared_result_count[idx] <= 0;
        input_stall_cycles[idx] <= 0;
        input_starve_cycles[idx] <= 0;
        result_block_cycles[idx] <= 0;
      end
{chr(10).join(f"      input_index_{cluster} <= 0;" for cluster in range(cluster_count))}
    end else begin
      cycle <= cycle + 1;
      if (!preload_done && preload_valid && preload_ready) begin
        if (preload_index == (PRELOAD_COUNT - 1)) begin
          preload_done <= 1'b1;
        end else begin
          preload_index <= preload_index + 1;
        end
      end
      if ((CLUSTERS > 1) && !shared_result_block_done && !shared_result_block_active && shared_result_valid) begin
        shared_result_block_active <= 1'b1;
        shared_result_block_competitor_seen <= 1'b0;
        shared_result_block_cycles_left <= 3;
        blocked_payload_valid <= 1'b0;
      end
      if (shared_result_block_active) begin
        if (shared_result_block_cycles_left > 0) begin
          shared_result_block_cycles_left <= shared_result_block_cycles_left - 1;
        end
        for (idx = 0; idx < CLUSTERS; idx = idx + 1) begin
          if ((idx != shared_result_cluster) && cluster_result_valid[idx]) begin
            shared_result_block_competitor_seen <= 1'b1;
          end
        end
        if (!shared_result_valid) begin
          $fatal(1, "shared result valid dropped while blocked");
        end
        if (!blocked_payload_valid) begin
          blocked_payload_valid <= 1'b1;
          blocked_cluster_q <= shared_result_cluster;
          blocked_command_id_q <= shared_result_command_id;
          blocked_global_max_q <= shared_result_global_max;
          blocked_exp_sum_q <= shared_result_exp_sum;
          blocked_slice_q <= shared_result_slice;
          blocked_last_q <= shared_result_last;
          blocked_value_q <= shared_result_value;
        end else if ((shared_result_cluster != blocked_cluster_q) ||
                     (shared_result_command_id != blocked_command_id_q) ||
                     (shared_result_global_max != blocked_global_max_q) ||
                     (shared_result_exp_sum != blocked_exp_sum_q) ||
                     (shared_result_slice != blocked_slice_q) ||
                     (shared_result_last != blocked_last_q) ||
                     (shared_result_value != blocked_value_q)) begin
          $fatal(1, "shared result payload changed while blocked");
        end
        if ((shared_result_block_cycles_left == 0) && shared_result_block_competitor_seen) begin
          shared_result_block_active <= 1'b0;
          shared_result_block_done <= 1'b1;
          blocked_payload_valid <= 1'b0;
        end
      end
{chr(10).join(per_cluster_seq)}
{chr(10).join(per_cluster_log)}
      if (shared_result_valid && shared_result_ready) begin
        if (prev_shared_result_fire) begin
          shared_result_back_to_back_seen <= 1'b1;
        end
        shared_result_count[shared_result_cluster] <= shared_result_count[shared_result_cluster] + 1;
        $display("INT_RESULT cluster=%0d slice=%0d last=%0d id=%0d max=%0d sum=%0d value=%080x cycle=%0d error=%0d",
                 shared_result_cluster, shared_result_slice, shared_result_last, shared_result_command_id,
                 $signed(shared_result_global_max), shared_result_exp_sum, shared_result_value, cycle, protocol_error);
        if (shared_result_last) begin
          done[shared_result_cluster] <= 1'b1;
          done_cycle[shared_result_cluster] <= cycle;
          $display("INT_DONE cluster=%0d cycle=%0d accepted=%0d completed=%0d", shared_result_cluster, cycle,
                   cluster_accepted_count[(32*shared_result_cluster) +: 32],
                   cluster_completed_count[(32*shared_result_cluster) +: 32]);
        end
      end
      prev_shared_result_fire <= shared_result_valid && shared_result_ready;
      if ({' && '.join(per_cluster_done)}) begin
{f'        if ((CLUSTERS > 1) && !shared_result_block_done) $fatal(1, "shared result stability stress did not complete");'}
{f'        if ((CLUSTERS > 1) && !shared_result_back_to_back_seen) $fatal(1, "shared result did not sustain back-to-back handshakes");'}
{chr(10).join(
    f'        $display("INT_COUNTER cluster={cluster} input_stall=%0d input_starve=%0d result_block=%0d req_count=%0d wide_count=%0d", input_stall_cycles[{cluster}], input_starve_cycles[{cluster}], result_block_cycles[{cluster}], req_count[{cluster}], wide_count[{cluster}]);'
    for cluster in range(cluster_count)
)}
        $display("INT_SHARED completion_cycle=%0d protocol_error=%0d router_inject=%0d arb=%0d router_resp_block=%0d router_req_occ=%0d router_req_max=%0d router_resp_occ=%0d router_resp_max=%0d service_req=%0d service_emit=%0d bank_conflict=%0d service_resp_block=%0d service_req_occ=%0d service_req_max=%0d service_resp_occ=%0d service_resp_max=%0d result_arb=%0d result_egress=%0d result_b2b=%0d",
                 cycle, protocol_error, router_injection_stall_cycles, router_arbitration_contention_cycles,
                 router_response_block_cycles, router_req_current_occupancy, router_req_max_occupancy,
                 router_resp_current_occupancy, router_resp_max_occupancy, service_accepted_req_count,
                 service_emitted_resp_count, service_bank_conflict_count, service_response_block_cycles,
                 service_req_current_occupancy, service_req_max_occupancy, service_resp_current_occupancy,
                 service_resp_max_occupancy, dut.result_arbitration_contention_cycles, dut.result_egress_block_cycles,
                 shared_result_back_to_back_seen);
        #1 $finish;
      end
      if (cycle > 60000) $fatal(1, "integrated timeout");
    end
  end

  initial begin
{preload_init}
{chr(10).join(per_cluster_mem_init)}
    cluster_command_id = {{(CLUSTERS*16){{1'b0}}}};
    cluster_command_block_count = {{(CLUSTERS*15){{1'b0}}}};
    cluster_command_score_multiplier = {{(CLUSTERS*32){{1'b0}}}};
    cluster_command_score_shift = {{(CLUSTERS*6){{1'b0}}}};
    for (idx = 0; idx < CLUSTERS; idx = idx + 1) begin
      cluster_command_id[(16*idx) +: 16] = 16'h4a21 + idx[15:0];
      cluster_command_block_count[(15*idx) +: 15] = 15'd3;
      cluster_command_score_multiplier[(32*idx) +: 32] = 32'd1;
      cluster_command_score_shift[(6*idx) +: 6] = 6'd0;
    end
    repeat (3) @(posedge clk);
    @(negedge clk);
    rst_n = 1'b1;
  end
endmodule
"""


def _compile_and_run(*, sources: list[Path], top: str = "tb", timeout: int = 180) -> str:
    with tempfile.TemporaryDirectory(prefix="multivalue-integrated-run-") as tmp_text:
        simv = Path(tmp_text) / "simv"
        compiled = subprocess.run(
            [_tool("iverilog"), "-g2012", "-s", top, "-o", str(simv), *[str(src) for src in sources]],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if compiled.returncode:
            raise RuntimeError(f"iverilog failed:\n{compiled.stderr}")
        run = subprocess.run([_tool("vvp"), str(simv)], capture_output=True, text=True, timeout=timeout)
        if run.returncode:
            raise RuntimeError(f"simulation failed:\n{run.stdout}\n{run.stderr}")
        return run.stdout


def _parse_score_lines(stdout: str, pattern: re.Pattern[str]) -> list[JsonDict]:
    rows: list[JsonDict] = []
    for line in stdout.splitlines():
        if match := pattern.fullmatch(line.strip()):
            rows.append(
                {
                    "cluster": int(match.group(1)),
                    "addr": int(match.group(2)),
                    "row": unpack_signed(int(match.group(3), 16), lanes=8, bits=32),
                }
            )
    return rows


def _parse_result_lines(stdout: str, pattern: re.Pattern[str]) -> list[JsonDict]:
    rows: list[JsonDict] = []
    for line in stdout.splitlines():
        if match := pattern.fullmatch(line.strip()):
            rows.append(
                {
                    "cluster": int(match.group(1)),
                    "slice": int(match.group(2)),
                    "last": bool(int(match.group(3))),
                    "command_id": int(match.group(4)),
                    "global_max": int(match.group(5)),
                    "exp_sum": int(match.group(6)),
                    "value": unpack_signed(int(match.group(7), 16), lanes=8, bits=40),
                    "cycle": int(match.group(8)),
                    "protocol_error": bool(int(match.group(9))),
                }
            )
    return rows


def _run_baseline(case: JsonDict, expected_clusters: list[JsonDict], values: list[list[list[list[int]]]]) -> JsonDict:
    cluster_count = int(case["cluster_count"])
    with tempfile.TemporaryDirectory(prefix="multivalue-baseline-") as tmp_text:
        tmp = Path(tmp_text)
        rtl_dir = tmp / "rtl"
        tb_path = tmp / "tb.sv"
        top_name = f"baseline_cluster_c{cluster_count}"
        generate_cluster(_cluster_config(top_name), rtl_dir)
        tb_path.write_text(
            _baseline_testbench(top_name=top_name, cluster_count=cluster_count, values=values),
            encoding="utf-8",
        )
        stdout = _compile_and_run(sources=[rtl_dir / "top.v", tb_path])
        manifest = json.loads(
            (rtl_dir / "attention_decode_score_multivalue_cluster_manifest.json").read_text(encoding="utf-8")
        )
        top_sha = _sha256_file(rtl_dir / "top.v")

    scores = _parse_score_lines(stdout, _BASE_SCORE_RE)
    results = _parse_result_lines(stdout, _BASE_RESULT_RE)
    done_rows = {
        int(match.group(1)): {
            "cycle": int(match.group(2)),
            "accepted": int(match.group(3)),
            "completed": int(match.group(4)),
        }
        for line in stdout.splitlines()
        if (match := _BASE_DONE_RE.fullmatch(line.strip()))
    }
    summary_match = next(
        (match for line in stdout.splitlines() if (match := _BASE_SUMMARY_RE.fullmatch(line.strip()))),
        None,
    )
    if summary_match is None:
        raise RuntimeError("baseline summary line missing")
    return {
        "score_rows": scores,
        "results": results,
        "done_rows": done_rows,
        "completion_cycle": int(summary_match.group(1)),
        "protocol_error": bool(int(summary_match.group(2))),
        "manifest": manifest,
        "top_sha256": top_sha,
    }


def _run_integrated(case: JsonDict, values: list[list[list[list[int]]]]) -> JsonDict:
    cluster_count = int(case["cluster_count"])
    with tempfile.TemporaryDirectory(prefix="multivalue-integrated-") as tmp_text:
        tmp = Path(tmp_text)
        rtl_dir = tmp / "rtl"
        tb_path = tmp / "tb.sv"
        top_name = f"integrated_service_c{cluster_count}_p{case['packet_w']}_b{case['banks']}"
        generate_service(_service_config(case, top_name), rtl_dir)
        tb_path.write_text(
            _integrated_testbench(top_name=top_name, cluster_count=cluster_count, values=values),
            encoding="utf-8",
        )
        stdout = _compile_and_run(sources=[rtl_dir / "top.v", tb_path], timeout=240)
        manifest = json.loads(
            (rtl_dir / "attention_decode_score_multivalue_service_manifest.json").read_text(encoding="utf-8")
        )
        top_sha = _sha256_file(rtl_dir / "top.v")

    scores = _parse_score_lines(stdout, _INT_SCORE_RE)
    req_rows = [
        {
            "cluster": int(match.group(1)),
            "tag": int(match.group(2)),
            "addr": int(match.group(3)),
            "slice": int(match.group(4)),
            "cycle": int(match.group(5)),
        }
        for line in stdout.splitlines()
        if (match := _INT_REQ_RE.fullmatch(line.strip()))
    ]
    wide_rows = [
        {
            "cluster": int(match.group(1)),
            "source": int(match.group(2)),
            "tag": int(match.group(3)),
            "addr": int(match.group(4)),
            "slice": int(match.group(5)),
            "cycle": int(match.group(6)),
            "matrix_hex": match.group(7).lower(),
            "protocol_error": bool(int(match.group(8))),
        }
        for line in stdout.splitlines()
        if (match := _INT_WIDE_RE.fullmatch(line.strip()))
    ]
    results = _parse_result_lines(stdout, _INT_RESULT_RE)
    done_rows = {
        int(match.group(1)): {
            "cycle": int(match.group(2)),
            "accepted": int(match.group(3)),
            "completed": int(match.group(4)),
        }
        for line in stdout.splitlines()
        if (match := _INT_DONE_RE.fullmatch(line.strip()))
    }
    counter_rows = {
        int(match.group(1)): {
            "input_stall_cycles": int(match.group(2)),
            "input_starvation_cycles": int(match.group(3)),
            "result_egress_block_cycles": int(match.group(4)),
            "request_count": int(match.group(5)),
            "wide_response_count": int(match.group(6)),
        }
        for line in stdout.splitlines()
        if (match := _INT_COUNTER_RE.fullmatch(line.strip()))
    }
    shared_match = next(
        (match for line in stdout.splitlines() if (match := _INT_SHARED_RE.fullmatch(line.strip()))),
        None,
    )
    if shared_match is None:
        raise RuntimeError("integrated shared counter line missing")
    shared = {
        "completion_cycle": int(shared_match.group(1)),
        "protocol_error": bool(int(shared_match.group(2))),
        "router_injection_stall_cycles": int(shared_match.group(3)),
        "router_arbitration_contention_cycles": int(shared_match.group(4)),
        "router_response_block_cycles": int(shared_match.group(5)),
        "router_req_current_occupancy": int(shared_match.group(6)),
        "router_req_max_occupancy": int(shared_match.group(7)),
        "router_resp_current_occupancy": int(shared_match.group(8)),
        "router_resp_max_occupancy": int(shared_match.group(9)),
        "service_accepted_req_count": int(shared_match.group(10)),
        "service_emitted_resp_count": int(shared_match.group(11)),
        "service_bank_conflict_count": int(shared_match.group(12)),
        "service_response_block_cycles": int(shared_match.group(13)),
        "service_req_current_occupancy": int(shared_match.group(14)),
        "service_req_max_occupancy": int(shared_match.group(15)),
        "service_resp_current_occupancy": int(shared_match.group(16)),
        "service_resp_max_occupancy": int(shared_match.group(17)),
        "result_arbitration_contention_cycles": int(shared_match.group(18)),
        "result_egress_block_cycles": int(shared_match.group(19)),
        "result_back_to_back_fire_seen": bool(int(shared_match.group(20))),
    }
    return {
        "score_rows": scores,
        "request_rows": req_rows,
        "wide_rows": wide_rows,
        "results": results,
        "done_rows": done_rows,
        "counter_rows": counter_rows,
        "shared": shared,
        "manifest": manifest,
        "top_sha256": top_sha,
    }


def _canonical_scores(rows: list[JsonDict]) -> list[JsonDict]:
    return [
        {
            "cluster": row["cluster"],
            "addr": row["addr"],
            "row": list(row["row"]),
        }
        for row in sorted(rows, key=lambda item: (item["cluster"], item["addr"]))
    ]


def _canonical_results(rows: list[JsonDict]) -> list[JsonDict]:
    return [
        {
            "cluster": row["cluster"],
            "slice": row["slice"],
            "last": row["last"],
            "command_id": row["command_id"],
            "global_max": row["global_max"],
            "exp_sum": row["exp_sum"],
            "value": list(row["value"]),
        }
        for row in sorted(rows, key=lambda item: (item["cluster"], item["slice"]))
    ]


def _canonical_requests(rows: list[JsonDict]) -> list[JsonDict]:
    return [
        {
            "cluster": row["cluster"],
            "tag": row["tag"],
            "addr": row["addr"],
            "slice": row["slice"],
        }
        for row in sorted(rows, key=lambda item: (item["cluster"], item["tag"]))
    ]


def _canonical_wide(rows: list[JsonDict]) -> list[JsonDict]:
    return [
        {
            "cluster": row["cluster"],
            "source": row["source"],
            "tag": row["tag"],
            "addr": row["addr"],
            "slice": row["slice"],
            "matrix_hex": row["matrix_hex"],
        }
        for row in sorted(rows, key=lambda item: (item["cluster"], item["tag"]))
    ]


def _summarize_case(case: JsonDict, baseline: JsonDict, integrated: JsonDict, preload_entries: list[JsonDict]) -> JsonDict:
    cluster_count = int(case["cluster_count"])
    values = _shared_value_matrices()
    expected_clusters = [_cluster_expected(cluster, values) for cluster in range(cluster_count)]
    expected_scores = [
        {"cluster": cluster, "addr": addr, "row": rows}
        for cluster, payload in enumerate(expected_clusters)
        for addr, rows in enumerate(payload["score_rows"])
    ]
    expected_results = [row for payload in expected_clusters for row in payload["results"]]
    expected_requests = [row for payload in expected_clusters for row in payload["request_records"]]
    expected_wide = [row for payload in expected_clusters for row in payload["response_records"]]

    baseline_scores = _canonical_scores(baseline["score_rows"])
    integrated_scores = _canonical_scores(integrated["score_rows"])
    expected_score_rows = _canonical_scores(expected_scores)
    baseline_results = _canonical_results(baseline["results"])
    integrated_results = _canonical_results(integrated["results"])
    expected_result_rows = _canonical_results(expected_results)
    integrated_requests = _canonical_requests(integrated["request_rows"])
    expected_request_rows = _canonical_requests(expected_requests)
    integrated_wide = _canonical_wide(integrated["wide_rows"])
    expected_wide_rows = _canonical_wide(expected_wide)

    per_cluster_done = [
        {
            "cluster": cluster,
            "baseline_cycle": int(baseline["done_rows"][cluster]["cycle"]),
            "integrated_cycle": int(integrated["done_rows"][cluster]["cycle"]),
            "accepted_count": int(integrated["done_rows"][cluster]["accepted"]),
            "completed_count": int(integrated["done_rows"][cluster]["completed"]),
        }
        for cluster in range(cluster_count)
    ]
    per_cluster_counters = [
        {
            "cluster": cluster,
            **integrated["counter_rows"][cluster],
        }
        for cluster in range(cluster_count)
    ]

    counts_ok = (
        len(baseline_results) == 16 * cluster_count
        and len(integrated_results) == 16 * cluster_count
        and len(integrated_requests) == 48 * cluster_count
        and len(integrated_wide) == 48 * cluster_count
        and integrated["shared"]["service_accepted_req_count"] == 48 * cluster_count
        and integrated["shared"]["service_emitted_resp_count"] == 48 * cluster_count
    )
    exact_match = (
        baseline_scores == expected_score_rows
        and integrated_scores == expected_score_rows
        and baseline_results == expected_result_rows
        and integrated_results == expected_result_rows
        and integrated_requests == expected_request_rows
        and integrated_wide == expected_wide_rows
    )
    baseline_hash_gate_ok = (
        _hash(baseline_scores) == _hash(expected_score_rows)
        and _hash(baseline_results) == _hash(expected_result_rows)
    )
    integrated_hash_gate_ok = (
        _hash(integrated_scores) == _hash(expected_score_rows)
        and _hash(integrated_results) == _hash(expected_result_rows)
        and _hash(integrated_requests) == _hash(expected_request_rows)
        and _hash(integrated_wide) == _hash(expected_wide_rows)
    )
    no_protocol_errors = (
        not baseline["protocol_error"]
        and not integrated["shared"]["protocol_error"]
        and not any(row["protocol_error"] for row in baseline["results"])
        and not any(row["protocol_error"] for row in integrated["results"])
        and not any(row["protocol_error"] for row in integrated["wide_rows"])
    )
    service_penalty_cycles = integrated["shared"]["completion_cycle"] - baseline["completion_cycle"]
    cycle_bound_ok = service_penalty_cycles >= 0
    no_drop_duplicate_deadlock_timeout = counts_ok and len(per_cluster_done) == cluster_count
    decision = "pass" if exact_match and no_protocol_errors and cycle_bound_ok and no_drop_duplicate_deadlock_timeout else "fail"

    return {
        "case_id": str(case["case_id"]),
        "decision": decision,
        "config": {
            key: case[key]
            for key in (
                "cluster_count",
                "packet_w",
                "banks",
                "req_queue_depth",
                "resp_queue_depth",
                "bank_queue_depth",
                "read_latency",
                "arb_mode",
                "locality_burst_max",
            )
        },
        "baseline_no_stall": {
            "completion_cycle": baseline["completion_cycle"],
            "score_hash": _hash(baseline_scores),
            "final_hash": _hash(baseline_results),
            "hash_gate_ok": baseline_hash_gate_ok,
            "score_matches_expected": baseline_scores == expected_score_rows,
            "final_matches_expected": baseline_results == expected_result_rows,
            "cluster_done": per_cluster_done,
            "top_sha256": baseline["top_sha256"],
        },
        "integrated_service": {
            "completion_cycle": integrated["shared"]["completion_cycle"],
            "service_penalty_cycles": service_penalty_cycles,
            "score_hash": _hash(integrated_scores),
            "final_hash": _hash(integrated_results),
            "request_hash": _hash(integrated_requests),
            "wide_response_matrix_hash": _hash(integrated_wide),
            "hash_gate_ok": integrated_hash_gate_ok,
            "exact_match": exact_match,
            "no_protocol_errors": no_protocol_errors,
            "no_drop_duplicate_deadlock_timeout": no_drop_duplicate_deadlock_timeout,
            "cycle_bound_ok": cycle_bound_ok,
            "cluster_done": per_cluster_done,
            "counters": {
                "cluster_input": per_cluster_counters,
                "request_injection_stall_cycles": integrated["shared"]["router_injection_stall_cycles"],
                "arbitration_contention_cycles": integrated["shared"]["router_arbitration_contention_cycles"],
                "bank_conflict_count": integrated["shared"]["service_bank_conflict_count"],
                "response_block_cycles": {
                    "router": integrated["shared"]["router_response_block_cycles"],
                    "service": integrated["shared"]["service_response_block_cycles"],
                },
                "shared_result": {
                    "arbitration_contention_cycles": integrated["shared"]["result_arbitration_contention_cycles"],
                    "egress_block_cycles": integrated["shared"]["result_egress_block_cycles"],
                },
                "max_occupancy": {
                    "router_req": integrated["shared"]["router_req_max_occupancy"],
                    "router_resp": integrated["shared"]["router_resp_max_occupancy"],
                    "service_req": integrated["shared"]["service_req_max_occupancy"],
                    "service_resp": integrated["shared"]["service_resp_max_occupancy"],
                },
            },
            "result_count": len(integrated_results),
            "request_count": len(integrated_requests),
            "wide_response_count": len(integrated_wide),
            "service_counts": {
                "accepted_req_count": integrated["shared"]["service_accepted_req_count"],
                "emitted_resp_count": integrated["shared"]["service_emitted_resp_count"],
            },
            "shared_result_egress": {
                "architecture": integrated["manifest"]["shared_result_egress"],
                "documented_initiation_interval": integrated["manifest"]["shared_result_egress_initiation_interval"],
                "stall_semantics": integrated["manifest"]["shared_result_egress_stall_semantics"],
                "back_to_back_fire_seen": integrated["shared"]["result_back_to_back_fire_seen"],
            },
            "top_sha256": integrated["top_sha256"],
        },
        "gates": {
            "hash_gate_ok": baseline_hash_gate_ok and integrated_hash_gate_ok,
            "protocol_gate_ok": no_protocol_errors,
            "count_gate_ok": counts_ok,
        },
        "expected_hashes": {
            "score_hash": _hash(expected_score_rows),
            "final_hash": _hash(expected_result_rows),
            "request_hash": _hash(expected_request_rows),
            "wide_response_matrix_hash": _hash(expected_wide_rows),
        },
        "preload": {
            "entry_count": len(preload_entries),
            "entries_hash": _hash(preload_entries),
        },
        "generated_manifests": {
            "baseline": baseline["manifest"],
            "integrated": integrated["manifest"],
        },
    }


def _selected_scale_point(reports: list[JsonDict]) -> JsonDict:
    nominal = [
        case
        for case in reports
        if int(case["config"]["req_queue_depth"]) == 4
        and int(case["config"]["resp_queue_depth"]) == 4
        and int(case["config"]["bank_queue_depth"]) == 4
        and int(case["config"]["read_latency"]) == 2
        and str(case["config"]["arb_mode"]) == "round_robin"
    ]
    selection_pool = nominal or reports
    selection_role = (
        "representative_largest_nominal_scale_point"
        if nominal
        else "representative_largest_available_scale_point"
    )
    selection_basis = (
        "Largest tested cluster_count, then packet_w, then banks among q4/read_latency=2/round_robin "
        "cases; coverage representative only, not a performance or architectural ranking."
        if nominal
        else "Largest tested cluster_count, then packet_w, then banks because no q4/read_latency=2/round_robin "
        "case was provided; coverage representative only, not a performance or architectural ranking."
    )
    selected = max(
        selection_pool,
        key=lambda case: (
            int(case["config"]["cluster_count"]),
            int(case["config"]["packet_w"]),
            int(case["config"]["banks"]),
            str(case["case_id"]),
        ),
    )
    config = dict(selected["config"])
    integrated = dict(selected["integrated_service"])
    return {
        "selection_role": selection_role,
        "selection_basis": selection_basis,
        "arch_id": "decode_score_multivalue_integrated_service",
        "macro_mode": "rtl_probe",
        "cluster_count": config["cluster_count"],
        "bank_count": config["banks"],
        "packet_payload_bytes": int(config["packet_w"]) // 8,
        "schedule_policy": "shared_score_value_service_probe",
        "bank_arbiter_policy": config["arb_mode"],
        "completion_cycle": integrated["completion_cycle"],
        "service_penalty_cycles": integrated["service_penalty_cycles"],
        "dominant_tile_resource": "onchip_shared_service",
        "case_id": selected["case_id"],
        "shared_result_egress_block_cycles": integrated["counters"]["shared_result"]["egress_block_cycles"],
        "router_arbitration_contention_cycles": integrated["counters"]["arbitration_contention_cycles"],
        "bank_conflict_count": integrated["counters"]["bank_conflict_count"],
    }


def _report_summary(reports: list[JsonDict]) -> JsonDict:
    stress_case = max(
        reports,
        key=lambda case: (
            int(case["integrated_service"]["service_penalty_cycles"]),
            int(case["integrated_service"]["completion_cycle"]),
            int(case["config"]["cluster_count"]),
        ),
    )
    return {
        "validated_case_count": len(reports),
        "max_cluster_count": max(int(case["config"]["cluster_count"]) for case in reports),
        "max_completion_cycle": max(int(case["integrated_service"]["completion_cycle"]) for case in reports),
        "max_service_penalty_cycles": max(
            int(case["integrated_service"]["service_penalty_cycles"]) for case in reports
        ),
        "max_router_arbitration_contention_cycles": max(
            int(case["integrated_service"]["counters"]["arbitration_contention_cycles"]) for case in reports
        ),
        "max_shared_result_egress_block_cycles": max(
            int(case["integrated_service"]["counters"]["shared_result"]["egress_block_cycles"]) for case in reports
        ),
        "max_bank_conflict_count": max(
            int(case["integrated_service"]["counters"]["bank_conflict_count"]) for case in reports
        ),
        "max_router_req_occupancy": max(
            int(case["integrated_service"]["counters"]["max_occupancy"]["router_req"]) for case in reports
        ),
        "max_service_req_occupancy": max(
            int(case["integrated_service"]["counters"]["max_occupancy"]["service_req"]) for case in reports
        ),
        "stress_case_id": str(stress_case["case_id"]),
        "all_hash_gates_passed": all(bool(case["gates"]["hash_gate_ok"]) for case in reports),
        "all_protocol_gates_passed": all(bool(case["gates"]["protocol_gate_ok"]) for case in reports),
        "all_count_gates_passed": all(bool(case["gates"]["count_gate_ok"]) for case in reports),
    }


def _validate_case(case: JsonDict) -> JsonDict:
    cluster_count = int(case.get("cluster_count", 0))
    packet_w = int(case.get("packet_w", 0))
    banks = int(case.get("banks", 0))
    req_queue_depth = int(case.get("req_queue_depth", 0))
    resp_queue_depth = int(case.get("resp_queue_depth", 0))
    bank_queue_depth = int(case.get("bank_queue_depth", 0))
    read_latency = int(case.get("read_latency", -1))
    locality_burst_max = int(case.get("locality_burst_max", 0))
    arb_mode = str(case.get("arb_mode", "")).strip().lower()
    case_id = str(case.get("case_id") or "").strip()
    if not case_id:
        raise ValueError("case requires case_id")
    if cluster_count < 1 or cluster_count > 32:
        raise ValueError(f"{case_id}: cluster_count must be in [1, 32]")
    if packet_w not in {128, 256}:
        raise ValueError(f"{case_id}: packet_w must be 128 or 256")
    if banks < 1:
        raise ValueError(f"{case_id}: banks must be positive")
    if min(req_queue_depth, resp_queue_depth, bank_queue_depth) < 1:
        raise ValueError(f"{case_id}: queue depths must be positive")
    if read_latency < 0:
        raise ValueError(f"{case_id}: read_latency must be non-negative")
    if arb_mode not in {"round_robin", "locality_first_bounded"}:
        raise ValueError(f"{case_id}: arb_mode must be round_robin or locality_first_bounded")
    if locality_burst_max < 1:
        raise ValueError(f"{case_id}: locality_burst_max must be positive")
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


def build_report(
    config: JsonDict | None = None,
    *,
    proposal_id: str | None = None,
    proposal_path: str | None = None,
    depends_on_item_ids: list[str] | None = None,
) -> JsonDict:
    payload = config or {"cases": DEFAULT_CASES}
    case_rows = payload.get("cases")
    if not isinstance(case_rows, list) or not case_rows:
        raise ValueError("config must provide non-empty cases list")
    cases = [_validate_case(row if isinstance(row, dict) else {}) for row in case_rows]

    values = _shared_value_matrices()
    preload_entries = _preload_entries(values)
    reports = []
    for case in cases:
        expected_clusters = [_cluster_expected(cluster, values) for cluster in range(int(case["cluster_count"]))]
        baseline = _run_baseline(case, expected_clusters, values)
        integrated = _run_integrated(case, values)
        reports.append(_summarize_case(case, baseline, integrated, preload_entries))

    decision = "pass" if all(case["decision"] == "pass" for case in reports) else "fail"
    result = {
        "version": 1,
        "model": "llm_decoder_attention_decode_score_multivalue_integrated_service_probe_v1",
        "decision": decision,
        "diagnosis": {
            "decision": (
                "multivalue_integrated_service_probe_passed"
                if decision == "pass"
                else "multivalue_integrated_service_probe_failed"
            ),
            "recommended_next_step": (
                "Use this merged/materialized integrated-service probe as the shared-score on-chip service "
                "closure input before any NoC, HBM, physical PPA, SRAM macro timing, or token-energy claim."
            ),
        },
        "exclusions": REPORT_EXCLUSIONS,
        "source_identities": {
            "repo_commit": _git_head(),
            "tool_versions": {
                "iverilog": _tool_version("iverilog"),
                "vvp": _tool_version("vvp"),
            },
            "files": [
                {
                    "path": rel,
                    "sha256": _sha256_file(REPO_ROOT / rel),
                }
                for rel in (
                    "npu/rtlgen/gen_attention_decode_score_multivalue_service.py",
                    "npu/eval/probe_attention_decode_score_multivalue_integrated_service.py",
                    "npu/rtlgen/gen_attention_decode_score_multivalue_cluster.py",
                    "npu/sim/rtl/noc_ready_valid_fifo.sv",
                    "npu/sim/rtl/noc_ready_valid_router.sv",
                    "npu/sim/rtl/banked_value_memory_service.sv",
                    "npu/sim/rtl/noc_value_matrix_reassembler.sv",
                )
            ],
        },
        "preload_entries": preload_entries,
        "selected_scale_point": _selected_scale_point(reports),
        "summary": _report_summary(reports),
        "cases": reports,
    }
    linkage: JsonDict = {}
    if proposal_id:
        linkage["proposal_id"] = str(proposal_id)
    if proposal_path:
        linkage["proposal_path"] = str(proposal_path)
    depends = [str(item).strip() for item in (depends_on_item_ids or []) if str(item).strip()]
    if depends:
        linkage["depends_on_item_ids"] = depends
    if linkage:
        result["source_links"] = linkage
    validate_report(result)
    return result


def validate_report(payload: JsonDict) -> None:
    if payload.get("version") != 1:
        raise ValueError("report version must be 1")
    if payload.get("model") != "llm_decoder_attention_decode_score_multivalue_integrated_service_probe_v1":
        raise ValueError("unexpected report model")
    if payload.get("exclusions") != REPORT_EXCLUSIONS:
        raise ValueError(f"report exclusions must explicitly be {', '.join(REPORT_EXCLUSIONS)}")
    source = payload.get("source_identities")
    if not isinstance(source, dict) or not source.get("repo_commit"):
        raise ValueError("report lacks source identities")
    preload_entries = payload.get("preload_entries")
    if not isinstance(preload_entries, list) or len(preload_entries) != 48:
        raise ValueError("report must include all 48 preload entries")
    cases = payload.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("report must contain cases")
    summary = payload.get("summary")
    if not isinstance(summary, dict):
        raise ValueError("report must contain summary")
    if int(summary.get("validated_case_count", 0)) != len(cases):
        raise ValueError("summary validated_case_count mismatch")
    selected_scale_point = payload.get("selected_scale_point")
    if not isinstance(selected_scale_point, dict):
        raise ValueError("report must contain selected_scale_point")
    if selected_scale_point.get("selection_role") not in {
        "representative_largest_nominal_scale_point",
        "representative_largest_available_scale_point",
    }:
        raise ValueError("selected_scale_point lacks representative selection role")
    if "not a performance or architectural ranking" not in str(selected_scale_point.get("selection_basis", "")):
        raise ValueError("selected_scale_point must explicitly disclaim ranking")
    case_ids = {str(case.get("case_id")) for case in cases if isinstance(case, dict)}
    if str(selected_scale_point.get("case_id")) not in case_ids:
        raise ValueError("selected_scale_point does not reference a report case")
    for case in cases:
        if not isinstance(case, dict):
            raise ValueError("case rows must be objects")
        if case.get("decision") != "pass":
            raise ValueError(f"case failed: {case.get('case_id')}")
        baseline = case.get("baseline_no_stall")
        integrated = case.get("integrated_service")
        if not isinstance(baseline, dict) or not isinstance(integrated, dict):
            raise ValueError("case lacks baseline or integrated section")
        if int(integrated.get("service_penalty_cycles", -1)) < 0:
            raise ValueError(f"negative service penalty for {case.get('case_id')}")
        if int(integrated.get("completion_cycle", -1)) < int(baseline.get("completion_cycle", 0)):
            raise ValueError(f"integrated completion cycle below baseline for {case.get('case_id')}")
        if integrated.get("exact_match") is not True:
            raise ValueError(f"exact result match missing for {case.get('case_id')}")
        if integrated.get("no_protocol_errors") is not True:
            raise ValueError(f"protocol errors present for {case.get('case_id')}")
        if integrated.get("no_drop_duplicate_deadlock_timeout") is not True:
            raise ValueError(f"drop/duplicate/deadlock evidence missing for {case.get('case_id')}")
        if integrated.get("cycle_bound_ok") is not True:
            raise ValueError(f"cycle bound violated for {case.get('case_id')}")
        counters = integrated.get("counters")
        if not isinstance(counters, dict):
            raise ValueError(f"counters missing for {case.get('case_id')}")
        required_counter_keys = {
            "cluster_input",
            "request_injection_stall_cycles",
            "arbitration_contention_cycles",
            "bank_conflict_count",
            "response_block_cycles",
            "shared_result",
            "max_occupancy",
        }
        if required_counter_keys - set(counters):
            raise ValueError(f"incomplete counters for {case.get('case_id')}")
        egress = integrated.get("shared_result_egress")
        if not isinstance(egress, dict):
            raise ValueError(f"shared_result_egress missing for {case.get('case_id')}")
        if int(egress.get("documented_initiation_interval", 0)) != 1:
            raise ValueError(f"unexpected shared_result egress II for {case.get('case_id')}")
        if int(case.get("config", {}).get("cluster_count", 0)) > 1 and egress.get("back_to_back_fire_seen") is not True:
            raise ValueError(f"missing shared_result back-to-back evidence for {case.get('case_id')}")
        gates = case.get("gates")
        if not isinstance(gates, dict) or not all(bool(gates.get(key)) for key in ("hash_gate_ok", "protocol_gate_ok", "count_gate_ok")):
            raise ValueError(f"gate status missing or failed for {case.get('case_id')}")


def _build_markdown(report: JsonDict) -> str:
    summary = dict(report["summary"])
    selected_scale_point = dict(report["selected_scale_point"])
    linkage = dict(report.get("source_links") or {})
    lines = [
        "# Attention Decode Score Multivalue Integrated Service Probe",
        "",
        f"- decision: `{report['decision']}`",
        f"- outcome: `{report['diagnosis']['decision']}`",
        f"- repo commit: `{report['source_identities']['repo_commit']}`",
        f"- cases: `{summary['validated_case_count']}`",
        f"- max_cluster_count: `{summary['max_cluster_count']}`",
        f"- max_completion_cycle: `{summary['max_completion_cycle']}`",
        f"- max_service_penalty_cycles: `{summary['max_service_penalty_cycles']}`",
        f"- stress_case_id: `{summary['stress_case_id']}`",
        f"- selected_scale_point: `{selected_scale_point['case_id']}`",
        f"- selected_scale_point_role: `{selected_scale_point['selection_role']}`",
        f"- selected_scale_point_note: {selected_scale_point['selection_basis']}",
        f"- gates: `hash={summary['all_hash_gates_passed']}` `protocol={summary['all_protocol_gates_passed']}` `count={summary['all_count_gates_passed']}`",
        f"- exclusions: `{', '.join(report['exclusions'])}`",
    ]
    if linkage.get("proposal_id"):
        lines.append(f"- proposal_id: `{linkage['proposal_id']}`")
    if linkage.get("proposal_path"):
        lines.append(f"- proposal_path: `{linkage['proposal_path']}`")
    depends = linkage.get("depends_on_item_ids")
    if isinstance(depends, list) and depends:
        lines.append(f"- depends_on_item_ids: `{', '.join(str(item) for item in depends)}`")
    lines.extend(
        [
            "",
            "## Cases",
            "",
            "| case | cfg | done | penalty | gate | req stall | router arb | bank conflict | resp block r/s | shared arb/block | occ rreq/rresp/sreq/sresp |",
            "| --- | --- | ---: | ---: | --- | ---: | ---: | ---: | --- | --- | --- |",
        ]
    )
    for case in report["cases"]:
        config = dict(case["config"])
        integrated = dict(case["integrated_service"])
        counters = dict(integrated["counters"])
        occupancy = dict(counters["max_occupancy"])
        shared = dict(counters["shared_result"])
        response_block = dict(counters["response_block_cycles"])
        gate = dict(case["gates"])
        lines.append(
            "| {case_id} | c{cluster}/p{packet}/b{banks}/{arb}/q{queue}/rl{latency} | {done} | {penalty} | "
            "h:{hash_gate}/p:{protocol_gate}/c:{count_gate} | {req_stall} | {router_arb} | {bank_conflict} | "
            "{router_block}/{service_block} | {shared_arb}/{shared_block} | {router_req}/{router_resp}/{service_req}/{service_resp} |".format(
                case_id=case["case_id"],
                cluster=config["cluster_count"],
                packet=config["packet_w"],
                banks=config["banks"],
                arb=config["arb_mode"],
                queue=config["req_queue_depth"],
                latency=config["read_latency"],
                done=integrated["completion_cycle"],
                penalty=integrated["service_penalty_cycles"],
                hash_gate="ok" if gate["hash_gate_ok"] else "fail",
                protocol_gate="ok" if gate["protocol_gate_ok"] else "fail",
                count_gate="ok" if gate["count_gate_ok"] else "fail",
                req_stall=counters["request_injection_stall_cycles"],
                router_arb=counters["arbitration_contention_cycles"],
                bank_conflict=counters["bank_conflict_count"],
                router_block=response_block["router"],
                service_block=response_block["service"],
                shared_arb=shared["arbitration_contention_cycles"],
                shared_block=shared["egress_block_cycles"],
                router_req=occupancy["router_req"],
                router_resp=occupancy["router_resp"],
                service_req=occupancy["service_req"],
                service_resp=occupancy["service_resp"],
            )
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--out-md", type=Path)
    parser.add_argument("--proposal-id")
    parser.add_argument("--proposal-path")
    parser.add_argument("--depends-on-item-id", action="append", default=[])
    args = parser.parse_args()
    config = None
    if args.config is not None:
        config_payload = json.loads(args.config.read_text(encoding="utf-8"))
        if not isinstance(config_payload, dict):
            raise SystemExit("config must decode to a JSON object")
        config = config_payload
    report = build_report(
        config,
        proposal_id=str(args.proposal_id or "").strip() or None,
        proposal_path=str(args.proposal_path or "").strip() or None,
        depends_on_item_ids=[str(item).strip() for item in args.depends_on_item_id if str(item).strip()],
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.out_md is not None:
        args.out_md.parent.mkdir(parents=True, exist_ok=True)
        args.out_md.write_text(_build_markdown(report), encoding="utf-8")
    return 0 if report["decision"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
