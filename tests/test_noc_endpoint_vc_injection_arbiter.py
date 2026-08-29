from __future__ import annotations

from collections import deque
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.sim.perf.noc_endpoint_vc_injection_arbiter import (
    EndpointVcArbiterCycle,
    EndpointVcInjectionArbiter,
)
from npu.sim.perf.noc_segmented_mesh import (
    ModelFlit,
    TrafficFlow,
    packetize_traffic_flow,
    simulate_scheduled_flits,
)

RTL = REPO_ROOT / "npu/sim/rtl/noc_endpoint_vc_injection_arbiter.sv"


def _flit(index: int, *, vc: int) -> ModelFlit:
    return ModelFlit(
        source=index & 0xF,
        destination=(15 - index) & 0xF,
        tag=(0x20 + index) & 0xFF,
        fragment=index & 0x7,
        last=(index & 0x7) == 7,
        vc=vc,
        data=(0xA5000000 | (vc << 12) | index) & 0xFFFFFFFF,
        label=f"vc{vc}_{index}",
    )


def _build_schedule() -> tuple[
    list[tuple[ModelFlit | None, ModelFlit | None, bool]],
    list[EndpointVcArbiterCycle],
]:
    vc0_queue = deque(_flit(index, vc=0) for index in range(12))
    vc1_queue = deque(_flit(index + 16, vc=1) for index in range(9))
    model = EndpointVcInjectionArbiter()
    schedule: list[tuple[ModelFlit | None, ModelFlit | None, bool]] = []
    expected: list[EndpointVcArbiterCycle] = []
    for cycle in range(64):
        vc0 = vc0_queue[0] if vc0_queue else None
        vc1 = vc1_queue[0] if vc1_queue else None
        out_ready = cycle % 7 not in (2, 3)
        row = model.step(vc0=vc0, vc1=vc1, out_ready=out_ready)
        schedule.append((vc0, vc1, out_ready))
        expected.append(row)
        if row.vc0_ready and vc0_queue:
            vc0_queue.popleft()
        if row.vc1_ready and vc1_queue:
            vc1_queue.popleft()
        if not vc0_queue and not vc1_queue:
            break

    malformed = _flit(30, vc=2)
    valid_vc1 = _flit(31, vc=1)
    expected.append(model.step(vc0=malformed, vc1=valid_vc1, out_ready=True))
    schedule.append((malformed, valid_vc1, True))
    expected.append(model.step(vc0=None, vc1=None, out_ready=True))
    schedule.append((None, None, True))
    return schedule, expected


def test_model_round_robin_holds_selection_through_stall() -> None:
    model = EndpointVcInjectionArbiter()
    vc0 = _flit(0, vc=0)
    vc1 = _flit(16, vc=1)

    stalled = model.step(vc0=vc0, vc1=vc1, out_ready=False)
    accepted0 = model.step(vc0=vc0, vc1=vc1, out_ready=True)
    accepted1 = model.step(vc0=vc0, vc1=vc1, out_ready=True)

    assert stalled.output == vc0
    assert not stalled.vc0_ready and not stalled.vc1_ready
    assert accepted0.output == vc0 and accepted0.vc0_ready
    assert accepted1.output == vc1 and accepted1.vc1_ready


def test_model_drops_wrong_vc_identity_and_sets_sticky_error() -> None:
    model = EndpointVcInjectionArbiter()
    malformed = _flit(0, vc=3)

    dropped = model.step(vc0=malformed, vc1=None, out_ready=False)
    after = model.step(vc0=None, vc1=None, out_ready=True)

    assert dropped.dropped_vc0 and dropped.vc0_ready
    assert dropped.output is None
    assert not dropped.protocol_error
    assert after.protocol_error


def test_model_matches_shared_mesh_vc_round_robin_injection_trace() -> None:
    flows = [
        TrafficFlow(
            name=f"vc{vc}_{index}",
            source=0,
            destination=15,
            payload_bytes=4 * 32,
            packet_payload_bytes=32,
            vc=vc,
            release_cycle=index,
            schedule_order=index,
        )
        for index, vc in enumerate((0, 0, 1, 1))
    ]
    scheduled = [item for flow in flows for item in packetize_traffic_flow(flow)]
    mesh = simulate_scheduled_flits(
        scheduled,
        endpoint_injection_policy="vc_round_robin",
        max_cycles=256,
    )

    future = deque(sorted(scheduled, key=lambda item: item.release_cycle))
    queues = (deque(), deque())
    model = EndpointVcInjectionArbiter()
    for trace in mesh.traces:
        while future and future[0].release_cycle <= trace.cycle:
            item = future.popleft()
            queues[item.flit.vc].append(item.flit)
        row = model.step(
            vc0=queues[0][0] if queues[0] else None,
            vc1=queues[1][0] if queues[1] else None,
            out_ready=trace.endpoint_in_ready[0],
        )
        observed = [flit for source, flit in trace.injected if source == 0]
        expected = [row.output] if row.output_fire else []
        assert observed == expected
        if row.vc0_ready and queues[0]:
            queues[0].popleft()
        if row.vc1_ready and queues[1]:
            queues[1].popleft()

    assert not future and not queues[0] and not queues[1]


def _tool(name: str) -> str | None:
    resolved = shutil.which(name)
    bundled = Path("/oss-cad-suite/bin") / name
    return resolved or (str(bundled) if bundled.exists() else None)


