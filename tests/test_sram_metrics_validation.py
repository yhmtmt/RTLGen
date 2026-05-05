import json
from pathlib import Path

import pytest

from npu.synth.pre_synth_memory import ensure_metrics_shape


def _write_metrics(path: Path, instances: list[dict]) -> None:
    path.write_text(json.dumps({"instances": instances}), encoding="utf-8")


def test_sram_metrics_validation_rejects_no_estimated_instances(tmp_path: Path) -> None:
    metrics = tmp_path / "sram_metrics.json"
    _write_metrics(
        metrics,
        [
            {
                "instance": {"name": "activation_sram"},
                "estimated": False,
                "metrics": {"raw": {}},
            }
        ],
    )

    with pytest.raises(ValueError, match="at least one estimated SRAM instance"):
        ensure_metrics_shape(metrics)


def test_sram_metrics_validation_rejects_incomplete_estimated_metrics(tmp_path: Path) -> None:
    metrics = tmp_path / "sram_metrics.json"
    _write_metrics(
        metrics,
        [
            {
                "instance": {"name": "activation_sram"},
                "estimated": True,
                "metrics": {
                    "area_um2": 100.0,
                    "access_time_ns": 1.0,
                    "read_energy_pj": 2.0,
                },
            }
        ],
    )

    with pytest.raises(ValueError, match="write_energy_pj"):
        ensure_metrics_shape(metrics)


def test_sram_metrics_validation_accepts_complete_estimated_metrics(tmp_path: Path) -> None:
    metrics = tmp_path / "sram_metrics.json"
    _write_metrics(
        metrics,
        [
            {
                "instance": {"name": "activation_sram"},
                "estimated": True,
                "metrics": {
                    "area_um2": 100.0,
                    "access_time_ns": 1.0,
                    "read_energy_pj": 2.0,
                    "write_energy_pj": 3.0,
                },
            }
        ],
    )

    ensure_metrics_shape(metrics)
