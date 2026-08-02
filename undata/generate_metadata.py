import os
import csv
import glob
import argparse
from pathlib import Path

# Mapping of data columns to their respective codelist files
COLUMN_TO_CL = {
    "SERIES": "CL_SERIES.csv",
    "GEOGRAPHY": "CL_GEOGRAPHY.csv",
    "AGE": "CL_AGE.csv",
    "SEX": "CL_SEX.csv",
    "EDUCATION_LEVEL": "CL_EDUCATION_LEVEL.csv",
    "WEALTH_QUANTILE": "CL_WEALTH_QUANTILE.csv",
    "URBANIZATION": "CL_URBANIZATION.csv",
    "UNIT_MEASURE": "CL_UNIT_MEASURE.csv",
    "UNIT_MULT": "CL_UNIT_MULT.csv",
    "CENSORED_VALUE_TYPE": "CL_CENSORED_VALUE_TYPE.csv",
    "FREQUENCY": "CL_FREQUENCY.csv",
    "OBSERVATION_STATUS": "CL_OBSERVATION_STATUS.csv",
    "ICT_SKILL": "CL_ICT_SKILL.csv",
    "OCCUPATION": "CL_OCCUPATION.csv",
    "ANTENATAL_CARE_VISITS": "CL_ANTENATAL_CARE_VISITS.csv",
    "ECONOMIC_ACTIVITY": "CL_ECONOMIC_ACTIVITY.csv",
    "GHE_CAUSE": "CL_GHE_CAUSE.csv",
    "REP_HEALTH_DECISION": "CL_REP_HEALTH_DECISION.csv",
    "CHILDREN_UNDER6": "CL_CHILDREN_UNDER6.csv",
    "HOUSEHOLD_COMPOSITION": "CL_HOUSEHOLD_COMPOSITION.csv",
    "GENDER_EQ_AREA": "CL_GENDER_EQ_AREA.csv",
    "PARENTAL_CONSENT_STATUS": "CL_PARENTAL_CONSENT_STATUS.csv",
    "STATUS_IN_EMPLOYMENT": "CL_STATUS_IN_EMPLOYMENT.csv",
    "GOVERNMENT_LEVEL": "CL_GOVERNMENT_LEVEL.csv",
    "VALUE_CATEGORY": "CL_VALUE_CATEGORY.csv",
    "ILO_CONVENTION": "CL_ILO_CONVENTION.csv",
    "TYPE_OF_QUOTA": "CL_TYPE_OF_QUOTA.csv",
    "DISABILITY_STATUS": "CL_DISABILITY_STATUS.csv",
    "TIME_USE_ACTIVITY": "CL_TIME_USE_ACTIVITY.csv",
    "VIOLENCE_TYPE": "CL_VIOLENCE_TYPE.csv",
    # Additional SDG Columns
    "PRODUCT": "CL_PRODUCT.csv",
    "NATURE": "CL_NATURE.csv",
    "REPORTING_LEVEL": "CL_REPORTING_LEVEL.csv",
    "VALUE_TYPE": "CL_VALUE_TYPE.csv",
    "TIME_DETAIL": "CL_TIME_DETAIL.csv",
    "SOURCE": "CL_SOURCE.csv",
    "BASE_PERIOD": "CL_BASE_PERIOD.csv",
    "BIOCLIMATIC_BELT": "CL_BIOCLIMATIC_BELT.csv",
    "CHLOROPHYLL_A_CONCENTRATION_FREQ": "CL_CHLOROPHYLL_A_CONCENTRATION_FREQ.csv",
    "CLIMATE_FINANCIAL_SUPPORT": "CL_CLIMATE_FINANCIAL_SUPPORT.csv",
    "DEVIATION_LEVEL": "CL_DEVIATION_LEVEL.csv",
    "FISCAL_INTERVENTION_STAGE": "CL_FISCAL_INTERVENTION_STAGE.csv",
    "FOOD_WASTE_SECTOR": "CL_FOOD_WASTE_SECTOR.csv",
    "GEOGRAPHY_COUNTERPART": "CL_GEOGRAPHY.csv",
    "GOVERNMENT_NAME": "CL_GOVERNMENT_NAME.csv",
    "GROUNDS_OF_DISCRIMINATION": "CL_GROUNDS_OF_DISCRIMINATION.csv",
    "IHR_CAPACITY": "CL_IHR_CAPACITY.csv",
    "ILLICIT_FINANCIAL_FLOWS": "CL_ILLICIT_FINANCIAL_FLOWS.csv",
    "INTERNATIONAL_ORGANIZATION": "CL_INTERNATIONAL_ORGANIZATION.csv",
    "INTERNET_SPEED": "CL_INTERNET_SPEED.csv",
    "LAND_COVER": "CL_LAND_COVER.csv",
    "LETHAL_INSTRUMENT": "CL_LETHAL_INSTRUMENT.csv",
    "LEVEL_STATUS": "CL_LEVEL_STATUS.csv",
    "LOWER_BOUND": "CL_LOWER_BOUND.csv",
    "MARINE_SPATIAL_PLAN": "CL_MARINE_SPATIAL_PLAN.csv",
    "MIGRATORY_STATUS": "CL_MIGRATORY_STATUS.csv",
    "NATURE": "CL_NATURE.csv",
    "NUTRIENT_LOADING": "CL_NUTRIENT_LOADING.csv",
    "OFDI_SCHEME": "CL_OFDI_SCHEME.csv",
    "PARLIAMENTARY_COMMITTEES": "CL_PARLIAMENTARY_COMMITTEES.csv",
    "POLICY_DOMAINS": "CL_POLICY_DOMAINS.csv",
    "POLICY_INSTRUMENTS": "CL_POLICY_INSTRUMENTS.csv",
    "POPULATION_GROUP": "CL_POPULATION_GROUP.csv",
    "PRICE_LEVEL_SEVERITY": "CL_PRICE_LEVEL_SEVERITY.csv",
    "RENEWABLE_TECHNOLOGY": "CL_RENEWABLE_TECHNOLOGY.csv",
    "REPORT_ORDINAL": "CL_REPORT_ORDINAL.csv",
    "REQUIREMENT_LEVEL": "CL_REQUIREMENT_LEVEL.csv",
    "SERVICE_ATTRIBUTE": "CL_SERVICE_ATTRIBUTE.csv",
    "SKILL": "CL_SKILL.csv",
    "SUBSTANCE": "CL_SUBSTANCE.csv",
    "TRANSPORT_MODE": "CL_TRANSPORT_MODE.csv",
    "UPPER_BOUND": "CL_UPPER_BOUND.csv",
    "WASTE_TREATMENT": "CL_WASTE_TREATMENT.csv",
}

