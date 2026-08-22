"""Byte-exact GQA8 K/V layout for one 1024-token Llama7B tile.

The layout matches the existing dual-stream producer and value-SRAM service:

* one command handles one KV head and its eight query heads;
* each stream owns 64 blocks of eight tokens;
* a K beat contains eight token lanes for one head dimension (64 bits);
* a V row contains an 8-token by 8-dimension slice (512 bits).

Four 256 KiB head regions form one 1 MiB all-head tile context.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

KV_HEADS = 4
QUERY_HEADS_PER_KV = 8
HEAD_DIM = 128
TILE_TOKENS = 1024
STREAMS = 2
BLOCK_TOKENS = 8
BLOCKS_PER_STREAM = TILE_TOKENS // STREAMS // BLOCK_TOKENS
VALUE_SLICES = HEAD_DIM // BLOCK_TOKENS

K_BEAT_BYTES = BLOCK_TOKENS
V_ROW_BYTES = BLOCK_TOKENS * BLOCK_TOKENS
K_BYTES_PER_HEAD = TILE_TOKENS * HEAD_DIM
V_BYTES_PER_HEAD = TILE_TOKENS * HEAD_DIM
HEAD_CONTEXT_BYTES = K_BYTES_PER_HEAD + V_BYTES_PER_HEAD
TILE_CONTEXT_BYTES = KV_HEADS * HEAD_CONTEXT_BYTES

SHARED_WORD_BYTES = 128
SHARED_MACROS_PER_HOME = 17


def _check_index(name: str, value: int, limit: int) -> int:
    resolved = int(value)
    if resolved not in range(limit):
        raise ValueError(f"{name} must be in [0, {limit}), got {resolved}")
    return resolved


def _encode_s8(value: int) -> int:
    resolved = int(value)
    if not -128 <= resolved <= 127:
        raise ValueError(f"int8 tensor value is out of range: {resolved}")
    return resolved & 0xFF


def _decode_s8(value: int) -> int:
    return value - 256 if value >= 128 else value


def token_index(*, stream: int, block_slot: int, token_lane: int) -> int:
    stream = _check_index("stream", stream, STREAMS)
    block_slot = _check_index("block_slot", block_slot, BLOCKS_PER_STREAM)
    token_lane = _check_index("token_lane", token_lane, BLOCK_TOKENS)
    return ((stream * BLOCKS_PER_STREAM + block_slot) * BLOCK_TOKENS) + token_lane


def head_region_offset(kv_head: int) -> int:
    return _check_index("kv_head", kv_head, KV_HEADS) * HEAD_CONTEXT_BYTES


def k_beat_offset(*, kv_head: int, stream: int, block_slot: int, dimension: int) -> int:
    stream = _check_index("stream", stream, STREAMS)
    block_slot = _check_index("block_slot", block_slot, BLOCKS_PER_STREAM)
    dimension = _check_index("dimension", dimension, HEAD_DIM)
    beat_index = ((stream * BLOCKS_PER_STREAM + block_slot) * HEAD_DIM) + dimension
    return head_region_offset(kv_head) + beat_index * K_BEAT_BYTES


def v_row_offset(*, kv_head: int, stream: int, block_slot: int, slice_index: int) -> int:
    stream = _check_index("stream", stream, STREAMS)
    block_slot = _check_index("block_slot", block_slot, BLOCKS_PER_STREAM)
    slice_index = _check_index("slice_index", slice_index, VALUE_SLICES)
    row_index = ((stream * BLOCKS_PER_STREAM + block_slot) * VALUE_SLICES) + slice_index
    return head_region_offset(kv_head) + K_BYTES_PER_HEAD + row_index * V_ROW_BYTES


def shared_word_address(byte_offset: int) -> int:
    resolved = int(byte_offset)
    if resolved < 0 or resolved >= TILE_CONTEXT_BYTES:
        raise ValueError("byte_offset is outside one tile context")
    return resolved // SHARED_WORD_BYTES


def interleaved_bank(byte_offset: int, *, banks: int = SHARED_MACROS_PER_HOME) -> int:
    if banks <= 0:
        raise ValueError("banks must be positive")
    return shared_word_address(byte_offset) % banks


def interleaved_row(byte_offset: int, *, banks: int = SHARED_MACROS_PER_HOME) -> int:
    if banks <= 0:
        raise ValueError("banks must be positive")
    return shared_word_address(byte_offset) // banks


def pack_kv_tile(
    keys: Sequence[Sequence[Sequence[int]]],
    values: Sequence[Sequence[Sequence[int]]],
) -> bytes:
    """Pack ``[kv_head][token][dimension]`` signed-int8 tensors."""

    if len(keys) != KV_HEADS or len(values) != KV_HEADS:
        raise ValueError(f"keys and values must each contain {KV_HEADS} KV heads")
    payload = bytearray(TILE_CONTEXT_BYTES)
    for head in range(KV_HEADS):
        if len(keys[head]) != TILE_TOKENS or len(values[head]) != TILE_TOKENS:
            raise ValueError(f"head {head} must contain {TILE_TOKENS} tokens")
        for stream in range(STREAMS):
            for block_slot in range(BLOCKS_PER_STREAM):
                for dimension in range(HEAD_DIM):
                    offset = k_beat_offset(
                        kv_head=head,
                        stream=stream,
                        block_slot=block_slot,
                        dimension=dimension,
                    )
                    for lane in range(BLOCK_TOKENS):
                        token = token_index(
                            stream=stream,
                            block_slot=block_slot,
                            token_lane=lane,
                        )
                        if len(keys[head][token]) != HEAD_DIM:
                            raise ValueError(f"key head {head} token {token} must have {HEAD_DIM} dimensions")
                        payload[offset + lane] = _encode_s8(keys[head][token][dimension])
                for slice_index in range(VALUE_SLICES):
                    offset = v_row_offset(
                        kv_head=head,
                        stream=stream,
                        block_slot=block_slot,
                        slice_index=slice_index,
                    )
                    for token_lane in range(BLOCK_TOKENS):
                        token = token_index(
                            stream=stream,
                            block_slot=block_slot,
                            token_lane=token_lane,
                        )
                        if len(values[head][token]) != HEAD_DIM:
                            raise ValueError(f"value head {head} token {token} must have {HEAD_DIM} dimensions")
                        for dimension_lane in range(BLOCK_TOKENS):
                            dimension = slice_index * BLOCK_TOKENS + dimension_lane
                            payload[offset + token_lane * BLOCK_TOKENS + dimension_lane] = _encode_s8(
                                values[head][token][dimension]
                            )
    return bytes(payload)


def unpack_k_beat(payload: bytes, *, kv_head: int, stream: int, block_slot: int, dimension: int) -> tuple[int, ...]:
    offset = k_beat_offset(
        kv_head=kv_head,
        stream=stream,
        block_slot=block_slot,
        dimension=dimension,
    )
    if len(payload) != TILE_CONTEXT_BYTES:
        raise ValueError(f"payload must contain exactly {TILE_CONTEXT_BYTES} bytes")
    return tuple(_decode_s8(value) for value in payload[offset : offset + K_BEAT_BYTES])


def unpack_v_row(payload: bytes, *, kv_head: int, stream: int, block_slot: int, slice_index: int) -> tuple[tuple[int, ...], ...]:
    offset = v_row_offset(
        kv_head=kv_head,
        stream=stream,
        block_slot=block_slot,
        slice_index=slice_index,
    )
    if len(payload) != TILE_CONTEXT_BYTES:
        raise ValueError(f"payload must contain exactly {TILE_CONTEXT_BYTES} bytes")
    flat = tuple(_decode_s8(value) for value in payload[offset : offset + V_ROW_BYTES])
    return tuple(
        flat[token_lane * BLOCK_TOKENS : (token_lane + 1) * BLOCK_TOKENS]
        for token_lane in range(BLOCK_TOKENS)
    )


@dataclass(frozen=True)
class KPrefetchGeometry:
    banks: int
    words_per_dimension_group: int
    dimension_group: int
    minimum_read_cycles: int
    compute_cycles: int
    buffer_bytes: int


def k_prefetch_geometry(*, banks: int = SHARED_MACROS_PER_HOME) -> KPrefetchGeometry:
    """Return the no-conflict lower bound for one 16-dimension K window.

    One 1024-bit word holds 16 dimension beats for one 8-token block.  All 128
    stream/block slots therefore need 128 words per dimension window.  A
    double-buffered 16 KiB word window hides the eight-cycle, 17-bank fetch
    behind sixteen compute cycles.
    """

    if banks <= 0:
        raise ValueError("banks must be positive")
    words = STREAMS * BLOCKS_PER_STREAM
    dimension_group = SHARED_WORD_BYTES // K_BEAT_BYTES
    minimum_read_cycles = (words + banks - 1) // banks
    return KPrefetchGeometry(
        banks=banks,
        words_per_dimension_group=words,
        dimension_group=dimension_group,
        minimum_read_cycles=minimum_read_cycles,
        compute_cycles=dimension_group,
        buffer_bytes=words * SHARED_WORD_BYTES,
    )
