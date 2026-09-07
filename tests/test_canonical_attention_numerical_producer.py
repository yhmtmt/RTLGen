import json
import shutil

import pytest

from npu.eval.canonical_attention_producer_inputs import CanonicalProducerInputs
from npu.eval.canonical_attention_staged_inputs import CanonicalStagedInputs
from npu.eval.canonical_attention_transposed_inputs import CanonicalTransposedInputs
from npu.eval.canonical_attention_value_inputs import CanonicalValueIngressInputs
from npu.eval.canonical_attention_sram_inputs import CanonicalSramInputs
from npu.eval.probe_attention_score32_exact_partial_gqa8_dual_stream_producer import build_report, compact_report


@pytest.mark.parametrize("producers", [53, 54])
@pytest.mark.parametrize("assignment", range(5))
def test_canonical_tensor_numerical_producer(tmp_path, producers, assignment):
    if not shutil.which("iverilog") or not shutil.which("vvp"):
        pytest.skip("Icarus unavailable")
    # One representative for each rotated extra-block group, plus the final
    # single-block producer. This distinguishes the p53/p54 slot mappings.
    producer = assignment * (64 - producers) if assignment < 4 else producers - 1
    inputs = CanonicalProducerInputs(producers=producers, producer=producer)
    report = build_report(heads=32, command_count=4, head_dim=128,
        head_bases=(0, 8, 16, 24), block_counts_per_stream=inputs.counts(),
        stress_interfaces=True, input_provider=inputs)
    (tmp_path / "result.json").write_text(json.dumps(compact_report(report), indent=2) + "\n")
    assert report["passed"]
    assert report["outputs"] == report["expected_outputs"] == 512
    assert report["input_fixture"] == inputs.identity()
    assert report["llama_wave_reference_cycles"] is None
    assert report["llama_wave_drain_delta_vs_986"] is None
    assert not report["protocol_error"]


def test_canonical_provider_rejects_truncated_workload():
    inputs = CanonicalProducerInputs(producers=53, producer=0)
    with pytest.raises(ValueError, match="four full-dimension"):
        inputs.validate_workload(dict(head_dim=16, command_count=4,
            head_bases=(0, 8, 16, 24), block_counts_per_stream=inputs.counts()))


@pytest.mark.parametrize("producers", [53, 54])
@pytest.mark.parametrize("with_transpose", [False, True, "kv", "sram"])
def test_live_canonical_kq_stage_to_numerical_producer(tmp_path, producers, with_transpose):
    if not shutil.which("iverilog") or not shutil.which("vvp"):
        pytest.skip("Icarus unavailable")
    provider = CanonicalTransposedInputs if with_transpose else CanonicalStagedInputs
    if with_transpose == "kv":
        provider = CanonicalValueIngressInputs
    if with_transpose == "sram":
        provider = CanonicalSramInputs
    inputs = provider(producers=producers, producer=64-producers)
    report = build_report(heads=32, command_count=4, head_dim=128,
        head_bases=(0, 8, 16, 24), block_counts_per_stream=inputs.counts(),
        stress_interfaces=True, input_provider=inputs)
    (tmp_path / "result.json").write_text(json.dumps(compact_report(report), indent=2) + "\n")
    assert report["passed"]
    assert report["outputs"] == 512
    assert report["input_fixture"]["live_kq_stage"]
