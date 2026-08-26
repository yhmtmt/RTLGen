from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from npu.eval.generate_llm_decoder_attention_score32_noc_router_rtl_activity import (
    run_rtl_activity,
)
from npu.sim.perf.noc_segmented_mesh import (
    TrafficFlow,
    packetize_traffic_flow,
    simulate_scheduled_flits,
)


def _tool(name: str) -> bool:
    return bool(shutil.which(name) or (Path("/oss-cad-suite/bin") / name).is_file())


@pytest.mark.skipif(not _tool("iverilog") or not _tool("vvp"), reason="iverilog/vvp unavailable")
def test_router_rtl_activity_matches_streamed_perf_replay(tmp_path: Path) -> None:
    flows = (
        TrafficFlow(name="a", source=1, destination=0, payload_bytes=64, vc=0),
        TrafficFlow(name="b", source=4, destination=0, payload_bytes=64, vc=1),
    )
    scheduled = [item for flow in flows for item in packetize_traffic_flow(flow)]
    ready = [[True] * 16 for _ in range(64)]
    for cycle in range(5, 9):
        ready[cycle][0] = False
    mesh = simulate_scheduled_flits(
        scheduled,
        endpoint_out_ready_schedule=ready,
        max_cycles=64,
        capture_router_replay_nodes=(0,),
    )

    result = run_rtl_activity(
        mesh,
        node=0,
        clock_period_ns=1.0,
        out_dir=tmp_path,
        timeout_seconds=30,
    )

    assert result["equivalence_status"] == "pass"
    assert result["forwarded_event_count"] == mesh.router_summaries[0].forwarded_flit_count
    assert (tmp_path / result["vcd"]).stat().st_size > 0
    assert (tmp_path / result["sequential_register_activity"]).stat().st_size > 0
