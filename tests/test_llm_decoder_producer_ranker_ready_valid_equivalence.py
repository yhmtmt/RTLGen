from npu.eval.probe_llm_decoder_producer_ranker_ready_valid_equivalence import build_report


def test_ready_valid_equivalence_report_requires_r64_k1_and_rtl_match() -> None:
    producer_config = {
        "compute": {"gemm": {"mac_type": "fp16", "num_modules": 16, "lanes_per_module": 1}}
    }
    logit_rank_config = {
        "operations": [
            {
                "type": "logit_rank",
                "module_name": "logit_rank_r64_l16_k1",
                "options": {"row_elems": 64, "logit_bits": 16, "top_k": 1},
            }
        ]
    }
    merge_config = {
        "operations": [
            {
                "type": "candidate_stream_merge_fifo",
                "module_name": "candidate_stream_merge_fifo_k1_l16_t16_d16",
                "options": {
                    "top_k": 1,
                    "logit_bits": 16,
                    "token_id_bits": 16,
                    "fifo_depth_groups": 16,
                },
            }
        ]
    }
    rtl_sim = {
        "status": "ok",
        "expected": {"token": 5, "logit": 500},
        "observed": {"token": 5, "logit": 500, "accepted": 3},
    }

    report = build_report(
        producer_config=producer_config,
        logit_rank_config=logit_rank_config,
        merge_config=merge_config,
        integration_plan={"recommendation": {"next_target": {"name": "r64_k1_nm16_ready_valid_equivalence"}}},
        rtl_sim=rtl_sim,
    )

    assert report["target"]["producer_lanes"] == 64
    assert report["target"]["top_k"] == 1
    assert report["producer_config_summary"]["mac_lanes_per_cycle"] == 16
    assert report["decision"]["decision"] == "ready_valid_equivalence_passed"
