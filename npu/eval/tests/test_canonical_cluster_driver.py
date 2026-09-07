import pytest

from npu.eval.gqa8_compositional_exact import _cluster_driver_data, _canonical_cluster_fill_rows
from npu.sim.perf.canonical_attention_fixture import CanonicalAttentionFixture


@pytest.mark.parametrize("cluster,producers", [(0,54),(8,53)])
def test_all_producer_canonical_streams_preserve_wave_and_slot_mapping(cluster, producers):
    fixture = CanonicalAttentionFixture()
    data = _cluster_driver_data(cluster=cluster, logical_head_groups=1, canonical_fixture=fixture)
    stride = data["max_beats_per_producer"]
    accepted = 0
    for p in range(producers):
        cursor = 0
        for index, command in enumerate(data["wave_commands"]):
            tile = cluster + 16 * command["wave_index"]
            for q, k, last in fixture.producer_stream(producers=producers, producer=p, group=0, tile=tile):
                flat = p * stride + cursor
                assert data["query_words"][flat] == int.from_bytes(bytes(x & 255 for x in q), "little")
                assert data["key_words"][flat] == int.from_bytes(bytes(x & 255 for x in k), "little")
                assert data["last_words"][flat] == last
                cursor += 1
                accepted += 1
            assert cursor == data["beat_limits"][index][p]
    assert accepted == 8 * 8192


def test_canonical_cluster_driver_rejects_unimplemented_layer_rotation():
    with pytest.raises(ValueError, match="layer zero"):
        _cluster_driver_data(cluster=0, logical_head_groups=1,
            canonical_fixture=CanonicalAttentionFixture(layer=1))


def test_canonical_cluster_fill_storage_order_matches_tensor_coordinates():
    fixture = CanonicalAttentionFixture()
    rows = _canonical_cluster_fill_rows(fixture, cluster=8, wave=7, group=3)
    assert len(rows) == 2048
    for stream in range(2):
        for slot in range(64):
            for value_slice in (0, 15):
                data = rows[stream * 1024 + slot * 16 + value_slice].to_bytes(64, "little")
                for row in range(8):
                    address = 524288 + 3 * 131072 + stream * 65536 + slot * 1024 + row * 128 + value_slice * 8
                    flit = fixture.memory_flit(tile=120, address=address & ~31)
                    assert data[row*8:row*8+8] == flit[address%32:address%32+8]
