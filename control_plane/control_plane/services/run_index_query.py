"""Filtered drill-down queries and comparative analytics over centralized run index rows."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import math

from sqlalchemy.orm import Session

from control_plane.models.run_index_rows import RunIndexRow


def _safe_float_text(value: object) -> float | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _comparable_critical_path(value: object) -> float | None:
    numeric = _safe_float_text(value)
    if numeric is None or numeric <= 0:
        return None
    return numeric


def _mean(values: list[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def _sample_stddev(values: list[float]) -> float | None:
    if not values:
        return None
    if len(values) == 1:
        return 0.0
    avg = _mean(values)
    assert avg is not None
    variance = sum((value - avg) ** 2 for value in values) / (len(values) - 1)
    return math.sqrt(variance)


@dataclass(frozen=True)
class RunIndexQueryRequest:
    circuit_type: str | None = None
    platform: str | None = None
    status: str | None = None
    design_query: str | None = None
    limit: int = 50
    offset: int = 0
    sort_by: str = "index_order"
    descending: bool = False


@dataclass(frozen=True)
class RunIndexQueryResult:
    total_count: int
    filtered_count: int
    available_filters: dict[str, list[str]]
    rows: list[dict[str, object]]


@dataclass(frozen=True)
class RunIndexComparativeResult:
    summary: dict[str, object]
    families: list[dict[str, object]]
    best_designs: list[dict[str, object]]
    family_leaders: list[dict[str, object]]
    failure_rates: list[dict[str, object]]
    design_variance: list[dict[str, object]]
    failure_hotspots: list[dict[str, object]]


def _base_rows(session: Session) -> list[RunIndexRow]:
    return (
        session.query(RunIndexRow)
        .order_by(RunIndexRow.index_order.asc(), RunIndexRow.created_at.asc())
        .all()
    )


def _row_dict(row: RunIndexRow) -> dict[str, object]:
    return {
        "index_order": row.index_order,
        "circuit_type": str(row.circuit_type or ""),
        "design": str(row.design or ""),
        "platform": str(row.platform or ""),
        "status": str(row.status or ""),
        "critical_path_ns": _safe_float_text(row.critical_path_ns),
        "die_area": _safe_float_text(row.die_area),
        "total_power_mw": _safe_float_text(row.total_power_mw),
        "config_hash": str(row.config_hash or ""),
        "param_hash": str(row.param_hash or ""),
        "tag": str(row.tag or ""),
        "result_path": str(row.result_path or ""),
        "params_json": str(row.params_json or ""),
        "metrics_path": str(row.metrics_path or ""),
        "design_path": str(row.design_path or ""),
        "sram_area_um2": _safe_float_text(row.sram_area_um2),
        "sram_read_energy_pj": _safe_float_text(row.sram_read_energy_pj),
        "sram_write_energy_pj": _safe_float_text(row.sram_write_energy_pj),
        "sram_max_access_time_ns": _safe_float_text(row.sram_max_access_time_ns),
    }


def query_run_index(session: Session, request: RunIndexQueryRequest) -> RunIndexQueryResult:
    rows = _base_rows(session)
    available_filters = {
        "circuit_types": sorted({str(row.circuit_type or "").strip() for row in rows if str(row.circuit_type or "").strip()}),
        "platforms": sorted({str(row.platform or "").strip() for row in rows if str(row.platform or "").strip()}),
        "statuses": sorted({str(row.status or "").strip() for row in rows if str(row.status or "").strip()}),
    }

    filtered = rows
    if request.circuit_type:
        needle = request.circuit_type.strip()
        filtered = [row for row in filtered if str(row.circuit_type or "").strip() == needle]
    if request.platform:
        needle = request.platform.strip()
        filtered = [row for row in filtered if str(row.platform or "").strip() == needle]
    if request.status:
        needle = request.status.strip()
        filtered = [row for row in filtered if str(row.status or "").strip() == needle]
    if request.design_query:
        needle = request.design_query.strip().lower()
        filtered = [row for row in filtered if needle in str(row.design or "").strip().lower()]

    sort_map = {
        "index_order": lambda row: row.index_order,
        "design": lambda row: str(row.design or ""),
        "critical_path_ns": lambda row: _safe_float_text(row.critical_path_ns) if _safe_float_text(row.critical_path_ns) is not None else float("inf"),
        "die_area": lambda row: _safe_float_text(row.die_area) if _safe_float_text(row.die_area) is not None else float("inf"),
        "total_power_mw": lambda row: _safe_float_text(row.total_power_mw) if _safe_float_text(row.total_power_mw) is not None else float("inf"),
    }
    sort_key = sort_map.get(request.sort_by, sort_map["index_order"])
    filtered = sorted(filtered, key=sort_key, reverse=request.descending)

    start = max(request.offset, 0)
    stop = start + max(1, min(request.limit, 200))
    page_rows = [_row_dict(row) for row in filtered[start:stop]]
    return RunIndexQueryResult(
        total_count=len(rows),
        filtered_count=len(filtered),
        available_filters=available_filters,
        rows=page_rows,
    )


def comparative_run_index(session: Session, *, limit: int) -> RunIndexComparativeResult:
    rows = _base_rows(session)
    if not rows:
        empty_summary = {
            "row_count": 0,
            "ok_row_count": 0,
            "design_count": 0,
            "platform_count": 0,
            "status_counts": {},
        }
        return RunIndexComparativeResult(
            summary=empty_summary,
            families=[],
            best_designs=[],
            family_leaders=[],
            failure_rates=[],
            design_variance=[],
            failure_hotspots=[],
        )

    status_counts: Counter[str] = Counter()
    platforms: set[str] = set()
    family_buckets: dict[str, dict[str, object]] = {}
    design_buckets: dict[tuple[str, str], dict[str, object]] = {}
    leader_buckets: dict[str, dict[str, object]] = {}

    for row in rows:
        circuit_type = str(row.circuit_type or "").strip() or "unknown"
        design = str(row.design or "").strip() or "unknown"
        platform = str(row.platform or "").strip() or "unknown"
        status = str(row.status or "").strip() or "unknown"
        platforms.add(platform)
        status_counts[status] += 1

        family = family_buckets.setdefault(
            circuit_type,
            {"circuit_type": circuit_type, "row_count": 0, "ok_row_count": 0, "designs": set(), "fail_row_count": 0},
        )
        family["row_count"] = int(family["row_count"]) + 1
        family["designs"].add(design)
        if status == "ok":
            family["ok_row_count"] = int(family["ok_row_count"]) + 1
        else:
            family["fail_row_count"] = int(family["fail_row_count"]) + 1

        key = (design, platform)
        bucket = design_buckets.setdefault(
            key,
            {
                "circuit_type": circuit_type,
                "design": design,
                "platform": platform,
                "row_count": 0,
                "ok_row_count": 0,
                "fail_row_count": 0,
                "metrics_path": str(row.metrics_path or "").strip(),
                "_best_score": (float("inf"), float("inf"), float("inf")),
                "best_critical_path_ns": None,
                "best_die_area": None,
                "best_total_power_mw": None,
                "_cp_values": [],
                "_status_counts": Counter(),
            },
        )
        bucket["row_count"] = int(bucket["row_count"]) + 1
        if not bucket["metrics_path"]:
            bucket["metrics_path"] = str(row.metrics_path or "").strip()
        bucket["_status_counts"][status] += 1
        if status != "ok":
            bucket["fail_row_count"] = int(bucket["fail_row_count"]) + 1
            continue

        bucket["ok_row_count"] = int(bucket["ok_row_count"]) + 1
        cp = _comparable_critical_path(row.critical_path_ns)
        if cp is None:
            continue
        bucket["_cp_values"].append(cp)
        area = _safe_float_text(row.die_area)
        power = _safe_float_text(row.total_power_mw)
        score = (
            cp,
            area if area is not None else float("inf"),
            power if power is not None else float("inf"),
        )
        if score < bucket["_best_score"]:
            bucket["_best_score"] = score
            bucket["best_critical_path_ns"] = cp
            bucket["best_die_area"] = area
            bucket["best_total_power_mw"] = power

        leader = leader_buckets.get(circuit_type)
        leader_score = leader["_best_score"] if leader is not None else (float("inf"), float("inf"), float("inf"))
        if score < leader_score:
            leader_buckets[circuit_type] = {
                "circuit_type": circuit_type,
                "design": design,
                "platform": platform,
                "best_critical_path_ns": cp,
                "best_die_area": area,
                "best_total_power_mw": power,
                "_best_score": score,
            }

    summary = {
        "row_count": len(rows),
        "ok_row_count": status_counts.get("ok", 0),
        "design_count": len(design_buckets),
        "platform_count": len(platforms),
        "status_counts": dict(sorted(status_counts.items())),
    }

    families = [
        {
            "circuit_type": bucket["circuit_type"],
            "row_count": int(bucket["row_count"]),
            "ok_row_count": int(bucket["ok_row_count"]),
            "design_count": len(bucket["designs"]),
        }
        for bucket in family_buckets.values()
    ]
    families.sort(key=lambda row: (-int(row["row_count"]), str(row["circuit_type"])))

    best_designs = [
        {
            "circuit_type": bucket["circuit_type"],
            "design": bucket["design"],
            "platform": bucket["platform"],
            "row_count": int(bucket["row_count"]),
            "ok_row_count": int(bucket["ok_row_count"]),
            "best_critical_path_ns": bucket["best_critical_path_ns"],
            "best_die_area": bucket["best_die_area"],
            "best_total_power_mw": bucket["best_total_power_mw"],
            "metrics_path": bucket["metrics_path"],
        }
        for bucket in design_buckets.values()
        if bucket["best_critical_path_ns"] is not None
    ]
    best_designs.sort(
        key=lambda row: (
            row["best_critical_path_ns"] is None,
            row["best_critical_path_ns"] if row["best_critical_path_ns"] is not None else float("inf"),
            row["best_die_area"] if row["best_die_area"] is not None else float("inf"),
            row["best_total_power_mw"] if row["best_total_power_mw"] is not None else float("inf"),
            str(row["design"]),
        )
    )

    family_leaders = [
        {
            "circuit_type": row["circuit_type"],
            "design": row["design"],
            "platform": row["platform"],
            "best_critical_path_ns": row["best_critical_path_ns"],
            "best_die_area": row["best_die_area"],
            "best_total_power_mw": row["best_total_power_mw"],
        }
        for row in leader_buckets.values()
    ]
    family_leaders.sort(
        key=lambda row: (
            row["best_critical_path_ns"] is None,
            row["best_critical_path_ns"] if row["best_critical_path_ns"] is not None else float("inf"),
            str(row["circuit_type"]),
        )
    )

    failure_rates = []
    for bucket in family_buckets.values():
        row_count = int(bucket["row_count"])
        fail_row_count = int(bucket["fail_row_count"])
        failure_rates.append(
            {
                "circuit_type": bucket["circuit_type"],
                "row_count": row_count,
                "fail_row_count": fail_row_count,
                "failure_rate": (fail_row_count / row_count) if row_count else 0.0,
            }
        )
    failure_rates.sort(key=lambda row: (-float(row["failure_rate"]), -int(row["row_count"]), str(row["circuit_type"])))

    design_variance = []
    failure_hotspots = []
    for bucket in design_buckets.values():
        cp_values = sorted(float(value) for value in bucket["_cp_values"])
        if len(cp_values) >= 2:
            cp_mean = _mean(cp_values)
            cp_stddev = _sample_stddev(cp_values)
            design_variance.append(
                {
                    "circuit_type": bucket["circuit_type"],
                    "design": bucket["design"],
                    "platform": bucket["platform"],
                    "comparable_ok_count": len(cp_values),
                    "critical_path_min_ns": cp_values[0],
                    "critical_path_mean_ns": cp_mean,
                    "critical_path_max_ns": cp_values[-1],
                    "critical_path_range_ns": cp_values[-1] - cp_values[0],
                    "critical_path_stddev_ns": cp_stddev,
                    "best_critical_path_ns": bucket["best_critical_path_ns"],
                }
            )

        fail_row_count = int(bucket["fail_row_count"])
        row_count = int(bucket["row_count"])
        if fail_row_count > 0 and row_count > 0:
            status_breakdown = {
                status: count
                for status, count in sorted(bucket["_status_counts"].items())
                if status != "ok"
            }
            failure_hotspots.append(
                {
                    "circuit_type": bucket["circuit_type"],
                    "design": bucket["design"],
                    "platform": bucket["platform"],
                    "fail_row_count": fail_row_count,
                    "row_count": row_count,
                    "failure_rate": fail_row_count / row_count,
                    "ok_row_count": int(bucket["ok_row_count"]),
                    "status_breakdown": status_breakdown,
                }
            )

    design_variance.sort(
        key=lambda row: (
            -(row["critical_path_stddev_ns"] if row["critical_path_stddev_ns"] is not None else 0.0),
            -(row["critical_path_range_ns"] if row["critical_path_range_ns"] is not None else 0.0),
            -int(row["comparable_ok_count"]),
            str(row["design"]),
        )
    )
    failure_hotspots.sort(
        key=lambda row: (
            -float(row["failure_rate"]),
            -int(row["fail_row_count"]),
            str(row["design"]),
        )
    )

    return RunIndexComparativeResult(
        summary=summary,
        families=families[:limit],
        best_designs=best_designs[:limit],
        family_leaders=family_leaders[:limit],
        failure_rates=failure_rates[:limit],
        design_variance=design_variance[:limit],
        failure_hotspots=failure_hotspots[:limit],
    )
