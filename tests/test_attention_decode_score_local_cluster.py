import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.rtlgen.gen_attention_decode_score_local_cluster import generate, requantize_s32


def _config(*, top_name: str = "attention_decode_score_local_cluster_smoke", max_blocks: int = 16, scale_lanes: int = 1) -> dict:
    return {
        "top_name": top_name,
        "attention_decode_score_local_cluster": {
            "max_blocks": max_blocks,
            "array_n": 8,
            "divider_impl": "iterative_restoring",
            "score_scale_lanes_per_cycle": scale_lanes,
        },
    }


def _iverilog() -> str | None:
    return shutil.which("iverilog") or ("/oss-cad-suite/bin/iverilog" if Path("/oss-cad-suite/bin/iverilog").exists() else None)


def _exp_lut(bucket: int) -> int:
    import math

    return max(1, int(math.exp(-(bucket / 256.0)) * 65535 + 0.5))


def _reference_result(score_rows: list[list[int]], value_rows: list[list[int]]) -> tuple[int, int, list[int]]:
    global_max = max(max(row) for row in score_rows)
    exp_sum = 0
    numerators = [0] * 8
    for row_scores, row_values in zip(score_rows, value_rows):
        for row_idx, score_lane in enumerate(row_scores):
            delta_score = global_max - score_lane
            if delta_score < 0:
                delta_score = 0
            bucket = (delta_score + 524288) >> 20
            weight = _exp_lut(bucket)
            exp_sum += weight
            for dim_idx in range(8):
                numerators[dim_idx] += row_values[row_idx * 8 + dim_idx] * weight
    result_value = []
    for numerator in numerators:
        magnitude = abs(numerator)
        quotient = ((magnitude * 65535) + (exp_sum >> 1)) // exp_sum
        result_value.append(-quotient if numerator < 0 else quotient)
    return global_max, exp_sum, result_value


def _verilog_signed_literal(value: int, bits: int) -> str:
    if value < 0:
        return f"-{bits}'sd{abs(value)}"
    return f"{bits}'sd{value}"


def test_requantize_s32_rounding_and_saturation_edges() -> None:
    assert requantize_s32(7, 3, 0) == 21
    assert requantize_s32(7, 3, 1) == 11
    assert requantize_s32(-7, 3, 1) == -11
    assert requantize_s32(5, 1, 1) == 3
    assert requantize_s32(-5, 1, 1) == -3
    assert requantize_s32((1 << 31) - 1, 2, 0) == (1 << 31) - 1
    assert requantize_s32(-(1 << 31), 2, 0) == -(1 << 31)


def test_attention_decode_score_local_cluster_manifest_and_structure(tmp_path: Path) -> None:
    generate(_config(max_blocks=16384), tmp_path)

    text = (tmp_path / "top.v").read_text(encoding="utf-8")
    manifest = json.loads((tmp_path / "attention_decode_score_local_cluster_manifest.json").read_text(encoding="utf-8"))

    assert manifest["semantic_profile"] == "decode_m1x8_score_sram_two_pass_iterdiv_v1"
    assert manifest["score_tile_result_mode"] == "packed_score_row"
    assert manifest["score_bank_macro_count"] == 56
    assert manifest["value_replay"] == "external_ready_valid_address_matched"
    assert manifest["divider_impl"] == "iterative_restoring"
    assert manifest["score_scale_lanes_per_cycle"] == 1
    assert "u_score_tile" in text
    assert "u_score_bank" in text
    assert "u_two_pass" in text
    assert "score_write_valid" in text
    assert "score_write_ready" in text
    assert "score_write_addr" in text
    assert "score_write_data" in text
    assert "score_response_valid" in text
    assert "value_read_req_valid" in text
    assert "value_response_valid" in text
    assert ".fill_score_row(two_pass_fill_score_row)" in text
    assert ".fill_score_row(tile_result_score_row)" not in text
    assert text.count("fakeram45_2048x39 u_group_") == 56


