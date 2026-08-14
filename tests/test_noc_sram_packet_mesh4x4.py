from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.generate_design import (  # noqa: E402
    generate_l1_memory_noc_design,
    generate_wrapper,
    identify_design,
)

RTL_SOURCES = [
    REPO_ROOT / "npu/sim/rtl/noc_ready_valid_fifo.sv",
    REPO_ROOT / "npu/sim/rtl/noc_segmented_mesh_router.sv",
    REPO_ROOT / "npu/sim/rtl/noc_segmented_mesh4x4.sv",
    REPO_ROOT / "npu/sim/rtl/noc_sram_packet_endpoint.sv",
    REPO_ROOT / "npu/sim/rtl/noc_sram_packet_mesh4x4.sv",
]
TB = REPO_ROOT / "tests/noc_sram_packet_mesh4x4_tb.sv"
HARNESS = REPO_ROOT / "npu/sim/rtl/noc_sram_packet_mesh4x4_ppa_harness.sv"
PPA_CONFIG = (
    REPO_ROOT
    / "runs/designs/noc/l1_noc_sram_packet_mesh4x4_w256_vc4_d4_td4_to8_rx8_wrapper"
    / "config_l1_noc_sram_packet_mesh4x4_w256_vc4_d4_td4_to8_rx8.json"
)


def _tool(name: str) -> str | None:
    return shutil.which(name) or (
        f"/oss-cad-suite/bin/{name}"
        if Path(f"/oss-cad-suite/bin/{name}").exists()
        else None
    )


