import os
import numpy as np
import pandas as pd
from typing import List, Dict
import urllib.request

from who.gho.base_processor import GHOIndicatorProcessorBase
from who.gho.immunization.aggregate_level import utils

WHO_GHO_DATA_API_URL = 'https://apps.who.int/gho/athena/data/GHO/{0}?filter=COUNTRY:*&x-sideaxis=COUNTRY&x-topaxis=GHO;YEAR&profile=verbose&format=csv'

RAW_DATA_COLUMNS_TO_TYPE = {'GHO (CODE)': str, 
                            'YEAR (DISPLAY)': int, 
                            'COUNTRY (CODE)': str, 
                            'Numeric': float}


class GHOIndicatorAggregateCountryDataProcessor(GHOIndicatorProcessorBase):

    def __init__(self):
        
        indicator_category = "immunization_country_aggregate" 
        indicators_metadata_csv = os.path.join(
            os.path.abspath(os.path.join(__file__ ,"../")), 
            'indicator_metadata.csv')

        data_base_path = WHO_GHO_DATA_API_URL
        
        output_filepath = os.path.join(os.path.dirname(__file__), 
            'output_files/')
        output_mcf_filename = indicator_category + ".mcf"
        output_tmcf_filename = indicator_category + ".tmcf"
        output_processed_data_filename = indicator_category + ".csv"
        existing_stat_vars = []
        
        super().__init__(
            indicator_category, 
            indicators_metadata_csv, 
            data_base_path, 
            output_filepath, 
            output_mcf_filename, 
            output_tmcf_filename, 
            output_processed_data_filename,
            existing_stat_vars)

    def _retrieve_and_process_data(self):     
        assert(self.metadata_df is not None)
        return utils.retrieve_and_process_data_helper(self.data_base_path, 
            self.metadata_df, RAW_DATA_COLUMNS_TO_TYPE)

    def _create_stats_vars(self) -> Dict:
        assert(self.metadata_df is not None)
        return utils.create_stats_vars_helper(self.metadata_df, 
            self.stat_var_template)
        

if __name__ == '__main__':
    a = GHOIndicatorAggregateCountryDataProcessor()
    a.process_all()