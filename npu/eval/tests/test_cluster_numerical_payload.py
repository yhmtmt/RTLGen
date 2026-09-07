import pytest

from npu.eval.cluster_numerical_payload import pack_all_endpoints, pack_observed_cluster
from npu.sim.perf.attention_exact_partial import unpack_numerators


def fixture():
    return {
        "cluster": 8, "passed": True,
        "exact_row_audit": {"passed": True, "expected_row_count": 512, "observed_row_count": 512},
        "groups": [{"logical_group": g, "command_id": 100 + g, "head_base": 8 * g} for g in range(4)],
        "observed_rows": [{
            "cluster": 8, "command_id": 100 + i // 128, "head_id": i // 16,
            "slice": i % 16, "last": i % 16 == 15, "global_max": -123,
            "exp_sum": (1 << 33) - 1,
            "value": [-(1 << 40), (1 << 40) - 1, -1, 0, 1, 2, 3, 4],
        } for i in range(512)],
    }


def test_signed_extremes_and_metadata_survive_packing():
    data = fixture()
    words = pack_observed_cluster(data, expected_cluster=8)
    assert len(words) == 512
    assert list(unpack_numerators(words[0] >> 91)) == data["observed_rows"][0]["value"]
    assert (words[0] >> 21) & 0xffffffff == (-123 & 0xffffffff)
    assert words[-1] & 0xffff == 103
    assert (words[-1] >> 16) & 31 == 31


@pytest.mark.parametrize("field,value", [
    ("cluster", 0), ("head_id", 1), ("slice", 1), ("last", 0),
    ("command_id", 101), ("global_max", 1 << 31), ("exp_sum", 1 << 33),
    ("value", [1 << 40] * 8), ("value", [0] * 7),
])
def test_corrupt_rows_rejected(field, value):
    data = fixture()
    data["observed_rows"][0][field] = value
    with pytest.raises(ValueError):
        pack_observed_cluster(data, expected_cluster=8)


def test_timing_only_artifact_cannot_supply_numerical_payload():
    data = fixture()
    del data["observed_rows"]
    with pytest.raises(ValueError, match="observed numerical"):
        pack_observed_cluster(data, expected_cluster=8)


def endpoints():
    result = []
    for endpoint in range(16):
        data = fixture()
        data["cluster"] = endpoint
        for row in data["observed_rows"]:
            row["cluster"] = endpoint
            row["value"][0] = endpoint
        result.append(data)
    return result


def test_all_endpoints_preserve_distinct_payloads_in_endpoint_order():
    words = pack_all_endpoints(list(reversed(endpoints())))
    assert len(words) == 8192
    for endpoint in range(16):
        assert unpack_numerators(words[endpoint * 512] >> 91)[0] == endpoint


def test_representatives_cannot_substitute_for_sixteen_streams():
    data = endpoints()
    with pytest.raises(ValueError, match="sixteen"):
        pack_all_endpoints([data[0], data[8]])
    with pytest.raises(ValueError, match="duplicate"):
        pack_all_endpoints([data[0]] * 16)


def test_endpoint_command_mismatch_rejected():
    data = endpoints()
    data[1]["groups"][0]["command_id"] = 999
    for row in data[1]["observed_rows"][:128]:
        row["command_id"] = 999
    with pytest.raises(ValueError, match="command identities"):
        pack_all_endpoints(data)
