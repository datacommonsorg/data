import os
import subprocess
import sys
import tempfile
import unittest
import pandas as pd
from absl import logging

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, '..', '..'))
sys.path.append(os.path.join(_REPO_ROOT, 'util'))
sys.path.append(os.path.join(_REPO_ROOT, 'tools', 'statvar_importer'))

from counters import Counters
from mcf_diff import diff_mcf_files


class MongoliaImportTestBase(unittest.TestCase):
    """Base class for testing Mongolia import processing against expected testdata."""

    def setUp(self):
        self.maxDiff = None
        if os.path.exists('/tmp/stat_vars.mcf'):
            self.existing_statvar_mcf = '/tmp/stat_vars.mcf'
        else:
            self.existing_statvar_mcf = '/dev/null'

    def compare_mcf_files(self, actual_file: str, expected_file: str):
        """Compare files with MCF nodes allowing reordering of nodes and properties."""
        if not os.path.exists(expected_file):
            self.fail(f"Expected MCF file not found: {expected_file}")
        if not os.path.exists(actual_file):
            self.fail(f"Actual MCF file was not created: {actual_file}")
        counters = Counters()
        diff = diff_mcf_files(actual_file, expected_file, {'show_diff_nodes_only': True}, counters)
        self.assertEqual(
            diff,
            '',
            f'Found diffs in MCF nodes:\n"{actual_file}" vs "{expected_file}":\n{diff}\nCounters: {counters.get_counters_string()}',
        )

    def compare_csv_files(self, actual_file: str, expected_file: str):
        """Compare CSV files with statvar observation data."""
        if not os.path.exists(expected_file):
            self.fail(f"Expected CSV file not found: {expected_file}")
        if not os.path.exists(actual_file):
            self.fail(f"Actual CSV file was not created: {actual_file}")
        df_expected = pd.read_csv(expected_file)
        df_actual = pd.read_csv(actual_file)
        self.assertEqual(
            df_expected.columns.to_list(),
            df_actual.columns.to_list(),
            f'Found different columns in CSV files:\nexpected:{expected_file}:{df_expected.columns.to_list()}\nactual:{actual_file}:{df_actual.columns.to_list()}',
        )
        df_expected.sort_values(by=df_expected.columns.to_list(), inplace=True, ignore_index=True)
        df_actual.sort_values(by=df_actual.columns.to_list(), inplace=True, ignore_index=True)
        self.assertTrue(
            df_expected.equals(df_actual),
            f'Found diffs in CSV rows:\n"{actual_file}" vs "{expected_file}"',
        )

    def compare_tmcf_files(self, actual_file: str, expected_file: str):
        """Compare TMCF template files."""
        if not os.path.exists(expected_file):
            self.fail(f"Expected TMCF file not found: {expected_file}")
        if not os.path.exists(actual_file):
            self.fail(f"Actual TMCF file was not created: {actual_file}")
        with open(actual_file, 'r', encoding='utf-8') as act_f:
            act_str = act_f.read().strip()
        with open(expected_file, 'r', encoding='utf-8') as exp_f:
            exp_str = exp_f.read().strip()
        self.assertEqual(act_str, exp_str, f'Mismatched TMCF actual:{actual_file} expected:{expected_file}')

    def verify_processing(self, import_dir: str, prefix: str, pvmap: str, config: str, places_resolved: str = None):
        """Runs StatVarDataProcessor via subprocess and asserts output matches expected files in testdata/."""
        testdata_dir = os.path.join(import_dir, 'testdata')
        input_file = os.path.join(testdata_dir, f'{prefix}_input.csv')
        expected_output_prefix = os.path.join(testdata_dir, f'{prefix}_output')

        with tempfile.TemporaryDirectory() as tmp_dir:
            actual_output_prefix = os.path.join(tmp_dir, f'{prefix}_output')
            cmd = [
                sys.executable,
                os.path.join(_REPO_ROOT, 'tools', 'statvar_importer', 'stat_var_processor.py'),
                f'--input_data={input_file}',
                f'--pv_map={os.path.join(import_dir, pvmap)}',
                f'--config_file={os.path.join(import_dir, config)}',
                f'--output_path={actual_output_prefix}',
                f'--existing_statvar_mcf={self.existing_statvar_mcf}',
            ]
            if places_resolved:
                cmd.append(f'--places_resolved_csv={os.path.join(import_dir, places_resolved)}')

            res = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(res.returncode, 0, f"Processor failed for {prefix}:\n{res.stderr}")

            # Compare CSV
            self.compare_csv_files(f'{actual_output_prefix}.csv', f'{expected_output_prefix}.csv')

            # Compare TMCF
            self.compare_tmcf_files(f'{actual_output_prefix}.tmcf', f'{expected_output_prefix}.tmcf')

            # Compare stat_vars.mcf if expected exists or actual is created
            expected_sv_mcf = f'{expected_output_prefix}_stat_vars.mcf'
            actual_sv_mcf = f'{actual_output_prefix}_stat_vars.mcf'
            if os.path.exists(expected_sv_mcf) or os.path.exists(actual_sv_mcf):
                self.compare_mcf_files(actual_sv_mcf, expected_sv_mcf)

            # Compare stat_vars_schema.mcf if expected exists or actual is created
            expected_schema_mcf = f'{expected_output_prefix}_stat_vars_schema.mcf'
            actual_schema_mcf = f'{actual_output_prefix}_stat_vars_schema.mcf'
            if os.path.exists(expected_schema_mcf) or os.path.exists(actual_schema_mcf):
                self.compare_mcf_files(actual_schema_mcf, expected_schema_mcf)
