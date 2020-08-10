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
"""Contains functions involving creating enum schema mcf files and loading
enum to dicd dictionaries used in cleaning and writing the data mcf.

Calling create_enums.py from command line will write enum schema to
FDADrugsEnumSchema.mcf
"""
import pandas as pd


def add_to_dict_not_set(dictionary, key, value):
    """Write key value pair to dictionary

    Enum to dcid dictionaries should be 1:1, if multiple values(dcids) attempt
    to be added to the same key(enum), an error message will be printed.
    """
    if not value or pd.isnull(value):
        print("Null value added to dict, key: " + key)
    if key not in dictionary:
        dictionary[key] = value
    else:
        print('tried to overwrite key: ' + key)


def parse_dosage_form_fda(enum_schema_file, df_dict, row):
    """Create a Dosage Form enum from a row of the dosage_forms_fda dataframe

    The enum dcid is loaded into df_dict which stores the enum to dcid
    relationship.
    If enum_schema_file is not None, then the enum is written in mcf format to
    the file
    """
    is_sub_enum = False

    dosage_form_name = str(row['Term']).title()
    code = str(row['Code'])

    dosage_form_name = dosage_form_name.replace(' / ', ', ')
    dosage_form_name = dosage_form_name.replace('/ ', ', ')
    dosage_form_name = dosage_form_name.replace('/', ',')
    dosage_form_name = dosage_form_name.replace('Pellets', 'Pellet')

    split = dosage_form_name.split(',')
    split_length = len(split)
    if split_length > 1:
        is_sub_enum = True
        parent = split[0].replace(' ', '')
        dcid = dosage_form_name.replace(' ', '').replace(',', '')
    else:
        dcid = dosage_form_name.replace(' ', '')

    # add enum dcid to dictionary
    add_to_dict_not_set(df_dict, dosage_form_name, 'DosageForm' + dcid)

    # write mcf to file
    dosage_form_mcf = '\nNode: dcid:DosageForm' + dcid + '\n'
    dosage_form_mcf = dosage_form_mcf + 'typeOf: dcs:DosageFormEnum\n'
    dosage_form_mcf = dosage_form_mcf + 'name: "' + dosage_form_name + '"\n'
    dosage_form_mcf = dosage_form_mcf + 'fdaCode: "' + code + '"\n'
    if is_sub_enum:
        dosage_form_mcf = dosage_form_mcf + 'specializationOf: dcs:DosageForm' + parent + '\n'

    if enum_schema_file:
        enum_schema_file.write(dosage_form_mcf)


def add_custom_dosage_form_enums(enum_schema_file, dosage_form_enums):
    """Create custom Dosage Form enums that appear in Products.txt that are not
    in FDADosageForms.csv

    The enum dcid is loaded into dosage_form_enums which stores the enum to dcid
    relationship.
    If enum_schema_file is not None, then the enum is written in mcf format to
    the file
    """
    custom_dosage_forms = {
        'Syringe':
            'DosageFormSyringe',
        'Vial':
            'DosageFormVial',
        'Powder, Lyophilized Powder':
            'DosageFormPowderLyophilizedPowder',
        'Solution, Metered':
            'DosageFormSolutionMetered',
        'Suspension, Liposomal':
            'DosageFormSuspensionLiposomal',
        'Suspension, Delayed Release':
            'DosageFormSuspensionDelayedRelease',
        'Oil, Drops':
            'DosageFormOilDrops',
        'Tablet, Dispersible':
            'DosageFormTabletDispersible',
        'Gel, Augmented':
            'DosageFormGelAugmented',
        'For Suspension, Delayed Release':
            'DosageFormForSuspensionDelayedRelease',
        'Injection, Extended Release':
            'DosageFormInjectionExtendedRelease',
        'System, Extended Release':
            'DosageFormSystemExtendedRelease',
        'Powder, Extended Release':
            'DosageFormPowderExtendedRelease',
        'Tablet, Orally Disintegrating, Extended Release':
            'DosageFormTabletOrallyDisintegratingExtendedRelease',
        'Foam':
            'DosageFormFoam',
        'Solution, Extended Release':
            'DosageFormSolutionExtendedRelease',
        'Bar':
            'DosageFormBar',
        'Fiber':
            'DosageFormFiber',
        'Gum':
            'DosageFormGum',
        'Injectable':
            'DosageFormInjectable',
    }

    dosage_form_enums.update(custom_dosage_forms)

    if enum_schema_file:
        for dosage_form in custom_dosage_forms:
            is_sub_enum = False
            split = dosage_form.split(',')
            split_length = len(split)
            if split_length > 1:
                is_sub_enum = True
                parent = split[0].replace(' ', '')

            mcf = '\nNode: dcid:' + custom_dosage_forms[dosage_form] + '\n'
            mcf = mcf + 'typeOf: dcs:DosageFormEnum\n'
            mcf = mcf + 'name: "' + dosage_form + '"\n'
            if is_sub_enum:
                mcf = mcf + 'specializationOf: dcs:DosageForm' + parent + '\n'
            enum_schema_file.write(mcf)


