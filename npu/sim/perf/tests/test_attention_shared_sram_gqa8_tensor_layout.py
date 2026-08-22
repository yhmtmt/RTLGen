from __future__ import annotations

from npu.sim.perf.attention_shared_sram_gqa8_tensor_layout import (
    BLOCKS_PER_STREAM,
    HEAD_CONTEXT_BYTES,
    HEAD_DIM,
    K_BYTES_PER_HEAD,
    KV_HEADS,
    SHARED_MACROS_PER_HOME,
    STREAMS,
    TILE_CONTEXT_BYTES,
    TILE_TOKENS,
    V_BYTES_PER_HEAD,
    interleaved_bank,
    interleaved_row,
    k_beat_offset,
    k_prefetch_geometry,
    pack_kv_tile,
    token_index,
    unpack_k_beat,
    unpack_v_row,
    v_row_offset,
)


def _tensor(seed: int) -> list[list[list[int]]]:
    return [
        [
            [((seed + head * 17 + token * 7 + dimension * 3) % 256) - 128 for dimension in range(HEAD_DIM)]
            for token in range(TILE_TOKENS)
        ]
        for head in range(KV_HEADS)
    ]


def test_layout_capacity_is_one_mebibyte_with_equal_k_and_v_regions() -> None:
    assert K_BYTES_PER_HEAD == 128 * 1024
    assert V_BYTES_PER_HEAD == 128 * 1024
    assert HEAD_CONTEXT_BYTES == 256 * 1024
    assert TILE_CONTEXT_BYTES == 1024 * 1024


def test_offsets_cover_disjoint_contiguous_head_regions() -> None:
    offsets: set[int] = set()
    for head in range(KV_HEADS):
        for stream in range(STREAMS):
            for block in range(BLOCKS_PER_STREAM):
                for dimension in range(HEAD_DIM):
                    offset = k_beat_offset(kv_head=head, stream=stream, block_slot=block, dimension=dimension)
                    offsets.update(range(offset, offset + 8))
                for slice_index in range(16):
                    offset = v_row_offset(kv_head=head, stream=stream, block_slot=block, slice_index=slice_index)
                    offsets.update(range(offset, offset + 64))
    assert len(offsets) == TILE_CONTEXT_BYTES
    assert min(offsets) == 0
    assert max(offsets) == TILE_CONTEXT_BYTES - 1


def test_token_mapping_covers_each_tile_token_once() -> None:
    tokens = {
        token_index(stream=stream, block_slot=block, token_lane=lane)
        for stream in range(STREAMS)
        for block in range(BLOCKS_PER_STREAM)
        for lane in range(8)
    }
    assert tokens == set(range(TILE_TOKENS))


def test_round_trip_matches_dual_stream_k_beats_and_value_rows() -> None:
    keys = _tensor(11)
    values = _tensor(73)
    payload = pack_kv_tile(keys, values)
    assert len(payload) == TILE_CONTEXT_BYTES

    for head, stream, block, dimension in ((0, 0, 0, 0), (1, 1, 7, 63), (3, 1, 63, 127)):
        observed = unpack_k_beat(
            payload,
            kv_head=head,
            stream=stream,
            block_slot=block,
            dimension=dimension,
        )
        expected = tuple(
            keys[head][token_index(stream=stream, block_slot=block, token_lane=lane)][dimension]
            for lane in range(8)
        )
        assert observed == expected

    for head, stream, block, slice_index in ((0, 0, 0, 0), (2, 1, 11, 5), (3, 1, 63, 15)):
        observed = unpack_v_row(
            payload,
            kv_head=head,
            stream=stream,
            block_slot=block,
            slice_index=slice_index,
        )
        expected = tuple(
            tuple(
                values[head][token_index(stream=stream, block_slot=block, token_lane=token_lane)][
                    slice_index * 8 + dimension_lane
                ]
                for dimension_lane in range(8)
            )
            for token_lane in range(8)
        )
        assert observed == expected


def test_seventeen_way_interleave_is_reversible_at_word_granularity() -> None:
    for word in range(TILE_CONTEXT_BYTES // 128):
        offset = word * 128
        bank = interleaved_bank(offset)
        row = interleaved_row(offset)
        assert bank in range(SHARED_MACROS_PER_HOME)
        assert row * SHARED_MACROS_PER_HOME + bank == word


def test_k_prefetch_window_hides_macro_reads_behind_compute_with_two_buffers() -> None:
    geometry = k_prefetch_geometry()
    assert geometry.words_per_dimension_group == 128
    assert geometry.dimension_group == 16
    assert geometry.minimum_read_cycles == 8
    assert geometry.compute_cycles == 16
    assert geometry.buffer_bytes == 16 * 1024
    assert geometry.minimum_read_cycles <= geometry.compute_cycles
