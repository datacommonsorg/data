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

flags.DEFINE_string("spanner_project", "datcom-store", "Spanner Instance ID.")
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
flags.DEFINE_integer("spanner_batch_size", 1000, "Number of input rows to process as a single spanner batch update.")

# Map from input csv to spanner graph table columns
_DEFAULT_TABLE_CONFIG = {
    # Default variables for common StatVarObservation properties
    "DefaultVariables": {
        "measurementMethod": "",
        "provenance": "",
        "unit": "",
        "observationPeriod": "",
        "scalingFactor": "",
        "observationAbout": "",
        "footnote": "",
    },
    # Local variables reused in multiple tables
    "LocalVariables": {
        # "FacetId": "=crc32('{provenance}-{measurementMethod}-{observationPeriod}-{unit}-{scalingFactor}')",
        "FacetId": "{provenance}-{measurementMethod}-{observationPeriod}-{unit}-{scalingFactor}",
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
      #"ObservationAttribute": [{
      #    "id": "{StatVarObservation_id}",
      #    "date": "{observationDate}",
      #    "property": "footnote",
      #    "value": "{footnote}",
      #}],
    }
}


class SpannerStatVarObservationsUploader:
    """Upload statvar observations to Spanner.
    
    Uses a table config file to determine how to map input CSV columns to Spanner tables.
    The table config file is a JSON file with the following structure:
    {
        "DefaultVariables": {
            # List of default property:values for each input row
            "variableMeasured": "",
            "provenance": "",
            "unit": "",
            "observationPeriod": "",
            "scalingFactor": "",
        },
        "LocalVariables": {
            # Additional local varaiables computed form teh input row used in tables
            "FacetId": "=crc32('{provenance}-{measurementMethod}-{observationPeriod}-{unit}-{scalingFactor}')",
        },
        "SpannerTables": {
            # Mappings per spanner table, in order of insertion.
            # Each mapping can be a single dict or a list of dicts for tables with multiple rows per input row.
            # A variable is also created for each properoty in each table in the form {TableName}_{PropertyName}
            # This can be referenced in other tables using {<TableName>_<PropertyName>}
            "TimeSeries": {
                "id": "{variableMeasured};{donor};{recipient};{FacetId}",
                "variable_measured": "{variableMeasured}",
                "provenance": "{provenance}",
            },
            "TimeSeriesAttribute": [
                {
                    "id": "{TimeSeries_id}",
                    "property": "facetId",
                    "value": "{provenance};{donor};{recipient};{unit};{observationPeriod};{measurementMethod}",
                },
                {
                    "id": "{TimeSeries_id}",
                    "property": "importName",
                    "value": "{provenance}",
                },
                {
                    "id": "{TimeSeries_id}",
                    "property": "observationAbout",
                    "value": "{observationAbout}",
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
                {
                    "id": "{TimeSeries_id}",
                    "property": "observationPeriod",
                    "value": "{observationPeriod}",
                },
                {
                    "id": "{TimeSeries_id}",
                    "property": "scalingFactor",
                    "value": "{scalingFactor}",
                }
            ],
            "StatVarObservation": {
                "id": "{TimeSeries_id}",
                "date": "{observationDate}",
                "value": "{value}",
            },
            "ObservationAttribute": [
                {
                    "id": "{StatVarObservation_id}",
                    "date": "{observationDate}",
                    "property": "errorMargin",
                    "value": "{errorMargin}",
                },
                {
                    "id": "{StatVarObservation_id}",
                    "date": "{observationDate}",
                    "property": "footnote",
                    "value": "{footnote}",
                },
            ],
        }
    }
    """

    def __init__(self,
                 project_id,
                 instance_id,
                 database_id,
                 table_config_file: str = "",
                 default_values: list = [],
                 batch_size: int = 1000,
                 dry_run: bool = False,
                 counters=None):
        self._project_id = project_id
        self._instance_id = instance_id
        self._database_id = database_id
        self._spanner_batch_size = batch_size
        self._table_config_file = table_config_file
        self._default_values = {}
        if isinstance(default_values, str):
            default_values = default_values.split(',')
        if default_values:
            # Parse default values as prop=value
            for default_value in default_values:
                key, value = default_value.split("=", 1)
                self._default_values[key.strip()] = value.strip()
        self._spanner_client = spanner.Client(project=self._project_id)
        self._instance = self._spanner_client.instance(instance_id)
        self._database = self._instance.database(database_id)
        self._counters = counters or Counters()
        self._dry_run = dry_run
        self._table_config = None
        self.load_spanner_config(self._table_config_file)

        # Cache of keys already inserted into spanner
        self._inserted_keys = set()
        logging.info(f'Created spanner uploader for {instance_id}:{database_id} with table config: {self._table_config}')

    def load_spanner_config(self, table_config_file:str) -> dict:
        if table_config_file:
            with file_util.FileIO(table_config_file, "r") as f:
                self._table_config = json.load(f)
        else:
            self._table_config = _DEFAULT_TABLE_CONFIG
        self._table_config_name = table_config_file
        return self._table_config


    def _get_default_variables(self, row: dict = None) -> dict:
        def_vars = self._table_config.get("DefaultVariables", {})
        def_vars.update(self._default_values)
        if row:
          def_vars.update(row)
        return def_vars

    def _get_local_variables(self, pvs: dict):
        local_vars = self._table_config.get("LocalVariables", {})
        for var in local_vars.keys():
            value = _build_value_from_template(local_vars[var], pvs)
            pvs[var] = value
        return pvs

    def process_input_row(self, row: dict, batch):
        """Process a single row from the input CSV and generate Spanner mutations.
        
        Args:
            row: A dictionary representing a single row from the input CSV.
        
        Returns:
            A list of Spanner mutations.
        """
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
                # Handle list of templates for the same table
                table_row = []
                for index, tpl in enumerate(table_cfg):
                    sub_table_row = {}
                    for col in tpl.keys():
                        template = tpl[col]
                        value = _build_value_from_template(template, pvs)
                        if value:
                            sub_table_row[col] = value
                            pvs_key = f'{table}_{col}'
                            if pvs_key in pvs:
                                pvs_key = f'{table}_{col}_{index}'
                            pvs[pvs_key] = value
                    table_row.append(sub_table_row)
            mutations.append((table, table_row))
        logging.debug(f'Generated table from {row}: {mutations}')
        self._counters.add_counter('spanner-mutations-generated', 1)
        return self._insert_spanner_mutations(batch, mutations, row)

    def _insert_spanner_mutations(self, batch, mutations, input_row: dict) -> int:
        """Insert mutations into Spanner.

        Args:
            mutations: List of mutations to insert.
            input_row: Input row from the CSV.

        Returns:
            Number of mutations inserted.
        """
        num_mutations = 0
        if self._dry_run:
          return num_mutations
        for table, table_row in mutations:
            if isinstance(table_row, list):
                for row in table_row:
                    if self._insert_spanner_batch_row(batch, table, row):
                        num_mutations += len(row.keys())
            else:
                if self._insert_spanner_batch_row(batch, table, table_row):
                    num_mutations += len(table_row.keys())
        return num_mutations

    def _insert_spanner_batch_row(self, batch, table:str, table_row:dict) -> bool:
        """Insert a single row into the batch.

        Args:
            batch: Batch to insert into.
            table: Table name.
            table_row: Row to insert.

        Returns:
            True if the row was inserted, False otherwise.
        """
        key = _build_key(table, table_row)
        if key in self._inserted_keys:
            self._counters.add_counter(
                f'spanner-inserts-skipped-{table}', 1)
            return False
        self._inserted_keys.add(key)
        batch.insert(table=table,
                     columns=table_row.keys(),
                     values=[table_row.values()])
        self._counters.add_counter(f'spanner-rows-inserted-{table}', 1)
        return True


    def process_input_file(self, input_file: str) -> int:
        """Process an input file and insert mutations into Spanner.

        Args:
            input_file: Input file to process.

        Returns:
            Number of mutations inserted into Spanner tables.
        """
        input_files = file_util.file_get_matching(input_file)
        num_mutations = 0
        for infile in input_files:
            self._counters.add_counter('spanner-input-files', 1)
            with file_util.FileIO(infile, 'r') as f:
                estimated_rows = file_util.file_estimate_num_rows(infile)
                self._counters.add_counter('total', estimated_rows)
                logging.info(f'Processing input file: {infile} with estimated rows: {estimated_rows}')
                reader = csv.DictReader(f)
                batch_count = 0
                while self.process_input_batch(reader):
                  batch_count += 1
                  self._counters.add_counter('spanner-batch-count', 1)
                  logging.info(f'Processed batch:{batch_count} of {self._spanner_batch_size} rows for {infile}')
                logging.info(f'Processed input file: {infile} in {batch_count} batches')
        if not input_files:
            # Process an empty row for any default variables
            num_mutations += self.process_input_row({}, None)
            self._counters.add_counter('processed', 1)
        logging.info(
            f'Added {num_mutations} rows from {len(input_files)} files to spanner database {self._instance_id}.{self._database_id}'
        )


    def process_input_batch(self, csv_reader) -> bool:
        """Process a batch of inputs from a file.

        Returns:
          True if the input is not completely processed and can be called again.
        """
        num_mutations = 0
        with self._database.batch() as batch:
            num_input_rows = 0
            while num_input_rows < self._spanner_batch_size:
                row = next(csv_reader, None)
                if row is None:
                  # End of the input.
                  return False
                for prop in row.keys():
                    row[prop] = mcf_file_util.strip_namespace(row[prop])
                num_mutations += self.process_input_row(row, batch)
                num_input_rows += 1
                self._counters.add_counter('processed', 1)
        return True

    def delete_statvar_observations(self):
        """Delete data from all tables for a given provenance."""
        pvs = self._get_default_variables()
        provenance = pvs.get('provenance')
        if not self._dry_run:
            for table, template in self._table_config.get("SpannerTables", {}).items():
                if 'provenance' in template:
                    row_ct = self._database.execute_partitioned_dml(
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

def _build_key(table:str, table_row:dict) -> int:
    """Build a key for a table row."""
    return hash(tuple(table_row.values()))

def spanner_upload_statvar_observations(project, instance_id, database_id,
                                        table_config_file, default_values,
                                        input_file, delete, batch_size, dry_run):
    uploader = SpannerStatVarObservationsUploader(project,instance_id, database_id,
                                                  table_config_file,
                                                  default_values, batch_size, dry_run)
    if delete:
        uploader.delete_statvar_observations()
    if input_file:
        uploader.process_input_file(input_file)
    return uploader._counters


def main(_):
    if _FLAGS.spanner_debug:
        logging.set_verbosity(logging.DEBUG)
    counters = spanner_upload_statvar_observations(
        _FLAGS.spanner_project,
                                        _FLAGS.spanner_instance_id,
                                        _FLAGS.spanner_database_id,
                                        _FLAGS.spanner_table_config_file,
                                        _FLAGS.spanner_default_values,
                                        _FLAGS.spanner_input_file,
                                        _FLAGS.spanner_delete,
                                        _FLAGS.spanner_batch_size,
                                        _FLAGS.dry_run)
    counters.print_counters()


if __name__ == "__main__":
    app.run(main)
