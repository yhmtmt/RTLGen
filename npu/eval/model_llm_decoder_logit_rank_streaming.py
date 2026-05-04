#!/usr/bin/env python3
"""Model decoder logit-rank streaming hierarchy throughput and latency."""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path
from typing import Any


JsonDict = dict[str, Any]

DEFAULT_RANK_PPA = Path(
    "control_plane/shadow_exports/l1_promotions/l1_decoder_logit_rank_datapath_v1_r2.json"
)
DEFAULT_SCALE_PPA = Path(
    "control_plane/shadow_exports/l1_promotions/l1_decoder_logit_rank_scale_v1.json"
)


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _ceil_div(numerator: int, denominator: int) -> int:
    if denominator <= 0:
        raise ValueError("denominator must be positive")
    return (numerator + denominator - 1) // denominator


def _parse_csv_point(path: str) -> JsonDict:
    match = re.search(r"logit_rank_r(?P<lanes>\d+)_l(?P<bits>\d+)_k(?P<topk>\d+)", path)
    if not match:
        return {"lanes": None, "logit_bits": None, "top_k": None}
    return {
        "lanes": int(match.group("lanes")),
        "logit_bits": int(match.group("bits")),
        "top_k": int(match.group("topk")),
    }


def _load_json(path: Path) -> JsonDict:
    with path.open("r", encoding="utf-8") as f:
        payload = json.load(f)
    if not isinstance(payload, dict):
        raise SystemExit(f"expected JSON object: {path}")
    return payload


def load_ranker_points(path: Path | None) -> list[JsonDict]:
    if path is None or not path.exists():
        return []
    payload = _load_json(path)
    rows: list[JsonDict] = []
    for proposal in payload.get("proposals") or []:
        if not isinstance(proposal, dict):
            continue
        ref = proposal.get("metrics_ref")
        metrics = proposal.get("metric_summary")
        if not isinstance(ref, dict) or not isinstance(metrics, dict):
            continue
        if str(ref.get("status") or "") != "ok":
            continue
        metrics_csv = str(ref.get("metrics_csv") or "")
        point = _parse_csv_point(metrics_csv)
        rows.append(
            {
                "source": str(path),
                "artifact_item_id": payload.get("item_id"),
                "metrics_csv": metrics_csv,
                "lanes": point["lanes"],
                "logit_bits": point["logit_bits"],
                "top_k": point["top_k"],
                "metrics": {
                    "critical_path_ns": _as_float(metrics.get("critical_path_ns")),
                    "die_area": _as_float(metrics.get("die_area")),
                    "total_power_mw": _as_float(metrics.get("total_power_mw")),
                },
            }
        )
    rows.sort(
        key=lambda row: (
            _as_int(row.get("lanes"), 10**9),
            _as_int(row.get("top_k"), 10**9),
            row["metrics"]["critical_path_ns"],
        )
    )
    return rows


def load_ranker_points_from_paths(paths: list[Path | None]) -> list[JsonDict]:
    points: list[JsonDict] = []
    seen: set[tuple[str | None, int, int]] = set()
    for path in paths:
        for point in load_ranker_points(path):
            key = (
                point.get("metrics_csv"),
                _as_int(point.get("lanes")),
                _as_int(point.get("top_k")),
            )
            if key in seen:
                continue
            seen.add(key)
            points.append(point)
    points.sort(
        key=lambda row: (
            _as_int(row.get("lanes"), 10**9),
            _as_int(row.get("top_k"), 10**9),
            row["metrics"]["critical_path_ns"],
        )
    )
    return points


def _fallback_ranker_point(*, lanes: int, top_k: int, critical_path_ns: float) -> JsonDict:
    return {
        "source": "cli_default",
        "metrics_csv": None,
        "lanes": lanes,
        "logit_bits": 16,
        "top_k": top_k,
        "metrics": {
            "critical_path_ns": critical_path_ns,
            "die_area": None,
            "total_power_mw": None,
        },
    }