def test_attention_decode_score_local_cluster_generator_compiles(tmp_path: Path) -> None:
    iverilog = _iverilog()
    if not iverilog:
        pytest.skip("iverilog unavailable")

    generate(_config(), tmp_path)
    subprocess.run(
        [
            iverilog,
            "-g2012",
            "-s",
            "attention_decode_score_local_cluster_smoke",
            "-o",
            str(tmp_path / "simv"),
            str(tmp_path / "top.v"),
            str(REPO_ROOT / "npu" / "rtl" / "fakeram45_2048x39_blackbox.v"),
        ],
        check=True,
        capture_output=True,
        text=True,
    )


def test_attention_decode_score_local_cluster_guard_accepts_generated_design(tmp_path: Path) -> None:
    design_dir = tmp_path / "design"
    design_dir.mkdir()
    config = _config(top_name="attention_decode_score_local_cluster_guard", max_blocks=16384)
    (design_dir / "config.json").write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    (design_dir / "macro_manifest.json").write_text(
        json.dumps(
            {
                "version": "0.1",
                "design_id": "attention_decode_score_local_cluster_guard",
                "module": "attention_decode_score_local_cluster_guard",
                "platform": "nangate45",
                "flow_variant": "decode_score_local_cluster_v1",
                "blackboxes": ["fakeram45_2048x39"],
                "additional_lefs": ["/orfs/flow/platforms/nangate45/lef/fakeram45_2048x39.lef"],
                "additional_libs": ["/orfs/flow/platforms/nangate45/lib/fakeram45_2048x39.lib"],
                "additional_gds": [],
                "blackbox_verilog": ["npu/rtl/fakeram45_2048x39_blackbox.v"],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    generate(config, design_dir / "verilog")

    subprocess.run(
        [sys.executable, "npu/eval/check_attention_decode_score_local_cluster_guard.py", "--design-dir", str(design_dir)],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )


def test_attention_decode_score_local_cluster_end_to_end_protocol(tmp_path: Path) -> None:
    iverilog = _iverilog()
    if not iverilog:
        pytest.skip("iverilog unavailable")

    design_dir = tmp_path / "design"
    generate(_config(top_name="attention_decode_score_local_cluster_tb", max_blocks=16), design_dir)

    q_values = [3, -2]
    k_rows = [
        [4, 1, -3, 2, -5, 6, -7, 8],
        [-1, 2, 3, -4, 5, -6, 7, -8],
    ]
    multiplier = 5
    shift = 1
    score_rows = [[requantize_s32(q * k, multiplier, shift) for k in row] for q, row in zip(q_values, k_rows)]
    value_rows = [
        [
            1, 2, 3, 4, 5, 6, 7, 8,
            -1, -2, -3, -4, -5, -6, -7, -8,
            2, 3, 4, 5, 6, 7, 8, 9,
            -2, -3, -4, -5, -6, -7, -8, -9,
            3, 4, 5, 6, 7, 8, 9, 10,
            -3, -4, -5, -6, -7, -8, -9, -10,
            4, 5, 6, 7, 8, 9, 10, 11,
            -4, -5, -6, -7, -8, -9, -10, -11,
        ],
        [
            5, 4, 3, 2, 1, 0, -1, -2,
            6, 5, 4, 3, 2, 1, 0, -1,
            7, 6, 5, 4, 3, 2, 1, 0,
            8, 7, 6, 5, 4, 3, 2, 1,
            -5, -4, -3, -2, -1, 0, 1, 2,
            -6, -5, -4, -3, -2, -1, 0, 1,
            -7, -6, -5, -4, -3, -2, -1, 0,
            -8, -7, -6, -5, -4, -3, -2, -1,
        ],
    ]
    expected_global_max, expected_exp_sum, expected_result = _reference_result(score_rows, value_rows)

    packed_values = []
    for row in value_rows:
        packed = 0
        for idx, value in enumerate(row):
            packed |= ((value & 0xFF) << (idx * 8))
        packed_values.append(packed)

    expected_value_packed = 0
    for idx, value in enumerate(expected_result):
        expected_value_packed |= ((value & ((1 << 40) - 1)) << (idx * 40))
    packed_k0 = sum((k & 0xFF) << (idx * 8) for idx, k in enumerate(k_rows[0]))
    packed_k1 = sum((k & 0xFF) << (idx * 8) for idx, k in enumerate(k_rows[1]))

    tb_text = f"""`timescale 1ns/1ps
module fakeram45_2048x39 (
    output wire [38:0] rd_out,
    input  wire [10:0] addr_in,
    input  wire        we_in,
    input  wire [38:0] wd_in,
    input  wire [38:0] w_mask_in,
    input  wire        clk,
    input  wire        ce_in
);
  reg [38:0] mem [0:2047];
  reg [10:0] addr_q;
  reg [38:0] rd_out_q;
  integer idx;
  integer bit_idx;

  initial begin
    addr_q = 11'd0;
    rd_out_q = 39'd0;
    for (idx = 0; idx < 2048; idx = idx + 1)
      mem[idx] = 39'd0;
  end

  always @(posedge clk) begin
    rd_out_q <= mem[addr_q];
    if (ce_in) begin
      if (we_in) begin
        for (bit_idx = 0; bit_idx < 39; bit_idx = bit_idx + 1) begin
          if (w_mask_in[bit_idx])
            mem[addr_in][bit_idx] <= wd_in[bit_idx];
        end
      end
      addr_q <= addr_in;
    end
  end

  assign rd_out = rd_out_q;
endmodule

module tb;
  reg clk;
  reg rst_n;
  reg command_valid;
  wire command_ready;
  reg [15:0] command_id;
  reg [14:0] command_block_count;
  reg [31:0] command_score_multiplier;
  reg [5:0] command_score_shift;
  reg input_valid;
  wire input_ready;
  reg input_last;
  reg signed [7:0] input_a;
  reg signed [63:0] input_b;
  wire value_read_req_valid;
  reg value_read_req_ready;
  wire [13:0] value_read_req_address;
  reg value_response_valid;
  reg [13:0] value_response_address;
  reg [511:0] value_response_matrix;
  wire result_valid;
  reg result_ready;
  wire [15:0] result_command_id;
  wire signed [31:0] result_global_max;
  wire [32:0] result_exp_sum;
  wire [319:0] result_value;
  wire [31:0] accepted_count;
  wire [31:0] completed_count;
  wire [31:0] cycle_count;
  wire protocol_error;

  reg [511:0] expected_values [0:1];
  reg [13:0] captured_addrs [0:1];
  integer req_count;
  integer rsp_delay;
  reg pending_rsp;
  reg [13:0] pending_addr;

  attention_decode_score_local_cluster_tb dut (
      .clk(clk),
      .rst_n(rst_n),
      .command_valid(command_valid),
      .command_ready(command_ready),
      .command_id(command_id),
      .command_block_count(command_block_count),
      .command_score_multiplier(command_score_multiplier),
      .command_score_shift(command_score_shift),
      .input_valid(input_valid),
      .input_ready(input_ready),
      .input_last(input_last),
      .input_a(input_a),
      .input_b(input_b),
      .value_read_req_valid(value_read_req_valid),
      .value_read_req_ready(value_read_req_ready),
      .value_read_req_address(value_read_req_address),
      .value_response_valid(value_response_valid),
      .value_response_address(value_response_address),
      .value_response_matrix(value_response_matrix),
      .result_valid(result_valid),
      .result_ready(result_ready),
      .result_command_id(result_command_id),
      .result_global_max(result_global_max),
      .result_exp_sum(result_exp_sum),
      .result_value(result_value),
      .accepted_count(accepted_count),
      .completed_count(completed_count),
      .cycle_count(cycle_count),
      .protocol_error(protocol_error)
  );

  always #5 clk = ~clk;

  task automatic drive_idle;
    begin
      command_valid = 1'b0;
      input_valid = 1'b0;
      input_last = 1'b0;
      input_a = '0;
      input_b = '0;
    end
  endtask

  task automatic send_block(input signed [7:0] q, input signed [63:0] packed_k);
    begin
      @(negedge clk);
      input_valid = 1'b1;
      input_last = 1'b1;
      input_a = q;
      input_b = packed_k;
      while (!(input_valid && input_ready)) begin
        @(posedge clk);
        @(negedge clk);
      end
      @(posedge clk);
      #1;
      drive_idle();
    end
  endtask

  initial begin
    expected_values[0] = 512'h{packed_values[0]:0128x};
    expected_values[1] = 512'h{packed_values[1]:0128x};
    clk = 1'b0;
    rst_n = 1'b0;
    command_valid = 1'b0;
    command_id = 16'h0021;
    command_block_count = 15'd2;
    command_score_multiplier = 32'd{multiplier};
    command_score_shift = 6'd{shift};
    input_valid = 1'b0;
    input_last = 1'b0;
    input_a = '0;
    input_b = '0;
    value_read_req_ready = 1'b1;
    value_response_valid = 1'b0;
    value_response_address = 14'd0;
    value_response_matrix = 512'd0;
    result_ready = 1'b1;
    req_count = 0;
    rsp_delay = 0;
    pending_rsp = 1'b0;
    pending_addr = 14'd0;

    repeat (2) @(posedge clk);
    rst_n = 1'b1;

    @(negedge clk);
    command_valid = 1'b1;
    if (!command_ready) begin
      $display("FAIL command not ready");
      $finish(1);
    end
    @(posedge clk);
    #1;
    command_valid = 1'b0;

    send_block({_verilog_signed_literal(q_values[0], 8)}, 64'h{packed_k0:016x});
    send_block({_verilog_signed_literal(q_values[1], 8)}, 64'h{packed_k1:016x});

    wait (result_valid === 1'b1);
    #1;
    if (result_command_id !== 16'h0021) begin
      $display("FAIL result command id mismatch");
      $finish(1);
    end
    if (result_global_max !== 32'sd{expected_global_max}) begin
      $display("FAIL global max mismatch expected=%0d got=%0d", 32'sd{expected_global_max}, result_global_max);
      $finish(1);
    end
    if (result_exp_sum !== 33'd{expected_exp_sum}) begin
      $display("FAIL exp sum mismatch expected=%0d got=%0d", 33'd{expected_exp_sum}, result_exp_sum);
      $finish(1);
    end
    if (result_value !== 320'h{expected_value_packed:080x}) begin
      $display("FAIL result value mismatch expected=%h got=%h", 320'h{expected_value_packed:080x}, result_value);
      $finish(1);
    end
    if (protocol_error) begin
      $display("FAIL protocol_error asserted");
      $finish(1);
    end
    if (accepted_count !== 32'd1 || completed_count !== 32'd0) begin
      $display("FAIL counter snapshot mismatch accepted=%0d completed=%0d", accepted_count, completed_count);
      $finish(1);
    end

    @(posedge clk);
    #1;
    if (completed_count !== 32'd1) begin
      $display("FAIL completed count did not increment");
      $finish(1);
    end
    if (req_count != 2 || captured_addrs[0] != 14'd0 || captured_addrs[1] != 14'd1) begin
      $display("FAIL read request addresses mismatch count=%0d a0=%0d a1=%0d", req_count, captured_addrs[0], captured_addrs[1]);
      $finish(1);
    end

    $display("PASS attention_decode_score_local_cluster protocol");
    $finish(0);
  end

  always @(posedge clk) begin
    value_response_valid <= 1'b0;
    if (value_read_req_valid && value_read_req_ready) begin
      if (req_count > 1) begin
        $display("FAIL unexpected extra replay request");
        $finish(1);
      end
      captured_addrs[req_count] <= value_read_req_address;
      pending_rsp <= 1'b1;
      pending_addr <= value_read_req_address;
      rsp_delay <= (value_read_req_address == 14'd0) ? 2 : 1;
      req_count <= req_count + 1;
    end else if (pending_rsp) begin
      if (rsp_delay == 0) begin
        value_response_valid <= 1'b1;
        value_response_address <= pending_addr;
        value_response_matrix <= expected_values[pending_addr];
        pending_rsp <= 1'b0;
      end else begin
        rsp_delay <= rsp_delay - 1;
      end
    end
  end
endmodule
"""

    tb_path = tmp_path / "tb.v"
    tb_path.write_text(tb_text, encoding="utf-8")

    subprocess.run(
        [
            iverilog,
            "-g2012",
            "-s",
            "tb",
            "-o",
            str(tmp_path / "simv"),
            str(tb_path),
            str(design_dir / "top.v"),
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
    )
    run = subprocess.run(
        [str(tmp_path / "simv")],
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert "PASS attention_decode_score_local_cluster protocol" in run.stdout
