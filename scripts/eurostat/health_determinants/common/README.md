# Configuration details to download and process input files.

### Download input files
1. Add input file details such as import url, file names, file extension to import_download_details.py
2. Add import name to flag details in download_eurostat_input_files.py
3. Run below command to download input files and to store in import specific directory

`python scripts/eurostat/health_determinants/common/download_eurostat_input_files.py --import_name <import_name>`

E.g., to download alcohol_consumption input files, run below command. 
`python scripts/eurostat/health_determinants/common/download_eurostat_input_files.py --import_name alcohol_consumption`

Above command downloads and persists input files under scripts/eurostat/health_determinants/alchohol_consumption/input_files directory


### Process input files
scripts/eurostat/health_determinants/common/euro_stat.py module provides base class - EuroStat with common methods to generate csv, mcf and tmcf files
Depending on import specific properties one would have to override instance variables and abstract methods of EuroStat base class in child class.

Override below instance variables and methods in import specific sub-class

Instance variable -
_import_name
_mcf_template
_sv_value_to_property_mapping
_sv_properties_template

Methods -
_property_correction() - Override for Property correction / modification
_sv_name_correction() - Override for SV name corrections
_rename_frequency_column() - Incase frequency column needs to be renamed, use this method


Config files -
scripts/eurostat/health_determinants/common/sv_config.py 
Provide configuration details of how to form SV names from key properties available in input files.


scripts/eurostat/health_determinants/common/replacement_functions.py
Data standardization rules for various properites (columns).
