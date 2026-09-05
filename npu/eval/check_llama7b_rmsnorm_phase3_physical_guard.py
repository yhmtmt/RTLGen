#!/usr/bin/env python3
"""Guard checked Llama7B RMSNorm Phase-3 physical harness artifacts."""

from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.rtlgen.gen_llama7b_rmsnorm import generate

_REGISTER_PROPOSAL_ID = "prop_l1_decoder_llama7b_rmsnorm_phase3_bounded_physical_v1"
_MACRO_PROPOSAL_ID = "prop_l1_decoder_llama7b_rmsnorm_phase3_macro_banked_physical_v1"


def _json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit(f"expected JSON object: {path}")
    return payload


def _require(value: object, expected: object, label: str) -> None:
    if value != expected:
        raise SystemExit(f"{label}: expected {expected!r}, got {value!r}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--design-dir", type=Path, required=True)
    args = parser.parse_args(argv)

    design_dir = args.design_dir.resolve()
    config_path = design_dir / "config.json"
    rtl_dir = design_dir / "verilog"
    rtl_config_path = rtl_dir / "config.json"
    rtl_path = rtl_dir / "top.v"
    for path in (config_path, rtl_config_path, rtl_path):
        if not path.is_file():
            raise SystemExit(f"missing checked artifact: {path}")

    config = _json(config_path)
    generated_config = _json(rtl_config_path)
    _require(generated_config, config, "generated config")

    top_name = str(config.get("top_name") or "").strip()
    if not top_name:
        raise SystemExit("config top_name must not be empty")
    body = config.get("llama7b_rmsnorm")
    if not isinstance(body, dict):
        raise SystemExit("config must contain llama7b_rmsnorm object")
    _require(int(body.get("lanes", 0)), 16, "lane count")
    storage_backend = str(body.get("storage_backend", "register_arrays"))
    macro_backed = storage_backend.startswith("fakeram45_64x32_banked")
    if storage_backend not in {
        "register_arrays",
        "fakeram45_64x32_banked",
        "fakeram45_64x32_banked_pipelined",
    }:
        raise SystemExit(f"unsupported storage backend: {storage_backend}")

    links = config.get("report_links")
    if not isinstance(links, dict):
        raise SystemExit("config requires report_links")
    _require(
        links.get("proposal_id"),
        _MACRO_PROPOSAL_ID if macro_backed else _REGISTER_PROPOSAL_ID,
        "config proposal linkage",
    )

    with tempfile.TemporaryDirectory(prefix="llama7b-rmsnorm-phase3-guard-") as name:
        regenerated = Path(name)
        generate(config, regenerated)
        generated_files = ["top.v", "config.json"]
        if macro_backed:
            generated_files.extend(
                [
                    "llama7b_rmsnorm_banked_row_gamma_store.v",
                    "fakeram45_64x32_blackbox.v",
                    "macro_manifest.json",
                ]
            )
        for filename in generated_files:
            if (regenerated / filename).read_text(encoding="utf-8") != (
                rtl_dir / filename
            ).read_text(encoding="utf-8"):
                raise SystemExit(f"checked artifact differs from generator output: {filename}")

    rtl = rtl_path.read_text(encoding="utf-8")
    if not re.search(rf"^\s*module\s+{re.escape(top_name)}\b", rtl, re.MULTILINE):
        raise SystemExit(f"generated RTL does not define top module {top_name}")

    required_tokens = [
        "input  wire [255:0] in_row",
        "input  wire [255:0] in_gamma",
        "output wire [255:0] out_row",
        "output wire                         out_protocol_error",
        "output reg  [31:0]                  accepted_row_count",
        "output reg  [31:0]                  completed_row_count",
        "localparam integer LANES = 16;",
        "localparam integer HIDDEN_SIZE = 4096;",
        "localparam integer BEATS = 256;",
        "seed_rom = 21'h",
    ]
    if macro_backed:
        required_tokens.append("llama7b_rmsnorm_banked_row_gamma_store u_row_gamma_store")
        if storage_backend == "fakeram45_64x32_banked_pipelined":
            required_tokens.extend(
                [
                    "reg [BEAT_W:0] store_issue_count",
                    "reg [2:0] store_reads_inflight",
                    "wire [2:0] arithmetic_occupancy",
                    "{2'b0, s0_valid} + {2'b0, s1_valid} + {2'b0, s2_valid}",
                    "arithmetic_occupancy + store_reads_inflight < 3",
                ]
            )
        else:
            required_tokens.append("reg store_read_pending")
        forbidden_tokens = [
            "reg [15:0] row_mem [0:HIDDEN_SIZE-1];",
            "reg [15:0] gamma_mem [0:HIDDEN_SIZE-1];",
        ]
        manifest = _json(rtl_dir / "llama7b_rmsnorm_manifest.json")
        _require(manifest.get("macro_inventory"), {"fakeram45_64x32": 64}, "macro inventory")
        _require(manifest.get("storage_read_latency_cycles"), 2, "storage read latency")
        macro_manifest = _json(rtl_dir / "macro_manifest.json")
        _require(macro_manifest.get("blackboxes"), ["fakeram45_64x32"], "macro blackboxes")
        params = macro_manifest.get("manifest_params")
        if not isinstance(params, dict):
            raise SystemExit("macro manifest_params must be an object")
        _require(params.get("macro_count"), 64, "macro count")
    else:
        required_tokens.extend(
            [
                "reg [15:0] row_mem [0:HIDDEN_SIZE-1];",
                "reg [15:0] gamma_mem [0:HIDDEN_SIZE-1];",
            ]
        )
        forbidden_tokens = [
            "fakeram45_",
            "sky130_sram_",
            "sram ",
            "macro_manifest",
            "blackbox",
        ]
    for token in required_tokens:
        if token not in rtl:
            raise SystemExit(f"generated RTL missing expected token: {token}")
    for token in forbidden_tokens:
        if token in rtl:
            raise SystemExit(f"generated RTL must not imply SRAM-backed measurement evidence: {token}")

    print(f"OK: llama7b rmsnorm phase3 physical guard passed for {design_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
