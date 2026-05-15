from npu.eval.probe_llm_decoder_output_projection_weight_store_interface import (
    _perf_reference,
    build_report,
    build_scenarios,
)


def _feasibility() -> dict:
    return {
        "decision": {"decision": "weight_store_area_budget_feasible"},
        "shape_summaries": [
            {
                "label": "toy",
                "best_area_budget_feasible": {
                    "required_banks": 12,
                    "bank_read_width_bits": 512,
                    "read_ports_per_bank": 2,
                },
            }
        ],
    }


def test_weight_store_interface_builds_bounded_scenarios() -> None:
    scenarios = build_scenarios(
        _feasibility(),
        max_representative_banks=8,
        read_latency_cycles=[1, 2],
        request_count=4,
        address_stride=3,
    )

    assert [scenario.read_latency_cycles for scenario in scenarios] == [1, 2]
    assert scenarios[0].full_required_banks == 12
    assert scenarios[0].representative_banks == 8
    assert scenarios[0].bank_read_width_bits == 512


def test_weight_store_interface_perf_reference_checksum() -> None:
    scenario = build_scenarios(
        _feasibility(),
        max_representative_banks=2,
        read_latency_cycles=[1],
        request_count=2,
        address_stride=1,
    )[0]

    reference = _perf_reference(scenario)

    assert reference["accepted"] == 2
    assert reference["responses"] == 2
    assert reference["checksum"] == 656


def test_weight_store_interface_report_blocks_without_simulator() -> None:
    scenarios = build_scenarios(
        _feasibility(),
        max_representative_banks=4,
        read_latency_cycles=[1],
        request_count=2,
        address_stride=1,
    )

    report = build_report(feasibility=_feasibility(), scenarios=scenarios, iverilog=None, vvp=None)

    assert report["summary"]["scenario_count"] == 1
    assert report["summary"]["passed_count"] == 0
    assert report["interface_rows"][0]["rtl_sim"]["status"] == "simulator_missing"
    assert report["decision"]["decision"] == "weight_store_interface_contract_blocked"
