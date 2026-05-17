#!/usr/bin/env python3
"""Proxy-test native GQA/MQA KV quantization against same-sharing KV16 references."""

from __future__ import annotations

import argparse
import json
import math
import random
from pathlib import Path
from typing import Any

try:
    from npu.eval.estimate_llm_decoder_attention_kv_quality_proxy import (
        JsonDict,
        Matrix,
        Vector,
        _attention_eval,
        _candidate_id,
        _cosine,
        _int_list,
        _kl_divergence,
        _quantize_vector,
        _rmse,
        _str_list,
    )
except ModuleNotFoundError:
    from estimate_llm_decoder_attention_kv_quality_proxy import (  # type: ignore
        JsonDict,
        Matrix,
        Vector,
        _attention_eval,
        _candidate_id,
        _cosine,
        _int_list,
        _kl_divergence,
        _quantize_vector,
        _rmse,
        _str_list,
    )


def _kv_group_count(*, attention_heads: int, kv_sharing: str) -> int:
    if kv_sharing == "gqa4":
        return max(1, math.ceil(attention_heads / 4))
    if kv_sharing == "gqa8":
        return max(1, math.ceil(attention_heads / 8))
    if kv_sharing == "mqa":
        return 1
    raise ValueError(f"native GQA proxy supports gqa4, gqa8, and mqa; got {kv_sharing}")


