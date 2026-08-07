#!/usr/bin/env python3
"""Guard checked exact-partial physical-calibration harness artifacts."""

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

from npu.rtlgen.gen_attention_exact_partial_async_fifo_physical_harness import (
    generate as generate_cdc,
)
from npu.rtlgen.gen_attention_score32_exact_partial_temporal_finalizer_physical_harness import (
    generate as generate_temporal_finalizer,
)

_TEMPORAL_KEY = "attention_score32_exact_partial_temporal_finalizer_physical_harness"
_CDC_KEY = "attention_exact_partial_async_fifo_physical_harness"
_PROPOSAL_ID = "prop_l1_decoder_attention_exact_partial_physical_calibration_v1"


def _json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit(f"expected JSON object: {path}")
    return payload


def _top_module(rtl: str, top_name: str) -> str:
    match = re.search(
        rf"module\s+{re.escape(top_name)}\b.*?endmodule",
        rtl,
        flags=re.DOTALL,
    )
    if match is None:
        raise SystemExit(f"generated RTL does not contain top module {top_name}")
    return match.group(0)


def _require(value: object, expected: object, label: str) -> None:
    if value != expected:
        raise SystemExit(f"{label}: expected {expected!r}, got {value!r}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--design-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    design_dir = args.design_dir.resolve()
    config_path = design_dir / "config.json"
    checked_macro_path = design_dir / "macro_manifest.json"
    rtl_dir = design_dir / "verilog"
    for path in (config_path, checked_macro_path, rtl_dir / "top.v", rtl_dir / "config.json"):
        if not path.is_file():
            raise SystemExit(f"missing calibration artifact: {path}")

    config = _json(config_path)
    generated_config = _json(rtl_dir / "config.json")
    _require(generated_config, config, "generated config")
    top_name = str(config.get("top_name") or "").strip()
    if not top_name:
        raise SystemExit("config top_name must not be empty")

    if _TEMPORAL_KEY in config:
        generator = generate_temporal_finalizer
        manifest_name = (
            "attention_score32_exact_partial_temporal_finalizer_"
            "physical_harness_manifest.json"
        )
        kind = "temporal_finalizer"
    elif _CDC_KEY in config:
        generator = generate_cdc
        manifest_name = "attention_exact_partial_async_fifo_physical_harness_manifest.json"
        kind = "cdc"
    else:
        raise SystemExit("unsupported physical calibration config")

    with tempfile.TemporaryDirectory(prefix="exact-partial-physical-guard-") as name:
        regenerated = Path(name)
        generator(config, regenerated)
        for filename in ("top.v", "config.json", "macro_manifest.json", manifest_name):
            if (regenerated / filename).read_text(encoding="utf-8") != (
                rtl_dir / filename
            ).read_text(encoding="utf-8"):
                raise SystemExit(f"checked artifact differs from generator output: {filename}")

    manifest = _json(rtl_dir / manifest_name)
    generated_macro = _json(rtl_dir / "macro_manifest.json")
    checked_macro = _json(checked_macro_path)
    _require(manifest.get("linked_proposal_id"), _PROPOSAL_ID, "proposal linkage")
    _require(manifest.get("whole_dual_clock_common_delay_claim"), False, "timing claim")
    _require(
        generated_macro.get("blackboxes"),
        checked_macro.get("blackboxes"),
        "checked macro blackboxes",
    )
    generated_params = generated_macro.get("manifest_params")
    checked_params = checked_macro.get("manifest_params")
    if not isinstance(generated_params, dict) or not isinstance(checked_params, dict):
        raise SystemExit("macro manifests require manifest_params")

    rtl = (rtl_dir / "top.v").read_text(encoding="utf-8")
    top = _top_module(rtl, top_name)
    port_declarations = top.split(");", 1)[0]
    for forbidden in ("[463:0]", "[393:0]", "[327:0]", "[319:0]"):
        if forbidden in port_declarations:
            raise SystemExit(f"top-level narrow-I/O contract violated by {forbidden}")

    if kind == "temporal_finalizer":
        _require(manifest.get("top_pin_bits"), 388, "temporal top pin count")
        _require(manifest.get("macro_count"), 104, "temporal macro count")
        _require(generated_params.get("macro_count"), 104, "generated macro count")
        _require(checked_params.get("macro_count"), 104, "checked macro count")
        _require(manifest.get("physical_timing_claim"), "single_temporal_clock_domain", "timing claim")
        if "fakeram45_64x32 u_state_mem" not in rtl:
            raise SystemExit("temporal harness must instantiate fakeram45_64x32 state macros")
        for forbidden in (
            "state_global_max_q [0:",
            "state_exp_sum_q [0:",
            "state_value_q [0:",
            "reg [393:0] state",
        ):
            if forbidden in rtl:
                raise SystemExit(f"wide behavioral state array is forbidden: {forbidden}")
    else:
        _require(manifest.get("top_pin_bits"), 292, "CDC top pin count")
        _require(manifest.get("macro_count"), 0, "CDC macro count")
        _require(generated_params.get("macro_count"), 0, "generated CDC macro count")
        _require(
            manifest.get("cross_domain_paths_are_signoff_timing"),
            False,
            "CDC signoff claim",
        )
        if "reg [463:0] mem [0:DEPTH-1];" not in rtl:
            raise SystemExit("CDC harness must contain the real 464-bit depth-4 FIFO")
        if "helper_clk_q <= ~helper_clk_q;" not in top:
            raise SystemExit("CDC inactive domain must use protocol-safe generated clock")

    links = config.get("report_links")
    if not isinstance(links, dict):
        raise SystemExit("config requires report_links")
    _require(links.get("proposal_id"), _PROPOSAL_ID, "config proposal linkage")
    print(
        json.dumps(
            {
                "design": top_name,
                "kind": kind,
                "top_pin_bits": manifest["top_pin_bits"],
                "status": "ok",
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
