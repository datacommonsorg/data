# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.licenses/org/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
# Run an installation command
from bblocks import WorldBankData,DebtIDS

DEFAULT_INPUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "input_files")
if not os.path.exists(DEFAULT_INPUT_PATH):
        os.mkdir(DEFAULT_INPUT_PATH)

print(DEFAULT_INPUT_PATH)

interest = ["DT.INT.BLAT.CD","DT.INT.BLTC.CD","DT.INT.BLTC.CD","DT.INT.DLXF.CD",
            "DT.INT.DPNG.CD","DT.INT.DPPG.CD","DT.INT.MIBR.CD",
            "DT.INT.MIDA.CD","DT.INT.MLAT.CD","DT.INT.MLTC.CD",
            "DT.INT.OFFT.CD","DT.INT.PBND.CD","DT.INT.PCBK.CD",
            "DT.INT.PNGB.CD","DT.INT.PNGC.CD","DT.INT.PROP.CD",
            "DT.INT.PRVT.CD"]

principle = ["DT.AMT.DLXF.CD","DT.AMT.DPPG.CD","DT.AMT.DPPG.CD","DT.AMT.OFFT.CD",
            "DT.AMT.MLAT.CD","DT.AMT.MIBR.CD","DT.AMT.MIDA.CD",
            "DT.AMT.MLTC.CD","DT.AMT.BLAT.CD","DT.AMT.BLTC.CD",
            "DT.AMT.PRVT.CD","DT.AMT.PBND.CD","DT.AMT.PCBK.CD",
            "DT.AMT.PROP.CD","DT.AMT.DPNG.CD","DT.AMT.PNGB.CD",
            "DT.AMT.PNGC.CD"]

disbursed = ["DT.DOD.DLXF.CD","DT.DOD.DPPG.CD","DT.DOD.DPPG.CD","DT.DOD.OFFT.CD",
            "DT.DOD.MLAT.CD","DT.DOD.MIBR.CD","DT.DOD.MIDA.CD",
            "DT.DOD.MLTC.CD","DT.DOD.BLAT.CD","DT.DOD.BLTC.CD",
            "DT.DOD.PRVT.CD","DT.DOD.PBND.CD","DT.DOD.PCBK.CD",
            "DT.DOD.PROP.CD","DT.DOD.DPNG.CD","DT.DOD.PNGB.CD",
            "DT.DOD.PNGC.CD"]

currency = ["DT.CUR.DMAK.ZS","DT.CUR.EURO.ZS","DT.CUR.EURO.ZS","DT.CUR.JYEN.ZS",
            "DT.CUR.USDL.ZS","DT.CUR.SDRW.ZS","DT.CUR.OTHC.ZS",
            "DT.CUR.UKPS.ZS","DT.CUR.SWFR.ZS","DT.CUR.MULC.ZS",
            "DT.CUR.FFRC.ZS"]

indicator_list=[interest,currency,principle,disbursed]
indicator_listname=["interest","currency","principle","disbursed"]

for idx, indicator in enumerate(indicator_list):
    print(indicator)   
    debt_id = DebtIDS()
    debt_id.load_data( 
        indicators=indicator,
        start_year=1970,
        end_year=2029           
    )

    df=debt_id.get_data()

    df.to_csv(f"{DEFAULT_INPUT_PATH}/{indicator_listname[idx]}_input.csv",index=False)


