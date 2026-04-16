import csv
import json
import os
import sys

from google.cloud import spanner

from absl import app
from absl import flags
from absl import logging

_FLAGS = flags.FLAGS

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPT_DIR)
_DATA_DIR = os.path.dirname(os.path.dirname(_SCRIPT_DIR))
sys.path.append(_DATA_DIR)
sys.path.append(os.path.join(_DATA_DIR, 'util'))
sys.path.append(os.path.join(_DATA_DIR, 'tools', 'statvar_importer'))

from counters import Counters
from eval_functions import evaluate_statement

import file_util
import mcf_file_util

flags.DEFINE_string("spanner_instance_id", "dc-kg-test", "Spanner Instance ID.")
flags.DEFINE_string("spanner_database_id", "dc_graph_2026_01_27",
                    "Spanner Database ID.")
flags.DEFINE_string("spanner_input_file", "",
                    "Input file with observations to be uploaded.")
flags.DEFINE_string("spanner_table_config_file", "",
                    "Table config file and input column mappings")
flags.DEFINE_list("spanner_default_values", [],
                  "Default list of property=values")
flags.DEFINE_boolean("dry_run", False, "Dry run mode.")
flags.DEFINE_boolean("spanner_debug", False, "Spanner debug mode.")
flags.DEFINE_boolean("spanner_delete", False, "Delete data from Spanner.")

# Map from input csv to spanner graph table columns
_DEFAULT_TABLE_CONFIG = {
    # Default variables for common StatVarObservation properties
    "DefaultVariables": {
        "measurementMethod": "",
        "provenance": "",
        "unit": "",
        "observationPeriod": "",
        "scalingFactor": "",
    },
    # Local variables reused in multiple tables
    "LocalVariables": {
        "FacetId": "=crc32('{provenance}-{measurementMethod}-{observationPeriod}-{unit}-{scalingFactor}')",
    },

    "SpannerTables": {
    # TimeSeries Table with the schema:
    #   id STRING(1024) NOT NULL,
    #   variable_measured STRING(1024) NOT NULL,
    #   provenance STRING(1024) NOT NULL,
    "TimeSeries": {
        "id":
            "{variableMeasured};{donor};{recipient};{FacetId}",
        "variable_measured":
            "{variableMeasured}",
        "provenance":
            "{provenance}",
    },
    # TimeSeriesAttribute Table with facet properties
    # id STRING(1024) NOT NULL,
    # property STRING(1024) NOT NULL,
    # value STRING(1024) NOT NULL,
    "TimeSeriesAttribute": [
        {
            "id":
                "{TimeSeries_id}",
            "property":
                "facetId",
            "value":
                "{provenance};{donor};{recipient};{unit};{observationPeriod};{measurementMethod}",
        },
        {
            "id": "{TimeSeries_id}",
            "property": "importName",
            "value": "{provenance}",
        },
        {
            "id": "{TimeSeries_id}",
            "property": "recipient",
            "value": "{recipient}",
        },
        {
            "id": "{TimeSeries_id}",
            "property": "donor",
            "value": "{donor}",
        },
        {
            "id": "{TimeSeries_id}",
            "property": "measurementMethod",
            "value": "{measurementMethod}",
        },
        {
            "id": "{TimeSeries_id}",
            "property": "unit",
            "value": "{unit}",
        },
    ],
    # StatVarObservation
    #   id STRING(1024) NOT NULL,
    #   date STRING(32) NOT NULL,
    #   value STRING(1024) NOT NULL,
    "StatVarObservation": {
        "id": "{TimeSeries_id}",
        "date": "{observationDate}",
        "value": "{value}",
    },

    # ObservationAttribute (
    #   id STRING(1024) NOT NULL,
    #   date STRING(32) NOT NULL,
    #   property STRING(1024) NOT NULL,
    #   value STRING(1024) NOT NULL,
    "ObservationAttribute": [{
        "id": "{StatVarObservation_id}",
        "date": "{observationDate}",
        "property": "footnote",
        "value": "{footnote}",
    },],
    }
}


