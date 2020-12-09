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
"""Combines and cleans the raw data from fda into one dataFrame.

The columns used to write an mcf file from the resulting dataFrame are:
ApplNo - FDA Application number
ProductNo - FDA Application product number
CleanStrength - amount of active ingredients in drug
DosageFormEnums - type of disage form ie tablet, injectale etc
AdminRouteEnums - how the drug is taken ie oral, topical etc
ReferenceStandard - isReferenceStandard property of Drug
ReferenceDrug - isAvailableGenerically property of Drug
TECodes - te code enums property of DrugStrength
MarketStatus - marketing status enums property of DrugStrength
FinalVolQty - quantity formatted final volume for DrugStrength property
DrugCourse - quantity formatted drug course for DrugStrength property
SingleDose - boolean fomatted as string for DrugStrength property
AdditionalInfo - string for additionalInformation Drug property
DrugRef - either the ChEMBL id for the drug or sanitized verison of DrugName
"""
import re
import json
from os import path
from collections import defaultdict
import pandas as pd
from func_timeout import func_timeout
from chembl_webresource_client.new_client import new_client

from utils.format import get_qty_format
from utils.config import APPLICATION_TYPE_ENUMS, TE_CODE_ENUMS, \
MARKETING_STATUS_ENUMS, DOSAGE_FORM_ENUMS, ADMIN_ROUTE_ENUMS, \
ADMIN_ROUTES_W_COMMAS, ADMIN_ROUTE_REPLACEMENTS, DOSAGE_FORM_IN_ADMIN_ROUTE, \
DOSAGE_FORM_REPLACEMENTS, DOSAGE_FORMS_W_4_COMMAS, DOSAGE_FORMS_W_3_COMMAS, \
DOSAGE_FORMS_W_2_COMMAS, DOSAGE_FORMS_W_COMMA, DRUG_REF_REPLACEMENTS, \
ILL_FORMATTED_FORMS, ILL_FORMATTED_STRENGTHS, ILL_FORMATTED_INGREDIENTS, \
ADDITIONAL_INFO_TAGS, DOSE_TYPES, DRUG_COURSES

molecule = new_client.molecule

drug_ref_db = {}

drug_ref_file_name = './drug_refs_updated.json'
if not path.exists(drug_ref_file_name):
    drug_ref_file_name = './utils/drug_refs.json'
    
with open(drug_ref_file_name) as chembl_json:
    drug_ref_db = json.load(chembl_json)


def chembl_from_api(synonym):
    """Synonym must be stripped lower case to match"""
    print(synonym)
    chembl_id = None
    for molec in molecule.search(synonym):
        for molec_synonymyn in molec['molecule_synonyms']:
            if molec_synonymyn['molecule_synonym'].lower() == synonym:
                chembl_id = molec['molecule_chembl_id']
                return chembl_id
    return chembl_id


def create_drug_ref(drug_name):
    """Returns a suitable reference name for a drug when the chembl ID cannot
  be found. This reference name is used in dcids and therefore must not contain
  special characters.
  """
    ref_name = drug_name

    for special_format, replace_format in DRUG_REF_REPLACEMENTS.items():
        ref_name = ref_name.replace(special_format, replace_format).strip()

    ref_name = re.sub("[^0-9a-zA-Z_-]+", "", ref_name).title()

    if len(ref_name) > 136:
        print('WARNING ref_name too long: ' + ref_name)
    return ref_name


def get_drug_ref(drug_name, active_ingred):
    """Returns the drug reference to be used in creating a dcid for the drug."""

    # if drug name does not exist, set drug name to the active ingredient
    if not drug_name:
        drug_name = active_ingred

    # check if drug name is in the /utils/drug_refs.json file, then return the
    # the specified drug reference
    if drug_name in drug_ref_db:
        return drug_ref_db[drug_name]

    # check the /utils/drug_refs.json file for a standardized version of the
    # drug name
    synonym = re.split(r'[^a-zA-Z\s-]',
                       drug_name.lower().replace('.', ''))[0].strip()
    if synonym in drug_ref_db:
        return drug_ref_db[synonym]

    # find chembl id from chembl python api
    try:
        chembl_id = func_timeout(15, chembl_from_api, args=(synonym,))
    except:
        chembl_id = None

    if chembl_id:
        drug_ref_db[synonym] = chembl_id
        return chembl_id

    # create a new drug reference since a pre-existing one could not be found
    ref = create_drug_ref(drug_name)

    # save new drug reference to be written to /utils/drug_refs.json file
    drug_ref_db[drug_name] = ref
    drug_ref_db[synonym] = ref

    return ref


