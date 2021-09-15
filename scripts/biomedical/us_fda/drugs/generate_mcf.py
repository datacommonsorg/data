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
"""Write data mcf file for FDA Drugs Import.

This file contains the functions related to creating and writing the final data
mcf file for the FDA Drugs import.
"""
import re
from sys import path

from utils.config import FDA_APP_TEMPLATE, ACTIVE_INGRED_TEMPLATE, \
STRENGTH_TEMPLATE, DRUG_TEMPLATE, FDA_NODE, INGREDIENT_REPLACEMENTS
from utils.format import get_qty_format, get_qty_range_format

path.insert(1, '../../../')
from util import mcf_template_filler


def write_active_ingred_node(mcf_file, amount, ingredient):
    """Writes an active ingredient node in mcf format to mcf_file given an
    ingredient and the ingredient's amount.

    Sometimes the amount has two quantities as in '500mg/25ml (20mg/ml)',
    causing the need for the parentheses check seen in the function. Amount can
    be a single quantity or a quantity range.
    """

    if '-' in amount and 'OMEGA-3' not in amount and 'SINGLE-USE' not in amount:
        amount_qty = get_qty_range_format(amount.split('(')[0])
    else:
        amount_qty = get_qty_format(amount.split('(')[0])

    if '(' in amount:
        if '-' in amount and 'OMEGA-3' not in amount and 'SINGLE-USE' not in amount:
            second_amount_qty = get_qty_range_format(
                amount.split('(')[1].replace(')', ''))
        else:
            second_amount_qty = get_qty_format(
                amount.split('(')[1].replace(')', ''))
        amount_qty = amount_qty + ',' + second_amount_qty

    name = (ingredient.strip() + '_' + amount_qty).strip()

    for special_format, replace_format in INGREDIENT_REPLACEMENTS.items():
        name = name.replace(special_format, replace_format).strip()
    name = re.sub("[^0-9a-zA-Z_-]+", "", name).title()
    dcid = 'dcid:bio/' + name

    ingred_templater = mcf_template_filler.Filler(ACTIVE_INGRED_TEMPLATE,
                                                  required_vars=['dcid'])
    ingred_mcf = ingred_templater.fill({
        'active_ingred_dcid': dcid,
        'ingred_amount_qty': amount_qty,
        'ingred_name': ingredient.strip(),
        'name': name,
    })
    mcf_file.write(ingred_mcf)

    return dcid


def zip_ingred_comma_sep(mcf_file, strength_format_map, row):
    """Zips ingredients and strengths together when the ingredients are
    separated by a comma in the strengths column.

    Ex: strengths: 1mg, 2mg; 3mg, 4mg; 5mg, 6mg
        ingreidents: ingred1;ingred2
    resulting DrugStrength Nodes where ActiveIngredientAmount nodes are comma
    separated:
      * Strength 1: 1mg - ingred1, 2mg-ingred2
      * Strength 2: 3mg - ingred1, 4mg-ingred2
      * Strength 3: 5mg-ingred1, 6mg-ingred2
    """
    strengths = row['CleanStrength']
    active_ingreds = row['CleanActiveIngredient']

    strength_dcids = []
    base_dcid = strength_format_map['strength_dcid']

    for index, ingred_pair_list in enumerate(strengths.split(';')):
        strength_dcids.append(base_dcid + '_' + str(index))
        active_ingred_dcids = []

        for ingred_index, strength in enumerate(ingred_pair_list.split(',')):
            ingred_name = active_ingreds.split(
                ';')[ingred_index].strip().title()
            ingred_dcid = write_active_ingred_node(mcf_file, strength,
                                                   ingred_name)
            active_ingred_dcids.append(ingred_dcid)

        strength_format_map['strength_dcid'] = base_dcid + '_' + str(index)
        strength_format_map['name'] = (base_dcid + '_' + str(index)).replace(
            'dcid:bio/', '')
        strength_format_map['active_ingred_dcids'] = ','.join(
            active_ingred_dcids)

        strength_format_map = {
            key: value
            for key, value in strength_format_map.items() if value
        }
        strength_templater = mcf_template_filler.Filler(STRENGTH_TEMPLATE,
                                                        required_vars=['dcid'])
        strength_mcf = strength_templater.fill(strength_format_map)
        mcf_file.write(strength_mcf)
    return strength_dcids


