from __future__ import annotations

import json

import pytest

from npu.eval.audit_attention_decode_score_multivalue_gqa_group_equivalence import (
    _ordered_group_hash,
    _render_markdown,
    build_report,
)


def _config() -> dict:
    return {
        "top_name": "attention_decode_score_multivalue_gqa8_arithmetic_audit",
        "attention_decode_score_multivalue_gqa_group": {
            "max_blocks": 16,
            "array_n": 8,
            "value_slices": 16,
            "divider_impl": "iterative_restoring",
            "score_scale_lanes_per_cycle": 8,
            "query_heads_per_kv": 8,
        },
    }


@pytest.fixture(scope="module")
def report() -> dict:
    return build_report(_config())


def test_gqa8_shared_kv_real_cluster_arithmetic_equivalence(report: dict) -> None:
    assert report["decision"] == "llama7b_gqa8_shared_kv_equivalence_pass", json.dumps(report, indent=2)
    assert report["equivalence_pass"] is True
    assert report["arithmetic_equivalence_pass"] is True
    assert report["query_heads_per_kv"] == 8
    assert report["head_dim"] == 128
    assert len(report["heads"]) == 8
    assert [row["head"] for row in report["heads"]] == list(range(8))
    assert len({row["query_sha256"] for row in report["heads"]}) == 8
    assert report["shared_inputs_pass"] is True
    assert {row["shared_key_sha256"] for row in report["heads"]} == {report["shared_key_sha256"]}
    assert {row["shared_value_sha256"] for row in report["heads"]} == {report["shared_value_sha256"]}
    assert all(row["expected_score_sha256"] == row["observed_score_sha256"] for row in report["heads"])
    assert all(row["expected_result_sha256"] == row["observed_result_sha256"] for row in report["heads"])
    assert report["expected_group_result_sha256"] == report["observed_group_result_sha256"]
    assert report["group_result_sha256"] == report["observed_group_result_sha256"]
    assert report["expected_group_results"] == report["observed_group_results"]
    assert len(report["observed_group_results"]) == 128
    assert [(row["head"], row["slice"]) for row in report["observed_group_results"]] == [
        (head, value_slice) for head in range(8) for value_slice in range(16)
    ]
    assert report["per_head_result_sha256"] == [row["observed_result_sha256"] for row in report["heads"]]


def test_gqa8_report_states_compositional_scope_and_protocol_gate(report: dict) -> None:
    assert report["wrapper_protocol"]["sharing_and_order_pass"] is True
    assert report["wrapper_protocol"]["passed_test_count"] == 1
    proof = report["compositional_proof"]
    assert proof["method"] == "single_cluster_arithmetic_plus_wrapper_protocol"
    assert proof["flat_8_cluster_rtl_simulation_run"] is False
    markdown = _render_markdown(report)
    assert "real single-cluster arithmetic pass: `True`" in markdown
    assert "wrapper sharing/order protocol pass: `True`" in markdown
    assert "does not claim that a flat eight-cluster RTL simulation was run" in markdown


def test_ordered_group_hash_is_deterministic_and_head_order_sensitive() -> None:
    heads = [
        {"head": 1, "observed_result_sha256": "head-one"},
        {"head": 0, "observed_result_sha256": "head-zero"},
    ]
    assert _ordered_group_hash(heads, "observed_result_sha256") == _ordered_group_hash(
        list(reversed(heads)), "observed_result_sha256"
    )
    changed = [dict(row) for row in heads]
    changed[0]["head"] = 2
    assert _ordered_group_hash(heads, "observed_result_sha256") != _ordered_group_hash(
        changed, "observed_result_sha256"
    )
