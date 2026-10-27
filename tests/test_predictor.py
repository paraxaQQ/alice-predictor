import ctypes
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

import alice_predictor as model
import verify_evidence


ROOT = Path(__file__).resolve().parents[1]


class PredictorTests(unittest.TestCase):
    def test_known_native_rand_sequence(self) -> None:
        state = 1
        actual = []
        for _ in range(10):
            state, value = model.advance(state)
            actual.append(value)
        self.assertEqual(actual, [41, 18467, 6334, 26500, 19169, 15724, 11478, 29358, 26962, 24464])

    @unittest.skipUnless(sys.platform == 'win32', 'native msvcrt comparison requires Windows')
    def test_native_crt_across_seed_boundaries(self) -> None:
        crt = ctypes.CDLL('msvcrt')
        crt.srand.argtypes = [ctypes.c_uint]
        crt.srand.restype = None
        crt.rand.argtypes = []
        crt.rand.restype = ctypes.c_int
        for seed in [0, 1, 2, 1793081406, 0x7fffffff, 0x80000000, 0xffffffff]:
            crt.srand(seed)
            state = seed
            for _ in range(1000):
                state, predicted = model.advance(state)
                self.assertEqual(predicted, crt.rand())

    def test_recorded_advance_predictions(self) -> None:
        result = verify_evidence.verify(ROOT / 'evidence')
        self.assertEqual(result['lab_advance_matches'], 4)
        self.assertEqual(result['normal_startup_advance_matches'], 0)

    def test_tampered_evidence_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            evidence = Path(directory) / 'evidence'
            shutil.copytree(ROOT / 'evidence', evidence)
            path = evidence / 'lab-forecast.json'
            data = json.loads(path.read_text())
            data['predictions'][1]['word'] = 'TAMPERED'
            path.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, 'digest mismatch'):
                verify_evidence.verify(evidence)

    def test_empty_bank_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, 'empty'):
            model.shuffled_first(1, [], 0)

    def test_unmodeled_shuffle_endpoint_is_rejected(self) -> None:
        state = ((0x7fff0000 - 2531011) * pow(214013, -1, 2**32)) & 0xffffffff
        with self.assertRaisesRegex(ValueError, 'endpoint'):
            model.shuffled_first(state, ['a', 'b'], 0)

    def test_no_matching_observed_prefix(self) -> None:
        banks = [['a', 'b', 'c'], ['d', 'e', 'f']]
        self.assertEqual(model.recover(1793081406, 1, ['not in either bank'], banks, 1), [])

    def test_version_cli(self) -> None:
        result = subprocess.run([sys.executable, str(ROOT / 'alice_predictor.py'), '--version'],
                                capture_output=True, text=True, check=True)
        self.assertEqual(result.stdout.strip(), '0.1.0')


if __name__ == '__main__':
    unittest.main()
