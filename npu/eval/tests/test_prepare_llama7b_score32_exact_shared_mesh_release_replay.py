from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from npu.eval.prepare_llama7b_score32_exact_shared_mesh_release_replay import (
    StallDilatedReleasePlayer,
    build_replay,
    main,
)
from tests.test_attention_score32_exact_dual_producer_shared_mesh4x4_full import (
    _assert_release_trace_matches_model,
)


def _cluster(cluster: int, producers: int, offset: int) -> dict:
    groups = []
    for group in range(4):
        first = offset + group * 300
        cycles = [first + row * 2 for row in range(128)]
        groups.append(
            {
                "logical_group": group,
                "first_output_cycle": cycles[0],
                "last_output_cycle": cycles[-1],
                "output_span_cycles": cycles[-1] - cycles[0] + 1,
                "output_rows": 128,
                "output_cycles": cycles,
            }
        )
    return {
        "cluster": cluster,
        "producer_count": producers,
        "passed": True,
        "exact_row_audit": {
            "passed": True,
            "expected_row_count": 512,
            "observed_row_count": 512,
        },
        "summary": {
            "wave_command_accept_count": 32,
            "completed_command_count": 4,
            "emitted_beat_count": 512,
            "errors": 0,
        },
        "groups": groups,
    }


def _cadence() -> dict:
    return {
        "model": "llama7b_score32_exact_cluster_release_cadence_v1",
        "passed": True,
        "clock_domain": "generated_cluster_single_clock",
        "logical_head_groups": 4,
        "representative_clusters": [_cluster(0, 54, 100), _cluster(8, 53, 120)],
    }


def test_build_replay_preserves_all_rows_and_rejects_hidden_clock_conversion() -> None:
    replay = build_replay(_cadence())

    assert replay["rows_per_source"] == 512
    assert replay["p54_release_cycles"][:2] == [100, 102]
    assert replay["p53_release_cycles"][:2] == [120, 122]
    assert replay["conservative_family_release_cycles"][-1] == 1274
    assert replay["clock_contract"]["conversion"] == "identity"
    assert replay["backpressure_contract"]["hidden_queue_depth"] == 0
    assert replay["mapping"]["p54_endpoints"] == list(range(8))
    assert replay["mapping"]["p53_root_local_endpoint"] == 15


def test_stall_dilated_player_shifts_every_later_release() -> None:
    player = StallDilatedReleasePlayer((10, 12, 15))

    assert not player.step(cycle=9, group_active=True, ready=True)
    assert not player.step(cycle=10, group_active=True, ready=False)
    assert player.step(cycle=14, group_active=True, ready=True)
    assert player.next_release_cycle == 16
    assert not player.step(cycle=15, group_active=True, ready=True)
    assert player.step(cycle=16, group_active=True, ready=True)
    assert player.next_release_cycle == 19
    assert player.step(cycle=19, group_active=True, ready=True)


def test_replay_rejects_incomplete_or_nonmonotonic_cycles() -> None:
    cadence = _cadence()
    cadence["representative_clusters"][0]["groups"][1]["output_cycles"][0] = 1
    cadence["representative_clusters"][0]["groups"][1]["first_output_cycle"] = 1

    with pytest.raises(ValueError, match="span differs|across groups"):
        build_replay(cadence)


def test_cli_writes_exact_cycle_sidecars(tmp_path: Path) -> None:
    cadence_path = tmp_path / "cadence.json"
    cadence_path.write_text(json.dumps(_cadence()), encoding="utf-8")
    out = tmp_path / "replay.json"
    p54 = tmp_path / "p54.memh"
    p53 = tmp_path / "p53.memh"

    assert main(
        [
            "--cadence",
            str(cadence_path),
            "--out",
            str(out),
            "--p54-memh",
            str(p54),
            "--p53-memh",
            str(p53),
        ]
    ) == 0
    assert len(p54.read_text().splitlines()) == 512
    assert p54.read_text().splitlines()[0] == "00000064"
    assert p53.read_text().splitlines()[0] == "00000078"
    assert json.loads(out.read_text())["source_ref"]["sha256"]


def test_replay_input_is_not_mutated() -> None:
    cadence = _cadence()
    original = copy.deepcopy(cadence)
    build_replay(cadence)
    assert cadence == original


def test_release_trace_checker_covers_all_sixteen_sources(tmp_path: Path) -> None:
    replay = build_replay(_cadence())
    p54 = tuple(replay["p54_release_cycles"])
    p53 = tuple(replay["p53_release_cycles"])
    sources = [
        StallDilatedReleasePlayer(p54 if endpoint < 8 else p53)
        for endpoint in range(15)
    ]
    root = StallDilatedReleasePlayer(p53)
    active_group = None
    activate_next = None
    next_group = 0
    lines = []
    for cycle in range(2000):
        if activate_next is not None:
            active_group = activate_next
            activate_next = None
        group_active = active_group is not None
        limit = None if active_group is None else (active_group + 1) * 128
        admission = 0
        group = next_group if next_group < 4 else 3
        if (
            active_group is None
            and next_group < 4
            and all(int(source.next_release_cycle) <= cycle for source in sources)
            and int(root.next_release_cycle) <= cycle
        ):
            admission = 1
            group = next_group
            activate_next = next_group
            next_group += 1
        source_valid = sum(
            int(source.valid(cycle=cycle, group_active=group_active, index_limit=limit))
            << endpoint
            for endpoint, source in enumerate(sources)
        )
        root_valid = int(
            root.valid(cycle=cycle, group_active=group_active, index_limit=limit)
        )
        lines.append(
            f"REL {cycle} {admission} {group} "
            f"{'7fff' if admission else '0000'} {admission} "
            f"{source_valid:04x} 7fff {root_valid} 1"
        )
        for source in sources:
            source.step(
                cycle=cycle,
                group_active=group_active,
                ready=True,
                index_limit=limit,
            )
        root.step(
            cycle=cycle,
            group_active=group_active,
            ready=True,
            index_limit=limit,
        )
        if active_group is not None:
            end = (active_group + 1) * 128
            if all(source.index == end for source in sources) and root.index == end:
                active_group = None
        if next_group == 4 and all(source.index == 512 for source in sources):
            break

    trace = tmp_path / "release.trace"
    trace.write_text("\n".join(lines) + "\n", encoding="ascii")
    assert _assert_release_trace_matches_model(trace, replay) == 8192
