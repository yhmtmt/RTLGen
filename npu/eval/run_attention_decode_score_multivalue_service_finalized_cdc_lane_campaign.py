#!/usr/bin/env python3
"""Run the bounded lane-matched finalized-CDC functional probe campaign."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
import tempfile
from typing import Any, Callable

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from npu.eval.probe_attention_decode_score_multivalue_service_finalized_cdc import (
    build_report as build_probe_report,
)


JsonDict = dict[str, Any]
ProbeRunner = Callable[..., JsonDict]

_CAMPAIGN_MODEL = "attention_decode_score_multivalue_service_finalized_cdc_lane_campaign_v1"
_PROBE_MODEL = "attention_decode_score_multivalue_service_finalized_cdc_probe_v1"
_SERVICE_PERIOD_NS = 10.0
_TEMPORAL_PERIOD_NS = 12.0
_DIVIDER_LANES = (1, 2, 4, 8)
_TEMPORAL_STATE_BACKEND = "sram"
_SERVICE_VALUE_MEMORY_BACKEND = "macro_banked_4x16x64x32"
_SUMMARY_MODEL = "attention_decode_score_multivalue_service_finalized_cdc_probe_v1"
_AGGREGATE_MODEL = "attention_decode_score_multivalue_service_finalized_cdc_lane_campaign_summary_v1"
_PROPOSAL_ID = "prop_l2_decoder_attention_decode_score_multivalue_service_finalized_cdc_lane_probe_v1"
_PROPOSAL_PATH = f"docs/proposals/{_PROPOSAL_ID}/proposal.json"


def _load_json(path: Path) -> JsonDict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _portable_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(_REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _string(value: Any, label: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{label} must be a non-empty string")
    return text


def _finite_float(value: Any, label: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be finite") from exc
    if not math.isfinite(result) or result <= 0.0:
        raise ValueError(f"{label} must be positive and finite")
    return result


def _validate_campaign(payload: JsonDict) -> JsonDict:
    if _string(payload.get("model"), "campaign model") != _CAMPAIGN_MODEL:
        raise ValueError("campaign model mismatch")
    campaign_id = _string(payload.get("campaign_id"), "campaign_id")
    proposal_ref = payload.get("proposal_ref")
    if not isinstance(proposal_ref, dict):
        raise ValueError("campaign requires proposal_ref")
    proposal_id = _string(proposal_ref.get("proposal_id"), "proposal_ref.proposal_id")
    proposal_path = _string(proposal_ref.get("proposal_path"), "proposal_ref.proposal_path")
    if proposal_id != _PROPOSAL_ID or proposal_path != _PROPOSAL_PATH:
        raise ValueError("campaign proposal_ref must match the finalized-CDC lane-probe proposal")

    fixed = payload.get("fixed_parameters")
    if not isinstance(fixed, dict):
        raise ValueError("campaign requires fixed_parameters")
    service_period_ns = _finite_float(fixed.get("service_period_ns"), "service_period_ns")
    temporal_period_ns = _finite_float(fixed.get("temporal_period_ns"), "temporal_period_ns")
    if service_period_ns != _SERVICE_PERIOD_NS or temporal_period_ns != _TEMPORAL_PERIOD_NS:
        raise ValueError("campaign periods must be exactly service=10ns and temporal=12ns")
    if _string(fixed.get("temporal_state_backend"), "temporal_state_backend") != _TEMPORAL_STATE_BACKEND:
        raise ValueError("campaign temporal_state_backend must be sram")
    if (
        _string(fixed.get("service_value_memory_backend"), "service_value_memory_backend")
        != _SERVICE_VALUE_MEMORY_BACKEND
    ):
        raise ValueError("campaign service_value_memory_backend must be macro_banked_4x16x64x32")

    raw_lanes = payload.get("divider_lanes")
    if not isinstance(raw_lanes, list) or any(isinstance(value, bool) for value in raw_lanes):
        raise ValueError("campaign divider_lanes must be a list")
    try:
        lanes = tuple(int(value) for value in raw_lanes)
    except (TypeError, ValueError) as exc:
        raise ValueError("campaign divider_lanes must contain integers") from exc
    if lanes != _DIVIDER_LANES:
        raise ValueError("campaign divider_lanes must be exactly [1, 2, 4, 8]")

    return {
        "campaign_id": campaign_id,
        "proposal_ref": {
            "proposal_id": proposal_id,
            "proposal_path": proposal_path,
        },
        "service_period_ns": service_period_ns,
        "temporal_period_ns": temporal_period_ns,
        "divider_lanes": lanes,
        "temporal_state_backend": _TEMPORAL_STATE_BACKEND,
        "service_value_memory_backend": _SERVICE_VALUE_MEMORY_BACKEND,
    }


def _lightweight_probe_summary(report: JsonDict, *, campaign: JsonDict, lane: int) -> JsonDict:
    if report.get("passed") is not True:
        raise RuntimeError(f"finalized-CDC probe failed for divider_lanes={lane}")
    if _string(report.get("model"), "probe model") != _PROBE_MODEL:
        raise ValueError(f"probe model mismatch for divider_lanes={lane}")
    expected_values = {
        "service_period_ns": campaign["service_period_ns"],
        "temporal_period_ns": campaign["temporal_period_ns"],
        "divider_lanes": lane,
        "temporal_state_backend": campaign["temporal_state_backend"],
        "service_value_memory_backend": campaign["service_value_memory_backend"],
    }
    for key, expected in expected_values.items():
        if report.get(key) != expected:
            raise ValueError(f"probe {key} mismatch for divider_lanes={lane}")
    summary = report.get("summary")
    if not isinstance(summary, dict) or not summary:
        raise ValueError(f"probe summary missing for divider_lanes={lane}")
    normalized_summary: dict[str, int] = {}
    for key, value in summary.items():
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"probe summary.{key} must be an integer for divider_lanes={lane}")
        normalized_summary[str(key)] = value

    return {
        "model": _SUMMARY_MODEL,
        "passed": True,
        "service_period_ns": campaign["service_period_ns"],
        "temporal_period_ns": campaign["temporal_period_ns"],
        "divider_lanes": lane,
        "temporal_state_backend": campaign["temporal_state_backend"],
        "service_value_memory_backend": campaign["service_value_memory_backend"],
        "summary": dict(sorted(normalized_summary.items())),
        "campaign_provenance": {
            "campaign_id": campaign["campaign_id"],
            "proposal_ref": campaign["proposal_ref"],
            "full_probe_rows_omitted": True,
            "generated_rtl_manifests_omitted": True,
        },
    }


def run_campaign(
    *,
    campaign_path: Path,
    out_root: Path,
    probe_runner: ProbeRunner = build_probe_report,
) -> JsonDict:
    campaign_path = campaign_path.resolve()
    out_root = out_root.resolve()
    campaign = _validate_campaign(_load_json(campaign_path))
    out_root.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="finalized-cdc-lane-campaign-", dir=out_root.parent) as temp_name:
        stage_root = Path(temp_name)
        staged: list[tuple[Path, Path, JsonDict]] = []
        for lane in campaign["divider_lanes"]:
            print(f"running finalized-CDC probe divider_lanes={lane}", flush=True)
            full_report = probe_runner(
                service_period_ns=campaign["service_period_ns"],
                temporal_period_ns=campaign["temporal_period_ns"],
                divider_lanes=lane,
                temporal_state_backend=campaign["temporal_state_backend"],
                service_value_memory_backend=campaign["service_value_memory_backend"],
            )
            summary = _lightweight_probe_summary(full_report, campaign=campaign, lane=lane)
            staged_path = stage_root / f"lane{lane}.json"
            staged_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            staged.append((staged_path, out_root / staged_path.name, summary))
            print(f"passed finalized-CDC probe divider_lanes={lane}", flush=True)

        point_rows = [
            {
                "divider_lanes": summary["divider_lanes"],
                "output": _portable_path(final_path),
                "sha256": _sha256(staged_path),
                "service_cycles": summary["summary"].get("service_cycles"),
                "temporal_cycles": summary["summary"].get("temporal_cycles"),
                "finalizer_cycles_diagnostic": summary["summary"].get("finalizer_cycles"),
            }
            for staged_path, final_path, summary in staged
        ]
        aggregate = {
            "model": _AGGREGATE_MODEL,
            "campaign_id": campaign["campaign_id"],
            "passed": True,
            "proposal_ref": campaign["proposal_ref"],
            "campaign_path": _portable_path(campaign_path),
            "campaign_sha256": _sha256(campaign_path),
            "fixed_parameters": {
                "service_period_ns": campaign["service_period_ns"],
                "temporal_period_ns": campaign["temporal_period_ns"],
                "temporal_state_backend": campaign["temporal_state_backend"],
                "service_value_memory_backend": campaign["service_value_memory_backend"],
            },
            "divider_lanes": list(campaign["divider_lanes"]),
            "point_count": len(point_rows),
            "points": point_rows,
            "artifact_contract": {
                "per_lane_outputs_are_direct_recost_functional_probe_inputs": True,
                "observed_and_expected_rows_omitted": True,
                "generated_rtl_manifests_omitted": True,
            },
        }
        aggregate_stage = stage_root / "campaign_summary.json"
        aggregate_stage.write_text(json.dumps(aggregate, indent=2, sort_keys=True) + "\n", encoding="utf-8")

        out_root.mkdir(parents=True, exist_ok=True)
        for staged_path, final_path, _summary in staged:
            staged_path.replace(final_path)
        aggregate_stage.replace(out_root / "campaign_summary.json")
    return aggregate


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign", type=Path, required=True)
    parser.add_argument("--out-root", type=Path, required=True)
    args = parser.parse_args(argv)
    run_campaign(campaign_path=args.campaign, out_root=args.out_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
