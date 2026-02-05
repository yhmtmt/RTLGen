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

    tile_m = int(cfg.get("gemm_tile_m", 64))
    tile_n = int(cfg.get("gemm_tile_n", 64))
    tile_k = int(cfg.get("gemm_tile_k", 32))
    if tile_m <= 0 or tile_n <= 0 or tile_k <= 0:
        tile_m, tile_n, tile_k = 64, 64, 32

    macs = float(m) * float(n) * float(k)
    compute_seconds = (2.0 * macs) / (tops * 1e12)

    in_bw = float(cfg.get("gemm_in_bw_gbps", cfg.get("dma_bw_gbps", 16.0)))
    out_bw = float(cfg.get("gemm_out_bw_gbps", cfg.get("dma_bw_gbps", 16.0)))
    dtype_bytes = float(cfg.get("gemm_dtype_bytes", 1.0))
    input_bytes = dtype_bytes * (float(m) * float(k) + float(k) * float(n))
    output_bytes = dtype_bytes * (float(m) * float(n))
    mem_seconds = 0.0
    if in_bw > 0:
        mem_seconds += input_bytes / (in_bw * 1e9)
    if out_bw > 0:
        mem_seconds += output_bytes / (out_bw * 1e9)

    tile_overhead_ns = float(cfg.get("gemm_tile_overhead_ns", 0.0))
    tiles = (
        math.ceil(float(m) / tile_m)
        * math.ceil(float(n) / tile_n)
        * math.ceil(float(k) / tile_k)
    )
    overhead_seconds = (tile_overhead_ns * tiles) / 1e9

    seconds = max(compute_seconds, mem_seconds) + overhead_seconds
    return _ns_from_seconds(seconds)


def event_overhead_ns(cfg):
    return float(cfg.get("event_overhead_ns", 50.0))


def noop_overhead_ns(cfg):
    return float(cfg.get("noop_overhead_ns", 10.0))
