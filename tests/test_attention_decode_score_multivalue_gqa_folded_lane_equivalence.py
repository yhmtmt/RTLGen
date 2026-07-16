from __future__ import annotations

import json
from pathlib import Path

import pytest

from npu.eval.audit_attention_decode_score_multivalue_gqa_folded_lane_equivalence import (
    _render_markdown,
    build_report,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


def _configs() -> list[tuple[str, dict]]:
    design_root = REPO_ROOT / "runs" / "designs" / "npu_blocks"
    names = {
        1: "attention_decode_score_multivalue_gqa_group_lanes1_int8_m1x8_iterdiv",
        2: "attention_decode_score_multivalue_gqa_group_lanes2_int8_m1x8_iterdiv",
        4: "attention_decode_score_multivalue_gqa_group_lanes4_int8_m1x8_iterdiv",
        8: "attention_decode_score_multivalue_gqa_group_int8_m1x8_iterdiv",
    }
    rows = []
    for lanes, name in names.items():
        path = design_root / name / "config.json"
        rows.append((str(path.relative_to(REPO_ROOT)), json.loads(path.read_text(encoding="utf-8"))))
    return rows


@pytest.fixture(scope="module")
def report() -> dict:
    return build_report(_configs())


def test_folded_lane_direct_rtl_equivalence(report: dict) -> None:
    assert report["decision"] == "llama7b_gqa8_folded_lane_equivalence_pass"
    assert report["equivalence_pass"] is True
    assert report["all_lane_result_hashes_match"] is True
    assert report["tested_parallel_query_head_lanes"] == [1, 2, 4, 8]
    assert report["precision_contract"].startswith("exact_signed_int8")
    assert report["shared_result_sha256"]

    rows = {row["parallel_query_head_lanes"]: row for row in report["rows"]}
    assert {lanes: row["query_head_waves"] for lanes, row in rows.items()} == {
        1: 8,
        2: 4,
        4: 2,
        8: 1,
    }
    assert {lanes: row["score_bank_macro_count"] for lanes, row in rows.items()} == {
        1: 56,
        2: 112,
        4: 224,
        8: 448,
    }
    assert {lanes: row["shared_value_reads_per_block"] for lanes, row in rows.items()} == {
        1: 128,
        2: 64,
        4: 32,
        8: 16,
    }
    assert all(row["score_write_count"] == 24 for row in rows.values())
    assert all(row["score_read_count"] == 24 for row in rows.values())
    assert all(row["result_count"] == 128 for row in rows.values())
    assert all(row["expected_group_result_sha256"] == report["shared_result_sha256"] for row in rows.values())
    assert all(row["observed_group_result_sha256"] == report["shared_result_sha256"] for row in rows.values())


def test_folded_lane_report_is_compact_and_states_replay_contract(report: dict) -> None:
    assert len(json.dumps(report, sort_keys=True)) < 20_000
    assert report["scope"]["direct_rtl_simulation"] is True
    assert report["scope"]["intermediate_score_writes_and_reads_checked"] is True
    assert report["scope"]["ordered_result_beats_checked"] == 128
    assert "no hidden query or key buffer" in report["scope"]["producer_contract"]
    markdown = _render_markdown(report)
    assert "| lanes | waves | macros | cycles |" in markdown
    assert "| 1 | 8 | 56 |" in markdown
    assert "| 8 | 1 | 448 |" in markdown


def test_folded_lane_report_requires_complete_lane_set() -> None:
    with pytest.raises(ValueError, match="exactly one config"):
        build_report(_configs()[:-1])
