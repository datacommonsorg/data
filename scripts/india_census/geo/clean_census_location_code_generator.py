import os
import csv
import pandas as pd

census_location_id_pattern = "COI{year}-{state}-{district}-{subdistt}-{town_or_village}-{ward}-{eb}"


class LoadCensusGeoData:

    def __init__(self, census_data_dir, census_data_file, census_year):
        self.census_data_file = census_data_file
        self.census_year = census_year
        self.census_data_dir = census_data_dir
        self.cleaned_geos_file_name_pattern = "india_census_{year}_geo_cleaned.csv"
        self.raw_df = None

    def _download(self):
        path = os.path.join(self.census_data_dir, self.census_data_file)
        print(path)
        self.raw_df = pd.read_excel(path, dtype=str)

    def generate_location_csv(self):
        self._download()
        #keep the first seven columns and drop rest
        #State,District,Subdistt,Town/Village,Ward,EB,Level,Name
        columns_to_drop = list(self.raw_df.columns[8:])
        self.raw_df.drop(columns_to_drop, axis=1, inplace=True)
        self.raw_df["census_location_id"] = self.raw_df.apply(
            lambda row: census_location_id_pattern.format(
                year=self.census_year,
                state=row["State"],
                district=row["District"],
                subdistt=row["Subdistt"],
                town_or_village=row["Town/Village"],
                ward=row["Ward"],
                eb=row["EB"]),
            axis=1)
        self.raw_df = self.raw_df.drop_duplicates()
        output_file_path = os.path.join(
            self.census_data_dir,
            self.cleaned_geos_file_name_pattern.format(year=self.census_year))
        print(output_file_path)
        self.raw_df.to_csv(output_file_path,
                           index=False,
                           header=True)


if __name__ == '__main__':
    census_data_dir = os.path.join(os.path.dirname(__file__),"data")
    census_data_file = 'DDW_PCA0000_2011_Indiastatedist.xlsx'

    loader = LoadCensusGeoData(census_data_dir, census_data_file, 2011)
    loader.generate_location_csv()
