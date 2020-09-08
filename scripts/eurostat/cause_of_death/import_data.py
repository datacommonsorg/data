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
"""
Downloads and cleans Cause of Death data from the Eurostat database.
    Template adapted from fpernice-google
    Usage:
    python3 import_data.py
"""
import pandas as pd
import re


def download_data(link):
    return pd.read_table(link, sep='\s*\t\s*')


class EurostatCauseOfDeathImporter:
    DATA_LINK = "https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/BulkDownloadListing?file=data/hlth_cd_acdr2.tsv.gz"
    AGE_MAPPING = {
        'TOTAL': 'Total',
        'Y_LT1': 'Less than 1 year',
        'Y1-4': 'From 1 to 4 years',
        'Y5-9': 'From 5 to 9 years',
        'Y10-14': 'From 10 to 14 years',
        'Y_LT15': 'Less than 15 years',
        'Y15-19': 'From 15 to 19 years',
        'Y15-24': 'From 15 to 24 years',
        'Y20-24': 'From 20 to 24 years',
        'Y_LT25': 'Less than 25 years',
        'Y25-29': 'From 25 to 29 years',
        'Y30-34': 'From 30 to 34 years',
        'Y35-39': 'From 35 to 39 years',
        'Y40-44': 'From 40 to 44 years',
        'Y45-49': 'From 45 to 49 years',
        'Y50-54': 'From 50 to 54 years',
        'Y55-59': 'From 55 to 59 years',
        'Y60-64': 'From 60 to 64 years',
        'Y_LT65': 'Less than 65 years',
        'Y65-69': 'From 65 to 69 years',
        'Y_GE65': '65 years or over',
        'Y70-74': 'From 70 to 74 years',
        'Y75-79': 'From 75 to 79 years',
        'Y80-84': 'From 80 to 84 years',
        'Y85-89': 'From 85 to 89 years',
        'Y_GE85': '85 years or over',
        'Y90-94': 'From 90 to 94 years',
        'Y_GE95': '95 years or over'
    }
    ICD10_NAME = 'bq_icd10.csv'  # this is the csv downloaded from BQ: SELECT DISTINCT id, type, name FROM
    # `google.com:datcom-store-dev.dc_v3_dev.Instance` WHERE id LIKE '%ICD10%'
    GENDER_DICT = {'T': 'Total', 'M': 'Male', 'F': 'Female'}
    CAUSE_DICT = {
        'A-R_V-Y': ['ICD10/A00-Y89'],
        'A_B': ['ICD10/A00-B99'],
        'A15-A19_B90': ['ICD10/A15-A19', 'ICD10/B90'],
        'B15-B19_B942': ['ICD10/B15-B19', 'ICD10/B94.2'],
        'B180-B182': ['ICD10/B18.0', 'ICD10/B18.1', 'ICD10/B18.2'],
        'B20-B24': ['HumanImmunodeficiencyVirus(Hiv)Disease'],
        'A_B_OTH': ['OtherInfectiousAndParasiticDiseases'],
        'C00-D48': ['ICD10/C00-D48'],
        'C': ['MalignantNeoplasms'],
        'C00-C14': ['ICD10/C00-C14'],
        'C15': ['ICD10/C15'],
        'C16': ['ICD10/C16'],
        'C18-C21': ['MalignantNeoplasmsOfColon_RectumAndAnus'],
        'C22': ['ICD10/C22'],
        'C25': ['ICD10/C25'],
        'C32': ['ICD10/C32'],
        'C33_C34': ['MalignantNeoplasmsOfTrachea_BronchusAndLung'],
        'C43': ['ICD10/C43'],
        'C50': ['ICD10/C50'],
        'C53': ['ICD10/C53'],
        'C54_C55': ['MalignantNeoplasmsOfCorpusUteriAndUterus_PartUnspecified'],
        'C56': ['ICD10/C56'],
        'C61': ['ICD10/C61'],
        'C64': ['ICD10/C64'],
        'C67': ['ICD10/C67'],
        'C70-C72': [
            'MalignantNeoplasmsOfMeninges_BrainAndOtherPartsOfCentralNervousSystem'
        ],
        'C73': ['ICD10/C73'],
        'C81-C86': ['ICD10/C81-C86'],
        'C88_C90_C96': ['ICD10/C88', 'ICD10/C90', 'ICD10/C96'],
        'C91-C95': ['Leukemia'],
        'C_OTH': ['OtherMalignantNeoplasms'],
        'D00-D48': [
            'InSituNeoplasms_BenignNeoplasmsAndNeoplasmsOfUncertainOrUnknownBehavior'
        ],
        'D50-D89': ['ICD10/D50-D89'],
        'E': ['ICD10/E00-E90'],
        'E10-E14': ['DiabetesMellitus'],
        'E_OTH': ['OtherEndocrine_NutritionalAndMetabolicDiseases'],
        'F': ['ICD10/F00-F99'],
        'F01_F03': ['ICD10/F01', 'ICD10/F03'],
        'F10': ['ICD10/F10'],
        'TOXICO': ['DrugDependence_Toxicomania'],
        'F_OTH': ['OtherMentalAndBehaviouralDisorders'],
        'G_H': ['ICD10/G00-H95'],
        'G20': ['ICD10/G20'],
        'G30': ['ICD10/G30'],
        'G_H_OTH': ['OtherDiseasesOfTheNervousSystemAndTheSenseOrgans'],
        'I': ['ICD10/I00-I99'],
        'I20-I25': ['ICD10/I20-I25'],
        'I21_I22': ['ICD10/I21', 'ICD10/I22'],
        'I20_I23-I25': ['ICD10/I20', 'ICD10/I23-I25'],
        'I30-I51': ['ICD10/I30-I51'],
        'I60-I69': ['ICD10/I60-I69'],
        'I_OTH': ['OtherDiseasesOfTheCirculatorySystem'],
        'J': ['ICD10/J00-J99'],
        'J09-J11': ['ICD10/J09-J11'],
        'J12-J18': ['Pneumonia'],
        'J40-J47': ['ICD10/J40-J47'],
        'J45_J46': ['Asthma'],
        'J40-J44_J47': ['ICD10/J40-J44', 'ICD10/J47'],
        'J_OTH': ['OtherDiseasesOfTheRespiratorySystem'],
        'K': ['ICD10/K00-K93'],
        'K25-K28': ['PepticUlcer'],
        'K70_K73_K74': ['ChronicLiverDiseaseAndCirrhosis'],
        'K72-K75': ['ICD10/K72-K75'],
        'K_OTH': ['OtherDiseasesOfTheDigestiveSystem'],
        'L': ['ICD10/L00-L99'],
        'M': ['ICD10/M00-M99'],
        'RHEUM_ARTHRO': ['ICD10/M05-M06', 'ICD10/M15-M19'],
        'M_OTH': ['OtherDiseasesOfTheMusculoskeletalSystemAndConnectiveTissue'],
        'N': ['ICD10/N00-N99'],
        'N00-N29': ['ICD10/N00-N29'],
        'N_OTH': ['OtherDiseasesOfTheGenitourinarySystem'],
        'O': ['ICD10/O00-O99'],
        'P': ['ICD10/P00-P96'],
        'Q': ['ICD10/Q00-Q99'],
        'R': ['ICD10/R00-R99'],
        'R95': ['ICD10/R95'],
        'R96-R99': ['ICD10/R96-R99'],
        'R_OTH': [
            'OtherSymptoms_SignsAndAbnormalClinicalAndLaboratoryFindings'
        ],
        'V01-Y89': ['ICD10/V01-Y89'],
        'ACC': ['Accidents(UnintentionalInjuries)'],
        'V_Y85': ['TransportAccidents'],
        'ACC_OTH': ['Eurostat_OtherAccidents'],
        'W00-W19': ['ICD10/W00-W19'],
        'W65-W74': ['ICD10/W65-W74'],
        'X60-X84_Y870': ['IntentionalSelf-Harm(Suicide)'],
        'X40-X49': ['AccidentalPoisoningAndExposureToNoxiousSubstances'],
        'X85-Y09_Y871': ['Assault(Homicide)'],
        'Y10-Y34_Y872': ['Eurostat_EventOfUndeterminedIntent'],
        'V01-Y89_OTH': ['OtherExternalCausesOfMorbidityAndMortality']
    }
    CAUSE_MCF_NAME = 'causes.mcf'
    STAT_VAR_NAME = 'hlth_cd_acdr2_statvar.mcf'
    FINAL_CSV_NAME = 'hlth_cd_acdr2_final.csv'
    TEMPLATE_MCF_NAME = 'hlth_cd_acdr2.tmcf'

    def __init__(self):
        self.raw_df = None
        self.preprocessed_df = None
        self.clean_df = None
        self.stat_vars = None
        self.cause_id_name_dict = self.read_dict_from_mcf(self.CAUSE_MCF_NAME)
        self.icd10_dict = {}
        icd10 = pd.read_csv(self.ICD10_NAME)
        icd10_ids = list(icd10['id'])
        icd10_description = list(icd10['name'])
        for i in range(len(icd10_ids)):
            self.icd10_dict[icd10_ids[i]] = icd10_description[i]

    @staticmethod
    def read_dict_from_mcf(filename):
        """Read in a MCF file as dictionary with key being dcid and value being name"""
        with open(filename, 'r') as f:
            s = f.read()
        id_list = re.findall(r'dcid:(.*)', s)
        name_list = re.findall(r'name: "(.*)"', s)
        assert len(id_list) == len(name_list)
        d = {}
        for i in range(len(id_list)):
            d[id_list[i]] = name_list[i]
        return d

    @staticmethod
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

    def generate_stat_var(self):
        if self.stat_vars is None:
            raise ValueError("Uninitialized value of stat_vars. "
                             "Please check you are calling clean_data "
                             "before generate_stat_var.")
        base_template = ('Node: dcid:{0}\n'
                         'typeOf: dcs:StatisticalVariable\n'
                         'populationType: schema:MortalityEvent\n'
                         'measuredProperty: dcs:count\n'
                         'statType: dcs:measuredValue\n'
                         'measurementDenominator: dcs:Count_Person\n')
        optional_template = [
            'age: {0}\n', 'causeOfDeath: dcs:{0}\n', 'sex: schema:{0}\n'
        ]
        with open(self.STAT_VAR_NAME, 'w') as f:
            for i in range(len(self.stat_vars)):
                combined_stat_var = self.stat_vars[i][0]
                fields = self.stat_vars[i][1:]
                out = base_template.format(combined_stat_var)
                for j in range(3):
                    field = fields[j]
                    if field != '':
                        out += optional_template[j].format(field)
                out += '\n'
                f.write(out)

    def generate_tmcf(self):
        if self.clean_df is None:
            raise ValueError("Uninitialized value of clean_df. "
                             "Please check you are calling clean_df "
                             "before generate_tmcf.")
        """Generate the template mcf."""
        tmcf_template = ('Node: E:causedeath->E{0}\n'
                         'typeOf: dcs:StatVarObservation\n'
                         'variableMeasured: dcs:{1}\n'
                         'observationAbout: C:causedeath->geo\n'
                         'observationDate: C:causedeath->time\n'
                         'measurementMethod: dcs:EurostatRegionalStatistics\n'
                         'value: C:causedeath->{1}\n\n')
        columns = self.clean_df.columns[2:]
        with open(self.TEMPLATE_MCF_NAME, 'w') as f_out:
            for i in range(len(columns)):
                f_out.write(tmcf_template.format(i, columns[i]))

    def translate_column(self, column):
        column_list = column.split('|')[1:]  # remove unit RT here
        gender, age, cause = column_list

        # get the stat var
        age = self.AGE_MAPPING[age]
        age_stat_var = age.title().replace(' ', '').replace('Total', '')
        if age_stat_var != '':
            age_field = self.convert_range(age)
        else:
            age_field = ''
        gender = self.GENDER_DICT[gender]
        gender_stat_var = gender.replace('Total', '')
        gender_field = gender_stat_var
        cause_list = self.CAUSE_DICT[cause]
        cause_stat_var = ''
        cause_field = ''
        for c in cause_list:
            if c in self.icd10_dict.keys():
                cause_stat_var = self.icd10_dict[c].title().replace(
                    ' ', '').replace(',', '_') + '_'
            elif c in self.cause_id_name_dict:
                cause_stat_var += self.cause_id_name_dict[c] + '_'
            else:
                cause_stat_var += c + '_'
            cause_field += c + '&'
        cause_stat_var = cause_stat_var[:-1]
        cause_field = cause_field[:-1]
        if cause == 'C88_C90_C96':
            cause_stat_var = 'Other malignant neoplasm of lymphoid, haematopoietic and related tissue'.title(
            ).replace(' ', '').replace(',', '_')
        combined_stat_var = ''
        for stat_var in [age_stat_var, cause_stat_var, gender_stat_var]:
            if stat_var == '':
                continue
            else:
                combined_stat_var += stat_var + '_'
        if combined_stat_var != '':
            combined_stat_var = combined_stat_var[:-1]
        return [combined_stat_var, age_field, cause_field, gender_field]

    def download_data(self):
        """Downloads raw data from Eurostat website and stores it in instance
        data frame.
        """
        self.raw_df = pd.read_table(self.DATA_LINK)

    def preprocess_data(self):
        """Preprocesses instance raw_df and puts it into long format."""
        if self.raw_df is None:
            raise ValueError("Uninitialized value of raw data frame. Please "
                             "check you are calling download_data before "
                             "preprocess_data.")
        assert len(
            self.raw_df.columns) > 1, "Data must have at least two columns."
        assert self.raw_df.columns.values[0].endswith(
            '\\time'), "Expected the first column header to end with '\\time'."

        # Convert from one-year per column (wide format) to one row per
        # data point (long format).
        self.preprocessed_df = self.raw_df.melt(
            id_vars=[self.raw_df.columns[0]])
        # Rename the variable column.
        self.preprocessed_df.columns.values[1] = 'time'

        # Split the index column into two.
        # Ex: 'unit,sex,age,geo\time' -> 'unit,sex,age' and 'geo'.
        # '\time' labels the other columns so it is confusing.
        # Replace value column with extra space.
        self.preprocessed_df.value = self.preprocessed_df.value.str.replace(
            "([0-9:])$", lambda m: m.group(0) + ' ')
        statistical_variable = None
        # In case this returns only one element in the list.
        first_column_list = self.preprocessed_df.columns[0].rsplit(sep=",",
                                                                   maxsplit=1)
        if len(first_column_list) == 2:
            statistical_variable, geo = first_column_list
        else:
            geo = first_column_list[0]
        geo = geo.replace(r'\time', '')
        assert geo == "geo", "Expected the column header to end with 'geo'."

        if statistical_variable:
            split_df = self.preprocessed_df[
                self.preprocessed_df.columns[0]].str.rsplit(",",
                                                            n=1,
                                                            expand=True)
            self.preprocessed_df['statistical_variable'] = split_df[0]
            self.preprocessed_df['geo'] = split_df[1]
            self.preprocessed_df.drop(columns=[self.preprocessed_df.columns[0]],
                                      inplace=True)

        self.preprocessed_df = (self.preprocessed_df.set_index([
            "geo", "time"
        ]).pivot(
            columns="statistical_variable")['value'].reset_index().rename_axis(
            None, axis=1))
        # Fill missing 'geo' values with a colon.
        self.preprocessed_df.fillna(': ', inplace=True)

        # Split notes out of values.
        # Ex: "5598920 b" -> "5598920", "b".
        # Ex: "5665118" -> "5665118", ""
        # Ex: ": c" -> "", "c"
        # Append extra space for all values that do not come with a note.
        self.preprocessed_df[
            self.preprocessed_df.columns[2:]] = self.preprocessed_df[
                self.preprocessed_df.columns[2:]].replace(
                    "([0-9:])$", lambda m: m.group(0) + ' ')
        # replace comma in column names with a vertical bar so that we can save it in csv later
        new_column_names = []
        for column_name in self.preprocessed_df.columns:
            new_column_names.append(column_name.replace(',', '|'))
        self.preprocessed_df.columns = new_column_names
        for column_name in self.preprocessed_df.columns[2:]:
            self.preprocessed_df['{0}'.format(
                column_name)], self.preprocessed_df['{0}|notes'.format(
                    column_name)] = (zip(*self.preprocessed_df[column_name].
                                         apply(lambda x: x.split(' '))))

    def clean_data(self):
        """Drops unnecessary columns that are not needed for data import and reformat column names."""
        if self.preprocessed_df is None:
            raise ValueError("Uninitialized value of processed data frame. "
                             "Please check you are calling preprocess_data "
                             "before clean_data.")
        # drop unused columns
        self.clean_df = self.preprocessed_df[self.preprocessed_df.columns[:len(
            self.preprocessed_df.columns
        ) // 2 + 1]]  # number of columns should be 2 + 2X, we want the first 2 + X
        # columns
        # replace colon with NaN in order to convert to float64
        self.clean_df = self.clean_df.replace(':', '')
        self.clean_df.to_csv(self.FINAL_CSV_NAME, index=False)
        self.clean_df = pd.read_csv(self.FINAL_CSV_NAME)
        self.clean_df[self.clean_df.columns[2:]] = self.clean_df[
            self.clean_df.columns[2:]].astype('float64') / 1000
        # the below takes much longer than the above
        # self.clean_df = self.clean_df.replace(':', 'NaN')
        # # apply scaling factor of 1000
        # self.clean_df[self.clean_df.columns[2:]] = self.clean_df[self.clean_df.columns[2:]].astype('float64') / 1000

        self.clean_df['geo'] = 'dcid:nuts/' + self.clean_df['geo']
        stat_vars = []
        new_column_names = ['geo', 'time']
        for column in self.clean_df.columns[2:]:  # ignore geo and time
            stat_vars.append(self.translate_column(column))
            if stat_vars[-1][0] != '':
                stat_vars[-1][0] = 'Count_Death_' + stat_vars[-1][
                    0] + '_AsFractionOf_Count_Person'
            else:
                stat_vars[-1][0] = 'Count_Death_AsFractionOf_Count_Person'
            new_column_names.append(stat_vars[-1][0])
        self.clean_df.columns = new_column_names
        self.clean_df.to_csv(self.FINAL_CSV_NAME, index=False)
        self.stat_vars = stat_vars


if __name__ == "__main__":
    imp = EurostatCauseOfDeathImporter()
    imp.download_data()
    imp.preprocess_data()
    imp.clean_data()
    imp.generate_stat_var()
    imp.generate_tmcf()
