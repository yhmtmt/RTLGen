import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.rtlgen.gen_attention_decode_score_multivalue_gqa_array import generate


def _config(*, group_count: int, top_name: str | None = None, max_blocks: int = 16) -> dict:
    return {
        "top_name": top_name or f"attention_decode_score_multivalue_gqa_array_smoke_g{group_count}",
        "attention_decode_score_multivalue_gqa_array": {
            "max_blocks": max_blocks,
            "array_n": 8,
            "value_slices": 16,
            "divider_impl": "iterative_restoring",
            "score_scale_lanes_per_cycle": 1,
            "query_heads_per_kv": 8,
            "group_count": group_count,
        },
    }


def _iverilog() -> str | None:
    return shutil.which("iverilog") or (
        "/oss-cad-suite/bin/iverilog" if Path("/oss-cad-suite/bin/iverilog").exists() else None
    )


def _vvp() -> str | None:
    return shutil.which("vvp") or ("/oss-cad-suite/bin/vvp" if Path("/oss-cad-suite/bin/vvp").exists() else None)


def _macro_manifest(top_name: str, group_count: int) -> dict:
    return {
        "version": "0.1",
        "design_id": top_name,
        "module": top_name,
        "platform": "nangate45",
        "flow_variant": "decode_score_multivalue_gqa_array_v1",
        "blackboxes": ["fakeram45_2048x39"],
        "additional_lefs": ["/orfs/flow/platforms/nangate45/lef/fakeram45_2048x39.lef"],
        "additional_libs": ["/orfs/flow/platforms/nangate45/lib/fakeram45_2048x39.lib"],
        "additional_gds": [],
        "blackbox_verilog": ["npu/rtl/fakeram45_2048x39_blackbox.v"],
        "source": {
            "mode": "generated_composed_multivalue_gqa_array",
            "generator": "npu/rtlgen/gen_attention_decode_score_multivalue_gqa_array.py",
            "config": f"runs/designs/npu_blocks/{top_name}/config.json",
        },
        "manifest_params": {
            "semantic_profile": "decode_m1x8_shared_score_16x8d_value_iterdiv_gqa8_array_v1",
            "macro_count": 448 * group_count,
            "score_bank_macro_count": 448 * group_count,
            "per_group_macro_count": 448,
            "group_count": group_count,
            "logical_kv_groups": group_count,
            "total_parallel_query_heads": 8 * group_count,
            "independent_external_value_ports": group_count,
            "serialization": "none",
            "query_heads_per_kv": 8,
            "score_scale_lanes_per_cycle": 1,
            "score_passes_per_query_head": 1,
            "value_slices": 16,
        },
    }


def test_multivalue_gqa_array_manifest_and_structure(tmp_path: Path) -> None:
    group_count = 4
    config = _config(group_count=group_count)
    generate(config, tmp_path)
    text = (tmp_path / "top.v").read_text(encoding="utf-8")
    manifest = json.loads(
        (tmp_path / "attention_decode_score_multivalue_gqa_array_manifest.json").read_text(encoding="utf-8")
    )

    assert manifest["semantic_profile"] == "decode_m1x8_shared_score_16x8d_value_iterdiv_gqa8_array_v1"
    assert manifest["group_count"] == 4
    assert manifest["logical_kv_groups"] == 4
    assert manifest["total_parallel_query_heads"] == 32
    assert manifest["total_score_bank_macros"] == 1792
    assert manifest["per_group_macro_count"] == 448
    assert manifest["independent_external_value_ports"] == 4
    assert manifest["serialization"] == "none"
    assert manifest["no_serialization"] is True

    top_name = config["top_name"]
    assert text.count(f"module {top_name} (") == 1
    assert text.count(f"module {top_name}__group (") == 1
    assert text.count(f"{top_name}__group u_group_") == 4
    assert text.count(f"{top_name}__group__cluster u_head_") == 8
    assert text.count("fakeram45_2048x39 u_group_") == 56
    assert "input  wire signed [255:0] input_query" in text
    assert "input  wire signed [255:0] input_key" in text
    assert "assign command_ready = command_ready_all;" in text
    assert "assign input_ready = input_ready_all;" in text
    assert "assign protocol_error = |child_protocol_error;" in text
    assert ".command_valid(command_valid && command_ready)" in text
    assert ".input_valid(input_valid && input_ready)" in text


