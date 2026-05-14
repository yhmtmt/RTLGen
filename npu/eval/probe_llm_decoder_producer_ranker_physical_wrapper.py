#!/usr/bin/env python3
"""Measure a bounded r64/k1 decoder producer-to-ranker physical wrapper."""

from __future__ import annotations

import argparse
import csv
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

try:
    from probe_llm_decoder_producer_ranker_ready_valid_equivalence import (
        _as_int,
        _load_json,
        _module_name,
        _operation_options,
        _reference_top1,
        _resolve_executable,
        _run,
        _write_ready_valid_wrapper,
        _make_tile_values,
    )
except ImportError:  # pragma: no cover - used when imported as a package in tests
    from npu.eval.probe_llm_decoder_producer_ranker_ready_valid_equivalence import (
        _as_int,
        _load_json,
        _module_name,
        _operation_options,
        _reference_top1,
        _resolve_executable,
        _run,
        _write_ready_valid_wrapper,
        _make_tile_values,
    )


JsonDict = dict[str, Any]
REPO_ROOT = Path(__file__).resolve().parents[2]


def _rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _tail(path: Path, limit: int = 40) -> list[str]:
    try:
        return path.read_text(encoding="utf-8", errors="ignore").splitlines()[-limit:]
    except FileNotFoundError:
        return []


