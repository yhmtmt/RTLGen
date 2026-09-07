import hashlib
import json
from pathlib import Path


def test_retained_canonical_concurrent_rows_and_cadence():
    root = Path(__file__).resolve().parents[3]
    path = root / "docs/proposals/prop_l2_decoder_attention_score32_exact_kv_ingress_revision_llama7b_v1/canonical_concurrent_cluster_result.json"
    report = json.loads(path.read_text())
    assert report["passed"]
    assert "not live ingress" in report["scope"]
    assert {c["cluster"] for c in report["clusters"]} == {0, 8}
    assert len(report["clusters"]) == 2
    assert len(report["source_hashes"]) == 36
    assert len(report["generated_hashes"]) == 15
    for c in report["clusters"]:
        rows = c["observed_rows"]
        assert len(rows) == 512
        digest = hashlib.sha256(json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        assert digest == c["exact_row_audit"]["observed_hash"] == c["exact_row_audit"]["expected_hash"]
        assert {(r["head_id"], r["slice"]) for r in rows} == {(h,s) for h in range(32) for s in range(16)}
        assert all(r["cluster"] == c["cluster"] for r in rows)
        starts = [17432,33824,50216,66608] if c["cluster"] == 0 else [17437,33829,50221,66613]
        assert c["producer_count"] == (54 if c["cluster"] == 0 else 53)
        assert [g["first_output_cycle"] for g in c["groups"]] == starts
        for g, start in zip(c["groups"], starts):
            assert g["output_cycles"] == list(range(start,start+128))
        assert c["last_output_cycle"] == starts[-1]+127
        summary = c["summary"]
        assert summary["errors"] == 0
        assert summary["fill_row_accept_count"] == summary["request_accept_count"] == summary["response_accept_count"] == 65536
        assert summary["command_accept_count"] == summary["command_release_count"] == 32
