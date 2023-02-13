import csv
import datacommons as dc
import os

from absl import app
from absl import flags
from dataclasses import dataclass
from typing import Dict, List, Tuple

GEO_ID_COLUMN = 'GEO_ID'
NUM_DCIDS_TO_QUERY = 50


@dataclass
class NewCSVColumn:
    name: str

    # format example: data.census.gov/table/EC1200A1:ESTAB?naics2012={0}&taxstat={1}&typop={2}
    format: str

    # ordered_csv_column_names example: ["NAICS2012", "TAXSTAT", "TYPOP"]
    # The order should correspond to the {0}, {1}, {2}, ... in the format string above.
    ordered_csv_column_names: List[str]


def _replace_ce_t_with_filename(line: str, csv_out_name: str) -> str:
    if "C:T" in line or "E:T" in line:
        return line.replace(":T", ":" + csv_out_name)
    return line


def _replace_t_with_T_path(line: str, T: str) -> str:
    return line.replace("T:", T + ":")


def _detect_opaque_mapping(line: str) -> str:
    return ("?" in line)


def _split_source_query_portions(input: str) -> Tuple[str, str]:
    portions = input.split("?")
    if len(portions) != 2:
        raise Exception(
            f"Exactly one '?' expected in variableMeasured line. Got: {input}")
    source_str = portions[0]
    opaque_portion = portions[1]

    return (source_str, opaque_portion)


# TODO: remove this function after adding censusGeoId as a property.
def _census_geoId_to_dcid(census_geoids: List[str]) -> Dict[str, str]:
    geoId_to_dcid = {}
    for census_geoId in census_geoids:
        if 'US' in census_geoId:
            dcid = census_geoId.split("US")[1]
            if not dcid:
                dcid = "country/USA"
            else:
                dcid = f"geoId/{dcid}"
            geoId_to_dcid.update({census_geoId: dcid})
    return geoId_to_dcid


def _get_places_not_found(census_geoids: List[str]) -> List[str]:
    geoId_to_dcids = _census_geoId_to_dcid(census_geoids)
    geoIds_not_found = []

    geo_ids = list(geoId_to_dcids.keys())
    for i in range(0, len(geo_ids), NUM_DCIDS_TO_QUERY):
        selected_geo_ids = geo_ids[i:i + NUM_DCIDS_TO_QUERY]
        selected_dcids = [geoId_to_dcids[g] for g in selected_geo_ids]
        res = dc.get_property_values(selected_dcids, 'name')
        for index in range(len(selected_dcids)):
            if not res[selected_dcids[index]]:
                geoIds_not_found.append(selected_geo_ids[index])
    return geoIds_not_found


def _get_geoId_column(input_csv_filepath: str) -> List[str]:
    geoIds = []
    with open(input_csv_filepath, 'r') as input_csv:
        csv_reader = csv.DictReader(input_csv)
        for row_dict in csv_reader:
            if GEO_ID_COLUMN not in row_dict.keys():
                return []
            geoIds.append(row_dict[GEO_ID_COLUMN])
    return geoIds


def _process_var_measured_new_column(
        var_measured_str: str,
        new_csv_columns: List[NewCSVColumn]) -> NewCSVColumn:
    # Example of line: "T:ESTAB?naics2012=C:T->NAICS2012&taxstat=C:T->TAXSTAT&typop=C:T->TYPOP"

    # Step 0: split on "?"
    (source_str,
     opaque_portion) = _split_source_query_portions(var_measured_str)
    source_str = source_str.replace("http://", "")
    source_str = source_str.replace(":", "/variable/")

    # Step 1: split on '&'
    query_format = source_str + "?"
    query_split = opaque_portion.split("&")
    num_params = len(query_split)

    ordered_csv_column_names = []
    index = 0
    for param_and_val in query_split:
        # Step 2: split on "="
        key_val_split = param_and_val.split("=")
        if len(key_val_split) != 2:
            raise Exception(
                f"Exactly one '=' expected in the key/val opaque mapping. Got: {param_and_val}"
            )
        key = key_val_split[0]
        col_name = key_val_split[1].replace("C:T->", "")

        ordered_csv_column_names.append(col_name)
        query_format += key + "="
        query_format += "{" + str(index) + "}"
        query_format += "&"

        index += 1

    if query_format[-1] == "&":
        query_format = query_format[:-1]

    # TODO: remove these checks when a better format for opaque mapping is agreed.
    query_format = query_format.replace("?", "__")
    query_format = query_format.replace("&", "++")
    query_format = query_format.replace("=", "--")

    # Verify that such a new column does not already exist.
    for new_col in new_csv_columns:
        if query_format == new_col.format:
            return new_col

    new_col = NewCSVColumn(
        name="new_col_" + str(len(new_csv_columns)),
        format=query_format,
        ordered_csv_column_names=ordered_csv_column_names,
    )

    new_csv_columns.append(new_col)
    return new_col


