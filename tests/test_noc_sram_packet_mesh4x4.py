from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
RTL_SOURCES = [
    REPO_ROOT / "npu/sim/rtl/noc_ready_valid_fifo.sv",
    REPO_ROOT / "npu/sim/rtl/noc_segmented_mesh_router.sv",
    REPO_ROOT / "npu/sim/rtl/noc_segmented_mesh4x4.sv",
    REPO_ROOT / "npu/sim/rtl/noc_sram_packet_endpoint.sv",
    REPO_ROOT / "npu/sim/rtl/noc_sram_packet_mesh4x4.sv",
]
TB = REPO_ROOT / "tests/noc_sram_packet_mesh4x4_tb.sv"


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
