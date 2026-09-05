#!/usr/bin/env python3
"""Compose exact RMSNorm service cycles into the current Llama7B latency anchor."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

JsonDict = dict[str, Any]

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BASELINE = REPO_ROOT / (
    "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
    "decoder_attention_score32_integrated_frontier_ranking__"
    "l2_decoder_attention_score32_integrated_frontier_ranking_llama7b_v1.json"
)
DEFAULT_ATTENTION_SCOPE = REPO_ROOT / (
    "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
    "decoder_attention_composed_datapath_physical_feasibility__"
    "l2_decoder_attention_composed_datapath_score32_exp_lut_div_reduced_replica_"
    "measured_command_control_llama7b_v1.json"
)


def _load(path: Path) -> JsonDict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _portable_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve()))
    except ValueError:
        return str(path)


def build_report(
    baseline: JsonDict,
    *,
    baseline_path: Path,
    attention_scope: JsonDict,
    attention_scope_path: Path,
    row_cycles: int = 1800,
    rows_per_token: int = 65,
    clock_periods_ns: tuple[float, ...] = (10.0, 14.0, 18.0),
    hidden_fractions: tuple[float, ...] = (0.0, 0.5, 1.0),
) -> JsonDict:
    if row_cycles <= 0 or rows_per_token <= 0:
        raise ValueError("row_cycles and rows_per_token must be positive")
    diagnosis = baseline.get("diagnosis")
    if not isinstance(diagnosis, dict):
        raise ValueError("baseline is missing diagnosis")
    candidate_id = str(diagnosis.get("current_recommended_candidate") or "")
    latency_us = float(diagnosis.get("score32_latency_us") or 0.0)
    if not candidate_id or latency_us <= 0.0:
        raise ValueError("baseline lacks a positive score32 latency anchor")

    scope_row = attention_scope.get("best_requested")
    if not isinstance(scope_row, dict):
        raise ValueError("attention scope artifact is missing best_requested")
    terms = {
        "qkv_cycles": int(scope_row["replica_recost_qkv_cycles"]),
        "tile_waves": int(scope_row["tile_waves"]),
        "tile_service_cycles": int(scope_row["replica_recost_tile_service_cycles"]),
        "command_dispatch_cycles": int(scope_row["command_dispatch_cycles"]),
        "cross_tile_reduction_cycles": int(scope_row["cross_tile_reduction_cycles"]),
        "kv_write_cycles": int(scope_row["kv_write_cycles"]),
    }
    reconstructed_layer_cycles = (
        terms["qkv_cycles"]
        + terms["tile_waves"] * terms["tile_service_cycles"]
        + terms["command_dispatch_cycles"]
        + terms["cross_tile_reduction_cycles"]
        + terms["kv_write_cycles"]
    )
    recorded_layer_cycles = int(scope_row["replica_recost_layer_cycles"])
    recorded_total_cycles = int(scope_row["replica_recost_total_cycles"])
    layers = int(scope_row["layers"])
    if reconstructed_layer_cycles != recorded_layer_cycles:
        raise ValueError("attention layer-cycle provenance equation does not reconstruct")
    if recorded_layer_cycles * layers != recorded_total_cycles:
        raise ValueError("attention total-cycle provenance equation does not reconstruct")

    service_cycles = row_cycles * rows_per_token
    rows: list[JsonDict] = []
    for period_ns in clock_periods_ns:
        if period_ns <= 0.0:
            raise ValueError("clock periods must be positive")
        raw_norm_us = service_cycles * period_ns / 1000.0
        for hidden in hidden_fractions:
            if hidden < 0.0 or hidden > 1.0:
                raise ValueError("hidden fractions must be in [0, 1]")
            exposed_norm_us = raw_norm_us * (1.0 - hidden)
            composed_latency_us = latency_us + exposed_norm_us
            rows.append(
                {
                    "clock_period_ns": period_ns,
                    "hidden_fraction": hidden,
                    "rmsnorm_service_cycles_per_token": service_cycles,
                    "raw_rmsnorm_latency_us": round(raw_norm_us, 9),
                    "exposed_rmsnorm_latency_us": round(exposed_norm_us, 9),
                    "composed_latency_us": round(composed_latency_us, 9),
                    "composed_token_throughput_per_s": round(1.0e6 / composed_latency_us, 9),
                    "latency_increase_pct": round(100.0 * exposed_norm_us / latency_us, 9),
                }
            )

    return {
        "version": 1,
        "model": "llama7b_rmsnorm_macro_banked_latency_composition_v1",
        "decision": "latency_sensitivity_only_pending_routed_ppa",
        "baseline": {
            "candidate_id": candidate_id,
            "latency_us": latency_us,
            "token_throughput_per_s": float(diagnosis["score32_token_throughput_per_s"]),
            "source_path": _portable_path(baseline_path),
            "source_sha256": _sha256(baseline_path),
        },
        "rmsnorm_contract": {
            "transformer_layers": 32,
            "rows_per_layer": 2,
            "final_rows": 1,
            "rows_per_token": rows_per_token,
            "row_cycles": row_cycles,
            "service_cycles_per_token": service_cycles,
            "storage_backend": "fakeram45_64x32_banked",
            "macro_count": 64,
        },
        "attention_scope_proof": {
            "status": "verified_attention_only_excludes_transformer_rmsnorm",
            "source_path": _portable_path(attention_scope_path),
            "source_sha256": _sha256(attention_scope_path),
            "layer_cycle_terms": terms,
            "reconstructed_layer_cycles": reconstructed_layer_cycles,
            "recorded_layer_cycles": recorded_layer_cycles,
            "layers": layers,
            "recorded_total_cycles": recorded_total_cycles,
            "excluded_terms": ["pre_attention_rmsnorm", "pre_mlp_rmsnorm", "final_rmsnorm"],
        },
        "rows": rows,
        "promotion_gate_pass": False,
        "blockers": [
            "routed timing, area, and power for the macro-backed RMSNorm are pending",
            "the amount of RMSNorm overlap with attention/MLP execution is not measured",
            "activity-backed RMSNorm energy is unavailable",
        ],
        "interpretation": (
            "The source equation proves the attention baseline excludes transformer RMSNorm, so the zero-hidden "
            "row is a non-double-counted serialized increment and the fully hidden row is the overlap lower bound. "
            "Do not rerank PPA or claim final full-model latency until routed clock, "
            "overlap, area, and activity evidence are available."
        ),
    }


def render_markdown(report: JsonDict) -> str:
    base = report["baseline"]
    contract = report["rmsnorm_contract"]
    scope = report["attention_scope_proof"]
    lines = [
        "# Llama7B Macro-Backed RMSNorm Latency Composition",
        "",
        f"- decision: `{report['decision']}`",
        f"- baseline candidate: `{base['candidate_id']}`",
        f"- baseline latency: `{base['latency_us']} us`",
        f"- RMSNorm rows/token: `{contract['rows_per_token']}`",
        f"- RMSNorm cycles/row: `{contract['row_cycles']}`",
        f"- RMSNorm service cycles/token: `{contract['service_cycles_per_token']}`",
        f"- baseline scope proof: `{scope['status']}`",
        "",
        "| clock ns | hidden fraction | raw norm us | exposed norm us | composed us | token/s | increase |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in report["rows"]:
        lines.append(
            "| {clock_period_ns:g} | {hidden_fraction:.1f} | {raw_rmsnorm_latency_us:.3f} | "
            "{exposed_rmsnorm_latency_us:.3f} | {composed_latency_us:.3f} | "
            "{composed_token_throughput_per_s:.3f} | {latency_increase_pct:.3f}% |".format(**row)
        )
    lines.extend(["", "## Blockers", ""])
    lines.extend(f"- {item}" for item in report["blockers"])
    lines.extend(["", report["interpretation"], ""])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE)
    parser.add_argument("--attention-scope", type=Path, default=DEFAULT_ATTENTION_SCOPE)
    parser.add_argument("--out-json", type=Path)
    parser.add_argument("--out-md", type=Path)
    args = parser.parse_args()
    report = build_report(
        _load(args.baseline),
        baseline_path=args.baseline,
        attention_scope=_load(args.attention_scope),
        attention_scope_path=args.attention_scope,
    )
    if args.out_json:
        args.out_json.parent.mkdir(parents=True, exist_ok=True)
        args.out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.out_md:
        args.out_md.parent.mkdir(parents=True, exist_ok=True)
        args.out_md.write_text(render_markdown(report), encoding="utf-8")
    if not args.out_json and not args.out_md:
        print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
