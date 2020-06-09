# -*- coding: utf-8 -*-

import pandas as pd
import json
import os
import collections
import datetime

def main():
	# load and combine the data into single dataFrame
	current_path = os.getcwd()
	data_path = os.path.join(current_path, 'CSV_original/')
	CDC_prediction = pd.concat([pd.read_csv(os.path.join(data_path, file)) for file in os.listdir(data_path) if file[-4:] == '.csv'])
	CDC_prediction = CDC_prediction.rename(columns={"target_week_end_date": "target_date", "point": "cumulativeCount"})
	
	#resolve the inconsistency in model names, especially in data on 2020-05-04 and 2020-04-27
	model_rename = {"UChicago":"UChicago_10", "Geneva-DeterministicGrowth": "Geneva", "GT-DeepCOVID": "GA_Tech", "IHME-CurveFit":"IHME",\
                "LANL-GrowthRate":"LANL", "MIT_CovidAnalytics-DELPHI":"MIT", "MOBS_NEU-GLEAM_COVID":"MOBS","NotreDame-FRED":"NotreDame",\
                "UCLA-SuEIR":"UCLA", "UMass-MechBayes":"UMass-MB", "UT-Mobility":"UT", "UT Austin":"UT", "YYG-ParamSearch":"YYG",\
                "University of Geneva":"Geneva", "Imperial-ensemble1":"Imperial1", "Imperial-ensemble2": "Imperial2"}
	CDC_prediction["model"] = CDC_prediction["model"].map(model_rename).fillna(CDC_prediction["model"])                

	#map the abbreviation of state to full name
	state_map_path =  os.path.join(current_path,'mapping/state_abbrev.json')
	with open(state_map_path, 'r') as file:
	  state_map = json.load(file)

	#map the name of location to dcid
	dcid_map_path = os.path.join(current_path, 'mapping/state_dcid.json')
	with open(dcid_map_path, 'r') as file:
	  dcid_map = json.load(file)
	for key, value in state_map.items():
	  dcid_map[key] = dcid_map[value]

	#store the dcid to column "location"
	CDC_prediction["location"] = CDC_prediction["location_name"].map(dcid_map)
	assert CDC_prediction["location"].isnull().sum() == 0
	CDC_prediction = CDC_prediction.drop(columns = ["location_name"])
	
	# Convert date into YYYY-MM-DD format
	CDC_prediction["forecast_date"] = pd.to_datetime(CDC_prediction["forecast_date"]).dt.strftime('%Y-%m-%d')
	CDC_prediction["target_date"] = pd.to_datetime(CDC_prediction["target_date"]).dt.strftime("%Y-%m-%d")
	
	# Split Observation and Prediction
	CDC_observation = CDC_prediction[CDC_prediction["target"] == "observed"].drop(columns = ["target"])
	CDC_prediction = CDC_prediction[CDC_prediction["target"] != "observed"]

        # convert "target" into "target_date" for data without "target_date"
	# extract weeks from "target"
	target = CDC_prediction["target"].str.split(' ', expand = True)
	assert target.isnull().sum().sum() == 0 
	assert target[1].unique() == ["wk"] and target[2].unique() == ["ahead"] and target[4].unique() == ["death"]
        
	# save the countType: cummulative or increase (cum / inc)
	pd.options.mode.chained_assignment = None
	
	CDC_prediction["incrementalCount"] = CDC_prediction["cumulativeCount"]
	CDC_prediction["incrementalCount"][target[3] == "cum"] = None 
	CDC_prediction["cumulativeCount"][target[3] == "inc"] = None
	CDC_prediction["weeks"] = target[0].astype(int)
	grouped_missing_date = CDC_prediction[CDC_prediction["target_date"] == "NaT"].groupby(["weeks"]) 
	
        # assign date extracted from "target" to "target_date"
	for _,missingdate in grouped_missing_date:
	   week = missingdate["weeks"].unique()[0]
	   predicted_date = pd.to_datetime(missingdate["forecast_date"])+ pd.Timedelta("{} days".format(week*7))
	   CDC_prediction["target_date"].loc[predicted_date.index] = predicted_date.dt.strftime("%Y-%m-%d")
	CDC_prediction = CDC_prediction.drop(columns = ["target", "weeks"])
	
	# save the data
	CDC_data = pd.concat([CDC_prediction, CDC_observation],axis=0, ignore_index=True, sort = False)
	save_path = os.path.join(current_path,"forecast_death-2020-04-13to2020-06-01.csv")
	CDC_data.to_csv(save_path, index = False)
	
if __name__ == "__main__":
    main()
