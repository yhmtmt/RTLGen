from control_plane.artifact_policy import is_transportable_expected_output


def test_transportable_expected_output_allows_generated_campaign_json() -> None:
    assert is_transportable_expected_output(
        "runs/campaigns/npu/demo_campaign/campaign__l2_demo_campaign.json"
    )


def test_transportable_expected_output_rejects_campaign_artifacts_dir() -> None:
    assert not is_transportable_expected_output(
        "runs/campaigns/npu/demo_campaign__l2_demo_campaign/artifacts/mapper/x/schedule.yml"
    )
