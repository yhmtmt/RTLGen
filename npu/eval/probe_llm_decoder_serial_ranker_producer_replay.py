#!/usr/bin/env python3
"""Replay producer-like tile cadence through measured serial ranker RTL wrappers."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import shutil
import tempfile
from typing import Any

try:
    from probe_llm_decoder_pipelined_ranker_architecture import _rank_config
    from probe_llm_decoder_producer_ranker_ready_valid_equivalence import (
        _as_int,
        _resolve_executable,
        _run,
        _sv_signed_literal,
    )
    from probe_llm_decoder_producer_ranker_physical_wrapper import REPO_ROOT
except ImportError:  # pragma: no cover - package-style imports in tests
    from npu.eval.probe_llm_decoder_pipelined_ranker_architecture import _rank_config
    from npu.eval.probe_llm_decoder_producer_ranker_ready_valid_equivalence import (
        _as_int,
        _resolve_executable,
        _run,
        _sv_signed_literal,
    )
    from npu.eval.probe_llm_decoder_producer_ranker_physical_wrapper import REPO_ROOT


JsonDict = dict[str, Any]


def _load_json(path: str | Path) -> JsonDict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _make_tile_values(*, num_tiles: int, producer_lanes: int) -> list[list[int]]:
    tiles: list[list[int]] = []
    for tile in range(num_tiles):
        row = []
        for lane in range(producer_lanes):
            row.append(((tile + 3) * 23 + lane * 7) % 257 - 128)
        tiles.append(row)
    if num_tiles:
        tiles[0][5] = 500
    if num_tiles > 1:
        tiles[1][2] = 499
    if num_tiles > 2:
        tiles[2][7] = 500
    if num_tiles > 4:
        tiles[4][11] = 498
    return tiles


def _reference_top1(tiles: list[list[int]], *, producer_lanes: int) -> JsonDict:
    best_token = None
    best_logit = None
    for tile_id, logits in enumerate(tiles):
        for lane, logit in enumerate(logits):
            token = tile_id * producer_lanes + lane
            if best_logit is None or logit > best_logit or (
                logit == best_logit and token < int(best_token)
            ):
                best_token = token
                best_logit = logit
    return {"token": best_token, "logit": best_logit}


def _write_cadence_testbench(
    path: Path,
    *,
    wrapper_name: str,
    producer_lanes: int,
    logit_bits: int,
    token_id_bits: int,
    tiles: list[list[int]],
    expected: JsonDict,
    producer_ii_cycles: int,
    scenario: str,
    lanes_per_cycle: int,
) -> None:
    logit_width = producer_lanes * logit_bits
    num_tiles = len(tiles)
    wait_limit = producer_ii_cycles * max(4, num_tiles * 2) + 512
    lines = [
        "`timescale 1ns/1ps",
        "module decoder_serial_ranker_producer_replay_tb;",
        "  reg clk;",
        "  reg rst_n;",
        "  reg in_valid;",
        "  wire in_ready;",
        "  reg in_last;",
        f"  reg [{token_id_bits - 1}:0] in_base_token_id;",
        f"  reg [{producer_lanes - 1}:0] in_lane_valid;",
        f"  reg signed [{logit_width - 1}:0] in_logits;",
        "  wire out_valid;",
        "  reg out_ready;",
        "  wire out_valid_mask;",
        f"  wire [{token_id_bits - 1}:0] out_token_ids;",
        f"  wire signed [{logit_bits - 1}:0] out_logits;",
        "  wire [31:0] accepted_group_count;",
        "  wire [31:0] producer_stall_cycles;",
        "  wire [31:0] fifo_max_occupancy;",
        "  wire [31:0] final_completion_cycle;",
        "  integer cycle;",
        "  integer tile_id;",
        "  integer wait_cycles;",
        "  integer next_issue_cycle;",
        "  integer tb_backpressure_cycles;",
        f"  {wrapper_name} dut (",
        "    .clk(clk), .rst_n(rst_n), .in_valid(in_valid), .in_ready(in_ready),",
        "    .in_last(in_last), .in_base_token_id(in_base_token_id),",
        "    .in_lane_valid(in_lane_valid), .in_logits(in_logits),",
        "    .out_valid(out_valid), .out_ready(out_ready), .out_valid_mask(out_valid_mask),",
        "    .out_token_ids(out_token_ids), .out_logits(out_logits),",
        "    .accepted_group_count(accepted_group_count),",
        "    .producer_stall_cycles(producer_stall_cycles),",
        "    .fifo_max_occupancy(fifo_max_occupancy),",
        "    .final_completion_cycle(final_completion_cycle)",
        "  );",
        "  always #5 clk = ~clk;",
        "  always @(posedge clk or negedge rst_n) begin",
        "    if (!rst_n) cycle <= 0;",
        "    else cycle <= cycle + 1;",
        "  end",
        "  task clear_logits;",
        "    integer i;",
        "    begin",
        f"      for (i = 0; i < {producer_lanes}; i = i + 1) begin",
        f"        in_logits[i*{logit_bits} +: {logit_bits}] = {logit_bits}'sd0;",
        "      end",
        "    end",
        "  endtask",
        "  task drive_tile;",
        "    input [31:0] tid;",
        "    input last;",
        "    begin",
        "      in_valid = 1'b1;",
        "      in_last = last;",
        f"      in_base_token_id = tid * {producer_lanes};",
        f"      in_lane_valid = {{{producer_lanes}{{1'b1}}}};",
        "      clear_logits();",
    ]
    for tile_id, logits in enumerate(tiles):
        lines.append(f"      if (tid == {tile_id}) begin")
        for lane, value in enumerate(logits):
            lines.append(
                f"        in_logits[{lane * logit_bits} +: {logit_bits}] = "
                f"{_sv_signed_literal(logit_bits, value)};"
            )
        lines.append("      end")
    lines.extend(
        [
            "      while (!in_ready) begin",
            "        tb_backpressure_cycles = tb_backpressure_cycles + 1;",
            "        @(negedge clk);",
            "      end",
            "      @(negedge clk);",
            "      in_valid = 1'b0;",
            "      in_last = 1'b0;",
            "      in_base_token_id = 0;",
            "      in_lane_valid = 0;",
            "      clear_logits();",
            "    end",
            "  endtask",
            "  initial begin",
            "    clk = 1'b0;",
            "    rst_n = 1'b0;",
            "    in_valid = 1'b0;",
            "    in_last = 1'b0;",
            "    in_base_token_id = 0;",
            "    in_lane_valid = 0;",
            "    out_ready = 1'b0;",
            "    tb_backpressure_cycles = 0;",
            "    next_issue_cycle = 0;",
            "    clear_logits();",
            "    repeat (3) @(negedge clk);",
            "    rst_n = 1'b1;",
            f"    for (tile_id = 0; tile_id < {num_tiles}; tile_id = tile_id + 1) begin",
            "      while (cycle < next_issue_cycle) begin",
            "        @(negedge clk);",
            "      end",
            f"      drive_tile(tile_id, tile_id == ({num_tiles} - 1));",
            f"      next_issue_cycle = next_issue_cycle + {producer_ii_cycles};",
            "    end",
            "    wait_cycles = 0;",
            f"    while (!out_valid && wait_cycles < {wait_limit}) begin",
            "      wait_cycles = wait_cycles + 1;",
            "      @(negedge clk);",
            "    end",
            "    if (!out_valid) begin",
            "      $display(\"FAIL no out_valid wait=%0d\", wait_cycles);",
            "      $fatal;",
            "    end",
            f"    if (out_valid_mask !== 1'b1 || out_token_ids !== {token_id_bits}'d{expected['token']} || "
            f"$signed(out_logits) !== {_sv_signed_literal(logit_bits, int(expected['logit']))}) begin",
            "      $display(\"FAIL result token=%0d logit=%0d mask=%b\", out_token_ids, $signed(out_logits), out_valid_mask);",
            "      $fatal;",
            "    end",
            f"    $display(\"RESULT scenario={scenario} lpc={lanes_per_cycle} producer_ii={producer_ii_cycles} token=%0d logit=%0d accepted=%0d tb_backpressure=%0d dut_stalls=%0d fifo_max=%0d final_cycle=%0d\",",
            "      out_token_ids, $signed(out_logits), accepted_group_count, tb_backpressure_cycles,",
            "      producer_stall_cycles, fifo_max_occupancy, final_completion_cycle);",
            "    out_ready = 1'b1;",
            "    @(negedge clk);",
            "    out_ready = 1'b0;",
            "    $finish;",
            "  end",
            "endmodule",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def _simulate_variant(
    *,
    variant: JsonDict,
    scenario: str,
    producer_ii_cycles: int,
    num_tiles: int,
    merge_config: Path,
    rtlgen_binary: str | None,
    producer_lanes: int,
    logit_bits: int,
    token_id_bits: int,
) -> JsonDict:
    iverilog = shutil.which("iverilog")
    vvp = shutil.which("vvp")
    if iverilog is None or vvp is None:
        return {"status": "simulator_missing", "iverilog": iverilog, "vvp": vvp}
    top = str(variant["top"])
    design_dir = REPO_ROOT / str(variant["design_dir"])
    rank_module = f"logit_rank_r{variant['lanes_per_cycle']}_l{logit_bits}_k1"
    merge_module = "candidate_stream_merge_fifo_k1_l16_t16_d16"
    wrapper = design_dir / "verilog" / f"{top}.v"
    if not wrapper.is_file():
        return {"status": "wrapper_missing", "wrapper": str(wrapper)}
    tiles = _make_tile_values(num_tiles=num_tiles, producer_lanes=producer_lanes)
    expected = _reference_top1(tiles, producer_lanes=producer_lanes)
    with tempfile.TemporaryDirectory() as td:
        work = Path(td)
        if rtlgen_binary is None:
            return {
                "status": "rtlgen_binary_missing",
                "required_modules": [rank_module, merge_module],
            }
        generated_config = work / f"config_{rank_module}.json"
        generated_config.write_text(
            json.dumps(_rank_config(int(variant["lanes_per_cycle"]), logit_bits), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        rank_cmd = _run([rtlgen_binary, str(generated_config.resolve())], cwd=work)
        merge_cmd = _run([rtlgen_binary, str(merge_config.resolve())], cwd=work)
        if rank_cmd.returncode != 0 or merge_cmd.returncode != 0:
            return {
                "status": "rtlgen_failed",
                "rank_returncode": rank_cmd.returncode,
                "merge_returncode": merge_cmd.returncode,
                "rank_log_tail": rank_cmd.stdout.splitlines()[-20:],
                "merge_log_tail": merge_cmd.stdout.splitlines()[-20:],
            }
        tb = work / f"tb_{top}_producer_replay_{scenario}.v"
        _write_cadence_testbench(
            tb,
            wrapper_name=top,
            producer_lanes=producer_lanes,
            logit_bits=logit_bits,
            token_id_bits=token_id_bits,
            tiles=tiles,
            expected=expected,
            producer_ii_cycles=producer_ii_cycles,
            scenario=scenario,
            lanes_per_cycle=int(variant["lanes_per_cycle"]),
        )
        sim_path = work / f"sim_producer_replay_{scenario}"
        sources = [
            str(wrapper),
            str(work / f"{rank_module}.v"),
            str(work / f"{merge_module}.v"),
            str(tb),
        ]
        compile_cmd = _run(
            [
                "iverilog",
                "-g2012",
                "-s",
                "decoder_serial_ranker_producer_replay_tb",
                "-o",
                str(sim_path),
                *sources,
            ],
            cwd=REPO_ROOT,
        )
        if compile_cmd.returncode != 0:
            return {
                "status": "iverilog_failed",
                "returncode": compile_cmd.returncode,
                "log_tail": compile_cmd.stdout.splitlines()[-40:],
            }
        sim_cmd = _run(["vvp", str(sim_path)], cwd=REPO_ROOT)
    result: JsonDict = {
        "status": "ok" if sim_cmd.returncode == 0 else "vvp_failed",
        "returncode": sim_cmd.returncode,
        "expected": expected,
        "log_tail": sim_cmd.stdout.splitlines()[-40:],
    }
    match = re.search(
        r"RESULT scenario=(?P<scenario>\S+) lpc=(?P<lpc>\d+) producer_ii=(?P<producer_ii>\d+) "
        r"token=(?P<token>\d+) logit=(?P<logit>-?\d+) accepted=(?P<accepted>\d+) "
        r"tb_backpressure=(?P<tb_backpressure>\d+) dut_stalls=(?P<dut_stalls>\d+) "
        r"fifo_max=(?P<fifo_max>\d+) final_cycle=(?P<final_cycle>\d+)",
        sim_cmd.stdout,
    )
    if match:
        result["observed"] = {key: int(value) if value.lstrip("-").isdigit() else value for key, value in match.groupdict().items()}
    return result


def _variant_by_lanes(serial_ranker: JsonDict) -> dict[int, JsonDict]:
    return {
        int(variant["lanes_per_cycle"]): variant
        for variant in serial_ranker.get("variants", [])
        if isinstance(variant, dict) and variant.get("status") == "ok" and "lanes_per_cycle" in variant
    }


def _service_cycles(variant: JsonDict) -> int:
    return _as_int(variant.get("ii_goal_cycles"), _as_int(variant.get("tile_scan_cycles"), 0) + 1)


def build_report(
    *,
    serial_ranker: JsonDict,
    service_compatibility: JsonDict | None,
    replay_rows: list[JsonDict],
    producer_ii_cycles: list[int],
    lanes_per_cycle: list[int],
    num_tiles: int,
) -> JsonDict:
    passed_rows = [
        row
        for row in replay_rows
        if (row.get("rtl_sim") or {}).get("status") == "ok"
        and (row.get("rtl_sim") or {}).get("observed", {}).get("token")
        == (row.get("rtl_sim") or {}).get("expected", {}).get("token")
        and (row.get("rtl_sim") or {}).get("observed", {}).get("logit")
        == (row.get("rtl_sim") or {}).get("expected", {}).get("logit")
    ]
    throughput_safe = [
        row
        for row in replay_rows
        if row.get("expected_throughput_ok") and (row.get("rtl_sim") or {}).get("observed", {}).get("tb_backpressure") == 0
    ]
    lowest_power = (
        (service_compatibility or {}).get("recommendation", {}).get("lowest_power_feasible")
        if isinstance(service_compatibility, dict)
        else None
    )
    return {
        "version": 0.1,
        "model": "decoder_serial_ranker_producer_replay_v1",
        "target": {
            "producer_lanes": 64,
            "top_k": 1,
            "lanes_per_cycle": lanes_per_cycle,
            "producer_ii_cycles": producer_ii_cycles,
            "num_tiles": num_tiles,
            "serial_ranker_model": serial_ranker.get("model"),
            "service_compatibility_model": (
                service_compatibility.get("model") if isinstance(service_compatibility, dict) else None
            ),
        },
        "service_compatibility_lowest_power_feasible": lowest_power,
        "replay_rows": replay_rows,
        "decision": {
            "decision": (
                "producer_cadence_replay_passed"
                if len(passed_rows) == len(replay_rows) and replay_rows
                else "producer_cadence_replay_blocked"
            ),
            "throughput_safe_rows": len(throughput_safe),
            "total_rows": len(replay_rows),
            "next_step": (
                "Promote serial_lpc1 into a producer-coupled RTL wrapper if the chosen producer cadence "
                "matches the output-projection service model; keep lpc2/lpc4 as guard points for faster "
                "resident-weight producer assumptions."
                if len(passed_rows) == len(replay_rows) and replay_rows
                else "Fix replay RTL failures before promoting a serial ranker into producer-coupled RTL."
            ),
        },
        "assumptions": [
            "The replay uses the same generated serial-ranker RTL wrappers measured in the architecture sweep.",
            "Producer tiles are released at fixed issue intervals; if the ranker is busy, the testbench holds valid and counts backpressure.",
            "The RTL output is checked against a full-token top-1 reference with deterministic lower-token tie-break.",
            "This validates stream behavior and cadence tolerance; it is not a new physical PPA measurement.",
        ],
    }


def write_markdown(path: Path, payload: JsonDict) -> None:
    lines = [
        "# Decoder Serial Ranker Producer Replay",
        "",
        f"- model: `{payload['model']}`",
        f"- decision: `{payload['decision']['decision']}`",
        f"- throughput_safe_rows: `{payload['decision']['throughput_safe_rows']}/{payload['decision']['total_rows']}`",
        f"- next_step: {payload['decision']['next_step']}",
        "",
        "## Replay Rows",
        "",
        "| lpc | scenario | producer II | service | expected ok | rtl | token | logit | backpressure | final cycle |",
        "|---:|---|---:|---:|---|---|---:|---:|---:|---:|",
    ]
    for row in payload["replay_rows"]:
        sim = row.get("rtl_sim") or {}
        observed = sim.get("observed") if isinstance(sim.get("observed"), dict) else {}
        lines.append(
            "| {lpc} | {scenario} | {ii} | {service} | `{ok}` | `{rtl}` | {token} | {logit} | {bp} | {cycle} |".format(
                lpc=row.get("lanes_per_cycle"),
                scenario=row.get("scenario"),
                ii=row.get("producer_ii_cycles"),
                service=row.get("ranker_service_cycles"),
                ok=row.get("expected_throughput_ok"),
                rtl=sim.get("status"),
                token=observed.get("token", ""),
                logit=observed.get("logit", ""),
                bp=observed.get("tb_backpressure", ""),
                cycle=observed.get("final_cycle", ""),
            )
        )
    lines.extend(["", "## Assumptions", ""])
    for item in payload["assumptions"]:
        lines.append(f"- {item}")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="Replay producer cadence through serial ranker RTL wrappers")
    ap.add_argument("--serial-ranker", required=True)
    ap.add_argument("--service-compatibility")
    ap.add_argument("--merge-config", required=True)
    ap.add_argument("--rtlgen-binary", default="build/rtlgen")
    ap.add_argument("--lanes-per-cycle", default="1,2,4")
    ap.add_argument("--producer-ii-cycles", default="16,33,65,384")
    ap.add_argument("--num-tiles", type=int, default=6)
    ap.add_argument("--logit-bits", type=int, default=16)
    ap.add_argument("--token-id-bits", type=int, default=16)
    ap.add_argument("--out", required=True)
    ap.add_argument("--out-md", required=True)
    args = ap.parse_args()

    serial_ranker = _load_json(args.serial_ranker)
    service_compatibility = _load_json(args.service_compatibility) if args.service_compatibility else None
    rtlgen_binary = _resolve_executable(args.rtlgen_binary)
    variants = _variant_by_lanes(serial_ranker)
    lane_counts = [int(x) for x in args.lanes_per_cycle.split(",") if x.strip()]
    producer_iis = [int(x) for x in args.producer_ii_cycles.split(",") if x.strip()]
    replay_rows: list[JsonDict] = []
    for lanes in lane_counts:
        variant = variants.get(lanes)
        if variant is None:
            replay_rows.append(
                {
                    "lanes_per_cycle": lanes,
                    "status": "variant_missing",
                    "rtl_sim": {"status": "variant_missing"},
                }
            )
            continue
        service = _service_cycles(variant)
        for producer_ii in producer_iis:
            scenario = f"ii{producer_ii}"
            row: JsonDict = {
                "lanes_per_cycle": lanes,
                "scenario": scenario,
                "producer_ii_cycles": producer_ii,
                "ranker_service_cycles": service,
                "expected_throughput_ok": service <= producer_ii,
            }
            row["rtl_sim"] = _simulate_variant(
                variant=variant,
                scenario=scenario,
                producer_ii_cycles=producer_ii,
                num_tiles=args.num_tiles,
                merge_config=Path(args.merge_config),
                rtlgen_binary=rtlgen_binary,
                producer_lanes=64,
                logit_bits=args.logit_bits,
                token_id_bits=args.token_id_bits,
            )
            replay_rows.append(row)

    payload = build_report(
        serial_ranker=serial_ranker,
        service_compatibility=service_compatibility,
        replay_rows=replay_rows,
        producer_ii_cycles=producer_iis,
        lanes_per_cycle=lane_counts,
        num_tiles=args.num_tiles,
    )
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
