import json
from pathlib import Path
import shutil
import sys

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.eval.probe_attention_decode_score_multivalue_integrated_service import (
    DEFAULT_CASES,
    REPORT_EXCLUSIONS,
    build_report,
    validate_report,
)
from npu.rtlgen.gen_attention_decode_score_multivalue_service import generate


def _iverilog_available() -> bool:
    return bool(shutil.which("iverilog") and shutil.which("vvp"))


def _case(
    *,
    case_id: str,
    cluster_count: int,
    packet_w: int,
    banks: int,
    arb_mode: str,
    locality_burst_max: int = 2,
    req_queue_depth: int = 2,
    resp_queue_depth: int = 2,
    bank_queue_depth: int = 2,
    read_latency: int = 2,
) -> dict:
    return {
        "case_id": case_id,
        "cluster_count": cluster_count,
        "packet_w": packet_w,
        "banks": banks,
        "req_queue_depth": req_queue_depth,
        "resp_queue_depth": resp_queue_depth,
        "bank_queue_depth": bank_queue_depth,
        "read_latency": read_latency,
        "arb_mode": arb_mode,
        "locality_burst_max": locality_burst_max,
    }


def test_multivalue_service_generator_manifest(tmp_path: Path) -> None:
    config = {
        "top_name": "attention_decode_score_multivalue_service_smoke",
        "attention_decode_score_multivalue_service": {
            "cluster_count": 4,
            "max_blocks": 16,
            "packet_w": 256,
            "banks": 8,
            "req_queue_depth": 3,
            "resp_queue_depth": 2,
            "bank_queue_depth": 3,
            "read_latency": 3,
            "arb_mode": "locality_first_bounded",
            "locality_burst_max": 3,
            "score_scale_lanes_per_cycle": 1,
        },
    }
    generate(config, tmp_path)
    manifest = json.loads(
        (tmp_path / "attention_decode_score_multivalue_service_manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["semantic_profile"] == "decode_m1x8_shared_score_16x8d_value_iterdiv_onchip_service_v1"
    assert manifest["cluster_count"] == 4
    assert manifest["packet_w"] == 256
    assert manifest["banks"] == 8
    assert manifest["arb_mode"] == "locality_first_bounded"
    assert manifest["shared_result_egress"] == "single_ready_valid_round_robin_v1"
    assert manifest["response_metadata_guard"] == "single_outstanding_per_cluster_v1"
    assert manifest["submodule_manifests"]["multivalue_cluster"]["result_beats_per_command"] == 16


def test_integrated_service_default_cases_cover_requested_surface() -> None:
    assert {row["cluster_count"] for row in DEFAULT_CASES} >= {1, 2, 4}
    assert {row["packet_w"] for row in DEFAULT_CASES} == {128, 256}
    assert {row["banks"] for row in DEFAULT_CASES} >= {2, 4, 8}
    assert {row["arb_mode"] for row in DEFAULT_CASES} == {"round_robin", "locality_first_bounded"}


@pytest.mark.parametrize("packet_w", [128, 256])
def test_integrated_service_zero_contention_exact(packet_w: int) -> None:
    if not _iverilog_available():
        pytest.skip("iverilog/vvp unavailable")
    report = build_report(
        {
            "cases": [
                _case(
                    case_id=f"zero_{packet_w}",
                    cluster_count=1,
                    packet_w=packet_w,
                    banks=2 if packet_w == 128 else 8,
                    arb_mode="round_robin" if packet_w == 128 else "locality_first_bounded",
                    locality_burst_max=2 if packet_w == 128 else 3,
                    read_latency=1 if packet_w == 128 else 3,
                    req_queue_depth=2,
                    resp_queue_depth=2,
                    bank_queue_depth=2 if packet_w == 128 else 3,
                )
            ]
        }
    )
    case = report["cases"][0]
    assert report["decision"] == "pass"
    assert case["decision"] == "pass"
    assert case["integrated_service"]["exact_match"] is True
    assert case["integrated_service"]["no_protocol_errors"] is True
    assert case["integrated_service"]["cycle_bound_ok"] is True
    assert case["integrated_service"]["service_penalty_cycles"] >= 0
    assert case["integrated_service"]["result_count"] == 16
    assert case["integrated_service"]["request_count"] == 48
    assert case["integrated_service"]["wide_response_count"] == 48
    assert case["integrated_service"]["counters"]["bank_conflict_count"] == 0
    assert case["integrated_service"]["counters"]["shared_result"]["egress_block_cycles"] >= 0
    assert case["baseline_no_stall"]["score_hash"] == case["expected_hashes"]["score_hash"]
    assert case["baseline_no_stall"]["final_hash"] == case["expected_hashes"]["final_hash"]
    assert case["integrated_service"]["final_hash"] == case["expected_hashes"]["final_hash"]


@pytest.mark.parametrize(
    ("packet_w", "banks", "arb_mode", "locality_burst_max", "cluster_count"),
    [
        (128, 2, "round_robin", 2, 2),
        (256, 8, "locality_first_bounded", 3, 4),
    ],
)
def test_integrated_service_same_bank_contention_exact(
    packet_w: int,
    banks: int,
    arb_mode: str,
    locality_burst_max: int,
    cluster_count: int,
) -> None:
    if not _iverilog_available():
        pytest.skip("iverilog/vvp unavailable")
    report = build_report(
        {
            "cases": [
                _case(
                    case_id=f"contended_{packet_w}",
                    cluster_count=cluster_count,
                    packet_w=packet_w,
                    banks=banks,
                    arb_mode=arb_mode,
                    locality_burst_max=locality_burst_max,
                    req_queue_depth=2 if packet_w == 128 else 3,
                    resp_queue_depth=2,
                    bank_queue_depth=2 if packet_w == 128 else 3,
                    read_latency=2 if packet_w == 128 else 3,
                )
            ]
        }
    )
    case = report["cases"][0]
    assert report["decision"] == "pass"
    assert case["integrated_service"]["exact_match"] is True
    assert case["integrated_service"]["no_protocol_errors"] is True
    assert case["integrated_service"]["no_drop_duplicate_deadlock_timeout"] is True
    assert case["integrated_service"]["service_penalty_cycles"] >= 0
    assert case["integrated_service"]["counters"]["bank_conflict_count"] > 0
    assert case["integrated_service"]["counters"]["arbitration_contention_cycles"] > 0
    assert case["integrated_service"]["counters"]["shared_result"]["arbitration_contention_cycles"] >= 0
    assert case["integrated_service"]["counters"]["request_injection_stall_cycles"] >= 0
    assert case["integrated_service"]["service_counts"]["accepted_req_count"] == 48 * cluster_count
    assert case["integrated_service"]["service_counts"]["emitted_resp_count"] == 48 * cluster_count
    assert case["integrated_service"]["request_hash"] == case["expected_hashes"]["request_hash"]
    assert (
        case["integrated_service"]["wide_response_matrix_hash"]
        == case["expected_hashes"]["wide_response_matrix_hash"]
    )
    assert case["integrated_service"]["final_hash"] == case["expected_hashes"]["final_hash"]


def test_integrated_service_fixed_resource_scaling_pair() -> None:
    if not _iverilog_available():
        pytest.skip("iverilog/vvp unavailable")
    report = build_report(
        {
            "cases": [
                _case(
                    case_id="fixed_c1",
                    cluster_count=1,
                    packet_w=128,
                    banks=2,
                    arb_mode="round_robin",
                    locality_burst_max=2,
                    req_queue_depth=2,
                    resp_queue_depth=2,
                    bank_queue_depth=2,
                    read_latency=2,
                ),
                _case(
                    case_id="fixed_c2",
                    cluster_count=2,
                    packet_w=128,
                    banks=2,
                    arb_mode="round_robin",
                    locality_burst_max=2,
                    req_queue_depth=2,
                    resp_queue_depth=2,
                    bank_queue_depth=2,
                    read_latency=2,
                ),
            ]
        }
    )
    c1, c2 = report["cases"]
    assert report["decision"] == "pass"
    assert c1["config"]["packet_w"] == c2["config"]["packet_w"] == 128
    assert c1["config"]["banks"] == c2["config"]["banks"] == 2
    assert c1["config"]["req_queue_depth"] == c2["config"]["req_queue_depth"] == 2
    assert c1["config"]["resp_queue_depth"] == c2["config"]["resp_queue_depth"] == 2
    assert c1["config"]["bank_queue_depth"] == c2["config"]["bank_queue_depth"] == 2
    assert c1["config"]["read_latency"] == c2["config"]["read_latency"] == 2
    assert c1["config"]["arb_mode"] == c2["config"]["arb_mode"] == "round_robin"
    assert c2["integrated_service"]["completion_cycle"] >= c1["integrated_service"]["completion_cycle"]
    assert c2["integrated_service"]["service_penalty_cycles"] >= c1["integrated_service"]["service_penalty_cycles"]


def test_integrated_service_validate_report_rejects_incomplete_evidence() -> None:
    if not _iverilog_available():
        pytest.skip("iverilog/vvp unavailable")
    report = build_report({"cases": [_case(case_id="validate", cluster_count=1, packet_w=128, banks=2, arb_mode="round_robin")]})
    broken = json.loads(json.dumps(report))
    broken["exclusions"] = REPORT_EXCLUSIONS[:-1]
    with pytest.raises(ValueError, match="exclusions"):
        validate_report(broken)

    broken = json.loads(json.dumps(report))
    del broken["cases"][0]["integrated_service"]["counters"]["max_occupancy"]
    with pytest.raises(ValueError, match="incomplete counters"):
        validate_report(broken)

    broken = json.loads(json.dumps(report))
    broken["cases"][0]["integrated_service"]["service_penalty_cycles"] = -1
    with pytest.raises(ValueError, match="negative service penalty"):
        validate_report(broken)
