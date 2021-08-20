"""Base class definition for processing ACS Subject Tables """

import os
import csv
import json
import pandas as pd
import requests
from io import BytesIO
from zipfile import ZipFile

_TEMPLATE_STAT_VAR = """Node: dcid:{name}
description: "{description}"
typeOf: dcs:StatisticalVariable
populationType: dcs:{populationType}
statType: dcs:{statType}
measuredProperty: dcs:{measuredProperty}
{constraints}
"""

_TEMPLATE_TMCF =  """Node: E:Subject_Table->E{index}
typeOf: dcs:StatVarObservation
variableMeasured: dcs:{stat_var}
measurementMethod: dcs:CensusACS{estimate_period}yrSurvey
observationDate: C:Subject_Table->observationDate
observationAbout: C:Subject_Table->observationAbout
value: C:Subject_Table->{stat_var}{unit}
"""

_UNIT_TEMPLATE = """
unit: dcs:{unit}"""

_IGNORED_VALUES = set(['**', '-', '***', '*****', 'N', '(X)', 'null'])

class SubjectTableDataLoaderBase:
	"""Subject Table Data Loader
	
	Attributes:
	config_json: Config file with mapping and constraints for statVars based on populationType
	zip_file_path: Path to the subject table zip file download from data.census.gov
  csv_file_path: Path where the cleaned csv file will be saved
  tmcf_file_path: Path where the generated tmcf file will be saved 
  mcf_file_path: Path where the generated MCF file will be saved
  download_id: Download token provided by data.census.gov, if the script needs to download the subject tables
  existing_statVar_file_path: Path to file with list of existing stat vars that we do no need to generate. File expected to contains 1 stat var dcid per line.
  
  Backward compatibility with S2201 import
  stat_var_path: Path to a file that contains list of stat vars, new stat var names that are not in this file will be script
  features_json
	"""
	def __init__(self, acs_estimate_period=5, config_json_path=None, csv_file_path=None, tmcf_file_path=None, mcf_file_path=None, statVar_file_path=None):
		"""Constructor
		
		Arguments
			config_json_path: Path to the config file with mapping and constraints for statVars based on populationType
			acs_estimate_period: numerical value to specify the period of the estimate, either 1 year or 5 years. (Default value is 5)
			zip_file_path: Path to the subject table zip file download from data.census.gov
			csv_file_path: Path where the cleaned csv file will be saved
			tmcf_file_path: Path where the generated tmcf file will be saved 
			mcf_file_path: Path where the generated MCF file will be saved
			statVar_file_path: Path to a file that contains list of stat vars, new stat var names that are not in this file will be script
		"""
		self.csv_file_path = csv_file_path
		self.tmcf_file_path = tmcf_file_path
		self.mcf_file_path = mcf_file_path
		self.acs_estimate_period = str(acs_estimate_period)
		self.config_json = json.load(open(config_json_path, 'r'))
		self.stat_vars = open(statVar_file_path, 'r').read().splitlines() #for backward compatability
		
		self.raw_df = None
	
	def _download(self, download_id):
		"""Download the data files from data.census.gov as compressed zip files"""
		response = response.get(f'https://data.census.gov/api/access/table/download?download_id={download_id}')
		return BytesIO(response.content)
		
	def _process_zipFile(self, zipFile):
		"""Process the datasets in the zip file"""
		with ZipFile(zipFile) as zf:
			for filename in zf.namelist():
				if 'data_with_overlays' in filename:
					self._process_and_generate_csv(filename)
	
	def _process_and_generate_csv(self, filename, convertPercent=False):
		"""Process each dataset and append to the cleaned csv"""
		if f"ACSST{self.acs_estimate_period}Y" not in filename"
			return
		
		## initialize the output_csv, a flattened csv
		columns = ['observationDate', 'observationAbout', 'statVarName', 'value', 'unit']
		self.raw_df = pd.DataFrame(columns=columns)
		
		##read the dataset to a dataframe
		##TODO[sharadshriram]: based on the extension of the filename select either read_csv or read_excel
		df = pd.read_csv(filename)
		columnList = df.iloc[1] ##the first row of the dataset has the column names
		
		
		
		## add information about the observation
		observationDate = filename.split(f"ACSST{self.acs_estimate_period}Y")[1][:4]
	
		
		pass
		
			
			
			
			
			
			
			
			
			
			
			
			
			
			
			
			
	

	
  """To process the ACS subject tables

  Attributes:
    config_json: Config file with mapping and constraints for statVars based on populationType
    features_json: Backward compatability for the S2201 import
    download_id: Download token provided by data.census.gov, if the script needs to download the subject tables
    existing_stat_vars: Path to file with list of existing stat vars that we do no need to generate. File expected to contains 1 stat var dcid per line.
    zip_file_path: Input zip file downloaded from data.census.gov (optional)
    csv_file_path: Path where the cleaned csv file will be saved
    tmcf_file_path: Path where the generated tmcf file will be saved 
    mcf_file_path: Path where the generated MCF file will be saved
    stat_var_path: Path to a file that contains list of stat vars, new stat var names that are not in this file will be script. Used in the S2201 import.
  """
  ## TODO[sharadshriram]: add support for MCF 
  def __init__(self, config_json=None, feature_json=None, download_id=None, existing_stat_vars=None, zip_file_path=None, csv_file_path=None, tmcf_file_path=None, mcf_file_path=None):
    """Constructor """
    self.config_json = config_json
    self.feature_json = feature_json
    self.download_id = download_id
    self.existing_stat_var_list = open(existing_stat_vars).readlines.split('\n')
    self.zip_file_path = zip_file_path
    self.csv_file_path = csv_file_path
    self.tmcf_file_path = tmcf_file_path
    self.raw_df = None

  def download_and_process(self, download_id=None):
    pass
  
  def process_zip_file(self, zip_file_path):
    for fname in zip_file_path:
      self._get_data(fname)
    self._create_mcf()
    self._create_tmcf()
    self._format_data()
    pass

  def _get_data(self, raw_df_path):
    #read dataframe
    #based on the config_json set the types for each pd.read
    self.raw_df.apply(self._convert_percentages_as_count, axis=1)
    #returns a dataframe
    pass

  def _format_data(self):
    ## Drop unwanted columns
       # # First column is Name of the place
       # # Second column is Name of the TRU/placeOfResidenceClassification
       # # 3-N are the actual values
       # value_columns = list(self.raw_df.columns[1:-1])

       # # Converting rows in to columns. So the final structure will be
       # # Name,TRU,columnName,value
       # self.raw_df = self.raw_df.melt(id_vars=["census_location_id", "TRU"],
       #                                value_vars=value_columns,
       #                                var_name='columnName',
       #                                value_name='Value')

       # # Add corresponding StatisticalVariable, based on columnName and TRU
       # self.raw_df['StatisticalVariable'] = self.raw_df.apply(
       #     lambda row: self.stat_var_index["{0}_{1}".format(
       #         row["columnName"], row["TRU"])],
       #     axis=1)
       # # Add the census year
       # self.raw_df['Year'] = self.census_year

       # # Export it as CSV. It will have the following columns
       # # Name,TRU,columnName,value,StatisticalVariable,Year
       # self.raw_df.to_csv(self.csv_file_path, index=False, header=True)
    #makes the csv file
    pass

  def _convert_percentages_as_count(self, row):
    pass

