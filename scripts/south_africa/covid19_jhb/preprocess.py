"""Cleaning script for the COVID-19 data for Johannesburg."""

import pandas as pd


def process_csv(input_path, output_path):
    # Read the CSV file into a DataFrame
    df = pd.read_csv(input_path)

    # Add a new column 'place' with the DCID for Johannesburg'
    df["place"] = "wikidataId/Q2346838"

    df.rename(
        columns={
            "Johannesburg\tCases": "cases",
            "Johannesburg\tDeaths": "deaths",
        },
        inplace=True,
    )

    # Extract the desired columns
    selected_columns = ["date", "place", "cases", "deaths"]
    df_selected = df[selected_columns]

    # Convert specific columns to integers
    int_columns = ["cases", "deaths"]
    for col in int_columns:
        df_selected.loc[:, col] = pd.to_numeric(df_selected[col],
                                                errors="coerce").astype("Int64")

    # Remove duplicates and keep the first occurrence
    df_no_duplicates = df_selected.drop_duplicates()

    # Save the processed DataFrame to a new CSV file
    df_no_duplicates.to_csv(output_path, index=False)


if __name__ == "__main__":
    # Specify the path to your input CSV file
    input_csv_path = "gp_johannesburg.csv"

    # Specify the path for the output CSV file
    output_csv_path = "cleaned_data.csv"

    # Process the CSV file
    process_csv(input_csv_path, output_csv_path)
