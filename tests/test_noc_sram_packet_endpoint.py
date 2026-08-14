from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.sim.perf.noc_segmented_mesh import (  # noqa: E402
    TrafficFlow,
    packetize_traffic_flow,
)
from scripts.generate_design import (  # noqa: E402
    _emit_l1_sram_packet_endpoint,
    generate_wrapper,
    identify_design,
)

RTL = REPO_ROOT / "npu/sim/rtl/noc_sram_packet_endpoint.sv"
TB = REPO_ROOT / "tests/noc_sram_packet_endpoint_tb.sv"
PPA_CONFIG = (
    REPO_ROOT
    / "runs/designs/noc/l1_noc_sram_packet_endpoint_w256_td4_to8_rx8_wrapper"
    / "config_l1_noc_sram_packet_endpoint_w256_td4_to8_rx8.json"
)


def test_noc_sram_packet_endpoint_protocol(tmp_path: Path) -> None:
    iverilog = shutil.which("iverilog") or "/oss-cad-suite/bin/iverilog"
    vvp = shutil.which("vvp") or "/oss-cad-suite/bin/vvp"
    sim = tmp_path / "noc_sram_packet_endpoint_sim"
    subprocess.run(
        [
            iverilog,
            "-g2012",
            "-s",
            "noc_sram_packet_endpoint_tb",
            "-o",
            str(sim),
            str(RTL),
            str(TB),
        ],
        check=True,
        cwd=REPO_ROOT,
    )
    result = subprocess.run(
        [vvp, str(sim)],
        check=True,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert "PASS noc_sram_packet_endpoint requests=10 tx=10 writes=5 completions=2" in result.stdout
    observed = [
        tuple(int(value) for value in line.split()[1:])
        for line in result.stdout.splitlines()
        if line.startswith("TXTRACE ")
    ]
    expected = []
    for flow in (
        TrafficFlow(
            name="packet0",
            source=2,
            destination=5,
            payload_bytes=256,
            vc=1,
            packet_payload_bytes=256,
            tag_base=0xA1,
        ),
        TrafficFlow(
            name="packet1",
            source=2,
            destination=9,
            payload_bytes=64,
            vc=2,
            packet_payload_bytes=64,
            tag_base=0xB2,
        ),
    ):
        expected.extend(
            (
                scheduled.flit.source,
                scheduled.flit.destination,
                scheduled.flit.vc,
                scheduled.flit.tag,
                scheduled.flit.fragment,
                int(scheduled.flit.last),
            )
            for scheduled in packetize_traffic_flow(flow)
        )
    assert observed == expected


def test_noc_sram_packet_endpoint_synthesizes(tmp_path: Path) -> None:
    yosys = shutil.which("yosys") or "/oss-cad-suite/bin/yosys"
    subprocess.run(
        [
            yosys,
            "-q",
            "-p",
            f"read_verilog -DSYNTHESIS -sv {RTL}; "
            "hierarchy -check -top noc_sram_packet_endpoint; proc; check",
        ],
        check=True,
        cwd=REPO_ROOT,
    )


def test_noc_sram_packet_endpoint_ppa_harness_is_compact_live_and_compiles(
    tmp_path: Path,
) -> None:
    config = json.loads(PPA_CONFIG.read_text(encoding="utf-8"))
    design = identify_design(config)
    assert design["primitive"] == "sram_packet_endpoint"
    generated = _emit_l1_sram_packet_endpoint(design["module_name"], design)
    assert "output [255:0] observed_flit" in generated
    assert "input [3:0] rx_destination_probe" in generated
    assert "output [31:0] issued_packet_count" in generated
    assert ".TX_DESC_DEPTH(4)" in generated
    assert ".TX_OUTSTANDING(8)" in generated
    assert ".RX_CONTEXTS(8)" in generated
    assert "tx_mem_req_addr" in generated
    assert "rx_mem_write_addr" in generated

    generated_path = tmp_path / f"{design['module_name']}.v"
    generated_path.write_text(generated, encoding="utf-8")
    generate_wrapper(config, str(tmp_path), design)
    wrapper_path = tmp_path / f"{design['wrapper_name']}.v"
    tb_path = tmp_path / "tb_endpoint_ppa.sv"
    tb_path.write_text(
        f"""
module tb_endpoint_ppa;
  reg clk = 1'b0;
  reg rst_n = 1'b0;
  reg [3:0] rx_destination_probe = 4'd2;
  wire [255:0] observed_flit;
  wire [31:0] issued_packet_count;
  wire [31:0] completed_packet_count;
  wire protocol_error;
  always #1 clk = ~clk;
  {design['wrapper_name']} dut (
    .clk(clk), .rst_n(rst_n),
    .rx_destination_probe(rx_destination_probe), .observed_flit(observed_flit),
    .issued_packet_count(issued_packet_count),
    .completed_packet_count(completed_packet_count),
    .protocol_error(protocol_error)
  );
  initial begin
    repeat (3) @(posedge clk);
    rst_n = 1'b1;
    repeat (1024) begin
      @(posedge clk);
      if (^observed_flit === 1'bx) $fatal(1, "unknown observed signature");
      if (protocol_error) $fatal(1, "endpoint harness protocol error");
    end
    if (issued_packet_count < 8 || completed_packet_count < 4)
      $fatal(1, "endpoint harness did not exercise queued packets");
    $display("PASS endpoint_ppa issued=%0d completed=%0d", issued_packet_count, completed_packet_count);
    $finish;
  end
endmodule
""",
        encoding="utf-8",
    )
    iverilog = shutil.which("iverilog") or "/oss-cad-suite/bin/iverilog"
    vvp = shutil.which("vvp") or "/oss-cad-suite/bin/vvp"
    sim = tmp_path / "endpoint_ppa_sim"
    subprocess.run(
        [
            iverilog,
            "-g2012",
            "-s",
            "tb_endpoint_ppa",
            "-o",
            str(sim),
            str(generated_path),
            str(wrapper_path),
            str(tb_path),
        ],
        check=True,
        cwd=REPO_ROOT,
    )
    result = subprocess.run(
        [vvp, str(sim)],
        check=True,
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    assert "PASS endpoint_ppa" in result.stdout
