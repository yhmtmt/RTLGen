from argparse import Namespace
import json
from pathlib import Path

import pytest

from npu.eval.audit_llm_decoder_attention_score32_exact_hierarchy_cadence import _build_markdown, _build_report


REPO_ROOT = Path(__file__).resolve().parents[1]


def _args(tmp_path: Path) -> Namespace:
    return Namespace(
        source_recost_json=REPO_ROOT
        / "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_composed_datapath_physical_feasibility__l2_decoder_attention_composed_datapath_score32_exp_lut_div_schedule_wrapper_recost_llama7b_v1.json",
        wrapper_config=REPO_ROOT / "runs/designs/npu_blocks/attention_dual_stream_schedule_wrapper_score32_exp_lut_8x8_c2/config.json",
        wrapper_metrics=REPO_ROOT / "runs/designs/npu_blocks/attention_dual_stream_schedule_wrapper_score32_exp_lut_8x8_c2/metrics.csv",
        exact_c16_config=REPO_ROOT / "runs/designs/npu_blocks/attention_score32_exact_partial_producer_tree_c16_r2_l8_b59/config.json",
        subtile_pipeline_generator=REPO_ROOT / "npu/eval/estimate_llm_decoder_attention_kv_subtile_pipeline_schedule.py",
        schedule_wrapper_generator=REPO_ROOT / "npu/rtlgen/gen_attention_dual_stream_schedule_wrapper.py",
        composed_generator=REPO_ROOT / "npu/rtlgen/gen_attention_dual_stream_composed.py",
        exact_c16_generator=REPO_ROOT / "npu/rtlgen/gen_attention_score32_exact_partial_producer_tree_c16.py",
        producer_cluster_generator=REPO_ROOT / "npu/rtlgen/gen_attention_decode_score_multivalue_cluster.py",
        attention_online_source=REPO_ROOT / "npu/sim/perf/attention_online.py",
        out=tmp_path / "audit.json",
        out_md=tmp_path / "audit.md",
    )


