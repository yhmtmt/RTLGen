from argparse import Namespace
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.eval.audit_llm_decoder_attention_score32_local_reducer_measured_recost import build_report


def _args(tmp_path: Path) -> Namespace:
    return Namespace(
        exact_reduction_json=REPO_ROOT
        / "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_score32_exact_reduction_recost__l2_decoder_attention_score32_exact_reduction_recost_llama7b_v1.json",
        folded_global_json=REPO_ROOT
        / "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_score32_folded_global_exact_reduction_recost__l2_decoder_attention_score32_folded_global_exact_reduction_recost_llama7b_v2_r2.json",
        pair_metrics=REPO_ROOT
        / "runs/designs/npu_macros/attention_score32_exact_local_temporal_reducer_gqa8_pair_node_ng45_r7/metrics.csv",
        temporal_metrics=REPO_ROOT
        / "runs/designs/npu_macros/attention_score32_exact_local_temporal_reducer_gqa8_temporal_merge_ng45_r7/metrics.csv",
        macro_top_metrics=REPO_ROOT
        / "runs/designs/npu_blocks/attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p53_reducer_factored_hier_folded_mersenne_macro_w8/metrics.csv",
        macro_top_config=REPO_ROOT
        / "runs/designs/npu_blocks/attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p53_reducer_factored_hier_folded_mersenne_macro_w8/config.json",
        r6_diagnostic_json=REPO_ROOT
        / "docs/proposals/prop_l1_decoder_attention_score32_local_temporal_reducer_gqa8_v1/factored_hier_folded_mersenne_r6_globalplace_diagnostic.json",
        reducer_probe_config=REPO_ROOT
        / "runs/designs/npu_blocks/attention_score32_exact_local_temporal_reducer_gqa8_p53_w8/config.json",
        out=tmp_path / "report.json",
        out_md=tmp_path / "report.md",
    )


