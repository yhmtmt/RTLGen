from npu.sim.perf.attention_exact_partial import (
    EXACT_STATE_BYTES_PER_CLUSTER_32_HEADS,
    FINAL_LINK_BITS,
    FINAL_PAYLOAD_BITS,
    ExactFinalizedBeat,
    ExactLocalGlobalGqa8Composition,
    ExactLocalTemporalClusterComposition,
    ExactPartialBeat,
    LEAF_STREAM_BYTES_PER_CLUSTER_32_HEADS,
    LOCAL_TEMPORAL_WAVES,
    PARTIAL_PAYLOAD_BITS,
    compose_local16_global_tree_gqa8_exact,
    compose_local_temporal_cluster_exact,
    exact_finalized_tree_service_manifest,
    exact_local16_global_tree_gqa8_service_manifest,
    exact_local_temporal_reducer_service_manifest,
    exact_partial_staged_tree_service_manifest,
    exact_partial_tree_service_manifest,
    finalize_partial_beat,
    finalize_partial_beats,
    finalize_partial_stream,
    finalizer_accept_interval_cycles,
    finalizer_cycles_per_beat,
    finalizer_output_latency_cycles,
    merge_balanced_partial_streams,
    merge_partial_beats,
    merge_partial_streams,
    merge_partial_streams_via_local_normalization,
    merge_staged_partial_streams,
    normalized_merge_guard_case,
    pack_final_values,
    pack_numerators,
    partial_stream_from_blocks,
    reduce_local_temporal_partial_waves,
    simulate_exact_finalizer,
    unpack_final_values,
    unpack_numerators,
)

INT_MAX = (1 << 31) - 1
INT_MIN = -(1 << 31)


def _score_rows(seed: int) -> tuple[tuple[int, ...], ...]:
    return tuple(
        tuple(((seed * 19 + block * 23 + lane * 7) % 255) - 127 for lane in range(8))
        for block in range(3)
    )


def _value_blocks(seed: int) -> tuple[tuple[tuple[tuple[int, ...], ...], ...], ...]:
    return tuple(
        tuple(
            tuple(
                tuple((((seed * 29) + block * 17 + value_slice * 13 + row * 11 + lane * 5) % 255) - 127 for lane in range(8))
                for row in range(8)
            )
            for value_slice in range(16)
        )
        for block in range(3)
    )


def _beat(*, max_score: int, exp_sum: int = 19, numerators: tuple[int, ...] = (101, -55, 77, -33, 12, -9, 5, -3)) -> ExactPartialBeat:
    return ExactPartialBeat(
        command_id=0x4A21,
        head_id=3,
        slice_index=0,
        last=False,
        max_score=max_score,
        exp_sum=exp_sum,
        numerators=numerators,
    )


def _cluster_beat(*, cluster: int, producer: int, wave: int) -> ExactPartialBeat:
    value_base = 10 + (cluster * 17) + (producer * 13) + (wave * 19)
    return ExactPartialBeat(
        command_id=0x5200,
        head_id=7,
        slice_index=15,
        last=True,
        max_score=((cluster * 29) + (producer * 11) + (wave * 7)) - 200,
        exp_sum=200 + cluster + producer + wave,
        numerators=tuple(value_base + lane for lane in range(8)),
    )


def test_pack_unpack_partial_numerators_round_trip() -> None:
    lanes = (-321, 511, -1024, 777, -13, 0, 9999, -8888)
    packed = pack_numerators(lanes)

    assert PARTIAL_PAYLOAD_BITS == 328
    assert unpack_numerators(packed) == lanes


def test_pack_unpack_final_values_round_trip() -> None:
    lanes = (-321, 511, -1024, 777, -13, 0, 9999, -8888)
    packed = pack_final_values(lanes)

    assert FINAL_PAYLOAD_BITS == 320
    assert FINAL_LINK_BITS == 346
    assert unpack_final_values(packed) == lanes


def test_partial_stream_merge_matches_attention_online_semantics() -> None:
    left = partial_stream_from_blocks(
        command_id=0x4A21,
        head_id=3,
        score_rows=_score_rows(5),
        value_blocks=_value_blocks(7),
    )
    right = partial_stream_from_blocks(
        command_id=0x4A21,
        head_id=3,
        score_rows=_score_rows(11),
        value_blocks=_value_blocks(13),
    )

    merged_stream = merge_partial_streams(left, right)

    assert len(merged_stream) == 16
    assert [beat.slice_index for beat in merged_stream] == list(range(16))
    assert all(beat.command_id == 0x4A21 for beat in merged_stream)
    assert all(beat.head_id == 3 for beat in merged_stream)
    assert all(beat.exp_sum > 0 for beat in merged_stream)

    first = merge_partial_beats(left[0], right[0])
    assert merged_stream[0] == first