def _select_ranker_point(
    points: list[JsonDict], *, lanes: int, top_k: int, default_critical_path_ns: float
) -> JsonDict:
    exact = [
        row
        for row in points
        if _as_int(row.get("lanes")) == lanes and _as_int(row.get("top_k")) == top_k
    ]
    if exact:
        return exact[0]
    same_k = [row for row in points if _as_int(row.get("top_k")) == top_k and _as_int(row.get("lanes")) > 0]
    if same_k:
        nearest = min(same_k, key=lambda row: abs(_as_int(row.get("lanes")) - lanes))
        scale = math.log2(max(2, lanes)) / math.log2(max(2, _as_int(nearest.get("lanes"), lanes)))
        clone = json.loads(json.dumps(nearest))
        clone["source"] = f"{nearest['source']}#scaled_nearest_lane"
        clone["lanes"] = lanes
        clone["metrics"]["critical_path_ns"] = round(nearest["metrics"]["critical_path_ns"] * scale, 6)
        clone["model_note"] = (
            f"critical_path_ns scaled from measured r{nearest['lanes']} k{nearest['top_k']} "
            f"by log2(lanes) ratio"
        )
        return clone
    return _fallback_ranker_point(
        lanes=lanes, top_k=top_k, critical_path_ns=default_critical_path_ns
    )


def simulate_streaming_hierarchy(
    *,
    vocab_size: int,
    producer_lanes: int,
    producer_latency_cycles: int,
    producer_ii_cycles: int,
    local_ranker_latency_cycles: int,
    local_ranker_ii_cycles: int,
    local_top_k: int,
    global_merge_latency_cycles: int,
    global_merge_ii_cycles: int,
    candidate_fifo_depth_groups: int,
) -> JsonDict:
    tile_count = _ceil_div(vocab_size, producer_lanes)
    local_done_times: list[int] = []
    local_available = 0
    for tile in range(tile_count):
        producer_ready = producer_latency_cycles + tile * producer_ii_cycles
        local_start = max(producer_ready, local_available)
        local_done_times.append(local_start + local_ranker_latency_cycles)
        local_available = local_start + local_ranker_ii_cycles

    merge_start_times: list[int] = []
    merge_done_times: list[int] = []
    merge_available = 0
    for local_done in local_done_times:
        merge_start = max(local_done, merge_available)
        merge_start_times.append(merge_start)
        merge_done_times.append(merge_start + global_merge_latency_cycles)
        merge_available = merge_start + global_merge_ii_cycles

    events: list[tuple[int, int]] = []
    for t in local_done_times:
        events.append((t, 1))
    for t in merge_start_times:
        events.append((t, -1))
    events.sort(key=lambda item: (item[0], -item[1]))
    occupancy = 0
    max_occupancy = 0
    for _, delta in events:
        occupancy += delta
        max_occupancy = max(max_occupancy, occupancy)

    total_candidates = tile_count * local_top_k
    total_cycles = max(merge_done_times) if merge_done_times else 0
    return {
        "tile_count": tile_count,
        "producer_lanes": producer_lanes,
        "local_top_k": local_top_k,
        "total_candidates_emitted": total_candidates,
        "total_cycles": total_cycles,
        "producer_last_tile_ready_cycle": producer_latency_cycles + max(0, tile_count - 1) * producer_ii_cycles,
        "local_last_done_cycle": max(local_done_times) if local_done_times else 0,
        "global_last_done_cycle": total_cycles,
        "required_fifo_depth_groups": max_occupancy,
        "candidate_fifo_depth_groups": candidate_fifo_depth_groups,
        "fifo_capacity_ok": max_occupancy <= candidate_fifo_depth_groups,
        "producer_ii_cycles": producer_ii_cycles,
        "local_ranker_latency_cycles": local_ranker_latency_cycles,
        "local_ranker_ii_cycles": local_ranker_ii_cycles,
        "global_merge_latency_cycles": global_merge_latency_cycles,
        "global_merge_ii_cycles": global_merge_ii_cycles,
    }


def _time_summary(*, cycles: int, clock_ns: float, vocab_size: int) -> JsonDict:
    latency_ns = cycles * clock_ns
    latency_us = latency_ns / 1000.0
    tokens_per_s = 1_000_000_000.0 / latency_ns if latency_ns > 0 else 0.0
    logits_per_s = vocab_size * tokens_per_s
    return {
        "clock_ns": round(clock_ns, 6),
        "latency_cycles": cycles,
        "latency_us_per_token": round(latency_us, 6),
        "tokens_per_s": round(tokens_per_s, 3),
        "logits_per_s": round(logits_per_s, 3),
    }


def _flat_point_report(
    *,
    point: JsonDict,
    vocab_size: int,
    ranker_latency_cycles: int,
    ranker_ii_cycles: int,
) -> JsonDict:
    lanes = _as_int(point.get("lanes"), 1) or 1
    tiles = _ceil_div(vocab_size, lanes)
    cycles = ranker_latency_cycles + max(0, tiles - 1) * ranker_ii_cycles
    metrics = point["metrics"]
    return {
        "architecture": "flat_measured_ranker_scan",
        "lanes": lanes,
        "top_k": point.get("top_k"),
        "tile_count": tiles,
        "ranker_latency_cycles": ranker_latency_cycles,
        "ranker_ii_cycles": ranker_ii_cycles,
        "total_cycles": cycles,
        "timing": _time_summary(
            cycles=cycles,
            clock_ns=_as_float(metrics.get("critical_path_ns"), 1.0),
            vocab_size=vocab_size,
        ),
        "metrics": metrics,
        "source": point.get("source"),
        "metrics_csv": point.get("metrics_csv"),
    }


