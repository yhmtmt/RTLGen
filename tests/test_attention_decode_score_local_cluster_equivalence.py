import json

import pytest

from npu.eval.probe_attention_decode_score_local_cluster_equivalence import build_report


@pytest.mark.parametrize("scale_lanes", [1, 8])
def test_attention_decode_score_local_cluster_perf_rtl_equivalence(scale_lanes: int) -> None:
    report = build_report(
        {
            "top_name": f"attention_decode_score_local_cluster_equivalence_s{scale_lanes}",
            "attention_decode_score_local_cluster": {
                "max_blocks": 16,
                "array_n": 8,
                "divider_impl": "iterative_restoring",
                "score_scale_lanes_per_cycle": scale_lanes,
            },
        }
    )

    assert report["decision"] == "decode_score_local_cluster_equivalence_pass", json.dumps(report, indent=2)
    assert report["equivalence_pass"] is True
    assert report["scenario_count"] == 2
    assert all(row["equivalence_pass"] for row in report["scenarios"])
    assert all(row["score_addresses"] == [0, 1, 2] for row in report["scenarios"])
