#!/usr/bin/env python3
"""
Generate the llm_practical_scale_v1 ONNX-lite benchmark suite.
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
        "model_id": "practical_scale_attn6_s64_h64_kv1024",
        "active_tokens": 64,
        "hidden_dim": 64,
        "num_blocks": 6,
        "kv_context_tokens": 1024,
        "notes": "Scale step: 64 active tokens over a 1024-token KV context with six attention episodes.",
    },
    {
        "model_id": "practical_scale_attn8_s64_h64_kv1024",
        "active_tokens": 64,
        "hidden_dim": 64,
        "num_blocks": 8,
        "kv_context_tokens": 1024,
        "notes": "More repeated attention pressure at the same active-token and KV-context size.",
    },
    {
        "model_id": "practical_scale_attn6_s64_h64_kv2048",
        "active_tokens": 64,
        "hidden_dim": 64,
        "num_blocks": 6,
        "kv_context_tokens": 2048,
        "notes": "Wider KV-context pressure point: 64 active tokens over a 2048-token KV context.",
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
    ap = argparse.ArgumentParser(description="Generate the llm_practical_scale_v1 ONNX-lite suite.")
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
        active_tokens = int(spec["active_tokens"])
        hidden_dim = int(spec["hidden_dim"])
        num_blocks = int(spec["num_blocks"])
        kv_context_tokens = int(spec["kv_context_tokens"])
        blob = build_attention_block_model_bytes(
            name=spec["model_id"],
            seq_len=active_tokens,
            hidden_dim=hidden_dim,
            num_blocks=num_blocks,
            score_dim=kv_context_tokens,
            dtype=3,
        )
        model_path.write_bytes(blob)
        models.append(
            {
                "model_id": spec["model_id"],
                "onnx_path": _repo_friendly(model_path),
                "onnx_sha256": _sha256(model_path),
                "active_tokens": active_tokens,
                "seq_len": active_tokens,
                "hidden_dim": hidden_dim,
                "num_blocks": num_blocks,
                "softmax_episode_count": num_blocks,
                "kv_context_tokens": kv_context_tokens,
                "score_dim": kv_context_tokens,
                "kv_cache_proxy_bytes": kv_context_tokens * hidden_dim * 2,
                "notes": spec["notes"],
            }
        )

    manifest = {
        "version": 0.1,
        "model_set_id": "llm_practical_scale_v1",
        "description": (
            "Locally generated decoder-style scale proxy set that extends "
            "llm_practical_v1 from 32 active tokens / 512 KV-context tokens to "
            "64 active tokens and 1024-2048 KV-context score dimensions. This "
            "tests whether larger LLM-like attention pressure changes the nm1 "
            "vs nm2 PPA trend before opening a wider compute-array proposal."
        ),
        "models": models,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"gen_llm_practical_scale_suite_lite: wrote {len(models)} models to {out_dir}")
    print(f"gen_llm_practical_scale_suite_lite: wrote manifest to {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
