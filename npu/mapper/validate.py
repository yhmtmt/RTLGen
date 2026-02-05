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


def _is_number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _is_int(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _parse_int(value):
    if _is_int(value):
        return value
    if isinstance(value, str):
        return int(value, 0)
    raise ValueError("expected int or int-like string")


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


def validate_contract_doc(doc: dict) -> None:
    if not isinstance(doc, dict):
        raise ValueError("top-level must be a mapping")
    if doc.get("version") != 0.1:
        raise ValueError("version must be 0.1")
    if not isinstance(doc.get("arch"), str):
        raise ValueError("arch must be a string path")

    model = doc.get("model")
    if not isinstance(model, dict):
        raise ValueError("model must be a mapping")
    if not isinstance(model.get("name"), str):
        raise ValueError("model.name must be a string")
    if not isinstance(model.get("graph"), str):
        raise ValueError("model.graph must be a string path")
    inputs = model.get("inputs", [])
    if not isinstance(inputs, list):
        raise ValueError("model.inputs must be a list")
    for entry in inputs:
        if not isinstance(entry, dict):
            raise ValueError("model.inputs entries must be mappings")
        if not isinstance(entry.get("name"), str):
            raise ValueError("model.inputs.name must be a string")
        shape = entry.get("shape")
        if not isinstance(shape, list) or not shape:
            raise ValueError("model.inputs.shape must be a non-empty list")
        for dim in shape:
            if not _is_int(dim):
                raise ValueError("model.inputs.shape must be ints")
        if not isinstance(entry.get("dtype"), str):
            raise ValueError("model.inputs.dtype must be a string")

    targets = doc.get("targets")
    if not isinstance(targets, dict):
        raise ValueError("targets must be a mapping")
    mem_spaces = targets.get("memory_spaces", [])
    if not isinstance(mem_spaces, list) or not mem_spaces:
        raise ValueError("targets.memory_spaces must be a non-empty list")
    for space in mem_spaces:
        if not isinstance(space, dict):
            raise ValueError("memory_spaces entries must be mappings")
        if not isinstance(space.get("name"), str):
            raise ValueError("memory_spaces.name must be a string")
        for key in ("base_addr", "bytes"):
            if key not in space:
                raise ValueError(f"memory_spaces.{key} is required")
            _parse_int(space[key])

    dma = targets.get("dma", {})
    if not isinstance(dma, dict):
        raise ValueError("targets.dma must be a mapping")
    if "max_read_bw_gbps" in dma and not _is_number(dma["max_read_bw_gbps"]):
        raise ValueError("targets.dma.max_read_bw_gbps must be a number")
    if "max_write_bw_gbps" in dma and not _is_number(dma["max_write_bw_gbps"]):
        raise ValueError("targets.dma.max_write_bw_gbps must be a number")

    compute = targets.get("compute", {})
    if not isinstance(compute, dict):
        raise ValueError("targets.compute must be a mapping")
    gemm = compute.get("gemm", {})
    if gemm:
        if not isinstance(gemm, dict):
            raise ValueError("targets.compute.gemm must be a mapping")
        for key in ("m_tile", "n_tile", "k_tile"):
            if key not in gemm:
                raise ValueError(f"targets.compute.gemm.{key} is required")
            if not _is_int(gemm[key]):
                raise ValueError(f"targets.compute.gemm.{key} must be an int")

    constraints = doc.get("constraints", {})
    if constraints:
        if not isinstance(constraints, dict):
            raise ValueError("constraints must be a mapping")
        if "max_cq_depth" in constraints and not _is_int(constraints["max_cq_depth"]):
            raise ValueError("constraints.max_cq_depth must be an int")
        if "alignment_bytes" in constraints and not _is_int(constraints["alignment_bytes"]):
            raise ValueError("constraints.alignment_bytes must be an int")


def validate_file(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        doc = yaml.safe_load(f)
    validate_doc(doc)
    return doc


def main() -> int:
    args = sys.argv[1:]
    if not args or len(args) > 2:
        die("usage: npu/mapper/validate.py [--contract] <schedule.yml|contract.yml>")
    contract_mode = False
    if args[0] == "--contract":
        contract_mode = True
        args = args[1:]
    if len(args) != 1:
        die("usage: npu/mapper/validate.py [--contract] <schedule.yml|contract.yml>")
    path = args[0]
    try:
        with open(path, "r", encoding="utf-8") as f:
            doc = yaml.safe_load(f)
        if contract_mode or ("model" in doc or "targets" in doc):
            validate_contract_doc(doc)
        else:
            validate_doc(doc)
    except Exception as exc:
        die(str(exc))
    return 0


if __name__ == "__main__":
    sys.exit(main())
