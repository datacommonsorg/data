# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

'''
Generates the StatisticalVariable instance and template MCFs.
'''

USAGE = '''
python3 generate_mcf.py
    Writes out the StatisticalVariable instance MCFs to
    "treasury_constant_maturity_rates.mcf" and template MCFs to
    "treasury_constant_maturity_rates.tmcf" in the current working directory.
'''


from maturities import MATURITIES
import pandas as pd

def main():
    variable_template = ( 
        'Node: dcid:US_Treasury_{maturity_underscore}_Constant_Maturity_Rate\n'
        'name: "US_Treasury_{maturity_underscore}_Constant_Maturity_Rate"\n'
        'typeOf: dcs:StatisticalVariable\n'
        'populationType: dcs:Treasury{security_type}\n'
        'measuredProperty: dcs:interestRate\n'
        'statType: dcs:measuredValue\n'
        'measurementMethod: dcs:{maturity_no_hyphen}ConstantMaturity\n'
        'unit: dcs:Percent\n'
    )
    template_template = (
        'Node: E:{filename}->E{index}\n'
        'typeOf: dcs:StatVarObservation\n'
        'variableMeasured: dcs:US_Treasury_{maturity_underscore}_Constant_'\
        'Maturity_Rate\n'
        'observationAbout: dcid:country/USA\n'
        'observationDate: C:{filename}->date\n'
        'value: C:{filename}->{maturity_hyphen}\n'
    )

    with open("treasury_constant_maturity_rates.mcf", "w") as mcf_f, \
         open("treasury_constant_maturity_rates.tmcf", "w") as tmcf_f:

        index = 1
        for maturity, security_type in MATURITIES.items():
            maturity_hyphen = maturity.title()
            maturity_underscore = maturity_hyphen.replace("-", "_")
            format_dict = {
                "filename": "treasury_constant_maturity_rates",
                "index": index,
                "maturity_underscore": maturity_underscore,
                "maturity_hyphen": maturity_hyphen,
                "maturity_no_hyphen": maturity_hyphen.replace("-", ""),
                "security_type": security_type
            }
            
            mcf_f.write(variable_template.format_map(format_dict))
            mcf_f.write("\n")
            tmcf_f.write(template_template.format_map(format_dict))
            tmcf_f.write("\n")

            index += 1


if __name__ == "__main__":
    main()
