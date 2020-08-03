"""Write data mcf file for FDA Drugs Import.

This file contains the functions related to creating and writing the final data
mcf for the FDA Drugs import called FDADrugFinal.mcf .
"""

import re
import pandas as pd
from func_timeout import func_timeout, FunctionTimedOut
from chembl_webresource_client.new_client import new_client
from clean_data import get_quant_format
from create_enums import generate_enums

molecule = new_client.molecule


def get_quant_range_format(strength):
    """Retruns the quantity range format [# # UNIT] for a given strength.
    """
    split_list = list(filter(None, re.split(r'(\d*[.]?\d+)', strength)))
    first_val = split_list[0]
    for index, item in enumerate(split_list[1:]):
        if re.fullmatch(r'(\d*[.]?\d+)', item):
            second_val = item
            units = "".join(split_list[index + 2:])
            break
    return '[' + first_val + ' ' + second_val + ' ' + units.strip() + ']'


# FUNCTIONS: appending for fda Application functions
def append_appl_type_enum(fda_app_mcf, appl_type, appl_type_enums):
    """Returns FDAApplication node mcf after appending the application type
    enum dcid if application type exists.
    """
    if appl_type:
        if appl_type in appl_type_enums:
            fda_app_mcf = fda_app_mcf + 'applicationType: dcid:' + appl_type_enums[
                appl_type] + '\n'

    return fda_app_mcf


# FUNCTIONS:  appending properties for drug_mcf node


def append_dosage_form_enum(drug_mcf, drug_dosage_forms, dosage_form_enums):
    """Returns Drug node mcf after appending the dosage form enum dcid if
    the dosage form exists.
    """

    unusual_dosage_forms = {
        'TROCHE/LOZENGE':
            'TROCHE, LOZENGE',
        '/':
            ',',
        'INJECTABLE':
            'INJECTION',
        'Injectable':
            'Injection',
        'INJECTION, LIPOSOMAL':
            'INJECTABLE, LIPOSOMAL',
        'PELLETS':
            'PELLET',
        'TABLET, EXTENDED RELEASE, CHEWABLE':
            'TABLET, CHEWABLE, EXTENDED RELEASE',
        'SOLUTION FOR SLUSH':
            'SOLUTION, FOR SLUSH',
        'REL ':
            'RELEASE '  # space char after REL is necessary to distinguish REL from RELEASE
    }

    if not drug_dosage_forms or drug_dosage_forms == 'N/A':
        return drug_mcf

    drug_dosage_forms = drug_dosage_forms.replace('N/A', '')

    # replace the malformed patterns with the better format
    for bad_form in unusual_dosage_forms:
        drug_dosage_forms = drug_dosage_forms.replace(
            bad_form, unusual_dosage_forms[bad_form])

    # FDA splits the dosage forms by comma, even though some dosage forms have
    # commas inside of them
    split = drug_dosage_forms.split(',')

    while len(split) > 1:
        # must check for the cases where there is commas in the dosage form ie
        # TABLET, CHEWABLE, EXTENDED REALEASE is all one dosage form
        if len(split) > 3:
            specialization = (split[0].strip() + ', ' + split[1].strip() +
                              ', ' + split[2].strip() + ', ' +
                              split[3].strip()).title()
            if specialization in dosage_form_enums:
                drug_mcf = drug_mcf + 'dosageForm: dcid:' + dosage_form_enums[
                    specialization] + '\n'
                split = split[4:]
                continue
        if len(split) > 2:
            specialization = (split[0].strip() + ', ' + split[1].strip() +
                              ', ' + split[2].strip()).title()
            if specialization in dosage_form_enums:
                drug_mcf = drug_mcf + 'dosageForm: dcid:' + dosage_form_enums[
                    specialization] + '\n'
                split = split[3:]
                continue
        specialization = (split[0].strip() + ', ' + split[1].strip()).title()
        if specialization in dosage_form_enums:
            drug_mcf = drug_mcf + 'dosageForm: dcid:' + dosage_form_enums[
                specialization] + '\n'
            split = split[2:]
        elif split[0].strip().title() in dosage_form_enums:
            drug_mcf = drug_mcf + 'dosageForm: dcid:' + dosage_form_enums[
                split[0].strip().title()] + '\n'
            split = split[1:]
        else:
            print('unrecognized dosage_form_enums: ' + str(split) + 'from: ' +
                  drug_dosage_forms)
            split = split[1:]
    if len(split) == 1:
        if split[0].strip().title() in dosage_form_enums:
            drug_mcf = drug_mcf + 'dosageForm: dcid:' + dosage_form_enums[
                split[0].strip().title()] + '\n'
        else:
            print('unrecognized dosage_form_enums: ' + str(split) + 'from: ' +
                  drug_dosage_forms)

    return drug_mcf


