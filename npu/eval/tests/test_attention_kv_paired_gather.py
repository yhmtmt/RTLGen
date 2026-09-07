import pytest

from npu.sim.perf.attention_kv_paired_gather import key_head_spans, llama7b_descriptor_cost
from npu.sim.perf.attention_kv_paired_gather import addressed_key_spans


def test_full_model_paired_addresses_preserve_cache_and_hbm_layout():
    resident_bytes = hbm_bytes = count = 0
    for layer in range(32):
        for tile in range(128):
            for head in range(4):
                spans = addressed_key_spans(layer=layer, tile=tile, head=head)
                assert len({s.canonical_address for s in spans}) == 128
                for s in spans:
                    count += 1
                    offset = s.canonical_address - (head << 17)
                    resident = tile < 2 or (tile == 2 and offset < 16384)
                    assert s.source_hbm == (not resident)
                    assert s.destination_cluster == (3 * layer + tile) % 16
                    if resident:
                        resident_bytes += s.payload_bytes
                        local = (tile << 20) + s.canonical_address if tile < 2 else (2 << 20) + (head << 14) + offset
                        assert s.source_byte_address == layer * (2176 << 10) + local
                        assert s.source_endpoint == s.destination_cluster
                        assert s.source_byte_address + s.payload_bytes <= (layer + 1) * (2176 << 10)
                    else:
                        hbm_bytes += s.payload_bytes
                        assert s.source_byte_address == (layer << 27) + (tile << 20) + s.canonical_address
                        assert s.source_endpoint == (0, 3, 12, 15)[(layer + tile + head) % 4]
    assert count == 2097152
    assert resident_bytes == 32 * (1048576 + 65536)
    assert resident_bytes + hbm_bytes == 32 * 64 * 1048576


@pytest.mark.parametrize("field,value", [("layer", 32), ("tile", -1), ("head", 4), ("head", True)])
def test_address_oracle_rejects_invalid_coordinates(field, value):
    args = dict(layer=0, tile=0, head=0)
    args[field] = value
    with pytest.raises(ValueError):
        addressed_key_spans(**args)


@pytest.mark.parametrize("resident", [0, 16384, 131072])
def test_full_head_coverage_pairing_and_source_ownership(resident):
    spans = key_head_spans(resident_prefix_bytes=resident)
    assert len(spans) == 128
    flits = [span.canonical_offset + offset for span in spans for offset in range(0, 1024, 32)]
    assert sorted(flits) == list(range(0, 131072, 32))
    assert sum(s.payload_bytes for s in spans if s.resident) == resident
    for slot in range(64):
        a, b = spans[2*slot:2*slot+2]
        assert a.canonical_offset == slot * 1024
        assert b.canonical_offset == 65536 + slot * 1024
    assert flits[32] == 0x10000


def test_split_prefix_needs_alternating_sources_before_prefix_exhaustion():
    spans = key_head_spans(resident_prefix_bytes=16384)
    assert [s.resident for s in spans[:32]] == [True, False] * 16
    assert all(not s.resident for s in spans[32:])


def test_unaligned_source_boundary_rejected():
    with pytest.raises(ValueError):
        key_head_spans(resident_prefix_bytes=512)


def test_paired_control_work_exceeds_existing_aggregate_counter():
    cost = llama7b_descriptor_cost()
    assert cost["old_k_descriptors_per_layer"] == 516
    assert cost["paired_k_descriptors_per_layer"] == 65536
    assert cost["total_descriptors_per_layer"] == 66062
    assert cost["total_descriptors_full_model"] == 2113984
    assert cost["minimum_layer_count_bits"] == 17
    assert cost["minimum_model_count_bits"] == 22
    assert cost["k_payload_bytes_per_layer"] == 64 * 1024 * 1024
