from npu.eval.probe_attention_separated_equivalence import build_report
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
