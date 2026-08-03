import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PROPOSAL_PATH = (
    REPO_ROOT
    / "docs"
    / "proposals"
    / "prop_l1_decoder_attention_score32_local_temporal_reducer_gqa8_v1"
    / "proposal.json"
)
REQUESTS_PATH = (
    REPO_ROOT
    / "docs"
    / "proposals"
    / "prop_l1_decoder_attention_score32_local_temporal_reducer_gqa8_v1"
    / "evaluation_requests.json"
)
DIAGNOSTIC_PATH = (
    REPO_ROOT
    / "docs"
    / "proposals"
    / "prop_l1_decoder_attention_score32_local_temporal_reducer_gqa8_v1"
    / "legacy_lut_memory_boundary_r3_diagnostic.json"
)
R3_SWEEP_PATH = (
    REPO_ROOT
    / "runs"
    / "campaigns"
    / "npu"
    / "attention_score32_local_temporal_reducer_gqa8_v1"
    / "sweeps"
    / "nangate45_attention_score32_local_temporal_reducer_gqa8_physical_harness_boundary_noshare_memguard_r3.json"
)
R4_SWEEP_PATH = (
    REPO_ROOT
    / "runs"
    / "campaigns"
    / "npu"
    / "attention_score32_local_temporal_reducer_gqa8_v1"
    / "sweeps"
    / "nangate45_attention_score32_local_temporal_reducer_gqa8_physical_harness_boundary_factored_r4.json"
)
P53_CONFIG_PATH = (
    REPO_ROOT
    / "runs"
    / "designs"
    / "npu_blocks"
    / "attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p53_reducer_factored_w8"
    / "config.json"
)
P54_CONFIG_PATH = (
    REPO_ROOT
    / "runs"
    / "designs"
    / "npu_blocks"
    / "attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p54_reducer_factored_w8"
    / "config.json"
)


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_gqa8_factored_r4_configs_are_reducer_only() -> None:
    p53 = _load_json(P53_CONFIG_PATH)
    p54 = _load_json(P54_CONFIG_PATH)

    for config, producers in ((p53, 53), (p54, 54)):
        body = config["attention_score32_exact_local_temporal_reducer_gqa8_physical_harness"]
        assert body["producers"] == producers
        assert body["mode"] == "reducer"
        assert body["waves"] == 8
        assert body["exp_scale_impl"] == "factored_h33_l64_mul_exact"
        assert config["report_links"]["proposal_id"] == "prop_l1_decoder_attention_score32_local_temporal_reducer_gqa8_v1"


def test_gqa8_factored_r4_sweep_keeps_no_share_without_memory_override() -> None:
    r3 = _load_json(R3_SWEEP_PATH)
    r4 = _load_json(R4_SWEEP_PATH)

    assert r4["tag_prefix"] == "attention_score32_local_temporal_reducer_gqa8_physical_harness_boundary_factored_v1_r4"
    assert r4["tag_prefix"] != r3["tag_prefix"]
    assert r4["flow_params"] == {
        "CLOCK_PERIOD": [15.0, 20.0],
        "DIE_AREA": ["0 0 3000 3000"],
        "CORE_AREA": ["80 80 2920 2920"],
        "PLACE_DENSITY": [0.55],
        "SYNTH_HIERARCHICAL": [1],
        "SYNTH_ARGS": ["-noshare"],
    }
    assert "SYNTH_MEMORY_MAX_BITS" not in r4["flow_params"]
    assert r3["flow_params"]["SYNTH_MEMORY_MAX_BITS"] == [65536]


