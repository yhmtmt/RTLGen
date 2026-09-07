"""Keep adversarial arithmetic evidence distinct from resident decoder queries."""
import pytest

from npu.eval.probe_attention_score32_exact_local16_global_tree_gqa8 import _stream_block_beats


def queries(**overrides):
    coordinates = dict(cluster=0, producer=0, group_index=0, wave_index=0,
                       stream=0, block_count=2, seed=29)
    coordinates.update(overrides)
    return tuple(tuple(beat[0] for beat in block) for block in _stream_block_beats(**coordinates))


@pytest.mark.parametrize("axis", ["cluster", "producer", "wave_index", "stream"])
def test_stress_queries_are_not_shared_across_token_placement(axis):
    baseline = queries()[0]
    changed = queries(**{axis: 1})[0]
    assert len(baseline) == len(changed) == 128
    assert all(len(beat) == 8 for beat in baseline)
    assert all(a != b for a, b in zip(baseline, changed))


def test_stress_queries_also_change_between_blocks():
    first, second = queries()
    assert all(a != b for a, b in zip(first, second))
