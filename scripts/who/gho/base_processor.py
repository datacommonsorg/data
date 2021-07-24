import abc
import os
import csv
import copy
import numpy as np
import pandas as pd
from typing import List, Dict
import urllib.request


TEMPLATE_STAT_VAR = """Node: {name}
description: "{description}"
typeOf: dcs:StatisticalVariable
populationType: {populationType}
statType: {statType}
measuredProperty: {measuredProperty}
"""

TEMPLATE_TMCF = """Node: E:WHO_GHO_{indicator_category_name}->E0
typeOf: dcs:StatVarObservation
variableMeasured: C:WHO_GHO_{indicator_category_name}->StatisticalVariable
observationDate: C:WHO_GHO_{indicator_category_name}->Date
observationAbout: E:WHO_GHO_{indicator_category_name}->E1
value: C:WHO_GHO_{indicator_category_name}->Value

Node: E:WHO_GHO_{indicator_category_name}->E1
typeOf: schema:Country
dcid: C:WHO_GHO_{indicator_category_name}->Location_Code
"""


class GHOIndicatorProcessorBase(abc.ABC):
    """The base processor class for GHO indicators data.
    
    Attributes:
        indicator_category (str):  The category of indicators to process.
            This will be used in the output file names.
        indicators_metadata_csv (str): The csv file with indicator metadata.
        data_base_path (str): Url or full filepath for the data.
        output_filepath (str): Relative path of the output directory.
        output_mcf_filename (str): MCF file name.
        output_tmcf_filename (str): TMCF file name.
        output_processed_data_filename (str): Cleaned data file (csv) name.
        existing_stat_vars (list): List of existing Statistical Variables for
            which we don't need to generate an MCF.

        stat_var_template (str): Template for the StatisticalVariables. 
            The default for this in provided as a global variable.
        tmcf_template (str): Template for the tmcf file. 
            The default for this in provided as a global variable.

        processed_data (pd.DataFrame): Processed data.   
    """

    def __init__(self, indicator_category: str, indicators_metadata_csv: str, data_base_path: str, output_filepath: str, output_mcf_filename: str, output_tmcf_filename: str, output_processed_data_filename: str,
        existing_stat_vars: List = []):
        """
        Constructor
        
        Args:
            indicator_category (str):  The category of indicators to process.
                This will be used in the output file names.
            indicators_metadata_csv (str): The csv file with indicator metadata.
            data_base_path (str): Url or full filepath for the data.
            output_filepath (str): Relative path of the output directory.
            output_mcf_filename (str): MCF file name.
            output_tmcf_filename (str): TMCF file name.
            output_processed_data_filename (str): Cleaned data file (csv) name.
            existing_stat_vars (List[str]): List of existing Statistical 
                Variables (str) for which we don't need to generate an MCF. Default
                is an empty list.
        """
        self.indicator_category = indicator_category
        self.indicators_metadata_csv = indicators_metadata_csv
        self.data_base_path = data_base_path
        self.output_filepath = output_filepath
        self.output_mcf_filename = output_mcf_filename
        self.output_tmcf_filename = output_tmcf_filename
        self.output_processed_data_filename = output_processed_data_filename
        self.existing_stat_vars = existing_stat_vars

        self.stat_var_template = TEMPLATE_STAT_VAR
        self.tmcf_template = TEMPLATE_TMCF

        self.processed_data = None

        self._validate_inputs()

    def process_all(self):
        """Runs the entire processing pipeline.
        """

        # Retrieve the metadta and the processed data.
        self.metadata_df = self._get_indicator_metadata()
        self.processed_data = self._retrieve_and_process_data()
        
        # Validate that the metadata was processed sucessfully.
        assert(self.metadata_df is not None)
        assert(len(self.metadata_df) > 0)

        # Validate that the data was retrieved/processed sucessfully.
        assert(self.processed_data is not None)
        assert(len(self.processed_data) > 0)

        # Write data to file.
        self._write_processed_data_to_file()

        # Write the tmcf and mcf files.
        self._create_tmcf()
        self._create_mcf()

    def _validate_inputs(self):
        assert(self.indicator_category is not None and 
            type(self.indicator_category) == type('str'))

        assert(self.indicators_metadata_csv is not None and 
            type(self.indicators_metadata_csv) == type('str'))

        assert(self.data_base_path is not None and 
            type(self.data_base_path) == type('str'))

        assert(self.output_filepath is not None and 
            type(self.output_filepath) == type('str'))

        assert(self.output_tmcf_filename is not None and 
            type(self.output_tmcf_filename) == type('str'))

        assert(self.output_processed_data_filename is not None and 
            type(self.output_processed_data_filename) == type('str'))

        assert(self.existing_stat_vars is not None and 
            type(self.existing_stat_vars) == type(['0', '1', '2']))

    def _get_indicator_metadata(self):
        try:
            metadata_df = pd.read_csv(self.indicators_metadata_csv)
        except Exception as e:
            exception_msg = "Could not read the indicators metadata from: %s." %self.indicators_metadata_csv
            exception_msg += "\nAssigning None and continuing." 
            print(exception_msg)
            metadata_df = None
        return metadata_df

    @abc.abstractmethod
    def _retrieve_and_process_data(self) -> pd.DataFrame:
        """Retrieves the raw data and processes it.

        This function must be implemented by the sub-classes.
        
        Returns:
            A pd.DataFrame object with the processed data.   
        """
        pass

    @abc.abstractmethod
    def _create_stats_vars(self)-> Dict:
        """Creates all the Statistical Variables.

        This function must be implemented by the sub-classes.
        
        Returns:
            A Dict object where the keys are variable name and the values 
            are the formatted Stats Variable string.
        """
        pass

    def _write_processed_data_to_file(self):
        assert(self.processed_data is not None)
        self.processed_data.to_csv(
            path_or_buf=self.output_filepath + self.output_processed_data_filename, 
            index=False)

    def _create_tmcf(self):
        with open(self.output_filepath + self.output_tmcf_filename, 
            'w+') as f_out:
            f_out.write(
               self.tmcf_template.format(
                   indicator_category_name=self.indicator_category))


    def _create_mcf(self):
        assert(self.metadata_df is not None)
        stats_vars_dict = self._create_stats_vars()

        with open(self.output_filepath + self.output_mcf_filename, 
            'w+') as f_out:
            for name in stats_vars_dict.keys():
                if name in self.existing_stat_vars:
                    pass
                else:
                    f_out.write(stats_vars_dict[name])
