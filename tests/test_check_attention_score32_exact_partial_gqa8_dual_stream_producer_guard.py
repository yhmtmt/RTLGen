import json
from pathlib import Path
import subprocess
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.rtlgen.gen_attention_score32_exact_partial_gqa8_dual_stream_producer import generate


def _config_path(name: str = "config.json") -> Path:
    return (
        REPO_ROOT
        / "runs"
        / "designs"
        / "npu_blocks"
        / "attention_score32_exact_partial_gqa8_dual_stream_producer_b8"
        / name
    )


def _prepare_design_dir(tmp_path: Path, *, config_name: str) -> Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
    design_dir = tmp_path / config_name.replace(".json", "")
    design_dir.mkdir()
    config = json.loads(_config_path(config_name).read_text(encoding="utf-8"))
    (design_dir / config_name).write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    generate(config, design_dir / "verilog")
    return design_dir


def _run_guard(design_dir: Path, *, config_name: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "npu/eval/check_attention_score32_exact_partial_gqa8_dual_stream_producer_guard.py",
            "--design-dir",
            str(design_dir),
            "--config",
            str(design_dir / config_name),
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def test_exact_partial_gqa8_dual_stream_producer_guard_accepts_checked_in_configs(tmp_path: Path) -> None:
    for config_name in (
        "config.json",
        "config_heads32_native.json",
        "config_llama_wave.json",
        "config_llama_wave_worst4_group_major.json",
    ):
        design_dir = _prepare_design_dir(tmp_path / config_name.replace(".json", ""), config_name=config_name)
        result = _run_guard(design_dir, config_name=config_name)
        assert result.returncode == 0, result.stderr
        payload = json.loads(result.stdout)
        assert payload["status"] == "ok"
        assert payload["streams"] == 2
        assert payload["query_heads_per_stream"] == 8
        assert payload["structural_score_macs_per_cycle"] == 128
        assert payload["max_blocks"] == 8
        assert payload["design"] == "attention_score32_exact_partial_gqa8_dual_stream_producer_b8"


def test_exact_partial_gqa8_dual_stream_producer_guard_rejects_stale_top(tmp_path: Path) -> None:
    design_dir = _prepare_design_dir(tmp_path, config_name="config.json")
    top_path = design_dir / "verilog" / "top.v"
    top_path.write_text(top_path.read_text(encoding="utf-8") + "\n// stale drift\n", encoding="utf-8")

    result = _run_guard(design_dir, config_name="config.json")
    assert result.returncode != 0
    assert "generated RTL artifacts do not match current generator output: top.v" in result.stderr


def test_exact_partial_gqa8_dual_stream_producer_guard_rejects_manifest_result_mode_drift(tmp_path: Path) -> None:
    design_dir = _prepare_design_dir(tmp_path, config_name="config.json")
    manifest_path = design_dir / "verilog" / "attention_score32_exact_partial_gqa8_dual_stream_producer_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["submodule_manifests"]["gqa_group"]["result_mode"] = "normalized"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    result = _run_guard(design_dir, config_name="config.json")
    assert result.returncode != 0
    assert "gqa_group submodule manifest result_mode must be exact_partial" in result.stderr


def test_exact_partial_gqa8_dual_stream_producer_guard_rejects_missing_completion_token(tmp_path: Path) -> None:
    design_dir = _prepare_design_dir(tmp_path, config_name="config.json")
    top_path = design_dir / "verilog" / "top.v"
    text = top_path.read_text(encoding="utf-8")
    top_path.write_text(
        text.replace(
            "if (merge_fire_w && result_last && (result_head_id[2:0] == 3'd7)) begin",
            "if (merge_fire_w && result_last) begin",
        ),
        encoding="utf-8",
    )

    result = _run_guard(design_dir, config_name="config.json")
    assert result.returncode != 0
    assert "generated RTL missing semantic token: result_head_id[2:0] == 3'd7" in result.stderr


def test_exact_partial_gqa8_dual_stream_producer_guard_rejects_equivalence_hash_token(tmp_path: Path) -> None:
    design_dir = _prepare_design_dir(tmp_path, config_name="config.json")
    top_path = design_dir / "verilog" / "top.v"
    top_path.write_text(top_path.read_text(encoding="utf-8") + "\nwire equivalence_hash = 1'b0;\n", encoding="utf-8")

    result = _run_guard(design_dir, config_name="config.json")
    assert result.returncode != 0
    assert "functional datapath must not contain equivalence_hash tokens" in result.stderr
