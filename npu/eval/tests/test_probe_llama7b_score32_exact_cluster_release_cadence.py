from __future__ import annotations

import pytest
from pathlib import Path
import json

from npu.eval import probe_attention_score32_exact_local16_global_tree_cluster_sram_gqa8 as probe
from npu.eval.probe_llama7b_score32_exact_cluster_release_cadence import (
    _prepare_guarded_rtl,
    _write_behavioral_memories,
    _verilator_two_stage_commands,
    _verilator_control_file_text,
    _alias_module_family,
    extract_cluster_cadence,
    render_markdown,
)
from npu.sim.perf.attention_exact_partial import pack_numerators


def _cluster_stdout(monkeypatch: pytest.MonkeyPatch, *, omit_last: bool = False) -> str:
    rows = []
    lines = []
    packed = pack_numerators((1, 2, 3, 4, 5, 6, 7, 8))
    for group, command_id in enumerate(range(probe.COMMAND_ID_BASE, probe.COMMAND_ID_BASE + 4)):
        for row_index in range(128):
            row = {
                "cluster": 0,
                "command_id": command_id,
                "head_id": group * 8 + row_index // 16,
                "slice": row_index % 16,
                "last": row_index % 16 == 15,
                "global_max": -group,
                "exp_sum": 100 + row_index,
                "value": [1, 2, 3, 4, 5, 6, 7, 8],
            }
            rows.append(row)
            lines.append(
                "CLUSTER_RESULT cluster=0 "
                f"cmd={command_id} head={row['head_id']} slice={row['slice']} "
                f"last={int(row['last'])} max={row['global_max']} sum={row['exp_sum']} "
                f"value={packed:082x} cycle={1000 + group * 500 + row_index}"
            )
    monkeypatch.setattr(
        probe,
        "_reference",
        lambda **_kwargs: {"cluster_rows": [rows] + [[] for _ in range(15)]},
    )
    if omit_last:
        lines.pop()
    lines.append(
        "CLUSTER_SUMMARY cluster=0 wave_accept=32 completed=4 emitted=512 "
        "fill_targets=32 fill_rows=65536 requests=65536 responses=65536 "
        "command_accepts=32 command_releases=32 errors=0"
    )
    return "\n".join(lines)