def convert_column_to_stat_var(column, features):
    """Converts input CSV column name to Statistical Variable DCID."""
    s = column.split('!!')
    sv = []
    base = False
    for p in s:

        # Set base SV for special cases
        if not base and 'base' in features:
            if p in features['base']:
                sv = [features['base'][p]] + sv
                base = True

        # Skip implied properties
        if 'implied_properties' in features and p in features[
                'implied_properties']:
            dependent = False
            for feature in features['implied_properties'][p]:
                if feature in s:
                    dependent = True
                    break
            if dependent:
                continue

        if 'properties' in features and p in features['properties']:

            # Add inferred properties
            if 'inferred_properties' in features and p in features[
                    'inferred_properties'] and features['inferred_properties'][
                        p] not in s:
                sv.append(
                    features['properties'][features['inferred_properties'][p]])

            # Add current property
            sv.append(features['properties'][p])

    # Set default base SV
    if not base and 'base' in features and '_DEFAULT' in features['base']:
        sv = [features['base']['_DEFAULT']] + sv

    # Prefix MOE SVs
    if 'Margin of Error' in s:
        sv = ['MarginOfError'] + sv
    return '_'.join(sv)


def create_csv(output, stat_vars):
    """Creates output CSV file."""
    fieldnames = ['observationDate', 'observationAbout'] + stat_vars
    with open(output, 'w') as f_out:
        writer = csv.DictWriter(f_out, fieldnames=fieldnames)
        writer.writeheader()

