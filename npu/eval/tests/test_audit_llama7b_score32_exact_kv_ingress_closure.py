from __future__ import annotations

import json
from pathlib import Path

from npu.eval.audit_llama7b_score32_exact_kv_ingress_closure import (
    build_report,
    render_markdown,
)
from npu.sim.perf.attention_kv_tile_layout import (
    BYTES_PER_KV_TILE,
    KvCoordinate,
    decode_kv_byte_address,
    decode_value_fill_byte,
    encode_kv_byte_address,
    key_producer_location,
    kv_token_range_segments,
    value_fill_location,
)


ROOT = Path(__file__).resolve().parents[3]
PHASE2 = ROOT / (
    "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
    "decoder_attention_score32_noc_phase2_schedule__"
    "l2_decoder_attention_score32_noc_phase2_schedule_llama7b_v1_r1.json"
)


def test_kv_byte_layout_round_trips_boundaries() -> None:
    for tensor, head, token, dimension in (
        ("k", 0, 0, 0),
        ("k", 3, 1023, 127),
        ("v", 0, 0, 0),
        ("v", 3, 1023, 127),
    ):
        address = encode_kv_byte_address(
            tensor=tensor,
            kv_head=head,
            token=token,
            dimension=dimension,
        )
        assert decode_kv_byte_address(address) == KvCoordinate(
            tensor=tensor,
            kv_head=head,
            token=token,
            dimension=dimension,
        )
    assert encode_kv_byte_address(
        tensor="v", kv_head=3, token=1023, dimension=127
    ) == BYTES_PER_KV_TILE - 1


def test_planar_resident_range_requires_eight_tail_gathers() -> None:
    full = kv_token_range_segments(token_start=0, token_count=1024)
    assert [(segment.base_address, segment.payload_bytes) for segment in full] == [
        (0, BYTES_PER_KV_TILE)
    ]

    tail = kv_token_range_segments(token_start=0, token_count=128)
    assert len(tail) == 8
    assert {segment.payload_bytes for segment in tail} == {16 * 1024}
    assert [segment.base_address for segment in tail] == [
        plane * 128 * 1024 for plane in range(8)
    ]
    assert sum(segment.payload_bytes for segment in tail) == 128 * 1024


def test_value_fill_mapping_is_bijective_over_a_head_tile() -> None:
    seen = set()
    for token in range(1024):
        for dimension in range(128):
            location = value_fill_location(token=token, dimension=dimension)
            key = (location.flat_fill_row, location.byte_in_row)
            assert key not in seen
            seen.add(key)
            assert decode_value_fill_byte(
                flat_fill_row=location.flat_fill_row,
                byte_in_row=location.byte_in_row,
            ) == (token, dimension)
    assert len(seen) == 128 * 1024


def test_value_fill_requires_token_major_to_row_major_transpose() -> None:
    first_two_flit_rows = {
        value_fill_location(token=0, dimension=dimension).flat_fill_row
        for dimension in range(64)
    }
    assert first_two_flit_rows == set(range(8))

    first_fill_row_addresses = [
        encode_kv_byte_address(
            tensor="v",
            kv_head=0,
            token=token,
            dimension=dimension,
        )
        for token in range(8)
        for dimension in range(8)
    ]
    assert all(
        right - left == 1
        for left, right in zip(first_fill_row_addresses, first_fill_row_addresses[1:])
        if left % 128 != 7
    )
    assert [first_fill_row_addresses[token * 8] for token in range(8)] == [
        first_fill_row_addresses[0] + token * 128 for token in range(8)
    ]


def test_key_mapping_covers_every_block_for_p53_and_p54() -> None:
    for producers in (53, 54):
        for kv_head in range(4):
            covered = set()
            for token in range(1024):
                location = key_producer_location(
                    producers=producers,
                    kv_head=kv_head,
                    token=token,
                    dimension=127,
                )
                covered.add((location.stream, location.producer, location.producer_block))
                assert location.byte_in_128bit_beat == location.stream * 8 + location.token_lane
            assert len(covered) == 128


def test_key_mapping_packs_both_streams_for_each_dimension() -> None:
    for producers in (53, 54):
        for kv_head in range(4):
            for block_slot in range(64):
                locations = [
                    key_producer_location(
                        producers=producers,
                        kv_head=kv_head,
                        token=stream * 512 + block_slot * 8 + token_lane,
                        dimension=37,
                    )
                    for stream in range(2)
                    for token_lane in range(8)
                ]
                assert len({(row.producer, row.producer_block) for row in locations}) == 1
                assert {row.stream for row in locations} == {0, 1}
                assert {row.dimension for row in locations} == {37}
                assert {row.byte_in_128bit_beat for row in locations} == set(range(16))


def test_audit_retracts_direct_fractional_vc0_fill_mapping() -> None:
    report = build_report(phase2=json.loads(PHASE2.read_text(encoding="utf-8")))

    assert report["llama7b_layer_shape"]["layer_kv_bytes"] == 128 * 1024 * 1024
    assert report["cluster_consumption"]["total_value_fill_bytes"] == 64 * 1024 * 1024
    assert report["cluster_consumption"]["key_stream_bytes"] == 64 * 1024 * 1024
    assert report["capacity_driven_residency"]["resident_bytes_per_layer"] == 2_228_224
    assert report["capacity_driven_residency"]["exact_planar_gather_segments_per_layer"] == 10
    assert report["capacity_driven_residency"]["tail_128_token_contiguous_segments"] == 8
    assert report["capacity_driven_residency"]["unresident_hbm_return_bytes_per_layer"] == 131_989_504
    placements = report["capacity_driven_residency"]["placement_options"]
    assert placements["remote_balanced_contiguous"]["remote_transport_bytes_per_layer"] == 2_228_224
    assert placements["locality_aware_owner_compute"]["remote_transport_bytes_per_layer"] == 0
    assert placements["locality_aware_owner_compute"]["local_resident_bytes_per_layer"] == 2_228_224
    assert placements["locality_aware_owner_compute"]["does_not_include"] == (
        "transient HBM-return transport"
    )
    assert report["historical_phase2_vc0"]["remote_transport_bytes"] == 1_949_696
    assert report["historical_phase2_vc0"]["direct_cluster_fill_compatible"] is False
    assert report["port_gap"]["whole_kv_tile_packets_256B"] == 4096
    assert report["port_gap"]["payload_equivalent_vc0_flits_per_value_fill_row"] == 2
    assert report["port_gap"]["consecutive_flits_form_one_value_fill_row"] is False
    assert report["port_gap"]["value_transpose_extent_bytes"] == 1024
    assert report["port_gap"]["key_paired_stream_transpose_extent_bytes"] == 2048
    assert report["one_buffer_transpose_reference"]["value"] == {
        "input_flits": 32,
        "output_rows": 16,
        "transfer_cycles_without_stall": 48,
        "minimum_target_ii_cycles": 49,
    }
    assert report["one_buffer_transpose_reference"]["key"] == {
        "input_flits": 64,
        "output_beats": 128,
        "transfer_cycles_without_stall": 192,
        "minimum_target_ii_cycles": 193,
    }
    assert report["one_buffer_transpose_reference"]["not_a_cluster_throughput_claim"] is True
    assert report["revision_effect"]["frontier_recost_allowed"] is False
    assert "cannot be wired directly" in render_markdown(report)
