#!/usr/bin/env python3
"""Explore deeper pipelined r64/k1 decoder rank-tree wrappers."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    from probe_llm_decoder_pipelined_ranker_architecture import (
        _ceil_log2_at_least_one,
        _rank_config,
        _simulate_variant,
        _sv_signed_literal,
        _write_json,
    )
    from probe_llm_decoder_producer_ranker_physical_wrapper import (
        REPO_ROOT,
        _latest_metrics_row,
        _portable_metrics_row,
        _rel,
        _run_logged,
    )
    from probe_llm_decoder_producer_ranker_ready_valid_equivalence import (
        _as_int,
        _load_json,
        _operation_options,
        _resolve_executable,
        _run,
    )
except ImportError:  # pragma: no cover - package-style imports in tests
    from npu.eval.probe_llm_decoder_pipelined_ranker_architecture import (
        _ceil_log2_at_least_one,
        _rank_config,
        _simulate_variant,
        _sv_signed_literal,
        _write_json,
    )
    from npu.eval.probe_llm_decoder_producer_ranker_physical_wrapper import (
        REPO_ROOT,
        _latest_metrics_row,
        _portable_metrics_row,
        _rel,
        _run_logged,
    )
    from npu.eval.probe_llm_decoder_producer_ranker_ready_valid_equivalence import (
        _as_int,
        _load_json,
        _operation_options,
        _resolve_executable,
        _run,
    )


JsonDict = dict[str, Any]


def _rank_tree_levels(producer_lanes: int, radix: int) -> list[dict[str, int]]:
    if radix <= 1:
        raise ValueError("radix must be greater than one")
    levels: list[dict[str, int]] = []
    source_count = producer_lanes
    while source_count > 1:
        if source_count % radix != 0:
            raise ValueError(f"producer_lanes={producer_lanes} is not an exact radix-{radix} tree")
        levels.append(
            {
                "level": len(levels),
                "source_count": source_count,
                "dest_count": source_count // radix,
            }
        )
        source_count //= radix
    return levels


def _bus_range(index: int, width: int) -> str:
    return f"{index * width} +: {width}"


def _write_rank_tree_wrapper(
    path: Path,
    *,
    top: str,
    rank_module: str,
    merge_module: str,
    producer_lanes: int,
    radix: int,
    logit_bits: int,
    token_id_bits: int,
) -> None:
    levels = _rank_tree_levels(producer_lanes, radix)
    logit_width = producer_lanes * logit_bits
    rank_index_bits = _ceil_log2_at_least_one(radix)
    min_logit = -(2 ** (logit_bits - 1))
    lines = [
        "`timescale 1ns/1ps",
        f"module {top}(",
        "  input clk,",
        "  input rst_n,",
        "  input in_valid,",
        "  output in_ready,",
        "  input in_last,",
        f"  input [{token_id_bits - 1}:0] in_base_token_id,",
        f"  input [{producer_lanes - 1}:0] in_lane_valid,",
        f"  input signed [{logit_width - 1}:0] in_logits,",
        "  output out_valid,",
        "  input out_ready,",
        "  output out_valid_mask,",
        f"  output [{token_id_bits - 1}:0] out_token_ids,",
        f"  output signed [{logit_bits - 1}:0] out_logits,",
        "  output [31:0] accepted_group_count,",
        "  output [31:0] producer_stall_cycles,",
        "  output [31:0] fifo_max_occupancy,",
        "  output [31:0] final_completion_cycle",
        ");",
        f"  wire signed [{logit_width - 1}:0] masked_logits;",
    ]
    for lane in range(producer_lanes):
        lines.append(
            f"  assign masked_logits[{_bus_range(lane, logit_bits)}] = "
            f"in_lane_valid[{lane}] ? in_logits[{_bus_range(lane, logit_bits)}] : "
            f"{_sv_signed_literal(logit_bits, min_logit)};"
        )

    lines.append("  wire merge_in_ready;")
    for register_index, level in enumerate(levels, start=1):
        count = level["dest_count"]
        lines.extend(
            [
                f"  reg stage{register_index}_valid;",
                f"  reg stage{register_index}_last;",
                f"  reg signed [{count * logit_bits - 1}:0] stage{register_index}_logits;",
                f"  reg [{count * token_id_bits - 1}:0] stage{register_index}_token_ids;",
            ]
        )

    final_stage = len(levels)
    lines.append(f"  wire stage{final_stage}_ready = !stage{final_stage}_valid || merge_in_ready;")
    for register_index in range(final_stage - 1, 0, -1):
        lines.append(
            f"  wire stage{register_index}_ready = !stage{register_index}_valid || stage{register_index + 1}_ready;"
        )
    lines.extend(["  assign in_ready = stage1_ready;", ""])

    for level in levels:
        level_index = level["level"]
        source_count = level["source_count"]
        dest_count = level["dest_count"]
        source_prefix = "masked" if level_index == 0 else f"stage{level_index}"
        dest_prefix = f"level{level_index}"
        lines.extend(
            [
                f"  wire signed [{dest_count * logit_bits - 1}:0] {dest_prefix}_logits;",
                f"  reg [{dest_count * token_id_bits - 1}:0] {dest_prefix}_token_ids;",
            ]
        )
        for group in range(dest_count):
            source_base = group * radix
            source_logit_bus = (
                "masked_logits"
                if level_index == 0
                else f"stage{level_index}_logits"
            )
            source_token_bus = "" if level_index == 0 else f"stage{level_index}_token_ids"
            lines.extend(
                [
                    f"  wire [{rank_index_bits - 1}:0] {dest_prefix}_index_{group};",
                    f"  {rank_module} rank_l{level_index}_g{group} (",
                    f"    .logits({source_logit_bus}[{source_base * logit_bits} +: {radix * logit_bits}]),",
                    f"    .top_indices({dest_prefix}_index_{group}),",
                    f"    .top_logits({dest_prefix}_logits[{_bus_range(group, logit_bits)}])",
                    "  );",
                    "  always @* begin",
                ]
            )
            lines.append(f"    case ({dest_prefix}_index_{group})")
            for choice in range(radix):
                if level_index == 0:
                    token_expr = f"in_base_token_id + {token_id_bits}'d{source_base + choice}"
                else:
                    token_expr = f"{source_token_bus}[{_bus_range(source_base + choice, token_id_bits)}]"
                lines.append(
                    f"      {rank_index_bits}'d{choice}: {dest_prefix}_token_ids[{_bus_range(group, token_id_bits)}] = {token_expr};"
                )
            fallback = (
                f"in_base_token_id + {token_id_bits}'d{source_base}"
                if level_index == 0
                else f"{source_token_bus}[{_bus_range(source_base, token_id_bits)}]"
            )
            lines.extend(
                [
                    f"      default: {dest_prefix}_token_ids[{_bus_range(group, token_id_bits)}] = {fallback};",
                    "    endcase",
                    "  end",
                ]
            )

        source_valid = "in_valid" if level_index == 0 else f"stage{level_index}_valid"
        source_last = "in_last" if level_index == 0 else f"stage{level_index}_last"
        dest_register = level_index + 1
        dest_ready = f"stage{dest_register}_ready"
        lines.extend(
            [
                f"  always @(posedge clk or negedge rst_n) begin",
                "    if (!rst_n) begin",
                f"      stage{dest_register}_valid <= 1'b0;",
                f"      stage{dest_register}_last <= 1'b0;",
                f"      stage{dest_register}_logits <= '0;",
                f"      stage{dest_register}_token_ids <= '0;",
                f"    end else if ({dest_ready}) begin",
                f"      stage{dest_register}_valid <= {source_valid};",
                f"      stage{dest_register}_last <= {source_last};",
                f"      stage{dest_register}_logits <= {dest_prefix}_logits;",
                f"      stage{dest_register}_token_ids <= {dest_prefix}_token_ids;",
                "    end",
                "  end",
                "",
            ]
        )

    lines.extend(
        [
            f"  {merge_module} merger (",
            "    .clk(clk),",
            "    .rst_n(rst_n),",
            f"    .in_valid(stage{final_stage}_valid),",
            "    .in_ready(merge_in_ready),",
            f"    .in_last(stage{final_stage}_last),",
            "    .in_valid_mask(1'b1),",
            f"    .in_token_ids(stage{final_stage}_token_ids[0 +: {token_id_bits}]),",
            f"    .in_logits(stage{final_stage}_logits[0 +: {logit_bits}]),",
            "    .out_valid(out_valid),",
            "    .out_ready(out_ready),",
            "    .out_valid_mask(out_valid_mask),",
            "    .out_token_ids(out_token_ids),",
            "    .out_logits(out_logits),",
            "    .accepted_group_count(accepted_group_count),",
            "    .producer_stall_cycles(producer_stall_cycles),",
            "    .fifo_max_occupancy(fifo_max_occupancy),",
            "    .final_completion_cycle(final_completion_cycle)",
            "  );",
            "endmodule",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def _prepare_variant(
    *,
    rtlgen_binary: str,
    merge_config: Path,
    design_root: Path,
    radix: int,
    producer_lanes: int,
    logit_bits: int,
    token_id_bits: int,
) -> JsonDict:
    levels = _rank_tree_levels(producer_lanes, radix)
    top = f"decoder_r64_k1_ranktree_radix{radix}_pipe{len(levels)}_wrapper"
    design_dir = design_root / top
    verilog_dir = design_dir / "verilog"
    config_dir = design_dir / "generated_configs"
    verilog_dir.mkdir(parents=True, exist_ok=True)
    for old in verilog_dir.glob("*.v"):
        old.unlink()

    rank_config = config_dir / f"config_logit_rank_r{radix}_l{logit_bits}_k1.json"
    _write_json(rank_config, _rank_config(radix, logit_bits))
    rank_cmd = _run([rtlgen_binary, str(rank_config.resolve())], cwd=verilog_dir)
    merge_cmd = _run([rtlgen_binary, str(merge_config.resolve())], cwd=verilog_dir)
    if rank_cmd.returncode == 0 and merge_cmd.returncode == 0:
        _write_rank_tree_wrapper(
            verilog_dir / f"{top}.v",
            top=top,
            rank_module=f"logit_rank_r{radix}_l{logit_bits}_k1",
            merge_module="candidate_stream_merge_fifo_k1_l16_t16_d16",
            producer_lanes=producer_lanes,
            radix=radix,
            logit_bits=logit_bits,
            token_id_bits=token_id_bits,
        )

    manifest = {
        "version": 0.1,
        "top": top,
        "producer_lanes": producer_lanes,
        "rank_tree_radix": radix,
        "rank_tree_levels": levels,
        "pipeline_register_cuts": ["after_each_rank_level"],
        "ii_goal": 1,
        "logit_bits": logit_bits,
        "token_id_bits": token_id_bits,
        "generated_configs": [_rel(rank_config)],
    }
    _write_json(design_dir / f"config_{top}.json", manifest)
    return {
        "top": top,
        "design_dir": _rel(design_dir),
        "verilog_dir": _rel(verilog_dir),
        "radix": radix,
        "pipeline_stages": len(levels),
        "levels": levels,
        "status": "ok" if rank_cmd.returncode == 0 and merge_cmd.returncode == 0 else "rtlgen_failed",
        "returncodes": {
            "rank": rank_cmd.returncode,
            "merge": merge_cmd.returncode,
        },
        "generated_verilog": sorted(_rel(path) for path in verilog_dir.glob("*.v")),
        "config_manifest": _rel(design_dir / f"config_{top}.json"),
    }


def _run_physical_variant(
    variant: JsonDict,
    *,
    sweep: str,
    platform: str,
    make_target: str,
    timeout_seconds: int,
    stall_timeout_seconds: int,
) -> tuple[JsonDict, JsonDict | None]:
    top = str(variant["top"])
    log_dir = REPO_ROOT / "control_plane/runtime_logs/decoder_rank_tree_architecture"
    cmd = [
        "python3",
        "npu/synth/run_block_sweep.py",
        "--design_dir",
        str(variant["design_dir"]),
        "--platform",
        platform,
        "--top",
        top,
        "--sweep",
        sweep,
        "--make_target",
        make_target,
        "--out_root",
        "runs/designs/activations",
        "--force_copy",
    ]
    synthesis = _run_logged(
        cmd,
        cwd=REPO_ROOT,
        log_path=log_dir / f"{top}_{make_target}.log",
        timeout_seconds=timeout_seconds,
        stall_timeout_seconds=stall_timeout_seconds,
    )
    metrics = _portable_metrics_row(_latest_metrics_row(REPO_ROOT / str(variant["design_dir"]) / "metrics.csv"))
    return synthesis, metrics


def build_report(*, variants: list[JsonDict], sweep: str, make_target: str) -> JsonDict:
    measured = [row for row in variants if (row.get("metrics_row") or {}).get("status") == "ok"]

    def metric(row: JsonDict, key: str) -> float:
        return float((row.get("metrics_row") or {}).get(key, "inf"))

    best_timing = min(measured, key=lambda row: metric(row, "critical_path_ns"), default=None)
    return {
        "version": 0.1,
        "model": "decoder_rank_tree_architecture_v1",
        "target": {
            "producer_lanes": 64,
            "top_k": 1,
            "pipeline_register_cuts": ["after_each_rank_level"],
            "explored_radices": [row["radix"] for row in variants],
            "sweep": sweep,
            "make_target": make_target,
        },
        "variants": variants,
        "best_timing_variant": (
            {
                "top": best_timing.get("top"),
                "radix": best_timing.get("radix"),
                "pipeline_stages": best_timing.get("pipeline_stages"),
                "critical_path_ns": (best_timing.get("metrics_row") or {}).get("critical_path_ns"),
                "die_area": (best_timing.get("metrics_row") or {}).get("die_area"),
                "total_power_mw": (best_timing.get("metrics_row") or {}).get("total_power_mw"),
            }
            if best_timing
            else None
        ),
        "decision": {
            "decision": "rank_tree_architecture_measured" if measured else "rank_tree_architecture_blocked",
            "next_step": (
                "Use the best radix as the r64 ranker anchor, then test producer-coupled timing and r128 scaling."
                if measured
                else "Fix RTL generation, simulation, or physical constraints before using rank-tree costs."
            ),
        },
        "assumptions": [
            "All variants preserve a 64-logit tile and top-k=1 stream contract.",
            "Every rank level is separated by a ready-valid register cut, so added latency is tolerated while II=1 is preserved.",
            "The radix controls ranker fan-in and pipeline depth: radix 8 reproduces the prior two-stage 8x8 shape, radix 4 and 2 test deeper trees.",
        ],
    }


def write_markdown(path: Path, payload: JsonDict) -> None:
    lines = [
        "# Decoder Rank Tree Architecture",
        "",
        f"- model: `{payload['model']}`",
        f"- decision: `{payload['decision']['decision']}`",
        f"- next_step: {payload['decision']['next_step']}",
        "",
        "## Variants",
        "",
        "| radix | stages | materialized | sim | synth | metrics | critical_path_ns | die_area | power_mw |",
        "|---:|---:|---|---|---|---|---:|---:|---:|",
    ]
    for row in payload["variants"]:
        metrics = row.get("metrics_row") or {}
        lines.append(
            "| {radix} | {stages} | `{mat}` | `{sim}` | `{syn}` | `{met}` | {cp} | {area} | {power} |".format(
                radix=row.get("radix"),
                stages=row.get("pipeline_stages"),
                mat=row.get("status"),
                sim=(row.get("simulation") or {}).get("status"),
                syn=(row.get("synthesis") or {}).get("status"),
                met=metrics.get("status"),
                cp=metrics.get("critical_path_ns", ""),
                area=metrics.get("die_area", ""),
                power=metrics.get("total_power_mw", ""),
            )
        )
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="Explore deeper pipelined r64/k1 rank-tree architecture variants")
    ap.add_argument("--merge-config", required=True)
    ap.add_argument("--ready-valid-equivalence")
    ap.add_argument("--rtlgen-binary", default="build/rtlgen")
    ap.add_argument("--design-root", default="runs/designs/activations")
    ap.add_argument("--radices", default="2,4,8")
    ap.add_argument("--sweep", required=True)
    ap.add_argument("--platform", default="nangate45")
    ap.add_argument("--make-target", default="3_3_place_gp")
    ap.add_argument("--timeout-seconds", type=int, default=1800)
    ap.add_argument("--stall-timeout-seconds", type=int, default=900)
    ap.add_argument("--skip-physical", action="store_true")
    ap.add_argument("--out", required=True)
    ap.add_argument("--out-md", required=True)
    args = ap.parse_args()

    rtlgen_binary = _resolve_executable(args.rtlgen_binary)
    radices = [int(x) for x in args.radices.split(",") if x.strip()]
    if rtlgen_binary is None:
        variants = [
            {
                "status": "rtlgen_binary_missing",
                "requested": args.rtlgen_binary,
                "radix": radix,
                "pipeline_stages": len(_rank_tree_levels(64, radix)),
            }
            for radix in radices
        ]
    else:
        merge_config = Path(args.merge_config)
        merge_opts = _operation_options(_load_json(merge_config))
        producer_lanes = 64
        logit_bits = _as_int(merge_opts.get("logit_bits"), 16)
        token_id_bits = _as_int(merge_opts.get("token_id_bits"), 16)
        variants = []
        for radix in radices:
            variant = _prepare_variant(
                rtlgen_binary=rtlgen_binary,
                merge_config=merge_config,
                design_root=REPO_ROOT / args.design_root,
                radix=radix,
                producer_lanes=producer_lanes,
                logit_bits=logit_bits,
                token_id_bits=token_id_bits,
            )
            if variant["status"] == "ok":
                variant["simulation"] = _simulate_variant(
                    variant,
                    producer_lanes=producer_lanes,
                    logit_bits=logit_bits,
                    token_id_bits=token_id_bits,
                )
            if (
                variant["status"] == "ok"
                and (variant.get("simulation") or {}).get("status") == "ok"
                and not args.skip_physical
            ):
                synthesis, metrics = _run_physical_variant(
                    variant,
                    sweep=args.sweep,
                    platform=args.platform,
                    make_target=args.make_target,
                    timeout_seconds=args.timeout_seconds,
                    stall_timeout_seconds=args.stall_timeout_seconds,
                )
                variant["synthesis"] = synthesis
                variant["metrics_row"] = metrics
            variants.append(variant)

    payload = build_report(variants=variants, sweep=args.sweep, make_target=args.make_target)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    out_md = Path(args.out_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    write_markdown(out_md, payload)
    print(json.dumps({"ok": True, "out": str(out), "out_md": str(out_md)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
