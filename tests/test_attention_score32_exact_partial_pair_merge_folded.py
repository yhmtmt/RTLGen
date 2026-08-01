import json
import math
import os
from pathlib import Path
import random
import re
import shutil
import subprocess
import sys

import pytest

from npu.eval.probe_attention_score32_exact_partial_pair_merge_folded import build_report
from npu.rtlgen.gen_attention_decode_score_multivalue_cluster import generate as generate_cluster
from npu.rtlgen.gen_attention_score32_exact_partial_pair_merge_folded import (
    FACTORED_H33_L64_MUL_EXACT,
    MAX_EXP_BUCKET,
    exact_exp_scale_value,
    generate as generate_merge,
)
from npu.rtlgen.gen_attention_two_pass_multivalue_stream import generate as generate_reducer
from npu.sim.perf.attention_exact_partial import (
    ExactPartialBeat,
    folded_exact_partial_pair_merge_capture_to_output_latency_cycles,
    folded_exact_partial_pair_merge_compute_launch_interval_cycles,
    folded_exact_partial_pair_merge_compute_launch_to_output_latency_cycles,
    merge_partial_beats,
    pack_numerators,
    simulate_folded_exact_partial_pair_merge_service,
    unpack_numerators,
)

INT_MAX = (1 << 31) - 1
INT_MIN = -(1 << 31)
REPO_ROOT = Path(__file__).resolve().parents[1]


def _partial_cluster_config() -> dict:
    return {
        "top_name": "attention_decode_score_multivalue_cluster_exact_partial",
        "attention_decode_score_multivalue_cluster": {
            "max_blocks": 16,
            "array_n": 8,
            "value_slices": 16,
            "divider_impl": "iterative_restoring",
            "score_scale_lanes_per_cycle": 1,
            "result_mode": "exact_partial",
            "head_id_bits": 5,
        },
    }


def _partial_reducer_config() -> dict:
    return {
        "top_name": "attention_two_pass_multivalue_stream_exact_partial",
        "attention_two_pass_multivalue_stream": {
            "max_blocks": 16,
            "value_slices": 16,
            "divider_impl": "iterative_restoring",
            "result_mode": "exact_partial",
            "head_id_bits": 5,
        },
    }


def _merge_config() -> dict:
    return {
        "top_name": "attention_score32_online_state_merge_exact_partial",
        "attention_score32_exact_partial_pair_merge_folded": {
            "value_slices": 16,
            "head_id_bits": 5,
            "exp_scale_impl": FACTORED_H33_L64_MUL_EXACT,
            "lane_parallelism": 1,
        },
    }


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


def _signed_literal(value: int, bits: int) -> str:
    return f"-{bits}'sd{abs(value)}" if value < 0 else f"{bits}'sd{value}"


def _merge_beat(
    *,
    command_id: int = 0x4A21,
    head_id: int = 3,
    slice_index: int = 0,
    last: bool = False,
    max_score: int,
    exp_sum: int,
    numerators: tuple[int, ...],
) -> ExactPartialBeat:
    return ExactPartialBeat(
        command_id=command_id,
        head_id=head_id,
        slice_index=slice_index,
        last=last,
        max_score=max_score,
        exp_sum=exp_sum,
        numerators=numerators,
    )


