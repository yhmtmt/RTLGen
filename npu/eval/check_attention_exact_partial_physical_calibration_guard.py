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
_MACRO_WIDTH_UM = 20.14
_MACRO_HEIGHT_UM = 61.6
_CORE_LX_UM = 50.0
_CORE_LY_UM = 50.0
_CORE_UX_UM = 1550.0
_CORE_UY_UM = 1550.0
_PLACEMENT_RE = re.compile(
    r"^place_macro\s+-macro_name\s+\{([^}]+)\}\s+"
    r"-location\s+\{([0-9.]+)\s+([0-9.]+)\}\s+"
    r"-orientation\s+(R0|MY)$"
)


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


def _validate_temporal_macro_placement(
    *, design_dir: Path, checked_macro: dict[str, object]
) -> Path:
    raw_path = str(checked_macro.get("macro_placement_tcl") or "").strip()
    if not raw_path:
        raise SystemExit("temporal macro manifest requires macro_placement_tcl")
    placement_path = Path(raw_path)
    if not placement_path.is_absolute():
        placement_path = (design_dir / placement_path).resolve()
    if not placement_path.is_file():
        raise SystemExit(f"missing temporal macro placement: {placement_path}")

    placements: dict[str, tuple[float, float, str]] = {}
    for line_number, raw_line in enumerate(
        placement_path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        match = _PLACEMENT_RE.fullmatch(line)
        if match is None:
            raise SystemExit(
                f"unsupported temporal macro placement line {line_number}: {line}"
            )
        name, x_text, y_text, orientation = match.groups()
        if name in placements:
            raise SystemExit(f"duplicate temporal macro placement: {name}")
        x_um = float(x_text)
        y_um = float(y_text)
        if not (
            _CORE_LX_UM <= x_um
            and _CORE_LY_UM <= y_um
            and x_um + _MACRO_WIDTH_UM <= _CORE_UX_UM
            and y_um + _MACRO_HEIGHT_UM <= _CORE_UY_UM
        ):
            raise SystemExit(f"temporal macro placement lies outside the core: {name}")
        placements[name] = (x_um, y_um, orientation)

    expected = {
        (
            "u_temporal/u_state_memory/"
            f"gen_bank\\[{bank}\\].gen_lane\\[{lane}\\].u_state_mem"
        )
        for bank in range(8)
        for lane in range(13)
    }
    actual = set(placements)
    if actual != expected:
        missing = sorted(expected - actual)
        unexpected = sorted(actual - expected)
        raise SystemExit(
            "temporal macro placement inventory mismatch: "
            f"missing={missing[:4]} unexpected={unexpected[:4]}"
        )
    return placement_path


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
        placement_path = _validate_temporal_macro_placement(
            design_dir=design_dir,
            checked_macro=checked_macro,
        )
        _require(
            manifest.get("temporal_scale_divider_impl"),
            "mersenne24_correction2_exact",
            "temporal scale divider",
        )
        _require(manifest.get("physical_timing_claim"), "single_temporal_clock_domain", "timing claim")
        if "fakeram45_64x32 u_state_mem" not in rtl:
            raise SystemExit("temporal harness must instantiate fakeram45_64x32 state macros")
        for required in (
            "function automatic [33:0] divide_mersenne24_u57;",
            "function automatic [41:0] divide_mersenne24_u65;",
            "quotient = divide_mersenne24_u57(product);",
            "quotient = divide_mersenne24_u65(product);",
        ):
            if required not in rtl:
                raise SystemExit(f"temporal harness lacks exact Mersenne divider: {required}")
        for forbidden in (
            "/ 57'd16777215",
            "/ 65'd16777215",
        ):
            if forbidden in rtl:
                raise SystemExit(f"generic constant divider is forbidden: {forbidden}")
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
                "macro_placement_tcl": (
                    str(placement_path) if kind == "temporal_finalizer" else None
                ),
                "status": "ok",
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