def test_partial_stream_merge_survives_finalization() -> None:
    left, right = normalized_merge_guard_case()
    merged = merge_partial_streams(left, right)

    finalized = finalize_partial_stream(merged)

    assert len(finalized) == 16
    assert all(len(value_slice) == 8 for value_slice in finalized)


def test_finalize_partial_beat_matches_stream_helper() -> None:
    beat = partial_stream_from_blocks(
        command_id=0x4A21,
        head_id=3,
        score_rows=_score_rows(5),
        value_blocks=_value_blocks(7),
    )[0]

    finalized = finalize_partial_beat(beat)

    assert isinstance(finalized, ExactFinalizedBeat)
    assert finalized == finalize_partial_beats((beat,))[0]
    assert finalized.command_id == beat.command_id
    assert finalized.head_id == beat.head_id
    assert finalized.slice_index == beat.slice_index
    assert finalized.last == beat.last


def test_balanced_tree_merge_matches_left_to_right_pairing() -> None:
    leaves = [
        partial_stream_from_blocks(
            command_id=0x4A21,
            head_id=3,
            score_rows=_score_rows(seed),
            value_blocks=_value_blocks(seed + 2),
        )
        for seed in (5, 11, 17, 23)
    ]

    merged = merge_balanced_partial_streams(leaves)
    expected = merge_partial_streams(
        merge_partial_streams(leaves[0], leaves[1]),
        merge_partial_streams(leaves[2], leaves[3]),
    )

    assert merged == expected


def test_staged_tree_merge_carries_odd_leaf_forward() -> None:
    leaves = [
        partial_stream_from_blocks(
            command_id=0x4A30 + index,
            head_id=3,
            score_rows=_score_rows(seed),
            value_blocks=_value_blocks(seed + 2),
        )
        for index, seed in enumerate((5, 11, 17, 23, 29))
    ]
    remapped = [
        tuple(
            ExactPartialBeat(
                command_id=0x4A21,
                head_id=3,
                slice_index=beat.slice_index,
                last=beat.last,
                max_score=beat.max_score,
                exp_sum=beat.exp_sum,
                numerators=beat.numerators,
            )
            for beat in stream
        )
        for stream in leaves
    ]

    merged = merge_staged_partial_streams(remapped)
    expected = merge_partial_streams(
        merge_partial_streams(
            merge_partial_streams(remapped[0], remapped[1]),
            merge_partial_streams(remapped[2], remapped[3]),
        ),
        remapped[4],
    )

    assert merged == expected


def test_local_temporal_reduce_merges_exactly_eight_waves() -> None:
    waves = []
    for wave in range(LOCAL_TEMPORAL_WAVES):
        streams = []
        for producer in range(3):
            streams.append(
                partial_stream_from_blocks(
                    command_id=0x4A21,
                    head_id=7,
                    score_rows=_score_rows(5 + producer + wave),
                    value_blocks=_value_blocks(9 + producer + wave),
                )
            )
        waves.append(tuple(streams))

    reduced = reduce_local_temporal_partial_waves(tuple(waves))
    expected = merge_partial_streams(
        merge_partial_streams(
            merge_partial_streams(
                merge_partial_streams(
                    merge_partial_streams(
                        merge_partial_streams(
                            merge_staged_partial_streams(waves[0]),
                            merge_staged_partial_streams(waves[1]),
                        ),
                        merge_staged_partial_streams(waves[2]),
                    ),
                    merge_staged_partial_streams(waves[3]),
                ),
                merge_staged_partial_streams(waves[4]),
            ),
            merge_staged_partial_streams(waves[5]),
        ),
        merge_partial_streams(
            merge_staged_partial_streams(waves[6]),
            merge_staged_partial_streams(waves[7]),
        ),
    )

    assert reduced == expected


def test_local_temporal_cluster_composition_tracks_wave_roots_and_temporal_aggregate() -> None:
    waves = tuple(
        tuple(
            tuple(_cluster_beat(cluster=3, producer=producer, wave=wave) for _ in range(1))
            for producer in range(2)
        )
        for wave in range(LOCAL_TEMPORAL_WAVES)
    )

    composition = compose_local_temporal_cluster_exact(waves)

    assert isinstance(composition, ExactLocalTemporalClusterComposition)
    assert len(composition.wave_local_roots) == LOCAL_TEMPORAL_WAVES
    assert all(len(root) == 1 for root in composition.wave_local_roots)
    assert composition.wave_local_roots[0] == merge_staged_partial_streams(waves[0])
    assert composition.temporal_aggregate == reduce_local_temporal_partial_waves(waves)


