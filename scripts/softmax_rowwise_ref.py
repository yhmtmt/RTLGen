#!/usr/bin/env python3
import argparse
import json
import math
from pathlib import Path


def _load_config(path: str) -> dict:
    doc = json.loads(Path(path).read_text(encoding="utf-8"))
    operations = doc.get("operations", [])
    if len(operations) != 1 or operations[0].get("type") != "softmax_rowwise":
        raise ValueError("config must contain exactly one softmax_rowwise operation")
    opts = operations[0].get("options", {})
    return {
        "module_name": operations[0]["module_name"],
        "impl": str(opts.get("impl", "shift_exp")),
        "normalization_mode": str(opts.get("normalization_mode", "exact")),
        "reciprocal_bits": int(opts.get("reciprocal_bits", 0)),
        "reciprocal_lut_bucket_shift": int(opts.get("reciprocal_lut_bucket_shift", 0)),
        "row_elems": int(opts.get("row_elems", 1)),
        "max_shift": int(opts.get("max_shift", 7)),
        "input_frac_bits": int(opts.get("input_frac_bits", 0)),
        "weight_bits": int(opts.get("weight_bits", 0)),
        "accum_bits": int(opts.get("accum_bits", 16)),
        "output_scale": int(opts.get("output_scale", 127)),
    }


