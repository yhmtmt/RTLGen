import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.rtlgen.gen_attention_decode_score_multivalue_gqa_group import generate


def _config(*, scale_lanes: int = 1, query_heads_per_kv: int = 8) -> dict:
    return {
        "top_name": f"attention_decode_score_multivalue_gqa_group_s{scale_lanes}",
        "attention_decode_score_multivalue_gqa_group": {
            "max_blocks": 16,
            "array_n": 8,
            "value_slices": 16,
            "divider_impl": "iterative_restoring",
            "score_scale_lanes_per_cycle": scale_lanes,
            "query_heads_per_kv": query_heads_per_kv,
        },
    }


def _iverilog() -> str | None:
    iverilog = shutil.which("iverilog")
    if iverilog is not None:
        return iverilog
    fallback = Path("/oss-cad-suite/bin/iverilog")
    return str(fallback) if fallback.exists() else None


def _vvp() -> str | None:
    vvp = shutil.which("vvp")
    if vvp is not None:
        return vvp
    fallback = Path("/oss-cad-suite/bin/vvp")
    return str(fallback) if fallback.exists() else None


def _cluster_stub(module_name: str) -> str:
    return f"""
module {module_name} (
    input wire clk, input wire rst_n,
    input wire command_valid, output wire command_ready,
    input wire [15:0] command_id, input wire [14:0] command_block_count,
    input wire [31:0] command_score_multiplier, input wire [5:0] command_score_shift,
    input wire input_valid, output wire input_ready, input wire input_last,
    input wire signed [7:0] input_a, input wire signed [63:0] input_b,
    output wire value_read_req_valid, input wire value_read_req_ready,
    output wire [13:0] value_read_req_address, output wire [3:0] value_read_req_slice,
    input wire value_response_valid, output wire value_response_ready,
    input wire [13:0] value_response_address, input wire [3:0] value_response_slice,
    input wire [511:0] value_response_matrix,
    output wire result_valid, input wire result_ready,
    output wire [15:0] result_command_id, output wire signed [31:0] result_global_max,
    output wire [32:0] result_exp_sum, output wire [3:0] result_slice,
    output wire result_last, output wire [319:0] result_value,
    output reg [31:0] accepted_count, output reg [31:0] completed_count,
    output reg [31:0] cycle_count, output wire protocol_error
);
  localparam IDLE = 3'd0, INPUT = 3'd1, REQUEST = 3'd2,
      RESPONSE = 3'd3, RESULT = 3'd4;
  reg [2:0] state_q;
  reg [3:0] slice_q;
  reg [15:0] command_id_q;
  reg signed [7:0] input_a_q;
  assign command_ready = state_q == IDLE;
  assign input_ready = state_q == INPUT;
  assign value_read_req_valid = state_q == REQUEST;
  assign value_read_req_address = 14'd0;
  assign value_read_req_slice = slice_q;
  assign value_response_ready = state_q == RESPONSE;
  assign result_valid = state_q == RESULT;
  assign result_command_id = command_id_q;
  assign result_global_max = 32'sd7;
  assign result_exp_sum = 33'd11;
  assign result_slice = slice_q;
  assign result_last = slice_q == 4'd15;
  assign result_value = {{{{308{{1'b0}}}}, slice_q, input_a_q}};
  assign protocol_error = 1'b0;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state_q <= IDLE;
      slice_q <= 0;
      command_id_q <= 0;
      input_a_q <= 0;
      accepted_count <= 0;
      completed_count <= 0;
      cycle_count <= 0;
    end else begin
      cycle_count <= cycle_count + 1'b1;
      case (state_q)
        IDLE: if (command_valid && command_ready) begin
          command_id_q <= command_id;
          accepted_count <= accepted_count + 1'b1;
          state_q <= INPUT;
        end
        INPUT: if (input_valid && input_ready && input_last) begin
          input_a_q <= input_a;
          slice_q <= 0;
          state_q <= REQUEST;
        end
        REQUEST: if (value_read_req_valid && value_read_req_ready) state_q <= RESPONSE;
        RESPONSE: if (value_response_valid && value_response_ready) begin
          if (slice_q == 4'd15) begin
            slice_q <= 0;
            state_q <= RESULT;
          end else begin
            slice_q <= slice_q + 1'b1;
            state_q <= REQUEST;
          end
        end
        RESULT: if (result_valid && result_ready) begin
          if (slice_q == 4'd15) begin
            completed_count <= completed_count + 1'b1;
            state_q <= IDLE;
          end else slice_q <= slice_q + 1'b1;
        end
        default: state_q <= IDLE;
      endcase
    end
  end
endmodule
"""


