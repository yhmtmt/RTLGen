#!/usr/bin/env python3
"""
Generate a small imported-style Softmax-tail ONNX suite without external deps.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from onnx_lite import build_softmax_classifier_model_bytes  # noqa: E402


SUITE = [
    {
        "model_id": "softmax_cls_b128_i8_o16",
        "batch": 128,
        "input_dim": 8,
        "out_dim": 16,
        "notes": "Imported-style Cast -> Gemm -> Softmax tail with modest class count.",
    },
    {
        "model_id": "softmax_cls_b256_i8_o64",
        "batch": 256,
        "input_dim": 8,
        "out_dim": 64,
        "notes": "Higher output-width terminal Softmax tail to amplify output traffic.",
    },
    {
        "model_id": "softmax_cls_b128_i4_o128",
        "batch": 128,
        "input_dim": 4,
        "out_dim": 128,
        "notes": "Very class-heavy terminal Softmax tail with small input dimension.",
    },
]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _repo_friendly(path: Path) -> str:
    try:
        return path.resolve().relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate a small Softmax-tail ONNX suite.")
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
        blob = build_softmax_classifier_model_bytes(
            name=spec["model_id"],
            b=spec["batch"],
            input_dim=spec["input_dim"],
            out_dim=spec["out_dim"],
            add_cast=True,
            add_label_output=True,
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
        "model_set_id": "onnx_terminal_softmax_suite_v1",
        "description": (
            "Locally generated imported-style Softmax-tail models used for "
            "terminal-output-sensitive measurement-first evaluation."
        ),
        "models": models,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"gen_softmax_classifier_suite_lite: wrote {len(models)} models to {out_dir}")
    print(f"gen_softmax_classifier_suite_lite: wrote manifest to {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
