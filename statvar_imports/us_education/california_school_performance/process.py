#!/usr/bin/env python3
# Copyright 2025 Google LLC
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
"""High-throughput StatVar observation processor for California School Performance (CAASPP).

Processes normalized or raw CAASPP research files across all years (2015-present),
resolving California CDS school/district/county/state codes via config/school_code_mapping.json
and mapping all 55 student demographic subgroups, 8 grade levels (Grades 3-8, 11, and 13),
2 subjects (ELA and Mathematics), and 7 assessment metrics to their canonical Data Commons
Statistical Variables, producing cleaned CSV, TMCF, entity MCF, and counter outputs.
"""

from collections import Counter
import csv
import glob
import json
import os
import sys
import tempfile

from absl import app
from absl import flags
from absl import logging

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, '../../../'))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

try:
    from statvar_imports.us_education.california_school_performance import download
except ModuleNotFoundError:
    import download

FLAGS = flags.FLAGS

flags.DEFINE_string(
    'input_data',
    os.path.join(_SCRIPT_DIR, 'input_files', 'sb_ca_all_years_normalized.txt'),
    'Path or glob pattern to input CAASPP data file(s).',
)
flags.DEFINE_string(
    'pv_map',
    os.path.join(_SCRIPT_DIR, 'config',
                 'california_school_performance_pvmap.csv'),
    'Path to the PV map CSV file.',
)
flags.DEFINE_string(
    'school_code_mapping',
    os.path.join(_SCRIPT_DIR, 'config', 'school_code_mapping.json'),
    'Path to the CDS-to-DCID school code mapping JSON file.',
)
flags.DEFINE_string(
    'output_path',
    os.path.join(_SCRIPT_DIR, 'output_files',
                 'california_school_performance_all_years_output'),
    'Output prefix path for generated .csv, .tmcf, and .mcf files.',
)
flags.DEFINE_string(
    'output_counters',
    os.path.join(_SCRIPT_DIR, 'counters',
                 'california_school_performance_counters.csv'),
    'Output path for processing counters CSV.',
)

OUTPUT_COLUMNS = [
    'typeOf',
    'observationDate',
    'observationAbout',
    'value',
    'measurementMethod',
    'unit',
    'scalingFactor',
    'variableMeasured',
]

MEASUREMENT_METHOD = 'dcs:CaliforniaAssessmentOfStudentPerformanceAndProgress'
OBS_TYPE = 'dcs:StatVarObservation'

ACHIEVEMENT_LEVELS = (
    ('Percentage Standard Exceeded', 'CA_StandardExceeded'),
    ('Percentage Standard Met', 'CA_StandardMet'),
    ('Percentage Standard Met and Above', 'CA_StandardMetAndAbove'),
    ('Percentage Standard Nearly Met', 'CA_StandardNearlyMet'),
    ('Percentage Standard Not Met', 'CA_StandardNotMet'),
)


def _strip_namespace(val: str) -> str:
    """Strips dcid: or dcs: namespace prefix from a schema token."""
    val = val.strip()
    if val.startswith('dcid:'):
        return val[5:]
    if val.startswith('dcs:'):
        return val[4:]
    return val