def _write_modified_csv(original_csv_path, output_csv_path,
                        new_cols: List[NewCSVColumn],
                        geo_ids_to_dcids: Dict[str, str],
                        geo_ids_not_found: List[str]) -> None:
    # Get a list of existing columns in the input CSV.
    csv_column_names = []
    with open(original_csv_path, 'r') as input_csv:
        csv_reader = csv.DictReader(input_csv)
        csv_row = next(csv_reader)

        csv_column_names = list(csv_row.keys())

    # Add the new column names to the list.
    for col in new_cols:
        csv_column_names.append(col.name)

    output_rows: List[Dict] = []
    row_counter = 0
    with open(original_csv_path, 'r') as input_csv:
        csv_reader = csv.DictReader(input_csv)

        for row_dict in csv_reader:
            row_counter += 1

            # The first row after the header is special because it contains
            # more column metadata (specific to Census) and it can be ignored.
            # TODO: this should be set in the etmcf file. Remomve this check
            # when the data start row number can be read from the etmc file.
            if row_counter < 2:
                continue

            # Exclude geoIds not found. If it exists, replace census geoId with dcid.
            if GEO_ID_COLUMN in row_dict:
                if row_dict[GEO_ID_COLUMN] in geo_ids_not_found:
                    # TODO: write all unprocessed rows to a separate output file.
                    print(
                        f"... geoId: {row_dict[GEO_ID_COLUMN]} does not exist in DC. Skipping input row # {row_counter} in file {original_csv_path}"
                    )
                    continue
                else:
                    row_dict[GEO_ID_COLUMN] = geo_ids_to_dcids[
                        row_dict[GEO_ID_COLUMN]]

            # To the row_dict, add the key/values corresponding to the new columns.
            for col in new_cols:
                vals = [row_dict[k] for k in col.ordered_csv_column_names]
                val_str = col.format.format(*vals)
                row_dict.update({col.name: val_str})

            output_rows.append(row_dict)

    with open(output_csv_path, 'w', newline='') as output_csv:
        writer = csv.DictWriter(output_csv, fieldnames=csv_column_names)
        writer.writeheader()
        for row_dict in output_rows:
            writer.writerow(row_dict)


def process_enhanced_tmcf(input_folder, output_folder, etmcf_filename,
                          input_csv_filename, output_tmcf_filename,
                          output_csv_filename) -> None:
    """Processed the enhanced TMCF file and input CSV. Produces the traditional TMCF and modified CSV."""
    if not os.path.exists(input_folder):
        raise Exception(
            f"input_folder should exist.\nInput Folder: {input_folder}")
    if not os.path.exists(output_folder):
        raise Exception(
            f"output_folder should exist.\nOutput Folder: {output_folder}")

    etmcf_filepath = os.path.join(input_folder, etmcf_filename + ".tmcf")
    input_csv_filepath = os.path.join(input_folder, input_csv_filename + ".csv")

    if not os.path.exists(etmcf_filepath):
        raise Exception(
            f"Enhanced TMCF file should exist.\nE_TMCF file: {etmcf_filepath}")
    if not os.path.exists(input_csv_filepath):
        raise Exception(
            f"Input CSV file should exist.\nInput CSV file: {input_csv_filepath}"
        )

    # If the input_csv_filename has the 'geoId' column, pre-process to get all geoIds which
    # do not yet exist in DC.
    geo_ids = _get_geoId_column(input_csv_filepath)
    geo_ids_to_dcids = _census_geoId_to_dcid(geo_ids)
    geo_ids_not_found = _get_places_not_found(geo_ids)

    # new_csv_columns is a list of new columns to add to produce the processed CSV.
    new_csv_columns: List[NewCSVColumn] = []

    T = ""
    data_files = ""
    tmcf_out = os.path.join(output_folder, output_tmcf_filename + ".tmcf")
    csv_out = os.path.join(output_folder, output_csv_filename + ".csv")

    # Process the enhanced TMCF to identify the new columns to be introduced in the csv.
    with open(etmcf_filepath, 'r') as etmcf, open(tmcf_out, 'w') as out_tmcf:
        lines = etmcf.readlines()

        output_started = False
        for line in lines:
            out_line = line
            # TODO: should check that "Namespace:" comes immediately before T= line.
            if line.startswith("Namespace:"):
                continue
            elif line.startswith("T="):
                T = line.split("=")[1].replace("\n", "")
                continue
            elif line.startswith("DATAFILES="):
                data_files = line.split("=")[1].replace("\n", "")
                continue
            elif line == "" or line == "\n":
                if not output_started:
                    continue

            # TODO: remove these checks after the footnotes are added as a property.
            if line.startswith("footnote"):
                continue

            # Reaching here means the traditional TMCF can now start
            output_started = True

            # Detect opaque mapping.
            if line.startswith("variableMeasured:") and _detect_opaque_mapping(
                    line):
                # Split on " " (space)
                line_split = line.split(" ")
                var_measured_str = _replace_t_with_T_path(line_split[1],
                                                          T).replace("\n", "")
                new_col = _process_var_measured_new_column(
                    var_measured_str, new_csv_columns)
                out_line = line_split[0] + " C:T->" + new_col.name + "\n"

            # If the line has 'geoId:', replace it with 'dcid:'
            out_line = out_line.replace("geoId:", "dcid:")

            # TODO: this should not be needed once the input files are fixed.
            if line.startswith("standardError:"):
                out_line = out_line.replace("standardError:", "stdError:")

            out_line = _replace_ce_t_with_filename(out_line,
                                                   output_csv_filename)
            out_tmcf.write(out_line)

    # Use the existing input CSV, the new_csv_columns list and maps of geoIds to DCIDs (for places)
    # and a list of geoIds not found to produce the processed (traditional) TMCF and corresponding CSV.
    _write_modified_csv(input_csv_filepath, csv_out, new_csv_columns,
                        geo_ids_to_dcids, geo_ids_not_found)