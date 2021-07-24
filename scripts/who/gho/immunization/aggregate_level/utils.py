import os
import sys
import numpy as np
import pandas as pd
import urllib.request
from typing import Dict


def download_raw_data_csv(base_data_url: str, gho_indicator_code: str, 
	columns_to_dtypes: Dict= {}) -> pd.DataFrame:
	""" Download the data csv and return a dataframe.

	Args:
		base_data_url: a url string to extract the data from.
	"""

	# Some input validations.
	assert(base_data_url is not None),  "base_data_url is None."
	assert(gho_indicator_code is not None),  "ghp_indicator_code is None."
	assert(type(columns_to_dtypes) == type({})),  "columns_to_dtypes is not Dict."

	# Construct the data download url.
	url = base_data_url.format(gho_indicator_code)

	cols_to_dtypes_string = ' Attempting to retrieve only the following columns and their dtypes: {0}. '.format(columns_to_dtypes)
	
	# download the data
	try:
		if columns_to_dtypes:	
			raw_df = pd.read_csv(url, usecols=columns_to_dtypes.keys(), 
				dtype=columns_to_dtypes)
		else:
			cols_to_dtypes_string = ''
			raw_df = pd.read_csv(url)

		return raw_df

	except Exception as e:
		exception_msg = "An Exception occured in download_raw_data_csv(). \n"
		exception_msg += "Failed to retrieve and format the data from: \n\t{0}.\n".format(url)
		exception_msg += cols_to_dtypes_string + ".\n"
		exception_msg += 'Original Exception type: \n\t{0}.\n'.format(type(e))
		exception_msg += 'Original Exception message: \n\t{0}'.format(e)

	raise Exception(exception_msg)


def get_numerator_prefix_string(measured_property, population_type, age_field='', suffix=''):
    assert(type(measured_property) == type("str"))
    assert(type(population_type) == type("str"))
    assert(type(age_field) == type("str"))
    assert(type(suffix) == type("str"))

    numerator_prefix = "{0}_{1}".format(measured_property, population_type)
    if age_field:
        numerator_prefix += "_{0}".format(age_field)

    if suffix:
        numerator_prefix += "_{0}".format(suffix)
    
    return numerator_prefix

def get_denom_string(numerator_prefix, has_denom=False):
    assert(type(numerator_prefix) == type("str"))
    assert(type(has_denom) == type(True))

    denom_string = ""
    if has_denom:
        denom_string += "_AsAFractionOf_{0}".format(numerator_prefix)

    return denom_string


def stats_var_name(numerator_prefix, immunization_name, denom_string):
    assert(type(numerator_prefix) == type("str"))
    assert(type(immunization_name) == type("str"))
    assert(type(denom_string) == type("str"))

    numerator_string = numerator_prefix
    immunization_string = "_{0}Immunization".format(immunization_name)

    return "{0}{1}{2}".format(numerator_string, immunization_string, denom_string)

def _get_age_field(metadata_df_row, metadata_df_cols):
    age_field = ''
    # Only process age if both age and ageUnit have valid values.
    if ('age' in metadata_df_cols) and ('ageUnit' in metadata_df_cols):
        if ((~np.isnan(metadata_df_row.age)) 
            and (metadata_df_row.age != 'nan') 
            and (metadata_df_row.ageUnit != 'nan')):
            age_field = "%d%s" %(int(metadata_df_row.age), metadata_df_row.ageUnit)

    return age_field

def _get_numerator_and_denom_strings(metadata_df_row, metadata_df_cols):

    pop_type_string = str.split(metadata_df_row.populationType, ":")[1]
    age_field = _get_age_field(metadata_df_row, metadata_df_cols)

    suffix = ''
    if (('statsVarNameSuffix' in metadata_df_cols) 
        and (str(metadata_df_row.statsVarNameSuffix) != 'nan')):
        suffix = metadata_df_row.statsVarNameSuffix

    has_denom = False
    if (('hasDenominator' in metadata_df_cols) 
        and (str(metadata_df_row.hasDenominator) == 'Yes')):
        has_denom = True

    num_prefix = get_numerator_prefix_string(
        metadata_df_row.measuredProperty,
        pop_type_string, 
        age_field=age_field,
        suffix=suffix)

    denom_string = get_denom_string(num_prefix, has_denom)

    return (num_prefix, denom_string)

def create_stats_vars_helper(metadata_df: pd.DataFrame, stat_var_template: str) -> Dict:
    stats_vars = {}
    for i in range(0, len(metadata_df)):
        row = metadata_df.iloc[i]

        (num_prefix, denom_string) = _get_numerator_and_denom_strings(row, metadata_df.columns)
        var_name = stats_var_name(num_prefix, row.immunizationName, denom_string)

        age_field = _get_age_field(row, metadata_df.columns)

        # Format the mandatory fields.
        stats_vars_string = stat_var_template.format(
            name = "dcid:{0}".format(var_name),
            description = row.description,
            populationType = row.populationType,
            statType = 'dcs:measuredValue',
            measuredProperty = 'dcs:%s' %str.lower(row.measuredProperty)
        )

        # Add additional fields
        if "immunizedAgainst" in metadata_df.columns:
            stats_vars_string += "immunizedAgainst: dcs:{0}\n".format(row.immunizedAgainst)
        if "ghoCode" in metadata_df.columns:
            stats_vars_string += "ghoCode: {0}\n".format(row.ghoCode)
        if age_field:
            stats_vars_string += "age: [{1} {0}]\n".format(int(row.age), row.ageUnit)
        if denom_string:
            stats_vars_string += "measurementDenominator: dcs:{0}\n".format(num_prefix)

        # Finally, add constraints.
        if ("constraintProperties" in metadata_df.columns) and (row.constraintProperties != 'nan'):
            constraints_list = str.split(row.constraintProperties, ",")

            constraints_string = "constraintProperties: "
            for const in constraints_list:
                if const[0] == ' ':
                    const = const[1:]
                constraints_string += "dcs:" + str(const) + ", "

            # Remove the final ",".
            stats_vars_string += constraints_string[:-2] + "\n\n"

        stats_vars[row.ghoCode] = stats_vars_string
    return stats_vars

def retrieve_and_process_data_helper(
    data_base_path: str, metadata_df: pd.DataFrame, 
    columns_to_type_dict: Dict) -> pd.DataFrame:

    raw_data_df = pd.DataFrame()
    for i in range(0, len(metadata_df)):
        row = metadata_df.iloc[i]
        gho_code = row['ghoCode']

        (num_prefix, denom_string) = _get_numerator_and_denom_strings(
            row, metadata_df.columns)
        var_name = stats_var_name(
            num_prefix, row.immunizationName, denom_string)

        new_data_df = download_raw_data_csv(
            data_base_path, gho_code, columns_to_type_dict)

        new_data_df['VarName'] = var_name
        
        raw_data_df = pd.concat([raw_data_df, new_data_df])

    # Now process/sanitize the columns.
    #raw_data_df["GHO (CODE)"] = stats_var_name(raw_data_df["ghoCode"])
    raw_data_df["COUNTRY (CODE)"] = "country/" + raw_data_df["COUNTRY (CODE)"]
        
    raw_data_df = raw_data_df.rename(columns={
        "VarName": "StatisticalVariable", 
        "COUNTRY (CODE)":"Location_Code",
        "YEAR (DISPLAY)": "Date", 
        "Numeric": "Value",
        }, errors="raise")

    return raw_data_df