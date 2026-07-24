import hashlib
import json
from pathlib import Path
import shutil
import sys

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import npu.eval.probe_attention_decode_score_multivalue_integrated_service as probe_module
from npu.eval.probe_attention_decode_score_multivalue_integrated_service import (
    COMPACT_REPORT_MAX_BYTES,
    COMPACT_REPORT_MAX_LINES,
    DEFAULT_CASES,
    REPORT_EXCLUSIONS,
    _selected_scale_point,
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
    assert manifest["shared_result_egress"] == "single_ready_valid_round_robin_hold_reg_v2"
    assert manifest["shared_result_egress_initiation_interval"] == 1
    assert manifest["shared_result_egress_stall_semantics"] == "stable_until_handshake"
    assert manifest["response_metadata_guard"] == "single_outstanding_per_cluster_v1"
    assert manifest["submodule_manifests"]["multivalue_cluster"]["result_beats_per_command"] == 16


def test_integrated_service_default_cases_cover_requested_surface() -> None:
    assert len(DEFAULT_CASES) == 14
    assert {row["cluster_count"] for row in DEFAULT_CASES} >= {1, 2, 4, 8, 16, 32}
    assert {row["packet_w"] for row in DEFAULT_CASES} == {128, 256}
    assert {row["banks"] for row in DEFAULT_CASES} >= {4, 8, 16, 32}
    assert {row["arb_mode"] for row in DEFAULT_CASES} == {"round_robin", "locality_first_bounded"}
    fixed_resource = {
        row["case_id"]
        for row in DEFAULT_CASES
        if row["packet_w"] == 128 and row["banks"] == 4 and row["arb_mode"] == "round_robin"
    }
    assert fixed_resource == {
        "c1_p128_b4_rr",
        "c2_p128_b4_rr",
        "c4_p128_b4_rr",
        "c8_p128_b4_rr",
        "c16_p128_b4_rr",
        "c32_p128_b4_rr",
    }
    assert {"c32_p256_b32_q1_rr", "c32_p256_b32_rl6_rr"} <= {
        row["case_id"] for row in DEFAULT_CASES
    }


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
    assert case["integrated_service"]["shared_result_egress"]["documented_initiation_interval"] == 1
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
    assert case["integrated_service"]["counters"]["shared_result"]["egress_block_cycles"] > 0
    assert case["integrated_service"]["shared_result_egress"]["documented_initiation_interval"] == 1
    assert case["integrated_service"]["shared_result_egress"]["back_to_back_fire_seen"] is True
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
                    banks=4,
                    arb_mode="round_robin",
                    locality_burst_max=2,
                    req_queue_depth=4,
                    resp_queue_depth=4,
                    bank_queue_depth=4,
                    read_latency=2,
                ),
                _case(
                    case_id="fixed_c2",
                    cluster_count=2,
                    packet_w=128,
                    banks=4,
                    arb_mode="round_robin",
                    locality_burst_max=2,
                    req_queue_depth=4,
                    resp_queue_depth=4,
                    bank_queue_depth=4,
                    read_latency=2,
                ),
            ]
        }
    )
    c1, c2 = report["cases"]
    assert report["decision"] == "pass"
    assert c1["config"]["packet_w"] == c2["config"]["packet_w"] == 128
    assert c1["config"]["banks"] == c2["config"]["banks"] == 4
    assert c1["config"]["req_queue_depth"] == c2["config"]["req_queue_depth"] == 4
    assert c1["config"]["resp_queue_depth"] == c2["config"]["resp_queue_depth"] == 4
    assert c1["config"]["bank_queue_depth"] == c2["config"]["bank_queue_depth"] == 4
    assert c1["config"]["read_latency"] == c2["config"]["read_latency"] == 2
    assert c1["config"]["arb_mode"] == c2["config"]["arb_mode"] == "round_robin"
    assert c2["integrated_service"]["completion_cycle"] >= c1["integrated_service"]["completion_cycle"]
    assert c2["integrated_service"]["service_penalty_cycles"] >= c1["integrated_service"]["service_penalty_cycles"]
    assert c2["integrated_service"]["counters"]["shared_result"]["egress_block_cycles"] > 0
    assert c2["integrated_service"]["shared_result_egress"]["back_to_back_fire_seen"] is True


