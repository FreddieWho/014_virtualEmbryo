"""Offline regression, provenance, and relocation tests for the audit package."""
from __future__ import annotations
import csv
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def read_json(path):
    return json.loads(Path(path).read_text())


def rows(path):
    with Path(path).open() as f:
        return list(csv.DictReader(f, delimiter='\t' if str(path).endswith('.tsv') else ','))


class CalibrationAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='calibration-test-')
        cls.base = Path(cls.temp.name)
        cls.package = cls.base / 'moved' / 'calibration'
        shutil.copytree(ROOT, cls.package, ignore=shutil.ignore_patterns('__pycache__', 'recomputed'))
        cls.output = cls.base / 'new-results'
        result = subprocess.run([sys.executable, str(cls.package / 'analyze.py'), '--output-dir', str(cls.output)], cwd=cls.base, text=True, capture_output=True)
        if result.returncode:
            raise RuntimeError(result.stdout + result.stderr)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def assert_equivalent(self, expected, actual, label=''):
        if isinstance(expected, dict):
            self.assertEqual(expected.keys(), actual.keys(), label)
            for key in expected:
                self.assert_equivalent(expected[key], actual[key], f'{label}/{key}')
        elif isinstance(expected, list):
            self.assertEqual(len(expected), len(actual), label)
            for i, (left, right) in enumerate(zip(expected, actual)):
                self.assert_equivalent(left, right, f'{label}/{i}')
        elif isinstance(expected, (int, float)) and not isinstance(expected, bool):
            self.assertTrue(math.isclose(expected, actual, rel_tol=1e-12, abs_tol=1e-12), label)
        else:
            self.assertEqual(expected, actual, label)

    def test_relocation_regenerates_all_statistics(self):
        for task, names in {'t2': ['statistics.json'], 't3': ['computed_summary.json', 'verification.json', 'source_hashes.json']}.items():
            for name in names:
                self.assert_equivalent(read_json(ROOT / task / name), read_json(self.output / task / name), name)

    def test_all_derived_csvs_match(self):
        expected = {'t2': ['historical_paired_audit.csv', 'all_extrap_inclusion_audit.csv', 'new_run_raw_audit.csv'], 't3': ['paired_local_server.csv', 'dominance_reversals.csv', 'topk_counterfactual.csv', 'candidate_inventory.csv', 'fixed_donor_raw_rows.csv', 'fixed_donor_summary.csv']}
        for task, names in expected.items():
            for name in names:
                self.assertEqual(rows(ROOT / task / name), rows(self.output / task / name), name)

    def test_known_t2_threshold_examples(self):
        stats = read_json(self.output / 't2/statistics.json')
        self.assertEqual(stats['all17']['n'], 17)
        self.assertEqual(stats['nonbaseline16']['n'], 16)
        self.assertAlmostEqual(stats['all17']['spearman'], 0.11158800399001334)
        threshold = next(r for r in stats['thresholds'] if r['local_threshold'] == 1 and not r['require_guards'])
        self.assertEqual((threshold['selected_n'], threshold['retained_winners']), (5, 0))
        self.assertEqual(set(threshold['missed']), {'v0011', 'v0022'})

    def test_t2_receipts_are_all_42_calls_not_966_trials(self):
        records = rows(self.output / 't2/new_run_raw_audit.csv')
        calls = {(r['partition'], r['lane'], r['seed']) for r in records}
        self.assertEqual(len(records), 966)
        self.assertEqual(len(calls), 42)
        self.assertEqual(sum(p == 'dev' for p, _, _ in calls), 33)
        self.assertEqual(sum(p == 'reserve' for p, _, _ in calls), 9)

    def test_t3_reversal_and_coverage(self):
        summary = read_json(self.output / 't3/computed_summary.json')
        self.assertEqual(summary['n_local_records'], 106)
        self.assertEqual(summary['n_unique_scored_with_local'], 24)
        self.assertEqual(summary['n_published_inventory'], 26)
        self.assertEqual((summary['n_candidate_inventory'], summary['n_scored_inventory']), (87, 78))
        self.assertEqual(summary['source_strata_favoring_v85_all_five'], 6)
        self.assertEqual(summary['max_observed_source_dominance_reversal_server_gap'], 2.1)
        self.assertIsNone(summary['overall_false_negative_rate'])
        self.assertEqual(summary['n_same_target_absolute_score_pairs'], 0)

    def test_raw_frozen_donor_aggregation(self):
        verification = read_json(self.output / 't3/verification.json')
        self.assertTrue(verification['frozen_donor_code_hash_matches'])
        self.assertEqual(verification['raw_source_rows'], 390)
        self.assertLess(verification['summary_recomputed_from_raw_max_abs_error'], 1e-12)
        self.assertEqual(len(rows(self.output / 't3/fixed_donor_raw_rows.csv')), 156)

    def test_source_inventory_hashes(self):
        for item in read_json(ROOT / 'provenance/SOURCE_INVENTORY.json'):
            path = ROOT / item['published_path']
            self.assertTrue(path.is_file(), item['published_path'])
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), item['published_sha256'], item['published_path'])
            self.assertEqual(len(item['original_sha256']), 64)

    def test_excluded_reports_have_receipts_only(self):
        self.assertFalse(list((ROOT / 'evidence').rglob('*.md')))
        receipts = read_json(ROOT / 'provenance/EXCLUDED_SOURCE_RECEIPTS.json')['sources']
        self.assertEqual(len(receipts), 6)
        for receipt in receipts:
            self.assertFalse((ROOT / receipt['omitted_package_path']).exists())
            self.assertEqual(len(receipt['original_sha256']), 64)

    def test_primary_entrypoints_have_no_machine_paths(self):
        for rel in ['analyze.py', 'audit_support.py', 't2/analyze.py', 't3/analyze.py', 'config.json']:
            text = (ROOT / rel).read_text()
            self.assertNotIn('/workspace/', text)
            self.assertNotIn('/home/', text)
        for task in ['t2', 't3']:
            name = 'new_run_raw_audit.csv' if task == 't2' else 'paired_local_server.csv'
            for record in rows(self.output / task / name):
                self.assertTrue(record['source'].startswith('evidence/') or record['source'].startswith('https://github.com/FreddieWho/014_virtualEmbryo/blob/'))

    def test_cli_rejects_overwriting_evidence(self):
        result = subprocess.run([sys.executable, str(self.package / 't2/analyze.py'), '--output-dir', str(self.package / 'evidence')], cwd=self.base, text=True, capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('must not overwrite evidence', result.stderr)

    def test_cli_rejects_incomplete_t2_score_receipts(self):
        empty = self.base / 'empty-receipts'
        empty.mkdir(exist_ok=True)
        result = subprocess.run([sys.executable, str(self.package / 't2/analyze.py'), '--evaluation-dir', str(empty), '--output-dir', str(self.base / 'bad-run'), '--bootstrap-resamples', '1'], cwd=self.base, text=True, capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Expected all 42 frozen T2 score receipts', result.stderr)


if __name__ == '__main__':
    unittest.main()
