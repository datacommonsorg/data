import pandas as pd
from preprocess_data import preprocess_df

class EurostatGDPImporter:
    DATA_LINK = "https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/BulkDownloadListing?file=data/nama_10r_3gdp.tsv.gz"
    def __init__(self):
        self.raw_df = None
        self.preprocessed_df = None
        self.clean_df = None

    def download_data(self):
        self.raw_df = pd.read_table(self.DATA_LINK)

    def preprocess_data(self):
        self.preprocessed_df = preprocess_df(self.raw_df)
        print(self.preprocessed_df)


if __name__ == "__main__":
    imp = EurostatGDPImporter()
    imp.download_data()
    imp.preprocess_data()