def write_csv(filename, reader, output, features, stat_vars):
    """Reads input_file and writes cleaned CSV to output."""
    if 'ACSST5Y' not in filename:
        return
    fieldnames = ['observationDate', 'observationAbout'] + stat_vars
    stat_var_set = set(stat_vars)
    with open(output, 'a') as f_out:
        writer = csv.DictWriter(f_out, fieldnames=fieldnames)
        observation_date = filename.split('ACSST5Y')[1][:4]
        valid_columns = {}
        for row in reader:
            if row['GEO_ID'] == 'id':

                # Map feature names to stat vars
                for c in row:
                    sv = convert_column_to_stat_var(row[c], features)
                    if sv in stat_var_set:
                        valid_columns[c] = sv
                continue

            new_row = {
                'observationDate': observation_date,
                # TODO: Expand to support other prefixes?
                'observationAbout': 'dcid:geoId/' + row['GEO_ID'].split('US')[1]
            }
            for c in row:

                # We currently only support the stat vars in the list
                if c not in valid_columns:
                    continue
                sv = valid_columns[c]

                # Exclude missing values
                if row[c] in _IGNORED_VALUES:
                    continue

                # Exclude percentages
                if '.' in row[c]:
                    continue

                # Exclude suffix from median values
                if (row[c][-1] == '-' or row[c][-1] == '+'):
                    new_row[sv] = row[c][:-1]
                else:
                    new_row[sv] = row[c]
            writer.writerow(new_row)

  def _format_location_as_geoId(self, row):
    #this works on the geoID column and returns dc geoIds
    pass

  def _get_base_statVar_name(self, row):
    #this works out off config_json for each population type
    #this function will be overwritten by the child class
    name = 'Count' + row['populationType']
    return name
  
  def _create_mcf(self):
    self.mcf = []
    #logic to add new mcfs
    pass

  def _create_tmcf(self):
    #natalie's code
    pass
#def create_tmcf(output, features, stat_vars):
#    """Writes tMCF to output."""
#    with open(output, 'w') as f_out:
#        for i in range(len(stat_vars)):
#            unit = ''
#            if stat_vars[i] in features['units']:
#                unit = _UNIT_TEMPLATE.format(
#                    unit=features['units'][stat_vars[i]])
#            f_out.write(
#                _TMCF_TEMPLATE.format(index=i, stat_var=stat_vars[i],
#                                      unit=unit))
#

  def _convert_columnn_to_statVars(self, data_row):
    #this function updates mcf, uses TEMPLATE_STAT_VAR to make statVars
    pass


