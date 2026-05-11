from npu.eval.estimate_llm_decoder_stage_breakdown import build_report


def test_decoder_stage_breakdown_reports_attention_and_weight_models() -> None:
    report = build_report(
        sequence_length_list=[128, 8192],
        macs_per_cycle_list=[32768],
        memory_bandwidth_bytes_per_cycle_list=[256.0],
        clock_ns=1.0,
        weight_bits=16,
        activation_bits=16,
        ranker_lanes=64,
        ranker_ii_cycles=384,
    )

    rows = report["breakdown_sweep"]
    assert report["model"] == "llm_decoder_stage_breakdown_v1"
    assert {row["weight_residency"] for row in rows} == {"streaming_weights", "resident_weights"}
    assert {stage["stage"] for stage in rows[0]["stages"]} == {
        "attention",
        "mlp",
        "norm_residual",
        "output_projection",
        "ranker",
    }

    gpt2_long_resident = next(
        row
        for row in rows
        if row["label"] == "gpt2_small"
        and row["sequence_length"] == 8192
        and row["weight_residency"] == "resident_weights"
    )
    attention = next(stage for stage in gpt2_long_resident["stages"] if stage["stage"] == "attention")
    assert attention["kv_cache_bytes"] > attention["activation_bytes"]


def test_decoder_stage_breakdown_keeps_streamed_weights_visible() -> None:
    report = build_report(
        sequence_length_list=[128],
        macs_per_cycle_list=[32768],
        memory_bandwidth_bytes_per_cycle_list=[256.0],
        clock_ns=1.0,
        weight_bits=16,
        activation_bits=16,
        ranker_lanes=64,
        ranker_ii_cycles=384,
    )

    streamed = next(
        row
        for row in report["breakdown_sweep"]
        if row["label"] == "gpt2_small" and row["weight_residency"] == "streaming_weights"
    )
    resident = next(
        row
        for row in report["breakdown_sweep"]
        if row["label"] == "gpt2_small" and row["weight_residency"] == "resident_weights"
    )
    assert streamed["total_cycles"] > resident["total_cycles"]
    assert streamed["dominant_stage"] in {"mlp", "output_projection", "attention"}