def reformat_paren_with_semi(strength):
    """Reformats cases described below so that the strength format fits the
    pattern that is searched for in the strength parsing done in write_mcf.py
    """
    # case: 700 UNITS/10ML; 300 UNITS/10ML (70 UNITS/ML; 30 UNITS/ML)
    # -->700 UNITS/10ML (70 UNITS/ML); 300 UNITS/10ML (30 UNITS/ML)

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


def populate_dicts_from_te_df(appl_key_to_ms_enum, appl_key_to_te_enum, row):
    """Given a row of a dataframe created from TE.txt, populate dictionaries
    that map the ApplNo_ProductNo key of the drug to a TE Code and Marketing
    Status.
    """

    key = str(row['ApplNo']) + '_' + str(row['ProductNo'])
    te_code = row['TECode']
    market_stat_id = row['MarketingStatusID']

    if market_stat_id:
        appl_key_to_ms_enum[key].add(market_stat_id)

    if te_code and te_code != "TBD":
        appl_key_to_te_enum[key].add(te_code)


def populate_dict_from_ms_df(appl_key_to_ms_enum, row):
    """Given a row of a dataframe created from MarketingStatus.txt, populate
    dictionaries that map the ApplNo_ProductNo key of the drug to a Marketing
    Status.
    """
    key = str(row['ApplNo']) + '_' + str(row['ProductNo'])
    market_stat_id = row['MarketingStatusID']
    if market_stat_id:
        appl_key_to_ms_enum[key].add(market_stat_id)


def create_te_ms_columns(appl_key_to_ms_enum, appl_key_to_te_enum, row):
    """Given a row, the TECodeMCF and MarketStatMCF columns are appended and
    filled in by calling previously defined helper functions
    """
    appl_key = str(row['ApplNo']) + '_' + str(row['ProductNo'])

    ms_enums = ''
    if appl_key in appl_key_to_ms_enum:
        ms_ids = appl_key_to_ms_enum[appl_key]
        for ms_id in list(ms_ids):
            ms_enum = MARKETING_STATUS_ENUMS[str(ms_id)]
            ms_enums += 'dcid:' + ms_enum + ','

    row['MarketStatus'] = ms_enums.strip(',')

    te_enums = ''
    if appl_key in appl_key_to_te_enum:
        te_codes = appl_key_to_te_enum[appl_key]
        for te_code in list(te_codes):
            te_enum = TE_CODE_ENUMS[te_code]
            te_enums += 'dcid:' + te_enum + ','
    row['TECodes'] = te_enums.strip(',')

    return row


def expand_strength(row):
    """Extracts information from Strength column and cleans remaining strengths.

    Gets Additional Info and Final Volume Quantity columns from Strength.
    Reformats any malformed strengths and removes commas from within numbers.
    """
    strengths = row['Strength']

    # search for additional info marked by double asterisks
    if '*' in strengths:
        additional_info = ''
        for tag in ADDITIONAL_INFO_TAGS:
            if tag in strengths:
                additional_info = additional_info + tag + '. '
                strengths = strengths.replace(tag, '')
        row['AdditionalInfo'] = additional_info

    # search for final final Reconstituted Solution Volume quantity
    if re.match(r"(.*)?\(\d*[.,]?\d+(\s+)?ML\)$", strengths):
        paren = re.findall(r"[\(].*?[\)]", strengths)
        strengths = re.sub(r"[\(].*?[\)]", '', strengths).strip()
        row['FinalVolQty'] = get_qty_format(paren[0].strip('()'))

    # replace malformed strings for better formatting
    for bad_format, improved_format in ILL_FORMATTED_STRENGTHS.items():
        strengths = strengths.replace(bad_format, improved_format)

    # determine if there is a semi colon anywhere between two parentheses
    paren = re.findall(r'[\(][^)]*;.*?[\)]', strengths)
    if paren:
        strengths = reformat_paren_with_semi(strengths)

    # remove comma from numbers
    strengths = re.sub(r'(\d),(\d)', r'\1\2', strengths)

    row['CleanStrength'] = strengths.strip()
    return row


