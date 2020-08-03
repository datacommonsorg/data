"""Combines the raw data from fda into one dataFrame and writes it to CleanData.csv.

The columns used in write_mcf from the resultong dataFrame are:
ApplNo - FDA Application number
ProductNo - FDA Application product number
Strength - amount of active ingredients in drug
DosageForm - type of disage form ie tablet, injectale etc
AdminRoute - how the drug is taken ie oral, topical etc
ReferenceStandard - isReferenceStandard property of Drug
ReferenceDrug - isAvailableGenerically property of Drug
TECodeMCF - mcf of te code enum property of DrugStrength
MarketStatMCF - mcf of marketing status enum property of DrugStrength
FinalVolMCF - mcf of finalReconstitutedSolutionVolume DrugStrength property
DrugCourseMCF - mcf of drugCourse DrugStrength property
DoseTypeMCF - mcf of singleDose DrugStrength boolean property
AdditionalInfoMCF - mcf of additionalInformation Drug property
"""
import re
import pandas as pd

from create_enums import generate_enums


def add_to_dict(dictionary, key, value):
    """Adds key value pair to dicitoary in form of a list
    """
    if not value or pd.isnull(value):
        print("Null value added to dict, key: " + key)
    if key in dictionary:
        if value not in dictionary[key]:
            dictionary[key].append(value)
    else:
        dictionary[key] = [value]


# FUNCTIONS: formatting quantities and quantity ranges
def get_quant_format(strength):
    """Returns a quantity format [# UNIT] of a given strength
    """
    strength = strength.strip()
    if strength == 'N/A':
        return '"N/A"'
    if 'N/A' in strength:
        #print(strength)
        return '"' + strength + '"'
    split_list = list(filter(None, re.split(r'(\d*[.,]?\d+)', strength)))
    if len(split_list) < 2:
        return '"' + strength + '"'
    return '[' + split_list[0] + ' ' + "".join(split_list[1:]).strip().replace(
        ' ', '_') + ']'


# FUNCTIONS: data reading functions for TECodes and Marketing Status IDs, cleaning Form
def populate_dicts_from_te_df(market_stat_dict, te_code_dict, row):
    """Given a row of a dataframe created from TE.txt, populate dictionaries
    that map the ApplNo_ProductNo key of the drug to a TE Code and Marketing
    Status.
    """

    key = str(row['ApplNo']) + '_' + str(row['ProductNo'])
    te_code = row['TECode']
    market_stat_id = row['MarketingStatusID']

    if market_stat_id:
        add_to_dict(market_stat_dict, key, market_stat_id)

    if te_code and te_code != "TBD":
        add_to_dict(te_code_dict, key, te_code)


def populate_dict_from_ms_df(market_stat_dict, row):
    """Given a row of a dataframe created from MarketingStatus.txt, populate
    dictionaries that map the ApplNo_ProductNo key of the drug to a Marketing
    Status.
    """
    key = str(row['ApplNo']) + '_' + str(row['ProductNo'])
    market_stat_id = row['MarketingStatusID']
    if market_stat_id:
        add_to_dict(market_stat_dict, key, market_stat_id)


def get_te_code_mcf(appl_prod_key_to_te_code, te_code_to_dcid,
                    appl_prod_num_key):
    """Returns the te code DrugStrength property mcf of drug based on its
    applNo_ProductNo key.

    The ApplNo_ProductNo key must first be mapped to the drug's TE code, then
    the TE code must be mapped to the associated enum dcid.
    """

    te_code_mcf = ''
    if appl_prod_num_key in appl_prod_key_to_te_code:
        te_codes = appl_prod_key_to_te_code[appl_prod_num_key]
        for code in te_codes:
            te_code_enum = te_code_to_dcid[code]
            te_code_mcf = te_code_mcf + 'therapeuticEquivalenceCode: dcid:' + te_code_enum + '\n'
    return te_code_mcf


