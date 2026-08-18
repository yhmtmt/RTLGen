from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from npu.eval.verify_llm_decoder_attention_score32_noc_phase2_endpoint_rtl import (
    WorkloadPacket,
    run_performance_replay,
    run_rtl_replay,
    write_workload_memories,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


def _packets() -> list[WorkloadPacket]:
    return [
        WorkloadPacket(
            packet_id=0,
            schedule_order=0,
            release_cycle=4,
            source=0,
            destination=15,
            vc=1,
            tag=255,
            flit_count=8,
            label="packet0",
        ),
        WorkloadPacket(
            packet_id=1,
            schedule_order=1,
            release_cycle=4,
            source=3,
            destination=12,
            vc=2,
            tag=0,
            flit_count=3,
            label="packet1",
        ),
    ]


def _contention_packets() -> list[WorkloadPacket]:
    return [
        WorkloadPacket(
            packet_id=source,
            schedule_order=source,
            release_cycle=4,
            source=source,
            destination=15,
            vc=source % 4,
            tag=source,
            flit_count=8,
            label=f"packet{source}",
        )
        for source in range(8)
    ]


def test_workload_memories_encode_endpoint_queues_and_concrete_tags(
    tmp_path: Path,
) -> None:
    paths = write_workload_memories(_packets(), tmp_path)

    descriptor_words = [int(line, 16) for line in paths.descriptors.read_text().splitlines()]
    assert [(word >> 42) & 0xFF for word in descriptor_words] == [255, 0]
    assert [(word >> 50) & 0xF for word in descriptor_words] == [8, 3]
    assert [int(line, 16) for line in paths.command_order.read_text().splitlines()] == [
        0,
        1,
    ]

    source_meta = [int(line, 16) for line in paths.source_meta.read_text().splitlines()]
    destination_meta = [
        int(line, 16) for line in paths.destination_meta.read_text().splitlines()
    ]
    assert source_meta[0] >> 16 == 1
    assert source_meta[3] >> 16 == 1
    assert destination_meta[12] >> 16 == 1
    assert destination_meta[15] >> 16 == 1


@pytest.mark.skipif(
    not (shutil.which("iverilog") or Path("/oss-cad-suite/bin/iverilog").exists())
    or not (shutil.which("vvp") or Path("/oss-cad-suite/bin/vvp").exists()),
    reason="iverilog/vvp unavailable",
)
def test_composed_rtl_replays_paired_descriptors_and_all_flits(tmp_path: Path) -> None:
    packets = _contention_packets()
    performance = run_performance_replay(packets, max_cycles=10000)
    result = run_rtl_replay(
        repo_root=REPO_ROOT,
        packets=packets,
        work_dir=tmp_path,
        timeout_cycles=10000,
        wall_timeout_seconds=60,
    )

    assert result["counters"]["packets"] == 8
    assert result["counters"]["flits"] == 64
    assert result["counters"]["contention"] > 0
    assert result["counters"]["input_stalls"] > 0
    assert result["counters"] == {
        key: performance[key]
        for key in ("packets", "flits", "cycles", "contention", "input_stalls", "max_occupancy")
    }
    assert "PASS workload" in result["simulation_stdout"]


@pytest.mark.skipif(
    not (shutil.which("iverilog") or Path("/oss-cad-suite/bin/iverilog").exists())
    or not (shutil.which("vvp") or Path("/oss-cad-suite/bin/vvp").exists()),
    reason="iverilog/vvp unavailable",
)
def test_serial_scheduler_rtl_matches_performance_replay(tmp_path: Path) -> None:
    packets = _contention_packets()
    performance = run_performance_replay(
        packets,
        max_cycles=10000,
        descriptor_scheduler="serial_paired",
    )
    result = run_rtl_replay(
        repo_root=REPO_ROOT,
        packets=packets,
        work_dir=tmp_path,
        timeout_cycles=10000,
        wall_timeout_seconds=60,
        descriptor_scheduler="serial_paired",
    )

    assert result["counters"] == {
        key: performance[key]
        for key in (
            "packets",
            "flits",
            "cycles",
            "contention",
            "input_stalls",
            "max_occupancy",
        )
    }
    assert result["counters"]["cycles"] == 88
