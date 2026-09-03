"""Canonical int8 GQA K/V tile addressing for the exact score32 datapath."""

from __future__ import annotations

from dataclasses import dataclass

from npu.sim.perf.attention_score32_exact_cluster_sram_service_gqa8 import (
    BLOCK_SLOTS_PER_STREAM,
    STREAMS,
    VALUE_SLICES,
    exact_local_cluster_gqa8_command_block_counts,
    exact_local_cluster_gqa8_slot_bases,
)


TILE_TOKENS = 1024
HEAD_DIM = 128
KV_HEADS = 4
QUERY_HEADS_PER_KV = 8
ELEMENT_BITS = 8
ELEMENT_BYTES = 1
TOKENS_PER_BLOCK = 8
DIMENSIONS_PER_SLICE = 8
TOKENS_PER_STREAM = TILE_TOKENS // STREAMS
BYTES_PER_HEAD_TILE = TILE_TOKENS * HEAD_DIM * ELEMENT_BYTES
BYTES_PER_KV_TILE = 2 * KV_HEADS * BYTES_PER_HEAD_TILE
FILL_ROW_BYTES = TOKENS_PER_BLOCK * DIMENSIONS_PER_SLICE * ELEMENT_BYTES
FILL_ROWS_PER_HEAD_TILE = BYTES_PER_HEAD_TILE // FILL_ROW_BYTES
VALUE_BLOCK_BYTES = TOKENS_PER_BLOCK * HEAD_DIM
KEY_PAIRED_BLOCK_BYTES = 2 * VALUE_BLOCK_BYTES
INGRESS_FLIT_BYTES = 32
VALUE_BLOCK_INPUT_FLITS = VALUE_BLOCK_BYTES // INGRESS_FLIT_BYTES
KEY_BLOCK_PAIR_INPUT_FLITS = KEY_PAIRED_BLOCK_BYTES // INGRESS_FLIT_BYTES
VALUE_BLOCK_OUTPUT_ROWS = VALUE_BLOCK_BYTES // FILL_ROW_BYTES
VALUE_BLOCKS_PER_HEAD_TILE = STREAMS * BLOCK_SLOTS_PER_STREAM
VALUE_HEAD_TILE_ONE_BUFFER_FILL_CYCLES = (
    VALUE_BLOCKS_PER_HEAD_TILE * (VALUE_BLOCK_INPUT_FLITS + VALUE_BLOCK_OUTPUT_ROWS)
    + VALUE_BLOCKS_PER_HEAD_TILE
    - 1
)
KEY_BLOCK_PAIR_OUTPUT_BEATS = HEAD_DIM
KEY_BLOCK_PAIRS_PER_HEAD_TILE = BLOCK_SLOTS_PER_STREAM
KEY_HEAD_TILE_ONE_BUFFER_FILL_CYCLES = (
    KEY_BLOCK_PAIRS_PER_HEAD_TILE
    * (KEY_BLOCK_PAIR_INPUT_FLITS + KEY_BLOCK_PAIR_OUTPUT_BEATS)
    + KEY_BLOCK_PAIRS_PER_HEAD_TILE
    - 1
)
KEY_STAGE_COMMAND_INPUT_CYCLES = 2 * HEAD_DIM


@dataclass(frozen=True)
class KvCoordinate:
    tensor: str
    kv_head: int
    token: int
    dimension: int


@dataclass(frozen=True)
class ValueFillLocation:
    stream: int
    block_slot: int
    value_slice: int
    byte_in_row: int
    flat_fill_row: int


@dataclass(frozen=True)
class KeyProducerLocation:
    producer: int
    producer_block: int
    stream: int
    dimension: int
    token_lane: int
    byte_in_128bit_beat: int


@dataclass(frozen=True)
class KvRangeSegment:
    base_address: int
    payload_bytes: int


@dataclass(frozen=True)
class KvTransposeService:
    input_flits: int
    output_beats: int
    transfer_cycles_without_stall: int
    minimum_target_ii_cycles: int


@dataclass(frozen=True)
class KeyIngressArchitectureService:
    architecture: str
    transpose_buffers: int
    stage_write_bits: int
    target_from_first_flit: bool
    head_cycles_without_stall: int
    ingress_floor_cycles: int


def kv_transpose_service(*, tensor: str) -> KvTransposeService:
    """Return the one-buffer RTL service bound with no fill/drain overlap."""

    if tensor == "v":
        input_flits = VALUE_BLOCK_INPUT_FLITS
        output_beats = VALUE_BLOCK_OUTPUT_ROWS
    elif tensor == "k":
        input_flits = KEY_BLOCK_PAIR_INPUT_FLITS
        output_beats = KEY_BLOCK_PAIR_OUTPUT_BEATS
    else:
        raise ValueError("tensor must be 'k' or 'v'")
    return KvTransposeService(
        input_flits=input_flits,
        output_beats=output_beats,
        transfer_cycles_without_stall=input_flits + output_beats,
        minimum_target_ii_cycles=input_flits + output_beats + 1,
    )


