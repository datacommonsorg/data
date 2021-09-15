# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Tests for Drugs @ FDA import ."""
import unittest
import pandas as pd

import clean
import generate_mcf

# constants used for testing create_mcf()
DICT1 = {
    'ActiveIngredient': {
        0: 'HYDROXYAMPHETAMINE HYDROBROMIDE',
        1: 'SULFAPYRIDINE'
    },
    'AdditionalInfo': {
        0: '',
        1: ''
    },
    'AdminRoute': {
        0: 'OPHTHALMIC',
        1: 'ORAL'
    },
    'AdminRouteEnums': {
        0: 'dcid:AdministrationRouteOphthalmic',
        1: 'dcid:AdministrationRouteOral'
    },
    'ApplNo': {
        0: 4,
        1: 159
    },
    'ApplPublicNotes': {
        0: '',
        1: ''
    },
    'ApplType': {
        0: 'NDA',
        1: 'NDA'
    },
    'ApplTypeEnum': {
        0: 'dcid:ApplicationTypeNDA',
        1: 'dcid:ApplicationTypeNDA'
    },
    'CleanActiveIngredient': {
        0: 'Hydroxyamphetamine Hydrobromide',
        1: 'Sulfapyridine'
    },
    'CleanStrength': {
        0: '1%',
        1: '500MG'
    },
    'DosageForm': {
        0: 'SOLUTION/DROPS',
        1: 'TABLET'
    },
    'DosageFormEnums': {
        0: 'dcid:DosageFormSolutionDrops',
        1: 'dcid:DosageFormTablet'
    },
    'DrugCourse': {
        0: '',
        1: ''
    },
    'DrugName': {
        0: 'PAREDRINE',
        1: 'SULFAPYRIDINE'
    },
    'DrugRef': {
        0: 'CHEMBL1200705',
        1: 'CHEMBL700'
    },
    'FinalVolQty': {
        0: '',
        1: ''
    },
    'Form': {
        0: 'SOLUTION/DROPS;OPHTHALMIC',
        1: 'TABLET;ORAL'
    },
    'MarketStatus': {
        0: 'dcid:MarketingStatusDiscontinued',
        1: 'dcid:MarketingStatusDiscontinued'
    },
    'ProductNo': {
        0: 4,
        1: 1
    },
    'ReferenceDrug': {
        0: 0,
        1: 0
    },
    'ReferenceStandard': {
        0: 0.0,
        1: 0.0
    },
    'SingleDose': {
        0: '',
        1: ''
    },
    'SponsorName': {
        0: 'PHARMICS',
        1: 'LILLY'
    },
    'Strength': {
        0: '1%',
        1: '500MG'
    },
    'TECodes': {
        0: '',
        1: ''
    },
    '_merge': {
        0: 'both',
        1: 'both'
    }
}