def load_codelists(cl_dir):
    """Loads all reviewed codelists into a nested dictionary."""
    master_map = {}
    print(f"Loading codelists from {cl_dir}...")
    for column, cl_file in COLUMN_TO_CL.items():
        cl_path = os.path.join(cl_dir, cl_file)
        # Also check for files with 'processed_' prefix
        if not os.path.exists(cl_path):
            cl_path_processed = os.path.join(cl_dir, f"processed_{cl_file}")
            if os.path.exists(cl_path_processed):
                cl_path = cl_path_processed
            else:
                print(f"Warning: Codelist file {cl_file} (or processed_{cl_file}) not found for column {column}")
                continue
        
        try:
            with open(cl_path, mode='r', encoding='utf-8') as f:
                reader = csv.reader(f)
                header = next(reader)
                
                pv_start_idx = -1
                for i, col_name in enumerate(header):
                    if col_name.strip().upper() == 'DC_PV_PAIR':
                        pv_start_idx = i
                        break
                
                if pv_start_idx == -1:
                    print(f"Warning: DC_PV_PAIR column not found in {cl_file}")
                    continue
                
                col_map = {}
                for row in reader:
                    if not row or len(row) <= 1:
                        continue
                    
                    code = row[1] 
                    raw_parts = [p.strip() for p in row[pv_start_idx:] if p.strip()]
                    pv_pairs = []
                    for j in range(0, len(raw_parts), 2):
                        if j + 1 < len(raw_parts):
                            pv_pairs.append(f"{raw_parts[j]}:{raw_parts[j+1]}")
                        else:
                            pv_pairs.append(raw_parts[j])
                    
                    if code:
                        col_map[code] = [",".join(pv_pairs)] if pv_pairs else []
                
                master_map[column] = {
                    "codelist_map": col_map,
                    "additional_headers": ["DC_PV_PAIR"]
                }
                
        except Exception as e:
            print(f"Error loading {cl_file}: {e}")
            
    return master_map