def get_market_stat_mcf(appl_prod_key_to_market_stat, market_stat_to_dcid,
                        appl_prod_num_key):
    """Returns the marketing status DrugStrength property mcf of drug based on its
    applNo_ProductNo key.

    The ApplNo_ProductNo key must first be mapped to the drug's TE code, then
    the TE code must be mapped to the associated enum dcid.
    """
    market_stat_mcf = ''
    if appl_prod_num_key in appl_prod_key_to_market_stat:
        market_stat_ids = appl_prod_key_to_market_stat[appl_prod_num_key]
        for market_stat_id in market_stat_ids:
            market_stat_enum = market_stat_to_dcid[str(market_stat_id)]
            market_stat_mcf = market_stat_mcf + 'marketingStatus: dcid:' + market_stat_enum + '\n'
    return market_stat_mcf


def create_te_code_market_stat_columns(appl_prod_key_to_market_stat,
                                       market_stat_to_dcid,
                                       appl_prod_key_to_te_code,
                                       te_code_to_dcid, row):
    """Given a row, the TECodeMCF and MarketStatMCF columns are appended and
    filled in by calling previously defined helper functions
    """
    appl_prod_num_key = str(row['ApplNo']) + '_' + str(row['ProductNo'])
    row['TECodeMCF'] = get_te_code_mcf(appl_prod_key_to_te_code,
                                       te_code_to_dcid, appl_prod_num_key)
    row['MarketStatMCF'] = get_market_stat_mcf(appl_prod_key_to_market_stat,
                                               market_stat_to_dcid,
                                               appl_prod_num_key)
    return row


# Functions: cleaning Strengths and Ingredients


def replace_strength_patterns(strengths):
    """Replaces problematic patterns in the Strength column of Products.txt to
    make data importing more universal and less case by case basis.
    """
    if strengths:
        strengths = strengths.replace('EQ ', '')
        strengths = strengths.replace('(BASE)', 'BASE')
        strengths = strengths.replace('(U-100)', '')
        strengths = strengths.replace('(U-200)', '')
        strengths = strengths.replace('*', '')
        strengths = strengths.replace('UNKNOWN', '')
        strengths = strengths.replace('and', ';')
        strengths = strengths.replace('0.03MG,0.3MG;0.75MG',
                                      '0.03MG; 0.3MG;0.75MG')
        strengths = strengths.replace('300MG BASE,1MG,0.5MG; 300MG BASE',
                                      '300MG BASE;1MG;0.5MG')
        strengths = strengths.replace('N/A;N/A	N/A;N/A;N/A',
                                      'N/A;N/A;N/A;N/A;N/A')
        strengths = strengths.replace(
            '2.5MG/O.5ML',
            '2.5MG/0.5ML')  # yes, the FDA put an O instead of 0 :(
        strengths = strengths.strip()
    return strengths


def replace_ingredient_patterns(ingreds):
    """Replaces problematic patterns in the ActiveIngredients column of
    Products.txt to make data importing more universal and less case by case
    basis.
    """
    if ingreds:
        ingreds = ingreds.strip()
        ingreds = ingreds.replace('IRBESARTAN:', 'IRBESARTAN;')
        ingreds = ingreds.replace('LIOTRIX (T4;T3)', 'LIOTRIX (T4,T3)')
        ingreds = ingreds.replace('MENOTROPINS (FSH;LSH)',
                                  'MENOTROPINS (FSH,LH)')
        ingreds = ingreds.replace(
            'TRIPLE SULFA (SULFABENZAMIDE;SULFACETAMIDE;SULFATHIAZOLE',
            'SULFABENZAMIDE;SULFACETAMIDE;SULFATHIAZOLE (TRIPLE SULFA)')
        ingreds = ingreds.replace('PANCRELIPASE (AMYLASE;LIPASE;PROTEASE)',
                                  'AMYLASE;LIPASE;PROTEASE (PANCRELIPASE)')
        ingreds = ingreds.replace('LAMIVUDINE, NEVIRAPINE, AND STAVUDINE',
                                  'LAMIVUDINE; NEVIRAPINE; STAVUDINE')
        ingreds = ingreds.replace(
            'ELAGOLIX SODIUM,ESTRADIOL,NORETHINDRONE ACETATE; ELAGOLIX SODIUM',
            'ELAGOLIX SODIUM;ESTRADIOL;NORETHINDRONE ACETATE')
        ingreds = ingreds.replace(
            'TRISULFAPYRIMIDINES (SULFADIAZINE;SULFAMERAZINE;SULFAMETHAZINE)',
            'SULFADIAZINE;SULFAMERAZINE;SULFAMETHAZINE')
        ingreds = ingreds.strip()
    return ingreds


