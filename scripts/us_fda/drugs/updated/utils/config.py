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
Contains MCF template strings, enum dictionaries, and other constants related to
cleaning and reading the data files.
"""
FDA_APP_TEMPLATE = '''
Node: {fda_app_dcid}
typeOf: dcid:FDAApplication
name: "{name}"
fdaApplicationNumber: "{appl_num}"
applicationType: {appl_type_enums}
sponsor: "{sponsor_name}"
'''

ACTIVE_INGRED_TEMPLATE = '''
Node: {active_ingred_dcid}
typeOf: dcid:ActiveIngredientAmount
name: "{name}"
ingredientAmount: {ingred_amount_qty}
ingredientName: "{ingred_name}"
'''

STRENGTH_TEMPLATE = '''
Node: {strength_dcid}
hasActiveIngredientAmount: {active_ingred_dcids}
name: "{name}"
typeOf: schema:DrugStrength
activeIngredient: "{ingred_names}"
finalReconstitutedSolutionVolume: {final_vol_qty}
therapeuticEquivalenceCode: {te_enums}
marketingStatus: {ms_enums}
drugCourse: {course_qty}
fdaProductID: "{fda_prod_no}"
hasStrength: {strength_qty}
submittedFDAApplication: {fda_app_dcid}
singleDose: {is_single_dose}
manufacturer: "{sponsor}"
'''

DRUG_TEMPLATE = '''
Node: dcid:{drug_ref}
typeOf: schema:Drug
name: "{name}"
drugName: "{synonyms}"
recognizingAuthority: dcid:USFederalDrugAdministration
additionalDrugInformation: "{additional_info}"
isFDAReferenceStandard: {is_ref_std}
isAvailableGenerically: {is_available_generically}
administrationRoute: {admin_route_enum}
dosageForm: {dosage_form_enum}
activeIngredient: "{ingred_names}"
availableStrength: {strength_dcids}
'''

FDA_NODE = '''
Node: dcid:USFederalDrugAdministration
name: "USFederalDrugAdministration"
typeOf: schema:Organization
'''

APPLICATION_TYPE_ENUMS = {
    'NDA': 'ApplicationTypeNDA',
    'ANDA': 'ApplicationTypeANDA',
    'BLA': 'ApplicationTypeBLA',
}

TE_CODE_ENUMS = {
    'AA': 'TherapeuticEquivalenceCodeAA',
    'AB': 'TherapeuticEquivalenceCodeAB',
    'AB1': 'TherapeuticEquivalenceCodeAB1',
    'AB2': 'TherapeuticEquivalenceCodeAB2',
    'AB3': 'TherapeuticEquivalenceCodeAB3',
    'AB4': 'TherapeuticEquivalenceCodeAB4',
    'AN': 'TherapeuticEquivalenceCodeAN',
    'AO': 'TherapeuticEquivalenceCodeAO',
    'AP': 'TherapeuticEquivalenceCodeAP',
    'AP1': 'TherapeuticEquivalenceCodeAP1',
    'AP2': 'TherapeuticEquivalenceCodeAP2',
    'AT': 'TherapeuticEquivalenceCodeAT',
    'AT1': 'TherapeuticEquivalenceCodeAT1',
    'AT2': 'TherapeuticEquivalenceCodeAT2',
    'AT3': 'TherapeuticEquivalenceCodeAT3',
    'BC': 'TherapeuticEquivalenceCodeBC',
    'BD': 'TherapeuticEquivalenceCodeBD',
    'BE': 'TherapeuticEquivalenceCodeBE',
    'BN': 'TherapeuticEquivalenceCodeBN',
    'BP': 'TherapeuticEquivalenceCodeBP',
    'BR': 'TherapeuticEquivalenceCodeBR',
    'BS': 'TherapeuticEquivalenceCodeBS',
    'BT': 'TherapeuticEquivalenceCodeBT',
    'BX': 'TherapeuticEquivalenceCodeBX',
}
MARKETING_STATUS_ENUMS = {
    '1': 'MarketingStatusPrescription',
    '2': 'MarketingStatusOverTheCounter',
    '3': 'MarketingStatusDiscontinued',
    '4': 'MarketingStatusNone',
}

DOSAGE_FORM_ENUMS = {
    'Aerosol':
        'DosageFormAerosol',
    'Aerosol, Foam':
        'DosageFormAerosolFoam',
    'Aerosol, Metered':
        'DosageFormAerosolMetered',
    'Aerosol, Powder':
        'DosageFormAerosolPowder',
    'Aerosol, Spray':
        'DosageFormAerosolSpray',
    'Bar, Chewable':
        'DosageFormBarChewable',
    'Bead':
        'DosageFormBead',
    'Capsule':
        'DosageFormCapsule',
    'Capsule, Coated':
        'DosageFormCapsuleCoated',
    'Capsule, Coated Pellet':
        'DosageFormCapsuleCoatedPellet',
    'Capsule, Coated, Extended Release':
        'DosageFormCapsuleCoatedExtendedRelease',
    'Capsule, Delayed Release':
        'DosageFormCapsuleDelayedRelease',
    'Capsule, Delayed Release Pellet':
        'DosageFormCapsuleDelayedReleasePellet',
    'Capsule, Extended Release':
        'DosageFormCapsuleExtendedRelease',
    'Capsule, Film Coated, Extended Release':
        'DosageFormCapsuleFilmCoatedExtendedRelease',
    'Capsule, Gelatin Coated':
        'DosageFormCapsuleGelatinCoated',
    'Capsule, Liquid Filled':
        'DosageFormCapsuleLiquidFilled',
    'Cellular Sheet':
        'DosageFormCellularSheet',
    'Chewable Gel':
        'DosageFormChewableGel',
    'Cloth':
        'DosageFormCloth',
    'Concentrate':
        'DosageFormConcentrate',
    'Cream':
        'DosageFormCream',
    'Cream, Augmented':
        'DosageFormCreamAugmented',
    'Crystal':
        'DosageFormCrystal',
    'Disc':
        'DosageFormDisc',
    'Douche':
        'DosageFormDouche',
    'Dressing':
        'DosageFormDressing',
    'Elixir':
        'DosageFormElixir',
    'Emulsion':
        'DosageFormEmulsion',
    'Enema':
        'DosageFormEnema',
    'Extract':
        'DosageFormExtract',
    'Fiber, Extended Release':
        'DosageFormFiberExtendedRelease',
    'Film':
        'DosageFormFilm',
    'Film, Extended Release':
        'DosageFormFilmExtendedRelease',
    'Film, Soluble':
        'DosageFormFilmSoluble',
    'For Solution':
        'DosageFormForSolution',
    'For Suspension':
        'DosageFormForSuspension',
    'For Suspension, Extended Release':
        'DosageFormForSuspensionExtendedRelease',
    'Gas':
        'DosageFormGas',
    'Gel':
        'DosageFormGel',
    'Gel, Dentifrice':
        'DosageFormGelDentifrice',
    'Gel, Metered':
        'DosageFormGelMetered',
    'Globule':
        'DosageFormGlobule',
    'Granule':
        'DosageFormGranule',
    'Granule, Delayed Release':
        'DosageFormGranuleDelayedRelease',
    'Granule, Effervescent':
        'DosageFormGranuleEffervescent',
    'Granule, For Solution':
        'DosageFormGranuleForSolution',
    'Granule, For Suspension':
        'DosageFormGranuleForSuspension',
    'Granule, For Suspension, Extended Release':
        'DosageFormGranuleForSuspensionExtendedRelease',
    'Gum, Chewing':
        'DosageFormGumChewing',
    'Implant':
        'DosageFormImplant',
    'Inhalant':
        'DosageFormInhalant',
    'Injectable Foam':
        'DosageFormInjectableFoam',
    'Injectable, Liposomal':
        'DosageFormInjectableLiposomal',
    'Injection':
        'DosageFormInjection',
    'Injection, Emulsion':
        'DosageFormInjectionEmulsion',
    'Injection, Lipid Complex':
        'DosageFormInjectionLipidComplex',
    'Injection, Powder, For Solution':
        'DosageFormInjectionPowderForSolution',
    'Injection, Powder, For Suspension':
        'DosageFormInjectionPowderForSuspension',
    'Injection, Powder, For Suspension, Extended Release':
        'DosageFormInjectionPowderForSuspensionExtendedRelease',
    'Injection, Powder, Lyophilized, For Liposomal Suspension':
        'DosageFormInjectionPowderLyophilizedForLiposomalSuspension',
    'Injection, Powder, Lyophilized, For Solution':
        'DosageFormInjectionPowderLyophilizedForSolution',
    'Injection, Powder, Lyophilized, For Suspension':
        'DosageFormInjectionPowderLyophilizedForSuspension',
    'Injection, Powder, Lyophilized, For Suspension, Extended Release':
        'DosageFormInjectionPowderLyophilizedForSuspensionExtendedRelease',
    'Injection, Solution':
        'DosageFormInjectionSolution',
    'Injection, Solution, Concentrate':
        'DosageFormInjectionSolutionConcentrate',
    'Injection, Suspension':
        'DosageFormInjectionSuspension',
    'Injection, Suspension, Extended Release':
        'DosageFormInjectionSuspensionExtendedRelease',
    'Injection, Suspension, Liposomal':
        'DosageFormInjectionSuspensionLiposomal',
    'Injection, Suspension, Sonicated':
        'DosageFormInjectionSuspensionSonicated',
    'Insert':
        'DosageFormInsert',
    'Insert, Extended Release':
        'DosageFormInsertExtendedRelease',
    'Intrauterine Device':
        'DosageFormIntrauterineDevice',
    'Irrigant':
        'DosageFormIrrigant',
    'Jelly':
        'DosageFormJelly',
    'Kit':
        'DosageFormKit',
    'Liniment':
        'DosageFormLiniment',
    'Lipstick':
        'DosageFormLipstick',
    'Liquid':
        'DosageFormLiquid',
    'Liquid, Extended Release':
        'DosageFormLiquidExtendedRelease',
    'Lotion':
        'DosageFormLotion',
    'Lotion, Augmented':
        'DosageFormLotionAugmented',
    'Lotion, Shampoo':
        'DosageFormLotionShampoo',
    'Lozenge':
        'DosageFormLozenge',
    'Mouthwash':
        'DosageFormMouthwash',
    'Not Applicable':
        'DosageFormNotApplicable',
    'Oil':
        'DosageFormOil',
    'Ointment':
        'DosageFormOintment',
    'Ointment, Augmented':
        'DosageFormOintmentAugmented',
    'Paste':
        'DosageFormPaste',
    'Paste, Dentifrice':
        'DosageFormPasteDentifrice',
    'Pastille':
        'DosageFormPastille',
    'Patch':
        'DosageFormPatch',
    'Patch, Extended Release':
        'DosageFormPatchExtendedRelease',
    'Patch, Extended Release, Electrically Controlled':
        'DosageFormPatchExtendedReleaseElectricallyControlled',
    'Pellet':
        'DosageFormPellet',
    'Pellet, Implantable':
        'DosageFormPelletImplantable',
    'Pellet, Coated, Extended Release':
        'DosageFormPelletCoatedExtendedRelease',
    'Pill':
        'DosageFormPill',
    'Plaster':
        'DosageFormPlaster',
    'Poultice':
        'DosageFormPoultice',
    'Powder':
        'DosageFormPowder',
    'Powder, Dentifrice':
        'DosageFormPowderDentifrice',
    'Powder, For Solution':
        'DosageFormPowderForSolution',
    'Powder, For Suspension':
        'DosageFormPowderForSuspension',
    'Powder, Metered':
        'DosageFormPowderMetered',
    'Ring':
        'DosageFormRing',
    'Rinse':
        'DosageFormRinse',
    'Salve':
        'DosageFormSalve',
    'Shampoo':
        'DosageFormShampoo',
    'Shampoo, Suspension':
        'DosageFormShampooSuspension',
    'Soap':
        'DosageFormSoap',
    'Solution':
        'DosageFormSolution',
    'Solution, Concentrate':
        'DosageFormSolutionConcentrate',
    'Solution, For Slush':
        'DosageFormSolutionForSlush',
    'Solution, Gel Forming, Drops':
        'DosageFormSolutionGelFormingDrops',
    'Solution, Gel Forming, Extended Release':
        'DosageFormSolutionGelFormingExtendedRelease',
    'Solution, Drops':
        'DosageFormSolutionDrops',
    'Sponge':
        'DosageFormSponge',
    'Spray':
        'DosageFormSpray',
    'Spray, Metered':
        'DosageFormSprayMetered',
    'Spray, Suspension':
        'DosageFormSpraySuspension',
    'Stick':
        'DosageFormStick',
    'Strip':
        'DosageFormStrip',
    'Suppository':
        'DosageFormSuppository',
    'Suppository, Extended Release':
        'DosageFormSuppositoryExtendedRelease',
    'Suspension':
        'DosageFormSuspension',
    'Suspension, Extended Release':
        'DosageFormSuspensionExtendedRelease',
    'Suspension, Drops':
        'DosageFormSuspensionDrops',
    'Swab':
        'DosageFormSwab',
    'Syrup':
        'DosageFormSyrup',
    'System':
        'DosageFormSystem',
    'Tablet':
        'DosageFormTablet',
    'Tablet, Chewable':
        'DosageFormTabletChewable',
    'Tablet, Chewable, Extended Release':
        'DosageFormTabletChewableExtendedRelease',
    'Tablet, Coated':
        'DosageFormTabletCoated',
    'Tablet, Coated Particles':
        'DosageFormTabletCoatedParticles',
    'Tablet, Delayed Release':
        'DosageFormTabletDelayedRelease',
    'Tablet, Delayed Release Particles':
        'DosageFormTabletDelayedReleaseParticles',
    'Tablet, Effervescent':
        'DosageFormTabletEffervescent',
    'Tablet, Extended Release':
        'DosageFormTabletExtendedRelease',
    'Tablet, Film Coated':
        'DosageFormTabletFilmCoated',
    'Tablet, Film Coated, Extended Release':
        'DosageFormTabletFilmCoatedExtendedRelease',
    'Tablet, For Solution':
        'DosageFormTabletForSolution',
    'Tablet, For Suspension':
        'DosageFormTabletForSuspension',
    'Tablet, Multilayer':
        'DosageFormTabletMultilayer',
    'Tablet, Multilayer, Extended Release':
        'DosageFormTabletMultilayerExtendedRelease',
    'Tablet, Orally Disintegrating':
        'DosageFormTabletOrallyDisintegrating',
    'Tablet, Orally Disintegrating, Delayed Release':
        'DosageFormTabletOrallyDisintegratingDelayedRelease',
    'Tablet, Soluble':
        'DosageFormTabletSoluble',
    'Tablet, Sugar Coated':
        'DosageFormTabletSugarCoated',
    'Tablet With Sensor':
        'DosageFormTabletWithSensor',
    'Tampon':
        'DosageFormTampon',
    'Tape':
        'DosageFormTape',
    'Tincture':
        'DosageFormTincture',
    'Troche':
        'DosageFormTroche',
    'Wafer':
        'DosageFormWafer',
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
        'DosageFormSuspensionDelayedRelease',
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
        'DosageFormInjectable'
}

ADMIN_ROUTE_ENUMS = {
    'Auricular (Otic)':
        'AdministrationRouteAuricular',
    'Buccal':
        'AdministrationRouteBuccal',
    'Conjunctival':
        'AdministrationRouteConjunctival',
    'Cutaneous':
        'AdministrationRouteCutaneous',
    'Dental':
        'AdministrationRouteDental',
    'Electro-Osmosis':
        'AdministrationRouteElectro-Osmosis',
    'Endocervical':
        'AdministrationRouteEndocervical',
    'Endosinusial':
        'AdministrationRouteEndosinusial',
    'Endotracheal':
        'AdministrationRouteEndotracheal',
    'Enteral':
        'AdministrationRouteEnteral',
    'Epidural':
        'AdministrationRouteEpidural',
    'Extra‑Amniotic':
        'AdministrationRouteExtra‑Amniotic',
    'Extracorporeal':
        'AdministrationRouteExtracorporeal',
    'Hemodialysis':
        'AdministrationRouteHemodialysis',
    'Infiltration':
        'AdministrationRouteInfiltration',
    'Interstitial':
        'AdministrationRouteInterstitial',
    'Intra-Abdominal':
        'AdministrationRouteIntra-Abdominal',
    'Intra-Amniotic':
        'AdministrationRouteIntra-Amniotic',
    'Intra-Arterial':
        'AdministrationRouteIntra-Arterial',
    'Intra-Articular':
        'AdministrationRouteIntra-Articular',
    'Intrabiliary':
        'AdministrationRouteIntrabiliary',
    'Intrabronchial':
        'AdministrationRouteIntrabronchial',
    'Intrabursal':
        'AdministrationRouteIntrabursal',
    'Intracardiac':
        'AdministrationRouteIntracardiac',
    'Intracartilaginous':
        'AdministrationRouteIntracartilaginous',
    'Intracaudal':
        'AdministrationRouteIntracaudal',
    'Intracavernous':
        'AdministrationRouteIntracavernous',
    'Intracavitary':
        'AdministrationRouteIntracavitary',
    'Intracerebral':
        'AdministrationRouteIntracerebral',
    'Intracisternal':
        'AdministrationRouteIntracisternal',
    'Intracorneal':
        'AdministrationRouteIntracorneal',
    'Intracoronal, Dental':
        'AdministrationRouteIntraCoronalDental',
    'Intracoronary':
        'AdministrationRouteIntracoronary',
    'Intracorporus Cavernosum':
        'AdministrationRouteIntracorporusCavernosum',
    'Intradermal':
        'AdministrationRouteIntradermal',
    'Intradiscal':
        'AdministrationRouteIntradiscal',
    'Intraductal':
        'AdministrationRouteIntraductal',
    'Intraduodenal':
        'AdministrationRouteIntraduodenal',
    'Intradural':
        'AdministrationRouteIntradural',
    'Intraepidermal':
        'AdministrationRouteIntraepidermal',
    'Intraesophageal':
        'AdministrationRouteIntraesophageal',
    'Intragastric':
        'AdministrationRouteIntragastric',
    'Intragingival':
        'AdministrationRouteIntragingival',
    'Intraileal':
        'AdministrationRouteIntraileal',
    'Intralesional':
        'AdministrationRouteIntralesional',
    'Intraluminal':
        'AdministrationRouteIntraluminal',
    'Intralymphatic':
        'AdministrationRouteIntralymphatic',
    'Intramedullary':
        'AdministrationRouteIntramedullary',
    'Intrameningeal':
        'AdministrationRouteIntrameningeal',
    'Intramuscular':
        'AdministrationRouteIntramuscular',
    'Intraocular':
        'AdministrationRouteIntraocular',
    'Intraovarian':
        'AdministrationRouteIntraovarian',
    'Intrapericardial':
        'AdministrationRouteIntrapericardial',
    'Intraperitoneal':
        'AdministrationRouteIntraperitoneal',
    'Intrapleural':
        'AdministrationRouteIntrapleural',
    'Intraprostatic':
        'AdministrationRouteIntraprostatic',
    'Intrapulmonary':
        'AdministrationRouteIntrapulmonary',
    'Intrasinal':
        'AdministrationRouteIntrasinal',
    'Intraspinal':
        'AdministrationRouteIntraspinal',
    'Intrasynovial':
        'AdministrationRouteIntrasynovial',
    'Intratendinous':
        'AdministrationRouteIntratendinous',
    'Intratesticular':
        'AdministrationRouteIntratesticular',
    'Intrathecal':
        'AdministrationRouteIntrathecal',
    'Intrathoracic':
        'AdministrationRouteIntrathoracic',
    'Intratubular':
        'AdministrationRouteIntratubular',
    'Intratumor':
        'AdministrationRouteIntratumor',
    'Intratympanic':
        'AdministrationRouteIntratympanic',
    'Intrauterine':
        'AdministrationRouteIntrauterine',
    'Intravascular':
        'AdministrationRouteIntravascular',
    'Intravenous':
        'AdministrationRouteIntravenous',
    'Intravenous Bolus':
        'AdministrationRouteIntravenousBolus',
    'Intravenous Drip':
        'AdministrationRouteIntravenousDrip',
    'Intraventricular':
        'AdministrationRouteIntraventricular',
    'Intravesical':
        'AdministrationRouteIntravesical',
    'Intravitreal':
        'AdministrationRouteIntravitreal',
    'Iontophoresis':
        'AdministrationRouteIontophoresis',
    'Irrigation':
        'AdministrationRouteIrrigation',
    'Laryngeal':
        'AdministrationRouteLaryngeal',
    'Nasal':
        'AdministrationRouteNasal',
    'Nasogastric':
        'AdministrationRouteNasogastric',
    'Not Applicable':
        'AdministrationRouteNotApplicable',
    'Occlusive Dressing Technique':
        'AdministrationRouteOcclusiveDressingTechnique',
    'Ophthalmic':
        'AdministrationRouteOphthalmic',
    'Oral':
        'AdministrationRouteOral',
    'Oropharyngeal':
        'AdministrationRouteOropharyngeal',
    'Other':
        'AdministrationRouteOther',
    'Parenteral':
        'AdministrationRouteParenteral',
    'Percutaneous':
        'AdministrationRoutePercutaneous',
    'Periarticular':
        'AdministrationRoutePeriarticular',
    'Peridural':
        'AdministrationRoutePeridural',
    'Perineural':
        'AdministrationRoutePerineural',
    'Periodontal':
        'AdministrationRoutePeriodontal',
    'Rectal':
        'AdministrationRouteRectal',
    'Respiratory (Inhalation)':
        'AdministrationRouteRespiratory',
    'Retrobulbar':
        'AdministrationRouteRetrobulbar',
    'Soft Tissue':
        'AdministrationRouteSoftTissue',
    'Subarachnoid':
        'AdministrationRouteSubarachnoid',
    'Subconjunctival':
        'AdministrationRouteSubconjunctival',
    'Subcutaneous':
        'AdministrationRouteSubcutaneous',
    'Sublingual':
        'AdministrationRouteSublingual',
    'Submucosal':
        'AdministrationRouteSubmucosal',
    'Topical':
        'AdministrationRouteTopical',
    'Transdermal':
        'AdministrationRouteTransdermal',
    'Transmucosal':
        'AdministrationRouteTransmucosal',
    'Transplacental':
        'AdministrationRouteTransplacental',
    'Transtracheal':
        'AdministrationRouteTranstracheal',
    'Transtympanic':
        'AdministrationRouteTranstympanic',
    'Unassigned':
        'AdministrationRouteUnassigned',
    'Unknown':
        'AdministrationRouteUnknown',
    'Ureteral':
        'AdministrationRouteUreteral',
    'Urethral':
        'AdministrationRouteUrethral',
    'Vaginal':
        'AdministrationRouteVaginal',
    'Injection':
        'AdministrationRouteInjection',
    'Implantation':
        'AdministrationRouteImplantation',
    'Intra-Anal':
        'AdministrationRouteIntraAnal',
    'Pyelocalyceal':
        'AdministrationRoutePyelocalyceal',
    'Intracranial':
        'AdministrationRouteIntraCranial',
    'Intratracheal':
        'AdministrationRouteIntraTracheal',
    'For Rx Compounding':
        'AdministrationRouteForRxCompounding',
    'Perfusion, Biliary':
        'AdministrationRoutePerfusionBiliary',
    'PerfusionCardiac':
        'AdministrationRoutePerfusionCardiac',
}

ADMIN_ROUTES_W_COMMAS = {
    'PERFUSION, CARDIAC': 'AdministrationRoutePerfusionCardiac',
    'PERFUSION, BILIARY': 'AdministrationRoutePerfusionBiliary',
    'INTRACORONAL, DENTAL': 'AdministrationRouteIntracoronalDental',
}

ADMIN_ROUTE_REPLACEMENTS = {
    'INHALATION': 'RESPIRATORY (INHALATION)',
    'N/A': 'NOT APPLICABLE',
    'OTIC': 'AURICULAR (OTIC)',
    'SPINAL': 'INTRASPINAL',
    'IV (INFUSION)': 'INTRAVENOUS DRIP',
    'INTRAVESICULAR': 'INTRAVESICAL',
    'INTRAOSSEOUS': 'INTRAMEDULLARY',
    'IM-IV': 'INTRAVENOUS, INTRAMUSCULAR',
}

DOSAGE_FORM_IN_ADMIN_ROUTE = {
    'SUSPENSION': ['dcid:DosageFormSuspension,', ''],
    'ORAL SUSPENSION': [
        'dcid:DosageFormSuspension,', 'dcid:AdministrationRouteOral,'
    ],
    'SUBCUTANEOUS LYOPHILIZED POWER': [
        'dosageForm: dcid:DosageFormPowderLyophilizedPowder,',
        'administrationRoute: dcid:AdministrationRouteSubcutaneous,'
    ],
    'ORALLY DISINTEGRATING': [
        'dcid:DosageFormTabletOrallyDisintegrating,',
        'dcid:AdministrationRouteOral,'
    ],
}

DOSAGE_FORM_REPLACEMENTS = {
    'N/A': '',
    'TROCHE/LOZENGE': 'TROCHE, LOZENGE',
    '/': ', ',
    'INJECTABLE': 'INJECTION',
    'INJECTION, LIPOSOMAL': 'INJECTABLE, LIPOSOMAL',
    'PELLETS': 'PELLET',
    'TABLET, EXTENDED RELEASE, CHEWABLE': 'TABLET, CHEWABLE, EXTENDED RELEASE',
    'SOLUTION FOR SLUSH': 'SOLUTION, FOR SLUSH',
    'REL ':
        'RELEASE '  # space char after REL is necessary to distinguish REL from RELEASE
}
DOSAGE_FORMS_W_4_COMMAS = [
    'Injection, Powder, Lyophilized, For Suspension, Extended Release'
]

DOSAGE_FORMS_W_3_COMMAS = [
    'Injection, Powder, For Suspension, Extended Release',
    'Injection, Powder, Lyophilized, For Liposomal Suspension',
    'Injection, Powder, Lyophilized, For Solution',
    'Injection, Powder, Lyophilized, For Suspension',
]
DOSAGE_FORMS_W_2_COMMAS = [
    'Capsule, Coated, Extended Release',
    'Capsule, Film Coated, Extended Release',
    'Granule, For Suspension, Extended Release',
    'Injection, Powder, For Solution',
    'Injection, Powder, For Suspension',
    'Injection, Solution, Concentrate',
    'Injection, Suspension, Extended Release',
    'Injection, Suspension, Liposomal',
    'Injection, Suspension, Sonicated',
    'Patch, Extended Release, Electrically Controlled',
    'Pellet, Coated, Extended Release',
    'Solution, Gel Forming, Drops',
    'Solution, Gel Forming, Extended Release',
    'Tablet, Chewable, Extended Release',
    'Tablet, Film Coated, Extended Release',
    'Tablet, Multilayer, Extended Release',
    'Tablet, Orally Disintegrating, Delayed Release',
    'Tablet, Orally Disintegrating, Extended Release',
]

DOSAGE_FORMS_W_COMMA = [
    'Aerosol, Foam',
    'Aerosol, Metered',
    'Aerosol, Powder',
    'Aerosol, Spray',
    'Bar, Chewable',
    'Capsule, Coated',
    'Capsule, Coated Pellet',
    'Capsule, Delayed Release Pellet',
    'Capsule, Delayed Release',
    'Capsule, Extended Release',
    'Capsule, Gelatin Coated',
    'Capsule, Liquid Filled',
    'Cream, Augmented',
    'Fiber, Extended Release',
    'Film, Extended Release',
    'Film, Soluble',
    'For Suspension, Extended Release',
    'Gel, Dentifrice',
    'Gel, Metered',
    'Granule, Delayed Release',
    'Granule, Effervescent',
    'Granule, For Solution',
    'Granule, For Suspension',
    'Gum, Chewing',
    'Injectable, Liposomal',
    'Injection, Emulsion',
    'Injection, Lipid Complex',
    'Injection, Solution',
    'Injection, Suspension',
    'Insert, Extended Release',
    'Liquid, Extended Release',
    'Lotion, Augmented',
    'Lotion, Shampoo',
    'Ointment, Augmented',
    'Paste, Dentifrice',
    'Patch, Extended Release',
    'Pellet, Implantable',
    'Powder, Dentifrice',
    'Powder, For Solution',
    'Powder, For Suspension',
    'Powder, Metered',
    'Shampoo, Suspension',
    'Solution, Concentrate',
    'Solution, For Slush',
    'Solution, Drops',
    'Spray, Metered',
    'Spray, Suspension',
    'Suppository, Extended Release',
    'Suspension, Extended Release',
    'Suspension, Drops',
    'Tablet, Chewable',
    'Tablet, Coated Particles',
    'Tablet, Delayed Release Particles',
    'Tablet, Coated',
    'Tablet, Delayed Release',
    'Tablet, Effervescent',
    'Tablet, Extended Release',
    'Tablet, Film Coated',
    'Tablet, For Solution',
    'Tablet, For Suspension',
    'Tablet, Multilayer',
    'Tablet, Orally Disintegrating',
    'Tablet, Soluble',
    'Tablet, Sugar Coated',
    'Powder, Lyophilized Powder',
    'Solution, Metered',
    'Suspension, Liposomal',
    'For Suspension, Delayed Release',
    'Suspension, Delayed Release',
    'Oil, Drops',
    'Tablet, Dispersible',
    'Gel, Augmented',
    'Injection, Extended Release',
    'System, Extended Release',
    'Powder, Extended Release',
    'Solution, Extended Release',
]

DRUG_REF_REPLACEMENTS = {
    ' , ': '_',
    ', ': '_',
    ',': '_',
    '/ ': '_',
    '/': '-',
    '- ': '-',
    ' IN PLASTIC CONTAINER': '',
    ' IN WATER': '',
    ' ': '_',
    '%': 'PCT',
}

INGREDIENT_REPLACEMENTS = {
    ' , ': '_',
    ', ': '_',
    ',': '_',
    'N/A': 'NA',
    '/ ': '_',
    '/': '-',
    ' ': '_',
    '%': 'PRCT',
}

ILL_FORMATTED_FORMS = {
    'SOLUTION; ORAL AND TABLET; DELAYED RELEASE':
        'SOLUTION, TABLET, DELAYED RELEASE; ORAL',
    'CAPSULE; CAPSULE, DELAYED REL PELLETS; TABLET;ORAL':
        'CAPSULE, CAPSULE, DELAYED REL PELLETS, TABLET; ORAL',
    'POWDER, FOR INJECTION SOLUTION, LYOPHILIZED POWDER':
        'INJECTION, POWDER, LYOPHILIZED, FOR SOLUTION; INJECTION',
    'POWDER FOR ORAL SOLUTION':
        'POWDER, FOR SOLUTION; ORAL',
    'UNKNOWN':
        ''
}

ILL_FORMATTED_STRENGTHS = {
    'EQ': '',
    '(BASE)': 'BASE',
    '(U-100)': '',
    '(U-200)': '',
    '*': '',
    'UNKNOWN': '',
    'and': ';',
    '0.03MG,0.3MG;0.75MG': '0.03MG; 0.3MG;0.75MG',
    '300MG BASE,1MG,0.5MG; 300MG BASE': '300MG BASE;1MG;0.5MG',
    'N/A;N/A	N/A;N/A;N/A': 'N/A;N/A;N/A;N/A;N/A',
    '2.5MG/O.5ML': '2.5MG/0.5ML',
}

ILL_FORMATTED_INGREDIENTS = {
    'IRBESARTAN:':
        'IRBESARTAN;',
    'LIOTRIX (T4;T3)':
        'LIOTRIX (T4,T3)',
    'MENOTROPINS (FSH;LSH)':
        'MENOTROPINS (FSH,LH)',
    'TRIPLE SULFA (SULFABENZAMIDE;SULFACETAMIDE;SULFATHIAZOLE':
        'SULFABENZAMIDE;SULFACETAMIDE;SULFATHIAZOLE (TRIPLE SULFA)',
    'PANCRELIPASE (AMYLASE;LIPASE;PROTEASE)':
        'AMYLASE;LIPASE;PROTEASE (PANCRELIPASE)',
    'LAMIVUDINE, NEVIRAPINE, AND STAVUDINE':
        'LAMIVUDINE; NEVIRAPINE; STAVUDINE',
    'ELAGOLIX SODIUM,ESTRADIOL,NORETHINDRONE ACETATE; ELAGOLIX SODIUM':
        'ELAGOLIX SODIUM;ESTRADIOL;NORETHINDRONE ACETATE',
    'TRISULFAPYRIMIDINES (SULFADIAZINE;SULFAMERAZINE;SULFAMETHAZINE)':
        'SULFADIAZINE;SULFAMERAZINE;SULFAMETHAZINE',
}

ADDITIONAL_INFO_TAGS = [
    'See current Annual Edition, 1.8 Description of Special Situations, Levothyroxine Sodium',
    'Indicated for use and comarketed with Interferon ALFA-2B, Recombinant (INTRON A), as Rebetron Combination Therapy',
    'Federal Register determination that product was not discontinued or withdrawn for safety or efficacy reasons',
    'Federal Register determination that product was not withdrawn or discontinued for safety or efficacy reasons',
    'Federal Register determination that product was discontinued or withdrawn for safety or efficacy reasons',
    'Federal Register determination that product was discontinued or withdrawn for s or e reasons',
    'Federal Register determination that product was not discontinued or withdrawn for s or e reasons'
]
DOSE_TYPES = ['SINGLE-DOSE', 'SINGLE-USE', 'MULTIDOSE']
DRUG_COURSES = ['ORAL-28', 'ORAL-21', 'ORAL-20']
