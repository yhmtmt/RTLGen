from pathlib import Path

from npu.eval.probe_llm_decoder_output_projection_ranker_wrapper_contract import (
    _banked_r64_reference,
    build_report,
)


def _policy() -> dict:
    return {
        "decision": {"decision": "output_projection_ranker_policy_promoted"},
        "policy": {"serial_lpc1_min_ii_cycles": 384},
        "policy_rows": [
            {
                "selected_path": "serial_lpc1",
                "producer": {"producer_lanes": 64, "producer_ii_cycles": 384},
                "coverage_status": "covered",
            },
            {
                "selected_path": "single_r64_ranktree",
                "producer": {"producer_lanes": 64, "producer_ii_cycles": 6},
                "coverage_status": "covered",
            },
            {
                "selected_path": "banked_r64_ranktrees",
                "producer": {"producer_lanes": 128, "producer_ii_cycles": 3},
                "coverage_status": "covered",
            },
        ],
    }


def _serial_wrapper() -> dict:
    return {
        "selected_variant": {"top": "missing", "design_dir": "missing", "lanes_per_cycle": 1},
    }


def _ranktree_promotion() -> dict:
    return {
        "selected_ranktree_variant": {
            "simulation": {
                "status": "ok",
                "expected": {"token": 5, "logit": 500},
                "log_tail": ["RESULT token=5 logit=500 accepted=3 stalls=0 fifo_max=1 final_cycle=10"],
            }
        },
        "producer_modes": [
            {"mode": "single_r64_ranktree", "consumer_ii_cycles": 1, "ranker_instances": 1},
            {"mode": "banked_r64_ranktrees", "consumer_ii_cycles": 1, "ranker_instances": 2},
        ],
    }


def test_banked_r64_reference_matches_full_r128_reference() -> None:
    result = _banked_r64_reference(producer_lanes=128, num_tiles=6)

    assert result["equivalent"] is True
    assert result["banked_reference"] == result["full_reference"]
    assert len(result["bank_results"]) == 2


def test_wrapper_contract_blocks_when_serial_rtl_cannot_run() -> None:
    report = build_report(
        policy=_policy(),
        serial_wrapper=_serial_wrapper(),
        ranktree_promotion=_ranktree_promotion(),
        merge_config=Path("missing.json"),
        rtlgen_binary=None,
        num_tiles=6,
    )

    assert report["decision"]["decision"] == "output_projection_ranker_wrapper_contract_blocked"
    assert report["representative_cases"][0]["case"] == "streaming_serial_lpc1_r64"
    assert report["representative_cases"][0]["passed"] is False
    assert report["representative_cases"][1]["passed"] is True
    assert report["representative_cases"][2]["passed"] is True


def test_wrapper_contract_blocks_without_promoted_policy() -> None:
    policy = _policy()
    policy["decision"] = {"decision": "output_projection_ranker_policy_blocked"}

    report = build_report(
        policy=policy,
        serial_wrapper=_serial_wrapper(),
        ranktree_promotion=_ranktree_promotion(),
        merge_config=Path("missing.json"),
        rtlgen_binary=None,
        num_tiles=6,
    )

    assert report["decision"]["decision"] == "output_projection_ranker_wrapper_contract_blocked"
    assert report["checks"][0]["name"] == "ranker_policy_promoted"
    assert report["checks"][0]["passed"] is False
