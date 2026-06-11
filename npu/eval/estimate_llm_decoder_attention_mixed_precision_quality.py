#!/usr/bin/env python3
"""Proxy-test mixed-precision attention arithmetic for the Llama7B frontier."""

from __future__ import annotations

import argparse
import json
import math
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any

JsonDict = dict[str, Any]
Vector = list[float]
Matrix = list[Vector]


@dataclass(frozen=True)
class Candidate:
    candidate_id: str
    q_bits: int
    k_bits: int
    v_bits: int
    acc_bits: int
    score_bits: int
    weight_bits: int


def _int_list(value: str) -> list[int]:
    items = [int(item.strip()) for item in value.split(",") if item.strip()]
    if not items or any(item <= 0 for item in items):
        raise argparse.ArgumentTypeError("expected comma-separated positive integers")
    return items


def _str_list(value: str) -> list[str]:
    items = [item.strip() for item in value.split(",") if item.strip()]
    if not items:
        raise argparse.ArgumentTypeError("expected comma-separated strings")
    return items


def _dot(a: Vector, b: Vector) -> float:
    return sum(x * y for x, y in zip(a, b))


def _cosine(a: Vector, b: Vector) -> float:
    aa = math.sqrt(max(0.0, _dot(a, a)))
    bb = math.sqrt(max(0.0, _dot(b, b)))
    if aa == 0.0 or bb == 0.0:
        return 1.0 if aa == bb else 0.0
    return _dot(a, b) / (aa * bb)


def _rmse(a: Vector, b: Vector) -> float:
    if not a:
        return 0.0
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)) / len(a))


def _softmax(logits: Vector) -> Vector:
    top = max(logits)
    exps = [math.exp(min(80.0, value - top)) for value in logits]
    denom = sum(exps)
    return [value / denom for value in exps]


def _kl_divergence(reference: Vector, candidate: Vector) -> float:
    eps = 1e-12
    return sum(p * math.log(max(eps, p) / max(eps, q)) for p, q in zip(reference, candidate))


def _weighted_sum(weights: Vector, values: Matrix) -> Vector:
    if not values:
        return []
    out = [0.0 for _ in values[0]]
    for weight, vector in zip(weights, values):
        for index, value in enumerate(vector):
            out[index] += weight * value
    return out


def _quantize_symmetric(vector: Vector, bits: int) -> tuple[list[int], float]:
    if bits >= 16:
        return [int(round(value * 1024.0)) for value in vector], 1.0 / 1024.0
    levels = (1 << (bits - 1)) - 1
    max_abs = max((abs(value) for value in vector), default=0.0)
    if max_abs == 0.0:
        return [0 for _ in vector], 1.0
    scale = max_abs / levels
    return [max(-levels, min(levels, int(round(value / scale)))) for value in vector], scale


def _dequantize(qvector: list[int], scale: float) -> Vector:
    return [value * scale for value in qvector]


def _quantize_unsigned_probability(weights: Vector, bits: int) -> Vector:
    if bits >= 16:
        return list(weights)
    levels = (1 << bits) - 1
    quantized = [max(0, min(levels, int(round(weight * levels)))) for weight in weights]
    denom = sum(quantized)
    if denom <= 0:
        return list(weights)
    return [value / denom for value in quantized]


def _quantize_vector_symmetric_float(vector: Vector, bits: int) -> Vector:
    qvector, scale = _quantize_symmetric(vector, bits)
    return _dequantize(qvector, scale)


def _quantize_logits(logits: Vector, bits: int) -> Vector:
    if bits >= 24:
        return list(logits)
    qvector, scale = _quantize_symmetric(logits, bits)
    return _dequantize(qvector, scale)


def _candidate_dot_from_quantized_query(q_int: list[int], q_scale: float, key: Vector, candidate: Candidate) -> float:
    k_int, k_scale = _quantize_symmetric(key, candidate.k_bits)
    acc = sum(q * k for q, k in zip(q_int, k_int))
    signed_max = (1 << (candidate.acc_bits - 1)) - 1
    signed_min = -(1 << (candidate.acc_bits - 1))
    saturated = max(signed_min, min(signed_max, acc))
    return saturated * q_scale * k_scale


