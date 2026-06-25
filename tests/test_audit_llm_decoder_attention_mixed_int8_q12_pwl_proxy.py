#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.eval.audit_llm_decoder_attention_mixed_int8_q12_pwl_proxy import (  # noqa: E402
    _build_payload,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _args(tmp_path: Path) -> argparse.Namespace:
    return argparse.Namespace(
        q12_pwl_native_quality_json=tmp_path / "q12_quality.json",
        quality_backed_frontier_json=tmp_path / "frontier.json",
        composed_q12_pwl_metrics=tmp_path / "composed.csv",
        full_value_v8_metrics=tmp_path / "fullv8.csv",
        out=tmp_path / "out.json",
        out_md=tmp_path / "out.md",
    )


def test_hold_native_quality_status_no_longer_allows_quality_backed_proxy(tmp_path: Path) -> None:
    args = _args(tmp_path)
    _write_json(
        args.q12_pwl_native_quality_json,
        {
            "candidate_summaries": [
                {
                    "candidate_id": "qkv8_q12_pwl_recip_q12_bucket8",
                    "decision_status": "mixed_int8_native_attention_shadow_hold",
                    "top1_match_rate": 1.0,
                    "topk_contains_rate": 1.0,
                }
            ]
        },
    )
    _write_json(
        args.quality_backed_frontier_json,
        {
            "quality_backed_direction": {
                "candidate_id": "qkv8_float_exact",
                "decision_status": "mixed_int8_native_attention_shadow_pass",
            }
        },
    )

    payload = _build_payload(args)

    assert payload["decision"]["status"] == "q12_pwl_proxy_quality_rejected"
    assert payload["q12_pwl_quality"]["proxy_pass"] is False
    assert payload["q12_pwl_quality"]["quality_passed"] is False
