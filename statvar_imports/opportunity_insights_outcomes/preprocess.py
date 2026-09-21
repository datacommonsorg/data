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
"""Preprocesses Opportunity Insights (Opportunity Atlas Outcomes) CSVs for stat_var_processor.py.

Guarantees 0 deletions against production (/cns/jv-d/home/datcom/v3_resolved_mcf/oi/outcomes/20260722/)
by matching the exact StatisticalVariable schema:
- populationType: OpportunityInsightsCohort
- measuredProperty: exact translated property names (including meanPercentileIncomeRank for kir
  and householdIncomeRankImmigantMother for kfr_imm)
- statType: measuredValue, meanValue, stdError, meanStdError, sampleSize
- observationDate & observationPeriod: exact 1991-2015 dates for baseline tables, plus new
  2016 / 2020-04-01 and 2005-2019 (age-27 cohort) dates for the 2024 source refreshes.
"""

import collections
import csv
import os
import re
from absl import app
from absl import flags
from absl import logging

try:
    from statvar_imports.opportunity_insights_outcomes import download as download_script
except ImportError:
    import download as download_script

FLAGS = flags.FLAGS

flags.DEFINE_string(
    'input_dir',
    'raw_data',
    'Directory containing raw Opportunity Atlas CSV files downloaded from source.',
)
flags.DEFINE_string(
    'output_dir',
    'input_files',
    'Directory where cleaned CSV files for stat_var_processor.py will be written.',
)
flags.DEFINE_bool(
    'download',
    True,
    'Whether to download/refresh the raw CSV files from opportunityinsights.org/data/ before processing.',
)
flags.DEFINE_integer(
    'max_rows_per_shard',
    5_000_000,
    'Maximum normalized observation rows per output CSV shard before rotating to a new shard file.',
)

# Source datasets to process: (filename, geo_level, dataset_mode)
# dataset_mode:
#   - 'baseline_1978_1983': preserves exact 1991-2015 observationDates & observationPeriods in DC
#   - 'late_cohort_1984_1989': 2024 release for 1984-1989 cohort (adds 2016 / 2020-04-01 observations)
#   - 'annual_cohort_1978_1992': 2024 release by birth cohort 1978-1992 (adds 2005-2019 P1Y observations)
DATASET_CONFIGS = [
    ('commuting_zone_outcomes.csv', 'commuting_zone', 'baseline_1978_1983'),
    ('county_outcomes.csv', 'county', 'baseline_1978_1983'),
    ('tract_outcomes.csv', 'tract', 'baseline_1978_1983'),
    ('tract_outcomes_late_simple.csv', 'tract', 'late_cohort_1984_1989'),
    ('county_by_cohort_outcomes.csv', 'county', 'annual_cohort_1978_1992'),
    ('cz_by_cohort_outcomes.csv', 'commuting_zone', 'annual_cohort_1978_1992'),
]

RACES = collections.OrderedDict([
    ('pooled', ''),
    ('aian', 'USC_AmericanIndianAndAlaskaNativeAlone'),
    ('asian', 'USC_AsianAlone'),
    ('black', 'USC_BlackOrAfricanAmericanAlone'),
    ('hisp', 'USC_HispanicOrLatinoRace'),
    ('natam', 'USC_AmericanIndianAndAlaskaNativeAlone'),
    ('white', 'USC_WhiteAloneNotHispanicOrLatino'),
    ('other', 'OI_RaceOther'),
])

GENDERS = collections.OrderedDict([
    ('pooled', ''),
    ('male', 'Male'),
    ('female', 'Female'),
])

PERCENTILES = collections.OrderedDict([
    ('p100', 'Percentile100'),
    ('p10', 'Percentile10'),
    ('p1', 'Percentile1'),
    ('p25', 'Percentile25'),
    ('p50', 'Percentile50'),
    ('p75', 'Percentile75'),
])

