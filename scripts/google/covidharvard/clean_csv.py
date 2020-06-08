import pandas as pd
import numpy as np
from datetime import datetime

class CovidHarvard:
    def __init__(self, confirmed_csv: str, deaths_csv: str, region: 'County' or 'State'):
        if region != 'State' and region != 'County':
            raise Exception("Invalid region!")

        print("Reading CSVs")
        confirmed = pd.read_csv(confirmed_csv)
        deaths = pd.read_csv(deaths_csv)

        print("Converting COUNTY column to fips")
        if region == 'County':
            confirmed = confirmed.rename(columns={'COUNTY': 'fips'})
            deaths = deaths.rename(columns={'COUNTY': 'fips'})

        print("Converting fips to DC dcid")
        confirmed = self.convert_fips_to_dcid(confirmed, region)
        deaths = self.convert_fips_to_dcid(deaths, region)

        print("Dropping unecessary columns")
        confirmed = self.drop_unecessary_columns(confirmed)
        deaths = self.drop_unecessary_columns(deaths)

        print("Combining DataFrames into one")
        combined = self.combine_dfs(confirmed=confirmed, deaths=deaths)

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

    def combine_dfs(self, confirmed, deaths):
        Date = []
        GeoId = []
        COVID19CumulativeCases = []
        COVID19CumulativeDeaths = []
        for dcid in confirmed.index:
            for date in confirmed:
                date_iso = date
                if '/' in date:
                    date_split = date.split('/')
                    date_iso = datetime(int(date_split[2]), int(date_split[0]), int(date_split[1])).isoformat()
                    date_iso = date_iso.split('T')[0]

                print(dcid, date_iso)

                if not date in confirmed or not dcid in confirmed[date]:
                    confirmed_val = np.nan
                else:
                    confirmed_val = confirmed[date][dcid]

                if not date in deaths or not dcid in deaths[date]:
                    deaths_val = np.nan
                else:
                    deaths_val = deaths[date][dcid]

                Date.append(date_iso)
                GeoId.append(dcid)
                COVID19CumulativeCases.append(confirmed_val)
                COVID19CumulativeDeaths.append(deaths_val)
        return pd.DataFrame({
                "Date": Date,
                "GeoId": GeoId,
                "COVID19CumulativeCases": COVID19CumulativeCases,
                "COVID19CumulativeDeaths": COVID19CumulativeDeaths
            })

CovidHarvard(confirmed_csv='./input/US_State_Confirmed.csv',
             deaths_csv='./input/US_State_Deaths.csv',
             region='State')