def append_admin_route_enum(drug_mcf, drug_admin_routes, admin_route_enums):
    """Returns Drug node mcf after appending the administration route enum dcid
    if the dosage form exists.
    """
    if not drug_admin_routes:
        return drug_mcf

    comma_sep_admin_routes = {
        'PERFUSION, CARDIAC': 'AdministrationRoutePerfusionCardiac',
        'PERFUSION, BILIARY': 'AdministrationRoutePerfusionBiliary',
        'INTRACORONAL, DENTAL': 'AdministrationRouteIntracoronalDental',
    }

    synonyms = {
        'INHALATION': 'RESPIRATORY (INHALATION)',
        'N/A': 'NOT APPLICABLE',
        'OTIC': 'AURICULAR (OTIC)',
        'SPINAL': 'INTRASPINAL',
        'ORAL-20': 'ORAL',
        'ORAL-28': 'ORAL',
        'ORAL-21': 'ORAL',
        'IV (INFUSION)': 'INTRAVENOUS DRIP',
        'INTRAVESICULAR': 'INTRAVESICAL',
        'INTRAOSSEOUS': 'INTRAMEDULLARY'
    }

    dose_types = ['SINGLE-DOSE', 'SINGLE-USE', 'MULTIDOSE']
    oral_drug_course = ['ORAL-28', 'ORAL-21', 'ORAL-20']

    drug_admin_routes = drug_admin_routes.upper()
    drug_admin_routes = drug_admin_routes.replace('IM-IV',
                                                  'INTRAVENOUS, INTRAMUSCULAR')

    for admin_route in comma_sep_admin_routes:
        if admin_route in drug_admin_routes:
            drug_mcf = drug_mcf + 'administrationRoute: dcid:' + comma_sep_admin_routes[
                admin_route] + '\n'
            drug_admin_routes = drug_admin_routes.replace(admin_route, '')

    split = drug_admin_routes.split(',')
    for route in split:
        route = route.strip()
        if route in oral_drug_course or route in dose_types:
            continue
        if route == 'SUSPENSION':
            drug_mcf = drug_mcf + 'dosageForm: dcid:DosageFormSuspension\n'
        elif route == 'ORAL SUSPENSION':
            drug_mcf = drug_mcf + 'dosageForm: dcid:DosageFormSuspension\n'
            drug_mcf = drug_mcf + 'administrationRoute: dcid:AdministrationRouteOral\n'
        elif route == 'SUBCUTANEOUS LYOPHILIZED POWER':
            drug_mcf = drug_mcf + 'dosageForm: dcid:DosageFormPowderLyophilizedPowder\n'
            drug_mcf = drug_mcf + 'administrationRoute: dcid:AdministrationRouteSubcutaneous\n'
        elif route == 'ORALLY DISINTEGRATING':
            drug_mcf = drug_mcf + 'dosageForm: dcid:DosageFormTabletOrallyDisintegrating\n'
            drug_mcf = drug_mcf + 'administrationRoute: dcid:AdministrationRouteOral\n'
        elif route == '':
            continue
        else:
            for alternate in synonyms:
                route = route.replace(alternate, synonyms[alternate])
            if route.title() in admin_route_enums:
                drug_mcf = drug_mcf + 'administrationRoute: dcid:' + admin_route_enums[
                    route.title()] + '\n'
            else:
                print('unrecognized admin_route_enums: ' + str(route) +
                      ' from ' + drug_admin_routes)
    return drug_mcf


def append_ref_standard_mcf(drug_mcf, standard):
    """Returns Drug node mcf after appending the reference standard property if
    the reference standard boolean is not null.
    """
    if standard == 1:
        drug_mcf = drug_mcf + 'isFDAReferenceStandard: True\n'
    elif standard == 0:
        drug_mcf = drug_mcf + 'isFDAReferenceStandard: False\n'

    return drug_mcf