def load_pv_map_dimensions(
    pv_map_path: str
) -> tuple[dict[str, dict[str, str]], dict[str, dict[str, str]], dict[str, dict[
        str, str]]]:
    """Loads subgroup, grade, and test ID PV mappings from california_school_performance_pvmap.csv."""
    if not os.path.exists(pv_map_path):
        raise FileNotFoundError(f'PV map file not found: {pv_map_path}')

    subgroups: dict[str, dict[str, str]] = {'1': {}}
    grades: dict[str, dict[str, str]] = {}
    tests: dict[str, dict[str, str]] = {}

    with open(pv_map_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if not row or not row[0] or row[0] == 'key':
                continue
            key = row[0].strip()
            if ':' not in key:
                continue
            col_name, code_raw = key.split(':', 1)
            col_name = col_name.strip()
            code_raw = code_raw.strip()
            if not code_raw.isdigit():
                continue
            norm_code = str(int(code_raw))

            pvs: dict[str, str] = {}
            for i in range(1, len(row) - 1, 2):
                prop = row[i].strip()
                val = row[i + 1].strip()
                if prop and val:
                    pvs[prop] = _strip_namespace(val)

            if col_name == 'Student Group ID':
                subgroups[norm_code] = pvs
            elif col_name == 'Grade':
                grades[norm_code] = pvs
            elif col_name == 'Test ID':
                tests[norm_code] = pvs

    return subgroups, grades, tests


def _derive_subgroup_affixes(sg_pvs: dict[str, str]) -> tuple[str, str]:
    """Derives the canonical Google3 StatVar DCID prefix and suffix from subgroup PVs."""
    prefix_parts: list[str] = []
    suffix_parts: list[str] = []

    if 'gender' in sg_pvs:
        prefix_parts.append(sg_pvs['gender'])
    if 'languageFluencyLevel' in sg_pvs:
        prefix_parts.append(sg_pvs['languageFluencyLevel'].replace('__', 'Or'))
    if 'languageLearned' in sg_pvs:
        prefix_parts.append(sg_pvs['languageLearned'])
    if 'languageLearningDuration' in sg_pvs:
        dur = sg_pvs['languageLearningDuration']
        if dur == '[- 12 Month]':
            prefix_parts.append('12OrLessMonth')
        elif dur == '[12 - Month]':
            prefix_parts.append('12OrMoreMonth')
    if 'languageLearningStatus' in sg_pvs:
        prefix_parts.append(sg_pvs['languageLearningStatus'])
    if 'languageLearningAgeGroup' in sg_pvs:
        prefix_parts.append(sg_pvs['languageLearningAgeGroup'])
    if 'armedForcesStatus' in sg_pvs:
        prefix_parts.append(sg_pvs['armedForcesStatus'])
    if 'race' in sg_pvs:
        prefix_parts.append(sg_pvs['race'])
    if 'parentEducationStatus' in sg_pvs:
        pe = sg_pvs['parentEducationStatus'].replace('_', '')
        prefix_parts.append(f'Parent{pe}')
    if 'disabilityStatus' in sg_pvs:
        prefix_parts.append(sg_pvs['disabilityStatus'])
    if 'socialVulnerabilityStatus' in sg_pvs:
        suffix_parts.append(sg_pvs['socialVulnerabilityStatus'])

    prefix = ('_'.join(prefix_parts) + '_') if prefix_parts else ''
    suffix = ('_' + '_'.join(suffix_parts)) if suffix_parts else ''
    return prefix, suffix


def build_statvar_lookup(
    pv_map_path: str,) -> dict[tuple[str, str, str], dict[str, str]]:
    """Precomputes O(1) lookup from (subgroup_id, grade_id, test_id) to canonical Google3 StatVar DCIDs."""
    subgroups, grades, tests = load_pv_map_dimensions(pv_map_path)

    sv_lookup: dict[tuple[str, str, str], dict[str, str]] = {}
    for sg_id, sg_pvs in subgroups.items():
        prefix, suffix = _derive_subgroup_affixes(sg_pvs)
        for gr_id, gr_pvs in grades.items():
            # Subgroup 243 (Adult English Learner) only exists in canonical Google3 schema
            # for Grades 11 and 13 (5,966 total canonical CAASPP StatVars).
            if sg_id == '243' and gr_id not in ('11', '13'):
                continue
            grade_tok = gr_pvs.get('schoolGradeLevel')
            if not grade_tok:
                continue
            for ts_id, ts_pvs in tests.items():
                subj_tok = ts_pvs.get('schoolSubject')
                if not subj_tok:
                    continue
                core = f'Student_{prefix}{grade_tok}_{subj_tok}{suffix}'
                count_dcid = f'Count_{core}'
                entry: dict[str, str] = {
                    'count':
                        f'dcid:{count_dcid}',
                    'mean': ('' if gr_id == '13' else
                             f'dcid:Mean_AssessmentScore_{core}'),
                }
                for _, ach_code in ACHIEVEMENT_LEVELS:
                    entry[ach_code] = f'dcid:Percent_{ach_code}_In_{count_dcid}'
                sv_lookup[(sg_id, gr_id, ts_id)] = entry

    return sv_lookup


def format_numeric_value(raw_val: str) -> str | None:
    """Formats a raw CAASPP cell value matching legacy StatVarProcessor numeric formatting."""
    v = raw_val.strip()
    if not v or v == '*':
        return None
    try:
        if '.' in v:
            return str(float(v))
        return str(int(v))
    except ValueError:
        return None


def generate_tmcf(table_name: str) -> str:
    """Generates the TMCF content for the given output table name."""
    lines = [f'Node: E:{table_name}->E0']
    for col in OUTPUT_COLUMNS:
        lines.append(f'{col}: C:{table_name}->{col}')
    return '\n'.join(lines) + '\n'


def process_files(
    input_pattern: str,
    pv_map_path: str,
    school_map_path: str,
    output_prefix: str,
    counters_path: str = '',
) -> dict[str, int]:
    """Streams input file(s) and produces .csv, .tmcf, .mcf (for unmapped CA places), and optional counters CSV."""
    input_files = sorted(glob.glob(input_pattern))
    if not input_files and os.path.exists(input_pattern):
        input_files = [input_pattern]
    if not input_files:
        raise FileNotFoundError(
            f'No input files matched pattern: {input_pattern}')

    sv_lookup = build_statvar_lookup(pv_map_path)
    if os.path.exists(school_map_path):
        with open(school_map_path, 'r', encoding='utf-8') as f:
            school_map = json.load(f)
    else:
        school_map = {}

    out_dir = os.path.dirname(os.path.abspath(output_prefix))
    os.makedirs(out_dir, exist_ok=True)
    table_name = os.path.basename(output_prefix)

    csv_path = f'{output_prefix}.csv'
    tmcf_path = f'{output_prefix}.tmcf'
    mcf_out_path = f'{output_prefix}.mcf'

    counters: Counter = Counter()
    observed_statvars: set[str] = set()
    observed_ca_places: dict[str, tuple[str, str]] = {}
    sample_invalid_dims: list[tuple[str, str, str, str]] = []
    sample_unmapped_dims: list[tuple[str, str, str]] = []

    temp_csv = tempfile.NamedTemporaryFile(
        'w',
        dir=out_dir,
        delete=False,
        encoding='utf-8',
        newline='',
        suffix='.tmp',
    )
    try:
        writer = csv.writer(temp_csv, lineterminator='\n')
        writer.writerow(OUTPUT_COLUMNS)

        writer_writerow = writer.writerow
        obs_sv_add = observed_statvars.add

        for file_path in input_files:
            counters['input_files_processed'] += 1
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                first_line = f.readline()
                if not first_line:
                    continue
                delim = '^' if '^' in first_line else ','
                f.seek(0)
                reader = csv.reader(f, delimiter=delim)
                raw_header = next(reader, None)
                if not raw_header:
                    continue
                col_idx = {
                    col.strip().strip('"'): i
                    for i, col in enumerate(raw_header)
                    if col
                }

                idx_place = col_idx.get('Place', -1)
                idx_county = col_idx.get('County Code', -1)
                idx_district = col_idx.get('District Code', -1)
                idx_school = col_idx.get('School Code', -1)
                idx_yr = col_idx.get('Test Year', -1)
                idx_sg = col_idx.get('Student Group ID',
                                     col_idx.get('Subgroup ID', -1))
                idx_gr = col_idx.get('Grade', -1)
                idx_ts = col_idx.get('Test ID', col_idx.get('Test Id', -1))
                idx_tested_list = [
                    col_idx[c] for c in (
                        'Total Students Tested',
                        'Students Tested',
                        'Total Students Tested with Scores',
                        'Students with Scores',
                    ) if c in col_idx
                ]
                idx_mean = col_idx.get('Mean Scale Score', -1)
                ach_col_indices = [(col_idx.get(col_name, -1), ach_code)
                                   for col_name, ach_code in ACHIEVEMENT_LEVELS]

                missing_cols = []
                if idx_place < 0 and (idx_county < 0 or idx_district < 0 or
                                      idx_school < 0):
                    missing_cols.append(
                        'Place or (County Code, District Code, School Code)')
                if idx_yr < 0:
                    missing_cols.append('Test Year')
                if idx_sg < 0:
                    missing_cols.append('Student Group ID / Subgroup ID')
                if idx_gr < 0:
                    missing_cols.append('Grade')
                if idx_ts < 0:
                    missing_cols.append('Test ID / Test Id')
                if not idx_tested_list and idx_mean < 0 and all(
                        idx < 0 for idx, _ in ach_col_indices):
                    missing_cols.append('assessment metric columns')
                if missing_cols:
                    raise ValueError(
                        f'Missing required columns {missing_cols} in {file_path}: {raw_header}'
                    )

                for raw_row in reader:
                    row_len = len(raw_row)
                    if row_len == 0:
                        continue
                    counters['input_data_rows'] += 1

                    place = (raw_row[idx_place].strip().strip('"')
                             if 0 <= idx_place < row_len else '')
                    if not place:
                        c_val = (raw_row[idx_county].strip().strip('"')
                                 if 0 <= idx_county < row_len else '')
                        d_val = (raw_row[idx_district].strip().strip('"')
                                 if 0 <= idx_district < row_len else '')
                        s_val = (raw_row[idx_school].strip().strip('"')
                                 if 0 <= idx_school < row_len else '')
                        place = download.resolve_place_dcid(
                            c_val, d_val, s_val, school_map)
                    if (place.startswith('CA-') and
                            place not in observed_ca_places):
                        c_val = (raw_row[idx_county].strip().strip('"')
                                 if 0 <= idx_county < row_len else '')
                        s_val = (raw_row[idx_school].strip().strip('"')
                                 if 0 <= idx_school < row_len else '')
                        observed_ca_places[place] = (
                            c_val.zfill(2),
                            s_val.zfill(7),
                        )

                    yr = (raw_row[idx_yr].strip().strip('"')
                          if 0 <= idx_yr < row_len else '')
                    sg_raw = (raw_row[idx_sg].strip().strip('"')
                              if 0 <= idx_sg < row_len else '')
                    gr_raw = (raw_row[idx_gr].strip().strip('"')
                              if 0 <= idx_gr < row_len else '')
                    ts_raw = (raw_row[idx_ts].strip().strip('"')
                              if 0 <= idx_ts < row_len else '')

                    if not (yr and sg_raw.isdigit() and gr_raw.isdigit() and
                            ts_raw.isdigit()):
                        counters['dropped_invalid_dimension_rows'] += 1
                        if len(sample_invalid_dims) < 5:
                            sample_invalid_dims.append(
                                (yr, sg_raw, gr_raw, ts_raw))
                        continue

                    sg = str(int(sg_raw))
                    gr = str(int(gr_raw))
                    ts = str(int(ts_raw))

                    svs = sv_lookup.get((sg, gr, ts))
                    if not svs:
                        counters['dropped_unmapped_dimension_rows'] += 1
                        if len(sample_unmapped_dims) < 5:
                            sample_unmapped_dims.append((sg, gr, ts))
                        continue

                    tested_raw = ''
                    for idx_t in idx_tested_list:
                        if idx_t < row_len:
                            val_t = raw_row[idx_t].strip().strip('"')
                            if val_t:
                                tested_raw = val_t
                                break

                    # 1. Student Count observation
                    val_count = format_numeric_value(tested_raw)
                    if val_count is not None and svs.get('count'):
                        sv_dcid = svs['count']
                        writer_writerow([
                            OBS_TYPE,
                            yr,
                            place,
                            val_count,
                            MEASUREMENT_METHOD,
                            '',
                            '',
                            sv_dcid,
                        ])
                        obs_sv_add(sv_dcid)
                        counters['output_svobs_rows'] += 1

                    # 2. Mean Scale Score observation
                    mean_raw = (raw_row[idx_mean].strip().strip('"')
                                if 0 <= idx_mean < row_len else '')
                    val_mean = format_numeric_value(mean_raw)
                    if val_mean is not None and svs.get('mean'):
                        sv_dcid = svs['mean']
                        writer_writerow([
                            OBS_TYPE,
                            yr,
                            place,
                            val_mean,
                            MEASUREMENT_METHOD,
                            '',
                            '',
                            sv_dcid,
                        ])
                        obs_sv_add(sv_dcid)
                        counters['output_svobs_rows'] += 1

                    # 3. Percentage achievement level observations
                    for idx_ach, ach_code in ach_col_indices:
                        ach_raw = (raw_row[idx_ach].strip().strip('"')
                                   if 0 <= idx_ach < row_len else '')
                        val_pct = format_numeric_value(ach_raw)
                        sv_dcid = svs.get(ach_code, '')
                        if val_pct is not None and sv_dcid:
                            writer_writerow([
                                OBS_TYPE,
                                yr,
                                place,
                                val_pct,
                                MEASUREMENT_METHOD,
                                'dcs:Percent',
                                '100',
                                sv_dcid,
                            ])
                            obs_sv_add(sv_dcid)
                            counters['output_svobs_rows'] += 1

        if (counters['input_data_rows'] > 0 and
                counters['output_svobs_rows'] == 0):
            raise RuntimeError(
                f'Processed {counters["input_data_rows"]} input rows but generated 0 observations '
                f'(dropped_invalid={counters["dropped_invalid_dimension_rows"]}, '
                f'dropped_unmapped={counters["dropped_unmapped_dimension_rows"]}).'
            )

        temp_csv.flush()
        os.fsync(temp_csv.fileno())
        temp_csv.close()
        os.replace(temp_csv.name, csv_path)
    except Exception:
        temp_csv.close()
        if os.path.exists(temp_csv.name):
            os.unlink(temp_csv.name)
        raise

    if counters['dropped_invalid_dimension_rows'] > 0:
        logging.warning(
            'Dropped %d rows with invalid dimensions; samples: %s',
            counters['dropped_invalid_dimension_rows'],
            sample_invalid_dims,
        )
    if counters['dropped_unmapped_dimension_rows'] > 0:
        logging.warning(
            'Dropped %d rows with unmapped dimensions; samples: %s',
            counters['dropped_unmapped_dimension_rows'],
            sample_unmapped_dims,
        )

    # Write TMCF
    with open(tmcf_path, 'w', encoding='utf-8', newline='\n') as f_tmcf:
        f_tmcf.write(generate_tmcf(table_name))

    # Write only unmapped CA-... School/SchoolDistrict Place entity nodes to .mcf.
    # All 5,966 canonical CAASPP StatisticalVariable nodes already exist in Google3 schema
    # and must not be re-emitted in node_mcf to prevent duplicate instance-node ingestion.
    counters['generated_statvars'] = len(observed_statvars)
    counters['generated_place_nodes'] = len(observed_ca_places)
    with open(mcf_out_path, 'w', encoding='utf-8', newline='\n') as f_mcf:
        blocks = []
        for pl, (county_code,
                 school_code) in sorted(observed_ca_places.items()):
            dcid_key = f'dcid:{pl}'
            c_num = int(county_code) if county_code.isdigit() else 0
            contained_in = (f'dcid:geoId/06{c_num * 2 - 1:03d}'
                            if 1 <= c_num <= 58 else 'dcid:geoId/06')
            type_of = ('dcs:SchoolDistrict'
                       if school_code == '0000000' else 'dcs:School')
            blocks.append(
                f'Node: {dcid_key}\ntypeOf: {type_of}\ncontainedInPlace: {contained_in}'
            )
        if blocks:
            f_mcf.write('\n\n'.join(blocks) + '\n')

    # Write counters if requested
    if counters_path:
        os.makedirs(os.path.dirname(os.path.abspath(counters_path)),
                    exist_ok=True)
        with open(counters_path, 'w', encoding='utf-8', newline='\n') as f_cnt:
            w_cnt = csv.writer(f_cnt, lineterminator='\n')
            w_cnt.writerow(['metric', 'value'])
            for k, v in sorted(counters.items()):
                w_cnt.writerow([k, v])

    logging.info(
        'Processed %d input rows into %d observations (%d StatVars, %d CA place nodes) -> %s',
        counters['input_data_rows'],
        counters['output_svobs_rows'],
        counters['generated_statvars'],
        counters['generated_place_nodes'],
        csv_path,
    )
    return dict(counters)


def main(argv):
    del argv
    try:
        process_files(
            input_pattern=FLAGS.input_data,
            pv_map_path=FLAGS.pv_map,
            school_map_path=FLAGS.school_code_mapping,
            output_prefix=FLAGS.output_path,
            counters_path=FLAGS.output_counters,
        )
    except (FileNotFoundError, ValueError, RuntimeError, OSError) as e:
        logging.fatal('Processing failed: %s', e)


if __name__ == '__main__':
    app.run(main)
