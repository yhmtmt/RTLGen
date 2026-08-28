from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from npu.eval import (
    generate_llm_decoder_attention_score32_noc_exact_router_rtl_activity as activity,
)
from npu.sim.perf.noc_segmented_mesh import verify_router_replay
from npu.sim.perf.noc_sram_packet_mesh import PacketDescriptor, simulate_packet_mesh
from npu.sim.perf.attention_shared_stream_context_service import (
    ServiceContext,
    simulate_context_service,
)


def test_packet_mesh_router_view_preserves_replay_signals() -> None:
    packet_mesh = simulate_packet_mesh(
        (
            PacketDescriptor(
                source=0,
                destination=5,
                vc=1,
                tag=3,
                flit_count=2,
                tx_base_addr=0,
                rx_base_addr=0,
                release_cycle=0,
            ),
        ),
        record_mesh_trace=True,
    )
    view = activity._router_view(packet_mesh)
    verification = verify_router_replay(view, node=0)

    assert view.cycles == packet_mesh.cycles
    assert view.traces == packet_mesh.mesh_traces
    assert verification.forwarded_flit_count > 0


def test_shared_context_service_trace_capture_is_opt_in() -> None:
    kwargs = {
        "event_candidate_cycles": (0,),
        "source_sram_request_ready": lambda _cycle, _endpoint: True,
        "destination_sram_write_ready": lambda _cycle, _endpoint: True,
        "context_completion_ready": lambda _cycle: True,
    }
    context = ServiceContext(
        wave=0,
        source=0,
        destination=1,
        source_base=0,
        destination_base=0,
        packet_count=1,
    )
    compact = simulate_context_service((context,), **kwargs)
    traced = simulate_context_service((context,), record_mesh_trace=True, **kwargs)

    assert compact.packet_mesh.mesh_traces == ()
    assert traced.packet_mesh.mesh_traces
    assert traced.cycles == compact.cycles
    assert traced.write_fold == compact.write_fold


def test_manifest_keeps_exact_vc0_and_all_vc1_groups(tmp_path: Path, monkeypatch) -> None:
    phases = (
        activity.ExactRouterPhase(
            name="shared_vc0_full_context_service",
            transport_class="shared_sram_context_vc0",
            mesh_result=SimpleNamespace(cycles=7783),
            packet_count=7616,
            flit_count=60928,
            context_count=112,
        ),
        *(
            activity.ExactRouterPhase(
                name=f"reduction_vc1_group_{group}",
                transport_class="stats_once_exact_reduction_vc1",
                mesh_result=SimpleNamespace(cycles=2600 + group),
                packet_count=315,
                flit_count=2505,
                context_count=15,
                group=group,
            )
            for group in range(4)
        ),
    )
    monkeypatch.setattr(activity, "build_exact_phase_models", lambda: phases)
    monkeypatch.setattr(
        activity,
        "_source_hashes",
        lambda _repo_root: {"source": "a" * 64},
    )

    def fake_rtl(_mesh, *, node, clock_period_ns, out_dir, timeout_seconds):
        assert node == 5
        assert clock_period_ns == 1.8
        assert timeout_seconds == 900
        return {
            "vcd": "router_node5_activity.vcd",
            "vcd_sha256": "b" * 64,
            "sequential_register_activity": "router_node5_sequential.json",
            "sequential_register_activity_sha256": "c" * 64,
            "equivalence_status": "pass",
        }

    monkeypatch.setattr(activity, "run_rtl_activity", fake_rtl)
    payload = activity.build_manifest(
        repo_root=tmp_path,
        node=5,
        out_dir=tmp_path / "activity",
        timeout_seconds=900,
        clock_period_ns=1.8,
    )

    assert payload["version"] == 2
    assert payload["equivalence"]["status"] == "pass"
    assert len(payload["phases"]) == 5
    assert [row["group"] for row in payload["phases"]] == [None, 0, 1, 2, 3]
    assert payload["source_contract"]["partial_link_bits_per_beat"] == 419
    assert payload["source_contract"]["shared_flits"] == 60928
    assert payload["source_contract"]["reduction_flits"] == 10020
    assert payload["source_contract"]["total_flits"] == 70948
    assert all(row["rtl_equivalence"]["equivalence_status"] == "pass" for row in payload["phases"])
    assert payload["phases"][0]["vcd"].startswith("shared_vc0_full_context_service/")


def test_manifest_rejects_failed_phase_equivalence(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        activity,
        "build_exact_phase_models",
        lambda: (
            activity.ExactRouterPhase(
                name="shared_vc0_full_context_service",
                transport_class="shared_sram_context_vc0",
                mesh_result=SimpleNamespace(cycles=1),
                packet_count=1,
                flit_count=1,
                context_count=1,
            ),
        ),
    )
    monkeypatch.setattr(
        activity,
        "run_rtl_activity",
        lambda *_args, **_kwargs: {"equivalence_status": "fail"},
    )
    monkeypatch.setattr(activity, "_source_hashes", lambda _repo_root: {})

    try:
        activity.build_manifest(
            repo_root=tmp_path,
            node=5,
            out_dir=tmp_path / "activity",
            timeout_seconds=10,
            clock_period_ns=1.8,
        )
    except ValueError as exc:
        assert "did not pass" in str(exc)
    else:
        raise AssertionError("failed RTL phase equivalence was accepted")