TEST_MCF1 = """
Node: dcid:USFederalDrugAdministration
name: "USFederalDrugAdministration"
typeOf: schema:Organization

Node: dcid:bio/FDA_Application_4
typeOf: dcid:FDAApplication
name: "FDA_Application_4"
fdaApplicationNumber: "4"
applicationType: dcid:ApplicationTypeNDA
sponsor: "Pharmics"

Node: dcid:bio/Hydroxyamphetamine_Hydrobromide_1_Prct
typeOf: dcid:ActiveIngredientAmount
name: "Hydroxyamphetamine_Hydrobromide_1_Prct"
ingredientAmount: [1 %]
ingredientName: "Hydroxyamphetamine Hydrobromide"

Node: dcid:bio/CHEMBL1200705_Strength-4-4_0
hasActiveIngredientAmount: dcid:bio/Hydroxyamphetamine_Hydrobromide_1_Prct
name: "CHEMBL1200705_Strength-4-4_0"
typeOf: schema:DrugStrength
activeIngredient: "Hydroxyamphetamine Hydrobromide"
marketingStatus: dcid:MarketingStatusDiscontinued
fdaProductID: "4"
submittedFDAApplication: dcid:bio/FDA_Application_4
manufacturer: "Pharmics"

Node: dcid:bio/CHEMBL1200705
typeOf: schema:Drug
name: "CHEMBL1200705"
drugName: "Paredrine"
recognizingAuthority: dcid:USFederalDrugAdministration
isFDAReferenceStandard: False
isAvailableGenerically: False
administrationRoute: dcid:AdministrationRouteOphthalmic
dosageForm: dcid:DosageFormSolutionDrops
activeIngredient: "Hydroxyamphetamine Hydrobromide"
availableStrength: dcid:bio/CHEMBL1200705_Strength-4-4_0

Node: dcid:bio/FDA_Application_159
typeOf: dcid:FDAApplication
name: "FDA_Application_159"
fdaApplicationNumber: "159"
applicationType: dcid:ApplicationTypeNDA
sponsor: "Lilly"

Node: dcid:bio/Sulfapyridine_500_Mg
typeOf: dcid:ActiveIngredientAmount
name: "Sulfapyridine_500_Mg"
ingredientAmount: [500 MG]
ingredientName: "Sulfapyridine"

Node: dcid:bio/CHEMBL700_Strength-159-1_0
hasActiveIngredientAmount: dcid:bio/Sulfapyridine_500_Mg
name: "CHEMBL700_Strength-159-1_0"
typeOf: schema:DrugStrength
activeIngredient: "Sulfapyridine"
marketingStatus: dcid:MarketingStatusDiscontinued
fdaProductID: "1"
submittedFDAApplication: dcid:bio/FDA_Application_159
manufacturer: "Lilly"

Node: dcid:bio/CHEMBL700
typeOf: schema:Drug
name: "CHEMBL700"
drugName: "Sulfapyridine"
recognizingAuthority: dcid:USFederalDrugAdministration
isFDAReferenceStandard: False
isAvailableGenerically: False
administrationRoute: dcid:AdministrationRouteOral
dosageForm: dcid:DosageFormTablet
activeIngredient: "Sulfapyridine"
availableStrength: dcid:bio/CHEMBL700_Strength-159-1_0
"""

DICT2 = {
    'AdditionalInfo': {
        0: '',
        1: ''
    },
    'AdminRouteEnums': {
        0: 'dcid:AdministrationRouteOphthalmic',
        1: 'dcid:AdministrationRouteOral'
    },
    'ApplNo': {
        0: 4,
        1: 159
    },
    'ApplTypeEnum': {
        0: 'dcid:ApplicationTypeNDA',
        1: 'dcid:ApplicationTypeNDA'
    },
    'CleanActiveIngredient': {
        0: 'Ingred_A;Ingred_B',
        1: 'Ingred1;Ingred2'
    },
    'CleanStrength': {
        0: '100MG,200MG;300MG,400MG;500MG,600MG',
        1: '100MG, 200MG, 300MG; 400MG, 500MG, 600MG'
    },
    'DosageFormEnums': {
        0: 'dcid:DosageFormSolutionDrops',
        1: 'dcid:DosageFormTablet'
    },
    'DrugCourse': {
        0: '',
        1: ''
    },
    'DrugName': {
        0: 'PAREDRINE',
        1: 'SULFAPYRIDINE'
    },
    'DrugRef': {
        0: 'CHEMBL1200705',
        1: 'CHEMBL700'
    },
    'FinalVolQty': {
        0: '',
        1: ''
    },
    'MarketStatus': {
        0: 'dcid:MarketingStatusDiscontinued',
        1: 'dcid:MarketingStatusDiscontinued'
    },
    'ProductNo': {
        0: 4,
        1: 1
    },
    'ReferenceDrug': {
        0: 0,
        1: 0
    },
    'ReferenceStandard': {
        0: 0.0,
        1: 0.0
    },
    'SingleDose': {
        0: '',
        1: ''
    },
    'SponsorName': {
        0: 'PHARMICS',
        1: 'LILLY'
    },
    'Strength': {
        0: '1%',
        1: '500MG'
    },
    'TECodes': {
        0: '',
        1: ''
    },
}