class SpannerStatVarObservationsUploader:

    def __init__(self,
                 instance_id,
                 database_id,
                 table_config_file: str = "",
                 default_values: list = [],
                 dry_run: bool = False,
                 counters=None):
        self._instance_id = instance_id
        self._database_id = database_id
        self._table_config_file = table_config_file
        self._default_values = {}
        if isinstance(default_values, str):
            default_values = default_values.split(',')
        if default_values:
            # Parse default values as prop=value
            for default_value in default_values:
                key, value = default_value.split("=")
                self._default_values[key.strip()] = value.strip()
        self._spanner_client = spanner.Client()
        self._instance = self._spanner_client.instance(instance_id)
        self._database = self._instance.database(database_id)
        self._counters = counters or Counters()
        self._dry_run = dry_run
        self._table_config = None
        self.load_spanner_config(self._table_config_file)

    def load_spanner_config(self, table_config_file):
        if table_config_file:
            with open(table_config_file, "r") as f:
                self._table_config = json.load(f)
        else:
            self._table_config = _DEFAULT_TABLE_CONFIG


    def _get_default_variables(self, row: dict ):
        def_vars = self._table_config.get("DefaultVariables", {})
        def_vars.update(self._default_values)
        def_vars.update(row)
        return def_vars

    def _get_local_variables(self, pvs: dict):
        local_vars = self._table_config.get("LocalVariables", {})
        for var in local_vars.keys():
            value = _build_value_from_template(local_vars[var], pvs)
            pvs[var] = value
        return pvs

    def process_input_row(self, row: dict):
        """Process a single row from the input CSV and generate Spanner mutations."""
        mutations = []
        pvs = self._get_default_variables(row)
        pvs = self._get_local_variables(pvs)

        # Generate all table columns values from the input row
        self._counters.add_counter('spanner-input-rows', 1)
        spanner_tables = self._table_config.get("SpannerTables", {})
        for table, table_cfg in spanner_tables.items():
            # Generate mutation per table from the input row
            table_row = {}
            if isinstance(table_cfg, dict):
                for col in list(table_cfg.keys()):
                    template = table_cfg[col]
                    if isinstance(template, str):
                        value = _build_value_from_template(template, pvs)
                        if value:
                            table_row[col] = value
                        pvs[f'{table}_{col}'] = value
            elif isinstance(table_cfg, list):
                table_row = []
                for index, tpl in enumerate(table_cfg):
                    sub_table_row = {}
                    for col in tpl.keys():
                        template = tpl[col]
                        value = _build_value_from_template(template, pvs)
                        if value:
                            sub_table_row[col] = value
                            pvs_key = f'{table}{col}'
                            if pvs_key in pvs:
                                pvs_key = f'{table}_{col}_{index}'
                        pvs[pvs_key] = value
                    table_row.append(sub_table_row)
            mutations.append((table, table_row))
        logging.debug(f'Generated table from {row}: {mutations}')
        self._counters.add_counter('spanner-mutations-generated', 1)

        num_mutations = 0
        if not self._dry_run:
            with self.database.batch() as batch:
                for table, table_row in mutations:
                    if isinstance(table_row, list):
                        for row in table_row:
                            batch.insert(table=table,
                                         columns=row.keys(),
                                         values=[row.values()])
                            num_mutations += len(row.keys())
                        self._counters.add_counter(
                            f'spanner-rows-inserted-{table}', 1)
                else:
                    batch.insert(table=table,
                                 columns=table_row.keys(),
                                 values=[table_row.values()])
                    num_mutations += len(table_row.keys())
                    self._counters.add_counter(f'spanner-rows-inserted-{table}',
                                               1)
        return num_mutations

    def process_input_file(self, input_file: str):
        input_files = file_util.file_get_matching(input_file)
        num_mutations = 0
        for infile in input_files:
            self._counters.add_counter('spanner-input-files', 1)
            logging.info(f'Processing input file: {infile}')
            with file_util.FileIO(infile, 'r') as f:
                self._counters.add_counter(
                    'total', file_util.file_estimate_num_rows(infile))
                reader = csv.DictReader(f)
                for row in reader:
                    for prop in row.keys():
                        row[prop] = mcf_file_util.strip_namespace(row[prop])
                    num_mutations += self.process_input_row(row)
                    self._counters.add_counter('processed', 1)
        logging.info(
            f'Added {num_mutations} rows from {len(input_files)} files to spanner database {self._instance_id}.{self._database_id}'
        )

    def delete_statvar_observations(self):
        """Delete data from all tables for a given provenance."""
        pvs = self._get_default_variables()
        provenance = pvs.get('provenance')
        if not self._dry_run:
            for table, template in self._table_config.get("SpannerTables", {}).items():
                if 'provenance' in template:
                    row_ct = self.database.execute_partitioned_dml(
                        f"DELETE FROM {table} WHERE provenance = '{provenance}'"
                    )
                    logging.info(f"Bulk deleted {row_ct} records from {table}.")
                    self._counters.add_counter(f'spanner-rows-deleted-{table}', row_ct)
        else:
            logging.info(f"Dry run: would have deleted data from {len(self._table_config.get("SpannerTables", {}))} tables.")


def _build_value_from_template(template: str, row: dict) -> str:
    """Build a value from a template string and a row dictionary."""
    try:
        if template.startswith('='):
            variable, value = evaluate_statement(template[1:], row)
            row[variable] = value
            return value
        return template.format(**row)
    except KeyError as e:
        logging.error(f"KeyError: {e} in template: {template}, row: {row}")
        raise e


def spanner_upload_statvar_observations(instance_id, database_id,
                                        table_config_file, default_values,
                                        input_file, delete, dry_run):
    uploader = SpannerStatVarObservationsUploader(instance_id, database_id,
                                                  table_config_file,
                                                  default_values, dry_run)
    if delete:
        uploader.delete_statvar_observations()
    if input_file:
        uploader.process_input_file(input_file)
    return uploader._counters


def main(_):
    if _FLAGS.spanner_debug:
        logging.set_verbosity(logging.DEBUG)
    spanner_upload_statvar_observations(_FLAGS.spanner_instance_id,
                                        _FLAGS.spanner_database_id,
                                        _FLAGS.spanner_table_config_file,
                                        _FLAGS.spanner_default_values,
                                        _FLAGS.spanner_input_file,
                                        _FLAGS.spanner_delete,
                                        _FLAGS.dry_run)


if __name__ == "__main__":
    app.run(main)