def test_score32_exact_hierarchy_cadence_report_matches_expected_counts(tmp_path: Path) -> None:
    report = _build_report(_args(tmp_path))

    assert report["decision"] == (
        "score32_schedule_wrapper_cadence_arithmetically_reproducible_but_exact_hierarchy_unclosed"
    )
    assert report["source_contract"]["tile_count"] == 128
    assert report["source_contract"]["tile_waves"] == 8
    assert report["arithmetically_reproduced_frontier"]["wrapper_config"] == {
        "clusters": 2,
        "streams": 2,
        "array_m": 8,
        "array_n": 8,
        "k_unroll": 1,
        "wrapper_cluster_macs_per_cycle": 128,
        "wrapper_total_macs_per_cycle": 256,
        "semantic_profile": "score32_exp_lut_div",
    }
    assert report["source_contract"]["wrapper_count"] == 428
    assert report["source_contract"]["wrapper_cluster_datapaths"] == 856
    assert report["source_contract"]["frontier_macs_per_cycle"] == 109568
    assert report["arithmetically_reproduced_frontier"]["global_distribution"] == {
        "clusters_with_54_datapaths": 8,
        "clusters_with_53_datapaths": 8,
        "conservative_per_cluster_macs_per_cycle": 6784,
    }
    assert report["arithmetically_reproduced_frontier"]["tile_work"] == {
        "qk_macs": 4194304,
        "value_macs": 4194304,
        "qk_cycles": 619,
        "value_cycles": 619,
        "stats_cycles": 116,
    }
    pipeline = report["arithmetically_reproduced_frontier"]["subtile_pipeline_reconstruction"]
    assert pipeline["subtile_count"] == 8
    assert pipeline["prefetch_distance"] == 3
    assert pipeline["subtile_qk_cycles"] == 78
    assert pipeline["subtile_value_cycles"] == 78
    assert pipeline["subtile_stats_cycles"] == 15
    assert pipeline["subtile_hbm_cycles"] == 163
    assert pipeline["subtile_aux_memory_cycles"] == 86
    assert pipeline["hbm_exposed_cycles"] == 815
    assert pipeline["aux_memory_span_cycles"] == 688
    assert pipeline["pipeline_attention_cycles"] == 986
    assert pipeline["trace"][-1] == {
        "subtile": 7,
        "hbm_ready_cycle": 815,
        "aux_release_cycle": 602,
        "qk_start_cycle": 815,
        "qk_done_cycle": 893,
        "stats_start_cycle": 893,
        "stats_done_cycle": 908,
        "value_start_cycle": 908,
        "value_done_cycle": 986,
    }
    exact_gap = report["exact_hierarchy_gap"]
    assert exact_gap["exact_c16_slice"] == {
        "producers": 16,
        "producer_score_tile_array_m": 1,
        "producer_score_tile_array_n": 8,
        "slice_macs_per_cycle": 128,
        "frontier_ratio": 856,
        "semantics_only_not_frontier_cadence": True,
    }
    assert exact_gap["block_protocol"] == {
        "tokens_per_block": 8,
        "placeholder_c16_config_max_blocks": 16,
        "placeholder_per_wave_blocks_per_head": 128,
        "placeholder_eight_wave_blocks_per_head_if_one_command": 1024,
        "placeholder_per_wave_shortfall_blocks": 112,
        "placeholder_eight_wave_shortfall_blocks": 1008,
        "placeholder_shortfall_is_diagnostic_only": True,
    }
    assert exact_gap["required_exact_hierarchy"]["local_merge_counts"] == {
        "clusters_with_54_datapaths": 8,
        "clusters_with_53_datapaths": 8,
        "merges_per_54_datapath_cluster": 53,
        "merges_per_53_datapath_cluster": 52,
        "total_local_merges_per_beat": 840,
        "global_merges_per_beat": 15,
    }
    assert exact_gap["required_exact_hierarchy"]["functional_producer_block_distribution_per_wave"] == {
        "blocks_per_tile": 128,
        "streams_per_functional_producer": 2,
        "streams_per_53_datapath_cluster": 106,
        "streams_per_54_datapath_cluster": 108,
        "distribution_for_53_datapaths": {
            "streams_with_2_blocks": 22,
            "streams_with_1_block": 84,
        },
        "distribution_for_54_datapaths": {
            "streams_with_2_blocks": 20,
            "streams_with_1_block": 88,
        },
        "max_blocks_per_stream_per_wave": 2,
        "supported_generator_min_max_blocks": 8,
        "supported_generator_min_max_blocks_suffices": True,
    }
    assert exact_gap["required_exact_hierarchy"]["selected_temporal_accumulation_boundary"] == (
        "per_wave_producer_emission_then_local_53_54_way_reduction_then_"
        "persistent_local_state_across_8_waves_then_one_c16_global_exact_reduction"
    )
    assert exact_gap["measured_wrapper_classification"] == {
        "deterministic_stimulus_not_full_token_replay": True,
        "seed_lfsr_and_stream_buffers_present": True,
        "ppa_outputs_exposed_directly": True,
        "functional_exact_partial_protocol_present": False,
        "structural_density_anchor_only": True,
    }
    assert report["next_l1_contract"] == {
        "proposal_id": "prop_l1_decoder_attention_score32_exact_partial_dual_stream_producer_v1",
        "required_functional_block": "functional_2stream_m8x8_exact_partial_producer_before_53_54_way_local_aggregation",
        "required_macs_per_cycle_per_functional_block": 128,
        "producer_streams": 2,
        "per_wave_blocks_per_tile": 128,
        "max_blocks_per_stream_per_wave": 2,
        "minimum_supported_max_blocks_for_functional_block": 8,
        "temporal_accumulation_boundary": (
            "local_reducer_persistent_across_8_waves_before_one_c16_global_exact_reduction"
        ),
        "placeholder_c16_max_blocks_shortfall_is_diagnostic_only": True,
        "structural_wrapper_density_is_insufficient_for_functional_closure": True,
    }
    assert report["non_claims"] == [
        "Do not revise frontier throughput or latency yet.",
        "The 986-cycle tile service point is arithmetically reproducible from checked-in sources, but hardware-equivalence closure remains open.",
        "The native c16 exact slice proves protocol semantics only; it does not validate the 109568-MAC/cycle frontier cadence.",
        "The next unmeasured block is the local 53/54-way reducer plus temporal exact-partial state across 8 waves.",
    ]


def test_score32_exact_hierarchy_cadence_markdown_mentions_non_claims_and_max_blocks(tmp_path: Path) -> None:
    report = _build_report(_args(tmp_path))
    markdown = _build_markdown(report)

    assert "placeholder blocks per 1024-token tile: `128`" in markdown
    assert "placeholder blocks per head for one-command eight-wave persistence: `1024`" in markdown
    assert "That fixes per-wave producer demand at `2` blocks/stream" in markdown
    assert "minimum supported producer `max_blocks`: `8`" in markdown
    assert "The measured dual-stream wrapper is a structural PPA anchor, not a functional exact-partial producer." in markdown
    assert "Do not revise frontier throughput or latency yet." in markdown


def test_score32_exact_hierarchy_cadence_rejects_wrong_wrapper_cluster_count(tmp_path: Path) -> None:
    args = _args(tmp_path)
    payload = json.loads(Path(args.wrapper_config).read_text(encoding="utf-8"))
    payload["attention_dual_stream_schedule_wrapper"]["clusters"] = 3
    broken = tmp_path / "wrapper_config_bad.json"
    broken.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    args.wrapper_config = broken

    with pytest.raises(ValueError, match="wrapper config clusters must be 2"):
        _build_report(args)
