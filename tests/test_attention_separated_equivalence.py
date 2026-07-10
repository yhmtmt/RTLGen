from npu.eval.probe_attention_separated_equivalence import build_report
from npu.eval.evaluate_llm_decoder_model_native_mixed_int8_attention import _exp_lut_div_softmax
from npu.sim.perf.attention_separated import default_commands, exact_reference, simulate


def test_attention_separated_reference_is_deterministic_and_semantic() -> None:
    command = default_commands(1)[0]
    first = exact_reference(command)
    second = exact_reference(command)

    assert first == second
    assert len(first["consumer"]["score_row"]) == 8
    assert len(first["consumer"]["weights"]) == 8
    assert len(first["consumer"]["value"]) == 8
    assert sum(first["consumer"]["weights"]) in range(65531, 65540)


def test_attention_separated_softmax_matches_quality_model_profile() -> None:
    reference = exact_reference(default_commands(1)[0])["consumer"]
    logits = [score / float(1 << 28) for score in reference["score_row"]]
    quality_probs = _exp_lut_div_softmax(
        logits,
        score_bits=32,
        weight_bits=16,
        bucket_shift=20,
        input_frac_bits=28,
    )

    assert reference["weights"] == [round(probability * 65535) for probability in quality_probs]


def test_attention_separated_perf_scheduler_preserves_commands_under_backpressure() -> None:
    commands = default_commands(8)
    result = simulate(
        commands,
        producer_count=4,
        consumer_count=1,
        scenario="result_backpressure",
    )

    expected_order = [command.command_id for command in commands]
    assert result["accepted_count"] == 8
    assert result["completed_count"] == 8
    assert result["accepted_order"] == expected_order
    assert result["completed_order"] == expected_order


def test_attention_separated_rtl_matches_perf_for_one_to_one_and_four_to_one() -> None:
    report = build_report(ratios=[(1, 1), (4, 1), (4, 2), (8, 2)], command_count=8)

    assert report["decision"] == "attention_separated_cluster_equivalence_pass"
    assert report["equivalence_pass"] is True
    assert len(report["rows"]) == 16
    assert all(row["equivalence_pass"] for row in report["rows"])
