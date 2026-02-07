#!/usr/bin/env python3
"""
Generate tiny MLP ONNX models for the RTLGen minimal NPU demo.

No external Python deps are required; this uses `npu/mapper/onnx_lite.py`.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from onnx_lite import write_mlp_model  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate a tiny MLP ONNX model (lite).")
    ap.add_argument(
        "--preset",
        required=True,
        choices=["mlp1", "mlp2"],
        help="Model preset (MLP-1 or MLP-2)",
    )
    ap.add_argument("--out", required=True, help="Output path (*.onnx)")
    args = ap.parse_args()

    out_path = Path(args.out)
    write_mlp_model(out_path, preset=args.preset)
    print(f"gen_mlp_onnx_lite: wrote {args.preset} to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
