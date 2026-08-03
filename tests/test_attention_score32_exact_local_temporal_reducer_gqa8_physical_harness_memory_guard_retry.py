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
R2_SWEEP_PATH = (
    REPO_ROOT
    / "runs"
    / "campaigns"
    / "npu"
    / "attention_score32_local_temporal_reducer_gqa8_v1"
    / "sweeps"
    / "nangate45_attention_score32_local_temporal_reducer_gqa8_physical_harness_boundary_noshare_r2.json"
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


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_gqa8_physical_harness_memory_guard_retry_uses_distinct_sweep_identity() -> None:
    r2 = _load_json(R2_SWEEP_PATH)
    r3 = _load_json(R3_SWEEP_PATH)

    assert r2["tag_prefix"] != r3["tag_prefix"]
    assert r2["flow_params"] != r3["flow_params"]
    assert r3["flow_params"]["SYNTH_ARGS"] == ["-noshare"]
    assert r3["flow_params"]["SYNTH_MEMORY_MAX_BITS"] == [65536]
    assert "SYNTH_MEMORY_MAX_BITS" not in r2["flow_params"]
    for key in ("CLOCK_PERIOD", "DIE_AREA", "CORE_AREA", "PLACE_DENSITY", "SYNTH_HIERARCHICAL"):
        assert r3["flow_params"][key] == r2["flow_params"][key]


def test_gqa8_physical_harness_memory_guard_retry_docs_preserve_history() -> None:
    proposal = _load_json(PROPOSAL_PATH)
    requests = _load_json(REQUESTS_PATH)

    proposal_items = {item["item_id"]: item for item in proposal["required_evaluations"]}
    request_items = {item["item_id"]: item for item in requests["requested_items"]}

    r2 = proposal_items["l1_decoder_attention_score32_local_temporal_reducer_gqa8_ppa_v1_r2"]
    r3 = proposal_items["l1_decoder_attention_score32_local_temporal_reducer_gqa8_ppa_v1_r3"]
    requested_r3 = request_items["l1_decoder_attention_score32_local_temporal_reducer_gqa8_ppa_v1_r3"]

    assert r2["status"] == "failed_before_pnr"
    assert "Synthesized memory size 4096 exceeds SYNTH_MEMORY_MAX_BITS" in r2["notes"]
    assert "p53 reducer 8ns/10ns failed at 71.08s/71.30s" in r2["notes"]
    assert "p54 reducer 8ns/10ns failed at 69.01s/73.47s" in r2["notes"]
    assert "p53 8ns cp 0.8517 area 10794.3 cells 19522 power 0.00302" in r2["notes"]
    assert "p53 10ns cp 0.8663 area 10796.4 cells 19527 power 0.00245" in r2["notes"]
    assert "p54 8ns cp 0.8785 area 10560.2 cells 19367 power 0.00255" in r2["notes"]
    assert "p54 10ns cp 0.9874 area 10559.7 cells 19365 power 0.00209" in r2["notes"]
    assert "surrounding harness is viable" in r2["notes"]
    assert "remaining abort is the reducer-state guard" in r2["notes"]
    assert "Keep status `failed_before_pnr`." in r2["notes"]
    assert "Do not mutate or reuse this sweep identity for retries." in r2["notes"]

    assert r3["sweep_path"] == str(R3_SWEEP_PATH.relative_to(REPO_ROOT))
    assert r3["status"] == "pending"
    assert requested_r3["sweep_path"] == r3["sweep_path"]
    requested_r2 = request_items["l1_decoder_attention_score32_local_temporal_reducer_gqa8_ppa_v1_r2"]
    assert requested_r2["status"] == "merged"
    assert requested_r2["merged_pr_number"] == 1531
    assert requested_r2["merge_commit"] == "3afd7e718343e7a84a4b3bf158b5a4a6128dcaf8"
    assert requested_r2["merged_utc"] == "2026-08-03T10:22:05.177708Z"
    assert "Finalized via PR #1531" in requested_r2["notes"]
    assert "`SYNTH_MEMORY_MAX_BITS=65536`" in r3["objective"]
    assert "does not alter RTL semantics" in r3["objective"]
    assert "required 4096-bit persistent state" in r3["acceptance_notes"]
    assert "65536-bit guard" in r3["acceptance_notes"]
