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


def test_service_guard_accepts_c2_banked_4x16x64x32_macro_contract(tmp_path: Path) -> None:
    design_dir = tmp_path / "attention_decode_score_multivalue_service_c2_p128_b4_q4_rl2_rr"
    design_dir.mkdir()
    config = _config("attention_decode_score_multivalue_service_c2_p128_b4_q4_rl2_rr", 2)
    (design_dir / "config.json").write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    generate(config, design_dir / "verilog")
    generated_macro_manifest = (design_dir / "verilog" / "macro_manifest.json").read_text(encoding="utf-8")
    (design_dir / "macro_manifest.json").write_text(generated_macro_manifest, encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "npu/eval/check_attention_decode_score_multivalue_service_guard.py",
            "--design-dir",
            str(design_dir),
            "--config",
            str(design_dir / "config.json"),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
