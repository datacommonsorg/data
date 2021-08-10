"""Process the data from Census ACS5Year Table S2201."""

import csv
from google.cloud import storage
import io

_STAT_VAR_LIST = 'stat_vars.csv'
_BUCKET = 'datcom-csv'
_INPUT = 'census/acs5yr/subject_tables/s2201/'

_TMCF_TEMPLATE = """
Node: E:S2201->E{index}
typeOf: dcs:StatVarObservation
variableMeasured: dcs:{stat_var}
measurementMethod: dcs:CensusACS5yrSurvey
observationDate: C:S2201->observationDate
observationAbout: C:S2201->observationAbout
value: C:S2201->{stat_var}{unit}
"""

_UNIT_TEMPLATE = """
unit: dcs:USDollar"""

_FEATURE_TO_PROPERTY = {
    'Households receiving food stamps':
        'WithFoodStampsInThePast12Months',
    'Households receiving food stamps/SNAP':
        'WithFoodStampsInThePast12Months',
    'Households receiving food stamps/SNAP MOE':
        'WithFoodStampsInThePast12Months',
    'With one or more people 60 years and over':
        'WithPeopleOver60',
    'With one or more people in the household 60 years and over':
        'WithPeopleOver60',
    'No people in the household 60 years and over':
        'WithoutPeopleOver60',
    'Married-couple family':
        'MarriedCoupleFamilyHousehold',
    'Other family':
        'OtherFamilyHousehold',
    'Other family:':
        'OtherFamilyHousehold',
    'Male householder, no wife present':
        'SingleFatherFamilyHousehold',
    'Male householder, no spouse present':
        'SingleFatherFamilyHousehold',
    'Female householder, no husband present':
        'SingleMotherFamilyHousehold',
    'Female householder, no spouse present':
        'SingleMotherFamilyHousehold',
    'Nonfamily households':
        'NonfamilyHousehold',
    'With children under 18 years':
        'WithChildrenUnder18',
    'No children under 18 years':
        'WithoutChildrenUnder18',
    'Below poverty level':
        'BelowPovertyLevelInThePast12Months',
    'At or above poverty level':
        'AbovePovertyLevelInThePast12Months',
    'At or above  poverty level':
        'AbovePovertyLevelInThePast12Months',
    'With one or more people with a disability':
        'WithDisability',
    'With no persons with a disability':
        'NoDisability',
    'One race':
        'OneRace',
    'White':
        'WhiteAlone',
    'White alone':
        'WhiteAlone',
    'Black or African American':
        'BlackOrAfricanAmericanAlone',
    'Black or African American alone':
        'BlackOrAfricanAmericanAlone',
    'American Indian and Alaska Native':
        'AmericanIndianOrAlaskaNativeAlone',
    'American Indian and Alaska Native alone':
        'AmericanIndianOrAlaskaNativeAlone',
    'Asian':
        'AsianAlone',
    'Asian alone':
        'AsianAlone',
    'Native Hawaiian and Other Pacific Islander':
        'NativeHawaiianOrOtherPacificIslanderAlone',
    'Native Hawaiian and Other Pacific Islander alone':
        'NativeHawaiianOrOtherPacificIslanderAlone',
    'Some other race':
        'SomeOtherRaceAlone',
    'Some other race alone':
        'SomeOtherRaceAlone',
    'Two or more races':
        'TwoOrMoreRaces',
    'Hispanic or Latino origin (of any race)':
        'HispanicOrLatino',
    'White alone, not Hispanic or Latino':
        'WhiteAloneNotHispanicOrLatino',
    'Families':
        'FamilyHousehold',
    'No workers in past 12 months':
        'NoWorkersInThePast12Months',
    '1 worker in past 12 months':
        'OneWorkerInThePast12Months',
    '2 or more workers in past 12 months':
        'TwoOrMoreWorkersInThePast12Months',
    'Households not receiving food stamps':
        'WithoutFoodStampsInThePast12Months',
    'Households not receiving food stamps/SNAP':
        'WithoutFoodStampsInThePast12Months',
    'Households not receiving food stamps/SNAP MOE':
        'WithoutFoodStampsInThePast12Months',
}