# Exact measuredProperty names in /cns/jv-d/home/datcom/v3_resolved_mcf/oi/outcomes/20260722/statvars.mcf
OUTCOME_NEW_NAMES = {
    'coll': 'collegeGraduate',
    'comcoll': 'communityCollegeGraduate',
    'emp': 'fractionOfChildrenWithPositiveW2Earnings',
    'fpw': 'fractionChildhoodYearsSpentInGeography',
    'grad': 'hasGraduateDegree',
    'has_dad': 'fatherPresence',
    'has_mom': 'motherPresence',
    'hours_wk': 'weeklyHoursWorked',
    'hs': 'highSchoolGraduate',
    'jail': 'incarcerationRate',
    'kfi': 'householdIncome',
    'kfr': 'householdIncomeRank',
    'kfr_24': 'householdIncomeRankAge24',
    'kfr_26': 'householdIncomeRankAge26',
    'kfr_29': 'householdIncomeRankAge29',
    'kfr_imm': 'householdIncomeRankImmigantMother',
    'kfr_native': 'householdIncomeRankNativeMother',
    'kfr_stycz': 'householdIncomeRankLiveChildhoodCZ',
    'kfr_top01': 'householdIncomeTop1pct',
    'kfr_top20': 'householdIncomeRankTop20pct',
    'kii': 'individualIncome',
    'kir': 'meanPercentileIncomeRank',
    'kir_24': 'individualIncomeRankAge24',
    'kir_26': 'individualIncomeRankAge26',
    'kir_29': 'individualIncomeRankAge29',
    'kir_imm': 'individualIncomeRankImmigrantMother',
    'kir_native': 'individualIncomeRankNativeMother',
    'kir_stycz': 'individualIncomeRankLiveChildhoodCZ',
    'kir_top01': 'individualIncomeTop1pct',
    'kir_top20': 'individualIncomeRankTop20pct',
    'lpov_nbh': 'liveInLowPovertyNeighborhood',
    'marr_24': 'fractionChildrenMarriedAge24',
    'marr_26': 'fractionChildrenMarriedAge26',
    'marr_29': 'fractionChildrenMarriedAge29',
    'marr_32': 'fractionChildrenMarriedAge32',
    'married': 'fractionChildrenMarried',
    'par_rank': 'parentHouseholdIncomeRank',
    'pos_hours': 'positiveWorkHours',
    'proginc': 'receivesPublicAssistance',
    'somecoll': 'fractionOfChildrenWithSomeCollege',
    'spouse_rk': 'spouseIndividualIncomeRank',
    'staycz': 'liveChildhoodCZ',
    'stayhome': 'livingWithParents',
    'staytract': 'liveChildhoodTract',
    'teenbrth': 'teenageBirth',
    'two_par': 'twoParents',
    'wgflx_rk': 'hourlyWageRank',
    'work_24': 'fractionOfChildrenWithPositiveW2EarningsAge24',
    'work_26': 'fractionOfChildrenWithPositiveW2EarningsAge26',
    'work_29': 'fractionOfChildrenWithPositiveW2EarningsAge29',
    'work_32': 'fractionOfChildrenWithPositiveW2EarningsAge32',
    'working': 'fractionOfChildrenWithPositiveW2Earnings',
}

