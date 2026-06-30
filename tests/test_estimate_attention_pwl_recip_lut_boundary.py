#!/usr/bin/env python3

from __future__ import annotations

import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import npu.eval.estimate_attention_pwl_recip_lut_boundary as boundary


def _candidate(name: str, bits: int) -> boundary.Candidate:
    return boundary.Candidate(
        candidate_id=name,
        source=f"test:{name}",
        row_elems=8,
        score_bits=bits,
        weight_bits=bits,
        reciprocal_bits=bits,
        bucket_shift=8,
        accum_bits=max(24, bits + 8),
        softmax_impl="pwl_recip_lut",
    )


def test_boundary_estimator_separates_q12_q20_q24_direct_lut_sizes() -> None:
    payload = boundary.build_payload(
        [
            _candidate("q12", 12),
            _candidate("q20", 20),
            _candidate("q24", 24),
        ]
    )
    rows = {row["candidate_id"]: row for row in payload["candidate_rows"]}

    assert rows["q12"]["reciprocal_case_count"] == 128
    assert rows["q12"]["direct_lut_verdict"] == "direct_lut_ppa_reasonable"
    assert rows["q20"]["reciprocal_case_count"] == 32768
    assert rows["q20"]["direct_lut_verdict"] == "boundary_probe_only"
    assert rows["q24"]["reciprocal_case_count"] == 524288
    assert rows["q24"]["direct_lut_verdict"] == "requires_compact_reciprocal_before_ppa"
    assert payload["decision"] == "compact_reciprocal_required_for_widest_points"


def test_boundary_estimator_loads_composed_attention_config(tmp_path: Path) -> None:
    config = tmp_path / "design" / "config.json"
    config.parent.mkdir()
    config.write_text(
        json.dumps(
            {
                "top_name": "attention_q20_pwl",
                "attention_dual_stream_composed": {
                    "softmax_impl": "pwl_recip_lut",
                    "softmax_row_elems": 8,
                    "softmax_score_bits": 20,
                    "softmax_weight_bits": 20,
                    "reciprocal_bits": 20,
                    "softmax_reciprocal_lut_bucket_shift": 8,
                    "softmax_accum_bits": 32,
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )

    candidate = boundary._candidate_from_config(config)
    row = boundary.estimate_candidate(candidate)

    assert candidate.candidate_id == "attention_q20_pwl"
    assert row["reciprocal_case_count"] == 32768
    assert row["reciprocal_rom_bits"] == 32768 * 40


def test_report_mentions_guardrail_not_ppa_result() -> None:
    payload = boundary.build_payload([_candidate("q24", 24)])
    report = boundary._write_report_md(payload)

    assert "requires_compact_reciprocal_before_ppa" in report
    assert "not a PPA result" in report
