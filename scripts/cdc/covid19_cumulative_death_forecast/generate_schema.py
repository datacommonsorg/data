# Lint as: python3
"""
This script generates the StatisticalVariables defined for COVID19_cumulative_death_forecase
"""
import pandas as pd
import os 

def main():
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
                
if __name__ == '__main__':
    main()
