# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Unit tests for ET-layer StatVar aggregation (aggregator/)."""

import csv
import importlib.util
import json
import os
import sys
import tempfile
import unittest
from unittest import mock

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT_DIR = os.path.dirname(os.path.dirname(_SCRIPT_DIR))
for _p in [
        _SCRIPT_DIR,
        _ROOT_DIR,
        os.path.join(_ROOT_DIR, "util"),
        os.path.join(_ROOT_DIR, "tools", "import_differ"),
        os.path.join(_ROOT_DIR, "tools", "statvar_importer"),
]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import stat_var_aggregator
from tools.import_differ import bigquery_differ


def _load_aggregator_main():
    """Loads import-automation/aggregator/main.py as 'aggregator_main' without polluting sys.modules['main']."""
    mod_name = "aggregator_main"
    if mod_name in sys.modules:
        return sys.modules[mod_name]
    spec = importlib.util.spec_from_file_location(
        mod_name, os.path.join(_SCRIPT_DIR, "main.py"))
    module = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = module
    spec.loader.exec_module(module)
    return module


aggregator_main = _load_aggregator_main()

_SUMMARY_CSV_HEADER = [
    "StatVar",
    "NumPlaces",
    "NumObservations",
    "MinValue",
    "MaxValue",
    "NumDates",
    "MinDate",
    "MaxDate",
    "MeasurementMethods",
    "Units",
    "ScalingFactors",
    "ObservationPeriods",
]


