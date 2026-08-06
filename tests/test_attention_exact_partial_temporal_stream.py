from pathlib import Path
import sys

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.sim.perf.attention_exact_partial import (
    ExactPartialBeat,
    ExactPartialWindowRecord,
    VALUE_SLICES,
    merge_ordered_exact_partial_temporal_stream,
    merge_partial_beats,
)


def _beats(*, command_id: int, head_id: int, window_index: int) -> tuple[ExactPartialBeat, ...]:
    return tuple(
        ExactPartialBeat(
            command_id=command_id,
            head_id=head_id,
            slice_index=slice_index,
            last=slice_index == VALUE_SLICES - 1,
            max_score=100 + (window_index * 7) + head_id,
            exp_sum=17 + window_index + slice_index,
            numerators=tuple(
                (window_index + 1) * 100 + (slice_index * 11) + lane for lane in range(8)
            ),
        )
        for slice_index in range(VALUE_SLICES)
    )


def _record(
    *,
    sequence_id: int = 3,
    command_id: int = 0x4A21,
    head_id: int = 5,
    window_index: int,
    window_count: int,
    beats: tuple[ExactPartialBeat, ...] | None = None,
) -> ExactPartialWindowRecord:
    return ExactPartialWindowRecord(
        sequence_id=sequence_id,
        head_id=head_id,
        window_index=window_index,
        window_count=window_count,
        beats=beats
        if beats is not None
        else _beats(command_id=command_id, head_id=head_id, window_index=window_index),
    )


def _fold_expected(records: tuple[ExactPartialWindowRecord, ...]) -> tuple[ExactPartialBeat, ...]:
    aggregate = records[0].beats
    for record in records[1:]:
        aggregate = tuple(
            merge_partial_beats(aggregate[index], record.beats[index])
            for index in range(VALUE_SLICES)
        )
    return aggregate


def test_ordered_temporal_stream_merges_interleaved_sequence_heads() -> None:
    head5 = (
        _record(sequence_id=3, head_id=5, window_index=0, window_count=3),
        _record(sequence_id=3, head_id=5, window_index=1, window_count=3),
        _record(sequence_id=3, head_id=5, window_index=2, window_count=3),
    )
    head6 = (
        _record(sequence_id=3, command_id=0x4A22, head_id=6, window_index=0, window_count=2),
        _record(sequence_id=3, command_id=0x4A22, head_id=6, window_index=1, window_count=2),
    )

    results = merge_ordered_exact_partial_temporal_stream(
        (head5[0], head6[0], head5[1], head6[1], head5[2])
    )

    assert [(result.sequence_id, result.head_id, result.window_count) for result in results] == [
        (3, 5, 3),
        (3, 6, 2),
    ]
    assert len(results[0].beats) == VALUE_SLICES
    assert results[0].beats == _fold_expected(head5)
    assert results[1].beats == _fold_expected(head6)


def test_ordered_temporal_stream_preserves_single_window_stream() -> None:
    record = _record(sequence_id=9, head_id=2, window_index=0, window_count=1)

    results = merge_ordered_exact_partial_temporal_stream((record,))

    assert len(results) == 1
    assert results[0].sequence_id == 9
    assert results[0].head_id == 2
    assert results[0].window_count == 1
    assert results[0].beats == record.beats


def test_window_record_accepts_max_window_count_metadata() -> None:
    record = _record(window_index=0, window_count=16384)

    assert record.window_count == 16384


@pytest.mark.parametrize("window_count", [0, 16385])
def test_window_record_rejects_invalid_window_count(window_count: int) -> None:
    with pytest.raises(ValueError, match="window_count must be in"):
        _record(window_index=0, window_count=window_count)


def test_window_record_rejects_head_metadata_mismatch() -> None:
    beats = _beats(command_id=0x4A21, head_id=6, window_index=0)

    with pytest.raises(ValueError, match="head_id mismatch"):
        _record(head_id=5, window_index=0, window_count=1, beats=beats)


def test_window_record_rejects_slice_order_mismatch() -> None:
    beats = list(_beats(command_id=0x4A21, head_id=5, window_index=0))
    beats[0] = ExactPartialBeat(
        command_id=0x4A21,
        head_id=5,
        slice_index=1,
        last=False,
        max_score=101,
        exp_sum=17,
        numerators=tuple(range(8)),
    )

    with pytest.raises(ValueError, match="slice sequencing mismatch"):
        _record(window_index=0, window_count=1, beats=tuple(beats))


def test_temporal_stream_rejects_non_monotonic_window_order() -> None:
    records = (
        _record(window_index=0, window_count=3),
        _record(window_index=2, window_count=3),
    )

    with pytest.raises(ValueError, match="expected window_index 1, got 2"):
        merge_ordered_exact_partial_temporal_stream(records)


def test_temporal_stream_rejects_window_count_mismatch() -> None:
    records = (
        _record(window_index=0, window_count=2),
        _record(window_index=1, window_count=3),
    )

    with pytest.raises(ValueError, match="window_count mismatch"):
        merge_ordered_exact_partial_temporal_stream(records)


def test_temporal_stream_rejects_incomplete_window_group() -> None:
    with pytest.raises(ValueError, match="expected 2 windows, received 1"):
        merge_ordered_exact_partial_temporal_stream((_record(window_index=0, window_count=2),))


def test_temporal_stream_rejects_command_id_mismatch_across_windows() -> None:
    records = (
        _record(command_id=0x4A21, window_index=0, window_count=2),
        _record(command_id=0x4A22, window_index=1, window_count=2),
    )

    with pytest.raises(ValueError, match="command_id mismatch"):
        merge_ordered_exact_partial_temporal_stream(records)


def test_temporal_stream_rejects_empty_input() -> None:
    with pytest.raises(ValueError, match="expected at least one exact partial window record"):
        merge_ordered_exact_partial_temporal_stream(())
