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
	CDC_prediction = CDC_prediction.rename(columns={"target_week_end_date": "target_date"})

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
	CDC_observation = CDC_prediction[CDC_prediction["target"] == "observed"].reset_index(drop = True)
	CDC_observation = CDC_observation.drop(columns = ["forecast_date", "quantile_0.025", "quantile_0.975"])
	CDC_prediction = CDC_prediction[CDC_prediction["target"] != "observed"].reset_index(drop = True)

	# Combine target and target_date
	target = CDC_prediction["target"].str.split(' ', expand = True)
	assert target.isnull().sum().sum() == 0 
	assert target[1].unique() == ["wk"] and target[2].unique() == ["ahead"] and target[4].unique() == ["death"]
        
	#save the countType: cummulative or increase (cum / inc)
	CDC_prediction["countType"] = target[3]
	CDC_prediction["weeks"] = target[0].astype(int)
	pd.options.mode.chained_assignment = None
	
	#convert "target" into "target_date" for data without "target_date"
	grouped_missing_date = CDC_prediction[CDC_prediction["target_date"] == "NaT"].groupby(["weeks"]) 
	for _,missingdate in grouped_missing_date:
	   week = missingdate["weeks"].unique()[0]
	   predicted_date = pd.to_datetime(missingdate["forecast_date"])+ pd.Timedelta("{} days".format(week*7))
	   CDC_prediction["target_date"].loc[predicted_date.index] = predicted_date.dt.strftime("%Y-%m-%d")
	CDC_prediction = CDC_prediction.drop(columns = ["target", "weeks"])

	# split the cummulative death and increasing death data
	CDC_prediction_cum = CDC_prediction[CDC_prediction["countType"] == "cum"].reset_index(drop = True).drop(columns = ["countType"])
	CDC_prediction_inc = CDC_prediction[CDC_prediction["countType"] == "inc"].reset_index(drop = True).drop(columns = ["countType"])
    
	# save the data
	observation_save_path = os.path.join(current_path,"observation-2020-04-13to2020-06-01.csv")
	prediction_cum_save_path = os.path.join(current_path, "prediction_cum-2020-04-13to2020-06-01.csv")
	prediction_inc_save_path = os.path.join(current_path, "prediction_inc-2020-04-13to2020-06-01.csv")
	CDC_observation.to_csv(observation_save_path, index = False)
	CDC_prediction_cum.to_csv(prediction_cum_save_path, index = False)
	CDC_prediction_inc.to_csv(prediction_inc_save_path, index = False)
	
if __name__ == "__main__":
    main()