TEST_MCF2 = """
Node: dcid:USFederalDrugAdministration
name: "USFederalDrugAdministration"
typeOf: schema:Organization

Node: dcid:bio/FDA_Application_4
typeOf: dcid:FDAApplication
name: "FDA_Application_4"
fdaApplicationNumber: "4"
applicationType: dcid:ApplicationTypeNDA
sponsor: "Pharmics"

Node: dcid:bio/Ingred_A_100_Mg
typeOf: dcid:ActiveIngredientAmount
name: "Ingred_A_100_Mg"
ingredientAmount: [100 MG]
ingredientName: "Ingred_A"

Node: dcid:bio/Ingred_B_200_Mg
typeOf: dcid:ActiveIngredientAmount
name: "Ingred_B_200_Mg"
ingredientAmount: [200 MG]
ingredientName: "Ingred_B"

Node: dcid:bio/CHEMBL1200705_Strength-4-4_0
hasActiveIngredientAmount: dcid:bio/Ingred_A_100_Mg,dcid:bio/Ingred_B_200_Mg
name: "CHEMBL1200705_Strength-4-4_0"
typeOf: schema:DrugStrength
activeIngredient: "Ingred_A","Ingred_B"
marketingStatus: dcid:MarketingStatusDiscontinued
fdaProductID: "4"
submittedFDAApplication: dcid:bio/FDA_Application_4
manufacturer: "Pharmics"

Node: dcid:bio/Ingred_A_300_Mg
typeOf: dcid:ActiveIngredientAmount
name: "Ingred_A_300_Mg"
ingredientAmount: [300 MG]
ingredientName: "Ingred_A"

Node: dcid:bio/Ingred_B_400_Mg
typeOf: dcid:ActiveIngredientAmount
name: "Ingred_B_400_Mg"
ingredientAmount: [400 MG]
ingredientName: "Ingred_B"

Node: dcid:bio/CHEMBL1200705_Strength-4-4_1
hasActiveIngredientAmount: dcid:bio/Ingred_A_300_Mg,dcid:bio/Ingred_B_400_Mg
name: "CHEMBL1200705_Strength-4-4_1"
typeOf: schema:DrugStrength
activeIngredient: "Ingred_A","Ingred_B"
marketingStatus: dcid:MarketingStatusDiscontinued
fdaProductID: "4"
submittedFDAApplication: dcid:bio/FDA_Application_4
manufacturer: "Pharmics"

Node: dcid:bio/Ingred_A_500_Mg
typeOf: dcid:ActiveIngredientAmount
name: "Ingred_A_500_Mg"
ingredientAmount: [500 MG]
ingredientName: "Ingred_A"

Node: dcid:bio/Ingred_B_600_Mg
typeOf: dcid:ActiveIngredientAmount
name: "Ingred_B_600_Mg"
ingredientAmount: [600 MG]
ingredientName: "Ingred_B"

Node: dcid:bio/CHEMBL1200705_Strength-4-4_2
hasActiveIngredientAmount: dcid:bio/Ingred_A_500_Mg,dcid:bio/Ingred_B_600_Mg
name: "CHEMBL1200705_Strength-4-4_2"
typeOf: schema:DrugStrength
activeIngredient: "Ingred_A","Ingred_B"
marketingStatus: dcid:MarketingStatusDiscontinued
fdaProductID: "4"
submittedFDAApplication: dcid:bio/FDA_Application_4
manufacturer: "Pharmics"

Node: dcid:bio/CHEMBL1200705
typeOf: schema:Drug
name: "CHEMBL1200705"
drugName: "Paredrine"
recognizingAuthority: dcid:USFederalDrugAdministration
isFDAReferenceStandard: False
isAvailableGenerically: False
administrationRoute: dcid:AdministrationRouteOphthalmic
dosageForm: dcid:DosageFormSolutionDrops
activeIngredient: "Ingred_A","Ingred_B"
availableStrength: dcid:bio/CHEMBL1200705_Strength-4-4_0,dcid:bio/CHEMBL1200705_Strength-4-4_1,dcid:bio/CHEMBL1200705_Strength-4-4_2

Node: dcid:bio/FDA_Application_159
typeOf: dcid:FDAApplication
name: "FDA_Application_159"
fdaApplicationNumber: "159"
applicationType: dcid:ApplicationTypeNDA
sponsor: "Lilly"

Node: dcid:bio/Ingred1_100_Mg
typeOf: dcid:ActiveIngredientAmount
name: "Ingred1_100_Mg"
ingredientAmount: [100 MG]
ingredientName: "Ingred1"

Node: dcid:bio/Ingred2_400_Mg
typeOf: dcid:ActiveIngredientAmount
name: "Ingred2_400_Mg"
ingredientAmount: [400 MG]
ingredientName: "Ingred2"

Node: dcid:bio/CHEMBL700_Strength-159-1_0
hasActiveIngredientAmount: dcid:bio/Ingred1_100_Mg,dcid:bio/Ingred2_400_Mg
name: "CHEMBL700_Strength-159-1_0"
typeOf: schema:DrugStrength
activeIngredient: "Ingred1","Ingred2"
marketingStatus: dcid:MarketingStatusDiscontinued
fdaProductID: "1"
submittedFDAApplication: dcid:bio/FDA_Application_159
manufacturer: "Lilly"

Node: dcid:bio/Ingred1_200_Mg
typeOf: dcid:ActiveIngredientAmount
name: "Ingred1_200_Mg"
ingredientAmount: [200 MG]
ingredientName: "Ingred1"

Node: dcid:bio/Ingred2_500_Mg
typeOf: dcid:ActiveIngredientAmount
name: "Ingred2_500_Mg"
ingredientAmount: [500 MG]
ingredientName: "Ingred2"

Node: dcid:bio/CHEMBL700_Strength-159-1_1
hasActiveIngredientAmount: dcid:bio/Ingred1_200_Mg,dcid:bio/Ingred2_500_Mg
name: "CHEMBL700_Strength-159-1_1"
typeOf: schema:DrugStrength
activeIngredient: "Ingred1","Ingred2"
marketingStatus: dcid:MarketingStatusDiscontinued
fdaProductID: "1"
submittedFDAApplication: dcid:bio/FDA_Application_159
manufacturer: "Lilly"

Node: dcid:bio/Ingred1_300_Mg
typeOf: dcid:ActiveIngredientAmount
name: "Ingred1_300_Mg"
ingredientAmount: [300 MG]
ingredientName: "Ingred1"

Node: dcid:bio/Ingred2_600_Mg
typeOf: dcid:ActiveIngredientAmount
name: "Ingred2_600_Mg"
ingredientAmount: [600 MG]
ingredientName: "Ingred2"

Node: dcid:bio/CHEMBL700_Strength-159-1_2
hasActiveIngredientAmount: dcid:bio/Ingred1_300_Mg,dcid:bio/Ingred2_600_Mg
name: "CHEMBL700_Strength-159-1_2"
typeOf: schema:DrugStrength
activeIngredient: "Ingred1","Ingred2"
marketingStatus: dcid:MarketingStatusDiscontinued
fdaProductID: "1"
submittedFDAApplication: dcid:bio/FDA_Application_159
manufacturer: "Lilly"

Node: dcid:bio/CHEMBL700
typeOf: schema:Drug
name: "CHEMBL700"
drugName: "Sulfapyridine"
recognizingAuthority: dcid:USFederalDrugAdministration
isFDAReferenceStandard: False
isAvailableGenerically: False
administrationRoute: dcid:AdministrationRouteOral
dosageForm: dcid:DosageFormTablet
activeIngredient: "Ingred1","Ingred2"
availableStrength: dcid:bio/CHEMBL700_Strength-159-1_0,dcid:bio/CHEMBL700_Strength-159-1_1,dcid:bio/CHEMBL700_Strength-159-1_2
"""

