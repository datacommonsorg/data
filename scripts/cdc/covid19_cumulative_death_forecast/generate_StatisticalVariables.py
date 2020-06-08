# Lint as: python3
"""
This file generate the StatisticalVariables defined for COVID19_cumulative_death_forecase
"""

def main():
    STATVAR_TEMPLATE = "Node: dcid:COVID19{}DeathPrediction{}\ntypeof: schema:StatisticalVariable\npopulationType: dcs:MedicalConditionIncident\nstatType: dcs:MeasuredValue\n\n"
    countType = ["Cumulative", "Increased"]
    variable = ["", "Quantile_0.025", "Quantile_0.975"]
    
    
    with open('./COVID19_DeathPredictionCDC_StatisticalVariable.mcf', 'w', newline='') as f_out:
        for cnt in countType:
            for var in variable:
                f_out.write(STATVAR_TEMPLATE.format(cnt, var))
    return
                
if __name__ == '__main__':
    main()