def test_local16_global_gqa8_composition_matches_cluster_then_global_reference() -> None:
    clusters = tuple(
        tuple(
            tuple(tuple(_cluster_beat(cluster=cluster, producer=producer, wave=wave) for _ in range(1)) for producer in range(2))
            for wave in range(LOCAL_TEMPORAL_WAVES)
        )
        for cluster in range(16)
    )

    composition = compose_local16_global_tree_gqa8_exact(clusters)

    assert isinstance(composition, ExactLocalGlobalGqa8Composition)
    assert len(composition.cluster_compositions) == 16
    expected_cluster_aggregates = tuple(
        reduce_local_temporal_partial_waves(cluster) for cluster in clusters
    )
    assert tuple(component.temporal_aggregate for component in composition.cluster_compositions) == expected_cluster_aggregates
    assert composition.global_merged_partials == merge_balanced_partial_streams(expected_cluster_aggregates)
    assert composition.finalized_beats == finalize_partial_beats(composition.global_merged_partials)


def test_exact_partial_tree_service_manifest_is_consistent() -> None:
    manifest = exact_partial_tree_service_manifest(clusters=16)

    assert manifest["radix"] == 2
    assert manifest["tree_stages"] == 4
    assert manifest["tree_nodes"] == 15
    assert manifest["exact_state_bytes_per_cluster"] == EXACT_STATE_BYTES_PER_CLUSTER_32_HEADS == 21252
    assert manifest["leaf_stream_bytes_per_cluster"] == LEAF_STREAM_BYTES_PER_CLUSTER_32_HEADS == 26816
    assert manifest["total_leaf_stream_bytes"] == 16 * 26816
    assert manifest["direct_328bit_links_unclosed"] is True
    assert manifest["final_divider_embodied"] is False


def test_exact_partial_staged_tree_service_manifest_is_consistent() -> None:
    manifest = exact_partial_staged_tree_service_manifest(producers=53, heads=8)

    assert manifest["producers"] == 53
    assert manifest["heads"] == 8
    assert manifest["tree_stages"] == 6
    assert manifest["tree_nodes"] == 52
    assert manifest["partial_payload_bits_per_beat"] == PARTIAL_PAYLOAD_BITS
    assert manifest["staging_contract"] == "pairwise_ready_valid_exact_merge_with_odd_leaf_carry"
    assert manifest["direct_328bit_links_unclosed"] is True


def test_exact_finalized_tree_service_manifest_is_consistent() -> None:
    manifest = exact_finalized_tree_service_manifest(clusters=16, divider_lanes=8)

    assert manifest["radix"] == 2
    assert manifest["tree_stages"] == 4
    assert manifest["tree_nodes"] == 15
    assert manifest["exact_state_bytes_per_cluster"] == EXACT_STATE_BYTES_PER_CLUSTER_32_HEADS == 21252
    assert manifest["leaf_stream_bytes_per_cluster"] == LEAF_STREAM_BYTES_PER_CLUSTER_32_HEADS == 26816
    assert manifest["final_payload_bits_per_beat"] == FINAL_PAYLOAD_BITS == 320
    assert manifest["final_link_bits_per_beat"] == FINAL_LINK_BITS == 346
    assert manifest["divider_lanes"] == 8
    assert manifest["divider_cycles_per_beat"] == 57
    assert manifest["per_bank_output_latency_cycles"] == 58
    assert manifest["per_bank_accept_interval_cycles"] == 59
    assert manifest["direct_328bit_links_unclosed"] is True
    assert manifest["final_divider_embodied"] is True


def test_exact_local_temporal_reducer_service_manifest_is_consistent() -> None:
    manifest = exact_local_temporal_reducer_service_manifest(producers=54, heads=2)

    assert manifest["producers"] == 54
    assert manifest["persistent_waves"] == 8
    assert manifest["tree_stages"] == 6
    assert manifest["tree_nodes"] == 53
    assert manifest["comparison_baseline_contract"] == "python_structured_local_temporal_exact_partial_reference"
    assert manifest["remaining_abstractions"] == [
        "producer_fan_in_wiring_open",
        "noc_sram_ppa_open",
        "global_c16_exact_reduction_open",
    ]


