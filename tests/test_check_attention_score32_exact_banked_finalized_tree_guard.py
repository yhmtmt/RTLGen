import json
from pathlib import Path
import re
import subprocess
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.rtlgen.gen_attention_score32_exact_banked_finalized_tree import generate


def _config_path(banks: int) -> Path:
    return (
        REPO_ROOT
        / "runs"
        / "designs"
        / "npu_blocks"
        / f"attention_score32_exact_banked_finalized_tree_c16_r2_l8_b{banks}"
        / "config.json"
    )


def _factored_config_path(banks: int) -> Path:
    return (
        REPO_ROOT
        / "runs"
        / "designs"
        / "npu_blocks"
        / f"attention_score32_exact_banked_finalized_tree_factored_c16_r2_l8_b{banks}"
        / "config.json"
    )


def _prepare_design_dir(tmp_path: Path, *, banks: int, factored: bool = False) -> Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
    name = (
        f"attention_score32_exact_banked_finalized_tree_factored_c16_r2_l8_b{banks}"
        if factored
        else f"attention_score32_exact_banked_finalized_tree_c16_r2_l8_b{banks}"
    )
    design_dir = tmp_path / name
    design_dir.mkdir()
    source_config_path = _factored_config_path(banks) if factored else _config_path(banks)
    config = json.loads(source_config_path.read_text(encoding="utf-8"))
    (design_dir / "config.json").write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    generate(config, design_dir / "verilog")
    return design_dir


def _run_guard(design_dir: Path) -> subprocess.CompletedProcess[str]:
    return _run_guard_with_sweep(design_dir)


