"""Process data from Census ACS5Year Subject Table S2303."""
import os
import sys
import pandas as pd
import numpy as np

# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring

#pylint: disable=wrong-import-position
#pylint: disable=import-error
_CODEDIR = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(1, os.path.join(_CODEDIR, '..', 'common'))

from data_loader import SubjectTableDataLoaderBase  # commit hash - 4bc5102
from resolve_geo_id import convert_to_place_dcid
#pylint: enable=wrong-import-position
#pylint: enable=import-error


class S2303SubjectTableDataLoader(SubjectTableDataLoaderBase):
    """
    A child class for the S2303 import.
    """

    def _convert_percent_to_numbers(self, df):
        df_cols = df.columns.tolist()
        for count_col, percent_cols in self.json_spec['denominators'].items():
            if count_col in df_cols:
                for col in percent_cols:
                    if col in df_cols:
                        df[col] = df[col].astype(float)
                        df[count_col] = df[count_col].astype(float)
                        df[col] = (df[col] / 100) * df[count_col]
                        df[col] = df[col].round(3)
        return df

    def _process_dataframe(self, df, filename):
        """processes a dataframe read from a csv file"""
        df = self._replace_ignore_values_with_nan(df)
        year = filename.split(f'ACSST{self.estimate_period}Y')[1][:4]
        print(f"Processing: {filename}", end=" |  ", flush=True)

        df = df[~((df['id'].str.startswith('950')) |
                  (df['id'].str.startswith('960')) |
                  (df['id'].str.startswith('970')))]

        # Only calculating percentages for selected years
        percent_years = ['2014', '2013', '2012', '2011', '2010']
        if self.has_percent and year in percent_years:
            print("Converting percent to numbers", end=" |  ", flush=True)
            df = self._convert_percent_to_numbers(df)

        # if column map is not available generate, will rarely be False
        column_map = self.column_map[year]

        # add stats to dict_counter for current year
        self.counter_dict[year] = {
            "filename":
                filename,
            "number of columns in dataset":
                df.shape[1],
            "number of rows in dataset":
                df.shape[0],
            "number of statVars generated for columns":
                len(list(column_map.keys())),
            "number of observations":
                0,
            "number of unique StatVars with observations":
                0,
        }

        csv_file = open(self.clean_csv_path, 'a')
        place_geo_ids = df['id'].apply(convert_to_place_dcid)

        # update the clean csv
        for column in df.columns.tolist():
            if column in column_map:
                obs_df = pd.DataFrame(columns=self.csv_columns)
                obs_df['Place'] = place_geo_ids
                obs_df['StatVar'] = column_map[column]['Node']
                obs_df['Quantity'] = df[column].values.tolist()
                # add unit to the csv
                try:
                    unit = column_map[column]['unit']
                    del column_map[column]['unit']
                except KeyError:
                    unit = np.nan
                obs_df['Unit'] = unit

                # add scaling factor to the csv
                try:
                    scaling_factor = column_map[column]['scalingFactor']
                    del column_map[column]['scalingFactor']
                except KeyError:
                    unit = np.nan
                    scaling_factor = np.nan

                # if StatVar not in mcf_dict, add dcid
                dcid = column_map[column]['Node']

                if dcid not in self.mcf_dict:
                    ## key --> node dcid
                    self.mcf_dict[dcid] = {}
                    ## add pvs to dict
                    for key, value in column_map[column].items():
                        if key != 'Node':
                            self.mcf_dict[dcid][key] = value

                obs_df['ScalingFactor'] = scaling_factor
                obs_df['Year'] = year
                obs_df['Column'] = column

                # Replace empty places (unresolved geoIds) as null values
                obs_df['Place'].replace('', np.nan, inplace=True)

                # Drop rows with observations for empty (null) values
                obs_df.dropna(subset=['Place', 'Quantity'],
                              axis=0,
                              inplace=True)

                # Write the processed observations to the clean_csv
                if self.year_count == 0:
                    obs_df.to_csv(csv_file, header=True, index=False, mode='w')
                else:
                    obs_df.to_csv(csv_file, header=False, index=False, mode='a')
                self.year_count += 1

                # update stats for the year:
                self.counter_dict[year]["number of unique geos"] = len(
                    obs_df['Place'].unique())
                self.counter_dict[year][
                    "number of observations"] += obs_df.shape[0]
                self.counter_dict[year][
                    "number of unique StatVars with observations"] += len(
                        obs_df['StatVar'].unique())
                self.counter_dict[year]["number of StatVars in mcf_dict"] = len(
                    list(self.mcf_dict.keys()))
        csv_file.close()
        n_obs = self.counter_dict[year]['number of observations']
        n_sv = self.counter_dict[year][
            'number of unique StatVars with observations']
        n_geos = self.counter_dict[year]['number of unique geos']
        print(
            f" Completed with {n_obs} observation for {n_sv} StatVars at "
            f"{n_geos} places. ",
            flush=True)
