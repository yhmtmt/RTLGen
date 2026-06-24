#!/usr/bin/env python3
"""Tests for candidate-loading helpers in the measured compute estimator."""

import csv
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import npu.eval.estimate_llm_decoder_attention_kv_measured_compute as measured_compute


def _write_dense_gemm_design_config(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "dense_gemm_tile": {
            "precision": "fp16",
            "array_m": 16,
            "array_n": 16,
            "k_unroll": 1,
            "pipeline_stages": 1,
        }
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _write_metrics_csv(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        {
            "tag": "npu_dense_gemm_tile_v3_depth_hier",
            "status": "ok",
            "critical_path_ns": "1.23",
            "instance_area_um2": "4567.0",
            "total_power_mw": "12.5",
            "param_hash": "hash-a",
        }
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["tag", "status", "critical_path_ns", "instance_area_um2", "total_power_mw", "param_hash"]
        )
        writer.writeheader()
        writer.writerows(rows)


def test_load_dense_gemm_tile_candidates_reads_campaign_metrics(tmp_path: Path) -> None:
    design_name = "npu_dense_gemm_tile_fp16_16x16_k1_p1"
    design_config = tmp_path / "runs" / "designs" / "npu_blocks" / design_name / "config.json"
    _write_dense_gemm_design_config(design_config)

    campaign_metrics = tmp_path / "runs" / "campaigns" / "npu" / "dense_gemm_tile_v3" / design_name / "metrics.csv"
    _write_metrics_csv(campaign_metrics)

    candidates = measured_compute._load_dense_gemm_tile_candidates(
        repo_root=tmp_path,
        tag_substring="npu_dense_gemm_tile_v3_depth_hier",
    )

    assert len(candidates) == 1
    candidate = candidates[0]
    assert (
        candidate["metrics_csv"]
        == "runs/campaigns/npu/dense_gemm_tile_v3/npu_dense_gemm_tile_fp16_16x16_k1_p1/metrics.csv"
    )
    assert candidate["metrics_tag"] == "npu_dense_gemm_tile_v3_depth_hier"
    assert candidate["dense_array_m"] == 16
    assert candidate["dense_array_n"] == 16
    assert candidate["compute_arch"] == "dense_gemm_16x16_k1_p1"
