import sys
import pandas as pd
import re

def convert_range(s_input):
    """Convert range values from the format in StatVars to the format as 
        QuantityRange in Data Commons"""
    if 'OrMore' in s_input:
        match = re.match(r'(\d+)OrMore([a-zA-Z]+)', s_input)
        num = match.group(1)
        unit = match.group(2)
        return '[{} {} -]'.format(unit, num)
    elif 'Upto' in s_input:
        match = re.match(r'Upto(\d+)([a-zA-Z]+)', s_input)
        num = match.group(1)
        unit = match.group(2)
        return '[{} - {}]'.format(unit, num)
    elif 'To' in s_input:
        match = re.match(r'(\d+)To(\d+)([a-zA-Z]+)', s_input)
        num1 = match.group(1)
        num2 = match.group(2)
        unit = match.group(3)
        return '[{} {} {}]'.format(unit, num1, num2)
    else:
        match = re.match(r'(\d+)([a-zA-Z]+)', s_input)
        num = match.group(1)
        unit = match.group(2)
        return '[{} {}]'.format(unit, num)
  
def generate_statvar(statvars, path):
    """generate the statvars from the list of StatVar names"""
    by_age_template = ('Node: dcid:{stat_var}\n'
                               'typeOf: dcs:StatisticalVariable\n'
                               'populationType: schema:Person\n'
                               'age: {age}\n'
                               'measuredProperty: dcs:lifeExpectancy\n'
                               'statType: dcs:measuredValue\n'
                               'unit: dcs:Year\n\n')
    by_age_gender_template = by_age_template[:-1] + 'gender: schema:{gender}\n\n'

    with open(path, 'w') as f_out:
        for stat_var in statvars:
            keys = stat_var.split('_')
            age = convert_range(keys[2])
            if len(keys) == 3:
                f_out.write(by_age_template.format_map({'stat_var':stat_var,
                    'age':age}))
            else:
                gender = keys[-1]
                f_out.write(by_age_gender_template.format_map({'stat_var':stat_var,
                    'age':age, 'gender': gender}))

def generate_tmcf(statvars, path):
    """generate the templated mcf """
    statvar_template = ('Node: E:lifexp->E{sv_index}\n'
                    'typeOf: dcs:StatVarObservation\n'
                    'variableMeasured: dcs:{stat_var}\n'
                    'observationAbout: C:lifexp->{geo_col_name}\n'
                    'observationDate: C:lifexp->{year_col}\n'
                    'measurementMethod: dcs:EurostatRegionalStatistics\n'
                    'value: C:lifexp->{stat_var}\n\n')
    
    with open(path, 'w') as f_out:
        i = 0
        for stat_var in statvars:
            f_out.write(statvar_template.format_map({'sv_index': i+1,
                'stat_var': stat_var, 'year_col': stat_var+'_year', 
                'geo_col_name': stat_var+'_geo'}))
            i += 1

def main():
    CLEANED_CSV = "demo_r_mlifexp_cleaned.csv"
    statvars = []
    for col in pd.read_csv(CLEANED_CSV,nrows=0).columns:
        keys = col.split('_')
        if keys[-1] == 'geo':
            continue
        elif keys[-1] == 'year':
            continue
        else:
            statvars.append(col)
    generate_statvar(statvars, CLEANED_CSV.replace('_cleaned.csv', '_statvar.mcf'))
    generate_tmcf(statvars, CLEANED_CSV.replace('_cleaned.csv', '.tmcf'))
    return

if __name__ == '__main__':
    main()