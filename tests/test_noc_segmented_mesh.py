from __future__ import annotations

import re
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.sim.perf.noc_segmented_mesh import (
    ModelFlit,
    PORT_EAST,
    PORT_LOCAL,
    PORT_NAMES,
    PORT_NORTH,
    PORT_SOUTH,
    PORT_WEST,
    PORTS,
    RouterCycleInput,
    segmented_transfer,
    simulate_mesh,
    simulate_router,
)
ROUTER_CONFIG = (
    REPO_ROOT
    / "runs"
    / "designs"
    / "noc"
    / "l1_noc_segmented_xy_router_p5_w256_vc4_d4_wrapper"
    / "config_l1_noc_segmented_xy_router_p5_w256_vc4_d4.json"
)
GENERATED_SRC = Path("/orfs/flow/designs/src/l1_noc_segmented_xy_router_p5_w256_vc4_d4_wrapper")


def _iverilog() -> str | None:
    return shutil.which("iverilog") or ("/oss-cad-suite/bin/iverilog" if Path("/oss-cad-suite/bin/iverilog").exists() else None)


def _vvp() -> str | None:
    return shutil.which("vvp") or ("/oss-cad-suite/bin/vvp" if Path("/oss-cad-suite/bin/vvp").exists() else None)


def _compile_and_run(tmp_path: Path, *, top: str, sources: list[Path], tb_text: str) -> str:
    iverilog = _iverilog()
    vvp = _vvp()
    if iverilog is None or vvp is None:
        pytest.skip("iverilog/vvp unavailable")
    tb_path = tmp_path / f"{top}.sv"
    tb_path.write_text(tb_text, encoding="utf-8")
    simv = tmp_path / f"{top}.vvp"
    subprocess.run(
        [iverilog, "-g2012", "-s", top, "-o", str(simv), *[str(source) for source in sources], str(tb_path)],
        check=True,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    run = subprocess.run([vvp, str(simv)], check=True, cwd=REPO_ROOT, capture_output=True, text=True, timeout=20)
    return run.stdout


def _router_flit(*, source: int, destination: int, tag: int, fragment: int, vc: int, data: int) -> ModelFlit:
    return ModelFlit(
        source=source,
        destination=destination,
        tag=tag,
        fragment=fragment,
        last=fragment == 7,
        vc=vc,
        data=data,
    )


def _router_scenario() -> tuple[list[list[RouterCycleInput]], list[list[bool]]]:
    schedule = [[RouterCycleInput(False, None) for _ in range(PORTS)] for _ in range(12)]
    ready = [[True for _ in range(PORTS)] for _ in range(12)]

    east_dest = 6
    local_dest = 5

    schedule[0][PORT_LOCAL] = RouterCycleInput(True, _router_flit(source=4, destination=east_dest, tag=10, fragment=0, vc=0, data=0x100))
    schedule[1][PORT_NORTH] = RouterCycleInput(True, _router_flit(source=0, destination=east_dest, tag=20, fragment=0, vc=0, data=0x200))
    schedule[1][PORT_LOCAL] = RouterCycleInput(True, _router_flit(source=4, destination=east_dest, tag=11, fragment=1, vc=0, data=0x101))
    schedule[2][PORT_SOUTH] = RouterCycleInput(True, _router_flit(source=1, destination=east_dest, tag=30, fragment=0, vc=1, data=0x300))
    schedule[2][PORT_LOCAL] = RouterCycleInput(True, _router_flit(source=4, destination=east_dest, tag=12, fragment=2, vc=0, data=0x102))
    schedule[3][PORT_LOCAL] = RouterCycleInput(True, _router_flit(source=4, destination=east_dest, tag=13, fragment=3, vc=0, data=0x103))
    schedule[4][PORT_LOCAL] = RouterCycleInput(True, _router_flit(source=4, destination=east_dest, tag=14, fragment=4, vc=0, data=0x104))
    schedule[6][PORT_WEST] = RouterCycleInput(True, _router_flit(source=3, destination=local_dest, tag=40, fragment=0, vc=2, data=0x400))

    ready[2][PORT_EAST] = False
    ready[3][PORT_EAST] = False
    ready[7][PORT_LOCAL] = False
    return schedule, ready


def _router_tb(schedule: list[list[RouterCycleInput]], ready: list[list[bool]]) -> str:
    def pack_bus(values: list[int], field_width: int) -> int:
        packed = 0
        for index, value in enumerate(values):
            packed |= int(value) << (index * field_width)
        return packed

    def emit_cycle(cycle: int) -> str:
        valid_bits = 0
        dests: list[int] = []
        sources: list[int] = []
        tags: list[int] = []
        fragments: list[int] = []
        lasts: list[int] = []
        vcs: list[int] = []
        datas: list[int] = []
        for port, item in enumerate(schedule[cycle]):
            if item.valid:
                valid_bits |= 1 << port
                flit = item.flit
                assert flit is not None
                dests.append(flit.destination)
                sources.append(flit.source)
                tags.append(flit.tag)
                fragments.append(flit.fragment)
                lasts.append(1 if flit.last else 0)
                vcs.append(flit.vc)
                datas.append(flit.data)
            else:
                dests.append(0)
                sources.append(0)
                tags.append(0)
                fragments.append(0)
                lasts.append(0)
                vcs.append(0)
                datas.append(0)
        ready_bits = sum((1 if bit else 0) << idx for idx, bit in enumerate(ready[cycle]))
        packed_dest = pack_bus(dests, 4)
        packed_source = pack_bus(sources, 4)
        packed_tag = pack_bus(tags, 8)
        packed_fragment = pack_bus(fragments, 3)
        packed_vc = pack_bus(vcs, 2)
        packed_data = pack_bus(datas, 256)
        return textwrap.dedent(
            f"""\
            {cycle}: begin
              in_valid = 5'b{valid_bits:05b};
              in_dest = 20'h{packed_dest:05x};
              in_source = 20'h{packed_source:05x};
              in_tag = 40'h{packed_tag:010x};
              in_fragment = 15'h{packed_fragment:04x};
              in_last = 5'b{''.join(str(bit) for bit in reversed(lasts))};
              in_vc = 10'h{packed_vc:03x};
              in_data = 1280'h{packed_data:0320x};
              out_ready = 5'b{ready_bits:05b};
            end
            """
        )

    cycle_cases = "".join(emit_cycle(cycle) for cycle in range(len(schedule)))
    return f"""
`timescale 1ns/1ps
module tb_noc_segmented_mesh_router;
  reg clk;
  reg rst_n;
  reg [4:0] in_valid;
  wire [4:0] in_ready;
  reg [19:0] in_dest;
  reg [19:0] in_source;
  reg [39:0] in_tag;
  reg [14:0] in_fragment;
  reg [4:0] in_last;
  reg [9:0] in_vc;
  reg [1279:0] in_data;
  wire [4:0] out_valid;
  reg [4:0] out_ready;
  wire [19:0] out_dest;
  wire [19:0] out_source;
  wire [39:0] out_tag;
  wire [14:0] out_fragment;
  wire [4:0] out_last;
  wire [9:0] out_vc;
  wire [1279:0] out_data;
  wire [31:0] accepted_flit_count;
  wire [31:0] forwarded_flit_count;
  wire [31:0] input_stall_cycles;
  wire [31:0] output_stall_cycles;
  wire [31:0] arbitration_contention_cycles;
  wire [31:0] current_input_occupancy;
  wire [31:0] max_input_occupancy;
  wire [159:0] route_flit_count;
  integer cycle_count;
  integer drive_i;
  integer log_i;

  noc_segmented_mesh_router #(
    .X_COORD(1),
    .Y_COORD(1)
  ) dut (
    .clk(clk),
    .rst_n(rst_n),
    .in_valid(in_valid),
    .in_ready(in_ready),
    .in_dest(in_dest),
    .in_source(in_source),
    .in_tag(in_tag),
    .in_fragment(in_fragment),
    .in_last(in_last),
    .in_vc(in_vc),
    .in_data(in_data),
    .out_valid(out_valid),
    .out_ready(out_ready),
    .out_dest(out_dest),
    .out_source(out_source),
    .out_tag(out_tag),
    .out_fragment(out_fragment),
    .out_last(out_last),
    .out_vc(out_vc),
    .out_data(out_data),
    .accepted_flit_count(accepted_flit_count),
    .forwarded_flit_count(forwarded_flit_count),
    .input_stall_cycles(input_stall_cycles),
    .output_stall_cycles(output_stall_cycles),
    .arbitration_contention_cycles(arbitration_contention_cycles),
    .current_input_occupancy(current_input_occupancy),
    .max_input_occupancy(max_input_occupancy),
    .route_flit_count(route_flit_count)
  );

  initial clk = 1'b0;
  always #5 clk = ~clk;

  task automatic drive_cycle(input integer cycle);
    begin
      case (cycle)
{textwrap.indent(cycle_cases, '        ')}        default: begin
          in_valid = 5'b00000;
          in_dest = 20'h0;
          in_source = 20'h0;
          in_tag = 40'h0;
          in_fragment = 15'h0;
          in_last = 5'b00000;
          in_vc = 10'h0;
          in_data = 1280'h0;
          out_ready = 5'b11111;
        end
      endcase
    end
  endtask

  initial begin
    rst_n = 1'b0;
    cycle_count = -1;
    drive_cycle(-1);
    repeat (2) @(posedge clk);
    @(negedge clk);
    rst_n = 1'b1;
    drive_cycle(0);
    for (drive_i = 1; drive_i < {len(schedule)}; drive_i = drive_i + 1) begin
      @(negedge clk);
      drive_cycle(drive_i);
    end
    @(negedge clk);
    drive_cycle(-1);
    repeat (6) @(posedge clk);
    $display("SUMMARY accepted=%0d forwarded=%0d istall=%0d ostall=%0d contention=%0d occ=%0d maxocc=%0d east=%0d local=%0d",
      accepted_flit_count,
      forwarded_flit_count,
      input_stall_cycles,
      output_stall_cycles,
      arbitration_contention_cycles,
      current_input_occupancy,
      max_input_occupancy,
      route_flit_count[95:64],
      route_flit_count[159:128]);
    $finish;
  end

  always @(posedge clk) begin
    if (rst_n) begin
      cycle_count = cycle_count + 1;
      for (log_i = 0; log_i < 5; log_i = log_i + 1) begin
        if (out_valid[log_i] && out_ready[log_i]) begin
          $display("FWD cycle=%0d port=%0d source=%0d dest=%0d tag=%0d fragment=%0d vc=%0d last=%0d",
            cycle_count,
            log_i,
            out_source[(log_i * 4) +: 4],
            out_dest[(log_i * 4) +: 4],
            out_tag[(log_i * 8) +: 8],
            out_fragment[(log_i * 3) +: 3],
            out_vc[(log_i * 2) +: 2],
            out_last[log_i]);
        end
      end
    end
  end
endmodule
"""


def _mesh_tb() -> str:
    return """
`timescale 1ns/1ps
module tb_noc_segmented_mesh4x4;
  reg clk;
  reg rst_n;
  reg [15:0] endpoint_in_valid;
  wire [15:0] endpoint_in_ready;
  reg [63:0] endpoint_in_dest;
  reg [63:0] endpoint_in_source;
  reg [127:0] endpoint_in_tag;
  reg [47:0] endpoint_in_fragment;
  reg [15:0] endpoint_in_last;
  reg [31:0] endpoint_in_vc;
  reg [4095:0] endpoint_in_data;
  wire [15:0] endpoint_out_valid;
  reg [15:0] endpoint_out_ready;
  wire [63:0] endpoint_out_dest;
  wire [63:0] endpoint_out_source;
  wire [127:0] endpoint_out_tag;
  wire [47:0] endpoint_out_fragment;
  wire [15:0] endpoint_out_last;
  wire [31:0] endpoint_out_vc;
  wire [4095:0] endpoint_out_data;
  integer cycle_count;
  integer fragment_index;
  integer delivered_count;

  noc_segmented_mesh4x4 dut (
    .clk(clk),
    .rst_n(rst_n),
    .endpoint_in_valid(endpoint_in_valid),
    .endpoint_in_ready(endpoint_in_ready),
    .endpoint_in_dest(endpoint_in_dest),
    .endpoint_in_source(endpoint_in_source),
    .endpoint_in_tag(endpoint_in_tag),
    .endpoint_in_fragment(endpoint_in_fragment),
    .endpoint_in_last(endpoint_in_last),
    .endpoint_in_vc(endpoint_in_vc),
    .endpoint_in_data(endpoint_in_data),
    .endpoint_out_valid(endpoint_out_valid),
    .endpoint_out_ready(endpoint_out_ready),
    .endpoint_out_dest(endpoint_out_dest),
    .endpoint_out_source(endpoint_out_source),
    .endpoint_out_tag(endpoint_out_tag),
    .endpoint_out_fragment(endpoint_out_fragment),
    .endpoint_out_last(endpoint_out_last),
    .endpoint_out_vc(endpoint_out_vc),
    .endpoint_out_data(endpoint_out_data),
    .router_accepted_flit_count(),
    .router_forwarded_flit_count(),
    .router_input_stall_cycles(),
    .router_output_stall_cycles(),
    .router_contention_cycles(),
    .router_current_input_occupancy(),
    .router_max_input_occupancy(),
    .router_route_flit_count()
  );

  initial clk = 1'b0;
  always #5 clk = ~clk;

  task automatic drive_source;
    begin
      endpoint_in_valid = 16'h0000;
      endpoint_in_dest = 64'h0;
      endpoint_in_source = 64'h0;
      endpoint_in_tag = 128'h0;
      endpoint_in_fragment = 48'h0;
      endpoint_in_last = 16'h0000;
      endpoint_in_vc = 32'h0;
      endpoint_in_data = 4096'h0;
      if (fragment_index < 8) begin
        endpoint_in_valid[0] = 1'b1;
        endpoint_in_dest[3:0] = 4'd15;
        endpoint_in_source[3:0] = 4'd0;
        endpoint_in_tag[7:0] = 8'd7;
        endpoint_in_fragment[2:0] = fragment_index[2:0];
        endpoint_in_last[0] = (fragment_index == 7);
        endpoint_in_vc[1:0] = 2'd1;
        endpoint_in_data[255:0] = fragment_index;
      end
    end
  endtask

  initial begin
    rst_n = 1'b0;
    cycle_count = -1;
    fragment_index = 0;
    delivered_count = 0;
    endpoint_out_ready = 16'h8000;
    drive_source();
    repeat (2) @(posedge clk);
    @(negedge clk);
    rst_n = 1'b1;
    drive_source();
    repeat (40) begin
      @(posedge clk);
      @(negedge clk);
      drive_source();
    end
    $display("SUMMARY delivered=%0d", delivered_count);
    $finish;
  end

  always @(posedge clk) begin
    if (rst_n) begin
      cycle_count = cycle_count + 1;
      if (endpoint_in_valid[0] && endpoint_in_ready[0])
        fragment_index = fragment_index + 1;
      if (endpoint_out_valid[15] && endpoint_out_ready[15]) begin
        delivered_count = delivered_count + 1;
        $display("DELIVER cycle=%0d source=%0d dest=%0d tag=%0d fragment=%0d vc=%0d last=%0d",
          cycle_count,
          endpoint_out_source[63:60],
          endpoint_out_dest[63:60],
          endpoint_out_tag[127:120],
          endpoint_out_fragment[47:45],
          endpoint_out_vc[31:30],
          endpoint_out_last[15]);
      end
    end
  end
endmodule
"""


def test_segmented_router_wrapper_generates_and_compiles() -> None:
    subprocess.run(
        ["python3", "scripts/generate_design.py", str(ROUTER_CONFIG), "nangate45", "--force_gen", "True"],
        check=True,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    expected = {
        "l1_noc_segmented_xy_router_p5_w256_vc4_d4.v",
        "l1_noc_segmented_xy_router_p5_w256_vc4_d4_wrapper.v",
        "noc_ready_valid_fifo.v",
        "noc_segmented_mesh_router.v",
    }
    assert expected.issubset({path.name for path in GENERATED_SRC.iterdir()})

    iverilog = _iverilog()
    if iverilog is None:
        pytest.skip("iverilog unavailable")
    subprocess.run(
        [
            iverilog,
            "-g2012",
            "-s",
            "l1_noc_segmented_xy_router_p5_w256_vc4_d4_wrapper",
            "-t",
            "null",
            str(GENERATED_SRC / "noc_ready_valid_fifo.v"),
            str(GENERATED_SRC / "noc_segmented_mesh_router.v"),
            str(GENERATED_SRC / "l1_noc_segmented_xy_router_p5_w256_vc4_d4.v"),
            str(GENERATED_SRC / "l1_noc_segmented_xy_router_p5_w256_vc4_d4_wrapper.v"),
        ],
        check=True,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )


@pytest.mark.skipif(_iverilog() is None or _vvp() is None, reason="iverilog/vvp unavailable")
def test_router_cycle_model_matches_rtl(tmp_path: Path) -> None:
    schedule, ready = _router_scenario()
    expected = simulate_router(
        x_coord=1,
        y_coord=1,
        input_schedule=schedule,
        out_ready_schedule=ready,
    )
    output = _compile_and_run(
        tmp_path,
        top="tb_noc_segmented_mesh_router",
        sources=[
            REPO_ROOT / "npu/sim/rtl/noc_ready_valid_fifo.sv",
            REPO_ROOT / "npu/sim/rtl/noc_segmented_mesh_router.sv",
        ],
        tb_text=_router_tb(schedule, ready),
    )

    fwd_pattern = re.compile(
        r"FWD cycle=(?P<cycle>\d+) port=(?P<port>\d+) source=(?P<source>\d+) dest=(?P<dest>\d+) "
        r"tag=(?P<tag>\d+) fragment=(?P<fragment>\d+) vc=(?P<vc>\d+) last=(?P<last>\d+)"
    )
    summary_pattern = re.compile(
        r"SUMMARY accepted=(?P<accepted>\d+) forwarded=(?P<forwarded>\d+) istall=(?P<istall>\d+) "
        r"ostall=(?P<ostall>\d+) contention=(?P<contention>\d+) occ=(?P<occ>\d+) "
        r"maxocc=(?P<maxocc>\d+) east=(?P<east>\d+) local=(?P<local>\d+)"
    )

    observed = []
    summary_match = None
    for line in output.splitlines():
        match = fwd_pattern.match(line.strip())
        if match:
            observed.append({key: int(value) for key, value in match.groupdict().items()})
            continue
        summary_match = summary_match or summary_pattern.match(line.strip())

    assert summary_match is not None, output
    summary = {key: int(value) for key, value in summary_match.groupdict().items()}

    expected_forwarded = [
        {
            "cycle": trace.cycle,
            "port": port,
            "source": flit.source,
            "dest": flit.destination,
            "tag": flit.tag,
            "fragment": flit.fragment,
            "vc": flit.vc,
            "last": 1 if flit.last else 0,
        }
        for trace in expected.traces
        for port, flit in trace.forwarded
    ]

    assert observed == expected_forwarded
    assert summary["accepted"] == expected.accepted_flit_count
    assert summary["forwarded"] == expected.forwarded_flit_count
    assert summary["istall"] == expected.input_stall_cycles
    assert summary["ostall"] == expected.output_stall_cycles
    assert summary["contention"] == expected.arbitration_contention_cycles
    assert summary["occ"] == expected.current_input_occupancy
    assert summary["maxocc"] == expected.max_input_occupancy
    assert summary["east"] == expected.route_flit_count[PORT_EAST]
    assert summary["local"] == expected.route_flit_count[PORT_LOCAL]


@pytest.mark.skipif(_iverilog() is None or _vvp() is None, reason="iverilog/vvp unavailable")
def test_mesh_route_model_matches_rtl(tmp_path: Path) -> None:
    expected = simulate_mesh(source=0, destination=15, tag=7, vc=1)
    output = _compile_and_run(
        tmp_path,
        top="tb_noc_segmented_mesh4x4",
        sources=[
            REPO_ROOT / "npu/sim/rtl/noc_ready_valid_fifo.sv",
            REPO_ROOT / "npu/sim/rtl/noc_segmented_mesh_router.sv",
            REPO_ROOT / "npu/sim/rtl/noc_segmented_mesh4x4.sv",
        ],
        tb_text=_mesh_tb(),
    )

    delivery_pattern = re.compile(
        r"DELIVER cycle=(?P<cycle>\d+) source=(?P<source>\d+) dest=(?P<dest>\d+) "
        r"tag=(?P<tag>\d+) fragment=(?P<fragment>\d+) vc=(?P<vc>\d+) last=(?P<last>\d+)"
    )
    summary_pattern = re.compile(r"SUMMARY delivered=(?P<delivered>\d+)")
    observed = []
    summary_match = None
    for line in output.splitlines():
        match = delivery_pattern.match(line.strip())
        if match:
            observed.append({key: int(value) for key, value in match.groupdict().items()})
            continue
        summary_match = summary_match or summary_pattern.match(line.strip())

    assert summary_match is not None, output
    assert int(summary_match.group("delivered")) == len(expected["delivered"])

    expected_deliveries = [
        {
            "cycle": int(item["cycle"]),
            "source": int(item["source"]),
            "dest": int(item["destination"]),
            "tag": int(item["tag"]),
            "fragment": int(item["fragment"]),
            "vc": int(item["vc"]),
            "last": 1 if item["last"] else 0,
        }
        for item in expected["delivered"]
    ]
    assert observed == expected_deliveries