def parse_admin_route_fda(enum_schema_file, ar_dict, row):
    """Create an Administration Route enum from a row of the admin_route_fda
    dataframe

    The enum dcid is loaded into ar_dict which stores the enum to dcid
    relationship.
    If enum_schema_file is not None, then the enum is written in mcf format to
    the file
    """
    special_routes = {
        'INTRACORONAL, DENTAL': 'IntraCoronalDental',
        'AURICULAR (OTIC)': 'Auricular',
        'RESPIRATORY (INHALATION)': 'Respiratory'
    }

    name = str(row['NAME'])
    description = str(row['DEFINITION'])
    short_name = str(row['SHORT NAME'])
    fda_code = str(row['FDA CODE'])
    nci_code = str(row['NCI CONCEPT ID'])

    if name in special_routes:
        dcid = special_routes.get(name)
    else:
        dcid = name.title().replace(' ', '')

    name = name.title()

    # add enum to dictionary
    add_to_dict_not_set(ar_dict, name, 'AdministrationRoute' + dcid)

    # create and write mcf
    if enum_schema_file:
        admin_route_mcf = '\nNode: dcid:AdministrationRoute' + dcid.replace(
            '-', '') + '\n'
        admin_route_mcf = admin_route_mcf + 'typeOf: dcs:AdministrationRouteEnum\n'
        admin_route_mcf = admin_route_mcf + 'name: "' + name + '"\n'
        admin_route_mcf = admin_route_mcf + 'fdaCode: "' + fda_code + '"\n'
        admin_route_mcf = admin_route_mcf + 'nciConceptCode: "' + nci_code + '"\n'
        admin_route_mcf = admin_route_mcf + 'description: "' + description + '"\n'
        admin_route_mcf = admin_route_mcf + 'fdaShortName: "' + short_name + '"\n'
        admin_route_mcf = (
            admin_route_mcf +
            'descriptionURL: "https://www.fda.gov/drugs/data-standards-manual-monographs/route-administration"\n'
        )
        enum_schema_file.write(admin_route_mcf)


def add_custom_admin_route_enums(enum_schema_file, admin_route_enums):
    """Create custom Administration Route enums that appear in Products.txt
    that are not in FDADosageForms.csv

    The enum dcid is loaded into admin_route_enums which stores the enum to dcid
    relationship.
    If enum_schema_file is not None, then the enum is written in mcf format to
    the file
    """
    custom_admin_routes = {
        'Injection': 'AdministrationRouteInjection',
        'Implantation': 'AdministrationRouteImplantation',
        'Intra-Anal': 'AdministrationRouteIntraAnal',
        'Pyelocalyceal': 'AdministrationRoutePyelocalyceal',
        'Intracranial': 'AdministrationRouteIntraCranial',
        'Intratracheal': 'AdministrationRouteIntraTracheal',
        'For Rx Compounding': 'AdministrationRouteForRxCompounding',
        'Perfusion, Biliary': 'AdministrationRoutePerfusionBiliary',
        'Intracoronal, Dental': 'AdministrationRouteIntraCoronalDental',
        'PerfusionCardiac': 'AdministrationRoutePerfusionCardiac',
    }

    # add custom enums to dictionary
    admin_route_enums.update(custom_admin_routes)

    # write enum mcfs to file
    if enum_schema_file:
        for admin_route in custom_admin_routes:
            admin_route_mcf = '\nNode: dcid:' + custom_admin_routes[
                admin_route] + '\n'
            admin_route_mcf = admin_route_mcf + 'typeOf: dcs:AdministrationRouteEnum\n'
            admin_route_mcf = admin_route_mcf + 'name: "' + custom_admin_routes[
                admin_route] + '"\n'
            enum_schema_file.write(admin_route_mcf)