## Thej


    def __init__(self, data_file_path, metadata_file_path, mcf_file_path,
                 tmcf_file_path, csv_file_path, existing_stat_var, census_year,
                 dataset_name):
        """
        Constructor
        
        Args:
            data_file_path :  Input XLS file from Census of India. Can be url or local path
            metadata_file_path : Meta data csv file which has attribute details
            mcf_file_path : Path where generated mcf file will be saved
            tmcf_file_path : Path where generated tmcf file will be saved
            csv_file_path : Path where cleaned csv file will be saved
            existing_stat_var : List of existing stat vars that we don't need to generate
            census_year : Census Year
            dataset_name : Census dataset name. Eg:Primary_Abstract_Data
        """
        self.data_file_path = data_file_path
        self.metadata_file_path = metadata_file_path
        self.mcf_file_path = mcf_file_path
        self.csv_file_path = csv_file_path
        self.tmcf_file_path = tmcf_file_path
        self.existing_stat_var = existing_stat_var
        self.census_year = census_year
        self.dataset_name = dataset_name
        self.raw_df = None
        self.stat_var_index = {}
        self.census_columns = []

    def _download_and_standardize(self):
        dtype = {
            'State': str,
            'District': str,
            'Subdistt': str,
            "Town/Village": str,
            "Ward": str,
            "EB": str
        }
        self.raw_df = pd.read_excel(self.data_file_path, dtype=dtype)
        self.census_columns = self.raw_df.columns[CENSUS_DATA_COLUMN_START:]

    def _format_location(self, row):
        # In census of India. Location code for India is all zeros.
        if (row["Level"]).upper() == "INDIA":
            return "0"
        elif (row["Level"]).upper() == "STATE":
            return row["State"]
        elif (row["Level"]).upper() == "DISTRICT":
            return row["District"]
        elif (row["Level"]).upper() == "SUBDISTT":
            return row["Subdistt"]
        elif (row["Level"]).upper() == "TOWN":
            return row["Town/Village"]
        elif (row["Level"]).upper() == "VILLAGE":
            return row["Town/Village"]
        else:
            raise Exception("Location Level not supported")

    def _format_data(self):

        # Generate Census locationid
        self.raw_df["census_location_id"] = self.raw_df.apply(
            self._format_location, axis=1)

        # Remove the unwanted columns. They are census codes which we dont use
        # State,District,Subdistt,Town/Village,Ward,EB
        # We delete them only if they exists
        # From pandas documentation:
        # If errors=‘ignore’, suppress error and only existing labels are dropped
        self.raw_df.drop([
            "State", "District", "Subdistt", "Town/Village", "Ward", "EB",
            "Level", "Name"
        ],
                         axis=1,
                         inplace=True,
                         errors='ignore')
        # First column is Name of the place
        # Second column is Name of the TRU/placeOfResidenceClassification
        # 3-N are the actual values
        value_columns = list(self.raw_df.columns[1:-1])

        # Converting rows in to columns. So the final structure will be
        # Name,TRU,columnName,value
        self.raw_df = self.raw_df.melt(id_vars=["census_location_id", "TRU"],
                                       value_vars=value_columns,
                                       var_name='columnName',
                                       value_name='Value')

        # Add corresponding StatisticalVariable, based on columnName and TRU
        self.raw_df['StatisticalVariable'] = self.raw_df.apply(
            lambda row: self.stat_var_index["{0}_{1}".format(
                row["columnName"], row["TRU"])],
            axis=1)
        # Add the census year
        self.raw_df['Year'] = self.census_year

        # Export it as CSV. It will have the following columns
        # Name,TRU,columnName,value,StatisticalVariable,Year
        self.raw_df.to_csv(self.csv_file_path, index=False, header=True)

    def _get_base_name(self, row):
        # This function is overridden in the child class
        name = "Count_" + row["populationType"]
        return name

    def _get_base_constraints(self, row):
        # This function is overridden in the child class
        constraints = ""
        return constraints

    def _create_variable(self, data_row, place_of_residence=None):
        row = copy.deepcopy(data_row)
        name_array = []
        constraints_array = []

        name_array.append(self._get_base_name(row))

        # No need to add empty constraint to the list
        if self._get_base_constraints(row) != "":
            constraints_array.append(self._get_base_constraints(row))

        if row["age"] == "YearsUpto6":
            name_array.append("YearsUpto6")
            constraints_array.append("age: dcid:YearsUpto6")
        else:
            pass

        if row["socialCategory"] == "ScheduledCaste":
            name_array.append("ScheduledCaste")
            constraints_array.append("socialCategory: dcs:ScheduledCaste")
        if row["socialCategory"] == "ScheduledTribe":
            name_array.append("ScheduledTribe")
            constraints_array.append("socialCategory: dcs:ScheduledTribe")
        else:
            pass

        if row["literacyStatus"] == "Literate":
            name_array.append("Literate")
            constraints_array.append("literacyStatus: dcs:Literate")
        if row["literacyStatus"] == "Illiterate":
            name_array.append("Illiterate")
            constraints_array.append("literacyStatus: dcs:Illiterate")
        else:
            pass

        if row["workerStatus"] == "Worker":
            constraints_array.append("workerStatus: dcs:Worker")
            if row["workerClassification"] == "MainWorker":
                name_array.append("MainWorker")
                constraints_array.append("workerClassification: dcs:MainWorker")
                if row["workCategory"] != "":
                    name_array.append(row["workCategory"])
                    constraints_array.append("workCategory: dcs:" +
                                             row["workCategory"])

            elif row["workerClassification"] == "MarginalWorker":
                name_array.append("MarginalWorker")
                constraints_array.append(
                    "workerClassification: dcs:MarginalWorker")

                if row["workCategory"] != "":
                    name_array.append(row["workCategory"])
                    constraints_array.append("workCategory: dcs:" +
                                             row["workCategory"])

                if row["workPeriod"] == "[Month - 3]":
                    name_array.append("WorkedUpto3Months")
                    constraints_array.append("workPeriod:" + row["workPeriod"])

                if row["workPeriod"] == "[Month 3 6]":
                    name_array.append("Worked3To6Months")
                    constraints_array.append("workPeriod:" + row["workPeriod"])
            else:
                name_array.append("Workers")

        elif row["workerStatus"] == "NonWorker":
            name_array.append("NonWorker")
            constraints_array.append("workerStatus: dcs:NonWorker")

        if place_of_residence == "Urban":
            name_array.append("Urban")
            constraints_array.append(
                "placeOfResidenceClassification: dcs:Urban")
            row["description"] = row["description"] + " - Urban"

        elif place_of_residence == "Rural":
            name_array.append("Rural")
            constraints_array.append(
                "placeOfResidenceClassification: dcs:Rural")
            row["description"] = row["description"] + " - Rural"

        if row["gender"] == "Male":
            name_array.append("Male")
            constraints_array.append("gender: schema:Male")

        elif row["gender"] == "Female":
            name_array.append("Female")
            constraints_array.append("gender: schema:Female")

        name = "_".join(name_array)
        row["name"] = name
        row["constraints"] = "\n".join(constraints_array)

        key = "{0}_{1}".format(
            row["columnName"],
            place_of_residence if place_of_residence != None else "Total")
        self.stat_var_index[key] = name

        self.mcf.append(row)
        stat_var = TEMPLATE_STAT_VAR.format(**dict(row))
        return name, stat_var

    def _create_mcf(self):
        self.mcf = []
        with open(self.metadata_file_path) as csvfile:
            reader = csv.DictReader(csvfile)
            with open(self.mcf_file_path, 'w+', newline='') as f_out:
                for data_row in reader:
                    for place_of_residence in [None, "Urban", "Rural"]:
                        name, stat_var = self._create_variable(
                            data_row, place_of_residence)
                        # If the statvar already exists then we don't
                        # need to recreate it
                        if name in self.existing_stat_var:
                            pass
                        # We need to create statvars only for those columns that
                        # Exist in the current data file
                        elif data_row["columnName"] not in self.census_columns:
                            pass
                        else:
                            f_out.write(stat_var)

    def _create_tmcf(self):
        with open(self.tmcf_file_path, 'w+', newline='') as f_out:
            f_out.write(
                TEMPLATE_TMCF.format(year=self.census_year,
                                     dataset_name=self.dataset_name))

    def process(self):
        self._download_and_standardize()
        self._create_mcf()
        self._create_tmcf()
        self._format_data()