@pytest.mark.parametrize("group_count", [0, 3, 8])
def test_multivalue_gqa_array_rejects_unsupported_group_count(tmp_path: Path, group_count: int) -> None:
    with pytest.raises(SystemExit, match="group_count must be exactly one of 1, 2, or 4"):
        generate(_config(group_count=group_count), tmp_path)


@pytest.mark.parametrize("group_count", [1, 2, 4])
def test_multivalue_gqa_array_guard_accepts_llama7b_design(tmp_path: Path, group_count: int) -> None:
    source_name = f"attention_decode_score_multivalue_gqa_array_g{group_count}_int8_m1x8_iterdiv"
    source_design = REPO_ROOT / "runs" / "designs" / "npu_blocks" / source_name
    design_dir = tmp_path / source_name
    design_dir.mkdir()
    config = json.loads((source_design / "config.json").read_text(encoding="utf-8"))
    shutil.copy(source_design / "config.json", design_dir / "config.json")
    shutil.copy(source_design / "macro_manifest.json", design_dir / "macro_manifest.json")
    generate(config, design_dir / "verilog")

    result = subprocess.run(
        [
            sys.executable,
            "npu/eval/check_attention_decode_score_multivalue_gqa_array_guard.py",
            "--design-dir",
            str(design_dir),
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    assert payload["status"] == "ok"
    assert payload["group_count"] == group_count
    assert payload["macro_count"] == 448 * group_count


def test_multivalue_gqa_array_guard_rejects_wrong_macro_total(tmp_path: Path) -> None:
    group_count = 2
    source_name = "attention_decode_score_multivalue_gqa_array_g2_int8_m1x8_iterdiv"
    source_design = REPO_ROOT / "runs" / "designs" / "npu_blocks" / source_name
    design_dir = tmp_path / source_name
    design_dir.mkdir()
    config = json.loads((source_design / "config.json").read_text(encoding="utf-8"))
    shutil.copy(source_design / "config.json", design_dir / "config.json")
    macro_manifest = json.loads((source_design / "macro_manifest.json").read_text(encoding="utf-8"))
    macro_manifest["manifest_params"]["macro_count"] = 448
    (design_dir / "macro_manifest.json").write_text(json.dumps(macro_manifest), encoding="utf-8")
    generate(config, design_dir / "verilog")

    result = subprocess.run(
        [
            sys.executable,
            "npu/eval/check_attention_decode_score_multivalue_gqa_array_guard.py",
            "--design-dir",
            str(design_dir),
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "macro manifest macro_count must be 896" in result.stderr


def test_multivalue_gqa_array_generated_smoke_compiles(tmp_path: Path) -> None:
    iverilog = _iverilog()
    if not iverilog:
        pytest.skip("iverilog unavailable")
    config = _config(group_count=1, top_name="attention_decode_score_multivalue_gqa_array_compile", max_blocks=16)
    generate(config, tmp_path)
    subprocess.run(
        [
            iverilog,
            "-g2012",
            "-s",
            config["top_name"],
            "-o",
            str(tmp_path / "simv"),
            str(tmp_path / "top.v"),
            str(REPO_ROOT / "npu" / "rtl" / "fakeram45_2048x39_blackbox.v"),
        ],
        check=True,
        capture_output=True,
        text=True,
    )


def _group_stub(module_name: str) -> str:
    return f"""
module {module_name} (
    input wire clk, input wire rst_n,
    input wire command_valid, output wire command_ready,
    input wire [15:0] command_id, input wire [14:0] command_block_count,
    input wire [31:0] command_score_multiplier, input wire [5:0] command_score_shift,
    input wire input_valid, output wire input_ready, input wire input_last,
    input wire signed [63:0] input_query, input wire signed [63:0] input_key,
    output wire value_read_req_valid, input wire value_read_req_ready,
    output wire [13:0] value_read_req_address, output wire [3:0] value_read_req_slice,
    input wire value_response_valid, output wire value_response_ready,
    input wire [13:0] value_response_address, input wire [3:0] value_response_slice,
    input wire [511:0] value_response_matrix,
    output wire result_valid, input wire result_ready, output wire [2:0] result_head,
    output wire [15:0] result_command_id, output wire signed [31:0] result_global_max,
    output wire [32:0] result_exp_sum, output wire [3:0] result_slice,
    output wire result_last, output wire [319:0] result_value,
    output reg [31:0] accepted_count, output reg [31:0] completed_count,
    output reg [31:0] cycle_count, output wire protocol_error
);
  localparam IDLE = 3'd0, INPUT = 3'd1, REQUEST = 3'd2,
      RESPONSE = 3'd3, RESULT = 3'd4;
  reg [2:0] state_q;
  reg [15:0] command_id_q;
  assign command_ready = state_q == IDLE;
  assign input_ready = state_q == INPUT;
  assign value_read_req_valid = state_q == REQUEST;
  assign value_read_req_address = 14'd0;
  assign value_read_req_slice = 4'd0;
  assign value_response_ready = state_q == RESPONSE;
  assign result_valid = state_q == RESULT;
  assign result_head = 3'd0;
  assign result_command_id = command_id_q;
  assign result_global_max = 32'sd7;
  assign result_exp_sum = 33'd11;
  assign result_slice = 4'd0;
  assign result_last = 1'b1;
  assign result_value = 320'd0;
  assign protocol_error = 1'b0;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state_q <= IDLE;
      command_id_q <= 16'd0;
      accepted_count <= 32'd0;
      completed_count <= 32'd0;
      cycle_count <= 32'd0;
    end else begin
      cycle_count <= cycle_count + 1'b1;
      case (state_q)
        IDLE: if (command_valid && command_ready) begin
          command_id_q <= command_id;
          accepted_count <= accepted_count + 1'b1;
          state_q <= INPUT;
        end
        INPUT: if (input_valid && input_ready && input_last) state_q <= REQUEST;
        REQUEST: if (value_read_req_valid && value_read_req_ready) state_q <= RESPONSE;
        RESPONSE: if (value_response_valid && value_response_ready) state_q <= RESULT;
        RESULT: if (result_valid && result_ready) begin
          completed_count <= completed_count + 1'b1;
          state_q <= IDLE;
        end
        default: state_q <= IDLE;
      endcase
    end
  end
endmodule
"""


@pytest.mark.parametrize("group_count", [1, 2, 4])
def test_multivalue_gqa_array_atomic_broadcast_and_independent_channels(tmp_path: Path, group_count: int) -> None:
    iverilog = _iverilog()
    vvp = _vvp()
    if iverilog is None or vvp is None:
        pytest.skip("iverilog/vvp unavailable")

    config = _config(group_count=group_count, top_name=f"attention_decode_score_multivalue_gqa_array_protocol_g{group_count}")
    generate(config, tmp_path)
    generated = (tmp_path / "top.v").read_text(encoding="utf-8")
    wrapper_marker = f"module {config['top_name']} ("
    wrapper_path = tmp_path / "wrapper.v"
    wrapper_path.write_text(
        _group_stub(f"{config['top_name']}__group") + generated[generated.index(wrapper_marker) :],
        encoding="utf-8",
    )

    bus_ones = f"{{{group_count}{{1'b1}}}}"
    tb_text = f"""
module tb;
  localparam integer GC = {group_count};
  reg clk = 1'b0;
  always #1 clk = ~clk;
  reg rst_n = 1'b0;
  reg command_valid = 1'b0;
  wire command_ready;
  reg [15:0] command_id = 16'h1234;
  reg [14:0] command_block_count = 15'd1;
  reg [31:0] command_score_multiplier = 32'd1;
  reg [5:0] command_score_shift = 6'd0;
  reg input_valid = 1'b0;
  wire input_ready;
  reg input_last = 1'b0;
  reg signed [GC*64-1:0] input_query = '0;
  reg signed [GC*64-1:0] input_key = '0;
  wire [GC-1:0] value_read_req_valid;
  reg [GC-1:0] value_read_req_ready = '0;
  wire [GC*14-1:0] value_read_req_address;
  wire [GC*4-1:0] value_read_req_slice;
  reg [GC-1:0] value_response_valid = '0;
  wire [GC-1:0] value_response_ready;
  reg [GC*14-1:0] value_response_address = '0;
  reg [GC*4-1:0] value_response_slice = '0;
  reg [GC*512-1:0] value_response_matrix = '0;
  wire [GC-1:0] result_valid;
  reg [GC-1:0] result_ready = '0;
  wire [GC*3-1:0] result_head;
  wire [GC*16-1:0] result_command_id;
  wire signed [GC*32-1:0] result_global_max;
  wire [GC*33-1:0] result_exp_sum;
  wire [GC*4-1:0] result_slice;
  wire [GC-1:0] result_last;
  wire [GC*320-1:0] result_value;
  wire [GC*32-1:0] accepted_count;
  wire [GC*32-1:0] completed_count;
  wire [GC*32-1:0] cycle_count;
  wire protocol_error;
  integer i;

  {config['top_name']} dut (
      .clk(clk), .rst_n(rst_n), .command_valid(command_valid), .command_ready(command_ready),
      .command_id(command_id), .command_block_count(command_block_count),
      .command_score_multiplier(command_score_multiplier), .command_score_shift(command_score_shift),
      .input_valid(input_valid), .input_ready(input_ready), .input_last(input_last),
      .input_query(input_query), .input_key(input_key),
      .value_read_req_valid(value_read_req_valid), .value_read_req_ready(value_read_req_ready),
      .value_read_req_address(value_read_req_address), .value_read_req_slice(value_read_req_slice),
      .value_response_valid(value_response_valid), .value_response_ready(value_response_ready),
      .value_response_address(value_response_address), .value_response_slice(value_response_slice),
      .value_response_matrix(value_response_matrix), .result_valid(result_valid), .result_ready(result_ready),
      .result_head(result_head), .result_command_id(result_command_id), .result_global_max(result_global_max),
      .result_exp_sum(result_exp_sum), .result_slice(result_slice), .result_last(result_last),
      .result_value(result_value), .accepted_count(accepted_count), .completed_count(completed_count),
      .cycle_count(cycle_count), .protocol_error(protocol_error)
  );

  initial begin
    #3 rst_n = 1'b1;
    @(negedge clk); command_valid = 1'b1;
    @(posedge clk); #0.1;
    if (!command_ready) $fatal(1, "command broadcast was not accepted atomically");
    @(negedge clk); command_valid = 1'b0; input_valid = 1'b1; input_last = 1'b1;
    input_query = '0; input_key = '0;
    @(posedge clk); #0.1;
    if (!input_ready) $fatal(1, "input broadcast was not accepted atomically");
    @(negedge clk); input_valid = 1'b0; input_last = 1'b0; value_read_req_ready = {bus_ones};
    wait (value_read_req_valid === {bus_ones});
    @(posedge clk); #0.1;
    if (value_read_req_valid !== {bus_ones}) $fatal(1, "value requests were not parallel");
    @(negedge clk); value_read_req_ready = '0;
    for (i = 0; i < GC; i = i + 1) begin
      wait (value_response_ready[i]);
      @(negedge clk); value_response_valid[i] = 1'b1;
      @(posedge clk); #0.1;
      if (!value_response_ready[i]) $fatal(1, "group response lane was not independently ready");
      @(negedge clk); value_response_valid[i] = 1'b0;
    end
    for (i = 0; i < GC; i = i + 1) begin
      wait (result_valid[i]);
      if (result_command_id[i*16 +: 16] !== 16'h1234 || result_slice[i*4 +: 4] !== 4'd0 || !result_last[i])
        $fatal(1, "group result lane %0d mismatch", i);
      @(negedge clk); result_ready[i] = 1'b1;
      @(posedge clk); #0.1;
      result_ready[i] = 1'b0;
    end
    #2;
    if (protocol_error) $fatal(1, "protocol_error asserted");
    for (i = 0; i < GC; i = i + 1) begin
      if (accepted_count[i*32 +: 32] !== 32'd1 || completed_count[i*32 +: 32] !== 32'd1)
        $fatal(1, "counter mismatch for group %0d", i);
    end
    $display("PASS group_count=%0d", GC);
    $finish;
  end
endmodule
"""
    tb_path = tmp_path / "tb.v"
    tb_path.write_text(tb_text, encoding="utf-8")
    simv = tmp_path / "simv"
    subprocess.run(
        [iverilog, "-g2012", "-s", "tb", "-o", str(simv), str(wrapper_path), str(tb_path)],
        check=True,
        capture_output=True,
        text=True,
    )
    result = subprocess.run([vvp, str(simv)], check=True, capture_output=True, text=True)
    assert f"PASS group_count={group_count}" in result.stdout