def append_available_generically_mcf(drug_mcf, generic):
    """Returns Drug node mcf after appending the is available generically
    property that comes from the ReferenceDrug column of the clean dataframe.
    """
    if generic == 1:
        drug_mcf = drug_mcf + 'isAvailableGenerically: True\n'
    elif generic == 0:
        drug_mcf = drug_mcf + 'isAvailableGenerically: False\n'

    return drug_mcf


def get_id_from_chembl_file(line):
    """Helper method to extract chembl id from line of chembl_ids.out file.
    """
    molec = line.split(' ')[0]
    chembl_id = molec.replace('chembl_molecule:', '').strip()
    return chembl_id


def get_label_from_chembl_file(line):
    """Helper method to extract label from line of chembl_ids.out file.
    """
    label = re.findall(r'(?<=").*?(?=")', line)
    if len(label) != 1:
        print('Unexpected number of labels in ChemblFile: ' + str(label))
    return label[0]


def get_chembl_dict_from_file():
    """Loads a dictionary of drug names to chembl ids from the chembl_ids.out
    file using helper functions. Returns the dictionary.
    """
    # load chembl_ids from chembl file
    chembl_file_drugs = {}
    with open('raw_data/chembl_ids.out') as chembl_id_out:
        for line in chembl_id_out:
            if 'rdfs:label "CHEMBL' not in line:
                label = get_label_from_chembl_file(line)
                chembl_id = get_id_from_chembl_file(line)

                if label in chembl_file_drugs and chembl_id not in chembl_file_drugs[
                        label]:
                    chembl_file_drugs[label].append(chembl_id)
                else:
                    chembl_file_drugs[label] = [chembl_id]
    return chembl_file_drugs


# FUNCTIONS: match drugName to chembl_id
def get_chembl_id_through_api(search):
    """Uses the chembl python api to search for a chembl ID based on the
    drug name.
    """
    search = search.strip()
    chembl_id = None
    for molec in molecule.search(search):
        #print(molec)
        for molec_synonym in molec['molecule_synonyms']:
            if molec_synonym['molecule_synonym'].lower() == search.lower():
                chembl_id = molec['molecule_chembl_id']
                #print('found: ' + search)
                return chembl_id
    return chembl_id


def get_ref_name(synonyms):
    """Returns a suitable reference name for a drug when the chembl ID cannot
    be found. This reference name is used in dcids and therefore must not contain
    special characters.
    """
    ref_name = synonyms.replace(' , ', '_')
    ref_name = ref_name.replace(', ', '_')
    ref_name = ref_name.replace(',', '_')
    ref_name = ref_name.replace('/ ', '_')
    ref_name = ref_name.replace('/', '-')
    ref_name = ref_name.replace('- ', '-')
    ref_name = ref_name.replace(' IN PLASTIC CONTAINER', '').strip()
    ref_name = ref_name.replace(' IN WATER', '').strip()

    ref_name = ref_name.replace(' ', '_')
    ref_name = ref_name.replace('%', 'PRCT')

    ref_name = re.sub("[^0-9a-zA-Z_-]+", "", ref_name).title()

    if len(ref_name) > 136:
        print('WARNING ref_name too long: ' + ref_name)
    #print(ref_name)

    return ref_name


def get_drug_ref_name(synonyms, active_ingred, chembl_file_drugs):
    """Returns list of chembl IDs or drug references that will be used in the
    drug node's dcid.
    """
    check_list = [' AND ', ';', ' IN ']
    if any(check in synonyms for check in check_list):
        return get_ref_name(synonyms)

    synonyms = synonyms.replace('\'', '')
    synonyms = synonyms.replace('.', '')
    search_name = re.split(r'[^a-zA-Z\s-]', synonyms)[0]

    chembl_id = None
    if not search_name:
        return get_ref_name(active_ingred)
    if search_name in chembl_file_drugs:
        chembl_id = chembl_file_drugs[search_name]
    else:
        try:
            chembl_id = func_timeout(10,
                                     get_chembl_id_through_api,
                                     args=(search_name,))
        except FunctionTimedOut:
            chembl_id = None
        except:
            chembl_id = None

    if not chembl_id:
        return get_ref_name(synonyms)

    return chembl_id