def _base_merge_cases() -> list[tuple[str, ExactPartialBeat, ExactPartialBeat, bool]]:
    return [
        (
            "extreme_left",
            _merge_beat(
                max_score=INT_MAX,
                exp_sum=37,
                numerators=(31, -29, 23, -19, 17, -13, 11, -7),
            ),
            _merge_beat(
                max_score=INT_MIN,
                exp_sum=41,
                numerators=(-101, 99, -77, 55, -33, 22, -11, 9),
            ),
            False,
        ),
        (
            "extreme_right",
            _merge_beat(
                max_score=INT_MIN,
                exp_sum=41,
                numerators=(-101, 99, -77, 55, -33, 22, -11, 9),
            ),
            _merge_beat(
                max_score=INT_MAX,
                exp_sum=37,
                numerators=(31, -29, 23, -19, 17, -13, 11, -7),
            ),
            False,
        ),
        (
            "near_left",
            _merge_beat(
                command_id=0x4A22,
                head_id=7,
                max_score=INT_MAX - 1,
                exp_sum=53,
                numerators=(17, -15, 13, -11, 9, -7, 5, -3),
            ),
            _merge_beat(
                command_id=0x4A22,
                head_id=7,
                max_score=INT_MIN + 1,
                exp_sum=29,
                numerators=(-63, 57, -51, 45, -39, 33, -27, 21),
            ),
            False,
        ),
        (
            "near_right",
            _merge_beat(
                command_id=0x4A22,
                head_id=7,
                max_score=INT_MIN + 1,
                exp_sum=29,
                numerators=(-63, 57, -51, 45, -39, 33, -27, 21),
            ),
            _merge_beat(
                command_id=0x4A22,
                head_id=7,
                max_score=INT_MAX - 1,
                exp_sum=53,
                numerators=(17, -15, 13, -11, 9, -7, 5, -3),
            ),
            False,
        ),
        (
            "invalid_last_semantics",
            _merge_beat(
                command_id=0x4A23,
                head_id=11,
                max_score=77,
                exp_sum=19,
                numerators=(9, -7, 5, -3, 1, -1, 2, -2),
            ),
            _merge_beat(
                command_id=0x4A23,
                head_id=11,
                max_score=71,
                exp_sum=17,
                numerators=(-4, 6, -8, 10, -12, 14, -16, 18),
            ),
            True,
        ),
    ]


def _random_merge_cases(seed: int, count: int) -> list[tuple[str, ExactPartialBeat, ExactPartialBeat, bool]]:
    rng = random.Random(seed)
    cases: list[tuple[str, ExactPartialBeat, ExactPartialBeat, bool]] = []
    for index in range(count):
        command_id = 0x5000 + index
        head_id = rng.randrange(0, 32)
        slice_index = rng.randrange(0, 16)
        last = slice_index == 15
        left = _merge_beat(
            command_id=command_id,
            head_id=head_id,
            slice_index=slice_index,
            last=last,
            max_score=rng.randrange(INT_MIN, INT_MAX + 1),
            exp_sum=rng.randrange(0, (1 << 33) - 1),
            numerators=tuple(rng.randrange(-(1 << 40), 1 << 40) for _ in range(8)),
        )
        right = _merge_beat(
            command_id=command_id,
            head_id=head_id,
            slice_index=slice_index,
            last=last,
            max_score=rng.randrange(INT_MIN, INT_MAX + 1),
            exp_sum=rng.randrange(0, (1 << 33) - 1),
            numerators=tuple(rng.randrange(-(1 << 40), 1 << 40) for _ in range(8)),
        )
        cases.append((f"random_{index}", left, right, False))
    return cases


