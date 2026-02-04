import math


def _ns_from_seconds(seconds):
    return seconds * 1e9


def _find_sram_instance(addr, instances):
    for inst in instances:
        base = inst.get("base_addr")
        size = inst.get("size_bytes")
        if base is None or size is None:
            continue
        if base <= addr < (base + size):
            return inst
    return None


def _apply_bw_limit(effective_bw_gbps, candidate_bw_gbps):
    if candidate_bw_gbps is None or candidate_bw_gbps <= 0:
        return effective_bw_gbps
    if effective_bw_gbps is None:
        return candidate_bw_gbps
    return min(effective_bw_gbps, candidate_bw_gbps)


def dma_time_ns(bytes_count, cfg, src_addr=None, dst_addr=None):
    bw_gbps = float(cfg.get("dma_bw_gbps", 16.0))
    if bw_gbps <= 0:
        return 0.0
    effective_bw_gbps = bw_gbps
    instances = cfg.get("sram_instances")
    if instances and (src_addr is not None or dst_addr is not None):
        if src_addr is not None:
            src_inst = _find_sram_instance(src_addr, instances)
            if src_inst:
                effective_bw_gbps = _apply_bw_limit(
                    effective_bw_gbps, src_inst.get("read_bw_gbps")
                )
        if dst_addr is not None:
            dst_inst = _find_sram_instance(dst_addr, instances)
            if dst_inst:
                effective_bw_gbps = _apply_bw_limit(
                    effective_bw_gbps, dst_inst.get("write_bw_gbps")
                )
    seconds = bytes_count / (effective_bw_gbps * 1e9)
    return _ns_from_seconds(seconds)


def gemm_time_ns(m, n, k, cfg):
    tops = float(cfg.get("gemm_tops", 2.0))
    if tops <= 0:
        return 0.0
    ops = 2.0 * float(m) * float(n) * float(k)
    seconds = ops / (tops * 1e12)
    return _ns_from_seconds(seconds)


def event_overhead_ns(cfg):
    return float(cfg.get("event_overhead_ns", 50.0))


def noop_overhead_ns(cfg):
    return float(cfg.get("noop_overhead_ns", 10.0))
