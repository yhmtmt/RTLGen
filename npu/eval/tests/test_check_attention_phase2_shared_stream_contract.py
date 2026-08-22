from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from npu.eval.check_attention_phase2_shared_stream_contract import (
    ArtifactContractError,
    validate_artifact,
)


ARTIFACT = (
    Path(__file__).resolve().parents[3]
    / "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
    "decoder_attention_score32_noc_phase2_schedule__"
    "l2_decoder_attention_score32_noc_phase2_schedule_llama7b_v1_r1.json"
)


def _load() -> dict[str, object]:
    return json.loads(ARTIFACT.read_text(encoding="utf-8"))


def _write(tmp_path: Path, payload: dict[str, object]) -> Path:
    path = tmp_path / "phase2.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_checked_artifact_passes_and_reports_reduction_independence() -> None:
    result = validate_artifact(ARTIFACT)
    assert result["status"] == "ok"
    assert result["shared"] == {
        "contexts": 112,
        "bytes": 1_949_696,
        "packets": 7_616,
        "flits": 60_928,
        "packet_bytes": 256,
        "flits_per_packet": 8,
        "mapping_shifts": [4, 7, 10, 13, 0, 3, 6, 9],
    }
    assert result["retracted_reduction_validation"] == "ignored"


@pytest.mark.parametrize(
    ("section", "field", "value"),
    [
        ("flow_summary", "remote_shared_flow_count", 111),
        ("flow_summary", "remote_shared_packet_count", 1),
        ("flow_summary", "remote_shared_bytes", 0),
        ("mapping", "shared_sram_home_offset", 2),
        ("mapping", "shared_sram_home_stride", 5),
        ("mapping", "shared_sram_home_load_tiles", {str(i): 7 for i in range(16)}),
    ],
)
def test_shared_quantity_or_mapping_drift_fails_closed(
    tmp_path: Path, section: str, field: str, value: object
) -> None:
    payload = _load()
    section_payload = payload[section]
    assert isinstance(section_payload, dict)
    section_payload[field] = value
    with pytest.raises(ArtifactContractError):
        validate_artifact(_write(tmp_path, payload))


def test_reduction_values_are_not_used_as_shared_evidence(tmp_path: Path) -> None:
    payload = _load()
    flow_summary = payload["flow_summary"]
    assert isinstance(flow_summary, dict)
    flow_summary["remote_reduction_packet_count"] = 7_616
    flow_summary["remote_reduction_bytes"] = 1_949_696
    flow_summary["remote_reduction_flow_count"] = 112
    simulation = payload["simulation"]
    assert isinstance(simulation, dict)
    classes = simulation["delivery_flit_count_by_class"]
    assert isinstance(classes, dict)
    classes["reduction"] = 60_928
    result = validate_artifact(_write(tmp_path, payload))
    assert result["status"] == "ok"
    assert result["retracted_reduction_validation"] == "ignored"


def test_missing_shared_fields_do_not_fall_back_to_reduction(tmp_path: Path) -> None:
    payload = _load()
    flow_summary = payload["flow_summary"]
    assert isinstance(flow_summary, dict)
    del flow_summary["remote_shared_packet_count"]
    flow_summary["remote_reduction_packet_count"] = 7_616
    with pytest.raises(ArtifactContractError):
        validate_artifact(_write(tmp_path, payload))


def test_direct_shift_vector_if_present_must_match(tmp_path: Path) -> None:
    payload = _load()
    mapping = payload["mapping"]
    assert isinstance(mapping, dict)
    mapping["shared_sram_home_shifts"] = [4, 7, 10, 13, 1, 3, 6, 9]
    with pytest.raises(ArtifactContractError):
        validate_artifact(_write(tmp_path, payload))