def build_report(
    *,
    rank_ppa_path: Path | None = DEFAULT_RANK_PPA,
    scale_ppa_path: Path | None = DEFAULT_SCALE_PPA,
    prompt_stress_path: Path | None = None,
    logit_rank_bypass_path: Path | None = None,
    vocab_size: int = 50257,
    producer_lanes: int = 8,
    top_k: int = 4,
    producer_latency_cycles: int = 1,
    producer_ii_cycles: int = 1,
    local_ranker_latency_cycles: int = 4,
    local_ranker_ii_cycles: int = 1,
    global_merge_latency_cycles: int = 3,
    global_merge_ii_cycles_list: list[int] | None = None,
    candidate_fifo_depth_groups: int = 16,
    fallback_critical_path_ns: float = 3.6,
) -> JsonDict:
    if vocab_size <= 0:
        raise ValueError("vocab_size must be positive")
    if producer_lanes <= 0:
        raise ValueError("producer_lanes must be positive")
    if top_k <= 0:
        raise ValueError("top_k must be positive")
    merge_iis = global_merge_ii_cycles_list or [1, 2, 4]
    measured_points = load_ranker_points_from_paths([rank_ppa_path, scale_ppa_path])
    if not measured_points:
        measured_points = [
            _fallback_ranker_point(
                lanes=producer_lanes, top_k=1, critical_path_ns=fallback_critical_path_ns
            ),
            _fallback_ranker_point(
                lanes=producer_lanes, top_k=top_k, critical_path_ns=fallback_critical_path_ns
            ),
        ]

    flat = [
        _flat_point_report(
            point=point,
            vocab_size=vocab_size,
            ranker_latency_cycles=local_ranker_latency_cycles,
            ranker_ii_cycles=local_ranker_ii_cycles,
        )
        for point in measured_points
        if _as_int(point.get("lanes")) > 0
    ]

    local_point = _select_ranker_point(
        measured_points,
        lanes=producer_lanes,
        top_k=top_k,
        default_critical_path_ns=fallback_critical_path_ns,
    )
    global_point = _select_ranker_point(
        measured_points,
        lanes=max(producer_lanes, top_k),
        top_k=top_k,
        default_critical_path_ns=fallback_critical_path_ns,
    )
    local_clock = _as_float(local_point["metrics"].get("critical_path_ns"), fallback_critical_path_ns)
    global_clock = _as_float(global_point["metrics"].get("critical_path_ns"), fallback_critical_path_ns)
    hierarchy_clock_ns = max(local_clock, global_clock)
    alternatives: list[JsonDict] = []
    for merge_ii in merge_iis:
        sim = simulate_streaming_hierarchy(
            vocab_size=vocab_size,
            producer_lanes=producer_lanes,
            producer_latency_cycles=producer_latency_cycles,
            producer_ii_cycles=producer_ii_cycles,
            local_ranker_latency_cycles=local_ranker_latency_cycles,
            local_ranker_ii_cycles=local_ranker_ii_cycles,
            local_top_k=top_k,
            global_merge_latency_cycles=global_merge_latency_cycles,
            global_merge_ii_cycles=merge_ii,
            candidate_fifo_depth_groups=candidate_fifo_depth_groups,
        )
        alternatives.append(
            {
                "architecture": "hierarchical_streaming_local_rank_global_merge",
                "merge_variant": f"merge_ii_{merge_ii}",
                **sim,
                "timing": _time_summary(
                    cycles=sim["total_cycles"],
                    clock_ns=hierarchy_clock_ns,
                    vocab_size=vocab_size,
                ),
                "local_ranker_point": local_point,
                "global_merge_point": global_point,
            }
        )

    all_candidates = flat + alternatives
    best = min(
        all_candidates,
        key=lambda row: (
            not bool(row.get("fifo_capacity_ok", True)),
            row["timing"]["latency_us_per_token"],
            str(row["architecture"]),
        ),
    )
    baseline = min(flat, key=lambda row: row["timing"]["latency_us_per_token"]) if flat else None
    for row in alternatives:
        if baseline is None:
            row["speedup_vs_best_flat"] = None
        else:
            row["speedup_vs_best_flat"] = round(
                baseline["timing"]["latency_us_per_token"] / row["timing"]["latency_us_per_token"], 6
            )

    return {
        "version": 0.1,
        "model": "decoder_logit_rank_streaming_hierarchy_v1",
        "rank_ppa_path": str(rank_ppa_path) if rank_ppa_path is not None else None,
        "rank_ppa_paths": [
            str(path)
            for path in [rank_ppa_path, scale_ppa_path]
            if path is not None
        ],
        "inputs": {
            "rank_ppa_path": str(rank_ppa_path) if rank_ppa_path is not None else None,
            "scale_ppa_path": str(scale_ppa_path) if scale_ppa_path is not None else None,
            "prompt_stress_path": str(prompt_stress_path) if prompt_stress_path is not None else None,
            "logit_rank_bypass_path": str(logit_rank_bypass_path) if logit_rank_bypass_path is not None else None,
            "vocab_size": vocab_size,
            "producer_lanes": producer_lanes,
            "top_k": top_k,
            "producer_latency_cycles": producer_latency_cycles,
            "producer_ii_cycles": producer_ii_cycles,
            "local_ranker_latency_cycles": local_ranker_latency_cycles,
            "local_ranker_ii_cycles": local_ranker_ii_cycles,
            "global_merge_latency_cycles": global_merge_latency_cycles,
            "global_merge_ii_cycles_list": merge_iis,
            "candidate_fifo_depth_groups": candidate_fifo_depth_groups,
            "fallback_critical_path_ns": fallback_critical_path_ns,
        },
        "assumptions": [
            "Producer emits one W-lane logit tile after producer latency and then every producer II cycles.",
            "Local ranker accepts one producer tile per local ranker II and emits one candidate group after local ranker latency.",
            "Candidate FIFO depth is reported in local candidate groups; overflow is reported as capacity evidence, not hidden by backpressure.",
            "Global merge consumes one local candidate group per merge II and produces the final token rank after the last merge latency.",
            "Measured row-8 datapath and row-16/row-32 scale critical_path_ns values are used as ranker clock proxies.",
            "Missing lane points are explicit defaults or log2-lane scaled proxies.",
        ],
        "measured_ranker_points": measured_points,
        "flat_measured_ranker_points": flat,
        "hierarchical_streaming_alternatives": alternatives,
        "recommendation": {
            "architecture": best["architecture"],
            "merge_variant": best.get("merge_variant"),
            "latency_us_per_token": best["timing"]["latency_us_per_token"],
            "tokens_per_s": best["timing"]["tokens_per_s"],
            "fifo_capacity_ok": best.get("fifo_capacity_ok", True),
            "reason": (
                "Lowest modelled latency per token among FIFO-valid measured flat scans and "
                "hierarchical streaming alternatives."
            ),
        },
    }


