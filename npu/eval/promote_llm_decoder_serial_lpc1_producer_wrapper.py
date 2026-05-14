#!/usr/bin/env python3
"""Promote measured serial_lpc1 ranker as the producer-coupled wrapper candidate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    from probe_llm_decoder_serial_ranker_producer_replay import _simulate_variant
    from probe_llm_decoder_producer_ranker_ready_valid_equivalence import (
        _resolve_executable,
    )
except ImportError:  # pragma: no cover - package-style imports in tests
    from npu.eval.probe_llm_decoder_serial_ranker_producer_replay import _simulate_variant
    from npu.eval.probe_llm_decoder_producer_ranker_ready_valid_equivalence import (
        _resolve_executable,
    )


JsonDict = dict[str, Any]


def _load_json(path: str | Path) -> JsonDict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _maybe_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _placed_cell_area(variant: JsonDict) -> float | None:
    synthesis = variant.get("synthesis") if isinstance(variant.get("synthesis"), dict) else {}
    for line in synthesis.get("log_tail", []):
        text = str(line)
        if "Placed Cell Area" not in text:
            continue
        try:
            return float(text.split()[-1])
        except ValueError:
            continue
    return None


def _variant_by_lpc(serial_ranker: JsonDict, lanes_per_cycle: int) -> JsonDict | None:
    for variant in serial_ranker.get("variants", []):
        if not isinstance(variant, dict):
            continue
        if int(variant.get("lanes_per_cycle", -1)) == lanes_per_cycle:
            return variant
    return None


def _selected_replay_row(replay: JsonDict, *, lanes_per_cycle: int, producer_ii_cycles: int) -> JsonDict | None:
    for row in replay.get("replay_rows", []):
        if not isinstance(row, dict):
            continue
        if (
            int(row.get("lanes_per_cycle", -1)) == lanes_per_cycle
            and int(row.get("producer_ii_cycles", -1)) == producer_ii_cycles
        ):
            return row
    return None


def _metrics_summary(variant: JsonDict | None) -> JsonDict | None:
    if variant is None:
        return None
    metrics = variant.get("metrics_row") if isinstance(variant.get("metrics_row"), dict) else {}
    return {
        "critical_path_ns": _maybe_float(metrics.get("critical_path_ns")),
        "die_area_um2": _maybe_float(metrics.get("die_area")),
        "placed_cell_area_um2": _placed_cell_area(variant),
        "total_power_mw": _maybe_float(metrics.get("total_power_mw")),
        "stage_elapsed_seconds": _maybe_float(metrics.get("stage_elapsed_seconds")),
        "metrics_status": metrics.get("status"),
        "design_dir": variant.get("design_dir"),
        "top": variant.get("top"),
    }


def build_report(
    *,
    serial_ranker: JsonDict,
    service_compatibility: JsonDict,
    producer_replay: JsonDict,
    focused_rtl_sim: JsonDict | None,
    lanes_per_cycle: int,
    producer_ii_cycles: int,
) -> JsonDict:
    variant = _variant_by_lpc(serial_ranker, lanes_per_cycle)
    replay_row = _selected_replay_row(
        producer_replay,
        lanes_per_cycle=lanes_per_cycle,
        producer_ii_cycles=producer_ii_cycles,
    )
    lowest_power = (
        service_compatibility.get("recommendation", {}).get("lowest_power_feasible")
        if isinstance(service_compatibility.get("recommendation"), dict)
        else None
    )
    focused_observed = (
        focused_rtl_sim.get("observed")
        if isinstance(focused_rtl_sim, dict) and isinstance(focused_rtl_sim.get("observed"), dict)
        else {}
    )
    focused_expected = (
        focused_rtl_sim.get("expected")
        if isinstance(focused_rtl_sim, dict) and isinstance(focused_rtl_sim.get("expected"), dict)
        else {}
    )
    replay_observed = (
        (replay_row or {}).get("rtl_sim", {}).get("observed")
        if isinstance((replay_row or {}).get("rtl_sim"), dict)
        else {}
    )
    checks = [
        {
            "name": "selected_variant_exists",
            "passed": variant is not None and variant.get("status") == "ok",
            "observed": None if variant is None else variant.get("top"),
        },
        {
            "name": "selected_variant_has_physical_metrics",
            "passed": variant is not None and (variant.get("metrics_row") or {}).get("status") == "ok",
            "observed": _metrics_summary(variant),
        },
        {
            "name": "service_compatibility_selected_lowest_power",
            "passed": isinstance(lowest_power, dict)
            and str(lowest_power.get("ranker")) == f"serial_lpc{lanes_per_cycle}",
            "observed": lowest_power,
        },
        {
            "name": "prior_replay_clean_at_selected_cadence",
            "passed": bool(replay_row)
            and (replay_row.get("rtl_sim") or {}).get("status") == "ok"
            and int(replay_observed.get("tb_backpressure", -1)) == 0,
            "observed": replay_row,
        },
        {
            "name": "focused_rtl_replay_matches_reference",
            "passed": isinstance(focused_rtl_sim, dict)
            and focused_rtl_sim.get("status") == "ok"
            and focused_observed.get("token") == focused_expected.get("token")
            and focused_observed.get("logit") == focused_expected.get("logit")
            and int(focused_observed.get("tb_backpressure", -1)) == 0,
            "observed": focused_rtl_sim,
        },
    ]
    passed = all(bool(check["passed"]) for check in checks)
    return {
        "version": 0.1,
        "model": "decoder_serial_lpc1_producer_coupled_wrapper_v1",
        "target": {
            "producer_lanes": 64,
            "top_k": 1,
            "lanes_per_cycle": lanes_per_cycle,
            "producer_ii_cycles": producer_ii_cycles,
            "wrapper_role": "selected_serial_ranker_for_output_projection_producer",
        },
        "selected_variant": variant,
        "selected_metrics": _metrics_summary(variant),
        "service_compatibility_lowest_power_feasible": lowest_power,
        "selected_prior_replay_row": replay_row,
        "focused_rtl_sim": focused_rtl_sim,
        "checks": checks,
        "decision": {
            "decision": (
                "serial_lpc1_producer_coupled_wrapper_promoted"
                if passed
                else "serial_lpc1_producer_coupled_wrapper_blocked"
            ),
            "next_step": (
                "Use serial_lpc1 as the ranker block in the next output-projection producer wrapper. "
                "The next open architectural risk is replacing the analytical producer cadence with "
                "measured producer output statistics or a resident-weight producer model."
                if passed
                else "Fix the selected serial ranker metrics or focused cadence replay before producer-wrapper promotion."
            ),
        },
        "assumptions": [
            "The promoted wrapper is the measured serial_lpc1 ranker plus candidate merge FIFO, not a synthetic producer ROM.",
            "The output-projection producer is assumed to issue r64 tiles no faster than the selected 384-cycle cadence.",
            "The focused replay validates ready-valid behavior at the selected cadence and carries prior PPA from the serial architecture sweep.",
            "If a resident-weight or cached producer issues faster tiles, lpc2/lpc4 remain guard candidates from the replay result.",
        ],
    }


def write_markdown(path: Path, payload: JsonDict) -> None:
    metrics = payload.get("selected_metrics") or {}
    lines = [
        "# Decoder Serial LPC1 Producer-Coupled Wrapper",
        "",
        f"- model: `{payload['model']}`",
        f"- decision: `{payload['decision']['decision']}`",
        f"- producer_ii_cycles: `{payload['target']['producer_ii_cycles']}`",
        f"- critical_path_ns: `{metrics.get('critical_path_ns')}`",
        f"- placed_cell_area_um2: `{metrics.get('placed_cell_area_um2')}`",
        f"- total_power_mw: `{metrics.get('total_power_mw')}`",
        f"- next_step: {payload['decision']['next_step']}",
        "",
        "## Checks",
        "",
        "| check | passed | observed |",
        "|---|---|---|",
    ]
    for check in payload["checks"]:
        lines.append(f"| {check['name']} | `{check['passed']}` | `{check.get('observed')}` |")
    lines.extend(["", "## Assumptions", ""])
    for item in payload["assumptions"]:
        lines.append(f"- {item}")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--serial-ranker", required=True)
    ap.add_argument("--service-compatibility", required=True)
    ap.add_argument("--producer-replay", required=True)
    ap.add_argument("--merge-config", required=True)
    ap.add_argument("--rtlgen-binary", default="build/rtlgen")
    ap.add_argument("--lanes-per-cycle", type=int, default=1)
    ap.add_argument("--producer-ii-cycles", type=int, default=384)
    ap.add_argument("--num-tiles", type=int, default=6)
    ap.add_argument("--out", required=True)
    ap.add_argument("--out-md", required=True)
    args = ap.parse_args()

    serial_ranker = _load_json(args.serial_ranker)
    service_compatibility = _load_json(args.service_compatibility)
    producer_replay = _load_json(args.producer_replay)
    variant = _variant_by_lpc(serial_ranker, args.lanes_per_cycle)
    rtlgen_binary = _resolve_executable(args.rtlgen_binary)
    focused_rtl_sim = None
    if variant is not None:
        focused_rtl_sim = _simulate_variant(
            variant=variant,
            scenario=f"selected_ii{args.producer_ii_cycles}",
            producer_ii_cycles=args.producer_ii_cycles,
            num_tiles=args.num_tiles,
            merge_config=Path(args.merge_config),
            rtlgen_binary=rtlgen_binary,
            producer_lanes=64,
            logit_bits=16,
            token_id_bits=16,
        )
    payload = build_report(
        serial_ranker=serial_ranker,
        service_compatibility=service_compatibility,
        producer_replay=producer_replay,
        focused_rtl_sim=focused_rtl_sim,
        lanes_per_cycle=args.lanes_per_cycle,
        producer_ii_cycles=args.producer_ii_cycles,
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
