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
BASE_SWEEP_PATH = (
    REPO_ROOT
    / "runs"
    / "campaigns"
    / "npu"
    / "attention_score32_local_temporal_reducer_gqa8_v1"
    / "sweeps"
    / "nangate45_attention_score32_local_temporal_reducer_gqa8_physical_harness_boundary.json"
)
RETRY_SWEEP_PATH = (
    REPO_ROOT
    / "runs"
    / "campaigns"
    / "npu"
    / "attention_score32_local_temporal_reducer_gqa8_v1"
    / "sweeps"
    / "nangate45_attention_score32_local_temporal_reducer_gqa8_physical_harness_boundary_noshare_r2.json"
)


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_gqa8_physical_harness_noshare_retry_uses_distinct_sweep_identity() -> None:
    base = _load_json(BASE_SWEEP_PATH)
    retry = _load_json(RETRY_SWEEP_PATH)

    assert base["tag_prefix"] != retry["tag_prefix"]
    assert base["flow_params"] != retry["flow_params"]
    assert retry["flow_params"]["SYNTH_ARGS"] == ["-noshare"]
    assert "SYNTH_ARGS" not in base["flow_params"]
    for key in ("CLOCK_PERIOD", "DIE_AREA", "CORE_AREA", "PLACE_DENSITY", "SYNTH_HIERARCHICAL"):
        assert retry["flow_params"][key] == base["flow_params"][key]


def test_gqa8_physical_harness_noshare_retry_docs_preserve_v1_history() -> None:
    proposal = _load_json(PROPOSAL_PATH)
    requests = _load_json(REQUESTS_PATH)

    proposal_items = {item["item_id"]: item for item in proposal["required_evaluations"]}
    request_items = {item["item_id"]: item for item in requests["requested_items"]}

    historical = proposal_items["l1_decoder_attention_score32_local_temporal_reducer_gqa8_ppa_v1"]
    retry = proposal_items["l1_decoder_attention_score32_local_temporal_reducer_gqa8_ppa_v1_r2"]
    requested_retry = request_items["l1_decoder_attention_score32_local_temporal_reducer_gqa8_ppa_v1_r2"]

    assert historical["status"] == "failed_before_pnr"
    assert "SHARE (SAT-based resource sharing)" in historical["notes"]
    assert "Do not mutate or reuse this sweep identity for retries." in historical["notes"]

    assert retry["sweep_path"] == str(RETRY_SWEEP_PATH.relative_to(REPO_ROOT))
    assert retry["status"] == "failed_before_pnr"
    assert request_items["l1_decoder_attention_score32_local_temporal_reducer_gqa8_ppa_v1"]["status"] == (
        "failed_before_pnr"
    )
    assert request_items["l1_decoder_attention_score32_local_temporal_reducer_gqa8_ppa_v1_r2"]["status"] == "merged"
    assert requested_retry["sweep_path"] == retry["sweep_path"]
    assert "SAT-based resource-sharing pass" in retry["objective"]
    assert "`SYNTH_ARGS=-noshare`" in retry["objective"]
    assert "Synthesized memory size 4096 exceeds SYNTH_MEMORY_MAX_BITS" in retry["notes"]
    assert "Finalized via PR #1531" in requested_retry["notes"]
