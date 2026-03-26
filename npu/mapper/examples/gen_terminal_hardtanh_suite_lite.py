#!/usr/bin/env python3
"""
Generate a bounded hardtanh-first terminal ONNX suite for Layer 2 direct-output work.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from onnx_lite import build_terminal_hardtanh_model_bytes  # noqa: E402


SUITE = [
    {
        "model_id": "hardtanh_vec_b128_f64",
        "batch": 128,
        "input_shape": [64],
        "add_flatten": False,
        "add_cast": False,
        "notes": "First-pass standalone terminal HardTanh on a 2D activation tensor.",
    },
    {
        "model_id": "hardtanh_vec_b256_f256",
        "batch": 256,
        "input_shape": [256],
        "add_flatten": False,
        "add_cast": False,
        "notes": "Larger standalone terminal HardTanh to increase writeback pressure.",
    },
    {
        "model_id": "hardtanh_vec_flatten_b128_2x4x8",
        "batch": 128,
        "input_shape": [2, 4, 8],
        "add_flatten": True,
        "add_cast": False,
        "notes": "Flatten -> HardTanh terminal vec-op to prove the prelude path stays legal.",
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
    ap = argparse.ArgumentParser(description="Generate a bounded terminal HardTanh ONNX suite.")
    ap.add_argument("--out-dir", required=True, help="Target directory for generated models.")
    ap.add_argument("--manifest", help="Optional manifest.json output path. Defaults to <out-dir>/manifest.json.")
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = Path(args.manifest) if args.manifest else out_dir / "manifest.json"

    models = []
    for spec in SUITE:
        model_path = out_dir / f"{spec['model_id']}.onnx"
        blob = build_terminal_hardtanh_model_bytes(
            name=spec["model_id"],
            b=spec["batch"],
            input_shape=list(spec["input_shape"]),
            add_flatten=bool(spec["add_flatten"]),
            add_cast=bool(spec["add_cast"]),
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
        "model_set_id": "onnx_terminal_hardtanh_suite_v1",
        "description": (
            "Locally generated bounded terminal HardTanh models used "
            "for the first HardTanh measurement-only Layer 2 mapper pass."
        ),
        "models": models,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"gen_terminal_hardtanh_suite_lite: wrote {len(models)} models to {out_dir}")
    print(f"gen_terminal_hardtanh_suite_lite: wrote manifest to {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
