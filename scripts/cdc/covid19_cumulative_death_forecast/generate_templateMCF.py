# Lint as: python3
"""
This script generates the template MCF for COVID19_death_forecast_CDC
"""

def main():
   NAME = "COVID19DeathPredictionCDC"
   GEO = "Node: E:" + NAME + "->E0\n" + \
   	"typeof: schema:State\n" + \
   	"dcid: C:" + NAME + "->location\n\n"
   
   TEMPLATE = "Node: E:" + NAME +"->E{}\n" + \
   	"typeOf: dcs:StatVarObservation\n" + \
   	"dcid: C:" + NAME + "->countType\n" + \
   	"variableMeasured: dcs:COVID19{}DeathPrediction{}\n" + \
   	"observationAbout: E:" + NAME + "->E0\n" + \
   	"observationDate: C:" + NAME + "->target_date\n" + \
   	"predictionDate: C:" + NAME + "->forecast_date\n" + \
   	"value: C:" + NAME +"->{}\n" + \
   	"measurementMethod: C:"+ NAME + "->model\n\n"
   
   idx = 1
   countTypes = ["Cummulative", "Increased"]
   variable = ["", "Quantile_0.025", "Quantile_0.975"]
   varColumns = ["point", "quantile_0.025", "quantile_0.975"]
   
   with open('./COVID19_DeathPredictionCDC.mcf', 'w', newline='') as f_out:
       f_out.write(GEO)
       for cnt in countTypes:
           for var, varColumn in zip(variable, varColumns):
               f_out.write(TEMPLATE.format(idx, cnt, var, varColumn))
               idx += 1
       
       
if __name__ == '__main__':
    main()
