from __future__ import annotations

import copy

import pytest

from npu.eval.audit_attention_decode_score_multivalue_gqa_array_equivalence import _build_report


def _group_equivalence() -> dict:
    return {
        "model": "llama7b_gqa8_shared_kv_compositional_arithmetic_equivalence_v1",
        "decision": "llama7b_gqa8_shared_kv_equivalence_pass",
        "equivalence_pass": True,
        "semantic_profile": "decode_m1x8_shared_score_16x8d_value_iterdiv_gqa8_group_v1",
        "query_heads_per_kv": 8,
        "distinct_query_heads_pass": True,
        "shared_inputs_pass": True,
        "arithmetic_equivalence_pass": True,
        "expected_group_result_sha256": "same-group-hash",
        "observed_group_result_sha256": "same-group-hash",
        "wrapper_protocol": {"sharing_and_order_pass": True},
    }


def _configs() -> list[dict]:
    return [
        {
            "top_name": f"gqa_array_g{count}",
            "attention_decode_score_multivalue_gqa_array": {
                "max_blocks": 16384,
                "array_n": 8,
                "value_slices": 16,
                "divider_impl": "iterative_restoring",
                "score_scale_lanes_per_cycle": 1,
                "query_heads_per_kv": 8,
                "group_count": count,
            },
        }
        for count in (1, 2, 4)
    ]


def _protocol(passed: bool = True) -> dict:
    return {
        "passed_test_count": 3 if passed else 2,
        "atomic_broadcast_and_independent_channels_pass": passed,
    }


def test_array_equivalence_composes_exact_group_and_protocol_gates() -> None:
    report = _build_report(
        group_equivalence=_group_equivalence(), array_configs=_configs(), protocol=_protocol()
    )
    assert report["equivalence_pass"] is True
    assert report["precision_status"] == "exact"
    assert report["measured_group_counts"] == [1, 2, 4]
    assert report["logical_kv_groups"] == 4
    assert all(
        row["expected_array_result_sha256"] == row["observed_array_result_sha256"]
        for row in report["array_result_hashes"]
    )
    assert report["compositional_proof"]["flat_32_cluster_arithmetic_simulation_run"] is False


def test_array_equivalence_rejects_weak_group_or_protocol_evidence() -> None:
    group = _group_equivalence()
    group["arithmetic_equivalence_pass"] = False
    with pytest.raises(ValueError, match="group equivalence contract"):
        _build_report(group_equivalence=group, array_configs=_configs(), protocol=_protocol())

    report = _build_report(
        group_equivalence=_group_equivalence(),
        array_configs=_configs(),
        protocol=_protocol(False),
    )
    assert report["equivalence_pass"] is False
    assert report["precision_status"] == "rejected"


def test_array_equivalence_requires_exact_one_two_four_config_set() -> None:
    configs = _configs()[:-1]
    with pytest.raises(ValueError, match="must cover group counts"):
        _build_report(
            group_equivalence=_group_equivalence(), array_configs=configs, protocol=_protocol()
        )

    configs = copy.deepcopy(_configs())
    configs[1]["attention_decode_score_multivalue_gqa_array"]["value_slices"] = 8
    with pytest.raises(ValueError, match="exact Llama7B"):
        _build_report(
            group_equivalence=_group_equivalence(), array_configs=configs, protocol=_protocol()
        )
