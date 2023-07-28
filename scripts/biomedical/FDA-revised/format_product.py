# Copyright 2023 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

'''
Author: Suhana Bedi
Date: 06/01/2023
Name: format_products.py
Description: converts one input FDA products file into three different csv
files with 
@file_input: input .txt product file from FDA
'''

import pandas as pd
import numpy as np
import json
import re
import sys
from products_constant import *
from products_function import *

def market_te_codes_merge(df_products, df_te, df_market_stat):
	merged_data= df_products.merge(df_te, on=["ApplNo","ProductNo"], how='left')
	merged_data = merged_data.drop(['MarketingStatusID', 'TECode','ApplNo_dcid'], axis=1)
	merged_data= merged_data.merge(df_market_stat, on=["ApplNo","ProductNo"], how='left')
	merged_data = merged_data.drop(['ApplNo_dcid'], axis=1)
	return merged_data

def format_dosage_admin_routes(df_products):
	drugs_df = df_products
	cleaned_form = drugs_df["Form"].map(lambda form: ILL_FORMATTED_FORMS[
			form] if form in ILL_FORMATTED_FORMS else form)
	drugs_df["DosageForm"] = cleaned_form.str.split(";", expand=True)[0]
	drugs_df["AdminRoute"] = cleaned_form.str.split(";",
													expand=True)[1].fillna('')
	drugs_df = drugs_df.assign(Strength=drugs_df.Strength.str.split(";")).explode('Strength')
	drugs_df = drugs_df.assign(ActiveIngredient=drugs_df.ActiveIngredient.str.split(";")).explode('ActiveIngredient')
	return drugs_df

def wrapper_fun(df_products, df_te, df_market_stat):
	df_products = market_te_codes_merge(df_products, df_te, df_market_stat)
	df_products = map_chembl_pubchem_names(df_products)
	df_products['DrugName'] = df_products['DrugName'].apply(lambda x: format_chemical_names(x))
	df_products = format_dosage_admin_routes(df_products)
	df_products = format_final_products(df_products)
	df_products = format_products(df_products)
	df_range = format_product_range(df_products)
	df_range.to_csv('products_range.csv', doublequote=False, escapechar='\\')
	df_unit_value = format_product_unit(df_products)
	df_unit_value.to_csv('products_unit.csv', doublequote=False, escapechar='\\')
	df_strength = format_product_strength(df_products)
	df_strength.to_csv('products_strengths.csv', doublequote=False, escapechar='\\')

def main():
	df_products = pd.read_csv('Products.txt', sep = '\t', on_bad_lines='skip')
	df_te = pd.read_csv('TECodes.csv')
	df_market_stat = pd.read_csv('MarketingStatus.csv')
	wrapper_fun(df_products, df_te, df_market_stat)

if __name__ == "__main__":
	main()



