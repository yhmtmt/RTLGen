import json
from pathlib import Path


def test_composed_canonical_rows_match_direct_producer_evidence():
    root = Path(__file__).resolve().parents[3]
    evidence = root / "docs/proposals/prop_l2_decoder_attention_score32_exact_kv_ingress_revision_llama7b_v1"
    direct = json.loads((evidence / "canonical_numerical_producer_result.json").read_text())["reports"]
    composed = json.loads((evidence / "canonical_composed_numerical_result.json").read_text())["reports"]
    reference = {(r["input_fixture"]["producers"], r["input_fixture"]["producer"]):
                 r["expected_rows_sha256"] for r in direct}
    assert len(composed) == 8
    kinds = {"canonical_tensor_live_kq_stage_producer", "canonical_tensor_live_transpose_stage_producer",
             "canonical_tensor_kv_ingress_producer", "canonical_tensor_ingress_sram_producer"}
    for family in (53, 54):
        rows = [r for r in composed if r["input_fixture"]["producers"] == family]
        assert len(rows) == 4
        assert {r["input_fixture"]["kind"] for r in rows} == kinds
        for report in rows:
            fixture = report["input_fixture"]
            assert report["passed"] and report["outputs"] == 512
            assert report["observed_rows_sha256"] == report["expected_rows_sha256"] == reference[family, fixture["producer"]]
            assert fixture["live_mesh"] is False
            assert report["llama_wave_reference_cycles"] is None
            assert report["llama_wave_drain_delta_vs_986"] is None