def test_integrated_service_report_retains_linkage_and_summary() -> None:
    if not _iverilog_available():
        pytest.skip("iverilog/vvp unavailable")
    report = build_report(
        {"cases": [_case(case_id="linkage", cluster_count=2, packet_w=128, banks=4, arb_mode="round_robin")]},
        proposal_id="prop_l2_decoder_attention_decode_score_multivalue_integrated_service_llama7b_v1",
        proposal_path=(
            "docs/proposals/prop_l2_decoder_attention_decode_score_multivalue_integrated_service_llama7b_v1/proposal.json"
        ),
        depends_on_item_ids=["l2_decoder_attention_decode_score_multivalue_cluster_equivalence_llama7b_v1"],
    )
    assert report["model"] == "llm_decoder_attention_decode_score_multivalue_integrated_service_probe_v1"
    assert report["source_links"]["proposal_id"] == (
        "prop_l2_decoder_attention_decode_score_multivalue_integrated_service_llama7b_v1"
    )
    assert report["source_links"]["proposal_path"].endswith("/proposal.json")
    assert report["source_links"]["depends_on_item_ids"] == [
        "l2_decoder_attention_decode_score_multivalue_cluster_equivalence_llama7b_v1"
    ]
    assert report["summary"]["validated_case_count"] == 1
    assert report["summary"]["all_hash_gates_passed"] is True
    assert report["summary"]["all_protocol_gates_passed"] is True
    assert report["summary"]["all_count_gates_passed"] is True
    assert report["selected_scale_point"]["arch_id"] == "decode_score_multivalue_integrated_service"
    assert report["selected_scale_point"]["case_id"] == "linkage"
    assert "not a performance or architectural ranking" in report["selected_scale_point"]["selection_basis"]
    assert report["report_contract"]["shape"] == "deduplicated_shared_artifact_identities_v1"
    assert report["source_identities"]["generated_artifacts"]["shared_preload"]["entry_count"] == 48
    case = report["cases"][0]
    assert "generated_manifests" not in case
    assert "preload" not in case
    assert set(case["source_refs"]) == {
        "shared_preload",
        "baseline_manifest",
        "integrated_manifest",
        "baseline_top",
        "integrated_top",
    }


