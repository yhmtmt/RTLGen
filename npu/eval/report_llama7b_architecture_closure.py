#!/usr/bin/env python3
"""Validate and render the persistent Llama7B architecture closure matrix."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = REPO_ROOT / "npu/docs/llama7b_architecture_closure.json"
DEFAULT_OUTPUT = REPO_ROOT / "npu/docs/generated/llama7b_architecture_closure.md"

REQUIRED_COMPONENTS = [
    "precision",
    "dense_compute",
    "norm",
    "score_softmax",
    "multivalue_service",
    "reducer",
    "producer_service_reducer_composition",
    "noc",
    "sram",
    "scheduler_cdc",
    "external_memory_boundary",
    "full_llama7b_recost",
]
REQUIRED_DIMENSIONS = [
    "rtl",
    "equivalence",
    "routed_ppa",
    "activity",
    "composition",
    "scale_validation",
]
STATUS_VOCAB = {
    "closed",
    "routed_with_caveat",
    "measured_component",
    "rtl_unmeasured",
    "abstract_external",
    "open",
}
CONFIDENCE_VOCAB = {"high", "medium", "low"}
PASSLIKE_STATUSES = {"closed", "routed_with_caveat", "measured_component", "abstract_external"}
UNRESOLVED_STATUSES = {"open", "rtl_unmeasured"}


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: expected top-level JSON object")
    return payload


def _rel_to_repo(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path.resolve())


def _status_count(components: list[dict[str, Any]]) -> dict[str, int]:
    counts = {status: 0 for status in STATUS_VOCAB}
    for component in components:
        status = str(component.get("status", "")).strip()
        if status in counts:
            counts[status] += 1
    return counts


def _dimension_summary(component: dict[str, Any], dimension: str) -> dict[str, Any]:
    dims = component.get("dimensions")
    if not isinstance(dims, dict):
        return {}
    payload = dims.get(dimension)
    return payload if isinstance(payload, dict) else {}


def _evidence_dimensions(component: dict[str, Any]) -> set[str]:
    covered: set[str] = set()
    evidence = component.get("evidence")
    if not isinstance(evidence, list):
        return covered
    for entry in evidence:
        if not isinstance(entry, dict):
            continue
        dims = entry.get("dimensions")
        if not isinstance(dims, list):
            continue
        for dimension in dims:
            if isinstance(dimension, str):
                covered.add(dimension)
    return covered


def validate_matrix(matrix: dict[str, Any], *, repo_root: Path = REPO_ROOT) -> list[str]:
    errors: list[str] = []

    components = matrix.get("components")
    if not isinstance(components, list):
        return ["components: expected list"]

    if matrix.get("component_order") != REQUIRED_COMPONENTS:
        errors.append("component_order must exactly match the required Llama7B closure component order")
    if matrix.get("dimension_order") != REQUIRED_DIMENSIONS:
        errors.append("dimension_order must exactly match the required closure dimensions")

    status_vocab = matrix.get("status_vocabulary")
    if status_vocab != sorted(STATUS_VOCAB):
        errors.append("status_vocabulary must match the supported closure status set")
    confidence_vocab = matrix.get("confidence_vocabulary")
    if confidence_vocab != sorted(CONFIDENCE_VOCAB):
        errors.append("confidence_vocabulary must match the supported confidence set")

    generated_markdown = matrix.get("generated_markdown")
    if not isinstance(generated_markdown, str) or not generated_markdown.strip():
        errors.append("generated_markdown must be a non-empty repo-relative path")

    recommended = matrix.get("recommended_architecture")
    if not isinstance(recommended, dict):
        errors.append("recommended_architecture must be an object")
    else:
        why_provisional = recommended.get("why_provisional")
        if not isinstance(why_provisional, list) or not why_provisional:
            errors.append("recommended_architecture.why_provisional must be a non-empty list")

    seen_ids: set[str] = set()
    component_ids: list[str] = []
    for component in components:
        if not isinstance(component, dict):
            errors.append("components entries must be objects")
            continue

        component_id = str(component.get("id", "")).strip()
        component_ids.append(component_id)
        if component_id in seen_ids:
            errors.append(f"component {component_id}: duplicate id")
        seen_ids.add(component_id)
        if component_id not in REQUIRED_COMPONENTS:
            errors.append(f"component {component_id}: unsupported component id")

        status = str(component.get("status", "")).strip()
        if status not in STATUS_VOCAB:
            errors.append(f"component {component_id}: unsupported status {status!r}")

        confidence = str(component.get("confidence", "")).strip()
        if confidence not in CONFIDENCE_VOCAB:
            errors.append(f"component {component_id}: unsupported confidence {confidence!r}")

        summary = component.get("summary")
        if not isinstance(summary, str) or not summary.strip():
            errors.append(f"component {component_id}: summary must be a non-empty string")

        next_gate = component.get("next_gate")
        if not isinstance(next_gate, str) or not next_gate.strip():
            errors.append(f"component {component_id}: next_gate must be a non-empty string")

        caveats = component.get("caveats")
        if not isinstance(caveats, list):
            errors.append(f"component {component_id}: caveats must be a list")

        dimensions = component.get("dimensions")
        if not isinstance(dimensions, dict):
            errors.append(f"component {component_id}: dimensions must be an object")
            continue
        if list(dimensions.keys()) != REQUIRED_DIMENSIONS:
            errors.append(f"component {component_id}: dimensions must match the required order")

        for dimension in REQUIRED_DIMENSIONS:
            dim_payload = _dimension_summary(component, dimension)
            if not dim_payload:
                errors.append(f"component {component_id}: missing dimension {dimension}")
                continue
            dim_status = str(dim_payload.get("status", "")).strip()
            if dim_status not in STATUS_VOCAB:
                errors.append(f"component {component_id}.{dimension}: unsupported status {dim_status!r}")
            dim_summary = dim_payload.get("summary")
            if not isinstance(dim_summary, str) or not dim_summary.strip():
                errors.append(f"component {component_id}.{dimension}: summary must be a non-empty string")
            if dim_status == "abstract_external" and component_id != "external_memory_boundary":
                errors.append(
                    f"component {component_id}.{dimension}: abstract_external is reserved for external_memory_boundary"
                )

        evidence = component.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            errors.append(f"component {component_id}: evidence must be a non-empty list")
            continue
        for index, entry in enumerate(evidence):
            if not isinstance(entry, dict):
                errors.append(f"component {component_id}: evidence[{index}] must be an object")
                continue
            rel_path = entry.get("path")
            if not isinstance(rel_path, str) or not rel_path.strip():
                errors.append(f"component {component_id}: evidence[{index}] path must be a non-empty string")
                continue
            full_path = repo_root / rel_path
            if not full_path.exists():
                errors.append(f"component {component_id}: evidence path does not exist: {rel_path}")
            dims = entry.get("dimensions")
            if not isinstance(dims, list) or not dims:
                errors.append(f"component {component_id}: evidence[{index}] dimensions must be a non-empty list")
            else:
                for dimension in dims:
                    if dimension not in REQUIRED_DIMENSIONS:
                        errors.append(
                            f"component {component_id}: evidence[{index}] references unsupported dimension {dimension!r}"
                        )

        if component_id == "external_memory_boundary":
            if status != "abstract_external":
                errors.append("component external_memory_boundary: status must be abstract_external")
            for dimension in REQUIRED_DIMENSIONS:
                if _dimension_summary(component, dimension).get("status") != "abstract_external":
                    errors.append(
                        f"component external_memory_boundary.{dimension}: expected abstract_external status"
                    )
        elif status == "abstract_external":
            errors.append(f"component {component_id}: only external_memory_boundary may use abstract_external")

        if status == "closed":
            for dimension in REQUIRED_DIMENSIONS:
                dim_status = _dimension_summary(component, dimension).get("status")
                if dim_status != "closed":
                    errors.append(
                        f"component {component_id}: unsupported closure, overall closed but {dimension}={dim_status!r}"
                    )
        if status == "routed_with_caveat":
            routed_status = _dimension_summary(component, "routed_ppa").get("status")
            if routed_status != "routed_with_caveat":
                errors.append(
                    f"component {component_id}: routed_with_caveat requires routed_ppa=routed_with_caveat"
                )
            if not component.get("caveats"):
                errors.append(f"component {component_id}: routed_with_caveat requires at least one caveat")
        elif _dimension_summary(component, "routed_ppa").get("status") == "routed_with_caveat":
            errors.append(
                f"component {component_id}: routed_ppa=routed_with_caveat requires overall status routed_with_caveat"
            )

        coverage = _evidence_dimensions(component)
        for dimension in REQUIRED_DIMENSIONS:
            dim_status = str(_dimension_summary(component, dimension).get("status", "")).strip()
            if dim_status in PASSLIKE_STATUSES and dimension not in coverage:
                errors.append(
                    f"component {component_id}: unsupported closure for {dimension}, no evidence entry references it"
                )

        if status == "measured_component":
            measured_dims = {
                "routed_ppa",
                "activity",
                "composition",
                "scale_validation",
            }
            if not any(
                str(_dimension_summary(component, dim).get("status", "")).strip()
                in {"closed", "routed_with_caveat", "measured_component"}
                for dim in measured_dims
            ):
                errors.append(
                    f"component {component_id}: measured_component requires at least one measured/routed downstream dimension"
                )
        if status == "rtl_unmeasured":
            if str(_dimension_summary(component, "rtl").get("status", "")).strip() not in {"closed", "rtl_unmeasured"}:
                errors.append(f"component {component_id}: rtl_unmeasured requires an RTL implementation path")
        if status == "open":
            if all(
                str(_dimension_summary(component, dim).get("status", "")).strip() in PASSLIKE_STATUSES
                for dim in REQUIRED_DIMENSIONS
            ):
                errors.append(f"component {component_id}: open status is unsupported when every dimension is closed/measured")

        if component_id == "multivalue_service":
            accepted = component.get("accepted_routed_result")
            if not isinstance(accepted, dict):
                errors.append("component multivalue_service: accepted_routed_result is required")
            else:
                required_fields = {
                    "tag",
                    "critical_path_ns",
                    "die_area_mm2",
                    "core_area_mm2",
                    "instance_area_mm2",
                    "stdcell_area_mm2",
                    "stdcell_count",
                    "utilization_pct",
                    "vectorless_power_mw",
                    "max_cap_violations",
                    "worst_max_cap_ff",
                }
                missing = sorted(field for field in required_fields if field not in accepted)
                if missing:
                    errors.append(
                        "component multivalue_service: accepted_routed_result missing fields "
                        + ", ".join(missing)
                    )

    if component_ids != REQUIRED_COMPONENTS:
        errors.append("components must appear exactly once and in the required order")

    output_path = repo_root / str(generated_markdown or DEFAULT_OUTPUT)
    if output_path.parent != DEFAULT_OUTPUT.parent:
        errors.append("generated_markdown must stay under npu/docs/generated")
    return errors


def render_markdown(matrix: dict[str, Any], *, repo_root: Path = REPO_ROOT) -> str:
    components = matrix["components"]
    counts = _status_count(components)
    recommended = matrix["recommended_architecture"]
    generated_markdown = matrix["generated_markdown"]

    lines: list[str] = []
    lines.append("# Llama7B Architecture Closure Matrix")
    lines.append("")
    lines.append(f"- source JSON: `{_rel_to_repo(DEFAULT_INPUT)}`")
    lines.append(f"- generated Markdown: `{generated_markdown}`")
    lines.append(f"- as_of: `{matrix['as_of']}`")
    lines.append("")
    lines.append("## Headline")
    lines.append("")
    lines.append(
        "- closure counts: "
        f"`closed={counts['closed']}`, "
        f"`routed_with_caveat={counts['routed_with_caveat']}`, "
        f"`measured_component={counts['measured_component']}`, "
        f"`rtl_unmeasured={counts['rtl_unmeasured']}`, "
        f"`abstract_external={counts['abstract_external']}`, "
        f"`open={counts['open']}`"
    )
    lines.append(
        "- provisional recommendation: "
        f"`{recommended['compute']}` + `{recommended['score_path']}`, "
        f"`{recommended['service_topology']}`, `{recommended['clocking']}`"
    )
    for reason in recommended["why_provisional"]:
        lines.append(f"- provisional because: {reason}")
    lines.append("")
    lines.append("## Component Status")
    lines.append("")
    lines.append(
        "| Component | Status | Confidence | RTL | Equivalence | Routed PPA | Activity | Composition | Scale |"
    )
    lines.append(
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"
    )
    for component in components:
        dims = component["dimensions"]
        lines.append(
            "| "
            + " | ".join(
                [
                    component["label"],
                    component["status"],
                    component["confidence"],
                    dims["rtl"]["status"],
                    dims["equivalence"]["status"],
                    dims["routed_ppa"]["status"],
                    dims["activity"]["status"],
                    dims["composition"]["status"],
                    dims["scale_validation"]["status"],
                ]
            )
            + " |"
        )
    lines.append("")
    for component in components:
        lines.append(f"## {component['label']}")
        lines.append("")
        lines.append(f"- status: `{component['status']}`")
        lines.append(f"- confidence: `{component['confidence']}`")
        lines.append(f"- summary: {component['summary']}")
        lines.append(f"- next gate: {component['next_gate']}")
        if component["id"] == "multivalue_service":
            accepted = component["accepted_routed_result"]
            lines.append("- accepted c1 routed result:")
            lines.append(f"  - tag: `{accepted['tag']}`")
            lines.append(f"  - critical path: `{accepted['critical_path_ns']} ns`")
            lines.append(f"  - die/core: `{accepted['die_area_mm2']} mm2` / `{accepted['core_area_mm2']} mm2`")
            lines.append(
                f"  - instance/stdcell: `{accepted['instance_area_mm2']} mm2` / "
                f"`{accepted['stdcell_area_mm2']} mm2`, `{accepted['stdcell_count']} cells`"
            )
            lines.append(
                f"  - utilization/vectorless power: `{accepted['utilization_pct']}%` / "
                f"`{accepted['vectorless_power_mw']} mW`"
            )
            lines.append(
                f"  - route health: `DRC/setup/hold/slew clean`, but "
                f"`{accepted['max_cap_violations']}` max-cap violations, worst `{accepted['worst_max_cap_ff']} fF`"
            )
        lines.append("")
        lines.append("| Dimension | Status | Summary |")
        lines.append("| --- | --- | --- |")
        for dimension in REQUIRED_DIMENSIONS:
            dim_payload = component["dimensions"][dimension]
            lines.append(
                f"| `{dimension}` | `{dim_payload['status']}` | {dim_payload['summary']} |"
            )
        lines.append("")
        if component["caveats"]:
            lines.append("Caveats:")
            for caveat in component["caveats"]:
                lines.append(f"- {caveat}")
            lines.append("")
        lines.append("Evidence:")
        for evidence in component["evidence"]:
            dims = ", ".join(f"`{dim}`" for dim in evidence["dimensions"])
            lines.append(
                f"- `{_rel_to_repo(repo_root / evidence['path'])}` ({evidence['kind']}; {dims}): {evidence['note']}"
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="Source closure JSON")
    parser.add_argument("--output-md", type=Path, default=DEFAULT_OUTPUT, help="Rendered Markdown output")
    parser.add_argument(
        "--write-markdown",
        action="store_true",
        help="Write the rendered Markdown to --output-md after validation",
    )
    parser.add_argument(
        "--check-markdown",
        action="store_true",
        help="Fail if --output-md does not match the rendered Markdown",
    )
    args = parser.parse_args(argv)

    matrix = _load_json(args.input)
    errors = validate_matrix(matrix)
    if errors:
        for error in errors:
            print(f"[llama7b_closure] ERROR: {error}", file=sys.stderr)
        return 1

    rendered = render_markdown(matrix)
    if args.write_markdown:
        args.output_md.parent.mkdir(parents=True, exist_ok=True)
        args.output_md.write_text(rendered, encoding="utf-8")
    if args.check_markdown:
        current = args.output_md.read_text(encoding="utf-8") if args.output_md.exists() else ""
        if current != rendered:
            print(
                "[llama7b_closure] ERROR: rendered Markdown does not match committed output",
                file=sys.stderr,
            )
            return 1
    if not args.write_markdown and not args.check_markdown:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
