from npu.eval.probe_llm_decoder_output_projection_weight_fetch_wrapper import (
    build_report,
    build_scenarios,
    simulate_perf,
)


def _feasibility() -> dict:
    return {
        "decision": {"decision": "weight_store_area_budget_feasible"},
        "shape_summaries": [
            {
                "label": "toy",
                "best_area_budget_feasible": {
                    "required_banks": 4,
                    "bank_read_width_bits": 512,
                    "delivered_local_weight_cycles_per_tile": 3,
                    "target_local_weight_cycles_per_tile": 5,
                },
            }
        ],
    }


def test_weight_fetch_wrapper_builds_selected_and_stress_cadences() -> None:
    scenarios = build_scenarios(
        feasibility=_feasibility(),
        read_latency_cycles=[1],
        outstanding_depths=[1],
        request_count=4,
        address_stride=5,
    )

    assert [scenario.issue_interval_cycles for scenario in scenarios] == [1, 3, 5]
    assert scenarios[0].banks == 4
    assert scenarios[0].bank_read_width_bits == 512


def test_weight_fetch_wrapper_perf_model_accounts_for_stalls() -> None:
    scenario = build_scenarios(
        feasibility=_feasibility(),
        read_latency_cycles=[4],
        outstanding_depths=[1],
        request_count=4,
        address_stride=5,
    )[0]

    reference = simulate_perf(scenario)

    assert reference["accepted"] == 4
    assert reference["responses"] == 4
    assert reference["producer_stall_cycles"] > 0
    assert reference["final_cycle"] > 4


def test_weight_fetch_wrapper_report_blocks_without_simulator() -> None:
    scenarios = build_scenarios(
        feasibility=_feasibility(),
        read_latency_cycles=[1],
        outstanding_depths=[1],
        request_count=2,
        address_stride=1,
    )

    report = build_report(feasibility=_feasibility(), scenarios=scenarios, iverilog=None, vvp=None)

    assert report["summary"]["scenario_count"] == 3
    assert report["summary"]["passed_count"] == 0
    assert report["decision"]["decision"] == "weight_fetch_wrapper_contract_blocked"
