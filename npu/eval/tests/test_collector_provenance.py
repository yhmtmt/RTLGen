from npu.eval.collect_score32_cluster_payloads import ROOT, loaded_project_sources


def test_collector_pins_transitive_rtl_and_reference_dependencies():
    paths = {str(p.relative_to(ROOT)) for p in loaded_project_sources()}
    for path in (
        "npu/rtlgen/gen_attention_score32_exact_partial_tree.py",
        "npu/rtlgen/gen_attention_score32_exact_root_finalizer.py",
        "npu/sim/perf/attention_exact_partial.py",
        "npu/eval/collect_score32_cluster_payloads.py",
    ):
        assert path in paths