def test_integrated_service_report_compact_size_gate_with_large_manifests(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _baseline_manifest(case: dict) -> dict:
        return {
            "semantic_profile": "decode_m1x8_multivalue_cluster_equivalence_v1",
            "cluster_count": int(case["cluster_count"]),
            "result_beats_per_command": 16,
            "debug_payload": "b" * 8192,
        }

    def _integrated_manifest(case: dict) -> dict:
        return {
            "semantic_profile": "decode_m1x8_shared_score_16x8d_value_iterdiv_onchip_service_v1",
            "cluster_count": int(case["cluster_count"]),
            "packet_w": int(case["packet_w"]),
            "banks": int(case["banks"]),
            "arb_mode": str(case["arb_mode"]),
            "shared_result_egress": "single_ready_valid_round_robin_hold_reg_v2",
            "shared_result_egress_initiation_interval": 1,
            "shared_result_egress_stall_semantics": "stable_until_handshake",
            "response_metadata_guard": "single_outstanding_per_cluster_v1",
            "submodule_manifests": {
                "multivalue_cluster": {
                    "result_beats_per_command": 16,
                }
            },
            "debug_payload": "i" * 8192,
        }

    def _fake_baseline(case: dict, expected_clusters: list[dict], values: list[list[list[list[int]]]]) -> dict:
        del values
        score_rows = [
            {"cluster": cluster, "addr": addr, "row": rows}
            for cluster, payload in enumerate(expected_clusters)
            for addr, rows in enumerate(payload["score_rows"])
        ]
        results = [
            {
                **row,
                "cycle": 80 + row["slice"],
                "protocol_error": False,
            }
            for payload in expected_clusters
            for row in payload["results"]
        ]
        cluster_count = int(case["cluster_count"])
        done_rows = {
            cluster: {
                "cycle": 100 + cluster,
                "accepted": 48,
                "completed": 16,
            }
            for cluster in range(cluster_count)
        }
        top_sha256 = hashlib.sha256(f"baseline:{cluster_count}".encode()).hexdigest()
        return {
            "score_rows": score_rows,
            "results": results,
            "done_rows": done_rows,
            "completion_cycle": 180 + cluster_count,
            "protocol_error": False,
            "manifest": _baseline_manifest(case),
            "top_sha256": top_sha256,
        }

    def _fake_integrated(case: dict, values: list[list[list[list[int]]]]) -> dict:
        cluster_count = int(case["cluster_count"])
        expected_clusters = [
            probe_module._cluster_expected(cluster, values)
            for cluster in range(cluster_count)
        ]
        score_rows = [
            {"cluster": cluster, "addr": addr, "row": rows}
            for cluster, payload in enumerate(expected_clusters)
            for addr, rows in enumerate(payload["score_rows"])
        ]
        request_rows = [
            {
                **row,
                "cycle": 20 + row["tag"],
            }
            for payload in expected_clusters
            for row in payload["request_records"]
        ]
        wide_rows = [
            {
                **row,
                "cycle": 40 + row["tag"],
                "protocol_error": False,
            }
            for payload in expected_clusters
            for row in payload["response_records"]
        ]
        results = [
            {
                **row,
                "cycle": 220 + row["slice"],
                "protocol_error": False,
            }
            for payload in expected_clusters
            for row in payload["results"]
        ]
        done_rows = {
            cluster: {
                "cycle": 240 + cluster,
                "accepted": 48,
                "completed": 16,
            }
            for cluster in range(cluster_count)
        }
        counter_rows = {
            cluster: {
                "input_stall_cycles": cluster,
                "input_starvation_cycles": 0,
                "result_egress_block_cycles": max(cluster_count - 1, 0),
                "request_count": 48,
                "wide_response_count": 48,
            }
            for cluster in range(cluster_count)
        }
        top_sha256 = hashlib.sha256(
            f"integrated:{json.dumps(case, sort_keys=True)}".encode()
        ).hexdigest()
        return {
            "score_rows": score_rows,
            "request_rows": request_rows,
            "wide_rows": wide_rows,
            "results": results,
            "done_rows": done_rows,
            "counter_rows": counter_rows,
            "shared": {
                "completion_cycle": 260 + cluster_count,
                "protocol_error": False,
                "router_injection_stall_cycles": cluster_count,
                "router_arbitration_contention_cycles": max(cluster_count - 1, 0),
                "router_response_block_cycles": cluster_count // 2,
                "router_req_current_occupancy": 0,
                "router_req_max_occupancy": min(cluster_count, int(case["req_queue_depth"]) + 1),
                "router_resp_current_occupancy": 0,
                "router_resp_max_occupancy": min(cluster_count, int(case["resp_queue_depth"]) + 1),
                "service_accepted_req_count": 48 * cluster_count,
                "service_emitted_resp_count": 48 * cluster_count,
                "service_bank_conflict_count": max(cluster_count - 1, 0),
                "service_response_block_cycles": cluster_count // 2,
                "service_req_current_occupancy": 0,
                "service_req_max_occupancy": min(cluster_count, int(case["bank_queue_depth"]) + 1),
                "service_resp_current_occupancy": 0,
                "service_resp_max_occupancy": min(cluster_count, int(case["resp_queue_depth"]) + 1),
                "result_arbitration_contention_cycles": max(cluster_count - 1, 0),
                "result_egress_block_cycles": max(cluster_count - 1, 0),
                "result_back_to_back_fire_seen": True,
            },
            "manifest": _integrated_manifest(case),
            "top_sha256": top_sha256,
        }

    monkeypatch.setattr(probe_module, "_run_baseline", _fake_baseline)
    monkeypatch.setattr(probe_module, "_run_integrated", _fake_integrated)

    report = build_report()
    rendered = json.dumps(report, indent=2, sort_keys=True)

    assert len(rendered.encode()) <= COMPACT_REPORT_MAX_BYTES
    assert len(rendered.splitlines()) <= COMPACT_REPORT_MAX_LINES
    assert "preload_entries" not in report
    assert "debug_payload" not in rendered
    assert all("generated_manifests" not in case for case in report["cases"])
    assert all("preload" not in case for case in report["cases"])
    assert report["source_identities"]["generated_artifacts"]["shared_preload"]["payload_elided"] is True
    assert all(
        row["result_beats_per_command"] == 16
        for row in report["source_identities"]["generated_artifacts"]["generated_manifests"]
    )


def test_integrated_service_selected_scale_point_is_nominal_not_worst_penalty() -> None:
    reports = [
        {
            "case_id": "c32_nominal_rr",
            "config": {
                "cluster_count": 32,
                "packet_w": 256,
                "banks": 32,
                "req_queue_depth": 4,
                "resp_queue_depth": 4,
                "bank_queue_depth": 4,
                "read_latency": 2,
                "arb_mode": "round_robin",
            },
            "integrated_service": {
                "completion_cycle": 100,
                "service_penalty_cycles": 10,
                "counters": {
                    "shared_result": {"egress_block_cycles": 3},
                    "arbitration_contention_cycles": 4,
                    "bank_conflict_count": 5,
                },
            },
        },
        {
            "case_id": "c32_stress_q1",
            "config": {
                "cluster_count": 32,
                "packet_w": 256,
                "banks": 32,
                "req_queue_depth": 1,
                "resp_queue_depth": 1,
                "bank_queue_depth": 1,
                "read_latency": 2,
                "arb_mode": "round_robin",
            },
            "integrated_service": {
                "completion_cycle": 900,
                "service_penalty_cycles": 800,
                "counters": {
                    "shared_result": {"egress_block_cycles": 30},
                    "arbitration_contention_cycles": 40,
                    "bank_conflict_count": 50,
                },
            },
        },
    ]
    selected = _selected_scale_point(reports)
    assert selected["case_id"] == "c32_nominal_rr"
    assert selected["service_penalty_cycles"] == 10
    assert selected["selection_role"] == "representative_largest_nominal_scale_point"


def test_integrated_service_validate_report_rejects_incomplete_evidence() -> None:
    if not _iverilog_available():
        pytest.skip("iverilog/vvp unavailable")
    report = build_report(
        {"cases": [_case(case_id="validate", cluster_count=2, packet_w=128, banks=2, arb_mode="round_robin")]}
    )
    broken = json.loads(json.dumps(report))
    broken["decision"] = "fail"
    with pytest.raises(ValueError, match="decision must be pass"):
        validate_report(broken)

    broken = json.loads(json.dumps(report))
    broken["diagnosis"]["decision"] = "multivalue_integrated_service_probe_failed"
    with pytest.raises(ValueError, match="diagnosis must record a passed probe"):
        validate_report(broken)

    broken = json.loads(json.dumps(report))
    broken["summary"]["all_hash_gates_passed"] = False
    with pytest.raises(ValueError, match="summary must record all report gates as passed"):
        validate_report(broken)

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

    broken = json.loads(json.dumps(report))
    broken["cases"][0]["integrated_service"]["shared_result_egress"]["documented_initiation_interval"] = 2
    with pytest.raises(ValueError, match="shared_result egress II"):
        validate_report(broken)

    broken = json.loads(json.dumps(report))
    broken["cases"][0]["integrated_service"]["shared_result_egress"]["back_to_back_fire_seen"] = False
    with pytest.raises(ValueError, match="back-to-back evidence"):
        validate_report(broken)

    broken = json.loads(json.dumps(report))
    broken["preload_entries"] = []
    with pytest.raises(ValueError, match="elide preload payloads"):
        validate_report(broken)

    broken = json.loads(json.dumps(report))
    broken["source_identities"]["generated_artifacts"]["generated_manifests"][0]["result_beats_per_command"] = 0
    with pytest.raises(ValueError, match="finite positive result_beats_per_command"):
        validate_report(broken)

    broken = json.loads(json.dumps(report))
    broken["debug_payload"] = "x" * COMPACT_REPORT_MAX_BYTES
    with pytest.raises(ValueError, match="compact size gate"):
        validate_report(broken)