class StatVarAggregatorTest(unittest.TestCase):
    """Behavior-focused unit tests for stat_var_aggregator.py and main.py."""

    def test_load_config_from_yaml_and_import_spec_override(self):
        """Loads configured imports from YAML, supports import_spec overrides, and returns [] when unconfigured."""
        acs_rules = stat_var_aggregator.load_stat_var_aggregation_config(
            "CensusACS5YearSurvey")
        self.assertGreater(len(acs_rules), 40)
        rule_by_anc = {r["ancestor_sv_id"]: r for r in acs_rules}

        less_hs = rule_by_anc[
            "Count_Person_EducationalAttainment_LessThanHighSchoolDiploma"]
        self.assertIn("dc/05vn39gf0bz64", less_hs["source_sv_ids"])
        self.assertIn("dc/zrtnqhw8mhdp1", less_hs["source_sv_ids"])
        self.assertEqual(18, len(less_hs["source_sv_ids"]))

        override_rules = stat_var_aggregator.load_stat_var_aggregation_config(
            "UnconfiguredImport",
            import_spec={
                "stat_var_aggregation": {
                    "aggregations": [{
                        "ancestor_sv_id": "SV_Custom",
                        "source_sv_ids": ["SV_1", "SV_2"],
                    }]
                }
            },
        )
        self.assertEqual(1, len(override_rules))
        self.assertEqual("SV_Custom", override_rules[0]["ancestor_sv_id"])

        self.assertEqual(
            [],
            stat_var_aggregator.load_stat_var_aggregation_config(
                "UnconfiguredImport"),
        )
        self.assertEqual(
            [],
            stat_var_aggregator.load_stat_var_aggregation_config(
                "CensusACS5YearSurvey",
                config_path="/nonexistent/statvar_aggregation.yaml",
            ),
        )

    def test_expand_chained_rules_flattens_to_leaves_and_propagates_skip_flag(
            self):
        """Expands hierarchical rules into deduplicated leaf StatVars, propagates skip flags, and handles cycles."""
        s1251_raw = stat_var_aggregator.load_stat_var_aggregation_config(
            "CensusACS5YearSurvey_SubjectTables_S1251")
        s1251_expanded = stat_var_aggregator.expand_stat_var_aggregation_config(
            s1251_raw)
        s1251_map = {r["ancestor_sv_id"]: r for r in s1251_expanded}
        top_s1251 = s1251_map["Count_Person_WithOwnChildrenUnder18"]
        self.assertEqual(
            [
                "Count_Person_WithOwnChildrenUnder18_Female_FamilyHousehold_MarriedInThePast12Months_ResidesInHousehold",
                "Count_Person_WithOwnChildrenUnder18_Female_FamilyHousehold_DivorcedInThePast12Months_ResidesInHousehold",
                "Count_Person_WithOwnChildrenUnder18_Male_FamilyHousehold_MarriedInThePast12Months_ResidesInHousehold",
                "Count_Person_WithOwnChildrenUnder18_Male_FamilyHousehold_DivorcedInThePast12Months_ResidesInHousehold",
            ],
            top_s1251["source_sv_ids"],
        )
        self.assertFalse(top_s1251["skip_all_sources_present_check"])

        s0504_raw = stat_var_aggregator.load_stat_var_aggregation_config(
            "CensusACS5YearSurvey_SubjectTables_S0504")
        s0504_expanded = stat_var_aggregator.expand_stat_var_aggregation_config(
            s0504_raw)
        s0504_map = {r["ancestor_sv_id"]: r for r in s0504_expanded}
        top_s0504 = s0504_map["Count_Person_USCitizenByNaturalization"]
        self.assertEqual(96, len(top_s0504["source_sv_ids"]))
        self.assertTrue(top_s0504["skip_all_sources_present_check"])

        # Cyclic rules terminate cleanly without infinite recursion.
        cyclic_expanded = stat_var_aggregator.expand_stat_var_aggregation_config(
            [
                {
                    "ancestor_sv_id": "SV_A",
                    "source_sv_ids": ["SV_B", "Leaf_1"]
                },
                {
                    "ancestor_sv_id": "SV_B",
                    "source_sv_ids": ["SV_A", "Leaf_2"],
                    "skip_all_sources_present_check": True,
                },
            ])
        cyclic_map = {r["ancestor_sv_id"]: r for r in cyclic_expanded}
        self.assertTrue(cyclic_map["SV_A"]["skip_all_sources_present_check"])
        self.assertIn("Leaf_1", cyclic_map["SV_A"]["source_sv_ids"])
        self.assertIn("Leaf_2", cyclic_map["SV_A"]["source_sv_ids"])

    def test_expand_rules_normalizes_and_validates_aggregation_methods(self):
        """Defaults to SUM, normalizes method casing, skips incomplete rules, and rejects invalid methods."""
        expanded = stat_var_aggregator.expand_stat_var_aggregation_config([
            {
                "ancestor_sv_id": "",
                "source_sv_ids": ["SV1"]
            },
            {
                "ancestor_sv_id": "MissingSources",
                "source_sv_ids": []
            },
            {
                "ancestor_sv_id": "Out_Sum",
                "source_sv_ids": ["SV1", "SV2", "SV1"]
            },
            {
                "ancestor_sv_id": "Out_Min",
                "source_sv_ids": ["SV1", "SV2"],
                "aggregation_method": "min",
            },
            {
                "ancestor_sv_id": "Out_Max",
                "source_sv_ids": ["SV1", "SV2"],
                "aggregation_method": "MAX",
            },
            {
                "ancestor_sv_id": "Out_Avg",
                "source_sv_ids": ["SV1", "SV2"],
                "aggregation_method": "avg",
            },
        ])
        by_anc = {r["ancestor_sv_id"]: r for r in expanded}
        self.assertEqual(
            {"Out_Sum", "Out_Min", "Out_Max", "Out_Avg"},
            set(by_anc.keys()),
        )
        self.assertEqual(["SV1", "SV2"], by_anc["Out_Sum"]["source_sv_ids"])
        self.assertEqual("SUM", by_anc["Out_Sum"]["aggregation_method"])
        self.assertEqual("MIN", by_anc["Out_Min"]["aggregation_method"])
        self.assertEqual("MAX", by_anc["Out_Max"]["aggregation_method"])
        self.assertEqual("AVG", by_anc["Out_Avg"]["aggregation_method"])

        with self.assertRaisesRegex(ValueError,
                                    "Unsupported aggregation_method"):
            stat_var_aggregator.expand_stat_var_aggregation_config([{
                "ancestor_sv_id": "Bad_Rule",
                "source_sv_ids": ["SV1", "SV2"],
                "aggregation_method": "MEDIAN",
            }])

    def test_format_numeric_value(self):
        """Formats integers and decimals cleanly without scientific notation and handles non-finite inputs."""
        self.assertEqual("150", stat_var_aggregator.format_numeric_value(150.0))
        self.assertEqual("12.5",
                         stat_var_aggregator.format_numeric_value(12.5000))
        self.assertEqual("0", stat_var_aggregator.format_numeric_value(-0.0))
        self.assertEqual("",
                         stat_var_aggregator.format_numeric_value(float("nan")))
        self.assertEqual("",
                         stat_var_aggregator.format_numeric_value(float("inf")))
        self.assertEqual("", stat_var_aggregator.format_numeric_value(None))

    def test_compute_observation_dcid_determinism_and_uniqueness(self):
        """Produces deterministic dc/o/<13-hex> DCIDs and distinct hashes when any observation property changes."""
        base_kwargs = {
            "variable_measured": "Count_Person_Total",
            "observation_about": "geoId/06",
            "observation_date": "2022",
            "value_str": "250",
            "observation_period": "P1Y",
            "measurement_method": "dcAggregate/CensusACS5yrSurvey",
            "unit": "Person",
            "scaling_factor": "100",
        }
        dcid_1 = stat_var_aggregator.compute_observation_dcid(**base_kwargs)
        dcid_2 = stat_var_aggregator.compute_observation_dcid(**base_kwargs)
        self.assertTrue(dcid_1.startswith("dc/o/"))
        self.assertEqual(len("dc/o/") + 13, len(dcid_1))
        self.assertEqual(dcid_1, dcid_2)

        for field, changed_val in [
            ("variable_measured", "Count_Person_Other"),
            ("observation_about", "geoId/36"),
            ("observation_date", "2023"),
            ("value_str", "251"),
            ("observation_period", "P5Y"),
            ("measurement_method", "DataCommonsAggregate"),
            ("unit", "USDollar"),
            ("scaling_factor", "1000"),
        ]:
            modified = dict(base_kwargs, **{field: changed_val})
            self.assertNotEqual(
                dcid_1,
                stat_var_aggregator.compute_observation_dcid(**modified),
                msg=f"DCID did not change when {field} changed",
            )

    def test_write_and_parse_mcf_observations_roundtrip(self):
        """Writes StatVarObservation MCF nodes and parses them back while ignoring non-observation schema nodes."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            agg_mcf = os.path.join(tmp_dir, "stat_var_agg_nodes.mcf")
            stat_var_aggregator.write_mcf_observations(
                [
                    {
                        "variableMeasured": "dcs:SV_Total",
                        "observationAbout": "dcid:geoId/06",
                        "observationDate": "2022",
                        "value": 20.5,
                        "unit": "dcs:USDollar",
                        "measurementMethod": "dcAggregate/CensusACS5yrSurvey",
                        "observationPeriod": "P1Y",
                        "scalingFactor": "100",
                    },
                    {
                        "variableMeasured": "SV_Minimal",
                        "observationAbout": "country/USA",
                        "observationDate": "2021",
                        "value": 100.0,
                    },
                ],
                agg_mcf,
            )
            # Append a non-observation schema node to verify parse_mcf_observations ignores it.
            with open(agg_mcf, "a", encoding="utf-8") as f:
                f.write("\nNode: dcid:SV_Total\n"
                        "typeOf: dcs:StatisticalVariable\n"
                        "populationType: dcs:Person\n")

            parsed = stat_var_aggregator.parse_mcf_observations([agg_mcf])
            self.assertEqual(2, len(parsed))
            self.assertEqual("SV_Total", parsed[0]["variableMeasured"])
            self.assertEqual("geoId/06", parsed[0]["observationAbout"])
            self.assertEqual(20.5, parsed[0]["value"])
            self.assertEqual("20.5", parsed[0]["valueStr"])
            self.assertEqual("USDollar", parsed[0]["unit"])
            self.assertEqual("100", parsed[0]["scalingFactor"])
            self.assertTrue(parsed[0]["dcid"].startswith("dc/o/"))

            self.assertEqual("SV_Minimal", parsed[1]["variableMeasured"])
            self.assertEqual(100.0, parsed[1]["value"])
            self.assertEqual("", parsed[1]["unit"])
            self.assertEqual("", parsed[1]["observationPeriod"])

    def test_update_summary_report_csv_appends_and_overwrites_idempotently(
            self):
        """Appends aggregated StatVar stats to summary_report.csv and overwrites in place on rerun without duplicates."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            summary_csv = os.path.join(tmp_dir, "summary_report.csv")
            with open(summary_csv, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(_SUMMARY_CSV_HEADER)
                writer.writerow([
                    "dcs:SV_RawLeaf",
                    "1",
                    "1",
                    "50.0",
                    "50.0",
                    "1",
                    "2020",
                    "2020",
                    "[dcs:Method1]",
                    "[dcs:Person]",
                    "[]",
                    "[P1Y]",
                ])

            stat_var_aggregator.update_summary_report_csv(
                summary_csv,
                [
                    {
                        "variableMeasured": "SV_Agg",
                        "observationAbout": "geoId/06",
                        "observationDate": "2020",
                        "value": 100.0,
                        "measurementMethod": "dcAggregate/Method1",
                        "unit": "Person",
                        "observationPeriod": "P1Y",
                    },
                    {
                        "variableMeasured": "SV_Agg",
                        "observationAbout": "geoId/36",
                        "observationDate": "2021",
                        "value": 250.0,
                        "measurementMethod": "dcAggregate/Method1",
                        "unit": "Person",
                        "observationPeriod": "P1Y",
                    },
                ],
            )

            with open(summary_csv, "r", encoding="utf-8") as f:
                first_rows = list(csv.DictReader(f))
            self.assertEqual(["dcs:SV_RawLeaf", "dcs:SV_Agg"],
                             [r["StatVar"] for r in first_rows])
            self.assertEqual("2", first_rows[1]["NumPlaces"])
            self.assertEqual("2", first_rows[1]["NumObservations"])
            self.assertEqual("100.0", first_rows[1]["MinValue"])
            self.assertEqual("250.0", first_rows[1]["MaxValue"])
            self.assertEqual("2020", first_rows[1]["MinDate"])
            self.assertEqual("2021", first_rows[1]["MaxDate"])

            # Re-running updates dcs:SV_Agg in place without duplicating it or modifying dcs:SV_RawLeaf.
            stat_var_aggregator.update_summary_report_csv(
                summary_csv,
                [{
                    "variableMeasured": "SV_Agg",
                    "observationAbout": "geoId/06",
                    "observationDate": "2022",
                    "value": 300.0,
                    "measurementMethod": "dcAggregate/Method1",
                    "unit": "Person",
                    "observationPeriod": "P1Y",
                }],
            )
            with open(summary_csv, "r", encoding="utf-8") as f:
                rerun_rows = list(csv.DictReader(f))
            self.assertEqual(["dcs:SV_RawLeaf", "dcs:SV_Agg"],
                             [r["StatVar"] for r in rerun_rows])
            self.assertEqual("1", rerun_rows[1]["NumObservations"])
            self.assertEqual("300.0", rerun_rows[1]["MinValue"])
            self.assertEqual("2022", rerun_rows[1]["MinDate"])

    @mock.patch("stat_var_aggregator.bigquery_differ.load_mcf_to_bq_tables")
    @mock.patch("stat_var_aggregator.bigquery_differ.ensure_bq_dataset")
    def test_run_bigquery_aggregation_streams_pages_to_mcf_and_summary(
            self, mock_ensure_ds, mock_load_mcf):
        """Streams paginated BigQuery results to stat_var_agg_nodes.mcf and summary_report.csv and sets table TTL."""
        mock_load_mcf.return_value = (12, 2)
        mock_bq_client = mock.MagicMock()

        create_job = mock.MagicMock()
        create_job.result.return_value = []

        page1 = [(
            "dcid:SV_Agg1",
            "300",
            "geoId/06",
            "2020",
            "P1Y",
            "dcAggregate/Method1",
            "Person",
            "",
        )]
        page2 = [(
            "dcid:SV_Agg2",
            "500",
            "geoId/36",
            "2021",
            "P1Y",
            "DataCommonsAggregate",
            "Person",
            "",
        )]
        select_result = mock.MagicMock()
        select_result.pages = [page1, page2]
        select_job = mock.MagicMock()
        select_job.result.return_value = select_result

        mock_bq_client.query.side_effect = [create_job, select_job]

        with tempfile.TemporaryDirectory() as tmp_dir:
            out_mcf = os.path.join(tmp_dir, "stat_var_agg_nodes.mcf")
            summary_csv = os.path.join(tmp_dir, "summary_report.csv")
            with open(summary_csv, "w", encoding="utf-8", newline="") as f:
                csv.writer(f).writerow(_SUMMARY_CSV_HEADER)

            res = stat_var_aggregator.run_bigquery_aggregation(
                mcf_pattern="gs://bucket/import/2026_10_21/input0/genmcf/*.mcf",
                aggregations=[
                    {
                        "ancestor_sv_id": "SV_Agg1",
                        "source_sv_ids": ["SV_A", "SV_B"],
                    },
                    {
                        "ancestor_sv_id": "SV_Agg2",
                        "source_sv_ids": ["SV_C", "SV_D"],
                    },
                ],
                output_mcf_path=out_mcf,
                project_id="test-proj",
                dataset_id="test_ds",
                import_name="TestImport",
                version="2026_10_21",
                input_prefix="input0",
                summary_report_path=summary_csv,
                expiration_hours=12,
                bq_client=mock_bq_client,
                page_size=10000,
            )

            self.assertEqual(12, res["raw_obs_count"])
            self.assertEqual(2, res["raw_schema_count"])
            self.assertEqual(2, res["agg_obs_count"])
            self.assertEqual(out_mcf, res["output_mcf_path"])

            expected_tables = bigquery_differ.get_import_bq_table_ids(
                "test-proj.test_ds", "TestImport", "2026_10_21", "input0")
            self.assertEqual(expected_tables, res["table_ids"])

            _, load_kwargs = mock_load_mcf.call_args
            self.assertEqual({"stat_var_agg_nodes.mcf"},
                             load_kwargs["exclude_filenames"])
            select_job.result.assert_called_once_with(page_size=10000)
            mock_bq_client.update_table.assert_called_once()

            parsed = stat_var_aggregator.parse_mcf_observations([out_mcf])
            self.assertEqual(
                {
                    "SV_Agg1": 300.0,
                    "SV_Agg2": 500.0
                },
                {r["variableMeasured"]: r["value"] for r in parsed},
            )

            with open(summary_csv, "r", encoding="utf-8") as f:
                summary_rows = list(csv.DictReader(f))
            self.assertEqual(["dcs:SV_Agg1", "dcs:SV_Agg2"],
                             [r["StatVar"] for r in summary_rows])

    @mock.patch("stat_var_aggregator.bigquery_differ.load_mcf_to_bq_tables")
    @mock.patch("stat_var_aggregator.bigquery_differ.ensure_bq_dataset")
    def test_run_bigquery_aggregation_noop_on_empty_rules_or_zero_raw_obs(
            self, mock_ensure_ds, mock_load_mcf):
        """Does not create output MCF or run aggregation queries when rules are empty or raw observations are 0."""
        mock_bq_client = mock.MagicMock()

        with tempfile.TemporaryDirectory() as tmp_dir:
            out_mcf = os.path.join(tmp_dir, "stat_var_agg_nodes.mcf")

            empty_res = stat_var_aggregator.run_bigquery_aggregation(
                mcf_pattern="gs://bucket/in/*.mcf",
                aggregations=[],
                output_mcf_path=out_mcf,
                project_id="test-proj",
                bq_client=mock_bq_client,
            )
            self.assertEqual(0, empty_res["agg_obs_count"])
            self.assertIsNone(empty_res["output_mcf_path"])
            self.assertFalse(os.path.exists(out_mcf))
            mock_load_mcf.assert_not_called()
            mock_bq_client.query.assert_not_called()

            mock_load_mcf.return_value = (0, 3)
            zero_obs_res = stat_var_aggregator.run_bigquery_aggregation(
                mcf_pattern="gs://bucket/in/*.mcf",
                aggregations=[{
                    "ancestor_sv_id": "SV_Total",
                    "source_sv_ids": ["SV_A", "SV_B"],
                }],
                output_mcf_path=out_mcf,
                project_id="test-proj",
                bq_client=mock_bq_client,
            )
            self.assertEqual(0, zero_obs_res["raw_obs_count"])
            self.assertEqual(3, zero_obs_res["raw_schema_count"])
            self.assertEqual(0, zero_obs_res["agg_obs_count"])
            self.assertIsNone(zero_obs_res["output_mcf_path"])
            self.assertFalse(os.path.exists(out_mcf))
            mock_bq_client.query.assert_not_called()

    @mock.patch("aggregator_main.storage.Client")
    def test_main_run_aggregation_job_skips_unconfigured_and_validates_name(
            self, mock_storage_cls):
        """Exits with 0 without GCS calls when import has no rules, and rejects malformed import_name."""
        with self.assertRaisesRegex(ValueError, "--import_name must be"):
            aggregator_main.run_aggregation_job(
                absolute_import_name="malformed_name_without_colon")

        exit_code = aggregator_main.run_aggregation_job(
            absolute_import_name="scripts/us_fed:treasury_unconfigured",
            import_config_str='{"gcp_project_id": "test-proj"}',
            bucket_name="test-bucket",
        )
        self.assertEqual(0, exit_code)
        mock_storage_cls.assert_not_called()

    @mock.patch("aggregator_main.stat_var_aggregator.run_bigquery_aggregation")
    @mock.patch("aggregator_main.storage.Client")
    def test_main_run_aggregation_job_discovers_inputs_uploads_and_updates_summary(
            self, mock_storage_cls, mock_run_bq_agg):
        """Discovers input prefixes, uploads MCF & summary CSV when observations are produced, and updates import_summary.json."""
        mock_gcs = mock_storage_cls.return_value
        mock_bucket = mock.MagicMock()
        mock_gcs.bucket.return_value = mock_bucket

        base_path = "scripts/india_rbi/India_RBIStateDomesticProduct"
        blob_store = {
            f"{base_path}/staging_version.txt":
                "2026_10_21",
            f"{base_path}/2026_10_21/import_summary.json":
                json.dumps({
                    "import_name": "India_RBIStateDomesticProduct",
                    "status": "PENDING",
                }),
            f"{base_path}/2026_10_21/input0/genmcf/summary_report.csv":
                ",".join(_SUMMARY_CSV_HEADER),
            f"{base_path}/2026_10_21/input1/genmcf/summary_report.csv":
                ",".join(_SUMMARY_CSV_HEADER),
        }
        uploaded_strings = {}
        uploaded_files = {}

        def _get_blob(path):
            b = mock.MagicMock()
            b.name = path
            b.exists.return_value = path in blob_store
            b.download_as_text.return_value = blob_store.get(path, "")

            def _upload_str(content):
                uploaded_strings[path] = content

            def _upload_file(local_path):
                with open(local_path, "r", encoding="utf-8") as f:
                    uploaded_files[path] = f.read()

            b.upload_from_string.side_effect = _upload_str
            b.upload_from_filename.side_effect = _upload_file
            return b

        mock_bucket.blob.side_effect = _get_blob
        mock_iterator = mock.MagicMock()
        mock_iterator.prefixes = [
            f"{base_path}/2026_10_21/input0/",
            f"{base_path}/2026_10_21/input1/",
        ]
        mock_gcs.list_blobs.return_value = mock_iterator

        def _fake_bq_agg(**kwargs):
            # input0 produces 1 aggregated observation; input1 produces 0.
            if kwargs["input_prefix"] == "input1":
                return {"agg_obs_count": 0, "output_mcf_path": None}
            out_mcf = kwargs["output_mcf_path"]
            stat_var_aggregator.write_mcf_observations(
                [{
                    "dcid":
                        "dc/o/test123",
                    "variableMeasured":
                        "Nominal_Amount_EconomicActivity_GrossValueAdded",
                    "observationAbout":
                        "wikidataId/Q1185",
                    "observationDate":
                        "2020",
                    "value":
                        600.0,
                    "unit":
                        "IndianRupee",
                    "measurementMethod":
                        "dcAggregate/RBI_Methodology",
                }],
                out_mcf,
            )
            if kwargs.get("summary_report_path"):
                stat_var_aggregator.update_summary_report_csv(
                    kwargs["summary_report_path"],
                    stat_var_aggregator.parse_mcf_observations([out_mcf]),
                )
            return {"agg_obs_count": 1, "output_mcf_path": out_mcf}

        mock_run_bq_agg.side_effect = _fake_bq_agg

        exit_code = aggregator_main.run_aggregation_job(
            absolute_import_name=
            "scripts/india_rbi:India_RBIStateDomesticProduct",
            import_config_str='{"gcp_project_id": "test-proj"}',
            bucket_name="test-bucket",
            bq_dataset="test_dataset",
        )
        self.assertEqual(0, exit_code)
        self.assertEqual(2, mock_run_bq_agg.call_count)

        # input0 artifacts uploaded; input1 skipped uploading empty MCF.
        input0_mcf_blob = f"{base_path}/2026_10_21/input0/genmcf/stat_var_agg_nodes.mcf"
        input1_mcf_blob = f"{base_path}/2026_10_21/input1/genmcf/stat_var_agg_nodes.mcf"
        input0_summary_blob = f"{base_path}/2026_10_21/input0/genmcf/summary_report.csv"
        import_summary_blob = f"{base_path}/2026_10_21/import_summary.json"

        self.assertIn(input0_mcf_blob, uploaded_files)
        self.assertNotIn(input1_mcf_blob, uploaded_files)
        self.assertIn(
            "variableMeasured: dcs:Nominal_Amount_EconomicActivity_GrossValueAdded",
            uploaded_files[input0_mcf_blob],
        )
        self.assertIn(input0_summary_blob, uploaded_files)
        self.assertIn(
            "dcs:Nominal_Amount_EconomicActivity_GrossValueAdded",
            uploaded_files[input0_summary_blob],
        )

        updated_summary = json.loads(uploaded_strings[import_summary_blob])
        self.assertEqual(
            1, updated_summary["import_stats"]["aggregated_obs_count"])
        self.assertIn("aggregation_execution_time",
                      updated_summary["import_stats"])

        # Missing staging_version.txt raises RuntimeError.
        blob_store.pop(f"{base_path}/staging_version.txt")
        with self.assertRaisesRegex(RuntimeError, "No candidate version found"):
            aggregator_main.run_aggregation_job(
                absolute_import_name=
                "scripts/india_rbi:India_RBIStateDomesticProduct",
                bucket_name="test-bucket",
            )


if __name__ == "__main__":
    unittest.main()
