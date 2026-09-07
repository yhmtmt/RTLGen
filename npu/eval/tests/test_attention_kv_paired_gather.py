import pytest

from npu.sim.perf.attention_kv_paired_gather import key_head_spans, llama7b_descriptor_cost


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
