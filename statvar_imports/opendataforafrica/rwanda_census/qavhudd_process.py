import pandas as pd
import numpy as np

df_input = pd.read_csv("input_files/qavhudd.csv")


df_input["TMP_PLC"] = np.where((df_input["ID_DISTRICTS"]=="D"),
                             df_input["REGIONID_PROVINCE"],
                            df_input["REGIONID_DISTRICTS"]
)

df_input["PLACE"] = np.where( pd.isna(df_input['TMP_PLC']),
                            df_input["ID_DISTRICTS"],
                            df_input["TMP_PLC"]
)

df_input=df_input[["PROVINCE","ID_PROVINCE","REGIONID_PROVINCE","DISTRICTS","ID_DISTRICTS","REGIONID_DISTRICTS","TMP_PLC","PLACE","INDICATOR","ID_INDICATOR","FREQ","TIME_PERIOD","OBS_VALUE"]]

df_input.to_csv("input_files/qavhudd_modified.csv",
                index=False)