def test_local_reducer_measured_recost_records_bounded_schedule_and_macro_evidence(tmp_path: Path) -> None:
    report = build_report(_args(tmp_path))

    assert report["model"] == "llm_decoder_attention_score32_local_reducer_measured_recost_v1"
    assert report["decision"] == "score32_local_reducer_measured_bounded_recost_recorded"
    assert report["quality_rerun_required"] is False

    identity = report["identity_validation"]
    assert identity["pair_instance_count"] == 52
    assert identity["temporal_instance_count"] == 1
    assert identity["hierarchy_counts_match_r6_diagnostic"] is True

    pair = report["routed_component_ppa"]["pair_node"]
    temporal = report["routed_component_ppa"]["temporal_merge"]
    assert pair["critical_path_ns"] == 6.5967
    assert pair["die_area_um2"] == 108900.0
    assert pair["core_area_um2"] == 96100.0
    assert pair["total_power_mw"] == 0.24
    assert temporal["critical_path_ns"] == 6.5967
    assert temporal["die_area_um2"] == 108900.0
    assert temporal["core_area_um2"] == 96100.0
    assert temporal["total_power_mw"] == 0.24

    macro_sum = report["routed_component_ppa"]["macro_only_sum_per_cluster"]
    assert macro_sum["die_area_um2"] == 5771700.0
    assert macro_sum["core_area_um2"] == 5093300.0
    assert macro_sum["total_power_mw"] == 12.72
    assert macro_sum["die_area_mm2"] == 5.7717

    synth = report["routed_component_ppa"]["synthesis_area_lower_bound_per_cluster"]
    assert synth["total_hierarchy_stdcell_count"] == 1652145
    assert synth["total_hierarchy_area_um2"] == 3297112.826
    assert synth["total_hierarchy_area_mm2"] == 3.297113

    failures = report["macro_top_boundary_failures"]
    assert failures["10ns"]["classification"] == "global_route_oom_boundary"
    assert failures["10ns"]["failure_log_path"].endswith("/5_1_grt.log")
    assert failures["15ns"]["classification"] == "macro_placer_assertion"
    assert failures["15ns"]["failure_log_path"].endswith("/2_2_floorplan_macro.log")

    local_service = report["local_reducer_service_evidence"]
    assert local_service["measured_report"] == {
        "drain_cycles": 20730,
        "first_output_cycle": 20602,
        "last_output_cycle": 20729,
        "outputs": 128,
        "local_root_completed_count": 1024,
        "temporal_merge_completed_count": 896,
        "completed_command_count": 1,
    }
    assert local_service["service_model"]["comparison_cycle_origin"] == "cycle0_on_first_leaf_issue_of_group0_wave0"
    assert local_service["semantic_scope"]["includes_producer_compute_or_service"] is False

    global_tree = report["global_tree_finalizer_contract"]
    assert global_tree["service"]["full_wave_last_root_output_cycle"] == 2620
    assert global_tree["per_bank_output_latency_cycles"] == 58
    assert global_tree["per_bank_accept_interval_cycles"] == 59
    assert global_tree["composed_global_final_output_drain_cycles"] == 2678

    schedule = report["schedule_recost"]
    assert schedule["previous_bounded_interpretation"]["strict_serialized_bound_per_group_cycles"] == 6902
    assert schedule["corrected_bounded_schedule"]["strict_no_overlap_per_group_cycles"] == 27632
    assert schedule["corrected_bounded_schedule"]["conditional_overlap_lower_bound_per_group_cycles"] == 23408
    single_clock = schedule["single_clock_full_layer_bound"]
    assert single_clock["clock_ns"] == 48.6509
    assert single_clock["clock_origin"] == "inherited_single_clock_composed_compute_bound"
    assert single_clock["gqa_groups_per_layer"] == 4
    assert single_clock["producer_barrier_already_includes_all_8_waves_per_group"] is True
    assert single_clock["historical_tile_service_cycles_per_group_not_added"] == 986
    assert single_clock["strict_no_overlap_attention_tail_cycles"] == 110528
    assert single_clock["strict_no_overlap_layer_cycles"] == 110730
    assert single_clock["strict_no_overlap_total_cycles"] == 3543360
    assert single_clock["strict_no_overlap_latency_upper_bound_us"] == 172387.653024
    assert single_clock["strict_no_overlap_throughput_lower_bound_per_s"] == 5.800879485614
    assert single_clock["conditional_overlap_attention_tail_cycles"] == 93632
    assert single_clock["conditional_overlap_layer_cycles"] == 93834
    assert single_clock["conditional_overlap_total_cycles"] == 3002688
    assert single_clock["conditional_overlap_latency_lower_bound_us"] == 146083.473619
    assert single_clock["conditional_overlap_throughput_upper_bound_per_s"] == 6.845401298494

    dual_clock = schedule["dual_clock_component_rate_bound"]
    assert dual_clock["producer_clock_ns"] == 48.6509
    assert dual_clock["reducer_global_clock_ns"] == 8.0
    assert dual_clock["cdc_handshake_required"] is True
    assert dual_clock["measured_full_composition"] is False
    assert dual_clock["qkv_kv_single_clock_time_ns_per_layer"] == 9827.4818
    assert dual_clock["strict_no_overlap_group_time_ns"] == 392765.4016
    assert dual_clock["strict_no_overlap_latency_upper_bound_us"] == 50588.450822
    assert dual_clock["strict_no_overlap_throughput_lower_bound_per_s"] == 19.767357642925
    assert dual_clock["conditional_overlap_group_time_ns"] == 226925.4016
    assert dual_clock["conditional_overlap_latency_lower_bound_us"] == 29360.930822
    assert dual_clock["conditional_overlap_throughput_upper_bound_per_s"] == 34.058865710439

    best_requested = report["best_requested"]
    assert best_requested["cross_tile_reduction_cycles"] == 110528
    assert best_requested["replica_recost_tile_service_cycles"] == 0
    assert best_requested["tile_service_cycles"] == 0
    assert best_requested["historical_tile_service_cycles_per_group_source"] == 986
    assert best_requested["replica_recost_clock_ns"] == 48.6509
    assert best_requested["replica_recost_clock_origin"] == "inherited_single_clock_composed_compute_bound"
    assert best_requested["gqa_groups_per_layer"] == 4
    assert best_requested["producer_barrier_cycles_per_group"] == 4224
    assert best_requested["local_reducer_cycles_per_group"] == 20730
    assert best_requested["global_tree_cycles_per_group"] == 2678
    assert best_requested["replica_recost_layer_cycles"] == 110730
    assert best_requested["replica_recost_total_cycles"] == 3543360
    assert best_requested["replica_recost_latency_us"] == 172387.653024
    assert best_requested["local_reducer_measured_recost_replaces_unresolved_local_reducer_timing"] is True

    assert "single-clock bound inherits the 48.6509ns composed-compute clock" in " ".join(report["remaining_abstractions"])
