import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PROPOSAL_DIR = (
    REPO_ROOT
    / "docs"
    / "proposals"
    / "prop_l1_decoder_attention_score32_local_temporal_reducer_gqa8_v1"
)
PROPOSAL_PATH = PROPOSAL_DIR / "proposal.json"
REQUESTS_PATH = PROPOSAL_DIR / "evaluation_requests.json"
R5_DIAGNOSTIC_PATH = PROPOSAL_DIR / "factored_hier_r5_oom_diagnostic.json"
R6_DIAGNOSTIC_PATH = PROPOSAL_DIR / "factored_hier_folded_mersenne_r6_globalplace_diagnostic.json"
R6_SWEEP_PATH = (
    REPO_ROOT
    / "runs"
    / "campaigns"
    / "npu"
    / "attention_score32_local_temporal_reducer_gqa8_v1"
    / "sweeps"
    / "nangate45_attention_score32_local_temporal_reducer_gqa8_physical_harness_boundary_factored_hier_folded_mersenne_r6.json"
)
R7_SWEEP_PATH = (
    REPO_ROOT
    / "runs"
    / "campaigns"
    / "npu"
    / "attention_score32_local_temporal_reducer_gqa8_v1"
    / "sweeps"
    / "nangate45_attention_score32_local_temporal_reducer_gqa8_physical_harness_boundary_factored_hier_folded_mersenne_macro_r7.json"
)
P53_CONFIG_PATH = (
    REPO_ROOT
    / "runs"
    / "designs"
    / "npu_blocks"
    / "attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p53_reducer_factored_hier_folded_mersenne_w8"
    / "config.json"
)
P54_CONFIG_PATH = (
    REPO_ROOT
    / "runs"
    / "designs"
    / "npu_blocks"
    / "attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p54_reducer_factored_hier_folded_mersenne_w8"
    / "config.json"
)
R7_CONFIG_PATH = (
    REPO_ROOT
    / "runs"
    / "designs"
    / "npu_blocks"
    / "attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p53_reducer_factored_hier_folded_mersenne_macro_w8"
    / "config.json"
)
P53_METRICS_PATH = (
    REPO_ROOT
    / "runs"
    / "designs"
    / "npu_blocks"
    / "attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p53_reducer_factored_hier_folded_mersenne_w8"
    / "metrics.csv"
)
P53_TIMING_PATH = (
    REPO_ROOT
    / "runs"
    / "designs"
    / "npu_blocks"
    / "attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p53_reducer_factored_hier_folded_mersenne_w8"
    / "timing_debug_report.md"
)
EXACT_SOURCE = "b41c0694737d69c26db9147d04f03bd0d531d802"


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_gqa8_folded_mersenne_r6_and_r7_configs_match_preserved_contract() -> None:
    p53 = _load_json(P53_CONFIG_PATH)
    p54 = _load_json(P54_CONFIG_PATH)
    r7 = _load_json(R7_CONFIG_PATH)

    for config, producers in ((p53, 53), (p54, 54), (r7, 53)):
        body = config["attention_score32_exact_local_temporal_reducer_gqa8_physical_harness"]
        assert body["producers"] == producers
        assert body["mode"] == "reducer"
        assert body["waves"] == 8
        assert body["exp_scale_impl"] == "factored_h33_l64_mul_exact"
        assert body["pair_node_impl"] == "folded_sharedscale_mersenne_exact"
        assert body["keep_hierarchy"] is True

    macro_hardening = r7["macro_hardening"]
    assert macro_hardening["enabled"] is True
    assert macro_hardening["die_area"] == "0 0 330 330"
    assert macro_hardening["core_area"] == "10 10 320 320"
    assert macro_hardening["pair_node_macro_id"] == (
        "attention_score32_exact_local_temporal_reducer_gqa8_pair_node_ng45_r7"
    )
    assert macro_hardening["temporal_merge_macro_id"] == (
        "attention_score32_exact_local_temporal_reducer_gqa8_temporal_merge_ng45_r7"
    )
    assert macro_hardening["bundle_design_id"] == (
        "attention_score32_exact_local_temporal_reducer_gqa8_macro_bundle_ng45_r7"
    )