# Maps from outcome code to [default_prop, start_date, end_date, observation_period]
OUTCOMES = collections.OrderedDict([
    ('coll', ['collegeGraduate', '2003-01-01', '2015-01-01', 'P13Y']),
    ('comcoll', ['communityCollegeGraduate', '2003-01-01', '2015-01-01', 'P13Y']),
    ('emp', ['fractionOfChildrenWithPositiveW2Earnings', '2015-01-01', '2015-01-01', 'P1Y']),
    ('fpw', ['fractionChildhoodYearsSpentInGeography', '1994-01-01', '2006-01-01', 'P13Y']),
    ('grad', ['hasGraduateDegree', '2008-01-01', '2015-01-01', 'P8Y']),
    ('has_dad', ['fatherPresence', '1994-01-01', '2015-01-01', 'P22Y']),
    ('has_mom', ['motherPresence', '1994-01-01', '2015-01-01', 'P22Y']),
    ('hours_wk', ['weeklyHoursWorked', '2008-01-01', '2015-01-01', 'P8Y']),
    ('hs', ['highSchoolGraduate', '2000-01-01', '2015-01-01', 'P16Y']),
    ('jail', ['incarcerationRate', '2010-04-01', '2010-04-01', 'P1D']),
    ('kfi', ['householdIncome', '2014-01-01', '2015-01-01', 'P2Y']),
    ('kfr_imm', ['householdIncomeRankImmigantMother', '2014-01-01', '2015-01-01', 'P2Y']),
    ('kfr_native', ['householdIncomeRankNativeMother', '2014-01-01', '2015-01-01', 'P2Y']),
    ('kfr_stycz', ['householdIncomeRankLiveChildhoodCZ', '2014-01-01', '2015-01-01', 'P2Y']),
    ('kfr_top01', ['householdIncomeTop1pct', '2014-01-01', '2015-01-01', 'P2Y']),
    ('kfr_top20', ['householdIncomeRankTop20pct', '2014-01-01', '2015-01-01', 'P2Y']),
    ('kfr_24', ['householdIncomeRankAge24', '2002-01-01', '2007-01-01', 'P6Y']),
    ('kfr_26', ['householdIncomeRankAge26', '2004-01-01', '2009-01-01', 'P6Y']),
    ('kfr_29', ['householdIncomeRankAge29', '2007-01-01', '2012-01-01', 'P6Y']),
    ('kfr', ['householdIncomeRank', '2014-01-01', '2015-01-01', 'P2Y']),
    ('kii', ['individualIncome', '2014-01-01', '2015-01-01', 'P2Y']),
    ('kir_imm', ['individualIncomeRankImmigrantMother', '2014-01-01', '2015-01-01', 'P2Y']),
    ('kir_native', ['individualIncomeRankNativeMother', '2014-01-01', '2015-01-01', 'P2Y']),
    ('kir_stycz', ['individualIncomeRankLiveChildhoodCZ', '2014-01-01', '2015-01-01', 'P2Y']),
    ('kir_top01', ['individualIncomeTop1pct', '2014-01-01', '2015-01-01', 'P2Y']),
    ('kir_top20', ['individualIncomeRankTop20pct', '2014-01-01', '2015-01-01', 'P2Y']),
    ('kir_24', ['individualIncomeRankAge24', '2002-01-01', '2007-01-01', 'P6Y']),
    ('kir_26', ['individualIncomeRankAge26', '2004-01-01', '2009-01-01', 'P6Y']),
    ('kir_29', ['individualIncomeRankAge29', '2007-01-01', '2012-01-01', 'P6Y']),
    ('kir', ['meanPercentileIncomeRank', '2014-01-01', '2015-01-01', 'P2Y']),
    ('lpov_nbh', ['liveInLowPovertyNeighborhood', '2015-01-01', '2015-01-01', 'P1Y']),
    ('married', ['fractionChildrenMarried', '2015-01-01', '2015-01-01', 'P1Y']),
    ('marr_24', ['fractionChildrenMarriedAge24', '2002-01-01', '2007-01-01', 'P6Y']),
    ('marr_26', ['fractionChildrenMarriedAge26', '2004-01-01', '2009-01-01', 'P6Y']),
    ('marr_29', ['fractionChildrenMarriedAge29', '2007-01-01', '2012-01-01', 'P6Y']),
    ('marr_32', ['fractionChildrenMarriedAge32', '2010-01-01', '2015-01-01', 'P6Y']),
    ('pos_hours', ['positiveWorkHours', '2008-01-01', '2015-01-01', 'P8Y']),
    ('proginc', ['receivesPublicAssistance', '2008-01-01', '2015-01-01', 'P8Y']),
    ('somecoll', ['fractionOfChildrenWithSomeCollege', '2003-01-01', '2015-01-01', 'P13Y']),
    ('spouse_rk', ['spouseIndividualIncomeRank', '2014-01-01', '2015-01-01', 'P2Y']),
    ('staycz', ['liveChildhoodCZ', '1996-01-01', '2015-01-01', 'P20Y']),
    ('stayhome', ['livingWithParents', '2015-01-01', '2015-01-01', 'P1Y']),
    ('staytract', ['liveChildhoodTract', '1996-01-01', '2015-01-01', 'P20Y']),
    ('teenbrth', ['teenageBirth', '1991-01-01', '2002-01-01', 'P12Y']),
    ('two_par', ['twoParents', '1994-01-01', '2015-01-01', 'P22Y']),
    ('wgflx_rk', ['hourlyWageRank', '2008-01-01', '2015-01-01', 'P8Y']),
    ('working', ['fractionOfChildrenWithPositiveW2Earnings', '2015-01-01', '2015-01-01', 'P1Y']),
    ('work_24', ['fractionOfChildrenWithPositiveW2EarningsAge24', '2002-01-01', '2007-01-01', 'P6Y']),
    ('work_26', ['fractionOfChildrenWithPositiveW2EarningsAge26', '2004-01-01', '2009-01-01', 'P6Y']),
    ('work_29', ['fractionOfChildrenWithPositiveW2EarningsAge29', '2007-01-01', '2012-01-01', 'P6Y']),
    ('work_32', ['fractionOfChildrenWithPositiveW2EarningsAge32', '2010-01-01', '2015-01-01', 'P6Y']),
])

