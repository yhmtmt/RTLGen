import pytest

from npu.eval.numerical_mesh_sidecars import build_sidecars
from npu.eval.tests.test_cluster_numerical_payload import endpoints


def report():
    clusters = endpoints()
    for endpoint, cluster in enumerate(clusters):
        for group in cluster["groups"]:
            start = 1000 + endpoint + 300 * group["logical_group"]
            group["output_cycles"] = list(range(start, start + 128))
    return {"model": "score32_all_cluster_numerical_payloads_v1", "passed": True,
        "clusters": clusters, "expected_root_rows": [{
            "command_id": 100 + i // 128, "head_id": i // 16,
            "slice": i % 16, "last": i % 16 == 15,
            "value": [-(1 << 39), (1 << 39) - 1, -1, 0, 1, 2, 3, 4],
        } for i in range(512)]}


def test_serialization_preserves_command_and_signed_root_extremes():
    result = build_sidecars(report())
    assert len(result["leaf_memh"].splitlines()) == 8192
    assert len(result["root_memh"].splitlines()) == 512
    assert result["command_base"] == "100"
    cycles = result["release_memh"].splitlines()
    assert len(cycles) == 8192
    assert int(cycles[512], 16) == 1001
    root = int(result["root_memh"].splitlines()[0], 16)
    assert root & 65535 == 100
    assert (root >> 26) & ((1 << 40) - 1) == 1 << 39
    assert (root >> 66) & ((1 << 40) - 1) == (1 << 39) - 1


def test_bad_root_metadata_rejected():
    data = report()
    data["expected_root_rows"][3]["command_id"] = 0x6a00
    with pytest.raises(ValueError, match="metadata"):
        build_sidecars(data)
