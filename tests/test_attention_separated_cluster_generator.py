import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]


def _write_config(config_path: Path, *, producer_count: int, consumer_count: int, **overrides: int) -> None:
    cluster = {
        "producer_count": producer_count,
        "consumer_count": consumer_count,
        "row_elems": 8,
        "head_dim": 8,
        "value_dim": 8,
        "score_bits": 32,
        "weight_bits": 16,
        "input_frac_bits": 28,
        "exp_bucket_shift": 20,
    }
    cluster.update(overrides)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        json.dumps(
            {
                "top_name": "attention_separated_cluster_smoke",
                "attention_separated_cluster": cluster,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def _generate(design_dir: Path, config_path: Path) -> tuple[str, dict[str, object]]:
    subprocess.run(
        [
            sys.executable,
            "npu/rtlgen/gen_attention_separated_cluster.py",
            "--config",
            str(config_path),
            "--out",
            str(design_dir / "verilog"),
        ],
        cwd=str(REPO_ROOT),
        check=True,
    )
    top_text = (design_dir / "verilog" / "top.v").read_text(encoding="utf-8")
    manifest = json.loads(
        (design_dir / "verilog" / "attention_separated_cluster_manifest.json").read_text(encoding="utf-8")
    )
    return top_text, manifest


def _maybe_compile_with_iverilog(design_dir: Path) -> None:
    iverilog = shutil.which("iverilog")
    if iverilog is None:
        fallback = Path("/oss-cad-suite/bin/iverilog")
        if fallback.exists():
            iverilog = str(fallback)
    if iverilog is None:
        return
    subprocess.run(
        [
            iverilog,
            "-g2012",
            "-o",
            str(design_dir / "simv"),
            str(design_dir / "verilog" / "top.v"),
        ],
        cwd=str(REPO_ROOT),
        check=True,
    )


@pytest.mark.parametrize(("producer_count", "consumer_count"), [(1, 1), (4, 1)])
def test_attention_separated_cluster_generator_configurations(
    tmp_path: Path, producer_count: int, consumer_count: int
) -> None:
    design_dir = tmp_path / f"attention_separated_cluster_p{producer_count}_c{consumer_count}"
    config_path = design_dir / "config.json"
    _write_config(config_path, producer_count=producer_count, consumer_count=consumer_count)

    top_text, manifest = _generate(design_dir, config_path)

    assert manifest["semantic_profile"] == "q8_k8_v8_a32_s32_w16_exp_lut_div_b20"
    assert manifest["producer_count"] == producer_count
    assert manifest["consumer_count"] == consumer_count
    assert manifest["producer_to_consumer_ratio"] == f"{producer_count}:{consumer_count}"
    assert manifest["producer_queue_depth"] == 1
    assert manifest["consumer_queue_depth"] == 1
    assert manifest["producer_payload_width"] == 784
    assert manifest["consumer_result_width"] == 720
    assert manifest["stage_outputs"]["top"] == [
        "result_command_id",
        "result_score_row",
        "result_weights",
        "result_value",
    ]

    for token in (
        "command_valid",
        "command_ready",
        "command_id",
        "command_seed",
        "consumer_enable",
        "result_valid",
        "result_score_row",
        "result_weights",
        "result_value",
        "accepted_count",
        "completed_count",
        "issue_rr_ptr",
        "dispatch_producer_rr_ptr",
        "dispatch_consumer_rr_ptr",
        "result_rr_ptr",
        "exp_lut",
        "weight_numer = (exp_weight[row_idx] * 16'd65535) + (sum_exp >> 1);",
        "accum_lane = accum_lane + ($signed(value_lane) * $signed({1'b0, weight_lane[row_idx]}));",
    ):
        assert token in top_text

    assert "result_hash" not in top_text
    assert "equivalence_hash" not in top_text
    assert f"u_producer_{producer_count - 1}" in top_text
    assert f"u_consumer_{consumer_count - 1}" in top_text

    _maybe_compile_with_iverilog(design_dir)


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"producer_count": 0}, "producer_count must be in [1, 8]"),
        ({"consumer_count": 2, "producer_count": 1}, "consumer_count must be less than or equal to producer_count"),
        ({"row_elems": 4}, "row_elems must be 8"),
    ],
)
def test_attention_separated_cluster_generator_rejects_invalid_params(
    tmp_path: Path, overrides: dict[str, int], message: str
) -> None:
    design_dir = tmp_path / "attention_separated_cluster_invalid"
    config_path = design_dir / "config.json"
    local_overrides = dict(overrides)
    producer_count = local_overrides.pop("producer_count", 1)
    consumer_count = local_overrides.pop("consumer_count", 1)
    _write_config(
        config_path,
        producer_count=producer_count,
        consumer_count=consumer_count,
        **local_overrides,
    )

    result = subprocess.run(
        [
            sys.executable,
            "npu/rtlgen/gen_attention_separated_cluster.py",
            "--config",
            str(config_path),
            "--out",
            str(design_dir / "verilog"),
        ],
        cwd=str(REPO_ROOT),
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert message in (result.stderr + result.stdout)
