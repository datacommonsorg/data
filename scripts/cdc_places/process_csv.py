"""Processing script for CDC PLACES data."""

import argparse
import contextlib
import csv
import re
import sys

import progressbar


class StatisticalVariable(object):
    """A Stastical Variable created from the CDC PLACES dataset."""

    def __init__(self, measure_id, data_value_unit):
        self.measure_id = measure_id
        self.data_value_unit = data_value_unit

    @classmethod
    def from_row_dict(cls, row_dict):
        return cls(row_dict["MeasureId"], row_dict["Data_Value_Unit"])

    @property
    def age_range(self):
        """Return the variable's age range as a tuple (min, max) where both
        ends are inclusive.

        None indicates a missing min or max value, e.g. "18 and over" is
        indicated by `(18, None)`.
        """
        measure_id_to_age_range = {
            "ACCESS2": (18, 64),
            "ARTHRITIS": (18, None),
            "BINGE": (18, None),
            "BPHIGH": (18, None),
            "BPMED": (18, None),
            "CANCER": (18, None),
            "CASTHMA": (18, None),
            "CERVICAL": (21, 65),
            "CHD": (18, None),
            "CHECKUP": (18, None),
            "CHOLSCREEN": (18, None),
            "COLON_SCREEN": (50, 75),
            "COPD": (18, None),
            "COREM": (65, None),
            "COREW": (65, None),
            "CSMOKING": (18, None),
            "DENTAL": (18, None),
            "DIABETES": (18, None),
            "HIGHCHOL": (18, None),
            "KIDNEY": (18, None),
            "LPA": (18, None),
            "MAMMOUSE": (50, 74),  # NOTE: Currently stored as 50-75
            "MHLTH": (18, None),
            "OBESITY": (18, None),
            "PHLTH": (18, None),
            "SLEEP": (18, None),
            "STROKE": (18, None),
            "TEETHLOST": (65, None),
        }
        return measure_id_to_age_range[self.measure_id]

    @property
    def gender(self):
        if self.measure_id in ("CERVICAL", "COREW", "MAMMOUSE"):
            return "Female"
        elif self.measure_id == "COREM":
            return "Male"
        else:
            return None

    @property
    def health_behavior(self):
        """Returns the name of the variable's associated health behavior."""

        measure_id_to_health_behavior = {
            "BINGE": "BingeDrinking",
            "CSMOKING": "Smoking",
            "LPA": "PhysicalInactivity",
            "OBESITY": "Obesity",
            "SLEEP": "SleepLessThan7Hours",
        }
        return measure_id_to_health_behavior.get(self.measure_id)

    @property
    def health_outcome(self):
        """Returns the name of the variable's associated health outcome."""

        measure_id_to_health_outcome = {
            "MHLTH": "MentalHealthNotGood",
            "BPHIGH": "HighBloodPressure",
            "BPMED": "HighBloodPressure",
            "CHD": "CoronaryHeartDisease",
            "HIGHCHOL": "HighCholesterol",
            "CANCER": "CancerExcludingSkinCancer",
            "KIDNEY": "ChronicKidneyDisease",
            "STROKE": "Stroke",
            "CASTHMA": "Asthma",
            "TEETHLOST": "AllTeethLoss",
            "ARTHRITIS": "Arthritis",
            "PHLTH": "PhysicalHealthNotGood",
            "COPD": "ChronicObstructivePulmonaryDisease",
            "DIABETES": "Diabetes",
        }
        return measure_id_to_health_outcome.get(self.measure_id)

    @property
    def health_prevention(self):
        """Returns the name of the variable's associated health prevention
        measure."""

        measure_id_to_health_prevention = {
            "ACCESS2": "NoHealthInsurance",
            "BPMED": "TakingBloodPressureMedication",
            "CERVICAL": "CervicalCancerScreening",
            "CHECKUP": "AnnualCheckup",
            "CHOLSCREEN": "CholesterolScreening",
            "COLON_SCREEN": "ColorectalCancerScreening",
            "COREM": "CorePreventiveServices",
            "COREW": "CorePreventiveServices",
            "DENTAL": "DentalVisit",
            "MAMMOUSE": "Mammography",
        }
        return measure_id_to_health_prevention.get(self.measure_id)

    def validate(self):
        """Runs sanity-check validations for the variable's data.

        Throws a ValueError exception on validation errors."""

        # Data Value Unit
        if self.data_value_unit != "%":
            raise ValueError("Unknown data value unit: " + self.data_value_unit)

        # Age
        age_range = self.age_range
        if not age_range:
            raise ValueError("Missing age range")
        if not age_range[0]:
            raise ValueError("Missing lower bound on age range")
        if age_range[1] and age_range[0] > age_range[1]:
            raise ValueError("Invalid age range: upper bound must be " +
                             ">= lower bound")

    @property
    def mcf_node(self):
        """Returns the value of the MCF `Node` key."""

        parts = ["Percent", "Person"]
        if self.age_range:
            start, end = self.age_range
            if not (start == 18 and end is None):
                if not end:
                    parts.append(f"{start}OrMoreYears")
                else:
                    parts.append(f"{start}To{end}Years")
        if self.gender:
            parts.append(self.gender)
        if self.health_behavior:
            parts.append(self.health_behavior)
        if self.health_outcome:
            parts.append("With" + self.health_outcome)
        if self.health_prevention:
            parts.append("Received" + self.health_prevention)
        return "dcid:" + "_".join(parts)

    @property
    def mcf_properties(self):
        """Returns a dictionary of the variable's MCF key-value pairs."""

        stat_var_node_kvs = {
            "Node": self.mcf_node,
            "typeOf": "dcs:StatisticalVariable",
            "populationType": "dcs:Person",
            "statType": "dcs:measuredValue",
            "measuredProperty": "dcs:percent",
        }

        if self.age_range:
            start, end = self.age_range
            stat_var_node_kvs["age"] = f"[Years {start or '-'} {end or '-'}]"
        if self.gender:
            stat_var_node_kvs["gender"] = f"dcs:{self.gender}"
        if self.health_behavior:
            stat_var_node_kvs["healthBehavior"] = "dcs:" + self.health_behavior
        if self.health_outcome:
            stat_var_node_kvs["healthOutcome"] = "dcs:" + self.health_outcome
        if self.health_prevention:
            stat_var_node_kvs["healthPrevention"] = \
                "dcs:" + self.health_prevention

        return stat_var_node_kvs