def compute_shift_exp_row(
    logits,
    *,
    max_shift: int = 7,
    output_scale: int = 127,
    normalization_mode: str = "exact",
    reciprocal_bits: int = 0,
    reciprocal_lut_bucket_shift: int = 0,
):
    if not logits:
        return []
    max_val = max(int(v) for v in logits)
    weights = []
    for value in logits:
        delta = max_val - int(value)
        if delta < 0:
            delta = 0
        if delta > max_shift:
            delta = max_shift
        weights.append(1 << (max_shift - delta))
    sum_weights = sum(weights)
    if sum_weights <= 0:
        return [0 for _ in logits]
    out = []
    reciprocal = None
    if normalization_mode == "reciprocal_quantized":
        if reciprocal_bits <= 0:
            raise ValueError("reciprocal_bits must be positive for reciprocal_quantized")
        if reciprocal_lut_bucket_shift > 0:
            bucket = (sum_weights + ((1 << reciprocal_lut_bucket_shift) - 1)) >> reciprocal_lut_bucket_shift
            approx_sum = max(1, bucket << reciprocal_lut_bucket_shift)
        else:
            approx_sum = sum_weights
        reciprocal = ((output_scale << reciprocal_bits) + (approx_sum // 2)) // approx_sum
    elif normalization_mode != "exact":
        raise ValueError(f"unsupported normalization_mode: {normalization_mode}")
    for weight in weights:
        if reciprocal is None:
            quantized = ((weight * output_scale) + (sum_weights // 2)) // sum_weights
        else:
            quantized = ((weight * reciprocal) + (1 << (reciprocal_bits - 1))) >> reciprocal_bits
        if quantized < 0:
            quantized = 0
        if quantized > output_scale:
            quantized = output_scale
        out.append(int(quantized))
    return out


def compute_pwl_exp_row(
    logits,
    *,
    input_frac_bits: int = 0,
    weight_bits: int = 8,
    output_scale: int = 127,
    normalization_mode: str = "exact",
    reciprocal_bits: int = 0,
    reciprocal_lut_bucket_shift: int = 0,
):
    if not logits:
        return []
    if input_frac_bits < 0:
        raise ValueError("input_frac_bits must be non-negative")
    if weight_bits <= 0:
        raise ValueError("weight_bits must be positive")
    max_val = max(int(v) for v in logits)
    input_scale = 1 << input_frac_bits
    def round_half_up(value: float) -> int:
        return int(math.floor(value + 0.5))

    anchors = [
        (0, (1 << weight_bits) - 1),
        (2 * input_scale, round_half_up(math.exp(-2.0) * ((1 << weight_bits) - 1))),
        (4 * input_scale, round_half_up(math.exp(-4.0) * ((1 << weight_bits) - 1))),
        (8 * input_scale, round_half_up(math.exp(-8.0) * ((1 << weight_bits) - 1))),
    ]

    def pwl_weight(delta: int) -> int:
        if delta < 0:
            delta = 0
        if delta > anchors[-1][0]:
            return 0
        if delta == anchors[-1][0]:
            return int(anchors[-1][1])
        for (x0, y0), (x1, y1) in zip(anchors, anchors[1:]):
            if delta <= x1:
                seg_width = x1 - x0
                interp = ((delta - x0) * (y0 - y1) + (seg_width // 2)) // seg_width
                return max(0, int(y0 - interp))
        return 0

    weights = [pwl_weight(max_val - int(value)) for value in logits]
    sum_weights = sum(weights)
    if sum_weights <= 0:
        return [0 for _ in logits]
    out = []
    reciprocal = None
    if normalization_mode == "reciprocal_quantized":
        if reciprocal_bits <= 0:
            raise ValueError("reciprocal_bits must be positive for reciprocal_quantized")
        if reciprocal_lut_bucket_shift > 0:
            bucket = (sum_weights + ((1 << reciprocal_lut_bucket_shift) - 1)) >> reciprocal_lut_bucket_shift
            approx_sum = max(1, bucket << reciprocal_lut_bucket_shift)
        else:
            approx_sum = sum_weights
        reciprocal = ((output_scale << reciprocal_bits) + (approx_sum // 2)) // approx_sum
    elif normalization_mode != "exact":
        raise ValueError(f"unsupported normalization_mode: {normalization_mode}")
    for weight in weights:
        if reciprocal is None:
            quantized = ((weight * output_scale) + (sum_weights // 2)) // sum_weights
        else:
            quantized = ((weight * reciprocal) + (1 << (reciprocal_bits - 1))) >> reciprocal_bits
        if quantized < 0:
            quantized = 0
        if quantized > output_scale:
            quantized = output_scale
        out.append(int(quantized))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Reference model for Layer-1 softmax_rowwise candidates.")
    ap.add_argument("--config", required=True, help="Path to softmax_rowwise config JSON")
    ap.add_argument(
        "--row",
        action="append",
        required=True,
        help="Comma-separated signed integer logits for one row; pass multiple times for multiple rows",
    )
    args = ap.parse_args()

    cfg = _load_config(args.config)
    if cfg["impl"] not in {"shift_exp", "pwl_exp"}:
        raise SystemExit(f"unsupported impl: {cfg['impl']}")
    weight_bits = cfg["weight_bits"]
    if weight_bits == 0:
        operands = json.loads(Path(args.config).read_text(encoding="utf-8")).get("operands", [])
        weight_bits = int(operands[0].get("bit_width", 8)) if operands else 8

    rows = []
    for raw_row in args.row:
        values = [int(token.strip(), 0) for token in raw_row.split(",") if token.strip()]
        if len(values) != cfg["row_elems"]:
            raise SystemExit(
                f"row length mismatch: expected {cfg['row_elems']} values, got {len(values)} for {raw_row!r}"
            )
        rows.append(
            {
                "input": values,
                "output": (
                    compute_shift_exp_row(
                        values,
                        max_shift=cfg["max_shift"],
                        output_scale=cfg["output_scale"],
                        normalization_mode=cfg["normalization_mode"],
                        reciprocal_bits=cfg["reciprocal_bits"],
                        reciprocal_lut_bucket_shift=cfg["reciprocal_lut_bucket_shift"],
                    )
                    if cfg["impl"] == "shift_exp"
                    else compute_pwl_exp_row(
                        values,
                        input_frac_bits=cfg["input_frac_bits"],
                        weight_bits=weight_bits,
                        output_scale=cfg["output_scale"],
                        normalization_mode=cfg["normalization_mode"],
                        reciprocal_bits=cfg["reciprocal_bits"],
                        reciprocal_lut_bucket_shift=cfg["reciprocal_lut_bucket_shift"],
                    )
                ),
            }
        )

    print(
        json.dumps(
            {
                "module_name": cfg["module_name"],
                "impl": cfg["impl"],
                "normalization_mode": cfg["normalization_mode"],
                "reciprocal_bits": cfg["reciprocal_bits"],
                "reciprocal_lut_bucket_shift": cfg["reciprocal_lut_bucket_shift"],
                "row_elems": cfg["row_elems"],
                "max_shift": cfg["max_shift"],
                "input_frac_bits": cfg["input_frac_bits"],
                "weight_bits": weight_bits,
                "accum_bits": cfg["accum_bits"],
                "output_scale": cfg["output_scale"],
                "rows": rows,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
