"""Exact capacity-driven Llama7B K/V gather descriptor schedule."""

from __future__ import annotations

from dataclasses import dataclass, replace

from npu.sim.perf.attention_kv_tile_layout import BYTES_PER_KV_TILE


LAYERS = 32
TILES_PER_LAYER = 128
CLUSTERS = 16
RESIDENT_FULL_TILES = 2
RESIDENT_TAIL_TOKENS = 128
PLANE_BYTES = 128 * 1024
STREAM_BYTES = 64 * 1024
BLOCK_BYTES = 1024
TAIL_BYTES_PER_PLANE = 16 * 1024
TAIL_HBM_BYTES_PER_PLANE = PLANE_BYTES - TAIL_BYTES_PER_PLANE
RESIDENT_BYTES_PER_LAYER = 2_228_224
HBM_CORNER_ENDPOINTS = (0, 3, 12, 15)
ALL_PLANES = 8
HEAD_GROUPS = 4
WAVES = 8
TILES_PER_WAVE = 16
REFILL = "refill"
CONSUME = "consume"
HBM = "hbm"
RESIDENT = "resident"


@dataclass(frozen=True)
class KvGatherDescriptor:
    layer: int
    tile: int
    segment: int
    operation: str
    source: str
    source_endpoint: int
    destination_cluster: int
    plane: int
    canonical_base_address: int
    source_byte_address: int
    destination_byte_address: int
    payload_bytes: int
    last: bool


def _owner_cluster(layer: int, tile: int) -> int:
    return (layer * 3 + tile) % CLUSTERS


def _hbm_endpoint(layer: int, tile: int, plane: int) -> int:
    plane_term = 0 if plane == ALL_PLANES else plane
    return HBM_CORNER_ENDPOINTS[(layer + tile + plane_term) % len(HBM_CORNER_ENDPOINTS)]


def _hbm_address(layer: int, tile: int, canonical_address: int) -> int:
    return ((layer * TILES_PER_LAYER + tile) * BYTES_PER_KV_TILE) + canonical_address


def _resident_layer_base(layer: int) -> int:
    return layer * RESIDENT_BYTES_PER_LAYER


def _descriptor(
    *,
    layer: int,
    tile: int,
    segment: int,
    operation: str,
    source: str,
    plane: int,
    canonical_base_address: int,
    resident_offset: int,
    payload_bytes: int,
    last: bool = False,
) -> KvGatherDescriptor:
    destination_cluster = _owner_cluster(layer, tile)
    source_is_hbm = source == HBM
    source_address = (
        _hbm_address(layer, tile, canonical_base_address)
        if source_is_hbm
        else _resident_layer_base(layer) + resident_offset
    )
    destination_address = (
        _resident_layer_base(layer) + resident_offset
        if operation == REFILL
        else canonical_base_address
    )
    return KvGatherDescriptor(
        layer=layer,
        tile=tile,
        segment=segment,
        operation=operation,
        source=source,
        source_endpoint=(
            _hbm_endpoint(layer, tile, plane) if source_is_hbm else destination_cluster
        ),
        destination_cluster=destination_cluster,
        plane=plane,
        canonical_base_address=canonical_base_address,
        source_byte_address=source_address,
        destination_byte_address=destination_address,
        payload_bytes=payload_bytes,
        last=last,
    )


