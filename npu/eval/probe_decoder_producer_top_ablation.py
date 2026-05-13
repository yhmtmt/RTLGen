#!/usr/bin/env python3
"""Bounded npu_top ablation probe for decoder output-projection producer synth."""

from __future__ import annotations

import argparse
import copy
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT_FOR_IMPORT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT_FOR_IMPORT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT_FOR_IMPORT))

from npu.eval.probe_decoder_producer_synth_boundary import (
    REPO_ROOT,
    ensure_rtlgen_binaries,
    latest_metrics_row,
    load_json,
    rel,
    run_logged,
)


VARIANTS: list[dict[str, Any]] = [
    {
        "name": "full_reference",
        "top": "npu_top",
        "description": "Full nm2 producer top as generated today.",
        "updates": {},
    },
    {
        "name": "no_axi_lite_wrapper",
        "top": "npu_top",
        "description": "Remove the unused AXI-Lite wrapper files while keeping npu_top interfaces.",
        "updates": {"enable_axi_lite_wrapper": False},
    },
    {
        "name": "no_sram_instances",
        "top": "npu_top",
        "description": "Remove generated SRAM side models and SRAM map entries.",
        "updates": {"sram_instances": []},
    },
    {
        "name": "no_axi_ports",
        "top": "npu_top",
        "description": "Remove AXI4 memory-interface ports and AXI DMA FSM logic from npu_top.",
        "updates": {"enable_axi_ports": False, "enable_axi_lite_wrapper": False},
    },
    {
        "name": "no_cq_mem_ports",
        "top": "npu_top",
        "description": "Remove command-queue memory fetch ports and descriptor decode/issue logic.",
        "updates": {"enable_cq_mem_ports": False},
    },
    {
        "name": "external_ports_off",
        "top": "npu_top",
        "description": "Keep compute state inside npu_top but remove CQ memory, DMA, AXI, AXI-Lite, and SRAM side features.",
        "updates": {
            "enable_dma_ports": False,
            "enable_cq_mem_ports": False,
            "enable_axi_ports": False,
            "enable_axi_lite_wrapper": False,
            "sram_instances": [],
        },
    },
    {
        "name": "axi_lite_wrapper_top",
        "top": "npu_top_axi",
        "description": "Synthesize the generated AXI-Lite wrapper top instead of npu_top.",
        "updates": {"enable_axi_lite_wrapper": True},
    },
]


