"""Diagnostic full mesh test using analytically known, synthetic payloads."""
import json
import os

import pytest

from npu.eval.run_numerical_mesh import run
from npu.eval.tests.test_numerical_mesh_sidecars import report


@pytest.mark.skipif(os.environ.get("RTLGEN_RUN_NUMERICAL_MESH_DIAGNOSTIC") != "1",
                    reason="full numerical mesh diagnostic is opt-in")
def test_numerical_mode_preserves_known_exact_values(tmp_path):
    data = report()
    # Equal maxima, unit denominators and unit numerators at all sixteen
    # leaves normalize to Q16 unity (65535) at the finalizer.
    for endpoint, cluster in enumerate(data["clusters"]):
        for g, group in enumerate(cluster["groups"]):
            group["command_id"] = 0x8200 + g
            group["output_cycles"] = list(range(17000 + g*16400 + endpoint,
                                                17128 + g*16400 + endpoint))
        for i, row in enumerate(cluster["observed_rows"]):
            row.update(command_id=0x8200 + i//128, global_max=0,
                       exp_sum=1, value=[1]*8)
    for i, row in enumerate(data["expected_root_rows"]):
        row.update(command_id=0x8200 + i//128, value=[65535]*8)
    path = tmp_path / "synthetic_diagnostic_only.json"
    path.write_text(json.dumps(data))
    result = run(path)
    assert result["source_handshakes_checked"] == 8192
    assert result["observation"]["vc1_rows"] == 512
