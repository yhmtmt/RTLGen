#!/usr/bin/env python3
"""Bounded command-queue path ablation probe for decoder producer synth."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT_FOR_IMPORT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT_FOR_IMPORT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT_FOR_IMPORT))

from npu.eval.probe_decoder_producer_top_ablation import (  # noqa: E402
    REPO_ROOT,
    ensure_rtlgen_binaries,
    probe_variant,
    rel,
    write_variant_config,
)


VARIANTS: list[dict[str, Any]] = [
    {
        "name": "no_cq_mem_ports",
        "top": "npu_top",
        "description": "Known-passing anchor with CQ memory fetch and descriptor decode removed.",
        "updates": {"enable_cq_mem_ports": False},
    },
    {
        "name": "cq_fetch_only",
        "top": "npu_top",
        "description": "CQ memory port, address generation, one-word fetch, and descriptor retirement only.",
        "updates": {"cq_mem_ablation_mode": "fetch_only"},
    },
    {
        "name": "cq_v1_header_only",
        "top": "npu_top",
        "description": "CQ v0.1 header field capture without opcode issue logic.",
        "updates": {"cq_mem_ablation_mode": "v1_header_only"},
    },
    {
        "name": "cq_v1_dma_only",
        "top": "npu_top",
        "description": "CQ v0.1 DMA_COPY decode plus DMA request bookkeeping only.",
        "updates": {"cq_mem_ablation_mode": "v1_dma_only"},
    },
    {
        "name": "cq_v1_gemm_only",
        "top": "npu_top",
        "description": "CQ v0.1 GEMM opcode decode and GEMM slot issue chain only.",
        "updates": {"cq_mem_ablation_mode": "v1_gemm_only"},
    },
    {
        "name": "cq_v2_gemm_only",
        "top": "npu_top",
        "description": "CQ v0.2 extension fetch and GEMM slot issue chain only.",
        "updates": {"cq_mem_ablation_mode": "v2_gemm_only"},
    },
    {
        "name": "cq_v1_vec_only",
        "top": "npu_top",
        "description": "CQ v0.1 VEC_OP dtype/op validation and issue path only.",
        "updates": {"cq_mem_ablation_mode": "v1_vec_only"},
    },
    {
        "name": "cq_v1_softmax_event_only",
        "top": "npu_top",
        "description": "CQ v0.1 SOFTMAX and EVENT_SIGNAL/EVENT_WAIT paths only.",
        "updates": {"cq_mem_ablation_mode": "v1_softmax_event_only"},
    },
    {
        "name": "full_reference_guard",
        "top": "npu_top",
        "description": "Full CQ decode/issue reference, included as a bounded timeout guard.",
        "updates": {},
    },
]


def build_cq_ablation_diagnosis(rows: list[dict[str, Any]]) -> dict[str, Any]:
    ok = [row for row in rows if row.get("status") == "ok"]
    bad = [row for row in rows if row.get("status") != "ok"]
    first_bad = bad[0]["variant"] if bad else None
    full = next((row for row in rows if row.get("variant") == "full_reference_guard"), None)
    if full and full.get("status") == "ok":
        decision = "cq_reference_synth_ok_under_guard"
        next_step = "Use the full-reference metrics as an updated boundary before changing RTL."
    elif first_bad:
        decision = "cq_subpath_culprit_bracketed"
        next_step = (
            "Compare the first non-OK CQ subpath against the preceding OK subpath and "
            "stage or preserve hierarchy around that decode/issue expression."
        )
    else:
        decision = "cq_subpaths_individually_viable"
        next_step = (
            "Probe pairwise combinations of the individually viable CQ subpaths to isolate "
            "the interaction that triggers Yosys expansion."
        )
    return {
        "decision": decision,
        "ok_variants": [row.get("variant") for row in ok],
        "non_ok_variants": [row.get("variant") for row in bad],
        "first_non_ok_variant": first_bad,
        "recommended_next_step": next_step,
    }


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# Decoder Producer CQ Ablation",
        "",
        f"- base_config: `{payload['base_config']}`",
        f"- make_target: `{payload['make_target']}`",
        f"- timeout_seconds: `{payload['timeout_seconds']}`",
        f"- stall_timeout_seconds: `{payload['stall_timeout_seconds']}`",
        "",
        "| variant | top | status | elapsed_s | verilog_kb | reg_bits_est | wire_bits_est | log |",
        "|---|---|---|---:|---:|---:|---:|---|",
    ]
    for row in payload["probe_rows"]:
        synth = row.get("synthesis") or {}
        stats = row.get("static_verilog_stats") or {}
        elapsed = synth.get("elapsed_seconds")
        elapsed_text = f"{float(elapsed):.1f}" if elapsed is not None else ""
        lines.append(
            "| {variant} | {top} | {status} | {elapsed} | {kb:.1f} | {reg_bits} | {wire_bits} | {log} |".format(
                variant=row.get("variant"),
                top=row.get("top"),
                status=row.get("status"),
                elapsed=elapsed_text,
                kb=float(stats.get("verilog_bytes") or 0) / 1024.0,
                reg_bits=stats.get("reg_bit_count_est", ""),
                wire_bits=stats.get("wire_bit_count_est", ""),
                log=synth.get("log_path", ""),
            )
        )
    diagnosis = payload["diagnosis"]
    lines.extend(
        [
            "",
            "## Diagnosis",
            "",
            f"- decision: `{diagnosis.get('decision')}`",
            f"- ok_variants: `{diagnosis.get('ok_variants')}`",
            f"- non_ok_variants: `{diagnosis.get('non_ok_variants')}`",
            f"- first_non_ok_variant: `{diagnosis.get('first_non_ok_variant')}`",
            f"- recommended_next_step: {diagnosis.get('recommended_next_step')}",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base-config", required=True)
    ap.add_argument("--sweep", required=True)
    ap.add_argument("--platform", default="nangate45")
    ap.add_argument("--make-target", default="1_2_yosys")
    ap.add_argument("--out-root", default="runs/designs/npu_blocks")
    ap.add_argument("--timeout-seconds", type=int, default=900)
    ap.add_argument("--stall-timeout-seconds", type=int, default=450)
    ap.add_argument("--rtlgen-build-timeout-seconds", type=int, default=900)
    ap.add_argument("--skip-rtlgen-build", action="store_true")
    ap.add_argument("--continue-after-failure", action="store_true")
    ap.add_argument("--out", required=True)
    ap.add_argument("--out-md", required=True)
    args = ap.parse_args()

    base_config = (REPO_ROOT / args.base_config).resolve() if not Path(args.base_config).is_absolute() else Path(args.base_config)
    sweep = (REPO_ROOT / args.sweep).resolve() if not Path(args.sweep).is_absolute() else Path(args.sweep)
    out = (REPO_ROOT / args.out).resolve() if not Path(args.out).is_absolute() else Path(args.out)
    out_md = (REPO_ROOT / args.out_md).resolve() if not Path(args.out_md).is_absolute() else Path(args.out_md)
    out_root = (REPO_ROOT / args.out_root).resolve() if not Path(args.out_root).is_absolute() else Path(args.out_root)
    log_root = Path(os.environ.get("RTLGEN_PRODUCER_CQ_ABLATION_LOG_DIR", "/tmp/rtlgen-producer-cq-ablation"))
    log_dir = log_root / out.stem

    config_paths = [write_variant_config(base_config, variant, out_root) for variant in VARIANTS]
    setup = ensure_rtlgen_binaries(
        config_paths,
        log_dir=log_dir,
        build_timeout_seconds=args.rtlgen_build_timeout_seconds,
        stall_timeout_seconds=max(120, min(args.stall_timeout_seconds, 300)),
        skip_build=args.skip_rtlgen_build,
    )
    rows: list[dict[str, Any]] = []
    if setup["status"] != "ok":
        rows.append({"status": "setup_failed", "variant": "setup", "rtlgen_setup": setup})
    else:
        for variant, config_path in zip(VARIANTS, config_paths):
            row = probe_variant(
                config_path,
                variant=variant,
                sweep=sweep,
                platform=args.platform,
                make_target=args.make_target,
                out_root=out_root,
                timeout_seconds=args.timeout_seconds,
                stall_timeout_seconds=args.stall_timeout_seconds,
                log_dir=log_dir,
            )
            rows.append(row)
            if row.get("status") != "ok" and not args.continue_after_failure:
                break

    payload = {
        "version": 0.1,
        "model": "decoder_output_projection_producer_cq_ablation_v1",
        "platform": args.platform,
        "base_config": rel(base_config),
        "make_target": args.make_target,
        "timeout_seconds": args.timeout_seconds,
        "stall_timeout_seconds": args.stall_timeout_seconds,
        "rtlgen_setup": setup,
        "sweep": rel(sweep),
        "probe_rows": rows,
        "diagnosis": build_cq_ablation_diagnosis(rows),
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_markdown(out_md, payload)
    return 2 if setup["status"] != "ok" else 0


if __name__ == "__main__":
    raise SystemExit(main())
