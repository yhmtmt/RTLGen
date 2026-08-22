from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.eval.model_llama7b_shared_sram_residency import (  # noqa: E402
    FRACTIONAL_SMEAR,
    LAYER_BALANCED_CONTIGUOUS,
    LOCALITY_AWARE,
    PERSISTENT,
    TRANSIENT,
    build_residency_report,
    compare_residency_policies,
)


CAPACITY = 68 * 1024 * 1024


def _payload_distribution(report: dict) -> dict[int, int]:
    return {
        int(row["payload_bytes"]): int(row["context_count"])
        for row in report["residency"]["context_payload_distribution"]
    }


def _home_loads(report: dict) -> list[int]:
    return [
        int(row["resident_load_bytes"])
        for row in report["placement"]["home_capacity"]["per_home_loads"]
    ]


def test_gqa_capacity_balances_two_full_and_one_partial_tile_per_layer() -> None:
    report = build_residency_report(
        LAYER_BALANCED_CONTIGUOUS,
        kv_heads=4,
        shared_capacity_bytes=CAPACITY,
    )

    assert report["shape"]["kv_bytes_per_token"] == 1024
    assert report["shape"]["full_tile_bytes"] == 1_048_576
    assert report["shape"]["full_kv_bytes"] == 4 * 1024**3
    assert report["residency"]["resident_bytes"] == CAPACITY
    assert report["residency"]["context_count"] == 96
    assert report["residency"]["remote_context_count"] == 96
    assert report["residency"]["local_context_count"] == 0
    assert _payload_distribution(report) == {
        1_048_576: 64,
        131_072: 32,
    }
    assert report["transport"]["packet_count"] == 278_528
    assert report["transport"]["flit_count"] == 2_228_224
    assert report["transport"]["remote_transport_bytes"] == CAPACITY
    assert report["transport"]["local_resident_bytes"] == 0
    assert report["placement"]["home_capacity"]["capacity_ok"] is True
    assert _home_loads(report) == [CAPACITY // 16] * 16
    assert report["residency"]["capacity_conservation"]["conserved"] is True
    assert report["hbm"]["full_kv_storage_bytes"] == 4 * 1024**3
    assert report["hbm"]["hbm_bytes"] == 4 * 1024**3
    assert report["hbm"]["storage_savings_bytes"] == 0
    assert report["hbm"]["persistence_mode"] == TRANSIENT
    assert report["hbm"]["gross_read_avoidance"] == CAPACITY
    assert report["hbm"]["gross_read_avoidance_bytes"] == CAPACITY
    assert report["hbm"]["refill_bytes"] == CAPACITY
    assert report["hbm"]["net_hbm_read_bytes"] == 4 * 1024**3
    assert report["hbm"]["net_read_avoidance_bytes"] == 0


def test_mha_capacity_is_same_bytes_but_only_partial_contexts_fit() -> None:
    report = build_residency_report(
        LAYER_BALANCED_CONTIGUOUS,
        kv_heads=32,
        shared_capacity_bytes=CAPACITY,
    )

    assert report["shape"]["kv_bytes_per_token"] == 8192
    assert report["shape"]["full_tile_bytes"] == 8 * 1024**2
    assert report["shape"]["full_kv_bytes"] == 32 * 1024**3
    assert report["residency"]["resident_bytes"] == CAPACITY
    assert report["residency"]["context_count"] == 32
    assert _payload_distribution(report) == {2_228_224: 32}
    assert report["residency"]["whole_token_residency"] is True
    assert report["transport"]["packet_count"] == 278_528
    assert report["transport"]["flit_count"] == 2_228_224
    assert report["transport"]["remote_transport_bytes"] == CAPACITY
    assert report["transport"]["local_resident_bytes"] == 0
    assert report["placement"]["home_capacity"]["capacity_ok"] is True
    assert _home_loads(report) == [CAPACITY // 16] * 16
    assert report["hbm"]["full_kv_storage_bytes"] == 32 * 1024**3
    assert report["hbm"]["hbm_bytes"] == 32 * 1024**3
    assert report["hbm"]["storage_savings_bytes"] == 0


def test_fractional_smear_keeps_historical_bytes_explicit_and_is_not_mha_capacity_model() -> None:
    gqa = build_residency_report(
        FRACTIONAL_SMEAR,
        kv_heads=4,
        fractional_tile_bytes=17_408,
        shared_capacity_bytes=CAPACITY,
    )
    mha = build_residency_report(
        FRACTIONAL_SMEAR,
        kv_heads=32,
        fractional_tile_bytes=17_408,
        shared_capacity_bytes=CAPACITY,
    )

    for report in (gqa, mha):
        assert report["residency"]["context_count"] == 32 * 128
        assert _payload_distribution(report) == {17_408: 32 * 128}
        assert report["residency"]["resident_bytes"] == CAPACITY
        assert report["transport"]["packet_count"] == 278_528
        assert report["transport"]["flit_count"] == 2_228_224
        assert report["transport"]["remote_transport_bytes"] == 3_584 * 17_408
        assert report["transport"]["local_resident_bytes"] == 512 * 17_408
        assert report["residency"]["whole_token_residency"] is False
        assert report["hbm"]["storage_savings_bytes"] == 0
        assert report["placement"]["home_capacity"]["capacity_ok"] is True
        assert _home_loads(report) == [CAPACITY // 16] * 16

    assert gqa["shape"]["full_kv_bytes"] == 4 * 1024**3
    assert mha["shape"]["full_kv_bytes"] == 32 * 1024**3


def test_historical_112_remote_contexts_are_one_layer_placement_policy() -> None:
    report = build_residency_report(
        FRACTIONAL_SMEAR,
        kv_heads=4,
        fractional_tile_bytes=17_408,
    )
    history = report["historical_comparison"]

    assert history["context_count"] == 128
    assert history["remote_context_count"] == 112
    assert history["local_context_count"] == 16
    assert history["remote_context_count_per_layer"] == 112
    assert history["full_model_layer_multiplier"] == 32
    assert history["full_model_remote_context_count"] == 3_584
    assert history["full_model_local_context_count"] == 512
    assert history["remote_bytes"] == 112 * 17_408
    assert history["full_model_remote_transport_bytes"] == 3_584 * 17_408
    assert history["remote_packet_count"] == 112 * 68
    assert history["remote_flit_count"] == 112 * 544
    assert report["residency"]["context_count"] == 4096
    assert report["residency"]["remote_context_count"] == 112 * 32
    assert report["residency"]["local_context_count"] == 16 * 32


def test_locality_aware_assigns_every_resident_range_to_its_owner() -> None:
    for kv_heads in (4, 32):
        report = build_residency_report(
            LOCALITY_AWARE,
            kv_heads=kv_heads,
            shared_capacity_bytes=CAPACITY,
        )
        contexts = report["placement"]["resident_contexts"]
        assert contexts
        assert report["residency"]["remote_context_count"] == 0
        assert report["residency"]["local_context_count"] == report["residency"]["context_count"]
        assert all(context["owner_cluster"] == context["home_cluster"] for context in contexts)
        assert report["residency"]["capacity_conservation"]["conserved"] is True
        assert report["placement"]["home_capacity"]["per_home_capacity_bytes"] == CAPACITY // 16
        assert report["placement"]["home_capacity"]["capacity_ok"] is True
        assert _home_loads(report) == [CAPACITY // 16] * 16


def test_whole_token_layer_rotation_removes_old_endpoint_concentration() -> None:
    gqa = build_residency_report(LOCALITY_AWARE, kv_heads=4)
    mha = build_residency_report(LOCALITY_AWARE, kv_heads=32)

    gqa_offsets = gqa["placement"]["wave_assignment"]["layer_owner_rotation_offsets"]
    mha_offsets = mha["placement"]["wave_assignment"]["layer_owner_rotation_offsets"]
    assert gqa_offsets == [(3 * layer) % 16 for layer in range(32)]
    assert mha_offsets == [layer % 16 for layer in range(32)]

    gqa_contexts = gqa["placement"]["resident_contexts"]
    assert [row["owner_cluster"] for row in gqa_contexts if row["layer"] == 0] == [0, 1, 2]
    assert [row["owner_cluster"] for row in gqa_contexts if row["layer"] == 1] == [3, 4, 5]
    assert _home_loads(gqa) == [CAPACITY // 16] * 16
    assert _home_loads(mha) == [CAPACITY // 16] * 16


def test_rotated_compute_assignment_is_one_tile_per_cluster_per_complete_wave() -> None:
    for mode in (LAYER_BALANCED_CONTIGUOUS, LOCALITY_AWARE):
        for kv_heads in (4, 32):
            report = build_residency_report(mode, kv_heads=kv_heads)
            audit = report["placement"]["wave_assignment"]
            assert audit["complete_waves_per_layer"] == 8
            assert audit["checked_wave_count"] == 32 * 8
            assert audit["one_tile_per_cluster_per_complete_wave"] is True
            for offset in audit["layer_owner_rotation_offsets"]:
                assert {(offset + tile) % 16 for tile in range(16)} == set(range(16))


def test_historical_home_reports_overload_and_locality_fails_closed() -> None:
    historical = build_residency_report(
        LAYER_BALANCED_CONTIGUOUS,
        layers=1,
        kv_heads=4,
    )
    capacity = historical["placement"]["home_capacity"]
    assert capacity["capacity_ok"] is False
    assert capacity["enforcement"] == "diagnostic"
    assert capacity["overloaded_home_count"] == 4
    assert capacity["overloaded_home_clusters"] == [0, 1, 2, 3]
    assert capacity["load_conservation"] is True

    with pytest.raises(ValueError, match="exceeds per-home capacity"):
        build_residency_report(LOCALITY_AWARE, layers=1, kv_heads=4)


def test_fractional_smear_requires_explicit_bytes() -> None:
    with pytest.raises(ValueError, match="explicit fractional_tile_bytes"):
        build_residency_report(FRACTIONAL_SMEAR)


def test_persistent_residency_avoids_reads_but_not_hbm_backing_storage() -> None:
    report = build_residency_report(
        LAYER_BALANCED_CONTIGUOUS,
        kv_heads=4,
        persistence_mode=PERSISTENT,
    )

    assert report["hbm"]["hbm_bytes"] == 4 * 1024**3
    assert report["hbm"]["storage_savings_bytes"] == 0
    assert report["hbm"]["gross_read_avoidance_bytes"] == CAPACITY
    assert report["hbm"]["refill_bytes"] == 0
    assert report["hbm"]["net_hbm_read_bytes"] == 4 * 1024**3 - CAPACITY
    assert report["hbm"]["net_read_avoidance_bytes"] == CAPACITY


def test_impossible_capacity_and_shape_fail_closed() -> None:
    with pytest.raises(ValueError, match="one whole token"):
        build_residency_report(
            LAYER_BALANCED_CONTIGUOUS,
            layers=2,
            kv_heads=32,
            shared_capacity_bytes=8192,
        )
    with pytest.raises(ValueError, match="byte-aligned"):
        build_residency_report(LAYER_BALANCED_CONTIGUOUS, kv_bits=4)
    with pytest.raises(ValueError, match="multiple of 32"):
        build_residency_report(LAYER_BALANCED_CONTIGUOUS, packet_payload=33)
    with pytest.raises(ValueError, match="divide evenly"):
        build_residency_report(
            LAYER_BALANCED_CONTIGUOUS,
            shared_capacity_bytes=CAPACITY + 1,
        )
    with pytest.raises(ValueError, match="exceeds tile"):
        build_residency_report(
            FRACTIONAL_SMEAR,
            kv_heads=4,
            sequence_length=1024,
            tile_tokens=1024,
            fractional_tile_bytes=2_000_000,
        )


def test_compare_returns_all_three_explicit_policies() -> None:
    reports = compare_residency_policies(kv_heads=4)
    assert set(reports) == {
        FRACTIONAL_SMEAR,
        LAYER_BALANCED_CONTIGUOUS,
        LOCALITY_AWARE,
    }
    assert reports[LOCALITY_AWARE]["placement"]["home_policy"] == "owner_cluster"
