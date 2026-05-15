from npu.eval.estimate_llm_decoder_output_projection_integrated_breakdown import build_report


def _producer_rows():
    return [
        {
            "scope": "aggregate",
            "arch_id": "fp16_nm1",
            "macro_mode": "flat_nomacro",
            "critical_path_ns_mean": "5.5",
            "die_area_um2_mean": "1000",
            "total_power_mw_mean": "0.10",
            "latency_ms_mean": "0.01",
            "energy_mj_mean": "0.001",
            "flow_elapsed_s_mean": "10",
        },
        {
            "scope": "aggregate",
            "arch_id": "fp16_nm2",
            "macro_mode": "flat_nomacro",
            "critical_path_ns_mean": "5.7",
            "die_area_um2_mean": "2000",
            "total_power_mw_mean": "0.20",
            "latency_ms_mean": "0.02",
            "energy_mj_mean": "0.002",
            "flow_elapsed_s_mean": "20",
        },
    ]


def _ranker_payload():
    return {
        "decision": {"decision": "output_projection_ranker_wrapper_physical_measured"},
        "variants": [
            {
                "producer_lanes": 64,
                "metrics_row": {
                    "status": "ok",
                    "critical_path_ns": "4.4",
                    "die_area": "100",
                    "total_power_mw": "0.01",
                },
                "simulations": {
                    "serial": {"observed": {"final_cycle": 1987}},
                    "ranktree": {"observed": {"final_cycle": 35}},
                },
            },
            {
                "producer_lanes": 128,
                "metrics_row": {
                    "status": "ok",
                    "critical_path_ns": "4.5",
                    "die_area": "240",
                    "total_power_mw": "0.03",
                },
                "simulations": {
                    "serial": {"observed": {"final_cycle": 1987}},
                    "ranktree": {"observed": {"final_cycle": 20}},
                },
            },
        ],
    }


def _policy_payload():
    return {
        "decision": {"decision": "output_projection_ranker_policy_promoted"},
        "policy_rows": [
            {
                "selected_path": "serial_lpc1",
                "producer": {"producer_lanes": 64, "producer_ii_cycles": 512},
            },
            {
                "selected_path": "single_r64_ranktree",
                "producer": {"producer_lanes": 128, "producer_ii_cycles": 128},
            },
        ],
    }


def test_build_report_passes_for_additive_low_overhead() -> None:
    report = build_report(
        producer_rows=_producer_rows(),
        wrapper_physical=_ranker_payload(),
        policy=_policy_payload(),
        lane_map={"fp16_nm1": 64, "fp16_nm2": 128},
        source_refs={},
    )

    assert report["decision"]["decision"] == "producer_output_ranker_integration_accounting_passed"
    assert report["summary"]["ok_integrations"] == 2
    assert report["integrations"][0]["integrated_accounting"]["timing_bottleneck"] == "producer"
    assert report["integrations"][1]["ranker_wrapper"]["ranktree_final_cycle"] == 20
    assert report["summary"]["max_ranker_area_over_producer"] == 0.12


def test_build_report_flags_missing_lane_mapping() -> None:
    report = build_report(
        producer_rows=_producer_rows(),
        wrapper_physical=_ranker_payload(),
        policy=_policy_payload(),
        lane_map={"fp16_nm1": 64},
        source_refs={},
    )

    assert report["decision"]["decision"] == "producer_output_ranker_integration_needs_refinement"
    assert report["integrations"][1]["status"] == "missing_ranker_lane_mapping"
