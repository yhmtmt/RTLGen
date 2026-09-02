#!/usr/bin/env python3
"""Prepare exact cluster cadence for causal shared-mesh RTL replay."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


JsonDict = dict[str, Any]
CADENCE_MODEL = "llama7b_score32_exact_cluster_release_cadence_v1"
REPLAY_MODEL = "llama7b_score32_exact_shared_mesh_release_replay_v1"
GROUPS = 4
ROWS_PER_GROUP = 128
ROWS_PER_SOURCE = GROUPS * ROWS_PER_GROUP
REPO_ROOT = Path(__file__).resolve().parents[2]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_source_ref(path: Path) -> JsonDict:
    resolved = path.resolve()
    try:
        display_path = resolved.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        display_path = str(resolved)
    return {"path": display_path, "sha256": _sha256(resolved)}


def _positive_int(value: Any, label: str) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{label} must be a positive integer")
    try:
        result = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be a positive integer") from exc
    if result <= 0 or result != value:
        raise ValueError(f"{label} must be a positive integer")
    return result


def _family_cycles(cluster: JsonDict, *, expected_cluster: int, producers: int) -> list[int]:
    if int(cluster.get("cluster", -1)) != expected_cluster:
        raise ValueError(f"expected representative cluster {expected_cluster}")
    if int(cluster.get("producer_count", -1)) != producers:
        raise ValueError(f"cluster {expected_cluster} must have {producers} producers")
    if cluster.get("passed") is not True:
        raise ValueError(f"cluster {expected_cluster} cadence did not pass")
    audit = cluster.get("exact_row_audit")
    if not isinstance(audit, dict) or audit.get("passed") is not True:
        raise ValueError(f"cluster {expected_cluster} exact-row audit did not pass")
    if (
        int(audit.get("expected_row_count", -1)) != ROWS_PER_SOURCE
        or int(audit.get("observed_row_count", -1)) != ROWS_PER_SOURCE
    ):
        raise ValueError(f"cluster {expected_cluster} exact-row audit is incomplete")
    summary = cluster.get("summary")
    if not isinstance(summary, dict) or any(
        int(summary.get(field, -1)) != expected
        for field, expected in {
            "wave_command_accept_count": 32,
            "completed_command_count": GROUPS,
            "emitted_beat_count": ROWS_PER_SOURCE,
            "errors": 0,
        }.items()
    ):
        raise ValueError(f"cluster {expected_cluster} count/error summary is invalid")
    groups = cluster.get("groups")
    if not isinstance(groups, list) or len(groups) != GROUPS:
        raise ValueError(f"cluster {expected_cluster} must contain {GROUPS} groups")

    cycles: list[int] = []
    for group_index, group in enumerate(groups):
        if not isinstance(group, dict) or int(group.get("logical_group", -1)) != group_index:
            raise ValueError(f"cluster {expected_cluster} group order is invalid")
        rows = group.get("output_cycles")
        if not isinstance(rows, list) or len(rows) != ROWS_PER_GROUP:
            raise ValueError(
                f"cluster {expected_cluster} group {group_index} must retain "
                f"{ROWS_PER_GROUP} output cycles"
            )
        parsed = [
            _positive_int(cycle, f"cluster {expected_cluster} group {group_index} cycle")
            for cycle in rows
        ]
        if any(right <= left for left, right in zip(parsed, parsed[1:])):
            raise ValueError(
                f"cluster {expected_cluster} group {group_index} cycles must increase"
            )
        if int(group.get("first_output_cycle", -1)) != parsed[0]:
            raise ValueError(f"cluster {expected_cluster} group {group_index} first cycle differs")
        if int(group.get("last_output_cycle", -1)) != parsed[-1]:
            raise ValueError(f"cluster {expected_cluster} group {group_index} last cycle differs")
        if int(group.get("output_rows", -1)) != ROWS_PER_GROUP:
            raise ValueError(f"cluster {expected_cluster} group {group_index} row count differs")
        if int(group.get("output_span_cycles", -1)) != parsed[-1] - parsed[0] + 1:
            raise ValueError(f"cluster {expected_cluster} group {group_index} span differs")
        cycles.extend(parsed)
    if any(right <= left for left, right in zip(cycles, cycles[1:])):
        raise ValueError(f"cluster {expected_cluster} cycles must increase across groups")
    return cycles


def build_replay(cadence: JsonDict, *, cadence_path: Path | None = None) -> JsonDict:
    """Validate the measured artifact and build the common-clock replay contract."""

    if cadence.get("model") != CADENCE_MODEL or cadence.get("passed") is not True:
        raise ValueError("input is not a passing exact cluster cadence artifact")
    if cadence.get("clock_domain") != "generated_cluster_single_clock":
        raise ValueError("unexpected cadence clock domain")
    if int(cadence.get("logical_head_groups", -1)) != GROUPS:
        raise ValueError("cadence must contain four logical head groups")
    representatives = cadence.get("representative_clusters")
    if not isinstance(representatives, list) or len(representatives) != 2:
        raise ValueError("cadence must contain exactly the p54 and p53 representatives")

    by_cluster = {
        int(cluster.get("cluster", -1)): cluster
        for cluster in representatives
        if isinstance(cluster, dict)
    }
    if set(by_cluster) != {0, 8}:
        raise ValueError("representative clusters must be exactly 0 and 8")
    p54 = _family_cycles(by_cluster[0], expected_cluster=0, producers=54)
    p53 = _family_cycles(by_cluster[8], expected_cluster=8, producers=53)

    source_identity = None
    if cadence_path is not None:
        source_identity = make_source_ref(cadence_path)
    return {
        "version": 1,
        "model": REPLAY_MODEL,
        "decision": "exact_cluster_release_cadence_ready_for_causal_shared_mesh_replay",
        "source_ref": source_identity,
        "clock_contract": {
            "mode": "common_synchronous_clock",
            "conversion": "identity",
            "reason": (
                "The composed RTL uses one clk for the cluster-facing reducer and shared mesh. "
                "Independent physical clocks require an embodied CDC and are rejected by this replay."
            ),
        },
        "backpressure_contract": {
            "mode": "single_held_beat_stall_dilated",
            "release_rule": (
                "After row i is accepted at cycle A, row i+1 becomes valid no earlier than "
                "A + (measured[i+1] - measured[i])."
            ),
            "hidden_queue_depth": 0,
            "held_output_beats_per_source": 1,
        },
        "mapping": {
            "p54_endpoints": list(range(8)),
            "p53_remote_endpoints": list(range(8, 15)),
            "p53_root_local_endpoint": 15,
        },
        "groups": GROUPS,
        "rows_per_group": ROWS_PER_GROUP,
        "rows_per_source": ROWS_PER_SOURCE,
        "p54_release_cycles": p54,
        "p53_release_cycles": p53,
        "conservative_family_release_cycles": [max(a, b) for a, b in zip(p54, p53)],
        "remaining_abstractions": [
            "The p54 trace is replicated over endpoints 0-7 and the p53 trace over endpoints 8-15.",
            "The no-stall measured inter-row deltas are conservatively dilated by downstream stalls; a directly composed producer/reducer/mesh replay is still stronger evidence.",
            "VC0 SRAM writes are not yet wired as the cluster fill plane, so this contract times VC1 but does not prove VC0-to-compute data dependence.",
            "HBM/DRAM service remains outside the chip RTL boundary.",
        ],
    }


@dataclass
class StallDilatedReleasePlayer:
    """One-beat ready/valid source matching the release-replay TB contract."""

    release_cycles: tuple[int, ...]
    index: int = 0
    next_release_cycle: int | None = None

    def __post_init__(self) -> None:
        if not self.release_cycles:
            raise ValueError("release cycle list must not be empty")
        if any(cycle <= 0 for cycle in self.release_cycles):
            raise ValueError("release cycles must be positive")
        if any(b <= a for a, b in zip(self.release_cycles, self.release_cycles[1:])):
            raise ValueError("release cycles must strictly increase")
        if self.next_release_cycle is None:
            self.next_release_cycle = self.release_cycles[0]

    def valid(
        self,
        *,
        cycle: int,
        group_active: bool,
        index_limit: int | None = None,
    ) -> bool:
        return (
            group_active
            and self.index < len(self.release_cycles)
            and (index_limit is None or self.index < index_limit)
            and cycle >= int(self.next_release_cycle)
        )

    def step(
        self,
        *,
        cycle: int,
        group_active: bool,
        ready: bool,
        index_limit: int | None = None,
    ) -> bool:
        fire = self.valid(
            cycle=cycle,
            group_active=group_active,
            index_limit=index_limit,
        ) and ready
        if fire:
            previous = self.release_cycles[self.index]
            self.index += 1
            if self.index < len(self.release_cycles):
                delta = self.release_cycles[self.index] - previous
                self.next_release_cycle = cycle + delta
        return fire


def _write_memh(path: Path, cycles: list[int]) -> None:
    path.write_text("".join(f"{cycle:08x}\n" for cycle in cycles), encoding="ascii")


def render_markdown(replay: JsonDict) -> str:
    p54 = replay["p54_release_cycles"]
    p53 = replay["p53_release_cycles"]
    return "\n".join(
        [
            "# Exact Shared-Mesh Producer Release Replay",
            "",
            f"- clock contract: `{replay['clock_contract']['mode']}`",
            f"- backpressure contract: `{replay['backpressure_contract']['mode']}`",
            f"- rows per source: `{replay['rows_per_source']}`",
            f"- p54 release interval: `{p54[0]}..{p54[-1]}` cycles",
            f"- p53 release interval: `{p53[0]}..{p53[-1]}` cycles",
            "",
            "## Remaining Abstractions",
            "",
            *[f"- {item}" for item in replay["remaining_abstractions"]],
            "",
        ]
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cadence", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--out-md", type=Path)
    parser.add_argument("--p54-memh", type=Path, required=True)
    parser.add_argument("--p53-memh", type=Path, required=True)
    args = parser.parse_args(argv)

    cadence = json.loads(args.cadence.read_text(encoding="utf-8"))
    replay = build_replay(cadence, cadence_path=args.cadence)
    for path in (args.out, args.p54_memh, args.p53_memh):
        path.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(replay, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _write_memh(args.p54_memh, replay["p54_release_cycles"])
    _write_memh(args.p53_memh, replay["p53_release_cycles"])
    if args.out_md is not None:
        args.out_md.parent.mkdir(parents=True, exist_ok=True)
        args.out_md.write_text(render_markdown(replay), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