DICT3 = {
    'AdditionalInfo': {
        0: 'Sentence with additional info here.'
    },
    'AdminRouteEnums': {
        0: 'dcid:AdministrationRouteOphthalmic'
    },
    'ApplNo': {
        0: 4
    },
    'ApplTypeEnum': {
        0: 'dcid:ApplicationTypeBLA'
    },
    'CleanActiveIngredient': {
        0: 'Ingred_A'
    },
    'CleanStrength': {
        0: '100MG'
    },
    'DosageFormEnums': {
        0: 'dcid:DosageFormSolutionDrops'
    },
    'DrugCourse': {
        0: '[28 Days]'
    },
    'DrugName': {
        0: 'PAREDRINE'
    },
    'DrugRef': {
        0: 'CHEMBL1200705'
    },
    'FinalVolQty': {
        0: '[1000 ML]'
    },
    'MarketStatus': {
        0: 'dcid:MarketingStatusDiscontinued'
    },
    'ProductNo': {
        0: 4,
    },
    'ReferenceDrug': {
        0: 1
    },
    'ReferenceStandard': {
        0: 1
    },
    'SingleDose': {
        0: 'True'
    },
    'SponsorName': {
        0: 'PHARMICS'
    },
    'TECodes': {
        0: 'dcid:TherapeuticEquivalenceCodeAP'
    },
}

