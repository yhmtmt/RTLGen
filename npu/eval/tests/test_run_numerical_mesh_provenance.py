from npu.eval.run_numerical_mesh import ROOT, loaded_project_sources


def test_generator_and_checker_transitive_sources_are_pinned():
    paths = loaded_project_sources()
    assert paths == sorted(set(paths))
    assert all(path.is_relative_to(ROOT) and path.is_file() for path in paths)
    relative = {str(path.relative_to(ROOT)) for path in paths}
    assert {
        "npu/eval/run_numerical_mesh.py",
        "npu/eval/numerical_mesh_sidecars.py",
        "npu/eval/prepare_llama7b_score32_exact_shared_mesh_release_replay.py",
        "npu/rtlgen/gen_attention_score32_exact_banked_finalized_tree.py",
        "npu/rtlgen/gen_attention_score32_exact_partial_tree.py",
        "npu/rtlgen/gen_attention_score32_exact_root_finalizer.py",
        "npu/rtlgen/gen_attention_score32_online_state_merge.py",
        "npu/sim/perf/attention_exact_partial.py",
        "npu/sim/perf/noc_endpoint_vc_injection_arbiter.py",
    } <= relative
