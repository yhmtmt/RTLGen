from __future__ import annotations

import shutil
from pathlib import Path
from types import SimpleNamespace

import pytest

from npu.eval import generate_llm_decoder_attention_score32_noc_router_rtl_activity as rtl_activity
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

    result = rtl_activity.run_rtl_activity(
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


def test_build_manifest_retimestamps_cycle_sequence_without_changing_replay(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    schedule_path = tmp_path / "schedule.json"
    schedule_path.write_text("{}", encoding="utf-8")
    mesh = SimpleNamespace(cycles=123)
    monkeypatch.setattr(
        rtl_activity,
        "reproduce_schedule_mesh",
        lambda **kwargs: ({"source_contract": {"noc_clock_ns": 1.0}}, {}, mesh),
    )
    observed: dict[str, float] = {}

    def fake_activity_manifest(*args, **kwargs):
        observed["manifest_clock"] = kwargs["clock_period_ns"]
        return {"clock_period_ns": kwargs["clock_period_ns"]}

    def fake_rtl(*args, **kwargs):
        observed["rtl_clock"] = kwargs["clock_period_ns"]
        return {
            "vcd": "router.vcd",
            "vcd_sha256": "a" * 64,
            "sequential_register_activity": "sequential.json",
            "sequential_register_activity_sha256": "b" * 64,
            "equivalence_status": "pass",
        }

    monkeypatch.setattr(rtl_activity, "build_router_activity_manifest", fake_activity_manifest)
    monkeypatch.setattr(rtl_activity, "run_rtl_activity", fake_rtl)
    monkeypatch.setattr(rtl_activity, "_sha256_file", lambda path: "c" * 64)

    payload = rtl_activity.build_manifest(
        repo_root=tmp_path,
        schedule_json=schedule_path,
        node=5,
        out_dir=tmp_path / "activity",
        timeout_seconds=30,
        clock_period_ns=1.8,
    )

    assert observed == {"manifest_clock": 1.8, "rtl_clock": 1.8}
    assert payload["clock_contract"] == {
        "source_schedule_clock_ns": 1.0,
        "activity_annotation_clock_ns": 1.8,
        "cycle_sequence_retimed": True,
        "retiming_scope": "timestamps only; replay inputs, ready values, flits, and counters unchanged",
    }
    assert payload["phases"][0]["measured_cycles"] == 123