def _generate_native_shared_kv(
    *,
    rng: random.Random,
    regime: str,
    attention_heads: int,
    sequence_length: int,
    head_dim: int,
    kv_sharing: str,
) -> tuple[list[Matrix], list[Matrix], list[Vector], list[int]]:
    kv_groups = _kv_group_count(attention_heads=attention_heads, kv_sharing=kv_sharing)
    group_size = math.ceil(attention_heads / kv_groups)
    group_keys = [
        [[rng.gauss(0.0, 1.0) for _ in range(head_dim)] for _ in range(sequence_length)]
        for _ in range(kv_groups)
    ]
    group_values = [
        [[rng.gauss(0.0, 1.0) for _ in range(head_dim)] for _ in range(sequence_length)]
        for _ in range(kv_groups)
    ]
    keys_by_head: list[Matrix] = []
    values_by_head: list[Matrix] = []
    queries: list[Vector] = []
    targets: list[int] = []
    for head in range(attention_heads):
        group = min(kv_groups - 1, head // group_size)
        keys = group_keys[group]
        values = group_values[group]
        if regime == "native_retrieval":
            target = (31 * head + 7 * group + 5) % sequence_length
            query = [2.3 * value + rng.gauss(0.0, 0.12) for value in keys[target]]
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
        else:
            raise ValueError(f"unsupported native regime: {regime}")
        keys_by_head.append(keys)
        values_by_head.append(values)
        queries.append(query)
        targets.append(target)
    return keys_by_head, values_by_head, queries, targets


def _quantize_kv(keys: list[Matrix], values: list[Matrix], *, kv_bits: int) -> tuple[list[Matrix], list[Matrix]]:
    return (
        [[_quantize_vector(vector, kv_bits) for vector in head] for head in keys],
        [[_quantize_vector(vector, kv_bits) for vector in head] for head in values],
    )


def _summarize(rows: list[JsonDict]) -> JsonDict:
    out: JsonDict = {"sample_count": len(rows)}
    for key in ("top1_match", "retrieval_hit", "kl_divergence", "output_cosine", "output_rmse"):
        values = [float(row[key]) for row in rows]
        out[f"mean_{key}"] = round(sum(values) / len(values), 6) if values else 0.0
        out[f"min_{key}"] = round(min(values), 6) if values else 0.0
        out[f"max_{key}"] = round(max(values), 6) if values else 0.0
    return out


def _decision(summary: JsonDict, *, kv_sharing: str, kv_bits: int) -> str:
    if kv_sharing == "mqa":
        return "native_mqa_still_requires_model_evidence"
    if kv_bits >= 8 and summary["mean_top1_match"] >= 0.995 and summary["mean_output_cosine"] >= 0.999:
        return "native_proxy_pass"
    if kv_bits < 8 and summary["mean_top1_match"] >= 0.98 and summary["mean_output_cosine"] >= 0.995:
        return "native_lowbit_promising"
    return "native_proxy_risk"


def _parse_candidate_specs(candidate_specs: list[str]) -> list[tuple[str, int, str]]:
    out: list[tuple[str, int, str]] = []
    for spec in candidate_specs:
        try:
            sharing, bits_text = spec.split(":kv", 1)
            bits = int(bits_text)
        except ValueError as exc:
            raise ValueError(f"candidate spec must look like gqa8:kv4, got {spec}") from exc
        out.append((sharing, bits, _candidate_id(kv_sharing=sharing, kv_bits=bits)))
    return out


def build_report(
    *,
    quality_proxy: JsonDict | None,
    attention_heads: int,
    head_dim: int,
    sequence_length_list: list[int],
    regime_list: list[str],
    seed_count: int,
    candidate_specs: list[str],
) -> JsonDict:
    candidates = _parse_candidate_specs(candidate_specs)
    metric_rows: list[JsonDict] = []
    for sequence_length in sequence_length_list:
        for regime in regime_list:
            for seed in range(seed_count):
                for kv_sharing, kv_bits, candidate_id in candidates:
                    rng = random.Random(
                        0xB47A000
                        + sequence_length * 131
                        + seed * 17
                        + len(regime) * 19
                        + sum(ord(ch) for ch in kv_sharing)
                    )
                    keys, values, queries, targets = _generate_native_shared_kv(
                        rng=rng,
                        regime=regime,
                        attention_heads=attention_heads,
                        sequence_length=sequence_length,
                        head_dim=head_dim,
                        kv_sharing=kv_sharing,
                    )
                    reference = _attention_eval(
                        keys_by_head=keys,
                        values_by_head=values,
                        queries=queries,
                        targets=targets,
                    )
                    cand_keys, cand_values = _quantize_kv(keys, values, kv_bits=kv_bits)
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
        summary = _summarize(rows)
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
            summary = _summarize(rows)
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
        "model": "llm_decoder_attention_kv_native_gqa_proxy_v1",
        "inputs": {
            "quality_proxy_model": (quality_proxy or {}).get("model", ""),
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
            "This is a native-sharing proxy, not measured LLaMA perplexity.",
            "Each candidate is compared against a same-sharing KV16 reference, so GQA is not penalized for differing from MHA.",
            "KV8 and KV4 use symmetric per-vector packed quantization without learned scales.",
            "Passing this proxy only justifies a model-native GQA or QAT evaluation; it does not promote a final hardware format.",
        ],
    }


def _write_markdown(path: Path, payload: JsonDict) -> None:
    lines = [
        "# Decoder Attention/KV Native GQA Proxy",
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
    ap.add_argument("--quality-proxy")
    ap.add_argument("--attention-heads", type=int, default=32)
    ap.add_argument("--head-dim", type=int, default=32)
    ap.add_argument("--sequence-length-list", type=_int_list, default=[128, 512])
    ap.add_argument("--regime-list", type=_str_list, default=["native_correlated_queries", "native_retrieval", "native_low_margin"])
    ap.add_argument("--seed-count", type=int, default=2)
    ap.add_argument("--candidate-spec-list", type=_str_list, default=["gqa8:kv8", "gqa8:kv4", "mqa:kv8", "mqa:kv4"])
    ap.add_argument("--out", required=True)
    ap.add_argument("--out-md", required=True)
    args = ap.parse_args()

    quality_proxy = json.loads(Path(args.quality_proxy).read_text(encoding="utf-8")) if args.quality_proxy else None
    payload = build_report(
        quality_proxy=quality_proxy,
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
