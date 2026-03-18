#!/usr/bin/env python3
"""
Generate a small terminal-output ONNX suite for measurement-first mapper work.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from onnx_lite import build_gemm_mlp_model_bytes  # noqa: E402


SUITE = [
    {
        "model_id": "linear_tail_b128_f8_o64",
        "batch": 128,
        "input_shape": [2, 4],
        "hidden_dims": [],
        "out_dim": 64,
        "final_relu": False,
        "notes": "Flatten -> Gemm terminal linear output with modest output width.",
    },
    {
        "model_id": "linear_tail_b256_f8_o128",
        "batch": 256,
        "input_shape": [2, 4],
        "hidden_dims": [],
        "out_dim": 128,
        "final_relu": False,
        "notes": "Flatten -> Gemm terminal linear output with heavier writeback pressure.",
    },
    {
        "model_id": "relu_tail_b128_f8_o128",
        "batch": 128,
        "input_shape": [2, 4],
        "hidden_dims": [],
        "out_dim": 128,
        "final_relu": True,
        "notes": "Flatten -> Gemm -> Relu terminal output accepted by the current mapper for measurement-first baseline collection.",
    },
]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _repo_friendly(path: Path) -> str:
    repo_root = Path(__file__).resolve().parents[3]
    try:
        return path.resolve().relative_to(repo_root).as_posix()
    except ValueError:
        return path.as_posix()


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate a terminal direct-output ONNX suite.")
    ap.add_argument("--out-dir", required=True, help="Target directory for generated models.")
    ap.add_argument(
        "--manifest",
        help="Optional manifest.json output path. Defaults to <out-dir>/manifest.json.",
    )
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = Path(args.manifest) if args.manifest else out_dir / "manifest.json"

    models = []
    for spec in SUITE:
        model_path = out_dir / f"{spec['model_id']}.onnx"
        blob = build_gemm_mlp_model_bytes(
            name=spec["model_id"],
            b=spec["batch"],
            input_shape=list(spec["input_shape"]),
            hidden_dims=list(spec["hidden_dims"]),
            out_dim=spec["out_dim"],
            final_relu=bool(spec["final_relu"]),
        )
        model_path.write_bytes(blob)
        models.append(
            {
                "model_id": spec["model_id"],
                "onnx_path": _repo_friendly(model_path),
                "onnx_sha256": _sha256(model_path),
                "notes": spec["notes"],
            }
        )

    manifest = {
        "version": 0.1,
        "model_set_id": "onnx_terminal_direct_output_suite_v1",
        "description": (
            "Locally generated terminal linear and terminal ReLU models used "
            "for measurement-first direct-output mapper generalization."
        ),
        "models": models,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"gen_terminal_direct_output_suite_lite: wrote {len(models)} models to {out_dir}")
    print(f"gen_terminal_direct_output_suite_lite: wrote manifest to {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
