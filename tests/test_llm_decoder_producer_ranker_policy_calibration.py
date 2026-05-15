from npu.eval.calibrate_llm_decoder_producer_ranker_policy_service import build_report


def _coupled_row(**overrides: object) -> dict:
    row = {
        "vocab_size": 50257,
        "hidden_size": 768,
        "producer_lanes": 64,
        "macs_per_cycle": 32768,
        "memory_bandwidth_bytes_per_cycle": 256,
        "producer_ii_cycles": 512,
        "producer_latency_us_per_token": 300.0,
        "ranker_latency_us_per_token": 1000.0,
        "coupled_latency_us_per_token": 1000.0,
        "ranker_candidate_memory_bytes": 1024,
    }
    row.update(overrides)
    return row


def _wrapper(*, lanes: int = 64) -> dict:
    return {
        "producer_lanes": lanes,
        "metrics_row": {"critical_path_ns": "2.0"},
        "simulations": {
            "serial": {"observed": {"final_cycle": 1000}},
            "ranktree": {"observed": {"final_cycle": 10}},
        },
    }


def test_calibration_replaces_old_ranker_latency_with_measured_serial_service() -> None:
    report = build_report(
        coupled_report={"model": "coupled", "coupled_ranker_sweep": [_coupled_row()]},
        wrapper_physical={
            "model": "wrapper",
            "decision": {"decision": "output_projection_ranker_wrapper_physical_measured"},
            "variants": [_wrapper()],
        },
        policy={
            "model": "policy",
            "decision": {"decision": "output_projection_ranker_policy_promoted"},
            "policy_rows": [],
        },
    )

    best = report["calibrated_best"]
    assert best["calibrated_selected_path"] == "threshold_serial_lpc1"
    assert best["calibrated_ranker_latency_us_per_token"] == 2.0
    assert best["calibrated_coupled_latency_us_per_token"] == 300.0
    assert best["calibrated_dominant_term"] == "producer"
    assert report["summary"]["old_to_calibrated_best_latency_speedup"] == 3.333333


def test_calibration_uses_exact_policy_ranktree_row_when_available() -> None:
    row = _coupled_row(producer_ii_cycles=128)
    policy_row = {
        "producer": {
            "vocab_size": 50257,
            "hidden_size": 768,
            "producer_lanes": 64,
            "macs_per_cycle": 32768,
            "memory_bandwidth_bytes_per_cycle": 256,
            "producer_ii_cycles": 128,
        },
        "selected_path": "resident_ranktree_r64",
    }
    report = build_report(
        coupled_report={"coupled_ranker_sweep": [row]},
        wrapper_physical={
            "decision": {"decision": "output_projection_ranker_wrapper_physical_measured"},
            "variants": [_wrapper()],
        },
        policy={
            "decision": {"decision": "output_projection_ranker_policy_promoted"},
            "policy_rows": [policy_row],
        },
    )

    best = report["calibrated_best"]
    assert best["policy_match"] is True
    assert best["calibrated_selected_path"] == "resident_ranktree_r64"
    assert best["calibrated_scenario"] == "ranktree"
    assert best["calibrated_ranker_latency_us_per_token"] == 0.02


def test_calibration_marks_rows_without_wrapper_measurements() -> None:
    report = build_report(
        coupled_report={"coupled_ranker_sweep": [_coupled_row(producer_lanes=128)]},
        wrapper_physical={
            "decision": {"decision": "output_projection_ranker_wrapper_physical_measured"},
            "variants": [_wrapper(lanes=64)],
        },
        policy={"decision": {"decision": "output_projection_ranker_policy_promoted"}, "policy_rows": []},
    )

    assert report["calibrated_coupled_ranker_sweep"][0]["status"] == "missing_wrapper_physical"
    assert report["checks"][2]["passed"] is False
    assert report["summary"]["missing_wrapper_physical_rows"] == 1