def key_ingress_architecture_service(*, architecture: str) -> KeyIngressArchitectureService:
    """Return exact full-head service bounds for concrete K ingress organizations."""

    ingress_floor = KEY_BLOCK_PAIRS_PER_HEAD_TILE * KEY_BLOCK_PAIR_INPUT_FLITS
    rows = {
        "one_buffer_serial": (1, 128, False, KEY_HEAD_TILE_ONE_BUFFER_FILL_CYCLES),
        "pingpong_serial": (
            2,
            128,
            True,
            KEY_BLOCK_PAIR_INPUT_FLITS
            + KEY_BLOCK_PAIRS_PER_HEAD_TILE * KEY_BLOCK_PAIR_OUTPUT_BEATS,
        ),
        "one_buffer_wide": (
            1,
            256,
            False,
            KEY_BLOCK_PAIRS_PER_HEAD_TILE
            * (KEY_BLOCK_PAIR_INPUT_FLITS + KEY_BLOCK_PAIR_OUTPUT_BEATS // 2)
            + KEY_BLOCK_PAIRS_PER_HEAD_TILE
            - 1,
        ),
        "pingpong_wide_auto": (
            2,
            256,
            True,
            ingress_floor + KEY_BLOCK_PAIR_OUTPUT_BEATS // 2,
        ),
    }
    if architecture not in rows:
        raise ValueError(f"unknown K ingress architecture: {architecture}")
    buffers, write_bits, auto_target, cycles = rows[architecture]
    return KeyIngressArchitectureService(
        architecture=architecture,
        transpose_buffers=buffers,
        stage_write_bits=write_bits,
        target_from_first_flit=auto_target,
        head_cycles_without_stall=cycles,
        ingress_floor_cycles=ingress_floor,
    )


def _bounded(value: int, *, limit: int, label: str) -> int:
    result = int(value)
    if result not in range(limit):
        raise ValueError(f"{label} must be in [0, {limit - 1}]")
    return result


def encode_kv_byte_address(
    *,
    tensor: str,
    kv_head: int,
    token: int,
    dimension: int,
) -> int:
    """Encode one byte in canonical ``K heads, then V heads`` tile order."""

    if tensor not in {"k", "v"}:
        raise ValueError("tensor must be 'k' or 'v'")
    head = _bounded(kv_head, limit=KV_HEADS, label="kv_head")
    token_index = _bounded(token, limit=TILE_TOKENS, label="token")
    dim = _bounded(dimension, limit=HEAD_DIM, label="dimension")
    tensor_index = 0 if tensor == "k" else 1
    return (((tensor_index * KV_HEADS + head) * TILE_TOKENS + token_index) * HEAD_DIM) + dim


def decode_kv_byte_address(address: int) -> KvCoordinate:
    resolved = _bounded(address, limit=BYTES_PER_KV_TILE, label="address")
    plane, dimension = divmod(resolved, HEAD_DIM)
    tensor_head, token = divmod(plane, TILE_TOKENS)
    tensor_index, kv_head = divmod(tensor_head, KV_HEADS)
    return KvCoordinate(
        tensor="k" if tensor_index == 0 else "v",
        kv_head=kv_head,
        token=token,
        dimension=dimension,
    )


def kv_token_range_segments(*, token_start: int, token_count: int) -> tuple[KvRangeSegment, ...]:
    """Return minimal contiguous spans for a token range in the planar tile layout."""

    start = _bounded(token_start, limit=TILE_TOKENS, label="token_start")
    count = int(token_count)
    if count <= 0 or start + count > TILE_TOKENS:
        raise ValueError("token_count must be positive and remain inside the tile")
    plane_bytes = count * HEAD_DIM
    spans = [
        KvRangeSegment(
            base_address=encode_kv_byte_address(
                tensor=tensor,
                kv_head=kv_head,
                token=start,
                dimension=0,
            ),
            payload_bytes=plane_bytes,
        )
        for tensor in ("k", "v")
        for kv_head in range(KV_HEADS)
    ]
    merged: list[KvRangeSegment] = []
    for span in spans:
        if merged and merged[-1].base_address + merged[-1].payload_bytes == span.base_address:
            previous = merged[-1]
            merged[-1] = KvRangeSegment(
                base_address=previous.base_address,
                payload_bytes=previous.payload_bytes + span.payload_bytes,
            )
        else:
            merged.append(span)
    if sum(span.payload_bytes for span in merged) != count * 2 * KV_HEADS * HEAD_DIM:
        raise AssertionError("K/V token-range byte conservation failed")
    return tuple(merged)


def value_fill_location(*, token: int, dimension: int) -> ValueFillLocation:
    """Map a V byte to the existing 512-bit cluster fill interface."""

    token_index = _bounded(token, limit=TILE_TOKENS, label="token")
    dim = _bounded(dimension, limit=HEAD_DIM, label="dimension")
    stream, token_in_stream = divmod(token_index, TOKENS_PER_STREAM)
    block_slot, token_lane = divmod(token_in_stream, TOKENS_PER_BLOCK)
    value_slice, dimension_lane = divmod(dim, DIMENSIONS_PER_SLICE)
    flat_fill_row = (
        stream * BLOCK_SLOTS_PER_STREAM * VALUE_SLICES
        + block_slot * VALUE_SLICES
        + value_slice
    )
    return ValueFillLocation(
        stream=stream,
        block_slot=block_slot,
        value_slice=value_slice,
        byte_in_row=token_lane * DIMENSIONS_PER_SLICE + dimension_lane,
        flat_fill_row=flat_fill_row,
    )


def decode_value_fill_byte(*, flat_fill_row: int, byte_in_row: int) -> tuple[int, int]:
    row = _bounded(flat_fill_row, limit=FILL_ROWS_PER_HEAD_TILE, label="flat_fill_row")
    byte = _bounded(byte_in_row, limit=FILL_ROW_BYTES, label="byte_in_row")
    stream, row_in_stream = divmod(row, BLOCK_SLOTS_PER_STREAM * VALUE_SLICES)
    block_slot, value_slice = divmod(row_in_stream, VALUE_SLICES)
    token_lane, dimension_lane = divmod(byte, DIMENSIONS_PER_SLICE)
    token = stream * TOKENS_PER_STREAM + block_slot * TOKENS_PER_BLOCK + token_lane
    dimension = value_slice * DIMENSIONS_PER_SLICE + dimension_lane
    return token, dimension


def key_producer_location(
    *,
    producers: int,
    kv_head: int,
    token: int,
    dimension: int,
) -> KeyProducerLocation:
    """Map a K byte to the p53/p54 producer input beat that consumes it."""

    producer_count = int(producers)
    if producer_count not in {53, 54}:
        raise ValueError("producers must be 53 or 54")
    group = _bounded(kv_head, limit=KV_HEADS, label="kv_head")
    token_index = _bounded(token, limit=TILE_TOKENS, label="token")
    dim = _bounded(dimension, limit=HEAD_DIM, label="dimension")
    stream, token_in_stream = divmod(token_index, TOKENS_PER_STREAM)
    block_slot, token_lane = divmod(token_in_stream, TOKENS_PER_BLOCK)
    bases = exact_local_cluster_gqa8_slot_bases(
        producers=producer_count,
        group_index=group,
    )
    counts = exact_local_cluster_gqa8_command_block_counts(
        producers=producer_count,
        group_index=group,
    )
    for producer, (base, count) in enumerate(zip(bases, counts)):
        if base <= block_slot < base + count:
            producer_block = block_slot - base
            return KeyProducerLocation(
                producer=producer,
                producer_block=producer_block,
                stream=stream,
                dimension=dim,
                token_lane=token_lane,
                byte_in_128bit_beat=stream * TOKENS_PER_BLOCK + token_lane,
            )
    raise AssertionError("corrected p53/p54 slot schedule did not cover the K block")


__all__ = [
    "BYTES_PER_HEAD_TILE",
    "BYTES_PER_KV_TILE",
    "FILL_ROW_BYTES",
    "FILL_ROWS_PER_HEAD_TILE",
    "HEAD_DIM",
    "KV_HEADS",
    "KeyProducerLocation",
    "KEY_BLOCK_PAIR_INPUT_FLITS",
    "KEY_BLOCK_PAIR_OUTPUT_BEATS",
    "KEY_BLOCK_PAIRS_PER_HEAD_TILE",
    "KEY_HEAD_TILE_ONE_BUFFER_FILL_CYCLES",
    "KeyIngressArchitectureService",
    "KEY_PAIRED_BLOCK_BYTES",
    "KEY_STAGE_COMMAND_INPUT_CYCLES",
    "KvRangeSegment",
    "KvTransposeService",
    "KvCoordinate",
    "TILE_TOKENS",
    "VALUE_BLOCK_BYTES",
    "VALUE_BLOCK_INPUT_FLITS",
    "VALUE_BLOCKS_PER_HEAD_TILE",
    "VALUE_BLOCK_OUTPUT_ROWS",
    "VALUE_HEAD_TILE_ONE_BUFFER_FILL_CYCLES",
    "ValueFillLocation",
    "decode_kv_byte_address",
    "decode_value_fill_byte",
    "encode_kv_byte_address",
    "key_producer_location",
    "key_ingress_architecture_service",
    "kv_transpose_service",
    "kv_token_range_segments",
    "value_fill_location",
]
