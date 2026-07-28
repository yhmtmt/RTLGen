import copy
import json
from pathlib import Path
import sys

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.eval.probe_attention_score32_exact_local16_global_tree_gqa8 import (
    compare_compositional_rows,
    compare_full_rows,
)
from npu.rtlgen.gen_attention_score32_exact_local16_global_tree_gqa8 import _validate


def _config_path() -> Path:
    return (
        REPO_ROOT
        / "runs"
        / "designs"
        / "npu_blocks"
        / "attention_score32_exact_local16_global_tree_gqa8_p54x8_p53x8_c16_r2_l8_b59"
        / "config.json"
    )


def _sample_rows() -> list[dict[str, object]]:
    return [
        {
            "command_id": 0x8200,
            "head_id": 3,
            "slice": 7,
            "last": False,
            "global_max": -11,
            "exp_sum": 991,
            "value": [3, -2, 7, 0, 19, -5, 4, 8],
        },
        {
            "command_id": 0x8200,
            "head_id": 3,
            "slice": 8,
            "last": False,
            "global_max": -8,
            "exp_sum": 1012,
            "value": [4, -1, 8, 1, 20, -4, 5, 9],
        },
    ]


def test_full_row_comparator_accepts_exact_rows_and_rejects_one_field_mismatch() -> None:
    expected = _sample_rows()
    exact = compare_full_rows(expected, copy.deepcopy(expected))
    assert exact["passed"] is True
    assert exact["first_mismatch"] is None

    mismatched = copy.deepcopy(expected)
    mismatched[1]["exp_sum"] = 1013
    rejected = compare_full_rows(expected, mismatched)
    assert rejected["passed"] is False
    assert rejected["first_mismatch"] == {
        "row": 1,
        "field": "exp_sum",
        "expected": 1012,
        "observed": 1013,
    }
    assert rejected["expected_hash"] != rejected["observed_hash"]


def test_compositional_comparator_requires_all_cluster_and_root_rows() -> None:
    cluster_rows = [[{"cluster": cluster, "value": cluster}] for cluster in range(16)]
    root_rows = [{"command_id": 1, "head_id": 0, "slice": 0, "last": True, "value": [1] * 16}]
    exact = compare_compositional_rows(
        expected_cluster_rows=cluster_rows,
        observed_cluster_rows=copy.deepcopy(cluster_rows),
        expected_root_rows=root_rows,
        observed_root_rows=copy.deepcopy(root_rows),
    )
    assert exact["passed"] is True

    observed_clusters = copy.deepcopy(cluster_rows)
    observed_clusters[9][0]["value"] = -1
    rejected = compare_compositional_rows(
        expected_cluster_rows=cluster_rows,
        observed_cluster_rows=observed_clusters,
        expected_root_rows=root_rows,
        observed_root_rows=root_rows,
    )
    assert rejected["passed"] is False
    assert rejected["clusters"][9]["first_mismatch"]["field"] == "value"


def test_hierarchy_config_rejects_any_instance_count_drift() -> None:
    config = json.loads(_config_path().read_text(encoding="utf-8"))
    _validate(config)
    body = config["attention_score32_exact_local16_global_tree_gqa8"]
    body["cluster_producers"] = [54] * 7 + [53] * 9
    with pytest.raises(SystemExit, match="exactly eight 54s followed by eight 53s"):
        _validate(config)
