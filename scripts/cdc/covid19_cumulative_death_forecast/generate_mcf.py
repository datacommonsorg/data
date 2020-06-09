# Lint as: python3
"""
This script generates the required MCF files including: the templated MCF, Statistical Variable definition and other related schema definition for COVID19_death_forecast_CDC
"""
import sys
import pandas as pd
import os 

def generate_templateMCF() -> None:
   NAME = "COVID19DeathPredictionCDC"
   GEO = "Node: E:" + NAME + "->E0\n" + \
   	"typeOf: schema:State\n" + \
   	"dcid: C:" + NAME + "->location\n\n"
   
   TEMPLATE = "Node: E:" + NAME +"->E{}\n" + \
   	"typeOf: dcs:StatVarObservation\n" + \
   	"variableMeasured: dcs:COVID19{}DeathPrediction{}\n" + \
   	"observationAbout: E:" + NAME + "->E0\n" + \
   	"observationDate: C:" + NAME + "->target_date\n" + \
   	"predictionDate: C:" + NAME + "->forecast_date\n" + \
   	"value: C:" + NAME +"->{}\n" + \
   	"measurementMethod: C:"+ NAME + "->model\n\n"
   
   idx = 1
   countTypes = ["Cumulative", "Incremental"]
   variable = ["", "Quantile_0.025", "Quantile_0.975"]
   columns = [["cumulativeCount", "quantile_0.025", "quantile_0.975"],
              ["incrementalCount", "quantile_0.025", "quantile_0.975"]]
   with open('./COVID19_DeathPredictionCDC.mcf', 'w', newline='') as f_out:
       f_out.write(GEO)
       for cnt in range(2):
           for var in range(3):
               f_out.write(TEMPLATE.format(idx, countTypes[cnt], variable[var], columns[cnt][var]))
               idx += 1
               
def generate_StatisticalVariables()->None:
    STATVAR_TEMPLATE = "Node: dcid:COVID19{}DeathPrediction{}\n" + \
    	"typeOf: schema:StatisticalVariable\n" + \
    	"populationType: dcs:MedicalConditionIncident\n" + \
    	"measuredProperty: dcs:{}\n" + \
    	"statType: dcs:MeasuredValue\n\n"
    countTypes = ["Cumulative", "Incremental"]
    measuredProperty = ["cumulativeCount", "incrementalCount"]
    variable = ["", "Quantile_0.025", "Quantile_0.975"]

    with open('./COVID19_DeathPredictionCDC_StatisticalVariable.mcf', 'w', newline='') as f_out:
        
        #write the statistical variables
        for cnt,meas in zip(countTypes, measuredProperty):
            for var in variable:
                f_out.write(STATVAR_TEMPLATE.format(cnt, var, meas))
                         
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