TEST_MCF3 = """
Node: dcid:USFederalDrugAdministration
name: "USFederalDrugAdministration"
typeOf: schema:Organization

Node: dcid:bio/FDA_Application_4
typeOf: dcid:FDAApplication
name: "FDA_Application_4"
fdaApplicationNumber: "4"
applicationType: dcid:ApplicationTypeBLA
sponsor: "Pharmics"

Node: dcid:bio/Ingred_A_100_Mg
typeOf: dcid:ActiveIngredientAmount
name: "Ingred_A_100_Mg"
ingredientAmount: [100 MG]
ingredientName: "Ingred_A"

Node: dcid:bio/CHEMBL1200705_Strength-4-4_0
hasActiveIngredientAmount: dcid:bio/Ingred_A_100_Mg
name: "CHEMBL1200705_Strength-4-4_0"
typeOf: schema:DrugStrength
activeIngredient: "Ingred_A"
finalReconstitutedSolutionVolume: [1000 ML]
therapeuticEquivalenceCode: dcid:TherapeuticEquivalenceCodeAP
marketingStatus: dcid:MarketingStatusDiscontinued
drugCourse: [28 Days]
fdaProductID: "4"
submittedFDAApplication: dcid:bio/FDA_Application_4
singleDose: True
manufacturer: "Pharmics"

Node: dcid:bio/CHEMBL1200705
typeOf: schema:Drug
name: "CHEMBL1200705"
drugName: "Paredrine"
recognizingAuthority: dcid:USFederalDrugAdministration
additionalDrugInformation: "Sentence with additional info here."
isFDAReferenceStandard: True
isAvailableGenerically: True
administrationRoute: dcid:AdministrationRouteOphthalmic
dosageForm: dcid:DosageFormSolutionDrops
activeIngredient: "Ingred_A"
availableStrength: dcid:bio/CHEMBL1200705_Strength-4-4_0
"""


