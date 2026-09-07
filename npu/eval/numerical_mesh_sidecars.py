"""Serialize validated leaf payloads and exact finalized root expectations."""

from npu.eval.cluster_numerical_payload import _integer, pack_all_endpoints


def build_sidecars(report: dict) -> dict[str, str]:
    if report.get("model") != "score32_all_cluster_numerical_payloads_v1" or report.get("passed") is not True:
        raise ValueError("passing all-cluster collection required")
    clusters = report["clusters"]
    leaves = pack_all_endpoints(clusters)
    release_cycles = []
    for cluster in sorted(clusters, key=lambda c: c["cluster"]):
        cycles = []
        for group in cluster["groups"]:
            rows = group.get("output_cycles")
            if not isinstance(rows, list) or len(rows) != 128:
                raise ValueError("128 measured cycles per group required")
            cycles.extend(_integer(c, 1, (1 << 31) - 1, "release cycle") for c in rows)
        if any(b <= a for a, b in zip(cycles, cycles[1:])):
            raise ValueError("endpoint release cycles must increase")
        release_cycles.extend(cycles)
    groups = clusters[0]["groups"]
    commands = [g["command_id"] for g in groups]
    if commands != list(range(commands[0], commands[0] + 4)):
        raise ValueError("mesh requires four consecutive command identities")
    roots = report.get("expected_root_rows")
    if not isinstance(roots, list) or len(roots) != 512:
        raise ValueError("512 exact root rows required")
    root_words = []
    for index, row in enumerate(roots):
        if (row.get("command_id") != commands[index // 128]
            or row.get("head_id") != index // 16
            or row.get("slice") != index % 16
            or type(row.get("last")) is not bool
            or row["last"] != (index % 16 == 15)):
            raise ValueError("root metadata mismatch")
        values = row.get("value")
        if not isinstance(values, list) or len(values) != 8:
            raise ValueError("eight finalized lanes required")
        word = row["command_id"] | (row["head_id"] << 16) | (row["slice"] << 21) | (int(row["last"]) << 25)
        for lane, value in enumerate(values):
            value = _integer(value, -(1 << 39), (1 << 39) - 1, "finalized lane")
            word |= (value & ((1 << 40) - 1)) << (26 + lane * 40)
        root_words.append(word)
    return {
        "leaf_memh": "".join(f"{word:0105x}\n" for word in leaves),
        "root_memh": "".join(f"{word:087x}\n" for word in root_words),
        "release_memh": "".join(f"{cycle:08x}\n" for cycle in release_cycles),
        "command_base": str(commands[0]),
    }