# set strength dcid and active inred dcids in format map
def zip_ingred_semi_sep(mcf_file, strength_format_map, row):
    """Zips ingredients and strengths together when the ingredients are
    separated by a semi colon in the strengths column.

    Ex: strengths: 1 mg, 2mg, 3mg; 4mg, 5mg, 6mg
        ingredients: ingred1 ; ingred2
    resulting DrugStrength Nodes where ActiveIngredientAmount nodes are comma
    separated:
      * Strength 1:  1mg - ingred1, 4mg-ingred2
      * Strength 2: 2mg - ingred1, 5mg - ingred2
      * Strength 3: 3mg-ingred1, 6mg - ingred2
    """
    strengths = row['CleanStrength']
    active_ingreds = row['CleanActiveIngredient']

    strength_lists = []
    strength_lists.append(strengths.split(';')[0].split(','))

    base_dcid = strength_format_map['strength_dcid']
    strength_dcids = []

    # get all lists in strength_list
    for strength_list in strengths.split(';')[1:]:
        strength_list_comma_sep = strength_list.split(',')
        strength_lists.append(strength_list_comma_sep)

    for index, stren in enumerate(strength_lists[0]):
        strength_dcids.append(base_dcid + '_' + str(index))
        active_ingred_dcids = []
        for ingred_index, ingred_pair_list in enumerate(strength_lists):
            strength = ingred_pair_list[index]
            ingred_name = active_ingreds.split(
                ';')[ingred_index].strip().title()
            ingred_dcid = write_active_ingred_node(mcf_file, strength,
                                                   ingred_name)
            active_ingred_dcids.append(ingred_dcid)
        strength_format_map['strength_dcid'] = base_dcid + '_' + str(index)
        strength_format_map['name'] = (base_dcid + '_' + str(index)).replace(
            'dcid:bio/', '')
        strength_format_map['active_ingred_dcids'] = ','.join(
            active_ingred_dcids)

        strength_format_map = {
            key: value
            for key, value in strength_format_map.items() if value
        }
        strength_templater = mcf_template_filler.Filler(STRENGTH_TEMPLATE,
                                                        required_vars=['dcid'])
        strength_mcf = strength_templater.fill(strength_format_map)
        mcf_file.write(strength_mcf)
    return strength_dcids


def get_strength_qtys(strengths):
    """Converts raw strengths as text to mcf formatted quantities and returns as
    string.

    Used for appending all ingredient amounts to a single strength node.
    """
    strength_qtys = []
    separated_strengths = filter(None, re.split("[;,]+", strengths))
    for strength in separated_strengths:
        strength_qtys.append(get_qty_format(strength.strip()))
    return ','.join(strength_qtys)


def parse_strength_nodes(mcf_file, fda_app, row):
    """Determines if active ingredient nodes need to be generated and written to
    file by zipping Strength and ActiveIngredient columns.

    If the columns Strength and ActiveIngredient cannot be zipped, then single
    drug strength nodes is created and wirrten to mcf_file. This drug strength
    node has the strengths as a list of quantities and active ingredients as a
    list of strings. Otherwise the drug strength would point to Active
    Ingredient Amount nodes via dcids.
    """
    strength_dcid = 'dcid:bio/' + row['DrugRef'] + '_Strength-' + str(
        row['ApplNo']) + '-' + str(row['ProductNo'])
    ingred_name_list = '","'.join(
        [ingred.strip() for ingred in row['CleanActiveIngredient'].split(';')])
    strength_format_map = {
        'strength_dcid':
        strength_dcid,
        'fda_app_dcid':
        fda_app,
        'fda_prod_no':
        str(row['ProductNo']),
        'name':
        row['DrugRef'] + '_Strength-' + str(row['ApplNo']) + '-' +
        str(row['ProductNo']),
        'ingred_names':
        ingred_name_list,
        'te_enums':
        row['TECodes'],
        'ms_enums':
        row['MarketStatus'],
        'course_qty':
        row['DrugCourse'],
        'is_single_dose':
        row['SingleDose'],
        'sponsor':
        row['SponsorName'].title(),
        'final_vol_qty':
        row['FinalVolQty'],
    }

    strengths = row['CleanStrength']
    active_ingreds = row['CleanActiveIngredient']

    if active_ingreds and strengths:

        if len(strengths.split(';')) == len(active_ingreds.split(';')):
            return zip_ingred_semi_sep(mcf_file, strength_format_map, row)

        if strengths.split(';')[0].count(',') == len(
                active_ingreds.split(';')) - 1:
            return zip_ingred_comma_sep(mcf_file, strength_format_map, row)

    strength_format_map['strength_qty'] = get_strength_qtys(
        row['CleanStrength'])
    strength_format_map = {
        key: value
        for key, value in strength_format_map.items() if value
    }
    strength_templater = mcf_template_filler.Filler(STRENGTH_TEMPLATE,
                                                    required_vars=['dcid'])
    strength_mcf = strength_templater.fill(strength_format_map)
    mcf_file.write(strength_mcf)

    return [strength_dcid]


