"""Artifact staging coverage."""

from __future__ import annotations

import json
from pathlib import Path

from control_plane.workers.artifact_stage import collect_expected_output_artifacts, collect_linked_results_artifacts


def _write_json(path: Path, doc: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def test_collect_linked_results_artifacts_includes_decoder_sweep_sidecars(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    base = repo_root / "runs" / "datasets" / "llm_decoder_eval_tiny_v1"
    sweep_rel = "runs/datasets/llm_decoder_eval_tiny_v1/decoder_quality_sweep__demo.json"
    exact_manifest_rel = (
        "runs/datasets/llm_decoder_eval_tiny_v1/candidate_sweeps/demo/"
        "candidate_onnx_softmax_exact/candidate_manifest.json"
    )
    exact_quality_rel = (
        "runs/datasets/llm_decoder_eval_tiny_v1/candidate_sweeps/demo/"
        "candidate_onnx_softmax_exact/quality.json"
    )
    exact_sample_rel = (
        "runs/datasets/llm_decoder_eval_tiny_v1/candidate_sweeps/demo/"
        "candidate_onnx_softmax_exact/candidate/sample_001.json"
    )
    approx_manifest_rel = (
        "runs/datasets/llm_decoder_eval_tiny_v1/candidate_sweeps/demo/"
        "candidate_onnx_softmax_approx/candidate_manifest.json"
    )
    approx_quality_rel = (
        "runs/datasets/llm_decoder_eval_tiny_v1/candidate_sweeps/demo/"
        "candidate_onnx_softmax_approx/quality.json"
    )
    approx_sample_rel = (
        "runs/datasets/llm_decoder_eval_tiny_v1/candidate_sweeps/demo/"
        "candidate_onnx_softmax_approx/candidate/sample_001.json"
    )

    _write_json(repo_root / exact_sample_rel, {"sample_id": "sample_001", "token": "A"})
    _write_json(repo_root / approx_sample_rel, {"sample_id": "sample_001", "token": "B"})
    _write_json(repo_root / exact_quality_rel, {"aggregate": {"next_token_id_match_rate": 1.0}})
    _write_json(repo_root / approx_quality_rel, {"aggregate": {"next_token_id_match_rate": 0.8}})
    _write_json(
        repo_root / exact_manifest_rel,
        {"samples": [{"sample_id": "sample_001", "candidate_json": exact_sample_rel}]},
    )
    _write_json(
        repo_root / approx_manifest_rel,
        {"samples": [{"sample_id": "sample_001", "candidate_json": approx_sample_rel}]},
    )
    _write_json(
        base / "decoder_quality_sweep__demo.json",
        {
            "templates": [
                {"candidate_manifest": exact_manifest_rel, "quality_json": exact_quality_rel},
                {"candidate_manifest": approx_manifest_rel, "quality_json": approx_quality_rel},
            ]
        },
    )

    artifacts = collect_linked_results_artifacts(repo_root=str(repo_root), expected_outputs=[sweep_rel])

    assert [artifact.path for artifact in artifacts] == [
        exact_quality_rel,
        exact_manifest_rel,
        exact_sample_rel,
        approx_quality_rel,
        approx_manifest_rel,
        approx_sample_rel,
    ]
    assert all(artifact.kind == "supporting_output" for artifact in artifacts)
    assert all(artifact.metadata["transport_policy"] == "inline_text_supporting" for artifact in artifacts)


def test_collect_expected_output_artifacts_includes_attention_kv_dataset(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    json_rel = (
        "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
        "decoder_attention_kv_memory__l2_decoder_attention_kv_memory_v1.json"
    )
    report_rel = (
        "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
        "decoder_attention_kv_memory__l2_decoder_attention_kv_memory_v1.md"
    )
    _write_json(repo_root / json_rel, {"sweep_summary": {"generated_rows": 7200, "compact_rows": 240}})
    (repo_root / report_rel).write_text("# attention kv\n", encoding="utf-8")

    artifacts = collect_expected_output_artifacts(
        repo_root=str(repo_root),
        expected_outputs=[json_rel, report_rel],
    )

    assert [artifact.path for artifact in artifacts] == [json_rel, report_rel]
    assert all(artifact.kind == "expected_output" for artifact in artifacts)
    assert all(artifact.metadata["transport_policy"] == "inline_text_evidence" for artifact in artifacts)
    assert all("inline_utf8" in artifact.metadata for artifact in artifacts)


def test_collect_expected_output_artifacts_includes_operational_component_frontier(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    base = "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
    stem = (
        "decoder_attention_operational_component_frontier__"
        "l2_decoder_attention_operational_component_frontier_llama7b_v1"
    )
    json_rel = f"{base}{stem}.json"
    report_rel = f"{base}{stem}.md"
    _write_json(repo_root / json_rel, {"decision": "operational_component_area_timing_recosted_energy_retained"})
    (repo_root / report_rel).write_text("# Operational component frontier\n", encoding="utf-8")

    artifacts = collect_expected_output_artifacts(
        repo_root=str(repo_root),
        expected_outputs=[json_rel, report_rel],
    )

    assert [artifact.path for artifact in artifacts] == [json_rel, report_rel]
    assert all(artifact.kind == "expected_output" for artifact in artifacts)
    assert all(artifact.metadata["transport_policy"] == "inline_text_evidence" for artifact in artifacts)
    assert all("inline_utf8" in artifact.metadata for artifact in artifacts)


def test_collect_expected_output_artifacts_includes_decode_score_tile_equivalence(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    base = "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
    stem = (
        "decoder_attention_decode_score_tile_equivalence__"
        "l2_decoder_attention_decode_score_tile_m1x8_equivalence_llama7b_v1"
    )
    json_rel = f"{base}{stem}.json"
    report_rel = f"{base}{stem}.md"
    _write_json(repo_root / json_rel, {"equivalent": True})
    (repo_root / report_rel).write_text("# Decode score tile equivalence\n", encoding="utf-8")

    artifacts = collect_expected_output_artifacts(
        repo_root=str(repo_root),
        expected_outputs=[json_rel, report_rel],
    )

    assert [artifact.path for artifact in artifacts] == [json_rel, report_rel]
    assert all(artifact.kind == "expected_output" for artifact in artifacts)
    assert all(artifact.metadata["transport_policy"] == "inline_text_evidence" for artifact in artifacts)
    assert all("inline_utf8" in artifact.metadata for artifact in artifacts)


def test_collect_expected_output_artifacts_includes_decode_score_local_cluster_equivalence(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    base = "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
    stem = (
        "decoder_attention_decode_score_local_cluster_equivalence__"
        "l2_decoder_attention_decode_score_local_cluster_equivalence_llama7b_v1"
    )
    json_rel = f"{base}{stem}.json"
    report_rel = f"{base}{stem}.md"
    _write_json(repo_root / json_rel, {"equivalence_pass": True})
    (repo_root / report_rel).write_text("# Decode score local-cluster equivalence\n", encoding="utf-8")

    artifacts = collect_expected_output_artifacts(
        repo_root=str(repo_root),
        expected_outputs=[json_rel, report_rel],
    )

    assert [artifact.path for artifact in artifacts] == [json_rel, report_rel]
    assert all(artifact.kind == "expected_output" for artifact in artifacts)
    assert all(artifact.metadata["transport_policy"] == "inline_text_evidence" for artifact in artifacts)
    assert all("inline_utf8" in artifact.metadata for artifact in artifacts)


def test_collect_expected_output_artifacts_includes_large_attention_schedule_dataset(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    json_rel = (
        "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
        "decoder_attention_kv_dense_tile_endpoint_measured_l1_clustered_schedule__"
        "l2_decoder_attention_kv_dense_tile_endpoint_measured_l1_clustered_schedule_llama7b_v1.json"
    )
    report_rel = (
        "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
        "decoder_attention_kv_dense_tile_endpoint_measured_l1_clustered_schedule__"
        "l2_decoder_attention_kv_dense_tile_endpoint_measured_l1_clustered_schedule_llama7b_v1.md"
    )
    json_path = repo_root / json_rel
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text('{"rows":"' + ("x" * (1024 * 1024 + 1)) + '"}\n', encoding="utf-8")
    (repo_root / report_rel).write_text("# endpoint schedule\n", encoding="utf-8")

    artifacts = collect_expected_output_artifacts(
        repo_root=str(repo_root),
        expected_outputs=[json_rel, report_rel],
    )

    assert [artifact.path for artifact in artifacts] == [json_rel, report_rel]
    assert artifacts[0].kind == "expected_output"
    assert artifacts[0].metadata["transport_policy"] == "inline_text_evidence"
    assert "inline_utf8" not in artifacts[0].metadata
    assert artifacts[1].metadata["inline_utf8"] == "# endpoint schedule\n"


def test_collect_expected_output_artifacts_includes_design_local_diagnostic_and_timing_report(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    base = (
        "runs/designs/npu_blocks/"
        "attention_decode_score_multivalue_cluster_int8_m1x8_iterdiv"
    )
    diagnostic_rel = f"{base}/explicit_onehot_fsm_diagnostic.json"
    report_rel = f"{base}/timing_debug_report.md"
    _write_json(repo_root / diagnostic_rel, {"promotion_valid": False, "promotion_reasons": ["status is flow_failed, not ok"]})
    (repo_root / report_rel).write_text("# timing debug\n", encoding="utf-8")

    artifacts = collect_expected_output_artifacts(
        repo_root=str(repo_root),
        expected_outputs=[diagnostic_rel, report_rel],
    )

    assert [artifact.path for artifact in artifacts] == [diagnostic_rel, report_rel]
    assert all(artifact.kind == "expected_output" for artifact in artifacts)
    assert all(artifact.metadata["transport_policy"] == "inline_text_evidence" for artifact in artifacts)
    assert artifacts[0].metadata["inline_utf8"].startswith("{\n")
    assert artifacts[1].metadata["inline_utf8"] == "# timing debug\n"
