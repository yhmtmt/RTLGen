#!/usr/bin/env python3
import argparse
import json
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
    if cfg["impl"] != "shift_exp":
        raise SystemExit(f"unsupported impl: {cfg['impl']}")

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
                "output": compute_shift_exp_row(
                    values,
                    max_shift=cfg["max_shift"],
                    output_scale=cfg["output_scale"],
                    normalization_mode=cfg["normalization_mode"],
                    reciprocal_bits=cfg["reciprocal_bits"],
                    reciprocal_lut_bucket_shift=cfg["reciprocal_lut_bucket_shift"],
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