def _drive(flit: ModelFlit | None, prefix: str) -> str:
    if flit is None:
        return textwrap.dedent(
            f"""\
            {prefix}_valid = 1'b0;
            {prefix}_destination = 4'b0;
            {prefix}_source = 4'b0;
            {prefix}_tag = 8'b0;
            {prefix}_fragment = 3'b0;
            {prefix}_last = 1'b0;
            {prefix}_vc = 2'b0;
            {prefix}_data = 32'b0;"""
        )
    return textwrap.dedent(
        f"""\
        {prefix}_valid = 1'b1;
        {prefix}_destination = 4'h{flit.destination:x};
        {prefix}_source = 4'h{flit.source:x};
        {prefix}_tag = 8'h{flit.tag:02x};
        {prefix}_fragment = 3'h{flit.fragment:x};
        {prefix}_last = 1'b{int(flit.last)};
        {prefix}_vc = 2'h{flit.vc:x};
        {prefix}_data = 32'h{flit.data:08x};"""
    )


def _testbench(
    schedule: list[tuple[ModelFlit | None, ModelFlit | None, bool]],
) -> str:
    cycles = []
    for cycle, (vc0, vc1, out_ready) in enumerate(schedule):
        cycles.append(
            textwrap.dedent(
                f"""\
                @(negedge clk);
                {_drive(vc0, 'vc0')}
                {_drive(vc1, 'vc1')}
                out_ready = 1'b{int(out_ready)};
                #1;
                $display("TRACE {cycle} %0d %0d %0d %0h %0h %0h %0h %0d %0h %0h %0d",
                  vc0_ready, vc1_ready, out_valid, out_destination, out_source,
                  out_tag, out_fragment, out_last, out_vc, out_data,
                  protocol_error);
                @(posedge clk);"""
            )
        )
    cycle_body = "\n".join(cycles)
    return textwrap.dedent(
        f"""\
        `timescale 1ns/1ps
        module tb;
          reg clk = 1'b0;
          reg rst_n = 1'b0;
          always #5 clk = ~clk;

          reg vc0_valid;
          wire vc0_ready;
          reg [3:0] vc0_destination, vc0_source;
          reg [7:0] vc0_tag;
          reg [2:0] vc0_fragment;
          reg vc0_last;
          reg [1:0] vc0_vc;
          reg [31:0] vc0_data;
          reg vc1_valid;
          wire vc1_ready;
          reg [3:0] vc1_destination, vc1_source;
          reg [7:0] vc1_tag;
          reg [2:0] vc1_fragment;
          reg vc1_last;
          reg [1:0] vc1_vc;
          reg [31:0] vc1_data;
          wire out_valid;
          reg out_ready;
          wire [3:0] out_destination, out_source;
          wire [7:0] out_tag;
          wire [2:0] out_fragment;
          wire out_last;
          wire [1:0] out_vc;
          wire [31:0] out_data;
          wire protocol_error;

          noc_endpoint_vc_injection_arbiter #(.DATA_W(32)) dut (
            .clk(clk), .rst_n(rst_n),
            .vc0_valid(vc0_valid), .vc0_ready(vc0_ready),
            .vc0_destination(vc0_destination), .vc0_source(vc0_source),
            .vc0_tag(vc0_tag), .vc0_fragment(vc0_fragment),
            .vc0_last(vc0_last), .vc0_vc(vc0_vc), .vc0_data(vc0_data),
            .vc1_valid(vc1_valid), .vc1_ready(vc1_ready),
            .vc1_destination(vc1_destination), .vc1_source(vc1_source),
            .vc1_tag(vc1_tag), .vc1_fragment(vc1_fragment),
            .vc1_last(vc1_last), .vc1_vc(vc1_vc), .vc1_data(vc1_data),
            .out_valid(out_valid), .out_ready(out_ready),
            .out_destination(out_destination), .out_source(out_source),
            .out_tag(out_tag), .out_fragment(out_fragment),
            .out_last(out_last), .out_vc(out_vc), .out_data(out_data),
            .protocol_error(protocol_error)
          );

          initial begin
            vc0_valid = 0; vc1_valid = 0; out_ready = 0;
            vc0_destination = 0; vc0_source = 0; vc0_tag = 0;
            vc0_fragment = 0; vc0_last = 0; vc0_vc = 0; vc0_data = 0;
            vc1_destination = 0; vc1_source = 0; vc1_tag = 0;
            vc1_fragment = 0; vc1_last = 0; vc1_vc = 0; vc1_data = 0;
            repeat (2) @(posedge clk);
            @(negedge clk); rst_n = 1'b1;
            {cycle_body}
            $finish;
          end
        endmodule
        """
    )


def test_rtl_matches_cycle_model_under_stalls_and_simultaneous_sources(
    tmp_path: Path,
) -> None:
    iverilog = _tool("iverilog")
    vvp = _tool("vvp")
    if iverilog is None or vvp is None:
        pytest.skip("iverilog/vvp unavailable")
    schedule, expected = _build_schedule()
    tb = tmp_path / "tb.sv"
    simv = tmp_path / "tb.vvp"
    tb.write_text(_testbench(schedule), encoding="utf-8")
    subprocess.run(
        [iverilog, "-g2012", "-s", "tb", "-o", str(simv), str(RTL), str(tb)],
        check=True,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    run = subprocess.run(
        [vvp, str(simv)],
        check=True,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )
    observed = [line.split() for line in run.stdout.splitlines() if line.startswith("TRACE ")]
    assert len(observed) == len(expected)
    for fields, row in zip(observed, expected):
        output = row.output
        values = [int(value, 16) for value in fields[2:]]
        assert values == [
            int(row.vc0_ready),
            int(row.vc1_ready),
            int(output is not None),
            0 if output is None else output.destination,
            0 if output is None else output.source,
            0 if output is None else output.tag,
            0 if output is None else output.fragment,
            0 if output is None else int(output.last),
            0 if output is None else output.vc,
            0 if output is None else output.data,
            int(row.protocol_error),
        ]