NON_OUTCOMES = collections.OrderedDict([
    ('par_rank', ['parentHouseholdIncomeRank', '1994-01-01', '2000-01-01', 'P7Y']),
    ('kid_n', ['childrenUnder18', '2000-04-01', '2000-04-01', 'P1D']),
    ('frac_below_median', ['belowMedianIncome', '1994-01-01', '2000-01-01', 'P7Y']),
    ('kid_blw_p50', ['childrenBelowMedianIncomeFamilies', '1994-01-01', '2000-01-01', 'P7Y']),
    ('frac_years_xw', ['fractionChildhoodYearsSpentInGeography', '1994-01-01', '2006-01-01', 'P13Y']),
])

_DATE_LEN = {'Y': 4, 'M': 7, 'D': 10}

OUTPUT_FIELDNAMES = [
    'geo_id',
    'measured_property',
    'stat_type',
    'race',
    'gender',
    'parent_income',
    'observation_date',
    'observation_period',
    'value',
]


def get_measured_property(outcome_code: str) -> str:
    """Returns the exact measuredProperty name matching production statvars.mcf."""
    if outcome_code in OUTCOME_NEW_NAMES:
        return OUTCOME_NEW_NAMES[outcome_code]
    if outcome_code in OUTCOMES:
        return OUTCOMES[outcome_code][0]
    if outcome_code in NON_OUTCOMES:
        return NON_OUTCOMES[outcome_code][0]
    raise ValueError(f'Unknown outcome code: {outcome_code}')


def format_obs_date(date_string: str, duration: str) -> str:
    """Truncates YYYY-MM-DD based on duration unit (Y -> 4 chars, M -> 7, D -> 10)."""
    return date_string[: _DATE_LEN[duration[-1]]]


def format_geo_id(row: dict, geo_level: str) -> str:
    """Returns the Data Commons geoId dcid for a CSV row."""
    if geo_level == 'county':
        state = str(int(float(str(row['state']).strip()))).zfill(2)
        county = str(int(float(str(row['county']).strip()))).zfill(3)
        return f'geoId/{state}{county}'
    if geo_level == 'tract':
        state = str(int(float(str(row['state']).strip()))).zfill(2)
        county = str(int(float(str(row['county']).strip()))).zfill(3)
        tract = str(int(float(str(row['tract']).strip()))).zfill(6)
        return f'geoId/{state}{county}{tract}'
    if geo_level == 'commuting_zone':
        cz = str(int(float(str(row['cz']).strip()))).zfill(5)
        return f'geoId/cz{cz}'
    raise ValueError(f'Unsupported geo_level: {geo_level}')


def parse_population_slices(formatted_col: str) -> tuple[str, str, str]:
    """Extracts (race, gender, parent_income) from formatted column slice."""
    race_pattern = '|'.join(RACES.keys())
    gender_pattern = '|'.join(GENDERS.keys())
    percentile_pattern = '|'.join(PERCENTILES.keys())

    rgp_match = re.fullmatch(
        f'({race_pattern})_({gender_pattern})_({percentile_pattern})',
        formatted_col,
    )
    if rgp_match:
        return (
            RACES[rgp_match.group(1)],
            GENDERS[rgp_match.group(2)],
            PERCENTILES[rgp_match.group(3)],
        )

    rg_match = re.fullmatch(f'({race_pattern})_({gender_pattern})', formatted_col)
    if rg_match:
        return (
            RACES[rg_match.group(1)],
            GENDERS[rg_match.group(2)],
            '',
        )
    raise ValueError(f'Unable to parse population slice: {formatted_col}')


