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
    "KvCoordinate",
    "TILE_TOKENS",
    "ValueFillLocation",
    "decode_kv_byte_address",
    "decode_value_fill_byte",
    "encode_kv_byte_address",
    "key_producer_location",
    "value_fill_location",
]