def apply_updates(config: dict[str, Any], updates: dict[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(config)
    for key, value in updates.items():
        out[key] = value
    return out


def write_variant_config(base_config_path: Path, variant: dict[str, Any], out_root: Path) -> Path:
    base = load_json(base_config_path)
    config = apply_updates(base, variant.get("updates", {}))
    config["top_name"] = "npu_top"
    variant_dir = out_root / f"npu_fp16_cpp_nm2_top_ablate_{variant['name']}"
    variant_dir.mkdir(parents=True, exist_ok=True)
    config_path = variant_dir / "config.json"
    config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    return config_path


def _width_of_decl(decl: str) -> int:
    match = re.search(r"\[(\d+)\s*:\s*(\d+)\]", decl)
    if not match:
        return 1
    hi = int(match.group(1))
    lo = int(match.group(2))
    return abs(hi - lo) + 1


def _module_body(text: str, module_name: str) -> str:
    match = re.search(rf"\bmodule\s+{re.escape(module_name)}\b(?P<body>.*?)(?=\nendmodule\b)", text, re.S)
    if not match:
        return ""
    return match.group("body")


def static_verilog_stats(verilog_dir: Path, top: str) -> dict[str, Any]:
    files = sorted(verilog_dir.glob("*.v"))
    text_by_file = {path.name: path.read_text(encoding="utf-8", errors="ignore") for path in files}
    all_text = "\n".join(text_by_file.values())
    top_body = _module_body(all_text, top)
    decls = re.findall(r"\b(?:input|output|inout)\b[^;,\n]*(?:[,;]|\n)", top_body)
    reg_decls = re.findall(r"\breg\b[^;]*;", all_text)
    wire_decls = re.findall(r"\bwire\b[^;]*;", all_text)
    return {
        "verilog_file_count": len(files),
        "verilog_bytes": sum(path.stat().st_size for path in files),
        "verilog_lines": sum(text.count("\n") + 1 for text in text_by_file.values()),
        "module_count": len(re.findall(r"^\s*module\s+", all_text, re.M)),
        "top_found": bool(top_body),
        "top_port_decl_count_est": len(decls),
        "reg_decl_count": len(reg_decls),
        "reg_bit_count_est": sum(_width_of_decl(decl) for decl in reg_decls),
        "wire_decl_count": len(wire_decls),
        "wire_bit_count_est": sum(_width_of_decl(decl) for decl in wire_decls),
        "always_count": len(re.findall(r"\balways\b", all_text)),
        "assign_count": len(re.findall(r"\bassign\b", all_text)),
        "case_count": len(re.findall(r"\bcase\s*\(", all_text)),
        "ternary_count": all_text.count("?"),
        "multiply_operator_count": all_text.count("*"),
        "divide_operator_count": all_text.count("/"),
        "files": [
            {
                "path": rel(path),
                "bytes": path.stat().st_size,
                "lines": text_by_file[path.name].count("\n") + 1,
            }
            for path in files
        ],
    }


def probe_variant(
    config_path: Path,
    *,
    variant: dict[str, Any],
    sweep: Path,
    platform: str,
    make_target: str,
    out_root: Path,
    timeout_seconds: int,
    stall_timeout_seconds: int,
    log_dir: Path,
) -> dict[str, Any]:
    design_dir = config_path.parent
    verilog_dir = design_dir / "verilog"
    top = str(variant["top"])
    gen_result = run_logged(
        [
            sys.executable,
            "npu/rtlgen/gen.py",
            "--config",
            rel(config_path),
            "--out",
            rel(verilog_dir),
        ],
        cwd=REPO_ROOT,
        log_path=log_dir / f"{variant['name']}_rtlgen.log",
        timeout_seconds=max(300, min(timeout_seconds, 900)),
        stall_timeout_seconds=max(120, min(stall_timeout_seconds, 300)),
    )
    row: dict[str, Any] = {
        "variant": variant["name"],
        "description": variant["description"],
        "top": top,
        "config": rel(config_path),
        "design_dir": rel(design_dir),
        "updates": variant.get("updates", {}),
        "rtlgen": gen_result,
        "static_verilog_stats": None,
        "synthesis": None,
        "metrics_row": None,
    }
    if gen_result["status"] != "ok":
        row["status"] = f"rtlgen_{gen_result['status']}"
        return row

    row["static_verilog_stats"] = static_verilog_stats(verilog_dir, top)
    synth_result = run_logged(
        [
            sys.executable,
            "npu/synth/run_block_sweep.py",
            "--design_dir",
            rel(design_dir),
            "--platform",
            platform,
            "--top",
            top,
            "--sweep",
            rel(sweep),
            "--make_target",
            make_target,
            "--out_root",
            rel(out_root),
            "--force_copy",
        ],
        cwd=REPO_ROOT,
        log_path=log_dir / f"{variant['name']}_{top}_{make_target}.log",
        timeout_seconds=timeout_seconds,
        stall_timeout_seconds=stall_timeout_seconds,
    )
    row["synthesis"] = synth_result
    metrics_row = latest_metrics_row(out_root / design_dir.name)
    if metrics_row is not None:
        row["metrics_row"] = metrics_row
    if synth_result["status"] != "ok":
        row["status"] = synth_result["status"]
    elif metrics_row and str(metrics_row.get("status", "")).strip():
        row["status"] = str(metrics_row.get("status"))
    else:
        row["status"] = "ok"
    return row


def build_top_ablation_diagnosis(rows: list[dict[str, Any]]) -> dict[str, Any]:
    full = next((row for row in rows if row.get("variant") == "full_reference"), None)
    ok = [row for row in rows if row.get("status") == "ok"]
    bad = [row for row in rows if row.get("status") != "ok"]
    first_bad = bad[0]["variant"] if bad else None
    if full and full.get("status") == "ok":
        decision = "producer_top_reference_synth_ok"
        next_step = "Retry larger whole npu_top or full-PnR points with bounded staging."
    elif ok:
        decision = "producer_top_culprit_bracketed"
        next_step = "Compare the last passing ablation against the full reference to isolate the added top-level feature."
    else:
        decision = "producer_top_all_variants_nonviable"
        next_step = "Inspect RTL generation and Yosys logs before adding more architecture variants."
    return {
        "decision": decision,
        "ok_variants": [row.get("variant") for row in ok],
        "non_ok_variants": [row.get("variant") for row in bad],
        "first_non_ok_variant": first_bad,
        "recommended_next_step": next_step,
    }


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# Decoder Producer Top Ablation",
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
    ap.add_argument("--timeout-seconds", type=int, default=1800)
    ap.add_argument("--stall-timeout-seconds", type=int, default=900)
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
    log_root = Path(os.environ.get("RTLGEN_PRODUCER_TOP_ABLATION_LOG_DIR", "/tmp/rtlgen-producer-top-ablation"))
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
        "model": "decoder_output_projection_producer_top_ablation_v1",
        "platform": args.platform,
        "base_config": rel(base_config),
        "make_target": args.make_target,
        "timeout_seconds": args.timeout_seconds,
        "stall_timeout_seconds": args.stall_timeout_seconds,
        "rtlgen_setup": setup,
        "sweep": rel(sweep),
        "probe_rows": rows,
        "diagnosis": build_top_ablation_diagnosis(rows),
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_markdown(out_md, payload)
    return 2 if setup["status"] != "ok" else 0


if __name__ == "__main__":
    raise SystemExit(main())