from absl import app, flags
FLAGS = flags.FLAGS

flags.DEFINE_string('output', None, 'Path to folder for output files')
flags.DEFINE_string('download_id', None, 'Download id for input data')
flags.DEFINE_string('features', None, 'JSON of feature maps')
flags.DEFINE_string('stat_vars', None, 'Path to list of supported stat_vars')
flags.mark_flags_as_required(['output', 'features'])

def main(argv):
    f = open(FLAGS.features)
    features = json.load(f)
    f.close()
    f = open(FLAGS.stat_vars)
    stat_vars = f.read().splitlines()
    f.close()
    output_csv = os.path.join(FLAGS.output, 'output.csv')
    create_csv(output_csv, stat_vars)
    response = requests.get(
        f'https://data.census.gov/api/access/table/download?download_id={FLAGS.download_id}'
    )
    with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
        for filename in zf.namelist():
            if 'data_with_overlays' in filename:
                print(filename)
                with zf.open(filename, 'r') as infile:
                    reader = csv.DictReader(io.TextIOWrapper(infile, 'utf-8'))
                    write_csv(filename, reader, output_csv, features, stat_vars)
    create_tmcf(os.path.join(FLAGS.output, 'output.tmcf'), features, stat_vars)


if __name__ == '__main__':
  app.run(main)
  
  
## Thej child class
class CensusPrimaryCensusAbstractDataLoader(CensusPrimaryAbstractDataLoaderBase
                                           ):

    def _get_base_name(self, row):
        name = "Count_" + row["populationType"]
        return name

    def _get_base_constraints(self, row):
        constraints = ""
        return constraints


if __name__ == '__main__':
    data_file_path = os.path.join(os.path.dirname(__file__),
                                  'data/DDW_PCA0000_2011_Indiastatedist.xlsx')
    # data_file_path = "http://censusindia.gov.in/pca/DDW_PCA0000_2011_Indiastatedist.xlsx"
    metadata_file_path = os.path.join(
        os.path.dirname(__file__),
        '../common/primary_abstract_data_variables.csv')
    existing_stat_var = [
        "Count_Household", "Count_Person", "Count_Person_Urban",
        "Count_Person_Rural", "Count_Person_Male", "Count_Person_Female"
    ]
    mcf_file_path = os.path.join(os.path.dirname(__file__),
                                 './IndiaCensus2011_Primary_Abstract_Data.mcf')
    tmcf_file_path = os.path.join(
        os.path.dirname(__file__),
        './IndiaCensus2011_Primary_Abstract_Data.tmcf')
    csv_file_path = os.path.join(os.path.dirname(__file__),
                                 './IndiaCensus2011_Primary_Abstract_Data.csv')

    loader = CensusPrimaryCensusAbstractDataLoader(
        data_file_path=data_file_path,
        metadata_file_path=metadata_file_path,
        mcf_file_path=mcf_file_path,
        tmcf_file_path=tmcf_file_path,
        csv_file_path=csv_file_path,
        existing_stat_var=existing_stat_var,
        census_year=2011,
        dataset_name="Primary_Abstract_Data")
    loader.process()