class TestSuite(unittest.TestCase):
    def test_reformat_paren_with_semi(self):
        test_str = '700 UNITS/10ML; 300 UNITS/10ML (70 UNITS/ML; 30 UNITS/ML)'
        ref_str = '700 UNITS/10ML(70 UNITS/ML);300 UNITS/10ML(30 UNITS/ML)'
        self.assertEqual(clean.reformat_paren_with_semi(test_str), ref_str)

    def test_expand_strength(self):
        row = {
            'Strength':
            '2%;70% (100ML)**Indicated for use and comarketed with Interferon ALFA-2B, Recombinant (INTRON A), as Rebetron Combination Therapy',
        }
        expanded = {
            'Strength':
            '2%;70% (100ML)**Indicated for use and comarketed with Interferon ALFA-2B, Recombinant (INTRON A), as Rebetron Combination Therapy',
            'AdditionalInfo':
            'Indicated for use and comarketed with Interferon ALFA-2B, Recombinant (INTRON A), as Rebetron Combination Therapy. ',
            'FinalVolQty': '[100 ML]',
            'CleanStrength': '2%;70%'
        }
        self.assertEqual(clean.expand_strength(row), expanded)

        row = {'Strength': '15%(150GM/1000ML)(1.5ML)'}
        expanded = {
            'Strength': '15%(150GM/1000ML)(1.5ML)',
            'CleanStrength': '15%(150GM/1000ML)',
            'FinalVolQty': '[1.5 ML]',
        }
        self.assertEqual(clean.expand_strength(row), expanded)

        row = {
            'Strength':
            '700 UNITS/10ML; 300 UNITS/10ML (70 UNITS/ML; 30 UNITS/ML)'
        }
        expanded = {
            'Strength':
            '700 UNITS/10ML; 300 UNITS/10ML (70 UNITS/ML; 30 UNITS/ML)',
            'CleanStrength':
            '700 UNITS/10ML(70 UNITS/ML);300 UNITS/10ML(30 UNITS/ML)'
        }
        self.assertEqual(clean.expand_strength(row), expanded)

    def test_expand_dosage_form(self):
        row = {
            'DosageForm':
            'Aerosol, Foam,Capsule, Coated, Extended Release,Injection, Powder, For Suspension, Extended Release,Injection, Powder, Lyophilized, For Suspension, Extended Release'
        }
        expanded = {
            'DosageForm':
            'Aerosol, Foam,Capsule, Coated, Extended Release,Injection, Powder, For Suspension, Extended Release,Injection, Powder, Lyophilized, For Suspension, Extended Release',
            'DosageFormEnums':
            'dcid:DosageFormInjectionPowderLyophilizedForSuspensionExtendedRelease,dcid:DosageFormInjectionPowderForSuspensionExtendedRelease,dcid:DosageFormCapsuleCoatedExtendedRelease,dcid:DosageFormAerosolFoam'
        }
        self.assertEqual(clean.expand_dosage_form(row), expanded)

    def test_expand_admin_route(self):
        row = {'AdminRoute': 'ORAL-28'}
        expanded = {
            'AdminRoute': 'ORAL-28',
            'DrugCourse': '[28 Days]',
            'AdminRouteEnums': 'dcid:AdministrationRouteOral'
        }
        self.assertEqual(clean.expand_admin_route(row), expanded)

        row = {'AdminRoute': 'MULTIDOSE'}
        expanded = {
            'SingleDose': 'False',
            'AdminRoute': 'MULTIDOSE',
            'AdminRouteEnums': ''
        }
        self.assertEqual(clean.expand_admin_route(row), expanded)

        row = {
            'AdminRoute': 'SUBCUTANEOUS LYOPHILIZED POWER, ORAL',
        }
        expanded = {
            'AdminRoute':
            'SUBCUTANEOUS LYOPHILIZED POWER, ORAL',
            'DosageFormEnums':
            'dcid:DosageFormPowderLyophilizedPowder',
            'AdminRouteEnums':
            'dcid:AdministrationRouteSubcutaneous,dcid:AdministrationRouteOral'
        }
        self.assertEqual(clean.expand_admin_route(row), expanded)

    def test_create_mcf(self):
        # test first two lines of clean_data.csv
        drug_df = pd.DataFrame.from_dict(DICT1)
        generate_mcf.create_mcf('test.mcf', drug_df)

        with open('test.mcf', 'r') as mcf_file:
            mcf = mcf_file.read()

        self.assertEqual(mcf, TEST_MCF1)

        # made up data to test zip_ingred_semi_sep and zip_ingred_comma_sep
        drug_df = pd.DataFrame.from_dict(DICT2)
        generate_mcf.create_mcf('test2.mcf', drug_df)

        with open('test2.mcf', 'r') as mcf_file:
            mcf = mcf_file.read()

        self.assertEqual(mcf, TEST_MCF2)

        # made up data to test each possible property
        drug_df = pd.DataFrame.from_dict(DICT3)
        generate_mcf.create_mcf('test3.mcf', drug_df)

        with open('test3.mcf', 'r') as mcf_file:
            mcf = mcf_file.read()

        self.assertEqual(mcf, TEST_MCF3)


unittest.main(argv=['first-arg-is-ignored'], exit=False)
