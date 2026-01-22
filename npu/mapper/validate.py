#!/usr/bin/env python3
import sys

try:
    import yaml  # type: ignore
except Exception:
    print("Missing dependency: PyYAML is required to parse .yml files.", file=sys.stderr)
    sys.exit(2)


def die(msg: str) -> None:
    print(f"validate: {msg}", file=sys.stderr)
    sys.exit(1)


def validate_doc(doc: dict) -> None:
    if not isinstance(doc, dict):
        raise ValueError("top-level must be a mapping")
    if doc.get("version") != 0.1:
        raise ValueError("version must be 0.1")

    buffers = doc.get("buffers", [])
    if not isinstance(buffers, list):
        raise ValueError("buffers must be a list")
    buffer_ids = {b.get("id") for b in buffers if isinstance(b, dict)}
    if any(bid is None for bid in buffer_ids):
        raise ValueError("buffer entries must include id")

    ops = doc.get("ops", [])
    if not isinstance(ops, list):
        raise ValueError("ops must be a list")
    op_ids = []
    for op in ops:
        if not isinstance(op, dict):
            raise ValueError("op entries must be mappings")
        oid = op.get("id")
        if not oid:
            raise ValueError("op missing id")
        op_ids.append(oid)
        otype = op.get("type")
        if not otype:
            raise ValueError(f"op {oid} missing type")
        if otype in ("dma_copy", "vec_op", "softmax", "gemm"):
            for key in ("src", "dst"):
                if otype == "dma_copy" and op.get(key) not in buffer_ids:
                    raise ValueError(f"op {oid} references unknown buffer {op.get(key)}")
        if otype == "gemm":
            for key in ("a", "b", "c"):
                if op.get(key) not in buffer_ids:
                    raise ValueError(f"op {oid} references unknown buffer {op.get(key)}")

    if len(op_ids) != len(set(op_ids)):
        raise ValueError("op ids must be unique")

    deps = doc.get("deps", [])
    if deps:
        if not isinstance(deps, list):
            raise ValueError("deps must be a list")
        for dep in deps:
            if not isinstance(dep, dict):
                raise ValueError("dep entries must be mappings")
            waits = dep.get("wait", [])
            then = dep.get("then")
            for w in waits:
                if w not in op_ids:
                    raise ValueError(f"dep references unknown op {w}")
            if then not in op_ids:
                raise ValueError(f"dep references unknown op {then}")


def validate_file(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        doc = yaml.safe_load(f)
    validate_doc(doc)
    return doc


def main() -> int:
    if len(sys.argv) != 2:
        die("usage: npu/mapper/validate.py <schedule.yml>")
    path = sys.argv[1]
    try:
        validate_file(path)
    except Exception as exc:
        die(str(exc))
    return 0


if __name__ == "__main__":
    sys.exit(main())