def expand_dosage_form(row):
    """Creates DosageFormEnums column from DosageForm by parsing form and using
    dict from utils/config.py.
    """
    dosage_forms = row['DosageForm'].upper().strip()

    # replace malformed strings for better formatting
    for bad_format, improved_format in DOSAGE_FORM_REPLACEMENTS.items():
        dosage_forms = dosage_forms.replace(bad_format, improved_format)

    dosage_forms = dosage_forms.title()
    dosage_enums = ''

    dosgae_form_lists = [
        DOSAGE_FORMS_W_4_COMMAS,
        DOSAGE_FORMS_W_3_COMMAS,
        DOSAGE_FORMS_W_2_COMMAS,
        DOSAGE_FORMS_W_COMMA,
    ]

    # search for the dosage forms containing commas before splitting by comma
    for dosage_form_list in dosgae_form_lists:
        for form_w_comma in dosage_form_list:
            if form_w_comma in dosage_forms:
                dosage_enums += 'dcid:' + DOSAGE_FORM_ENUMS[form_w_comma] + ','
                dosage_forms = dosage_forms.replace(form_w_comma, '').strip()

    # append comma separated dosage forms as enums
    for dosage_form in dosage_forms.split(','):
        dosage_form = dosage_form.strip()
        if not dosage_form:
            continue
        if dosage_form not in DOSAGE_FORM_ENUMS:
            raise KeyError('dosage form enum not found for: ' + dosage_form +
                           '\n' + str(row))
        dosage_enums += 'dcid:' + DOSAGE_FORM_ENUMS[dosage_form] + ','

    row['DosageFormEnums'] = dosage_enums.strip(',')
    return row


def expand_admin_route(row):
    """Extracts columns from AdminRoute column and formats remaining
    administration routes into enums.

    Gets DrugCourse and SingleDose columns from AdminRoute column. Appends
    extra dosage form enums to DosageFormEnums column and creates
    AdminRouteEnums column using an enum dict from utils/config.py.

    """
    admin_routes = row['AdminRoute'].strip()

    # search admin route for drug course
    for course in DRUG_COURSES:
        if course in admin_routes:
            admin_routes = admin_routes.replace(course, 'ORAL')
            num_days = course.strip().split('-')[1]
            row['DrugCourse'] = '[' + num_days + ' Days]'
            break

    # search admin route for a dose type
    for dose in DOSE_TYPES:
        if dose in admin_routes:
            admin_routes = admin_routes.replace(dose, '')
            if dose == 'MULTIDOSE':
                row['SingleDose'] = 'False'
            else:
                row['SingleDose'] = 'True'

    admin_routes = admin_routes.upper()
    admin_enums = ''

    # remove admin routes with commas first so we can split by comma after
    for route_w_comma in ADMIN_ROUTES_W_COMMAS:
        if route_w_comma in admin_routes:
            admin_enums += 'dcid:' + ADMIN_ROUTES_W_COMMAS[route_w_comma] + ','
            admin_routes = admin_routes.replace(route_w_comma, '')

    # replace malformed strings for better formatting
    for short_form, long_form in ADMIN_ROUTE_REPLACEMENTS.items():
        admin_routes = admin_routes.replace(short_form, long_form)

    # append comma separated dosage forms as enums
    for admin_route in admin_routes.split(','):
        admin_route = admin_route.strip()
        if not admin_route:
            continue
        # search for hidden dosage forms
        if admin_route in DOSAGE_FORM_IN_ADMIN_ROUTE:
            row['DosageFormEnums'] += DOSAGE_FORM_IN_ADMIN_ROUTE[admin_route][0]
            admin_enums += DOSAGE_FORM_IN_ADMIN_ROUTE[admin_route][1]
        # append administration route enum
        else:
            admin_route = admin_route.title()
            if admin_route not in ADMIN_ROUTE_ENUMS:
                raise KeyError('admin route enum not found for: ' + str(row))
            admin_enums += 'dcid:' + ADMIN_ROUTE_ENUMS[admin_route] + ','

    row['AdminRouteEnums'] = admin_enums.strip(',')
    row['DosageFormEnums'] = row['DosageFormEnums'].strip(',')

    return row


