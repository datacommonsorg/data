# Copyright 2025 Google LLC
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

# Replacing values for the year 2008 and 2011
replacement_08_11 = {
    'state_and_county_fips_code': 'fips code',
    'pollutant_cd': 'pollutant code',
    'uom': 'emissions uom',
    'total_emissions': 'total emissions',
    'emissions_type_code': 'emissions type code'
}

# dropping unwanted values for the year 2008 and 2011
drop_08_11 = [
    'tribal_name', 'st_usps_cd', 'county_name', 'data_category_cd',
    'description', 'aircraft_engine_type_cd', 'emissions_op_type_code',
    'data_set_short_name'
]

# dropping unwanted values for the year 2008 and 2011
drop_08_11_event = [
    'st_usps_cd', 'county_name', 'SCC_Level_One', 'SCC_Level_Two',
    'SCC_Level_Three', 'SCC_Level_Four', 'EI_Sector', 'description'
]

# replacement for the year 2014
replacement_14 = {
    'state_and_county_fips_code': 'fips code',
    'fips': 'fips code',
    'SCC': 'scc',
    'pollutant_cd': 'pollutant code',
    'uom': 'emissions uom',
    'total_emissions': 'total emissions',
    'emissions_type_code': 'emissions type code'
}

# dropping unwanted values for the year 2014
drop_14 = [
    'tribal_name', 'fips_state_code', 'st_usps_cd', 'county_name',
    'data_category', 'emission_operating_type', 'pollutant_desc',
    'emissions_operating_type', 'data_set'
]

# dropping unwanted values for the year 2014
drop_14_event = ['state', 'county', 'fire_type', 'pollutant desc']

# replacing for the year 2017
replacement_17 = {
    'emissions uom': 'unit',
    'total emissions': 'observation',
    'data set': 'year'
}

# replacing for the year 2017
replacement_point_17 = {
    'fips': 'fips code',
    'pollutant_code': 'pollutant code',
    'total_emissions': 'total emissions',
    'emissions_uom': 'emissions uom',
    'total emissions': 'observation',
    'pollutant_type': 'pollutant type(s)'
}

# dropping unwanted values for the year 2017
drop_17 = [
    'epa region code', 'state', 'fips state code', 'county', 'aetc',
    'reporting period', 'sector', 'tribal name', 'pollutant desc',
    'data category', 'data set'
]

# dropping unwanted value for 2017
drop_17_event = [
    'state', 'fips state code', 'tribal name', 'county', 'data category',
    'reporting period', 'emissions operating type', 'pollutant desc', 'data set'
]
replacement_tribes = {'tribal name': 'fips code'}

replacement_20 = {
    'fips state/county code': 'fips code',
    'scc': 'scc',
    'pollutant code': 'pollutant code',
    'total emissions': 'observation',
    'uom': 'unit'
}