# FUNCTIONS: creating active_ingredientAmount nodes


def get_active_ingred_amount_dcid(ingred, quants):
    """Returns dcid for a given ingredient-quantity pair.
    """
    dcid = "_".join(ingred.strip().split(' ')) + '_' + quants
    dcid = dcid.strip()
    dcid = dcid.replace(' , ', '_')
    dcid = dcid.replace(', ', '_')
    dcid = dcid.replace(',', '_')
    dcid = dcid.replace('N/A', 'NA')
    dcid = dcid.replace('/ ', '_')
    dcid = dcid.replace('/', '-')
    dcid = dcid.replace(' ', '_')

    dcid = dcid.replace('%', 'PRCT')

    dcid = re.sub("[^0-9a-zA-Z_-]+", "", dcid).title()

    if len(dcid) > 256:
        print('WARNING DCID too Long: ' + dcid)

    return dcid


def get_active_ingred_amount(strength_pair, ingred_name):
    """Returns the mcf string for an ActiveIngredientAmount node and its dcid
    for a given strength and ingredient.
    """
    if strength_pair == '' or not strength_pair or strength_pair == 'nan':
        return '', ''

    quants = ''

    for strength in strength_pair.split('('):
        strength = strength.replace(')', '').strip()

        if '-' in strength and 'OMEGA-3' not in strength and 'SINGLE-USE' not in strength:
            quant = get_quant_range_format(strength)
        else:
            quant = get_quant_format(strength)

        quants = quants + quant + ','

    quants = quants.strip(',')

    dcid = get_active_ingred_amount_dcid(ingred_name, quants)

    active_ingred_amount_mcf = '\nNode: dcid:bio/' + dcid + '\n'
    active_ingred_amount_mcf = active_ingred_amount_mcf + 'typeOf: dcid:ActiveIngredientAmount\n'
    active_ingred_amount_mcf = active_ingred_amount_mcf + 'name: "' + dcid + '"\n'
    active_ingred_amount_mcf = active_ingred_amount_mcf + 'ingredientAmount: ' + quants + '\n'
    active_ingred_amount_mcf = active_ingred_amount_mcf + 'ingredientName: "' + ingred_name + '"\n'

    return dcid, active_ingred_amount_mcf


def get_active_ingredients_as_list(ingreds):
    """Parses and returns a string of ingredients as a separated list split at
    semicolons.
    """
    ingred_list = []

    if not ingreds:
        return ingred_list

    ingreds = str(ingreds).strip().title()

    for ingred in ingreds.split(';'):
        ingred_list.append(ingred.strip())
    return ingred_list


def append_all_ingredients(mcf, active_ingred):
    """Appends all ingredients as comma separated strings in mcf format to a
    given node.
    """
    if not active_ingred:
        return mcf
    ingreds = get_active_ingredients_as_list(active_ingred)
    return mcf + 'activeIngredient: "' + '","'.join(ingreds) + '"\n'


def append_all_strengths(drug_strength_mcf, strength_split):
    """Appends all strengths as comma separated quantities in mcf format to a
    given node.
    """
    quants = ''

    for strength in strength_split:
        for strength_no_paren in strength.split('('):
            quant = get_quant_format(strength_no_paren.replace(')', '').strip())
            quants = quants + quant + ','
    quants = quants.strip(',')

    drug_strength_mcf = drug_strength_mcf + 'hasStrength: ' + quants + '\n'

    return drug_strength_mcf


# FUNCTIONS: matching strengths to ingredients for Strength related nodes


