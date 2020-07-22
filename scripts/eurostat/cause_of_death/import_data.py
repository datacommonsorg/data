from og113 import ICD10_113_MAP
import pandas as pd
import re


def read_dict(filename):
    with open(filename, 'r') as f:
        lines = f.readlines()
    d = {}
    for line in lines:
        line = line.strip()
        line_list = line.split('\t')
        if len(line_list) != 2:
            raise NotImplementedError
        else:
            line_list[0] = line_list[0].strip()
            line_list[1] = line_list[1].strip()
            d[line_list[0]] = line_list[1]
    return d


def find_intersection(icd10_dict, icd10_113_dict, cause_dict):
    # find intersection of cause of death between three sources
    new_cause_dict = {}
    transformation_dict = {}
    for k in cause_dict:
        if len(k) == 1:  # if the cause of death is only 1 letter, need to see what range it actually refers to
            pattern = re.findall('\((.*)\)', cause_dict[k])
            if len(pattern) != 1:
                print(pattern)
                raise NotImplementedError
            else:
                new_key = pattern[0]
            new_cause_dict[new_key] = cause_dict[k]
            transformation_dict[new_key] = k
        else:
            new_cause_dict[k] = cause_dict[k]
    intersection_1 = set(new_cause_dict.keys()).intersection(icd10_dict)
    intersection_2 = set(new_cause_dict.keys()).intersection(icd10_113_dict)
    return intersection_1, intersection_2, transformation_dict, new_cause_dict


def generate_mcf_text(intersection_1, intersection_2, transformation_dict, new_cause_dict, path):
    # generate new enums for cause
    count = 0
    with open(path, 'w') as f:
        for k, v in new_cause_dict.items():
            if k not in intersection_1 and k not in intersection_2:
                count += 1
                if k in transformation_dict:
                    k = transformation_dict[k]
                k = k.replace('_OTH', ' and other')
                k = k.replace('_', ',')
                pattern = re.findall('( \(.*\).*)', v)
                if len(pattern) == 0:
                    pattern = ''
                elif len(pattern) == 1:
                    pattern = pattern[0]
                else:
                    raise NotImplementedError
                v = re.sub('(\(.*\).*)', '', v)
                v = v.title().replace(' ', '').replace(',', '_')
                f.write(
                    "Node: dcid:%s\ntypeOf: dcs:ICD10Code\nname: \"%s\"\ndescription: \"Corresponds to ICD10 Codes %s\"\n\n" % (
                        v, v, k + pattern))
    print('generate {0} new cause enums out of {1}'.format(count, len(new_cause_dict)))


def convert_range(s_input):
    """ (Reused from Lijuan's code) Convert range values from the format in statvar names (e.g. 10YearsOrMore)
     to the format as QuantityRange (e.g. [Years 10 -]) in Data Commons."""
    if 'or over' in s_input:
        match = re.findall(r'(\d+).*or over', s_input)[0]
        num = match[0]
        unit = 'Years'
        return '[{} {} -]'.format(unit, num)
    elif 'Less than' in s_input:
        match = re.findall(r'Less than (\d+).*', s_input)[0]
        num = match[0]
        unit = 'Years'
        return '[{} - {}]'.format(unit, num)
    elif 'to' in s_input:
        match = re.findall(r'(\d+) to (\d+).*', s_input)[0]
        num1 = match[0]
        num2 = match[1]
        unit = 'Years'
        return '[{} {} {}]'.format(unit, num1, num2)
    else:
        raise NotImplementedError


def translate_column(column, age_dict, intersection_1, intersection_2, icd10_dict, icd10_113_dict, reverse_transformation_dict, cause_dict, gender_dict):
    if column == 'geo' or column == 'time':
        return column
    column_list = column.split('|')[1:]  # remove unit RT here
    gender, age, cause = column_list

    # get the stat var
    age = age_dict[age]
    age_stat_var = age.title().replace(' ', '').replace('Total', '')
    if age_stat_var != '':
        age_field = convert_range(age)
    else:
        age_field = ''
    gender = gender_dict[gender]
    gender_stat_var = gender.replace('Total', '')
    gender_field = gender_stat_var
    if cause in reverse_transformation_dict:
        cause_transformed = reverse_transformation_dict[cause]
    else:
        cause_transformed = cause
    if cause_transformed in intersection_1:
        cause_description = icd10_dict[cause_transformed]
        # # if cause in reverse_transformation_dict:  # remove things in the bracket
        # cause_description = re.sub('(\(.*\d+-.*\).*)', '', cause_description)
        cause_stat_var = cause_description.title().replace(' ', '').replace(',', '_')
        cause_field = 'ICD10/' + cause_transformed
    elif cause_transformed in intersection_2:
        cause_description = icd10_113_dict[cause_transformed]
        cause_stat_var = cause_description.title().replace(' ', '').replace(',', '_')
        cause_field = cause_stat_var
    else:
        cause_description = cause_dict[cause]  # follow generate mcf
        cause_stat_var = re.sub('(\(.*\).*)', '', cause_description).title().replace(' ', '').replace(',', '_').replace('AllCausesOfDeath', '')
        cause_field = cause_stat_var
    combined_stat_var = ''
    for stat_var in [age_stat_var, cause_stat_var, gender_stat_var]:
        if stat_var == '':
            continue
        else:
            combined_stat_var += stat_var + '_'
    if combined_stat_var != '':
        combined_stat_var = combined_stat_var[:-1]
    return [combined_stat_var, age_field, cause_field, gender_field]