drop_tribes = [
    'state', 'fips state code', 'data category', 'reporting period',
    'emissions operating type', 'pollutant desc', 'data set'
]
drop_df = [
    'scc', 'pollutant code', 'emissions type code', 'pollutant type(s)',
    'fips code'
]
df_columns = [
    'year', 'fips code', 'scc', 'pollutant code', 'total emissions',
    'emissions uom', 'pollutant type(s)', 'emissions type code'
]
pollutants = [
    "50000", "57125", "67561", "67663", "71432", "75070", "91203", "108883",
    "108952", "110543", "129000", "1332214", "7439921", "7439965", "7439976",
    "7440020", "7440382", "7440439", "7440484", "7647010", "7664393", "7723140",
    "7782492", "7782505", "7783064", "8007452", "16065831", "18540299", "CH4",
    "CO", "CO2", "N2O", "NH3", "NOX", "PM10-PRI", "PM25-PRI", "SO2", "VOC"
]
replace_metadata = {
    "R":
        "Refueling",
    "E":
        "Evaporation",
    "X":
        "Exhaust",
    "B":
        "BName",
    "T":
        "TName",
    "C":
        "Cruise",
    "M":
        "Maneuvering",
    "Z":
        "ReducedSpeedZone",
    "140":
        "Coke_Oven_Emissions",
    "141":
        "Benzene_Soluble_Organics_BSO",
    "142":
        "Methylene_Chloride_Soluble_Organics_MCSO",
    "383":
        "Fine_Mineral_Fibers",
    "604":
        "Nickel_Refinery_Dust",
    "616":
        "Slagwool_Man_Made_Fibers",
    "617":
        "Rockwool_Man_Made_Fibers",
    "51796":
        "Ethyl_Carbamate",
    "53963":
        "N_9H_Fluoren_2_Yl_Acetamide",
    "57147":
        "1_1_Dimethyl_Hydrazine",
    "57578":
        "Oxetan_2_One",
    "57749":
        "Chlordane",
    "59892":
        "4_Nitrosomorpholine",
    "60117":
        "N_N_Dimethyl_4_Phenyldiazenylaniline",
    "62737":
        "2_2_Dichloroethenyl_Dimethyl_Phosphate",
    "62759":
        "N_N_Dimethylnitrous_Amide",
    "64675":
        "Diethyl_Sulfate",
    "67425":
        "Ethylenebis_Oxyethylenenitrilo_Tetraacetic_Acid",
    "67721":
        "1_1_1_2_2_2_Hexachloroethane",
    "72435":
        "Methoxychlor",
    "75558":
        "2_Methylaziridine",
    "76448":
        "Heptachlor",
    "79118":
        "2_Chloroacetic_Acid",
    "79447":
        "N_N_Dimethylcarbamoyl_Chloride",
    "90040":
        "2_Methoxyaniline",
    "91941":
        "4_4_Amino_3_Chlorophenyl_2_Chloroaniline",
    "92671":
        "4_Phenylaniline",
    "92875":
        "4_4_Aminophenyl_Aniline",
    "92933":
        "1_Nitro_4_Phenylbenzene",
    "95807":
        "4_Methylbenzene_1_3_Diamine",
    "95954":
        "2_4_5_Trichlorophenol",
    "96128":
        "1_2_Dibromo_3_Chloropropane",
    "96457":
        "Imidazolidine_2_Thione",
    "98077":
        "Trichloromethylbenzene",
    "101144":
        "4_4_Methylenebis_2_Chloraniline",
    "106503":
        "Benzene_1_4_Diamine",
    "106945":
        "1_Bromopropane",
    "107302":
        "Chloro_Methoxy_Methane",
    "110496":
        "2_Methoxyethanol",
    "110714":
        "1_2_Dimethoxyethane",
    "111444":
        "1_Chloro_2_2_Chloroethoxy_Ethane",
    "111966":
        "1_Methoxy_2_2_Methoxyethoxy_Ethane",
    "112254":
        "2_Hexoxyethanol",
    "112356":
        "2_2_2_Methoxyethoxy_Ethoxy_Ethanol",
    "112367":
        "1_Ethoxy_2_2_Ethoxyethoxy_Ethane",
    "112492":
        "1_Methoxy_2_2_2_Methoxyethoxy_Ethoxy_Ethane",
    "112505":
        "2_2_2_Ethoxyethoxy_Ethoxy_Ethanol",
    "114261":
        "2_2_Hexoxyethoxy_Ethanol",
    "119904":
        "4_4_Amino_3_Methoxyphenyl_2_Methoxyaniline",
    "119937":
        "4_4_Amino_3_Methylphenyl_2_Methylaniline",
    "122667":
        "1_2_Diphenylhydrazine",
    "133904":
        "3_Amino_2_5_Dichlorobenzoic_Acid",
    "143226":
        "2_2_2_Butoxyethoxy_Ethoxy_Ethanol",
    "151564":
        "Aziridine",
    "189559":
        "Dibenzo_a_i_Pyrene",
    "189640":
        "Dibenzo_a_h_Pyrene",
    "191300":
        "Dibenzo_a_l_Pyrene",
    "192654":
        "Dibenzo_a_e_Pyrene",
    "194592":
        "7H_Dibenzo_c_g_carbazole",
    "224420":
        "Dibenzo_a_j_Acridine",
    "226368":
        "Dibenz_a_h_acridine",
    "334883":
        "Hydrazine",
    "510156":
        "2_2_Bis_4_Chlorophenyl_2_Hydroxyacetate",
    "534521":
        "2_Methyl_4_6_Dinitrophenol",
    "542881":
        "Chloro_Chloromethoxy_Methane",
    "593602":
        "Bromoethene",
    "602879":
        "5_Nitro_1_2_Dihydroacenaphthylene",
    "624839":
        "Methylimino_Oxo_Methane",
    "629141":
        "1_2_Diethoxyethane",
    "680319":
        "Hexamethylphosphoramide",
    "684935":
        "1_Methyl_1_Nitrosourea",
    "101779":
        "4_4_Methylenedianiline",
    "1120714":
        "Oxathiolane_2_2_Dioxide",
    "1313991":
        "Oxonickel",
    "1332214":
        "Asbestos",
    "1333820":
        "Trioxochromium",
    "1589497":
        "Trifluralin",
    "4439241":
        "5_Methylchrysene",
    "5522430":
        "1_Nitropyrene",
    "7738945":
        "Chromic_Acid_VI",
    "7795917":
        "Hydrogen_Sulfide",
    "8001352":
        "Toxaphene",
    "8007452":
        "Coal_Tar",
    "20706256":
        "2_Propoxyethyl_Acetate",
    "10215335":
        "3_Butoxypropan_1_Ol",
    "12035722":
        "Sulfanylidene_Lambda4_Sulfanylidene_Nickel",
    "31508006":
        "1_2_4_Trichloro_5_3_4_Dichlorophenyl_Benzene",
    "32598133":
        "1_2_Dichloro_4_3_4_Dichlorophenyl_Benzene",
    "32598144":
        "1_2_3_Trichloro_4_3_4_Dichlorophenyl_Benzene",
    "38380084":
        "1_2_3_4_Tetrachloro_5_3_4_Dichlorophenyl_Benzene",
    "52663726":
        "1_2_3_Trichloro_5_2_4_5_Trichlorophenyl_Benzene",
    "74472370":
        "1_2_3_4_Tetrachloro_5_4_Chlorophenyl_Benzene",
    "16672392":
        "Di_Ethylene_Glycol_Monobutyl_Ether_Phthalate",
    "N590":
        "Polycyclic_Aromatic_Compounds",
    "SF6":
        "Hexafluoro_Lambda6_Sulfane",
    "H":
        "Hotelling",
    "PM-CON":
        "PMCondensible",
    "PM10-FIL":
        "PM10Filterable",
    "PM25-FIL":
        "PM2.5Filterable",
    "132649":
        "Dibenzofurans",
    "98862":
        "1_Phenylethanone",
    "100414":
        "EthylBenzene",
    "123386":
        "Propanal",
    "N2O":
        "NitrousOxide",
    "NH3":
        "Ammonia",
    "18540299":
        "Chromium_6",
    "1330207":
        "1_3_Xylene",
    "208968":
        "Acenaphthylene",
    "53703":
        "Naphtho_1_2_B_Phenanthrene",
    "75070":
        "Acetaldehyde",
    "DIESEL-PM10":
        "DieselPM10",
    "PM10-PRI":
        "PM10",
    "PMFINE":
        "PMFINE",
    "129000":
        "Pyrene",
    "205992":
        "Benzo_B_Fluoranthene",
    "207089":
        "Benzo_K_Fluoranthene",
    "7440382":
        "Arsenic",
    "86737":
        "Fluorene",
    "50000":
        "Formaldehyde",
    "83329":
        "Acenaphthene",
    "SO4":
        "Sulfate",
    "107028":
        "Acrolein",
    "206440":
        "Fluoranthene",
    "108883":
        "Toluene",
    "CH4":
        "Methane",
    "218019":
        "Chrysene",
    "7439976":
        "Mercury",
    "VOC":
        "VolatileOrganicCompound",
    "191242":
        "Benzo_GHI_Perylene",
    "PM25-PRI":
        "PM2.5",
    "EC":
        "ElementalCarbon",
    "OC":
        "OrganicCarbon",
    "110543":
        "Hexane",
    "NOX":
        "OxidesOfNitrogen",
    "SO2":
        "SulfurDioxide",
    "120127":
        "Anthracene",
    "50328":
        "Benzo_A_Pyrene",
    "540841":
        "2_2_4_Trimethylpentane",
    "7440020":
        "Nickel",
    "CO":
        "CarbonMonoxide",
    "100425":
        "Styrene",
    "56553":
        "Benzo_A_Anthracene",
    "7439965":
        "Manganese",
    "193395":
        "Indeno_1_2_3_C_D_Pyrene",
    "CO2":
        "CarbonDioxide",
    "NO3":
        "Nitrate",
    "71432":
        "Benzene",
    "85018":
        "Phenanthrene",
    "91203":
        "Naphthalene",
    "DIESEL-PM25":
        "DieselPM2.5",
    "106990":
        "Buta_1_3_Diene",
    "55673897":
        "1_2_3_4_7_8_9_Heptachlorodibenzofuran",
    "60851345":
        "2_3_4_6_7_8_Hexachlorodibenzofuran",
    "3268879":
        "1_2_3_4_6_7_8_9_Octachlorodibenzo_P_Dioxin",
    "57117416":
        "1_2_3_7_8_Pentachlorodibenzofuran",
    "40321764":
        "1_2_3_7_8_Pentachlorodibenzo_P_Dioxin",
    "72918219":
        "1_2_3_7_8_9_Hexachlorodibenzofuran",
    "67562394":
        "1_2_3_4_6_7_8_Heptachlorodibenzofuran",
    "51207319":
        "2_3_7_8_Tetrachlorodibenzofuran",
    "57117449":
        "1_2_3_6_7_8_Hexachlorodibenzofuran",
    "19408743":
        "1_2_3_7_8_9_Hexachlorodibenzo_P_Dioxin",
    "35822469":
        "1_2_3_4_6_7_8_Heptachlorodibenzo_P_Dioxin",
    "57117314":
        "2_3_4_7_8_Pentachlorodibenzofuran",
    "39001020":
        "1_2_3_4_6_7_8_9_Octachlorodibenzofuran",
    "70648269":
        "1_2_3_4_7_8_Hexachlorodibenzofuran",
    "57653857":
        "1_2_3_6_7_8_Hexachlorodibenzo_P_Dioxin",
    "DIESEL-PM2":
        "DieselPM2.5",
    "39227286":
        "1_2_3_4_7_8_Hexachlorodibenzo_P_Dioxin",
    "1746016":
        "2_3_7_8_Tetrachlorodibenzo_P_Dioxin",
    "DIESEL-PM1":
        "DieselPM10",
    "95476":
        "1_2_Xylene",
    "106423":
        "1_4_Xylene",
    "7440439":
        "Cadmium",
    "7440484":
        "Cobalt",
    "98828":
        "Cumene",
    "7439921":
        "Lead",
    "7782505":
        "Chlorine",
    "7782492":
        "Selenium",
    "7723140":
        "Phosphorus",
    "7440360":
        "Antimony",
    "67561":
        "Methanol",
    "16065831":
        "Oxo_Oxochromiooxy_Chromium",
    "108383":
        "1_3_Xylene",
    "130498292":
        "PolycyclicAromaticHydrocarbons_Total",
    "1634044":
        "2_Methoxy_2_Methylpropane",
    "91576":
        "2_Methylnaphthalene",
    "171":
        "Glycol_Ethers",
    "250":
        "PAH_POM_Unspecified",
    "284":
        "Extractable_Organic_Matter",
    "51285":
        "2_4_Dinitrophenol",
    "56235":
        "Tetrachloromethane",
    "56382":
        "Diethoxy_4_Nitrophenoxy_Sulfanylidene_Lambda5_Phosphane",
    "56495":
        "3_Methyl_1_2_Dihydrobenzo_J_Aceanthrylene",
    "57125":
        "Cyanide",
    "57976":
        "7_12_Dimethylbenz_A_Anthracene",
    "58899":
        "1_2_3_4_5_6_Hexachlorocyclohexane",
    "60344":
        "Methyl_Hydrazine",
    "60355":
        "Acetamide",
    "62533":
        "Aniline",
    "63252":
        "Naphthalen_1_Yl_N_Methylcarbamate",
    "67663":
        "Chloroform",
    "68122":
        "N_N_Dimethylformamide",
    "71556":
        "1_1_1_Trichloroethane",
    "74839":
        "Bromomethane",
    "74873":
        "Chloromethane",
    "74884":
        "Iodomethane",
    "74908":
        "Formonitrile",
    "75003":
        "Chloroethane",
    "75014":
        "Chloroethene",
    "75058":
        "Acetonitrile",
    "75092":
        "Dichloromethane",
    "75150":
        "Methylene_Chloride",
    "75218":
        "Oxirane",
    "75252":
        "Bromoform",
    "75343":
        "1_1_Dichloroethane",
    "75354":
        "1_1_Dichloroethylene",
    "75445":
        "Carbonyl_Dichloride",
    "75569":
        "2_Methyloxirane",
    "77474":
        "1_2_3_4_5_5_Hexachlorocyclopenta_1_3_Diene",
    "77781":
        "Dimethyl_Sulfate",
    "78591":
        "3_5_5_Trimethylcyclohex_2_En_1_One",
    "78875":
        "1_2_Dichloropropane",
    "79005":
        "1_1_2_Trichloroethane",
    "79016":
        "1_1_2_Trichloroethene",
    "79061":
        "Prop_2_Enamide",
    "79107":
        "Prop_2_Enoic_Acid",
    "79345":
        "1_1_2_2_Tetrachloroethane",
    "79469":
        "2_Nitropropane",
    "80626":
        "Methyl_2_Methylprop_2_Enoate",
    "82688":
        "Quintobenzene",
    "84742":
        "Dibutyl_Benzene_1_2_Dicarboxylate",
    "85449":
        "2_Benzofuran_1_3_Dione",
    "86748":
        "9H_Carbazole",
    "87683":
        "1_1_2_3_4_4_Hexachlorobuta_1_3_Diene",
    "87865":
        "2_3_4_5_6_Pentachlorophenol",
    "88062":
        "2_4_6_Trichlorophenol",
    "90120":
        "1_Methylnaphthalene",
    "91225":
        "Quinoline",
    "91587":
        "2_Chloronaphthalene",
    "92524":
        "1_1_Biphenyl",
    "94757":
        "2_2_4_Dichlorophenoxy_Acetic_Acid",
    "95487":
        "2_Methylphenol",
    "95534":
        "2_Methylaniline",
    "96093":
        "2_Phenyloxirane",
    "98862":
        "Cumene",
    "98953":
        "Nitrobenzene",
    "100027":
        "4_Nitrophenol",
    "100447":
        "Ethyl_Benzene",
    "101688":
        "Methylene_Diphenyl_Diisocyanate_Mdi",
    "106445":
        "4_Methylphenol",
    "106467":
        "1_4_Dichlorobenzene",
    "106514":
        "Cyclohexa_2_5_Diene_1_4_Dione",
    "106887":
        "2_Ethyloxirane",
    "106898":
        "L_Chloro_2_3_Epoxypropane",
    "106934":
        "Dibromoethane",
    "107051":
        "3_Chloroprop_1_Ene",
    "107062":
        "1_2_Dichloroethane",
    "107131":
        "Prop_2_Enenitrile",
    "107211":
        "Ethane_1_2_Diol",
    "108054":
        "Ethenyl_Acetate",
    "108101":
        "Hexone",
    "108316":
        "Furan_2_5_Dione",
    "108394":
        "3_Methylphenol",
    "108907":
        "Chlorobenzene",
    "108952":
        "Phenol",
    "109864":
        "2_Methoxyethanol",
    "110805":
        "2_Ethoxyethanol",
    "111159":
        "2_Ethoxyethyl_Acetate",
    "111422":
        "2_2_Hydroxyethylamino_Ethanol",
    "111773":
        "2_2_Methoxyethoxy_Ethanol",
    "111900":
        "2_2_Ethoxyethoxy_Ethanol",
    "112072":
        "2_Butoxyethyl_Acetate",
    "112152":
        "2_2_Ethoxyethoxy_Ethyl_Acetate",
    "112276":
        "2_2_2_Hydroxyethoxy_Ethoxy_Ethanol",
    "112345":
        "2_2_Butoxyethoxy_Ethanol",
    "112594":
        "2_2_Hexoxyethoxy_Ethanol",
    "117817":
        "Bis_2_Ethylhexyl_Benzene_1_2_Dicarboxylate",
    "118741":
        "1_2_3_4_5_6_Hexachlorobenzene",
    "120809":
        "Benzene_1_2_Diol",
    "120821":
        "1_2_4_Trichlorobenzene",
    "121142":
        "1_Methyl_2_4_Dinitrobenzene",
    "121448":
        "N_N_Diethylethanamine",
    "121697":
        "N_N_Dimethylaniline",
    "122996":
        "2_Phenoxyethanol",
    "123319":
        "Benzene_1_4_Diol",
    "123911":
        "1_4_Diethyleneoxide",
    "124174":
        "2_2_Butoxyethoxy_Ethyl_Acetate",
    "126998":
        "2_Chlorobuta_1_3_Diene",
    "127184":
        "Perchloroethylene",
    "131113":
        "Dimethyl_Benzene_1_2_Dicarboxylate",
    "132649":
        "Dibenzofurans",
    "133062":
        "2_Trichloromethylsulfanyl_3A_4_7_7A_Tetrahydroisoindole_1_3_Dione",
    "140885":
        "Ethyl_Prop_2_Enoate",
    "156627":
        "Azanidylidenemethylideneazanide",
    "192972":
        "Benzo_E_Pyrene",
    "195197":
        "Benzo_C_Phenanthrene",
    "198550":
        "Perylene",
    "203123":
        "Benzo_G_H_I_Fluoranthene",
    "203338":
        "Benzo_A_Fluoranthene",
    "205823":
        "Benzo_J_Fluoranthene",
    "302012":
        "Hydrazine",
    "463581":
        "Carbonyl_Sulfide",
    "532274":
        "2_Chloro_1_Phenylethanone",
    "540885":
        "Tert_Butyl_Acetate",
    "542756":
        "1_3_Dichloroprop_1_Ene",
    "584849":
        "2_4_Diisocyanato_1_Methylbenzene",
    "779022":
        "9_Methyl_Anthracene",
    "822060":
        "1_6_Diisocyanatohexane",
    "832699":
        "1_Methylphenanthrene",
    "1002671":
        "1_2_Ethoxyethoxy_2_Methoxyethane",
    "1319773":
        "Cresols_Cresylic_Acid_Isomers_And_Mixture",
    "1336363":
        "Polychlorinated_Biphenyls_Aroclors",
    "1582098":
        "Trifluralin",
    "2050682":
        "1_Chloro_4_4_Chlorophenyl_Benzene",
    "2051243":
        "1_2_3_4_5_Pentachloro_6_2_3_4_5_6_Pentachlorophenyl_Benzene",
    "2051607":
        "1_Chloro_2_Phenylbenzene",
    "2381217":
        "1_Methylpyrene",
    "2422799":
        "12_Methylbenz_A_Anthracene",
    "2531842":
        "2_Methylphenanthrene",
    "2807309":
        "2_Propoxyethanol",
    "3697243":
        "5_Methylchrysene",
    "7012375":
        "2_4_Dichloro_1_4_Chlorophenyl_Benzene",
    "7440417":
        "Beryllium",
    "7550450":
        "Tetrachlorotitanium",
    "7647010":
        "Chlorane",
    "7664393":
        "Fluorane",
    "7783064":
        "Sulfane",
    "7803512":
        "Phosphane",
    "25429292":
        "1_2_3_4_5_Pentachloro_6_Phenylbenzene",
    "26601649":
        "1_2_3_4_5_Pentachloro_6_2_Chlorophenyl_Benzene",
    "26914181":
        "2_Chloro_1_4_Dimethoxy_3_Methylanthracene_9_10_Dione",
    "26914330":
        "1_2_3_4_Tetrachloro_5_Phenylbenzene",
    "28655712":
        "1_2_3_4_5_Pentachloro_6_2_3_Dichlorophenyl_Benzene",
    "41637905":
        "6_Methylchrysene",
    "56832736":
        "Benzofluoranthenes",
    "65357699":
        "8_Methylbenzo_E_Pyrene",
    "2_Propoxyethyl_Acetate":
        "2-Propoxyethyl Acetate",
    "Di_Ethylene_Glycol_Monobutyl_Ether_Phthalate":
        "Di (Ethylene Glycol Monobutyl Ether) Phthalate",
    "Coke_Oven_Emissions":
        "Coke Oven Emissions",
    "Benzene_Soluble_Organics_BSO":
        "Benzene Soluble Organics (BSO)",
    "Methylene_Chloride_Soluble_Organics_MCSO":
        "Methylene Chloride Soluble Organics (MCSO)",
    "Fine_Mineral_Fibers":
        "Fine Mineral Fibers",
    "Nickel_Refinery_Dust":
        "Nickel Refinery Dust",
    "Slagwool_Man_Made_Fibers":
        "Slagwool (Man-Made Fibers)",
    "Rockwool_Man_Made_Fibers":
        "Rockwool (Man-Made Fibers)",
    "Ethyl_Carbamate":
        "Ethyl Carbamate",
    "N_9H_Fluoren_2_Yl_Acetamide":
        "N-(9H-Fluoren-2-Yl)Acetamide",
    "1_1_Dimethyl_Hydrazine":
        "1,1-Dimethyl Hydrazine",
    "Oxetan_2_One":
        "Oxetan-2-One",
    "Chlordane":
        "Chlordane",
    "4_Nitrosomorpholine":
        "4-Nitrosomorpholine",
    "N_N_Dimethyl_4_Phenyldiazenylaniline":
        "N,N-Dimethyl-4-Phenyldiazenylaniline",
    "2_2_Dichloroethenyl_Dimethyl_Phosphate":
        "2,2-Dichloroethenyl Dimethyl Phosphate",
    "N_N_Dimethylnitrous_Amide":
        "N,N-Dimethylnitrous Amide",
    "Diethyl_Sulfate":
        "Diethyl Sulfate",
    "Ethylenebis_Oxyethylenenitrilo_Tetraacetic_Acid":
        "(Ethylenebis(Oxyethylenenitrilo)) Tetraacetic Acid",
    "1_1_1_2_2_2_Hexachloroethane":
        "1,1,1,2,2,2-Hexachloroethane",
    "Methoxychlor":
        "Methoxychlor",
    "2_Methylaziridine":
        "2-Methylaziridine",
    "Heptachlor":
        "Heptachlor",
    "2_Chloroacetic_Acid":
        "2-Chloroacetic Acid",
    "N_N_Dimethylcarbamoyl_Chloride":
        "N,N-Dimethylcarbamoyl Chloride",
    "2_Methoxyaniline":
        "2-Methoxyaniline",
    "4_4_Amino_3_Chlorophenyl_2_Chloroaniline":
        "4-(4-Amino-3-Chlorophenyl)-2-Chloroaniline",
    "4_Phenylaniline":
        "4-Phenylaniline",
    "4_4_Aminophenyl_Aniline":
        "4-(4-Aminophenyl)Aniline",
    "1_Nitro_4_Phenylbenzene":
        "1-Nitro-4-Phenylbenzene",
    "4_Methylbenzene_1_3_Diamine":
        "4-Methylbenzene-1,3-Diamine",
    "2_4_5_Trichlorophenol":
        "2,4,5-Trichlorophenol",
    "1_2_Dibromo_3_Chloropropane":
        "1,2-Dibromo-3-Chloropropane",
    "Imidazolidine_2_Thione":
        "Imidazolidine-2-Thione",
    "Trichloromethylbenzene":
        "Trichloromethylbenzene",
    "4_4_Methylenebis_2_Chloraniline":
        "4,4-Methylenebis(2-Chloraniline)",
    "Benzene_1_4_Diamine":
        "Benzene-1,4-Diamine",
    "1_Bromopropane":
        "1-Bromopropane",
    "Chloro_Methoxy_Methane":
        "Chloro(Methoxy)Methane",
    "2_Methoxyethanol":
        "2-Methoxyethanol",
    "1_2_Dimethoxyethane":
        "1,2-Dimethoxyethane",
    "1_Chloro_2_2_Chloroethoxy_Ethane":
        "1-Chloro-2-(2-Chloroethoxy)Ethane",
    "1_Methoxy_2_2_Methoxyethoxy_Ethane":
        "1-Methoxy-2-(2-Methoxyethoxy)Ethane",
    "2_Hexoxyethanol":
        "2-Hexoxyethanol",
    "2_2_2_Methoxyethoxy_Ethoxy_Ethanol":
        "2-[2-(2-Methoxyethoxy)Ethoxy]Ethanol",
    "1_Ethoxy_2_2_Ethoxyethoxy_Ethane":
        "1-Ethoxy-2-(2-Ethoxyethoxy)Ethane",
    "1_Methoxy_2_2_2_Methoxyethoxy_Ethoxy_Ethane":
        "1-Methoxy-2-[2-(2-Methoxyethoxy)Ethoxy]Ethane",
    "2_2_2_Ethoxyethoxy_Ethoxy_Ethanol":
        "2-[2-(2-Ethoxyethoxy)Ethoxy]Ethanol",
    "2_2_Hexoxyethoxy_Ethanol":
        "2-(2-Hexoxyethoxy)Ethanol",
    "4_4_Amino_3_Methoxyphenyl_2_Methoxyaniline":
        "4-(4-Amino-3-Methoxyphenyl)-2-Methoxyaniline",
    "4_4_Amino_3_Methylphenyl_2_Methylaniline":
        "4-(4-Amino-3-Methylphenyl)-2-Methylaniline",
    "1_2_Diphenylhydrazine":
        "1,2-Diphenylhydrazine",
    "3_Amino_2_5_Dichlorobenzoic_Acid":
        "3-Amino-2,5-Dichlorobenzoic Acid",
    "2_2_2_Butoxyethoxy_Ethoxy_Ethanol":
        "2-[2-(2-Butoxyethoxy)Ethoxy]Ethanol",
    "Aziridine":
        "Aziridine",
    "Dibenzo_a_i_Pyrene":
        "Dibenzo[a,i]Pyrene",
    "Dibenzo_a_h_Pyrene":
        "Dibenzo[a,h]Pyrene",
    "Dibenzo_a_l_Pyrene":
        "Dibenzo[a,l]Pyrene",
    "Dibenzo_a_e_Pyrene":
        "Dibenzo[a,e]Pyrene",
    "7H_Dibenzo_c_g_carbazole":
        "7H-Dibenzo[c,g]carbazole",
    "Dibenzo_a_j_Acridine":
        "Dibenzo[a,j]Acridine",
    "Dibenz_a_h_acridine":
        "Dibenz[a,h]acridine",
    "Hydrazine":
        "Hydrazine",
    "2_2_Bis_4_Chlorophenyl_2_Hydroxyacetate":
        "2,2-Bis(4-Chlorophenyl)-2-Hydroxyacetate",
    "2_Methyl_4_6_Dinitrophenol":
        "2-Methyl-4,6-Dinitrophenol",
    "Chloro_Chloromethoxy_Methane":
        "Chloro(Chloromethoxy)Methane",
    "Bromoethene":
        "Bromoethene",
    "5_Nitro_1_2_Dihydroacenaphthylene":
        "5-Nitro-1,2-Dihydroacenaphthylene",
    "Methylimino_Oxo_Methane":
        "Methylimino(Oxo)Methane",
    "1_2_Diethoxyethane":
        "1,2-Diethoxyethane",
    "Hexamethylphosphoramide":
        "Hexamethylphosphoramide",
    "1_Methyl_1_Nitrosourea":
        "1-Methyl-1-Nitrosourea",
    "Oxathiolane_2_2_Dioxide":
        "Oxathiolane 2,2-Dioxide",
    "Oxonickel":
        "Oxonickel",
    "Asbestos":
        "Asbestos",
    "Trioxochromium":
        "Trioxochromium",
    "Trifluralin":
        "Trifluralin",
    "5_Methylchrysene":
        "5-Methylchrysene",
    "1_Nitropyrene":
        "1-Nitropyrene",
    "Chromic_Acid_VI":
        "Chromic Acid (VI)",
    "Hydrogen_Sulfide":
        "Hydrogen Sulfide",
    "Toxaphene":
        "Toxaphene",
    "Coal_Tar":
        "Coal Tar",
    "3_Butoxypropan_1_Ol":
        "3-Butoxypropan-1-Ol",
    "Sulfanylidene_Lambda4_Sulfanylidene_Nickel":
        "(Sulfanylidene-Lambda4-Sulfanylidene)Nickel",
    "1_2_4_Trichloro_5_3_4_Dichlorophenyl_Benzene":
        "1,2,4-Trichloro-5-(3,4-Dichlorophenyl)Benzene",
    "1_2_Dichloro_4_3_4_Dichlorophenyl_Benzene":
        "1,2-Dichloro-4-(3,4-Dichlorophenyl)Benzene",
    "1_2_3_Trichloro_4_3_4_Dichlorophenyl_Benzene":
        "1,2,3-Trichloro-4-(3,4-Dichlorophenyl)Benzene",
    "1_2_3_4_Tetrachloro_5_3_4_Dichlorophenyl_Benzene":
        "1,2,3,4-Tetrachloro-5-(3,4-Dichlorophenyl)Benzene",
    "1_2_3_Trichloro_5_2_4_5_Trichlorophenyl_Benzene":
        "1,2,3-Trichloro-5-(2,4,5-Trichlorophenyl)Benzene",
    "1_2_3_4_Tetrachloro_5_4_Chlorophenyl_Benzene":
        "1,2,3,4-Tetrachloro-5-(4-Chlorophenyl)Benzene",
    "Polycyclic_Aromatic_Compounds":
        "Polycyclic Aromatic Compounds",
    "Hexafluoro_Lambda6_Sulfane":
        "Hexafluoro-Lambda6-Sulfane",
    "4_4_Methylenedianiline":
        "4,4-Methylenedianiline",
    "EthylBenzene":
        "Ethyl Benzene",
    "Propanal":
        "Propanal",
    "NitrousOxide":
        "Nitrous Oxide",
    "Ammonia":
        "Ammonia",
    "Chromium_6":
        "Chromium(6+)",
    "1_3_Xylene":
        "1,3-Xylene",
    "Acenaphthylene":
        "Acenaphthylene",
    "Naphtho_1_2_B_Phenanthrene":
        "Naphtho[1,2-b]Phenanthrene",
    "Acetaldehyde":
        "Acetaldehyde",
    "DieselPM10":
        "Diesel PM10",
    "PM10":
        "PM10",
    "PMFINE":
        "PMFINE",
    "Pyrene":
        "Pyrene",
    "Benzo_B_Fluoranthene":
        "Benzo[B]Fluoranthene",
    "Benzo_K_Fluoranthene":
        "Benzo[K]Fluoranthene",
    "Arsenic":
        "Arsenic",
    "Fluorene":
        "Fluorene",
    "Formaldehyde":
        "Formaldehyde",
    "Acenaphthene":
        "Acenaphthene",
    "Sulfate":
        "Sulfate",
    "Acrolein":
        "Acrolein",
    "Fluoranthene":
        "Fluoranthene",
    "Toluene":
        "Toluene",
    "Methane":
        "Methane",
    "Chrysene":
        "Chrysene",
    "Mercury":
        "Mercury",
    "VolatileOrganicCompound":
        "Volatile Organic Compound",
    "Benzo_GHI_Perylene":
        "Benzo[G,H,I,]Perylene",
    "PM2.5":
        "PM2.5",
    "ElementalCarbon":
        "Elemental Carbon",
    "OrganicCarbon":
        "Organic Carbon",
    "Hexane":
        "Hexane",
    "OxidesOfNitrogen":
        "Oxides Of Nitrogen",
    "SulfurDioxide":
        "Sulfur Dioxide",
    "Anthracene":
        "Anthracene",
    "Benzo_A_Pyrene":
        "Benzo[A]Pyrene",
    "2_2_4_Trimethylpentane":
        "2,2,4-Trimethylpentane",
    "Nickel":
        "Nickel",
    "CarbonMonoxide":
        "Carbon Monoxide",
    "Styrene":
        "Styrene",
    "Benzo_A_Anthracene":
        "Benzo[A]Anthracene",
    "Manganese":
        "Manganese",
    "Indeno_1_2_3_C_D_Pyrene":
        "Indeno[1,2,3-C,D]Pyrene",
    "CarbonDioxide":
        "Carbon Dioxide",
    "Nitrate":
        "Nitrate",
    "Benzene":
        "Benzene",
    "Phenanthrene":
        "Phenanthrene",
    "Naphthalene":
        "Naphthalene",
    "DieselPM2.5":
        "Diesel PM2.5",
    "Buta_1_3_Diene":
        "Buta-1,3-Diene",
    "1_2_3_4_7_8_9_Heptachlorodibenzofuran":
        "1,2,3,4,7,8,9-Heptachlorodibenzofuran",
    "2_3_4_6_7_8_Hexachlorodibenzofuran":
        "2,3,4,6,7,8-Hexachlorodibenzofuran",
    "1_2_3_4_6_7_8_9_Octachlorodibenzo_P_Dioxin":
        "1,2,3,4,6,7,8,9-Octachlorodibenzo-P-Dioxin",
    "1_2_3_7_8_Pentachlorodibenzofuran":
        "1,2,3,7,8-Pentachlorodibenzofuran",
    "1_2_3_7_8_Pentachlorodibenzo_P_Dioxin":
        "1,2,3,7,8-Pentachlorodibenzo-P-Dioxin",
    "1_2_3_7_8_9_Hexachlorodibenzofuran":
        "1,2,3,7,8,9-Hexachlorodibenzofuran",
    "1_2_3_4_6_7_8_Heptachlorodibenzofuran":
        "1,2,3,4,6,7,8-Heptachlorodibenzofuran",
    "2_3_7_8_Tetrachlorodibenzofuran":
        "2,3,7,8-Tetrachlorodibenzofuran",
    "1_2_3_6_7_8_Hexachlorodibenzofuran":
        "1,2,3,6,7,8-Hexachlorodibenzofuran",
    "1_2_3_7_8_9_Hexachlorodibenzo_P_Dioxin":
        "1,2,3,7,8,9-Hexachlorodibenzo-P-Dioxin",
    "1_2_3_4_6_7_8_Heptachlorodibenzo_P_Dioxin":
        "1,2,3,4,6,7,8-Heptachlorodibenzo-P-Dioxin",
    "2_3_4_7_8_Pentachlorodibenzofuran":
        "2,3,4,7,8-Pentachlorodibenzofuran",
    "1_2_3_4_6_7_8_9_Octachlorodibenzofuran":
        "1,2,3,4,6,7,8,9-Octachlorodibenzofuran",
    "1_2_3_4_7_8_Hexachlorodibenzofuran":
        "1,2,3,4,7,8-Hexachlorodibenzofuran",
    "1_2_3_6_7_8_Hexachlorodibenzo_P_Dioxin":
        "1,2,3,6,7,8-Hexachlorodibenzo-P-Dioxin",
    "DieselPM2.5":
        "Diesel PM2.5",
    "1_2_3_4_7_8_Hexachlorodibenzo_P_Dioxin":
        "1,2,3,4,7,8-Hexachlorodibenzo-P-Dioxin",
    "2_3_7_8_Tetrachlorodibenzo_P_Dioxin":
        "2,3,7,8-Tetrachlorodibenzo-P-Dioxin",
    "DieselPM10":
        "Diesel PM10",
    "1_2_Xylene":
        "1,2-Xylene",
    "1_4_Xylene":
        "1,4-Xylene",
    "Cadmium":
        "Cadmium",
    "Cobalt":
        "Cobalt",
    "Cumene":
        "Cumene",
    "Lead":
        "Lead",
    "Chlorine":
        "Chlorine",
    "Selenium":
        "Selenium",
    "Phosphorus":
        "Phosphorus",
    "Antimony":
        "Antimony",
    "Methanol":
        "Methanol",
    "Oxo_Oxochromiooxy_Chromium":
        "Oxo(Oxochromiooxy)Chromium",
    "1_3_Xylene":
        "1,3-Xylene",
    "PolycyclicAromaticHydrocarbons_Total":
        "PolycyclicAromaticHydrocarbons, Total",
    "2_Methoxy_2_Methylpropane":
        "2-Methoxy-2-Methylpropane",
    "2_Methylnaphthalene":
        "2-Methylnaphthalene",
    "PMCondensible":
        "PM Condensible",
    "PM10Filterable":
        "PM10Filterable",
    "PM2.5Filterable":
        "PM2.5Filterable",
    "Dibenzofurans":
        "Dibenzofurans",
    "1_Phenylethanone":
        "1-Phenylethanone",
    "Glycol_Ethers":
        "Glycol Ethers",
    "PAH_POM_Unspecified":
        "PAH/POM - Unspecified",
    "Extractable_Organic_Matter":
        "Extractable Organic Matter",
    "2_4_Dinitrophenol":
        "2,4-Dinitrophenol",
    "Tetrachloromethane":
        "Tetrachloromethane",
    "Diethoxy_4_Nitrophenoxy_Sulfanylidene_Lambda5_Phosphane":
        "Diethoxy-(4-Nitrophenoxy)-Sulfanylidene-Lambda5-Phosphane",
    "3_Methyl_1_2_Dihydrobenzo_J_Aceanthrylene":
        "3-Methyl-1,2-Dihydrobenzo[J]Aceanthrylene",
    "Cyanide":
        "Cyanide",
    "7_12_Dimethylbenz_A_Anthracene":
        "7,12-Dimethylbenz[A]Anthracene",
    "1_2_3_4_5_6_Hexachlorocyclohexane":
        "1,2,3,4,5,6-Hexachlorocyclohexane",
    "Methyl_Hydrazine":
        "Methyl Hydrazine",
    "Acetamide":
        "Acetamide",
    "Aniline":
        "Aniline",
    "Naphthalen_1_Yl_N_Methylcarbamate":
        "Naphthalen-1-Yl N-Methylcarbamate",
    "Chloroform":
        "Chloroform",
    "N_N_Dimethylformamide":
        "N,N-Dimethylformamide",
    "1_1_1_Trichloroethane":
        "1,1,1-Trichloroethane",
    "Bromomethane":
        "Bromomethane",
    "Chloromethane":
        "Chloromethane",
    "Iodomethane":
        "Iodomethane",
    "Formonitrile":
        "Formonitrile",
    "Chloroethane":
        "Chloroethane",
    "Chloroethene":
        "Chloroethene",
    "Acetonitrile":
        "Acetonitrile",
    "Dichloromethane":
        "Dichloromethane",
    "Methylene_Chloride":
        "Methylene Chloride",
    "Oxirane":
        "Oxirane",
    "Bromoform":
        "Bromoform",
    "1_1_Dichloroethane":
        "1,1-Dichloroethane",
    "1_1_Dichloroethylene":
        "1,1-Dichloroethylene",
    "Carbonyl_Dichloride":
        "Carbonyl Dichloride",
    "2_Methyloxirane":
        "2-Methyloxirane",
    "1_2_3_4_5_5_Hexachlorocyclopenta_1_3_Diene":
        "1,2,3,4,5,5-Hexachlorocyclopenta-1,3-Diene",
    "Dimethyl_Sulfate":
        "Dimethyl Sulfate",
    "3_5_5_Trimethylcyclohex_2_En_1_One":
        "3,5,5-Trimethylcyclohex-2-En-1-One",
    "1_2_Dichloropropane":
        "1,2-Dichloropropane",
    "1_1_2_Trichloroethane":
        "1,1,2-Trichloroethane",
    "1_1_2_Trichloroethene":
        "1,1,2-Trichloroethene",
    "Prop_2_Enamide":
        "Prop-2-Enamide",
    "Prop_2_Enoic_Acid":
        "Prop-2-Enoic Acid",
    "1_1_2_2_Tetrachloroethane":
        "1,1,2,2-Tetrachloroethane",
    "2_Nitropropane":
        "2-Nitropropane",
    "Methyl_2_Methylprop_2_Enoate":
        "Methyl 2-Methylprop-2-Enoate",
    "Quintobenzene":
        "Quintobenzene",
    "Dibutyl_Benzene_1_2_Dicarboxylate":
        "Dibutyl Benzene-1,2-Dicarboxylate",
    "2_Benzofuran_1_3_Dione":
        "2-Benzofuran-1,3-Dione",
    "9H_Carbazole":
        "9H-Carbazole",
    "1_1_2_3_4_4_Hexachlorobuta_1_3_Diene":
        "1,1,2,3,4,4-Hexachlorobuta-1,3-Diene",
    "2_3_4_5_6_Pentachlorophenol":
        "2,3,4,5,6-Pentachlorophenol",
    "2_4_6_Trichlorophenol":
        "2,4,6-Trichlorophenol",
    "1_Methylnaphthalene":
        "1-Methylnaphthalene",
    "Quinoline":
        "Quinoline",
    "2_Chloronaphthalene":
        "2-Chloronaphthalene",
    "1_1_Biphenyl":
        "1,1'-Biphenyl",
    "2_2_4_Dichlorophenoxy_Acetic_Acid":
        "2-(2,4-Dichlorophenoxy)Acetic Acid",
    "2_Methylphenol":
        "2-Methylphenol",
    "2_Methylaniline":
        "2-Methylaniline",
    "2_Phenyloxirane":
        "2-Phenyloxirane",
    "Cumene":
        "Cumene",
    "Nitrobenzene":
        "Nitrobenzene",
    "4_Nitrophenol":
        "4-Nitrophenol",
    "Ethyl_Benzene":
        "Ethyl Benzene",
    "Methylene_Diphenyl_Diisocyanate_Mdi":
        "Methylene Diphenyl Diisocyanate (Mdi)",
    "4_Methylphenol":
        "4-Methylphenol",
    "1_4_Dichlorobenzene":
        "1,4-Dichlorobenzene",
    "Cyclohexa_2_5_Diene_1_4_Dione":
        "Cyclohexa-2,5-Diene-1,4-Dione",
    "2_Ethyloxirane":
        "2-Ethyloxirane",
    "L_Chloro_2_3_Epoxypropane":
        "L-Chloro-2,3-Epoxypropane",
    "Dibromoethane":
        "Dibromoethane",
    "3_Chloroprop_1_Ene":
        "3-Chloroprop-1-Ene",
    "1_2_Dichloroethane":
        "1,2-Dichloroethane",
    "Prop_2_Enenitrile":
        "Prop-2-Enenitrile",
    "Ethane_1_2_Diol":
        "Ethane-1,2-Diol",
    "Ethenyl_Acetate":
        "Ethenyl Acetate",
    "Hexone":
        "Hexone",
    "Furan_2_5_Dione":
        "Furan-2,5-Dione",
    "3_Methylphenol":
        "3-Methylphenol",
    "Chlorobenzene":
        "Chlorobenzene",
    "Phenol":
        "Phenol",
    "2_Methoxyethanol":
        "2-Methoxyethanol",
    "2_Ethoxyethanol":
        "2-Ethoxyethanol",
    "2_Ethoxyethyl_Acetate":
        "2-Ethoxyethyl Acetate",
    "2_2_Hydroxyethylamino_Ethanol":
        "2-(2-Hydroxyethylamino)Ethanol",
    "2_2_Methoxyethoxy_Ethanol":
        "2-(2-Methoxyethoxy)Ethanol",
    "2_2_Ethoxyethoxy_Ethanol":
        "2-(2-Ethoxyethoxy)Ethanol",
    "2_Butoxyethyl_Acetate":
        "2-Butoxyethyl Acetate",
    "2_2_Ethoxyethoxy_Ethyl_Acetate":
        "2-(2-Ethoxyethoxy)Ethyl Acetate",
    "2_2_2_Hydroxyethoxy_Ethoxy_Ethanol":
        "2-[2-(2-Hydroxyethoxy)Ethoxy]Ethanol",
    "2_2_Butoxyethoxy_Ethanol":
        "2-(2-Butoxyethoxy)Ethanol",
    "2_2_Hexoxyethoxy_Ethanol":
        "2-(2-Hexoxyethoxy)Ethanol",
    "Bis_2_Ethylhexyl_Benzene_1_2_Dicarboxylate":
        "Bis(2-Ethylhexyl) Benzene-1,2-Dicarboxylate",
    "1_2_3_4_5_6_Hexachlorobenzene":
        "1,2,3,4,5,6-Hexachlorobenzene",
    "Benzene_1_2_Diol":
        "Benzene-1,2-Diol",
    "1_2_4_Trichlorobenzene":
        "1,2,4-Trichlorobenzene",
    "1_Methyl_2_4_Dinitrobenzene":
        "1-Methyl-2,4-Dinitrobenzene",
    "N_N_Diethylethanamine":
        "N,N-Diethylethanamine",
    "N_N_Dimethylaniline":
        "N,N-Dimethylaniline",
    "2_Phenoxyethanol":
        "2-Phenoxyethanol",
    "Benzene_1_4_Diol":
        "Benzene-1,4-Diol",
    "1_4_Diethyleneoxide":
        "1,4-Diethyleneoxide",
    "2_2_Butoxyethoxy_Ethyl_Acetate":
        "2-(2-Butoxyethoxy)Ethyl Acetate",
    "2_Chlorobuta_1_3_Diene":
        "2-Chlorobuta-1,3-Diene",
    "Perchloroethylene":
        "Perchloroethylene",
    "Dimethyl_Benzene_1_2_Dicarboxylate":
        "Dimethyl Benzene-1,2-Dicarboxylate",
    "Dibenzofurans":
        "Dibenzofurans",
    "2_Trichloromethylsulfanyl_3A_4_7_7A_Tetrahydroisoindole_1_3_Dione":
        "2-(Trichloromethylsulfanyl)-3A,4,7,7A-Tetrahydroisoindole-1,3-Dione",
    "Ethyl_Prop_2_Enoate":
        "Ethyl Prop-2-Enoate",
    "Azanidylidenemethylideneazanide":
        "Azanidylidenemethylideneazanide",
    "Benzo_E_Pyrene":
        "Benzo[E]Pyrene",
    "Benzo_C_Phenanthrene":
        "Benzo(C)Phenanthrene",
    "Perylene":
        "Perylene",
    "Benzo_G_H_I_Fluoranthene":
        "Benzo(G,H,I)Fluoranthene",
    "Benzo_A_Fluoranthene":
        "Benzo(A)Fluoranthene",
    "Benzo_J_Fluoranthene":
        "Benzo[J]Fluoranthene",
    "Hydrazine":
        "Hydrazine",
    "Carbonyl_Sulfide":
        "Carbonyl Sulfide",
    "2_Chloro_1_Phenylethanone":
        "2-Chloro-1-Phenylethanone",
    "Tert_Butyl_Acetate":
        "Tert-butyl Acetate",
    "1_3_Dichloroprop_1_Ene":
        "1,3-Dichloroprop-1-Ene",
    "2_4_Diisocyanato_1_Methylbenzene":
        "2,4-Diisocyanato-1-Methylbenzene",
    "9_Methyl_Anthracene":
        "9-Methyl Anthracene",
    "1_6_Diisocyanatohexane":
        "1,6-Diisocyanatohexane",
    "1_Methylphenanthrene":
        "1-Methylphenanthrene",
    "1_2_Ethoxyethoxy_2_Methoxyethane":
        "1-(2-Ethoxyethoxy)-2-Methoxyethane",
    "Cresols_Cresylic_Acid_Isomers_And_Mixture":
        "Cresols/Cresylic Acid (Isomers And Mixture)",
    "Polychlorinated_Biphenyls_Aroclors":
        "Polychlorinated Biphenyls (Aroclors)",
    "Trifluralin":
        "Trifluralin",
    "1_Chloro_4_4_Chlorophenyl_Benzene":
        "1-Chloro-4-(4-Chlorophenyl)Benzene",
    "1_2_3_4_5_Pentachloro_6_2_3_4_5_6_Pentachlorophenyl_Benzene":
        "1,2,3,4,5-Pentachloro-6-(2,3,4,5,6-Pentachlorophenyl)Benzene",
    "1_Chloro_2_Phenylbenzene":
        "1-Chloro-2-Phenylbenzene",
    "1_Methylpyrene":
        "1-Methylpyrene",
    "12_Methylbenz_A_Anthracene":
        "12-Methylbenz(A)Anthracene",
    "2_Methylphenanthrene":
        "2-Methylphenanthrene",
    "2_Propoxyethanol":
        "2-Propoxyethanol",
    "5_Methylchrysene":
        "5-Methylchrysene",
    "2_4_Dichloro_1_4_Chlorophenyl_Benzene":
        "2,4-Dichloro-1-(4-Chlorophenyl)Benzene",
    "Beryllium":
        "Beryllium",
    "Tetrachlorotitanium":
        "Tetrachlorotitanium",
    "Chlorane":
        "Chlorane",
    "Fluorane":
        "Fluorane",
    "Sulfane":
        "Sulfane",
    "Phosphane":
        "Phosphane",
    "1_2_3_4_5_Pentachloro_6_Phenylbenzene":
        "1,2,3,4,5-Pentachloro-6-Phenylbenzene",
    "1_2_3_4_5_Pentachloro_6_2_Chlorophenyl_Benzene":
        "1,2,3,4,5-Pentachloro-6-(2-Chlorophenyl)Benzene",
    "2_Chloro_1_4_Dimethoxy_3_Methylanthracene_9_10_Dione":
        "2-Chloro-1,4-Dimethoxy-3-Methylanthracene-9,10-Dione",
    "1_2_3_4_Tetrachloro_5_Phenylbenzene":
        "1,2,3,4-Tetrachloro-5-Phenylbenzene",
    "1_2_3_4_5_Pentachloro_6_2_3_Dichlorophenyl_Benzene":
        "1,2,3,4,5-Pentachloro-6-(2,3-Dichlorophenyl)Benzene",
    "6_Methylchrysene":
        "6-Methylchrysene",
    "Benzofluoranthenes":
        "Benzofluoranthenes",
    "8_Methylbenzo_E_Pyrene":
        "8-Methylbenzo[E]Pyrene",
    'HAP':
        'HazardousAirPollutants',
    'GHG':
        'GreenhouseGas',
    'CAP':
        'CriteriaAirPollutants',
    'Kootenai Tribe of Idaho':
        88183,
    'Nez Perce Tribe of Idaho':
        88182,
    'Shoshone-Bannock Tribes of the Fort Hall Reservation of Idaho':
        88180,
    'Coeur dAlene Tribe of the Coeur dAlene Reservation, Idaho':
        88181,
    'Northern Cheyenne Tribe of the Northern Cheyenne Indian Reservation, Montana':
        88207,
    'Morongo Band of Cahuilla Mission Indians of the Morongo Reservation, California':
        88582,
    'TON':
        'Ton',
    'LB':
        'Pound'
}

replace_source_metadata = {
    "1": "External Combustion",
    "2": "Internal Combustion Engines",
    "3": "Industrial Processes",
    "4": "Chemical Evaporation",
    "4": "Petroleum And Solvent Evaporation",
    "5": "Waste Disposal",
    "6": "MACT Source Categories",
    "7": "Very Misc",
    "21": "Stationary Source Fuel Combustion",
    "22": "Mobile Sources",
    "23": "Industrial Processes",
    "24": "Solvent Utilization",
    "25": "Storage And Transport",
    "26": "Waste Disposal Treatment And Recovery",
    "27": "Natural Sources",
    "28": "Miscellaneous Area Sources",
    "29": "Very Misc",
    "32": "Industrial Processes",
    "33": "LPG Distribution",
    "44": "Brick Kilns",
    "55": "Domestic Ammonia"
}