def generate_metadata(cl_dir, data_dir, metadata_dir):
    """Generates a metadata dictionary for each data file."""
    master_map = load_codelists(cl_dir)
    os.makedirs(metadata_dir, exist_ok=True)
    
    data_files = glob.glob(os.path.join(data_dir, "*.csv"))
    print(f"Found {len(data_files)} data files in {data_dir}.")
    
    for data_path in data_files:
        filename = Path(data_path).stem
        output_path = os.path.join(metadata_dir, f"{filename}_metadata.csv")
        
        print(f"Processing {filename}...")
        
        try:
            with open(data_path, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                # Include all columns that are in COLUMN_TO_CL
                relevant_cols = [c for c in reader.fieldnames if c in COLUMN_TO_CL]
                
                if not relevant_cols:
                    print(f"No mappable columns found in {filename}")
                    continue
                
                unique_values = {col: set() for col in relevant_cols}
                for row in reader:
                    for col in relevant_cols:
                        val = row.get(col)
                        if val:
                            unique_values[col].add(val)
                
                metadata_rows = []
                output_fieldnames = ["column_name", "value"]
                seen_additional_headers = set()
                
                # First pass to get all additional headers from master_map
                for col in relevant_cols:
                    if col in master_map:
                        current_codelist_headers = master_map[col]["additional_headers"]
                        for header_name in current_codelist_headers:
                            if header_name not in seen_additional_headers:
                                output_fieldnames.append(header_name)
                                seen_additional_headers.add(header_name)
                
                # If DC_PV_PAIR not in seen_additional_headers, add it as a default
                if "DC_PV_PAIR" not in seen_additional_headers:
                    output_fieldnames.append("DC_PV_PAIR")

                for col in relevant_cols:
                    if col in master_map:
                        codelist_info = master_map[col]
                        codelist_map = codelist_info["codelist_map"]
                        current_codelist_headers = codelist_info["additional_headers"]
                    else:
                        codelist_map = {}
                        current_codelist_headers = ["DC_PV_PAIR"]

                    for val in sorted(unique_values[col]):
                        pv_parts = codelist_map.get(val)
                        
                        row_dict = {
                            "column_name": col,
                            "value": val,
                        }
                        
                        if pv_parts and pv_parts[0].strip():
                            for i, header_name in enumerate(current_codelist_headers):
                                if i < len(pv_parts):
                                    row_dict[header_name] = pv_parts[i]
                        else:
                            for header_name in current_codelist_headers:
                                row_dict[header_name] = ""
                        
                        # Fill in missing fields with empty string
                        for field in output_fieldnames:
                            if field not in row_dict:
                                row_dict[field] = ""
                        
                        metadata_rows.append(row_dict)
                
                if metadata_rows:
                    with open(output_path, mode='w', encoding='utf-8', newline='') as out_f:
                        writer = csv.DictWriter(out_f, fieldnames=output_fieldnames)
                        writer.writeheader()
                        writer.writerows(metadata_rows)
                    print(f"  Generated: {output_path}")
                else:
                    print(f"  No valid mappings found for {filename}")
                
        except Exception as e:
            print(f"Error processing {filename}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate metadata CSVs from data CSVs and codelists.")
    parser.add_argument("--cl_dir", default="undata/cl_reviewed", help="Directory containing codelist CSVs.")
    parser.add_argument("--data_dir", default="undata/SDG/data", help="Directory containing data CSVs.")
    parser.add_argument("--metadata_dir", default="undata/SDG/metadata", help="Directory to save generated metadata CSVs.")
    
    args = parser.parse_args()
    generate_metadata(args.cl_dir, args.data_dir, args.metadata_dir)

