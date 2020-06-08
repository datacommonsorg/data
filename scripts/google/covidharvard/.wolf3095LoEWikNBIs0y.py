import pandas as pd
import numpy as np

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
        dcid_format = "{:02}" if region == "County" else "{:06}"
        df['fips'] = df.fips.map(dcid_format.format)
        df['dcid'] = 'geoId/' + df['fips'].astype(str)
        return df

    def drop_unecessary_columns(self, df):
        df = df.drop(['fips', 'NAME', 'POP70', 'HHD70', 'POP80', 'HHD80', 'POP90', 'HHD90', 'POP00', 'HHD00', 'POP10', 'HHD10'], axis=1)
        df = df.set_index("dcid")
        return df

    def combine_dfs(self, confirmed, deaths):
        new_df = pd.DataFrame({})
        for dcid in confirmed.index:
            for date in confirmed:
                print(dcid, date)
                if date in confirmed:
                    continue
                if dcid in confirmed[date]:
                    continue

                try:
                    confirmed_val = confirmed[date][dcid]
                except:
                    confirmed_val = np.nan

                try:
                    deaths_val = deaths[date][dcid]
                except:
                    deaths_val = np.nan

                new_df = new_df.append(
                    {
                    "Date": date,
                    "GeoId": dcid,
                    "COVID19CumulativeCases": confirmed_val,
                    "COVID19CumulativeDeaths": deaths_val
                    }, ignore_index=True)
        return new_df

CovidHarvard('./input/US_State_Confirmed.csv', './input/US_State_Deaths.csv', region='State')