def create_te_code_enums(enum_schema_file, dcid_dict):
    """Create Therapeutic Equivalence enums that appear in TE.txt

    The enum dcid is loaded into dcid_dict which stores the enum to dcid
    relationship.
    If enum_schema_file is not None, then the enum is written in mcf format to
    the file
    """

    # descriptions for each enum are from the fda website, see line 282 for URL
    te_code_to_description = {
        'AA':
            'Products in conventional dosage forms not presenting bioequivalence problems. Considered to be therapeutically equivalent to other pharmaceutically equivalent products, i.e., drug products for which there are no known or suspected bioequivalence problems.',
        'AB':
            'Multisource drug products listed under the same heading (i.e., identical active ingredients(s), dosage form, and route(s) of administration) and having the same strength generally will be coded AB if data and information are submitted demonstrating bioequivalence.  Drugs coded as AB under a heading are considered therapeutically equivalent only to other drugs coded as AB under that heading.',
        'AB1':
            'Drugs coded with AB1 under a heading (specified active ingredients(s), dosage form, and route(s) of administration) are considered therapeutically equivalent only to other drugs also coded with AB1 under the same heading. The generic drug products bioequivalent to Adalat® CC have been assigned a rating of AB1.',
        'AB2':
            'Drugs coded with AB2 under a heading (specified active ingredients(s), dosage form, and route(s) of administration) are considered therapeutically equivalent only to other drugs also coded with AB2 under the same heading. The generic drug products bioequivalent to Procardia XL® have been assigned a rating of AB2.',
        'AB3':
            'Drugs coded with AB3 under a heading (specified active ingredients(s), dosage form, and route(s) of administration) are considered therapeutically equivalent only to other drugs also coded with AB3 under the same heading.',
        'AB4':
            'Drugs coded with AB4 under a heading (specified active ingredients(s), dosage form, and route(s) of administration) are considered therapeutically equivalent only to other drugs also coded with AB4 under the same heading.',
        'AN':
            'Solutions and powders for aerosolization. Considered to be therapeutically equivalent to other pharmaceutically equivalent products, i.e., drug products for which there are no known or suspected bioequivalence problems.',
        'AO':
            'Injectable oil solutions. Considered to be therapeutically equivalent to other pharmaceutically equivalent products, i.e., drug products for which there are no known or suspected bioequivalence problems.',
        'AP':
            'Injectable aqueous solutions and, in certain instances, intravenous non-aqueous solutions. Considered to be therapeutically equivalent to other pharmaceutically equivalent products, i.e., drug products for which there are no known or suspected bioequivalence problems.',
        'AP1':
            'Considered to be therapeutically equivalent to other drugs also coded with AP1.',
        'AP2':
            'Considered to be therapeutically equivalent to other drugs also coded with AP2.',
        'AT':
            'Topical products. Considered to be therapeutically equivalent to other pharmaceutically equivalent products, i.e., drug products for which there are no known or suspected bioequivalence problems.',
        'AT1':
            'Considered to be therapeutically equivalent to other drugs also coded with AT1.',
        'AT2':
            'Considered to be therapeutically equivalent to other drugs also coded with AT2.',
        'BC':
            'Extended-release dosage forms (capsules, injectables and tablets). Considered not to be therapeutically equivalent to other pharmaceutically equivalent products.',
        'BD':
            'Active ingredients and dosage forms with documented bioequivalence problems. Considered not to be therapeutically equivalent to other pharmaceutically equivalent products.',
        'BE':
            'Delayed‑release oral dosage forms. Considered not to be therapeutically equivalent to other pharmaceutically equivalent products.',
        'BN':
            'Products in aerosol-nebulizer drug delivery systems. Considered not to be therapeutically equivalent to other pharmaceutically equivalent products.',
        'BP':
            'Active ingredients and dosage forms with potential bioequivalence problems. Considered not to be therapeutically equivalent to other pharmaceutically equivalent products.',
        'BR':
            'Suppositories or enemas that deliver drugs for systemic absorption. Considered not to be therapeutically equivalent to other pharmaceutically equivalent products.',
        'BS':
            'Products having drug standard deficiencies. Considered not to be therapeutically equivalent to other pharmaceutically equivalent products.',
        'BT':
            'Topical products with bioequivalence issues. Considered not to be therapeutically equivalent to other pharmaceutically equivalent products.',
        'BX':
            'Drug products for which the data are insufficient to determine therapeutic equivalence. Considered not to be therapeutically equivalent to other pharmaceutically equivalent products.'
    }

    for te_code in te_code_to_description:
        # append enum to dcid relationship to dcid_dict
        dcid_dict[te_code] = 'TherapeuticEquivalenceCode' + te_code

        #write each enum to file
        if enum_schema_file:
            te_code_mcf = '\nNode: dcid:TherapeuticEquivalenceCode' + te_code + '\n'
            te_code_mcf = te_code_mcf + 'typeOf: TherapeuticEquivalenceCodeEnum\n'
            te_code_mcf = te_code_mcf + 'name: “TherapeuticEquivalenceCode' + te_code + '”\n'
            te_code_mcf = te_code_mcf + 'description: “' + te_code_to_description[
                te_code] + '”\n'
            te_code_mcf = te_code_mcf + 'descriptionURL: “https://www.fda.gov/drugs/development-approval-process-drugs/orange-book-preface#TEC”\n'

            if not te_code.isalpha():
                te_code_mcf = te_code_mcf + 'specializationOf: dcs:TherapeuticEquivalenceCode' + te_code[
                    0:2] + '\n'

            enum_schema_file.write(te_code_mcf)