def test_exact_local16_global_tree_gqa8_service_manifest_is_consistent() -> None:
    manifest = exact_local16_global_tree_gqa8_service_manifest(cluster_producers=((54,) * 8) + ((53,) * 8), head_groups=2)

    assert manifest["clusters"] == 16
    assert manifest["clusters_with_54_producers"] == 8
    assert manifest["clusters_with_53_producers"] == 8
    assert manifest["total_local_producers"] == 856
    assert manifest["total_value_memory_lanes"] == 1712
    assert manifest["local_aggregate_beats_per_group"] == 128
    assert manifest["global_finalized_beats_per_group"] == 128
    assert (
        manifest["command_block_count_contract"]
        == "derived_internally_from_head_base_with_p54_ranges_0_9_10_19_20_29_30_39_"
        "and_p53_ranges_0_10_11_21_22_32_33_43"
    )
    assert manifest["comparison_baseline_contract"] == "python_structured_full_row_producer_local16_global_exact_gqa8_reference"
    assert manifest["global_tree_contract"]["divider_lanes"] == 8
    assert manifest["global_tree_contract"]["finalizer_banks"] == 59
    assert manifest["remaining_abstractions"] == [
        "external_query_key_source_open",
        "external_value_memory_system_open",
        "physical_ppa_open",
    ]


def test_normalized_merge_boundary_is_not_exact() -> None:
    left, right = normalized_merge_guard_case()

    exact = finalize_partial_stream(merge_partial_streams(left, right))
    invalid = finalize_partial_stream(merge_partial_streams_via_local_normalization(left, right))

    assert exact != invalid


def test_partial_stream_reference_rejects_invalid_last_semantics() -> None:
    try:
        ExactPartialBeat(
            command_id=0x4A21,
            head_id=3,
            slice_index=0,
            last=True,
            max_score=0,
            exp_sum=1,
            numerators=(0, 0, 0, 0, 0, 0, 0, 0),
        )
    except ValueError as exc:
        assert "last must match" in str(exc)
    else:
        raise AssertionError("expected invalid last semantics to be rejected")


def test_partial_stream_merge_handles_extreme_score_deltas_without_overflow() -> None:
    dominant = _beat(max_score=INT_MAX, exp_sum=37, numerators=(31, -29, 23, -19, 17, -13, 11, -7))
    suppressed = _beat(max_score=INT_MIN, exp_sum=41, numerators=(-101, 99, -77, 55, -33, 22, -11, 9))

    merged_lr = merge_partial_beats(dominant, suppressed)
    merged_rl = merge_partial_beats(suppressed, dominant)

    assert merged_lr.max_score == INT_MAX
    assert merged_lr.exp_sum == dominant.exp_sum
    assert merged_lr.numerators == dominant.numerators
    assert merged_rl == merged_lr


def test_partial_stream_merge_handles_near_limit_score_deltas_in_both_orderings() -> None:
    dominant = _beat(max_score=INT_MAX - 1, exp_sum=53, numerators=(17, -15, 13, -11, 9, -7, 5, -3))
    suppressed = _beat(max_score=INT_MIN + 1, exp_sum=29, numerators=(-63, 57, -51, 45, -39, 33, -27, 21))

    merged_lr = merge_partial_beats(dominant, suppressed)
    merged_rl = merge_partial_beats(suppressed, dominant)

    assert merged_lr.max_score == INT_MAX - 1
    assert merged_lr.exp_sum == dominant.exp_sum
    assert merged_lr.numerators == dominant.numerators
    assert merged_rl == merged_lr


def test_exact_finalizer_cycle_reference_scales_with_lane_count() -> None:
    stream = partial_stream_from_blocks(
        command_id=0x4A21,
        head_id=3,
        score_rows=_score_rows(5),
        value_blocks=_value_blocks(7),
    )[:2]

    lane8 = simulate_exact_finalizer(stream, divider_lanes=8)
    lane4 = simulate_exact_finalizer(stream, divider_lanes=4)
    lane1 = simulate_exact_finalizer(stream, divider_lanes=1)

    assert finalizer_cycles_per_beat(8) == 57
    assert finalizer_cycles_per_beat(4) == 114
    assert finalizer_cycles_per_beat(1) == 456
    assert finalizer_output_latency_cycles(8) == 58
    assert finalizer_output_latency_cycles(4) == 115
    assert finalizer_output_latency_cycles(1) == 457
    assert finalizer_accept_interval_cycles(8) == 59
    assert finalizer_accept_interval_cycles(4) == 116
    assert finalizer_accept_interval_cycles(1) == 458
    assert lane8["accepted_count"] == 2
    assert lane8["completed_count"] == 2
    assert lane8["first_output_cycle"] == 58
    assert lane4["first_output_cycle"] == 115
    assert lane1["first_output_cycle"] == 457
