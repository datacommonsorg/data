import requests
import json
import pandas as pd

url =  "http://vocab.nic.in/rest.php/"

data_files = {
    'States': 'states/',
    'Country':  'country/',
    'Districts': 'district/tn/',
    'Pincode Details': 'pincode/110003/',
    'Taluks': 'taluk/tn/',
    'Language': 'lang/',
    'Taluks (District - wise)': 'taluk/tn/district/TN003/',
    'Audiences': 'audience/',
    'Sectors': 'sectors/',
    'Sub Sectors': 'sectors/subsectors/',
    'Site Count': 'sitecount/',
    'Sub Sectors (Sector-wise)': 'sectors/ST01/subsectors/'
}


class VocabularyDataLoader:
    def __init__(self, data_files, url):
        """
        Reads in the desired url paths to pull from. Initializes
        dictionary that will store the data frames after pulling.

        :param url: url where the data is stored.
        :param data_files: dictionary mapping each data type to be
        extrated to its relative path in the url.
        """
        self.paths = {
            key: url + data_files[key] + 'json' for key in data_files
        }
        self.data_frames = {}

    def pull_state_data(self):
        """
        Pulls data for states from the url specified at init.
        """
        path = self.paths['States']
        response = json.loads(requests.get(path).text)
        df = pd.DataFrame(
        [[state['state'][data_type] for data_type in state['state']] for state in response['states']],
        columns = [data_type for data_type in resp2onse['states'][0]['state']]
        )
        self.data_frames['States'] = df

    def save_data(self):
        """
        Saves all DataFrames stored in class instance.
        """
        for key in self.data_frames:
            self.data_frames[key].to_csv(key + '.csv')


l = VocabularyDataLoader(data_files, url)
l.pull_state_data()
l.save_data()
