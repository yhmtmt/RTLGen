from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess

import pytest

from npu.eval.check_noc_segmented_mesh4x4_direct_guard import check
from npu.rtlgen.stage_noc_segmented_mesh4x4_direct import SOURCES, stage


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_direct_mesh_staging_is_canonical_and_hierarchy_complete(tmp_path: Path) -> None:
    config = tmp_path / "config.json"
    config.write_text(
        json.dumps(
            {
                "top_name": "noc_segmented_mesh4x4_functional",
                "segmented_mesh4x4_direct": {
                    "nodes": 16,
                    "ports_per_router": 5,
                    "data_bits": 256,
                    "virtual_channels": 4,
                    "fifo_depth": 4,
                    "debug_counters": False,
                    "top_level_pin_count": 8962,
                    "pin_pitch_bound_um": 1.12,
                    "die_side_um": 3200,
                },
            }
        ),
        encoding="utf-8",
    )
    verilog_dir = tmp_path / "verilog"
    staged = stage(config, verilog_dir)

    assert [path.name for path in staged] == list(SOURCES)
    for name in SOURCES:
        assert (verilog_dir / name).read_bytes() == (
            REPO_ROOT / "npu" / "sim" / "rtl" / name
        ).read_bytes()
    perimeter = check(config, verilog_dir)
    assert perimeter == {
        "required_perimeter_um": 10037.44,
        "available_perimeter_um": 12800.0,
        "minimum_square_side_um": 2509.36,
        "perimeter_margin_um": 2762.5599999999995,
    }


def test_counter_disabled_mesh_preserves_functional_transport(tmp_path: Path) -> None:
    iverilog = shutil.which("iverilog")
    vvp = shutil.which("vvp")
    if not iverilog or not vvp:
        pytest.skip("iverilog/vvp unavailable")

    testbench = tmp_path / "tb.sv"
    testbench.write_text(
        r"""
module tb;
  reg clk = 1'b0;
  reg rst_n = 1'b0;
  reg [15:0] in_valid = 0;
  wire [15:0] in_ready_ref;
  wire [15:0] in_ready_functional;
  reg [63:0] in_dest = 0;
  reg [63:0] in_source = 0;
  reg [127:0] in_tag = 0;
  reg [47:0] in_fragment = 0;
  reg [15:0] in_last = 0;
  reg [31:0] in_vc = 0;
  reg [4095:0] in_data = 0;
  wire [15:0] out_valid_ref;
  wire [15:0] out_valid_functional;
  reg [15:0] out_ready = 16'hffff;
  wire [63:0] out_dest_ref, out_dest_functional;
  wire [63:0] out_source_ref, out_source_functional;
  wire [127:0] out_tag_ref, out_tag_functional;
  wire [47:0] out_fragment_ref, out_fragment_functional;
  wire [15:0] out_last_ref, out_last_functional;
  wire [31:0] out_vc_ref, out_vc_functional;
  wire [4095:0] out_data_ref, out_data_functional;
  wire [511:0] accepted_ref;
  integer cycles = 0;
  integer delivered = 0;

  always #1 clk = ~clk;

  noc_segmented_mesh4x4 reference (
    .clk(clk), .rst_n(rst_n),
    .endpoint_in_valid(in_valid), .endpoint_in_ready(in_ready_ref),
    .endpoint_in_dest(in_dest), .endpoint_in_source(in_source),
    .endpoint_in_tag(in_tag), .endpoint_in_fragment(in_fragment),
    .endpoint_in_last(in_last), .endpoint_in_vc(in_vc), .endpoint_in_data(in_data),
    .endpoint_out_valid(out_valid_ref), .endpoint_out_ready(out_ready),
    .endpoint_out_dest(out_dest_ref), .endpoint_out_source(out_source_ref),
    .endpoint_out_tag(out_tag_ref), .endpoint_out_fragment(out_fragment_ref),
    .endpoint_out_last(out_last_ref), .endpoint_out_vc(out_vc_ref),
    .endpoint_out_data(out_data_ref), .router_accepted_flit_count(accepted_ref),
    .router_forwarded_flit_count(), .router_input_stall_cycles(),
    .router_output_stall_cycles(), .router_contention_cycles(),
    .router_current_input_occupancy(), .router_max_input_occupancy(),
    .router_route_flit_count()
  );

  noc_segmented_mesh4x4_functional functional (
    .clk(clk), .rst_n(rst_n),
    .endpoint_in_valid(in_valid), .endpoint_in_ready(in_ready_functional),
    .endpoint_in_dest(in_dest), .endpoint_in_source(in_source),
    .endpoint_in_tag(in_tag), .endpoint_in_fragment(in_fragment),
    .endpoint_in_last(in_last), .endpoint_in_vc(in_vc), .endpoint_in_data(in_data),
    .endpoint_out_valid(out_valid_functional), .endpoint_out_ready(out_ready),
    .endpoint_out_dest(out_dest_functional), .endpoint_out_source(out_source_functional),
    .endpoint_out_tag(out_tag_functional), .endpoint_out_fragment(out_fragment_functional),
    .endpoint_out_last(out_last_functional), .endpoint_out_vc(out_vc_functional),
    .endpoint_out_data(out_data_functional)
  );

  always @(posedge clk) begin
    if (rst_n) begin
      cycles = cycles + 1;
      if ({in_ready_ref, out_valid_ref, out_dest_ref, out_source_ref, out_tag_ref,
           out_fragment_ref, out_last_ref, out_vc_ref, out_data_ref} !==
          {in_ready_functional, out_valid_functional, out_dest_functional,
           out_source_functional, out_tag_functional, out_fragment_functional,
           out_last_functional, out_vc_functional, out_data_functional})
        $fatal(1, "functional transport diverged at cycle %0d", cycles);
      if (out_valid_ref[15] && out_ready[15])
        delivered = delivered + 1;
    end
  end

  initial begin
    repeat (3) @(posedge clk);
    @(negedge clk);
    rst_n = 1'b1;
    in_valid[0] = 1'b1;
    in_dest[3:0] = 4'hf;
    in_source[3:0] = 4'h0;
    in_tag[7:0] = 8'h5a;
    in_fragment[2:0] = 3'h3;
    in_last[0] = 1'b1;
    in_vc[1:0] = 2'h2;
    in_data[255:0] = 256'h123456789abcdef;
    do @(negedge clk); while (!in_ready_ref[0]);
    in_valid[0] = 1'b0;
    repeat (40) @(posedge clk);
    if (accepted_ref == 0)
      $fatal(1, "reference counters did not observe traffic");
    if (functional.u_mesh.router_accepted_flit_count !== 0)
      $fatal(1, "disabled debug counters retained state");
    if (delivered != 1)
      $fatal(1, "expected one delivered flit, got %0d", delivered);
    $display("PASS");
    $finish;
  end
endmodule
""",
        encoding="utf-8",
    )
    executable = tmp_path / "simv"
    subprocess.run(
        [
            iverilog,
            "-g2012",
            "-s",
            "tb",
            "-o",
            str(executable),
            str(REPO_ROOT / "npu/sim/rtl/noc_ready_valid_fifo.sv"),
            str(REPO_ROOT / "npu/sim/rtl/noc_segmented_mesh_router.sv"),
            str(REPO_ROOT / "npu/sim/rtl/noc_segmented_mesh4x4.sv"),
            str(REPO_ROOT / "npu/sim/rtl/noc_segmented_mesh4x4_functional.sv"),
            str(testbench),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    result = subprocess.run(
        [vvp, str(executable)],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "PASS" in result.stdout