def _generate_native_gqa_case(
    *,
    rng: random.Random,
    regime: str,
    attention_heads: int,
    kv_heads: int,
    sequence_length: int,
    head_dim: int,
) -> tuple[list[Matrix], list[Matrix], list[Vector], list[int]]:
    if attention_heads % kv_heads != 0:
        raise ValueError("attention_heads must be divisible by kv_heads")
    group_size = attention_heads // kv_heads
    group_keys = [
        [[rng.gauss(0.0, 1.0) for _ in range(head_dim)] for _ in range(sequence_length)]
        for _ in range(kv_heads)
    ]
    group_values = [
        [[rng.gauss(0.0, 1.0) for _ in range(head_dim)] for _ in range(sequence_length)]
        for _ in range(kv_heads)
    ]
    keys_by_head: list[Matrix] = []
    values_by_head: list[Matrix] = []
    queries: list[Vector] = []
    targets: list[int] = []
    for head in range(attention_heads):
        group = min(kv_heads - 1, head // group_size)
        keys = group_keys[group]
        values = group_values[group]
        if regime == "native_retrieval":
            target = (31 * head + 7 * group + 5) % sequence_length
            query = [2.2 * value + rng.gauss(0.0, 0.10) for value in keys[target]]
            values[target] = [3.0 if index == (head % head_dim) else 0.0 for index in range(head_dim)]
        elif regime == "native_low_margin":
            target = (19 * head + 11 * group + 3) % sequence_length
            distractor = (target + max(1, sequence_length // 7)) % sequence_length
            query = [
                0.58 * keys[target][index] + 0.52 * keys[distractor][index] + rng.gauss(0.0, 0.12)
                for index in range(head_dim)
            ]
        elif regime == "native_correlated_queries":
            target = (17 * head + 13 * group) % sequence_length
            query = [value + rng.gauss(0.0, 0.08) for value in keys[target]]
        elif regime == "native_random":
            target = (23 * head + 3 * group + 11) % sequence_length
            query = [rng.gauss(0.0, 1.0) for _ in range(head_dim)]
        else:
            raise ValueError(f"unsupported regime: {regime}")
        keys_by_head.append(keys)
        values_by_head.append(values)
        queries.append(query)
        targets.append(target)
    return keys_by_head, values_by_head, queries, targets


def _reference_attention(keys: Matrix, values: Matrix, query: Vector, target: int) -> JsonDict:
    scale = 1.0 / math.sqrt(len(query))
    logits = [_dot(query, key) * scale for key in keys]
    weights = _softmax(logits)
    return {
        "top1": max(range(len(weights)), key=lambda index: weights[index]),
        "target": target,
        "weights": weights,
        "output": _weighted_sum(weights, values),
    }


def _candidate_attention(
    keys: Matrix,
    quantized_values: Matrix,
    query: Vector,
    target: int,
    candidate: Candidate,
) -> JsonDict:
    scale = 1.0 / math.sqrt(len(query))
    q_int, q_scale = _quantize_symmetric(query, candidate.q_bits)
    logits = [_candidate_dot_from_quantized_query(q_int, q_scale, key, candidate) * scale for key in keys]
    logits = _quantize_logits(logits, candidate.score_bits)
    weights = _softmax(logits)
    weights = _quantize_unsigned_probability(weights, candidate.weight_bits)
    return {
        "top1": max(range(len(weights)), key=lambda index: weights[index]),
        "target": target,
        "weights": weights,
        "output": _weighted_sum(weights, quantized_values),
    }


def _parse_candidate_spec(spec: str) -> Candidate:
    values: dict[str, int] = {}
    for part in spec.split(":"):
        if len(part) < 2:
            raise ValueError(f"bad candidate spec part {part!r} in {spec!r}")
        key = part[0]
        value = int(part[1:])
        values[key] = value
    required = {"q", "k", "v", "a", "s", "w"}
    missing = required - set(values)
    if missing:
        raise ValueError(f"candidate spec {spec!r} missing {sorted(missing)}")
    return Candidate(
        candidate_id=spec.replace(":", "_"),
        q_bits=values["q"],
        k_bits=values["k"],
        v_bits=values["v"],
        acc_bits=values["a"],
        score_bits=values["s"],
        weight_bits=values["w"],
    )


def _summarize(rows: list[JsonDict]) -> JsonDict:
    out: JsonDict = {"sample_count": len(rows)}
    for key in ("top1_match", "retrieval_hit", "kl_divergence", "output_cosine", "output_rmse"):
        if key == "retrieval_hit":
            source_rows = [
                row for row in rows if row.get("regime") in {"native_retrieval", "native_correlated_queries"}
            ]
        else:
            source_rows = rows
        values = [float(row[key]) for row in source_rows]
        out[f"mean_{key}"] = round(sum(values) / len(values), 6) if values else 0.0
        out[f"min_{key}"] = round(min(values), 6) if values else 0.0
        out[f"max_{key}"] = round(max(values), 6) if values else 0.0
    return out


def _decision(summary: JsonDict) -> str:
    if (
        float(summary["mean_top1_match"]) >= 0.995
        and float(summary["mean_retrieval_hit"]) >= 0.995
        and float(summary["mean_output_cosine"]) >= 0.999
        and float(summary["max_kl_divergence"]) <= 0.02
    ):
        return "mixed_precision_proxy_pass"
    if (
        float(summary["mean_top1_match"]) >= 0.99
        and float(summary["mean_retrieval_hit"]) >= 0.99
        and float(summary["mean_output_cosine"]) >= 0.995
    ):
        return "mixed_precision_borderline"
    return "mixed_precision_risky"


def _candidate_cost_key(row: JsonDict) -> tuple[int, int, int, int, int, int]:
    return (
        int(row["q_bits"]) + int(row["k_bits"]) + int(row["v_bits"]),
        int(row["acc_bits"]),
        int(row["score_bits"]),
        int(row["weight_bits"]),
        int(row["q_bits"]),
        int(row["v_bits"]),
    )


def build_report(
    *,
    dual_stream_feasibility: JsonDict | None,
    attention_heads: int,
    kv_heads: int,
    head_dim: int,
    sequence_length_list: list[int],
    regime_list: list[str],
    seed_count: int,
    candidate_specs: list[str],
) -> JsonDict:
    candidates = [_parse_candidate_spec(spec) for spec in candidate_specs]
    metric_rows: list[JsonDict] = []
    for sequence_length in sequence_length_list:
        for regime in regime_list:
            for seed in range(seed_count):
                rng = random.Random(
                    0xA771000
                    + sequence_length * 131
                    + seed * 17
                    + len(regime) * 19
                    + attention_heads * 3
                    + kv_heads * 5
                    + head_dim
                )
                keys_by_head, values_by_head, queries, targets = _generate_native_gqa_case(
                    rng=rng,
                    regime=regime,
                    attention_heads=attention_heads,
                    kv_heads=kv_heads,
                    sequence_length=sequence_length,
                    head_dim=head_dim,
                )
                references = [
                    _reference_attention(keys_by_head[head], values_by_head[head], queries[head], targets[head])
                    for head in range(attention_heads)
                ]
                for candidate in candidates:
                    quantized_values_by_head = [
                        [_quantize_vector_symmetric_float(value, candidate.v_bits) for value in values_by_head[head]]
                        for head in range(attention_heads)
                    ]
                    for head in range(attention_heads):
                        cand = _candidate_attention(
                            keys_by_head[head],
                            quantized_values_by_head[head],
                            queries[head],
                            targets[head],
                            candidate,
                        )
                        ref = references[head]
                        metric_rows.append(
                            {
                                "candidate_id": candidate.candidate_id,
                                "q_bits": candidate.q_bits,
                                "k_bits": candidate.k_bits,
                                "v_bits": candidate.v_bits,
                                "acc_bits": candidate.acc_bits,
                                "score_bits": candidate.score_bits,
                                "weight_bits": candidate.weight_bits,
                                "sequence_length": sequence_length,
                                "regime": regime,
                                "seed": seed,
                                "head": head,
                                "top1_match": 1.0 if cand["top1"] == ref["top1"] else 0.0,
                                "retrieval_hit": 1.0 if cand["top1"] == ref["target"] else 0.0,
                                "kl_divergence": _kl_divergence(ref["weights"], cand["weights"]),
                                "output_cosine": _cosine(ref["output"], cand["output"]),
                                "output_rmse": _rmse(ref["output"], cand["output"]),
                            }
                        )

    candidate_summary: list[JsonDict] = []
    for candidate in candidates:
        rows = [row for row in metric_rows if row["candidate_id"] == candidate.candidate_id]
        summary = _summarize(rows)
        summary.update(
            {
                "candidate_id": candidate.candidate_id,
                "q_bits": candidate.q_bits,
                "k_bits": candidate.k_bits,
                "v_bits": candidate.v_bits,
                "acc_bits": candidate.acc_bits,
                "score_bits": candidate.score_bits,
                "weight_bits": candidate.weight_bits,
                "decision": _decision(summary),
            }
        )
        candidate_summary.append(summary)

    regime_summary: list[JsonDict] = []
    for candidate in candidates:
        for regime in regime_list:
            rows = [
                row
                for row in metric_rows
                if row["candidate_id"] == candidate.candidate_id and row["regime"] == regime
            ]
            summary = _summarize(rows)
            summary.update({"candidate_id": candidate.candidate_id, "regime": regime, "decision": _decision(summary)})
            regime_summary.append(summary)

    passing = [row for row in candidate_summary if row["decision"] == "mixed_precision_proxy_pass"]
    borderline = [row for row in candidate_summary if row["decision"] == "mixed_precision_borderline"]
    best_quality = max(
        candidate_summary,
        key=lambda row: (
            float(row["mean_top1_match"]),
            float(row["mean_retrieval_hit"]),
            float(row["mean_output_cosine"]),
            -float(row["mean_kl_divergence"]),
        ),
    )
    best_low_cost_pass = min(passing, key=_candidate_cost_key) if passing else None
    best_low_cost_candidate = best_low_cost_pass or (min(borderline, key=_candidate_cost_key) if borderline else None)
    dual_diag = (dual_stream_feasibility or {}).get("diagnosis") or {}
    diagnosis = {
        "decision": (
            "mixed_precision_quality_candidate_found"
            if best_low_cost_pass
            else "mixed_precision_quality_borderline"
            if best_low_cost_candidate
            else "mixed_precision_quality_blocked"
        ),
        "best_quality_candidate": best_quality["candidate_id"],
        "best_quality_decision": best_quality["decision"],
        "best_low_cost_candidate": best_low_cost_candidate.get("candidate_id") if best_low_cost_candidate else None,
        "best_low_cost_decision": best_low_cost_candidate.get("decision") if best_low_cost_candidate else None,
        "passing_candidate_count": len(passing),
        "borderline_candidate_count": len(borderline),
        "dual_stream_required_compute_density_gain": dual_diag.get("best_requested_required_compute_density_gain"),
        "recommended_next_step": (
            "run PPA for the lowest-cost passing mixed-precision attention compute primitive and keep a real-checkpoint Llama-class quality gate before promotion"
            if best_low_cost_pass
            else "do not promote lower precision compute yet; either use the borderline candidate only as a PPA lower bound or expand quality/model-native evaluation"
            if best_low_cost_candidate
            else "hold mixed-precision compute promotion and test safer precision or QAT/model-native recovery"
        ),
    }
    return {
        "version": 1,
        "model": "llm_decoder_attention_mixed_precision_quality_llama7b_v1",
        "inputs": {
            "dual_stream_feasibility_model": (dual_stream_feasibility or {}).get("model", ""),
            "attention_heads": attention_heads,
            "kv_heads": kv_heads,
            "gqa_group_size": attention_heads // kv_heads,
            "head_dim": head_dim,
            "sequence_length_list": sequence_length_list,
            "regime_list": regime_list,
            "seed_count": seed_count,
            "candidate_specs": candidate_specs,
        },
        "sweep_summary": {
            "metric_row_count": len(metric_rows),
            "candidate_count": len(candidates),
            "passing_candidate_count": len(passing),
            "borderline_candidate_count": len(borderline),
        },
        "diagnosis": diagnosis,
        "best_quality": best_quality,
        "best_low_cost_candidate": best_low_cost_candidate,
        "candidate_summary": sorted(candidate_summary, key=lambda row: (row["decision"], _candidate_cost_key(row))),
        "regime_summary": sorted(regime_summary, key=lambda row: (row["candidate_id"], row["regime"])),
        "metric_rows_sample": metric_rows[:200],
        "assumptions": [
            "This is a Llama7B-shape synthetic native-GQA attention proxy, not measured Llama7B perplexity or task accuracy.",
            "The proxy uses 32 attention heads, 4 KV heads, and head_dim 128 by default to match the current GQA8 Llama7B frontier assumption.",
            "Q/K/V use per-vector symmetric quantization; accumulator saturation models fixed-width integer dot products.",
            "Passing this proxy is only a gate for mixed-precision RTL/PPA and later real-checkpoint validation.",
        ],
    }


def write_markdown(path: Path, payload: JsonDict) -> None:
    diag = payload["diagnosis"]
    lines = [
        "# Llama7B Attention Mixed-Precision Quality Proxy",
        "",
        f"- decision: `{diag['decision']}`",
        f"- best quality candidate: `{diag['best_quality_candidate']}`",
        f"- best low-cost candidate: `{diag['best_low_cost_candidate']}`",
        f"- passing candidates: `{diag['passing_candidate_count']}`",
        f"- borderline candidates: `{diag['borderline_candidate_count']}`",
        f"- dual-stream required density gain: `{diag['dual_stream_required_compute_density_gain']}`",
        f"- recommended next step: `{diag['recommended_next_step']}`",
        "",
        "## Candidate Summary",
        "",
        "| candidate | q | k | v | acc | score | weight | top1 | retrieval | cosine | kl | decision |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in payload["candidate_summary"]:
        lines.append(
            "| {candidate_id} | {q_bits} | {k_bits} | {v_bits} | {acc_bits} | {score_bits} | {weight_bits} | "
            "{mean_top1_match} | {mean_retrieval_hit} | {mean_output_cosine} | {mean_kl_divergence} | {decision} |".format(
                **row
            )
        )
    lines.extend(
        [
            "",
            "## Regime Summary",
            "",
            "| candidate | regime | top1 | retrieval | cosine | kl | decision |",
            "|---|---|---:|---:|---:|---:|---|",
        ]
    )
    for row in payload["regime_summary"]:
        lines.append(
            "| {candidate_id} | {regime} | {mean_top1_match} | {mean_retrieval_hit} | "
            "{mean_output_cosine} | {mean_kl_divergence} | {decision} |".format(**row)
        )
    lines.extend(["", "## Assumptions", ""])
    lines.extend(f"- {item}" for item in payload["assumptions"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dual-stream-feasibility")
    ap.add_argument("--attention-heads", type=int, default=32)
    ap.add_argument("--kv-heads", type=int, default=4)
    ap.add_argument("--head-dim", type=int, default=128)
    ap.add_argument("--sequence-length-list", type=_int_list, default=[64, 128])
    ap.add_argument(
        "--regime-list",
        type=_str_list,
        default=["native_correlated_queries", "native_retrieval", "native_low_margin", "native_random"],
    )
    ap.add_argument("--seed-count", type=int, default=1)
    ap.add_argument(
        "--candidate-spec-list",
        type=_str_list,
        default=[
            "q8:k8:v8:a24:s24:w16",
            "q8:k8:v8:a20:s24:w16",
            "q8:k8:v8:a24:s16:w12",
            "q6:k8:v8:a24:s24:w16",
            "q8:k8:v6:a24:s24:w16",
        ],
    )
    ap.add_argument("--out", required=True)
    ap.add_argument("--out-md", required=True)
    args = ap.parse_args()

    dual_stream = (
        json.loads(Path(args.dual_stream_feasibility).read_text(encoding="utf-8"))
        if args.dual_stream_feasibility
        else None
    )
    payload = build_report(
        dual_stream_feasibility=dual_stream,
        attention_heads=args.attention_heads,
        kv_heads=args.kv_heads,
        head_dim=args.head_dim,
        sequence_length_list=args.sequence_length_list,
        regime_list=args.regime_list,
        seed_count=args.seed_count,
        candidate_specs=args.candidate_spec_list,
    )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(Path(args.out_md), payload)
    print(json.dumps({"ok": True, "out": args.out, "out_md": args.out_md}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