@pytest.mark.skipif(
    _tool("iverilog") is None or _tool("vvp") is None,
    reason="iverilog/vvp unavailable",
)
def test_noc_sram_packet_mesh4x4_end_to_end(tmp_path: Path) -> None:
    sim = tmp_path / "noc_sram_packet_mesh4x4_sim"
    subprocess.run(
        [
            str(_tool("iverilog")),
            "-g2012",
            "-s",
            "noc_sram_packet_mesh4x4_tb",
            "-o",
            str(sim),
            *[str(path) for path in RTL_SOURCES],
            str(TB),
        ],
        check=True,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    result = subprocess.run(
        [str(_tool("vvp")), str(sim)],
        check=True,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert (
        "PASS noc_sram_packet_mesh4x4 req0=8 req3=3 write12=3 write15=8"
        in result.stdout
    )


@pytest.mark.skipif(_tool("yosys") is None, reason="yosys unavailable")
def test_noc_sram_packet_mesh4x4_synthesis_hierarchy(tmp_path: Path) -> None:
    script = tmp_path / "mesh.ys"
    script.write_text(
        "\n".join(
            [
                f"read_verilog -DSYNTHESIS -sv {' '.join(str(path) for path in RTL_SOURCES)}",
                "hierarchy -check -top noc_sram_packet_mesh4x4",
                "proc",
                "check",
            ]
        ),
        encoding="utf-8",
    )
    subprocess.run(
        [str(_tool("yosys")), "-q", "-s", str(script)],
        check=True,
        cwd=REPO_ROOT,
        timeout=60,
    )


@pytest.mark.skipif(_tool("verilator") is None, reason="verilator unavailable")
def test_noc_sram_packet_mesh4x4_has_no_combinational_ready_cycle() -> None:
    result = subprocess.run(
        [
            str(_tool("verilator")),
            "--lint-only",
            "-Wall",
            "-Wno-fatal",
            "--top-module",
            "noc_sram_packet_mesh4x4",
            *[str(path) for path in RTL_SOURCES],
        ],
        check=True,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )
    diagnostics = result.stdout + result.stderr
    assert "UNOPTFLAT" not in diagnostics


@pytest.mark.skipif(
    _tool("iverilog") is None or _tool("vvp") is None,
    reason="iverilog/vvp unavailable",
)
def test_noc_fifo_full_credit_recovers_one_cycle_later(tmp_path: Path) -> None:
    tb = tmp_path / "tb_registered_credit.sv"
    tb.write_text(
        """
module tb_registered_credit;
  reg clk = 1'b0;
  reg rst_n = 1'b0;
  reg in_valid = 1'b0;
  wire in_ready;
  reg [7:0] in_data = 0;
  wire out_valid;
  reg out_ready = 1'b0;
  wire [7:0] out_data;
  wire [1:0] occupancy;
  always #5 clk = ~clk;
  noc_ready_valid_fifo #(.WIDTH(8), .DEPTH(2)) dut (
    .clk(clk), .rst_n(rst_n),
    .in_valid(in_valid), .in_ready(in_ready), .in_data(in_data),
    .out_valid(out_valid), .out_ready(out_ready), .out_data(out_data),
    .occupancy(occupancy), .max_occupancy()
  );
  initial begin
    repeat (2) @(posedge clk);
    @(negedge clk); rst_n = 1'b1; in_valid = 1'b1; in_data = 8'h11;
    @(posedge clk); #1;
    @(negedge clk); in_data = 8'h22;
    @(posedge clk); #1;
    if (occupancy != 2 || in_ready || out_data != 8'h11)
      $fatal(1, "FIFO did not reach full state");
    @(negedge clk); out_ready = 1'b1; in_data = 8'h33;
    #1;
    if (in_ready)
      $fatal(1, "full FIFO leaked combinational downstream ready");
    @(posedge clk); #1;
    if (occupancy != 1 || !in_ready || out_data != 8'h22)
      $fatal(1, "credit did not return after registered pop");
    @(posedge clk); #1;
    if (occupancy != 1 || out_data != 8'h33)
      $fatal(1, "simultaneous non-full push/pop failed");
    @(negedge clk); in_valid = 1'b0;
    @(posedge clk); #1;
    if (occupancy != 0 || out_valid)
      $fatal(1, "FIFO did not drain");
    $display("PASS registered occupancy credit");
    $finish;
  end
endmodule
""",
        encoding="utf-8",
    )
    sim = tmp_path / "registered_credit.vvp"
    subprocess.run(
        [
            str(_tool("iverilog")),
            "-g2012",
            "-s",
            "tb_registered_credit",
            "-o",
            str(sim),
            str(RTL_SOURCES[0]),
            str(tb),
        ],
        check=True,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    result = subprocess.run(
        [str(_tool("vvp")), str(sim)],
        check=True,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert "PASS registered occupancy credit" in result.stdout


@pytest.mark.skipif(
    _tool("iverilog") is None or _tool("vvp") is None,
    reason="iverilog/vvp unavailable",
)
def test_noc_sram_packet_mesh4x4_ppa_harness_makes_progress(tmp_path: Path) -> None:
    tb = tmp_path / "tb_composed_ppa.sv"
    tb.write_text(
        """
module tb_composed_ppa;
  reg clk = 1'b0;
  reg rst_n = 1'b0;
  wire [15:0] observed_valid;
  wire [255:0] observed_flit;
  wire [31:0] issued_packet_count;
  wire [31:0] completed_packet_count;
  wire protocol_error;
  reg [15:0] observed_nodes = 0;
  reg [255:0] observed_bits = 0;
  integer cycle;
  always #1 clk = ~clk;
  noc_sram_packet_mesh4x4_ppa_harness dut (
    .clk(clk), .rst_n(rst_n),
    .observed_valid(observed_valid), .observed_flit(observed_flit),
    .issued_packet_count(issued_packet_count),
    .completed_packet_count(completed_packet_count),
    .protocol_error(protocol_error)
  );
  initial begin
    repeat (3) @(posedge clk);
    rst_n = 1'b1;
    for (cycle = 0; cycle < 4096; cycle = cycle + 1) begin
      @(posedge clk);
      if (^observed_flit === 1'bx)
        $fatal(1, "unknown compact observation");
      if (protocol_error)
        $fatal(1, "composed harness protocol error endpoints=%h state=%0d epoch=%0d",
          dut.endpoint_protocol_error, dut.setup_state, dut.epoch);
      observed_nodes = observed_nodes | observed_valid;
      observed_bits = observed_bits | observed_flit;
    end
    if (issued_packet_count < 128 || completed_packet_count < 112)
      $fatal(1, "insufficient packet progress");
    if (observed_nodes != 16'hffff || observed_bits == 0)
      $fatal(1, "incomplete endpoint observation");
    $display("PASS composed_ppa issued=%0d completed=%0d observed=%h",
      issued_packet_count, completed_packet_count, observed_nodes);
    $finish;
  end
endmodule
""",
        encoding="utf-8",
    )
    sim = tmp_path / "composed_ppa.vvp"
    subprocess.run(
        [
            str(_tool("iverilog")),
            "-g2012",
            "-s",
            "tb_composed_ppa",
            "-o",
            str(sim),
            *[str(path) for path in RTL_SOURCES],
            str(HARNESS),
            str(tb),
        ],
        check=True,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    result = subprocess.run(
        [str(_tool("vvp")), str(sim)],
        check=True,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert "PASS composed_ppa" in result.stdout


def test_noc_sram_packet_mesh4x4_generator_emits_exact_hierarchy(
    tmp_path: Path,
) -> None:
    config = json.loads(PPA_CONFIG.read_text(encoding="utf-8"))
    design = identify_design(config)
    assert design["primitive"] == "sram_packet_mesh4x4"
    generate_l1_memory_noc_design(str(tmp_path), design)
    generate_wrapper(config, str(tmp_path), design)

    expected_sources = {
        "noc_ready_valid_fifo.v",
        "noc_segmented_mesh_router.v",
        "noc_segmented_mesh4x4.v",
        "noc_sram_packet_endpoint.v",
        "noc_sram_packet_mesh4x4.v",
        "noc_sram_packet_mesh4x4_ppa_harness.v",
        f"{design['module_name']}.v",
        f"{design['wrapper_name']}.v",
    }
    assert expected_sources <= {path.name for path in tmp_path.glob("*.v")}

    iverilog = _tool("iverilog")
    if iverilog is None:
        pytest.skip("iverilog unavailable")
    subprocess.run(
        [
            iverilog,
            "-g2012",
            "-s",
            design["wrapper_name"],
            "-t",
            "null",
            *[str(path) for path in sorted(tmp_path.glob("*.v"))],
        ],
        check=True,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )
