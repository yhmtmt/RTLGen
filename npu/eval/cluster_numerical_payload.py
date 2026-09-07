"""Validate retained cluster rows before packing numerical mesh inputs."""

from npu.eval.gqa8_compositional_exact import _pack_global_row


def _integer(value: object, low: int, high: int, label: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{label} outside [{low}, {high}]")
    return value


def pack_observed_cluster(cluster: dict, *, expected_cluster: int) -> list[int]:
    """Pack one measured endpoint; never replicate another endpoint's values."""
    if cluster.get("cluster") != expected_cluster or cluster.get("passed") is not True:
        raise ValueError("cluster identity or passing status mismatch")
    audit = cluster.get("exact_row_audit", {})
    if audit.get("passed") is not True or any(
        audit.get(key) != 512 for key in ("expected_row_count", "observed_row_count")
    ):
        raise ValueError("missing complete exact-row audit")
    rows = cluster.get("observed_rows")
    groups = cluster.get("groups")
    if not isinstance(rows, list) or len(rows) != 512:
        raise ValueError("512 observed numerical rows required")
    if not isinstance(groups, list) or len(groups) != 4:
        raise ValueError("four group identities required")
    packed = []
    for index, row in enumerate(rows):
        group_index, offset = divmod(index, 128)
        group = groups[group_index]
        if row.get("cluster") != expected_cluster:
            raise ValueError("row belongs to another cluster")
        command = _integer(row.get("command_id"), 0, 65535, "command")
        head = _integer(row.get("head_id"), 0, 31, "head")
        slice_index = _integer(row.get("slice"), 0, 15, "slice")
        if (group.get("logical_group") != group_index
            or command != group.get("command_id")
            or group.get("head_base") != group_index * 8
            or head != group_index * 8 + offset // 16
            or slice_index != offset % 16
            or type(row.get("last")) is not bool
            or row["last"] != (offset % 16 == 15)):
            raise ValueError("row order or group metadata mismatch")
        _integer(row.get("global_max"), -(1 << 31), (1 << 31) - 1, "max")
        _integer(row.get("exp_sum"), 0, (1 << 33) - 1, "sum")
        values = row.get("value")
        if not isinstance(values, list) or len(values) != 8:
            raise ValueError("eight numerator lanes required")
        for value in values:
            _integer(value, -(1 << 40), (1 << 40) - 1, "numerator")
        packed.append(_pack_global_row(row))
    return packed


def pack_all_endpoints(clusters: list[dict]) -> list[int]:
    """Return endpoint-major words only when every endpoint has its own rows."""
    if len(clusters) != 16:
        raise ValueError("all sixteen endpoint streams required")
    by_endpoint = {}
    for cluster in clusters:
        endpoint = _integer(cluster.get("cluster"), 0, 15, "endpoint")
        if endpoint in by_endpoint:
            raise ValueError("duplicate endpoint stream")
        by_endpoint[endpoint] = cluster
    words = []
    commands = None
    for endpoint in range(16):
        cluster = by_endpoint[endpoint]
        endpoint_words = pack_observed_cluster(cluster, expected_cluster=endpoint)
        endpoint_commands = [group["command_id"] for group in cluster["groups"]]
        if commands is None:
            commands = endpoint_commands
        elif commands != endpoint_commands:
            raise ValueError("endpoint command identities differ")
        words.extend(endpoint_words)
    return words