def convert_column_to_stat_var(column):
    """Converts input CSV column name to Statistical Variable DCID."""
    s = column.split('!!')
    if 'Median income (dollars)' in s:
        sv = ['Median_Income_Household']
    else:
        sv = ['Count_Household']
    for p in s:

        # Prefix MOE SVs
        if p == 'Margin of Error':
            sv = ['MarginOfError'] + sv

        # Only include the most specific enum value when there are multiple
        elif p == 'Other family:' and (
                'Male householder, no spouse present' in s or
                'Female householder, no spouse present' in s):
            continue
        elif p == 'Other family' and (
                'Male householder, no wife present' in s or
                'Female householder, no husband present' in s):
            continue
        elif p == 'One race' and (
                'White' in s or 'Black or African American' in s or
                'American Indian and Alaska Native' in s or 'Asian' in s or
                'Native Hawaiian and Other Pacific Islander' in s or
                'Some other race' in s):
            continue

        elif p in _FEATURE_TO_PROPERTY:

            # Work status is only provided for FamilyHousehold
            if ((p == 'No workers in past 12 months' or
                 p == '1 worker in past 12 months' or
                 p == '2 or more workers in past 12 months') and
                    'Families' not in s):
                sv.append(_FEATURE_TO_PROPERTY['Families'])
            sv.append(_FEATURE_TO_PROPERTY[p])
    return '_'.join(sv)


def create_csv(output, stat_vars):
    """Creates output CSV file."""
    fieldnames = ['observationDate', 'observationAbout'] + stat_vars
    with open(output, 'w') as f_out:
        writer = csv.DictWriter(f_out, fieldnames=fieldnames)
        writer.writeheader()


def write_csv(filename, reader, output, stat_vars):
    """Reads input_file and writes cleaned CSV to output."""
    if 'ACSST5Y' not in filename:
        return
    fieldnames = ['observationDate', 'observationAbout'] + stat_vars
    stat_var_set = set(stat_vars)
    with open(output, 'a') as f_out:
        writer = csv.DictWriter(f_out, fieldnames=fieldnames)
        observation_date = filename.split('ACSST5Y')[1][:4]
        valid_columns = {}
        for row in reader:
            if row['GEO_ID'] == 'id':

                # Map feature names to stat vars
                for c in row:
                    sv = convert_column_to_stat_var(row[c])
                    if sv in stat_var_set:
                        valid_columns[c] = sv
                continue

            new_row = {
                'observationDate': observation_date,
                'observationAbout': 'dcid:geoId/' + row['GEO_ID'].split('US')[1]
            }
            for c in row:

                # We currently only support the stat vars in the list
                if c not in valid_columns:
                    continue
                sv = valid_columns[c]

                # Exclude missing values
                if (row[c] == '**' or row[c] == '-' or row[c] == '***' or
                        row[c] == '*****' or row[c] == 'N' or row[c] == '(X)' or
                        row[c] == 'null'):
                    continue

                # Exclude percentages
                if '.' in row[c]:
                    continue

                # Exclude suffix from median values
                if (row[c][-1] == '-' or row[c][-1] == '+'):
                    new_row[sv] = row[c][:-1]
                else:
                    new_row[sv] = row[c]
            writer.writerow(new_row)


def create_tmcf(output, stat_vars):
    """Writes tMCF to output."""
    with open(output, 'w') as f_out:
        for i in range(len(stat_vars)):
            unit = ''
            if 'Income' in stat_vars[i]:
                unit = _UNIT_TEMPLATE
            f_out.write(
                _TMCF_TEMPLATE.format(index=i, stat_var=stat_vars[i],
                                      unit=unit))


if __name__ == '__main__':
    client = storage.Client()
    f = open(_STAT_VAR_LIST)
    stat_vars = f.read().splitlines()
    f.close()
    create_csv('s2201.csv', stat_vars)
    for blob in client.list_blobs(_BUCKET, prefix=_INPUT):
        s = blob.download_as_string().decode('utf-8')
        reader = csv.DictReader(io.StringIO(s))
        write_csv(blob.name, reader, 's2201.csv', stat_vars)
    create_tmcf('s2201.tmcf', stat_vars)
