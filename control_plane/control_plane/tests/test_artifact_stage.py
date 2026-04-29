"""Artifact staging coverage."""

from __future__ import annotations

import json
from pathlib import Path

from control_plane.workers.artifact_stage import collect_linked_results_artifacts


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