# beginning of the final enum schema mcf file, contains Class definition for
# each enum type, marketing status enums, and application type enums
ENUMS_HANDWRITTEN = '''
Node: dcid:AdministrationRouteEnum
typeOf: schema:Class
subClassOf: schema:Enumeration
name: "AdministrationRouteEnum"
description: "Administration route enumeration for a drug."

Node: dcid:DosageFormEnum
typeOf: schema:Class
subClassOf: schema:Enumeration
name: "DosageFormEnum"
description: "Dosage form enumeration for a drug."

Node: dcid:TherapeuticEquivalenceCodeEnum
typeOf: schema:Class
subClassOf: schema:Enumeration
name: "TherapeuticEquivalenceCodeEnum"
description: "The therapeutic equivalence (TE) code enumeration as classified by the FDA."

Node: dcid:MarketingStatusEnum
typeOf: schema:Class
subClassOf: schema:Enumeration
name: "MarketingStatusEnum"
description: "The marketing status enumeration as classified by the FDA."

Node: dcid:MarketingStatusPrescription
typeOf: MarketingStatusEnum
name: "MarketingStatusPrescription"
description: "A prescription drug product requires a doctor's authorization to purchase."
descriptionURL: "https://www.fda.gov/drugs/drug-approvals-and-databases/drugsfda-glossary-terms#prescription_drug"

Node: dcid:MarketingStatusOverTheCounter
typeOf: MarketingStatusEnum
name: "MarketingStatusOverTheCounter"
description: "FDA defines OTC drugs as safe and effective for use by the general public without a doctor's prescription."
descriptionURL: "https://www.fda.gov/drugs/drug-approvals-and-databases/drugsfda-glossary-terms#OTC"

Node: dcid:MarketingStatusDiscontinued
typeOf: MarketingStatusEnum
name: "Discontinued"
description: "Products listed in Drugs@FDA as "discontinued" are approved products that have never been marketed, have been discontinued from marketing, are for military use, are for export only, or have had their approvals withdrawn for reasons other than safety or efficacy after being discontinued from marketing."
descriptionURL: "https://www.fda.gov/drugs/drug-approvals-and-databases/drugsfda-glossary-terms#discontinued_drug"

Node: dcid:MarketingStatusNone
typeOf: MarketingStatusEnum
name: "None (Tentative Approval)"
description: "Drug products that have been tentatively approved."
descriptionURL: "https://www.fda.gov/drugs/drug-approvals-and-databases/drugsfda-glossary-terms#M"

Node: dcid:ApplicationTypeEnum
typeOf: schema:Class
subClassOf: schema:Enumeration
name: "ApplicationTypeEnum"
description: "The application type enumeration as classified by the FDA."

Node: dcid:ApplicationTypeNDA
typeOf: ApplicationTypeEnum
name: "New Drug Application (NDA)"
description: "The application must contain data from specific technical viewpoints for review, including chemistry, pharmacology, medical, biopharmaceutics, and statistics."
descriptionURL: "https://www.fda.gov/drugs/drug-approvals-and-databases/drugsfda-glossary-terms#NDA"

Node: dcid:ApplicationTypeANDA
typeOf: ApplicationTypeEnum
name: "Abbreviated New Drug Application (ANDA)"
description: "An Abbreviated New Drug Application (ANDA) contains data that, when submitted to FDA's Center for Drug Evaluation and Research, Office of Generic Drugs, provides for the review and ultimate approval of a generic drug product."
descriptionURL: "https://www.fda.gov/drugs/drug-approvals-and-databases/drugsfda-glossary-terms#ANDA"

Node: dcid:ApplicationTypeBLA
typeOf: ApplicationTypeEnum
name: "Biologic License Application (BLA)"
description: "A biologics license application is a submission that contains specific information on the manufacturing processes, chemistry, pharmacology, clinical pharmacology and the medical affects of the biologic product."
descriptionURL: "https://www.fda.gov/drugs/drug-approvals-and-databases/drugsfda-glossary-terms#BLA"
'''


