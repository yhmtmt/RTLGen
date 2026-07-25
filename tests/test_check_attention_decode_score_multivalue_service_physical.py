import csv
import json
from pathlib import Path
import subprocess
import sys

from npu.rtlgen.gen_attention_decode_score_multivalue_service import generate


def _config(top_name: str, cluster_count: int) -> dict:
    return {
        "top_name": top_name,
        "attention_decode_score_multivalue_service": {
            "cluster_count": cluster_count,
            "max_blocks": 16,
            "packet_w": 128,
            "banks": 4,
            "req_queue_depth": 4,
            "resp_queue_depth": 4,
            "bank_queue_depth": 4,
            "read_latency": 2,
            "arb_mode": "round_robin",
            "locality_burst_max": 2,
            "score_scale_lanes_per_cycle": 1,
            "value_memory_backend": "macro_banked_4x16x64x32",
        },
    }


def test_service_physical_checker_accepts_c2_hierarchical_row(tmp_path: Path) -> None:
    repo_root = Path.cwd()
    design_dir = tmp_path / "attention_decode_score_multivalue_service_c2_p128_b4_q4_rl2_rr"
    design_dir.mkdir()
    config = _config("attention_decode_score_multivalue_service_c2_p128_b4_q4_rl2_rr", 2)
    (design_dir / "config.json").write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    generate(config, design_dir / "verilog")
    generated_macro_manifest = (design_dir / "verilog" / "macro_manifest.json").read_text(encoding="utf-8")
    (design_dir / "macro_manifest.json").write_text(generated_macro_manifest, encoding="utf-8")

    sweep_path = tmp_path / "nangate45_decode_score_multivalue_service_c2_p128_b4_q4_rl2_rr_3700.json"
    sweep_path.write_text(
        json.dumps(
            {
                "tag_prefix": "decode_score_multivalue_service_c2_p128_b4_q4_rl2_rr_3700_v1",
                "flow_params": {
                    "TAG": ["decode_score_multivalue_service_c2_p128_b4_q4_rl2_rr_3700_v1"],
                    "FLOW_VARIANT": ["decode_score_multivalue_service_c2_p128_b4_q4_rl2_rr_3700_v1"],
                    "CLOCK_PERIOD": [10],
                    "PLACE_DENSITY": [0.4],
                    "SYNTH_HIERARCHICAL": [1],
                    "SYNTH_MEMORY_MAX_BITS": [65536],
                },
                "mode_compare": {
                    "modes": [
                        {
                            "name": "flattened_wrapper",
                            "use_macro": True,
                            "param_overrides": {
                                "SYNTH_HIERARCHICAL": 0,
                                "DIE_AREA": "0 0 3700 3700",
                                "CORE_AREA": "50 50 3650 3650",
                            },
                        },
                        {
                            "name": "hierarchical_macro",
                            "use_macro": True,
                            "param_overrides": {
                                "SYNTH_HIERARCHICAL": 1,
                                "DIE_AREA": "0 0 3700 3700",
                                "CORE_AREA": "50 50 3650 3650",
                            },
                        },
                    ]
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    work_dir = tmp_path / "work"
    work_dir.mkdir()
    result_json = work_dir / "result.json"
    result_json.write_text(
        json.dumps({"macro_manifest_path": str((design_dir / "macro_manifest.json").resolve())}, indent=2) + "\n",
        encoding="utf-8",
    )

    metrics_path = design_dir / "metrics.csv"
    with metrics_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=[
                "design",
                "platform",
                "status",
                "critical_path_ns",
                "params_json",
                "result_path",
                "work_result_json",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "design": design_dir.name,
                "platform": "nangate45",
                "status": "ok",
                "critical_path_ns": "9.8",
                "params_json": json.dumps(
                    {
                        "FLOW_VARIANT": "decode_score_multivalue_service_c2_p128_b4_q4_rl2_rr_3700_v1_hierarchical_macro",
                        "CLOCK_PERIOD": 10,
                        "DIE_AREA": "0 0 3700 3700",
                        "CORE_AREA": "50 50 3650 3650",
                    }
                ),
                "result_path": f"runs/designs/npu_blocks/{design_dir.name}/work/mock",
                    "work_result_json": str(result_json),
                }
            )

    result = subprocess.run(
        [
            sys.executable,
            "npu/eval/check_attention_decode_score_multivalue_service_physical.py",
            "--design-dir",
            str(design_dir),
            "--metrics-path",
            str(metrics_path),
            "--sweep",
            str(sweep_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
