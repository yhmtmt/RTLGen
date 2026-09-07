import pytest

from npu.eval.canonical_attention_cluster_reference import producer_partial, canonical_cluster_rows
from npu.eval.canonical_attention_producer_inputs import CanonicalProducerInputs
from npu.eval.probe_attention_score32_exact_partial_gqa8_dual_stream_producer import _expected, _command_schedule


@pytest.mark.parametrize("producers", [53, 54])
def test_canonical_partial_matches_verified_direct_reference(producers):
    inputs = CanonicalProducerInputs(producers=producers, producer=64-producers)
    workload = dict(heads=32, command_count=4, head_dim=128,
                    head_bases=(0,8,16,24), block_counts_per_stream=inputs.counts())
    rows=[]
    for group, command in enumerate(_command_schedule(heads=32, command_count=4, head_bases=(0,8,16,24))):
        for beat in producer_partial(inputs, {**command, "group_index": group}):
            rows.append(dict(command_id=beat.command_id, head_id=beat.head_id,
                slice=beat.slice_index, last=beat.last, global_max=beat.max_score,
                exp_sum=beat.exp_sum, value=list(beat.numerators)))
    assert rows == _expected(workload, inputs)


@pytest.mark.parametrize("cluster", [0,8])
def test_canonical_full_producer_one_group_reference(cluster):
    rows = canonical_cluster_rows(cluster=cluster, logical_head_groups=1)
    assert len(rows)==128
    assert {(r["head_id"],r["slice"]) for r in rows} == {(h,s) for h in range(8) for s in range(16)}
    assert all(r["cluster"]==cluster and r["exp_sum"]>0 for r in rows)
