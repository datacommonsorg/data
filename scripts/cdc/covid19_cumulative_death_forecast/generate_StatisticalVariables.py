# Lint as: python3
"""
This script generates the StatisticalVariables defined for COVID19_cumulative_death_forecase
"""
import pandas as pd
import os 

def main():
    STATVAR_TEMPLATE = "Node: dcid:COVID19{}DeathPrediction{}\n" + \
    	"typeOf: schema:StatisticalVariable\n" + \
    	"populationType: dcs:MedicalConditionIncident\n" + \
    	"statType: dcs:MeasuredValue\n\n"
    countType = ["Cumulative", "Increased"]
    variable = ["", "Quantile_0.025", "Quantile_0.975"]
    
    
    model_info = pd.read_csv('./model_info.csv')
    MODEL_TEMPLATE = "Node: dcid:COVID19DeathPredictionModel_{}\n" + \
	"name: {}\n" + \
	"typeOf: dcs:MeasurementMethodEnum\n" +\
	"description: {}\n\n"

    
    with open('./COVID19_DeathPredictionCDC_StatisticalVariable.mcf', 'w', newline='') as f_out:
        #write the statistical variables
        for cnt in countType:
            for var in variable:
                f_out.write(STATVAR_TEMPLATE.format(cnt, var))
        #write the models
        
        for _,row in model_info.iterrows():
            f_out.write(MODEL_TEMPLATE.format(row["name"], row["name"], row["Description"]))
                   
    return
                
if __name__ == '__main__':
    main()
