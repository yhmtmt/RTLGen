import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.rtlgen.gen_attention_score_bank_proxy import generate


def _config() -> dict:
    return {
        "top_name": "attention_score_bank_proxy_smoke",
        "attention_score_bank_proxy": {},
    }


def _tb_text(top_name: str) -> str:
    return f"""`timescale 1ns/1ps
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
  integer bit_idx;

  initial begin
    addr_q = 11'd0;
    rd_out_q = 39'd0;
    for (bit_idx = 0; bit_idx < 2048; bit_idx = bit_idx + 1)
      mem[bit_idx] = 39'd0;
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
  reg         clk;
  reg         rst_n;
  reg         req_valid;
  wire        req_ready;
  reg         req_write;
  reg  [13:0] req_addr;
  reg  [255:0] req_wdata;
  reg  [255:0] req_wmask;
  wire        rsp_valid;
  wire [255:0] rsp_rdata;

  localparam [255:0] FULL_MASK = 256'hffff_ffff_ffff_ffff_ffff_ffff_ffff_ffff_ffff_ffff_ffff_ffff_ffff_ffff_ffff_ffff;
  localparam [255:0] DATA_A = 256'h00112233_44556677_8899aabb_ccddeeff_10213243_54657687_98a9bacb_dcedfe0f;
  localparam [255:0] DATA_B = 256'hfedcba98_76543210_0f1e2d3c_4b5a6978_8899aabb_ccddeeff_01234567_89abcdef;
  localparam [255:0] DATA_C = 256'h13579bdf_2468ace0_55aa55aa_aa55aa55_deadbeef_c001d00d_12345678_9abcdef0;
  localparam [255:0] DATA_D = 256'h0badf00d_f00dcafe_01020304_05060708_a0b0c0d0_e0f00112_22334455_66778899;
  localparam [255:0] DATA_E = 256'hcafefade_bead1234_99990000_11112222_33334444_55556666_77778888_9999aaaa;

  {top_name} dut (
      .clk(clk),
      .rst_n(rst_n),
      .req_valid(req_valid),
      .req_ready(req_ready),
      .req_write(req_write),
      .req_addr(req_addr),
      .req_wdata(req_wdata),
      .req_wmask(req_wmask),
      .rsp_valid(rsp_valid),
      .rsp_rdata(rsp_rdata)
  );

  always #5 clk = ~clk;

  task automatic drive_idle;
    begin
      req_valid = 1'b0;
      req_write = 1'b0;
      req_addr = 14'd0;
      req_wdata = 256'd0;
      req_wmask = 256'd0;
    end
  endtask

  task automatic issue_write(input [13:0] addr, input [255:0] data);
    begin
      @(negedge clk);
      req_valid = 1'b1;
      req_write = 1'b1;
      req_addr = addr;
      req_wdata = data;
      req_wmask = FULL_MASK;
      @(posedge clk);
      #1;
      if (!req_ready) begin
        $display("FAIL req_ready deasserted during write to %0d", addr);
        $finish(1);
      end
      if (rsp_valid) begin
        $display("FAIL write emitted rsp_valid at addr %0d", addr);
        $finish(1);
      end
      drive_idle();
    end
  endtask

  task automatic issue_read_expect(input [13:0] addr, input [255:0] expected);
    begin
      @(negedge clk);
      req_valid = 1'b1;
      req_write = 1'b0;
      req_addr = addr;
      req_wdata = 256'd0;
      req_wmask = 256'd0;
      @(posedge clk);
      #1;
      if (!req_ready) begin
        $display("FAIL req_ready deasserted during read to %0d", addr);
        $finish(1);
      end
      if (rsp_valid) begin
        $display("FAIL read responded too early for addr %0d", addr);
        $finish(1);
      end
      drive_idle();
      @(posedge clk);
      #1;
      if (!rsp_valid) begin
        $display("FAIL read missing rsp_valid for addr %0d", addr);
        $finish(1);
      end
      if (rsp_rdata !== expected) begin
        $display("FAIL read mismatch addr=%0d expected=%h got=%h", addr, expected, rsp_rdata);
        $finish(1);
      end
    end
  endtask

  initial begin
    clk = 1'b0;
    rst_n = 1'b0;
    drive_idle();

    repeat (2) @(posedge clk);
    rst_n = 1'b1;
    @(posedge clk);
    #1;
    if (rsp_valid) begin
      $display("FAIL rsp_valid asserted immediately after reset release");
      $finish(1);
    end

    issue_write(14'd0, DATA_A);
    issue_write(14'd2047, DATA_B);
    issue_write(14'd2048, DATA_C);
    issue_write(14'd4117, DATA_D);
    issue_write(14'd10261, DATA_E);

    issue_read_expect(14'd0, DATA_A);
    issue_read_expect(14'd2047, DATA_B);
    issue_read_expect(14'd2048, DATA_C);
    issue_read_expect(14'd4117, DATA_D);
    issue_read_expect(14'd10261, DATA_E);

    issue_write(14'd2048, DATA_D);
    issue_read_expect(14'd2048, DATA_D);
    issue_read_expect(14'd2047, DATA_B);
    issue_read_expect(14'd4117, DATA_D);
    issue_read_expect(14'd10261, DATA_E);

    $display("PASS attention_score_bank_proxy synchronous 1RW behavior");
    $finish(0);
  end
endmodule
"""


def test_attention_score_bank_proxy_generator_structure(tmp_path: Path) -> None:
    generate(_config(), tmp_path)

    text = (tmp_path / "top.v").read_text(encoding="utf-8")
    manifest = json.loads((tmp_path / "attention_score_bank_proxy_manifest.json").read_text(encoding="utf-8"))

    assert "LEF/LIB proxy semantics only" in text
    assert "not SRAM signoff collateral" in text
    assert text.count("fakeram45_2048x39 u_group_") == 56
    assert "req_valid" in text
    assert "req_write" in text
    assert "req_wmask" in text
    assert "rsp_valid_q <= read_pending_q;" in text
    assert "rsp_group_q <= read_group_q;" in text
    assert "wire [272:0] req_wdata_padded = {17'd0, req_wdata};" in text
    assert "wire [272:0] req_wmask_padded = {17'd0, req_wmask};" in text
    assert manifest["macro_count"] == 56
    assert manifest["logical_depth"] == 16384
    assert manifest["logical_width"] == 256
    assert manifest["depth_groups"] == 8
    assert manifest["width_slices_per_group"] == 7
    assert manifest["unused_pad_bits"] == 17
    assert manifest["interface"]["type"] == "synchronous_1rw"
    assert manifest["interface"]["read_latency_cycles"] == 1
    assert manifest["proxy_semantics"] == "lef_lib_physical_proxy_only"
    assert manifest["sram_signoff"] is False


def test_attention_score_bank_proxy_compiles_and_simulates(tmp_path: Path) -> None:
    iverilog = shutil.which("iverilog")
    vvp = shutil.which("vvp")
    if not iverilog or not vvp:
        pytest.skip("iverilog/vvp unavailable")

    config = _config()
    generate(config, tmp_path)
    tb_path = tmp_path / "attention_score_bank_proxy_tb.v"
    tb_path.write_text(_tb_text(config["top_name"]), encoding="utf-8")

    simv = tmp_path / "simv"
    subprocess.run(
        [
            iverilog,
            "-g2012",
            "-s",
            "tb",
            "-o",
            str(simv),
            str(tmp_path / "top.v"),
            str(tb_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    run = subprocess.run([vvp, str(simv)], check=True, capture_output=True, text=True)
    assert "PASS attention_score_bank_proxy synchronous 1RW behavior" in run.stdout
