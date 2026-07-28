import json
from pathlib import Path
import subprocess
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.rtlgen.gen_attention_score32_exact_local_temporal_reducer_physical_harness import generate


def _config_path(producers: int, mode: str) -> Path:
    return (
        REPO_ROOT
        / "runs"
        / "designs"
        / "npu_blocks"
        / f"attention_score32_exact_local_temporal_reducer_physical_harness_p{producers}_{mode}_w8"
        / "config.json"
    )


def _prepare_design_dir(tmp_path: Path, *, producers: int, mode: str) -> Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
    design_dir = tmp_path / f"design_p{producers}_{mode}"
    design_dir.mkdir()
    config = json.loads(_config_path(producers, mode).read_text(encoding="utf-8"))
    (design_dir / "config.json").write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    generate(config, design_dir / "verilog")
    return design_dir


def _run_guard(design_dir: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "npu/eval/check_attention_score32_exact_local_temporal_reducer_physical_harness_guard.py",
            "--design-dir",
            str(design_dir),
            "--config",
            str(design_dir / "config.json"),
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def test_physical_harness_guard_accepts_checked_in_configs(tmp_path: Path) -> None:
    for producers, mode in ((53, "reducer"), (53, "source_only"), (54, "reducer"), (54, "source_only")):
        design_dir = _prepare_design_dir(tmp_path / f"p{producers}_{mode}", producers=producers, mode=mode)
        result = _run_guard(design_dir)
        assert result.returncode == 0, result.stderr
        payload = json.loads(result.stdout)
        assert payload["producers"] == producers
        assert payload["mode"] == mode
        assert payload["waves"] == 8
        assert payload["status"] == "ok"


def test_physical_harness_guard_rejects_stale_top(tmp_path: Path) -> None:
    design_dir = _prepare_design_dir(tmp_path, producers=53, mode="reducer")
    top_path = design_dir / "verilog" / "top.v"
    top_path.write_text(top_path.read_text(encoding="utf-8") + "\n// stale drift\n", encoding="utf-8")

    result = _run_guard(design_dir)
    assert result.returncode != 0
    assert "generated RTL artifacts do not match current generator output: top.v" in result.stderr


def test_physical_harness_guard_rejects_missing_proposal_linkage(tmp_path: Path) -> None:
    design_dir = _prepare_design_dir(tmp_path, producers=53, mode="source_only")
    for config_path in (design_dir / "config.json", design_dir / "verilog" / "config.json"):
        config = json.loads(config_path.read_text(encoding="utf-8"))
        config["report_links"]["proposal_id"] = "wrong_proposal"
        config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")

    result = _run_guard(design_dir)
    assert result.returncode != 0
    assert "report_links proposal_id must be prop_l1_decoder_attention_score32_local_temporal_reducer_v1" in result.stderr


def test_physical_harness_guard_rejects_missing_source_token(tmp_path: Path) -> None:
    design_dir = _prepare_design_dir(tmp_path, producers=53, mode="source_only")
    top_path = design_dir / "verilog" / "top.v"
    text = top_path.read_text(encoding="utf-8")
    top_path.write_text(
        text.replace("if (shared_beat_count_q == 9'd255) begin", "if (shared_beat_count_q == 9'd254) begin"),
        encoding="utf-8",
    )

    result = _run_guard(design_dir)
    assert result.returncode != 0
    assert "generated RTL missing semantic token: if (shared_beat_count_q == 9'd255) begin" in result.stderr