def classify_column(col: str):
    """Classifies a CSV header column into (metric_code, slice_key, stat_type, obs_date, obs_period)."""
    outcome_pattern = '|'.join(OUTCOMES.keys())
    outcome_match = re.fullmatch(f'({outcome_pattern})_(\\w+)', col)
    if outcome_match:
        outcome = outcome_match.group(1)
        rest = outcome_match.group(2)
        meta_match = re.fullmatch(r'(\w+?)_(mean_se|mean|se|n)', rest)
        if meta_match:
            formatted_name = meta_match.group(1)
            meta = meta_match.group(2)
        else:
            formatted_name = rest
            meta = None

        try:
            parse_population_slices(formatted_name)
        except ValueError:
            return None

        stat_type_map = {
            None: 'measuredValue',
            'se': 'stdError',
            'mean': 'meanValue',
            'mean_se': 'meanStdError',
            'n': 'sampleSize',
        }
        _, start_time, _, duration = OUTCOMES[outcome]
        return (
            outcome,
            formatted_name,
            stat_type_map[meta],
            format_obs_date(start_time, duration),
            duration,
        )

    race_pattern = '|'.join(RACES.keys())
    gender_pattern = '|'.join(GENDERS.keys())
    par_rank_match = re.fullmatch(
        f'par_rank_(({race_pattern})_({gender_pattern}))_(mean_se|mean)', col
    )
    if par_rank_match:
        formatted_name = par_rank_match.group(1)
        meta = par_rank_match.group(4)
        stat_type = 'meanValue' if meta == 'mean' else 'meanStdError'
        _, start_time, _, duration = NON_OUTCOMES['par_rank']
        return (
            'par_rank',
            formatted_name,
            stat_type,
            format_obs_date(start_time, duration),
            duration,
        )

    non_outcome_patterns = [
        ('kid_n', f'kid_(({race_pattern})_({gender_pattern}))_n'),
        ('kid_n', f'(({race_pattern})_({gender_pattern}))_count'),
        ('frac_below_median', f'frac_below_median_(({race_pattern})_({gender_pattern}))'),
        ('kid_blw_p50', f'kid_(({race_pattern})_({gender_pattern}))_blw_p50_n'),
        ('kid_blw_p50', f'(({race_pattern})_({gender_pattern}))_blw_p50_count'),
        ('frac_years_xw', f'frac_years_xw_(({race_pattern})_({gender_pattern}))'),
    ]
    for code, pat in non_outcome_patterns:
        m = re.fullmatch(pat, col)
        if m:
            formatted_name = m.group(1)
            _, start_time, _, duration = NON_OUTCOMES[code]
            return (
                code,
                formatted_name,
                'measuredValue',
                format_obs_date(start_time, duration),
                duration,
            )

    return None


def resolve_date_and_period(
    row: dict,
    dataset_mode: str,
    metric_code: str,
    default_obs_date: str,
    default_obs_period: str,
) -> tuple[str, str]:
    """Computes (observation_date, observation_period) so baseline rows match DC and new cohorts add new dates."""
    if dataset_mode == 'baseline_1978_1983':
        return default_obs_date, default_obs_period

    if dataset_mode == 'late_cohort_1984_1989':
        # 1984-1989 cohort outcomes measured in 2011-2016 (age 27) and 2020 Census for incarceration
        if metric_code == 'jail':
            return '2020-04-01', 'P1D'
        if metric_code == 'kid_n':
            return '2010-04-01', 'P1D'
        return '2016', 'P6Y'

    if dataset_mode == 'annual_cohort_1978_1992':
        # Birth cohorts 1978-1992 measured at age 27 -> observation years 2005-2019 (P1Y)
        row_cohort = (row.get('cohort') or '').strip()
        if row_cohort:
            try:
                return str(int(float(row_cohort)) + 27), 'P1Y'
            except ValueError:
                pass

    return default_obs_date, default_obs_period


