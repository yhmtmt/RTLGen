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
R3_DIAGNOSTIC_PATH = (
    REPO_ROOT
    / "docs"
    / "proposals"
    / "prop_l1_decoder_attention_score32_local_temporal_reducer_gqa8_v1"
    / "legacy_lut_memory_boundary_r3_diagnostic.json"
)
R4_DIAGNOSTIC_PATH = (
    REPO_ROOT
    / "docs"
    / "proposals"
    / "prop_l1_decoder_attention_score32_local_temporal_reducer_gqa8_v1"
    / "factored_r4_oom_diagnostic.json"
)
R5_DIAGNOSTIC_PATH = (
    REPO_ROOT
    / "docs"
    / "proposals"
    / "prop_l1_decoder_attention_score32_local_temporal_reducer_gqa8_v1"
    / "factored_hier_r5_oom_diagnostic.json"
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
R5_SWEEP_PATH = (
    REPO_ROOT
    / "runs"
    / "campaigns"
    / "npu"
    / "attention_score32_local_temporal_reducer_gqa8_v1"
    / "sweeps"
    / "nangate45_attention_score32_local_temporal_reducer_gqa8_physical_harness_boundary_factored_hier_r5.json"
)
P53_CONFIG_PATH = (
    REPO_ROOT
    / "runs"
    / "designs"
    / "npu_blocks"
    / "attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p53_reducer_factored_hier_w8"
    / "config.json"
)
P54_CONFIG_PATH = (
    REPO_ROOT
    / "runs"
    / "designs"
    / "npu_blocks"
    / "attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p54_reducer_factored_hier_w8"
    / "config.json"
)


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_gqa8_factored_hier_r5_configs_are_reducer_only_and_preserve_merge_hierarchy() -> None:
    p53 = _load_json(P53_CONFIG_PATH)
    p54 = _load_json(P54_CONFIG_PATH)

    for config, producers in ((p53, 53), (p54, 54)):
        body = config["attention_score32_exact_local_temporal_reducer_gqa8_physical_harness"]
        assert body["producers"] == producers
        assert body["mode"] == "reducer"
        assert body["waves"] == 8
        assert body["exp_scale_impl"] == "factored_h33_l64_mul_exact"
        assert body["keep_hierarchy"] is True
        assert config["report_links"]["proposal_id"] == "prop_l1_decoder_attention_score32_local_temporal_reducer_gqa8_v1"


def test_gqa8_factored_hier_r5_sweep_keeps_no_share_without_memory_override() -> None:
    r4 = _load_json(R4_SWEEP_PATH)
    r5 = _load_json(R5_SWEEP_PATH)

    assert r5["tag_prefix"] == "attention_score32_local_temporal_reducer_gqa8_physical_harness_boundary_factored_hier_v1_r5"
    assert r5["tag_prefix"] != r4["tag_prefix"]
    assert r5["flow_params"] == {
        "CLOCK_PERIOD": [15.0, 20.0],
        "DIE_AREA": ["0 0 3000 3000"],
        "CORE_AREA": ["80 80 2920 2920"],
        "PLACE_DENSITY": [0.55],
        "SYNTH_HIERARCHICAL": [1],
        "SYNTH_ARGS": ["-noshare"],
    }
    assert "SYNTH_MEMORY_MAX_BITS" not in r5["flow_params"]
    assert "SYNTH_MEMORY_MAX_BITS" not in r4["flow_params"]


def test_gqa8_factored_hier_r5_docs_preserve_r4_and_r5_history() -> None:
    proposal = _load_json(PROPOSAL_PATH)
    requests = _load_json(REQUESTS_PATH)

    proposal_items = {item["item_id"]: item for item in proposal["required_evaluations"]}
    request_items = {item["item_id"]: item for item in requests["requested_items"]}

    r4 = proposal_items["l1_decoder_attention_score32_local_temporal_reducer_gqa8_factored_ppa_v1"]
    requested_r4 = request_items["l1_decoder_attention_score32_local_temporal_reducer_gqa8_factored_ppa_v1"]
    r5 = proposal_items["l1_decoder_attention_score32_local_temporal_reducer_gqa8_factored_hier_ppa_v1"]
    requested_r5 = request_items["l1_decoder_attention_score32_local_temporal_reducer_gqa8_factored_hier_ppa_v1"]

    assert r4["status"] == "failed_oom_canceled"
    assert requested_r4["status"] == "failed_oom_canceled"
    assert "run_de60dd9a4d966235" in r4["notes"]
    assert "factored_r4_oom_diagnostic.json" in requested_r4["notes"]

    assert r5["status"] == "failed_oom_canceled"
    assert requested_r5["status"] == "failed_oom_canceled"
    assert requested_r5["title"] == "Layer 1 GQA8 score32 local temporal reducer factorized-exp hierarchy-preserved boundary sweep"
    assert r5["configs"] == requested_r5["configs"] == [
        str(P53_CONFIG_PATH.relative_to(REPO_ROOT)),
        str(P54_CONFIG_PATH.relative_to(REPO_ROOT)),
    ]
    assert r5["sweep_path"] == requested_r5["sweep_path"] == str(R5_SWEEP_PATH.relative_to(REPO_ROOT))
    assert r5["expected_outputs"] == requested_r5["expected_outputs"] == [
        "runs/designs/npu_blocks/attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p53_reducer_factored_hier_w8/metrics.csv",
        "runs/designs/npu_blocks/attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p53_reducer_factored_hier_w8/timing_debug_report.md",
        "runs/designs/npu_blocks/attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p54_reducer_factored_hier_w8/metrics.csv",
        "runs/designs/npu_blocks/attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p54_reducer_factored_hier_w8/timing_debug_report.md",
    ]
    assert "keep `SYNTH_HIERARCHICAL=1`" in r5["acceptance_notes"]
    assert "merge-level `keep_hierarchy`" in r5["objective"]
    assert "Generate only the fresh r6 DB task" in requests["source_commit_note"]
    assert "factored_hier_r5_oom_diagnostic.json" in r5["notes"]
    assert "TECHMAP" in requested_r5["notes"]

    for ref in (
        str(R3_DIAGNOSTIC_PATH.relative_to(REPO_ROOT)),
        str(R4_DIAGNOSTIC_PATH.relative_to(REPO_ROOT)),
        str(R5_DIAGNOSTIC_PATH.relative_to(REPO_ROOT)),
        str(P53_CONFIG_PATH.relative_to(REPO_ROOT)),
        str(P54_CONFIG_PATH.relative_to(REPO_ROOT)),
        str(R5_SWEEP_PATH.relative_to(REPO_ROOT)),
    ):
        assert ref in proposal["source_refs"]


def test_gqa8_factored_r4_oom_diagnostic_matches_exact_db_evidence() -> None:
    diagnostic = _load_json(R4_DIAGNOSTIC_PATH)

    assert diagnostic["source_commit"] == "f8cd7cdd11342b539b5afb60f8761a2757d8e5c5"
    assert diagnostic["checkout_commit"] == "f8cd7cdd11342b539b5afb60f8761a2757d8e5c5"
    assert diagnostic["related_item_id"] == "l1_decoder_attention_score32_local_temporal_reducer_gqa8_factored_ppa_v1"
    assert diagnostic["work_item_uuid"] == "5f6c9288-362b-4b42-a932-ac0a4258747f"
    assert diagnostic["run_id"] == "e54d85c3-537a-4afd-9bfd-39a75837ab41"
    assert diagnostic["run_key"] == "l1_decoder_attention_score32_local_temporal_reducer_gqa8_factored_ppa_v1_run_de60dd9a4d966235"
    assert diagnostic["event_id"] == 1161
    assert diagnostic["evaluator"] == "eval-daemon-b7c2d9c80c1c"
    assert diagnostic["run_status"] == "CANCELED"
    assert diagnostic["failure_stage"] == (
        "run_block_sweep_attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p53_reducer_factored_w8"
    )
    assert diagnostic["failure_category"] == "command_canceled"
    assert diagnostic["run_runtime_seconds"] == 294.907201
    assert diagnostic["started_utc"] == "2026-08-03T11:23:54Z"
    assert diagnostic["completed_utc"] == "2026-08-03T11:28:48Z"

    first_point = diagnostic["first_point"]
    assert first_point["design"] == "attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p53_reducer_factored_w8"
    assert first_point["clock_period_ns"] == 15.0
    assert first_point["elapsed_seconds"] == 186.92
    assert first_point["peak_kb"] == 12238788
    assert first_point["cgroup_memory_max_bytes"] == 12884901888
    assert first_point["cgroup_memory_peak_bytes"] == 12884971520
    assert first_point["memory_events"] == {"oom": 2, "oom_kill": 1}
    assert "cleared the default synthesis memory-size guard" in first_point["observation"]

    cancellation = diagnostic["cancellation_rationale"]
    assert cancellation["second_point_canceled"] is True
    assert cancellation["second_point"] == {
        "design": "attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p53_reducer_factored_w8",
        "clock_period_ns": 20.0,
    }
    assert cancellation["p54_started"] is False
    assert "clock-independent OOM mode" in cancellation["reason"]

    worker_logs = diagnostic["worker_logs"]
    assert worker_logs["base"].endswith(
        "/03_run_block_sweep_attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p53_reducer_factored_w8"
    )
    assert worker_logs["stdout_log"].endswith(".stdout.log")
    assert worker_logs["stderr_log"].endswith(".stderr.log")

    assert diagnostic["known_orfs_path_patterns"]["results"] == [
        "/orfs/flow/results/nangate45/attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p53_reducer_factored_w8/base/<artifact>",
        "/orfs/flow/results/nangate45/attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p54_reducer_factored_w8/base/<artifact>",
    ]
    assert diagnostic["known_orfs_path_patterns"]["logs"] == [
        "/orfs/flow/logs/nangate45/attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p53_reducer_factored_w8/base/<step>.log",
        "/orfs/flow/logs/nangate45/attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p54_reducer_factored_w8/base/<step>.log",
    ]
