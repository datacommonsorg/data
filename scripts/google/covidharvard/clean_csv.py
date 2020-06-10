import pandas as pd
import numpy as np
from datetime import datetime

class CovidHarvard:
    def __init__(self, confirmed_cumulative_csv: str, deaths_cumulative_csv: str, region: 'County' or 'State'):
        if region != 'State' and region != 'County':
            raise Exception("Invalid region!")

        print("Reading CSVs")
        confirmed_cumulative_df = pd.read_csv(confirmed_cumulative_csv)
        deaths_cumulative_df = pd.read_csv(deaths_cumulative_csv)

        print("Converting COUNTY column to fips")
        if region == 'County':
            confirmed_cumulative_df = confirmed_cumulative_df.rename(columns={'COUNTY': 'fips'})
            deaths_cumulative_df = deaths_cumulative_df.rename(columns={'COUNTY': 'fips'})

        print("Converting fips to DC dcid")
        confirmed_cumulative_df = self.convert_fips_to_dcid(confirmed_cumulative_df, region)
        deaths_cumulative_df = self.convert_fips_to_dcid(deaths_cumulative_df, region)

        print("Dropping unecessary columns")
        confirmed_cumulative_df = self.drop_unecessary_columns(confirmed_cumulative_df)
        deaths_cumulative_df = self.drop_unecessary_columns(deaths_cumulative_df)

        print("Combining DataFrames into one")
        combined = self.combine_dfs(confirmed=confirmed_cumulative_df, deaths=deaths_cumulative_df)

        print("Exporting to ./output directory")
        combined.to_csv(f"./output/{region}_COVID_Harvard.csv", index=False)


    def convert_fips_to_dcid(self, df, region):
        dcid_format = "{:02}" if region == "State" else "{:05}"
        df['fips'] = df.fips.map(dcid_format.format)
        df['dcid'] = 'geoId/' + df['fips'].astype(str)
        return df

    def drop_unecessary_columns(self, df):
        df = df.drop(['fips', 'NAME', 'POP70', 'HHD70', 'POP80', 'HHD80', 'POP90', 'HHD90', 'POP00', 'HHD00', 'POP10', 'HHD10'], axis=1)
        df = df.set_index("dcid")
        return df

    @staticmethod
    def get_value(df, dcid, date):
        if not dcid:
            raise Exception("dcid cannot be None!")
        if not date:
            raise Exception("date cannot be None!")
        if df.empty:
            raise Exception("DataFrame is either empty or None!")
        if not date or not dcid:
            return np.nan
        if not date in df or not dcid in df[date]:
            return np.nan
        return df[date][dcid]

    def combine_dfs(self, confirmed, deaths):
        confirmed_incremental = confirmed.T.diff().T
        deaths_incremental = deaths.T.diff().T
        Date = []
        GeoId = []
        COVID19CumulativeCases, COVID19CumulativeDeaths = [], []
        COVID19IncrementalCases, COVID19IncrementalDeaths = [], []
        for dcid in confirmed.index:
            for date in confirmed:
                date_iso = date
                # Somtimes the data is in the form of XX/XX/XX, let's convert it to ISO
                if '/' in date:
                    date_split = date.split('/')
                    date_iso = datetime(int(date_split[2]), int(date_split[0]), int(date_split[1])).isoformat()
                    date_iso = date_iso.split('T')[0]

                print(dcid, date_iso)

                confirmed_cumulative_value = self.get_value(df=confirmed, dcid=dcid, date=date)
                deaths_cumulative_value = self.get_value(df=deaths, dcid=dcid, date=date)
                confirmed_incremental_value = self.get_value(df=confirmed_incremental, dcid=dcid, date=date)
                deaths_incremental_value = self.get_value(df=deaths_incremental, dcid=dcid, date=date)

                Date.append(date_iso)
                GeoId.append(dcid)
                COVID19CumulativeCases.append(confirmed_cumulative_value)
                COVID19CumulativeDeaths.append(deaths_cumulative_value)
                COVID19IncrementalCases.append(confirmed_incremental_value)
                COVID19IncrementalDeaths.append(deaths_incremental_value)

        return pd.DataFrame({
                "Date": Date,
                "GeoId": GeoId,
                "HarvardCOVID19CumulativeCases": COVID19CumulativeCases,
                "HarvardCOVID19CumulativeDeaths": COVID19CumulativeDeaths,
                "HarvardCOVID19IncrementalCases": COVID19IncrementalCases,
                "HarvardCOVID19IncrementalDeaths": COVID19IncrementalDeaths,
            })

CovidHarvard(confirmed_cumulative_csv='./input/US_County_Confirmed.csv',
             deaths_cumulative_csv='./input/US_County_Deaths.csv',
             region='County')