def test_gqa8_folded_mersenne_r6_and_r7_sweeps_are_immutable_and_bounded() -> None:
    r6 = _load_json(R6_SWEEP_PATH)
    r7 = _load_json(R7_SWEEP_PATH)

    assert r6["tag_prefix"] == (
        "attention_score32_local_temporal_reducer_gqa8_physical_harness_boundary_"
        "factored_hier_folded_mersenne_v1_r6"
    )
    assert r6["flow_params"] == {
        "CLOCK_PERIOD": [10.0, 15.0],
        "DIE_AREA": ["0 0 3000 3000"],
        "CORE_AREA": ["80 80 2920 2920"],
        "PLACE_DENSITY": [0.55],
        "SYNTH_HIERARCHICAL": [1],
        "SYNTH_ARGS": ["-noshare"],
    }

    assert r7["tag_prefix"] == (
        "attention_score32_local_temporal_reducer_gqa8_physical_harness_boundary_"
        "factored_hier_folded_mersenne_macro_v1_r7"
    )
    assert r7["flow_params"] == {
        "CLOCK_PERIOD": [10.0, 15.0],
        "DIE_AREA": ["0 0 3500 3500"],
        "CORE_AREA": ["80 80 3420 3420"],
        "PLACE_DENSITY": [0.55],
        "SYNTH_HIERARCHICAL": [1],
        "SYNTH_ARGS": ["-noshare"],
    }


def test_gqa8_folded_mersenne_docs_preserve_rescued_r6_and_stage_r7_macro_retry() -> None:
    proposal = _load_json(PROPOSAL_PATH)
    requests = _load_json(REQUESTS_PATH)

    proposal_items = {item["item_id"]: item for item in proposal["required_evaluations"]}
    request_items = {item["item_id"]: item for item in requests["requested_items"]}

    r5 = proposal_items["l1_decoder_attention_score32_local_temporal_reducer_gqa8_factored_hier_ppa_v1"]
    requested_r5 = request_items["l1_decoder_attention_score32_local_temporal_reducer_gqa8_factored_hier_ppa_v1"]
    r6 = proposal_items["l1_decoder_attention_score32_local_temporal_reducer_gqa8_factored_hier_folded_mersenne_ppa_v1"]
    requested_r6 = request_items[
        "l1_decoder_attention_score32_local_temporal_reducer_gqa8_factored_hier_folded_mersenne_ppa_v1"
    ]
    r7 = proposal_items[
        "l1_decoder_attention_score32_local_temporal_reducer_gqa8_factored_hier_folded_mersenne_macro_ppa_v1"
    ]
    requested_r7 = request_items[
        "l1_decoder_attention_score32_local_temporal_reducer_gqa8_factored_hier_folded_mersenne_macro_ppa_v1"
    ]

    assert r5["status"] == "failed_oom_canceled"
    assert requested_r5["status"] == "failed_oom_canceled"
    assert "factored_hier_r5_oom_diagnostic.json" in r5["notes"]

    assert proposal["remaining_abstractions"][-1].startswith(
        "The fully instantiated folded p53 reducer now has measured one-group ideal service of 20730 drain cycles"
    )

    assert r6["status"] == "failed_oom_canceled"
    assert requested_r6["status"] == "failed_oom_canceled"
    assert r6["configs"] == requested_r6["configs"] == [
        str(P53_CONFIG_PATH.relative_to(REPO_ROOT)),
        str(P54_CONFIG_PATH.relative_to(REPO_ROOT)),
    ]
    assert r6["sweep_path"] == requested_r6["sweep_path"] == str(R6_SWEEP_PATH.relative_to(REPO_ROOT))
    assert "Do not claim p54 as measured." in r6["notes"]
    assert "Do not claim p54 as measured." in requested_r6["notes"]
    assert "Attempt 1 artifacts were recovered and attempt 2 was canceled" in r6["notes"]
    assert "global placement after synthesis" in requested_r6["notes"]

    assert r7["status"] == "pending"
    assert requested_r7["status"] == "pending"
    assert requested_r7["title"] == "Layer 1 GQA8 folded-Mersenne reducer macro-composed p53 boundary sweep"
    assert r7["configs"] == requested_r7["configs"] == [str(R7_CONFIG_PATH.relative_to(REPO_ROOT))]
    assert r7["sweep_path"] == requested_r7["sweep_path"] == str(R7_SWEEP_PATH.relative_to(REPO_ROOT))
    assert "pre_synth_compute.py" in r7["acceptance_notes"]
    assert "--macro_manifest" in r7["acceptance_notes"]
    assert "Do not add p54 to this item." in r7["acceptance_notes"]
    assert "20730 cycles versus the earlier 4224-cycle conservative producer barrier" in r7["expected_result"]["reason"]

    assert requests["source_commit"] == EXACT_SOURCE
    assert "Generate only the fresh r7 DB task" in requests["source_commit_note"]
    assert "must not claim p54 was measured" in requests["source_commit_note"]

    for ref in (
        str(R5_DIAGNOSTIC_PATH.relative_to(REPO_ROOT)),
        str(R6_DIAGNOSTIC_PATH.relative_to(REPO_ROOT)),
        str(P53_CONFIG_PATH.relative_to(REPO_ROOT)),
        str(P54_CONFIG_PATH.relative_to(REPO_ROOT)),
        str(R7_CONFIG_PATH.relative_to(REPO_ROOT)),
        str(R6_SWEEP_PATH.relative_to(REPO_ROOT)),
        str(R7_SWEEP_PATH.relative_to(REPO_ROOT)),
        "npu/synth/build_composite_macro_manifest.py",
        "control_plane/control_plane/services/l1_task_generator.py",
    ):
        assert ref in proposal["source_refs"]