def _run_logged(
    cmd: list[str],
    *,
    cwd: Path,
    log_path: Path,
    timeout_seconds: int,
    stall_timeout_seconds: int,
) -> JsonDict:
    start = time.monotonic()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf-8") as log:
        proc = subprocess.Popen(
            cmd,
            cwd=cwd,
            stdout=log,
            stderr=subprocess.STDOUT,
            text=True,
            preexec_fn=os.setsid,
        )
        last_size = -1
        last_activity = time.monotonic()
        timed_out = False
        stalled = False
        while proc.poll() is None:
            now = time.monotonic()
            try:
                size = log_path.stat().st_size
            except FileNotFoundError:
                size = 0
            if size != last_size:
                last_size = size
                last_activity = now
            if timeout_seconds > 0 and now - start >= timeout_seconds:
                timed_out = True
                break
            if stall_timeout_seconds > 0 and now - last_activity >= stall_timeout_seconds:
                stalled = True
                break
            time.sleep(2.0)
        if timed_out or stalled:
            try:
                os.killpg(proc.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                proc.wait(timeout=20)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                proc.wait()
    if timed_out:
        status = "timeout"
    elif stalled:
        status = "stall_timeout"
    elif proc.returncode == 0:
        status = "ok"
    else:
        status = "failed"
    return {
        "status": status,
        "returncode": proc.returncode,
        "elapsed_seconds": time.monotonic() - start,
        "command": " ".join(cmd),
        "log_path": _rel(log_path),
        "log_tail": _tail(log_path),
    }


def _latest_metrics_row(metrics_path: Path) -> JsonDict | None:
    if not metrics_path.exists():
        return None
    with metrics_path.open(encoding="utf-8", newline="") as f:
        rows = [dict(row) for row in csv.DictReader(f)]
    return rows[-1] if rows else None


def _portable_metrics_row(row: JsonDict | None) -> JsonDict | None:
    if row is None:
        return None
    portable = dict(row)
    for key in ("result_path", "work_result_json", "synth_script_path"):
        value = str(portable.get(key, "") or "")
        if not value:
            continue
        path = Path(value)
        if path.is_absolute():
            try:
                portable[key] = str(path.resolve().relative_to(REPO_ROOT))
            except ValueError:
                portable[key] = ""
    return portable


def materialize_wrapper(
    *,
    rtlgen_binary: str,
    logit_rank_config: Path,
    merge_config: Path,
    design_dir: Path,
    top: str,
) -> JsonDict:
    verilog_dir = design_dir / "verilog"
    verilog_dir.mkdir(parents=True, exist_ok=True)
    for old in verilog_dir.glob("*.v"):
        old.unlink()

    rank_config = _load_json(logit_rank_config)
    merge_config_json = _load_json(merge_config)
    rank_opts = _operation_options(rank_config)
    merge_opts = _operation_options(merge_config_json)
    rank_module = _module_name(rank_config)
    merge_module = _module_name(merge_config_json)
    producer_lanes = _as_int(rank_opts.get("row_elems"))
    logit_bits = _as_int(rank_opts.get("logit_bits"))
    token_id_bits = _as_int(merge_opts.get("token_id_bits"))
    top_k = _as_int(rank_opts.get("top_k"))

    rank_cmd = _run([rtlgen_binary, str(logit_rank_config.resolve())], cwd=verilog_dir)
    merge_cmd = _run([rtlgen_binary, str(merge_config.resolve())], cwd=verilog_dir)
    wrapper = verilog_dir / f"{top}.v"
    if rank_cmd.returncode == 0 and merge_cmd.returncode == 0:
        _write_ready_valid_wrapper(
            wrapper,
            wrapper_name=top,
            rank_module=rank_module,
            merge_module=merge_module,
            producer_lanes=producer_lanes,
            logit_bits=logit_bits,
            token_id_bits=token_id_bits,
            top_k=top_k,
        )

    config_manifest = {
        "version": 0.1,
        "design": top,
        "top": top,
        "logit_rank_config": _rel(logit_rank_config),
        "merge_config": _rel(merge_config),
        "producer_lanes": producer_lanes,
        "top_k": top_k,
        "logit_bits": logit_bits,
        "token_id_bits": token_id_bits,
        "stream_contract": "LogitTileStream to CandidateStream ready-valid wrapper",
        "rtlgen_binary": rtlgen_binary,
    }
    design_dir.mkdir(parents=True, exist_ok=True)
    (design_dir / "config_decoder_r64_k1_producer_ranker_physical_wrapper.json").write_text(
        json.dumps(config_manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return {
        "status": "ok" if rank_cmd.returncode == 0 and merge_cmd.returncode == 0 else "rtlgen_failed",
        "design_dir": _rel(design_dir),
        "verilog_dir": _rel(verilog_dir),
        "top": top,
        "rank_module": rank_module,
        "merge_module": merge_module,
        "rank_returncode": rank_cmd.returncode,
        "merge_returncode": merge_cmd.returncode,
        "rank_log_tail": rank_cmd.stdout.splitlines()[-20:],
        "merge_log_tail": merge_cmd.stdout.splitlines()[-20:],
        "generated_verilog": sorted(_rel(path) for path in verilog_dir.glob("*.v")),
        "config_manifest": _rel(design_dir / "config_decoder_r64_k1_producer_ranker_physical_wrapper.json"),
        "target": {
            "producer_lanes": producer_lanes,
            "top_k": top_k,
            "logit_bits": logit_bits,
            "token_id_bits": token_id_bits,
        },
    }


def build_report(
    *,
    ready_valid_equivalence: JsonDict | None,
    materialization: JsonDict,
    synthesis: JsonDict | None,
    metrics_row: JsonDict | None,
    sweep: str,
    make_target: str,
) -> JsonDict:
    tiles = _make_tile_values()
    reference = _reference_top1(
        tiles,
        producer_lanes=_as_int(materialization.get("target", {}).get("producer_lanes")),
    )
    metrics_status = str((metrics_row or {}).get("status", "") or "")
    synthesis_status = str((synthesis or {}).get("status", "") or "")
    measured = metrics_status == "ok"
    equivalence_decision = (
        (ready_valid_equivalence or {}).get("decision", {}).get("decision")
        if isinstance(ready_valid_equivalence, dict)
        else None
    )
    checks = [
        {
            "name": "ready_valid_equivalence_predecessor_passed",
            "passed": equivalence_decision == "ready_valid_equivalence_passed",
            "observed": equivalence_decision,
        },
        {
            "name": "physical_wrapper_rtl_materialized",
            "passed": materialization.get("status") == "ok",
            "observed": materialization.get("generated_verilog", []),
        },
        {
            "name": "physical_sweep_completed_with_metrics",
            "passed": measured,
            "observed": {"synthesis_status": synthesis_status, "metrics_status": metrics_status},
        },
    ]
    decision = "producer_ranker_physical_wrapper_measured" if all(c["passed"] for c in checks) else "producer_ranker_physical_wrapper_blocked"
    return {
        "version": 0.1,
        "model": "decoder_producer_ranker_physical_wrapper_v1",
        "target": {
            "name": "r64_k1_nm16_ready_valid_physical_wrapper",
            **materialization.get("target", {}),
            "make_target": make_target,
            "sweep": sweep,
        },
        "reference": {
            "deterministic_tile_count": len(tiles),
            "full_vocab_top1": reference,
            "source_equivalence_decision": equivalence_decision,
        },
        "materialization": materialization,
        "synthesis": synthesis,
        "metrics_row": metrics_row,
        "checks": checks,
        "decision": {
            "decision": decision,
            "next_step": (
                "Use this wrapper PPA as the first measured producer-ranker integration point and then compare r128 or producer-coupled variants."
                if decision.endswith("_measured")
                else "Fix wrapper materialization, tool setup, or floorplan constraints before scaling producer-ranker integration."
            ),
        },
        "assumptions": [
            "The wrapper measures ranker plus candidate-merge ready-valid logic, not the full output-projection GEMM.",
            "The deterministic stream reference remains token/logit exact with lower-token tie order from the predecessor equivalence run.",
            "The top-level physical wrapper is a bounded macro diagnostic; padded die area and IO pin pressure must be interpreted separately from connected producer placement.",
        ],
    }


def write_markdown(path: Path, payload: JsonDict) -> None:
    lines = [
        "# Decoder Producer/Ranker Physical Wrapper",
        "",
        f"- model: `{payload['model']}`",
        f"- target: `{payload['target']['name']}`",
        f"- decision: `{payload['decision']['decision']}`",
        f"- next_step: {payload['decision']['next_step']}",
        "",
        "## Checks",
        "",
        "| check | passed | observed |",
        "|---|---|---|",
    ]
    for check in payload["checks"]:
        lines.append(f"| {check['name']} | `{check['passed']}` | `{check.get('observed')}` |")
    metrics = payload.get("metrics_row") or {}
    lines.extend(
        [
            "",
            "## Metrics",
            "",
            f"- status: `{metrics.get('status')}`",
            f"- critical_path_ns: `{metrics.get('critical_path_ns')}`",
            f"- die_area: `{metrics.get('die_area')}`",
            f"- total_power_mw: `{metrics.get('total_power_mw')}`",
            f"- result_path: `{metrics.get('result_path')}`",
        ]
    )
    synthesis = payload.get("synthesis") or {}
    lines.extend(["", "## Synthesis", "", f"- status: `{synthesis.get('status')}`"])
    if synthesis.get("log_path"):
        lines.append(f"- log_path: `{synthesis.get('log_path')}`")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="Probe r64/k1 producer-ranker physical wrapper")
    ap.add_argument("--logit-rank-config", required=True)
    ap.add_argument("--merge-config", required=True)
    ap.add_argument("--ready-valid-equivalence")
    ap.add_argument("--rtlgen-binary", default="build/rtlgen")
    ap.add_argument("--design-dir", required=True)
    ap.add_argument("--top", default="decoder_r64_k1_producer_ranker_physical_wrapper")
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
    design_dir = (REPO_ROOT / args.design_dir).resolve() if not Path(args.design_dir).is_absolute() else Path(args.design_dir)
    log_dir = REPO_ROOT / "control_plane" / "runtime_logs" / "decoder_producer_ranker_physical_wrapper"
    ready_valid = _load_json(args.ready_valid_equivalence) if args.ready_valid_equivalence else None

    if rtlgen_binary is None:
        materialization = {
            "status": "rtlgen_binary_missing",
            "requested": args.rtlgen_binary,
            "rtlgen_binary_env": os.environ.get("RTLGEN_BINARY"),
            "design_dir": _rel(design_dir),
            "target": {},
        }
        synthesis = None
        metrics_row = None
    else:
        materialization = materialize_wrapper(
            rtlgen_binary=rtlgen_binary,
            logit_rank_config=Path(args.logit_rank_config),
            merge_config=Path(args.merge_config),
            design_dir=design_dir,
            top=args.top,
        )
        synthesis = None
        metrics_row = None
        if materialization.get("status") == "ok" and not args.skip_physical:
            synth_cmd = [
                sys.executable,
                "npu/synth/run_block_sweep.py",
                "--design_dir",
                _rel(design_dir),
                "--platform",
                args.platform,
                "--top",
                args.top,
                "--sweep",
                args.sweep,
                "--make_target",
                args.make_target,
                "--out_root",
                _rel(design_dir.parent),
                "--force_copy",
            ]
            synthesis = _run_logged(
                synth_cmd,
                cwd=REPO_ROOT,
                log_path=log_dir / f"{args.top}_{args.make_target}.log",
                timeout_seconds=args.timeout_seconds,
                stall_timeout_seconds=args.stall_timeout_seconds,
            )
            metrics_row = _portable_metrics_row(_latest_metrics_row(design_dir / "metrics.csv"))

    payload = build_report(
        ready_valid_equivalence=ready_valid,
        materialization=materialization,
        synthesis=synthesis,
        metrics_row=metrics_row,
        sweep=args.sweep,
        make_target=args.make_target,
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
