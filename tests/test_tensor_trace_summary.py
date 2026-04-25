import json
import tempfile
import unittest
from pathlib import Path

from npu.eval.tensor_trace_summary import (
    packed_u8_tensor_summary,
    parse_rtl_tensor_trace_log,
    scalar_tensor_summary,
    selected_tensor_trace_hash,
    tensor_summary,
    trace_selected_outputs,
)


class TensorTraceSummaryRegressionTest(unittest.TestCase):
    def test_tensor_summary_hash_is_canonical(self):
        tensors_a = [
            {'name': 'present.0.key', 'step': 0, 'shape': [1, 2], 'dtype': 'float32', 'min': -1.0, 'max': 1.0, 'mean': 0.0, 'std': 0.5},
        ]
        tensors_b = [
            {'std': 0.5, 'mean': 0.0, 'max': 1.0, 'min': -1.0, 'dtype': 'float32', 'shape': [1, 2], 'step': 0, 'name': 'present.0.key'},
        ]
        self.assertEqual(selected_tensor_trace_hash(tensors_a), selected_tensor_trace_hash(tensors_b))

    def test_trace_selected_outputs_sorts_and_filters_outputs(self):
        traced = trace_selected_outputs(
            outputs_by_name={
                'logits': [[0.0]],
                'present.1.key': [[2.0, 4.0]],
                'present.0.key': [[-1.0, 1.0]],
            },
            trace_patterns=['present.*'],
            step=3,
        )
        self.assertEqual(['present.0.key', 'present.1.key'], [entry['name'] for entry in traced])
        self.assertEqual(3, traced[0]['step'])
        self.assertEqual([1, 2], traced[0]['shape'])

    def test_rtl_tensor_trace_log_matches_software_summary_hash(self):
        expected = [
            tensor_summary([[1.0, -1.0]], name='present.0.key', step=0),
            tensor_summary([[2.0, 4.0]], name='present.1.key', step=0, quantization={'bits': 4, 'mode': 'trace_tensor_quant'}),
        ]
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'rtl.log'
            path.write_text(
                '\n'.join(
                    [
                        'noise before trace',
                        "TENSOR_TRACE name=present.1.key step=0 shape=1,2 dtype=float32 min=2.0 max=4.0 mean=3.0 std=1.0 quantization='"
                        + json.dumps({'bits': 4, 'mode': 'trace_tensor_quant'}, separators=(',', ':'))
                        + "'",
                        'TENSOR_TRACE name=present.0.key step=0 shape=1,2 dtype=float32 min=-1.0 max=1.0 mean=0.0 std=1.0',
                    ]
                )
                + '\n',
                encoding='utf-8',
            )
            parsed = parse_rtl_tensor_trace_log(path)

        self.assertEqual(expected, parsed)
        self.assertEqual(selected_tensor_trace_hash(expected), selected_tensor_trace_hash(parsed))

    def test_compact_packed_result_trace_matches_summary_helper(self):
        expected = [packed_u8_tensor_summary(name='vec.result', step=1, result='0x00000000000000ff', lanes=8)]
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'rtl.log'
            path.write_text(
                'TENSOR_TRACE name=vec.result step=1 lanes=8 dtype=packed_u8 result=0x00000000000000ff\n',
                encoding='utf-8',
            )
            parsed = parse_rtl_tensor_trace_log(path)

        self.assertEqual(expected, parsed)
        self.assertEqual(selected_tensor_trace_hash(expected), selected_tensor_trace_hash(parsed))

    def test_scalar_tensor_trace_matches_summary_helper(self):
        expected = [scalar_tensor_summary(name='gemm.accum', step=1, value=-7, dtype='int32')]
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'rtl.log'
            path.write_text(
                'TENSOR_TRACE name=gemm.accum step=1 shape=1 dtype=int32 min=-7 max=-7 mean=-7 std=0\n',
                encoding='utf-8',
            )
            parsed = parse_rtl_tensor_trace_log(path)

        self.assertEqual(expected, parsed)
        self.assertEqual(selected_tensor_trace_hash(expected), selected_tensor_trace_hash(parsed))


if __name__ == '__main__':
    unittest.main()