def _run_guard_with_sweep(design_dir: Path, sweep: Path | None = None) -> subprocess.CompletedProcess[str]:
    command = [
        sys.executable,
        "npu/eval/check_attention_score32_exact_banked_finalized_tree_guard.py",
        "--design-dir",
        str(design_dir),
        "--config",
        str(design_dir / "config.json"),
    ]
    if sweep is not None:
        command.extend(["--sweep", str(sweep)])
    return subprocess.run(
        command,
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def test_banked_exact_finalized_tree_guard_accepts_all_checked_in_configs(tmp_path: Path) -> None:
    for banks in (1, 16, 32, 57, 58, 59, 64):
        design_dir = _prepare_design_dir(tmp_path / f"case_{banks}", banks=banks)
        result = _run_guard(design_dir)
        assert result.returncode == 0, result.stderr
        payload = json.loads(result.stdout)
        assert payload["finalizer_banks"] == banks
        assert payload["clusters"] == 16
        assert payload["tree_nodes"] == 15
        assert payload["tree_stages"] == 4
        assert payload["status"] == "ok"


def test_banked_exact_finalized_tree_guard_accepts_factored_retry_configs(tmp_path: Path) -> None:
    for banks in (59, 64):
        design_dir = _prepare_design_dir(tmp_path / f"factored_case_{banks}", banks=banks, factored=True)
        result = _run_guard(design_dir)
        assert result.returncode == 0, result.stderr
        payload = json.loads(result.stdout)
        assert payload["finalizer_banks"] == banks
        assert payload["status"] == "ok"


def test_banked_exact_finalized_tree_guard_rejects_stale_generated_top(tmp_path: Path) -> None:
    design_dir = _prepare_design_dir(tmp_path, banks=59)
    top_path = design_dir / "verilog" / "top.v"
    top_path.write_text(top_path.read_text(encoding="utf-8") + "\n// stale artifact drift\n", encoding="utf-8")

    result = _run_guard(design_dir)
    assert result.returncode != 0
    assert "generated RTL artifacts do not match current generator output: top.v" in result.stderr


def test_banked_exact_finalized_tree_guard_rejects_manifest_boundary_mismatch(tmp_path: Path) -> None:
    design_dir = _prepare_design_dir(tmp_path, banks=58)
    manifest_path = design_dir / "verilog" / "attention_score32_exact_banked_finalized_tree_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["actual_finalizer_accept_interval_cycles"] = 58
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    result = _run_guard(design_dir)
    assert result.returncode != 0
    assert "generated manifest actual_finalizer_accept_interval_cycles must be 59" in result.stderr


def test_banked_exact_finalized_tree_guard_rejects_missing_order_fifo_token(tmp_path: Path) -> None:
    design_dir = _prepare_design_dir(tmp_path, banks=57)
    top_path = design_dir / "verilog" / "top.v"
    text = top_path.read_text(encoding="utf-8")
    top_path.write_text(
        text.replace(
            "wire order_fifo_enqueue_ready_w = !order_fifo_full_w || order_fifo_dequeue_fire_w;",
            "wire order_fifo_enqueue_ready_w = !order_fifo_full_w;",
        ),
        encoding="utf-8",
    )

    result = _run_guard(design_dir)
    assert result.returncode != 0
    assert (
        "generated RTL missing semantic token: wire order_fifo_enqueue_ready_w = !order_fifo_full_w || order_fifo_dequeue_fire_w;"
        in result.stderr
    )


def test_banked_exact_finalized_tree_guard_rejects_finalizer_combinational_divide(tmp_path: Path) -> None:
    design_dir = _prepare_design_dir(tmp_path, banks=59)
    top_path = design_dir / "verilog" / "top.v"
    text = top_path.read_text(encoding="utf-8")
    module_name = "attention_score32_exact_banked_finalized_tree_c16_r2_l8_b59__root_finalizer"
    pattern = re.compile(rf"(module\s+{re.escape(module_name)}\b.*?)(endmodule\s*)", re.DOTALL)
    match = pattern.search(text)
    assert match is not None
    top_path.write_text(
        text[: match.start()] + match.group(1) + "  wire [31:0] bad_div = 32'd8 / 32'd2;\n" + match.group(2) + text[match.end() :],
        encoding="utf-8",
    )

    result = _run_guard(design_dir)
    assert result.returncode != 0
    assert "generated finalizer RTL must not contain combinational division operators" in result.stderr


def test_banked_exact_finalized_tree_guard_does_not_flag_pair_merge_division_as_finalizer_divide(tmp_path: Path) -> None:
    design_dir = _prepare_design_dir(tmp_path, banks=59)
    top_path = design_dir / "verilog" / "top.v"
    text = top_path.read_text(encoding="utf-8")
    module_name = "attention_score32_exact_banked_finalized_tree_c16_r2_l8_b59__partial_tree__pair_node"
    pattern = re.compile(rf"(module\s+{re.escape(module_name)}\b.*?)(endmodule\s*)", re.DOTALL)
    match = pattern.search(text)
    assert match is not None
    top_path.write_text(
        text[: match.start()] + match.group(1) + "  wire [31:0] benign_div = 32'd8 / 32'd2;\n" + match.group(2) + text[match.end() :],
        encoding="utf-8",
    )

    result = _run_guard(design_dir)
    assert result.returncode != 0
    assert "generated finalizer RTL must not contain combinational division operators" not in result.stderr


def test_banked_exact_finalized_tree_guard_accepts_banked_ppa_sweep_membership(tmp_path: Path) -> None:
    sweep_path = (
        REPO_ROOT
        / "runs"
        / "campaigns"
        / "npu"
        / "attention_score32_exact_banked_finalized_tree_v1"
        / "sweeps"
        / "nangate45_attention_score32_exact_banked_finalized_tree_c16_bank_firstpass.json"
    )
    for banks in (16, 32, 59, 64):
        design_dir = _prepare_design_dir(tmp_path / f"ppa_case_{banks}", banks=banks)
        result = _run_guard_with_sweep(design_dir, sweep=sweep_path)
        assert result.returncode == 0, result.stderr


def test_banked_exact_finalized_tree_guard_accepts_factored_retry_sweep_membership(tmp_path: Path) -> None:
    sweep_path = (
        REPO_ROOT
        / "runs"
        / "campaigns"
        / "npu"
        / "attention_score32_exact_banked_finalized_tree_factored_v2"
        / "sweeps"
        / "nangate45_attention_score32_exact_banked_finalized_tree_factored_c16_bank_retry_r2.json"
    )
    for banks in (59, 64):
        design_dir = _prepare_design_dir(tmp_path / f"factored_ppa_case_{banks}", banks=banks, factored=True)
        result = _run_guard_with_sweep(design_dir, sweep=sweep_path)
        assert result.returncode == 0, result.stderr


def test_banked_exact_finalized_tree_guard_rejects_non_ppa_bank_membership_when_sweep_is_supplied(tmp_path: Path) -> None:
    sweep_path = (
        REPO_ROOT
        / "runs"
        / "campaigns"
        / "npu"
        / "attention_score32_exact_banked_finalized_tree_v1"
        / "sweeps"
        / "nangate45_attention_score32_exact_banked_finalized_tree_c16_bank_firstpass.json"
    )
    design_dir = _prepare_design_dir(tmp_path, banks=57)
    result = _run_guard_with_sweep(design_dir, sweep=sweep_path)
    assert result.returncode != 0
    assert "banked PPA sweep membership requires c16/r2/l8 with finalizer_banks in [16, 32, 59, 64]" in result.stderr


def test_banked_exact_finalized_tree_guard_rejects_factored_sweep_bank_mismatch(tmp_path: Path) -> None:
    sweep_path = (
        REPO_ROOT
        / "runs"
        / "campaigns"
        / "npu"
        / "attention_score32_exact_banked_finalized_tree_factored_v2"
        / "sweeps"
        / "nangate45_attention_score32_exact_banked_finalized_tree_factored_c16_bank_retry_r2.json"
    )
    design_dir = _prepare_design_dir(tmp_path, banks=57)
    result = _run_guard_with_sweep(design_dir, sweep=sweep_path)
    assert result.returncode != 0
    assert "banked PPA sweep membership requires c16/r2/l8 with finalizer_banks in [59, 64]" in result.stderr


def test_banked_exact_finalized_tree_guard_rejects_ppa_sweep_knob_drift(tmp_path: Path) -> None:
    design_dir = _prepare_design_dir(tmp_path, banks=59)
    sweep_path = tmp_path / "nangate45_attention_score32_exact_banked_finalized_tree_c16_bank_firstpass.json"
    sweep_path.write_text(
        json.dumps(
            {
                "tag_prefix": "attention_score32_exact_banked_finalized_tree_c16_bank_firstpass_v1",
                "flow_params": {
                    "CLOCK_PERIOD": [8.0],
                    "DIE_AREA": ["0 0 2500 2500"],
                    "CORE_AREA": ["50 50 2450 2450"],
                    "PLACE_DENSITY": [0.3, 0.5],
                    "SYNTH_HIERARCHICAL": [1],
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    result = _run_guard_with_sweep(design_dir, sweep=sweep_path)
    assert result.returncode != 0
    assert "banked PPA sweep flow_params do not match the checked-in banked-finalized-tree contract" in result.stderr


def test_banked_exact_finalized_tree_guard_rejects_equivalence_hash_token_in_datapath(tmp_path: Path) -> None:
    design_dir = _prepare_design_dir(tmp_path, banks=59)
    top_path = design_dir / "verilog" / "top.v"
    top_path.write_text(top_path.read_text(encoding="utf-8") + "\nwire equivalence_hash = 1'b0;\n", encoding="utf-8")

    result = _run_guard(design_dir)
    assert result.returncode != 0
    assert "functional datapath must not contain equivalence_hash tokens" in result.stderr
