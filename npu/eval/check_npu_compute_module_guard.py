#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _repo_rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _expected_num_modules(config: dict[str, Any]) -> int:
    compute = config.get("compute")
    if not isinstance(compute, dict):
        raise ValueError("config missing compute block")
    gemm = compute.get("gemm")
    if not isinstance(gemm, dict):
        raise ValueError("config missing compute.gemm block")
    return int(gemm.get("num_modules", 1))


def _extract_localparam(text: str, name: str) -> int | None:
    pattern = re.compile(rf"\blocalparam\s+integer\s+{re.escape(name)}\s*=\s*(\d+)\s*;")
    match = pattern.search(text)
    if not match:
        return None
    return int(match.group(1))


def _vector_register_count(text: str, prefix: str) -> int:
    pattern = re.compile(rf"\breg\s+\[15:0\]\s+{re.escape(prefix)}(\d+)\s*;")
    indexes = {int(match.group(1)) for match in pattern.finditer(text)}
    if not indexes:
        return 0
    return max(indexes) + 1 if indexes == set(range(max(indexes) + 1)) else len(indexes)


def _writeback_slot_count(text: str) -> int:
    pattern = re.compile(r"\bdma_writeback_data\[15:0\]\s*<=\s*gemm_slot_accum(\d+)\s*;")
    indexes = {int(match.group(1)) for match in pattern.finditer(text)}
    if not indexes:
        return 0
    return max(indexes) + 1 if indexes == set(range(max(indexes) + 1)) else len(indexes)


def _check_config(config_path: Path) -> dict[str, Any]:
    config = _load_json(config_path)
    expected = _expected_num_modules(config)
    with tempfile.TemporaryDirectory() as td:
        out_dir = Path(td) / "rtl"
        subprocess.run(
            [
                sys.executable,
                "npu/rtlgen/gen.py",
                "--config",
                str(config_path),
                "--out",
                str(out_dir),
            ],
            cwd=str(REPO_ROOT),
            check=True,
            capture_output=True,
            text=True,
        )
        top_v = out_dir / "top.v"
        text = top_v.read_text(encoding="utf-8")

    array_modules = _extract_localparam(text, "NUM_MODULES")
    top_modules = _extract_localparam(text, "GEMM_NUM_MODULES")
    a_regs = _vector_register_count(text, "gemm_mac_a_vec")
    b_regs = _vector_register_count(text, "gemm_mac_b_vec")
    writeback_slots = _writeback_slot_count(text)
    has_slot_loop = "begin : g_slot" in text and "u_slot_mac" in text
    ok = (
        array_modules == expected
        and top_modules == expected
        and a_regs == expected
        and b_regs == expected
        and writeback_slots == expected
        and has_slot_loop
    )
    return {
        "config": _repo_rel(config_path),
        "expected_num_modules": expected,
        "rtl_num_modules_localparam": array_modules,
        "top_gemm_num_modules_localparam": top_modules,
        "gemm_mac_a_register_count": a_regs,
        "gemm_mac_b_register_count": b_regs,
        "has_gemm_slot_loop": has_slot_loop,
        "gemm_writeback_slot_count": writeback_slots,
        "status": "ok" if ok else "failed",
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check generated NPU RTL keeps the requested FP16 GEMM module structure."
    )
    parser.add_argument("--configs", nargs="+", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    results = []
    for config_text in args.configs:
        config_path = Path(config_text)
        if not config_path.is_absolute():
            config_path = REPO_ROOT / config_path
        results.append(_check_config(config_path.resolve()))

    payload = {
        "schema": "npu_compute_module_guard_v1",
        "configs_checked": len(results),
        "results": results,
        "status": "ok" if all(row["status"] == "ok" for row in results) else "failed",
    }
    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = REPO_ROOT / out_path
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {out_path}")
    if payload["status"] != "ok":
        print(json.dumps(payload, indent=2, sort_keys=True), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