# SCRIPT: Create Enum Files and associated Dictionaries
def generate_enums(should_write_file):
    """Generates enum schema file and returns loaded enum dictionaries

    If should_write_file is true, then all enums are written to
    FDADrugsEnumSchema.mcf .
    The loaded dictioanries are always returned. These dictionaries are used in
    clean_data.py and write_mcf.py .
    """

    if should_write_file:
        enums_schema_file = open('FDADrugsEnumSchema.mcf', 'w')
        enums_schema_file.write(ENUMS_HANDWRITTEN)
    else:
        enums_schema_file = None

    # create dosage_form enum dict and write dosage_form Enum Schema to file
    dosage_forms_fda = pd.read_csv('raw_data/FDADosageForms.csv')
    dosage_form_to_dcid = {}
    dosage_forms_fda.apply(lambda x: parse_dosage_form_fda(
        enums_schema_file, dosage_form_to_dcid, x),
                           axis=1)
    add_custom_dosage_form_enums(enums_schema_file, dosage_form_to_dcid)

    # create adminROute enum dict and write admin_route Enum Schema to file
    admin_route_to_dcid = {}
    admin_route_fda = pd.read_csv('raw_data/FDAAdminRoutes.csv')
    admin_route_fda.apply(lambda x: parse_admin_route_fda(
        enums_schema_file, admin_route_to_dcid, x),
                          axis=1)
    add_custom_admin_route_enums(enums_schema_file, admin_route_to_dcid)

    # create applType enum dict
    appl_type_to_dcid = {
        'NDA': 'ApplicationTypeNDA',
        'ANDA': 'ApplicationTypeANDA',
        'BLA': 'ApplicationTypeBLA'
    }

    # create TherapueticEquivalence Enum Schema File + dictionary
    te_code_to_dcid = {}
    create_te_code_enums(enums_schema_file, te_code_to_dcid)

    # create Marketing Status Dictionary
    market_stat_to_dcid = {
        '1': 'MarketingStatusPrescription',
        '2': 'MarketingStatusOverTheCounter',
        '3': 'MarketingStatusDiscontinued',
        '4': 'MarketingStatusNone'
    }

    if enums_schema_file:
        enums_schema_file.close()
    return dosage_form_to_dcid, admin_route_to_dcid, appl_type_to_dcid, te_code_to_dcid, market_stat_to_dcid


def main():
    """Calling create_enums.py from command line will write enums to file.
    """
    generate_enums(True)


if __name__ == "__main__":
    main()