def _write_markdown(path: Path, payload: JsonDict) -> None:
    rec = payload["recommendation"]
    lines = [
        "# Decoder Logit-Rank Streaming Hierarchy",
        "",
        f"- model: `{payload['model']}`",
        f"- rank_ppa_paths: `{', '.join(payload.get('rank_ppa_paths') or [])}`",
        f"- recommendation: `{rec['architecture']}`",
        f"- merge_variant: `{rec['merge_variant'] or ''}`",
        f"- latency_us_per_token: `{rec['latency_us_per_token']}`",
        f"- tokens_per_s: `{rec['tokens_per_s']}`",
        f"- fifo_capacity_ok: `{rec['fifo_capacity_ok']}`",
        f"- reason: {rec['reason']}",
        "",
        "## Inputs",
        "",
        "| input | value |",
        "|---|---:|",
    ]
    for key, value in payload["inputs"].items():
        lines.append(f"| `{key}` | `{value}` |")
    lines.extend(
        [
            "",
            "## Flat Measured Ranker Points",
            "",
            "| lanes | top_k | cycles | latency_us | tokens_per_s | critical_path_ns | source |",
            "|---:|---:|---:|---:|---:|---:|---|",
        ]
    )
    for row in payload["flat_measured_ranker_points"]:
        lines.append(
            "| {lanes} | {topk} | {cycles} | {latency} | {tps} | {cp} | `{source}` |".format(
                lanes=row["lanes"],
                topk=row["top_k"],
                cycles=row["total_cycles"],
                latency=row["timing"]["latency_us_per_token"],
                tps=row["timing"]["tokens_per_s"],
                cp=row["timing"]["clock_ns"],
                source=row.get("metrics_csv") or row.get("source") or "",
            )
        )
    lines.extend(
        [
            "",
            "## Hierarchical Streaming Alternatives",
            "",
            "| variant | W | top_k | cycles | latency_us | tokens_per_s | fifo required/capacity | fifo ok | speedup vs flat |",
            "|---|---:|---:|---:|---:|---:|---:|---|---:|",
        ]
    )
    for row in payload["hierarchical_streaming_alternatives"]:
        lines.append(
            "| `{variant}` | {lanes} | {topk} | {cycles} | {latency} | {tps} | {fifo}/{cap} | `{ok}` | {speedup} |".format(
                variant=row["merge_variant"],
                lanes=row["producer_lanes"],
                topk=row["local_top_k"],
                cycles=row["total_cycles"],
                latency=row["timing"]["latency_us_per_token"],
                tps=row["timing"]["tokens_per_s"],
                fifo=row["required_fifo_depth_groups"],
                cap=row["candidate_fifo_depth_groups"],
                ok=row["fifo_capacity_ok"],
                speedup=row["speedup_vs_best_flat"],
            )
        )
    lines.extend(["", "## Assumptions", ""])
    for item in payload["assumptions"]:
        lines.append(f"- {item}")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def _int_list(value: str) -> list[int]:
    items = [item.strip() for item in value.split(",") if item.strip()]
    if not items:
        raise argparse.ArgumentTypeError("expected comma-separated integer list")
    parsed = [int(item) for item in items]
    if any(item <= 0 for item in parsed):
        raise argparse.ArgumentTypeError("all list items must be positive")
    return parsed