def reformat_paren_with_semi(strength):
    """Reformats cases described below so that the strength format fits the
    pattern that is searched for in the strength parsing done in write_mcf.py
    """
    # case: 700 UNITS/10ML; 300 UNITS/10ML (70 UNITS/ML; 30 UNITS/ML)
    # -->700 UNITS/10ML (70 UNITS/ML) 70 UNITS/ML; 300 UNITS/10ML (30 UNITS/ML)

    paren_strength = re.findall(r'(?<=\().*?(?=\))', strength)
    strengths_no_paren = re.sub(r'[\(].*?[\)]', '', strength)
    paren_split = paren_strength[0].split(';')
    not_in_paren_split = strengths_no_paren.split(';')

    if len(paren_split) != len(not_in_paren_split):
        print('Error in reformat_paren_with_semi: ' + strength)
    else:
        for index, stren in enumerate(not_in_paren_split):
            not_in_paren_split[index] = stren.strip(
            ) + '(' + paren_split[index].strip() + ')'
    return ';'.join(not_in_paren_split)


def reformat_parens(strengths):
    """Finds cases where there is a semi colon between parentheses in the
    strength and calls helper function to fix the format.
    """
    # case: 700 UNITS/10ML; 300 UNITS/10ML (70 UNITS/ML; 30 UNITS/ML)
    paren = re.findall(r'[\(].*?[\)]', strengths)
    if paren:
        for found in paren:
            if ';' in found:
                strengths = reformat_paren_with_semi(strengths)
    strengths = strengths.strip()
    return strengths


def remove_comma_from_nums(strengths):
    """Removes comma from strength if the comma is between two digits
    """
    if ',' in strengths:
        strengths = re.sub(r'(\d),(\d)', r'\1\2', strengths)

    strengths = strengths.strip()
    return strengths


# FUNCTIONS: get properties into mcf for new columns


def get_drug_course_mcf(drug_admin_routes):
    """Searches the AdminRoute column of dataframe for drug course information

    If drug course is found, the course is removed from the AdminRoute column
    and the mcf property is written to the drugCourseMCF column
    """
    oral_drug_course = ['ORAL-28', 'ORAL-21', 'ORAL-20']
    drug_course_mcf = ''

    if not drug_admin_routes:
        return drug_course_mcf, drug_admin_routes

    for course in oral_drug_course:
        if course in drug_admin_routes:
            drug_admin_routes = drug_admin_routes.replace(course, 'ORAL')
            num_days = course.strip().split('-')[1]
            drug_course_mcf = 'drugCourse: [' + num_days + ' Days]\n'

    return drug_course_mcf, drug_admin_routes


def get_dose_type_mcf(drug_admin_routes):
    """Searches the AdminRoute column of dataframe for dose type information

    If doseType is found, the course is removed from the AdminRoute column
    and the mcf property is written to the doseTypeMCF column
    """

    dose_types = ['SINGLE-DOSE', 'SINGLE-USE', 'MULTIDOSE']
    dose_type_mcf = ''

    if not drug_admin_routes:
        return dose_type_mcf, drug_admin_routes

    for dose in dose_types:
        if dose in drug_admin_routes:
            drug_admin_routes = drug_admin_routes.replace(dose, '')
            if dose == 'MULTIDOSE':
                dose_type_mcf = 'singleDose: False\n'
            else:
                dose_type_mcf = 'singleDose: True\n'
    return dose_type_mcf, drug_admin_routes


def get_additional_info_mcf(strengths):
    """Searches the Strength column of dataframe for drug additional info

    If additionalInfo (characterized by two preceding asterisks in Products.txt)
    is found, the additionalInfo tag is removed from the strength column and
    the mcf property is written to the AdditionalInfoMCF column
    """

    asterisk_tags = [
        'See current Annual Edition, 1.8 Description of Special Situations, Levothyroxine Sodium',
        'Indicated for use and comarketed with Interferon ALFA-2B, Recombinant (INTRON A), as Rebetron Combination Therapy',
        'Federal Register determination that product was not discontinued or withdrawn for safety or efficacy reasons',
        'Federal Register determination that product was not withdrawn or discontinued for safety or efficacy reasons',
        'Federal Register determination that product was discontinued or withdrawn for safety or efficacy reasons',
        'Federal Register determination that product was discontinued or withdrawn for s or e reasons',
        'Federal Register determination that product was not discontinued or withdrawn for s or e reasons'
    ]

    additional_info_mcf = ''

    if strengths:
        additional_info = ''
        for tag in asterisk_tags:
            if tag in strengths:
                additional_info = additional_info + tag + '. '
                strengths = strengths.replace(tag, '')
                #print(tag)

        if additional_info:
            additional_info_mcf = 'additionalDrugInformation: "' + additional_info + '"\n'

    return additional_info_mcf, strengths


