# Lint as: python3
"""
This script generates the StatisticalVariables defined for COVID19_cumulative_death_forecase
"""
def main():
    STATVAR_TEMPLATE = "Node: dcid:COVID19{}DeathPrediction{}\n" + \
    	"typeOf: schema:StatisticalVariable\n" + \
    	"populationType: dcs:MedicalConditionIncident\n" + \
    	"measuredProperty: dcs:{}\n" + \
    	"statType: dcs:MeasuredValue\n\n"
    countType = ["Cumulative", "Incremental"]
    measuredProperty = ["cumulativeCount", "incrementalCount"]
    variable = ["", "Quantile_0.025", "Quantile_0.975"]

    with open('./COVID19_DeathPredictionCDC_StatisticalVariable.mcf', 'w', newline='') as f_out:
        
        #write the statistical variables
        for cnt,meas in zip(countType, measuredProperty):
            for var in variable:
                f_out.write(STATVAR_TEMPLATE.format(cnt, var, meas))
                         
    return
                
if __name__ == '__main__':
    main()