def expand_df(appl_key_to_ms_enum, appl_key_to_te_enum, row):
    """Expands the DataFrame created by combining Applications.txt and
    Products.txt.

    Takes in dictionaries containing in Marketing Status information and
    Therapeutic Equivalence information to append their data to the DataFrame.
    Cleans the raw data from the .txt files and creates new columns based on
    extra within the original columns.
    """

    row = create_te_ms_columns(appl_key_to_ms_enum, appl_key_to_te_enum, row)

    row = expand_strength(row)
    row = expand_dosage_form(row)
    row = expand_admin_route(row)

    # replace malformed strings for better formatting
    ingredients = row['ActiveIngredient']
    for bad_format, improved_format in ILL_FORMATTED_INGREDIENTS.items():
        ingredients = ingredients.replace(bad_format, improved_format)
    row['CleanActiveIngredient'] = ingredients.title()

    # get enum for application type
    appl_type = row['ApplType']
    if appl_type in APPLICATION_TYPE_ENUMS:
        row['ApplTypeEnum'] = 'dcid:' + APPLICATION_TYPE_ENUMS[appl_type]

    row['DrugRef'] = get_drug_ref(row['DrugName'], row['CleanActiveIngredient'])

    return row


def get_df(file_name_dict):
    """Returns a single DataFrame containing cleaned data from Applications.txt,
    Products.txt, MS.txt, TE.txt, and utils/drug_refs.json. Writes the generated
    DataFrame to a csv.
    """
    with open(file_name_dict['products_file_name'], 'r') as products_file:
        lines = [line.strip() + '\n' for line in products_file]

    with open(file_name_dict['clean_products_out'], 'w') as products_file:
        products_file.writelines(lines)

    # merge the columns from Applications.txt and Products.txt
    products_df = pd.read_csv(file_name_dict['clean_products_out'], sep='\t')
    products_df = products_df.fillna('')

    applications_df = pd.read_csv(file_name_dict['applications_file_name'],
                                  sep='\t')
    applications_df = applications_df.fillna('')

    print('....merging Products.txt and Applications.txt')
    drugs_df = pd.merge(left=products_df,
                        right=applications_df,
                        how='left',
                        left_on=['ApplNo'],
                        right_on=['ApplNo'],
                        indicator=True)

    print('....splitting Form Column into DosageForm and AdminRoute')
    cleaned_form = drugs_df["Form"].map(lambda form: ILL_FORMATTED_FORMS[
        form] if form in ILL_FORMATTED_FORMS else form)
    drugs_df["DosageForm"] = cleaned_form.str.split(";", expand=True)[0]
    drugs_df["AdminRoute"] = cleaned_form.str.split(";",
                                                    expand=True)[1].fillna('')

    appl_key_to_ms_enum = defaultdict(set)
    appl_key_to_te_enum = defaultdict(set)

    print('....loading TE.txt')
    # read and save te_codes and MarketingStatus IDs from TECodes.txt into dictionary
    te_df = pd.read_csv(file_name_dict['te_file_name'], sep='\t')
    te_df = te_df.fillna('')
    te_df.apply(lambda x: populate_dicts_from_te_df(appl_key_to_ms_enum,
                                                    appl_key_to_te_enum, x),
                axis=1)

    print('....loading MS.txt')
    # read and save Marketing Status IDs from MarketingStatus.txt into dictionary
    ms_df = pd.read_csv(file_name_dict['market_stat_file_name'], sep='\t')
    ms_df = ms_df.fillna('')
    ms_df.apply(lambda x: populate_dict_from_ms_df(appl_key_to_ms_enum, x),
                axis=1)

    print('....expanding DataFrame')
    drugs_df = drugs_df.apply(
        lambda x: expand_df(appl_key_to_ms_enum, appl_key_to_te_enum, x),
        axis=1)
    with open("./drug_refs_updated.json", "w") as outfile:
        json.dump(drug_ref_db, outfile)

    drugs_df = drugs_df.fillna('')
    drugs_df.to_csv(file_name_dict['clean_data_out'], index=False)

    return drugs_df
