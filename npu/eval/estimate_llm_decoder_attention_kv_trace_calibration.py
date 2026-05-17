#!/usr/bin/env python3
"""Calibrate native GQA/KV4 proxy risk with trained-checkpoint KV trace stats."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

JsonDict = dict[str, Any]


def _load_json(path: str | Path) -> JsonDict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _percentile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = int(round((len(ordered) - 1) * q))
    return ordered[max(0, min(len(ordered) - 1, index))]


def _candidate_summary(native_gqa_proxy: JsonDict, candidate_id: str) -> JsonDict:
    for row in native_gqa_proxy.get("candidate_summary") or []:
        if row.get("candidate_id") == candidate_id:
            return dict(row)
    raise ValueError(f"native GQA proxy is missing candidate_summary row {candidate_id}")


def _regime_summary(native_gqa_proxy: JsonDict, candidate_id: str, regime: str) -> JsonDict:
    for row in native_gqa_proxy.get("regime_summary") or []:
        if row.get("candidate_id") == candidate_id and row.get("regime") == regime:
            return dict(row)
    return {}


def _trace_rows(quality_compare: JsonDict) -> list[JsonDict]:
    rows: list[JsonDict] = []
    for sample in quality_compare.get("samples") or []:
        sample_id = str(sample.get("sample_id") or "")
        trace = sample.get("selected_tensor_trace") or {}
        for tensor in trace.get("compared_tensors") or []:
            name = str(tensor.get("name") or "")
            if not name.startswith("present."):
                continue
            deltas = tensor.get("deltas") or {}
            quant = tensor.get("candidate_quantization") or {}
            rows.append(
                {
                    "sample_id": sample_id,
                    "name": name,
                    "kind": "key" if name.endswith(".key") else "value" if name.endswith(".value") else "other",
                    "mean_abs_delta": _float(deltas.get("mean_abs_delta")),
                    "max_abs_delta": _float(deltas.get("max_abs_delta")),
                    "std_abs_delta": _float(deltas.get("std_abs_delta")),
                    "quant_bits": int(_float(quant.get("bits"))),
                    "quant_scale": _float(quant.get("scale")),
                    "quant_max_abs": _float(quant.get("max_abs")),
                }
            )
    return rows


def _rollup_trace_rows(rows: list[JsonDict]) -> JsonDict:
    mean_abs = [_float(row.get("mean_abs_delta")) for row in rows]
    max_abs = [_float(row.get("max_abs_delta")) for row in rows]
    std_abs = [_float(row.get("std_abs_delta")) for row in rows]
    scales = [_float(row.get("quant_scale")) for row in rows if _float(row.get("quant_scale")) > 0.0]
    quant_max_abs = [_float(row.get("quant_max_abs")) for row in rows if _float(row.get("quant_max_abs")) > 0.0]
    key_rows = [row for row in rows if row.get("kind") == "key"]
    value_rows = [row for row in rows if row.get("kind") == "value"]
    return {
        "tensor_count": len(rows),
        "key_tensor_count": len(key_rows),
        "value_tensor_count": len(value_rows),
        "mean_of_mean_abs_delta": round(_mean(mean_abs), 9),
        "p95_of_mean_abs_delta": round(_percentile(mean_abs, 0.95), 9),
        "max_of_mean_abs_delta": round(max(mean_abs) if mean_abs else 0.0, 9),
        "mean_of_max_abs_delta": round(_mean(max_abs), 9),
        "p95_of_max_abs_delta": round(_percentile(max_abs, 0.95), 9),
        "max_of_max_abs_delta": round(max(max_abs) if max_abs else 0.0, 9),
        "mean_of_std_abs_delta": round(_mean(std_abs), 9),
        "max_of_std_abs_delta": round(max(std_abs) if std_abs else 0.0, 9),
        "mean_quant_scale": round(_mean(scales), 9),
        "p95_quant_scale": round(_percentile(scales, 0.95), 9),
        "max_quant_scale": round(max(scales) if scales else 0.0, 9),
        "p95_quant_max_abs": round(_percentile(quant_max_abs, 0.95), 9),
        "max_quant_max_abs": round(max(quant_max_abs) if quant_max_abs else 0.0, 9),
    }


def _quality_record(label: str, path: str, payload: JsonDict) -> JsonDict:
    aggregate = payload.get("aggregate") or {}
    trace_rows = _trace_rows(payload)
    distribution = aggregate.get("distribution") or {}
    return {
        "label": label,
        "path": path,
        "dataset_id": payload.get("dataset_id", ""),
        "candidate_semantics": payload.get("candidate_semantics", ""),
        "sample_count": int(aggregate.get("sample_count") or 0),
        "next_token_id_match_rate": _float(aggregate.get("next_token_id_match_rate")),
        "topk_contains_reference_id_rate": _float(aggregate.get("topk_contains_reference_id_rate")),
        "reference_top1_top2_logit_margin_min": _float(distribution.get("reference_top1_top2_logit_margin_min")),
        "reference_top1_top2_logit_margin_mean": _float(distribution.get("reference_top1_top2_logit_margin_mean")),
        "candidate_top1_top2_score_margin_min": _float(distribution.get("candidate_top1_top2_score_margin_min")),
        "candidate_top1_top2_score_margin_mean": _float(distribution.get("candidate_top1_top2_score_margin_mean")),
        "trace_rollup": _rollup_trace_rows(trace_rows),
    }


def _decision(*, native_kv4: JsonDict, native_low_margin: JsonDict, quality_records: list[JsonDict]) -> JsonDict:
    exact_quality = all(
        _float(row.get("next_token_id_match_rate")) >= 1.0
        and _float(row.get("topk_contains_reference_id_rate")) >= 1.0
        for row in quality_records
    )
    max_mean_delta = max((_float((row.get("trace_rollup") or {}).get("max_of_mean_abs_delta")) for row in quality_records), default=0.0)
    mean_mean_delta = max((_float((row.get("trace_rollup") or {}).get("mean_of_mean_abs_delta")) for row in quality_records), default=0.0)
    native_promising = str(native_kv4.get("decision")) == "native_lowbit_promising"
    low_margin_top1 = _float(native_low_margin.get("mean_top1_match"), 1.0)
    low_margin_cosine = _float(native_low_margin.get("mean_output_cosine"), 1.0)

    blockers: list[str] = []
    if not native_promising:
        blockers.append("native GQA8/KV4 proxy did not classify as low-bit promising")
    if not exact_quality:
        blockers.append("one or more trained-checkpoint prompt-stress controls lost exact next-token or top-k quality")
    if mean_mean_delta > 0.005:
        blockers.append("trained-checkpoint KV4 trace mean delta exceeds calibration threshold")
    if max_mean_delta > 0.03:
        blockers.append("trained-checkpoint KV4 trace max per-tensor mean delta exceeds calibration threshold")

    cautions: list[str] = []
    if low_margin_top1 < 0.99 or low_margin_cosine < 0.995:
        cautions.append("native low-margin synthetic regime remains sensitive and must be included in the next real-model dataset")
    if blockers:
        status = "hold_for_kv4_recovery"
        next_step = "Improve KV4 calibration or run a narrower outlier diagnosis before a model-native GQA experiment."
    else:
        status = "advance_model_native_gqa_kv4_quality_run"
        next_step = (
            "Schedule a real model-native or QAT GQA8/KV4 quality run; include low-margin and KV-outlier prompt regimes."
        )
    return {
        "status": status,
        "blockers": blockers,
        "cautions": cautions,
        "next_step": next_step,
        "thresholds": {
            "max_allowed_trace_mean_of_mean_abs_delta": 0.005,
            "max_allowed_trace_max_of_mean_abs_delta": 0.03,
            "native_low_margin_top1_caution_below": 0.99,
            "native_low_margin_cosine_caution_below": 0.995,
        },
    }


def build_report(
    *,
    native_gqa_proxy: JsonDict,
    quality_compare_inputs: list[tuple[str, str, JsonDict]],
) -> JsonDict:
    native_kv4 = _candidate_summary(native_gqa_proxy, "gqa8_kv4")
    native_kv8 = _candidate_summary(native_gqa_proxy, "gqa8_kv8")
    native_low_margin = _regime_summary(native_gqa_proxy, "gqa8_kv4", "native_low_margin")
    quality_records = [_quality_record(label, path, payload) for label, path, payload in quality_compare_inputs]
    decision = _decision(native_kv4=native_kv4, native_low_margin=native_low_margin, quality_records=quality_records)
    return {
        "version": 0.1,
        "model": "llm_decoder_attention_kv_trace_calibration_v1",
        "native_proxy": {
            "model": native_gqa_proxy.get("model", ""),
            "gqa8_kv4": native_kv4,
            "gqa8_kv8": native_kv8,
            "gqa8_kv4_low_margin": native_low_margin,
        },
        "trained_checkpoint_trace_records": quality_records,
        "decision": decision,
        "assumptions": [
            "The trained-checkpoint trace inputs are GPT-2-family MHA controls, not native GQA model quality.",
            "The trace calibration checks whether existing real-checkpoint KV4 tensor quantization error is in-family with the synthetic native GQA/KV4 proxy.",
            "A pass only schedules a model-native or QAT GQA8/KV4 quality run; it does not promote GQA8/KV4 as deployable.",
        ],
    }


def _write_markdown(path: Path, payload: JsonDict) -> None:
    lines = [
        "# Decoder Attention/KV Trace Calibration",
        "",
        f"- model: `{payload['model']}`",
        f"- decision: `{payload['decision']['status']}`",
        f"- next_step: {payload['decision']['next_step']}",
        "",
        "## Native Proxy",
        "",
        "| candidate | decision | top1 | cosine | rmse |",
        "|---|---|---:|---:|---:|",
    ]
    for key in ("gqa8_kv8", "gqa8_kv4"):
        row = payload["native_proxy"][key]
        lines.append(
            "| {candidate} | {decision} | {top1} | {cosine} | {rmse} |".format(
                candidate=row["candidate_id"],
                decision=row["decision"],
                top1=row["mean_top1_match"],
                cosine=row["mean_output_cosine"],
                rmse=row["mean_output_rmse"],
            )
        )
    low = payload["native_proxy"].get("gqa8_kv4_low_margin") or {}
    lines.extend(
        [
            "",
            "## Low-Margin Native Regime",
            "",
            f"- gqa8_kv4 low-margin top1: `{low.get('mean_top1_match', 0)}`",
            f"- gqa8_kv4 low-margin cosine: `{low.get('mean_output_cosine', 0)}`",
            "",
            "## Trained-Checkpoint KV4 Trace Controls",
            "",
            "| label | samples | next | topk | tensors | mean_delta | max_tensor_mean_delta | p95_scale | max_abs |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in payload["trained_checkpoint_trace_records"]:
        trace = row["trace_rollup"]
        lines.append(
            "| {label} | {samples} | {next_rate} | {topk_rate} | {tensors} | {mean_delta} | {max_mean_delta} | {p95_scale} | {max_abs} |".format(
                label=row["label"],
                samples=row["sample_count"],
                next_rate=row["next_token_id_match_rate"],
                topk_rate=row["topk_contains_reference_id_rate"],
                tensors=trace["tensor_count"],
                mean_delta=trace["mean_of_mean_abs_delta"],
                max_mean_delta=trace["max_of_mean_abs_delta"],
                p95_scale=trace["p95_quant_scale"],
                max_abs=trace["max_quant_max_abs"],
            )
        )
    lines.extend(["", "## Cautions", ""])
    cautions = payload["decision"]["cautions"] or ["none"]
    lines.extend(f"- {item}" for item in cautions)
    lines.extend(["", "## Assumptions", ""])
    lines.extend(f"- {item}" for item in payload["assumptions"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _parse_quality_compare_arg(value: str) -> tuple[str, str]:
    if "=" in value:
        label, path = value.split("=", 1)
        return label.strip(), path.strip()
    path = value.strip()
    return Path(path).stem, path


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--native-gqa-proxy", required=True)
    ap.add_argument("--quality-compare", action="append", required=True, help="label=path to decoder quality compare JSON")
    ap.add_argument("--out", required=True)
    ap.add_argument("--out-md", required=True)
    args = ap.parse_args()

    quality_inputs = []
    for raw in args.quality_compare:
        label, path = _parse_quality_compare_arg(raw)
        quality_inputs.append((label, path, _load_json(path)))
    payload = build_report(native_gqa_proxy=_load_json(args.native_gqa_proxy), quality_compare_inputs=quality_inputs)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _write_markdown(Path(args.out_md), payload)
    print(json.dumps({"ok": True, "out": args.out, "out_md": args.out_md}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
