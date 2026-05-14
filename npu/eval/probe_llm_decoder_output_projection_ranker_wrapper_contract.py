#!/usr/bin/env python3
"""Check the output-projection ranker wrapper policy contract on representative cases."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

try:
    from probe_llm_decoder_serial_ranker_producer_replay import (
        _make_tile_values,
        _reference_top1,
        _simulate_variant as _simulate_serial_variant,
    )
    from probe_llm_decoder_producer_ranker_ready_valid_equivalence import _resolve_executable
except ImportError:  # pragma: no cover - package-style imports in tests
    from npu.eval.probe_llm_decoder_serial_ranker_producer_replay import (
        _make_tile_values,
        _reference_top1,
        _simulate_variant as _simulate_serial_variant,
    )
    from npu.eval.probe_llm_decoder_producer_ranker_ready_valid_equivalence import _resolve_executable


JsonDict = dict[str, Any]
R64_LANES = 64


def _load_json(path: str | Path) -> JsonDict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _ranktree_result_from_log(sim: JsonDict) -> JsonDict:
    for line in sim.get("log_tail", []):
        match = re.search(
            r"RESULT token=(?P<token>\d+) logit=(?P<logit>-?\d+) accepted=(?P<accepted>\d+) "
            r"stalls=(?P<stalls>\d+) fifo_max=(?P<fifo_max>\d+) final_cycle=(?P<final_cycle>\d+)",
            str(line),
        )
        if match:
            return {key: int(value) for key, value in match.groupdict().items()}
    return {}


def _policy_rows(policy: JsonDict, selected_path: str) -> list[JsonDict]:
    return [
        row
        for row in policy.get("policy_rows", [])
        if isinstance(row, dict) and row.get("selected_path") == selected_path
    ]


def _representative_policy_row(policy: JsonDict, selected_path: str) -> JsonDict | None:
    rows = _policy_rows(policy, selected_path)
    if not rows:
        return None
    return min(rows, key=lambda row: int((row.get("producer") or {}).get("producer_ii_cycles", 10**9)))


def _banked_r64_reference(*, producer_lanes: int, num_tiles: int) -> JsonDict:
    tiles = _make_tile_values(num_tiles=num_tiles, producer_lanes=producer_lanes)
    full_reference = _reference_top1(tiles, producer_lanes=producer_lanes)
    bank_results: list[JsonDict] = []
    for bank_id, lane_base in enumerate(range(0, producer_lanes, R64_LANES)):
        bank_tiles = [row[lane_base : lane_base + R64_LANES] for row in tiles]
        bank_ref = _reference_top1(bank_tiles, producer_lanes=R64_LANES)
        bank_results.append(
            {
                "bank": bank_id,
                "local_token": bank_ref["token"],
                "global_token": int(bank_ref["token"]) + lane_base,
                "logit": bank_ref["logit"],
            }
        )
    selected = min(
        bank_results,
        key=lambda row: (-int(row["logit"]), int(row["global_token"])),
    )
    banked_reference = {"token": selected["global_token"], "logit": selected["logit"]}
    return {
        "producer_lanes": producer_lanes,
        "num_tiles": num_tiles,
        "bank_results": bank_results,
        "banked_reference": banked_reference,
        "full_reference": full_reference,
        "equivalent": banked_reference == full_reference,
    }


def _serial_case(
    *,
    policy: JsonDict,
    serial_wrapper: JsonDict,
    merge_config: Path,
    rtlgen_binary: str | None,
    num_tiles: int,
) -> JsonDict:
    row = _representative_policy_row(policy, "serial_lpc1")
    variant = serial_wrapper.get("selected_variant") if isinstance(serial_wrapper.get("selected_variant"), dict) else None
    threshold = (policy.get("policy") or {}).get("serial_lpc1_min_ii_cycles")
    sim = None
    if variant is not None and threshold is not None:
        sim = _simulate_serial_variant(
            variant=variant,
            scenario="policy_serial_lpc1",
            producer_ii_cycles=int(threshold),
            num_tiles=num_tiles,
            merge_config=merge_config,
            rtlgen_binary=rtlgen_binary,
            producer_lanes=R64_LANES,
            logit_bits=16,
            token_id_bits=16,
        )
    observed = (sim or {}).get("observed") if isinstance((sim or {}).get("observed"), dict) else {}
    expected = (sim or {}).get("expected") if isinstance((sim or {}).get("expected"), dict) else {}
    passed = (
        row is not None
        and isinstance(sim, dict)
        and sim.get("status") == "ok"
        and observed.get("token") == expected.get("token")
        and observed.get("logit") == expected.get("logit")
        and int(observed.get("tb_backpressure", -1)) == 0
    )
    return {
        "case": "streaming_serial_lpc1_r64",
        "policy_row": row,
        "rtl_sim": sim,
        "passed": passed,
        "reason": "serial RTL replay matches perf reference with zero backpressure" if passed else "serial RTL replay failed or policy row missing",
    }


def _ranktree_r64_case(*, policy: JsonDict, ranktree_promotion: JsonDict) -> JsonDict:
    row = _representative_policy_row(policy, "single_r64_ranktree")
    variant = (
        ranktree_promotion.get("selected_ranktree_variant")
        if isinstance(ranktree_promotion.get("selected_ranktree_variant"), dict)
        else {}
    )
    sim = variant.get("simulation") if isinstance(variant.get("simulation"), dict) else {}
    observed = _ranktree_result_from_log(sim)
    expected = sim.get("expected") if isinstance(sim.get("expected"), dict) else {}
    passed = (
        row is not None
        and sim.get("status") == "ok"
        and observed.get("token") == expected.get("token")
        and observed.get("logit") == expected.get("logit")
    )
    return {
        "case": "resident_ranktree_r64",
        "policy_row": row,
        "primitive_rtl_sim": sim,
        "observed": observed,
        "passed": passed,
        "reason": "rank-tree r64 RTL primitive matches perf reference" if passed else "rank-tree r64 primitive failed or policy row missing",
    }


def _ranktree_r128_case(*, policy: JsonDict, ranktree_promotion: JsonDict, num_tiles: int) -> JsonDict:
    row = _representative_policy_row(policy, "banked_r64_ranktrees")
    modes = {
        str(mode.get("mode")): mode
        for mode in ranktree_promotion.get("producer_modes", [])
        if isinstance(mode, dict)
    }
    banked_mode = modes.get("banked_r64_ranktrees")
    composition = _banked_r64_reference(producer_lanes=128, num_tiles=num_tiles)
    primitive_status = (
        (ranktree_promotion.get("selected_ranktree_variant") or {}).get("simulation") or {}
    ).get("status")
    passed = (
        row is not None
        and isinstance(banked_mode, dict)
        and int(banked_mode.get("ranker_instances", 0)) == 2
        and int(banked_mode.get("consumer_ii_cycles", 0)) == 1
        and primitive_status == "ok"
        and bool(composition["equivalent"])
    )
    return {
        "case": "resident_ranktree_banked_r128",
        "policy_row": row,
        "banked_mode": banked_mode,
        "primitive_rtl_status": primitive_status,
        "composition_reference": composition,
        "passed": passed,
        "reason": "banked r64 composition matches full r128 perf reference" if passed else "banked r128 composition failed or policy row missing",
    }


def build_report(
    *,
    policy: JsonDict,
    serial_wrapper: JsonDict,
    ranktree_promotion: JsonDict,
    merge_config: Path,
    rtlgen_binary: str | None,
    num_tiles: int,
) -> JsonDict:
    policy_decision = (policy.get("decision") or {}).get("decision") if isinstance(policy.get("decision"), dict) else None
    cases = [
        _serial_case(
            policy=policy,
            serial_wrapper=serial_wrapper,
            merge_config=merge_config,
            rtlgen_binary=rtlgen_binary,
            num_tiles=num_tiles,
        ),
        _ranktree_r64_case(policy=policy, ranktree_promotion=ranktree_promotion),
        _ranktree_r128_case(policy=policy, ranktree_promotion=ranktree_promotion, num_tiles=num_tiles),
    ]
    checks = [
        {
            "name": "ranker_policy_promoted",
            "passed": policy_decision == "output_projection_ranker_policy_promoted",
            "observed": policy_decision,
        },
        {
            "name": "representative_cases_passed",
            "passed": all(bool(case.get("passed")) for case in cases),
            "observed": {case["case"]: case.get("passed") for case in cases},
        },
    ]
    passed = all(bool(check["passed"]) for check in checks)
    return {
        "version": 0.1,
        "model": "decoder_output_projection_ranker_wrapper_contract_v1",
        "target": {
            "paths": ["serial_lpc1", "single_r64_ranktree", "banked_r64_ranktrees"],
            "producer_lanes": [64, 128],
            "num_tiles": num_tiles,
            "top_k": 1,
        },
        "representative_cases": cases,
        "checks": checks,
        "decision": {
            "decision": (
                "output_projection_ranker_wrapper_contract_passed"
                if passed
                else "output_projection_ranker_wrapper_contract_blocked"
            ),
            "next_step": (
                "Implement the wrapper RTL mux/control around the verified serial_lpc1 and rank-tree primitive paths, then run a physical wrapper sweep."
                if passed
                else "Fix the failing representative wrapper contract case before RTL wrapper implementation."
            ),
        },
        "assumptions": [
            "The serial path is checked by a fresh RTL replay of the promoted serial_lpc1 wrapper at the policy threshold.",
            "The r64 rank-tree path reuses the promoted rank-tree primitive RTL simulation from the rank-tree architecture sweep.",
            "The r128 banked path is a composition contract: two proven r64 primitives plus deterministic lower-token tie-break across banks.",
            "This job does not synthesize the final wrapper mux/control; it establishes the contract that the next RTL wrapper must implement.",
        ],
    }


def write_markdown(path: Path, payload: JsonDict) -> None:
    lines = [
        "# Decoder Output-Projection Ranker Wrapper Contract",
        "",
        f"- model: `{payload['model']}`",
        f"- decision: `{payload['decision']['decision']}`",
        f"- next_step: {payload['decision']['next_step']}",
        "",
        "## Representative Cases",
        "",
        "| case | passed | reason |",
        "|---|---|---|",
    ]
    for case in payload["representative_cases"]:
        lines.append(f"| {case['case']} | `{case['passed']}` | {case['reason']} |")
    lines.extend(["", "## Checks", "", "| check | passed | observed |", "|---|---|---|"])
    for check in payload["checks"]:
        lines.append(f"| {check['name']} | `{check['passed']}` | `{check.get('observed')}` |")
    lines.extend(["", "## Assumptions", ""])
    for item in payload["assumptions"]:
        lines.append(f"- {item}")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--policy", required=True)
    ap.add_argument("--serial-wrapper", required=True)
    ap.add_argument("--ranktree-promotion", required=True)
    ap.add_argument("--merge-config", required=True)
    ap.add_argument("--rtlgen-binary", default="build/rtlgen")
    ap.add_argument("--num-tiles", type=int, default=6)
    ap.add_argument("--out", required=True)
    ap.add_argument("--out-md", required=True)
    args = ap.parse_args()

    payload = build_report(
        policy=_load_json(args.policy),
        serial_wrapper=_load_json(args.serial_wrapper),
        ranktree_promotion=_load_json(args.ranktree_promotion),
        merge_config=Path(args.merge_config),
        rtlgen_binary=_resolve_executable(args.rtlgen_binary),
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
