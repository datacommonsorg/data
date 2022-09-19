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
    "2205320080":
        "MobileSources HighwayVehiclesEthanolE85 LightCommercialTruck Allonandoffnetworkprocessesexceptrefueling",
    "2202410080":
        "MobileSources HighwayVehiclesDiesel OtherBuses Allonandoffnetworkprocessesexceptrefueling",
    "2201110080":
        "MobileSources HighwayVehiclesGasoline Motorcycle Allonandoffnetworkprocessesexceptrefueling",
    "2202430080":
        "MobileSources HighwayVehiclesDiesel SchoolBus Allonandoffnetworkprocessesexceptrefueling",
    "2202420080":
        "MobileSources HighwayVehiclesDiesel TransitBus Allonandoffnetworkprocessesexceptrefueling",
    "2202540080":
        "MobileSources HighwayVehiclesDiesel MotorHome Allonandoffnetworkprocessesexceptrefueling",
    "2202320080":
        "MobileSources HighwayVehiclesDiesel LightCommercialTruck Allonandoffnetworkprocessesexceptrefueling",
    "2202530080":
        "MobileSources HighwayVehiclesDiesel SingleUnitLonghaulTruck Allonandoffnetworkprocessesexceptrefueling",
    "2201520080":
        "MobileSources HighwayVehiclesGasoline SingleUnitShorthaulTruck Allonandoffnetworkprocessesexceptrefueling",
    "2201510080":
        "MobileSources HighwayVehiclesGasoline RefuseTruck Allonandoffnetworkprocessesexceptrefueling",
    "2202510080":
        "MobileSources HighwayVehiclesDiesel RefuseTruck Allonandoffnetworkprocessesexceptrefueling",
    "2205310080":
        "MobileSources HighwayVehiclesEthanolE85 PassengerTruck Allonandoffnetworkprocessesexceptrefueling",
    "2205210080":
        "MobileSources HighwayVehiclesEthanolE85 PassengerCar Allonandoffnetworkprocessesexceptrefueling",
    "2201310080":
        "MobileSources HighwayVehiclesGasoline PassengerTruck Allonandoffnetworkprocessesexceptrefueling",
    "2201430080":
        "MobileSources HighwayVehiclesGasoline SchoolBus Allonandoffnetworkprocessesexceptrefueling",
    "2201000062":
        "MobileSources HighwayVehiclesGasoline Refueling TotalSpillageandDisplacement",
    "2201530080":
        "MobileSources HighwayVehiclesGasoline SingleUnitLonghaulTruck Allonandoffnetworkprocessesexceptrefueling",
    "2202310080":
        "MobileSources HighwayVehiclesDiesel PassengerTruck Allonandoffnetworkprocessesexceptrefueling",
    "2201210080":
        "MobileSources HighwayVehiclesGasoline PassengerCar Allonandoffnetworkprocessesexceptrefueling",
    "2201610080":
        "MobileSources HighwayVehiclesGasoline CombinationShorthaulTruck Allonandoffnetworkprocessesexceptrefueling",
    "2202210080":
        "MobileSources HighwayVehiclesDiesel PassengerCar Allonandoffnetworkprocessesexceptrefueling",
    "2202620080":
        "MobileSources HighwayVehiclesDiesel CombinationLonghaulTruck Allonandoffnetworkprocessesexceptrefueling",
    "2202520080":
        "MobileSources HighwayVehiclesDiesel SingleUnitShorthaulTruck Allonandoffnetworkprocessesexceptrefueling",
    "2202610080":
        "MobileSources HighwayVehiclesDiesel CombinationShorthaulTruck Allonandoffnetworkprocessesexceptrefueling",
    "2202000062":
        "MobileSources HighwayVehiclesDiesel Refueling TotalSpillageandDisplacement",
    "2201540080":
        "MobileSources HighwayVehiclesGasoline MotorHome Allonandoffnetworkprocessesexceptrefueling",
    "2201420080":
        "MobileSources HighwayVehiclesGasoline TransitBus Allonandoffnetworkprocessesexceptrefueling",
    "2205000062":
        "MobileSources HighwayVehiclesEthanolE85 Refueling TotalSpillageandDisplacement",
    "2201320080":
        "MobileSources HighwayVehiclesGasoline LightCommercialTruck Allonandoffnetworkprocessesexceptrefueling",
    "2203420080":
        "MobileSources HighwayVehiclesCompressedNaturalGasCNG TransitBus Allonandoffnetworkprocessesexceptrefueling",
    "2209310080":
        "MobileSources HighwayVehiclesElectricity PassengerTruck Allonandoffnetworkprocessesexceptrefueling",
    "2209210080":
        "MobileSources HighwayVehiclesElectricity PassengerCar Allonandoffnetworkprocessesexceptrefueling",
    "2201001110":
        "MobileSources HighwayVehiclesGasoline LightDutyGasolineVehiclesLDGV RuralInterstateTotal",
    "2201001130":
        "MobileSources HighwayVehiclesGasoline LightDutyGasolineVehiclesLDGV RuralOtherPrincipalArterialTotal",
    "2201001150":
        "MobileSources HighwayVehiclesGasoline LightDutyGasolineVehiclesLDGV RuralMinorArterialTotal",
    "2201001170":
        "MobileSources HighwayVehiclesGasoline LightDutyGasolineVehiclesLDGV RuralMajorCollectorTotal",
    "2201001190":
        "MobileSources HighwayVehiclesGasoline LightDutyGasolineVehiclesLDGV RuralMinorCollectorTotal",
    "2201001210":
        "MobileSources HighwayVehiclesGasoline LightDutyGasolineVehiclesLDGV RuralLocalTotal",
    "2201001230":
        "MobileSources HighwayVehiclesGasoline LightDutyGasolineVehiclesLDGV UrbanInterstateTotal",
    "2201001250":
        "MobileSources HighwayVehiclesGasoline LightDutyGasolineVehiclesLDGV UrbanOtherFreewaysandExpresswaysTotal",
    "2201001270":
        "MobileSources HighwayVehiclesGasoline LightDutyGasolineVehiclesLDGV UrbanOtherPrincipalArterialTotal",
    "2201001290":
        "MobileSources HighwayVehiclesGasoline LightDutyGasolineVehiclesLDGV UrbanMinorArterialTotal",
    "2201001310":
        "MobileSources HighwayVehiclesGasoline LightDutyGasolineVehiclesLDGV UrbanCollectorTotal",
    "2201001330":
        "MobileSources HighwayVehiclesGasoline LightDutyGasolineVehiclesLDGV UrbanLocalTotal",
    "2201001390":
        "MobileSources HighwayVehiclesGasoline LightDutyGasolineVehiclesLDGV ParkingAreaTotal",
    "2201020110":
        "MobileSources HighwayVehiclesGasoline LightDutyGasolineTrucks1&2M6LDGT1M5 RuralInterstateTotal",
    "2201020130":
        "MobileSources HighwayVehiclesGasoline LightDutyGasolineTrucks1&2M6LDGT1M5 RuralOtherPrincipalArterialTotal",
    "2201020150":
        "MobileSources HighwayVehiclesGasoline LightDutyGasolineTrucks1&2M6LDGT1M5 RuralMinorArterialTotal",
    "2201020170":
        "MobileSources HighwayVehiclesGasoline LightDutyGasolineTrucks1&2M6LDGT1M5 RuralMajorCollectorTotal",
    "2201020190":
        "MobileSources HighwayVehiclesGasoline LightDutyGasolineTrucks1&2M6LDGT1M5 RuralMinorCollectorTotal",
    "2201020210":
        "MobileSources HighwayVehiclesGasoline LightDutyGasolineTrucks1&2M6LDGT1M5 RuralLocalTotal",
    "2201020230":
        "MobileSources HighwayVehiclesGasoline LightDutyGasolineTrucks1&2M6LDGT1M5 UrbanInterstateTotal",
    "2201020250":
        "MobileSources HighwayVehiclesGasoline LightDutyGasolineTrucks1&2M6LDGT1M5 UrbanOtherFreewaysandExpresswaysTotal",
    "2201020270":
        "MobileSources HighwayVehiclesGasoline LightDutyGasolineTrucks1&2M6LDGT1M5 UrbanOtherPrincipalArterialTotal",
    "2201020290":
        "MobileSources HighwayVehiclesGasoline LightDutyGasolineTrucks1&2M6LDGT1M5 UrbanMinorArterialTotal",
    "2201020310":
        "MobileSources HighwayVehiclesGasoline LightDutyGasolineTrucks1&2M6LDGT1M5 UrbanCollectorTotal",
    "2201020330":
        "MobileSources HighwayVehiclesGasoline LightDutyGasolineTrucks1&2M6LDGT1M5 UrbanLocalTotal",
    "2201020390":
        "MobileSources HighwayVehiclesGasoline LightDutyGasolineTrucks1&2M6LDGT1M5 ParkingAreaTotal",
    "2201040110":
        "MobileSources HighwayVehiclesGasoline LightDutyGasolineTrucks3&4M6LDGT2M5 RuralInterstateTotal",
    "2201040130":
        "MobileSources HighwayVehiclesGasoline LightDutyGasolineTrucks3&4M6LDGT2M5 RuralOtherPrincipalArterialTotal",
    "2201040150":
        "MobileSources HighwayVehiclesGasoline LightDutyGasolineTrucks3&4M6LDGT2M5 RuralMinorArterialTotal",
    "2201040170":
        "MobileSources HighwayVehiclesGasoline LightDutyGasolineTrucks3&4M6LDGT2M5 RuralMajorCollectorTotal",
    "2201040190":
        "MobileSources HighwayVehiclesGasoline LightDutyGasolineTrucks3&4M6LDGT2M5 RuralMinorCollectorTotal",
    "2201040210":
        "MobileSources HighwayVehiclesGasoline LightDutyGasolineTrucks3&4M6LDGT2M5 RuralLocalTotal",
    "2201040230":
        "MobileSources HighwayVehiclesGasoline LightDutyGasolineTrucks3&4M6LDGT2M5 UrbanInterstateTotal",
    "2201040250":
        "MobileSources HighwayVehiclesGasoline LightDutyGasolineTrucks3&4M6LDGT2M5 UrbanOtherFreewaysandExpresswaysTotal",
    "2201040270":
        "MobileSources HighwayVehiclesGasoline LightDutyGasolineTrucks3&4M6LDGT2M5 UrbanOtherPrincipalArterialTotal",
    "2201040290":
        "MobileSources HighwayVehiclesGasoline LightDutyGasolineTrucks3&4M6LDGT2M5 UrbanMinorArterialTotal",
    "2201040310":
        "MobileSources HighwayVehiclesGasoline LightDutyGasolineTrucks3&4M6LDGT2M5 UrbanCollectorTotal",
    "2201040330":
        "MobileSources HighwayVehiclesGasoline LightDutyGasolineTrucks3&4M6LDGT2M5 UrbanLocalTotal",
    "2201040390":
        "MobileSources HighwayVehiclesGasoline LightDutyGasolineTrucks3&4M6LDGT2M5 ParkingAreaTotal",
    "2201070110":
        "MobileSources HighwayVehiclesGasoline HeavyDutyGasolineVehicles2Bthru8B&BusesHDGV RuralInterstateTotal",
    "2201070130":
        "MobileSources HighwayVehiclesGasoline HeavyDutyGasolineVehicles2Bthru8B&BusesHDGV RuralOtherPrincipalArterialTotal",
    "2201070150":
        "MobileSources HighwayVehiclesGasoline HeavyDutyGasolineVehicles2Bthru8B&BusesHDGV RuralMinorArterialTotal",
    "2201070170":
        "MobileSources HighwayVehiclesGasoline HeavyDutyGasolineVehicles2Bthru8B&BusesHDGV RuralMajorCollectorTotal",
    "2201070190":
        "MobileSources HighwayVehiclesGasoline HeavyDutyGasolineVehicles2Bthru8B&BusesHDGV RuralMinorCollectorTotal",
    "2201070210":
        "MobileSources HighwayVehiclesGasoline HeavyDutyGasolineVehicles2Bthru8B&BusesHDGV RuralLocalTotal",
    "2201070230":
        "MobileSources HighwayVehiclesGasoline HeavyDutyGasolineVehicles2Bthru8B&BusesHDGV UrbanInterstateTotal",
    "2201070250":
        "MobileSources HighwayVehiclesGasoline HeavyDutyGasolineVehicles2Bthru8B&BusesHDGV UrbanOtherFreewaysandExpresswaysTotal",
    "2201070270":
        "MobileSources HighwayVehiclesGasoline HeavyDutyGasolineVehicles2Bthru8B&BusesHDGV UrbanOtherPrincipalArterialTotal",
    "2201070290":
        "MobileSources HighwayVehiclesGasoline HeavyDutyGasolineVehicles2Bthru8B&BusesHDGV UrbanMinorArterialTotal",
    "2201070310":
        "MobileSources HighwayVehiclesGasoline HeavyDutyGasolineVehicles2Bthru8B&BusesHDGV UrbanCollectorTotal",
    "2201070330":
        "MobileSources HighwayVehiclesGasoline HeavyDutyGasolineVehicles2Bthru8B&BusesHDGV UrbanLocalTotal",
    "2201070390":
        "MobileSources HighwayVehiclesGasoline HeavyDutyGasolineVehicles2Bthru8B&BusesHDGV ParkingAreaTotal",
    "2201080110":
        "MobileSources HighwayVehiclesGasoline MotorcyclesMC RuralInterstateTotal",
    "2201080130":
        "MobileSources HighwayVehiclesGasoline MotorcyclesMC RuralOtherPrincipalArterialTotal",
    "2201080150":
        "MobileSources HighwayVehiclesGasoline MotorcyclesMC RuralMinorArterialTotal",
    "2201080170":
        "MobileSources HighwayVehiclesGasoline MotorcyclesMC RuralMajorCollectorTotal",
    "2201080190":
        "MobileSources HighwayVehiclesGasoline MotorcyclesMC RuralMinorCollectorTotal",
    "2201080210":
        "MobileSources HighwayVehiclesGasoline MotorcyclesMC RuralLocalTotal",
    "2201080230":
        "MobileSources HighwayVehiclesGasoline MotorcyclesMC UrbanInterstateTotal",
    "2201080250":
        "MobileSources HighwayVehiclesGasoline MotorcyclesMC UrbanOtherFreewaysandExpresswaysTotal",
    "2201080270":
        "MobileSources HighwayVehiclesGasoline MotorcyclesMC UrbanOtherPrincipalArterialTotal",
    "2201080290":
        "MobileSources HighwayVehiclesGasoline MotorcyclesMC UrbanMinorArterialTotal",
    "2201080310":
        "MobileSources HighwayVehiclesGasoline MotorcyclesMC UrbanCollectorTotal",
    "2201080330":
        "MobileSources HighwayVehiclesGasoline MotorcyclesMC UrbanLocalTotal",
    "2201080390":
        "MobileSources HighwayVehiclesGasoline MotorcyclesMC ParkingAreaTotal",
    "2230001110":
        "MobileSources HighwayVehiclesDiesel LightDutyDieselVehiclesLDDV RuralInterstateTotal",
    "2230001130":
        "MobileSources HighwayVehiclesDiesel LightDutyDieselVehiclesLDDV RuralOtherPrincipalArterialTotal",
    "2230001150":
        "MobileSources HighwayVehiclesDiesel LightDutyDieselVehiclesLDDV RuralMinorArterialTotal",
    "2230001170":
        "MobileSources HighwayVehiclesDiesel LightDutyDieselVehiclesLDDV RuralMajorCollectorTotal",
    "2230001190":
        "MobileSources HighwayVehiclesDiesel LightDutyDieselVehiclesLDDV RuralMinorCollectorTotal",
    "2230001210":
        "MobileSources HighwayVehiclesDiesel LightDutyDieselVehiclesLDDV RuralLocalTotal",
    "2230001230":
        "MobileSources HighwayVehiclesDiesel LightDutyDieselVehiclesLDDV UrbanInterstateTotal",
    "2230001250":
        "MobileSources HighwayVehiclesDiesel LightDutyDieselVehiclesLDDV UrbanOtherFreewaysandExpresswaysTotal",
    "2230001270":
        "MobileSources HighwayVehiclesDiesel LightDutyDieselVehiclesLDDV UrbanOtherPrincipalArterialTotal",
    "2230001290":
        "MobileSources HighwayVehiclesDiesel LightDutyDieselVehiclesLDDV UrbanMinorArterialTotal",
    "2230001310":
        "MobileSources HighwayVehiclesDiesel LightDutyDieselVehiclesLDDV UrbanCollectorTotal",
    "2230001330":
        "MobileSources HighwayVehiclesDiesel LightDutyDieselVehiclesLDDV UrbanLocalTotal",
    "2230001390":
        "MobileSources HighwayVehiclesDiesel LightDutyDieselVehiclesLDDV ParkingAreaTotal",
    "2230060110":
        "MobileSources HighwayVehiclesDiesel LightDutyDieselTrucks1thru4M6LDDT RuralInterstateTotal",
    "2230060130":
        "MobileSources HighwayVehiclesDiesel LightDutyDieselTrucks1thru4M6LDDT RuralOtherPrincipalArterialTotal",
    "2230060150":
        "MobileSources HighwayVehiclesDiesel LightDutyDieselTrucks1thru4M6LDDT RuralMinorArterialTotal",
    "2230060170":
        "MobileSources HighwayVehiclesDiesel LightDutyDieselTrucks1thru4M6LDDT RuralMajorCollectorTotal",
    "2230060190":
        "MobileSources HighwayVehiclesDiesel LightDutyDieselTrucks1thru4M6LDDT RuralMinorCollectorTotal",
    "2230060210":
        "MobileSources HighwayVehiclesDiesel LightDutyDieselTrucks1thru4M6LDDT RuralLocalTotal",
    "2230060230":
        "MobileSources HighwayVehiclesDiesel LightDutyDieselTrucks1thru4M6LDDT UrbanInterstateTotal",
    "2230060250":
        "MobileSources HighwayVehiclesDiesel LightDutyDieselTrucks1thru4M6LDDT UrbanOtherFreewaysandExpresswaysTotal",
    "2230060270":
        "MobileSources HighwayVehiclesDiesel LightDutyDieselTrucks1thru4M6LDDT UrbanOtherPrincipalArterialTotal",
    "2230060290":
        "MobileSources HighwayVehiclesDiesel LightDutyDieselTrucks1thru4M6LDDT UrbanMinorArterialTotal",
    "2230060310":
        "MobileSources HighwayVehiclesDiesel LightDutyDieselTrucks1thru4M6LDDT UrbanCollectorTotal",
    "2230060330":
        "MobileSources HighwayVehiclesDiesel LightDutyDieselTrucks1thru4M6LDDT UrbanLocalTotal",
    "2230060390":
        "MobileSources HighwayVehiclesDiesel LightDutyDieselTrucks1thru4M6LDDT ParkingAreaTotal",
    "2230071110":
        "MobileSources HighwayVehiclesDiesel HeavyDutyDieselVehiclesHDDVClass2B RuralInterstateTotal",
    "2230071130":
        "MobileSources HighwayVehiclesDiesel HeavyDutyDieselVehiclesHDDVClass2B RuralOtherPrincipalArterialTotal",
    "2230071150":
        "MobileSources HighwayVehiclesDiesel HeavyDutyDieselVehiclesHDDVClass2B RuralMinorArterialTotal",
    "2230071170":
        "MobileSources HighwayVehiclesDiesel HeavyDutyDieselVehiclesHDDVClass2B RuralMajorCollectorTotal",
    "2230071190":
        "MobileSources HighwayVehiclesDiesel HeavyDutyDieselVehiclesHDDVClass2B RuralMinorCollectorTotal",
    "2230071210":
        "MobileSources HighwayVehiclesDiesel HeavyDutyDieselVehiclesHDDVClass2B RuralLocalTotal",
    "2230071230":
        "MobileSources HighwayVehiclesDiesel HeavyDutyDieselVehiclesHDDVClass2B UrbanInterstateTotal",
    "2230071250":
        "MobileSources HighwayVehiclesDiesel HeavyDutyDieselVehiclesHDDVClass2B UrbanOtherFreewaysandExpresswaysTotal",
    "2230071270":
        "MobileSources HighwayVehiclesDiesel HeavyDutyDieselVehiclesHDDVClass2B UrbanOtherPrincipalArterialTotal",
    "2230071290":
        "MobileSources HighwayVehiclesDiesel HeavyDutyDieselVehiclesHDDVClass2B UrbanMinorArterialTotal",
    "2230071310":
        "MobileSources HighwayVehiclesDiesel HeavyDutyDieselVehiclesHDDVClass2B UrbanCollectorTotal",
    "2230071330":
        "MobileSources HighwayVehiclesDiesel HeavyDutyDieselVehiclesHDDVClass2B UrbanLocalTotal",
    "2230071390":
        "MobileSources HighwayVehiclesDiesel HeavyDutyDieselVehiclesHDDVClass2B ParkingAreaTotal",
    "2230072110":
        "MobileSources HighwayVehiclesDiesel HeavyDutyDieselVehiclesHDDVClass34&5 RuralInterstateTotal",
    "2230072130":
        "MobileSources HighwayVehiclesDiesel HeavyDutyDieselVehiclesHDDVClass34&5 RuralOtherPrincipalArterialTotal",
    "2230072150":
        "MobileSources HighwayVehiclesDiesel HeavyDutyDieselVehiclesHDDVClass34&5 RuralMinorArterialTotal",
    "2230072170":
        "MobileSources HighwayVehiclesDiesel HeavyDutyDieselVehiclesHDDVClass34&5 RuralMajorCollectorTotal",
    "2230072190":
        "MobileSources HighwayVehiclesDiesel HeavyDutyDieselVehiclesHDDVClass34&5 RuralMinorCollectorTotal",
    "2230072210":
        "MobileSources HighwayVehiclesDiesel HeavyDutyDieselVehiclesHDDVClass34&5 RuralLocalTotal",
    "2230072230":
        "MobileSources HighwayVehiclesDiesel HeavyDutyDieselVehiclesHDDVClass34&5 UrbanInterstateTotal",
    "2230072250":
        "MobileSources HighwayVehiclesDiesel HeavyDutyDieselVehiclesHDDVClass34&5 UrbanOtherFreewaysandExpresswaysTotal",
    "2230072270":
        "MobileSources HighwayVehiclesDiesel HeavyDutyDieselVehiclesHDDVClass34&5 UrbanOtherPrincipalArterialTotal",
    "2230072290":
        "MobileSources HighwayVehiclesDiesel HeavyDutyDieselVehiclesHDDVClass34&5 UrbanMinorArterialTotal",
    "2230072310":
        "MobileSources HighwayVehiclesDiesel HeavyDutyDieselVehiclesHDDVClass34&5 UrbanCollectorTotal",
    "2230072330":
        "MobileSources HighwayVehiclesDiesel HeavyDutyDieselVehiclesHDDVClass34&5 UrbanLocalTotal",
    "2230072390":
        "MobileSources HighwayVehiclesDiesel HeavyDutyDieselVehiclesHDDVClass34&5 ParkingAreaTotal",
    "2230073110":
        "MobileSources HighwayVehiclesDiesel HeavyDutyDieselVehiclesHDDVClass6&7 RuralInterstateTotal",
    "2230073130":
        "MobileSources HighwayVehiclesDiesel HeavyDutyDieselVehiclesHDDVClass6&7 RuralOtherPrincipalArterialTotal",
    "2230073150":
        "MobileSources HighwayVehiclesDiesel HeavyDutyDieselVehiclesHDDVClass6&7 RuralMinorArterialTotal",
    "2230073170":
        "MobileSources HighwayVehiclesDiesel HeavyDutyDieselVehiclesHDDVClass6&7 RuralMajorCollectorTotal",
    "2230073190":
        "MobileSources HighwayVehiclesDiesel HeavyDutyDieselVehiclesHDDVClass6&7 RuralMinorCollectorTotal",
    "2230073210":
        "MobileSources HighwayVehiclesDiesel HeavyDutyDieselVehiclesHDDVClass6&7 RuralLocalTotal",
    "2230073230":
        "MobileSources HighwayVehiclesDiesel HeavyDutyDieselVehiclesHDDVClass6&7 UrbanInterstateTotal",
    "2230073250":
        "MobileSources HighwayVehiclesDiesel HeavyDutyDieselVehiclesHDDVClass6&7 UrbanOtherFreewaysandExpresswaysTotal",
    "2230073270":
        "MobileSources HighwayVehiclesDiesel HeavyDutyDieselVehiclesHDDVClass6&7 UrbanOtherPrincipalArterialTotal",
    "2230073290":
        "MobileSources HighwayVehiclesDiesel HeavyDutyDieselVehiclesHDDVClass6&7 UrbanMinorArterialTotal",
    "2230073310":
        "MobileSources HighwayVehiclesDiesel HeavyDutyDieselVehiclesHDDVClass6&7 UrbanCollectorTotal",
    "2230073330":
        "MobileSources HighwayVehiclesDiesel HeavyDutyDieselVehiclesHDDVClass6&7 UrbanLocalTotal",
    "2230073390":
        "MobileSources HighwayVehiclesDiesel HeavyDutyDieselVehiclesHDDVClass6&7 ParkingAreaTotal",
    "2230074110":
        "MobileSources HighwayVehiclesDiesel HeavyDutyDieselVehiclesHDDVClass8A&8B RuralInterstateTotal",
    "2230074130":
        "MobileSources HighwayVehiclesDiesel HeavyDutyDieselVehiclesHDDVClass8A&8B RuralOtherPrincipalArterialTotal",
    "2230074150":
        "MobileSources HighwayVehiclesDiesel HeavyDutyDieselVehiclesHDDVClass8A&8B RuralMinorArterialTotal",
    "2230074170":
        "MobileSources HighwayVehiclesDiesel HeavyDutyDieselVehiclesHDDVClass8A&8B RuralMajorCollectorTotal",
    "2230074190":
        "MobileSources HighwayVehiclesDiesel HeavyDutyDieselVehiclesHDDVClass8A&8B RuralMinorCollectorTotal",
    "2230074210":
        "MobileSources HighwayVehiclesDiesel HeavyDutyDieselVehiclesHDDVClass8A&8B RuralLocalTotal",
    "2230074230":
        "MobileSources HighwayVehiclesDiesel HeavyDutyDieselVehiclesHDDVClass8A&8B UrbanInterstateTotal",
    "2230074250":
        "MobileSources HighwayVehiclesDiesel HeavyDutyDieselVehiclesHDDVClass8A&8B UrbanOtherFreewaysandExpresswaysTotal",
    "2230074270":
        "MobileSources HighwayVehiclesDiesel HeavyDutyDieselVehiclesHDDVClass8A&8B UrbanOtherPrincipalArterialTotal",
    "2230074290":
        "MobileSources HighwayVehiclesDiesel HeavyDutyDieselVehiclesHDDVClass8A&8B UrbanMinorArterialTotal",
    "2230074310":
        "MobileSources HighwayVehiclesDiesel HeavyDutyDieselVehiclesHDDVClass8A&8B UrbanCollectorTotal",
    "2230074330":
        "MobileSources HighwayVehiclesDiesel HeavyDutyDieselVehiclesHDDVClass8A&8B UrbanLocalTotal",
    "2230074390":
        "MobileSources HighwayVehiclesDiesel HeavyDutyDieselVehiclesHDDVClass8A&8B ParkingAreaTotal",
    "2230075110":
        "MobileSources HighwayVehiclesDiesel HeavyDutyDieselBusesSchool&Transit RuralInterstateTotal",
    "2230075130":
        "MobileSources HighwayVehiclesDiesel HeavyDutyDieselBusesSchool&Transit RuralOtherPrincipalArterialTotal",
    "2230075150":
        "MobileSources HighwayVehiclesDiesel HeavyDutyDieselBusesSchool&Transit RuralMinorArterialTotal",
    "2230075170":
        "MobileSources HighwayVehiclesDiesel HeavyDutyDieselBusesSchool&Transit RuralMajorCollectorTotal",
    "2230075190":
        "MobileSources HighwayVehiclesDiesel HeavyDutyDieselBusesSchool&Transit RuralMinorCollectorTotal",
    "2230075210":
        "MobileSources HighwayVehiclesDiesel HeavyDutyDieselBusesSchool&Transit RuralLocalTotal",
    "2230075230":
        "MobileSources HighwayVehiclesDiesel HeavyDutyDieselBusesSchool&Transit UrbanInterstateTotal",
    "2230075250":
        "MobileSources HighwayVehiclesDiesel HeavyDutyDieselBusesSchool&Transit UrbanOtherFreewaysandExpresswaysTotal",
    "2230075270":
        "MobileSources HighwayVehiclesDiesel HeavyDutyDieselBusesSchool&Transit UrbanOtherPrincipalArterialTotal",
    "2230075290":
        "MobileSources HighwayVehiclesDiesel HeavyDutyDieselBusesSchool&Transit UrbanMinorArterialTotal",
    "2230075310":
        "MobileSources HighwayVehiclesDiesel HeavyDutyDieselBusesSchool&Transit UrbanCollectorTotal",
    "2230075330":
        "MobileSources HighwayVehiclesDiesel HeavyDutyDieselBusesSchool&Transit UrbanLocalTotal",
    "2230075390":
        "MobileSources HighwayVehiclesDiesel HeavyDutyDieselBusesSchool&Transit ParkingAreaTotal",
    "2260001010":
        "MobileSources OffhighwayVehicleGasoline2Stroke RecreationalEquipment MotorcyclesOffroad",
    "2260001020":
        "MobileSources OffhighwayVehicleGasoline RecreationalEquipment 2StrokeSnowmobiles",
    "2260001022":
        "MobileSources OffhighwayVehicleGasoline RecreationalEquipment 2StrokeOtherRecreationalEquip.",
    "2260001030":
        "MobileSources OffhighwayVehicleGasoline2Stroke RecreationalEquipment AllTerrainVehicles",
    "2260001060":
        "MobileSources OffhighwayVehicleGasoline RecreationalEquipment 2StrokeSpecialtyVehiclesCarts",
    "2260002006":
        "MobileSources OffhighwayVehicleGasoline2Stroke ConstructionandMiningEquipment TampersRammers",
    "2260002009":
        "MobileSources OffhighwayVehicleGasoline2Stroke ConstructionandMiningEquipment PlateCompactors",
    "2260002021":
        "MobileSources OffhighwayVehicleGasoline2Stroke ConstructionandMiningEquipment PavingEquipment",
    "2260002022":
        "MobileSources OffhighwayVehicleGasoline ConstructionEquipment 2StrokeConstructionEquipment",
    "2260002027":
        "MobileSources OffhighwayVehicleGasoline2Stroke ConstructionandMiningEquipment SignalBoardsLightPlants",
    "2260002039":
        "PetroleumandSolventEvaporation OrganicSolventEvaporation MiscellaneousVolatileOrganicCompoundEvaporation IdentifytheProcessandSolventinComments",
    "2260002054":
        "PetroleumandSolventEvaporation OrganicSolventEvaporation MiscellaneousVolatileOrganicCompoundEvaporation IdentifytheProcessandSolventinComments",
    "2260003022":
        "PetroleumandSolventEvaporation OrganicSolventEvaporation MiscellaneousVolatileOrganicCompoundEvaporation IdentifytheProcessandSolventinComments",
    "2260003030":
        "PetroleumandSolventEvaporation OrganicSolventEvaporation MiscellaneousVolatileOrganicCompoundEvaporation IdentifytheProcessandSolventinComments",
    "2260003040":
        "PetroleumandSolventEvaporation OrganicSolventEvaporation MiscellaneousVolatileOrganicCompoundEvaporation IdentifytheProcessandSolventinComments",
    "2260004015":
        "PetroleumandSolventEvaporation OrganicSolventEvaporation MiscellaneousVolatileOrganicCompoundEvaporation IdentifytheProcessandSolventinComments",
    "2260004016":
        "PetroleumandSolventEvaporation OrganicSolventEvaporation MiscellaneousVolatileOrganicCompoundEvaporation IdentifytheProcessandSolventinComments",
    "2260004020":
        "PetroleumandSolventEvaporation OrganicSolventEvaporation MiscellaneousVolatileOrganicCompoundEvaporation IdentifytheProcessandSolventinComments",
    "2260004021":
        "PetroleumandSolventEvaporation OrganicSolventEvaporation MiscellaneousVolatileOrganicCompoundEvaporation IdentifytheProcessandSolventinComments",
    "2260004022":
        "PetroleumandSolventEvaporation OrganicSolventEvaporation MiscellaneousVolatileOrganicCompoundEvaporation IdentifytheProcessandSolventinComments",
    "2260004025":
        "PetroleumandSolventEvaporation OrganicSolventEvaporation MiscellaneousVolatileOrganicCompoundEvaporation IdentifytheProcessandSolventinComments",
    "2260004026":
        "PetroleumandSolventEvaporation OrganicSolventEvaporation MiscellaneousVolatileOrganicCompoundEvaporation IdentifytheProcessandSolventinComments",
    "2260004030":
        "PetroleumandSolventEvaporation OrganicSolventEvaporation MiscellaneousVolatileOrganicCompoundEvaporation IdentifytheProcessandSolventinComments",
    "2260004031":
        "PetroleumandSolventEvaporation OrganicSolventEvaporation MiscellaneousVolatileOrganicCompoundEvaporation IdentifytheProcessandSolventinComments",
    "2260004033":
        "PetroleumandSolventEvaporation OrganicSolventEvaporation MiscellaneousVolatileOrganicCompoundEvaporation IdentifytheProcessandSolventinComments",
    "2260004035":
        "PetroleumandSolventEvaporation OrganicSolventEvaporation MiscellaneousVolatileOrganicCompoundEvaporation IdentifytheProcessandSolventinComments",
    "2260004036":
        "PetroleumandSolventEvaporation OrganicSolventEvaporation MiscellaneousVolatileOrganicCompoundEvaporation IdentifytheProcessandSolventinComments",
    "2260004044":
        "PetroleumandSolventEvaporation OrganicSolventEvaporation MiscellaneousVolatileOrganicCompoundEvaporation IdentifytheProcessandSolventinComments",
    "2260004071":
        "PetroleumandSolventEvaporation OrganicSolventEvaporation MiscellaneousVolatileOrganicCompoundEvaporation IdentifytheProcessandSolventinComments",
    "2260005022":
        "PetroleumandSolventEvaporation OrganicSolventEvaporation MiscellaneousVolatileOrganicCompoundEvaporation IdentifytheProcessandSolventinComments",
    "2260005035":
        "PetroleumandSolventEvaporation OrganicSolventEvaporation MiscellaneousVolatileOrganicCompoundEvaporation IdentifytheProcessandSolventinComments",
    "2260006005":
        "PetroleumandSolventEvaporation OrganicSolventEvaporation MiscellaneousVolatileOrganicCompoundEvaporation IdentifytheProcessandSolventinComments",
    "2260006010":
        "PetroleumandSolventEvaporation OrganicSolventEvaporation MiscellaneousVolatileOrganicCompoundEvaporation IdentifytheProcessandSolventinComments",
    "2260006015":
        "PetroleumandSolventEvaporation OrganicSolventEvaporation MiscellaneousVolatileOrganicCompoundEvaporation IdentifytheProcessandSolventinComments",
    "2260006022":
        "PetroleumandSolventEvaporation OrganicSolventEvaporation MiscellaneousVolatileOrganicCompoundEvaporation IdentifytheProcessandSolventinComments",
    "2260006035":
        "PetroleumandSolventEvaporation OrganicSolventEvaporation MiscellaneousVolatileOrganicCompoundEvaporation IdentifytheProcessandSolventinComments",
    "2260007005":
        "PetroleumandSolventEvaporation OrganicSolventEvaporation MiscellaneousVolatileOrganicCompoundEvaporation IdentifytheProcessandSolventinComments",
    "2260007022":
        "PetroleumandSolventEvaporation OrganicSolventEvaporation MiscellaneousVolatileOrganicCompoundEvaporation IdentifytheProcessandSolventinComments",
    "2265001010":
        "MobileSources OffhighwayVehicleGasoline4Stroke RecreationalEquipment MotorcyclesOffroad",
    "2265001022":
        "MobileSources OffhighwayVehicleGasoline RecreationalEquipment 4StrokeOtherRecreationalEquip.",
    "2265001030":
        "MobileSources OffhighwayVehicleGasoline4Stroke RecreationalEquipment AllTerrainVehicles",
    "2265001050":
        "MobileSources OffhighwayVehicleGasoline RecreationalEquipment 4StrokeGolfCarts",
    "2265001060":
        "MobileSources OffhighwayVehicleGasoline RecreationalEquipment 4StrokeSpecialtyVehiclesCarts",
    "2265002003":
        "MobileSources OffhighwayVehicleGasoline4Stroke ConstructionandMiningEquipment Pavers",
    "2265002006":
        "MobileSources OffhighwayVehicleGasoline4Stroke ConstructionandMiningEquipment TampersRammers",
    "2265002009":
        "MobileSources OffhighwayVehicleGasoline4Stroke ConstructionandMiningEquipment PlateCompactors",
    "2265002015":
        "MobileSources OffhighwayVehicleGasoline4Stroke ConstructionandMiningEquipment Rollers",
    "2265002021":
        "MobileSources OffhighwayVehicleGasoline4Stroke ConstructionandMiningEquipment PavingEquipment",
    "2265002022":
        "MobileSources OffhighwayVehicleGasoline ConstructionEquipment 4StrokeConstructionEquipment",
    "2265002024":
        "MobileSources OffhighwayVehicleGasoline4Stroke ConstructionandMiningEquipment SurfacingEquipment",
    "2265002027":
        "MobileSources OffhighwayVehicleGasoline4Stroke ConstructionandMiningEquipment SignalBoardsLightPlants",
    "2265002030":
        "MobileSources OffhighwayVehicleGasoline4Stroke ConstructionandMiningEquipment Trenchers",
    "2265002033":
        "MobileSources OffhighwayVehicleGasoline4Stroke ConstructionandMiningEquipment BoreDrillRigs",
    "2265002039":
        "MobileSources OffhighwayVehicleGasoline4Stroke ConstructionandMiningEquipment ConcreteIndustrialSaws",
    "2265002042":
        "MobileSources OffhighwayVehicleGasoline4Stroke ConstructionandMiningEquipment CementandMortarMixers",
    "2265002045":
        "MobileSources OffhighwayVehicleGasoline4Stroke ConstructionandMiningEquipment Cranes",
    "2265002054":
        "MobileSources OffhighwayVehicleGasoline4Stroke ConstructionandMiningEquipment CrushingProcessingEquipment",
    "2265002057":
        "MobileSources OffhighwayVehicleGasoline4Stroke ConstructionandMiningEquipment RoughTerrainForklifts",
    "2265002060":
        "MobileSources OffhighwayVehicleGasoline4Stroke ConstructionandMiningEquipment RubberTireLoaders",
    "2265002066":
        "MobileSources OffhighwayVehicleGasoline4Stroke ConstructionandMiningEquipment TractorsLoadersBackhoes",
    "2265002072":
        "MobileSources OffhighwayVehicleGasoline4Stroke ConstructionandMiningEquipment SkidSteerLoaders",
    "2265002078":
        "MobileSources OffhighwayVehicleGasoline4Stroke ConstructionandMiningEquipment DumpersTenders",
    "2265002081":
        "MobileSources OffhighwayVehicleGasoline4Stroke ConstructionandMiningEquipment OtherConstructionEquipment",
    "2265003010":
        "MobileSources OffhighwayVehicleGasoline4Stroke IndustrialEquipment AerialLifts",
    "2265003020":
        "MobileSources OffhighwayVehicleGasoline4Stroke IndustrialEquipment Forklifts",
    "2265003022":
        "MobileSources OffhighwayVehicleGasoline IndustrialEquipment 4StrokeIndustrialEquipment",
    "2265003030":
        "MobileSources OffhighwayVehicleGasoline4Stroke IndustrialEquipment SweepersScrubbers",
    "2265003040":
        "MobileSources OffhighwayVehicleGasoline4Stroke IndustrialEquipment OtherGeneralIndustrialEquipment",
    "2265003050":
        "MobileSources OffhighwayVehicleGasoline4Stroke IndustrialEquipment OtherMaterialHandlingEquipment",
    "2265003060":
        "MobileSources OffhighwayVehicleGasoline IndustrialEquipment 4StrokeAC\Refrigeration",
    "2265003070":
        "MobileSources OffhighwayVehicleGasoline4Stroke IndustrialEquipment TerminalTractors",
    "2265004010":
        "MobileSources OffhighwayVehicleGasoline4Stroke LawnandGardenEquipment LawnMowersResidential",
    "2265004011":
        "MobileSources OffhighwayVehicleGasoline4Stroke LawnandGardenEquipment LawnMowersCommercial",
    "2265004015":
        "MobileSources OffhighwayVehicleGasoline4Stroke LawnandGardenEquipment RotaryTillers6HPResidential",
    "2265004016":
        "MobileSources OffhighwayVehicleGasoline4Stroke LawnandGardenEquipment RotaryTillers6HPCommercial",
    "2265004022":
        "MobileSources OffhighwayVehicleGasoline LawnandGardenEquipment 4StrokeMowersTractorsTurfEqtCommercial",
    "2265004025":
        "MobileSources OffhighwayVehicleGasoline4Stroke LawnandGardenEquipment TrimmersEdgersBrushCuttersResidential",
    "2265004026":
        "MobileSources OffhighwayVehicleGasoline4Stroke LawnandGardenEquipment TrimmersEdgersBrushCuttersCommercial",
    "2265004030":
        "MobileSources OffhighwayVehicleGasoline4Stroke LawnandGardenEquipment LeafblowersVacuumsResidential",
    "2265004031":
        "MobileSources OffhighwayVehicleGasoline4Stroke LawnandGardenEquipment LeafblowersVacuumsCommercial",
    "2265004033":
        "MobileSources OffhighwayVehicleGasoline LawnandGardenEquipment 4StrokeLawn&GardenEqtResidential",
    "2265004035":
        "MobileSources OffhighwayVehicleGasoline LawnandGardenEquipment 4StrokeSnowblowersResidential",
    "2265004036":
        "MobileSources OffhighwayVehicleGasoline LawnandGardenEquipment 4StrokeSnowblowersCommercial",
    "2265004040":
        "MobileSources OffhighwayVehicleGasoline4Stroke LawnandGardenEquipment RearEngineRidingMowersResidential",
    "2265004041":
        "MobileSources OffhighwayVehicleGasoline4Stroke LawnandGardenEquipment RearEngineRidingMowersCommercial",
    "2265004044":
        "MobileSources OffhighwayVehicleGasoline LawnandGardenEquipment 4StrokeLawn&GardenEqtCommercial",
    "2265004046":
        "MobileSources OffhighwayVehicleGasoline4Stroke LawnandGardenEquipment FrontMowersCommercial",
    "2265004050":
        "MobileSources OffhighwayVehicleGasoline4Stroke LawnandGardenEquipment Shredders6HPResidential",
    "2265004051":
        "MobileSources OffhighwayVehicleGasoline4Stroke LawnandGardenEquipment Shredders6HPCommercial",
    "2265004055":
        "MobileSources OffhighwayVehicleGasoline4Stroke LawnandGardenEquipment LawnandGardenTractorsResidential",
    "2265004056":
        "MobileSources OffhighwayVehicleGasoline4Stroke LawnandGardenEquipment LawnandGardenTractorsCommercial",
    "2265004066":
        "MobileSources OffhighwayVehicleGasoline4Stroke LawnandGardenEquipment ChippersStumpGrindersCommercial",
    "2265004071":
        "MobileSources OffhighwayVehicleGasoline4Stroke LawnandGardenEquipment TurfEquipmentCommercial",
    "2265004075":
        "MobileSources OffhighwayVehicleGasoline4Stroke LawnandGardenEquipment OtherLawnandGardenEquipmentResidential",
    "2265004076":
        "MobileSources OffhighwayVehicleGasoline4Stroke LawnandGardenEquipment OtherLawnandGardenEquipmentCommercial",
    "2265005010":
        "MobileSources OffhighwayVehicleGasoline4Stroke AgriculturalEquipment 2WheelTractors",
    "2265005015":
        "MobileSources OffhighwayVehicleGasoline4Stroke AgriculturalEquipment AgriculturalTractors",
    "2265005020":
        "MobileSources OffhighwayVehicleGasoline4Stroke AgriculturalEquipment Combines",
    "2265005022":
        "MobileSources OffhighwayVehicleGasoline AgriculturalEquipment 4StrokeAgricultureEquipment",
    "2265005025":
        "MobileSources OffhighwayVehicleGasoline4Stroke AgriculturalEquipment Balers",
    "2265005030":
        "MobileSources OffhighwayVehicleGasoline4Stroke AgriculturalEquipment AgriculturalMowers",
    "2265005035":
        "MobileSources OffhighwayVehicleGasoline4Stroke AgriculturalEquipment Sprayers",
    "2265005040":
        "MobileSources OffhighwayVehicleGasoline4Stroke AgriculturalEquipment Tillers6HP",
    "2265005045":
        "MobileSources OffhighwayVehicleGasoline4Stroke AgriculturalEquipment Swathers",
    "2265005055":
        "MobileSources OffhighwayVehicleGasoline4Stroke AgriculturalEquipment OtherAgriculturalEquipment",
    "2265005060":
        "MobileSources OffhighwayVehicleGasoline4Stroke AgriculturalEquipment IrrigationSets",
    "2265006005":
        "MobileSources OffhighwayVehicleGasoline4Stroke CommercialEquipment GeneratorSets",
    "2265006010":
        "MobileSources OffhighwayVehicleGasoline4Stroke CommercialEquipment Pumps",
    "2265006015":
        "MobileSources OffhighwayVehicleGasoline4Stroke CommercialEquipment AirCompressors",
    "2265006022":
        "MobileSources OffhighwayVehicleGasoline CommercialEquipment 4StrokeCommercialEquipment",
    "2265006025":
        "MobileSources OffhighwayVehicleGasoline4Stroke CommercialEquipment Welders",
    "2265006030":
        "MobileSources OffhighwayVehicleGasoline4Stroke CommercialEquipment PressureWashers",
    "2265006035":
        "MobileSources OffhighwayVehicleGasoline4Stroke CommercialEquipment HydropowerUnits",
    "2265007010":
        "MobileSources OffhighwayVehicleGasoline4Stroke LoggingEquipment Shredders6HP",
    "2265007015":
        "MobileSources OffhighwayVehicleGasoline4Stroke LoggingEquipment ForestEqpFellerBunchSkidder",
    "2265007022":
        "MobileSources OffhighwayVehicleGasoline LoggingEquipment 4StrokeLoggingEquipment",
    "2265010010":
        "MobileSources OffhighwayVehicleGasoline IndustrialEquipment 4StrokeOtherOilFieldEquipment",
    "2267001060":
        "MobileSources OffhighwayVehicleLPG RecreationalEquipment LPGSpecialtyVehiclesCarts",
    "2267002003":
        "MobileSources LPG ConstructionandMiningEquipment Pavers",
    "2267002015":
        "MobileSources LPG ConstructionandMiningEquipment Rollers",
    "2267002021":
        "MobileSources LPG ConstructionandMiningEquipment PavingEquipment",
    "2267002022":
        "MobileSources OffhighwayVehicleLPG ConstructionEquipment LPGConstructionEquipment",
    "2267002024":
        "MobileSources LPG ConstructionandMiningEquipment SurfacingEquipment",
    "2267002030":
        "MobileSources LPG ConstructionandMiningEquipment Trenchers",
    "2267002033":
        "MobileSources LPG ConstructionandMiningEquipment BoreDrillRigs",
    "2267002039":
        "MobileSources LPG ConstructionandMiningEquipment ConcreteIndustrialSaws",
    "2267002045":
        "MobileSources LPG ConstructionandMiningEquipment Cranes",
    "2267002054":
        "MobileSources LPG ConstructionandMiningEquipment CrushingProcessingEquipment",
    "2267002057":
        "MobileSources LPG ConstructionandMiningEquipment RoughTerrainForklifts",
    "2267002060":
        "MobileSources LPG ConstructionandMiningEquipment RubberTireLoaders",
    "2267002066":
        "MobileSources LPG ConstructionandMiningEquipment TractorsLoadersBackhoes",
    "2267002072":
        "MobileSources LPG ConstructionandMiningEquipment SkidSteerLoaders",
    "2267002081":
        "MobileSources LPG ConstructionandMiningEquipment OtherConstructionEquipment",
    "2267003010":
        "MobileSources LPG IndustrialEquipment AerialLifts",
    "2267003020":
        "MobileSources LPG IndustrialEquipment Forklifts",
    "2267003022":
        "MobileSources OffhighwayVehicleLPG IndustrialEquipment LPGIndustrialEquipment",
    "2267003030":
        "MobileSources LPG IndustrialEquipment SweepersScrubbers",
    "2267003040":
        "MobileSources LPG IndustrialEquipment OtherGeneralIndustrialEquipment",
    "2267003050":
        "MobileSources LPG IndustrialEquipment OtherMaterialHandlingEquipment",
    "2267003070":
        "MobileSources LPG IndustrialEquipment TerminalTractors",
    "2267004044":
        "MobileSources OffhighwayVehicleLPG LawnandGardenEquipment LPGLawn&GardenEqtCommercial",
    "2267004066":
        "MobileSources LPG LawnandGardenEquipment ChippersStumpGrindersCommercial",
    "2267005022":
        "MobileSources OffhighwayVehicleLPG AgriculturalEquipment LPGAgricultureEquipment",
    "2267005055":
        "MobileSources LPG AgriculturalEquipment OtherAgriculturalEquipment",
    "2267005060":
        "MobileSources LPG AgriculturalEquipment IrrigationSets",
    "2267006005":
        "MobileSources LPG CommercialEquipment GeneratorSets",
    "2267006010":
        "MobileSources LPG CommercialEquipment Pumps",
    "2267006015":
        "MobileSources LPG CommercialEquipment AirCompressors",
    "2267006022":
        "MobileSources OffhighwayVehicleLPG CommercialEquipment LPGCommercialEquipment",
    "2267006025":
        "MobileSources LPG CommercialEquipment Welders",
    "2267006030":
        "MobileSources LPG CommercialEquipment PressureWashers",
    "2267006035":
        "MobileSources LPG CommercialEquipment HydropowerUnits",
    "2268002022":
        "MobileSources OffhighwayVehicleCNG ConstructionEquipment CNGConstructionEquipment",
    "2268002081":
        "MobileSources CNG ConstructionandMiningEquipment OtherConstructionEquipment",
    "2268003020":
        "MobileSources CNG IndustrialEquipment Forklifts",
    "2268003022":
        "MobileSources OffhighwayVehicleCNG IndustrialEquipment CNGIndustrialEquipment",
    "2268003030":
        "MobileSources CNG IndustrialEquipment SweepersScrubbers",
    "2268003040":
        "MobileSources CNG IndustrialEquipment OtherGeneralIndustrialEquipment",
    "2268003060":
        "MobileSources OffhighwayVehicleCNG IndustrialEquipment CNGAC\Refrigeration",
    "2268003070":
        "MobileSources CNG IndustrialEquipment TerminalTractors",
    "2268005022":
        "MobileSources OffhighwayVehicleCNG AgriculturalEquipment CNGAgricultureEquipment",
    "2268005055":
        "MobileSources CNG AgriculturalEquipment OtherAgriculturalEquipment",
    "2268005060":
        "MobileSources CNG AgriculturalEquipment IrrigationSets",
    "2268006005":
        "MobileSources CNG CommercialEquipment GeneratorSets",
    "2268006010":
        "MobileSources CNG CommercialEquipment Pumps",
    "2268006015":
        "MobileSources CNG CommercialEquipment AirCompressors",
    "2268006020":
        "MobileSources CNG CommercialEquipment GasCompressors",
    "2268006022":
        "MobileSources OffhighwayVehicleCNG CommercialEquipment CNGCommercialEquipment",
    "2268006035":
        "MobileSources CNG CommercialEquipment HydropowerUnits",
    "2268010010":
        "MobileSources OffhighwayVehicleCNG IndustrialEquipment CNGOtherOilFieldEquipment",
    "2270001060":
        "MobileSources OffhighwayVehicleDiesel RecreationalEquipment SpecialtyVehiclesCarts",
    "2270002003":
        "MobileSources OffhighwayVehicleDiesel ConstructionandMiningEquipment Pavers",
    "2270002006":
        "MobileSources OffhighwayVehicleDiesel ConstructionandMiningEquipment TampersRammers",
    "2270002009":
        "MobileSources OffhighwayVehicleDiesel ConstructionandMiningEquipment PlateCompactors",
    "2270002015":
        "MobileSources OffhighwayVehicleDiesel ConstructionandMiningEquipment Rollers",
    "2270002018":
        "MobileSources OffhighwayVehicleDiesel ConstructionandMiningEquipment Scrapers",
    "2270002021":
        "MobileSources OffhighwayVehicleDiesel ConstructionandMiningEquipment PavingEquipment",
    "2270002022":
        "MobileSources OffhighwayVehicleDiesel ConstructionEquipment DieselConstructionEquipment",
    "2270002024":
        "MobileSources OffhighwayVehicleDiesel ConstructionandMiningEquipment SurfacingEquipment",
    "2270002027":
        "MobileSources OffhighwayVehicleDiesel ConstructionandMiningEquipment SignalBoardsLightPlants",
    "2270002030":
        "MobileSources OffhighwayVehicleDiesel ConstructionandMiningEquipment Trenchers",
    "2270002033":
        "MobileSources OffhighwayVehicleDiesel ConstructionandMiningEquipment BoreDrillRigs",
    "2270002036":
        "MobileSources OffhighwayVehicleDiesel ConstructionandMiningEquipment Excavators",
    "2270002039":
        "MobileSources OffhighwayVehicleDiesel ConstructionandMiningEquipment ConcreteIndustrialSaws",
    "2270002042":
        "MobileSources OffhighwayVehicleDiesel ConstructionandMiningEquipment CementandMortarMixers",
    "2270002045":
        "MobileSources OffhighwayVehicleDiesel ConstructionandMiningEquipment Cranes",
    "2270002048":
        "MobileSources OffhighwayVehicleDiesel ConstructionandMiningEquipment Graders",
    "2270002051":
        "MobileSources OffhighwayVehicleDiesel ConstructionandMiningEquipment OffhighwayTrucks",
    "2270002054":
        "MobileSources OffhighwayVehicleDiesel ConstructionandMiningEquipment CrushingProcessingEquipment",
    "2270002057":
        "MobileSources OffhighwayVehicleDiesel ConstructionandMiningEquipment RoughTerrainForklifts",
    "2270002060":
        "MobileSources OffhighwayVehicleDiesel ConstructionandMiningEquipment RubberTireLoaders",
    "2270002066":
        "MobileSources OffhighwayVehicleDiesel ConstructionandMiningEquipment TractorsLoadersBackhoes",
    "2270002069":
        "MobileSources OffhighwayVehicleDiesel ConstructionandMiningEquipment CrawlerTractorDozers",
    "2270002072":
        "MobileSources OffhighwayVehicleDiesel ConstructionandMiningEquipment SkidSteerLoaders",
    "2270002075":
        "MobileSources OffhighwayVehicleDiesel ConstructionandMiningEquipment OffhighwayTractors",
    "2270002078":
        "MobileSources OffhighwayVehicleDiesel ConstructionandMiningEquipment DumpersTenders",
    "2270002081":
        "MobileSources OffhighwayVehicleDiesel ConstructionandMiningEquipment OtherConstructionEquipment",
    "2270003010":
        "MobileSources OffhighwayVehicleDiesel IndustrialEquipment AerialLifts",
    "2270003020":
        "MobileSources OffhighwayVehicleDiesel IndustrialEquipment Forklifts",
    "2270003022":
        "MobileSources OffhighwayVehicleDiesel IndustrialEquipment DieselIndustrialEquipment",
    "2270003030":
        "MobileSources OffhighwayVehicleDiesel IndustrialEquipment SweepersScrubbers",
    "2270003040":
        "MobileSources OffhighwayVehicleDiesel IndustrialEquipment OtherGeneralIndustrialEquipment",
    "2270003050":
        "MobileSources OffhighwayVehicleDiesel IndustrialEquipment OtherMaterialHandlingEquipment",
    "2270003060":
        "MobileSources OffhighwayVehicleDiesel IndustrialEquipment AC\Refrigeration",
    "2270003070":
        "MobileSources OffhighwayVehicleDiesel IndustrialEquipment TerminalTractors",
    "2270004022":
        "MobileSources OffhighwayVehicleDiesel LawnandGardenEquipment DieselMowersTractorsTurfEqtCommercial",
    "2270004031":
        "MobileSources OffhighwayVehicleDiesel LawnandGardenEquipment LeafblowersVacuumsCommercial",
    "2270004036":
        "MobileSources OffhighwayVehicleDiesel LawnandGardenEquipment SnowblowersCommercial",
    "2270004044":
        "MobileSources OffhighwayVehicleDiesel LawnandGardenEquipment DieselLawn&GardenEqtCommercial",
    "2270004046":
        "MobileSources OffhighwayVehicleDiesel LawnandGardenEquipment FrontMowersCommercial",
    "2270004056":
        "MobileSources OffhighwayVehicleDiesel LawnandGardenEquipment LawnandGardenTractorsCommercial",
    "2270004066":
        "MobileSources OffhighwayVehicleDiesel LawnandGardenEquipment ChippersStumpGrindersCommercial",
    "2270004071":
        "MobileSources OffhighwayVehicleDiesel LawnandGardenEquipment TurfEquipmentCommercial",
    "2270004076":
        "MobileSources OffhighwayVehicleDiesel LawnandGardenEquipment OtherLawnandGardenEquipmentCommercial",
    "2270005010":
        "MobileSources OffhighwayVehicleDiesel AgriculturalEquipment 2WheelTractors",
    "2270005015":
        "MobileSources OffhighwayVehicleDiesel AgriculturalEquipment AgriculturalTractors",
    "2270005020":
        "MobileSources OffhighwayVehicleDiesel AgriculturalEquipment Combines",
    "2270005022":
        "MobileSources OffhighwayVehicleDiesel AgriculturalEquipment DieselAgricultureEquipment",
    "2270005025":
        "MobileSources OffhighwayVehicleDiesel AgriculturalEquipment Balers",
    "2270005030":
        "MobileSources OffhighwayVehicleDiesel AgriculturalEquipment AgriculturalMowers",
    "2270005035":
        "MobileSources OffhighwayVehicleDiesel AgriculturalEquipment Sprayers",
    "2270005040":
        "MobileSources OffhighwayVehicleDiesel AgriculturalEquipment Tillers6HP",
    "2270005045":
        "MobileSources OffhighwayVehicleDiesel AgriculturalEquipment Swathers",
    "2270005055":
        "MobileSources OffhighwayVehicleDiesel AgriculturalEquipment OtherAgriculturalEquipment",
    "2270005060":
        "MobileSources OffhighwayVehicleDiesel AgriculturalEquipment IrrigationSets",
    "2270006005":
        "MobileSources OffhighwayVehicleDiesel CommercialEquipment GeneratorSets",
    "2270006010":
        "MobileSources OffhighwayVehicleDiesel CommercialEquipment Pumps",
    "2270006015":
        "MobileSources OffhighwayVehicleDiesel CommercialEquipment AirCompressors",
    "2270006020":
        "MobileSources OffhighwayVehicleDiesel CommercialEquipment GasCompressors",
    "2270006022":
        "MobileSources OffhighwayVehicleDiesel CommercialEquipment DieselCommercialEquipment",
    "2270006025":
        "MobileSources OffhighwayVehicleDiesel CommercialEquipment Welders",
    "2270006030":
        "MobileSources OffhighwayVehicleDiesel CommercialEquipment PressureWashers",
    "2270006035":
        "MobileSources OffhighwayVehicleDiesel CommercialEquipment HydropowerUnits",
    "2270007010":
        "MobileSources OffhighwayVehicleDiesel LoggingEquipment Shredders6HP",
    "2270007015":
        "MobileSources OffhighwayVehicleDiesel LoggingEquipment ForestEqpFellerBunchSkidder",
    "2270007022":
        "MobileSources OffhighwayVehicleDiesel LoggingEquipment DieselLoggingEquipment",
    "2270009010":
        "MobileSources OffhighwayVehicleDiesel UndergroundMiningEquipment OtherUndergroundMiningEquipment",
    "2270010010":
        "MobileSources OffhighwayVehicleDiesel IndustrialEquipment OtherOilFieldEquipment",
    "2282005010":
        "MobileSources PleasureCraft Gasoline2Stroke Outboard",
    "2282005015":
        "MobileSources PleasureCraft Gasoline2Stroke PersonalWaterCraft",
    "2282005022":
        "MobileSources PleasureCraft Gasoline 2StrokePleasureCraft",
    "2282010005":
        "MobileSources PleasureCraft Gasoline4Stroke InboardSterndrive",
    "2282020005":
        "WasteDisposal SolidWasteDisposalInstitutional WastewaterTreatment OtherNotElsewhereClassified",
    "2282020010":
        "WasteDisposal SolidWasteDisposalInstitutional WastewaterTreatment OtherNotElsewhereClassified",
    "2282020022":
        "WasteDisposal SolidWasteDisposalInstitutional WastewaterTreatment OtherNotElsewhereClassified",
    "2285002015":
        "WasteDisposal SolidWasteDisposalInstitutional WastewaterTreatment OtherNotElsewhereClassified",
    "2285004015":
        "WasteDisposal SolidWasteDisposalInstitutional WastewaterTreatment OtherNotElsewhereClassified",
    "2285006015":
        "WasteDisposal SolidWasteDisposalInstitutional WastewaterTreatment OtherNotElsewhereClassified",
    "10100101":
        "ExternalCombustion ElectricGenerationBoilers AnthraciteCoal AnthraciteCoalPulverizedBoiler",
    "10100102":
        "ExternalCombustion ElectricGenerationBoilers AnthraciteCoal BoilerTravelingGrateOverfeedStoker",
    "10100201":
        "ExternalCombustion ElectricGenerationBoilers BituminousSubbituminousCoal BituminousCoalPulverizedBoilerWetBottom",
    "10100202":
        "ExternalCombustion ElectricGenerationBoilers BituminousSubbituminousCoal BituminousCoalPulverizedBoilerDryBottom",
    "10100203":
        "ExternalCombustion ElectricGenerationBoilers BituminousSubbituminousCoal BituminousCoalBoilerCycloneFurnace",
    "10100204":
        "ExternalCombustion ElectricGenerationBoilers BituminousSubbituminousCoal BituminousCoalBoilerSpreaderStoker",
    "10100205":
        "ExternalCombustion ElectricGenerationBoilers BituminousSubbituminousCoal BituminousCoalBoilerTravelingGrateOverfeedStoker",
    "10100211":
        "ExternalCombustion ElectricGenerationBoilers BituminousSubbituminousCoal BituminousCoalBoilerWetBottomTangentialfired",
    "10100212":
        "ExternalCombustion ElectricGenerationBoilers BituminousSubbituminousCoal BituminousCoalPulverizedBoilerDryBottomTangentialfired",
    "10100215":
        "ExternalCombustion ElectricGenerationBoilers BituminousSubbituminousCoal BituminousCoalCellBurner",
    "10100217":
        "ExternalCombustion ElectricGenerationBoilers BituminousSubbituminousCoal BituminousCoalBoilerAtmosphericFluidizedBedCombustionBubblingBed",
    "10100218":
        "ExternalCombustion ElectricGenerationBoilers BituminousSubbituminousCoal BituminousCoalBoilerAtmosphericFluidizedBedCombustionCirculatingBed",
    "10100221":
        "ExternalCombustion ElectricGenerationBoilers BituminousSubbituminousCoal SubbituminousCoalPulverizedBoilerWetBottom",
    "10100222":
        "ExternalCombustion ElectricGenerationBoilers BituminousSubbituminousCoal SubbituminousCoalPulverizedBoilerDryBottom",
    "10100223":
        "ExternalCombustion ElectricGenerationBoilers BituminousSubbituminousCoal SubbituminousCoalCycloneFurnace",
    "10100224":
        "ExternalCombustion ElectricGenerationBoilers BituminousSubbituminousCoal SubbituminousCoalBoilerSpreaderStoker",
    "10100225":
        "ExternalCombustion ElectricGenerationBoilers BituminousSubbituminousCoal SubbituminousCoalBoilerTravelingGrateOverfeedStoker",
    "10100226":
        "ExternalCombustion ElectricGenerationBoilers BituminousSubbituminousCoal SubbituminousCoalPulverizedBoilerDryBottomTangentialfired",
    "10100237":
        "ExternalCombustion ElectricGenerationBoilers BituminousSubbituminousCoal SubbituminousCoalBoilerAtmosphericFluidizedBedCombustionBubblingBed",
    "10100238":
        "ExternalCombustion ElectricGenerationBoilers BituminousSubbituminousCoal SubbituminousCoalBoilerAtmosphericFluidizedBedCombustionCirculatingBed",
    "10100301":
        "ExternalCombustion ElectricGenerationBoilers Lignite PulverizedLigniteBoilerDryBottomWallfired",
    "10100302":
        "ExternalCombustion ElectricGenerationBoilers Lignite PulverizedLigniteBoilerDryBottomTangentialfired",
    "10100303":
        "ExternalCombustion ElectricGenerationBoilers Lignite CycloneFurnace",
    "10100306":
        "ExternalCombustion ElectricGenerationBoilers Lignite BoilerSpreaderStoker",
    "10100317":
        "ExternalCombustion ElectricGenerationBoilers Lignite BoilerAtmosphericFluidizedBedCombustionBubblingBed",
    "10100318":
        "ExternalCombustion ElectricGenerationBoilers Lignite BoilerAtmosphericFluidizedBedCombustionCirculatingBed",
    "10100401":
        "ExternalCombustion ElectricGenerationBoilers ResidualOil ResidualOilGrade6BoilerNormalFiring",
    "10100404":
        "ExternalCombustion ElectricGenerationBoilers ResidualOil ResidualOilGrade6BoilerTangentialfired",
    "10100405":
        "ExternalCombustion ElectricGenerationBoilers ResidualOil Grade5OilNormalFiring",
    "10100406":
        "ExternalCombustion ElectricGenerationBoilers ResidualOil Grade5OilTangentialFiring",
    "10100501":
        "ExternalCombustion ElectricGenerationBoilers DistillateOil DistillateOilGrades1and2Boiler",
    "10100504":
        "ExternalCombustion ElectricGenerationBoilers DistillateOil DistillateOilGrade4BoilerNormalFiring",
    "10100505":
        "ExternalCombustion ElectricGenerationBoilers DistillateOil DistillateOilGrade4BoilerTangentialfired",
    "10100601":
        "ExternalCombustion ElectricGenerationBoilers NaturalGas Boiler100MillionBTUhr",
    "10100602":
        "ExternalCombustion ElectricGenerationBoilers NaturalGas Boiler100MillionBTUexcepttangential",
    "10100604":
        "ExternalCombustion ElectricGenerationBoilers NaturalGas BoilerTangentialfired",
    "10100701":
        "ExternalCombustion ElectricGenerationBoilers ProcessGas Boiler100MillionBTUhr",
    "10100702":
        "ExternalCombustion ElectricGenerationBoilers ProcessGas Boiler100MillionBtuhr",
    "10100703":
        "ExternalCombustion ElectricGenerationBoilers ProcessGas PetroleumRefineryGasBoiler",
    "10100704":
        "ExternalCombustion ElectricGenerationBoilers ProcessGas BlastFurnaceGas",
    "10100711":
        "ExternalCombustion ElectricGenerationBoilers ProcessGas LandfillGas",
    "10100712":
        "ExternalCombustion ElectricGenerationBoilers ProcessGas DigesterGas",
    "10100801":
        "ExternalCombustion ElectricGenerationBoilers PetroleumCoke AllBoilerSizes",
    "10100901":
        "ExternalCombustion ElectricGenerationBoilers WoodBarkWaste BarkfiredBoiler",
    "10100902":
        "ExternalCombustion ElectricGenerationBoilers WoodBarkWaste WoodBarkFiredBoiler",
    "10100903":
        "ExternalCombustion ElectricGenerationBoilers WoodBarkWaste WoodfiredBoilerWetWood20%moisture",
    "10100908":
        "ExternalCombustion ElectricGenerationBoilers WoodBarkWaste WoodfiredBoilerDryWood20%moisture",
    "10100910":
        "ExternalCombustion ElectricGenerationBoilers WoodBarkWaste FuelcellDutchovenboilers",
    "10100911":
        "ExternalCombustion ElectricGenerationBoilers WoodBarkWaste Stokerboilers",
    "10100912":
        "ExternalCombustion ElectricGenerationBoilers WoodBarkWaste Fluidizedbedcombustionboiler",
    "10101001":
        "ExternalCombustion ElectricGenerationBoilers LiquifiedPetroleumGasLPG Butane",
    "10101002":
        "ExternalCombustion ElectricGenerationBoilers LiquifiedPetroleumGasLPG Propane",
    "10101003":
        "ExternalCombustion ElectricGenerationBoilers LiquifiedPetroleumGasLPG ButanePropaneMixtureSpecifyPercentButaneinComments",
    "10101101":
        "ExternalCombustion ElectricGenerationBoilers Bagasse AllBoilerSizes",
    "10101201":
        "ExternalCombustion ElectricGenerationBoilers SolidWaste SpecifyWasteMaterialinComments",
    "10101202":
        "ExternalCombustion ElectricGenerationBoilers SolidWaste RefuseDerivedFuel",
    "10101204":
        "ExternalCombustion ElectricGenerationBoilers SolidWaste TireDerivedFuelShredded",
    "10101205":
        "ExternalCombustion ElectricGenerationBoilers SolidWaste SludgeWaste",
    "10101206":
        "ExternalCombustion ElectricGenerationBoilers SolidWaste AgriculturalByproductsriceorpeanuthullsshellscowmanureetc",
    "10101207":
        "ExternalCombustion ElectricGenerationBoilers SolidWaste BiomassSolidsBiomassSolidsBoilertypeunknownuse10101209or10",
    "10101208":
        "ExternalCombustion ElectricGenerationBoilers SolidWaste PaperPellets",
    "10101209":
        "ExternalCombustion ElectricGenerationBoilers SolidWaste BiomassSolidsBoilerStoker",
    "10101210":
        "ExternalCombustion ElectricGenerationBoilers SolidWaste BiomassSolidsBoilerNonstoker",
    "10101301":
        "ExternalCombustion ElectricGenerationBoilers LiquidWaste SpecifyWasteMaterialinComments",
    "10101302":
        "ExternalCombustion ElectricGenerationBoilers LiquidWaste WasteOil",
    "10101304":
        "ExternalCombustion ElectricGenerationBoilers LiquidWaste BlackLiquor",
    "10101501":
        "ExternalCombustion ElectricGenerationBoilers GeothermalPowerPlants GeothermalPowerPlantOffgasEjectors",
    "10101502":
        "ExternalCombustion ElectricGenerationBoilers GeothermalPowerPlants GeothermalPowerPlantCoolingTowerExhaust",
    "10101601":
        "ExternalCombustion ElectricGenerationBoilers Methanol All",
    "10102101":
        "ExternalCombustion ElectricGenerationBoilers OtherOil All",
    "10200101":
        "ExternalCombustion IndustrialBoilers AnthraciteCoal PulverizedCoal",
    "10200104":
        "ExternalCombustion IndustrialBoilers AnthraciteCoal TirederivedFuel",
    "10200117":
        "ExternalCombustion IndustrialBoilers AnthraciteCoal FluidizedBedBoilerBurningAnthraciteCulmFuel",
    "10200201":
        "ExternalCombustion IndustrialBoilers BituminousSubbituminousCoal BituminousCoalPulverizedCoalWetBottom",
    "10200202":
        "ExternalCombustion IndustrialBoilers BituminousSubbituminousCoal BituminousCoalPulverizedCoalDryBottom",
    "10200203":
        "ExternalCombustion IndustrialBoilers BituminousSubbituminousCoal BituminousCoalCycloneFurnace",
    "10200204":
        "ExternalCombustion IndustrialBoilers BituminousSubbituminousCoal BituminousCoalSpreaderStoker",
    "10200205":
        "ExternalCombustion IndustrialBoilers BituminousSubbituminousCoal BituminousCoalOverfeedStoker",
    "10200206":
        "ExternalCombustion IndustrialBoilers BituminousSubbituminousCoal BituminousCoalUnderfeedStoker",
    "10200212":
        "ExternalCombustion IndustrialBoilers BituminousSubbituminousCoal BituminousCoalPulverizedCoalDryBottomTangential",
    "10200213":
        "ExternalCombustion IndustrialBoilers BituminousSubbituminousCoal BituminousCoalWetSlurry",
    "10200217":
        "ExternalCombustion IndustrialBoilers BituminousSubbituminousCoal BituminousCoalAtmosphericFluidizedBedCombustionBubblingBed",
    "10200218":
        "ExternalCombustion IndustrialBoilers BituminousSubbituminousCoal BituminousCoalAtmosphericFluidizedBedCombustionCirculatingBed",
    "10200219":
        "ExternalCombustion IndustrialBoilers BituminousSubbituminousCoal BituminousCoalCogeneration",
    "10200221":
        "ExternalCombustion IndustrialBoilers BituminousSubbituminousCoal SubbituminousCoalPulverizedCoalWetBottom",
    "10200222":
        "ExternalCombustion IndustrialBoilers BituminousSubbituminousCoal SubbituminousCoalPulverizedCoalDryBottom",
    "10200223":
        "ExternalCombustion IndustrialBoilers BituminousSubbituminousCoal SubbituminousCoalCycloneFurnace",
    "10200224":
        "ExternalCombustion IndustrialBoilers BituminousSubbituminousCoal SubbituminousCoalSpreaderStoker",
    "10200225":
        "ExternalCombustion IndustrialBoilers BituminousSubbituminousCoal SubbituminousCoalTravelingGrateOverfeedStoker",
    "10200226":
        "ExternalCombustion IndustrialBoilers BituminousSubbituminousCoal SubbituminousCoalPulverizedCoalDryBottomTangential",
    "10200229":
        "ExternalCombustion IndustrialBoilers BituminousSubbituminousCoal SubbituminousCoalCogeneration",
    "10200301":
        "ExternalCombustion IndustrialBoilers Lignite PulverizedCoalDryBottomWallFired",
    "10200303":
        "ExternalCombustion IndustrialBoilers Lignite CycloneFurnace",
    "10200306":
        "ExternalCombustion IndustrialBoilers Lignite SpreaderStoker",
    "10200307":
        "ExternalCombustion IndustrialBoilers Lignite Cogeneration",
    "10200401":
        "ExternalCombustion IndustrialBoilers ResidualOil Grade6oil",
    "10200402":
        "ExternalCombustion IndustrialBoilers ResidualOil 10100MillionBTUhr",
    "10200403":
        "ExternalCombustion IndustrialBoilers ResidualOil 10MillionBTUhr",
    "10200404":
        "ExternalCombustion IndustrialBoilers ResidualOil Grade5Oil",
    "10200405":
        "ExternalCombustion IndustrialBoilers ResidualOil Cogeneration",
    "10200406":
        "ExternalCombustion IndustrialBoilers ResidualOil Boiler100MillionBTUhr",
    "10200501":
        "ExternalCombustion IndustrialBoilers DistillateOil DistillateOilGrades1and2Boiler",
    "10200502":
        "ExternalCombustion IndustrialBoilers DistillateOil 10100MillionBTUhr",
    "10200503":
        "ExternalCombustion IndustrialBoilers DistillateOil 10MillionBTUhr",
    "10200504":
        "ExternalCombustion IndustrialBoilers DistillateOil Grade4Oil",
    "10200505":
        "ExternalCombustion IndustrialBoilers DistillateOil Cogeneration",
    "10200506":
        "ExternalCombustion IndustrialBoilers DistillateOil Boiler100MillionBTUhr",
    "10200601":
        "ExternalCombustion IndustrialBoilers NaturalGas 100MillionBTUhr",
    "10200602":
        "ExternalCombustion IndustrialBoilers NaturalGas 10100MillionBTUhr",
    "10200603":
        "ExternalCombustion IndustrialBoilers NaturalGas 10MillionBTUhr",
    "10200604":
        "ExternalCombustion IndustrialBoilers NaturalGas Cogeneration",
    "10200701":
        "ExternalCombustion IndustrialBoilers ProcessGas PetroleumRefineryGas",
    "10200704":
        "ExternalCombustion IndustrialBoilers ProcessGas BlastFurnaceGas",
    "10200707":
        "ExternalCombustion IndustrialBoilers ProcessGas CokeOvenGas",
    "10200710":
        "ExternalCombustion IndustrialBoilers ProcessGas Cogeneration",
    "10200711":
        "ExternalCombustion IndustrialBoilers ProcessGas LandfillGas",
    "10200799":
        "ExternalCombustion IndustrialBoilers ProcessGas OtherSpecifyinComments",
    "10200802":
        "ExternalCombustion IndustrialBoilers PetroleumCoke AllBoilerSizes",
    "10200804":
        "ExternalCombustion IndustrialBoilers PetroleumCoke Cogeneration",
    "10200901":
        "ExternalCombustion IndustrialBoilers WoodBarkWaste BarkfiredBoiler",
    "10200902":
        "ExternalCombustion IndustrialBoilers WoodBarkWaste WoodBarkfiredBoiler",
    "10200903":
        "ExternalCombustion IndustrialBoilers WoodBarkWaste WoodfiredBoilerWetWood20%moisture",
    "10200904":
        "ExternalCombustion IndustrialBoilers WoodBarkWaste BarkfiredBoiler50000LbSteam",
    "10200905":
        "ExternalCombustion IndustrialBoilers WoodBarkWaste WoodBarkfiredBoiler50000LbSteam",
    "10200906":
        "ExternalCombustion IndustrialBoilers WoodBarkWaste WoodfiredBoiler50000LbSteam",
    "10200907":
        "ExternalCombustion IndustrialBoilers WoodBarkWaste WoodCogeneration",
    "10200908":
        "ExternalCombustion IndustrialBoilers WoodBarkWaste WoodfiredBoilerDryWood20%moisture",
    "10200910":
        "ExternalCombustion IndustrialBoilers WoodBarkWaste FuelcellDutchovenboilers",
    "10200911":
        "ExternalCombustion IndustrialBoilers WoodBarkWaste Stokerboilers",
    "10200912":
        "ExternalCombustion IndustrialBoilers WoodBarkWaste Fluidizedbedcombustionboiler",
    "10201001":
        "ExternalCombustion IndustrialBoilers LiquifiedPetroleumGasLPG Butane",
    "10201002":
        "ExternalCombustion IndustrialBoilers LiquifiedPetroleumGasLPG Propane",
    "10201003":
        "ExternalCombustion IndustrialBoilers LiquifiedPetroleumGasLPG ButanePropaneMixtureSpecifyPercentButaneinComments",
    "10201101":
        "ExternalCombustion IndustrialBoilers Bagasse AllBoilerSizes",
    "10201201":
        "ExternalCombustion IndustrialBoilers SolidWaste SpecifyWasteMaterialinComments",
    "10201202":
        "ExternalCombustion IndustrialBoilers SolidWaste RefuseDerivedFuel",
    "10201301":
        "ExternalCombustion IndustrialBoilers LiquidWaste SpecifyWasteMaterialinComments",
    "10201302":
        "ExternalCombustion IndustrialBoilers LiquidWaste WasteOil",
    "10201303":
        "ExternalCombustion IndustrialBoilers LiquidWaste SalableAnimalFat",
    "10201401":
        "ExternalCombustion IndustrialBoilers COBoiler NaturalGas",
    "10201402":
        "ExternalCombustion IndustrialBoilers COBoiler ProcessGas",
    "10201403":
        "ExternalCombustion IndustrialBoilers COBoiler DistillateOil",
    "10201404":
        "ExternalCombustion IndustrialBoilers COBoiler ResidualOil",
    "10201501":
        "ExternalCombustion IndustrialBoilers TirederivedFuel BoilerStoker",
    "10201502":
        "ExternalCombustion IndustrialBoilers TirederivedFuel BoilerNonstoker",
    "10201601":
        "ExternalCombustion IndustrialBoilers Methanol IndustrialBoiler",
    "10201701":
        "ExternalCombustion IndustrialBoilers Gasoline IndustrialBoiler",
    "10201901":
        "ExternalCombustion IndustrialBoilers WoodResiduals BoilerStoker",
    "10201902":
        "ExternalCombustion IndustrialBoilers WoodResiduals Boilernonstoker",
    "10300101":
        "ExternalCombustion CommercialInstitutionalBoilers AnthraciteCoal PulverizedCoal",
    "10300102":
        "ExternalCombustion CommercialInstitutionalBoilers AnthraciteCoal TravelingGrateOverfeedStoker",
    "10300103":
        "ExternalCombustion CommercialInstitutionalBoilers AnthraciteCoal Handfired",
    "10300203":
        "ExternalCombustion CommercialInstitutionalBoilers BituminousSubbituminousCoal BituminousCoalCycloneFurnace",
    "10300205":
        "ExternalCombustion CommercialInstitutionalBoilers BituminousSubbituminousCoal BituminousCoalPulverizedCoalWetBottom",
    "10300206":
        "ExternalCombustion CommercialInstitutionalBoilers BituminousSubbituminousCoal BituminousCoalPulverizedCoalDryBottom",
    "10300207":
        "ExternalCombustion CommercialInstitutionalBoilers BituminousSubbituminousCoal BituminousCoalOverfeedStoker",
    "10300208":
        "ExternalCombustion CommercialInstitutionalBoilers BituminousSubbituminousCoal BituminousCoalUnderfeedStoker",
    "10300209":
        "ExternalCombustion CommercialInstitutionalBoilers BituminousSubbituminousCoal BituminousCoalSpreaderStoker",
    "10300214":
        "ExternalCombustion CommercialInstitutionalBoilers BituminousSubbituminousCoal BituminousCoalHandfired",
    "10300216":
        "ExternalCombustion CommercialInstitutionalBoilers BituminousSubbituminousCoal BituminousCoalPulverizedCoalDryBottomTangential",
    "10300217":
        "ExternalCombustion CommercialInstitutionalBoilers BituminousSubbituminousCoal BituminousCoalAtmosphericFluidizedBedCombustionBubblingBed",
    "10300218":
        "ExternalCombustion CommercialInstitutionalBoilers BituminousSubbituminousCoal BituminousCoalAtmosphericFluidizedBedCombustionCirculatingBed",
    "10300222":
        "ExternalCombustion CommercialInstitutionalBoilers BituminousSubbituminousCoal SubbituminousCoalPulverizedCoalDryBottom",
    "10300224":
        "ExternalCombustion CommercialInstitutionalBoilers BituminousSubbituminousCoal SubbituminousCoalSpreaderStoker",
    "10300225":
        "ExternalCombustion CommercialInstitutionalBoilers BituminousSubbituminousCoal SubbituminousCoalTravelingGrateOverfeedStoker",
    "10300226":
        "ExternalCombustion CommercialInstitutionalBoilers BituminousSubbituminousCoal SubbituminousCoalPulverizedCoalDryBottomTangential",
    "10300306":
        "ExternalCombustion CommercialInstitutionalBoilers Lignite PulverizedCoalDryBottomTangentialFired",
    "10300401":
        "ExternalCombustion CommercialInstitutionalBoilers ResidualOil ResidualOilGrade6Boiler",
    "10300402":
        "ExternalCombustion CommercialInstitutionalBoilers ResidualOil 10100MillionBTUhr",
    "10300403":
        "ExternalCombustion CommercialInstitutionalBoilers ResidualOil 10MillionBTUhr",
    "10300404":
        "ExternalCombustion CommercialInstitutionalBoilers ResidualOil Grade5Oil",
    "10300405":
        "ExternalCombustion CommercialInstitutionalBoilers ResidualOil Boiler100MillionBTUhr",
    "10300501":
        "ExternalCombustion CommercialInstitutionalBoilers DistillateOil DistillateOilGrades1and2Boiler",
    "10300502":
        "ExternalCombustion CommercialInstitutionalBoilers DistillateOil 10100MillionBTUhr",
    "10300503":
        "ExternalCombustion CommercialInstitutionalBoilers DistillateOil 10MillionBTUhr",
    "10300504":
        "ExternalCombustion CommercialInstitutionalBoilers DistillateOil Grade4Oil",
    "10300505":
        "ExternalCombustion CommercialInstitutionalBoilers DistillateOil Boiler100MillionBTUhr",
    "10300601":
        "ExternalCombustion CommercialInstitutionalBoilers NaturalGas 100MillionBTUhr",
    "10300602":
        "ExternalCombustion CommercialInstitutionalBoilers NaturalGas 10100MillionBTUhr",
    "10300603":
        "ExternalCombustion CommercialInstitutionalBoilers NaturalGas 10MillionBTUhr",
    "10300701":
        "ExternalCombustion CommercialInstitutionalBoilers ProcessGas POTWDigesterGasfiredBoiler",
    "10300799":
        "ExternalCombustion CommercialInstitutionalBoilers ProcessGas OtherNotClassified",
    "10300811":
        "ExternalCombustion CommercialInstitutionalBoilers LandfillGas LandfillGas",
    "10300901":
        "ExternalCombustion CommercialInstitutionalBoilers WoodBarkWaste BarkfiredBoiler",
    "10300902":
        "ExternalCombustion CommercialInstitutionalBoilers WoodBarkWaste WoodBarkfiredBoiler",
    "10300903":
        "ExternalCombustion CommercialInstitutionalBoilers WoodBarkWaste WoodfiredBoilerWetWood20%moisture",
    "10300908":
        "ExternalCombustion CommercialInstitutionalBoilers WoodBarkWaste WoodfiredBoilerDryWood20%moisture",
    "10300910":
        "ExternalCombustion CommercialInstitutionalBoilers WoodBarkWaste FuelcellDutchovenboilers",
    "10300911":
        "ExternalCombustion CommercialInstitutionalBoilers WoodBarkWaste Stokerboilers",
    "10300912":
        "ExternalCombustion CommercialInstitutionalBoilers WoodBarkWaste Fluidizedbedcombustionboiler",
    "10301001":
        "ExternalCombustion CommercialInstitutionalBoilers LiquifiedPetroleumGasLPG Butane",
    "10301002":
        "ExternalCombustion CommercialInstitutionalBoilers LiquifiedPetroleumGasLPG Propane",
    "10301003":
        "ExternalCombustion CommercialInstitutionalBoilers LiquifiedPetroleumGasLPG ButanePropaneMixtureSpecifyPercentButaneinComments",
    "10301101":
        "ExternalCombustion CommercialInstitutionalBoilers Biomass BoilerStoker",
    "10301102":
        "ExternalCombustion CommercialInstitutionalBoilers Biomass BoilerNonstoker",
    "10301201":
        "ExternalCombustion CommercialInstitutionalBoilers SolidWaste SpecifyWasteMaterialinComments",
    "10301202":
        "ExternalCombustion CommercialInstitutionalBoilers SolidWaste RefuseDerivedFuel",
    "10301301":
        "ExternalCombustion CommercialInstitutionalBoilers LiquidWaste SpecifyWasteMaterialinComments",
    "10301302":
        "ExternalCombustion CommercialInstitutionalBoilers LiquidWaste WasteOil",
    "10301303":
        "ExternalCombustion CommercialInstitutionalBoilers LiquidWaste SewageGreaseSkimmings",
    "10500102":
        "ExternalCombustion SpaceHeaters Industrial Coal",
    "10500105":
        "ExternalCombustion SpaceHeaters Industrial DistillateOil",
    "10500106":
        "ExternalCombustion SpaceHeaters Industrial NaturalGas",
    "10500110":
        "ExternalCombustion SpaceHeaters Industrial LiquifiedPetroleumGasLPG",
    "10500113":
        "ExternalCombustion SpaceHeaters Industrial WasteOilAirAtomizedBurner",
    "10500114":
        "ExternalCombustion SpaceHeaters Industrial WasteOilVaporizingBurner",
    "10500202":
        "ExternalCombustion SpaceHeaters CommercialInstitutional Coal",
    "10500205":
        "ExternalCombustion SpaceHeaters CommercialInstitutional DistillateOil",
    "10500206":
        "ExternalCombustion SpaceHeaters CommercialInstitutional NaturalGas",
    "10500209":
        "ExternalCombustion SpaceHeaters CommercialInstitutional Wood",
    "10500210":
        "ExternalCombustion SpaceHeaters CommercialInstitutional LiquifiedPetroleumGasLPG",
    "10500213":
        "ExternalCombustion SpaceHeaters CommercialInstitutional WasteOilAirAtomizedBurner",
    "10500214":
        "ExternalCombustion SpaceHeaters CommercialInstitutional WasteOilVaporizingBurner",
    "20100101":
        "InternalCombustionEngines ElectricGeneration DistillateOilDiesel Turbine",
    "20100102":
        "InternalCombustionEngines ElectricGeneration DistillateOilDiesel Reciprocating",
    "20100105":
        "InternalCombustionEngines ElectricGeneration DistillateOilDiesel ReciprocatingCrankcaseBlowby",
    "20100106":
        "InternalCombustionEngines ElectricGeneration DistillateOilDiesel ReciprocatingEvaporativeLossesFuelStorageandDeliverySystem",
    "20100107":
        "InternalCombustionEngines ElectricGeneration DistillateOilDiesel ReciprocatingExhaust",
    "20100108":
        "InternalCombustionEngines ElectricGeneration DistillateOilDiesel TurbineEvaporativeLossesFuelStorageandDeliverySystem",
    "20100109":
        "InternalCombustionEngines ElectricGeneration DistillateOilDiesel TurbineExhaust",
    "20100201":
        "InternalCombustionEngines ElectricGeneration NaturalGas Turbine",
    "20100202":
        "InternalCombustionEngines ElectricGeneration NaturalGas Reciprocating",
    "20100205":
        "InternalCombustionEngines ElectricGeneration NaturalGas ReciprocatingCrankcaseBlowby",
    "20100206":
        "InternalCombustionEngines ElectricGeneration NaturalGas ReciprocatingEvaporativeLossesFuelDeliverySystem",
    "20100207":
        "InternalCombustionEngines ElectricGeneration NaturalGas ReciprocatingExhaust",
    "20100208":
        "InternalCombustionEngines ElectricGeneration NaturalGas TurbineEvaporativeLossesFuelDeliverySystem",
    "20100209":
        "InternalCombustionEngines ElectricGeneration NaturalGas TurbineExhaust",
    "20100301":
        "InternalCombustionEngines ElectricGeneration GasifiedCoal Turbine",
    "20100702":
        "InternalCombustionEngines ElectricGeneration ProcessGas Reciprocating",
    "20100707":
        "InternalCombustionEngines ElectricGeneration ProcessGas ReciprocatingExhaust",
    "20100801":
        "InternalCombustionEngines ElectricGeneration LandfillGas Turbine",
    "20100802":
        "InternalCombustionEngines ElectricGeneration LandfillGas Reciprocating",
    "20100805":
        "InternalCombustionEngines ElectricGeneration LandfillGas ReciprocatingCrankcaseBlowby",
    "20100807":
        "InternalCombustionEngines ElectricGeneration LandfillGas ReciprocatingExhaust",
    "20100809":
        "InternalCombustionEngines ElectricGeneration LandfillGas TurbineExhaust",
    "20100901":
        "InternalCombustionEngines ElectricGeneration KeroseneNaphthaJetFuel Turbine",
    "20100902":
        "InternalCombustionEngines ElectricGeneration KeroseneNaphthaJetFuel Reciprocating",
    "20100905":
        "InternalCombustionEngines ElectricGeneration KeroseneNaphthaJetFuel ReciprocatingCrankcaseBlowby",
    "20100907":
        "InternalCombustionEngines ElectricGeneration KeroseneNaphthaJetFuel ReciprocatingExhaust",
    "20100908":
        "InternalCombustionEngines ElectricGeneration KeroseneNaphthaJetFuel TurbineEvaporativeLossesFuelStorageandDeliverySystem",
    "20100909":
        "InternalCombustionEngines ElectricGeneration KeroseneNaphthaJetFuel TurbineExhaust",
    "20101001":
        "InternalCombustionEngines ElectricGeneration GeysersGeothermal SteamTurbine",
    "20101010":
        "InternalCombustionEngines ElectricGeneration GeysersGeothermal WellDrillingSteamEmissions",
    "20101020":
        "InternalCombustionEngines ElectricGeneration GeysersGeothermal WellPadFugitivesBlowdown",
    "20101021":
        "InternalCombustionEngines ElectricGeneration GeysersGeothermal WellPadFugitivesVentsLeaks",
    "20101030":
        "InternalCombustionEngines ElectricGeneration GeysersGeothermal PipelineFugitivesBlowdown",
    "20101031":
        "InternalCombustionEngines ElectricGeneration GeysersGeothermal PipelineFugitivesVentsLeaks",
    "20101302":
        "InternalCombustionEngines ElectricGeneration LiquidWaste WasteOilTurbine",
    "20180001":
        "InternalCombustionEngines ElectricGeneration EquipmentLeaks EquipmentLeaks",
    "20182001":
        "InternalCombustionEngines ElectricGeneration WastewaterAggregate ProcessAreaDrains",
    "20182599":
        "InternalCombustionEngines ElectricGeneration WastewaterPointsofGeneration SpecifyPointofGeneration",
    "20190099":
        "InternalCombustionEngines ElectricGeneration Flares HeavyWater",
    "20200101":
        "InternalCombustionEngines Industrial DistillateOilDiesel Turbine",
    "20200102":
        "InternalCombustionEngines Industrial DistillateOilDiesel Reciprocating",
    "20200103":
        "InternalCombustionEngines Industrial DistillateOilDiesel TurbineCogeneration",
    "20200104":
        "InternalCombustionEngines Industrial DistillateOilDiesel ReciprocatingCogeneration",
    "20200105":
        "InternalCombustionEngines Industrial DistillateOilDiesel ReciprocatingCrankcaseBlowby",
    "20200106":
        "InternalCombustionEngines Industrial DistillateOilDiesel ReciprocatingEvaporativeLossesFuelStorageandDeliverySystem",
    "20200107":
        "InternalCombustionEngines Industrial DistillateOilDiesel ReciprocatingExhaust",
    "20200108":
        "InternalCombustionEngines Industrial DistillateOilDiesel TurbineEvaporativeLossesFuelStorageandDeliverySystem",
    "20200109":
        "InternalCombustionEngines Industrial DistillateOilDiesel TurbineExhaust",
    "20200201":
        "InternalCombustionEngines Industrial NaturalGas Turbine",
    "20200202":
        "InternalCombustionEngines Industrial NaturalGas Reciprocating",
    "20200203":
        "InternalCombustionEngines Industrial NaturalGas TurbineCogeneration",
    "20200204":
        "InternalCombustionEngines Industrial NaturalGas ReciprocatingCogeneration",
    "20200205":
        "InternalCombustionEngines Industrial NaturalGas ReciprocatingCrankcaseBlowby",
    "20200206":
        "InternalCombustionEngines Industrial NaturalGas ReciprocatingEvaporativeLossesFuelDeliverySystem",
    "20200207":
        "InternalCombustionEngines Industrial NaturalGas ReciprocatingExhaust",
    "20200208":
        "InternalCombustionEngines Industrial NaturalGas TurbineEvaporativeLossesFuelDeliverySystem",
    "20200209":
        "InternalCombustionEngines Industrial NaturalGas TurbineExhaust",
    "20200251":
        "InternalCombustionEngines Industrial NaturalGas 2cycleRichBurn",
    "20200252":
        "InternalCombustionEngines Industrial NaturalGas 2cycleLeanBurn",
    "20200253":
        "InternalCombustionEngines Industrial NaturalGas 4cycleRichBurn",
    "20200254":
        "InternalCombustionEngines Industrial NaturalGas 4cycleLeanBurn",
    "20200255":
        "InternalCombustionEngines Industrial NaturalGas 2cycleCleanBurn",
    "20200256":
        "InternalCombustionEngines Industrial NaturalGas 4cycleCleanBurn",
    "20200301":
        "InternalCombustionEngines Industrial Gasoline Reciprocating",
    "20200401":
        "InternalCombustionEngines Industrial OtherFuels DieselLargeBoreEngine",
    "20200402":
        "InternalCombustionEngines Industrial OtherFuels DualFuelOilGasLargeBoreEngine",
    "20200403":
        "InternalCombustionEngines Industrial OtherFuels DualFuelLargeBoreEngineCogeneration",
    "20200406":
        "InternalCombustionEngines Industrial OtherFuels LargeBoreEngineEvaporativeLossesFuelStorageandDeliverySystem",
    "20200407":
        "InternalCombustionEngines Industrial OtherFuels LargeBoreEngineExhaust",
    "20200501":
        "InternalCombustionEngines Industrial ResidualCrudeOil Reciprocating",
    "20200506":
        "InternalCombustionEngines Industrial ResidualCrudeOil ReciprocatingEvaporativeLossesFuelStorageandDeliverySystem",
    "20200701":
        "InternalCombustionEngines Industrial ProcessGas Turbine",
    "20200702":
        "InternalCombustionEngines Industrial ProcessGas ReciprocatingEngine",
    "20200705":
        "InternalCombustionEngines Industrial ProcessGas RefineryGasTurbine",
    "20200706":
        "InternalCombustionEngines Industrial ProcessGas RefineryGasReciprocatingEngine",
    "20200711":
        "InternalCombustionEngines Industrial ProcessGas ReciprocatingEvaporativeLossesFuelDeliverySystem",
    "20200712":
        "InternalCombustionEngines Industrial ProcessGas ReciprocatingExhaust",
    "20200714":
        "InternalCombustionEngines Industrial ProcessGas TurbineExhaust",
    "20200901":
        "InternalCombustionEngines Industrial KeroseneNaphthaJetFuel Turbine",
    "20200902":
        "InternalCombustionEngines Industrial KeroseneNaphthaJetFuel Reciprocating",
    "20200905":
        "InternalCombustionEngines Industrial KeroseneNaphthaJetFuel ReciprocatingCrankcaseBlowby",
    "20200907":
        "InternalCombustionEngines Industrial KeroseneNaphthaJetFuel ReciprocatingExhaust",
    "20200908":
        "InternalCombustionEngines Industrial KeroseneNaphthaJetFuel TurbineEvaporativeLossesFuelStorageandDeliverySystem",
    "20200909":
        "InternalCombustionEngines Industrial KeroseneNaphthaJetFuel TurbineExhaust",
    "20201001":
        "InternalCombustionEngines Industrial LiquifiedPetroleumGasLPG PropaneReciprocating",
    "20201002":
        "InternalCombustionEngines Industrial LiquifiedPetroleumGasLPG ButaneReciprocating",
    "20201005":
        "InternalCombustionEngines Industrial LiquifiedPetroleumGasLPG ReciprocatingCrankcaseBlowby",
    "20201006":
        "InternalCombustionEngines Industrial LiquifiedPetroleumGasLPG ReciprocatingEvaporativeLossesFuelStorageandDeliverySystem",
    "20201007":
        "InternalCombustionEngines Industrial LiquifiedPetroleumGasLPG ReciprocatingExhaust",
    "20201011":
        "InternalCombustionEngines Industrial LiquifiedPetroleumGasLPG Turbine",
    "20201012":
        "InternalCombustionEngines Industrial LiquifiedPetroleumGasLPG ReciprocatingEngine",
    "20201013":
        "InternalCombustionEngines Industrial LiquifiedPetroleumGasLPG TurbineCogeneration",
    "20201602":
        "InternalCombustionEngines Industrial Methanol ReciprocatingEngine",
    "20201607":
        "InternalCombustionEngines Industrial Methanol ReciprocatingExhaust",
    "20201609":
        "InternalCombustionEngines Industrial Methanol TurbineExhaust",
    "20201701":
        "InternalCombustionEngines Industrial Gasoline Turbine",
    "20201702":
        "InternalCombustionEngines Industrial Gasoline ReciprocatingEngine",
    "20201706":
        "InternalCombustionEngines Industrial Gasoline ReciprocatingEvaporativeLossesFuelStorageandDeliverySystem",
    "20201707":
        "InternalCombustionEngines Industrial Gasoline ReciprocatingExhaust",
    "20280001":
        "InternalCombustionEngines Industrial EquipmentLeaks EquipmentLeaks",
    "20282001":
        "InternalCombustionEngines Industrial WastewaterAggregate ProcessAreaDrains",
    "20282599":
        "InternalCombustionEngines Industrial WastewaterPointsofGeneration SpecifyPointofGeneration",
    "20300101":
        "InternalCombustionEngines CommercialInstitutional DistillateOilDiesel Reciprocating",
    "20300102":
        "InternalCombustionEngines CommercialInstitutional DistillateOilDiesel Turbine",
    "20300105":
        "InternalCombustionEngines CommercialInstitutional DistillateOilDiesel ReciprocatingCrankcaseBlowby",
    "20300106":
        "InternalCombustionEngines CommercialInstitutional DistillateOilDiesel ReciprocatingEvaporativeLossesFuelStorageandDeliverySystem",
    "20300107":
        "InternalCombustionEngines CommercialInstitutional DistillateOilDiesel ReciprocatingExhaust",
    "20300108":
        "InternalCombustionEngines CommercialInstitutional DistillateOilDiesel TurbineEvaporativeLossesFuelStorageandDeliverySystem",
    "20300109":
        "InternalCombustionEngines CommercialInstitutional DistillateOilDiesel TurbineExhaust",
    "20300201":
        "InternalCombustionEngines CommercialInstitutional NaturalGas Reciprocating",
    "20300202":
        "InternalCombustionEngines CommercialInstitutional NaturalGas Turbine",
    "20300203":
        "InternalCombustionEngines CommercialInstitutional NaturalGas TurbineCogeneration",
    "20300204":
        "InternalCombustionEngines CommercialInstitutional NaturalGas ReciprocatingCogeneration",
    "20300205":
        "InternalCombustionEngines CommercialInstitutional NaturalGas ReciprocatingCrankcaseBlowby",
    "20300206":
        "InternalCombustionEngines CommercialInstitutional NaturalGas ReciprocatingEvaporativeLossesFuelDeliverySystem",
    "20300207":
        "InternalCombustionEngines CommercialInstitutional NaturalGas ReciprocatingExhaust",
    "20300209":
        "InternalCombustionEngines CommercialInstitutional NaturalGas TurbineExhaust",
    "20300301":
        "InternalCombustionEngines CommercialInstitutional Gasoline Reciprocating",
    "20300306":
        "InternalCombustionEngines CommercialInstitutional Gasoline ReciprocatingEvaporativeLossesFuelStorageandDeliverySystem",
    "20300307":
        "InternalCombustionEngines CommercialInstitutional Gasoline ReciprocatingExhaust",
    "20300401":
        "InternalCombustionEngines CommercialInstitutional Diesel LargeBoreEngine",
    "20300701":
        "InternalCombustionEngines CommercialInstitutional DigesterGas Turbine",
    "20300702":
        "InternalCombustionEngines CommercialInstitutional DigesterGas ReciprocatingPOTWDigesterGas",
    "20300705":
        "InternalCombustionEngines CommercialInstitutional DigesterGas ReciprocatingCrankcaseBlowby",
    "20300706":
        "InternalCombustionEngines CommercialInstitutional DigesterGas ReciprocatingEvaporativeLossesFuelStorageandDeliverySystem",
    "20300707":
        "InternalCombustionEngines CommercialInstitutional DigesterGas ReciprocatingExhaust",
    "20300709":
        "InternalCombustionEngines CommercialInstitutional DigesterGas TurbineExhaust",
    "20300801":
        "InternalCombustionEngines CommercialInstitutional LandfillGas Turbine",
    "20300802":
        "InternalCombustionEngines CommercialInstitutional LandfillGas Reciprocating",
    "20300805":
        "InternalCombustionEngines CommercialInstitutional LandfillGas ReciprocatingCrankcaseBlowby",
    "20300807":
        "InternalCombustionEngines CommercialInstitutional LandfillGas ReciprocatingExhaust",
    "20300809":
        "InternalCombustionEngines CommercialInstitutional LandfillGas TurbineExhaust",
    "20300901":
        "InternalCombustionEngines CommercialInstitutional KeroseneNaphthaJetFuel TurbineJP4",
    "20300909":
        "InternalCombustionEngines CommercialInstitutional KeroseneNaphthaJetFuel TurbineExhaust",
    "20301001":
        "InternalCombustionEngines CommercialInstitutional LiquifiedPetroleumGasLPG PropaneReciprocating",
    "20301002":
        "InternalCombustionEngines CommercialInstitutional LiquifiedPetroleumGasLPG ButaneReciprocating",
    "20301007":
        "InternalCombustionEngines CommercialInstitutional LiquifiedPetroleumGasLPG ReciprocatingExhaust",
    "20380001":
        "InternalCombustionEngines CommercialInstitutional EquipmentLeaks EquipmentLeaks",
    "20400101":
        "InternalCombustionEngines EngineTesting AircraftEngineTesting Turbojet",
    "20400102":
        "InternalCombustionEngines EngineTesting AircraftEngineTesting Turboshaft",
    "20400110":
        "InternalCombustionEngines EngineTesting AircraftEngineTesting JetAFuel",
    "20400111":
        "InternalCombustionEngines EngineTesting AircraftEngineTesting JP5Fuel",
    "20400112":
        "InternalCombustionEngines EngineTesting AircraftEngineTesting JP4Fuel",
    "20400199":
        "InternalCombustionEngines EngineTesting AircraftEngineTesting OtherNotClassified",
    "20400201":
        "InternalCombustionEngines EngineTesting RocketEngineTesting RocketMotorSolidPropellant",
    "20400202":
        "InternalCombustionEngines EngineTesting RocketEngineTesting LiquidPropellant",
    "20400299":
        "InternalCombustionEngines EngineTesting RocketEngineTesting OtherNotClassified",
    "20400301":
        "InternalCombustionEngines EngineTesting Turbine NaturalGas",
    "20400302":
        "InternalCombustionEngines EngineTesting Turbine DieselKerosene",
    "20400303":
        "InternalCombustionEngines EngineTesting Turbine DistillateOil",
    "20400304":
        "InternalCombustionEngines EngineTesting Turbine LandfillGas",
    "20400305":
        "InternalCombustionEngines EngineTesting Turbine KeroseneNaphtha",
    "20400399":
        "InternalCombustionEngines EngineTesting Turbine OtherNotClassified",
    "20400401":
        "InternalCombustionEngines EngineTesting ReciprocatingEngine Gasoline",
    "20400402":
        "InternalCombustionEngines EngineTesting ReciprocatingEngine DieselKerosene",
    "20400403":
        "InternalCombustionEngines EngineTesting ReciprocatingEngine DistillateOil",
    "20400404":
        "InternalCombustionEngines EngineTesting ReciprocatingEngine ProcessGas",
    "20400406":
        "InternalCombustionEngines EngineTesting ReciprocatingEngine KeroseneNaphthaJetFuel",
    "20400407":
        "InternalCombustionEngines EngineTesting ReciprocatingEngine DualFuelGasOil",
    "20400408":
        "InternalCombustionEngines EngineTesting ReciprocatingEngine ResidualOilCrudeOil",
    "20400409":
        "InternalCombustionEngines EngineTesting ReciprocatingEngine LiquifiedPetroleumGasLPG",
    "20400499":
        "InternalCombustionEngines EngineTesting ReciprocatingEngine OtherNotClassified",
    "20482599":
        "InternalCombustionEngines EngineTesting WastewaterPointsofGeneration SpecifyPointofGeneration",
    "26000320":
        "InternalCombustionEngines Offhighway2strokeGasolineEngines IndustrialEquipment IndustrialForkLiftGasolineEngine2stroke",
    "26500320":
        "InternalCombustionEngines Offhighway4strokeGasolineEngines IndustrialEquipment IndustrialForkLiftGasolineEngine4stroke",
    "27000320":
        "InternalCombustionEngines OffhighwayDieselEngines IndustrialEquipment IndustrialForkLiftDiesel",
    "27300320":
        "InternalCombustionEngines OffhighwayLPGfueledEngines IndustrialEquipment IndustrialForkLiftLiquifiedPetroleumGasLPG",
    "27501015":
        "InternalCombustionEngines FixedWingAircraftL&TOExhaust Military JetEngineJP5",
    "27502011":
        "InternalCombustionEngines FixedWingAircraftL&TOExhaust Commercial JetEngineJetA",
    "27505001":
        "InternalCombustionEngines FixedWingAircraftL&TOExhaust Civil PistonEngineAviationGas",
    "27505011":
        "InternalCombustionEngines FixedWingAircraftL&TOExhaust Civil JetEngineJetA",
    "27601014":
        "InternalCombustionEngines RotaryWingAircraftL&TOExhaust Military JetEngineJP4",
    "27601015":
        "InternalCombustionEngines RotaryWingAircraftL&TOExhaust Military JetEngineJP5",
    "27602011":
        "InternalCombustionEngines RotaryWingAircraftL&TOExhaust Commercial JetEngineJetA",
    "28000211":
        "InternalCombustionEngines MarineVesselsCommercial Diesel CrewBoatsMainEngineExhaustIdling",
    "28000212":
        "InternalCombustionEngines MarineVesselsCommercial Diesel CrewBoatsMainEngineExhaustManeuvering",
    "28000213":
        "InternalCombustionEngines MarineVesselsCommercial Diesel CrewBoatsAuxiliaryGeneratorExhaustHotelling",
    "28000216":
        "InternalCombustionEngines MarineVesselsCommercial Diesel SupplyBoatsMainEngineExhaustIdling",
    "28000217":
        "InternalCombustionEngines MarineVesselsCommercial Diesel SupplyBoatsMainEngineExhaustManeuvering",
    "28000218":
        "InternalCombustionEngines MarineVesselsCommercial Diesel SupplyBoatsAuxiliaryGeneratorExhaustHotelling",
    "28500201":
        "InternalCombustionEngines RailroadEquipment Diesel YardLocomotives",
    "28888801":
        "InternalCombustionEngines FugitiveEmissions OtherNotClassified SpecifyinComments",
    "30100101":
        "IndustrialProcesses ChemicalManufacturing AdipicAcid General",
    "30100102":
        "IndustrialProcesses ChemicalManufacturing AdipicAcid RawMaterialStorage",
    "30100103":
        "IndustrialProcesses ChemicalManufacturing AdipicAcid CyclohexaneOxidation",
    "30100104":
        "IndustrialProcesses ChemicalManufacturing AdipicAcid NitricAcidReaction",
    "30100105":
        "IndustrialProcesses ChemicalManufacturing AdipicAcid AdipicAcidRefining",
    "30100106":
        "IndustrialProcesses ChemicalManufacturing AdipicAcid DryingLoadingandStorage",
    "30100107":
        "IndustrialProcesses ChemicalManufacturing AdipicAcid Absorber",
    "30100108":
        "IndustrialProcesses ChemicalManufacturing AdipicAcid Dryer",
    "30100109":
        "IndustrialProcesses ChemicalManufacturing AdipicAcid Cooler",
    "30100110":
        "IndustrialProcesses ChemicalManufacturing AdipicAcid LoadingAndStorage",
    "30100180":
        "IndustrialProcesses ChemicalManufacturing AdipicAcid FugitiveEmissionsGeneral",
    "30100199":
        "IndustrialProcesses ChemicalManufacturing AdipicAcid OtherNotClassified",
    "30100305":
        "IndustrialProcesses ChemicalManufacturing AmmoniaProduction FeedstockDesulfurization",
    "30100306":
        "IndustrialProcesses ChemicalManufacturing AmmoniaProduction PrimaryReformerNaturalGasFired",
    "30100307":
        "IndustrialProcesses ChemicalManufacturing AmmoniaProduction PrimaryReformerOilFired",
    "30100308":
        "IndustrialProcesses ChemicalManufacturing AmmoniaProduction CarbonDioxideRegenerator",
    "30100309":
        "IndustrialProcesses ChemicalManufacturing AmmoniaProduction CondensateStripper",
    "30100310":
        "IndustrialProcesses ChemicalManufacturing AmmoniaProduction StorageandLoadingTanks",
    "30100399":
        "IndustrialProcesses ChemicalManufacturing AmmoniaProduction OtherNotClassified",
    "30100502":
        "IndustrialProcesses ChemicalManufacturing CarbonBlackProduction ThermalProcess",
    "30100503":
        "IndustrialProcesses ChemicalManufacturing CarbonBlackProduction GasFurnaceProcessMainProcessVent",
    "30100504":
        "IndustrialProcesses ChemicalManufacturing CarbonBlackProduction OilFurnaceProcessMainProcessVent",
    "30100506":
        "IndustrialProcesses ChemicalManufacturing CarbonBlackProduction TransportAirVent",
    "30100507":
        "IndustrialProcesses ChemicalManufacturing CarbonBlackProduction PelletDryer",
    "30100508":
        "IndustrialProcesses ChemicalManufacturing CarbonBlackProduction BaggingLoading",
    "30100509":
        "IndustrialProcesses ChemicalManufacturing CarbonBlackProduction FurnaceProcessFugitiveEmissions",
    "30100510":
        "IndustrialProcesses ChemicalManufacturing CarbonBlackProduction MainProcessVentwithCOBoilerandIncinerator",
    "30100599":
        "IndustrialProcesses ChemicalManufacturing CarbonBlackProduction OtherNotClassified",
    "30100601":
        "IndustrialProcesses ChemicalManufacturing CharcoalManufacturing General",
    "30100603":
        "IndustrialProcesses ChemicalManufacturing CharcoalManufacturing BatchKiln",
    "30100604":
        "IndustrialProcesses ChemicalManufacturing CharcoalManufacturing ContinuousKiln",
    "30100605":
        "IndustrialProcesses ChemicalManufacturing CharcoalManufacturing Briquetting",
    "30100606":
        "IndustrialProcesses ChemicalManufacturing CharcoalManufacturing RawMaterialHandling",
    "30100607":
        "IndustrialProcesses ChemicalManufacturing CharcoalManufacturing Crushing",
    "30100608":
        "IndustrialProcesses ChemicalManufacturing CharcoalManufacturing HandlingandStorage",
    "30100699":
        "IndustrialProcesses ChemicalManufacturing CharcoalManufacturing OtherNotClassified",
    "30100701":
        "IndustrialProcesses ChemicalManufacturing Chlorine CarbonReactivation",
    "30100702":
        "IndustrialProcesses ChemicalManufacturing Chlorine CarbonReactivationImpregnationKiln",
    "30100705":
        "IndustrialProcesses ChemicalManufacturing Chlorine CarbonReactivationFugitives",
    "30100706":
        "IndustrialProcesses ChemicalManufacturing Chlorine CarbonReactivationAfterburner",
    "30100709":
        "IndustrialProcesses ChemicalManufacturing Chlorine CarbonReactivationProductHandlingMeshPrss",
    "30100799":
        "IndustrialProcesses ChemicalManufacturing Chlorine OtherNotClassified",
    "30100801":
        "IndustrialProcesses ChemicalManufacturing ChloroalkaliProduction LiquefactionDiaphragmCellProcess",
    "30100802":
        "IndustrialProcesses ChemicalManufacturing ChloroalkaliProduction LiquefactionMercuryCellProcess",
    "30100804":
        "IndustrialProcesses ChemicalManufacturing ChloroalkaliProduction ChlorineLoadingStorageCarVent",
    "30100805":
        "IndustrialProcesses ChemicalManufacturing ChloroalkaliProduction AirBlowingofMercuryCellBrine",
    "30100899":
        "IndustrialProcesses ChemicalManufacturing ChloroalkaliProduction OtherNotClassified",
    "30100901":
        "IndustrialProcesses ChemicalManufacturing CleaningChemicals SprayDryingSoapsandDetergents",
    "30100902":
        "IndustrialProcesses ChemicalManufacturing CleaningChemicals SpecialtyCleaners",
    "30100905":
        "IndustrialProcesses ChemicalManufacturing CleaningChemicals AlkalineSaponification",
    "30100906":
        "IndustrialProcesses ChemicalManufacturing CleaningChemicals DirectSaponification",
    "30100907":
        "IndustrialProcesses ChemicalManufacturing CleaningChemicals BlendingAndMixing",
    "30100908":
        "IndustrialProcesses ChemicalManufacturing CleaningChemicals SoapPackaging",
    "30100909":
        "IndustrialProcesses ChemicalManufacturing CleaningChemicals DetergentSlurryPreparation",
    "30100910":
        "IndustrialProcesses ChemicalManufacturing CleaningChemicals DetergentGranuleHandling",
    "30100999":
        "IndustrialProcesses ChemicalManufacturing CleaningChemicals OtherNotClassified",
    "30101005":
        "IndustrialProcesses ChemicalManufacturing ExplosivesTrinitrotoluene NitricSulfuricAcidMixing",
    "30101010":
        "IndustrialProcesses ChemicalManufacturing ExplosivesTrinitrotoluene ProcessVentsBatchProcess",
    "30101011":
        "IndustrialProcesses ChemicalManufacturing ExplosivesTrinitrotoluene BatchProcessNitrationReactorsFumeRecovery",
    "30101014":
        "IndustrialProcesses ChemicalManufacturing ExplosivesTrinitrotoluene BatchProcessSulfuricAcidConcentrators",
    "30101022":
        "IndustrialProcesses ChemicalManufacturing ExplosivesTrinitrotoluene ContinuousProcessNitrationReactorAcidRecoverUse30101052",
    "30101030":
        "IndustrialProcesses ChemicalManufacturing ExplosivesTrinitrotoluene OpenBurningWaste",
    "30101046":
        "IndustrialProcesses ChemicalManufacturing ExplosivesTrinitrotoluene BatchProcessFinishingDryers",
    "30101055":
        "IndustrialProcesses ChemicalManufacturing ExplosivesTrinitrotoluene ContinuousProcessSulfuricAcidConcentrators",
    "30101086":
        "IndustrialProcesses ChemicalManufacturing ExplosivesTrinitrotoluene ContinuousProcessFinishingDryers",
    "30101099":
        "IndustrialProcesses ChemicalManufacturing ExplosivesTrinitrotoluene OtherNotClassified",
    "30101101":
        "IndustrialProcesses ChemicalManufacturing HydrochloricAcid ByproductProcess",
    "30101198":
        "IndustrialProcesses ChemicalManufacturing HydrochloricAcid TransferOperations",
    "30101199":
        "IndustrialProcesses ChemicalManufacturing HydrochloricAcid OtherNotElsewhereClassified",
    "30101202":
        "IndustrialProcesses ChemicalManufacturing HydrofluoricAcid RotaryKilnAcidReactor",
    "30101203":
        "IndustrialProcesses ChemicalManufacturing HydrofluoricAcid FluorsparGrindingDrying",
    "30101204":
        "IndustrialProcesses ChemicalManufacturing HydrofluoricAcid FluorsparHandlingSilos",
    "30101205":
        "IndustrialProcesses ChemicalManufacturing HydrofluoricAcid FluorsparTransfer",
    "30101206":
        "IndustrialProcesses ChemicalManufacturing HydrofluoricAcid TailGasVent",
    "30101299":
        "IndustrialProcesses ChemicalManufacturing HydrofluoricAcid General",
    "30101301":
        "IndustrialProcesses ChemicalManufacturing NitricAcid AbsorberTailGasPre1970Facilities",
    "30101302":
        "IndustrialProcesses ChemicalManufacturing NitricAcid AbsorberTailGasPost1970Facilities",
    "30101303":
        "IndustrialProcesses ChemicalManufacturing NitricAcid NitricAcidConcentratorsPre1970Facilities",
    "30101304":
        "IndustrialProcesses ChemicalManufacturing NitricAcid NitricAcidConcentratorsPost1970Facilities",
    "30101399":
        "IndustrialProcesses ChemicalManufacturing NitricAcid General",
    "30101401":
        "IndustrialProcesses ChemicalManufacturing PaintManufacture GeneralMixingandHandling",
    "30101402":
        "IndustrialProcesses ChemicalManufacturing PaintManufacture PigmentHandling",
    "30101403":
        "IndustrialProcesses ChemicalManufacturing PaintManufacture SolventLossGeneral",
    "30101404":
        "IndustrialProcesses ChemicalManufacturing PaintManufacture RawMaterialStorage",
    "30101415":
        "IndustrialProcesses ChemicalManufacturing PaintManufacture PremixPreassembly",
    "30101416":
        "IndustrialProcesses ChemicalManufacturing PaintManufacture PremixPreassemblyMixTanksandAgitators",
    "30101418":
        "IndustrialProcesses ChemicalManufacturing PaintManufacture PremixPreassemblyMaterialLoading",
    "30101430":
        "IndustrialProcesses ChemicalManufacturing PaintManufacture PigmentGrindingMilling",
    "30101431":
        "IndustrialProcesses ChemicalManufacturing PaintManufacture PigmentGrindingMillingRollerMills",
    "30101432":
        "IndustrialProcesses ChemicalManufacturing PaintManufacture PigmentGrindingMillingBallandPebbleMills",
    "30101434":
        "IndustrialProcesses ChemicalManufacturing PaintManufacture PigmentGrindingMillingSandMills",
    "30101441":
        "IndustrialProcesses ChemicalManufacturing PaintManufacture PigmentGrindingMillingHorizontalMediaMills",
    "30101450":
        "IndustrialProcesses ChemicalManufacturing PaintManufacture ProductFinishing",
    "30101451":
        "IndustrialProcesses ChemicalManufacturing PaintManufacture ProductFinishingTintingMixTankandDisperser",
    "30101452":
        "IndustrialProcesses ChemicalManufacturing PaintManufacture ProductFinishingTintingFixedBlendTank",
    "30101453":
        "IndustrialProcesses ChemicalManufacturing PaintManufacture ProductFinishingThinningMixTankandDisperser",
    "30101454":
        "IndustrialProcesses ChemicalManufacturing PaintManufacture ProductFinishingThinningFixedBlendTank",
    "30101460":
        "IndustrialProcesses ChemicalManufacturing PaintManufacture ProductFilling",
    "30101461":
        "IndustrialProcesses ChemicalManufacturing PaintManufacture ProductFillingScaleSystem",
    "30101463":
        "IndustrialProcesses ChemicalManufacturing PaintManufacture ProductFillingFillingOperations",
    "30101470":
        "IndustrialProcesses ChemicalManufacturing PaintManufacture EquipmentCleaning",
    "30101471":
        "IndustrialProcesses ChemicalManufacturing PaintManufacture EquipmentCleaningHandWipe",
    "30101472":
        "IndustrialProcesses ChemicalManufacturing PaintManufacture EquipmentCleaningTanksVesselsetc.",
    "30101499":
        "IndustrialProcesses ChemicalManufacturing PaintManufacture OtherNotClassified",
    "30101501":
        "IndustrialProcesses ChemicalManufacturing VarnishManufacturing BodyingOil",
    "30101502":
        "IndustrialProcesses ChemicalManufacturing VarnishManufacturing Oleoresinous",
    "30101503":
        "IndustrialProcesses ChemicalManufacturing VarnishManufacturing Alkyd",
    "30101505":
        "IndustrialProcesses ChemicalManufacturing VarnishManufacturing Acrylic",
    "30101510":
        "IndustrialProcesses ChemicalManufacturing VarnishManufacturing OilStorage",
    "30101520":
        "IndustrialProcesses ChemicalManufacturing VarnishManufacturing VarnishCooking",
    "30101530":
        "IndustrialProcesses ChemicalManufacturing VarnishManufacturing VarnishThinning",
    "30101550":
        "IndustrialProcesses ChemicalManufacturing VarnishManufacturing EndProductTransfer",
    "30101560":
        "IndustrialProcesses ChemicalManufacturing VarnishManufacturing EndProductStorage",
    "30101599":
        "IndustrialProcesses ChemicalManufacturing VarnishManufacturing OtherNotClassified",
    "30101601":
        "IndustrialProcesses ChemicalManufacturing PhosphoricAcid WetProcessReactor",
    "30101602":
        "IndustrialProcesses ChemicalManufacturing PhosphoricAcid WetProcessGypsumDewateringStack",
    "30101603":
        "IndustrialProcesses ChemicalManufacturing PhosphoricAcid WetProcessCondenser",
    "30101620":
        "IndustrialProcesses ChemicalManufacturing PhosphoricAcid SuperphosphoricAcidProcessOxidationReactor",
    "30101698":
        "IndustrialProcesses ChemicalManufacturing PhosphoricAcid FugitiveEmissions",
    "30101699":
        "IndustrialProcesses ChemicalManufacturing PhosphoricAcid PhosphoricAcidWetProcessOtherNotClassified",
    "30101704":
        "IndustrialProcesses ChemicalManufacturing PhosphoricAcidThermalProcess AbsorberwithVenturiScrubber",
    "30101705":
        "IndustrialProcesses ChemicalManufacturing PhosphoricAcidThermalProcess AbsorberwithGlassMistEliminator",
    "30101706":
        "IndustrialProcesses ChemicalManufacturing PhosphoricAcidThermalProcess AbsorberwithWireMistEliminator",
    "30101707":
        "IndustrialProcesses ChemicalManufacturing PhosphoricAcidThermalProcess AbsorberwithHighpressureMistEliminator",
    "30101799":
        "IndustrialProcesses ChemicalManufacturing PhosphoricAcidThermalProcess OtherNotClassified",
    "30101801":
        "IndustrialProcesses ChemicalManufacturing PlasticsProduction PolyvinylChloridesandCopolymersUse6463X0XX",
    "30101802":
        "IndustrialProcesses ChemicalManufacturing PlasticsProduction PolypropyleneandCopolymers",
    "30101803":
        "IndustrialProcesses ChemicalManufacturing PlasticsProduction EthylenePropyleneCopolymers",
    "30101805":
        "IndustrialProcesses ChemicalManufacturing PlasticsProduction PhenolicResins",
    "30101807":
        "IndustrialProcesses ChemicalManufacturing PlasticsProduction GeneralPolyethyleneHighDensity",
    "30101808":
        "IndustrialProcesses ChemicalManufacturing PlasticsProduction MonomerandSolventStorage",
    "30101809":
        "IndustrialProcesses ChemicalManufacturing PlasticsProduction Extruder",
    "30101810":
        "IndustrialProcesses ChemicalManufacturing PlasticsProduction Conveying",
    "30101811":
        "IndustrialProcesses ChemicalManufacturing PlasticsProduction Storage",
    "30101812":
        "IndustrialProcesses ChemicalManufacturing PlasticsProduction GeneralPolyethyleneLowDensity",
    "30101813":
        "IndustrialProcesses ChemicalManufacturing PlasticsProduction RecoveryandPurificationSystem",
    "30101814":
        "IndustrialProcesses ChemicalManufacturing PlasticsProduction Extruder",
    "30101815":
        "IndustrialProcesses ChemicalManufacturing PlasticsProduction PelletSilo",
    "30101816":
        "IndustrialProcesses ChemicalManufacturing PlasticsProduction TransferringHandlingLoadingPacking",
    "30101817":
        "IndustrialProcesses ChemicalManufacturing PlasticsProduction General",
    "30101818":
        "IndustrialProcesses ChemicalManufacturing PlasticsProduction Reactor",
    "30101819":
        "IndustrialProcesses ChemicalManufacturing PlasticsProduction SolventRecovery",
    "30101820":
        "IndustrialProcesses ChemicalManufacturing PlasticsProduction PolymerDrying",
    "30101821":
        "IndustrialProcesses ChemicalManufacturing PlasticsProduction ExtrudingPelletizingConveyingStorage",
    "30101822":
        "IndustrialProcesses ChemicalManufacturing PlasticsProduction AcrylicResins",
    "30101827":
        "IndustrialProcesses ChemicalManufacturing PlasticsProduction PolyamideResins",
    "30101832":
        "IndustrialProcesses ChemicalManufacturing PlasticsProduction UreaFormaldehydeResins",
    "30101837":
        "IndustrialProcesses ChemicalManufacturing PlasticsProduction PolyesterResins",
    "30101838":
        "IndustrialProcesses ChemicalManufacturing PlasticsProduction ReactorKettle",
    "30101839":
        "IndustrialProcesses ChemicalManufacturing PlasticsProduction ResinThinningTank",
    "30101840":
        "IndustrialProcesses ChemicalManufacturing PlasticsProduction ResinStorageTank",
    "30101842":
        "IndustrialProcesses ChemicalManufacturing PlasticsProduction MelamineResins",
    "30101847":
        "IndustrialProcesses ChemicalManufacturing PlasticsProduction EpoxyResins",
    "30101849":
        "IndustrialProcesses ChemicalManufacturing PlasticsProduction AcrylonitrileButadieneStyreneABSResin",
    "30101852":
        "IndustrialProcesses ChemicalManufacturing PlasticsProduction Polyfluorocarbons",
    "30101860":
        "IndustrialProcesses ChemicalManufacturing PlasticsProduction RecoverySystemPolyethylene",
    "30101861":
        "IndustrialProcesses ChemicalManufacturing PlasticsProduction PurificationSystemPolyethylene",
    "30101863":
        "IndustrialProcesses ChemicalManufacturing PlasticsProduction Extruder",
    "30101864":
        "IndustrialProcesses ChemicalManufacturing PlasticsProduction PelletSiloStorage",
    "30101865":
        "IndustrialProcesses ChemicalManufacturing PlasticsProduction TransferringConveying",
    "30101866":
        "IndustrialProcesses ChemicalManufacturing PlasticsProduction PackingShipping",
    "30101870":
        "IndustrialProcesses ChemicalManufacturing PlasticsProduction PolyetherResinsReactor",
    "30101871":
        "IndustrialProcesses ChemicalManufacturing PlasticsProduction PolyetherResinsBlowingAgentFreon",
    "30101872":
        "IndustrialProcesses ChemicalManufacturing PlasticsProduction PolyetherResinsGeneral",
    "30101880":
        "IndustrialProcesses ChemicalManufacturing PlasticsProduction PolyurethaneReactor",
    "30101881":
        "IndustrialProcesses ChemicalManufacturing PlasticsProduction PolyurethaneBlowingAgentFreon",
    "30101882":
        "IndustrialProcesses ChemicalManufacturing PlasticsProduction PolyurethaneBlowingAgentMethyleneChloride",
    "30101883":
        "IndustrialProcesses ChemicalManufacturing PlasticsProduction PolyurethaneTransferringConveyingStorage",
    "30101884":
        "IndustrialProcesses ChemicalManufacturing PlasticsProduction PolyurethanePackingShipping",
    "30101885":
        "IndustrialProcesses ChemicalManufacturing PlasticsProduction PolyurethaneGeneral",
    "30101890":
        "IndustrialProcesses ChemicalManufacturing PlasticsProduction CatalystPreparation",
    "30101891":
        "IndustrialProcesses ChemicalManufacturing PlasticsProduction ReactorVents",
    "30101892":
        "IndustrialProcesses ChemicalManufacturing PlasticsProduction SeparationProcesses",
    "30101893":
        "IndustrialProcesses ChemicalManufacturing PlasticsProduction RawMaterialStorage",
    "30101894":
        "IndustrialProcesses ChemicalManufacturing PlasticsProduction SolventStorage",
    "30101899":
        "IndustrialProcesses ChemicalManufacturing PlasticsProduction OthersNotSpecified",
    "30101901":
        "IndustrialProcesses ChemicalManufacturing PhthalicAnhydride oXyleneOxidationMainProcessStream",
    "30101904":
        "IndustrialProcesses ChemicalManufacturing PhthalicAnhydride oXyleneOxidationDistillation",
    "30101906":
        "IndustrialProcesses ChemicalManufacturing PhthalicAnhydride NaphthaleneOxidationPreTreatment",
    "30101907":
        "IndustrialProcesses ChemicalManufacturing PhthalicAnhydride NaphthaleneOxidationDistillation",
    "30101908":
        "IndustrialProcesses ChemicalManufacturing PhthalicAnhydride Dryer",
    "30101909":
        "IndustrialProcesses ChemicalManufacturing PhthalicAnhydride FlakingandBagging",
    "30102001":
        "IndustrialProcesses ChemicalManufacturing PrintingInkManufacture VehicleCookingGeneral",
    "30102002":
        "IndustrialProcesses ChemicalManufacturing PrintingInkManufacture VehicleCookingOils",
    "30102004":
        "IndustrialProcesses ChemicalManufacturing PrintingInkManufacture VehicleCookingAlkyds",
    "30102005":
        "IndustrialProcesses ChemicalManufacturing PrintingInkManufacture PigmentMixing",
    "30102015":
        "IndustrialProcesses ChemicalManufacturing PrintingInkManufacture PremixPreassembly",
    "30102017":
        "IndustrialProcesses ChemicalManufacturing PrintingInkManufacture PremixPreassemblyDrums",
    "30102018":
        "IndustrialProcesses ChemicalManufacturing PrintingInkManufacture PremixPreassemblyMaterialLoading",
    "30102030":
        "IndustrialProcesses ChemicalManufacturing PrintingInkManufacture PigmentGrindingMilling",
    "30102031":
        "IndustrialProcesses ChemicalManufacturing PrintingInkManufacture PigmentGrindingMillingRollerMills",
    "30102032":
        "IndustrialProcesses ChemicalManufacturing PrintingInkManufacture PigmentGrindingMillingBallandPebbleMills",
    "30102036":
        "IndustrialProcesses ChemicalManufacturing PrintingInkManufacture PigmentGrindingMillingShotMills",
    "30102050":
        "IndustrialProcesses ChemicalManufacturing PrintingInkManufacture ProductFinishing",
    "30102051":
        "IndustrialProcesses ChemicalManufacturing PrintingInkManufacture ProductFinishingTintingMixTankandDisperser",
    "30102052":
        "IndustrialProcesses ChemicalManufacturing PrintingInkManufacture ProductFinishingTintingFixedBlendTank",
    "30102053":
        "IndustrialProcesses ChemicalManufacturing PrintingInkManufacture ProductFinishingThinningMixTankandDisperser",
    "30102054":
        "IndustrialProcesses ChemicalManufacturing PrintingInkManufacture ProductFinishingThinningFixedBlendTank",
    "30102060":
        "IndustrialProcesses ChemicalManufacturing PrintingInkManufacture ProductFilling",
    "30102061":
        "IndustrialProcesses ChemicalManufacturing PrintingInkManufacture ProductFillingScaleSystem",
    "30102063":
        "IndustrialProcesses ChemicalManufacturing PrintingInkManufacture ProductFillingFillingOperations",
    "30102070":
        "IndustrialProcesses ChemicalManufacturing PrintingInkManufacture EquipmentCleaning",
    "30102071":
        "IndustrialProcesses ChemicalManufacturing PrintingInkManufacture EquipmentCleaningHandWipe",
    "30102072":
        "IndustrialProcesses ChemicalManufacturing PrintingInkManufacture EquipmentCleaningTanksVesselsetc.",
    "30102099":
        "IndustrialProcesses ChemicalManufacturing PrintingInkManufacture OtherNotClassified",
    "30102102":
        "IndustrialProcesses ChemicalManufacturing SodiumCarbonate SolvayProcessHandling",
    "30102103":
        "IndustrialProcesses ChemicalManufacturing SodiumCarbonate TronaCrushingScreening",
    "30102104":
        "IndustrialProcesses ChemicalManufacturing SodiumCarbonate MonohydrateProcessRotaryOreCalcinerGasfired",
    "30102105":
        "IndustrialProcesses ChemicalManufacturing SodiumCarbonate MonohydrateProcessRotaryOreCalcinerCoalfired",
    "30102106":
        "IndustrialProcesses ChemicalManufacturing SodiumCarbonate RotarySodaAshDryers",
    "30102107":
        "IndustrialProcesses ChemicalManufacturing SodiumCarbonate FluidbedSodaAshDryersCoolers",
    "30102108":
        "IndustrialProcesses ChemicalManufacturing SodiumCarbonate Dissolver",
    "30102110":
        "IndustrialProcesses ChemicalManufacturing SodiumCarbonate TronaCalcining",
    "30102111":
        "IndustrialProcesses ChemicalManufacturing SodiumCarbonate TronaDryer",
    "30102113":
        "IndustrialProcesses ChemicalManufacturing SodiumCarbonate BleacherGasfired",
    "30102114":
        "IndustrialProcesses ChemicalManufacturing SodiumCarbonate RotaryDryerSteamTube",
    "30102120":
        "IndustrialProcesses ChemicalManufacturing SodiumCarbonate BrineEvaporation",
    "30102121":
        "IndustrialProcesses ChemicalManufacturing SodiumCarbonate OreCrushingandScreening",
    "30102122":
        "IndustrialProcesses ChemicalManufacturing SodiumCarbonate SodaAshStorageLoadingandUnloading",
    "30102123":
        "IndustrialProcesses ChemicalManufacturing SodiumCarbonate OreMining",
    "30102124":
        "IndustrialProcesses ChemicalManufacturing SodiumCarbonate OreTransfer",
    "30102125":
        "IndustrialProcesses ChemicalManufacturing SodiumCarbonate SesquicarbonateProcessRotaryCalciner",
    "30102126":
        "IndustrialProcesses ChemicalManufacturing SodiumCarbonate SesquicarbonateProcessFluidbedCalciner",
    "30102127":
        "IndustrialProcesses ChemicalManufacturing SodiumCarbonate SodaAshScreening",
    "30102199":
        "IndustrialProcesses ChemicalManufacturing SodiumCarbonate OtherNotClassified",
    "30102201":
        "IndustrialProcesses ChemicalManufacturing SulfuricAcidChamberProcess General",
    "30102301":
        "IndustrialProcesses ChemicalManufacturing SulfuricAcid Absorber99.9%Conversion",
    "30102304":
        "IndustrialProcesses ChemicalManufacturing SulfuricAcid Absorber99.5%Conversion",
    "30102306":
        "IndustrialProcesses ChemicalManufacturing SulfuricAcid Absorber99.0%Conversion",
    "30102308":
        "IndustrialProcesses ChemicalManufacturing SulfuricAcid Absorber98.0%Conversion",
    "30102310":
        "IndustrialProcesses ChemicalManufacturing SulfuricAcid Absorber97.0%Conversion",
    "30102312":
        "IndustrialProcesses ChemicalManufacturing SulfuricAcid Absorber96.0%Conversion",
    "30102314":
        "IndustrialProcesses ChemicalManufacturing SulfuricAcid Absorber95.0%Conversion",
    "30102318":
        "IndustrialProcesses ChemicalManufacturing SulfuricAcid Absorber93.0%Conversion",
    "30102319":
        "IndustrialProcesses ChemicalManufacturing SulfuricAcid Concentrator",
    "30102320":
        "IndustrialProcesses ChemicalManufacturing SulfuricAcid TankCarandTruckUnloading",
    "30102321":
        "IndustrialProcesses ChemicalManufacturing SulfuricAcid StorageTankVent",
    "30102322":
        "IndustrialProcesses ChemicalManufacturing SulfuricAcid EquipmentLeaks",
    "30102323":
        "IndustrialProcesses ChemicalManufacturing SulfuricAcid SulfurMeltingandFiltering",
    "30102325":
        "IndustrialProcesses ChemicalManufacturing SulfuricAcid GasCleaningandCooling",
    "30102330":
        "IndustrialProcesses ChemicalManufacturing SulfuricAcid CombustionChamber",
    "30102331":
        "IndustrialProcesses ChemicalManufacturing SulfuricAcid DryingTower",
    "30102399":
        "IndustrialProcesses ChemicalManufacturing SulfuricAcid General",
    "30102401":
        "IndustrialProcesses ChemicalManufacturing SyntheticOrganicFiber Nylon#6StapleUncontrolled",
    "30102402":
        "IndustrialProcesses ChemicalManufacturing SyntheticOrganicFiber PolyestersStaple",
    "30102403":
        "IndustrialProcesses ChemicalManufacturing SyntheticOrganicFiber PolyesterYarn",
    "30102404":
        "IndustrialProcesses ChemicalManufacturing SyntheticOrganicFiber Nylon#6Yarn",
    "30102405":
        "IndustrialProcesses ChemicalManufacturing SyntheticOrganicFiber Polyfluorocarbonse.g.Teflon",
    "30102406":
        "IndustrialProcesses ChemicalManufacturing SyntheticOrganicFiber Nylon#66Controlled",
    "30102407":
        "IndustrialProcesses ChemicalManufacturing SyntheticOrganicFiber Nylon#66Uncontrolled",
    "30102409":
        "IndustrialProcesses ChemicalManufacturing SyntheticOrganicFiberManufacturing AcrylicControlled",
    "30102410":
        "IndustrialProcesses ChemicalManufacturing SyntheticOrganicFiberManufacturing AcrylicUncontrolled",
    "30102412":
        "IndustrialProcesses ChemicalManufacturing SyntheticOrganicFiberManufacturing AcrylicandModacrylicWetSpun",
    "30102414":
        "IndustrialProcesses ChemicalManufacturing SyntheticOrganicFiber PolyolefinMeltSpun",
    "30102416":
        "IndustrialProcesses ChemicalManufacturing SyntheticOrganicFiber Aramid",
    "30102417":
        "IndustrialProcesses ChemicalManufacturing SyntheticOrganicFiberManufacturing SpandexDrySpunUse649300XX",
    "30102421":
        "IndustrialProcesses ChemicalManufacturing SyntheticOrganicFiber DopePreparation",
    "30102422":
        "IndustrialProcesses ChemicalManufacturing SyntheticOrganicFiber Filtration",
    "30102423":
        "IndustrialProcesses ChemicalManufacturing SyntheticOrganicFiber FiberExtrusion",
    "30102424":
        "IndustrialProcesses ChemicalManufacturing SyntheticOrganicFiber WashingDryingFinishing",
    "30102425":
        "IndustrialProcesses ChemicalManufacturing SyntheticOrganicFiber FiberStorage",
    "30102426":
        "IndustrialProcesses ChemicalManufacturing SyntheticOrganicFiber EquipmentCleanup",
    "30102427":
        "IndustrialProcesses ChemicalManufacturing SyntheticOrganicFiber SolventStorage",
    "30102429":
        "IndustrialProcesses ChemicalManufacturing SyntheticOrganicFiber Mixing",
    "30102431":
        "IndustrialProcesses ChemicalManufacturing SyntheticOrganicFiber HeatTreatingFurnaceCarbonization",
    "30102432":
        "IndustrialProcesses ChemicalManufacturing SyntheticOrganicFiber CuringOvenCarbonization",
    "30102434":
        "IndustrialProcesses ChemicalManufacturing SyntheticOrganicFiber FiberLaminateProcess",
    "30102435":
        "IndustrialProcesses ChemicalManufacturing SyntheticOrganicFiber FiberHandlingandStorage",
    "30102436":
        "IndustrialProcesses ChemicalManufacturing SyntheticOrganicFiber AcrylicandModacrylicGeneral",
    "30102477":
        "IndustrialProcesses ChemicalManufacturing SyntheticOrganicFiber RayonGeneral",
    "30102479":
        "IndustrialProcesses ChemicalManufacturing SyntheticOrganicFiber RayonFilamentFormation",
    "30102499":
        "IndustrialProcesses ChemicalManufacturing SyntheticOrganicFiber OtherNotClassified",
    "30102501":
        "IndustrialProcesses ChemicalManufacturing CellulosicFiberProduction Viscosee.g.RayonUse649200XX",
    "30102505":
        "IndustrialProcesses ChemicalManufacturing CellulosicFiberProduction CelluloseAcetateFilerTow",
    "30102599":
        "IndustrialProcesses ChemicalManufacturing CellulosicFiberProduction OtherNotClassified",
    "30102601":
        "IndustrialProcesses ChemicalManufacturing SyntheticRubberManufacturingOnly General",
    "30102602":
        "IndustrialProcesses ChemicalManufacturing SyntheticRubberManufacturingOnly ButylIsobutylene",
    "30102608":
        "IndustrialProcesses ChemicalManufacturing SyntheticRubberManufacturingOnly Acrylonitrile",
    "30102609":
        "IndustrialProcesses ChemicalManufacturing SyntheticRubberManufacturingOnly Dryers",
    "30102610":
        "IndustrialProcesses ChemicalManufacturing SyntheticRubberManufacturingOnly BlowdownTank",
    "30102611":
        "IndustrialProcesses ChemicalManufacturing SyntheticRubberManufacturingOnly SteamStripper",
    "30102612":
        "IndustrialProcesses ChemicalManufacturing SyntheticRubberManufacturingOnly PrestorageTank",
    "30102613":
        "IndustrialProcesses ChemicalManufacturing SyntheticRubberManufacturingOnly MonomerRecoveryAbsorberVent",
    "30102614":
        "IndustrialProcesses ChemicalManufacturing SyntheticRubberManufacturingOnly BlendingTanks",
    "30102616":
        "IndustrialProcesses ChemicalManufacturing SyntheticRubberManufacturingOnly LatexMonomerRemoval",
    "30102617":
        "IndustrialProcesses ChemicalManufacturing SyntheticRubberManufacturingOnly LatexBlendingTank",
    "30102619":
        "IndustrialProcesses ChemicalManufacturing SyntheticRubberManufacturingOnly InhibitedMonomerStorage",
    "30102620":
        "IndustrialProcesses ChemicalManufacturing SyntheticRubberManufacturingOnly MonomerInhibitorRemoval",
    "30102621":
        "IndustrialProcesses ChemicalManufacturing SyntheticRubberManufacturingOnly EmulsionCrumbProcessPolymerization",
    "30102623":
        "IndustrialProcesses ChemicalManufacturing SyntheticRubberManufacturingOnly EmulsionCrumbProcessStyreneRecovery",
    "30102625":
        "IndustrialProcesses ChemicalManufacturing SyntheticRubberManufacturingOnly Chloroprene",
    "30102627":
        "IndustrialProcesses ChemicalManufacturing SyntheticRubberManufacturingOnly EmulsionCrumbProcessCrumbStorage",
    "30102630":
        "IndustrialProcesses ChemicalManufacturing SyntheticRubberManufacturingOnly SiliconeRubber",
    "30102641":
        "IndustrialProcesses ChemicalManufacturing SyntheticRubberManufacturingOnly EmulsionLatexProcessPolymerization",
    "30102644":
        "IndustrialProcesses ChemicalManufacturing SyntheticRubberManufacturingOnly EmulsionLatexProcessLatexPackaging",
    "30102645":
        "IndustrialProcesses ChemicalManufacturing SyntheticRubberManufacturingOnly EmulsionLatexProcessLatexLoading",
    "30102646":
        "IndustrialProcesses ChemicalManufacturing SyntheticRubberManufacturingOnly EmulsionLatexProcessLatexProductStorage",
    "30102650":
        "IndustrialProcesses ChemicalManufacturing SyntheticRubberManufacturingOnly FugitiveEmissionsMonomerUnloading",
    "30102651":
        "IndustrialProcesses ChemicalManufacturing SyntheticRubberManufacturingOnly FugitiveEmissionsSoapSolutionStorage",
    "30102652":
        "IndustrialProcesses ChemicalManufacturing SyntheticRubberManufacturingOnly FugitiveEmissionsActivatedCatalystStorage",
    "30102655":
        "IndustrialProcesses ChemicalManufacturing SyntheticRubberManufacturingOnly FugitiveEmissionsAntioxidantStorage",
    "30102656":
        "IndustrialProcesses ChemicalManufacturing SyntheticRubberManufacturingOnly FugitiveEmissionsCarbonBlackStorage",
    "30102660":
        "IndustrialProcesses ChemicalManufacturing SyntheticRubberManufacturingOnly Wastewater",
    "30102665":
        "IndustrialProcesses ChemicalManufacturing SyntheticRubberManufacturingOnly StorageVessels",
    "30102670":
        "IndustrialProcesses ChemicalManufacturing SyntheticRubberManufacturingOnly ContinuousReactorsandOtherUnitsuptoandincludingtheStripper",
    "30102690":
        "IndustrialProcesses ChemicalManufacturing SyntheticRubberManufacturingOnly CoolingTowers",
    "30102699":
        "IndustrialProcesses ChemicalManufacturing SyntheticRubberManufacturingOnly OtherNotClassified",
    "30102701":
        "IndustrialProcesses ChemicalManufacturing AmmoniumNitrateProduction PrillingTowerNeutralizer",
    "30102704":
        "IndustrialProcesses ChemicalManufacturing AmmoniumNitrateProduction Neutralizer",
    "30102705":
        "IndustrialProcesses ChemicalManufacturing AmmoniumNitrateProduction Granulator",
    "30102706":
        "IndustrialProcesses ChemicalManufacturing AmmoniumNitrateProduction DryersandCoolers",
    "30102707":
        "IndustrialProcesses ChemicalManufacturing AmmoniumNitrateProduction RotaryDrumGranulator",
    "30102708":
        "IndustrialProcesses ChemicalManufacturing AmmoniumNitrateProduction PanGranulator",
    "30102709":
        "IndustrialProcesses ChemicalManufacturing AmmoniumNitrateProduction BulkLoadingGeneral",
    "30102710":
        "IndustrialProcesses ChemicalManufacturing AmmoniumNitrateProduction BaggingofProduct",
    "30102711":
        "IndustrialProcesses ChemicalManufacturing AmmoniumNitrateProduction NeutralizerHighDensity",
    "30102712":
        "IndustrialProcesses ChemicalManufacturing AmmoniumNitrateProduction PrillingTowerHighDensity",
    "30102713":
        "IndustrialProcesses ChemicalManufacturing AmmoniumNitrateProduction HighDensityDryersandCoolersscb",
    "30102714":
        "IndustrialProcesses ChemicalManufacturing AmmoniumNitrateProduction PrillingCoolerHighDensity",
    "30102717":
        "IndustrialProcesses ChemicalManufacturing AmmoniumNitrateProduction EvaporatorConcentratorHighDensity",
    "30102718":
        "IndustrialProcesses ChemicalManufacturing AmmoniumNitrateProduction CoatingHighDensity",
    "30102720":
        "IndustrialProcesses ChemicalManufacturing AmmoniumNitrateProduction SolidsScreening",
    "30102721":
        "IndustrialProcesses ChemicalManufacturing AmmoniumNitrateProduction NeutralizerLowDensity",
    "30102722":
        "IndustrialProcesses ChemicalManufacturing AmmoniumNitrateProduction PrillingTowerLowDensity",
    "30102723":
        "IndustrialProcesses ChemicalManufacturing AmmoniumNitrateProduction LowDensityDryersandCoolersscb",
    "30102724":
        "IndustrialProcesses ChemicalManufacturing AmmoniumNitrateProduction PrillingCoolerLowDensity",
    "30102725":
        "IndustrialProcesses ChemicalManufacturing AmmoniumNitrateProduction PrillingDryerLowDensity",
    "30102727":
        "IndustrialProcesses ChemicalManufacturing AmmoniumNitrateProduction EvaporatorConcentratorLowDensity",
    "30102728":
        "IndustrialProcesses ChemicalManufacturing AmmoniumNitrateProduction CoatingLowDensity",
    "30102801":
        "IndustrialProcesses ChemicalManufacturing NormalSuperphosphates Grinding",
    "30102805":
        "IndustrialProcesses ChemicalManufacturing NormalSuperphosphates MixerDen",
    "30102807":
        "IndustrialProcesses ChemicalManufacturing NormalSuperphosphates BaggingHandling",
    "30102820":
        "IndustrialProcesses ChemicalManufacturing NormalSuperphosphates Mixing",
    "30102821":
        "IndustrialProcesses ChemicalManufacturing NormalSuperphosphates Den",
    "30102822":
        "IndustrialProcesses ChemicalManufacturing NormalSuperphosphates Curing",
    "30102823":
        "IndustrialProcesses ChemicalManufacturing NormalSuperphosphates AmmoniatorGranulator",
    "30102903":
        "IndustrialProcesses ChemicalManufacturing TripleSuperphosphate RockUnloading",
    "30102904":
        "IndustrialProcesses ChemicalManufacturing TripleSuperphosphate RockFeederSystem",
    "30102906":
        "IndustrialProcesses ChemicalManufacturing TripleSuperphosphate GranulatorReactorDryer",
    "30102908":
        "IndustrialProcesses ChemicalManufacturing TripleSuperphosphate BaggingHandling",
    "30102910":
        "IndustrialProcesses ChemicalManufacturing TripleSuperphosphate CrushingandScreening",
    "30102920":
        "IndustrialProcesses ChemicalManufacturing TripleSuperphosphate Mixing",
    "30102923":
        "IndustrialProcesses ChemicalManufacturing TripleSuperphosphate AmmoniatorGranulator",
    "30102924":
        "IndustrialProcesses ChemicalManufacturing TripleSuperphosphate Dryer",
    "30102925":
        "IndustrialProcesses ChemicalManufacturing TripleSuperphosphate Cooler",
    "30103000":
        "IndustrialProcesses ChemicalManufacturing AmmoniumPhosphates EntirePlant",
    "30103001":
        "IndustrialProcesses ChemicalManufacturing AmmoniumPhosphates DryersandCoolers",
    "30103002":
        "IndustrialProcesses ChemicalManufacturing AmmoniumPhosphates AmmoniatorGranulator",
    "30103003":
        "IndustrialProcesses ChemicalManufacturing AmmoniumPhosphates Screening",
    "30103004":
        "IndustrialProcesses ChemicalManufacturing AmmoniumPhosphates BaggingHandling",
    "30103020":
        "IndustrialProcesses ChemicalManufacturing AmmoniumPhosphates Mixing",
    "30103024":
        "IndustrialProcesses ChemicalManufacturing AmmoniumPhosphates Dryer",
    "30103025":
        "IndustrialProcesses ChemicalManufacturing AmmoniumPhosphates Cooler",
    "30103099":
        "IndustrialProcesses ChemicalManufacturing AmmoniumPhosphates OtherNotClassified",
    "30103101":
        "IndustrialProcesses ChemicalManufacturing TerephthalicAcidDimethylTerephthalate HNO3ParaxyleneGeneral",
    "30103102":
        "IndustrialProcesses ChemicalManufacturing TerephthalicAcidDimethylTerephthalate ReactorVent",
    "30103103":
        "IndustrialProcesses ChemicalManufacturing TerephthalicAcidDimethylTerephthalate CrystallizationSeparationandDryingVent",
    "30103104":
        "IndustrialProcesses ChemicalManufacturing TerephthalicAcidDimethylTerephthalate DistillationandRecoveryVent",
    "30103105":
        "IndustrialProcesses ChemicalManufacturing TerephthalicAcidDimethylTerephthalate ProductTransferVent",
    "30103106":
        "IndustrialProcesses ChemicalManufacturing TerephthalicAcidDimethylTerephthalate GasLiquidSeparator",
    "30103107":
        "IndustrialProcesses ChemicalManufacturing TerephthalicAcidDimethylTerephthalate HighPressureAbsorber",
    "30103108":
        "IndustrialProcesses ChemicalManufacturing TerephthalicAcidDimethylTerephthalate SolidLiquidSeparator",
    "30103109":
        "IndustrialProcesses ChemicalManufacturing TerephthalicAcidDimethylTerephthalate ResidueStill",
    "30103110":
        "IndustrialProcesses ChemicalManufacturing TerephthalicAcidDimethylTerephthalate CTPAPurification",
    "30103180":
        "IndustrialProcesses ChemicalManufacturing TerephthalicAcidDimethylTerephthalate FugitiveEmissions",
    "30103199":
        "IndustrialProcesses ChemicalManufacturing TerephthalicAcidDimethylTerephthalate OtherNotClassified",
    "30103201":
        "IndustrialProcesses ChemicalManufacturing ElementalSulfurProduction Mod.Claus2StagewoControl9295%Removal",
    "30103202":
        "IndustrialProcesses ChemicalManufacturing ElementalSulfurProduction Mod.Claus3StagewoControl9596%Removal",
    "30103203":
        "IndustrialProcesses ChemicalManufacturing ElementalSulfurProduction Mod.Claus4StagewoControl9697%Removal",
    "30103204":
        "IndustrialProcesses ChemicalManufacturing ElementalSulfurProduction SulfurRemovalProcess99.9%Removal",
    "30103205":
        "IndustrialProcesses ChemicalManufacturing ElementalSulfurProduction SulfurStorage",
    "30103299":
        "IndustrialProcesses ChemicalManufacturing ElementalSulfurProduction OtherNotClassified",
    "30103301":
        "IndustrialProcesses ChemicalManufacturing Pesticides Malathion",
    "30103311":
        "IndustrialProcesses ChemicalManufacturing Pesticides General",
    "30103320":
        "IndustrialProcesses ChemicalManufacturing Pesticides Reactor",
    "30103326":
        "IndustrialProcesses ChemicalManufacturing Pesticides Condenser",
    "30103328":
        "IndustrialProcesses ChemicalManufacturing Pesticides ProductDryer",
    "30103330":
        "IndustrialProcesses ChemicalManufacturing Pesticides ProcessTank",
    "30103331":
        "IndustrialProcesses ChemicalManufacturing Pesticides StorageVessels",
    "30103340":
        "IndustrialProcesses ChemicalManufacturing Pesticides Formulation",
    "30103341":
        "IndustrialProcesses ChemicalManufacturing Pesticides ProductPackaging",
    "30103343":
        "IndustrialProcesses ChemicalManufacturing Pesticides Blending",
    "30103399":
        "IndustrialProcesses ChemicalManufacturing Pesticides OtherNotElsewhereClassified",
    "30103402":
        "IndustrialProcesses ChemicalManufacturing AnilineEthanolamines GeneralAniline",
    "30103403":
        "IndustrialProcesses ChemicalManufacturing AnilineEthanolamines ReactorCyclePurgeVent",
    "30103404":
        "IndustrialProcesses ChemicalManufacturing AnilineEthanolamines DehydrationColumnVent",
    "30103405":
        "IndustrialProcesses ChemicalManufacturing AnilineEthanolamines PurificationColumnVent",
    "30103406":
        "IndustrialProcesses ChemicalManufacturing AnilineEthanolamines FugitiveEmissions",
    "30103410":
        "IndustrialProcesses ChemicalManufacturing AnilineEthanolamines GeneralEthanolamines",
    "30103411":
        "IndustrialProcesses ChemicalManufacturing AnilineEthanolamines AmmoniaScrubberVent",
    "30103412":
        "IndustrialProcesses ChemicalManufacturing AnilineEthanolamines VacuumDistillationJetVent",
    "30103415":
        "IndustrialProcesses ChemicalManufacturing AnilineEthanolamines Ethylenediamine",
    "30103420":
        "IndustrialProcesses ChemicalManufacturing AnilineEthanolamines Hexamethylenediamine",
    "30103435":
        "IndustrialProcesses ChemicalManufacturing AnilineEthanolamines Methylamines",
    "30103499":
        "IndustrialProcesses ChemicalManufacturing AnilineEthanolamines OtherNotElsewhereClassified",
    "30103501":
        "IndustrialProcesses ChemicalManufacturing InorganicPigments TiO2SulfateProcessCalciner",
    "30103503":
        "IndustrialProcesses ChemicalManufacturing InorganicPigments TiO2ChlorideProcessReactor",
    "30103506":
        "IndustrialProcesses ChemicalManufacturing InorganicPigments LeadOxideBartonPot",
    "30103550":
        "IndustrialProcesses ChemicalManufacturing InorganicPigments OreGrinding",
    "30103551":
        "IndustrialProcesses ChemicalManufacturing InorganicPigments OreDryer",
    "30103552":
        "IndustrialProcesses ChemicalManufacturing InorganicPigments PigmentMilling",
    "30103553":
        "IndustrialProcesses ChemicalManufacturing InorganicPigments PigmentDryer",
    "30103554":
        "IndustrialProcesses ChemicalManufacturing InorganicPigments ConveyingStoragePacking",
    "30103599":
        "IndustrialProcesses ChemicalManufacturing InorganicPigments OtherNotClassified",
    "30103601":
        "IndustrialProcesses ChemicalManufacturing ChromicAcidManufacturing ChromateOreHandlingGrinding&Drying",
    "30103602":
        "IndustrialProcesses ChemicalManufacturing ChromicAcidManufacturing BichromateKilns",
    "30103603":
        "IndustrialProcesses ChemicalManufacturing ChromicAcidManufacturing KilnProductQuenchTanks",
    "30103605":
        "IndustrialProcesses ChemicalManufacturing ChromicAcidManufacturing KilnProductEvaporators",
    "30103606":
        "IndustrialProcesses ChemicalManufacturing ChromicAcidManufacturing SaltCakeFlashDryer",
    "30103607":
        "IndustrialProcesses ChemicalManufacturing ChromicAcidManufacturing SaltCakeBulkLoading&ConveyorTransport",
    "30103608":
        "IndustrialProcesses ChemicalManufacturing ChromicAcidManufacturing CrystalSeparationDrying&StorageSystem",
    "30103609":
        "IndustrialProcesses ChemicalManufacturing ChromicAcidManufacturing ChromeAcidProcessingTanks",
    "30103699":
        "IndustrialProcesses ChemicalManufacturing ChromicAcidManufacturing MiscellaneousProcesses",
    "30103801":
        "IndustrialProcesses ChemicalManufacturing SodiumBicarbonate General",
    "30103901":
        "IndustrialProcesses ChemicalManufacturing HydrogenCyanide AirHeaterGeneral",
    "30103902":
        "IndustrialProcesses ChemicalManufacturing HydrogenCyanide AmmoniaAbsorber",
    "30103903":
        "IndustrialProcesses ChemicalManufacturing HydrogenCyanide HCNAbsorber",
    "30104001":
        "IndustrialProcesses ChemicalManufacturing UreaProduction GeneralSpecifyinComments",
    "30104002":
        "IndustrialProcesses ChemicalManufacturing UreaProduction SolutionConcentrationControlled",
    "30104003":
        "IndustrialProcesses ChemicalManufacturing UreaProduction Prilling",
    "30104004":
        "IndustrialProcesses ChemicalManufacturing UreaProduction DrumGranulation",
    "30104005":
        "IndustrialProcesses ChemicalManufacturing UreaProduction Coating",
    "30104006":
        "IndustrialProcesses ChemicalManufacturing UreaProduction Bagging",
    "30104007":
        "IndustrialProcesses ChemicalManufacturing UreaProduction BulkLoading",
    "30104010":
        "IndustrialProcesses ChemicalManufacturing UreaProduction FluidizedBedPrillingAgriculturalGrade",
    "30104012":
        "IndustrialProcesses ChemicalManufacturing UreaProduction RotaryDrumCooler",
    "30104013":
        "IndustrialProcesses ChemicalManufacturing UreaProduction SolidsScreening",
    "30104014":
        "IndustrialProcesses ChemicalManufacturing UreaProduction PanGranulation",
    "30104020":
        "IndustrialProcesses ChemicalManufacturing UreaProduction SolutionSynthesis",
    "30104101":
        "IndustrialProcesses ChemicalManufacturing Nitrocellulose NitrationReactor",
    "30104162":
        "IndustrialProcesses ChemicalManufacturing Nitrocellulose ContinuousProcessSpentAcidRecoverySulfuricAcidRegenerator",
    "30104172":
        "IndustrialProcesses ChemicalManufacturing Nitrocellulose ContinuousProcessNitricAcidConcentrationBleacher",
    "30104202":
        "IndustrialProcesses ChemicalManufacturing LeadAlkylManufacturingSodiumLeadAlloyProcess ProcessVentsTetraethylLead",
    "30104301":
        "IndustrialProcesses ChemicalManufacturing LeadAlkylManufacturingElectrolyticProcess General",
    "30104501":
        "IndustrialProcesses ChemicalManufacturing OrganicFertilizer GeneralMixingHandling",
    "30105001":
        "IndustrialProcesses ChemicalManufacturing Adhesives GeneralCompoundUnknown",
    "30105105":
        "IndustrialProcesses ChemicalManufacturing AnimalAdhesives RawMaterialsGrinding",
    "30105112":
        "IndustrialProcesses ChemicalManufacturing AnimalAdhesives Washing",
    "30105114":
        "IndustrialProcesses ChemicalManufacturing AnimalAdhesives Cooking",
    "30105118":
        "IndustrialProcesses ChemicalManufacturing AnimalAdhesives FilteringCentrifuging",
    "30105120":
        "IndustrialProcesses ChemicalManufacturing AnimalAdhesives Evaporation",
    "30105124":
        "IndustrialProcesses ChemicalManufacturing AnimalAdhesives Drying",
    "30105130":
        "IndustrialProcesses ChemicalManufacturing AnimalAdhesives EndProductFinishing",
    "30105240":
        "IndustrialProcesses ChemicalManufacturing Casein GrindingPackagingandStoring",
    "30105719":
        "IndustrialProcesses ChemicalManufacturing PolybutadieneRubberProduction General",
    "30105900":
        "IndustrialProcesses ChemicalManufacturing StyreneButadieneRubberandLatexProduction RawMaterialStorage",
    "30105910":
        "IndustrialProcesses ChemicalManufacturing StyreneButadieneRubberandLatexProduction ProductDryer",
    "30105911":
        "IndustrialProcesses ChemicalManufacturing StyreneButadieneRubberandLatexProduction Wastewater",
    "30105912":
        "IndustrialProcesses ChemicalManufacturing StyreneButadieneRubberandLatexProduction EquipmentLeaks[Seealso3010591314or15]",
    "30105916":
        "IndustrialProcesses ChemicalManufacturing StyreneButadieneRubberandLatexProduction BlowdownTank",
    "30106001":
        "IndustrialProcesses ChemicalManufacturing PharmaceuticalProduction VacuumDryer",
    "30106002":
        "IndustrialProcesses ChemicalManufacturing PharmaceuticalProduction Reactor",
    "30106003":
        "IndustrialProcesses ChemicalManufacturing PharmaceuticalProduction DistillationUnit",
    "30106004":
        "IndustrialProcesses ChemicalManufacturing PharmaceuticalProduction Filtration",
    "30106005":
        "IndustrialProcesses ChemicalManufacturing PharmaceuticalProduction Extractor",
    "30106006":
        "IndustrialProcesses ChemicalManufacturing PharmaceuticalProduction Centrifuge",
    "30106007":
        "IndustrialProcesses ChemicalManufacturing PharmaceuticalProduction Crystallization",
    "30106008":
        "IndustrialProcesses ChemicalManufacturing PharmaceuticalProduction ExhaustSystem",
    "30106009":
        "IndustrialProcesses ChemicalManufacturing PharmaceuticalProduction AirDryer",
    "30106010":
        "IndustrialProcesses ChemicalManufacturing PharmaceuticalProduction StorageVessel",
    "30106011":
        "IndustrialProcesses ChemicalManufacturing PharmaceuticalProduction CoatingProcess",
    "30106012":
        "IndustrialProcesses ChemicalManufacturing PharmaceuticalProduction GranulationProcess",
    "30106013":
        "IndustrialProcesses ChemicalManufacturing PharmaceuticalProduction FermentationTank",
    "30106014":
        "IndustrialProcesses ChemicalManufacturing PharmaceuticalProduction BlendingMixing",
    "30106015":
        "IndustrialProcesses ChemicalManufacturing PharmaceuticalProduction TabletPressing",
    "30106016":
        "IndustrialProcesses ChemicalManufacturing PharmaceuticalProduction CapsuleFilling",
    "30106017":
        "IndustrialProcesses ChemicalManufacturing PharmaceuticalProduction ProductPackaging",
    "30106018":
        "IndustrialProcesses ChemicalManufacturing PharmaceuticalProduction MaterialTransfer",
    "30106019":
        "IndustrialProcesses ChemicalManufacturing PharmaceuticalProduction RegenerationofSpentAdsorbent",
    "30106021":
        "IndustrialProcesses ChemicalManufacturing PharmaceuticalProduction RawMaterialUnloading",
    "30106022":
        "IndustrialProcesses ChemicalManufacturing PharmaceuticalProduction MiscellaneousFugitives",
    "30106023":
        "IndustrialProcesses ChemicalManufacturing PharmaceuticalProduction FugitiveEmissions",
    "30106026":
        "IndustrialProcesses ChemicalManufacturing PharmaceuticalProduction WastewaterTreatment",
    "30106033":
        "IndustrialProcesses ChemicalManufacturing PharmaceuticalProduction ProductDryer",
    "30106035":
        "IndustrialProcesses ChemicalManufacturing PharmaceuticalProduction ProcessTank",
    "30106036":
        "IndustrialProcesses ChemicalManufacturing PharmaceuticalProduction Formulation",
    "30106099":
        "IndustrialProcesses ChemicalManufacturing PharmaceuticalProduction OtherNotClassified",
    "30106201":
        "IndustrialProcesses ChemicalManufacturing AcrylonitrileButadieneStyreneResinProduction General",
    "30106501":
        "IndustrialProcesses ChemicalManufacturing PolystyreneResinProduction General",
    "30106508":
        "IndustrialProcesses ChemicalManufacturing PolystyreneResinProduction Blending",
    "30106515":
        "IndustrialProcesses ChemicalManufacturing PolystyreneResinProduction ProcessTank",
    "30106701":
        "IndustrialProcesses ChemicalManufacturing MaleicAnhydrideCopolymersProduction PolymerizationBulkProcess",
    "30106703":
        "IndustrialProcesses ChemicalManufacturing MaleicAnhydrideCopolymersProduction PolymerizationEmulsionProcess",
    "30106802":
        "IndustrialProcesses ChemicalManufacturing AlkydResinProduction ReactorSolventProcess",
    "30106803":
        "IndustrialProcesses ChemicalManufacturing AlkydResinProduction ReactorFusionProcess",
    "30106806":
        "IndustrialProcesses ChemicalManufacturing AlkydResinProduction SolventRecovery",
    "30106807":
        "IndustrialProcesses ChemicalManufacturing AlkydResinProduction ProductFinishing",
    "30106808":
        "IndustrialProcesses ChemicalManufacturing AlkydResinProduction ProductStorage",
    "30106809":
        "IndustrialProcesses ChemicalManufacturing AlkydResinProduction TransferOperations",
    "30107001":
        "IndustrialProcesses ChemicalManufacturing InorganicChemicalManufacturingGeneral FugitiveLeaks",
    "30107002":
        "IndustrialProcesses ChemicalManufacturing InorganicChemicalManufacturingGeneral StorageTransfer",
    "30107101":
        "IndustrialProcesses ChemicalManufacturing Hydrogen Reformer",
    "30107102":
        "IndustrialProcesses ChemicalManufacturing Hydrogen COConverter",
    "30107103":
        "IndustrialProcesses ChemicalManufacturing Hydrogen HydrogenStorage",
    "30107405":
        "IndustrialProcesses ChemicalManufacturing AcetalResins ProcessVent",
    "30107406":
        "IndustrialProcesses ChemicalManufacturing AcetalResins Condenser",
    "30107501":
        "IndustrialProcesses ChemicalManufacturing AminoPhenolicResinProduction General",
    "30107502":
        "IndustrialProcesses ChemicalManufacturing AminoPhenolicResinProduction Reactor",
    "30107608":
        "IndustrialProcesses ChemicalManufacturing PolycarbonateProduction ProcessTank",
    "30107701":
        "IndustrialProcesses ChemicalManufacturing PolyvinylChlorideandCopolymersProduction General",
    "30107702":
        "IndustrialProcesses ChemicalManufacturing PolyvinylChlorideandCopolymersProduction PolymerizationReactorSuspensionProcess",
    "30107703":
        "IndustrialProcesses ChemicalManufacturing PolyvinylChlorideandCopolymersProduction PolymerizationReactorDispersionProcess",
    "30107705":
        "IndustrialProcesses ChemicalManufacturing PolyvinylChlorideandCopolymersProduction PolymerizationReactorBulkProcess",
    "30107706":
        "IndustrialProcesses ChemicalManufacturing PolyvinylChlorideandCopolymersProduction ResinStripper",
    "30107708":
        "IndustrialProcesses ChemicalManufacturing PolyvinylChlorideandCopolymersProduction ProcessTank",
    "30107710":
        "IndustrialProcesses ChemicalManufacturing PolyvinylChlorideandCopolymersProduction MaterialRecovery",
    "30107711":
        "IndustrialProcesses ChemicalManufacturing PolyvinylChlorideandCopolymersProduction Centrifuge",
    "30107716":
        "IndustrialProcesses ChemicalManufacturing PolyvinylChlorideandCopolymersProduction FilterSieve",
    "30107720":
        "IndustrialProcesses ChemicalManufacturing PolyvinylChlorideandCopolymersProduction Dryer",
    "30107722":
        "IndustrialProcesses ChemicalManufacturing PolyvinylChlorideandCopolymersProduction BaggingOperations",
    "30107724":
        "IndustrialProcesses ChemicalManufacturing PolyvinylChlorideandCopolymersProduction FeedIntermediateProductStorage",
    "30107725":
        "IndustrialProcesses ChemicalManufacturing PolyvinylChlorideandCopolymersProduction ProductLoading",
    "30107727":
        "IndustrialProcesses ChemicalManufacturing PolyvinylChlorideandCopolymersProduction FugitiveEmissionsOpeningofEquipmentforInspectionorMaintenance",
    "30107801":
        "IndustrialProcesses ChemicalManufacturing EpoxyResinProduction General",
    "30107901":
        "IndustrialProcesses ChemicalManufacturing NonnylonPolyamideProduction General",
    "30108001":
        "IndustrialProcesses ChemicalManufacturing PolypropyleneProduction General",
    "30108101":
        "IndustrialProcesses ChemicalManufacturing PolyethyleneProduction LowDensityGeneral",
    "30108104":
        "IndustrialProcesses ChemicalManufacturing PolyethyleneProduction LowDensityMaterialRecovery",
    "30108105":
        "IndustrialProcesses ChemicalManufacturing PolyethyleneProduction LowDensityProductFinishing",
    "30108110":
        "IndustrialProcesses ChemicalManufacturing PolyethyleneProduction HighDensityGeneral",
    "30108201":
        "IndustrialProcesses ChemicalManufacturing PolymethylMethacrylateProduction BulkPolymerizationBatchcellMethodGeneral",
    "30108202":
        "IndustrialProcesses ChemicalManufacturing PolymethylMethacrylateProduction BulkPolymerizationBatchcellMethodReactor",
    "30108209":
        "IndustrialProcesses ChemicalManufacturing PolymethylMethacrylateProduction BulkPolymerizationContinuousCastingGeneral",
    "30108226":
        "IndustrialProcesses ChemicalManufacturing PolymethylMethacrylateProduction SolutionPolymerizationGeneral",
    "30108229":
        "IndustrialProcesses ChemicalManufacturing PolymethylMethacrylateProduction SolutionPolymerizationDryer",
    "30108236":
        "IndustrialProcesses ChemicalManufacturing PolymethylMethacrylateProduction EmulsionPolymerizationGeneral",
    "30108240":
        "IndustrialProcesses ChemicalManufacturing PolymethylMethacrylateProduction EmulsionPolymerizationProductStorage",
    "30108301":
        "IndustrialProcesses ChemicalManufacturing CellophaneManufacturing OtherNotElsewhereClassified",
    "30108310":
        "IndustrialProcesses ChemicalManufacturing CellophaneManufacturing CellophaneFormation",
    "30108320":
        "IndustrialProcesses ChemicalManufacturing CellophaneManufacturing CoatingOperations",
    "30108401":
        "IndustrialProcesses ChemicalManufacturing CelluloseEthersProduction OtherNotElsewhereClassified",
    "30108402":
        "IndustrialProcesses ChemicalManufacturing CelluloseEthersProduction Reactor",
    "30108405":
        "IndustrialProcesses ChemicalManufacturing CelluloseEthersProduction Neutralization",
    "30108410":
        "IndustrialProcesses ChemicalManufacturing CelluloseEthersProduction ProductFinishing",
    "30108411":
        "IndustrialProcesses ChemicalManufacturing CelluloseEthersProduction ProductStorage",
    "30108801":
        "IndustrialProcesses ChemicalManufacturing PolymerizedVinylideneChlorideProduction OtherNotElsewhereClassified",
    "30108802":
        "IndustrialProcesses ChemicalManufacturing PolymerizedVinylideneChlorideProduction PolymerizationReactorEmulsionProcess",
    "30108803":
        "IndustrialProcesses ChemicalManufacturing PolymerizedVinylideneChlorideProduction PolymerizationReactorSuspensionProcess",
    "30108805":
        "IndustrialProcesses ChemicalManufacturing PolymerizedVinylideneChlorideProduction RawMaterialStorage",
    "30108806":
        "IndustrialProcesses ChemicalManufacturing PolymerizedVinylideneChlorideProduction RawMaterialTransfer",
    "30108807":
        "IndustrialProcesses ChemicalManufacturing PolymerizedVinylideneChlorideProduction IntermediateProductStorage",
    "30108810":
        "IndustrialProcesses ChemicalManufacturing PolymerizedVinylideneChlorideProduction Dryer",
    "30108812":
        "IndustrialProcesses ChemicalManufacturing PolymerizedVinylideneChlorideProduction ProductFinishing",
    "30108902":
        "IndustrialProcesses ChemicalManufacturing PolyvinylAcetateEmulsionsProduction PolymerizationReactorEmulsionProcess",
    "30109005":
        "IndustrialProcesses ChemicalManufacturing PolyvinylAlcoholProduction IntermediateProductStorage",
    "30109011":
        "IndustrialProcesses ChemicalManufacturing PolyvinylAlcoholProduction ProductFinishing",
    "30109101":
        "IndustrialProcesses ChemicalManufacturing AcetoneKetoneProduction AcetoneGeneral",
    "30109105":
        "IndustrialProcesses ChemicalManufacturing AcetoneKetoneProduction MethylEthylKetone",
    "30109110":
        "IndustrialProcesses ChemicalManufacturing AcetoneKetoneProduction MethylIsobutylKetone",
    "30109151":
        "IndustrialProcesses ChemicalManufacturing AcetoneKetoneProduction AcetoneCumeneOxidation",
    "30109152":
        "IndustrialProcesses ChemicalManufacturing AcetoneKetoneProduction AcetoneCHPConcentrator",
    "30109153":
        "IndustrialProcesses ChemicalManufacturing AcetoneKetoneProduction AcetoneLightendsDistillationVent",
    "30109180":
        "IndustrialProcesses ChemicalManufacturing AcetoneKetoneProduction AcetoneFugitiveEmissions",
    "30109199":
        "IndustrialProcesses ChemicalManufacturing AcetoneKetoneProduction KetoneOtherNotClassified",
    "30110002":
        "IndustrialProcesses ChemicalManufacturing MaleicAnhydride ProductRecoveryAbsorber",
    "30110003":
        "IndustrialProcesses ChemicalManufacturing MaleicAnhydride VacuumSystemVent",
    "30110080":
        "IndustrialProcesses ChemicalManufacturing MaleicAnhydride FugitiveEmissions",
    "30110099":
        "IndustrialProcesses ChemicalManufacturing MaleicAnhydride OtherNotClassified",
    "30111199":
        "IndustrialProcesses ChemicalManufacturing AsbestosChemical NotClassified",
    "30111201":
        "IndustrialProcesses ChemicalManufacturing ElementalPhosphorous Calciner",
    "30111202":
        "IndustrialProcesses ChemicalManufacturing ElementalPhosphorous Furnace",
    "30111299":
        "IndustrialProcesses ChemicalManufacturing ElementalPhosphorous OtherNotClassified",
    "30111301":
        "IndustrialProcesses ChemicalManufacturing BoricAcid Dryer",
    "30111401":
        "IndustrialProcesses ChemicalManufacturing PotassiumChloride Dryer",
    "30111506":
        "IndustrialProcesses ChemicalManufacturing AluminumSulfateManufacturing Cooker",
    "30111507":
        "IndustrialProcesses ChemicalManufacturing AluminumSulfateManufacturing AlumsStorage",
    "30111508":
        "IndustrialProcesses ChemicalManufacturing AluminumSulfateManufacturing H2SO4ProcessTank",
    "30112001":
        "IndustrialProcesses ChemicalManufacturing FormaldahydeAcroleinAcetaldehydeButyraldehyde FormaldehydeSilverCatalyst",
    "30112002":
        "IndustrialProcesses ChemicalManufacturing FormaldahydeAcroleinAcetaldehydeButyraldehyde FormaldehydeMixedOxideCatalyst",
    "30112005":
        "IndustrialProcesses ChemicalManufacturing FormaldahydeAcroleinAcetaldehydeButyraldehyde FormaldehydeAbsorberVent",
    "30112006":
        "IndustrialProcesses ChemicalManufacturing FormaldahydeAcroleinAcetaldehydeButyraldehyde FormaldehydeFractionatorVent",
    "30112007":
        "IndustrialProcesses ChemicalManufacturing FormaldahydeAcroleinAcetaldehydeButyraldehyde FormaldehydeFugitiveEmissions",
    "30112011":
        "IndustrialProcesses ChemicalManufacturing FormaldahydeAcroleinAcetaldehydeButyraldehyde AcetaldehydefromEthylene",
    "30112012":
        "IndustrialProcesses ChemicalManufacturing FormaldahydeAcroleinAcetaldehydeButyraldehyde AcetaldehydefromEthanol",
    "30112017":
        "IndustrialProcesses ChemicalManufacturing FormaldahydeAcroleinAcetaldehydeButyraldehyde AcetaldehydeFugitiveEmissions",
    "30112021":
        "IndustrialProcesses ChemicalManufacturing FormaldahydeAcroleinAcetaldehydeButyraldehyde ButyraldehydeGeneral",
    "30112031":
        "IndustrialProcesses ChemicalManufacturing FormaldahydeAcroleinAcetaldehydeButyraldehyde AcroleinCO2StrippingTower",
    "30112037":
        "IndustrialProcesses ChemicalManufacturing FormaldahydeAcroleinAcetaldehydeButyraldehyde AcroleinFugitiveEmissions",
    "30112099":
        "IndustrialProcesses ChemicalManufacturing FormaldahydeAcroleinAcetaldehydeButyraldehyde AcroleinOtherNotClassified",
    "30112199":
        "IndustrialProcesses ChemicalManufacturing OrganicDyesPigments OtherNotClassified",
    "30112480":
        "IndustrialProcesses ChemicalManufacturing Chloroprene FugitiveEmissions",
    "30112501":
        "IndustrialProcesses ChemicalManufacturing ChlorineDerivatives EthyleneDichlorideviaOxychlorination",
    "30112502":
        "IndustrialProcesses ChemicalManufacturing ChlorineDerivatives EthyleneDichlorideviaDirectChlorination",
    "30112504":
        "IndustrialProcesses ChemicalManufacturing ChlorineDerivatives EthyleneDichlorideCausticScrubber",
    "30112505":
        "IndustrialProcesses ChemicalManufacturing ChlorineDerivatives EthyleneDichlorideReactorVessel",
    "30112509":
        "IndustrialProcesses ChemicalManufacturing ChlorineDerivatives EthyleneDichlorideFugitiveEmissions",
    "30112510":
        "IndustrialProcesses ChemicalManufacturing ChlorineDerivatives ChloromethanesGeneral",
    "30112512":
        "IndustrialProcesses ChemicalManufacturing ChlorineDerivatives ChloromethanesDryingBedRegenerationVent",
    "30112514":
        "IndustrialProcesses ChemicalManufacturing ChlorineDerivatives ChloromethanesFugitiveEmissions",
    "30112515":
        "IndustrialProcesses ChemicalManufacturing ChlorineDerivatives EthylChlorideGeneral",
    "30112520":
        "IndustrialProcesses ChemicalManufacturing ChlorineDerivatives PerchloroethyleneGeneral",
    "30112524":
        "IndustrialProcesses ChemicalManufacturing ChlorineDerivatives PerchloroethyleneFugitiveEmissions",
    "30112525":
        "IndustrialProcesses ChemicalManufacturing ChlorineDerivatives TrichloroethaneGeneral",
    "30112526":
        "IndustrialProcesses ChemicalManufacturing ChlorineDerivatives TrichloroethaneHClAbsorberVent",
    "30112528":
        "IndustrialProcesses ChemicalManufacturing ChlorineDerivatives TrichloroethaneDistillationColumnVent",
    "30112530":
        "IndustrialProcesses ChemicalManufacturing ChlorineDerivatives TrichloroethyleneGeneral",
    "30112531":
        "IndustrialProcesses ChemicalManufacturing ChlorineDerivatives TrichloroethyleneDistillationUnit",
    "30112533":
        "IndustrialProcesses ChemicalManufacturing ChlorineDerivatives TrichloroethyleneProductDryingColumn",
    "30112534":
        "IndustrialProcesses ChemicalManufacturing ChlorineDerivatives TrichloroethyleneFugitiveEmissions",
    "30112535":
        "IndustrialProcesses ChemicalManufacturing ChlorineDerivatives ChlorobenzenesGeneral",
    "30112540":
        "IndustrialProcesses ChemicalManufacturing ChlorineDerivatives VinylChlorideGeneral",
    "30112541":
        "IndustrialProcesses ChemicalManufacturing ChlorineDerivatives VinylChlorideCrackingFurnace",
    "30112542":
        "IndustrialProcesses ChemicalManufacturing ChlorineDerivatives VinylChlorideHClRecovery",
    "30112544":
        "IndustrialProcesses ChemicalManufacturing ChlorineDerivatives DichloroethaneDryingColumn",
    "30112547":
        "IndustrialProcesses ChemicalManufacturing ChlorineDerivatives VinylChlorideCrackingFurnaceDecoking",
    "30112550":
        "IndustrialProcesses ChemicalManufacturing ChlorineDerivatives VinylChlorideFugitiveEmissions",
    "30112551":
        "IndustrialProcesses ChemicalManufacturing ChlorineDerivatives VinylideneChlorideGeneral",
    "30112553":
        "IndustrialProcesses ChemicalManufacturing ChlorineDerivatives VinylideneChlorideDistillationColumnVent",
    "30112556":
        "IndustrialProcesses ChemicalManufacturing ChlorineDerivatives ChloromethanesviaMH&MCCProcessesInertgasPurgeVent",
    "30112557":
        "IndustrialProcesses ChemicalManufacturing ChlorineDerivatives ChloromethanesviaMH&MCCProcessesMethyleneChlorideCondenser",
    "30112558":
        "IndustrialProcesses ChemicalManufacturing ChlorineDerivatives ChloromethanesviaMH&MCCProcessesChloroformCondenser",
    "30112599":
        "IndustrialProcesses ChemicalManufacturing ChlorineDerivatives OtherNotClassified",
    "30112699":
        "IndustrialProcesses ChemicalManufacturing BrominatedOrganics BromineOrganics",
    "30112701":
        "IndustrialProcesses ChemicalManufacturing FluorocarbonsChlorofluorocarbons General",
    "30112702":
        "IndustrialProcesses ChemicalManufacturing FluorocarbonsChlorofluorocarbons DistillationColumn",
    "30112703":
        "IndustrialProcesses ChemicalManufacturing FluorocarbonsChlorofluorocarbons HClRecoveryColumn",
    "30112720":
        "IndustrialProcesses ChemicalManufacturing FluorocarbonsChlorofluorocarbons Chlorofluorocarbon1211",
    "30112730":
        "IndustrialProcesses ChemicalManufacturing FluorocarbonsChlorofluorocarbons Chlorofluorocarbon2322",
    "30112740":
        "IndustrialProcesses ChemicalManufacturing FluorocarbonsChlorofluorocarbons Chlorofluorocarbon113114",
    "30112780":
        "IndustrialProcesses ChemicalManufacturing FluorocarbonsChlorofluorocarbons FugitiveEmissions",
    "30112803":
        "IndustrialProcesses ChemicalManufacturing ChlorinatedParaffinsProduction ReactorConinuousProcess",
    "30113001":
        "IndustrialProcesses ChemicalManufacturing AmmoniumSulfateUse301210forCaprolactumProduction CaprolactumByproductPlants",
    "30113003":
        "IndustrialProcesses ChemicalManufacturing AmmoniumSulfateUse301210forCaprolactumProduction ProcessVents",
    "30113004":
        "IndustrialProcesses ChemicalManufacturing AmmoniumSulfate CaprolactamByproductRotaryDryer",
    "30113005":
        "IndustrialProcesses ChemicalManufacturing AmmoniumSulfate CaprolactamByproductFluidBedDryer",
    "30113006":
        "IndustrialProcesses ChemicalManufacturing AmmoniumSulfate CaprolactamByproductCrystallizerEvaporator",
    "30113007":
        "IndustrialProcesses ChemicalManufacturing AmmoniumSulfate CaprolactamByproductScreening",
    "30113099":
        "IndustrialProcesses ChemicalManufacturing AmmoniumSulfate General",
    "30113201":
        "IndustrialProcesses ChemicalManufacturing OrganicAcidManufacturing AceticAcidviaMethanol",
    "30113210":
        "IndustrialProcesses ChemicalManufacturing OrganicAcidManufacturing AceticAcidviaAcetaldehyde",
    "30113221":
        "IndustrialProcesses ChemicalManufacturing OrganicAcidManufacturing GeneralAcrylicAcid",
    "30113222":
        "IndustrialProcesses ChemicalManufacturing OrganicAcidManufacturing QuenchAbsorber",
    "30113223":
        "IndustrialProcesses ChemicalManufacturing OrganicAcidManufacturing ExtractionColumn",
    "30113224":
        "IndustrialProcesses ChemicalManufacturing OrganicAcidManufacturing VacuumSystem",
    "30113227":
        "IndustrialProcesses ChemicalManufacturing OrganicAcidManufacturing FugitiveEmissions",
    "30113299":
        "IndustrialProcesses ChemicalManufacturing OrganicAcidManufacturing OtherNotClassified",
    "30113301":
        "IndustrialProcesses ChemicalManufacturing AceticAnhydride General",
    "30113302":
        "IndustrialProcesses ChemicalManufacturing AceticAnhydride ReactorByproductGasVent",
    "30113303":
        "IndustrialProcesses ChemicalManufacturing AceticAnhydride DistillationColumnVent",
    "30113701":
        "IndustrialProcesses ChemicalManufacturing EstersProduction EthylAcrylate",
    "30113710":
        "IndustrialProcesses ChemicalManufacturing EstersProduction ButylAcrylate",
    "30113799":
        "IndustrialProcesses ChemicalManufacturing EstersProduction AcrylatesSpecifyinComments",
    "30114001":
        "IndustrialProcesses ChemicalManufacturing AcetyleneProducion RawMaterialHandling",
    "30114002":
        "IndustrialProcesses ChemicalManufacturing AcetyleneProducion GrindingMilling",
    "30114003":
        "IndustrialProcesses ChemicalManufacturing AcetyleneProducion Mixing",
    "30114004":
        "IndustrialProcesses ChemicalManufacturing AcetyleneProducion WasteHandling",
    "30114005":
        "IndustrialProcesses ChemicalManufacturing AcetyleneProducion General",
    "30114502":
        "IndustrialProcesses ChemicalManufacturing HydrazineProduction OlinRaschigProcessReactor",
    "30115001":
        "IndustrialProcesses ChemicalManufacturing PhthalatePlasticizersProduction OtherNotElsewhereClassified",
    "30115201":
        "IndustrialProcesses ChemicalManufacturing BisphenolA General",
    "30115301":
        "IndustrialProcesses ChemicalManufacturing Butadiene General",
    "30115311":
        "IndustrialProcesses ChemicalManufacturing Butadiene HoudryProcessFlueGasVent",
    "30115320":
        "IndustrialProcesses ChemicalManufacturing Butadiene nButeneProcessTotal",
    "30115380":
        "IndustrialProcesses ChemicalManufacturing Butadiene FugitiveEmissions",
    "30115601":
        "IndustrialProcesses ChemicalManufacturing Cumene General",
    "30115680":
        "IndustrialProcesses ChemicalManufacturing Cumene FugitiveEmissions",
    "30115701":
        "IndustrialProcesses ChemicalManufacturing Cyclohexane General",
    "30115702":
        "IndustrialProcesses ChemicalManufacturing Cyclohexane BlowndownTankDischarge",
    "30115703":
        "IndustrialProcesses ChemicalManufacturing Cyclohexane PumpsValvesCompressors",
    "30115704":
        "IndustrialProcesses ChemicalManufacturing Cyclohexane CatalystReplacement",
    "30115780":
        "IndustrialProcesses ChemicalManufacturing Cyclohexane FugitiveEmissions",
    "30115801":
        "IndustrialProcesses ChemicalManufacturing CyclohexanoneCyclohexanol General",
    "30115802":
        "IndustrialProcesses ChemicalManufacturing CyclohexanoneCyclohexanol HighPressureScrubberVent",
    "30115803":
        "IndustrialProcesses ChemicalManufacturing CyclohexanoneCyclohexanol LowPressureScrubberVent",
    "30115821":
        "IndustrialProcesses ChemicalManufacturing CyclohexanoneCyclohexanol HydrogenationReactorVent",
    "30115822":
        "IndustrialProcesses ChemicalManufacturing CyclohexanoneCyclohexanol DistillationVent",
    "30115880":
        "IndustrialProcesses ChemicalManufacturing CyclohexanoneCyclohexanol FugitiveEmissions",
    "30116701":
        "IndustrialProcesses ChemicalManufacturing VinylAcetate General",
    "30116702":
        "IndustrialProcesses ChemicalManufacturing VinylAcetate InertgasPurgeVent",
    "30116703":
        "IndustrialProcesses ChemicalManufacturing VinylAcetate CO2PurgeVent",
    "30116780":
        "IndustrialProcesses ChemicalManufacturing VinylAcetate FugitiveEmissions",
    "30116799":
        "IndustrialProcesses ChemicalManufacturing VinylAcetate OtherNotClassified",
    "30116901":
        "IndustrialProcesses ChemicalManufacturing EthylBenzene General",
    "30116902":
        "IndustrialProcesses ChemicalManufacturing EthylBenzene AlkylationReactorVent",
    "30116980":
        "IndustrialProcesses ChemicalManufacturing EthylBenzene FugitiveEmissions",
    "30117401":
        "IndustrialProcesses ChemicalManufacturing EthyleneOxide General",
    "30117402":
        "IndustrialProcesses ChemicalManufacturing EthyleneOxide AirOxidationProcessReactorMainVent",
    "30117410":
        "IndustrialProcesses ChemicalManufacturing EthyleneOxide OxygenOxidationProcessReactorCO2PurgeVent",
    "30117411":
        "IndustrialProcesses ChemicalManufacturing EthyleneOxide OxygenOxidationProcessReactorArgonPurgeVent",
    "30117421":
        "IndustrialProcesses ChemicalManufacturing EthyleneOxide StripperPurgeVent",
    "30117480":
        "IndustrialProcesses ChemicalManufacturing EthyleneOxide FugitiveEmissions",
    "30117601":
        "IndustrialProcesses ChemicalManufacturing GlycerinGlycerol General",
    "30117612":
        "IndustrialProcesses ChemicalManufacturing GlycerinGlycerol Evaporator",
    "30117618":
        "IndustrialProcesses ChemicalManufacturing GlycerinGlycerol CoolingTower",
    "30117634":
        "IndustrialProcesses ChemicalManufacturing GlycerinGlycerol ProductDistillationColumn",
    "30117680":
        "IndustrialProcesses ChemicalManufacturing GlycerinGlycerol FugitiveEmissions",
    "30118101":
        "IndustrialProcesses ChemicalManufacturing TolueneDiisocyanate General",
    "30118110":
        "IndustrialProcesses ChemicalManufacturing TolueneDiisocyanate HClAbsorber",
    "30118180":
        "IndustrialProcesses ChemicalManufacturing TolueneDiisocyanate FugitiveEmissions",
    "30119001":
        "IndustrialProcesses ChemicalManufacturing MethylMethacrylate General",
    "30119012":
        "IndustrialProcesses ChemicalManufacturing MethylMethacrylate MMAandLightendsDistillationUnit",
    "30119014":
        "IndustrialProcesses ChemicalManufacturing MethylMethacrylate MMAPurification",
    "30119080":
        "IndustrialProcesses ChemicalManufacturing MethylMethacrylate FugitiveEmissions",
    "30119501":
        "IndustrialProcesses ChemicalManufacturing Nitrobenzene General",
    "30119504":
        "IndustrialProcesses ChemicalManufacturing Nitrobenzene WasherandNeutralizerVent",
    "30119505":
        "IndustrialProcesses ChemicalManufacturing Nitrobenzene NitrobenzeneStripperVent",
    "30119506":
        "IndustrialProcesses ChemicalManufacturing Nitrobenzene WasteAcidStorage",
    "30119701":
        "IndustrialProcesses ChemicalManufacturing ButyleneEthylenePropyleneOlefinProduction EthyleneGeneral",
    "30119705":
        "IndustrialProcesses ChemicalManufacturing ButyleneEthylenePropyleneOlefinProduction PropyleneGeneral",
    "30119706":
        "IndustrialProcesses ChemicalManufacturing ButyleneEthylenePropyleneOlefinProduction PropyleneReactor",
    "30119707":
        "IndustrialProcesses ChemicalManufacturing ButyleneEthylenePropyleneOlefinProduction PropyleneDryingTower",
    "30119708":
        "IndustrialProcesses ChemicalManufacturing ButyleneEthylenePropyleneOlefinProduction PropyleneLightendsStripper",
    "30119709":
        "IndustrialProcesses ChemicalManufacturing ButyleneEthylenePropyleneOlefinProduction PropyleneFugitiveEmissions",
    "30119710":
        "IndustrialProcesses ChemicalManufacturing ButyleneEthylenePropyleneOlefinProduction ButyleneGeneral",
    "30119741":
        "IndustrialProcesses ChemicalManufacturing ButyleneEthylenePropyleneOlefinProduction EthyleneCrackingFurnaceFireboxStack",
    "30119742":
        "IndustrialProcesses ChemicalManufacturing ButyleneEthylenePropyleneOlefinProduction EthyleneDecoking",
    "30119743":
        "IndustrialProcesses ChemicalManufacturing ButyleneEthylenePropyleneOlefinProduction EthyleneAcidGasRemoval",
    "30119744":
        "IndustrialProcesses ChemicalManufacturing ButyleneEthylenePropyleneOlefinProduction EthyleneCatalystRegeneration",
    "30119745":
        "IndustrialProcesses ChemicalManufacturing ButyleneEthylenePropyleneOlefinProduction EthyleneCompressorLubeOilVent",
    "30119749":
        "IndustrialProcesses ChemicalManufacturing ButyleneEthylenePropyleneOlefinProduction EthyleneFugitiveEmissions",
    "30119799":
        "IndustrialProcesses ChemicalManufacturing ButyleneEthylenePropyleneOlefinProduction OtherNotClassified",
    "30120201":
        "IndustrialProcesses ChemicalManufacturing Phenol General",
    "30120202":
        "IndustrialProcesses ChemicalManufacturing Phenol CumeneOxidation",
    "30120203":
        "IndustrialProcesses ChemicalManufacturing Phenol CHPConcentrator",
    "30120204":
        "IndustrialProcesses ChemicalManufacturing Phenol LightendsDistillationVent",
    "30120205":
        "IndustrialProcesses ChemicalManufacturing Phenol AcetoneFinishing",
    "30120206":
        "IndustrialProcesses ChemicalManufacturing Phenol PhenolDistillationColumn",
    "30120211":
        "IndustrialProcesses ChemicalManufacturing Phenol CHPCleavageVent",
    "30120280":
        "IndustrialProcesses ChemicalManufacturing Phenol FugitiveEmissions",
    "30120501":
        "IndustrialProcesses ChemicalManufacturing PropyleneOxide General",
    "30120502":
        "IndustrialProcesses ChemicalManufacturing PropyleneOxide ChlorohydronationProcessGeneral",
    "30120503":
        "IndustrialProcesses ChemicalManufacturing PropyleneOxide VentGasScrubberVent",
    "30120521":
        "IndustrialProcesses ChemicalManufacturing PropyleneOxide OxidationReactorScrubberVent",
    "30120523":
        "IndustrialProcesses ChemicalManufacturing PropyleneOxide CatalystMixTankVent",
    "30120527":
        "IndustrialProcesses ChemicalManufacturing PropyleneOxide WastewaterStrippingColumnVent",
    "30120528":
        "IndustrialProcesses ChemicalManufacturing PropyleneOxide SolventScrubberVent",
    "30120529":
        "IndustrialProcesses ChemicalManufacturing PropyleneOxide SolventRecoveryColumnVent",
    "30120530":
        "IndustrialProcesses ChemicalManufacturing PropyleneOxide WaterStrippingColumnVent",
    "30120531":
        "IndustrialProcesses ChemicalManufacturing PropyleneOxide PropyleneGlycolandDipropyleneGlycolCombinedVent",
    "30120540":
        "IndustrialProcesses ChemicalManufacturing PropyleneOxide EthylbenzeneHydroperoxideProcessGeneral",
    "30120545":
        "IndustrialProcesses ChemicalManufacturing PropyleneOxide LightendsStrippingColumnVent",
    "30120580":
        "IndustrialProcesses ChemicalManufacturing PropyleneOxide FugitiveEmissions",
    "30120601":
        "IndustrialProcesses ChemicalManufacturing Styrene General",
    "30120602":
        "IndustrialProcesses ChemicalManufacturing Styrene BenzeneRecycle",
    "30120603":
        "IndustrialProcesses ChemicalManufacturing Styrene StyrenePurification",
    "30120680":
        "IndustrialProcesses ChemicalManufacturing Styrene FugitiveEmissions",
    "30121001":
        "IndustrialProcesses ChemicalManufacturing CaprolactumUse301130forAmmoniumSulfateByproductProduction General",
    "30121002":
        "IndustrialProcesses ChemicalManufacturing CaprolactumUse301130forAmmoniumSulfateByproductProduction CyclohexanonePurificationVent",
    "30121005":
        "IndustrialProcesses ChemicalManufacturing CaprolactumUse301130forAmmoniumSulfateByproductProduction NeutralizationReactorVent",
    "30121006":
        "IndustrialProcesses ChemicalManufacturing CaprolactumUse301130forAmmoniumSulfateByproductProduction SolventSeparationRecovery",
    "30121007":
        "IndustrialProcesses ChemicalManufacturing CaprolactumUse301130forAmmoniumSulfateByproductProduction OximationReactorSeparator",
    "30121008":
        "IndustrialProcesses ChemicalManufacturing CaprolactumUse301130forAmmoniumSulfateByproductProduction CaprolactumPurification",
    "30121009":
        "IndustrialProcesses ChemicalManufacturing CaprolactumUse301130forAmmoniumSulfateByproductProduction AmmoniumSulfateDryingUse30113004or30113005",
    "30121080":
        "IndustrialProcesses ChemicalManufacturing CaprolactumUse301130forAmmoniumSulfateByproductProduction FugitiveEmissions",
    "30121101":
        "IndustrialProcesses ChemicalManufacturing LinearAlkylbenzene OlefinProcessGeneral",
    "30121103":
        "IndustrialProcesses ChemicalManufacturing LinearAlkylbenzene HydrogenFluorideScrubberVent",
    "30121104":
        "IndustrialProcesses ChemicalManufacturing LinearAlkylbenzene VacuumRefining",
    "30121124":
        "IndustrialProcesses ChemicalManufacturing LinearAlkylbenzene AtmosphericWashDecantVent",
    "30121180":
        "IndustrialProcesses ChemicalManufacturing LinearAlkylbenzene FugitiveEmissions",
    "30125001":
        "IndustrialProcesses ChemicalManufacturing MethanolAlcoholProduction MethanolGeneral",
    "30125002":
        "IndustrialProcesses ChemicalManufacturing MethanolAlcoholProduction MethanolPurgeGasVent",
    "30125003":
        "IndustrialProcesses ChemicalManufacturing MethanolAlcoholProduction MethanolDistillationVent",
    "30125004":
        "IndustrialProcesses ChemicalManufacturing MethanolAlcoholProduction MethanolFugitiveEmissions",
    "30125005":
        "IndustrialProcesses ChemicalManufacturing MethanolAlcoholProduction EthanolviaEthylene",
    "30125010":
        "IndustrialProcesses ChemicalManufacturing MethanolAlcoholProduction EthanolbyFermentation",
    "30125015":
        "IndustrialProcesses ChemicalManufacturing MethanolAlcoholProduction Isopropanol",
    "30125020":
        "IndustrialProcesses ChemicalManufacturing MethanolAlcoholProduction AlcoholsbyOxoProcess",
    "30125025":
        "IndustrialProcesses ChemicalManufacturing MethanolAlcoholProduction FattyAlcoholsbyHydrogenation",
    "30125099":
        "IndustrialProcesses ChemicalManufacturing MethanolAlcoholProduction OtherNotClassified",
    "30125101":
        "IndustrialProcesses ChemicalManufacturing EthyleneGlycol General",
    "30125104":
        "IndustrialProcesses ChemicalManufacturing EthyleneGlycol DistillationColumnVent",
    "30125180":
        "IndustrialProcesses ChemicalManufacturing EthyleneGlycol FugitiveEmissions",
    "30125201":
        "IndustrialProcesses ChemicalManufacturing EthereneProduction General",
    "30125301":
        "IndustrialProcesses ChemicalManufacturing GlycolEthers General",
    "30125302":
        "IndustrialProcesses ChemicalManufacturing GlycolEthers VacuumSystemVent",
    "30125305":
        "IndustrialProcesses ChemicalManufacturing GlycolEthers CatalystMethanolMixTank",
    "30125306":
        "IndustrialProcesses ChemicalManufacturing GlycolEthers MethanolRecoveryColumnVent",
    "30125316":
        "IndustrialProcesses ChemicalManufacturing GlycolEthers EthanolRecoveryColumnVent",
    "30125325":
        "IndustrialProcesses ChemicalManufacturing GlycolEthers CatalystButanolMixTank",
    "30125326":
        "IndustrialProcesses ChemicalManufacturing GlycolEthers ButanolRecoveryColumnVent",
    "30125380":
        "IndustrialProcesses ChemicalManufacturing GlycolEthers FugitiveEmissions",
    "30125401":
        "IndustrialProcesses ChemicalManufacturing NitrilesAcrylonitrileAdiponitrileProduction Acetonitrile",
    "30125405":
        "IndustrialProcesses ChemicalManufacturing NitrilesAcrylonitrileAdiponitrileProduction GeneralAcrylonitrile",
    "30125406":
        "IndustrialProcesses ChemicalManufacturing NitrilesAcrylonitrileAdiponitrileProduction AbsorberVentNormal",
    "30125407":
        "IndustrialProcesses ChemicalManufacturing NitrilesAcrylonitrileAdiponitrileProduction AbsorberVentStartup",
    "30125408":
        "IndustrialProcesses ChemicalManufacturing NitrilesAcrylonitrileAdiponitrileProduction RecoveryPurificationColumnVent",
    "30125410":
        "IndustrialProcesses ChemicalManufacturing NitrilesAcrylonitrileAdiponitrileProduction ViaAdipicAcidGeneral",
    "30125412":
        "IndustrialProcesses ChemicalManufacturing NitrilesAcrylonitrileAdiponitrileProduction ProductFractionatorVent",
    "30125413":
        "IndustrialProcesses ChemicalManufacturing NitrilesAcrylonitrileAdiponitrileProduction ProductRecoveryVent",
    "30125415":
        "IndustrialProcesses ChemicalManufacturing NitrilesAcrylonitrileAdiponitrileProduction ViaButadieneGeneral",
    "30125420":
        "IndustrialProcesses ChemicalManufacturing NitrilesAcrylonitrileAdiponitrileProduction FugitiveEmissions",
    "30125499":
        "IndustrialProcesses ChemicalManufacturing NitrilesAcrylonitrileAdiponitrileProduction OtherNotClassified",
    "30125801":
        "IndustrialProcesses ChemicalManufacturing BenzeneTolueneAromaticsXylenes BenzeneGeneral",
    "30125802":
        "IndustrialProcesses ChemicalManufacturing BenzeneTolueneAromaticsXylenes BenzeneReactor",
    "30125803":
        "IndustrialProcesses ChemicalManufacturing BenzeneTolueneAromaticsXylenes BenzeneDistillationUnit",
    "30125805":
        "IndustrialProcesses ChemicalManufacturing BenzeneTolueneAromaticsXylenes TolueneGeneral",
    "30125806":
        "IndustrialProcesses ChemicalManufacturing BenzeneTolueneAromaticsXylenes TolueneReactor",
    "30125807":
        "IndustrialProcesses ChemicalManufacturing BenzeneTolueneAromaticsXylenes TolueneDistillationUnit",
    "30125810":
        "IndustrialProcesses ChemicalManufacturing BenzeneTolueneAromaticsXylenes pXyleneGeneral",
    "30125815":
        "IndustrialProcesses ChemicalManufacturing BenzeneTolueneAromaticsXylenes XylenesGeneral",
    "30125816":
        "IndustrialProcesses ChemicalManufacturing BenzeneTolueneAromaticsXylenes XylenesReactor",
    "30125817":
        "IndustrialProcesses ChemicalManufacturing BenzeneTolueneAromaticsXylenes XylenesDistillationUnit",
    "30125880":
        "IndustrialProcesses ChemicalManufacturing BenzeneTolueneAromaticsXylenes AromaticsFugitiveEmissions",
    "30125899":
        "IndustrialProcesses ChemicalManufacturing BenzeneTolueneAromaticsXylenes OtherNotClassified",
    "30126006":
        "IndustrialProcesses ChemicalManufacturing InorganicChemicalManufacturingAntimonyOxides MaterialRecovery",
    "30126301":
        "IndustrialProcesses ChemicalManufacturing InorganicChemicalManufacturingSodiumCyanide OtherNotElsewhereClassified",
    "30126304":
        "IndustrialProcesses ChemicalManufacturing InorganicChemicalManufacturingSodiumCyanide Filtration",
    "30126306":
        "IndustrialProcesses ChemicalManufacturing InorganicChemicalManufacturingSodiumCyanide Dryer",
    "30126402":
        "IndustrialProcesses ChemicalManufacturing InorganicChemicalManufacturingUraniumHexafluoride Fluorination",
    "30126403":
        "IndustrialProcesses ChemicalManufacturing InorganicChemicalManufacturingUraniumHexafluoride ProductFinishing",
    "30130101":
        "IndustrialProcesses ChemicalManufacturing Chlorobenzene TailGasScrubber",
    "30130105":
        "IndustrialProcesses ChemicalManufacturing Chlorobenzene MCBDistillation",
    "30130107":
        "IndustrialProcesses ChemicalManufacturing Chlorobenzene DCBCrystallization",
    "30130114":
        "IndustrialProcesses ChemicalManufacturing Chlorobenzene SecondaryEmissionsHandlingandDisposalofWastewater",
    "30130115":
        "IndustrialProcesses ChemicalManufacturing Chlorobenzene AtmosphericDistillationVents",
    "30130180":
        "IndustrialProcesses ChemicalManufacturing Chlorobenzene FugitiveEmissions",
    "30130201":
        "IndustrialProcesses ChemicalManufacturing CarbonTetrachloride General",
    "30130202":
        "IndustrialProcesses ChemicalManufacturing CarbonTetrachloride DistillationVent",
    "30130203":
        "IndustrialProcesses ChemicalManufacturing CarbonTetrachloride CausticScrubber",
    "30130280":
        "IndustrialProcesses ChemicalManufacturing CarbonTetrachloride FugitiveEmissions",
    "30130301":
        "IndustrialProcesses ChemicalManufacturing AllylChloride ChlorinationProcessGeneral",
    "30130302":
        "IndustrialProcesses ChemicalManufacturing AllylChloride HClAbsorber",
    "30130380":
        "IndustrialProcesses ChemicalManufacturing AllylChloride FugitiveEmissions",
    "30130402":
        "IndustrialProcesses ChemicalManufacturing AllylAlcohol CatalystPreparation",
    "30130405":
        "IndustrialProcesses ChemicalManufacturing AllylAlcohol DistillationSystemCondenser",
    "30130480":
        "IndustrialProcesses ChemicalManufacturing AllylAlcohol FugitiveEmissions",
    "30130501":
        "IndustrialProcesses ChemicalManufacturing Epichlorohydrin General",
    "30130502":
        "IndustrialProcesses ChemicalManufacturing Epichlorohydrin EpoxidationReactor",
    "30130504":
        "IndustrialProcesses ChemicalManufacturing Epichlorohydrin LightendsStripper",
    "30130505":
        "IndustrialProcesses ChemicalManufacturing Epichlorohydrin FinishingColumn",
    "30130580":
        "IndustrialProcesses ChemicalManufacturing Epichlorohydrin FugitiveEmissions",
    "30140101":
        "IndustrialProcesses ChemicalManufacturing NitroglycerinProduction ContinuousNitrator",
    "30140151":
        "IndustrialProcesses ChemicalManufacturing NitroglycerinProduction WasteDisposalSeparation",
    "30140199":
        "IndustrialProcesses ChemicalManufacturing NitroglycerinProduction OtherNotClassified",
    "30140210":
        "IndustrialProcesses ChemicalManufacturing ExplosivesManufacturePentaerythritolTetranitratePETN ProcessVentsBatchProcess",
    "30140211":
        "IndustrialProcesses ChemicalManufacturing ExplosivesManufacturePentaerythritolTetranitratePETN BatchProcessNitrationReactorsandWashers",
    "30140214":
        "IndustrialProcesses ChemicalManufacturing ExplosivesManufacturePentaerythritolTetranitratePETN BatchProcessStabilization",
    "30140250":
        "IndustrialProcesses ChemicalManufacturing ExplosivesManufacturePentaerythritolTetranitratePETN ProcessVentsContinuousProcess",
    "30140299":
        "IndustrialProcesses ChemicalManufacturing ExplosivesManufacturePentaerythritolTetranitratePETN OtherNotClassified",
    "30140306":
        "IndustrialProcesses ChemicalManufacturing ExplosivesManufactureRDXHMXProduction NitricAcidAmmoniumNitrateMixing",
    "30140310":
        "IndustrialProcesses ChemicalManufacturing ExplosivesManufactureRDXHMXProduction ProcessVentsBatchProcess",
    "30140311":
        "IndustrialProcesses ChemicalManufacturing ExplosivesManufactureRDXHMXProduction BatchProcessNitrationReactor",
    "30140330":
        "IndustrialProcesses ChemicalManufacturing ExplosivesManufactureRDXHMXProduction BatchProcessBlending",
    "30140350":
        "IndustrialProcesses ChemicalManufacturing ExplosivesManufactureRDXHMXProduction BatchProcessAceticAcidRecovery",
    "30140360":
        "IndustrialProcesses ChemicalManufacturing ExplosivesManufactureRDXHMXProduction BatchProcessAcetoneorCyclohexanoneRecovery",
    "30140399":
        "IndustrialProcesses ChemicalManufacturing ExplosivesManufactureRDXHMXProduction OtherNotClassified",
    "30180001":
        "IndustrialProcesses ChemicalManufacturing EquipmentLeaks General",
    "30180002":
        "IndustrialProcesses ChemicalManufacturing GeneralProcesses PipelineValvesGasStream",
    "30180003":
        "IndustrialProcesses ChemicalManufacturing EquipmentLeaks PipelineValvesLightLiquidGasStream",
    "30180004":
        "IndustrialProcesses ChemicalManufacturing EquipmentLeaks PipelineValvesHeavyLiquidStream",
    "30180006":
        "IndustrialProcesses ChemicalManufacturing EquipmentLeaks OpenendedValvesorLinesAllStreams",
    "30180007":
        "IndustrialProcesses ChemicalManufacturing EquipmentLeaks FlangesAllStreams",
    "30180008":
        "IndustrialProcesses ChemicalManufacturing EquipmentLeaks PumpSealsLightLiquidGasStream",
    "30180009":
        "IndustrialProcesses ChemicalManufacturing EquipmentLeaks PumpSealsHeavyLiquidStream",
    "30180010":
        "IndustrialProcesses ChemicalManufacturing EquipmentLeaks CompressorSealsGasStream",
    "30180011":
        "IndustrialProcesses ChemicalManufacturing EquipmentLeaks CompressorSealsHeavyLiquidStream",
    "30180012":
        "IndustrialProcesses ChemicalManufacturing EquipmentLeaks DrainsAllStreams",
    "30180013":
        "IndustrialProcesses ChemicalManufacturing GeneralProcesses VesselReliefValvesAllStreams",
    "30180014":
        "IndustrialProcesses ChemicalManufacturing EquipmentLeaks PressureReliefDevicesGasStream",
    "30181001":
        "IndustrialProcesses ChemicalManufacturing GeneralProcesses AirOxidationUnit",
    "30181002":
        "IndustrialProcesses ChemicalManufacturing GeneralProcesses DistillationUnit",
    "30181003":
        "IndustrialProcesses ChemicalManufacturing GeneralProcesses StorageTransfer",
    "30182001":
        "IndustrialProcesses ChemicalManufacturing WastewaterTreatment Stripper",
    "30182002":
        "IndustrialProcesses ChemicalManufacturing WastewaterTreatment General",
    "30182004":
        "IndustrialProcesses ChemicalManufacturing WastewaterTreatment JunctionBox",
    "30182005":
        "IndustrialProcesses ChemicalManufacturing WastewaterTreatment LiftStation",
    "30182006":
        "IndustrialProcesses ChemicalManufacturing WastewaterTreatment AeratedImpoundment",
    "30182007":
        "IndustrialProcesses ChemicalManufacturing WastewaterTreatment NonaeratedImpoundment",
    "30182008":
        "IndustrialProcesses ChemicalManufacturing WastewaterTreatment Weir",
    "30182009":
        "IndustrialProcesses ChemicalManufacturing WastewaterTreatment ActivatedSludgeImpoundment",
    "30182010":
        "IndustrialProcesses ChemicalManufacturing WastewaterTreatment Clarifier",
    "30182011":
        "IndustrialProcesses ChemicalManufacturing WastewaterTreatment OpenTrench",
    "30182014":
        "IndustrialProcesses ChemicalManufacturing WastewaterTreatment Drain",
    "30182015":
        "IndustrialProcesses ChemicalManufacturing WastewaterTreatment Tank",
    "30182502":
        "IndustrialProcesses ChemicalManufacturing WastewaterPointsofGeneration TNTSelliteTreatmentandSubsequentWashingofCrudeTNTRedH2O",
    "30182504":
        "IndustrialProcesses ChemicalManufacturing WastewaterPointsofGeneration TNTFinishingOperationFumeScrubber",
    "30182515":
        "IndustrialProcesses ChemicalManufacturing WastewaterPointsofGeneration NGSpentAcidStorage",
    "30182531":
        "IndustrialProcesses ChemicalManufacturing WastewaterPointsofGeneration NCNitrationReactor",
    "30182551":
        "IndustrialProcesses ChemicalManufacturing WastewaterPointsofGeneration PETNSpentAcidRecovery",
    "30182563":
        "IndustrialProcesses ChemicalManufacturing WastewaterPointsofGeneration RDXHMXDewatering",
    "30182599":
        "IndustrialProcesses ChemicalManufacturing WastewaterPointsofGeneration OtherNotClassified",
    "30183001":
        "IndustrialProcesses ChemicalManufacturing GeneralProcesses StorageTransfer",
    "30184001":
        "IndustrialProcesses ChemicalManufacturing GeneralProcesses DistillationUnits",
    "30187001":
        "IndustrialProcesses ChemicalManufacturing InorganicChemicalStorageFixedRoofTanks HydrochloricAcidBreathingLossUse30187033",
    "30187002":
        "IndustrialProcesses ChemicalManufacturing InorganicChemicalStorageFixedRoofTanks HydrochloricAcidWorkingLossUse30187034",
    "30187003":
        "IndustrialProcesses ChemicalManufacturing InorganicChemicalStorageFixedRoofTanks HydrofluoricAcidBreathingLoss",
    "30187004":
        "IndustrialProcesses ChemicalManufacturing InorganicChemicalStorageFixedRoofTanks HydrofluoricAcidWorkingLoss",
    "30187005":
        "IndustrialProcesses ChemicalManufacturing InorganicChemicalStorageFixedRoofTanks NitricAcidBreathingLoss",
    "30187006":
        "IndustrialProcesses ChemicalManufacturing InorganicChemicalStorageFixedRoofTanks NitricAcidWorkingLoss",
    "30187007":
        "IndustrialProcesses ChemicalManufacturing InorganicChemicalStorageFixedRoofTanks PhosphoricAcidBreathingLoss",
    "30187008":
        "IndustrialProcesses ChemicalManufacturing InorganicChemicalStorageFixedRoofTanks PhosphoricAcidWorkingLoss",
    "30187009":
        "IndustrialProcesses ChemicalManufacturing InorganicChemicalStorageFixedRoofTanks SulfuricAcidBreathingLoss",
    "30187010":
        "IndustrialProcesses ChemicalManufacturing InorganicChemicalStorageFixedRoofTanks SulfuricAcidWorkingLoss",
    "30187011":
        "IndustrialProcesses ChemicalManufacturing InorganicChemicalStorageFixedRoofTanks AmmoniumNitrateBreathingLoss",
    "30187013":
        "IndustrialProcesses ChemicalManufacturing InorganicChemicalStorageFixedRoofTanks UreaBreathingLoss",
    "30187014":
        "IndustrialProcesses ChemicalManufacturing InorganicChemicalStorageFixedRoofTanks UreaWorkingLoss",
    "30187017":
        "IndustrialProcesses ChemicalManufacturing InorganicChemicalStorageFixedRoofTanks AqueousAmmoniaBreathingLoss",
    "30187018":
        "IndustrialProcesses ChemicalManufacturing InorganicChemicalStorageFixedRoofTanks AqueousAmmoniaWorkingLoss",
    "30187020":
        "IndustrialProcesses ChemicalManufacturing InorganicChemicalStorageFixedRoofTanks AmmoniumBicarbonateWorkingLoss",
    "30187022":
        "IndustrialProcesses ChemicalManufacturing InorganicChemicalStorageFixedRoofTanks HydrazineHydrateWorkingLoss",
    "30187023":
        "IndustrialProcesses ChemicalManufacturing InorganicChemicalStorageFixedRoofTanks AnhydrousHydrazineBreathingLoss",
    "30187025":
        "IndustrialProcesses ChemicalManufacturing InorganicChemicalStorageFixedRoofTanks AmmoniumSulfateBreathingLoss",
    "30187031":
        "IndustrialProcesses ChemicalManufacturing InorganicChemicalStorageFixedRoofTanks ChromicAcidBreathingLoss",
    "30187033":
        "IndustrialProcesses ChemicalManufacturing InorganicChemicalStorageFixedRoofTanks HydrochloricAcidBreathingLoss",
    "30187034":
        "IndustrialProcesses ChemicalManufacturing InorganicChemicalStorageFixedRoofTanks HydrochloricAcidWorkingLoss",
    "30187097":
        "IndustrialProcesses ChemicalManufacturing InorganicChemicalStorageFixedRoofTanks InorganicChemicalsBreathingLoss",
    "30187098":
        "IndustrialProcesses ChemicalManufacturing InorganicChemicalStorageFixedRoofTanks InorganicChemicalsWorkingLoss",
    "30187501":
        "IndustrialProcesses ChemicalManufacturing InorganicChemicalStorageFloatingRoofTank CarbonDisulfideBreathingLossUse40729601",
    "30187502":
        "IndustrialProcesses ChemicalManufacturing InorganicChemicalStorageFloatingRoofTank CarbonDisulfideWithdrawalLossUse40729602",
    "30187517":
        "IndustrialProcesses ChemicalManufacturing InorganicChemicalStorageFloatingRoofTanks AqueousAmmoniaBreathingLoss",
    "30187518":
        "IndustrialProcesses ChemicalManufacturing InorganicChemicalStorageFloatingRoofTanks AqueousAmmoniaWorkingLoss",
    "30187533":
        "IndustrialProcesses ChemicalManufacturing InorganicChemicalStorageFloatingRoofTanks HydrochloricAcidBreathingLoss",
    "30187534":
        "IndustrialProcesses ChemicalManufacturing InorganicChemicalStorageFloatingRoofTanks HydrochloricAcidWorkingLoss",
    "30187597":
        "IndustrialProcesses ChemicalManufacturing InorganicChemicalStorageFloatingRoofTanks InorganicChemicalsBreathingLoss",
    "30187598":
        "IndustrialProcesses ChemicalManufacturing InorganicChemicalStorageFloatingRoofTanks InorganicChemicalsWorkingLoss",
    "30188501":
        "IndustrialProcesses ChemicalManufacturing InorganicChemicalStoragePressureTanks Ammonia",
    "30188503":
        "IndustrialProcesses ChemicalManufacturing InorganicChemicalStoragePressureTanks Chlorine",
    "30188505":
        "IndustrialProcesses ChemicalManufacturing InorganicChemicalStoragePressureTanks SulfurDioxide",
    "30188507":
        "IndustrialProcesses ChemicalManufacturing InorganicChemicalStoragePressureTanks CarbonDioxide",
    "30188510":
        "IndustrialProcesses ChemicalManufacturing InorganicChemicalStoragePressureTanks AnhydrousAmmonia",
    "30188513":
        "IndustrialProcesses ChemicalManufacturing InorganicChemicalStoragePressureTanks HydrogenChloride",
    "30188599":
        "IndustrialProcesses ChemicalManufacturing InorganicChemicalStoragePressureTanks InorganicChemicals",
    "30188801":
        "IndustrialProcesses ChemicalManufacturing FugitiveEmissions AllNotElsewhereClassified",
    "30188805":
        "IndustrialProcesses ChemicalManufacturing FugitiveEmissions SpecifyinCommentsField",
    "30190001":
        "IndustrialProcesses ChemicalManufacturing FuelFiredEquipment ProcessHeaterDistillateOilNo.2",
    "30190002":
        "IndustrialProcesses ChemicalManufacturing FuelFiredEquipment ProcessHeaterResidualOil",
    "30190003":
        "IndustrialProcesses ChemicalManufacturing FuelFiredEquipment ProcessHeaterNaturalGas",
    "30190004":
        "IndustrialProcesses ChemicalManufacturing FuelFiredEquipment ProcessHeaterProcessGas",
    "30190011":
        "IndustrialProcesses ChemicalManufacturing FuelFiredEquipment IncineratorDistillateOilNo.2",
    "30190012":
        "IndustrialProcesses ChemicalManufacturing FuelFiredEquipment IncineratorResidualOil",
    "30190013":
        "IndustrialProcesses ChemicalManufacturing FuelFiredEquipment IncineratorNaturalGas",
    "30190014":
        "IndustrialProcesses ChemicalManufacturing FuelFiredEquipment IncineratorProcessGas",
    "30190021":
        "IndustrialProcesses ChemicalManufacturing FuelFiredEquipment FlareDistillateOilNo.2",
    "30190022":
        "IndustrialProcesses ChemicalManufacturing FuelFiredEquipment FlareResidualOil",
    "30190023":
        "IndustrialProcesses ChemicalManufacturing FuelFiredEquipment FlareNaturalGas",
    "30190099":
        "IndustrialProcesses ChemicalManufacturing FuelFiredEquipment OtherNotElsewhereClassified",
    "30199998":
        "IndustrialProcesses ChemicalManufacturing OtherNotClassified OtherNotElsewhereClassified",
    "30199999":
        "IndustrialProcesses ChemicalManufacturing OtherNotClassified SpecifyinCommentsField",
    "30200101":
        "IndustrialProcesses FoodandAgriculture AlfalfaDehydration General",
    "30200102":
        "IndustrialProcesses FoodandAgriculture AlfalfaDehydration PrimaryCycloneandDryeruse11thru14",
    "30200103":
        "IndustrialProcesses FoodandAgriculture AlfalfaDehydration MealCollectorCyclone",
    "30200104":
        "IndustrialProcesses FoodandAgriculture AlfalfaDehydration PelletCoolerCyclone",
    "30200107":
        "IndustrialProcesses FoodandAgriculture AlfalfaDehydration PelletCollectorCyclone",
    "30200111":
        "IndustrialProcesses FoodandAgriculture AlfalfaDehydration GasfiredTriplePassDryerCyclone",
    "30200115":
        "IndustrialProcesses FoodandAgriculture AlfalfaDehydration GasfiredSinglePassDryerCyclone",
    "30200117":
        "IndustrialProcesses FoodandAgriculture AlfalfaDehydration WoodfiredSinglePassDryerCyclone",
    "30200120":
        "IndustrialProcesses FoodandAgriculture AlfalfaDehydration PelletStorageBinCyclone",
    "30200199":
        "IndustrialProcesses FoodandAgriculture AlfalfaDehydration OtherNotClassified",
    "30200201":
        "IndustrialProcesses FoodandAgriculture CoffeeRoasting DirectFiredRoasteruse30200224or25",
    "30200202":
        "IndustrialProcesses FoodandAgriculture CoffeeRoasting IndirectFiredRoasteruse30200220or21",
    "30200203":
        "IndustrialProcesses FoodandAgriculture CoffeeRoasting StonerCooleruse30200230",
    "30200204":
        "IndustrialProcesses FoodandAgriculture CoffeeRoasting GreenCoffeeBeanUnloading",
    "30200206":
        "IndustrialProcesses FoodandAgriculture CoffeeRoasting ScreeningDebrisRemovalfromGreenCoffeeBeans",
    "30200208":
        "IndustrialProcesses FoodandAgriculture CoffeeRoasting GreenCoffeeBeanStorageandHandling",
    "30200216":
        "IndustrialProcesses FoodandAgriculture CoffeeRoasting SteamorHotAirDryingofDecaffeinatedGreenCoffeeBeans",
    "30200220":
        "IndustrialProcesses FoodandAgriculture CoffeeRoasting IndirectfiredBatchRoasterNaturalGasinclcombustionemiss",
    "30200221":
        "IndustrialProcesses FoodandAgriculture CoffeeRoasting IndirectfiredContinuousRoasterNaturalGasinclcombustionemiss",
    "30200224":
        "IndustrialProcesses FoodandAgriculture CoffeeRoasting DirectfiredBatchRoasterNaturalGas",
    "30200225":
        "IndustrialProcesses FoodandAgriculture CoffeeRoasting DirectfiredContinuousRoasterNaturalGas",
    "30200228":
        "IndustrialProcesses FoodandAgriculture CoffeeRoasting CoolingofRoastedCoffeeBeans",
    "30200230":
        "IndustrialProcesses FoodandAgriculture CoffeeRoasting DestoningAirClassificationforDebrisRemoval",
    "30200234":
        "IndustrialProcesses FoodandAgriculture CoffeeRoasting EquilibrationAirDrying&StabilizationofRoastedCoffeeBeans",
    "30200299":
        "IndustrialProcesses FoodandAgriculture CoffeeRoasting OtherNotClassified",
    "30200301":
        "IndustrialProcesses FoodandAgriculture InstantCoffeeProducts SprayDryingInstantCoffeeGroundCoffeeafterH2OExtraction",
    "30200401":
        "IndustrialProcesses FoodandAgriculture CottonGinning UnloadingFan",
    "30200402":
        "IndustrialProcesses FoodandAgriculture CottonGinning SeedCottonCleaningSystemuseSCCs3020042021&22",
    "30200403":
        "IndustrialProcesses FoodandAgriculture CottonGinning MasterTrashFaninclStick&BurrMachGinStandExtrrFeedBattCond",
    "30200404":
        "IndustrialProcesses FoodandAgriculture CottonGinning MiscellaneousinclLintClrBattCondTrashOverflo&MoteFans",
    "30200406":
        "IndustrialProcesses FoodandAgriculture CottonGinning SawGinning",
    "30200407":
        "IndustrialProcesses FoodandAgriculture CottonGinning LintCleaners",
    "30200408":
        "IndustrialProcesses FoodandAgriculture CottonGinning BatteryCondenserinclBalingSystem",
    "30200410":
        "IndustrialProcesses FoodandAgriculture CottonGinning GeneralEntireProcessSumofTypicalEquipUsed",
    "30200415":
        "IndustrialProcesses FoodandAgriculture CottonGinning DryinguseSCCs3020042021&22",
    "30200420":
        "IndustrialProcesses FoodandAgriculture CottonGinning No.1DryerandCleaner",
    "30200421":
        "IndustrialProcesses FoodandAgriculture CottonGinning No.2DryerandCleaner",
    "30200425":
        "IndustrialProcesses FoodandAgriculture CottonGinning OverflowFan",
    "30200435":
        "IndustrialProcesses FoodandAgriculture CottonGinning MoteFan",
    "30200436":
        "IndustrialProcesses FoodandAgriculture CottonGinning MoteTrashFan",
    "30200499":
        "IndustrialProcesses FoodandAgriculture CottonGinning NotClassified",
    "30200501":
        "IndustrialProcesses FoodandAgriculture FeedandGrainTerminalElevators ShippingReceiving",
    "30200502":
        "IndustrialProcesses FoodandAgriculture FeedandGrainTerminalElevators TransferConvey",
    "30200503":
        "IndustrialProcesses FoodandAgriculture FeedandGrainTerminalElevators Cleaning",
    "30200504":
        "IndustrialProcesses FoodandAgriculture FeedandGrainTerminalElevators Drying",
    "30200505":
        "IndustrialProcesses FoodandAgriculture FeedandGrainTerminalElevators UnloadingReceiving",
    "30200506":
        "IndustrialProcesses FoodandAgriculture FeedandGrainTerminalElevators LoadingShipping",
    "30200507":
        "IndustrialProcesses FoodandAgriculture FeedandGrainTerminalElevators RemovalfromBinsTunnelBelt",
    "30200508":
        "IndustrialProcesses FoodandAgriculture FeedandGrainTerminalElevators ElevatorLegsHeadhouse",
    "30200509":
        "IndustrialProcesses FoodandAgriculture FeedandGrainTerminalElevators TripperGalleryBelt",
    "30200512":
        "IndustrialProcesses FoodandAgriculture FeedandGrainTerminalElevators CountryElevatorsGeneral",
    "30200513":
        "IndustrialProcesses FoodandAgriculture FeedandGrainTerminalElevators FumigationTanks",
    "30200516":
        "IndustrialProcesses FoodandAgriculture FeedandGrainTerminalElevators Loading",
    "30200517":
        "IndustrialProcesses FoodandAgriculture FeedandGrainTerminalElevators Turning",
    "30200520":
        "IndustrialProcesses FoodandAgriculture FeedandGrainTerminalElevators BatchDryer",
    "30200521":
        "IndustrialProcesses FoodandAgriculture FeedandGrainTerminalElevators CrossflowDryer",
    "30200522":
        "IndustrialProcesses FoodandAgriculture FeedandGrainTerminalElevators CounterflowDryer",
    "30200526":
        "IndustrialProcesses FoodandAgriculture FeedandGrainTerminalElevators General",
    "30200527":
        "IndustrialProcesses FoodandAgriculture FeedandGrainTerminalElevators GrainDryingColumnDryer",
    "30200528":
        "IndustrialProcesses FoodandAgriculture FeedandGrainTerminalElevators GrainDryingRackDryer",
    "30200530":
        "IndustrialProcesses FoodandAgriculture FeedandGrainTerminalElevators Headhouse&InternalHandlinglegsbeltsdistributorsscaleetc.",
    "30200531":
        "IndustrialProcesses FoodandAgriculture FeedandGrainTerminalElevators FugitiveEmissionsGeneral",
    "30200532":
        "IndustrialProcesses FoodandAgriculture FeedandGrainTerminalElevators FugitiveEmissionsShippingReceiving",
    "30200537":
        "IndustrialProcesses FoodandAgriculture FeedandGrainTerminalElevators GrainCleaningInternalVibrating",
    "30200538":
        "IndustrialProcesses FoodandAgriculture FeedandGrainTerminalElevators GrainCleaningStationaryEnclosed",
    "30200540":
        "IndustrialProcesses FoodandAgriculture FeedandGrainTerminalElevators StorageBinVents",
    "30200550":
        "IndustrialProcesses FoodandAgriculture FeedandGrainTerminalElevators UnloadingReceivingfromTrucksunspecifiedtype",
    "30200551":
        "IndustrialProcesses FoodandAgriculture FeedandGrainTerminalElevators UnloadingReceivingfromStraightTrucks",
    "30200552":
        "IndustrialProcesses FoodandAgriculture FeedandGrainTerminalElevators UnloadingReceivingfromHopperTrucks",
    "30200553":
        "IndustrialProcesses FoodandAgriculture FeedandGrainTerminalElevators UnloadingReceivingfromRailcars",
    "30200554":
        "IndustrialProcesses FoodandAgriculture FeedandGrainTerminalElevators UnloadingReceivingfromBargesUnspecifiedsee56and57",
    "30200555":
        "IndustrialProcesses FoodandAgriculture FeedandGrainTerminalElevators UnloadingReceivingfromShips",
    "30200556":
        "IndustrialProcesses FoodandAgriculture FeedandGrainTerminalElevators UnloadingReceivingfromBargesContinuousBargeUnloader",
    "30200557":
        "IndustrialProcesses FoodandAgriculture FeedandGrainTerminalElevators UnloadingReceivingfromBargesMarineLeg",
    "30200560":
        "IndustrialProcesses FoodandAgriculture FeedandGrainTerminalElevators LoadingShippingintoTrucksunspecifiedtype",
    "30200561":
        "IndustrialProcesses FoodandAgriculture FeedandGrainTerminalElevators LoadingShippingintoStraightTrucks",
    "30200562":
        "IndustrialProcesses FoodandAgriculture FeedandGrainTerminalElevators LoadingShippingintoHopperTrucks",
    "30200563":
        "IndustrialProcesses FoodandAgriculture FeedandGrainTerminalElevators LoadingShippingintoRailcars",
    "30200564":
        "IndustrialProcesses FoodandAgriculture FeedandGrainTerminalElevators LoadingShippingintoBarges",
    "30200565":
        "IndustrialProcesses FoodandAgriculture FeedandGrainTerminalElevators LoadingShippingintoShips",
    "30200601":
        "IndustrialProcesses FoodandAgriculture FeedandGrainCountryElevators ShippingReceiving",
    "30200602":
        "IndustrialProcesses FoodandAgriculture FeedandGrainCountryElevators TransferConvey",
    "30200603":
        "IndustrialProcesses FoodandAgriculture FeedandGrainCountryElevators Cleaning",
    "30200604":
        "IndustrialProcesses FoodandAgriculture FeedandGrainCountryElevators Drying",
    "30200605":
        "IndustrialProcesses FoodandAgriculture FeedandGrainCountryElevators UnloadingReceiving",
    "30200606":
        "IndustrialProcesses FoodandAgriculture FeedandGrainCountryElevators LoadingShipping",
    "30200607":
        "IndustrialProcesses FoodandAgriculture FeedandGrainCountryElevators RemovalfromBinsTunnelBelt",
    "30200608":
        "IndustrialProcesses FoodandAgriculture FeedandGrainCountryElevators ElevatorLegsHeadhouse",
    "30200609":
        "IndustrialProcesses FoodandAgriculture FeedandGrainCountryElevators TripperGalleryBelt",
    "30200699":
        "IndustrialProcesses FoodandAgriculture FeedandGrainCountryElevators General",
    "30200703":
        "IndustrialProcesses FoodandAgriculture GrainMillings BarleyCleaning",
    "30200705":
        "IndustrialProcesses FoodandAgriculture GrainMillings BarleyFlourMill",
    "30200706":
        "IndustrialProcesses FoodandAgriculture GrainMillings BarleyReceiving",
    "30200708":
        "IndustrialProcesses FoodandAgriculture GrainMillings BarleyMaltingGrainReceiving",
    "30200709":
        "IndustrialProcesses FoodandAgriculture GrainMillings BarleyMaltingGasfiredMaltKiln",
    "30200710":
        "IndustrialProcesses FoodandAgriculture GrainMillings MiloReceiving",
    "30200711":
        "IndustrialProcesses FoodandAgriculture GrainMillings DurumMillingGrainReceiving",
    "30200712":
        "IndustrialProcesses FoodandAgriculture GrainMillings DurumMillingPrecleaningHandling",
    "30200713":
        "IndustrialProcesses FoodandAgriculture GrainMillings DurumMillingCleaningHouse",
    "30200714":
        "IndustrialProcesses FoodandAgriculture GrainMillings DurumMillingMillhouse",
    "30200721":
        "IndustrialProcesses FoodandAgriculture GrainMillings RyeGrainReceiving",
    "30200722":
        "IndustrialProcesses FoodandAgriculture GrainMillings RyePrecleaningHandling",
    "30200724":
        "IndustrialProcesses FoodandAgriculture GrainMillings RyeMillhouse",
    "30200730":
        "IndustrialProcesses FoodandAgriculture GrainMillings General",
    "30200731":
        "IndustrialProcesses FoodandAgriculture GrainMillings WheatGrainReceiving",
    "30200732":
        "IndustrialProcesses FoodandAgriculture GrainMillings WheatPrecleaningHandling",
    "30200733":
        "IndustrialProcesses FoodandAgriculture GrainMillings WheatCleaningHouse",
    "30200734":
        "IndustrialProcesses FoodandAgriculture GrainMillings WheatMillhouse",
    "30200740":
        "IndustrialProcesses FoodandAgriculture GrainMillings DryCornMillingSiloStorage",
    "30200741":
        "IndustrialProcesses FoodandAgriculture GrainMillings DryCornMillingGrainReceiving",
    "30200742":
        "IndustrialProcesses FoodandAgriculture GrainMillings DryCornMillingGrainDrying",
    "30200743":
        "IndustrialProcesses FoodandAgriculture GrainMillings DryCornMillingPrecleaningHandling",
    "30200744":
        "IndustrialProcesses FoodandAgriculture GrainMillings DryCornMillingCleaningHouse",
    "30200745":
        "IndustrialProcesses FoodandAgriculture GrainMillings DryCornMillingDegermingandMilling",
    "30200746":
        "IndustrialProcesses FoodandAgriculture GrainMillings DryCornMillingBulkLoading",
    "30200747":
        "IndustrialProcesses FoodandAgriculture GrainMillings DryCornMillingPneumaticConveyor",
    "30200748":
        "IndustrialProcesses FoodandAgriculture GrainMillings DryCornMillingGrinding",
    "30200751":
        "IndustrialProcesses FoodandAgriculture GrainMillings WetCornMillingGrainReceiving",
    "30200752":
        "IndustrialProcesses FoodandAgriculture GrainMillings WetCornMillingGrainHandling",
    "30200753":
        "IndustrialProcesses FoodandAgriculture GrainMillings WetCornMillingGrainCleaning",
    "30200754":
        "IndustrialProcesses FoodandAgriculture GrainMillings WetCornMillingDryers",
    "30200755":
        "IndustrialProcesses FoodandAgriculture GrainMillings WetCornMillingBulkLoading",
    "30200756":
        "IndustrialProcesses FoodandAgriculture GrainMillings WetCornMillingMilling",
    "30200757":
        "IndustrialProcesses FoodandAgriculture GrainMillings DryCornMillingMixingTank",
    "30200759":
        "IndustrialProcesses FoodandAgriculture GrainMillings DryCornMillingKettleCooker",
    "30200760":
        "IndustrialProcesses FoodandAgriculture GrainMillings OatGeneral",
    "30200761":
        "IndustrialProcesses FoodandAgriculture GrainMillings SteepingGrainConditioninginTanksContainingDiluteSulfurousAcid",
    "30200762":
        "IndustrialProcesses FoodandAgriculture GrainMillings EvaporatorsConcentrateSteepwaterto3055%SolidsbyEvaporation",
    "30200763":
        "IndustrialProcesses FoodandAgriculture GrainMillings GlutenFeedDryingDirectfiredDryerProducesCornGlutenFeed",
    "30200764":
        "IndustrialProcesses FoodandAgriculture GrainMillings GlutenFeedDryingIndirectfiredDryerProducesCornGlutenFeed",
    "30200765":
        "IndustrialProcesses FoodandAgriculture GrainMillings DegerminatingMillsSeparatesGermfromStarchandGluten",
    "30200766":
        "IndustrialProcesses FoodandAgriculture GrainMillings GermDryingDryingGermfromDegerminatingMills",
    "30200767":
        "IndustrialProcesses FoodandAgriculture GrainMillings FiberDryingDryingCornHullsafterSeparationfromStarch&Gluten",
    "30200768":
        "IndustrialProcesses FoodandAgriculture GrainMillings GlutenDryingDirectfiredDryerProducesCornGlutenMeal",
    "30200769":
        "IndustrialProcesses FoodandAgriculture GrainMillings GlutenDryingIndirectfiredDryerProducesCornGlutenMeal",
    "30200770":
        "IndustrialProcesses FoodandAgriculture GrainMillings DextroseDrying",
    "30200771":
        "IndustrialProcesses FoodandAgriculture GrainMillings RiceGrainReceiving",
    "30200772":
        "IndustrialProcesses FoodandAgriculture GrainMillings RicePrecleaningHandling",
    "30200773":
        "IndustrialProcesses FoodandAgriculture GrainMillings RiceDrying",
    "30200774":
        "IndustrialProcesses FoodandAgriculture GrainMillings RiceCleaningMillhouse",
    "30200776":
        "IndustrialProcesses FoodandAgriculture GrainMillings RiceMillHouse",
    "30200777":
        "IndustrialProcesses FoodandAgriculture GrainMillings RiceAspirator",
    "30200781":
        "IndustrialProcesses FoodandAgriculture GrainMillings SoybeanGrainReceiving",
    "30200782":
        "IndustrialProcesses FoodandAgriculture GrainMillings SoybeanGrainHandling",
    "30200783":
        "IndustrialProcesses FoodandAgriculture GrainMillings SoybeanGrainCleaning",
    "30200784":
        "IndustrialProcesses FoodandAgriculture GrainMillings SoybeanDrying",
    "30200785":
        "IndustrialProcesses FoodandAgriculture GrainMillings SoybeanCrackingandDehulling",
    "30200786":
        "IndustrialProcesses FoodandAgriculture GrainMillings SoybeanHullGrinding",
    "30200787":
        "IndustrialProcesses FoodandAgriculture GrainMillings SoybeanBeanConditioning",
    "30200788":
        "IndustrialProcesses FoodandAgriculture GrainMillings SoybeanFlaking",
    "30200789":
        "IndustrialProcesses FoodandAgriculture GrainMillings SoybeanMealDryer",
    "30200790":
        "IndustrialProcesses FoodandAgriculture GrainMillings SoybeanMealCooler",
    "30200791":
        "IndustrialProcesses FoodandAgriculture GrainMillings SoybeanBulkLoading",
    "30200792":
        "IndustrialProcesses FoodandAgriculture GrainMillings SoybeanWhiteFlakeCooler",
    "30200793":
        "IndustrialProcesses FoodandAgriculture GrainMillings SoybeanMealGrinderSizing",
    "30200799":
        "IndustrialProcesses FoodandAgriculture GrainMillings SeeComment",
    "30200801":
        "IndustrialProcesses FoodandAgriculture FeedManufacture General",
    "30200802":
        "IndustrialProcesses FoodandAgriculture FeedManufacture GrainReceiving",
    "30200803":
        "IndustrialProcesses FoodandAgriculture FeedManufacture Shipping",
    "30200804":
        "IndustrialProcesses FoodandAgriculture FeedManufacture Handling",
    "30200805":
        "IndustrialProcesses FoodandAgriculture FeedManufacture Grinding",
    "30200806":
        "IndustrialProcesses FoodandAgriculture FeedManufacture PelletCoolers",
    "30200807":
        "IndustrialProcesses FoodandAgriculture FeedManufacture GrainCleaning",
    "30200808":
        "IndustrialProcesses FoodandAgriculture FeedManufacture Milling",
    "30200809":
        "IndustrialProcesses FoodandAgriculture FeedManufacture MixingBlending",
    "30200810":
        "IndustrialProcesses FoodandAgriculture FeedManufacture Conveying",
    "30200811":
        "IndustrialProcesses FoodandAgriculture FeedManufacture Scalping",
    "30200812":
        "IndustrialProcesses FoodandAgriculture FeedManufacture BulkLoadout",
    "30200813":
        "IndustrialProcesses FoodandAgriculture FeedManufacture Shaking",
    "30200814":
        "IndustrialProcesses FoodandAgriculture FeedManufacture Storage",
    "30200815":
        "IndustrialProcesses FoodandAgriculture FeedManufacture Grinding",
    "30200816":
        "IndustrialProcesses FoodandAgriculture FeedManufacture PelletCooler",
    "30200817":
        "IndustrialProcesses FoodandAgriculture FeedManufacture GrainMillingHammermill",
    "30200818":
        "IndustrialProcesses FoodandAgriculture FeedManufacture GrainMillingFlaker",
    "30200819":
        "IndustrialProcesses FoodandAgriculture FeedManufacture GrainMillingGrainCracker",
    "30200821":
        "IndustrialProcesses FoodandAgriculture FeedManufacture FugitiveEmissionsGeneral",
    "30200822":
        "IndustrialProcesses FoodandAgriculture FeedManufacture FugitiveEmissionsShippingReceiving",
    "30200823":
        "IndustrialProcesses FoodandAgriculture FeedManufacture FugitiveEmissionsPacking",
    "30200832":
        "IndustrialProcesses FoodandAgriculture FeedManufacture CitrateHandlingTransferring",
    "30200833":
        "IndustrialProcesses FoodandAgriculture FeedManufacture CitrateGrinding",
    "30200834":
        "IndustrialProcesses FoodandAgriculture FeedManufacture CitrateDrying",
    "30200835":
        "IndustrialProcesses FoodandAgriculture FeedManufacture CitrateStorage",
    "30200899":
        "IndustrialProcesses FoodandAgriculture FeedManufacture NotClassified",
    "30200901":
        "IndustrialProcesses FoodandAgriculture BeerProduction GrainHandlingseealso302005xx",
    "30200902":
        "IndustrialProcesses FoodandAgriculture BeerProduction DryingSpentGrainsuseSCCs30200930&31",
    "30200903":
        "IndustrialProcesses FoodandAgriculture BeerProduction BrewKettleuseSCC30200907",
    "30200904":
        "IndustrialProcesses FoodandAgriculture BeerProduction AgingTankSecondaryFermentation",
    "30200905":
        "IndustrialProcesses FoodandAgriculture BeerProduction MaltKiln",
    "30200906":
        "IndustrialProcesses FoodandAgriculture BeerProduction MaltMill",
    "30200907":
        "IndustrialProcesses FoodandAgriculture BeerProduction BrewKettle",
    "30200908":
        "IndustrialProcesses FoodandAgriculture BeerProduction AgingTankFilling",
    "30200910":
        "IndustrialProcesses FoodandAgriculture BeerProduction BeerBottlingStorage",
    "30200911":
        "IndustrialProcesses FoodandAgriculture BeerProduction FugitiveEmissionsGeneral",
    "30200915":
        "IndustrialProcesses FoodandAgriculture BeerProduction MilledMaltHopper",
    "30200920":
        "IndustrialProcesses FoodandAgriculture BeerProduction RawMaterialStorage",
    "30200921":
        "IndustrialProcesses FoodandAgriculture BeerProduction MashTun",
    "30200922":
        "IndustrialProcesses FoodandAgriculture BeerProduction CerealCooker",
    "30200923":
        "IndustrialProcesses FoodandAgriculture BeerProduction LauterTunorStrainmaster",
    "30200924":
        "IndustrialProcesses FoodandAgriculture BeerProduction HotWortSettlingTank",
    "30200925":
        "IndustrialProcesses FoodandAgriculture BeerProduction WortCooler",
    "30200926":
        "IndustrialProcesses FoodandAgriculture BeerProduction TrubVessel",
    "30200930":
        "IndustrialProcesses FoodandAgriculture BeerProduction BrewersGrainDryerNaturalGasfired",
    "30200932":
        "IndustrialProcesses FoodandAgriculture BeerProduction BrewersGrainDryerSteamheated",
    "30200935":
        "IndustrialProcesses FoodandAgriculture BeerProduction FermenterVentingClosedFermenter",
    "30200937":
        "IndustrialProcesses FoodandAgriculture BeerProduction FermenterVentingOpenFermenter",
    "30200939":
        "IndustrialProcesses FoodandAgriculture BeerProduction ActivatedCarbonRegeneration",
    "30200940":
        "IndustrialProcesses FoodandAgriculture BeerProduction BrewersYeastDisposal",
    "30200941":
        "IndustrialProcesses FoodandAgriculture BeerProduction YeastPropagation",
    "30200951":
        "IndustrialProcesses FoodandAgriculture BeerProduction CanFillingLine",
    "30200952":
        "IndustrialProcesses FoodandAgriculture BeerProduction SterilizedCanFillingLine",
    "30200953":
        "IndustrialProcesses FoodandAgriculture BeerProduction BottleFillingLine",
    "30200954":
        "IndustrialProcesses FoodandAgriculture BeerProduction SterilizedBottleFillingLine",
    "30200955":
        "IndustrialProcesses FoodandAgriculture BeerProduction KegFillingLine",
    "30200960":
        "IndustrialProcesses FoodandAgriculture BeerProduction BottleSoakerandCleaner",
    "30200961":
        "IndustrialProcesses FoodandAgriculture BeerProduction BottleCrusher",
    "30200962":
        "IndustrialProcesses FoodandAgriculture BeerProduction CanCrusherwithPneumaticConveyor",
    "30200963":
        "IndustrialProcesses FoodandAgriculture BeerProduction BeerSump",
    "30200964":
        "IndustrialProcesses FoodandAgriculture BeerProduction WasteBeerRecovery",
    "30200965":
        "IndustrialProcesses FoodandAgriculture BeerProduction WasteBeerStorageTanks",
    "30200966":
        "IndustrialProcesses FoodandAgriculture BeerProduction EthanolRemovalfromWasteBeer",
    "30200967":
        "IndustrialProcesses FoodandAgriculture BeerProduction EthanolRecoveryfromWasteBeer",
    "30200998":
        "IndustrialProcesses FoodandAgriculture BeerProduction OtherNotClassified",
    "30201001":
        "IndustrialProcesses FoodandAgriculture DistilledSpirits GrainHandlingsee30200605",
    "30201002":
        "IndustrialProcesses FoodandAgriculture DistilledSpirits DryerHouseOperations",
    "30201003":
        "IndustrialProcesses FoodandAgriculture DistilledSpirits Agingsee30201017",
    "30201004":
        "IndustrialProcesses FoodandAgriculture DistilledSpirits FermentationTanksee30201014",
    "30201005":
        "IndustrialProcesses FoodandAgriculture DistilledSpirits MaltMilling",
    "30201006":
        "IndustrialProcesses FoodandAgriculture DistilledSpirits MaltDrying",
    "30201010":
        "IndustrialProcesses FoodandAgriculture DistilledSpirits WhiskeyBottlingStoragesee30201018",
    "30201011":
        "IndustrialProcesses FoodandAgriculture DistilledSpirits FugitiveEmissionsGeneral",
    "30201013":
        "IndustrialProcesses FoodandAgriculture DistilledSpirits WhiskeyGrainMashing",
    "30201014":
        "IndustrialProcesses FoodandAgriculture DistilledSpirits WhiskeyFermentationTank",
    "30201015":
        "IndustrialProcesses FoodandAgriculture DistilledSpirits WhiskeyDistillation",
    "30201017":
        "IndustrialProcesses FoodandAgriculture DistilledSpirits WhiskeyAgingEvaporationLoss",
    "30201018":
        "IndustrialProcesses FoodandAgriculture DistilledSpirits WhiskeyBlendingBottling",
    "30201020":
        "IndustrialProcesses FoodandAgriculture DistilledSpirits RawMaterialStorage",
    "30201099":
        "IndustrialProcesses FoodandAgriculture DistilledSpirits OtherNotClassified",
    "30201103":
        "IndustrialProcesses FoodandAgriculture WinesBrandyandBrandySpirits Aging",
    "30201104":
        "IndustrialProcesses FoodandAgriculture WinesBrandyandBrandySpirits FermentationTank",
    "30201105":
        "IndustrialProcesses FoodandAgriculture WinesBrandyandBrandySpirits WineFermentationWhiteWine",
    "30201106":
        "IndustrialProcesses FoodandAgriculture WinesBrandyandBrandySpirits WineFermentationRedWine",
    "30201110":
        "IndustrialProcesses FoodandAgriculture WinesBrandyandBrandySpirits WineBottlingStorage",
    "30201120":
        "IndustrialProcesses FoodandAgriculture WinesBrandyandBrandySpirits RawMaterialStorage",
    "30201199":
        "IndustrialProcesses FoodandAgriculture WinesBrandyandBrandySpirits OtherNotClassified",
    "30201202":
        "IndustrialProcesses FoodandAgriculture FishProcessing CookersStaleFishScrap",
    "30201203":
        "IndustrialProcesses FoodandAgriculture FishProcessing Dryers",
    "30201204":
        "IndustrialProcesses FoodandAgriculture FishProcessing CanningCookers",
    "30201205":
        "IndustrialProcesses FoodandAgriculture FishProcessing SteamTubeDryer",
    "30201206":
        "IndustrialProcesses FoodandAgriculture FishProcessing DirectFiredDryer",
    "30201299":
        "IndustrialProcesses FoodandAgriculture FishProcessing OtherNotClassified",
    "30201301":
        "IndustrialProcesses FoodandAgriculture MeatSmokehouses CombinedOperations",
    "30201302":
        "IndustrialProcesses FoodandAgriculture MeatSmokehouses BatchSmokehousesSmokingCycle",
    "30201303":
        "IndustrialProcesses FoodandAgriculture MeatSmokehouses BatchSmokehousesCookingCycle",
    "30201304":
        "IndustrialProcesses FoodandAgriculture MeatSmokehouses ContinuousSmokehouseSmokeZone",
    "30201305":
        "IndustrialProcesses FoodandAgriculture MeatSmokehouses ContinuousSmokehouseHeatZone",
    "30201311":
        "IndustrialProcesses FoodandAgriculture MeatSmokehouses MeatCharbroiler",
    "30201401":
        "IndustrialProcesses FoodandAgriculture StarchManufacturing CombinedOperations",
    "30201402":
        "IndustrialProcesses FoodandAgriculture StarchManufacturing SteepingAcidification",
    "30201403":
        "IndustrialProcesses FoodandAgriculture StarchManufacturing Grinding",
    "30201404":
        "IndustrialProcesses FoodandAgriculture StarchManufacturing Screening",
    "30201405":
        "IndustrialProcesses FoodandAgriculture StarchManufacturing Centrifuging",
    "30201406":
        "IndustrialProcesses FoodandAgriculture StarchManufacturing StarchFiltering",
    "30201407":
        "IndustrialProcesses FoodandAgriculture StarchManufacturing StarchStorageBin",
    "30201408":
        "IndustrialProcesses FoodandAgriculture StarchManufacturing StarchBulkLoadout",
    "30201410":
        "IndustrialProcesses FoodandAgriculture StarchManufacturing ModifiedStarchDryingFlashDryers",
    "30201411":
        "IndustrialProcesses FoodandAgriculture StarchManufacturing ModifiedStarchDryingSprayDryers",
    "30201412":
        "IndustrialProcesses FoodandAgriculture StarchManufacturing UnmodifiedStarchDryingFlashDryers",
    "30201413":
        "IndustrialProcesses FoodandAgriculture StarchManufacturing UnmodifiedStarchDryingSprayDryers",
    "30201421":
        "IndustrialProcesses FoodandAgriculture StarchManufacturing FugitiveEmissionsGeneral",
    "30201422":
        "IndustrialProcesses FoodandAgriculture StarchManufacturing FugitiveEmissionsStarchPackaging",
    "30201501":
        "IndustrialProcesses FoodandAgriculture SugarCaneRefining General",
    "30201507":
        "IndustrialProcesses FoodandAgriculture SugarCaneRefining VacuumPans",
    "30201510":
        "IndustrialProcesses FoodandAgriculture SugarCaneRefining CaneSugarDryer",
    "30201512":
        "IndustrialProcesses FoodandAgriculture SugarCaneRefining BulkSugarStorage",
    "30201514":
        "IndustrialProcesses FoodandAgriculture SugarCaneRefining BulkSugarLoadout",
    "30201521":
        "IndustrialProcesses FoodandAgriculture SugarCaneRefining ClarificationCarbonation",
    "30201525":
        "IndustrialProcesses FoodandAgriculture SugarCaneRefining AdsorbentRegeneration",
    "30201526":
        "IndustrialProcesses FoodandAgriculture SugarCaneRefining AdsorbentConveyorTransfer",
    "30201535":
        "IndustrialProcesses FoodandAgriculture SugarCaneRefining SugarDryer",
    "30201536":
        "IndustrialProcesses FoodandAgriculture SugarCaneRefining SugarCooler",
    "30201537":
        "IndustrialProcesses FoodandAgriculture SugarCaneRefining SugarGranulatorDryer&Cooler",
    "30201540":
        "IndustrialProcesses FoodandAgriculture SugarCaneRefining Screen",
    "30201542":
        "IndustrialProcesses FoodandAgriculture SugarCaneRefining SugarStorageandPackaging",
    "30201544":
        "IndustrialProcesses FoodandAgriculture SugarCaneRefining BulkLoadout",
    "30201599":
        "IndustrialProcesses FoodandAgriculture SugarCaneRefining OtherNotClassified",
    "30201601":
        "IndustrialProcesses FoodandAgriculture SugarBeetProcessing PulpDryerCoalfired",
    "30201605":
        "IndustrialProcesses FoodandAgriculture SugarBeetProcessing PulpDryerOilfired",
    "30201608":
        "IndustrialProcesses FoodandAgriculture SugarBeetProcessing PulpDryerNaturalGasfired",
    "30201612":
        "IndustrialProcesses FoodandAgriculture SugarBeetProcessing DriedPulpPelletizer",
    "30201616":
        "IndustrialProcesses FoodandAgriculture SugarBeetProcessing DriedPulpPelletCooler",
    "30201621":
        "IndustrialProcesses FoodandAgriculture SugarBeetProcessing FirstCarbonationTank",
    "30201631":
        "IndustrialProcesses FoodandAgriculture SugarBeetProcessing SulfurStoveContactingTower",
    "30201641":
        "IndustrialProcesses FoodandAgriculture SugarBeetProcessing FirstEffectEvaporatorVent",
    "30201651":
        "IndustrialProcesses FoodandAgriculture SugarBeetProcessing SugarDryer",
    "30201655":
        "IndustrialProcesses FoodandAgriculture SugarBeetProcessing SugarCooler",
    "30201658":
        "IndustrialProcesses FoodandAgriculture SugarBeetProcessing SugarGranulatorDryer&Cooler",
    "30201661":
        "IndustrialProcesses FoodandAgriculture SugarBeetProcessing SugarConveyingandSacking",
    "30201682":
        "IndustrialProcesses FoodandAgriculture SugarBeetProcessing LimeCrusher",
    "30201684":
        "IndustrialProcesses FoodandAgriculture SugarBeetProcessing LimeKilnCoalfired",
    "30201686":
        "IndustrialProcesses FoodandAgriculture SugarBeetProcessing LimeKilnNaturalGasfired",
    "30201688":
        "IndustrialProcesses FoodandAgriculture SugarBeetProcessing LimeSlaker",
    "30201699":
        "IndustrialProcesses FoodandAgriculture SugarBeetProcessing OtherNotClassified",
    "30201701":
        "IndustrialProcesses FoodandAgriculture PeanutProcessing LoadingUnloading",
    "30201702":
        "IndustrialProcesses FoodandAgriculture PeanutProcessing Cleaning",
    "30201703":
        "IndustrialProcesses FoodandAgriculture PeanutProcessing Shelling",
    "30201704":
        "IndustrialProcesses FoodandAgriculture PeanutProcessing Milling",
    "30201705":
        "IndustrialProcesses FoodandAgriculture PeanutProcessing Dryer",
    "30201711":
        "IndustrialProcesses FoodandAgriculture PeanutProcessing UnloadingofAlmondstoReceivingPit",
    "30201712":
        "IndustrialProcesses FoodandAgriculture PeanutProcessing PrecleaningofOrchardDebrisfromAlmonds",
    "30201713":
        "IndustrialProcesses FoodandAgriculture PeanutProcessing HullRemovalandSeparationfromInshellAlmonds",
    "30201714":
        "IndustrialProcesses FoodandAgriculture PeanutProcessing HullingandShellingofAlmondsHullerSheller",
    "30201715":
        "IndustrialProcesses FoodandAgriculture PeanutProcessing ClassifierScreenDecktoRemoveShellfromMeats",
    "30201716":
        "IndustrialProcesses FoodandAgriculture PeanutProcessing AirLegtoSeparateShellsfromMeats",
    "30201717":
        "IndustrialProcesses FoodandAgriculture PeanutProcessing AlmondRoasterDirectfiredRotatingDrum",
    "30201799":
        "IndustrialProcesses FoodandAgriculture PeanutProcessing OtherNotClassified",
    "30201899":
        "IndustrialProcesses FoodandAgriculture CandyManufacturing OtherNotClassified",
    "30201902":
        "IndustrialProcesses FoodandAgriculture VegetableOilProcessing CottonseedOilGeneral",
    "30201906":
        "IndustrialProcesses FoodandAgriculture VegetableOilProcessing CornOilGeneral",
    "30201916":
        "IndustrialProcesses FoodandAgriculture VegetableOilProcessing OilExtraction",
    "30201917":
        "IndustrialProcesses FoodandAgriculture VegetableOilProcessing MealPreparation",
    "30201918":
        "IndustrialProcesses FoodandAgriculture VegetableOilProcessing OilRefining",
    "30201919":
        "IndustrialProcesses FoodandAgriculture VegetableOilProcessing FugitiveLeaks",
    "30201920":
        "IndustrialProcesses FoodandAgriculture VegetableOilProcessing SolventStorageUse40701615&16or40717603&04",
    "30201921":
        "IndustrialProcesses FoodandAgriculture VegetableOilProcessing SolventWorkTank",
    "30201925":
        "IndustrialProcesses FoodandAgriculture VegetableOilProcessing OilExtractionRotaryCellExtractor",
    "30201927":
        "IndustrialProcesses FoodandAgriculture VegetableOilProcessing OilExtractionContinuousShallowbedRectangularLoopNoBaskets",
    "30201930":
        "IndustrialProcesses FoodandAgriculture VegetableOilProcessing MealPreparationDesolventizerToaster",
    "30201931":
        "IndustrialProcesses FoodandAgriculture VegetableOilProcessing MealPreparationDryer",
    "30201932":
        "IndustrialProcesses FoodandAgriculture VegetableOilProcessing MealPreparationCooler",
    "30201933":
        "IndustrialProcesses FoodandAgriculture VegetableOilProcessing MealPreparationPneumaticConveyor",
    "30201935":
        "IndustrialProcesses FoodandAgriculture VegetableOilProcessing MealPreparationScreeningandGrinding",
    "30201939":
        "IndustrialProcesses FoodandAgriculture VegetableOilProcessing MealStorageTanks",
    "30201941":
        "IndustrialProcesses FoodandAgriculture VegetableOilProcessing OilRefiningMiscellaneousHoldingTank",
    "30201942":
        "IndustrialProcesses FoodandAgriculture VegetableOilProcessing OilRefiningEvaporators",
    "30201949":
        "IndustrialProcesses FoodandAgriculture VegetableOilProcessing CrudeOilStorageTanks",
    "30201950":
        "IndustrialProcesses FoodandAgriculture VegetableOilProcessing SolventWaterSeparator",
    "30201960":
        "IndustrialProcesses FoodandAgriculture VegetableOilProcessing WastewaterEvaporator",
    "30201997":
        "IndustrialProcesses FoodandAgriculture VegetableOilProcessing SoybeanOilProductionCompleteProcessSolventLossPlantspecific",
    "30201998":
        "IndustrialProcesses FoodandAgriculture VegetableOilProcessing SoybeanOilProductionCompleteProcessSolventLossaverage",
    "30201999":
        "IndustrialProcesses FoodandAgriculture VegetableOilProcessing OtherNotClassified",
    "30202001":
        "IndustrialProcesses FoodandAgriculture CattleManagement BeefCattleFeedlotsFeedlotsGeneral",
    "30202020":
        "IndustrialProcesses FoodandAgriculture CattleManagement DairyCattleEntericConfinementManureHandlingStorageLandApplication",
    "30202070":
        "IndustrialProcesses FoodandAgriculture CattleManagement SilagepileAFOStorageandHandling",
    "30202080":
        "IndustrialProcesses FoodandAgriculture CattleManagement SilageTMRAFOStorageandHandling",
    "30202101":
        "IndustrialProcesses FoodandAgriculture NoncattleLivestockManagement EggsandPoultryProductionManureHandlingDry",
    "30202120":
        "IndustrialProcesses FoodandAgriculture NoncattleLivestockManagement BroilersEntericConfinementManureHandlingStorageLandApplication",
    "30202201":
        "IndustrialProcesses FoodandAgriculture CottonSeedDelinting AcidDelintingofCottonSeeds",
    "30202601":
        "IndustrialProcesses FoodandAgriculture SeedProductsandProcessing SeedHandlingGeneral",
    "30202801":
        "IndustrialProcesses FoodandAgriculture MushroomGrowing General",
    "30203001":
        "IndustrialProcesses FoodandAgriculture DairyProducts MilkSprayDryer",
    "30203010":
        "IndustrialProcesses FoodandAgriculture DairyProducts WheyDryer",
    "30203020":
        "IndustrialProcesses FoodandAgriculture DairyProducts CheeseDryer",
    "30203099":
        "IndustrialProcesses FoodandAgriculture DairyProducts OtherNotClassified",
    "30203103":
        "IndustrialProcesses FoodandAgriculture ExportGrainElevators Cleaning",
    "30203104":
        "IndustrialProcesses FoodandAgriculture ExportGrainElevators Drying",
    "30203105":
        "IndustrialProcesses FoodandAgriculture ExportGrainElevators Unloading",
    "30203106":
        "IndustrialProcesses FoodandAgriculture ExportGrainElevators Loading",
    "30203107":
        "IndustrialProcesses FoodandAgriculture ExportGrainElevators RemovalfromBinsTunnelBelt",
    "30203108":
        "IndustrialProcesses FoodandAgriculture ExportGrainElevators ElevatorLegsHeadhouse",
    "30203109":
        "IndustrialProcesses FoodandAgriculture ExportGrainElevators TripperGalleryBelt",
    "30203201":
        "IndustrialProcesses FoodandAgriculture Bakeries BreadBakingSpongeDoughProcess",
    "30203202":
        "IndustrialProcesses FoodandAgriculture Bakeries BreadBakingStraightDoughProcess",
    "30203203":
        "IndustrialProcesses FoodandAgriculture Bakeries MaterialHandlingandTransferring",
    "30203204":
        "IndustrialProcesses FoodandAgriculture Bakeries FlourStorage",
    "30203205":
        "IndustrialProcesses FoodandAgriculture Bakeries CrackerandCookieBaking",
    "30203299":
        "IndustrialProcesses FoodandAgriculture Bakeries OtherNotClassified",
    "30203399":
        "IndustrialProcesses FoodandAgriculture TobaccoProcessing OtherNotClassified",
    "30203404":
        "IndustrialProcesses FoodandAgriculture BakersYeastManufacturingDryYeast IntermediateFermentorF4Stage",
    "30203405":
        "IndustrialProcesses FoodandAgriculture BakersYeastManufacturingDryYeast StockFermentorF5Stage",
    "30203406":
        "IndustrialProcesses FoodandAgriculture BakersYeastManufacturingDryYeast PitchFermentorF6Stage",
    "30203407":
        "IndustrialProcesses FoodandAgriculture BakersYeastManufacturingDryYeast TradeFermentorF7Stage",
    "30203410":
        "IndustrialProcesses FoodandAgriculture BakersYeastManufacturingDryYeast WastewaterTreatment",
    "30203420":
        "IndustrialProcesses FoodandAgriculture BakersYeastManufacturingDryYeast Dryer",
    "30203421":
        "IndustrialProcesses FoodandAgriculture BakersYeastManufacturingDryYeast DryingChamber",
    "30203424":
        "IndustrialProcesses FoodandAgriculture BakersYeastManufacturingDryYeast AirliftDryerContinuousProcess",
    "30203504":
        "IndustrialProcesses FoodandAgriculture BakersYeastManufacturingCompressedYeast IntermediateFermentorF4Stage",
    "30203505":
        "IndustrialProcesses FoodandAgriculture BakersYeastManufacturingCompressedYeast StockFermentorF5Stage",
    "30203506":
        "IndustrialProcesses FoodandAgriculture BakersYeastManufacturingCompressedYeast PitchFermentorF6Stage",
    "30203507":
        "IndustrialProcesses FoodandAgriculture BakersYeastManufacturingCompressedYeast TradeFermentorF7Stage",
    "30203531":
        "IndustrialProcesses FoodandAgriculture BakersYeastManufacturingCompressedYeast HarvestingCentrifuge",
    "30203601":
        "IndustrialProcesses FoodandAgriculture DeepFatFrying ContinuousDeepFatFryerPotatoChips",
    "30203602":
        "IndustrialProcesses FoodandAgriculture DeepFatFrying ContinuousDeepFatFryerOtherSnackChips",
    "30203603":
        "IndustrialProcesses FoodandAgriculture DeepFatFrying BatchDeepFatFryerPotatoChips",
    "30203604":
        "IndustrialProcesses FoodandAgriculture DeepFatFrying GasfiredToasterSnackChips",
    "30203801":
        "IndustrialProcesses FoodandAgriculture AnimalPoultryRendering General",
    "30203802":
        "IndustrialProcesses FoodandAgriculture AnimalPoultryRendering SizeReduction",
    "30203803":
        "IndustrialProcesses FoodandAgriculture AnimalPoultryRendering Cooking",
    "30203804":
        "IndustrialProcesses FoodandAgriculture AnimalPoultryRendering Storage",
    "30203805":
        "IndustrialProcesses FoodandAgriculture AnimalPoultryRendering MaterialHandling",
    "30203811":
        "IndustrialProcesses FoodandAgriculture AnimalPoultryRendering BloodDryerNaturalGasDirectFired",
    "30203812":
        "IndustrialProcesses FoodandAgriculture AnimalPoultryRendering BloodDryerSteamcoilIndirectHeated",
    "30203901":
        "IndustrialProcesses FoodandAgriculture CarobKibble Roaster",
    "30203902":
        "IndustrialProcesses FoodandAgriculture CarobKibble Receiving",
    "30204001":
        "IndustrialProcesses FoodandAgriculture Cereal Dryer",
    "30204002":
        "IndustrialProcesses FoodandAgriculture Cereal CerealConveying",
    "30204003":
        "IndustrialProcesses FoodandAgriculture Cereal CerealPackaging",
    "30204004":
        "IndustrialProcesses FoodandAgriculture Cereal CerealCoating",
    "30204201":
        "IndustrialProcesses FoodandAgriculture VinegarManufacturing FermentationAlcohol",
    "30204401":
        "IndustrialProcesses FoodandAgriculture CelluloseFoodCasingManufacture OtherNotElsewhereClassified",
    "30204402":
        "IndustrialProcesses FoodandAgriculture CelluloseFoodCasingManufacture Reactor",
    "30204405":
        "IndustrialProcesses FoodandAgriculture CelluloseFoodCasingManufacture Drying",
    "30205010":
        "IndustrialProcesses FoodandAgriculture EthanolProduction Distillation",
    "30205011":
        "IndustrialProcesses FoodandAgriculture EthanolProduction Fermentation",
    "30205012":
        "IndustrialProcesses FoodandAgriculture EthanolProduction StillageDryingDryMillProcess",
    "30205013":
        "IndustrialProcesses FoodandAgriculture EthanolProduction StillageDryingWetMillProcess",
    "30205014":
        "IndustrialProcesses FoodandAgriculture EthanolProduction DDGSCooling",
    "30205020":
        "IndustrialProcesses FoodandAgriculture EthanolProduction NaturalGasCombustionfromDryer",
    "30205021":
        "IndustrialProcesses FoodandAgriculture EthanolProduction NaturalGasCombustionfromThermalOxidizer",
    "30205030":
        "IndustrialProcesses FoodandAgriculture EthanolProduction DenaturedEthanolStorageStandingLoss",
    "30205031":
        "IndustrialProcesses FoodandAgriculture EthanolProduction DenaturedEthanolStorageWorkingLoss",
    "30205032":
        "IndustrialProcesses FoodandAgriculture EthanolProduction E85DenaturedEthanolStorageStandingLoss",
    "30205033":
        "IndustrialProcesses FoodandAgriculture EthanolProduction E85DenaturedEthanolStorageWorkingLoss",
    "30205034":
        "IndustrialProcesses FoodandAgriculture EthanolProduction 200ProofEthanolStorageStandingLoss",
    "30205035":
        "IndustrialProcesses FoodandAgriculture EthanolProduction 200ProofEthanolStorageWorkingLoss",
    "30205038":
        "IndustrialProcesses FoodandAgriculture EthanolProduction 190ProofEthanolStorageStandingLoss",
    "30205039":
        "IndustrialProcesses FoodandAgriculture EthanolProduction 190ProofEthanolStorageWorkingLoss",
    "30205040":
        "IndustrialProcesses FoodandAgriculture EthanolProduction BiomethanatorFlaring",
    "30205041":
        "IndustrialProcesses FoodandAgriculture EthanolProduction VaporRecoveryFromEthanolLoadoutCombustion",
    "30205050":
        "IndustrialProcesses FoodandAgriculture EthanolProduction DDGSLoadouttoTrucks",
    "30205051":
        "IndustrialProcesses FoodandAgriculture EthanolProduction DDGSLoadouttoRailcars",
    "30205052":
        "IndustrialProcesses FoodandAgriculture EthanolProduction EthanolLoadouttoTruck",
    "30205053":
        "IndustrialProcesses FoodandAgriculture EthanolProduction EthanolLoadouttoRailcar",
    "30205054":
        "IndustrialProcesses FoodandAgriculture EthanolProduction HaulingonPavedUnpavedRoad",
    "30205091":
        "IndustrialProcesses FoodandAgriculture EthanolProduction EquipmentLeaks",
    "30206011":
        "IndustrialProcesses FoodandAgriculture BiodieselProduction CrudeOilTank",
    "30206012":
        "IndustrialProcesses FoodandAgriculture BiodieselProduction OilTreatment",
    "30206013":
        "IndustrialProcesses FoodandAgriculture BiodieselProduction BiodieselProcessVents",
    "30206014":
        "IndustrialProcesses FoodandAgriculture BiodieselProduction BiodieselStorageTanks&ReworkTank",
    "30206015":
        "IndustrialProcesses FoodandAgriculture BiodieselProduction BiodieselLoadout",
    "30206016":
        "IndustrialProcesses FoodandAgriculture BiodieselProduction MethanolTank",
    "30206017":
        "IndustrialProcesses FoodandAgriculture BiodieselProduction CatalystTank",
    "30206018":
        "IndustrialProcesses FoodandAgriculture BiodieselProduction GlycerinProcessVents",
    "30206019":
        "IndustrialProcesses FoodandAgriculture BiodieselProduction GlycerinStorage",
    "30206020":
        "IndustrialProcesses FoodandAgriculture BiodieselProduction GlycerinLoadout",
    "30206021":
        "IndustrialProcesses FoodandAgriculture BiodieselProduction FattyAcidProcess",
    "30206022":
        "IndustrialProcesses FoodandAgriculture BiodieselProduction SoapstockProcess",
    "30206025":
        "IndustrialProcesses FoodandAgriculture BiodieselProduction HaulingonPavedUnpavedRoad",
    "30280001":
        "IndustrialProcesses FoodandAgriculture EquipmentLeaks EquipmentLeaks",
    "30282001":
        "IndustrialProcesses FoodandAgriculture WastewaterAggregate ProcessAreaDrains",
    "30282002":
        "IndustrialProcesses FoodandAgriculture WastewaterAggregate ProcessEquipmentDrains",
    "30282501":
        "IndustrialProcesses FoodandAgriculture WastewaterPointsofGeneration MineralOilStripper",
    "30282503":
        "IndustrialProcesses FoodandAgriculture WastewaterPointsofGeneration CondensatefromCondensers",
    "30282504":
        "IndustrialProcesses FoodandAgriculture WastewaterPointsofGeneration WastewaterSeparator",
    "30282599":
        "IndustrialProcesses FoodandAgriculture WastewaterPointsofGeneration SpecifyPointofGeneration",
    "30288801":
        "IndustrialProcesses FoodandAgriculture FugitiveEmissions SpecifyinCommentsField",
    "30290001":
        "IndustrialProcesses FoodandAgriculture FuelFiredEquipment DistillateOilNo.2ProcessHeaters",
    "30290002":
        "IndustrialProcesses FoodandAgriculture FuelFiredEquipment ResidualOilProcessHeaters",
    "30290003":
        "IndustrialProcesses FoodandAgriculture FuelFiredEquipment NaturalGasProcessHeaters",
    "30290005":
        "IndustrialProcesses FoodandAgriculture FuelFiredEquipment LiquifiedPetroleumGasLPGProcessHeaters",
    "30291001":
        "IndustrialProcesses FoodandAgriculture FuelFiredEquipment BroilingFoodNaturalGas",
    "30299998":
        "IndustrialProcesses FoodandAgriculture OtherNotSpecified OtherNotClassified",
    "30299999":
        "IndustrialProcesses FoodandAgriculture OtherNotSpecified OtherNotClassified",
    "30300001":
        "IndustrialProcesses PrimaryMetalProduction BauxiteOreProcessing CrushingHandling",
    "30300002":
        "IndustrialProcesses PrimaryMetalProduction BauxiteOreProcessing DryingOven",
    "30300003":
        "IndustrialProcesses PrimaryMetalProduction BauxiteOreProcessing FineOreStorage",
    "30300004":
        "IndustrialProcesses PrimaryMetalProduction BauxiteOreProcessing LoadingandUnloading",
    "30300101":
        "IndustrialProcesses PrimaryMetalProduction AluminaElectrolyticReduction PrebakePotlinePrimaryEmissions[Seealso30300113thru16]",
    "30300102":
        "IndustrialProcesses PrimaryMetalProduction AluminaElectrolyticReduction HorizontalStudSoderbergPotlinePrimaryEmissions",
    "30300103":
        "IndustrialProcesses PrimaryMetalProduction AluminaElectrolyticReduction VerticalStudSoderbergOneVSS1PotlinePrimaryEmissions",
    "30300104":
        "IndustrialProcesses PrimaryMetalProduction AluminaElectrolyticReduction MaterialsHandling[Seealso30300123and30300125]",
    "30300105":
        "IndustrialProcesses PrimaryMetalProduction AluminaElectrolyticReduction AnodeBakingFurnacePrimaryEmissions",
    "30300106":
        "IndustrialProcesses PrimaryMetalProduction AluminaElectrolyticReduction Degassing",
    "30300107":
        "IndustrialProcesses PrimaryMetalProduction AluminaElectrolyticReduction RoofVents",
    "30300108":
        "IndustrialProcesses PrimaryMetalProduction AluminaElectrolyticReduction PrebakePotlineSecondaryEmissions[Seealso30300119thru22]",
    "30300110":
        "IndustrialProcesses PrimaryMetalProduction AluminaElectrolyticReduction VerticalStudSoderbergOneVSS1PotlineSecondaryEmissions",
    "30300111":
        "IndustrialProcesses PrimaryMetalProduction AluminaElectrolyticReduction AnodeBakeFurnaceSecondaryEmissions",
    "30300199":
        "IndustrialProcesses PrimaryMetalProduction AluminaElectrolyticReduction Nototherwiseclassified",
    "30300201":
        "IndustrialProcesses PrimaryMetalProduction AluminumHydroxideCalcining OverallProcess",
    "30300302":
        "IndustrialProcesses PrimaryMetalProduction MetallurgicalCokeManufacturing ByproductProcessOvenCharging",
    "30300303":
        "IndustrialProcesses PrimaryMetalProduction MetallurgicalCokeManufacturing ByproductProcessOvenPushing",
    "30300304":
        "IndustrialProcesses PrimaryMetalProduction MetallurgicalCokeManufacturing ByproductProcessQuenching",
    "30300305":
        "IndustrialProcesses PrimaryMetalProduction MetallurgicalCokeManufacturing CoalUnloading",
    "30300306":
        "IndustrialProcesses PrimaryMetalProduction ByproductCokeManufacturing OvenUnderfiring",
    "30300307":
        "IndustrialProcesses PrimaryMetalProduction MetallurgicalCokeManufacturing CoalCrushingHandling",
    "30300308":
        "IndustrialProcesses PrimaryMetalProduction MetallurgicalCokeManufacturing ByproductProcessOvenDoorLeaks",
    "30300309":
        "IndustrialProcesses PrimaryMetalProduction MetallurgicalCokeManufacturing CoalConveying",
    "30300310":
        "IndustrialProcesses PrimaryMetalProduction MetallurgicalCokeManufacturing CoalCrushing",
    "30300311":
        "IndustrialProcesses PrimaryMetalProduction MetallurgicalCokeManufacturing CoalScreening",
    "30300312":
        "IndustrialProcesses PrimaryMetalProduction MetallurgicalCokeManufacturing CokeCrushingScreeningHandling",
    "30300313":
        "IndustrialProcesses PrimaryMetalProduction MetallurgicalCokeManufacturing CoalPreheater",
    "30300314":
        "IndustrialProcesses PrimaryMetalProduction MetallurgicalCokeManufacturing ByproductProcessTopsideLeaksLidLeaks",
    "30300315":
        "IndustrialProcesses PrimaryMetalProduction MetallurgicalCokeManufacturing ByproductProcessGasByproductPlant",
    "30300316":
        "IndustrialProcesses PrimaryMetalProduction MetallurgicalCokeManufacturing CoalStoragePile",
    "30300317":
        "IndustrialProcesses PrimaryMetalProduction MetallurgicalCokeManufacturing ByproductProcessCombustionStackCokeOvenGasCOG",
    "30300318":
        "IndustrialProcesses PrimaryMetalProduction MetallurgicalCokeManufacturing ByproductProcessCombustionStackBlastFurnaceGasBFG",
    "30300331":
        "IndustrialProcesses PrimaryMetalProduction MetallurgicalCokeManufacturing ByproductProcessGeneral",
    "30300332":
        "IndustrialProcesses PrimaryMetalProduction MetallurgicalCokeManufacturing ByproductProcessChemicalPlantFlushingliquorCirculationTank",
    "30300333":
        "IndustrialProcesses PrimaryMetalProduction MetallurgicalCokeManufacturing ByproductProcessChemicalPlantExcessAmmoniaLiquorTank",
    "30300334":
        "IndustrialProcesses PrimaryMetalProduction MetallurgicalCokeManufacturing ByproductProcessChemicalPlantTarDehydrator",
    "30300335":
        "IndustrialProcesses PrimaryMetalProduction MetallurgicalCokeManufacturing ByproductProcessChemicalPlantTarIntercedingSump",
    "30300336":
        "IndustrialProcesses PrimaryMetalProduction MetallurgicalCokeManufacturing ByproductProcessChemicalPlantTarStorage",
    "30300341":
        "IndustrialProcesses PrimaryMetalProduction MetallurgicalCokeManufacturing ByproductProcessChemicalPlantLightOilSump",
    "30300342":
        "IndustrialProcesses PrimaryMetalProduction MetallurgicalCokeManufacturing ByproductProcessChemicalPlantLightOilDecanterCondenserVent",
    "30300343":
        "IndustrialProcesses PrimaryMetalProduction MetallurgicalCokeManufacturing ByproductProcessChemicalPlantWashOilDecanter",
    "30300344":
        "IndustrialProcesses PrimaryMetalProduction MetallurgicalCokeManufacturing ByproductProcessChemicalPlantWashOilCirculationTank",
    "30300352":
        "IndustrialProcesses PrimaryMetalProduction MetallurgicalCokeManufacturing ByproductProcessChemicalPlantTarBottomFinalCooler",
    "30300361":
        "IndustrialProcesses PrimaryMetalProduction MetallurgicalCokeManufacturing ByproductProcessChemicalPlantEquipmentLeaks",
    "30300371":
        "IndustrialProcesses PrimaryMetalProduction MetallurgicalCokeManufacturing HeatNoChemicalRecoveryProcessPushing",
    "30300372":
        "IndustrialProcesses PrimaryMetalProduction MetallurgicalCokeManufacturing HeatNoChemicalRecoveryProcessQuenching",
    "30300375":
        "IndustrialProcesses PrimaryMetalProduction MetallurgicalCokeManufacturing HeatNoChemicalRecoveryProcessOvenCharging",
    "30300376":
        "IndustrialProcesses PrimaryMetalProduction MetallurgicalCokeManufacturing HeatNoChemicalRecoveryProcessMainStack",
    "30300399":
        "IndustrialProcesses PrimaryMetalProduction MetallurgicalCokeManufacturing ByproductProcessNotClassified",
    "30300401":
        "IndustrialProcesses PrimaryMetalProduction CokeManufactureBeehiveProcess General",
    "30300502":
        "IndustrialProcesses PrimaryMetalProduction PrimaryCopperSmelting MultipleHearthRoaster",
    "30300504":
        "IndustrialProcesses PrimaryMetalProduction PrimaryCopperSmelting ConverterAllConfigurations",
    "30300505":
        "IndustrialProcesses PrimaryMetalProduction PrimaryCopperSmelting FireFurnaceRefining",
    "30300506":
        "IndustrialProcesses PrimaryMetalProduction PrimaryCopperSmelting OreConcentrateDryer",
    "30300510":
        "IndustrialProcesses PrimaryMetalProduction PrimaryCopperSmelting ElectricSmeltingFurnace",
    "30300511":
        "IndustrialProcesses PrimaryMetalProduction PrimaryCopperSmelting ElectrolyticRefining",
    "30300512":
        "IndustrialProcesses PrimaryMetalProduction PrimaryCopperSmelting FlashSmelting",
    "30300515":
        "IndustrialProcesses PrimaryMetalProduction PrimaryCopperSmelting ConverterFugitiveEmissions",
    "30300516":
        "IndustrialProcesses PrimaryMetalProduction PrimaryCopperSmelting AnodeRefiningFurnaceFugitiveEmissions",
    "30300517":
        "IndustrialProcesses PrimaryMetalProduction PrimaryCopperSmelting SlagCleaningFurnaceFugitiveEmissions",
    "30300519":
        "IndustrialProcesses PrimaryMetalProduction PrimaryCopperSmelting UnpavedRoadTrafficFugitiveEmissions",
    "30300527":
        "IndustrialProcesses PrimaryMetalProduction PrimaryCopperSmelting DryerwithFlashFurnaceandConverter",
    "30300528":
        "IndustrialProcesses PrimaryMetalProduction PrimaryCopperSmelting NoranderReactorandConverter",
    "30300534":
        "IndustrialProcesses PrimaryMetalProduction PrimaryCopperSmelting FlashFurnaceAfterConcentrateDryer",
    "30300599":
        "IndustrialProcesses PrimaryMetalProduction PrimaryCopperSmelting OtherNotClassified",
    "30300601":
        "IndustrialProcesses PrimaryMetalProduction FerroalloyProduction OpenElectricSmeltingFurnace50%FeSi",
    "30300603":
        "IndustrialProcesses PrimaryMetalProduction FerroalloyProduction OpenElectricSmeltingFurnace90%FeSi",
    "30300604":
        "IndustrialProcesses PrimaryMetalProduction FerroalloyProduction OpenElectricSmeltingFurnaceSiliconMetal",
    "30300605":
        "IndustrialProcesses PrimaryMetalProduction FerroalloyProduction OpenElectricSmeltingFurnaceSilicomanaganese",
    "30300606":
        "IndustrialProcesses PrimaryMetalProduction FerroalloyProduction OpenElectricSmeltingFurnace80%Ferromanganese",
    "30300609":
        "IndustrialProcesses PrimaryMetalProduction FerroalloyProduction RawMaterialCrushing",
    "30300610":
        "IndustrialProcesses PrimaryMetalProduction FerroalloyProduction OreScreening",
    "30300611":
        "IndustrialProcesses PrimaryMetalProduction FerroalloyProduction OreDryer",
    "30300613":
        "IndustrialProcesses PrimaryMetalProduction FerroalloyProduction RawMaterialStorage",
    "30300614":
        "IndustrialProcesses PrimaryMetalProduction FerroalloyProduction RawMaterialTransfer",
    "30300617":
        "IndustrialProcesses PrimaryMetalProduction FerroalloyProduction CastHouse",
    "30300620":
        "IndustrialProcesses PrimaryMetalProduction FerroalloyProduction Tapping",
    "30300621":
        "IndustrialProcesses PrimaryMetalProduction FerroalloyProduction Casting",
    "30300622":
        "IndustrialProcesses PrimaryMetalProduction FerroalloyProduction Cooling",
    "30300623":
        "IndustrialProcesses PrimaryMetalProduction FerroalloyProduction ProductCrushing",
    "30300624":
        "IndustrialProcesses PrimaryMetalProduction FerroalloyProduction ProductStorage",
    "30300625":
        "IndustrialProcesses PrimaryMetalProduction FerroalloyProduction ProductLoading",
    "30300626":
        "IndustrialProcesses PrimaryMetalProduction FerroalloyProduction MetalOxygenRefiningProcess",
    "30300699":
        "IndustrialProcesses PrimaryMetalProduction FerroalloyProduction OtherNotClassified",
    "30300701":
        "IndustrialProcesses PrimaryMetalProduction FerroalloyProduction SemicoveredElectricArcFurnaceFerromanganese",
    "30300702":
        "IndustrialProcesses PrimaryMetalProduction FerroalloyProduction SemicoveredElectricArcFurnaceOtherAlloys",
    "30300801":
        "IndustrialProcesses PrimaryMetalProduction IronProductionSee303015forIntegratedIron&SteelMACT OreCharging",
    "30300802":
        "IndustrialProcesses PrimaryMetalProduction IronProductionSee303015forIntegratedIron&SteelMACT AgglomerateCharging",
    "30300805":
        "IndustrialProcesses PrimaryMetalProduction IronProductionSee303015forIntegratedIron&SteelMACT LoaderLowSilt",
    "30300808":
        "IndustrialProcesses PrimaryMetalProduction IronProductionSee303015forIntegratedIron&SteelMACT SlagCrushingandSizing",
    "30300809":
        "IndustrialProcesses PrimaryMetalProduction IronProductionSee303015forIntegratedIron&SteelMACT SlagRemovalandDumping",
    "30300811":
        "IndustrialProcesses PrimaryMetalProduction IronProductionSee303015forIntegratedIron&SteelMACT RawMaterialStockpilesCokeBreezeLimestoneOreFines",
    "30300812":
        "IndustrialProcesses PrimaryMetalProduction IronProductionSee303015forIntegratedIron&SteelMACT RawMaterialTransferHandling",
    "30300813":
        "IndustrialProcesses PrimaryMetalProduction IronProductionSee303015forIntegratedIron&SteelMACT Windbox",
    "30300814":
        "IndustrialProcesses PrimaryMetalProduction IronProductionSee303015forIntegratedIron&SteelMACT DischargeEnd",
    "30300815":
        "IndustrialProcesses PrimaryMetalProduction IronProductionSee303015forIntegratedIron&SteelMACT SinterBreaker",
    "30300817":
        "IndustrialProcesses PrimaryMetalProduction IronProductionSee303015forIntegratedIron&SteelMACT Cooler",
    "30300818":
        "IndustrialProcesses PrimaryMetalProduction IronProductionSee303015forIntegratedIron&SteelMACT ColdScreening",
    "30300819":
        "IndustrialProcesses PrimaryMetalProduction IronProductionSee303015forIntegratedIron&SteelMACT SinterProcessCombinedCodeincludes15161718",
    "30300820":
        "IndustrialProcesses PrimaryMetalProduction IronProductionSee303015forIntegratedIron&SteelMACT SinterConveyorTransferStation",
    "30300821":
        "IndustrialProcesses PrimaryMetalProduction IronProductionSee303015forIntegratedIron&SteelMACT UnloadOrePelletsLimestoneintoBlastFurnace",
    "30300822":
        "IndustrialProcesses PrimaryMetalProduction IronProductionSee303015forIntegratedIron&SteelMACT RawMaterialStockpileOrePelletsLimestoneCokeSinter",
    "30300823":
        "IndustrialProcesses PrimaryMetalProduction IronProductionSee303015forIntegratedIron&SteelMACT ChargeMaterialsTransferHandling",
    "30300824":
        "IndustrialProcesses PrimaryMetalProduction IronProductionSee303015forIntegratedIron&SteelMACT BlastHeatingStoves",
    "30300825":
        "IndustrialProcesses PrimaryMetalProduction IronProductionSee303015forIntegratedIron&SteelMACT CastHouse",
    "30300826":
        "IndustrialProcesses PrimaryMetalProduction IronProductionSee303015forIntegratedIron&SteelMACT BlastFurnaceSlip",
    "30300827":
        "IndustrialProcesses PrimaryMetalProduction IronProductionSee303015forIntegratedIron&SteelMACT LumpOreUnloading",
    "30300829":
        "IndustrialProcesses PrimaryMetalProduction IronProductionSee303015forIntegratedIron&SteelMACT BlastFurnaceTapholeandTrough",
    "30300831":
        "IndustrialProcesses PrimaryMetalProduction IronProductionSee303015forIntegratedIron&SteelMACT UnpavedRoadsLightDutyVehicles",
    "30300832":
        "IndustrialProcesses PrimaryMetalProduction IronProductionSee303015forIntegratedIron&SteelMACT UnpavedRoadsMediumDutyVehicles",
    "30300833":
        "IndustrialProcesses PrimaryMetalProduction IronProductionSee303015forIntegratedIron&SteelMACT UnpavedRoadsHeavyDutyVehicles",
    "30300834":
        "IndustrialProcesses PrimaryMetalProduction IronProductionSee303015forIntegratedIron&SteelMACT PavedRoadsAllVehicleTypes",
    "30300841":
        "IndustrialProcesses PrimaryMetalProduction IronProductionSee303015forIntegratedIron&SteelMACT FlueDustUnloading",
    "30300842":
        "IndustrialProcesses PrimaryMetalProduction IronProductionSee303015forIntegratedIron&SteelMACT BlendedOreUnloading",
    "30300899":
        "IndustrialProcesses PrimaryMetalProduction IronProductionSee303015forIntegratedIron&SteelMACT SeeComment",
    "30300902":
        "IndustrialProcesses PrimaryMetalProduction SteelManufacturingSee303015forIntegratedIron&SteelMACT PicklingLineContinuous",
    "30300903":
        "IndustrialProcesses PrimaryMetalProduction SteelManufacturingSee303015forIntegratedIron&SteelMACT PicklingLineBatch",
    "30300904":
        "IndustrialProcesses PrimaryMetalProduction SteelManufacturingSee303015forIntegratedIron&SteelMACT ElectricArcFurnaceAlloySteelStack",
    "30300905":
        "IndustrialProcesses PrimaryMetalProduction SteelManufacturingSee303015forIntegratedIron&SteelMACT PicklingLineHClRegenerationPlant",
    "30300906":
        "IndustrialProcesses PrimaryMetalProduction SteelManufacturingSee303015forIntegratedIron&SteelMACT ChargingElectricArcFurnace",
    "30300907":
        "IndustrialProcesses PrimaryMetalProduction SteelManufacturingSee303015forIntegratedIron&SteelMACT TappingElectricArcFurnace",
    "30300908":
        "IndustrialProcesses PrimaryMetalProduction SteelManufacturingSee303015forIntegratedIron&SteelMACT ElectricArcFurnaceCarbonSteelStack",
    "30300909":
        "IndustrialProcesses PrimaryMetalProduction SteelManufacturingSee303015forIntegratedIron&SteelMACT PicklingLineHClStorageVessel",
    "30300910":
        "IndustrialProcesses PrimaryMetalProduction SteelManufacturingSee303015forIntegratedIron&SteelMACT PicklingSeealso303009020305and09",
    "30300911":
        "IndustrialProcesses PrimaryMetalProduction SteelManufacturingSee303015forIntegratedIron&SteelMACT SoakingPits",
    "30300912":
        "IndustrialProcesses PrimaryMetalProduction SteelManufacturingSee303015forIntegratedIron&SteelMACT Grinding",
    "30300913":
        "IndustrialProcesses PrimaryMetalProduction SteelManufacturingSee303015forIntegratedIron&SteelMACT BasicOxygenFurnaceOpenHoodStack",
    "30300914":
        "IndustrialProcesses PrimaryMetalProduction SteelManufacturingSee303015forIntegratedIron&SteelMACT BasicOxygenFurnaceClosedHoodStack",
    "30300915":
        "IndustrialProcesses PrimaryMetalProduction SteelManufacturingSee303015forIntegratedIron&SteelMACT HotMetalIronTransfertoSteelmakingFurnace",
    "30300916":
        "IndustrialProcesses PrimaryMetalProduction SteelManufacturingSee303015forIntegratedIron&SteelMACT ChargingBOF",
    "30300917":
        "IndustrialProcesses PrimaryMetalProduction SteelManufacturingSee303015forIntegratedIron&SteelMACT TappingBOF",
    "30300920":
        "IndustrialProcesses PrimaryMetalProduction SteelManufacturingSee303015forIntegratedIron&SteelMACT HotMetalDesulfurization",
    "30300921":
        "IndustrialProcesses PrimaryMetalProduction SteelManufacturingSee303015forIntegratedIron&SteelMACT TeemingUnleadedSteel",
    "30300922":
        "IndustrialProcesses PrimaryMetalProduction SteelManufacturingSee303015forIntegratedIron&SteelMACT ContinuousCasting",
    "30300923":
        "IndustrialProcesses PrimaryMetalProduction SteelManufacturingSee303015forIntegratedIron&SteelMACT SteelFurnaceSlagTappingandDumping",
    "30300924":
        "IndustrialProcesses PrimaryMetalProduction SteelManufacturingSee303015forIntegratedIron&SteelMACT SteelFurnaceSlagProcessing",
    "30300925":
        "IndustrialProcesses PrimaryMetalProduction SteelManufacturingSee303015forIntegratedIron&SteelMACT TeemingLeadedSteel",
    "30300926":
        "IndustrialProcesses PrimaryMetalProduction SteelManufacturingSee303015forIntegratedIron&SteelMACT ElectricInductionFurnace",
    "30300927":
        "IndustrialProcesses PrimaryMetalProduction SteelManufacturingSee303015forIntegratedIron&SteelMACT SteelScrapPreheater",
    "30300928":
        "IndustrialProcesses PrimaryMetalProduction SteelManufacturingSee303015forIntegratedIron&SteelMACT ArgonoxygenDecarburization",
    "30300929":
        "IndustrialProcesses PrimaryMetalProduction SteelManufacturingSee303015forIntegratedIron&SteelMACT SteelPlateBurnerTorchCutter",
    "30300930":
        "IndustrialProcesses PrimaryMetalProduction SteelManufacturingSee303015forIntegratedIron&SteelMACT QBOPMeltingandRefining",
    "30300931":
        "IndustrialProcesses PrimaryMetalProduction SteelManufacturingSee303015forIntegratedIron&SteelMACT HotRolling",
    "30300932":
        "IndustrialProcesses PrimaryMetalProduction SteelManufacturingSee303015forIntegratedIron&SteelMACT Scarfing",
    "30300933":
        "IndustrialProcesses PrimaryMetalProduction SteelManufacturingSee303015forIntegratedIron&SteelMACT ReheatFurnaces",
    "30300934":
        "IndustrialProcesses PrimaryMetalProduction SteelManufacturingSee303015forIntegratedIron&SteelMACT HeatTreatingFurnacesAnnealing",
    "30300935":
        "IndustrialProcesses PrimaryMetalProduction SteelManufacturingSee303015forIntegratedIron&SteelMACT ColdRolling",
    "30300936":
        "IndustrialProcesses PrimaryMetalProduction SteelManufacturingSee303015forIntegratedIron&SteelMACT CoatingTinZincetc.",
    "30300999":
        "IndustrialProcesses PrimaryMetalProduction SteelManufacturingSee303015forIntegratedIron&SteelMACT OtherNotClassified",
    "30301001":
        "IndustrialProcesses PrimaryMetalProduction LeadProduction SinteringSingleStream",
    "30301002":
        "IndustrialProcesses PrimaryMetalProduction LeadProduction BlastFurnace",
    "30301004":
        "IndustrialProcesses PrimaryMetalProduction LeadProduction OreCrushing",
    "30301009":
        "IndustrialProcesses PrimaryMetalProduction LeadProduction LeadDrossing",
    "30301010":
        "IndustrialProcesses PrimaryMetalProduction LeadProduction RawMaterialCrushingGrinding",
    "30301011":
        "IndustrialProcesses PrimaryMetalProduction LeadProduction RawMaterialUnloading",
    "30301012":
        "IndustrialProcesses PrimaryMetalProduction LeadProduction RawMaterialStoragePile",
    "30301013":
        "IndustrialProcesses PrimaryMetalProduction LeadProduction RawMaterialTransfer",
    "30301015":
        "IndustrialProcesses PrimaryMetalProduction LeadProduction SinterCrushingScreening",
    "30301016":
        "IndustrialProcesses PrimaryMetalProduction LeadProduction SinterTransfer",
    "30301018":
        "IndustrialProcesses PrimaryMetalProduction LeadProduction BlastFurnaceCharging",
    "30301021":
        "IndustrialProcesses PrimaryMetalProduction LeadProduction BlastFurnaceSlagPouring",
    "30301022":
        "IndustrialProcesses PrimaryMetalProduction LeadProduction LeadRefiningSilverRetort",
    "30301023":
        "IndustrialProcesses PrimaryMetalProduction LeadProduction LeadCasting",
    "30301025":
        "IndustrialProcesses PrimaryMetalProduction LeadProduction SinterBuildingFugitiveEmissions",
    "30301026":
        "IndustrialProcesses PrimaryMetalProduction LeadProduction SinterDumpArea",
    "30301030":
        "IndustrialProcesses PrimaryMetalProduction LeadProduction SinterStorage",
    "30301099":
        "IndustrialProcesses PrimaryMetalProduction LeadProduction General",
    "30301101":
        "IndustrialProcesses PrimaryMetalProduction Molybdenum MiningGeneral",
    "30301102":
        "IndustrialProcesses PrimaryMetalProduction Molybdenum MillingGeneral",
    "30301199":
        "IndustrialProcesses PrimaryMetalProduction Molybdenum OtherNotClassified",
    "30301201":
        "IndustrialProcesses PrimaryMetalProduction Titanium Chlorination",
    "30301202":
        "IndustrialProcesses PrimaryMetalProduction Titanium DryingTitaniumSandOreCycloneExit",
    "30301299":
        "IndustrialProcesses PrimaryMetalProduction Titanium OtherNotClassified",
    "30301301":
        "IndustrialProcesses PrimaryMetalProduction GoldProcessing GeneralProcesses",
    "30301302":
        "IndustrialProcesses PrimaryMetalProduction GoldProcessing FinesCrushing",
    "30301303":
        "IndustrialProcesses PrimaryMetalProduction GoldProcessing Autoclave",
    "30301305":
        "IndustrialProcesses PrimaryMetalProduction GoldProcessing CarbonKiln",
    "30301306":
        "IndustrialProcesses PrimaryMetalProduction GoldProcessing PregnantSolutionTank",
    "30301307":
        "IndustrialProcesses PrimaryMetalProduction GoldProcessing ElectrowinningCell",
    "30301308":
        "IndustrialProcesses PrimaryMetalProduction GoldProcessing MercuryRetort",
    "30301309":
        "IndustrialProcesses PrimaryMetalProduction GoldProcessing MeltFurnace",
    "30301310":
        "IndustrialProcesses PrimaryMetalProduction GoldProcessing Quenching",
    "30301311":
        "IndustrialProcesses PrimaryMetalProduction GoldProcessing Roasting",
    "30301499":
        "IndustrialProcesses PrimaryMetalProduction BariumOreProcessing OtherNotClassified",
    "30301501":
        "IndustrialProcesses PrimaryMetalProduction IntegratedIronandSteelManufacturing IntegratedIronandSteelFoundries",
    "30301502":
        "IndustrialProcesses PrimaryMetalProduction IntegratedIronandSteelManufacturing SinteringRawMaterialsHandlingTransferStorage",
    "30301503":
        "IndustrialProcesses PrimaryMetalProduction IntegratedIronandSteelManufacturing SinteringWindbox",
    "30301504":
        "IndustrialProcesses PrimaryMetalProduction IntegratedIronandSteelManufacturing SinteringDischargeEnd",
    "30301505":
        "IndustrialProcesses PrimaryMetalProduction IntegratedIronandSteelManufacturing SinteringCooler",
    "30301507":
        "IndustrialProcesses PrimaryMetalProduction IntegratedIronandSteelManufacturing SinteringCombinedProcesses",
    "30301508":
        "IndustrialProcesses PrimaryMetalProduction IntegratedIronandSteelManufacturing LadleMetallurgyElectricHeating",
    "30301509":
        "IndustrialProcesses PrimaryMetalProduction IntegratedIronandSteelManufacturing LadleMetallurgyNonelectricHeatingandorChemical",
    "30301510":
        "IndustrialProcesses PrimaryMetalProduction IntegratedIronandSteelManufacturing BlastFurnaceSlip",
    "30301511":
        "IndustrialProcesses PrimaryMetalProduction IntegratedIronandSteelManufacturing BlastFurnaceCharging",
    "30301512":
        "IndustrialProcesses PrimaryMetalProduction IntegratedIronandSteelManufacturing BlastFurnaceCastingTappingCasthouseRoofMonitor",
    "30301513":
        "IndustrialProcesses PrimaryMetalProduction IntegratedIronandSteelManufacturing BlastFurnaceCastingTappingLocalEvacuation",
    "30301515":
        "IndustrialProcesses PrimaryMetalProduction IntegratedIronandSteelManufacturing BlastFurnaceRawMaterialsHandlingTransferStorage",
    "30301516":
        "IndustrialProcesses PrimaryMetalProduction IntegratedIronandSteelManufacturing HotMetalTransferSkimmingDesulfurizationCombinedSystem",
    "30301517":
        "IndustrialProcesses PrimaryMetalProduction IntegratedIronandSteelManufacturing HotMetalTransfer",
    "30301518":
        "IndustrialProcesses PrimaryMetalProduction IntegratedIronandSteelManufacturing HotMetalDesulfurization",
    "30301519":
        "IndustrialProcesses PrimaryMetalProduction IntegratedIronandSteelManufacturing BasicOxygenFurnaceBOFMeltShopRoofMonitor",
    "30301520":
        "IndustrialProcesses PrimaryMetalProduction IntegratedIronandSteelManufacturing BasicOxygenFurnaceBOF",
    "30301521":
        "IndustrialProcesses PrimaryMetalProduction IntegratedIronandSteelManufacturing BasicOxygenFurnaceBOFTopBlownFurnaceSecondaryMeltShop",
    "30301522":
        "IndustrialProcesses PrimaryMetalProduction IntegratedIronandSteelManufacturing BasicOxygenFurnaceBOFTopBlownFurnacePrimary",
    "30301523":
        "IndustrialProcesses PrimaryMetalProduction IntegratedIronandSteelManufacturing BasicOxygenFurnaceBOFBottomBlownFurnaceSecondaryMeltShop",
    "30301526":
        "IndustrialProcesses PrimaryMetalProduction IntegratedIronandSteelManufacturing BasicOxygenFurnaceBOFOpenHoodStack",
    "30301527":
        "IndustrialProcesses PrimaryMetalProduction IntegratedIronandSteelManufacturing BasicOxygenFurnaceBOFClosedHoodStack",
    "30301528":
        "IndustrialProcesses PrimaryMetalProduction IntegratedIronandSteelManufacturing BasicOxygenFurnaceBOFCharging",
    "30301529":
        "IndustrialProcesses PrimaryMetalProduction IntegratedIronandSteelManufacturing BasicOxygenFurnaceBOFTapping",
    "30301530":
        "IndustrialProcesses PrimaryMetalProduction IntegratedIronandSteelManufacturing BasicOxygenFurnaceBOFBottomBlownMeltingandRefining",
    "30301532":
        "IndustrialProcesses PrimaryMetalProduction IntegratedIronandSteelManufacturing ElectricArcFurnaceEAFSpecialtySteel",
    "30301540":
        "IndustrialProcesses PrimaryMetalProduction IntegratedIronandSteelManufacturing ElectricArcFurnaceEAFCarbonSteelCharging",
    "30301541":
        "IndustrialProcesses PrimaryMetalProduction IntegratedIronandSteelManufacturing ElectricArcFurnaceEAFCarbonSteelMeltingandRefining",
    "30301542":
        "IndustrialProcesses PrimaryMetalProduction IntegratedIronandSteelManufacturing ElectricArcFurnaceEAFCarbonSteelTapping",
    "30301544":
        "IndustrialProcesses PrimaryMetalProduction IntegratedIronandSteelManufacturing ElectricArcFurnaceEAFCarbonSteel",
    "30301546":
        "IndustrialProcesses PrimaryMetalProduction IntegratedIronandSteelManufacturing ElectricArcFurnaceEAFCarbonSteelChargingMeltingandRefiningTapping",
    "30301548":
        "IndustrialProcesses PrimaryMetalProduction IntegratedIronandSteelManufacturing ElectricArcFurnaceEAFCarbonSteelDustHandlingFugitiveEmissions",
    "30301554":
        "IndustrialProcesses PrimaryMetalProduction IntegratedIronandSteelManufacturing OpenHearthFurnaceSlagging",
    "30301556":
        "IndustrialProcesses PrimaryMetalProduction IntegratedIronandSteelManufacturing ArgonOxygenDecarburizationCarbonSteel",
    "30301558":
        "IndustrialProcesses PrimaryMetalProduction IntegratedIronandSteelManufacturing SteelPlateBurnerTorchCutter",
    "30301561":
        "IndustrialProcesses PrimaryMetalProduction IntegratedIronandSteelManufacturing TeemingUnleadedSteel",
    "30301564":
        "IndustrialProcesses PrimaryMetalProduction IntegratedIronandSteelManufacturing SlagTappingDumping",
    "30301565":
        "IndustrialProcesses PrimaryMetalProduction IntegratedIronandSteelManufacturing SlagProcessing",
    "30301566":
        "IndustrialProcesses PrimaryMetalProduction IntegratedIronandSteelManufacturing PavedRoadsAllVehicleTypes",
    "30301567":
        "IndustrialProcesses PrimaryMetalProduction IntegratedIronandSteelManufacturing UnpavedRoadsLightDutyVehicles",
    "30301568":
        "IndustrialProcesses PrimaryMetalProduction IntegratedIronandSteelManufacturing UnpavedRoadsMediumDutyVehicles",
    "30301569":
        "IndustrialProcesses PrimaryMetalProduction IntegratedIronandSteelManufacturing UnpavedRoadsHeavyDutyVehicles",
    "30301570":
        "IndustrialProcesses PrimaryMetalProduction IntegratedIronandSteelManufacturing MachineScarfing",
    "30301571":
        "IndustrialProcesses PrimaryMetalProduction IntegratedIronandSteelManufacturing ManualScarfing",
    "30301572":
        "IndustrialProcesses PrimaryMetalProduction IntegratedIronandSteelManufacturing Scarfing",
    "30301573":
        "IndustrialProcesses PrimaryMetalProduction IntegratedIronandSteelManufacturing HotRolling",
    "30301574":
        "IndustrialProcesses PrimaryMetalProduction IntegratedIronandSteelManufacturing ColdRolling",
    "30301575":
        "IndustrialProcesses PrimaryMetalProduction IntegratedIronandSteelManufacturing CoatingTinZincetc.",
    "30301576":
        "IndustrialProcesses PrimaryMetalProduction IntegratedIronandSteelManufacturing SteelPickling",
    "30301577":
        "IndustrialProcesses PrimaryMetalProduction IntegratedIronandSteelManufacturing PicklingContinuous",
    "30301578":
        "IndustrialProcesses PrimaryMetalProduction IntegratedIronandSteelManufacturing PicklingBatch",
    "30301579":
        "IndustrialProcesses PrimaryMetalProduction IntegratedIronandSteelManufacturing PicklingHClRegenerationPlant",
    "30301580":
        "IndustrialProcesses PrimaryMetalProduction IntegratedIronandSteelManufacturing MiscellaneousCombustionSources",
    "30301581":
        "IndustrialProcesses PrimaryMetalProduction IntegratedIronandSteelManufacturing BlastFurnaceStove",
    "30301582":
        "IndustrialProcesses PrimaryMetalProduction IntegratedIronandSteelManufacturing MiscellaneousCombustionSourcesBoilers",
    "30301584":
        "IndustrialProcesses PrimaryMetalProduction IntegratedIronandSteelManufacturing MiscellaneousCombustionSourcesReheatFurnaces",
    "30301585":
        "IndustrialProcesses PrimaryMetalProduction IntegratedIronandSteelManufacturing ElectricInductionFurnace",
    "30301586":
        "IndustrialProcesses PrimaryMetalProduction IntegratedIronandSteelManufacturing SteelScrapPreheater",
    "30301587":
        "IndustrialProcesses PrimaryMetalProduction IntegratedIronandSteelManufacturing HeatTreatingFurnaceAnnealing",
    "30301590":
        "IndustrialProcesses PrimaryMetalProduction IntegratedIronandSteelManufacturing OpenDustSources",
    "30301591":
        "IndustrialProcesses PrimaryMetalProduction IntegratedIronandSteelManufacturing ContinuousDropConveyorTransferStation",
    "30301592":
        "IndustrialProcesses PrimaryMetalProduction IntegratedIronandSteelManufacturing PileFormationStackerPelletOre",
    "30301594":
        "IndustrialProcesses PrimaryMetalProduction IntegratedIronandSteelManufacturing PileFormationStackerCoal",
    "30301595":
        "IndustrialProcesses PrimaryMetalProduction IntegratedIronandSteelManufacturing BatchDropFrontEndLoaderTruckHighSiltSlag",
    "30301596":
        "IndustrialProcesses PrimaryMetalProduction IntegratedIronandSteelManufacturing BatchDropFrontEndLoaderTruckLowSiltSlag",
    "30301597":
        "IndustrialProcesses PrimaryMetalProduction IntegratedIronandSteelManufacturing WastewaterTreatmentSystemCoolingTower",
    "30301598":
        "IndustrialProcesses PrimaryMetalProduction IntegratedIronandSteelManufacturing Grinding",
    "30301599":
        "IndustrialProcesses PrimaryMetalProduction IntegratedIronandSteelManufacturing OtherNotClassified",
    "30302301":
        "IndustrialProcesses PrimaryMetalProduction TaconiteIronOreProcessing PrimaryCrushing",
    "30302302":
        "IndustrialProcesses PrimaryMetalProduction TaconiteIronOreProcessing TertiaryCrusher",
    "30302303":
        "IndustrialProcesses PrimaryMetalProduction TaconiteIronOreProcessing OreScreening",
    "30302304":
        "IndustrialProcesses PrimaryMetalProduction TaconiteIronOreProcessing OreTransfer",
    "30302305":
        "IndustrialProcesses PrimaryMetalProduction TaconiteIronOreProcessing OreStorage",
    "30302306":
        "IndustrialProcesses PrimaryMetalProduction TaconiteIronOreProcessing DryGrindingMilling",
    "30302307":
        "IndustrialProcesses PrimaryMetalProduction TaconiteIronOreProcessing BentoniteStorage",
    "30302308":
        "IndustrialProcesses PrimaryMetalProduction TaconiteIronOreProcessing BentoniteBlending",
    "30302312":
        "IndustrialProcesses PrimaryMetalProduction TaconiteIronOreProcessing InduratingFurnaceGasFiredsee30302351thru88",
    "30302314":
        "IndustrialProcesses PrimaryMetalProduction TaconiteIronOreProcessing InduratingFurnaceCoalFiredsee30302351thru88",
    "30302315":
        "IndustrialProcesses PrimaryMetalProduction TaconiteIronOreProcessing PelletCooler",
    "30302316":
        "IndustrialProcesses PrimaryMetalProduction TaconiteIronOreProcessing PelletTransfertoStorage",
    "30302320":
        "IndustrialProcesses PrimaryMetalProduction TaconiteIronOreProcessing ConveyorsTransferandLoadingsee30302351thru88",
    "30302321":
        "IndustrialProcesses PrimaryMetalProduction TaconiteIronOreProcessing HaulRoadRock",
    "30302322":
        "IndustrialProcesses PrimaryMetalProduction TaconiteIronOreProcessing HaulRoadTaconite",
    "30302345":
        "IndustrialProcesses PrimaryMetalProduction TaconiteIronOreProcessing BentoniteTransfertoBlending",
    "30302349":
        "IndustrialProcesses PrimaryMetalProduction TaconiteIronOreProcessing GrateKilnFurnaceFeed",
    "30302350":
        "IndustrialProcesses PrimaryMetalProduction TaconiteIronOreProcessing GrateKilnFurnaceDischarge",
    "30302351":
        "IndustrialProcesses PrimaryMetalProduction TaconiteIronOreProcessing IndurationGrateKilnGasfiredAcidPellets",
    "30302352":
        "IndustrialProcesses PrimaryMetalProduction TaconiteIronOreProcessing IndurationGrateKilnGasfiredFluxPellets",
    "30302353":
        "IndustrialProcesses PrimaryMetalProduction TaconiteIronOreProcessing IndurationGrateKilnGas&OilfiredAcidPellets",
    "30302354":
        "IndustrialProcesses PrimaryMetalProduction TaconiteIronOreProcessing IndurationGrateKilnGas&OilfiredFluxPellets",
    "30302357":
        "IndustrialProcesses PrimaryMetalProduction TaconiteIronOreProcessing IndurationGrateKilnCoke&CoalfiredAcidPellets",
    "30302359":
        "IndustrialProcesses PrimaryMetalProduction TaconiteIronOreProcessing IndurationGrateKilnCoalfiredAcidPellets",
    "30302360":
        "IndustrialProcesses PrimaryMetalProduction TaconiteIronOreProcessing IndurationGrateKilnCoalfiredFluxPellets",
    "30302379":
        "IndustrialProcesses PrimaryMetalProduction TaconiteIronOreProcessing StraightGrateFurnaceFeed",
    "30302380":
        "IndustrialProcesses PrimaryMetalProduction TaconiteIronOreProcessing StraightGrateFurnaceDischarge",
    "30302381":
        "IndustrialProcesses PrimaryMetalProduction TaconiteIronOreProcessing IndurationStraightGrateGasfiredAcidPellets",
    "30302382":
        "IndustrialProcesses PrimaryMetalProduction TaconiteIronOreProcessing IndurationStraightGrateGasfiredFluxPellets",
    "30302395":
        "IndustrialProcesses PrimaryMetalProduction TaconiteIronOreProcessing PelletScreen",
    "30302396":
        "IndustrialProcesses PrimaryMetalProduction TaconiteIronOreProcessing PelletStorageBinLoading",
    "30302399":
        "IndustrialProcesses PrimaryMetalProduction TaconiteIronOreProcessing OtherNotClassified",
    "30302401":
        "IndustrialProcesses PrimaryMetalProduction MetalMiningGeneralProcesses PrimaryCrushingLowMoistureOre",
    "30302402":
        "IndustrialProcesses PrimaryMetalProduction MetalMiningGeneralProcesses SecondaryCrushingLowMoistureOre",
    "30302403":
        "IndustrialProcesses PrimaryMetalProduction MetalMiningGeneralProcesses TertiaryCrushingLowMoistureOre",
    "30302404":
        "IndustrialProcesses PrimaryMetalProduction MetalMiningGeneralProcesses MaterialHandlingLowMoistureOre",
    "30302405":
        "IndustrialProcesses PrimaryMetalProduction MetalMiningGeneralProcesses PrimaryCrushingHighMoistureOre",
    "30302406":
        "IndustrialProcesses PrimaryMetalProduction MetalMiningGeneralProcesses SecondaryCrushingHighMoistureOre",
    "30302407":
        "IndustrialProcesses PrimaryMetalProduction MetalMiningGeneralProcesses TertiaryCrushingHighMoistureOre",
    "30302408":
        "IndustrialProcesses PrimaryMetalProduction MetalMiningGeneralProcesses MaterialHandlingHighMoistureOre",
    "30302409":
        "IndustrialProcesses PrimaryMetalProduction MetalMiningGeneralProcesses DryGrindingwithAirConveying",
    "30302410":
        "IndustrialProcesses PrimaryMetalProduction MetalMiningGeneralProcesses DryGrindingwithoutAirConveying",
    "30302411":
        "IndustrialProcesses PrimaryMetalProduction MetalMiningGeneralProcesses OreDrying",
    "30303003":
        "IndustrialProcesses PrimaryMetalProduction ZincProduction SinterStrand",
    "30303005":
        "IndustrialProcesses PrimaryMetalProduction ZincProduction VerticalRetortElectrothermalFurnace",
    "30303006":
        "IndustrialProcesses PrimaryMetalProduction ZincProduction ElectrolyticProcessor",
    "30303009":
        "IndustrialProcesses PrimaryMetalProduction ZincProduction RawMaterialHandlingandTransfer",
    "30303010":
        "IndustrialProcesses PrimaryMetalProduction ZincProduction SinterBreakingandCooling",
    "30303011":
        "IndustrialProcesses PrimaryMetalProduction ZincProduction ZincCasting",
    "30303012":
        "IndustrialProcesses PrimaryMetalProduction ZincProduction RawMaterialUnloading",
    "30303014":
        "IndustrialProcesses PrimaryMetalProduction ZincProduction CrushingScreening",
    "30303015":
        "IndustrialProcesses PrimaryMetalProduction ZincProduction ZincMelting",
    "30303016":
        "IndustrialProcesses PrimaryMetalProduction ZincProduction Alloying",
    "30303018":
        "IndustrialProcesses PrimaryMetalProduction ZincProduction Purification",
    "30303019":
        "IndustrialProcesses PrimaryMetalProduction ZincProduction SinterPlantWindBox",
    "30303022":
        "IndustrialProcesses PrimaryMetalProduction ZincProduction FlueDustHandling",
    "30303023":
        "IndustrialProcesses PrimaryMetalProduction ZincProduction DrossHandling",
    "30303027":
        "IndustrialProcesses PrimaryMetalProduction ZincProduction RetortBuildingFugitiveEmissions",
    "30303028":
        "IndustrialProcesses PrimaryMetalProduction ZincProduction CastingFugitiveEmissions",
    "30303099":
        "IndustrialProcesses PrimaryMetalProduction ZincProduction OtherNotClassified",
    "30303102":
        "IndustrialProcesses PrimaryMetalProduction LeadbearingOreCrushingandGrinding ZincOrew0.2%LeadContent",
    "30303104":
        "IndustrialProcesses PrimaryMetalProduction LeadbearingOreCrushingandGrinding LeadZincOrew2%LeadContent",
    "30303107":
        "IndustrialProcesses PrimaryMetalProduction LeadbearingOreCrushingandGrinding CopperLeadZincw2%LeadContent",
    "30304001":
        "IndustrialProcesses PrimaryMetalProduction AluminaProcessingBayerProcess BayerProcess",
    "30304010":
        "IndustrialProcesses PrimaryMetalProduction AluminaProcessingBayerProcess OreCrushingGrinding",
    "30304014":
        "IndustrialProcesses PrimaryMetalProduction AluminaProcessingBayerProcess HydrolizationCooling",
    "30304017":
        "IndustrialProcesses PrimaryMetalProduction AluminaProcessingBayerProcess CoolingofAlumina",
    "30380001":
        "IndustrialProcesses PrimaryMetalProduction EquipmentLeaks EquipmentLeaks",
    "30382001":
        "IndustrialProcesses PrimaryMetalProduction WastewaterAggregate ProcessAreaDrains",
    "30382002":
        "IndustrialProcesses PrimaryMetalProduction WastewaterAggregate ProcessEquipmentDrains",
    "30382599":
        "IndustrialProcesses PrimaryMetalProduction WastewaterPointsofGeneration SpecifyPointofGeneration",
    "30388801":
        "IndustrialProcesses PrimaryMetalProduction FugitiveEmissions SpecifyinCommentsField",
    "30390001":
        "IndustrialProcesses PrimaryMetalProduction FuelFiredEquipment DistillateOilNo.2ProcessHeaters",
    "30390002":
        "IndustrialProcesses PrimaryMetalProduction FuelFiredEquipment ResidualOilProcessHeaters",
    "30390003":
        "IndustrialProcesses PrimaryMetalProduction FuelFiredEquipment NaturalGasProcessHeaters",
    "30390004":
        "IndustrialProcesses PrimaryMetalProduction FuelFiredEquipment ProcessGasProcessHeaters",
    "30390011":
        "IndustrialProcesses PrimaryMetalProduction FuelFiredEquipment DistillateOilNo.2Incinerators",
    "30390013":
        "IndustrialProcesses PrimaryMetalProduction FuelFiredEquipment NaturalGasIncinerators",
    "30390014":
        "IndustrialProcesses PrimaryMetalProduction FuelFiredEquipment ProcessGasIncinerators",
    "30390023":
        "IndustrialProcesses PrimaryMetalProduction FuelFiredEquipment NaturalGasFlares",
    "30390024":
        "IndustrialProcesses PrimaryMetalProduction FuelFiredEquipment ProcessGasFlares",
    "30399999":
        "IndustrialProcesses PrimaryMetalProduction OtherNotClassified OtherNotClassified",
    "30400101":
        "IndustrialProcesses SecondaryMetalProduction Aluminum SweatFurnace",
    "30400102":
        "IndustrialProcesses SecondaryMetalProduction Aluminum SmeltingFurnaceCrucible",
    "30400103":
        "IndustrialProcesses SecondaryMetalProduction Aluminum SmeltingFurnaceReverberatory",
    "30400104":
        "IndustrialProcesses SecondaryMetalProduction Aluminum FluxingChlorinationChlorineDemagging",
    "30400105":
        "IndustrialProcesses SecondaryMetalProduction Aluminum FluxingFluoridationFluorineDemagging",
    "30400106":
        "IndustrialProcesses SecondaryMetalProduction Aluminum FluxingDegassing",
    "30400107":
        "IndustrialProcesses SecondaryMetalProduction Aluminum DrossFurnace",
    "30400108":
        "IndustrialProcesses SecondaryMetalProduction Aluminum PreprocessingScrapShreddingCrushingScreening",
    "30400109":
        "IndustrialProcesses SecondaryMetalProduction Aluminum BurningDrying",
    "30400110":
        "IndustrialProcesses SecondaryMetalProduction Aluminum FoilRolling",
    "30400111":
        "IndustrialProcesses SecondaryMetalProduction Aluminum FoilConverting",
    "30400112":
        "IndustrialProcesses SecondaryMetalProduction Aluminum AnnealingFurnace",
    "30400113":
        "IndustrialProcesses SecondaryMetalProduction Aluminum SlabFurnace",
    "30400114":
        "IndustrialProcesses SecondaryMetalProduction Aluminum PouringCasting",
    "30400115":
        "IndustrialProcesses SecondaryMetalProduction Aluminum PreprocessingSweatFurnaceGrate",
    "30400116":
        "IndustrialProcesses SecondaryMetalProduction Aluminum PreprocessingDryMillingDross",
    "30400120":
        "IndustrialProcesses SecondaryMetalProduction Aluminum CanManufacture",
    "30400121":
        "IndustrialProcesses SecondaryMetalProduction Aluminum PreprocessingRoasting",
    "30400130":
        "IndustrialProcesses SecondaryMetalProduction Aluminum Demagging",
    "30400131":
        "IndustrialProcesses SecondaryMetalProduction Aluminum FurnaceCharging",
    "30400132":
        "IndustrialProcesses SecondaryMetalProduction Aluminum RawMaterialStorage",
    "30400133":
        "IndustrialProcesses SecondaryMetalProduction Aluminum FurnaceTapping",
    "30400134":
        "IndustrialProcesses SecondaryMetalProduction Aluminum PreprocessingThermalChipDryer",
    "30400135":
        "IndustrialProcesses SecondaryMetalProduction Aluminum PreprocessingScrapDryerDelacqueringDecoatingKiln",
    "30400136":
        "IndustrialProcesses SecondaryMetalProduction Aluminum RotaryDrossCooler",
    "30400137":
        "IndustrialProcesses SecondaryMetalProduction Aluminum Group1FurnaceCleanChargeOnly",
    "30400138":
        "IndustrialProcesses SecondaryMetalProduction Aluminum Group1FurnaceOtherthanCleanCharge",
    "30400150":
        "IndustrialProcesses SecondaryMetalProduction Aluminum RollingDrawingExtruding",
    "30400160":
        "IndustrialProcesses SecondaryMetalProduction Aluminum MaterialHandling",
    "30400199":
        "IndustrialProcesses SecondaryMetalProduction Aluminum OtherNotClassified",
    "30400207":
        "IndustrialProcesses SecondaryMetalProduction Copper ScrapDryerRotary",
    "30400208":
        "IndustrialProcesses SecondaryMetalProduction Copper WireBurningIncinerator",
    "30400210":
        "IndustrialProcesses SecondaryMetalProduction Copper ChargewithScrapCopperCupolas",
    "30400212":
        "IndustrialProcesses SecondaryMetalProduction Copper ChargewithScrapCopperAndBrassCupolas",
    "30400214":
        "IndustrialProcesses SecondaryMetalProduction Copper ChargewithCopperReverberatoryFurnace",
    "30400215":
        "IndustrialProcesses SecondaryMetalProduction Copper ChargewithBrassandBronzeReverberatoryFurnace",
    "30400217":
        "IndustrialProcesses SecondaryMetalProduction Copper ChargewithBrassandBronzeRotaryFurnace",
    "30400218":
        "IndustrialProcesses SecondaryMetalProduction Copper ChargewithCopperCrucibleandPotFurnace",
    "30400219":
        "IndustrialProcesses SecondaryMetalProduction Copper ChargewithBrassandBronzeCrucibleandPotFurnace",
    "30400220":
        "IndustrialProcesses SecondaryMetalProduction Copper ChargewithCopperElectricArcFurnace",
    "30400221":
        "IndustrialProcesses SecondaryMetalProduction Copper ChargewithBrassandBronzeElectricArcFurnace",
    "30400223":
        "IndustrialProcesses SecondaryMetalProduction Copper ChargewithCopperElectricInduction",
    "30400224":
        "IndustrialProcesses SecondaryMetalProduction Copper ChargewithBrassandBronzeElectricInduction",
    "30400230":
        "IndustrialProcesses SecondaryMetalProduction Copper ScrapMetalPretreatment",
    "30400234":
        "IndustrialProcesses SecondaryMetalProduction Copper CupolaFurnace",
    "30400235":
        "IndustrialProcesses SecondaryMetalProduction Copper ReverberatoryFurnace",
    "30400236":
        "IndustrialProcesses SecondaryMetalProduction Copper RotaryFurnace",
    "30400237":
        "IndustrialProcesses SecondaryMetalProduction Copper CrucibleFurnace",
    "30400238":
        "IndustrialProcesses SecondaryMetalProduction Copper ElectricInductionFurnace",
    "30400239":
        "IndustrialProcesses SecondaryMetalProduction Copper CastingOperations",
    "30400240":
        "IndustrialProcesses SecondaryMetalProduction Copper ChargewithCopperHoldingFurnace",
    "30400299":
        "IndustrialProcesses SecondaryMetalProduction Copper OtherNotClassified",
    "30400301":
        "IndustrialProcesses SecondaryMetalProduction GreyIronFoundries Cupola",
    "30400302":
        "IndustrialProcesses SecondaryMetalProduction GreyIronFoundries ReverberatoryFurnace",
    "30400303":
        "IndustrialProcesses SecondaryMetalProduction GreyIronFoundries ElectricInductionFurnace",
    "30400304":
        "IndustrialProcesses SecondaryMetalProduction GreyIronFoundries ElectricArcFurnace",
    "30400305":
        "IndustrialProcesses SecondaryMetalProduction GreyIronFoundries AnnealingOperation",
    "30400310":
        "IndustrialProcesses SecondaryMetalProduction GreyIronFoundries Inoculation",
    "30400314":
        "IndustrialProcesses SecondaryMetalProduction GreyIronFoundries ScrapMetalPreheating",
    "30400315":
        "IndustrialProcesses SecondaryMetalProduction GreyIronFoundries ChargeHandling",
    "30400316":
        "IndustrialProcesses SecondaryMetalProduction GreyIronFoundries Tapping",
    "30400317":
        "IndustrialProcesses SecondaryMetalProduction GreyIronFoundries PouringLadle",
    "30400318":
        "IndustrialProcesses SecondaryMetalProduction GreyIronFoundries PouringCooling",
    "30400319":
        "IndustrialProcesses SecondaryMetalProduction GreyIronFoundries CoreMakingBaking",
    "30400320":
        "IndustrialProcesses SecondaryMetalProduction GreyIronFoundries PouringCasting",
    "30400321":
        "IndustrialProcesses SecondaryMetalProduction GreyIronFoundries MagnesiumTreatment",
    "30400322":
        "IndustrialProcesses SecondaryMetalProduction GreyIronFoundries Refining",
    "30400325":
        "IndustrialProcesses SecondaryMetalProduction GreyIronFoundries CastingsCooling",
    "30400330":
        "IndustrialProcesses SecondaryMetalProduction GreyIronFoundries MiscellaneousCastingFabricating",
    "30400331":
        "IndustrialProcesses SecondaryMetalProduction GreyIronFoundries CastingShakeout",
    "30400332":
        "IndustrialProcesses SecondaryMetalProduction GreyIronFoundries CastingKnockOut",
    "30400333":
        "IndustrialProcesses SecondaryMetalProduction GreyIronFoundries ShakeoutMachine",
    "30400340":
        "IndustrialProcesses SecondaryMetalProduction GreyIronFoundries GrindingCleaning",
    "30400341":
        "IndustrialProcesses SecondaryMetalProduction GreyIronFoundries CastingCleaningTumblers",
    "30400342":
        "IndustrialProcesses SecondaryMetalProduction GreyIronFoundries CastingCleaningChippers",
    "30400350":
        "IndustrialProcesses SecondaryMetalProduction GreyIronFoundries SandGrindingHandling",
    "30400351":
        "IndustrialProcesses SecondaryMetalProduction GreyIronFoundries CoreOvens",
    "30400355":
        "IndustrialProcesses SecondaryMetalProduction GreyIronFoundries SandDryer",
    "30400356":
        "IndustrialProcesses SecondaryMetalProduction GreyIronFoundries SandSilo",
    "30400357":
        "IndustrialProcesses SecondaryMetalProduction GreyIronFoundries ConveyorsElevators",
    "30400358":
        "IndustrialProcesses SecondaryMetalProduction GreyIronFoundries SandScreens",
    "30400360":
        "IndustrialProcesses SecondaryMetalProduction GreyIronFoundries CastingsFinishing",
    "30400370":
        "IndustrialProcesses SecondaryMetalProduction GreyIronFoundries ShellCoreMachine",
    "30400371":
        "IndustrialProcesses SecondaryMetalProduction GreyIronFoundries CoreMachinesOther",
    "30400398":
        "IndustrialProcesses SecondaryMetalProduction GreyIronFoundries OtherNotClassified",
    "30400399":
        "IndustrialProcesses SecondaryMetalProduction GreyIronFoundries OtherNotClassified",
    "30400401":
        "IndustrialProcesses SecondaryMetalProduction Lead RefiningKettlePotFurnace",
    "30400402":
        "IndustrialProcesses SecondaryMetalProduction Lead SmeltingFurnaceReverberatory",
    "30400403":
        "IndustrialProcesses SecondaryMetalProduction Lead SmeltingFurnaceBlast",
    "30400404":
        "IndustrialProcesses SecondaryMetalProduction Lead SweatingFurnaceRotary",
    "30400407":
        "IndustrialProcesses SecondaryMetalProduction Lead RefiningKettlePotFurnaceHeaterNaturalGas",
    "30400408":
        "IndustrialProcesses SecondaryMetalProduction Lead RefiningBartonProcessReactorOxidationKettle",
    "30400409":
        "IndustrialProcesses SecondaryMetalProduction Lead Casting",
    "30400410":
        "IndustrialProcesses SecondaryMetalProduction Lead BatteryBreaking",
    "30400411":
        "IndustrialProcesses SecondaryMetalProduction Lead ScrapCrushing",
    "30400412":
        "IndustrialProcesses SecondaryMetalProduction Lead SweatingFurnaceFugitiveEmissions",
    "30400413":
        "IndustrialProcesses SecondaryMetalProduction Lead SmeltingFurnaceFugitiveEmissions",
    "30400414":
        "IndustrialProcesses SecondaryMetalProduction Lead RefiningKettleFugitiveEmissions",
    "30400416":
        "IndustrialProcesses SecondaryMetalProduction Lead FurnaceCharging",
    "30400417":
        "IndustrialProcesses SecondaryMetalProduction Lead FurnaceTappingLeadSlag",
    "30400419":
        "IndustrialProcesses SecondaryMetalProduction Lead Dryer",
    "30400420":
        "IndustrialProcesses SecondaryMetalProduction Lead RawMaterialUnloading",
    "30400421":
        "IndustrialProcesses SecondaryMetalProduction Lead RawMaterialTransferConveying",
    "30400422":
        "IndustrialProcesses SecondaryMetalProduction Lead RawMaterialStoragePile",
    "30400423":
        "IndustrialProcesses SecondaryMetalProduction Lead SlagBreaking",
    "30400424":
        "IndustrialProcesses SecondaryMetalProduction Lead SizeSeparation",
    "30400425":
        "IndustrialProcesses SecondaryMetalProduction Lead Casting",
    "30400426":
        "IndustrialProcesses SecondaryMetalProduction Lead RefiningKettle",
    "30400499":
        "IndustrialProcesses SecondaryMetalProduction Lead General",
    "30400512":
        "IndustrialProcesses SecondaryMetalProduction LeadBatteryManufacture Formation",
    "30400513":
        "IndustrialProcesses SecondaryMetalProduction LeadBatteryManufacture BartonProcessOxidationKettle",
    "30400521":
        "IndustrialProcesses SecondaryMetalProduction LeadBatteryManufacture OverallProcess",
    "30400522":
        "IndustrialProcesses SecondaryMetalProduction LeadBatteryManufacture GridCasting",
    "30400523":
        "IndustrialProcesses SecondaryMetalProduction LeadBatteryManufacture PasteMixing",
    "30400524":
        "IndustrialProcesses SecondaryMetalProduction LeadBatteryManufacture LeadOxideMillBaghouseOutlet",
    "30400525":
        "IndustrialProcesses SecondaryMetalProduction LeadBatteryManufacture ThreeProcessOperation",
    "30400526":
        "IndustrialProcesses SecondaryMetalProduction LeadBatteryManufacture LeadReclaimingFurnace",
    "30400527":
        "IndustrialProcesses SecondaryMetalProduction LeadBatteryManufacture SmallPartsCasting",
    "30400528":
        "IndustrialProcesses SecondaryMetalProduction LeadBatteryManufacture Formation",
    "30400529":
        "IndustrialProcesses SecondaryMetalProduction LeadBatteryManufacture GridCastPasteMixCombinedOperation",
    "30400530":
        "IndustrialProcesses SecondaryMetalProduction LeadBatteryManufacture PasteMixLeadChargeCombinedOperation",
    "30400599":
        "IndustrialProcesses SecondaryMetalProduction LeadBatteryManufacture OtherNotClassified",
    "30400601":
        "IndustrialProcesses SecondaryMetalProduction Magnesium PotFurnace",
    "30400605":
        "IndustrialProcesses SecondaryMetalProduction Magnesium DowSeawaterProcessNeutralizationTank",
    "30400650":
        "IndustrialProcesses SecondaryMetalProduction Magnesium AmericanMagnesiumProcess",
    "30400699":
        "IndustrialProcesses SecondaryMetalProduction Magnesium OtherNotClassified",
    "30400701":
        "IndustrialProcesses SecondaryMetalProduction SteelFoundries ElectricArcFurnace",
    "30400702":
        "IndustrialProcesses SecondaryMetalProduction SteelFoundries OpenHearthFurnace",
    "30400703":
        "IndustrialProcesses SecondaryMetalProduction SteelFoundries OpenHearthFurnacewithOxygenLance",
    "30400704":
        "IndustrialProcesses SecondaryMetalProduction SteelFoundries HeatTreatingFurnace",
    "30400705":
        "IndustrialProcesses SecondaryMetalProduction SteelFoundries ElectricInductionFurnace",
    "30400706":
        "IndustrialProcesses SecondaryMetalProduction SteelFoundries SandGrindingHandling",
    "30400707":
        "IndustrialProcesses SecondaryMetalProduction SteelFoundries CoreOvens",
    "30400708":
        "IndustrialProcesses SecondaryMetalProduction SteelFoundries PouringCasting",
    "30400709":
        "IndustrialProcesses SecondaryMetalProduction SteelFoundries CastingShakeout",
    "30400710":
        "IndustrialProcesses SecondaryMetalProduction SteelFoundries CastingKnockOut",
    "30400711":
        "IndustrialProcesses SecondaryMetalProduction SteelFoundries Cleaning",
    "30400712":
        "IndustrialProcesses SecondaryMetalProduction SteelFoundries ChargeHandling",
    "30400713":
        "IndustrialProcesses SecondaryMetalProduction SteelFoundries CastingsCooling",
    "30400714":
        "IndustrialProcesses SecondaryMetalProduction SteelFoundries ShakeoutMachine",
    "30400715":
        "IndustrialProcesses SecondaryMetalProduction SteelFoundries Finishing",
    "30400717":
        "IndustrialProcesses SecondaryMetalProduction SteelFoundries CoreOvens",
    "30400720":
        "IndustrialProcesses SecondaryMetalProduction SteelFoundries SandDryer",
    "30400721":
        "IndustrialProcesses SecondaryMetalProduction SteelFoundries SandSilo",
    "30400722":
        "IndustrialProcesses SecondaryMetalProduction SteelFoundries Muller",
    "30400723":
        "IndustrialProcesses SecondaryMetalProduction SteelFoundries ConveyorsElevators",
    "30400724":
        "IndustrialProcesses SecondaryMetalProduction SteelFoundries SandScreens",
    "30400725":
        "IndustrialProcesses SecondaryMetalProduction SteelFoundries CastingCleaningTumblers",
    "30400726":
        "IndustrialProcesses SecondaryMetalProduction SteelFoundries CastingCleaningChippers",
    "30400730":
        "IndustrialProcesses SecondaryMetalProduction SteelFoundries ShellCoreMachine",
    "30400731":
        "IndustrialProcesses SecondaryMetalProduction SteelFoundries CoreMachinesOther",
    "30400732":
        "IndustrialProcesses SecondaryMetalProduction SteelFoundries ElectricArcFurnaceBaghouse",
    "30400733":
        "IndustrialProcesses SecondaryMetalProduction SteelFoundries ElectricArcFurnaceBaghouseDustHandling",
    "30400735":
        "IndustrialProcesses SecondaryMetalProduction SteelFoundries RawMaterialUnloading",
    "30400736":
        "IndustrialProcesses SecondaryMetalProduction SteelFoundries ConveyorsElevatorsRawMaterial",
    "30400737":
        "IndustrialProcesses SecondaryMetalProduction SteelFoundries RawMaterialSilo",
    "30400739":
        "IndustrialProcesses SecondaryMetalProduction SteelFoundries ScrapCentrifugation",
    "30400740":
        "IndustrialProcesses SecondaryMetalProduction SteelFoundries ReheatingFurnaceNaturalGas",
    "30400741":
        "IndustrialProcesses SecondaryMetalProduction SteelFoundries ScrapHeating",
    "30400744":
        "IndustrialProcesses SecondaryMetalProduction SteelFoundries Ladle",
    "30400745":
        "IndustrialProcesses SecondaryMetalProduction SteelFoundries FugitiveEmissionsFurnace",
    "30400760":
        "IndustrialProcesses SecondaryMetalProduction SteelFoundries AlloyFeeding",
    "30400765":
        "IndustrialProcesses SecondaryMetalProduction SteelFoundries BilletCutting",
    "30400768":
        "IndustrialProcesses SecondaryMetalProduction SteelFoundries ScrapHandling",
    "30400770":
        "IndustrialProcesses SecondaryMetalProduction SteelFoundries SlagStoragePile",
    "30400775":
        "IndustrialProcesses SecondaryMetalProduction SteelFoundries SlagCrushing",
    "30400780":
        "IndustrialProcesses SecondaryMetalProduction SteelFoundries LimerockHandling",
    "30400785":
        "IndustrialProcesses SecondaryMetalProduction SteelFoundries RoofMonitorsHotMetalTransfer",
    "30400799":
        "IndustrialProcesses SecondaryMetalProduction SteelFoundries OtherNotClassified",
    "30400803":
        "IndustrialProcesses SecondaryMetalProduction Zinc PotFurnace",
    "30400805":
        "IndustrialProcesses SecondaryMetalProduction Zinc GalvanizingKettle",
    "30400809":
        "IndustrialProcesses SecondaryMetalProduction Zinc RotarySweatFurnace",
    "30400812":
        "IndustrialProcesses SecondaryMetalProduction Zinc CrushingScreeningofZincResidues",
    "30400814":
        "IndustrialProcesses SecondaryMetalProduction Zinc KettleSweatFurnaceCleanMetallicScrap",
    "30400818":
        "IndustrialProcesses SecondaryMetalProduction Zinc ReverberatorySweatFurnaceCleanMetallicScrap",
    "30400824":
        "IndustrialProcesses SecondaryMetalProduction Zinc KettleSweatFurnaceGeneralMetallicScrap",
    "30400828":
        "IndustrialProcesses SecondaryMetalProduction Zinc ReverberatorySweatFurnaceGeneralMetallicScrap",
    "30400840":
        "IndustrialProcesses SecondaryMetalProduction Zinc Alloying",
    "30400841":
        "IndustrialProcesses SecondaryMetalProduction Zinc ScrapMeltingCrucible",
    "30400842":
        "IndustrialProcesses SecondaryMetalProduction Zinc ScrapMeltingReverberatoryFurnace",
    "30400843":
        "IndustrialProcesses SecondaryMetalProduction Zinc ScrapMeltingElectricInductionFurnace",
    "30400853":
        "IndustrialProcesses SecondaryMetalProduction Zinc GraphiteRodDistillation",
    "30400854":
        "IndustrialProcesses SecondaryMetalProduction Zinc RetortDistillationOxidation",
    "30400864":
        "IndustrialProcesses SecondaryMetalProduction Zinc KettlePotSweating",
    "30400867":
        "IndustrialProcesses SecondaryMetalProduction Zinc KettlePotMeltingFurnace",
    "30400868":
        "IndustrialProcesses SecondaryMetalProduction Zinc CrucibleMeltingFurnace",
    "30400869":
        "IndustrialProcesses SecondaryMetalProduction Zinc ReverberatoryMeltingFurnace",
    "30400870":
        "IndustrialProcesses SecondaryMetalProduction Zinc ElectricInductionMeltingFurnace",
    "30400873":
        "IndustrialProcesses SecondaryMetalProduction Zinc Casting",
    "30400899":
        "IndustrialProcesses SecondaryMetalProduction Zinc OtherNotClassified",
    "30400901":
        "IndustrialProcesses SecondaryMetalProduction MalleableIron Annealing",
    "30400999":
        "IndustrialProcesses SecondaryMetalProduction MalleableIron OtherNotClassified",
    "30401001":
        "IndustrialProcesses SecondaryMetalProduction Nickel FluxFurnace",
    "30401002":
        "IndustrialProcesses SecondaryMetalProduction Nickel MixingBlendingGrindingScreening",
    "30401004":
        "IndustrialProcesses SecondaryMetalProduction Nickel HeatTreatFurnace",
    "30401005":
        "IndustrialProcesses SecondaryMetalProduction Nickel InductionFurnaceInletAir",
    "30401006":
        "IndustrialProcesses SecondaryMetalProduction Nickel InductionFurnaceUnderVacuum",
    "30401007":
        "IndustrialProcesses SecondaryMetalProduction Nickel ElectricArcFurnacewithCarbonElectrode",
    "30401010":
        "IndustrialProcesses SecondaryMetalProduction Nickel FinishingPicklingNeutralizing",
    "30401011":
        "IndustrialProcesses SecondaryMetalProduction Nickel FinishingGrinding",
    "30401017":
        "IndustrialProcesses SecondaryMetalProduction Nickel ReverberatoryFurnace",
    "30401018":
        "IndustrialProcesses SecondaryMetalProduction Nickel ElectricFurnace",
    "30401099":
        "IndustrialProcesses SecondaryMetalProduction Nickel OtherNotClassified",
    "30401514":
        "IndustrialProcesses SecondaryMetalProduction SteelManufacturing ElectricArcFurnaceEAFCarbonSteelChargingMeltingandRefiningTapping",
    "30401515":
        "IndustrialProcesses SecondaryMetalProduction SteelManufacturing ElectricArcFurnaceEAFCarbonSteelMeltShopRoofMonitor",
    "30402001":
        "IndustrialProcesses SecondaryMetalProduction FurnaceElectrodeManufacture Calcination",
    "30402002":
        "IndustrialProcesses SecondaryMetalProduction FurnaceElectrodeManufacture Mixing",
    "30402003":
        "IndustrialProcesses SecondaryMetalProduction FurnaceElectrodeManufacture PitchTreating",
    "30402004":
        "IndustrialProcesses SecondaryMetalProduction FurnaceElectrodeManufacture BakeFurnaces",
    "30402005":
        "IndustrialProcesses SecondaryMetalProduction FurnaceElectrodeManufacture GrafitizationofCoalbyHeatingProcess",
    "30402099":
        "IndustrialProcesses SecondaryMetalProduction FurnaceElectrodeManufacture OtherNotClassified",
    "30402201":
        "IndustrialProcesses SecondaryMetalProduction MetalHeatTreating FurnaceGeneral",
    "30402210":
        "IndustrialProcesses SecondaryMetalProduction MetalHeatTreating QuenchBath",
    "30402211":
        "IndustrialProcesses SecondaryMetalProduction MetalHeatTreating Quenching",
    "30404001":
        "IndustrialProcesses SecondaryMetalProduction LeadCableCoating General",
    "30404901":
        "IndustrialProcesses SecondaryMetalProduction MiscellaneousCastingandFabricating WaxBurnoutOven",
    "30405001":
        "IndustrialProcesses SecondaryMetalProduction MiscellaneousCastingFabricating OtherNotClassified",
    "30405101":
        "IndustrialProcesses SecondaryMetalProduction MetallicLeadProducts Ammunition",
    "30405103":
        "IndustrialProcesses SecondaryMetalProduction MetallicLeadProducts OtherSourcesofLead",
    "30482001":
        "IndustrialProcesses SecondaryMetalProduction WastewaterAggregate ProcessAreaDrains",
    "30482599":
        "IndustrialProcesses SecondaryMetalProduction WastewaterPointsofGeneration SpecifyPointofGeneration",
    "30488801":
        "IndustrialProcesses SecondaryMetalProduction FugitiveEmissions SpecifyinCommentsField",
    "30490001":
        "IndustrialProcesses SecondaryMetalProduction FuelFiredEquipment DistillateOilNo.2ProcessHeaters",
    "30490002":
        "IndustrialProcesses SecondaryMetalProduction FuelFiredEquipment ResidualOilProcessHeaters",
    "30490003":
        "IndustrialProcesses SecondaryMetalProduction FuelFiredEquipment NaturalGasProcessHeaters",
    "30490004":
        "IndustrialProcesses SecondaryMetalProduction FuelFiredEquipment ProcessGasProcessHeaters",
    "30490013":
        "IndustrialProcesses SecondaryMetalProduction FuelFiredEquipment NaturalGasIncinerators",
    "30490014":
        "IndustrialProcesses SecondaryMetalProduction FuelFiredEquipment ProcessGasIncinerators",
    "30490023":
        "IndustrialProcesses SecondaryMetalProduction FuelFiredEquipment NaturalGasFlares",
    "30490024":
        "IndustrialProcesses SecondaryMetalProduction FuelFiredEquipment ProcessGasFlares",
    "30490031":
        "IndustrialProcesses SecondaryMetalProduction FuelFiredEquipment DistillateOilNo.2Furnaces",
    "30490032":
        "IndustrialProcesses SecondaryMetalProduction FuelFiredEquipment ResidualOilFurnaces",
    "30490033":
        "IndustrialProcesses SecondaryMetalProduction FuelFiredEquipment NaturalGasFurnaces",
    "30490034":
        "IndustrialProcesses SecondaryMetalProduction FuelFiredEquipment ProcessGasFurnaces",
    "30490035":
        "IndustrialProcesses SecondaryMetalProduction FuelFiredEquipment PropaneFurnaces",
    "30499999":
        "IndustrialProcesses SecondaryMetalProduction OtherNotClassified SpecifyinCommentsField",
    "30500101":
        "IndustrialProcesses MineralProducts AsphaltRoofingManufacture AsphaltBlowingSaturantUse30505010forMACT",
    "30500102":
        "IndustrialProcesses MineralProducts AsphaltRoofingManufacture AsphaltBlowingCoatingUse30505010forMACT",
    "30500103":
        "IndustrialProcesses MineralProducts AsphaltRoofingManufacture FeltSaturationDippingOnly",
    "30500104":
        "IndustrialProcesses MineralProducts AsphaltRoofingManufacture FeltSaturationDippingSpraying",
    "30500105":
        "IndustrialProcesses MineralProducts AsphaltRoofingManufacture General",
    "30500106":
        "IndustrialProcesses MineralProducts AsphaltRoofingManufacture ShinglesandRollsSprayingOnly",
    "30500107":
        "IndustrialProcesses MineralProducts AsphaltRoofingManufacture ShinglesandRollsMineralDryer",
    "30500108":
        "IndustrialProcesses MineralProducts AsphaltRoofingManufacture ShinglesandRollsCoating",
    "30500110":
        "IndustrialProcesses MineralProducts AsphaltRoofingManufacture BlowingUse30505001forMACT",
    "30500111":
        "IndustrialProcesses MineralProducts AsphaltRoofingManufacture DippingOnly",
    "30500112":
        "IndustrialProcesses MineralProducts AsphaltRoofingManufacture SprayingOnly",
    "30500113":
        "IndustrialProcesses MineralProducts AsphaltRoofingManufacture DippingSpraying",
    "30500114":
        "IndustrialProcesses MineralProducts AsphaltRoofingManufacture AsphalticFeltCoating",
    "30500115":
        "IndustrialProcesses MineralProducts AsphaltRoofingManufacture StorageBinsSteamDryingDrums",
    "30500116":
        "IndustrialProcesses MineralProducts AsphaltRoofingManufacture ShingleSaturationDipSaturatorDryinginDrumHotLooper&Coater",
    "30500119":
        "IndustrialProcesses MineralProducts AsphaltRoofingManufacture ShingleSationSprayDipSaturDryinginDrmHotLooprCoatr&StrTk",
    "30500121":
        "IndustrialProcesses MineralProducts AsphaltRoofingManufacture StorageBinsMineralStabilizer",
    "30500130":
        "IndustrialProcesses MineralProducts AsphaltRoofingManufacture FixedRoofTankBreathingLoss",
    "30500131":
        "IndustrialProcesses MineralProducts AsphaltRoofingManufacture FixedRoofTankWorkingLoss",
    "30500132":
        "IndustrialProcesses MineralProducts AsphaltRoofingManufacture FloatingRoofTankStandingLoss",
    "30500133":
        "IndustrialProcesses MineralProducts AsphaltRoofingManufacture FloatingRoofTankWorkingLoss",
    "30500134":
        "IndustrialProcesses MineralProducts AsphaltRoofingManufacture BlownSaturantStorage",
    "30500135":
        "IndustrialProcesses MineralProducts AsphaltRoofingManufacture BlownCoatingStorage",
    "30500140":
        "IndustrialProcesses MineralProducts AsphaltRoofingManufacture GranulesUnloading",
    "30500141":
        "IndustrialProcesses MineralProducts AsphaltRoofingManufacture GranulesStorage",
    "30500142":
        "IndustrialProcesses MineralProducts AsphaltRoofingManufacture MineralDustUnloading",
    "30500143":
        "IndustrialProcesses MineralProducts AsphaltRoofingManufacture MineralDustStorage",
    "30500144":
        "IndustrialProcesses MineralProducts AsphaltRoofingManufacture GranulesTransportScrewConveyorandBucketElevator",
    "30500145":
        "IndustrialProcesses MineralProducts AsphaltRoofingManufacture MineralDustTransportScrewConveyorandBucketElevator",
    "30500146":
        "IndustrialProcesses MineralProducts AsphaltRoofingManufacture SandSurgeBin",
    "30500147":
        "IndustrialProcesses MineralProducts AsphaltRoofingManufacture GranulesSurgeBin",
    "30500150":
        "IndustrialProcesses MineralProducts AsphaltRoofingManufacture MineralDustFillerandAsphaltCoatingMixer",
    "30500151":
        "IndustrialProcesses MineralProducts AsphaltRoofingManufacture Granules",
    "30500152":
        "IndustrialProcesses MineralProducts AsphaltRoofingManufacture SandApplicator",
    "30500153":
        "IndustrialProcesses MineralProducts AsphaltRoofingManufacture CoolingRolls",
    "30500154":
        "IndustrialProcesses MineralProducts AsphaltRoofingManufacture FinishFloatingLooper",
    "30500198":
        "IndustrialProcesses MineralProducts AsphaltRoofingManufacture OtherNotElsewhereClassified",
    "30500199":
        "IndustrialProcesses MineralProducts AsphaltRoofingManufacture SeeComment",
    "30500201":
        "IndustrialProcesses MineralProducts AsphaltConcrete RotaryDryerConventionalPlantsee30500250to53forsubtypes",
    "30500202":
        "IndustrialProcesses MineralProducts AsphaltConcrete BatchMixPlantHotElevsScreensBins&Mixeralsosee45thru47",
    "30500203":
        "IndustrialProcesses MineralProducts AsphaltConcrete StoragePiles",
    "30500204":
        "IndustrialProcesses MineralProducts AsphaltConcrete ColdAggregateHandling",
    "30500205":
        "IndustrialProcesses MineralProducts AsphaltConcrete DrumDryerDrumMixPlantsee30500255thru63forsubtypes",
    "30500206":
        "IndustrialProcesses MineralProducts AsphaltConcrete AsphaltHeaterNaturalGas",
    "30500207":
        "IndustrialProcesses MineralProducts AsphaltConcrete AsphaltHeaterResidualOil",
    "30500208":
        "IndustrialProcesses MineralProducts AsphaltConcrete AsphaltHeaterDistillateOil",
    "30500209":
        "IndustrialProcesses MineralProducts AsphaltConcrete AsphaltHeaterLPG",
    "30500210":
        "IndustrialProcesses MineralProducts AsphaltConcrete AsphaltHeaterWasteOil",
    "30500211":
        "IndustrialProcesses MineralProducts AsphaltConcrete RotaryDryerConventionalPlantwithCycloneuseuse30500201wCTL",
    "30500212":
        "IndustrialProcesses MineralProducts AsphaltConcrete HeatedAsphaltStorageTanks",
    "30500213":
        "IndustrialProcesses MineralProducts AsphaltConcrete StorageSilo",
    "30500214":
        "IndustrialProcesses MineralProducts AsphaltConcrete TruckLoadout",
    "30500215":
        "IndustrialProcesses MineralProducts AsphaltConcrete InPlaceRecyclingPropane",
    "30500216":
        "IndustrialProcesses MineralProducts AsphaltConcrete ColdAggregateFeedBins",
    "30500217":
        "IndustrialProcesses MineralProducts AsphaltConcrete ColdAggregateConveyorsandElevators",
    "30500220":
        "IndustrialProcesses MineralProducts AsphaltConcrete ElevatorsBatchProcessalsosee45thru47forcomboswscrbins",
    "30500221":
        "IndustrialProcesses MineralProducts AsphaltConcrete ElevatorsContinuousProcess",
    "30500230":
        "IndustrialProcesses MineralProducts AsphaltConcrete HotBinsandScreensBatchProcessalsosee45thru47forcombos",
    "30500231":
        "IndustrialProcesses MineralProducts AsphaltConcrete HotBinsandScreensContinuousProcess",
    "30500240":
        "IndustrialProcesses MineralProducts AsphaltConcrete MixersBatchProcessalsosee45thru47forcomboswscrbins",
    "30500241":
        "IndustrialProcesses MineralProducts AsphaltConcrete MixersContinuousMixoutsidethedrumProcess",
    "30500242":
        "IndustrialProcesses MineralProducts AsphaltConcrete MixersDrumMixProcessuse305002005andsubtypes",
    "30500245":
        "IndustrialProcesses MineralProducts AsphaltConcrete BatchMixPlantHotElevatorsScreensBinsMixer&NGRotDryer",
    "30500246":
        "IndustrialProcesses MineralProducts AsphaltConcrete BatchMixPlantHotElevatorsScreensBinsMixer&#2OilRotDryer",
    "30500247":
        "IndustrialProcesses MineralProducts AsphaltConcrete BatchMixPlantHotElevsScrnsBinsMixer&WasteDrain#6OilRot",
    "30500250":
        "IndustrialProcesses MineralProducts AsphaltConcrete ConventionalContinuousMixoutsideofdrumPlantRotaryDryer",
    "30500251":
        "IndustrialProcesses MineralProducts AsphaltConcrete BatchMixPlantRotaryDryerNaturalGasFiredalsosee45",
    "30500252":
        "IndustrialProcesses MineralProducts AsphaltConcrete BatchMixPlantRotaryDryerOilFiredalsosee46",
    "30500253":
        "IndustrialProcesses MineralProducts AsphaltConcrete BatchMixPlantRotaryDryerWasteDrain#6OilFiredalsosee47",
    "30500255":
        "IndustrialProcesses MineralProducts AsphaltConcrete DrumMixPlantRotaryDrumDryerMixerNaturalGasFired",
    "30500256":
        "IndustrialProcesses MineralProducts AsphaltConcrete DrumMixPlantRotaryDrumDryerMixerNaturalGasParallelFlow",
    "30500257":
        "IndustrialProcesses MineralProducts AsphaltConcrete DrumMixPlantRotaryDrumDryerMixerNaturalGasCounterflow",
    "30500258":
        "IndustrialProcesses MineralProducts AsphaltConcrete DrumMixPlantRotaryDrumDryerMixer#2OilFired",
    "30500259":
        "IndustrialProcesses MineralProducts AsphaltConcrete DrumMixPlantRotaryDrumDryerMixer#2OilFiredParallelFlow",
    "30500260":
        "IndustrialProcesses MineralProducts AsphaltConcrete DrumMixPlantRotaryDrumDryerMixer#2OilFiredCounterflow",
    "30500261":
        "IndustrialProcesses MineralProducts AsphaltConcrete DrumMixPlantRotaryDrumDryerMixerWasteDrain#6OilFired",
    "30500262":
        "IndustrialProcesses MineralProducts AsphaltConcrete DrumMixPlRotaryDrumDryerMixerWasteDrain#6OilParallelFlo",
    "30500263":
        "IndustrialProcesses MineralProducts AsphaltConcrete DrumMixPlRotaryDrumDryerMixerWasteDrain#6OilCounterflow",
    "30500270":
        "IndustrialProcesses MineralProducts AsphaltConcrete YardEmissionsEmissionsfromasphaltintruckbeds",
    "30500290":
        "IndustrialProcesses MineralProducts AsphaltConcrete HaulRoadsGeneral",
    "30500298":
        "IndustrialProcesses MineralProducts AsphaltConcrete OtherNotClassified",
    "30500299":
        "IndustrialProcesses MineralProducts AsphaltConcrete SeeComment",
    "30500301":
        "IndustrialProcesses MineralProducts BrickandStructuralClayProductsManufacture RawMaterialDrying",
    "30500302":
        "IndustrialProcesses MineralProducts BrickandStructuralClayProductsManufacture RawMaterialCrushingGrindingandScreening",
    "30500303":
        "IndustrialProcesses MineralProducts BrickandStructuralClayProductsManufacture RawMaterialStorage",
    "30500304":
        "IndustrialProcesses MineralProducts BrickandStructuralClayProductsManufacture Curing",
    "30500305":
        "IndustrialProcesses MineralProducts BrickandStructuralClayProductsManufacture RawMaterialHandlingandTransfer",
    "30500306":
        "IndustrialProcesses MineralProducts BrickandStructuralClayProductsManufacture Pulverizing",
    "30500307":
        "IndustrialProcesses MineralProducts BrickandStructuralClayProductsManufacture Calcining",
    "30500308":
        "IndustrialProcesses MineralProducts BrickManufacture Screening",
    "30500309":
        "IndustrialProcesses MineralProducts BrickandStructuralClayProductsManufacture BlendingandMixing",
    "30500310":
        "IndustrialProcesses MineralProducts BrickandStructuralClayProductsManufacture TunnelKilnSawdustfired",
    "30500311":
        "IndustrialProcesses MineralProducts BrickandStructuralClayProductsManufacture TunnelKilnGasfired",
    "30500312":
        "IndustrialProcesses MineralProducts BrickandStructuralClayProductsManufacture TunnelKilnOilfired",
    "30500313":
        "IndustrialProcesses MineralProducts BrickandStructuralClayProductsManufacture TunnelKilnCoalfired",
    "30500314":
        "IndustrialProcesses MineralProducts BrickandStructuralClayProductsManufacture PeriodicKilnGasfired",
    "30500315":
        "IndustrialProcesses MineralProducts BrickandStructuralClayProductsManufacture PeriodicKilnOilfired",
    "30500316":
        "IndustrialProcesses MineralProducts BrickandStructuralClayProductsManufacture PeriodicKilnCoalfired",
    "30500317":
        "IndustrialProcesses MineralProducts BrickandStructuralClayProductsManufacture RawMaterialUnloading",
    "30500318":
        "IndustrialProcesses MineralProducts BrickandStructuralClayProductsManufacture TunnelKilnWoodfired",
    "30500319":
        "IndustrialProcesses MineralProducts BrickManufacture TransferandConveying",
    "30500321":
        "IndustrialProcesses MineralProducts BrickManufacture General",
    "30500330":
        "IndustrialProcesses MineralProducts BrickandStructuralClayProductsManufacture PeriodicKilnDualFuelfired",
    "30500331":
        "IndustrialProcesses MineralProducts BrickandStructuralClayProductsManufacture TunnelKilnDualFuelfired",
    "30500332":
        "IndustrialProcesses MineralProducts BrickandStructuralClayProductsManufacture OtherKilnGasfired",
    "30500335":
        "IndustrialProcesses MineralProducts BrickandStructuralClayProductsManufacture OtherKilnDualFuelfired",
    "30500340":
        "IndustrialProcesses MineralProducts BrickManufacture PrimaryCrusher",
    "30500342":
        "IndustrialProcesses MineralProducts BrickandStructuralClayProductsManufacture ExtrusionLine",
    "30500350":
        "IndustrialProcesses MineralProducts BrickandStructuralClayProductsManufacture BrickDryerHeatedWithWasteHeatFromKilnCoolingZone",
    "30500351":
        "IndustrialProcesses MineralProducts BrickandStructuralClayProductsManufacture BrickDryerHeatedWithWasteHeatAndSupplementalGasBurners",
    "30500355":
        "IndustrialProcesses MineralProducts BrickandStructuralClayProductsManufacture CoalCrushingAndStorageSystem",
    "30500361":
        "IndustrialProcesses MineralProducts BrickandStructuralClayProductsManufacture SawdustDryerHeatedWithExhaustFromSawdustfiredKiln",
    "30500370":
        "IndustrialProcesses MineralProducts BrickManufacture FiringNaturalGasfiredTunnelKilnFiringStructuralClayTile",
    "30500397":
        "IndustrialProcesses MineralProducts BrickManufacture OtherNotClassified",
    "30500398":
        "IndustrialProcesses MineralProducts BrickManufacture OtherNotClassified",
    "30500399":
        "IndustrialProcesses MineralProducts BrickandStructuralClayProductsManufacture BrickManufactureOtherNotClassified",
    "30500401":
        "IndustrialProcesses MineralProducts CalciumCarbide ElectricFurnaceHoodsandMainStack",
    "30500402":
        "IndustrialProcesses MineralProducts CalciumCarbide CokeDryer",
    "30500403":
        "IndustrialProcesses MineralProducts CalciumCarbide FurnaceRoomVents",
    "30500404":
        "IndustrialProcesses MineralProducts CalciumCarbide TapFumeVents",
    "30500405":
        "IndustrialProcesses MineralProducts CalciumCarbide PrimarySecondaryCrushing",
    "30500406":
        "IndustrialProcesses MineralProducts CalciumCarbide CircularChargingConveyor",
    "30500499":
        "IndustrialProcesses MineralProducts CalciumCarbide OtherNotClassified",
    "30500501":
        "IndustrialProcesses MineralProducts CastableRefractory FireClayRotaryDryer",
    "30500502":
        "IndustrialProcesses MineralProducts CastableRefractory RawMaterialCrushingProcessing",
    "30500503":
        "IndustrialProcesses MineralProducts CastableRefractory ElectricArcMeltFurnace",
    "30500504":
        "IndustrialProcesses MineralProducts CastableRefractory CuringOven",
    "30500505":
        "IndustrialProcesses MineralProducts CastableRefractory MoldingandShakeout",
    "30500507":
        "IndustrialProcesses MineralProducts CastableRefractory FireClayTunnelKiln",
    "30500509":
        "IndustrialProcesses MineralProducts CastableRefractory ChromiteMagnesiteOreTunnelKiln",
    "30500599":
        "IndustrialProcesses MineralProducts CastableRefractory OtherNotClassified",
    "30500606":
        "IndustrialProcesses MineralProducts CementManufacturingDryProcess Kiln",
    "30500607":
        "IndustrialProcesses MineralProducts CementManufacturingDryProcess RawMaterialUnloading",
    "30500608":
        "IndustrialProcesses MineralProducts CementManufacturingDryProcess RawMaterialPile",
    "30500609":
        "IndustrialProcesses MineralProducts CementManufacturingDryProcess PrimaryCrushing",
    "30500610":
        "IndustrialProcesses MineralProducts CementManufacturingDryProcess SecondaryCrushing",
    "30500611":
        "IndustrialProcesses MineralProducts CementManufacturingDryProcess Screening",
    "30500612":
        "IndustrialProcesses MineralProducts CementManufacturingDryProcess RawMaterialTransfer",
    "30500613":
        "IndustrialProcesses MineralProducts CementManufacturingDryProcess RawMaterialGrindingandDrying",
    "30500614":
        "IndustrialProcesses MineralProducts CementManufacturingDryProcess ClinkerCooler",
    "30500615":
        "IndustrialProcesses MineralProducts CementManufacturingDryProcess ClinkerPile",
    "30500616":
        "IndustrialProcesses MineralProducts CementManufacturingDryProcess ClinkerTransfer",
    "30500617":
        "IndustrialProcesses MineralProducts CementManufacturingDryProcess ClinkerGrinding",
    "30500618":
        "IndustrialProcesses MineralProducts CementManufacturingDryProcess CementSilo",
    "30500619":
        "IndustrialProcesses MineralProducts CementManufacturingDryProcess CementLoadOut",
    "30500620":
        "IndustrialProcesses MineralProducts CementManufacturingDryProcess Predryer",
    "30500621":
        "IndustrialProcesses MineralProducts CementManufacturingDryProcess PulverizedCoalKilnFeedUnits",
    "30500622":
        "IndustrialProcesses MineralProducts CementManufacturingDryProcess PreheaterKiln",
    "30500623":
        "IndustrialProcesses MineralProducts CementManufacturingDryProcess PreheaterPrecalcinerKiln",
    "30500624":
        "IndustrialProcesses MineralProducts CementManufacturingDryProcess RawMillFeedBelt",
    "30500625":
        "IndustrialProcesses MineralProducts CementManufacturingDryProcess RawMillWeighHopper",
    "30500626":
        "IndustrialProcesses MineralProducts CementManufacturingDryProcess RawMillAirSeparator",
    "30500627":
        "IndustrialProcesses MineralProducts CementManufacturingDryProcess FinishGrindingMillFeedBelt",
    "30500628":
        "IndustrialProcesses MineralProducts CementManufacturingDryProcess FinishGrindingMillWeighHopper",
    "30500629":
        "IndustrialProcesses MineralProducts CementManufacturingDryProcess FinishGrindingMillAirSeparator",
    "30500699":
        "IndustrialProcesses MineralProducts CementManufacturingDryProcess General",
    "30500706":
        "IndustrialProcesses MineralProducts CementManufacturingWetProcess Kiln",
    "30500707":
        "IndustrialProcesses MineralProducts CementManufacturingWetProcess RawMaterialUnloading",
    "30500708":
        "IndustrialProcesses MineralProducts CementManufacturingWetProcess RawMaterialPile",
    "30500709":
        "IndustrialProcesses MineralProducts CementManufacturingWetProcess PrimaryCrushing",
    "30500710":
        "IndustrialProcesses MineralProducts CementManufacturingWetProcess SecondaryCrushing",
    "30500711":
        "IndustrialProcesses MineralProducts CementManufacturingWetProcess Screening",
    "30500712":
        "IndustrialProcesses MineralProducts CementManufacturingWetProcess RawMaterialTransfer",
    "30500714":
        "IndustrialProcesses MineralProducts CementManufacturingWetProcess ClinkerCooler",
    "30500715":
        "IndustrialProcesses MineralProducts CementManufacturingWetProcess ClinkerPile",
    "30500716":
        "IndustrialProcesses MineralProducts CementManufacturingWetProcess ClinkerTransfer",
    "30500717":
        "IndustrialProcesses MineralProducts CementManufacturingWetProcess ClinkerGrinding",
    "30500718":
        "IndustrialProcesses MineralProducts CementManufacturingWetProcess CementSilo",
    "30500719":
        "IndustrialProcesses MineralProducts CementManufacturingWetProcess CementLoadOut",
    "30500727":
        "IndustrialProcesses MineralProducts CementManufacturingWetProcess FinishGrindingMillFeedBelt",
    "30500728":
        "IndustrialProcesses MineralProducts CementManufacturingWetProcess FinishGrindingMillWeighHopper",
    "30500729":
        "IndustrialProcesses MineralProducts CementManufacturingWetProcess FinishGrindingMillAirSeparator",
    "30500799":
        "IndustrialProcesses MineralProducts CementManufacturingWetProcess General",
    "30500801":
        "IndustrialProcesses MineralProducts CeramicClayTileManufacture DryinguseSCC30500813",
    "30500802":
        "IndustrialProcesses MineralProducts ClayCeramicsManufacture RawMaterialCrushingGrindingandMilling",
    "30500803":
        "IndustrialProcesses MineralProducts ClayCeramicsManufacture RawMaterialStorage",
    "30500804":
        "IndustrialProcesses MineralProducts ClayCeramicsManufacture ScreeningandFloating",
    "30500805":
        "IndustrialProcesses MineralProducts ClayCeramicsManufacture Mixing",
    "30500806":
        "IndustrialProcesses MineralProducts ClayCeramicsManufacture RawMaterialHandlingandTransfer",
    "30500807":
        "IndustrialProcesses MineralProducts CeramicClayTileManufacture GrindingdryuseSCC30500802",
    "30500810":
        "IndustrialProcesses MineralProducts ClayCeramicsManufacture SprayDryerNaturalGasfired",
    "30500811":
        "IndustrialProcesses MineralProducts ClayCeramicsManufacture InfraredIRDryer",
    "30500812":
        "IndustrialProcesses MineralProducts CeramicClayTileManufacture GlazingandfiringkilnuseSCCs30500845&50",
    "30500813":
        "IndustrialProcesses MineralProducts ClayCeramicsManufacture ConvectionDryer",
    "30500816":
        "IndustrialProcesses MineralProducts CeramicClayTileManufacture SizingVibratingScreens",
    "30500818":
        "IndustrialProcesses MineralProducts ClayCeramicsManufacture AirClassifier",
    "30500821":
        "IndustrialProcesses MineralProducts ClayCeramicsManufacture RotaryCalcinerNaturalGasfired",
    "30500823":
        "IndustrialProcesses MineralProducts ClayCeramicsManufacture FluidizedBedCalcinerNaturalGasfired",
    "30500828":
        "IndustrialProcesses MineralProducts CeramicClayTileManufacture MixingRawMatlsBindersPlasticizersSurfactants&OtherAgent",
    "30500830":
        "IndustrialProcesses MineralProducts ClayCeramicsManufacture FormingGeneral",
    "30500831":
        "IndustrialProcesses MineralProducts ClayCeramicsManufacture FormingTypeCasters",
    "30500835":
        "IndustrialProcesses MineralProducts ClayCeramicsManufacture GreenMachining",
    "30500840":
        "IndustrialProcesses MineralProducts ClayCeramicsManufacture PresinterThermalProcessingNaturalGasfiredKiln",
    "30500843":
        "IndustrialProcesses MineralProducts ClayCeramicsManufacture GlazePreparation",
    "30500845":
        "IndustrialProcesses MineralProducts ClayCeramicsManufacture GlazeSprayBooth",
    "30500850":
        "IndustrialProcesses MineralProducts ClayCeramicsManufacture TunnelKilnNaturalGasfired",
    "30500856":
        "IndustrialProcesses MineralProducts ClayCeramicsManufacture RefiringNaturalGasfiredKiln",
    "30500858":
        "IndustrialProcesses MineralProducts ClayCeramicsManufacture Cooler",
    "30500860":
        "IndustrialProcesses MineralProducts ClayCeramicsManufacture FinalProcessingGrindingandPolishing",
    "30500880":
        "IndustrialProcesses MineralProducts ClayCeramicsManufacture FinalProcessingSurfaceCoating",
    "30500899":
        "IndustrialProcesses MineralProducts ClayCeramicsManufacture OtherNotClassified",
    "30500901":
        "IndustrialProcesses MineralProducts ClayandFlyAshSintering FlyAshSintering",
    "30500902":
        "IndustrialProcesses MineralProducts ClayandFlyAshSintering ClayCokeSintering",
    "30500903":
        "IndustrialProcesses MineralProducts ClayandFlyAshSintering NaturalClayShaleSintering",
    "30500904":
        "IndustrialProcesses MineralProducts ClayandFlyAshSintering RawClayShaleCrushingScreening",
    "30500905":
        "IndustrialProcesses MineralProducts ClayandFlyAshSintering RawClayShaleTransferConveying",
    "30500906":
        "IndustrialProcesses MineralProducts ClayandFlyAshSintering RawClayShaleStoragePiles",
    "30500908":
        "IndustrialProcesses MineralProducts ClayandFlyAshSintering SinteredClayShaleProductCrushingScreening",
    "30500909":
        "IndustrialProcesses MineralProducts ClayandFlyAshSintering ExpandedShaleClinkerCooling",
    "30500910":
        "IndustrialProcesses MineralProducts ClayandFlyAshSintering ExpandedShaleStorage",
    "30500915":
        "IndustrialProcesses MineralProducts ClayandFlyAshSintering RotaryKiln",
    "30500916":
        "IndustrialProcesses MineralProducts ClayandFlyAshSintering Dryer",
    "30500999":
        "IndustrialProcesses MineralProducts ClayandFlyAshSintering OtherNotClassified",
    "30501001":
        "IndustrialProcesses MineralProducts CoalMiningCleaningandMaterialHandling FluidizedBedReactor",
    "30501002":
        "IndustrialProcesses MineralProducts CoalMiningCleaningandMaterialHandling FlashDryer",
    "30501003":
        "IndustrialProcesses MineralProducts CoalMiningCleaningandMaterialHandling MultilouveredDryer",
    "30501004":
        "IndustrialProcesses MineralProducts CoalMiningCleaningandMaterialHandling RotaryDryer",
    "30501005":
        "IndustrialProcesses MineralProducts CoalMiningCleaningandMaterialHandling CascadeDryer",
    "30501006":
        "IndustrialProcesses MineralProducts CoalMiningCleaningandMaterialHandling Conveyor",
    "30501007":
        "IndustrialProcesses MineralProducts CoalMiningCleaningandMaterialHandling Screen",
    "30501008":
        "IndustrialProcesses MineralProducts CoalMiningCleaningandMaterialHandling Unloading",
    "30501009":
        "IndustrialProcesses MineralProducts CoalMiningCleaningandMaterialHandling RawCoalStorage",
    "30501010":
        "IndustrialProcesses MineralProducts CoalMiningCleaningandMaterialHandling Crushing",
    "30501011":
        "IndustrialProcesses MineralProducts CoalMiningCleaningandMaterialHandling CoalTransfer",
    "30501012":
        "IndustrialProcesses MineralProducts CoalMiningCleaningandMaterialHandling Screening",
    "30501013":
        "IndustrialProcesses MineralProducts CoalMiningCleaningandMaterialHandling CoalCleaningAirTable",
    "30501014":
        "IndustrialProcesses MineralProducts CoalMiningCleaningandMaterialHandling CleanedCoalStorage",
    "30501015":
        "IndustrialProcesses MineralProducts CoalMiningCleaningandMaterialHandling CoalLoadingForCleanCoalLoadingUSE30501016",
    "30501016":
        "IndustrialProcesses MineralProducts CoalMiningCleaningandMaterialHandling CleanCoalLoading",
    "30501017":
        "IndustrialProcesses MineralProducts CoalMiningCleaningandMaterialHandling SecondaryCrushing",
    "30501021":
        "IndustrialProcesses MineralProducts CoalMiningCleaningandMaterialHandling OverburdenRemoval",
    "30501022":
        "IndustrialProcesses MineralProducts CoalMiningCleaningandMaterialHandling DrillingBlasting",
    "30501024":
        "IndustrialProcesses MineralProducts CoalMiningCleaningandMaterialHandling Hauling",
    "30501029":
        "IndustrialProcesses MineralProducts CoalMiningCleaningandMaterialHandling CoalCleaningStaticThickener",
    "30501030":
        "IndustrialProcesses MineralProducts CoalMiningCleaningandMaterialHandling TopsoilRemovalSeealso30501033353637424548",
    "30501031":
        "IndustrialProcesses MineralProducts CoalMiningCleaningandMaterialHandling ScrapersTravelMode",
    "30501032":
        "IndustrialProcesses MineralProducts CoalMiningCleaningandMaterialHandling TopsoilUnloading",
    "30501033":
        "IndustrialProcesses MineralProducts CoalMiningCleaningandMaterialHandling OverburdenSeealso30501030353637424548",
    "30501034":
        "IndustrialProcesses MineralProducts CoalMiningCleaningandMaterialHandling CoalSeamDrilling",
    "30501035":
        "IndustrialProcesses MineralProducts CoalMiningCleaningandMaterialHandling BlastingCoalOverburden",
    "30501036":
        "IndustrialProcesses MineralProducts CoalMiningCleaningandMaterialHandling DraglineOverburdenRemoval",
    "30501037":
        "IndustrialProcesses MineralProducts CoalMiningCleaningandMaterialHandling TruckLoadingOverburden",
    "30501038":
        "IndustrialProcesses MineralProducts CoalMiningCleaningandMaterialHandling TruckLoadingCoal",
    "30501039":
        "IndustrialProcesses MineralProducts CoalMiningCleaningandMaterialHandling HaulingHaulTrucks",
    "30501040":
        "IndustrialProcesses MineralProducts CoalMiningCleaningandMaterialHandling TruckUnloadingEndDumpCoal",
    "30501041":
        "IndustrialProcesses MineralProducts CoalMiningCleaningandMaterialHandling TruckUnloadingBottomDumpCoal",
    "30501042":
        "IndustrialProcesses MineralProducts CoalMiningCleaningandMaterialHandling TruckUnloadingBottomDumpOverburden",
    "30501043":
        "IndustrialProcesses MineralProducts CoalMiningCleaningandMaterialHandling OpenStoragePileCoal",
    "30501044":
        "IndustrialProcesses MineralProducts CoalMiningCleaningandMaterialHandling TrainLoadingCoal",
    "30501045":
        "IndustrialProcesses MineralProducts CoalMiningCleaningandMaterialHandling BulldozingOverburden",
    "30501046":
        "IndustrialProcesses MineralProducts CoalMiningCleaningandMaterialHandling BulldozingCoal",
    "30501047":
        "IndustrialProcesses MineralProducts CoalMiningCleaningandMaterialHandling Grading",
    "30501048":
        "IndustrialProcesses MineralProducts CoalMiningCleaningandMaterialHandling OverburdenReplacement",
    "30501049":
        "IndustrialProcesses MineralProducts CoalMiningCleaningandMaterialHandling WindErosionExposedAreas",
    "30501050":
        "IndustrialProcesses MineralProducts CoalMiningCleaningandMaterialHandling VehicleTrafficLightMediumVehicles",
    "30501051":
        "IndustrialProcesses MineralProducts CoalMiningCleaningandMaterialHandling SurfaceMiningOperationsOpenStoragePileSpoils",
    "30501060":
        "IndustrialProcesses MineralProducts CoalMiningCleaningandMaterialHandling SurfaceMiningOperationsPrimaryCrushing",
    "30501061":
        "IndustrialProcesses MineralProducts CoalMiningCleaningandMaterialHandling SurfaceMiningOperationsSecondaryCrushing",
    "30501062":
        "IndustrialProcesses MineralProducts CoalMiningCleaningandMaterialHandling SurfaceMiningOperationsScreening",
    "30501090":
        "IndustrialProcesses MineralProducts CoalMiningCleaningandMaterialHandling HaulRoads",
    "30501099":
        "IndustrialProcesses MineralProducts CoalMiningCleaningandMaterialHandling OtherNotClassified",
    "30501101":
        "IndustrialProcesses MineralProducts ConcreteBatching TotalFacilityEmissionsexceptroaddust&windblowndust",
    "30501104":
        "IndustrialProcesses MineralProducts ConcreteBatching AggregateTransfertoElevatedStorage",
    "30501105":
        "IndustrialProcesses MineralProducts ConcreteBatching SandTransfertoElevatedStorage",
    "30501106":
        "IndustrialProcesses MineralProducts ConcreteBatching TransferSandAggregatetoElevatedBinsSeeAlso04&05",
    "30501107":
        "IndustrialProcesses MineralProducts ConcreteBatching CementUnloadingtoElevatedStorageSilo",
    "30501108":
        "IndustrialProcesses MineralProducts ConcreteBatching WeightHopperLoadingofSandandAggregate",
    "30501109":
        "IndustrialProcesses MineralProducts ConcreteBatching MixerLoadingofCementSandAggregate",
    "30501110":
        "IndustrialProcesses MineralProducts ConcreteBatching LoadingofTransitMixTruck",
    "30501111":
        "IndustrialProcesses MineralProducts ConcreteBatching LoadingofDrybatchTruck",
    "30501112":
        "IndustrialProcesses MineralProducts ConcreteBatching MixingWet",
    "30501113":
        "IndustrialProcesses MineralProducts ConcreteBatching MixingDry",
    "30501114":
        "IndustrialProcesses MineralProducts ConcreteBatching TransferringConveyorsElevators",
    "30501115":
        "IndustrialProcesses MineralProducts ConcreteBatching StorageBinsHoppers",
    "30501117":
        "IndustrialProcesses MineralProducts ConcreteBatching CementSupplementUnloadingtoElevatedStorageSilo",
    "30501120":
        "IndustrialProcesses MineralProducts ConcreteBatching AsbestosCementProducts",
    "30501121":
        "IndustrialProcesses MineralProducts ConcreteBatching AggregateDeliverytoGroundStorage",
    "30501122":
        "IndustrialProcesses MineralProducts ConcreteBatching SandDeliverytoGroundStorage",
    "30501123":
        "IndustrialProcesses MineralProducts ConcreteBatching AggregateTransfertoConveyor",
    "30501124":
        "IndustrialProcesses MineralProducts ConcreteBatching SandTransfertoConveyor",
    "30501199":
        "IndustrialProcesses MineralProducts ConcreteBatching OtherNotClassified",
    "30501201":
        "IndustrialProcesses MineralProducts FiberglassManufacturing RegenerativeFurnaceWooltypeFiber",
    "30501202":
        "IndustrialProcesses MineralProducts FiberglassManufacturing RecuperativeFurnaceWooltypeFiber",
    "30501203":
        "IndustrialProcesses MineralProducts FiberglassManufacturing ElectricFurnaceWooltypeFiber",
    "30501204":
        "IndustrialProcesses MineralProducts FiberglassManufacturing FormingRotarySpunWooltypeFiber",
    "30501205":
        "IndustrialProcesses MineralProducts FiberglassManufacturing CuringOvenRotarySpunWooltypeFiber",
    "30501206":
        "IndustrialProcesses MineralProducts FiberglassManufacturing CoolingWooltypeFiber",
    "30501207":
        "IndustrialProcesses MineralProducts FiberglassManufacturing UnitMelterFurnaceWooltypeFiber",
    "30501208":
        "IndustrialProcesses MineralProducts FiberglassManufacturing FormingFlameAttenuationWooltypeFiber",
    "30501209":
        "IndustrialProcesses MineralProducts FiberglassManufacturing CuringFlameAttenuationWooltypeFiber",
    "30501211":
        "IndustrialProcesses MineralProducts FiberglassManufacturing RegenerativeFurnaceTextiletypeFiber",
    "30501212":
        "IndustrialProcesses MineralProducts FiberglassManufacturing RecuperativeFurnaceTextiletypeFiber",
    "30501213":
        "IndustrialProcesses MineralProducts FiberglassManufacturing UnitMelterFurnaceTextiletypeFiber",
    "30501214":
        "IndustrialProcesses MineralProducts FiberglassManufacturing FormingProcessTextiletypeFiber",
    "30501215":
        "IndustrialProcesses MineralProducts FiberglassManufacturing CuringOvenTextiletypeFiber",
    "30501217":
        "IndustrialProcesses MineralProducts FiberglassManufacturing OxyfuelFurnaceWooltypeFiber",
    "30501221":
        "IndustrialProcesses MineralProducts FiberglassManufacturing RawMaterialUnloadingConveying",
    "30501222":
        "IndustrialProcesses MineralProducts FiberglassManufacturing RawMaterialStorageBins",
    "30501223":
        "IndustrialProcesses MineralProducts FiberglassManufacturing RawMaterialMixingWeighing",
    "30501224":
        "IndustrialProcesses MineralProducts FiberglassManufacturing RawMaterialCrushingCharging",
    "30501299":
        "IndustrialProcesses MineralProducts FiberglassManufacturing OtherNotClassified",
    "30501301":
        "IndustrialProcesses MineralProducts FritManufacture Generaluse30501305or30501306",
    "30501303":
        "IndustrialProcesses MineralProducts FritManufacture DryMixingofrawmaterials",
    "30501305":
        "IndustrialProcesses MineralProducts FritManufacture RotarySmeltingFurnace",
    "30501306":
        "IndustrialProcesses MineralProducts FritManufacture ContinuousSmeltingFurnace",
    "30501310":
        "IndustrialProcesses MineralProducts FritManufacture WaterSprayQuenchingtoshattermaterialintosmallparticles",
    "30501315":
        "IndustrialProcesses MineralProducts FritManufacture DryMillingofquenchedfritwithaballmill",
    "30501399":
        "IndustrialProcesses MineralProducts FritManufacture OtherNotClassified",
    "30501401":
        "IndustrialProcesses MineralProducts GlassManufacture FurnaceGeneral",
    "30501402":
        "IndustrialProcesses MineralProducts GlassManufacture ContainerGlassMeltingFurnace",
    "30501403":
        "IndustrialProcesses MineralProducts GlassManufacture FlatGlassMeltingFurnace",
    "30501404":
        "IndustrialProcesses MineralProducts GlassManufacture PressedandBlownGlassMeltingFurnace",
    "30501405":
        "IndustrialProcesses MineralProducts GlassManufacture Presintering",
    "30501406":
        "IndustrialProcesses MineralProducts GlassManufacture ContainerGlassFormingFinishing",
    "30501407":
        "IndustrialProcesses MineralProducts GlassManufacture FlatGlassFormingFinishing",
    "30501408":
        "IndustrialProcesses MineralProducts GlassManufacture PressedandBlownGlassFormingFinishing",
    "30501410":
        "IndustrialProcesses MineralProducts GlassManufacture RawMaterialHandlingAllTypesofGlass",
    "30501411":
        "IndustrialProcesses MineralProducts GlassManufacture General",
    "30501412":
        "IndustrialProcesses MineralProducts GlassManufacture HoldTanks",
    "30501413":
        "IndustrialProcesses MineralProducts GlassManufacture CulletCrushingGrinding",
    "30501414":
        "IndustrialProcesses MineralProducts GlassManufacture GroundCulletBeadingFurnace",
    "30501415":
        "IndustrialProcesses MineralProducts GlassManufacture GlassEtchingwithHydrofluoricAcidSolution",
    "30501416":
        "IndustrialProcesses MineralProducts GlassManufacture GlassManufacturing",
    "30501418":
        "IndustrialProcesses MineralProducts GlassManufacture Pelletizing",
    "30501420":
        "IndustrialProcesses MineralProducts GlassManufacture MirrorPlatingGeneral",
    "30501421":
        "IndustrialProcesses MineralProducts GlassManufacture DemineralizerGeneral",
    "30501499":
        "IndustrialProcesses MineralProducts GlassManufacture SeeComment",
    "30501501":
        "IndustrialProcesses MineralProducts GypsumManufacture RotaryOreDryer",
    "30501502":
        "IndustrialProcesses MineralProducts GypsumManufacture PrimaryGrinderRollerMills",
    "30501503":
        "IndustrialProcesses MineralProducts GypsumManufacture NotClassified",
    "30501504":
        "IndustrialProcesses MineralProducts GypsumManufacture Conveying",
    "30501505":
        "IndustrialProcesses MineralProducts GypsumManufacture PrimaryCrushingGypsumOre",
    "30501506":
        "IndustrialProcesses MineralProducts GypsumManufacture SecondaryCrushingGypsumOre",
    "30501507":
        "IndustrialProcesses MineralProducts GypsumManufacture ScreeningGypsumOre",
    "30501508":
        "IndustrialProcesses MineralProducts GypsumManufacture StockpileGypsumOre",
    "30501509":
        "IndustrialProcesses MineralProducts GypsumManufacture StorageBinsGypsumOre",
    "30501510":
        "IndustrialProcesses MineralProducts GypsumManufacture StorageBinsLandplaster",
    "30501511":
        "IndustrialProcesses MineralProducts GypsumManufacture ContinuousKettleCalciner",
    "30501512":
        "IndustrialProcesses MineralProducts GypsumManufacture FlashCalciner",
    "30501513":
        "IndustrialProcesses MineralProducts GypsumManufacture ImpactMill",
    "30501514":
        "IndustrialProcesses MineralProducts GypsumManufacture StorageBinsStucco",
    "30501515":
        "IndustrialProcesses MineralProducts GypsumManufacture TubeBallMills",
    "30501516":
        "IndustrialProcesses MineralProducts GypsumManufacture Mixers",
    "30501517":
        "IndustrialProcesses MineralProducts GypsumManufacture Bagging",
    "30501518":
        "IndustrialProcesses MineralProducts GypsumManufacture MixersConveyors",
    "30501519":
        "IndustrialProcesses MineralProducts GypsumManufacture FormingLine",
    "30501520":
        "IndustrialProcesses MineralProducts GypsumManufacture DryingKiln",
    "30501521":
        "IndustrialProcesses MineralProducts GypsumManufacture EndSawing8Ft.",
    "30501522":
        "IndustrialProcesses MineralProducts GypsumManufacture EndSawing12Ft.",
    "30501599":
        "IndustrialProcesses MineralProducts GypsumManufacture SeeComment",
    "30501601":
        "IndustrialProcesses MineralProducts LimeManufacture PrimaryCrushing",
    "30501602":
        "IndustrialProcesses MineralProducts LimeManufacture SecondaryCrushingScreening",
    "30501603":
        "IndustrialProcesses MineralProducts LimeManufacture CalciningVerticalKiln",
    "30501604":
        "IndustrialProcesses MineralProducts LimeManufacture CalciningRotaryKilnSeeSCCCodes30501618192021",
    "30501605":
        "IndustrialProcesses MineralProducts LimeManufacture CalciningGasfiredCalcimaticKiln",
    "30501606":
        "IndustrialProcesses MineralProducts LimeManufacture FluidizedBedKiln",
    "30501607":
        "IndustrialProcesses MineralProducts LimeManufacture RawMaterialTransferandConveying",
    "30501608":
        "IndustrialProcesses MineralProducts LimeManufacture RawMaterialUnloading",
    "30501609":
        "IndustrialProcesses MineralProducts LimeManufacture HydratorAtmospheric",
    "30501610":
        "IndustrialProcesses MineralProducts LimeManufacture RawMaterialStoragePiles",
    "30501611":
        "IndustrialProcesses MineralProducts LimeManufacture ProductCooler",
    "30501612":
        "IndustrialProcesses MineralProducts LimeManufacture PressureHydrator",
    "30501613":
        "IndustrialProcesses MineralProducts LimeManufacture LimeSilos",
    "30501614":
        "IndustrialProcesses MineralProducts LimeManufacture PackingShipping",
    "30501615":
        "IndustrialProcesses MineralProducts LimeManufacture ProductTransferandConveying",
    "30501616":
        "IndustrialProcesses MineralProducts LimeManufacture PrimaryScreening",
    "30501617":
        "IndustrialProcesses MineralProducts LimeManufacture MultipleHearthCalciner",
    "30501618":
        "IndustrialProcesses MineralProducts LimeManufacture CalciningCoalfiredRotaryKiln",
    "30501619":
        "IndustrialProcesses MineralProducts LimeManufacture CalciningGasfiredRotaryKiln",
    "30501620":
        "IndustrialProcesses MineralProducts LimeManufacture CalciningCoalandGasfiredRotaryKiln",
    "30501621":
        "IndustrialProcesses MineralProducts LimeManufacture CalciningCoalandCokefiredRotaryKiln",
    "30501622":
        "IndustrialProcesses MineralProducts LimeManufacture CalciningCoalfiredRotaryPreheaterKiln",
    "30501623":
        "IndustrialProcesses MineralProducts LimeManufacture CalciningGasfiredParallelFlowRegenerativeKiln",
    "30501624":
        "IndustrialProcesses MineralProducts LimeManufacture ConveyorTransferPrimaryCrushedMaterial",
    "30501625":
        "IndustrialProcesses MineralProducts LimeManufacture SecondaryTertiaryScreening",
    "30501626":
        "IndustrialProcesses MineralProducts LimeManufacture ProductLoadingEnclosedTruck",
    "30501627":
        "IndustrialProcesses MineralProducts LimeManufacture ProductLoadingOpenTruck",
    "30501628":
        "IndustrialProcesses MineralProducts LimeManufacture Pulverizing",
    "30501629":
        "IndustrialProcesses MineralProducts LimeManufacture TertiaryScreeningAfterPulverizing",
    "30501630":
        "IndustrialProcesses MineralProducts LimeManufacture ScreeningAfterCalcination",
    "30501631":
        "IndustrialProcesses MineralProducts LimeManufacture CrushingandPulverizingAfterCalcinating",
    "30501632":
        "IndustrialProcesses MineralProducts LimeManufacture Milling",
    "30501633":
        "IndustrialProcesses MineralProducts LimeManufacture SeparatorAfterHydrator",
    "30501640":
        "IndustrialProcesses MineralProducts LimeManufacture VehicleTraffic",
    "30501650":
        "IndustrialProcesses MineralProducts LimeManufacture QuarryingRawLimestone",
    "30501660":
        "IndustrialProcesses MineralProducts LimeManufacture WasteTreatment",
    "30501699":
        "IndustrialProcesses MineralProducts LimeManufacture SeeComment",
    "30501701":
        "IndustrialProcesses MineralProducts MineralWoolManufacturing Cupola",
    "30501702":
        "IndustrialProcesses MineralProducts MineralWoolManufacturing ReverberatoryFurnace",
    "30501703":
        "IndustrialProcesses MineralProducts MineralWoolManufacturing BlowChamber",
    "30501704":
        "IndustrialProcesses MineralProducts MineralWoolManufacturing CuringOven",
    "30501705":
        "IndustrialProcesses MineralProducts MineralWoolManufacturing Cooler",
    "30501706":
        "IndustrialProcesses MineralProducts MineralWoolManufacturing GranulatedProductsProcessing",
    "30501707":
        "IndustrialProcesses MineralProducts MineralWoolManufacturing Handling",
    "30501708":
        "IndustrialProcesses MineralProducts MineralWoolManufacturing Packaging",
    "30501709":
        "IndustrialProcesses MineralProducts MineralWoolManufacturing BattApplication",
    "30501710":
        "IndustrialProcesses MineralProducts MineralWoolManufacturing StorageofOilsandBinders",
    "30501711":
        "IndustrialProcesses MineralProducts MineralWoolManufacturing MixingofOilsandBinders",
    "30501799":
        "IndustrialProcesses MineralProducts MineralWoolManufacturing OtherNotClassified",
    "30501801":
        "IndustrialProcesses MineralProducts PerliteManufacturing VerticalFurnace",
    "30501899":
        "IndustrialProcesses MineralProducts PerliteManufacturing OtherNotClassified",
    "30501901":
        "IndustrialProcesses MineralProducts PhosphateRock Drying",
    "30501902":
        "IndustrialProcesses MineralProducts PhosphateRock Grinding",
    "30501903":
        "IndustrialProcesses MineralProducts PhosphateRock TransferStorage",
    "30501999":
        "IndustrialProcesses MineralProducts PhosphateRock OtherNotClassified",
    "30502001":
        "IndustrialProcesses MineralProducts StoneQuarryingProcessing PrimaryCrushing",
    "30502002":
        "IndustrialProcesses MineralProducts StoneQuarryingProcessing SecondaryCrushingScreening",
    "30502003":
        "IndustrialProcesses MineralProducts StoneQuarryingProcessing TertiaryCrushingScreening",
    "30502004":
        "IndustrialProcesses MineralProducts StoneQuarryingProcessing RecrushingScreening",
    "30502005":
        "IndustrialProcesses MineralProducts StoneQuarryingProcessing FinesMill",
    "30502006":
        "IndustrialProcesses MineralProducts StoneQuarryingProcessing MiscellaneousOperationsScreenConveyHandling",
    "30502007":
        "IndustrialProcesses MineralProducts StoneQuarryingProcessing OpenStorage",
    "30502008":
        "IndustrialProcesses MineralProducts StoneQuarryingProcessing CutStoneGeneral",
    "30502009":
        "IndustrialProcesses MineralProducts StoneQuarryingProcessing BlastingGeneral",
    "30502010":
        "IndustrialProcesses MineralProducts StoneQuarryingProcessing Drilling",
    "30502011":
        "IndustrialProcesses MineralProducts StoneQuarryingProcessing Hauling",
    "30502012":
        "IndustrialProcesses MineralProducts StoneQuarryingProcessing Drying",
    "30502013":
        "IndustrialProcesses MineralProducts StoneQuarryingProcessing BarGrizzlies",
    "30502014":
        "IndustrialProcesses MineralProducts StoneQuarryingProcessing ShakerScreens",
    "30502015":
        "IndustrialProcesses MineralProducts StoneQuarryingProcessing VibratingScreens",
    "30502016":
        "IndustrialProcesses MineralProducts StoneQuarryingProcessing RevolvingScreens",
    "30502017":
        "IndustrialProcesses MineralProducts StoneQuarryingProcessing Pugmill",
    "30502021":
        "IndustrialProcesses MineralProducts StoneQuarryingProcessing FinesScreening",
    "30502031":
        "IndustrialProcesses MineralProducts StoneQuarryingProcessing TruckUnloading",
    "30502032":
        "IndustrialProcesses MineralProducts StoneQuarryingProcessing TruckLoadingConveyor",
    "30502033":
        "IndustrialProcesses MineralProducts StoneQuarryingProcessing TruckLoadingFrontEndLoader",
    "30502090":
        "IndustrialProcesses MineralProducts StoneQuarryingProcessing HaulRoadsGeneral",
    "30502099":
        "IndustrialProcesses MineralProducts StoneQuarryingProcessing NotClassified",
    "30502101":
        "IndustrialProcesses MineralProducts SaltMining General",
    "30502102":
        "IndustrialProcesses MineralProducts SaltMining GranulationStackDryer",
    "30502103":
        "IndustrialProcesses MineralProducts SaltMining FiltrationVacuumFilter",
    "30502104":
        "IndustrialProcesses MineralProducts SaltMining Crushing",
    "30502105":
        "IndustrialProcesses MineralProducts SaltMining Screening",
    "30502106":
        "IndustrialProcesses MineralProducts SaltMining Conveying",
    "30502201":
        "IndustrialProcesses MineralProducts PotashProduction MineGrindingDrying",
    "30502299":
        "IndustrialProcesses MineralProducts PotashProduction OtherNotClassified",
    "30502401":
        "IndustrialProcesses MineralProducts MagnesiumCarbonate MineProcess",
    "30502499":
        "IndustrialProcesses MineralProducts MagnesiumCarbonate OtherNotClassified",
    "30502501":
        "IndustrialProcesses MineralProducts ConstructionSandandGravel TotalPlantGeneral",
    "30502502":
        "IndustrialProcesses MineralProducts ConstructionSandandGravel AggregateStorage",
    "30502503":
        "IndustrialProcesses MineralProducts ConstructionSandandGravel MaterialTransferandConveying",
    "30502504":
        "IndustrialProcesses MineralProducts ConstructionSandandGravel Hauling",
    "30502505":
        "IndustrialProcesses MineralProducts ConstructionSandandGravel PileFormingStacker",
    "30502506":
        "IndustrialProcesses MineralProducts ConstructionSandandGravel BulkLoading",
    "30502507":
        "IndustrialProcesses MineralProducts ConstructionSandandGravel StoragePiles",
    "30502508":
        "IndustrialProcesses MineralProducts ConstructionSandandGravel DryerSee30502720thru24forIndustrialSandDryers",
    "30502509":
        "IndustrialProcesses MineralProducts ConstructionSandandGravel CoolerSee30502730forIndustrialSandCoolers",
    "30502510":
        "IndustrialProcesses MineralProducts ConstructionSandandGravel Crushing",
    "30502511":
        "IndustrialProcesses MineralProducts ConstructionSandandGravel Screening",
    "30502512":
        "IndustrialProcesses MineralProducts ConstructionSandandGravel OverburdenRemoval",
    "30502513":
        "IndustrialProcesses MineralProducts ConstructionSandandGravel Excavating",
    "30502514":
        "IndustrialProcesses MineralProducts ConstructionSandandGravel DrillingandBlasting",
    "30502522":
        "IndustrialProcesses MineralProducts ConstructionSandandGravel RodmillingFineCrushingofConstructionSand",
    "30502523":
        "IndustrialProcesses MineralProducts ConstructionSandandGravel FineScreeningofConstructionSandFollowingDewateringorRodmilling",
    "30502599":
        "IndustrialProcesses MineralProducts ConstructionSandandGravel NotClassified",
    "30502601":
        "IndustrialProcesses MineralProducts DiatomaceousEarth Handling",
    "30502699":
        "IndustrialProcesses MineralProducts DiatomaceousEarth OtherNotClassified",
    "30502701":
        "IndustrialProcesses MineralProducts IndustrialSandandGravel PrimaryCrushingofRawMaterial",
    "30502705":
        "IndustrialProcesses MineralProducts IndustrialSandandGravel SecondaryCrushing",
    "30502709":
        "IndustrialProcesses MineralProducts IndustrialSandandGravel GrindingSizeReductionto50MicronsorSmaller",
    "30502713":
        "IndustrialProcesses MineralProducts IndustrialSandandGravel ScreeningSizeClassification",
    "30502717":
        "IndustrialProcesses MineralProducts IndustrialSandandGravel DrainingRemovalofMoisturetoAbout6%AfterFrothFlotation",
    "30502720":
        "IndustrialProcesses MineralProducts IndustrialSandandGravel SandDryingGasorOilfiredRotaryorFluidizedBedDryer",
    "30502721":
        "IndustrialProcesses MineralProducts IndustrialSandandGravel SandDryingGasfiredRotaryDryer",
    "30502722":
        "IndustrialProcesses MineralProducts IndustrialSandandGravel SandDryingOilfiredRotaryDryer",
    "30502723":
        "IndustrialProcesses MineralProducts IndustrialSandandGravel SandDryingGasfiredFluidizedBedDryer",
    "30502730":
        "IndustrialProcesses MineralProducts IndustrialSandandGravel CoolingofDriedSand",
    "30502740":
        "IndustrialProcesses MineralProducts IndustrialSandandGravel FinalClassifyingScreeningtoClassifySandbySize",
    "30502760":
        "IndustrialProcesses MineralProducts IndustrialSandandGravel SandHandlingTransferandStorage",
    "30502910":
        "IndustrialProcesses MineralProducts LightweightAggregateManufacture RotaryKiln",
    "30502920":
        "IndustrialProcesses MineralProducts LightweightAggregateManufacture ClinkerCooler",
    "30503099":
        "IndustrialProcesses MineralProducts CeramicElectricParts OtherNotClassified",
    "30503104":
        "IndustrialProcesses MineralProducts AsbestosMining Loading",
    "30503107":
        "IndustrialProcesses MineralProducts AsbestosMining Unloading",
    "30503109":
        "IndustrialProcesses MineralProducts AsbestosMining VentilationofProcessOperations",
    "30503201":
        "IndustrialProcesses MineralProducts AsbestosMilling Crushing",
    "30503299":
        "IndustrialProcesses MineralProducts AsbestosMilling OtherNotClassified",
    "30503301":
        "IndustrialProcesses MineralProducts Vermiculite General",
    "30503321":
        "IndustrialProcesses MineralProducts Vermiculite VermiculiteConcentrateDryingRotaryDryerGasfired",
    "30503331":
        "IndustrialProcesses MineralProducts Vermiculite CrushingofDriedVermiculiteConcentrate",
    "30503336":
        "IndustrialProcesses MineralProducts Vermiculite ScreeningSizeClassificationofCrushedVermiculiteConcentrate",
    "30503341":
        "IndustrialProcesses MineralProducts Vermiculite ConveyingofVermiculiteConcentratetoStorage",
    "30503351":
        "IndustrialProcesses MineralProducts Vermiculite ExfoliationofVermiculiteConcentrateGasfiredVerticalFurnace",
    "30503361":
        "IndustrialProcesses MineralProducts Vermiculite ProductGrindingGrindingofExfoliatedVermiculite",
    "30503366":
        "IndustrialProcesses MineralProducts Vermiculite ProductClassifyingAirClassificationofExfoliatedVermiculite",
    "30503401":
        "IndustrialProcesses MineralProducts Feldspar BallMill",
    "30503402":
        "IndustrialProcesses MineralProducts Feldspar Dryer",
    "30503501":
        "IndustrialProcesses MineralProducts AbrasiveGrainProcessing PrimaryCrushing",
    "30503503":
        "IndustrialProcesses MineralProducts AbrasiveGrainProcessing FinalCrushing",
    "30503505":
        "IndustrialProcesses MineralProducts AbrasiveGrainProcessing WashingDrying",
    "30503507":
        "IndustrialProcesses MineralProducts AbrasiveGrainProcessing AirClassification",
    "30503601":
        "IndustrialProcesses MineralProducts BondedAbrasivesManufacturing Mixing",
    "30503602":
        "IndustrialProcesses MineralProducts BondedAbrasivesManufacturing Molding",
    "30503605":
        "IndustrialProcesses MineralProducts BondedAbrasivesManufacturing FiringorCuring",
    "30503606":
        "IndustrialProcesses MineralProducts BondedAbrasivesManufacturing Cooling",
    "30503607":
        "IndustrialProcesses MineralProducts BondedAbrasivesManufacturing FinalMachining",
    "30503702":
        "IndustrialProcesses MineralProducts CoatedAbrasivesManufacturing MakeCoatApplication",
    "30503704":
        "IndustrialProcesses MineralProducts CoatedAbrasivesManufacturing Drying",
    "30503705":
        "IndustrialProcesses MineralProducts CoatedAbrasivesManufacturing SizeCoatApplication",
    "30503706":
        "IndustrialProcesses MineralProducts CoatedAbrasivesManufacturing FinalDryingandCuring",
    "30503708":
        "IndustrialProcesses MineralProducts CoatedAbrasivesManufacturing FinalProduction",
    "30503811":
        "IndustrialProcesses MineralProducts PulverizedMineralProcessing CoarseandFineGrindingDryMode",
    "30503812":
        "IndustrialProcesses MineralProducts PulverizedMineralProcessing ClassificationDryMode",
    "30503813":
        "IndustrialProcesses MineralProducts PulverizedMineralProcessing ProductStorage",
    "30503814":
        "IndustrialProcesses MineralProducts PulverizedMineralProcessing ProductPackagingandBulkLoading",
    "30503831":
        "IndustrialProcesses MineralProducts PulverizedMineralProcessing CoarseGrindingWetMode",
    "30503832":
        "IndustrialProcesses MineralProducts PulverizedMineralProcessing BeneficiationviaFlotation",
    "30503835":
        "IndustrialProcesses MineralProducts PulverizedMineralProcessing FlashDryer",
    "30504001":
        "IndustrialProcesses MineralProducts MiningandQuarryingofNonmetallicMinerals OpenPitBlasting",
    "30504002":
        "IndustrialProcesses MineralProducts MiningandQuarryingofNonmetallicMinerals OpenPitDrilling",
    "30504003":
        "IndustrialProcesses MineralProducts MiningandQuarryingofNonmetallicMinerals OpenPitCobbing",
    "30504010":
        "IndustrialProcesses MineralProducts MiningandQuarryingofNonmetallicMinerals UndergroundVentilation",
    "30504020":
        "IndustrialProcesses MineralProducts MiningandQuarryingofNonmetallicMinerals Loading",
    "30504021":
        "IndustrialProcesses MineralProducts MiningandQuarryingofNonmetallicMinerals ConveyHaulMaterial",
    "30504022":
        "IndustrialProcesses MineralProducts MiningandQuarryingofNonmetallicMinerals ConveyHaulWaste",
    "30504023":
        "IndustrialProcesses MineralProducts MiningandQuarryingofNonmetallicMinerals Unloading",
    "30504024":
        "IndustrialProcesses MineralProducts MiningandQuarryingofNonmetallicMinerals OverburdenStripping",
    "30504025":
        "IndustrialProcesses MineralProducts MiningandQuarryingofNonmetallicMinerals Stockpiling",
    "30504030":
        "IndustrialProcesses MineralProducts MiningandQuarryingofNonmetallicMinerals PrimaryCrusher",
    "30504031":
        "IndustrialProcesses MineralProducts MiningandQuarryingofNonmetallicMinerals SecondaryCrusher",
    "30504032":
        "IndustrialProcesses MineralProducts MiningandQuarryingofNonmetallicMinerals OreConcentrator",
    "30504033":
        "IndustrialProcesses MineralProducts MiningandQuarryingofNonmetallicMinerals OreDryer",
    "30504034":
        "IndustrialProcesses MineralProducts MiningandQuarryingofNonmetallicMinerals Screening",
    "30504036":
        "IndustrialProcesses MineralProducts MiningandQuarryingofNonmetallicMinerals TailingPiles",
    "30504099":
        "IndustrialProcesses MineralProducts MiningandQuarryingofNonmetallicMinerals OtherNotClassified",
    "30504101":
        "IndustrialProcesses MineralProducts ClayprocessingKaolin Mining",
    "30504102":
        "IndustrialProcesses MineralProducts ClayprocessingKaolin Rawmaterialstorage",
    "30504103":
        "IndustrialProcesses MineralProducts ClayprocessingKaolin Rawmaterialtransfer",
    "30504115":
        "IndustrialProcesses MineralProducts ClayprocessingKaolin RawmaterialcrushingNEC",
    "30504119":
        "IndustrialProcesses MineralProducts ClayprocessingKaolin RawmaterialgrindingNEC",
    "30504129":
        "IndustrialProcesses MineralProducts ClayprocessingKaolin ScreeningNEC",
    "30504130":
        "IndustrialProcesses MineralProducts ClayprocessingKaolin Dryingrotarydryer",
    "30504131":
        "IndustrialProcesses MineralProducts ClayprocessingKaolin Dryingspraydryer",
    "30504132":
        "IndustrialProcesses MineralProducts ClayprocessingKaolin Dryingaprondryer",
    "30504139":
        "IndustrialProcesses MineralProducts ClayprocessingKaolin DryingdryerNEC",
    "30504140":
        "IndustrialProcesses MineralProducts ClayprocessingKaolin Calciningrotarycalciner",
    "30504141":
        "IndustrialProcesses MineralProducts ClayprocessingKaolin Calciningmultiplehearthfurnace",
    "30504142":
        "IndustrialProcesses MineralProducts ClayprocessingKaolin Calciningflashcalciner",
    "30504149":
        "IndustrialProcesses MineralProducts ClayprocessingKaolin CalciningcalcinerNEC",
    "30504150":
        "IndustrialProcesses MineralProducts ClayprocessingKaolin Productgrinding",
    "30504151":
        "IndustrialProcesses MineralProducts ClayprocessingKaolin Productscreeningclassification",
    "30504170":
        "IndustrialProcesses MineralProducts ClayprocessingKaolin Producttransfer",
    "30504171":
        "IndustrialProcesses MineralProducts ClayprocessingKaolin Productstorage",
    "30504172":
        "IndustrialProcesses MineralProducts ClayprocessingKaolin Productpackaging",
    "30504202":
        "IndustrialProcesses MineralProducts ClayprocessingBallclay Rawmaterialstorage",
    "30504203":
        "IndustrialProcesses MineralProducts ClayprocessingBallclay Rawmaterialtransfer",
    "30504215":
        "IndustrialProcesses MineralProducts ClayprocessingBallclay RawmaterialcrushingNEC",
    "30504219":
        "IndustrialProcesses MineralProducts ClayprocessingBallclay RawmaterialgrindingNEC",
    "30504230":
        "IndustrialProcesses MineralProducts ClayprocessingBallclay Dryingrotarydryer",
    "30504232":
        "IndustrialProcesses MineralProducts ClayprocessingBallclay Dryingaprondryer",
    "30504233":
        "IndustrialProcesses MineralProducts ClayprocessingBallclay Dryingvibratinggratedryer",
    "30504239":
        "IndustrialProcesses MineralProducts ClayprocessingBallclay DryingdryerNEC",
    "30504250":
        "IndustrialProcesses MineralProducts ClayprocessingBallclay Productgrinding",
    "30504270":
        "IndustrialProcesses MineralProducts ClayprocessingBallclay Producttransfer",
    "30504271":
        "IndustrialProcesses MineralProducts ClayprocessingBallclay Productstorage",
    "30504272":
        "IndustrialProcesses MineralProducts ClayprocessingBallclay Productpackaging",
    "30504302":
        "IndustrialProcesses MineralProducts ClayprocessingFireclay Rawmaterialstorage",
    "30504303":
        "IndustrialProcesses MineralProducts ClayprocessingFireclay Rawmaterialtransfer",
    "30504315":
        "IndustrialProcesses MineralProducts ClayprocessingFireclay RawmaterialcrushingNEC",
    "30504329":
        "IndustrialProcesses MineralProducts ClayprocessingFireclay ScreeningNEC",
    "30504330":
        "IndustrialProcesses MineralProducts ClayprocessingFireclay Dryingrotarydryer",
    "30504340":
        "IndustrialProcesses MineralProducts ClayprocessingFireclay Calciningrotarycalciner",
    "30504341":
        "IndustrialProcesses MineralProducts ClayprocessingFireclay Calciningmultiplehearthfurnace",
    "30504350":
        "IndustrialProcesses MineralProducts ClayprocessingFireclay Productgrinding",
    "30504351":
        "IndustrialProcesses MineralProducts ClayprocessingFireclay Productscreeningclassification",
    "30504370":
        "IndustrialProcesses MineralProducts ClayprocessingFireclay Producttransfer",
    "30504372":
        "IndustrialProcesses MineralProducts ClayprocessingFireclay Productpackaging",
    "30504401":
        "IndustrialProcesses MineralProducts ClayprocessingBentonite Mining",
    "30504402":
        "IndustrialProcesses MineralProducts ClayprocessingBentonite Rawmaterialstorage",
    "30504403":
        "IndustrialProcesses MineralProducts ClayprocessingBentonite Rawmaterialtransfer",
    "30504415":
        "IndustrialProcesses MineralProducts ClayprocessingBentonite RawmaterialcrushingNEC",
    "30504419":
        "IndustrialProcesses MineralProducts ClayprocessingBentonite RawmaterialgrindingNEC",
    "30504430":
        "IndustrialProcesses MineralProducts ClayprocessingBentonite Dryingrotarydryer",
    "30504431":
        "IndustrialProcesses MineralProducts ClayprocessingBentonite Dryingspraydryer",
    "30504432":
        "IndustrialProcesses MineralProducts ClayprocessingBentonite Dryingaprondryer",
    "30504433":
        "IndustrialProcesses MineralProducts ClayprocessingBentonite Dryingvibratinggratedryer",
    "30504439":
        "IndustrialProcesses MineralProducts ClayprocessingBentonite DryingdryerNEC",
    "30504450":
        "IndustrialProcesses MineralProducts ClayprocessingBentonite Productgrinding",
    "30504451":
        "IndustrialProcesses MineralProducts ClayprocessingBentonite Productscreeningclassification",
    "30504470":
        "IndustrialProcesses MineralProducts ClayprocessingBentonite Producttransfer",
    "30504471":
        "IndustrialProcesses MineralProducts ClayprocessingBentonite Productstorage",
    "30504472":
        "IndustrialProcesses MineralProducts ClayprocessingBentonite Productpackaging",
    "30504502":
        "IndustrialProcesses MineralProducts ClayprocessingFullersearth Rawmaterialstorage",
    "30504503":
        "IndustrialProcesses MineralProducts ClayprocessingFullersearth Rawmaterialtransfer",
    "30504519":
        "IndustrialProcesses MineralProducts ClayprocessingFullersearth RawmaterialgrindingNEC",
    "30504530":
        "IndustrialProcesses MineralProducts ClayprocessingFullersearth Dryingrotarydryer",
    "30504539":
        "IndustrialProcesses MineralProducts ClayprocessingFullersearth DryingdryerNEC",
    "30504550":
        "IndustrialProcesses MineralProducts ClayprocessingFullersearth Productgrinding",
    "30504551":
        "IndustrialProcesses MineralProducts ClayprocessingFullersearth Productscreeningclassification",
    "30504570":
        "IndustrialProcesses MineralProducts ClayprocessingFullersearth Producttransfer",
    "30504571":
        "IndustrialProcesses MineralProducts ClayprocessingFullersearth Productstorage",
    "30504572":
        "IndustrialProcesses MineralProducts ClayprocessingFullersearth Productpackaging",
    "30504601":
        "IndustrialProcesses MineralProducts ClayprocessingCommonclayandshaleNEC Mining",
    "30504602":
        "IndustrialProcesses MineralProducts ClayprocessingCommonclayandshaleNEC Rawmaterialstorage",
    "30504603":
        "IndustrialProcesses MineralProducts ClayprocessingCommonclayandshaleNEC Rawmaterialtransfer",
    "30504615":
        "IndustrialProcesses MineralProducts ClayprocessingCommonclayandshaleNEC RawmaterialcrushingNEC",
    "30504619":
        "IndustrialProcesses MineralProducts ClayprocessingCommonclayandshaleNEC RawmaterialgrindingNEC",
    "30504629":
        "IndustrialProcesses MineralProducts ClayprocessingCommonclayandshaleNEC ScreeningNEC",
    "30504631":
        "IndustrialProcesses MineralProducts ClayprocessingCommonclayandshaleNEC Dryingspraydryer",
    "30504670":
        "IndustrialProcesses MineralProducts ClayprocessingCommonclayandshaleNEC Producttransfer",
    "30504671":
        "IndustrialProcesses MineralProducts ClayprocessingCommonclayandshaleNEC Productstorage",
    "30505001":
        "IndustrialProcesses MineralProducts AsphaltProcessingBlowing AsphaltProcessingBlowing",
    "30505005":
        "IndustrialProcesses MineralProducts AsphaltProcessingBlowing AsphaltStoragePriortoBlowing",
    "30505010":
        "IndustrialProcesses MineralProducts AsphaltProcessingBlowing AsphaltBlowingStill",
    "30505020":
        "IndustrialProcesses MineralProducts AsphaltProcessingBlowing AsphaltHeaterNaturalGas",
    "30505022":
        "IndustrialProcesses MineralProducts AsphaltProcessingBlowing AsphaltHeaterDistillateOil",
    "30505023":
        "IndustrialProcesses MineralProducts AsphaltProcessingBlowing AsphaltHeaterLPG",
    "30508908":
        "IndustrialProcesses MineralProducts TalcProcessing ConveyorTransferofRawTalctoPrimaryCrusher",
    "30508909":
        "IndustrialProcesses MineralProducts TalcProcessing NaturalGasFiredCrudeOreDryer",
    "30508911":
        "IndustrialProcesses MineralProducts TalcProcessing Primarycrusher",
    "30508912":
        "IndustrialProcesses MineralProducts TalcProcessing CrushedTalcRailcarLoading",
    "30508914":
        "IndustrialProcesses MineralProducts TalcProcessing CrushedTalcStorageBinLoading",
    "30508917":
        "IndustrialProcesses MineralProducts TalcProcessing ScreeningOversizeOretoReturntoPrimaryCrusher",
    "30508921":
        "IndustrialProcesses MineralProducts TalcProcessing NaturalGasfiredRotaryDryer",
    "30508931":
        "IndustrialProcesses MineralProducts TalcProcessing NaturalGasfiredRotaryCalciner",
    "30508945":
        "IndustrialProcesses MineralProducts TalcProcessing GrindingofDriedTalc",
    "30508949":
        "IndustrialProcesses MineralProducts TalcProcessing GroundTalcStorageBinLoading",
    "30508950":
        "IndustrialProcesses MineralProducts TalcProcessing AirClassifierSizeClassificationofGroundTalc",
    "30508955":
        "IndustrialProcesses MineralProducts TalcProcessing PelletDryer",
    "30508958":
        "IndustrialProcesses MineralProducts TalcProcessing PneumaticConveyorVents",
    "30508982":
        "IndustrialProcesses MineralProducts TalcProcessing CustomGrindingAdditionalSizeReduction",
    "30508985":
        "IndustrialProcesses MineralProducts TalcProcessing FinalProductStorageBinLoading",
    "30508988":
        "IndustrialProcesses MineralProducts TalcProcessing Packaging",
    "30509001":
        "IndustrialProcesses MineralProducts Mica RotaryDryer",
    "30509002":
        "IndustrialProcesses MineralProducts Mica FluidEnergyMillGrinding",
    "30509201":
        "IndustrialProcesses MineralProducts CatalystManufacturing TransferringandHandling",
    "30509202":
        "IndustrialProcesses MineralProducts CatalystManufacturing MixingandBlending",
    "30509203":
        "IndustrialProcesses MineralProducts CatalystManufacturing Reacting",
    "30509204":
        "IndustrialProcesses MineralProducts CatalystManufacturing Drying",
    "30509205":
        "IndustrialProcesses MineralProducts CatalystManufacturing Storage",
    "30510001":
        "IndustrialProcesses MineralProducts BulkMaterialsElevators Unloading",
    "30510002":
        "IndustrialProcesses MineralProducts BulkMaterialsElevators Loading",
    "30510003":
        "IndustrialProcesses MineralProducts BulkMaterialsElevators RemovalfromBins",
    "30510004":
        "IndustrialProcesses MineralProducts BulkMaterialsElevators Drying",
    "30510005":
        "IndustrialProcesses MineralProducts BulkMaterialsElevators Cleaning",
    "30510006":
        "IndustrialProcesses MineralProducts BulkMaterialsElevators ElevatorLegsHeadhouse",
    "30510007":
        "IndustrialProcesses MineralProducts BulkMaterialsElevators TripperGalleryBelt",
    "30510101":
        "IndustrialProcesses MineralProducts BulkMaterialsConveyors AmmoniumSulfate",
    "30510102":
        "IndustrialProcesses MineralProducts BulkMaterialsConveyors Cement",
    "30510103":
        "IndustrialProcesses MineralProducts BulkMaterialsConveyors Coal",
    "30510104":
        "IndustrialProcesses MineralProducts BulkMaterialsConveyors Coke",
    "30510105":
        "IndustrialProcesses MineralProducts BulkMaterialsConveyors Limestone",
    "30510106":
        "IndustrialProcesses MineralProducts BulkMaterialsConveyors PhosphateRock",
    "30510107":
        "IndustrialProcesses MineralProducts BulkMaterialsConveyors ScrapMetal",
    "30510108":
        "IndustrialProcesses MineralProducts BulkMaterialsConveyors Sulfur",
    "30510196":
        "IndustrialProcesses MineralProducts BulkMaterialsConveyors ChemicalSpecifyinComments",
    "30510197":
        "IndustrialProcesses MineralProducts BulkMaterialsConveyors FertilizerSpecifyinComments",
    "30510198":
        "IndustrialProcesses MineralProducts BulkMaterialsConveyors MineralSpecifyinComments",
    "30510199":
        "IndustrialProcesses MineralProducts BulkMaterialsConveyors OtherNotClassified",
    "30510201":
        "IndustrialProcesses MineralProducts BulkMaterialsStorageBins AmmoniumSulfate",
    "30510202":
        "IndustrialProcesses MineralProducts BulkMaterialsStorageBins Cement",
    "30510203":
        "IndustrialProcesses MineralProducts BulkMaterialsStorageBins Coal",
    "30510204":
        "IndustrialProcesses MineralProducts BulkMaterialsStorageBins Coke",
    "30510205":
        "IndustrialProcesses MineralProducts BulkMaterialsStorageBins Limestone",
    "30510206":
        "IndustrialProcesses MineralProducts BulkMaterialsStorageBins PhosphateRock",
    "30510208":
        "IndustrialProcesses MineralProducts BulkMaterialsStorageBins Sulfur",
    "30510209":
        "IndustrialProcesses MineralProducts BulkMaterialsStorageBins Sand",
    "30510296":
        "IndustrialProcesses MineralProducts BulkMaterialsStorageBins ChemicalSpecifyinComments",
    "30510297":
        "IndustrialProcesses MineralProducts BulkMaterialsStorageBins FertilizerSpecifyinComments",
    "30510298":
        "IndustrialProcesses MineralProducts BulkMaterialsStorageBins MineralSpecifyinComments",
    "30510299":
        "IndustrialProcesses MineralProducts BulkMaterialsStorageBins OtherNotClassified",
    "30510302":
        "IndustrialProcesses MineralProducts BulkMaterialsOpenStockpiles Cement",
    "30510303":
        "IndustrialProcesses MineralProducts BulkMaterialsOpenStockpiles Coal",
    "30510304":
        "IndustrialProcesses MineralProducts BulkMaterialsOpenStockpiles Coke",
    "30510305":
        "IndustrialProcesses MineralProducts BulkMaterialsOpenStockpiles Limestone",
    "30510306":
        "IndustrialProcesses MineralProducts BulkMaterialsOpenStockpiles PhosphateRock",
    "30510307":
        "IndustrialProcesses MineralProducts BulkMaterialsOpenStockpiles ScrapMetal",
    "30510308":
        "IndustrialProcesses MineralProducts BulkMaterialsOpenStockpiles Sulfur",
    "30510309":
        "IndustrialProcesses MineralProducts BulkMaterialsOpenStockpiles Sand",
    "30510310":
        "IndustrialProcesses MineralProducts BulkMaterialsOpenStockpiles Fluxes",
    "30510396":
        "IndustrialProcesses MineralProducts BulkMaterialsOpenStockpiles ChemicalSpecifyinComments",
    "30510397":
        "IndustrialProcesses MineralProducts BulkMaterialsOpenStockpiles FertilizerSpecifyinComments",
    "30510398":
        "IndustrialProcesses MineralProducts BulkMaterialsOpenStockpiles MineralSpecifyinComments",
    "30510399":
        "IndustrialProcesses MineralProducts BulkMaterialsOpenStockpiles OtherNotClassified",
    "30510401":
        "IndustrialProcesses MineralProducts BulkMaterialsUnloadingOperation AmmoniumSulfate",
    "30510402":
        "IndustrialProcesses MineralProducts BulkMaterialsUnloadingOperation Cement",
    "30510403":
        "IndustrialProcesses MineralProducts BulkMaterialsUnloadingOperation Coal",
    "30510404":
        "IndustrialProcesses MineralProducts BulkMaterialsUnloadingOperation Coke",
    "30510405":
        "IndustrialProcesses MineralProducts BulkMaterialsUnloadingOperation Limestone",
    "30510406":
        "IndustrialProcesses MineralProducts BulkMaterialsUnloadingOperation PhosphateRock",
    "30510408":
        "IndustrialProcesses MineralProducts BulkMaterialsUnloadingOperation Sulfur",
    "30510496":
        "IndustrialProcesses MineralProducts BulkMaterialsUnloadingOperation ChemicalSpecifyinComments",
    "30510497":
        "IndustrialProcesses MineralProducts BulkMaterialsUnloadingOperation FertilizerSpecifyinComments",
    "30510498":
        "IndustrialProcesses MineralProducts BulkMaterialsUnloadingOperation MineralSpecifyinComments",
    "30510499":
        "IndustrialProcesses MineralProducts BulkMaterialsUnloadingOperation OtherNotClassified",
    "30510502":
        "IndustrialProcesses MineralProducts BulkMaterialsLoadingOperation Cement",
    "30510503":
        "IndustrialProcesses MineralProducts BulkMaterialsLoadingOperation Coal",
    "30510504":
        "IndustrialProcesses MineralProducts BulkMaterialsLoadingOperation Coke",
    "30510505":
        "IndustrialProcesses MineralProducts BulkMaterialsLoadingOperation Limestone",
    "30510506":
        "IndustrialProcesses MineralProducts BulkMaterialsLoadingOperation PhosphateRock",
    "30510507":
        "IndustrialProcesses MineralProducts BulkMaterialsLoadingOperation ScrapMetal",
    "30510508":
        "IndustrialProcesses MineralProducts BulkMaterialsLoadingOperation Sulfur",
    "30510596":
        "IndustrialProcesses MineralProducts BulkMaterialsLoadingOperation ChemicalSpecifyinComments",
    "30510597":
        "IndustrialProcesses MineralProducts BulkMaterialsLoadingOperation FertilizerSpecifyinComments",
    "30510598":
        "IndustrialProcesses MineralProducts BulkMaterialsLoadingOperation MineralSpecifyinComments",
    "30510599":
        "IndustrialProcesses MineralProducts BulkMaterialsLoadingOperation OtherNotClassified",
    "30510604":
        "IndustrialProcesses MineralProducts BulkMaterialsScreeningSizeClassification Coke",
    "30510709":
        "IndustrialProcesses MineralProducts BulkMaterialsSeparationCyclones Bauxite",
    "30510808":
        "IndustrialProcesses MineralProducts BulkMaterialsGrindingCrushing Sulfur",
    "30510809":
        "IndustrialProcesses MineralProducts BulkMaterialsGrindingCrushing Bauxite",
    "30515001":
        "IndustrialProcesses MineralProducts Calcining RawMaterialHandling",
    "30515002":
        "IndustrialProcesses MineralProducts Calcining General",
    "30515003":
        "IndustrialProcesses MineralProducts Calcining GrindingMilling",
    "30515004":
        "IndustrialProcesses MineralProducts Calcining FinishedProductHandling",
    "30515005":
        "IndustrialProcesses MineralProducts Calcining Mixing",
    "30531010":
        "IndustrialProcesses MineralProducts CoalMiningCleaningandMaterialHandlingSee305010 Crushing",
    "30531014":
        "IndustrialProcesses MineralProducts CoalMiningCleaningandMaterialHandlingSee305010 CleanedCoalStorage",
    "30531090":
        "IndustrialProcesses MineralProducts CoalMiningCleaningandMaterialHandlingSee305010 HaulRoadsGeneral",
    "30580001":
        "IndustrialProcesses MineralProducts EquipmentLeaks EquipmentLeaks",
    "30582001":
        "IndustrialProcesses MineralProducts WastewaterAggregate ProcessAreaDrains",
    "30588801":
        "IndustrialProcesses MineralProducts FugitiveEmissions SpecifyinCommentsField",
    "30588803":
        "IndustrialProcesses MineralProducts FugitiveEmissions SpecifyinCommentsField",
    "30590001":
        "IndustrialProcesses MineralProducts FuelFiredEquipment DistillateOilNo.2ProcessHeaters",
    "30590002":
        "IndustrialProcesses MineralProducts FuelFiredEquipment ResidualOilProcessHeaters",
    "30590003":
        "IndustrialProcesses MineralProducts FuelFiredEquipment NaturalGasProcessHeaters",
    "30590005":
        "IndustrialProcesses MineralProducts FuelFiredEquipment LiquifiedPetroleumGasLPGProcessHeaters",
    "30590011":
        "IndustrialProcesses MineralProducts FuelFiredEquipment DistillateOilNo.2Incinerators",
    "30590013":
        "IndustrialProcesses MineralProducts FuelFiredEquipment NaturalGasIncinerators",
    "30590023":
        "IndustrialProcesses MineralProducts FuelFiredEquipment NaturalGasFlares",
    "30599999":
        "IndustrialProcesses MineralProducts OtherNotDefined SpecifyinCommentsField",
    "30600101":
        "IndustrialProcesses PetroleumIndustry ProcessHeaters Oilfired",
    "30600102":
        "IndustrialProcesses PetroleumIndustry ProcessHeaters Gasfired",
    "30600103":
        "IndustrialProcesses PetroleumIndustry ProcessHeaters Oil",
    "30600104":
        "IndustrialProcesses PetroleumIndustry ProcessHeaters Gas",
    "30600105":
        "IndustrialProcesses PetroleumIndustry ProcessHeaters NaturalGas",
    "30600106":
        "IndustrialProcesses PetroleumIndustry ProcessHeaters ProcessGas",
    "30600107":
        "IndustrialProcesses PetroleumIndustry ProcessHeaters LiquifiedPetroleumGasLPG",
    "30600108":
        "IndustrialProcesses PetroleumIndustry ProcessHeaters LandfillGas",
    "30600111":
        "IndustrialProcesses PetroleumIndustry ProcessHeaters No.6Oil",
    "30600199":
        "IndustrialProcesses PetroleumIndustry ProcessHeaters OtherNotElsewhereClassified",
    "30600201":
        "IndustrialProcesses PetroleumIndustry CatalyticCrackingUnit FluidCatalyticCrackingUnit",
    "30600202":
        "IndustrialProcesses PetroleumIndustry CatalyticCrackingUnit CatalystHandlingSystem",
    "30600203":
        "IndustrialProcesses PetroleumIndustry CatalyticCrackingUnit FluidCatalyticCrackingUnitwithCOBoilerNaturalGas",
    "30600204":
        "IndustrialProcesses PetroleumIndustry CatalyticCrackingUnit FluidCatalyticCrackingUnitwithCOBoilerProcessGas",
    "30600205":
        "IndustrialProcesses PetroleumIndustry CatalyticCrackingUnit FluidCatalyticCrackingUnitwithCOBoilerOil",
    "30600207":
        "IndustrialProcesses PetroleumIndustry CatalyticCrackingUnit ThermalCatalyticCrackingUnit",
    "30600301":
        "IndustrialProcesses PetroleumIndustry CatalyticCrackingUnit ThermalCatalyticCrackingUnit",
    "30600401":
        "IndustrialProcesses PetroleumIndustry BlowdownSystems BlowdownSystemwithVaporRecoverySystemwithFlaring",
    "30600402":
        "IndustrialProcesses PetroleumIndustry BlowdownSystems AllNotElsewhereClassified",
    "30600503":
        "IndustrialProcesses PetroleumIndustry WastewaterTreatment ProcessDrainsandWastewaterSeparators",
    "30600505":
        "IndustrialProcesses PetroleumIndustry WastewaterTreatment WastewaterTreatmentwithoutSeparator",
    "30600508":
        "IndustrialProcesses PetroleumIndustry WastewaterTreatment OilWaterSeparator",
    "30600510":
        "IndustrialProcesses PetroleumIndustry WastewaterTreatment LiquidLiquidSeparatorHydrocarbonAmine",
    "30600511":
        "IndustrialProcesses PetroleumIndustry WastewaterTreatment SourWaterTreating",
    "30600514":
        "IndustrialProcesses PetroleumIndustry WastewaterTreatment JunctionBox",
    "30600515":
        "IndustrialProcesses PetroleumIndustry WastewaterTreatment LiftStation",
    "30600516":
        "IndustrialProcesses PetroleumIndustry WastewaterTreatment AeratedImpoundment",
    "30600517":
        "IndustrialProcesses PetroleumIndustry WastewaterTreatment NonaeratedImpoundment",
    "30600518":
        "IndustrialProcesses PetroleumIndustry WastewaterTreatment Weir",
    "30600519":
        "IndustrialProcesses PetroleumIndustry WastewaterTreatment ActivatedSludgeImpoundment",
    "30600520":
        "IndustrialProcesses PetroleumIndustry WastewaterTreatment Clarifier",
    "30600521":
        "IndustrialProcesses PetroleumIndustry WastewaterTreatment OpenTrench",
    "30600522":
        "IndustrialProcesses PetroleumIndustry WastewaterTreatment AugerPumps",
    "30600602":
        "IndustrialProcesses PetroleumIndustry VacuumDistillation ColumnCondenser",
    "30600701":
        "IndustrialProcesses PetroleumIndustry CoolingTowers AllNotElsewhereClassified",
    "30600801":
        "IndustrialProcesses PetroleumIndustry FugitiveEmissions PipelineValvesandFlanges",
    "30600802":
        "IndustrialProcesses PetroleumIndustry FugitiveEmissions VesselReliefValves",
    "30600803":
        "IndustrialProcesses PetroleumIndustry FugitiveEmissions PumpSeals",
    "30600804":
        "IndustrialProcesses PetroleumIndustry FugitiveEmissions CompressorSeals",
    "30600805":
        "IndustrialProcesses PetroleumIndustry FugitiveEmissions MiscellaneousSamplingNonAsphaltBlowingPurgingetc.",
    "30600806":
        "IndustrialProcesses PetroleumIndustry FugitiveEmissions PumpSealswithControls",
    "30600807":
        "IndustrialProcesses PetroleumIndustry FugitiveEmissions BlindChanging",
    "30600811":
        "IndustrialProcesses PetroleumIndustry FugitiveEmissions PipelineValvesGasStreams",
    "30600812":
        "IndustrialProcesses PetroleumIndustry FugitiveEmissions PipelineValvesLightLiquidGasStreams",
    "30600813":
        "IndustrialProcesses PetroleumIndustry FugitiveEmissions PipelineValvesHeavyLiquidStreams",
    "30600815":
        "IndustrialProcesses PetroleumIndustry FugitiveEmissions OpenendedValvesAllStreams",
    "30600816":
        "IndustrialProcesses PetroleumIndustry FugitiveEmissions FlangesAllStreams",
    "30600817":
        "IndustrialProcesses PetroleumIndustry FugitiveEmissions PumpSealsLightLiquidGasStreams",
    "30600818":
        "IndustrialProcesses PetroleumIndustry FugitiveEmissions PumpSealsHeavyLiquidStreams",
    "30600819":
        "IndustrialProcesses PetroleumIndustry FugitiveEmissions CompressorSealsGasStreams",
    "30600820":
        "IndustrialProcesses PetroleumIndustry FugitiveEmissions CompressorSealsHeavyLiquidStreams",
    "30600821":
        "IndustrialProcesses PetroleumIndustry FugitiveEmissions DrainsAllStreams",
    "30600822":
        "IndustrialProcesses PetroleumIndustry FugitiveEmissions PressureReliefDevicesAllStreams",
    "30600901":
        "IndustrialProcesses PetroleumIndustry Flares DistillateOil",
    "30600902":
        "IndustrialProcesses PetroleumIndustry Flares ResidualOil",
    "30600903":
        "IndustrialProcesses PetroleumIndustry Flares NaturalGas",
    "30600904":
        "IndustrialProcesses PetroleumIndustry Flares ProcessGas",
    "30600905":
        "IndustrialProcesses PetroleumIndustry Flares LiquifiedPetroleumGas",
    "30600906":
        "IndustrialProcesses PetroleumIndustry Flares HydrogenSulfide",
    "30600999":
        "IndustrialProcesses PetroleumIndustry Flares NotClassified",
    "30601001":
        "IndustrialProcesses PetroleumIndustry SludgeConverter AllNotElsewhereClassified",
    "30601011":
        "IndustrialProcesses PetroleumIndustry SludgeConverter OilSludgeDewateringUnit",
    "30601101":
        "IndustrialProcesses PetroleumIndustry AsphaltBitumenProduction AsphaltBlowing",
    "30601201":
        "IndustrialProcesses PetroleumIndustry FluidCokingUnit AllNotElsewhereClassified",
    "30601301":
        "IndustrialProcesses PetroleumIndustry CokeHandlingSystem StorageTransfer",
    "30601401":
        "IndustrialProcesses PetroleumIndustry PetroleumCokeCalcining Calciner",
    "30601402":
        "IndustrialProcesses PetroleumIndustry PetroleumCokeCalcining DelayedCokingUnit",
    "30601599":
        "IndustrialProcesses PetroleumIndustry BauxiteBurning OtherNotClassified",
    "30601601":
        "IndustrialProcesses PetroleumIndustry CatalyticReformingUnit General",
    "30601602":
        "IndustrialProcesses PetroleumIndustry CatalyticReformingUnit AlkylationFeedTreater",
    "30601603":
        "IndustrialProcesses PetroleumIndustry CatalyticReformingUnit AlkylationUnitHydrofluoricAcid",
    "30601604":
        "IndustrialProcesses PetroleumIndustry CatalyticReformingUnit AlkylationUnitSulfuricAcid",
    "30601605":
        "IndustrialProcesses PetroleumIndustry CatalyticReformingUnit Continuous",
    "30601607":
        "IndustrialProcesses PetroleumIndustry CatalyticReformingUnit SemiRegenerative",
    "30601701":
        "IndustrialProcesses PetroleumIndustry CatalyticHydrotreatingUnit AllNotElsewhereClassified",
    "30601801":
        "IndustrialProcesses PetroleumIndustry HydrogenGenerationUnit AllNotElsewhereClassified",
    "30601901":
        "IndustrialProcesses PetroleumIndustry MeroxTreatingUnit AllNotElsewhereClassified",
    "30602001":
        "IndustrialProcesses PetroleumIndustry CrudeUnitAtmosphericDistillation AllNotElsewhereClassified",
    "30602101":
        "IndustrialProcesses PetroleumIndustry LightEndsFractionationUnit AllNotElsewhereClassified",
    "30602201":
        "IndustrialProcesses PetroleumIndustry GasolineBlendingUnit AllNotElsewhereClassified",
    "30602301":
        "IndustrialProcesses PetroleumIndustry HydrocrackingUnit AllNotElsewhereClassified",
    "30602501":
        "IndustrialProcesses PetroleumIndustry AlkylationUnit AlkylationFeedTreater",
    "30602502":
        "IndustrialProcesses PetroleumIndustry AlkylationUnit SulfuricAcidAlkylation",
    "30602503":
        "IndustrialProcesses PetroleumIndustry AlkylationUnit HydrofluoricAcidAlkylation",
    "30603201":
        "IndustrialProcesses PetroleumIndustry SourGasTreatingUnit AllNotElsewhereClassified",
    "30603301":
        "IndustrialProcesses PetroleumIndustry SulfurRecoveryUnit AllNotElsewhereClassified",
    "30609901":
        "IndustrialProcesses PetroleumIndustry Incinerators DistillateOilNo.2",
    "30609902":
        "IndustrialProcesses PetroleumIndustry Incinerators ResidualOil",
    "30609903":
        "IndustrialProcesses PetroleumIndustry Incinerators NaturalGas",
    "30609904":
        "IndustrialProcesses PetroleumIndustry Incinerators ProcessGas",
    "30609905":
        "IndustrialProcesses PetroleumIndustry Incinerators LiquifiedPetroleumGasLPG",
    "30610001":
        "IndustrialProcesses PetroleumIndustry LubeOilRefining AllNotElsewhereClassified",
    "30622001":
        "IndustrialProcesses PetroleumIndustry RemediationSoil AllNotElsewhereClassified",
    "30622002":
        "IndustrialProcesses PetroleumIndustry RemediationSoil ResidualOil",
    "30622003":
        "IndustrialProcesses PetroleumIndustry RemediationSoil NaturalGas",
    "30622004":
        "IndustrialProcesses PetroleumIndustry RemediationSoil DistillateOil",
    "30622005":
        "IndustrialProcesses PetroleumIndustry RemediationSoil LiquifiedPetroleumGasLPG",
    "30622006":
        "IndustrialProcesses PetroleumIndustry RemediationSoil WasteOil",
    "30622201":
        "IndustrialProcesses PetroleumIndustry RemediationVaporExtract AllNotElsewhereClassified",
    "30622203":
        "IndustrialProcesses PetroleumIndustry RemediationVaporExtract NaturalGas",
    "30622204":
        "IndustrialProcesses PetroleumIndustry RemediationVaporExtract DistillateOil",
    "30622205":
        "IndustrialProcesses PetroleumIndustry RemediationVaporExtract LiquifiedPetroleumGasLPG",
    "30622206":
        "IndustrialProcesses PetroleumIndustry RemediationVaporExtract WasteOil",
    "30622401":
        "IndustrialProcesses PetroleumIndustry RemediationAirStripping AllNotElsewhereClassified",
    "30622403":
        "IndustrialProcesses PetroleumIndustry RemediationAirStripping NaturalGas",
    "30622404":
        "IndustrialProcesses PetroleumIndustry RemediationAirStripping DistillateOil",
    "30622405":
        "IndustrialProcesses PetroleumIndustry RemediationAirStripping LiquifiedPetroleumGasLPG",
    "30622406":
        "IndustrialProcesses PetroleumIndustry RemediationAirStripping WasteOil",
    "30630005":
        "IndustrialProcesses PetroleumIndustry RerefiningofLubeOilsandGreases WasteOilStillVent",
    "30630006":
        "IndustrialProcesses PetroleumIndustry RerefiningofLubeOilsandGreases StorageTankWasteOil",
    "30630007":
        "IndustrialProcesses PetroleumIndustry RerefiningofLubeOilsandGreases StorageTankFinishedProduct",
    "30688801":
        "IndustrialProcesses PetroleumIndustry FugitiveEmissions OtherNotElsewhereClassified",
    "30688902":
        "IndustrialProcesses PetroleumIndustry FugitiveDust PavedRoadsAllVehicleTypes",
    "30699999":
        "IndustrialProcesses PetroleumIndustry OtherUnitsProcesses OtherNotElsewhereClassified",
    "30700101":
        "IndustrialProcesses PulpandPaperandWoodProducts SulfateKraftPulping DigesterSystemContinuousorBatch",
    "30700102":
        "IndustrialProcesses PulpandPaperandWoodProducts SulfateKraftPulping BrownStockWashingSystem",
    "30700103":
        "IndustrialProcesses PulpandPaperandWoodProducts SulfateKraftPulping MultipleEffectEvaporatorsandConcentrators",
    "30700104":
        "IndustrialProcesses PulpandPaperandWoodProducts SulfateKraftPulping RecoveryFurnaceDirectContactEvaporator",
    "30700105":
        "IndustrialProcesses PulpandPaperandWoodProducts SulfateKraftPulping SmeltDissolvingTank",
    "30700106":
        "IndustrialProcesses PulpandPaperandWoodProducts SulfateKraftPulping LimeKiln",
    "30700107":
        "IndustrialProcesses PulpandPaperandWoodProducts SulfateKraftPulping TurpentineCondenser",
    "30700108":
        "IndustrialProcesses PulpandPaperandWoodProducts SulfateKraftPulping FluidBedCalciner",
    "30700109":
        "IndustrialProcesses PulpandPaperandWoodProducts SulfateKraftPulping BlackLiquorOxidationSystem",
    "30700110":
        "IndustrialProcesses PulpandPaperandWoodProducts SulfateKraftPulping RecoveryFurnaceIndirectContactEvaporator",
    "30700112":
        "IndustrialProcesses PulpandPaperandWoodProducts SulfateKraftPulping LimeMudWashers",
    "30700113":
        "IndustrialProcesses PulpandPaperandWoodProducts SulfateKraftPulping LimeMudFilterSystem",
    "30700114":
        "IndustrialProcesses PulpandPaperandWoodProducts SulfateKraftPulping BleachPlant",
    "30700115":
        "IndustrialProcesses PulpandPaperandWoodProducts SulfateKraftPulping ChlorineDioxideGenerator",
    "30700116":
        "IndustrialProcesses PulpandPaperandWoodProducts SulfateKraftPulping TurpentineStorageandLoadingincldecantingstorageandloading",
    "30700117":
        "IndustrialProcesses PulpandPaperandWoodProducts SulfateKraftPulping Ventingofcondensatestripperoffgases",
    "30700119":
        "IndustrialProcesses PulpandPaperandWoodProducts SulfateKraftPulping SaltCakeMixTankBoilerAshHandling",
    "30700120":
        "IndustrialProcesses PulpandPaperandWoodProducts SulfateKraftPulping StockWashingScreening",
    "30700121":
        "IndustrialProcesses PulpandPaperandWoodProducts SulfateKraftPulping WastewaterGeneral",
    "30700122":
        "IndustrialProcesses PulpandPaperandWoodProducts SulfateKraftPulping CausticizingMiscellaneous",
    "30700123":
        "IndustrialProcesses PulpandPaperandWoodProducts SulfateKraftPulping LimeSlakerVent",
    "30700124":
        "IndustrialProcesses PulpandPaperandWoodProducts SulfateKraftPulping BlackLiquorStorageTanks",
    "30700125":
        "IndustrialProcesses PulpandPaperandWoodProducts SulfateKraftPulping LowVolumeHighConcentrationSystemVentingofNoncondensibleGases",
    "30700126":
        "IndustrialProcesses PulpandPaperandWoodProducts SulfateKraftPulping HighVolumeLowConcentrationSystemVentingofNoncondensibleGases",
    "30700127":
        "IndustrialProcesses PulpandPaperandWoodProducts SulfateKraftPulping NoncondensibleGasesIncinerator",
    "30700128":
        "IndustrialProcesses PulpandPaperandWoodProducts SulfateKraftPulping TotalReducedSulfurThermalOxidizeranysupplementalfuel",
    "30700130":
        "IndustrialProcesses PulpandPaperandWoodProducts SulfateKraftPulping DeckerSystem",
    "30700131":
        "IndustrialProcesses PulpandPaperandWoodProducts SulfateKraftPulping KnotterDeknotterSystem",
    "30700132":
        "IndustrialProcesses PulpandPaperandWoodProducts SulfateKraftPulping GreenLiquorProcessing",
    "30700133":
        "IndustrialProcesses PulpandPaperandWoodProducts SulfateKraftPulping WhiteLiquorProcessing",
    "30700134":
        "IndustrialProcesses PulpandPaperandWoodProducts SulfateKraftPulping OxygenDelignificationSystem",
    "30700135":
        "IndustrialProcesses PulpandPaperandWoodProducts SulfateKraftPulping PulpStorageBleachedandUnbleached",
    "30700136":
        "IndustrialProcesses PulpandPaperandWoodProducts SulfateKraftPulping TallOilSystemincludestalloilreactorandtalloilstorage",
    "30700199":
        "IndustrialProcesses PulpandPaperandWoodProducts SulfateKraftPulping OtherNotClassified",
    "30700211":
        "IndustrialProcesses PulpandPaperandWoodProducts SulfitePulping DigesterBlowPitDumpTankCalcium",
    "30700214":
        "IndustrialProcesses PulpandPaperandWoodProducts SulfitePulping DigesterBlowPitDumpTankNH3withProcessChange",
    "30700216":
        "IndustrialProcesses PulpandPaperandWoodProducts SulfitePulping BleachPlantincludesbleachingtowersfiltratetanksvacuumpump",
    "30700222":
        "IndustrialProcesses PulpandPaperandWoodProducts SulfitePulping RecoverySystemNH3includingliquorevaporators",
    "30700224":
        "IndustrialProcesses PulpandPaperandWoodProducts SulfitePulping WastewaterGeneral",
    "30700231":
        "IndustrialProcesses PulpandPaperandWoodProducts SulfitePulping AcidPlantNH3",
    "30700233":
        "IndustrialProcesses PulpandPaperandWoodProducts SulfitePulping AcidPlantCa",
    "30700234":
        "IndustrialProcesses PulpandPaperandWoodProducts SulfitePulping KnottersWashersScreensetc.",
    "30700299":
        "IndustrialProcesses PulpandPaperandWoodProducts SulfitePulping SeeComment",
    "30700301":
        "IndustrialProcesses PulpandPaperandWoodProducts SemichemicalPulping NeutralSulfiteSemichemicalPulpingDigesterBlowPitDumpTank",
    "30700302":
        "IndustrialProcesses PulpandPaperandWoodProducts SemichemicalPulping NeutralSulfiteSemichemicalPulpingEvaporator",
    "30700304":
        "IndustrialProcesses PulpandPaperandWoodProducts SemichemicalPulping NeutralSulfiteSemichemicalPulpingSulfurBurnerAbsorbers",
    "30700307":
        "IndustrialProcesses PulpandPaperandWoodProducts SemichemicalPulping NeutralSulfiteSemichemicalPulpingPulpwashingsystem",
    "30700309":
        "IndustrialProcesses PulpandPaperandWoodProducts SemichemicalPulping NeutralSulfiteSemichemicalPulpingLiquorstoragetanks",
    "30700320":
        "IndustrialProcesses PulpandPaperandWoodProducts SemichemicalPulping SemichemicalnonsulfurPulpwashingsystem",
    "30700326":
        "IndustrialProcesses PulpandPaperandWoodProducts SemichemicalPulping SemichemicalnonsulfurDigestersrefinersblowtanksblowheatrecoverysystem",
    "30700329":
        "IndustrialProcesses PulpandPaperandWoodProducts SemichemicalPulping SemichemicalnonsulfurOtherNotClassified",
    "30700399":
        "IndustrialProcesses PulpandPaperandWoodProducts SemichemicalPulping NeutralSulfiteSemichemicalPulpingOtherNotClassified",
    "30700401":
        "IndustrialProcesses PulpandPaperandWoodProducts PaperPaperboardandPulpboardManufacture PaperMachinePulpDryer",
    "30700402":
        "IndustrialProcesses PulpandPaperandWoodProducts PulpboardManufacture FiberboardGeneral",
    "30700403":
        "IndustrialProcesses PulpandPaperandWoodProducts PaperPaperboardandPulpboardManufacture RawMaterialStorageandHandling",
    "30700404":
        "IndustrialProcesses PulpandPaperandWoodProducts PaperPaperboardandPulpboardManufacture SecondaryFiberPulpingStockPreparationandRepulper",
    "30700405":
        "IndustrialProcesses PulpandPaperandWoodProducts PulpboardManufacture PaperBoardForming",
    "30700407":
        "IndustrialProcesses PulpandPaperandWoodProducts PaperPaperboardandPulpboardManufacture CoatingOperationsOnMachine",
    "30700408":
        "IndustrialProcesses PulpandPaperandWoodProducts PaperPaperboardandPulpboardManufacture SecondaryFiberPulpingDeinkingoperations",
    "30700409":
        "IndustrialProcesses PulpandPaperandWoodProducts PaperPaperboardandPulpboardManufacture CoatingOperationsOffMachine",
    "30700410":
        "IndustrialProcesses PulpandPaperandWoodProducts PaperPaperboardandPulpboardManufacture SecondaryFiberPulpingBleachingBrighteningDecoloring",
    "30700499":
        "IndustrialProcesses PulpandPaperandWoodProducts PaperPaperboardandPulpboardManufacture SeeComment",
    "30700501":
        "IndustrialProcesses PulpandPaperandWoodProducts WoodPressureTreating Creosote",
    "30700505":
        "IndustrialProcesses PulpandPaperandWoodProducts WoodPressureTreating Untreatedwoodstorage",
    "30700510":
        "IndustrialProcesses PulpandPaperandWoodProducts WoodPressureTreating Fullcellprocesscreosote",
    "30700511":
        "IndustrialProcesses PulpandPaperandWoodProducts WoodPressureTreating Fullcellprocesspentachlorophenol",
    "30700513":
        "IndustrialProcesses PulpandPaperandWoodProducts WoodPressureTreating Modifiedfullcellprocesschromatedcopperarsenate",
    "30700514":
        "IndustrialProcesses PulpandPaperandWoodProducts WoodPressureTreating Modifiedfullcellprocessotherwaterbornepreservative",
    "30700530":
        "IndustrialProcesses PulpandPaperandWoodProducts WoodPressureTreating Emptycellprocesscreosote",
    "30700531":
        "IndustrialProcesses PulpandPaperandWoodProducts WoodPressureTreating Emptycellprocesspentachlorophenol",
    "30700541":
        "IndustrialProcesses PulpandPaperandWoodProducts WoodPressureTreating Emptycellprocesswithartificialconditioningpentachlorophenol",
    "30700542":
        "IndustrialProcesses PulpandPaperandWoodProducts WoodPressureTreating Emptycellprocesswithartificialconditioningotheroilbornepreser",
    "30700543":
        "IndustrialProcesses PulpandPaperandWoodProducts WoodPressureTreating Emptycellprocesswithartificialconditioningchromatedcopperarse",
    "30700554":
        "IndustrialProcesses PulpandPaperandWoodProducts WoodPressureTreating Emptycellprocesswithsteamheatingotherwaterbornepreservative",
    "30700573":
        "IndustrialProcesses PulpandPaperandWoodProducts WoodPressureTreating Quenchingchromatedcopperarsenate",
    "30700574":
        "IndustrialProcesses PulpandPaperandWoodProducts WoodPressureTreating Quenchingotherwaterbornepreservative",
    "30700581":
        "IndustrialProcesses PulpandPaperandWoodProducts WoodPressureTreating Retortunloadingpentachlorophenol",
    "30700590":
        "IndustrialProcesses PulpandPaperandWoodProducts WoodPressureTreating Treatedwoodstoragecreosote",
    "30700591":
        "IndustrialProcesses PulpandPaperandWoodProducts WoodPressureTreating Treatedwoodstoragepentachlorophenol",
    "30700592":
        "IndustrialProcesses PulpandPaperandWoodProducts WoodPressureTreating Treatedwoodstorageotheroilbornepreservative",
    "30700593":
        "IndustrialProcesses PulpandPaperandWoodProducts WoodPressureTreating Treatedwoodstoragechromatedcopperarsenate",
    "30700594":
        "IndustrialProcesses PulpandPaperandWoodProducts WoodPressureTreating Treatedwoodstorageotherwaterbornepreservative",
    "30700597":
        "IndustrialProcesses PulpandPaperandWoodProducts WoodPressureTreating OtherNotElsewhereClassified",
    "30700598":
        "IndustrialProcesses PulpandPaperandWoodProducts WoodPressureTreating OtherNotClassified",
    "30700599":
        "IndustrialProcesses PulpandPaperandWoodProducts WoodPressureTreating OtherNotClassified",
    "30700602":
        "IndustrialProcesses PulpandPaperandWoodProducts ParticleboardManufacture DirectWoodfiredRotaryDryerUnspecifiedPines730FInletAir",
    "30700606":
        "IndustrialProcesses PulpandPaperandWoodProducts ParticleboardManufacture DirectWoodfiredRotaryDryerSouthernYellowPine",
    "30700607":
        "IndustrialProcesses PulpandPaperandWoodProducts ParticleboardManufacture DirectWoodfiredRotaryDryerSoftwood",
    "30700608":
        "IndustrialProcesses PulpandPaperandWoodProducts ParticleboardManufacture DirectWoodfiredRotaryDryermixedsofthardwoods",
    "30700610":
        "IndustrialProcesses PulpandPaperandWoodProducts ParticleboardManufacture DirectWoodfiredRotaryDryerHardwoods",
    "30700611":
        "IndustrialProcesses PulpandPaperandWoodProducts ParticleboardManufacture DirectNaturalGasFiredRotaryDryerUnspecifiedPines",
    "30700621":
        "IndustrialProcesses PulpandPaperandWoodProducts ParticleboardManufacture DirectWoodfiredRotaryFinalDryerUnspecifiedPines",
    "30700625":
        "IndustrialProcesses PulpandPaperandWoodProducts ParticleboardManufacture DirectWoodfiredRotaryDryerSoftwoodgreen50%inletmoisture",
    "30700626":
        "IndustrialProcesses PulpandPaperandWoodProducts ParticleboardManufacture DirectWoodfiredRotaryDryermixedsofthardwoodsgreen",
    "30700628":
        "IndustrialProcesses PulpandPaperandWoodProducts ParticleboardManufacture DirectWoodfiredRotaryPredryerDouglasFir",
    "30700630":
        "IndustrialProcesses PulpandPaperandWoodProducts ParticleboardManufacture DirectNaturalGasfiredRotaryDryerSoftwood",
    "30700635":
        "IndustrialProcesses PulpandPaperandWoodProducts ParticleboardManufacture DryRotaryDryerIndirectheated600FInletair30%MCSoftwood",
    "30700637":
        "IndustrialProcesses PulpandPaperandWoodProducts ParticleboardManufacture DryRotaryDryerIndirectheated600FInletair30%MCMixedSoftwoodHardwood",
    "30700641":
        "IndustrialProcesses PulpandPaperandWoodProducts ParticleboardManufacture FormerOperationsUreaFormaldehydeResin",
    "30700642":
        "IndustrialProcesses PulpandPaperandWoodProducts ParticleboardManufacture FormerOperationsNonUreaFormaldehydeResin",
    "30700649":
        "IndustrialProcesses PulpandPaperandWoodProducts ParticleboardManufacture BlenderNonUreaFormaldehydeResin",
    "30700651":
        "IndustrialProcesses PulpandPaperandWoodProducts ParticleboardManufacture ReconstitutedWoodProductsPressBatchUreaFormaldehydeResin",
    "30700652":
        "IndustrialProcesses PulpandPaperandWoodProducts ParticleboardManufacture ReconstitutedWoodProductsPressContinuousUreaFormaldehydeResin",
    "30700654":
        "IndustrialProcesses PulpandPaperandWoodProducts ParticleboardManufacture ReconstitutedWoodProductsPressBatchNonUreaFormaldehydeResin",
    "30700655":
        "IndustrialProcesses PulpandPaperandWoodProducts ParticleboardManufacture VeneerPressUreaFormaldehydeResin",
    "30700657":
        "IndustrialProcesses PulpandPaperandWoodProducts ParticleboardManufacture FlakerHardwood",
    "30700660":
        "IndustrialProcesses PulpandPaperandWoodProducts ParticleboardManufacture BoardCoolerNonUreaFormaldehydeResin",
    "30700661":
        "IndustrialProcesses PulpandPaperandWoodProducts ParticleboardManufacture BoardCoolerUreaFormaldehydeResin",
    "30700663":
        "IndustrialProcesses PulpandPaperandWoodProducts ParticleboardManufacture RefinerDryWoodMaterials",
    "30700664":
        "IndustrialProcesses PulpandPaperandWoodProducts ParticleboardManufacture RefinerGreenWoodMaterialSoftwood",
    "30700665":
        "IndustrialProcesses PulpandPaperandWoodProducts ParticleboardManufacture SandingOperations",
    "30700666":
        "IndustrialProcesses PulpandPaperandWoodProducts ParticleboardManufacture RefinerMixedDryandGreenWoodMaterial",
    "30700667":
        "IndustrialProcesses PulpandPaperandWoodProducts ParticleboardManufacture SandingOperationsUreaFormaldehydeResin",
    "30700668":
        "IndustrialProcesses PulpandPaperandWoodProducts ParticleboardManufacture SandingOperationsNonUreaFormaldehydeResin",
    "30700671":
        "IndustrialProcesses PulpandPaperandWoodProducts ParticleboardManufacture DryRotaryDryerDirectWoodfired600FInletair30%MCSoftwood",
    "30700673":
        "IndustrialProcesses PulpandPaperandWoodProducts ParticleboardManufacture DryRotaryDryerDirectNaturalGasfired600FInletair30%MCHardwood",
    "30700676":
        "IndustrialProcesses PulpandPaperandWoodProducts ParticleboardManufacture GreenRotaryDryerDirectWoodfiredHardwood",
    "30700677":
        "IndustrialProcesses PulpandPaperandWoodProducts ParticleboardManufacture GreenRotaryDryerDirectWoodfiredSoftwood",
    "30700678":
        "IndustrialProcesses PulpandPaperandWoodProducts ParticleboardManufacture GreenRotaryDryerDirectWoodfiredMixedSoftwoodHardwood",
    "30700679":
        "IndustrialProcesses PulpandPaperandWoodProducts ParticleboardManufacture GreenRotaryDryerDirectNaturalGasfiredHardwood",
    "30700680":
        "IndustrialProcesses PulpandPaperandWoodProducts ParticleboardManufacture GreenRotaryDryerDirectNaturalGasfiredSoftwood",
    "30700681":
        "IndustrialProcesses PulpandPaperandWoodProducts ParticleboardManufacture GreenRotaryDryerDirectNaturalGasfiredMixedSoftwoodHardwood",
    "30700690":
        "IndustrialProcesses PulpandPaperandWoodProducts ParticleboardManufacture SawingOperationsPostPressPreBoardCoolerNonUreaFormaldehydeResin",
    "30700691":
        "IndustrialProcesses PulpandPaperandWoodProducts ParticleboardManufacture SawingOperationsPostBoardCoolerUreaFormaldehydeResin",
    "30700692":
        "IndustrialProcesses PulpandPaperandWoodProducts ParticleboardManufacture SawingOperationsPostBoardCoolerNonUreaFormaldehydeResin",
    "30700695":
        "IndustrialProcesses PulpandPaperandWoodProducts ParticleboardManufacture CombinedProcessUnitTypeDustCollectionDryWoodMaterial",
    "30700697":
        "IndustrialProcesses PulpandPaperandWoodProducts ParticleboardManufacture ResinStorageTanks",
    "30700699":
        "IndustrialProcesses PulpandPaperandWoodProducts ParticleboardManufacture OtherNotClassified",
    "30700701":
        "IndustrialProcesses PulpandPaperandWoodProducts PlywoodOperations GeneralNotClassified",
    "30700702":
        "IndustrialProcesses PulpandPaperandWoodProducts PlywoodOperations SandingOperations",
    "30700703":
        "IndustrialProcesses PulpandPaperandWoodProducts PlywoodOperations ParticleboardDryingSee307006ForMoreDetailedParticleboardSCC",
    "30700704":
        "IndustrialProcesses PulpandPaperandWoodProducts PlywoodOperations WaferboardDryerSee307010ForMoreDetailedOSBSCCs",
    "30700705":
        "IndustrialProcesses PulpandPaperandWoodProducts PlywoodOperations HardboardCoreDryer",
    "30700706":
        "IndustrialProcesses PulpandPaperandWoodProducts PlywoodOperations HardboardPredryer",
    "30700707":
        "IndustrialProcesses PulpandPaperandWoodProducts PlywoodOperations HardboardPressing",
    "30700708":
        "IndustrialProcesses PulpandPaperandWoodProducts PlywoodOperations HardboardTempering",
    "30700709":
        "IndustrialProcesses PulpandPaperandWoodProducts PlywoodOperations HardboardBakeOven",
    "30700710":
        "IndustrialProcesses PulpandPaperandWoodProducts PlywoodOperations SawingOperationsDryVeneerandPlywoodTrimming",
    "30700711":
        "IndustrialProcesses PulpandPaperandWoodProducts PlywoodOperations FirSapwoodSteamfiredDryer",
    "30700712":
        "IndustrialProcesses PulpandPaperandWoodProducts PlywoodOperations FirSapwoodGasfiredDryer",
    "30700713":
        "IndustrialProcesses PulpandPaperandWoodProducts PlywoodOperations FirHeartwoodPlywoodVeneerDryer",
    "30700714":
        "IndustrialProcesses PulpandPaperandWoodProducts PlywoodOperations LarchPlywoodVeneerDryer",
    "30700715":
        "IndustrialProcesses PulpandPaperandWoodProducts PlywoodOperations SouthernPinePlywoodVeneerDryer",
    "30700716":
        "IndustrialProcesses PulpandPaperandWoodProducts PlywoodOperations PoplarWoodFiredVeneerDryer",
    "30700717":
        "IndustrialProcesses PulpandPaperandWoodProducts PlywoodOperations GasVeneerDryerPinesuse30700750",
    "30700718":
        "IndustrialProcesses PulpandPaperandWoodProducts PlywoodOperations SteamVeneerDryerPinesuse30700760",
    "30700720":
        "IndustrialProcesses PulpandPaperandWoodProducts PlywoodOperations VeneerRedryerSteamheated",
    "30700724":
        "IndustrialProcesses PulpandPaperandWoodProducts PlywoodOperations SawingOperationsGreenVeneerTrimmingSoftwood",
    "30700725":
        "IndustrialProcesses PulpandPaperandWoodProducts PlywoodOperations VeneerCutting",
    "30700727":
        "IndustrialProcesses PulpandPaperandWoodProducts PlywoodOperations VeneerLayingandGlueSpreading",
    "30700730":
        "IndustrialProcesses PulpandPaperandWoodProducts PlywoodOperations WoodSteaming",
    "30700731":
        "IndustrialProcesses PulpandPaperandWoodProducts PlywoodOperations LogSteamingVat",
    "30700732":
        "IndustrialProcesses PulpandPaperandWoodProducts PlywoodOperations ResinStorageTanks",
    "30700734":
        "IndustrialProcesses PulpandPaperandWoodProducts PlywoodOperations HardwoodVeneerDryerDirectWoodfiredHeatedZones",
    "30700736":
        "IndustrialProcesses PulpandPaperandWoodProducts PlywoodOperations SoftwoodVeneerDryerDirectWoodfiredHeatedZones",
    "30700737":
        "IndustrialProcesses PulpandPaperandWoodProducts PlywoodOperations SoftwoodVeneerDryerDirectWoodfiredCoolingSection",
    "30700740":
        "IndustrialProcesses PulpandPaperandWoodProducts PlywoodOperations DirectWoodFiredDryerNonspecifiedPineSpeciesVeneer",
    "30700746":
        "IndustrialProcesses PulpandPaperandWoodProducts PlywoodOperations DirectWoodFiredDryerNonspecifiedFirSpeciesVeneer",
    "30700747":
        "IndustrialProcesses PulpandPaperandWoodProducts PlywoodOperations DirectWoodFiredDryerDouglasFirVeneer",
    "30700750":
        "IndustrialProcesses PulpandPaperandWoodProducts PlywoodOperations DirectNaturalGasFiredDryerNonspecifiedPineSpeciesVeneer",
    "30700752":
        "IndustrialProcesses PulpandPaperandWoodProducts PlywoodOperations SoftwoodVeneerDryerDirectNaturalGasfiredHeatedZones",
    "30700753":
        "IndustrialProcesses PulpandPaperandWoodProducts PlywoodOperations SoftwoodVeneerDryerDirectNaturalGasfiredCoolingSection",
    "30700756":
        "IndustrialProcesses PulpandPaperandWoodProducts PlywoodOperations HardwoodVeneerDryerIndirectheatedHeatedZones",
    "30700757":
        "IndustrialProcesses PulpandPaperandWoodProducts PlywoodOperations HardwoodVeneerDryerIndirectheatedCoolingSection",
    "30700760":
        "IndustrialProcesses PulpandPaperandWoodProducts PlywoodOperations IndirectHeatedDryerNonspecifiedPineSpeciesVeneer",
    "30700762":
        "IndustrialProcesses PulpandPaperandWoodProducts PlywoodOperations SoftwoodVeneerDryerIndirectheatedHeatedZones",
    "30700763":
        "IndustrialProcesses PulpandPaperandWoodProducts PlywoodOperations SoftwoodVeneerDryerIndirectheatedCoolingSection",
    "30700766":
        "IndustrialProcesses PulpandPaperandWoodProducts PlywoodOperations IndirectHeatedDryerNonspecifiedFirSpeciesVeneer",
    "30700767":
        "IndustrialProcesses PulpandPaperandWoodProducts PlywoodOperations IndirectHeatedDryerDouglasFirVeneer",
    "30700769":
        "IndustrialProcesses PulpandPaperandWoodProducts PlywoodOperations IndirectHeatedDryerPoplarVeneer",
    "30700773":
        "IndustrialProcesses PulpandPaperandWoodProducts PlywoodOperations BoardCooler",
    "30700777":
        "IndustrialProcesses PulpandPaperandWoodProducts PlywoodOperations CombinedProcessUnitTypeDustCollectionDryWoodMaterial",
    "30700778":
        "IndustrialProcesses PulpandPaperandWoodProducts PlywoodOperations CombinedProcessUnitTypeDustCollectionMixedDryandGreenWoodMaterial",
    "30700780":
        "IndustrialProcesses PulpandPaperandWoodProducts PlywoodOperations PlywoodPressPhenolformaldehydeResin",
    "30700781":
        "IndustrialProcesses PulpandPaperandWoodProducts PlywoodOperations PlywoodPressUreaformaldehydeResin",
    "30700783":
        "IndustrialProcesses PulpandPaperandWoodProducts PlywoodOperations PressPhenolFormaldehydeResinSoftwood",
    "30700784":
        "IndustrialProcesses PulpandPaperandWoodProducts PlywoodOperations PressNonUreaFormaldehydeResinHardwood",
    "30700785":
        "IndustrialProcesses PulpandPaperandWoodProducts PlywoodOperations PressUreaFormaldehydeResinHardwood",
    "30700788":
        "IndustrialProcesses PulpandPaperandWoodProducts PlywoodOperations HardwdPlywdCombdDustBHTrim&CoreSawsComposrDryHogHammermillSandr",
    "30700789":
        "IndustrialProcesses PulpandPaperandWoodProducts PlywoodOperations SoftwoodPlywoodLogSteamingVat",
    "30700790":
        "IndustrialProcesses PulpandPaperandWoodProducts PlywoodOperations HammermillChipperGreenWoodMaterialSoftwood",
    "30700791":
        "IndustrialProcesses PulpandPaperandWoodProducts PlywoodOperations HammermillChipperDryWoodMaterial",
    "30700792":
        "IndustrialProcesses PulpandPaperandWoodProducts PlywoodOperations SoftwoodPlywoodSandersandSpecialtySaw",
    "30700793":
        "IndustrialProcesses PulpandPaperandWoodProducts PlywoodOperations SoftwoodPlywoodSawsHogandSander",
    "30700794":
        "IndustrialProcesses PulpandPaperandWoodProducts PlywoodOperations MiscellaneousCoatingOperations",
    "30700799":
        "IndustrialProcesses PulpandPaperandWoodProducts PlywoodOperations OtherNotClassified",
    "30700801":
        "IndustrialProcesses PulpandPaperandWoodProducts SawmillOperations LogDebarking",
    "30700802":
        "IndustrialProcesses PulpandPaperandWoodProducts SawmillOperations LogSawing",
    "30700803":
        "IndustrialProcesses PulpandPaperandWoodProducts SawmillOperations SawdustPileHandling",
    "30700804":
        "IndustrialProcesses PulpandPaperandWoodProducts SawmillOperations SawingCycloneExhaust",
    "30700805":
        "IndustrialProcesses PulpandPaperandWoodProducts SawmillOperations PlaningTrimmingCycloneExhaust",
    "30700806":
        "IndustrialProcesses PulpandPaperandWoodProducts SawmillOperations SandingOperationsCycloneExhaust",
    "30700807":
        "IndustrialProcesses PulpandPaperandWoodProducts SawmillOperations SanderdustCycloneExhaust",
    "30700808":
        "IndustrialProcesses PulpandPaperandWoodProducts SawmillOperations OtherOperationsCycloneExhaust",
    "30700809":
        "IndustrialProcesses PulpandPaperandWoodProducts SawmillOperations OtherOperationsCycloneExhaustGreenWoodMaterialSoftwood",
    "30700811":
        "IndustrialProcesses PulpandPaperandWoodProducts SawmillOperations OtherOperationsCycloneExhaustDryWoodMaterial",
    "30700818":
        "IndustrialProcesses PulpandPaperandWoodProducts SawmillOperations ChippingandScreeningSoftwood",
    "30700820":
        "IndustrialProcesses PulpandPaperandWoodProducts SawmillOperations ChippingandScreening",
    "30700821":
        "IndustrialProcesses PulpandPaperandWoodProducts SawmillOperations ChipStoragePiles",
    "30700822":
        "IndustrialProcesses PulpandPaperandWoodProducts SawmillOperations ChipTransferConveying",
    "30700825":
        "IndustrialProcesses PulpandPaperandWoodProducts SawmillOperations ChipTransferConveyingSoftwood",
    "30700827":
        "IndustrialProcesses PulpandPaperandWoodProducts SawmillOperations ChipStoragePilesSoftwood",
    "30700828":
        "IndustrialProcesses PulpandPaperandWoodProducts SawmillOperations ChipStoragePilesHardwood",
    "30700830":
        "IndustrialProcesses PulpandPaperandWoodProducts SawmillOperations LumberKilnSoftwoodPineSpecies",
    "30700831":
        "IndustrialProcesses PulpandPaperandWoodProducts SawmillOperations LumberKilnSoftwoodWesternNonPineSoftwood",
    "30700832":
        "IndustrialProcesses PulpandPaperandWoodProducts SawmillOperations LumberKilnSoftwoodEasternNonPineSoftwood",
    "30700833":
        "IndustrialProcesses PulpandPaperandWoodProducts SawmillOperations LumberKilnHardwood",
    "30700839":
        "IndustrialProcesses PulpandPaperandWoodProducts SawmillOperations LumberKilnSoftwoodWesternPineSoftwood",
    "30700841":
        "IndustrialProcesses PulpandPaperandWoodProducts SawmillOperations LumberKilnIndirectheatedSoftwoodPineSpecies",
    "30700842":
        "IndustrialProcesses PulpandPaperandWoodProducts SawmillOperations LumberKilnIndirectheatedSoftwoodNonPineSpecies",
    "30700843":
        "IndustrialProcesses PulpandPaperandWoodProducts SawmillOperations LumberKilnIndirectheatedHardwood",
    "30700844":
        "IndustrialProcesses PulpandPaperandWoodProducts SawmillOperations LumberKilnDirectfiredSoftwoodPineSpecies",
    "30700845":
        "IndustrialProcesses PulpandPaperandWoodProducts SawmillOperations LumberKilnDirectfiredSoftwoodNonPineSpecies",
    "30700895":
        "IndustrialProcesses PulpandPaperandWoodProducts SawmillOperations LogStorage",
    "30700896":
        "IndustrialProcesses PulpandPaperandWoodProducts SawmillOperations OtherNotClassified",
    "30700897":
        "IndustrialProcesses PulpandPaperandWoodProducts SawmillOperations SoftwoodSawmillOperationsOtherNotClassified",
    "30700898":
        "IndustrialProcesses PulpandPaperandWoodProducts SawmillOperations HardwoodSawmillOperationsOtherNotClassified",
    "30700899":
        "IndustrialProcesses PulpandPaperandWoodProducts SawmillOperations OtherNotClassified",
    "30700909":
        "IndustrialProcesses PulpandPaperandWoodProducts MediumDensityFiberboardMDFManufacture PressurizedRefinerPrimaryTubeDryerDirectNaturalGasfiredBlowlineBlendNonUreaFormaldehydeResinSoftwood",
    "30700913":
        "IndustrialProcesses PulpandPaperandWoodProducts MediumDensityFiberboardMDFManufacture PressurizedRefinerPrimaryTubeDryerDirectNaturalGasfiredBlowlineBlendUreaFormaldehydeResinSoftwood",
    "30700915":
        "IndustrialProcesses PulpandPaperandWoodProducts MediumDensityFiberboardMDFManufacture PressurizedRefinerPrimaryTubeDryerDirectWoodfiredNonBlowlineBlendSoftwood",
    "30700918":
        "IndustrialProcesses PulpandPaperandWoodProducts MediumDensityFiberboardMDFManufacture PressurizedRefinerPrimaryTubeDryerDirectWoodfiredBlowlineBlendNonUreaFormaldehydeResinHardwood",
    "30700919":
        "IndustrialProcesses PulpandPaperandWoodProducts MediumDensityFiberboardMDFManufacture PressurizedRefinerPrimaryTubeDryerDirectWoodfiredBlowlineBlendNonUreaFormaldehydeResinMixedSoftwoodHardwood",
    "30700921":
        "IndustrialProcesses PulpandPaperandWoodProducts MediumDensityFiberboardMDFManufacture DirectWoodfiredTubeDryerUnspecifiedPines",
    "30700923":
        "IndustrialProcesses PulpandPaperandWoodProducts MediumDensityFiberboardMDFManufacture PressurizedRefinerPrimaryTubeDryerDirectWoodfiredBlowlineBlendUreaFormaldehydeResinSoftwood",
    "30700924":
        "IndustrialProcesses PulpandPaperandWoodProducts MediumDensityFiberboardMDFManufacture PressurizedRefinerPrimaryTubeDryerDirectWoodfiredBlowlineBlendUreaFormaldehydeResinMixedSoftwoodHardwood",
    "30700925":
        "IndustrialProcesses PulpandPaperandWoodProducts MediumDensityFiberboardMDFManufacture PressurizedRefinerPrimaryTubeDryerDirectWoodfiredBlowlineBlendUreaFormaldehydeResinHardwood",
    "30700927":
        "IndustrialProcesses PulpandPaperandWoodProducts MediumDensityFiberboardMDFManufacture PressurizedRefinerPrimaryTubeDryerDirectNaturalGasfiredNonBlowlineBlendHardwood",
    "30700931":
        "IndustrialProcesses PulpandPaperandWoodProducts MediumDensityFiberboardMDFManufacture IndirectheatedTubeDryerUnspecifiedPines",
    "30700932":
        "IndustrialProcesses PulpandPaperandWoodProducts MediumDensityFiberboardMDFManufacture PressurizedRefinerPrimaryTubeDryerIndirectheatedBlowlineBlendUreaFormaldehydeResinSoftwood",
    "30700935":
        "IndustrialProcesses PulpandPaperandWoodProducts MediumDensityFiberboardMDFManufacture IndirectheatedTubeDryerHardwoods",
    "30700936":
        "IndustrialProcesses PulpandPaperandWoodProducts MediumDensityFiberboardMDFManufacture PressurizedRefinerPrimaryTubeDryerIndirectheatedBlowlineBlendUreaFormaldehydeResinHardwood",
    "30700939":
        "IndustrialProcesses PulpandPaperandWoodProducts MediumDensityFiberboardMDFManufacture PressurizedRefinerPrimaryTubeDryerIndirectheatedBlowlineBlendUreaFormaldehydeResinMixedSoftwoodHardwood",
    "30700942":
        "IndustrialProcesses PulpandPaperandWoodProducts MediumDensityFiberboardMDFManufacture SecondaryTubeDryerAllIndirectfiredUnits",
    "30700943":
        "IndustrialProcesses PulpandPaperandWoodProducts MediumDensityFiberboardMDFManufacture SecondaryTubeDryerAllDirectfiredUnits",
    "30700946":
        "IndustrialProcesses PulpandPaperandWoodProducts MediumDensityFiberboardMDFManufacture FiberDryersOther",
    "30700950":
        "IndustrialProcesses PulpandPaperandWoodProducts MediumDensityFiberboardMDFManufacture ReconstitutedWoodProductsPressContinuousUreaFormaldehydeResin",
    "30700960":
        "IndustrialProcesses PulpandPaperandWoodProducts MediumDensityFiberboardMDFManufacture ReconstitutedWoodProductsPressBatchUreaFormaldehydeResin",
    "30700961":
        "IndustrialProcesses PulpandPaperandWoodProducts MediumDensityFiberboardMDFManufacture ReconstitutedWoodProductsPressBatchNonUreaFormaldehydeResin",
    "30700971":
        "IndustrialProcesses PulpandPaperandWoodProducts MediumDensityFiberboardMDFManufacture BoardCoolerUreaFormaldehydeResin",
    "30700980":
        "IndustrialProcesses PulpandPaperandWoodProducts MediumDensityFiberboardMDFManufacture BlenderUreaFormaldehydeResin",
    "30700981":
        "IndustrialProcesses PulpandPaperandWoodProducts MediumDensityFiberboardMDFManufacture FormerWithoutBlowlineBlendUreaFormaldehydeResin",
    "30700982":
        "IndustrialProcesses PulpandPaperandWoodProducts MediumDensityFiberboardMDFManufacture FormerWithBlowlineBlendUreaFormaldehydeResin",
    "30700983":
        "IndustrialProcesses PulpandPaperandWoodProducts MediumDensityFiberboardMDFManufacture SandingOperationsUreaFormaldehydeResin",
    "30700984":
        "IndustrialProcesses PulpandPaperandWoodProducts MediumDensityFiberboardMDFManufacture SawingOperationsPrePressUreaFormaldehydeResin",
    "30700987":
        "IndustrialProcesses PulpandPaperandWoodProducts MediumDensityFiberboardMDFManufacture SawingOperationsPostBoardCoolerUreaFormaldehydeResin",
    "30700991":
        "IndustrialProcesses PulpandPaperandWoodProducts MediumDensityFiberboardMDFManufacture PanelTrimHammermillChipper",
    "30700995":
        "IndustrialProcesses PulpandPaperandWoodProducts MediumDensityFiberboardMDFManufacture CombinedProcessUnitTypeDustCollectionMixedDryandGreenWoodMaterial",
    "30700996":
        "IndustrialProcesses PulpandPaperandWoodProducts MediumDensityFiberboardMDFManufacture ResinStorageTanks",
    "30700997":
        "IndustrialProcesses PulpandPaperandWoodProducts MediumDensityFiberboardMDFManufacture MiscellaneousCoatingOperations",
    "30700999":
        "IndustrialProcesses PulpandPaperandWoodProducts MediumDensityFiberboardMDFManufacture OtherNotClassified",
    "30701001":
        "IndustrialProcesses PulpandPaperandWoodProducts OrientedStrandboardOSBManufacture DirectWoodfiredRotaryDryerUnspecifiedPines",
    "30701008":
        "IndustrialProcesses PulpandPaperandWoodProducts OrientedStrandboardOSBManufacture DirectWoodfiredRotaryDryerAspen",
    "30701009":
        "IndustrialProcesses PulpandPaperandWoodProducts OrientedStrandboardOSBManufacture RotaryStrandDryerDirectWoodfiredSoftwood",
    "30701010":
        "IndustrialProcesses PulpandPaperandWoodProducts OrientedStrandboardOSBManufacture RotaryStrandDryerDirectWoodfiredHardwood",
    "30701015":
        "IndustrialProcesses PulpandPaperandWoodProducts OrientedStrandboardOSBManufacture RotaryStrandDryerDirectWoodfiredMixedSoftwoodHardwood",
    "30701020":
        "IndustrialProcesses PulpandPaperandWoodProducts OrientedStrandboardOSBManufacture RotaryStrandDryerDirectNaturalGasfiredHardwood",
    "30701030":
        "IndustrialProcesses PulpandPaperandWoodProducts OrientedStrandboardOSBManufacture RotaryStrandDryerIndirectheatedHardwood",
    "30701031":
        "IndustrialProcesses PulpandPaperandWoodProducts OrientedStrandboardOSBManufacture RotaryStrandDryerIndirectheatedSoftwood",
    "30701032":
        "IndustrialProcesses PulpandPaperandWoodProducts OrientedStrandboardOSBManufacture RotaryStrandDryerIndirectheatedMixedSoftwoodHardwood",
    "30701039":
        "IndustrialProcesses PulpandPaperandWoodProducts OrientedStrandboardOSBManufacture IndirectheatedConveyorDryerSoftwoods",
    "30701042":
        "IndustrialProcesses PulpandPaperandWoodProducts OrientedStrandboardOSBManufacture ConveyorDryerHeatedZonesMixedHardwoodSoftwood",
    "30701053":
        "IndustrialProcesses PulpandPaperandWoodProducts OrientedStrandboardOSBManufacture ReconstitutedWoodProductsPressPhenolFormaldehydeResin",
    "30701055":
        "IndustrialProcesses PulpandPaperandWoodProducts OrientedStrandboardOSBManufacture ReconstitutedWoodProductsPressMethyleneDiphenylDiisocyanateMDIResin",
    "30701057":
        "IndustrialProcesses PulpandPaperandWoodProducts OrientedStrandboardOSBManufacture ReconstitutedWoodProductsPressPhenolFormaldehydeResinsurfacelayersMethyleneDiphenylDiisocyanateMDIResincorelayers",
    "30701058":
        "IndustrialProcesses PulpandPaperandWoodProducts OrientedStrandboardOSBManufacture ReconstitutedWoodProductsPress",
    "30701060":
        "IndustrialProcesses PulpandPaperandWoodProducts OrientedStrandboardOSBManufacture BlenderPFResinMDIResin",
    "30701062":
        "IndustrialProcesses PulpandPaperandWoodProducts OrientedStrandboardOSBManufacture SandingOperations",
    "30701064":
        "IndustrialProcesses PulpandPaperandWoodProducts OrientedStrandboardOSBManufacture StorageBinsTrimmingandDryerExhaustCycloneDust",
    "30701070":
        "IndustrialProcesses PulpandPaperandWoodProducts OrientedStrandboardOSBManufacture BlenderPhenolFormaldehydeResin",
    "30701071":
        "IndustrialProcesses PulpandPaperandWoodProducts OrientedStrandboardOSBManufacture BlenderMethyleneDiphenylDiisocyanateMDIResin",
    "30701072":
        "IndustrialProcesses PulpandPaperandWoodProducts OrientedStrandboardOSBManufacture FormerPhenolFormaldehydeResin",
    "30701073":
        "IndustrialProcesses PulpandPaperandWoodProducts OrientedStrandboardOSBManufacture FormerOperationsMethyleneDiphenylDiisocyanateMDIResin",
    "30701074":
        "IndustrialProcesses PulpandPaperandWoodProducts OrientedStrandboardOSBManufacture FormerOperationsPhenolFormaldehydeResinMethyleneDiphenylDiisocyanateMDIResin",
    "30701081":
        "IndustrialProcesses PulpandPaperandWoodProducts OrientedStrandboardOSBManufacture WaferizerStrander",
    "30701084":
        "IndustrialProcesses PulpandPaperandWoodProducts OrientedStrandboardOSBManufacture HammermillChipperDryWoodMaterial",
    "30701086":
        "IndustrialProcesses PulpandPaperandWoodProducts OrientedStrandboardOSBManufacture MiscellaneousCoatingOperations",
    "30701087":
        "IndustrialProcesses PulpandPaperandWoodProducts OrientedStrandboardOSBManufacture ResinStorageTanks",
    "30701090":
        "IndustrialProcesses PulpandPaperandWoodProducts OrientedStrandboardOSBManufacture SawingOperationsPrePressMatTrimmingPhenolFormaldehydeResin",
    "30701093":
        "IndustrialProcesses PulpandPaperandWoodProducts OrientedStrandboardOSBManufacture SawingOperationsPostPressPanelTrimmingPhenolFormaldehydeResin",
    "30701094":
        "IndustrialProcesses PulpandPaperandWoodProducts OrientedStrandboardOSBManufacture SawingOperationsPostPressPanelTrimmingMethyleneDiphenylDiisocyanateMDIResin",
    "30701095":
        "IndustrialProcesses PulpandPaperandWoodProducts OrientedStrandboardOSBManufacture SawingOperationsPostPressPanelTrimmingPhenolFormaldehydeResinMethyleneDiphenylDiisocyanateMDIResin",
    "30701099":
        "IndustrialProcesses PulpandPaperandWoodProducts OrientedStrandboardOSBManufacture OtherNotClassified",
    "30701199":
        "IndustrialProcesses PulpandPaperandWoodProducts PaperCoatingandGlazing ExtrusionCoatingLinewithSolventFreeResinWax",
    "30701201":
        "IndustrialProcesses PulpandPaperandWoodProducts MiscellaneousPaperProcesses Cyclones",
    "30701202":
        "IndustrialProcesses PulpandPaperandWoodProducts MiscellaneousPaperProcesses WastewaterGeneral",
    "30701220":
        "IndustrialProcesses PulpandPaperandWoodProducts MechanicalPulpingOperations ThermomechanicalProcessandChemithermomechanicalPulping",
    "30701221":
        "IndustrialProcesses PulpandPaperandWoodProducts MechanicalPulpingOperations PressurizedGroundwoodStoneGroundwoodProcess",
    "30701223":
        "IndustrialProcesses PulpandPaperandWoodProducts MechanicalPulpingOperations WastewaterGeneral",
    "30701301":
        "IndustrialProcesses PulpandPaperandWoodProducts MiscellaneousPaperProcesses ShreddingNewspaperforInsulationManufacturing",
    "30701399":
        "IndustrialProcesses PulpandPaperandWoodProducts MiscellaneousPaperProcesses OtherNotClassified",
    "30701410":
        "IndustrialProcesses PulpandPaperandWoodProducts HardboardHBManufacture PressurizedRefinerPrimaryTubeDryerDirectWoodfiredBlowlineBlendPhenolFormaldehydeResinHardwood",
    "30701413":
        "IndustrialProcesses PulpandPaperandWoodProducts HardboardHBManufacture PressurizedRefinerPrimaryTubeDryerNaturalGasfiredBlowlineBlendPhenolFormaldehydeResinSoftwood",
    "30701420":
        "IndustrialProcesses PulpandPaperandWoodProducts HardboardHBManufacture Temperingovendirectnaturalgasfiredhardwood",
    "30701421":
        "IndustrialProcesses PulpandPaperandWoodProducts HardboardHBManufacture HardboardOven",
    "30701424":
        "IndustrialProcesses PulpandPaperandWoodProducts HardboardHBManufacture SecondaryTubeDryerAllIndirectfiredUnits",
    "30701425":
        "IndustrialProcesses PulpandPaperandWoodProducts HardboardHBManufacture Tubedryersecondstageindirectheatedhardwood",
    "30701426":
        "IndustrialProcesses PulpandPaperandWoodProducts HardboardHBManufacture FiberDryersOther",
    "30701427":
        "IndustrialProcesses PulpandPaperandWoodProducts HardboardHBManufacture PressPreDryerPhenolFormaldehydeResin",
    "30701430":
        "IndustrialProcesses PulpandPaperandWoodProducts HardboardHBManufacture Humidificationkilnindirectheated",
    "30701431":
        "IndustrialProcesses PulpandPaperandWoodProducts HardboardHBManufacture Humidifier",
    "30701440":
        "IndustrialProcesses PulpandPaperandWoodProducts HardboardHBManufacture HotpressPFresin",
    "30701441":
        "IndustrialProcesses PulpandPaperandWoodProducts HardboardHBManufacture DryHardboardPressPhenolFormaldehydeResin",
    "30701443":
        "IndustrialProcesses PulpandPaperandWoodProducts HardboardHBManufacture DryHardboardPressNonPhenolFormaldehydeResin",
    "30701444":
        "IndustrialProcesses PulpandPaperandWoodProducts HardboardHBManufacture WetHardboardPressPhenolFormaldehydeResin",
    "30701456":
        "IndustrialProcesses PulpandPaperandWoodProducts HardboardHBManufacture DigesterHardwood",
    "30701466":
        "IndustrialProcesses PulpandPaperandWoodProducts HardboardHBManufacture PressurizedDigesterRefinerSoftwood",
    "30701467":
        "IndustrialProcesses PulpandPaperandWoodProducts HardboardHBManufacture PressurizedDigesterRefinerHardwood",
    "30701468":
        "IndustrialProcesses PulpandPaperandWoodProducts HardboardHBManufacture PressurizedDigesterRefinerMixedSoftwoodHardwood",
    "30701480":
        "IndustrialProcesses PulpandPaperandWoodProducts HardboardHBManufacture SandingOperations",
    "30701482":
        "IndustrialProcesses PulpandPaperandWoodProducts HardboardHBManufacture Logchipperhardwood",
    "30701484":
        "IndustrialProcesses PulpandPaperandWoodProducts HardboardHBManufacture Pressurizeddigesterrefinerhardwood",
    "30701485":
        "IndustrialProcesses PulpandPaperandWoodProducts HardboardHBManufacture WetHardboardFormerVacuumSystemNonPhenolFormaldehydeResin",
    "30701486":
        "IndustrialProcesses PulpandPaperandWoodProducts HardboardHBManufacture WetHardboardFormerVacuumSystemPhenolFormaldehydeResin",
    "30701494":
        "IndustrialProcesses PulpandPaperandWoodProducts HardboardHBManufacture CombinedProcessUnitTypeDustCollectionMixedDryandGreenWoodMaterial",
    "30701496":
        "IndustrialProcesses PulpandPaperandWoodProducts HardboardHBManufacture MiscellaneousCoatingOperations",
    "30701499":
        "IndustrialProcesses PulpandPaperandWoodProducts HardboardHBManufacture OtherNotClassified",
    "30701510":
        "IndustrialProcesses PulpandPaperandWoodProducts FiberboardFBManufacture Boarddryerindirectheatedsoftwoodstarchbinderheatedzones",
    "30701540":
        "IndustrialProcesses PulpandPaperandWoodProducts FiberboardFBManufacture FiberWasherSoftwood",
    "30701601":
        "IndustrialProcesses PulpandPaperandWoodProducts EngineeredWoodProducts LaminatedVeneerLumberLVLManufactureHardwoodVeneerDryerIndirectheatedHeatedZones",
    "30701602":
        "IndustrialProcesses PulpandPaperandWoodProducts EngineeredWoodProducts LaminatedVeneerLumberLVLManufactureHardwoodVeneerDryerIndirectheatedCoolingSection",
    "30701612":
        "IndustrialProcesses PulpandPaperandWoodProducts EngineeredWoodProducts LaminatedVeneerLumberLVLManufacturePressPhenolFormaldehydeResin",
    "30701614":
        "IndustrialProcesses PulpandPaperandWoodProducts EngineeredWoodProducts LaminatedVeneerLumberLVLManufacturePressNonPhenolFormaldehydeResin",
    "30701620":
        "IndustrialProcesses PulpandPaperandWoodProducts LaminatedVeneerLumberManufacture LVLIBeamSaw",
    "30701623":
        "IndustrialProcesses PulpandPaperandWoodProducts EngineeredWoodProducts LaminatedVeneerLumberLVLManufactureHammermillChipperDryWoodMaterial",
    "30701627":
        "IndustrialProcesses PulpandPaperandWoodProducts EngineeredWoodProducts LaminatedVeneerLumberLVLManufactureSawingOperationsDryVeneerandLaminatedVeneerLumberLVLTrimming",
    "30701628":
        "IndustrialProcesses PulpandPaperandWoodProducts EngineeredWoodProducts LaminatedVeneerLumberLVLManufactureLogSteamingVat",
    "30701629":
        "IndustrialProcesses PulpandPaperandWoodProducts EngineeredWoodProducts LaminatedVeneerLumberLVLManufactureResinStorageTanks",
    "30701630":
        "IndustrialProcesses PulpandPaperandWoodProducts LaminatedVeneerLumberManufacture IJoistmanufactureIJoistcuringchamber",
    "30701631":
        "IndustrialProcesses PulpandPaperandWoodProducts EngineeredWoodProducts LaminatedVeneerLumberLVLManufactureCombinedProcessUnitTypeDustCollectionGreenWoodMaterialSoftwood",
    "30701635":
        "IndustrialProcesses PulpandPaperandWoodProducts EngineeredWoodProducts LaminatedVeneerLumberLVLManufactureMiscellaneousCoatingOperations",
    "30701639":
        "IndustrialProcesses PulpandPaperandWoodProducts EngineeredWoodProducts LaminatedVeneerLumberLVLManufactureOtherNotClassified",
    "30701641":
        "IndustrialProcesses PulpandPaperandWoodProducts LaminatedStrandLumberManufacture LSLconveyorindirectheatedhardwood",
    "30701650":
        "IndustrialProcesses PulpandPaperandWoodProducts LaminatedStrandLumberManufacture LSLpressMDIresin",
    "30701660":
        "IndustrialProcesses PulpandPaperandWoodProducts LaminatedStrandLumberManufacture LSLSander",
    "30701661":
        "IndustrialProcesses PulpandPaperandWoodProducts LaminatedStrandLumberManufacture LSLSaw",
    "30701670":
        "IndustrialProcesses PulpandPaperandWoodProducts EngineeredWoodProducts IJoistManufactureCuringChamber",
    "30701671":
        "IndustrialProcesses PulpandPaperandWoodProducts EngineeredWoodProducts IJoistManufactureResinStorageTanks",
    "30701672":
        "IndustrialProcesses PulpandPaperandWoodProducts EngineeredWoodProducts IJoistManufactureSawingOperations",
    "30701679":
        "IndustrialProcesses PulpandPaperandWoodProducts EngineeredWoodProducts IJoistManufactureOtherNotClassified",
    "30701680":
        "IndustrialProcesses PulpandPaperandWoodProducts EngineeredWoodProducts GlulamManufacturePressCuringChamberPhenolResorcinolFormaldehydePRFresin",
    "30701681":
        "IndustrialProcesses PulpandPaperandWoodProducts EngineeredWoodProducts GlulamManufacturePressCuringChamberNonPhenolResorcinolFormaldehydePRFResin",
    "30701701":
        "IndustrialProcesses PulpandPaperandWoodProducts EngineeredWoodProducts LaminatedStrandLumberLSLManufactureRotaryStrandDryerDirectWoodfiredHardwood",
    "30701708":
        "IndustrialProcesses PulpandPaperandWoodProducts EngineeredWoodProducts LaminatedStrandLumberLSLManufactureRotaryStrandDryerIndirectheatedHardwood",
    "30701720":
        "IndustrialProcesses PulpandPaperandWoodProducts EngineeredWoodProducts LaminatedStrandLumberLSLManufacturePressMethyleneDiphenylDiisocyanateMDIAdhesive",
    "30701722":
        "IndustrialProcesses PulpandPaperandWoodProducts EngineeredWoodProducts LaminatedStrandLumberLSLManufactureBlenderMethyleneDiphenylDiisocyanateMDIAdhesive",
    "30701730":
        "IndustrialProcesses PulpandPaperandWoodProducts EngineeredWoodProducts LaminatedStrandLumberLSLManufactureSandingOperations",
    "30701731":
        "IndustrialProcesses PulpandPaperandWoodProducts EngineeredWoodProducts LaminatedStrandLumberLSLManufactureSawingOperations",
    "30701737":
        "IndustrialProcesses PulpandPaperandWoodProducts EngineeredWoodProducts LaminatedStrandLumberLSLManufactureResinStorageTanks",
    "30701739":
        "IndustrialProcesses PulpandPaperandWoodProducts EngineeredWoodProducts LaminatedStrandLumberLSLManufactureOtherNotClassified",
    "30701760":
        "IndustrialProcesses PulpandPaperandWoodProducts EngineeredWoodProducts ParallelStrandLumberPSLManufacturePressPhenolFormaldehydeResin",
    "30702001":
        "IndustrialProcesses PulpandPaperandWoodProducts FurnitureManufacture Roughend",
    "30702002":
        "IndustrialProcesses PulpandPaperandWoodProducts FurnitureManufacture MachineRoom",
    "30702003":
        "IndustrialProcesses PulpandPaperandWoodProducts FurnitureManufacture Sanding",
    "30702004":
        "IndustrialProcesses PulpandPaperandWoodProducts FurnitureManufacture WoodHog",
    "30702021":
        "IndustrialProcesses PulpandPaperandWoodProducts FurnitureManufacture VeneerHotPressUreaFormaldehydeResin",
    "30702098":
        "IndustrialProcesses PulpandPaperandWoodProducts FurnitureManufacture OtherNotClassified",
    "30702099":
        "IndustrialProcesses PulpandPaperandWoodProducts FurnitureManufacture OtherNotClassified",
    "30703001":
        "IndustrialProcesses PulpandPaperandWoodProducts MiscellaneousWoodWorkingOperations WoodWasteStorageBinVent",
    "30703002":
        "IndustrialProcesses PulpandPaperandWoodProducts MiscellaneousWoodWorkingOperations WoodWasteStorageBinLoadout",
    "30703099":
        "IndustrialProcesses PulpandPaperandWoodProducts MiscellaneousWoodWorkingOperations SandingPlaningOperationsSpecify",
    "30704001":
        "IndustrialProcesses PulpandPaperandWoodProducts BulkHandlingandStorageWoodBark StorageBins",
    "30704002":
        "IndustrialProcesses PulpandPaperandWoodProducts BulkHandlingandStorageWoodBark Stockpiles",
    "30704003":
        "IndustrialProcesses PulpandPaperandWoodProducts BulkHandlingandStorageWoodBark Unloading",
    "30704004":
        "IndustrialProcesses PulpandPaperandWoodProducts BulkHandlingandStorageWoodBark Loading",
    "30704005":
        "IndustrialProcesses PulpandPaperandWoodProducts BulkHandlingandStorageWoodBark Conveyors",
    "30788801":
        "IndustrialProcesses PulpandPaperandWoodProducts FugitiveEmissions SpecifyinCommentsField",
    "30788898":
        "IndustrialProcesses PulpandPaperandWoodProducts FugitiveEmissions SpecifyinCommentsField",
    "30790003":
        "IndustrialProcesses PulpandPaperandWoodProducts FuelFiredEquipment NaturalGasProcessHeaters",
    "30799901":
        "IndustrialProcesses PulpandPaperandWoodProducts OtherNotClassified BatterySeparators",
    "30799998":
        "IndustrialProcesses PulpandPaperandWoodProducts OtherNotClassified OtherNotClassified",
    "30799999":
        "IndustrialProcesses PulpandPaperandWoodProducts OtherNotClassified SeeComment",
    "30800101":
        "IndustrialProcesses RubberandMiscellaneousPlasticsProducts TireManufacture UndertreadandSidewallCementing",
    "30800102":
        "IndustrialProcesses RubberandMiscellaneousPlasticsProducts TireManufacture BeadDipping",
    "30800103":
        "IndustrialProcesses RubberandMiscellaneousPlasticsProducts TireManufacture BeadSwabbing",
    "30800104":
        "IndustrialProcesses RubberandMiscellaneousPlasticsProducts TireManufacture TireBuilding",
    "30800105":
        "IndustrialProcesses RubberandMiscellaneousPlasticsProducts TireManufacture TreadEndCementing",
    "30800106":
        "IndustrialProcesses RubberandMiscellaneousPlasticsProducts TireManufacture GreenTireSpraying",
    "30800107":
        "IndustrialProcesses RubberandMiscellaneousPlasticsProducts TireManufacture TireCuring",
    "30800108":
        "IndustrialProcesses RubberandMiscellaneousPlasticsProducts TireManufacture SolventMixing",
    "30800109":
        "IndustrialProcesses RubberandMiscellaneousPlasticsProducts TireManufacture SolventStorageUse40700401thru40799998ifpossible",
    "30800110":
        "IndustrialProcesses RubberandMiscellaneousPlasticsProducts TireManufacture SolventStorageUse40700401thru40799998ifpossible",
    "30800111":
        "IndustrialProcesses RubberandMiscellaneousPlasticsProducts TireManufacture Compounding",
    "30800112":
        "IndustrialProcesses RubberandMiscellaneousPlasticsProducts TireManufacture Milling",
    "30800113":
        "IndustrialProcesses RubberandMiscellaneousPlasticsProducts TireManufacture TreadExtruder",
    "30800114":
        "IndustrialProcesses RubberandMiscellaneousPlasticsProducts TireManufacture SidewallExtruder",
    "30800115":
        "IndustrialProcesses RubberandMiscellaneousPlasticsProducts TireManufacture Calendering",
    "30800117":
        "IndustrialProcesses RubberandMiscellaneousPlasticsProducts TireManufacture Finishing",
    "30800121":
        "IndustrialProcesses RubberandMiscellaneousPlasticsProducts TireManufacture TreadEndCementing",
    "30800128":
        "IndustrialProcesses RubberandMiscellaneousPlasticsProducts TireManufacture Milling",
    "30800199":
        "IndustrialProcesses RubberandMiscellaneousPlasticsProducts TireManufacture OtherNotClassified",
    "30800501":
        "IndustrialProcesses RubberandMiscellaneousPlasticsProducts TireRetreading TireBuffingMachines",
    "30800699":
        "IndustrialProcesses RubberandMiscellaneousPlasticsProducts OtherFabricatedPlastics OtherNotClassified",
    "30800701":
        "IndustrialProcesses RubberandMiscellaneousPlasticsProducts FiberglassResinProducts PlasticsMachiningDrillingSandingSawingetc.",
    "30800702":
        "IndustrialProcesses RubberandMiscellaneousPlasticsProducts FiberglassResinProducts MouldRelease",
    "30800703":
        "IndustrialProcesses RubberandMiscellaneousPlasticsProducts FiberglassResinProducts SolventConsumption",
    "30800704":
        "IndustrialProcesses RubberandMiscellaneousPlasticsProducts FiberglassResinProducts AdhesiveConsumption",
    "30800705":
        "IndustrialProcesses RubberandMiscellaneousPlasticsProducts FiberglassResinProducts WaxBurnoutOven",
    "30800718":
        "IndustrialProcesses RubberandMiscellaneousPlasticsProducts FiberglassResinProducts GelCoatNonatomizedSpray",
    "30800719":
        "IndustrialProcesses RubberandMiscellaneousPlasticsProducts FiberglassResinProducts GelCoatRoboticSpray",
    "30800720":
        "IndustrialProcesses RubberandMiscellaneousPlasticsProducts FiberglassResinProducts General",
    "30800721":
        "IndustrialProcesses RubberandMiscellaneousPlasticsProducts FiberglassResinProducts GelCoatManualApplication",
    "30800722":
        "IndustrialProcesses RubberandMiscellaneousPlasticsProducts FiberglassResinProducts GelCoatAtomizedSpray",
    "30800723":
        "IndustrialProcesses RubberandMiscellaneousPlasticsProducts FiberglassResinProducts MechanicalResinApplicNonatomizedsprayinclpressurefedrollers",
    "30800726":
        "IndustrialProcesses RubberandMiscellaneousPlasticsProducts FiberglassResinProducts ResinManualApplicationBucketandBrush",
    "30800730":
        "IndustrialProcesses RubberandMiscellaneousPlasticsProducts FiberglassResinProducts MechanicalResinApplicationnonvaporsuppressed",
    "30800731":
        "IndustrialProcesses RubberandMiscellaneousPlasticsProducts FiberglassResinProducts MechanicalResinApplicationvaporsuppressed",
    "30800732":
        "IndustrialProcesses RubberandMiscellaneousPlasticsProducts FiberglassResinProducts MechanicalResinApplicationvacuumbagging",
    "30800736":
        "IndustrialProcesses RubberandMiscellaneousPlasticsProducts FiberglassResinProducts ResinClosedMolding",
    "30800742":
        "IndustrialProcesses RubberandMiscellaneousPlasticsProducts FiberglassResinProducts FilamentApplication",
    "30800748":
        "IndustrialProcesses RubberandMiscellaneousPlasticsProducts FiberglassResinProducts CentrifugalCasting",
    "30800754":
        "IndustrialProcesses RubberandMiscellaneousPlasticsProducts FiberglassResinProducts ContinuousLamination",
    "30800766":
        "IndustrialProcesses RubberandMiscellaneousPlasticsProducts FiberglassResinProducts PolymerCastingCulturedMarbleorMarbleCasting",
    "30800772":
        "IndustrialProcesses RubberandMiscellaneousPlasticsProducts FiberglassResinProducts Pultrusion",
    "30800778":
        "IndustrialProcesses RubberandMiscellaneousPlasticsProducts FiberglassResinProducts SheetMoldingCompoundManufacturing",
    "30800790":
        "IndustrialProcesses RubberandMiscellaneousPlasticsProducts FiberglassResinProducts Mixing",
    "30800791":
        "IndustrialProcesses RubberandMiscellaneousPlasticsProducts FiberglassResinProducts Storage",
    "30800799":
        "IndustrialProcesses RubberandMiscellaneousPlasticsProducts FiberglassResinProducts OtherNotClassified",
    "30800801":
        "IndustrialProcesses RubberandMiscellaneousPlasticsProducts FoamProduction MoldedFoamExpansionProcessUsingSteam",
    "30800802":
        "IndustrialProcesses RubberandMiscellaneousPlasticsProducts FoamProduction MoldedFoamMoldingProcess",
    "30800803":
        "IndustrialProcesses RubberandMiscellaneousPlasticsProducts FoamProduction MoldedFoamBeadStorage",
    "30800804":
        "IndustrialProcesses RubberandMiscellaneousPlasticsProducts FoamProduction MoldedFoamGeneral",
    "30800811":
        "IndustrialProcesses RubberandMiscellaneousPlasticsProducts FoamProduction SlabstockFoamPouringLine",
    "30800899":
        "IndustrialProcesses RubberandMiscellaneousPlasticsProducts FoamProduction General",
    "30800901":
        "IndustrialProcesses RubberandMiscellaneousPlasticsProducts PlasticMiscellaneousProducts PolystyreneGeneral",
    "30801001":
        "IndustrialProcesses RubberandMiscellaneousPlasticsProducts PlasticProductsManufacturing AdhesivesProductionGeneralProcess",
    "30801002":
        "IndustrialProcesses RubberandMiscellaneousPlasticsProducts PlasticProductsManufacturing Extruder",
    "30801003":
        "IndustrialProcesses RubberandMiscellaneousPlasticsProducts PlasticProductsManufacturing FilmProductionDieFlatCircular",
    "30801004":
        "IndustrialProcesses RubberandMiscellaneousPlasticsProducts PlasticProductsManufacturing SheetProductionPolymerizer",
    "30801005":
        "IndustrialProcesses RubberandMiscellaneousPlasticsProducts PlasticProductsManufacturing FoamProductionGeneralProcess",
    "30801006":
        "IndustrialProcesses RubberandMiscellaneousPlasticsProducts PlasticProductsManufacturing LaminationKettlesOven",
    "30801007":
        "IndustrialProcesses RubberandMiscellaneousPlasticsProducts PlasticProductsManufacturing MoldingMachine",
    "30801008":
        "IndustrialProcesses RubberandMiscellaneousPlasticsProducts PlasticProductsManufacturing SheetProductionCalendering",
    "30805001":
        "IndustrialProcesses RubberandMiscellaneousPlasticsProducts VinylFloorTileManufacturing TileChipBinTipper",
    "30805002":
        "IndustrialProcesses RubberandMiscellaneousPlasticsProducts VinylFloorTileManufacturing TileChipReceivingHopper",
    "30805003":
        "IndustrialProcesses RubberandMiscellaneousPlasticsProducts VinylFloorTileManufacturing TileChipBeltConveyors",
    "30805004":
        "IndustrialProcesses RubberandMiscellaneousPlasticsProducts VinylFloorTileManufacturing ScrapHopper",
    "30805005":
        "IndustrialProcesses RubberandMiscellaneousPlasticsProducts VinylFloorTileManufacturing WeighScales",
    "30805006":
        "IndustrialProcesses RubberandMiscellaneousPlasticsProducts VinylFloorTileManufacturing Mixer",
    "30805007":
        "IndustrialProcesses RubberandMiscellaneousPlasticsProducts VinylFloorTileManufacturing Mill",
    "30805008":
        "IndustrialProcesses RubberandMiscellaneousPlasticsProducts VinylFloorTileManufacturing Blender",
    "30805009":
        "IndustrialProcesses RubberandMiscellaneousPlasticsProducts VinylFloorTileManufacturing Conveyors",
    "30805010":
        "IndustrialProcesses RubberandMiscellaneousPlasticsProducts VinylFloorTileManufacturing ScrapChopper",
    "30805011":
        "IndustrialProcesses RubberandMiscellaneousPlasticsProducts VinylFloorTileManufacturing AdhesiveApplicator",
    "30805012":
        "IndustrialProcesses RubberandMiscellaneousPlasticsProducts VinylFloorTileManufacturing LimestonePurge",
    "30805013":
        "IndustrialProcesses RubberandMiscellaneousPlasticsProducts VinylFloorTileManufacturing ScrapDischarging",
    "30805014":
        "IndustrialProcesses RubberandMiscellaneousPlasticsProducts VinylFloorTileManufacturing PVCUnloading",
    "30805015":
        "IndustrialProcesses RubberandMiscellaneousPlasticsProducts VinylFloorTileManufacturing PVCStorage",
    "30805016":
        "IndustrialProcesses RubberandMiscellaneousPlasticsProducts VinylFloorTileManufacturing PVCSurgeBins",
    "30805017":
        "IndustrialProcesses RubberandMiscellaneousPlasticsProducts VinylFloorTileManufacturing LimestoneStorage",
    "30805019":
        "IndustrialProcesses RubberandMiscellaneousPlasticsProducts VinylFloorTileManufacturing UnloadingOperationLimestone",
    "30805099":
        "IndustrialProcesses RubberandMiscellaneousPlasticsProducts VinylFloorTileManufacturing Unspecified",
    "30880001":
        "IndustrialProcesses RubberandMiscellaneousPlasticsProducts EquipmentLeaks EquipmentLeaks",
    "30882599":
        "IndustrialProcesses RubberandMiscellaneousPlasticsProducts WastewaterPointsofGeneration SpecifyPointofGeneration",
    "30890001":
        "IndustrialProcesses RubberandMiscellaneousPlasticsProducts FuelFiredEquipment DistillateOilNo.2ProcessHeaters",
    "30890003":
        "IndustrialProcesses RubberandMiscellaneousPlasticsProducts FuelFiredEquipment NaturalGasProcessHeaters",
    "30890004":
        "IndustrialProcesses RubberandMiscellaneousPlasticsProducts FuelFiredEquipment LiquifiedPetroleumGasLPGProcessHeaters",
    "30890013":
        "IndustrialProcesses RubberandMiscellaneousPlasticsProducts FuelFiredEquipment NaturalGasIncinerators",
    "30890023":
        "IndustrialProcesses RubberandMiscellaneousPlasticsProducts FuelFiredEquipment NaturalGasFlares",
    "30899999":
        "IndustrialProcesses RubberandMiscellaneousPlasticsProducts OtherNotSpecified OtherNotClassified",
    "30900198":
        "IndustrialProcesses FabricatedMetalProducts GeneralProcesses OtherNotClassified",
    "30900199":
        "IndustrialProcesses FabricatedMetalProducts GeneralProcesses OtherNotClassified",
    "30900201":
        "IndustrialProcesses FabricatedMetalProducts AbrasiveBlastingofMetalParts General",
    "30900202":
        "IndustrialProcesses FabricatedMetalProducts AbrasiveBlastingofMetalParts SandAbrasive",
    "30900203":
        "IndustrialProcesses FabricatedMetalProducts AbrasiveBlastingofMetalParts SlagAbrasive",
    "30900204":
        "IndustrialProcesses FabricatedMetalProducts AbrasiveBlastingofMetalParts GarnetAbrasive",
    "30900205":
        "IndustrialProcesses FabricatedMetalProducts AbrasiveBlastingofMetalParts SteelGritAbrasive",
    "30900206":
        "IndustrialProcesses FabricatedMetalProducts AbrasiveBlastingofMetalParts WalnutShellAbrasive",
    "30900207":
        "IndustrialProcesses FabricatedMetalProducts AbrasiveBlastingofMetalParts ShotblastwithAir",
    "30900208":
        "IndustrialProcesses FabricatedMetalProducts AbrasiveBlastingofMetalParts ShotblastwoAir",
    "30900301":
        "IndustrialProcesses FabricatedMetalProducts AbrasiveCleaningofMetalParts BrushCleaning",
    "30900302":
        "IndustrialProcesses FabricatedMetalProducts AbrasiveCleaningofMetalParts TumbleCleaning",
    "30900303":
        "IndustrialProcesses FabricatedMetalProducts AbrasiveCleaningofMetalParts Polishing",
    "30900304":
        "IndustrialProcesses FabricatedMetalProducts AbrasiveCleaningofMetalParts Buffing",
    "30900500":
        "IndustrialProcesses FabricatedMetalProducts Welding General",
    "30900501":
        "IndustrialProcesses FabricatedMetalProducts Welding ArcWeldingGeneralSee309050",
    "30900502":
        "IndustrialProcesses FabricatedMetalProducts Welding OxyfuelWeldingGeneralSee309044",
    "30901001":
        "IndustrialProcesses FabricatedMetalProducts ElectroplatingOperations EntireProcessGeneral",
    "30901003":
        "IndustrialProcesses FabricatedMetalProducts ElectroplatingOperations EntireProcessNickel",
    "30901004":
        "IndustrialProcesses FabricatedMetalProducts ElectroplatingOperations EntireProcessCopper",
    "30901005":
        "IndustrialProcesses FabricatedMetalProducts ElectroplatingOperations EntireProcessZinc",
    "30901006":
        "IndustrialProcesses FabricatedMetalProducts ElectroplatingOperations EntireProcessChrome",
    "30901007":
        "IndustrialProcesses FabricatedMetalProducts ElectroplatingOperations EntireProcessCadmium",
    "30901014":
        "IndustrialProcesses FabricatedMetalProducts ElectroplatingOperations ChromiumalltypesAlkalineCleaning",
    "30901015":
        "IndustrialProcesses FabricatedMetalProducts ElectroplatingOperations ChromiumalltypesAcidDip",
    "30901016":
        "IndustrialProcesses FabricatedMetalProducts ElectroplatingOperations HardChromiumChromicAcidAnodicTreatment",
    "30901018":
        "IndustrialProcesses FabricatedMetalProducts ElectroplatingOperations HardChromiumElectroplatingTank",
    "30901028":
        "IndustrialProcesses FabricatedMetalProducts ElectroplatingOperations DecorativeChromiumElectroplatingTank",
    "30901038":
        "IndustrialProcesses FabricatedMetalProducts ElectroplatingOperations ChromicAcidAnodizingAnodizingTank",
    "30901042":
        "IndustrialProcesses FabricatedMetalProducts ElectroplatingOperations CoppercyanideincludingstrikeElectroplatingTank",
    "30901045":
        "IndustrialProcesses FabricatedMetalProducts ElectroplatingOperations CoppersulfateElectroplatingTank",
    "30901048":
        "IndustrialProcesses FabricatedMetalProducts ElectroplatingOperations CoppergeneralElectroplatingTank1000amphrcurrentapplied",
    "30901052":
        "IndustrialProcesses FabricatedMetalProducts ElectroplatingOperations CadmiumcyanideElectroplatingTank1000amphrcurrentapplied",
    "30901058":
        "IndustrialProcesses FabricatedMetalProducts ElectroplatingOperations CadmiumgeneralElectroplatingTank1000amphrcurrentapplied",
    "30901061":
        "IndustrialProcesses FabricatedMetalProducts ElectroplatingOperations NickelallchlorideElectroplatingTank1000amphrcurrentappli",
    "30901063":
        "IndustrialProcesses FabricatedMetalProducts ElectroplatingOperations NickelchloridesulfateElectroplatingTank1000amphrcurrent",
    "30901065":
        "IndustrialProcesses FabricatedMetalProducts ElectroplatingOperations NickelsulfamateorwattsElectroplatingTank1000amphrcurrent",
    "30901067":
        "IndustrialProcesses FabricatedMetalProducts ElectroplatingOperations NickelnonchlorideElectroplatingTank1000amphrcurrentappli",
    "30901068":
        "IndustrialProcesses FabricatedMetalProducts ElectroplatingOperations NickelgeneralElectroplatingTank",
    "30901078":
        "IndustrialProcesses FabricatedMetalProducts ElectroplatingOperations ZincgeneralElectroplatingTank",
    "30901098":
        "IndustrialProcesses FabricatedMetalProducts ElectroplatingOperations OtherNotClassified",
    "30901101":
        "IndustrialProcesses FabricatedMetalProducts ConversionCoatingofMetalProducts AlkalineCleaningBath",
    "30901102":
        "IndustrialProcesses FabricatedMetalProducts ConversionCoatingofMetalProducts AcidCleaningBathPickling",
    "30901103":
        "IndustrialProcesses FabricatedMetalProducts ConversionCoatingofMetalProducts AnodizingKettle",
    "30901104":
        "IndustrialProcesses FabricatedMetalProducts ConversionCoatingofMetalProducts RinsingFinishing",
    "30901199":
        "IndustrialProcesses FabricatedMetalProducts ConversionCoatingofMetalProducts OtherNotClassified",
    "30901201":
        "IndustrialProcesses FabricatedMetalProducts PreciousMetalsRecovery ReclamationFurnace",
    "30901202":
        "IndustrialProcesses FabricatedMetalProducts PreciousMetalsRecovery CrucibleFurnace",
    "30901203":
        "IndustrialProcesses FabricatedMetalProducts PreciousMetalsRecovery SizeReduction",
    "30901204":
        "IndustrialProcesses FabricatedMetalProducts PreciousMetalsRecovery Reactor",
    "30901205":
        "IndustrialProcesses FabricatedMetalProducts PreciousMetalsRecovery Drying",
    "30901501":
        "IndustrialProcesses FabricatedMetalProducts ChemicalMillingofMetalProducts MillingTank",
    "30901601":
        "IndustrialProcesses FabricatedMetalProducts MetalPipeCoatingofMetalParts AsphaltDipping",
    "30901602":
        "IndustrialProcesses FabricatedMetalProducts MetalPipeCoatingofMetalParts PipeSpinning",
    "30901603":
        "IndustrialProcesses FabricatedMetalProducts MetalPipeCoatingofMetalParts PipeWrapping",
    "30901604":
        "IndustrialProcesses FabricatedMetalProducts MetalPipeCoatingofMetalParts CoalTarAsphaltMeltingKettle",
    "30901699":
        "IndustrialProcesses FabricatedMetalProducts MetalPipeCoatingofMetalParts OtherNotClassified",
    "30902099":
        "IndustrialProcesses FabricatedMetalProducts OtherNotClassified SeeComment",
    "30902501":
        "IndustrialProcesses FabricatedMetalProducts DrumCleaningReclamation DrumBurningFurnace",
    "30903004":
        "IndustrialProcesses FabricatedMetalProducts MachiningOperations SpecifyMaterial",
    "30903005":
        "IndustrialProcesses FabricatedMetalProducts MachiningOperations SawingSpecifyMaterialinComments",
    "30903006":
        "IndustrialProcesses FabricatedMetalProducts MachiningOperations HoningSpecifyMaterialinComments",
    "30903007":
        "IndustrialProcesses FabricatedMetalProducts MachiningOperations LubricationSpecifyMaterial",
    "30903008":
        "IndustrialProcesses FabricatedMetalProducts MachiningOperations PlasmaTorch",
    "30903010":
        "IndustrialProcesses FabricatedMetalProducts MachiningOperations StampingandDrawingAutoBodyParts",
    "30903099":
        "IndustrialProcesses FabricatedMetalProducts MachiningOperations SeeComment",
    "30903901":
        "IndustrialProcesses FabricatedMetalProducts PowderMetallurgyPartManufacturingNAICS332117 ElectricSinterOvenVents",
    "30903902":
        "IndustrialProcesses FabricatedMetalProducts PowderMetallurgyPartManufacturingNAICS332117 ElectricSinterOvenGasBurners",
    "30903951":
        "IndustrialProcesses FabricatedMetalProducts PowderMetallurgyPartManufacturingNAICS332117 ApplicationofCoatingstoSinteredParts",
    "30904001":
        "IndustrialProcesses FabricatedMetalProducts MetalDepositionProcesses MetallizingWireAtomizationandSpraying",
    "30904010":
        "IndustrialProcesses FabricatedMetalProducts MetalDepositionProcesses ThermalSprayingofPowderedMetal",
    "30904020":
        "IndustrialProcesses FabricatedMetalProducts MetalDepositionProcesses PlasmaArcSprayingofPowderedMetal",
    "30904030":
        "IndustrialProcesses FabricatedMetalProducts MetalDepositionProcesses TinningBatchProcess",
    "30904100":
        "IndustrialProcesses FabricatedMetalProducts ResistanceWelding General",
    "30904200":
        "IndustrialProcesses FabricatedMetalProducts Brazing General",
    "30904300":
        "IndustrialProcesses FabricatedMetalProducts Soldering General",
    "30904400":
        "IndustrialProcesses FabricatedMetalProducts OxyfuelWelding General",
    "30904500":
        "IndustrialProcesses FabricatedMetalProducts ThermalSpraying General",
    "30904600":
        "IndustrialProcesses FabricatedMetalProducts OxyfuelCutting General",
    "30904700":
        "IndustrialProcesses FabricatedMetalProducts ArcCutting General",
    "30905000":
        "IndustrialProcesses FabricatedMetalProducts ArcWeldingGeneralConsummableandNonconsummableElectrode ConsumableandNonconsumableElectrode",
    "30905100":
        "IndustrialProcesses FabricatedMetalProducts ShieldedMetalArcWeldingSMAW General",
    "30905104":
        "IndustrialProcesses FabricatedMetalProducts ShieldedMetalArcWeldingSMAW 14Mn4CrElectrode",
    "30905108":
        "IndustrialProcesses FabricatedMetalProducts ShieldedMetalArcWeldingSMAW E11018Electrode",
    "30905112":
        "IndustrialProcesses FabricatedMetalProducts ShieldedMetalArcWeldingSMAW E308Electrode",
    "30905116":
        "IndustrialProcesses FabricatedMetalProducts ShieldedMetalArcWeldingSMAW E310Electrode",
    "30905120":
        "IndustrialProcesses FabricatedMetalProducts ShieldedMetalArcWeldingSMAW E316Electrode",
    "30905124":
        "IndustrialProcesses FabricatedMetalProducts ShieldedMetalArcWeldingSMAW E410Electrode",
    "30905128":
        "IndustrialProcesses FabricatedMetalProducts ShieldedMetalArcWeldingSMAW E6010Electrode",
    "30905132":
        "IndustrialProcesses FabricatedMetalProducts ShieldedMetalArcWeldingSMAW E6011Electrode",
    "30905136":
        "IndustrialProcesses FabricatedMetalProducts ShieldedMetalArcWeldingSMAW E6012Electrode",
    "30905140":
        "IndustrialProcesses FabricatedMetalProducts ShieldedMetalArcWeldingSMAW E6013Electrode",
    "30905144":
        "IndustrialProcesses FabricatedMetalProducts ShieldedMetalArcWeldingSMAW E7018Electrode",
    "30905148":
        "IndustrialProcesses FabricatedMetalProducts ShieldedMetalArcWeldingSMAW E7024Electrode",
    "30905152":
        "IndustrialProcesses FabricatedMetalProducts ShieldedMetalArcWeldingSMAW E7028Electrode",
    "30905156":
        "IndustrialProcesses FabricatedMetalProducts ShieldedMetalArcWeldingSMAW E8018Electrode",
    "30905160":
        "IndustrialProcesses FabricatedMetalProducts ShieldedMetalArcWeldingSMAW E9015Electrode",
    "30905164":
        "IndustrialProcesses FabricatedMetalProducts ShieldedMetalArcWeldingSMAW E9018Electrode",
    "30905176":
        "IndustrialProcesses FabricatedMetalProducts ShieldedMetalArcWeldingSMAW ENiCrMoElectrode",
    "30905180":
        "IndustrialProcesses FabricatedMetalProducts ShieldedMetalArcWeldingSMAW ENiCuElectrode",
    "30905200":
        "IndustrialProcesses FabricatedMetalProducts GasMetalArcWeldingGMAW General",
    "30905210":
        "IndustrialProcesses FabricatedMetalProducts GasMetalArcWeldingGMAW ER1260Electrode",
    "30905212":
        "IndustrialProcesses FabricatedMetalProducts GasMetalArcWeldingGMAW E308lElectrode",
    "30905220":
        "IndustrialProcesses FabricatedMetalProducts GasMetalArcWeldingGMAW ER316Electrode",
    "30905226":
        "IndustrialProcesses FabricatedMetalProducts GasMetalArcWeldingGMAW ER5154Electrode",
    "30905254":
        "IndustrialProcesses FabricatedMetalProducts GasMetalArcWeldingGMAW E70SElectrode",
    "30905276":
        "IndustrialProcesses FabricatedMetalProducts GasMetalArcWeldingGMAW ERNiCrMoElectrode",
    "30905280":
        "IndustrialProcesses FabricatedMetalProducts GasMetalArcWeldingGMAW ERNiCuElectrode",
    "30905300":
        "IndustrialProcesses FabricatedMetalProducts FluxCoredArcWeldingFCAW General",
    "30905306":
        "IndustrialProcesses FabricatedMetalProducts FluxCoredArcWeldingFCAW E110T5K3Electrode",
    "30905308":
        "IndustrialProcesses FabricatedMetalProducts FluxCoredArcWeldingFCAW E11018Electrode",
    "30905312":
        "IndustrialProcesses FabricatedMetalProducts FluxCoredArcWeldingFCAW E308LTElectrode",
    "30905320":
        "IndustrialProcesses FabricatedMetalProducts FluxCoredArcWeldingFCAW E316LTElectrode",
    "30905354":
        "IndustrialProcesses FabricatedMetalProducts FluxCoredArcWeldingFCAW E70TElectrode",
    "30905355":
        "IndustrialProcesses FabricatedMetalProducts FluxCoredArcWeldingFCAW E71TElectrode",
    "30905400":
        "IndustrialProcesses FabricatedMetalProducts SubmergedArcWeldingSAW General",
    "30905410":
        "IndustrialProcesses FabricatedMetalProducts SubmergedArcWeldingSAW EM12KElectrode",
    "30905500":
        "IndustrialProcesses FabricatedMetalProducts ElectrogasWeldingEGW General",
    "30905600":
        "IndustrialProcesses FabricatedMetalProducts ElectrostagWeldingESW General",
    "30905800":
        "IndustrialProcesses FabricatedMetalProducts GasTungstenArcWeldingGTAW General",
    "30905900":
        "IndustrialProcesses FabricatedMetalProducts PlasmaArcWeldingPAW General",
    "30906001":
        "IndustrialProcesses FabricatedMetalProducts PorcelainEnamelCeramicGlazeSpraying SprayBooth",
    "30906002":
        "IndustrialProcesses FabricatedMetalProducts PorcelainEnamelCeramicGlazeSpraying CeramicGlazeMaterialHandling",
    "30906004":
        "IndustrialProcesses FabricatedMetalProducts PorcelainEnamelCeramicGlazeSpraying CeramicGlazeSurfacePreparation",
    "30906005":
        "IndustrialProcesses FabricatedMetalProducts PorcelainEnamelCeramicGlazeSpraying CeramicGlazePlating",
    "30906007":
        "IndustrialProcesses FabricatedMetalProducts PorcelainEnamelCeramicGlazeSpraying CeramicGlazeDrying",
    "30980001":
        "IndustrialProcesses FabricatedMetalProducts EquipmentLeaks EquipmentLeaks",
    "30982002":
        "IndustrialProcesses FabricatedMetalProducts WastewaterAggregate ProcessEquipmentDrains",
    "30982599":
        "IndustrialProcesses FabricatedMetalProducts WastewaterPointsofGeneration SpecifyPointofGeneration",
    "30988801":
        "IndustrialProcesses FabricatedMetalProducts FugitiveEmissions SpecifyinCommentsField",
    "30988806":
        "IndustrialProcesses FabricatedMetalProducts FugitiveEmissions OtherNotClassified",
    "30990001":
        "IndustrialProcesses FabricatedMetalProducts FuelFiredEquipment DistillateOilNo.2ProcessHeaters",
    "30990002":
        "IndustrialProcesses FabricatedMetalProducts FuelFiredEquipment ResidualOilProcessHeaters",
    "30990003":
        "IndustrialProcesses FabricatedMetalProducts FuelFiredEquipment NaturalGasProcessHeaters",
    "30990011":
        "IndustrialProcesses FabricatedMetalProducts FuelFiredEquipment DistillateOilNo.2Incinerators",
    "30990013":
        "IndustrialProcesses FabricatedMetalProducts FuelFiredEquipment NaturalGasIncinerators",
    "30990023":
        "IndustrialProcesses FabricatedMetalProducts FuelFiredEquipment NaturalGasFlares",
    "30999999":
        "IndustrialProcesses FabricatedMetalProducts OtherNotClassified OtherNotClassified",
    "31000101":
        "IndustrialProcesses OilandGasProduction CrudeOilProduction WellCompletion",
    "31000102":
        "IndustrialProcesses OilandGasProduction CrudeOilProduction MiscellaneousWellGeneral",
    "31000103":
        "IndustrialProcesses OilandGasProduction CrudeOilProduction WellsRodPumps",
    "31000104":
        "IndustrialProcesses OilandGasProduction CrudeOilProduction CrudeOilSumps",
    "31000105":
        "IndustrialProcesses OilandGasProduction CrudeOilProduction CrudeOilPits",
    "31000107":
        "IndustrialProcesses OilandGasProduction CrudeOilProduction OilGasWaterSeparation",
    "31000108":
        "IndustrialProcesses OilandGasProduction CrudeOilProduction EvaporationfromLiquidLeaksintoOilWellCellars",
    "31000122":
        "IndustrialProcesses OilandGasProduction CrudeOilProduction WellDrilling",
    "31000123":
        "IndustrialProcesses OilandGasProduction CrudeOilProduction WellCasingVents",
    "31000124":
        "IndustrialProcesses OilandGasProduction CrudeOilProduction ValvesGeneral",
    "31000125":
        "IndustrialProcesses OilandGasProduction CrudeOilProduction ReliefValves",
    "31000126":
        "IndustrialProcesses OilandGasProduction CrudeOilProduction PumpSeals",
    "31000127":
        "IndustrialProcesses OilandGasProduction CrudeOilProduction FlangesandConnections",
    "31000128":
        "IndustrialProcesses OilandGasProduction CrudeOilProduction OilHeating",
    "31000129":
        "IndustrialProcesses OilandGasProduction CrudeOilProduction GasLiquidSeparation",
    "31000130":
        "IndustrialProcesses OilandGasProduction CrudeOilProduction FugitivesCompressorSeals",
    "31000131":
        "IndustrialProcesses OilandGasProduction CrudeOilProduction FugitivesDrains",
    "31000132":
        "IndustrialProcesses OilandGasProduction CrudeOilProduction AtmosphericWashTank2ndStageofGasOilSeparationFlashingLoss",
    "31000133":
        "IndustrialProcesses OilandGasProduction CrudeOilProduction StorageTank",
    "31000140":
        "IndustrialProcesses OilandGasProduction CrudeOilProduction WasteSumpsPrimaryLightCrude",
    "31000142":
        "IndustrialProcesses OilandGasProduction CrudeOilProduction WasteSumpsSecondaryLightCrude",
    "31000146":
        "IndustrialProcesses OilandGasProduction CrudeOilProduction GatheringLines",
    "31000151":
        "IndustrialProcesses OilandGasProduction CrudeOilProduction PneumaticControllersLowBleed",
    "31000152":
        "IndustrialProcesses OilandGasProduction CrudeOilProduction PneumaticControllersHighBleed6scfh",
    "31000153":
        "IndustrialProcesses OilandGasProduction CrudeOilProduction PneumaticControllersIntermittentBleed",
    "31000160":
        "IndustrialProcesses OilandGasProduction CrudeOilProduction Flares",
    "31000199":
        "IndustrialProcesses OilandGasProduction CrudeOilProduction ProcessingOperationsNotClassified",
    "31000201":
        "IndustrialProcesses OilandGasProduction NaturalGasProduction AmineProcess",
    "31000202":
        "IndustrialProcesses OilandGasProduction NaturalGasProduction GasStrippingOperations",
    "31000203":
        "IndustrialProcesses OilandGasProduction NaturalGasProduction CompressorsSeealso31000312and13",
    "31000204":
        "IndustrialProcesses OilandGasProduction NaturalGasProduction Wells",
    "31000205":
        "IndustrialProcesses OilandGasProduction NaturalGasProduction Flares",
    "31000206":
        "IndustrialProcesses OilandGasProduction NaturalGasProduction GasLift",
    "31000207":
        "IndustrialProcesses OilandGasProduction NaturalGasProduction ValvesFugitiveEmissions",
    "31000208":
        "IndustrialProcesses OilandGasProduction NaturalGasProduction SulfurRecoveryUnit",
    "31000209":
        "IndustrialProcesses OilandGasProduction NaturalGasProduction IncineratorsBurningWasteGasorAugmentedWasteGas",
    "31000211":
        "IndustrialProcesses OilandGasProduction NaturalGasProduction PipelinePiggingreleasesduringpigremoval",
    "31000212":
        "IndustrialProcesses OilandGasProduction NaturalGasProduction CondensateStorageTank",
    "31000213":
        "IndustrialProcesses OilandGasProduction NaturalGasProduction ProducedWaterStorageTank",
    "31000214":
        "IndustrialProcesses OilandGasProduction NaturalGasProduction NaturalGasLiquidsStorageTank",
    "31000215":
        "IndustrialProcesses OilandGasProduction NaturalGasProduction FlaresCombustingGases1000BTUscf",
    "31000216":
        "IndustrialProcesses OilandGasProduction NaturalGasProduction FlaresCombustingGases1000BTUscf",
    "31000220":
        "IndustrialProcesses OilandGasProduction NaturalGasProduction AllEquiptLeakFugitivesValvesFlangesConnectionsSealsDrains",
    "31000221":
        "IndustrialProcesses OilandGasProduction NaturalGasProduction SitePreparation",
    "31000222":
        "IndustrialProcesses OilandGasProduction NaturalGasProduction WellCompletions",
    "31000223":
        "IndustrialProcesses OilandGasProduction NaturalGasProduction ReliefValves",
    "31000224":
        "IndustrialProcesses OilandGasProduction NaturalGasProduction PumpSeals",
    "31000225":
        "IndustrialProcesses OilandGasProduction NaturalGasProduction CompressorSeals",
    "31000226":
        "IndustrialProcesses OilandGasProduction NaturalGasProduction FlangesandConnections",
    "31000227":
        "IndustrialProcesses OilandGasProduction NaturalGasProduction GlycolDehydratorReboilerStillStack",
    "31000228":
        "IndustrialProcesses OilandGasProduction NaturalGasProduction GlycolDehydratorReboilerBurner",
    "31000229":
        "IndustrialProcesses OilandGasProduction NaturalGasProduction GatheringLines",
    "31000230":
        "IndustrialProcesses OilandGasProduction NaturalGasProduction HydrocarbonSkimmer",
    "31000231":
        "IndustrialProcesses OilandGasProduction NaturalGasProduction FugitivesDrains",
    "31000233":
        "IndustrialProcesses OilandGasProduction NaturalGasProduction PneumaticControllersLowBleed",
    "31000234":
        "IndustrialProcesses OilandGasProduction NaturalGasProduction PneumaticControllersHighBleed6scfh",
    "31000235":
        "IndustrialProcesses OilandGasProduction NaturalGasProduction PneumaticControllersIntermittentBleed",
    "31000299":
        "IndustrialProcesses OilandGasProduction NaturalGasProduction OtherNotClassified",
    "31000301":
        "IndustrialProcesses OilandGasProduction NaturalGasProcessing GlycolDehydratorReboilerStillStack",
    "31000302":
        "IndustrialProcesses OilandGasProduction NaturalGasProcessing GlycolDehydratorBurnerStack",
    "31000303":
        "IndustrialProcesses OilandGasProduction NaturalGasProcessing GlycolDehydratorSeparatorVent",
    "31000304":
        "IndustrialProcesses OilandGasProduction NaturalGasProcessing GlycolDehydratorSeealso3100030131000303",
    "31000305":
        "IndustrialProcesses OilandGasProduction NaturalGasProcessing AmineProcess",
    "31000306":
        "IndustrialProcesses OilandGasProduction NaturalGasProcessing ProcessValves",
    "31000307":
        "IndustrialProcesses OilandGasProduction NaturalGasProcessing ReliefValves",
    "31000308":
        "IndustrialProcesses OilandGasProduction NaturalGasProcessing OpenendedLines",
    "31000309":
        "IndustrialProcesses OilandGasProduction NaturalGasProcessing CompressorSeals",
    "31000310":
        "IndustrialProcesses OilandGasProduction NaturalGasProcessing PumpSeals",
    "31000311":
        "IndustrialProcesses OilandGasProduction NaturalGasProcessing FlangesandConnections",
    "31000313":
        "IndustrialProcesses OilandGasProduction NaturalGasProcessing ReciprocatingCompressor",
    "31000314":
        "IndustrialProcesses OilandGasProduction NaturalGasProcessing SoliddesiccantDehydrationProcess",
    "31000321":
        "IndustrialProcesses OilandGasProduction NaturalGasProcessing GlycolDehydratorsNiagaranFormationMich.",
    "31000322":
        "IndustrialProcesses OilandGasProduction NaturalGasProcessing GlycolDehydratorsPrairieduChienFormationMich.",
    "31000323":
        "IndustrialProcesses OilandGasProduction NaturalGasProcessing GlycolDehydratorsAntrimFormationMich.",
    "31000324":
        "IndustrialProcesses OilandGasProduction NaturalGasProcessing PneumaticControllersLowBleed",
    "31000325":
        "IndustrialProcesses OilandGasProduction NaturalGasProcessing PneumaticControllersHighBleed6scfh",
    "31000326":
        "IndustrialProcesses OilandGasProduction NaturalGasProcessing PneumaticControllersIntermittentBleed",
    "31000401":
        "IndustrialProcesses OilandGasProduction ProcessHeaters DistillateOilNo.2",
    "31000402":
        "IndustrialProcesses OilandGasProduction ProcessHeaters ResidualOil",
    "31000403":
        "IndustrialProcesses OilandGasProduction ProcessHeaters CrudeOil",
    "31000404":
        "IndustrialProcesses OilandGasProduction ProcessHeaters NaturalGas",
    "31000405":
        "IndustrialProcesses OilandGasProduction ProcessHeaters ProcessGas",
    "31000406":
        "IndustrialProcesses OilandGasProduction ProcessHeaters PropaneButane",
    "31000411":
        "IndustrialProcesses OilandGasProduction ProcessHeaters DistillateOilNo.2SteamGenerators",
    "31000412":
        "IndustrialProcesses OilandGasProduction ProcessHeaters ResidualOilSteamGenerators",
    "31000413":
        "IndustrialProcesses OilandGasProduction ProcessHeaters CrudeOilSteamGenerators",
    "31000414":
        "IndustrialProcesses OilandGasProduction ProcessHeaters NaturalGasSteamGenerators",
    "31000415":
        "IndustrialProcesses OilandGasProduction ProcessHeaters ProcessGasSteamGenerators",
    "31000501":
        "IndustrialProcesses OilandGasProduction LiquidWasteTreatment FloatationUnits",
    "31000502":
        "IndustrialProcesses OilandGasProduction LiquidWasteTreatment LiquidLiquidSeparator",
    "31000503":
        "IndustrialProcesses OilandGasProduction LiquidWasteTreatment OilWaterSeparator",
    "31000504":
        "IndustrialProcesses OilandGasProduction LiquidWasteTreatment OilSludgeWasteWaterPit",
    "31000506":
        "IndustrialProcesses OilandGasProduction LiquidWasteTreatment OilWaterSeparationWastewaterHoldingTanks",
    "31000507":
        "IndustrialProcesses OilandGasProduction LiquidWasteTreatment ProducedWaterTreatment",
    "31088801":
        "IndustrialProcesses OilandGasProduction FugitiveEmissions SpecifyinCommentsField",
    "31088802":
        "IndustrialProcesses OilandGasProduction FugitiveEmissions SpecifyinCommentsField",
    "31088803":
        "IndustrialProcesses OilandGasProduction FugitiveEmissions SpecifyinCommentsField",
    "31088804":
        "IndustrialProcesses OilandGasProduction FugitiveEmissions SpecifyinCommentsField",
    "31088805":
        "IndustrialProcesses OilandGasProduction FugitiveEmissions SpecifyinCommentsField",
    "31088811":
        "IndustrialProcesses OilandGasProduction FugitiveEmissions FugitiveEmissions",
    "31100101":
        "IndustrialProcesses BuildingConstruction ConstructionBuildingContractors SitePreparationTopsoilRemoval",
    "31100102":
        "IndustrialProcesses BuildingConstruction ConstructionBuildingContractors SitePreparationEarthMovingCutandFill",
    "31100103":
        "IndustrialProcesses BuildingConstruction ConstructionBuildingContractors SitePreparationAggregateHaulingOnDirt",
    "31100199":
        "IndustrialProcesses BuildingConstruction ConstructionBuildingContractors OtherNotClassified",
    "31100202":
        "IndustrialProcesses BuildingConstruction DemolitionsSpecialTradeContracts MechanicalorExplosiveDismemberment",
    "31100204":
        "IndustrialProcesses BuildingConstruction DemolitionsSpecialTradeContracts DebrisLoading",
    "31100206":
        "IndustrialProcesses BuildingConstruction DemolitionsSpecialTradeContracts OnsiteTruckTraffic",
    "31100299":
        "IndustrialProcesses BuildingConstruction DemolitionsSpecialTradeContracts OtherNotClassifiedConstructionDemolition",
    "31299999":
        "IndustrialProcesses MachineryMiscellaneous MiscellaneousMachinery OtherNotClassified",
    "31300500":
        "IndustrialProcesses ElectricalEquipment ElectricalSwitchManufacture ElectricalSwitchManufactureOverallProcess",
    "31301001":
        "IndustrialProcesses ElectricalEquipment LightBulbManufacture LightBulbGlasstoSocketBaseLubricationwithSO2",
    "31301100":
        "IndustrialProcesses ElectricalEquipment FluorescentLampManufacture FluorescentLampManufactureOverallProcess",
    "31301200":
        "IndustrialProcesses ElectricalEquipment FluorescentLampRecycling FluorescentLampRecyclingLampCrusher",
    "31303001":
        "IndustrialProcesses ElectricalEquipment ManufacturingGeneral CircuitBoardManufacturing",
    "31303061":
        "IndustrialProcesses ElectricalEquipment ManufacturingGeneral CircuitBoardEtchingAcid",
    "31303063":
        "IndustrialProcesses ElectricalEquipment ManufacturingGeneral CircuitBoardEtchingPlasma",
    "31303501":
        "IndustrialProcesses ElectricalEquipment ManufacturingGeneralProcesses Soldering",
    "31303502":
        "IndustrialProcesses ElectricalEquipment ManufacturingGeneralProcesses Cleaning",
    "31306500":
        "IndustrialProcesses ElectricalEquipment SemiconductorManufacturing IntegratedCircuitManufacturingGeneral",
    "31306501":
        "IndustrialProcesses ElectricalEquipment SemiconductorManufacturing CleaningProcessesWetChemicalSpecifyAqueousSolution",
    "31306502":
        "IndustrialProcesses ElectricalEquipment SemiconductorManufacturing CleaningProcessPlasmaProcessSpecifyGasUsed",
    "31306505":
        "IndustrialProcesses ElectricalEquipment SemiconductorManufacturing PhotoresistOperationsGeneral",
    "31306510":
        "IndustrialProcesses ElectricalEquipment SemiconductorManufacturing ChemicalVaporDepositionGeneralSpecifyGasUsed",
    "31306520":
        "IndustrialProcesses ElectricalEquipment SemiconductorManufacturing DiffusionProcessDepositionOperationSpecifyGasUsed",
    "31306530":
        "IndustrialProcesses ElectricalEquipment SemiconductorManufacturing EtchingProcessWetChemicalSpecifyAqueousSolution",
    "31306531":
        "IndustrialProcesses ElectricalEquipment SemiconductorManufacturing EtchingProcessPlasmaReactiveIonSpecifyGasUsed",
    "31306599":
        "IndustrialProcesses ElectricalEquipment SemiconductorManufacturing MiscellaneousOperationsGeneralSpecifyMaterial",
    "31307001":
        "IndustrialProcesses ElectricalEquipment ElectricalWindingsReclamation SingleChamberIncineratorOven",
    "31307002":
        "IndustrialProcesses ElectricalEquipment ElectricalWindingsReclamation MultipleChamberIncineratorOven",
    "31380001":
        "IndustrialProcesses ElectricalEquipment EquipmentLeaks EquipmentLeaks",
    "31382002":
        "IndustrialProcesses ElectricalEquipment WastewaterAggregate ProcessEquipmentDrains",
    "31382599":
        "IndustrialProcesses ElectricalEquipment WastewaterPointsofGeneration SpecifyPointofGeneration",
    "31390001":
        "IndustrialProcesses ElectricalEquipment ProcessHeaters DistillateOilNo.2",
    "31390002":
        "IndustrialProcesses ElectricalEquipment ProcessHeaters ResidualOil",
    "31390003":
        "IndustrialProcesses ElectricalEquipment ProcessHeaters NaturalGas",
    "31399999":
        "IndustrialProcesses ElectricalEquipment OtherNotClassified OtherNotClassified",
    "31400901":
        "IndustrialProcesses TransportationEquipment AutomobilesTruckAssemblyOperations SolderJointGrinding",
    "31400902":
        "IndustrialProcesses TransportationEquipment AutomobilesTruckAssemblyOperations SolderingMachine",
    "31400903":
        "IndustrialProcesses TransportationEquipment AutomobilesTruckAssemblyOperations Stamping",
    "31401001":
        "IndustrialProcesses TransportationEquipment BrakeShoeDebonding SingleChamberIncinerator",
    "31401002":
        "IndustrialProcesses TransportationEquipment BrakeShoeDebonding MultipleChamberIncinerator",
    "31401101":
        "IndustrialProcesses TransportationEquipment AutoBodyShredding PrimaryMetalRecoveryLine",
    "31401102":
        "IndustrialProcesses TransportationEquipment AutoBodyShredding SecondaryMetalRecoveryLine",
    "31401201":
        "IndustrialProcesses TransportationEquipment WeldingSolderingAutomotiveRepair Soldering",
    "31401501":
        "IndustrialProcesses TransportationEquipment BoatManufacturing General",
    "31401503":
        "IndustrialProcesses TransportationEquipment BoatManufacturing ResinStorage",
    "31401510":
        "IndustrialProcesses TransportationEquipment BoatManufacturing MoldingandLaminationOperations",
    "31401511":
        "IndustrialProcesses TransportationEquipment BoatManufacturing OpenContactMoldingManualGelCoatApplication",
    "31401512":
        "IndustrialProcesses TransportationEquipment BoatManufacturing OpenContactMoldingSprayGelCoatApplication",
    "31401513":
        "IndustrialProcesses TransportationEquipment BoatManufacturing OpenContactMoldingGelCoatCuring",
    "31401514":
        "IndustrialProcesses TransportationEquipment BoatManufacturing OpenContactMoldingResinLaminateApplicationMachineLayup",
    "31401515":
        "IndustrialProcesses TransportationEquipment BoatManufacturing OpenContactMoldingResinLaminateApplicationHandLayupSpraying",
    "31401516":
        "IndustrialProcesses TransportationEquipment BoatManufacturing OpenContactMoldingResinHandLayup",
    "31401517":
        "IndustrialProcesses TransportationEquipment BoatManufacturing OpenContactMoldingResinSprayLayup",
    "31401525":
        "IndustrialProcesses TransportationEquipment BoatManufacturing ClosedMolding",
    "31401540":
        "IndustrialProcesses TransportationEquipment BoatManufacturing LaminationPreparationofResinLaminate",
    "31401550":
        "IndustrialProcesses TransportationEquipment BoatManufacturing AssemblyArea",
    "31401551":
        "IndustrialProcesses TransportationEquipment BoatManufacturing AssemblyAreaSandingTrimmingofLaminatedParts",
    "31401552":
        "IndustrialProcesses TransportationEquipment BoatManufacturing AssemblyAreaPaintSpraying",
    "31401553":
        "IndustrialProcesses TransportationEquipment BoatManufacturing AssemblyAreaCarpetGlues",
    "31401560":
        "IndustrialProcesses TransportationEquipment BoatManufacturing Cleanup",
    "31401570":
        "IndustrialProcesses TransportationEquipment BoatManufacturing WasteDisposalUsedCleanupSolvents",
    "31480001":
        "IndustrialProcesses TransportationEquipment EquipmentLeaks EquipmentLeaks",
    "31482002":
        "IndustrialProcesses TransportationEquipment WastewaterAggregate ProcessEquipmentDrains",
    "31482599":
        "IndustrialProcesses TransportationEquipment WastewaterPointofGeneration SpecifyPointofGeneration",
    "31499999":
        "IndustrialProcesses TransportationEquipment OtherNotClassified OtherNotClassified",
    "31501001":
        "IndustrialProcesses PhotoEquipHealthCareLabsAirConditSwimPools PhotocopyingEquipmentManufacturing ResinTransferStorage",
    "31501002":
        "IndustrialProcesses PhotoEquipHealthCareLabsAirConditSwimPools PhotocopyingEquipmentManufacturing TonerClassification",
    "31502001":
        "IndustrialProcesses PhotoEquipHealthCareLabsAirConditSwimPools HealthCare SterilizationwithEthyleneOxide",
    "31502002":
        "IndustrialProcesses PhotoEquipHealthCareLabsAirConditSwimPools HealthCare SterilizationwithFreon",
    "31502003":
        "IndustrialProcesses PhotoEquipHealthCareLabsAirConditSwimPools HealthCare SterilizationwithFormaldehyde",
    "31502088":
        "IndustrialProcesses PhotoEquipHealthCareLabsAirConditSwimPools HealthCare LaboratoryFugitiveEmissions",
    "31502089":
        "IndustrialProcesses PhotoEquipHealthCareLabsAirConditSwimPools HealthCare MiscellaneousFugitiveEmissions",
    "31502101":
        "IndustrialProcesses PhotoEquipHealthCareLabsAirConditSwimPools HealthCareCrematoriums CrematoryStack",
    "31502102":
        "IndustrialProcesses PhotoEquipHealthCareLabsAirConditSwimPools HealthCareCrematoriums CrematoryStackHumanandAnimalCrematories",
    "31502103":
        "IndustrialProcesses PhotoEquipHealthCareLabsAirConditSwimPools HealthCareCrematoriums CremationHuman",
    "31502104":
        "IndustrialProcesses PhotoEquipHealthCareLabsAirConditSwimPools HealthCareCrematoriums CremationAnimal",
    "31502500":
        "IndustrialProcesses PhotoEquipHealthCareLabsAirConditSwimPools DentalAlloyMercuryAmalgamsProduction DentalAlloyMercuryAmalgamsProductionOverallProcess",
    "31502700":
        "IndustrialProcesses PhotoEquipHealthCareLabsAirConditSwimPools ThermometerManufacture ThermometerManufactureOverallProcess",
    "31503001":
        "IndustrialProcesses PhotoEquipHealthCareLabsAirConditSwimPools Laboratories BenchScaleReagentsResearch",
    "31503002":
        "IndustrialProcesses PhotoEquipHealthCareLabsAirConditSwimPools Laboratories BenchScaleReagentsTesting",
    "31503003":
        "IndustrialProcesses PhotoEquipHealthCareLabsAirConditSwimPools Laboratories BenchScaleReagentsMedical",
    "31503101":
        "IndustrialProcesses PhotoEquipHealthCareLabsAirConditSwimPools Xrays MedicalGeneral",
    "31503102":
        "IndustrialProcesses PhotoEquipHealthCareLabsAirConditSwimPools Xrays StructuralGeneral",
    "31504001":
        "IndustrialProcesses PhotoEquipHealthCareLabsAirConditSwimPools CommercialSwimmingPoolsChlorinationChloroform ChlorinationChloroform",
    "31505001":
        "IndustrialProcesses PhotoEquipHealthCareLabsAirConditSwimPools AirconditioningRefrigeration CoolingFluidFreons",
    "31505002":
        "IndustrialProcesses PhotoEquipHealthCareLabsAirConditSwimPools AirconditioningRefrigeration CoolingFluidAmmonia",
    "31505003":
        "IndustrialProcesses PhotoEquipHealthCareLabsAirConditSwimPools AirconditioningRefrigeration CoolingFluidSpecifyFluid",
    "31603001":
        "IndustrialProcesses PhotographicFilmManufacturing ProductManufacturingSubstratePreparation ExtrusionOperations",
    "31603002":
        "IndustrialProcesses PhotographicFilmManufacturing ProductManufacturingSubstratePreparation FilmSupportOperations",
    "31604001":
        "IndustrialProcesses PhotographicFilmManufacturing ProductManufacturingChemicalPreparation ChemicalManufacturing",
    "31604002":
        "IndustrialProcesses PhotographicFilmManufacturing ProductManufacturingChemicalPreparation EmulsionMakingOperations",
    "31604003":
        "IndustrialProcesses PhotographicFilmManufacturing ProductManufacturingChemicalPreparation ChemicalMixingOperations",
    "31605001":
        "IndustrialProcesses PhotographicFilmManufacturing ProductManufacturingSurfaceTreatments SurfaceCoatingOperations",
    "31605002":
        "IndustrialProcesses PhotographicFilmManufacturing ProductManufacturingSurfaceTreatments GridIonizers",
    "31605003":
        "IndustrialProcesses PhotographicFilmManufacturing ProductManufacturingSurfaceTreatments CoronaDischargeTreatment",
    "31605004":
        "IndustrialProcesses PhotographicFilmManufacturing ProductManufacturingSurfaceTreatments PhotographicDryingOperations",
    "31606001":
        "IndustrialProcesses PhotographicFilmManufacturing ProductManufacturingFinishingOperations GeneralFilmManufacturing",
    "31606002":
        "IndustrialProcesses PhotographicFilmManufacturing ProductManufacturingFinishingOperations CuttingSlittingOperations",
    "31612001":
        "IndustrialProcesses PhotographicFilmManufacturing SupportActivitiesCleaningOperations TankCleaningOperations",
    "31612002":
        "IndustrialProcesses PhotographicFilmManufacturing SupportActivitiesCleaningOperations GeneralCleaningOperations",
    "31612003":
        "IndustrialProcesses PhotographicFilmManufacturing SupportActivitiesCleaningOperations PartsCleaningOperations",
    "31613001":
        "IndustrialProcesses PhotographicFilmManufacturing SupportActivitiesStorageOperations SolventStorageOperations",
    "31613002":
        "IndustrialProcesses PhotographicFilmManufacturing SupportActivitiesStorageOperations GeneralStorageOperations",
    "31613003":
        "IndustrialProcesses PhotographicFilmManufacturing SupportActivitiesStorageOperations StorageSilos",
    "31613004":
        "IndustrialProcesses PhotographicFilmManufacturing SupportActivitiesStorageOperations WasteStorageOperations",
    "31614001":
        "IndustrialProcesses PhotographicFilmManufacturing SupportActivitiesMaterialTransferOperations FillingOperationsnonpetroleum",
    "31614002":
        "IndustrialProcesses PhotographicFilmManufacturing SupportActivitiesMaterialTransferOperations TransferofChemicals",
    "31615001":
        "IndustrialProcesses PhotographicFilmManufacturing SupportActivitiesSeparationProcesses RecoveryOperations",
    "31615003":
        "IndustrialProcesses PhotographicFilmManufacturing SupportActivitiesSeparationProcesses DistillationOperations",
    "31616001":
        "IndustrialProcesses PhotographicFilmManufacturing SupportActivitiesOtherOperations GeneralVentillationManufacturingAreas",
    "31616002":
        "IndustrialProcesses PhotographicFilmManufacturing SupportActivitiesOtherOperations GeneralProcessTankOperations",
    "31616003":
        "IndustrialProcesses PhotographicFilmManufacturing SupportActivitiesOtherOperations MiscellaneousManufacturingOperations",
    "31616004":
        "IndustrialProcesses PhotographicFilmManufacturing SupportActivitiesOtherOperations PaintSprayingOperations",
    "31616005":
        "IndustrialProcesses PhotographicFilmManufacturing SupportActivitiesOtherOperations GeneralMaintenanceOperations",
    "31616006":
        "IndustrialProcesses PhotographicFilmManufacturing SupportActivitiesOtherOperations ChemicalWeighingOperations",
    "31700101":
        "IndustrialProcesses NGTS NaturalGasTransmissionandStorageFacilities PneumaticControllersLowBleed",
    "31801001":
        "IndustrialProcesses ElectricGeneration GeysersGeothermal SteamTurbine",
    "31801030":
        "IndustrialProcesses ElectricGeneration GeysersGeothermal PipelineFugitivesBlowdown",
    "32099997":
        "IndustrialProcesses LeatherandLeatherProducts OtherNotClassified OtherNotClassified",
    "32099998":
        "IndustrialProcesses LeatherandLeatherProducts OtherNotClassified OtherNotClassified",
    "32099999":
        "IndustrialProcesses LeatherandLeatherProducts OtherNotClassified OtherNotClassified",
    "33000101":
        "IndustrialProcesses TextileProducts Miscellaneous YarnPreparationBleaching",
    "33000102":
        "IndustrialProcesses TextileProducts Miscellaneous Printing",
    "33000103":
        "IndustrialProcesses TextileProducts Miscellaneous PolyesterThreadProduction",
    "33000104":
        "IndustrialProcesses TextileProducts Miscellaneous TenterFramesHeatSetting",
    "33000105":
        "IndustrialProcesses TextileProducts Miscellaneous Carding",
    "33000106":
        "IndustrialProcesses TextileProducts Miscellaneous Drying",
    "33000199":
        "IndustrialProcesses TextileProducts Miscellaneous OtherNotClassified",
    "33000201":
        "IndustrialProcesses TextileProducts RubberizedFabrics General",
    "33000202":
        "IndustrialProcesses TextileProducts RubberizedFabrics WetCoatingGeneral",
    "33000203":
        "IndustrialProcesses TextileProducts RubberizedFabrics HotMeltCoatingGeneral",
    "33000211":
        "IndustrialProcesses TextileProducts RubberizedFabrics Impregnation",
    "33000212":
        "IndustrialProcesses TextileProducts RubberizedFabrics WetCoating",
    "33000213":
        "IndustrialProcesses TextileProducts RubberizedFabrics HotMeltCoating",
    "33000214":
        "IndustrialProcesses TextileProducts RubberizedFabrics WetCoatingMixing",
    "33000297":
        "IndustrialProcesses TextileProducts RubberizedFabrics OtherNotClassified",
    "33000298":
        "IndustrialProcesses TextileProducts RubberizedFabrics OtherNotClassified",
    "33000299":
        "IndustrialProcesses TextileProducts RubberizedFabrics OtherNotClassified",
    "33000301":
        "IndustrialProcesses TextileProducts CarpetOperations PreparationProcessing",
    "33000302":
        "IndustrialProcesses TextileProducts CarpetOperations PrintingDyeing",
    "33000303":
        "IndustrialProcesses TextileProducts CarpetOperations BasicMaterialMixing",
    "33000304":
        "IndustrialProcesses TextileProducts CarpetOperations Shearing",
    "33000306":
        "IndustrialProcesses TextileProducts CarpetOperations HeatTreating",
    "33000307":
        "IndustrialProcesses TextileProducts CarpetOperations Drying",
    "33000399":
        "IndustrialProcesses TextileProducts CarpetOperations OtherNotClassified",
    "33000499":
        "IndustrialProcesses TextileProducts FabricFinishing OtherNotClassified",
    "33088801":
        "IndustrialProcesses TextileProducts FugitiveEmissions SpecifyinCommentsField",
    "36000101":
        "IndustrialProcesses PrintingPublishing ScrapProcesses TypesettingLeadRemeltingRemeltingLeadEmissionsOnly",
    "36000102":
        "IndustrialProcesses PrintingPublishing ScrapProcesses FlexographicScrapSubstrateCollectionSystem",
    "36000103":
        "IndustrialProcesses PrintingPublishing ScrapProcesses RotogravureScrapSubstrateCollectionSystem",
    "38500101":
        "IndustrialProcesses CoolingTower ProcessCooling MechanicalDraft",
    "38500102":
        "IndustrialProcesses CoolingTower ProcessCooling NaturalDraft",
    "38500110":
        "IndustrialProcesses CoolingTower ProcessCooling OtherNotClassified",
    "39000189":
        "IndustrialProcesses InprocessFuelUse AnthraciteCoal General",
    "39000199":
        "IndustrialProcesses InprocessFuelUse AnthraciteCoal General",
    "39000201":
        "IndustrialProcesses InprocessFuelUse BituminousCoal CementKilnDryer",
    "39000203":
        "IndustrialProcesses InprocessFuelUse BituminousCoal LimeKilnBituminous",
    "39000288":
        "IndustrialProcesses InprocessFuelUse BituminousCoal GeneralSubbituminous",
    "39000289":
        "IndustrialProcesses InprocessFuelUse BituminousCoal GeneralBituminous",
    "39000299":
        "IndustrialProcesses InprocessFuelUse BituminousCoal GeneralBituminous",
    "39000399":
        "IndustrialProcesses InprocessFuelUse Lignite General",
    "39000402":
        "IndustrialProcesses InprocessFuelUse ResidualOil CementKilnDryer",
    "39000403":
        "IndustrialProcesses InprocessFuelUse ResidualOil LimeKiln",
    "39000489":
        "IndustrialProcesses InprocessFuelUse ResidualOil General",
    "39000499":
        "IndustrialProcesses InprocessFuelUse ResidualOil General",
    "39000501":
        "IndustrialProcesses InprocessFuelUse DistillateOil AsphaltDryer",
    "39000502":
        "IndustrialProcesses InprocessFuelUse DistillateOil CementKilnDryer",
    "39000503":
        "IndustrialProcesses InprocessFuelUse DistillateOil LimeKiln",
    "39000598":
        "IndustrialProcesses InprocessFuelUse DistillateOil Grade4OilGeneral",
    "39000599":
        "IndustrialProcesses InprocessFuelUse DistillateOil General",
    "39000602":
        "IndustrialProcesses InprocessFuelUse NaturalGas CementKilnDryer",
    "39000603":
        "IndustrialProcesses InprocessFuelUse NaturalGas LimeKiln",
    "39000605":
        "IndustrialProcesses InprocessFuelUse NaturalGas MetalMelting",
    "39000689":
        "IndustrialProcesses InprocessFuelUse NaturalGas General",
    "39000699":
        "IndustrialProcesses InprocessFuelUse NaturalGas General",
    "39000701":
        "IndustrialProcesses InprocessFuelUse ProcessGas CokeOvenorBlastFurnace",
    "39000702":
        "IndustrialProcesses InprocessFuelUse ProcessGas CokeOvenGas",
    "39000797":
        "IndustrialProcesses InprocessFuelUse ProcessGas General",
    "39000801":
        "IndustrialProcesses InprocessFuelUse Coke MineralWoolFuel",
    "39000889":
        "IndustrialProcesses InprocessFuelUse Coke General",
    "39000899":
        "IndustrialProcesses InprocessFuelUse Coke GeneralCoke",
    "39000989":
        "IndustrialProcesses InprocessFuelUse Wood General",
    "39000999":
        "IndustrialProcesses InprocessFuelUse Wood GeneralWood",
    "39001089":
        "IndustrialProcesses InprocessFuelUse LiquifiedPetroleumGas General",
    "39001099":
        "IndustrialProcesses InprocessFuelUse LiquifiedPetroleumGas General",
    "39001289":
        "IndustrialProcesses InprocessFuelUse SolidWaste SolidWasteGeneral",
    "39001299":
        "IndustrialProcesses InprocessFuelUse SolidWaste General",
    "39001385":
        "IndustrialProcesses InprocessFuelUse LiquidWaste RecoveredSolventGeneral",
    "39001399":
        "IndustrialProcesses InprocessFuelUse LiquidWaste General",
    "39090001":
        "IndustrialProcesses InprocessFuelUse FuelStorageFixedRoofTanks ResidualOilBreathingLoss",
    "39090002":
        "IndustrialProcesses InprocessFuelUse FuelStorageFixedRoofTanks ResidualOilWorkingLoss",
    "39090003":
        "IndustrialProcesses InprocessFuelUse FuelStorageFixedRoofTanks DistillateOilNo.2BreathingLoss",
    "39090004":
        "IndustrialProcesses InprocessFuelUse FuelStorageFixedRoofTanks DistillateOilNo.2WorkingLoss",
    "39090005":
        "IndustrialProcesses InprocessFuelUse FuelStorageFixedRoofTanks OilNo.6BreathingLoss",
    "39090006":
        "IndustrialProcesses InprocessFuelUse FuelStorageFixedRoofTanks OilNo.6WorkingLoss",
    "39090007":
        "IndustrialProcesses InprocessFuelUse FuelStorageFixedRoofTanks MethanolBreathingLoss",
    "39090008":
        "IndustrialProcesses InprocessFuelUse FuelStorageFixedRoofTanks MethanolWorkingLoss",
    "39090009":
        "IndustrialProcesses InprocessFuelUse FuelStorageFixedRoofTanks ResidualOilCrudeOilBreathingLoss",
    "39090010":
        "IndustrialProcesses InprocessFuelUse FuelStorageFixedRoofTanks ResidualOilCrudeOilWorkingLoss",
    "39090011":
        "IndustrialProcesses InprocessFuelUse FuelStorageFixedRoofTanks DualFuelGasOilBreathingLoss",
    "39090012":
        "IndustrialProcesses InprocessFuelUse FuelStorageFixedRoofTanks DualFuelGasOilWorkingLoss",
    "39091001":
        "IndustrialProcesses InprocessFuelUse FuelStorageFloatingRoofTanks ResidualOilStandingLoss",
    "39091003":
        "IndustrialProcesses InprocessFuelUse FuelStorageFloatingRoofTanks DistillateOilNo.2StandingLoss",
    "39091004":
        "IndustrialProcesses InprocessFuelUse FuelStorageFloatingRoofTanks DistillateOilNo.2WithdrawalLoss",
    "39091005":
        "IndustrialProcesses InprocessFuelUse FuelStorageFloatingRoofTanks OilNo.6StandingLoss",
    "39091006":
        "IndustrialProcesses InprocessFuelUse FuelStorageFloatingRoofTanks OilNo.6WithdrawalLoss",
    "39091007":
        "IndustrialProcesses InprocessFuelUse FuelStorageFloatingRoofTanks MethanolStandingLoss",
    "39091009":
        "IndustrialProcesses InprocessFuelUse FuelStorageFloatingRoofTanks ResidualOilCrudeOilStandingLoss",
    "39091010":
        "IndustrialProcesses InprocessFuelUse FuelStorageFloatingRoofTanks ResidualOilCrudeOilWithdrawalLoss",
    "39091011":
        "IndustrialProcesses InprocessFuelUse FuelStorageFloatingRoofTanks DualFuelGasOilStandingLoss",
    "39091012":
        "IndustrialProcesses InprocessFuelUse FuelStorageFloatingRoofTanks DualFuelGasOilWithdrawalLoss",
    "39092050":
        "IndustrialProcesses InprocessFuelUse FuelStoragePressureTanks NaturalGasWithdrawalLoss",
    "39092051":
        "IndustrialProcesses InprocessFuelUse FuelStoragePressureTanks LPGWithdrawalLoss",
    "39092052":
        "IndustrialProcesses InprocessFuelUse FuelStoragePressureTanks LandfillGasWithdrawalLoss",
    "39092053":
        "IndustrialProcesses InprocessFuelUse FuelStoragePressureTanks RefineryGasWithdrawalLoss",
    "39092055":
        "IndustrialProcesses InprocessFuelUse FuelStoragePressureTanks ProcessGasWithdrawalLoss",
    "39092056":
        "IndustrialProcesses InprocessFuelUse FuelStoragePressureTanks DualFuelGasOilWithdrawalLoss",
    "39900501":
        "IndustrialProcesses MiscellaneousManufacturingIndustries ProcessHeaterFurnace DistillateOil",
    "39900601":
        "IndustrialProcesses MiscellaneousManufacturingIndustries ProcessHeaterFurnace NaturalGas",
    "39900701":
        "IndustrialProcesses MiscellaneousManufacturingIndustries ProcessHeaterFurnace ProcessGas",
    "39900711":
        "IndustrialProcesses MiscellaneousManufacturingIndustries ProcessHeaterFurnace RefineryGas",
    "39900721":
        "IndustrialProcesses MiscellaneousManufacturingIndustries ProcessHeaterFurnace DigesterGas",
    "39900801":
        "IndustrialProcesses MiscellaneousManufacturingIndustries ProcessHeaterFurnace LandfillGas",
    "39901001":
        "IndustrialProcesses MiscellaneousManufacturingIndustries ProcessHeaterFurnace LPG",
    "39901601":
        "IndustrialProcesses MiscellaneousManufacturingIndustries ProcessHeaterFurnace Methanol",
    "39901701":
        "IndustrialProcesses MiscellaneousManufacturingIndustries ProcessHeaterFurnace Gasoline",
    "39902001":
        "IndustrialProcesses MiscellaneousManufacturingIndustries PaintStrippingNonchemical MediaBlastingGeneral",
    "39902002":
        "IndustrialProcesses MiscellaneousManufacturingIndustries PaintStrippingNonchemical MediaBlastingSand",
    "39902003":
        "IndustrialProcesses MiscellaneousManufacturingIndustries PaintStrippingNonchemical MediaBlastingGrit",
    "39902004":
        "IndustrialProcesses MiscellaneousManufacturingIndustries PaintStrippingNonchemical MediaBlastingMetalShot",
    "39902009":
        "IndustrialProcesses MiscellaneousManufacturingIndustries PaintStrippingNonchemical MediaBlastingPlasticBead",
    "39902054":
        "IndustrialProcesses MiscellaneousManufacturingIndustries PaintStrippingNonchemical CarbonDioxidePulsedLaser",
    "39990001":
        "IndustrialProcesses MiscellaneousManufacturingIndustries MiscellaneousManufacturingIndustries DistillateOilNo.2ProcessHeaters",
    "39990002":
        "IndustrialProcesses MiscellaneousManufacturingIndustries MiscellaneousManufacturingIndustries ResidualOilProcessHeaters",
    "39990003":
        "IndustrialProcesses MiscellaneousManufacturingIndustries MiscellaneousManufacturingIndustries NaturalGasProcessHeaters",
    "39990004":
        "IndustrialProcesses MiscellaneousManufacturingIndustries MiscellaneousManufacturingIndustries ProcessGasProcessHeaters",
    "39990011":
        "IndustrialProcesses MiscellaneousManufacturingIndustries MiscellaneousManufacturingIndustries DistillateOilNo.2Incinerators",
    "39990012":
        "IndustrialProcesses MiscellaneousManufacturingIndustries MiscellaneousManufacturingIndustries ResidualOilIncinerators",
    "39990013":
        "IndustrialProcesses MiscellaneousManufacturingIndustries MiscellaneousManufacturingIndustries NaturalGasIncinerators",
    "39990014":
        "IndustrialProcesses MiscellaneousManufacturingIndustries MiscellaneousManufacturingIndustries ProcessGasIncinerators",
    "39990021":
        "IndustrialProcesses MiscellaneousManufacturingIndustries MiscellaneousManufacturingIndustries DistillateOilNo.2Flares",
    "39990022":
        "IndustrialProcesses MiscellaneousManufacturingIndustries MiscellaneousManufacturingIndustries ResidualOilFlares",
    "39990023":
        "IndustrialProcesses MiscellaneousManufacturingIndustries MiscellaneousManufacturingIndustries NaturalGasFlares",
    "39990024":
        "IndustrialProcesses MiscellaneousManufacturingIndustries MiscellaneousManufacturingIndustries ProcessGasFlares",
    "39999989":
        "IndustrialProcesses MiscellaneousManufacturingIndustries MiscellaneousIndustrialProcesses OtherNotClassified",
    "39999991":
        "IndustrialProcesses MiscellaneousManufacturingIndustries MiscellaneousIndustrialProcesses OtherNotClassified",
    "39999992":
        "IndustrialProcesses MiscellaneousManufacturingIndustries MiscellaneousIndustrialProcesses OtherNotClassified",
    "39999993":
        "IndustrialProcesses MiscellaneousManufacturingIndustries MiscellaneousIndustrialProcesses OtherNotClassified",
    "39999994":
        "IndustrialProcesses MiscellaneousManufacturingIndustries MiscellaneousIndustrialProcesses OtherNotElsewhereClassified",
    "39999995":
        "IndustrialProcesses MiscellaneousManufacturingIndustries MiscellaneousIndustrialProcesses OtherNotClassified",
    "39999996":
        "IndustrialProcesses MiscellaneousManufacturingIndustries MiscellaneousIndustrialProcesses OtherNotElsewhereClassified",
    "39999997":
        "IndustrialProcesses MiscellaneousManufacturingIndustries MiscellaneousIndustrialProcesses OtherNotClassified",
    "39999998":
        "IndustrialProcesses MiscellaneousManufacturingIndustries MiscellaneousIndustrialProcesses OtherNotClassified",
    "39999999":
        "IndustrialProcesses MiscellaneousManufacturingIndustries MiscellaneousIndustrialProcesses OtherNotElsewhereClassified",
    "40100101":
        "ChemicalEvaporation OrganicSolventEvaporation DryCleaning Perchloroethylene",
    "40100102":
        "ChemicalEvaporation OrganicSolventEvaporation DryCleaning StoddardPetroleumSolventUse41000101or41000201",
    "40100103":
        "PetroleumandSolventEvaporation OrganicSolventEvaporation DryCleaning Perchloroethylene",
    "40100104":
        "ChemicalEvaporation OrganicSolventEvaporation DryCleaning StoddardPetroleumSolventUse41000102or41000202",
    "40100146":
        "ChemicalEvaporation OrganicSolventEvaporation DryCleaning StoddardFiltrDispCookedMuckDrainedUse41000161or00261",
    "40100198":
        "ChemicalEvaporation OrganicSolventEvaporation DryCleaning OtherNotClassified",
    "40100199":
        "PetroleumandSolventEvaporation OrganicSolventEvaporation DryCleaning SeeComment",
    "40100201":
        "ChemicalEvaporation OrganicSolventEvaporation Degreasing StoddardPetroleumSolventOpentopVaporDegreasing",
    "40100202":
        "ChemicalEvaporation OrganicSolventEvaporation Degreasing 111TrichloroethaneMethylChloroformOpentopVaporDegreasing",
    "40100203":
        "ChemicalEvaporation OrganicSolventEvaporation Degreasing PerchloroethyleneOpentopVaporDegreasing",
    "40100204":
        "ChemicalEvaporation OrganicSolventEvaporation Degreasing MethyleneChlorideOpentopVaporDegreasing",
    "40100205":
        "ChemicalEvaporation OrganicSolventEvaporation Degreasing TrichloroethyleneOpentopVaporDegreasing",
    "40100206":
        "ChemicalEvaporation OrganicSolventEvaporation Degreasing TolueneOpentopVaporDegreasing",
    "40100207":
        "ChemicalEvaporation OrganicSolventEvaporation Degreasing TrichlorotrifluoroethaneFreonOpentopVaporDegreasing",
    "40100209":
        "ChemicalEvaporation OrganicSolventEvaporation Degreasing ButylAcetateOpentopVaporDegreasing",
    "40100215":
        "ChemicalEvaporation OrganicSolventEvaporation Degreasing EntireUnitOpentopVaporDegreasing",
    "40100221":
        "ChemicalEvaporation OrganicSolventEvaporation Degreasing StoddardPetroleumSolventConveyorizedVaporDegreasing",
    "40100222":
        "ChemicalEvaporation OrganicSolventEvaporation Degreasing 111TrichloroethaneMethylChloroformConveyorizedVaporDegreaser",
    "40100223":
        "ChemicalEvaporation OrganicSolventEvaporation Degreasing PerchloroethyleneConveyorizedVaporDegreasing",
    "40100224":
        "ChemicalEvaporation OrganicSolventEvaporation Degreasing MethyleneChlorideConveyorizedVaporDegreasing",
    "40100225":
        "ChemicalEvaporation OrganicSolventEvaporation Degreasing TrichloroethyleneConveyorizedVaporDegreasing",
    "40100235":
        "ChemicalEvaporation OrganicSolventEvaporation Degreasing EntireUnitwithVaporizedSolventConveyorizedVaporDegreasing",
    "40100236":
        "ChemicalEvaporation OrganicSolventEvaporation Degreasing EntireUnitwithNonboilingSolventConveyorizedVaporDegreasing",
    "40100251":
        "ChemicalEvaporation OrganicSolventEvaporation Degreasing StoddardPetroleumSolventGeneralDegreasingUnits",
    "40100252":
        "ChemicalEvaporation OrganicSolventEvaporation Degreasing 111TrichloroethaneMethylChloroformGeneralDegreasingUnits",
    "40100253":
        "ChemicalEvaporation OrganicSolventEvaporation Degreasing PerchloroethyleneGeneralDegreasingUnits",
    "40100254":
        "ChemicalEvaporation OrganicSolventEvaporation Degreasing MethyleneChlorideGeneralDegreasingUnits",
    "40100255":
        "ChemicalEvaporation OrganicSolventEvaporation Degreasing TrichloroethyleneGeneralDegreasingUnits",
    "40100256":
        "ChemicalEvaporation OrganicSolventEvaporation Degreasing TolueneGeneralDegreasingUnits",
    "40100257":
        "ChemicalEvaporation OrganicSolventEvaporation Degreasing TrichlorotrifluoroethaneFreonGeneralDegreasingUnits",
    "40100258":
        "ChemicalEvaporation OrganicSolventEvaporation Degreasing TrichlorofluoromethaneGeneralDegreasingUnits",
    "40100295":
        "PetroleumandSolventEvaporation OrganicSolventEvaporation Degreasing OtherNotClassifiedGeneralDegreasingUnits",
    "40100296":
        "ChemicalEvaporation OrganicSolventEvaporation Degreasing OtherNotClassifiedGeneralDegreasingUnits",
    "40100298":
        "ChemicalEvaporation OrganicSolventEvaporation Degreasing OtherNotClassifiedConveyorizedVaporDegreasing",
    "40100299":
        "ChemicalEvaporation OrganicSolventEvaporation Degreasing OtherNotClassifiedOpentopVaporDegreasing",
    "40100301":
        "ChemicalEvaporation OrganicSolventEvaporation ColdSolventCleaningStripping Methanol",
    "40100302":
        "ChemicalEvaporation OrganicSolventEvaporation ColdSolventCleaningStripping MethyleneChloride",
    "40100303":
        "ChemicalEvaporation OrganicSolventEvaporation ColdSolventCleaningStripping StoddardPetroleumSolvent",
    "40100304":
        "ChemicalEvaporation OrganicSolventEvaporation ColdSolventCleaningStripping Perchloroethylene",
    "40100305":
        "ChemicalEvaporation OrganicSolventEvaporation ColdSolventCleaningStripping 111TrichloroethaneMethylChloroform",
    "40100306":
        "ChemicalEvaporation OrganicSolventEvaporation ColdSolventCleaningStripping Trichloroethylene",
    "40100307":
        "ChemicalEvaporation OrganicSolventEvaporation ColdSolventCleaningStripping IsopropylAlcohol",
    "40100308":
        "ChemicalEvaporation OrganicSolventEvaporation ColdSolventCleaningStripping MethylEthylKetone",
    "40100309":
        "ChemicalEvaporation OrganicSolventEvaporation ColdSolventCleaningStripping Freon",
    "40100310":
        "ChemicalEvaporation OrganicSolventEvaporation ColdSolventCleaningStripping Acetone",
    "40100311":
        "ChemicalEvaporation OrganicSolventEvaporation ColdSolventCleaningStripping GlycolEthers",
    "40100335":
        "ChemicalEvaporation OrganicSolventEvaporation ColdSolventCleaningStripping EntireUnit",
    "40100336":
        "ChemicalEvaporation OrganicSolventEvaporation ColdSolventCleaningStripping DegreaserEntireUnit",
    "40100398":
        "PetroleumandSolventEvaporation OrganicSolventEvaporation ColdSolventCleaningStripping OtherNotClassified",
    "40100399":
        "ChemicalEvaporation OrganicSolventEvaporation ColdSolventCleaningStripping OtherNotClassified",
    "40100401":
        "ChemicalEvaporation OrganicSolventEvaporation KnitFabricScouringwithChlorinatedSolvent Perchloroethylene",
    "40100499":
        "ChemicalEvaporation OrganicSolventEvaporation KnitFabricScouringwithChlorinatedSolvent OtherNotClassified",
    "40100501":
        "ChemicalEvaporation OrganicSolventEvaporation SolventStorage GeneralProcessesSpentSolventStorage",
    "40100550":
        "ChemicalEvaporation OrganicSolventEvaporation SolventStorage GeneralProcessesDrumStoragePureOrganicChemicals",
    "40188801":
        "PetroleumandSolventEvaporation OrganicSolventEvaporation FugitiveEmissions SpecifyinCommentsField",
    "40188805":
        "PetroleumandSolventEvaporation OrganicSolventEvaporation FugitiveEmissions SpecifyinCommentsField",
    "40188898":
        "ChemicalEvaporation OrganicSolventEvaporation FugitiveEmissions General",
    "40200101":
        "ChemicalEvaporation SurfaceCoatingOperations SurfaceCoatingApplicationGeneral PaintSolventbase",
    "40200110":
        "PetroleumandSolventEvaporation SurfaceCoatingOperations SurfaceCoatingApplicationGeneral PaintSolventbase",
    "40200201":
        "ChemicalEvaporation SurfaceCoatingOperations SurfaceCoatingApplicationGeneral PaintWaterbase",
    "40200210":
        "PetroleumandSolventEvaporation SurfaceCoatingOperations SurfaceCoatingApplicationGeneral PaintWaterbase",
    "40200301":
        "ChemicalEvaporation SurfaceCoatingOperations SurfaceCoatingApplicationGeneral VarnishShellac",
    "40200310":
        "PetroleumandSolventEvaporation SurfaceCoatingOperations SurfaceCoatingApplicationGeneral VarnishShellac",
    "40200401":
        "ChemicalEvaporation SurfaceCoatingOperations SurfaceCoatingApplicationGeneral Lacquer",
    "40200410":
        "PetroleumandSolventEvaporation SurfaceCoatingOperations SurfaceCoatingApplicationGeneral Lacquer",
    "40200501":
        "ChemicalEvaporation SurfaceCoatingOperations SurfaceCoatingApplicationGeneral Enamel",
    "40200510":
        "PetroleumandSolventEvaporation SurfaceCoatingOperations SurfaceCoatingApplicationGeneral Enamel",
    "40200601":
        "ChemicalEvaporation SurfaceCoatingOperations SurfaceCoatingApplicationGeneral Primer",
    "40200610":
        "PetroleumandSolventEvaporation SurfaceCoatingOperations SurfaceCoatingApplicationGeneral Primer",
    "40200701":
        "ChemicalEvaporation SurfaceCoatingOperations SurfaceCoatingApplicationGeneral AdhesiveApplication",
    "40200706":
        "ChemicalEvaporation SurfaceCoatingOperations SurfaceCoatingApplicationGeneral AdhesiveSolventMixing",
    "40200707":
        "ChemicalEvaporation SurfaceCoatingOperations SurfaceCoatingApplicationGeneral AdhesiveSolventStorage",
    "40200710":
        "ChemicalEvaporation SurfaceCoatingOperations SurfaceCoatingApplicationGeneral AdhesiveGeneral",
    "40200711":
        "ChemicalEvaporation SurfaceCoatingOperations SurfaceCoatingApplicationGeneral AdhesiveSpray",
    "40200712":
        "ChemicalEvaporation SurfaceCoatingOperations SurfaceCoatingApplicationGeneral AdhesiveRollon",
    "40200801":
        "ChemicalEvaporation SurfaceCoatingOperations CoatingOvenGeneral General",
    "40200802":
        "ChemicalEvaporation SurfaceCoatingOperations CoatingOvenGeneral Dried175F",
    "40200803":
        "ChemicalEvaporation SurfaceCoatingOperations CoatingOvenGeneral Baked175F",
    "40200810":
        "PetroleumandSolventEvaporation SurfaceCoatingOperations CoatingOvenGeneral General",
    "40200820":
        "ChemicalEvaporation SurfaceCoatingOperations CoatingOvenGeneral PrimeBaseCoatOven",
    "40200830":
        "ChemicalEvaporation SurfaceCoatingOperations CoatingOvenGeneral TopcoatOven",
    "40200840":
        "ChemicalEvaporation SurfaceCoatingOperations CoatingOvenGeneral TwoPieceCanCuringOvensGeneralIncludesCodes4142and43",
    "40200841":
        "ChemicalEvaporation SurfaceCoatingOperations CoatingOvenGeneral TwoPieceCanBaseCoatOven",
    "40200842":
        "ChemicalEvaporation SurfaceCoatingOperations CoatingOvenGeneral TwoPieceCanOverVarnishOven",
    "40200843":
        "ChemicalEvaporation SurfaceCoatingOperations CoatingOvenGeneral TwoPieceCanInteriorBodyCoatOven",
    "40200845":
        "ChemicalEvaporation SurfaceCoatingOperations CoatingOvenGeneral ThreePieceCanCuringOvensIncludesCodes464748and49",
    "40200848":
        "ChemicalEvaporation SurfaceCoatingOperations CoatingOvenGeneral ThreePieceCanSheetLithographicCoatingOven",
    "40200855":
        "ChemicalEvaporation SurfaceCoatingOperations CoatingOvenGeneral FillerOven",
    "40200856":
        "ChemicalEvaporation SurfaceCoatingOperations CoatingOvenGeneral SealerOven",
    "40200861":
        "ChemicalEvaporation SurfaceCoatingOperations CoatingOvenGeneral SingleCoatApplicationOven",
    "40200870":
        "ChemicalEvaporation SurfaceCoatingOperations CoatingOvenGeneral ColorCoatOven",
    "40200871":
        "ChemicalEvaporation SurfaceCoatingOperations CoatingOvenGeneral TopcoatTextureCoatOven",
    "40200899":
        "PetroleumandSolventEvaporation SurfaceCoatingOperations CoatingOvenGeneral SeeComment",
    "40200901":
        "ChemicalEvaporation SurfaceCoatingOperations ThinningSolventsGeneral General",
    "40200902":
        "ChemicalEvaporation SurfaceCoatingOperations ThinningSolventsGeneral Acetone",
    "40200903":
        "ChemicalEvaporation SurfaceCoatingOperations ThinningSolventsGeneral ButylAcetate",
    "40200904":
        "ChemicalEvaporation SurfaceCoatingOperations ThinningSolventsGeneral ButylAlcohol",
    "40200906":
        "ChemicalEvaporation SurfaceCoatingOperations ThinningSolventsGeneral Cellosolve",
    "40200907":
        "ChemicalEvaporation SurfaceCoatingOperations ThinningSolventsGeneral CellosolveAcetate",
    "40200908":
        "ChemicalEvaporation SurfaceCoatingOperations ThinningSolventsGeneral DimethylFormamide",
    "40200909":
        "ChemicalEvaporation SurfaceCoatingOperations ThinningSolventsGeneral EthylAcetate",
    "40200910":
        "ChemicalEvaporation SurfaceCoatingOperations ThinningSolventsGeneral EthylAlcohol",
    "40200911":
        "ChemicalEvaporation SurfaceCoatingOperations ThinningSolventsGeneral Gasoline",
    "40200912":
        "ChemicalEvaporation SurfaceCoatingOperations ThinningSolventsGeneral IsopropylAlcohol",
    "40200913":
        "ChemicalEvaporation SurfaceCoatingOperations ThinningSolventsGeneral IsopropylAcetate",
    "40200914":
        "ChemicalEvaporation SurfaceCoatingOperations ThinningSolventsGeneral Kerosene",
    "40200915":
        "ChemicalEvaporation SurfaceCoatingOperations ThinningSolventsGeneral LactolSpirits",
    "40200916":
        "ChemicalEvaporation SurfaceCoatingOperations ThinningSolventsGeneral MethylAcetate",
    "40200917":
        "ChemicalEvaporation SurfaceCoatingOperations ThinningSolventsGeneral MethylAlcohol",
    "40200918":
        "ChemicalEvaporation SurfaceCoatingOperations ThinningSolventsGeneral MethylEthylKetone",
    "40200919":
        "ChemicalEvaporation SurfaceCoatingOperations ThinningSolventsGeneral MethylIsobutylKetone",
    "40200920":
        "ChemicalEvaporation SurfaceCoatingOperations ThinningSolventsGeneral MineralSpirits",
    "40200921":
        "ChemicalEvaporation SurfaceCoatingOperations ThinningSolventsGeneral Naphtha",
    "40200922":
        "ChemicalEvaporation SurfaceCoatingOperations ThinningSolventsGeneral Toluene",
    "40200923":
        "ChemicalEvaporation SurfaceCoatingOperations ThinningSolventsGeneral Varsol",
    "40200924":
        "ChemicalEvaporation SurfaceCoatingOperations ThinningSolventsGeneral Xylene",
    "40200926":
        "ChemicalEvaporation SurfaceCoatingOperations ThinningSolventsGeneral Turpentine",
    "40200927":
        "ChemicalEvaporation SurfaceCoatingOperations ThinningSolventsGeneral HexyleneGlycol",
    "40200929":
        "ChemicalEvaporation SurfaceCoatingOperations ThinningSolventsGeneral 111TrichloroethaneMethylChloroform",
    "40200930":
        "ChemicalEvaporation SurfaceCoatingOperations ThinningSolventsGeneral MethyleneChloride",
    "40200931":
        "ChemicalEvaporation SurfaceCoatingOperations ThinningSolventsGeneral Perchloroethylene",
    "40200998":
        "PetroleumandSolventEvaporation SurfaceCoatingOperations ThinningSolventsGeneral GeneralSpecifyinComments",
    "40201001":
        "ChemicalEvaporation SurfaceCoatingOperations CoatingOvenHeater NaturalGas",
    "40201002":
        "ChemicalEvaporation SurfaceCoatingOperations CoatingOvenHeater DistillateOil",
    "40201004":
        "ChemicalEvaporation SurfaceCoatingOperations CoatingOvenHeater LiquifiedPetroleumGasLPG",
    "40201101":
        "ChemicalEvaporation SurfaceCoatingOperations FabricCoatingPrinting CoatingOperationAlsoSeeSpecificCoatingMethodCodes40204X",
    "40201103":
        "ChemicalEvaporation SurfaceCoatingOperations FabricCoatingPrinting CoatingMixingAlsoSeeSpecificCoatingMethodCodes40204X",
    "40201104":
        "ChemicalEvaporation SurfaceCoatingOperations FabricCoatingPrinting CoatingStorageAlsoSeeSpecificCoatingMethodCodes40204X",
    "40201105":
        "ChemicalEvaporation SurfaceCoatingOperations FabricCoatingPrinting EquipmentCleanupFabricCoatingAlsoSpecCoatMethodCodes40204X",
    "40201112":
        "ChemicalEvaporation SurfaceCoatingOperations FabricCoatingPrinting FabricPrintingRollerAlsoSeeNewCodesUnder402040XX",
    "40201114":
        "ChemicalEvaporation SurfaceCoatingOperations FabricCoatingPrinting FabricPrintingRotaryScreenAlsoSeeNewCodesUnder402040XX",
    "40201115":
        "PetroleumandSolventEvaporation SurfaceCoatingOperations FabricCoatingPrinting FabricPrintingFlatScreenAlsoSeeNewCodesUnder402040XX",
    "40201116":
        "ChemicalEvaporation SurfaceCoatingOperations FabricCoatingPrinting FabricPrintingFlatScreenAlsoSeeNewCodesUnder402040XX",
    "40201121":
        "ChemicalEvaporation SurfaceCoatingOperations FabricCoatingPrinting FabricPrintDryerSteamCoilAlsoSeeNewCodesUnder402040XX",
    "40201122":
        "ChemicalEvaporation SurfaceCoatingOperations FabricCoatingPrinting FabricPrintDryerFuelfiredAlsoSeeNewCodesUnder402040XX",
    "40201197":
        "ChemicalEvaporation SurfaceCoatingOperations FabricCoatingPrinting Misc.FugitivesAlsoNewCodes402040XX",
    "40201199":
        "ChemicalEvaporation SurfaceCoatingOperations FabricCoatingPrinting OtherNotClassifiedAlsoSeeNewCodesUnder402040XX",
    "40201201":
        "ChemicalEvaporation SurfaceCoatingOperations FabricDyeing DyeApplicationGeneralAlsoSeeNewCodesUnder402060XX",
    "40201301":
        "ChemicalEvaporation SurfaceCoatingOperations PaperCoating CoatingOperation",
    "40201303":
        "ChemicalEvaporation SurfaceCoatingOperations PaperCoating CoatingMixing",
    "40201304":
        "ChemicalEvaporation SurfaceCoatingOperations PaperCoating CoatingStorage",
    "40201305":
        "ChemicalEvaporation SurfaceCoatingOperations PaperCoating EquipmentCleanup",
    "40201310":
        "ChemicalEvaporation SurfaceCoatingOperations PaperCoating CoatingApplicationKnifeCoater",
    "40201320":
        "ChemicalEvaporation SurfaceCoatingOperations PaperCoating CoatingApplicationReverseRollCoater",
    "40201330":
        "ChemicalEvaporation SurfaceCoatingOperations PaperCoating CoatingApplicationRotogravurePrinter",
    "40201399":
        "ChemicalEvaporation SurfaceCoatingOperations PaperCoating OtherNotClassified",
    "40201401":
        "ChemicalEvaporation SurfaceCoatingOperations LargeAppliances PrimeCoatingOperation",
    "40201402":
        "ChemicalEvaporation SurfaceCoatingOperations LargeAppliances CleaningPretreatment",
    "40201403":
        "ChemicalEvaporation SurfaceCoatingOperations LargeAppliances CoatingMixing",
    "40201404":
        "ChemicalEvaporation SurfaceCoatingOperations LargeAppliances CoatingStorage",
    "40201405":
        "ChemicalEvaporation SurfaceCoatingOperations LargeAppliances EquipmentCleanup",
    "40201406":
        "ChemicalEvaporation SurfaceCoatingOperations LargeAppliances TopcoatSpray",
    "40201410":
        "ChemicalEvaporation SurfaceCoatingOperations LargeAppliances PrimeCoatFlashoff",
    "40201411":
        "ChemicalEvaporation SurfaceCoatingOperations LargeAppliances TopcoatFlashoff",
    "40201431":
        "ChemicalEvaporation SurfaceCoatingOperations LargeAppliances CoatingLineGeneral",
    "40201432":
        "ChemicalEvaporation SurfaceCoatingOperations LargeAppliances PrimeAirSpray",
    "40201433":
        "ChemicalEvaporation SurfaceCoatingOperations LargeAppliances PrimeElectrostaticSpray",
    "40201434":
        "ChemicalEvaporation SurfaceCoatingOperations LargeAppliances PrimeFlowCoat",
    "40201435":
        "ChemicalEvaporation SurfaceCoatingOperations LargeAppliances PrimeDipCoat",
    "40201436":
        "ChemicalEvaporation SurfaceCoatingOperations LargeAppliances PrimeElectrodeposition",
    "40201437":
        "ChemicalEvaporation SurfaceCoatingOperations LargeAppliances TopAirSpray",
    "40201438":
        "ChemicalEvaporation SurfaceCoatingOperations LargeAppliances TopElectrostaticSpray",
    "40201499":
        "ChemicalEvaporation SurfaceCoatingOperations LargeAppliances OtherNotClassified",
    "40201501":
        "ChemicalEvaporation SurfaceCoatingOperations MagnetWireSurfaceCoating CoatingApplicationCuring",
    "40201502":
        "ChemicalEvaporation SurfaceCoatingOperations MagnetWireSurfaceCoating CleaningPretreatment",
    "40201503":
        "ChemicalEvaporation SurfaceCoatingOperations MagnetWireSurfaceCoating CoatingMixing",
    "40201504":
        "ChemicalEvaporation SurfaceCoatingOperations MagnetWireSurfaceCoating CoatingStorage",
    "40201505":
        "ChemicalEvaporation SurfaceCoatingOperations MagnetWireSurfaceCoating EquipmentCleanup",
    "40201531":
        "ChemicalEvaporation SurfaceCoatingOperations MagnetWireSurfaceCoating CoatingLineGeneral",
    "40201599":
        "ChemicalEvaporation SurfaceCoatingOperations MagnetWireSurfaceCoating OtherNotClassified",
    "40201601":
        "ChemicalEvaporation SurfaceCoatingOperations AutomobilesandLightTrucks PrimeApplicationElectodepositionDipSpray",
    "40201602":
        "ChemicalEvaporation SurfaceCoatingOperations AutomobilesandLightTrucks CleaningPretreatment",
    "40201603":
        "ChemicalEvaporation SurfaceCoatingOperations AutomobilesandLightTrucks CoatingMixing",
    "40201604":
        "ChemicalEvaporation SurfaceCoatingOperations AutomobilesandLightTrucks CoatingStorage",
    "40201605":
        "ChemicalEvaporation SurfaceCoatingOperations AutomobilesandLightTrucks EquipmentCleanup",
    "40201606":
        "ChemicalEvaporation SurfaceCoatingOperations AutomobilesandLightTrucks TopcoatOperation",
    "40201607":
        "ChemicalEvaporation SurfaceCoatingOperations AutomobilesandLightTrucks Sealers",
    "40201608":
        "ChemicalEvaporation SurfaceCoatingOperations AutomobilesandLightTrucks Deadeners",
    "40201609":
        "ChemicalEvaporation SurfaceCoatingOperations AutomobilesandLightTrucks AnticorrosionPriming",
    "40201619":
        "ChemicalEvaporation SurfaceCoatingOperations AutomobilesandLightTrucks PrimeSurfacingOperation",
    "40201620":
        "ChemicalEvaporation SurfaceCoatingOperations AutomobilesandLightTrucks RepairTopcoatApplicationArea",
    "40201621":
        "ChemicalEvaporation SurfaceCoatingOperations AutomobilesandLightTrucks PrimeCoatingSolventborneAutomobiles",
    "40201622":
        "ChemicalEvaporation SurfaceCoatingOperations AutomobilesandLightTrucks PrimeCoatingElectrodepositionAutomobiles",
    "40201623":
        "ChemicalEvaporation SurfaceCoatingOperations AutomobilesandLightTrucks GuideCoatingSolventborneAutomobiles",
    "40201624":
        "ChemicalEvaporation SurfaceCoatingOperations AutomobilesandLightTrucks GuideCoatingWaterborneAutomobiles",
    "40201625":
        "ChemicalEvaporation SurfaceCoatingOperations AutomobilesandLightTrucks TopcoatSolventborneAutomobiles",
    "40201626":
        "ChemicalEvaporation SurfaceCoatingOperations AutomobilesandLightTrucks TopcoatWaterborneAutomobiles",
    "40201627":
        "ChemicalEvaporation SurfaceCoatingOperations AutomobilesandLightTrucks PrimeCoatingSolventborneLightTrucks",
    "40201628":
        "ChemicalEvaporation SurfaceCoatingOperations AutomobilesandLightTrucks PrimeCoatingElectrodepositionLightTrucks",
    "40201629":
        "ChemicalEvaporation SurfaceCoatingOperations AutomobilesandLightTrucks GuideCoatingSolventborneLightTrucks",
    "40201630":
        "ChemicalEvaporation SurfaceCoatingOperations AutomobilesandLightTrucks GuideCoatingWaterborneLightTrucks",
    "40201631":
        "ChemicalEvaporation SurfaceCoatingOperations AutomobilesandLightTrucks TopcoatSolventborneLightTrucks",
    "40201632":
        "ChemicalEvaporation SurfaceCoatingOperations AutomobilesandLightTrucks TopcoatWaterborneLightTrucks",
    "40201699":
        "ChemicalEvaporation SurfaceCoatingOperations AutomobilesandLightTrucks OtherNotClassified",
    "40201702":
        "ChemicalEvaporation SurfaceCoatingOperations MetalCanCoating CleaningPretreatment",
    "40201703":
        "ChemicalEvaporation SurfaceCoatingOperations MetalCanCoating CoatingMixing",
    "40201704":
        "ChemicalEvaporation SurfaceCoatingOperations MetalCanCoating CoatingStorage",
    "40201705":
        "ChemicalEvaporation SurfaceCoatingOperations MetalCanCoating EquipmentCleanup",
    "40201706":
        "ChemicalEvaporation SurfaceCoatingOperations MetalCanCoating SolventStorage",
    "40201721":
        "ChemicalEvaporation SurfaceCoatingOperations MetalCanCoating TwoPieceExteriorBaseCoating",
    "40201722":
        "ChemicalEvaporation SurfaceCoatingOperations MetalCanCoating InteriorSprayCoating",
    "40201723":
        "ChemicalEvaporation SurfaceCoatingOperations MetalCanCoating SheetBaseCoatingInterior",
    "40201724":
        "ChemicalEvaporation SurfaceCoatingOperations MetalCanCoating SheetBaseCoatingExterior",
    "40201725":
        "ChemicalEvaporation SurfaceCoatingOperations MetalCanCoating SideSeamSprayCoating",
    "40201726":
        "ChemicalEvaporation SurfaceCoatingOperations MetalCanCoating EndSealingCompoundAlsoSee40201736&37",
    "40201727":
        "ChemicalEvaporation SurfaceCoatingOperations MetalCanCoating Lithography",
    "40201728":
        "ChemicalEvaporation SurfaceCoatingOperations MetalCanCoating OverVarnish",
    "40201729":
        "ChemicalEvaporation SurfaceCoatingOperations MetalCanCoating ExteriorEndCoating",
    "40201731":
        "ChemicalEvaporation SurfaceCoatingOperations MetalCanCoating ThreepieceCanSheetBaseCoating",
    "40201732":
        "ChemicalEvaporation SurfaceCoatingOperations MetalCanCoating ThreepieceCanSheetLithographicCoatingLine",
    "40201733":
        "ChemicalEvaporation SurfaceCoatingOperations MetalCanCoating ThreepieceCansideSeamSprayCoating",
    "40201734":
        "ChemicalEvaporation SurfaceCoatingOperations MetalCanCoating ThreepieceCanInteriorBodySprayCoat",
    "40201735":
        "ChemicalEvaporation SurfaceCoatingOperations MetalCanCoating TwopieceCanCoatingLine",
    "40201736":
        "ChemicalEvaporation SurfaceCoatingOperations MetalCanCoating TwopieceCanEndSealingCompound",
    "40201737":
        "ChemicalEvaporation SurfaceCoatingOperations MetalCanCoating ThreePieceCanEndSealingCompound",
    "40201738":
        "ChemicalEvaporation SurfaceCoatingOperations MetalCanCoating TwoPieceCanLithographicCoatingLine",
    "40201739":
        "ChemicalEvaporation SurfaceCoatingOperations MetalCanCoating ThreePieceCanCoatingLineAllCoatingSolventEmissionPoints",
    "40201799":
        "ChemicalEvaporation SurfaceCoatingOperations MetalCanCoating OtherNotClassified",
    "40201801":
        "ChemicalEvaporation SurfaceCoatingOperations MetalCoilCoating PrimeCoatingApplication",
    "40201802":
        "ChemicalEvaporation SurfaceCoatingOperations MetalCoilCoating CleaningPretreatment",
    "40201803":
        "ChemicalEvaporation SurfaceCoatingOperations MetalCoilCoating SolventMixing",
    "40201804":
        "ChemicalEvaporation SurfaceCoatingOperations MetalCoilCoating SolventStorageUse40700401thru40799998ifpossible",
    "40201805":
        "ChemicalEvaporation SurfaceCoatingOperations MetalCoilCoating EquipmentCleanup",
    "40201806":
        "ChemicalEvaporation SurfaceCoatingOperations MetalCoilCoating FinishCoating",
    "40201807":
        "ChemicalEvaporation SurfaceCoatingOperations MetalCoilCoating CoatingStorage",
    "40201899":
        "ChemicalEvaporation SurfaceCoatingOperations MetalCoilCoating OtherNotClassified",
    "40201901":
        "ChemicalEvaporation SurfaceCoatingOperations WoodFurnitureSurfaceCoating CoatingOperation",
    "40201903":
        "ChemicalEvaporation SurfaceCoatingOperations WoodFurnitureSurfaceCoating CoatingMixing",
    "40201904":
        "ChemicalEvaporation SurfaceCoatingOperations WoodFurnitureSurfaceCoating CoatingStorage",
    "40201999":
        "ChemicalEvaporation SurfaceCoatingOperations WoodFurnitureSurfaceCoating OtherNotClassified",
    "40202001":
        "ChemicalEvaporation SurfaceCoatingOperations MetalFurnitureOperations CoatingOperation",
    "40202002":
        "ChemicalEvaporation SurfaceCoatingOperations MetalFurnitureOperations CleaningPretreatment",
    "40202003":
        "ChemicalEvaporation SurfaceCoatingOperations MetalFurnitureOperations CoatingMixing",
    "40202004":
        "ChemicalEvaporation SurfaceCoatingOperations MetalFurnitureOperations CoatingStorage",
    "40202005":
        "ChemicalEvaporation SurfaceCoatingOperations MetalFurnitureOperations EquipmentCleanup",
    "40202010":
        "ChemicalEvaporation SurfaceCoatingOperations MetalFurnitureOperations PrimeCoatApplication",
    "40202013":
        "ChemicalEvaporation SurfaceCoatingOperations MetalFurnitureOperations PrimeCoatApplicationDip",
    "40202020":
        "ChemicalEvaporation SurfaceCoatingOperations MetalFurnitureOperations TopcoatApplication",
    "40202022":
        "ChemicalEvaporation SurfaceCoatingOperations MetalFurnitureOperations TopcoatApplicationSprayWaterborne",
    "40202024":
        "ChemicalEvaporation SurfaceCoatingOperations MetalFurnitureOperations TopcoatApplicationFlowCoat",
    "40202031":
        "ChemicalEvaporation SurfaceCoatingOperations MetalFurnitureOperations SingleSprayLineGeneral",
    "40202032":
        "ChemicalEvaporation SurfaceCoatingOperations MetalFurnitureOperations SprayDipLineGeneralUse40202037",
    "40202033":
        "ChemicalEvaporation SurfaceCoatingOperations MetalFurnitureOperations SprayHighSolidsCoatingUse40202035",
    "40202034":
        "ChemicalEvaporation SurfaceCoatingOperations MetalFurnitureOperations SprayWaterborneCoatingUse40202036",
    "40202035":
        "ChemicalEvaporation SurfaceCoatingOperations MetalFurnitureOperations SingleCoatApplicationSprayHighSolids",
    "40202037":
        "ChemicalEvaporation SurfaceCoatingOperations MetalFurnitureOperations SingleCoatApplicationDip",
    "40202039":
        "ChemicalEvaporation SurfaceCoatingOperations MetalFurnitureOperations SingleCoatApplicationFlashoff",
    "40202099":
        "ChemicalEvaporation SurfaceCoatingOperations MetalFurnitureOperations OtherNotClassified",
    "40202101":
        "ChemicalEvaporation SurfaceCoatingOperations FlatwoodWoodBuildingProducts BaseCoat",
    "40202103":
        "ChemicalEvaporation SurfaceCoatingOperations FlatwoodWoodBuildingProducts CoatingMixing",
    "40202104":
        "ChemicalEvaporation SurfaceCoatingOperations FlatwoodWoodBuildingProducts CoatingStorage",
    "40202105":
        "ChemicalEvaporation SurfaceCoatingOperations FlatwoodWoodBuildingProducts EquipmentCleanup",
    "40202106":
        "ChemicalEvaporation SurfaceCoatingOperations FlatwoodWoodBuildingProducts Topcoat",
    "40202107":
        "ChemicalEvaporation SurfaceCoatingOperations FlatwoodWoodBuildingProducts Filler",
    "40202108":
        "ChemicalEvaporation SurfaceCoatingOperations FlatwoodWoodBuildingProducts Sealer",
    "40202109":
        "ChemicalEvaporation SurfaceCoatingOperations FlatwoodWoodBuildingProducts Inks",
    "40202110":
        "ChemicalEvaporation SurfaceCoatingOperations FlatwoodWoodBuildingProducts GroveCoatApplication",
    "40202111":
        "ChemicalEvaporation SurfaceCoatingOperations FlatwoodWoodBuildingProducts StainApplication",
    "40202117":
        "ChemicalEvaporation SurfaceCoatingOperations FlatwoodWoodBuildingProducts FillerSander",
    "40202118":
        "ChemicalEvaporation SurfaceCoatingOperations FlatwoodWoodBuildingProducts SealerSander",
    "40202131":
        "ChemicalEvaporation SurfaceCoatingOperations FlatwoodWoodBuildingProducts WaterborneCoating",
    "40202132":
        "ChemicalEvaporation SurfaceCoatingOperations FlatwoodWoodBuildingProducts SolventborneCoating",
    "40202133":
        "ChemicalEvaporation SurfaceCoatingOperations FlatwoodWoodBuildingProducts UltravioletCoating",
    "40202140":
        "ChemicalEvaporation SurfaceCoatingOperations FlatwoodWoodBuildingProducts SurfacePreparationIncludesTemperingSandingBrushingGroveCut",
    "40202199":
        "ChemicalEvaporation SurfaceCoatingOperations FlatwoodWoodBuildingProducts OtherNotElsewhereClassified",
    "40202201":
        "ChemicalEvaporation SurfaceCoatingOperations PlasticParts CoatingOperation",
    "40202202":
        "ChemicalEvaporation SurfaceCoatingOperations PlasticParts CleaningPretreatment",
    "40202203":
        "ChemicalEvaporation SurfaceCoatingOperations PlasticParts CoatingMixing",
    "40202204":
        "ChemicalEvaporation SurfaceCoatingOperations PlasticParts CoatingStorage",
    "40202205":
        "ChemicalEvaporation SurfaceCoatingOperations PlasticParts EquipmentCleanup",
    "40202206":
        "ChemicalEvaporation SurfaceCoatingOperations PlasticParts BusinessBaselineCoatingMix",
    "40202207":
        "ChemicalEvaporation SurfaceCoatingOperations PlasticParts BusinessLowSolidsSolventborneCoating",
    "40202211":
        "ChemicalEvaporation SurfaceCoatingOperations PlasticParts BusinessWaterborneCoating",
    "40202213":
        "ChemicalEvaporation SurfaceCoatingOperations PlasticParts BusinessHigherSolidsSolventborneEMIRFIShieldingCoating",
    "40202220":
        "ChemicalEvaporation SurfaceCoatingOperations PlasticParts PrimeCoatApplication",
    "40202229":
        "ChemicalEvaporation SurfaceCoatingOperations PlasticParts PrimeCoatFlashoff",
    "40202230":
        "ChemicalEvaporation SurfaceCoatingOperations PlasticParts ColorCoatApplication",
    "40202239":
        "ChemicalEvaporation SurfaceCoatingOperations PlasticParts ColorCoatFlashoff",
    "40202240":
        "ChemicalEvaporation SurfaceCoatingOperations PlasticParts TopcoatTextureCoatApplication",
    "40202249":
        "ChemicalEvaporation SurfaceCoatingOperations PlasticParts TopcoatTextureCoatFlashoff",
    "40202270":
        "ChemicalEvaporation SurfaceCoatingOperations PlasticParts SandingGritBlastingPriortoEMIRFIShieldingCoatApplication",
    "40202280":
        "ChemicalEvaporation SurfaceCoatingOperations PlasticParts MaskantApplication",
    "40202299":
        "ChemicalEvaporation SurfaceCoatingOperations PlasticParts OtherNotClassified",
    "40202301":
        "ChemicalEvaporation SurfaceCoatingOperations LargeShips PrimeCoatingOperation",
    "40202302":
        "ChemicalEvaporation SurfaceCoatingOperations LargeShips CleaningPretreatment",
    "40202303":
        "ChemicalEvaporation SurfaceCoatingOperations LargeShips CoatingMixing",
    "40202304":
        "ChemicalEvaporation SurfaceCoatingOperations LargeShips CoatingStorage",
    "40202305":
        "ChemicalEvaporation SurfaceCoatingOperations LargeShips EquipmentCleanup",
    "40202306":
        "ChemicalEvaporation SurfaceCoatingOperations LargeShips TopcoatOperation",
    "40202399":
        "ChemicalEvaporation SurfaceCoatingOperations LargeShips OtherNotClassified",
    "40202401":
        "ChemicalEvaporation SurfaceCoatingOperations Aerospace PrimerApplication",
    "40202402":
        "ChemicalEvaporation SurfaceCoatingOperations Aerospace CleaningPretreatment",
    "40202403":
        "ChemicalEvaporation SurfaceCoatingOperations Aerospace CoatingMixing",
    "40202404":
        "ChemicalEvaporation SurfaceCoatingOperations Aerospace CoatingStorage",
    "40202405":
        "ChemicalEvaporation SurfaceCoatingOperations Aerospace EquipmentCleanup",
    "40202406":
        "ChemicalEvaporation SurfaceCoatingOperations Aerospace TopcoatApplication",
    "40202407":
        "ChemicalEvaporation SurfaceCoatingOperations Aerospace SpecialtyCoatingApplication",
    "40202409":
        "ChemicalEvaporation SurfaceCoatingOperations Aerospace ChemicalMilling",
    "40202411":
        "ChemicalEvaporation SurfaceCoatingOperations Aerospace ChemicalDepainting",
    "40202499":
        "ChemicalEvaporation SurfaceCoatingOperations Aerospace LargeAircraftOtherNotClassified",
    "40202501":
        "ChemicalEvaporation SurfaceCoatingOperations MiscellaneousMetalParts CoatingOperation",
    "40202502":
        "ChemicalEvaporation SurfaceCoatingOperations MiscellaneousMetalParts CleaningPretreatment",
    "40202503":
        "ChemicalEvaporation SurfaceCoatingOperations MiscellaneousMetalParts CoatingMixing",
    "40202504":
        "ChemicalEvaporation SurfaceCoatingOperations MiscellaneousMetalParts CoatingStorage",
    "40202505":
        "ChemicalEvaporation SurfaceCoatingOperations MiscellaneousMetalParts EquipmentCleanup",
    "40202510":
        "ChemicalEvaporation SurfaceCoatingOperations MiscellaneousMetalParts PrimeCoatApplication",
    "40202511":
        "ChemicalEvaporation SurfaceCoatingOperations MiscellaneousMetalParts PrimeCoatApplicationSprayHighSolids",
    "40202512":
        "ChemicalEvaporation SurfaceCoatingOperations MiscellaneousMetalParts PrimeCoatApplicationSprayWaterborne",
    "40202515":
        "ChemicalEvaporation SurfaceCoatingOperations MiscellaneousMetalParts PrimeCoatApplicationFlashoff",
    "40202520":
        "ChemicalEvaporation SurfaceCoatingOperations MiscellaneousMetalParts TopcoatApplication",
    "40202521":
        "ChemicalEvaporation SurfaceCoatingOperations MiscellaneousMetalParts TopcoatApplicationSprayHighSolids",
    "40202522":
        "ChemicalEvaporation SurfaceCoatingOperations MiscellaneousMetalParts TopcoatApplicationSprayWaterborne",
    "40202523":
        "ChemicalEvaporation SurfaceCoatingOperations MiscellaneousMetalParts TopcoatApplicationDip",
    "40202525":
        "ChemicalEvaporation SurfaceCoatingOperations MiscellaneousMetalParts TopcoatApplicationFlashoff",
    "40202531":
        "ChemicalEvaporation SurfaceCoatingOperations MiscellaneousMetalParts ConveyorSingleFlow",
    "40202532":
        "ChemicalEvaporation SurfaceCoatingOperations MiscellaneousMetalParts ConveyorSingleDip",
    "40202533":
        "ChemicalEvaporation SurfaceCoatingOperations MiscellaneousMetalParts ConveyorSingleSpray",
    "40202534":
        "ChemicalEvaporation SurfaceCoatingOperations MiscellaneousMetalParts ConveyorTwoCoatFlowandSpray",
    "40202535":
        "ChemicalEvaporation SurfaceCoatingOperations MiscellaneousMetalParts ConveyorTwoCoatDipandSpray",
    "40202536":
        "ChemicalEvaporation SurfaceCoatingOperations MiscellaneousMetalParts ConveyorTwoCoatSpray",
    "40202537":
        "ChemicalEvaporation SurfaceCoatingOperations MiscellaneousMetalParts ManualTwoCoatSprayandAirDry",
    "40202542":
        "ChemicalEvaporation SurfaceCoatingOperations MiscellaneousMetalParts SingleCoatApplicationSprayHighSolids",
    "40202543":
        "ChemicalEvaporation SurfaceCoatingOperations MiscellaneousMetalParts SingleCoatApplicationSprayWaterborne",
    "40202544":
        "ChemicalEvaporation SurfaceCoatingOperations MiscellaneousMetalParts SingleCoatApplicationDip",
    "40202545":
        "ChemicalEvaporation SurfaceCoatingOperations MiscellaneousMetalParts SingleCoatApplicationFlowCoat",
    "40202546":
        "ChemicalEvaporation SurfaceCoatingOperations MiscellaneousMetalParts SingleCoatApplicationFlashoff",
    "40202599":
        "ChemicalEvaporation SurfaceCoatingOperations MiscellaneousMetalParts OtherNotClassified",
    "40202601":
        "ChemicalEvaporation SurfaceCoatingOperations SteelDrums CoatingOperation",
    "40202602":
        "ChemicalEvaporation SurfaceCoatingOperations SteelDrums CleaningPretreatment",
    "40202603":
        "ChemicalEvaporation SurfaceCoatingOperations SteelDrums CoatingMixing",
    "40202604":
        "ChemicalEvaporation SurfaceCoatingOperations SteelDrums CoatingStorage",
    "40202605":
        "ChemicalEvaporation SurfaceCoatingOperations SteelDrums EquipmentCleanup",
    "40202606":
        "ChemicalEvaporation SurfaceCoatingOperations SteelDrums InteriorCoating",
    "40202607":
        "ChemicalEvaporation SurfaceCoatingOperations SteelDrums ExteriorCoating",
    "40202699":
        "ChemicalEvaporation SurfaceCoatingOperations SteelDrums OtherNotClassified",
    "40202701":
        "ChemicalEvaporation SurfaceCoatingOperations GlassMirrors MirrorBackingCoatingOperation",
    "40202710":
        "PetroleumandSolventEvaporation SurfaceCoatingOperations GlassMirrors MirrorBackingCoatingOperation",
    "40202801":
        "ChemicalEvaporation SurfaceCoatingOperations GlassOpticalFibers ChemicalVaporDepositionofPreforms",
    "40202802":
        "ChemicalEvaporation SurfaceCoatingOperations GlassOpticalFibers PlasmaOvercladding",
    "40202899":
        "ChemicalEvaporation SurfaceCoatingOperations GlassOpticalFibers Miscellaneous",
    "40203001":
        "ChemicalEvaporation SurfaceCoatingOperations Semiconductors Solvent",
    "40204002":
        "ChemicalEvaporation SurfaceCoatingOperations FabricPrinting RollerApplication",
    "40204004":
        "ChemicalEvaporation SurfaceCoatingOperations FabricPrinting RollerSteamCansDrying",
    "40204011":
        "ChemicalEvaporation SurfaceCoatingOperations FabricPrinting RotaryScreenApplication",
    "40204013":
        "ChemicalEvaporation SurfaceCoatingOperations FabricPrinting RotaryScreenDryingCuring",
    "40204020":
        "ChemicalEvaporation SurfaceCoatingOperations FabricPrinting FlatScreenPrintPaste",
    "40204021":
        "ChemicalEvaporation SurfaceCoatingOperations FabricPrinting FlatScreenApplication",
    "40204022":
        "ChemicalEvaporation SurfaceCoatingOperations FabricPrinting FlatScreenTransfer",
    "40204121":
        "ChemicalEvaporation SurfaceCoatingOperations FabricCoatingKnifeCoating MixingTanks",
    "40204130":
        "ChemicalEvaporation SurfaceCoatingOperations FabricCoatingKnifeCoating CoatingApplication",
    "40204140":
        "ChemicalEvaporation SurfaceCoatingOperations FabricCoatingKnifeCoating DryingCuring",
    "40204230":
        "ChemicalEvaporation SurfaceCoatingOperations FabricCoatingRollerCoating CoatingApplication",
    "40204240":
        "ChemicalEvaporation SurfaceCoatingOperations FabricCoatingRollerCoating DryingCuring",
    "40204321":
        "ChemicalEvaporation SurfaceCoatingOperations FabricCoatingDipCoating MixingTanks",
    "40204330":
        "ChemicalEvaporation SurfaceCoatingOperations FabricCoatingDipCoating CoatingApplication",
    "40204340":
        "ChemicalEvaporation SurfaceCoatingOperations FabricCoatingDipCoating DryingCuring",
    "40204421":
        "ChemicalEvaporation SurfaceCoatingOperations FabricCoatingTransferCoating MixingTanks",
    "40204430":
        "ChemicalEvaporation SurfaceCoatingOperations FabricCoatingTransferCoating CoatingApplication",
    "40204435":
        "ChemicalEvaporation SurfaceCoatingOperations FabricCoatingTransferCoating LaminationLaminatingDevice",
    "40204440":
        "ChemicalEvaporation SurfaceCoatingOperations FabricCoatingTransferCoating DryingCuring",
    "40204442":
        "ChemicalEvaporation SurfaceCoatingOperations FabricCoatingTransferCoating DryingCuringSecondPredrier",
    "40204455":
        "ChemicalEvaporation SurfaceCoatingOperations FabricCoatingTransferCoating Winding",
    "40204471":
        "ChemicalEvaporation SurfaceCoatingOperations FabricCoatingTransferCoating WasteCleaningRags",
    "40204530":
        "ChemicalEvaporation SurfaceCoatingOperations FabricCoatingExtrusionCoating CoatingApplication",
    "40204531":
        "ChemicalEvaporation SurfaceCoatingOperations FabricCoatingExtrusionCoating CoatingApplicationExtruder",
    "40204532":
        "ChemicalEvaporation SurfaceCoatingOperations FabricCoatingExtrusionCoating CoatingApplicationCoatingDie",
    "40204561":
        "ChemicalEvaporation SurfaceCoatingOperations FabricCoatingExtrusionCoating CleanupCoatingApplicationEquipment",
    "40204630":
        "ChemicalEvaporation SurfaceCoatingOperations FabricCoatingMeltRollCoating CoatingApplication",
    "40204730":
        "ChemicalEvaporation SurfaceCoatingOperations FabricCoatingCoagulationCoating CoatingApplication",
    "40204740":
        "ChemicalEvaporation SurfaceCoatingOperations FabricCoatingCoagulationCoating SolventRecovery",
    "40204760":
        "ChemicalEvaporation SurfaceCoatingOperations FabricCoatingCoagulationCoating Cleanup",
    "40206010":
        "ChemicalEvaporation SurfaceCoatingOperations FabricDyeing DyePreparation",
    "40206030":
        "ChemicalEvaporation SurfaceCoatingOperations FabricDyeing DyeApplication",
    "40206032":
        "ChemicalEvaporation SurfaceCoatingOperations FabricDyeing DyeApplicationBeck",
    "40206034":
        "ChemicalEvaporation SurfaceCoatingOperations FabricDyeing DyeApplicationJet",
    "40206035":
        "ChemicalEvaporation SurfaceCoatingOperations FabricDyeing DyeApplicationContinuous",
    "40206050":
        "ChemicalEvaporation SurfaceCoatingOperations FabricDyeing Waste",
    "40280001":
        "ChemicalEvaporation SurfaceCoatingOperations EquipmentLeaks EquipmentLeaks",
    "40282001":
        "ChemicalEvaporation SurfaceCoatingOperations WastewaterAggregate ProcessAreaDrains",
    "40282002":
        "ChemicalEvaporation SurfaceCoatingOperations WastewaterAggregate ProcessEquipmentDrains",
    "40282599":
        "ChemicalEvaporation SurfaceCoatingOperations WastewaterPointsofGeneration OtherNotClassified",
    "40288801":
        "ChemicalEvaporation SurfaceCoatingOperations FugitiveEmissions General",
    "40288821":
        "ChemicalEvaporation SurfaceCoatingOperations FugitiveEmissions Basecoat",
    "40288822":
        "ChemicalEvaporation SurfaceCoatingOperations FugitiveEmissions Coating",
    "40288823":
        "ChemicalEvaporation SurfaceCoatingOperations FugitiveEmissions CleartopCoat",
    "40288824":
        "ChemicalEvaporation SurfaceCoatingOperations FugitiveEmissions Cleanup",
    "40290011":
        "ChemicalEvaporation SurfaceCoatingOperations FuelFiredEquipment DistillateOilIncineratorAfterburner",
    "40290012":
        "ChemicalEvaporation SurfaceCoatingOperations FuelFiredEquipment ResidualOilIncineratorAfterburner",
    "40290013":
        "ChemicalEvaporation SurfaceCoatingOperations FuelFiredEquipment NaturalGasIncineratorAfterburner",
    "40290023":
        "ChemicalEvaporation SurfaceCoatingOperations FuelFiredEquipment NaturalGasFlares",
    "40299995":
        "PetroleumandSolventEvaporation SurfaceCoatingOperations Miscellaneous SpecifyinCommentsField",
    "40299996":
        "PetroleumandSolventEvaporation SurfaceCoatingOperations Miscellaneous SpecifyinCommentsField",
    "40299998":
        "ChemicalEvaporation SurfaceCoatingOperations Miscellaneous Miscellaneous",
    "40299999":
        "PetroleumandSolventEvaporation SurfaceCoatingOperations Miscellaneous SeeComment",
    "40300101":
        "PetroleumandSolventEvaporation PetroleumProductStorageatRefineries DeletedDoNotUseSee403010and407 Gasoline",
    "40300103":
        "PetroleumandSolventEvaporation PetroleumProductStorageatRefineries DeletedDoNotUseSee403010and407 Gasoline",
    "40300105":
        "PetroleumandSolventEvaporation PetroleumProductStorageatRefineries DeletedDoNotUseSee403010and407 JetFuel",
    "40300106":
        "PetroleumandSolventEvaporation PetroleumProductStorageatRefineries DeletedDoNotUseSee403010and407 Kerosene",
    "40300152":
        "PetroleumandSolventEvaporation PetroleumProductStorageatRefineries DeletedDoNotUseSee403010and407 DistFuel",
    "40300198":
        "PetroleumandSolventEvaporation PetroleumProductStorageatRefineries DeletedDoNotUseSee403010and407 SeeComment",
    "40300302":
        "PetroleumandSolventEvaporation PetroleumProductStorageatRefineries DeletedDoNotUseSee403011and407 Gasoline",
    "40301001":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FixedRoofTanksVaryingSizes GasolineRVP13BreathingLoss67000Bbl.Size",
    "40301002":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FixedRoofTanksVaryingSizes GasolineRVP10BreathingLoss67000Bbl.Size",
    "40301003":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FixedRoofTanksVaryingSizes GasolineRVP7BreathingLoss67000Bbl.Size",
    "40301004":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FixedRoofTanksVaryingSizes GasolineRVP13BreathingLoss250000Bbl.Size",
    "40301005":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FixedRoofTanksVaryingSizes GasolineRVP10BreathingLoss250000Bbl.Size",
    "40301006":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FixedRoofTanksVaryingSizes GasolineRVP7BreathingLoss250000Bbl.Size",
    "40301007":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FixedRoofTanksVaryingSizes GasolineRVP13WorkingLoss",
    "40301008":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FixedRoofTanksVaryingSizes GasolineRVP10WorkingLoss",
    "40301009":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FixedRoofTanksVaryingSizes GasolineRVP7WorkingLoss",
    "40301010":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FixedRoofTanksVaryingSizes CrudeOilRVP5BreathingLoss67000Bbl.Size",
    "40301011":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FixedRoofTanksVaryingSizes CrudeOilRVP5BreathingLoss250000Bbl.Size",
    "40301012":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FixedRoofTanksVaryingSizes CrudeOilRVP5WorkingLoss",
    "40301013":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FixedRoofTanksVaryingSizes JetNaphthaJP4BreathingLoss67000Bbl.Size",
    "40301014":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FixedRoofTanksVaryingSizes JetNaphthaJP4BreathingLoss250000Bbl.Size",
    "40301015":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FixedRoofTanksVaryingSizes JetNaphthaJP4WorkingLoss",
    "40301016":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FixedRoofTanksVaryingSizes JetKeroseneBreathingLoss67000Bbl.Size",
    "40301017":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FixedRoofTanksVaryingSizes JetKeroseneBreathingLoss250000Bbl.Size",
    "40301018":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FixedRoofTanksVaryingSizes JetKeroseneWorkingLoss",
    "40301019":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FixedRoofTanksVaryingSizes DistillateFuel#2BreathingLoss67000Bbl.Size",
    "40301020":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FixedRoofTanksVaryingSizes DistillateFuel#2BreathingLoss250000Bbl.Size",
    "40301021":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FixedRoofTanksVaryingSizes DistillateFuel#2WorkingLoss",
    "40301022":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FixedRoofTanksVaryingSizes AsphaltOilBreathingLoss67000Bbl.Size",
    "40301023":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FixedRoofTanksVaryingSizes AsphaltOilWorkingLoss",
    "40301024":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FixedRoofTanksVaryingSizes AsphaltOilBreathingLoss250000Bbl.Size",
    "40301025":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FixedRoofTanksVaryingSizes Grade6FuelOilBreathingLoss67000Bbl.Size",
    "40301026":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FixedRoofTanksVaryingSizes Grade5FuelOilBreathingLoss67000Bbl.Size",
    "40301027":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FixedRoofTanksVaryingSizes Grade4FuelOilBreathingLoss67000Bbl.Size",
    "40301028":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FixedRoofTanksVaryingSizes Grade2FuelOilBreathingLoss67000Bbl.Size",
    "40301029":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FixedRoofTanksVaryingSizes Grade1FuelOilBreathingLoss67000Bbl.Size",
    "40301065":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FixedRoofTanksVaryingSizes Grade6FuelOilBreathingLoss250000Bbl.Size",
    "40301067":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FixedRoofTanksVaryingSizes Grade4FuelOilBreathingLoss250000Bbl.Size",
    "40301068":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FixedRoofTanksVaryingSizes Grade2FuelOilBreathingLoss250000Bbl.Size",
    "40301069":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FixedRoofTanksVaryingSizes Grade1FuelOilBreathingLoss250000Bbl.Size",
    "40301075":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FixedRoofTanksVaryingSizes Grade6FuelOilWorkingLoss",
    "40301076":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FixedRoofTanksVaryingSizes Grade5FuelOilWorkingLoss",
    "40301077":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FixedRoofTanksVaryingSizes Grade4FuelOilWorkingLoss",
    "40301078":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FixedRoofTanksVaryingSizes Grade2FuelOilWorkingLoss",
    "40301079":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FixedRoofTanksVaryingSizes Grade1FuelOilWorkingLoss",
    "40301097":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FixedRoofTanksVaryingSizes OtherProductBreathingLoss67000Bbl.Size",
    "40301098":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FixedRoofTanksVaryingSizes OtherProductBreathingLoss250000Bbl.Size",
    "40301099":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FixedRoofTanksVaryingSizes OtherProductWorkingLoss",
    "40301101":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FloatingRoofTanksVaryingSizes GasolineRVP13BreathingLoss67000Bbl.Size",
    "40301102":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FloatingRoofTanksVaryingSizes GasolineRVP10BreathingLoss67000Bbl.Size",
    "40301103":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FloatingRoofTanksVaryingSizes GasolineRVP7BreathingLoss67000Bbl.Size",
    "40301104":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FloatingRoofTanksVaryingSizes GasolineRVP13BreathingLoss250000Bbl.Size",
    "40301105":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FloatingRoofTanksVaryingSizes GasolineRVP10BreathingLoss250000Bbl.Size",
    "40301106":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FloatingRoofTanksVaryingSizes GasolineRVP7BreathingLoss250000Bbl.Size",
    "40301107":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FloatingRoofTanksVaryingSizes GasolineRVP13107WorkingLoss67000Bbl.Size",
    "40301108":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FloatingRoofTanksVaryingSizes GasolineRVP13107WorkingLoss250000Bbl.Size",
    "40301109":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FloatingRoofTanksVaryingSizes CrudeOilRVP5BreathingLoss67000Bbl.Size",
    "40301110":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FloatingRoofTanksVaryingSizes CrudeOilRVP5BreathingLoss250000Bbl.Size",
    "40301111":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FloatingRoofTanksVaryingSizes JetNaphthaJP4BreathingLoss67000Bbl.Size",
    "40301112":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FloatingRoofTanksVaryingSizes JetNaphthaJP4BreathingLoss250000Bbl.Size",
    "40301113":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FloatingRoofTanksVaryingSizes JetKeroseneBreathingLoss67000Bbl.Size",
    "40301114":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FloatingRoofTanksVaryingSizes JetKeroseneBreathingLoss250000Bbl.Size",
    "40301115":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FloatingRoofTanksVaryingSizes DistillateFuel#2BreathingLoss67000Bbl.Size",
    "40301116":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FloatingRoofTanksVaryingSizes DistillateFuel#2BreathingLoss250000Bbl.Size",
    "40301117":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FloatingRoofTanksVaryingSizes CrudeOilRVP5WorkingLoss",
    "40301118":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FloatingRoofTanksVaryingSizes JetNaphthaJP4WorkingLoss",
    "40301119":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FloatingRoofTanksVaryingSizes JetKeroseneWorkingLoss",
    "40301120":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FloatingRoofTanksVaryingSizes DistillateFuel#2WorkingLoss",
    "40301125":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FloatingRoofTanksVaryingSizes Grade6FuelOilBreathingLoss67000Bbl.Size",
    "40301126":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FloatingRoofTanksVaryingSizes Grade5FuelOilBreathingLoss67000Bbl.Size",
    "40301127":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FloatingRoofTanksVaryingSizes Grade4FuelOilBreathingLoss67000Bbl.Size",
    "40301129":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FloatingRoofTanksVaryingSizes Grade1FuelOilBreathingLoss67000Bbl.Size",
    "40301130":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FloatingRoofTanksVaryingSizes OtherProductBreathingLossExternalPrimarySeal",
    "40301131":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FloatingRoofTanksVaryingSizes GasolineBreathingLossExternalPrimarySeal",
    "40301132":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FloatingRoofTanksVaryingSizes CrudeOilBreathingLossExternalPrimarySeal",
    "40301133":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FloatingRoofTanksVaryingSizes JetNaphthaJP4BreathingLossExternalPrimarySeal",
    "40301134":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FloatingRoofTanksVaryingSizes JetKeroseneBreathingLossExternalPrimarySeal",
    "40301135":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FloatingRoofTanksVaryingSizes DistillateFuel#2BreathingLossExternalPrimarySeal",
    "40301140":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FloatingRoofTanksVaryingSizes OtherProductBreathingLossExternalSecondarySeal",
    "40301141":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FloatingRoofTanksVaryingSizes GasolineBreathingLossExternalSecondarySeal",
    "40301142":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FloatingRoofTanksVaryingSizes CrudeOilBreathingLossExternalSecondarySeal",
    "40301143":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FloatingRoofTanksVaryingSizes JetNaphthaJP4BreathingLossExternalSecondarySeal",
    "40301144":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FloatingRoofTanksVaryingSizes JetKeroseneBreathingLossExternalSecondarySeal",
    "40301145":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FloatingRoofTanksVaryingSizes DistillateFuel#2BreathingLossExternalSecondarySeal",
    "40301150":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FloatingRoofTanksVaryingSizes OtherProductBreathingLossInternal",
    "40301151":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FloatingRoofTanksVaryingSizes GasolineBreathingLossInternal",
    "40301152":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FloatingRoofTanksVaryingSizes CrudeOilBreathingLossInternal",
    "40301153":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FloatingRoofTanksVaryingSizes JetNaphthaJP4BreathingLossInternal",
    "40301154":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FloatingRoofTanksVaryingSizes JetKeroseneBreathingLossInternal",
    "40301155":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FloatingRoofTanksVaryingSizes DistillateFuel#2BreathingLossInternal",
    "40301165":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FloatingRoofTanksVaryingSizes Grade6FuelOilBreathingLoss250000Bbl.Size",
    "40301166":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FloatingRoofTanksVaryingSizes Grade5FuelOilBreathingLoss250000Bbl.Size",
    "40301167":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FloatingRoofTanksVaryingSizes Grade4FuelOilBreathingLoss250000Bbl.Size",
    "40301168":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FloatingRoofTanksVaryingSizes Grd2FuelOilBreathingLoss250000BblTankSizeUse40301116",
    "40301175":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FloatingRoofTanksVaryingSizes Grade6FuelOilWorkingLoss",
    "40301177":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FloatingRoofTanksVaryingSizes Grade4FuelOilWorkingLoss",
    "40301178":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FloatingRoofTanksVaryingSizes Grade2FuelOilWorkingLoss",
    "40301179":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FloatingRoofTanksVaryingSizes Grade1FuelOilWorkingLoss",
    "40301180":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FloatingRoofTanksVaryingSizes GasolineRVP13WorkingLoss",
    "40301181":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FloatingRoofTanksVaryingSizes GasolineRVP10WorkingLoss",
    "40301182":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FloatingRoofTanksVaryingSizes GasolineRVP7WorkingLoss",
    "40301197":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FloatingRoofTanksVaryingSizes OtherProductWorkingLoss",
    "40301198":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FloatingRoofTanksVaryingSizes OtherProductBreathingLoss67000Bbl.Size",
    "40301199":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FloatingRoofTanksVaryingSizes OtherProductBreathingLoss250000Bbl.Size",
    "40301201":
        "ChemicalEvaporation PetroleumProductStorageatRefineries VariableVaporSpace GasolineRVP13FillingLoss",
    "40301202":
        "ChemicalEvaporation PetroleumProductStorageatRefineries VariableVaporSpace GasolineRVP10FillingLoss",
    "40301203":
        "ChemicalEvaporation PetroleumProductStorageatRefineries VariableVaporSpace GasolineRVP7FillingLoss",
    "40301204":
        "ChemicalEvaporation PetroleumProductStorageatRefineries VariableVaporSpace JetNaphthaJP4FillingLoss",
    "40301205":
        "ChemicalEvaporation PetroleumProductStorageatRefineries VariableVaporSpace JetKeroseneFillingLoss",
    "40301206":
        "ChemicalEvaporation PetroleumProductStorageatRefineries VariableVaporSpace DistillateFuel#2FillingLoss",
    "40301207":
        "ChemicalEvaporation PetroleumProductStorageatRefineries VariableVaporSpace BenzeneFillingLoss",
    "40301299":
        "ChemicalEvaporation PetroleumProductStorageatRefineries VariableVaporSpace OtherProductFillingLoss",
    "40388801":
        "ChemicalEvaporation PetroleumProductStorageatRefineries FugitiveEmissions AllNotElsewhereClassified",
    "40399999":
        "ChemicalEvaporation PetroleumProductStorageatRefineries OtherNotClassified OtherNotElsewhereClassified",
    "40400101":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery BulkTerminals GasolineRVP13BreathingLoss67000BblCapacityFixedRoofTank",
    "40400102":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery BulkTerminals GasolineRVP10BreathingLoss67000BblCapacityFixedRoofTank",
    "40400103":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery BulkTerminals GasolineRVP7BreathingLoss67000Bbl.CapacityFixedRoofTank",
    "40400104":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery BulkTerminals GasolineRVP13BreathingLoss250000BblCapacityFixedRoofTank",
    "40400105":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery BulkTerminals GasolineRVP10BreathingLoss250000BblCapacityFixedRoofTank",
    "40400106":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery BulkTerminals GasolineRVP7BreathingLoss250000BblCapacityFixedRoofTank",
    "40400107":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery BulkTerminals GasolineRVP13WorkingLossDiam.IndependentFixedRoofTank",
    "40400108":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery BulkTerminals GasolineRVP10WorkingLossDiameterIndependentFixedRoofTank",
    "40400109":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery BulkTerminals GasolineRVP7WorkingLossDiameterIndependentFixedRoofTank",
    "40400110":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery BulkTerminals GasolineRVP13BreathingLoss67000BblCapacityFloatingRoofTank",
    "40400111":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery BulkTerminals GasolineRVP10BreathingLoss67000BblCapacityFloatingRoofTank",
    "40400112":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery BulkTerminals GasolineRVP7BreathingLoss67000BblCapacityFloatingRoofTank",
    "40400113":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery BulkTerminals GasolineRVP13BreathingLoss250000BblCap.FloatingRoofTank",
    "40400114":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery BulkTerminals GasolineRVP10BreathingLoss250000BblCap.FloatingRoofTank",
    "40400115":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery BulkTerminals GasolineRVP7BreathingLoss250000BblCap.FloatingRoofTank",
    "40400116":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery BulkTerminals GasolineRVP13107WorkingLoss67000BblCap.FloatRfTnk",
    "40400117":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery BulkTerminals GasolineRVP13107WorkingLoss250000BblCap.FloatRfTnk",
    "40400118":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery BulkTerminals GasolineRVP13FillingLoss10500BblCap.VariableVaporSpace",
    "40400119":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery BulkTerminals GasolineRVP10FillingLoss10500BblCap.VariableVaporSpace",
    "40400120":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery BulkTerminals GasolineRVP7FillingLoss10500BblCap.VariableVaporSpace",
    "40400121":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery BulkTerminals DieselFuelBreathingLossDiameterIndependentFixedRoofTank",
    "40400122":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery BulkTerminals DieselFuelWorkingLossDiameterIndependentFixedRoofTank",
    "40400123":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery BulkTerminals OtherLiquidsBreathingLossDiamIndependentFixedRoofTank",
    "40400124":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery BulkTerminals OtherLiquidsWorkingLossDiamIndependentFixedRoofTank",
    "40400130":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery BulkTerminals OtherLiquidsBreathingLossExternalFloatingRoofwPrimarySeal",
    "40400131":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery BulkTerminals GasolineRVP13BreathingLossExt.FloatingRoofwPrimarySeal",
    "40400132":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery BulkTerminals GasolineRVP10BreathingLossExt.FloatingRoofwPrimarySeal",
    "40400133":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery BulkTerminals GasolineRVP7BreathingLossExternalFloatingRoofwPrimarySeal",
    "40400140":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery BulkTerminals OtherLiquidsBreathingLossExt.FloatRoofTankwSecondySeal",
    "40400141":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery BulkTerminals GasolineRVP13BreathingLossExt.FloatingRoofwSecondarySeal",
    "40400142":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery BulkTerminals GasolineRVP10BreathingLossExt.FloatingRoofwSecondarySeal",
    "40400143":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery BulkTerminals GasolineRVP7BreathingLossExt.FloatingRoofwSecondarySeal",
    "40400148":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery BulkTerminals GasolineRVP13107WorkingLossExt.FloatRoofPriSecSeal",
    "40400149":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery BulkTerminals OtherLiquidsExternalFloatingRoofPrimarySecondarySeal",
    "40400150":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery BulkTerminals MiscellaneousLossesLeaksLoadingRacks",
    "40400151":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery BulkTerminals ValvesFlangesandPumps",
    "40400152":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery BulkTerminals VaporCollectionLosses",
    "40400153":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery BulkTerminals VaporControlUnitLosses",
    "40400154":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery BulkTerminals TankTruckVaporLeaks",
    "40400160":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery BulkTerminals OtherLiquidsBreathingLossInternalFloatingRoofwPrimarySeal",
    "40400161":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery BulkTerminals GasolineRVP13BreathingLossInt.FloatingRoofwPrimarySeal",
    "40400162":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery BulkTerminals GasolineRVP10BreathingLossInt.FloatingRoofwPrimarySeal",
    "40400163":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery BulkTerminals GasolineRVP7BreathingLossInternalFloatingRoofwPrimarySeal",
    "40400170":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery BulkTerminals OtherLiquidsBreathingLossInt.FloatingRoofwSecondarySeal",
    "40400171":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery BulkTerminals GasolineRVP13BreathingLossInt.FloatingRoofwSecondarySeal",
    "40400172":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery BulkTerminals GasolineRVP10BreathingLossInt.FloatingRoofwSecondarySeal",
    "40400173":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery BulkTerminals GasolineRVP7BreathingLossInt.FloatingRoofwSecondarySeal",
    "40400178":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery BulkTerminals GasolineRVP13107WorkingLossInt.FloatRoofPriSecSeal",
    "40400179":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery BulkTerminals OtherLiquidsWorkingLossInt.FloatRoofPriSecSeal",
    "40400199":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery BulkTerminals OtherNotClassified",
    "40400201":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery BulkPlants GasolineRVP13BreathingLoss67000BblCapacityFixedRoofTank",
    "40400202":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery BulkPlants GasolineRVP10BreathingLoss67000BblCapacityFixedRoofTank",
    "40400203":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery BulkPlants GasolineRVP7BreathingLoss67000Bbl.CapacityFixedRoofTank",
    "40400204":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery BulkPlants GasolineRVP13WorkingLoss67000Bbl.CapacityFixedRoofTank",
    "40400205":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery BulkPlants GasolineRVP10WorkingLoss67000Bbl.CapacityFixedRoofTank",
    "40400206":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery BulkPlants GasolineRVP7WorkingLoss67000Bbl.CapacityFixedRoofTank",
    "40400207":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery BulkPlants GasolineRVP13BreathingLoss67000BblCap.FloatingRoofTank",
    "40400208":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery BulkPlants GasolineRVP10BreathingLoss67000BblCap.FloatingRoofTank",
    "40400209":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery BulkPlants GasolineRVP7BreathingLoss67000BblCap.FloatingRoofTank",
    "40400210":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery BulkPlants GasolineRVP13107WorkingLoss67000BblCap.FloatRfTnk",
    "40400211":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery BulkPlants GasolineRVP13FillingLoss10500BblCap.VariableVaporSpace",
    "40400212":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery BulkPlants GasolineRVP10FillingLoss10500BblCap.VariableVaporSpace",
    "40400213":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery BulkPlants GasolineRVP7FillingLoss10500BblCap.VariableVaporSpace",
    "40400230":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery BulkPlants OtherLiquidsBreathingLossExternalFloatingRoofwPrimarySeal",
    "40400231":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery BulkPlants GasolineRVP13BreathingLossExt.FloatingRoofwPrimarySeal",
    "40400232":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery BulkPlants GasolineRVP10BreathingLossExt.FloatingRoofwPrimarySeal",
    "40400233":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery BulkPlants GasolineRVP7BreathingLossExternalFloatingRoofwPrimarySeal",
    "40400240":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery BulkPlants OtherLiquidsBreathingLossExt.FloatingRoofwSecondarySeal",
    "40400241":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery BulkPlants GasolineRVP13BreathingLossExt.FloatingRoofwSecondarySeal",
    "40400248":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery BulkPlants GasolineRVP10137WorkingLossExt.FloatRoofPriSecSeal",
    "40400249":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery BulkPlants OtherLiquidsExternalFloatingRoofPrimarySecondarySeal",
    "40400250":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery BulkPlants LoadingRacks",
    "40400251":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery BulkPlants ValvesFlangesandPumps",
    "40400252":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery BulkPlants MiscellaneousLossesLeaksVaporCollectionLosses",
    "40400253":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery BulkPlants MiscellaneousLossesLeaksVaporControlUnitLosses",
    "40400254":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery BulkPlants TankTruckVaporLosses",
    "40400255":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery BulkPlants LoadingRacksJetFuel",
    "40400260":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery BulkPlants OtherLiquidsBreathingLossInternalFloatingRoofwPrimarySeal",
    "40400261":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery BulkPlants GasolineRVP13BreathingLossInt.FloatingRoofwPrimarySeal",
    "40400262":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery BulkPlants GasolineRVP10BreathingLossInt.FloatingRoofwPrimarySeal",
    "40400263":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery BulkPlants GasolineRVP7BreathingLossInternalFloatingRoofwPrimarySeal",
    "40400270":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery BulkPlants OtherLiquidsBreathingLossInt.FloatingRoofwSecondarySeal",
    "40400271":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery BulkPlants GasolineRVP13BreathingLossInt.FloatingRoofwSecondarySeal",
    "40400272":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery BulkPlants GasolineRVP10BreathingLossInt.FloatingRoofwSecondarySeal",
    "40400273":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery BulkPlants GasolineRVP7BreathingLossInt.FloatingRoofwSecondarySeal",
    "40400278":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery BulkPlants GasolineRVP10137WorkingLossInt.FloatRoofPriSecSeal",
    "40400279":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery BulkPlants OtherLiquidsInternalFloatingRoofPrimarySecondarySeal",
    "40400300":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery OilandGasFieldStorageandWorkingTanks FixedRoofTankFlashingLoss",
    "40400301":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery OilandGasFieldStorageandWorkingTanks FixedRoofTankBreathingLoss",
    "40400302":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery OilandGasFieldStorageandWorkingTanks FixedRoofTankWorkingLoss",
    "40400303":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery OilandGasFieldStorageandWorkingTanks ExternalFloatingRoofTankwithPrimarySealsBreathingLoss",
    "40400304":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery OilandGasFieldStorageandWorkingTanks ExternalFloatingRoofTankwithSecondarySealsBreathingLoss",
    "40400305":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery OilandGasFieldStorageandWorkingTanks InternalFloatingRoofTankBreathingLoss",
    "40400306":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery OilandGasFieldStorageandWorkingTanks ExternalFloatingRoofTankWorkingLoss",
    "40400307":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery OilandGasFieldStorageandWorkingTanks InternalFloatingRoofTankWorkingLoss",
    "40400311":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery OilandGasFieldStorageandWorkingTanks FixedRoofTankCondensateworking+breathing+flashinglosses",
    "40400312":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery OilandGasFieldStorageandWorkingTanks FixedRoofTankCrudeOilworking+breathing+flashinglosses",
    "40400313":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery OilandGasFieldStorageandWorkingTanks FixedRoofTankLubeOilworking+breathing+flashinglosses",
    "40400314":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery OilandGasFieldStorageandWorkingTanks FixedRoofTankSpecialtyChemworking+breathing+flashing",
    "40400315":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery OilandGasFieldStorageandWorkingTanks FixedRoofTankProducedWaterworking+breathing+flashing",
    "40400316":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery OilandGasFieldStorageandWorkingTanks FixedRoofTankDieselworking+breathing+flashinglosses",
    "40400321":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery OilandGasFieldStorageandWorkingTanks ExternalFloatingRoofTankCondensateworking+breathing+flashing",
    "40400322":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery OilandGasFieldStorageandWorkingTanks ExternalFloatingRoofTankCrudeOilworking+breathing+flashing",
    "40400323":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery OilandGasFieldStorageandWorkingTanks ExternalFloatingRoofTankLubeOilworking+breathing+flashing",
    "40400324":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery OilandGasFieldStorageandWorkingTanks ExternalFloatingRoofTankSpecialtyChemworking+breathing+flashing",
    "40400325":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery OilandGasFieldStorageandWorkingTanks ExternalFloatingRoofTankProducedWaterworking+breathing+flashing",
    "40400326":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery OilandGasFieldStorageandWorkingTanks ExternalFloatingRoofTankDieselworking+breathing+flashing",
    "40400331":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery OilandGasFieldStorageandWorkingTanks InternalFloatingRoofTankCondensateworking+breathing+flashing",
    "40400332":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery OilandGasFieldStorageandWorkingTanks InternalFloatingRoofTankCrudeOilworking+breathing+flashing",
    "40400334":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery OilandGasFieldStorageandWorkingTanks InternalFloatingRoofTankSpecialtyChemworking+breathing+flashing",
    "40400335":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery OilandGasFieldStorageandWorkingTanks InternalFloatingRoofTankProducedWaterworking+breathing+flashing",
    "40400336":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery OilandGasFieldStorageandWorkingTanks InternalFloatingRoofTankDieselworking+breathing+flashing",
    "40400340":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery OilandGasFieldStorageandWorkingTanks PressureTankspressurerelieffrompopoffvalves",
    "40400401":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery PetroleumProductsUndergroundTanks GasolineRVP13BreathingLoss",
    "40400402":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery PetroleumProductsUndergroundTanks GasolineRVP13WorkingLoss",
    "40400403":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery PetroleumProductsUndergroundTanks GasolineRVP10BreathingLoss",
    "40400404":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery PetroleumProductsUndergroundTanks GasolineRVP10WorkingLoss",
    "40400405":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery PetroleumProductsUndergroundTanks GasolineRVP7BreathingLoss",
    "40400406":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery PetroleumProductsUndergroundTanks GasolineRVP7WorkingLoss",
    "40400407":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery PetroleumProductsUndergroundTanks CrudeOilRVP5BreathingLoss",
    "40400408":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery PetroleumProductsUndergroundTanks CrudeOilRVP5WorkingLoss",
    "40400409":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery PetroleumProductsUndergroundTanks JetNaphthaJP4BreathingLoss",
    "40400410":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery PetroleumProductsUndergroundTanks JetNaphthaJP4WorkingLoss",
    "40400411":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery PetroleumProductsUndergroundTanks JetKeroseneBreathingLoss",
    "40400412":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery PetroleumProductsUndergroundTanks JetKeroseneWorkingLoss",
    "40400413":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery PetroleumProductsUndergroundTanks DistillateFuel#2BreathingLoss",
    "40400414":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery PetroleumProductsUndergroundTanks DistillateFuel#2WorkingLoss",
    "40400497":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery PetroleumProductsUndergroundTanks OtherLiquidsBreathingLoss",
    "40400498":
        "ChemicalEvaporation PetroleumLiquidsStoragenonRefinery PetroleumProductsUndergroundTanks OtherLiquidsWorkingLoss",
    "40500101":
        "ChemicalEvaporation PrintingPublishing Drying Dryer",
    "40500201":
        "ChemicalEvaporation PrintingPublishing Letterpress Printing",
    "40500203":
        "ChemicalEvaporation PrintingPublishing Letterpress InkThinningSolventsMineralSolvents",
    "40500204":
        "ChemicalEvaporation PrintingPublishing Letterpress Dryer",
    "40500205":
        "ChemicalEvaporation PrintingPublishing Letterpress Othernondryerprinting",
    "40500211":
        "PetroleumandSolventEvaporation PrintingPublishing Letterpress Letterpress2751",
    "40500215":
        "ChemicalEvaporation PrintingPublishing Letterpress CleaningSolution",
    "40500301":
        "ChemicalEvaporation PrintingPublishing Flexographic Printing",
    "40500302":
        "ChemicalEvaporation PrintingPublishing Flexographic InkThinningSolventCarbitol",
    "40500303":
        "ChemicalEvaporation PrintingPublishing Flexographic InkThinningSolventCellosolve",
    "40500304":
        "ChemicalEvaporation PrintingPublishing Flexographic InkThinningSolventEthylAlcohol",
    "40500305":
        "ChemicalEvaporation PrintingPublishing Flexographic InkThinningSolventIsopropylAlcohol",
    "40500306":
        "ChemicalEvaporation PrintingPublishing Flexographic InkThinningSolventnPropylAlcohol",
    "40500307":
        "ChemicalEvaporation PrintingPublishing Flexographic InkThinningSolventNaphtha",
    "40500308":
        "ChemicalEvaporation PrintingPublishing Flexographic Dryer",
    "40500309":
        "ChemicalEvaporation PrintingPublishing Flexographic Othernondryerprinting",
    "40500311":
        "PetroleumandSolventEvaporation PrintingPublishing Flexographic PrintingFlexographic",
    "40500314":
        "ChemicalEvaporation PrintingPublishing Flexographic PropylAlcoholCleanup",
    "40500315":
        "ChemicalEvaporation PrintingPublishing Flexographic SteamWaterbased",
    "40500318":
        "ChemicalEvaporation PrintingPublishing Flexographic SteamWaterbasedinInk",
    "40500401":
        "ChemicalEvaporation PrintingPublishing Lithographic Printing",
    "40500402":
        "ChemicalEvaporation PrintingPublishing Lithographic Dryer",
    "40500403":
        "ChemicalEvaporation PrintingPublishing Lithographic Othernondryerprinting",
    "40500411":
        "PetroleumandSolventEvaporation PrintingPublishing Lithographic Lithographic2752",
    "40500412":
        "PetroleumandSolventEvaporation PrintingPublishing Lithographic Lithographic2752",
    "40500413":
        "ChemicalEvaporation PrintingPublishing Lithographic IsopropylAlcoholCleanup",
    "40500414":
        "PetroleumandSolventEvaporation PrintingPublishing General FlexographicPropylAlcoholCleanup",
    "40500415":
        "ChemicalEvaporation PrintingPublishing OffsetLithography DampeningSolutionwithAlcoholSubstitute",
    "40500416":
        "ChemicalEvaporation PrintingPublishing OffsetLithography DampeningSolutionwithHighSolventContent",
    "40500417":
        "ChemicalEvaporation PrintingPublishing OffsetLithography CleaningSolutionWaterbased",
    "40500418":
        "ChemicalEvaporation PrintingPublishing OffsetLithography DampeningSolutionwithIsopropylAlcohol",
    "40500421":
        "ChemicalEvaporation PrintingPublishing OffsetLithography HeatsetInkMixing",
    "40500422":
        "ChemicalEvaporation PrintingPublishing OffsetLithography HeatsetSolventStorage",
    "40500431":
        "ChemicalEvaporation PrintingPublishing OffsetLithography NonheatedLithographicInks",
    "40500432":
        "PetroleumandSolventEvaporation PrintingPublishing OffsetLithography NonheatedLithographicInks",
    "40500502":
        "ChemicalEvaporation PrintingPublishing Gravure InkThinningSolventDimethylformamide",
    "40500503":
        "ChemicalEvaporation PrintingPublishing Gravure InkThinningSolventEthylAcetate",
    "40500506":
        "ChemicalEvaporation PrintingPublishing Gravure InkThinningSolventMethylEthylKetone",
    "40500510":
        "ChemicalEvaporation PrintingPublishing Gravure InkThinningSolventToluene",
    "40500511":
        "ChemicalEvaporation PrintingPublishing Gravure Printing",
    "40500514":
        "ChemicalEvaporation PrintingPublishing Gravure CleanupSolvent",
    "40500515":
        "ChemicalEvaporation PrintingPublishing Rotogravure Dryer",
    "40500516":
        "ChemicalEvaporation PrintingPublishing Rotogravure Othernondryerprinting",
    "40500597":
        "ChemicalEvaporation PrintingPublishing General OtherNotClassified",
    "40500599":
        "ChemicalEvaporation PrintingPublishing Printing InkThinningSolvent",
    "40500601":
        "ChemicalEvaporation PrintingPublishing Printing InkMixing",
    "40500701":
        "ChemicalEvaporation PrintingPublishing Printing SolventStorage",
    "40500801":
        "ChemicalEvaporation PrintingPublishing ScreenPrinting ScreenPrinting",
    "40500802":
        "ChemicalEvaporation PrintingPublishing ScreenPrinting FugitiveEmissionsCleaningRags",
    "40500804":
        "ChemicalEvaporation PrintingPublishing ScreenPrinting Othernondryerprinting",
    "40500806":
        "ChemicalEvaporation PrintingPublishing DigitalPrinting Othernondryerprinting",
    "40500812":
        "PetroleumandSolventEvaporation PrintingPublishing ScreenPrinting ScreenPrinting",
    "40500906":
        "ChemicalEvaporation PrintingPublishing DigitalPrinting Othernondryerprinting",
    "40588801":
        "ChemicalEvaporation PrintingPublishing FugitiveEmissions General",
    "40600101":
        "ChemicalEvaporation TransportationandMarketingofPetroleumProducts TankCarsandTrucks GasolineSplashLoading",
    "40600126":
        "ChemicalEvaporation TransportationandMarketingofPetroleumProducts TankCarsandTrucks GasolineSubmergedLoading",
    "40600129":
        "ChemicalEvaporation TransportationandMarketingofPetroleumProducts TankCarsandTrucks AsphaltSplashLoading",
    "40600130":
        "ChemicalEvaporation TransportationandMarketingofPetroleumProducts TankCarsandTrucks DistillateOilSubmergedLoading",
    "40600131":
        "ChemicalEvaporation TransportationandMarketingofPetroleumProducts TankCarsandTrucks GasolineSubmergedLoadingNormalService",
    "40600132":
        "ChemicalEvaporation TransportationandMarketingofPetroleumProducts TankCarsandTrucks CrudeOilSubmergedLoadingNormalService",
    "40600133":
        "ChemicalEvaporation TransportationandMarketingofPetroleumProducts TankCarsandTrucks JetNaphthaSubmergedLoadingNormalService",
    "40600134":
        "ChemicalEvaporation TransportationandMarketingofPetroleumProducts TankCarsandTrucks KeroseneSubmergedLoadingNormalService",
    "40600135":
        "ChemicalEvaporation TransportationandMarketingofPetroleumProducts TankCarsandTrucks DistillateOilSubmergedLoadingNormalService",
    "40600136":
        "ChemicalEvaporation TransportationandMarketingofPetroleumProducts TankCarsandTrucks GasolineSplashLoadingNormalService",
    "40600137":
        "ChemicalEvaporation TransportationandMarketingofPetroleumProducts TankCarsandTrucks CrudeOilSplashLoadingNormalService",
    "40600138":
        "ChemicalEvaporation TransportationandMarketingofPetroleumProducts TankCarsandTrucks JetNaphthaSplashLoadingNormalService",
    "40600139":
        "ChemicalEvaporation TransportationandMarketingofPetroleumProducts TankCarsandTrucks KeroseneSplashLoadingNormalService",
    "40600140":
        "ChemicalEvaporation TransportationandMarketingofPetroleumProducts TankCarsandTrucks DistillateOilSplashLoadingNormalService",
    "40600141":
        "ChemicalEvaporation TransportationandMarketingofPetroleumProducts TankCarsandTrucks GasolineSubmergedLoadingBalancedService",
    "40600142":
        "ChemicalEvaporation TransportationandMarketingofPetroleumProducts TankCarsandTrucks CrudeOilSubmergedLoadingBalancedService",
    "40600143":
        "ChemicalEvaporation TransportationandMarketingofPetroleumProducts TankCarsandTrucks JetNaphthaSubmergedLoadingBalancedService",
    "40600144":
        "ChemicalEvaporation TransportationandMarketingofPetroleumProducts TankCarsandTrucks GasolineSplashLoadingBalancedService",
    "40600145":
        "ChemicalEvaporation TransportationandMarketingofPetroleumProducts TankCarsandTrucks CrudeOilSplashLoadingBalancedService",
    "40600146":
        "ChemicalEvaporation TransportationandMarketingofPetroleumProducts TankCarsandTrucks JetNaphthaSplashLoadingBalancedService",
    "40600147":
        "ChemicalEvaporation TransportationandMarketingofPetroleumProducts TankCarsandTrucks GasolineSubmergedLoadingCleanTanks",
    "40600148":
        "ChemicalEvaporation TransportationandMarketingofPetroleumProducts TankCarsandTrucks CrudeOilSubmergedLoadingCleanTanks",
    "40600149":
        "ChemicalEvaporation TransportationandMarketingofPetroleumProducts TankCarsandTrucks JetNaphthaSubmergedLoadingCleanTanks",
    "40600151":
        "ChemicalEvaporation TransportationandMarketingofPetroleumProducts TankCarsandTrucks EthanolSubmergedLoadingBalancedService",
    "40600160":
        "ChemicalEvaporation TransportationandMarketingofPetroleumProducts TankCarsandTrucks KeroseneSubmergedLoadingCleanTanks",
    "40600161":
        "ChemicalEvaporation TransportationandMarketingofPetroleumProducts TankCarsandTrucks DistillateOilSubmergedLoadingCleanTanks",
    "40600162":
        "ChemicalEvaporation TransportationandMarketingofPetroleumProducts TankCarsandTrucks GasolineLoadedwithFuelTransitLosses",
    "40600163":
        "ChemicalEvaporation TransportationandMarketingofPetroleumProducts TankCarsandTrucks GasolineReturnwithVaporTransitLosses",
    "40600164":
        "ChemicalEvaporation TransportationandMarketingofPetroleumProducts TankCarsandTrucks CrudeOilLoadedwithProductTransitLosses",
    "40600165":
        "ChemicalEvaporation TransportationandMarketingofPetroleumProducts TankCarsandTrucks CrudeOilLoadedwithVaporTransitLosses",
    "40600166":
        "ChemicalEvaporation TransportationandMarketingofPetroleumProducts TankCarsandTrucks JetFuelLoadedwithProductTransitLosses",
    "40600167":
        "ChemicalEvaporation TransportationandMarketingofPetroleumProducts TankCarsandTrucks JetFuelLoadedwithVaporTransitLosses",
    "40600168":
        "ChemicalEvaporation TransportationandMarketingofPetroleumProducts TankCarsandTrucks KeroseneLoadedwithProductTransitLosses",
    "40600170":
        "ChemicalEvaporation TransportationandMarketingofPetroleumProducts TankCarsandTrucks DistillateOilLoadedwithProductTransitLosses",
    "40600171":
        "ChemicalEvaporation TransportationandMarketingofPetroleumProducts TankCarsandTrucks DistillateOilLoadedwithVaporTransitLosses",
    "40600172":
        "ChemicalEvaporation TransportationandMarketingofPetroleumProducts TankCarsandTrucks LiquifiedPetroleumGasLPGLoadedwithFuelTransitLosses",
    "40600173":
        "ChemicalEvaporation TransportationandMarketingofPetroleumProducts TankCarsandTrucks LiquifiedPetroleumGasLPGReturnwithVaporTransitLosses",
    "40600190":
        "ChemicalEvaporation TransportationandMarketingofPetroleumProducts TankCarsandTrucks LoadingRackCombinedStream",
    "40600197":
        "PetroleumandSolventEvaporation TransportationandMarketingofPetroleumProducts TankCarsandTrucks NotClassified",
    "40600199":
        "ChemicalEvaporation TransportationandMarketingofPetroleumProducts TankCarsandTrucks OtherNotElsewhereClassified",
    "40600231":
        "ChemicalEvaporation TransportationandMarketingofPetroleumProducts MarineVessels GasolineLoadingTankersCleanedandVaporFreeTanks",
    "40600232":
        "ChemicalEvaporation TransportationandMarketingofPetroleumProducts MarineVessels GasolineLoadingTankers",
    "40600233":
        "ChemicalEvaporation TransportationandMarketingofPetroleumProducts MarineVessels GasolineLoadingBargesCleanedandVaporFreeTanks",
    "40600234":
        "ChemicalEvaporation TransportationandMarketingofPetroleumProducts MarineVessels GasolineLoadingTankersBallastedTank",
    "40600235":
        "ChemicalEvaporation TransportationandMarketingofPetroleumProducts MarineVessels GasolineOceanBargesLoadingBallastedTank",
    "40600236":
        "ChemicalEvaporation TransportationandMarketingofPetroleumProducts MarineVessels GasolineLoadingTankersUncleanedTanks",
    "40600237":
        "ChemicalEvaporation TransportationandMarketingofPetroleumProducts MarineVessels GasolineOceanBargesLoadingUncleanedTanks",
    "40600238":
        "ChemicalEvaporation TransportationandMarketingofPetroleumProducts MarineVessels GasolineLoadingBargesUncleanedTanks",
    "40600239":
        "ChemicalEvaporation TransportationandMarketingofPetroleumProducts MarineVessels GasolineTankersBallastedTank",
    "40600240":
        "ChemicalEvaporation TransportationandMarketingofPetroleumProducts MarineVessels GasolineLoadingBargesAverageTankCondition",
    "40600241":
        "ChemicalEvaporation TransportationandMarketingofPetroleumProducts MarineVessels GasolineTankerBallasting",
    "40600242":
        "ChemicalEvaporation TransportationandMarketingofPetroleumProducts MarineVessels GasolineTransitLoss",
    "40600243":
        "ChemicalEvaporation TransportationandMarketingofPetroleumProducts MarineVessels CrudeOilLoadingTankers",
    "40600244":
        "ChemicalEvaporation TransportationandMarketingofPetroleumProducts MarineVessels JetFuelLoadingTankers",
    "40600245":
        "ChemicalEvaporation TransportationandMarketingofPetroleumProducts MarineVessels KeroseneLoadingTankers",
    "40600246":
        "ChemicalEvaporation TransportationandMarketingofPetroleumProducts MarineVessels DistillateOilLoadingTankers",
    "40600248":
        "ChemicalEvaporation TransportationandMarketingofPetroleumProducts MarineVessels CrudeOilLoadingBarges",
    "40600249":
        "ChemicalEvaporation TransportationandMarketingofPetroleumProducts MarineVessels JetFuelLoadingBarges",
    "40600250":
        "ChemicalEvaporation TransportationandMarketingofPetroleumProducts MarineVessels KeroseneLoadingBarges",
    "40600251":
        "ChemicalEvaporation TransportationandMarketingofPetroleumProducts MarineVessels DistillateOilLoadingBarges",
    "40600253":
        "ChemicalEvaporation TransportationandMarketingofPetroleumProducts MarineVessels CrudeOilTankerBallasting",
    "40600255":
        "ChemicalEvaporation TransportationandMarketingofPetroleumProducts MarineVessels JetFuelTransitLoss",
    "40600257":
        "ChemicalEvaporation TransportationandMarketingofPetroleumProducts MarineVessels DistillateOilTransitLoss",
    "40600259":
        "ChemicalEvaporation TransportationandMarketingofPetroleumProducts MarineVessels TankerBargeCleaning",
    "40600260":
        "ChemicalEvaporation TransportationandMarketingofPetroleumProducts MarineVessels GasolineBargeLoadingBallasted",
    "40600273":
        "ChemicalEvaporation TransportationandMarketingofPetroleumProducts MarineVessels CrudeOilLoadingTankersAnyTankCondition",
    "40600298":
        "PetroleumandSolventEvaporation TransportationandMarketingofPetroleumProducts MarineVessels NotClassified",
    "40600299":
        "ChemicalEvaporation TransportationandMarketingofPetroleumProducts MarineVessels OtherNotElsewhereClassified",
    "40600301":
        "ChemicalEvaporation TransportationandMarketingofPetroleumProducts GasolineRetailOperationsStageI SplashFilling",
    "40600302":
        "ChemicalEvaporation TransportationandMarketingofPetroleumProducts GasolineRetailOperationsStageI SubmergedFilling",
    "40600305":
        "ChemicalEvaporation TransportationandMarketingofPetroleumProducts GasolineRetailOperationsStageI Unloading",
    "40600306":
        "ChemicalEvaporation TransportationandMarketingofPetroleumProducts GasolineRetailOperationsStageI BalancedSubmergedFilling",
    "40600307":
        "ChemicalEvaporation TransportationandMarketingofPetroleumProducts GasolineRetailOperationsStageI UndergroundTankBreathingandEmptying",
    "40600399":
        "ChemicalEvaporation TransportationandMarketingofPetroleumProducts GasolineRetailOperationsStageI OtherNotElsewhereClassified",
    "40600401":
        "ChemicalEvaporation TransportationandMarketingofPetroleumProducts FillingVehicleGasTanksStageII VaporLoss",
    "40600402":
        "ChemicalEvaporation TransportationandMarketingofPetroleumProducts FillingVehicleGasTanksStageII LiquidSpillLoss",
    "40600403":
        "PetroleumandSolventEvaporation TransportationandMarketingofPetroleumProducts FillingVehicleGasTanksStageII VaporLosswoControls",
    "40600499":
        "ChemicalEvaporation TransportationandMarketingofPetroleumProducts FillingVehicleGasTanksStageII OtherNotElsewhereClassified",
    "40600501":
        "ChemicalEvaporation TransportationandMarketingofPetroleumProducts PipelinePetroleumTransportGeneralAllProducts PipelineLeaks",
    "40600502":
        "ChemicalEvaporation TransportationandMarketingofPetroleumProducts PipelinePetroleumTransportGeneralAllProducts PipelineVenting",
    "40600503":
        "ChemicalEvaporation TransportationandMarketingofPetroleumProducts PipelinePetroleumTransportGeneralAllProducts PumpStation",
    "40600504":
        "ChemicalEvaporation TransportationandMarketingofPetroleumProducts PipelinePetroleumTransportGeneralAllProducts PumpStationLeaks",
    "40600601":
        "ChemicalEvaporation TransportationandMarketingofPetroleumProducts ConsumerCorporateFleetRefuelingStageII VaporLoss",
    "40600602":
        "ChemicalEvaporation TransportationandMarketingofPetroleumProducts ConsumerCorporateFleetRefuelingStageII LiquidSpillLosswithoutControls",
    "40600603":
        "ChemicalEvaporation TransportationandMarketingofPetroleumProducts ConsumerCorporateFleetRefuelingStageII VaporLosswithControls",
    "40600630":
        "ChemicalEvaporation TransportationandMarketingofPetroleumProducts ConsumerCorporateFleetRefuelingStageII AsphaltSplashLoading",
    "40600651":
        "ChemicalEvaporation TransportationandMarketingofPetroleumProducts ConsumerCorporateFleetRefuelingStageII DieselVaporLossw",
    "40600701":
        "ChemicalEvaporation TransportationandMarketingofPetroleumProducts ConsumerCorporateFleetRefuelingStageI SplashFilling",
    "40600702":
        "ChemicalEvaporation TransportationandMarketingofPetroleumProducts ConsumerCorporateFleetRefuelingStageI SubmergedFilling",
    "40600706":
        "ChemicalEvaporation TransportationandMarketingofPetroleumProducts ConsumerCorporateFleetRefuelingStageI BalancedSubmergedFilling",
    "40600707":
        "ChemicalEvaporation TransportationandMarketingofPetroleumProducts ConsumerCorporateFleetRefuelingStageI UndergroundTankBreathingandEmptying",
    "40688801":
        "ChemicalEvaporation TransportationandMarketingofPetroleumProducts FugitiveEmissions AllNotElsewhereClassified",
    "40688802":
        "PetroleumandSolventEvaporation TransportationandMarketingofPetroleumProducts FugitiveEmissions SpecifyinCommentsField",
    "40700401":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksAnhydrides AceticAnhydridesBreathingLoss",
    "40700402":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksAnhydrides AceticAnhydridesWorkingLoss",
    "40700403":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksAnhydrides MaleicAnhydrideBreathingLoss",
    "40700404":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksAnhydrides MaleicAnhydrideWorkingLoss",
    "40700406":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksAnhydrides PhthalicAnhydrideWorkingLoss",
    "40700497":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksAnhydrides AnhydridesBreathingLoss",
    "40700498":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksAnhydrides AnhydridesWorkingLoss",
    "40700801":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksAlcohols nButanolBreathingLoss",
    "40700802":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksAlcohols nButanolWorkingLoss",
    "40700803":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksAlcohols secButanolBreathingLoss",
    "40700804":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksAlcohols secBuanolWorkingLoss",
    "40700805":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksAlcohols tertButanolBreathingLoss",
    "40700806":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksAlcohols tertButanolWorkingLoss",
    "40700807":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksAlcohols CyclohexanolBreathingLoss",
    "40700808":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksAlcohols CyclohexanolWorkingLoss",
    "40700809":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksAlcohols EthanolBreathingLoss",
    "40700810":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksAlcohols EthanolWorkingLoss",
    "40700811":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksAlcohols IsobutylAlcoholBreathingLoss",
    "40700812":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksAlcohols IsobutylAlcoholWorkingLoss",
    "40700813":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksAlcohols IsopropylAlcoholBreathingLoss",
    "40700814":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksAlcohols IsopropylAlcoholWorkingLoss",
    "40700815":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksAlcohols MethanolBreathingLoss",
    "40700816":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksAlcohols MethanolWorkingLoss",
    "40700817":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksAlcohols nPropanolBreathingLoss",
    "40700818":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksAlcohols nPropanolWorkingLoss",
    "40700897":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksAlcohols AlcoholsBreathingLoss",
    "40700898":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksAlcohols AlcoholsWorkingLoss",
    "40701601":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksAlkanesParaffins DecaneBreathingLoss",
    "40701602":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksAlkanesParaffins DecaneWorkingLoss",
    "40701603":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksAlkanesParaffins DodecaneBreathingLoss",
    "40701604":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksAlkanesParaffins DodecaneWorkingLoss",
    "40701605":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksAlkanesParaffins HeptaneBreathingLoss",
    "40701606":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksAlkanesParaffins HeptaneWorkingLoss",
    "40701607":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksAlkanesParaffins IsopentaneBreathingLoss",
    "40701608":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksAlkanesParaffins IsopentaneWorkingLoss",
    "40701611":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksAlkanesParaffins NaphthaBreathingLoss",
    "40701612":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksAlkanesParaffins NaphthaWorkingLoss",
    "40701613":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksAlkanesParaffins PetroleumDistillateBreathingLoss",
    "40701614":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksAlkanesParaffins PetroleumDistillateWorkingLoss",
    "40701615":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksAlkanesParaffins HexaneBreathingLoss",
    "40701616":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksAlkanesParaffins HexaneWorkingLoss",
    "40701697":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksAlkanesParaffins AlkanesBreathingLoss",
    "40701698":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksAlkanesParaffins AlkanesWorkingLoss",
    "40702002":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksAlkenes DodeceneWorkingLoss",
    "40702097":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksAlkenes AlkenesBreathingLoss",
    "40702098":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksAlkenes AlkenesWorkingLoss",
    "40702801":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksAmides DimethylformamideBreathingLoss",
    "40702802":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksAmides DimethylformamideWorkingLoss",
    "40703201":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksAmines AnilineBreathingLoss",
    "40703202":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksAmines AnilineWorkingLoss",
    "40703203":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksAmines EthanolaminesBreathingLoss",
    "40703204":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksAmines EthanolaminesWorkingLoss",
    "40703205":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksAmines EthyleneaminesBreathingLoss",
    "40703206":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksAmines EthyleneaminesWorkingLoss",
    "40703207":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksAmines MonoethanolamineBreathingLoss",
    "40703208":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksAmines MonoethanolamineWorkingLoss",
    "40703210":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksAmines HexamineWorkingLoss",
    "40703212":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksAmines EthylenediamineWorkingLoss",
    "40703297":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksAmines AminesBreathingLoss",
    "40703298":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksAmines AminesWorkingLoss",
    "40703601":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksAromatics BenzeneBreathingLoss",
    "40703602":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksAromatics BenzeneWorkingLoss",
    "40703603":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksAromatics CresolBreathingLoss",
    "40703604":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksAromatics CresolWorkingLoss",
    "40703605":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksAromatics CumeneBreathingLoss",
    "40703606":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksAromatics CumeneWorkingLoss",
    "40703607":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksAromatics DiisopropylBenzeneBreathingLoss",
    "40703608":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksAromatics DiisopropylBenzeneWorkingLoss",
    "40703609":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksAromatics EthylBenzeneBreathingLoss",
    "40703610":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksAromatics EthylBenzeneWorkingLoss",
    "40703611":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksAromatics MethylStyreneBreathingLoss",
    "40703612":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksAromatics MethylStyreneWorkingLoss",
    "40703613":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksAromatics StyreneBreathingLoss",
    "40703614":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksAromatics StyreneWorkingLoss",
    "40703615":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksAromatics TolueneBreathingLoss",
    "40703616":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksAromatics TolueneWorkingLoss",
    "40703617":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksAromatics mXyleneBreathingLoss",
    "40703618":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksAromatics mXyleneWorkingLoss",
    "40703619":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksAromatics oXyleneBreathingLoss",
    "40703620":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksAromatics oXyleneWorkingLoss",
    "40703621":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksAromatics pXyleneBreathingLoss",
    "40703622":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksAromatics pXyleneWorkingLoss",
    "40703623":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksAromatics XylenesBreathingLoss",
    "40703624":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksAromatics XylenesWorkingLoss",
    "40703625":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksAromatics CreosoteBreathingLoss",
    "40703626":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksAromatics CreosoteWorkingLoss",
    "40703697":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksAromatics AromaticsBreathingLoss",
    "40703698":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksAromatics AromaticsWorkingLoss",
    "40704001":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksCarboxylicAcids AceticAcidBreathingLoss",
    "40704002":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksCarboxylicAcids AceticAcidWorkingLoss",
    "40704003":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksCarboxylicAcids AcrylicAcidBreathingLoss",
    "40704004":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksCarboxylicAcids AcrylicAcidWorkingLoss",
    "40704007":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksCarboxylicAcids FormicAcidBreathingLoss",
    "40704008":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksCarboxylicAcids FormicAcidWorkingLoss",
    "40704009":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksCarboxylicAcids PropionicAcidBreathingLoss",
    "40704010":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksCarboxylicAcids PropionicAcidWorkingLoss",
    "40704097":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksCarboxylicAcids CarboxylicAcidsBreathingLoss",
    "40704098":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksCarboxylicAcids CarboxylicAcidsWorkingLoss",
    "40704401":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksEsters ButylAcetateBreathingLoss",
    "40704402":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksEsters ButylAcetateWorkingLoss",
    "40704403":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksEsters ButylAcrylateBreathingLoss",
    "40704404":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksEsters ButylAcrylateWorkingLoss",
    "40704405":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksEsters EthylAcetateBreathingLoss",
    "40704406":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksEsters EthylAcetateWorkingLoss",
    "40704407":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksEsters EthylAcrylateBreathingLoss",
    "40704408":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksEsters EthylAcrylateWorkingLoss",
    "40704410":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksEsters IsobutylAcrylateWorkingLoss",
    "40704411":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksEsters IsopropylAcetateBreathingLoss",
    "40704412":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksEsters IsopropylAcetateWorkingLoss",
    "40704413":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksEsters MethylAcetateBreathingLoss",
    "40704414":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksEsters MethylAcetateWorkingLoss",
    "40704415":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksEsters MethylAcrylateBreathingLoss",
    "40704416":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksEsters MethylAcrylateWorkingLoss",
    "40704417":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksEsters MethylMethacrylateBreathingLoss",
    "40704418":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksEsters MethylMethacrylateWorkingLoss",
    "40704419":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksEsters VinylAcetateBreathingLoss",
    "40704420":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksEsters VinylAcetateWorkingLoss",
    "40704421":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksEsters nPropylAcetateBreathingLoss",
    "40704422":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksEsters nPropylAcetateWorkingLoss",
    "40704423":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksEsters iButyliButyrateBreathingLoss",
    "40704424":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksEsters iButyliButyrateWorkingLoss",
    "40704425":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksEsters AcrylicEstersBreathingLoss",
    "40704426":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksEsters AcrylicEstersWorkingLoss",
    "40704497":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksEsters EstersBreathingLoss",
    "40704498":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksEsters EstersWorkingLoss",
    "40704801":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksEthers MethyltertButylEtherBreathingLoss",
    "40704802":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksEthers MethyltertButylEtherWorkingLoss",
    "40704897":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksEthers EthersBreathingLoss",
    "40704898":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksEthers EthersWorkingLoss",
    "40705201":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksGlycolEthers ButylCarbitolBreathingLoss",
    "40705203":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksGlycolEthers ButylCellosolveBreathingLoss",
    "40705204":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksGlycolEthers ButylCellosolveWorkingLoss",
    "40705205":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksGlycolEthers CarbitolBreathingLoss",
    "40705206":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksGlycolEthers CarbitolWorkingLoss",
    "40705207":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksGlycolEthers CellosolveBreathingLoss",
    "40705208":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksGlycolEthers CellosolveWorkingLoss",
    "40705209":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksGlycolEthers DiethyleneGlycolBreathingLoss",
    "40705210":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksGlycolEthers DiethyleneGlycolWorkingLoss",
    "40705212":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksGlycolEthers MethylCarbitolWorkingLoss",
    "40705215":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksGlycolEthers PolyethyleneGlycolBreathingLoss",
    "40705216":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksGlycolEthers PolyethyleneGlycolWorkingLoss",
    "40705217":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksGlycolEthers TriethyleneGlycolBreathingLoss",
    "40705218":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksGlycolEthers TriethyleneGlycolWorkingLoss",
    "40705297":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksGlycolEthers GlycolEthersBreathingLoss",
    "40705298":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksGlycolEthers GlycolEthersWorkingLoss",
    "40705601":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksGlycols 14ButanediolBreathingLoss",
    "40705602":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksGlycols 14ButanediolWorkingLoss",
    "40705603":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksGlycols EthyleneGlycolBreathingLoss",
    "40705604":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksGlycols EthyleneGlycolWorkingLoss",
    "40705605":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksGlycols DipropyleneGlycolBreathingLoss",
    "40705606":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksGlycols DipropyleneGlycolWorkingLoss",
    "40705607":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksGlycols GlycerolBreathingLoss",
    "40705608":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksGlycols GlycerolWorkingLoss",
    "40705609":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksGlycols PropyleneGlycolBreathingLoss",
    "40705610":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksGlycols PropyleneGlycolWorkingLoss",
    "40705697":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksGlycols GlycolsBreathingLoss",
    "40705698":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksGlycols GlycolsWorkingLoss",
    "40706001":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksHalogenatedOrganics BenzylChlorideBreathingLoss",
    "40706002":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksHalogenatedOrganics BenzylChlorideWorkingLoss",
    "40706003":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksHalogenatedOrganics CaprolactamSolutionBreathingLoss",
    "40706004":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksHalogenatedOrganics CaprolactamSolutionWorkingLoss",
    "40706005":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksHalogenatedOrganics CarbonTetrachlorideBreathingLoss",
    "40706006":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksHalogenatedOrganics CarbonTetrachlorideWorkingLoss",
    "40706007":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksHalogenatedOrganics ChlorobenzeneBreathingLoss",
    "40706008":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksHalogenatedOrganics ChlorobenzeneWorkingLoss",
    "40706009":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksHalogenatedOrganics oDichlorobenzeneBreathingLoss",
    "40706010":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksHalogenatedOrganics oDichlorobenzeneWorkingLoss",
    "40706011":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksHalogenatedOrganics pDichlorobenzeneBreathingLoss",
    "40706012":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksHalogenatedOrganics pDichlorobenzeneWorkingLoss",
    "40706013":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksHalogenatedOrganics EpichlorohydrinBreathingLoss",
    "40706014":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksHalogenatedOrganics EpichlorohydrinWorkingLoss",
    "40706015":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksHalogenatedOrganics EthyleneDibromideBreathingLoss",
    "40706017":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksHalogenatedOrganics EthyleneDichlorideBreathingLoss",
    "40706018":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksHalogenatedOrganics EthyleneDichlorideWorkingLoss",
    "40706019":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksHalogenatedOrganics MethyleneChlorideDichloromethaneBreathingLoss",
    "40706020":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksHalogenatedOrganics MethyleneChlorideDichloromethaneWorkingLoss",
    "40706021":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksHalogenatedOrganics PerchloroethyleneBreathingLoss",
    "40706022":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksHalogenatedOrganics PerchloroethyleneWorkingLoss",
    "40706023":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksHalogenatedOrganics TrichloroethyleneBreathingLoss",
    "40706024":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksHalogenatedOrganics TrichloroethyleneWorkingLoss",
    "40706027":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksHalogenatedOrganics 111TrichloroethaneMethylChloroformBreathingLoss",
    "40706028":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksHalogenatedOrganics 111TrichloroethaneMethylChloroformWorkingLoss",
    "40706029":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksHalogenatedOrganics ChlorosolveBreathingLoss",
    "40706031":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksHalogenatedOrganics MethylChlorideBreathingLoss",
    "40706032":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksHalogenatedOrganics MethylChlorideWorkingLoss",
    "40706033":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksHalogenatedOrganics ChloroformBreathingLoss",
    "40706034":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksHalogenatedOrganics ChloroformWorkingLoss",
    "40706097":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksHalogenatedOrganics HalogenatedOrganicsBreathingLoss",
    "40706098":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksHalogenatedOrganics HalogenatedOrganicsWorkingLoss",
    "40706401":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksIsocyanates MethylenediphenylDiisocyanateMDIBreathingLoss",
    "40706402":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksIsocyanates MethylenediphenylDiisocyanateMDIWorkingLoss",
    "40706403":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksIsocyanates TolueneDiisocyanateTDIBreathingLoss",
    "40706404":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksIsocyanates TolueneDiisocyanateTDIWorkingLoss",
    "40706497":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksIsocyanates IsocyanatesBreathingLoss",
    "40706498":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksIsocyanates IsocyanatesWorkingLoss",
    "40706801":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksKetones CyclohexanoneBreathingLoss",
    "40706802":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksKetones CyclohexanoneWorkingLoss",
    "40706803":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksKetones AcetoneBreathingLoss",
    "40706804":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksKetones AcetoneWorkingLoss",
    "40706805":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksKetones MethylEthylKetoneBreathingLoss",
    "40706806":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksKetones MethylEthylKetoneWorkingLoss",
    "40706807":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksKetones MethylIsobutylKetoneBreathingLoss",
    "40706808":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksKetones MethylIsobutylKetoneWorkingLoss",
    "40706813":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksKetones MethylamylKetoneBreathingLoss",
    "40706814":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksKetones MethylamylKetoneWorkingLoss",
    "40706897":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksKetones KetonesBreathingLoss",
    "40706898":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksKetones KetonesWorkingLoss",
    "40707601":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksNitriles AcrylonitrileBreathingLoss",
    "40707602":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksNitriles AcrylonitrileWorkingLoss",
    "40707603":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksNitriles AcetonitrileBreathingLoss",
    "40707604":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksNitriles AcetonitrileWorkingLoss",
    "40707697":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksNitriles NitrilesBreathingLoss",
    "40707698":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksNitriles NitrilesWorkingLoss",
    "40708001":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksNitroCompounds NitrobenzeneBreathingLoss",
    "40708002":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksNitroCompounds NitrobenzeneWorkingLoss",
    "40708097":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksNitroCompounds NitroCompoundsBreathingLoss",
    "40708098":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksNitroCompounds NitroCompoundsWorkingLoss",
    "40708401":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksPhenols NonylphenolBreathingLoss",
    "40708402":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksPhenols NonylphenolWorkingLoss",
    "40708403":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksPhenols PhenolBreathingLoss",
    "40708404":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksPhenols PhenolWorkingLoss",
    "40708497":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksPhenols PhenolsBreathingLoss",
    "40708498":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksPhenols PhenolsWorkingLoss",
    "40714601":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksMiscellaneous CarbonDisulfideBreathingLoss",
    "40714602":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksMiscellaneous CarbonDisulfideWorkingLoss",
    "40714603":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksMiscellaneous DimethylSulfoxideBreathingLoss",
    "40714604":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksMiscellaneous DimethylSulfoxideWorkingLoss",
    "40714605":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksMiscellaneous TetrahydrofuranBreathingLoss",
    "40714606":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksMiscellaneous TetrahydrofuranWorkingLoss",
    "40714697":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksMiscellaneous OtherNotElsewhereClassifiedBreathingLoss",
    "40714698":
        "ChemicalEvaporation OrganicChemicalStorage FixedRoofTanksMiscellaneous OtherNotElsewhereClassifiedWorkingLoss",
    "40715801":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksAlcohols MethanolBreathingLoss",
    "40715802":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksAlcohols MethanolWorkingLoss",
    "40715809":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksAlcohols EthanolBreathingLoss",
    "40715810":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksAlcohols EthanolWorkingLoss",
    "40715811":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksAlcohols IsopropanolBreathingLoss",
    "40715812":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksAlcohols IsopropanolWorkingLoss",
    "40717204":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksAldehydes AcroleinWorkingLoss",
    "40717205":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksAldehydes ButyraldehydeBreathingLoss",
    "40717206":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksAldehydes ButyraldehydeWorkingLoss",
    "40717207":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksAldehydes FormadehydeBreathingLoss",
    "40717208":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksAldehydes FormadehydeWorkingLoss",
    "40717209":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksAldehydes IsobutyraldehydeBreathingLoss",
    "40717210":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksAldehydes IsobutyraldehydeWorkingLoss",
    "40717211":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksAldehydes PropionaldehydeBreathingLoss",
    "40717297":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksAldehydes AldehydesBreathingLoss",
    "40717298":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksAldehydes AldehydesWorkingLoss",
    "40717601":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksAlkanesParaffins CyclohexaneBreathingLoss",
    "40717602":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksAlkanesParaffins CyclohexaneWorkingLoss",
    "40717603":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksAlkanesParaffins HexaneBreathingLoss",
    "40717604":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksAlkanesParaffins HexaneWorkingLoss",
    "40717605":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksAlkanesParaffins PentaneBreathingLoss",
    "40717606":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksAlkanesParaffins PentaneWorkingLoss",
    "40717611":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksAlkanesParaffins NaphthaBreathingLoss",
    "40717612":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksAlkanesParaffins NaphthaWorkingLoss",
    "40717613":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksAlkanesParaffins PetroleumDistillatesBreathingLoss",
    "40717614":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksAlkanesParaffins PetroleumDistillatesWorkingLoss",
    "40717697":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksAlkanesParaffins AlkanesBreathingLoss",
    "40717698":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksAlkanesParaffins AlkanesWorkingLoss",
    "40718002":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksAlkenes IsopreneWorkingLoss",
    "40718006":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksAlkenes 1PenteneWorkingLoss",
    "40718009":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksAlkenes CyclopenteneBreathingLoss",
    "40718097":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksAlkenes AlkenesBreathingLoss",
    "40718098":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksAlkenes AlkenesWorkingLoss",
    "40718801":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksAmides DimethylformamideBreathingLoss",
    "40719601":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksAromatics BenzeneBreathingLoss",
    "40719602":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksAromatics BenzeneWorkingLoss",
    "40719613":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksAromatics StyreneBreathingLoss",
    "40719614":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksAromatics StyreneWorkingLoss",
    "40719615":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksAromatics TolueneBreathingLoss",
    "40719616":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksAromatics TolueneWorkingLoss",
    "40719620":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksAromatics oXyleneWorkingLoss",
    "40719621":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksAromatics pXyleneBreathingLoss",
    "40719622":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksAromatics pXyleneWorkingLoss",
    "40719623":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksAromatics XylenesBreathingLoss",
    "40719624":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksAromatics XylenesWorkingLoss",
    "40719697":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksAromatics AromaticsBreathingLoss",
    "40719698":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksAromatics AromaticsWorkingLoss",
    "40720098":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksCarboxylicAcids CarboxylicAcidsWorkingLoss",
    "40720402":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksEsters ButylAcetateWorkingLoss",
    "40720405":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksEsters EthylAcetateBreathingLoss",
    "40720406":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksEsters EthylAcetateWorkingLoss",
    "40720418":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksEsters MethylMethacrylateWorkingLoss",
    "40720419":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksEsters VinylAcetateBreathingLoss",
    "40720420":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksEsters VinylAcetateWorkingLoss",
    "40720426":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksEsters AcrylicEstersWorkingLoss",
    "40720803":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksEthers PropyleneOxideBreathingLoss",
    "40720804":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksEthers PropyleneOxideWorkingLoss",
    "40720897":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksEthers EthersBreathingLoss",
    "40720898":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksEthers EthersWorkingLoss",
    "40721603":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksGlycols EthyleneGlycolBreathingLoss",
    "40721604":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksGlycols EthyleneGlycolWorkingLoss",
    "40722001":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksHalogenatedOrganics CarbonTetrachlorideBreathingLoss",
    "40722002":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksHalogenatedOrganics CarbonTetrachlorideWorkingLoss",
    "40722003":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksHalogenatedOrganics ChloroformBreathingLoss",
    "40722004":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksHalogenatedOrganics ChloroformWorkingLoss",
    "40722005":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksHalogenatedOrganics EthyleneDichlorideBreathingLoss",
    "40722006":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksHalogenatedOrganics EthyleneDichlorideWorkingLoss",
    "40722008":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksHalogenatedOrganics MethyleneChlorideDichloromethaneWorkingLoss",
    "40722009":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksHalogenatedOrganics TrichlorethyleneBreathingLoss",
    "40722010":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksHalogenatedOrganics TrichlorethyleneWorkingLoss",
    "40722022":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksHalogenatedOrganics PerchloroethyleneWorkingLoss",
    "40722031":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksHalogenatedOrganics MethylChlorideBreathingloss",
    "40722032":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksHalogenatedOrganics MethylChlorideWorkingLoss",
    "40722097":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksHalogenatedOrganics HalogenatedOrganicsBreathingLoss",
    "40722098":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksHalogenatedOrganics HalogenatedOrganicsWorkingLoss",
    "40722801":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksKetones AcetoneBreathingLoss",
    "40722802":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksKetones AcetoneWorkingLoss",
    "40722803":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksKetones MethylEthylKetoneBreathingLoss",
    "40722804":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksKetones MethylEthylKetoneWorkingLoss",
    "40722805":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksKetones MethylIsobutylKetoneBreathingLoss",
    "40722806":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksKetones MethylIsobutylKetoneWorkingLoss",
    "40722807":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksKetones CyclohexanoneBreathingLoss",
    "40722898":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksKetones KetonesWorkingLoss",
    "40723297":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksMercaptans MercaptansBreathingLoss",
    "40723298":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksMercaptans MercaptansWorkingLoss",
    "40723601":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksNitriles AcrylonitrileBreathingLoss",
    "40729601":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksMiscellaneous CarbonDisulfideBreathingLoss",
    "40729602":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksMiscellaneous CarbonDisulfideWorkingLoss",
    "40729603":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksMiscellaneous DimethylSulfoxideBreathingLoss",
    "40729604":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksMiscellaneous DimethylSulfoxideWorkingLoss",
    "40729605":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksMiscellaneous TetrahydrofuranBreathingLoss",
    "40729606":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksMiscellaneous TetrahydrofuranWorkingLoss",
    "40729697":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksMiscellaneous OtherNotElsewhereClassifiedBreathingLoss",
    "40729698":
        "ChemicalEvaporation OrganicChemicalStorage FloatingRoofTanksMiscellaneous OtherNotElsewhereClassifiedWorkingLoss",
    "40750014":
        "ChemicalEvaporation OrganicChemicalStorage UndergroundStorageTanks MethylMethacrylate",
    "40750016":
        "ChemicalEvaporation OrganicChemicalStorage UndergroundStorageTanks AcrylonitrileWorkingLoss",
    "40750072":
        "ChemicalEvaporation OrganicChemicalStorage UndergroundStorageTanks Alcohols",
    "40750098":
        "ChemicalEvaporation OrganicChemicalStorage UndergroundStorageTanks OtherNotClassified",
    "40780403":
        "ChemicalEvaporation OrganicChemicalStorage PressureTanksAnhydrides MaleicAnhydride",
    "40780815":
        "ChemicalEvaporation OrganicChemicalStorage PressureTanksAlcohols Methanol",
    "40780819":
        "ChemicalEvaporation OrganicChemicalStorage PressureTanksAlcohols Xylol",
    "40781201":
        "ChemicalEvaporation OrganicChemicalStorage PressureTanksAldehydes Acetaldehyde",
    "40781202":
        "ChemicalEvaporation OrganicChemicalStorage PressureTanksAldehydes Acrolein",
    "40781602":
        "ChemicalEvaporation OrganicChemicalStorage PressureTanksAlkanes Butane",
    "40781604":
        "ChemicalEvaporation OrganicChemicalStorage PressureTanksAlkanes NaturalGas",
    "40781605":
        "ChemicalEvaporation OrganicChemicalStorage PressureTanksAlkanes Propane",
    "40781606":
        "ChemicalEvaporation OrganicChemicalStorage PressureTanksAlkanes Isopentane",
    "40781607":
        "ChemicalEvaporation OrganicChemicalStorage PressureTanksAlkanes Pentane",
    "40781699":
        "ChemicalEvaporation OrganicChemicalStorage PressureTanksAlkanes Alkanes",
    "40782001":
        "ChemicalEvaporation OrganicChemicalStorage PressureTanksAlkenes 13Butadiene",
    "40782002":
        "ChemicalEvaporation OrganicChemicalStorage PressureTanksAlkenes 1Butene",
    "40782004":
        "ChemicalEvaporation OrganicChemicalStorage PressureTanksAlkenes Ethylene",
    "40782005":
        "ChemicalEvaporation OrganicChemicalStorage PressureTanksAlkenes Isobutylene",
    "40782006":
        "ChemicalEvaporation OrganicChemicalStorage PressureTanksAlkenes Propylene",
    "40782007":
        "ChemicalEvaporation OrganicChemicalStorage PressureTanksAlkenes Isoprene",
    "40782009":
        "ChemicalEvaporation OrganicChemicalStorage PressureTanksAlkenes 1Pentene",
    "40782011":
        "ChemicalEvaporation OrganicChemicalStorage PressureTanksAlkenes Cyclopentene",
    "40782099":
        "ChemicalEvaporation OrganicChemicalStorage PressureTanksAlkenes Alkenes",
    "40783202":
        "ChemicalEvaporation OrganicChemicalStorage PressureTanksAmines Dimethylamine",
    "40783203":
        "ChemicalEvaporation OrganicChemicalStorage PressureTanksAmines Trimethylamine",
    "40783299":
        "ChemicalEvaporation OrganicChemicalStorage PressureTanksAmines Amines",
    "40784801":
        "ChemicalEvaporation OrganicChemicalStorage PressureTanksEthers EthyleneOxide",
    "40784899":
        "ChemicalEvaporation OrganicChemicalStorage PressureTanksEthers Ethers",
    "40786001":
        "ChemicalEvaporation OrganicChemicalStorage PressureTanksHalogenatedOrganics EthylChloride",
    "40786002":
        "ChemicalEvaporation OrganicChemicalStorage PressureTanksHalogenatedOrganics MethylChloride",
    "40786003":
        "ChemicalEvaporation OrganicChemicalStorage PressureTanksHalogenatedOrganics Phosgene",
    "40786023":
        "ChemicalEvaporation OrganicChemicalStorage PressureTanksHalogenatedOrganics Trichloroethylene",
    "40786099":
        "ChemicalEvaporation OrganicChemicalStorage PressureTanksHalogenatedOrganics HalogenatedOrganics",
    "40786401":
        "ChemicalEvaporation OrganicChemicalStorage PressureTanksIsocyanates MethylIsocyanate",
    "40786499":
        "ChemicalEvaporation OrganicChemicalStorage PressureTanksIsocyanates Isocyanates",
    "40786803":
        "ChemicalEvaporation OrganicChemicalStorage PressureTanksKetones Acetone",
    "40786805":
        "ChemicalEvaporation OrganicChemicalStorage PressureTanksKetones MethylEthylKetone",
    "40787201":
        "ChemicalEvaporation OrganicChemicalStorage PressureTanksMercaptansThiols MethylMercaptan",
    "40787299":
        "ChemicalEvaporation OrganicChemicalStorage PressureTanksMercaptansThiols Mercaptans",
    "40788403":
        "ChemicalEvaporation OrganicChemicalStorage PressureTanksPhenols Phenol",
    "40799901":
        "ChemicalEvaporation OrganicChemicalStorage MiscellaneousChemicals CarbonDisulfide",
    "40799905":
        "ChemicalEvaporation OrganicChemicalStorage MiscellaneousChemicals Tetrahydrofuran",
    "40799997":
        "PetroleumandSolventEvaporation OrganicChemicalStorage Miscellaneous SpecifyinComments",
    "40799998":
        "PetroleumandSolventEvaporation OrganicChemicalStorage Miscellaneous SpecifyinComments",
    "40799999":
        "ChemicalEvaporation OrganicChemicalStorage MiscellaneousChemicals OtherNotClassified",
    "40880001":
        "ChemicalEvaporation OrganicChemicalTransportation EquipmentLeaks General",
    "40899995":
        "ChemicalEvaporation OrganicChemicalTransportation OrganicChemicals CarsTrucksLoadingRack",
    "40899996":
        "ChemicalEvaporation OrganicChemicalTransportation OrganicChemicals MarineVesselsLoading",
    "40899997":
        "ChemicalEvaporation OrganicChemicalTransportation OrganicChemicals MarineVesselsLoadingRack",
    "40899999":
        "ChemicalEvaporation OrganicChemicalTransportation OrganicChemicals OtherNotClassifiedLoadingRack",
    "41000101":
        "ChemicalEvaporation DryCleaning PetroleumSolventIndustrial Stoddard",
    "41000115":
        "ChemicalEvaporation DryCleaning PetroleumSolventIndustrial WasherExtractor",
    "41000125":
        "ChemicalEvaporation DryCleaning PetroleumSolventIndustrial SolventSettlingTankBatchFlow",
    "41000130":
        "ChemicalEvaporation DryCleaning PetroleumSolventIndustrial Dryer",
    "41000143":
        "ChemicalEvaporation DryCleaning PetroleumSolventIndustrial FiltrationDiatomiteRegenerative",
    "41000202":
        "ChemicalEvaporation DryCleaning PetroleumSolventCommercial Stoddard",
    "41000215":
        "ChemicalEvaporation DryCleaning PetroleumSolventCommercial WasherExtractor",
    "41000230":
        "ChemicalEvaporation DryCleaning PetroleumSolventCommercial Dryer",
    "41000231":
        "ChemicalEvaporation DryCleaning PetroleumSolventCommercial DryerLoadingUnloading",
    "41000244":
        "ChemicalEvaporation DryCleaning PetroleumSolventCommercial FiltrationCartridgeCarbonCoreBatchOperation",
    "41000262":
        "ChemicalEvaporation DryCleaning PetroleumSolventCommercial WasteDisposalFilterWasteCentrifuged",
    "41082001":
        "ChemicalEvaporation DryCleaning PetroleumSolventWastewaterAggregate ProcessAreaDrains",
    "41100101":
        "ChemicalEvaporation AerosolCans FillingFacilities OtherNotElsewhereClassified",
    "41100102":
        "ChemicalEvaporation AerosolCans FillingFacilities Mixing",
    "41100103":
        "ChemicalEvaporation AerosolCans FillingFacilities Filling",
    "41100104":
        "ChemicalEvaporation AerosolCans FillingFacilities LeakCheck",
    "41100105":
        "ChemicalEvaporation AerosolCans FillingFacilities Washing",
    "42500101":
        "ChemicalEvaporation unknown unknown FixedRoofTanks210BblSizeBreathingLoss",
    "42500102":
        "ChemicalEvaporation unknown unknown FixedRoofTanks210BblSizeWorkingLoss",
    "42500201":
        "ChemicalEvaporation unknown unknown FixedRoofTanks500BblSizeBreathingLoss",
    "42500202":
        "ChemicalEvaporation unknown unknown FixedRoofTanks500BblSizeWorkingLoss",
    "42500301":
        "ChemicalEvaporation unknown unknown FixedRoofTanks1000BblSizeBreathingLoss",
    "42500302":
        "ChemicalEvaporation unknown unknown FixedRoofTanks1000BblSizeWorkingLoss",
    "42505001":
        "ChemicalEvaporation unknown unknown FloatingRoofTanks1000BblSizeStandingLoss",
    "42505002":
        "ChemicalEvaporation unknown unknown FloatingRoofTanks1000BblSizeWorkingLoss",
    "42505101":
        "ChemicalEvaporation unknown unknown FloatingRoofTanks5000BblSizeStandingLoss",
    "42505102":
        "ChemicalEvaporation unknown unknown FloatingRoofTanks5000BblSizeCrudeOilWorkingLoss",
    "49000101":
        "ChemicalEvaporation OrganicSolventEvaporation SolventExtractionProcess PetroleumNaphthaStoddard",
    "49000102":
        "ChemicalEvaporation OrganicSolventEvaporation SolventExtractionProcess MethylEthylKetone",
    "49000103":
        "ChemicalEvaporation OrganicSolventEvaporation SolventExtractionProcess MethylIsobutylKetone",
    "49000104":
        "ChemicalEvaporation OrganicSolventEvaporation SolventExtractionProcess Furfural",
    "49000105":
        "ChemicalEvaporation OrganicSolventEvaporation SolventExtractionProcess Trichloroethylene",
    "49000199":
        "ChemicalEvaporation OrganicSolventEvaporation SolventExtractionProcess OtherNotClassified",
    "49000201":
        "ChemicalEvaporation OrganicSolventEvaporation WasteSolventRecoveryOperations StorageTankVent",
    "49000202":
        "ChemicalEvaporation OrganicSolventEvaporation WasteSolventRecoveryOperations CondenserVent",
    "49000203":
        "ChemicalEvaporation OrganicSolventEvaporation WasteSolventRecoveryOperations IncineratorStack",
    "49000204":
        "ChemicalEvaporation OrganicSolventEvaporation WasteSolventRecoveryOperations SolventSpillage",
    "49000205":
        "ChemicalEvaporation OrganicSolventEvaporation WasteSolventRecoveryOperations SolventLoading",
    "49000206":
        "ChemicalEvaporation OrganicSolventEvaporation WasteSolventRecoveryOperations FugitiveLeaks",
    "49000207":
        "ChemicalEvaporation OrganicSolventEvaporation WasteSolventRecoveryOperations DistillationVent",
    "49000208":
        "ChemicalEvaporation OrganicSolventEvaporation WasteSolventRecoveryOperations Decanting",
    "49000299":
        "ChemicalEvaporation OrganicSolventEvaporation WasteSolventRecoveryOperations OtherNotClassified",
    "49000399":
        "ChemicalEvaporation OrganicSolventEvaporation RailCarCleaning OtherNotClassified",
    "49000401":
        "ChemicalEvaporation OrganicSolventEvaporation TankTruckCleaning Acetone",
    "49000405":
        "ChemicalEvaporation OrganicSolventEvaporation TankTruckCleaning PropyleneGlycol",
    "49000499":
        "ChemicalEvaporation OrganicSolventEvaporation TankTruckCleaning OtherNotClassified",
    "49000501":
        "ChemicalEvaporation OrganicSolventEvaporation AirStrippingTower Trichloroethylene",
    "49000502":
        "ChemicalEvaporation OrganicSolventEvaporation AirStrippingTower Perchloroethylene",
    "49000503":
        "ChemicalEvaporation OrganicSolventEvaporation AirStrippingTower 111Trichloroethane",
    "49000504":
        "ChemicalEvaporation OrganicSolventEvaporation AirStrippingTower Chloroform",
    "49000599":
        "ChemicalEvaporation OrganicSolventEvaporation AirStrippingTower Solvent",
    "49000601":
        "ChemicalEvaporation OrganicSolventEvaporation FreonRecoveryRecyclingOperations CFC12RecoveryAutoAirConditioning",
    "49090011":
        "ChemicalEvaporation OrganicSolventEvaporation FuelFiredEquipment IncineratorDistillateOilNo.2",
    "49090013":
        "ChemicalEvaporation OrganicSolventEvaporation FuelFiredEquipment IncineratorNaturalGas",
    "49090015":
        "ChemicalEvaporation OrganicSolventEvaporation FuelFiredEquipment OtherIncineratorsRecoveredSolvents",
    "49090021":
        "ChemicalEvaporation OrganicSolventEvaporation FuelFiredEquipment FlareDistillateOilNo.2",
    "49090023":
        "ChemicalEvaporation OrganicSolventEvaporation FuelFiredEquipment FlareNaturalGas",
    "49099998":
        "ChemicalEvaporation OrganicSolventEvaporation MiscellaneousVolatileOrganicCompoundEvaporation Miscellaneous",
    "49099999":
        "PetroleumandSolventEvaporation OrganicSolventEvaporation MiscellaneousVolatileOrganicCompoundEvaporation IdentifytheProcessandSolventinComments",
    "50100101":
        "WasteDisposal SolidWasteDisposalGovernment MunicipalWasteIncineration ModularStarvedAirCombustor",
    "50100102":
        "WasteDisposal SolidWasteDisposalGovernment MunicipalWasteIncineration MassBurnCombustor",
    "50100103":
        "WasteDisposal SolidWasteDisposalGovernment MunicipalWasteIncineration CombustorRefuseDerivedFuelRDF",
    "50100104":
        "WasteDisposal SolidWasteDisposalGovernment MunicipalWasteIncineration MassBurnRefractoryWallCombustor",
    "50100105":
        "WasteDisposal SolidWasteDisposalGovernment MunicipalWasteIncineration MassBurnWaterwallCombustor",
    "50100106":
        "WasteDisposal SolidWasteDisposalGovernment MunicipalWasteIncineration MassBurnRotaryWaterwallCombustor",
    "50100107":
        "WasteDisposal SolidWasteDisposalGovernment MunicipalWasteIncineration ModularExcessAirCombustor",
    "50100108":
        "WasteDisposal SolidWasteDisposalGovernment MunicipalIncineration FluidizedBedRefuseDerivedFuel",
    "50100119":
        "WasteDisposal SolidWasteDisposalGovernment MunicipalWasteIncineration Largegreaterthan250tonsperdayFluidizedBedRefuseDerivedFuel",
    "50100201":
        "WasteDisposal SolidWasteDisposalGovernment OpenBurningDump GeneralRefuse",
    "50100202":
        "WasteDisposal SolidWasteDisposalGovernment OpenBurningDump VegetationOnly",
    "50100302":
        "WasteDisposal SolidWasteDisposalGovernment HospitalMedicalInfectiousWasteIncinerationHMIWI IncineratorLowlevelRadioactiveWaste",
    "50100303":
        "WasteDisposal SolidWasteDisposalGovernment HospitalMedicalInfectiousWasteIncinerationHMIWI IncineratorPathologicalWaste",
    "50100321":
        "WasteDisposal SolidWasteDisposalGovernment HospitalMedicalInfectiousWasteIncinerationHMIWI Smalllessthan200lbshror1600lbdaybatchBatchIncinerator",
    "50100322":
        "WasteDisposal SolidWasteDisposalGovernment HospitalMedicalInfectiousWasteIncinerationHMIWI Smalllessthan200lbshror1600lbdaybatchBatchModularExcessAirCombustor",
    "50100333":
        "WasteDisposal SolidWasteDisposalGovernment HospitalMedicalInfectiousWasteIncinerationHMIWI Smalllessthan200lbshror1600lbdaybatchIncinerator",
    "50100401":
        "WasteDisposal SolidWasteDisposalGovernment MunicipalSolidWasteLandfill UnpavedRoadTraffic",
    "50100402":
        "WasteDisposal SolidWasteDisposalGovernment MunicipalSolidWasteLandfill FugitiveEmissions",
    "50100403":
        "WasteDisposal SolidWasteDisposalGovernment MunicipalSolidWasteLandfill AreaMethod",
    "50100404":
        "WasteDisposal SolidWasteDisposalGovernment MunicipalSolidWasteLandfill TrenchMethod",
    "50100405":
        "WasteDisposal SolidWasteDisposalGovernment MunicipalSolidWasteLandfill RampMethod",
    "50100406":
        "WasteDisposal SolidWasteDisposalGovernment MunicipalSolidWasteLandfill GasCollectionSystemOther",
    "50100407":
        "WasteDisposal SolidWasteDisposalGovernment MunicipalSolidWasteLandfill StoragePiles",
    "50100408":
        "WasteDisposal SolidWasteDisposalGovernment MunicipalSolidWasteLandfill ConveyingofCoverMaterial",
    "50100409":
        "WasteDisposal SolidWasteDisposalGovernment MunicipalSolidWasteLandfill SpreadingofDailyCover",
    "50100410":
        "WasteDisposal SolidWasteDisposalGovernment MunicipalSolidWasteLandfill LandfillDumpWasteGasDestructionWasteGasFlares",
    "50100411":
        "WasteDisposal SolidWasteDisposalGovernment MunicipalSolidWasteLandfill LandfillGasLFGDestructionIncinerator",
    "50100412":
        "WasteDisposal SolidWasteDisposalGovernment MunicipalSolidWasteLandfill LandfillGasLFGDestructionOtherNotElsewhereClassified",
    "50100420":
        "WasteDisposal SolidWasteDisposalGovernment MunicipalSolidWasteLandfill LandfillGasLFGEnergyRecoveryTurbine",
    "50100421":
        "WasteDisposal SolidWasteDisposalGovernment MunicipalSolidWasteLandfill LandfillGasLFGEnergyRecoveryInternalCombustionEngine",
    "50100422":
        "WasteDisposal SolidWasteDisposalGovernment MunicipalSolidWasteLandfill LandfillGasLFGEnergyRecoveryOtherNotElsewhereClassified",
    "50100423":
        "WasteDisposal SolidWasteDisposalGovernment MunicipalSolidWasteLandfill LandfillGasLFGEnergyRecoveryBoiler",
    "50100431":
        "WasteDisposal SolidWasteDisposalMunicipalWaste LandfillDump WasteGasPurificationAdsorption",
    "50100432":
        "WasteDisposal SolidWasteDisposalMunicipalWaste LandfillDump WasteGasPurificationMembranes",
    "50100433":
        "WasteDisposal SolidWasteDisposalGovernment MunicipalSolidWasteLandfill LandfillGasLFGPurification",
    "50100505":
        "WasteDisposal SolidWasteDisposalGovernment OtherIncineration MedicalWasteIncineratorunspecifiedtypeInfectiouswastesonly",
    "50100506":
        "WasteDisposal SolidWasteDisposalGovernment OtherIncineration Sludge",
    "50100507":
        "WasteDisposal SolidWasteDisposalGovernment OtherIncineration ConicalDesignTeePeeMunicipalRefuse",
    "50100510":
        "WasteDisposal SolidWasteDisposalGovernment OtherIncineration TrenchBurnerWood",
    "50100511":
        "WasteDisposal SolidWasteDisposalGovernment OtherIncineration TrenchBurnerTires",
    "50100512":
        "WasteDisposal SolidWasteDisposalGovernment OtherIncineration TrenchBurnerRefuse",
    "50100515":
        "WasteDisposal SolidWasteDisposalGovernment OtherIncineration SludgeMultipleHearth",
    "50100516":
        "WasteDisposal SolidWasteDisposalGovernment OtherIncineration SludgeFluidizedBed",
    "50100518":
        "WasteDisposal SolidWasteDisposalGovernment OtherIncineration SewageSludgeIncineratorSingleHearthCyclone",
    "50100519":
        "WasteDisposal SolidWasteDisposalGovernment OtherIncineration SewageSludgeIncineratorRotaryKiln",
    "50100520":
        "WasteDisposal SolidWasteDisposalGovernment OtherIncineration SewageSludgeIncineratorHighPressureWetOxidation",
    "50100601":
        "WasteDisposal SolidWasteDisposalGovernment FireFighting StructureJetFuel",
    "50100602":
        "WasteDisposal SolidWasteDisposalGovernment FireFighting StructureDistillateOil",
    "50100603":
        "WasteDisposal SolidWasteDisposalGovernment FireFighting StructureKerosene",
    "50100604":
        "WasteDisposal SolidWasteDisposalGovernment FireFighting StructureWoodPallets",
    "50100701":
        "WasteDisposal SolidWasteDisposalGovernment PubliclyOwnedTreatmentWorks EntirePlantNotElsewhereClassified",
    "50100702":
        "WasteDisposal SolidWasteDisposalGovernment PubliclyOwnedTreatmentWorks PrimarySettlingTank",
    "50100703":
        "WasteDisposal SolidWasteDisposalGovernment PubliclyOwnedTreatmentWorks SecondarySettlingTank",
    "50100704":
        "WasteDisposal SolidWasteDisposalGovernment PubliclyOwnedTreatmentWorks AerationBasin",
    "50100707":
        "WasteDisposal SolidWasteDisposalGovernment PubliclyOwnedTreatmentWorks HeadworksScreening",
    "50100710":
        "WasteDisposal SolidWasteDisposalGovernment PubliclyOwnedTreatmentWorks CollectorSewers",
    "50100712":
        "WasteDisposal SolidWasteDisposalGovernment PubliclyOwnedTreatmentWorks Drain",
    "50100715":
        "WasteDisposal SolidWasteDisposalGovernment PubliclyOwnedTreatmentWorks AeratedGritChamber",
    "50100719":
        "WasteDisposal SolidWasteDisposalGovernment PubliclyOwnedTreatmentWorks LiftStation",
    "50100720":
        "WasteDisposal SolidWasteDisposalGovernment SewageTreatment POTWPrimarySettlingTank",
    "50100731":
        "WasteDisposal SolidWasteDisposalGovernment PubliclyOwnedTreatmentWorks DiffusedAirActivatedSludgeThickener",
    "50100732":
        "WasteDisposal SolidWasteDisposalGovernment PubliclyOwnedTreatmentWorks MechanicalMixAirActivatedSludge",
    "50100733":
        "WasteDisposal SolidWasteDisposalGovernment PubliclyOwnedTreatmentWorks PureOxygenActivatedSludge",
    "50100734":
        "WasteDisposal SolidWasteDisposalGovernment PubliclyOwnedTreatmentWorks TricklingFilter",
    "50100740":
        "WasteDisposal SolidWasteDisposalGovernment PubliclyOwnedTreatmentWorks SecondaryClarifier",
    "50100760":
        "WasteDisposal SolidWasteDisposalGovernment PubliclyOwnedTreatmentWorks ChlorineContactBasin",
    "50100769":
        "WasteDisposal SolidWasteDisposalGovernment PubliclyOwnedTreatmentWorks StorageBasinorOpenTank",
    "50100771":
        "WasteDisposal SolidWasteDisposalGovernment PubliclyOwnedTreatmentWorks GravitySludgeThickener",
    "50100772":
        "WasteDisposal SolidWasteDisposalGovernment PubliclyOwnedTreatmentWorks DAFSludgeThickener",
    "50100781":
        "WasteDisposal SolidWasteDisposalGovernment PubliclyOwnedTreatmentWorks AnaerobicDigester",
    "50100789":
        "WasteDisposal SolidWasteDisposalGovernment PubliclyOwnedTreatmentWorks SludgeDigesterGasFlare",
    "50100791":
        "WasteDisposal SolidWasteDisposalGovernment PubliclyOwnedTreatmentWorks BeltFilterPress",
    "50100792":
        "WasteDisposal SolidWasteDisposalGovernment PubliclyOwnedTreatmentWorks SludgeCentrifuge",
    "50100793":
        "WasteDisposal SolidWasteDisposalGovernment PubliclyOwnedTreatmentWorks SludgeDryingBed",
    "50100795":
        "WasteDisposal SolidWasteDisposalGovernment PubliclyOwnedTreatmentWorks SludgeStorageLagoonsDryingBeds",
    "50100799":
        "WasteDisposal SolidWasteDisposalGovernment PubliclyOwnedTreatmentWorks OtherNotClassified",
    "50100801":
        "WasteDisposal SolidWasteDisposalGovernment SewageSludgeIncineration Incinerator",
    "50100802":
        "WasteDisposal SolidWasteDisposalGovernment SewageSludgeIncineration MultipleHearthIncinerator",
    "50100803":
        "WasteDisposal SolidWasteDisposalGovernment SewageSludgeIncineration FluidizedBedCombustor",
    "50180001":
        "WasteDisposal SolidWasteDisposalGovernment EquipmentLeaks EquipmentLeaks",
    "50182001":
        "WasteDisposal SolidWasteDisposalGovernment WastewaterAggregate ProcessAreaDrains",
    "50182002":
        "WasteDisposal SolidWasteDisposalGovernment WastewaterAggregate ProcessEquipmentDrains",
    "50182599":
        "WasteDisposal SolidWasteDisposalGovernment WastewaterPointsofGeneration SpecifyPointofGeneration",
    "50190005":
        "WasteDisposal SolidWasteDisposalGovernment AuxillaryFuelNoEmissions DistillateOil",
    "50190006":
        "WasteDisposal SolidWasteDisposalGovernment AuxillaryFuelNoEmissions NaturalGas",
    "50190010":
        "WasteDisposal SolidWasteDisposalGovernment AuxillaryFuelNoEmissions LiquifiedPetroleumGasLPG",
    "50200101":
        "WasteDisposal SolidWasteDisposalCommercialInstitutional Incineration MultipleChamber",
    "50200102":
        "WasteDisposal SolidWasteDisposalCommercialInstitutional Incineration SingleChamber",
    "50200103":
        "WasteDisposal SolidWasteDisposalCommercialInstitutional Incineration ControlledAir",
    "50200104":
        "WasteDisposal SolidWasteDisposalCommercialInstitutional Incineration ConicalDesignTeePeeMunicipalRefuse",
    "50200105":
        "WasteDisposal SolidWasteDisposalCommercialInstitutional Incineration ConicalDesignTeePeeWoodRefuse",
    "50200201":
        "WasteDisposal SolidWasteDisposalCommercialInstitutional OpenBurning Wood",
    "50200202":
        "WasteDisposal SolidWasteDisposalCommercialInstitutional OpenBurning Refuse",
    "50200205":
        "WasteDisposal SolidWasteDisposalCommercialInstitutional OpenBurning Weeds",
    "50200207":
        "WasteDisposal SolidWasteDisposalCommercialInstitutional OpenBurning ForestResidues",
    "50200501":
        "WasteDisposal SolidWasteDisposalCommercialInstitutional IncinerationSpecialPurpose MedWasteControlledAirIncinakaStarvedair2stgorModularcomb",
    "50200502":
        "WasteDisposal SolidWasteDisposalCommercialInstitutional IncinerationSpecialPurpose MedWasteExcessAirIncinakaBatchMultipleChamberorRetort",
    "50200503":
        "WasteDisposal SolidWasteDisposalCommercialInstitutional IncinerationSpecialPurpose MedicalWasteRotaryKilnIncinerator",
    "50200504":
        "WasteDisposal SolidWasteDisposalCommercialInstitutional IncinerationSpecialPurpose MedicalWasteIncineratorunspecifiedtypeuse502005010203",
    "50200505":
        "WasteDisposal SolidWasteDisposalCommercialInstitutional IncinerationSpecialPurpose MedicalWasteIncineratorunspecifiedtypeInfectiouswastesonly",
    "50200506":
        "WasteDisposal SolidWasteDisposalCommercialInstitutional IncinerationSpecialPurpose Sludge",
    "50200507":
        "WasteDisposal SolidWasteDisposalCommercialInstitutional IncinerationSpecialPurpose VOCContaminatedSoil",
    "50200515":
        "WasteDisposal SolidWasteDisposalCommercialInstitutional IncinerationSpecialPurpose SewageSludgeIncineratorMultipleHearth",
    "50200516":
        "WasteDisposal SolidWasteDisposalCommercialInstitutional IncinerationSpecialPurpose SewageSludgeIncineratorFluidizedBed",
    "50200518":
        "WasteDisposal SolidWasteDisposalCommercialInstitutional IncinerationSpecialPurpose SewageSludgeIncineratorSingleHearthCyclone",
    "50200519":
        "WasteDisposal SolidWasteDisposalCommercialInstitutional IncinerationSpecialPurpose SewageSludgeIncineratorRotaryKiln",
    "50200601":
        "WasteDisposal SolidWasteDisposalCommercialInstitutional LandfillDump WasteGasFlares",
    "50200602":
        "WasteDisposal SolidWasteDisposalCommercialInstitutional LandfillDump MunicipalFugitiveEmissions",
    "50200901":
        "WasteDisposal SolidWasteDisposalCommercialInstitutional AsbestosRemoval General",
    "50280001":
        "WasteDisposal SolidWasteDisposalCommercialInstitutional EquipmentLeaks EquipmentLeaks",
    "50282001":
        "WasteDisposal SolidWasteDisposalCommercialInstitutional WastewaterAggregate ProcessAreaDrains",
    "50282002":
        "WasteDisposal SolidWasteDisposalCommercialInstitutional WastewaterAggregate ProcessEquipmentDrains",
    "50282599":
        "WasteDisposal SolidWasteDisposalCommercialInstitutional WastewaterPointsofGeneration SpecifyPointofGeneration",
    "50290005":
        "WasteDisposal SolidWasteDisposalCommercialInstitutional AuxillaryFuelNoEmissions DistillateOil",
    "50290006":
        "WasteDisposal SolidWasteDisposalCommercialInstitutional AuxillaryFuelNoEmissions NaturalGas",
    "50290010":
        "WasteDisposal SolidWasteDisposalCommercialInstitutional AuxillaryFuelNoEmissions LiquifiedPetroleumGasLPG",
    "50300101":
        "WasteDisposal SolidWasteDisposalIndustrial Incineration MultipleChamber",
    "50300102":
        "WasteDisposal SolidWasteDisposalIndustrial Incineration SingleChamber",
    "50300103":
        "WasteDisposal SolidWasteDisposalIndustrial Incineration ControlledAir",
    "50300105":
        "WasteDisposal SolidWasteDisposalIndustrial Incineration ConicalDesignTeePeeWoodRefuse",
    "50300106":
        "WasteDisposal SolidWasteDisposalIndustrial Incineration AirCurtainCombustorWood",
    "50300107":
        "WasteDisposal SolidWasteDisposalIndustrial Incineration AirCurtainCombustorTires",
    "50300109":
        "WasteDisposal SolidWasteDisposalIndustrial Incineration AirCurtainCombustorRefuse",
    "50300111":
        "WasteDisposal SolidWasteDisposalIndustrial Incineration MassBurnRefractoryWallCombustor",
    "50300112":
        "WasteDisposal SolidWasteDisposalIndustrial Incineration MassBurnWaterwallCombustor",
    "50300113":
        "WasteDisposal SolidWasteDisposalIndustrial Incineration MassBurnRotaryWaterwallCombustor",
    "50300114":
        "WasteDisposal SolidWasteDisposalIndustrial Incineration ModularStarvedAirCombustor",
    "50300115":
        "WasteDisposal SolidWasteDisposalIndustrial Incineration ModularExcessAirCombustor",
    "50300116":
        "WasteDisposal SolidWasteDisposalIndustrial Incineration IncineratorThermalOxidizer",
    "50300149":
        "WasteDisposal SolidWasteDisposalIndustrial Incineration SmallRemoteIncineratorburnslessthan3tonsdayCyclonicBurnBarrel",
    "50300151":
        "WasteDisposal SolidWasteDisposalIndustrial Incineration BurnOffOvenOtherNotElsewhereClassified",
    "50300154":
        "WasteDisposal SolidWasteDisposalIndustrial Incineration BurnOffOvenPartReclamationUnit",
    "50300201":
        "WasteDisposal SolidWasteDisposalIndustrial OpenBurning WoodVegetationLeaves",
    "50300202":
        "WasteDisposal SolidWasteDisposalIndustrial OpenBurning Refuse",
    "50300203":
        "WasteDisposal SolidWasteDisposalIndustrial OpenBurning AutoBodyComponents",
    "50300204":
        "WasteDisposal SolidWasteDisposalIndustrial OpenBurning CoalRefusePiles",
    "50300205":
        "WasteDisposal SolidWasteDisposalIndustrial OpenBurning RocketPropellant",
    "50300501":
        "WasteDisposal SolidWasteDisposalIndustrial Incineration HazardousWaste",
    "50300502":
        "WasteDisposal SolidWasteDisposalIndustrial Incineration HazardousWasteIncineratorsFluidizedBed",
    "50300503":
        "WasteDisposal SolidWasteDisposalIndustrial Incineration HazardousWasteIncineratorsLiquidInjection",
    "50300504":
        "WasteDisposal SolidWasteDisposalIndustrial Incineration HazardousWasteIncineratorsRotaryKiln",
    "50300505":
        "WasteDisposal SolidWasteDisposalIndustrial Incineration HazardousWasteIncineratorsMultipleHearth",
    "50300506":
        "WasteDisposal SolidWasteDisposalIndustrial Incineration Sludge",
    "50300516":
        "WasteDisposal SolidWasteDisposalIndustrial Incineration SewageSludgeIncineratorFluidizedBed",
    "50300520":
        "WasteDisposal SolidWasteDisposalIndustrial Incineration SewageSludgeIncineratorHighPressureWetOxidation",
    "50300599":
        "WasteDisposal SolidWasteDisposalIndustrial Incineration FuelNotClassified",
    "50300601":
        "WasteDisposal SolidWasteDisposalIndustrial SolidWasteLandfill LandfillDumpWasteGasFlares",
    "50300602":
        "WasteDisposal SolidWasteDisposalIndustrial SolidWasteLandfill OtherNotElsewhereClassified",
    "50300603":
        "WasteDisposal SolidWasteDisposalIndustrial SolidWasteLandfill FugitiveEmissions",
    "50300607":
        "WasteDisposal SolidWasteDisposalIndustrial SolidWasteLandfill StoragePiles",
    "50300701":
        "WasteDisposal SolidWasteDisposalIndustrial WastewaterTreatment General",
    "50300702":
        "WasteDisposal SolidWasteDisposalIndustrial LiquidWaste WasteTreatmentGeneral",
    "50300703":
        "WasteDisposal SolidWasteDisposalIndustrial WastewaterTreatment EntirePlantNotElsewhereClassified",
    "50300705":
        "WasteDisposal SolidWasteDisposalIndustrial WastewaterTreatment AerationBasin",
    "50300710":
        "WasteDisposal SolidWasteDisposalIndustrial WastewaterTreatment OpenSump",
    "50300712":
        "WasteDisposal SolidWasteDisposalIndustrial WastewaterTreatment AeratedGritChamber",
    "50300713":
        "WasteDisposal SolidWasteDisposalIndustrial WastewaterTreatment OilWaterSeparator",
    "50300718":
        "WasteDisposal SolidWasteDisposalIndustrial WastewaterTreatment Drain",
    "50300724":
        "WasteDisposal SolidWasteDisposalIndustrial WastewaterTreatment EqualizationBasin",
    "50300727":
        "WasteDisposal SolidWasteDisposalIndustrial WastewaterTreatment NeutralizationBasin",
    "50300731":
        "WasteDisposal SolidWasteDisposalIndustrial WastewaterTreatment DiffusedAirActivatedSludge",
    "50300732":
        "WasteDisposal SolidWasteDisposalIndustrial WastewaterTreatment MechanicalMixAirActivatedSludge",
    "50300734":
        "WasteDisposal SolidWasteDisposalIndustrial WastewaterTreatment TricklingFilter",
    "50300740":
        "WasteDisposal SolidWasteDisposalIndustrial WastewaterTreatment Clarifier",
    "50300769":
        "WasteDisposal SolidWasteDisposalIndustrial WastewaterTreatment StorageBasinorOpenTank",
    "50300781":
        "WasteDisposal SolidWasteDisposalIndustrial WastewaterTreatment SludgeDigester",
    "50300783":
        "WasteDisposal SolidWasteDisposalIndustrial WastewaterTreatment SludgeCentrifuge",
    "50300789":
        "WasteDisposal SolidWasteDisposalIndustrial WastewaterTreatment SludgeDigesterGasFlare",
    "50300799":
        "WasteDisposal SolidWasteDisposalIndustrial WastewaterTreatment OtherNotElsewhereClassified",
    "50300801":
        "WasteDisposal SolidWasteDisposalIndustrial TreatmentStorageDisposalTSDF SurfaceImpoundmentFugitiveEmissions",
    "50300810":
        "WasteDisposal SolidWasteDisposalIndustrial TreatmentStorageDisposalTSDF WastePilesFugitiveEmissions",
    "50300820":
        "WasteDisposal SolidWasteDisposalIndustrial TreatmentStorageDisposalTSDF LandTreatmentFugitiveEmissions",
    "50300830":
        "WasteDisposal SolidWasteDisposalIndustrial TreatmentStorageDisposalTSDF ContainersFugitiveEmissions",
    "50300899":
        "WasteDisposal SolidWasteDisposalIndustrial TreatmentStorageDisposalTSDF GeneralFugitiveEmissions",
    "50300901":
        "WasteDisposal SolidWasteDisposalIndustrial AsbestosRemoval General",
    "50301101":
        "WasteDisposal SolidWasteDisposalIndustrial SewageSludgeIncineration Incinerator",
    "50301102":
        "WasteDisposal SolidWasteDisposalIndustrial SewageSludgeIncineration MultipleHearthIncinerator",
    "50301103":
        "WasteDisposal SolidWasteDisposalIndustrial SewageSludgeIncineration FluidizedBedCombustor",
    "50380001":
        "WasteDisposal SolidWasteDisposalIndustrial EquipmentLeaks EquipmentLeaks",
    "50382001":
        "WasteDisposal SolidWasteDisposalIndustrial WastewaterAggregate ProcessAreaDrains",
    "50382002":
        "WasteDisposal SolidWasteDisposalIndustrial WastewaterAggregate ProcessEquipmentDrains",
    "50382501":
        "WasteDisposal SolidWasteDisposalIndustrial WastewaterPointsofGeneration LiquidInjectionIncinerator",
    "50382599":
        "WasteDisposal SolidWasteDisposalIndustrial WastewaterPointsofGeneration SpecifyPointofGeneration",
    "50390002":
        "WasteDisposal SolidWasteDisposalIndustrial AuxillaryFuelNoEmissions Coal",
    "50390005":
        "WasteDisposal SolidWasteDisposalIndustrial AuxillaryFuelNoEmissions DistillateOil",
    "50390006":
        "WasteDisposal SolidWasteDisposalIndustrial AuxillaryFuelNoEmissions NaturalGas",
    "50390007":
        "WasteDisposal SolidWasteDisposalIndustrial AuxillaryFuelNoEmissions ProcessGas",
    "50390010":
        "WasteDisposal SolidWasteDisposalIndustrial AuxillaryFuelNoEmissions LiquifiedPetroleumGasLPG",
    "50400101":
        "WasteDisposal SiteRemediation GeneralProcesses FixedRoofTanksBreathingLoss",
    "50400102":
        "WasteDisposal SiteRemediation GeneralProcesses FixedRoofTanksWorkingLoss",
    "50400103":
        "WasteDisposal SiteRemediation GeneralProcesses FloatRoofTanksStandingLoss",
    "50400151":
        "WasteDisposal SiteRemediation GeneralProcesses LiquidWasteGeneralTransfer",
    "50400201":
        "WasteDisposal SiteRemediation GeneralProcesses Miscellaneous",
    "50400301":
        "WasteDisposal SiteRemediation GeneralProcesses OpenRefuseStockpilesGeneral",
    "50400303":
        "WasteDisposal SiteRemediation GeneralProcesses RefuseLoadingGeneral",
    "50400320":
        "WasteDisposal SiteRemediation GeneralProcesses StorageBinsSolidWaste",
    "50410001":
        "WasteDisposal SiteRemediation ExcavationSoilsHandling Excavation",
    "50410002":
        "WasteDisposal SiteRemediation ExcavationSoilsHandling ExcavationBackhoes",
    "50410004":
        "WasteDisposal SiteRemediation ExcavationSoilsHandling ExcavationBulldozers",
    "50410005":
        "WasteDisposal SiteRemediation ExcavationSoilsHandling ExcavationScrapers",
    "50410010":
        "WasteDisposal SiteRemediation ExcavationSoilsHandling Transport",
    "50410020":
        "WasteDisposal SiteRemediation ExcavationSoilsHandling Dumping",
    "50410021":
        "WasteDisposal SiteRemediation ExcavationSoilsHandling DumpingMachineryintoTruck",
    "50410022":
        "WasteDisposal SiteRemediation ExcavationSoilsHandling DumpingTrucksontoStoragePiles",
    "50410030":
        "WasteDisposal SiteRemediation ExcavationSoilsHandling Storage",
    "50410040":
        "WasteDisposal SiteRemediation ExcavationSoilsHandling Grading",
    "50410101":
        "WasteDisposal SiteRemediation StabilizationSolidification Drying",
    "50410110":
        "WasteDisposal SiteRemediation StabilizationSolidification Mixing",
    "50410111":
        "WasteDisposal SiteRemediation StabilizationSolidification MixingBinsLoading",
    "50410112":
        "WasteDisposal SiteRemediation StabilizationSolidification MixingBinsUnloading",
    "50410120":
        "WasteDisposal SiteRemediation StabilizationSolidification Process",
    "50410210":
        "WasteDisposal SiteRemediation Capping Capping",
    "50410211":
        "WasteDisposal SiteRemediation Capping SyntheticMembrane",
    "50410212":
        "WasteDisposal SiteRemediation Capping LowPermeabilitySoil",
    "50410213":
        "WasteDisposal SiteRemediation Capping SoilBentoniteAdmixtures",
    "50410216":
        "WasteDisposal SiteRemediation Capping MultilayerCover",
    "50410310":
        "WasteDisposal SiteRemediation InSituVentingVentingofSoils ActiveAeration",
    "50410311":
        "WasteDisposal SiteRemediation InSituVentingVentingofSoils ActiveAerationVacuum",
    "50410312":
        "WasteDisposal SiteRemediation InSituVentingVentingofSoils ActiveAerationVacuumVaporRecoveryWell",
    "50410313":
        "WasteDisposal SiteRemediation InSituVentingVentingofSoils ActiveAerationVacuumVacuumSystem",
    "50410314":
        "WasteDisposal SiteRemediation InSituVentingVentingofSoils ActiveAerationVacuumControlDevice",
    "50410321":
        "WasteDisposal SiteRemediation InSituVentingVentingofSoils ActiveAerationForcedAirPositivePressure",
    "50410322":
        "WasteDisposal SiteRemediation InSituVentingVentingofSoils ActiveAerationForcedAirPositivePressureTreatmentUnit",
    "50410405":
        "WasteDisposal SiteRemediation AirStrippingofGroundwater OilWaterSeparator",
    "50410406":
        "WasteDisposal SiteRemediation AirStrippingofGroundwater StorageSurgeTanks",
    "50410408":
        "WasteDisposal SiteRemediation AirStrippingofGroundwater TreatmentTanks",
    "50410409":
        "WasteDisposal SiteRemediation AirStrippingofGroundwater Conduits",
    "50410420":
        "WasteDisposal SiteRemediation AirStrippingofGroundwater AirStrippingTower",
    "50410510":
        "WasteDisposal SiteRemediation ThermalDestruction WastePreparation",
    "50410513":
        "WasteDisposal SiteRemediation ThermalDestruction WastePreparationShredding",
    "50410520":
        "WasteDisposal SiteRemediation ThermalDestruction WasteFeedSystem",
    "50410523":
        "WasteDisposal SiteRemediation ThermalDestruction WasteFeedSystemAuger",
    "50410530":
        "WasteDisposal SiteRemediation ThermalDestruction CombustionUnit",
    "50410534":
        "WasteDisposal SiteRemediation ThermalDestruction CombustionUnitFluidizedBedIncinerator",
    "50410535":
        "WasteDisposal SiteRemediation ThermalDestruction CombustionUnitRotaryKiln",
    "50410538":
        "WasteDisposal SiteRemediation ThermalDestruction CombustionUnitPyrolysis",
    "50410541":
        "WasteDisposal SiteRemediation ThermalDestruction CombustionUnitPlasmaArc",
    "50410560":
        "WasteDisposal SiteRemediation ThermalDestruction WasteDisposal",
    "50410561":
        "WasteDisposal SiteRemediation ThermalDestruction WasteDisposalDewatering",
    "50410563":
        "WasteDisposal SiteRemediation ThermalDestruction WasteDisposalLandfill",
    "50410620":
        "WasteDisposal SiteRemediation ThermalDesorption ThermalDesorber",
    "50410621":
        "WasteDisposal SiteRemediation ThermalDesorption ThermalDesorberIndirectHeatTransfer",
    "50410640":
        "WasteDisposal SiteRemediation ThermalDesorption Wastes",
    "50410644":
        "WasteDisposal SiteRemediation ThermalDesorption WastesWastePiles",
    "50410710":
        "WasteDisposal SiteRemediation BiologicalTreatment Biooxidation",
    "50410712":
        "WasteDisposal SiteRemediation BiologicalTreatment BiooxidationMicrobialAerobicBiosolubilization",
    "50410720":
        "WasteDisposal SiteRemediation BiologicalTreatment AnaerobicBiodegradation",
    "50410721":
        "WasteDisposal SiteRemediation BiologicalTreatment AnaerobicBiodegradationDigester",
    "50410722":
        "WasteDisposal SiteRemediation BiologicalTreatment AnaerobicBiodegradationActivatedSludgeSystem",
    "50410725":
        "WasteDisposal SiteRemediation BiologicalTreatment AnaerobicBiodegradationFluidizedBedBioreactors",
    "50410740":
        "WasteDisposal SiteRemediation BiologicalTreatment SurfaceBioremediation",
    "50410760":
        "WasteDisposal SiteRemediation BiologicalTreatment Bioreactors",
    "50410761":
        "WasteDisposal SiteRemediation BiologicalTreatment BioreactorsActivatedSludge",
    "50410763":
        "WasteDisposal SiteRemediation BiologicalTreatment BioreactorsSequencingBatch",
    "50410780":
        "WasteDisposal SiteRemediation BiologicalTreatment InSituBioremediation",
    "50480001":
        "WasteDisposal SiteRemediation EquipmentLeaks EquipmentLeaks",
    "50482001":
        "WasteDisposal SiteRemediation WastewaterAggregate ProcessAreaDrains",
    "50482002":
        "WasteDisposal SiteRemediation WastewaterAggregate ProcessEquipmentDrains",
    "50482599":
        "WasteDisposal SiteRemediation WastewaterPointsofGeneration SpecifyPointofGeneration",
    "50490004":
        "WasteDisposal SiteRemediation GeneralProcesses IncineratorsProcessGas",
    "50600101":
        "WasteDisposal SolidWasteDisposalCommercial Incineration ConicalDesignTeePeeMunicipalRefuseWoodRefuse",
    "50600102":
        "WasteDisposal SolidWasteDisposalCommercial Incineration IncineratorSingleChamber",
    "50600103":
        "WasteDisposal SolidWasteDisposalCommercial Incineration IncineratorDualChamber",
    "50600106":
        "WasteDisposal SolidWasteDisposalCommercial Incineration IncineratorBurnBox",
    "50600110":
        "WasteDisposal SolidWasteDisposalCommercial Incineration ModularStarvedAirCombustor",
    "50600111":
        "WasteDisposal SolidWasteDisposalCommercial Incineration ModularExcessAirCombustor",
    "50600117":
        "WasteDisposal SolidWasteDisposalCommercial Incineration SmallRemoteIncineratorburnslessthan3tonsdayCyclonicBurnBarrel",
    "50600121":
        "WasteDisposal SolidWasteDisposalCommercial Incineration BurnOffOvenRackReclamationUnit",
    "50600201":
        "WasteDisposal SolidWasteDisposalCommercial HospitalMedicalInfectiousWasteIncinerationHMIWI IncineratorChemotherapeuticWaste",
    "50600202":
        "WasteDisposal SolidWasteDisposalCommercial HospitalMedicalInfectiousWasteIncinerationHMIWI IncineratorLowlevelRadioactiveWaste",
    "50600203":
        "WasteDisposal SolidWasteDisposalCommercial HospitalMedicalInfectiousWasteIncinerationHMIWI IncineratorPathologicalWaste",
    "50600204":
        "WasteDisposal SolidWasteDisposalCommercial HospitalMedicalInfectiousWasteIncinerationHMIWI IncineratorHospitalMedicalInfectiousWasteCofiredwithOtherWaste",
    "50600207":
        "WasteDisposal SolidWasteDisposalCommercial HospitalMedicalInfectiousWasteIncinerationHMIWI SmallRurallocatedmorethan50milesfromMSA&burnslessthan2000lbweekwasteBatchModularStarvedAirCombustor",
    "50600208":
        "WasteDisposal SolidWasteDisposalCommercial HospitalMedicalInfectiousWasteIncinerationHMIWI SmallRurallocatedmorethan50milesfromMSA&burnslessthan2000lbweekwasteBatchRotaryKiln",
    "50600265":
        "WasteDisposal SolidWasteDisposalCommercial HospitalMedicalInfectiousWasteIncinerationHMIWI Largemorethan500lbshror4000lbdaybatchIncinerator",
    "50600601":
        "WasteDisposal SolidWasteDisposalCommercial MunicipalSolidWasteLandfill FugitiveEmissions",
    "50600602":
        "WasteDisposal SolidWasteDisposalCommercial MunicipalSolidWasteLandfill HazardousFugitiveEmissions",
    "50600603":
        "WasteDisposal SolidWasteDisposalCommercial MunicipalSolidWasteLandfill UnpavedRoadTraffic",
    "50600607":
        "WasteDisposal SolidWasteDisposalCommercial MunicipalSolidWasteLandfill GasCollectionSystemOtherNotElsewhereClassified",
    "50600611":
        "WasteDisposal SolidWasteDisposalCommercial MunicipalSolidWasteLandfill LandfillGasLFGDestructionOtherNotElsewhereClassified",
    "50600642":
        "WasteDisposal SolidWasteDisposalCommercial MunicipalSolidWasteLandfill ConveyingofCoverMaterial",
    "50600701":
        "WasteDisposal SolidWasteDisposalCommercial SewageSludgeIncineration Incinerator",
    "50600702":
        "WasteDisposal SolidWasteDisposalCommercial SewageSludgeIncineration MultipleHearthIncinerator",
    "50600703":
        "WasteDisposal SolidWasteDisposalCommercial SewageSludgeIncineration FluidizedBedCombustor",
    "50682003":
        "WasteDisposal SolidWasteDisposalCommercial WastewaterTreatment Drain",
    "50682005":
        "WasteDisposal SolidWasteDisposalCommercial WastewaterTreatment AeratedImpoundment",
    "50682099":
        "WasteDisposal SolidWasteDisposalCommercial WastewaterTreatment OtherNotElsewhereClassified",
    "50700203":
        "WasteDisposal SolidWasteDisposalInstitutional HospitalMedicalInfectiousWasteIncinerationHMIWI IncineratorPathologicalWaste",
    "50700204":
        "WasteDisposal SolidWasteDisposalInstitutional HospitalMedicalInfectiousWasteIncinerationHMIWI IncineratorHospitalMedicalInfectiousWasteCofiredwithOtherWaste",
    "50700219":
        "WasteDisposal SolidWasteDisposalInstitutional HospitalMedicalInfectiousWasteIncinerationHMIWI SmallRurallocatedmorethan50milesfromMSA&burnslessthan2000lbweekwasteModularStarvedAirCombustor",
    "50700259":
        "WasteDisposal SolidWasteDisposalInstitutional HospitalMedicalInfectiousWasteIncinerationHMIWI Largemorethan500lbshror4000lbdaybatchContinuousModularStarvedAirCombustor",
    "62540023":
        "MACTSourceCategories FoodandAgriculturalProcesses CelluloseFoodCasingManufacture ViscoseProcessingRegeneration",
    "62540024":
        "MACTSourceCategories FoodandAgriculturalProcesses CelluloseFoodCasingManufacture ViscoseProcessingWaterWashing",
    "62540025":
        "MACTSourceCategories FoodandAgriculturalProcesses CelluloseFoodCasingManufacture DryingandHumidification",
    "62540030":
        "MACTSourceCategories FoodandAgriculturalProcesses CelluloseFoodCasingManufacture MPOperation",
    "62580001":
        "MACTSourceCategories FoodandAgriculturalProcesses EquipmentLeaks EquipmentLeaks",
    "62582501":
        "MACTSourceCategories FoodandAgriculturalProcesses WastewaterPointsofGeneration ViscoseFiltering",
    "62582503":
        "MACTSourceCategories FoodandAgriculturalProcesses WastewaterPointsofGeneration AcidBathEvaporator",
    "62582599":
        "MACTSourceCategories FoodandAgriculturalProcesses WastewaterPointsofGeneration SpecifyPointofGeneration",
    "63111001":
        "MACTSourceCategories AgriculturalChemicalsProduction 24DSaltsandEstersProduction 24DSaltsandEstersProduction",
    "63125012":
        "MACTSourceCategories AgriculturalChemicalsProduction CaptanProduction ProcessVentsCaptanUnitHoldingVessel",
    "63131001":
        "MACTSourceCategories AgriculturalChemicalsProduction ChlorothalonilProduction ChlorothalonilProduction",
    "63131013":
        "MACTSourceCategories AgriculturalChemicalsProduction ChlorothalonilProduction ProcessVentsReactor",
    "63131018":
        "MACTSourceCategories AgriculturalChemicalsProduction ChlorothalonilProduction ProcessVentsProductPackaging",
    "63134013":
        "MACTSourceCategories AgriculturalChemicalsProduction DacthalProduction ProcessVentsThermalChlorinationReactor",
    "63134027":
        "MACTSourceCategories AgriculturalChemicalsProduction DacthalProduction ProcessVentsFormulationGrindingTanks",
    "63134037":
        "MACTSourceCategories AgriculturalChemicalsProduction DacthalProduction ProcessVentsFormulationPackagingSolids",
    "63134077":
        "MACTSourceCategories AgriculturalChemicalsProduction DacthalProduction ProcessTanksProductPackagingTanks",
    "63182002":
        "MACTSourceCategories AgriculturalChemicalsProduction WastewaterAggregate ProcessEquipmentDrains",
    "63182501":
        "MACTSourceCategories AgriculturalChemicalsProduction WastewaterPointsofGeneration 24DRecovery",
    "63182582":
        "MACTSourceCategories AgriculturalChemicalsProduction WastewaterPointsofGeneration DissolveResidueinWater",
    "63182599":
        "MACTSourceCategories AgriculturalChemicalsProduction WastewaterPointsofGeneration SpecifyPointofGeneration",
    "64130001":
        "MACTSourceCategories StyreneorMethacrylateBasedResins PolymethylMethacrylateProdBulkPolymerizationBatchcellMethod PolymethylMethacrylateResinsBulkBatchCellProcess",
    "64130010":
        "MACTSourceCategories StyreneorMethacrylateBasedResins PolymethylMethacrylateProdBulkPolymerizationBatchcellMethod ProcessVentsBulkBatchCellProcess",
    "64130011":
        "MACTSourceCategories StyreneorMethacrylateBasedResins PolymethylMethacrylateProdBulkPolymerizationBatchcellMethod ProcessVentsReactor",
    "64130101":
        "MACTSourceCategories StyreneorMethacrylateBasedResins PolymethylMethacrylateProdBulkPolymerizationContinuousCasting PolymethylMethacrylateResinsBulkContinuousProcess",
    "64130211":
        "MACTSourceCategories StyreneorMethacrylateBasedResins PolymethylMethacrylateProdBulkPolymeriznCentrifugalPolymerizn ProcessVentsReactor",
    "64131001":
        "MACTSourceCategories StyreneorMethacrylateBasedResins PolymethylMethacrylateProdSolutionPolymerization PolymethylMethacrylateResinsSolventProcess",
    "64131020":
        "MACTSourceCategories StyreneorMethacrylateBasedResins PolymethylMethacrylateProdSolutionPolymerization ProcessVentsDryer",
    "64132001":
        "MACTSourceCategories StyreneorMethacrylateBasedResins PolymethylMethacrylateProdEmulsionPolymerization PolymethylMethacrylateResinsEmulsionProcess",
    "64132030":
        "MACTSourceCategories StyreneorMethacrylateBasedResins PolymethylMethacrylateProdEmulsionPolymerization ProcessVentsProductStorage",
    "64133001":
        "MACTSourceCategories StyreneorMethacrylateBasedResins PolymethylMethacrylateProdSuspensionPolymerization PolymethylMethacrylateResinsSuspensionProcess",
    "64133020":
        "MACTSourceCategories StyreneorMethacrylateBasedResins PolymethylMethacrylateProdSuspensionPolymerization ProcessVentsSeparationFiltration",
    "64133025":
        "MACTSourceCategories StyreneorMethacrylateBasedResins PolymethylMethacrylateProdSuspensionPolymerization ProcessVentsDryer",
    "64180001":
        "MACTSourceCategories StyreneorMethacrylateBasedResins EquipmentLeaks EquipmentLeaks",
    "64182001":
        "MACTSourceCategories StyreneorMethacrylateBasedResins WastewaterAggregate ProcessAreaDrains",
    "64420033":
        "MACTSourceCategories CellulosebasedResins CarboxymethylcelluloseProduction ProductFinishingPurificationExtraction",
    "64431017":
        "MACTSourceCategories CellulosebasedResins MethylCelluloseProductionLiquidMethylChlorideProcess ProcessVentsSolventRecovery",
    "64450011":
        "MACTSourceCategories CellulosebasedResins CelluloseEthersProduction AlkalizationSodiumHydroxideBath",
    "64470001":
        "MACTSourceCategories CellulosebasedResins CellophaneManufacturing CellophaneManufacturing",
    "64470010":
        "MACTSourceCategories CellulosebasedResins CellophaneManufacturing ProductionofViscoseSolution",
    "64470040":
        "MACTSourceCategories CellulosebasedResins CellophaneManufacturing CoatingOperations",
    "64480001":
        "MACTSourceCategories CellulosebasedResins EquipmentLeaks EquipmentLeaks",
    "64482002":
        "MACTSourceCategories CellulosebasedResins WastewaterAggregate ProcessEquipmentDrains",
    "64520001":
        "MACTSourceCategories MiscellaneousResins AlkydResinProductionSolventProcess AlkydProductionSolventProcess",
    "64520010":
        "MACTSourceCategories MiscellaneousResins AlkydResinProductionSolventProcess PolymerizationReaction",
    "64520011":
        "MACTSourceCategories MiscellaneousResins AlkydResinProductionSolventProcess PolymerizationReactionKettle",
    "64520020":
        "MACTSourceCategories MiscellaneousResins AlkydResinProductionSolventProcess ProductFinishing",
    "64520021":
        "MACTSourceCategories MiscellaneousResins AlkydResinProductionSolventProcess ProductFinishingThinningVessels",
    "64520022":
        "MACTSourceCategories MiscellaneousResins AlkydResinProductionSolventProcess ProductFinishingFilter",
    "64520023":
        "MACTSourceCategories MiscellaneousResins AlkydResinProductionSolventProcess ProductFinishingIntermediateStorage",
    "64520030":
        "MACTSourceCategories MiscellaneousResins AlkydResinProductionSolventProcess SolventRecovery",
    "64520031":
        "MACTSourceCategories MiscellaneousResins AlkydResinProductionSolventProcess SolventRecoveryDecanter",
    "64520040":
        "MACTSourceCategories MiscellaneousResins AlkydResinProductionSolventProcess EndProductStorage",
    "64520041":
        "MACTSourceCategories MiscellaneousResins AlkydResinProductionSolventProcess EndProductStorageDrumandBulkLoading",
    "64521001":
        "MACTSourceCategories MiscellaneousResins AlkydResinProductionFusionProcess AlkydProductionFusionProcess",
    "64521010":
        "MACTSourceCategories MiscellaneousResins AlkydResinProductionFusionProcess PolymerizationReaction",
    "64521011":
        "MACTSourceCategories MiscellaneousResins AlkydResinProductionFusionProcess PolymerizationReactionKettle",
    "64521020":
        "MACTSourceCategories MiscellaneousResins AlkydResinProductionFusionProcess ProductFinishing",
    "64521021":
        "MACTSourceCategories MiscellaneousResins AlkydResinProductionFusionProcess ProductFinishingThinningVessels",
    "64521041":
        "MACTSourceCategories MiscellaneousResins AlkydResinProductionFusionProcess EndProductStorageDrumandBulkLoading",
    "64580001":
        "MACTSourceCategories MiscellaneousResins EquipmentLeaks EquipmentLeaks",
    "64582002":
        "MACTSourceCategories MiscellaneousResins WastewaterAggregate ProcessEquipmentDrains",
    "64582599":
        "MACTSourceCategories MiscellaneousResins WastewaterPointsofGeneration SpecifyPointofGeneration",
    "64610010":
        "MACTSourceCategories VinylbasedResins PolymerizedVinylideneChlorideProductionEmulsionLatexProd. RawMaterialPreparation",
    "64610011":
        "MACTSourceCategories VinylbasedResins PolymerizedVinylideneChlorideProductionEmulsionLatexProd. RawMaterialPreparationRawWeighingandHoldingTanks",
    "64610012":
        "MACTSourceCategories VinylbasedResins PolymerizedVinylideneChlorideProductionEmulsionLatexProd. RawMaterialPreparationRawMaterialLoadingLines",
    "64610020":
        "MACTSourceCategories VinylbasedResins PolymerizedVinylideneChlorideProductionEmulsionLatexProd. Polymerization",
    "64610021":
        "MACTSourceCategories VinylbasedResins PolymerizedVinylideneChlorideProductionEmulsionLatexProd. PolymerizationReactorOpeningLoss",
    "64610031":
        "MACTSourceCategories VinylbasedResins PolymerizedVinylideneChlorideProductionEmulsionLatexProd. MaterialRecoveryStrippingVessel",
    "64610040":
        "MACTSourceCategories VinylbasedResins PolymerizedVinylideneChlorideProductionEmulsionLatexProd. ProductFinishing",
    "64610041":
        "MACTSourceCategories VinylbasedResins PolymerizedVinylideneChlorideProductionEmulsionLatexProd. ProductFinishingPolymerHoldingTanks",
    "64610050":
        "MACTSourceCategories VinylbasedResins PolymerizedVinylideneChlorideProductionEmulsionLatexProd. EndProductStorage",
    "64610201":
        "MACTSourceCategories VinylbasedResins PolymerizedVinylideneChlorideProductionSuspension PolymerizedVinylideneChlorideProductionSuspensionPolymerization",
    "64610220":
        "MACTSourceCategories VinylbasedResins PolymerizedVinylideneChlorideProductionSuspension Polymerization",
    "64610221":
        "MACTSourceCategories VinylbasedResins PolymerizedVinylideneChlorideProductionSuspension PolymerizationReactorOpeningLoss",
    "64615010":
        "MACTSourceCategories VinylbasedResins PolyvinylAcetateEmulsionsBatchEmulsionProcess Polymerization",
    "64620013":
        "MACTSourceCategories VinylbasedResins PolyvinylAlcoholProductionSolutionPolymerization RawMaterialPreparationPurifiedUninhibitedVAMDayStorageTank",
    "64620020":
        "MACTSourceCategories VinylbasedResins PolyvinylAlcoholProductionSolutionPolymerization ProductFinishing",
    "64630001":
        "MACTSourceCategories VinylbasedResins PolyvinylChlorideandCopolymersProductionSuspensionProcess PVCandCopolymersProductionSuspensionProcess",
    "64630010":
        "MACTSourceCategories VinylbasedResins PolyvinylChlorideandCopolymersProductionSuspensionProcess ProcessVentsSuspensionProcess",
    "64630012":
        "MACTSourceCategories VinylbasedResins PolyvinylChlorideandCopolymersProductionSuspensionProcess ProcessVentsWeightTanks",
    "64630015":
        "MACTSourceCategories VinylbasedResins PolyvinylChlorideandCopolymersProductionSuspensionProcess ProcessVentsReactorOpeningLoss",
    "64630025":
        "MACTSourceCategories VinylbasedResins PolyvinylChlorideandCopolymersProductionSuspensionProcess ProcessVentsStripperVinylChlorideStrippedfromPolymertoAtmos",
    "64630030":
        "MACTSourceCategories VinylbasedResins PolyvinylChlorideandCopolymersProductionSuspensionProcess ProcessVentsSlurryBlendTank",
    "64630035":
        "MACTSourceCategories VinylbasedResins PolyvinylChlorideandCopolymersProductionSuspensionProcess ProcessVentsCentrifuge",
    "64630040":
        "MACTSourceCategories VinylbasedResins PolyvinylChlorideandCopolymersProductionSuspensionProcess ProcessVentsDirectRotaryDryer[forindirectUSE64630043]",
    "64630041":
        "MACTSourceCategories VinylbasedResins PolyvinylChlorideandCopolymersProductionSuspensionProcess ProcessVentsFlashDryer",
    "64630050":
        "MACTSourceCategories VinylbasedResins PolyvinylChlorideandCopolymersProductionSuspensionProcess ProcessVentsSiloStorage",
    "64630051":
        "MACTSourceCategories VinylbasedResins PolyvinylChlorideandCopolymersProductionSuspensionProcess ProcessVentsBaggerAreaMachines",
    "64630052":
        "MACTSourceCategories VinylbasedResins PolyvinylChlorideandCopolymersProductionSuspensionProcess ProcessVentsBaggerAreaResinTransfer",
    "64630053":
        "MACTSourceCategories VinylbasedResins PolyvinylChlorideandCopolymersProductionSuspensionProcess ProcessVentsBulkLoading",
    "64630080":
        "MACTSourceCategories VinylbasedResins PolyvinylChlorideandCopolymersProductionSuspensionProcess FugitiveEmissions",
    "64630082":
        "MACTSourceCategories VinylbasedResins PolyvinylChlorideandCopolymersProductionSuspensionProcess FugitiveEmissionsOpeningofEquipmentforInspectionorMaintenance",
    "64631001":
        "MACTSourceCategories VinylbasedResins PolyvinylChlorideandCopolymersProductionDispersionProcess PVCandCopolymersProductionDispersionProcess",
    "64631040":
        "MACTSourceCategories VinylbasedResins PolyvinylChlorideandCopolymersProductionDispersionProcess ProcessVentsSprayDryer",
    "64631050":
        "MACTSourceCategories VinylbasedResins PolyvinylChlorideandCopolymersProductionDispersionProcess ProcessVentsSiloStorage",
    "64631052":
        "MACTSourceCategories VinylbasedResins PolyvinylChlorideandCopolymersProductionDispersionProcess ProcessVentsBaggerAreaResinTransfer",
    "64632010":
        "MACTSourceCategories VinylbasedResins PolyvinylChlorideandCopolymersProductionSolventProcess ProcessVentsSolventProcess",
    "64632030":
        "MACTSourceCategories VinylbasedResins PolyvinylChlorideandCopolymersProductionSolventProcess ProcessVentsDirectDryer[forIndirectDryerUSE64632031]",
    "64632040":
        "MACTSourceCategories VinylbasedResins PolyvinylChlorideandCopolymersProductionSolventProcess ProcessVentsProductFilterorSieve",
    "64632082":
        "MACTSourceCategories VinylbasedResins PolyvinylChlorideandCopolymersProductionSolventProcess FugitiveEmissionsOpeningofEquipmentforInspectionorMaintenance",
    "64633020":
        "MACTSourceCategories VinylbasedResins PolyvinylChlorideandCopolymersProductionBulkProcess ProcessVentsPolymerizationReactorSafetyValveVents",
    "64633080":
        "MACTSourceCategories VinylbasedResins PolyvinylChlorideandCopolymersProductionBulkProcess EquipmentLeaks[Seealso6463308485or86]",
    "64682001":
        "MACTSourceCategories VinylbasedResins WastewaterAggregate ProcessAreaDrains",
    "64682502":
        "MACTSourceCategories VinylbasedResins WastewaterPointsofGeneration ReactorCleaning",
    "64820001":
        "MACTSourceCategories MiscellaneousPolymers MaleicAnhydrideCopolymersProductionBulkPolymerization MaleicAnhydrideCopolymerProductionBulkPolymerization",
    "64821010":
        "MACTSourceCategories MiscellaneousPolymers MaleicAnhydrideCopolymersProductionSolutionPolymerization ProcessVentsSolutionProcess",
    "64822001":
        "MACTSourceCategories MiscellaneousPolymers MaleicAnhydrideCopolymersProductionEmulsionPolymerization MaleicAnhydrideCopolymerProductionEmulsionPolymerization",
    "64822010":
        "MACTSourceCategories MiscellaneousPolymers MaleicAnhydrideCopolymersProductionEmulsionPolymerization ProcessVentsEmulsionProcess",
    "64880001":
        "MACTSourceCategories MiscellaneousPolymers EquipmentLeaks EquipmentLeaks",
    "64920001":
        "MACTSourceCategories FibersProductionProcesses RayonFiberProduction RayonProduction",
    "64920021":
        "MACTSourceCategories FibersProductionProcesses RayonFiberProduction FilamentFormationSpinningMachine",
    "64980001":
        "MACTSourceCategories FibersProductionProcesses EquipmentLeaks EquipmentLeaks",
    "64982599":
        "MACTSourceCategories FibersProductionProcesses WastewaterPointsofGeneration SpecifyPointofGeneration",
    "65110021":
        "MACTSourceCategories InorganicChemicalsManufacturing AntimonyOxidesManufacturing RecoveryBaghouse",
    "65130001":
        "MACTSourceCategories InorganicChemicalsManufacturing FumedSilicaManufacturing FumedSilicaProduction",
    "65130010":
        "MACTSourceCategories InorganicChemicalsManufacturing FumedSilicaManufacturing ProcessVents",
    "65140001":
        "MACTSourceCategories InorganicChemicalsManufacturing SodiumCyanideManufacturing SodiumCyanideProduction",
    "65140010":
        "MACTSourceCategories InorganicChemicalsManufacturing SodiumCyanideManufacturing ProcessVents",
    "65140013":
        "MACTSourceCategories InorganicChemicalsManufacturing SodiumCyanideManufacturing ProcessVentsFiltration",
    "65140015":
        "MACTSourceCategories InorganicChemicalsManufacturing SodiumCyanideManufacturing ProcessVentsDrying",
    "65140018":
        "MACTSourceCategories InorganicChemicalsManufacturing SodiumCyanideManufacturing ProcessVentsBriquetting",
    "65145001":
        "MACTSourceCategories InorganicChemicalsManufacturing UraniumHexafluorideManufacturing UraniumHexafluorideProductionDirectFluorination",
    "65145020":
        "MACTSourceCategories InorganicChemicalsManufacturing UraniumHexafluorideManufacturing ProductFinishing",
    "65180001":
        "MACTSourceCategories InorganicChemicalsManufacturing EquipmentLeaks EquipmentLeaks",
    "65182001":
        "MACTSourceCategories InorganicChemicalsManufacturing WastewaterAggregate ProcessAreaDrains",
    "65182501":
        "MACTSourceCategories InorganicChemicalsManufacturing WastewaterPointsofGeneration Filtration",
    "68110001":
        "MACTSourceCategories ConsumerProductManufacturingFacilities AerosolCanFillingFacilities AerosolCanFilling",
    "68110010":
        "MACTSourceCategories ConsumerProductManufacturingFacilities AerosolCanFillingFacilities ProcessVents",
    "68110011":
        "MACTSourceCategories ConsumerProductManufacturingFacilities AerosolCanFillingFacilities ProcessVentsMixingTanks",
    "68110020":
        "MACTSourceCategories ConsumerProductManufacturingFacilities AerosolCanFillingFacilities ProcessVentsAerosolCanFilling",
    "68110021":
        "MACTSourceCategories ConsumerProductManufacturingFacilities AerosolCanFillingFacilities ProcessVentsAerosolCanFillingProductFilling",
    "68110022":
        "MACTSourceCategories ConsumerProductManufacturingFacilities AerosolCanFillingFacilities ProcessVentsAerosolCanFillingValveStemandValveInsertion",
    "68110023":
        "MACTSourceCategories ConsumerProductManufacturingFacilities AerosolCanFillingFacilities ProcessVentsAerosolCanFillingPropellantCharging",
    "68110024":
        "MACTSourceCategories ConsumerProductManufacturingFacilities AerosolCanFillingFacilities ProcessVentsAerosolCanFillingSealingProductionCan",
    "68110030":
        "MACTSourceCategories ConsumerProductManufacturingFacilities AerosolCanFillingFacilities ProcessVentsWaterBathLeakCheck",
    "68110035":
        "MACTSourceCategories ConsumerProductManufacturingFacilities AerosolCanFillingFacilities ProcessVentsCanWashing",
    "68180001":
        "MACTSourceCategories ConsumerProductManufacturingFacilities EquipmentLeaks EquipmentLeaks",
    "68182599":
        "MACTSourceCategories ConsumerProductManufacturingFacilities WastewaterPointsofGeneration SpecifyPointofGeneration",
    "68240030":
        "MACTSourceCategories MiscellaneousProcesses PaintStripperUsersChemicalStrippers ApplicationDegradationandCoatingRemovalSteps",
    "68240031":
        "MACTSourceCategories MiscellaneousProcesses PaintStripperUsersChemicalStrippers ApplicationDegradationandCoatingRemovalStepsMethyleneChloride",
    "68241001":
        "MACTSourceCategories MiscellaneousProcesses PaintStripperUsersNonchemicalStrippers MediaBlasting",
    "68241002":
        "MACTSourceCategories MiscellaneousProcesses PaintStripperUsersNonchemicalStrippers MediaBlastingPlasticBeadMedia",
    "68241006":
        "MACTSourceCategories MiscellaneousProcesses PaintStripperUsersNonchemicalStrippers MediaBlastingGrit",
    "68241008":
        "MACTSourceCategories MiscellaneousProcesses PaintStripperUsersNonchemicalStrippers MediaBlastingSand",
    "68241030":
        "MACTSourceCategories MiscellaneousProcesses PaintStripperUsersNonchemicalStrippers MediaBlastingOtherNotListed",
    "68241046":
        "MACTSourceCategories MiscellaneousProcesses PaintStripperUsersNonchemicalStrippers CarbonDioxidePulsedLaser",
    "68282001":
        "MACTSourceCategories MiscellaneousProcesses WastewaterAggregate ProcessAreaDrains",
    "68282599":
        "MACTSourceCategories MiscellaneousProcesses WastewaterPointsofGeneration SpecifyPointofGeneration",
    "68430101":
        "MACTSourceCategories MiscellaneousProcessesChemicals ChlorinatedParaffinsProductionContinuousProcess ChlorinatedParaffinsContinuousProcess",
    "68435040":
        "MACTSourceCategories MiscellaneousProcessesChemicals DodecanoicAcidProduction WasteLiquids",
    "68445011":
        "MACTSourceCategories MiscellaneousProcessesChemicals HydrazineProductionOlinRaschigProcess ProcessVentsChlorinationReactor",
    "68445012":
        "MACTSourceCategories MiscellaneousProcessesChemicals HydrazineProductionOlinRaschigProcess ProcessVentsChloramineReactor",
    "68445030":
        "MACTSourceCategories MiscellaneousProcessesChemicals HydrazineProductionOlinRaschigProcess AmmoniaRecoverySystem",
    "68445040":
        "MACTSourceCategories MiscellaneousProcessesChemicals HydrazineProductionOlinRaschigProcess ProductStorage",
    "68445101":
        "MACTSourceCategories MiscellaneousProcessesChemicals HydrazineProductionBayerKetazineProcess HydrazineProductionBayerKetazineProcess",
    "68445211":
        "MACTSourceCategories MiscellaneousProcessesChemicals HydrazineProductionPCUKPeroxideProcess ProcessVentsReactorVessel",
    "68480001":
        "MACTSourceCategories MiscellaneousProcessesChemicals EquipmentLeaks EquipmentLeaks",
    "68482001":
        "MACTSourceCategories MiscellaneousProcessesChemicals WastewaterAggregate ProcessAreaDrains",
    "68482504":
        "MACTSourceCategories MiscellaneousProcessesChemicals WastewaterPointsofGeneration ConcentratorPurge",
    "68482599":
        "MACTSourceCategories MiscellaneousProcessesChemicals WastewaterPointsofGeneration SpecifyPointofGeneration",
    "68510001":
        "MACTSourceCategories MiscellaneousProcessesChemicals PhthalatePlasticizersProduction PhthalatePlasticizerProduction",
    "68510010":
        "MACTSourceCategories MiscellaneousProcessesChemicals PhthalatePlasticizersProduction ProcessVents",
    "2265008005":
        "MobileSources OffhighwayVehicleGasoline AirportGroundSupportEquipment 4StrokeAirportGroundSupportEquipment",
    "2267008005":
        "MobileSources OffhighwayVehicleLPG AirportGroundSupportEquipment LPGAirportGroundSupportEquipment",
    "2268008005":
        "MobileSources OffhighwayVehicleCNG AirportGroundSupportEquipment CNGAirportGroundSupportEquipment",
    "2270008005":
        "MobileSources OffhighwayVehicleDiesel AirportGroundSupportEquipment AirportGroundSupportEquipment",
    "2275001000":
        "MobileSources Aircraft MilitaryAircraft Total",
    "2275020000":
        "MobileSources Aircraft CommercialAircraft TotalAllTypes",
    "2275050011":
        "MobileSources Aircraft GeneralAviation Piston",
    "2275050012":
        "MobileSources Aircraft GeneralAviation Turbine",
    "2275060011":
        "MobileSources Aircraft AirTaxi Piston",
    "2275060012":
        "MobileSources Aircraft AirTaxi Turbine",
    "2275070000":
        "MobileSources Aircraft AircraftAuxiliaryPowerUnits Total",
    "2103008000":
        "StationarySourceFuelCombustion CommercialInstitutional Wood TotalAllBoilerTypes",
    "2102008000":
        "StationarySourceFuelCombustion Industrial Wood TotalAllBoilerTypes",
    "2302002200":
        "IndustrialProcesses FoodandKindredProductsSIC20 CommercialCookingCharbroiling UnderfiredCharbroiling",
    "2302002100":
        "IndustrialProcesses FoodandKindredProductsSIC20 CommercialCookingCharbroiling ConveyorizedCharbroiling",
    "2440020000":
        "SolventUtilization MiscellaneousIndustrial AdhesiveIndustrialApplication TotalAllSolventTypes",
    "2501995000":
        "StorageandTransport PetroleumandPetroleumProductStorage AllStorageTypesWorkingLoss TotalAllProducts",
    "2620030000":
        "WasteDisposalTreatmentandRecovery Landfills Municipal Total",
    "2501060100":
        "StorageandTransport PetroleumandPetroleumProductStorage GasolineServiceStations Stage2Total",
    "2801500330":
        "MiscellaneousAreaSources AgricultureProductionCrops AgriculturalFieldBurningwholefieldsetonfire OrchardCropisApricot",
    "2460800000":
        "SolventUtilization MiscellaneousNonindustrialConsumerandCommercial AllFIFRARelatedProducts TotalAllSolventTypes",
    "2801500100":
        "MiscellaneousAreaSources AgricultureProductionCropsasnonpoint AgriculturalFieldBurningwholefieldsetonfire FieldCropsUnspecified",
    "2460200000":
        "SolventUtilization MiscellaneousNonindustrialConsumerandCommercial AllHouseholdProducts TotalAllSolventTypes",
    "2801500261":
        "MiscellaneousAreaSources AgricultureProductionCrops AgriculturalFieldBurningwholefieldsetonfire FieldCropisWheatHeadfireBurning",
    "2104002000":
        "StationarySourceFuelCombustion Residential BituminousSubbituminousCoal TotalAllCombustorTypes",
    "2102005000":
        "StationarySourceFuelCombustion Industrial ResidualOil TotalAllBoilerTypes",
    "2501060103":
        "StorageandTransport PetroleumandPetroleumProductStorage GasolineServiceStations Stage2Spillage",
    "2801500170":
        "MiscellaneousAreaSources AgricultureProductionCrops AgriculturalFieldBurningwholefieldsetonfire FieldCropisGrassesBurningTechniquesNotImportant",
    "2460600000":
        "SolventUtilization MiscellaneousNonindustrialConsumerandCommercial AllAdhesivesandSealants TotalAllSolventTypes",
    "2801500191":
        "MiscellaneousAreaSources AgricultureProductionCrops AgriculturalFieldBurningwholefieldsetonfire FieldCropisOatsHeadfireBurning",
    "2801500390":
        "MiscellaneousAreaSources AgricultureProductionCrops AgriculturalFieldBurningwholefieldsetonfire OrchardCropisNectarine",
    "2460500000":
        "SolventUtilization MiscellaneousNonindustrialConsumerandCommercial AllCoatingsandRelatedProducts TotalAllSolventTypes",
    "2280002200":
        "MobileSources MarineVesselsCommercial Diesel Underwayemissions",
    "2401002000":
        "SolventUtilization SurfaceCoating ArchitecturalCoatingsSolventbased TotalAllSolventTypes",
    "2801500430":
        "MiscellaneousAreaSources AgricultureProductionCrops AgriculturalFieldBurningwholefieldsetonfire OrchardCropisPrune",
    "2801500111":
        "MiscellaneousAreaSources AgricultureProductionCrops AgriculturalFieldBurningwholefieldsetonfire FieldCropisAlfalfaHeadfireBurning",
    "2801500320":
        "MiscellaneousAreaSources AgricultureProductionCrops AgriculturalFieldBurningwholefieldsetonfire OrchardCropisApple",
    "2460400000":
        "SolventUtilization MiscellaneousNonindustrialConsumerandCommercial AllAutomotiveAftermarketProducts TotalAllSolventTypes",
    "2425040000":
        "SolventUtilization GraphicArts Flexography TotalAllSolventTypes",
    "2461021000":
        "SolventUtilization MiscellaneousNonindustrialCommercial CutbackAsphalt TotalAllSolventTypes",
    "2810025000":
        "MiscellaneousAreaSources OtherCombustion ResidentialGrillingsee2302002xxxforCommercial Total",
    "2102002000":
        "StationarySourceFuelCombustion Industrial BituminousSubbituminousCoal TotalAllBoilerTypes",
    "2801500130":
        "MiscellaneousAreaSources AgricultureProductionCrops AgriculturalFieldBurningwholefieldsetonfire FieldCropisBarleyBurningTechniquesNotSignificant",
    "2505030120":
        "StorageandTransport PetroleumandPetroleumProductTransport Truck Gasoline",
    "2801500410":
        "MiscellaneousAreaSources AgricultureProductionCrops AgriculturalFieldBurningwholefieldsetonfire OrchardCropisPeach",
    "2415300000":
        "SolventUtilization Degreasing AllIndustriesColdCleaning TotalAllSolventTypes",
    "2501060101":
        "StorageandTransport PetroleumandPetroleumProductStorage GasolineServiceStations Stage2DisplacementLossUncontrolled",
    "2501060201":
        "StorageandTransport PetroleumandPetroleumProductStorage GasolineServiceStations UndergroundTankBreathingandEmptying",
    "2801500500":
        "MiscellaneousAreaSources AgricultureProductionCrops AgriculturalFieldBurningwholefieldsetonfire VineCropUnspecified",
    "2401008000":
        "SolventUtilization SurfaceCoating TrafficMarkings TotalAllSolventTypes",
    "2801500350":
        "MiscellaneousAreaSources AgricultureProductionCrops AgriculturalFieldBurningwholefieldsetonfire OrchardCropisCherry",
    "2801500420":
        "MiscellaneousAreaSources AgricultureProductionCrops AgriculturalFieldBurningwholefieldsetonfire OrchardCropisPear",
    "2303000000":
        "IndustrialProcesses PrimaryMetalProductionSIC33 AllProcesses Total",
    "2312000000":
        "IndustrialProcesses MachinerySIC35 AllProcesses Total",
    "2501060052":
        "StorageandTransport PetroleumandPetroleumProductStorage GasolineServiceStations Stage1SplashFilling",
    "2280002100":
        "MobileSources MarineVesselsCommercial Diesel Portemissions",
    "2103002000":
        "StationarySourceFuelCombustion CommercialInstitutional BituminousSubbituminousCoal TotalAllBoilerTypes",
    "2285002006":
        "MobileSources RailroadEquipment Diesel LineHaulLocomotivesClassIOperations",
    "2306010000":
        "IndustrialProcesses PetroleumRefiningSIC29 AsphaltMixingPlantsandPavingRoofingMaterials AsphaltPavingRoofingMaterialsTotal",
    "2401001000":
        "SolventUtilization SurfaceCoating ArchitecturalCoatings TotalAllSolventTypes",
    "2501011015":
        "StorageandTransport PetroleumandPetroleumProductStorage ResidentialPortableGasCans RefillingatthePumpSpillage",
    "2501080050":
        "StorageandTransport PetroleumandPetroleumProductStorage AirportsAviationGasoline Stage1Total",
    "2501012012":
        "StorageandTransport PetroleumandPetroleumProductStorage CommercialPortableGasCans EvaporationincludesDiurnallosses",
    "2285002007":
        "MobileSources RailroadEquipment Diesel LineHaulLocomotivesClassIIIIIOperations",
    "2501012014":
        "StorageandTransport PetroleumandPetroleumProductStorage CommercialPortableGasCans RefillingatthePumpVaporDisplacement",
    "2630020000":
        "WasteDisposalTreatmentandRecovery WastewaterTreatment PublicOwned TotalProcessed",
    "2501011012":
        "StorageandTransport PetroleumandPetroleumProductStorage ResidentialPortableGasCans EvaporationincludesDiurnallosses",
    "2501012013":
        "StorageandTransport PetroleumandPetroleumProductStorage CommercialPortableGasCans SpillageDuringTransport",
    "2505040120":
        "StorageandTransport PetroleumandPetroleumProductTransport Pipeline Gasoline",
    "2501012015":
        "StorageandTransport PetroleumandPetroleumProductStorage CommercialPortableGasCans RefillingatthePumpSpillage",
    "2501080100":
        "StorageandTransport PetroleumandPetroleumProductStorage AirportsAviationGasoline Stage2Total",
    "2501060050":
        "StorageandTransport PetroleumandPetroleumProductStorage GasolineServiceStations Stage1Total",
    "2104001000":
        "StationarySourceFuelCombustion Residential AnthraciteCoal TotalAllCombustorTypes",
    "2501011014":
        "StorageandTransport PetroleumandPetroleumProductStorage ResidentialPortableGasCans RefillingatthePumpVaporDisplacement",
    "2501011013":
        "StorageandTransport PetroleumandPetroleumProductStorage ResidentialPortableGasCans SpillageDuringTransport",
    "2501011011":
        "StorageandTransport PetroleumandPetroleumProductStorage ResidentialPortableGasCans Permeation",
    "2501060053":
        "StorageandTransport PetroleumandPetroleumProductStorage GasolineServiceStations Stage1BalancedSubmergedFilling",
    "2285002010":
        "MobileSources RailroadEquipment Diesel YardLocomotives",
    "2501012011":
        "StorageandTransport PetroleumandPetroleumProductStorage CommercialPortableGasCans Permeation",
    "2610000400":
        "WasteDisposalTreatmentandRecovery OpenBurning AllCategories YardWasteBrushSpeciesUnspecified",
    "2610000100":
        "WasteDisposalTreatmentandRecovery OpenBurning AllCategories YardWasteLeafSpeciesUnspecified",
    "2501060051":
        "StorageandTransport PetroleumandPetroleumProductStorage GasolineServiceStations Stage1SubmergedFilling",
    "2285002009":
        "MobileSources RailroadEquipment Diesel LineHaulLocomotivesCommuterLines",
    "2610000500":
        "WasteDisposalTreatmentandRecovery OpenBurning AllCategories LandClearingDebrisuse2810005000forLoggingDebrisBurning",
    "2660000000":
        "WasteDisposalTreatmentandRecovery LeakingUndergroundStorageTanks LeakingUndergroundStorageTanks TotalAllStorageTypes",
    "2620000000":
        "WasteDisposalTreatmentandRecovery Landfills AllCategories Total",
    "2461850000":
        "SolventUtilization MiscellaneousNonindustrialCommercial PesticideApplicationAgricultural AllProcesses",
    "2830000000":
        "MiscellaneousAreaSources CatastrophicAccidentalReleases AllCatastrophicAccidentialReleases Total",
    "2830010000":
        "MiscellaneousAreaSources CatastrophicAccidentalReleases TransportationAccidents Total",
    "2630010000":
        "WasteDisposalTreatmentandRecovery WastewaterTreatment Industrial TotalProcessed",
    "2285002008":
        "MobileSources RailroadEquipment Diesel LineHaulLocomotivesPassengerTrainsAmtrak",
    "2501055120":
        "StorageandTransport PetroleumandPetroleumProductStorage BulkPlantsAllEvaporativeLosses Gasoline",
    "2501050120":
        "StorageandTransport PetroleumandPetroleumProductStorage BulkTerminalsAllEvaporativeLosses Gasoline",
    "2103001000":
        "StationarySourceFuelCombustion CommercialInstitutional AnthraciteCoal TotalAllBoilerTypes",
    "2461850005":
        "SolventUtilization MiscellaneousNonindustrialCommercial PesticideApplicationAgricultural HerbicidesSoyBeans",
    "2401003000":
        "SolventUtilization SurfaceCoating ArchitecturalCoatingsWaterbased TotalAllSolventTypes",
    "2505020120":
        "StorageandTransport PetroleumandPetroleumProductTransport MarineVessel Gasoline",
    "2505020060":
        "StorageandTransport PetroleumandPetroleumProductTransport MarineVessel ResidualOil",
    "2401005500":
        "SolventUtilization SurfaceCoating AutoRefinishingSIC7532 SurfacePreparationSolvents",
    "2501080201":
        "StorageandTransport PetroleumandPetroleumProductStorage AirportsAviationGasoline UndergroundTankBreathingandEmptying",
    "2401005600":
        "SolventUtilization SurfaceCoating AutoRefinishingSIC7532 Primers",
    "2461850099":
        "SolventUtilization MiscellaneousNonindustrialCommercial PesticideApplicationAgricultural OtherPesticidesNotElsewhereClassified",
    "2401100000":
        "SolventUtilization SurfaceCoating IndustrialMaintenanceCoatings TotalAllSolventTypes",
    "2461850001":
        "SolventUtilization MiscellaneousNonindustrialCommercial PesticideApplicationAgricultural HerbicidesCorn",
    "2461850051":
        "SolventUtilization MiscellaneousNonindustrialCommercial PesticideApplicationAgricultural OtherPesticidesCorn",
    "2460100000":
        "SolventUtilization MiscellaneousNonindustrialConsumerandCommercial AllPersonalCareProducts TotalAllSolventTypes",
    "2425010000":
        "SolventUtilization GraphicArts Lithography TotalAllSolventTypes",
    "2505020150":
        "StorageandTransport PetroleumandPetroleumProductTransport MarineVessel JetNaphtha",
    "2461850009":
        "SolventUtilization MiscellaneousNonindustrialCommercial PesticideApplicationAgricultural HerbicidesNotElsewhereClassified",
    "2801500600":
        "MiscellaneousAreaSources AgricultureProductionCrops AgriculturalFieldBurningwholefieldsetonfire ForestResiduesUnspecified",
    "2461850055":
        "SolventUtilization MiscellaneousNonindustrialCommercial PesticideApplicationAgricultural OtherPesticidesSoyBeans",
    "2425030000":
        "SolventUtilization GraphicArts Rotogravure TotalAllSolventTypes",
    "2401005700":
        "SolventUtilization SurfaceCoating AutoRefinishingSIC7532 TopCoats",
    "2401005800":
        "SolventUtilization SurfaceCoating AutoRefinishingSIC7532 CleanupSolvents",
    "2461850056":
        "SolventUtilization MiscellaneousNonindustrialCommercial PesticideApplicationAgricultural OtherPesticidesHay&Grains",
    "2460900000":
        "SolventUtilization MiscellaneousNonindustrialConsumerandCommercial MiscellaneousProductsNotOtherwiseCovered TotalAllSolventTypes",
    "2415360000":
        "SolventUtilization Degreasing AutoRepairServicesSIC75ColdCleaning TotalAllSolventTypes",
    "2425020000":
        "SolventUtilization GraphicArts Letterpress TotalAllSolventTypes",
    "2505020180":
        "StorageandTransport PetroleumandPetroleumProductTransport MarineVessel Kerosene",
    "2461850006":
        "SolventUtilization MiscellaneousNonindustrialCommercial PesticideApplicationAgricultural HerbicidesHay&Grains",
    "2505020090":
        "StorageandTransport PetroleumandPetroleumProductTransport MarineVessel DistillateOil",
    "2505020030":
        "StorageandTransport PetroleumandPetroleumProductTransport MarineVessel CrudeOil",
    "2420000370":
        "SolventUtilization DryCleaning AllProcesses SpecialNaphthas",
    "2311000000":
        "IndustrialProcesses ConstructionSIC1517 AllProcesses Total",
    "2401015000":
        "SolventUtilization SurfaceCoating FactoryFinishedWoodSIC2426thru242 TotalAllSolventTypes",
    "2465000000":
        "SolventUtilization MiscellaneousNonindustrialConsumer AllProductsProcesses TotalAllSolventTypes",
    "2640000000":
        "WasteDisposalTreatmentandRecovery TSDFs AllTSDFTypes TotalAllProcesses",
    "2510000000":
        "StorageandTransport OrganicChemicalStorage AllStorageTypesBreathingLoss TotalAllProducts",
    "2420000055":
        "SolventUtilization DryCleaning AllProcesses Perchloroethylene",
    "2401005000":
        "SolventUtilization SurfaceCoating AutoRefinishingSIC7532 TotalAllSolventTypes",
    "2601020000":
        "WasteDisposalTreatmentandRecovery OnsiteIncineration CommercialInstitutional Total",
    "2461020000":
        "SolventUtilization MiscellaneousNonindustrialCommercial AsphaltApplicationAllProcesses TotalAllSolventTypes",
    "2515000900":
        "StorageandTransport OrganicChemicalTransport AllTransportTypes TankCleaning",
    "2465100000":
        "SolventUtilization MiscellaneousNonindustrialConsumer PersonalCareProducts TotalAllSolventTypes",
    "2810003000":
        "MiscellaneousAreaSources OtherCombustion CigaretteSmoke Total",
    "2415345000":
        "SolventUtilization Degreasing MiscellaneousManufacturingSIC39ColdCleaning TotalAllSolventTypes",
    "2401050000":
        "SolventUtilization SurfaceCoating MiscellaneousFinishedMetalsSIC34341+3498 TotalAllSolventTypes",
    "2401030000":
        "SolventUtilization SurfaceCoating PaperSIC26 TotalAllSolventTypes",
    "2620020000":
        "WasteDisposalTreatmentandRecovery Landfills CommercialInstitutional Total",
    "2425000000":
        "SolventUtilization GraphicArts AllProcesses TotalAllSolventTypes",
    "2505020000":
        "StorageandTransport PetroleumandPetroleumProductTransport MarineVessel TotalAllProducts",
    "2465400000":
        "SolventUtilization MiscellaneousNonindustrialConsumer AutomotiveAftermarketProducts TotalAllSolventTypes",
    "2465800000":
        "SolventUtilization MiscellaneousNonindustrialConsumer PesticideApplication TotalAllSolventTypes",
    "2103007000":
        "StationarySourceFuelCombustion CommercialInstitutional LiquifiedPetroleumGasLPG TotalAllCombustorTypes",
    "2501050000":
        "StorageandTransport PetroleumandPetroleumProductStorage BulkTerminalsAllEvaporativeLosses TotalAllProducts",
    "2401090000":
        "SolventUtilization SurfaceCoating MiscellaneousManufacturing TotalAllSolventTypes",
    "2302002000":
        "IndustrialProcesses FoodandKindredProductsSIC20 CommercialCookingCharbroiling CharbroilingTotal",
    "2401080000":
        "SolventUtilization SurfaceCoating MarineSIC373 TotalAllSolventTypes",
    "2302050000":
        "IndustrialProcesses FoodandKindredProductsSIC20 BakeryProducts Total",
    "2401060000":
        "SolventUtilization SurfaceCoating LargeAppliancesSIC363 TotalAllSolventTypes",
    "2102006000":
        "StationarySourceFuelCombustion Industrial NaturalGas TotalBoilersandICEngines",
    "2465200000":
        "SolventUtilization MiscellaneousNonindustrialConsumer HouseholdProducts TotalAllSolventTypes",
    "2103006000":
        "StationarySourceFuelCombustion CommercialInstitutional NaturalGas TotalBoilersandICEngines",
    "2670001000":
        "WasteDisposalTreatmentandRecovery MunitionsDetonation TNTDetonation General",
    "2505030000":
        "StorageandTransport PetroleumandPetroleumProductTransport Truck TotalAllProducts",
    "2401070000":
        "SolventUtilization SurfaceCoating MotorVehiclesSIC371 TotalAllSolventTypes",
    "2415000000":
        "SolventUtilization Degreasing AllProcessesAllIndustries TotalAllSolventTypes",
    "2401065000":
        "SolventUtilization SurfaceCoating ElectronicandOtherElectricalSIC36363 TotalAllSolventTypes",
    "2401020000":
        "SolventUtilization SurfaceCoating WoodFurnitureSIC25 TotalAllSolventTypes",
    "2401055000":
        "SolventUtilization SurfaceCoating MachineryandEquipmentSIC35 TotalAllSolventTypes",
    "2103004002":
        "StationarySourceFuelCombustion CommercialInstitutional DistillateOil ICEngines",
    "2102004000":
        "StationarySourceFuelCombustion Industrial DistillateOil TotalBoilersandICEngines",
    "2610030000":
        "WasteDisposalTreatmentandRecovery OpenBurning Residential HouseholdWasteuse2610000xxxforYardWastes",
    "2102001000":
        "StationarySourceFuelCombustion Industrial AnthraciteCoal TotalAllBoilerTypes",
    "2103004000":
        "StationarySourceFuelCombustion CommercialInstitutional DistillateOil TotalBoilersandICEngines",
    "2102004002":
        "StationarySourceFuelCombustion Industrial DistillateOil AllICEngineTypes",
    "2103004001":
        "StationarySourceFuelCombustion CommercialInstitutional DistillateOil Boilers",
    "2103005000":
        "StationarySourceFuelCombustion CommercialInstitutional ResidualOil TotalAllBoilerTypes",
    "2501060200":
        "StorageandTransport PetroleumandPetroleumProductStorage GasolineServiceStations UndergroundTankTotal",
    "2102004001":
        "StationarySourceFuelCombustion Industrial DistillateOil AllBoilerTypes",
    "2280003200":
        "MobileSources MarineVesselsCommercial Residual Underwayemissions",
    "2280003100":
        "MobileSources MarineVesselsCommercial Residual Portemissions",
    "2103011000":
        "StationarySourceFuelCombustion CommercialInstitutional Kerosene TotalAllCombustorTypes",
    "2102006002":
        "StationarySourceFuelCombustion Industrial NaturalGas AllICEngineTypes",
    "2801520000":
        "MiscellaneousAreaSources AgricultureProductionCrops OrchardHeaters Totalallfuels",
    "2505000120":
        "StorageandTransport PetroleumandPetroleumProductTransport AllTransportTypes Gasoline",
    "2440000000":
        "SolventUtilization MiscellaneousIndustrial AllProcesses TotalAllSolventTypes",
    "2104004000":
        "StationarySourceFuelCombustion Residential DistillateOil TotalAllCombustorTypes",
    "2305070000":
        "IndustrialProcesses MineralProcessesSIC32 ConcreteGypsumPlasterProducts Total",
    "2401040000":
        "SolventUtilization SurfaceCoating MetalCansSIC341 TotalAllSolventTypes",
    "2501995120":
        "StorageandTransport PetroleumandPetroleumProductStorage AllStorageTypesWorkingLoss Gasoline",
    "2104011000":
        "StationarySourceFuelCombustion Residential Kerosene TotalAllHeaterTypes",
    "2401085000":
        "SolventUtilization SurfaceCoating RailroadSIC374 TotalAllSolventTypes",
    "2401010000":
        "SolventUtilization SurfaceCoating TextileProductsSIC22 TotalAllSolventTypes",
    "2401025000":
        "SolventUtilization SurfaceCoating MetalFurnitureSIC25 TotalAllSolventTypes",
    "2401200000":
        "SolventUtilization SurfaceCoating OtherSpecialPurposeCoatings TotalAllSolventTypes",
    "2610040400":
        "WasteDisposalTreatmentandRecovery OpenBurning Municipalcollectedfromresidencesparksotherforcentralburn YardWasteTotalincludesLeavesWeedsandBrush",
    "2630000000":
        "WasteDisposalTreatmentandRecovery WastewaterTreatment AllCategories TotalProcessed",
    "2102011000":
        "StationarySourceFuelCombustion Industrial Kerosene TotalAllBoilerTypes",
    "2104006000":
        "StationarySourceFuelCombustion Residential NaturalGas TotalAllCombustorTypes",
    "2810090000":
        "MiscellaneousAreaSources OtherCombustion OpenFire Notcategorized",
    "2104005000":
        "StationarySourceFuelCombustion Residential ResidualOil TotalAllCombustorTypes",
    "2310000000":
        "IndustrialProcesses OilandGasExplorationandProduction AllProcesses TotalAllProcesses",
    "2104007000":
        "StationarySourceFuelCombustion Residential LiquifiedPetroleumGasLPG TotalAllCombustorTypes",
    "2610000300":
        "WasteDisposalTreatmentandRecovery OpenBurning AllCategories YardWasteWeedSpeciesUnspecifiedinclGrass",
    "2810035000":
        "MiscellaneousAreaSources OtherCombustion FirefightingTraining Total",
    "2102007000":
        "StationarySourceFuelCombustion Industrial LiquifiedPetroleumGasLPG TotalAllBoilerTypes",
    "2415310000":
        "SolventUtilization Degreasing PrimaryMetalIndustriesSIC33ColdCleaning TotalAllSolventTypes",
    "2415340000":
        "SolventUtilization Degreasing InstrumentsandRelatedProductsSIC38ColdCleaning TotalAllSolventTypes",
    "2415320000":
        "SolventUtilization Degreasing FabricatedMetalProductsSIC34ColdCleaning TotalAllSolventTypes",
    "2415305000":
        "SolventUtilization Degreasing FurnitureandFixturesSIC25ColdCleaning TotalAllSolventTypes",
    "2415350000":
        "SolventUtilization Degreasing TransportationMaintenanceFacilitiesSIC4045ColdCleaning TotalAllSolventTypes",
    "2415355000":
        "SolventUtilization Degreasing AutomotiveDealersSIC55ColdCleaning TotalAllSolventTypes",
    "2415335000":
        "SolventUtilization Degreasing TransportationEquipmentSIC37ColdCleaning TotalAllSolventTypes",
    "2415365000":
        "SolventUtilization Degreasing MiscellaneousRepairServicesSIC76ColdCleaning TotalAllSolventTypes",
    "2415330000":
        "SolventUtilization Degreasing ElectronicandOtherElec.SIC36ColdCleaning TotalAllSolventTypes",
    "2415325000":
        "SolventUtilization Degreasing IndustrialMachineryandEquipmentSIC35ColdCleaning TotalAllSolventTypes",
    "2301010000":
        "IndustrialProcesses ChemicalManufacturingSIC28 IndustrialInorganicChemicalManufacturing Total",
    "2430000000":
        "SolventUtilization RubberPlastics AllProcesses TotalAllSolventTypes",
    "2460000000":
        "SolventUtilization MiscellaneousNonindustrialConsumerandCommercial AllProcesses TotalAllSolventTypes",
    "2104008510":
        "StationarySourceFuelCombustion Residential Wood FurnaceIndoorcordwoodfirednonEPAcertified",
    "2104008610":
        "StationarySourceFuelCombustion Residential Wood Hydronicheateroutdoor",
    "2104008400":
        "StationarySourceFuelCombustion Residential Wood WoodstovepelletfiredgeneralfreestandingorFPinsert",
    "2104008210":
        "StationarySourceFuelCombustion Residential Wood Woodstovefireplaceinserts;nonEPAcertified",
    "2104008310":
        "StationarySourceFuelCombustion Residential Wood WoodstovefreestandingnonEPAcertified",
    "2104008330":
        "StationarySourceFuelCombustion Residential Wood WoodstovefreestandingEPAcertifiedcatalytic",
    "2104008230":
        "StationarySourceFuelCombustion Residential Wood Woodstovefireplaceinserts;EPAcertified;catalytic",
    "2104008320":
        "StationarySourceFuelCombustion Residential Wood WoodstovefreestandingEPAcertifiednoncatalytic",
    "2104008100":
        "StationarySourceFuelCombustion Residential Wood Fireplacegeneral",
    "2104008220":
        "StationarySourceFuelCombustion Residential Wood Woodstovefireplaceinserts;EPAcertified;noncatalytic",
    "2104008700":
        "StationarySourceFuelCombustion Residential Wood OutdoorwoodburningdeviceNECfirepitschimeasetc",
    "2104009000":
        "StationarySourceFuelCombustion Residential Firelog TotalAllCombustorTypes",
    "2801500000":
        "MiscellaneousAreaSources AgricultureProductionCrops AgriculturalFieldBurningwholefieldsetonfire UnspecifiedcroptypeandBurnMethod",
    "2810030000":
        "MiscellaneousAreaSources OtherCombustion StructureFires Unspecified",
    "2810050000":
        "MiscellaneousAreaSources OtherCombustion MotorVehicleFires Unspecified",
    "2104008300":
        "StationarySourceFuelCombustion Residential Wood Woodstovefreestandinggeneral",
    "2461100000":
        "SolventUtilization MiscellaneousNonindustrialCommercial SolventReclamationAllProcesses TotalAllSolventTypes",
    "2401075000":
        "SolventUtilization SurfaceCoating AircraftSIC372 TotalAllSolventTypes",
    "2401045000":
        "SolventUtilization SurfaceCoating MetalCoilsSIC3498 TotalAllSolventTypes",
    "2104006010":
        "StationarySourceFuelCombustion Residential NaturalGas ResidentialFurnaces",
    "2307000000":
        "IndustrialProcesses WoodProductsSIC24 AllProcesses Total",
    "2840010000":
        "MiscellaneousAreaSources AutomotiveRepairShops AutoTopandBodyRepair Total",
    "2302080000":
        "IndustrialProcesses FoodandKindredProductsSIC20 MiscellaneousFoodandKindredProducts Total",
    "2461023000":
        "SolventUtilization MiscellaneousNonindustrialCommercial AsphaltRoofing TotalAllSolventTypes",
    "2308000000":
        "IndustrialProcesses RubberPlasticsSIC30 AllProcesses Total",
    "2305000000":
        "IndustrialProcesses MineralProcessesSIC32 AllProcesses Total",
    "2310030000":
        "IndustrialProcesses OilandGasExplorationandProduction NaturalGasLiquids TotalAllProcesses",
    "2310020000":
        "IndustrialProcesses OilandGasExplorationandProduction NaturalGas TotalAllProcesses",
    "2310010000":
        "IndustrialProcesses OilandGasExplorationandProduction CrudePetroleum TotalAllProcesses",
    "2399000000":
        "IndustrialProcesses IndustrialProcessesNEC IndustrialProcessesNEC Total",
    "2301020000":
        "IndustrialProcesses ChemicalManufacturingSIC28 ProcessEmissionsfromSyntheticFibersManufNAPAPcat.107 Total",
    "2302000000":
        "IndustrialProcesses FoodandKindredProductsSIC20 AllProcesses Total",
    "2325030000":
        "IndustrialProcesses MiningandQuarryingSIC10andSIC14 SandandGravel Total",
    "2301000000":
        "IndustrialProcesses ChemicalManufacturingSIC28 AllProcesses Total",
    "2304000000":
        "IndustrialProcesses SecondaryMetalProductionSIC33 AllProcesses Total",
    "2520010000":
        "StorageandTransport InorganicChemicalStorage CommercialIndustrialBreathingLoss TotalAllProducts",
    "2305080000":
        "IndustrialProcesses MineralProcessesSIC32 CutStoneandStoneProducts Total",
    "2415225000":
        "SolventUtilization Degreasing IndustrialMachineryandEquipmentSIC35ConveyerizedDegreasing TotalAllSolventTypes",
    "2415160000":
        "SolventUtilization Degreasing AutoRepairServicesSIC75OpenTopDegreasing TotalAllSolventTypes",
    "2415220000":
        "SolventUtilization Degreasing FabricatedMetalProductsSIC34ConveyerizedDegreasing TotalAllSolventTypes",
    "2415205000":
        "SolventUtilization Degreasing FurnitureandFixturesSIC25ConveyerizedDegreasing TotalAllSolventTypes",
    "2415165000":
        "SolventUtilization Degreasing MiscellaneousRepairServicesSIC76OpenTopDegreasing TotalAllSolventTypes",
    "2415150000":
        "SolventUtilization Degreasing TransportationMaintenanceFacilitiesSIC4045OpenTopDegreasing TotalAllSolventTypes",
    "2415240000":
        "SolventUtilization Degreasing InstrumentsandRelatedProductsSIC38ConveyerizedDegreasing TotalAllSolventTypes",
    "2415105000":
        "SolventUtilization Degreasing FurnitureandFixturesSIC25OpenTopDegreasing TotalAllSolventTypes",
    "2415210000":
        "SolventUtilization Degreasing PrimaryMetalIndustriesSIC33ConveyerizedDegreasing TotalAllSolventTypes",
    "2415125000":
        "SolventUtilization Degreasing IndustrialMachineryandEquipmentSIC35OpenTopDegreasing TotalAllSolventTypes",
    "2415130000":
        "SolventUtilization Degreasing ElectronicandOtherElec.SIC36OpenTopDegreasing TotalAllSolventTypes",
    "2415235000":
        "SolventUtilization Degreasing TransportationEquipmentSIC37ConveyerizedDegreasing TotalAllSolventTypes",
    "2415245000":
        "SolventUtilization Degreasing MiscellaneousManufacturingSIC39ConveyerizedDegreasing TotalAllSolventTypes",
    "2415155000":
        "SolventUtilization Degreasing AutomotiveDealersSIC55OpenTopDegreasing TotalAllSolventTypes",
    "2415255000":
        "SolventUtilization Degreasing AutomotiveDealersSIC55ConveyerizedDegreasing TotalAllSolventTypes",
    "2415140000":
        "SolventUtilization Degreasing InstrumentsandRelatedProductsSIC38OpenTopDegreasing TotalAllSolventTypes",
    "2415265000":
        "SolventUtilization Degreasing MiscellaneousRepairServicesSIC76ConveyerizedDegreasing TotalAllSolventTypes",
    "2415230000":
        "SolventUtilization Degreasing ElectronicandOtherElec.SIC36ConveyerizedDegreasing TotalAllSolventTypes",
    "2415145000":
        "SolventUtilization Degreasing MiscellaneousManufacturingSIC39OpenTopDegreasing TotalAllSolventTypes",
    "2415110000":
        "SolventUtilization Degreasing PrimaryMetalIndustriesSIC33OpenTopDegreasing TotalAllSolventTypes",
    "2415260000":
        "SolventUtilization Degreasing AutoRepairServicesSIC75ConveyerizedDegreasing TotalAllSolventTypes",
    "2415135000":
        "SolventUtilization Degreasing TransportationEquipmentSIC37OpenTopDegreasing TotalAllSolventTypes",
    "2415250000":
        "SolventUtilization Degreasing Trans.MaintenanceFacilitiesSIC4045ConveyerizedDegreasing TotalAllSolventTypes",
    "2415120000":
        "SolventUtilization Degreasing FabricatedMetalProductsSIC34OpenTopDegreasing TotalAllSolventTypes",
    "2102012000":
        "StationarySourceFuelCombustion Industrial Wasteoil Total",
    "2415030000":
        "SolventUtilization Degreasing ElectronicandOtherElec.SIC36AllProcesses TotalAllSolventTypes",
    "2415035000":
        "SolventUtilization Degreasing TransportationEquipmentSIC37AllProcesses TotalAllSolventTypes",
    "2415020000":
        "SolventUtilization Degreasing FabricatedMetalProductsSIC34AllProcesses TotalAllSolventTypes",
    "2415025000":
        "SolventUtilization Degreasing IndustrialMachineryandEquipmentSIC35AllProcesses TotalAllSolventTypes",
    "2415040000":
        "SolventUtilization Degreasing InstrumentsandRelatedProductsSIC38AllProcesses TotalAllSolventTypes",
    "2415045000":
        "SolventUtilization Degreasing MiscellaneousManufacturingSIC39AllProcesses TotalAllSolventTypes",
    "2415005000":
        "SolventUtilization Degreasing FurnitureandFixturesSIC25AllProcesses TotalAllSolventTypes",
    "2415065000":
        "SolventUtilization Degreasing AutoRepairServicesSIC75AllProcesses TotalAllSolventTypes",
    "2461800000":
        "SolventUtilization MiscellaneousNonindustrialCommercial PesticideApplicationAllProcesses TotalAllSolventTypes",
    "2810060100":
        "MiscellaneousAreaSources OtherCombustion Cremation Humans",
    "2810060200":
        "MiscellaneousAreaSources OtherCombustion Cremation Animals",
    "2302003100":
        "IndustrialProcesses FoodandKindredProductsSIC20 CommercialCookingFrying FlatGriddleFrying",
    "2294000000":
        "MobileSources PavedRoads AllPavedRoads TotalFugitives",
    "2302003000":
        "IndustrialProcesses FoodandKindredProductsSIC20 CommercialCookingFrying DeepFatFrying",
    "2302003200":
        "IndustrialProcesses FoodandKindredProductsSIC20 CommercialCookingFrying ClamshellGriddleFrying",
    "2420020055":
        "SolventUtilization DryCleaning CoinoperatedCleaners Perchloroethylene",
    "2415100000":
        "SolventUtilization Degreasing AllIndustriesOpenTopDegreasing TotalAllSolventTypes",
    "2420010055":
        "SolventUtilization DryCleaning CommercialIndustrialCleaners Perchloroethylene",
    "2420000000":
        "SolventUtilization DryCleaning AllProcesses TotalAllSolventTypes",
    "2420020000":
        "SolventUtilization DryCleaning CoinoperatedCleaners TotalAllSolventTypes",
    "2420010000":
        "SolventUtilization DryCleaning CommercialIndustrialCleaners TotalAllSolventTypes",
    "2306000000":
        "IndustrialProcesses PetroleumRefiningSIC29 AllProcesses Total",
    "2501000120":
        "StorageandTransport PetroleumandPetroleumProductStorage AllStorageTypesBreathingLoss Gasoline",
    "2461850004":
        "SolventUtilization MiscellaneousNonindustrialCommercial PesticideApplicationAgricultural HerbicidesPotatoes",
    "2309100010":
        "IndustrialProcesses FabricatedMetalsSIC34 CoatingEngravingandAlliedServices Electroplating",
    "2309100030":
        "IndustrialProcesses FabricatedMetalsSIC34 CoatingEngravingandAlliedServices PlatingMetalDeposition",
    "2309100050":
        "IndustrialProcesses FabricatedMetalsSIC34 CoatingEngravingandAlliedServices Anodizing",
    "2801000003":
        "MiscellaneousAreaSources AgricultureProductionCrops AgricultureCrops Tilling",
    "2311010000":
        "IndustrialProcesses ConstructionSIC1517 Residential Total",
    "2311030000":
        "IndustrialProcesses ConstructionSIC1517 RoadConstruction Total",
    "2701200000":
        "NaturalSources Biogenic Vegetation Total",
    "2103010000":
        "StationarySourceFuelCombustion CommercialInstitutional ProcessGas POTWDigesterGasfiredBoilers",
    "2309000000":
        "IndustrialProcesses FabricatedMetalsSIC34 AllProcesses Total",
    "2862000000":
        "MiscellaneousAreaSources SwimmingPools TotalCommercialResidentialPublic Total",
    "2415200000":
        "SolventUtilization Degreasing AllIndustriesConveyerizedDegreasing TotalAllSolventTypes",
    "2415050000":
        "SolventUtilization Degreasing TransportationMaintenanceFacilitiesSIC4045AllProcesses TotalAllSolventTypes",
    "2275087000":
        "MobileSources Aircraft InflightnonLandingTakeoffcycle Total",
    "2296000000":
        "MobileSources UnpavedRoads AllUnpavedRoads TotalFugitives",
    "2840000000":
        "MiscellaneousAreaSources AutomotiveRepairShops AutomotiveRepairShops Total",
    "2861000000":
        "MiscellaneousAreaSources FluorescentLampBreakage FluorescentLampBreakage NonrecyclingRelatedEmissionsTotal",
    "2861000010":
        "MiscellaneousAreaSources FluorescentLampBreakage FluorescentLampBreakage RecyclingRelatedEmissionsTotal",
    "2851001000":
        "MiscellaneousAreaSources Laboratories BenchScaleReagents Total",
    "2850001000":
        "MiscellaneousAreaSources HealthServices DentalAlloyProduction OverallProcess",
    "2525000000":
        "StorageandTransport InorganicChemicalTransport AllTransportTypes TotalAllProducts",
    "2680001000":
        "WasteDisposalTreatmentandRecovery Composting 100%Biosolidse.g.sewagesludgemanuremixturesofthesematls AllProcesses",
    "2461900000":
        "SolventUtilization MiscellaneousNonindustrialCommercial MiscellaneousProductsNEC TotalAllSolventTypes",
    "2680003000":
        "WasteDisposalTreatmentandRecovery Composting 100%GreenWastee.g.residentialormunicipalyardwastes AllProcesses",
    "2650000000":
        "WasteDisposalTreatmentandRecovery ScrapandWasteMaterials ScrapandWasteMaterials TotalAllProcesses",
    "2850000010":
        "MiscellaneousAreaSources HealthServices Hospitals SterilizationOperations",
    "2601000000":
        "WasteDisposalTreatmentandRecovery OnsiteIncineration AllCategories Total",
    "2805002000":
        "MiscellaneousAreaSources AgricultureProductionLivestock Beefcattleproductioncomposite NotElsewhereClassified",
    "2805018000":
        "MiscellaneousAreaSources AgricultureProductionLivestock Dairycattlecomposite NotElsewhereClassified",
    "2805030000":
        "MiscellaneousAreaSources AgricultureProductionLivestock PoultryWasteEmissions NotElsewhereClassifiedseealso2805007008009",
    "2805025000":
        "MiscellaneousAreaSources AgricultureProductionLivestock Swineproductioncomposite NotElsewhereClassifiedseealso2805039047053",
    "2461022000":
        "SolventUtilization MiscellaneousNonindustrialCommercial EmulsifiedAsphalt TotalAllSolventTypes",
    "2103007005":
        "StationarySourceFuelCombustion CommercialInstitutional LiquifiedPetroleumGasLPG AllBoilerTypes",
    "2601010000":
        "WasteDisposalTreatmentandRecovery OnsiteIncineration Industrial Total",
    "2801500300":
        "MiscellaneousAreaSources AgricultureProductionCrops AgriculturalFieldBurningwholefieldsetonfire OrchardCropUnspecified",
    "2302070005":
        "IndustrialProcesses FoodandKindredProductsSIC20 FermentationBeverages Wineries",
    "2302070010":
        "IndustrialProcesses FoodandKindredProductsSIC20 FermentationBeverages Distilleries",
    "2310021403":
        "IndustrialProcesses OilandGasExplorationandProduction OnShoreGasProduction NatGasFired4CycleRichBurnCompressorEngines500+HPwNSCR",
    "2310021103":
        "IndustrialProcesses OilandGasExplorationandProduction OnShoreGasProduction NaturalGasFired2CycleLeanBurnCompressorEngines500+HP",
    "2310021302":
        "IndustrialProcesses OilandGasExplorationandProduction OnShoreGasProduction NaturalGasFired4CycleRichBurnCompressorEngines50To499HP",
    "2310000220":
        "IndustrialProcesses OilandGasExplorationandProduction AllProcesses DrillRigs",
    "2310020600":
        "IndustrialProcesses OilandGasExplorationandProduction NaturalGas CompressorEngines",
    "2310000330":
        "IndustrialProcesses OilandGasExplorationandProduction AllProcesses ArtificialLift",
    "2310021203":
        "IndustrialProcesses OilandGasExplorationandProduction OnShoreGasProduction NaturalGasFired4CycleLeanBurnCompressorEngines500+HP",
    "2310021401":
        "IndustrialProcesses OilandGasExplorationandProduction OnShoreGasProduction NatGasFired4CycleRichBurnCompressorEngines50HPwNSCR",
    "2310021201":
        "IndustrialProcesses OilandGasExplorationandProduction OnShoreGasProduction NaturalGasFired4CycleLeanBurnCompressorEngines50HP",
    "2310021102":
        "IndustrialProcesses OilandGasExplorationandProduction OnShoreGasProduction NaturalGasFired2CycleLeanBurnCompressorEngines50To499HP",
    "2310021301":
        "IndustrialProcesses OilandGasExplorationandProduction OnShoreGasProduction NaturalGasFired4CycleRichBurnCompressorEngines50HP",
    "2310021303":
        "IndustrialProcesses OilandGasExplorationandProduction OnShoreGasProduction NaturalGasFired4CycleRichBurnCompressorEngines500+HP",
    "2310021100":
        "IndustrialProcesses OilandGasExplorationandProduction OnShoreGasProduction GasWellHeaters",
    "2310010100":
        "IndustrialProcesses OilandGasExplorationandProduction CrudePetroleum OilWellHeaters",
    "2310021402":
        "IndustrialProcesses OilandGasExplorationandProduction OnShoreGasProduction NatGasFired4CycleRichBurnCompressorEngines50To499HPwNSCR",
    "2310021400":
        "IndustrialProcesses OilandGasExplorationandProduction OnShoreGasProduction GasWellDehydrators",
    "2801500181":
        "MiscellaneousAreaSources AgricultureProductionCrops AgriculturalFieldBurningwholefieldsetonfire FieldCropisHaywildHeadfireBurning",
    "2310021202":
        "IndustrialProcesses OilandGasExplorationandProduction OnShoreGasProduction NaturalGasFired4CycleLeanBurnCompressorEngines50To499HP",
    "2310021101":
        "IndustrialProcesses OilandGasExplorationandProduction OnShoreGasProduction NaturalGasFired2CycleLeanBurnCompressorEngines50HP",
    "2310011100":
        "IndustrialProcesses OilandGasExplorationandProduction OnShoreOilProduction HeaterTreater",
    "2801500250":
        "MiscellaneousAreaSources AgricultureProductionCrops AgriculturalFieldBurningwholefieldsetonfire FieldCropisSugarCaneBurningTechniquesNotSignificant",
    "2310121702":
        "IndustrialProcesses OilandGasExplorationandProduction OnShoreGasExploration GasWellCompletionVenting",
    "2310121700":
        "IndustrialProcesses OilandGasExplorationandProduction OnShoreGasExploration GasWellCompletionAllProcesses",
    "2801500220":
        "MiscellaneousAreaSources AgricultureProductionCrops AgriculturalFieldBurningwholefieldsetonfire FieldCropisRiceBurningTechniquesNotSignificant",
    "2310021509":
        "IndustrialProcesses OilandGasExplorationandProduction OnShoreGasProduction FugitivesAllProcesses",
    "2801500150":
        "MiscellaneousAreaSources AgricultureProductionCrops AgriculturalFieldBurningwholefieldsetonfire FieldCropisCornBurningTechniquesNotImportant",
    "2801500262":
        "MiscellaneousAreaSources AgricultureProductionCrops AgriculturalFieldBurningwholefieldsetonfire FieldCropisWheatBackfireBurning",
    "2810040000":
        "MiscellaneousAreaSources OtherCombustion AircraftRocketEngineFiringandTesting Total",
    "2461800001":
        "SolventUtilization MiscellaneousNonindustrialCommercial PesticideApplicationAllProcesses SurfaceApplication",
    "2104008200":
        "StationarySourceFuelCombustion Residential Wood Woodstovefireplaceinserts;general",
    "2810005001":
        "MiscellaneousAreaSources OtherCombustion ManagedBurningSlashLoggingDebris PileBurning",
    "2810005002":
        "MiscellaneousAreaSources OtherCombustion ManagedBurningSlashLoggingDebris BroadcastBurning",
    "2805045000":
        "MiscellaneousAreaSources AgricultureProductionLivestock GoatsWasteEmissions NotElsewhereClassified",
    "2805035000":
        "MiscellaneousAreaSources AgricultureProductionLivestock HorsesandPoniesWasteEmissions NotElsewhereClassified",
    "2805040000":
        "MiscellaneousAreaSources AgricultureProductionLivestock SheepandLambsWasteEmissions Total",
    "2801700001":
        "MiscellaneousAreaSources AgricultureProductionCrops FertilizerApplication AnhydrousAmmonia",
    "2807030000":
        "MiscellaneousAreaSources WildAnimalsWasteEmissions Deer Total",
    "2807025000":
        "MiscellaneousAreaSources WildAnimalsWasteEmissions Elk Total",
    "2807020001":
        "MiscellaneousAreaSources WildAnimalsWasteEmissions Bears BlackBears",
    "2630030000":
        "WasteDisposalTreatmentandRecovery WastewaterTreatment ResidentialSubdivisionOwned TotalProcessed",
    "2805020002":
        "MiscellaneousAreaSources AgricultureProductionLivestock CattleandCalvesWasteEmissions BeefCows",
    "2805020000":
        "MiscellaneousAreaSources AgricultureProductionLivestock CattleandCalvesWasteEmissions Totalseealso2805001002003",
    "2801700006":
        "MiscellaneousAreaSources AgricultureProductionCrops FertilizerApplication AmmoniumSulfate",
    "2805019100":
        "MiscellaneousAreaSources AgricultureProductionLivestock DairyCattleWaste DairycattleflushdairyConfinement",
    "2805010100":
        "MiscellaneousAreaSources AgricultureProductionLivestock Poultryproductionturkeys Confinement",
    "2801700013":
        "MiscellaneousAreaSources AgricultureProductionCrops FertilizerApplication DiammoniumPhosphate",
    "2806010000":
        "MiscellaneousAreaSources DomesticAnimalsWasteEmissions Cats Total",
    "2805039100":
        "MiscellaneousAreaSources AgricultureProductionLivestock SwineWaste SwineProductionOperationswithLagoonsUnspecifiedAnimalAgeConfinement",
    "2805007100":
        "MiscellaneousAreaSources AgricultureProductionLivestock PoultryWaste PoultryProductionLayerswithDryManureManagementSystemsConfinement",
    "2805009200":
        "MiscellaneousAreaSources AgricultureProductionLivestock Poultryproductionbroilers Manurehandlingandstorage",
    "2805001200":
        "MiscellaneousAreaSources AgricultureProductionLivestock Beefcattlewaste BeefCattleFinishingOperationsonFeedlotsDrylotsManureHandlingandStorage",
    "2801700010":
        "MiscellaneousAreaSources AgricultureProductionCrops FertilizerApplication NPKmultigradenutrientfertilizers",
    "2805021200":
        "MiscellaneousAreaSources AgricultureProductionLivestock Dairycattlescrapedairy Manurehandlingandstorage",
    "2805019200":
        "MiscellaneousAreaSources AgricultureProductionLivestock DairyCattleWaste DairycattleflushdairyManurehandlingandstorage",
    "2810010000":
        "MiscellaneousAreaSources OtherCombustion HumanPerspirationandRespiration Total",
    "2805023200":
        "MiscellaneousAreaSources AgricultureProductionLivestock Dairycattledrylotpasturedairy Manurehandlingandstorage",
    "2805047300":
        "MiscellaneousAreaSources AgricultureProductionLivestock Swineproductiondeeppithouseoperationsunspecifiedanimalage Landapplicationofmanure",
    "2801700002":
        "MiscellaneousAreaSources AgricultureProductionCrops FertilizerApplication AqueousAmmonia",
    "2805047100":
        "MiscellaneousAreaSources AgricultureProductionLivestock Swineproductiondeeppithouseoperationsunspecifiedanimalage Confinement",
    "2801700005":
        "MiscellaneousAreaSources AgricultureProductionCrops FertilizerApplication AmmoniumNitrate",
    "2805008300":
        "MiscellaneousAreaSources AgricultureProductionLivestock Poultryproductionlayerswithwetmanuremanagementsystems Landapplicationofmanure",
    "2805010300":
        "MiscellaneousAreaSources AgricultureProductionLivestock Poultryproductionturkeys Landapplicationofmanure",
    "2805030008":
        "MiscellaneousAreaSources AgricultureProductionLivestock PoultryWasteEmissions Geese",
    "2805021100":
        "MiscellaneousAreaSources AgricultureProductionLivestock Dairycattlescrapedairy Confinement",
    "2805009100":
        "MiscellaneousAreaSources AgricultureProductionLivestock Poultryproductionbroilers Confinement",
    "2805008200":
        "MiscellaneousAreaSources AgricultureProductionLivestock Poultryproductionlayerswithwetmanuremanagementsystems Manurehandlingandstorage",
    "2801700003":
        "MiscellaneousAreaSources AgricultureProductionCrops FertilizerApplication NitrogenSolutions",
    "2801700004":
        "MiscellaneousAreaSources AgricultureProductionCrops FertilizerApplication Urea",
    "2805023100":
        "MiscellaneousAreaSources AgricultureProductionLivestock Dairycattledrylotpasturedairy Confinement",
    "2805053100":
        "MiscellaneousAreaSources AgricultureProductionLivestock Swineproductionoutdooroperationsunspecifiedanimalage Confinement",
    "2805039300":
        "MiscellaneousAreaSources AgricultureProductionLivestock SwineWaste SwineProductionOperationswithLagoonsUnspecifiedAnimalAgeLandApplicationofManure",
    "2805010200":
        "MiscellaneousAreaSources AgricultureProductionLivestock Poultryproductionturkeys Manurehandlingandstorage",
    "2805022300":
        "MiscellaneousAreaSources AgricultureProductionLivestock Dairycattledeeppitdairy Landapplicationofmanure",
    "2805022200":
        "MiscellaneousAreaSources AgricultureProductionLivestock Dairycattledeeppitdairy Manurehandlingandstorage",
    "2801700015":
        "MiscellaneousAreaSources AgricultureProductionCrops FertilizerApplication LiquidAmmoniumPolyphosphate",
    "2805021300":
        "MiscellaneousAreaSources AgricultureProductionLivestock Dairycattlescrapedairy Landapplicationofmanure",
    "2805008100":
        "MiscellaneousAreaSources AgricultureProductionLivestock Poultryproductionlayerswithwetmanuremanagementsystems Confinement",
    "2805009300":
        "MiscellaneousAreaSources AgricultureProductionLivestock Poultryproductionbroilers Landapplicationofmanure",
    "2805001100":
        "MiscellaneousAreaSources AgricultureProductionLivestock Beefcattlewaste BeefCattleFinishingOperationsonFeedlotsDrylotsConfinement",
    "2805003100":
        "MiscellaneousAreaSources AgricultureProductionLivestock Beefcattlewaste BeefcattlefinishingoperationsonpasturerangeConfinement",
    "2805039200":
        "MiscellaneousAreaSources AgricultureProductionLivestock SwineWaste SwineProductionOperationswithLagoonsUnspecifiedAnimalAgeManureHandlingandStorage",
    "2801700011":
        "MiscellaneousAreaSources AgricultureProductionCrops FertilizerApplication CalciumAmmoniumNitrate",
    "2801700099":
        "MiscellaneousAreaSources AgricultureProductionCrops FertilizerApplication MiscellaneousFertilizers",
    "2680002000":
        "WasteDisposalTreatmentandRecovery Composting MixedWastee.g.a5050mixtureofbiosolidsandgreenwastes AllProcesses",
    "2805019300":
        "MiscellaneousAreaSources AgricultureProductionLivestock DairyCattleWaste DairycattleflushdairyLandapplicationofmanure",
    "2805007300":
        "MiscellaneousAreaSources AgricultureProductionLivestock PoultryWaste PoultryProductionLayerswithDryManureManagementsystemsLandApplicationofManure",
    "2805030007":
        "MiscellaneousAreaSources AgricultureProductionLivestock PoultryWasteEmissions Ducks",
    "2805023300":
        "MiscellaneousAreaSources AgricultureProductionLivestock Dairycattledrylotpasturedairy Landapplicationofmanure",
    "2805022100":
        "MiscellaneousAreaSources AgricultureProductionLivestock Dairycattledeeppitdairy Confinement",
    "2399010000":
        "IndustrialProcesses IndustrialProcessesNEC RefrigerantLosses AllProcesses",
    "2805001300":
        "MiscellaneousAreaSources AgricultureProductionLivestock Beefcattlewaste BeefCattlefinishingoperationsonfeedlotsdrylotsLandapplicationofmanure",
    "2801700014":
        "MiscellaneousAreaSources AgricultureProductionCrops FertilizerApplication MonoammoniumPhosphate",
    "2801700007":
        "MiscellaneousAreaSources AgricultureProductionCrops FertilizerApplication AmmoniumThiosulfate",
    "2801700012":
        "MiscellaneousAreaSources AgricultureProductionCrops FertilizerApplication PotassiumNitrate",
    "2806015000":
        "MiscellaneousAreaSources DomesticAnimalsWasteEmissions Dogs Total",
    "2807020002":
        "MiscellaneousAreaSources WildAnimalsWasteEmissions Bears GrizzlyBears",
    "2807040000":
        "MiscellaneousAreaSources WildAnimalsWasteEmissions Birds Total",
    "2805030009":
        "MiscellaneousAreaSources AgricultureProductionLivestock PoultryWasteEmissions Turkeys",
    "2302080002":
        "IndustrialProcesses FoodandKindredProductsSIC20 MiscellaneousFoodandKindredProducts Refrigeration",
    "2805030001":
        "MiscellaneousAreaSources AgricultureProductionLivestock PoultryWasteEmissions PulletChicksandPulletslessthan13weeksold",
    "2805030002":
        "MiscellaneousAreaSources AgricultureProductionLivestock PoultryWasteEmissions Pullets13weeksoldandolderbutlessthan20weeksold",
    "2805045002":
        "MiscellaneousAreaSources AgricultureProductionLivestock GoatsWasteEmissions AngoraGoats",
    "2805020004":
        "MiscellaneousAreaSources AgricultureProductionLivestock CattleandCalvesWasteEmissions SteersSteerCalvesBullsandBullCalves",
    "2805045003":
        "MiscellaneousAreaSources AgricultureProductionLivestock GoatsWasteEmissions MilkGoats",
    "2805030004":
        "MiscellaneousAreaSources AgricultureProductionLivestock PoultryWasteEmissions Broilers",
    "2805030003":
        "MiscellaneousAreaSources AgricultureProductionLivestock PoultryWasteEmissions Layers",
    "2805020003":
        "MiscellaneousAreaSources AgricultureProductionLivestock CattleandCalvesWasteEmissions HeifersandHeiferCalves",
    "2805020001":
        "MiscellaneousAreaSources AgricultureProductionLivestock CattleandCalvesWasteEmissions MilkCows",
    "2801700009":
        "MiscellaneousAreaSources AgricultureProductionCrops FertilizerApplication AmmoniumPhosphatesseealsosubsets131415",
    "2801700008":
        "MiscellaneousAreaSources AgricultureProductionCrops FertilizerApplication OtherStraightNitrogen",
    "2701220000":
        "NaturalSources Biogenic VegetationAgriculture Total",
    "2801600000":
        "MiscellaneousAreaSources AgricultureProductionCrops CountryGrainElevators Total",
    "2325000000":
        "IndustrialProcesses MiningandQuarryingSIC10andSIC14 AllProcesses Total",
    "2311020000":
        "IndustrialProcesses ConstructionSIC1517 IndustrialCommercialInstitutional Total",
    "2325020000":
        "IndustrialProcesses MiningandQuarryingSIC10andSIC14 CrushedandBrokenStone Total",
    "2805001000":
        "MiscellaneousAreaSources AgricultureProductionLivestock DustkickedupbyLivestock Beefcattlefinishingoperationsonfeedlotsdrylots",
    "2801000000":
        "MiscellaneousAreaSources AgricultureProductionCrops AgricultureCrops Total",
    "2275085000":
        "MobileSources Aircraft UnpavedAirstrips Total",
    "2801000005":
        "MiscellaneousAreaSources AgricultureProductionCrops AgricultureCrops Harvesting",
    "2296005000":
        "MobileSources UnpavedRoads PublicUnpavedRoads TotalFugitives",
    "2294010000":
        "MobileSources PavedRoads AllOtherPublicPavedRoads TotalFugitives",
    "2302040000":
        "IndustrialProcesses FoodandKindredProductsSIC20 GrainMillProducts Total",
    "2307020000":
        "IndustrialProcesses WoodProductsSIC24 SawmillsPlaningMills Total",
    "2302010000":
        "IndustrialProcesses FoodandKindredProductsSIC20 MeatProducts Total",
    "2309100080":
        "IndustrialProcesses FabricatedMetalsSIC34 CoatingEngravingandAlliedServices HotDipGalvanizingZinc",
    "2307060000":
        "IndustrialProcesses WoodProductsSIC24 MiscellaneousWoodProducts Total",
    "2304050000":
        "IndustrialProcesses SecondaryMetalProductionSIC33 NonferrousFoundriesCastings Total",
    "2801000002":
        "MiscellaneousAreaSources AgricultureProductionCrops AgricultureCrops Planting",
    "2801000008":
        "MiscellaneousAreaSources AgricultureProductionCrops AgricultureCrops Transport",
    "2302070001":
        "IndustrialProcesses FoodandKindredProductsSIC20 FermentationBeverages Breweries",
    "2401035000":
        "SolventUtilization SurfaceCoating PlasticProductsSIC308 TotalAllSolventTypes",
    "2461870999":
        "SolventUtilization MiscellaneousNonindustrialCommercial PesticideApplicationNonAgricultural NotElsewhereClassified",
    "2302070000":
        "IndustrialProcesses FoodandKindredProductsSIC20 FermentationBeverages Total",
    "2461800002":
        "SolventUtilization MiscellaneousNonindustrialCommercial PesticideApplicationAllProcesses SoilIncorporation",
    "2461200000":
        "SolventUtilization MiscellaneousNonindustrialCommercial AdhesivesandSealants TotalAllSolventTypes",
    "2501050060":
        "StorageandTransport PetroleumandPetroleumProductStorage BulkTerminalsAllEvaporativeLosses ResidualOil",
    "2501050030":
        "StorageandTransport PetroleumandPetroleumProductStorage BulkTerminalsAllEvaporativeLosses CrudeOil",
    "2501050180":
        "StorageandTransport PetroleumandPetroleumProductStorage BulkTerminalsAllEvaporativeLosses Kerosene",
    "2501995180":
        "StorageandTransport PetroleumandPetroleumProductStorage AllStorageTypesWorkingLoss Kerosene",
    "2501050090":
        "StorageandTransport PetroleumandPetroleumProductStorage BulkTerminalsAllEvaporativeLosses DistillateOil",
    "2501995060":
        "StorageandTransport PetroleumandPetroleumProductStorage AllStorageTypesWorkingLoss ResidualOil",
    "2501050150":
        "StorageandTransport PetroleumandPetroleumProductStorage BulkTerminalsAllEvaporativeLosses JetNaphtha",
    "2501995030":
        "StorageandTransport PetroleumandPetroleumProductStorage AllStorageTypesWorkingLoss CrudeOil",
    "2501995150":
        "StorageandTransport PetroleumandPetroleumProductStorage AllStorageTypesWorkingLoss JetNaphtha",
    "2501995090":
        "StorageandTransport PetroleumandPetroleumProductStorage AllStorageTypesWorkingLoss DistillateOil",
    "2501070000":
        "StorageandTransport PetroleumandPetroleumProductStorage DieselServiceStations TotalAllProductsAllProcesses",
    "2301030000":
        "IndustrialProcesses ChemicalManufacturingSIC28 ProcessEmissionsfromPharmaceuticalManufNAPAPcat.106 Total",
    "2301040000":
        "IndustrialProcesses ChemicalManufacturingSIC28 FugitiveEmissionsfromSyntheticOrganicChemManufNAPAPcat.102 Total",
    "2505020900":
        "StorageandTransport PetroleumandPetroleumProductTransport MarineVessel TankCleaning",
    "2420010370":
        "SolventUtilization DryCleaning CommercialIndustrialCleaners SpecialNaphthas",
    "2415015000":
        "SolventUtilization Degreasing SecondaryMetalIndustriesSIC33AllProcesses TotalAllSolventTypes",
    "2310011502":
        "IndustrialProcesses OilandGasExplorationandProduction OnShoreOilProduction FugitivesFlanges",
    "2310010700":
        "IndustrialProcesses OilandGasExplorationandProduction CrudePetroleum OilWellFugitives",
    "2310011020":
        "IndustrialProcesses OilandGasExplorationandProduction OnShoreOilProduction StorageTanksCrudeOil",
    "2310021010":
        "IndustrialProcesses OilandGasExplorationandProduction OnShoreGasProduction StorageTanksCondensate",
    "2310011505":
        "IndustrialProcesses OilandGasExplorationandProduction OnShoreOilProduction FugitivesValves",
    "2310011501":
        "IndustrialProcesses OilandGasExplorationandProduction OnShoreOilProduction FugitivesConnectors",
    "2310021501":
        "IndustrialProcesses OilandGasExplorationandProduction OnShoreGasProduction FugitivesConnectors",
    "2310021504":
        "IndustrialProcesses OilandGasExplorationandProduction OnShoreGasProduction FugitivesPumps",
    "2310011450":
        "IndustrialProcesses OilandGasExplorationandProduction OnShoreOilProduction Wellhead",
    "2310121401":
        "IndustrialProcesses OilandGasExplorationandProduction OnShoreGasExploration GasWellPneumaticPumps",
    "2310021506":
        "IndustrialProcesses OilandGasExplorationandProduction OnShoreGasProduction FugitivesOther",
    "2310011503":
        "IndustrialProcesses OilandGasExplorationandProduction OnShoreOilProduction FugitivesOpenEndedLines",
    "2310011506":
        "IndustrialProcesses OilandGasExplorationandProduction OnShoreOilProduction FugitivesOther",
    "2310011201":
        "IndustrialProcesses OilandGasExplorationandProduction OnShoreOilProduction TankTruckRailcarLoadingCrudeOil",
    "2310021505":
        "IndustrialProcesses OilandGasExplorationandProduction OnShoreGasProduction FugitivesValves",
    "2310021600":
        "IndustrialProcesses OilandGasExplorationandProduction OnShoreGasProduction GasWellVenting",
    "2310010200":
        "IndustrialProcesses OilandGasExplorationandProduction CrudePetroleum OilWellTanksFlashing&StandingWorkingBreathing",
    "2310021503":
        "IndustrialProcesses OilandGasExplorationandProduction OnShoreGasProduction FugitivesOpenEndedLines",
    "2310011504":
        "IndustrialProcesses OilandGasExplorationandProduction OnShoreOilProduction FugitivesPumps",
    "2310021502":
        "IndustrialProcesses OilandGasExplorationandProduction OnShoreGasProduction FugitivesFlanges",
    "2310020700":
        "IndustrialProcesses OilandGasExplorationandProduction NaturalGas GasWellFugitives",
    "2310111700":
        "IndustrialProcesses OilandGasExplorationandProduction OnShoreOilExploration OilWellCompletionAllProcesses",
    "2310021030":
        "IndustrialProcesses OilandGasExplorationandProduction OnShoreGasProduction TankTruckRailcarLoadingCondensate",
    "2310021300":
        "IndustrialProcesses OilandGasExplorationandProduction OnShoreGasProduction GasWellPneumaticDevices",
    "2310111702":
        "IndustrialProcesses OilandGasExplorationandProduction OnShoreOilExploration OilWellCompletionVenting",
    "2515040000":
        "StorageandTransport OrganicChemicalTransport Pipeline TotalAllProducts",
    "2501060102":
        "StorageandTransport PetroleumandPetroleumProductStorage GasolineServiceStations Stage2DisplacementLossControlled",
    "2501000150":
        "StorageandTransport PetroleumandPetroleumProductStorage AllStorageTypesBreathingLoss JetNaphtha",
    "2461160000":
        "SolventUtilization MiscellaneousNonindustrialCommercial TankDrumCleaningAllProcesses TotalAllSolventTypes",
    "2850000000":
        "MiscellaneousAreaSources HealthServices Hospitals TotalAllOperations",
    "2461000000":
        "SolventUtilization MiscellaneousNonindustrialCommercial AllProcesses TotalAllSolventTypes",
    "2635000000":
        "WasteDisposalTreatmentandRecovery SoilandGroundwaterRemediation AllCategories Total",
    "2510010000":
        "StorageandTransport OrganicChemicalStorage CommercialIndustrialBreathingLoss TotalAllProducts",
    "2310021251":
        "IndustrialProcesses OilandGasExplorationandProduction OnShoreGasProduction LateralCompressors4CycleLeanBurn",
    "2310000550":
        "IndustrialProcesses OilandGasExplorationandProduction AllProcesses ProducedWater",
    "2310000660":
        "IndustrialProcesses OilandGasExplorationandProduction AllProcesses HydraulicFracturingEngines",
    "2310010300":
        "IndustrialProcesses OilandGasExplorationandProduction CrudePetroleum OilWellPneumaticDevices",
    "2310121100":
        "IndustrialProcesses OilandGasExplorationandProduction OnShoreGasExploration MudDegassing",
    "2310011000":
        "IndustrialProcesses OilandGasExplorationandProduction OnShoreOilProduction TotalAllProcesses",
    "2310111100":
        "IndustrialProcesses OilandGasExplorationandProduction OnShoreOilExploration MudDegassing",
    "2310021603":
        "IndustrialProcesses OilandGasExplorationandProduction OnShoreGasProduction GasWellVentingBlowdowns",
    "2310021351":
        "IndustrialProcesses OilandGasExplorationandProduction OnShoreGasProduction LateralCompressors4CycleRichBurn",
    "2310111401":
        "IndustrialProcesses OilandGasExplorationandProduction OnShoreOilExploration OilWellPneumaticPumps",
    "2310023310":
        "IndustrialProcesses OilandGasExplorationandProduction CoalBedMethaneNaturalGas PneumaticPumps",
    "2310023513":
        "IndustrialProcesses OilandGasExplorationandProduction CoalBedMethaneNaturalGas FugitivesOpenEndedLines",
    "2310023030":
        "IndustrialProcesses OilandGasExplorationandProduction CoalBedMethaneNaturalGas TankTruckRailcarLoadingCondensate",
    "2310023302":
        "IndustrialProcesses OilandGasExplorationandProduction CoalBedMethaneNaturalGas CBMFired4CycleRichBurnCompressorEngines50To499HP",
    "2310021500":
        "IndustrialProcesses OilandGasExplorationandProduction OnShoreGasProduction GasWellCompletionFlaring",
    "2310023516":
        "IndustrialProcesses OilandGasExplorationandProduction CoalBedMethaneNaturalGas FugitivesOther",
    "2310023400":
        "IndustrialProcesses OilandGasExplorationandProduction CoalBedMethaneNaturalGas Dehydrators",
    "2310023102":
        "IndustrialProcesses OilandGasExplorationandProduction CoalBedMethaneNaturalGas CBMFired2CycleLeanBurnCompressorEngines50To499HP",
    "2310021310":
        "IndustrialProcesses OilandGasExplorationandProduction OnShoreGasProduction GasWellPneumaticPumps",
    "2310023251":
        "IndustrialProcesses OilandGasExplorationandProduction CoalBedMethaneNaturalGas LateralCompressors4CycleLeanBurn",
    "2310023512":
        "IndustrialProcesses OilandGasExplorationandProduction CoalBedMethaneNaturalGas FugitivesFlanges",
    "2310023010":
        "IndustrialProcesses OilandGasExplorationandProduction CoalBedMethaneNaturalGas StorageTanksCondensate",
    "2310023300":
        "IndustrialProcesses OilandGasExplorationandProduction CoalBedMethaneNaturalGas PneumaticDevices",
    "2310023600":
        "IndustrialProcesses OilandGasExplorationandProduction CoalBedMethaneNaturalGas CBMWellCompletionAllProcesses",
    "2310023515":
        "IndustrialProcesses OilandGasExplorationandProduction CoalBedMethaneNaturalGas FugitivesValves",
    "2310023202":
        "IndustrialProcesses OilandGasExplorationandProduction CoalBedMethaneNaturalGas CBMFired4CycleLeanBurnCompressorEngines50To499HP",
    "2310023351":
        "IndustrialProcesses OilandGasExplorationandProduction CoalBedMethaneNaturalGas LateralCompressors4CycleRichBurn",
    "2310023606":
        "IndustrialProcesses OilandGasExplorationandProduction CoalBedMethaneNaturalGas MudDegassing",
    "2310023603":
        "IndustrialProcesses OilandGasExplorationandProduction CoalBedMethaneNaturalGas CBMWellVentingBlowdowns",
    "2310000230":
        "IndustrialProcesses OilandGasExplorationandProduction AllProcesses WorkoverRigs",
    "2310023511":
        "IndustrialProcesses OilandGasExplorationandProduction CoalBedMethaneNaturalGas FugitivesConnectors",
    "2310021700":
        "IndustrialProcesses OilandGasExplorationandProduction OnShoreGasProduction MiscellaneousEngines",
    "2310002411":
        "IndustrialProcesses OilandGasExplorationandProduction OffShoreOilAndGasProduction PressureLevelControllers",
    "2310012020":
        "IndustrialProcesses OilandGasExplorationandProduction OffShoreOilProduction StorageTanksCrudeOil",
    "2310022010":
        "IndustrialProcesses OilandGasExplorationandProduction OffShoreGasProduction StorageTanksCondensate",
    "2310012521":
        "IndustrialProcesses OilandGasExplorationandProduction OffShoreOilProduction FugitivesConnectorsOilWaterStreams",
    "2310022420":
        "IndustrialProcesses OilandGasExplorationandProduction OffShoreGasProduction Dehydrator",
    "2310012526":
        "IndustrialProcesses OilandGasExplorationandProduction OffShoreOilProduction FugitivesOtherOilWater",
    "2310022505":
        "IndustrialProcesses OilandGasExplorationandProduction OffShoreGasProduction FugitivesValvesGas",
    "2310012515":
        "IndustrialProcesses OilandGasExplorationandProduction OffShoreOilProduction FugitivesValvesOil",
    "2310012511":
        "IndustrialProcesses OilandGasExplorationandProduction OffShoreOilProduction FugitivesConnectorsOilStreams",
    "2310112401":
        "IndustrialProcesses OilandGasExplorationandProduction OffShoreOilExploration OilWellPneumaticPumps",
    "2310022501":
        "IndustrialProcesses OilandGasExplorationandProduction OffShoreGasProduction FugitivesConnectorsGasStreams",
    "2310022506":
        "IndustrialProcesses OilandGasExplorationandProduction OffShoreGasProduction FugitivesOtherGas",
    "2310022502":
        "IndustrialProcesses OilandGasExplorationandProduction OffShoreGasProduction FugitivesFlangesGasStreams",
    "2310012522":
        "IndustrialProcesses OilandGasExplorationandProduction OffShoreOilProduction FugitivesFlangesOilWater",
    "2310012512":
        "IndustrialProcesses OilandGasExplorationandProduction OffShoreOilProduction FugitivesFlangesOil",
    "2310002421":
        "IndustrialProcesses OilandGasExplorationandProduction OffShoreOilAndGasProduction ColdVents",
    "2310022105":
        "IndustrialProcesses OilandGasExplorationandProduction OffShoreGasProduction DieselEngines",
    "2310002401":
        "IndustrialProcesses OilandGasExplorationandProduction OffShoreOilAndGasProduction PneumaticPumpsGasAndOilWells",
    "2310012516":
        "IndustrialProcesses OilandGasExplorationandProduction OffShoreOilProduction FugitivesOtherOil",
    "2310122100":
        "IndustrialProcesses OilandGasExplorationandProduction OffShoreGasExploration MudDegassing",
    "2310021209":
        "IndustrialProcesses OilandGasExplorationandProduction OnShoreGasProduction TotalAllNaturalGasFired4CycleLeanBurnCompressorEngines",
    "2310021309":
        "IndustrialProcesses OilandGasExplorationandProduction OnShoreGasProduction TotalAllNaturalGasFired4CycleRichBurnCompressorEngines",
    "2310021601":
        "IndustrialProcesses OilandGasExplorationandProduction OnShoreGasProduction GasWellVentingInitialCompletions",
    "2310010800":
        "IndustrialProcesses OilandGasExplorationandProduction CrudePetroleum OilWellTruckLoading",
    "2310020800":
        "IndustrialProcesses OilandGasExplorationandProduction NaturalGas GasWellTruckLoading",
    "2310030300":
        "IndustrialProcesses OilandGasExplorationandProduction NaturalGasLiquids GasWellWaterTankLosses",
    "2310011500":
        "IndustrialProcesses OilandGasExplorationandProduction OnShoreOilProduction FugitivesAllProcesses",
    "2310023601":
        "IndustrialProcesses OilandGasExplorationandProduction CoalBedMethaneNaturalGas VentingInitialCompletions",
    "2310030401":
        "IndustrialProcesses OilandGasExplorationandProduction NaturalGasLiquids GasPlantTruckLoading",
    "2310030210":
        "IndustrialProcesses OilandGasExplorationandProduction NaturalGasLiquids GasWellTanksFlashing&StandingWorkingBreathingUncontrolled",
    "2310023602":
        "IndustrialProcesses OilandGasExplorationandProduction CoalBedMethaneNaturalGas VentingRecompletions",
    "2310023509":
        "IndustrialProcesses OilandGasExplorationandProduction CoalBedMethaneNaturalGas Fugitives",
    "2310011600":
        "IndustrialProcesses OilandGasExplorationandProduction OnShoreOilProduction ArtificialLiftEngines",
    "2310021602":
        "IndustrialProcesses OilandGasExplorationandProduction OnShoreGasProduction GasWellVentingRecompletions",
    "2310021604":
        "IndustrialProcesses OilandGasExplorationandProduction OnShoreGasProduction GasWellVentingCompressorStartups",
    "2310021605":
        "IndustrialProcesses OilandGasExplorationandProduction OnShoreGasProduction GasWellVentingCompressorShutdowns",
    "2505010000":
        "StorageandTransport PetroleumandPetroleumProductTransport RailTankCar TotalAllProducts",
    "2460270000":
        "SolventUtilization MiscellaneousNonindustrialConsumerandCommercial HouseholdProductsShoeandLeatherCareProducts TotalAllSolventTypes",
    "2460610000":
        "SolventUtilization MiscellaneousNonindustrialConsumerandCommercial AdhesivesandSealantsAdhesives TotalAllSolventTypes",
    "2460110000":
        "SolventUtilization MiscellaneousNonindustrialConsumerandCommercial PersonalCareProductsHairCareProducts TotalAllSolventTypes",
    "2460510000":
        "SolventUtilization MiscellaneousNonindustrialConsumerandCommercial CoatingsandRelatedProductsAerosolSprayPaints TotalAllSolventTypes",
    "2460820000":
        "SolventUtilization MiscellaneousNonindustrialConsumerandCommercial FIFRARelatedProductsFungicidesandNematicides TotalAllSolventTypes",
    "2460520000":
        "SolventUtilization MiscellaneousNonindustrialConsumerandCommercial CoatingsandRelatedProductsCoatingRelatedProducts TotalAllSolventTypes",
    "2460290000":
        "SolventUtilization MiscellaneousNonindustrialConsumerandCommercial HouseholdProductsMiscellaneousHouseholdProducts TotalAllSolventTypes",
    "2460410000":
        "SolventUtilization MiscellaneousNonindustrialConsumerandCommercial AutomotiveAftermarketProductsDetailingProducts TotalAllSolventTypes",
    "2460810000":
        "SolventUtilization MiscellaneousNonindustrialConsumerandCommercial FIFRARelatedProductsInsecticides TotalAllSolventTypes",
    "2460420000":
        "SolventUtilization MiscellaneousNonindustrialConsumerandCommercial AutomotiveAftermarketProductsMaintenanceandRepairProducts TotalAllSolventTypes",
    "2460230000":
        "SolventUtilization MiscellaneousNonindustrialConsumerandCommercial HouseholdProductsFabricandCarpetCareProducts TotalAllSolventTypes",
    "2460250000":
        "SolventUtilization MiscellaneousNonindustrialConsumerandCommercial HouseholdProductsWaxesandPolishes TotalAllSolventTypes",
    "2460130000":
        "SolventUtilization MiscellaneousNonindustrialConsumerandCommercial PersonalCareProductsFragranceProducts TotalAllSolventTypes",
    "2460190000":
        "SolventUtilization MiscellaneousNonindustrialConsumerandCommercial PersonalCareProductsMiscellaneousPersonalCareProducts TotalAllSolventTypes",
    "2460150000":
        "SolventUtilization MiscellaneousNonindustrialConsumerandCommercial PersonalCareProductsNailCareProducts TotalAllSolventTypes",
    "2505020121":
        "StorageandTransport PetroleumandPetroleumProductTransport MarineVessel GasolineBarge",
    "2460220000":
        "SolventUtilization MiscellaneousNonindustrialConsumerandCommercial HouseholdProductsLaundryProducts TotalAllSolventTypes",
    "2801500141":
        "MiscellaneousAreaSources AgricultureProductionCrops AgriculturalFieldBurningwholefieldsetonfire FieldCropisBeanredHeadfireBurning",
    "2505030150":
        "StorageandTransport PetroleumandPetroleumProductTransport Truck JetNaphtha",
    "2801500440":
        "MiscellaneousAreaSources AgricultureProductionCrops AgriculturalFieldBurningwholefieldsetonfire OrchardCropisWalnut",
    "2801500450":
        "MiscellaneousAreaSources AgricultureProductionCrops AgriculturalFieldBurningwholefieldsetonfire OrchardCropisFilbertHazelnut",
    "2630020020":
        "WasteDisposalTreatmentandRecovery WastewaterTreatment PublicOwned BiosolidsProcessesTotal",
    "2310023100":
        "IndustrialProcesses OilandGasExplorationandProduction CoalBedMethaneNaturalGas CBMWellHeaters",
    "2310022090":
        "IndustrialProcesses OilandGasExplorationandProduction OffShoreGasProduction BoilersHeatersNaturalGas",
    "2460180000":
        "SolventUtilization MiscellaneousNonindustrialConsumerandCommercial PersonalCareProductsHealthUseProductsExternalOnly TotalAllSolventTypes",
    "2415055000":
        "SolventUtilization Degreasing AutomotiveDealersSIC55AllProcesses TotalAllSolventTypes",
    "2415010000":
        "SolventUtilization Degreasing PrimaryMetalIndustriesSIC33AllProcesses TotalAllSolventTypes",
    "2415060000":
        "SolventUtilization Degreasing MiscellaneousRepairServicesSIC76AllProcesses TotalAllSolventTypes",
    "2460120000":
        "SolventUtilization MiscellaneousNonindustrialConsumerandCommercial PersonalCareProductsDeodorantsandAntiperspirants TotalAllSolventTypes",
    "2460160000":
        "SolventUtilization MiscellaneousNonindustrialConsumerandCommercial PersonalCareProductsFacialandBodyTreatments TotalAllSolventTypes",
    "2460210000":
        "SolventUtilization MiscellaneousNonindustrialConsumerandCommercial HouseholdProductsHardSurfaceCleaners TotalAllSolventTypes",
    "2460170000":
        "SolventUtilization MiscellaneousNonindustrialConsumerandCommercial PersonalCareProductsOralCareProducts TotalAllSolventTypes",
    "2801520004":
        "MiscellaneousAreaSources AgricultureProductionCrops OrchardHeaters Diesel",
    "2104008420":
        "StationarySourceFuelCombustion Residential Wood WoodstovepelletfiredEPAcertifiedfreestandingorFPinsert",
    "2461850052":
        "SolventUtilization MiscellaneousNonindustrialCommercial PesticideApplicationAgricultural OtherPesticidesApples",
    "2461850053":
        "SolventUtilization MiscellaneousNonindustrialCommercial PesticideApplicationAgricultural OtherPesticidesGrapes",
    "2505020093":
        "StorageandTransport PetroleumandPetroleumProductTransport MarineVessel DistillateOilMarineDieselBarge",
    "2461850054":
        "SolventUtilization MiscellaneousNonindustrialCommercial PesticideApplicationAgricultural OtherPesticidesPotatoes",
    "2325060000":
        "IndustrialProcesses MiningandQuarryingSIC10andSIC14 LeadOreMiningandMilling Total",
    "2620030001":
        "WasteDisposalTreatmentandRecovery Landfills Municipal DumpingCrushingSpreadingofNewMaterialsworkingface",
    "2650000002":
        "WasteDisposalTreatmentandRecovery ScrapandWasteMaterials ScrapandWasteMaterials Shredding",
    "2402000000":
        "SolventUtilization PaintStrippers ChemicalStrippers ApplicationDegradationandCoatingRemovalStepsOtherNotListed",
    "2310002000":
        "IndustrialProcesses OilandGasExplorationandProduction OffShoreOilAndGasProduction TotalAllProcesses",
    "2310012000":
        "IndustrialProcesses OilandGasExplorationandProduction OffShoreOilProduction TotalAllProcesses",
    "2310002305":
        "IndustrialProcesses OilandGasExplorationandProduction OffShoreOilAndGasProduction FlaresFlaringOperations",
    "2310022000":
        "IndustrialProcesses OilandGasExplorationandProduction OffShoreGasProduction TotalAllProcesses",
    "2310022051":
        "IndustrialProcesses OilandGasExplorationandProduction OffShoreGasProduction TurbinesNaturalGas",
    "2310002301":
        "IndustrialProcesses OilandGasExplorationandProduction OffShoreOilAndGasProduction FlaresContinuousPilotLight",
    "2310022410":
        "IndustrialProcesses OilandGasExplorationandProduction OffShoreGasProduction AmineUnit",
    "2310021011":
        "IndustrialProcesses OilandGasExplorationandProduction OnShoreGasProduction CondensateTankFlaring",
    "2310021411":
        "IndustrialProcesses OilandGasExplorationandProduction OnShoreGasProduction GasWellDehydratorsFlaring",
    "2830001000":
        "MiscellaneousAreaSources CatastrophicAccidentalReleases IndustrialAccidents Total",
    "2280004000":
        "MobileSources MarineVesselsCommercial Gasoline TotalAllVesselTypes",
    "2801520010":
        "MiscellaneousAreaSources AgricultureProductionCrops OrchardHeaters Propane",
    "2630040000":
        "WasteDisposalTreatmentandRecovery WastewaterTreatment PublicOwned AmmoniapHControl",
    "2294005000":
        "MobileSources PavedRoads InterstateArterial TotalFugitives",
    "2311000070":
        "IndustrialProcesses ConstructionSIC1517 AllProcesses VehicleTraffic",
    "2296010000":
        "MobileSources UnpavedRoads IndustrialUnpavedRoads TotalFugitives",
    "2311040000":
        "IndustrialProcesses ConstructionSIC1517 SpecialTradeConstruction Total",
    "2294000002":
        "MobileSources PavedRoads AllPavedRoads TotalSandingSaltingFugitives",
    "2461850003":
        "SolventUtilization MiscellaneousNonindustrialCommercial PesticideApplicationAgricultural HerbicidesGrapes",
    "2461850002":
        "SolventUtilization MiscellaneousNonindustrialCommercial PesticideApplicationAgricultural HerbicidesApples",
    "2801500171":
        "MiscellaneousAreaSources AgricultureProductionCrops AgriculturalFieldBurningwholefieldsetonfire Fallow",
    "2801500160":
        "MiscellaneousAreaSources AgricultureProductionCrops AgriculturalFieldBurningwholefieldsetonfire FieldCropisCottonBurningTechniquesNotImportant",
    "2801500263":
        "MiscellaneousAreaSources AgricultureProductionCrops AgriculturalFieldBurningwholefieldsetonfire DoubleCropWinterWheatandCotton",
    "2310421010":
        "IndustrialProcesses OilandGasExplorationandProduction OnShoreGasProductionUnconventional StorageTanksCondensate",
    "2801500264":
        "MiscellaneousAreaSources AgricultureProductionCrops AgriculturalFieldBurningwholefieldsetonfire DoubleCropWinterWheatandSoybeans",
    "2805001010":
        "MiscellaneousAreaSources AgricultureProductionLivestock DustkickedupbyLivestock DairyCattle",
    "2805001020":
        "MiscellaneousAreaSources AgricultureProductionLivestock DustkickedupbyLivestock Broilers",
    "2805001040":
        "MiscellaneousAreaSources AgricultureProductionLivestock DustkickedupbyLivestock Swine",
    "2805001050":
        "MiscellaneousAreaSources AgricultureProductionLivestock DustkickedupbyLivestock Turkeys",
    "2805001030":
        "MiscellaneousAreaSources AgricultureProductionLivestock DustkickedupbyLivestock Layers",
    "2801500161":
        "MiscellaneousAreaSources AgricultureProductionCrops AgriculturalFieldBurningwholefieldsetonfire DoubleCropSoybeansandCotton",
    "2104008530":
        "StationarySourceFuelCombustion Residential Wood FurnaceIndoorpelletfiredgeneral",
    "2310011001":
        "IndustrialProcesses OilandGasExplorationandProduction OnShoreOilProduction AssociatedGasVenting",
    "2104008620":
        "StationarySourceFuelCombustion Residential Wood Hydronicheaterindoor",
    "2104008630":
        "StationarySourceFuelCombustion Residential Wood Hydronicheaterpelletfired",
    "2310321100":
        "IndustrialProcesses OilandGasExplorationandProduction OnShoreGasProductionConventional GasWellHeaters",
    "2801500151":
        "MiscellaneousAreaSources AgricultureProductionCrops AgriculturalFieldBurningwholefieldsetonfire DoubleCropWinterWheatandCorn",
    "2310321400":
        "IndustrialProcesses OilandGasExplorationandProduction OnShoreGasProductionConventional GasWellDehydrators",
    "2801500142":
        "MiscellaneousAreaSources AgricultureProductionCrops AgriculturalFieldBurningwholefieldsetonfire FieldCropisBeanredBackfireBurning",
    "2280002101":
        "MobileSources MarineVesselsCommercial Diesel C1C2PortemissionsMainEngine",
    "2280002202":
        "MobileSources MarineVesselsCommercial Diesel C1C2UnderwayemissionsAuxiliaryEngine",
    "2280002201":
        "MobileSources MarineVesselsCommercial Diesel C1C2UnderwayemissionsMainEngine",
    "2280002102":
        "MobileSources MarineVesselsCommercial Diesel C1C2PortemissionsAuxiliaryEngine",
    "2310030400":
        "IndustrialProcesses OilandGasExplorationandProduction NaturalGasLiquids TruckLoading",
    "2310400220":
        "IndustrialProcesses OilandGasExplorationandProduction AllProcessesUnconventional DrillRigs",
    "2310421100":
        "IndustrialProcesses OilandGasExplorationandProduction OnShoreGasProductionUnconventional GasWellHeaters",
    "2310111701":
        "IndustrialProcesses OilandGasExplorationandProduction OnShoreOilExploration OilWellCompletionFlaring",
    "2310321603":
        "IndustrialProcesses OilandGasExplorationandProduction OnShoreGasProductionConventional GasWellVentingBlowdowns",
    "2310030220":
        "IndustrialProcesses OilandGasExplorationandProduction NaturalGasLiquids GasWellTanksFlashing&StandingWorkingBreathingControlled",
    "2310000553":
        "IndustrialProcesses OilandGasExplorationandProduction AllProcesses ProducedWaterfromOilWells",
    "2620010000":
        "WasteDisposalTreatmentandRecovery Landfills Industrial Total",
    "2310000551":
        "IndustrialProcesses OilandGasExplorationandProduction AllProcesses ProducedWaterfromCBMWells",
    "2310000552":
        "IndustrialProcesses OilandGasExplorationandProduction AllProcesses ProducedWaterfromGasWells",
    "2310023000":
        "IndustrialProcesses OilandGasExplorationandProduction CoalBedMethaneNaturalGas DewateringPumpEngines",
    "2310021803":
        "IndustrialProcesses OilandGasExplorationandProduction OnShoreGasProduction Midstreamgasventingformaintenancestartupshutdownormalfunction",
    "2310021801":
        "IndustrialProcesses OilandGasExplorationandProduction OnShoreGasProduction PipelineBlowdownsandPigging",
    "2310021802":
        "IndustrialProcesses OilandGasExplorationandProduction OnShoreGasProduction PipelineLeaks",
    "2801500152":
        "MiscellaneousAreaSources AgricultureProductionCrops AgriculturalFieldBurningwholefieldsetonfire DoubleCropCornandSoybeans",
    "2306010100":
        "IndustrialProcesses PetroleumRefiningSIC29 AsphaltMixingPlantsandPavingRoofingMaterials AsphaltMixingPlantsTotal",
    "2310300220":
        "IndustrialProcesses OilandGasExplorationandProduction AllProcessesConventional DrillRigs",
    "2310321010":
        "IndustrialProcesses OilandGasExplorationandProduction OnShoreGasProductionConventional StorageTanksCondensate",
    "2310021412":
        "IndustrialProcesses OilandGasExplorationandProduction OnShoreGasProduction GasWellDehydratorsReboiler",
    "2310421603":
        "IndustrialProcesses OilandGasExplorationandProduction OnShoreGasProductionUnconventional GasWellVentingBlowdowns",
    "2310023401":
        "IndustrialProcesses OilandGasExplorationandProduction CoalBedMethaneNaturalGas DehydratorsReboiler",
    "2310421400":
        "IndustrialProcesses OilandGasExplorationandProduction OnShoreGasProductionUnconventional GasWellDehydrators",
    "2280002204":
        "MobileSources MarineVesselsCommercial Diesel C3UnderwayemissionsAuxiliaryEngine",
    "2420000999":
        "SolventUtilization DryCleaning AllProcesses SolventsNEC",
    "2280002203":
        "MobileSources MarineVesselsCommercial Diesel C3UnderwayemissionsMainEngine",
    "2310001000":
        "IndustrialProcesses OilandGasExplorationandProduction AllProcessesOnshore TotalAllProcesses",
    "2801500112":
        "MiscellaneousAreaSources AgricultureProductionCrops AgriculturalFieldBurningwholefieldsetonfire FieldCropisAlfalfaBackfireBurning",
    "2801500182":
        "MiscellaneousAreaSources AgricultureProductionCrops AgriculturalFieldBurningwholefieldsetonfire FieldCropisHaywildBackfireBurning",
    "2801500202":
        "MiscellaneousAreaSources AgricultureProductionCrops AgriculturalFieldBurningwholefieldsetonfire FieldCropisPeaBackfireBurning",
    "2801500192":
        "MiscellaneousAreaSources AgricultureProductionCrops AgriculturalFieldBurningwholefieldsetonfire FieldCropisOatsBackfireBurning",
    "2310021450":
        "IndustrialProcesses OilandGasExplorationandProduction OnShoreGasProduction Wellhead",
    "2280002104":
        "MobileSources MarineVesselsCommercial Diesel C3PortemissionsAuxiliaryEngine",
    "2280002103":
        "MobileSources MarineVesselsCommercial Diesel C3PortemissionsMainEngine",
    "2280003204":
        "MobileSources MarineVesselsCommercial Residual C3UnderwayemissionsAuxiliaryEngine",
    "2280003104":
        "MobileSources MarineVesselsCommercial Residual C3PortemissionsAuxiliaryEngine",
    "2280003103":
        "MobileSources MarineVesselsCommercial Residual C3PortemissionsMainEngine",
    "2280003203":
        "MobileSources MarineVesselsCommercial Residual C3UnderwayemissionsMainEngine",
    "2310021109":
        "IndustrialProcesses OilandGasExplorationandProduction OnShoreGasProduction TotalAllNaturalGasFired2CycleLeanBurnCompressorEngines",
    "2102010000":
        "StationarySourceFuelCombustion Industrial ProcessGas TotalAllBoilerTypes",
    "2810005000":
        "MiscellaneousAreaSources OtherCombustion ManagedBurningSlashLoggingDebris UnspecifiedBurnMethoduse2610000500fornonloggingdebris",
    "2501070053":
        "StorageandTransport PetroleumandPetroleumProductStorage DieselServiceStations Stage1BalancedSubmergedFilling",
    "2801700000":
        "MiscellaneousAreaSources AgricultureProductionCrops FertilizerApplication TotalFertilizers",
    "2801000007":
        "MiscellaneousAreaSources AgricultureProductionCrops AgricultureCrops Loading",
    "2501070201":
        "StorageandTransport PetroleumandPetroleumProductStorage DieselServiceStations UndergroundTankBreathingandEmptying",
    "2460140000":
        "SolventUtilization MiscellaneousNonindustrialConsumerandCommercial PersonalCareProductsPowders TotalAllSolventTypes",
    "2401001050":
        "SolventUtilization SurfaceCoating ArchitecturalCoatings AllOtherArchitecturalCategories",
    "2310012525":
        "IndustrialProcesses OilandGasExplorationandProduction OffShoreOilProduction FugitivesValvesOilWater",
    "2801500201":
        "MiscellaneousAreaSources AgricultureProductionCrops AgriculturalFieldBurningwholefieldsetonfire FieldCropisPeaHeadfireBurning",
    "2461024000":
        "SolventUtilization MiscellaneousNonindustrialCommercial AsphaltPipeCoating TotalAllSolventTypes",
    "2311010070":
        "IndustrialProcesses ConstructionSIC1517 Residential VehicleTraffic",
    "2801500120":
        "MiscellaneousAreaSources AgricultureProductionCrops AgriculturalFieldBurningwholefieldsetonfire FieldCropisAsparagusBurningTechniquesNotSignificant",
    "2801500400":
        "MiscellaneousAreaSources AgricultureProductionCrops AgriculturalFieldBurningwholefieldsetonfire OrchardCropisOlive",
    "2801500360":
        "MiscellaneousAreaSources AgricultureProductionCrops AgriculturalFieldBurningwholefieldsetonfire OrchardCropisCitrusorangelemon",
    "2309100200":
        "IndustrialProcesses FabricatedMetalsSIC34 CoatingEngravingandAlliedServices AbrasiveBlasting"
}