def test_extract_cluster_cadence_preserves_exact_group_release_cycles(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    report = extract_cluster_cadence(_cluster_stdout(monkeypatch), cluster=0)

    assert report["passed"] is True
    assert report["producer_count"] == 54
    assert [group["first_output_cycle"] for group in report["groups"]] == [
        1000,
        1500,
        2000,
        2500,
    ]
    assert [group["last_output_cycle"] for group in report["groups"]] == [
        1127,
        1627,
        2127,
        2627,
    ]
    assert all(group["output_rows"] == 128 for group in report["groups"])
    assert report["groups"][2]["output_cycles"] == list(range(2000, 2128))

    markdown = render_markdown(
        {
            "decision": "measured",
            "precision": "exact",
            "conservative_group_ready_cycles": [1000, 1500, 2000, 2500],
            "conservative_group_complete_cycles": [1127, 1627, 2127, 2627],
            "representative_clusters": [report],
            "remaining_abstractions": ["mesh replay pending"],
        }
    )
    assert "| 0 | 54 | 3 | 24 | 2500 | 2627 | 128 |" in markdown


def test_extract_cluster_cadence_rejects_incomplete_group(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with pytest.raises(ValueError, match="exact-row mismatch"):
        extract_cluster_cadence(
            _cluster_stdout(monkeypatch, omit_last=True),
            cluster=0,
        )


def test_prepare_guarded_rtl_uses_guard_design_layout(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    calls = []

    def fake_generate(config: dict, out_dir: Path) -> None:
        calls.append(("generate", config, out_dir))
        out_dir.mkdir(parents=True)
        (out_dir / "config.json").write_text("{}", encoding="utf-8")

    def fake_guard(argv: list[str]) -> int:
        calls.append(("guard", argv))
        assert argv == [
            "--design-dir",
            str(tmp_path),
            "--config",
            str(tmp_path / "verilog/config.json"),
        ]
        return 0

    module = __import__(
        "npu.eval.probe_llama7b_score32_exact_cluster_release_cadence",
        fromlist=["generate"],
    )
    monkeypatch.setattr(module, "generate", fake_generate)
    monkeypatch.setattr(module, "strict_guard_main", fake_guard)

    assert _prepare_guarded_rtl({"top_name": "dut"}, tmp_path) == tmp_path / "verilog"
    assert calls[0] == ("generate", {"top_name": "dut"}, tmp_path / "verilog")
    assert calls[1][0] == "guard"


def test_behavioral_memory_bundle_covers_cluster_macros(tmp_path: Path) -> None:
    text = _write_behavioral_memories(tmp_path).read_text(encoding="utf-8")
    assert text.count("module fakeram45_2048x39") == 1
    assert text.count("module fakeram45_64x32") == 1


def test_cadence_request_is_source_pinned_and_human_gated() -> None:
    root = Path(__file__).resolve().parents[3]
    proposal_dir = root / (
        "docs/proposals/"
        "prop_l2_decoder_attention_score32_exact_cluster_release_cadence_llama7b_v1"
    )
    request = json.loads((proposal_dir / "evaluation_requests.json").read_text(encoding="utf-8"))
    item = request["requested_items"][0]
    assert request["source_commit"] == "90047370adde8e174c72de0764fccc496ae5534d"
    assert item["status"] == "ready_to_queue_pending_human_approval"
    assert item["run_physical"] is False
    assert "Human dispatch approval is mandatory" in item["acceptance_notes"]
    gate = (proposal_dir / "evaluation_gate.md").read_text(encoding="utf-8")
    assert "awaiting_human_approval" in gate
    assert "48,384" in gate


def test_verilator_two_stage_flow_avoids_binary_hierarchy_bug(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    module = __import__(
        "npu.eval.probe_llama7b_score32_exact_cluster_release_cadence",
        fromlist=["probe"],
    )
    monkeypatch.setattr(module.probe, "_tool", lambda name: f"/tools/{name}")
    commands = _verilator_two_stage_commands(
        rtl_dir=tmp_path / "rtl",
        fakeram_path=tmp_path / "memories.sv",
        tb_path=tmp_path / "tb.sv",
        control_path=tmp_path / "cluster.vlt",
        obj_dir=tmp_path / "obj",
    )
    assert commands[0][:7] == [
        "/tools/verilator",
        "--cc",
        "--main",
        "--timing",
        "--hierarchical",
        "--build-dep-bin",
        "/tools/verilator",
    ]
    assert "--binary" not in commands[0]
    assert commands[1][:5] == ["make", "-C", str(tmp_path / "obj"), "-f", "Vtb.mk"]
    assert commands[2][-2:] == ["-pthread", "-latomic"]


def test_module_family_alias_removes_verilator_double_underscore_boundary() -> None:
    source = "module long__cluster; long__cluster__child u(); endmodule\n"
    aliased = _alias_module_family(source, prefix="long__cluster", alias="cadence_p54")
    assert aliased == "module cadence_p54; cadence_p54_h_child u(); endmodule\n"
    with pytest.raises(ValueError, match="contain no double underscore"):
        _alias_module_family(source, prefix="long__cluster", alias="bad__alias")


def test_verilator_control_partitions_repeated_cluster_blocks() -> None:
    text = _verilator_control_file_text("cadence_p54")
    assert 'hier_block -module "cadence_p54"' not in text
    assert text.count("hier_block") == 3
    assert 'hier_block -module "cadence_p54_h_compute_cluster_h_producer"' in text
    assert 'hier_block -module "cadence_p54_h_compute_cluster_h_reducer"' in text
    assert 'hier_block -module "cadence_p54_h_sram_endpoint"' in text
