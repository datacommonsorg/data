# Copyright 2022 Google LLC
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

replacement_08_11 = {
    'state_and_county_fips_code': 'fips code',
    'pollutant_cd': 'pollutant code',
    'uom': 'emissions uom',
    'total_emissions': 'total emissions',
    'emissions_type_code': 'emissions type code'
}
drop_08_11 = [
    'tribal_name', 'st_usps_cd', 'county_name', 'data_category_cd',
    'description', 'aircraft_engine_type_cd', 'emissions_op_type_code',
    'data_set_short_name'
]
replacement_14 = {
    'state_and_county_fips_code': 'fips code',
    'pollutant_cd': 'pollutant code',
    'uom': 'emissions uom',
    'total_emissions': 'total emissions',
    'emissions_type_code': 'emissions type code'
}
drop_14 = [
    'tribal_name', 'fips_state_code', 'st_usps_cd', 'county_name',
    'data_category', 'emission_operating_type', 'pollutant_desc',
    'emissions_operating_type', 'data_set'
]
replacement_17 = {
    'emissions uom': 'unit',
    'total emissions': 'observation',
    'data set': 'year'
}
drop_17 = [
    'epa region code', 'state', 'fips state code', 'county', 'aetc',
    'reporting period', 'sector', 'tribal name', 'pollutant desc',
    'data category', 'data set'
]
replacement_tribes = {'tribal name': 'fips code'}

drop_tribes = [
    'state', 'fips state code', 'data category', 'reporting period',
    'emissions operating type', 'pollutant desc', 'data set'
]
drop_df = [
    'scc', 'pollutant code', 'emissions type code', 'pollutant type(s)',
    'fips code'
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
        "dcs:Sulfur Dioxide",
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
    "44":"Brick Kilns",
    "55":"Domestic Ammonia",
    "23":"Industrial Processes",
    "32":"Industrial Processes",
    "33":"LPG Distribution",
    "28":"Miscellaneous Area Sources",
    "22":"Mobile Sources",
    "27":"Natural Sources",
    "24":"Solvent Utilization",
    "21":"Stationary Source Fuel Combustion",
    "25":"Storage and Transport",
    "29":"very misc",
    "26":"Waste Disposal, Treatment, and Recovery",
    "4444":"Brick Kilns, Brick Kilns",
    "5555":"Domestic Ammonia, Domestic Ammonia",
    "2301":"Industrial Processes, Chemical Manufacturing: SIC 28",
    "2302":"Industrial Processes, Food and Kindred Products: SIC 20",
    "2303":"Industrial Processes, Primary Metal Production: SIC 33",
    "2304":"Industrial Processes, Secondary Metal Production: SIC 33",
    "2305":"Industrial Processes, Mineral Processes: SIC 32",
    "2306":"Industrial Processes, Petroleum Refining: SIC 29",
    "2307":"Industrial Processes, Wood Products: SIC 24",
    "2308":"Industrial Processes, Rubber/Plastics: SIC 30",
    "2309":"Industrial Processes, Fabricated Metals: SIC 34",
    "2310":"Industrial Processes, Oil and Gas Exploration and Production",
    "2311":"Industrial Processes, Construction: SIC 15 - 17",
    "2312":"Industrial Processes, Machinery: SIC 35",
    "2325":"Industrial Processes, Mining and Quarrying: SIC 10 and SIC 14",
    "2390":"Industrial Processes, In-process Fuel Use",
    "2399":"Industrial Processes, Industrial Processes: NEC",
    "3210":"Industrial Processes, Oil and Gas Exploration and Production",
    "3333":"LPG Distribution, LPG Distribution",
    "2801":"Miscellaneous Area Sources, Agriculture Production - Crops",
    "2801":"Miscellaneous Area Sources, Agriculture Production - Crops - as nonpoint",
    "2802":"Miscellaneous Area Sources, Agricultural Crop Usage",
    "2805":"Miscellaneous Area Sources, Agriculture Production - Livestock",
    "2806":"Miscellaneous Area Sources, Domestic Animals Waste Emissions",
    "2807":"Miscellaneous Area Sources, Wild Animals Waste Emissions",
    "2810":"Miscellaneous Area Sources, Other Combustion",
    "2820":"Miscellaneous Area Sources, Cooling Towers",
    "2830":"Miscellaneous Area Sources, Catastrophic/Accidental Releases",
    "2840":"Miscellaneous Area Sources, Automotive Repair Shops",
    "2841":"Miscellaneous Area Sources, Miscellaneous Repair Shops",
    "2850":"Miscellaneous Area Sources, Health Services",
    "2851":"Miscellaneous Area Sources, Laboratories",
    "2861":"Miscellaneous Area Sources, Fluorescent Lamp Breakage",
    "2862":"Miscellaneous Area Sources, Swimming Pools",
    "2201":"Mobile Sources, Highway Vehicles - Gasoline",
    "2202":"Mobile Sources, Highway Vehicles - Diesel",
    "2203":"Mobile Sources, Highway Vehicles - Compressed Natural Gas (CNG)",
    "2204":"Mobile Sources, Highway Vehicles - Liquefied Petroleum Gas (LPG)",
    "2205":"Mobile Sources, Highway Vehicles - Ethanol (E-85)",
    "2209":"Mobile Sources, Highway Vehicles - Electricity",
    "2222":"Mobile Sources, Border Crossings",
    "2230":"Mobile Sources, Highway Vehicles - Diesel",
    "2260":"Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke",
    "2260":"Mobile Sources, Off-highway Vehicle Gasoline",
    "2265":"Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke",
    "2265":"Mobile Sources, Off-highway Vehicle Gasoline",
    "2267":"Mobile Sources, LPG",
    "2267":"Mobile Sources, Off-highway Vehicle LPG",
    "2268":"Mobile Sources, CNG",
    "2268":"Mobile Sources, Off-highway Vehicle CNG",
    "2270":"Mobile Sources, Off-highway Vehicle Diesel",
    "2275":"Mobile Sources, Aircraft",
    "2280":"Mobile Sources, Marine Vessels, Commercial",
    "2282":"Mobile Sources, Pleasure Craft",
    "2283":"Mobile Sources, Marine Vessels, Military",
    "2285":"Mobile Sources, Railroad Equipment",
    "2294":"Mobile Sources, Paved Roads",
    "2296":"Mobile Sources, Unpaved Roads",
    "2297":"Mobile Sources, unknown non-US source",
    "2701":"Natural Sources, Biogenic",
    "2401":"Solvent Utilization, Surface Coating",
    "2402":"Solvent Utilization, Paint Strippers",
    "2415":"Solvent Utilization, Degreasing",
    "2420":"Solvent Utilization, Dry Cleaning",
    "2425":"Solvent Utilization, Graphic Arts",
    "2430":"Solvent Utilization, Rubber/Plastics",
    "2440":"Solvent Utilization, Miscellaneous Industrial",
    "2460":"Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial",
    "2461":"Solvent Utilization, Miscellaneous Non-industrial: Commercial",
    "2461":"Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial",
    "2465":"Solvent Utilization, Miscellaneous Non-industrial: Consumer",
    "2495":"Solvent Utilization, All Solvent User Categories",
    "2101":"Stationary Source Fuel Combustion, Electric Utility",
    "2102":"Stationary Source Fuel Combustion, Industrial",
    "2103":"Stationary Source Fuel Combustion, Commercial/Institutional",
    "2104":"Stationary Source Fuel Combustion, Residential",
    "2199":"Stationary Source Fuel Combustion, Total Area Source Fuel Combustion",
    "2501":"Storage and Transport, Petroleum and Petroleum Product Storage",
    "2505":"Storage and Transport, Petroleum and Petroleum Product Transport",
    "2510":"Storage and Transport, Organic Chemical Storage",
    "2515":"Storage and Transport, Organic Chemical Transport",
    "2520":"Storage and Transport, Inorganic Chemical Storage",
    "2525":"Storage and Transport, Inorganic Chemical Transport",
    "2530":"Storage and Transport, Bulk Materials Storage",
    "2535":"Storage and Transport, Bulk Materials Transport",
    "2999":"very misc, holding scc",
    "2601":"Waste Disposal, Treatment, and Recovery, On-site Incineration",
    "2610":"Waste Disposal, Treatment, and Recovery, Open Burning",
    "2620":"Waste Disposal, Treatment, and Recovery, Landfills",
    "2630":"Waste Disposal, Treatment, and Recovery, Wastewater Treatment",
    "2635":"Waste Disposal, Treatment, and Recovery, Soil and Groundwater Remediation",
    "2640":"Waste Disposal, Treatment, and Recovery, TSDFs",
    "2650":"Waste Disposal, Treatment, and Recovery, Scrap and Waste Materials",
    "2660":"Waste Disposal, Treatment, and Recovery, Leaking Underground Storage Tanks",
    "2670":"Waste Disposal, Treatment, and Recovery, Munitions Detonation",
    "2680":"Waste Disposal, Treatment, and Recovery, Composting",
    "4444444":"Brick Kilns, Brick Kilns, Brick Kilns",
    "5555555":"Domestic Ammonia, Domestic Ammonia, Domestic Ammonia",
    "2301000":"Industrial Processes, Chemical Manufacturing: SIC 28, All Processes",
    "2301010":"Industrial Processes, Chemical Manufacturing: SIC 28, Industrial Inorganic Chemical Manufacturing",
    "2301020":"Industrial Processes, Chemical Manufacturing: SIC 28, Process Emissions from Synthetic Fibers Manuf (NAPAP cat. 107)",
    "2301030":"Industrial Processes, Chemical Manufacturing: SIC 28, Process Emissions from Pharmaceutical Manuf (NAPAP cat. 106)",
    "2301040":"Industrial Processes, Chemical Manufacturing: SIC 28, Fugitive Emissions from Synthetic Organic Chem Manuf (NAPAP cat. 102)",
    "2301050":"Industrial Processes, Chemical Manufacturing: SIC 28, Plastics Production",
    "2302000":"Industrial Processes, Food and Kindred Products: SIC 20, All Processes",
    "2302002":"Industrial Processes, Food and Kindred Products: SIC 20, Commercial Cooking - Charbroiling",
    "2302003":"Industrial Processes, Food and Kindred Products: SIC 20, Commercial Cooking - Frying",
    "2302010":"Industrial Processes, Food and Kindred Products: SIC 20, Meat Products",
    "2302040":"Industrial Processes, Food and Kindred Products: SIC 20, Grain Mill Products",
    "2302050":"Industrial Processes, Food and Kindred Products: SIC 20, Bakery Products",
    "2302070":"Industrial Processes, Food and Kindred Products: SIC 20, Fermentation/Beverages",
    "2302080":"Industrial Processes, Food and Kindred Products: SIC 20, Miscellaneous Food and Kindred Products",
    "2303000":"Industrial Processes, Primary Metal Production: SIC 33, All Processes",
    "2303020":"Industrial Processes, Primary Metal Production: SIC 33, Iron and Steel Foundries",
    "2304000":"Industrial Processes, Secondary Metal Production: SIC 33, All Processes",
    "2304050":"Industrial Processes, Secondary Metal Production: SIC 33, Nonferrous Foundries (Castings)",
    "2305000":"Industrial Processes, Mineral Processes: SIC 32, All Processes",
    "2305070":"Industrial Processes, Mineral Processes: SIC 32, Concrete, Gypsum, Plaster Products",
    "2305080":"Industrial Processes, Mineral Processes: SIC 32, Cut Stone and Stone Products",
    "2306000":"Industrial Processes, Petroleum Refining: SIC 29, All Processes",
    "2306010":"Industrial Processes, Petroleum Refining: SIC 29, Asphalt Mixing Plants and Paving/Roofing Materials",
    "2307000":"Industrial Processes, Wood Products: SIC 24, All Processes",
    "2307010":"Industrial Processes, Wood Products: SIC 24, Logging Operations",
    "2307020":"Industrial Processes, Wood Products: SIC 24, Sawmills/Planing Mills",
    "2307030":"Industrial Processes, Wood Products: SIC 24, Millwork, Plywood, and Structural Members",
    "2307060":"Industrial Processes, Wood Products: SIC 24, Miscellaneous Wood Products",
    "2308000":"Industrial Processes, Rubber/Plastics: SIC 30, All Processes",
    "2309000":"Industrial Processes, Fabricated Metals: SIC 34, All Processes",
    "2309010":"Industrial Processes, Fabricated Metals: SIC 34, Precious Metals Recovery",
    "2309100":"Industrial Processes, Fabricated Metals: SIC 34, Coating, Engraving, and Allied Services",
    "2310000":"Industrial Processes, Oil and Gas Exploration and Production, All Processes",
    "2310001":"Industrial Processes, Oil and Gas Exploration and Production, All Processes : On-shore",
    "2310002":"Industrial Processes, Oil and Gas Exploration and Production, Off-Shore Oil And Gas Production",
    "2310010":"Industrial Processes, Oil and Gas Exploration and Production, Crude Petroleum",
    "2310011":"Industrial Processes, Oil and Gas Exploration and Production, On-Shore Oil Production",
    "2310012":"Industrial Processes, Oil and Gas Exploration and Production, Off-Shore Oil Production",
    "2310020":"Industrial Processes, Oil and Gas Exploration and Production, Natural Gas",
    "2310021":"Industrial Processes, Oil and Gas Exploration and Production, On-Shore Gas Production",
    "2310022":"Industrial Processes, Oil and Gas Exploration and Production, Off-Shore Gas Production",
    "2310023":"Industrial Processes, Oil and Gas Exploration and Production, Coal Bed Methane Natural Gas",
    "2310030":"Industrial Processes, Oil and Gas Exploration and Production, Natural Gas Liquids",
    "2310031":"Industrial Processes, Oil and Gas Exploration and Production, Natural Gas Liquids : On-shore",
    "2310032":"Industrial Processes, Oil and Gas Exploration and Production, Natural Gas Liquids : Off-shore",
    "2310111":"Industrial Processes, Oil and Gas Exploration and Production, On-Shore Oil Exploration",
    "2310112":"Industrial Processes, Oil and Gas Exploration and Production, Off-Shore Oil Exploration",
    "2310121":"Industrial Processes, Oil and Gas Exploration and Production, On-Shore Gas Exploration",
    "2310122":"Industrial Processes, Oil and Gas Exploration and Production, Off-Shore Gas Exploration",
    "2310300":"Industrial Processes, Oil and Gas Exploration and Production, All Processes - Conventional",
    "2310321":"Industrial Processes, Oil and Gas Exploration and Production, On-Shore Gas Production - Conventional",
    "2310400":"Industrial Processes, Oil and Gas Exploration and Production, All Processes - Unconventional",
    "2310421":"Industrial Processes, Oil and Gas Exploration and Production, On-Shore Gas Production - Unconventional",
    "2311000":"Industrial Processes, Construction: SIC 15 - 17, All Processes",
    "2311010":"Industrial Processes, Construction: SIC 15 - 17, Residential",
    "2311020":"Industrial Processes, Construction: SIC 15 - 17, Industrial/Commercial/Institutional",
    "2311030":"Industrial Processes, Construction: SIC 15 - 17, Road Construction",
    "2311040":"Industrial Processes, Construction: SIC 15 - 17, Special Trade Construction",
    "2312000":"Industrial Processes, Machinery: SIC 35, All Processes",
    "2312050":"Industrial Processes, Machinery: SIC 35, Metalworking Machinery: Tool and Die Maker",
    "2325000":"Industrial Processes, Mining and Quarrying: SIC 10 and SIC 14, All Processes",
    "2325010":"Industrial Processes, Mining and Quarrying: SIC 10 and SIC 14, Dimension Stone",
    "2325020":"Industrial Processes, Mining and Quarrying: SIC 10 and SIC 14, Crushed and Broken Stone",
    "2325030":"Industrial Processes, Mining and Quarrying: SIC 10 and SIC 14, Sand and Gravel",
    "2325040":"Industrial Processes, Mining and Quarrying: SIC 10 and SIC 14, Clay, Ceramic, and Refractory",
    "2325050":"Industrial Processes, Mining and Quarrying: SIC 10 and SIC 14, Chemical and Fertilizer Materials",
    "2325060":"Industrial Processes, Mining and Quarrying: SIC 10 and SIC 14, Lead Ore Mining and Milling",
    "2390001":"Industrial Processes, In-process Fuel Use, Anthracite Coal",
    "2390002":"Industrial Processes, In-process Fuel Use, Bituminous/Subbituminous Coal",
    "2390004":"Industrial Processes, In-process Fuel Use, Distillate Oil",
    "2390005":"Industrial Processes, In-process Fuel Use, Residual Oil",
    "2390006":"Industrial Processes, In-process Fuel Use, Natural Gas",
    "2390007":"Industrial Processes, In-process Fuel Use, Liquified Petroleum Gas (LPG)",
    "2390008":"Industrial Processes, In-process Fuel Use, Wood",
    "2390009":"Industrial Processes, In-process Fuel Use, Coke",
    "2390010":"Industrial Processes, In-process Fuel Use, Process Gas",
    "2399000":"Industrial Processes, Industrial Processes: NEC, Industrial Processes: NEC",
    "2399010":"Industrial Processes, Industrial Processes: NEC, Refrigerant Losses",
    "3210000":"Industrial Processes, Oil and Gas Exploration and Production, All Processes",
    "3333333":"LPG Distribution, LPG Distribution, LPG Distribution",
    "2801000":"Miscellaneous Area Sources, Agriculture Production - Crops, Agriculture - Crops",
    "2801500":"Miscellaneous Area Sources, Agriculture Production - Crops, Agricultural Field Burning - whole field set on fire",
    "2801500":"Miscellaneous Area Sources, Agriculture Production - Crops - as nonpoint, Agricultural Field Burning - whole field set on fire",
    "2801501":"Miscellaneous Area Sources, Agriculture Production - Crops - as nonpoint, Agricultural Propaning - tractor-pulled burners to burn stubble only",
    "2801502":"Miscellaneous Area Sources, Agriculture Production - Crops - as nonpoint, Agricultural Stack Burning - straw stacks moved from field for burning",
    "2801520":"Miscellaneous Area Sources, Agriculture Production - Crops, Orchard Heaters",
    "2801530":"Miscellaneous Area Sources, Agriculture Production - Crops, Country Grain Elevators",
    "2801600":"Miscellaneous Area Sources, Agriculture Production - Crops, Country Grain Elevators",
    "2801600":"Miscellaneous Area Sources, Agriculture Production - Crops, Agricultural Field Burning - Pile Burning",
    "2801700":"Miscellaneous Area Sources, Agriculture Production - Crops, Fertilizer Application",
    "2802004":"Miscellaneous Area Sources, Agricultural Crop Usage, Agriculture Silage",
    "2805000":"Miscellaneous Area Sources, Agriculture Production - Livestock, Agriculture - Livestock",
    "2805001":"Miscellaneous Area Sources, Agriculture Production - Livestock, Dust kicked up by Livestock",
    "2805001":"Miscellaneous Area Sources, Agriculture Production - Livestock, Beef cattle - finishing operations on feedlots (drylots)",
    "2805001":"Miscellaneous Area Sources, Agriculture Production - Livestock, Beef cattle waste",
    "2805002":"Miscellaneous Area Sources, Agriculture Production - Livestock, Beef cattle production composite",
    "2805003":"Miscellaneous Area Sources, Agriculture Production - Livestock, Beef cattle waste",
    "2805005":"Miscellaneous Area Sources, Agriculture Production - Livestock, Poultry Operations",
    "2805007":"Miscellaneous Area Sources, Agriculture Production - Livestock, Poultry Waste",
    "2805008":"Miscellaneous Area Sources, Agriculture Production - Livestock, Poultry production - layers with wet manure management systems",
    "2805009":"Miscellaneous Area Sources, Agriculture Production - Livestock, Poultry production - broilers",
    "2805010":"Miscellaneous Area Sources, Agriculture Production - Livestock, Poultry production - turkeys",
    "2805015":"Miscellaneous Area Sources, Agriculture Production - Livestock, Hog Operations",
    "2805018":"Miscellaneous Area Sources, Agriculture Production - Livestock, Dairy cattle composite",
    "2805019":"Miscellaneous Area Sources, Agriculture Production - Livestock, Dairy Cattle Waste",
    "2805020":"Miscellaneous Area Sources, Agriculture Production - Livestock, Cattle and Calves Waste Emissions",
    "2805021":"Miscellaneous Area Sources, Agriculture Production - Livestock, Dairy cattle - scrape dairy",
    "2805022":"Miscellaneous Area Sources, Agriculture Production - Livestock, Dairy cattle - deep pit dairy",
    "2805023":"Miscellaneous Area Sources, Agriculture Production - Livestock, Dairy cattle - drylot/pasture dairy",
    "2805025":"Miscellaneous Area Sources, Agriculture Production - Livestock, Swine production composite",
    "2805030":"Miscellaneous Area Sources, Agriculture Production - Livestock, Poultry Waste Emissions",
    "2805035":"Miscellaneous Area Sources, Agriculture Production - Livestock, Horses and Ponies Waste Emissions",
    "2805039":"Miscellaneous Area Sources, Agriculture Production - Livestock, Swine Waste",
    "2805040":"Miscellaneous Area Sources, Agriculture Production - Livestock, Sheep and Lambs Waste Emissions",
    "2805045":"Miscellaneous Area Sources, Agriculture Production - Livestock, Goats Waste Emissions",
    "2805047":"Miscellaneous Area Sources, Agriculture Production - Livestock, Swine production - deep-pit house operations (unspecified animal age)",
    "2805053":"Miscellaneous Area Sources, Agriculture Production - Livestock, Swine production - outdoor operations (unspecified animal age)",
    "2805100":"Miscellaneous Area Sources, Agriculture Production - Livestock, Dust kicked up by Livestock",
    "2806010":"Miscellaneous Area Sources, Domestic Animals Waste Emissions, Cats",
    "2806015":"Miscellaneous Area Sources, Domestic Animals Waste Emissions, Dogs",
    "2807020":"Miscellaneous Area Sources, Wild Animals Waste Emissions, Bears",
    "2807025":"Miscellaneous Area Sources, Wild Animals Waste Emissions, Elk",
    "2807030":"Miscellaneous Area Sources, Wild Animals Waste Emissions, Deer",
    "2807035":"Miscellaneous Area Sources, Wild Animals Waste Emissions, Squirrels",
    "2807040":"Miscellaneous Area Sources, Wild Animals Waste Emissions, Birds",
    "2807045":"Miscellaneous Area Sources, Wild Animals Waste Emissions, Wolves",
    "2810003":"Miscellaneous Area Sources, Other Combustion, Cigarette Smoke",
    "2810005":"Miscellaneous Area Sources, Other Combustion, Managed Burning, Slash (Logging Debris)",
    "2810010":"Miscellaneous Area Sources, Other Combustion, Human Perspiration and Respiration",
    "2810014":"Miscellaneous Area Sources, Other Combustion, Prescribed Burning",
    "2810015":"Miscellaneous Area Sources, Other Combustion, Prescribed Forest Burning",
    "2810020":"Miscellaneous Area Sources, Other Combustion, Prescribed Rangeland Burning",
    "2810025":"Miscellaneous Area Sources, Other Combustion, Residential Grilling (see 23-02-002-xxx for Commercial)",
    "2810030":"Miscellaneous Area Sources, Other Combustion, Structure Fires",
    "2810035":"Miscellaneous Area Sources, Other Combustion, Firefighting Training",
    "2810040":"Miscellaneous Area Sources, Other Combustion, Aircraft/Rocket Engine Firing and Testing",
    "2810050":"Miscellaneous Area Sources, Other Combustion, Motor Vehicle Fires",
    "2810060":"Miscellaneous Area Sources, Other Combustion, Cremation",
    "2810090":"Miscellaneous Area Sources, Other Combustion, Open Fire",
    "2820000":"Miscellaneous Area Sources, Cooling Towers, All Types",
    "2820010":"Miscellaneous Area Sources, Cooling Towers, Process Cooling Towers",
    "2820020":"Miscellaneous Area Sources, Cooling Towers, Comfort Cooling Towers",
    "2830000":"Miscellaneous Area Sources, Catastrophic/Accidental Releases, All Catastrophic/Accidential Releases",
    "2830001":"Miscellaneous Area Sources, Catastrophic/Accidental Releases, Industrial Accidents",
    "2830010":"Miscellaneous Area Sources, Catastrophic/Accidental Releases, Transportation Accidents",
    "2840000":"Miscellaneous Area Sources, Automotive Repair Shops, Automotive Repair Shops",
    "2840010":"Miscellaneous Area Sources, Automotive Repair Shops, Auto Top and Body Repair",
    "2840020":"Miscellaneous Area Sources, Automotive Repair Shops, Automotive Exhaust Repair Shops",
    "2840030":"Miscellaneous Area Sources, Automotive Repair Shops, Tire Retreading and Repair Shops",
    "2841000":"Miscellaneous Area Sources, Miscellaneous Repair Shops, Miscellaneous Repair Shops",
    "2841010":"Miscellaneous Area Sources, Miscellaneous Repair Shops, Welding Repair Shops",
    "2850000":"Miscellaneous Area Sources, Health Services, Hospitals",
    "2850001":"Miscellaneous Area Sources, Health Services, Dental Alloy Production",
    "2851001":"Miscellaneous Area Sources, Laboratories, Bench Scale Reagents",
    "2861000":"Miscellaneous Area Sources, Fluorescent Lamp Breakage, Fluorescent Lamp Breakage",
    "2862000":"Miscellaneous Area Sources, Swimming Pools, Total (Commercial, Residential, Public)",
    "2862001":"Miscellaneous Area Sources, Swimming Pools, Public",
    "2862002":"Miscellaneous Area Sources, Swimming Pools, Residential",
    "2201000":"Mobile Sources, Highway Vehicles - Gasoline, Refueling",
    "2201001":"Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV)",
    "2201020":"Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5)",
    "2201040":"Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5)",
    "2201060":"Mobile Sources, Highway Vehicles - Gasoline, NOT USED - Previously all LDGT (1&2) under M5",
    "2201070":"Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV)",
    "2201080":"Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC)",
    "2201110":"Mobile Sources, Highway Vehicles - Gasoline, Motorcycle",
    "2201210":"Mobile Sources, Highway Vehicles - Gasoline, Passenger Car",
    "2201310":"Mobile Sources, Highway Vehicles - Gasoline, Passenger Truck",
    "2201320":"Mobile Sources, Highway Vehicles - Gasoline, Light Commercial Truck",
    "2201410":"Mobile Sources, Highway Vehicles - Gasoline, Other Buses",
    "2201420":"Mobile Sources, Highway Vehicles - Gasoline, Transit Bus",
    "2201430":"Mobile Sources, Highway Vehicles - Gasoline, School Bus",
    "2201510":"Mobile Sources, Highway Vehicles - Gasoline, Refuse Truck",
    "2201520":"Mobile Sources, Highway Vehicles - Gasoline, Single Unit Short-haul Truck",
    "2201530":"Mobile Sources, Highway Vehicles - Gasoline, Single Unit Long-haul Truck",
    "2201540":"Mobile Sources, Highway Vehicles - Gasoline, Motor Home",
    "2201610":"Mobile Sources, Highway Vehicles - Gasoline, Combination Short-haul Truck",
    "2201620":"Mobile Sources, Highway Vehicles - Gasoline, Combination Long-haul Truck",
    "2202000":"Mobile Sources, Highway Vehicles - Diesel, Refueling",
    "2202110":"Mobile Sources, Highway Vehicles - Diesel, Motorcycle",
    "2202210":"Mobile Sources, Highway Vehicles - Diesel, Passenger Car",
    "2202310":"Mobile Sources, Highway Vehicles - Diesel, Passenger Truck",
    "2202320":"Mobile Sources, Highway Vehicles - Diesel, Light Commercial Truck",
    "2202410":"Mobile Sources, Highway Vehicles - Diesel, Other Buses",
    "2202420":"Mobile Sources, Highway Vehicles - Diesel, Transit Bus",
    "2202430":"Mobile Sources, Highway Vehicles - Diesel, School Bus",
    "2202510":"Mobile Sources, Highway Vehicles - Diesel, Refuse Truck",
    "2202520":"Mobile Sources, Highway Vehicles - Diesel, Single Unit Short-haul Truck",
    "2202530":"Mobile Sources, Highway Vehicles - Diesel, Single Unit Long-haul Truck",
    "2202540":"Mobile Sources, Highway Vehicles - Diesel, Motor Home",
    "2202610":"Mobile Sources, Highway Vehicles - Diesel, Combination Short-haul Truck",
    "2202620":"Mobile Sources, Highway Vehicles - Diesel, Combination Long-haul Truck",
    "2203000":"Mobile Sources, Highway Vehicles - Compressed Natural Gas (CNG), Refueling",
    "2203110":"Mobile Sources, Highway Vehicles - Compressed Natural Gas (CNG), Motorcycle",
    "2203210":"Mobile Sources, Highway Vehicles - Compressed Natural Gas (CNG), Passenger Car",
    "2203310":"Mobile Sources, Highway Vehicles - Compressed Natural Gas (CNG), Passenger Truck",
    "2203320":"Mobile Sources, Highway Vehicles - Compressed Natural Gas (CNG), Light Commercial Truck",
    "2203410":"Mobile Sources, Highway Vehicles - Compressed Natural Gas (CNG), Other Buses",
    "2203420":"Mobile Sources, Highway Vehicles - Compressed Natural Gas (CNG), Transit Bus",
    "2203430":"Mobile Sources, Highway Vehicles - Compressed Natural Gas (CNG), School Bus",
    "2203510":"Mobile Sources, Highway Vehicles - Compressed Natural Gas (CNG), Refuse Truck",
    "2203520":"Mobile Sources, Highway Vehicles - Compressed Natural Gas (CNG), Single Unit Short-haul Truck",
    "2203530":"Mobile Sources, Highway Vehicles - Compressed Natural Gas (CNG), Single Unit Long-haul Truck",
    "2203540":"Mobile Sources, Highway Vehicles - Compressed Natural Gas (CNG), Motor Home",
    "2203610":"Mobile Sources, Highway Vehicles - Compressed Natural Gas (CNG), Combination Short-haul Truck",
    "2203620":"Mobile Sources, Highway Vehicles - Compressed Natural Gas (CNG), Combination Long-haul Truck",
    "2204000":"Mobile Sources, Highway Vehicles - Liquefied Petroleum Gas (LPG), Refueling",
    "2204110":"Mobile Sources, Highway Vehicles - Liquefied Petroleum Gas (LPG), Motorcycle",
    "2204210":"Mobile Sources, Highway Vehicles - Liquefied Petroleum Gas (LPG), Passenger Car",
    "2204310":"Mobile Sources, Highway Vehicles - Liquefied Petroleum Gas (LPG), Passenger Truck",
    "2204320":"Mobile Sources, Highway Vehicles - Liquefied Petroleum Gas (LPG), Light Commercial Truck",
    "2204410":"Mobile Sources, Highway Vehicles - Liquefied Petroleum Gas (LPG), Other Buses",
    "2204420":"Mobile Sources, Highway Vehicles - Liquefied Petroleum Gas (LPG), Transit Bus",
    "2204430":"Mobile Sources, Highway Vehicles - Liquefied Petroleum Gas (LPG), School Bus",
    "2204510":"Mobile Sources, Highway Vehicles - Liquefied Petroleum Gas (LPG), Refuse Truck",
    "2204520":"Mobile Sources, Highway Vehicles - Liquefied Petroleum Gas (LPG), Single Unit Short-haul Truck",
    "2204530":"Mobile Sources, Highway Vehicles - Liquefied Petroleum Gas (LPG), Single Unit Long-haul Truck",
    "2204540":"Mobile Sources, Highway Vehicles - Liquefied Petroleum Gas (LPG), Motor Home",
    "2204610":"Mobile Sources, Highway Vehicles - Liquefied Petroleum Gas (LPG), Combination Short-haul Truck",
    "2204620":"Mobile Sources, Highway Vehicles - Liquefied Petroleum Gas (LPG), Combination Long-haul Truck",
    "2205000":"Mobile Sources, Highway Vehicles - Ethanol (E-85), Refueling",
    "2205110":"Mobile Sources, Highway Vehicles - Ethanol (E-85), Motorcycle",
    "2205210":"Mobile Sources, Highway Vehicles - Ethanol (E-85), Passenger Car",
    "2205310":"Mobile Sources, Highway Vehicles - Ethanol (E-85), Passenger Truck",
    "2205320":"Mobile Sources, Highway Vehicles - Ethanol (E-85), Light Commercial Truck",
    "2205410":"Mobile Sources, Highway Vehicles - Ethanol (E-85), Other Buses",
    "2205420":"Mobile Sources, Highway Vehicles - Ethanol (E-85), Transit Bus",
    "2205430":"Mobile Sources, Highway Vehicles - Ethanol (E-85), School Bus",
    "2205510":"Mobile Sources, Highway Vehicles - Ethanol (E-85), Refuse Truck",
    "2205520":"Mobile Sources, Highway Vehicles - Ethanol (E-85), Single Unit Short-haul Truck",
    "2205530":"Mobile Sources, Highway Vehicles - Ethanol (E-85), Single Unit Long-haul Truck",
    "2205540":"Mobile Sources, Highway Vehicles - Ethanol (E-85), Motor Home",
    "2205610":"Mobile Sources, Highway Vehicles - Ethanol (E-85), Combination Short-haul Truck",
    "2205620":"Mobile Sources, Highway Vehicles - Ethanol (E-85), Combination Long-haul Truck",
    "2209000":"Mobile Sources, Highway Vehicles - Electricity, Refueling",
    "2209110":"Mobile Sources, Highway Vehicles - Electricity, Motorcycle",
    "2209210":"Mobile Sources, Highway Vehicles - Electricity, Passenger Car",
    "2209310":"Mobile Sources, Highway Vehicles - Electricity, Passenger Truck",
    "2209320":"Mobile Sources, Highway Vehicles - Electricity, Light Commercial Truck",
    "2209410":"Mobile Sources, Highway Vehicles - Electricity, Other Buses",
    "2209420":"Mobile Sources, Highway Vehicles - Electricity, Transit Bus",
    "2209430":"Mobile Sources, Highway Vehicles - Electricity, School Bus",
    "2209510":"Mobile Sources, Highway Vehicles - Electricity, Refuse Truck",
    "2209520":"Mobile Sources, Highway Vehicles - Electricity, Single Unit Short-haul Truck",
    "2209530":"Mobile Sources, Highway Vehicles - Electricity, Single Unit Long-haul Truck",
    "2209540":"Mobile Sources, Highway Vehicles - Electricity, Motor Home",
    "2209610":"Mobile Sources, Highway Vehicles - Electricity, Combination Short-haul Truck",
    "2209620":"Mobile Sources, Highway Vehicles - Electricity, Combination Long-haul Truck",
    "2222222":"Mobile Sources, Border Crossings, Border Crossings",
    "2230001":"Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV)",
    "2230060":"Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT)",
    "2230070":"Mobile Sources, Highway Vehicles - Diesel, All HDDV including Buses (use subdivisions -071 thru -075 if possible)",
    "2230071":"Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 2B",
    "2230072":"Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 3, 4, & 5",
    "2230073":"Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 6 & 7",
    "2230074":"Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 8A & 8B",
    "2230075":"Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Buses (School & Transit)",
    "2260000":"Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, 2-Stroke Gasoline except Rail and Marine",
    "2260001":"Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Recreational Equipment",
    "2260001":"Mobile Sources, Off-highway Vehicle Gasoline, Recreational Equipment",
    "2260002":"Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Construction and Mining Equipment",
    "2260002":"Mobile Sources, Off-highway Vehicle Gasoline, Construction Equipment",
    "2260003":"Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Industrial Equipment",
    "2260003":"Mobile Sources, Off-highway Vehicle Gasoline, Industrial Equipment",
    "2260004":"Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Lawn and Garden Equipment",
    "2260004":"Mobile Sources, Off-highway Vehicle Gasoline, Lawn and Garden Equipment",
    "2260005":"Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Agricultural Equipment",
    "2260005":"Mobile Sources, Off-highway Vehicle Gasoline, Agricultural Equipment",
    "2260006":"Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Commercial Equipment",
    "2260006":"Mobile Sources, Off-highway Vehicle Gasoline, Commercial Equipment",
    "2260007":"Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Logging Equipment",
    "2260007":"Mobile Sources, Off-highway Vehicle Gasoline, Logging Equipment",
    "2260008":"Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Airport Ground Support Equipment",
    "2260009":"Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Underground Mining Equipment",
    "2260010":"Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Industrial Equipment",
    "2265000":"Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, 4-Stroke Gasoline except Rail and Marine",
    "2265001":"Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Recreational Equipment",
    "2265001":"Mobile Sources, Off-highway Vehicle Gasoline, Recreational Equipment",
    "2265002":"Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Construction and Mining Equipment",
    "2265002":"Mobile Sources, Off-highway Vehicle Gasoline, Construction Equipment",
    "2265003":"Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Industrial Equipment",
    "2265003":"Mobile Sources, Off-highway Vehicle Gasoline, Industrial Equipment",
    "2265004":"Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Lawn and Garden Equipment",
    "2265004":"Mobile Sources, Off-highway Vehicle Gasoline, Lawn and Garden Equipment",
    "2265005":"Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Agricultural Equipment",
    "2265005":"Mobile Sources, Off-highway Vehicle Gasoline, Agricultural Equipment",
    "2265006":"Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Commercial Equipment",
    "2265006":"Mobile Sources, Off-highway Vehicle Gasoline, Commercial Equipment",
    "2265007":"Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Logging Equipment",
    "2265007":"Mobile Sources, Off-highway Vehicle Gasoline, Logging Equipment",
    "2265008":"Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Airport Ground Support Equipment",
    "2265009":"Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Underground Mining Equipment",
    "2265010":"Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Industrial Equipment",
    "2265010":"Mobile Sources, Off-highway Vehicle Gasoline, Industrial Equipment",
    "2267000":"Mobile Sources, LPG, LPG Equipment except Rail and Marine",
    "2267001":"Mobile Sources, LPG, Recreational Equipment",
    "2267001":"Mobile Sources, Off-highway Vehicle LPG, Recreational Equipment",
    "2267002":"Mobile Sources, LPG, Construction and Mining Equipment",
    "2267002":"Mobile Sources, Off-highway Vehicle LPG, Construction Equipment",
    "2267003":"Mobile Sources, LPG, Industrial Equipment",
    "2267003":"Mobile Sources, Off-highway Vehicle LPG, Industrial Equipment",
    "2267004":"Mobile Sources, LPG, Lawn and Garden Equipment",
    "2267004":"Mobile Sources, Off-highway Vehicle LPG, Lawn and Garden Equipment",
    "2267005":"Mobile Sources, LPG, Agricultural Equipment",
    "2267005":"Mobile Sources, Off-highway Vehicle LPG, Agricultural Equipment",
    "2267006":"Mobile Sources, LPG, Commercial Equipment",
    "2267006":"Mobile Sources, Off-highway Vehicle LPG, Commercial Equipment",
    "2267007":"Mobile Sources, LPG, Logging Equipment",
    "2267007":"Mobile Sources, Off-highway Vehicle LPG, Logging Equipment",
    "2267009":"Mobile Sources, LPG, Underground Mining Equipment",
    "2267010":"Mobile Sources, LPG, Industrial Equipment",
    "2268000":"Mobile Sources, CNG, CNG Equipment except Rail and Marine",
    "2268001":"Mobile Sources, CNG, Recreational Equipment",
    "2268002":"Mobile Sources, CNG, Construction and Mining Equipment",
    "2268002":"Mobile Sources, Off-highway Vehicle CNG, Construction Equipment",
    "2268003":"Mobile Sources, CNG, Industrial Equipment",
    "2268003":"Mobile Sources, Off-highway Vehicle CNG, Industrial Equipment",
    "2268004":"Mobile Sources, CNG, Lawn and Garden Equipment",
    "2268004":"Mobile Sources, Off-highway Vehicle CNG, Lawn and Garden Equipment",
    "2268005":"Mobile Sources, CNG, Agricultural Equipment",
    "2268005":"Mobile Sources, Off-highway Vehicle CNG, Agricultural Equipment",
    "2268006":"Mobile Sources, CNG, Commercial Equipment",
    "2268006":"Mobile Sources, Off-highway Vehicle CNG, Commercial Equipment",
    "2268007":"Mobile Sources, CNG, Logging Equipment",
    "2268007":"Mobile Sources, Off-highway Vehicle CNG, Logging Equipment",
    "2268009":"Mobile Sources, CNG, Underground Mining Equipment",
    "2268010":"Mobile Sources, CNG, Industrial Equipment",
    "2268010":"Mobile Sources, Off-highway Vehicle CNG, Industrial Equipment",
    "2270000":"Mobile Sources, Off-highway Vehicle Diesel, Compression Ignition Equipment except Rail and Marine",
    "2270001":"Mobile Sources, Off-highway Vehicle Diesel, Recreational Equipment",
    "2270002":"Mobile Sources, Off-highway Vehicle Diesel, Construction and Mining Equipment",
    "2270002":"Mobile Sources, Off-highway Vehicle Diesel, Construction Equipment",
    "2270003":"Mobile Sources, Off-highway Vehicle Diesel, Industrial Equipment",
    "2270004":"Mobile Sources, Off-highway Vehicle Diesel, Lawn and Garden Equipment",
    "2270005":"Mobile Sources, Off-highway Vehicle Diesel, Agricultural Equipment",
    "2270006":"Mobile Sources, Off-highway Vehicle Diesel, Commercial Equipment",
    "2270007":"Mobile Sources, Off-highway Vehicle Diesel, Logging Equipment",
    "2270008":"Mobile Sources, Off-highway Vehicle Diesel, Airport Ground Support Equipment",
    "2270009":"Mobile Sources, Off-highway Vehicle Diesel, Underground Mining Equipment",
    "2270010":"Mobile Sources, Off-highway Vehicle Diesel, Industrial Equipment",
    "2275001":"Mobile Sources, Aircraft, Military Aircraft",
    "2275020":"Mobile Sources, Aircraft, Commercial Aircraft",
    "2275050":"Mobile Sources, Aircraft, General Aviation",
    "2275085":"Mobile Sources, Aircraft, Unpaved Airstrips",
    "2275087":"Mobile Sources, Aircraft, In-flight (non-Landing-Takeoff cycle)",
    "2275900":"Mobile Sources, Aircraft, Refueling: All Fuels",
    "2280000":"Mobile Sources, Marine Vessels, Commercial, All Fuels",
    "2280001":"Mobile Sources, Marine Vessels, Commercial, Coal",
    "2280002":"Mobile Sources, Marine Vessels, Commercial, Diesel",
    "2280003":"Mobile Sources, Marine Vessels, Commercial, Residual",
    "2280004":"Mobile Sources, Marine Vessels, Commercial, Gasoline",
    "2282000":"Mobile Sources, Pleasure Craft, All Fuels",
    "2282005":"Mobile Sources, Pleasure Craft, Gasoline 2-Stroke",
    "2282005":"Mobile Sources, Pleasure Craft, Gasoline",
    "2282010":"Mobile Sources, Pleasure Craft, Gasoline 4-Stroke",
    "2282020":"Mobile Sources, Pleasure Craft, Diesel",
    "2283000":"Mobile Sources, Marine Vessels, Military, unknown",
    "2283001":"Mobile Sources, Marine Vessels, Military, unknown",
    "2283002":"Mobile Sources, Marine Vessels, Military, Diesel",
    "2283002":"Mobile Sources, Marine Vessels, Military, unknown",
    "2283003":"Mobile Sources, Marine Vessels, Military, unknown",
    "2283004":"Mobile Sources, Marine Vessels, Military, unknown",
    "2285000":"Mobile Sources, Railroad Equipment, All Fuels",
    "2285002":"Mobile Sources, Railroad Equipment, Diesel",
    "2285003":"Mobile Sources, Railroad Equipment, Gasoline, 2-Stroke",
    "2285004":"Mobile Sources, Railroad Equipment, Gasoline, 4-Stroke",
    "2285006":"Mobile Sources, Railroad Equipment, LPG",
    "2285008":"Mobile Sources, Railroad Equipment, CNG",
    "2294000":"Mobile Sources, Paved Roads, All Paved Roads",
    "2294000":"Mobile Sources, Paved Roads, unknown",
    "2294005":"Mobile Sources, Paved Roads, Interstate/Arterial",
    "2294010":"Mobile Sources, Paved Roads, All Other Public Paved Roads",
    "2294015":"Mobile Sources, Paved Roads, Industrial Roads",
    "2296000":"Mobile Sources, Unpaved Roads, All Unpaved Roads",
    "2296000":"Mobile Sources, Unpaved Roads, unknown",
    "2296005":"Mobile Sources, Unpaved Roads, Public Unpaved Roads",
    "2296010":"Mobile Sources, Unpaved Roads, Industrial Unpaved Roads",
    "2297000":"Mobile Sources, unknown non-US source, unknown non-US source",
    "2701200":"Natural Sources, Biogenic, Vegetation",
    "2701220":"Natural Sources, Biogenic, Vegetation/Agriculture",
    "2401001":"Solvent Utilization, Surface Coating, Architectural Coatings",
    "2401002":"Solvent Utilization, Surface Coating, Architectural Coatings - Solvent-based",
    "2401003":"Solvent Utilization, Surface Coating, Architectural Coatings - Water-based",
    "2401004":"Solvent Utilization, Surface Coating, Allied Paint Products",
    "2401005":"Solvent Utilization, Surface Coating, Auto Refinishing: SIC 7532",
    "2401008":"Solvent Utilization, Surface Coating, Traffic Markings",
    "2401010":"Solvent Utilization, Surface Coating, Textile Products: SIC 22",
    "2401015":"Solvent Utilization, Surface Coating, Factory Finished Wood: SIC 2426 thru 242",
    "2401020":"Solvent Utilization, Surface Coating, Wood Furniture: SIC 25",
    "2401025":"Solvent Utilization, Surface Coating, Metal Furniture: SIC 25",
    "2401030":"Solvent Utilization, Surface Coating, Paper: SIC 26",
    "2401035":"Solvent Utilization, Surface Coating, Plastic Products: SIC 308",
    "2401040":"Solvent Utilization, Surface Coating, Metal Cans: SIC 341",
    "2401045":"Solvent Utilization, Surface Coating, Metal Coils: SIC 3498",
    "2401050":"Solvent Utilization, Surface Coating, Miscellaneous Finished Metals: SIC 34 - (341 + 3498)",
    "2401055":"Solvent Utilization, Surface Coating, Machinery and Equipment: SIC 35",
    "2401060":"Solvent Utilization, Surface Coating, Large Appliances: SIC 363",
    "2401065":"Solvent Utilization, Surface Coating, Electronic and Other Electrical: SIC 36 - 363",
    "2401070":"Solvent Utilization, Surface Coating, Motor Vehicles: SIC 371",
    "2401075":"Solvent Utilization, Surface Coating, Aircraft: SIC 372",
    "2401080":"Solvent Utilization, Surface Coating, Marine: SIC 373",
    "2401085":"Solvent Utilization, Surface Coating, Railroad: SIC 374",
    "2401090":"Solvent Utilization, Surface Coating, Miscellaneous Manufacturing",
    "2401100":"Solvent Utilization, Surface Coating, Industrial Maintenance Coatings",
    "2401200":"Solvent Utilization, Surface Coating, Other Special Purpose Coatings",
    "2401990":"Solvent Utilization, Surface Coating, All Surface Coating Categories",
    "2402000":"Solvent Utilization, Paint Strippers, Chemical Strippers",
    "2415000":"Solvent Utilization, Degreasing, All Processes/All Industries",
    "2415005":"Solvent Utilization, Degreasing, Furniture and Fixtures (SIC 25): All Processes",
    "2415010":"Solvent Utilization, Degreasing, Primary Metal Industries (SIC 33): All Processes",
    "2415015":"Solvent Utilization, Degreasing, Secondary Metal Industries (SIC 33): All Processes",
    "2415020":"Solvent Utilization, Degreasing, Fabricated Metal Products (SIC 34): All Processes",
    "2415025":"Solvent Utilization, Degreasing, Industrial Machinery and Equipment (SIC 35): All Processes",
    "2415030":"Solvent Utilization, Degreasing, Electronic and Other Elec. (SIC 36): All Processes",
    "2415035":"Solvent Utilization, Degreasing, Transportation Equipment (SIC 37): All Processes",
    "2415040":"Solvent Utilization, Degreasing, Instruments and Related Products (SIC 38): All Processes",
    "2415045":"Solvent Utilization, Degreasing, Miscellaneous Manufacturing (SIC 39): All Processes",
    "2415050":"Solvent Utilization, Degreasing, Transportation Maintenance Facilities (SIC 40-45): All Processes",
    "2415055":"Solvent Utilization, Degreasing, Automotive Dealers (SIC 55): All Processes",
    "2415060":"Solvent Utilization, Degreasing, Miscellaneous Repair Services (SIC 76): All Processes",
    "2415065":"Solvent Utilization, Degreasing, Auto Repair Services (SIC 75): All Processes",
    "2415100":"Solvent Utilization, Degreasing, All Industries: Open Top Degreasing",
    "2415105":"Solvent Utilization, Degreasing, Furniture and Fixtures (SIC 25): Open Top Degreasing",
    "2415110":"Solvent Utilization, Degreasing, Primary Metal Industries (SIC 33): Open Top Degreasing",
    "2415115":"Solvent Utilization, Degreasing, Secondary Metal Industries (SIC 33): Open Top Degreasing",
    "2415120":"Solvent Utilization, Degreasing, Fabricated Metal Products (SIC 34): Open Top Degreasing",
    "2415125":"Solvent Utilization, Degreasing, Industrial Machinery and Equipment (SIC 35): Open Top Degreasing",
    "2415130":"Solvent Utilization, Degreasing, Electronic and Other Elec. (SIC 36): Open Top Degreasing",
    "2415135":"Solvent Utilization, Degreasing, Transportation Equipment (SIC 37): Open Top Degreasing",
    "2415140":"Solvent Utilization, Degreasing, Instruments and Related Products (SIC 38): Open Top Degreasing",
    "2415145":"Solvent Utilization, Degreasing, Miscellaneous Manufacturing (SIC 39): Open Top Degreasing",
    "2415150":"Solvent Utilization, Degreasing, Transportation Maintenance Facilities (SIC 40-45): Open Top Degreasing",
    "2415155":"Solvent Utilization, Degreasing, Automotive Dealers (SIC 55): Open Top Degreasing",
    "2415160":"Solvent Utilization, Degreasing, Auto Repair Services (SIC 75): Open Top Degreasing",
    "2415165":"Solvent Utilization, Degreasing, Miscellaneous Repair Services (SIC 76): Open Top Degreasing",
    "2415200":"Solvent Utilization, Degreasing, All Industries: Conveyerized Degreasing",
    "2415205":"Solvent Utilization, Degreasing, Furniture and Fixtures (SIC 25): Conveyerized Degreasing",
    "2415210":"Solvent Utilization, Degreasing, Primary Metal Industries (SIC 33): Conveyerized Degreasing",
    "2415215":"Solvent Utilization, Degreasing, Secondary Metal Industries (SIC 33): Conveyerized Degreasing",
    "2415220":"Solvent Utilization, Degreasing, Fabricated Metal Products (SIC 34): Conveyerized Degreasing",
    "2415225":"Solvent Utilization, Degreasing, Industrial Machinery and Equipment (SIC 35): Conveyerized Degreasing",
    "2415230":"Solvent Utilization, Degreasing, Electronic and Other Elec. (SIC 36): Conveyerized Degreasing",
    "2415235":"Solvent Utilization, Degreasing, Transportation Equipment (SIC 37): Conveyerized Degreasing",
    "2415240":"Solvent Utilization, Degreasing, Instruments and Related Products (SIC 38): Conveyerized Degreasing",
    "2415245":"Solvent Utilization, Degreasing, Miscellaneous Manufacturing (SIC 39): Conveyerized Degreasing",
    "2415250":"Solvent Utilization, Degreasing, Trans. Maintenance Facilities (SIC 40-45): Conveyerized Degreasing",
    "2415255":"Solvent Utilization, Degreasing, Automotive Dealers (SIC 55): Conveyerized Degreasing",
    "2415260":"Solvent Utilization, Degreasing, Auto Repair Services (SIC 75): Conveyerized Degreasing",
    "2415265":"Solvent Utilization, Degreasing, Miscellaneous Repair Services (SIC 76): Conveyerized Degreasing",
    "2415300":"Solvent Utilization, Degreasing, All Industries: Cold Cleaning",
    "2415305":"Solvent Utilization, Degreasing, Furniture and Fixtures (SIC 25): Cold Cleaning",
    "2415310":"Solvent Utilization, Degreasing, Primary Metal Industries (SIC 33): Cold Cleaning",
    "2415315":"Solvent Utilization, Degreasing, Secondary Metal Industries (SIC 33): Cold Cleaning",
    "2415320":"Solvent Utilization, Degreasing, Fabricated Metal Products (SIC 34): Cold Cleaning",
    "2415325":"Solvent Utilization, Degreasing, Industrial Machinery and Equipment (SIC 35): Cold Cleaning",
    "2415330":"Solvent Utilization, Degreasing, Electronic and Other Elec. (SIC 36): Cold Cleaning",
    "2415335":"Solvent Utilization, Degreasing, Transportation Equipment (SIC 37): Cold Cleaning",
    "2415340":"Solvent Utilization, Degreasing, Instruments and Related Products (SIC 38): Cold Cleaning",
    "2415345":"Solvent Utilization, Degreasing, Miscellaneous Manufacturing (SIC 39): Cold Cleaning",
    "2415350":"Solvent Utilization, Degreasing, Transportation Maintenance Facilities (SIC 40-45): Cold Cleaning",
    "2415355":"Solvent Utilization, Degreasing, Automotive Dealers (SIC 55): Cold Cleaning",
    "2415360":"Solvent Utilization, Degreasing, Auto Repair Services (SIC 75): Cold Cleaning",
    "2415365":"Solvent Utilization, Degreasing, Miscellaneous Repair Services (SIC 76): Cold Cleaning",
    "2420000":"Solvent Utilization, Dry Cleaning, All Processes",
    "2420010":"Solvent Utilization, Dry Cleaning, Commercial/Industrial Cleaners",
    "2420020":"Solvent Utilization, Dry Cleaning, Coin-operated Cleaners",
    "2425000":"Solvent Utilization, Graphic Arts, All Processes",
    "2425010":"Solvent Utilization, Graphic Arts, Lithography",
    "2425020":"Solvent Utilization, Graphic Arts, Letterpress",
    "2425030":"Solvent Utilization, Graphic Arts, Rotogravure",
    "2425040":"Solvent Utilization, Graphic Arts, Flexography",
    "2425050":"Solvent Utilization, Graphic Arts, Digital",
    "2430000":"Solvent Utilization, Rubber/Plastics, All Processes",
    "2440000":"Solvent Utilization, Miscellaneous Industrial, All Processes",
    "2440020":"Solvent Utilization, Miscellaneous Industrial, Adhesive (Industrial) Application",
    "2460000":"Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, All Processes",
    "2460030":"Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, Lighter Fluid, Fire Starter, Other Fuels",
    "2460100":"Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, All Personal Care Products",
    "2460110":"Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, Personal Care Products: Hair Care Products",
    "2460120":"Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, Personal Care Products: Deodorants and Antiperspirants",
    "2460130":"Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, Personal Care Products: Fragrance Products",
    "2460140":"Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, Personal Care Products: Powders",
    "2460150":"Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, Personal Care Products: Nail Care Products",
    "2460160":"Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, Personal Care Products: Facial and Body Treatments",
    "2460170":"Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, Personal Care Products: Oral Care Products",
    "2460180":"Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, Personal Care Products: Health Use Products (External Only)",
    "2460190":"Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, Personal Care Products: Miscellaneous Personal Care Products",
    "2460200":"Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, All Household Products",
    "2460210":"Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, Household Products: Hard Surface Cleaners",
    "2460220":"Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, Household Products: Laundry Products",
    "2460230":"Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, Household Products: Fabric and Carpet Care Products",
    "2460240":"Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, Household Products: Dishwashing Products",
    "2460250":"Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, Household Products: Waxes and Polishes",
    "2460260":"Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, Household Products: Air Fresheners",
    "2460270":"Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, Household Products: Shoe and Leather Care Products",
    "2460290":"Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, Household Products: Miscellaneous Household Products",
    "2460400":"Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, All Automotive Aftermarket Products",
    "2460410":"Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, Automotive Aftermarket Products: Detailing Products",
    "2460420":"Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, Automotive Aftermarket Products: Maintenance and Repair Products",
    "2460500":"Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, All Coatings and Related Products",
    "2460510":"Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, Coatings and Related Products: Aerosol Spray Paints",
    "2460520":"Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, Coatings and Related Products: Coating Related Products",
    "2460600":"Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, All Adhesives and Sealants",
    "2460610":"Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, Adhesives and Sealants: Adhesives",
    "2460620":"Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, Adhesives and Sealants: Sealants",
    "2460800":"Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, All FIFRA Related Products",
    "2460810":"Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, FIFRA Related Products: Insecticides",
    "2460820":"Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, FIFRA Related Products: Fungicides and Nematicides",
    "2460830":"Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, FIFRA Related Products: Herbicides",
    "2460840":"Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, FIFRA Related Products: Antimicrobial Agents",
    "2460890":"Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, FIFRA Related Products: Other FIFRA Related Products",
    "2460900":"Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, Miscellaneous Products (Not Otherwise Covered)",
    "2460910":"Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, Miscellaneous Products: Arts and Crafts Supplies",
    "2460920":"Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, Miscellaneous Products: Non-Pesticidal Veterinary and Pet Products",
    "2460930":"Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, Miscellaneous Products: Pressurized Food Products",
    "2460940":"Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, Miscellaneous Products: Office Supplies",
    "2461000":"Solvent Utilization, Miscellaneous Non-industrial: Commercial, All Processes",
    "2461020":"Solvent Utilization, Miscellaneous Non-industrial: Commercial, Asphalt Application: All Processes",
    "2461021":"Solvent Utilization, Miscellaneous Non-industrial: Commercial, Cutback Asphalt",
    "2461022":"Solvent Utilization, Miscellaneous Non-industrial: Commercial, Emulsified Asphalt",
    "2461023":"Solvent Utilization, Miscellaneous Non-industrial: Commercial, Asphalt Roofing",
    "2461024":"Solvent Utilization, Miscellaneous Non-industrial: Commercial, Asphalt Pipe Coating",
    "2461025":"Solvent Utilization, Miscellaneous Non-industrial: Commercial, Asphalt Paving: Hot and Warm Mix",
    "2461026":"Solvent Utilization, Miscellaneous Non-industrial: Commercial, Asphalt Paving: Road Oil",
    "2461030":"Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, Lighter Fluid, Fire Starter, Other Fuels",
    "2461050":"Solvent Utilization, Miscellaneous Non-industrial: Commercial, Film Roofing: All Processes",
    "2461100":"Solvent Utilization, Miscellaneous Non-industrial: Commercial, Solvent Reclamation: All Processes",
    "2461160":"Solvent Utilization, Miscellaneous Non-industrial: Commercial, Tank/Drum Cleaning: All Processes",
    "2461200":"Solvent Utilization, Miscellaneous Non-industrial: Commercial, Adhesives and Sealants",
    "2461800":"Solvent Utilization, Miscellaneous Non-industrial: Commercial, Pesticide Application: All Processes",
    "2461850":"Solvent Utilization, Miscellaneous Non-industrial: Commercial, Pesticide Application: Agricultural",
    "2461870":"Solvent Utilization, Miscellaneous Non-industrial: Commercial, Pesticide Application: Non-Agricultural",
    "2461900":"Solvent Utilization, Miscellaneous Non-industrial: Commercial, Miscellaneous Products: NEC",
    "2465000":"Solvent Utilization, Miscellaneous Non-industrial: Consumer, All Products/Processes",
    "2465100":"Solvent Utilization, Miscellaneous Non-industrial: Consumer, Personal Care Products",
    "2465200":"Solvent Utilization, Miscellaneous Non-industrial: Consumer, Household Products",
    "2465400":"Solvent Utilization, Miscellaneous Non-industrial: Consumer, Automotive Aftermarket Products",
    "2465600":"Solvent Utilization, Miscellaneous Non-industrial: Consumer, Adhesives and Sealants",
    "2465800":"Solvent Utilization, Miscellaneous Non-industrial: Consumer, Pesticide Application",
    "2465900":"Solvent Utilization, Miscellaneous Non-industrial: Consumer, Miscellaneous Products: NEC",
    "2495000":"Solvent Utilization, All Solvent User Categories, All Processes",
    "2101001":"Stationary Source Fuel Combustion, Electric Utility, Anthracite Coal",
    "2101002":"Stationary Source Fuel Combustion, Electric Utility, Bituminous/Subbituminous Coal",
    "2101003":"Stationary Source Fuel Combustion, Electric Utility, Lignite Coal",
    "2101004":"Stationary Source Fuel Combustion, Electric Utility, Distillate Oil",
    "2101005":"Stationary Source Fuel Combustion, Electric Utility, Residual Oil",
    "2101006":"Stationary Source Fuel Combustion, Electric Utility, Natural Gas",
    "2101007":"Stationary Source Fuel Combustion, Electric Utility, Liquified Petroleum Gas (LPG)",
    "2101008":"Stationary Source Fuel Combustion, Electric Utility, Wood",
    "2101009":"Stationary Source Fuel Combustion, Electric Utility, Petroleum Coke",
    "2101010":"Stationary Source Fuel Combustion, Electric Utility, Process Gas",
    "2102001":"Stationary Source Fuel Combustion, Industrial, Anthracite Coal",
    "2102002":"Stationary Source Fuel Combustion, Industrial, Bituminous/Subbituminous Coal",
    "2102004":"Stationary Source Fuel Combustion, Industrial, Distillate Oil",
    "2102005":"Stationary Source Fuel Combustion, Industrial, Residual Oil",
    "2102006":"Stationary Source Fuel Combustion, Industrial, Natural Gas",
    "2102007":"Stationary Source Fuel Combustion, Industrial, Liquified Petroleum Gas (LPG)",
    "2102008":"Stationary Source Fuel Combustion, Industrial, Wood",
    "2102009":"Stationary Source Fuel Combustion, Industrial, Petroleum Coke",
    "2102010":"Stationary Source Fuel Combustion, Industrial, Process Gas",
    "2102011":"Stationary Source Fuel Combustion, Industrial, Kerosene",
    "2102012":"Stationary Source Fuel Combustion, Industrial, Waste oil",
    "2103001":"Stationary Source Fuel Combustion, Commercial/Institutional, Anthracite Coal",
    "2103002":"Stationary Source Fuel Combustion, Commercial/Institutional, Bituminous/Subbituminous Coal",
    "2103004":"Stationary Source Fuel Combustion, Commercial/Institutional, Distillate Oil",
    "2103005":"Stationary Source Fuel Combustion, Commercial/Institutional, Residual Oil",
    "2103006":"Stationary Source Fuel Combustion, Commercial/Institutional, Natural Gas",
    "2103007":"Stationary Source Fuel Combustion, Commercial/Institutional, Liquified Petroleum Gas (LPG)",
    "2103008":"Stationary Source Fuel Combustion, Commercial/Institutional, Wood",
    "2103010":"Stationary Source Fuel Combustion, Commercial/Institutional, Process Gas",
    "2103011":"Stationary Source Fuel Combustion, Commercial/Institutional, Kerosene",
    "2104001":"Stationary Source Fuel Combustion, Residential, Anthracite Coal",
    "2104002":"Stationary Source Fuel Combustion, Residential, Bituminous/Subbituminous Coal",
    "2104004":"Stationary Source Fuel Combustion, Residential, Distillate Oil",
    "2104005":"Stationary Source Fuel Combustion, Residential, Residual Oil",
    "2104006":"Stationary Source Fuel Combustion, Residential, Natural Gas",
    "2104007":"Stationary Source Fuel Combustion, Residential, Liquified Petroleum Gas (LPG)",
    "2104008":"Stationary Source Fuel Combustion, Residential, Wood",
    "2104009":"Stationary Source Fuel Combustion, Residential, Firelog",
    "2104010":"Stationary Source Fuel Combustion, Residential, Biomass; All Except Wood",
    "2104011":"Stationary Source Fuel Combustion, Residential, Kerosene",
    "2199001":"Stationary Source Fuel Combustion, Total Area Source Fuel Combustion, Anthracite Coal",
    "2199002":"Stationary Source Fuel Combustion, Total Area Source Fuel Combustion, Bituminous/Subbituminous Coal",
    "2199003":"Stationary Source Fuel Combustion, Total Area Source Fuel Combustion, Lignite Coal",
    "2199004":"Stationary Source Fuel Combustion, Total Area Source Fuel Combustion, Distillate Oil",
    "2199005":"Stationary Source Fuel Combustion, Total Area Source Fuel Combustion, Residual Oil",
    "2199006":"Stationary Source Fuel Combustion, Total Area Source Fuel Combustion, Natural Gas",
    "2199007":"Stationary Source Fuel Combustion, Total Area Source Fuel Combustion, Liquified Petroleum Gas (LPG)",
    "2199008":"Stationary Source Fuel Combustion, Total Area Source Fuel Combustion, Wood",
    "2199009":"Stationary Source Fuel Combustion, Total Area Source Fuel Combustion, Petroleum Coke",
    "2199010":"Stationary Source Fuel Combustion, Total Area Source Fuel Combustion, Process Gas",
    "2199011":"Stationary Source Fuel Combustion, Total Area Source Fuel Combustion, Kerosene",
    "2501000":"Storage and Transport, Petroleum and Petroleum Product Storage, All Storage Types: Breathing Loss",
    "2501010":"Storage and Transport, Petroleum and Petroleum Product Storage, Commercial/Industrial: Breathing Loss",
    "2501011":"Storage and Transport, Petroleum and Petroleum Product Storage, Residential Portable Gas Cans",
    "2501012":"Storage and Transport, Petroleum and Petroleum Product Storage, Commercial Portable Gas Cans",
    "2501013":"Storage and Transport, Petroleum and Petroleum Product Storage, Residential/Commercial Portable Gas Cans",
    "2501050":"Storage and Transport, Petroleum and Petroleum Product Storage, Bulk Terminals: All Evaporative Losses",
    "2501055":"Storage and Transport, Petroleum and Petroleum Product Storage, Bulk Plants: All Evaporative Losses",
    "2501060":"Storage and Transport, Petroleum and Petroleum Product Storage, Gasoline Service Stations",
    "2501070":"Storage and Transport, Petroleum and Petroleum Product Storage, Diesel Service Stations",
    "2501080":"Storage and Transport, Petroleum and Petroleum Product Storage, Airports : Aviation Gasoline",
    "2501995":"Storage and Transport, Petroleum and Petroleum Product Storage, All Storage Types: Working Loss",
    "2505000":"Storage and Transport, Petroleum and Petroleum Product Transport, All Transport Types",
    "2505010":"Storage and Transport, Petroleum and Petroleum Product Transport, Rail Tank Car",
    "2505020":"Storage and Transport, Petroleum and Petroleum Product Transport, Marine Vessel",
    "2505030":"Storage and Transport, Petroleum and Petroleum Product Transport, Truck",
    "2505040":"Storage and Transport, Petroleum and Petroleum Product Transport, Pipeline",
    "2510000":"Storage and Transport, Organic Chemical Storage, All Storage Types: Breathing Loss",
    "2510010":"Storage and Transport, Organic Chemical Storage, Commercial/Industrial: Breathing Loss",
    "2510050":"Storage and Transport, Organic Chemical Storage, Bulk Stations/Terminals: Breathing Loss",
    "2510995":"Storage and Transport, Organic Chemical Storage, All Storage Types: Working Loss",
    "2515000":"Storage and Transport, Organic Chemical Transport, All Transport Types",
    "2515010":"Storage and Transport, Organic Chemical Transport, Rail Tank Car",
    "2515020":"Storage and Transport, Organic Chemical Transport, Marine Vessel",
    "2515030":"Storage and Transport, Organic Chemical Transport, Truck",
    "2515040":"Storage and Transport, Organic Chemical Transport, Pipeline",
    "2520000":"Storage and Transport, Inorganic Chemical Storage, All Storage Types: Breathing Loss",
    "2520010":"Storage and Transport, Inorganic Chemical Storage, Commercial/Industrial: Breathing Loss",
    "2520050":"Storage and Transport, Inorganic Chemical Storage, Bulk Stations/Terminals: Breathing Loss",
    "2520995":"Storage and Transport, Inorganic Chemical Storage, All Storage Types: Working Loss",
    "2525000":"Storage and Transport, Inorganic Chemical Transport, All Transport Types",
    "2525010":"Storage and Transport, Inorganic Chemical Transport, Rail Tank Car",
    "2525020":"Storage and Transport, Inorganic Chemical Transport, Marine Vessel",
    "2525030":"Storage and Transport, Inorganic Chemical Transport, Truck",
    "2525040":"Storage and Transport, Inorganic Chemical Transport, Pipeline",
    "2530000":"Storage and Transport, Bulk Materials Storage, All Storage Types",
    "2530010":"Storage and Transport, Bulk Materials Storage, Commercial/Industrial",
    "2530050":"Storage and Transport, Bulk Materials Storage, Bulk Stations/Terminals",
    "2535000":"Storage and Transport, Bulk Materials Transport, All Transport Types",
    "2535010":"Storage and Transport, Bulk Materials Transport, Rail Car",
    "2535020":"Storage and Transport, Bulk Materials Transport, Marine Vessel",
    "2535030":"Storage and Transport, Bulk Materials Transport, Truck",
    "2999001":"very misc, holding scc, for state-reported",
    "2601000":"Waste Disposal, Treatment, and Recovery, On-site Incineration, All Categories",
    "2601010":"Waste Disposal, Treatment, and Recovery, On-site Incineration, Industrial",
    "2601020":"Waste Disposal, Treatment, and Recovery, On-site Incineration, Commercial/Institutional",
    "2601030":"Waste Disposal, Treatment, and Recovery, On-site Incineration, Residential",
    "2610000":"Waste Disposal, Treatment, and Recovery, Open Burning, All Categories",
    "2610010":"Waste Disposal, Treatment, and Recovery, Open Burning, Industrial",
    "2610020":"Waste Disposal, Treatment, and Recovery, Open Burning, Commercial/Institutional",
    "2610030":"Waste Disposal, Treatment, and Recovery, Open Burning, Residential",
    "2610040":"Waste Disposal, Treatment, and Recovery, Open Burning, Municipal (collected from residences, parks,other for central burn)",
    "2620000":"Waste Disposal, Treatment, and Recovery, Landfills, All Categories",
    "2620010":"Waste Disposal, Treatment, and Recovery, Landfills, Industrial",
    "2620020":"Waste Disposal, Treatment, and Recovery, Landfills, Commercial/Institutional",
    "2620030":"Waste Disposal, Treatment, and Recovery, Landfills, Municipal",
    "2630000":"Waste Disposal, Treatment, and Recovery, Wastewater Treatment, All Categories",
    "2630010":"Waste Disposal, Treatment, and Recovery, Wastewater Treatment, Industrial",
    "2630020":"Waste Disposal, Treatment, and Recovery, Wastewater Treatment, Public Owned",
    "2630030":"Waste Disposal, Treatment, and Recovery, Wastewater Treatment, Residential/Subdivision Owned",
    "2630040":"Waste Disposal, Treatment, and Recovery, Wastewater Treatment, Public Owned",
    "2630050":"Waste Disposal, Treatment, and Recovery, Wastewater Treatment, Public Owned",
    "2635000":"Waste Disposal, Treatment, and Recovery, Soil and Groundwater Remediation, All Categories",
    "2640000":"Waste Disposal, Treatment, and Recovery, TSDFs, All TSDF Types",
    "2640010":"Waste Disposal, Treatment, and Recovery, TSDFs, Industrial",
    "2640020":"Waste Disposal, Treatment, and Recovery, TSDFs, Commercial/Institutional",
    "2650000":"Waste Disposal, Treatment, and Recovery, Scrap and Waste Materials, Scrap and Waste Materials",
    "2660000":"Waste Disposal, Treatment, and Recovery, Leaking Underground Storage Tanks, Leaking Underground Storage Tanks",
    "2670001":"Waste Disposal, Treatment, and Recovery, Munitions Detonation, TNT Detonation",
    "2670002":"Waste Disposal, Treatment, and Recovery, Munitions Detonation, RDX Detonation",
    "2670003":"Waste Disposal, Treatment, and Recovery, Munitions Detonation, PETN Detonation",
    "2680001":"Waste Disposal, Treatment, and Recovery, Composting, 100% Biosolids (e.g., sewage sludge, manure, mixtures of these matls)",
    "2680002":"Waste Disposal, Treatment, and Recovery, Composting, Mixed Waste (e.g., a 50:50 mixture of biosolids and green wastes)",
    "2680003":"Waste Disposal, Treatment, and Recovery, Composting, 100% Green Waste (e.g., residential or municipal yard wastes)",
    "4444444444":
        "Brick Kilns, Brick Kilns, Brick Kilns, Brick Kilns",
    "5555555555":
        "Domestic Ammonia, Domestic Ammonia, Domestic Ammonia, Domestic Ammonia",
    "2301000000":
        "Industrial Processes, Chemical Manufacturing: SIC 28, All Processes, Total",
    "2301010000":
        "Industrial Processes, Chemical Manufacturing: SIC 28, Industrial Inorganic Chemical Manufacturing, Total",
    "2301010010":
        "Industrial Processes, Chemical Manufacturing: SIC 28, Industrial Inorganic Chemical Manufacturing, Sulfur Recovery: Sour Gas",
    "2301020000":
        "Industrial Processes, Chemical Manufacturing: SIC 28, Process Emissions from Synthetic Fibers Manuf (NAPAP cat. 107), Total",
    "2301030000":
        "Industrial Processes, Chemical Manufacturing: SIC 28, Process Emissions from Pharmaceutical Manuf (NAPAP cat. 106), Total",
    "2301040000":
        "Industrial Processes, Chemical Manufacturing: SIC 28, Fugitive Emissions from Synthetic Organic Chem Manuf (NAPAP cat. 102), Total",
    "2301050001":
        "Industrial Processes, Chemical Manufacturing: SIC 28, Plastics Production, Reactor (Polyurethane)",
    "2301050002":
        "Industrial Processes, Chemical Manufacturing: SIC 28, Plastics Production, Foam Production - General Process",
    "2302000000":
        "Industrial Processes, Food and Kindred Products: SIC 20, All Processes, Total",
    "2302002000":
        "Industrial Processes, Food and Kindred Products: SIC 20, Commercial Cooking - Charbroiling, Charbroiling Total",
    "2302002100":
        "Industrial Processes, Food and Kindred Products: SIC 20, Commercial Cooking - Charbroiling, Conveyorized Charbroiling",
    "2302002200":
        "Industrial Processes, Food and Kindred Products: SIC 20, Commercial Cooking - Charbroiling, Under-fired Charbroiling",
    "2302003000":
        "Industrial Processes, Food and Kindred Products: SIC 20, Commercial Cooking - Frying, Deep Fat Frying",
    "2302003100":
        "Industrial Processes, Food and Kindred Products: SIC 20, Commercial Cooking - Frying, Flat Griddle Frying",
    "2302003200":
        "Industrial Processes, Food and Kindred Products: SIC 20, Commercial Cooking - Frying, Clamshell Griddle Frying",
    "2302003299":
        "Industrial Processes, Food and Kindred Products: SIC 20, Commercial Cooking - Frying, Total for all Commercial-Cooking - Frying processes",
    "2302010000":
        "Industrial Processes, Food and Kindred Products: SIC 20, Meat Products, Total",
    "2302040000":
        "Industrial Processes, Food and Kindred Products: SIC 20, Grain Mill Products, Total",
    "2302050000":
        "Industrial Processes, Food and Kindred Products: SIC 20, Bakery Products, Total",
    "2302070000":
        "Industrial Processes, Food and Kindred Products: SIC 20, Fermentation/Beverages, Total",
    "2302070001":
        "Industrial Processes, Food and Kindred Products: SIC 20, Fermentation/Beverages, Breweries",
    "2302070005":
        "Industrial Processes, Food and Kindred Products: SIC 20, Fermentation/Beverages, Wineries",
    "2302070010":
        "Industrial Processes, Food and Kindred Products: SIC 20, Fermentation/Beverages, Distilleries",
    "2302080000":
        "Industrial Processes, Food and Kindred Products: SIC 20, Miscellaneous Food and Kindred Products, Total",
    "2302080002":
        "Industrial Processes, Food and Kindred Products: SIC 20, Miscellaneous Food and Kindred Products, Refrigeration",
    "2303000000":
        "Industrial Processes, Primary Metal Production: SIC 33, All Processes, Total",
    "2303020000":
        "Industrial Processes, Primary Metal Production: SIC 33, Iron and Steel Foundries, Total",
    "2304000000":
        "Industrial Processes, Secondary Metal Production: SIC 33, All Processes, Total",
    "2304050000":
        "Industrial Processes, Secondary Metal Production: SIC 33, Nonferrous Foundries (Castings), Total",
    "2305000000":
        "Industrial Processes, Mineral Processes: SIC 32, All Processes, Total",
    "2305070000":
        "Industrial Processes, Mineral Processes: SIC 32, Concrete, Gypsum, Plaster Products, Total",
    "2305080000":
        "Industrial Processes, Mineral Processes: SIC 32, Cut Stone and Stone Products, Total",
    "2306000000":
        "Industrial Processes, Petroleum Refining: SIC 29, All Processes, Total",
    "2306010000":
        "Industrial Processes, Petroleum Refining: SIC 29, Asphalt Mixing Plants and Paving/Roofing Materials, Asphalt Paving/Roofing Materials: Total",
    "2306010100":
        "Industrial Processes, Petroleum Refining: SIC 29, Asphalt Mixing Plants and Paving/Roofing Materials, Asphalt Mixing Plants: Total",
    "2307000000":
        "Industrial Processes, Wood Products: SIC 24, All Processes, Total",
    "2307010000":
        "Industrial Processes, Wood Products: SIC 24, Logging Operations, Total",
    "2307020000":
        "Industrial Processes, Wood Products: SIC 24, Sawmills/Planing Mills, Total",
    "2307030000":
        "Industrial Processes, Wood Products: SIC 24, Millwork, Plywood, and Structural Members, Total",
    "2307060000":
        "Industrial Processes, Wood Products: SIC 24, Miscellaneous Wood Products, Total",
    "2308000000":
        "Industrial Processes, Rubber/Plastics: SIC 30, All Processes, Total",
    "2309000000":
        "Industrial Processes, Fabricated Metals: SIC 34, All Processes, Total",
    "2309010000":
        "Industrial Processes, Fabricated Metals: SIC 34, Precious Metals Recovery, Reclamation Furnace",
    "2309100000":
        "Industrial Processes, Fabricated Metals: SIC 34, Coating, Engraving, and Allied Services, Total: All Processes",
    "2309100010":
        "Industrial Processes, Fabricated Metals: SIC 34, Coating, Engraving, and Allied Services, Electroplating",
    "2309100030":
        "Industrial Processes, Fabricated Metals: SIC 34, Coating, Engraving, and Allied Services, Plating: Metal Deposition",
    "2309100050":
        "Industrial Processes, Fabricated Metals: SIC 34, Coating, Engraving, and Allied Services, Anodizing",
    "2309100080":
        "Industrial Processes, Fabricated Metals: SIC 34, Coating, Engraving, and Allied Services, Hot Dip Galvanizing (Zinc)",
    "2309100110":
        "Industrial Processes, Fabricated Metals: SIC 34, Coating, Engraving, and Allied Services, Engraving",
    "2309100140":
        "Industrial Processes, Fabricated Metals: SIC 34, Coating, Engraving, and Allied Services, Hot Dip Metal Coating",
    "2309100170":
        "Industrial Processes, Fabricated Metals: SIC 34, Coating, Engraving, and Allied Services, Abrasive Cleaning",
    "2309100200":
        "Industrial Processes, Fabricated Metals: SIC 34, Coating, Engraving, and Allied Services, Abrasive Blasting",
    "2309100230":
        "Industrial Processes, Fabricated Metals: SIC 34, Coating, Engraving, and Allied Services, Alkaline Cleaning",
    "2309100260":
        "Industrial Processes, Fabricated Metals: SIC 34, Coating, Engraving, and Allied Services, Acid Cleaning",
    "2310000000":
        "Industrial Processes, Oil and Gas Exploration and Production, All Processes, Total: All Processes",
    "2310000220":
        "Industrial Processes, Oil and Gas Exploration and Production, All Processes, Drill Rigs",
    "2310000230":
        "Industrial Processes, Oil and Gas Exploration and Production, All Processes, Workover Rigs",
    "2310000330":
        "Industrial Processes, Oil and Gas Exploration and Production, All Processes, Artificial Lift",
    "2310000440":
        "Industrial Processes, Oil and Gas Exploration and Production, All Processes, Saltwater Disposal Engines",
    "2310000550":
        "Industrial Processes, Oil and Gas Exploration and Production, All Processes, Produced Water",
    "2310000551":
        "Industrial Processes, Oil and Gas Exploration and Production, All Processes, Produced Water from CBM Wells",
    "2310000552":
        "Industrial Processes, Oil and Gas Exploration and Production, All Processes, Produced Water from Gas Wells",
    "2310000553":
        "Industrial Processes, Oil and Gas Exploration and Production, All Processes, Produced Water from Oil Wells",
    "2310000660":
        "Industrial Processes, Oil and Gas Exploration and Production, All Processes, Hydraulic Fracturing Engines",
    "2310001000":
        "Industrial Processes, Oil and Gas Exploration and Production, All Processes : On-shore, Total: All Processes",
    "2310002000":
        "Industrial Processes, Oil and Gas Exploration and Production, Off-Shore Oil And Gas Production, Total: All Processes",
    "2310002301":
        "Industrial Processes, Oil and Gas Exploration and Production, Off-Shore Oil And Gas Production, Flares: Continuous Pilot Light",
    "2310002305":
        "Industrial Processes, Oil and Gas Exploration and Production, Off-Shore Oil And Gas Production, Flares: Flaring Operations",
    "2310002401":
        "Industrial Processes, Oil and Gas Exploration and Production, Off-Shore Oil And Gas Production, Pneumatic Pumps: Gas And Oil Wells",
    "2310002411":
        "Industrial Processes, Oil and Gas Exploration and Production, Off-Shore Oil And Gas Production, Pressure/Level Controllers",
    "2310002421":
        "Industrial Processes, Oil and Gas Exploration and Production, Off-Shore Oil And Gas Production, Cold Vents",
    "2310010000":
        "Industrial Processes, Oil and Gas Exploration and Production, Crude Petroleum, Total: All Processes",
    "2310010100":
        "Industrial Processes, Oil and Gas Exploration and Production, Crude Petroleum, Oil Well Heaters",
    "2310010200":
        "Industrial Processes, Oil and Gas Exploration and Production, Crude Petroleum, Oil Well Tanks - Flashing & Standing/Working/Breathing",
    "2310010300":
        "Industrial Processes, Oil and Gas Exploration and Production, Crude Petroleum, Oil Well Pneumatic Devices",
    "2310010700":
        "Industrial Processes, Oil and Gas Exploration and Production, Crude Petroleum, Oil Well Fugitives",
    "2310010800":
        "Industrial Processes, Oil and Gas Exploration and Production, Crude Petroleum, Oil Well Truck Loading",
    "2310011000":
        "Industrial Processes, Oil and Gas Exploration and Production, On-Shore Oil Production, Total: All Processes",
    "2310011001":
        "Industrial Processes, Oil and Gas Exploration and Production, On-Shore Oil Production, Associated Gas Venting",
    "2310011020":
        "Industrial Processes, Oil and Gas Exploration and Production, On-Shore Oil Production, Storage Tanks: Crude Oil",
    "2310011100":
        "Industrial Processes, Oil and Gas Exploration and Production, On-Shore Oil Production, Heater Treater",
    "2310011201":
        "Industrial Processes, Oil and Gas Exploration and Production, On-Shore Oil Production, Tank Truck/Railcar Loading: Crude Oil",
    "2310011401":
        "Industrial Processes, Oil and Gas Exploration and Production, On-Shore Oil Production, Oil Well Pneumatic Pumps",
    "2310011450":
        "Industrial Processes, Oil and Gas Exploration and Production, On-Shore Oil Production, Wellhead",
    "2310011500":
        "Industrial Processes, Oil and Gas Exploration and Production, On-Shore Oil Production, Fugitives: All Processes",
    "2310011501":
        "Industrial Processes, Oil and Gas Exploration and Production, On-Shore Oil Production, Fugitives: Connectors",
    "2310011502":
        "Industrial Processes, Oil and Gas Exploration and Production, On-Shore Oil Production, Fugitives: Flanges",
    "2310011503":
        "Industrial Processes, Oil and Gas Exploration and Production, On-Shore Oil Production, Fugitives: Open Ended Lines",
    "2310011504":
        "Industrial Processes, Oil and Gas Exploration and Production, On-Shore Oil Production, Fugitives: Pumps",
    "2310011505":
        "Industrial Processes, Oil and Gas Exploration and Production, On-Shore Oil Production, Fugitives: Valves",
    "2310011506":
        "Industrial Processes, Oil and Gas Exploration and Production, On-Shore Oil Production, Fugitives: Other",
    "2310011600":
        "Industrial Processes, Oil and Gas Exploration and Production, On-Shore Oil Production, Artificial Lift Engines",
    "2310012000":
        "Industrial Processes, Oil and Gas Exploration and Production, Off-Shore Oil Production, Total: All Processes",
    "2310012020":
        "Industrial Processes, Oil and Gas Exploration and Production, Off-Shore Oil Production, Storage Tanks: Crude Oil",
    "2310012201":
        "Industrial Processes, Oil and Gas Exploration and Production, Off-Shore Oil Production, Barge Loading: Crude Oil",
    "2310012511":
        "Industrial Processes, Oil and Gas Exploration and Production, Off-Shore Oil Production, Fugitives, Connectors: Oil Streams",
    "2310012512":
        "Industrial Processes, Oil and Gas Exploration and Production, Off-Shore Oil Production, Fugitives, Flanges: Oil",
    "2310012515":
        "Industrial Processes, Oil and Gas Exploration and Production, Off-Shore Oil Production, Fugitives, Valves: Oil",
    "2310012516":
        "Industrial Processes, Oil and Gas Exploration and Production, Off-Shore Oil Production, Fugitives, Other: Oil",
    "2310012521":
        "Industrial Processes, Oil and Gas Exploration and Production, Off-Shore Oil Production, Fugitives, Connectors: Oil/Water Streams",
    "2310012522":
        "Industrial Processes, Oil and Gas Exploration and Production, Off-Shore Oil Production, Fugitives, Flanges: Oil/Water",
    "2310012525":
        "Industrial Processes, Oil and Gas Exploration and Production, Off-Shore Oil Production, Fugitives, Valves: Oil/Water",
    "2310012526":
        "Industrial Processes, Oil and Gas Exploration and Production, Off-Shore Oil Production, Fugitives, Other: Oil/Water",
    "2310020000":
        "Industrial Processes, Oil and Gas Exploration and Production, Natural Gas, Total: All Processes",
    "2310020600":
        "Industrial Processes, Oil and Gas Exploration and Production, Natural Gas, Compressor Engines",
    "2310020700":
        "Industrial Processes, Oil and Gas Exploration and Production, Natural Gas, Gas Well Fugitives",
    "2310020800":
        "Industrial Processes, Oil and Gas Exploration and Production, Natural Gas, Gas Well Truck Loading",
    "2310021000":
        "Industrial Processes, Oil and Gas Exploration and Production, On-Shore Gas Production, Total: All Processes",
    "2310021010":
        "Industrial Processes, Oil and Gas Exploration and Production, On-Shore Gas Production, Storage Tanks: Condensate",
    "2310021011":
        "Industrial Processes, Oil and Gas Exploration and Production, On-Shore Gas Production, Condensate Tank Flaring",
    "2310021030":
        "Industrial Processes, Oil and Gas Exploration and Production, On-Shore Gas Production, Tank Truck/Railcar Loading: Condensate",
    "2310021100":
        "Industrial Processes, Oil and Gas Exploration and Production, On-Shore Gas Production, Gas Well Heaters",
    "2310021101":
        "Industrial Processes, Oil and Gas Exploration and Production, On-Shore Gas Production, Natural Gas Fired 2Cycle Lean Burn Compressor Engines < 50 HP",
    "2310021102":
        "Industrial Processes, Oil and Gas Exploration and Production, On-Shore Gas Production, Natural Gas Fired 2Cycle Lean Burn Compressor Engines 50 To 499 HP",
    "2310021103":
        "Industrial Processes, Oil and Gas Exploration and Production, On-Shore Gas Production, Natural Gas Fired 2Cycle Lean Burn Compressor Engines 500+ HP",
    "2310021109":
        "Industrial Processes, Oil and Gas Exploration and Production, On-Shore Gas Production, Total: All Natural Gas Fired 2Cycle Lean Burn Compressor Engines",
    "2310021201":
        "Industrial Processes, Oil and Gas Exploration and Production, On-Shore Gas Production, Natural Gas Fired 4Cycle Lean Burn Compressor Engines <50 HP",
    "2310021202":
        "Industrial Processes, Oil and Gas Exploration and Production, On-Shore Gas Production, Natural Gas Fired 4Cycle Lean Burn Compressor Engines 50 To 499 HP",
    "2310021203":
        "Industrial Processes, Oil and Gas Exploration and Production, On-Shore Gas Production, Natural Gas Fired 4Cycle Lean Burn Compressor Engines 500+ HP",
    "2310021209":
        "Industrial Processes, Oil and Gas Exploration and Production, On-Shore Gas Production, Total: All Natural Gas Fired 4Cycle Lean Burn Compressor Engines",
    "2310021251":
        "Industrial Processes, Oil and Gas Exploration and Production, On-Shore Gas Production, Lateral Compressors 4 Cycle Lean Burn",
    "2310021300":
        "Industrial Processes, Oil and Gas Exploration and Production, On-Shore Gas Production, Gas Well Pneumatic Devices",
    "2310021301":
        "Industrial Processes, Oil and Gas Exploration and Production, On-Shore Gas Production, Natural Gas Fired 4Cycle Rich Burn Compressor Engines <50 HP",
    "2310021302":
        "Industrial Processes, Oil and Gas Exploration and Production, On-Shore Gas Production, Natural Gas Fired 4Cycle Rich Burn Compressor Engines 50 To 499 HP",
    "2310021303":
        "Industrial Processes, Oil and Gas Exploration and Production, On-Shore Gas Production, Natural Gas Fired 4Cycle Rich Burn Compressor Engines 500+ HP",
    "2310021309":
        "Industrial Processes, Oil and Gas Exploration and Production, On-Shore Gas Production, Total: All Natural Gas Fired 4Cycle Rich Burn Compressor Engines",
    "2310021310":
        "Industrial Processes, Oil and Gas Exploration and Production, On-Shore Gas Production, Gas Well Pneumatic Pumps",
    "2310021351":
        "Industrial Processes, Oil and Gas Exploration and Production, On-Shore Gas Production, Lateral Compressors 4 Cycle Rich Burn",
    "2310021400":
        "Industrial Processes, Oil and Gas Exploration and Production, On-Shore Gas Production, Gas Well Dehydrators",
    "2310021401":
        "Industrial Processes, Oil and Gas Exploration and Production, On-Shore Gas Production, Nat Gas Fired 4Cycle Rich Burn Compressor Engines <50 HP w/NSCR",
    "2310021402":
        "Industrial Processes, Oil and Gas Exploration and Production, On-Shore Gas Production, Nat Gas Fired 4Cycle Rich Burn Compressor Engines 50 To 499 HP w/NSCR",
    "2310021403":
        "Industrial Processes, Oil and Gas Exploration and Production, On-Shore Gas Production, Nat Gas Fired 4Cycle Rich Burn Compressor Engines 500+ HP w/NSCR",
    "2310021409":
        "Industrial Processes, Oil and Gas Exploration and Production, On-Shore Gas Production, Total: All Nat Gas Fired 4Cycle Rich Burn Compressor Engines w/NSCR",
    "2310021410":
        "Industrial Processes, Oil and Gas Exploration and Production, On-Shore Gas Production, Amine Unit",
    "2310021411":
        "Industrial Processes, Oil and Gas Exploration and Production, On-Shore Gas Production, Gas Well Dehydrators - Flaring",
    "2310021412":
        "Industrial Processes, Oil and Gas Exploration and Production, On-Shore Gas Production, Gas Well Dehydrators/Reboiler",
    "2310021450":
        "Industrial Processes, Oil and Gas Exploration and Production, On-Shore Gas Production, Wellhead",
    "2310021500":
        "Industrial Processes, Oil and Gas Exploration and Production, On-Shore Gas Production, Gas Well Completion - Flaring",
    "2310021501":
        "Industrial Processes, Oil and Gas Exploration and Production, On-Shore Gas Production, Fugitives: Connectors",
    "2310021502":
        "Industrial Processes, Oil and Gas Exploration and Production, On-Shore Gas Production, Fugitives: Flanges",
    "2310021503":
        "Industrial Processes, Oil and Gas Exploration and Production, On-Shore Gas Production, Fugitives: Open Ended Lines",
    "2310021504":
        "Industrial Processes, Oil and Gas Exploration and Production, On-Shore Gas Production, Fugitives: Pumps",
    "2310021505":
        "Industrial Processes, Oil and Gas Exploration and Production, On-Shore Gas Production, Fugitives: Valves",
    "2310021506":
        "Industrial Processes, Oil and Gas Exploration and Production, On-Shore Gas Production, Fugitives: Other",
    "2310021509":
        "Industrial Processes, Oil and Gas Exploration and Production, On-Shore Gas Production, Fugitives: All Processes",
    "2310021600":
        "Industrial Processes, Oil and Gas Exploration and Production, On-Shore Gas Production, Gas Well Venting",
    "2310021601":
        "Industrial Processes, Oil and Gas Exploration and Production, On-Shore Gas Production, Gas Well Venting - Initial Completions",
    "2310021602":
        "Industrial Processes, Oil and Gas Exploration and Production, On-Shore Gas Production, Gas Well Venting - Recompletions",
    "2310021603":
        "Industrial Processes, Oil and Gas Exploration and Production, On-Shore Gas Production, Gas Well Venting - Blowdowns",
    "2310021604":
        "Industrial Processes, Oil and Gas Exploration and Production, On-Shore Gas Production, Gas Well Venting - Compressor Startups",
    "2310021605":
        "Industrial Processes, Oil and Gas Exploration and Production, On-Shore Gas Production, Gas Well Venting - Compressor Shutdowns",
    "2310021700":
        "Industrial Processes, Oil and Gas Exploration and Production, On-Shore Gas Production, Miscellaneous Engines",
    "2310021801":
        "Industrial Processes, Oil and Gas Exploration and Production, On-Shore Gas Production, Pipeline Blowdowns and Pigging",
    "2310021802":
        "Industrial Processes, Oil and Gas Exploration and Production, On-Shore Gas Production, Pipeline Leaks",
    "2310021803":
        "Industrial Processes, Oil and Gas Exploration and Production, On-Shore Gas Production, Midstream gas venting for maintenance, startup, shutdown, or malfunction",
    "2310022000":
        "Industrial Processes, Oil and Gas Exploration and Production, Off-Shore Gas Production, Total: All Processes",
    "2310022010":
        "Industrial Processes, Oil and Gas Exploration and Production, Off-Shore Gas Production, Storage Tanks: Condensate",
    "2310022051":
        "Industrial Processes, Oil and Gas Exploration and Production, Off-Shore Gas Production, Turbines: Natural Gas",
    "2310022090":
        "Industrial Processes, Oil and Gas Exploration and Production, Off-Shore Gas Production, Boilers/Heaters: Natural Gas",
    "2310022101":
        "Industrial Processes, Oil and Gas Exploration and Production, Off-Shore Gas Production, Natural Gas Fired 2Cycle Lean Burn Compressor Engines < 50 HP",
    "2310022102":
        "Industrial Processes, Oil and Gas Exploration and Production, Off-Shore Gas Production, Natural Gas Fired 2Cycle Lean Burn Compressor Engines 50 To 499 HP",
    "2310022103":
        "Industrial Processes, Oil and Gas Exploration and Production, Off-Shore Gas Production, Natural Gas Fired 2Cycle Lean Burn Compressor Engines 500+ HP",
    "2310022105":
        "Industrial Processes, Oil and Gas Exploration and Production, Off-Shore Gas Production, Diesel Engines",
    "2310022109":
        "Industrial Processes, Oil and Gas Exploration and Production, Off-Shore Gas Production, Total: All Natural Gas Fired 2Cycle Lean Burn Compressor Engines",
    "2310022201":
        "Industrial Processes, Oil and Gas Exploration and Production, Off-Shore Gas Production, Natural Gas Fired 4Cycle Lean Burn Compressor Engines <50 HP",
    "2310022202":
        "Industrial Processes, Oil and Gas Exploration and Production, Off-Shore Gas Production, Natural Gas Fired 4Cycle Lean Burn Compressor Engines 50 To 499 HP",
    "2310022203":
        "Industrial Processes, Oil and Gas Exploration and Production, Off-Shore Gas Production, Natural Gas Fired 4Cycle Lean Burn Compressor Engines 500+ HP",
    "2310022300":
        "Industrial Processes, Oil and Gas Exploration and Production, Off-Shore Gas Production, Compressor Engines: 4Cycle Rich",
    "2310022301":
        "Industrial Processes, Oil and Gas Exploration and Production, Off-Shore Gas Production, Natural Gas Fired 4Cycle Rich Burn Compressor Engines <50 HP",
    "2310022302":
        "Industrial Processes, Oil and Gas Exploration and Production, Off-Shore Gas Production, Natural Gas Fired 4Cycle Rich Burn Compressor Engines 50 To 499 HP",
    "2310022303":
        "Industrial Processes, Oil and Gas Exploration and Production, Off-Shore Gas Production, Natural Gas Fired 4Cycle Rich Burn Compressor Engines 500+ HP",
    "2310022401":
        "Industrial Processes, Oil and Gas Exploration and Production, Off-Shore Gas Production, Nat Gas Fired 4Cycle Rich Burn Compressor Engines <50 HP w/NSCR",
    "2310022402":
        "Industrial Processes, Oil and Gas Exploration and Production, Off-Shore Gas Production, Nat Gas Fired 4Cycle Rich Burn Compressor Engines 50 To 499 HP w/NSCR",
    "2310022403":
        "Industrial Processes, Oil and Gas Exploration and Production, Off-Shore Gas Production, Nat Gas Fired 4Cycle Rich Burn Compressor Engines 500+ HP w/NSCR",
    "2310022409":
        "Industrial Processes, Oil and Gas Exploration and Production, Off-Shore Gas Production, Total: All Nat Gas Fired 4Cycle Rich Burn Compressor Engines w/NSCR",
    "2310022410":
        "Industrial Processes, Oil and Gas Exploration and Production, Off-Shore Gas Production, Amine Unit",
    "2310022420":
        "Industrial Processes, Oil and Gas Exploration and Production, Off-Shore Gas Production, Dehydrator",
    "2310022501":
        "Industrial Processes, Oil and Gas Exploration and Production, Off-Shore Gas Production, Fugitives, Connectors: Gas Streams",
    "2310022502":
        "Industrial Processes, Oil and Gas Exploration and Production, Off-Shore Gas Production, Fugitives, Flanges: Gas Streams",
    "2310022505":
        "Industrial Processes, Oil and Gas Exploration and Production, Off-Shore Gas Production, Fugitives, Valves: Gas",
    "2310022506":
        "Industrial Processes, Oil and Gas Exploration and Production, Off-Shore Gas Production, Fugitives, Other: Gas",
    "2310023000":
        "Industrial Processes, Oil and Gas Exploration and Production, Coal Bed Methane Natural Gas, Dewatering Pump Engines",
    "2310023010":
        "Industrial Processes, Oil and Gas Exploration and Production, Coal Bed Methane Natural Gas, Storage Tanks: Condensate",
    "2310023030":
        "Industrial Processes, Oil and Gas Exploration and Production, Coal Bed Methane Natural Gas, Tank Truck/Railcar Loading: Condensate",
    "2310023100":
        "Industrial Processes, Oil and Gas Exploration and Production, Coal Bed Methane Natural Gas, CBM Well Heaters",
    "2310023102":
        "Industrial Processes, Oil and Gas Exploration and Production, Coal Bed Methane Natural Gas, CBM Fired 2Cycle Lean Burn Compressor Engines 50 To 499 HP",
    "2310023202":
        "Industrial Processes, Oil and Gas Exploration and Production, Coal Bed Methane Natural Gas, CBM Fired 4Cycle Lean Burn Compressor Engines 50 To 499 HP",
    "2310023251":
        "Industrial Processes, Oil and Gas Exploration and Production, Coal Bed Methane Natural Gas, Lateral Compressors 4 Cycle Lean Burn",
    "2310023300":
        "Industrial Processes, Oil and Gas Exploration and Production, Coal Bed Methane Natural Gas, Pneumatic Devices",
    "2310023302":
        "Industrial Processes, Oil and Gas Exploration and Production, Coal Bed Methane Natural Gas, CBM Fired 4Cycle Rich Burn Compressor Engines 50 To 499 HP",
    "2310023310":
        "Industrial Processes, Oil and Gas Exploration and Production, Coal Bed Methane Natural Gas, Pneumatic Pumps",
    "2310023351":
        "Industrial Processes, Oil and Gas Exploration and Production, Coal Bed Methane Natural Gas, Lateral Compressors 4 Cycle Rich Burn",
    "2310023400":
        "Industrial Processes, Oil and Gas Exploration and Production, Coal Bed Methane Natural Gas, Dehydrators",
    "2310023401":
        "Industrial Processes, Oil and Gas Exploration and Production, Coal Bed Methane Natural Gas, Dehydrators/Reboiler",
    "2310023410":
        "Industrial Processes, Oil and Gas Exploration and Production, Coal Bed Methane Natural Gas, Amine Units",
    "2310023509":
        "Industrial Processes, Oil and Gas Exploration and Production, Coal Bed Methane Natural Gas, Fugitives",
    "2310023511":
        "Industrial Processes, Oil and Gas Exploration and Production, Coal Bed Methane Natural Gas, Fugitives: Connectors",
    "2310023512":
        "Industrial Processes, Oil and Gas Exploration and Production, Coal Bed Methane Natural Gas, Fugitives: Flanges",
    "2310023513":
        "Industrial Processes, Oil and Gas Exploration and Production, Coal Bed Methane Natural Gas, Fugitives: Open Ended Lines",
    "2310023515":
        "Industrial Processes, Oil and Gas Exploration and Production, Coal Bed Methane Natural Gas, Fugitives: Valves",
    "2310023516":
        "Industrial Processes, Oil and Gas Exploration and Production, Coal Bed Methane Natural Gas, Fugitives: Other",
    "2310023600":
        "Industrial Processes, Oil and Gas Exploration and Production, Coal Bed Methane Natural Gas, CBM Well Completion: All Processes",
    "2310023601":
        "Industrial Processes, Oil and Gas Exploration and Production, Coal Bed Methane Natural Gas, Venting - Initial Completions",
    "2310023602":
        "Industrial Processes, Oil and Gas Exploration and Production, Coal Bed Methane Natural Gas, Venting - Recompletions",
    "2310023603":
        "Industrial Processes, Oil and Gas Exploration and Production, Coal Bed Methane Natural Gas, CBM Well Venting - Blowdowns",
    "2310023604":
        "Industrial Processes, Oil and Gas Exploration and Production, Coal Bed Methane Natural Gas, Venting - Compressor Startup",
    "2310023605":
        "Industrial Processes, Oil and Gas Exploration and Production, Coal Bed Methane Natural Gas, Venting - Compressor Shutdown",
    "2310023606":
        "Industrial Processes, Oil and Gas Exploration and Production, Coal Bed Methane Natural Gas, Mud Degassing",
    "2310023700":
        "Industrial Processes, Oil and Gas Exploration and Production, Coal Bed Methane Natural Gas, Abandoned Well: Plugged and Unplugged",
    "2310023701":
        "Industrial Processes, Oil and Gas Exploration and Production, Coal Bed Methane Natural Gas, Abandoned Well: Plugged",
    "2310023702":
        "Industrial Processes, Oil and Gas Exploration and Production, Coal Bed Methane Natural Gas, Abandoned Well: Unplugged",
    "2310030000":
        "Industrial Processes, Oil and Gas Exploration and Production, Natural Gas Liquids, Total: All Processes",
    "2310030210":
        "Industrial Processes, Oil and Gas Exploration and Production, Natural Gas Liquids, Gas Well Tanks - Flashing & Standing/Working/Breathing, Uncontrolled",
    "2310030220":
        "Industrial Processes, Oil and Gas Exploration and Production, Natural Gas Liquids, Gas Well Tanks - Flashing & Standing/Working/Breathing, Controlled",
    "2310030230":
        "Industrial Processes, Oil and Gas Exploration and Production, Natural Gas Liquids, Gas Well Tanks - Flaring",
    "2310030300":
        "Industrial Processes, Oil and Gas Exploration and Production, Natural Gas Liquids, Gas Well Water Tank Losses",
    "2310030400":
        "Industrial Processes, Oil and Gas Exploration and Production, Natural Gas Liquids, Truck Loading",
    "2310030401":
        "Industrial Processes, Oil and Gas Exploration and Production, Natural Gas Liquids, Gas Plant Truck Loading",
    "2310031000":
        "Industrial Processes, Oil and Gas Exploration and Production, Natural Gas Liquids : On-shore, Total: All Processes",
    "2310032000":
        "Industrial Processes, Oil and Gas Exploration and Production, Natural Gas Liquids : Off-shore, Total: All Processes",
    "2310111000":
        "Industrial Processes, Oil and Gas Exploration and Production, On-Shore Oil Exploration, All Processes",
    "2310111100":
        "Industrial Processes, Oil and Gas Exploration and Production, On-Shore Oil Exploration, Mud Degassing",
    "2310111401":
        "Industrial Processes, Oil and Gas Exploration and Production, On-Shore Oil Exploration, Oil Well Pneumatic Pumps",
    "2310111700":
        "Industrial Processes, Oil and Gas Exploration and Production, On-Shore Oil Exploration, Oil Well Completion: All Processes",
    "2310111701":
        "Industrial Processes, Oil and Gas Exploration and Production, On-Shore Oil Exploration, Oil Well Completion: Flaring",
    "2310111702":
        "Industrial Processes, Oil and Gas Exploration and Production, On-Shore Oil Exploration, Oil Well Completion: Venting",
    "2310111800":
        "Industrial Processes, Oil and Gas Exploration and Production, On-Shore Oil Exploration, Abandoned Well: Plugged and Unplugged",
    "2310111801":
        "Industrial Processes, Oil and Gas Exploration and Production, On-Shore Oil Exploration, Abandoned Well: Plugged",
    "2310111802":
        "Industrial Processes, Oil and Gas Exploration and Production, On-Shore Oil Exploration, Abandoned Well: Unplugged",
    "2310112000":
        "Industrial Processes, Oil and Gas Exploration and Production, Off-Shore Oil Exploration, All Processes",
    "2310112100":
        "Industrial Processes, Oil and Gas Exploration and Production, Off-Shore Oil Exploration, Mud Degassing Activities",
    "2310112401":
        "Industrial Processes, Oil and Gas Exploration and Production, Off-Shore Oil Exploration, Oil Well Pneumatic Pumps",
    "2310112700":
        "Industrial Processes, Oil and Gas Exploration and Production, Off-Shore Oil Exploration, Oil Well Completion: All Processes",
    "2310112701":
        "Industrial Processes, Oil and Gas Exploration and Production, Off-Shore Oil Exploration, Oil Well Completion: Flaring",
    "2310112702":
        "Industrial Processes, Oil and Gas Exploration and Production, Off-Shore Oil Exploration, Oil Well Completion: Venting",
    "2310121000":
        "Industrial Processes, Oil and Gas Exploration and Production, On-Shore Gas Exploration, All Processes",
    "2310121100":
        "Industrial Processes, Oil and Gas Exploration and Production, On-Shore Gas Exploration, Mud Degassing",
    "2310121401":
        "Industrial Processes, Oil and Gas Exploration and Production, On-Shore Gas Exploration, Gas Well Pneumatic Pumps",
    "2310121700":
        "Industrial Processes, Oil and Gas Exploration and Production, On-Shore Gas Exploration, Gas Well Completion: All Processes",
    "2310121701":
        "Industrial Processes, Oil and Gas Exploration and Production, On-Shore Gas Exploration, Gas Well Completion: Flaring",
    "2310121702":
        "Industrial Processes, Oil and Gas Exploration and Production, On-Shore Gas Exploration, Gas Well Completion: Venting",
    "2310121800":
        "Industrial Processes, Oil and Gas Exploration and Production, On-Shore Gas Exploration, Abandoned Well: Plugged and Unplugged",
    "2310121801":
        "Industrial Processes, Oil and Gas Exploration and Production, On-Shore Gas Exploration, Abandoned Well: Plugged",
    "2310121802":
        "Industrial Processes, Oil and Gas Exploration and Production, On-Shore Gas Exploration, Abandoned Well: Unplugged",
    "2310122000":
        "Industrial Processes, Oil and Gas Exploration and Production, Off-Shore Gas Exploration, All Processes",
    "2310122100":
        "Industrial Processes, Oil and Gas Exploration and Production, Off-Shore Gas Exploration, Mud Degassing",
    "2310122401":
        "Industrial Processes, Oil and Gas Exploration and Production, Off-Shore Gas Exploration, Gas Well Pneumatic Pumps",
    "2310122700":
        "Industrial Processes, Oil and Gas Exploration and Production, Off-Shore Gas Exploration, Gas Well Completion: All Processes",
    "2310122701":
        "Industrial Processes, Oil and Gas Exploration and Production, Off-Shore Gas Exploration, Gas Well Completion: Flaring",
    "2310122702":
        "Industrial Processes, Oil and Gas Exploration and Production, Off-Shore Gas Exploration, Gas Well Completion: Venting",
    "2310300220":
        "Industrial Processes, Oil and Gas Exploration and Production, All Processes - Conventional, Drill Rigs",
    "2310321010":
        "Industrial Processes, Oil and Gas Exploration and Production, On-Shore Gas Production - Conventional, Storage Tanks: Condensate",
    "2310321100":
        "Industrial Processes, Oil and Gas Exploration and Production, On-Shore Gas Production - Conventional, Gas Well Heaters",
    "2310321400":
        "Industrial Processes, Oil and Gas Exploration and Production, On-Shore Gas Production - Conventional, Gas Well Dehydrators",
    "2310321603":
        "Industrial Processes, Oil and Gas Exploration and Production, On-Shore Gas Production - Conventional, Gas Well Venting - Blowdowns",
    "2310400220":
        "Industrial Processes, Oil and Gas Exploration and Production, All Processes - Unconventional, Drill Rigs",
    "2310421010":
        "Industrial Processes, Oil and Gas Exploration and Production, On-Shore Gas Production - Unconventional, Storage Tanks: Condensate",
    "2310421100":
        "Industrial Processes, Oil and Gas Exploration and Production, On-Shore Gas Production - Unconventional, Gas Well Heaters",
    "2310421400":
        "Industrial Processes, Oil and Gas Exploration and Production, On-Shore Gas Production - Unconventional, Gas Well Dehydrators",
    "2310421603":
        "Industrial Processes, Oil and Gas Exploration and Production, On-Shore Gas Production - Unconventional, Gas Well Venting - Blowdowns",
    "2310421700":
        "Industrial Processes, Oil and Gas Exploration and Production, On-Shore Gas Production - Unconventional, Gas Well Completion: All Processes",
    "2311000000":
        "Industrial Processes, Construction: SIC 15 - 17, All Processes, Total",
    "2311000010":
        "Industrial Processes, Construction: SIC 15 - 17, All Processes, Land Clearing",
    "2311000020":
        "Industrial Processes, Construction: SIC 15 - 17, All Processes, Demolition",
    "2311000030":
        "Industrial Processes, Construction: SIC 15 - 17, All Processes, Blasting",
    "2311000040":
        "Industrial Processes, Construction: SIC 15 - 17, All Processes, Ground Excavations",
    "2311000050":
        "Industrial Processes, Construction: SIC 15 - 17, All Processes, Cut and Fill Operations",
    "2311000060":
        "Industrial Processes, Construction: SIC 15 - 17, All Processes, Construction",
    "2311000070":
        "Industrial Processes, Construction: SIC 15 - 17, All Processes, Vehicle Traffic",
    "2311000080":
        "Industrial Processes, Construction: SIC 15 - 17, All Processes, Welding Operations",
    "2311000100":
        "Industrial Processes, Construction: SIC 15 - 17, All Processes, Wind Erosion",
    "2311010000":
        "Industrial Processes, Construction: SIC 15 - 17, Residential, Total",
    "2311010010":
        "Industrial Processes, Construction: SIC 15 - 17, Residential, Land Clearing",
    "2311010020":
        "Industrial Processes, Construction: SIC 15 - 17, Residential, Demolition",
    "2311010030":
        "Industrial Processes, Construction: SIC 15 - 17, Residential, Blasting",
    "2311010040":
        "Industrial Processes, Construction: SIC 15 - 17, Residential, Ground Excavations",
    "2311010050":
        "Industrial Processes, Construction: SIC 15 - 17, Residential, Cut and Fill Operations",
    "2311010060":
        "Industrial Processes, Construction: SIC 15 - 17, Residential, Construction",
    "2311010070":
        "Industrial Processes, Construction: SIC 15 - 17, Residential, Vehicle Traffic",
    "2311010080":
        "Industrial Processes, Construction: SIC 15 - 17, Residential, Welding Operations",
    "2311010100":
        "Industrial Processes, Construction: SIC 15 - 17, Residential, Wind Erosion",
    "2311020000":
        "Industrial Processes, Construction: SIC 15 - 17, Industrial/Commercial/Institutional, Total",
    "2311020010":
        "Industrial Processes, Construction: SIC 15 - 17, Industrial/Commercial/Institutional, Land Clearing",
    "2311020020":
        "Industrial Processes, Construction: SIC 15 - 17, Industrial/Commercial/Institutional, Demolition",
    "2311020030":
        "Industrial Processes, Construction: SIC 15 - 17, Industrial/Commercial/Institutional, Blasting",
    "2311020040":
        "Industrial Processes, Construction: SIC 15 - 17, Industrial/Commercial/Institutional, Ground Excavations",
    "2311020050":
        "Industrial Processes, Construction: SIC 15 - 17, Industrial/Commercial/Institutional, Cut and Fill Operations",
    "2311020060":
        "Industrial Processes, Construction: SIC 15 - 17, Industrial/Commercial/Institutional, Construction",
    "2311020070":
        "Industrial Processes, Construction: SIC 15 - 17, Industrial/Commercial/Institutional, Vehicle Traffic",
    "2311020080":
        "Industrial Processes, Construction: SIC 15 - 17, Industrial/Commercial/Institutional, Welding Operations",
    "2311020100":
        "Industrial Processes, Construction: SIC 15 - 17, Industrial/Commercial/Institutional, Wind Erosion",
    "2311030000":
        "Industrial Processes, Construction: SIC 15 - 17, Road Construction, Total",
    "2311030010":
        "Industrial Processes, Construction: SIC 15 - 17, Road Construction, Land Clearing",
    "2311030020":
        "Industrial Processes, Construction: SIC 15 - 17, Road Construction, Demolition",
    "2311030030":
        "Industrial Processes, Construction: SIC 15 - 17, Road Construction, Blasting",
    "2311030040":
        "Industrial Processes, Construction: SIC 15 - 17, Road Construction, Ground Excavations",
    "2311030050":
        "Industrial Processes, Construction: SIC 15 - 17, Road Construction, Cut and Fill Operations",
    "2311030060":
        "Industrial Processes, Construction: SIC 15 - 17, Road Construction, Construction",
    "2311030070":
        "Industrial Processes, Construction: SIC 15 - 17, Road Construction, Vehicle Traffic",
    "2311030080":
        "Industrial Processes, Construction: SIC 15 - 17, Road Construction, Welding Operations",
    "2311030100":
        "Industrial Processes, Construction: SIC 15 - 17, Road Construction, Wind Erosion",
    "2311040000":
        "Industrial Processes, Construction: SIC 15 - 17, Special Trade Construction, Total",
    "2311040080":
        "Industrial Processes, Construction: SIC 15 - 17, Special Trade Construction, Welding Operations",
    "2311040100":
        "Industrial Processes, Construction: SIC 15 - 17, Special Trade Construction, Wind Erosion",
    "2312000000":
        "Industrial Processes, Machinery: SIC 35, All Processes, Total",
    "2312050000":
        "Industrial Processes, Machinery: SIC 35, Metalworking Machinery: Tool and Die Maker, Total",
    "2325000000":
        "Industrial Processes, Mining and Quarrying: SIC 10 and SIC 14, All Processes, Total",
    "2325010000":
        "Industrial Processes, Mining and Quarrying: SIC 10 and SIC 14, Dimension Stone, Total",
    "2325020000":
        "Industrial Processes, Mining and Quarrying: SIC 10 and SIC 14, Crushed and Broken Stone, Total",
    "2325030000":
        "Industrial Processes, Mining and Quarrying: SIC 10 and SIC 14, Sand and Gravel, Total",
    "2325040000":
        "Industrial Processes, Mining and Quarrying: SIC 10 and SIC 14, Clay, Ceramic, and Refractory, Total",
    "2325050000":
        "Industrial Processes, Mining and Quarrying: SIC 10 and SIC 14, Chemical and Fertilizer Materials, Total",
    "2325060000":
        "Industrial Processes, Mining and Quarrying: SIC 10 and SIC 14, Lead Ore Mining and Milling, Total",
    "2390001000":
        "Industrial Processes, In-process Fuel Use, Anthracite Coal, Total",
    "2390002000":
        "Industrial Processes, In-process Fuel Use, Bituminous/Subbituminous Coal, Total",
    "2390004000":
        "Industrial Processes, In-process Fuel Use, Distillate Oil, Total",
    "2390005000":
        "Industrial Processes, In-process Fuel Use, Residual Oil, Total",
    "2390006000":
        "Industrial Processes, In-process Fuel Use, Natural Gas, Total",
    "2390007000":
        "Industrial Processes, In-process Fuel Use, Liquified Petroleum Gas (LPG), Total",
    "2390008000":
        "Industrial Processes, In-process Fuel Use, Wood, Total",
    "2390009000":
        "Industrial Processes, In-process Fuel Use, Coke, Total",
    "2390010000":
        "Industrial Processes, In-process Fuel Use, Process Gas, Total",
    "2399000000":
        "Industrial Processes, Industrial Processes: NEC, Industrial Processes: NEC, Total",
    "2399010000":
        "Industrial Processes, Industrial Processes: NEC, Refrigerant Losses, All Processes",
    "3210000660":
        "Industrial Processes, Oil and Gas Exploration and Production, All Processes, Hydraulic Fracturing Engines",
    "3333333333":
        "LPG Distribution, LPG Distribution, LPG Distribution, LPG Distribution",
    "2801000000":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Agriculture - Crops, Total",
    "2801000001":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Agriculture - Crops, Land Breaking",
    "2801000002":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Agriculture - Crops, Planting",
    "2801000003":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Agriculture - Crops, Tilling",
    "2801000004":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Agriculture - Crops, Defoliation",
    "2801000005":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Agriculture - Crops, Harvesting",
    "2801000006":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Agriculture - Crops, Drying",
    "2801000007":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Agriculture - Crops, Loading",
    "2801000008":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Agriculture - Crops, Transport",
    "2801500000":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Agricultural Field Burning - whole field set on fire, Unspecified crop type and Burn Method",
    "2801500001":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Agricultural Field Burning - whole field set on fire, NATURAL (Native American Fire Use)",
    "2801500002":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Agricultural Field Burning - whole field set on fire, ANTHROPOGENIC",
    "2801500100":
        "Miscellaneous Area Sources, Agriculture Production - Crops - as nonpoint, Agricultural Field Burning - whole field set on fire, Field Crops Unspecified",
    "2801500111":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Agricultural Field Burning - whole field set on fire, Field Crop is Alfalfa : Headfire Burning",
    "2801500112":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Agricultural Field Burning - whole field set on fire, Field Crop is Alfalfa: Backfire Burning",
    "2801500120":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Agricultural Field Burning - whole field set on fire, Field Crop is Asparagus: Burning Techniques Not Significant",
    "2801500130":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Agricultural Field Burning - whole field set on fire, Field Crop is Barley: Burning Techniques Not Significant",
    "2801500141":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Agricultural Field Burning - whole field set on fire, Field Crop is Bean (red): Headfire Burning",
    "2801500142":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Agricultural Field Burning - whole field set on fire, Field Crop is Bean (red): Backfire Burning",
    "2801500150":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Agricultural Field Burning - whole field set on fire, Field Crop is Corn: Burning Techniques Not Important",
    "2801500151":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Agricultural Field Burning - whole field set on fire, Double Crop Winter Wheat and Corn",
    "2801500152":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Agricultural Field Burning - whole field set on fire, DoubleCrop Corn and Soybeans",
    "2801500160":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Agricultural Field Burning - whole field set on fire, Field Crop is Cotton: Burning Techniques Not Important",
    "2801500161":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Agricultural Field Burning - whole field set on fire, DoubleCrop Soybeans and Cotton",
    "2801500170":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Agricultural Field Burning - whole field set on fire, Field Crop is Grasses: Burning Techniques Not Important",
    "2801500171":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Agricultural Field Burning - whole field set on fire, Fallow",
    "2801500181":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Agricultural Field Burning - whole field set on fire, Field Crop is Hay (wild): Headfire Burning",
    "2801500182":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Agricultural Field Burning - whole field set on fire, Field Crop is Hay (wild): Backfire Burning",
    "2801500191":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Agricultural Field Burning - whole field set on fire, Field Crop is Oats: Headfire Burning",
    "2801500192":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Agricultural Field Burning - whole field set on fire, Field Crop is Oats: Backfire Burning",
    "2801500201":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Agricultural Field Burning - whole field set on fire, Field Crop is Pea: Headfire Burning",
    "2801500202":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Agricultural Field Burning - whole field set on fire, Field Crop is Pea: Backfire Burning",
    "2801500210":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Agricultural Field Burning - whole field set on fire, Field Crop is Pineapple: Burning Techniques Not Significant",
    "2801500220":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Agricultural Field Burning - whole field set on fire, Field Crop is Rice: Burning Techniques Not Significant",
    "2801500230":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Agricultural Field Burning - whole field set on fire, Field Crop is Safflower: Burning Techniques Not Significant",
    "2801500240":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Agricultural Field Burning - whole field set on fire, Field Crop is Sorghum: Burning Techniques Not Significant",
    "2801500250":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Agricultural Field Burning - whole field set on fire, Field Crop is Sugar Cane: Burning Techniques Not Significant",
    "2801500261":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Agricultural Field Burning - whole field set on fire, Field Crop is Wheat: Headfire Burning",
    "2801500262":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Agricultural Field Burning - whole field set on fire, Field Crop is Wheat: Backfire Burning",
    "2801500263":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Agricultural Field Burning - whole field set on fire, DoubleCrop Winter Wheat and Cotton",
    "2801500264":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Agricultural Field Burning - whole field set on fire, DoubleCrop Winter Wheat and Soybeans",
    "2801500300":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Agricultural Field Burning - whole field set on fire, Orchard Crop Unspecified",
    "2801500310":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Agricultural Field Burning - whole field set on fire, Orchard Crop is Almond",
    "2801500320":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Agricultural Field Burning - whole field set on fire, Orchard Crop is Apple",
    "2801500330":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Agricultural Field Burning - whole field set on fire, Orchard Crop is Apricot",
    "2801500340":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Agricultural Field Burning - whole field set on fire, Orchard Crop is Avocado",
    "2801500350":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Agricultural Field Burning - whole field set on fire, Orchard Crop is Cherry",
    "2801500360":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Agricultural Field Burning - whole field set on fire, Orchard Crop is Citrus (orange, lemon)",
    "2801500370":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Agricultural Field Burning - whole field set on fire, Orchard Crop is Date palm",
    "2801500380":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Agricultural Field Burning - whole field set on fire, Orchard Crop is Fig",
    "2801500390":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Agricultural Field Burning - whole field set on fire, Orchard Crop is Nectarine",
    "2801500400":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Agricultural Field Burning - whole field set on fire, Orchard Crop is Olive",
    "2801500410":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Agricultural Field Burning - whole field set on fire, Orchard Crop is Peach",
    "2801500420":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Agricultural Field Burning - whole field set on fire, Orchard Crop is Pear",
    "2801500430":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Agricultural Field Burning - whole field set on fire, Orchard Crop is Prune",
    "2801500440":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Agricultural Field Burning - whole field set on fire, Orchard Crop is Walnut",
    "2801500450":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Agricultural Field Burning - whole field set on fire, Orchard Crop is Filbert (Hazelnut)",
    "2801500500":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Agricultural Field Burning - whole field set on fire, Vine Crop Unspecified",
    "2801500600":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Agricultural Field Burning - whole field set on fire, Forest Residues Unspecified",
    "2801500610":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Agricultural Field Burning - whole field set on fire, Forest Residues: Species are Hemlock, Douglas fir, Cedar",
    "2801500620":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Agricultural Field Burning - whole field set on fire, Forest Residues: Species is Ponderosa Pine (see also 28-10-015-000)",
    "2801501000":
        "Miscellaneous Area Sources, Agriculture Production - Crops - as nonpoint, Agricultural Propaning - tractor-pulled burners to burn stubble only, Unspecified crop types",
    "2801501105":
        "Miscellaneous Area Sources, Agriculture Production - Crops - as nonpoint, Agricultural Propaning - tractor-pulled burners to burn stubble only, Cereal Grains, Total",
    "2801501130":
        "Miscellaneous Area Sources, Agriculture Production - Crops - as nonpoint, Agricultural Propaning - tractor-pulled burners to burn stubble only, Barley",
    "2801501170":
        "Miscellaneous Area Sources, Agriculture Production - Crops - as nonpoint, Agricultural Propaning - tractor-pulled burners to burn stubble only, Grass",
    "2801501260":
        "Miscellaneous Area Sources, Agriculture Production - Crops - as nonpoint, Agricultural Propaning - tractor-pulled burners to burn stubble only, Wheat",
    "2801501270":
        "Miscellaneous Area Sources, Agriculture Production - Crops - as nonpoint, Agricultural Propaning - tractor-pulled burners to burn stubble only, Mint",
    "2801502000":
        "Miscellaneous Area Sources, Agriculture Production - Crops - as nonpoint, Agricultural Stack Burning - straw stacks moved from field for burning, Unspecified crop types",
    "2801502105":
        "Miscellaneous Area Sources, Agriculture Production - Crops - as nonpoint, Agricultural Stack Burning - straw stacks moved from field for burning, Cereal Grains, Total",
    "2801502130":
        "Miscellaneous Area Sources, Agriculture Production - Crops - as nonpoint, Agricultural Stack Burning - straw stacks moved from field for burning, Barley",
    "2801502170":
        "Miscellaneous Area Sources, Agriculture Production - Crops - as nonpoint, Agricultural Stack Burning - straw stacks moved from field for burning, Grass",
    "2801502260":
        "Miscellaneous Area Sources, Agriculture Production - Crops - as nonpoint, Agricultural Stack Burning - straw stacks moved from field for burning, Wheat",
    "2801502270":
        "Miscellaneous Area Sources, Agriculture Production - Crops - as nonpoint, Agricultural Stack Burning - straw stacks moved from field for burning, Mint",
    "2801520000":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Orchard Heaters, Total, all fuels",
    "2801520004":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Orchard Heaters, Diesel",
    "2801520006":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Orchard Heaters, Natural Gas",
    "2801520010":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Orchard Heaters, Propane",
    "2801530000":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Country Grain Elevators, Total",
    "2801600000":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Country Grain Elevators, Total",
    "2801600300":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Agricultural Field Burning - Pile Burning, Orchard Crop Other Not Elsewhere Classified",
    "2801600310":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Agricultural Field Burning - Pile Burning, Orchard Crop is Almond",
    "2801600320":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Agricultural Field Burning - Pile Burning, Orchard Crop is Apple",
    "2801600330":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Agricultural Field Burning - Pile Burning, Orchard Crop is Apricot",
    "2801600340":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Agricultural Field Burning - Pile Burning, Orchard Crop is Avocado",
    "2801600350":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Agricultural Field Burning - Pile Burning, Orchard Crop is Cherry",
    "2801600360":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Agricultural Field Burning - Pile Burning, Orchard Crop is Citrus (orange, lemon)",
    "2801600370":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Agricultural Field Burning - Pile Burning, Orchard Crop is Date palm",
    "2801600380":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Agricultural Field Burning - Pile Burning, Orchard Crop is Fig",
    "2801600390":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Agricultural Field Burning - Pile Burning, Orchard Crop is Nectarine",
    "2801600400":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Agricultural Field Burning - Pile Burning, Orchard Crop is Olive",
    "2801600410":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Agricultural Field Burning - Pile Burning, Orchard Crop is Peach",
    "2801600420":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Agricultural Field Burning - Pile Burning, Orchard Crop is Pear",
    "2801600430":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Agricultural Field Burning - Pile Burning, Orchard Crop is Prune",
    "2801600440":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Agricultural Field Burning - Pile Burning, Orchard Crop is Walnut",
    "2801600450":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Agricultural Field Burning - Pile Burning, Orchard Crop is Filbert (Hazelnut)",
    "2801600500":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Agricultural Field Burning - Pile Burning, Vine Crop Other Not Elsewhere Classified",
    "2801700000":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Fertilizer Application, Total Fertilizers",
    "2801700001":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Fertilizer Application, Anhydrous Ammonia",
    "2801700002":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Fertilizer Application, Aqueous Ammonia",
    "2801700003":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Fertilizer Application, Nitrogen Solutions",
    "2801700004":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Fertilizer Application, Urea",
    "2801700005":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Fertilizer Application, Ammonium Nitrate",
    "2801700006":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Fertilizer Application, Ammonium Sulfate",
    "2801700007":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Fertilizer Application, Ammonium Thiosulfate",
    "2801700008":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Fertilizer Application, Other Straight Nitrogen",
    "2801700009":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Fertilizer Application, Ammonium Phosphates (see also subsets (-13, -14, -15)",
    "2801700010":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Fertilizer Application, N-P-K (multi-grade nutrient fertilizers)",
    "2801700011":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Fertilizer Application, Calcium Ammonium Nitrate",
    "2801700012":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Fertilizer Application, Potassium Nitrate",
    "2801700013":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Fertilizer Application, Diammonium Phosphate",
    "2801700014":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Fertilizer Application, Monoammonium Phosphate",
    "2801700015":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Fertilizer Application, Liquid Ammonium Polyphosphate",
    "2801700099":
        "Miscellaneous Area Sources, Agriculture Production - Crops, Fertilizer Application, Miscellaneous Fertilizers",
    "2802004001":
        "Miscellaneous Area Sources, Agricultural Crop Usage, Agriculture Silage, Storage",
    "2802004002":
        "Miscellaneous Area Sources, Agricultural Crop Usage, Agriculture Silage, Mixing",
    "2802004003":
        "Miscellaneous Area Sources, Agricultural Crop Usage, Agriculture Silage, Feeding",
    "2805000000":
        "Miscellaneous Area Sources, Agriculture Production - Livestock, Agriculture - Livestock, Total",
    "2805001000":
        "Miscellaneous Area Sources, Agriculture Production - Livestock, Dust kicked up by Livestock, Beef cattle - finishing operations on feedlots (drylots)",
    "2805001001":
        "Miscellaneous Area Sources, Agriculture Production - Livestock, Beef cattle - finishing operations on feedlots (drylots), Feed Preparation",
    "2805001010":
        "Miscellaneous Area Sources, Agriculture Production - Livestock, Dust kicked up by Livestock, Dairy Cattle",
    "2805001020":
        "Miscellaneous Area Sources, Agriculture Production - Livestock, Dust kicked up by Livestock, Broilers",
    "2805001030":
        "Miscellaneous Area Sources, Agriculture Production - Livestock, Dust kicked up by Livestock, Layers",
    "2805001040":
        "Miscellaneous Area Sources, Agriculture Production - Livestock, Dust kicked up by Livestock, Swine",
    "2805001050":
        "Miscellaneous Area Sources, Agriculture Production - Livestock, Dust kicked up by Livestock, Turkeys",
    "2805001099":
        "Miscellaneous Area Sources, Agriculture Production - Livestock, Dust kicked up by Livestock, All Animals",
    "2805001100":
        "Miscellaneous Area Sources, Agriculture Production - Livestock, Beef cattle waste, Beef Cattle - Finishing Operations on Feedlots (Drylots): Confinement",
    "2805001101":
        "Miscellaneous Area Sources, Agriculture Production - Livestock, Beef cattle waste, Beef cattle - finishing operations on pasture/range: Confinement",
    "2805001200":
        "Miscellaneous Area Sources, Agriculture Production - Livestock, Beef cattle waste, Beef Cattle - Finishing Operations on Feedlots (Drylots): Manure Handling and Storage",
    "2805001300":
        "Miscellaneous Area Sources, Agriculture Production - Livestock, Beef cattle waste, Beef Cattle - finishing operations on feedlots (drylots): Land application of manure",
    "2805001400":
        "Miscellaneous Area Sources, Agriculture Production - Livestock, Beef cattle waste, Beef cattle production composite: Total for all Beef cattle production composite processes",
    "2805002000":
        "Miscellaneous Area Sources, Agriculture Production - Livestock, Beef cattle production composite, Not Elsewhere Classified",
    "2805003000":
        "Miscellaneous Area Sources, Agriculture Production - Livestock, Beef cattle waste, Beef cattle production composite: Total for all Beef cattle production composite processes",
    "2805003100":
        "Miscellaneous Area Sources, Agriculture Production - Livestock, Beef cattle waste, Beef cattle - finishing operations on pasture/range: Confinement",
    "2805005000":
        "Miscellaneous Area Sources, Agriculture Production - Livestock, Poultry Operations, Total (see 28-05-030, 28-05-007, -008, -009)",
    "2805005001":
        "Miscellaneous Area Sources, Agriculture Production - Livestock, Poultry Operations, Feed Preparation",
    "2805007000":
        "Miscellaneous Area Sources, Agriculture Production - Livestock, Poultry Waste, Poultry Production - Layers: Total for All Processes",
    "2805007100":
        "Miscellaneous Area Sources, Agriculture Production - Livestock, Poultry Waste, Poultry Production - Layers with Dry Manure Management Systems: Confinement",
    "2805007300":
        "Miscellaneous Area Sources, Agriculture Production - Livestock, Poultry Waste, Poultry Production - Layers with Dry Manure Management systems: Land Application of Manure",
    "2805008100":
        "Miscellaneous Area Sources, Agriculture Production - Livestock, Poultry production - layers with wet manure management systems, Confinement",
    "2805008200":
        "Miscellaneous Area Sources, Agriculture Production - Livestock, Poultry production - layers with wet manure management systems, Manure handling and storage",
    "2805008300":
        "Miscellaneous Area Sources, Agriculture Production - Livestock, Poultry production - layers with wet manure management systems, Land application of manure",
    "2805009000":
        "Miscellaneous Area Sources, Agriculture Production - Livestock, Poultry production - broilers, Total for All Processes",
    "2805009100":
        "Miscellaneous Area Sources, Agriculture Production - Livestock, Poultry production - broilers, Confinement",
    "2805009200":
        "Miscellaneous Area Sources, Agriculture Production - Livestock, Poultry production - broilers, Manure handling and storage",
    "2805009300":
        "Miscellaneous Area Sources, Agriculture Production - Livestock, Poultry production - broilers, Land application of manure",
    "2805010000":
        "Miscellaneous Area Sources, Agriculture Production - Livestock, Poultry production - turkeys, Total (use 2805020, -001, -002, or -003 for Cattle Waste",
    "2805010001":
        "Miscellaneous Area Sources, Agriculture Production - Livestock, Poultry production - turkeys, Feed Preparation",
    "2805010100":
        "Miscellaneous Area Sources, Agriculture Production - Livestock, Poultry production - turkeys, Confinement",
    "2805010200":
        "Miscellaneous Area Sources, Agriculture Production - Livestock, Poultry production - turkeys, Manure handling and storage",
    "2805010300":
        "Miscellaneous Area Sources, Agriculture Production - Livestock, Poultry production - turkeys, Land application of manure",
    "2805015000":
        "Miscellaneous Area Sources, Agriculture Production - Livestock, Hog Operations, Total (use 2805025000)",
    "2805015001":
        "Miscellaneous Area Sources, Agriculture Production - Livestock, Hog Operations, Feed Preparation",
    "2805018000":
        "Miscellaneous Area Sources, Agriculture Production - Livestock, Dairy cattle composite, Not Elsewhere Classified",
    "2805019000":
        "Miscellaneous Area Sources, Agriculture Production - Livestock, Dairy Cattle Waste, Dairy cattle composite: Total for All Processes",
    "2805019100":
        "Miscellaneous Area Sources, Agriculture Production - Livestock, Dairy Cattle Waste, Dairy cattle - flush dairy: Confinement",
    "2805019200":
        "Miscellaneous Area Sources, Agriculture Production - Livestock, Dairy Cattle Waste, Dairy cattle - flush dairy: Manure handling and storage",
    "2805019300":
        "Miscellaneous Area Sources, Agriculture Production - Livestock, Dairy Cattle Waste, Dairy cattle - flush dairy: Land application of manure",
    "2805020000":
        "Miscellaneous Area Sources, Agriculture Production - Livestock, Cattle and Calves Waste Emissions, Total (see also 28-05-001, -002, -003)",
    "2805020001":
        "Miscellaneous Area Sources, Agriculture Production - Livestock, Cattle and Calves Waste Emissions, Milk Cows",
    "2805020002":
        "Miscellaneous Area Sources, Agriculture Production - Livestock, Cattle and Calves Waste Emissions, Beef Cows",
    "2805020003":
        "Miscellaneous Area Sources, Agriculture Production - Livestock, Cattle and Calves Waste Emissions, Heifers and Heifer Calves",
    "2805020004":
        "Miscellaneous Area Sources, Agriculture Production - Livestock, Cattle and Calves Waste Emissions, Steers, Steer Calves, Bulls, and Bull Calves",
    "2805021100":
        "Miscellaneous Area Sources, Agriculture Production - Livestock, Dairy cattle - scrape dairy, Confinement",
    "2805021200":
        "Miscellaneous Area Sources, Agriculture Production - Livestock, Dairy cattle - scrape dairy, Manure handling and storage",
    "2805021300":
        "Miscellaneous Area Sources, Agriculture Production - Livestock, Dairy cattle - scrape dairy, Land application of manure",
    "2805022100":
        "Miscellaneous Area Sources, Agriculture Production - Livestock, Dairy cattle - deep pit dairy, Confinement",
    "2805022200":
        "Miscellaneous Area Sources, Agriculture Production - Livestock, Dairy cattle - deep pit dairy, Manure handling and storage",
    "2805022300":
        "Miscellaneous Area Sources, Agriculture Production - Livestock, Dairy cattle - deep pit dairy, Land application of manure",
    "2805023100":
        "Miscellaneous Area Sources, Agriculture Production - Livestock, Dairy cattle - drylot/pasture dairy, Confinement",
    "2805023200":
        "Miscellaneous Area Sources, Agriculture Production - Livestock, Dairy cattle - drylot/pasture dairy, Manure handling and storage",
    "2805023300":
        "Miscellaneous Area Sources, Agriculture Production - Livestock, Dairy cattle - drylot/pasture dairy, Land application of manure",
    "2805025000":
        "Miscellaneous Area Sources, Agriculture Production - Livestock, Swine production composite, Not Elsewhere Classified (see also 28-05-039, -047, -053)",
    "2805030000":
        "Miscellaneous Area Sources, Agriculture Production - Livestock, Poultry Waste Emissions, Not Elsewhere Classified (see also 28-05-007, -008, -009)",
    "2805030001":
        "Miscellaneous Area Sources, Agriculture Production - Livestock, Poultry Waste Emissions, Pullet Chicks and Pullets less than 13 weeks old",
    "2805030002":
        "Miscellaneous Area Sources, Agriculture Production - Livestock, Poultry Waste Emissions, Pullets 13 weeks old and older but less than 20 weeks old",
    "2805030003":
        "Miscellaneous Area Sources, Agriculture Production - Livestock, Poultry Waste Emissions, Layers",
    "2805030004":
        "Miscellaneous Area Sources, Agriculture Production - Livestock, Poultry Waste Emissions, Broilers",
    "2805030007":
        "Miscellaneous Area Sources, Agriculture Production - Livestock, Poultry Waste Emissions, Ducks",
    "2805030008":
        "Miscellaneous Area Sources, Agriculture Production - Livestock, Poultry Waste Emissions, Geese",
    "2805030009":
        "Miscellaneous Area Sources, Agriculture Production - Livestock, Poultry Waste Emissions, Turkeys",
    "2805035000":
        "Miscellaneous Area Sources, Agriculture Production - Livestock, Horses and Ponies Waste Emissions, Not Elsewhere Classified",
    "2805039000":
        "Miscellaneous Area Sources, Agriculture Production - Livestock, Swine Waste, Swine production: Total for All Processes",
    "2805039100":
        "Miscellaneous Area Sources, Agriculture Production - Livestock, Swine Waste, Swine Production - Operations with Lagoons (Unspecified Animal Age): Confinement",
    "2805039200":
        "Miscellaneous Area Sources, Agriculture Production - Livestock, Swine Waste, Swine Production - Operations with Lagoons (Unspecified Animal Age): Manure Handling and Storage",
    "2805039300":
        "Miscellaneous Area Sources, Agriculture Production - Livestock, Swine Waste, Swine Production - Operations with Lagoons (Unspecified Animal Age): Land Application of Manure",
    "2805040000":
        "Miscellaneous Area Sources, Agriculture Production - Livestock, Sheep and Lambs Waste Emissions, Total",
    "2805045000":
        "Miscellaneous Area Sources, Agriculture Production - Livestock, Goats Waste Emissions, Not Elsewhere Classified",
    "2805045001":
        "Miscellaneous Area Sources, Agriculture Production - Livestock, Goats Waste Emissions, Total",
    "2805045002":
        "Miscellaneous Area Sources, Agriculture Production - Livestock, Goats Waste Emissions, Angora Goats",
    "2805045003":
        "Miscellaneous Area Sources, Agriculture Production - Livestock, Goats Waste Emissions, Milk Goats",
    "2805047100":
        "Miscellaneous Area Sources, Agriculture Production - Livestock, Swine production - deep-pit house operations (unspecified animal age), Confinement",
    "2805047300":
        "Miscellaneous Area Sources, Agriculture Production - Livestock, Swine production - deep-pit house operations (unspecified animal age), Land application of manure",
    "2805053100":
        "Miscellaneous Area Sources, Agriculture Production - Livestock, Swine production - outdoor operations (unspecified animal age), Confinement",
    "2805100000":
        "Miscellaneous Area Sources, Agriculture Production - Livestock, Dust kicked up by Livestock, All Animals",
    "2805100010":
        "Miscellaneous Area Sources, Agriculture Production - Livestock, Dust kicked up by Livestock, Beef cattle - finishing operations on feedlots (drylots)",
    "2805100020":
        "Miscellaneous Area Sources, Agriculture Production - Livestock, Dust kicked up by Livestock, Dairy Cattle",
    "2805100030":
        "Miscellaneous Area Sources, Agriculture Production - Livestock, Dust kicked up by Livestock, Broilers",
    "2805100040":
        "Miscellaneous Area Sources, Agriculture Production - Livestock, Dust kicked up by Livestock, Layers",
    "2805100050":
        "Miscellaneous Area Sources, Agriculture Production - Livestock, Dust kicked up by Livestock, Swine",
    "2805100060":
        "Miscellaneous Area Sources, Agriculture Production - Livestock, Dust kicked up by Livestock, Turkeys",
    "2806010000":
        "Miscellaneous Area Sources, Domestic Animals Waste Emissions, Cats, Total",
    "2806015000":
        "Miscellaneous Area Sources, Domestic Animals Waste Emissions, Dogs, Total",
    "2807020001":
        "Miscellaneous Area Sources, Wild Animals Waste Emissions, Bears, Black Bears",
    "2807020002":
        "Miscellaneous Area Sources, Wild Animals Waste Emissions, Bears, Grizzly Bears",
    "2807025000":
        "Miscellaneous Area Sources, Wild Animals Waste Emissions, Elk, Total",
    "2807030000":
        "Miscellaneous Area Sources, Wild Animals Waste Emissions, Deer, Total",
    "2807035000":
        "Miscellaneous Area Sources, Wild Animals Waste Emissions, Squirrels, Total",
    "2807040000":
        "Miscellaneous Area Sources, Wild Animals Waste Emissions, Birds, Total",
    "2807045000":
        "Miscellaneous Area Sources, Wild Animals Waste Emissions, Wolves, Total",
    "2810003000":
        "Miscellaneous Area Sources, Other Combustion, Cigarette Smoke, Total",
    "2810005000":
        "Miscellaneous Area Sources, Other Combustion, Managed Burning, Slash (Logging Debris), Unspecified Burn Method (use 2610000500 for non-logging debris)",
    "2810005001":
        "Miscellaneous Area Sources, Other Combustion, Managed Burning, Slash (Logging Debris), Pile Burning",
    "2810005002":
        "Miscellaneous Area Sources, Other Combustion, Managed Burning, Slash (Logging Debris), Broadcast Burning",
    "28100050F0":
        "Miscellaneous Area Sources, Other Combustion, Managed Burning, Slash (Logging Debris), Flaming",
    "2810010000":
        "Miscellaneous Area Sources, Other Combustion, Human Perspiration and Respiration, Total",
    "2810014000":
        "Miscellaneous Area Sources, Other Combustion, Prescribed Burning, Generic - Unspecified land cover, ownership, class/purpose",
    "2810015000":
        "Miscellaneous Area Sources, Other Combustion, Prescribed Forest Burning, Unspecified",
    "2810015001":
        "Miscellaneous Area Sources, Other Combustion, Prescribed Forest Burning, NATURAL",
    "2810015002":
        "Miscellaneous Area Sources, Other Combustion, Prescribed Forest Burning, ANTHROPOGENIC",
    "28100150F0":
        "Miscellaneous Area Sources, Other Combustion, Prescribed Forest Burning, Flaming",
    "28100150F1":
        "Miscellaneous Area Sources, Other Combustion, Prescribed Forest Burning, Flaming Natural",
    "2810020000":
        "Miscellaneous Area Sources, Other Combustion, Prescribed Rangeland Burning, Unspecified",
    "2810020001":
        "Miscellaneous Area Sources, Other Combustion, Prescribed Rangeland Burning, Non-Federal Rangeland NATURAL",
    "2810020002":
        "Miscellaneous Area Sources, Other Combustion, Prescribed Rangeland Burning, Non-Federal Rangeland ANTHROPOGENIC",
    "28100200F0":
        "Miscellaneous Area Sources, Other Combustion, Prescribed Rangeland Burning, Flaming",
    "2810025000":
        "Miscellaneous Area Sources, Other Combustion, Residential Grilling (see 23-02-002-xxx for Commercial), Total",
    "2810030000":
        "Miscellaneous Area Sources, Other Combustion, Structure Fires, Unspecified",
    "2810035000":
        "Miscellaneous Area Sources, Other Combustion, Firefighting Training, Total",
    "2810040000":
        "Miscellaneous Area Sources, Other Combustion, Aircraft/Rocket Engine Firing and Testing, Total",
    "2810050000":
        "Miscellaneous Area Sources, Other Combustion, Motor Vehicle Fires, Unspecified",
    "2810060000":
        "Miscellaneous Area Sources, Other Combustion, Cremation, Humans and animals",
    "2810060100":
        "Miscellaneous Area Sources, Other Combustion, Cremation, Humans",
    "2810060200":
        "Miscellaneous Area Sources, Other Combustion, Cremation, Animals",
    "2810090000":
        "Miscellaneous Area Sources, Other Combustion, Open Fire, Not categorized",
    "2820000000":
        "Miscellaneous Area Sources, Cooling Towers, All Types, Total",
    "2820010000":
        "Miscellaneous Area Sources, Cooling Towers, Process Cooling Towers, Total",
    "2820020000":
        "Miscellaneous Area Sources, Cooling Towers, Comfort Cooling Towers, Total",
    "2830000000":
        "Miscellaneous Area Sources, Catastrophic/Accidental Releases, All Catastrophic/Accidential Releases, Total",
    "2830001000":
        "Miscellaneous Area Sources, Catastrophic/Accidental Releases, Industrial Accidents, Total",
    "2830010000":
        "Miscellaneous Area Sources, Catastrophic/Accidental Releases, Transportation Accidents, Total",
    "2840000000":
        "Miscellaneous Area Sources, Automotive Repair Shops, Automotive Repair Shops, Total",
    "2840000010":
        "Miscellaneous Area Sources, Automotive Repair Shops, Automotive Repair Shops, Cutting Torch Operations",
    "2840000020":
        "Miscellaneous Area Sources, Automotive Repair Shops, Automotive Repair Shops, Welding Operations",
    "2840000030":
        "Miscellaneous Area Sources, Automotive Repair Shops, Automotive Repair Shops, Brazing Operations",
    "2840000040":
        "Miscellaneous Area Sources, Automotive Repair Shops, Automotive Repair Shops, Soldering Operations",
    "2840000050":
        "Miscellaneous Area Sources, Automotive Repair Shops, Automotive Repair Shops, Grinding Operations",
    "2840010000":
        "Miscellaneous Area Sources, Automotive Repair Shops, Auto Top and Body Repair, Total",
    "2840010010":
        "Miscellaneous Area Sources, Automotive Repair Shops, Auto Top and Body Repair, Cutting Torch Operations",
    "2840010020":
        "Miscellaneous Area Sources, Automotive Repair Shops, Auto Top and Body Repair, Welding Operations",
    "2840010030":
        "Miscellaneous Area Sources, Automotive Repair Shops, Auto Top and Body Repair, Brazing Operations",
    "2840010040":
        "Miscellaneous Area Sources, Automotive Repair Shops, Auto Top and Body Repair, Soldering Operations",
    "2840010050":
        "Miscellaneous Area Sources, Automotive Repair Shops, Auto Top and Body Repair, Grinding Operations",
    "2840020000":
        "Miscellaneous Area Sources, Automotive Repair Shops, Automotive Exhaust Repair Shops, Total",
    "2840020010":
        "Miscellaneous Area Sources, Automotive Repair Shops, Automotive Exhaust Repair Shops, Cutting Torch Operations",
    "2840020020":
        "Miscellaneous Area Sources, Automotive Repair Shops, Automotive Exhaust Repair Shops, Welding Operations",
    "2840020030":
        "Miscellaneous Area Sources, Automotive Repair Shops, Automotive Exhaust Repair Shops, Brazing Operations",
    "2840020040":
        "Miscellaneous Area Sources, Automotive Repair Shops, Automotive Exhaust Repair Shops, Soldering Operations",
    "2840020050":
        "Miscellaneous Area Sources, Automotive Repair Shops, Automotive Exhaust Repair Shops, Grinding Operations",
    "2840030000":
        "Miscellaneous Area Sources, Automotive Repair Shops, Tire Retreading and Repair Shops, Total",
    "2840030010":
        "Miscellaneous Area Sources, Automotive Repair Shops, Tire Retreading and Repair Shops, Buffing Operations",
    "2841000000":
        "Miscellaneous Area Sources, Miscellaneous Repair Shops, Miscellaneous Repair Shops, Total",
    "2841000010":
        "Miscellaneous Area Sources, Miscellaneous Repair Shops, Miscellaneous Repair Shops, Cutting Torch Operations",
    "2841000020":
        "Miscellaneous Area Sources, Miscellaneous Repair Shops, Miscellaneous Repair Shops, Welding Operations",
    "2841000030":
        "Miscellaneous Area Sources, Miscellaneous Repair Shops, Miscellaneous Repair Shops, Brazing Operations",
    "2841000040":
        "Miscellaneous Area Sources, Miscellaneous Repair Shops, Miscellaneous Repair Shops, Soldering Operations",
    "2841000050":
        "Miscellaneous Area Sources, Miscellaneous Repair Shops, Miscellaneous Repair Shops, Grinding Operations",
    "2841010000":
        "Miscellaneous Area Sources, Miscellaneous Repair Shops, Welding Repair Shops, Total",
    "2841010010":
        "Miscellaneous Area Sources, Miscellaneous Repair Shops, Welding Repair Shops, Cutting Torch Operations",
    "2841010020":
        "Miscellaneous Area Sources, Miscellaneous Repair Shops, Welding Repair Shops, Welding Operations",
    "2841010030":
        "Miscellaneous Area Sources, Miscellaneous Repair Shops, Welding Repair Shops, Brazing Operations",
    "2841010040":
        "Miscellaneous Area Sources, Miscellaneous Repair Shops, Welding Repair Shops, Soldering Operations",
    "2841010050":
        "Miscellaneous Area Sources, Miscellaneous Repair Shops, Welding Repair Shops, Grinding Operations",
    "2850000000":
        "Miscellaneous Area Sources, Health Services, Hospitals, Total: All Operations",
    "2850000010":
        "Miscellaneous Area Sources, Health Services, Hospitals, Sterilization Operations",
    "2850000030":
        "Miscellaneous Area Sources, Health Services, Hospitals, Pathological Incineration",
    "2850001000":
        "Miscellaneous Area Sources, Health Services, Dental Alloy Production, Overall Process",
    "2851001000":
        "Miscellaneous Area Sources, Laboratories, Bench Scale Reagents, Total",
    "2861000000":
        "Miscellaneous Area Sources, Fluorescent Lamp Breakage, Fluorescent Lamp Breakage, Non-recycling Related Emissions: Total",
    "2861000010":
        "Miscellaneous Area Sources, Fluorescent Lamp Breakage, Fluorescent Lamp Breakage, Recycling Related Emissions: Total",
    "2862000000":
        "Miscellaneous Area Sources, Swimming Pools, Total (Commercial, Residential, Public), Total",
    "2862001000":
        "Miscellaneous Area Sources, Swimming Pools, Public, Total",
    "2862002000":
        "Miscellaneous Area Sources, Swimming Pools, Residential, Total",
    "2201000062":
        "Mobile Sources, Highway Vehicles - Gasoline, Refueling, Total Spillage and Displacement",
    "2201001000":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Total: All Road Types",
    "2201001110":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Rural Interstate: Total",
    "2201001111":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Interstate: Rural Time 1",
    "2201001112":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Interstate: Rural Time 2",
    "2201001113":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Interstate: Rural Time 3",
    "2201001114":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Interstate: Rural Time 4",
    "220100111B":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Rural Interstate: Brake Wear",
    "220100111T":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Rural Interstate: Tire Wear",
    "220100111V":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Rural Interstate: Evap (except Refueling)",
    "220100111X":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Rural Interstate: Exhaust",
    "2201001130":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Rural Other Principal Arterial: Total",
    "2201001131":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Other Principal Arterial: Rural Time 1",
    "2201001132":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Other Principal Arterial: Rural Time 2",
    "2201001133":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Other Principal Arterial: Rural Time 3",
    "2201001134":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Other Principal Arterial: Rural Time 4",
    "220100113B":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Rural Other Principal Arterial: Brake Wear",
    "220100113T":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Rural Other Principal Arterial: Tire Wear",
    "220100113V":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Rural Other Principal Arterial: Evap (except Refueling)",
    "220100113X":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Rural Other Principal Arterial: Exhaust",
    "2201001150":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Rural Minor Arterial: Total",
    "2201001151":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Minor Arterial: Rural Time 1",
    "2201001152":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Minor Arterial: Rural Time 2",
    "2201001153":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Minor Arterial: Rural Time 3",
    "2201001154":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Minor Arterial: Rural Time 4",
    "220100115B":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Rural Minor Arterial: Brake Wear",
    "220100115T":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Rural Minor Arterial: Tire Wear",
    "220100115V":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Rural Minor Arterial: Evap (except Refueling)",
    "220100115X":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Rural Minor Arterial: Exhaust",
    "2201001170":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Rural Major Collector: Total",
    "2201001171":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Major Collector: Rural Time 1",
    "2201001172":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Major Collector: Rural Time 2",
    "2201001173":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Major Collector: Rural Time 3",
    "2201001174":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Major Collector: Rural Time 4",
    "220100117B":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Rural Major Collector: Brake Wear",
    "220100117T":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Rural Major Collector: Tire Wear",
    "220100117V":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Rural Major Collector: Evap (except Refueling)",
    "220100117X":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Rural Major Collector: Exhaust",
    "2201001190":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Rural Minor Collector: Total",
    "2201001191":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Minor Collector: Rural Time 1",
    "2201001192":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Minor Collector: Rural Time 2",
    "2201001193":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Minor Collector: Rural Time 3",
    "2201001194":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Minor Collector: Rural Time 4",
    "220100119B":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Rural Minor Collector: Brake Wear",
    "220100119T":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Rural Minor Collector: Tire Wear",
    "220100119V":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Rural Minor Collector: Evap (except Refueling)",
    "220100119X":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Rural Minor Collector: Exhaust",
    "2201001210":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Rural Local: Total",
    "2201001211":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Local: Rural Time 1",
    "2201001212":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Local: Rural Time 2",
    "2201001213":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Local: Rural Time 3",
    "2201001214":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Local: Rural Time 4",
    "220100121B":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Rural Local: Brake Wear",
    "220100121T":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Rural Local: Tire Wear",
    "220100121V":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Rural Local: Evap (except Refueling)",
    "220100121X":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Rural Local: Exhaust",
    "2201001230":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Urban Interstate: Total",
    "2201001231":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Interstate: Urban Time 1",
    "2201001232":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Interstate: Urban Time 2",
    "2201001233":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Interstate: Urban Time 3",
    "2201001234":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Interstate: Urban Time 4",
    "220100123B":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Urban Interstate: Brake Wear",
    "220100123T":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Urban Interstate: Tire Wear",
    "220100123V":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Urban Interstate: Evap (except Refueling)",
    "220100123X":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Urban Interstate: Exhaust",
    "2201001250":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Urban Other Freeways and Expressways: Total",
    "2201001251":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Other Freeways and Expressways: Urban Time 1",
    "2201001252":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Other Freeways and Expressways: Urban Time 2",
    "2201001253":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Other Freeways and Expressways: Urban Time 3",
    "2201001254":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Other Freeways and Expressways: Urban Time 4",
    "220100125B":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Urban Other Freeways and Expressways: Brake Wear",
    "220100125T":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Urban Other Freeways and Expressways: Tire Wear",
    "220100125V":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Urban Other Freeways and Expressways: Evap (except Refueling)",
    "220100125X":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Urban Other Freeways and Expressways: Exhaust",
    "2201001270":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Urban Other Principal Arterial: Total",
    "2201001271":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Other Principal Arterial: Urban Time 1",
    "2201001272":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Other Principal Arterial: Urban Time 2",
    "2201001273":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Other Principal Arterial: Urban Time 3",
    "2201001274":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Other Principal Arterial: Urban Time 4",
    "220100127B":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Urban Other Principal Arterial: Brake Wear",
    "220100127T":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Urban Other Principal Arterial: Tire Wear",
    "220100127V":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Urban Other Principal Arterial: Evap (except Refueling)",
    "220100127X":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Urban Other Principal Arterial: Exhaust",
    "2201001290":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Urban Minor Arterial: Total",
    "2201001291":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Minor Arterial: Urban Time 1",
    "2201001292":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Minor Arterial: Urban Time 2",
    "2201001293":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Minor Arterial: Urban Time 3",
    "2201001294":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Minor Arterial: Urban Time 4",
    "220100129B":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Urban Minor Arterial: Brake Wear",
    "220100129T":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Urban Minor Arterial: Tire Wear",
    "220100129V":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Urban Minor Arterial: Evap (except Refueling)",
    "220100129X":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Urban Minor Arterial: Exhaust",
    "2201001310":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Urban Collector: Total",
    "2201001311":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Collector: Urban Time 1",
    "2201001312":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Collector: Urban Time 2",
    "2201001313":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Collector: Urban Time 3",
    "2201001314":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Collector: Urban Time 4",
    "220100131B":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Urban Collector: Brake Wear",
    "220100131T":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Urban Collector: Tire Wear",
    "220100131V":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Urban Collector: Evap (except Refueling)",
    "220100131X":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Urban Collector: Exhaust",
    "2201001330":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Urban Local: Total",
    "2201001331":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Local: Urban Time 1",
    "2201001332":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Local: Urban Time 2",
    "2201001333":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Local: Urban Time 3",
    "2201001334":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Local: Urban Time 4",
    "220100133B":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Urban Local: Brake Wear",
    "220100133T":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Urban Local: Tire Wear",
    "220100133V":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Urban Local: Evap (except Refueling)",
    "220100133X":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Urban Local: Exhaust",
    "2201001350":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Parking Area: Rural",
    "2201001370":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Parking Area: Urban",
    "2201001390":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Vehicles (LDGV), Parking Area: Total",
    "2201020000":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Total: All Road Types",
    "2201020110":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Rural Interstate: Total",
    "2201020111":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Interstate: Rural Time 1",
    "2201020112":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Interstate: Rural Time 2",
    "2201020113":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Interstate: Rural Time 3",
    "2201020114":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Interstate: Rural Time 4",
    "220102011B":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Rural Interstate: Brake Wear",
    "220102011T":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Rural Interstate: Tire Wear",
    "220102011V":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Rural Interstate: Evap (except Refueling)",
    "220102011X":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Rural Interstate: Exhaust",
    "2201020130":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Rural Other Principal Arterial: Total",
    "2201020131":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Other Principal Arterial: Rural Time 1",
    "2201020132":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Other Principal Arterial: Rural Time 2",
    "2201020133":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Other Principal Arterial: Rural Time 3",
    "2201020134":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Other Principal Arterial: Rural Time 4",
    "220102013B":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Rural Other Principal Arterial: Brake Wear",
    "220102013T":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Rural Other Principal Arterial: Tire Wear",
    "220102013V":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Rural Other Principal Arterial: Evap (except Refueling)",
    "220102013X":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Rural Other Principal Arterial: Exhaust",
    "2201020150":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Rural Minor Arterial: Total",
    "2201020151":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Minor Arterial: Rural Time 1",
    "2201020152":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Minor Arterial: Rural Time 2",
    "2201020153":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Minor Arterial: Rural Time 3",
    "2201020154":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Minor Arterial: Rural Time 4",
    "220102015B":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Rural Minor Arterial: Brake Wear",
    "220102015T":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Rural Minor Arterial: Tire Wear",
    "220102015V":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Rural Minor Arterial: Evap (except Refueling)",
    "220102015X":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Rural Minor Arterial: Exhaust",
    "2201020170":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Rural Major Collector: Total",
    "2201020171":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Major Collector: Rural Time 1",
    "2201020172":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Major Collector: Rural Time 2",
    "2201020173":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Major Collector: Rural Time 3",
    "2201020174":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Major Collector: Rural Time 4",
    "220102017B":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Rural Major Collector: Brake Wear",
    "220102017T":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Rural Major Collector: Tire Wear",
    "220102017V":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Rural Major Collector: Evap (except Refueling)",
    "220102017X":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Rural Major Collector: Exhaust",
    "2201020190":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Rural Minor Collector: Total",
    "2201020191":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Minor Collector: Rural Time 1",
    "2201020192":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Minor Collector: Rural Time 2",
    "2201020193":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Minor Collector: Rural Time 3",
    "2201020194":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Minor Collector: Rural Time 4",
    "220102019B":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Rural Minor Collector: Brake Wear",
    "220102019T":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Rural Minor Collector: Tire Wear",
    "220102019V":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Rural Minor Collector: Evap (except Refueling)",
    "220102019X":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Rural Minor Collector: Exhaust",
    "2201020210":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Rural Local: Total",
    "2201020211":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Local: Rural Time 1",
    "2201020212":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Local: Rural Time 2",
    "2201020213":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Local: Rural Time 3",
    "2201020214":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Local: Rural Time 4",
    "220102021B":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Rural Local: Brake Wear",
    "220102021T":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Rural Local: Tire Wear",
    "220102021V":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Rural Local: Evap (except Refueling)",
    "220102021X":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Rural Local: Exhaust",
    "2201020230":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Urban Interstate: Total",
    "2201020231":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Interstate: Urban Time 1",
    "2201020232":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Interstate: Urban Time 2",
    "2201020233":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Interstate: Urban Time 3",
    "2201020234":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Interstate: Urban Time 4",
    "220102023B":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Urban Interstate: Brake Wear",
    "220102023T":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Urban Interstate: Tire Wear",
    "220102023V":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Urban Interstate: Evap (except Refueling)",
    "220102023X":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Urban Interstate: Exhaust",
    "2201020250":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Urban Other Freeways and Expressways: Total",
    "2201020251":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Other Freeways and Expressways: Urban Time 1",
    "2201020252":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Other Freeways and Expressways: Urban Time 2",
    "2201020253":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Other Freeways and Expressways: Urban Time 3",
    "2201020254":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Other Freeways and Expressways: Urban Time 4",
    "220102025B":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Urban Other Freeways and Expressways: Brake Wear",
    "220102025T":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Urban Other Freeways and Expressways: Tire Wear",
    "220102025V":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Urban Other Freeways and Expressways: Evap (except Refueling)",
    "220102025X":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Urban Other Freeways and Expressways: Exhaust",
    "2201020270":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Urban Other Principal Arterial: Total",
    "2201020271":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Other Principal Arterial: Urban Time 1",
    "2201020272":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Other Principal Arterial: Urban Time 2",
    "2201020273":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Other Principal Arterial: Urban Time 3",
    "2201020274":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Other Principal Arterial: Urban Time 4",
    "220102027B":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Urban Other Principal Arterial: Brake Wear",
    "220102027T":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Urban Other Principal Arterial: Tire Wear",
    "220102027V":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Urban Other Principal Arterial: Evap (except Refueling)",
    "220102027X":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Urban Other Principal Arterial: Exhaust",
    "2201020290":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Urban Minor Arterial: Total",
    "2201020291":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Minor Arterial: Urban Time 1",
    "2201020292":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Minor Arterial: Urban Time 2",
    "2201020293":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Minor Arterial: Urban Time 3",
    "2201020294":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Minor Arterial: Urban Time 4",
    "220102029B":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Urban Minor Arterial: Brake Wear",
    "220102029T":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Urban Minor Arterial: Tire Wear",
    "220102029V":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Urban Minor Arterial: Evap (except Refueling)",
    "220102029X":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Urban Minor Arterial: Exhaust",
    "2201020310":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Urban Collector: Total",
    "2201020311":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Collector: Urban Time 1",
    "2201020312":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Collector: Urban Time 2",
    "2201020313":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Collector: Urban Time 3",
    "2201020314":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Collector: Urban Time 4",
    "220102031B":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Urban Collector: Brake Wear",
    "220102031T":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Urban Collector: Tire Wear",
    "220102031V":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Urban Collector: Evap (except Refueling)",
    "220102031X":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Urban Collector: Exhaust",
    "2201020330":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Urban Local: Total",
    "2201020331":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Local: Urban Time 1",
    "2201020332":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Local: Urban Time 2",
    "2201020333":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Local: Urban Time 3",
    "2201020334":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Local: Urban Time 4",
    "220102033B":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Urban Local: Brake Wear",
    "220102033T":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Urban Local: Tire Wear",
    "220102033V":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Urban Local: Evap (except Refueling)",
    "220102033X":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Urban Local: Exhaust",
    "2201020350":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Parking Area: Rural",
    "2201020370":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Parking Area: Urban",
    "2201020390":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 1 & 2 (M6) = LDGT1 (M5), Parking Area: Total",
    "2201040000":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Total: All Road Types",
    "2201040110":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Rural Interstate: Total",
    "2201040111":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Interstate: Rural Time 1",
    "2201040112":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Interstate: Rural Time 2",
    "2201040113":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Interstate: Rural Time 3",
    "2201040114":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Interstate: Rural Time 4",
    "220104011B":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Rural Interstate: Brake Wear",
    "220104011T":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Rural Interstate: Tire Wear",
    "220104011V":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Rural Interstate: Evap (except Refueling)",
    "220104011X":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Rural Interstate: Exhaust",
    "2201040130":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Rural Other Principal Arterial: Total",
    "2201040131":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Other Principal Arterial: Rural Time 1",
    "2201040132":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Other Principal Arterial: Rural Time 2",
    "2201040133":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Other Principal Arterial: Rural Time 3",
    "2201040134":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Other Principal Arterial: Rural Time 4",
    "220104013B":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Rural Other Principal Arterial: Brake Wear",
    "220104013T":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Rural Other Principal Arterial: Tire Wear",
    "220104013V":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Rural Other Principal Arterial: Evap (except Refueling)",
    "220104013X":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Rural Other Principal Arterial: Exhaust",
    "2201040150":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Rural Minor Arterial: Total",
    "2201040151":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Minor Arterial: Rural Time 1",
    "2201040152":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Minor Arterial: Rural Time 2",
    "2201040153":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Minor Arterial: Rural Time 3",
    "2201040154":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Minor Arterial: Rural Time 4",
    "220104015B":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Rural Minor Arterial: Brake Wear",
    "220104015T":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Rural Minor Arterial: Tire Wear",
    "220104015V":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Rural Minor Arterial: Evap (except Refueling)",
    "220104015X":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Rural Minor Arterial: Exhaust",
    "2201040170":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Rural Major Collector: Total",
    "2201040171":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Major Collector: Rural Time 1",
    "2201040172":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Major Collector: Rural Time 2",
    "2201040173":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Major Collector: Rural Time 3",
    "2201040174":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Major Collector: Rural Time 4",
    "220104017B":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Rural Major Collector: Brake Wear",
    "220104017T":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Rural Major Collector: Tire Wear",
    "220104017V":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Rural Major Collector: Evap (except Refueling)",
    "220104017X":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Rural Major Collector: Exhaust",
    "2201040190":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Rural Minor Collector: Total",
    "2201040191":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Minor Collector: Rural Time 1",
    "2201040192":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Minor Collector: Rural Time 2",
    "2201040193":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Minor Collector: Rural Time 3",
    "2201040194":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Minor Collector: Rural Time 4",
    "220104019B":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Rural Minor Collector: Brake Wear",
    "220104019T":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Rural Minor Collector: Tire Wear",
    "220104019V":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Rural Minor Collector: Evap (except Refueling)",
    "220104019X":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Rural Minor Collector: Exhaust",
    "2201040210":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Rural Local: Total",
    "2201040211":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Local: Rural Time 1",
    "2201040212":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Local: Rural Time 2",
    "2201040213":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Local: Rural Time 3",
    "2201040214":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Local: Rural Time 4",
    "220104021B":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Rural Local: Brake Wear",
    "220104021T":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Rural Local: Tire Wear",
    "220104021V":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Rural Local: Evap (except Refueling)",
    "220104021X":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Rural Local: Exhaust",
    "2201040230":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Urban Interstate: Total",
    "2201040231":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Interstate: Urban Time 1",
    "2201040232":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Interstate: Urban Time 2",
    "2201040233":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Interstate: Urban Time 3",
    "2201040234":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Interstate: Urban Time 4",
    "220104023B":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Urban Interstate: Brake Wear",
    "220104023T":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Urban Interstate: Tire Wear",
    "220104023V":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Urban Interstate: Evap (except Refueling)",
    "220104023X":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Urban Interstate: Exhaust",
    "2201040250":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Urban Other Freeways and Expressways: Total",
    "2201040251":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Other Freeways and Expressways: Urban Time 1",
    "2201040252":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Other Freeways and Expressways: Urban Time 2",
    "2201040253":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Other Freeways and Expressways: Urban Time 3",
    "2201040254":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Other Freeways and Expressways: Urban Time 4",
    "220104025B":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Urban Other Freeways and Expressways: Brake Wear",
    "220104025T":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Urban Other Freeways and Expressways: Tire Wear",
    "220104025V":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Urban Other Freeways and Expressways: Evap (except Refueling)",
    "220104025X":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Urban Other Freeways and Expressways: Exhaust",
    "2201040270":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Urban Other Principal Arterial: Total",
    "2201040271":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Other Principal Arterial: Urban Time 1",
    "2201040272":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Other Principal Arterial: Urban Time 2",
    "2201040273":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Other Principal Arterial: Urban Time 3",
    "2201040274":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Other Principal Arterial: Urban Time 4",
    "220104027B":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Urban Other Principal Arterial: Brake Wear",
    "220104027T":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Urban Other Principal Arterial: Tire Wear",
    "220104027V":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Urban Other Principal Arterial: Evap (except Refueling)",
    "220104027X":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Urban Other Principal Arterial: Exhaust",
    "2201040290":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Urban Minor Arterial: Total",
    "2201040291":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Minor Arterial: Urban Time 1",
    "2201040292":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Minor Arterial: Urban Time 2",
    "2201040293":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Minor Arterial: Urban Time 3",
    "2201040294":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Minor Arterial: Urban Time 4",
    "220104029B":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Urban Minor Arterial: Brake Wear",
    "220104029T":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Urban Minor Arterial: Tire Wear",
    "220104029V":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Urban Minor Arterial: Evap (except Refueling)",
    "220104029X":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Urban Minor Arterial: Exhaust",
    "2201040310":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Urban Collector: Total",
    "2201040311":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Collector: Urban Time 1",
    "2201040312":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Collector: Urban Time 2",
    "2201040313":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Collector: Urban Time 3",
    "2201040314":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Collector: Urban Time 4",
    "220104031B":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Urban Collector: Brake Wear",
    "220104031T":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Urban Collector: Tire Wear",
    "220104031V":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Urban Collector: Evap (except Refueling)",
    "220104031X":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Urban Collector: Exhaust",
    "2201040330":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Urban Local: Total",
    "2201040331":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Local: Urban Time 1",
    "2201040332":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Local: Urban Time 2",
    "2201040333":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Local: Urban Time 3",
    "2201040334":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Local: Urban Time 4",
    "220104033B":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Urban Local: Brake Wear",
    "220104033T":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Urban Local: Tire Wear",
    "220104033V":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Urban Local: Evap (except Refueling)",
    "220104033X":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Urban Local: Exhaust",
    "2201040350":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Parking Area: Rural",
    "2201040370":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Parking Area: Urban",
    "2201040390":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Duty Gasoline Trucks 3 & 4 (M6) = LDGT2 (M5), Parking Area: Total",
    "2201060000":
        "Mobile Sources, Highway Vehicles - Gasoline, NOT USED - Previously all LDGT (1&2) under M5, Total: All Road Types",
    "2201060110":
        "Mobile Sources, Highway Vehicles - Gasoline, NOT USED - Previously all LDGT (1&2) under M5, Rural Interstate: Total",
    "2201060111":
        "Mobile Sources, Highway Vehicles - Gasoline, NOT USED - Previously all LDGT (1&2) under M5, Interstate: Rural Time 1",
    "2201060112":
        "Mobile Sources, Highway Vehicles - Gasoline, NOT USED - Previously all LDGT (1&2) under M5, Interstate: Rural Time 2",
    "2201060113":
        "Mobile Sources, Highway Vehicles - Gasoline, NOT USED - Previously all LDGT (1&2) under M5, Interstate: Rural Time 3",
    "2201060114":
        "Mobile Sources, Highway Vehicles - Gasoline, NOT USED - Previously all LDGT (1&2) under M5, Interstate: Rural Time 4",
    "2201060130":
        "Mobile Sources, Highway Vehicles - Gasoline, NOT USED - Previously all LDGT (1&2) under M5, Rural Other Principal Arterial: Total",
    "2201060131":
        "Mobile Sources, Highway Vehicles - Gasoline, NOT USED - Previously all LDGT (1&2) under M5, Other Principal Arterial: Rural Time 1",
    "2201060132":
        "Mobile Sources, Highway Vehicles - Gasoline, NOT USED - Previously all LDGT (1&2) under M5, Other Principal Arterial: Rural Time 2",
    "2201060133":
        "Mobile Sources, Highway Vehicles - Gasoline, NOT USED - Previously all LDGT (1&2) under M5, Other Principal Arterial: Rural Time 3",
    "2201060134":
        "Mobile Sources, Highway Vehicles - Gasoline, NOT USED - Previously all LDGT (1&2) under M5, Other Principal Arterial: Rural Time 4",
    "2201060150":
        "Mobile Sources, Highway Vehicles - Gasoline, NOT USED - Previously all LDGT (1&2) under M5, Rural Minor Arterial: Total",
    "2201060151":
        "Mobile Sources, Highway Vehicles - Gasoline, NOT USED - Previously all LDGT (1&2) under M5, Minor Arterial: Rural Time 1",
    "2201060152":
        "Mobile Sources, Highway Vehicles - Gasoline, NOT USED - Previously all LDGT (1&2) under M5, Minor Arterial: Rural Time 2",
    "2201060153":
        "Mobile Sources, Highway Vehicles - Gasoline, NOT USED - Previously all LDGT (1&2) under M5, Minor Arterial: Rural Time 3",
    "2201060154":
        "Mobile Sources, Highway Vehicles - Gasoline, NOT USED - Previously all LDGT (1&2) under M5, Minor Arterial: Rural Time 4",
    "2201060170":
        "Mobile Sources, Highway Vehicles - Gasoline, NOT USED - Previously all LDGT (1&2) under M5, Rural Major Collector: Total",
    "2201060171":
        "Mobile Sources, Highway Vehicles - Gasoline, NOT USED - Previously all LDGT (1&2) under M5, Major Collector: Rural Time 1",
    "2201060172":
        "Mobile Sources, Highway Vehicles - Gasoline, NOT USED - Previously all LDGT (1&2) under M5, Major Collector: Rural Time 2",
    "2201060173":
        "Mobile Sources, Highway Vehicles - Gasoline, NOT USED - Previously all LDGT (1&2) under M5, Major Collector: Rural Time 3",
    "2201060174":
        "Mobile Sources, Highway Vehicles - Gasoline, NOT USED - Previously all LDGT (1&2) under M5, Major Collector: Rural Time 4",
    "2201060190":
        "Mobile Sources, Highway Vehicles - Gasoline, NOT USED - Previously all LDGT (1&2) under M5, Rural Minor Collector: Total",
    "2201060191":
        "Mobile Sources, Highway Vehicles - Gasoline, NOT USED - Previously all LDGT (1&2) under M5, Minor Collector: Rural Time 1",
    "2201060192":
        "Mobile Sources, Highway Vehicles - Gasoline, NOT USED - Previously all LDGT (1&2) under M5, Minor Collector: Rural Time 2",
    "2201060193":
        "Mobile Sources, Highway Vehicles - Gasoline, NOT USED - Previously all LDGT (1&2) under M5, Minor Collector: Rural Time 3",
    "2201060194":
        "Mobile Sources, Highway Vehicles - Gasoline, NOT USED - Previously all LDGT (1&2) under M5, Minor Collector: Rural Time 4",
    "2201060210":
        "Mobile Sources, Highway Vehicles - Gasoline, NOT USED - Previously all LDGT (1&2) under M5, Rural Local: Total",
    "2201060211":
        "Mobile Sources, Highway Vehicles - Gasoline, NOT USED - Previously all LDGT (1&2) under M5, Local: Rural Time 1",
    "2201060212":
        "Mobile Sources, Highway Vehicles - Gasoline, NOT USED - Previously all LDGT (1&2) under M5, Local: Rural Time 2",
    "2201060213":
        "Mobile Sources, Highway Vehicles - Gasoline, NOT USED - Previously all LDGT (1&2) under M5, Local: Rural Time 3",
    "2201060214":
        "Mobile Sources, Highway Vehicles - Gasoline, NOT USED - Previously all LDGT (1&2) under M5, Local: Rural Time 4",
    "2201060230":
        "Mobile Sources, Highway Vehicles - Gasoline, NOT USED - Previously all LDGT (1&2) under M5, Urban Interstate: Total",
    "2201060231":
        "Mobile Sources, Highway Vehicles - Gasoline, NOT USED - Previously all LDGT (1&2) under M5, Interstate: Urban Time 1",
    "2201060232":
        "Mobile Sources, Highway Vehicles - Gasoline, NOT USED - Previously all LDGT (1&2) under M5, Interstate: Urban Time 2",
    "2201060233":
        "Mobile Sources, Highway Vehicles - Gasoline, NOT USED - Previously all LDGT (1&2) under M5, Interstate: Urban Time 3",
    "2201060234":
        "Mobile Sources, Highway Vehicles - Gasoline, NOT USED - Previously all LDGT (1&2) under M5, Interstate: Urban Time 4",
    "2201060250":
        "Mobile Sources, Highway Vehicles - Gasoline, NOT USED - Previously all LDGT (1&2) under M5, Urban Other Freeways and Expressways: Total",
    "2201060251":
        "Mobile Sources, Highway Vehicles - Gasoline, NOT USED - Previously all LDGT (1&2) under M5, Other Freeways and Expressways: Urban Time 1",
    "2201060252":
        "Mobile Sources, Highway Vehicles - Gasoline, NOT USED - Previously all LDGT (1&2) under M5, Other Freeways and Expressways: Urban Time 2",
    "2201060253":
        "Mobile Sources, Highway Vehicles - Gasoline, NOT USED - Previously all LDGT (1&2) under M5, Other Freeways and Expressways: Urban Time 3",
    "2201060254":
        "Mobile Sources, Highway Vehicles - Gasoline, NOT USED - Previously all LDGT (1&2) under M5, Other Freeways and Expressways: Urban Time 4",
    "2201060270":
        "Mobile Sources, Highway Vehicles - Gasoline, NOT USED - Previously all LDGT (1&2) under M5, Urban Other Principal Arterial: Total",
    "2201060271":
        "Mobile Sources, Highway Vehicles - Gasoline, NOT USED - Previously all LDGT (1&2) under M5, Other Principal Arterial: Urban Time 1",
    "2201060272":
        "Mobile Sources, Highway Vehicles - Gasoline, NOT USED - Previously all LDGT (1&2) under M5, Other Principal Arterial: Urban Time 2",
    "2201060273":
        "Mobile Sources, Highway Vehicles - Gasoline, NOT USED - Previously all LDGT (1&2) under M5, Other Principal Arterial: Urban Time 3",
    "2201060274":
        "Mobile Sources, Highway Vehicles - Gasoline, NOT USED - Previously all LDGT (1&2) under M5, Other Principal Arterial: Urban Time 4",
    "2201060290":
        "Mobile Sources, Highway Vehicles - Gasoline, NOT USED - Previously all LDGT (1&2) under M5, Urban Minor Arterial: Total",
    "2201060291":
        "Mobile Sources, Highway Vehicles - Gasoline, NOT USED - Previously all LDGT (1&2) under M5, Minor Arterial: Urban Time 1",
    "2201060292":
        "Mobile Sources, Highway Vehicles - Gasoline, NOT USED - Previously all LDGT (1&2) under M5, Minor Arterial: Urban Time 2",
    "2201060293":
        "Mobile Sources, Highway Vehicles - Gasoline, NOT USED - Previously all LDGT (1&2) under M5, Minor Arterial: Urban Time 3",
    "2201060294":
        "Mobile Sources, Highway Vehicles - Gasoline, NOT USED - Previously all LDGT (1&2) under M5, Minor Arterial: Urban Time 4",
    "2201060310":
        "Mobile Sources, Highway Vehicles - Gasoline, NOT USED - Previously all LDGT (1&2) under M5, Urban Collector: Total",
    "2201060311":
        "Mobile Sources, Highway Vehicles - Gasoline, NOT USED - Previously all LDGT (1&2) under M5, Collector: Urban Time 1",
    "2201060312":
        "Mobile Sources, Highway Vehicles - Gasoline, NOT USED - Previously all LDGT (1&2) under M5, Collector: Urban Time 2",
    "2201060313":
        "Mobile Sources, Highway Vehicles - Gasoline, NOT USED - Previously all LDGT (1&2) under M5, Collector: Urban Time 3",
    "2201060314":
        "Mobile Sources, Highway Vehicles - Gasoline, NOT USED - Previously all LDGT (1&2) under M5, Collector: Urban Time 4",
    "2201060330":
        "Mobile Sources, Highway Vehicles - Gasoline, NOT USED - Previously all LDGT (1&2) under M5, Urban Local: Total",
    "2201060331":
        "Mobile Sources, Highway Vehicles - Gasoline, NOT USED - Previously all LDGT (1&2) under M5, Local: Urban Time 1",
    "2201060332":
        "Mobile Sources, Highway Vehicles - Gasoline, NOT USED - Previously all LDGT (1&2) under M5, Local: Urban Time 2",
    "2201060333":
        "Mobile Sources, Highway Vehicles - Gasoline, NOT USED - Previously all LDGT (1&2) under M5, Local: Urban Time 3",
    "2201060334":
        "Mobile Sources, Highway Vehicles - Gasoline, NOT USED - Previously all LDGT (1&2) under M5, Local: Urban Time 4",
    "2201070000":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Total: All Road Types",
    "2201070110":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Rural Interstate: Total",
    "2201070111":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Interstate: Rural Time 1",
    "2201070112":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Interstate: Rural Time 2",
    "2201070113":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Interstate: Rural Time 3",
    "2201070114":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Interstate: Rural Time 4",
    "220107011B":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Rural Interstate: Brake Wear",
    "220107011T":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Rural Interstate: Tire Wear",
    "220107011V":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Rural Interstate: Evap (except Refueling)",
    "220107011X":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Rural Interstate: Exhaust",
    "2201070130":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Rural Other Principal Arterial: Total",
    "2201070131":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Other Principal Arterial: Rural Time 1",
    "2201070132":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Other Principal Arterial: Rural Time 2",
    "2201070133":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Other Principal Arterial: Rural Time 3",
    "2201070134":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Other Principal Arterial: Rural Time 4",
    "220107013B":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Rural Other Principal Arterial: Brake Wear",
    "220107013T":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Rural Other Principal Arterial: Tire Wear",
    "220107013V":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Rural Other Principal Arterial: Evap (except Refueling)",
    "220107013X":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Rural Other Principal Arterial: Exhaust",
    "2201070150":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Rural Minor Arterial: Total",
    "2201070151":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Minor Arterial: Rural Time 1",
    "2201070152":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Minor Arterial: Rural Time 2",
    "2201070153":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Minor Arterial: Rural Time 3",
    "2201070154":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Minor Arterial: Rural Time 4",
    "220107015B":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Rural Minor Arterial: Brake Wear",
    "220107015T":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Rural Minor Arterial: Tire Wear",
    "220107015V":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Rural Minor Arterial: Evap (except Refueling)",
    "220107015X":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Rural Minor Arterial: Exhaust",
    "2201070170":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Rural Major Collector: Total",
    "2201070171":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Major Collector: Rural Time 1",
    "2201070172":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Major Collector: Rural Time 2",
    "2201070173":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Major Collector: Rural Time 3",
    "2201070174":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Major Collector: Rural Time 4",
    "220107017B":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Rural Major Collector: Brake Wear",
    "220107017T":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Rural Major Collector: Tire Wear",
    "220107017V":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Rural Major Collector: Evap (except Refueling)",
    "220107017X":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Rural Major Collector: Exhaust",
    "2201070190":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Rural Minor Collector: Total",
    "2201070191":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Minor Collector: Rural Time 1",
    "2201070192":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Minor Collector: Rural Time 2",
    "2201070193":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Minor Collector: Rural Time 3",
    "2201070194":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Minor Collector: Rural Time 4",
    "220107019B":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Rural Minor Collector: Brake Wear",
    "220107019T":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Rural Minor Collector: Tire Wear",
    "220107019V":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Rural Minor Collector: Evap (except Refueling)",
    "220107019X":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Rural Minor Collector: Exhaust",
    "2201070210":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Rural Local: Total",
    "2201070211":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Local: Rural Time 1",
    "2201070212":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Local: Rural Time 2",
    "2201070213":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Local: Rural Time 3",
    "2201070214":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Local: Rural Time 4",
    "220107021B":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Rural Local: Brake Wear",
    "220107021T":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Rural Local: Tire Wear",
    "220107021V":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Rural Local: Evap (except Refueling)",
    "220107021X":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Rural Local: Exhaust",
    "2201070230":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Urban Interstate: Total",
    "2201070231":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Interstate: Urban Time 1",
    "2201070232":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Interstate: Urban Time 2",
    "2201070233":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Interstate: Urban Time 3",
    "2201070234":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Interstate: Urban Time 4",
    "220107023B":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Urban Interstate: Brake Wear",
    "220107023T":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Urban Interstate: Tire Wear",
    "220107023V":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Urban Interstate: Evap (except Refueling)",
    "220107023X":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Urban Interstate: Exhaust",
    "2201070250":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Urban Other Freeways and Expressways: Total",
    "2201070251":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Other Freeways and Expressways: Urban Time 1",
    "2201070252":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Other Freeways and Expressways: Urban Time 2",
    "2201070253":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Other Freeways and Expressways: Urban Time 3",
    "2201070254":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Other Freeways and Expressways: Urban Time 4",
    "220107025B":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Urban Other Freeways and Expressways: Brake Wear",
    "220107025T":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Urban Other Freeways and Expressways: Tire Wear",
    "220107025V":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Urban Other Freeways and Expressways: Evap (except Refueling)",
    "220107025X":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Urban Other Freeways and Expressways: Exhaust",
    "2201070270":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Urban Other Principal Arterial: Total",
    "2201070271":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Other Principal Arterial: Urban Time 1",
    "2201070272":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Other Principal Arterial: Urban Time 2",
    "2201070273":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Other Principal Arterial: Urban Time 3",
    "2201070274":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Other Principal Arterial: Urban Time 4",
    "220107027B":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Urban Other Principal Arterial: Brake Wear",
    "220107027T":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Urban Other Principal Arterial: Tire Wear",
    "220107027V":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Urban Other Principal Arterial: Evap (except Refueling)",
    "220107027X":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Urban Other Principal Arterial: Exhaust",
    "2201070290":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Urban Minor Arterial: Total",
    "2201070291":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Minor Arterial: Urban Time 1",
    "2201070292":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Minor Arterial: Urban Time 2",
    "2201070293":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Minor Arterial: Urban Time 3",
    "2201070294":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Minor Arterial: Urban Time 4",
    "220107029B":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Urban Minor Arterial: Brake Wear",
    "220107029T":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Urban Minor Arterial: Tire Wear",
    "220107029V":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Urban Minor Arterial: Evap (except Refueling)",
    "220107029X":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Urban Minor Arterial: Exhaust",
    "2201070310":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Urban Collector: Total",
    "2201070311":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Collector: Urban Time 1",
    "2201070312":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Collector: Urban Time 2",
    "2201070313":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Collector: Urban Time 3",
    "2201070314":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Collector: Urban Time 4",
    "220107031B":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Urban Collector: Brake Wear",
    "220107031T":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Urban Collector: Tire Wear",
    "220107031V":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Urban Collector: Evap (except Refueling)",
    "220107031X":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Urban Collector: Exhaust",
    "2201070330":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Urban Local: Total",
    "2201070331":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Local: Urban Time 1",
    "2201070332":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Local: Urban Time 2",
    "2201070333":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Local: Urban Time 3",
    "2201070334":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Local: Urban Time 4",
    "220107033B":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Urban Local: Brake Wear",
    "220107033T":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Urban Local: Tire Wear",
    "220107033V":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Urban Local: Evap (except Refueling)",
    "220107033X":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Urban Local: Exhaust",
    "2201070350":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Parking Area: Rural",
    "2201070370":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Parking Area: Urban",
    "2201070390":
        "Mobile Sources, Highway Vehicles - Gasoline, Heavy Duty Gasoline Vehicles 2B thru 8B & Buses (HDGV), Parking Area: Total",
    "2201080000":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Total: All Road Types",
    "2201080110":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Rural Interstate: Total",
    "2201080111":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Interstate: Rural Time 1",
    "2201080112":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Interstate: Rural Time 2",
    "2201080113":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Interstate: Rural Time 3",
    "2201080114":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Interstate: Rural Time 4",
    "220108011B":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Rural Interstate: Brake Wear",
    "220108011T":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Rural Interstate: Tire Wear",
    "220108011V":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Rural Interstate: Evap (except Refueling)",
    "220108011X":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Rural Interstate: Exhaust",
    "2201080130":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Rural Other Principal Arterial: Total",
    "2201080131":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Other Principal Arterial: Rural Time 1",
    "2201080132":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Other Principal Arterial: Rural Time 2",
    "2201080133":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Other Principal Arterial: Rural Time 3",
    "2201080134":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Other Principal Arterial: Rural Time 4",
    "220108013B":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Rural Other Principal Arterial: Brake Wear",
    "220108013T":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Rural Other Principal Arterial: Tire Wear",
    "220108013V":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Rural Other Principal Arterial: Evap (except Refueling)",
    "220108013X":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Rural Other Principal Arterial: Exhaust",
    "2201080150":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Rural Minor Arterial: Total",
    "2201080151":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Minor Arterial: Rural Time 1",
    "2201080152":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Minor Arterial: Rural Time 2",
    "2201080153":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Minor Arterial: Rural Time 3",
    "2201080154":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Minor Arterial: Rural Time 4",
    "220108015B":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Rural Minor Arterial: Brake Wear",
    "220108015T":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Rural Minor Arterial: Tire Wear",
    "220108015V":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Rural Minor Arterial: Evap (except Refueling)",
    "220108015X":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Rural Minor Arterial: Exhaust",
    "2201080170":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Rural Major Collector: Total",
    "2201080171":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Major Collector: Rural Time 1",
    "2201080172":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Major Collector: Rural Time 2",
    "2201080173":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Major Collector: Rural Time 3",
    "2201080174":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Major Collector: Rural Time 4",
    "220108017B":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Rural Major Collector: Brake Wear",
    "220108017T":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Rural Major Collector: Tire Wear",
    "220108017V":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Rural Major Collector: Evap (except Refueling)",
    "220108017X":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Rural Major Collector: Exhaust",
    "2201080190":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Rural Minor Collector: Total",
    "2201080191":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Minor Collector: Rural Time 1",
    "2201080192":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Minor Collector: Rural Time 2",
    "2201080193":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Minor Collector: Rural Time 3",
    "2201080194":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Minor Collector: Rural Time 4",
    "220108019B":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Rural Minor Collector: Brake Wear",
    "220108019T":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Rural Minor Collector: Tire Wear",
    "220108019V":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Rural Minor Collector: Evap (except Refueling)",
    "220108019X":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Rural Minor Collector: Exhaust",
    "2201080210":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Rural Local: Total",
    "2201080211":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Local: Rural Time 1",
    "2201080212":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Local: Rural Time 2",
    "2201080213":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Local: Rural Time 3",
    "2201080214":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Local: Rural Time 4",
    "220108021B":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Rural Local: Brake Wear",
    "220108021T":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Rural Local: Tire Wear",
    "220108021V":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Rural Local: Evap (except Refueling)",
    "220108021X":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Rural Local: Exhaust",
    "2201080230":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Urban Interstate: Total",
    "2201080231":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Interstate: Urban Time 1",
    "2201080232":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Interstate: Urban Time 2",
    "2201080233":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Interstate: Urban Time 3",
    "2201080234":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Interstate: Urban Time 4",
    "220108023B":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Urban Interstate: Brake Wear",
    "220108023T":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Urban Interstate: Tire Wear",
    "220108023V":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Urban Interstate: Evap (except Refueling)",
    "220108023X":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Urban Interstate: Exhaust",
    "2201080250":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Urban Other Freeways and Expressways: Total",
    "2201080251":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Other Freeways and Expressways: Urban Time 1",
    "2201080252":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Other Freeways and Expressways: Urban Time 2",
    "2201080253":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Other Freeways and Expressways: Urban Time 3",
    "2201080254":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Other Freeways and Expressways: Urban Time 4",
    "220108025B":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Urban Other Freeways and Expressways: Brake Wear",
    "220108025T":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Urban Other Freeways and Expressways: Tire Wear",
    "220108025V":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Urban Other Freeways and Expressways: Evap (except Refueling)",
    "220108025X":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Urban Other Freeways and Expressways: Exhaust",
    "2201080270":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Urban Other Principal Arterial: Total",
    "2201080271":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Other Principal Arterial: Urban Time 1",
    "2201080272":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Other Principal Arterial: Urban Time 2",
    "2201080273":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Other Principal Arterial: Urban Time 3",
    "2201080274":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Other Principal Arterial: Urban Time 4",
    "220108027B":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Urban Other Principal Arterial: Brake Wear",
    "220108027T":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Urban Other Principal Arterial: Tire Wear",
    "220108027V":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Urban Other Principal Arterial: Evap (except Refueling)",
    "220108027X":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Urban Other Principal Arterial: Exhaust",
    "2201080290":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Urban Minor Arterial: Total",
    "2201080291":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Minor Arterial: Urban Time 1",
    "2201080292":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Minor Arterial: Urban Time 2",
    "2201080293":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Minor Arterial: Urban Time 3",
    "2201080294":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Minor Arterial: Urban Time 4",
    "220108029B":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Urban Minor Arterial: Brake Wear",
    "220108029T":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Urban Minor Arterial: Tire Wear",
    "220108029V":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Urban Minor Arterial: Evap (except Refueling)",
    "220108029X":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Urban Minor Arterial: Exhaust",
    "2201080310":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Urban Collector: Total",
    "2201080311":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Collector: Urban Time 1",
    "2201080312":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Collector: Urban Time 2",
    "2201080313":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Collector: Urban Time 3",
    "2201080314":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Collector: Urban Time 4",
    "220108031B":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Urban Collector: Brake Wear",
    "220108031T":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Urban Collector: Tire Wear",
    "220108031V":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Urban Collector: Evap (except Refueling)",
    "220108031X":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Urban Collector: Exhaust",
    "2201080330":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Urban Local: Total",
    "2201080331":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Local: Urban Time 1",
    "2201080332":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Local: Urban Time 2",
    "2201080333":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Local: Urban Time 3",
    "2201080334":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Local: Urban Time 4",
    "220108033B":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Urban Local: Brake Wear",
    "220108033T":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Urban Local: Tire Wear",
    "220108033V":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Urban Local: Evap (except Refueling)",
    "220108033X":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Urban Local: Exhaust",
    "2201080350":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Parking Area: Rural",
    "2201080370":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Parking Area: Urban",
    "2201080390":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycles (MC), Parking Area: Total",
    "2201110080":
        "Mobile Sources, Highway Vehicles - Gasoline, Motorcycle, All on and off-network processes except refueling",
    "2201210080":
        "Mobile Sources, Highway Vehicles - Gasoline, Passenger Car, All on and off-network processes except refueling",
    "2201310080":
        "Mobile Sources, Highway Vehicles - Gasoline, Passenger Truck, All on and off-network processes except refueling",
    "2201320080":
        "Mobile Sources, Highway Vehicles - Gasoline, Light Commercial Truck, All on and off-network processes except refueling",
    "2201410080":
        "Mobile Sources, Highway Vehicles - Gasoline, Other Buses, All on and off-network processes except refueling",
    "2201420080":
        "Mobile Sources, Highway Vehicles - Gasoline, Transit Bus, All on and off-network processes except refueling",
    "2201430080":
        "Mobile Sources, Highway Vehicles - Gasoline, School Bus, All on and off-network processes except refueling",
    "2201510080":
        "Mobile Sources, Highway Vehicles - Gasoline, Refuse Truck, All on and off-network processes except refueling",
    "2201520080":
        "Mobile Sources, Highway Vehicles - Gasoline, Single Unit Short-haul Truck, All on and off-network processes except refueling",
    "2201530080":
        "Mobile Sources, Highway Vehicles - Gasoline, Single Unit Long-haul Truck, All on and off-network processes except refueling",
    "2201540080":
        "Mobile Sources, Highway Vehicles - Gasoline, Motor Home, All on and off-network processes except refueling",
    "2201610080":
        "Mobile Sources, Highway Vehicles - Gasoline, Combination Short-haul Truck, All on and off-network processes except refueling",
    "2201620080":
        "Mobile Sources, Highway Vehicles - Gasoline, Combination Long-haul Truck, All on and off-network processes except refueling",
    "2202000062":
        "Mobile Sources, Highway Vehicles - Diesel, Refueling, Total Spillage and Displacement",
    "2202110080":
        "Mobile Sources, Highway Vehicles - Diesel, Motorcycle, All on and off-network processes except refueling",
    "2202210080":
        "Mobile Sources, Highway Vehicles - Diesel, Passenger Car, All on and off-network processes except refueling",
    "2202310080":
        "Mobile Sources, Highway Vehicles - Diesel, Passenger Truck, All on and off-network processes except refueling",
    "2202320080":
        "Mobile Sources, Highway Vehicles - Diesel, Light Commercial Truck, All on and off-network processes except refueling",
    "2202410080":
        "Mobile Sources, Highway Vehicles - Diesel, Other Buses, All on and off-network processes except refueling",
    "2202420080":
        "Mobile Sources, Highway Vehicles - Diesel, Transit Bus, All on and off-network processes except refueling",
    "2202430080":
        "Mobile Sources, Highway Vehicles - Diesel, School Bus, All on and off-network processes except refueling",
    "2202510080":
        "Mobile Sources, Highway Vehicles - Diesel, Refuse Truck, All on and off-network processes except refueling",
    "2202520080":
        "Mobile Sources, Highway Vehicles - Diesel, Single Unit Short-haul Truck, All on and off-network processes except refueling",
    "2202530080":
        "Mobile Sources, Highway Vehicles - Diesel, Single Unit Long-haul Truck, All on and off-network processes except refueling",
    "2202540080":
        "Mobile Sources, Highway Vehicles - Diesel, Motor Home, All on and off-network processes except refueling",
    "2202610080":
        "Mobile Sources, Highway Vehicles - Diesel, Combination Short-haul Truck, All on and off-network processes except refueling",
    "2202620080":
        "Mobile Sources, Highway Vehicles - Diesel, Combination Long-haul Truck, All on and off-network processes except refueling",
    "2203000062":
        "Mobile Sources, Highway Vehicles - Compressed Natural Gas (CNG), Refueling, Total Spillage and Displacement",
    "2203110080":
        "Mobile Sources, Highway Vehicles - Compressed Natural Gas (CNG), Motorcycle, All on and off-network processes except refueling",
    "2203210080":
        "Mobile Sources, Highway Vehicles - Compressed Natural Gas (CNG), Passenger Car, All on and off-network processes except refueling",
    "2203310080":
        "Mobile Sources, Highway Vehicles - Compressed Natural Gas (CNG), Passenger Truck, All on and off-network processes except refueling",
    "2203320080":
        "Mobile Sources, Highway Vehicles - Compressed Natural Gas (CNG), Light Commercial Truck, All on and off-network processes except refueling",
    "2203410080":
        "Mobile Sources, Highway Vehicles - Compressed Natural Gas (CNG), Other Buses, All on and off-network processes except refueling",
    "2203420080":
        "Mobile Sources, Highway Vehicles - Compressed Natural Gas (CNG), Transit Bus, All on and off-network processes except refueling",
    "2203430080":
        "Mobile Sources, Highway Vehicles - Compressed Natural Gas (CNG), School Bus, All on and off-network processes except refueling",
    "2203510080":
        "Mobile Sources, Highway Vehicles - Compressed Natural Gas (CNG), Refuse Truck, All on and off-network processes except refueling",
    "2203520080":
        "Mobile Sources, Highway Vehicles - Compressed Natural Gas (CNG), Single Unit Short-haul Truck, All on and off-network processes except refueling",
    "2203530080":
        "Mobile Sources, Highway Vehicles - Compressed Natural Gas (CNG), Single Unit Long-haul Truck, All on and off-network processes except refueling",
    "2203540080":
        "Mobile Sources, Highway Vehicles - Compressed Natural Gas (CNG), Motor Home, All on and off-network processes except refueling",
    "2203610080":
        "Mobile Sources, Highway Vehicles - Compressed Natural Gas (CNG), Combination Short-haul Truck, All on and off-network processes except refueling",
    "2203620080":
        "Mobile Sources, Highway Vehicles - Compressed Natural Gas (CNG), Combination Long-haul Truck, All on and off-network processes except refueling",
    "2204000062":
        "Mobile Sources, Highway Vehicles - Liquefied Petroleum Gas (LPG), Refueling, Total Spillage and Displacement",
    "2204110080":
        "Mobile Sources, Highway Vehicles - Liquefied Petroleum Gas (LPG), Motorcycle, All on and off-network processes except refueling",
    "2204210080":
        "Mobile Sources, Highway Vehicles - Liquefied Petroleum Gas (LPG), Passenger Car, All on and off-network processes except refueling",
    "2204310080":
        "Mobile Sources, Highway Vehicles - Liquefied Petroleum Gas (LPG), Passenger Truck, All on and off-network processes except refueling",
    "2204320080":
        "Mobile Sources, Highway Vehicles - Liquefied Petroleum Gas (LPG), Light Commercial Truck, All on and off-network processes except refueling",
    "2204410080":
        "Mobile Sources, Highway Vehicles - Liquefied Petroleum Gas (LPG), Other Buses, All on and off-network processes except refueling",
    "2204420080":
        "Mobile Sources, Highway Vehicles - Liquefied Petroleum Gas (LPG), Transit Bus, All on and off-network processes except refueling",
    "2204430080":
        "Mobile Sources, Highway Vehicles - Liquefied Petroleum Gas (LPG), School Bus, All on and off-network processes except refueling",
    "2204510080":
        "Mobile Sources, Highway Vehicles - Liquefied Petroleum Gas (LPG), Refuse Truck, All on and off-network processes except refueling",
    "2204520080":
        "Mobile Sources, Highway Vehicles - Liquefied Petroleum Gas (LPG), Single Unit Short-haul Truck, All on and off-network processes except refueling",
    "2204530080":
        "Mobile Sources, Highway Vehicles - Liquefied Petroleum Gas (LPG), Single Unit Long-haul Truck, All on and off-network processes except refueling",
    "2204540080":
        "Mobile Sources, Highway Vehicles - Liquefied Petroleum Gas (LPG), Motor Home, All on and off-network processes except refueling",
    "2204610080":
        "Mobile Sources, Highway Vehicles - Liquefied Petroleum Gas (LPG), Combination Short-haul Truck, All on and off-network processes except refueling",
    "2204620080":
        "Mobile Sources, Highway Vehicles - Liquefied Petroleum Gas (LPG), Combination Long-haul Truck, All on and off-network processes except refueling",
    "2205000062":
        "Mobile Sources, Highway Vehicles - Ethanol (E-85), Refueling, Total Spillage and Displacement",
    "2205110080":
        "Mobile Sources, Highway Vehicles - Ethanol (E-85), Motorcycle, All on and off-network processes except refueling",
    "2205210080":
        "Mobile Sources, Highway Vehicles - Ethanol (E-85), Passenger Car, All on and off-network processes except refueling",
    "2205310080":
        "Mobile Sources, Highway Vehicles - Ethanol (E-85), Passenger Truck, All on and off-network processes except refueling",
    "2205320080":
        "Mobile Sources, Highway Vehicles - Ethanol (E-85), Light Commercial Truck, All on and off-network processes except refueling",
    "2205410080":
        "Mobile Sources, Highway Vehicles - Ethanol (E-85), Other Buses, All on and off-network processes except refueling",
    "2205420080":
        "Mobile Sources, Highway Vehicles - Ethanol (E-85), Transit Bus, All on and off-network processes except refueling",
    "2205430080":
        "Mobile Sources, Highway Vehicles - Ethanol (E-85), School Bus, All on and off-network processes except refueling",
    "2205510080":
        "Mobile Sources, Highway Vehicles - Ethanol (E-85), Refuse Truck, All on and off-network processes except refueling",
    "2205520080":
        "Mobile Sources, Highway Vehicles - Ethanol (E-85), Single Unit Short-haul Truck, All on and off-network processes except refueling",
    "2205530080":
        "Mobile Sources, Highway Vehicles - Ethanol (E-85), Single Unit Long-haul Truck, All on and off-network processes except refueling",
    "2205540080":
        "Mobile Sources, Highway Vehicles - Ethanol (E-85), Motor Home, All on and off-network processes except refueling",
    "2205610080":
        "Mobile Sources, Highway Vehicles - Ethanol (E-85), Combination Short-haul Truck, All on and off-network processes except refueling",
    "2205620080":
        "Mobile Sources, Highway Vehicles - Ethanol (E-85), Combination Long-haul Truck, All on and off-network processes except refueling",
    "2209000062":
        "Mobile Sources, Highway Vehicles - Electricity, Refueling, Total Spillage and Displacement",
    "2209110080":
        "Mobile Sources, Highway Vehicles - Electricity, Motorcycle, All on and off-network processes except refueling",
    "2209210080":
        "Mobile Sources, Highway Vehicles - Electricity, Passenger Car, All on and off-network processes except refueling",
    "2209310080":
        "Mobile Sources, Highway Vehicles - Electricity, Passenger Truck, All on and off-network processes except refueling",
    "2209320080":
        "Mobile Sources, Highway Vehicles - Electricity, Light Commercial Truck, All on and off-network processes except refueling",
    "2209410080":
        "Mobile Sources, Highway Vehicles - Electricity, Other Buses, All on and off-network processes except refueling",
    "2209420080":
        "Mobile Sources, Highway Vehicles - Electricity, Transit Bus, All on and off-network processes except refueling",
    "2209430080":
        "Mobile Sources, Highway Vehicles - Electricity, School Bus, All on and off-network processes except refueling",
    "2209510080":
        "Mobile Sources, Highway Vehicles - Electricity, Refuse Truck, All on and off-network processes except refueling",
    "2209520080":
        "Mobile Sources, Highway Vehicles - Electricity, Single Unit Short-haul Truck, All on and off-network processes except refueling",
    "2209530080":
        "Mobile Sources, Highway Vehicles - Electricity, Single Unit Long-haul Truck, All on and off-network processes except refueling",
    "2209540080":
        "Mobile Sources, Highway Vehicles - Electricity, Motor Home, All on and off-network processes except refueling",
    "2209610080":
        "Mobile Sources, Highway Vehicles - Electricity, Combination Short-haul Truck, All on and off-network processes except refueling",
    "2209620080":
        "Mobile Sources, Highway Vehicles - Electricity, Combination Long-haul Truck, All on and off-network processes except refueling",
    "2222222222":
        "Mobile Sources, Border Crossings, Border Crossings, Border Crossings",
    "2230001000":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Total: All Road Types",
    "2230001110":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Rural Interstate: Total",
    "2230001111":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Interstate: Rural Time 1",
    "2230001112":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Interstate: Rural Time 2",
    "2230001113":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Interstate: Rural Time 3",
    "2230001114":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Interstate: Rural Time 4",
    "223000111B":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Rural Interstate: Brake Wear",
    "223000111T":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Rural Interstate: Tire Wear",
    "223000111X":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Rural Interstate: Exhaust",
    "2230001130":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Rural Other Principal Arterial: Total",
    "2230001131":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Other Principal Arterial: Rural Time 1",
    "2230001132":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Other Principal Arterial: Rural Time 2",
    "2230001133":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Other Principal Arterial: Rural Time 3",
    "2230001134":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Other Principal Arterial: Rural Time 4",
    "223000113B":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Rural Other Principal Arterial: Brake Wear",
    "223000113T":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Rural Other Principal Arterial: Tire Wear",
    "223000113X":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Rural Other Principal Arterial: Exhaust",
    "2230001150":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Rural Minor Arterial: Total",
    "2230001151":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Minor Arterial: Rural Time 1",
    "2230001152":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Minor Arterial: Rural Time 2",
    "2230001153":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Minor Arterial: Rural Time 3",
    "2230001154":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Minor Arterial: Rural Time 4",
    "223000115B":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Rural Minor Arterial: Brake Wear",
    "223000115T":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Rural Minor Arterial: Tire Wear",
    "223000115X":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Rural Minor Arterial: Exhaust",
    "2230001170":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Rural Major Collector: Total",
    "2230001171":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Major Collector: Rural Time 1",
    "2230001172":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Major Collector: Rural Time 2",
    "2230001173":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Major Collector: Rural Time 3",
    "2230001174":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Major Collector: Rural Time 4",
    "223000117B":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Rural Major Collector: Brake Wear",
    "223000117T":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Rural Major Collector: Tire Wear",
    "223000117X":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Rural Major Collector: Exhaust",
    "2230001190":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Rural Minor Collector: Total",
    "2230001191":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Minor Collector: Rural Time 1",
    "2230001192":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Minor Collector: Rural Time 2",
    "2230001193":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Minor Collector: Rural Time 3",
    "2230001194":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Minor Collector: Rural Time 4",
    "223000119B":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Rural Minor Collector: Brake Wear",
    "223000119T":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Rural Minor Collector: Tire Wear",
    "223000119X":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Rural Minor Collector: Exhaust",
    "2230001210":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Rural Local: Total",
    "2230001211":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Local: Rural Time 1",
    "2230001212":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Local: Rural Time 2",
    "2230001213":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Local: Rural Time 3",
    "2230001214":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Local: Rural Time 4",
    "223000121B":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Rural Local: Brake Wear",
    "223000121T":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Rural Local: Tire Wear",
    "223000121X":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Rural Local: Exhaust",
    "2230001230":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Urban Interstate: Total",
    "2230001231":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Interstate: Urban Time 1",
    "2230001232":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Interstate: Urban Time 2",
    "2230001233":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Interstate: Urban Time 3",
    "2230001234":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Interstate: Urban Time 4",
    "223000123B":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Urban Interstate: Brake Wear",
    "223000123T":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Urban Interstate: Tire Wear",
    "223000123X":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Urban Interstate: Exhaust",
    "2230001250":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Urban Other Freeways and Expressways: Total",
    "2230001251":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Other Freeways and Expressways: Urban Time 1",
    "2230001252":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Other Freeways and Expressways: Urban Time 2",
    "2230001253":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Other Freeways and Expressways: Urban Time 3",
    "2230001254":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Other Freeways and Expressways: Urban Time 4",
    "223000125B":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Urban Other Freeways and Expressways: Brake Wear",
    "223000125T":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Urban Other Freeways and Expressways: Tire Wear",
    "223000125X":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Urban Other Freeways and Expressways: Exhaust",
    "2230001270":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Urban Other Principal Arterial: Total",
    "2230001271":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Other Principal Arterial: Urban Time 1",
    "2230001272":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Other Principal Arterial: Urban Time 2",
    "2230001273":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Other Principal Arterial: Urban Time 3",
    "2230001274":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Other Principal Arterial: Urban Time 4",
    "223000127B":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Urban Other Principal Arterial: Brake Wear",
    "223000127T":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Urban Other Principal Arterial: Tire Wear",
    "223000127X":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Urban Other Principal Arterial: Exhaust",
    "2230001290":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Urban Minor Arterial: Total",
    "2230001291":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Minor Arterial: Urban Time 1",
    "2230001292":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Minor Arterial: Urban Time 2",
    "2230001293":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Minor Arterial: Urban Time 3",
    "2230001294":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Minor Arterial: Urban Time 4",
    "223000129B":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Urban Minor Arterial: Brake Wear",
    "223000129T":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Urban Minor Arterial: Tire Wear",
    "223000129X":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Urban Minor Arterial: Exhaust",
    "2230001310":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Urban Collector: Total",
    "2230001311":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Collector: Urban Time 1",
    "2230001312":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Collector: Urban Time 2",
    "2230001313":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Collector: Urban Time 3",
    "2230001314":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Collector: Urban Time 4",
    "223000131B":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Urban Collector: Brake Wear",
    "223000131T":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Urban Collector: Tire Wear",
    "223000131X":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Urban Collector: Exhaust",
    "2230001330":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Urban Local: Total",
    "2230001331":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Local: Urban Time 1",
    "2230001332":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Local: Urban Time 2",
    "2230001333":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Local: Urban Time 3",
    "2230001334":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Local: Urban Time 4",
    "223000133B":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Urban Local: Brake Wear",
    "223000133T":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Urban Local: Tire Wear",
    "223000133X":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Urban Local: Exhaust",
    "2230001350":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Parking Area: Rural",
    "2230001370":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Parking Area: Urban",
    "2230001390":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Vehicles (LDDV), Parking Area: Total",
    "2230060000":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Total: All Road Types",
    "2230060110":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Rural Interstate: Total",
    "2230060111":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Interstate: Rural Time 1",
    "2230060112":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Interstate: Rural Time 2",
    "2230060113":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Interstate: Rural Time 3",
    "2230060114":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Interstate: Rural Time 4",
    "223006011B":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Rural Interstate: Brake Wear",
    "223006011T":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Rural Interstate: Tire Wear",
    "223006011X":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Rural Interstate: Exhaust",
    "2230060130":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Rural Other Principal Arterial: Total",
    "2230060131":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Other Principal Arterial: Rural Time 1",
    "2230060132":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Other Principal Arterial: Rural Time 2",
    "2230060133":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Other Principal Arterial: Rural Time 3",
    "2230060134":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Other Principal Arterial: Rural Time 4",
    "223006013B":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Rural Other Principal Arterial: Brake Wear",
    "223006013T":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Rural Other Principal Arterial: Tire Wear",
    "223006013X":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Rural Other Principal Arterial: Exhaust",
    "2230060150":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Rural Minor Arterial: Total",
    "2230060151":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Minor Arterial: Rural Time 1",
    "2230060152":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Minor Arterial: Rural Time 2",
    "2230060153":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Minor Arterial: Rural Time 3",
    "2230060154":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Minor Arterial: Rural Time 4",
    "223006015B":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Rural Minor Arterial: Brake Wear",
    "223006015T":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Rural Minor Arterial: Tire Wear",
    "223006015X":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Rural Minor Arterial: Exhaust",
    "2230060170":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Rural Major Collector: Total",
    "2230060171":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Major Collector: Rural Time 1",
    "2230060172":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Major Collector: Rural Time 2",
    "2230060173":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Major Collector: Rural Time 3",
    "2230060174":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Major Collector: Rural Time 4",
    "223006017B":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Rural Major Collector: Brake Wear",
    "223006017T":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Rural Major Collector: Tire Wear",
    "223006017X":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Rural Major Collector: Exhaust",
    "2230060190":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Rural Minor Collector: Total",
    "2230060191":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Minor Collector: Rural Time 1",
    "2230060192":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Minor Collector: Rural Time 2",
    "2230060193":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Minor Collector: Rural Time 3",
    "2230060194":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Minor Collector: Rural Time 4",
    "223006019B":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Rural Minor Collector: Brake Wear",
    "223006019T":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Rural Minor Collector: Tire Wear",
    "223006019X":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Rural Minor Collector: Exhaust",
    "2230060210":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Rural Local: Total",
    "2230060211":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Local: Rural Time 1",
    "2230060212":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Local: Rural Time 2",
    "2230060213":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Local: Rural Time 3",
    "2230060214":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Local: Rural Time 4",
    "223006021B":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Rural Local: Brake Wear",
    "223006021T":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Rural Local: Tire Wear",
    "223006021X":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Rural Local: Exhaust",
    "2230060230":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Urban Interstate: Total",
    "2230060231":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Interstate: Urban Time 1",
    "2230060232":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Interstate: Urban Time 2",
    "2230060233":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Interstate: Urban Time 3",
    "2230060234":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Interstate: Urban Time 4",
    "223006023B":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Urban Interstate: Brake Wear",
    "223006023T":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Urban Interstate: Tire Wear",
    "223006023X":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Urban Interstate: Exhaust",
    "2230060250":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Urban Other Freeways and Expressways: Total",
    "2230060251":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Other Freeways and Expressways: Urban Time 1",
    "2230060252":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Other Freeways and Expressways: Urban Time 2",
    "2230060253":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Other Freeways and Expressways: Urban Time 3",
    "2230060254":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Other Freeways and Expressways: Urban Time 4",
    "223006025B":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Urban Other Freeways and Expressways: Brake Wear",
    "223006025T":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Urban Other Freeways and Expressways: Tire Wear",
    "223006025X":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Urban Other Freeways and Expressways: Exhaust",
    "2230060270":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Urban Other Principal Arterial: Total",
    "2230060271":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Other Principal Arterial: Urban Time 1",
    "2230060272":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Other Principal Arterial: Urban Time 2",
    "2230060273":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Other Principal Arterial: Urban Time 3",
    "2230060274":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Other Principal Arterial: Urban Time 4",
    "223006027B":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Urban Other Principal Arterial: Brake Wear",
    "223006027T":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Urban Other Principal Arterial: Tire Wear",
    "223006027X":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Urban Other Principal Arterial: Exhaust",
    "2230060290":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Urban Minor Arterial: Total",
    "2230060291":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Minor Arterial: Urban Time 1",
    "2230060292":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Minor Arterial: Urban Time 2",
    "2230060293":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Minor Arterial: Urban Time 3",
    "2230060294":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Minor Arterial: Urban Time 4",
    "223006029B":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Urban Minor Arterial: Brake Wear",
    "223006029T":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Urban Minor Arterial: Tire Wear",
    "223006029X":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Urban Minor Arterial: Exhaust",
    "2230060310":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Urban Collector: Total",
    "2230060311":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Collector: Urban Time 1",
    "2230060312":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Collector: Urban Time 2",
    "2230060313":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Collector: Urban Time 3",
    "2230060314":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Collector: Urban Time 4",
    "223006031B":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Urban Collector: Brake Wear",
    "223006031T":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Urban Collector: Tire Wear",
    "223006031X":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Urban Collector: Exhaust",
    "2230060330":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Urban Local: Total",
    "2230060331":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Local: Urban Time 1",
    "2230060332":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Local: Urban Time 2",
    "2230060333":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Local: Urban Time 3",
    "2230060334":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Local: Urban Time 4",
    "223006033B":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Urban Local: Brake Wear",
    "223006033T":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Urban Local: Tire Wear",
    "223006033X":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Urban Local: Exhaust",
    "2230060350":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Parking Area: Rural",
    "2230060370":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Parking Area: Urban",
    "2230060390":
        "Mobile Sources, Highway Vehicles - Diesel, Light Duty Diesel Trucks 1 thru 4 (M6) (LDDT), Parking Area: Total",
    "2230070000":
        "Mobile Sources, Highway Vehicles - Diesel, All HDDV including Buses (use subdivisions -071 thru -075 if possible), Total: All Road Types",
    "2230070110":
        "Mobile Sources, Highway Vehicles - Diesel, All HDDV including Buses (use subdivisions -071 thru -075 if possible), Rural Interstate: Total",
    "2230070111":
        "Mobile Sources, Highway Vehicles - Diesel, All HDDV including Buses (use subdivisions -071 thru -075 if possible), Interstate: Rural Time 1",
    "2230070112":
        "Mobile Sources, Highway Vehicles - Diesel, All HDDV including Buses (use subdivisions -071 thru -075 if possible), Interstate: Rural Time 2",
    "2230070113":
        "Mobile Sources, Highway Vehicles - Diesel, All HDDV including Buses (use subdivisions -071 thru -075 if possible), Interstate: Rural Time 3",
    "2230070114":
        "Mobile Sources, Highway Vehicles - Diesel, All HDDV including Buses (use subdivisions -071 thru -075 if possible), Interstate: Rural Time 4",
    "2230070130":
        "Mobile Sources, Highway Vehicles - Diesel, All HDDV including Buses (use subdivisions -071 thru -075 if possible), Rural Other Principal Arterial: Total",
    "2230070131":
        "Mobile Sources, Highway Vehicles - Diesel, All HDDV including Buses (use subdivisions -071 thru -075 if possible), Other Principal Arterial: Rural Time 1",
    "2230070132":
        "Mobile Sources, Highway Vehicles - Diesel, All HDDV including Buses (use subdivisions -071 thru -075 if possible), Other Principal Arterial: Rural Time 2",
    "2230070133":
        "Mobile Sources, Highway Vehicles - Diesel, All HDDV including Buses (use subdivisions -071 thru -075 if possible), Other Principal Arterial: Rural Time 3",
    "2230070134":
        "Mobile Sources, Highway Vehicles - Diesel, All HDDV including Buses (use subdivisions -071 thru -075 if possible), Other Principal Arterial: Rural Time 4",
    "2230070150":
        "Mobile Sources, Highway Vehicles - Diesel, All HDDV including Buses (use subdivisions -071 thru -075 if possible), Rural Minor Arterial: Total",
    "2230070151":
        "Mobile Sources, Highway Vehicles - Diesel, All HDDV including Buses (use subdivisions -071 thru -075 if possible), Minor Arterial: Rural Time 1",
    "2230070152":
        "Mobile Sources, Highway Vehicles - Diesel, All HDDV including Buses (use subdivisions -071 thru -075 if possible), Minor Arterial: Rural Time 2",
    "2230070153":
        "Mobile Sources, Highway Vehicles - Diesel, All HDDV including Buses (use subdivisions -071 thru -075 if possible), Minor Arterial: Rural Time 3",
    "2230070154":
        "Mobile Sources, Highway Vehicles - Diesel, All HDDV including Buses (use subdivisions -071 thru -075 if possible), Minor Arterial: Rural Time 4",
    "2230070170":
        "Mobile Sources, Highway Vehicles - Diesel, All HDDV including Buses (use subdivisions -071 thru -075 if possible), Rural Major Collector: Total",
    "2230070171":
        "Mobile Sources, Highway Vehicles - Diesel, All HDDV including Buses (use subdivisions -071 thru -075 if possible), Major Collector: Rural Time 1",
    "2230070172":
        "Mobile Sources, Highway Vehicles - Diesel, All HDDV including Buses (use subdivisions -071 thru -075 if possible), Major Collector: Rural Time 2",
    "2230070173":
        "Mobile Sources, Highway Vehicles - Diesel, All HDDV including Buses (use subdivisions -071 thru -075 if possible), Major Collector: Rural Time 3",
    "2230070174":
        "Mobile Sources, Highway Vehicles - Diesel, All HDDV including Buses (use subdivisions -071 thru -075 if possible), Major Collector: Rural Time 4",
    "2230070190":
        "Mobile Sources, Highway Vehicles - Diesel, All HDDV including Buses (use subdivisions -071 thru -075 if possible), Rural Minor Collector: Total",
    "2230070191":
        "Mobile Sources, Highway Vehicles - Diesel, All HDDV including Buses (use subdivisions -071 thru -075 if possible), Minor Collector: Rural Time 1",
    "2230070192":
        "Mobile Sources, Highway Vehicles - Diesel, All HDDV including Buses (use subdivisions -071 thru -075 if possible), Minor Collector: Rural Time 2",
    "2230070193":
        "Mobile Sources, Highway Vehicles - Diesel, All HDDV including Buses (use subdivisions -071 thru -075 if possible), Minor Collector: Rural Time 3",
    "2230070194":
        "Mobile Sources, Highway Vehicles - Diesel, All HDDV including Buses (use subdivisions -071 thru -075 if possible), Minor Collector: Rural Time 4",
    "2230070210":
        "Mobile Sources, Highway Vehicles - Diesel, All HDDV including Buses (use subdivisions -071 thru -075 if possible), Rural Local: Total",
    "2230070211":
        "Mobile Sources, Highway Vehicles - Diesel, All HDDV including Buses (use subdivisions -071 thru -075 if possible), Local: Rural Time 1",
    "2230070212":
        "Mobile Sources, Highway Vehicles - Diesel, All HDDV including Buses (use subdivisions -071 thru -075 if possible), Local: Rural Time 2",
    "2230070213":
        "Mobile Sources, Highway Vehicles - Diesel, All HDDV including Buses (use subdivisions -071 thru -075 if possible), Local: Rural Time 3",
    "2230070214":
        "Mobile Sources, Highway Vehicles - Diesel, All HDDV including Buses (use subdivisions -071 thru -075 if possible), Local: Rural Time 4",
    "2230070230":
        "Mobile Sources, Highway Vehicles - Diesel, All HDDV including Buses (use subdivisions -071 thru -075 if possible), Urban Interstate: Total",
    "2230070231":
        "Mobile Sources, Highway Vehicles - Diesel, All HDDV including Buses (use subdivisions -071 thru -075 if possible), Interstate: Urban Time 1",
    "2230070232":
        "Mobile Sources, Highway Vehicles - Diesel, All HDDV including Buses (use subdivisions -071 thru -075 if possible), Interstate: Urban Time 2",
    "2230070233":
        "Mobile Sources, Highway Vehicles - Diesel, All HDDV including Buses (use subdivisions -071 thru -075 if possible), Interstate: Urban Time 3",
    "2230070234":
        "Mobile Sources, Highway Vehicles - Diesel, All HDDV including Buses (use subdivisions -071 thru -075 if possible), Interstate: Urban Time 4",
    "2230070250":
        "Mobile Sources, Highway Vehicles - Diesel, All HDDV including Buses (use subdivisions -071 thru -075 if possible), Urban Other Freeways and Expressways: Total",
    "2230070251":
        "Mobile Sources, Highway Vehicles - Diesel, All HDDV including Buses (use subdivisions -071 thru -075 if possible), Other Freeways and Expressways: Urban Time 1",
    "2230070252":
        "Mobile Sources, Highway Vehicles - Diesel, All HDDV including Buses (use subdivisions -071 thru -075 if possible), Other Freeways and Expressways: Urban Time 2",
    "2230070253":
        "Mobile Sources, Highway Vehicles - Diesel, All HDDV including Buses (use subdivisions -071 thru -075 if possible), Other Freeways and Expressways: Urban Time 3",
    "2230070254":
        "Mobile Sources, Highway Vehicles - Diesel, All HDDV including Buses (use subdivisions -071 thru -075 if possible), Other Freeways and Expressways: Urban Time 4",
    "2230070270":
        "Mobile Sources, Highway Vehicles - Diesel, All HDDV including Buses (use subdivisions -071 thru -075 if possible), Urban Other Principal Arterial: Total",
    "2230070271":
        "Mobile Sources, Highway Vehicles - Diesel, All HDDV including Buses (use subdivisions -071 thru -075 if possible), Other Principal Arterial: Urban Time 1",
    "2230070272":
        "Mobile Sources, Highway Vehicles - Diesel, All HDDV including Buses (use subdivisions -071 thru -075 if possible), Other Principal Arterial: Urban Time 2",
    "2230070273":
        "Mobile Sources, Highway Vehicles - Diesel, All HDDV including Buses (use subdivisions -071 thru -075 if possible), Other Principal Arterial: Urban Time 3",
    "2230070274":
        "Mobile Sources, Highway Vehicles - Diesel, All HDDV including Buses (use subdivisions -071 thru -075 if possible), Other Principal Arterial: Urban Time 4",
    "2230070290":
        "Mobile Sources, Highway Vehicles - Diesel, All HDDV including Buses (use subdivisions -071 thru -075 if possible), Urban Minor Arterial: Total",
    "2230070291":
        "Mobile Sources, Highway Vehicles - Diesel, All HDDV including Buses (use subdivisions -071 thru -075 if possible), Minor Arterial: Urban Time 1",
    "2230070292":
        "Mobile Sources, Highway Vehicles - Diesel, All HDDV including Buses (use subdivisions -071 thru -075 if possible), Minor Arterial: Urban Time 2",
    "2230070293":
        "Mobile Sources, Highway Vehicles - Diesel, All HDDV including Buses (use subdivisions -071 thru -075 if possible), Minor Arterial: Urban Time 3",
    "2230070294":
        "Mobile Sources, Highway Vehicles - Diesel, All HDDV including Buses (use subdivisions -071 thru -075 if possible), Minor Arterial: Urban Time 4",
    "2230070310":
        "Mobile Sources, Highway Vehicles - Diesel, All HDDV including Buses (use subdivisions -071 thru -075 if possible), Urban Collector: Total",
    "2230070311":
        "Mobile Sources, Highway Vehicles - Diesel, All HDDV including Buses (use subdivisions -071 thru -075 if possible), Collector: Urban Time 1",
    "2230070312":
        "Mobile Sources, Highway Vehicles - Diesel, All HDDV including Buses (use subdivisions -071 thru -075 if possible), Collector: Urban Time 2",
    "2230070313":
        "Mobile Sources, Highway Vehicles - Diesel, All HDDV including Buses (use subdivisions -071 thru -075 if possible), Collector: Urban Time 3",
    "2230070314":
        "Mobile Sources, Highway Vehicles - Diesel, All HDDV including Buses (use subdivisions -071 thru -075 if possible), Collector: Urban Time 4",
    "2230070330":
        "Mobile Sources, Highway Vehicles - Diesel, All HDDV including Buses (use subdivisions -071 thru -075 if possible), Urban Local: Total",
    "2230070331":
        "Mobile Sources, Highway Vehicles - Diesel, All HDDV including Buses (use subdivisions -071 thru -075 if possible), Local: Urban Time 1",
    "2230070332":
        "Mobile Sources, Highway Vehicles - Diesel, All HDDV including Buses (use subdivisions -071 thru -075 if possible), Local: Urban Time 2",
    "2230070333":
        "Mobile Sources, Highway Vehicles - Diesel, All HDDV including Buses (use subdivisions -071 thru -075 if possible), Local: Urban Time 3",
    "2230070334":
        "Mobile Sources, Highway Vehicles - Diesel, All HDDV including Buses (use subdivisions -071 thru -075 if possible), Local: Urban Time 4",
    "2230071110":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 2B, Rural Interstate: Total",
    "223007111B":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 2B, Rural Interstate: Brake Wear",
    "223007111T":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 2B, Rural Interstate: Tire Wear",
    "223007111X":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 2B, Rural Interstate: Exhaust",
    "2230071130":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 2B, Rural Other Principal Arterial: Total",
    "223007113B":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 2B, Rural Other Principal Arterial: Brake Wear",
    "223007113T":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 2B, Rural Other Principal Arterial: Tire Wear",
    "223007113X":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 2B, Rural Other Principal Arterial: Exhaust",
    "2230071150":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 2B, Rural Minor Arterial: Total",
    "223007115B":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 2B, Rural Minor Arterial: Brake Wear",
    "223007115T":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 2B, Rural Minor Arterial: Tire Wear",
    "223007115X":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 2B, Rural Minor Arterial: Exhaust",
    "2230071170":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 2B, Rural Major Collector: Total",
    "223007117B":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 2B, Rural Major Collector: Brake Wear",
    "223007117T":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 2B, Rural Major Collector: Tire Wear",
    "223007117X":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 2B, Rural Major Collector: Exhaust",
    "2230071190":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 2B, Rural Minor Collector: Total",
    "223007119B":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 2B, Rural Minor Collector: Brake Wear",
    "223007119T":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 2B, Rural Minor Collector: Tire Wear",
    "223007119X":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 2B, Rural Minor Collector: Exhaust",
    "2230071210":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 2B, Rural Local: Total",
    "223007121B":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 2B, Rural Local: Brake Wear",
    "223007121T":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 2B, Rural Local: Tire Wear",
    "223007121X":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 2B, Rural Local: Exhaust",
    "2230071230":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 2B, Urban Interstate: Total",
    "223007123B":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 2B, Urban Interstate: Brake Wear",
    "223007123T":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 2B, Urban Interstate: Tire Wear",
    "223007123X":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 2B, Urban Interstate: Exhaust",
    "2230071250":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 2B, Urban Other Freeways and Expressways: Total",
    "223007125B":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 2B, Urban Other Freeways and Expressways: Brake Wear",
    "223007125T":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 2B, Urban Other Freeways and Expressways: Tire Wear",
    "223007125X":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 2B, Urban Other Freeways and Expressways: Exhaust",
    "2230071270":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 2B, Urban Other Principal Arterial: Total",
    "223007127B":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 2B, Urban Other Principal Arterial: Brake Wear",
    "223007127T":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 2B, Urban Other Principal Arterial: Tire Wear",
    "223007127X":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 2B, Urban Other Principal Arterial: Exhaust",
    "2230071290":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 2B, Urban Minor Arterial: Total",
    "223007129B":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 2B, Urban Minor Arterial: Brake Wear",
    "223007129T":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 2B, Urban Minor Arterial: Tire Wear",
    "223007129X":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 2B, Urban Minor Arterial: Exhaust",
    "2230071310":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 2B, Urban Collector: Total",
    "223007131B":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 2B, Urban Collector: Brake Wear",
    "223007131T":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 2B, Urban Collector: Tire Wear",
    "223007131X":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 2B, Urban Collector: Exhaust",
    "2230071330":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 2B, Urban Local: Total",
    "223007133B":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 2B, Urban Local: Brake Wear",
    "223007133T":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 2B, Urban Local: Tire Wear",
    "223007133X":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 2B, Urban Local: Exhaust",
    "2230071350":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 2B, Parking Area: Rural",
    "2230071370":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 2B, Parking Area: Urban",
    "2230071390":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 2B, Parking Area: Total",
    "2230072110":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 3, 4, & 5, Rural Interstate: Total",
    "223007211B":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 3, 4, & 5, Rural Interstate: Brake Wear",
    "223007211T":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 3, 4, & 5, Rural Interstate: Tire Wear",
    "223007211X":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 3, 4, & 5, Rural Interstate: Exhaust",
    "2230072130":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 3, 4, & 5, Rural Other Principal Arterial: Total",
    "223007213B":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 3, 4, & 5, Rural Other Principal Arterial: Brake Wear",
    "223007213T":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 3, 4, & 5, Rural Other Principal Arterial: Tire Wear",
    "223007213X":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 3, 4, & 5, Rural Other Principal Arterial: Exhaust",
    "2230072150":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 3, 4, & 5, Rural Minor Arterial: Total",
    "223007215B":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 3, 4, & 5, Rural Minor Arterial: Brake Wear",
    "223007215T":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 3, 4, & 5, Rural Minor Arterial: Tire Wear",
    "223007215X":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 3, 4, & 5, Rural Minor Arterial: Exhaust",
    "2230072170":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 3, 4, & 5, Rural Major Collector: Total",
    "223007217B":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 3, 4, & 5, Rural Major Collector: Brake Wear",
    "223007217T":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 3, 4, & 5, Rural Major Collector: Tire Wear",
    "223007217X":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 3, 4, & 5, Rural Major Collector: Exhaust",
    "2230072190":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 3, 4, & 5, Rural Minor Collector: Total",
    "223007219B":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 3, 4, & 5, Rural Minor Collector: Brake Wear",
    "223007219T":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 3, 4, & 5, Rural Minor Collector: Tire Wear",
    "223007219X":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 3, 4, & 5, Rural Minor Collector: Exhaust",
    "2230072210":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 3, 4, & 5, Rural Local: Total",
    "223007221B":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 3, 4, & 5, Rural Local: Brake Wear",
    "223007221T":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 3, 4, & 5, Rural Local: Tire Wear",
    "223007221X":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 3, 4, & 5, Rural Local: Exhaust",
    "2230072230":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 3, 4, & 5, Urban Interstate: Total",
    "223007223B":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 3, 4, & 5, Urban Interstate: Brake Wear",
    "223007223T":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 3, 4, & 5, Urban Interstate: Tire Wear",
    "223007223X":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 3, 4, & 5, Urban Interstate: Exhaust",
    "2230072250":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 3, 4, & 5, Urban Other Freeways and Expressways: Total",
    "223007225B":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 3, 4, & 5, Urban Other Freeways and Expressways: Brake Wear",
    "223007225T":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 3, 4, & 5, Urban Other Freeways and Expressways: Tire Wear",
    "223007225X":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 3, 4, & 5, Urban Other Freeways and Expressways: Exhaust",
    "2230072270":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 3, 4, & 5, Urban Other Principal Arterial: Total",
    "223007227B":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 3, 4, & 5, Urban Other Principal Arterial: Brake Wear",
    "223007227T":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 3, 4, & 5, Urban Other Principal Arterial: Tire Wear",
    "223007227X":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 3, 4, & 5, Urban Other Principal Arterial: Exhaust",
    "2230072290":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 3, 4, & 5, Urban Minor Arterial: Total",
    "223007229B":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 3, 4, & 5, Urban Minor Arterial: Brake Wear",
    "223007229T":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 3, 4, & 5, Urban Minor Arterial: Tire Wear",
    "223007229X":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 3, 4, & 5, Urban Minor Arterial: Exhaust",
    "2230072310":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 3, 4, & 5, Urban Collector: Total",
    "223007231B":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 3, 4, & 5, Urban Collector: Brake Wear",
    "223007231T":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 3, 4, & 5, Urban Collector: Tire Wear",
    "223007231X":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 3, 4, & 5, Urban Collector: Exhaust",
    "2230072330":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 3, 4, & 5, Urban Local: Total",
    "223007233B":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 3, 4, & 5, Urban Local: Brake Wear",
    "223007233T":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 3, 4, & 5, Urban Local: Tire Wear",
    "223007233X":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 3, 4, & 5, Urban Local: Exhaust",
    "2230072350":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 3, 4, & 5, Parking Area: Rural",
    "2230072370":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 3, 4, & 5, Parking Area: Urban",
    "2230072390":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 3, 4, & 5, Parking Area: Total",
    "2230073110":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 6 & 7, Rural Interstate: Total",
    "223007311B":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 6 & 7, Rural Interstate: Brake Wear",
    "223007311T":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 6 & 7, Rural Interstate: Tire Wear",
    "223007311X":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 6 & 7, Rural Interstate: Exhaust",
    "2230073130":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 6 & 7, Rural Other Principal Arterial: Total",
    "223007313B":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 6 & 7, Rural Other Principal Arterial: Brake Wear",
    "223007313T":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 6 & 7, Rural Other Principal Arterial: Tire Wear",
    "223007313X":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 6 & 7, Rural Other Principal Arterial: Exhaust",
    "2230073150":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 6 & 7, Rural Minor Arterial: Total",
    "223007315B":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 6 & 7, Rural Minor Arterial: Brake Wear",
    "223007315T":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 6 & 7, Rural Minor Arterial: Tire Wear",
    "223007315X":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 6 & 7, Rural Minor Arterial: Exhaust",
    "2230073170":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 6 & 7, Rural Major Collector: Total",
    "223007317B":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 6 & 7, Rural Major Collector: Brake Wear",
    "223007317T":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 6 & 7, Rural Major Collector: Tire Wear",
    "223007317X":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 6 & 7, Rural Major Collector: Exhaust",
    "2230073190":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 6 & 7, Rural Minor Collector: Total",
    "223007319B":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 6 & 7, Rural Minor Collector: Brake Wear",
    "223007319T":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 6 & 7, Rural Minor Collector: Tire Wear",
    "223007319X":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 6 & 7, Rural Minor Collector: Exhaust",
    "2230073210":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 6 & 7, Rural Local: Total",
    "223007321B":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 6 & 7, Rural Local: Brake Wear",
    "223007321T":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 6 & 7, Rural Local: Tire Wear",
    "223007321X":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 6 & 7, Rural Local: Exhaust",
    "2230073230":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 6 & 7, Urban Interstate: Total",
    "223007323B":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 6 & 7, Urban Interstate: Brake Wear",
    "223007323T":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 6 & 7, Urban Interstate: Tire Wear",
    "223007323X":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 6 & 7, Urban Interstate: Exhaust",
    "2230073250":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 6 & 7, Urban Other Freeways and Expressways: Total",
    "223007325B":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 6 & 7, Urban Other Freeways and Expressways: Brake Wear",
    "223007325T":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 6 & 7, Urban Other Freeways and Expressways: Tire Wear",
    "223007325X":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 6 & 7, Urban Other Freeways and Expressways: Exhaust",
    "2230073270":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 6 & 7, Urban Other Principal Arterial: Total",
    "223007327B":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 6 & 7, Urban Other Principal Arterial: Brake Wear",
    "223007327T":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 6 & 7, Urban Other Principal Arterial: Tire Wear",
    "223007327X":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 6 & 7, Urban Other Principal Arterial: Exhaust",
    "2230073290":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 6 & 7, Urban Minor Arterial: Total",
    "223007329B":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 6 & 7, Urban Minor Arterial: Brake Wear",
    "223007329T":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 6 & 7, Urban Minor Arterial: Tire Wear",
    "223007329X":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 6 & 7, Urban Minor Arterial: Exhaust",
    "2230073310":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 6 & 7, Urban Collector: Total",
    "223007331B":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 6 & 7, Urban Collector: Brake Wear",
    "223007331T":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 6 & 7, Urban Collector: Tire Wear",
    "223007331X":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 6 & 7, Urban Collector: Exhaust",
    "2230073330":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 6 & 7, Urban Local: Total",
    "223007333B":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 6 & 7, Urban Local: Brake Wear",
    "223007333T":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 6 & 7, Urban Local: Tire Wear",
    "223007333X":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 6 & 7, Urban Local: Exhaust",
    "2230073350":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 6 & 7, Parking Area: Rural",
    "2230073370":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 6 & 7, Parking Area: Urban",
    "2230073390":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 6 & 7, Parking Area: Total",
    "2230074110":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 8A & 8B, Rural Interstate: Total",
    "223007411B":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 8A & 8B, Rural Interstate: Brake Wear",
    "223007411T":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 8A & 8B, Rural Interstate: Tire Wear",
    "223007411X":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 8A & 8B, Rural Interstate: Exhaust",
    "2230074130":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 8A & 8B, Rural Other Principal Arterial: Total",
    "223007413B":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 8A & 8B, Rural Other Principal Arterial: Brake Wear",
    "223007413T":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 8A & 8B, Rural Other Principal Arterial: Tire Wear",
    "223007413X":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 8A & 8B, Rural Other Principal Arterial: Exhaust",
    "2230074150":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 8A & 8B, Rural Minor Arterial: Total",
    "223007415B":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 8A & 8B, Rural Minor Arterial: Brake Wear",
    "223007415T":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 8A & 8B, Rural Minor Arterial: Tire Wear",
    "223007415X":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 8A & 8B, Rural Minor Arterial: Exhaust",
    "2230074170":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 8A & 8B, Rural Major Collector: Total",
    "223007417B":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 8A & 8B, Rural Major Collector: Brake Wear",
    "223007417T":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 8A & 8B, Rural Major Collector: Tire Wear",
    "223007417X":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 8A & 8B, Rural Major Collector: Exhaust",
    "2230074190":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 8A & 8B, Rural Minor Collector: Total",
    "223007419B":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 8A & 8B, Rural Minor Collector: Brake Wear",
    "223007419T":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 8A & 8B, Rural Minor Collector: Tire Wear",
    "223007419X":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 8A & 8B, Rural Minor Collector: Exhaust",
    "2230074210":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 8A & 8B, Rural Local: Total",
    "223007421B":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 8A & 8B, Rural Local: Brake Wear",
    "223007421T":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 8A & 8B, Rural Local: Tire Wear",
    "223007421X":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 8A & 8B, Rural Local: Exhaust",
    "2230074230":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 8A & 8B, Urban Interstate: Total",
    "223007423B":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 8A & 8B, Urban Interstate: Brake Wear",
    "223007423T":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 8A & 8B, Urban Interstate: Tire Wear",
    "223007423X":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 8A & 8B, Urban Interstate: Exhaust",
    "2230074250":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 8A & 8B, Urban Other Freeways and Expressways: Total",
    "223007425B":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 8A & 8B, Urban Other Freeways and Expressways: Brake Wear",
    "223007425T":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 8A & 8B, Urban Other Freeways and Expressways: Tire Wear",
    "223007425X":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 8A & 8B, Urban Other Freeways and Expressways: Exhaust",
    "2230074270":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 8A & 8B, Urban Other Principal Arterial: Total",
    "223007427B":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 8A & 8B, Urban Other Principal Arterial: Brake Wear",
    "223007427T":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 8A & 8B, Urban Other Principal Arterial: Tire Wear",
    "223007427X":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 8A & 8B, Urban Other Principal Arterial: Exhaust",
    "2230074290":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 8A & 8B, Urban Minor Arterial: Total",
    "223007429B":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 8A & 8B, Urban Minor Arterial: Brake Wear",
    "223007429T":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 8A & 8B, Urban Minor Arterial: Tire Wear",
    "223007429X":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 8A & 8B, Urban Minor Arterial: Exhaust",
    "2230074310":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 8A & 8B, Urban Collector: Total",
    "223007431B":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 8A & 8B, Urban Collector: Brake Wear",
    "223007431T":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 8A & 8B, Urban Collector: Tire Wear",
    "223007431X":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 8A & 8B, Urban Collector: Exhaust",
    "2230074330":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 8A & 8B, Urban Local: Total",
    "223007433B":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 8A & 8B, Urban Local: Brake Wear",
    "223007433T":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 8A & 8B, Urban Local: Tire Wear",
    "223007433X":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 8A & 8B, Urban Local: Exhaust",
    "2230074350":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 8A & 8B, Parking Area: Rural",
    "2230074370":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 8A & 8B, Parking Area: Urban",
    "2230074390":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Vehicles (HDDV) Class 8A & 8B, Parking Area: Total",
    "2230075110":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Buses (School & Transit), Rural Interstate: Total",
    "223007511B":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Buses (School & Transit), Rural Interstate: Brake Wear",
    "223007511T":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Buses (School & Transit), Rural Interstate: Tire Wear",
    "223007511X":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Buses (School & Transit), Rural Interstate: Exhaust",
    "2230075130":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Buses (School & Transit), Rural Other Principal Arterial: Total",
    "223007513B":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Buses (School & Transit), Rural Other Principal Arterial: Brake Wear",
    "223007513T":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Buses (School & Transit), Rural Other Principal Arterial: Tire Wear",
    "223007513X":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Buses (School & Transit), Rural Other Principal Arterial: Exhaust",
    "2230075150":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Buses (School & Transit), Rural Minor Arterial: Total",
    "223007515B":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Buses (School & Transit), Rural Minor Arterial: Brake Wear",
    "223007515T":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Buses (School & Transit), Rural Minor Arterial: Tire Wear",
    "223007515X":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Buses (School & Transit), Rural Minor Arterial: Exhaust",
    "2230075170":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Buses (School & Transit), Rural Major Collector: Total",
    "223007517B":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Buses (School & Transit), Rural Major Collector: Brake Wear",
    "223007517T":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Buses (School & Transit), Rural Major Collector: Tire Wear",
    "223007517X":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Buses (School & Transit), Rural Major Collector: Exhaust",
    "2230075190":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Buses (School & Transit), Rural Minor Collector: Total",
    "223007519B":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Buses (School & Transit), Rural Minor Collector: Brake Wear",
    "223007519T":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Buses (School & Transit), Rural Minor Collector: Tire Wear",
    "223007519X":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Buses (School & Transit), Rural Minor Collector: Exhaust",
    "2230075210":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Buses (School & Transit), Rural Local: Total",
    "223007521B":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Buses (School & Transit), Rural Local: Brake Wear",
    "223007521T":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Buses (School & Transit), Rural Local: Tire Wear",
    "223007521X":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Buses (School & Transit), Rural Local: Exhaust",
    "2230075230":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Buses (School & Transit), Urban Interstate: Total",
    "223007523B":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Buses (School & Transit), Urban Interstate: Brake Wear",
    "223007523T":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Buses (School & Transit), Urban Interstate: Tire Wear",
    "223007523X":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Buses (School & Transit), Urban Interstate: Exhaust",
    "2230075250":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Buses (School & Transit), Urban Other Freeways and Expressways: Total",
    "223007525B":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Buses (School & Transit), Urban Other Freeways and Expressways: Brake Wear",
    "223007525T":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Buses (School & Transit), Urban Other Freeways and Expressways: Tire Wear",
    "223007525X":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Buses (School & Transit), Urban Other Freeways and Expressways: Exhaust",
    "2230075270":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Buses (School & Transit), Urban Other Principal Arterial: Total",
    "223007527B":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Buses (School & Transit), Urban Other Principal Arterial: Brake Wear",
    "223007527T":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Buses (School & Transit), Urban Other Principal Arterial: Tire Wear",
    "223007527X":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Buses (School & Transit), Urban Other Principal Arterial: Exhaust",
    "2230075290":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Buses (School & Transit), Urban Minor Arterial: Total",
    "223007529B":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Buses (School & Transit), Urban Minor Arterial: Brake Wear",
    "223007529T":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Buses (School & Transit), Urban Minor Arterial: Tire Wear",
    "223007529X":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Buses (School & Transit), Urban Minor Arterial: Exhaust",
    "2230075310":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Buses (School & Transit), Urban Collector: Total",
    "223007531B":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Buses (School & Transit), Urban Collector: Brake Wear",
    "223007531T":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Buses (School & Transit), Urban Collector: Tire Wear",
    "223007531X":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Buses (School & Transit), Urban Collector: Exhaust",
    "2230075330":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Buses (School & Transit), Urban Local: Total",
    "223007533B":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Buses (School & Transit), Urban Local: Brake Wear",
    "223007533T":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Buses (School & Transit), Urban Local: Tire Wear",
    "223007533X":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Buses (School & Transit), Urban Local: Exhaust",
    "2230075350":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Buses (School & Transit), Parking Area: Rural",
    "2230075370":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Buses (School & Transit), Parking Area: Urban",
    "2230075390":
        "Mobile Sources, Highway Vehicles - Diesel, Heavy Duty Diesel Buses (School & Transit), Parking Area: Total",
    "2260000000":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, 2-Stroke Gasoline except Rail and Marine, All",
    "2260001000":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Recreational Equipment, Total",
    "2260001010":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Recreational Equipment, Motorcycles: Off-road",
    "2260001020":
        "Mobile Sources, Off-highway Vehicle Gasoline, Recreational Equipment, 2-Stroke Snowmobiles",
    "2260001022":
        "Mobile Sources, Off-highway Vehicle Gasoline, Recreational Equipment, 2-Stroke Other Recreational Equip.",
    "2260001030":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Recreational Equipment, All Terrain Vehicles",
    "2260001040":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Recreational Equipment, Minibikes",
    "2260001050":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Recreational Equipment, Golf Carts",
    "2260001060":
        "Mobile Sources, Off-highway Vehicle Gasoline, Recreational Equipment, 2-Stroke Specialty Vehicles/Carts",
    "2260002000":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Construction and Mining Equipment, Total",
    "2260002003":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Construction and Mining Equipment, Pavers",
    "2260002006":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Construction and Mining Equipment, Tampers/Rammers",
    "2260002009":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Construction and Mining Equipment, Plate Compactors",
    "2260002012":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Construction and Mining Equipment, Concrete Pavers",
    "2260002015":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Construction and Mining Equipment, Rollers",
    "2260002018":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Construction and Mining Equipment, Scrapers",
    "2260002021":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Construction and Mining Equipment, Paving Equipment",
    "2260002022":
        "Mobile Sources, Off-highway Vehicle Gasoline, Construction Equipment, 2-Stroke Construction Equipment",
    "2260002024":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Construction and Mining Equipment, Surfacing Equipment",
    "2260002027":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Construction and Mining Equipment, Signal Boards/Light Plants",
    "2260002030":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Construction and Mining Equipment, Trenchers",
    "2260002033":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Construction and Mining Equipment, Bore/Drill Rigs",
    "2260002036":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Construction and Mining Equipment, Excavators",
    "2260002039":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Construction and Mining Equipment, Concrete/Industrial Saws",
    "2260002042":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Construction and Mining Equipment, Cement and Mortar Mixers",
    "2260002045":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Construction and Mining Equipment, Cranes",
    "2260002048":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Construction and Mining Equipment, Graders",
    "2260002051":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Construction and Mining Equipment, Off-highway Trucks",
    "2260002054":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Construction and Mining Equipment, Crushing/Processing Equipment",
    "2260002057":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Construction and Mining Equipment, Rough Terrain Forklifts",
    "2260002060":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Construction and Mining Equipment, Rubber Tire Loaders",
    "2260002063":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Construction and Mining Equipment, Rubber Tire Tractor/Dozers",
    "2260002066":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Construction and Mining Equipment, Tractors/Loaders/Backhoes",
    "2260002069":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Construction and Mining Equipment, Crawler Tractor/Dozers",
    "2260002072":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Construction and Mining Equipment, Skid Steer Loaders",
    "2260002075":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Construction and Mining Equipment, Off-highway Tractors",
    "2260002078":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Construction and Mining Equipment, Dumpers/Tenders",
    "2260002081":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Construction and Mining Equipment, Other Construction Equipment",
    "2260003000":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Industrial Equipment, Total",
    "2260003010":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Industrial Equipment, Aerial Lifts",
    "2260003020":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Industrial Equipment, Forklifts",
    "2260003022":
        "Mobile Sources, Off-highway Vehicle Gasoline, Industrial Equipment, 2-Stroke Industrial Equipment",
    "2260003030":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Industrial Equipment, Sweepers/Scrubbers",
    "2260003040":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Industrial Equipment, Other General Industrial Equipment",
    "2260003050":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Industrial Equipment, Other Material Handling Equipment",
    "2260003060":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Industrial Equipment, AC\Refrigeration",
    "2260003070":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Industrial Equipment, Terminal Tractors",
    "2260004000":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Lawn and Garden Equipment, All",
    "2260004010":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Lawn and Garden Equipment, Lawn Mowers (Residential)",
    "2260004011":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Lawn and Garden Equipment, Lawn Mowers (Commercial)",
    "2260004015":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Lawn and Garden Equipment, Rotary Tillers < 6 HP (Residential)",
    "2260004016":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Lawn and Garden Equipment, Rotary Tillers < 6 HP (Commercial)",
    "2260004020":
        "Mobile Sources, Off-highway Vehicle Gasoline, Lawn and Garden Equipment, 2-Stroke Chain Saws < 6 HP (Residential)",
    "2260004021":
        "Mobile Sources, Off-highway Vehicle Gasoline, Lawn and Garden Equipment, 2-Stroke Chain Saws < 6 HP (Commercial)",
    "2260004022":
        "Mobile Sources, Off-highway Vehicle Gasoline, Lawn and Garden Equipment, 2-Stroke Mowers, Tractors, Turf Eqt (Commercial)",
    "2260004025":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Lawn and Garden Equipment, Trimmers/Edgers/Brush Cutters (Residential)",
    "2260004026":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Lawn and Garden Equipment, Trimmers/Edgers/Brush Cutters (Commercial)",
    "2260004030":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Lawn and Garden Equipment, Leafblowers/Vacuums (Residential)",
    "2260004031":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Lawn and Garden Equipment, Leafblowers/Vacuums (Commercial)",
    "2260004033":
        "Mobile Sources, Off-highway Vehicle Gasoline, Lawn and Garden Equipment, 2-Stroke Lawn & Garden Eqt (Residential)",
    "2260004035":
        "Mobile Sources, Off-highway Vehicle Gasoline, Lawn and Garden Equipment, 2-Stroke Snowblowers (Residential)",
    "2260004036":
        "Mobile Sources, Off-highway Vehicle Gasoline, Lawn and Garden Equipment, 2-Stroke Snowblowers (Commercial)",
    "2260004040":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Lawn and Garden Equipment, Rear Engine Riding Mowers (Residential)",
    "2260004041":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Lawn and Garden Equipment, Rear Engine Riding Mowers (Commercial)",
    "2260004044":
        "Mobile Sources, Off-highway Vehicle Gasoline, Lawn and Garden Equipment, 2-Stroke Lawn & Garden Eqt (Commercial)",
    "2260004045":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Lawn and Garden Equipment, Front Mowers (Residential)",
    "2260004046":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Lawn and Garden Equipment, Front Mowers (Commercial)",
    "2260004050":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Lawn and Garden Equipment, Shredders < 6 HP (Residential)",
    "2260004051":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Lawn and Garden Equipment, Shredders < 6 HP (Commercial)",
    "2260004055":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Lawn and Garden Equipment, Lawn and Garden Tractors (Residential)",
    "2260004056":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Lawn and Garden Equipment, Lawn and Garden Tractors (Commercial)",
    "2260004060":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Lawn and Garden Equipment, Wood Splitters (Residential)",
    "2260004061":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Lawn and Garden Equipment, Wood Splitters (Commercial)",
    "2260004065":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Lawn and Garden Equipment, Chippers/Stump Grinders (Residential)",
    "2260004066":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Lawn and Garden Equipment, Chippers/Stump Grinders (Commercial)",
    "2260004070":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Lawn and Garden Equipment, Commercial Turf Equipment",
    "2260004071":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Lawn and Garden Equipment, Turf Equipment (Commercial)",
    "2260004075":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Lawn and Garden Equipment, Other Lawn and Garden Equipment (Residential)",
    "2260004076":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Lawn and Garden Equipment, Other Lawn and Garden Equipment (Commercial)",
    "2260005000":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Agricultural Equipment, Total",
    "2260005010":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Agricultural Equipment, 2-Wheel Tractors",
    "2260005015":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Agricultural Equipment, Agricultural Tractors",
    "2260005020":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Agricultural Equipment, Combines",
    "2260005022":
        "Mobile Sources, Off-highway Vehicle Gasoline, Agricultural Equipment, 2-Stroke Agriculture Equipment",
    "2260005025":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Agricultural Equipment, Balers",
    "2260005030":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Agricultural Equipment, Agricultural Mowers",
    "2260005035":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Agricultural Equipment, Sprayers",
    "2260005040":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Agricultural Equipment, Tillers > 6 HP",
    "2260005045":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Agricultural Equipment, Swathers",
    "2260005050":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Agricultural Equipment, Hydro-power Units",
    "2260005055":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Agricultural Equipment, Other Agricultural Equipment",
    "2260005060":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Agricultural Equipment, Irrigation Sets",
    "2260006000":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Commercial Equipment, Total",
    "2260006005":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Commercial Equipment, Generator Sets",
    "2260006010":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Commercial Equipment, Pumps",
    "2260006015":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Commercial Equipment, Air Compressors",
    "2260006020":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Commercial Equipment, Gas Compressors",
    "2260006022":
        "Mobile Sources, Off-highway Vehicle Gasoline, Commercial Equipment, 2-Stroke Commercial Equipment",
    "2260006025":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Commercial Equipment, Welders",
    "2260006030":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Commercial Equipment, Pressure Washers",
    "2260006035":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Commercial Equipment, Hydro-power Units",
    "2260007000":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Logging Equipment, Total",
    "2260007005":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Logging Equipment, Chain Saws > 6 HP",
    "2260007010":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Logging Equipment, Shredders > 6 HP",
    "2260007015":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Logging Equipment, Forest Eqp - Feller/Bunch/Skidder",
    "2260007020":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Logging Equipment, Fellers/Bunchers",
    "2260007022":
        "Mobile Sources, Off-highway Vehicle Gasoline, Logging Equipment, 2-Stroke Logging Equipment",
    "2260008010":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Airport Ground Support Equipment, Terminal Tractors",
    "2260009000":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Underground Mining Equipment, All",
    "2260009010":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Underground Mining Equipment, Other Underground Mining Equipment",
    "2260010000":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Industrial Equipment, All",
    "2260010010":
        "Mobile Sources, Off-highway Vehicle Gasoline, 2-Stroke, Industrial Equipment, Other Oil Field Equipment",
    "2265000000":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, 4-Stroke Gasoline except Rail and Marine, All",
    "2265001000":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Recreational Equipment, Total",
    "2265001010":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Recreational Equipment, Motorcycles: Off-road",
    "2265001020":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Recreational Equipment, Snowmobiles",
    "2265001022":
        "Mobile Sources, Off-highway Vehicle Gasoline, Recreational Equipment, 4-Stroke Other Recreational Equip.",
    "2265001030":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Recreational Equipment, All Terrain Vehicles",
    "2265001040":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Recreational Equipment, Minibikes",
    "2265001050":
        "Mobile Sources, Off-highway Vehicle Gasoline, Recreational Equipment, 4-Stroke Golf Carts",
    "2265001060":
        "Mobile Sources, Off-highway Vehicle Gasoline, Recreational Equipment, 4-Stroke Specialty Vehicles/Carts",
    "2265002000":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Construction and Mining Equipment, Total",
    "2265002003":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Construction and Mining Equipment, Pavers",
    "2265002006":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Construction and Mining Equipment, Tampers/Rammers",
    "2265002009":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Construction and Mining Equipment, Plate Compactors",
    "2265002012":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Construction and Mining Equipment, Concrete Pavers",
    "2265002015":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Construction and Mining Equipment, Rollers",
    "2265002018":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Construction and Mining Equipment, Scrapers",
    "2265002021":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Construction and Mining Equipment, Paving Equipment",
    "2265002022":
        "Mobile Sources, Off-highway Vehicle Gasoline, Construction Equipment, 4-Stroke Construction Equipment",
    "2265002024":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Construction and Mining Equipment, Surfacing Equipment",
    "2265002027":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Construction and Mining Equipment, Signal Boards/Light Plants",
    "2265002030":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Construction and Mining Equipment, Trenchers",
    "2265002033":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Construction and Mining Equipment, Bore/Drill Rigs",
    "2265002036":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Construction and Mining Equipment, Excavators",
    "2265002039":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Construction and Mining Equipment, Concrete/Industrial Saws",
    "2265002042":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Construction and Mining Equipment, Cement and Mortar Mixers",
    "2265002045":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Construction and Mining Equipment, Cranes",
    "2265002048":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Construction and Mining Equipment, Graders",
    "2265002051":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Construction and Mining Equipment, Off-highway Trucks",
    "2265002054":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Construction and Mining Equipment, Crushing/Processing Equipment",
    "2265002057":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Construction and Mining Equipment, Rough Terrain Forklifts",
    "2265002060":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Construction and Mining Equipment, Rubber Tire Loaders",
    "2265002063":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Construction and Mining Equipment, Rubber Tire Tractor/Dozers",
    "2265002066":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Construction and Mining Equipment, Tractors/Loaders/Backhoes",
    "2265002069":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Construction and Mining Equipment, Crawler Tractor/Dozers",
    "2265002072":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Construction and Mining Equipment, Skid Steer Loaders",
    "2265002075":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Construction and Mining Equipment, Off-highway Tractors",
    "2265002078":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Construction and Mining Equipment, Dumpers/Tenders",
    "2265002081":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Construction and Mining Equipment, Other Construction Equipment",
    "2265003000":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Industrial Equipment, Total",
    "2265003010":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Industrial Equipment, Aerial Lifts",
    "2265003020":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Industrial Equipment, Forklifts",
    "2265003022":
        "Mobile Sources, Off-highway Vehicle Gasoline, Industrial Equipment, 4-Stroke Industrial Equipment",
    "2265003030":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Industrial Equipment, Sweepers/Scrubbers",
    "2265003040":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Industrial Equipment, Other General Industrial Equipment",
    "2265003050":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Industrial Equipment, Other Material Handling Equipment",
    "2265003060":
        "Mobile Sources, Off-highway Vehicle Gasoline, Industrial Equipment, 4-Stroke AC\Refrigeration",
    "2265003070":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Industrial Equipment, Terminal Tractors",
    "2265004000":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Lawn and Garden Equipment, All",
    "2265004010":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Lawn and Garden Equipment, Lawn Mowers (Residential)",
    "2265004011":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Lawn and Garden Equipment, Lawn Mowers (Commercial)",
    "2265004015":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Lawn and Garden Equipment, Rotary Tillers < 6 HP (Residential)",
    "2265004016":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Lawn and Garden Equipment, Rotary Tillers < 6 HP (Commercial)",
    "2265004020":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Lawn and Garden Equipment, Chain Saws < 6 HP (Residential)",
    "2265004021":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Lawn and Garden Equipment, Chain Saws < 6 HP (Commercial)",
    "2265004022":
        "Mobile Sources, Off-highway Vehicle Gasoline, Lawn and Garden Equipment, 4-Stroke Mowers, Tractors, Turf Eqt (Commercial)",
    "2265004025":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Lawn and Garden Equipment, Trimmers/Edgers/Brush Cutters (Residential)",
    "2265004026":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Lawn and Garden Equipment, Trimmers/Edgers/Brush Cutters (Commercial)",
    "2265004030":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Lawn and Garden Equipment, Leafblowers/Vacuums (Residential)",
    "2265004031":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Lawn and Garden Equipment, Leafblowers/Vacuums (Commercial)",
    "2265004033":
        "Mobile Sources, Off-highway Vehicle Gasoline, Lawn and Garden Equipment, 4-Stroke Lawn & Garden Eqt (Residential)",
    "2265004035":
        "Mobile Sources, Off-highway Vehicle Gasoline, Lawn and Garden Equipment, 4-Stroke Snowblowers (Residential)",
    "2265004036":
        "Mobile Sources, Off-highway Vehicle Gasoline, Lawn and Garden Equipment, 4-Stroke Snowblowers (Commercial)",
    "2265004040":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Lawn and Garden Equipment, Rear Engine Riding Mowers (Residential)",
    "2265004041":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Lawn and Garden Equipment, Rear Engine Riding Mowers (Commercial)",
    "2265004044":
        "Mobile Sources, Off-highway Vehicle Gasoline, Lawn and Garden Equipment, 4-Stroke Lawn & Garden Eqt (Commercial)",
    "2265004045":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Lawn and Garden Equipment, Front Mowers (Residential)",
    "2265004046":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Lawn and Garden Equipment, Front Mowers (Commercial)",
    "2265004050":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Lawn and Garden Equipment, Shredders < 6 HP (Residential)",
    "2265004051":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Lawn and Garden Equipment, Shredders < 6 HP (Commercial)",
    "2265004055":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Lawn and Garden Equipment, Lawn and Garden Tractors (Residential)",
    "2265004056":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Lawn and Garden Equipment, Lawn and Garden Tractors (Commercial)",
    "2265004060":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Lawn and Garden Equipment, Wood Splitters (Residential)",
    "2265004061":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Lawn and Garden Equipment, Wood Splitters (Commercial)",
    "2265004065":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Lawn and Garden Equipment, Chippers/Stump Grinders (Residential)",
    "2265004066":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Lawn and Garden Equipment, Chippers/Stump Grinders (Commercial)",
    "2265004070":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Lawn and Garden Equipment, Commercial Turf Equipment",
    "2265004071":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Lawn and Garden Equipment, Turf Equipment (Commercial)",
    "2265004075":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Lawn and Garden Equipment, Other Lawn and Garden Equipment (Residential)",
    "2265004076":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Lawn and Garden Equipment, Other Lawn and Garden Equipment (Commercial)",
    "2265005000":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Agricultural Equipment, Total",
    "2265005010":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Agricultural Equipment, 2-Wheel Tractors",
    "2265005015":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Agricultural Equipment, Agricultural Tractors",
    "2265005020":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Agricultural Equipment, Combines",
    "2265005022":
        "Mobile Sources, Off-highway Vehicle Gasoline, Agricultural Equipment, 4-Stroke Agriculture Equipment",
    "2265005025":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Agricultural Equipment, Balers",
    "2265005030":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Agricultural Equipment, Agricultural Mowers",
    "2265005035":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Agricultural Equipment, Sprayers",
    "2265005040":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Agricultural Equipment, Tillers > 6 HP",
    "2265005045":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Agricultural Equipment, Swathers",
    "2265005050":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Agricultural Equipment, Hydro-power Units",
    "2265005055":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Agricultural Equipment, Other Agricultural Equipment",
    "2265005060":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Agricultural Equipment, Irrigation Sets",
    "2265006000":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Commercial Equipment, Total",
    "2265006005":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Commercial Equipment, Generator Sets",
    "2265006010":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Commercial Equipment, Pumps",
    "2265006015":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Commercial Equipment, Air Compressors",
    "2265006020":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Commercial Equipment, Gas Compressors",
    "2265006022":
        "Mobile Sources, Off-highway Vehicle Gasoline, Commercial Equipment, 4-Stroke Commercial Equipment",
    "2265006025":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Commercial Equipment, Welders",
    "2265006030":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Commercial Equipment, Pressure Washers",
    "2265006035":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Commercial Equipment, Hydro-power Units",
    "2265007000":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Logging Equipment, Total",
    "2265007005":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Logging Equipment, Chain Saws > 6 HP",
    "2265007010":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Logging Equipment, Shredders > 6 HP",
    "2265007015":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Logging Equipment, Forest Eqp - Feller/Bunch/Skidder",
    "2265007020":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Logging Equipment, Fellers/Bunchers",
    "2265007022":
        "Mobile Sources, Off-highway Vehicle Gasoline, Logging Equipment, 4-Stroke Logging Equipment",
    "2265008010":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Airport Ground Support Equipment, Terminal Tractors",
    "2265009000":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Underground Mining Equipment, All",
    "2265009010":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Underground Mining Equipment, Other Underground Mining Equipment",
    "2265010000":
        "Mobile Sources, Off-highway Vehicle Gasoline, 4-Stroke, Industrial Equipment, All",
    "2265010010":
        "Mobile Sources, Off-highway Vehicle Gasoline, Industrial Equipment, 4-Stroke Other Oil Field Equipment",
    "2267000000":
        "Mobile Sources, LPG, LPG Equipment except Rail and Marine, All",
    "2267001000":
        "Mobile Sources, LPG, Recreational Equipment, All",
    "2267001010":
        "Mobile Sources, LPG, Recreational Equipment, Motorcycles: Off-road",
    "2267001020":
        "Mobile Sources, LPG, Recreational Equipment, Snowmobiles",
    "2267001030":
        "Mobile Sources, LPG, Recreational Equipment, All Terrain Vehicles",
    "2267001040":
        "Mobile Sources, LPG, Recreational Equipment, Minibikes",
    "2267001050":
        "Mobile Sources, LPG, Recreational Equipment, Golf Carts",
    "2267001060":
        "Mobile Sources, Off-highway Vehicle LPG, Recreational Equipment, LPG Specialty Vehicles/Carts",
    "2267002000":
        "Mobile Sources, LPG, Construction and Mining Equipment, All",
    "2267002003":
        "Mobile Sources, LPG, Construction and Mining Equipment, Pavers",
    "2267002006":
        "Mobile Sources, LPG, Construction and Mining Equipment, Tampers/Rammers",
    "2267002009":
        "Mobile Sources, LPG, Construction and Mining Equipment, Plate Compactors",
    "2267002015":
        "Mobile Sources, LPG, Construction and Mining Equipment, Rollers",
    "2267002018":
        "Mobile Sources, LPG, Construction and Mining Equipment, Scrapers",
    "2267002021":
        "Mobile Sources, LPG, Construction and Mining Equipment, Paving Equipment",
    "2267002022":
        "Mobile Sources, Off-highway Vehicle LPG, Construction Equipment, LPG Construction Equipment",
    "2267002024":
        "Mobile Sources, LPG, Construction and Mining Equipment, Surfacing Equipment",
    "2267002027":
        "Mobile Sources, LPG, Construction and Mining Equipment, Signal Boards/Light Plants",
    "2267002030":
        "Mobile Sources, LPG, Construction and Mining Equipment, Trenchers",
    "2267002033":
        "Mobile Sources, LPG, Construction and Mining Equipment, Bore/Drill Rigs",
    "2267002036":
        "Mobile Sources, LPG, Construction and Mining Equipment, Excavators",
    "2267002039":
        "Mobile Sources, LPG, Construction and Mining Equipment, Concrete/Industrial Saws",
    "2267002042":
        "Mobile Sources, LPG, Construction and Mining Equipment, Cement and Mortar Mixers",
    "2267002045":
        "Mobile Sources, LPG, Construction and Mining Equipment, Cranes",
    "2267002048":
        "Mobile Sources, LPG, Construction and Mining Equipment, Graders",
    "2267002051":
        "Mobile Sources, LPG, Construction and Mining Equipment, Off-highway Trucks",
    "2267002054":
        "Mobile Sources, LPG, Construction and Mining Equipment, Crushing/Processing Equipment",
    "2267002057":
        "Mobile Sources, LPG, Construction and Mining Equipment, Rough Terrain Forklifts",
    "2267002060":
        "Mobile Sources, LPG, Construction and Mining Equipment, Rubber Tire Loaders",
    "2267002063":
        "Mobile Sources, LPG, Construction and Mining Equipment, Rubber Tire Tractor/Dozers",
    "2267002066":
        "Mobile Sources, LPG, Construction and Mining Equipment, Tractors/Loaders/Backhoes",
    "2267002069":
        "Mobile Sources, LPG, Construction and Mining Equipment, Crawler Tractor/Dozers",
    "2267002072":
        "Mobile Sources, LPG, Construction and Mining Equipment, Skid Steer Loaders",
    "2267002075":
        "Mobile Sources, LPG, Construction and Mining Equipment, Off-highway Tractors",
    "2267002078":
        "Mobile Sources, LPG, Construction and Mining Equipment, Dumpers/Tenders",
    "2267002081":
        "Mobile Sources, LPG, Construction and Mining Equipment, Other Construction Equipment",
    "2267003000":
        "Mobile Sources, LPG, Industrial Equipment, All",
    "2267003010":
        "Mobile Sources, LPG, Industrial Equipment, Aerial Lifts",
    "2267003020":
        "Mobile Sources, LPG, Industrial Equipment, Forklifts",
    "2267003022":
        "Mobile Sources, Off-highway Vehicle LPG, Industrial Equipment, LPG Industrial Equipment",
    "2267003030":
        "Mobile Sources, LPG, Industrial Equipment, Sweepers/Scrubbers",
    "2267003040":
        "Mobile Sources, LPG, Industrial Equipment, Other General Industrial Equipment",
    "2267003050":
        "Mobile Sources, LPG, Industrial Equipment, Other Material Handling Equipment",
    "2267003060":
        "Mobile Sources, LPG, Industrial Equipment, AC\Refrigeration",
    "2267003070":
        "Mobile Sources, LPG, Industrial Equipment, Terminal Tractors",
    "2267004000":
        "Mobile Sources, LPG, Lawn and Garden Equipment, All",
    "2267004010":
        "Mobile Sources, LPG, Lawn and Garden Equipment, Lawn Mowers (Residential)",
    "2267004011":
        "Mobile Sources, LPG, Lawn and Garden Equipment, Lawn Mowers (Commercial)",
    "2267004015":
        "Mobile Sources, LPG, Lawn and Garden Equipment, Rotary Tillers < 6 HP (Residential)",
    "2267004016":
        "Mobile Sources, LPG, Lawn and Garden Equipment, Rotary Tillers < 6 HP (Commercial)",
    "2267004020":
        "Mobile Sources, LPG, Lawn and Garden Equipment, Chain Saws < 6 HP (Residential)",
    "2267004021":
        "Mobile Sources, LPG, Lawn and Garden Equipment, Chain Saws < 6 HP (Commercial)",
    "2267004022":
        "Mobile Sources, Off-highway Vehicle LPG, Lawn and Garden Equipment, LPG Mowers, Tractors, Turf Eqt (Commercial)",
    "2267004025":
        "Mobile Sources, LPG, Lawn and Garden Equipment, Trimmers/Edgers/Brush Cutters (Residential)",
    "2267004026":
        "Mobile Sources, LPG, Lawn and Garden Equipment, Trimmers/Edgers/Brush Cutters (Commercial)",
    "2267004030":
        "Mobile Sources, LPG, Lawn and Garden Equipment, Leafblowers/Vacuums (Residential)",
    "2267004031":
        "Mobile Sources, LPG, Lawn and Garden Equipment, Leafblowers/Vacuums (Commercial)",
    "2267004033":
        "Mobile Sources, Off-highway Vehicle LPG, Lawn and Garden Equipment, LPG Lawn & Garden Eqt (Residential)",
    "2267004035":
        "Mobile Sources, LPG, Lawn and Garden Equipment, Snowblowers (Residential)",
    "2267004036":
        "Mobile Sources, LPG, Lawn and Garden Equipment, Snowblowers (Commercial)",
    "2267004040":
        "Mobile Sources, LPG, Lawn and Garden Equipment, Rear Engine Riding Mowers (Residential)",
    "2267004041":
        "Mobile Sources, LPG, Lawn and Garden Equipment, Rear Engine Riding Mowers (Commercial)",
    "2267004044":
        "Mobile Sources, Off-highway Vehicle LPG, Lawn and Garden Equipment, LPG Lawn & Garden Eqt (Commercial)",
    "2267004045":
        "Mobile Sources, LPG, Lawn and Garden Equipment, Front Mowers (Residential)",
    "2267004046":
        "Mobile Sources, LPG, Lawn and Garden Equipment, Front Mowers (Commercial)",
    "2267004050":
        "Mobile Sources, LPG, Lawn and Garden Equipment, Shredders < 6 HP (Residential)",
    "2267004051":
        "Mobile Sources, LPG, Lawn and Garden Equipment, Shredders < 6 HP (Commercial)",
    "2267004055":
        "Mobile Sources, LPG, Lawn and Garden Equipment, Lawn and Garden Tractors (Residential)",
    "2267004056":
        "Mobile Sources, LPG, Lawn and Garden Equipment, Lawn and Garden Tractors (Commercial)",
    "2267004060":
        "Mobile Sources, LPG, Lawn and Garden Equipment, Wood Splitters (Residential)",
    "2267004061":
        "Mobile Sources, LPG, Lawn and Garden Equipment, Wood Splitters (Commercial)",
    "2267004065":
        "Mobile Sources, LPG, Lawn and Garden Equipment, Chippers/Stump Grinders (Residential)",
    "2267004066":
        "Mobile Sources, LPG, Lawn and Garden Equipment, Chippers/Stump Grinders (Commercial)",
    "2267004071":
        "Mobile Sources, LPG, Lawn and Garden Equipment, Turf Equipment (Commercial)",
    "2267004075":
        "Mobile Sources, LPG, Lawn and Garden Equipment, Other Lawn and Garden Equipment (Residential)",
    "2267004076":
        "Mobile Sources, LPG, Lawn and Garden Equipment, Other Lawn and Garden Equipment (Commercial)",
    "2267005000":
        "Mobile Sources, LPG, Agricultural Equipment, All",
    "2267005010":
        "Mobile Sources, LPG, Agricultural Equipment, 2-Wheel Tractors",
    "2267005015":
        "Mobile Sources, LPG, Agricultural Equipment, Agricultural Tractors",
    "2267005020":
        "Mobile Sources, LPG, Agricultural Equipment, Combines",
    "2267005022":
        "Mobile Sources, Off-highway Vehicle LPG, Agricultural Equipment, LPG Agriculture Equipment",
    "2267005025":
        "Mobile Sources, LPG, Agricultural Equipment, Balers",
    "2267005030":
        "Mobile Sources, LPG, Agricultural Equipment, Agricultural Mowers",
    "2267005035":
        "Mobile Sources, LPG, Agricultural Equipment, Sprayers",
    "2267005040":
        "Mobile Sources, LPG, Agricultural Equipment, Tillers > 6 HP",
    "2267005045":
        "Mobile Sources, LPG, Agricultural Equipment, Swathers",
    "2267005050":
        "Mobile Sources, LPG, Agricultural Equipment, Hydro-power Units",
    "2267005055":
        "Mobile Sources, LPG, Agricultural Equipment, Other Agricultural Equipment",
    "2267005060":
        "Mobile Sources, LPG, Agricultural Equipment, Irrigation Sets",
    "2267006000":
        "Mobile Sources, LPG, Commercial Equipment, All",
    "2267006005":
        "Mobile Sources, LPG, Commercial Equipment, Generator Sets",
    "2267006010":
        "Mobile Sources, LPG, Commercial Equipment, Pumps",
    "2267006015":
        "Mobile Sources, LPG, Commercial Equipment, Air Compressors",
    "2267006020":
        "Mobile Sources, LPG, Commercial Equipment, Gas Compressors",
    "2267006022":
        "Mobile Sources, Off-highway Vehicle LPG, Commercial Equipment, LPG Commercial Equipment",
    "2267006025":
        "Mobile Sources, LPG, Commercial Equipment, Welders",
    "2267006030":
        "Mobile Sources, LPG, Commercial Equipment, Pressure Washers",
    "2267006035":
        "Mobile Sources, LPG, Commercial Equipment, Hydro-power Units",
    "2267007000":
        "Mobile Sources, LPG, Logging Equipment, All",
    "2267007005":
        "Mobile Sources, LPG, Logging Equipment, Chain Saws > 6 HP",
    "2267007010":
        "Mobile Sources, LPG, Logging Equipment, Shredders > 6 HP",
    "2267007015":
        "Mobile Sources, LPG, Logging Equipment, Forest Eqp - Feller/Bunch/Skidder",
    "2267007022":
        "Mobile Sources, Off-highway Vehicle LPG, Logging Equipment, LPG Logging Equipment",
    "2267009000":
        "Mobile Sources, LPG, Underground Mining Equipment, All",
    "2267009010":
        "Mobile Sources, LPG, Underground Mining Equipment, Other Underground Mining Equipment",
    "2267010000":
        "Mobile Sources, LPG, Industrial Equipment, All",
    "2267010010":
        "Mobile Sources, LPG, Industrial Equipment, Other Oil Field Equipment",
    "2268000000":
        "Mobile Sources, CNG, CNG Equipment except Rail and Marine, All",
    "2268001000":
        "Mobile Sources, CNG, Recreational Equipment, All",
    "2268001010":
        "Mobile Sources, CNG, Recreational Equipment, Motorcycles: Off-road",
    "2268001020":
        "Mobile Sources, CNG, Recreational Equipment, Snowmobiles",
    "2268001030":
        "Mobile Sources, CNG, Recreational Equipment, All Terrain Vehicles",
    "2268001040":
        "Mobile Sources, CNG, Recreational Equipment, Minibikes",
    "2268001050":
        "Mobile Sources, CNG, Recreational Equipment, Golf Carts",
    "2268001060":
        "Mobile Sources, CNG, Recreational Equipment, Specialty Vehicles/Carts",
    "2268002000":
        "Mobile Sources, CNG, Construction and Mining Equipment, All",
    "2268002003":
        "Mobile Sources, CNG, Construction and Mining Equipment, Pavers",
    "2268002006":
        "Mobile Sources, CNG, Construction and Mining Equipment, Tampers/Rammers",
    "2268002009":
        "Mobile Sources, CNG, Construction and Mining Equipment, Plate Compactors",
    "2268002015":
        "Mobile Sources, CNG, Construction and Mining Equipment, Rollers",
    "2268002018":
        "Mobile Sources, CNG, Construction and Mining Equipment, Scrapers",
    "2268002021":
        "Mobile Sources, CNG, Construction and Mining Equipment, Paving Equipment",
    "2268002022":
        "Mobile Sources, Off-highway Vehicle CNG, Construction Equipment, CNG Construction Equipment",
    "2268002024":
        "Mobile Sources, CNG, Construction and Mining Equipment, Surfacing Equipment",
    "2268002027":
        "Mobile Sources, CNG, Construction and Mining Equipment, Signal Boards/Light Plants",
    "2268002030":
        "Mobile Sources, CNG, Construction and Mining Equipment, Trenchers",
    "2268002033":
        "Mobile Sources, CNG, Construction and Mining Equipment, Bore/Drill Rigs",
    "2268002036":
        "Mobile Sources, CNG, Construction and Mining Equipment, Excavators",
    "2268002039":
        "Mobile Sources, CNG, Construction and Mining Equipment, Concrete/Industrial Saws",
    "2268002042":
        "Mobile Sources, CNG, Construction and Mining Equipment, Cement and Mortar Mixers",
    "2268002045":
        "Mobile Sources, CNG, Construction and Mining Equipment, Cranes",
    "2268002048":
        "Mobile Sources, CNG, Construction and Mining Equipment, Graders",
    "2268002051":
        "Mobile Sources, CNG, Construction and Mining Equipment, Off-highway Trucks",
    "2268002054":
        "Mobile Sources, CNG, Construction and Mining Equipment, Crushing/Processing Equipment",
    "2268002057":
        "Mobile Sources, CNG, Construction and Mining Equipment, Rough Terrain Forklifts",
    "2268002060":
        "Mobile Sources, CNG, Construction and Mining Equipment, Rubber Tire Loaders",
    "2268002063":
        "Mobile Sources, CNG, Construction and Mining Equipment, Rubber Tire Tractor/Dozers",
    "2268002066":
        "Mobile Sources, CNG, Construction and Mining Equipment, Tractors/Loaders/Backhoes",
    "2268002069":
        "Mobile Sources, CNG, Construction and Mining Equipment, Crawler Tractor/Dozers",
    "2268002072":
        "Mobile Sources, CNG, Construction and Mining Equipment, Skid Steer Loaders",
    "2268002075":
        "Mobile Sources, CNG, Construction and Mining Equipment, Off-highway Tractors",
    "2268002078":
        "Mobile Sources, CNG, Construction and Mining Equipment, Dumpers/Tenders",
    "2268002081":
        "Mobile Sources, CNG, Construction and Mining Equipment, Other Construction Equipment",
    "2268003000":
        "Mobile Sources, CNG, Industrial Equipment, All",
    "2268003010":
        "Mobile Sources, CNG, Industrial Equipment, Aerial Lifts",
    "2268003020":
        "Mobile Sources, CNG, Industrial Equipment, Forklifts",
    "2268003022":
        "Mobile Sources, Off-highway Vehicle CNG, Industrial Equipment, CNG Industrial Equipment",
    "2268003030":
        "Mobile Sources, CNG, Industrial Equipment, Sweepers/Scrubbers",
    "2268003040":
        "Mobile Sources, CNG, Industrial Equipment, Other General Industrial Equipment",
    "2268003050":
        "Mobile Sources, CNG, Industrial Equipment, Other Material Handling Equipment",
    "2268003060":
        "Mobile Sources, Off-highway Vehicle CNG, Industrial Equipment, CNG AC\Refrigeration",
    "2268003070":
        "Mobile Sources, CNG, Industrial Equipment, Terminal Tractors",
    "2268004000":
        "Mobile Sources, CNG, Lawn and Garden Equipment, All",
    "2268004010":
        "Mobile Sources, CNG, Lawn and Garden Equipment, Lawn Mowers (Residential)",
    "2268004011":
        "Mobile Sources, CNG, Lawn and Garden Equipment, Lawn Mowers (Commercial)",
    "2268004015":
        "Mobile Sources, CNG, Lawn and Garden Equipment, Rotary Tillers < 6 HP (Residential)",
    "2268004016":
        "Mobile Sources, CNG, Lawn and Garden Equipment, Rotary Tillers < 6 HP (Commercial)",
    "2268004020":
        "Mobile Sources, CNG, Lawn and Garden Equipment, Chain Saws < 6 HP (Residential)",
    "2268004021":
        "Mobile Sources, CNG, Lawn and Garden Equipment, Chain Saws < 6 HP (Commercial)",
    "2268004022":
        "Mobile Sources, Off-highway Vehicle CNG, Lawn and Garden Equipment, CNG Mowers, Tractors, Turf Eqt (Commercial)",
    "2268004025":
        "Mobile Sources, CNG, Lawn and Garden Equipment, Trimmers/Edgers/Brush Cutters (Residential)",
    "2268004026":
        "Mobile Sources, CNG, Lawn and Garden Equipment, Trimmers/Edgers/Brush Cutters (Commercial)",
    "2268004030":
        "Mobile Sources, CNG, Lawn and Garden Equipment, Leafblowers/Vacuums (Residential)",
    "2268004031":
        "Mobile Sources, CNG, Lawn and Garden Equipment, Leafblowers/Vacuums (Commercial)",
    "2268004033":
        "Mobile Sources, Off-highway Vehicle CNG, Lawn and Garden Equipment, CNG Lawn & Garden Eqt (Residential)",
    "2268004035":
        "Mobile Sources, CNG, Lawn and Garden Equipment, Snowblowers (Residential)",
    "2268004036":
        "Mobile Sources, CNG, Lawn and Garden Equipment, Snowblowers (Commercial)",
    "2268004040":
        "Mobile Sources, CNG, Lawn and Garden Equipment, Rear Engine Riding Mowers (Residential)",
    "2268004041":
        "Mobile Sources, CNG, Lawn and Garden Equipment, Rear Engine Riding Mowers (Commercial)",
    "2268004044":
        "Mobile Sources, Off-highway Vehicle CNG, Lawn and Garden Equipment, CNG Lawn & Garden Eqt (Commercial)",
    "2268004045":
        "Mobile Sources, CNG, Lawn and Garden Equipment, Front Mowers (Residential)",
    "2268004046":
        "Mobile Sources, CNG, Lawn and Garden Equipment, Front Mowers (Commercial)",
    "2268004050":
        "Mobile Sources, CNG, Lawn and Garden Equipment, Shredders < 6 HP (Residential)",
    "2268004051":
        "Mobile Sources, CNG, Lawn and Garden Equipment, Shredders < 6 HP (Commercial)",
    "2268004055":
        "Mobile Sources, CNG, Lawn and Garden Equipment, Lawn and Garden Tractors (Residential)",
    "2268004056":
        "Mobile Sources, CNG, Lawn and Garden Equipment, Lawn and Garden Tractors (Commercial)",
    "2268004060":
        "Mobile Sources, CNG, Lawn and Garden Equipment, Wood Splitters (Residential)",
    "2268004061":
        "Mobile Sources, CNG, Lawn and Garden Equipment, Wood Splitters (Commercial)",
    "2268004065":
        "Mobile Sources, CNG, Lawn and Garden Equipment, Chippers/Stump Grinders (Residential)",
    "2268004066":
        "Mobile Sources, CNG, Lawn and Garden Equipment, Chippers/Stump Grinders (Commercial)",
    "2268004071":
        "Mobile Sources, CNG, Lawn and Garden Equipment, Turf Equipment (Commercial)",
    "2268004075":
        "Mobile Sources, CNG, Lawn and Garden Equipment, Other Lawn and Garden Equipment (Residential)",
    "2268004076":
        "Mobile Sources, CNG, Lawn and Garden Equipment, Other Lawn and Garden Equipment (Commercial)",
    "2268005000":
        "Mobile Sources, CNG, Agricultural Equipment, All",
    "2268005010":
        "Mobile Sources, CNG, Agricultural Equipment, 2-Wheel Tractors",
    "2268005015":
        "Mobile Sources, CNG, Agricultural Equipment, Agricultural Tractors",
    "2268005020":
        "Mobile Sources, CNG, Agricultural Equipment, Combines",
    "2268005022":
        "Mobile Sources, Off-highway Vehicle CNG, Agricultural Equipment, CNG Agriculture Equipment",
    "2268005025":
        "Mobile Sources, CNG, Agricultural Equipment, Balers",
    "2268005030":
        "Mobile Sources, CNG, Agricultural Equipment, Agricultural Mowers",
    "2268005035":
        "Mobile Sources, CNG, Agricultural Equipment, Sprayers",
    "2268005040":
        "Mobile Sources, CNG, Agricultural Equipment, Tillers > 6 HP",
    "2268005045":
        "Mobile Sources, CNG, Agricultural Equipment, Swathers",
    "2268005050":
        "Mobile Sources, CNG, Agricultural Equipment, Hydro-power Units",
    "2268005055":
        "Mobile Sources, CNG, Agricultural Equipment, Other Agricultural Equipment",
    "2268005060":
        "Mobile Sources, CNG, Agricultural Equipment, Irrigation Sets",
    "2268006000":
        "Mobile Sources, CNG, Commercial Equipment, All",
    "2268006005":
        "Mobile Sources, CNG, Commercial Equipment, Generator Sets",
    "2268006010":
        "Mobile Sources, CNG, Commercial Equipment, Pumps",
    "2268006015":
        "Mobile Sources, CNG, Commercial Equipment, Air Compressors",
    "2268006020":
        "Mobile Sources, CNG, Commercial Equipment, Gas Compressors",
    "2268006022":
        "Mobile Sources, Off-highway Vehicle CNG, Commercial Equipment, CNG Commercial Equipment",
    "2268006025":
        "Mobile Sources, CNG, Commercial Equipment, Welders",
    "2268006030":
        "Mobile Sources, CNG, Commercial Equipment, Pressure Washers",
    "2268006035":
        "Mobile Sources, CNG, Commercial Equipment, Hydro-power Units",
    "2268007000":
        "Mobile Sources, CNG, Logging Equipment, All",
    "2268007005":
        "Mobile Sources, CNG, Logging Equipment, Chain Saws > 6 HP",
    "2268007010":
        "Mobile Sources, CNG, Logging Equipment, Shredders > 6 HP",
    "2268007015":
        "Mobile Sources, CNG, Logging Equipment, Forest Eqp - Feller/Bunch/Skidder",
    "2268007022":
        "Mobile Sources, Off-highway Vehicle CNG, Logging Equipment, CNG Logging Equipment",
    "2268009000":
        "Mobile Sources, CNG, Underground Mining Equipment, All",
    "2268009010":
        "Mobile Sources, CNG, Underground Mining Equipment, Other Underground Mining Equipment",
    "2268010000":
        "Mobile Sources, CNG, Industrial Equipment, All",
    "2268010010":
        "Mobile Sources, Off-highway Vehicle CNG, Industrial Equipment, CNG Other Oil Field Equipment",
    "2270000000":
        "Mobile Sources, Off-highway Vehicle Diesel, Compression Ignition Equipment except Rail and Marine, Total",
    "2270001000":
        "Mobile Sources, Off-highway Vehicle Diesel, Recreational Equipment, Total",
    "2270001010":
        "Mobile Sources, Off-highway Vehicle Diesel, Recreational Equipment, Motorcycles: Off-road",
    "2270001020":
        "Mobile Sources, Off-highway Vehicle Diesel, Recreational Equipment, Snowmobiles",
    "2270001030":
        "Mobile Sources, Off-highway Vehicle Diesel, Recreational Equipment, All Terrain Vehicles",
    "2270001040":
        "Mobile Sources, Off-highway Vehicle Diesel, Recreational Equipment, Minibikes",
    "2270001050":
        "Mobile Sources, Off-highway Vehicle Diesel, Recreational Equipment, Golf Carts",
    "2270001060":
        "Mobile Sources, Off-highway Vehicle Diesel, Recreational Equipment, Specialty Vehicles/Carts",
    "2270002000":
        "Mobile Sources, Off-highway Vehicle Diesel, Construction and Mining Equipment, Total",
    "2270002003":
        "Mobile Sources, Off-highway Vehicle Diesel, Construction and Mining Equipment, Pavers",
    "2270002006":
        "Mobile Sources, Off-highway Vehicle Diesel, Construction and Mining Equipment, Tampers/Rammers",
    "2270002009":
        "Mobile Sources, Off-highway Vehicle Diesel, Construction and Mining Equipment, Plate Compactors",
    "2270002012":
        "Mobile Sources, Off-highway Vehicle Diesel, Construction and Mining Equipment, Concrete Pavers",
    "2270002015":
        "Mobile Sources, Off-highway Vehicle Diesel, Construction and Mining Equipment, Rollers",
    "2270002018":
        "Mobile Sources, Off-highway Vehicle Diesel, Construction and Mining Equipment, Scrapers",
    "2270002021":
        "Mobile Sources, Off-highway Vehicle Diesel, Construction and Mining Equipment, Paving Equipment",
    "2270002022":
        "Mobile Sources, Off-highway Vehicle Diesel, Construction Equipment, Diesel Construction Equipment",
    "2270002024":
        "Mobile Sources, Off-highway Vehicle Diesel, Construction and Mining Equipment, Surfacing Equipment",
    "2270002027":
        "Mobile Sources, Off-highway Vehicle Diesel, Construction and Mining Equipment, Signal Boards/Light Plants",
    "2270002030":
        "Mobile Sources, Off-highway Vehicle Diesel, Construction and Mining Equipment, Trenchers",
    "2270002033":
        "Mobile Sources, Off-highway Vehicle Diesel, Construction and Mining Equipment, Bore/Drill Rigs",
    "2270002036":
        "Mobile Sources, Off-highway Vehicle Diesel, Construction and Mining Equipment, Excavators",
    "2270002039":
        "Mobile Sources, Off-highway Vehicle Diesel, Construction and Mining Equipment, Concrete/Industrial Saws",
    "2270002042":
        "Mobile Sources, Off-highway Vehicle Diesel, Construction and Mining Equipment, Cement and Mortar Mixers",
    "2270002045":
        "Mobile Sources, Off-highway Vehicle Diesel, Construction and Mining Equipment, Cranes",
    "2270002048":
        "Mobile Sources, Off-highway Vehicle Diesel, Construction and Mining Equipment, Graders",
    "2270002051":
        "Mobile Sources, Off-highway Vehicle Diesel, Construction and Mining Equipment, Off-highway Trucks",
    "2270002054":
        "Mobile Sources, Off-highway Vehicle Diesel, Construction and Mining Equipment, Crushing/Processing Equipment",
    "2270002057":
        "Mobile Sources, Off-highway Vehicle Diesel, Construction and Mining Equipment, Rough Terrain Forklifts",
    "2270002060":
        "Mobile Sources, Off-highway Vehicle Diesel, Construction and Mining Equipment, Rubber Tire Loaders",
    "2270002063":
        "Mobile Sources, Off-highway Vehicle Diesel, Construction and Mining Equipment, Rubber Tire Tractor/Dozers",
    "2270002066":
        "Mobile Sources, Off-highway Vehicle Diesel, Construction and Mining Equipment, Tractors/Loaders/Backhoes",
    "2270002069":
        "Mobile Sources, Off-highway Vehicle Diesel, Construction and Mining Equipment, Crawler Tractor/Dozers",
    "2270002072":
        "Mobile Sources, Off-highway Vehicle Diesel, Construction and Mining Equipment, Skid Steer Loaders",
    "2270002075":
        "Mobile Sources, Off-highway Vehicle Diesel, Construction and Mining Equipment, Off-highway Tractors",
    "2270002078":
        "Mobile Sources, Off-highway Vehicle Diesel, Construction and Mining Equipment, Dumpers/Tenders",
    "2270002081":
        "Mobile Sources, Off-highway Vehicle Diesel, Construction and Mining Equipment, Other Construction Equipment",
    "2270003000":
        "Mobile Sources, Off-highway Vehicle Diesel, Industrial Equipment, Total",
    "2270003010":
        "Mobile Sources, Off-highway Vehicle Diesel, Industrial Equipment, Aerial Lifts",
    "2270003020":
        "Mobile Sources, Off-highway Vehicle Diesel, Industrial Equipment, Forklifts",
    "2270003022":
        "Mobile Sources, Off-highway Vehicle Diesel, Industrial Equipment, Diesel Industrial Equipment",
    "2270003030":
        "Mobile Sources, Off-highway Vehicle Diesel, Industrial Equipment, Sweepers/Scrubbers",
    "2270003040":
        "Mobile Sources, Off-highway Vehicle Diesel, Industrial Equipment, Other General Industrial Equipment",
    "2270003050":
        "Mobile Sources, Off-highway Vehicle Diesel, Industrial Equipment, Other Material Handling Equipment",
    "2270003060":
        "Mobile Sources, Off-highway Vehicle Diesel, Industrial Equipment, AC\Refrigeration",
    "2270003070":
        "Mobile Sources, Off-highway Vehicle Diesel, Industrial Equipment, Terminal Tractors",
    "2270004000":
        "Mobile Sources, Off-highway Vehicle Diesel, Lawn and Garden Equipment, All",
    "2270004010":
        "Mobile Sources, Off-highway Vehicle Diesel, Lawn and Garden Equipment, Lawn Mowers (Residential)",
    "2270004011":
        "Mobile Sources, Off-highway Vehicle Diesel, Lawn and Garden Equipment, Lawn Mowers (Commercial)",
    "2270004015":
        "Mobile Sources, Off-highway Vehicle Diesel, Lawn and Garden Equipment, Rotary Tillers < 6 HP (Residential)",
    "2270004016":
        "Mobile Sources, Off-highway Vehicle Diesel, Lawn and Garden Equipment, Rotary Tillers < 6 HP (Commercial)",
    "2270004020":
        "Mobile Sources, Off-highway Vehicle Diesel, Lawn and Garden Equipment, Chain Saws < 6 HP (Residential)",
    "2270004021":
        "Mobile Sources, Off-highway Vehicle Diesel, Lawn and Garden Equipment, Chain Saws < 6 HP (Commercial)",
    "2270004022":
        "Mobile Sources, Off-highway Vehicle Diesel, Lawn and Garden Equipment, Diesel Mowers, Tractors, Turf Eqt (Commercial)",
    "2270004025":
        "Mobile Sources, Off-highway Vehicle Diesel, Lawn and Garden Equipment, Trimmers/Edgers/Brush Cutters (Residential)",
    "2270004026":
        "Mobile Sources, Off-highway Vehicle Diesel, Lawn and Garden Equipment, Trimmers/Edgers/Brush Cutters (Commercial)",
    "2270004030":
        "Mobile Sources, Off-highway Vehicle Diesel, Lawn and Garden Equipment, Leafblowers/Vacuums (Residential)",
    "2270004031":
        "Mobile Sources, Off-highway Vehicle Diesel, Lawn and Garden Equipment, Leafblowers/Vacuums (Commercial)",
    "2270004033":
        "Mobile Sources, Off-highway Vehicle Diesel, Lawn and Garden Equipment, Diesel Lawn & Garden Eqt (Residential)",
    "2270004035":
        "Mobile Sources, Off-highway Vehicle Diesel, Lawn and Garden Equipment, Snowblowers (Residential)",
    "2270004036":
        "Mobile Sources, Off-highway Vehicle Diesel, Lawn and Garden Equipment, Snowblowers (Commercial)",
    "2270004040":
        "Mobile Sources, Off-highway Vehicle Diesel, Lawn and Garden Equipment, Rear Engine Riding Mowers (Residential)",
    "2270004041":
        "Mobile Sources, Off-highway Vehicle Diesel, Lawn and Garden Equipment, Rear Engine Riding Mowers (Commercial)",
    "2270004044":
        "Mobile Sources, Off-highway Vehicle Diesel, Lawn and Garden Equipment, Diesel Lawn & Garden Eqt (Commercial)",
    "2270004045":
        "Mobile Sources, Off-highway Vehicle Diesel, Lawn and Garden Equipment, Front Mowers (Residential)",
    "2270004046":
        "Mobile Sources, Off-highway Vehicle Diesel, Lawn and Garden Equipment, Front Mowers (Commercial)",
    "2270004050":
        "Mobile Sources, Off-highway Vehicle Diesel, Lawn and Garden Equipment, Shredders < 6 HP (Residential)",
    "2270004051":
        "Mobile Sources, Off-highway Vehicle Diesel, Lawn and Garden Equipment, Shredders < 6 HP (Commercial)",
    "2270004055":
        "Mobile Sources, Off-highway Vehicle Diesel, Lawn and Garden Equipment, Lawn and Garden Tractors (Residential)",
    "2270004056":
        "Mobile Sources, Off-highway Vehicle Diesel, Lawn and Garden Equipment, Lawn and Garden Tractors (Commercial)",
    "2270004060":
        "Mobile Sources, Off-highway Vehicle Diesel, Lawn and Garden Equipment, Wood Splitters (Residential)",
    "2270004061":
        "Mobile Sources, Off-highway Vehicle Diesel, Lawn and Garden Equipment, Wood Splitters (Commercial)",
    "2270004065":
        "Mobile Sources, Off-highway Vehicle Diesel, Lawn and Garden Equipment, Chippers/Stump Grinders (Residential)",
    "2270004066":
        "Mobile Sources, Off-highway Vehicle Diesel, Lawn and Garden Equipment, Chippers/Stump Grinders (Commercial)",
    "2270004070":
        "Mobile Sources, Off-highway Vehicle Diesel, Lawn and Garden Equipment, Commercial Turf Equipment",
    "2270004071":
        "Mobile Sources, Off-highway Vehicle Diesel, Lawn and Garden Equipment, Turf Equipment (Commercial)",
    "2270004075":
        "Mobile Sources, Off-highway Vehicle Diesel, Lawn and Garden Equipment, Other Lawn and Garden Equipment (Residential)",
    "2270004076":
        "Mobile Sources, Off-highway Vehicle Diesel, Lawn and Garden Equipment, Other Lawn and Garden Equipment (Commercial)",
    "2270005000":
        "Mobile Sources, Off-highway Vehicle Diesel, Agricultural Equipment, Total",
    "2270005010":
        "Mobile Sources, Off-highway Vehicle Diesel, Agricultural Equipment, 2-Wheel Tractors",
    "2270005015":
        "Mobile Sources, Off-highway Vehicle Diesel, Agricultural Equipment, Agricultural Tractors",
    "2270005020":
        "Mobile Sources, Off-highway Vehicle Diesel, Agricultural Equipment, Combines",
    "2270005022":
        "Mobile Sources, Off-highway Vehicle Diesel, Agricultural Equipment, Diesel Agriculture Equipment",
    "2270005025":
        "Mobile Sources, Off-highway Vehicle Diesel, Agricultural Equipment, Balers",
    "2270005030":
        "Mobile Sources, Off-highway Vehicle Diesel, Agricultural Equipment, Agricultural Mowers",
    "2270005035":
        "Mobile Sources, Off-highway Vehicle Diesel, Agricultural Equipment, Sprayers",
    "2270005040":
        "Mobile Sources, Off-highway Vehicle Diesel, Agricultural Equipment, Tillers > 6 HP",
    "2270005045":
        "Mobile Sources, Off-highway Vehicle Diesel, Agricultural Equipment, Swathers",
    "2270005050":
        "Mobile Sources, Off-highway Vehicle Diesel, Agricultural Equipment, Hydro-power Units",
    "2270005055":
        "Mobile Sources, Off-highway Vehicle Diesel, Agricultural Equipment, Other Agricultural Equipment",
    "2270005060":
        "Mobile Sources, Off-highway Vehicle Diesel, Agricultural Equipment, Irrigation Sets",
    "2270006000":
        "Mobile Sources, Off-highway Vehicle Diesel, Commercial Equipment, Total",
    "2270006005":
        "Mobile Sources, Off-highway Vehicle Diesel, Commercial Equipment, Generator Sets",
    "2270006010":
        "Mobile Sources, Off-highway Vehicle Diesel, Commercial Equipment, Pumps",
    "2270006015":
        "Mobile Sources, Off-highway Vehicle Diesel, Commercial Equipment, Air Compressors",
    "2270006020":
        "Mobile Sources, Off-highway Vehicle Diesel, Commercial Equipment, Gas Compressors",
    "2270006022":
        "Mobile Sources, Off-highway Vehicle Diesel, Commercial Equipment, Diesel Commercial Equipment",
    "2270006025":
        "Mobile Sources, Off-highway Vehicle Diesel, Commercial Equipment, Welders",
    "2270006030":
        "Mobile Sources, Off-highway Vehicle Diesel, Commercial Equipment, Pressure Washers",
    "2270006035":
        "Mobile Sources, Off-highway Vehicle Diesel, Commercial Equipment, Hydro-power Units",
    "2270007000":
        "Mobile Sources, Off-highway Vehicle Diesel, Logging Equipment, Total",
    "2270007005":
        "Mobile Sources, Off-highway Vehicle Diesel, Logging Equipment, Chain Saws > 6 HP",
    "2270007010":
        "Mobile Sources, Off-highway Vehicle Diesel, Logging Equipment, Shredders > 6 HP",
    "2270007015":
        "Mobile Sources, Off-highway Vehicle Diesel, Logging Equipment, Forest Eqp - Feller/Bunch/Skidder",
    "2270007020":
        "Mobile Sources, Off-highway Vehicle Diesel, Logging Equipment, Fellers/Bunchers",
    "2270007022":
        "Mobile Sources, Off-highway Vehicle Diesel, Logging Equipment, Diesel Logging Equipment",
    "2270008010":
        "Mobile Sources, Off-highway Vehicle Diesel, Airport Ground Support Equipment, Terminal Tractors",
    "2270009000":
        "Mobile Sources, Off-highway Vehicle Diesel, Underground Mining Equipment, All",
    "2270009010":
        "Mobile Sources, Off-highway Vehicle Diesel, Underground Mining Equipment, Other Underground Mining Equipment",
    "2270010000":
        "Mobile Sources, Off-highway Vehicle Diesel, Industrial Equipment, All",
    "2270010010":
        "Mobile Sources, Off-highway Vehicle Diesel, Industrial Equipment, Other Oil Field Equipment",
    "2275001001":
        "Mobile Sources, Aircraft, Military Aircraft, unknown",
    "2275020001":
        "Mobile Sources, Aircraft, Commercial Aircraft, unknown",
    "2275020021":
        "Mobile Sources, Aircraft, Commercial Aircraft, unknown",
    "2275050001":
        "Mobile Sources, Aircraft, General Aviation, unknown",
    "2275085000":
        "Mobile Sources, Aircraft, Unpaved Airstrips, Total",
    "2275087000":
        "Mobile Sources, Aircraft, In-flight (non-Landing-Takeoff cycle), Total",
    "2275900000":
        "Mobile Sources, Aircraft, Refueling: All Fuels, All Processes (Use 25-01-080-xxx)",
    "2275900101":
        "Mobile Sources, Aircraft, Refueling: All Fuels, Displacement Loss/Uncontrolled",
    "2275900102":
        "Mobile Sources, Aircraft, Refueling: All Fuels, Displacement Loss/Controlled",
    "2275900103":
        "Mobile Sources, Aircraft, Refueling: All Fuels, Spillage",
    "2275900201":
        "Mobile Sources, Aircraft, Refueling: All Fuels, Underground Tank: Total",
    "2275900202":
        "Mobile Sources, Aircraft, Refueling: All Fuels, Underground Tank: Breathing and Emptying",
    "2280000000":
        "Mobile Sources, Marine Vessels, Commercial, All Fuels, Total, All Vessel Types",
    "2280001000":
        "Mobile Sources, Marine Vessels, Commercial, Coal, Total, All Vessel Types",
    "2280001010":
        "Mobile Sources, Marine Vessels, Commercial, Coal, Ocean-going Vessels",
    "2280001020":
        "Mobile Sources, Marine Vessels, Commercial, Coal, Harbor Vessels",
    "2280001030":
        "Mobile Sources, Marine Vessels, Commercial, Coal, Fishing Vessels",
    "2280001040":
        "Mobile Sources, Marine Vessels, Commercial, Coal, Military Vessels",
    "2280002000":
        "Mobile Sources, Marine Vessels, Commercial, Diesel, Total, All Vessel Types",
    "2280002010":
        "Mobile Sources, Marine Vessels, Commercial, Diesel, Ocean-going Vessels",
    "2280002020":
        "Mobile Sources, Marine Vessels, Commercial, Diesel, Harbor Vessels",
    "2280002030":
        "Mobile Sources, Marine Vessels, Commercial, Diesel, Fishing Vessels",
    "2280002040":
        "Mobile Sources, Marine Vessels, Commercial, Diesel, Military Vessels",
    "2280002100":
        "Mobile Sources, Marine Vessels, Commercial, Diesel, Port emissions",
    "2280002101":
        "Mobile Sources, Marine Vessels, Commercial, Diesel, C1C2 Port emissions: Main Engine",
    "2280002102":
        "Mobile Sources, Marine Vessels, Commercial, Diesel, C1C2 Port emissions: Auxiliary Engine",
    "2280002103":
        "Mobile Sources, Marine Vessels, Commercial, Diesel, C3 Port emissions: Main Engine",
    "2280002104":
        "Mobile Sources, Marine Vessels, Commercial, Diesel, C3 Port emissions: Auxiliary Engine",
    "2280002200":
        "Mobile Sources, Marine Vessels, Commercial, Diesel, Underway emissions",
    "2280002201":
        "Mobile Sources, Marine Vessels, Commercial, Diesel, C1C2 Underway emissions: Main Engine",
    "2280002202":
        "Mobile Sources, Marine Vessels, Commercial, Diesel, C1C2 Underway emissions: Auxiliary Engine",
    "2280002203":
        "Mobile Sources, Marine Vessels, Commercial, Diesel, C3 Underway emissions: Main Engine",
    "2280002204":
        "Mobile Sources, Marine Vessels, Commercial, Diesel, C3 Underway emissions: Auxiliary Engine",
    "2280003000":
        "Mobile Sources, Marine Vessels, Commercial, Residual, Total, All Vessel Types",
    "2280003010":
        "Mobile Sources, Marine Vessels, Commercial, Residual, Ocean-going Vessels",
    "2280003020":
        "Mobile Sources, Marine Vessels, Commercial, Residual, Harbor Vessels",
    "2280003030":
        "Mobile Sources, Marine Vessels, Commercial, Residual, Fishing Vessels",
    "2280003040":
        "Mobile Sources, Marine Vessels, Commercial, Residual, Military Vessels",
    "2280003100":
        "Mobile Sources, Marine Vessels, Commercial, Residual, Port emissions",
    "2280003103":
        "Mobile Sources, Marine Vessels, Commercial, Residual, C3 Port emissions: Main Engine",
    "2280003104":
        "Mobile Sources, Marine Vessels, Commercial, Residual, C3 Port emissions: Auxiliary Engine",
    "2280003200":
        "Mobile Sources, Marine Vessels, Commercial, Residual, Underway emissions",
    "2280003203":
        "Mobile Sources, Marine Vessels, Commercial, Residual, C3 Underway emissions: Main Engine",
    "2280003204":
        "Mobile Sources, Marine Vessels, Commercial, Residual, C3 Underway emissions: Auxiliary Engine",
    "2280004000":
        "Mobile Sources, Marine Vessels, Commercial, Gasoline, Total, All Vessel Types",
    "2280004010":
        "Mobile Sources, Marine Vessels, Commercial, Gasoline, Ocean-going Vessels",
    "2280004020":
        "Mobile Sources, Marine Vessels, Commercial, Gasoline, Harbor Vessels",
    "2280004030":
        "Mobile Sources, Marine Vessels, Commercial, Gasoline, Fishing Vessels",
    "2280004040":
        "Mobile Sources, Marine Vessels, Commercial, Gasoline, Military Vessels",
    "2282000000":
        "Mobile Sources, Pleasure Craft, All Fuels, Total, All Vessel Types",
    "2282005000":
        "Mobile Sources, Pleasure Craft, Gasoline 2-Stroke, Total",
    "2282005005":
        "Mobile Sources, Pleasure Craft, Gasoline 2-Stroke, Inboard",
    "2282005010":
        "Mobile Sources, Pleasure Craft, Gasoline 2-Stroke, Outboard",
    "2282005015":
        "Mobile Sources, Pleasure Craft, Gasoline 2-Stroke, Personal Water Craft",
    "2282005020":
        "Mobile Sources, Pleasure Craft, Gasoline 2-Stroke, Sailboat Auxiliary Inboard",
    "2282005022":
        "Mobile Sources, Pleasure Craft, Gasoline, 2-Stroke Pleasure Craft",
    "2282005025":
        "Mobile Sources, Pleasure Craft, Gasoline 2-Stroke, Sailboat Auxiliary Outboard",
    "2282010000":
        "Mobile Sources, Pleasure Craft, Gasoline 4-Stroke, Total",
    "2282010005":
        "Mobile Sources, Pleasure Craft, Gasoline 4-Stroke, Inboard/Sterndrive",
    "2282010010":
        "Mobile Sources, Pleasure Craft, Gasoline 4-Stroke, Outboard",
    "2282010015":
        "Mobile Sources, Pleasure Craft, Gasoline 4-Stroke, Sterndrive",
    "2282010020":
        "Mobile Sources, Pleasure Craft, Gasoline 4-Stroke, Sailboat Auxiliary Inboard",
    "2282010025":
        "Mobile Sources, Pleasure Craft, Gasoline 4-Stroke, Sailboat Auxiliary Outboard",
    "2282020000":
        "Mobile Sources, Pleasure Craft, Diesel, Total",
    "2282020005":
        "Mobile Sources, Pleasure Craft, Diesel, Inboard/Sterndrive",
    "2282020010":
        "Mobile Sources, Pleasure Craft, Diesel, Outboard",
    "2282020015":
        "Mobile Sources, Pleasure Craft, Diesel, Sterndrive",
    "2282020020":
        "Mobile Sources, Pleasure Craft, Diesel, Sailboat Auxiliary Inboard",
    "2282020022":
        "Mobile Sources, Pleasure Craft, Diesel, Diesel Pleasure Craft",
    "2282020025":
        "Mobile Sources, Pleasure Craft, Diesel, Sailboat Auxiliary Outboard",
    "2283000000":
        "Mobile Sources, Marine Vessels, Military, unknown, unknown",
    "2283001000":
        "Mobile Sources, Marine Vessels, Military, unknown, unknown",
    "2283001010":
        "Mobile Sources, Marine Vessels, Military, unknown, unknown",
    "2283001020":
        "Mobile Sources, Marine Vessels, Military, unknown, unknown",
    "2283002000":
        "Mobile Sources, Marine Vessels, Military, Diesel, Total, All Vessel Types (incl in 22-80-002-X00)",
    "2283002010":
        "Mobile Sources, Marine Vessels, Military, unknown, unknown",
    "2283002020":
        "Mobile Sources, Marine Vessels, Military, unknown, unknown",
    "2283003000":
        "Mobile Sources, Marine Vessels, Military, unknown, unknown",
    "2283003010":
        "Mobile Sources, Marine Vessels, Military, unknown, unknown",
    "2283003020":
        "Mobile Sources, Marine Vessels, Military, unknown, unknown",
    "2283004000":
        "Mobile Sources, Marine Vessels, Military, unknown, unknown",
    "2283004010":
        "Mobile Sources, Marine Vessels, Military, unknown, unknown",
    "2283004020":
        "Mobile Sources, Marine Vessels, Military, unknown, unknown",
    "2285000000":
        "Mobile Sources, Railroad Equipment, All Fuels, Total",
    "2285002000":
        "Mobile Sources, Railroad Equipment, Diesel, Total",
    "2285002005":
        "Mobile Sources, Railroad Equipment, Diesel, Line Haul Locomotives (use subdivisions by class/operation)",
    "2285002006":
        "Mobile Sources, Railroad Equipment, Diesel, Line Haul Locomotives: Class I Operations",
    "2285002007":
        "Mobile Sources, Railroad Equipment, Diesel, Line Haul Locomotives: Class II / III Operations",
    "2285002008":
        "Mobile Sources, Railroad Equipment, Diesel, Line Haul Locomotives: Passenger Trains (Amtrak)",
    "2285002009":
        "Mobile Sources, Railroad Equipment, Diesel, Line Haul Locomotives: Commuter Lines",
    "2285002010":
        "Mobile Sources, Railroad Equipment, Diesel, Yard Locomotives",
    "2285002015":
        "Mobile Sources, Railroad Equipment, Diesel, Railway Maintenance",
    "2285003015":
        "Mobile Sources, Railroad Equipment, Gasoline, 2-Stroke, Railway Maintenance",
    "2285004015":
        "Mobile Sources, Railroad Equipment, Gasoline, 4-Stroke, Railway Maintenance",
    "2285006015":
        "Mobile Sources, Railroad Equipment, LPG, Railway Maintenance",
    "2285008015":
        "Mobile Sources, Railroad Equipment, CNG, Railway Maintenance",
    "2294000000":
        "Mobile Sources, Paved Roads, All Paved Roads, Total: Fugitives",
    "2294000001":
        "Mobile Sources, Paved Roads, All Paved Roads, Total: Average Conditions - Fugitives",
    "2294000002":
        "Mobile Sources, Paved Roads, All Paved Roads, Total: Sanding/Salting - Fugitives",
    "2294000110":
        "Mobile Sources, Paved Roads, unknown, unknown",
    "2294000130":
        "Mobile Sources, Paved Roads, unknown, unknown",
    "2294000150":
        "Mobile Sources, Paved Roads, unknown, unknown",
    "2294000170":
        "Mobile Sources, Paved Roads, unknown, unknown",
    "2294000190":
        "Mobile Sources, Paved Roads, unknown, unknown",
    "2294000210":
        "Mobile Sources, Paved Roads, unknown, unknown",
    "2294000230":
        "Mobile Sources, Paved Roads, unknown, unknown",
    "2294000250":
        "Mobile Sources, Paved Roads, unknown, unknown",
    "2294000270":
        "Mobile Sources, Paved Roads, unknown, unknown",
    "2294000290":
        "Mobile Sources, Paved Roads, unknown, unknown",
    "2294000310":
        "Mobile Sources, Paved Roads, unknown, unknown",
    "2294000330":
        "Mobile Sources, Paved Roads, unknown, unknown",
    "2294005000":
        "Mobile Sources, Paved Roads, Interstate/Arterial, Total: Fugitives",
    "2294005001":
        "Mobile Sources, Paved Roads, Interstate/Arterial, Total: Average Conditions - Fugitives",
    "2294005002":
        "Mobile Sources, Paved Roads, Interstate/Arterial, Total: Sanding/Salting - Fugitives",
    "2294010000":
        "Mobile Sources, Paved Roads, All Other Public Paved Roads, Total: Fugitives",
    "2294010001":
        "Mobile Sources, Paved Roads, All Other Public Paved Roads, Total: Average Conditions - Fugitives",
    "2294010002":
        "Mobile Sources, Paved Roads, All Other Public Paved Roads, Total: Sanding/Salting - Fugitives",
    "2294015000":
        "Mobile Sources, Paved Roads, Industrial Roads, Total: Fugitives",
    "2294015001":
        "Mobile Sources, Paved Roads, Industrial Roads, Total: Average Conditions - Fugitives",
    "2294015002":
        "Mobile Sources, Paved Roads, Industrial Roads, Total: Sanding/Salting - Fugitives",
    "2296000000":
        "Mobile Sources, Unpaved Roads, All Unpaved Roads, Total: Fugitives",
    "2296000110":
        "Mobile Sources, Unpaved Roads, unknown, unknown",
    "2296000130":
        "Mobile Sources, Unpaved Roads, unknown, unknown",
    "2296000150":
        "Mobile Sources, Unpaved Roads, unknown, unknown",
    "2296000170":
        "Mobile Sources, Unpaved Roads, unknown, unknown",
    "2296000190":
        "Mobile Sources, Unpaved Roads, unknown, unknown",
    "2296000210":
        "Mobile Sources, Unpaved Roads, unknown, unknown",
    "2296000230":
        "Mobile Sources, Unpaved Roads, unknown, unknown",
    "2296000250":
        "Mobile Sources, Unpaved Roads, unknown, unknown",
    "2296000270":
        "Mobile Sources, Unpaved Roads, unknown, unknown",
    "2296000290":
        "Mobile Sources, Unpaved Roads, unknown, unknown",
    "2296000310":
        "Mobile Sources, Unpaved Roads, unknown, unknown",
    "2296000330":
        "Mobile Sources, Unpaved Roads, unknown, unknown",
    "2296005000":
        "Mobile Sources, Unpaved Roads, Public Unpaved Roads, Total: Fugitives",
    "2296010000":
        "Mobile Sources, Unpaved Roads, Industrial Unpaved Roads, Total: Fugitives",
    "2297000000":
        "Mobile Sources, unknown non-US source, unknown non-US source, unknown non-US source",
    "2701200000":
        "Natural Sources, Biogenic, Vegetation, Total",
    "2701220000":
        "Natural Sources, Biogenic, Vegetation/Agriculture, Total",
    "2401001000":
        "Solvent Utilization, Surface Coating, Architectural Coatings, Total: All Solvent Types",
    "2401001001":
        "Solvent Utilization, Surface Coating, Architectural Coatings, Flat Paints",
    "2401001005":
        "Solvent Utilization, Surface Coating, Architectural Coatings, Nonflat Paints - Low and Medium Gloss",
    "2401001006":
        "Solvent Utilization, Surface Coating, Architectural Coatings, Nonflat Paints - High Gloss",
    "2401001010":
        "Solvent Utilization, Surface Coating, Architectural Coatings, Primers, Sealers, and Undercoaters",
    "2401001011":
        "Solvent Utilization, Surface Coating, Architectural Coatings, Quick Dry - Primers, Sealers, and Undercoaters",
    "2401001015":
        "Solvent Utilization, Surface Coating, Architectural Coatings, Stains - Semi-transparent",
    "2401001020":
        "Solvent Utilization, Surface Coating, Architectural Coatings, Quick Dry - Enamels",
    "2401001025":
        "Solvent Utilization, Surface Coating, Architectural Coatings, Lacquers - Clear",
    "2401001030":
        "Solvent Utilization, Surface Coating, Architectural Coatings, Acetone",
    "2401001050":
        "Solvent Utilization, Surface Coating, Architectural Coatings, All Other Architectural Categories",
    "2401001055":
        "Solvent Utilization, Surface Coating, Architectural Coatings, Butyl Acetate",
    "2401001060":
        "Solvent Utilization, Surface Coating, Architectural Coatings, Butyl Alcohols: All Types",
    "2401001065":
        "Solvent Utilization, Surface Coating, Architectural Coatings, n-Butyl Alcohol",
    "2401001070":
        "Solvent Utilization, Surface Coating, Architectural Coatings, Isobutyl Alcohol",
    "2401001125":
        "Solvent Utilization, Surface Coating, Architectural Coatings, Diethylene Glycol Monobutyl Ether",
    "2401001130":
        "Solvent Utilization, Surface Coating, Architectural Coatings, Diethylene Glycol Monoethyl Ether",
    "2401001135":
        "Solvent Utilization, Surface Coating, Architectural Coatings, Diethylene Glycol Monomethyl Ether",
    "2401001170":
        "Solvent Utilization, Surface Coating, Architectural Coatings, Ethyl Acetate",
    "2401001200":
        "Solvent Utilization, Surface Coating, Architectural Coatings, Ethylene Glycol Monoethyl Ether (2-Ethoxyethanol)",
    "2401001210":
        "Solvent Utilization, Surface Coating, Architectural Coatings, Ethylene Glycol Monomethyl Ether (2-Methoxyethanol)",
    "2401001215":
        "Solvent Utilization, Surface Coating, Architectural Coatings, Ethylene Glycol Monobutyl Ether (2-Butoxyethanol)",
    "2401001235":
        "Solvent Utilization, Surface Coating, Architectural Coatings, Glycol Ethers: All Types",
    "2401001250":
        "Solvent Utilization, Surface Coating, Architectural Coatings, Isopropanol",
    "2401001275":
        "Solvent Utilization, Surface Coating, Architectural Coatings, Methyl Ethyl Ketone",
    "2401001285":
        "Solvent Utilization, Surface Coating, Architectural Coatings, Methyl Isobutyl Ketone",
    "2401001370":
        "Solvent Utilization, Surface Coating, Architectural Coatings, Special Naphthas",
    "2401001999":
        "Solvent Utilization, Surface Coating, Architectural Coatings, Solvents: NEC",
    "2401002000":
        "Solvent Utilization, Surface Coating, Architectural Coatings - Solvent-based, Total: All Solvent Types",
    "2401003000":
        "Solvent Utilization, Surface Coating, Architectural Coatings - Water-based, Total: All Solvent Types",
    "2401004000":
        "Solvent Utilization, Surface Coating, Allied Paint Products, Total: All Solvent Types",
    "2401005000":
        "Solvent Utilization, Surface Coating, Auto Refinishing: SIC 7532, Total: All Solvent Types",
    "2401005030":
        "Solvent Utilization, Surface Coating, Auto Refinishing: SIC 7532, Acetone",
    "2401005055":
        "Solvent Utilization, Surface Coating, Auto Refinishing: SIC 7532, Butyl Acetate",
    "2401005060":
        "Solvent Utilization, Surface Coating, Auto Refinishing: SIC 7532, Butyl Alcohols: All Types",
    "2401005065":
        "Solvent Utilization, Surface Coating, Auto Refinishing: SIC 7532, n-Butyl Alcohol",
    "2401005070":
        "Solvent Utilization, Surface Coating, Auto Refinishing: SIC 7532, Isobutyl Alcohol",
    "2401005125":
        "Solvent Utilization, Surface Coating, Auto Refinishing: SIC 7532, Diethylene Glycol Monobutyl Ether",
    "2401005130":
        "Solvent Utilization, Surface Coating, Auto Refinishing: SIC 7532, Diethylene Glycol Monoethyl Ether",
    "2401005135":
        "Solvent Utilization, Surface Coating, Auto Refinishing: SIC 7532, Diethylene Glycol Monomethyl Ether",
    "2401005170":
        "Solvent Utilization, Surface Coating, Auto Refinishing: SIC 7532, Ethyl Acetate",
    "2401005200":
        "Solvent Utilization, Surface Coating, Auto Refinishing: SIC 7532, Ethylene Glycol Monoethyl Ether (2-Ethoxyethanol)",
    "2401005210":
        "Solvent Utilization, Surface Coating, Auto Refinishing: SIC 7532, Ethylene Glycol Monomethyl Ether (2-Methoxyethanol)",
    "2401005215":
        "Solvent Utilization, Surface Coating, Auto Refinishing: SIC 7532, Ethylene Glycol Monobutyl Ether (2-Butoxyethanol)",
    "2401005235":
        "Solvent Utilization, Surface Coating, Auto Refinishing: SIC 7532, Glycol Ethers: All Types",
    "2401005250":
        "Solvent Utilization, Surface Coating, Auto Refinishing: SIC 7532, Isopropanol",
    "2401005275":
        "Solvent Utilization, Surface Coating, Auto Refinishing: SIC 7532, Methyl Ethyl Ketone",
    "2401005285":
        "Solvent Utilization, Surface Coating, Auto Refinishing: SIC 7532, Methyl Isobutyl Ketone",
    "2401005370":
        "Solvent Utilization, Surface Coating, Auto Refinishing: SIC 7532, Special Naphthas",
    "2401005500":
        "Solvent Utilization, Surface Coating, Auto Refinishing: SIC 7532, Surface Preparation Solvents",
    "2401005600":
        "Solvent Utilization, Surface Coating, Auto Refinishing: SIC 7532, Primers",
    "2401005700":
        "Solvent Utilization, Surface Coating, Auto Refinishing: SIC 7532, Top Coats",
    "2401005800":
        "Solvent Utilization, Surface Coating, Auto Refinishing: SIC 7532, Clean-up Solvents",
    "2401005999":
        "Solvent Utilization, Surface Coating, Auto Refinishing: SIC 7532, Solvents: NEC",
    "2401008000":
        "Solvent Utilization, Surface Coating, Traffic Markings, Total: All Solvent Types",
    "2401008030":
        "Solvent Utilization, Surface Coating, Traffic Markings, Acetone",
    "2401008055":
        "Solvent Utilization, Surface Coating, Traffic Markings, Butyl Acetate",
    "2401008060":
        "Solvent Utilization, Surface Coating, Traffic Markings, Butyl Alcohols: All Types",
    "2401008065":
        "Solvent Utilization, Surface Coating, Traffic Markings, n-Butyl Alcohol",
    "2401008070":
        "Solvent Utilization, Surface Coating, Traffic Markings, Isobutyl Alcohol",
    "2401008125":
        "Solvent Utilization, Surface Coating, Traffic Markings, Diethylene Glycol Monobutyl Ether",
    "2401008130":
        "Solvent Utilization, Surface Coating, Traffic Markings, Diethylene Glycol Monoethyl Ether",
    "2401008135":
        "Solvent Utilization, Surface Coating, Traffic Markings, Diethylene Glycol Monomethyl Ether",
    "2401008170":
        "Solvent Utilization, Surface Coating, Traffic Markings, Ethyl Acetate",
    "2401008200":
        "Solvent Utilization, Surface Coating, Traffic Markings, Ethylene Glycol Monoethyl Ether (2-Ethoxyethanol)",
    "2401008210":
        "Solvent Utilization, Surface Coating, Traffic Markings, Ethylene Glycol Monomethyl Ether (2-Methoxyethanol)",
    "2401008215":
        "Solvent Utilization, Surface Coating, Traffic Markings, Ethylene Glycol Monobutyl Ether (2-Butoxyethanol)",
    "2401008235":
        "Solvent Utilization, Surface Coating, Traffic Markings, Glycol Ethers: All Types",
    "2401008250":
        "Solvent Utilization, Surface Coating, Traffic Markings, Isopropanol",
    "2401008275":
        "Solvent Utilization, Surface Coating, Traffic Markings, Methyl Ethyl Ketone",
    "2401008285":
        "Solvent Utilization, Surface Coating, Traffic Markings, Methyl Isobutyl Ketone",
    "2401008370":
        "Solvent Utilization, Surface Coating, Traffic Markings, Special Naphthas",
    "2401008999":
        "Solvent Utilization, Surface Coating, Traffic Markings, Solvents: NEC",
    "2401010000":
        "Solvent Utilization, Surface Coating, Textile Products: SIC 22, Total: All Solvent Types",
    "2401010030":
        "Solvent Utilization, Surface Coating, Textile Products: SIC 22, Acetone",
    "2401010055":
        "Solvent Utilization, Surface Coating, Textile Products: SIC 22, Butyl Acetate",
    "2401010060":
        "Solvent Utilization, Surface Coating, Textile Products: SIC 22, Butyl Alcohols: All Types",
    "2401010065":
        "Solvent Utilization, Surface Coating, Textile Products: SIC 22, n-Butyl Alcohol",
    "2401010070":
        "Solvent Utilization, Surface Coating, Textile Products: SIC 22, Isobutyl Alcohol",
    "2401010125":
        "Solvent Utilization, Surface Coating, Textile Products: SIC 22, Diethylene Glycol Monobutyl Ether",
    "2401010130":
        "Solvent Utilization, Surface Coating, Textile Products: SIC 22, Diethylene Glycol Monoethyl Ether",
    "2401010135":
        "Solvent Utilization, Surface Coating, Textile Products: SIC 22, Diethylene Glycol Monomethyl Ether",
    "2401010170":
        "Solvent Utilization, Surface Coating, Textile Products: SIC 22, Ethyl Acetate",
    "2401010200":
        "Solvent Utilization, Surface Coating, Textile Products: SIC 22, Ethylene Glycol Monoethyl Ether (2-Ethoxyethanol)",
    "2401010210":
        "Solvent Utilization, Surface Coating, Textile Products: SIC 22, Ethylene Glycol Monomethyl Ether (2-Methoxyethanol)",
    "2401010215":
        "Solvent Utilization, Surface Coating, Textile Products: SIC 22, Ethylene Glycol Monobutyl Ether (2-Butoxyethanol)",
    "2401010235":
        "Solvent Utilization, Surface Coating, Textile Products: SIC 22, Glycol Ethers: All Types",
    "2401010250":
        "Solvent Utilization, Surface Coating, Textile Products: SIC 22, Isopropanol",
    "2401010275":
        "Solvent Utilization, Surface Coating, Textile Products: SIC 22, Methyl Ethyl Ketone",
    "2401010285":
        "Solvent Utilization, Surface Coating, Textile Products: SIC 22, Methyl Isobutyl Ketone",
    "2401010370":
        "Solvent Utilization, Surface Coating, Textile Products: SIC 22, Special Naphthas",
    "2401010999":
        "Solvent Utilization, Surface Coating, Textile Products: SIC 22, Solvents: NEC",
    "2401015000":
        "Solvent Utilization, Surface Coating, Factory Finished Wood: SIC 2426 thru 242, Total: All Solvent Types",
    "2401015030":
        "Solvent Utilization, Surface Coating, Factory Finished Wood: SIC 2426 thru 242, Acetone",
    "2401015055":
        "Solvent Utilization, Surface Coating, Factory Finished Wood: SIC 2426 thru 242, Butyl Acetate",
    "2401015060":
        "Solvent Utilization, Surface Coating, Factory Finished Wood: SIC 2426 thru 242, Butyl Alcohols: All Types",
    "2401015065":
        "Solvent Utilization, Surface Coating, Factory Finished Wood: SIC 2426 thru 242, n-Butyl Alcohol",
    "2401015070":
        "Solvent Utilization, Surface Coating, Factory Finished Wood: SIC 2426 thru 242, Isobutyl Alcohol",
    "2401015125":
        "Solvent Utilization, Surface Coating, Factory Finished Wood: SIC 2426 thru 242, Diethylene Glycol Monobutyl Ether",
    "2401015130":
        "Solvent Utilization, Surface Coating, Factory Finished Wood: SIC 2426 thru 242, Diethylene Glycol Monoethyl Ether",
    "2401015135":
        "Solvent Utilization, Surface Coating, Factory Finished Wood: SIC 2426 thru 242, Diethylene Glycol Monomethyl Ether",
    "2401015170":
        "Solvent Utilization, Surface Coating, Factory Finished Wood: SIC 2426 thru 242, Ethyl Acetate",
    "2401015200":
        "Solvent Utilization, Surface Coating, Factory Finished Wood: SIC 2426 thru 242, Ethylene Glycol Monoethyl Ether (2-Ethoxyethanol)",
    "2401015210":
        "Solvent Utilization, Surface Coating, Factory Finished Wood: SIC 2426 thru 242, Ethylene Glycol Monomethyl Ether (2-Methoxyethanol)",
    "2401015215":
        "Solvent Utilization, Surface Coating, Factory Finished Wood: SIC 2426 thru 242, Ethylene Glycol Monobutyl Ether (2-Butoxyethanol)",
    "2401015235":
        "Solvent Utilization, Surface Coating, Factory Finished Wood: SIC 2426 thru 242, Glycol Ethers: All Types",
    "2401015250":
        "Solvent Utilization, Surface Coating, Factory Finished Wood: SIC 2426 thru 242, Isopropanol",
    "2401015275":
        "Solvent Utilization, Surface Coating, Factory Finished Wood: SIC 2426 thru 242, Methyl Ethyl Ketone",
    "2401015285":
        "Solvent Utilization, Surface Coating, Factory Finished Wood: SIC 2426 thru 242, Methyl Isobutyl Ketone",
    "2401015370":
        "Solvent Utilization, Surface Coating, Factory Finished Wood: SIC 2426 thru 242, Special Naphthas",
    "2401015999":
        "Solvent Utilization, Surface Coating, Factory Finished Wood: SIC 2426 thru 242, Solvents: NEC",
    "2401020000":
        "Solvent Utilization, Surface Coating, Wood Furniture: SIC 25, Total: All Solvent Types",
    "2401020030":
        "Solvent Utilization, Surface Coating, Wood Furniture: SIC 25, Acetone",
    "2401020055":
        "Solvent Utilization, Surface Coating, Wood Furniture: SIC 25, Butyl Acetate",
    "2401020060":
        "Solvent Utilization, Surface Coating, Wood Furniture: SIC 25, Butyl Alcohols: All Types",
    "2401020065":
        "Solvent Utilization, Surface Coating, Wood Furniture: SIC 25, n-Butyl Alcohol",
    "2401020070":
        "Solvent Utilization, Surface Coating, Wood Furniture: SIC 25, Isobutyl Alcohol",
    "2401020125":
        "Solvent Utilization, Surface Coating, Wood Furniture: SIC 25, Diethylene Glycol Monobutyl Ether",
    "2401020130":
        "Solvent Utilization, Surface Coating, Wood Furniture: SIC 25, Diethylene Glycol Monoethyl Ether",
    "2401020135":
        "Solvent Utilization, Surface Coating, Wood Furniture: SIC 25, Diethylene Glycol Monomethyl Ether",
    "2401020170":
        "Solvent Utilization, Surface Coating, Wood Furniture: SIC 25, Ethyl Acetate",
    "2401020200":
        "Solvent Utilization, Surface Coating, Wood Furniture: SIC 25, Ethylene Glycol Monoethyl Ether (2-Ethoxyethanol)",
    "2401020210":
        "Solvent Utilization, Surface Coating, Wood Furniture: SIC 25, Ethylene Glycol Monomethyl Ether (2-Methoxyethanol)",
    "2401020215":
        "Solvent Utilization, Surface Coating, Wood Furniture: SIC 25, Ethylene Glycol Monobutyl Ether (2-Butoxyethanol)",
    "2401020235":
        "Solvent Utilization, Surface Coating, Wood Furniture: SIC 25, Glycol Ethers: All Types",
    "2401020250":
        "Solvent Utilization, Surface Coating, Wood Furniture: SIC 25, Isopropanol",
    "2401020275":
        "Solvent Utilization, Surface Coating, Wood Furniture: SIC 25, Methyl Ethyl Ketone",
    "2401020285":
        "Solvent Utilization, Surface Coating, Wood Furniture: SIC 25, Methyl Isobutyl Ketone",
    "2401020370":
        "Solvent Utilization, Surface Coating, Wood Furniture: SIC 25, Special Naphthas",
    "2401020999":
        "Solvent Utilization, Surface Coating, Wood Furniture: SIC 25, Solvents: NEC",
    "2401025000":
        "Solvent Utilization, Surface Coating, Metal Furniture: SIC 25, Total: All Solvent Types",
    "2401025030":
        "Solvent Utilization, Surface Coating, Metal Furniture: SIC 25, Acetone",
    "2401025055":
        "Solvent Utilization, Surface Coating, Metal Furniture: SIC 25, Butyl Acetate",
    "2401025060":
        "Solvent Utilization, Surface Coating, Metal Furniture: SIC 25, Butyl Alcohols: All Types",
    "2401025065":
        "Solvent Utilization, Surface Coating, Metal Furniture: SIC 25, n-Butyl Alcohol",
    "2401025070":
        "Solvent Utilization, Surface Coating, Metal Furniture: SIC 25, Isobutyl Alcohol",
    "2401025125":
        "Solvent Utilization, Surface Coating, Metal Furniture: SIC 25, Diethylene Glycol Monobutyl Ether",
    "2401025130":
        "Solvent Utilization, Surface Coating, Metal Furniture: SIC 25, Diethylene Glycol Monoethyl Ether",
    "2401025135":
        "Solvent Utilization, Surface Coating, Metal Furniture: SIC 25, Diethylene Glycol Monomethyl Ether",
    "2401025170":
        "Solvent Utilization, Surface Coating, Metal Furniture: SIC 25, Ethyl Acetate",
    "2401025200":
        "Solvent Utilization, Surface Coating, Metal Furniture: SIC 25, Ethylene Glycol Monoethyl Ether (2-Ethoxyethanol)",
    "2401025210":
        "Solvent Utilization, Surface Coating, Metal Furniture: SIC 25, Ethylene Glycol Monomethyl Ether (2-Methoxyethanol)",
    "2401025215":
        "Solvent Utilization, Surface Coating, Metal Furniture: SIC 25, Ethylene Glycol Monobutyl Ether (2-Butoxyethanol)",
    "2401025235":
        "Solvent Utilization, Surface Coating, Metal Furniture: SIC 25, Glycol Ethers: All Types",
    "2401025250":
        "Solvent Utilization, Surface Coating, Metal Furniture: SIC 25, Isopropanol",
    "2401025275":
        "Solvent Utilization, Surface Coating, Metal Furniture: SIC 25, Methyl Ethyl Ketone",
    "2401025285":
        "Solvent Utilization, Surface Coating, Metal Furniture: SIC 25, Methyl Isobutyl Ketone",
    "2401025370":
        "Solvent Utilization, Surface Coating, Metal Furniture: SIC 25, Special Naphthas",
    "2401025999":
        "Solvent Utilization, Surface Coating, Metal Furniture: SIC 25, Solvents: NEC",
    "2401030000":
        "Solvent Utilization, Surface Coating, Paper: SIC 26, Total: All Solvent Types",
    "2401030030":
        "Solvent Utilization, Surface Coating, Paper: SIC 26, Acetone",
    "2401030055":
        "Solvent Utilization, Surface Coating, Paper: SIC 26, Butyl Acetate",
    "2401030060":
        "Solvent Utilization, Surface Coating, Paper: SIC 26, Butyl Alcohols: All Types",
    "2401030065":
        "Solvent Utilization, Surface Coating, Paper: SIC 26, n-Butyl Alcohol",
    "2401030070":
        "Solvent Utilization, Surface Coating, Paper: SIC 26, Isobutyl Alcohol",
    "2401030125":
        "Solvent Utilization, Surface Coating, Paper: SIC 26, Diethylene Glycol Monobutyl Ether",
    "2401030130":
        "Solvent Utilization, Surface Coating, Paper: SIC 26, Diethylene Glycol Monoethyl Ether",
    "2401030135":
        "Solvent Utilization, Surface Coating, Paper: SIC 26, Diethylene Glycol Monomethyl Ether",
    "2401030170":
        "Solvent Utilization, Surface Coating, Paper: SIC 26, Ethyl Acetate",
    "2401030200":
        "Solvent Utilization, Surface Coating, Paper: SIC 26, Ethylene Glycol Monoethyl Ether (2-Ethoxyethanol)",
    "2401030210":
        "Solvent Utilization, Surface Coating, Paper: SIC 26, Ethylene Glycol Monomethyl Ether (2-Methoxyethanol)",
    "2401030215":
        "Solvent Utilization, Surface Coating, Paper: SIC 26, Ethylene Glycol Monobutyl Ether (2-Butoxyethanol)",
    "2401030235":
        "Solvent Utilization, Surface Coating, Paper: SIC 26, Glycol Ethers: All Types",
    "2401030250":
        "Solvent Utilization, Surface Coating, Paper: SIC 26, Isopropanol",
    "2401030275":
        "Solvent Utilization, Surface Coating, Paper: SIC 26, Methyl Ethyl Ketone",
    "2401030285":
        "Solvent Utilization, Surface Coating, Paper: SIC 26, Methyl Isobutyl Ketone",
    "2401030370":
        "Solvent Utilization, Surface Coating, Paper: SIC 26, Special Naphthas",
    "2401030999":
        "Solvent Utilization, Surface Coating, Paper: SIC 26, Solvents: NEC",
    "2401035000":
        "Solvent Utilization, Surface Coating, Plastic Products: SIC 308, Total: All Solvent Types",
    "2401035030":
        "Solvent Utilization, Surface Coating, Plastic Products: SIC 308, Acetone",
    "2401035055":
        "Solvent Utilization, Surface Coating, Plastic Products: SIC 308, Butyl Acetate",
    "2401035060":
        "Solvent Utilization, Surface Coating, Plastic Products: SIC 308, Butyl Alcohols: All Types",
    "2401035065":
        "Solvent Utilization, Surface Coating, Plastic Products: SIC 308, n-Butyl Alcohol",
    "2401035070":
        "Solvent Utilization, Surface Coating, Plastic Products: SIC 308, Isobutyl Alcohol",
    "2401035125":
        "Solvent Utilization, Surface Coating, Plastic Products: SIC 308, Diethylene Glycol Monobutyl Ether",
    "2401035130":
        "Solvent Utilization, Surface Coating, Plastic Products: SIC 308, Diethylene Glycol Monoethyl Ether",
    "2401035135":
        "Solvent Utilization, Surface Coating, Plastic Products: SIC 308, Diethylene Glycol Monomethyl Ether",
    "2401035170":
        "Solvent Utilization, Surface Coating, Plastic Products: SIC 308, Ethyl Acetate",
    "2401035200":
        "Solvent Utilization, Surface Coating, Plastic Products: SIC 308, Ethylene Glycol Monoethyl Ether (2-Ethoxyethanol)",
    "2401035210":
        "Solvent Utilization, Surface Coating, Plastic Products: SIC 308, Ethylene Glycol Monomethyl Ether (2-Methoxyethanol)",
    "2401035215":
        "Solvent Utilization, Surface Coating, Plastic Products: SIC 308, Ethylene Glycol Monobutyl Ether (2-Butoxyethanol)",
    "2401035235":
        "Solvent Utilization, Surface Coating, Plastic Products: SIC 308, Glycol Ethers: All Types",
    "2401035250":
        "Solvent Utilization, Surface Coating, Plastic Products: SIC 308, Isopropanol",
    "2401035275":
        "Solvent Utilization, Surface Coating, Plastic Products: SIC 308, Methyl Ethyl Ketone",
    "2401035285":
        "Solvent Utilization, Surface Coating, Plastic Products: SIC 308, Methyl Isobutyl Ketone",
    "2401035370":
        "Solvent Utilization, Surface Coating, Plastic Products: SIC 308, Special Naphthas",
    "2401035999":
        "Solvent Utilization, Surface Coating, Plastic Products: SIC 308, Solvents: NEC",
    "2401040000":
        "Solvent Utilization, Surface Coating, Metal Cans: SIC 341, Total: All Solvent Types",
    "2401040030":
        "Solvent Utilization, Surface Coating, Metal Cans: SIC 341, Acetone",
    "2401040055":
        "Solvent Utilization, Surface Coating, Metal Cans: SIC 341, Butyl Acetate",
    "2401040060":
        "Solvent Utilization, Surface Coating, Metal Cans: SIC 341, Butyl Alcohols: All Types",
    "2401040065":
        "Solvent Utilization, Surface Coating, Metal Cans: SIC 341, n-Butyl Alcohol",
    "2401040070":
        "Solvent Utilization, Surface Coating, Metal Cans: SIC 341, Isobutyl Alcohol",
    "2401040125":
        "Solvent Utilization, Surface Coating, Metal Cans: SIC 341, Diethylene Glycol Monobutyl Ether",
    "2401040130":
        "Solvent Utilization, Surface Coating, Metal Cans: SIC 341, Diethylene Glycol Monoethyl Ether",
    "2401040135":
        "Solvent Utilization, Surface Coating, Metal Cans: SIC 341, Diethylene Glycol Monomethyl Ether",
    "2401040170":
        "Solvent Utilization, Surface Coating, Metal Cans: SIC 341, Ethyl Acetate",
    "2401040200":
        "Solvent Utilization, Surface Coating, Metal Cans: SIC 341, Ethylene Glycol Monoethyl Ether (2-Ethoxyethanol)",
    "2401040210":
        "Solvent Utilization, Surface Coating, Metal Cans: SIC 341, Ethylene Glycol Monomethyl Ether (2-Methoxyethanol)",
    "2401040215":
        "Solvent Utilization, Surface Coating, Metal Cans: SIC 341, Ethylene Glycol Monobutyl Ether (2-Butoxyethanol)",
    "2401040235":
        "Solvent Utilization, Surface Coating, Metal Cans: SIC 341, Glycol Ethers: All Types",
    "2401040250":
        "Solvent Utilization, Surface Coating, Metal Cans: SIC 341, Isopropanol",
    "2401040275":
        "Solvent Utilization, Surface Coating, Metal Cans: SIC 341, Methyl Ethyl Ketone",
    "2401040285":
        "Solvent Utilization, Surface Coating, Metal Cans: SIC 341, Methyl Isobutyl Ketone",
    "2401040370":
        "Solvent Utilization, Surface Coating, Metal Cans: SIC 341, Special Naphthas",
    "2401040999":
        "Solvent Utilization, Surface Coating, Metal Cans: SIC 341, Solvents: NEC",
    "2401045000":
        "Solvent Utilization, Surface Coating, Metal Coils: SIC 3498, Total: All Solvent Types",
    "2401045030":
        "Solvent Utilization, Surface Coating, Metal Coils: SIC 3498, Acetone",
    "2401045055":
        "Solvent Utilization, Surface Coating, Metal Coils: SIC 3498, Butyl Acetate",
    "2401045060":
        "Solvent Utilization, Surface Coating, Metal Coils: SIC 3498, Butyl Alcohols: All Types",
    "2401045065":
        "Solvent Utilization, Surface Coating, Metal Coils: SIC 3498, n-Butyl Alcohol",
    "2401045070":
        "Solvent Utilization, Surface Coating, Metal Coils: SIC 3498, Isobutyl Alcohol",
    "2401045125":
        "Solvent Utilization, Surface Coating, Metal Coils: SIC 3498, Diethylene Glycol Monobutyl Ether",
    "2401045130":
        "Solvent Utilization, Surface Coating, Metal Coils: SIC 3498, Diethylene Glycol Monoethyl Ether",
    "2401045135":
        "Solvent Utilization, Surface Coating, Metal Coils: SIC 3498, Diethylene Glycol Monomethyl Ether",
    "2401045170":
        "Solvent Utilization, Surface Coating, Metal Coils: SIC 3498, Ethyl Acetate",
    "2401045200":
        "Solvent Utilization, Surface Coating, Metal Coils: SIC 3498, Ethylene Glycol Monoethyl Ether (2-Ethoxyethanol)",
    "2401045210":
        "Solvent Utilization, Surface Coating, Metal Coils: SIC 3498, Ethylene Glycol Monomethyl Ether (2-Methoxyethanol)",
    "2401045215":
        "Solvent Utilization, Surface Coating, Metal Coils: SIC 3498, Ethylene Glycol Monobutyl Ether (2-Butoxyethanol)",
    "2401045235":
        "Solvent Utilization, Surface Coating, Metal Coils: SIC 3498, Glycol Ethers: All Types",
    "2401045250":
        "Solvent Utilization, Surface Coating, Metal Coils: SIC 3498, Isopropanol",
    "2401045275":
        "Solvent Utilization, Surface Coating, Metal Coils: SIC 3498, Methyl Ethyl Ketone",
    "2401045285":
        "Solvent Utilization, Surface Coating, Metal Coils: SIC 3498, Methyl Isobutyl Ketone",
    "2401045370":
        "Solvent Utilization, Surface Coating, Metal Coils: SIC 3498, Special Naphthas",
    "2401045999":
        "Solvent Utilization, Surface Coating, Metal Coils: SIC 3498, Solvents: NEC",
    "2401050000":
        "Solvent Utilization, Surface Coating, Miscellaneous Finished Metals: SIC 34 - (341 + 3498), Total: All Solvent Types",
    "2401050030":
        "Solvent Utilization, Surface Coating, Miscellaneous Finished Metals: SIC 34 - (341 + 3498), Acetone",
    "2401050055":
        "Solvent Utilization, Surface Coating, Miscellaneous Finished Metals: SIC 34 - (341 + 3498), Butyl Acetate",
    "2401050060":
        "Solvent Utilization, Surface Coating, Miscellaneous Finished Metals: SIC 34 - (341 + 3498), Butyl Alcohols: All Types",
    "2401050065":
        "Solvent Utilization, Surface Coating, Miscellaneous Finished Metals: SIC 34 - (341 + 3498), n-Butyl Alcohol",
    "2401050070":
        "Solvent Utilization, Surface Coating, Miscellaneous Finished Metals: SIC 34 - (341 + 3498), Isobutyl Alcohol",
    "2401050125":
        "Solvent Utilization, Surface Coating, Miscellaneous Finished Metals: SIC 34 - (341 + 3498), Diethylene Glycol Monobutyl Ether",
    "2401050130":
        "Solvent Utilization, Surface Coating, Miscellaneous Finished Metals: SIC 34 - (341 + 3498), Diethylene Glycol Monoethyl Ether",
    "2401050135":
        "Solvent Utilization, Surface Coating, Miscellaneous Finished Metals: SIC 34 - (341 + 3498), Diethylene Glycol Monomethyl Ether",
    "2401050170":
        "Solvent Utilization, Surface Coating, Miscellaneous Finished Metals: SIC 34 - (341 + 3498), Ethyl Acetate",
    "2401050200":
        "Solvent Utilization, Surface Coating, Miscellaneous Finished Metals: SIC 34 - (341 + 3498), Ethylene Glycol Monoethyl Ether (2-Ethoxyethanol)",
    "2401050210":
        "Solvent Utilization, Surface Coating, Miscellaneous Finished Metals: SIC 34 - (341 + 3498), Ethylene Glycol Monomethyl Ether (2-Methoxyethanol)",
    "2401050215":
        "Solvent Utilization, Surface Coating, Miscellaneous Finished Metals: SIC 34 - (341 + 3498), Ethylene Glycol Monobutyl Ether (2-Butoxyethanol)",
    "2401050235":
        "Solvent Utilization, Surface Coating, Miscellaneous Finished Metals: SIC 34 - (341 + 3498), Glycol Ethers: All Types",
    "2401050250":
        "Solvent Utilization, Surface Coating, Miscellaneous Finished Metals: SIC 34 - (341 + 3498), Isopropanol",
    "2401050275":
        "Solvent Utilization, Surface Coating, Miscellaneous Finished Metals: SIC 34 - (341 + 3498), Methyl Ethyl Ketone",
    "2401050285":
        "Solvent Utilization, Surface Coating, Miscellaneous Finished Metals: SIC 34 - (341 + 3498), Methyl Isobutyl Ketone",
    "2401050370":
        "Solvent Utilization, Surface Coating, Miscellaneous Finished Metals: SIC 34 - (341 + 3498), Special Naphthas",
    "2401050999":
        "Solvent Utilization, Surface Coating, Miscellaneous Finished Metals: SIC 34 - (341 + 3498), Solvents: NEC",
    "2401055000":
        "Solvent Utilization, Surface Coating, Machinery and Equipment: SIC 35, Total: All Solvent Types",
    "2401055030":
        "Solvent Utilization, Surface Coating, Machinery and Equipment: SIC 35, Acetone",
    "2401055055":
        "Solvent Utilization, Surface Coating, Machinery and Equipment: SIC 35, Butyl Acetate",
    "2401055060":
        "Solvent Utilization, Surface Coating, Machinery and Equipment: SIC 35, Butyl Alcohols: All Types",
    "2401055065":
        "Solvent Utilization, Surface Coating, Machinery and Equipment: SIC 35, n-Butyl Alcohol",
    "2401055070":
        "Solvent Utilization, Surface Coating, Machinery and Equipment: SIC 35, Isobutyl Alcohol",
    "2401055125":
        "Solvent Utilization, Surface Coating, Machinery and Equipment: SIC 35, Diethylene Glycol Monobutyl Ether",
    "2401055130":
        "Solvent Utilization, Surface Coating, Machinery and Equipment: SIC 35, Diethylene Glycol Monoethyl Ether",
    "2401055135":
        "Solvent Utilization, Surface Coating, Machinery and Equipment: SIC 35, Diethylene Glycol Monomethyl Ether",
    "2401055170":
        "Solvent Utilization, Surface Coating, Machinery and Equipment: SIC 35, Ethyl Acetate",
    "2401055200":
        "Solvent Utilization, Surface Coating, Machinery and Equipment: SIC 35, Ethylene Glycol Monoethyl Ether (2-Ethoxyethanol)",
    "2401055210":
        "Solvent Utilization, Surface Coating, Machinery and Equipment: SIC 35, Ethylene Glycol Monomethyl Ether (2-Methoxyethanol)",
    "2401055215":
        "Solvent Utilization, Surface Coating, Machinery and Equipment: SIC 35, Ethylene Glycol Monobutyl Ether (2-Butoxyethanol)",
    "2401055235":
        "Solvent Utilization, Surface Coating, Machinery and Equipment: SIC 35, Glycol Ethers: All Types",
    "2401055250":
        "Solvent Utilization, Surface Coating, Machinery and Equipment: SIC 35, Isopropanol",
    "2401055275":
        "Solvent Utilization, Surface Coating, Machinery and Equipment: SIC 35, Methyl Ethyl Ketone",
    "2401055285":
        "Solvent Utilization, Surface Coating, Machinery and Equipment: SIC 35, Methyl Isobutyl Ketone",
    "2401055370":
        "Solvent Utilization, Surface Coating, Machinery and Equipment: SIC 35, Special Naphthas",
    "2401055999":
        "Solvent Utilization, Surface Coating, Machinery and Equipment: SIC 35, Solvents: NEC",
    "2401060000":
        "Solvent Utilization, Surface Coating, Large Appliances: SIC 363, Total: All Solvent Types",
    "2401060030":
        "Solvent Utilization, Surface Coating, Large Appliances: SIC 363, Acetone",
    "2401060055":
        "Solvent Utilization, Surface Coating, Large Appliances: SIC 363, Butyl Acetate",
    "2401060060":
        "Solvent Utilization, Surface Coating, Large Appliances: SIC 363, Butyl Alcohols: All Types",
    "2401060065":
        "Solvent Utilization, Surface Coating, Large Appliances: SIC 363, n-Butyl Alcohol",
    "2401060070":
        "Solvent Utilization, Surface Coating, Large Appliances: SIC 363, Isobutyl Alcohol",
    "2401060125":
        "Solvent Utilization, Surface Coating, Large Appliances: SIC 363, Diethylene Glycol Monobutyl Ether",
    "2401060130":
        "Solvent Utilization, Surface Coating, Large Appliances: SIC 363, Diethylene Glycol Monoethyl Ether",
    "2401060135":
        "Solvent Utilization, Surface Coating, Large Appliances: SIC 363, Diethylene Glycol Monomethyl Ether",
    "2401060170":
        "Solvent Utilization, Surface Coating, Large Appliances: SIC 363, Ethyl Acetate",
    "2401060200":
        "Solvent Utilization, Surface Coating, Large Appliances: SIC 363, Ethylene Glycol Monoethyl Ether (2-Ethoxyethanol)",
    "2401060210":
        "Solvent Utilization, Surface Coating, Large Appliances: SIC 363, Ethylene Glycol Monomethyl Ether (2-Methoxyethanol)",
    "2401060215":
        "Solvent Utilization, Surface Coating, Large Appliances: SIC 363, Ethylene Glycol Monobutyl Ether (2-Butoxyethanol)",
    "2401060235":
        "Solvent Utilization, Surface Coating, Large Appliances: SIC 363, Glycol Ethers: All Types",
    "2401060250":
        "Solvent Utilization, Surface Coating, Large Appliances: SIC 363, Isopropanol",
    "2401060275":
        "Solvent Utilization, Surface Coating, Large Appliances: SIC 363, Methyl Ethyl Ketone",
    "2401060285":
        "Solvent Utilization, Surface Coating, Large Appliances: SIC 363, Methyl Isobutyl Ketone",
    "2401060370":
        "Solvent Utilization, Surface Coating, Large Appliances: SIC 363, Special Naphthas",
    "2401060999":
        "Solvent Utilization, Surface Coating, Large Appliances: SIC 363, Solvents: NEC",
    "2401065000":
        "Solvent Utilization, Surface Coating, Electronic and Other Electrical: SIC 36 - 363, Total: All Solvent Types",
    "2401065030":
        "Solvent Utilization, Surface Coating, Electronic and Other Electrical: SIC 36 - 363, Acetone",
    "2401065055":
        "Solvent Utilization, Surface Coating, Electronic and Other Electrical: SIC 36 - 363, Butyl Acetate",
    "2401065060":
        "Solvent Utilization, Surface Coating, Electronic and Other Electrical: SIC 36 - 363, Butyl Alcohols: All Types",
    "2401065065":
        "Solvent Utilization, Surface Coating, Electronic and Other Electrical: SIC 36 - 363, n-Butyl Alcohol",
    "2401065070":
        "Solvent Utilization, Surface Coating, Electronic and Other Electrical: SIC 36 - 363, Isobutyl Alcohol",
    "2401065125":
        "Solvent Utilization, Surface Coating, Electronic and Other Electrical: SIC 36 - 363, Diethylene Glycol Monobutyl Ether",
    "2401065130":
        "Solvent Utilization, Surface Coating, Electronic and Other Electrical: SIC 36 - 363, Diethylene Glycol Monoethyl Ether",
    "2401065135":
        "Solvent Utilization, Surface Coating, Electronic and Other Electrical: SIC 36 - 363, Diethylene Glycol Monomethyl Ether",
    "2401065170":
        "Solvent Utilization, Surface Coating, Electronic and Other Electrical: SIC 36 - 363, Ethyl Acetate",
    "2401065200":
        "Solvent Utilization, Surface Coating, Electronic and Other Electrical: SIC 36 - 363, Ethylene Glycol Monoethyl Ether (2-Ethoxyethanol)",
    "2401065210":
        "Solvent Utilization, Surface Coating, Electronic and Other Electrical: SIC 36 - 363, Ethylene Glycol Monomethyl Ether (2-Methoxyethanol)",
    "2401065215":
        "Solvent Utilization, Surface Coating, Electronic and Other Electrical: SIC 36 - 363, Ethylene Glycol Monobutyl Ether (2-Butoxyethanol)",
    "2401065235":
        "Solvent Utilization, Surface Coating, Electronic and Other Electrical: SIC 36 - 363, Glycol Ethers: All Types",
    "2401065250":
        "Solvent Utilization, Surface Coating, Electronic and Other Electrical: SIC 36 - 363, Isopropanol",
    "2401065275":
        "Solvent Utilization, Surface Coating, Electronic and Other Electrical: SIC 36 - 363, Methyl Ethyl Ketone",
    "2401065285":
        "Solvent Utilization, Surface Coating, Electronic and Other Electrical: SIC 36 - 363, Methyl Isobutyl Ketone",
    "2401065370":
        "Solvent Utilization, Surface Coating, Electronic and Other Electrical: SIC 36 - 363, Special Naphthas",
    "2401065999":
        "Solvent Utilization, Surface Coating, Electronic and Other Electrical: SIC 36 - 363, Solvents: NEC",
    "2401070000":
        "Solvent Utilization, Surface Coating, Motor Vehicles: SIC 371, Total: All Solvent Types",
    "2401070030":
        "Solvent Utilization, Surface Coating, Motor Vehicles: SIC 371, Acetone",
    "2401070055":
        "Solvent Utilization, Surface Coating, Motor Vehicles: SIC 371, Butyl Acetate",
    "2401070060":
        "Solvent Utilization, Surface Coating, Motor Vehicles: SIC 371, Butyl Alcohols: All Types",
    "2401070065":
        "Solvent Utilization, Surface Coating, Motor Vehicles: SIC 371, n-Butyl Alcohol",
    "2401070070":
        "Solvent Utilization, Surface Coating, Motor Vehicles: SIC 371, Isobutyl Alcohol",
    "2401070125":
        "Solvent Utilization, Surface Coating, Motor Vehicles: SIC 371, Diethylene Glycol Monobutyl Ether",
    "2401070130":
        "Solvent Utilization, Surface Coating, Motor Vehicles: SIC 371, Diethylene Glycol Monoethyl Ether",
    "2401070135":
        "Solvent Utilization, Surface Coating, Motor Vehicles: SIC 371, Diethylene Glycol Monomethyl Ether",
    "2401070170":
        "Solvent Utilization, Surface Coating, Motor Vehicles: SIC 371, Ethyl Acetate",
    "2401070200":
        "Solvent Utilization, Surface Coating, Motor Vehicles: SIC 371, Ethylene Glycol Monoethyl Ether (2-Ethoxyethanol)",
    "2401070210":
        "Solvent Utilization, Surface Coating, Motor Vehicles: SIC 371, Ethylene Glycol Monomethyl Ether (2-Methoxyethanol)",
    "2401070215":
        "Solvent Utilization, Surface Coating, Motor Vehicles: SIC 371, Ethylene Glycol Monobutyl Ether (2-Butoxyethanol)",
    "2401070235":
        "Solvent Utilization, Surface Coating, Motor Vehicles: SIC 371, Glycol Ethers: All Types",
    "2401070250":
        "Solvent Utilization, Surface Coating, Motor Vehicles: SIC 371, Isopropanol",
    "2401070275":
        "Solvent Utilization, Surface Coating, Motor Vehicles: SIC 371, Methyl Ethyl Ketone",
    "2401070285":
        "Solvent Utilization, Surface Coating, Motor Vehicles: SIC 371, Methyl Isobutyl Ketone",
    "2401070370":
        "Solvent Utilization, Surface Coating, Motor Vehicles: SIC 371, Special Naphthas",
    "2401070999":
        "Solvent Utilization, Surface Coating, Motor Vehicles: SIC 371, Solvents: NEC",
    "2401075000":
        "Solvent Utilization, Surface Coating, Aircraft: SIC 372, Total: All Solvent Types",
    "2401075030":
        "Solvent Utilization, Surface Coating, Aircraft: SIC 372, Acetone",
    "2401075055":
        "Solvent Utilization, Surface Coating, Aircraft: SIC 372, Butyl Acetate",
    "2401075060":
        "Solvent Utilization, Surface Coating, Aircraft: SIC 372, Butyl Alcohols: All Types",
    "2401075065":
        "Solvent Utilization, Surface Coating, Aircraft: SIC 372, n-Butyl Alcohol",
    "2401075070":
        "Solvent Utilization, Surface Coating, Aircraft: SIC 372, Isobutyl Alcohol",
    "2401075125":
        "Solvent Utilization, Surface Coating, Aircraft: SIC 372, Diethylene Glycol Monobutyl Ether",
    "2401075130":
        "Solvent Utilization, Surface Coating, Aircraft: SIC 372, Diethylene Glycol Monoethyl Ether",
    "2401075135":
        "Solvent Utilization, Surface Coating, Aircraft: SIC 372, Diethylene Glycol Monomethyl Ether",
    "2401075170":
        "Solvent Utilization, Surface Coating, Aircraft: SIC 372, Ethyl Acetate",
    "2401075200":
        "Solvent Utilization, Surface Coating, Aircraft: SIC 372, Ethylene Glycol Monoethyl Ether (2-Ethoxyethanol)",
    "2401075210":
        "Solvent Utilization, Surface Coating, Aircraft: SIC 372, Ethylene Glycol Monomethyl Ether (2-Methoxyethanol)",
    "2401075215":
        "Solvent Utilization, Surface Coating, Aircraft: SIC 372, Ethylene Glycol Monobutyl Ether (2-Butoxyethanol)",
    "2401075235":
        "Solvent Utilization, Surface Coating, Aircraft: SIC 372, Glycol Ethers: All Types",
    "2401075250":
        "Solvent Utilization, Surface Coating, Aircraft: SIC 372, Isopropanol",
    "2401075275":
        "Solvent Utilization, Surface Coating, Aircraft: SIC 372, Methyl Ethyl Ketone",
    "2401075285":
        "Solvent Utilization, Surface Coating, Aircraft: SIC 372, Methyl Isobutyl Ketone",
    "2401075370":
        "Solvent Utilization, Surface Coating, Aircraft: SIC 372, Special Naphthas",
    "2401075999":
        "Solvent Utilization, Surface Coating, Aircraft: SIC 372, Solvents: NEC",
    "2401080000":
        "Solvent Utilization, Surface Coating, Marine: SIC 373, Total: All Solvent Types",
    "2401080030":
        "Solvent Utilization, Surface Coating, Marine: SIC 373, Acetone",
    "2401080055":
        "Solvent Utilization, Surface Coating, Marine: SIC 373, Butyl Acetate",
    "2401080060":
        "Solvent Utilization, Surface Coating, Marine: SIC 373, Butyl Alcohols: All Types",
    "2401080065":
        "Solvent Utilization, Surface Coating, Marine: SIC 373, n-Butyl Alcohol",
    "2401080070":
        "Solvent Utilization, Surface Coating, Marine: SIC 373, Isobutyl Alcohol",
    "2401080125":
        "Solvent Utilization, Surface Coating, Marine: SIC 373, Diethylene Glycol Monobutyl Ether",
    "2401080130":
        "Solvent Utilization, Surface Coating, Marine: SIC 373, Diethylene Glycol Monoethyl Ether",
    "2401080135":
        "Solvent Utilization, Surface Coating, Marine: SIC 373, Diethylene Glycol Monomethyl Ether",
    "2401080170":
        "Solvent Utilization, Surface Coating, Marine: SIC 373, Ethyl Acetate",
    "2401080200":
        "Solvent Utilization, Surface Coating, Marine: SIC 373, Ethylene Glycol Monoethyl Ether (2-Ethoxyethanol)",
    "2401080210":
        "Solvent Utilization, Surface Coating, Marine: SIC 373, Ethylene Glycol Monomethyl Ether (2-Methoxyethanol)",
    "2401080215":
        "Solvent Utilization, Surface Coating, Marine: SIC 373, Ethylene Glycol Monobutyl Ether (2-Butoxyethanol)",
    "2401080235":
        "Solvent Utilization, Surface Coating, Marine: SIC 373, Glycol Ethers: All Types",
    "2401080250":
        "Solvent Utilization, Surface Coating, Marine: SIC 373, Isopropanol",
    "2401080275":
        "Solvent Utilization, Surface Coating, Marine: SIC 373, Methyl Ethyl Ketone",
    "2401080285":
        "Solvent Utilization, Surface Coating, Marine: SIC 373, Methyl Isobutyl Ketone",
    "2401080370":
        "Solvent Utilization, Surface Coating, Marine: SIC 373, Special Naphthas",
    "2401080999":
        "Solvent Utilization, Surface Coating, Marine: SIC 373, Solvents: NEC",
    "2401085000":
        "Solvent Utilization, Surface Coating, Railroad: SIC 374, Total: All Solvent Types",
    "2401085030":
        "Solvent Utilization, Surface Coating, Railroad: SIC 374, Acetone",
    "2401085055":
        "Solvent Utilization, Surface Coating, Railroad: SIC 374, Butyl Acetate",
    "2401085060":
        "Solvent Utilization, Surface Coating, Railroad: SIC 374, Butyl Alcohols: All Types",
    "2401085065":
        "Solvent Utilization, Surface Coating, Railroad: SIC 374, n-Butyl Alcohol",
    "2401085070":
        "Solvent Utilization, Surface Coating, Railroad: SIC 374, Isobutyl Alcohol",
    "2401085125":
        "Solvent Utilization, Surface Coating, Railroad: SIC 374, Diethylene Glycol Monobutyl Ether",
    "2401085130":
        "Solvent Utilization, Surface Coating, Railroad: SIC 374, Diethylene Glycol Monoethyl Ether",
    "2401085135":
        "Solvent Utilization, Surface Coating, Railroad: SIC 374, Diethylene Glycol Monomethyl Ether",
    "2401085170":
        "Solvent Utilization, Surface Coating, Railroad: SIC 374, Ethyl Acetate",
    "2401085200":
        "Solvent Utilization, Surface Coating, Railroad: SIC 374, Ethylene Glycol Monoethyl Ether (2-Ethoxyethanol)",
    "2401085210":
        "Solvent Utilization, Surface Coating, Railroad: SIC 374, Ethylene Glycol Monomethyl Ether (2-Methoxyethanol)",
    "2401085215":
        "Solvent Utilization, Surface Coating, Railroad: SIC 374, Ethylene Glycol Monobutyl Ether (2-Butoxyethanol)",
    "2401085235":
        "Solvent Utilization, Surface Coating, Railroad: SIC 374, Glycol Ethers: All Types",
    "2401085250":
        "Solvent Utilization, Surface Coating, Railroad: SIC 374, Isopropanol",
    "2401085275":
        "Solvent Utilization, Surface Coating, Railroad: SIC 374, Methyl Ethyl Ketone",
    "2401085285":
        "Solvent Utilization, Surface Coating, Railroad: SIC 374, Methyl Isobutyl Ketone",
    "2401085370":
        "Solvent Utilization, Surface Coating, Railroad: SIC 374, Special Naphthas",
    "2401085999":
        "Solvent Utilization, Surface Coating, Railroad: SIC 374, Solvents: NEC",
    "2401090000":
        "Solvent Utilization, Surface Coating, Miscellaneous Manufacturing, Total: All Solvent Types",
    "2401090030":
        "Solvent Utilization, Surface Coating, Miscellaneous Manufacturing, Acetone",
    "2401090055":
        "Solvent Utilization, Surface Coating, Miscellaneous Manufacturing, Butyl Acetate",
    "2401090060":
        "Solvent Utilization, Surface Coating, Miscellaneous Manufacturing, Butyl Alcohols: All Types",
    "2401090065":
        "Solvent Utilization, Surface Coating, Miscellaneous Manufacturing, n-Butyl Alcohol",
    "2401090070":
        "Solvent Utilization, Surface Coating, Miscellaneous Manufacturing, Isobutyl Alcohol",
    "2401090125":
        "Solvent Utilization, Surface Coating, Miscellaneous Manufacturing, Diethylene Glycol Monobutyl Ether",
    "2401090130":
        "Solvent Utilization, Surface Coating, Miscellaneous Manufacturing, Diethylene Glycol Monoethyl Ether",
    "2401090135":
        "Solvent Utilization, Surface Coating, Miscellaneous Manufacturing, Diethylene Glycol Monomethyl Ether",
    "2401090170":
        "Solvent Utilization, Surface Coating, Miscellaneous Manufacturing, Ethyl Acetate",
    "2401090200":
        "Solvent Utilization, Surface Coating, Miscellaneous Manufacturing, Ethylene Glycol Monoethyl Ether (2-Ethoxyethanol)",
    "2401090210":
        "Solvent Utilization, Surface Coating, Miscellaneous Manufacturing, Ethylene Glycol Monomethyl Ether (2-Methoxyethanol)",
    "2401090215":
        "Solvent Utilization, Surface Coating, Miscellaneous Manufacturing, Ethylene Glycol Monobutyl Ether (2-Butoxyethanol)",
    "2401090235":
        "Solvent Utilization, Surface Coating, Miscellaneous Manufacturing, Glycol Ethers: All Types",
    "2401090250":
        "Solvent Utilization, Surface Coating, Miscellaneous Manufacturing, Isopropanol",
    "2401090275":
        "Solvent Utilization, Surface Coating, Miscellaneous Manufacturing, Methyl Ethyl Ketone",
    "2401090285":
        "Solvent Utilization, Surface Coating, Miscellaneous Manufacturing, Methyl Isobutyl Ketone",
    "2401090370":
        "Solvent Utilization, Surface Coating, Miscellaneous Manufacturing, Special Naphthas",
    "2401090999":
        "Solvent Utilization, Surface Coating, Miscellaneous Manufacturing, Solvents: NEC",
    "2401100000":
        "Solvent Utilization, Surface Coating, Industrial Maintenance Coatings, Total: All Solvent Types",
    "2401100001":
        "Solvent Utilization, Surface Coating, Industrial Maintenance Coatings, Thinning and Clean-Up of Solvent-Based Coatings",
    "2401100030":
        "Solvent Utilization, Surface Coating, Industrial Maintenance Coatings, Acetone",
    "2401100055":
        "Solvent Utilization, Surface Coating, Industrial Maintenance Coatings, Butyl Acetate",
    "2401100060":
        "Solvent Utilization, Surface Coating, Industrial Maintenance Coatings, Butyl Alcohols: All Types",
    "2401100065":
        "Solvent Utilization, Surface Coating, Industrial Maintenance Coatings, n-Butyl Alcohol",
    "2401100070":
        "Solvent Utilization, Surface Coating, Industrial Maintenance Coatings, Isobutyl Alcohol",
    "2401100125":
        "Solvent Utilization, Surface Coating, Industrial Maintenance Coatings, Diethylene Glycol Monobutyl Ether",
    "2401100130":
        "Solvent Utilization, Surface Coating, Industrial Maintenance Coatings, Diethylene Glycol Monoethyl Ether",
    "2401100135":
        "Solvent Utilization, Surface Coating, Industrial Maintenance Coatings, Diethylene Glycol Monomethyl Ether",
    "2401100170":
        "Solvent Utilization, Surface Coating, Industrial Maintenance Coatings, Ethyl Acetate",
    "2401100200":
        "Solvent Utilization, Surface Coating, Industrial Maintenance Coatings, Ethylene Glycol Monoethyl Ether (2-Ethoxyethanol)",
    "2401100210":
        "Solvent Utilization, Surface Coating, Industrial Maintenance Coatings, Ethylene Glycol Monomethyl Ether (2-Methoxyethanol)",
    "2401100215":
        "Solvent Utilization, Surface Coating, Industrial Maintenance Coatings, Ethylene Glycol Monobutyl Ether (2-Butoxyethanol)",
    "2401100235":
        "Solvent Utilization, Surface Coating, Industrial Maintenance Coatings, Glycol Ethers: All Types",
    "2401100250":
        "Solvent Utilization, Surface Coating, Industrial Maintenance Coatings, Isopropanol",
    "2401100275":
        "Solvent Utilization, Surface Coating, Industrial Maintenance Coatings, Methyl Ethyl Ketone",
    "2401100285":
        "Solvent Utilization, Surface Coating, Industrial Maintenance Coatings, Methyl Isobutyl Ketone",
    "2401100370":
        "Solvent Utilization, Surface Coating, Industrial Maintenance Coatings, Special Naphthas",
    "2401100999":
        "Solvent Utilization, Surface Coating, Industrial Maintenance Coatings, Solvents: NEC",
    "2401200000":
        "Solvent Utilization, Surface Coating, Other Special Purpose Coatings, Total: All Solvent Types",
    "2401200030":
        "Solvent Utilization, Surface Coating, Other Special Purpose Coatings, Acetone",
    "2401200055":
        "Solvent Utilization, Surface Coating, Other Special Purpose Coatings, Butyl Acetate",
    "2401200060":
        "Solvent Utilization, Surface Coating, Other Special Purpose Coatings, Butyl Alcohols: All Types",
    "2401200065":
        "Solvent Utilization, Surface Coating, Other Special Purpose Coatings, n-Butyl Alcohol",
    "2401200070":
        "Solvent Utilization, Surface Coating, Other Special Purpose Coatings, Isobutyl Alcohol",
    "2401200125":
        "Solvent Utilization, Surface Coating, Other Special Purpose Coatings, Diethylene Glycol Monobutyl Ether",
    "2401200130":
        "Solvent Utilization, Surface Coating, Other Special Purpose Coatings, Diethylene Glycol Monoethyl Ether",
    "2401200135":
        "Solvent Utilization, Surface Coating, Other Special Purpose Coatings, Diethylene Glycol Monomethyl Ether",
    "2401200170":
        "Solvent Utilization, Surface Coating, Other Special Purpose Coatings, Ethyl Acetate",
    "2401200200":
        "Solvent Utilization, Surface Coating, Other Special Purpose Coatings, Ethylene Glycol Monoethyl Ether (2-Ethoxyethanol)",
    "2401200210":
        "Solvent Utilization, Surface Coating, Other Special Purpose Coatings, Ethylene Glycol Monomethyl Ether (2-Methoxyethanol)",
    "2401200215":
        "Solvent Utilization, Surface Coating, Other Special Purpose Coatings, Ethylene Glycol Monobutyl Ether (2-Butoxyethanol)",
    "2401200235":
        "Solvent Utilization, Surface Coating, Other Special Purpose Coatings, Glycol Ethers: All Types",
    "2401200250":
        "Solvent Utilization, Surface Coating, Other Special Purpose Coatings, Isopropanol",
    "2401200275":
        "Solvent Utilization, Surface Coating, Other Special Purpose Coatings, Methyl Ethyl Ketone",
    "2401200285":
        "Solvent Utilization, Surface Coating, Other Special Purpose Coatings, Methyl Isobutyl Ketone",
    "2401200370":
        "Solvent Utilization, Surface Coating, Other Special Purpose Coatings, Special Naphthas",
    "2401200999":
        "Solvent Utilization, Surface Coating, Other Special Purpose Coatings, Solvents: NEC",
    "2401990000":
        "Solvent Utilization, Surface Coating, All Surface Coating Categories, Total: All Solvent Types",
    "2401990030":
        "Solvent Utilization, Surface Coating, All Surface Coating Categories, Acetone",
    "2401990055":
        "Solvent Utilization, Surface Coating, All Surface Coating Categories, Butyl Acetate",
    "2401990060":
        "Solvent Utilization, Surface Coating, All Surface Coating Categories, Butyl Alcohols: All Types",
    "2401990065":
        "Solvent Utilization, Surface Coating, All Surface Coating Categories, n-Butyl Alcohol",
    "2401990070":
        "Solvent Utilization, Surface Coating, All Surface Coating Categories, Isobutyl Alcohol",
    "2401990125":
        "Solvent Utilization, Surface Coating, All Surface Coating Categories, Diethylene Glycol Monobutyl Ether",
    "2401990130":
        "Solvent Utilization, Surface Coating, All Surface Coating Categories, Diethylene Glycol Monoethyl Ether",
    "2401990135":
        "Solvent Utilization, Surface Coating, All Surface Coating Categories, Diethylene Glycol Monomethyl Ether",
    "2401990170":
        "Solvent Utilization, Surface Coating, All Surface Coating Categories, Ethyl Acetate",
    "2401990200":
        "Solvent Utilization, Surface Coating, All Surface Coating Categories, Ethylene Glycol Monoethyl Ether (2-Ethoxyethanol)",
    "2401990210":
        "Solvent Utilization, Surface Coating, All Surface Coating Categories, Ethylene Glycol Monomethyl Ether (2-Methoxyethanol)",
    "2401990215":
        "Solvent Utilization, Surface Coating, All Surface Coating Categories, Ethylene Glycol Monobutyl Ether (2-Butoxyethanol)",
    "2401990235":
        "Solvent Utilization, Surface Coating, All Surface Coating Categories, Glycol Ethers: All Types",
    "2401990250":
        "Solvent Utilization, Surface Coating, All Surface Coating Categories, Isopropanol",
    "2401990275":
        "Solvent Utilization, Surface Coating, All Surface Coating Categories, Methyl Ethyl Ketone",
    "2401990285":
        "Solvent Utilization, Surface Coating, All Surface Coating Categories, Methyl Isobutyl Ketone",
    "2401990370":
        "Solvent Utilization, Surface Coating, All Surface Coating Categories, Special Naphthas",
    "2401990999":
        "Solvent Utilization, Surface Coating, All Surface Coating Categories, Solvents: NEC",
    "2402000000":
        "Solvent Utilization, Paint Strippers, Chemical Strippers, Application, Degradation, and Coating Removal Steps: Other Not Listed",
    "2415000000":
        "Solvent Utilization, Degreasing, All Processes/All Industries, Total: All Solvent Types",
    "2415000300":
        "Solvent Utilization, Degreasing, All Processes/All Industries, Monochlorobenzene",
    "2415000350":
        "Solvent Utilization, Degreasing, All Processes/All Industries, Perchloroethylene",
    "2415000370":
        "Solvent Utilization, Degreasing, All Processes/All Industries, Special Naphthas",
    "2415000385":
        "Solvent Utilization, Degreasing, All Processes/All Industries, Trichloroethylene",
    "2415000999":
        "Solvent Utilization, Degreasing, All Processes/All Industries, Solvents: NEC",
    "2415005000":
        "Solvent Utilization, Degreasing, Furniture and Fixtures (SIC 25): All Processes, Total: All Solvent Types",
    "2415005300":
        "Solvent Utilization, Degreasing, Furniture and Fixtures (SIC 25): All Processes, Monochlorobenzene",
    "2415005350":
        "Solvent Utilization, Degreasing, Furniture and Fixtures (SIC 25): All Processes, Perchloroethylene",
    "2415005370":
        "Solvent Utilization, Degreasing, Furniture and Fixtures (SIC 25): All Processes, Special Naphthas",
    "2415005385":
        "Solvent Utilization, Degreasing, Furniture and Fixtures (SIC 25): All Processes, Trichloroethylene",
    "2415005999":
        "Solvent Utilization, Degreasing, Furniture and Fixtures (SIC 25): All Processes, Solvents: NEC",
    "2415010000":
        "Solvent Utilization, Degreasing, Primary Metal Industries (SIC 33): All Processes, Total: All Solvent Types",
    "2415010300":
        "Solvent Utilization, Degreasing, Primary Metal Industries (SIC 33): All Processes, Monochlorobenzene",
    "2415010350":
        "Solvent Utilization, Degreasing, Primary Metal Industries (SIC 33): All Processes, Perchloroethylene",
    "2415010370":
        "Solvent Utilization, Degreasing, Primary Metal Industries (SIC 33): All Processes, Special Naphthas",
    "2415010385":
        "Solvent Utilization, Degreasing, Primary Metal Industries (SIC 33): All Processes, Trichloroethylene",
    "2415010999":
        "Solvent Utilization, Degreasing, Primary Metal Industries (SIC 33): All Processes, Solvents: NEC",
    "2415015000":
        "Solvent Utilization, Degreasing, Secondary Metal Industries (SIC 33): All Processes, Total: All Solvent Types",
    "2415015300":
        "Solvent Utilization, Degreasing, Secondary Metal Industries (SIC 33): All Processes, Monochlorobenzene",
    "2415015350":
        "Solvent Utilization, Degreasing, Secondary Metal Industries (SIC 33): All Processes, Perchloroethylene",
    "2415015370":
        "Solvent Utilization, Degreasing, Secondary Metal Industries (SIC 33): All Processes, Special Naphthas",
    "2415015385":
        "Solvent Utilization, Degreasing, Secondary Metal Industries (SIC 33): All Processes, Trichloroethylene",
    "2415015999":
        "Solvent Utilization, Degreasing, Secondary Metal Industries (SIC 33): All Processes, Solvents: NEC",
    "2415020000":
        "Solvent Utilization, Degreasing, Fabricated Metal Products (SIC 34): All Processes, Total: All Solvent Types",
    "2415020300":
        "Solvent Utilization, Degreasing, Fabricated Metal Products (SIC 34): All Processes, Monochlorobenzene",
    "2415020350":
        "Solvent Utilization, Degreasing, Fabricated Metal Products (SIC 34): All Processes, Perchloroethylene",
    "2415020370":
        "Solvent Utilization, Degreasing, Fabricated Metal Products (SIC 34): All Processes, Special Naphthas",
    "2415020385":
        "Solvent Utilization, Degreasing, Fabricated Metal Products (SIC 34): All Processes, Trichloroethylene",
    "2415020999":
        "Solvent Utilization, Degreasing, Fabricated Metal Products (SIC 34): All Processes, Solvents: NEC",
    "2415025000":
        "Solvent Utilization, Degreasing, Industrial Machinery and Equipment (SIC 35): All Processes, Total: All Solvent Types",
    "2415025300":
        "Solvent Utilization, Degreasing, Industrial Machinery and Equipment (SIC 35): All Processes, Monochlorobenzene",
    "2415025350":
        "Solvent Utilization, Degreasing, Industrial Machinery and Equipment (SIC 35): All Processes, Perchloroethylene",
    "2415025370":
        "Solvent Utilization, Degreasing, Industrial Machinery and Equipment (SIC 35): All Processes, Special Naphthas",
    "2415025385":
        "Solvent Utilization, Degreasing, Industrial Machinery and Equipment (SIC 35): All Processes, Trichloroethylene",
    "2415025999":
        "Solvent Utilization, Degreasing, Industrial Machinery and Equipment (SIC 35): All Processes, Solvents: NEC",
    "2415030000":
        "Solvent Utilization, Degreasing, Electronic and Other Elec. (SIC 36): All Processes, Total: All Solvent Types",
    "2415030300":
        "Solvent Utilization, Degreasing, Electronic and Other Elec. (SIC 36): All Processes, Monochlorobenzene",
    "2415030350":
        "Solvent Utilization, Degreasing, Electronic and Other Elec. (SIC 36): All Processes, Perchloroethylene",
    "2415030370":
        "Solvent Utilization, Degreasing, Electronic and Other Elec. (SIC 36): All Processes, Special Naphthas",
    "2415030385":
        "Solvent Utilization, Degreasing, Electronic and Other Elec. (SIC 36): All Processes, Trichloroethylene",
    "2415030999":
        "Solvent Utilization, Degreasing, Electronic and Other Elec. (SIC 36): All Processes, Solvents: NEC",
    "2415035000":
        "Solvent Utilization, Degreasing, Transportation Equipment (SIC 37): All Processes, Total: All Solvent Types",
    "2415035300":
        "Solvent Utilization, Degreasing, Transportation Equipment (SIC 37): All Processes, Monochlorobenzene",
    "2415035350":
        "Solvent Utilization, Degreasing, Transportation Equipment (SIC 37): All Processes, Perchloroethylene",
    "2415035370":
        "Solvent Utilization, Degreasing, Transportation Equipment (SIC 37): All Processes, Special Naphthas",
    "2415035385":
        "Solvent Utilization, Degreasing, Transportation Equipment (SIC 37): All Processes, Trichloroethylene",
    "2415035999":
        "Solvent Utilization, Degreasing, Transportation Equipment (SIC 37): All Processes, Solvents: NEC",
    "2415040000":
        "Solvent Utilization, Degreasing, Instruments and Related Products (SIC 38): All Processes, Total: All Solvent Types",
    "2415040300":
        "Solvent Utilization, Degreasing, Instruments and Related Products (SIC 38): All Processes, Monochlorobenzene",
    "2415040350":
        "Solvent Utilization, Degreasing, Instruments and Related Products (SIC 38): All Processes, Perchloroethylene",
    "2415040370":
        "Solvent Utilization, Degreasing, Instruments and Related Products (SIC 38): All Processes, Special Naphthas",
    "2415040385":
        "Solvent Utilization, Degreasing, Instruments and Related Products (SIC 38): All Processes, Trichloroethylene",
    "2415040999":
        "Solvent Utilization, Degreasing, Instruments and Related Products (SIC 38): All Processes, Solvents: NEC",
    "2415045000":
        "Solvent Utilization, Degreasing, Miscellaneous Manufacturing (SIC 39): All Processes, Total: All Solvent Types",
    "2415045300":
        "Solvent Utilization, Degreasing, Miscellaneous Manufacturing (SIC 39): All Processes, Monochlorobenzene",
    "2415045350":
        "Solvent Utilization, Degreasing, Miscellaneous Manufacturing (SIC 39): All Processes, Perchloroethylene",
    "2415045370":
        "Solvent Utilization, Degreasing, Miscellaneous Manufacturing (SIC 39): All Processes, Special Naphthas",
    "2415045385":
        "Solvent Utilization, Degreasing, Miscellaneous Manufacturing (SIC 39): All Processes, Trichloroethylene",
    "2415045999":
        "Solvent Utilization, Degreasing, Miscellaneous Manufacturing (SIC 39): All Processes, Solvents: NEC",
    "2415050000":
        "Solvent Utilization, Degreasing, Transportation Maintenance Facilities (SIC 40-45): All Processes, Total: All Solvent Types",
    "2415050300":
        "Solvent Utilization, Degreasing, Transportation Maintenance Facilities (SIC 40-45): All Processes, Monochlorobenzene",
    "2415050350":
        "Solvent Utilization, Degreasing, Transportation Maintenance Facilities (SIC 40-45): All Processes, Perchloroethylene",
    "2415050370":
        "Solvent Utilization, Degreasing, Transportation Maintenance Facilities (SIC 40-45): All Processes, Special Naphthas",
    "2415050385":
        "Solvent Utilization, Degreasing, Transportation Maintenance Facilities (SIC 40-45): All Processes, Trichloroethylene",
    "2415050999":
        "Solvent Utilization, Degreasing, Transportation Maintenance Facilities (SIC 40-45): All Processes, Solvents: NEC",
    "2415055000":
        "Solvent Utilization, Degreasing, Automotive Dealers (SIC 55): All Processes, Total: All Solvent Types",
    "2415055300":
        "Solvent Utilization, Degreasing, Automotive Dealers (SIC 55): All Processes, Monochlorobenzene",
    "2415055350":
        "Solvent Utilization, Degreasing, Automotive Dealers (SIC 55): All Processes, Perchloroethylene",
    "2415055370":
        "Solvent Utilization, Degreasing, Automotive Dealers (SIC 55): All Processes, Special Naphthas",
    "2415055385":
        "Solvent Utilization, Degreasing, Automotive Dealers (SIC 55): All Processes, Trichloroethylene",
    "2415055999":
        "Solvent Utilization, Degreasing, Automotive Dealers (SIC 55): All Processes, Solvents: NEC",
    "2415060000":
        "Solvent Utilization, Degreasing, Miscellaneous Repair Services (SIC 76): All Processes, Total: All Solvent Types",
    "2415060300":
        "Solvent Utilization, Degreasing, Miscellaneous Repair Services (SIC 76): All Processes, Monochlorobenzene",
    "2415060350":
        "Solvent Utilization, Degreasing, Miscellaneous Repair Services (SIC 76): All Processes, Perchloroethylene",
    "2415060370":
        "Solvent Utilization, Degreasing, Miscellaneous Repair Services (SIC 76): All Processes, Special Naphthas",
    "2415060385":
        "Solvent Utilization, Degreasing, Miscellaneous Repair Services (SIC 76): All Processes, Trichloroethylene",
    "2415060999":
        "Solvent Utilization, Degreasing, Miscellaneous Repair Services (SIC 76): All Processes, Solvents: NEC",
    "2415065000":
        "Solvent Utilization, Degreasing, Auto Repair Services (SIC 75): All Processes, Total: All Solvent Types",
    "2415065300":
        "Solvent Utilization, Degreasing, Auto Repair Services (SIC 75): All Processes, Monochlorobenzene",
    "2415065350":
        "Solvent Utilization, Degreasing, Auto Repair Services (SIC 75): All Processes, Perchloroethylene",
    "2415065370":
        "Solvent Utilization, Degreasing, Auto Repair Services (SIC 75): All Processes, Special Naphthas",
    "2415065385":
        "Solvent Utilization, Degreasing, Auto Repair Services (SIC 75): All Processes, Trichloroethylene",
    "2415065999":
        "Solvent Utilization, Degreasing, Auto Repair Services (SIC 75): All Processes, Solvents: NEC",
    "2415100000":
        "Solvent Utilization, Degreasing, All Industries: Open Top Degreasing, Total: All Solvent Types",
    "2415100300":
        "Solvent Utilization, Degreasing, All Industries: Open Top Degreasing, Monochlorobenzene",
    "2415100350":
        "Solvent Utilization, Degreasing, All Industries: Open Top Degreasing, Perchloroethylene",
    "2415100370":
        "Solvent Utilization, Degreasing, All Industries: Open Top Degreasing, Special Naphthas",
    "2415100385":
        "Solvent Utilization, Degreasing, All Industries: Open Top Degreasing, Trichloroethylene",
    "2415100999":
        "Solvent Utilization, Degreasing, All Industries: Open Top Degreasing, Solvents: NEC",
    "2415105000":
        "Solvent Utilization, Degreasing, Furniture and Fixtures (SIC 25): Open Top Degreasing, Total: All Solvent Types",
    "2415105300":
        "Solvent Utilization, Degreasing, Furniture and Fixtures (SIC 25): Open Top Degreasing, Monochlorobenzene",
    "2415105350":
        "Solvent Utilization, Degreasing, Furniture and Fixtures (SIC 25): Open Top Degreasing, Perchloroethylene",
    "2415105370":
        "Solvent Utilization, Degreasing, Furniture and Fixtures (SIC 25): Open Top Degreasing, Special Naphthas",
    "2415105385":
        "Solvent Utilization, Degreasing, Furniture and Fixtures (SIC 25): Open Top Degreasing, Trichloroethylene",
    "2415105999":
        "Solvent Utilization, Degreasing, Furniture and Fixtures (SIC 25): Open Top Degreasing, Solvents: NEC",
    "2415110000":
        "Solvent Utilization, Degreasing, Primary Metal Industries (SIC 33): Open Top Degreasing, Total: All Solvent Types",
    "2415110300":
        "Solvent Utilization, Degreasing, Primary Metal Industries (SIC 33): Open Top Degreasing, Monochlorobenzene",
    "2415110350":
        "Solvent Utilization, Degreasing, Primary Metal Industries (SIC 33): Open Top Degreasing, Perchloroethylene",
    "2415110370":
        "Solvent Utilization, Degreasing, Primary Metal Industries (SIC 33): Open Top Degreasing, Special Naphthas",
    "2415110385":
        "Solvent Utilization, Degreasing, Primary Metal Industries (SIC 33): Open Top Degreasing, Trichloroethylene",
    "2415110999":
        "Solvent Utilization, Degreasing, Primary Metal Industries (SIC 33): Open Top Degreasing, Solvents: NEC",
    "2415115000":
        "Solvent Utilization, Degreasing, Secondary Metal Industries (SIC 33): Open Top Degreasing, Total: All Solvent Types",
    "2415115300":
        "Solvent Utilization, Degreasing, Secondary Metal Industries (SIC 33): Open Top Degreasing, Monochlorobenzene",
    "2415115350":
        "Solvent Utilization, Degreasing, Secondary Metal Industries (SIC 33): Open Top Degreasing, Perchloroethylene",
    "2415115370":
        "Solvent Utilization, Degreasing, Secondary Metal Industries (SIC 33): Open Top Degreasing, Special Naphthas",
    "2415115385":
        "Solvent Utilization, Degreasing, Secondary Metal Industries (SIC 33): Open Top Degreasing, Trichloroethylene",
    "2415115999":
        "Solvent Utilization, Degreasing, Secondary Metal Industries (SIC 33): Open Top Degreasing, Solvents: NEC",
    "2415120000":
        "Solvent Utilization, Degreasing, Fabricated Metal Products (SIC 34): Open Top Degreasing, Total: All Solvent Types",
    "2415120300":
        "Solvent Utilization, Degreasing, Fabricated Metal Products (SIC 34): Open Top Degreasing, Monochlorobenzene",
    "2415120350":
        "Solvent Utilization, Degreasing, Fabricated Metal Products (SIC 34): Open Top Degreasing, Perchloroethylene",
    "2415120370":
        "Solvent Utilization, Degreasing, Fabricated Metal Products (SIC 34): Open Top Degreasing, Special Naphthas",
    "2415120385":
        "Solvent Utilization, Degreasing, Fabricated Metal Products (SIC 34): Open Top Degreasing, Trichloroethylene",
    "2415120999":
        "Solvent Utilization, Degreasing, Fabricated Metal Products (SIC 34): Open Top Degreasing, Solvents: NEC",
    "2415125000":
        "Solvent Utilization, Degreasing, Industrial Machinery and Equipment (SIC 35): Open Top Degreasing, Total: All Solvent Types",
    "2415125300":
        "Solvent Utilization, Degreasing, Industrial Machinery and Equipment (SIC 35): Open Top Degreasing, Monochlorobenzene",
    "2415125350":
        "Solvent Utilization, Degreasing, Industrial Machinery and Equipment (SIC 35): Open Top Degreasing, Perchloroethylene",
    "2415125370":
        "Solvent Utilization, Degreasing, Industrial Machinery and Equipment (SIC 35): Open Top Degreasing, Special Naphthas",
    "2415125385":
        "Solvent Utilization, Degreasing, Industrial Machinery and Equipment (SIC 35): Open Top Degreasing, Trichloroethylene",
    "2415125999":
        "Solvent Utilization, Degreasing, Industrial Machinery and Equipment (SIC 35): Open Top Degreasing, Solvents: NEC",
    "2415130000":
        "Solvent Utilization, Degreasing, Electronic and Other Elec. (SIC 36): Open Top Degreasing, Total: All Solvent Types",
    "2415130300":
        "Solvent Utilization, Degreasing, Electronic and Other Elec. (SIC 36): Open Top Degreasing, Monochlorobenzene",
    "2415130350":
        "Solvent Utilization, Degreasing, Electronic and Other Elec. (SIC 36): Open Top Degreasing, Perchloroethylene",
    "2415130370":
        "Solvent Utilization, Degreasing, Electronic and Other Elec. (SIC 36): Open Top Degreasing, Special Naphthas",
    "2415130385":
        "Solvent Utilization, Degreasing, Electronic and Other Elec. (SIC 36): Open Top Degreasing, Trichloroethylene",
    "2415130999":
        "Solvent Utilization, Degreasing, Electronic and Other Elec. (SIC 36): Open Top Degreasing, Solvents: NEC",
    "2415135000":
        "Solvent Utilization, Degreasing, Transportation Equipment (SIC 37): Open Top Degreasing, Total: All Solvent Types",
    "2415135300":
        "Solvent Utilization, Degreasing, Transportation Equipment (SIC 37): Open Top Degreasing, Monochlorobenzene",
    "2415135350":
        "Solvent Utilization, Degreasing, Transportation Equipment (SIC 37): Open Top Degreasing, Perchloroethylene",
    "2415135370":
        "Solvent Utilization, Degreasing, Transportation Equipment (SIC 37): Open Top Degreasing, Special Naphthas",
    "2415135385":
        "Solvent Utilization, Degreasing, Transportation Equipment (SIC 37): Open Top Degreasing, Trichloroethylene",
    "2415135999":
        "Solvent Utilization, Degreasing, Transportation Equipment (SIC 37): Open Top Degreasing, Solvents: NEC",
    "2415140000":
        "Solvent Utilization, Degreasing, Instruments and Related Products (SIC 38): Open Top Degreasing, Total: All Solvent Types",
    "2415140300":
        "Solvent Utilization, Degreasing, Instruments and Related Products (SIC 38): Open Top Degreasing, Monochlorobenzene",
    "2415140350":
        "Solvent Utilization, Degreasing, Instruments and Related Products (SIC 38): Open Top Degreasing, Perchloroethylene",
    "2415140370":
        "Solvent Utilization, Degreasing, Instruments and Related Products (SIC 38): Open Top Degreasing, Special Naphthas",
    "2415140385":
        "Solvent Utilization, Degreasing, Instruments and Related Products (SIC 38): Open Top Degreasing, Trichloroethylene",
    "2415140999":
        "Solvent Utilization, Degreasing, Instruments and Related Products (SIC 38): Open Top Degreasing, Solvents: NEC",
    "2415145000":
        "Solvent Utilization, Degreasing, Miscellaneous Manufacturing (SIC 39): Open Top Degreasing, Total: All Solvent Types",
    "2415145300":
        "Solvent Utilization, Degreasing, Miscellaneous Manufacturing (SIC 39): Open Top Degreasing, Monochlorobenzene",
    "2415145350":
        "Solvent Utilization, Degreasing, Miscellaneous Manufacturing (SIC 39): Open Top Degreasing, Perchloroethylene",
    "2415145370":
        "Solvent Utilization, Degreasing, Miscellaneous Manufacturing (SIC 39): Open Top Degreasing, Special Naphthas",
    "2415145385":
        "Solvent Utilization, Degreasing, Miscellaneous Manufacturing (SIC 39): Open Top Degreasing, Trichloroethylene",
    "2415145999":
        "Solvent Utilization, Degreasing, Miscellaneous Manufacturing (SIC 39): Open Top Degreasing, Solvents: NEC",
    "2415150000":
        "Solvent Utilization, Degreasing, Transportation Maintenance Facilities (SIC 40-45): Open Top Degreasing, Total: All Solvent Types",
    "2415150300":
        "Solvent Utilization, Degreasing, Transportation Maintenance Facilities (SIC 40-45): Open Top Degreasing, Monochlorobenzene",
    "2415150350":
        "Solvent Utilization, Degreasing, Transportation Maintenance Facilities (SIC 40-45): Open Top Degreasing, Perchloroethylene",
    "2415150370":
        "Solvent Utilization, Degreasing, Transportation Maintenance Facilities (SIC 40-45): Open Top Degreasing, Special Naphthas",
    "2415150385":
        "Solvent Utilization, Degreasing, Transportation Maintenance Facilities (SIC 40-45): Open Top Degreasing, Trichloroethylene",
    "2415150999":
        "Solvent Utilization, Degreasing, Transportation Maintenance Facilities (SIC 40-45): Open Top Degreasing, Solvents: NEC",
    "2415155000":
        "Solvent Utilization, Degreasing, Automotive Dealers (SIC 55): Open Top Degreasing, Total: All Solvent Types",
    "2415155300":
        "Solvent Utilization, Degreasing, Automotive Dealers (SIC 55): Open Top Degreasing, Monochlorobenzene",
    "2415155350":
        "Solvent Utilization, Degreasing, Automotive Dealers (SIC 55): Open Top Degreasing, Perchloroethylene",
    "2415155370":
        "Solvent Utilization, Degreasing, Automotive Dealers (SIC 55): Open Top Degreasing, Special Naphthas",
    "2415155385":
        "Solvent Utilization, Degreasing, Automotive Dealers (SIC 55): Open Top Degreasing, Trichloroethylene",
    "2415155999":
        "Solvent Utilization, Degreasing, Automotive Dealers (SIC 55): Open Top Degreasing, Solvents: NEC",
    "2415160000":
        "Solvent Utilization, Degreasing, Auto Repair Services (SIC 75): Open Top Degreasing, Total: All Solvent Types",
    "2415160300":
        "Solvent Utilization, Degreasing, Auto Repair Services (SIC 75): Open Top Degreasing, Monochlorobenzene",
    "2415160350":
        "Solvent Utilization, Degreasing, Auto Repair Services (SIC 75): Open Top Degreasing, Perchloroethylene",
    "2415160370":
        "Solvent Utilization, Degreasing, Auto Repair Services (SIC 75): Open Top Degreasing, Special Naphthas",
    "2415160385":
        "Solvent Utilization, Degreasing, Auto Repair Services (SIC 75): Open Top Degreasing, Trichloroethylene",
    "2415160999":
        "Solvent Utilization, Degreasing, Auto Repair Services (SIC 75): Open Top Degreasing, Solvents: NEC",
    "2415165000":
        "Solvent Utilization, Degreasing, Miscellaneous Repair Services (SIC 76): Open Top Degreasing, Total: All Solvent Types",
    "2415165300":
        "Solvent Utilization, Degreasing, Miscellaneous Repair Services (SIC 76): Open Top Degreasing, Monochlorobenzene",
    "2415165350":
        "Solvent Utilization, Degreasing, Miscellaneous Repair Services (SIC 76): Open Top Degreasing, Perchloroethylene",
    "2415165370":
        "Solvent Utilization, Degreasing, Miscellaneous Repair Services (SIC 76): Open Top Degreasing, Special Naphthas",
    "2415165385":
        "Solvent Utilization, Degreasing, Miscellaneous Repair Services (SIC 76): Open Top Degreasing, Trichloroethylene",
    "2415165999":
        "Solvent Utilization, Degreasing, Miscellaneous Repair Services (SIC 76): Open Top Degreasing, Solvents: NEC",
    "2415200000":
        "Solvent Utilization, Degreasing, All Industries: Conveyerized Degreasing, Total: All Solvent Types",
    "2415200300":
        "Solvent Utilization, Degreasing, All Industries: Conveyerized Degreasing, Monochlorobenzene",
    "2415200350":
        "Solvent Utilization, Degreasing, All Industries: Conveyerized Degreasing, Perchloroethylene",
    "2415200370":
        "Solvent Utilization, Degreasing, All Industries: Conveyerized Degreasing, Special Naphthas",
    "2415200385":
        "Solvent Utilization, Degreasing, All Industries: Conveyerized Degreasing, Trichloroethylene",
    "2415200999":
        "Solvent Utilization, Degreasing, All Industries: Conveyerized Degreasing, Solvents: NEC",
    "2415205000":
        "Solvent Utilization, Degreasing, Furniture and Fixtures (SIC 25): Conveyerized Degreasing, Total: All Solvent Types",
    "2415205300":
        "Solvent Utilization, Degreasing, Furniture and Fixtures (SIC 25): Conveyerized Degreasing, Monochlorobenzene",
    "2415205350":
        "Solvent Utilization, Degreasing, Furniture and Fixtures (SIC 25): Conveyerized Degreasing, Perchloroethylene",
    "2415205370":
        "Solvent Utilization, Degreasing, Furniture and Fixtures (SIC 25): Conveyerized Degreasing, Special Naphthas",
    "2415205385":
        "Solvent Utilization, Degreasing, Furniture and Fixtures (SIC 25): Conveyerized Degreasing, Trichloroethylene",
    "2415205999":
        "Solvent Utilization, Degreasing, Furniture and Fixtures (SIC 25): Conveyerized Degreasing, Solvents: NEC",
    "2415210000":
        "Solvent Utilization, Degreasing, Primary Metal Industries (SIC 33): Conveyerized Degreasing, Total: All Solvent Types",
    "2415210300":
        "Solvent Utilization, Degreasing, Primary Metal Industries (SIC 33): Conveyerized Degreasing, Monochlorobenzene",
    "2415210350":
        "Solvent Utilization, Degreasing, Primary Metal Industries (SIC 33): Conveyerized Degreasing, Perchloroethylene",
    "2415210370":
        "Solvent Utilization, Degreasing, Primary Metal Industries (SIC 33): Conveyerized Degreasing, Special Naphthas",
    "2415210385":
        "Solvent Utilization, Degreasing, Primary Metal Industries (SIC 33): Conveyerized Degreasing, Trichloroethylene",
    "2415210999":
        "Solvent Utilization, Degreasing, Primary Metal Industries (SIC 33): Conveyerized Degreasing, Solvents: NEC",
    "2415215000":
        "Solvent Utilization, Degreasing, Secondary Metal Industries (SIC 33): Conveyerized Degreasing, Total: All Solvent Types",
    "2415215300":
        "Solvent Utilization, Degreasing, Secondary Metal Industries (SIC 33): Conveyerized Degreasing, Monochlorobenzene",
    "2415215350":
        "Solvent Utilization, Degreasing, Secondary Metal Industries (SIC 33): Conveyerized Degreasing, Perchloroethylene",
    "2415215370":
        "Solvent Utilization, Degreasing, Secondary Metal Industries (SIC 33): Conveyerized Degreasing, Special Naphthas",
    "2415215385":
        "Solvent Utilization, Degreasing, Secondary Metal Industries (SIC 33): Conveyerized Degreasing, Trichloroethylene",
    "2415215999":
        "Solvent Utilization, Degreasing, Secondary Metal Industries (SIC 33): Conveyerized Degreasing, Solvents: NEC",
    "2415220000":
        "Solvent Utilization, Degreasing, Fabricated Metal Products (SIC 34): Conveyerized Degreasing, Total: All Solvent Types",
    "2415220300":
        "Solvent Utilization, Degreasing, Fabricated Metal Products (SIC 34): Conveyerized Degreasing, Monochlorobenzene",
    "2415220350":
        "Solvent Utilization, Degreasing, Fabricated Metal Products (SIC 34): Conveyerized Degreasing, Perchloroethylene",
    "2415220370":
        "Solvent Utilization, Degreasing, Fabricated Metal Products (SIC 34): Conveyerized Degreasing, Special Naphthas",
    "2415220385":
        "Solvent Utilization, Degreasing, Fabricated Metal Products (SIC 34): Conveyerized Degreasing, Trichloroethylene",
    "2415220999":
        "Solvent Utilization, Degreasing, Fabricated Metal Products (SIC 34): Conveyerized Degreasing, Solvents: NEC",
    "2415225000":
        "Solvent Utilization, Degreasing, Industrial Machinery and Equipment (SIC 35): Conveyerized Degreasing, Total: All Solvent Types",
    "2415225300":
        "Solvent Utilization, Degreasing, Industrial Machinery and Equipment (SIC 35): Conveyerized Degreasing, Monochlorobenzene",
    "2415225350":
        "Solvent Utilization, Degreasing, Industrial Machinery and Equipment (SIC 35): Conveyerized Degreasing, Perchloroethylene",
    "2415225370":
        "Solvent Utilization, Degreasing, Industrial Machinery and Equipment (SIC 35): Conveyerized Degreasing, Special Naphthas",
    "2415225385":
        "Solvent Utilization, Degreasing, Industrial Machinery and Equipment (SIC 35): Conveyerized Degreasing, Trichloroethylene",
    "2415225999":
        "Solvent Utilization, Degreasing, Industrial Machinery and Equipment (SIC 35): Conveyerized Degreasing, Solvents: NEC",
    "2415230000":
        "Solvent Utilization, Degreasing, Electronic and Other Elec. (SIC 36): Conveyerized Degreasing, Total: All Solvent Types",
    "2415230300":
        "Solvent Utilization, Degreasing, Electronic and Other Elec. (SIC 36): Conveyerized Degreasing, Monochlorobenzene",
    "2415230350":
        "Solvent Utilization, Degreasing, Electronic and Other Elec. (SIC 36): Conveyerized Degreasing, Perchloroethylene",
    "2415230370":
        "Solvent Utilization, Degreasing, Electronic and Other Elec. (SIC 36): Conveyerized Degreasing, Special Naphthas",
    "2415230385":
        "Solvent Utilization, Degreasing, Electronic and Other Elec. (SIC 36): Conveyerized Degreasing, Trichloroethylene",
    "2415230999":
        "Solvent Utilization, Degreasing, Electronic and Other Elec. (SIC 36): Conveyerized Degreasing, Solvents: NEC",
    "2415235000":
        "Solvent Utilization, Degreasing, Transportation Equipment (SIC 37): Conveyerized Degreasing, Total: All Solvent Types",
    "2415235300":
        "Solvent Utilization, Degreasing, Transportation Equipment (SIC 37): Conveyerized Degreasing, Monochlorobenzene",
    "2415235350":
        "Solvent Utilization, Degreasing, Transportation Equipment (SIC 37): Conveyerized Degreasing, Perchloroethylene",
    "2415235370":
        "Solvent Utilization, Degreasing, Transportation Equipment (SIC 37): Conveyerized Degreasing, Special Naphthas",
    "2415235385":
        "Solvent Utilization, Degreasing, Transportation Equipment (SIC 37): Conveyerized Degreasing, Trichloroethylene",
    "2415235999":
        "Solvent Utilization, Degreasing, Transportation Equipment (SIC 37): Conveyerized Degreasing, Solvents: NEC",
    "2415240000":
        "Solvent Utilization, Degreasing, Instruments and Related Products (SIC 38): Conveyerized Degreasing, Total: All Solvent Types",
    "2415240300":
        "Solvent Utilization, Degreasing, Instruments and Related Products (SIC 38): Conveyerized Degreasing, Monochlorobenzene",
    "2415240350":
        "Solvent Utilization, Degreasing, Instruments and Related Products (SIC 38): Conveyerized Degreasing, Perchloroethylene",
    "2415240370":
        "Solvent Utilization, Degreasing, Instruments and Related Products (SIC 38): Conveyerized Degreasing, Special Naphthas",
    "2415240385":
        "Solvent Utilization, Degreasing, Instruments and Related Products (SIC 38): Conveyerized Degreasing, Trichloroethylene",
    "2415240999":
        "Solvent Utilization, Degreasing, Instruments and Related Products (SIC 38): Conveyerized Degreasing, Solvents: NEC",
    "2415245000":
        "Solvent Utilization, Degreasing, Miscellaneous Manufacturing (SIC 39): Conveyerized Degreasing, Total: All Solvent Types",
    "2415245300":
        "Solvent Utilization, Degreasing, Miscellaneous Manufacturing (SIC 39): Conveyerized Degreasing, Monochlorobenzene",
    "2415245350":
        "Solvent Utilization, Degreasing, Miscellaneous Manufacturing (SIC 39): Conveyerized Degreasing, Perchloroethylene",
    "2415245370":
        "Solvent Utilization, Degreasing, Miscellaneous Manufacturing (SIC 39): Conveyerized Degreasing, Special Naphthas",
    "2415245385":
        "Solvent Utilization, Degreasing, Miscellaneous Manufacturing (SIC 39): Conveyerized Degreasing, Trichloroethylene",
    "2415245999":
        "Solvent Utilization, Degreasing, Miscellaneous Manufacturing (SIC 39): Conveyerized Degreasing, Solvents: NEC",
    "2415250000":
        "Solvent Utilization, Degreasing, Trans. Maintenance Facilities (SIC 40-45): Conveyerized Degreasing, Total: All Solvent Types",
    "2415250300":
        "Solvent Utilization, Degreasing, Trans. Maintenance Facilities (SIC 40-45): Conveyerized Degreasing, Monochlorobenzene",
    "2415250350":
        "Solvent Utilization, Degreasing, Trans. Maintenance Facilities (SIC 40-45): Conveyerized Degreasing, Perchloroethylene",
    "2415250370":
        "Solvent Utilization, Degreasing, Trans. Maintenance Facilities (SIC 40-45): Conveyerized Degreasing, Special Naphthas",
    "2415250385":
        "Solvent Utilization, Degreasing, Trans. Maintenance Facilities (SIC 40-45): Conveyerized Degreasing, Trichloroethylene",
    "2415250999":
        "Solvent Utilization, Degreasing, Trans. Maintenance Facilities (SIC 40-45): Conveyerized Degreasing, Solvents: NEC",
    "2415255000":
        "Solvent Utilization, Degreasing, Automotive Dealers (SIC 55): Conveyerized Degreasing, Total: All Solvent Types",
    "2415255300":
        "Solvent Utilization, Degreasing, Automotive Dealers (SIC 55): Conveyerized Degreasing, Monochlorobenzene",
    "2415255350":
        "Solvent Utilization, Degreasing, Automotive Dealers (SIC 55): Conveyerized Degreasing, Perchloroethylene",
    "2415255370":
        "Solvent Utilization, Degreasing, Automotive Dealers (SIC 55): Conveyerized Degreasing, Special Naphthas",
    "2415255385":
        "Solvent Utilization, Degreasing, Automotive Dealers (SIC 55): Conveyerized Degreasing, Trichloroethylene",
    "2415255999":
        "Solvent Utilization, Degreasing, Automotive Dealers (SIC 55): Conveyerized Degreasing, Solvents: NEC",
    "2415260000":
        "Solvent Utilization, Degreasing, Auto Repair Services (SIC 75): Conveyerized Degreasing, Total: All Solvent Types",
    "2415260300":
        "Solvent Utilization, Degreasing, Auto Repair Services (SIC 75): Conveyerized Degreasing, Monochlorobenzene",
    "2415260350":
        "Solvent Utilization, Degreasing, Auto Repair Services (SIC 75): Conveyerized Degreasing, Perchloroethylene",
    "2415260370":
        "Solvent Utilization, Degreasing, Auto Repair Services (SIC 75): Conveyerized Degreasing, Special Naphthas",
    "2415260385":
        "Solvent Utilization, Degreasing, Auto Repair Services (SIC 75): Conveyerized Degreasing, Trichloroethylene",
    "2415260999":
        "Solvent Utilization, Degreasing, Auto Repair Services (SIC 75): Conveyerized Degreasing, Solvents: NEC",
    "2415265000":
        "Solvent Utilization, Degreasing, Miscellaneous Repair Services (SIC 76): Conveyerized Degreasing, Total: All Solvent Types",
    "2415265300":
        "Solvent Utilization, Degreasing, Miscellaneous Repair Services (SIC 76): Conveyerized Degreasing, Monochlorobenzene",
    "2415265350":
        "Solvent Utilization, Degreasing, Miscellaneous Repair Services (SIC 76): Conveyerized Degreasing, Perchloroethylene",
    "2415265370":
        "Solvent Utilization, Degreasing, Miscellaneous Repair Services (SIC 76): Conveyerized Degreasing, Special Naphthas",
    "2415265385":
        "Solvent Utilization, Degreasing, Miscellaneous Repair Services (SIC 76): Conveyerized Degreasing, Trichloroethylene",
    "2415265999":
        "Solvent Utilization, Degreasing, Miscellaneous Repair Services (SIC 76): Conveyerized Degreasing, Solvents: NEC",
    "2415300000":
        "Solvent Utilization, Degreasing, All Industries: Cold Cleaning, Total: All Solvent Types",
    "2415300300":
        "Solvent Utilization, Degreasing, All Industries: Cold Cleaning, Monochlorobenzene",
    "2415300350":
        "Solvent Utilization, Degreasing, All Industries: Cold Cleaning, Perchloroethylene",
    "2415300370":
        "Solvent Utilization, Degreasing, All Industries: Cold Cleaning, Special Naphthas",
    "2415300385":
        "Solvent Utilization, Degreasing, All Industries: Cold Cleaning, Trichloroethylene",
    "2415300999":
        "Solvent Utilization, Degreasing, All Industries: Cold Cleaning, Solvents: NEC",
    "2415305000":
        "Solvent Utilization, Degreasing, Furniture and Fixtures (SIC 25): Cold Cleaning, Total: All Solvent Types",
    "2415305300":
        "Solvent Utilization, Degreasing, Furniture and Fixtures (SIC 25): Cold Cleaning, Monochlorobenzene",
    "2415305350":
        "Solvent Utilization, Degreasing, Furniture and Fixtures (SIC 25): Cold Cleaning, Perchloroethylene",
    "2415305370":
        "Solvent Utilization, Degreasing, Furniture and Fixtures (SIC 25): Cold Cleaning, Special Naphthas",
    "2415305385":
        "Solvent Utilization, Degreasing, Furniture and Fixtures (SIC 25): Cold Cleaning, Trichloroethylene",
    "2415305999":
        "Solvent Utilization, Degreasing, Furniture and Fixtures (SIC 25): Cold Cleaning, Solvents: NEC",
    "2415310000":
        "Solvent Utilization, Degreasing, Primary Metal Industries (SIC 33): Cold Cleaning, Total: All Solvent Types",
    "2415310300":
        "Solvent Utilization, Degreasing, Primary Metal Industries (SIC 33): Cold Cleaning, Monochlorobenzene",
    "2415310350":
        "Solvent Utilization, Degreasing, Primary Metal Industries (SIC 33): Cold Cleaning, Perchloroethylene",
    "2415310370":
        "Solvent Utilization, Degreasing, Primary Metal Industries (SIC 33): Cold Cleaning, Special Naphthas",
    "2415310385":
        "Solvent Utilization, Degreasing, Primary Metal Industries (SIC 33): Cold Cleaning, Trichloroethylene",
    "2415310999":
        "Solvent Utilization, Degreasing, Primary Metal Industries (SIC 33): Cold Cleaning, Solvents: NEC",
    "2415315000":
        "Solvent Utilization, Degreasing, Secondary Metal Industries (SIC 33): Cold Cleaning, Total: All Solvent Types",
    "2415315300":
        "Solvent Utilization, Degreasing, Secondary Metal Industries (SIC 33): Cold Cleaning, Monochlorobenzene",
    "2415315350":
        "Solvent Utilization, Degreasing, Secondary Metal Industries (SIC 33): Cold Cleaning, Perchloroethylene",
    "2415315370":
        "Solvent Utilization, Degreasing, Secondary Metal Industries (SIC 33): Cold Cleaning, Special Naphthas",
    "2415315385":
        "Solvent Utilization, Degreasing, Secondary Metal Industries (SIC 33): Cold Cleaning, Trichloroethylene",
    "2415315999":
        "Solvent Utilization, Degreasing, Secondary Metal Industries (SIC 33): Cold Cleaning, Solvents: NEC",
    "2415320000":
        "Solvent Utilization, Degreasing, Fabricated Metal Products (SIC 34): Cold Cleaning, Total: All Solvent Types",
    "2415320300":
        "Solvent Utilization, Degreasing, Fabricated Metal Products (SIC 34): Cold Cleaning, Monochlorobenzene",
    "2415320350":
        "Solvent Utilization, Degreasing, Fabricated Metal Products (SIC 34): Cold Cleaning, Perchloroethylene",
    "2415320370":
        "Solvent Utilization, Degreasing, Fabricated Metal Products (SIC 34): Cold Cleaning, Special Naphthas",
    "2415320385":
        "Solvent Utilization, Degreasing, Fabricated Metal Products (SIC 34): Cold Cleaning, Trichloroethylene",
    "2415320999":
        "Solvent Utilization, Degreasing, Fabricated Metal Products (SIC 34): Cold Cleaning, Solvents: NEC",
    "2415325000":
        "Solvent Utilization, Degreasing, Industrial Machinery and Equipment (SIC 35): Cold Cleaning, Total: All Solvent Types",
    "2415325300":
        "Solvent Utilization, Degreasing, Industrial Machinery and Equipment (SIC 35): Cold Cleaning, Monochlorobenzene",
    "2415325350":
        "Solvent Utilization, Degreasing, Industrial Machinery and Equipment (SIC 35): Cold Cleaning, Perchloroethylene",
    "2415325370":
        "Solvent Utilization, Degreasing, Industrial Machinery and Equipment (SIC 35): Cold Cleaning, Special Naphthas",
    "2415325385":
        "Solvent Utilization, Degreasing, Industrial Machinery and Equipment (SIC 35): Cold Cleaning, Trichloroethylene",
    "2415325999":
        "Solvent Utilization, Degreasing, Industrial Machinery and Equipment (SIC 35): Cold Cleaning, Solvents: NEC",
    "2415330000":
        "Solvent Utilization, Degreasing, Electronic and Other Elec. (SIC 36): Cold Cleaning, Total: All Solvent Types",
    "2415330300":
        "Solvent Utilization, Degreasing, Electronic and Other Elec. (SIC 36): Cold Cleaning, Monochlorobenzene",
    "2415330350":
        "Solvent Utilization, Degreasing, Electronic and Other Elec. (SIC 36): Cold Cleaning, Perchloroethylene",
    "2415330370":
        "Solvent Utilization, Degreasing, Electronic and Other Elec. (SIC 36): Cold Cleaning, Special Naphthas",
    "2415330385":
        "Solvent Utilization, Degreasing, Electronic and Other Elec. (SIC 36): Cold Cleaning, Trichloroethylene",
    "2415330999":
        "Solvent Utilization, Degreasing, Electronic and Other Elec. (SIC 36): Cold Cleaning, Solvents: NEC",
    "2415335000":
        "Solvent Utilization, Degreasing, Transportation Equipment (SIC 37): Cold Cleaning, Total: All Solvent Types",
    "2415335300":
        "Solvent Utilization, Degreasing, Transportation Equipment (SIC 37): Cold Cleaning, Monochlorobenzene",
    "2415335350":
        "Solvent Utilization, Degreasing, Transportation Equipment (SIC 37): Cold Cleaning, Perchloroethylene",
    "2415335370":
        "Solvent Utilization, Degreasing, Transportation Equipment (SIC 37): Cold Cleaning, Special Naphthas",
    "2415335385":
        "Solvent Utilization, Degreasing, Transportation Equipment (SIC 37): Cold Cleaning, Trichloroethylene",
    "2415335999":
        "Solvent Utilization, Degreasing, Transportation Equipment (SIC 37): Cold Cleaning, Solvents: NEC",
    "2415340000":
        "Solvent Utilization, Degreasing, Instruments and Related Products (SIC 38): Cold Cleaning, Total: All Solvent Types",
    "2415340300":
        "Solvent Utilization, Degreasing, Instruments and Related Products (SIC 38): Cold Cleaning, Monochlorobenzene",
    "2415340350":
        "Solvent Utilization, Degreasing, Instruments and Related Products (SIC 38): Cold Cleaning, Perchloroethylene",
    "2415340370":
        "Solvent Utilization, Degreasing, Instruments and Related Products (SIC 38): Cold Cleaning, Special Naphthas",
    "2415340385":
        "Solvent Utilization, Degreasing, Instruments and Related Products (SIC 38): Cold Cleaning, Trichloroethylene",
    "2415340999":
        "Solvent Utilization, Degreasing, Instruments and Related Products (SIC 38): Cold Cleaning, Solvents: NEC",
    "2415345000":
        "Solvent Utilization, Degreasing, Miscellaneous Manufacturing (SIC 39): Cold Cleaning, Total: All Solvent Types",
    "2415345300":
        "Solvent Utilization, Degreasing, Miscellaneous Manufacturing (SIC 39): Cold Cleaning, Monochlorobenzene",
    "2415345350":
        "Solvent Utilization, Degreasing, Miscellaneous Manufacturing (SIC 39): Cold Cleaning, Perchloroethylene",
    "2415345370":
        "Solvent Utilization, Degreasing, Miscellaneous Manufacturing (SIC 39): Cold Cleaning, Special Naphthas",
    "2415345385":
        "Solvent Utilization, Degreasing, Miscellaneous Manufacturing (SIC 39): Cold Cleaning, Trichloroethylene",
    "2415345999":
        "Solvent Utilization, Degreasing, Miscellaneous Manufacturing (SIC 39): Cold Cleaning, Solvents: NEC",
    "2415350000":
        "Solvent Utilization, Degreasing, Transportation Maintenance Facilities (SIC 40-45): Cold Cleaning, Total: All Solvent Types",
    "2415350300":
        "Solvent Utilization, Degreasing, Transportation Maintenance Facilities (SIC 40-45): Cold Cleaning, Monochlorobenzene",
    "2415350350":
        "Solvent Utilization, Degreasing, Transportation Maintenance Facilities (SIC 40-45): Cold Cleaning, Perchloroethylene",
    "2415350370":
        "Solvent Utilization, Degreasing, Transportation Maintenance Facilities (SIC 40-45): Cold Cleaning, Special Naphthas",
    "2415350385":
        "Solvent Utilization, Degreasing, Transportation Maintenance Facilities (SIC 40-45): Cold Cleaning, Trichloroethylene",
    "2415350999":
        "Solvent Utilization, Degreasing, Transportation Maintenance Facilities (SIC 40-45): Cold Cleaning, Solvents: NEC",
    "2415355000":
        "Solvent Utilization, Degreasing, Automotive Dealers (SIC 55): Cold Cleaning, Total: All Solvent Types",
    "2415355300":
        "Solvent Utilization, Degreasing, Automotive Dealers (SIC 55): Cold Cleaning, Monochlorobenzene",
    "2415355350":
        "Solvent Utilization, Degreasing, Automotive Dealers (SIC 55): Cold Cleaning, Perchloroethylene",
    "2415355370":
        "Solvent Utilization, Degreasing, Automotive Dealers (SIC 55): Cold Cleaning, Special Naphthas",
    "2415355385":
        "Solvent Utilization, Degreasing, Automotive Dealers (SIC 55): Cold Cleaning, Trichloroethylene",
    "2415355999":
        "Solvent Utilization, Degreasing, Automotive Dealers (SIC 55): Cold Cleaning, Solvents: NEC",
    "2415360000":
        "Solvent Utilization, Degreasing, Auto Repair Services (SIC 75): Cold Cleaning, Total: All Solvent Types",
    "2415360300":
        "Solvent Utilization, Degreasing, Auto Repair Services (SIC 75): Cold Cleaning, Monochlorobenzene",
    "2415360350":
        "Solvent Utilization, Degreasing, Auto Repair Services (SIC 75): Cold Cleaning, Perchloroethylene",
    "2415360370":
        "Solvent Utilization, Degreasing, Auto Repair Services (SIC 75): Cold Cleaning, Special Naphthas",
    "2415360385":
        "Solvent Utilization, Degreasing, Auto Repair Services (SIC 75): Cold Cleaning, Trichloroethylene",
    "2415360999":
        "Solvent Utilization, Degreasing, Auto Repair Services (SIC 75): Cold Cleaning, Solvents: NEC",
    "2415365000":
        "Solvent Utilization, Degreasing, Miscellaneous Repair Services (SIC 76): Cold Cleaning, Total: All Solvent Types",
    "2415365300":
        "Solvent Utilization, Degreasing, Miscellaneous Repair Services (SIC 76): Cold Cleaning, Monochlorobenzene",
    "2415365350":
        "Solvent Utilization, Degreasing, Miscellaneous Repair Services (SIC 76): Cold Cleaning, Perchloroethylene",
    "2415365370":
        "Solvent Utilization, Degreasing, Miscellaneous Repair Services (SIC 76): Cold Cleaning, Special Naphthas",
    "2415365385":
        "Solvent Utilization, Degreasing, Miscellaneous Repair Services (SIC 76): Cold Cleaning, Trichloroethylene",
    "2415365999":
        "Solvent Utilization, Degreasing, Miscellaneous Repair Services (SIC 76): Cold Cleaning, Solvents: NEC",
    "2420000000":
        "Solvent Utilization, Dry Cleaning, All Processes, Total: All Solvent Types",
    "2420000055":
        "Solvent Utilization, Dry Cleaning, All Processes, Perchloroethylene",
    "2420000370":
        "Solvent Utilization, Dry Cleaning, All Processes, Special Naphthas",
    "2420000999":
        "Solvent Utilization, Dry Cleaning, All Processes, Solvents: NEC",
    "2420010000":
        "Solvent Utilization, Dry Cleaning, Commercial/Industrial Cleaners, Total: All Solvent Types",
    "2420010055":
        "Solvent Utilization, Dry Cleaning, Commercial/Industrial Cleaners, Perchloroethylene",
    "2420010370":
        "Solvent Utilization, Dry Cleaning, Commercial/Industrial Cleaners, Special Naphthas",
    "2420010999":
        "Solvent Utilization, Dry Cleaning, Commercial/Industrial Cleaners, Solvents: NEC",
    "2420020000":
        "Solvent Utilization, Dry Cleaning, Coin-operated Cleaners, Total: All Solvent Types",
    "2420020055":
        "Solvent Utilization, Dry Cleaning, Coin-operated Cleaners, Perchloroethylene",
    "2420020370":
        "Solvent Utilization, Dry Cleaning, Coin-operated Cleaners, Special Naphthas",
    "2420020999":
        "Solvent Utilization, Dry Cleaning, Coin-operated Cleaners, Solvents: NEC",
    "2425000000":
        "Solvent Utilization, Graphic Arts, All Processes, Total: All Solvent Types",
    "2425000055":
        "Solvent Utilization, Graphic Arts, All Processes, Butyl Acetate",
    "2425000370":
        "Solvent Utilization, Graphic Arts, All Processes, Special Naphthas",
    "2425000999":
        "Solvent Utilization, Graphic Arts, All Processes, Solvents: NEC",
    "2425010000":
        "Solvent Utilization, Graphic Arts, Lithography, Total: All Solvent Types",
    "2425010055":
        "Solvent Utilization, Graphic Arts, Lithography, Butyl Acetate",
    "2425010370":
        "Solvent Utilization, Graphic Arts, Lithography, Special Naphthas",
    "2425010999":
        "Solvent Utilization, Graphic Arts, Lithography, Solvents: NEC",
    "2425020000":
        "Solvent Utilization, Graphic Arts, Letterpress, Total: All Solvent Types",
    "2425020055":
        "Solvent Utilization, Graphic Arts, Letterpress, Butyl Acetate",
    "2425020370":
        "Solvent Utilization, Graphic Arts, Letterpress, Special Naphthas",
    "2425020999":
        "Solvent Utilization, Graphic Arts, Letterpress, Solvents: NEC",
    "2425030000":
        "Solvent Utilization, Graphic Arts, Rotogravure, Total: All Solvent Types",
    "2425030055":
        "Solvent Utilization, Graphic Arts, Rotogravure, Butyl Acetate",
    "2425030370":
        "Solvent Utilization, Graphic Arts, Rotogravure, Special Naphthas",
    "2425030999":
        "Solvent Utilization, Graphic Arts, Rotogravure, Solvents: NEC",
    "2425040000":
        "Solvent Utilization, Graphic Arts, Flexography, Total: All Solvent Types",
    "2425040055":
        "Solvent Utilization, Graphic Arts, Flexography, Butyl Acetate",
    "2425040370":
        "Solvent Utilization, Graphic Arts, Flexography, Special Naphthas",
    "2425040999":
        "Solvent Utilization, Graphic Arts, Flexography, Solvents: NEC",
    "2425050000":
        "Solvent Utilization, Graphic Arts, Digital, Total: All Solvent Types",
    "2430000000":
        "Solvent Utilization, Rubber/Plastics, All Processes, Total: All Solvent Types",
    "2430000170":
        "Solvent Utilization, Rubber/Plastics, All Processes, Ethyl Acetate",
    "2430000340":
        "Solvent Utilization, Rubber/Plastics, All Processes, p-Dichlorobenzene",
    "2430000350":
        "Solvent Utilization, Rubber/Plastics, All Processes, Propylene Glycol",
    "2430000370":
        "Solvent Utilization, Rubber/Plastics, All Processes, Special Naphthas",
    "2430000999":
        "Solvent Utilization, Rubber/Plastics, All Processes, Solvents: NEC",
    "2440000000":
        "Solvent Utilization, Miscellaneous Industrial, All Processes, Total: All Solvent Types",
    "2440000060":
        "Solvent Utilization, Miscellaneous Industrial, All Processes, Butyl Alcohols: All Types",
    "2440000065":
        "Solvent Utilization, Miscellaneous Industrial, All Processes, n-Butyl Alcohol",
    "2440000070":
        "Solvent Utilization, Miscellaneous Industrial, All Processes, Isobutyl Alcohol",
    "2440000100":
        "Solvent Utilization, Miscellaneous Industrial, All Processes, Cyclohexanone",
    "2440000125":
        "Solvent Utilization, Miscellaneous Industrial, All Processes, Diethylene Glycol Monobutyl Ether",
    "2440000130":
        "Solvent Utilization, Miscellaneous Industrial, All Processes, Diethylene Glycol Monoethyl Ether",
    "2440000135":
        "Solvent Utilization, Miscellaneous Industrial, All Processes, Diethylene Glycol Monomethyl Ether",
    "2440000165":
        "Solvent Utilization, Miscellaneous Industrial, All Processes, Ethanol",
    "2440000200":
        "Solvent Utilization, Miscellaneous Industrial, All Processes, Ethylene Glycol Monoethyl Ether (2-Ethoxyethanol)",
    "2440000210":
        "Solvent Utilization, Miscellaneous Industrial, All Processes, Ethylene Glycol Monomethyl Ether (2-Methoxyethanol)",
    "2440000215":
        "Solvent Utilization, Miscellaneous Industrial, All Processes, Ethylene Glycol Monobutyl Ether (2-Butoxyethanol)",
    "2440000235":
        "Solvent Utilization, Miscellaneous Industrial, All Processes, Glycol Ethers: All Types",
    "2440000250":
        "Solvent Utilization, Miscellaneous Industrial, All Processes, Isopropanol",
    "2440000260":
        "Solvent Utilization, Miscellaneous Industrial, All Processes, Methanol",
    "2440000275":
        "Solvent Utilization, Miscellaneous Industrial, All Processes, Methyl Ethyl Ketone",
    "2440000285":
        "Solvent Utilization, Miscellaneous Industrial, All Processes, Methyl Isobutyl Ketone",
    "2440000300":
        "Solvent Utilization, Miscellaneous Industrial, All Processes, Monochlorobenzene",
    "2440000330":
        "Solvent Utilization, Miscellaneous Industrial, All Processes, o-Dichlorobenzene",
    "2440000350":
        "Solvent Utilization, Miscellaneous Industrial, All Processes, Propylene Glycol",
    "2440000370":
        "Solvent Utilization, Miscellaneous Industrial, All Processes, Special Naphthas",
    "2440000999":
        "Solvent Utilization, Miscellaneous Industrial, All Processes, Solvents: NEC",
    "2440020000":
        "Solvent Utilization, Miscellaneous Industrial, Adhesive (Industrial) Application, Total: All Solvent Types",
    "2460000000":
        "Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, All Processes, Total: All Solvent Types",
    "2460000030":
        "Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, All Processes, Acetone",
    "2460000055":
        "Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, All Processes, Butyl Acetate",
    "2460000060":
        "Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, All Processes, Butyl Alcohols: All Types",
    "2460000065":
        "Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, All Processes, n-Butyl Alcohol",
    "2460000070":
        "Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, All Processes, Isobutyl Alcohol",
    "2460000165":
        "Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, All Processes, Ethanol",
    "2460000170":
        "Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, All Processes, Ethyl Acetate",
    "2460000185":
        "Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, All Processes, Ethylbenzene",
    "2460000250":
        "Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, All Processes, Isopropanol",
    "2460000260":
        "Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, All Processes, Methanol",
    "2460000285":
        "Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, All Processes, Methyl Isobutyl Ketone",
    "2460000300":
        "Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, All Processes, Monochlorobenzene",
    "2460000330":
        "Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, All Processes, o-Dichlorobenzene",
    "2460000340":
        "Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, All Processes, p-Dichlorobenzene",
    "2460000345":
        "Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, All Processes, Perchloroethylene",
    "2460000350":
        "Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, All Processes, Propylene Glycol",
    "2460000370":
        "Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, All Processes, Special Naphthas",
    "2460000385":
        "Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, All Processes, Trichloroethylene",
    "2460000999":
        "Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, All Processes, Solvents: NEC",
    "2460030999":
        "Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, Lighter Fluid, Fire Starter, Other Fuels, Total: All Volatile Chemical Product Types",
    "2460100000":
        "Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, All Personal Care Products, Total: All Solvent Types",
    "2460110000":
        "Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, Personal Care Products: Hair Care Products, Total: All Solvent Types",
    "2460120000":
        "Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, Personal Care Products: Deodorants and Antiperspirants, Total: All Solvent Types",
    "2460130000":
        "Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, Personal Care Products: Fragrance Products, Total: All Solvent Types",
    "2460140000":
        "Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, Personal Care Products: Powders, Total: All Solvent Types",
    "2460150000":
        "Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, Personal Care Products: Nail Care Products, Total: All Solvent Types",
    "2460160000":
        "Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, Personal Care Products: Facial and Body Treatments, Total: All Solvent Types",
    "2460170000":
        "Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, Personal Care Products: Oral Care Products, Total: All Solvent Types",
    "2460180000":
        "Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, Personal Care Products: Health Use Products (External Only), Total: All Solvent Types",
    "2460190000":
        "Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, Personal Care Products: Miscellaneous Personal Care Products, Total: All Solvent Types",
    "2460200000":
        "Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, All Household Products, Total: All Solvent Types",
    "2460210000":
        "Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, Household Products: Hard Surface Cleaners, Total: All Solvent Types",
    "2460220000":
        "Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, Household Products: Laundry Products, Total: All Solvent Types",
    "2460230000":
        "Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, Household Products: Fabric and Carpet Care Products, Total: All Solvent Types",
    "2460240000":
        "Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, Household Products: Dishwashing Products, Total: All Solvent Types",
    "2460250000":
        "Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, Household Products: Waxes and Polishes, Total: All Solvent Types",
    "2460260000":
        "Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, Household Products: Air Fresheners, Total: All Solvent Types",
    "2460270000":
        "Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, Household Products: Shoe and Leather Care Products, Total: All Solvent Types",
    "2460290000":
        "Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, Household Products: Miscellaneous Household Products, Total: All Solvent Types",
    "2460400000":
        "Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, All Automotive Aftermarket Products, Total: All Solvent Types",
    "2460410000":
        "Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, Automotive Aftermarket Products: Detailing Products, Total: All Solvent Types",
    "2460420000":
        "Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, Automotive Aftermarket Products: Maintenance and Repair Products, Total: All Solvent Types",
    "2460500000":
        "Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, All Coatings and Related Products, Total: All Solvent Types",
    "2460510000":
        "Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, Coatings and Related Products: Aerosol Spray Paints, Total: All Solvent Types",
    "2460520000":
        "Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, Coatings and Related Products: Coating Related Products, Total: All Solvent Types",
    "2460600000":
        "Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, All Adhesives and Sealants, Total: All Solvent Types",
    "2460610000":
        "Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, Adhesives and Sealants: Adhesives, Total: All Solvent Types",
    "2460620000":
        "Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, Adhesives and Sealants: Sealants, Total: All Solvent Types",
    "2460800000":
        "Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, All FIFRA Related Products, Total: All Solvent Types",
    "2460810000":
        "Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, FIFRA Related Products: Insecticides, Total: All Solvent Types",
    "2460820000":
        "Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, FIFRA Related Products: Fungicides and Nematicides, Total: All Solvent Types",
    "2460830000":
        "Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, FIFRA Related Products: Herbicides, Total: All Solvent Types",
    "2460840000":
        "Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, FIFRA Related Products: Antimicrobial Agents, Total: All Solvent Types",
    "2460890000":
        "Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, FIFRA Related Products: Other FIFRA Related Products, Total: All Solvent Types",
    "2460900000":
        "Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, Miscellaneous Products (Not Otherwise Covered), Total: All Solvent Types",
    "2460910000":
        "Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, Miscellaneous Products: Arts and Crafts Supplies, Total: All Solvent Types",
    "2460920000":
        "Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, Miscellaneous Products: Non-Pesticidal Veterinary and Pet Products, Total: All Solvent Types",
    "2460930000":
        "Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, Miscellaneous Products: Pressurized Food Products, Total: All Solvent Types",
    "2460940000":
        "Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, Miscellaneous Products: Office Supplies, Total: All Solvent Types",
    "2461000000":
        "Solvent Utilization, Miscellaneous Non-industrial: Commercial, All Processes, Total: All Solvent Types",
    "2461020000":
        "Solvent Utilization, Miscellaneous Non-industrial: Commercial, Asphalt Application: All Processes, Total: All Solvent Types",
    "2461020370":
        "Solvent Utilization, Miscellaneous Non-industrial: Commercial, Asphalt Application: All Processes, Special Naphthas",
    "2461020999":
        "Solvent Utilization, Miscellaneous Non-industrial: Commercial, Asphalt Application: All Processes, Solvents: NEC",
    "2461021000":
        "Solvent Utilization, Miscellaneous Non-industrial: Commercial, Cutback Asphalt, Total: All Solvent Types",
    "2461021370":
        "Solvent Utilization, Miscellaneous Non-industrial: Commercial, Cutback Asphalt, Special Naphthas",
    "2461021999":
        "Solvent Utilization, Miscellaneous Non-industrial: Commercial, Cutback Asphalt, Solvents: NEC",
    "2461022000":
        "Solvent Utilization, Miscellaneous Non-industrial: Commercial, Emulsified Asphalt, Total: All Solvent Types",
    "2461022370":
        "Solvent Utilization, Miscellaneous Non-industrial: Commercial, Emulsified Asphalt, Special Naphthas",
    "2461022999":
        "Solvent Utilization, Miscellaneous Non-industrial: Commercial, Emulsified Asphalt, Solvents: NEC",
    "2461023000":
        "Solvent Utilization, Miscellaneous Non-industrial: Commercial, Asphalt Roofing, Total: All Solvent Types",
    "2461023370":
        "Solvent Utilization, Miscellaneous Non-industrial: Commercial, Asphalt Roofing, Special Naphthas",
    "2461023999":
        "Solvent Utilization, Miscellaneous Non-industrial: Commercial, Asphalt Roofing, Solvents: NEC",
    "2461024000":
        "Solvent Utilization, Miscellaneous Non-industrial: Commercial, Asphalt Pipe Coating, Total: All Solvent Types",
    "2461024370":
        "Solvent Utilization, Miscellaneous Non-industrial: Commercial, Asphalt Pipe Coating, Special Naphthas",
    "2461024999":
        "Solvent Utilization, Miscellaneous Non-industrial: Commercial, Asphalt Pipe Coating, Solvents: NEC",
    "2461025000":
        "Solvent Utilization, Miscellaneous Non-industrial: Commercial, Asphalt Paving: Hot and Warm Mix, Hot and Warm Mix Total: All Solvent Types",
    "2461025100":
        "Solvent Utilization, Miscellaneous Non-industrial: Commercial, Asphalt Paving: Hot and Warm Mix, Hot Mix Total: All Solvent Types",
    "2461025200":
        "Solvent Utilization, Miscellaneous Non-industrial: Commercial, Asphalt Paving: Hot and Warm Mix, Warm Mix Total: All Solvent Types",
    "2461026000":
        "Solvent Utilization, Miscellaneous Non-industrial: Commercial, Asphalt Paving: Road Oil, Total: All Solvent Types",
    "2461030999":
        "Solvent Utilization, Miscellaneous Non-industrial: Consumer and Commercial, Lighter Fluid, Fire Starter, Other Fuels, Total: All Volatile Chemical Product Types",
    "2461050000":
        "Solvent Utilization, Miscellaneous Non-industrial: Commercial, Film Roofing: All Processes, Total: All Solvent Types",
    "2461100000":
        "Solvent Utilization, Miscellaneous Non-industrial: Commercial, Solvent Reclamation: All Processes, Total: All Solvent Types",
    "2461160000":
        "Solvent Utilization, Miscellaneous Non-industrial: Commercial, Tank/Drum Cleaning: All Processes, Total: All Solvent Types",
    "2461200000":
        "Solvent Utilization, Miscellaneous Non-industrial: Commercial, Adhesives and Sealants, Total: All Solvent Types",
    "2461800000":
        "Solvent Utilization, Miscellaneous Non-industrial: Commercial, Pesticide Application: All Processes, Total: All Solvent Types",
    "2461800001":
        "Solvent Utilization, Miscellaneous Non-industrial: Commercial, Pesticide Application: All Processes, Surface Application",
    "2461800002":
        "Solvent Utilization, Miscellaneous Non-industrial: Commercial, Pesticide Application: All Processes, Soil Incorporation",
    "2461800999":
        "Solvent Utilization, Miscellaneous Non-industrial: Commercial, Pesticide Application: All Processes, Solvents: NEC",
    "2461850000":
        "Solvent Utilization, Miscellaneous Non-industrial: Commercial, Pesticide Application: Agricultural, All Processes",
    "2461850001":
        "Solvent Utilization, Miscellaneous Non-industrial: Commercial, Pesticide Application: Agricultural, Herbicides, Corn",
    "2461850002":
        "Solvent Utilization, Miscellaneous Non-industrial: Commercial, Pesticide Application: Agricultural, Herbicides, Apples",
    "2461850003":
        "Solvent Utilization, Miscellaneous Non-industrial: Commercial, Pesticide Application: Agricultural, Herbicides, Grapes",
    "2461850004":
        "Solvent Utilization, Miscellaneous Non-industrial: Commercial, Pesticide Application: Agricultural, Herbicides, Potatoes",
    "2461850005":
        "Solvent Utilization, Miscellaneous Non-industrial: Commercial, Pesticide Application: Agricultural, Herbicides, Soy Beans",
    "2461850006":
        "Solvent Utilization, Miscellaneous Non-industrial: Commercial, Pesticide Application: Agricultural, Herbicides, Hay & Grains",
    "2461850009":
        "Solvent Utilization, Miscellaneous Non-industrial: Commercial, Pesticide Application: Agricultural, Herbicides, Not Elsewhere Classified",
    "2461850051":
        "Solvent Utilization, Miscellaneous Non-industrial: Commercial, Pesticide Application: Agricultural, Other Pesticides, Corn",
    "2461850052":
        "Solvent Utilization, Miscellaneous Non-industrial: Commercial, Pesticide Application: Agricultural, Other Pesticides, Apples",
    "2461850053":
        "Solvent Utilization, Miscellaneous Non-industrial: Commercial, Pesticide Application: Agricultural, Other Pesticides, Grapes",
    "2461850054":
        "Solvent Utilization, Miscellaneous Non-industrial: Commercial, Pesticide Application: Agricultural, Other Pesticides, Potatoes",
    "2461850055":
        "Solvent Utilization, Miscellaneous Non-industrial: Commercial, Pesticide Application: Agricultural, Other Pesticides, Soy Beans",
    "2461850056":
        "Solvent Utilization, Miscellaneous Non-industrial: Commercial, Pesticide Application: Agricultural, Other Pesticides, Hay & Grains",
    "2461850099":
        "Solvent Utilization, Miscellaneous Non-industrial: Commercial, Pesticide Application: Agricultural, Other Pesticides, Not Elsewhere Classified",
    "2461870999":
        "Solvent Utilization, Miscellaneous Non-industrial: Commercial, Pesticide Application: Non-Agricultural, Not Elsewhere Classified",
    "2461900000":
        "Solvent Utilization, Miscellaneous Non-industrial: Commercial, Miscellaneous Products: NEC, Total: All Solvent Types",
    "2465000000":
        "Solvent Utilization, Miscellaneous Non-industrial: Consumer, All Products/Processes, Total: All Solvent Types",
    "2465000030":
        "Solvent Utilization, Miscellaneous Non-industrial: Consumer, All Products/Processes, Acetone",
    "2465000055":
        "Solvent Utilization, Miscellaneous Non-industrial: Consumer, All Products/Processes, Butyl Acetate",
    "2465000060":
        "Solvent Utilization, Miscellaneous Non-industrial: Consumer, All Products/Processes, Butyl Alcohols: All Types",
    "2465000065":
        "Solvent Utilization, Miscellaneous Non-industrial: Consumer, All Products/Processes, n-Butyl Alcohol",
    "2465000070":
        "Solvent Utilization, Miscellaneous Non-industrial: Consumer, All Products/Processes, Isobutyl Alcohol",
    "2465000165":
        "Solvent Utilization, Miscellaneous Non-industrial: Consumer, All Products/Processes, Ethanol",
    "2465000170":
        "Solvent Utilization, Miscellaneous Non-industrial: Consumer, All Products/Processes, Ethyl Acetate",
    "2465000185":
        "Solvent Utilization, Miscellaneous Non-industrial: Consumer, All Products/Processes, Ethylbenzene",
    "2465000250":
        "Solvent Utilization, Miscellaneous Non-industrial: Consumer, All Products/Processes, Isopropanol",
    "2465000260":
        "Solvent Utilization, Miscellaneous Non-industrial: Consumer, All Products/Processes, Methanol",
    "2465000285":
        "Solvent Utilization, Miscellaneous Non-industrial: Consumer, All Products/Processes, Methyl Isobutyl Ketone",
    "2465000300":
        "Solvent Utilization, Miscellaneous Non-industrial: Consumer, All Products/Processes, Monochlorobenzene",
    "2465000330":
        "Solvent Utilization, Miscellaneous Non-industrial: Consumer, All Products/Processes, o-Dichlorobenzene",
    "2465000340":
        "Solvent Utilization, Miscellaneous Non-industrial: Consumer, All Products/Processes, p-Dichlorobenzene",
    "2465000345":
        "Solvent Utilization, Miscellaneous Non-industrial: Consumer, All Products/Processes, Perchloroethylene",
    "2465000350":
        "Solvent Utilization, Miscellaneous Non-industrial: Consumer, All Products/Processes, Propylene Glycol",
    "2465000370":
        "Solvent Utilization, Miscellaneous Non-industrial: Consumer, All Products/Processes, Special Naphthas",
    "2465000385":
        "Solvent Utilization, Miscellaneous Non-industrial: Consumer, All Products/Processes, Trichloroethylene",
    "2465000999":
        "Solvent Utilization, Miscellaneous Non-industrial: Consumer, All Products/Processes, Solvents: NEC",
    "2465100000":
        "Solvent Utilization, Miscellaneous Non-industrial: Consumer, Personal Care Products, Total: All Solvent Types",
    "2465200000":
        "Solvent Utilization, Miscellaneous Non-industrial: Consumer, Household Products, Total: All Solvent Types",
    "2465400000":
        "Solvent Utilization, Miscellaneous Non-industrial: Consumer, Automotive Aftermarket Products, Total: All Solvent Types",
    "2465600000":
        "Solvent Utilization, Miscellaneous Non-industrial: Consumer, Adhesives and Sealants, Total: All Solvent Types",
    "2465800000":
        "Solvent Utilization, Miscellaneous Non-industrial: Consumer, Pesticide Application, Total: All Solvent Types",
    "2465900000":
        "Solvent Utilization, Miscellaneous Non-industrial: Consumer, Miscellaneous Products: NEC, Total: All Solvent Types",
    "2495000000":
        "Solvent Utilization, All Solvent User Categories, All Processes, Total: All Solvent Types",
    "2495000001":
        "Solvent Utilization, All Solvent User Categories, All Processes, 1,2,4-Trichlorobenzene",
    "2495000005":
        "Solvent Utilization, All Solvent User Categories, All Processes, 1,2-Dichloroethane",
    "2495000010":
        "Solvent Utilization, All Solvent User Categories, All Processes, 1-Hexane",
    "2495000015":
        "Solvent Utilization, All Solvent User Categories, All Processes, 2-Butoxyethanol",
    "2495000020":
        "Solvent Utilization, All Solvent User Categories, All Processes, 2-Ethylhexanol",
    "2495000025":
        "Solvent Utilization, All Solvent User Categories, All Processes, Acetal and Other Aroma Chemicals",
    "2495000030":
        "Solvent Utilization, All Solvent User Categories, All Processes, Acetone",
    "2495000035":
        "Solvent Utilization, All Solvent User Categories, All Processes, Acetonitrile",
    "2495000040":
        "Solvent Utilization, All Solvent User Categories, All Processes, Amyl Alcohols (Mixed)",
    "2495000045":
        "Solvent Utilization, All Solvent User Categories, All Processes, Benzyl Alcohol",
    "2495000050":
        "Solvent Utilization, All Solvent User Categories, All Processes, Butyl Benzoate",
    "2495000055":
        "Solvent Utilization, All Solvent User Categories, All Processes, Butyl Acetate",
    "2495000060":
        "Solvent Utilization, All Solvent User Categories, All Processes, Butyl Alcohols: All Types",
    "2495000065":
        "Solvent Utilization, All Solvent User Categories, All Processes, n-Butyl Alcohol",
    "2495000070":
        "Solvent Utilization, All Solvent User Categories, All Processes, Isobutyl Alcohol",
    "2495000075":
        "Solvent Utilization, All Solvent User Categories, All Processes, Carbon Disulfide",
    "2495000080":
        "Solvent Utilization, All Solvent User Categories, All Processes, Chlorobenzene",
    "2495000085":
        "Solvent Utilization, All Solvent User Categories, All Processes, Chlorofluorocarbons: General",
    "2495000090":
        "Solvent Utilization, All Solvent User Categories, All Processes, Chloroform",
    "2495000095":
        "Solvent Utilization, All Solvent User Categories, All Processes, Cresylic Acid",
    "2495000100":
        "Solvent Utilization, All Solvent User Categories, All Processes, Cyclohexanone",
    "2495000105":
        "Solvent Utilization, All Solvent User Categories, All Processes, Decanol",
    "2495000110":
        "Solvent Utilization, All Solvent User Categories, All Processes, Diacetone Alcohol",
    "2495000115":
        "Solvent Utilization, All Solvent User Categories, All Processes, Diethylamine",
    "2495000120":
        "Solvent Utilization, All Solvent User Categories, All Processes, Diethylene Glycol",
    "2495000125":
        "Solvent Utilization, All Solvent User Categories, All Processes, Diethylene Glycol Monobutyl Ether",
    "2495000130":
        "Solvent Utilization, All Solvent User Categories, All Processes, Diethylene Glycol Monoethyl Ether",
    "2495000135":
        "Solvent Utilization, All Solvent User Categories, All Processes, Diethylene Glycol Monomethyl Ether",
    "2495000140":
        "Solvent Utilization, All Solvent User Categories, All Processes, Dimethyl Acetamide",
    "2495000145":
        "Solvent Utilization, All Solvent User Categories, All Processes, Dimethylamine",
    "2495000150":
        "Solvent Utilization, All Solvent User Categories, All Processes, Dimethylformanide",
    "2495000155":
        "Solvent Utilization, All Solvent User Categories, All Processes, Dipropylene Glycol",
    "2495000160":
        "Solvent Utilization, All Solvent User Categories, All Processes, Dipropylene Glycol Monomethyl Ether",
    "2495000165":
        "Solvent Utilization, All Solvent User Categories, All Processes, Ethanol",
    "2495000170":
        "Solvent Utilization, All Solvent User Categories, All Processes, Ethyl Acetate",
    "2495000175":
        "Solvent Utilization, All Solvent User Categories, All Processes, Ethyl Chloride (Chloroethane)",
    "2495000180":
        "Solvent Utilization, All Solvent User Categories, All Processes, Ethyl Ether",
    "2495000185":
        "Solvent Utilization, All Solvent User Categories, All Processes, Ethylbenzene",
    "2495000190":
        "Solvent Utilization, All Solvent User Categories, All Processes, Ethylene Dibromide",
    "2495000195":
        "Solvent Utilization, All Solvent User Categories, All Processes, Ethylene Glycol",
    "2495000200":
        "Solvent Utilization, All Solvent User Categories, All Processes, Ethylene Glycol Monoethyl Ether (2-Ethoxyethanol)",
    "2495000205":
        "Solvent Utilization, All Solvent User Categories, All Processes, Ethylene Glycol Monoethyl Ether Acetate",
    "2495000210":
        "Solvent Utilization, All Solvent User Categories, All Processes, Ethylene Glycol Monomethyl Ether (2-Methoxyethanol)",
    "2495000215":
        "Solvent Utilization, All Solvent User Categories, All Processes, Ethylene Glycol Monobutyl Ether (2-Butoxyethanol)",
    "2495000220":
        "Solvent Utilization, All Solvent User Categories, All Processes, Formalin",
    "2495000225":
        "Solvent Utilization, All Solvent User Categories, All Processes, Formic Acid",
    "2495000230":
        "Solvent Utilization, All Solvent User Categories, All Processes, Furfural",
    "2495000235":
        "Solvent Utilization, All Solvent User Categories, All Processes, Glycol Ethers: All Types",
    "2495000240":
        "Solvent Utilization, All Solvent User Categories, All Processes, Gum Turpentine",
    "2495000245":
        "Solvent Utilization, All Solvent User Categories, All Processes, Isobutyl Acetate",
    "2495000250":
        "Solvent Utilization, All Solvent User Categories, All Processes, Isopropanol",
    "2495000255":
        "Solvent Utilization, All Solvent User Categories, All Processes, Isopropyl/n-Propyl Acetate",
    "2495000260":
        "Solvent Utilization, All Solvent User Categories, All Processes, Methanol",
    "2495000265":
        "Solvent Utilization, All Solvent User Categories, All Processes, Methyl Chloride",
    "2495000270":
        "Solvent Utilization, All Solvent User Categories, All Processes, Methyl Chloroform",
    "2495000275":
        "Solvent Utilization, All Solvent User Categories, All Processes, Methyl Ethyl Ketone",
    "2495000280":
        "Solvent Utilization, All Solvent User Categories, All Processes, Methyl Isobutyl Carbinol",
    "2495000285":
        "Solvent Utilization, All Solvent User Categories, All Processes, Methyl Isobutyl Ketone",
    "2495000290":
        "Solvent Utilization, All Solvent User Categories, All Processes, Methylamine",
    "2495000295":
        "Solvent Utilization, All Solvent User Categories, All Processes, Methylene Chloride",
    "2495000300":
        "Solvent Utilization, All Solvent User Categories, All Processes, Monochlorobenzene",
    "2495000305":
        "Solvent Utilization, All Solvent User Categories, All Processes, n-Methyl-2-Pyrrolidone",
    "2495000310":
        "Solvent Utilization, All Solvent User Categories, All Processes, n-Propanol",
    "2495000315":
        "Solvent Utilization, All Solvent User Categories, All Processes, Naphthenic Acids",
    "2495000320":
        "Solvent Utilization, All Solvent User Categories, All Processes, Nitrobenzene",
    "2495000325":
        "Solvent Utilization, All Solvent User Categories, All Processes, o-, m-, and p-Cresol",
    "2495000330":
        "Solvent Utilization, All Solvent User Categories, All Processes, o-Dichlorobenzene",
    "2495000335":
        "Solvent Utilization, All Solvent User Categories, All Processes, Oxalic Acid",
    "2495000340":
        "Solvent Utilization, All Solvent User Categories, All Processes, p-Dichlorobenzene",
    "2495000345":
        "Solvent Utilization, All Solvent User Categories, All Processes, Perchloroethylene",
    "2495000350":
        "Solvent Utilization, All Solvent User Categories, All Processes, Propylene Glycol",
    "2495000355":
        "Solvent Utilization, All Solvent User Categories, All Processes, Propylene Glycol Monomethyl Ether",
    "2495000360":
        "Solvent Utilization, All Solvent User Categories, All Processes, Propylene Glycol Monomethyl Ether Acetate",
    "2495000365":
        "Solvent Utilization, All Solvent User Categories, All Processes, Pyridine",
    "2495000370":
        "Solvent Utilization, All Solvent User Categories, All Processes, Special Naphthas",
    "2495000375":
        "Solvent Utilization, All Solvent User Categories, All Processes, Tetrahydrofuran",
    "2495000380":
        "Solvent Utilization, All Solvent User Categories, All Processes, Toluene",
    "2495000385":
        "Solvent Utilization, All Solvent User Categories, All Processes, Trichloroethylene",
    "2495000390":
        "Solvent Utilization, All Solvent User Categories, All Processes, Trichlorotrifluoroethane (Freon 113)",
    "2495000395":
        "Solvent Utilization, All Solvent User Categories, All Processes, Triethylamine",
    "2495000400":
        "Solvent Utilization, All Solvent User Categories, All Processes, Triethylene Glycol",
    "2495000405":
        "Solvent Utilization, All Solvent User Categories, All Processes, Xylenes (Mixed)",
    "2495000999":
        "Solvent Utilization, All Solvent User Categories, All Processes, Solvents: NEC",
    "2101001000":
        "Stationary Source Fuel Combustion, Electric Utility, Anthracite Coal, Total: All Boiler Types",
    "2101002000":
        "Stationary Source Fuel Combustion, Electric Utility, Bituminous/Subbituminous Coal, Total: All Boiler Types",
    "2101003000":
        "Stationary Source Fuel Combustion, Electric Utility, Lignite Coal, Total: All Boiler Types",
    "2101004000":
        "Stationary Source Fuel Combustion, Electric Utility, Distillate Oil, Total: Boilers and IC Engines",
    "2101004001":
        "Stationary Source Fuel Combustion, Electric Utility, Distillate Oil, All Boiler Types",
    "2101004002":
        "Stationary Source Fuel Combustion, Electric Utility, Distillate Oil, All IC Engine Types",
    "2101005000":
        "Stationary Source Fuel Combustion, Electric Utility, Residual Oil, Total: All Boiler Types",
    "2101006000":
        "Stationary Source Fuel Combustion, Electric Utility, Natural Gas, Total: Boilers and IC Engines",
    "2101006001":
        "Stationary Source Fuel Combustion, Electric Utility, Natural Gas, All Boiler Types",
    "2101006002":
        "Stationary Source Fuel Combustion, Electric Utility, Natural Gas, All IC Engine Types",
    "2101007000":
        "Stationary Source Fuel Combustion, Electric Utility, Liquified Petroleum Gas (LPG), Total: All Boiler Types",
    "2101008000":
        "Stationary Source Fuel Combustion, Electric Utility, Wood, Total: All Boiler Types",
    "2101009000":
        "Stationary Source Fuel Combustion, Electric Utility, Petroleum Coke, Total: All Boiler Types",
    "2101010000":
        "Stationary Source Fuel Combustion, Electric Utility, Process Gas, Total: All Boiler Types",
    "2102001000":
        "Stationary Source Fuel Combustion, Industrial, Anthracite Coal, Total: All Boiler Types",
    "2102002000":
        "Stationary Source Fuel Combustion, Industrial, Bituminous/Subbituminous Coal, Total: All Boiler Types",
    "2102004000":
        "Stationary Source Fuel Combustion, Industrial, Distillate Oil, Total: Boilers and IC Engines",
    "2102004001":
        "Stationary Source Fuel Combustion, Industrial, Distillate Oil, All Boiler Types",
    "2102004002":
        "Stationary Source Fuel Combustion, Industrial, Distillate Oil, All IC Engine Types",
    "2102005000":
        "Stationary Source Fuel Combustion, Industrial, Residual Oil, Total: All Boiler Types",
    "2102006000":
        "Stationary Source Fuel Combustion, Industrial, Natural Gas, Total: Boilers and IC Engines",
    "2102006001":
        "Stationary Source Fuel Combustion, Industrial, Natural Gas, All Boiler Types",
    "2102006002":
        "Stationary Source Fuel Combustion, Industrial, Natural Gas, All IC Engine Types",
    "2102007000":
        "Stationary Source Fuel Combustion, Industrial, Liquified Petroleum Gas (LPG), Total: All Boiler Types",
    "2102008000":
        "Stationary Source Fuel Combustion, Industrial, Wood, Total: All Boiler Types",
    "2102009000":
        "Stationary Source Fuel Combustion, Industrial, Petroleum Coke, Total: All Boiler Types",
    "2102010000":
        "Stationary Source Fuel Combustion, Industrial, Process Gas, Total: All Boiler Types",
    "2102011000":
        "Stationary Source Fuel Combustion, Industrial, Kerosene, Total: All Boiler Types",
    "2102012000":
        "Stationary Source Fuel Combustion, Industrial, Waste oil, Total",
    "2103001000":
        "Stationary Source Fuel Combustion, Commercial/Institutional, Anthracite Coal, Total: All Boiler Types",
    "2103002000":
        "Stationary Source Fuel Combustion, Commercial/Institutional, Bituminous/Subbituminous Coal, Total: All Boiler Types",
    "2103004000":
        "Stationary Source Fuel Combustion, Commercial/Institutional, Distillate Oil, Total: Boilers and IC Engines",
    "2103004001":
        "Stationary Source Fuel Combustion, Commercial/Institutional, Distillate Oil, Boilers",
    "2103004002":
        "Stationary Source Fuel Combustion, Commercial/Institutional, Distillate Oil, IC Engines",
    "2103005000":
        "Stationary Source Fuel Combustion, Commercial/Institutional, Residual Oil, Total: All Boiler Types",
    "2103006000":
        "Stationary Source Fuel Combustion, Commercial/Institutional, Natural Gas, Total: Boilers and IC Engines",
    "2103007000":
        "Stationary Source Fuel Combustion, Commercial/Institutional, Liquified Petroleum Gas (LPG), Total: All Combustor Types",
    "2103007005":
        "Stationary Source Fuel Combustion, Commercial/Institutional, Liquified Petroleum Gas (LPG), All Boiler Types",
    "2103007010":
        "Stationary Source Fuel Combustion, Commercial/Institutional, Liquified Petroleum Gas (LPG), Asphalt Kettle Heaters",
    "2103008000":
        "Stationary Source Fuel Combustion, Commercial/Institutional, Wood, Total: All Boiler Types",
    "2103010000":
        "Stationary Source Fuel Combustion, Commercial/Institutional, Process Gas, POTW Digester Gas-fired Boilers",
    "2103011000":
        "Stationary Source Fuel Combustion, Commercial/Institutional, Kerosene, Total: All Combustor Types",
    "2103011005":
        "Stationary Source Fuel Combustion, Commercial/Institutional, Kerosene, All Boiler Types",
    "2103011010":
        "Stationary Source Fuel Combustion, Commercial/Institutional, Kerosene, Asphalt Kettle Heaters",
    "2104001000":
        "Stationary Source Fuel Combustion, Residential, Anthracite Coal, Total: All Combustor Types",
    "2104002000":
        "Stationary Source Fuel Combustion, Residential, Bituminous/Subbituminous Coal, Total: All Combustor Types",
    "2104004000":
        "Stationary Source Fuel Combustion, Residential, Distillate Oil, Total: All Combustor Types",
    "2104005000":
        "Stationary Source Fuel Combustion, Residential, Residual Oil, Total: All Combustor Types",
    "2104006000":
        "Stationary Source Fuel Combustion, Residential, Natural Gas, Total: All Combustor Types",
    "2104006010":
        "Stationary Source Fuel Combustion, Residential, Natural Gas, Residential Furnaces",
    "2104007000":
        "Stationary Source Fuel Combustion, Residential, Liquified Petroleum Gas (LPG), Total: All Combustor Types",
    "2104008000":
        "Stationary Source Fuel Combustion, Residential, Wood, Total: Woodstoves and Fireplaces",
    "2104008001":
        "Stationary Source Fuel Combustion, Residential, Wood, Fireplace: general",
    "2104008002":
        "Stationary Source Fuel Combustion, Residential, Wood, Fireplaces: Insert; non-EPA certified",
    "2104008003":
        "Stationary Source Fuel Combustion, Residential, Wood, Fireplaces: Insert; EPA certified; non-catalytic",
    "2104008004":
        "Stationary Source Fuel Combustion, Residential, Wood, Fireplaces: Insert; EPA certified; catalytic",
    "2104008010":
        "Stationary Source Fuel Combustion, Residential, Wood, Woodstoves: General",
    "2104008030":
        "Stationary Source Fuel Combustion, Residential, Wood, Catalytic Woodstoves: General",
    "2104008050":
        "Stationary Source Fuel Combustion, Residential, Wood, Non-catalytic Woodstoves: EPA certified",
    "2104008051":
        "Stationary Source Fuel Combustion, Residential, Wood, Non-catalytic Woodstoves: Non-EPA certified",
    "2104008052":
        "Stationary Source Fuel Combustion, Residential, Wood, Non-catalytic Woodstoves: Low Emitting",
    "2104008053":
        "Stationary Source Fuel Combustion, Residential, Wood, Non-catalytic Woodstoves: Pellet Fired",
    "2104008070":
        "Stationary Source Fuel Combustion, Residential, Wood, Outdoor Wood Burning Equipment",
    "2104008100":
        "Stationary Source Fuel Combustion, Residential, Wood, Fireplace: general",
    "2104008110":
        "Stationary Source Fuel Combustion, Residential, Wood, Fireplace: open",
    "2104008120":
        "Stationary Source Fuel Combustion, Residential, Wood, Fireplace: enclosed (or otherwise modified)",
    "2104008130":
        "Stationary Source Fuel Combustion, Residential, Wood, Fireplace: qualified for EPA voluntary program",
    "2104008200":
        "Stationary Source Fuel Combustion, Residential, Wood, Woodstove: fireplace inserts; general",
    "2104008210":
        "Stationary Source Fuel Combustion, Residential, Wood, Woodstove: fireplace inserts; non-EPA certified",
    "2104008220":
        "Stationary Source Fuel Combustion, Residential, Wood, Woodstove: fireplace inserts; EPA certified; non-catalytic",
    "2104008230":
        "Stationary Source Fuel Combustion, Residential, Wood, Woodstove: fireplace inserts; EPA certified; catalytic",
    "2104008300":
        "Stationary Source Fuel Combustion, Residential, Wood, Woodstove: freestanding, general",
    "2104008310":
        "Stationary Source Fuel Combustion, Residential, Wood, Woodstove: freestanding, non-EPA certified",
    "2104008320":
        "Stationary Source Fuel Combustion, Residential, Wood, Woodstove: freestanding, EPA certified, non-catalytic",
    "2104008330":
        "Stationary Source Fuel Combustion, Residential, Wood, Woodstove: freestanding, EPA certified, catalytic",
    "2104008340":
        "Stationary Source Fuel Combustion, Residential, Wood, Woodstove: freestanding, masonry heater",
    "2104008400":
        "Stationary Source Fuel Combustion, Residential, Wood, Woodstove: pellet-fired, general (freestanding or FP insert)",
    "2104008410":
        "Stationary Source Fuel Combustion, Residential, Wood, Woodstove: pellet-fired, non-EPA certified (freestanding or FP insert)",
    "2104008420":
        "Stationary Source Fuel Combustion, Residential, Wood, Woodstove: pellet-fired, EPA certified (freestanding or FP insert)",
    "2104008500":
        "Stationary Source Fuel Combustion, Residential, Wood, Furnace: Indoor, cordwood-fired, general",
    "2104008510":
        "Stationary Source Fuel Combustion, Residential, Wood, Furnace: Indoor, cordwood-fired, non-EPA certified",
    "2104008520":
        "Stationary Source Fuel Combustion, Residential, Wood, Furnace: Indoor, cordwood-fired, EPA certified",
    "2104008530":
        "Stationary Source Fuel Combustion, Residential, Wood, Furnace: Indoor, pellet-fired, general",
    "2104008540":
        "Stationary Source Fuel Combustion, Residential, Wood, Furnace: Indoor, pellet-fired, non-EPA certified",
    "2104008550":
        "Stationary Source Fuel Combustion, Residential, Wood, Furnace: Indoor, pellet-fired, EPA certified",
    "2104008600":
        "Stationary Source Fuel Combustion, Residential, Wood, Hydronic heater: general, all types",
    "2104008610":
        "Stationary Source Fuel Combustion, Residential, Wood, Hydronic heater: outdoor",
    "2104008620":
        "Stationary Source Fuel Combustion, Residential, Wood, Hydronic heater: indoor",
    "2104008630":
        "Stationary Source Fuel Combustion, Residential, Wood, Hydronic heater: pellet-fired",
    "2104008640":
        "Stationary Source Fuel Combustion, Residential, Wood, Hydronic heater: meets NESCAUM phase II standards",
    "2104008700":
        "Stationary Source Fuel Combustion, Residential, Wood, Outdoor wood burning device, NEC (fire-pits, chimeas, etc)",
    "2104009000":
        "Stationary Source Fuel Combustion, Residential, Firelog, Total: All Combustor Types",
    "2104010000":
        "Stationary Source Fuel Combustion, Residential, Biomass; All Except Wood, Total: All Combustor Types",
    "2104011000":
        "Stationary Source Fuel Combustion, Residential, Kerosene, Total: All Heater Types",
    "2199001000":
        "Stationary Source Fuel Combustion, Total Area Source Fuel Combustion, Anthracite Coal, Total: All Boiler Types",
    "2199002000":
        "Stationary Source Fuel Combustion, Total Area Source Fuel Combustion, Bituminous/Subbituminous Coal, Total: All Boiler Types",
    "2199003000":
        "Stationary Source Fuel Combustion, Total Area Source Fuel Combustion, Lignite Coal, Total: All Boiler Types",
    "2199004000":
        "Stationary Source Fuel Combustion, Total Area Source Fuel Combustion, Distillate Oil, Total: Boilers and IC Engines",
    "2199004001":
        "Stationary Source Fuel Combustion, Total Area Source Fuel Combustion, Distillate Oil, All Boiler Types",
    "2199004002":
        "Stationary Source Fuel Combustion, Total Area Source Fuel Combustion, Distillate Oil, All IC Engine Types",
    "2199005000":
        "Stationary Source Fuel Combustion, Total Area Source Fuel Combustion, Residual Oil, Total: All Boiler Types",
    "2199006000":
        "Stationary Source Fuel Combustion, Total Area Source Fuel Combustion, Natural Gas, Total: Boilers and IC Engines",
    "2199006001":
        "Stationary Source Fuel Combustion, Total Area Source Fuel Combustion, Natural Gas, All Boiler Types",
    "2199006002":
        "Stationary Source Fuel Combustion, Total Area Source Fuel Combustion, Natural Gas, All IC Engine Types",
    "2199007000":
        "Stationary Source Fuel Combustion, Total Area Source Fuel Combustion, Liquified Petroleum Gas (LPG), Total: All Boiler Types",
    "2199008000":
        "Stationary Source Fuel Combustion, Total Area Source Fuel Combustion, Wood, Total: All Boiler Types",
    "2199009000":
        "Stationary Source Fuel Combustion, Total Area Source Fuel Combustion, Petroleum Coke, Total: All Boiler Types",
    "2199010000":
        "Stationary Source Fuel Combustion, Total Area Source Fuel Combustion, Process Gas, Total: All Boiler Types",
    "2199011000":
        "Stationary Source Fuel Combustion, Total Area Source Fuel Combustion, Kerosene, Total: All Heater Types",
    "2501000000":
        "Storage and Transport, Petroleum and Petroleum Product Storage, All Storage Types: Breathing Loss, Total: All Products",
    "2501000030":
        "Storage and Transport, Petroleum and Petroleum Product Storage, All Storage Types: Breathing Loss, Crude Oil",
    "2501000060":
        "Storage and Transport, Petroleum and Petroleum Product Storage, All Storage Types: Breathing Loss, Residual Oil",
    "2501000090":
        "Storage and Transport, Petroleum and Petroleum Product Storage, All Storage Types: Breathing Loss, Distillate Oil",
    "2501000120":
        "Storage and Transport, Petroleum and Petroleum Product Storage, All Storage Types: Breathing Loss, Gasoline",
    "2501000150":
        "Storage and Transport, Petroleum and Petroleum Product Storage, All Storage Types: Breathing Loss, Jet Naphtha",
    "2501000180":
        "Storage and Transport, Petroleum and Petroleum Product Storage, All Storage Types: Breathing Loss, Kerosene",
    "2501000900":
        "Storage and Transport, Petroleum and Petroleum Product Storage, All Storage Types: Breathing Loss, Tank Cleaning",
    "2501010000":
        "Storage and Transport, Petroleum and Petroleum Product Storage, Commercial/Industrial: Breathing Loss, Total: All Products",
    "2501010030":
        "Storage and Transport, Petroleum and Petroleum Product Storage, Commercial/Industrial: Breathing Loss, Crude Oil",
    "2501010060":
        "Storage and Transport, Petroleum and Petroleum Product Storage, Commercial/Industrial: Breathing Loss, Residual Oil",
    "2501010090":
        "Storage and Transport, Petroleum and Petroleum Product Storage, Commercial/Industrial: Breathing Loss, Distillate Oil",
    "2501010120":
        "Storage and Transport, Petroleum and Petroleum Product Storage, Commercial/Industrial: Breathing Loss, Gasoline",
    "2501010150":
        "Storage and Transport, Petroleum and Petroleum Product Storage, Commercial/Industrial: Breathing Loss, Jet Naphtha",
    "2501010180":
        "Storage and Transport, Petroleum and Petroleum Product Storage, Commercial/Industrial: Breathing Loss, Kerosene",
    "2501010900":
        "Storage and Transport, Petroleum and Petroleum Product Storage, Commercial/Industrial: Breathing Loss, Tank Cleaning",
    "2501011011":
        "Storage and Transport, Petroleum and Petroleum Product Storage, Residential Portable Gas Cans, Permeation",
    "2501011012":
        "Storage and Transport, Petroleum and Petroleum Product Storage, Residential Portable Gas Cans, Evaporation (includes Diurnal losses)",
    "2501011013":
        "Storage and Transport, Petroleum and Petroleum Product Storage, Residential Portable Gas Cans, Spillage During Transport",
    "2501011014":
        "Storage and Transport, Petroleum and Petroleum Product Storage, Residential Portable Gas Cans, Refilling at the Pump - Vapor Displacement",
    "2501011015":
        "Storage and Transport, Petroleum and Petroleum Product Storage, Residential Portable Gas Cans, Refilling at the Pump - Spillage",
    "2501012011":
        "Storage and Transport, Petroleum and Petroleum Product Storage, Commercial Portable Gas Cans, Permeation",
    "2501012012":
        "Storage and Transport, Petroleum and Petroleum Product Storage, Commercial Portable Gas Cans, Evaporation (includes Diurnal losses)",
    "2501012013":
        "Storage and Transport, Petroleum and Petroleum Product Storage, Commercial Portable Gas Cans, Spillage During Transport",
    "2501012014":
        "Storage and Transport, Petroleum and Petroleum Product Storage, Commercial Portable Gas Cans, Refilling at the Pump - Vapor Displacement",
    "2501012015":
        "Storage and Transport, Petroleum and Petroleum Product Storage, Commercial Portable Gas Cans, Refilling at the Pump - Spillage",
    "2501013010":
        "Storage and Transport, Petroleum and Petroleum Product Storage, Residential/Commercial Portable Gas Cans, Total: All Types",
    "2501050000":
        "Storage and Transport, Petroleum and Petroleum Product Storage, Bulk Terminals: All Evaporative Losses, Total: All Products",
    "2501050030":
        "Storage and Transport, Petroleum and Petroleum Product Storage, Bulk Terminals: All Evaporative Losses, Crude Oil",
    "2501050060":
        "Storage and Transport, Petroleum and Petroleum Product Storage, Bulk Terminals: All Evaporative Losses, Residual Oil",
    "2501050090":
        "Storage and Transport, Petroleum and Petroleum Product Storage, Bulk Terminals: All Evaporative Losses, Distillate Oil",
    "2501050120":
        "Storage and Transport, Petroleum and Petroleum Product Storage, Bulk Terminals: All Evaporative Losses, Gasoline",
    "2501050150":
        "Storage and Transport, Petroleum and Petroleum Product Storage, Bulk Terminals: All Evaporative Losses, Jet Naphtha",
    "2501050180":
        "Storage and Transport, Petroleum and Petroleum Product Storage, Bulk Terminals: All Evaporative Losses, Kerosene",
    "2501050900":
        "Storage and Transport, Petroleum and Petroleum Product Storage, Bulk Terminals: All Evaporative Losses, Tank Cleaning",
    "2501055120":
        "Storage and Transport, Petroleum and Petroleum Product Storage, Bulk Plants: All Evaporative Losses, Gasoline",
    "2501060000":
        "Storage and Transport, Petroleum and Petroleum Product Storage, Gasoline Service Stations, Total: All Gasoline/All Processes",
    "2501060050":
        "Storage and Transport, Petroleum and Petroleum Product Storage, Gasoline Service Stations, Stage 1: Total",
    "2501060051":
        "Storage and Transport, Petroleum and Petroleum Product Storage, Gasoline Service Stations, Stage 1: Submerged Filling",
    "2501060052":
        "Storage and Transport, Petroleum and Petroleum Product Storage, Gasoline Service Stations, Stage 1: Splash Filling",
    "2501060053":
        "Storage and Transport, Petroleum and Petroleum Product Storage, Gasoline Service Stations, Stage 1: Balanced Submerged Filling",
    "2501060100":
        "Storage and Transport, Petroleum and Petroleum Product Storage, Gasoline Service Stations, Stage 2: Total",
    "2501060101":
        "Storage and Transport, Petroleum and Petroleum Product Storage, Gasoline Service Stations, Stage 2: Displacement Loss/Uncontrolled",
    "2501060102":
        "Storage and Transport, Petroleum and Petroleum Product Storage, Gasoline Service Stations, Stage 2: Displacement Loss/Controlled",
    "2501060103":
        "Storage and Transport, Petroleum and Petroleum Product Storage, Gasoline Service Stations, Stage 2: Spillage",
    "2501060200":
        "Storage and Transport, Petroleum and Petroleum Product Storage, Gasoline Service Stations, Underground Tank: Total",
    "2501060201":
        "Storage and Transport, Petroleum and Petroleum Product Storage, Gasoline Service Stations, Underground Tank: Breathing and Emptying",
    "2501070000":
        "Storage and Transport, Petroleum and Petroleum Product Storage, Diesel Service Stations, Total: All Products/All Processes",
    "2501070050":
        "Storage and Transport, Petroleum and Petroleum Product Storage, Diesel Service Stations, Stage 1: Total",
    "2501070051":
        "Storage and Transport, Petroleum and Petroleum Product Storage, Diesel Service Stations, Stage 1: Submerged Filling",
    "2501070052":
        "Storage and Transport, Petroleum and Petroleum Product Storage, Diesel Service Stations, Stage 1: Splash Filling",
    "2501070053":
        "Storage and Transport, Petroleum and Petroleum Product Storage, Diesel Service Stations, Stage 1: Balanced Submerged Filling",
    "2501070100":
        "Storage and Transport, Petroleum and Petroleum Product Storage, Diesel Service Stations, Stage 2: Total",
    "2501070101":
        "Storage and Transport, Petroleum and Petroleum Product Storage, Diesel Service Stations, Stage 2: Displacement Loss/Uncontrolled",
    "2501070102":
        "Storage and Transport, Petroleum and Petroleum Product Storage, Diesel Service Stations, Stage 2: Displacement Loss/Controlled",
    "2501070103":
        "Storage and Transport, Petroleum and Petroleum Product Storage, Diesel Service Stations, Stage 2: Spillage",
    "2501070200":
        "Storage and Transport, Petroleum and Petroleum Product Storage, Diesel Service Stations, Underground Tank: Total",
    "2501070201":
        "Storage and Transport, Petroleum and Petroleum Product Storage, Diesel Service Stations, Underground Tank: Breathing and Emptying",
    "2501080050":
        "Storage and Transport, Petroleum and Petroleum Product Storage, Airports : Aviation Gasoline, Stage 1: Total",
    "2501080100":
        "Storage and Transport, Petroleum and Petroleum Product Storage, Airports : Aviation Gasoline, Stage 2: Total",
    "2501080201":
        "Storage and Transport, Petroleum and Petroleum Product Storage, Airports : Aviation Gasoline, Underground Tank: Breathing and Emptying",
    "2501995000":
        "Storage and Transport, Petroleum and Petroleum Product Storage, All Storage Types: Working Loss, Total: All Products",
    "2501995030":
        "Storage and Transport, Petroleum and Petroleum Product Storage, All Storage Types: Working Loss, Crude Oil",
    "2501995060":
        "Storage and Transport, Petroleum and Petroleum Product Storage, All Storage Types: Working Loss, Residual Oil",
    "2501995090":
        "Storage and Transport, Petroleum and Petroleum Product Storage, All Storage Types: Working Loss, Distillate Oil",
    "2501995120":
        "Storage and Transport, Petroleum and Petroleum Product Storage, All Storage Types: Working Loss, Gasoline",
    "2501995150":
        "Storage and Transport, Petroleum and Petroleum Product Storage, All Storage Types: Working Loss, Jet Naphtha",
    "2501995180":
        "Storage and Transport, Petroleum and Petroleum Product Storage, All Storage Types: Working Loss, Kerosene",
    "2505000000":
        "Storage and Transport, Petroleum and Petroleum Product Transport, All Transport Types, Total: All Products",
    "2505000030":
        "Storage and Transport, Petroleum and Petroleum Product Transport, All Transport Types, Crude Oil",
    "2505000060":
        "Storage and Transport, Petroleum and Petroleum Product Transport, All Transport Types, Residual Oil",
    "2505000090":
        "Storage and Transport, Petroleum and Petroleum Product Transport, All Transport Types, Distillate Oil",
    "2505000120":
        "Storage and Transport, Petroleum and Petroleum Product Transport, All Transport Types, Gasoline",
    "2505000150":
        "Storage and Transport, Petroleum and Petroleum Product Transport, All Transport Types, Jet Naphtha",
    "2505000180":
        "Storage and Transport, Petroleum and Petroleum Product Transport, All Transport Types, Kerosene",
    "2505000900":
        "Storage and Transport, Petroleum and Petroleum Product Transport, All Transport Types, Tank Cleaning",
    "2505010000":
        "Storage and Transport, Petroleum and Petroleum Product Transport, Rail Tank Car, Total: All Products",
    "2505010030":
        "Storage and Transport, Petroleum and Petroleum Product Transport, Rail Tank Car, Crude Oil",
    "2505010060":
        "Storage and Transport, Petroleum and Petroleum Product Transport, Rail Tank Car, Residual Oil",
    "2505010090":
        "Storage and Transport, Petroleum and Petroleum Product Transport, Rail Tank Car, Distillate Oil",
    "2505010120":
        "Storage and Transport, Petroleum and Petroleum Product Transport, Rail Tank Car, Gasoline",
    "2505010150":
        "Storage and Transport, Petroleum and Petroleum Product Transport, Rail Tank Car, Jet Naphtha",
    "2505010180":
        "Storage and Transport, Petroleum and Petroleum Product Transport, Rail Tank Car, Kerosene",
    "2505010900":
        "Storage and Transport, Petroleum and Petroleum Product Transport, Rail Tank Car, Tank Cleaning",
    "2505020000":
        "Storage and Transport, Petroleum and Petroleum Product Transport, Marine Vessel, Total: All Products",
    "2505020030":
        "Storage and Transport, Petroleum and Petroleum Product Transport, Marine Vessel, Crude Oil",
    "2505020041":
        "Storage and Transport, Petroleum and Petroleum Product Transport, Marine Vessel, Lube Oil-Barge",
    "2505020060":
        "Storage and Transport, Petroleum and Petroleum Product Transport, Marine Vessel, Residual Oil",
    "2505020090":
        "Storage and Transport, Petroleum and Petroleum Product Transport, Marine Vessel, Distillate Oil",
    "2505020091":
        "Storage and Transport, Petroleum and Petroleum Product Transport, Marine Vessel, Distillate Oil-#1 Diesel-Barge",
    "2505020092":
        "Storage and Transport, Petroleum and Petroleum Product Transport, Marine Vessel, Distillate Oil-#2 Diesel-Barge",
    "2505020093":
        "Storage and Transport, Petroleum and Petroleum Product Transport, Marine Vessel, Distillate Oil-Marine Diesel-Barge",
    "2505020120":
        "Storage and Transport, Petroleum and Petroleum Product Transport, Marine Vessel, Gasoline",
    "2505020121":
        "Storage and Transport, Petroleum and Petroleum Product Transport, Marine Vessel, Gasoline - Barge",
    "2505020150":
        "Storage and Transport, Petroleum and Petroleum Product Transport, Marine Vessel, Jet Naphtha",
    "2505020180":
        "Storage and Transport, Petroleum and Petroleum Product Transport, Marine Vessel, Kerosene",
    "2505020182":
        "Storage and Transport, Petroleum and Petroleum Product Transport, Marine Vessel, Jet Kerosene-Barge",
    "2505020900":
        "Storage and Transport, Petroleum and Petroleum Product Transport, Marine Vessel, Tank Cleaning",
    "2505030000":
        "Storage and Transport, Petroleum and Petroleum Product Transport, Truck, Total: All Products",
    "2505030030":
        "Storage and Transport, Petroleum and Petroleum Product Transport, Truck, Crude Oil",
    "2505030060":
        "Storage and Transport, Petroleum and Petroleum Product Transport, Truck, Residual Oil",
    "2505030090":
        "Storage and Transport, Petroleum and Petroleum Product Transport, Truck, Distillate Oil",
    "2505030120":
        "Storage and Transport, Petroleum and Petroleum Product Transport, Truck, Gasoline",
    "2505030150":
        "Storage and Transport, Petroleum and Petroleum Product Transport, Truck, Jet Naphtha",
    "2505030180":
        "Storage and Transport, Petroleum and Petroleum Product Transport, Truck, Kerosene",
    "2505030900":
        "Storage and Transport, Petroleum and Petroleum Product Transport, Truck, Tank Cleaning",
    "2505040000":
        "Storage and Transport, Petroleum and Petroleum Product Transport, Pipeline, Total: All Products",
    "2505040030":
        "Storage and Transport, Petroleum and Petroleum Product Transport, Pipeline, Crude Oil",
    "2505040060":
        "Storage and Transport, Petroleum and Petroleum Product Transport, Pipeline, Residual Oil",
    "2505040090":
        "Storage and Transport, Petroleum and Petroleum Product Transport, Pipeline, Distillate Oil",
    "2505040120":
        "Storage and Transport, Petroleum and Petroleum Product Transport, Pipeline, Gasoline",
    "2505040150":
        "Storage and Transport, Petroleum and Petroleum Product Transport, Pipeline, Jet Naphtha",
    "2505040180":
        "Storage and Transport, Petroleum and Petroleum Product Transport, Pipeline, Kerosene",
    "2510000000":
        "Storage and Transport, Organic Chemical Storage, All Storage Types: Breathing Loss, Total: All Products",
    "2510000030":
        "Storage and Transport, Organic Chemical Storage, All Storage Types: Breathing Loss, Acetone",
    "2510000060":
        "Storage and Transport, Organic Chemical Storage, All Storage Types: Breathing Loss, Butyl Alcohols: All Types",
    "2510000065":
        "Storage and Transport, Organic Chemical Storage, All Storage Types: Breathing Loss, n-Butyl Alcohol",
    "2510000070":
        "Storage and Transport, Organic Chemical Storage, All Storage Types: Breathing Loss, Isobutyl Alcohol",
    "2510000100":
        "Storage and Transport, Organic Chemical Storage, All Storage Types: Breathing Loss, Cyclohexanone",
    "2510000165":
        "Storage and Transport, Organic Chemical Storage, All Storage Types: Breathing Loss, Ethanol",
    "2510000185":
        "Storage and Transport, Organic Chemical Storage, All Storage Types: Breathing Loss, Ethylbenzene",
    "2510000195":
        "Storage and Transport, Organic Chemical Storage, All Storage Types: Breathing Loss, Ethylene Glycol",
    "2510000220":
        "Storage and Transport, Organic Chemical Storage, All Storage Types: Breathing Loss, Formalin",
    "2510000235":
        "Storage and Transport, Organic Chemical Storage, All Storage Types: Breathing Loss, Glycol Ethers: All Types",
    "2510000240":
        "Storage and Transport, Organic Chemical Storage, All Storage Types: Breathing Loss, Gum Turpentine",
    "2510000250":
        "Storage and Transport, Organic Chemical Storage, All Storage Types: Breathing Loss, Isopropanol",
    "2510000260":
        "Storage and Transport, Organic Chemical Storage, All Storage Types: Breathing Loss, Methanol",
    "2510000265":
        "Storage and Transport, Organic Chemical Storage, All Storage Types: Breathing Loss, Methyl Chloride",
    "2510000270":
        "Storage and Transport, Organic Chemical Storage, All Storage Types: Breathing Loss, Methyl Chloroform",
    "2510000275":
        "Storage and Transport, Organic Chemical Storage, All Storage Types: Breathing Loss, Methyl Ethyl Ketone",
    "2510000285":
        "Storage and Transport, Organic Chemical Storage, All Storage Types: Breathing Loss, Methyl Isobutyl Ketone",
    "2510000295":
        "Storage and Transport, Organic Chemical Storage, All Storage Types: Breathing Loss, Methylene Chloride",
    "2510000310":
        "Storage and Transport, Organic Chemical Storage, All Storage Types: Breathing Loss, n-Propanol",
    "2510000320":
        "Storage and Transport, Organic Chemical Storage, All Storage Types: Breathing Loss, Nitrobenzene",
    "2510000345":
        "Storage and Transport, Organic Chemical Storage, All Storage Types: Breathing Loss, Perchloroethylene",
    "2510000350":
        "Storage and Transport, Organic Chemical Storage, All Storage Types: Breathing Loss, Propylene Glycol",
    "2510000370":
        "Storage and Transport, Organic Chemical Storage, All Storage Types: Breathing Loss, Special Naphthas",
    "2510000380":
        "Storage and Transport, Organic Chemical Storage, All Storage Types: Breathing Loss, Toluene",
    "2510000385":
        "Storage and Transport, Organic Chemical Storage, All Storage Types: Breathing Loss, Trichloroethylene",
    "2510000405":
        "Storage and Transport, Organic Chemical Storage, All Storage Types: Breathing Loss, Xylenes (Mixed)",
    "2510000900":
        "Storage and Transport, Organic Chemical Storage, All Storage Types: Breathing Loss, Tank Cleaning",
    "2510010000":
        "Storage and Transport, Organic Chemical Storage, Commercial/Industrial: Breathing Loss, Total: All Products",
    "2510010030":
        "Storage and Transport, Organic Chemical Storage, Commercial/Industrial: Breathing Loss, Acetone",
    "2510010060":
        "Storage and Transport, Organic Chemical Storage, Commercial/Industrial: Breathing Loss, Butyl Alcohols: All Types",
    "2510010065":
        "Storage and Transport, Organic Chemical Storage, Commercial/Industrial: Breathing Loss, n-Butyl Alcohol",
    "2510010070":
        "Storage and Transport, Organic Chemical Storage, Commercial/Industrial: Breathing Loss, Isobutyl Alcohol",
    "2510010100":
        "Storage and Transport, Organic Chemical Storage, Commercial/Industrial: Breathing Loss, Cyclohexanone",
    "2510010165":
        "Storage and Transport, Organic Chemical Storage, Commercial/Industrial: Breathing Loss, Ethanol",
    "2510010185":
        "Storage and Transport, Organic Chemical Storage, Commercial/Industrial: Breathing Loss, Ethylbenzene",
    "2510010195":
        "Storage and Transport, Organic Chemical Storage, Commercial/Industrial: Breathing Loss, Ethylene Glycol",
    "2510010220":
        "Storage and Transport, Organic Chemical Storage, Commercial/Industrial: Breathing Loss, Formalin",
    "2510010235":
        "Storage and Transport, Organic Chemical Storage, Commercial/Industrial: Breathing Loss, Glycol Ethers: All Types",
    "2510010240":
        "Storage and Transport, Organic Chemical Storage, Commercial/Industrial: Breathing Loss, Gum Turpentine",
    "2510010250":
        "Storage and Transport, Organic Chemical Storage, Commercial/Industrial: Breathing Loss, Isopropanol",
    "2510010260":
        "Storage and Transport, Organic Chemical Storage, Commercial/Industrial: Breathing Loss, Methanol",
    "2510010265":
        "Storage and Transport, Organic Chemical Storage, Commercial/Industrial: Breathing Loss, Methyl Chloride",
    "2510010270":
        "Storage and Transport, Organic Chemical Storage, Commercial/Industrial: Breathing Loss, Methyl Chloroform",
    "2510010275":
        "Storage and Transport, Organic Chemical Storage, Commercial/Industrial: Breathing Loss, Methyl Ethyl Ketone",
    "2510010285":
        "Storage and Transport, Organic Chemical Storage, Commercial/Industrial: Breathing Loss, Methyl Isobutyl Ketone",
    "2510010295":
        "Storage and Transport, Organic Chemical Storage, Commercial/Industrial: Breathing Loss, Methylene Chloride",
    "2510010310":
        "Storage and Transport, Organic Chemical Storage, Commercial/Industrial: Breathing Loss, n-Propanol",
    "2510010320":
        "Storage and Transport, Organic Chemical Storage, Commercial/Industrial: Breathing Loss, Nitrobenzene",
    "2510010345":
        "Storage and Transport, Organic Chemical Storage, Commercial/Industrial: Breathing Loss, Perchloroethylene",
    "2510010350":
        "Storage and Transport, Organic Chemical Storage, Commercial/Industrial: Breathing Loss, Propylene Glycol",
    "2510010370":
        "Storage and Transport, Organic Chemical Storage, Commercial/Industrial: Breathing Loss, Special Naphthas",
    "2510010380":
        "Storage and Transport, Organic Chemical Storage, Commercial/Industrial: Breathing Loss, Toluene",
    "2510010385":
        "Storage and Transport, Organic Chemical Storage, Commercial/Industrial: Breathing Loss, Trichloroethylene",
    "2510010405":
        "Storage and Transport, Organic Chemical Storage, Commercial/Industrial: Breathing Loss, Xylenes (Mixed)",
    "2510010900":
        "Storage and Transport, Organic Chemical Storage, Commercial/Industrial: Breathing Loss, Tank Cleaning",
    "2510050000":
        "Storage and Transport, Organic Chemical Storage, Bulk Stations/Terminals: Breathing Loss, Total: All Products",
    "2510050030":
        "Storage and Transport, Organic Chemical Storage, Bulk Stations/Terminals: Breathing Loss, Acetone",
    "2510050060":
        "Storage and Transport, Organic Chemical Storage, Bulk Stations/Terminals: Breathing Loss, Butyl Alcohols: All Types",
    "2510050065":
        "Storage and Transport, Organic Chemical Storage, Bulk Stations/Terminals: Breathing Loss, n-Butyl Alcohol",
    "2510050070":
        "Storage and Transport, Organic Chemical Storage, Bulk Stations/Terminals: Breathing Loss, Isobutyl Alcohol",
    "2510050100":
        "Storage and Transport, Organic Chemical Storage, Bulk Stations/Terminals: Breathing Loss, Cyclohexanone",
    "2510050165":
        "Storage and Transport, Organic Chemical Storage, Bulk Stations/Terminals: Breathing Loss, Ethanol",
    "2510050185":
        "Storage and Transport, Organic Chemical Storage, Bulk Stations/Terminals: Breathing Loss, Ethylbenzene",
    "2510050195":
        "Storage and Transport, Organic Chemical Storage, Bulk Stations/Terminals: Breathing Loss, Ethylene Glycol",
    "2510050220":
        "Storage and Transport, Organic Chemical Storage, Bulk Stations/Terminals: Breathing Loss, Formalin",
    "2510050235":
        "Storage and Transport, Organic Chemical Storage, Bulk Stations/Terminals: Breathing Loss, Glycol Ethers: All Types",
    "2510050240":
        "Storage and Transport, Organic Chemical Storage, Bulk Stations/Terminals: Breathing Loss, Gum Turpentine",
    "2510050250":
        "Storage and Transport, Organic Chemical Storage, Bulk Stations/Terminals: Breathing Loss, Isopropanol",
    "2510050260":
        "Storage and Transport, Organic Chemical Storage, Bulk Stations/Terminals: Breathing Loss, Methanol",
    "2510050265":
        "Storage and Transport, Organic Chemical Storage, Bulk Stations/Terminals: Breathing Loss, Methyl Chloride",
    "2510050270":
        "Storage and Transport, Organic Chemical Storage, Bulk Stations/Terminals: Breathing Loss, Methyl Chloroform",
    "2510050275":
        "Storage and Transport, Organic Chemical Storage, Bulk Stations/Terminals: Breathing Loss, Methyl Ethyl Ketone",
    "2510050285":
        "Storage and Transport, Organic Chemical Storage, Bulk Stations/Terminals: Breathing Loss, Methyl Isobutyl Ketone",
    "2510050295":
        "Storage and Transport, Organic Chemical Storage, Bulk Stations/Terminals: Breathing Loss, Methylene Chloride",
    "2510050310":
        "Storage and Transport, Organic Chemical Storage, Bulk Stations/Terminals: Breathing Loss, n-Propanol",
    "2510050320":
        "Storage and Transport, Organic Chemical Storage, Bulk Stations/Terminals: Breathing Loss, Nitrobenzene",
    "2510050345":
        "Storage and Transport, Organic Chemical Storage, Bulk Stations/Terminals: Breathing Loss, Perchloroethylene",
    "2510050350":
        "Storage and Transport, Organic Chemical Storage, Bulk Stations/Terminals: Breathing Loss, Propylene Glycol",
    "2510050370":
        "Storage and Transport, Organic Chemical Storage, Bulk Stations/Terminals: Breathing Loss, Special Naphthas",
    "2510050380":
        "Storage and Transport, Organic Chemical Storage, Bulk Stations/Terminals: Breathing Loss, Toluene",
    "2510050385":
        "Storage and Transport, Organic Chemical Storage, Bulk Stations/Terminals: Breathing Loss, Trichloroethylene",
    "2510050405":
        "Storage and Transport, Organic Chemical Storage, Bulk Stations/Terminals: Breathing Loss, Xylenes (Mixed)",
    "2510050900":
        "Storage and Transport, Organic Chemical Storage, Bulk Stations/Terminals: Breathing Loss, Tank Cleaning",
    "2510995000":
        "Storage and Transport, Organic Chemical Storage, All Storage Types: Working Loss, Total: All Products",
    "2510995030":
        "Storage and Transport, Organic Chemical Storage, All Storage Types: Working Loss, Acetone",
    "2510995060":
        "Storage and Transport, Organic Chemical Storage, All Storage Types: Working Loss, Butyl Alcohols: All Types",
    "2510995065":
        "Storage and Transport, Organic Chemical Storage, All Storage Types: Working Loss, n-Butyl Alcohol",
    "2510995070":
        "Storage and Transport, Organic Chemical Storage, All Storage Types: Working Loss, Isobutyl Alcohol",
    "2510995100":
        "Storage and Transport, Organic Chemical Storage, All Storage Types: Working Loss, Cyclohexanone",
    "2510995165":
        "Storage and Transport, Organic Chemical Storage, All Storage Types: Working Loss, Ethanol",
    "2510995185":
        "Storage and Transport, Organic Chemical Storage, All Storage Types: Working Loss, Ethylbenzene",
    "2510995195":
        "Storage and Transport, Organic Chemical Storage, All Storage Types: Working Loss, Ethylene Glycol",
    "2510995220":
        "Storage and Transport, Organic Chemical Storage, All Storage Types: Working Loss, Formalin",
    "2510995235":
        "Storage and Transport, Organic Chemical Storage, All Storage Types: Working Loss, Glycol Ethers: All Types",
    "2510995240":
        "Storage and Transport, Organic Chemical Storage, All Storage Types: Working Loss, Gum Turpentine",
    "2510995250":
        "Storage and Transport, Organic Chemical Storage, All Storage Types: Working Loss, Isopropanol",
    "2510995260":
        "Storage and Transport, Organic Chemical Storage, All Storage Types: Working Loss, Methanol",
    "2510995265":
        "Storage and Transport, Organic Chemical Storage, All Storage Types: Working Loss, Methyl Chloride",
    "2510995270":
        "Storage and Transport, Organic Chemical Storage, All Storage Types: Working Loss, Methyl Chloroform",
    "2510995275":
        "Storage and Transport, Organic Chemical Storage, All Storage Types: Working Loss, Methyl Ethyl Ketone",
    "2510995285":
        "Storage and Transport, Organic Chemical Storage, All Storage Types: Working Loss, Methyl Isobutyl Ketone",
    "2510995295":
        "Storage and Transport, Organic Chemical Storage, All Storage Types: Working Loss, Methylene Chloride",
    "2510995310":
        "Storage and Transport, Organic Chemical Storage, All Storage Types: Working Loss, n-Propanol",
    "2510995320":
        "Storage and Transport, Organic Chemical Storage, All Storage Types: Working Loss, Nitrobenzene",
    "2510995345":
        "Storage and Transport, Organic Chemical Storage, All Storage Types: Working Loss, Perchloroethylene",
    "2510995350":
        "Storage and Transport, Organic Chemical Storage, All Storage Types: Working Loss, Propylene Glycol",
    "2510995370":
        "Storage and Transport, Organic Chemical Storage, All Storage Types: Working Loss, Special Naphthas",
    "2510995380":
        "Storage and Transport, Organic Chemical Storage, All Storage Types: Working Loss, Toluene",
    "2510995385":
        "Storage and Transport, Organic Chemical Storage, All Storage Types: Working Loss, Trichloroethylene",
    "2510995405":
        "Storage and Transport, Organic Chemical Storage, All Storage Types: Working Loss, Xylenes (Mixed)",
    "2515000000":
        "Storage and Transport, Organic Chemical Transport, All Transport Types, Total: All Products",
    "2515000030":
        "Storage and Transport, Organic Chemical Transport, All Transport Types, Acetone",
    "2515000060":
        "Storage and Transport, Organic Chemical Transport, All Transport Types, Butyl Alcohols: All Types",
    "2515000065":
        "Storage and Transport, Organic Chemical Transport, All Transport Types, n-Butyl Alcohol",
    "2515000070":
        "Storage and Transport, Organic Chemical Transport, All Transport Types, Isobutyl Alcohol",
    "2515000100":
        "Storage and Transport, Organic Chemical Transport, All Transport Types, Cyclohexanone",
    "2515000165":
        "Storage and Transport, Organic Chemical Transport, All Transport Types, Ethanol",
    "2515000185":
        "Storage and Transport, Organic Chemical Transport, All Transport Types, Ethylbenzene",
    "2515000195":
        "Storage and Transport, Organic Chemical Transport, All Transport Types, Ethylene Glycol",
    "2515000220":
        "Storage and Transport, Organic Chemical Transport, All Transport Types, Formalin",
    "2515000235":
        "Storage and Transport, Organic Chemical Transport, All Transport Types, Glycol Ethers: All Types",
    "2515000240":
        "Storage and Transport, Organic Chemical Transport, All Transport Types, Gum Turpentine",
    "2515000250":
        "Storage and Transport, Organic Chemical Transport, All Transport Types, Isopropanol",
    "2515000260":
        "Storage and Transport, Organic Chemical Transport, All Transport Types, Methanol",
    "2515000265":
        "Storage and Transport, Organic Chemical Transport, All Transport Types, Methyl Chloride",
    "2515000270":
        "Storage and Transport, Organic Chemical Transport, All Transport Types, Methyl Chloroform",
    "2515000275":
        "Storage and Transport, Organic Chemical Transport, All Transport Types, Methyl Ethyl Ketone",
    "2515000285":
        "Storage and Transport, Organic Chemical Transport, All Transport Types, Methyl Isobutyl Ketone",
    "2515000295":
        "Storage and Transport, Organic Chemical Transport, All Transport Types, Methylene Chloride",
    "2515000310":
        "Storage and Transport, Organic Chemical Transport, All Transport Types, n-Propanol",
    "2515000320":
        "Storage and Transport, Organic Chemical Transport, All Transport Types, Nitrobenzene",
    "2515000345":
        "Storage and Transport, Organic Chemical Transport, All Transport Types, Perchloroethylene",
    "2515000350":
        "Storage and Transport, Organic Chemical Transport, All Transport Types, Propylene Glycol",
    "2515000370":
        "Storage and Transport, Organic Chemical Transport, All Transport Types, Special Naphthas",
    "2515000380":
        "Storage and Transport, Organic Chemical Transport, All Transport Types, Toluene",
    "2515000385":
        "Storage and Transport, Organic Chemical Transport, All Transport Types, Trichloroethylene",
    "2515000405":
        "Storage and Transport, Organic Chemical Transport, All Transport Types, Xylenes (Mixed)",
    "2515000900":
        "Storage and Transport, Organic Chemical Transport, All Transport Types, Tank Cleaning",
    "2515010000":
        "Storage and Transport, Organic Chemical Transport, Rail Tank Car, Total: All Products",
    "2515010030":
        "Storage and Transport, Organic Chemical Transport, Rail Tank Car, Acetone",
    "2515010060":
        "Storage and Transport, Organic Chemical Transport, Rail Tank Car, Butyl Alcohols: All Types",
    "2515010065":
        "Storage and Transport, Organic Chemical Transport, Rail Tank Car, n-Butyl Alcohol",
    "2515010070":
        "Storage and Transport, Organic Chemical Transport, Rail Tank Car, Isobutyl Alcohol",
    "2515010100":
        "Storage and Transport, Organic Chemical Transport, Rail Tank Car, Cyclohexanone",
    "2515010165":
        "Storage and Transport, Organic Chemical Transport, Rail Tank Car, Ethanol",
    "2515010185":
        "Storage and Transport, Organic Chemical Transport, Rail Tank Car, Ethylbenzene",
    "2515010195":
        "Storage and Transport, Organic Chemical Transport, Rail Tank Car, Ethylene Glycol",
    "2515010220":
        "Storage and Transport, Organic Chemical Transport, Rail Tank Car, Formalin",
    "2515010235":
        "Storage and Transport, Organic Chemical Transport, Rail Tank Car, Glycol Ethers: All Types",
    "2515010240":
        "Storage and Transport, Organic Chemical Transport, Rail Tank Car, Gum Turpentine",
    "2515010250":
        "Storage and Transport, Organic Chemical Transport, Rail Tank Car, Isopropanol",
    "2515010260":
        "Storage and Transport, Organic Chemical Transport, Rail Tank Car, Methanol",
    "2515010265":
        "Storage and Transport, Organic Chemical Transport, Rail Tank Car, Methyl Chloride",
    "2515010270":
        "Storage and Transport, Organic Chemical Transport, Rail Tank Car, Methyl Chloroform",
    "2515010275":
        "Storage and Transport, Organic Chemical Transport, Rail Tank Car, Methyl Ethyl Ketone",
    "2515010285":
        "Storage and Transport, Organic Chemical Transport, Rail Tank Car, Methyl Isobutyl Ketone",
    "2515010295":
        "Storage and Transport, Organic Chemical Transport, Rail Tank Car, Methylene Chloride",
    "2515010310":
        "Storage and Transport, Organic Chemical Transport, Rail Tank Car, n-Propanol",
    "2515010320":
        "Storage and Transport, Organic Chemical Transport, Rail Tank Car, Nitrobenzene",
    "2515010345":
        "Storage and Transport, Organic Chemical Transport, Rail Tank Car, Perchloroethylene",
    "2515010350":
        "Storage and Transport, Organic Chemical Transport, Rail Tank Car, Propylene Glycol",
    "2515010370":
        "Storage and Transport, Organic Chemical Transport, Rail Tank Car, Special Naphthas",
    "2515010380":
        "Storage and Transport, Organic Chemical Transport, Rail Tank Car, Toluene",
    "2515010385":
        "Storage and Transport, Organic Chemical Transport, Rail Tank Car, Trichloroethylene",
    "2515010405":
        "Storage and Transport, Organic Chemical Transport, Rail Tank Car, Xylenes (Mixed)",
    "2515010900":
        "Storage and Transport, Organic Chemical Transport, Rail Tank Car, Tank Cleaning",
    "2515020000":
        "Storage and Transport, Organic Chemical Transport, Marine Vessel, Total: All Products",
    "2515020001":
        "Storage and Transport, Organic Chemical Transport, Marine Vessel, Heptane -Barge",
    "2515020002":
        "Storage and Transport, Organic Chemical Transport, Marine Vessel, n-Decane -Barge",
    "2515020003":
        "Storage and Transport, Organic Chemical Transport, Marine Vessel, 1-Heptene -Barge",
    "2515020004":
        "Storage and Transport, Organic Chemical Transport, Marine Vessel, Hexane -Barge",
    "2515020005":
        "Storage and Transport, Organic Chemical Transport, Marine Vessel, Nonene -Barge",
    "2515020006":
        "Storage and Transport, Organic Chemical Transport, Marine Vessel, Decanol -Barge",
    "2515020007":
        "Storage and Transport, Organic Chemical Transport, Marine Vessel, Hexanol -Barge",
    "2515020008":
        "Storage and Transport, Organic Chemical Transport, Marine Vessel, 2-Ethylhexanol -Barge",
    "2515020011":
        "Storage and Transport, Organic Chemical Transport, Marine Vessel, Acetic Acid-Barge",
    "2515020012":
        "Storage and Transport, Organic Chemical Transport, Marine Vessel, Propionic Acid-Barge",
    "2515020013":
        "Storage and Transport, Organic Chemical Transport, Marine Vessel, Butyric Acid-Barge",
    "2515020014":
        "Storage and Transport, Organic Chemical Transport, Marine Vessel, Styrene-Barge",
    "2515020015":
        "Storage and Transport, Organic Chemical Transport, Marine Vessel, Cumene-Barge",
    "2515020016":
        "Storage and Transport, Organic Chemical Transport, Marine Vessel, MTBE-Barge",
    "2515020017":
        "Storage and Transport, Organic Chemical Transport, Marine Vessel, Butyl Acrylate-Barge",
    "2515020018":
        "Storage and Transport, Organic Chemical Transport, Marine Vessel, Vinyl Acetate-Barge",
    "2515020019":
        "Storage and Transport, Organic Chemical Transport, Marine Vessel, Propyl Acetate-Barge",
    "2515020030":
        "Storage and Transport, Organic Chemical Transport, Marine Vessel, Acetone",
    "2515020060":
        "Storage and Transport, Organic Chemical Transport, Marine Vessel, Butyl Alcohols: All Types",
    "2515020065":
        "Storage and Transport, Organic Chemical Transport, Marine Vessel, n-Butyl Alcohol",
    "2515020070":
        "Storage and Transport, Organic Chemical Transport, Marine Vessel, Isobutyl Alcohol",
    "2515020100":
        "Storage and Transport, Organic Chemical Transport, Marine Vessel, Cyclohexanone",
    "2515020165":
        "Storage and Transport, Organic Chemical Transport, Marine Vessel, Ethanol",
    "2515020185":
        "Storage and Transport, Organic Chemical Transport, Marine Vessel, Ethylbenzene",
    "2515020195":
        "Storage and Transport, Organic Chemical Transport, Marine Vessel, Ethylene Glycol",
    "2515020220":
        "Storage and Transport, Organic Chemical Transport, Marine Vessel, Formalin",
    "2515020235":
        "Storage and Transport, Organic Chemical Transport, Marine Vessel, Glycol Ethers: All Types",
    "2515020240":
        "Storage and Transport, Organic Chemical Transport, Marine Vessel, Gum Turpentine",
    "2515020250":
        "Storage and Transport, Organic Chemical Transport, Marine Vessel, Isopropanol",
    "2515020260":
        "Storage and Transport, Organic Chemical Transport, Marine Vessel, Methanol",
    "2515020265":
        "Storage and Transport, Organic Chemical Transport, Marine Vessel, Methyl Chloride",
    "2515020270":
        "Storage and Transport, Organic Chemical Transport, Marine Vessel, Methyl Chloroform",
    "2515020275":
        "Storage and Transport, Organic Chemical Transport, Marine Vessel, Methyl Ethyl Ketone",
    "2515020285":
        "Storage and Transport, Organic Chemical Transport, Marine Vessel, Methyl Isobutyl Ketone",
    "2515020295":
        "Storage and Transport, Organic Chemical Transport, Marine Vessel, Methylene Chloride",
    "2515020310":
        "Storage and Transport, Organic Chemical Transport, Marine Vessel, n-Propanol",
    "2515020320":
        "Storage and Transport, Organic Chemical Transport, Marine Vessel, Nitrobenzene",
    "2515020345":
        "Storage and Transport, Organic Chemical Transport, Marine Vessel, Perchloroethylene",
    "2515020350":
        "Storage and Transport, Organic Chemical Transport, Marine Vessel, Propylene Glycol",
    "2515020370":
        "Storage and Transport, Organic Chemical Transport, Marine Vessel, Special Naphthas",
    "2515020372":
        "Storage and Transport, Organic Chemical Transport, Marine Vessel, Solvents-Barge",
    "2515020380":
        "Storage and Transport, Organic Chemical Transport, Marine Vessel, Toluene",
    "2515020382":
        "Storage and Transport, Organic Chemical Transport, Marine Vessel, Benzene-Barge",
    "2515020385":
        "Storage and Transport, Organic Chemical Transport, Marine Vessel, Trichloroethylene",
    "2515020405":
        "Storage and Transport, Organic Chemical Transport, Marine Vessel, Xylenes (Mixed)",
    "2515020900":
        "Storage and Transport, Organic Chemical Transport, Marine Vessel, Tank Cleaning",
    "2515030000":
        "Storage and Transport, Organic Chemical Transport, Truck, Total: All Products",
    "2515030030":
        "Storage and Transport, Organic Chemical Transport, Truck, Acetone",
    "2515030060":
        "Storage and Transport, Organic Chemical Transport, Truck, Butyl Alcohols: All Types",
    "2515030065":
        "Storage and Transport, Organic Chemical Transport, Truck, n-Butyl Alcohol",
    "2515030070":
        "Storage and Transport, Organic Chemical Transport, Truck, Isobutyl Alcohol",
    "2515030100":
        "Storage and Transport, Organic Chemical Transport, Truck, Cyclohexanone",
    "2515030165":
        "Storage and Transport, Organic Chemical Transport, Truck, Ethanol",
    "2515030185":
        "Storage and Transport, Organic Chemical Transport, Truck, Ethylbenzene",
    "2515030195":
        "Storage and Transport, Organic Chemical Transport, Truck, Ethylene Glycol",
    "2515030220":
        "Storage and Transport, Organic Chemical Transport, Truck, Formalin",
    "2515030235":
        "Storage and Transport, Organic Chemical Transport, Truck, Glycol Ethers: All Types",
    "2515030240":
        "Storage and Transport, Organic Chemical Transport, Truck, Gum Turpentine",
    "2515030250":
        "Storage and Transport, Organic Chemical Transport, Truck, Isopropanol",
    "2515030260":
        "Storage and Transport, Organic Chemical Transport, Truck, Methanol",
    "2515030265":
        "Storage and Transport, Organic Chemical Transport, Truck, Methyl Chloride",
    "2515030270":
        "Storage and Transport, Organic Chemical Transport, Truck, Methyl Chloroform",
    "2515030275":
        "Storage and Transport, Organic Chemical Transport, Truck, Methyl Ethyl Ketone",
    "2515030285":
        "Storage and Transport, Organic Chemical Transport, Truck, Methyl Isobutyl Ketone",
    "2515030295":
        "Storage and Transport, Organic Chemical Transport, Truck, Methylene Chloride",
    "2515030310":
        "Storage and Transport, Organic Chemical Transport, Truck, n-Propanol",
    "2515030320":
        "Storage and Transport, Organic Chemical Transport, Truck, Nitrobenzene",
    "2515030345":
        "Storage and Transport, Organic Chemical Transport, Truck, Perchloroethylene",
    "2515030350":
        "Storage and Transport, Organic Chemical Transport, Truck, Propylene Glycol",
    "2515030370":
        "Storage and Transport, Organic Chemical Transport, Truck, Special Naphthas",
    "2515030380":
        "Storage and Transport, Organic Chemical Transport, Truck, Toluene",
    "2515030385":
        "Storage and Transport, Organic Chemical Transport, Truck, Trichloroethylene",
    "2515030405":
        "Storage and Transport, Organic Chemical Transport, Truck, Xylenes (Mixed)",
    "2515030900":
        "Storage and Transport, Organic Chemical Transport, Truck, Tank Cleaning",
    "2515040000":
        "Storage and Transport, Organic Chemical Transport, Pipeline, Total: All Products",
    "2515040030":
        "Storage and Transport, Organic Chemical Transport, Pipeline, Acetone",
    "2515040045":
        "Storage and Transport, Organic Chemical Transport, Pipeline, 1,3-Butadiene",
    "2515040060":
        "Storage and Transport, Organic Chemical Transport, Pipeline, Butyl Alcohols: All Types",
    "2515040065":
        "Storage and Transport, Organic Chemical Transport, Pipeline, n-Butyl Alcohol",
    "2515040070":
        "Storage and Transport, Organic Chemical Transport, Pipeline, Isobutyl Alcohol",
    "2515040100":
        "Storage and Transport, Organic Chemical Transport, Pipeline, Cyclohexanone",
    "2515040165":
        "Storage and Transport, Organic Chemical Transport, Pipeline, Ethanol",
    "2515040185":
        "Storage and Transport, Organic Chemical Transport, Pipeline, Ethylbenzene",
    "2515040190":
        "Storage and Transport, Organic Chemical Transport, Pipeline, Ethylene",
    "2515040195":
        "Storage and Transport, Organic Chemical Transport, Pipeline, Ethylene Glycol",
    "2515040220":
        "Storage and Transport, Organic Chemical Transport, Pipeline, Formalin",
    "2515040235":
        "Storage and Transport, Organic Chemical Transport, Pipeline, Glycol Ethers: All Types",
    "2515040240":
        "Storage and Transport, Organic Chemical Transport, Pipeline, Gum Turpentine",
    "2515040250":
        "Storage and Transport, Organic Chemical Transport, Pipeline, Isopropanol",
    "2515040260":
        "Storage and Transport, Organic Chemical Transport, Pipeline, Methanol",
    "2515040265":
        "Storage and Transport, Organic Chemical Transport, Pipeline, Methyl Chloride",
    "2515040270":
        "Storage and Transport, Organic Chemical Transport, Pipeline, Methyl Chloroform",
    "2515040275":
        "Storage and Transport, Organic Chemical Transport, Pipeline, Methyl Ethyl Ketone",
    "2515040285":
        "Storage and Transport, Organic Chemical Transport, Pipeline, Methyl Isobutyl Ketone",
    "2515040295":
        "Storage and Transport, Organic Chemical Transport, Pipeline, Methylene Chloride",
    "2515040310":
        "Storage and Transport, Organic Chemical Transport, Pipeline, n-Propanol",
    "2515040320":
        "Storage and Transport, Organic Chemical Transport, Pipeline, Nitrobenzene",
    "2515040345":
        "Storage and Transport, Organic Chemical Transport, Pipeline, Perchloroethylene",
    "2515040348":
        "Storage and Transport, Organic Chemical Transport, Pipeline, Propylene",
    "2515040350":
        "Storage and Transport, Organic Chemical Transport, Pipeline, Propylene Glycol",
    "2515040370":
        "Storage and Transport, Organic Chemical Transport, Pipeline, Special Naphthas",
    "2515040380":
        "Storage and Transport, Organic Chemical Transport, Pipeline, Toluene",
    "2515040385":
        "Storage and Transport, Organic Chemical Transport, Pipeline, Trichloroethylene",
    "2515040405":
        "Storage and Transport, Organic Chemical Transport, Pipeline, Xylenes (Mixed)",
    "2520000000":
        "Storage and Transport, Inorganic Chemical Storage, All Storage Types: Breathing Loss, Total: All Products",
    "2520000010":
        "Storage and Transport, Inorganic Chemical Storage, All Storage Types: Breathing Loss, Ammonia",
    "2520000020":
        "Storage and Transport, Inorganic Chemical Storage, All Storage Types: Breathing Loss, Hydrochloric Acid",
    "2520000030":
        "Storage and Transport, Inorganic Chemical Storage, All Storage Types: Breathing Loss, Nitric Acid",
    "2520000040":
        "Storage and Transport, Inorganic Chemical Storage, All Storage Types: Breathing Loss, Sulfuric Acid",
    "2520000900":
        "Storage and Transport, Inorganic Chemical Storage, All Storage Types: Breathing Loss, Tank Cleaning",
    "2520010000":
        "Storage and Transport, Inorganic Chemical Storage, Commercial/Industrial: Breathing Loss, Total: All Products",
    "2520010010":
        "Storage and Transport, Inorganic Chemical Storage, Commercial/Industrial: Breathing Loss, Ammonia",
    "2520010020":
        "Storage and Transport, Inorganic Chemical Storage, Commercial/Industrial: Breathing Loss, Hydrochloric Acid",
    "2520010030":
        "Storage and Transport, Inorganic Chemical Storage, Commercial/Industrial: Breathing Loss, Nitric Acid",
    "2520010040":
        "Storage and Transport, Inorganic Chemical Storage, Commercial/Industrial: Breathing Loss, Sulfuric Acid",
    "2520010900":
        "Storage and Transport, Inorganic Chemical Storage, Commercial/Industrial: Breathing Loss, Tank Cleaning",
    "2520050000":
        "Storage and Transport, Inorganic Chemical Storage, Bulk Stations/Terminals: Breathing Loss, Total: All Products",
    "2520050010":
        "Storage and Transport, Inorganic Chemical Storage, Bulk Stations/Terminals: Breathing Loss, Ammonia",
    "2520050020":
        "Storage and Transport, Inorganic Chemical Storage, Bulk Stations/Terminals: Breathing Loss, Hydrochloric Acid",
    "2520050030":
        "Storage and Transport, Inorganic Chemical Storage, Bulk Stations/Terminals: Breathing Loss, Nitric Acid",
    "2520050040":
        "Storage and Transport, Inorganic Chemical Storage, Bulk Stations/Terminals: Breathing Loss, Sulfuric Acid",
    "2520050900":
        "Storage and Transport, Inorganic Chemical Storage, Bulk Stations/Terminals: Breathing Loss, Tank Cleaning",
    "2520995000":
        "Storage and Transport, Inorganic Chemical Storage, All Storage Types: Working Loss, Total: All Products",
    "2520995010":
        "Storage and Transport, Inorganic Chemical Storage, All Storage Types: Working Loss, Ammonia",
    "2520995020":
        "Storage and Transport, Inorganic Chemical Storage, All Storage Types: Working Loss, Hydrochloric Acid",
    "2520995030":
        "Storage and Transport, Inorganic Chemical Storage, All Storage Types: Working Loss, Nitric Acid",
    "2520995040":
        "Storage and Transport, Inorganic Chemical Storage, All Storage Types: Working Loss, Sulfuric Acid",
    "2525000000":
        "Storage and Transport, Inorganic Chemical Transport, All Transport Types, Total: All Products",
    "2525000010":
        "Storage and Transport, Inorganic Chemical Transport, All Transport Types, Ammonia",
    "2525000020":
        "Storage and Transport, Inorganic Chemical Transport, All Transport Types, Hydrochloric Acid",
    "2525000030":
        "Storage and Transport, Inorganic Chemical Transport, All Transport Types, Nitric Acid",
    "2525000040":
        "Storage and Transport, Inorganic Chemical Transport, All Transport Types, Sulfuric Acid",
    "2525000900":
        "Storage and Transport, Inorganic Chemical Transport, All Transport Types, Tank Cleaning",
    "2525010000":
        "Storage and Transport, Inorganic Chemical Transport, Rail Tank Car, Total: All Products",
    "2525010010":
        "Storage and Transport, Inorganic Chemical Transport, Rail Tank Car, Ammonia",
    "2525010020":
        "Storage and Transport, Inorganic Chemical Transport, Rail Tank Car, Hydrochloric Acid",
    "2525010030":
        "Storage and Transport, Inorganic Chemical Transport, Rail Tank Car, Nitric Acid",
    "2525010040":
        "Storage and Transport, Inorganic Chemical Transport, Rail Tank Car, Sulfuric Acid",
    "2525010900":
        "Storage and Transport, Inorganic Chemical Transport, Rail Tank Car, Tank Cleaning",
    "2525020000":
        "Storage and Transport, Inorganic Chemical Transport, Marine Vessel, Total: All Products",
    "2525020010":
        "Storage and Transport, Inorganic Chemical Transport, Marine Vessel, Ammonia",
    "2525020020":
        "Storage and Transport, Inorganic Chemical Transport, Marine Vessel, Hydrochloric Acid",
    "2525020030":
        "Storage and Transport, Inorganic Chemical Transport, Marine Vessel, Nitric Acid",
    "2525020040":
        "Storage and Transport, Inorganic Chemical Transport, Marine Vessel, Sulfuric Acid",
    "2525020900":
        "Storage and Transport, Inorganic Chemical Transport, Marine Vessel, Tank Cleaning",
    "2525030000":
        "Storage and Transport, Inorganic Chemical Transport, Truck, Total: All Products",
    "2525030010":
        "Storage and Transport, Inorganic Chemical Transport, Truck, Ammonia",
    "2525030020":
        "Storage and Transport, Inorganic Chemical Transport, Truck, Hydrochloric Acid",
    "2525030030":
        "Storage and Transport, Inorganic Chemical Transport, Truck, Nitric Acid",
    "2525030040":
        "Storage and Transport, Inorganic Chemical Transport, Truck, Sulfuric Acid",
    "2525030900":
        "Storage and Transport, Inorganic Chemical Transport, Truck, Tank Cleaning",
    "2525040000":
        "Storage and Transport, Inorganic Chemical Transport, Pipeline, Total: All Products",
    "2525040010":
        "Storage and Transport, Inorganic Chemical Transport, Pipeline, Ammonia",
    "2525040020":
        "Storage and Transport, Inorganic Chemical Transport, Pipeline, Hydrochloric Acid",
    "2525040030":
        "Storage and Transport, Inorganic Chemical Transport, Pipeline, Nitric Acid",
    "2525040040":
        "Storage and Transport, Inorganic Chemical Transport, Pipeline, Sulfuric Acid",
    "2530000000":
        "Storage and Transport, Bulk Materials Storage, All Storage Types, Total: All Products",
    "2530000020":
        "Storage and Transport, Bulk Materials Storage, All Storage Types, Cement",
    "2530000040":
        "Storage and Transport, Bulk Materials Storage, All Storage Types, Coal",
    "2530000060":
        "Storage and Transport, Bulk Materials Storage, All Storage Types, Crushed Stone",
    "2530000080":
        "Storage and Transport, Bulk Materials Storage, All Storage Types, Gravel",
    "2530000100":
        "Storage and Transport, Bulk Materials Storage, All Storage Types, Limestone",
    "2530000120":
        "Storage and Transport, Bulk Materials Storage, All Storage Types, Sand",
    "2530010000":
        "Storage and Transport, Bulk Materials Storage, Commercial/Industrial, Total: All Products",
    "2530010020":
        "Storage and Transport, Bulk Materials Storage, Commercial/Industrial, Cement",
    "2530010040":
        "Storage and Transport, Bulk Materials Storage, Commercial/Industrial, Coal",
    "2530010060":
        "Storage and Transport, Bulk Materials Storage, Commercial/Industrial, Crushed Stone",
    "2530010080":
        "Storage and Transport, Bulk Materials Storage, Commercial/Industrial, Gravel",
    "2530010100":
        "Storage and Transport, Bulk Materials Storage, Commercial/Industrial, Limestone",
    "2530010120":
        "Storage and Transport, Bulk Materials Storage, Commercial/Industrial, Sand",
    "2530050000":
        "Storage and Transport, Bulk Materials Storage, Bulk Stations/Terminals, Total: All Products",
    "2530050020":
        "Storage and Transport, Bulk Materials Storage, Bulk Stations/Terminals, Cement",
    "2530050040":
        "Storage and Transport, Bulk Materials Storage, Bulk Stations/Terminals, Coal",
    "2530050060":
        "Storage and Transport, Bulk Materials Storage, Bulk Stations/Terminals, Crushed Stone",
    "2530050080":
        "Storage and Transport, Bulk Materials Storage, Bulk Stations/Terminals, Gravel",
    "2530050100":
        "Storage and Transport, Bulk Materials Storage, Bulk Stations/Terminals, Limestone",
    "2530050120":
        "Storage and Transport, Bulk Materials Storage, Bulk Stations/Terminals, Sand",
    "2535000000":
        "Storage and Transport, Bulk Materials Transport, All Transport Types, Total: All Products",
    "2535000020":
        "Storage and Transport, Bulk Materials Transport, All Transport Types, Cement",
    "2535000040":
        "Storage and Transport, Bulk Materials Transport, All Transport Types, Coal",
    "2535000060":
        "Storage and Transport, Bulk Materials Transport, All Transport Types, Crushed Stone",
    "2535000080":
        "Storage and Transport, Bulk Materials Transport, All Transport Types, Gravel",
    "2535000100":
        "Storage and Transport, Bulk Materials Transport, All Transport Types, Limestone",
    "2535000120":
        "Storage and Transport, Bulk Materials Transport, All Transport Types, Sand",
    "2535000140":
        "Storage and Transport, Bulk Materials Transport, All Transport Types, Phosphate Rock",
    "2535010000":
        "Storage and Transport, Bulk Materials Transport, Rail Car, Total: All Products",
    "2535010020":
        "Storage and Transport, Bulk Materials Transport, Rail Car, Cement",
    "2535010040":
        "Storage and Transport, Bulk Materials Transport, Rail Car, Coal",
    "2535010060":
        "Storage and Transport, Bulk Materials Transport, Rail Car, Crushed Stone",
    "2535010080":
        "Storage and Transport, Bulk Materials Transport, Rail Car, Gravel",
    "2535010100":
        "Storage and Transport, Bulk Materials Transport, Rail Car, Limestone",
    "2535010120":
        "Storage and Transport, Bulk Materials Transport, Rail Car, Sand",
    "2535010140":
        "Storage and Transport, Bulk Materials Transport, Rail Car, Phosphate Rock",
    "2535020000":
        "Storage and Transport, Bulk Materials Transport, Marine Vessel, Total: All Products",
    "2535020020":
        "Storage and Transport, Bulk Materials Transport, Marine Vessel, Cement",
    "2535020040":
        "Storage and Transport, Bulk Materials Transport, Marine Vessel, Coal",
    "2535020060":
        "Storage and Transport, Bulk Materials Transport, Marine Vessel, Crushed Stone",
    "2535020080":
        "Storage and Transport, Bulk Materials Transport, Marine Vessel, Gravel",
    "2535020100":
        "Storage and Transport, Bulk Materials Transport, Marine Vessel, Limestone",
    "2535020120":
        "Storage and Transport, Bulk Materials Transport, Marine Vessel, Sand",
    "2535020140":
        "Storage and Transport, Bulk Materials Transport, Marine Vessel, Phosphate Rock",
    "2535030000":
        "Storage and Transport, Bulk Materials Transport, Truck, Total: All Products",
    "2535030020":
        "Storage and Transport, Bulk Materials Transport, Truck, Cement",
    "2535030040":
        "Storage and Transport, Bulk Materials Transport, Truck, Coal",
    "2535030060":
        "Storage and Transport, Bulk Materials Transport, Truck, Crushed Stone",
    "2535030080":
        "Storage and Transport, Bulk Materials Transport, Truck, Gravel",
    "2535030100":
        "Storage and Transport, Bulk Materials Transport, Truck, Limestone",
    "2535030120":
        "Storage and Transport, Bulk Materials Transport, Truck, Sand",
    "2535030140":
        "Storage and Transport, Bulk Materials Transport, Truck, Phosphate Rock",
    "2999001001":
        "very misc, holding scc, for state-reported, unknown SCCs",
    "2601000000":
        "Waste Disposal, Treatment, and Recovery, On-site Incineration, All Categories, Total",
    "2601010000":
        "Waste Disposal, Treatment, and Recovery, On-site Incineration, Industrial, Total",
    "2601020000":
        "Waste Disposal, Treatment, and Recovery, On-site Incineration, Commercial/Institutional, Total",
    "2601030000":
        "Waste Disposal, Treatment, and Recovery, On-site Incineration, Residential, Total",
    "2610000000":
        "Waste Disposal, Treatment, and Recovery, Open Burning, All Categories, Total",
    "2610000100":
        "Waste Disposal, Treatment, and Recovery, Open Burning, All Categories, Yard Waste - Leaf Species Unspecified",
    "2610000110":
        "Waste Disposal, Treatment, and Recovery, Open Burning, All Categories, Leaf Species is Black Ash",
    "2610000120":
        "Waste Disposal, Treatment, and Recovery, Open Burning, All Categories, Leaf Species is Modesto Ash",
    "2610000130":
        "Waste Disposal, Treatment, and Recovery, Open Burning, All Categories, Leaf Species is White Ash",
    "2610000140":
        "Waste Disposal, Treatment, and Recovery, Open Burning, All Categories, Leaf Species is Catalpa",
    "2610000150":
        "Waste Disposal, Treatment, and Recovery, Open Burning, All Categories, Leaf Species is Horse Chestnut",
    "2610000160":
        "Waste Disposal, Treatment, and Recovery, Open Burning, All Categories, Leaf Species is Cottonwood",
    "2610000170":
        "Waste Disposal, Treatment, and Recovery, Open Burning, All Categories, Leaf Species is American Elm",
    "2610000180":
        "Waste Disposal, Treatment, and Recovery, Open Burning, All Categories, Leaf Species is Eucalyptus",
    "2610000190":
        "Waste Disposal, Treatment, and Recovery, Open Burning, All Categories, Leaf Species is Sweet Gum",
    "2610000200":
        "Waste Disposal, Treatment, and Recovery, Open Burning, All Categories, Leaf Species is Black Locust",
    "2610000210":
        "Waste Disposal, Treatment, and Recovery, Open Burning, All Categories, Leaf Species is Magnolia",
    "2610000220":
        "Waste Disposal, Treatment, and Recovery, Open Burning, All Categories, Leaf Species is Silver Maple",
    "2610000230":
        "Waste Disposal, Treatment, and Recovery, Open Burning, All Categories, Leaf Species is American Sycamore",
    "2610000240":
        "Waste Disposal, Treatment, and Recovery, Open Burning, All Categories, Leaf Species is California Sycamore",
    "2610000250":
        "Waste Disposal, Treatment, and Recovery, Open Burning, All Categories, Leaf Species is Tulip",
    "2610000260":
        "Waste Disposal, Treatment, and Recovery, Open Burning, All Categories, Leaf Species is Red Oak",
    "2610000270":
        "Waste Disposal, Treatment, and Recovery, Open Burning, All Categories, Leaf Species is Sugar Maple",
    "2610000300":
        "Waste Disposal, Treatment, and Recovery, Open Burning, All Categories, Yard Waste - Weed Species Unspecified (incl Grass)",
    "2610000310":
        "Waste Disposal, Treatment, and Recovery, Open Burning, All Categories, Weed Species is Russian thistle (tumbleweed)",
    "2610000320":
        "Waste Disposal, Treatment, and Recovery, Open Burning, All Categories, Weed Species is Tales (wild reeds)",
    "2610000400":
        "Waste Disposal, Treatment, and Recovery, Open Burning, All Categories, Yard Waste - Brush Species Unspecified",
    "2610000500":
        "Waste Disposal, Treatment, and Recovery, Open Burning, All Categories, Land Clearing Debris (use 28-10-005-000 for Logging Debris Burning)",
    "2610010000":
        "Waste Disposal, Treatment, and Recovery, Open Burning, Industrial, Total",
    "2610020000":
        "Waste Disposal, Treatment, and Recovery, Open Burning, Commercial/Institutional, Total",
    "2610030000":
        "Waste Disposal, Treatment, and Recovery, Open Burning, Residential, Household Waste (use 26-10-000-xxx for Yard Wastes)",
    "2610040400":
        "Waste Disposal, Treatment, and Recovery, Open Burning, Municipal (collected from residences, parks,other for central burn), Yard Waste - Total (includes Leaves, Weeds, and Brush)",
    "2620000000":
        "Waste Disposal, Treatment, and Recovery, Landfills, All Categories, Total",
    "2620010000":
        "Waste Disposal, Treatment, and Recovery, Landfills, Industrial, Total",
    "2620020000":
        "Waste Disposal, Treatment, and Recovery, Landfills, Commercial/Institutional, Total",
    "2620030000":
        "Waste Disposal, Treatment, and Recovery, Landfills, Municipal, Total",
    "2620030001":
        "Waste Disposal, Treatment, and Recovery, Landfills, Municipal, Dumping/Crushing/Spreading of New Materials (working face)",
    "2630000000":
        "Waste Disposal, Treatment, and Recovery, Wastewater Treatment, All Categories, Total Processed",
    "2630010000":
        "Waste Disposal, Treatment, and Recovery, Wastewater Treatment, Industrial, Total Processed",
    "2630020000":
        "Waste Disposal, Treatment, and Recovery, Wastewater Treatment, Public Owned, Total Processed",
    "2630020001":
        "Waste Disposal, Treatment, and Recovery, Wastewater Treatment, Public Owned, Flaring of Gases",
    "2630020010":
        "Waste Disposal, Treatment, and Recovery, Wastewater Treatment, Public Owned, Wastewater Treatment Processes Total",
    "2630020020":
        "Waste Disposal, Treatment, and Recovery, Wastewater Treatment, Public Owned, Biosolids Processes Total",
    "2630030000":
        "Waste Disposal, Treatment, and Recovery, Wastewater Treatment, Residential/Subdivision Owned, Total Processed",
    "2630040000":
        "Waste Disposal, Treatment, and Recovery, Wastewater Treatment, Public Owned, Ammonia pH Control",
    "2630050000":
        "Waste Disposal, Treatment, and Recovery, Wastewater Treatment, Public Owned, Land Application - Digested Sludge",
    "2635000000":
        "Waste Disposal, Treatment, and Recovery, Soil and Groundwater Remediation, All Categories, Total",
    "2640000000":
        "Waste Disposal, Treatment, and Recovery, TSDFs, All TSDF Types, Total: All Processes",
    "2640000001":
        "Waste Disposal, Treatment, and Recovery, TSDFs, All TSDF Types, Surface Impoundments",
    "2640000002":
        "Waste Disposal, Treatment, and Recovery, TSDFs, All TSDF Types, Land Treatment",
    "2640000003":
        "Waste Disposal, Treatment, and Recovery, TSDFs, All TSDF Types, Landfills",
    "2640000004":
        "Waste Disposal, Treatment, and Recovery, TSDFs, All TSDF Types, Transfer, Storage, and Handling",
    "2640010000":
        "Waste Disposal, Treatment, and Recovery, TSDFs, Industrial, Total: All Processes",
    "2640010001":
        "Waste Disposal, Treatment, and Recovery, TSDFs, Industrial, Surface Impoundments",
    "2640010002":
        "Waste Disposal, Treatment, and Recovery, TSDFs, Industrial, Land Treatment",
    "2640010003":
        "Waste Disposal, Treatment, and Recovery, TSDFs, Industrial, Landfills",
    "2640010004":
        "Waste Disposal, Treatment, and Recovery, TSDFs, Industrial, Transfer, Storage, and Handling",
    "2640020000":
        "Waste Disposal, Treatment, and Recovery, TSDFs, Commercial/Institutional, Total: All Processes",
    "2640020001":
        "Waste Disposal, Treatment, and Recovery, TSDFs, Commercial/Institutional, Surface Impoundments",
    "2640020002":
        "Waste Disposal, Treatment, and Recovery, TSDFs, Commercial/Institutional, Land Treatment",
    "2640020003":
        "Waste Disposal, Treatment, and Recovery, TSDFs, Commercial/Institutional, Landfills",
    "2640020004":
        "Waste Disposal, Treatment, and Recovery, TSDFs, Commercial/Institutional, Transfer, Storage, and Handling",
    "2650000000":
        "Waste Disposal, Treatment, and Recovery, Scrap and Waste Materials, Scrap and Waste Materials, Total: All Processes",
    "2650000001":
        "Waste Disposal, Treatment, and Recovery, Scrap and Waste Materials, Scrap and Waste Materials, Crushing",
    "2650000002":
        "Waste Disposal, Treatment, and Recovery, Scrap and Waste Materials, Scrap and Waste Materials, Shredding",
    "2650000003":
        "Waste Disposal, Treatment, and Recovery, Scrap and Waste Materials, Scrap and Waste Materials, Sorting",
    "2650000004":
        "Waste Disposal, Treatment, and Recovery, Scrap and Waste Materials, Scrap and Waste Materials, Transferring",
    "2650000005":
        "Waste Disposal, Treatment, and Recovery, Scrap and Waste Materials, Scrap and Waste Materials, Storage Piles",
    "2660000000":
        "Waste Disposal, Treatment, and Recovery, Leaking Underground Storage Tanks, Leaking Underground Storage Tanks, Total: All Storage Types",
    "2670001000":
        "Waste Disposal, Treatment, and Recovery, Munitions Detonation, TNT Detonation, General",
    "2670002000":
        "Waste Disposal, Treatment, and Recovery, Munitions Detonation, RDX Detonation, General",
    "2670003000":
        "Waste Disposal, Treatment, and Recovery, Munitions Detonation, PETN Detonation, General",
    "2680001000":
        "Waste Disposal, Treatment, and Recovery, Composting, 100% Biosolids (e.g., sewage sludge, manure, mixtures of these matls), All Processes",
    "2680002000":
        "Waste Disposal, Treatment, and Recovery, Composting, Mixed Waste (e.g., a 50:50 mixture of biosolids and green wastes), All Processes",
    "2680003000":
        "Waste Disposal, Treatment, and Recovery, Composting, 100% Green Waste (e.g., residential or municipal yard wastes), All Processes",
    "2680003010":
        "Waste Disposal, Treatment, and Recovery, Composting, 100% Green Waste (e.g., residential or municipal yard wastes), Chipping&Shredding Ops(where processed matl is shipped out w/in 1 day)"
}
