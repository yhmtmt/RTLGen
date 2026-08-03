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
R5_DIAGNOSTIC_PATH = (
    REPO_ROOT
    / "docs"
    / "proposals"
    / "prop_l1_decoder_attention_score32_local_temporal_reducer_gqa8_v1"
    / "factored_hier_r5_oom_diagnostic.json"
)
R6_SWEEP_PATH = (
    REPO_ROOT
    / "runs"
    / "campaigns"
    / "npu"
    / "attention_score32_local_temporal_reducer_gqa8_v1"
    / "sweeps"
    / "nangate45_attention_score32_local_temporal_reducer_gqa8_physical_harness_boundary_factored_hier_folded_mersenne_r6.json"
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


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_gqa8_folded_mersenne_r6_configs_select_folded_pair_nodes() -> None:
    p53 = _load_json(P53_CONFIG_PATH)
    p54 = _load_json(P54_CONFIG_PATH)

    for config, producers in ((p53, 53), (p54, 54)):
        body = config["attention_score32_exact_local_temporal_reducer_gqa8_physical_harness"]
        assert body["producers"] == producers
        assert body["mode"] == "reducer"
        assert body["waves"] == 8
        assert body["exp_scale_impl"] == "factored_h33_l64_mul_exact"
        assert body["pair_node_impl"] == "folded_sharedscale_mersenne_exact"
        assert body["keep_hierarchy"] is True


def test_gqa8_folded_mersenne_r6_sweep_uses_10ns_and_15ns() -> None:
    sweep = _load_json(R6_SWEEP_PATH)

    assert sweep["tag_prefix"] == (
        "attention_score32_local_temporal_reducer_gqa8_physical_harness_boundary_factored_hier_folded_mersenne_v1_r6"
    )
    assert sweep["flow_params"] == {
        "CLOCK_PERIOD": [10.0, 15.0],
        "DIE_AREA": ["0 0 3000 3000"],
        "CORE_AREA": ["80 80 2920 2920"],
        "PLACE_DENSITY": [0.55],
        "SYNTH_HIERARCHICAL": [1],
        "SYNTH_ARGS": ["-noshare"],
    }


def test_gqa8_folded_mersenne_r6_docs_preserve_r5_history_and_stage_r6() -> None:
    proposal = _load_json(PROPOSAL_PATH)
    requests = _load_json(REQUESTS_PATH)

    proposal_items = {item["item_id"]: item for item in proposal["required_evaluations"]}
    request_items = {item["item_id"]: item for item in requests["requested_items"]}

    r5 = proposal_items["l1_decoder_attention_score32_local_temporal_reducer_gqa8_factored_hier_ppa_v1"]
    requested_r5 = request_items["l1_decoder_attention_score32_local_temporal_reducer_gqa8_factored_hier_ppa_v1"]
    r6 = proposal_items["l1_decoder_attention_score32_local_temporal_reducer_gqa8_factored_hier_folded_mersenne_ppa_v1"]
    requested_r6 = request_items["l1_decoder_attention_score32_local_temporal_reducer_gqa8_factored_hier_folded_mersenne_ppa_v1"]

    assert r5["status"] == "failed_oom_canceled"
    assert requested_r5["status"] == "failed_oom_canceled"
    assert "factored_hier_r5_oom_diagnostic.json" in r5["notes"]
    assert "TECHMAP" in requested_r5["notes"]

    assert r6["status"] == "pending"
    assert requested_r6["status"] == "pending"
    assert requested_r6["title"] == (
        "Layer 1 GQA8 score32 local temporal reducer folded-Mersenne hierarchy-preserved boundary sweep"
    )
    assert r6["configs"] == requested_r6["configs"] == [
        str(P53_CONFIG_PATH.relative_to(REPO_ROOT)),
        str(P54_CONFIG_PATH.relative_to(REPO_ROOT)),
    ]
    assert r6["sweep_path"] == requested_r6["sweep_path"] == str(R6_SWEEP_PATH.relative_to(REPO_ROOT))
    assert "10ns and 15ns" in r6["acceptance_notes"]
    assert "replace the remaining wide generic-divider merge nodes" in r6["objective"]
    assert "Generate only the fresh r6 DB task" in requests["source_commit_note"]

    for ref in (
        str(R5_DIAGNOSTIC_PATH.relative_to(REPO_ROOT)),
        str(P53_CONFIG_PATH.relative_to(REPO_ROOT)),
        str(P54_CONFIG_PATH.relative_to(REPO_ROOT)),
        str(R6_SWEEP_PATH.relative_to(REPO_ROOT)),
    ):
        assert ref in proposal["source_refs"]


def test_gqa8_factored_hier_r5_diagnostic_matches_evaluator_evidence() -> None:
    diagnostic = _load_json(R5_DIAGNOSTIC_PATH)

    assert diagnostic["source_commit"] == "c2fbf8cac773dbec69b0fe91ab28ea3a96e877bd"
    assert diagnostic["related_item_id"] == "l1_decoder_attention_score32_local_temporal_reducer_gqa8_factored_hier_ppa_v1"
    assert diagnostic["work_item_uuid"] == "c727d5ac-a971-43fe-b325-590e57c7bd5d"
    assert diagnostic["run_id"] == "758b01d0-c15f-48ef-973f-a145d18df3db"
    assert diagnostic["run_key"] == (
        "l1_decoder_attention_score32_local_temporal_reducer_gqa8_factored_hier_ppa_v1_run_a3496c300f748aea"
    )
    assert diagnostic["evaluator"] == "eval-daemon-b7c2d9c80c1c"
    assert diagnostic["run_failure_category"] == "command_canceled"
    assert diagnostic["diagnostic_category"] == "techmap_oom_canceled"
    assert diagnostic["run_runtime_seconds"] == 166.18383
    assert diagnostic["primary_point"]["event_id"] == 1173
    assert diagnostic["primary_point"]["elapsed_seconds"] == 125.412839
    assert diagnostic["primary_point"]["rss_bytes"] == 12286513152
    assert diagnostic["primary_point"]["cgroup_events_before"] == {"oom": 2, "oom_kill": 1}
    assert diagnostic["primary_point"]["cgroup_events_after"] == {"oom": 4, "oom_kill": 2}
    assert diagnostic["cancellation"]["event_id"] == 1174
    assert diagnostic["canonical_hierarchy_evidence"]["hierarchy_retained"] is True
    assert diagnostic["canonical_hierarchy_evidence"]["aggregate_cells_before_mapping"] == 19135
    assert diagnostic["canonical_hierarchy_evidence"]["aggregate_div_cells_before_mapping"] == 954
    assert diagnostic["canonical_hierarchy_evidence"]["aggregate_mul_cells_before_mapping"] == 1060