def test_multivalue_gqa_group_manifest_and_structure(tmp_path: Path) -> None:
    config = _config()
    generate(config, tmp_path)
    top_name = config["top_name"]
    manifest = json.loads(
        (tmp_path / "attention_decode_score_multivalue_gqa_group_manifest.json").read_text(encoding="utf-8")
    )
    text = (tmp_path / "top.v").read_text(encoding="utf-8")

    assert manifest["semantic_profile"] == "decode_m1x8_shared_score_16x8d_value_iterdiv_gqa8_group_v1"
    assert manifest["query_heads_per_kv"] == 8
    assert manifest["parallel_query_head_clusters"] == 8
    assert manifest["query_head_score_computations_per_command"] == 8
    assert manifest["score_passes_per_query_head"] == 1
    assert manifest["shared_external_value_reads_per_block"] == 16
    assert manifest["result_beats_per_command"] == 128
    assert manifest["submodule_manifests"]["multivalue_cluster"]["result_beats_per_command"] == 16

    assert text.count(f"module {top_name}__cluster (") == 1
    assert text.count(f"{top_name}__cluster u_head_") == 8
    assert "output wire [2:0] result_head" in text
    assert "wire value_req_divergent" in text
    assert "assign child_value_response_valid = {QUERY_HEADS_PER_KV{value_response_valid && value_response_ready}};" in text
    assert "assign command_ready = !command_active_q && command_block_count_valid && command_ready_all;" in text


def test_multivalue_gqa_group_rejects_wrong_query_heads_per_kv(tmp_path: Path) -> None:
    with pytest.raises(SystemExit, match="query_heads_per_kv must be 8"):
        generate(_config(query_heads_per_kv=4), tmp_path)


