"""Guard the retained concrete replay evidence without relabeling its scope."""
import json
from pathlib import Path

from npu.eval.numerical_mesh_sidecars import build_sidecars


def test_all_concrete_endpoint_payloads_remain_replayable():
    root = Path(__file__).resolve().parents[3]
    archive = root / "docs/proposals/prop_l2_decoder_attention_score32_exact_cluster_release_cadence_llama7b_v1/all_cluster_numerical_payloads.json"
    data = json.loads(archive.read_text())
    assert data["passed"] is True
    assert data["packed_word_count"] == 8192
    assert [c["cluster"] for c in data["clusters"]] == list(range(16))
    assert len(data["expected_root_rows"]) == 512
    for endpoint, cluster in enumerate(data["clusters"]):
        assert len(cluster["observed_rows"]) == 512
        expected = [17432, 33824, 50216, 66608] if endpoint < 8 else [17437, 33829, 50221, 66613]
        assert [g["output_cycles"][0] for g in cluster["groups"]] == expected
        assert cluster["groups"][-1]["output_cycles"][-1] == expected[-1] + 127
    sidecars = build_sidecars(data)
    assert len(sidecars["leaf_memh"].splitlines()) == 8192
    assert len(sidecars["release_memh"].splitlines()) == 8192
    assert len(sidecars["root_memh"].splitlines()) == 512
    assert int(sidecars["command_base"]) == 0x8200
