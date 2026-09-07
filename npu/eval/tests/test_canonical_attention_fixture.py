from dataclasses import replace
import pytest

from npu.sim.perf.canonical_attention_fixture import CanonicalAttentionFixture
from npu.sim.perf.attention_kv_tile_layout import encode_kv_byte_address
from npu.sim.perf.attention_score32_exact_cluster_sram_service_gqa8 import exact_local_cluster_gqa8_slot_bases


@pytest.mark.parametrize("producers", [53, 54])
@pytest.mark.parametrize("group", range(4))
def test_producer_bytes_come_from_canonical_memory_with_resident_queries(producers, group):
    fixture = CanonicalAttentionFixture(layer=7)
    bases = exact_local_cluster_gqa8_slot_bases(producers=producers, group_index=group)
    # Cover every producer/block and both streams at four dimension boundaries.
    count = 0
    for producer in range(producers):
        for beat, (q, k, last) in enumerate(fixture.producer_stream(
                producers=producers, producer=producer, group=group, tile=2)):
            dimension = beat % 128
            assert q[:8] == q[8:] == fixture.query(group=group, dimension=dimension)
            assert last == (dimension == 127)
            count += 1
            if dimension not in (0, 31, 64, 127):
                continue
            for lane, value in enumerate(k):
                token = (lane // 8) * 512 + (bases[producer] + beat // 128) * 8 + lane % 8
                address = encode_kv_byte_address(tensor="k", kv_head=group, token=token, dimension=dimension)
                flit = fixture.memory_flit(tile=2, address=address & ~31)
                assert flit[address % 32] == value & 255
    assert count == 8192


def test_new_decode_query_does_not_rewrite_cached_kv():
    first = CanonicalAttentionFixture()
    second = replace(first, decode_token=131073)
    assert first.query(group=0, dimension=0) != second.query(group=0, dimension=0)
    for address in (0, 0x4000, 0x10000, 0x80000, 0xfffe0):
        assert first.memory_flit(tile=127, address=address) == second.memory_flit(tile=127, address=address)


def test_invalid_coordinates_are_rejected():
    with pytest.raises(ValueError):
        CanonicalAttentionFixture(layer=True)
    with pytest.raises(ValueError):
        CanonicalAttentionFixture().memory_flit(tile=0, address=1)
