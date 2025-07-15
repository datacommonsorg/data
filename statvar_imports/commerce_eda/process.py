import pandas as pd
import os

input_filepath = "input_file/Investment.csv"
output_filepath = "input_file/Investment1.csv"  

us_states = {
    "Alabama", "Alaska", "American Samoa", "Arizona", "Arkansas", "California",
    "Colorado", "Connecticut", "Delaware", "District of Columbia",
    "Federated States of Micronesia", "Florida", "Georgia", "Guam", "Hawaii",
    "Idaho", "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky", "Louisiana",
    "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota", "Mississippi",
    "Missouri", "Montana", "Nebraska", "Nevada", "New Hampshire", "New Jersey",
    "New Mexico", "New York", "North Carolina", "North Dakota",
    "Northern Mariana Islands", "Ohio", "Oklahoma", "Oregon", "Pennsylvania",
    "Puerto Rico", "Rhode Island", "South Carolina", "South Dakota", "Tennessee",
    "Texas", "Utah", "Vermont", "Virginia", "Washington", "West Virginia",
    "Wisconsin", "Wyoming", "U.S. Virgin Islands"
}

# Read CSV without header and skipping first row (if it's a header row)
df = pd.read_csv(input_filepath, header=None, skiprows=1, dtype=str)

output_data = []
current_state = None

for index, row in df.iterrows():
    original_col_a = str(row[0]).strip() if pd.notna(row[0]) else ""

    # Detect state name in column A
    if original_col_a in us_states:
        current_state = original_col_a
        new_col_a = current_state
        new_col_b = "Total"
    else:
        new_col_a = current_state
        new_col_b = original_col_a

    # Explicitly override first processed row’s first column as 'Place'
    if index == 0:
        new_col_a = "Place"

    # Build row: [State, Category, ...remaining columns]
    output_row = [new_col_a, new_col_b]

    for col_idx in range(1, len(row)):
        val = row[col_idx]
        if pd.isna(val) or str(val).lower() == "nan":
            output_row.append(None)
        else:
            val_str = str(val).strip()
            if val_str.endswith(".0") and val_str.replace(".0", "").isdigit():
                val_str = val_str.replace(".0", "")
            output_row.append(val_str)

    output_data.append(output_row)

# Define column names temporarily (won’t be saved in final CSV)
output_column_names = ["State", "Category"] + [f"Original_Col_{i}" for i in range(1, df.shape[1])]

# Create DataFrame
output_df = pd.DataFrame(output_data, columns=output_column_names)

# Replace all string 'nan' or NaN values with None
output_df = output_df.applymap(lambda x: None if x is None or str(x).lower() == "nan" else x)

# Save CSV without header so 'Place' stays as first row
output_df.to_csv(output_filepath, index=False, header=False)

print(f"✅ Successfully processed '{input_filepath}' and saved to '{output_filepath}' (no float .0 values, empty cells preserved)")