def generate_stat_var(path, nested_list):
    base_template = ('Node: dcid:{0}\n'
                     'typeOf: dcs:StatisticalVariable\n'
                     'populationType: schema:MortalityEvent\n'
                     'measuredProperty: dcs:count\n'
                     'statType: dcs:measuredValue\n'
                     'measurementDenominator: dcs:Count_Person\n')
    optional_template = ['age: {0}\n', 'causeOfDeath: dcs:{0}\n', 'sex: schema:{0}\n']
    with open(path, 'w') as f:
        for i in range(len(nested_list)):
            combined_stat_var = nested_list[i][0]
            fields = nested_list[i][1:]
            out = base_template.format(combined_stat_var)
            for j in range(3):
                field = fields[j]
                if field != '':
                    out += optional_template[j].format(field)
            out += '\n'
            f.write(out)


def generate_tmcf(statvars, path):
    """Generate the template mcf."""
    statvar_template = ('Node: E:causedeath->E{0}\n'
                        'typeOf: dcs:StatVarObservation\n'
                        'variableMeasured: dcs:{1}\n'
                        'observationAbout: C:causedeath->geo\n'
                        'observationDate: C:causedeath->time\n'
                        'measurementMethod: dcs:EurostatRegionalStatistics\n'
                        'value: C:causedeath->{1}\n\n')

    with open(path, 'w') as f_out:
        for i in range(len(statvars)):
            f_out.write(statvar_template.format(i, statvars[i]))


def main():
    cause_dict = read_dict('causes.txt')  # from Eurostats
    icd10 = pd.read_csv('bq_icd10.csv')  # this is the csv downloaded from BQ
    age_dict = read_dict('age.txt')  # from Eurostats
    gender_dict = {'T': 'Total', 'M': 'Male', 'F': 'Female'}
    icd10_ids = list(icd10['id'].str.replace('ICD10/', ''))
    icd10_description = list(icd10['name'])
    icd10_dict = {}
    for i in range(len(icd10_ids)):
        icd10_dict[icd10_ids[i]] = icd10_description[i]
    intersection_1, intersection_2, transformation_dict, new_cause_dict = find_intersection(icd10_dict, ICD10_113_MAP,
                                                                                            cause_dict)
    reverse_transformation_dict = {}
    for k, v in transformation_dict.items():  # {'C00-C97': C}
        reverse_transformation_dict[v] = k  # {'C': 'C00-C97'}

    generate_mcf_text(intersection_1, intersection_2, transformation_dict, new_cause_dict, 'causes.mcf')

    data = pd.read_csv('hlth_cd_acdr2_processed.csv', usecols=list(range(2 + 7364)))  # read geo, time and 7364 stats vars
    data = data.replace(':', '')
    data.to_csv('hlth_cd_acdr2_final.csv', index=False)
    data = pd.read_csv('hlth_cd_acdr2_final.csv')
    data[data.columns[2:]] = data[data.columns[2:]].astype('float64') / 1000
    data['geo'] = 'dcid:nuts/' + data['geo']

    stat_vars = []
    new_column_names = ['geo', 'time']
    for column in data.columns[2:]:  # ignore geo and time
        stat_vars.append(translate_column(column, age_dict, intersection_1, intersection_2, icd10_dict, ICD10_113_MAP,
                                          reverse_transformation_dict, cause_dict, gender_dict))
        if stat_vars[-1][0] != '':
            stat_vars[-1][0] = 'Count_MortalityEvent_' + stat_vars[-1][0] + '_Count_Person'
        else:
            stat_vars[-1][0] = 'Count_MortalityEvent_Count_Person'
        new_column_names.append(stat_vars[-1][0])
    generate_stat_var('hlth_cd_acdr2_statvar.mcf', stat_vars)
    data.columns = new_column_names
    data.to_csv('hlth_cd_acdr2_final.csv', index=False)
    generate_tmcf(new_column_names[2:], 'hlth_cd_acdr2.tmcf')


if __name__ == '__main__':
    main()
