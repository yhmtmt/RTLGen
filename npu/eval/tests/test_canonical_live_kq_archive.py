import hashlib
import json
from pathlib import Path
import pytest


@pytest.mark.parametrize("ingress", [False, True, "kv"])
def test_live_kq_concurrent_canonical_archive(ingress):
    root = Path(__file__).resolve().parents[3]
    directory = root / "docs/proposals/prop_l2_decoder_attention_score32_exact_kv_ingress_revision_llama7b_v1"
    filename = "canonical_live_key_ingress_concurrent_cluster_result.json" if ingress else "canonical_live_kq_concurrent_cluster_result.json"
    if ingress == "kv":
        filename = "canonical_live_kv_ingress_concurrent_cluster_result.json"
    report = json.loads((directory / filename).read_text())
    baseline = json.loads((directory / "canonical_concurrent_cluster_result.json").read_text())
    assert report["passed"] and report["live_kq_stage"]
    assert len(report["source_hashes"]) == (44 if ingress == "kv" else 41 if ingress else 38)
    assert len(report["generated_hashes"]) == (19 if ingress == "kv" else 17 if ingress else 15)
    if ingress == "kv":
        assert report["live_value_ingress"]
        assert "npu/sim/rtl/attention_score32_exact_kv_value_ingress.sv" in report["source_hashes"]
    if ingress:
        assert report["live_key_ingress"]
        assert "npu/sim/rtl/attention_kv_paired_head_schedule.sv" in report["source_hashes"]
        assert "npu/sim/rtl/attention_score32_exact_kv_key_pingpong_transpose.sv" in report["source_hashes"]
    assert "npu/sim/rtl/attention_score32_exact_kv_key_stage_wide.sv" in report["source_hashes"]
    assert {c["cluster"] for c in report["clusters"]} == {0, 8}
    assert len(report["clusters"]) == 2
    for cluster in report["clusters"]:
        original = next(c for c in baseline["clusters"] if c["cluster"] == cluster["cluster"])
        rows = cluster["observed_rows"]
        assert rows == original["observed_rows"]
        assert len(rows) == 512
        digest = hashlib.sha256(json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        assert digest == cluster["exact_row_audit"]["observed_hash"] == cluster["exact_row_audit"]["expected_hash"]
        start = 36214 if cluster["cluster"] == 0 else 36216
        start += 512 if ingress else 0
        stride = 36472 if ingress else 35960
        if ingress == "kv":
            start = 51224 if cluster["cluster"] == 0 else 51229
            stride = 50184
        assert [g["first_output_cycle"] for g in cluster["groups"]] == [start + stride*i for i in range(4)]
        assert cluster["last_output_cycle"] == start + stride*3 + 127
        summary = cluster["summary"]
        assert summary["errors"] == 0
        assert summary["fill_row_accept_count"] == summary["request_accept_count"] == summary["response_accept_count"] == 65536
        assert summary["command_accept_count"] == summary["command_release_count"] == 32
