"""Canonical inputs for a numerical producer probe, not live ingress evidence."""
from dataclasses import dataclass

from npu.sim.perf.canonical_attention_fixture import CanonicalAttentionFixture, bounded
from npu.sim.perf.attention_score32_exact_cluster_sram_service_gqa8 import (
    exact_local_cluster_gqa8_command_block_counts,
)


@dataclass(frozen=True)
class CanonicalProducerInputs:
    producers: int
    producer: int
    tile: int = 2
    fixture: CanonicalAttentionFixture = CanonicalAttentionFixture(layer=7)

    def __post_init__(self):
        if self.producers not in (53, 54):
            raise ValueError("invalid producer family")
        bounded(self.producer, self.producers, "producer")
        bounded(self.tile, 128, "tile")

    def counts(self):
        return tuple(exact_local_cluster_gqa8_command_block_counts(
            producers=self.producers, group_index=g)[self.producer] for g in range(4))

    def validate_workload(self, workload):
        if (workload["head_dim"] != 128 or workload["command_count"] != 4
                or tuple(workload["head_bases"]) != (0, 8, 16, 24)
                or tuple(workload["block_counts_per_stream"]) != self.counts()):
            raise ValueError("canonical producer probe requires four full-dimension groups and mapped block counts")

    def identity(self):
        return {"kind": "canonical_tensor_direct_producer", "producers": self.producers,
                "producer": self.producer, "tile": self.tile, "layer": self.fixture.layer,
                "seed": self.fixture.seed, "decode_token": self.fixture.decode_token,
                "live_ingress": False, "model_quality": False}

    def block_beats(self, stream, command_index, *, block_count_per_stream, head_dim):
        bounded(stream, 2, "stream")
        bounded(command_index, 4, "group")
        if head_dim != 128 or block_count_per_stream != self.counts()[command_index]:
            raise ValueError("canonical K/Q geometry mismatch")
        beats = list(self.fixture.producer_stream(producers=self.producers,
            producer=self.producer, group=command_index, tile=self.tile))
        return [[(list(q[stream * 8:stream * 8 + 8]), list(k[stream * 8:stream * 8 + 8]))
                 for q, k, last in beats[b * 128:(b + 1) * 128]]
                for b in range(block_count_per_stream)]

    def values_for(self, stream, command_index, *, block_count_per_stream):
        bounded(stream, 2, "stream")
        bounded(command_index, 4, "group")
        if block_count_per_stream != self.counts()[command_index]:
            raise ValueError("canonical V geometry mismatch")
        return [[self.fixture.producer_value_slice(producers=self.producers,
            producer=self.producer, group=command_index, tile=self.tile, block=b,
            stream=stream, value_slice=s) for s in range(16)]
            for b in range(block_count_per_stream)]
