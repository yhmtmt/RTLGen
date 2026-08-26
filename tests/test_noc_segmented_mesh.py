from __future__ import annotations

import json
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
    MeshDelivery,
    ModelFlit,
    PORT_EAST,
    PORT_LOCAL,
    PORT_NAMES,
    PORT_NORTH,
    PORT_SOUTH,
    PORT_WEST,
    PORTS,
    RouterCycleInput,
    TrafficFlow,
    coordinates,
    extract_router_replay_schedules,
    packetize_traffic_flow,
    segmented_transfer,
    simulate_mesh,
    simulate_router,
    simulate_scheduled_flits,
)
from scripts.generate_design import (
    _emit_l1_segmented_mesh4x4,
    _emit_l1_segmented_router,
    generate_wrapper,
    identify_design,
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
MESH_PPA_CONFIG = (
    REPO_ROOT
    / "runs"
    / "designs"
    / "noc"
    / "l1_noc_segmented_xy_mesh4x4_w256_vc4_d4_wrapper"
    / "config_l1_noc_segmented_xy_mesh4x4_w256_vc4_d4.json"
)


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


def _multiflow_mesh_flows() -> list[TrafficFlow]:
    return [
        TrafficFlow(
            name="shared_a",
            source=0,
            destination=15,
            payload_bytes=256,
            vc=0,
            release_cycle=0,
            packet_payload_bytes=256,
            tag_base=7,
            data_seed=1,
        ),
        TrafficFlow(
            name="shared_b",
            source=1,
            destination=15,
            payload_bytes=256,
            vc=1,
            release_cycle=0,
            packet_payload_bytes=256,
            tag_base=17,
            data_seed=2,
        ),
        TrafficFlow(
            name="reduction_c",
            source=4,
            destination=15,
            payload_bytes=256,
            vc=0,
            release_cycle=0,
            packet_payload_bytes=256,
            tag_base=27,
            data_seed=3,
        ),
    ]


def _multiflow_mesh_ready() -> list[list[bool]]:
    ready = [[False for _ in range(16)] for _ in range(64)]
    for cycle in range(64):
        ready[cycle][15] = cycle not in {14, 15}
    return ready


def _multiflow_mesh_tb() -> str:
    return """
`timescale 1ns/1ps
module tb_noc_segmented_mesh4x4_multiflow;
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
  wire [511:0] router_accepted_flit_count;
  wire [511:0] router_forwarded_flit_count;
  wire [511:0] router_input_stall_cycles;
  wire [511:0] router_output_stall_cycles;
  wire [511:0] router_contention_cycles;
  wire [511:0] router_current_input_occupancy;
  wire [511:0] router_max_input_occupancy;
  wire [2559:0] router_route_flit_count;
  integer cycle_count;
  integer drive_i;
  integer idx0;
  integer idx1;
  integer idx4;
  integer delivered_count;
  integer router_i;

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
    .router_accepted_flit_count(router_accepted_flit_count),
    .router_forwarded_flit_count(router_forwarded_flit_count),
    .router_input_stall_cycles(router_input_stall_cycles),
    .router_output_stall_cycles(router_output_stall_cycles),
    .router_contention_cycles(router_contention_cycles),
    .router_current_input_occupancy(router_current_input_occupancy),
    .router_max_input_occupancy(router_max_input_occupancy),
    .router_route_flit_count(router_route_flit_count)
  );

  initial clk = 1'b0;
  always #5 clk = ~clk;

  task automatic drive_sources;
    begin
      endpoint_in_valid = 16'h0000;
      endpoint_in_dest = 64'h0;
      endpoint_in_source = 64'h0;
      endpoint_in_tag = 128'h0;
      endpoint_in_fragment = 48'h0;
      endpoint_in_last = 16'h0000;
      endpoint_in_vc = 32'h0;
      endpoint_in_data = 4096'h0;
      if (idx0 < 8) begin
        endpoint_in_valid[0] = 1'b1;
        endpoint_in_dest[3:0] = 4'd15;
        endpoint_in_source[3:0] = 4'd0;
        endpoint_in_tag[7:0] = 8'd7;
        endpoint_in_fragment[2:0] = idx0[2:0];
        endpoint_in_last[0] = (idx0 == 7);
        endpoint_in_vc[1:0] = 2'd0;
        endpoint_in_data[255:0] = 256'h1000 + idx0;
      end
      if (idx1 < 8) begin
        endpoint_in_valid[1] = 1'b1;
        endpoint_in_dest[7:4] = 4'd15;
        endpoint_in_source[7:4] = 4'd1;
        endpoint_in_tag[15:8] = 8'd17;
        endpoint_in_fragment[5:3] = idx1[2:0];
        endpoint_in_last[1] = (idx1 == 7);
        endpoint_in_vc[3:2] = 2'd1;
        endpoint_in_data[511:256] = 256'h2000 + idx1;
      end
      if (idx4 < 8) begin
        endpoint_in_valid[4] = 1'b1;
        endpoint_in_dest[19:16] = 4'd15;
        endpoint_in_source[19:16] = 4'd4;
        endpoint_in_tag[39:32] = 8'd27;
        endpoint_in_fragment[14:12] = idx4[2:0];
        endpoint_in_last[4] = (idx4 == 7);
        endpoint_in_vc[9:8] = 2'd0;
        endpoint_in_data[1279:1024] = 256'h3000 + idx4;
      end
    end
  endtask

  task automatic drive_ready(input integer cycle);
    begin
      endpoint_out_ready = 16'h0000;
      endpoint_out_ready[15] = (cycle != 14) && (cycle != 15);
    end
  endtask

  initial begin
    rst_n = 1'b0;
    cycle_count = -1;
    idx0 = 0;
    idx1 = 0;
    idx4 = 0;
    delivered_count = 0;
    drive_ready(-1);
    drive_sources();
    repeat (2) @(posedge clk);
    @(negedge clk);
    rst_n = 1'b1;
    drive_ready(0);
    drive_sources();
    for (drive_i = 1; drive_i < 64; drive_i = drive_i + 1) begin
      @(posedge clk);
      @(negedge clk);
      drive_ready(drive_i);
      drive_sources();
    end
    $display("SUMMARY delivered=%0d", delivered_count);
    for (router_i = 0; router_i < 16; router_i = router_i + 1) begin
      $display(
        "ROUTER node=%0d accepted=%0d forwarded=%0d istall=%0d ostall=%0d contention=%0d maxocc=%0d local=%0d east=%0d south=%0d",
        router_i,
        router_accepted_flit_count[(router_i * 32) +: 32],
        router_forwarded_flit_count[(router_i * 32) +: 32],
        router_input_stall_cycles[(router_i * 32) +: 32],
        router_output_stall_cycles[(router_i * 32) +: 32],
        router_contention_cycles[(router_i * 32) +: 32],
        router_max_input_occupancy[(router_i * 32) +: 32],
        router_route_flit_count[((router_i * 5 * 32) + (4 * 32)) +: 32],
        router_route_flit_count[((router_i * 5 * 32) + (2 * 32)) +: 32],
        router_route_flit_count[((router_i * 5 * 32) + (1 * 32)) +: 32]
      );
    end
    $finish;
  end

  always @(posedge clk) begin
    if (rst_n) begin
      cycle_count = cycle_count + 1;
      if (endpoint_in_valid[0] && endpoint_in_ready[0])
        idx0 = idx0 + 1;
      if (endpoint_in_valid[1] && endpoint_in_ready[1])
        idx1 = idx1 + 1;
      if (endpoint_in_valid[4] && endpoint_in_ready[4])
        idx4 = idx4 + 1;
      if (endpoint_out_valid[15] && endpoint_out_ready[15]) begin
        delivered_count = delivered_count + 1;
        $display(
          "DELIVER cycle=%0d source=%0d dest=%0d tag=%0d fragment=%0d vc=%0d last=%0d",
          cycle_count,
          endpoint_out_source[63:60],
          endpoint_out_dest[63:60],
          endpoint_out_tag[127:120],
          endpoint_out_fragment[47:45],
          endpoint_out_vc[31:30],
          endpoint_out_last[15]
        );
      end
    end
  end
endmodule
"""


def test_segmented_router_generator_drives_full_width_state_under_backpressure() -> None:
    config = json.loads(ROUTER_CONFIG.read_text(encoding="utf-8"))
    design = identify_design(config)
    generated_top = _emit_l1_segmented_router(design["module_name"], design)

    assert "function [DATA_W-1:0] advance_flit_data" in generated_top
    assert "in_data[(port_i * DATA_W) +: DATA_W] <= advance_flit_data(" in generated_top
    assert "flit_seed" not in generated_top
    ready_block = generated_top.split(
        "if (in_valid[port_i] && in_ready[port_i]) begin", maxsplit=1
    )[1]
    assert ready_block.index("advance_flit_data(") < ready_block.index("end")
    assert "vc_seed[port_i] <= (vc_seed[port_i] == VC_COUNT-1)" in ready_block
    assert "dest_seed[port_i] <= dest_seed[port_i] + 1'b1" in ready_block
    assert "source_seed[port_i] <= source_seed[port_i] + 1'b1" in ready_block
    assert "out_ready[port_i] <= !(tag_seed[port_i][1:0] == port_i[1:0])" in generated_top


def test_segmented_mesh4x4_ppa_top_is_compact_observable_and_compiles(tmp_path: Path) -> None:
    config = json.loads(MESH_PPA_CONFIG.read_text(encoding="utf-8"))
    design = identify_design(config)
    assert design["primitive"] == "segmented_mesh4x4"
    generated_top = _emit_l1_segmented_mesh4x4(design["module_name"], design)

    assert "output [15:0] observed_valid" in generated_top
    assert "output [255:0] observed_flit" in generated_top
    assert "dest_seed[node_i] <= dest_seed[node_i] + 4'd5" in generated_top
    assert "vc_seed[node_i] <= (vc_seed[node_i] == VC_COUNT-1)" in generated_top
    assert "node_i * OBSERVE_SLICE_W" in generated_top
    assert "output [NODES*DATA_W-1:0]" not in generated_top

    generated_path = tmp_path / "l1_noc_segmented_xy_mesh4x4_w256_vc4_d4.v"
    generated_path.write_text(generated_top, encoding="utf-8")
    generate_wrapper(config, str(tmp_path), design)
    wrapper_path = tmp_path / f"{design['wrapper_name']}.v"
    assert wrapper_path.exists()
    output = _compile_and_run(
        tmp_path,
        top="tb_segmented_mesh4x4_ppa",
        sources=[
            REPO_ROOT / "npu/sim/rtl/noc_ready_valid_fifo.sv",
            REPO_ROOT / "npu/sim/rtl/noc_segmented_mesh_router.sv",
            REPO_ROOT / "npu/sim/rtl/noc_segmented_mesh4x4.sv",
            generated_path,
            wrapper_path,
        ],
        tb_text=f"""
module tb_segmented_mesh4x4_ppa;
  reg clk = 1'b0;
  reg rst_n = 1'b0;
  wire [15:0] observed_valid;
  wire [255:0] observed_flit;
  reg [15:0] seen = 16'b0;

  always #1 clk = ~clk;

  {design['wrapper_name']} dut (
    .clk(clk),
    .rst_n(rst_n),
    .observed_valid(observed_valid),
    .observed_flit(observed_flit)
  );

  initial begin
    repeat (3) @(posedge clk);
    rst_n = 1'b1;
    repeat (512) begin
      @(posedge clk);
      seen = seen | observed_valid;
      if (^observed_flit === 1'bx)
        $fatal(1, "unknown observed flit signature");
    end
    $display("SEEN=%h", seen);
    $finish;
  end
endmodule
""",
    )
    assert "SEEN=ffff" in output


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


def test_router_round_robin_scan_does_not_reselect_wide_flits() -> None:
    rtl = (REPO_ROOT / "npu/sim/rtl/noc_segmented_mesh_router.sv").read_text(
        encoding="utf-8"
    )
    scan_start = rtl.index("for (comb_scan_i = 0;")
    grant_start = rtl.index("for (comb_grant_i = 0;", scan_start)
    scan = rtl[scan_start:grant_start]

    assert "route_request_r" in scan
    assert "fifo_out_bus" not in scan
    assert "candidate_count_r" not in rtl


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


@pytest.mark.skipif(_iverilog() is None or _vvp() is None, reason="iverilog/vvp unavailable")
def test_multiflow_mesh_cycle_model_matches_rtl(tmp_path: Path) -> None:
    flows = _multiflow_mesh_flows()
    ready = _multiflow_mesh_ready()
    scheduled = [scheduled for flow in flows for scheduled in packetize_traffic_flow(flow)]
    expected = simulate_scheduled_flits(scheduled, endpoint_out_ready_schedule=ready, max_cycles=256)
    output = _compile_and_run(
        tmp_path,
        top="tb_noc_segmented_mesh4x4_multiflow",
        sources=[
            REPO_ROOT / "npu/sim/rtl/noc_ready_valid_fifo.sv",
            REPO_ROOT / "npu/sim/rtl/noc_segmented_mesh_router.sv",
            REPO_ROOT / "npu/sim/rtl/noc_segmented_mesh4x4.sv",
        ],
        tb_text=_multiflow_mesh_tb(),
    )

    delivery_pattern = re.compile(
        r"DELIVER cycle=(?P<cycle>\d+) source=(?P<source>\d+) dest=(?P<dest>\d+) "
        r"tag=(?P<tag>\d+) fragment=(?P<fragment>\d+) vc=(?P<vc>\d+) last=(?P<last>\d+)"
    )
    summary_pattern = re.compile(r"SUMMARY delivered=(?P<delivered>\d+)")
    router_pattern = re.compile(
        r"ROUTER node=(?P<node>\d+) accepted=(?P<accepted>\d+) forwarded=(?P<forwarded>\d+) "
        r"istall=(?P<istall>\d+) ostall=(?P<ostall>\d+) contention=(?P<contention>\d+) "
        r"maxocc=(?P<maxocc>\d+) local=(?P<local>\d+) east=(?P<east>\d+) south=(?P<south>\d+)"
    )

    observed_deliveries = []
    summary_match = None
    observed_routers: dict[int, dict[str, int]] = {}
    for line in output.splitlines():
        stripped = line.strip()
        match = delivery_pattern.match(stripped)
        if match:
            observed_deliveries.append({key: int(value) for key, value in match.groupdict().items()})
            continue
        summary_match = summary_match or summary_pattern.match(stripped)
        router_match = router_pattern.match(stripped)
        if router_match:
            values = {key: int(value) for key, value in router_match.groupdict().items()}
            observed_routers[values["node"]] = values

    assert summary_match is not None, output
    assert int(summary_match.group("delivered")) == len(expected.deliveries)

    expected_deliveries = [
        {
            "cycle": delivery.cycle,
            "source": delivery.flit.source,
            "dest": delivery.flit.destination,
            "tag": delivery.flit.tag,
            "fragment": delivery.flit.fragment,
            "vc": delivery.flit.vc,
            "last": 1 if delivery.flit.last else 0,
        }
        for delivery in expected.deliveries
    ]
    assert observed_deliveries == expected_deliveries

    assert len(observed_routers) == 16
    for node, summary in enumerate(expected.router_summaries):
        observed = observed_routers[node]
        assert observed["accepted"] == summary.accepted_flit_count
        assert observed["forwarded"] == summary.forwarded_flit_count
        assert observed["istall"] == summary.input_stall_cycles
        assert observed["ostall"] == summary.output_stall_cycles
        assert observed["contention"] == summary.arbitration_contention_cycles
        assert observed["maxocc"] == summary.max_input_occupancy
        assert observed["local"] == summary.route_flit_count[PORT_LOCAL]
        assert observed["east"] == summary.route_flit_count[PORT_EAST]
        assert observed["south"] == summary.route_flit_count[PORT_SOUTH]


def test_multiflow_mesh_preserves_conservation_order_and_fairness() -> None:
    flows = _multiflow_mesh_flows()
    ready = _multiflow_mesh_ready()
    scheduled = [scheduled for flow in flows for scheduled in packetize_traffic_flow(flow)]
    result = simulate_scheduled_flits(scheduled, endpoint_out_ready_schedule=ready, max_cycles=256)

    assert result.endpoint_injected_flit_count == len(scheduled)
    assert len(result.deliveries) == len(scheduled)

    by_label: dict[str, list[MeshDelivery]] = {}
    for delivery in result.deliveries:
        by_label.setdefault(delivery.flit.label, []).append(delivery)

    assert set(by_label) == {flow.name for flow in flows}
    for deliveries in by_label.values():
        assert [delivery.flit.fragment for delivery in deliveries] == list(range(8))

    first_sixteen_tags = {delivery.flit.tag for delivery in result.deliveries[:16]}
    assert len(first_sixteen_tags) >= 2
    assert any(summary.arbitration_contention_cycles > 0 for summary in result.router_summaries)


def test_mesh_router_traces_replay_each_router_cycle_exactly() -> None:
    flows = _multiflow_mesh_flows()
    ready = _multiflow_mesh_ready()
    scheduled = [scheduled for flow in flows for scheduled in packetize_traffic_flow(flow)]
    result = simulate_scheduled_flits(scheduled, endpoint_out_ready_schedule=ready, max_cycles=256)

    for node in (0, 5, 15):
        input_schedule, out_ready_schedule = extract_router_replay_schedules(result, node=node)
        x_coord, y_coord = coordinates(node)
        replay = simulate_router(
            x_coord=x_coord,
            y_coord=y_coord,
            input_schedule=input_schedule,
            out_ready_schedule=out_ready_schedule,
        )
        expected_traces = tuple(mesh_trace.router_traces[node] for mesh_trace in result.traces)

        assert replay.traces == expected_traces
        assert replay.accepted_flit_count == result.router_summaries[node].accepted_flit_count
        assert replay.forwarded_flit_count == result.router_summaries[node].forwarded_flit_count


def test_router_replay_restores_fast_forwarded_idle_cycles() -> None:
    flows = [
        TrafficFlow(name="early", source=0, destination=1, payload_bytes=32, vc=0, release_cycle=0),
        TrafficFlow(name="late", source=0, destination=1, payload_bytes=32, vc=0, release_cycle=1000),
    ]
    scheduled = [item for flow in flows for item in packetize_traffic_flow(flow)]
    result = simulate_scheduled_flits(scheduled, max_cycles=1100, fast_forward_idle=True)
    input_schedule, out_ready_schedule = extract_router_replay_schedules(result, node=0)
    replay = simulate_router(
        x_coord=0,
        y_coord=0,
        input_schedule=input_schedule,
        out_ready_schedule=out_ready_schedule,
    )

    assert len(result.traces) < result.cycles
    assert len(replay.traces) == result.cycles
    for mesh_trace in result.traces:
        assert replay.traces[mesh_trace.cycle] == mesh_trace.router_traces[0]


def test_mesh_idle_fast_forward_preserves_absolute_delivery_cycles() -> None:
    flows = [
        TrafficFlow(name="early", source=0, destination=1, payload_bytes=32, vc=0, release_cycle=0),
        TrafficFlow(name="late", source=0, destination=1, payload_bytes=32, vc=0, release_cycle=1000),
    ]
    scheduled = [item for flow in flows for item in packetize_traffic_flow(flow)]

    normal = simulate_scheduled_flits(scheduled, max_cycles=1100)
    accelerated = simulate_scheduled_flits(scheduled, max_cycles=1100, fast_forward_idle=True)

    assert accelerated.cycles == normal.cycles
    assert [delivery.cycle for delivery in accelerated.deliveries] == [
        delivery.cycle for delivery in normal.deliveries
    ]
    assert len(accelerated.traces) < len(normal.traces)
    assert accelerated.endpoint_injected_flit_count == normal.endpoint_injected_flit_count


def test_mesh_schedule_order_is_independent_of_wrapped_wire_tag() -> None:
    flows = [
        TrafficFlow(
            name="before_wrap",
            source=0,
            destination=1,
            payload_bytes=32,
            vc=0,
            release_cycle=0,
            tag_base=255,
            schedule_order=10,
        ),
        TrafficFlow(
            name="after_wrap",
            source=0,
            destination=1,
            payload_bytes=32,
            vc=0,
            release_cycle=0,
            tag_base=0,
            schedule_order=11,
        ),
    ]
    scheduled = [item for flow in flows for item in packetize_traffic_flow(flow)]

    result = simulate_scheduled_flits(scheduled, max_cycles=32)

    assert [delivery.flit.label for delivery in result.deliveries] == [
        "before_wrap",
        "after_wrap",
    ]
    assert [delivery.flit.tag for delivery in result.deliveries] == [255, 0]


def test_mesh_flow_and_packet_order_remain_distinct_across_tag_wrap() -> None:
    flows = [
        TrafficFlow(
            name="multi_packet",
            source=0,
            destination=1,
            payload_bytes=64,
            packet_payload_bytes=32,
            vc=0,
            release_cycle=0,
            tag_base=255,
            schedule_order=10,
        ),
        TrafficFlow(
            name="following_flow",
            source=0,
            destination=1,
            payload_bytes=32,
            packet_payload_bytes=32,
            vc=0,
            release_cycle=0,
            tag_base=1,
            schedule_order=11,
        ),
    ]
    scheduled = [item for flow in flows for item in packetize_traffic_flow(flow)]

    assert [(item.flit.tag, item.schedule_order, item.packet_order) for item in scheduled] == [
        (255, 10, 0),
        (0, 10, 1),
        (1, 11, 0),
    ]

    result = simulate_scheduled_flits(scheduled, max_cycles=32)

    assert [delivery.flit.label for delivery in result.deliveries] == [
        "multi_packet",
        "multi_packet",
        "following_flow",
    ]
    assert [delivery.flit.tag for delivery in result.deliveries] == [255, 0, 1]
