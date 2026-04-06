from __future__ import annotations

from pathlib import Path
import tempfile

from control_plane.services.trial_variance import load_seed_trial_variance


def test_load_seed_trial_variance_uses_successful_seed_trials_only() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td)
        trial_root = repo_root / "control_plane" / "shadow_exports" / "l1_trials" / "trial_item"
        trial_root.mkdir(parents=True)
        (trial_root / "trial_table.csv").write_text(
            "run_key,attempt,trial_index,seed,status,metrics_csv,critical_path_ns,die_area,total_power_mw,failure_category,failure_stage,failure_signature\n"
            "trial_run_1,1,1,11,succeeded,runs/designs/activations/terminal_sigmoid_int8_wrapper/metrics.csv,0.40,12900.0,0.00011,none,,\n"
            "trial_run_2,1,2,12,succeeded,runs/designs/activations/terminal_sigmoid_int8_wrapper/metrics.csv,0.44,12800.0,0.00012,none,,\n"
            "trial_run_3,1,3,13,failed,,,-,-,checkout_error,checkout,bad fetch\n",
            encoding="utf-8",
        )

        rows = load_seed_trial_variance(repo_root=str(repo_root), limit=10)

    assert len(rows) == 1
    row = rows[0]
    assert row["item_id"] == "trial_item"
    assert row["design"] == "terminal_sigmoid_int8_wrapper"
    assert row["circuit_type"] == "activations"
    assert row["success_count"] == 2
    assert row["seed_count"] == 2
    assert row["seeds"] == [11, 12]
    assert round(float(row["critical_path_mean_ns"]), 2) == 0.42
    assert round(float(row["critical_path_range_ns"]), 2) == 0.04
