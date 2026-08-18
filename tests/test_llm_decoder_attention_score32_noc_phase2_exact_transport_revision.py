from __future__ import annotations

import json
from pathlib import Path

import pytest

from npu.eval.revise_llm_decoder_attention_score32_noc_phase2_exact_transport import (
    DEFAULT_EXACT_MANIFEST,
    DEFAULT_PRIOR_SCHEDULE,
    build_report,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_revision_uses_embodied_exact_link_and_group_release_contract() -> None:
    report = build_report(
        exact_manifest=REPO_ROOT / DEFAULT_EXACT_MANIFEST,
        prior_schedule=REPO_ROOT / DEFAULT_PRIOR_SCHEDULE,
    )

    assert report["decision"] == (
        "prior_phase2_reduction_contract_retracted_exact_transport_required"
    )
    assert report["exact_source"] == {
        "manifest": str(REPO_ROOT / DEFAULT_EXACT_MANIFEST),
        "clusters": 16,
        "head_groups": 4,
        "heads_per_group": 8,
        "persistent_local_waves_per_group": 8,
        "slices_per_head": 16,
        "aggregate_beats_per_group_per_cluster": 128,
        "partial_link_bits_per_beat": 419,
        "partial_payload_bits_per_beat": 328,
        "stats_bits_per_head": 65,
        "release_contract": (
            "one aggregate stream per head group after eight local waves"
        ),
    }
    modes = {mode["name"]: mode for mode in report["exact_transport_modes"]}
    assert modes["aligned_419b_two_flits_per_beat"]["total_phase2_flits"] == 76288
    assert modes["packed_419b_group_bitstream"]["total_phase2_flits"] == 73528
    assert modes["stats_once_ordered_exact"] == {
        "name": "stats_once_ordered_exact",
        "bits_per_group": 42504,
        "flits_per_group": 167,
        "packets_per_group": 21,
        "flits_per_cluster_layer": 668,
        "packets_per_cluster_layer": 84,
        "remote_reduction_flits": 10020,
        "remote_reduction_packets": 1260,
        "total_phase2_flits": 70948,
        "total_phase2_commands": 8876,
        "flit_reduction_vs_prior": 21180,
        "flit_ratio_vs_prior": 0.770102,
    }


def test_revision_rejects_nonexact_manifest(tmp_path: Path) -> None:
    manifest = json.loads((REPO_ROOT / DEFAULT_EXACT_MANIFEST).read_text())
    manifest["service_model"]["partial_link_bits_per_beat"] = 418
    bad_manifest = tmp_path / "manifest.json"
    bad_manifest.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ValueError, match="partial_link_bits_per_beat mismatch"):
        build_report(
            exact_manifest=bad_manifest,
            prior_schedule=REPO_ROOT / DEFAULT_PRIOR_SCHEDULE,
        )
