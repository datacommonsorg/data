# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https: #www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""UNData Country codes mapped to DataCommons"""

from typing import List

# Map from UNData country codes to dcids.
# This includes some older country coded marked as '(additional)'
UN_COUNTRY_CODES = {
    4: 'country/AFG',  # Afghanistan, AF
    8: 'country/ALB',  # Albania, AL
    12: 'country/DZA',  # Algeria, DZ
    16: 'country/ASM',  # American Samoa, AS
    20: 'country/AND',  # Andorra, AD
    24: 'country/AGO',  # Angola, AO
    660: 'country/AIA',  # Anguilla, AI
    10: 'country/ATA',  # Antarctica, AQ
    28: 'country/ATG',  # Antigua and Barbuda, AG
    32: 'country/ARG',  # Argentina, AR
    51: 'country/ARM',  # Armenia, AM
    533: 'country/ABW',  # Aruba, AW
    36: 'country/AUS',  # Australia, AU
    40: 'country/AUT',  # Austria, AT
    31: 'country/AZE',  # Azerbaijan, AZ
    44: 'country/BHS',  # Bahamas, BS
    48: 'country/BHR',  # Bahrain, BH
    50: 'country/BGD',  # Bangladesh, BD
    52: 'country/BRB',  # Barbados, BB
    112: 'country/BLR',  # Belarus, BY
    56: 'country/BEL',  # Belgium, BE
    84: 'country/BLZ',  # Belize, BZ
    204: 'country/BEN',  # Benin, BJ
    60: 'country/BMU',  # Bermuda, BM
    64: 'country/BTN',  # Bhutan, BT
    68: 'country/BOL',  # Bolivia, Plurinational State of, BO
    68: 'country/BOL',  # Bolivia, BO
    535: 'country/BES',  # Bonaire St Eustatius Saba, BQ
    70: 'country/BIH',  # Bosnia and Herzegovina, BA
    72: 'country/BWA',  # Botswana, BW
    74: 'country/BVT',  # Bouvet Island, BV
    76: 'country/BRA',  # Brazil, BR
    86: 'country/IOT',  # British Indian Ocean Territory, IO
    96: 'country/BRN',  # Brunei Darussalam, BN
    96: 'country/BRN',  # Brunei, BN
    100: 'country/BGR',  # Bulgaria, BG
    854: 'country/BFA',  # Burkina Faso, BF
    108: 'country/BDI',  # Burundi, BI
    116: 'country/KHM',  # Cambodia, KH
    120: 'country/CMR',  # Cameroon, CM
    124: 'country/CAN',  # Canada, CA
    132: 'country/CPV',  # Cape Verde, CV
    136: 'country/CYM',  # Cayman Islands, KY
    140: 'country/CAF',  # Central African Republic, CF
    148: 'country/TCD',  # Chad, TD
    152: 'country/CHL',  # Chile, CL
    156: 'country/CHN',  # China, CN
    162: 'country/CXR',  # Christmas Island, CX
    166: 'country/CCK',  # Cocos (Keeling) Islands, CC
    170: 'country/COL',  # Colombia, CO
    174: 'country/COM',  # Comoros, KM
    178: 'country/COG',  # Congo, CG
    180: 'country/COD',  # Congo, the Democratic Republic of the, CD
    184: 'country/COK',  # Cook Islands, CK
    188: 'country/CRI',  # Costa Rica, CR
    384: 'country/CIV',  # Côte d'Ivoire, CI
    384: 'country/CIV',  # Ivory Coast, CI
    191: 'country/HRV',  # Croatia, HR
    192: 'country/CUB',  # Cuba, CU
    531: 'country/CUW',  # Curacao, CW
    196: 'country/CYP',  # Cyprus, CY
    200: 'country/CZE',  # Czechoslovakia (former), CZ (additional)
    203: 'country/CZE',  # Czech Republic, CZ
    208: 'country/DNK',  # Denmark, DK
    262: 'country/DJI',  # Djibouti, DJ
    212: 'country/DMA',  # Dominica, DM
    214: 'country/DOM',  # Dominican Republic, DO
    218: 'country/ECU',  # Ecuador, EC
    818: 'country/EGY',  # Egypt, EG
    222: 'country/SLV',  # El Salvador, SV
    226: 'country/GNQ',  # Equatorial Guinea, GQ
    232: 'country/ERI',  # Eritrea, ER
    233: 'country/EST',  # Estonia, EE
    230: 'country/ETH',  # Ethiopia, incl. Eritrea, ET (additional)
    231: 'country/ETH',  # Ethiopia, ET
    238: 'country/FLK',  # Falkland Islands (Malvinas), FK
    234: 'country/FRO',  # Faroe Islands, FO
    242: 'country/FJI',  # Fiji, FJ
    246: 'country/FIN',  # Finland, FI
    250: 'country/FRA',  # France, FR
    251: 'country/FRA',  # France, FR (additional)
    254: 'country/GUF',  # French Guiana, GF
    255: 'country/GUF',  # French Guiana, GF (additional)
    258: 'country/PYF',  # French Polynesia, PF
    260: 'country/ATF',  # French Southern Territories, TF
    266: 'country/GAB',  # Gabon, GA
    270: 'country/GMB',  # Gambia, GM
    268: 'country/GEO',  # Georgia, GE
    276: 'country/DEU',  # Germany, DE
    278: 'country/DEU',  # German Dem. R. (former), DE (additional)
    280: 'country/DEU',  # German Dem. R. (former), DE (additional)
    288: 'country/GHA',  # Ghana, GH
    292: 'country/GIB',  # Gibraltar, GI
    300: 'country/GRC',  # Greece, GR
    304: 'country/GRL',  # Greenland, GL
    308: 'country/GRD',  # Grenada, GD
    312: 'country/GLP',  # Guadeloupe, GP
    313: 'country/GLP',  # Guadeloupe, GP (additional)
    316: 'country/GUM',  # Guam, GU
    320: 'country/GTM',  # Guatemala, GT
    831: 'country/GGY',  # Guernsey, GG
    324: 'country/GIN',  # Guinea, GN
    624: 'country/GNB',  # Guinea-Bissau, GW
    328: 'country/GUY',  # Guyana, GY
    332: 'country/HTI',  # Haiti, HT
    334: 'country/HMD',  # Heard Island and McDonald Islands, HM
    336: 'country/VAT',  # Holy See (Vatican City State), VA
    340: 'country/HND',  # Honduras, HN
    344: 'country/HKG',  # Hong Kong, HK
    348: 'country/HUN',  # Hungary, HU
    352: 'country/ISL',  # Iceland, IS
    356: 'country/IND',  # India, IN
    360: 'country/IDN',  # Indonesia, ID
    364: 'country/IRN',  # Iran, Islamic Republic of, IR
    368: 'country/IRQ',  # Iraq, IQ
    372: 'country/IRL',  # Ireland, IE
    833: 'country/IMN',  # Isle of Man, IM
    376: 'country/ISR',  # Israel, IL
    380: 'country/ITA',  # Italy, IT
    382: 'country/ITA',  # Italy, IT (additional)
    388: 'country/JAM',  # Jamaica, JM
    392: 'country/JPN',  # Japan, JP
    832: 'country/JEY',  # Jersey, JE
    400: 'country/JOR',  # Jordan, JO
    398: 'country/KAZ',  # Kazakhstan, KZ
    404: 'country/KEN',  # Kenya, KE
    296: 'country/KIR',  # Kiribati, KI
    408: 'country/PRK',  # Korea, Democratic People's Republic of, KP
    410: 'country/KOR',  # Korea, Republic of, KR
    410: 'country/KOR',  # South Korea, KR
    412: 'country/XXK',  # Kosovo, XK (additional)
    414: 'country/KWT',  # Kuwait, KW
    417: 'country/KGZ',  # Kyrgyzstan, KG
    418: 'country/LAO',  # Lao People's Democratic Republic, LA
    428: 'country/LVA',  # Latvia, LV
    422: 'country/LBN',  # Lebanon, LB
    426: 'country/LSO',  # Lesotho, LS
    430: 'country/LBR',  # Liberia, LR
    434: 'country/LBY',  # Libyan Arab Jamahiriya, LY
    434: 'country/LBY',  # Libya, LY
    438: 'country/LIE',  # Liechtenstein, LI
    440: 'country/LTU',  # Lithuania, LT
    442: 'country/LUX',  # Luxembourg, LU
    446: 'country/MAC',  # Macao, MO
    807: 'country/MKD',  # Macedonia, the former Yugoslav Republic of, MK
    450: 'country/MDG',  # Madagascar, MG
    454: 'country/MWI',  # Malawi, MW
    458: 'country/MYS',  # Malaysia, MY
    462: 'country/MDV',  # Maldives, MV
    466: 'country/MLI',  # Mali, ML
    470: 'country/MLT',  # Malta, MT
    584: 'country/MHL',  # Marshall Islands, MH
    474: 'country/MTQ',  # Martinique, MQ
    475: 'country/MTQ',  # Martinique, MQ (additional)
    478: 'country/MRT',  # Mauritania, MR
    480: 'country/MUS',  # Mauritius, MU
    175: 'country/MYT',  # Mayotte, YT
    176: 'country/MYT',  # Mayotte, YT (additional)
    484: 'country/MEX',  # Mexico, MX
    583: 'country/FSM',  # Micronesia, Federated States of, FM
    498: 'country/MDA',  # Moldova, Republic of, MD
    492: 'country/MCO',  # Monaco, MC
    496: 'country/MNG',  # Mongolia, MN
    499: 'country/MNE',  # Montenegro, ME
    500: 'country/MSR',  # Montserrat, MS
    504: 'country/MAR',  # Morocco, MA
    508: 'country/MOZ',  # Mozambique, MZ
    104: 'country/MMR',  # Myanmar, MM
    104: 'country/MMR',  # Burma, MM
    516: 'country/NAM',  # Namibia, NA
    520: 'country/NRU',  # Nauru, NR
    524: 'country/NPL',  # Nepal, NP
    528: 'country/NLD',  # Netherlands, NL
    530: 'country/ANT',  # Netherlands Antilles, AN
    540: 'country/NCL',  # New Caledonia, NC
    554: 'country/NZL',  # New Zealand, NZ
    558: 'country/NIC',  # Nicaragua, NI
    562: 'country/NER',  # Niger, NE
    566: 'country/NGA',  # Nigeria, NG
    570: 'country/NIU',  # Niue, NU
    574: 'country/NFK',  # Norfolk Island, NF
    580: 'country/MNP',  # Northern Mariana Islands, MP
    578: 'country/NOR',  # Norway, NO
    579: 'country/NOR',  # Norway, NO (additional)
    512: 'country/OMN',  # Oman, OM
    586: 'country/PAK',  # Pakistan, PK
    585: 'country/PLW',  # Palau, PW
    275: 'country/PSE',  # Palestinian Territory, Occupied, PS
    591: 'country/PAN',  # Panama, PA
    598: 'country/PNG',  # Papua New Guinea, PG
    600: 'country/PRY',  # Paraguay, PY
    582: 'country/PCI',  # Pacific Islands (former), (PC)
    604: 'country/PER',  # Peru, PE
    608: 'country/PHL',  # Philippines, PH
    612: 'country/PCN',  # Pitcairn, PN
    616: 'country/POL',  # Poland, PL
    620: 'country/PRT',  # Portugal, PT
    630: 'country/PRI',  # Puerto Rico, PR
    634: 'country/QAT',  # Qatar, QA
    638: 'country/REU',  # Réunion, RE
    639: 'country/REU',  # Réunion, RE (additional)
    642: 'country/ROU',  # Romania, RO
    643: 'country/RUS',  # Russian Federation, RU
    643: 'country/RUS',  # Russia, RU
    646: 'country/RWA',  # Rwanda, RW
    654: 'country/SHN',  # Saint Helena, Ascension and Tristan da Cunha, SH
    659: 'country/KNA',  # Saint Kitts and Nevis, KN
    662: 'country/LCA',  # Saint Lucia, LC
    666: 'country/SPM',  # Saint Pierre and Miquelon, PM
    670: 'country/VCT',  # Saint Vincent and the Grenadines, VC
    670: 'country/VCT',  # Saint Vincent & the Grenadines, VC
    670: 'country/VCT',  # St. Vincent and the Grenadines, VC
    882: 'country/WSM',  # Samoa, WS
    674: 'country/SMR',  # San Marino, SM
    678: 'country/STP',  # Sao Tome and Principe, ST
    682: 'country/SAU',  # Saudi Arabia, SA
    686: 'country/SEN',  # Senegal, SN
    688: 'country/SRB',  # Serbia, RS
    891: 'country/SCG',  # Serbia and Montenegro (former), RS (additional)
    690: 'country/SYC',  # Seychelles, SC
    694: 'country/SLE',  # Sierra Leone, SL
    702: 'country/SGP',  # Singapore, SG
    703: 'country/SVK',  # Slovakia, SK
    705: 'country/SVN',  # Slovenia, SI
    90: 'country/SLB',  # Solomon Islands, SB
    706: 'country/SOM',  # Somalia, SO
    710: 'country/ZAF',  # South Africa, ZA
    239: 'country/SGS',  # South Georgia and the South Sandwich Islands, GS
    728: 'country/SSD',  # South Sudan, SS
    724: 'country/ESP',  # Spain, ES
    144: 'country/LKA',  # Sri Lanka, LK
    534: 'country/SXM',  # Sint Maarten (Dutch part), SX
    729: 'country/SDN',  # Sudan, SD
    736: 'country/SDN',  # Sudan, SD
    740: 'country/SUR',  # Suriname, SR
    744: 'country/SJM',  # Svalbard and Jan Mayen, SJ
    748: 'country/SWZ',  # Swaziland, SZ
    752: 'country/SWE',  # Sweden, SE
    756: 'country/CHE',  # Switzerland, CH
    757: 'country/CHE',  # Switzerland, CH (additional)
    760: 'country/SYR',  # Syrian Arab Republic, SY
    158: 'country/TWN',  # Taiwan, Province of China, TW
    158: 'country/TWN',  # Taiwan, TW
    762: 'country/TJK',  # Tajikistan, TJ
    834: 'country/TZA',  # Tanzania, United Republic of, TZ
    764: 'country/THA',  # Thailand, TH
    626: 'country/TLS',  # Timor-Leste, TL
    768: 'country/TGO',  # Togo, TG
    772: 'country/TKL',  # Tokelau, TK
    776: 'country/TON',  # Tonga, TO
    780: 'country/TTO',  # Trinidad and Tobago, TT
    788: 'country/TUN',  # Tunisia, TN
    792: 'country/TUR',  # Turkey, TR
    795: 'country/TKM',  # Turkmenistan, TM
    796: 'country/TCA',  # Turks and Caicos Islands, TC
    798: 'country/TUV',  # Tuvalu, TV
    800: 'country/UGA',  # Uganda, UG
    804: 'country/UKR',  # Ukraine, UA
    784: 'country/ARE',  # United Arab Emirates, AE
    826: 'country/GBR',  # United Kingdom, GB
    840: 'country/USA',  # United States, US
    581: 'country/UMI',  # United States Minor Outlying Islands, UM
    858: 'country/URY',  # Uruguay, UY
    810: 'country/SUN',  # USSR (former), SU (additional)
    860: 'country/UZB',  # Uzbekistan, UZ
    548: 'country/VUT',  # Vanuatu, VU
    862: 'country/VEN',  # Venezuela, Bolivarian Republic of, VE
    862: 'country/VEN',  # Venezuela, VE
    704: 'country/VNM',  # Viet Nam, VN
    704: 'country/VNM',  # Vietnam, VN
    92: 'country/VGB',  # Virgin Islands, British, VG
    850: 'country/VIR',  # Virgin Islands, U.S., VI
    876: 'country/WLF',  # Wallis and Futuna, WF
    732: 'country/ESH',  # Western Sahara, EH
    887: 'country/YEM',  # Yemen, YE
    886: 'country/YEM',  # Yemen Arab Rep. (former), YE (additional)
    720: 'country/YEM',  # Yemen Dem. (former), YE (additional)
    887: 'country/YEM',  # Yemen, YE
    890: 'country/YUG',  # Yugoslavia (former), YU (additional)
    894: 'country/ZMB',  # Zambia, ZM
    716: 'country/ZWE',  # Zimbabwe, ZW
}


def get_all_country_codes() -> List[str]:
    return list(UN_COUNTRY_CODES.keys())


def get_country_dcid(country_code: str) -> str:
    numeric_code = int(country_code, 10)
    if numeric_code in UN_COUNTRY_CODES:
        return UN_COUNTRY_CODES[numeric_code]
    return None