def _run_merge_rtl_cases(tmp_path: Path, valid_cases: list[tuple[str, ExactPartialBeat, ExactPartialBeat, bool]]) -> dict[str, object]:
    expected_rows = []
    for index, (name, left, right, invalid_last) in enumerate(valid_cases):
        merged = merge_partial_beats(left, right)
        expected_rows.append(
            {
                "index": index,
                "name": name,
                "command_id": merged.command_id,
                "head_id": merged.head_id,
                "slice": merged.slice_index,
                "last": True if invalid_last else merged.last,
                "global_max": merged.max_score,
                "exp_sum": merged.exp_sum,
                "value": list(merged.numerators),
                "expect_protocol_error": invalid_last,
            }
        )

    generate_merge(_merge_config(), tmp_path / "rtl")
    tb_path = tmp_path / "tb.sv"
    left_init = []
    right_init = []
    for index, (_, left, right, invalid_last) in enumerate(valid_cases):
        left_init.append(
            f"    l_cmd[{index}] = 16'h{left.command_id:04x}; l_head[{index}] = 5'd{left.head_id}; "
            f"l_max[{index}] = {_signed_literal(left.max_score, 32)}; l_sum[{index}] = 33'd{left.exp_sum}; "
            f"l_slice[{index}] = 4'd{left.slice_index}; l_last[{index}] = 1'b{1 if invalid_last else int(left.last)}; "
            f"l_value[{index}] = 328'h{pack_numerators(left.numerators):082x};"
        )
        right_init.append(
            f"    r_cmd[{index}] = 16'h{right.command_id:04x}; r_head[{index}] = 5'd{right.head_id}; "
            f"r_max[{index}] = {_signed_literal(right.max_score, 32)}; r_sum[{index}] = 33'd{right.exp_sum}; "
            f"r_slice[{index}] = 4'd{right.slice_index}; r_last[{index}] = 1'b{1 if invalid_last else int(right.last)}; "
            f"r_value[{index}] = 328'h{pack_numerators(right.numerators):082x};"
        )
    tb_path.write_text(
        f"""`timescale 1ns/1ps
module tb;
  localparam integer CASE_COUNT = {len(valid_cases)};
  reg clk = 0, rst_n = 0;
  reg [15:0] l_cmd [0:CASE_COUNT-1];
  reg [4:0] l_head [0:CASE_COUNT-1];
  reg signed [31:0] l_max [0:CASE_COUNT-1];
  reg [32:0] l_sum [0:CASE_COUNT-1];
  reg [3:0] l_slice [0:CASE_COUNT-1];
  reg l_last [0:CASE_COUNT-1];
  reg [327:0] l_value [0:CASE_COUNT-1];
  reg [15:0] r_cmd [0:CASE_COUNT-1];
  reg [4:0] r_head [0:CASE_COUNT-1];
  reg signed [31:0] r_max [0:CASE_COUNT-1];
  reg [32:0] r_sum [0:CASE_COUNT-1];
  reg [3:0] r_slice [0:CASE_COUNT-1];
  reg r_last [0:CASE_COUNT-1];
  reg [327:0] r_value [0:CASE_COUNT-1];
  reg left_valid, right_valid, out_ready;
  wire left_ready, right_ready, out_valid, out_last, protocol_error;
  wire [15:0] out_command_id;
  wire [4:0] out_head_id;
  wire signed [31:0] out_global_max;
  wire [32:0] out_exp_sum;
  wire [3:0] out_slice;
  wire [327:0] out_value;
  wire [31:0] completed_count, cycle_count;
  integer cycle = 0, issue = 0, seen = 0, launch_seen = 0, output_valid_seen = 0;
  reg pending_summary = 0;

  always #5 clk = ~clk;

  attention_score32_online_state_merge_exact_partial dut (
      .clk(clk), .rst_n(rst_n),
      .left_valid(left_valid), .left_ready(left_ready), .left_command_id(l_cmd[issue]),
      .left_head_id(l_head[issue]), .left_global_max(l_max[issue]), .left_exp_sum(l_sum[issue]),
      .left_slice(l_slice[issue]), .left_last(l_last[issue]), .left_value(l_value[issue]),
      .right_valid(right_valid), .right_ready(right_ready), .right_command_id(r_cmd[issue]),
      .right_head_id(r_head[issue]), .right_global_max(r_max[issue]), .right_exp_sum(r_sum[issue]),
      .right_slice(r_slice[issue]), .right_last(r_last[issue]), .right_value(r_value[issue]),
      .out_valid(out_valid), .out_ready(out_ready), .out_command_id(out_command_id), .out_head_id(out_head_id),
      .out_global_max(out_global_max), .out_exp_sum(out_exp_sum), .out_slice(out_slice), .out_last(out_last),
      .out_value(out_value), .completed_count(completed_count), .cycle_count(cycle_count), .protocol_error(protocol_error)
  );

  always @* begin
    left_valid = rst_n && issue < CASE_COUNT;
    right_valid = rst_n && issue < CASE_COUNT;
    out_ready = (cycle % 5) != 2;
  end

  always @(posedge clk) begin
    if (!rst_n) begin
      cycle <= 0;
      issue <= 0;
      seen <= 0;
      launch_seen <= 0;
      output_valid_seen <= 0;
      pending_summary <= 0;
    end else begin
      cycle <= cycle + 1;
      if (left_valid && left_ready && right_valid && right_ready) begin
        $display("ACCEPT idx=%0d cycle=%0d", issue, cycle);
        issue <= issue + 1;
      end
      if (dut.start_pair) begin
        $display("LAUNCH idx=%0d cycle=%0d", launch_seen, cycle);
        launch_seen <= launch_seen + 1;
      end
      if (out_valid && output_valid_seen == seen) begin
        $display("OUTPUT_VALID idx=%0d cycle=%0d", seen, cycle);
        output_valid_seen <= output_valid_seen + 1;
      end
      if (out_valid && out_ready) begin
        $display("RESULT idx=%0d cycle=%0d cmd=%0d head=%0d slice=%0d last=%0d max=%0d sum=%0d value=%082x",
                 seen, cycle, out_command_id, out_head_id, out_slice, out_last, $signed(out_global_max), out_exp_sum, out_value);
        seen <= seen + 1;
        if (seen + 1 == CASE_COUNT) pending_summary <= 1;
      end
      if (pending_summary) begin
        $display("SUMMARY completed=%0d cycle=%0d protocol_error=%0d", completed_count, cycle_count, protocol_error);
        #1 $finish;
      end
      if (cycle > (CASE_COUNT * 32)) $fatal(1, "timeout");
    end
  end

  initial begin
{chr(10).join(left_init)}
{chr(10).join(right_init)}
    repeat (3) @(posedge clk); @(negedge clk); rst_n = 1;
  end
endmodule
""",
        encoding="utf-8",
    )
    simv = tmp_path / "simv"
    compiled = subprocess.run(
        [
            _tool("iverilog"),
            "-g2012",
            "-s",
            "tb",
            "-o",
            str(simv),
            str(tmp_path / "rtl" / "top.v"),
            str(tb_path),
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if compiled.returncode:
        raise RuntimeError(f"iverilog failed:\\n{compiled.stderr}")
    run = subprocess.run([_tool("vvp"), str(simv)], capture_output=True, text=True, timeout=60)
    if run.returncode:
        raise RuntimeError(f"simulation failed:\\n{run.stdout}\\n{run.stderr}")

    result_re = re.compile(
        r"RESULT idx=(\d+) cycle=(\d+) cmd=(\d+) head=(\d+) slice=(\d+) last=(\d+) max=(-?\d+) sum=(\d+) value=([0-9a-fA-F]+)"
    )
    accept_re = re.compile(r"ACCEPT idx=(\d+) cycle=(\d+)")
    launch_re = re.compile(r"LAUNCH idx=(\d+) cycle=(\d+)")
    output_valid_re = re.compile(r"OUTPUT_VALID idx=(\d+) cycle=(\d+)")
    summary_re = re.compile(r"SUMMARY completed=(\d+) cycle=(\d+) protocol_error=(\d+)")
    observed_rows = []
    accept_cycles = []
    launch_cycles = []
    output_valid_cycles = []
    summary = None
    for line in run.stdout.splitlines():
        if match := accept_re.fullmatch(line.strip()):
            assert int(match.group(1)) == len(accept_cycles)
            accept_cycles.append(int(match.group(2)))
        elif match := launch_re.fullmatch(line.strip()):
            assert int(match.group(1)) == len(launch_cycles)
            launch_cycles.append(int(match.group(2)))
        elif match := output_valid_re.fullmatch(line.strip()):
            assert int(match.group(1)) == len(output_valid_cycles)
            output_valid_cycles.append(int(match.group(2)))
        elif match := result_re.fullmatch(line.strip()):
            observed_rows.append(
                {
                    "index": int(match.group(1)),
                    "cycle": int(match.group(2)),
                    "command_id": int(match.group(3)),
                    "head_id": int(match.group(4)),
                    "slice": int(match.group(5)),
                    "last": bool(int(match.group(6))),
                    "global_max": int(match.group(7)),
                    "exp_sum": int(match.group(8)),
                    "value": list(unpack_numerators(int(match.group(9), 16))),
                }
            )
        elif match := summary_re.fullmatch(line.strip()):
            summary = {
                "completed": int(match.group(1)),
                "cycle": int(match.group(2)),
                "protocol_error": bool(int(match.group(3))),
            }
    if summary is None:
        raise RuntimeError("summary missing from direct merge RTL regression")
    return {
        "expected": expected_rows,
        "observed": observed_rows,
        "summary": summary,
        "accept_cycles": accept_cycles,
        "launch_cycles": launch_cycles,
        "output_valid_cycles": output_valid_cycles,
    }


def _run_direct_merge_rtl_vectors(tmp_path: Path) -> dict[str, object]:
    return _run_merge_rtl_cases(tmp_path, _base_merge_cases())


def test_exact_partial_reducer_manifest_and_ports(tmp_path: Path) -> None:
    generate_reducer(_partial_reducer_config(), tmp_path)

    manifest = json.loads(
        (tmp_path / "attention_two_pass_multivalue_stream_manifest.json").read_text(encoding="utf-8")
    )
    rtl = (tmp_path / "top.v").read_text(encoding="utf-8")

    assert manifest["result_mode"] == "exact_partial"
    assert manifest["semantic_profile"] == "q8_k8_v8_a32_s32_exp_lut_b20_shared_score_multivalue_exact_partial_v1"
    assert manifest["result_value_bits_per_beat"] == 328
    assert manifest["divider_cycles_per_command"] == 0
    assert manifest["equivalence_hash"] is False
    assert "input  wire [4:0] command_head_id" in rtl
    assert "output reg  [4:0] result_head_id" in rtl
    assert "output reg  [327:0] result_value" in rtl


def test_exact_partial_cluster_manifest_and_ports(tmp_path: Path) -> None:
    generate_cluster(_partial_cluster_config(), tmp_path)

    manifest = json.loads(
        (tmp_path / "attention_decode_score_multivalue_cluster_manifest.json").read_text(encoding="utf-8")
    )
    rtl = (tmp_path / "top.v").read_text(encoding="utf-8")

    assert manifest["result_mode"] == "exact_partial"
    assert manifest["semantic_profile"] == "decode_m1x8_shared_score_16x8d_value_exact_partial_v1"
    assert manifest["head_id_bits"] == 5
    assert manifest["result_value_bits_per_beat"] == 328
    assert manifest["equivalence_hash"] is False
    assert manifest["submodule_manifests"]["multivalue_reducer"]["result_mode"] == "exact_partial"
    assert "input  wire [4:0]  command_head_id" in rtl
    assert "output wire [4:0] result_head_id" in rtl
    assert "output wire [327:0] result_value" in rtl


def test_exact_partial_merge_manifest_and_ports(tmp_path: Path) -> None:
    generate_merge(_merge_config(), tmp_path)

    manifest = json.loads(
        (tmp_path / "attention_score32_exact_partial_pair_merge_folded_manifest.json").read_text(encoding="utf-8")
    )
    rtl = (tmp_path / "top.v").read_text(encoding="utf-8")

    assert manifest["semantic_profile"] == "score32_online_exact_partial_pair_merge_folded_sharedscale_v1"
    assert manifest["numerical_semantics"] == "score32_online_exact_partial_pair_merge_v1"
    assert manifest["partial_payload_bits_per_beat"] == 328
    assert manifest["equivalence_hash"] is False
    assert manifest["exp_scale_impl"] == FACTORED_H33_L64_MUL_EXACT
    assert manifest["exp_scale_bucket_max"] == MAX_EXP_BUCKET
    assert manifest["lane_parallelism"] == 1
    assert manifest["implementation_style"] == "shared_single_scale_folded_exact_v1"
    assert manifest["shared_signed_scale_datapaths"] == 1
    assert manifest["shared_unsigned_scale_datapaths"] == 1
    assert (
        manifest["pair_capture_to_output_latency_cycles"]
        == folded_exact_partial_pair_merge_capture_to_output_latency_cycles()
    )
    assert (
        manifest["pair_compute_launch_to_output_latency_cycles"]
        == folded_exact_partial_pair_merge_compute_launch_to_output_latency_cycles()
    )
    assert (
        manifest["pair_compute_launch_interval_cycles"]
        == folded_exact_partial_pair_merge_compute_launch_interval_cycles()
    )
    assert manifest["service_cycle_definition"] == "active_edge_preupdate_handshake_v1"
    assert manifest["output_cycle_event"] == "first_out_valid_handshake_opportunity"
    assert manifest["exp_factor_step"] == 64
    assert manifest["exp_factor_high_entries"] == 33
    assert manifest["exp_factor_low_entries"] == 64
    assert "input  wire [4:0] left_head_id" in rtl
    assert "output wire [4:0] out_head_id" in rtl
    assert "output wire [327:0] out_value" in rtl
    assert "function automatic [36:0] exp_lut_high;" in rtl
    assert "function automatic [30:0] exp_lut_low;" in rtl
    assert "product = high_scale * low_scale;" in rtl
    assert "exp_lut = rounded_product >> 43;" in rtl
    assert f"if (bucket > 33'd{MAX_EXP_BUCKET}) begin" in rtl
    assert "localparam [2:0] PHASE_EXP_SUM_LEFT = 3'd1;" in rtl
    assert "localparam [2:0] PHASE_LANE_RIGHT = 3'd4;" in rtl
    assert rtl.count("scale_signed41(shared_signed_value_r, shared_signed_scale_r)") == 1
    assert rtl.count("scale_unsigned33(shared_unsigned_value_r, shared_unsigned_scale_r)") == 1
    assert "active_scaled_left_lane_q <= shared_signed_scaled_w;" in rtl
    assert "active_scaled_left_exp_sum_q <= shared_unsigned_scaled_w;" in rtl


def test_exact_partial_merge_python_exp_scale_matches_legacy_formula_exhaustively() -> None:
    expected = [
        max(1, int(math.exp(-(bucket / 256.0)) * ((1 << 24) - 1) + 0.5))
        for bucket in range(MAX_EXP_BUCKET + 1)
    ]
    observed = [exact_exp_scale_value(bucket) for bucket in range(MAX_EXP_BUCKET + 1)]
    assert observed == expected
    assert exact_exp_scale_value(-1) == 0
    assert exact_exp_scale_value(MAX_EXP_BUCKET + 1) == 0


@pytest.mark.skipif(not _rtl_tools_available(), reason="iverilog/vvp/verilator unavailable")
def test_exact_partial_merge_rtl_exp_scale_matches_python_exhaustively(tmp_path: Path) -> None:
    generate_merge(_merge_config(), tmp_path / "rtl")
    tb_path = tmp_path / "tb_exp_scale.sv"
    expected_json = json.dumps({str(bucket): exact_exp_scale_value(bucket) for bucket in range(MAX_EXP_BUCKET + 1)}, sort_keys=True)
    tb_path.write_text(
        f"""`timescale 1ns/1ps
module tb;
  localparam integer MAX_BUCKET = {MAX_EXP_BUCKET};
  localparam integer MERGE_SCALE = 24'hffffff;
  reg clk = 0, rst_n = 0;
  reg left_valid = 0, right_valid = 0, out_ready = 1;
  reg [15:0] left_command_id = 16'h0021, right_command_id = 16'h0021;
  reg [4:0] left_head_id = 5'd2, right_head_id = 5'd2;
    reg signed [31:0] left_global_max = 32'sd0, right_global_max = 32'sd0;
  reg [32:0] left_exp_sum = 33'd0, right_exp_sum = 33'd0;
  reg [3:0] left_slice = 4'd0, right_slice = 4'd0;
  reg left_last = 1'b0, right_last = 1'b0;
  reg [327:0] left_value = 328'd0, right_value = 328'd0;
  wire left_ready, right_ready, out_valid, out_last, protocol_error;
  wire [15:0] out_command_id;
  wire [4:0] out_head_id;
  wire signed [31:0] out_global_max;
  wire [32:0] out_exp_sum;
  wire [3:0] out_slice;
  wire [327:0] out_value;
  wire [31:0] completed_count, cycle_count;
    integer bucket;
    localparam integer OUT_OF_RANGE_SENTINEL = 4096;

  always #5 clk = ~clk;

  attention_score32_online_state_merge_exact_partial dut (
      .clk(clk), .rst_n(rst_n),
      .left_valid(left_valid), .left_ready(left_ready), .left_command_id(left_command_id),
      .left_head_id(left_head_id), .left_global_max(left_global_max), .left_exp_sum(left_exp_sum),
      .left_slice(left_slice), .left_last(left_last), .left_value(left_value),
      .right_valid(right_valid), .right_ready(right_ready), .right_command_id(right_command_id),
      .right_head_id(right_head_id), .right_global_max(right_global_max), .right_exp_sum(right_exp_sum),
      .right_slice(right_slice), .right_last(right_last), .right_value(right_value),
      .out_valid(out_valid), .out_ready(out_ready), .out_command_id(out_command_id),
      .out_head_id(out_head_id), .out_global_max(out_global_max), .out_exp_sum(out_exp_sum),
      .out_slice(out_slice), .out_last(out_last), .out_value(out_value),
      .completed_count(completed_count), .cycle_count(cycle_count), .protocol_error(protocol_error)
  );

  task automatic drive_case(input integer bucket_value);
    begin
      @(negedge clk);
      left_global_max = -bucket_value * 32'sd1048576;
      right_global_max = 32'sd0;
      left_exp_sum = 33'd16777215;
      right_exp_sum = 33'd0;
      left_valid = 1'b1;
      right_valid = 1'b1;
      while (!(left_ready && right_ready)) begin
        @(negedge clk);
      end
      @(negedge clk);
      left_valid = 1'b0;
      right_valid = 1'b0;
      while (!out_valid) begin
        @(posedge clk);
      end
      $display("BUCKET=%0d SCALE=%0d", bucket_value, out_exp_sum);
      @(posedge clk);
    end
  endtask

  initial begin
    repeat (2) @(negedge clk);
    rst_n = 1'b1;
    for (bucket = 0; bucket <= MAX_BUCKET; bucket = bucket + 1) begin
      drive_case(bucket);
    end
    @(negedge clk);
    left_global_max = -32'sd2147483648;
    right_global_max = 32'sd2147483647;
    left_exp_sum = 33'd16777215;
    right_exp_sum = 33'd0;
    left_valid = 1'b1;
    right_valid = 1'b1;
    while (!(left_ready && right_ready)) begin
      @(negedge clk);
    end
    @(negedge clk);
    left_valid = 1'b0;
    right_valid = 1'b0;
    while (!out_valid) begin
      @(posedge clk);
    end
    $display("BUCKET=%0d SCALE=%0d", OUT_OF_RANGE_SENTINEL, out_exp_sum);
    $finish;
  end
endmodule
""",
        encoding="utf-8",
    )

    sim_out = tmp_path / "sim.out"
    compile_run = subprocess.run(
        [
            _tool("iverilog"),
            "-g2012",
            "-o",
            str(sim_out),
            str(tb_path),
            str(tmp_path / "rtl" / "top.v"),
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        timeout=120,
    )
    assert compile_run.returncode == 0, compile_run.stderr or compile_run.stdout
    run = subprocess.run(
        [_tool("vvp"), str(sim_out)],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        timeout=120,
    )
    assert run.returncode == 0, run.stderr or run.stdout

    observed: dict[int, int] = {}
    pattern = re.compile(r"BUCKET=(\d+) SCALE=(\d+)")
    for line in run.stdout.splitlines():
        match = pattern.search(line)
        if match:
            observed[int(match.group(1))] = int(match.group(2))

    expected = {bucket: exact_exp_scale_value(bucket) for bucket in range(MAX_EXP_BUCKET + 1)}
    expected[4096] = 0
    assert observed == expected, json.dumps({"expected": expected_json, "observed": observed}, indent=2, sort_keys=True)


@pytest.mark.skipif(not _rtl_tools_available(), reason="iverilog/vvp/verilator unavailable")
def test_exact_partial_merge_rtl_handles_extreme_and_invalid_last_vectors(tmp_path: Path) -> None:
    report = _run_direct_merge_rtl_vectors(tmp_path)

    clean_observed = [{key: value for key, value in row.items() if key != "cycle"} for row in report["observed"]]
    assert clean_observed == [
        {
            key: value
            for key, value in row.items()
            if key != "name" and key != "expect_protocol_error"
        }
        for row in report["expected"]
    ]
    assert report["summary"]["completed"] == len(report["expected"])
    assert report["summary"]["protocol_error"] is True


@pytest.mark.skipif(not _rtl_tools_available(), reason="iverilog/vvp/verilator unavailable")
def test_exact_partial_merge_rtl_randomized_matches_python(tmp_path: Path) -> None:
    cases = _random_merge_cases(seed=7, count=12)
    report = _run_merge_rtl_cases(tmp_path, cases)

    clean_observed = [{key: value for key, value in row.items() if key != "cycle"} for row in report["observed"]]
    assert clean_observed == [
        {
            key: value
            for key, value in row.items()
            if key != "name" and key != "expect_protocol_error"
        }
        for row in report["expected"]
    ]
    assert report["summary"]["protocol_error"] is False


@pytest.mark.skipif(not _rtl_tools_available(), reason="iverilog/vvp/verilator unavailable")
def test_exact_partial_merge_service_contract_matches_rtl_backpressure(tmp_path: Path) -> None:
    cases = _random_merge_cases(seed=11, count=6)
    report = _run_merge_rtl_cases(tmp_path, cases)
    schedule = simulate_folded_exact_partial_pair_merge_service(
        pair_count=len(cases),
        output_ready_pattern=(True, True, False, True, True),
    )

    observed_cycles = [row["cycle"] for row in report["observed"]]
    assert report["accept_cycles"] == schedule["accept_cycles"]
    assert report["launch_cycles"] == schedule["launch_cycles"]
    assert report["output_valid_cycles"] == schedule["output_valid_cycles"]
    assert observed_cycles == schedule["output_fire_cycles"]
    assert (
        schedule["capture_to_output_latency_cycles"]
        == folded_exact_partial_pair_merge_capture_to_output_latency_cycles()
    )
    assert (
        schedule["compute_launch_to_output_latency_cycles"]
        == folded_exact_partial_pair_merge_compute_launch_to_output_latency_cycles()
    )
    assert (
        schedule["compute_launch_interval_cycles"]
        == folded_exact_partial_pair_merge_compute_launch_interval_cycles()
    )


@pytest.mark.skipif(not _rtl_tools_available(), reason="iverilog/vvp/verilator unavailable")
def test_score32_exact_partial_pair_probe_passes() -> None:
    report = build_report()

    assert report["decision"] == "pass", json.dumps(report, indent=2)
    assert report["equivalence_pass"] is True
    assert report["cluster_result_count"] == [48, 48]
    assert report["merge_result_count"] == 48
    assert report["summary"]["c0_accept"] == 3
    assert report["summary"]["c1_accept"] == 3
    assert report["summary"]["c0_complete"] == 3
    assert report["summary"]["c1_complete"] == 3
    assert report["summary"]["merge_complete"] == 48
    assert report["cluster_hashes"] == report["expected"]["cluster_hashes"]
    assert report["merge_hash"] == report["expected"]["merge_hash"]


@pytest.mark.skipif(not _rtl_tools_available(), reason="iverilog/vvp/verilator unavailable")
def test_score32_exact_partial_pair_probe_cli_bootstraps_repo_root(tmp_path: Path) -> None:
    out_path = tmp_path / "probe.json"
    env = {
        "HOME": os.environ.get("HOME", str(tmp_path)),
        "LANG": os.environ.get("LANG", "C.UTF-8"),
        "PATH": os.environ.get("PATH", ""),
    }

    run = subprocess.run(
        [
            sys.executable,
            "npu/eval/probe_attention_score32_exact_partial_pair_merge_folded.py",
            "--out",
            str(out_path),
        ],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )

    assert run.returncode == 0, run.stderr or run.stdout
    assert out_path.exists()
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["decision"] == "pass"
    assert payload["equivalence_pass"] is True
    assert payload["semantic_profile"] == "score32_online_exact_partial_pair_merge_folded_sharedscale_v1"
