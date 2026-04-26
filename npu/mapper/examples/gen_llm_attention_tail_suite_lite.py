#!/usr/bin/env python3
"""
Generate the llm_attention_tail_v1 ONNX-lite benchmark suite.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from onnx_lite import build_attention_block_model_bytes  # noqa: E402


SUITE = [
    {
        "model_id": "tail_attn2_s32_h64",
        "seq_len": 32,
        "hidden_dim": 64,
        "num_blocks": 2,
        "notes": "Two attention-tail proxy blocks at the smoke-suite base sequence length.",
    },
    {
        "model_id": "tail_attn2_s64_h64",
        "seq_len": 64,
        "hidden_dim": 64,
        "num_blocks": 2,
        "notes": "Two repeated softmax-bearing blocks with longer sequence pressure.",
    },
    {
        "model_id": "tail_attn3_s64_h64",
        "seq_len": 64,
        "hidden_dim": 64,
        "num_blocks": 3,
        "notes": "Three repeated blocks to expose queueing and overlap behavior in one path.",
    },
    {
        "model_id": "tail_attn4_s64_h64",
        "seq_len": 64,
        "hidden_dim": 64,
        "num_blocks": 4,
        "notes": "Four repeated blocks for softmax occupancy and backpressure sensitivity.",
    },
    {
        "model_id": "tail_attn4_s128_h64",
        "seq_len": 128,
        "hidden_dim": 64,
        "num_blocks": 4,
        "notes": "Largest bounded tail slice with sequence length 128 and four softmax episodes.",
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
    ap = argparse.ArgumentParser(description="Generate the llm_attention_tail_v1 ONNX-lite suite.")
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
        blob = build_attention_block_model_bytes(
            name=spec["model_id"],
            seq_len=int(spec["seq_len"]),
            hidden_dim=int(spec["hidden_dim"]),
            num_blocks=int(spec["num_blocks"]),
            dtype=3,
        )
        model_path.write_bytes(blob)
        models.append(
            {
                "model_id": spec["model_id"],
                "onnx_path": _repo_friendly(model_path),
                "onnx_sha256": _sha256(model_path),
                "seq_len": int(spec["seq_len"]),
                "hidden_dim": int(spec["hidden_dim"]),
                "num_blocks": int(spec["num_blocks"]),
                "softmax_episode_count": int(spec["num_blocks"]),
                "notes": spec["notes"],
            }
        )

    manifest = {
        "version": 0.1,
        "model_set_id": "llm_attention_tail_v1",
        "description": (
            "Locally generated repeated attention-tail ONNX-lite proxy set used "
            "to expose sequence-length pressure, repeated non-terminal Softmax "
            "episodes, queue stalls, and overlap behavior."
        ),
        "models": models,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"gen_llm_attention_tail_suite_lite: wrote {len(models)} models to {out_dir}")
    print(f"gen_llm_attention_tail_suite_lite: wrote manifest to {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
