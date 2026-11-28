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
"""Base class for India WRIS Ground Water and Surface Water Quality imports."""

import json
import os
import re
import sys

from absl import logging
import pandas as pd

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
_SCRIPTS_DIR = os.path.dirname(_MODULE_DIR)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from india.geo.districts import IndiaDistrictsMapper

# Station name normalizations from the 2023 CNS production manual fixes.
_STATION_NAME_REPLACEMENTS = {
    ('Borewell Located At Rahiv Gruha Ka;Pa Ahmedguda Ambedkar Nagar'
     ' Kapra Medchal District.'):
        ('Borewell Located At Rahiv Gruha Ka Pa Ahmedguda Ambedkar Nagar'
         ' Kapra Medchal District.'),
    ('B/W Near Malkapur Lake Malkapur Village (Agricultural Field)'
     ' Choutuppa; Mandal'):
        ('B/W Near Malkapur Lake Malkapur Village (Agricultural Field)'
         ' Choutuppa  Mandal'),
    'Kodarma': 'Koderma',
}

# State name normalizations for LGD district code resolution.
_STATE_NAME_REPLACEMENTS = {
    'Daman & Diu': 'dadra and nagar haveli and daman and diu',
    'Jammu & Kashmir': 'jammu and kashmir',
}

# District name normalizations for LGD district code resolution.
_DISTRICT_NAME_REPLACEMENTS = {
    'Baramula': 'Baramulla',
    'Bijapur': 'vijayapura',
    'Darjiling': 'Darjeeling',
    'Hugli': 'hooghly',
    'Janjgir - Champa': 'janjgir-champa',
    'Kodarma': 'Koderma',
    'Kumuram Bheem': 'kumuram bheem asifabad',
    'Puruliya': 'Purulia',
    'Rajauri': 'Rajouri',
    'Shrawasti': 'Shravasti',
    'West Nimar': 'Khargone',
    'west nimar': 'Khargone',
}

# Explicit (State, District) to LGD code overrides matching production station DCIDs.
_DISTRICT_CODE_OVERRIDES = {
    ('Odisha', 'Nabarangapur'): '366',
    ('Telangana', 'Rangareddy'): '518',
    ('Telangana', 'Warangal Rural'): '36',
}


def _find_first_column(columns, candidates):
    """Returns the first column name from candidates present in columns."""
    for candidate in candidates:
        if candidate in columns:
            return candidate
    raise ValueError(
        f'None of the expected columns {candidates} found in {list(columns)}')


