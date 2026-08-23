from npu.eval.revise_llm_decoder_attention_score32_noc_phase2_exact_transport import (
    DEFAULT_EXACT_MANIFEST,
    DEFAULT_PRIOR_SCHEDULE,
    build_report,
)


def test_exact_transport_separates_contexts_from_packet_descriptors() -> None:
    report = build_report(
        exact_manifest=DEFAULT_EXACT_MANIFEST,
        prior_schedule=DEFAULT_PRIOR_SCHEDULE,
    )
    modes = {mode["name"]: mode for mode in report["exact_transport_modes"]}
    assert report["version"] == 2
    assert report["control_boundary"]["central_scheduler"] == "context_admission_only"

    aligned = modes["aligned_419b_two_flits_per_beat"]
    stats_once = modes["stats_once_ordered_exact"]
    for mode in modes.values():
        assert mode["shared_context_commands"] == 112
        assert mode["reduction_context_commands"] == 4
        assert mode["total_phase2_context_commands"] == 116
        assert mode["total_phase2_commands_semantics"] == (
            "deprecated_packet_descriptor_count"
        )

    assert aligned["total_phase2_packet_descriptors"] == 9536
    assert aligned["total_phase2_flits"] == 76288
    assert stats_once["total_phase2_packet_descriptors"] == 8876
    assert stats_once["total_phase2_flits"] == 70948
    assert stats_once["total_phase2_commands"] == 8876
    assert report["prior_quantities"]["scheduled_commands_semantics"] == (
        "deprecated_packet_descriptor_count"
    )
