# Lint as: python3
"""
This script generates the required MCF files including: the templated MCF, Statistical Variable definition and other related schema definition for COVID19_death_forecast_CDC
"""
import sys
import pandas as pd
import os 

def loadColnames(filename:str):
   # get the model and target from file
   colnames = []
   with open(filename, 'r') as filehandle:
    for line in filehandle:
        # remove linebreak which is the last character of the string
        row = line[:-1].split(",")
        # add item to the list
        colnames.append(row)
   return colnames

def generate_templateMCF() -> None:
   colnames = loadColnames("./colnames.txt")
   
   NAME = "COVID19DeathPredictionCDC"
   GEO_TEMPLATE = "Node: E:" + NAME + "->E0\n" + \
   	"typeOf: dcs:State\n" + \
   	"dcid: C:" + NAME + "->location\n\n"
   
   TEMPLATE = "Node: E:" + NAME +"->E{index}\n" + \
   	"typeOf: dcs:StatVarObservation\n" + \
   	"variableMeasured: dcs:COVID19_{prefix}\n" + \
   	"observationAbout: E:" + NAME + "->E0\n" + \
   	"observationDate: C:" + NAME + "->target_date\n" + \
   	"value: C:" + NAME +"->{prefix}\n\n"
   
   idx = 1

   with open('./COVID19_DeathPredictionCDC.mcf', 'w', newline='') as f_out:
     f_out.write(GEO_TEMPLATE)
     for model, target in colnames:
       prefix = model + "_" + target
       f_out.write(TEMPLATE.format_map({"index": idx,"prefix": prefix}))
       idx += 1
               
def generate_StatisticalVariables()->None:
    colnames = loadColnames("./colnames.txt")
    STATVAR_TEMPLATE = "Node: dcid:COVID19_{prefix}\n" + \
    	"typeOf: dcs:StatisticalVariable\n" + \
    	"populationType: dcs:MedicalConditionIncident\n" + \
    	"measuredProperty: dcs:{countType}\n" + \
    	"statType: dcs:measuredValue\n\n"
    
    with open('./COVID19_DeathPredictionCDC_StatisticalVariable.mcf', 'w', newline='') as f_out:
        for model, target in colnames:
            prefix = model + "_" + target
            if "inc" in target:
               countType = "incrementalCount"
            else:
               countType = "cumulativeCount"
            f_out.write(STATVAR_TEMPLATE.format_map({"prefix":prefix, "countType":countType}))
                         
    return
    
def generate_schema() -> None:
    model_info = pd.read_csv('./model_info-cleanup.csv')
    MODEL_TEMPLATE = "Node: dcid:COVID19DeathPredictionModel_{name}\n" + \
	"name: {name}\n" + \
	"typeOf: dcs:MeasurementMethodEnum\n" + \
	"description: {description}\n" + \
	"url: {url}\n\n"
	
    with open('./COVID19_DeathPredictionCDC_schema.mcf', 'w', newline='') as f_out:
        Predict_date = "Node: dcid:predictionDate\n" + \
            "name: predictionData\n" + \
            "typeOf: schema:Property\n" + \
            "domainIncludes: dcs:Observation\n" + \
            "rangeIncludes: dcs:Date\n" + \
            "description: the date the prediction was made\n\n"
        f_out.write(Predict_date)
        for _,row in model_info.iterrows():
            f_out.write(MODEL_TEMPLATE.format_map({"name": row["name"], "description": row["Description"], "url": row["url"]}))                  
    return

def main(argv):
    if not argv:
    	print("\nspecify the file(s) to be generated: \n" +\
    		"\ttMCF: template MCF\n\tSV: StatisticalVariable\n\tschema\n")
    for name in argv:
        if name == "tMCF":
            generate_templateMCF()
        if name == "SV":
            generate_StatisticalVariables()
        if name == "schema":
            generate_schema()
       
if __name__ == '__main__':
    main(sys.argv[1:])