def zip_ingred_semi_sep(mcf_file, drug_strength_dcid, row):
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
    strengths = row['Strength']
    active_ingreds = row['ActiveIngredient']

    strength_split_on_semi = strengths.split(';')
    ingred_split_on_semi = active_ingreds.split(';')

    drug_strength_mcf_list = {}

    strength_lists = []
    strength_lists.append(strength_split_on_semi[0].split(','))

    # get all lists in strength_list
    for strength_list in strength_split_on_semi[1:]:
        strength_list_comma_sep = strength_list.split(',')
        if len(strength_list_comma_sep) != len(strength_lists[0]):
            print('MisMatch number of strengths when zipping: ' +
                  str(row['Strength']))
            return []
        strength_lists.append(strength_list_comma_sep)

    for index, stren in enumerate(strength_lists[0]):
        strength_dcid = drug_strength_dcid + '_' + str(index)
        drug_strength_mcf = '\nNode: dcid:bio/' + strength_dcid + '\n'
        for ingred_index, ingred_pair_list in enumerate(strength_lists):
            strength = ingred_pair_list[index]
            ingred_name = ingred_split_on_semi[ingred_index].strip().title()
            ingred_dcid, ingred_mcf = get_active_ingred_amount(
                strength, ingred_name)
            mcf_file.write(ingred_mcf)
            drug_strength_mcf = (drug_strength_mcf +
                                 'hasActiveIngredientAmount: dcid:bio/' +
                                 ingred_dcid + '\n')
        drug_strength_mcf_list[strength_dcid] = drug_strength_mcf
    return drug_strength_mcf_list


def zip_ingred_comma_sep(mcf_file, drug_strength_dcid, row):
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
    strengths = row['Strength']
    active_ingreds = row['ActiveIngredient']

    drug_strength_mcf_list = {}

    strength_split_on_semi = strengths.split(';')
    ingred_split_on_semi = active_ingreds.split(';')

    for index, ingred_pair_list in enumerate(strength_split_on_semi):
        strength_dcid = drug_strength_dcid + '_' + str(index)
        drug_strength_mcf = '\nNode: dcid:bio/' + strength_dcid + '\n'

        for ingred_index, strength in enumerate(ingred_pair_list.split(',')):
            ingred_name = ingred_split_on_semi[ingred_index].strip().title()
            ingred_dcid, ingred_mcf = get_active_ingred_amount(
                strength, ingred_name)
            mcf_file.write(ingred_mcf)
            drug_strength_mcf = (drug_strength_mcf +
                                 'hasActiveIngredientAmount: dcid:bio/' +
                                 ingred_dcid + '\n')

        drug_strength_mcf_list[strength_dcid] = drug_strength_mcf
    return drug_strength_mcf_list


# Functions: handling multiple drug Nodes or multiple drugStrengths
def replace_ref(drug_mcf, ref):
    """Helper method to replace the drug reference in an mcf node to copy drug
    info to multiple dcids (when multiple chembl ids are found)
    """
    new_mcf = re.sub('(Node: dcid:bio/).*(\n)', r'\1' + ref + r'\2', drug_mcf)
    return new_mcf


def write_fda_app_mcf(mcf_file, fda_app_dcid, appl_type_to_dcid, row):
    """Create and  write FDA Application mcf node to file.
    """
    appl_num = str(row['ApplNo'])
    appl_type = str(row['ApplType'])

    sponsor_mcf = ''
    if row['SponsorName']:
        sponsor_mcf = 'sponsor: "' + str(row['SponsorName']).title() + '"\n'

    fda_app_mcf = '\nNode: dcid:bio/' + fda_app_dcid + '\n'
    fda_app_mcf = fda_app_mcf + 'typeOf: dcid:FDAApplication\n'
    fda_app_mcf = fda_app_mcf + 'name: "' + fda_app_dcid + '"\n'
    fda_app_mcf = fda_app_mcf + 'fdaApplicationNumber: "' + appl_num + '"\n'
    fda_app_mcf = append_appl_type_enum(fda_app_mcf, appl_type,
                                        appl_type_to_dcid)
    fda_app_mcf = fda_app_mcf + sponsor_mcf
    mcf_file.write(fda_app_mcf)


def get_drug_ref_list(row, synonym_to_ref_dict, chembl_file_drugs):
    """Calls the get drug reference helper methods to get the drug references,
    then formats it into list.
    """
    synonyms = row['DrugName']
    active_ingred = row['ActiveIngredient']
    # get drug reference used in dcid
    if not synonyms:
        drug_ref = get_drug_ref_name(synonyms, active_ingred, chembl_file_drugs)
    elif synonyms in synonym_to_ref_dict:
        drug_ref = synonym_to_ref_dict[synonyms]
    else:
        drug_ref = get_drug_ref_name(synonyms, active_ingred, chembl_file_drugs)
        synonym_to_ref_dict[synonyms] = drug_ref

    if isinstance(drug_ref, list):
        return drug_ref

    return [drug_ref]


