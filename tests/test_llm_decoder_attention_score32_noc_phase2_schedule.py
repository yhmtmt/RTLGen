import argparse
import json
from pathlib import Path

import pytest

from npu.eval.measure_llm_decoder_attention_score32_noc_phase2_schedule import (
    DEFAULT_MEASURED_L1_COSTS,
    DEFAULT_SOURCE_JSON,
    build_report,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


def _args(**overrides: object) -> argparse.Namespace:
    values: dict[str, object] = {
        "repo_root": REPO_ROOT,
        "source_json": DEFAULT_SOURCE_JSON,
        "measured_l1_costs": DEFAULT_MEASURED_L1_COSTS,
        "wave_limit": 1,
        "packet_payload_bytes": 256,
        "cluster_endpoints": None,
        "root_endpoint": 15,
        "shared_vc": 0,
        "reduction_vc": 1,
        "max_cycles": 200000,
    }
    values.update(overrides)
    return argparse.Namespace(**values)


def test_score32_noc_phase2_report_is_explicit_and_bounded() -> None:
    report = build_report(_args())

    assert report["profile"] == "decoder_attention_score32_noc_phase2_schedule"
    assert report["source_contract"]["simulated_wave_count"] == 1
    assert report["traffic_quantities"]["simulated_tiles"] == report["source_contract"]["active_clusters"]
    assert report["flow_summary"]["remote_shared_flow_count"] > 0
    assert report["flow_summary"]["remote_reduction_flow_count"] > 0
    assert report["simulation"]["delivered_flit_count"] == report["simulation"]["scheduled_flit_count"]
    assert report["simulation"]["router_contention_cycles"] > 0
    assert any(
        "HBM/DRAM timing is intentionally excluded" in item
        for item in report["explicit_assumptions"]
    )


def test_score32_noc_phase2_rejects_missing_quantity(tmp_path: Path) -> None:
    source = json.loads((REPO_ROOT / DEFAULT_SOURCE_JSON).read_text(encoding="utf-8"))
    del source["best_requested"]["tile_waves"]
    broken = tmp_path / "broken_source.json"
    broken.write_text(json.dumps(source), encoding="utf-8")

    with pytest.raises(ValueError, match="tile_waves"):
        build_report(_args(source_json=broken))
