#!/usr/bin/env python3
"""Explore serial/partially-serial r64/k1 decoder ranker wrappers."""

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


def _bus_range(index: int, width: int) -> str:
    return f"{index * width} +: {width}"


def _write_serial_wrapper(
    path: Path,
    *,
    top: str,
    rank_module: str,
    merge_module: str,
    producer_lanes: int,
    lanes_per_cycle: int,
    logit_bits: int,
    token_id_bits: int,
) -> None:
    chunks = producer_lanes // lanes_per_cycle
    if chunks * lanes_per_cycle != producer_lanes:
        raise ValueError("lanes_per_cycle must divide producer_lanes")
    logit_width = producer_lanes * logit_bits
    chunk_logit_width = lanes_per_cycle * logit_bits
    chunk_index_bits = _ceil_log2_at_least_one(chunks)
    local_index_bits = _ceil_log2_at_least_one(lanes_per_cycle)
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

    lines.extend(
        [
            "  localparam STATE_IDLE = 2'd0;",
            "  localparam STATE_SCAN = 2'd1;",
            "  localparam STATE_EMIT = 2'd2;",
            "  reg [1:0] state;",
            f"  reg signed [{logit_width - 1}:0] tile_logits;",
            f"  reg [{token_id_bits - 1}:0] tile_base_token_id;",
            "  reg tile_last;",
            f"  reg [{chunk_index_bits - 1}:0] chunk_index;",
            "  reg best_valid;",
            f"  reg signed [{logit_bits - 1}:0] best_logit;",
            f"  reg [{token_id_bits - 1}:0] best_token_id;",
            f"  reg signed [{chunk_logit_width - 1}:0] chunk_logits;",
            f"  reg [{token_id_bits - 1}:0] chunk_base_token_id;",
            "  wire merge_in_ready;",
            "  wire accept_input = in_valid && in_ready;",
            "  wire emit_done = (state == STATE_EMIT) && merge_in_ready;",
            "  assign in_ready = (state == STATE_IDLE);",
            "",
            "  always @* begin",
            "    chunk_logits = '0;",
            "    chunk_base_token_id = tile_base_token_id;",
            "    case (chunk_index)",
        ]
    )
    for chunk in range(chunks):
        lane_base = chunk * lanes_per_cycle
        lines.extend(
            [
                f"      {chunk_index_bits}'d{chunk}: begin",
                f"        chunk_logits = tile_logits[{lane_base * logit_bits} +: {chunk_logit_width}];",
                f"        chunk_base_token_id = tile_base_token_id + {token_id_bits}'d{lane_base};",
                "      end",
            ]
        )
    lines.extend(
        [
            "      default: begin",
            f"        chunk_logits = tile_logits[0 +: {chunk_logit_width}];",
            "        chunk_base_token_id = tile_base_token_id;",
            "      end",
            "    endcase",
            "  end",
            f"  wire [{local_index_bits - 1}:0] chunk_top_index;",
            f"  wire signed [{logit_bits - 1}:0] chunk_top_logit;",
            f"  {rank_module} chunk_rank (",
            "    .logits(chunk_logits),",
            "    .top_indices(chunk_top_index),",
            "    .top_logits(chunk_top_logit)",
            "  );",
            f"  wire [{token_id_bits - 1}:0] chunk_top_token_id = "
            f"chunk_base_token_id + {{ {token_id_bits - local_index_bits}'d0, chunk_top_index }};",
            "  wire chunk_beats_best = !best_valid || (chunk_top_logit > best_logit) || "
            "((chunk_top_logit == best_logit) && (chunk_top_token_id < best_token_id));",
            "",
            "  always @(posedge clk or negedge rst_n) begin",
            "    if (!rst_n) begin",
            "      state <= STATE_IDLE;",
            "      tile_logits <= '0;",
            "      tile_base_token_id <= '0;",
            "      tile_last <= 1'b0;",
            "      chunk_index <= '0;",
            "      best_valid <= 1'b0;",
            "      best_logit <= '0;",
            "      best_token_id <= '0;",
            "    end else begin",
            "      case (state)",
            "        STATE_IDLE: begin",
            "          if (accept_input) begin",
            "            tile_logits <= masked_logits;",
            "            tile_base_token_id <= in_base_token_id;",
            "            tile_last <= in_last;",
            "            chunk_index <= '0;",
            "            best_valid <= 1'b0;",
            "            best_logit <= '0;",
            "            best_token_id <= '0;",
            "            state <= STATE_SCAN;",
            "          end",
            "        end",
            "        STATE_SCAN: begin",
            "          if (chunk_beats_best) begin",
            "            best_valid <= 1'b1;",
            "            best_logit <= chunk_top_logit;",
            "            best_token_id <= chunk_top_token_id;",
            "          end",
            f"          if (chunk_index == {chunk_index_bits}'d{chunks - 1}) begin",
            "            state <= STATE_EMIT;",
            "          end else begin",
            "            chunk_index <= chunk_index + 1'b1;",
            "          end",
            "        end",
            "        STATE_EMIT: begin",
            "          if (emit_done) begin",
            "            state <= STATE_IDLE;",
            "          end",
            "        end",
            "        default: state <= STATE_IDLE;",
            "      endcase",
            "    end",
            "  end",
            f"  {merge_module} merger (",
            "    .clk(clk),",
            "    .rst_n(rst_n),",
            "    .in_valid(state == STATE_EMIT),",
            "    .in_ready(merge_in_ready),",
            "    .in_last(tile_last),",
            "    .in_valid_mask(1'b1),",
            "    .in_token_ids(best_token_id),",
            "    .in_logits(best_logit),",
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
    lanes_per_cycle: int,
    producer_lanes: int,
    logit_bits: int,
    token_id_bits: int,
) -> JsonDict:
    top = f"decoder_r64_k1_serial_rank_lpc{lanes_per_cycle}_wrapper"
    design_dir = design_root / top
    verilog_dir = design_dir / "verilog"
    config_dir = design_dir / "generated_configs"
    verilog_dir.mkdir(parents=True, exist_ok=True)
    for old in verilog_dir.glob("*.v"):
        old.unlink()
    rank_config = config_dir / f"config_logit_rank_r{lanes_per_cycle}_l{logit_bits}_k1.json"
    _write_json(rank_config, _rank_config(lanes_per_cycle, logit_bits))
    rank_cmd = _run([rtlgen_binary, str(rank_config.resolve())], cwd=verilog_dir)
    merge_cmd = _run([rtlgen_binary, str(merge_config.resolve())], cwd=verilog_dir)
    if rank_cmd.returncode == 0 and merge_cmd.returncode == 0:
        _write_serial_wrapper(
            verilog_dir / f"{top}.v",
            top=top,
            rank_module=f"logit_rank_r{lanes_per_cycle}_l{logit_bits}_k1",
            merge_module="candidate_stream_merge_fifo_k1_l16_t16_d16",
            producer_lanes=producer_lanes,
            lanes_per_cycle=lanes_per_cycle,
            logit_bits=logit_bits,
            token_id_bits=token_id_bits,
        )

    chunks = producer_lanes // lanes_per_cycle
    manifest = {
        "version": 0.1,
        "top": top,
        "producer_lanes": producer_lanes,
        "lanes_per_cycle": lanes_per_cycle,
        "tile_scan_cycles": chunks,
        "ii_goal_cycles": chunks + 1,
        "architecture": "serial_running_best",
        "logit_bits": logit_bits,
        "token_id_bits": token_id_bits,
        "generated_configs": [_rel(rank_config)],
    }
    _write_json(design_dir / f"config_{top}.json", manifest)
    return {
        "top": top,
        "design_dir": _rel(design_dir),
        "verilog_dir": _rel(verilog_dir),
        "lanes_per_cycle": lanes_per_cycle,
        "tile_scan_cycles": chunks,
        "ii_goal_cycles": chunks + 1,
        "status": "ok" if rank_cmd.returncode == 0 and merge_cmd.returncode == 0 else "rtlgen_failed",
        "returncodes": {"rank": rank_cmd.returncode, "merge": merge_cmd.returncode},
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
    log_dir = REPO_ROOT / "control_plane/runtime_logs/decoder_serial_ranker_architecture"
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

    best_area = min(measured, key=lambda row: metric(row, "total_power_mw"), default=None)
    best_timing = min(measured, key=lambda row: metric(row, "critical_path_ns"), default=None)
    return {
        "version": 0.1,
        "model": "decoder_serial_ranker_architecture_v1",
        "target": {
            "producer_lanes": 64,
            "top_k": 1,
            "architecture": "serial_running_best",
            "explored_lanes_per_cycle": [row["lanes_per_cycle"] for row in variants],
            "sweep": sweep,
            "make_target": make_target,
        },
        "variants": variants,
        "best_timing_variant": (
            {
                "top": best_timing.get("top"),
                "lanes_per_cycle": best_timing.get("lanes_per_cycle"),
                "tile_scan_cycles": best_timing.get("tile_scan_cycles"),
                "critical_path_ns": (best_timing.get("metrics_row") or {}).get("critical_path_ns"),
                "die_area": (best_timing.get("metrics_row") or {}).get("die_area"),
                "total_power_mw": (best_timing.get("metrics_row") or {}).get("total_power_mw"),
            }
            if best_timing
            else None
        ),
        "lowest_power_variant": (
            {
                "top": best_area.get("top"),
                "lanes_per_cycle": best_area.get("lanes_per_cycle"),
                "tile_scan_cycles": best_area.get("tile_scan_cycles"),
                "critical_path_ns": (best_area.get("metrics_row") or {}).get("critical_path_ns"),
                "die_area": (best_area.get("metrics_row") or {}).get("die_area"),
                "total_power_mw": (best_area.get("metrics_row") or {}).get("total_power_mw"),
            }
            if best_area
            else None
        ),
        "decision": {
            "decision": "serial_ranker_architecture_measured" if measured else "serial_ranker_architecture_blocked",
            "next_step": (
                "Compare serial service time against producer output cadence, then choose a ranker point for producer coupling."
                if measured
                else "Fix RTL generation, simulation, or physical constraints before using serial ranker costs."
            ),
        },
        "assumptions": [
            "All variants preserve a 64-logit tile and top-k=1 stream contract.",
            "The serial wrapper backpressures the producer while scanning one tile; it is intended for producer cadences slower than one full 64-logit tile per cycle.",
            "The measured PPA isolates ranker area/timing and must be compared against producer service time before promotion.",
        ],
    }


def write_markdown(path: Path, payload: JsonDict) -> None:
    lines = [
        "# Decoder Serial Ranker Architecture",
        "",
        f"- model: `{payload['model']}`",
        f"- decision: `{payload['decision']['decision']}`",
        f"- next_step: {payload['decision']['next_step']}",
        "",
        "## Variants",
        "",
        "| lanes_per_cycle | scan_cycles | materialized | sim | synth | metrics | critical_path_ns | die_area | power_mw |",
        "|---:|---:|---|---|---|---|---:|---:|---:|",
    ]
    for row in payload["variants"]:
        metrics = row.get("metrics_row") or {}
        lines.append(
            "| {lpc} | {cycles} | `{mat}` | `{sim}` | `{syn}` | `{met}` | {cp} | {area} | {power} |".format(
                lpc=row.get("lanes_per_cycle"),
                cycles=row.get("tile_scan_cycles"),
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
    ap = argparse.ArgumentParser(description="Explore serial r64/k1 ranker architecture variants")
    ap.add_argument("--merge-config", required=True)
    ap.add_argument("--ready-valid-equivalence")
    ap.add_argument("--rtlgen-binary", default="build/rtlgen")
    ap.add_argument("--design-root", default="runs/designs/activations")
    ap.add_argument("--lanes-per-cycle", default="1,2,4,8,16")
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
    lane_counts = [int(x) for x in args.lanes_per_cycle.split(",") if x.strip()]
    if rtlgen_binary is None:
        variants = [
            {
                "status": "rtlgen_binary_missing",
                "requested": args.rtlgen_binary,
                "lanes_per_cycle": lanes,
                "tile_scan_cycles": 64 // lanes,
            }
            for lanes in lane_counts
        ]
    else:
        merge_config = Path(args.merge_config)
        merge_opts = _operation_options(_load_json(merge_config))
        producer_lanes = 64
        logit_bits = _as_int(merge_opts.get("logit_bits"), 16)
        token_id_bits = _as_int(merge_opts.get("token_id_bits"), 16)
        variants = []
        for lanes in lane_counts:
            variant = _prepare_variant(
                rtlgen_binary=rtlgen_binary,
                merge_config=merge_config,
                design_root=REPO_ROOT / args.design_root,
                lanes_per_cycle=lanes,
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