def test_gqa8_folded_mersenne_r6_diagnostic_matches_recovered_globalplace_evidence() -> None:
    diagnostic = _load_json(R6_DIAGNOSTIC_PATH)

    assert diagnostic["source_commit"] == EXACT_SOURCE
    assert diagnostic["checkout_commit"] == EXACT_SOURCE
    assert diagnostic["related_item_id"] == (
        "l1_decoder_attention_score32_local_temporal_reducer_gqa8_factored_hier_folded_mersenne_ppa_v1"
    )
    assert diagnostic["run_failure_category"] == "flow_failed_signal_9"
    assert diagnostic["diagnostic_category"] == "globalplace_oom_artifacts_recovered"
    assert diagnostic["hierarchy_evidence"] == {
        "synthesis_succeeded": True,
        "measured_design_scope": "p53 only",
        "p54_measured": False,
        "top_logic_stdcell_count_excluding_submodules": 278859,
        "top_logic_area_um2_excluding_submodules": 623623.168,
        "local_pair_node_instances": 52,
        "local_pair_node_stdcell_count_each": 25904,
        "local_pair_node_area_um2_each": 50431.472,
        "temporal_merge_instances": 1,
        "temporal_merge_stdcell_count_each": 26331,
        "temporal_merge_area_um2_each": 51053.114,
        "total_hierarchy_stdcell_count": 1652145,
        "total_hierarchy_area_um2": 3297112.826,
    }
    assert diagnostic["cgroup_memory_evidence"]["events_before"] == {"oom": 4, "oom_kill": 2}
    assert diagnostic["cgroup_memory_evidence"]["events_after"] == {"oom": 8, "oom_kill": 6}
    assert diagnostic["attempt_history"] == {
        "attempt_1_artifacts_recovered": True,
        "attempt_2_canceled": True,
        "attempt_2_reason": (
            "The first attempt already recovered both p53 boundary rows, and the second attempt was canceled "
            "to avoid duplicating the same global-placement OOM evidence while p54 remained unstarted."
        ),
    }
    recovered_points = diagnostic["recovered_points"]
    assert [(point["clock_period_ns"], point["param_hash"]) for point in recovered_points] == [
        (10.0, "b3bca973"),
        (15.0, "cf6bf533"),
    ]
    assert diagnostic["measured_service_evidence"] == {
        "source_commit": EXACT_SOURCE,
        "scope": "p53 ideal one-group RTL/perf equivalence probe on current master",
        "drain_cycles": 20730,
        "first_output_cycle": 20602,
        "last_output_cycle": 20729,
        "local_root_completed_count": 1024,
        "temporal_merge_completed_count": 896,
        "output_count": 128,
        "conservative_producer_barrier_cycles_per_group": 4224,
        "slowdown_vs_conservative_barrier": 4.91,
        "observation": (
            "The fully instantiated folded reducer is both physically large and service-dominant: one group "
            "drains in 20730 cycles, 4.91x slower than the earlier 4224-cycle conservative producer barrier."
        ),
    }


def test_gqa8_folded_mersenne_r6_rescued_metrics_are_preserved_as_two_p53_rows_only() -> None:
    metrics_lines = P53_METRICS_PATH.read_text(encoding="utf-8").splitlines()
    timing_report = P53_TIMING_PATH.read_text(encoding="utf-8")

    assert len(metrics_lines) == 3
    assert "param_hash" in metrics_lines[0]
    assert "b3bca973" in metrics_lines[1]
    assert "cf6bf533" in metrics_lines[2]
    assert "flow_failed" in metrics_lines[1]
    assert "flow_failed" in metrics_lines[2]
    assert "globalplace,2" in metrics_lines[1]
    assert "globalplace,2" in metrics_lines[2]
    assert "p54" not in "\n".join(metrics_lines)
    assert "rows_considered: 0" in timing_report
    assert "No report_checks-style Startpoint/Endpoint path blocks were found." in timing_report