def initialize_drug_mcf(drug_ref, row, admin_route_to_dcid,
                        dosage_form_to_dcid):
    """Initializes Drug node mcf with all properties excpet for DrugStrengths.
    """
    synonyms = row['DrugName']

    # create and add info to drug Node
    drug_mcf = '\nNode: dcid:bio/' + drug_ref + '\n'
    drug_mcf = drug_mcf + 'typeOf: schema:Drug\n'
    drug_mcf = drug_mcf + 'name: "' + drug_ref + '"\n'

    if synonyms:
        drug_mcf = drug_mcf + 'drugName: "' + synonyms.title() + '"\n'

    drug_mcf = drug_mcf + 'recognizingAuthority: dcid:USFederalDrugAdministration\n'
    drug_mcf = drug_mcf + row['AdditionalInfoMCF']
    drug_mcf = append_ref_standard_mcf(drug_mcf, row['ReferenceStandard'])
    drug_mcf = append_available_generically_mcf(drug_mcf, row['ReferenceDrug'])
    drug_mcf = append_admin_route_enum(drug_mcf, row['AdminRoute'],
                                       admin_route_to_dcid)
    drug_mcf = append_dosage_form_enum(drug_mcf, row['DosageForm'],
                                       dosage_form_to_dcid)
    drug_mcf = append_all_ingredients(drug_mcf, row['ActiveIngredient'])
    return drug_mcf


def append_drug_strength_properties(row, fda_app_dcid, strength_mcf):
    """Appends DrgStrength properties to DrugStrength node.
    """
    strength_mcf = strength_mcf + 'typeOf: schema:DrugStrength\n'
    strength_mcf = append_all_ingredients(strength_mcf, row['ActiveIngredient'])
    manufacturer_mcf = ''
    if row['SponsorName']:
        manufacturer_mcf = 'manufacturer: "' + str(
            row['SponsorName']).title() + '"\n'
    strength_mcf = strength_mcf + row['FinalVolMCF']
    strength_mcf = strength_mcf + row['TECodeMCF']
    strength_mcf = strength_mcf + row['MarketStatMCF']
    strength_mcf = strength_mcf + row['DrugCourseMCF']
    strength_mcf = strength_mcf + row['DoseTypeMCF']
    strength_mcf = strength_mcf + 'fdaProductID: "' + str(
        row['ProductNo']) + '"\n'
    strength_mcf = strength_mcf + 'submittedFDAApplication: dcid:bio/' + fda_app_dcid + '\n'
    strength_mcf = strength_mcf + manufacturer_mcf
    return strength_mcf


def initialize_single_drug_strength(row, drug_strength_dcid):
    """Initialized a DrugStrength node with a given dcid.
    """
    drug_strength_mcf = drug_strength_mcf = '\nNode: dcid:bio/' + drug_strength_dcid + '\n'
    strength_split_on_semi = row['Strength'].split(';')
    drug_strength_mcf = append_all_strengths(drug_strength_mcf,
                                             strength_split_on_semi)
    return {drug_strength_dcid: drug_strength_mcf}