def test_gqa8_factored_r4_docs_link_job_and_preserve_r3_metadata() -> None:
    proposal = _load_json(PROPOSAL_PATH)
    requests = _load_json(REQUESTS_PATH)

    proposal_items = {item["item_id"]: item for item in proposal["required_evaluations"]}
    request_items = {item["item_id"]: item for item in requests["requested_items"]}

    r3 = request_items["l1_decoder_attention_score32_local_temporal_reducer_gqa8_ppa_v1_r3"]
    r4 = proposal_items["l1_decoder_attention_score32_local_temporal_reducer_gqa8_factored_ppa_v1"]
    requested_r4 = request_items["l1_decoder_attention_score32_local_temporal_reducer_gqa8_factored_ppa_v1"]

    assert r3["status"] == "merged"
    assert r3["merged_pr_number"] == 1533
    assert r3["merge_commit"] == "d96c3379c3af228606f9b266142529255fd12699"
    assert r3["merged_utc"] == "2026-08-03T10:58:06.037636Z"

    assert requests["source_commit"] == "379b4e723cb2a8ee61ce82bcb027b8bec9e7e0db"
    assert "legacy monolithic exp-LUT encoding boundary" in requests["source_commit_note"]

    assert r4["status"] == "pending"
    assert requested_r4["status"] == "pending"
    assert r4["configs"] == requested_r4["configs"] == [
        str(P53_CONFIG_PATH.relative_to(REPO_ROOT)),
        str(P54_CONFIG_PATH.relative_to(REPO_ROOT)),
    ]
    assert r4["sweep_path"] == requested_r4["sweep_path"] == str(R4_SWEEP_PATH.relative_to(REPO_ROOT))
    assert r4["expected_outputs"] == requested_r4["expected_outputs"] == [
        "runs/designs/npu_blocks/attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p53_reducer_factored_w8/metrics.csv",
        "runs/designs/npu_blocks/attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p53_reducer_factored_w8/timing_debug_report.md",
        "runs/designs/npu_blocks/attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p54_reducer_factored_w8/metrics.csv",
        "runs/designs/npu_blocks/attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p54_reducer_factored_w8/timing_debug_report.md",
    ]
    assert "do not add `SYNTH_MEMORY_MAX_BITS`" in r4["acceptance_notes"]
    assert "Do not rerun source_only controls" in r4["acceptance_notes"]
    assert "factorized configs, sweep, and diagnostic evidence" in requested_r4["notes"]

    for ref in (
        str(P53_CONFIG_PATH.relative_to(REPO_ROOT)),
        str(P54_CONFIG_PATH.relative_to(REPO_ROOT)),
        str(R4_SWEEP_PATH.relative_to(REPO_ROOT)),
        str(DIAGNOSTIC_PATH.relative_to(REPO_ROOT)),
    ):
        assert ref in proposal["source_refs"]


def test_gqa8_factored_r4_diagnostic_arithmetic_matches_generator_structure() -> None:
    diagnostic = _load_json(DIAGNOSTIC_PATH)

    assert diagnostic["merge_commit"] == "d96c3379c3af228606f9b266142529255fd12699"
    assert diagnostic["r3_source_commit"] == "c733716b4756afe2eaf41e4feccb060a4de29f2c"
    assert diagnostic["source_identification"]["evaluator_machine_key"] == "eval-daemon-b7c2d9c80c1c"
    assert diagnostic["source_identification"]["result_mem_json_paths"] == [
        "/orfs/flow/results/nangate45/attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p53_reducer_w8/base/mem.json",
        "/orfs/flow/results/nangate45/attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p54_reducer_w8/base/mem.json",
    ]
    assert diagnostic["legacy_monolithic_exp_lut"]["per_memory_kind"] == "$mem_v2"
    assert diagnostic["legacy_monolithic_exp_lut"]["depth"] == 4096
    assert diagnostic["legacy_monolithic_exp_lut"]["width_bits"] == 24
    assert diagnostic["legacy_monolithic_exp_lut"]["bits_per_memory"] == 4096 * 24
    assert diagnostic["failure_text_observation"]["text"] == (
        "Error: Synthesized memory size 65536 exceeds SYNTH_MEMORY_MAX_BITS"
    )
    assert diagnostic["failure_text_observation"]["actual_max_instance_bits"] == 98304
    assert "prints args.max_bits" in diagnostic["failure_text_observation"]["mem_dump_behavior"]
    assert "configured threshold comparison" in diagnostic["failure_text_observation"]["meaning"]

    for name, producers, expected_memories, expected_total_bits in (
        ("p53", 53, 106, 10420224),
        ("p54", 54, 108, 10616832),
    ):
        case = diagnostic["cases"][name]
        local_nodes = producers - 1
        temporal_nodes = 1
        exp_lut_evals = 2
        assert case["producers"] == producers
        assert case["local_merge_nodes"] == local_nodes
        assert case["temporal_merge_nodes"] == temporal_nodes
        assert case["exp_lut_evaluations_per_merge"] == exp_lut_evals
        assert case["inferred_memories"] == expected_memories == exp_lut_evals * (local_nodes + temporal_nodes)
        assert case["all_memories_match_4096x24"] is True
        assert case["total_bits"] == expected_total_bits == expected_memories * 4096 * 24
