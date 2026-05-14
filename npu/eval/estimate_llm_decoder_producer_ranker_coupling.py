#!/usr/bin/env python3
"""Estimate decoder output-projection producer service coupled to logit ranker."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys
from typing import Any

try:
    from npu.eval.model_llm_decoder_logit_rank_streaming import build_report
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from model_llm_decoder_logit_rank_streaming import build_report

JsonDict = dict[str, Any]


def _int_list(value: str) -> list[int]:
    items = [item.strip() for item in value.split(",") if item.strip()]
    if not items:
        raise argparse.ArgumentTypeError("expected comma-separated integer list")
    parsed = [int(item) for item in items]
    if any(item <= 0 for item in parsed):
        raise argparse.ArgumentTypeError("all list items must be positive")
    return parsed


def _float_list(value: str) -> list[float]:
    items = [item.strip() for item in value.split(",") if item.strip()]
    if not items:
        raise argparse.ArgumentTypeError("expected comma-separated float list")
    parsed = [float(item) for item in items]
    if any(item <= 0.0 for item in parsed):
        raise argparse.ArgumentTypeError("all list items must be positive")
    return parsed


def _byte_width(bits: int) -> int:
    return max(1, math.ceil(bits / 8))


def _ceil_div(a: int, b: int) -> int:
    return (a + b - 1) // b


def _load_producer_control_boundary(path: Path | None) -> JsonDict | None:
    if path is None:
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    diagnosis = payload.get("diagnosis") if isinstance(payload.get("diagnosis"), dict) else {}
    guard = None
    for row in payload.get("probe_rows", []):
        if isinstance(row, dict) and row.get("variant") == "cq_v1_softmax_event_guard":
            guard = row
            break
    if guard is None:
        return {
            "source": str(path),
            "status": "missing_guard_variant",
            "decision": diagnosis.get("decision"),
        }
    synthesis = guard.get("synthesis") if isinstance(guard.get("synthesis"), dict) else {}
    static_stats = (
        guard.get("static_verilog_stats")
        if isinstance(guard.get("static_verilog_stats"), dict)
        else {}
    )
    metrics = guard.get("metrics_row") if isinstance(guard.get("metrics_row"), dict) else {}
    return {
        "source": str(path),
        "status": guard.get("status"),
        "decision": diagnosis.get("decision"),
        "guard_variant": guard.get("variant"),
        "synthesis_status": synthesis.get("status"),
        "synthesis_elapsed_seconds": synthesis.get("elapsed_seconds"),
        "flow_elapsed_seconds": metrics.get("flow_elapsed_seconds"),
        "stage_elapsed_seconds": metrics.get("stage_elapsed_seconds"),
        "verilog_kb": round(float(static_stats.get("verilog_bytes", 0) or 0) / 1024.0, 3),
        "reg_bits_est": static_stats.get("reg_bit_count_est"),
        "wire_bits_est": static_stats.get("wire_bit_count_est"),
    }


def _producer_service_row(
    *,
    scenario: str,
    vocab_size: int,
    hidden_size: int,
    producer_lanes: int,
    macs_per_cycle: int,
    memory_bandwidth_bytes_per_cycle: float,
    memory_share: float,
    weight_bits: int,
    activation_bits: int,
    clock_ns: float,
) -> JsonDict:
    if memory_share <= 0.0:
        raise ValueError("memory_share must be positive")
    effective_bandwidth = memory_bandwidth_bytes_per_cycle * memory_share
    tile_count = _ceil_div(vocab_size, producer_lanes)
    weight_bytes_per_tile = producer_lanes * hidden_size * _byte_width(weight_bits)
    hidden_bytes_per_token = hidden_size * _byte_width(activation_bits)
    macs_per_tile = producer_lanes * hidden_size
    compute_cycles_per_tile = _ceil_div(macs_per_tile, macs_per_cycle)
    weight_cycles_per_tile = math.ceil(weight_bytes_per_tile / effective_bandwidth)
    hidden_load_cycles = math.ceil(hidden_bytes_per_token / effective_bandwidth)
    producer_ii_cycles = max(1, compute_cycles_per_tile, weight_cycles_per_tile)
    producer_latency_cycles = hidden_load_cycles + compute_cycles_per_tile
    total_cycles = producer_latency_cycles + max(0, tile_count - 1) * producer_ii_cycles
    return {
        "scenario": scenario,
        "vocab_size": vocab_size,
        "hidden_size": hidden_size,
        "producer_lanes": producer_lanes,
        "tile_count": tile_count,
        "macs_per_cycle": macs_per_cycle,
        "memory_bandwidth_bytes_per_cycle": memory_bandwidth_bytes_per_cycle,
        "memory_share": memory_share,
        "effective_memory_bandwidth_bytes_per_cycle": effective_bandwidth,
        "weight_bits": weight_bits,
        "activation_bits": activation_bits,
        "macs_per_tile": macs_per_tile,
        "weight_bytes_per_tile": weight_bytes_per_tile,
        "hidden_bytes_per_token": hidden_bytes_per_token,
        "weight_bytes_per_token": weight_bytes_per_tile * tile_count,
        "compute_cycles_per_tile": compute_cycles_per_tile,
        "weight_cycles_per_tile": weight_cycles_per_tile,
        "hidden_load_cycles": hidden_load_cycles,
        "producer_latency_cycles": producer_latency_cycles,
        "producer_ii_cycles": producer_ii_cycles,
        "producer_total_cycles": total_cycles,
        "producer_latency_us_per_token": round(total_cycles * clock_ns / 1000.0, 6),
        "service_limiter": (
            "weight_memory"
            if weight_cycles_per_tile >= compute_cycles_per_tile
            else "compute_array"
        ),
    }


def build_coupling_report(
    *,
    mode: str,
    rank_ppa_path: Path | None,
    scale_ppa_path: Path | None,
    candidate_merge_ppa_path: Path | None,
    boundary_ppa_path: Path | None,
    producer_control_boundary_path: Path | None,
    sram_metrics_json_path: Path | None,
    vocab_size_list: list[int],
    hidden_size_list: list[int],
    producer_lanes_list: list[int],
    macs_per_cycle_list: list[int],
    memory_bandwidth_bytes_per_cycle_list: list[float],
    memory_share_list: list[float],
    top_k_list: list[int],
    weight_bits: int,
    activation_bits: int,
    clock_ns: float,
) -> JsonDict:
    producer_control_boundary = _load_producer_control_boundary(producer_control_boundary_path)
    scenarios = (
        ["shared_gemm_stage_serial"]
        if mode == "producer_service"
        else ["shared_gemm_stage_serial", "shared_noc_contention"]
    )
    producer_rows: list[JsonDict] = []
    for scenario in scenarios:
        shares = [1.0] if scenario == "shared_gemm_stage_serial" else memory_share_list
        for vocab_size in vocab_size_list:
            for hidden_size in hidden_size_list:
                for lanes in producer_lanes_list:
                    for macs_per_cycle in macs_per_cycle_list:
                        for bandwidth in memory_bandwidth_bytes_per_cycle_list:
                            for share in shares:
                                producer_rows.append(
                                    _producer_service_row(
                                        scenario=scenario,
                                        vocab_size=vocab_size,
                                        hidden_size=hidden_size,
                                        producer_lanes=lanes,
                                        macs_per_cycle=macs_per_cycle,
                                        memory_bandwidth_bytes_per_cycle=bandwidth,
                                        memory_share=share,
                                        weight_bits=weight_bits,
                                        activation_bits=activation_bits,
                                        clock_ns=clock_ns,
                                    )
                                )

    coupled_rows: list[JsonDict] = []
    if mode == "coupled_noc":
        primary_vocab = vocab_size_list[0]
        producer_iis = sorted({row["producer_ii_cycles"] for row in producer_rows})
        rank_report = build_report(
            rank_ppa_path=rank_ppa_path,
            scale_ppa_path=scale_ppa_path,
            candidate_merge_ppa_path=candidate_merge_ppa_path,
            boundary_ppa_path=boundary_ppa_path,
            sram_metrics_json_path=sram_metrics_json_path,
            vocab_size=primary_vocab,
            vocab_size_list=vocab_size_list,
            producer_lanes_list=producer_lanes_list,
            producer_interface_focus_lanes=[lane for lane in producer_lanes_list if lane >= 64],
            top_k_list=top_k_list,
            producer_ii_cycles_list=producer_iis,
            global_merge_ii_cycles_list=[1, 2],
            candidate_fifo_depth_groups_list=[16, 256],
            memory_bandwidth_bytes_per_cycle=memory_bandwidth_bytes_per_cycle_list[0],
            noc_hops=2,
        )
        rank_rows = {
            (
                row.get("vocab_size"),
                row.get("producer_lanes"),
                row.get("producer_ii_cycles"),
                row.get("local_top_k"),
            ): row
            for row in rank_report.get("overlap_traffic_sweep", [])
            if row.get("global_merge_ii_cycles") == 1
            and row.get("candidate_fifo_depth_groups") == 16
        }
        for producer in producer_rows:
            for top_k in top_k_list:
                rank = rank_rows.get(
                    (
                        producer["vocab_size"],
                        producer["producer_lanes"],
                        producer["producer_ii_cycles"],
                        top_k,
                    )
                )
                if rank is None:
                    continue
                coupled_latency_us = max(
                    producer["producer_latency_us_per_token"],
                    rank["timing"]["latency_us_per_token"],
                )
                coupled_rows.append(
                    {
                        "scenario": producer["scenario"],
                        "vocab_size": producer["vocab_size"],
                        "hidden_size": producer["hidden_size"],
                        "producer_lanes": producer["producer_lanes"],
                        "top_k": top_k,
                        "macs_per_cycle": producer["macs_per_cycle"],
                        "memory_share": producer["memory_share"],
                        "producer_ii_cycles": producer["producer_ii_cycles"],
                        "producer_latency_us_per_token": producer["producer_latency_us_per_token"],
                        "ranker_latency_us_per_token": rank["timing"]["latency_us_per_token"],
                        "coupled_latency_us_per_token": coupled_latency_us,
                        "ranker_fifo_capacity_ok": rank["fifo_capacity_ok"],
                        "ranker_required_fifo_depth_groups": rank["required_fifo_depth_groups"],
                        "ranker_candidate_memory_bytes": rank["traffic"]["streaming_candidate_memory_bytes"],
                        "ranker_traffic_reduction_vs_materialized": rank["traffic"]["traffic_reduction_vs_materialized"],
                        "service_limiter": producer["service_limiter"],
                    }
                )
    else:
        rank_report = None

    producer_best = min(
        producer_rows,
        key=lambda row: (
            row["producer_latency_us_per_token"],
            row["weight_bytes_per_token"],
            -row["producer_lanes"],
        ),
    )
    coupled_best = (
        min(
            coupled_rows,
            key=lambda row: (
                not row["ranker_fifo_capacity_ok"],
                row["coupled_latency_us_per_token"],
                row["ranker_candidate_memory_bytes"],
            ),
        )
        if coupled_rows
        else None
    )
    return {
        "version": 0.1,
        "model": "decoder_output_projection_producer_ranker_coupling_v1",
        "mode": mode,
        "inputs": {
            "vocab_size_list": vocab_size_list,
            "hidden_size_list": hidden_size_list,
            "producer_lanes_list": producer_lanes_list,
            "macs_per_cycle_list": macs_per_cycle_list,
            "memory_bandwidth_bytes_per_cycle_list": memory_bandwidth_bytes_per_cycle_list,
            "memory_share_list": memory_share_list,
            "top_k_list": top_k_list,
            "weight_bits": weight_bits,
            "activation_bits": activation_bits,
            "clock_ns": clock_ns,
        },
        "producer_control_boundary": producer_control_boundary,
        "assumptions": [
            "Producer means only the final decoder output-projection logit source.",
            "Shared GEMM is stage-serialized: attention/MLP have completed before output projection starts.",
            "producer_ii_cycles is derived as max(compute cycles per tile, weight-memory service cycles per tile).",
            "Hidden vector load is charged once per token; output projection weights are streamed per vocabulary tile.",
            "shared_noc_contention reduces effective producer memory bandwidth by memory_share.",
            "Ranker coupling reuses the ready-valid logit-rank model and preserves its equivalence observables.",
            "If producer_control_boundary is present, it is control-path synthesis feasibility evidence; it does not replace the output-projection service model.",
        ],
        "producer_service_sweep": producer_rows,
        "coupled_ranker_sweep": coupled_rows,
        "ranker_report_summary": (
            {
                "recommendation": rank_report.get("recommendation"),
                "producer_integrated_interface": rank_report.get("producer_integrated_interface"),
            }
            if mode == "coupled_noc" and rank_report is not None
            else None
        ),
        "recommendation": {
            "producer_service_best": producer_best,
            "coupled_best": coupled_best,
            "reason": (
                "Lowest producer service latency first; coupled mode additionally requires FIFO-valid "
                "ranker rows and then minimizes candidate traffic."
            ),
        },
    }


def _write_markdown(path: Path, payload: JsonDict) -> None:
    rec = payload["recommendation"]
    lines = [
        "# Decoder Producer/Ranker Coupling",
        "",
        f"- model: `{payload['model']}`",
        f"- mode: `{payload['mode']}`",
        f"- producer_service_best: `{rec['producer_service_best']['scenario']} "
        f"w{rec['producer_service_best']['producer_lanes']} "
        f"ii{rec['producer_service_best']['producer_ii_cycles']}`",
    ]
    if rec.get("coupled_best"):
        best = rec["coupled_best"]
        lines.append(
            f"- coupled_best: `{best['scenario']} w{best['producer_lanes']} k{best['top_k']} "
            f"ii{best['producer_ii_cycles']}`"
        )
    if payload.get("producer_control_boundary"):
        boundary = payload["producer_control_boundary"]
        lines.extend(
            [
                f"- producer_control_boundary: `{boundary.get('decision')} "
                f"{boundary.get('guard_variant')} {boundary.get('synthesis_status')}`",
                f"- producer_control_boundary_elapsed_s: `{boundary.get('synthesis_elapsed_seconds')}`",
            ]
        )
    lines.extend(
        [
            "",
            "## Producer Service Sweep",
            "",
            "| scenario | vocab | hidden | W | MAC/cycle | BW | share | II | limiter | latency_us | weight_bytes/token |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|",
        ]
    )
    for row in payload["producer_service_sweep"][:48]:
        lines.append(
            "| {scenario} | {vocab} | {hidden} | {lanes} | {macs} | {bw} | {share} | {ii} | {limiter} | {latency} | {bytes} |".format(
                scenario=row["scenario"],
                vocab=row["vocab_size"],
                hidden=row["hidden_size"],
                lanes=row["producer_lanes"],
                macs=row["macs_per_cycle"],
                bw=row["memory_bandwidth_bytes_per_cycle"],
                share=row["memory_share"],
                ii=row["producer_ii_cycles"],
                limiter=row["service_limiter"],
                latency=row["producer_latency_us_per_token"],
                bytes=row["weight_bytes_per_token"],
            )
        )
    if payload.get("coupled_ranker_sweep"):
        lines.extend(
            [
                "",
                "## Coupled Ranker Sweep",
                "",
                "| scenario | vocab | hidden | W | top_k | MAC/cycle | share | producer_ii | producer_us | ranker_us | coupled_us | fifo ok | candidate_bytes | traffic reduction |",
                "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|",
            ]
        )
        for row in payload["coupled_ranker_sweep"][:48]:
            lines.append(
                "| {scenario} | {vocab} | {hidden} | {lanes} | {topk} | {macs} | {share} | {ii} | {prod_us} | {rank_us} | {coupled_us} | `{ok}` | {cand_bytes} | {traffic} |".format(
                    scenario=row["scenario"],
                    vocab=row["vocab_size"],
                    hidden=row["hidden_size"],
                    lanes=row["producer_lanes"],
                    topk=row["top_k"],
                    macs=row["macs_per_cycle"],
                    share=row["memory_share"],
                    ii=row["producer_ii_cycles"],
                    prod_us=row["producer_latency_us_per_token"],
                    rank_us=row["ranker_latency_us_per_token"],
                    coupled_us=row["coupled_latency_us_per_token"],
                    ok=row["ranker_fifo_capacity_ok"],
                    cand_bytes=row["ranker_candidate_memory_bytes"],
                    traffic=row["ranker_traffic_reduction_vs_materialized"],
                )
            )
    lines.extend(["", "## Assumptions", ""])
    for item in payload["assumptions"]:
        lines.append(f"- {item}")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="Estimate output-projection producer and ranker coupling")
    ap.add_argument("--mode", choices=["producer_service", "coupled_noc"], required=True)
    ap.add_argument("--rank-ppa", help="rank datapath PPA JSON")
    ap.add_argument("--scale-ppa", help="rank scale PPA JSON")
    ap.add_argument("--candidate-merge-ppa", help="candidate merge PPA JSON")
    ap.add_argument("--boundary-ppa", help="boundary diagnostic PPA JSON")
    ap.add_argument("--producer-control-boundary", help="bounded producer control-path evidence JSON")
    ap.add_argument("--sram-metrics-json", help="SRAM metrics JSON")
    ap.add_argument("--vocab-size-list", type=_int_list, default=[50257, 100000, 200000])
    ap.add_argument("--hidden-size-list", type=_int_list, default=[768, 1024, 2048])
    ap.add_argument("--producer-lanes-list", type=_int_list, default=[64, 128])
    ap.add_argument("--macs-per-cycle-list", type=_int_list, default=[8192, 32768])
    ap.add_argument("--memory-bandwidth-bytes-per-cycle-list", type=_float_list, default=[64.0, 256.0])
    ap.add_argument("--memory-share-list", type=_float_list, default=[1.0, 0.5, 0.25])
    ap.add_argument("--top-k-list", type=_int_list, default=[1, 4])
    ap.add_argument("--weight-bits", type=int, default=16)
    ap.add_argument("--activation-bits", type=int, default=16)
    ap.add_argument("--clock-ns", type=float, default=1.0)
    ap.add_argument("--out", required=True)
    ap.add_argument("--out-md", required=True)
    args = ap.parse_args()
    payload = build_coupling_report(
        mode=args.mode,
        rank_ppa_path=Path(args.rank_ppa) if args.rank_ppa else None,
        scale_ppa_path=Path(args.scale_ppa) if args.scale_ppa else None,
        candidate_merge_ppa_path=Path(args.candidate_merge_ppa) if args.candidate_merge_ppa else None,
        boundary_ppa_path=Path(args.boundary_ppa) if args.boundary_ppa else None,
        producer_control_boundary_path=Path(args.producer_control_boundary) if args.producer_control_boundary else None,
        sram_metrics_json_path=Path(args.sram_metrics_json) if args.sram_metrics_json else None,
        vocab_size_list=args.vocab_size_list,
        hidden_size_list=args.hidden_size_list,
        producer_lanes_list=args.producer_lanes_list,
        macs_per_cycle_list=args.macs_per_cycle_list,
        memory_bandwidth_bytes_per_cycle_list=args.memory_bandwidth_bytes_per_cycle_list,
        memory_share_list=args.memory_share_list,
        top_k_list=args.top_k_list,
        weight_bits=args.weight_bits,
        activation_bits=args.activation_bits,
        clock_ns=args.clock_ns,
    )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    out_md = Path(args.out_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    _write_markdown(out_md, payload)
    print(json.dumps({"ok": True, "out": str(out), "out_md": str(out_md)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
