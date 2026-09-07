"""Canonical tensor reference for concurrent local producers and temporal waves."""
from npu.eval.canonical_attention_producer_inputs import CanonicalProducerInputs
from npu.sim.perf.canonical_attention_fixture import CanonicalAttentionFixture, bounded
from npu.sim.perf.attention_exact_partial import (
    compose_local_temporal_cluster_exact, merge_partial_streams, partial_stream_from_blocks,
)
from npu.eval.probe_attention_score32_exact_partial_gqa8_dual_stream_producer import _raw_scores, requantize_score_row


def producer_partial(inputs, command):
    group = int(command["group_index"])
    count = inputs.counts()[group]
    blocks = [inputs.block_beats(s, group, block_count_per_stream=count, head_dim=128) for s in range(2)]
    values = [inputs.values_for(s, group, block_count_per_stream=count) for s in range(2)]
    result = []
    for head in range(8):
        streams = [partial_stream_from_blocks(command_id=int(command["command_id"]),
            head_id=int(command["head_base"])+head,
            score_rows=[list(requantize_score_row(_raw_scores(block, head),
                multiplier=int(command["multiplier"]), shift=int(command["shift"]))) for block in blocks[s]],
            value_blocks=values[s]) for s in range(2)]
        result.extend(merge_partial_streams(*streams))
    return tuple(result)


def canonical_cluster_rows(*, cluster, logical_head_groups=4, fixture=None):
    from npu.eval import probe_attention_score32_exact_local16_global_tree_cluster_sram_gqa8 as probe
    bounded(cluster, 16, "cluster")
    fixture = fixture or CanonicalAttentionFixture()
    if fixture.layer != 0:
        raise ValueError("canonical cluster reference requires layer zero destination mapping")
    if logical_head_groups not in (1, 2, 3, 4):
        raise ValueError("invalid head group count")
    producers = probe.CLUSTER_PRODUCERS[cluster]
    rows = []
    for command in probe._logical_commands(logical_head_groups=logical_head_groups):
        waves = []
        for wave in range(8):
            waves.append(tuple(producer_partial(CanonicalProducerInputs(producers=producers,
                producer=p, tile=cluster+16*wave, fixture=fixture), command) for p in range(producers)))
        composition = compose_local_temporal_cluster_exact(waves)
        rows.extend({"cluster": cluster, "command_id": beat.command_id,
            "head_id": beat.head_id, "slice": beat.slice_index, "last": beat.last,
            "global_max": beat.max_score, "exp_sum": beat.exp_sum,
            "value": list(beat.numerators)} for beat in composition.temporal_aggregate)
    return rows
