#!/usr/bin/env python3
"""Analytical shared-SRAM residency and placement model for Llama 7B.

This module is intentionally read-only.  It models the placement of a KV
cache in a shared SRAM and the packetization needed to move resident ranges
between compute clusters.  It does not model HBM timing or claim that a
transient SRAM cache reduces the HBM capacity needed for the complete KV
cache.

The historical Phase-2 schedule used a fractional byte share per tile.  That
policy is retained as an explicit mode so it can be compared with capacity-
driven whole-token policies without silently treating the historical 112
remote contexts as a consequence of SRAM capacity.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from dataclasses import dataclass
from typing import Any, Iterable

DEFAULT_SEQUENCE_LENGTH = 131_072
DEFAULT_TILE_TOKENS = 1_024
DEFAULT_LAYERS = 32
DEFAULT_KV_HEADS = 4
DEFAULT_HEAD_DIM = 128
DEFAULT_KV_BITS = 8
DEFAULT_SHARED_CAPACITY_BYTES = 68 * 1024 * 1024
DEFAULT_CLUSTERS = 16
DEFAULT_PACKET_PAYLOAD = 256
FLIT_BYTES = 32
TRANSIENT = "transient"
PERSISTENT = "persistent"
SUPPORTED_PERSISTENCE = (TRANSIENT, PERSISTENT)

FRACTIONAL_SMEAR = "fractional_smear"
LAYER_BALANCED_CONTIGUOUS = "layer_balanced_contiguous"
LOCALITY_AWARE = "locality_aware"
SUPPORTED_MODES = (
    FRACTIONAL_SMEAR,
    LAYER_BALANCED_CONTIGUOUS,
    LOCALITY_AWARE,
)

JsonDict = dict[str, Any]


def _ceil_div(numerator: int, denominator: int) -> int:
    if numerator < 0 or denominator <= 0:
        raise ValueError("ceil division requires a non-negative numerator and positive denominator")
    return (numerator + denominator - 1) // denominator


def _require_positive(name: str, value: int) -> int:
    if value <= 0:
        raise ValueError(f"{name} must be positive")
    return value


@dataclass(frozen=True)
class ResidencyConfig:
    """Shape and transport parameters for one analytical residency run."""

    sequence_length: int = DEFAULT_SEQUENCE_LENGTH
    tile_tokens: int = DEFAULT_TILE_TOKENS
    layers: int = DEFAULT_LAYERS
    kv_heads: int = DEFAULT_KV_HEADS
    head_dim: int = DEFAULT_HEAD_DIM
    kv_bits: int = DEFAULT_KV_BITS
    shared_capacity_bytes: int = DEFAULT_SHARED_CAPACITY_BYTES
    clusters: int = DEFAULT_CLUSTERS
    packet_payload: int = DEFAULT_PACKET_PAYLOAD
    persistence_mode: str = TRANSIENT

    def __post_init__(self) -> None:
        for name in (
            "sequence_length",
            "tile_tokens",
            "layers",
            "kv_heads",
            "head_dim",
            "kv_bits",
            "shared_capacity_bytes",
            "clusters",
            "packet_payload",
        ):
            _require_positive(name, int(getattr(self, name)))
        if self.kv_bits % 8:
            raise ValueError("kv_bits must be byte-aligned")
        if self.packet_payload < FLIT_BYTES:
            raise ValueError(f"packet_payload must be at least {FLIT_BYTES} bytes")
        if self.packet_payload % FLIT_BYTES:
            raise ValueError(f"packet_payload must be a multiple of {FLIT_BYTES} bytes")
        if self.shared_capacity_bytes % self.clusters:
            raise ValueError("shared_capacity_bytes must divide evenly across clusters")
        if self.persistence_mode not in SUPPORTED_PERSISTENCE:
            raise ValueError(
                f"persistence_mode must be one of {SUPPORTED_PERSISTENCE}, "
                f"got {self.persistence_mode!r}"
            )

    @property
    def kv_bytes_per_token(self) -> int:
        return 2 * self.kv_heads * self.head_dim * (self.kv_bits // 8)

    @property
    def tile_count(self) -> int:
        return _ceil_div(self.sequence_length, self.tile_tokens)

    @property
    def full_kv_bytes(self) -> int:
        return self.sequence_length * self.layers * self.kv_bytes_per_token

    @property
    def full_tile_bytes(self) -> int:
        return self.tile_tokens * self.kv_bytes_per_token

    def tile_token_count(self, tile_index: int) -> int:
        if tile_index < 0 or tile_index >= self.tile_count:
            raise ValueError(f"tile index {tile_index} is outside the configured sequence")
        start = tile_index * self.tile_tokens
        return min(self.tile_tokens, self.sequence_length - start)


@dataclass(frozen=True)
class ResidencyContext:
    """One contiguous resident tile range and its explicit ownership/home."""

    context_id: int
    layer: int
    tile_index: int
    token_start: int
    token_count: int
    payload_bytes: int
    owner_cluster: int
    home_cluster: int
    owner_rotation_offset: int
    packet_count: int
    flit_count: int

    @property
    def remote(self) -> bool:
        return self.owner_cluster != self.home_cluster

    def as_dict(self) -> JsonDict:
        return {
            "context_id": self.context_id,
            "layer": self.layer,
            "tile_index": self.tile_index,
            "token_start": self.token_start,
            "token_count": self.token_count,
            "payload_bytes": self.payload_bytes,
            "owner_cluster": self.owner_cluster,
            "home_cluster": self.home_cluster,
            "owner_rotation_offset": self.owner_rotation_offset,
            "remote": self.remote,
            "packet_count": self.packet_count,
            "flit_count": self.flit_count,
        }


def _historical_home(*, owner_cluster: int, tile_index: int, clusters: int) -> int:
    """Reproduce the old offset=1, stride=3 wave mapping.

    With 16 clusters and eight waves this makes exactly wave four local and
    the other seven waves remote: 112 remote contexts per layer.  This is a
    placement policy, not a capacity calculation.
    """

    wave = tile_index // clusters
    return (owner_cluster + 1 + ((wave + 1) * 3)) % clusters


def _home_for(mode: str, *, owner_cluster: int, tile_index: int, clusters: int) -> int:
    if mode == LOCALITY_AWARE:
        return owner_cluster
    return _historical_home(
        owner_cluster=owner_cluster,
        tile_index=tile_index,
        clusters=clusters,
    )


def _context(
    *,
    context_id: int,
    layer: int,
    tile_index: int,
    token_start: int,
    token_count: int,
    payload_bytes: int,
    config: ResidencyConfig,
    mode: str,
    owner_rotation_offset: int = 0,
) -> ResidencyContext:
    if token_count <= 0 or payload_bytes <= 0:
        raise ValueError("resident contexts must contain a positive token range and payload")
    normalized_offset = owner_rotation_offset % config.clusters
    owner_cluster = (normalized_offset + tile_index) % config.clusters
    home_cluster = _home_for(
        mode,
        owner_cluster=owner_cluster,
        tile_index=tile_index,
        clusters=config.clusters,
    )
    return ResidencyContext(
        context_id=context_id,
        layer=layer,
        tile_index=tile_index,
        token_start=token_start,
        token_count=token_count,
        payload_bytes=payload_bytes,
        owner_cluster=owner_cluster,
        home_cluster=home_cluster,
        owner_rotation_offset=normalized_offset,
        packet_count=_ceil_div(payload_bytes, config.packet_payload),
        flit_count=_ceil_div(payload_bytes, FLIT_BYTES),
    )


def _fractional_contexts(
    config: ResidencyConfig,
    *,
    fractional_tile_bytes: int | None,
    mode: str,
) -> list[ResidencyContext]:
    if fractional_tile_bytes is None:
        raise ValueError(
            "fractional_smear requires explicit fractional_tile_bytes; "
            "the historical value is not a defaulted physical fact"
        )
    _require_positive("fractional_tile_bytes", fractional_tile_bytes)
    contexts: list[ResidencyContext] = []
    context_id = 0
    for layer in range(config.layers):
        for tile_index in range(config.tile_count):
            token_count = config.tile_token_count(tile_index)
            # Preserve a uniform share while scaling only a shortened final tile.
            payload_bytes = _ceil_div(
                fractional_tile_bytes * token_count,
                config.tile_tokens,
            )
            actual_tile_bytes = token_count * config.kv_bytes_per_token
            if payload_bytes > actual_tile_bytes:
                raise ValueError(
                    f"fractional payload {payload_bytes} exceeds tile {tile_index} "
                    f"KV bytes {actual_tile_bytes}"
                )
            contexts.append(
                _context(
                    context_id=context_id,
                    layer=layer,
                    tile_index=tile_index,
                    token_start=tile_index * config.tile_tokens,
                    token_count=token_count,
                    payload_bytes=payload_bytes,
                    config=config,
                    mode=mode,
                )
            )
            context_id += 1
    return contexts


def _balanced_token_counts(config: ResidencyConfig) -> list[int]:
    minimum_required = config.layers * config.kv_bytes_per_token
    if config.shared_capacity_bytes < minimum_required:
        raise ValueError(
            "shared capacity cannot allocate one whole token to every layer: "
            f"need {minimum_required} bytes, have {config.shared_capacity_bytes}"
        )
    total_slots = min(
        config.sequence_length * config.layers,
        config.shared_capacity_bytes // config.kv_bytes_per_token,
    )
    base, remainder = divmod(total_slots, config.layers)
    return [base + (1 if layer < remainder else 0) for layer in range(config.layers)]


def _whole_token_contexts(config: ResidencyConfig, *, mode: str) -> list[ResidencyContext]:
    token_counts = _balanced_token_counts(config)
    contexts: list[ResidencyContext] = []
    context_id = 0
    prior_context_count = 0
    for layer, resident_tokens in enumerate(token_counts):
        layer_context_count = _ceil_div(resident_tokens, config.tile_tokens)
        owner_rotation_offset = prior_context_count % config.clusters
        token_start = 0
        tile_index = 0
        while token_start < resident_tokens:
            token_count = min(config.tile_tokens, resident_tokens - token_start)
            payload_bytes = token_count * config.kv_bytes_per_token
            contexts.append(
                _context(
                    context_id=context_id,
                    layer=layer,
                    tile_index=tile_index,
                    token_start=token_start,
                    token_count=token_count,
                    payload_bytes=payload_bytes,
                    config=config,
                    mode=mode,
                    owner_rotation_offset=owner_rotation_offset,
                )
            )
            context_id += 1
            token_start += token_count
            tile_index += 1
        if tile_index != layer_context_count:
            raise AssertionError("whole-token layer context count mismatch")
        prior_context_count += layer_context_count
    return contexts


def _distribution(contexts: Iterable[ResidencyContext]) -> list[JsonDict]:
    counts = Counter(context.payload_bytes for context in contexts)
    return [
        {"payload_bytes": payload_bytes, "context_count": count}
        for payload_bytes, count in sorted(counts.items())
    ]


def _layer_owner_offsets(
    contexts: Iterable[ResidencyContext],
    *,
    layers: int,
) -> list[int]:
    offsets: list[int | None] = [None] * layers
    for context in contexts:
        current = offsets[context.layer]
        if current is None:
            offsets[context.layer] = context.owner_rotation_offset
        elif current != context.owner_rotation_offset:
            raise AssertionError(f"layer {context.layer} uses multiple owner rotation offsets")
    if any(offset is None for offset in offsets):
        raise AssertionError("every layer must have at least one resident context")
    return [int(offset) for offset in offsets]


def _wave_assignment_audit(
    config: ResidencyConfig,
    *,
    layer_offsets: list[int],
    rotation_rule: str,
) -> JsonDict:
    expected = list(range(config.clusters))
    complete_waves_per_layer = config.tile_count // config.clusters
    checked_wave_count = 0
    for layer, offset in enumerate(layer_offsets):
        for wave in range(complete_waves_per_layer):
            first_tile = wave * config.clusters
            owners = sorted(
                (offset + tile_index) % config.clusters
                for tile_index in range(first_tile, first_tile + config.clusters)
            )
            if owners != expected:
                raise AssertionError(
                    f"layer {layer} wave {wave} is not one tile per compute cluster: {owners}"
                )
            checked_wave_count += 1
    return {
        "wave_size_tiles": config.clusters,
        "complete_waves_per_layer": complete_waves_per_layer,
        "checked_wave_count": checked_wave_count,
        "one_tile_per_cluster_per_complete_wave": True,
        "layer_owner_rotation_offsets": layer_offsets,
        "rotation_rule": rotation_rule,
    }


def _home_capacity_audit(
    config: ResidencyConfig,
    *,
    contexts: list[ResidencyContext],
    mode: str,
) -> JsonDict:
    per_home_capacity = config.shared_capacity_bytes // config.clusters
    rows: list[JsonDict] = []
    for home in range(config.clusters):
        home_contexts = [context for context in contexts if context.home_cluster == home]
        remote_contexts = [context for context in home_contexts if context.remote]
        local_contexts = [context for context in home_contexts if not context.remote]
        resident_load = sum(context.payload_bytes for context in home_contexts)
        remote_bytes = sum(context.payload_bytes for context in remote_contexts)
        local_bytes = sum(context.payload_bytes for context in local_contexts)
        rows.append(
            {
                "home_cluster": home,
                "capacity_bytes": per_home_capacity,
                "resident_load_bytes": resident_load,
                "unused_capacity_bytes": max(0, per_home_capacity - resident_load),
                "overload_bytes": max(0, resident_load - per_home_capacity),
                "context_count": len(home_contexts),
                "remote_context_count": len(remote_contexts),
                "local_context_count": len(local_contexts),
                "remote_transport_bytes": remote_bytes,
                "local_resident_bytes": local_bytes,
            }
        )
    total_load = sum(int(row["resident_load_bytes"]) for row in rows)
    expected_load = sum(context.payload_bytes for context in contexts)
    if total_load != expected_load:
        raise AssertionError(
            f"per-home load accounting mismatch: expected {expected_load}, observed {total_load}"
        )
    overloaded = [row for row in rows if int(row["overload_bytes"]) > 0]
    result = {
        "total_capacity_bytes": config.shared_capacity_bytes,
        "per_home_capacity_bytes": per_home_capacity,
        "per_home_loads": rows,
        "max_home_load_bytes": max(int(row["resident_load_bytes"]) for row in rows),
        "min_home_load_bytes": min(int(row["resident_load_bytes"]) for row in rows),
        "overloaded_home_count": len(overloaded),
        "overloaded_home_clusters": [int(row["home_cluster"]) for row in overloaded],
        "capacity_ok": not overloaded,
        "load_conservation": total_load == expected_load,
        "enforcement": "fail_closed" if mode == LOCALITY_AWARE else "diagnostic",
    }
    if overloaded and mode == LOCALITY_AWARE:
        details = ", ".join(
            f"home {row['home_cluster']} load={row['resident_load_bytes']} "
            f"capacity={per_home_capacity}"
            for row in overloaded
        )
        raise ValueError(f"locality-aware placement exceeds per-home capacity: {details}")
    return result


def _historical_window(config: ResidencyConfig, fractional_tile_bytes: int | None) -> JsonDict | None:
    if fractional_tile_bytes is None:
        return None
    per_layer: list[ResidencyContext] = []
    for tile_index in range(config.tile_count):
        token_count = config.tile_token_count(tile_index)
        payload_bytes = _ceil_div(fractional_tile_bytes * token_count, config.tile_tokens)
        per_layer.append(
            _context(
                context_id=tile_index,
                layer=0,
                tile_index=tile_index,
                token_start=tile_index * config.tile_tokens,
                token_count=token_count,
                payload_bytes=payload_bytes,
                config=config,
                mode=FRACTIONAL_SMEAR,
            )
        )
    remote = [context for context in per_layer if context.remote]
    local = [context for context in per_layer if not context.remote]
    remote_bytes = sum(context.payload_bytes for context in remote)
    local_bytes = sum(context.payload_bytes for context in local)
    return {
        "scope": "one_layer_full_sequence",
        "contexts_per_layer": len(per_layer),
        "context_count": len(per_layer),
        "remote_context_count": len(remote),
        "local_context_count": len(local),
        "remote_context_count_per_layer": len(remote),
        "local_context_count_per_layer": len(local),
        "remote_bytes": remote_bytes,
        "local_bytes": local_bytes,
        "remote_transport_bytes_per_layer": remote_bytes,
        "local_resident_bytes_per_layer": local_bytes,
        "remote_packet_count": sum(context.packet_count for context in remote),
        "remote_flit_count": sum(context.flit_count for context in remote),
        "payload_bytes_per_full_tile": fractional_tile_bytes,
        "full_model_layer_multiplier": config.layers,
        "full_model_remote_context_count": len(remote) * config.layers,
        "full_model_local_context_count": len(local) * config.layers,
        "full_model_remote_transport_bytes": remote_bytes * config.layers,
        "full_model_local_resident_bytes": local_bytes * config.layers,
        "policy_note": (
            "The 112 remote contexts arise from the historical eight-wave home "
            "mapping for one layer; full-model counts multiply by the layer count. "
            "They are not implied by shared capacity."
        ),
    }


def build_residency_report(
    mode: str,
    *,
    sequence_length: int = DEFAULT_SEQUENCE_LENGTH,
    tile_tokens: int = DEFAULT_TILE_TOKENS,
    layers: int = DEFAULT_LAYERS,
    kv_heads: int = DEFAULT_KV_HEADS,
    head_dim: int = DEFAULT_HEAD_DIM,
    kv_bits: int = DEFAULT_KV_BITS,
    shared_capacity_bytes: int = DEFAULT_SHARED_CAPACITY_BYTES,
    clusters: int = DEFAULT_CLUSTERS,
    packet_payload: int = DEFAULT_PACKET_PAYLOAD,
    fractional_tile_bytes: int | None = None,
    persistence_mode: str = TRANSIENT,
) -> JsonDict:
    """Build one placement report without touching RTL, files, or transport state."""

    if mode not in SUPPORTED_MODES:
        raise ValueError(f"unsupported residency mode {mode!r}; choose from {SUPPORTED_MODES}")
    config = ResidencyConfig(
        sequence_length=sequence_length,
        tile_tokens=tile_tokens,
        layers=layers,
        kv_heads=kv_heads,
        head_dim=head_dim,
        kv_bits=kv_bits,
        shared_capacity_bytes=shared_capacity_bytes,
        clusters=clusters,
        packet_payload=packet_payload,
        persistence_mode=persistence_mode,
    )
    if mode == FRACTIONAL_SMEAR:
        contexts = _fractional_contexts(
            config,
            fractional_tile_bytes=fractional_tile_bytes,
            mode=mode,
        )
    else:
        contexts = _whole_token_contexts(config, mode=mode)

    resident_bytes = sum(context.payload_bytes for context in contexts)
    if resident_bytes > config.shared_capacity_bytes:
        raise ValueError(
            f"residency requires {resident_bytes} bytes but shared capacity is "
            f"{config.shared_capacity_bytes} bytes"
        )
    remote_contexts = [context for context in contexts if context.remote]
    local_contexts = [context for context in contexts if not context.remote]
    unused_capacity = config.shared_capacity_bytes - resident_bytes
    if resident_bytes + unused_capacity != config.shared_capacity_bytes:
        raise AssertionError("shared capacity conservation failed")
    layer_offsets = _layer_owner_offsets(contexts, layers=config.layers)
    wave_assignment = _wave_assignment_audit(
        config,
        layer_offsets=layer_offsets,
        rotation_rule=(
            "fixed_zero_offset_full_sequence_coverage"
            if mode == FRACTIONAL_SMEAR
            else "cumulative_prior_resident_context_count_modulo_clusters"
        ),
    )
    home_capacity = _home_capacity_audit(config, contexts=contexts, mode=mode)

    packet_count = sum(context.packet_count for context in contexts)
    flit_count = sum(context.flit_count for context in contexts)
    remote_packet_count = sum(context.packet_count for context in remote_contexts)
    local_packet_count = sum(context.packet_count for context in local_contexts)
    remote_flit_count = sum(context.flit_count for context in remote_contexts)
    local_flit_count = sum(context.flit_count for context in local_contexts)
    remote_payload_bytes = sum(context.payload_bytes for context in remote_contexts)
    local_payload_bytes = sum(context.payload_bytes for context in local_contexts)
    wire_bytes = flit_count * FLIT_BYTES
    remote_wire_bytes = remote_flit_count * FLIT_BYTES
    local_wire_bytes = local_flit_count * FLIT_BYTES
    token_resident = all(
        context.payload_bytes == context.token_count * config.kv_bytes_per_token
        for context in contexts
    )
    max_payload = max(context.payload_bytes for context in contexts)
    report: JsonDict = {
        "model": "llama7b_shared_sram_residency_v1",
        "mode": mode,
        "shape": {
            "sequence_length": config.sequence_length,
            "tile_tokens": config.tile_tokens,
            "tile_count": config.tile_count,
            "layers": config.layers,
            "kv_heads": config.kv_heads,
            "head_dim": config.head_dim,
            "kv_bits": config.kv_bits,
            "kv_bytes_per_token": config.kv_bytes_per_token,
            "full_tile_bytes": config.full_tile_bytes,
            "full_kv_bytes": config.full_kv_bytes,
        },
        "placement": {
            "owner_policy": (
                "tile_index_modulo_clusters"
                if mode == FRACTIONAL_SMEAR
                else "tile_index_plus_layer_rotation_modulo_clusters"
            ),
            "home_policy": "owner_cluster" if mode == LOCALITY_AWARE else "historical_wave_offset_1_stride_3",
            "clusters": config.clusters,
            "wave_assignment": wave_assignment,
            "home_capacity": home_capacity,
            "resident_contexts": [context.as_dict() for context in contexts],
        },
        "residency": {
            "resident_bytes": resident_bytes,
            "resident_mib": resident_bytes / (1024 * 1024),
            "context_count": len(contexts),
            "remote_context_count": len(remote_contexts),
            "local_context_count": len(local_contexts),
            "max_context_payload_bytes": max_payload,
            "context_payload_distribution": _distribution(contexts),
            "whole_token_residency": token_resident,
            "capacity_bytes": config.shared_capacity_bytes,
            "unused_capacity_bytes": unused_capacity,
            "capacity_conservation": {
                "resident_bytes": resident_bytes,
                "unused_capacity_bytes": unused_capacity,
                "capacity_bytes": config.shared_capacity_bytes,
                "conserved": resident_bytes + unused_capacity == config.shared_capacity_bytes,
            },
        },
        "transport": {
            "packet_payload_bytes": config.packet_payload,
            "flit_bytes": FLIT_BYTES,
            "packet_count": packet_count,
            "flit_count": flit_count,
            "payload_bytes": resident_bytes,
            "wire_bytes": wire_bytes,
            "flit_padding_bytes": wire_bytes - resident_bytes,
            "remote_packet_count": remote_packet_count,
            "local_packet_count": local_packet_count,
            "remote_flit_count": remote_flit_count,
            "local_flit_count": local_flit_count,
            "remote_transport_bytes": remote_payload_bytes,
            "local_resident_bytes": local_payload_bytes,
            "remote_wire_bytes": remote_wire_bytes,
            "local_wire_bytes": local_wire_bytes,
            "remote_flit_padding_bytes": remote_wire_bytes - remote_payload_bytes,
            "local_flit_padding_bytes": local_wire_bytes - local_payload_bytes,
        },
        "hbm": {
            "persistence_mode": config.persistence_mode,
            "hbm_bytes": config.full_kv_bytes,
            "full_kv_storage_bytes": config.full_kv_bytes,
            "resident_cache_bytes": resident_bytes,
            "unresident_kv_bytes": config.full_kv_bytes - resident_bytes,
            "storage_savings_bytes": 0,
            "baseline_decode_read_bytes": config.full_kv_bytes,
            "gross_read_avoidance": resident_bytes,
            "gross_read_avoidance_bytes": resident_bytes,
            "refill_bytes": resident_bytes if config.persistence_mode == TRANSIENT else 0,
            "net_hbm_read_bytes": (
                config.full_kv_bytes
                - resident_bytes
                + (resident_bytes if config.persistence_mode == TRANSIENT else 0)
            ),
            "net_read_avoidance_bytes": (
                0 if config.persistence_mode == TRANSIENT else resident_bytes
            ),
            "note": (
                "HBM bytes are complete KV backing storage. Gross read avoidance is "
                "the resident payload; transient residency refills that payload each "
                "decode, so its net read avoidance is zero. Persistent residency has "
                "zero refill in this analytical accounting."
            ),
        },
        "historical_comparison": _historical_window(config, fractional_tile_bytes),
        "assumptions": [
            "KV layout is two tensors (K and V), with kv_heads x head_dim values per token.",
            "A context is one contiguous token range within one layer.",
            "A packet carries at most packet_payload bytes and each flit carries 32 bytes.",
            "Whole-token owner assignment rotates each layer by cumulative prior resident contexts.",
            "Fractional smear retains tile_index modulo clusters because every layer covers all tiles.",
            "Each SRAM home receives an equal share of aggregate shared capacity.",
            "Home placement and overload enforcement are explicit.",
            "HBM remains the complete KV backing store and is outside this model.",
            "HBM read accounting assumes one full KV read per decode before residency effects.",
        ],
    }
    return report


def compare_residency_policies(
    *,
    fractional_tile_bytes: int = 17_408,
    **kwargs: int,
) -> dict[str, JsonDict]:
    """Return all requested policies for one KV shape."""

    return {
        mode: build_residency_report(
            mode,
            fractional_tile_bytes=fractional_tile_bytes if mode == FRACTIONAL_SMEAR else None,
            **kwargs,
        )
        for mode in SUPPORTED_MODES
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=SUPPORTED_MODES, default=LAYER_BALANCED_CONTIGUOUS)
    parser.add_argument("--kv-heads", type=int, default=DEFAULT_KV_HEADS)
    parser.add_argument("--fractional-tile-bytes", type=int, default=None)
    parser.add_argument("--persistence-mode", choices=SUPPORTED_PERSISTENCE, default=TRANSIENT)
    parser.add_argument("--pretty", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    report = build_residency_report(
        args.mode,
        kv_heads=args.kv_heads,
        fractional_tile_bytes=args.fractional_tile_bytes,
        persistence_mode=args.persistence_mode,
    )
    print(json.dumps(report, indent=2 if args.pretty else None, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