def get_final_vol_mcf(strengths):
    """Searches the Strength column of dataframe for final volume information

    If final volume (characterized by strength ending in '(# ML)') is found,
    the final volume is removed from the strength column and the mcf property
    is written to the FinalVolMCF column.
    """
    final_vol_mcf = ''

    if re.match(r"(.*)?\(\d*[.,]?\d+(\s+)?ML\)$", strengths):
        paren = re.findall(r"[\(].*?[\)]", strengths)
        final_vol_quant = get_quant_format(paren[0].strip('()'))
        strengths = re.sub(r"[\(].*?[\)]", '', strengths).strip()
        final_vol_mcf = 'finalReconstitutedSolutionVolume: ' + final_vol_quant + '\n'
    return final_vol_mcf, strengths


# FUNCTIONS: given a row, clean by column


def clean_form(form):
    """Replaces problematic strings from the original Form column in
    Products.txt with strings that can be split according to the
    <DosageForm>;<AdminRoute> format that most of the Form column follows.
    """
    unusual_forms = {
        'SOLUTION; ORAL AND TABLET; DELAYED RELEASE':
            'SOLUTION, TABLET, DELAYED RELEASE; ORAL',
        'CAPSULE; CAPSULE, DELAYED REL PELLETS; TABLET;ORAL':
            'CAPSULE, CAPSULE, DELAYED REL PELLETS, TABLET; ORAL',
        'POWDER, FOR INJECTION SOLUTION, LYOPHILIZED POWDER':
            'INJECTION, POWDER, LYOPHILIZED, FOR SOLUTION; INJECTION',
        'POWDER FOR ORAL SOLUTION':
            'POWDER, FOR SOLUTION; ORAL',
        'UNKNOWN':
            None
    }
    form = str(form)

    if form in unusual_forms:
        form = unusual_forms.get(form)
    return form


def clean_strength(row):
    """Applies previously defined helper functions to clean the strength column
    """

    if not row['Strength']:
        row['Strength'] = ''
        row['AdditionalInfoMCF'] = ''
        row['FinalVolMCF'] = ''
        return row

    row['AdditionalInfoMCF'], row['Strength'] = get_additional_info_mcf(
        row['Strength'])
    row['FinalVolMCF'], row['Strength'] = get_final_vol_mcf(row['Strength'])

    row['Strength'] = replace_strength_patterns(row['Strength'])
    row['Strength'] = reformat_parens(row['Strength'])
    row['Strength'] = remove_comma_from_nums(row['Strength'])
    return row


def clean_active_ingredient(row):
    """Applies previously defined helper functions to clean the ActiveIngredient
    column.
    """
    if not row['ActiveIngredient']:
        return row

    row['ActiveIngredient'] = replace_ingredient_patterns(
        row['ActiveIngredient'])
    return row


def clean_admin_route(row):
    """Applies previously defined helper functions to clean the AdminRoute
    column.
    """
    if not row['AdminRoute']:
        row['AdminRoute'] = ''
        row['DrugCourseMCF'] = ''
        row['DoseTypeMCF'] = ''
        return row

    row['DrugCourseMCF'], row['AdminRoute'] = get_drug_course_mcf(
        row['AdminRoute'])
    row['DoseTypeMCF'], row['AdminRoute'] = get_dose_type_mcf(row['AdminRoute'])
    return row


def clean_dataframe(row):
    """Cleans a row of the dataframe by the column.
    """
    row = clean_strength(row)
    row = clean_active_ingredient(row)
    row = clean_admin_route(row)
    return row


