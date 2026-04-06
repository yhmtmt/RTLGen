"""Seed-trial variance analytics from L1 trial artifacts."""

from __future__ import annotations

import csv
from dataclasses import dataclass
import math
from pathlib import Path


def _safe_float(value: object) -> float | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _sample_stddev(values: list[float]) -> float | None:
    if not values:
        return None
    if len(values) == 1:
        return 0.0
    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / (len(values) - 1)
    return math.sqrt(variance)


def _derive_design_from_metrics_path(metrics_path: str) -> str:
    parts = Path(metrics_path).parts
    try:
        idx = parts.index('designs')
    except ValueError:
        return Path(metrics_path).stem or ''
    if len(parts) > idx + 2:
        return parts[idx + 2]
    return Path(metrics_path).stem or ''


def _derive_circuit_type_from_metrics_path(metrics_path: str) -> str:
    parts = Path(metrics_path).parts
    try:
        idx = parts.index('designs')
    except ValueError:
        return ''
    if len(parts) > idx + 1:
        return parts[idx + 1]
    return ''


def _derive_platform_from_item_id(item_id: str) -> str:
    known = ('nangate45', 'asap7', 'sky130hd')
    for candidate in known:
        marker = f'_{candidate}_'
        if marker in item_id:
            return candidate
    return ''


@dataclass(frozen=True)
class SeedTrialVarianceRow:
    item_id: str
    circuit_type: str
    design: str
    platform: str
    success_count: int
    seed_count: int
    critical_path_min_ns: float
    critical_path_mean_ns: float
    critical_path_max_ns: float
    critical_path_range_ns: float
    critical_path_stddev_ns: float
    seeds: list[int]

    def as_dict(self) -> dict[str, object]:
        return {
            'item_id': self.item_id,
            'circuit_type': self.circuit_type,
            'design': self.design,
            'platform': self.platform,
            'success_count': self.success_count,
            'seed_count': self.seed_count,
            'critical_path_min_ns': self.critical_path_min_ns,
            'critical_path_mean_ns': self.critical_path_mean_ns,
            'critical_path_max_ns': self.critical_path_max_ns,
            'critical_path_range_ns': self.critical_path_range_ns,
            'critical_path_stddev_ns': self.critical_path_stddev_ns,
            'seeds': self.seeds,
        }


def load_seed_trial_variance(*, repo_root: str, limit: int) -> list[dict[str, object]]:
    trials_root = Path(repo_root).resolve() / 'control_plane' / 'shadow_exports' / 'l1_trials'
    if not trials_root.exists():
        return []

    rows: list[SeedTrialVarianceRow] = []
    for trial_table in sorted(trials_root.rglob('trial_table.csv')):
        item_id = trial_table.parent.name
        with trial_table.open('r', newline='', encoding='utf-8') as handle:
            reader = csv.DictReader(handle)
            successful = []
            for row in reader:
                if str(row.get('status') or '').strip().lower() != 'succeeded':
                    continue
                cp = _safe_float(row.get('critical_path_ns'))
                if cp is None or cp <= 0:
                    continue
                seed_raw = str(row.get('seed') or '').strip()
                seed = int(seed_raw) if seed_raw else None
                successful.append({
                    'seed': seed,
                    'critical_path_ns': cp,
                    'metrics_csv': str(row.get('metrics_csv') or '').strip(),
                })

        if len(successful) < 2:
            continue
        seeds = sorted({entry['seed'] for entry in successful if entry['seed'] is not None})
        if len(seeds) < 2:
            continue
        cp_values = sorted(float(entry['critical_path_ns']) for entry in successful)
        metrics_path = next((entry['metrics_csv'] for entry in successful if entry['metrics_csv']), '')
        mean = sum(cp_values) / len(cp_values)
        stddev = _sample_stddev(cp_values)
        if stddev is None:
            continue
        rows.append(
            SeedTrialVarianceRow(
                item_id=item_id,
                circuit_type=_derive_circuit_type_from_metrics_path(metrics_path),
                design=_derive_design_from_metrics_path(metrics_path),
                platform=_derive_platform_from_item_id(item_id),
                success_count=len(successful),
                seed_count=len(seeds),
                critical_path_min_ns=cp_values[0],
                critical_path_mean_ns=mean,
                critical_path_max_ns=cp_values[-1],
                critical_path_range_ns=cp_values[-1] - cp_values[0],
                critical_path_stddev_ns=stddev,
                seeds=seeds,
            )
        )

    rows.sort(
        key=lambda row: (
            -float(row.critical_path_stddev_ns),
            -float(row.critical_path_range_ns),
            -int(row.seed_count),
            row.item_id,
        )
    )
    return [row.as_dict() for row in rows[:limit]]
