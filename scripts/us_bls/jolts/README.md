# Scripts for importing dataset from the Search Results U.S. Bureau of Labor Statistics (BLS) Job Openings and Labor Turnover Survey (JOLTS)

Data is fetched from various data sources within the BLS site
then combined and cleaned.

Statistical Variables are generated and cleaned CSV is output.

Download the requirements.txt via pip and execute the file with Python 3.

Dataset being processed: https://download.bls.gov/pub/time.series/jt/

JOLTS dataset contains both NAICS industry codes and BLS jolts aggregations.
# Existing NAICS Codes are mapped directly while
# custom JOLTS codes include a colon distinguishing their new name.
_CODE_MAPPINGS = {
    '000000': '000000:Total nonfarm',  # New Code
    '100000': '10',
    '110099': '110099:Mining and logging',  # New Code
    '230000': '23',
    '300000': '300000:Manufacturing',  # New Code
    '320000': '320000:Durable goods manufacturing',  # New Code
    '340000': '340000:Nondurable goods manufacturing',  # New Code
    '400000': '400000:Trade, transportation, and utilities',  # New Code
    '420000': '42',
    '440000': '44',
    '480099': '480099:Transportation warehousing, and utilities',  # New Code
    '510000': '51',
    '510099': '510099:Financial activities',  # New Code
    '520000': '52',
    '530000': '53',
    '540099': '540099:Professional and business services',  # New Code
    '600000': '600000:Education and health services',  # New Code
    '610000': '61',
    '620000': '62',
    '700000': '700000:Leisure and hospitality',  # New Code
    '710000': '71',
    '720000': '72',
    '810000': '81',
    '900000': '900000:Government',  # New Code
    '910000': '910000:Federal',  # New Code
    '920000': '92',
    '923000': '923000:State and local government education',  # New Code
    '929000':
        '929000:State and local government excluding education'  # New Code
}


"""Fetches and combines BLS Jolts data sources.

Downloads detailed series information from the entire JOLTS dataset.
Each of the files is read, combined into a single dataframe, and processed.

Returns:
 jolts_df: The 6 job data categories by industry, year, and adjustment,
  as a data frame.
 schema_mapping: List of tuples that contains information for each dataset.
  """
  
Additional information about each dataframe.
1. Tuple Format: Statistical Variable name, Stat Var population,
2. Stat Var Job Change Type If Relevant, Dataframe for Stat Var.
    
     """Creates Statistical Variable nodes.

    A new statistical industry is needed for each of the 6 job variables
    and for every industry.
    The industry codes may be either NAICS or BLS_JOLTS aggregations.
    The schema_mapping is used for additional information for
    each of the 6 job variables. These new variables are written
    to the statistical variables mcf file.

    Args:
      jolts_df: The df of BLS Jolts data created by generate_cleaned_dataframe.
      schema_mapping: The schema mapping created by generate_cleaned_dataframe.
  """
    template_stat_var = """
  Node: dcid:{STAT_CLASS}_NAICS{INDUSTRY}_{ADJUSTMENT}
  typeOf: dcs:StatisticalVariable
  populationType: {POPULATION}
  jobChangeEvent: dcs:{JOB_CHANGE_EVENT}
  statType: dcs:measuredValue
  measuredProperty: dcs:count
  measurementQualifier: {BLS_ADJUSTMENT}
  naics: dcid:NAICS/{INDUSTRY}
  """
  
   """ Executes the downloading, preprocessing, and outputting of
  required MCF and CSV for JOLTS data.
  """
  
IMPORTANT: 
	If any new statistical variable comes in future , it is to be added to the dictionaries : _dcid_map in map_config.py
		

