import math


def _ns_from_seconds(seconds):
    return seconds * 1e9


def dma_time_ns(bytes_count, cfg):
    bw_gbps = float(cfg.get("dma_bw_gbps", 16.0))
    if bw_gbps <= 0:
        return 0.0
    seconds = bytes_count / (bw_gbps * 1e9)
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
