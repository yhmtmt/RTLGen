#!/usr/bin/env python3
"""Explore segmented/pipelined r64/k1 decoder ranker wrappers."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
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
        _make_tile_values,
        _operation_options,
        _reference_top1,
        _resolve_executable,
        _run,
        _write_testbench,
    )
except ImportError:  # pragma: no cover - package-style imports in tests
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
        _make_tile_values,
        _operation_options,
        _reference_top1,
        _resolve_executable,
        _run,
        _write_testbench,
    )


JsonDict = dict[str, Any]


def _rank_config(row_elems: int, logit_bits: int, top_k: int = 1) -> JsonDict:
    return {
        "version": "1.1",
        "operands": [
            {
                "name": "logits",
                "dimensions": 1,
                "bit_width": logit_bits,
                "signed": True,
                "kind": "int",
            }
        ],
        "operations": [
            {
                "type": "logit_rank",
                "module_name": f"logit_rank_r{row_elems}_l{logit_bits}_k{top_k}",
                "operand": "logits",
                "options": {
                    "row_elems": row_elems,
                    "logit_bits": logit_bits,
                    "top_k": top_k,
                    "logit_signed": True,
                },
            }
        ],
    }


def _write_json(path: Path, payload: JsonDict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _ceil_log2_at_least_one(value: int) -> int:
    if value <= 1:
        return 1
    return (value - 1).bit_length()


def _sv_signed_literal(bits: int, value: int) -> str:
    return f"-{bits}'sd{abs(value)}" if value < 0 else f"{bits}'sd{value}"


def _write_segmented_wrapper(
    path: Path,
    *,
    top: str,
    local_rank_module: str,
    global_rank_module: str,
    merge_module: str,
    producer_lanes: int,
    local_lanes: int,
    logit_bits: int,
    token_id_bits: int,
) -> None:
    groups = producer_lanes // local_lanes
    local_index_bits = _ceil_log2_at_least_one(local_lanes)
    group_index_bits = _ceil_log2_at_least_one(groups)
    logit_width = producer_lanes * logit_bits
    local_logit_width = local_lanes * logit_bits
    group_logit_width = groups * logit_bits
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
            f"  assign masked_logits[{lane * logit_bits} +: {logit_bits}] = "
            f"in_lane_valid[{lane}] ? in_logits[{lane * logit_bits} +: {logit_bits}] : {_sv_signed_literal(logit_bits, min_logit)};"
        )
    lines.extend(
        [
            f"  wire [{groups * local_index_bits - 1}:0] local_indices;",
            f"  wire signed [{group_logit_width - 1}:0] local_logits;",
        ]
    )
    for group in range(groups):
        lane_base = group * local_lanes
        lines.extend(
            [
                f"  {local_rank_module} local_rank_{group} (",
                f"    .logits(masked_logits[{lane_base * logit_bits} +: {local_logit_width}]),",
                f"    .top_indices(local_indices[{group * local_index_bits} +: {local_index_bits}]),",
                f"    .top_logits(local_logits[{group * logit_bits} +: {logit_bits}])",
                "  );",
            ]
        )
    lines.extend(
        [
            "  wire merge_in_ready;",
            "  reg stage1_valid;",
            "  reg stage1_last;",
            f"  reg signed [{group_logit_width - 1}:0] stage1_logits;",
            f"  reg [{groups * token_id_bits - 1}:0] stage1_token_ids;",
            "  reg stage2_valid;",
            "  reg stage2_last;",
            f"  reg signed [{logit_bits - 1}:0] stage2_logit;",
            f"  reg [{token_id_bits - 1}:0] stage2_token_id;",
            "  wire stage2_ready = !stage2_valid || merge_in_ready;",
            "  wire stage1_ready = !stage1_valid || stage2_ready;",
            "  assign in_ready = stage1_ready;",
            "",
            "  integer token_i;",
            "  always @(posedge clk or negedge rst_n) begin",
            "    if (!rst_n) begin",
            "      stage1_valid <= 1'b0;",
            "      stage1_last <= 1'b0;",
            "      stage1_logits <= '0;",
            "      stage1_token_ids <= '0;",
            "    end else if (stage1_ready) begin",
            "      stage1_valid <= in_valid;",
            "      stage1_last <= in_last;",
            "      stage1_logits <= local_logits;",
            f"      for (token_i = 0; token_i < {groups}; token_i = token_i + 1) begin",
            f"        stage1_token_ids[token_i*{token_id_bits} +: {token_id_bits}] <= "
            f"in_base_token_id + token_i*{local_lanes} + "
            f"{{ {token_id_bits - local_index_bits}'d0, local_indices[token_i*{local_index_bits} +: {local_index_bits}] }};",
            "      end",
            "    end",
            "  end",
            f"  wire [{group_index_bits - 1}:0] global_index;",
            f"  wire signed [{logit_bits - 1}:0] global_logit;",
            f"  {global_rank_module} global_rank (",
            "    .logits(stage1_logits),",
            "    .top_indices(global_index),",
            "    .top_logits(global_logit)",
            "  );",
            f"  reg [{token_id_bits - 1}:0] global_token_id;",
            "  always @* begin",
            "    global_token_id = '0;",
            "    case (global_index)",
        ]
    )
    for group in range(groups):
        lines.append(
            f"      {group_index_bits}'d{group}: global_token_id = stage1_token_ids[{group * token_id_bits} +: {token_id_bits}];"
        )
    lines.extend(
        [
            f"      default: global_token_id = stage1_token_ids[0 +: {token_id_bits}];",
            "    endcase",
            "  end",
            "  always @(posedge clk or negedge rst_n) begin",
            "    if (!rst_n) begin",
            "      stage2_valid <= 1'b0;",
            "      stage2_last <= 1'b0;",
            "      stage2_logit <= '0;",
            "      stage2_token_id <= '0;",
            "    end else if (stage2_ready) begin",
            "      stage2_valid <= stage1_valid;",
            "      stage2_last <= stage1_last;",
            "      stage2_logit <= global_logit;",
            "      stage2_token_id <= global_token_id;",
            "    end",
            "  end",
            f"  {merge_module} merger (",
            "    .clk(clk),",
            "    .rst_n(rst_n),",
            "    .in_valid(stage2_valid),",
            "    .in_ready(merge_in_ready),",
            "    .in_last(stage2_last),",
            "    .in_valid_mask(1'b1),",
            "    .in_token_ids(stage2_token_id),",
            "    .in_logits(stage2_logit),",
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
    local_lanes: int,
    producer_lanes: int,
    logit_bits: int,
    token_id_bits: int,
) -> JsonDict:
    groups = producer_lanes // local_lanes
    top = f"decoder_r64_k1_rankseg{local_lanes}_pipe2_wrapper"
    design_dir = design_root / top
    verilog_dir = design_dir / "verilog"
    config_dir = design_dir / "generated_configs"
    verilog_dir.mkdir(parents=True, exist_ok=True)
    for old in verilog_dir.glob("*.v"):
        old.unlink()
    local_config = config_dir / f"config_logit_rank_r{local_lanes}_l{logit_bits}_k1.json"
    global_config = config_dir / f"config_logit_rank_r{groups}_l{logit_bits}_k1.json"
    _write_json(local_config, _rank_config(local_lanes, logit_bits))
    _write_json(global_config, _rank_config(groups, logit_bits))
    local_cmd = _run([rtlgen_binary, str(local_config.resolve())], cwd=verilog_dir)
    global_cmd = _run([rtlgen_binary, str(global_config.resolve())], cwd=verilog_dir)
    merge_cmd = _run([rtlgen_binary, str(merge_config.resolve())], cwd=verilog_dir)
    if local_cmd.returncode == 0 and global_cmd.returncode == 0 and merge_cmd.returncode == 0:
        _write_segmented_wrapper(
            verilog_dir / f"{top}.v",
            top=top,
            local_rank_module=f"logit_rank_r{local_lanes}_l{logit_bits}_k1",
            global_rank_module=f"logit_rank_r{groups}_l{logit_bits}_k1",
            merge_module="candidate_stream_merge_fifo_k1_l16_t16_d16",
            producer_lanes=producer_lanes,
            local_lanes=local_lanes,
            logit_bits=logit_bits,
            token_id_bits=token_id_bits,
        )
    manifest = {
        "version": 0.1,
        "top": top,
        "producer_lanes": producer_lanes,
        "local_lanes": local_lanes,
        "groups": groups,
        "pipeline_register_cuts": ["after_local_rank", "before_merge_fifo"],
        "ii_goal": 1,
        "logit_bits": logit_bits,
        "token_id_bits": token_id_bits,
        "generated_configs": [_rel(local_config), _rel(global_config)],
    }
    _write_json(design_dir / f"config_{top}.json", manifest)
    return {
        "top": top,
        "design_dir": _rel(design_dir),
        "verilog_dir": _rel(verilog_dir),
        "local_lanes": local_lanes,
        "groups": groups,
        "status": "ok"
        if local_cmd.returncode == 0 and global_cmd.returncode == 0 and merge_cmd.returncode == 0
        else "rtlgen_failed",
        "returncodes": {
            "local": local_cmd.returncode,
            "global": global_cmd.returncode,
            "merge": merge_cmd.returncode,
        },
        "generated_verilog": sorted(_rel(path) for path in verilog_dir.glob("*.v")),
        "config_manifest": _rel(design_dir / f"config_{top}.json"),
    }


def _simulate_variant(variant: JsonDict, *, producer_lanes: int, logit_bits: int, token_id_bits: int) -> JsonDict:
    design_dir = REPO_ROOT / str(variant["design_dir"])
    verilog_dir = design_dir / "verilog"
    top = str(variant["top"])
    tiles = _make_tile_values()
    expected = _reference_top1(tiles, producer_lanes=producer_lanes)
    tb = design_dir / f"tb_{top}.v"
    _write_testbench(
        tb,
        wrapper_name=top,
        producer_lanes=producer_lanes,
        logit_bits=logit_bits,
        token_id_bits=token_id_bits,
        tiles=tiles,
        expected=expected,
    )
    sim_path = design_dir / "sim"
    sources = sorted(str(path) for path in verilog_dir.glob("*.v")) + [str(tb)]
    compile_cmd = _run(["iverilog", "-g2012", "-s", "decoder_ranker_ready_valid_tb", "-o", str(sim_path), *sources], cwd=REPO_ROOT)
    if compile_cmd.returncode != 0:
        return {
            "status": "iverilog_failed",
            "returncode": compile_cmd.returncode,
            "log_tail": compile_cmd.stdout.splitlines()[-40:],
        }
    sim_cmd = _run(["vvp", str(sim_path)], cwd=REPO_ROOT)
    return {
        "status": "ok" if sim_cmd.returncode == 0 else "vvp_failed",
        "returncode": sim_cmd.returncode,
        "expected": expected,
        "log_tail": sim_cmd.stdout.splitlines()[-40:],
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
    log_dir = REPO_ROOT / "control_plane/runtime_logs/decoder_pipelined_ranker_architecture"
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
    measured = [
        row
        for row in variants
        if (row.get("metrics_row") or {}).get("status") == "ok"
    ]
    def metric(row: JsonDict, key: str) -> float:
        return float((row.get("metrics_row") or {}).get(key, "inf"))
    best_timing = min(measured, key=lambda row: metric(row, "critical_path_ns"), default=None)
    return {
        "version": 0.1,
        "model": "decoder_pipelined_ranker_architecture_v1",
        "target": {
            "producer_lanes": 64,
            "top_k": 1,
            "pipeline_register_cuts": ["after_local_rank", "before_merge_fifo"],
            "explored_local_lanes": [row["local_lanes"] for row in variants],
            "sweep": sweep,
            "make_target": make_target,
        },
        "variants": variants,
        "best_timing_variant": (
            {
                "top": best_timing.get("top"),
                "local_lanes": best_timing.get("local_lanes"),
                "groups": best_timing.get("groups"),
                "critical_path_ns": (best_timing.get("metrics_row") or {}).get("critical_path_ns"),
                "die_area": (best_timing.get("metrics_row") or {}).get("die_area"),
                "total_power_mw": (best_timing.get("metrics_row") or {}).get("total_power_mw"),
            }
            if best_timing
            else None
        ),
        "decision": {
            "decision": "pipelined_ranker_architecture_measured" if measured else "pipelined_ranker_architecture_blocked",
            "next_step": (
                "Compare the best pipelined r64 point against the unpipelined wrapper, then decide whether to scale r128 or tune register cuts."
                if measured
                else "Fix RTL generation, simulation, or physical constraints before using pipelined ranker costs."
            ),
        },
        "assumptions": [
            "All variants preserve a 64-logit tile and top-k=1 stream contract.",
            "Local rankers operate in parallel; only local winners cross the register cut into the global selector.",
            "The generated wrappers target II=1 when downstream merge FIFO is ready; additional latency is tolerated.",
        ],
    }


def write_markdown(path: Path, payload: JsonDict) -> None:
    lines = [
        "# Decoder Pipelined Ranker Architecture",
        "",
        f"- model: `{payload['model']}`",
        f"- decision: `{payload['decision']['decision']}`",
        f"- next_step: {payload['decision']['next_step']}",
        "",
        "## Variants",
        "",
        "| local_lanes | groups | materialized | sim | synth | metrics | critical_path_ns | die_area | power_mw |",
        "|---:|---:|---|---|---|---|---:|---:|---:|",
    ]
    for row in payload["variants"]:
        metrics = row.get("metrics_row") or {}
        lines.append(
            "| {local} | {groups} | `{mat}` | `{sim}` | `{syn}` | `{met}` | {cp} | {area} | {power} |".format(
                local=row.get("local_lanes"),
                groups=row.get("groups"),
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
    ap = argparse.ArgumentParser(description="Explore pipelined r64/k1 ranker architecture variants")
    ap.add_argument("--merge-config", required=True)
    ap.add_argument("--ready-valid-equivalence")
    ap.add_argument("--rtlgen-binary", default="build/rtlgen")
    ap.add_argument("--design-root", default="runs/designs/activations")
    ap.add_argument("--local-lanes", default="8,16,32")
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
    if rtlgen_binary is None:
        variants = [
            {
                "status": "rtlgen_binary_missing",
                "requested": args.rtlgen_binary,
                "local_lanes": lanes,
                "groups": 64 // lanes,
            }
            for lanes in [int(x) for x in args.local_lanes.split(",") if x.strip()]
        ]
    else:
        merge_config = Path(args.merge_config)
        merge_opts = _operation_options(_load_json(merge_config))
        producer_lanes = 64
        logit_bits = _as_int(merge_opts.get("logit_bits"), 16)
        token_id_bits = _as_int(merge_opts.get("token_id_bits"), 16)
        variants = []
        for local_lanes in [int(x) for x in args.local_lanes.split(",") if x.strip()]:
            variant = _prepare_variant(
                rtlgen_binary=rtlgen_binary,
                merge_config=merge_config,
                design_root=REPO_ROOT / args.design_root,
                local_lanes=local_lanes,
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
