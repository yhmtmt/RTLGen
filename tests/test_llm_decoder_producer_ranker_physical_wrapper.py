from npu.eval.probe_llm_decoder_producer_ranker_physical_wrapper import build_report


def test_physical_wrapper_report_requires_equivalence_materialization_and_metrics() -> None:
    report = build_report(
        ready_valid_equivalence={"decision": {"decision": "ready_valid_equivalence_passed"}},
        materialization={
            "status": "ok",
            "target": {"producer_lanes": 64, "top_k": 1, "logit_bits": 16, "token_id_bits": 16},
            "generated_verilog": [
                "runs/designs/activations/decoder_r64_k1_producer_ranker_physical_wrapper/verilog/decoder_r64_k1_producer_ranker_physical_wrapper.v"
            ],
        },
        synthesis={"status": "ok"},
        metrics_row={
            "status": "ok",
            "critical_path_ns": "6.2",
            "die_area": "810000",
            "total_power_mw": "0.12",
        },
        sweep="runs/campaigns/npu/decoder_producer_ranker_physical_wrapper/sweeps/nangate45_r64_k1_macro.json",
        make_target="3_3_place_gp",
    )

    assert report["target"]["producer_lanes"] == 64
    assert report["target"]["top_k"] == 1
    assert report["reference"]["full_vocab_top1"] == {"token": 5, "logit": 500}
    assert report["decision"]["decision"] == "producer_ranker_physical_wrapper_measured"


def test_physical_wrapper_blocks_without_predecessor_equivalence() -> None:
    report = build_report(
        ready_valid_equivalence={"decision": {"decision": "ready_valid_equivalence_blocked"}},
        materialization={
            "status": "ok",
            "target": {"producer_lanes": 64, "top_k": 1, "logit_bits": 16, "token_id_bits": 16},
            "generated_verilog": [],
        },
        synthesis={"status": "ok"},
        metrics_row={"status": "ok"},
        sweep="sweep.json",
        make_target="3_3_place_gp",
    )

    assert report["decision"]["decision"] == "producer_ranker_physical_wrapper_blocked"
