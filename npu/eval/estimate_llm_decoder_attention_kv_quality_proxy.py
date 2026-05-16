#!/usr/bin/env python3
"""Proxy-test attention/KV structural reductions on controlled attention regimes."""

from __future__ import annotations

import argparse
import json
import math
import random
from pathlib import Path
from typing import Any

JsonDict = dict[str, Any]
Vector = list[float]
Matrix = list[Vector]


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


def _add(a: Vector, b: Vector) -> Vector:
    return [x + y for x, y in zip(a, b)]


def _scale(a: Vector, factor: float) -> Vector:
    return [x * factor for x in a]


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


def _quantize_vector(vector: Vector, bits: int) -> Vector:
    if bits >= 16:
        return list(vector)
    levels = (1 << (bits - 1)) - 1
    max_abs = max((abs(value) for value in vector), default=0.0)
    if max_abs == 0.0:
        return list(vector)
    scale = max_abs / levels
    return [max(-levels, min(levels, round(value / scale))) * scale for value in vector]


def _average_vectors(vectors: list[Vector]) -> Vector:
    if not vectors:
        return []
    out = [0.0 for _ in vectors[0]]
    for vector in vectors:
        for index, value in enumerate(vector):
            out[index] += value
    return [value / len(vectors) for value in out]


def _kv_group_count(*, attention_heads: int, kv_sharing: str) -> int:
    if kv_sharing == "mha":
        return attention_heads
    if kv_sharing == "gqa4":
        return max(1, math.ceil(attention_heads / 4))
    if kv_sharing == "gqa8":
        return max(1, math.ceil(attention_heads / 8))
    if kv_sharing == "mqa":
        return 1
    raise ValueError(f"unsupported kv sharing: {kv_sharing}")


def _candidate_id(*, kv_sharing: str, kv_bits: int) -> str:
    return f"{kv_sharing}_kv{kv_bits}"


