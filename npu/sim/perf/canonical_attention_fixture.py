"""Deterministic int8 tensor identity for ingress integration, not model quality."""
from dataclasses import dataclass
import hashlib
import struct

from npu.sim.perf.attention_kv_tile_layout import decode_kv_byte_address
from npu.sim.perf.attention_score32_exact_cluster_sram_service_gqa8 import (
    exact_local_cluster_gqa8_command_block_counts,
    exact_local_cluster_gqa8_slot_bases,
)


def bounded(value, limit, label):
    if type(value) is not int or not 0 <= value < limit:
        raise ValueError(f"invalid {label}")
    return value


@dataclass(frozen=True)
class CanonicalAttentionFixture:
    seed: int = 29
    layer: int = 0
    decode_token: int = 131072

    def __post_init__(self):
        bounded(self.seed, 1 << 32, "seed")
        bounded(self.layer, 32, "layer")
        bounded(self.decode_token, 1 << 32, "decode token")

    def _sample(self, kind, token, head, dimension):
        payload = struct.pack("<6I", self.seed, self.layer, kind, token, head, dimension)
        return hashlib.sha256(payload).digest()[0] - 128

    def query(self, *, group: int, dimension: int) -> tuple[int, ...]:
        bounded(group, 4, "query group")
        bounded(dimension, 128, "dimension")
        return tuple(self._sample(0, self.decode_token, group * 8 + h, dimension) for h in range(8))

    def kv(self, *, tensor: str, head: int, token: int, dimension: int) -> int:
        if tensor not in ("k", "v"):
            raise ValueError("invalid tensor")
        bounded(head, 4, "KV head")
        bounded(token, 131072, "cache token")
        bounded(dimension, 128, "dimension")
        return self._sample(1 if tensor == "k" else 2, token, head, dimension)

    def memory_flit(self, *, tile: int, address: int) -> bytes:
        bounded(tile, 128, "tile")
        bounded(address, 1 << 20, "canonical address")
        if address % 32:
            raise ValueError("unaligned flit")
        values = []
        for byte in range(32):
            c = decode_kv_byte_address(address + byte)
            values.append(self.kv(tensor=c.tensor, head=c.kv_head,
                                  token=tile * 1024 + c.token, dimension=c.dimension) & 255)
        return bytes(values)

    def producer_stream(self, *, producers: int, producer: int, group: int, tile: int):
        """Yield (16 Q lanes, 16 K lanes, block-last), in real stage order."""
        if producers not in (53, 54):
            raise ValueError("invalid producer family")
        bounded(producer, producers, "producer")
        bounded(group, 4, "query group")
        bounded(tile, 128, "tile")
        counts = exact_local_cluster_gqa8_command_block_counts(producers=producers, group_index=group)
        bases = exact_local_cluster_gqa8_slot_bases(producers=producers, group_index=group)
        for block in range(counts[producer]):
            slot = bases[producer] + block
            for dimension in range(128):
                q = self.query(group=group, dimension=dimension)
                k = tuple(self.kv(tensor="k", head=group,
                                  token=tile * 1024 + stream * 512 + slot * 8 + lane,
                                  dimension=dimension)
                          for stream in range(2) for lane in range(8))
                yield q + q, k, dimension == 127
