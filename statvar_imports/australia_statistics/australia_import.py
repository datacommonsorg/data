# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Orchestrates the AustraliaStatistics data refresh and StatVar processing."""

from concurrent import futures
import glob
import os
import shutil
import subprocess
import sys
from typing import Dict, Tuple

from absl import app
from absl import flags
from absl import logging

from preprocess_abs_labour_force import refresh_labour_force_csv
from preprocess_abs_life_expectancy import refresh_life_expectancy_csvs

FLAGS = flags.FLAGS

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_MODULE_DIR, '..', '..'))
_STAT_VAR_PROCESSOR = os.path.join(_REPO_ROOT, 'tools', 'statvar_importer',
                                   'stat_var_processor.py')

flags.DEFINE_string(
    'intermediate_dir',
    os.path.join(_MODULE_DIR, 'intermediate_files'),
    'Directory containing intermediate CSVs, PVMaps, and config.',
)
flags.DEFINE_string(
    'output_dir',
    os.path.join(_MODULE_DIR, 'output_files'),
    'Directory where cleaned CSV, TMCF, and MCF files are written.',
)
flags.DEFINE_string(
    'counters_dir',
    os.path.join(_MODULE_DIR, 'counters'),
    'Directory where stat_var_processor counter files are written.',
)
flags.DEFINE_bool(
    'skip_download',
    False,
    'If True, skip downloading updates from abs.gov.au and use staged CSVs.',
)

TABLE_SPECS: Dict[str, Tuple[str, str]] = {
    'aus_count_person_gender_agegrp_historic': (
        'aus_count_person_gender_agegrp_historic_int.csv',
        'aus_count_person_gender_agegrp_historic_map.py',
    ),
    'aus_count_person_gender_agegrp_historic_states': (
        'aus_count_person_gender_agegrp_historic_states_int.csv',
        'aus_count_person_gender_agegrp_historic_states_map.py',
    ),
    'aus_health_condition': (
        'aus_health_condition_int.csv',
        'aus_health_condition_map.py',
    ),
    'aus_health_condition_state': (
        'aus_health_condition_states_int.csv',
        'aus_health_condition_states_map.py',
    ),
    'aus_weekly_household_income': (
        'aus_weekly_household_income.csv',
        'aus_weekly_household_income_map.py',
    ),
    'aus_life_expectancy_gender_age': (
        'life_expectancy_age_aus.csv',
        'life_expectancy_age_aus_map.py',
    ),
    'aus_life_expectancy_states': (
        'life_expectancy_aus_states.csv',
        'life_expectancy_aus_states_map.py',
    ),
    'aus_employment': (
        'aus_employment_int.csv',
        'aus_employment_map.py',
    ),
}

STATIC_OUTPUT_FILES = (
    'aus_count_person_gender_2021.csv',
    'aus_count_person_gender_2021.tmcf',
    'aus_count_person_gender_agegrp_2021.csv',
    'aus_count_person_gender_agegrp_2021.tmcf',
    'aus_count_person_gender_agegrp_historic_states.mcf',
    'aus_employment.mcf',
    'aus_health_condition.mcf',
    'aus_health_condition_state.mcf',
    'aus_life_expectancy_gender_age.mcf',
    'aus_weekly_household_income.mcf',
    'schema.mcf',
)


def _run_stat_var_processor_job(
    table_name: str,
    input_csv: str,
    pv_map: str,
    config_file: str,
    existing_statvar_mcf: str,
    output_dir: str,
    counters_dir: str,
) -> None:
    """Runs stat_var_processor.py for a single AustraliaStatistics table."""
    output_prefix = os.path.join(output_dir, table_name)
    counters_file = os.path.join(counters_dir, f'{table_name}_counters.txt')
    cmd = [
        sys.executable,
        _STAT_VAR_PROCESSOR,
        f'--input_data={input_csv}',
        f'--pv_map={pv_map}',
        f'--config_file={config_file}',
        f'--existing_statvar_mcf={existing_statvar_mcf}',
        f'--output_path={output_prefix}',
        f'--output_counters={counters_file}',
    ]
    env = os.environ.copy()
    pythonpath_parts = [
        _REPO_ROOT,
        os.path.join(_REPO_ROOT, 'tools', 'statvar_importer'),
    ]
    if env.get('PYTHONPATH'):
        pythonpath_parts.append(env['PYTHONPATH'])
    env['PYTHONPATH'] = ':'.join(pythonpath_parts)

    logging.info('Running StatVarProcessor for %s', table_name)
    result = subprocess.run(
        cmd,
        cwd=_MODULE_DIR,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f'stat_var_processor failed for {table_name} '
            f'(exit {result.returncode}):\n{result.stderr}\n{result.stdout}')

    stat_vars_mcf = f'{output_prefix}_stat_vars.mcf'
    if os.path.exists(stat_vars_mcf):
        os.remove(stat_vars_mcf)

    for extra_schema in glob.glob(f'{output_prefix}*_schema.mcf'):
        os.remove(extra_schema)


def run_pipeline(
    intermediate_dir: str,
    output_dir: str,
    counters_dir: str,
    skip_download: bool = False,
) -> None:
    """Refreshes ABS intermediate data and processes all Australia tables."""
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(counters_dir, exist_ok=True)

    if not skip_download:
        employment_csv = os.path.join(intermediate_dir,
                                      'aus_employment_int.csv')
        refresh_labour_force_csv(employment_csv)

        age_csv = os.path.join(intermediate_dir, 'life_expectancy_age_aus.csv')
        states_csv = os.path.join(intermediate_dir,
                                  'life_expectancy_aus_states.csv')
        refresh_life_expectancy_csvs(age_csv, states_csv)

    config_file = os.path.join(intermediate_dir, 'aus_config.conf')
    existing_statvar_mcf = os.path.join(intermediate_dir,
                                        'existing_stat_vars.mcf')

    with futures.ThreadPoolExecutor(max_workers=8) as executor:
        future_to_table = {}
        for table_name, (csv_name, map_name) in TABLE_SPECS.items():
            input_csv = os.path.join(intermediate_dir, csv_name)
            pv_map = os.path.join(intermediate_dir, map_name)
            fut = executor.submit(
                _run_stat_var_processor_job,
                table_name,
                input_csv,
                pv_map,
                config_file,
                existing_statvar_mcf,
                output_dir,
                counters_dir,
            )
            future_to_table[fut] = table_name

        for fut in futures.as_completed(future_to_table):
            table_name = future_to_table[fut]
            fut.result()
            logging.info('Completed table: %s', table_name)

    static_dir = os.path.join(intermediate_dir, 'static_output')
    for filename in STATIC_OUTPUT_FILES:
        src = os.path.join(static_dir, filename)
        dst = os.path.join(output_dir, filename)
        if os.path.exists(src):
            shutil.copyfile(src, dst)


def main(_):
    run_pipeline(
        intermediate_dir=FLAGS.intermediate_dir,
        output_dir=FLAGS.output_dir,
        counters_dir=FLAGS.counters_dir,
        skip_download=FLAGS.skip_download,
    )


if __name__ == '__main__':
    app.run(main)
