def main():
    import sys
    import os
    import numpy as np
    import pandas as pd

    file_input = sys.argv[1]
    
    kinetic_dict = {
        "FB2N0": 0,
        "FB1N1000": -1000,
        "FB3N1000": 1000
    }

    df_reactions = pd.read_csv(file_input, sep='\t')
    df_reactions["lowerFluxBound"] = df_reactions["lowerFluxBound"].map(kinetic_dict)
    df_reactions["upperFluxBound"] = df_reactions["upperFluxBound"].map(kinetic_dict)
    # modify reaction ID to humanGEMID format
    df_reactions["id"] = df_reactions["id"].str[2:]
    df_reactions["dcid"] = "bio/" + df_reactions["id"].astype(str)
    df_reactions["fluxRange"] = "[" + df_reactions["lowerFluxBound"].astype(str) + " " + df_reactions["upperFluxBound"].astype(str) + " mmol/gDW" + "]"
    df_reactions = df_reactions.drop(columns = ["lowerFluxBound", "upperFluxBound"], axis = 1)

    output_path = os.path.join(os.getcwd(), "reactions.csv")
    df_reactions.to_csv(output_path, index = None)

if __name__ == '__main__':
    main()