def main() -> int:
    ap = argparse.ArgumentParser(description="Model decoder logit-rank streaming hierarchy")
    ap.add_argument("--prompt-stress", help="prompt-stress evidence JSON path")
    ap.add_argument("--logit-rank-bypass", help="logit-rank bypass evidence JSON path")
    ap.add_argument("--rank-ppa", default=str(DEFAULT_RANK_PPA), help="rank datapath PPA JSON")
    ap.add_argument("--scale-ppa", default=str(DEFAULT_SCALE_PPA), help="rank scale PPA JSON")
    ap.add_argument("--vocab-size", type=int, default=50257, help="decoder vocabulary size")
    ap.add_argument("--producer-lanes", type=int, default=8, help="W-lane producer tile width")
    ap.add_argument("--top-k", type=int, default=4, help="local candidates per tile")
    ap.add_argument("--producer-latency-cycles", type=int, default=1)
    ap.add_argument("--producer-ii-cycles", type=int, default=1)
    ap.add_argument("--local-ranker-latency-cycles", type=int, default=4)
    ap.add_argument("--local-ranker-ii-cycles", type=int, default=1)
    ap.add_argument("--global-merge-latency-cycles", type=int, default=3)
    ap.add_argument("--global-merge-ii-cycles", type=_int_list, default=[1, 2, 4])
    ap.add_argument("--candidate-fifo-depth-groups", type=int, default=16)
    ap.add_argument("--fallback-critical-path-ns", type=float, default=3.6)
    ap.add_argument("--out", required=True, help="output JSON path")
    ap.add_argument("--out-md", required=True, help="output Markdown path")
    args = ap.parse_args()

    payload = build_report(
        rank_ppa_path=Path(args.rank_ppa) if args.rank_ppa else None,
        scale_ppa_path=Path(args.scale_ppa) if args.scale_ppa else None,
        prompt_stress_path=Path(args.prompt_stress) if args.prompt_stress else None,
        logit_rank_bypass_path=Path(args.logit_rank_bypass) if args.logit_rank_bypass else None,
        vocab_size=args.vocab_size,
        producer_lanes=args.producer_lanes,
        top_k=args.top_k,
        producer_latency_cycles=args.producer_latency_cycles,
        producer_ii_cycles=args.producer_ii_cycles,
        local_ranker_latency_cycles=args.local_ranker_latency_cycles,
        local_ranker_ii_cycles=args.local_ranker_ii_cycles,
        global_merge_latency_cycles=args.global_merge_latency_cycles,
        global_merge_ii_cycles_list=args.global_merge_ii_cycles,
        candidate_fifo_depth_groups=args.candidate_fifo_depth_groups,
        fallback_critical_path_ns=args.fallback_critical_path_ns,
    )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    out_md = Path(args.out_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    _write_markdown(out_md, payload)
    print(
        json.dumps(
            {
                "ok": True,
                "out": str(out),
                "out_md": str(out_md),
                "recommendation": payload["recommendation"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