def _generate_regime(
    *,
    rng: random.Random,
    regime: str,
    attention_heads: int,
    sequence_length: int,
    head_dim: int,
) -> tuple[list[Matrix], list[Matrix], list[Vector], list[int]]:
    base_keys = [[rng.gauss(0.0, 1.0) for _ in range(head_dim)] for _ in range(sequence_length)]
    base_values = [[rng.gauss(0.0, 1.0) for _ in range(head_dim)] for _ in range(sequence_length)]
    keys_by_head: list[Matrix] = []
    values_by_head: list[Matrix] = []
    queries: list[Vector] = []
    targets: list[int] = []
    for head in range(attention_heads):
        if regime == "correlated_heads":
            noise = 0.08
            keys = [
                [value + rng.gauss(0.0, noise) for value in vector]
                for vector in base_keys
            ]
            values = [
                [value + rng.gauss(0.0, noise) for value in vector]
                for vector in base_values
            ]
            target = (17 * head + 13) % sequence_length
            query = [value + rng.gauss(0.0, noise) for value in keys[target]]
        elif regime == "retrieval":
            keys = [[rng.gauss(0.0, 1.0) for _ in range(head_dim)] for _ in range(sequence_length)]
            values = [[rng.gauss(0.0, 1.0) for _ in range(head_dim)] for _ in range(sequence_length)]
            target = (31 * head + 7) % sequence_length
            query = [2.3 * value + rng.gauss(0.0, 0.12) for value in keys[target]]
            values[target] = [3.0 if index == (head % head_dim) else 0.0 for index in range(head_dim)]
        elif regime == "low_margin":
            keys = [[rng.gauss(0.0, 1.0) for _ in range(head_dim)] for _ in range(sequence_length)]
            values = [[rng.gauss(0.0, 1.0) for _ in range(head_dim)] for _ in range(sequence_length)]
            target = (19 * head + 5) % sequence_length
            distractor = (target + max(1, sequence_length // 5)) % sequence_length
            query = _add(_scale(keys[target], 0.55), _scale(keys[distractor], 0.50))
            query = [value + rng.gauss(0.0, 0.15) for value in query]
        elif regime == "independent_heads":
            keys = [[rng.gauss(0.0, 1.0) for _ in range(head_dim)] for _ in range(sequence_length)]
            values = [[rng.gauss(0.0, 1.0) for _ in range(head_dim)] for _ in range(sequence_length)]
            target = (23 * head + 11) % sequence_length
            query = [rng.gauss(0.0, 1.0) for _ in range(head_dim)]
        else:
            raise ValueError(f"unsupported regime: {regime}")
        keys_by_head.append(keys)
        values_by_head.append(values)
        queries.append(query)
        targets.append(target)
    return keys_by_head, values_by_head, queries, targets


def _apply_candidate_kv(
    *,
    keys_by_head: list[Matrix],
    values_by_head: list[Matrix],
    attention_heads: int,
    kv_sharing: str,
    kv_bits: int,
) -> tuple[list[Matrix], list[Matrix]]:
    kv_groups = _kv_group_count(attention_heads=attention_heads, kv_sharing=kv_sharing)
    group_size = math.ceil(attention_heads / kv_groups)
    out_keys: list[Matrix] = []
    out_values: list[Matrix] = []
    for head in range(attention_heads):
        start = (head // group_size) * group_size
        end = min(attention_heads, start + group_size)
        member_keys = keys_by_head[start:end]
        member_values = values_by_head[start:end]
        token_count = len(keys_by_head[head])
        shared_keys: Matrix = []
        shared_values: Matrix = []
        for token in range(token_count):
            shared_keys.append(_quantize_vector(_average_vectors([keys[token] for keys in member_keys]), kv_bits))
            shared_values.append(_quantize_vector(_average_vectors([values[token] for values in member_values]), kv_bits))
        out_keys.append(shared_keys)
        out_values.append(shared_values)
    return out_keys, out_values


def _attention_eval(
    *,
    keys_by_head: list[Matrix],
    values_by_head: list[Matrix],
    queries: list[Vector],
    targets: list[int],
) -> list[JsonDict]:
    rows: list[JsonDict] = []
    scale = 1.0 / math.sqrt(len(queries[0]))
    for head, query in enumerate(queries):
        logits = [_dot(query, key) * scale for key in keys_by_head[head]]
        weights = _softmax(logits)
        rows.append(
            {
                "head": head,
                "weights": weights,
                "top1": max(range(len(weights)), key=lambda index: weights[index]),
                "target": targets[head],
                "output": _weighted_sum(weights, values_by_head[head]),
            }
        )
    return rows


def _summarize_metrics(rows: list[JsonDict]) -> JsonDict:
    if not rows:
        return {}
    keys = ["top1_match", "kl_divergence", "output_cosine", "output_rmse"]
    out: JsonDict = {"sample_count": len(rows)}
    for key in keys:
        values = [float(row[key]) for row in rows]
        out[f"mean_{key}"] = round(sum(values) / len(values), 6)
        out[f"min_{key}"] = round(min(values), 6)
        out[f"max_{key}"] = round(max(values), 6)
    retrieval_rows = [row for row in rows if row.get("regime") in {"retrieval", "correlated_heads"}]
    retrieval_values = [float(row["retrieval_hit"]) for row in retrieval_rows] or [0.0]
    out["mean_retrieval_hit"] = round(sum(retrieval_values) / len(retrieval_values), 6)
    out["min_retrieval_hit"] = round(min(retrieval_values), 6)
    out["max_retrieval_hit"] = round(max(retrieval_values), 6)
    return out


def _decision(summary: JsonDict, *, kv_sharing: str, kv_bits: int) -> str:
    if kv_sharing == "mqa":
        return "bound_only_retraining_required"
    if kv_bits < 8:
        if summary["mean_top1_match"] >= 0.98 and summary["mean_output_cosine"] >= 0.995:
            return "quality_experiment_promising"
        return "quality_experiment_risky"
    if summary["mean_top1_match"] >= 0.99 and summary["mean_output_cosine"] >= 0.995:
        return "proxy_pass"
    return "proxy_risk_needs_model_native_eval"


def build_report(
    *,
    quality_gate: JsonDict | None,
    attention_heads: int,
    head_dim: int,
    sequence_length_list: list[int],
    regime_list: list[str],
    seed_count: int,
    candidate_specs: list[str],
) -> JsonDict:
    candidates: list[tuple[str, int, str]] = []
    for spec in candidate_specs:
        try:
            sharing, bits_text = spec.split(":kv", 1)
            bits = int(bits_text)
        except ValueError as exc:
            raise ValueError(f"candidate spec must look like gqa8:kv4, got {spec}") from exc
        candidates.append((sharing, bits, _candidate_id(kv_sharing=sharing, kv_bits=bits)))

    metric_rows: list[JsonDict] = []
    for sequence_length in sequence_length_list:
        for regime in regime_list:
            for seed in range(seed_count):
                rng = random.Random(0xA77E000 + sequence_length * 131 + seed * 17 + len(regime))
                keys, values, queries, targets = _generate_regime(
                    rng=rng,
                    regime=regime,
                    attention_heads=attention_heads,
                    sequence_length=sequence_length,
                    head_dim=head_dim,
                )
                reference = _attention_eval(
                    keys_by_head=keys,
                    values_by_head=values,
                    queries=queries,
                    targets=targets,
                )
                for kv_sharing, kv_bits, candidate_id in candidates:
                    cand_keys, cand_values = _apply_candidate_kv(
                        keys_by_head=keys,
                        values_by_head=values,
                        attention_heads=attention_heads,
                        kv_sharing=kv_sharing,
                        kv_bits=kv_bits,
                    )
                    candidate = _attention_eval(
                        keys_by_head=cand_keys,
                        values_by_head=cand_values,
                        queries=queries,
                        targets=targets,
                    )
                    for ref_row, cand_row in zip(reference, candidate):
                        metric_rows.append(
                            {
                                "candidate_id": candidate_id,
                                "kv_sharing": kv_sharing,
                                "kv_bits": kv_bits,
                                "sequence_length": sequence_length,
                                "regime": regime,
                                "seed": seed,
                                "head": ref_row["head"],
                                "top1_match": 1.0 if ref_row["top1"] == cand_row["top1"] else 0.0,
                                "retrieval_hit": 1.0 if cand_row["top1"] == ref_row["target"] else 0.0,
                                "kl_divergence": _kl_divergence(ref_row["weights"], cand_row["weights"]),
                                "output_cosine": _cosine(ref_row["output"], cand_row["output"]),
                                "output_rmse": _rmse(ref_row["output"], cand_row["output"]),
                            }
                        )

    candidate_summary: list[JsonDict] = []
    for kv_sharing, kv_bits, candidate_id in candidates:
        rows = [row for row in metric_rows if row["candidate_id"] == candidate_id]
        summary = _summarize_metrics(rows)
        summary.update(
            {
                "candidate_id": candidate_id,
                "kv_sharing": kv_sharing,
                "kv_bits": kv_bits,
                "decision": _decision(summary, kv_sharing=kv_sharing, kv_bits=kv_bits),
            }
        )
        candidate_summary.append(summary)

    regime_summary: list[JsonDict] = []
    for kv_sharing, kv_bits, candidate_id in candidates:
        for regime in regime_list:
            rows = [row for row in metric_rows if row["candidate_id"] == candidate_id and row["regime"] == regime]
            summary = _summarize_metrics(rows)
            summary.update(
                {
                    "candidate_id": candidate_id,
                    "kv_sharing": kv_sharing,
                    "kv_bits": kv_bits,
                    "regime": regime,
                    "decision": _decision(summary, kv_sharing=kv_sharing, kv_bits=kv_bits),
                }
            )
            regime_summary.append(summary)

    return {
        "version": 0.1,
        "model": "llm_decoder_attention_kv_quality_proxy_v1",
        "inputs": {
            "quality_gate_model": (quality_gate or {}).get("model", ""),
            "attention_heads": attention_heads,
            "head_dim": head_dim,
            "sequence_length_list": sequence_length_list,
            "regime_list": regime_list,
            "seed_count": seed_count,
            "candidate_specs": candidate_specs,
        },
        "sweep_summary": {
            "metric_row_count": len(metric_rows),
            "candidate_count": len(candidates),
        },
        "candidate_summary": sorted(candidate_summary, key=lambda row: row["candidate_id"]),
        "regime_summary": sorted(regime_summary, key=lambda row: (row["candidate_id"], row["regime"])),
        "metric_rows_sample": metric_rows[:100],
        "assumptions": [
            "This is a controlled attention proxy, not measured LLaMA perplexity.",
            "GQA/MQA are modeled as post-hoc K/V head averaging, which is intentionally pessimistic for non-native GQA/MQA models.",
            "KV quantization is symmetric per-vector packed quantization; scales are not learned.",
            "Retrieval regimes align a query with a target K/V entry to stress long-context top-1 preservation.",
            "A native GQA model or QAT run is still required before promoting GQA/KV4 or MQA candidates.",
        ],
    }


def _write_markdown(path: Path, payload: JsonDict) -> None:
    lines = [
        "# Decoder Attention/KV Quality Proxy",
        "",
        f"- model: `{payload['model']}`",
        f"- metric_row_count: `{payload['sweep_summary']['metric_row_count']}`",
        f"- candidates: `{payload['sweep_summary']['candidate_count']}`",
        "",
        "## Candidate Summary",
        "",
        "| candidate | top1 | retrieval | cosine | kl | decision |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for row in payload["candidate_summary"]:
        lines.append(
            "| {candidate} | {top1} | {retrieval} | {cosine} | {kl} | {decision} |".format(
                candidate=row["candidate_id"],
                top1=row["mean_top1_match"],
                retrieval=row["mean_retrieval_hit"],
                cosine=row["mean_output_cosine"],
                kl=row["mean_kl_divergence"],
                decision=row["decision"],
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
            "| {candidate} | {regime} | {top1} | {retrieval} | {cosine} | {kl} | {decision} |".format(
                candidate=row["candidate_id"],
                regime=row["regime"],
                top1=row["mean_top1_match"],
                retrieval=row["mean_retrieval_hit"],
                cosine=row["mean_output_cosine"],
                kl=row["mean_kl_divergence"],
                decision=row["decision"],
            )
        )
    lines.extend(["", "## Assumptions", ""])
    lines.extend(f"- {item}" for item in payload["assumptions"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--quality-gate")
    ap.add_argument("--attention-heads", type=int, default=32)
    ap.add_argument("--head-dim", type=int, default=32)
    ap.add_argument("--sequence-length-list", type=_int_list, default=[128, 512, 1024])
    ap.add_argument("--regime-list", type=_str_list, default=["correlated_heads", "retrieval", "low_margin", "independent_heads"])
    ap.add_argument("--seed-count", type=int, default=3)
    ap.add_argument("--candidate-spec-list", type=_str_list, default=["mha:kv8", "mha:kv4", "gqa8:kv8", "gqa8:kv4", "mqa:kv4"])
    ap.add_argument("--out", required=True)
    ap.add_argument("--out-md", required=True)
    args = ap.parse_args()

    quality_gate = json.loads(Path(args.quality_gate).read_text(encoding="utf-8")) if args.quality_gate else None
    payload = build_report(
        quality_gate=quality_gate,
        attention_heads=args.attention_heads,
        head_dim=args.head_dim,
        sequence_length_list=args.sequence_length_list,
        regime_list=args.regime_list,
        seed_count=args.seed_count,
        candidate_specs=args.candidate_spec_list,
    )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _write_markdown(Path(args.out_md), payload)
    print(json.dumps({"ok": True, "out": args.out, "out_md": args.out_md}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
