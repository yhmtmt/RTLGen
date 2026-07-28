from argparse import Namespace
from pathlib import Path

from npu.eval.audit_llm_decoder_attention_score32_exact_hierarchy_cadence_r2 import (
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
        / "runs/designs/npu_blocks/attention_score32_exact_partial_gqa8_dual_stream_producer_b8/config_llama_wave.json",
        functional_producer_probe=REPO_ROOT
        / "npu/eval/probe_attention_score32_exact_partial_gqa8_dual_stream_producer.py",
        out=tmp_path / "audit.json",
        out_md=tmp_path / "audit.md",
    )


def test_r2_uses_paired_gqa_jobs_and_measured_ideal_service(tmp_path: Path) -> None:
    report = _build_report(_args(tmp_path))

    assert report["decision"] == "score32_986_cycle_arithmetic_not_sustained_by_functional_exact_producer"
    revision = report["functional_producer_revision"]
    assert revision["mapping"] == {
        "token_blocks_per_1024_token_tile": 128,
        "token_streams_per_producer": 2,
        "paired_token_blocks": 64,
        "gqa_groups": 4,
        "paired_gqa_jobs_per_wave": 256,
        "distribution_for_53_datapaths": {
            "datapaths": 53,
            "paired_gqa_jobs": 256,
            "datapaths_with_5_jobs": 44,
            "datapaths_with_4_jobs": 9,
            "worst_loaded_commands": 5,
        },
        "distribution_for_54_datapaths": {
            "datapaths": 54,
            "paired_gqa_jobs": 256,
            "datapaths_with_5_jobs": 40,
            "datapaths_with_4_jobs": 14,
            "worst_loaded_commands": 5,
        },
        "producer_command_contract": "one_paired_token_block_times_one_gqa8_head_group",
        "producer_blocks_per_stream_per_command": 1,
    }
    measured = revision["measured_service"]
    assert measured["passed"] is True
    assert measured["interface_mode"] == "ideal"
    assert measured["commands"] == 5
    assert measured["integrated_drain_cycles"] == 1681
    assert measured["result_stall_cycles"] == 0
    assert measured["llama_wave_drain_delta_vs_986"] == 695
    assert revision["interpretation"]["reference_986_cycles_sustained"] is False
    assert report["next_l1_contract"]["next_required_block"] == (
        "functional_53_54_way_local_exact_reducer_with_8_wave_persistent_state"
    )


def test_r2_markdown_blocks_frontier_promotion(tmp_path: Path) -> None:
    report = _build_report(_args(tmp_path))
    markdown = _build_markdown(report)

    assert "paired GQA jobs/wave: `256`" in markdown
    assert "53 datapaths: `44` carry 5 jobs, `9` carry 4" in markdown
    assert "functional ideal-interface service: `1681` cycles" in markdown
    assert "current frontier must remain unpromoted" in markdown
