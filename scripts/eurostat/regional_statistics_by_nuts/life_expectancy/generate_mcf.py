# Copyright 2020 Google LLC
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

import pandas as pd
import re


def convert_range(s_input):
    """Convert range values from the format in statvar names (e.g. 10YearsOrMore)
     to the format as QuantityRange (e.g. [Years 10 -]) in Data Commons."""
    if 'OrMore' in s_input:
        match = re.fullmatch(r'(\d+)OrMore([a-zA-Z]+)', s_input)
        num = match.group(1)
        unit = match.group(2)
        return '[{} {} -]'.format(unit, num)
    elif 'Upto' in s_input:
        match = re.fullmatch(r'Upto(\d+)([a-zA-Z]+)', s_input)
        num = match.group(1)
        unit = match.group(2)
        return '[{} - {}]'.format(unit, num)
    elif 'To' in s_input:
        match = re.fullmatch(r'(\d+)To(\d+)([a-zA-Z]+)', s_input)
        num1 = match.group(1)
        num2 = match.group(2)
        unit = match.group(3)
        return '[{} {} {}]'.format(unit, num1, num2)
    else:
        match = re.fullmatch(r'(\d+)([a-zA-Z]+)', s_input)
        num = match.group(1)
        unit = match.group(2)
        return '[{} {}]'.format(unit, num)


def generate_statvar(statvars, path):
    """Generate the statvars from the list of statvar names."""
    by_age_template = ('Node: dcid:{stat_var}\n'
                       'typeOf: dcs:StatisticalVariable\n'
                       'populationType: schema:Person\n'
                       'age: {age}\n'
                       'measuredProperty: dcs:lifeExpectancy\n'
                       'statType: dcs:measuredValue\n\n')

    by_age_gender_template = by_age_template[:-1] + 'gender: schema:{gender}\n\n'

    with open(path, 'w') as f_out:
        for stat_var in statvars:
            keys = stat_var.split('_')
            if len(keys) < 3:
                raise Exception("Invalid StatVar")
            age = convert_range(keys[2])
            if len(keys) == 3:  # measuredPropery_populationType_age
                f_out.write(
                    by_age_template.format_map({
                        'stat_var': stat_var,
                        'age': age
                    }))
            elif len(keys) == 4:  # measuredPropery_populationType_age_gender
                gender = keys[-1]
                f_out.write(
                    by_age_gender_template.format_map({
                        'stat_var': stat_var,
                        'age': age,
                        'gender': gender
                    }))


def generate_tmcf(statvars, path):
    """Generate the template mcf."""
    statvar_template = ('Node: E:lifexp->E{sv_index}\n'
                        'typeOf: dcs:StatVarObservation\n'
                        'variableMeasured: dcs:{stat_var}\n'
                        'observationAbout: C:lifexp->{geo_col}\n'
                        'observationDate: C:lifexp->{year_col}\n'
                        'measurementMethod: dcs:EurostatRegionalStatistics\n'
                        'value: C:lifexp->{stat_var}\n\n')

    with open(path, 'w') as f_out:
        i = 1
        for stat_var in statvars:
            f_out.write(
                statvar_template.format_map({
                    'sv_index': i,
                    'stat_var': stat_var,
                    'year_col': stat_var + '_year',
                    'geo_col': stat_var + '_geo'
                }))
            i += 1


def main():
    CLEANED_CSV = "demo_r_mlifexp_cleaned.csv"
    statvars = []
    # Get all the statvar names from the columns of csv files.
    # Each statvar has three columns: sv, sv_geo, sv_year.
    for col in pd.read_csv(CLEANED_CSV, nrows=0).columns:
        if col[-4:] != '_geo' and col[-5:] != '_year':
            statvars.append(col)
    generate_statvar(statvars,
                     CLEANED_CSV.replace('_cleaned.csv', '_statvar.mcf'))
    generate_tmcf(statvars, CLEANED_CSV.replace('_cleaned.csv', '.tmcf'))
    return


if __name__ == '__main__':
    main()
