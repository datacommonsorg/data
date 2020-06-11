# -*- coding: utf-8 -*-

import pandas as pd
import json
import os
import collections
import datetime

def main():
  #Step 0: load and combine the data into single dataFrame
  CDC_prediction = pd.concat([pd.read_csv(os.path.join("./CSV_original", file)) for file in os.listdir("./CSV_original") if file[-4:] == '.csv']).reset_index(drop = True)
  CDC_prediction = CDC_prediction.rename(columns={"target_week_end_date": "target_date"})
   
  #drop the quantiles for now, come back later
  CDC_prediction = CDC_prediction.drop(columns = ["quantile_0.025", "quantile_0.975"])

  #Step 1: resolve the inconsistency in model names, especially in data on 2020-05-04 and 2020-04-27
  model_rename = {"UChicago":"UChicago_10", "Geneva-DeterministicGrowth": "Geneva", "GT-DeepCOVID": "GA_Tech", "IHME-CurveFit":"IHME",\
                "LANL-GrowthRate":"LANL", "MIT_CovidAnalytics-DELPHI":"MIT", "MOBS_NEU-GLEAM_COVID":"MOBS","NotreDame-FRED":"NotreDame",\
                "UCLA-SuEIR":"UCLA", "UMass-MechBayes":"UMass-MB", "UT-Mobility":"UT", "UT Austin":"UT", "YYG-ParamSearch":"YYG",\
                "University of Geneva":"Geneva", "Imperial-ensemble1":"Imperial1", "Imperial-ensemble2": "Imperial2"}
  CDC_prediction["model"] = CDC_prediction["model"].map(model_rename).fillna(CDC_prediction["model"])
  CDC_prediction["model"] = CDC_prediction["model"].str.replace(" ","")


  #Step 2: convert the "location_name" to dcid in Data Commons
    #map the abbreviation of state to full name
  state_map_path = './mapping/state_abbrev.json'
  with open(state_map_path, 'r') as file:
    state_map = json.load(file)

    #map the name of location to dcid
  dcid_map_path = './mapping/state_dcid.json'
  with open(dcid_map_path, 'r') as file:
    dcid_map = json.load(file)
    for key, value in state_map.items():
      dcid_map[key] = dcid_map[value]

    #store the dcid to column "location"
  CDC_prediction["location"] = CDC_prediction["location_name"].map(dcid_map)
  assert CDC_prediction["location"].isnull().sum() == 0
  CDC_prediction = CDC_prediction.drop(columns = ["location_name"])


  #Step 3: Convert date into YYYY-MM-DD format
  CDC_prediction["forecast_date"] = pd.to_datetime(CDC_prediction["forecast_date"]).dt.strftime('%Y-%m-%d')
  CDC_prediction["target_date"] = pd.to_datetime(CDC_prediction["target_date"]).dt.strftime("%Y-%m-%d")


  #Step 4: convert "target" into "target_date" for data without "target_date"
    #extract the weeks from target
  CDC_missing = CDC_prediction[CDC_prediction["target_date"] == "NaT"]
  CDC_missing[["weeks", "wk", "ahead", "countType", "death"]] = CDC_missing["target"].str.split(' ', expand = True)
  assert (CDC_missing["wk"] != "wk").sum() == 0 and (CDC_missing["ahead"] != "ahead").sum() == 0 and\
      (CDC_missing["death"] != "death").sum() == 0
  CDC_missing = CDC_missing.drop(columns = ["wk", "ahead", "death"])
  CDC_missing["weeks"] = CDC_missing["weeks"].astype(int)

    #assign date extracted from "target" to "target_date"
  pd.options.mode.chained_assignment = None
  grouped_missing_date = CDC_missing.groupby(["weeks"])
  for _,missingdate in grouped_missing_date:
    week = missingdate["weeks"].unique()[0]
    predicted_date = pd.to_datetime(missingdate["forecast_date"])+ pd.Timedelta("{} days".format(week*7))
    #print(predicted_date.index)
    CDC_prediction["target_date"].loc[predicted_date.index] = predicted_date.dt.strftime("%Y-%m-%d")

  #Step 5: split the "point" value based on "model" and "target"
  grouped_CDC = CDC_prediction.groupby(["model", "target"])
  prefixes = []

  for _, prediction in grouped_CDC:
    #get the "model" and "target" and store it for generating tMCF
    modelname = prediction["model"].unique()[0]
    targets = prediction["target"].unique()[0].split(" ")
    if len(targets) == 5:
      target = targets[0]+"Weeks" + targets[3][0].capitalize()+targets[3][1:]
    else:#observed data
      target = prediction["target"].unique()[0]
    colname = modelname + "_" + target
    prefixes.append([modelname, target])
    
    #split the columns
    CDC_prediction[colname] = None
    CDC_prediction[colname].loc[prediction.index] = prediction["point"]
  CDC_prediction = CDC_prediction.drop(columns = ["point", "model", "target"])
  
  #Step 6: save the data
  save_path = "./forecast_death-2020-04-13to2020-06-01.csv"
  CDC_prediction.to_csv(save_path, index = False)
  with open('colnames.txt', 'w') as filehandle:
    for model,target in prefixes:
        filehandle.write("{},{}\n".format(model,target))

if __name__ == "__main__":
    main()