def test_multivalue_gqa_group_atomic_replay_and_result_order(tmp_path: Path) -> None:
    iverilog = _iverilog()
    vvp = _vvp()
    if iverilog is None or vvp is None:
        pytest.skip("iverilog/vvp unavailable")

    design_dir = tmp_path / "design"
    design_dir.mkdir()
    config = _config()
    generate(config, design_dir)
    top_name = config["top_name"]
    generated = (design_dir / "top.v").read_text(encoding="utf-8")
    wrapper_marker = f"module {top_name} ("
    wrapper_path = tmp_path / "wrapper.v"
    wrapper_path.write_text(
        _cluster_stub(f"{top_name}__cluster") + generated[generated.index(wrapper_marker) :],
        encoding="utf-8",
    )

    tb_text = f"""
module tb;
  reg clk = 1'b0;
  always #5 clk = ~clk;

  reg rst_n = 1'b0;
  reg command_valid = 1'b0;
  wire command_ready;
  reg [15:0] command_id = 16'd0;
  reg [14:0] command_block_count = 15'd0;
  reg [31:0] command_score_multiplier = 32'd0;
  reg [5:0] command_score_shift = 6'd0;
  reg input_valid = 1'b0;
  wire input_ready;
  reg input_last = 1'b0;
  reg signed [63:0] input_query = 64'sd0;
  reg signed [63:0] input_key = 64'sd0;
  wire value_read_req_valid;
  reg value_read_req_ready = 1'b1;
  wire [13:0] value_read_req_address;
  wire [3:0] value_read_req_slice;
  reg value_response_valid = 1'b0;
  wire value_response_ready;
  reg [13:0] value_response_address = 14'd0;
  reg [3:0] value_response_slice = 4'd0;
  reg [511:0] value_response_matrix = 512'd0;
  wire result_valid;
  reg result_ready = 1'b1;
  wire [2:0] result_head;
  wire [15:0] result_command_id;
  wire signed [31:0] result_global_max;
  wire [32:0] result_exp_sum;
  wire [3:0] result_slice;
  wire result_last;
  wire [319:0] result_value;
  wire [31:0] accepted_count;
  wire [31:0] completed_count;
  wire [31:0] cycle_count;
  wire protocol_error;

  integer request_count = 0;
  integer result_count = 0;
  integer watchdog = 0;
  integer expected_head = 0;
  integer expected_slice = 0;
  reg pending_rsp = 1'b0;
  reg [13:0] pending_addr = 14'd0;
  reg [3:0] pending_slice = 4'd0;
  reg command_inflight = 1'b0;
  reg first_command_done = 1'b0;

  {top_name} dut (
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
      .input_query(input_query),
      .input_key(input_key),
      .value_read_req_valid(value_read_req_valid),
      .value_read_req_ready(value_read_req_ready),
      .value_read_req_address(value_read_req_address),
      .value_read_req_slice(value_read_req_slice),
      .value_response_valid(value_response_valid),
      .value_response_ready(value_response_ready),
      .value_response_address(value_response_address),
      .value_response_slice(value_response_slice),
      .value_response_matrix(value_response_matrix),
      .result_valid(result_valid),
      .result_ready(result_ready),
      .result_head(result_head),
      .result_command_id(result_command_id),
      .result_global_max(result_global_max),
      .result_exp_sum(result_exp_sum),
      .result_slice(result_slice),
      .result_last(result_last),
      .result_value(result_value),
      .accepted_count(accepted_count),
      .completed_count(completed_count),
      .cycle_count(cycle_count),
      .protocol_error(protocol_error)
  );

  task automatic send_command(input [15:0] cmd_id);
    begin
      @(negedge clk);
      command_id = cmd_id;
      command_block_count = 15'd1;
      command_score_multiplier = 32'd1;
      command_score_shift = 6'd0;
      command_valid = 1'b1;
      @(posedge clk);
      while (!command_ready) @(posedge clk);
      @(negedge clk);
      command_valid = 1'b0;
      command_inflight = 1'b1;
    end
  endtask

  task automatic send_input_beat(input [63:0] query_pack, input [63:0] key_pack);
    begin
      @(negedge clk);
      input_query = query_pack;
      input_key = key_pack;
      input_last = 1'b1;
      input_valid = 1'b1;
      @(posedge clk);
      while (!input_ready) @(posedge clk);
      @(negedge clk);
      input_valid = 1'b0;
      input_last = 1'b0;
    end
  endtask

  always @(posedge clk) begin
    if (rst_n) begin
      watchdog <= watchdog + 1;
      if (watchdog > 1000) begin
        $display("FAIL timeout active=%0d head=%0d child0_state=%0d reqs=%0d results=%0d",
            dut.command_active_q, dut.result_head_q, dut.u_head_0.state_q, request_count, result_count);
        $finish(1);
      end
    end
    value_response_valid <= 1'b0;
    if (value_read_req_valid && value_read_req_ready) begin
      if (!first_command_done) begin
        if (request_count >= 16) begin
          $display("FAIL expected one shared external request per slice");
          $finish(1);
        end
        if (value_read_req_address !== 14'd0) begin
          $display("FAIL unexpected request address %0d", value_read_req_address);
          $finish(1);
        end
        if (value_read_req_slice !== request_count[3:0]) begin
          $display("FAIL request slice order mismatch got=%0d expected=%0d", value_read_req_slice, request_count);
          $finish(1);
        end
      end
      pending_rsp <= 1'b1;
      pending_addr <= value_read_req_address;
      pending_slice <= value_read_req_slice;
      request_count <= request_count + 1;
    end else if (pending_rsp && value_response_ready) begin
      value_response_valid <= 1'b1;
      value_response_address <= pending_addr;
      value_response_slice <= pending_slice;
      value_response_matrix <= {{64{{8'h01}}}};
      pending_rsp <= 1'b0;
    end
  end

  always @(posedge clk) begin
    if (rst_n && !first_command_done && protocol_error) begin
      $display("FAIL protocol_error asserted during aligned replay");
      $finish(1);
    end
    if (rst_n && command_inflight && !first_command_done && command_ready) begin
      $display("FAIL command_ready reasserted before every head completed");
      $finish(1);
    end
    if (!first_command_done && result_valid && result_ready) begin
      if (result_command_id !== 16'h1234) begin
        $display("FAIL unexpected command id %0d", result_command_id);
        $finish(1);
      end
      if (result_head !== expected_head[2:0]) begin
        $display("FAIL result head order mismatch got=%0d expected=%0d", result_head, expected_head);
        $finish(1);
      end
      if (result_slice !== expected_slice[3:0]) begin
        $display("FAIL result slice order mismatch got=%0d expected=%0d", result_slice, expected_slice);
        $finish(1);
      end
      if (result_last !== (expected_slice == 15)) begin
        $display("FAIL result_last mismatch at head=%0d slice=%0d", expected_head, expected_slice);
        $finish(1);
      end
      if (result_value[7:0] !== expected_head + 1 || result_value[11:8] !== expected_slice[3:0]) begin
        $display("FAIL result payload mapping mismatch head=%0d slice=%0d value=%0h",
            expected_head, expected_slice, result_value[11:0]);
        $finish(1);
      end
      result_count <= result_count + 1;
      if (expected_slice == 15) begin
        expected_slice <= 0;
        if (expected_head == 7) begin
          first_command_done <= 1'b1;
          command_inflight <= 1'b0;
        end else begin
          expected_head <= expected_head + 1;
        end
      end else begin
        expected_slice <= expected_slice + 1;
      end
    end
  end

  initial begin
    repeat (4) @(posedge clk);
    @(negedge clk);
    rst_n = 1'b1;

    send_command(16'h1234);
    send_input_beat(64'h08_07_06_05_04_03_02_01, 64'h01_01_01_01_01_01_01_01);

    wait (first_command_done);
    @(posedge clk);
    if (request_count != 16) begin
      $display("FAIL expected 16 shared requests, saw %0d", request_count);
      $finish(1);
    end
    if (result_count != 128) begin
      $display("FAIL expected 128 serialized result beats, saw %0d", result_count);
      $finish(1);
    end
    if (!command_ready) begin
      $display("FAIL command_ready did not return after full group completion");
      $finish(1);
    end
    if (accepted_count != 32'd1 || completed_count != 32'd1) begin
      $display("FAIL wrapper counters accepted=%0d completed=%0d", accepted_count, completed_count);
      $finish(1);
    end

    send_command(16'h5678);
    force dut.u_head_7.value_read_req_slice = 4'd15;
    send_input_beat(64'h08_07_06_05_04_03_02_01, 64'h01_01_01_01_01_01_01_01);
    wait (dut.u_head_7.value_read_req_valid);
    @(posedge clk);
    @(negedge clk);
    release dut.u_head_7.value_read_req_slice;
    repeat (3) @(posedge clk);
    if (!protocol_error) begin
      $display("FAIL protocol_error did not assert on divergent request");
      $finish(1);
    end

    $display("PASS attention_decode_score_multivalue_gqa_group protocol");
    $finish(0);
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
            str(wrapper_path),
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    run = subprocess.run(
        [vvp, str(tmp_path / "simv")],
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert "PASS attention_decode_score_multivalue_gqa_group protocol" in run.stdout
