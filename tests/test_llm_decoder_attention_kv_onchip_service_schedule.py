from npu.eval import estimate_llm_decoder_attention_kv_onchip_service_schedule as onchip


def test_objective_key_breaks_latency_ties_with_power_area_then_precision() -> None:
    q8 = {
        "measured_l1_profile": "hd64_kv8_full_value_p8_ppc2_noc128_softmax_int8_q8",
        "latency_us": 10.0,
        "total_cycles": 100,
        "logic_power_mw": 5.0,
        "logic_area_used_um2": 1000.0,
    }
    q12 = {
        "measured_l1_profile": "hd64_kv8_full_value_p8_ppc2_noc128_softmax_int8_q12",
        "latency_us": 10.0,
        "total_cycles": 100,
        "logic_power_mw": 4.0,
        "logic_area_used_um2": 900.0,
    }
    same_ppa_higher_precision = {
        "measured_l1_profile": "hd64_kv8_full_value_p8_ppc2_noc128_softmax_int8_q10",
        "latency_us": 10.0,
        "total_cycles": 100,
        "logic_power_mw": 5.0,
        "logic_area_used_um2": 1000.0,
    }

    assert onchip._objective_key(q12) < onchip._objective_key(q8)
    assert onchip._objective_key(same_ppa_higher_precision) < onchip._objective_key(q8)
