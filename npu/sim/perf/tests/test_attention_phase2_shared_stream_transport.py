from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

from npu.sim.perf.attention_phase2_shared_stream_transport import (
    CONTEXT_BYTES,
    CONTEXT_COUNT,
    DESTINATION_SPACE_BASE,
    FLIT_BYTES,
    FLITS_PER_PACKET,
    LOCAL_ONLY_WAVE,
    MAPPING_SHIFTS,
    PACKETS_PER_CONTEXT,
    PACKET_BYTES,
    REMOTE_WAVES,
    TOTAL_FLITS,
    TOTAL_PACKETS,
    TOTAL_SHARED_BYTES,
    ContextCompletionTracker,
    PacketTagLifetimeTracker,
    TransportContractError,
    build_context,
    build_contexts,
    canonical_memory_writes,
    copy_payload_and_validate,
    destination_base_for,
    packet_descriptors,
    packet_tag,
    source_base_for,
    source_endpoint_for,
    validate_payload_equivalence,
)


def test_exact_transport_totals_and_packet_shape() -> None:
    contexts = build_contexts()
    assert len(contexts) == CONTEXT_COUNT == 112
    assert sum(context.payload_bytes for context in contexts) == TOTAL_SHARED_BYTES == 1_949_696
    assert sum(context.packet_count for context in contexts) == TOTAL_PACKETS == 7_616
    assert sum(context.packet_count * context.flits_per_packet for context in contexts) == TOTAL_FLITS == 60_928
    assert all(context.payload_bytes == CONTEXT_BYTES for context in contexts)
    assert all(context.packet_count == PACKETS_PER_CONTEXT for context in contexts)
    assert all(context.flits_per_packet == FLITS_PER_PACKET for context in contexts)
    assert all(context.vc == 0 for context in contexts)


def test_all_wave_mapping_shifts_and_local_wave_is_excluded() -> None:
    contexts = build_contexts()
    assert REMOTE_WAVES == (0, 1, 2, 3, 5, 6, 7)
    assert len(MAPPING_SHIFTS) == 8
    assert not any(context.wave_index == LOCAL_ONLY_WAVE for context in contexts)
    for wave in range(8):
        assert {source_endpoint_for(wave_index=wave, destination_endpoint=destination)
                for destination in range(16)} == set(range(16)) if wave != 4 else True
    for context in contexts:
        assert context.source_endpoint == source_endpoint_for(
            wave_index=context.wave_index,
            destination_endpoint=context.destination_endpoint,
        )


def test_source_and_destination_windows_are_non_overlapping() -> None:
    contexts = build_contexts()
    source_windows = {(context.source_base, context.source_base + CONTEXT_BYTES) for context in contexts}
    destination_windows = {
        (context.destination_base, context.destination_base + CONTEXT_BYTES) for context in contexts
    }
    assert len(source_windows) == CONTEXT_COUNT
    assert len(destination_windows) == CONTEXT_COUNT
    assert max(end for _, end in source_windows) <= DESTINATION_SPACE_BASE
    assert min(start for start, _ in destination_windows) >= DESTINATION_SPACE_BASE

    def assert_disjoint(windows: set[tuple[int, int]]) -> None:
        ordered = sorted(windows)
        assert all(left[1] <= right[0] for left, right in zip(ordered, ordered[1:]))

    assert_disjoint(source_windows)
    assert_disjoint(destination_windows)