class WaterQualityBase:
    """Base class to preprocess data files and generate MCF/TMCF files.

    Args:
        dataset_name (str): Name of the dataset import.
        util_names (str): Name of the corresponding data csv and json file.
        template_strings (dict): Dictionary with mcf/tmcf node templates.
        input_csv_path (str, optional): Custom path to input CSV file.
        output_dir (str, optional): Custom directory to write outputs.
    """

    def __init__(
        self,
        dataset_name,
        util_names,
        template_strings,
        input_csv_path=None,
        output_dir=None,
    ):
        self.dataset_name = dataset_name
        self.util_names = util_names
        self.module_dir = _MODULE_DIR
        self.input_csv_path = input_csv_path or os.path.join(
            self.module_dir, 'data', f'{self.util_names}.csv')
        self.output_dir = output_dir or os.path.join(self.module_dir,
                                                     self.dataset_name)

        self.solute_mcf = template_strings['solute_mcf']
        if not self.solute_mcf:
            raise ValueError('solute_mcf template must not be empty')

        self.solute_tmcf = template_strings['solute_tmcf']
        if not self.solute_tmcf:
            raise ValueError('solute_tmcf template must not be empty')

        self.chemprop_mcf = template_strings['chemprop_mcf']
        if not self.chemprop_mcf:
            raise ValueError('chemprop_mcf template must not be empty')

        self.chemprop_tmcf = template_strings['chemprop_tmcf']
        if not self.chemprop_tmcf:
            raise ValueError('chemprop_tmcf template must not be empty')

        self.site_dcid = template_strings['site_dcid']
        self.unit_node = template_strings['unit_node']
        if not self.unit_node:
            raise ValueError('unit_node template must not be empty')

    def _drop_all_empty_rows(self, df):
        """Drops rows that only contain station metadata without observations."""
        if df.empty:
            return df
        metadata_cols = {
            'Station Name',
            'State Name',
            'District Name',
            'Basin Name',
            'Sub Basin Name',
            'Agency Name',
            'Latitude',
            'Longitude',
            'Date Collection',
            'StateName',
            'DistrictName',
            'Month',
            'Year',
            'StationName',
            'SurfaceWaterStationLatitude',
            'SurfaceWaterStationLongitude',
            'ObsMonth',
            'StationNameLong',
            'DistrictCode',
            'LGDCode',
            'dcid',
            'LatLong',
        }
        obs_cols = [c for c in df.columns if c not in metadata_cols]
        if obs_cols:
            return df.dropna(subset=obs_cols, how='all')
        max_na = df.notnull().sum(axis=1).min() + 2
        return df.dropna(thresh=max_na)

    def _normalize_names(self, df, state_col, district_col, station_col):
        """Applies canonical state, district, and station name normalizations."""
        df = df.copy()
        df[station_col] = df[station_col].replace(_STATION_NAME_REPLACEMENTS)
        df[state_col] = df[state_col].replace(_STATE_NAME_REPLACEMENTS)

        # Fix state reassignments for Telangana and Daman/Diu districts.
        telangana_mask = (df[state_col] == 'Andhra Pradesh') & (
            df[district_col].isin(['Khammam', 'Rangareddy']))
        df.loc[telangana_mask, state_col] = 'Telangana'

        daman_diu_mask = (df[state_col].isin(
            ['Gujarat', 'Gujrat'])) & (df[district_col].isin(['Daman', 'Diu']))
        df.loc[daman_diu_mask,
               state_col] = ('dadra and nagar haveli and daman and diu')

        # Scope Bijapur -> vijayapura to Karnataka (Chhattisgarh also has a Bijapur district).
        karnataka_bijapur_mask = (df[state_col] == 'Karnataka') & (
            df[district_col] == 'Bijapur')
        df.loc[karnataka_bijapur_mask, district_col] = 'vijayapura'

        df[district_col] = df[district_col].replace({
            k: v
            for k, v in _DISTRICT_NAME_REPLACEMENTS.items()
            if k != 'Bijapur'
        })
        return df

    def _map_district_to_lgdcodes(self, mapper, state, district):
        if (state, district) in _DISTRICT_CODE_OVERRIDES:
            return _DISTRICT_CODE_OVERRIDES[(state, district)]
        try:
            return mapper.get_district_name_to_lgd_code_mapping(state, district)
        except Exception as e:
            logging.warning(
                'Failed to map state=%r, district=%r to LGD code: %s',
                state,
                district,
                e,
            )
            return district

    def create_dcids_in_csv(self):
        """Maps district names to LGD codes and generates station DCIDs in CSV."""
        if not os.path.exists(self.input_csv_path):
            raise FileNotFoundError(
                f'Input CSV file not found: {self.input_csv_path}')

        logging.info(
            'Reading %s input data from %s',
            self.dataset_name,
            self.input_csv_path,
        )
        self.df = pd.read_csv(self.input_csv_path, low_memory=False)

        state_col = _find_first_column(self.df.columns,
                                       ['State Name', 'StateName'])
        district_col = _find_first_column(self.df.columns,
                                          ['District Name', 'DistrictName'])
        station_col = _find_first_column(self.df.columns,
                                         ['Station Name', 'StationName'])
        date_col = _find_first_column(self.df.columns,
                                      ['Date Collection', 'Month', 'Year'])

        # Drop pre-existing derived columns if re-processing a staged CNS CSV.
        for derived_col in ['DistrictCode', 'LGDCode', 'dcid', 'LatLong']:
            if derived_col in self.df.columns:
                self.df = self.df.drop(columns=[derived_col])

        self.df = self._drop_all_empty_rows(self.df)
        self.df = self._normalize_names(self.df, state_col, district_col,
                                        station_col)

        # Deduplicate station observations for the same station/place/date.
        self.df = self.df.drop_duplicates(
            subset=[station_col, state_col, district_col, date_col],
            keep='last',
        ).reset_index(drop=True)

        # Map district names to LGD codes.
        mapper = IndiaDistrictsMapper()
        df_map = (self.df[[state_col, district_col]].drop_duplicates().dropna())
        df_map['DistrictCode'] = df_map.apply(
            lambda x: self._map_district_to_lgdcodes(mapper, x[state_col], x[
                district_col]),
            axis=1,
        )

        # Intentionally merge LGD codes keyed by district_col (matching legacy
        # CNS 20231005 and IndiaWaterQualityStations 20231226 station DCIDs, e.g.
        # indiaWris/189_*, indiaWris/174_*, indiaWris/149_*) so existing KG
        # WaterQualitySite station references remain 100% preserved.
        df_map_dedup = df_map.drop(columns=[state_col]).drop_duplicates(
            subset=[district_col], keep='last')
        self.df = self.df.merge(df_map_dedup, on=district_col, how='left')

        self.df['dcid'] = self.df.apply(
            lambda x: ''.join([
                'indiaWris/',
                str(x['DistrictCode']),
                '_',
                ''.join(re.split(r'\W+', str(x[station_col]))),
            ]),
            axis=1,
        )

        # Format DistrictCode as unpadded integer string when numeric.
        self.df['DistrictCode'] = self.df['DistrictCode'].apply(
            lambda c: str(int(c)) if str(c).isdigit() else str(c))

        latitude_col = [col for col in self.df.columns if 'Latitude' in col]
        longitude_col = [col for col in self.df.columns if 'Longitude' in col]
        if not latitude_col or not longitude_col:
            raise ValueError(
                f'Missing Latitude/Longitude columns in {self.input_csv_path}')
        self.df['LatLong'] = self.df.apply(
            lambda x: '[LatLong {} {}]'.format(x[latitude_col[0]], x[
                longitude_col[0]]),
            axis=1,
        )

        os.makedirs(self.output_dir, exist_ok=True)
        csv_save_path = os.path.join(self.output_dir,
                                     f'{self.dataset_name}.csv')
        tmp_csv_path = f'{csv_save_path}.tmp'
        self.df.to_csv(tmp_csv_path, index=None)
        os.replace(tmp_csv_path, csv_save_path)
        logging.info('Wrote %d processed rows to %s', len(self.df),
                     csv_save_path)

    def create_mcfs(self):
        """Creates MCF and TMCF files from the JSON configuration and templates."""
        json_file_path = os.path.join(self.module_dir, 'util',
                                      f'{self.util_names}.json')
        os.makedirs(self.output_dir, exist_ok=True)
        tmcf_file = os.path.join(self.output_dir, f'{self.dataset_name}.tmcf')
        mcf_file = os.path.join(self.output_dir, f'{self.dataset_name}.mcf')

        with open(json_file_path, 'r', encoding='utf-8') as j:
            properties = json.loads(j.read())

        pollutants, chem_props = properties
        idx = 2  # StatVarObs start from E2; E0 and E1 are location nodes.

        tmp_mcf = f'{mcf_file}.tmp'
        tmp_tmcf = f'{tmcf_file}.tmp'
        with (
                open(tmp_mcf, 'w', encoding='utf-8') as mcf,
                open(tmp_tmcf, 'w', encoding='utf-8') as tmcf,
        ):
            if self.site_dcid:
                tmcf.write(
                    self.site_dcid.format(dataset_name=self.dataset_name))

            for pollutant in pollutants['Pollutant']:
                name = pollutant['name']
                statvar = pollutant['statvar']
                unit = pollutant['unit']

                mcf.write(self.solute_mcf.format(variable=statvar))
                tmcf.write(
                    self.solute_tmcf.format(
                        dataset_name=self.dataset_name,
                        index=idx,
                        variable=statvar,
                        name=name,
                    ))
                if unit:
                    tmcf.write(self.unit_node.format(unit=unit))
                else:
                    tmcf.write('\n')
                idx += 1

            for chem_prop in chem_props['ChemicalProperty']:
                name = chem_prop['name']
                statvar = chem_prop['statvar']
                unit = chem_prop['unit']
                dcid = chem_prop['dcid']

                mcf.write(
                    self.chemprop_mcf.format(variable=statvar,
                                             dcid=dcid,
                                             statvar=statvar))
                tmcf.write(
                    self.chemprop_tmcf.format(
                        dataset_name=self.dataset_name,
                        index=idx,
                        unit=unit,
                        variable=statvar,
                        dcid=dcid,
                        name=name,
                    ))
                if unit:
                    tmcf.write(self.unit_node.format(unit=unit))
                else:
                    tmcf.write('\n')
                idx += 1

        os.replace(tmp_mcf, mcf_file)
        os.replace(tmp_tmcf, tmcf_file)
        logging.info('Generated %s and %s', mcf_file, tmcf_file)
