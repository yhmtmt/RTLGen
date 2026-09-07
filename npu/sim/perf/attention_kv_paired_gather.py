"""Exact K-head paired-block delivery plan; not a measured RTL schedule."""
from dataclasses import dataclass


@dataclass(frozen=True)
class PairedSpan:
    canonical_offset: int
    payload_bytes: int
    resident: bool


@dataclass(frozen=True)
class AddressedKeySpan:
    canonical_address: int
    source_byte_address: int
    source_hbm: bool
    source_endpoint: int
    destination_cluster: int
    payload_bytes: int


def addressed_key_spans(*, layer: int, tile: int, head: int) -> tuple[AddressedKeySpan, ...]:
    """Resolve paired delivery against the existing 68-MiB cache layout.

    This is an integration oracle, not evidence of RTL scheduler integration.
    Each layer owns 2 MiB of whole tiles plus eight packed 16-KiB prefixes.
    HBM retains the uncompressed 128-MiB per-layer canonical layout.
    """
    for value, limit, label in ((layer, 32, "layer"), (tile, 128, "tile"),
                                (head, 4, "head")):
        if type(value) is not int or not 0 <= value < limit:
            raise ValueError(f"invalid {label}")
    prefix = 131072 if tile < 2 else 16384 if tile == 2 else 0
    destination = (3 * layer + tile) % 16
    corner = (0, 3, 12, 15)[(layer + tile + head) % 4]
    result = []
    for span in key_head_spans(resident_prefix_bytes=prefix):
        canonical = head * 131072 + span.canonical_offset
        if span.resident:
            local = (tile * 1048576 + canonical if tile < 2 else
                     2097152 + head * 16384 + span.canonical_offset)
            source = layer * 2228224 + local
        else:
            source = layer * 134217728 + tile * 1048576 + canonical
        result.append(AddressedKeySpan(canonical, source, not span.resident,
                                       destination if span.resident else corner,
                                       destination, span.payload_bytes))
    return tuple(result)


def key_head_spans(*, resident_prefix_bytes: int) -> tuple[PairedSpan, ...]:
    """Alternate matching stream blocks while retaining canonical source ownership.

    A K head has 128 KiB; stream bit 16 separates its two 64 KiB halves.
    The resident prefix is expressed in canonical bytes, not delivery order.
    """
    if type(resident_prefix_bytes) is not int or not 0 <= resident_prefix_bytes <= 131072:
        raise ValueError("resident prefix outside head")
    if resident_prefix_bytes % 1024:
        raise ValueError("resident boundary must align to a transpose block")
    return tuple(PairedSpan(stream * 65536 + slot * 1024, 1024,
                            stream * 65536 + slot * 1024 < resident_prefix_bytes)
                 for slot in range(64) for stream in range(2))


def llama7b_descriptor_cost() -> dict[str, int]:
    """Count control work for paired K spans with existing V/refill descriptors."""
    tiles, heads, layers = 128, 4, 32
    old_k = tiles * heads + heads  # one split resident/HBM tile per head
    new_k = tiles * heads * len(key_head_spans(resident_prefix_bytes=0))
    value = old_k
    refill = 10
    per_layer = new_k + value + refill
    return {
        "old_k_descriptors_per_layer": old_k,
        "paired_k_descriptors_per_layer": new_k,
        "value_descriptors_per_layer": value,
        "refill_descriptors_per_layer": refill,
        "total_descriptors_per_layer": per_layer,
        "total_descriptors_full_model": per_layer * layers,
        "minimum_layer_count_bits": per_layer.bit_length(),
        "minimum_model_count_bits": (per_layer * layers).bit_length(),
        "k_payload_bytes_per_layer": tiles * heads * 131072,
    }