def load_data(products_file_name, applications_file_name, te_file_name,
              market_stat_file_name, clean_products_out):
    """Read in raw data to create a raw dataframe and dicitonaries.

    Merges the info from Applications.txt and Products.txt into one dataframe.
    Creates the applNo_ProductNo drug key to TE code and Marketing Status enum
    dcid dictionaries.
    """
    dosage_form_to_dcid, admin_route_to_dcid, appl_type_to_dcid, te_code_to_dcid, market_stat_to_dcid = generate_enums(
        False)

    #Products.txt has extra tabs at the end of some lines, this ensures that all
    #lines end without extra trailing tabs and with a newline char
    with open(products_file_name, 'r') as products_file:
        lines = [line.strip() + '\n' for line in products_file]

    with open(clean_products_out, 'w') as products_file:
        products_file.writelines(lines)

    # merge the columns from Applications.txt and Products.txt
    products_df = pd.read_csv(clean_products_out, sep='\t')
    products_df = products_df.fillna('')
    applications_df = pd.read_csv(applications_file_name, sep='\t')
    applications_df = applications_df.fillna('')
    drugs_df = pd.merge(left=products_df,
                        right=applications_df,
                        how='left',
                        left_on=['ApplNo'],
                        right_on=['ApplNo'],
                        indicator=True)

    appl_prod_num_to_market_stat = {}
    appl_prod_num_to_te_code = {}

    # read and save te_codes and MarketingStatus IDs from TECodes.txt into dictionary
    te_df = pd.read_csv(te_file_name, sep='\t')
    te_df = te_df.fillna('')
    te_df.apply(lambda x: populate_dicts_from_te_df(
        appl_prod_num_to_market_stat, appl_prod_num_to_te_code, x),
                axis=1)

    # read and save Marketing Status IDs from MarketingStatus.txt into dictionary
    marketing_status_df = pd.read_csv(market_stat_file_name, sep='\t')
    marketing_status_df = marketing_status_df.fillna('')
    marketing_status_df.apply(
        lambda x: populate_dict_from_ms_df(appl_prod_num_to_market_stat, x),
        axis=1)

    # create TECodeMCF and MarketStatMCF columns in dataframe based on the applNo/ProductNo key and preivously created dictionaries
    drugs_df = drugs_df.apply(lambda x: create_te_code_market_stat_columns(
        appl_prod_num_to_market_stat, market_stat_to_dcid,
        appl_prod_num_to_te_code, te_code_to_dcid, x),
                              axis=1)

    drugs_df = drugs_df.fillna('')
    return drugs_df


def write_clean_data(products_file_name, applications_file_name, te_file_name,
                     market_stat_file_name, clean_products_out, clean_data_out):
    """Calls the load raw data helper function, then cleans the resulting
    dataframe while using the loaded dicitoanries to append MCF columns used
    in write_mcf.py .
    Writes the cleaned dataframe to the specified location.
    """
    drugs_clean_df = load_data(products_file_name, applications_file_name,
                               te_file_name, market_stat_file_name,
                               clean_products_out).copy()

    # split Form column into dosageForm and adminRoute
    drugs_clean_df["CleanedForm"] = drugs_clean_df["Form"].map(
        lambda val: clean_form(val))
    split_form = drugs_clean_df["CleanedForm"].str.split(";", expand=True)
    drugs_clean_df["DosageForm"] = split_form[0]
    drugs_clean_df["AdminRoute"] = split_form[1]

    # clean by specific column
    drugs_clean_df = drugs_clean_df.apply(clean_dataframe, axis=1)
    #drugs_clean_df = drugs_clean_df.apply(clean_active_ingredient, axis=1)
    #drugs_clean_df = drugs_clean_df.apply(clean_admin_route, axis=1)

    drugs_clean_df = drugs_clean_df.fillna('')

    drugs_clean_df.to_csv(clean_data_out, index=False)


def main():
    """Calls write_clean_data with the files from raw_data/ and writes
    the clean data to ./CleanData.csv
    """
    products_file_name = 'raw_data/Products.txt'
    applications_file_name = 'raw_data/Applications.txt'
    te_file_name = 'raw_data/TE.txt'
    market_stat_file_name = 'raw_data/MarketingStatus.txt'

    clean_products_out = 'CleanProducts.txt'
    clean_data_out = 'CleanData.csv'

    write_clean_data(products_file_name, applications_file_name, te_file_name,
                     market_stat_file_name, clean_products_out, clean_data_out)


if __name__ == "__main__":
    main()
