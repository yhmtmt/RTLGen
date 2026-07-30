import json
from pathlib import Path
import subprocess
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.rtlgen.gen_attention_score32_exact_partial_tree import generate


def _config_path(clusters: int) -> Path:
    return (
        REPO_ROOT
        / "runs"
        / "designs"
        / "npu_blocks"
        / f"attention_score32_exact_partial_tree_c{clusters}_r2"
        / "config.json"
    )


def _prepare_design_dir(tmp_path: Path, *, clusters: int) -> Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
    design_dir = tmp_path / f"attention_score32_exact_partial_tree_c{clusters}_r2"
    design_dir.mkdir()
    config = json.loads(_config_path(clusters).read_text(encoding="utf-8"))
    (design_dir / "config.json").write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    generate(config, design_dir / "verilog")
    return design_dir


def test_exact_partial_tree_guard_accepts_all_checked_in_cluster_configs(tmp_path: Path) -> None:
    for clusters in (2, 4, 8, 16):
        design_dir = _prepare_design_dir(tmp_path / f"case_{clusters}", clusters=clusters)
        result = subprocess.run(
            [
                sys.executable,
                "npu/eval/check_attention_score32_exact_partial_tree_guard.py",
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
        assert result.returncode == 0, result.stderr
        payload = json.loads(result.stdout)
        assert payload["clusters"] == clusters
        assert payload["tree_nodes"] == clusters - 1
        assert payload["tree_stages"] == {2: 1, 4: 2, 8: 3, 16: 4}[clusters]
        assert payload["status"] == "ok"


def test_exact_partial_tree_guard_rejects_stale_generated_config(tmp_path: Path) -> None:
    design_dir = _prepare_design_dir(tmp_path, clusters=4)
    config = json.loads((design_dir / "config.json").read_text(encoding="utf-8"))
    config["attention_score32_exact_partial_tree"]["clusters"] = 8
    (design_dir / "config.json").write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "npu/eval/check_attention_score32_exact_partial_tree_guard.py",
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
    assert result.returncode != 0
    assert "generated config does not match source config" in result.stderr


def test_exact_partial_tree_guard_rejects_manifest_boundary_mismatch(tmp_path: Path) -> None:
    design_dir = _prepare_design_dir(tmp_path, clusters=8)
    manifest_path = design_dir / "verilog" / "attention_score32_exact_partial_tree_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["direct_328bit_links_unclosed"] = False
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "npu/eval/check_attention_score32_exact_partial_tree_guard.py",
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
    assert result.returncode != 0
    assert "generated manifest direct_328bit_links_unclosed must be True" in result.stderr


def test_exact_partial_tree_guard_accepts_explicit_legacy_monolithic_pair_merge_impl(tmp_path: Path) -> None:
    design_dir = tmp_path / "legacy_case"
    design_dir.mkdir()
    config = json.loads(_config_path(8).read_text(encoding="utf-8"))
    config["attention_score32_exact_partial_tree"]["exp_scale_impl"] = "legacy_monolithic_lut_exact"
    (design_dir / "config.json").write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    generate(config, design_dir / "verilog")

    result = subprocess.run(
        [
            sys.executable,
            "npu/eval/check_attention_score32_exact_partial_tree_guard.py",
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
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["status"] == "ok"


def test_exact_partial_tree_guard_rejects_pair_merge_impl_manifest_mismatch(tmp_path: Path) -> None:
    design_dir = tmp_path / "factored_mismatch_case"
    design_dir.mkdir()
    config = json.loads(_config_path(8).read_text(encoding="utf-8"))
    config["attention_score32_exact_partial_tree"]["exp_scale_impl"] = "factored_h33_l64_mul_exact"
    (design_dir / "config.json").write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    generate(config, design_dir / "verilog")
    manifest_path = design_dir / "verilog" / "attention_score32_exact_partial_tree_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["submodule_manifests"]["pair_merge"]["exp_scale_impl"] = "legacy_monolithic_lut_exact"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "npu/eval/check_attention_score32_exact_partial_tree_guard.py",
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
    assert result.returncode != 0
    assert "pair-merge submodule manifest exp_scale_impl must be factored_h33_l64_mul_exact" in result.stderr


def test_exact_partial_tree_guard_rejects_top_level_internal_storage(tmp_path: Path) -> None:
    design_dir = _prepare_design_dir(tmp_path, clusters=16)
    top_path = design_dir / "verilog" / "top.v"
    text = top_path.read_text(encoding="utf-8")
    prefix, suffix = text.rsplit("endmodule\n", 1)
    top_path.write_text(
        prefix + "reg [327:0] illegal_full_state_q [0:31];\nendmodule\n" + suffix,
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "npu/eval/check_attention_score32_exact_partial_tree_guard.py",
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
    assert result.returncode != 0
    assert "top module must not contain internal reg storage" in result.stderr