def parse_row(mcf_file, seen_fda_apps, row):
    """Writes nodes in mcf format to mcf_file.

    First writes FDA Application node. Parses strength nodes, writing Active
    Ingreident Amount nodes when necessary, then writes the strength nodes.
    Finally, one drug node is written per row.
    """

    fda_app = 'dcid:bio/FDA_Application_' + str(row['ApplNo'])

    if row['ApplNo'] not in seen_fda_apps:

        app_template_map = {
            'fda_app_dcid': fda_app,
            'appl_num': str(row['ApplNo']),
            'name': 'FDA_Application_' + str(row['ApplNo']),
            'sponsor_name': row['SponsorName'].title(),
            'appl_type_enums': row['ApplTypeEnum'],
        }
        app_template_map = {
            key: value
            for key, value in app_template_map.items() if value
        }
        fda_app_templater = mcf_template_filler.Filler(FDA_APP_TEMPLATE,
                                                       required_vars=['dcid'])
        fda_app_mcf = fda_app_templater.fill(app_template_map)

        mcf_file.write(fda_app_mcf)
        seen_fda_apps.append(row['ApplNo'])

    strength_dcids = parse_strength_nodes(mcf_file, fda_app, row)
    ingred_name_list = '","'.join(
        [ingred.strip() for ingred in row['CleanActiveIngredient'].split(';')])
    drug_format_map = {
        'drug_ref': 'bio/' + row['DrugRef'],
        'name': row['DrugRef'],
        'synonyms': '","'.join(row['DrugName'].split(';')).title(),
        'strength_dcids': ','.join(strength_dcids),
        'ingred_names': ingred_name_list,
        'dosage_form_enum': row['DosageFormEnums'],
        'admin_route_enum': row['AdminRouteEnums'],
        'additional_info': row['AdditionalInfo'],
    }

    if row['ReferenceStandard'] == 0:
        drug_format_map['is_ref_std'] = 'False'
    if row['ReferenceStandard'] and row['ReferenceStandard'] > 0:
        drug_format_map['is_ref_std'] = 'True'
    if row['ReferenceDrug'] == 0:
        drug_format_map['is_available_generically'] = 'False'
    if row['ReferenceDrug'] and row['ReferenceDrug'] > 0:
        drug_format_map['is_available_generically'] = 'True'

    drug_format_map = {
        key: value
        for key, value in drug_format_map.items() if value
    }
    drug_templater = mcf_template_filler.Filler(DRUG_TEMPLATE,
                                                required_vars=['dcid'])
    drug_mcf = drug_templater.fill(drug_format_map)
    mcf_file.write(drug_mcf)


def create_mcf(file_name, drugs_df):
    """Parses each row of the given DataFrame, writing the data in MCF format
    to the given file name.
    """
    seen_fda_apps = []

    mcf_file = open(file_name, 'w')

    mcf_file.write(FDA_NODE)

    drugs_df.apply(lambda row: parse_row(mcf_file, seen_fda_apps, row), axis=1)

    mcf_file.close()
