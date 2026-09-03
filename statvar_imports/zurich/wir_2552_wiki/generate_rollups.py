#!/usr/bin/env python3
"""Preprocesses Zurich WIR255OD2552 dataset to filter total roll-up rows (Alle Rechtsformen and Alle Betriebsgrössen)."""

import os
import pandas as pd

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_RAW = os.path.join(CURRENT_DIR, 'input_files', 'WIR255OD2552.csv')
OUTPUT_ROLLUPS = os.path.join(CURRENT_DIR, 'input_files', 'WIR255OD2552_rollups.csv')

def main():
    if not os.path.exists(INPUT_RAW):
        raise FileNotFoundError(f"{INPUT_RAW} not found.")

    try:
        df = pd.read_csv(INPUT_RAW, encoding='utf-8')
    except UnicodeDecodeError:
        df = pd.read_csv(INPUT_RAW, encoding='iso-8859-1')

    # Keep only the total rows (Alle Rechtsformen and Alle Betriebsgrössen)
    df_rollups = df[(df['RechtsformSort'] == 0) & (df['BetriebsgrSort'] == 0)].copy()

    # Convert numeric columns, converting non-numeric markers (e.g. 'K') to NaN/numeric
    val_cols = ['Arbeitsstaetten', 'AnzBesch', 'AnzBeschW', 'AnzBeschM', 'AnzVZA', 'AnzVZAW', 'AnzVZAM']
    for col in val_cols:
        if col in df_rollups.columns:
            df_rollups[col] = pd.to_numeric(df_rollups[col], errors='coerce')

    df_rollups.to_csv(OUTPUT_ROLLUPS, index=False, encoding='utf-8')
    print(f"Successfully generated {OUTPUT_ROLLUPS} with {len(df_rollups)} rows.")

if __name__ == '__main__':
    main()