def write_drug_strength_mcf(mcf_file, drug_mcf, drug_ref, fda_app_dcid, row):
    """Create and write DrugStrength Node to file. Add the DrugStrength dicd
    as a property to Drug node.
    """
    strengths = row['Strength']
    active_ingreds = row['ActiveIngredient']

    drug_strength_mcf_list = {}
    drug_strength_dcid = drug_ref + '_Strength-' + str(
        row['ApplNo']) + '-' + str(row['ProductNo'])

    if active_ingreds and strengths:
        strength_split_on_semi = strengths.split(';')
        ingred_split_on_semi = active_ingreds.split(';')

        if len(strength_split_on_semi) == len(ingred_split_on_semi):
            drug_strength_mcf_list = zip_ingred_semi_sep(
                mcf_file, drug_strength_dcid, row)
        elif strengths == '250.0MG;12.5MG;75.0MG;250MG BASE,N/A,N/A,N/A; N/A,12.5MG,75MG,50MG':
            row['Strength'] = ";".join(strength_split_on_semi[3:])
            drug_strength_mcf_list = zip_ingred_comma_sep(
                mcf_file, drug_strength_dcid, row)
            drug_strength_mcf = drug_strength_mcf = '\nNode: dcid:bio/' + drug_strength_dcid + '\n'
            drug_strength_mcf = append_all_strengths(
                drug_strength_mcf, strength_split_on_semi[0:3])
            drug_strength_mcf_list[drug_strength_dcid] = drug_strength_mcf
            #print('writeDrugStrength if else: '+ strengths + ' : ' +
            #       active_ingreds + ' : ' + str(row['ApplNo']) + '-' + str(row['ProductNo']))
        elif strength_split_on_semi[0].count(
                ',') == len(ingred_split_on_semi) - 1:
            drug_strength_mcf_list = zip_ingred_comma_sep(
                mcf_file, drug_strength_dcid, row)
            #print('writeDrugStrength if else: '+ strengths + ' : ' +
            #       active_ingreds + ' : ' + str(row['ApplNo']) + '-' + str(row['ProductNo']))
        else:
            drug_strength_mcf_list = initialize_single_drug_strength(
                row, drug_strength_dcid)
            #print('writeDrugStrength if else: '+ strengths + ' : ' +
            #       active_ingreds + ' : ' + str(row['ApplNo']) + '-' + str(row['ProductNo']))

    elif strengths:
        drug_strength_mcf_list = initialize_single_drug_strength(
            row, drug_strength_dcid)
        #print('writeDrugStrength if else: '+ strengths + ' : ' +
        #       active_ingreds + ' : ' + str(row['ApplNo']) + '-' + str(row['ProductNo']))

    for strength_dcid, strength_mcf in drug_strength_mcf_list.items():
        strength_mcf = strength_mcf + 'name: "' + strength_dcid + '"\n'
        strength_mcf = append_drug_strength_properties(row, fda_app_dcid,
                                                       strength_mcf)
        mcf_file.write(strength_mcf)
        drug_mcf = drug_mcf + 'availableStrength: dcid:bio/' + strength_dcid + '\n'

    return drug_mcf


def write_mcf_file(drugs_clean_df, mcf_file_name):
    """Write file with all data mcf.
    """
    (dosage_form_to_dcid, admin_route_to_dcid, appl_type_to_dcid,
     te_code_to_dcid, market_stat_to_dcid) = generate_enums(False)

    mcf_file = open(mcf_file_name, 'w')

    # write FDA Org node
    fda_org_mcf = '''
Node: dcid:USFederalDrugAdministration
name: "USFederalDrugAdministration"
typeOf: schema:Organization
'''
    mcf_file.write(fda_org_mcf)

    chembl_file_drugs = get_chembl_dict_from_file()

    seen_appl_num = set()
    synonym_to_ref_dict = {}

    for index, row in drugs_clean_df.iterrows():

        # get FDAApp dcid used as property for drugStrength
        appl_num = str(row['ApplNo'])
        fda_app_dcid = 'FDA_Application_' + appl_num

        # create FDAApplication node if not seen before
        if appl_num not in seen_appl_num:
            seen_appl_num.add(appl_num)
            write_fda_app_mcf(mcf_file, fda_app_dcid, appl_type_to_dcid, row)

        drug_ref_list = get_drug_ref_list(row, synonym_to_ref_dict,
                                          chembl_file_drugs)
        drug_ref = drug_ref_list[0]

        # create and append info to Drug node
        drug_mcf = initialize_drug_mcf(drug_ref, row, admin_route_to_dcid,
                                       dosage_form_to_dcid)

        # write drugStrengths and ActiveIngredientAmounts, append drugStrength IDs to drug_mcf
        drug_mcf = write_drug_strength_mcf(mcf_file, drug_mcf, drug_ref,
                                           fda_app_dcid, row)

        mcf_file.write(drug_mcf)

        # if multple chembl IDs correspond to the same drug, write the drug info to each ID
        if len(drug_ref_list) > 1:
            for ref in drug_ref_list[1:]:
                new_drug_mcf = replace_ref(drug_mcf, ref)
                mcf_file.write(new_drug_mcf)

    mcf_file.close()


def main():
    """Writes the data from CleanData.csv in mcf format to FDADrugsFinal.mcf .
    """
    drugs_clean_df = pd.read_csv('CleanData.csv')
    drugs_clean_df = drugs_clean_df.fillna('')

    mcf_file_name = 'FDADrugsFinal.mcf'

    write_mcf_file(drugs_clean_df, mcf_file_name)


if __name__ == "__main__":
    main()
