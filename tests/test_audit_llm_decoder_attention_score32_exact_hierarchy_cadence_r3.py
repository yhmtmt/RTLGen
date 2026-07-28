from argparse import Namespace
from pathlib import Path

from npu.eval.audit_llm_decoder_attention_score32_exact_hierarchy_cadence_r3 import (
    _build_markdown,
    _build_report,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


def _args(tmp_path: Path) -> Namespace:
    return Namespace(
        source_recost_json=REPO_ROOT
        / "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_composed_datapath_physical_feasibility__l2_decoder_attention_composed_datapath_score32_exp_lut_div_schedule_wrapper_recost_llama7b_v1.json",
        wrapper_config=REPO_ROOT
        / "runs/designs/npu_blocks/attention_dual_stream_schedule_wrapper_score32_exp_lut_8x8_c2/config.json",
        wrapper_metrics=REPO_ROOT
        / "runs/designs/npu_blocks/attention_dual_stream_schedule_wrapper_score32_exp_lut_8x8_c2/metrics.csv",
        exact_c16_config=REPO_ROOT
        / "runs/designs/npu_blocks/attention_score32_exact_partial_producer_tree_c16_r2_l8_b59/config.json",
        subtile_pipeline_generator=REPO_ROOT
        / "npu/eval/estimate_llm_decoder_attention_kv_subtile_pipeline_schedule.py",
        schedule_wrapper_generator=REPO_ROOT / "npu/rtlgen/gen_attention_dual_stream_schedule_wrapper.py",
        composed_generator=REPO_ROOT / "npu/rtlgen/gen_attention_dual_stream_composed.py",
        exact_c16_generator=REPO_ROOT
        / "npu/rtlgen/gen_attention_score32_exact_partial_producer_tree_c16.py",
        producer_cluster_generator=REPO_ROOT
        / "npu/rtlgen/gen_attention_decode_score_multivalue_cluster.py",
        attention_online_source=REPO_ROOT / "npu/sim/perf/attention_online.py",
        functional_producer_config=REPO_ROOT
        / "runs/designs/npu_blocks/attention_score32_exact_partial_gqa8_dual_stream_producer_b8/config_llama_wave_worst4_group_major.json",
        functional_producer_probe=REPO_ROOT
        / "npu/eval/probe_attention_score32_exact_partial_gqa8_dual_stream_producer.py",
        superseded_audit_json=REPO_ROOT
        / "npu/docs/generated/llama7b_score32_exact_hierarchy_cadence_audit_v2.json",
        out=tmp_path / "audit.json",
        out_md=tmp_path / "audit.md",
    )


def test_r3_uses_group_commands_and_corrected_worst4_service(tmp_path: Path) -> None:
    report = _build_report(_args(tmp_path))

    assert report["decision"] == "score32_986_cycle_arithmetic_not_sustained_by_corrected_group_command_mapping"
    revision = report["functional_producer_revision"]
    assert revision["mapping"] == {
        "token_blocks_per_1024_token_tile": 128,
        "token_streams_per_producer": 2,
        "gqa_groups": 4,
        "producer_command_contract": "one_gqa8_head_group_for_one_tile_wave_with_1or2_blocks_per_stream",
        "per_datapath_group_commands_per_wave": 4,
        "distribution_for_53_datapaths": {
            "dual_stream_datapaths": 53,
            "group_commands_per_datapath_per_wave": 4,
            "two_block_commands_per_stream_per_group": 11,
            "one_block_commands_per_stream_per_group": 42,
            "rotated_two_block_assignments_across_4_groups": 44,
            "datapaths_with_one_two_block_command": 44,
            "datapaths_with_zero_two_block_commands": 9,
            "worst_loaded_block_counts_per_stream": [2, 1, 1, 1],
        },
        "distribution_for_54_datapaths": {
            "dual_stream_datapaths": 54,
            "group_commands_per_datapath_per_wave": 4,
            "two_block_commands_per_stream_per_group": 10,
            "one_block_commands_per_stream_per_group": 44,
            "rotated_two_block_assignments_across_4_groups": 40,
            "datapaths_with_one_two_block_command": 40,
            "datapaths_with_zero_two_block_commands": 14,
            "worst_loaded_block_counts_per_stream": [2, 1, 1, 1],
        },
    }
    measured = revision["measured_service"]
    assert measured["passed"] is True
    assert measured["commands"] == 4
    assert measured["blocks_per_stream"] == 2
    assert measured["block_counts_per_stream"] == [2, 1, 1, 1]
    assert measured["interface_mode"] == "ideal"
    assert measured["integrated_drain_cycles"] == 1536
    assert measured["result_stall_cycles"] == 0
    assert measured["llama_wave_drain_delta_vs_986"] == 550
    assert revision["interpretation"]["reference_986_cycles_sustained"] is False
    assert revision["group_major_reducer_schedule"]["schedule_contract"] == (
        "process_one_fixed_gqa8_group_across_all_8_tile_waves_then_emit_finalize_before_next_head_base"
    )
    assert report["next_l1_contract"]["next_required_block"] == (
        "functional_53_54_way_local_exact_reducer_with_group_major_8_wave_persistent_state"
    )


def test_r3_markdown_records_group_major_schedule(tmp_path: Path) -> None:
    report = _build_report(_args(tmp_path))
    markdown = _build_markdown(report)

    assert "corrected ideal-interface producer service: `1536` cycles" in markdown
    assert "worst-loaded per-wave schedule: `[2, 1, 1, 1]`" in markdown
    assert "rotated p53 extras across 4 groups: `44` datapaths get one `2`-block command, `9` get none" in markdown
    assert "safe interleave: `not_established`" in markdown
