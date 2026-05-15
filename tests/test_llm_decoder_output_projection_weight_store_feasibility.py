from npu.eval.estimate_llm_decoder_output_projection_weight_store_feasibility import build_report


def _memory_hierarchy() -> dict:
    return {
        "model": "memory_hierarchy",
        "shape_summaries": [
            {
                "label": "toy",
                "sequence_length": 128,
                "hidden_size": 64,
                "vocab_size": 256,
                "baseline_producer_us": 0.2,
                "best_parallel": {
                    "producer_lanes": 64,
                    "macs_per_cycle": 4096,
                    "local_cache_bw_bytes_per_cycle": 1024.0,
                    "cache_capacity_mb": 1.0,
                    "effective_cache_hit_rate": 1.0,
                    "resident_weight_mb": 1.0,
                    "cache_weight_mb": 1.0,
                    "weight_bytes_per_tile": 4096,
                    "local_weight_cycles_per_tile": 4,
                    "producer_ii_cycles_parallel": 4,
                },
            }
        ],
    }


def test_weight_store_feasibility_satisfies_capacity_and_bandwidth() -> None:
    report = build_report(
        memory_hierarchy=_memory_hierarchy(),
        bank_capacity_mb_list=[0.5],
        bank_read_width_bits_list=[512],
        read_ports_per_bank_list=[1],
        area_budget_mm2_list=[100.0],
        bitcell_area_um2_per_bit=0.01,
        peripheral_area_overhead=0.0,
    )

    best = report["shape_summaries"][0]["best_area_budget_feasible"]
    assert best["capacity_banks"] == 2
    assert best["bandwidth_banks"] == 16
    assert best["required_banks"] == 16
    assert best["capacity_ok"] is True
    assert best["bandwidth_ok"] is True
    assert best["area_budget_ok"] is True
    assert report["decision"]["decision"] == "weight_store_area_budget_feasible"


def test_weight_store_feasibility_reports_area_unbounded_when_budget_fails() -> None:
    report = build_report(
        memory_hierarchy=_memory_hierarchy(),
        bank_capacity_mb_list=[1.0],
        bank_read_width_bits_list=[8192],
        read_ports_per_bank_list=[1],
        area_budget_mm2_list=[0.001],
        bitcell_area_um2_per_bit=0.2,
        peripheral_area_overhead=0.35,
    )

    summary = report["shape_summaries"][0]
    assert summary["best_area_budget_feasible"] is None
    assert summary["best_capacity_bandwidth"]["capacity_ok"] is True
    assert summary["best_capacity_bandwidth"]["bandwidth_ok"] is True
    assert report["decision"]["decision"] == "weight_store_capacity_bandwidth_feasible_area_unbounded"