def test_byte_address_formulas_cover_each_packet_and_flit() -> None:
    context = build_contexts()[0]
    writes = canonical_memory_writes(context, bytes(range(256)) * (CONTEXT_BYTES // 256) + bytes(0))
    assert len(writes) == PACKETS_PER_CONTEXT * FLITS_PER_PACKET
    for ordinal, write in enumerate(writes):
        packet, flit = divmod(ordinal, FLITS_PER_PACKET)
        offset = packet * PACKET_BYTES + flit * FLIT_BYTES
        assert write.packet_index == packet
        assert write.flit_index == flit
        assert write.source_address == context.source_base + offset
        assert write.destination_address == context.destination_base + offset
        assert len(write.data) == FLIT_BYTES


def test_payload_equivalence_copies_full_window_and_compares_bytes() -> None:
    context = build_contexts()[37]
    source = bytes((index * 17 + context.context_id) & 0xFF for index in range(CONTEXT_BYTES))
    destination: dict[int, int] = {}
    result = copy_payload_and_validate(context, source, destination)
    assert result.byte_count == CONTEXT_BYTES
    assert result.write_count == TOTAL_FLITS // CONTEXT_COUNT
    assert result.unique_address_count == CONTEXT_BYTES
    assert bytes(destination[context.destination_base + index] for index in range(CONTEXT_BYTES)) == source


@pytest.mark.parametrize("mutation", ["corrupt", "missing", "duplicate"])
def test_payload_equivalence_rejects_corruption_missing_and_duplicate_writes(mutation: str) -> None:
    context = build_contexts()[0]
    source = bytes(index & 0xFF for index in range(CONTEXT_BYTES))
    writes = list(canonical_memory_writes(context, source))
    if mutation == "corrupt":
        writes[11] = dataclasses.replace(writes[11], data=bytes([writes[11].data[0] ^ 1]) + writes[11].data[1:])
    elif mutation == "missing":
        writes.pop(11)
    else:
        writes[11] = writes[10]
    with pytest.raises(TransportContractError):
        validate_payload_equivalence(context, source, writes)


def test_invalid_payload_never_mutates_destination() -> None:
    context = build_contexts()[0]
    source = bytes([3]) * CONTEXT_BYTES
    writes = list(canonical_memory_writes(context, source))
    writes[-1] = dataclasses.replace(writes[-1], data=bytes([4]) * FLIT_BYTES)
    destination: dict[int, int] = {}
    with pytest.raises(TransportContractError):
        copy_payload_and_validate(context, source, destination, writes)
    assert destination == {}


def test_context_completion_is_ordered_and_release_is_consumer_owned() -> None:
    contexts = build_contexts()
    tracker = ContextCompletionTracker(contexts)
    first = contexts[:16]
    for context in first:
        tracker.admit(context.context_id)
    with pytest.raises(TransportContractError):
        tracker.admit(contexts[16].context_id)
    context = first[0]
    with pytest.raises(TransportContractError):
        tracker.complete_packet(context.context_id, 1)
    for packet_index in range(PACKETS_PER_CONTEXT):
        tracker.complete_packet(context.context_id, packet_index)
    status = tracker.status(context.context_id)
    assert status.completion_valid
    assert status.admitted
    assert status.source_owned and status.destination_owned
    tracker.accept_completion(context.context_id)
    status = tracker.status(context.context_id)
    assert status.completion_valid and status.completion_accepted
    assert not status.admitted
    assert not status.source_owned and not status.destination_owned


def test_variable_packet_context_uses_modulo_256_tags_and_exact_payload() -> None:
    context = build_context(wave_index=0, destination_endpoint=0, packets_per_context=257)
    assert context.packet_count == 257
    assert context.payload_bytes == 257 * PACKET_BYTES
    descriptors = packet_descriptors(context)
    assert descriptors[0].tag == 0
    assert descriptors[255].tag == 255
    assert descriptors[256].tag == 0
    source = bytes(index & 0xFF for index in range(context.payload_bytes))
    writes = canonical_memory_writes(context, source)
    result = validate_payload_equivalence(context, source, writes)
    assert result.byte_count == context.payload_bytes
    assert result.packet_count == 257
    assert result.flit_count == 257 * FLITS_PER_PACKET


def test_default_packet_context_bound_is_eight_and_tag_reuse_is_safe() -> None:
    context = build_context(wave_index=0, destination_endpoint=0, packets_per_context=257)
    tracker = ContextCompletionTracker([context])
    tracker.admit(context.context_id)
    for packet_index in range(8):
        assert tracker.expose_packet(context.context_id, packet_index) == packet_tag(packet_index)
    assert tracker.status(context.context_id).inflight_packet_count == 8
    with pytest.raises(TransportContractError, match="full"):
        tracker.expose_packet(context.context_id, 8)
    tracker.complete_packet(context.context_id, 0)
    assert tracker.expose_packet(context.context_id, 8) == packet_tag(8)
    assert tracker.status(context.context_id).inflight_packet_count == 8


def test_same_tag_cannot_be_exposed_until_prior_packet_completes() -> None:
    context = build_context(wave_index=0, destination_endpoint=0, packets_per_context=257)
    tracker = PacketTagLifetimeTracker(257, max_in_flight=257)
    for packet_index in range(256):
        assert tracker.expose(packet_index) == packet_tag(packet_index)
    with pytest.raises(TransportContractError, match="cannot be reused"):
        tracker.expose(256)
    tracker.complete(0)
    assert tracker.expose(256) == 0
    assert tracker.inflight_packet_count == 256


def test_checked_old_artifact_has_independent_shared_contract() -> None:
    from npu.eval.check_attention_phase2_shared_stream_contract import validate_artifact

    artifact = (
        Path(__file__).resolve().parents[4]
        / "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
        "decoder_attention_score32_noc_phase2_schedule__"
        "l2_decoder_attention_score32_noc_phase2_schedule_llama7b_v1_r1.json"
    )
    result = validate_artifact(artifact)
    assert result["status"] == "ok"
    assert result["shared"]["contexts"] == CONTEXT_COUNT
    assert result["retracted_reduction_validation"] == "ignored"