_MISSING_VALUE_PLACEHOLDERS = frozenset({'', 'NA', 'N/A', '.', 'NAN', 'NULL'})


def _get_shard_path(output_csv: str, shard_idx: int) -> str:
    """Returns the output path for a given 0-based shard index."""
    if shard_idx == 0:
        return output_csv
    if output_csv.endswith('_cleaned.csv'):
        base = output_csv[: -len('_cleaned.csv')]
        return f'{base}_part_{shard_idx:03d}_cleaned.csv'
    stem, ext = os.path.splitext(output_csv)
    return f'{stem}_part_{shard_idx:03d}{ext}'


def process_csv_file(
    input_csv: str,
    output_csv: str,
    geo_level: str,
    dataset_mode: str = 'baseline_1978_1983',
    max_rows_per_shard: int = 5_000_000,
) -> int:
    """Converts a wide Opportunity Atlas CSV into sharded normalized CSV(s) for stat_var_processor.py."""
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    rows_written = 0
    shard_idx = 0
    shard_rows = 0

    outfile = open(
        _get_shard_path(output_csv, shard_idx),
        mode='w',
        encoding='utf-8',
        newline='',
    )
    try:
        writer = csv.DictWriter(outfile, fieldnames=OUTPUT_FIELDNAMES)
        writer.writeheader()

        with open(input_csv, mode='r', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            col_specs = {}
            for col in reader.fieldnames or []:
                spec = classify_column(col)
                if spec:
                    col_specs[col] = spec

            for row in reader:
                geo_id = format_geo_id(row, geo_level)

                for col, (
                    metric_code,
                    formatted_name,
                    stat_type,
                    obs_date,
                    obs_period,
                ) in col_specs.items():
                    raw_val = (row.get(col) or '').strip()
                    if raw_val.upper() in _MISSING_VALUE_PLACEHOLDERS:
                        continue
                    if max_rows_per_shard > 0 and shard_rows >= max_rows_per_shard:
                        outfile.close()
                        shard_idx += 1
                        shard_rows = 0
                        outfile = open(
                            _get_shard_path(output_csv, shard_idx),
                            mode='w',
                            encoding='utf-8',
                            newline='',
                        )
                        writer = csv.DictWriter(
                            outfile, fieldnames=OUTPUT_FIELDNAMES
                        )
                        writer.writeheader()

                    resolved_date, resolved_period = resolve_date_and_period(
                        row, dataset_mode, metric_code, obs_date, obs_period
                    )
                    race, gender, parent_income = parse_population_slices(
                        formatted_name
                    )
                    writer.writerow({
                        'geo_id': geo_id,
                        'measured_property': get_measured_property(metric_code),
                        'stat_type': stat_type,
                        'race': race,
                        'gender': gender,
                        'parent_income': parent_income,
                        'observation_date': resolved_date,
                        'observation_period': resolved_period,
                        'value': raw_val,
                    })
                    rows_written += 1
                    shard_rows += 1
    finally:
        outfile.close()

    logging.info(
        'Wrote %d normalized observation rows across %d shard(s) for %s',
        rows_written,
        shard_idx + 1,
        output_csv,
    )
    return rows_written


def main(_):
    os.makedirs(FLAGS.input_dir, exist_ok=True)
    os.makedirs(FLAGS.output_dir, exist_ok=True)

    if FLAGS.download:
        download_script.download_all_sources(FLAGS.input_dir)

    for filename, geo_level, dataset_mode in DATASET_CONFIGS:
        input_path = os.path.join(FLAGS.input_dir, filename)
        if not os.path.exists(input_path):
            raise FileNotFoundError(
                f'Required input file not found for {filename}: {input_path}'
            )
        stem = os.path.splitext(filename)[0]
        output_path = os.path.join(FLAGS.output_dir, f'{stem}_cleaned.csv')
        process_csv_file(
            input_path,
            output_path,
            geo_level,
            dataset_mode,
            max_rows_per_shard=FLAGS.max_rows_per_shard,
        )


if __name__ == '__main__':
    app.run(main)
