import json
import subprocess
import sys
from pathlib import Path

from npu.eval.estimate_llm_decoder_attention_kv_dual_stream_physical_feasibility import (
    _load_composed_semantic_profile,
    _load_composed_total_macs,
    _load_composed_variant_kind,
)


def _write_config(config_path: Path, *, clusters: int = 2) -> None:
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        json.dumps(
            {
                "top_name": f"attention_dual_stream_schedule_wrapper_smoke_c{clusters}",
                "attention_dual_stream_schedule_wrapper": {
                    "clusters": clusters,
                    "queue_depth": 8,
                    "tile_id_bits": 16,
                    "wave_id_bits": 12,
                    "base_token_bits": 18,
                    "max_inflight_per_cluster": 2,
                    "cluster_service_cycles": 4,
                    "datapath": {
                        "streams": 2,
                        "array_m": 2,
                        "array_n": 2,
                        "k_unroll": 1,
                        "mac_accum_bits": 32,
                        "softmax_row_elems": 4,
                        "softmax_score_bits": 32,
                        "softmax_weight_bits": 16,
                        "softmax_input_frac_bits": 28,
                        "softmax_accum_bits": 40,
                        "reciprocal_bits": 16,
                        "softmax_reciprocal_lut_bucket_shift": 20,
                        "value_bits": 8,
                        "value_lanes": 4,
                        "partials": 4,
                        "partials_per_cycle": 1,
                        "stream_buffer_bits": 256,
                        "equivalence_hash": False,
                        "softmax_pipeline_stages": 1,
                        "softmax_impl": "exp_lut_div",
                        "semantic_profile": "score32_exp_lut_div",
                    },
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def test_attention_dual_stream_schedule_wrapper_generator_guard_and_syntax(tmp_path: Path) -> None:
    design_dir = tmp_path / "attention_dual_stream_schedule_wrapper_smoke_c2"
    config_path = design_dir / "config.json"
    _write_config(config_path, clusters=2)

    subprocess.run(
        [
            sys.executable,
            "npu/rtlgen/gen_attention_dual_stream_schedule_wrapper.py",
            "--config",
            str(config_path),
            "--out",
            str(design_dir / "verilog"),
        ],
        check=True,
    )
    subprocess.run(
        [
            sys.executable,
            "npu/eval/check_attention_dual_stream_schedule_wrapper_guard.py",
            "--design-dir",
            str(design_dir),
        ],
        check=True,
    )
    subprocess.run(
        [
            "/oss-cad-suite/bin/iverilog",
            "-g2012",
            "-o",
            str(design_dir / "simv"),
            str(design_dir / "verilog" / "top.v"),
        ],
        check=True,
    )

    top_text = (design_dir / "verilog" / "top.v").read_text(encoding="utf-8")
    manifest = json.loads(
        (design_dir / "verilog" / "attention_dual_stream_schedule_wrapper_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    assert manifest["clusters"] == 2
    assert manifest["datapath_total_macs_per_cluster"] == 8
    assert manifest["total_macs"] == 16
    assert manifest["datapath_manifest"]["semantic_profile"] == "score32_exp_lut_div"
    assert "u_dispatch" in top_text
    assert "u_cluster_datapath_0" in top_text
    assert "u_cluster_datapath_1" in top_text
    assert "local_issue_valid" in top_text
    assert "cluster_done_valid" in top_text
    assert "datapath_result_fold" in top_text


def test_schedule_wrapper_metrics_are_loaded_as_composed_compute_variant(tmp_path: Path) -> None:
    design_dir = tmp_path / "attention_dual_stream_schedule_wrapper_smoke_c4"
    config_path = design_dir / "config.json"
    _write_config(config_path, clusters=4)

    subprocess.run(
        [
            sys.executable,
            "npu/rtlgen/gen_attention_dual_stream_schedule_wrapper.py",
            "--config",
            str(config_path),
            "--out",
            str(design_dir / "verilog"),
        ],
        check=True,
    )
    metrics_path = design_dir / "metrics.csv"
    metrics_path.write_text(
        "design,status,critical_path_ns,die_area,total_power_mw,instance_area_um2,param_hash,tag,result_path\n"
        "attention_dual_stream_schedule_wrapper_smoke_c4,ok,12.5,1000,3.25,900,abc,tag,out\n",
        encoding="utf-8",
    )

    assert _load_composed_variant_kind(metrics_path) == "dual_stream_schedule_wrapper"
    assert _load_composed_semantic_profile(metrics_path) == "score32_exp_lut_div"
    assert _load_composed_total_macs(metrics_path) == 32
