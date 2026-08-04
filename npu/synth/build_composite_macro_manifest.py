#!/usr/bin/env python3
"""Compose multiple hardened macro manifests into one top-level macro bundle manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


JsonDict = dict[str, Any]


def _load_json(path: Path) -> JsonDict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit(f"macro manifest must decode to a JSON object: {path}")
    return payload


def _parse_key_value_list(values: list[str]) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for raw in values:
        token = str(raw).strip()
        if not token:
            continue
        if "=" not in token:
            raise SystemExit(f"invalid manifest_param token (expected key=value): {raw}")
        key, value = token.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            raise SystemExit(f"invalid empty manifest_param key: {raw}")
        parsed[key] = value
    return parsed


def _append_unique(target: list[str], values: list[str]) -> None:
    for value in values:
        text = str(value).strip()
        if text and text not in target:
            target.append(text)


def build_manifest(
    *,
    design_id: str,
    module: str,
    platform: str,
    component_manifest_paths: list[str],
    flow_variant: str,
    source_config: str,
    source_generator: str,
    manifest_params: dict[str, str],
) -> JsonDict:
    if not component_manifest_paths:
        raise SystemExit("at least one --component-manifest is required")

    additional_lefs: list[str] = []
    additional_libs: list[str] = []
    additional_gds: list[str] = []
    blackboxes: list[str] = []
    blackbox_verilog: list[str] = []

    for manifest_path_text in component_manifest_paths:
        manifest = _load_json(Path(manifest_path_text))
        manifest_platform = str(manifest.get("platform", "")).strip()
        if manifest_platform and manifest_platform != platform:
            raise SystemExit(
                f"component manifest platform mismatch for {manifest_path_text}: "
                f"expected {platform}, found {manifest_platform}"
            )
        _append_unique(additional_lefs, [str(x) for x in manifest.get("additional_lefs", [])])
        _append_unique(additional_libs, [str(x) for x in manifest.get("additional_libs", [])])
        _append_unique(additional_gds, [str(x) for x in manifest.get("additional_gds", [])])
        _append_unique(blackboxes, [str(x) for x in manifest.get("blackboxes", [])])
        _append_unique(blackbox_verilog, [str(x) for x in manifest.get("blackbox_verilog", [])])

    manifest: JsonDict = {
        "version": "0.1",
        "design_id": design_id,
        "module": module,
        "platform": platform,
        "flow_variant": flow_variant,
        "blackboxes": blackboxes,
        "additional_lefs": additional_lefs,
        "additional_libs": additional_libs,
        "additional_gds": additional_gds,
        "blackbox_verilog": blackbox_verilog,
        "source": {
            "mode": "composite_macro_bundle",
            "config": source_config,
            "generator": source_generator,
            "component_manifests": component_manifest_paths,
        },
        "manifest_params": manifest_params,
        "make_target": "generate_abstract",
    }
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--design-id", required=True)
    parser.add_argument("--module", required=True)
    parser.add_argument("--platform", required=True)
    parser.add_argument("--flow-variant", default="base")
    parser.add_argument("--source-config", required=True)
    parser.add_argument("--source-generator", required=True)
    parser.add_argument("--component-manifest", action="append", default=[])
    parser.add_argument("--manifest-param", action="append", default=[])
    args = parser.parse_args()

    manifest = build_manifest(
        design_id=str(args.design_id).strip(),
        module=str(args.module).strip(),
        platform=str(args.platform).strip(),
        component_manifest_paths=[str(Path(path)) for path in args.component_manifest],
        flow_variant=str(args.flow_variant).strip() or "base",
        source_config=str(args.source_config).strip(),
        source_generator=str(args.source_generator).strip(),
        manifest_params=_parse_key_value_list(args.manifest_param),
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
