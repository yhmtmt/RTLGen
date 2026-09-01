from __future__ import annotations

import pytest

from npu.eval import probe_attention_score32_exact_local16_global_tree_cluster_sram_gqa8 as probe
from npu.eval.probe_llama7b_score32_exact_cluster_release_cadence import (
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
