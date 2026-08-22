#!/usr/bin/env python3
"""Audit SRAM access granularity and energy for the Llama 7B shared stream.

The audit consumes the checked-in residency model and CACTI per-macro metrics.
It deliberately keeps SRAM traffic separate from HBM accounting: transient
and persistent residency select the residency-model traffic input, but this
module does not invent an HBM controller or HBM energy model.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
if __package__ in {None, ""}:
    sys.path.insert(0, str(REPO_ROOT))

from npu.eval.model_llama7b_shared_sram_residency import (
    DEFAULT_CLUSTERS,
    DEFAULT_HEAD_DIM,
    DEFAULT_KV_BITS,
    DEFAULT_KV_HEADS,
    DEFAULT_LAYERS,
    DEFAULT_PACKET_PAYLOAD,
    DEFAULT_SEQUENCE_LENGTH,
    DEFAULT_TILE_TOKENS,
    FRACTIONAL_SMEAR,
    LOCALITY_AWARE,
    PERSISTENT,
    TRANSIENT,
    build_residency_report,
)


LOCAL_CAPACITY_METRICS = (
    REPO_ROOT / "runs/designs/sram/llama7b_attention_local_capacity_v1/sram_metrics.json"
)
TILE_BUFFER_METRICS = (
    REPO_ROOT / "runs/designs/sram/llama7b_attention_tile_buffers_v1/sram_metrics.json"
)

DEFAULT_FRACTIONAL_TILE_BYTES = 17_408
DEFAULT_SHARED_CAPACITY_BYTES = 68 * 1024 * 1024
FLIT_BYTES = 32
BURST_FLITS = 4
NATIVE_256_WIDTH = 256


class SramAuditError(ValueError):
    """Raised when a CACTI entry or access accounting contract is invalid."""


JsonDict = dict[str, Any]


def _ceil_div(numerator: int, denominator: int) -> int:
    return (numerator + denominator - 1) // denominator


def _positive_number(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise SramAuditError(f"CACTI field {field!r} must be a finite number")
    if value <= 0:
        raise SramAuditError(f"CACTI field {field!r} must be positive")
    return float(value)


@dataclass(frozen=True)
class CactiMacro:
    """One physical SRAM macro and its per-access CACTI values."""

    name: str
    source_path: str
    pdk: str
    capacity_bytes: int
    width_bits: int
    bus_width_bits: int
    word_size_bytes: int
    access_time_ns: float
    read_energy_pj: float
    write_energy_pj: float
    area_um2: float

    @classmethod
    def from_entry(cls, entry: JsonDict, *, source_path: Path) -> "CactiMacro":
        instance = entry.get("instance")
        metrics = entry.get("metrics")
        if not isinstance(instance, dict) or not isinstance(metrics, dict):
            raise SramAuditError(f"invalid CACTI entry in {source_path}")
        raw = metrics.get("raw")
        if not isinstance(raw, dict):
            raise SramAuditError(f"CACTI entry {instance.get('name')!r} has no raw metrics")

        def positive_int(field: str) -> int:
            value = instance.get(field)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise SramAuditError(
                    f"CACTI entry {instance.get('name')!r} field {field!r} must be a positive integer"
                )
            return value

        name = instance.get("name")
        pdk = instance.get("pdk")
        if not isinstance(name, str) or not name or not isinstance(pdk, str) or not pdk:
            raise SramAuditError(f"CACTI entry in {source_path} lacks name/pdk")
        width_bits = positive_int("width")
        word_size_bytes = positive_int("word_size_bytes")
        if word_size_bytes != _ceil_div(width_bits, 8):
            raise SramAuditError(
                f"CACTI entry {name!r} width/word mismatch: {width_bits} bits, "
                f"{word_size_bytes} bytes"
            )
        capacity_bytes = positive_int("size_bytes")
        bus_width_bits = positive_int("bus_width_bits")
        return cls(
            name=name,
            source_path=str(source_path),
            pdk=pdk,
            capacity_bytes=capacity_bytes,
            width_bits=width_bits,
            bus_width_bits=bus_width_bits,
            word_size_bytes=word_size_bytes,
            access_time_ns=_positive_number(raw.get("access_time_ns"), "access_time_ns"),
            read_energy_pj=_positive_number(raw.get("read_energy_nj"), "read_energy_nj") * 1000.0,
            write_energy_pj=_positive_number(raw.get("write_energy_nj"), "write_energy_nj") * 1000.0,
            area_um2=_positive_number(raw.get("area_mm2"), "area_mm2") * 1_000_000.0,
        )

    def as_dict(self) -> JsonDict:
        return {
            "name": self.name,
            "source_path": self.source_path,
            "pdk": self.pdk,
            "capacity_bytes": self.capacity_bytes,
            "capacity_kib": self.capacity_bytes / 1024,
            "width_bits": self.width_bits,
            "bus_width_bits": self.bus_width_bits,
            "word_size_bytes": self.word_size_bytes,
            "access_time_ns": self.access_time_ns,
            "read_energy_pj_per_access": self.read_energy_pj,
            "write_energy_pj_per_access": self.write_energy_pj,
            "area_um2": self.area_um2,
            "area_mm2": self.area_um2 / 1_000_000.0,
        }


def load_cacti_entries(path: Path) -> dict[str, CactiMacro]:
    """Load all usable per-macro CACTI entries from one metrics JSON file."""

    try:
        document = json.loads(path.read_text())
    except FileNotFoundError as exc:
        raise SramAuditError(f"CACTI metrics file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SramAuditError(f"invalid CACTI JSON in {path}: {exc}") from exc
    entries = document.get("instances") if isinstance(document, dict) else None
    if not isinstance(entries, list) or not entries:
        raise SramAuditError(f"CACTI metrics file has no instances: {path}")
    macros: dict[str, CactiMacro] = {}
    for entry in entries:
        # Some manifests declare logical buffers whose CACTI run is absent.
        # They are not usable comparison points, but should not invalidate
        # complete entries from the same manifest.
        if not isinstance(entry, dict) or not isinstance(entry.get("metrics"), dict):
            continue
        raw = entry["metrics"].get("raw")
        if not isinstance(raw, dict) or any(
            raw.get(field) is None
            for field in ("access_time_ns", "read_energy_nj", "write_energy_nj", "area_mm2")
        ):
            continue
        macro = CactiMacro.from_entry(entry, source_path=path)
        if macro.name in macros:
            raise SramAuditError(f"duplicate CACTI instance {macro.name!r} in {path}")
        macros[macro.name] = macro
    return macros


def load_selected_macros(
    *,
    local_capacity_path: Path = LOCAL_CAPACITY_METRICS,
    tile_buffer_path: Path = TILE_BUFFER_METRICS,
) -> tuple[CactiMacro, CactiMacro]:
    """Load the selected 1024-bit macro and the available native 256-bit macro."""

    local = load_cacti_entries(local_capacity_path)
    try:
        selected = local["local_capacity_chunk_02_256kib"]
    except KeyError as exc:
        raise SramAuditError("selected 256 KiB/1024-bit CACTI macro is missing") from exc
    if selected.capacity_bytes != 256 * 1024 or selected.width_bits != 1024:
        raise SramAuditError("selected CACTI macro is not 256 KiB/1024-bit")

    tile = load_cacti_entries(tile_buffer_path)
    native_candidates = [macro for macro in tile.values() if macro.width_bits == NATIVE_256_WIDTH]
    if not native_candidates:
        raise SramAuditError("no native 256-bit CACTI macro is available")
    native = next(
        (macro for macro in native_candidates if macro.name == "kv_tile_read_buffer"),
        max(native_candidates, key=lambda macro: macro.capacity_bytes),
    )
    return selected, native


def _residency_traffic(
    *,
    mode: str,
    fractional_tile_bytes: int,
    persistence_mode: str,
    scope: str,
    shared_capacity_bytes: int,
    placement: str,
    sequence_length: int,
    tile_tokens: int,
    layers: int,
    kv_heads: int,
    head_dim: int,
    kv_bits: int,
    clusters: int,
    packet_payload: int,
) -> JsonDict:
    report = build_residency_report(
        mode,
        sequence_length=sequence_length,
        tile_tokens=tile_tokens,
        layers=layers,
        kv_heads=kv_heads,
        head_dim=head_dim,
        kv_bits=kv_bits,
        clusters=clusters,
        packet_payload=packet_payload,
        fractional_tile_bytes=fractional_tile_bytes if mode == FRACTIONAL_SMEAR else None,
        persistence_mode=persistence_mode,
        shared_capacity_bytes=shared_capacity_bytes,
    )
    if placement not in {"remote", "local"}:
        raise SramAuditError("placement must be 'remote' or 'local'")
    contexts = [
        context
        for context in report["placement"]["resident_contexts"]
        if bool(context["remote"]) == (placement == "remote")
        and (scope == "full_model" or context["layer"] == 0)
    ]
    if not contexts:
        raise SramAuditError(
            f"residency model produced no {placement} contexts for scope {scope!r}"
        )
    payload_bytes = sum(int(context["payload_bytes"]) for context in contexts)
    packet_count = sum(int(context["packet_count"]) for context in contexts)
    flit_count = sum(int(context["flit_count"]) for context in contexts)
    model_flit_bytes = flit_count * FLIT_BYTES
    if packet_count <= 0 or flit_count <= 0:
        raise SramAuditError("residency model produced non-positive transport counts")
    return {
        "scope": scope,
        "mode": mode,
        "placement": placement,
        "shape": report["shape"],
        "clusters": report["placement"]["clusters"],
        "shared_capacity_bytes": report["residency"]["capacity_bytes"],
        "packet_payload_bytes": report["transport"]["packet_payload_bytes"],
        "persistence_mode": persistence_mode,
        "context_count": len(contexts),
        "payload_bytes": payload_bytes,
        "packet_count": packet_count,
        "flit_count": flit_count,
        "flit_bytes": FLIT_BYTES,
        "flit_payload_bytes": model_flit_bytes,
        "flit_padding_bytes": model_flit_bytes - payload_bytes,
        "context_payload_bytes": [int(context["payload_bytes"]) for context in contexts],
        "source_read_bytes": payload_bytes,
        "destination_write_bytes": payload_bytes if placement == "remote" else 0,
        "source_read_is_remote_transport": placement == "remote",
        "destination_write_is_remote_transport": placement == "remote",
        "transport_packet_count": packet_count if placement == "remote" else 0,
        "transport_flit_count": flit_count if placement == "remote" else 0,
        "persistence_note": (
            "Transient/persistent selection is inherited as a residency-model input. "
            "It does not change this SRAM access count and "
            "does not model HBM behavior."
        ),
        "placement_note": (
            "Remote placement reads shared source storage and writes every flit into the "
            "destination local buffer."
            if placement == "remote"
            else "Locality-aware placement reads local shared storage without transport or destination writes."
        ),
        "residency_model": report["model"],
    }


def _combine_historical_source_traffic(remote: JsonDict, local_bypass: JsonDict) -> JsonDict:
    """Combine remote and bypassed contexts into the complete source-read workload."""

    for field in (
        "scope",
        "mode",
        "persistence_mode",
        "shape",
        "clusters",
        "shared_capacity_bytes",
        "packet_payload_bytes",
    ):
        if remote[field] != local_bypass[field]:
            raise SramAuditError(f"remote/local historical traffic disagrees on {field}")
    payload_bytes = int(remote["payload_bytes"]) + int(local_bypass["payload_bytes"])
    packet_count = int(remote["packet_count"]) + int(local_bypass["packet_count"])
    flit_count = int(remote["flit_count"]) + int(local_bypass["flit_count"])
    context_payload_bytes = [
        *remote["context_payload_bytes"],
        *local_bypass["context_payload_bytes"],
    ]
    if sum(context_payload_bytes) != payload_bytes:
        raise SramAuditError("combined source traffic does not conserve payload bytes")
    return {
        "scope": remote["scope"],
        "mode": remote["mode"],
        "placement": "historical_remote_plus_local_bypass",
        "persistence_mode": remote["persistence_mode"],
        "shape": remote["shape"],
        "clusters": remote["clusters"],
        "shared_capacity_bytes": remote["shared_capacity_bytes"],
        "packet_payload_bytes": remote["packet_payload_bytes"],
        "context_count": int(remote["context_count"]) + int(local_bypass["context_count"]),
        "remote_context_count": int(remote["context_count"]),
        "local_bypass_context_count": int(local_bypass["context_count"]),
        "payload_bytes": payload_bytes,
        "remote_payload_bytes": int(remote["payload_bytes"]),
        "local_bypass_payload_bytes": int(local_bypass["payload_bytes"]),
        "packet_count": packet_count,
        "flit_count": flit_count,
        "flit_bytes": FLIT_BYTES,
        "flit_payload_bytes": flit_count * FLIT_BYTES,
        "flit_padding_bytes": flit_count * FLIT_BYTES - payload_bytes,
        "context_payload_bytes": context_payload_bytes,
        "source_read_bytes": payload_bytes,
        "destination_write_bytes": int(remote["payload_bytes"]),
        "transport_packet_count": int(remote["transport_packet_count"]),
        "transport_flit_count": int(remote["transport_flit_count"]),
        "local_bypass_packet_count": int(local_bypass["packet_count"]),
        "local_bypass_flit_count": int(local_bypass["flit_count"]),
        "residency_model": remote["residency_model"],
        "source_read_note": (
            "Source shared SRAM serves every resident context: remote transport plus local bypass."
        ),
        "destination_write_note": (
            "Only remote transport flits write the existing destination local buffer."
        ),
    }


def _access_accounting(
    *,
    macro: CactiMacro,
    payload_bytes: int,
    flit_count: int,
    context_payload_bytes: list[int],
    coalesce_flits: int,
    label: str,
) -> JsonDict:
    if payload_bytes <= 0 or flit_count <= 0 or coalesce_flits <= 0:
        raise SramAuditError("access accounting requires positive payload, flits, and coalescing")
    if not context_payload_bytes or sum(context_payload_bytes) != payload_bytes:
        raise SramAuditError("context payloads do not conserve the residency payload")
    expected_flits = sum(_ceil_div(context_payload, FLIT_BYTES) for context_payload in context_payload_bytes)
    if flit_count != expected_flits:
        raise SramAuditError(
            f"residency flit count {flit_count} does not match payload {payload_bytes}"
        )
    if coalesce_flits * FLIT_BYTES > macro.word_size_bytes:
        raise SramAuditError(
            f"{label} coalesces {coalesce_flits} flits into more bytes than macro word"
        )
    full_groups = 0
    tail_flits = 0
    access_count = 0
    useful_flit_bytes = 0
    partial_access_count = 0
    for context_payload in context_payload_bytes:
        context_flits = _ceil_div(context_payload, FLIT_BYTES)
        context_full_groups, context_tail_flits = divmod(context_flits, coalesce_flits)
        full_groups += context_full_groups
        tail_flits += context_tail_flits
        access_count += context_full_groups + (1 if context_tail_flits else 0)
        useful_flit_bytes += context_flits * FLIT_BYTES
        if coalesce_flits * FLIT_BYTES < macro.word_size_bytes:
            partial_access_count += context_full_groups
        if context_tail_flits:
            partial_access_count += 1
        elif context_payload % (coalesce_flits * FLIT_BYTES):
            # A final flit can be only partially useful even when it occupies
            # a complete coalescing group (notably the native 256-bit case).
            partial_access_count += 1
    macro_touched_bytes = access_count * macro.word_size_bytes
    flit_padding_bytes = useful_flit_bytes - payload_bytes
    macro_word_padding_bytes = macro_touched_bytes - payload_bytes
    coalesced_flit_groups = full_groups if coalesce_flits > 1 else 0
    useful_bytes_per_access = payload_bytes / access_count
    return {
        "label": label,
        "macro": macro.as_dict(),
        "coalesce_flits": coalesce_flits,
        "coalesced_flit_groups": coalesced_flit_groups,
        "coalesced_flit_count": coalesced_flit_groups * coalesce_flits,
        "full_group_count": full_groups,
        "tail_flit_count": tail_flits,
        "access_count": access_count,
        "macro_bytes_per_access": macro.word_size_bytes,
        "useful_bytes_per_access": useful_bytes_per_access,
        "flit_padding_bytes": flit_padding_bytes,
        "macro_word_padding_bytes": macro_word_padding_bytes,
        "byte_masked_access_count": partial_access_count,
        "fully_utilized_access_count": access_count - partial_access_count,
        "aligned_payload": all(
            context_payload % (coalesce_flits * FLIT_BYTES) == 0
            for context_payload in context_payload_bytes
        ),
        "coalescing_note": (
            f"{coalesce_flits} {FLIT_BYTES * 8}-bit flits are coalesced per macro access"
            if coalesce_flits > 1
            else "one flit is issued per macro access; no flit coalescing"
        ),
    }


def _with_directional_energy(profile: JsonDict, *, macro: CactiMacro) -> JsonDict:
    read_energy = profile["access_count"] * macro.read_energy_pj
    write_energy = profile["access_count"] * macro.write_energy_pj
    payload_bytes = profile["useful_bytes_per_access"] * profile["access_count"]
    profile["source_read"] = {
        "access_count": profile["access_count"],
        "energy_pj": read_energy,
        "energy_nj": read_energy / 1000.0,
        "energy_per_useful_byte_pj": read_energy / payload_bytes,
        "energy_basis": "CACTI read_energy per one macro access",
    }
    profile["destination_write"] = {
        "access_count": profile["access_count"],
        "energy_pj": write_energy,
        "energy_nj": write_energy / 1000.0,
        "energy_per_useful_byte_pj": write_energy / payload_bytes,
        "energy_basis": "CACTI write_energy per one macro access",
    }
    profile["total_sram_energy_pj"] = read_energy + write_energy
    profile["total_sram_energy_nj"] = (read_energy + write_energy) / 1000.0
    profile["total_energy_per_useful_byte_pj"] = (read_energy + write_energy) / payload_bytes
    return profile


def _operation(
    profile: JsonDict,
    *,
    macro: CactiMacro,
    operation: str,
    role: str,
) -> JsonDict:
    if operation not in {"read", "write"}:
        raise SramAuditError("operation must be 'read' or 'write'")
    energy_per_access = macro.read_energy_pj if operation == "read" else macro.write_energy_pj
    access_count = int(profile["access_count"])
    payload_bytes = profile["useful_bytes_per_access"] * access_count
    energy_pj = access_count * energy_per_access
    return {
        "role": role,
        "operation": operation,
        "macro": macro.as_dict(),
        "access_count": access_count,
        "energy_pj_per_access": energy_per_access,
        "energy_pj": energy_pj,
        "energy_nj": energy_pj / 1000.0,
        "energy_per_useful_byte_pj": energy_pj / payload_bytes,
        "access_time_ns": macro.access_time_ns,
        "coalesce_flits": profile["coalesce_flits"],
        "useful_bytes_per_access": profile["useful_bytes_per_access"],
        "flit_padding_bytes": profile["flit_padding_bytes"],
        "macro_word_padding_bytes": profile["macro_word_padding_bytes"],
        "byte_masked_access_count": profile["byte_masked_access_count"],
        "fully_utilized_access_count": profile["fully_utilized_access_count"],
    }


def _zero_destination_write() -> JsonDict:
    return {
        "role": "destination_local_buffer",
        "operation": "write",
        "macro": None,
        "access_count": 0,
        "energy_pj_per_access": 0.0,
        "energy_pj": 0.0,
        "energy_nj": 0.0,
        "energy_per_useful_byte_pj": 0.0,
        "access_time_ns": 0.0,
        "transport_write": False,
        "reason": "locality-aware residency supplies the consumer locally",
    }


def _capacity_pack(macro: CactiMacro, capacity_bytes: int) -> JsonDict:
    macro_count = _ceil_div(capacity_bytes, macro.capacity_bytes)
    provided = macro_count * macro.capacity_bytes
    return {
        "required_capacity_bytes": capacity_bytes,
        "macro_count": macro_count,
        "provided_capacity_bytes": provided,
        "slack_bytes": provided - capacity_bytes,
        "area_um2": macro_count * macro.area_um2,
        "area_mm2": macro_count * macro.area_um2 / 1_000_000.0,
        "capacity_note": (
            "Area is the macro count needed for the source shared-SRAM capacity pack only."
        ),
    }


def _primitive_profiles(
    traffic: JsonDict,
    *,
    selected: CactiMacro,
    native: CactiMacro,
) -> dict[str, JsonDict]:
    payload_bytes = int(traffic["payload_bytes"])
    flit_count = int(traffic["flit_count"])
    context_payload_bytes = traffic["context_payload_bytes"]
    profiles = {
        "selected_1024b_macro_burst4": _access_accounting(
            macro=selected,
            payload_bytes=payload_bytes,
            flit_count=flit_count,
            context_payload_bytes=context_payload_bytes,
            coalesce_flits=BURST_FLITS,
            label="256KiB/1024-bit macro with 4x256-bit burst adapter",
        ),
        "selected_1024b_macro_naive_flit": _access_accounting(
            macro=selected,
            payload_bytes=payload_bytes,
            flit_count=flit_count,
            context_payload_bytes=context_payload_bytes,
            coalesce_flits=1,
            label="256KiB/1024-bit macro, one macro access per 256-bit flit",
        ),
        "native_256b_macro": _access_accounting(
            macro=native,
            payload_bytes=payload_bytes,
            flit_count=flit_count,
            context_payload_bytes=context_payload_bytes,
            coalesce_flits=1,
            label="native 256-bit-width macro",
        ),
    }
    for profile in profiles.values():
        macro = selected if profile["macro"]["name"] == selected.name else native
        _with_directional_energy(profile, macro=macro)
        profile["access_time_ns"] = macro.access_time_ns
    return profiles


def _compose_profile(
    *,
    label: str,
    source_primitive_name: str,
    source_primitive: JsonDict,
    source_macro: CactiMacro,
    payload_bytes: int,
    shared_capacity_bytes: int,
    destination_primitive: JsonDict | None,
    destination_macro: CactiMacro | None,
    locality_aware: bool,
) -> JsonDict:
    source_read = _operation(
        source_primitive,
        macro=source_macro,
        operation="read",
        role="local_shared_storage" if locality_aware else "remote_shared_source_storage",
    )
    if locality_aware:
        destination_write = _zero_destination_write()
    else:
        if destination_primitive is None or destination_macro is None:
            raise SramAuditError("remote composition requires a destination primitive and macro")
        destination_write = _operation(
            destination_primitive,
            macro=destination_macro,
            operation="write",
            role="destination_local_kv_tile_read_buffer",
        )
        destination_write["transport_write"] = True
    total_energy_pj = source_read["energy_pj"] + destination_write["energy_pj"]
    source_capacity_pack = _capacity_pack(source_macro, shared_capacity_bytes)
    endpoint_times = [source_read["access_time_ns"]]
    if destination_write["access_count"]:
        endpoint_times.append(destination_write["access_time_ns"])
    return {
        "label": label,
        "path": "locality_aware_local_read" if locality_aware else "remote_shared_to_local_buffer",
        "source_primitive": source_primitive_name,
        "source_read": source_read,
        "destination_write": destination_write,
        "source_shared_capacity_pack": source_capacity_pack,
        "destination_capacity_pack": None,
        "destination_area_note": (
            "The destination is the existing local kv_tile_read_buffer; no second 68 MiB "
            "capacity pack or ranked destination area is added."
            if not locality_aware
            else "No destination transport buffer is accessed for locality-aware residency."
        ),
        "total_sram_energy_pj": total_energy_pj,
        "total_sram_energy_nj": total_energy_pj / 1000.0,
        "total_energy_per_useful_byte_pj": total_energy_pj / payload_bytes,
        "total_layer_energy_pj": total_energy_pj,
        "total_layer_energy_nj": total_energy_pj / 1000.0,
        "total_layer_energy_per_total_source_byte_pj": total_energy_pj / payload_bytes,
        "total_source_read_bytes": payload_bytes,
        "remote_only_energy_per_useful_byte_pj": None,
        "source_capacity_area_um2": source_capacity_pack["area_um2"],
        "source_capacity_area_mm2": source_capacity_pack["area_mm2"],
        "endpoint_access_time_bound_ns": max(endpoint_times),
    }


def _compose_historical_remote_profile(
    *,
    label: str,
    source_primitive_name: str,
    total_source_primitive: JsonDict,
    remote_source_primitive: JsonDict,
    local_bypass_primitive: JsonDict,
    source_macro: CactiMacro,
    destination_primitive: JsonDict,
    destination_macro: CactiMacro,
    total_source_bytes: int,
    remote_payload_bytes: int,
    local_bypass_bytes: int,
    shared_capacity_bytes: int,
) -> JsonDict:
    total_source_read = _operation(
        total_source_primitive,
        macro=source_macro,
        operation="read",
        role="historical_total_shared_source_storage",
    )
    remote_source_read = _operation(
        remote_source_primitive,
        macro=source_macro,
        operation="read",
        role="remote_shared_source_component",
    )
    local_bypass_source_read = _operation(
        local_bypass_primitive,
        macro=source_macro,
        operation="read",
        role="local_bypass_shared_source_component",
    )
    if (
        remote_source_read["access_count"] + local_bypass_source_read["access_count"]
        != total_source_read["access_count"]
    ):
        raise SramAuditError("remote and local-bypass source accesses do not sum to total source")
    if not math.isclose(
        remote_source_read["energy_pj"] + local_bypass_source_read["energy_pj"],
        total_source_read["energy_pj"],
        rel_tol=1e-12,
        abs_tol=1e-9,
    ):
        raise SramAuditError("remote and local-bypass source energies do not sum to total source")
    destination_write = _operation(
        destination_primitive,
        macro=destination_macro,
        operation="write",
        role="destination_local_kv_tile_read_buffer",
    )
    destination_write["transport_write"] = True
    total_layer_energy_pj = total_source_read["energy_pj"] + destination_write["energy_pj"]
    remote_only_energy_pj = remote_source_read["energy_pj"] + destination_write["energy_pj"]
    source_capacity_pack = _capacity_pack(source_macro, shared_capacity_bytes)
    return {
        "label": label,
        "path": "historical_remote_plus_local_bypass",
        "source_primitive": source_primitive_name,
        "source_read": total_source_read,
        "total_source_read": total_source_read,
        "remote_source_read": remote_source_read,
        "local_bypass_source_read": local_bypass_source_read,
        "destination_write": destination_write,
        "total_source_read_bytes": total_source_bytes,
        "remote_source_read_bytes": remote_payload_bytes,
        "local_bypass_source_read_bytes": local_bypass_bytes,
        "destination_write_bytes": remote_payload_bytes,
        "source_shared_capacity_pack": source_capacity_pack,
        "destination_capacity_pack": None,
        "destination_area_note": (
            "The destination is the existing local kv_tile_read_buffer; no second 68 MiB "
            "capacity pack or ranked destination area is added."
        ),
        "total_layer_energy_pj": total_layer_energy_pj,
        "total_layer_energy_nj": total_layer_energy_pj / 1000.0,
        "total_layer_energy_per_total_source_byte_pj": total_layer_energy_pj / total_source_bytes,
        "remote_only_energy_pj": remote_only_energy_pj,
        "remote_only_energy_nj": remote_only_energy_pj / 1000.0,
        "remote_only_energy_per_useful_byte_pj": remote_only_energy_pj / remote_payload_bytes,
        "remote_only_diagnostic_note": (
            "Remote-only energy excludes local-bypass source reads and is not the ranking metric."
        ),
        "total_sram_energy_pj": total_layer_energy_pj,
        "total_sram_energy_nj": total_layer_energy_pj / 1000.0,
        "total_energy_per_useful_byte_pj": total_layer_energy_pj / total_source_bytes,
        "source_capacity_area_um2": source_capacity_pack["area_um2"],
        "source_capacity_area_mm2": source_capacity_pack["area_mm2"],
        "endpoint_access_time_bound_ns": max(
            total_source_read["access_time_ns"], destination_write["access_time_ns"]
        ),
    }


def _rank_composed(profiles: dict[str, JsonDict]) -> list[JsonDict]:
    ordered = sorted(
        profiles.items(),
        key=lambda item: (
            item[1]["total_layer_energy_pj"],
            item[1]["source_capacity_area_mm2"],
            item[1]["endpoint_access_time_bound_ns"],
        ),
    )
    return [
        {
            "rank": rank,
            "profile": name,
            "total_layer_energy_pj": profile["total_layer_energy_pj"],
            "total_layer_energy_nj": profile["total_layer_energy_nj"],
            "total_layer_energy_per_total_source_byte_pj": profile[
                "total_layer_energy_per_total_source_byte_pj"
            ],
            "remote_only_energy_per_useful_byte_pj": profile[
                "remote_only_energy_per_useful_byte_pj"
            ],
            "total_energy_per_useful_byte_pj": profile["total_energy_per_useful_byte_pj"],
            "total_sram_energy_pj": profile["total_sram_energy_pj"],
            "source_capacity_area_mm2": profile["source_capacity_area_mm2"],
            "endpoint_access_time_bound_ns": profile["endpoint_access_time_bound_ns"],
        }
        for rank, (name, profile) in enumerate(ordered, start=1)
    ]


def build_audit_report(
    *,
    mode: str = FRACTIONAL_SMEAR,
    fractional_tile_bytes: int = DEFAULT_FRACTIONAL_TILE_BYTES,
    persistence_mode: str = TRANSIENT,
    scope: str = "one_layer_remote",
    sequence_length: int = DEFAULT_SEQUENCE_LENGTH,
    tile_tokens: int = DEFAULT_TILE_TOKENS,
    layers: int = DEFAULT_LAYERS,
    kv_heads: int = DEFAULT_KV_HEADS,
    head_dim: int = DEFAULT_HEAD_DIM,
    kv_bits: int = DEFAULT_KV_BITS,
    clusters: int = DEFAULT_CLUSTERS,
    packet_payload: int = DEFAULT_PACKET_PAYLOAD,
    shared_capacity_bytes: int = DEFAULT_SHARED_CAPACITY_BYTES,
    local_capacity_path: Path = LOCAL_CAPACITY_METRICS,
    tile_buffer_path: Path = TILE_BUFFER_METRICS,
) -> JsonDict:
    """Return exact source-read/destination-write accounting for three options."""

    if scope not in {"one_layer_remote", "full_model"}:
        raise SramAuditError("scope must be 'one_layer_remote' or 'full_model'")
    if mode == FRACTIONAL_SMEAR and fractional_tile_bytes <= 0:
        raise SramAuditError("fractional_tile_bytes must be positive")
    selected, native = load_selected_macros(
        local_capacity_path=local_capacity_path,
        tile_buffer_path=tile_buffer_path,
    )
    remote_traffic = _residency_traffic(
        mode=mode,
        fractional_tile_bytes=fractional_tile_bytes,
        persistence_mode=persistence_mode,
        scope=scope,
        shared_capacity_bytes=shared_capacity_bytes,
        placement="remote",
        sequence_length=sequence_length,
        tile_tokens=tile_tokens,
        layers=layers,
        kv_heads=kv_heads,
        head_dim=head_dim,
        kv_bits=kv_bits,
        clusters=clusters,
        packet_payload=packet_payload,
    )
    historical_local_bypass_traffic = _residency_traffic(
        mode=mode,
        fractional_tile_bytes=fractional_tile_bytes,
        persistence_mode=persistence_mode,
        scope=scope,
        shared_capacity_bytes=shared_capacity_bytes,
        placement="local",
        sequence_length=sequence_length,
        tile_tokens=tile_tokens,
        layers=layers,
        kv_heads=kv_heads,
        head_dim=head_dim,
        kv_bits=kv_bits,
        clusters=clusters,
        packet_payload=packet_payload,
    )
    total_source_traffic = _combine_historical_source_traffic(
        remote_traffic,
        historical_local_bypass_traffic,
    )
    locality_traffic = _residency_traffic(
        mode=LOCALITY_AWARE,
        fractional_tile_bytes=fractional_tile_bytes,
        persistence_mode=persistence_mode,
        scope=scope,
        shared_capacity_bytes=shared_capacity_bytes,
        placement="local",
        sequence_length=sequence_length,
        tile_tokens=tile_tokens,
        layers=layers,
        kv_heads=kv_heads,
        head_dim=head_dim,
        kv_bits=kv_bits,
        clusters=clusters,
        packet_payload=packet_payload,
    )
    remote_primitives = _primitive_profiles(remote_traffic, selected=selected, native=native)
    historical_local_bypass_primitives = _primitive_profiles(
        historical_local_bypass_traffic,
        selected=selected,
        native=native,
    )
    total_source_primitives = _primitive_profiles(
        total_source_traffic,
        selected=selected,
        native=native,
    )
    locality_primitives = _primitive_profiles(locality_traffic, selected=selected, native=native)
    destination_primitive = remote_primitives["native_256b_macro"]
    remote_composed = {
        "shared1024_burst4_source_local256_destination": _compose_historical_remote_profile(
            label="shared 1024-bit burst4 source + local 256-bit destination",
            source_primitive_name="selected_1024b_macro_burst4",
            total_source_primitive=total_source_primitives["selected_1024b_macro_burst4"],
            remote_source_primitive=remote_primitives["selected_1024b_macro_burst4"],
            local_bypass_primitive=historical_local_bypass_primitives[
                "selected_1024b_macro_burst4"
            ],
            source_macro=selected,
            destination_primitive=destination_primitive,
            destination_macro=native,
            total_source_bytes=int(total_source_traffic["payload_bytes"]),
            remote_payload_bytes=int(remote_traffic["payload_bytes"]),
            local_bypass_bytes=int(historical_local_bypass_traffic["payload_bytes"]),
            shared_capacity_bytes=shared_capacity_bytes,
        ),
        "shared1024_naive_source_local256_destination": _compose_historical_remote_profile(
            label="shared 1024-bit naive source + local 256-bit destination",
            source_primitive_name="selected_1024b_macro_naive_flit",
            total_source_primitive=total_source_primitives["selected_1024b_macro_naive_flit"],
            remote_source_primitive=remote_primitives["selected_1024b_macro_naive_flit"],
            local_bypass_primitive=historical_local_bypass_primitives[
                "selected_1024b_macro_naive_flit"
            ],
            source_macro=selected,
            destination_primitive=destination_primitive,
            destination_macro=native,
            total_source_bytes=int(total_source_traffic["payload_bytes"]),
            remote_payload_bytes=int(remote_traffic["payload_bytes"]),
            local_bypass_bytes=int(historical_local_bypass_traffic["payload_bytes"]),
            shared_capacity_bytes=shared_capacity_bytes,
        ),
        "native256_shared_source_local256_destination": _compose_historical_remote_profile(
            label="native 256-bit shared source + local 256-bit destination",
            source_primitive_name="native_256b_macro",
            total_source_primitive=total_source_primitives["native_256b_macro"],
            remote_source_primitive=remote_primitives["native_256b_macro"],
            local_bypass_primitive=historical_local_bypass_primitives["native_256b_macro"],
            source_macro=native,
            destination_primitive=destination_primitive,
            destination_macro=native,
            total_source_bytes=int(total_source_traffic["payload_bytes"]),
            remote_payload_bytes=int(remote_traffic["payload_bytes"]),
            local_bypass_bytes=int(historical_local_bypass_traffic["payload_bytes"]),
            shared_capacity_bytes=shared_capacity_bytes,
        ),
    }
    locality_composed = {
        "shared1024_burst4_local_read": _compose_profile(
            label="locality-aware shared 1024-bit burst4 read",
            source_primitive_name="selected_1024b_macro_burst4",
            source_primitive=locality_primitives["selected_1024b_macro_burst4"],
            source_macro=selected,
            payload_bytes=int(locality_traffic["payload_bytes"]),
            shared_capacity_bytes=shared_capacity_bytes,
            destination_primitive=None,
            destination_macro=None,
            locality_aware=True,
        ),
        "shared1024_naive_local_read": _compose_profile(
            label="locality-aware shared 1024-bit naive read",
            source_primitive_name="selected_1024b_macro_naive_flit",
            source_primitive=locality_primitives["selected_1024b_macro_naive_flit"],
            source_macro=selected,
            payload_bytes=int(locality_traffic["payload_bytes"]),
            shared_capacity_bytes=shared_capacity_bytes,
            destination_primitive=None,
            destination_macro=None,
            locality_aware=True,
        ),
        "native256_shared_local_read": _compose_profile(
            label="locality-aware native 256-bit shared read",
            source_primitive_name="native_256b_macro",
            source_primitive=locality_primitives["native_256b_macro"],
            source_macro=native,
            payload_bytes=int(locality_traffic["payload_bytes"]),
            shared_capacity_bytes=shared_capacity_bytes,
            destination_primitive=None,
            destination_macro=None,
            locality_aware=True,
        ),
    }
    remote_ranking = _rank_composed(remote_composed)
    locality_ranking = _rank_composed(locality_composed)
    return {
        "model": "llama7b_shared_sram_access_energy_audit_v3",
        "shape": total_source_traffic["shape"],
        "configuration": {
            "shape": total_source_traffic["shape"],
            "clusters": total_source_traffic["clusters"],
            "packet_payload_bytes": total_source_traffic["packet_payload_bytes"],
            "shared_capacity_bytes": total_source_traffic["shared_capacity_bytes"],
            "persistence_mode": persistence_mode,
        },
        "traffic": remote_traffic,
        "historical_local_bypass_traffic": historical_local_bypass_traffic,
        "total_source_traffic": total_source_traffic,
        "locality_aware_traffic": locality_traffic,
        "cacti": {
            "selected_1024b_macro": selected.as_dict(),
            "native_256b_macro": native.as_dict(),
        },
        "profiles": total_source_primitives,
        "profiles_note": (
            "Diagnostic historical total-source symmetric primitives only; they are not ranked."
        ),
        "remote_only_primitives": remote_primitives,
        "historical_local_bypass_primitives": historical_local_bypass_primitives,
        "locality_aware_primitives": locality_primitives,
        "composed_profiles": remote_composed,
        "locality_aware_composed_profiles": locality_composed,
        "ranking": {
            "basis": "total layer energy of composed source-read and destination-write paths",
            "remote": remote_ranking,
            "locality_aware": locality_ranking,
        },
        "summary": {
            "best_remote_profile": remote_ranking[0]["profile"],
            "best_locality_aware_profile": locality_ranking[0]["profile"],
            "ranking_metric": "total_layer_energy_pj",
            "remote_destination_macro": native.name,
            "remote_destination_write_accesses": remote_traffic["flit_count"],
            "historical_total_source_read_bytes": total_source_traffic["payload_bytes"],
            "historical_remote_source_read_bytes": remote_traffic["payload_bytes"],
            "historical_local_bypass_source_read_bytes": historical_local_bypass_traffic[
                "payload_bytes"
            ],
            "historical_burst4_total_source_read_accesses": remote_composed[
                "shared1024_burst4_source_local256_destination"
            ]["source_read"]["access_count"],
            "locality_aware_destination_write_accesses": 0,
            "ranked_area_scope": "source shared-storage capacity pack only",
        },
        "method": {
            "source_read": (
                "historical remote-policy paths charge source reads for remote and local-bypass "
                "resident contexts; locality-aware paths charge all-local source reads"
            ),
            "destination_write": (
                "remote paths charge one kv_tile_read_buffer CACTI write per 256-bit flit; "
                "locality-aware paths charge zero destination writes"
            ),
            "useful_bytes": "residency payload bytes, excluding flit and macro-word padding",
            "ranking_energy": (
                "Remote-policy ranking uses total layer energy: total source reads plus remote-only "
                "destination writes. Remote-only pJ/useful-byte is retained as a diagnostic."
            ),
            "padding": "flit padding and macro-word padding are reported independently",
            "dimensional_guard": (
                "Energy is access_count * per_macro_access_energy. It is never divided by "
                "aggregate capacity; energy_per_useful_byte divides only by useful payload."
            ),
            "area_boundary": (
                "Only the source shared-storage capacity pack is ranked. The existing local "
                "destination buffer is not expanded into a second 68 MiB pack."
            ),
            "hbm_boundary": "HBM is external and is not modeled by this audit",
        },
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope", choices=("one_layer_remote", "full_model"), default="one_layer_remote")
    parser.add_argument("--mode", default=FRACTIONAL_SMEAR)
    parser.add_argument("--fractional-tile-bytes", type=int, default=DEFAULT_FRACTIONAL_TILE_BYTES)
    parser.add_argument("--persistence-mode", choices=(TRANSIENT, PERSISTENT), default=TRANSIENT)
    parser.add_argument("--sequence-length", type=int, default=DEFAULT_SEQUENCE_LENGTH)
    parser.add_argument("--tile-tokens", type=int, default=DEFAULT_TILE_TOKENS)
    parser.add_argument("--layers", type=int, default=DEFAULT_LAYERS)
    parser.add_argument("--kv-heads", type=int, default=DEFAULT_KV_HEADS)
    parser.add_argument("--head-dim", type=int, default=DEFAULT_HEAD_DIM)
    parser.add_argument("--kv-bits", type=int, default=DEFAULT_KV_BITS)
    parser.add_argument("--clusters", type=int, default=DEFAULT_CLUSTERS)
    parser.add_argument("--packet-payload", type=int, default=DEFAULT_PACKET_PAYLOAD)
    parser.add_argument("--shared-capacity-bytes", type=int, default=DEFAULT_SHARED_CAPACITY_BYTES)
    parser.add_argument("--pretty", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    report = build_audit_report(
        mode=args.mode,
        fractional_tile_bytes=args.fractional_tile_bytes,
        persistence_mode=args.persistence_mode,
        scope=args.scope,
        sequence_length=args.sequence_length,
        tile_tokens=args.tile_tokens,
        layers=args.layers,
        kv_heads=args.kv_heads,
        head_dim=args.head_dim,
        kv_bits=args.kv_bits,
        clusters=args.clusters,
        packet_payload=args.packet_payload,
        shared_capacity_bytes=args.shared_capacity_bytes,
    )
    print(json.dumps(report, indent=2 if args.pretty else None, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
