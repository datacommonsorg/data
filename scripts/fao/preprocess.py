# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""A script that takes in the .csv file and cleans the data, outputting a
new .csv file named "cleaned_output.csv" in an "output/" folder.
"""
import csv
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

BASELINE_CSV_FILENAME = os.path.join(SCRIPT_DIR, 'CurrencyFAO.csv')
DOWNLOADED_CSV_FILENAME = os.path.join(
    SCRIPT_DIR, 'input_data', 'Exchange_rate_E_All_Data_(Normalized).csv')
OUTPUT_DIR = os.path.join(SCRIPT_DIR, 'output')
OUTPUT_CSV_FILENAME = os.path.join(OUTPUT_DIR, 'cleaned_output.csv')

# Variable for representing 'Year' in dataset.
YEAR_CODE = '7021'

# Define order of headers for output via DictWriter.
HEADERS_OUT = [
    'Country', 'Currency', 'YearMonth', 'ObservationPeriod',
    'ExchangeRatePerUSD', 'ExchangeRatePerUSD_Standardized', '# Comments'
]

# UN M49 numeric code to Data Commons country DCID mapping.
M49_TO_COUNTRY = {
    '004': 'country/AFG',
    '008': 'country/ALB',
    '012': 'country/DZA',
    '020': 'country/AND',
    '024': 'country/AGO',
    '028': 'country/ATG',
    '031': 'country/AZE',
    '032': 'country/ARG',
    '036': 'country/AUS',
    '040': 'country/AUT',
    '044': 'country/BHS',
    '048': 'country/BHR',
    '050': 'country/BGD',
    '051': 'country/ARM',
    '052': 'country/BRB',
    '056': 'country/BEL',
    '060': 'country/BMU',
    '064': 'country/BTN',
    '068': 'country/BOL',
    '070': 'country/BIH',
    '072': 'country/BWA',
    '076': 'country/BRA',
    '084': 'country/BLZ',
    '090': 'country/SLB',
    '092': 'country/VGB',
    '096': 'country/BRN',
    '100': 'country/BGR',
    '104': 'country/MMR',
    '108': 'country/BDI',
    '112': 'country/BLR',
    '116': 'country/KHM',
    '120': 'country/CMR',
    '124': 'country/CAN',
    '132': 'country/CPV',
    '136': 'country/CYM',
    '140': 'country/CAF',
    '144': 'country/LKA',
    '148': 'country/TCD',
    '152': 'country/CHL',
    '156': 'country/CHN',
    '158': 'country/TWN',
    '170': 'country/COL',
    '174': 'country/COM',
    '175': 'country/MYT',
    '178': 'country/COG',
    '180': 'country/COD',
    '184': 'country/COK',
    '188': 'country/CRI',
    '191': 'country/HRV',
    '192': 'country/CUB',
    '196': 'country/CYP',
    '200': 'country/CSK',
    '203': 'country/CZE',
    '204': 'country/BEN',
    '208': 'country/DNK',
    '212': 'country/DMA',
    '214': 'country/DOM',
    '218': 'country/ECU',
    '222': 'country/SLV',
    '226': 'country/GNQ',
    '230': 'country/ETH',
    '231': 'country/ETH',
    '232': 'country/ERI',
    '233': 'country/EST',
    '234': 'country/FRO',
    '242': 'country/FJI',
    '246': 'country/FIN',
    '248': 'country/ALA',
    '250': 'country/FRA',
    '254': 'country/GUF',
    '258': 'country/PYF',
    '260': 'country/ATF',
    '262': 'country/DJI',
    '266': 'country/GAB',
    '268': 'country/GEO',
    '270': 'country/GMB',
    '275': 'country/PSE',
    '276': 'country/DEU',
    '288': 'country/GHA',
    '292': 'country/GIB',
    '296': 'country/KIR',
    '300': 'country/GRC',
    '304': 'country/GRL',
    '308': 'country/GRD',
    '312': 'country/GLP',
    '320': 'country/GTM',
    '324': 'country/GIN',
    '328': 'country/GUY',
    '332': 'country/HTI',
    '336': 'country/VAT',
    '340': 'country/HND',
    '344': 'country/HKG',
    '348': 'country/HUN',
    '352': 'country/ISL',
    '356': 'country/IND',
    '360': 'country/IDN',
    '364': 'country/IRN',
    '368': 'country/IRQ',
    '372': 'country/IRL',
    '376': 'country/ISR',
    '380': 'country/ITA',
    '384': 'country/CIV',
    '388': 'country/JAM',
    '392': 'country/JPN',
    '398': 'country/KAZ',
    '400': 'country/JOR',
    '404': 'country/KEN',
    '408': 'country/PRK',
    '410': 'country/KOR',
    '414': 'country/KWT',
    '417': 'country/KGZ',
    '418': 'country/LAO',
    '422': 'country/LBN',
    '426': 'country/LSO',
    '428': 'country/LVA',
    '430': 'country/LBR',
    '434': 'country/LBY',
    '438': 'country/LIE',
    '440': 'country/LTU',
    '442': 'country/LUX',
    '446': 'country/MAC',
    '450': 'country/MDG',
    '454': 'country/MWI',
    '458': 'country/MYS',
    '462': 'country/MDV',
    '466': 'country/MLI',
    '470': 'country/MLT',
    '474': 'country/MTQ',
    '478': 'country/MRT',
    '480': 'country/MUS',
    '484': 'country/MEX',
    '492': 'country/MCO',
    '496': 'country/MNG',
    '498': 'country/MDA',
    '499': 'country/MNE',
    '500': 'country/MSR',
    '504': 'country/MAR',
    '508': 'country/MOZ',
    '512': 'country/OMN',
    '516': 'country/NAM',
    '520': 'country/NRU',
    '524': 'country/NPL',
    '528': 'country/NLD',
    '530': 'country/NLD',
    '531': 'country/CUW',
    '533': 'country/ABW',
    '534': 'country/SXM',
    '540': 'country/NCL',
    '548': 'country/VUT',
    '554': 'country/NZL',
    '558': 'country/NIC',
    '562': 'country/NER',
    '566': 'country/NGA',
    '578': 'country/NOR',
    '583': 'country/FSM',
    '584': 'country/MHL',
    '585': 'country/PLW',
    '586': 'country/PAK',
    '591': 'country/PAN',
    '598': 'country/PNG',
    '600': 'country/PRY',
    '604': 'country/PER',
    '608': 'country/PHL',
    '616': 'country/POL',
    '620': 'country/PRT',
    '624': 'country/GNB',
    '626': 'country/TLS',
    '630': 'country/PRI',
    '634': 'country/QAT',
    '638': 'country/REU',
    '642': 'country/ROU',
    '643': 'country/RUS',
    '646': 'country/RWA',
    '659': 'country/KNA',
    '660': 'country/AIA',
    '662': 'country/LCA',
    '663': 'country/MAF',
    '666': 'country/SPM',
    '670': 'country/VCT',
    '674': 'country/SMR',
    '678': 'country/STP',
    '682': 'country/SAU',
    '686': 'country/SEN',
    '688': 'country/SRB',
    '690': 'country/SYC',
    '694': 'country/SLE',
    '702': 'country/SGP',
    '703': 'country/SVK',
    '704': 'country/VNM',
    '705': 'country/SVN',
    '706': 'country/SOM',
    '710': 'country/ZAF',
    '716': 'country/ZWE',
    '720': 'country/YEM',
    '724': 'country/ESP',
    '728': 'country/SSD',
    '729': 'country/SDN',
    '736': 'country/SDN',
    '740': 'country/SUR',
    '748': 'country/SWZ',
    '752': 'country/SWE',
    '756': 'country/CHE',
    '760': 'country/SYR',
    '762': 'country/TJK',
    '764': 'country/THA',
    '768': 'country/TGO',
    '776': 'country/TON',
    '780': 'country/TTO',
    '784': 'country/ARE',
    '788': 'country/TUN',
    '792': 'country/TUR',
    '795': 'country/TKM',
    '796': 'country/TCA',
    '798': 'country/TUV',
    '800': 'country/UGA',
    '804': 'country/UKR',
    '807': 'country/MKD',
    '810': 'country/SUN',
    '818': 'country/EGY',
    '826': 'country/GBR',
    '831': 'country/GGY',
    '832': 'country/JEY',
    '833': 'country/IMN',
    '834': 'country/TZA',
    '840': 'country/USA',
    '854': 'country/BFA',
    '858': 'country/URY',
    '860': 'country/UZB',
    '862': 'country/VEN',
    '882': 'country/WSM',
    '886': 'country/YEM',
    '887': 'country/YEM',
    '890': 'country/YUG',
    '894': 'country/ZMB',
}


def resolve_country(m49_raw: str) -> str:
    """Resolves a raw M49 code (e.g. \"'004\") to a Data Commons country DCID."""
    m49 = m49_raw.strip().replace("'", "").zfill(3)
    if m49 in M49_TO_COUNTRY:
        return M49_TO_COUNTRY[m49]
    try:
        import pycountry
        decoded = pycountry.countries.get(numeric=m49)
        if decoded:
            return f"country/{decoded.alpha_3}"
    except ImportError:
        pass
    raise ValueError(f"Unresolved M49 country code: {m49_raw}")


def preprocess(input_files, output_csv_filename=OUTPUT_CSV_FILENAME):
    """Reads one or more FAOSTAT Normalized CSV files, merges them additively,
    and writes cleaned_output.csv.
    """
    os.makedirs(os.path.dirname(output_csv_filename), exist_ok=True)
    rows_by_key = {}
    for file_path in input_files:
        if not os.path.exists(file_path):
            continue
        with open(file_path, 'r', encoding='ISO-8859-1') as csv_in:
            reader = csv.DictReader(csv_in, delimiter=',')
            for row_dict in reader:
                m49 = row_dict['Area Code (M49)'].strip().replace("'",
                                                                  "").zfill(3)
                key = (m49, row_dict['Element Code'].strip(),
                       row_dict['ISO Currency Code'].strip(),
                       row_dict['Year'].strip(),
                       row_dict['Months Code'].strip())
                rows_by_key[key] = (row_dict, reader.line_num)

    with open(output_csv_filename, 'w', encoding='utf-8',
              newline='') as csv_out:
        writer = csv.DictWriter(csv_out, fieldnames=HEADERS_OUT)
        writer.writeheader()
        for (row_dict, line_num) in rows_by_key.values():
            processed_dict = {}
            processed_dict['Currency'] = row_dict['ISO Currency Code'].strip()

            if row_dict['Months Code'].strip() == YEAR_CODE:
                processed_dict['YearMonth'] = row_dict['Year'].strip()
                processed_dict['ObservationPeriod'] = 'P1Y'
            else:
                processed_dict['YearMonth'] = '%s-%s' % (
                    row_dict['Year'].strip(),
                    row_dict['Months Code'].strip().replace("70", ""))
                processed_dict['ObservationPeriod'] = 'P1M'

            processed_dict['Country'] = resolve_country(
                row_dict['Area Code (M49)'])

            if row_dict['Element Code'].strip() == 'LCU':
                processed_dict['ExchangeRatePerUSD'] = row_dict['Value'].strip()
            elif row_dict['Element Code'].strip() == 'SLC':
                processed_dict['ExchangeRatePerUSD_Standardized'] = row_dict[
                    'Value'].strip()

            processed_dict['# Comments'] = "#" + str(line_num) + " row original"
            writer.writerow(processed_dict)


def main():
    input_files = [BASELINE_CSV_FILENAME]
    if os.path.exists(DOWNLOADED_CSV_FILENAME):
        input_files.append(DOWNLOADED_CSV_FILENAME)
    preprocess(input_files, OUTPUT_CSV_FILENAME)


if __name__ == '__main__':
    main()