out_field_names = (
    "Year",
    # "StateAbbr",
    # "StateDesc",
    # "LocationName",
    # "DataSource",
    # "Category",
    # "Data_Value_Unit",
    # "Data_Value_Type",
    "Data_Value",
    # "Data_Value_Footnote_Symbol",
    # "Data_Value_Footnote",
    # "Low_Confidence_Limit",
    # "High_Confidence_Limit",
    # "TotalPopulation",
    # "Geolocation",
    # "LocationID",
    # "CategoryID",
    # "MeasureId",
    # "DataValueTypeID",
    "Latitude",
    "Longitude",
    "StatisticalVariable",
)


def preprocess_csv(args):
    """Runs the preprocess_csv subcommand.

    The command process the input CSV and generates an output CSV with the
    requisite columns to import into the Data Commons KG."""

    stat_var_names = {}
    with contextlib.closing(args.input) as input_file, \
            contextlib.closing(args.output) as output_file:
        line_count = sum(1 for _ in input_file)
        input_file.seek(0)
        reader = csv.DictReader(input_file)
        progress = progressbar.ProgressBar(max_value=line_count,
                                           redirect_stdout=True)
        writer = csv.DictWriter(output_file, fieldnames=out_field_names)
        writer.writeheader()
        for row_dict in reader:
            mid = row_dict["MeasureId"]
            if mid not in stat_var_names:
                sv = StatisticalVariable.from_row_dict(row_dict)
                stat_var_names[mid] = sv.mcf_node
            row_dict["StatisticalVariable"] = stat_var_names[mid]
            gl = row_dict["Geolocation"]
            m = re.search(r"^POINT \((\S+)\s(\S+)\)$", gl)
            row_dict["Latitude"] = m.group(1)
            row_dict["Longitude"] = m.group(2)
            writer.writerow({key: row_dict[key] for key in out_field_names})
            progress.update(reader.line_num)


def generate_stat_vars(args):
    """Runs the generate_stat_vars subcommand.

    The command processes the input CSV and generates StasticalVariable
    MCF for each measure found in the input file. The output can be written
    to a file or printed to stdout.

    If the number of measures/variables is known ahead of time, this command
    can short-circuit once `count` variables have been identified."""

    stat_vars = {}
    progress = progressbar.NullBar()
    with contextlib.closing(args.input) as input_file:
        if not args.count:
            line_count = sum(1 for _ in input_file)
            progress = progressbar.ProgressBar(max_value=line_count,
                                               redirect_stdout=True)
            input_file.seek(0)
        reader = csv.DictReader(input_file)
        for row_dict in reader:
            mid = row_dict["MeasureId"]
            if mid not in stat_vars:
                stat_vars[mid] = StatisticalVariable.from_row_dict(row_dict)
            progress.update(reader.line_num)
            if args.count and args.count == len(stat_vars):
                break

    nodes = []
    for sv in stat_vars.values():
        sv.validate()
        stat_var_node_kvs = sv.mcf_properties
        nodes.append("\n".join(
            f"{k}: {v}" for k, v in stat_var_node_kvs.items()))

    with contextlib.closing(args.output) as output_file:
        output_file.write("\n".join(n.strip() + "\n" for n in nodes))


def main():
    parser = argparse.ArgumentParser(description="Process CDC Places CSV")

    subparsers = parser.add_subparsers(dest="command")

    preprocess_csv_parser = subparsers.add_parser(
        "preprocess_csv",
        help="Preprocesses CSV file for import into Data Commons KG.")
    preprocess_csv_parser.add_argument("--input",
                                       required=True,
                                       type=argparse.FileType("r"),
                                       help="Path to input CSV file.")
    preprocess_csv_parser.add_argument("--output",
                                       required=True,
                                       type=argparse.FileType("w"),
                                       help="Path to output CSV file.")
    preprocess_csv_parser.set_defaults(func=preprocess_csv)

    generate_stat_vars_parser = subparsers.add_parser(
        "generate_stat_vars",
        help="Generates StatisticalVariable MCF nodes from input CSV file.")
    generate_stat_vars_parser.add_argument("--input",
                                           required=True,
                                           type=argparse.FileType("r"),
                                           help="Path to input CSV file.")
    generate_stat_vars_parser.add_argument(
        "--output",
        required=False,
        type=argparse.FileType("w"),
        default=sys.stdout,
        help="Path to MCF output file. If empty, prints to stdout.")
    generate_stat_vars_parser.add_argument(
        "--count",
        required=False,
        type=int,
        default=0,
        help="Number of StatisticalVariables to generate. Can be used " +
        "to avoid loading the entire CSV file if known ahead of time.")
    generate_stat_vars_parser.set_defaults(func=generate_stat_vars)

    args = parser.parse_args()
    if args.command:
        parser.error("A subcommand is required.")
        return

    args.func(args)


if __name__ == "__main__":
    main()