def layer_descriptors(layer: int) -> tuple[KvGatherDescriptor, ...]:
    if layer not in range(LAYERS):
        raise ValueError(f"layer must be in [0, {LAYERS - 1}]")
    rows: list[KvGatherDescriptor] = []

    # Refill the capacity-backed 2176-token prefix from HBM.
    for tile in range(RESIDENT_FULL_TILES):
        rows.append(
            _descriptor(
                layer=layer,
                tile=tile,
                segment=0,
                operation=REFILL,
                source=HBM,
                plane=ALL_PLANES,
                canonical_base_address=0,
                resident_offset=tile * BYTES_PER_KV_TILE,
                payload_bytes=BYTES_PER_KV_TILE,
            )
        )
    for plane in range(ALL_PLANES):
        rows.append(
            _descriptor(
                layer=layer,
                tile=2,
                segment=plane,
                operation=REFILL,
                source=HBM,
                plane=plane,
                canonical_base_address=plane * PLANE_BYTES,
                resident_offset=2 * BYTES_PER_KV_TILE + plane * TAIL_BYTES_PER_PLANE,
                payload_bytes=TAIL_BYTES_PER_PLANE,
            )
        )

    # Match the embodied hierarchy's group-major command cadence. Full K
    # planes are packet-permuted downstream into block/stream order. Tile 2
    # crosses the resident/HBM boundary, so its K plane is explicitly emitted
    # as 1 KiB block spans after the other 15 tiles in wave 0.
    for group in range(HEAD_GROUPS):
        for wave in range(WAVES):
            key_plane_base = group * PLANE_BYTES
            ordinary_tiles = list(
                range(wave * TILES_PER_WAVE, (wave + 1) * TILES_PER_WAVE)
            )
            if wave == 0:
                ordinary_tiles.remove(RESIDENT_FULL_TILES)
            for tile in ordinary_tiles:
                rows.append(
                    _descriptor(
                        layer=layer,
                        tile=tile,
                        segment=group * 2,
                        operation=CONSUME,
                        source=RESIDENT if tile < RESIDENT_FULL_TILES else HBM,
                        plane=group,
                        canonical_base_address=key_plane_base,
                        resident_offset=tile * BYTES_PER_KV_TILE + key_plane_base,
                        payload_bytes=PLANE_BYTES,
                    )
                )
            if wave == 0:
                for block in range(64):
                    for stream in range(2):
                        canonical_base = (
                            key_plane_base
                            + stream * STREAM_BYTES
                            + block * BLOCK_BYTES
                        )
                        resident = stream == 0 and block < 16
                        rows.append(
                            _descriptor(
                                layer=layer,
                                tile=RESIDENT_FULL_TILES,
                                segment=stream * 8 + block % 8,
                                operation=CONSUME,
                                source=RESIDENT if resident else HBM,
                                plane=group,
                                canonical_base_address=canonical_base,
                                resident_offset=(
                                    2 * BYTES_PER_KV_TILE
                                    + group * TAIL_BYTES_PER_PLANE
                                    + block * BLOCK_BYTES
                                ),
                                payload_bytes=BLOCK_BYTES,
                            )
                        )

            plane = HEAD_GROUPS + group
            for tile_lane in range(TILES_PER_WAVE):
                tile = wave * TILES_PER_WAVE + tile_lane
                canonical_plane_base = plane * PLANE_BYTES
                if tile < RESIDENT_FULL_TILES:
                    rows.append(
                        _descriptor(
                            layer=layer,
                            tile=tile,
                            segment=plane * 2,
                            operation=CONSUME,
                            source=RESIDENT,
                            plane=plane,
                            canonical_base_address=canonical_plane_base,
                            resident_offset=(
                                tile * BYTES_PER_KV_TILE + canonical_plane_base
                            ),
                            payload_bytes=PLANE_BYTES,
                        )
                    )
                elif tile == RESIDENT_FULL_TILES:
                    resident_offset = (
                        2 * BYTES_PER_KV_TILE + plane * TAIL_BYTES_PER_PLANE
                    )
                    rows.append(
                        _descriptor(
                            layer=layer,
                            tile=tile,
                            segment=plane * 2,
                            operation=CONSUME,
                            source=RESIDENT,
                            plane=plane,
                            canonical_base_address=canonical_plane_base,
                            resident_offset=resident_offset,
                            payload_bytes=TAIL_BYTES_PER_PLANE,
                        )
                    )
                    rows.append(
                        _descriptor(
                            layer=layer,
                            tile=tile,
                            segment=plane * 2 + 1,
                            operation=CONSUME,
                            source=HBM,
                            plane=plane,
                            canonical_base_address=(
                                canonical_plane_base + TAIL_BYTES_PER_PLANE
                            ),
                            resident_offset=0,
                            payload_bytes=TAIL_HBM_BYTES_PER_PLANE,
                        )
                    )
                else:
                    rows.append(
                        _descriptor(
                            layer=layer,
                            tile=tile,
                            segment=plane * 2,
                            operation=CONSUME,
                            source=HBM,
                            plane=plane,
                            canonical_base_address=canonical_plane_base,
                            resident_offset=0,
                            payload_bytes=PLANE_BYTES,
                        )
                    )
    return tuple(rows)


def llama7b_descriptors() -> tuple[KvGatherDescriptor, ...]:
    rows = [row for layer in range(LAYERS) for row in layer_descriptors(layer)]
    if not rows:
        raise AssertionError("exact K/V gather schedule is empty")
    rows[-1] = replace(rows[-1], last=True)
    return tuple(rows)


__all__ = [
    "ALL_PLANES",
    "CLUSTERS",
    "CONSUME",
    "HBM",
    "HBM_CORNER_ENDPOINTS",
    "HEAD_GROUPS",
    "KvGatherDescriptor",
    "LAYERS",
    "REFILL",
    "RESIDENT",
    "RESIDENT_BYTES_PER_LAYER",
    "TILES_PER_LAYER",
    "TILES_PER_WAVE",
    "WAVES",
    "layer_descriptors",
    "llama7b_descriptors",
]
