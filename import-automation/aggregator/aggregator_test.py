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
"""Unit and end-to-end tests for ET-layer StatVar aggregation (aggregator/)."""

import csv
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import types
import unittest
from unittest import mock

import duckdb

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


def _get_java_genmcf_command() -> list[str]:
    """Returns the command prefix to run org.datacommons.tool.Main genmcf."""
    workspace_root = os.path.abspath(os.path.join(_ROOT_DIR, ".."))
    fat_jar = os.path.join(
        workspace_root,
        "import",
        "tool",
        "target",
        "datacommons-import-tool-0.1-SNAPSHOT-jar-with-dependencies.jar",
    )
    if os.path.exists(fat_jar):
        return ["java", "-jar", fat_jar]

    tool_classes = os.path.join(workspace_root, "import", "tool", "target",
                                "classes")
    util_jar = os.path.join(
        workspace_root,
        "import",
        "util",
        "target",
        "datacommons-import-util-0.1-SNAPSHOT.jar",
    )
    m2 = os.path.expanduser("~/.m2/repository")
    cp_jars = [
        tool_classes,
        util_jar,
        f"{m2}/com/fasterxml/jackson/core/jackson-core/2.15.4/jackson-core-2.15.4.jar",
        f"{m2}/com/fasterxml/jackson/core/jackson-databind/2.15.4/jackson-databind-2.15.4.jar",
        f"{m2}/com/fasterxml/jackson/core/jackson-annotations/2.15.4/jackson-annotations-2.15.4.jar",
        f"{m2}/commons-io/commons-io/2.11.0/commons-io-2.11.0.jar",
        f"{m2}/com/google/protobuf/protobuf-java/3.25.5/protobuf-java-3.25.5.jar",
        f"{m2}/com/google/protobuf/protobuf-java-util/3.25.5/protobuf-java-util-3.25.5.jar",
        f"{m2}/com/google/code/gson/gson/2.10.1/gson-2.10.1.jar",
        f"{m2}/org/apache/commons/commons-csv/1.6/commons-csv-1.6.jar",
        f"{m2}/org/apache/commons/commons-text/1.10.0/commons-text-1.10.0.jar",
        f"{m2}/org/apache/commons/commons-lang3/3.12.0/commons-lang3-3.12.0.jar",
        f"{m2}/org/apache/commons/commons-compress/1.26.1/commons-compress-1.26.1.jar",
        f"{m2}/info/picocli/picocli/4.6.1/picocli-4.6.1.jar",
        f"{m2}/org/freemarker/freemarker/2.3.31/freemarker-2.3.31.jar",
        f"{m2}/org/jfree/jfreechart/1.5.3/jfreechart-1.5.3.jar",
        f"{m2}/org/jfree/jfreesvg/3.3/jfreesvg-3.3.jar",
        f"{m2}/com/google/guava/guava/32.1.3-jre/guava-32.1.3-jre.jar",
        f"{m2}/com/google/guava/failureaccess/1.0.1/failureaccess-1.0.1.jar",
        f"{m2}/dev/failsafe/failsafe/3.3.2/failsafe-3.3.2.jar",
        f"{m2}/com/github/jsonld-java/jsonld-java/0.13.6/jsonld-java-0.13.6.jar",
        f"{m2}/org/apache/logging/log4j/log4j-api/2.16.0/log4j-api-2.16.0.jar",
        f"{m2}/org/apache/logging/log4j/log4j-core/2.16.0/log4j-core-2.16.0.jar",
        f"{m2}/org/slf4j/slf4j-api/1.7.36/slf4j-api-1.7.36.jar",
        f"{m2}/org/apache/httpcomponents/httpclient-osgi/4.5.14/httpclient-osgi-4.5.14.jar",
        f"{m2}/org/apache/httpcomponents/httpcore-osgi/4.4.16/httpcore-osgi-4.4.16.jar",
    ]
    return ["java", "-cp", ":".join(cp_jars), "org.datacommons.tool.Main"]


def _run_genmcf_local(
    tmcf_content: str,
    csv_content: str,
    work_dir: str,
    csv_name: str = "data.csv",
) -> str:
    """Writes TMCF and CSV, runs Java import-tool genmcf with LOCAL resolution, returns genmcf dir."""
    tmcf_path = os.path.join(work_dir, "test.tmcf")
    csv_path = os.path.join(work_dir, csv_name)
    genmcf_dir = os.path.join(work_dir, "genmcf")
    with open(tmcf_path, "w", encoding="utf-8") as f:
        f.write(tmcf_content)
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write(csv_content)

    cmd = _get_java_genmcf_command() + [
        "genmcf",
        "--resolution=LOCAL",
        "--existence-checks=false",
        f"--output-dir={genmcf_dir}",
        tmcf_path,
        csv_path,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(
            f"genmcf failed (exit {proc.returncode}):\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
        )
    return genmcf_dir


class StatVarAggregatorTest(unittest.TestCase):
    """Tests for ET-layer StatVar aggregation (stat_var_aggregator.py and main.py)."""

    def test_central_yaml_parity_1_preserves_exact_dcids(self):
        """Parity 1: Central YAML preserves exact dc/... hash DCIDs from stat_var_aggregation.textproto."""
        acs_rules = stat_var_aggregator.load_stat_var_aggregation_config(
            "CensusACS5YearSurvey")
        self.assertTrue(len(acs_rules) > 40)
        rule_by_anc = {r["ancestor_sv_id"]: r for r in acs_rules}

        less_hs = rule_by_anc[
            "Count_Person_EducationalAttainment_LessThanHighSchoolDiploma"]
        self.assertIn("dc/05vn39gf0bz64", less_hs["source_sv_ids"])
        self.assertIn("dc/zrtnqhw8mhdp1", less_hs["source_sv_ids"])
        self.assertEqual(18, len(less_hs["source_sv_ids"]))

        s1201_rules = stat_var_aggregator.load_stat_var_aggregation_config(
            "CensusACS5YearSurvey_SubjectTables_S1201")
        s1201_map = {r["ancestor_sv_id"]: r for r in s1201_rules}
        self.assertEqual(
            [
                "Count_Person_InLaborForce_Female_Divorced",
                "Count_Person_InLaborForce_Male_Divorced",
            ],
            s1201_map["Count_Person_InLaborForce_Divorced"]["source_sv_ids"],
        )

        s2408_rules = stat_var_aggregator.load_stat_var_aggregation_config(
            "CensusACS5YearSurvey_SubjectTables_S2408")
        s2408_map = {r["ancestor_sv_id"]: r for r in s2408_rules}
        self.assertEqual(
            [
                "Count_Person_PrivatelyOwnedNotForProfitEstablishment_Male_PaidWorker",
                "Count_Person_PrivatelyOwnedNotForProfitEstablishment_Female_PaidWorker",
            ],
            s2408_map[
                "Count_Person_PrivatelyOwnedNotForProfitEstablishment_PaidWorker"]
            ["source_sv_ids"],
        )

    def test_parity_2_expand_chained_rules_s1251_and_s0504(self):
        """Parity 2: Hierarchical/chained rules in S1251 and S0504 expand in memory to leaf StatVars."""
        s1251_raw = stat_var_aggregator.load_stat_var_aggregation_config(
            "CensusACS5YearSurvey_SubjectTables_S1251")
        s1251_expanded = stat_var_aggregator.expand_stat_var_aggregation_config(
            s1251_raw)
        s1251_map = {r["ancestor_sv_id"]: r for r in s1251_expanded}
        top_s1251 = s1251_map["Count_Person_WithOwnChildrenUnder18"]
        self.assertTrue(top_s1251.get("has_derived_sources"))
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
        self.assertTrue(top_s0504.get("has_derived_sources"))
        self.assertEqual(96, len(top_s0504["source_sv_ids"]))
        self.assertTrue(top_s0504["skip_all_sources_present_check"])

    def test_parity_3a_group_by_original_facet_before_dc_aggregate_prefix(self):
        """Parity 3A: Observations with 'MethodA' and 'dcAggregate/MethodA' are NOT merged into the same group."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            mcf_path = os.path.join(tmp_dir, "table_mcf_nodes_test.mcf")
            records = [
                {
                    "dcid": "obs1",
                    "variableMeasured": "SV_Child1",
                    "observationAbout": "geoId/06",
                    "observationDate": "2020",
                    "value": 10.0,
                    "valueStr": "10",
                    "unit": "Person",
                    "measurementMethod": "MethodA",
                    "observationPeriod": "P1Y",
                    "scalingFactor": "",
                },
                {
                    "dcid": "obs2",
                    "variableMeasured": "SV_Child2",
                    "observationAbout": "geoId/06",
                    "observationDate": "2020",
                    "value": 20.0,
                    "valueStr": "20",
                    "unit": "Person",
                    "measurementMethod": "dcAggregate/MethodA",
                    "observationPeriod": "P1Y",
                    "scalingFactor": "",
                },
            ]
            stat_var_aggregator.write_mcf_observations(records, mcf_path)

            rules_strict = [{
                "ancestor_sv_id": "SV_Parent",
                "source_sv_ids": ["SV_Child1", "SV_Child2"],
                "skip_all_sources_present_check": False,
            }]
            out_strict = stat_var_aggregator.run_stat_var_aggregation_duckdb(
                [mcf_path], rules_strict)
            self.assertEqual([], out_strict)

            rules_skip = [{
                "ancestor_sv_id": "SV_Parent",
                "source_sv_ids": ["SV_Child1", "SV_Child2"],
                "skip_all_sources_present_check": True,
            }]
            out_skip = stat_var_aggregator.run_stat_var_aggregation_duckdb(
                [mcf_path], rules_skip)
            self.assertEqual(2, len(out_skip))
            self.assertEqual([10.0, 20.0], sorted(r["value"] for r in out_skip))

    def test_parity_3b_deduplicate_input_observations_last_wins(self):
        """Parity 3B: Duplicate input observations for the same (SV, place, date, facet) keep the last by row_num."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            mcf_path = os.path.join(tmp_dir, "table_mcf_nodes_dup.mcf")
            records = [
                {
                    "dcid": "obs1_dup_early",
                    "variableMeasured": "SV_Child1",
                    "observationAbout": "geoId/06",
                    "observationDate": "2020",
                    "value": 999.0,
                    "valueStr": "999",
                    "unit": "Person",
                    "measurementMethod": "CensusACS5yrSurvey",
                    "observationPeriod": "P1Y",
                    "scalingFactor": "",
                },
                {
                    "dcid": "obs1_dup_last",
                    "variableMeasured": "SV_Child1",
                    "observationAbout": "geoId/06",
                    "observationDate": "2020",
                    "value": 100.0,
                    "valueStr": "100",
                    "unit": "Person",
                    "measurementMethod": "CensusACS5yrSurvey",
                    "observationPeriod": "P1Y",
                    "scalingFactor": "",
                },
                {
                    "dcid": "obs2",
                    "variableMeasured": "SV_Child2",
                    "observationAbout": "geoId/06",
                    "observationDate": "2020",
                    "value": 50.0,
                    "valueStr": "50",
                    "unit": "Person",
                    "measurementMethod": "CensusACS5yrSurvey",
                    "observationPeriod": "P1Y",
                    "scalingFactor": "",
                },
            ]
            stat_var_aggregator.write_mcf_observations(records, mcf_path)
            rules = [{
                "ancestor_sv_id": "SV_Parent",
                "source_sv_ids": ["SV_Child1", "SV_Child2"],
            }]
            out = stat_var_aggregator.run_stat_var_aggregation_duckdb(
                [mcf_path], rules)
            self.assertEqual(1, len(out))
            self.assertEqual(150.0, out[0]["value"])
            self.assertEqual("150", out[0]["valueStr"])
            self.assertEqual("dcAggregate/CensusACS5yrSurvey",
                             out[0]["measurementMethod"])

    def test_parity_4_aggregation_methods_sum_min_max_avg(self):
        """Parity 4: Supports SUM (default), MIN, MAX, and AVG aggregation methods."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            mcf_path = os.path.join(tmp_dir, "table_mcf_nodes_methods.mcf")
            records = [
                {
                    "dcid": "o1",
                    "variableMeasured": "SV1",
                    "observationAbout": "country/USA",
                    "observationDate": "2021",
                    "value": 10.0,
                    "valueStr": "10",
                    "unit": "",
                    "measurementMethod": "",
                    "observationPeriod": "",
                    "scalingFactor": "",
                },
                {
                    "dcid": "o2",
                    "variableMeasured": "SV2",
                    "observationAbout": "country/USA",
                    "observationDate": "2021",
                    "value": 30.0,
                    "valueStr": "30",
                    "unit": "",
                    "measurementMethod": "",
                    "observationPeriod": "",
                    "scalingFactor": "",
                },
            ]
            stat_var_aggregator.write_mcf_observations(records, mcf_path)
            rules = [
                {
                    "ancestor_sv_id": "Out_Sum",
                    "source_sv_ids": ["SV1", "SV2"]
                },
                {
                    "ancestor_sv_id": "Out_Min",
                    "source_sv_ids": ["SV1", "SV2"],
                    "aggregation_method": "MIN",
                },
                {
                    "ancestor_sv_id": "Out_Max",
                    "source_sv_ids": ["SV1", "SV2"],
                    "aggregation_method": "MAX",
                },
                {
                    "ancestor_sv_id": "Out_Avg",
                    "source_sv_ids": ["SV1", "SV2"],
                    "aggregation_method": "AVG",
                },
            ]
            out = stat_var_aggregator.run_stat_var_aggregation_duckdb(
                [mcf_path], rules)
            by_sv = {r["variableMeasured"]: r for r in out}
            self.assertEqual(40.0, by_sv["Out_Sum"]["value"])
            self.assertEqual(10.0, by_sv["Out_Min"]["value"])
            self.assertEqual(30.0, by_sv["Out_Max"]["value"])
            self.assertEqual(20.0, by_sv["Out_Avg"]["value"])
            self.assertEqual("DataCommonsAggregate",
                             by_sv["Out_Sum"]["measurementMethod"])

    def test_agg_obs_key_combined_matches_flush_node_to_csv_on_stat_var_agg_nodes_mcf(
        self,):
        """Verifies agg_obs key_combined, variableMeasured, and value match _flush_node_to_csv on stat_var_agg_nodes.mcf."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            raw_mcf = os.path.join(tmp_dir, "table_mcf_nodes_0.mcf")
            agg_mcf = os.path.join(tmp_dir, "stat_var_agg_nodes.mcf")
            records = [
                {
                    "dcid": "o1",
                    "variableMeasured": "SV_Child1",
                    "observationAbout": "geoId/06",
                    "observationDate": "2022",
                    "value": 12.5,
                    "valueStr": "12.5",
                    "unit": "USDollar",
                    "measurementMethod": "CensusACS5yrSurvey",
                    "observationPeriod": "P1Y",
                    "scalingFactor": "100",
                },
                {
                    "dcid": "o2",
                    "variableMeasured": "SV_Child2",
                    "observationAbout": "geoId/06",
                    "observationDate": "2022",
                    "value": 7.5,
                    "valueStr": "7.5",
                    "unit": "USDollar",
                    "measurementMethod": "CensusACS5yrSurvey",
                    "observationPeriod": "P1Y",
                    "scalingFactor": "100",
                },
            ]
            stat_var_aggregator.write_mcf_observations(records, raw_mcf)
            rules = [{
                "ancestor_sv_id": "SV_Total",
                "source_sv_ids": ["SV_Child1", "SV_Child2"],
            }]
            res = stat_var_aggregator.run_duckdb_aggregation(
                mcf_pattern=raw_mcf,
                aggregations=rules,
                output_mcf_path=agg_mcf,
                return_agg_obs_rows=True,
            )
            self.assertEqual(1, res["agg_obs_count"])
            agg_obs_row = res["agg_obs_rows"][0]

            parsed_obs_csv = os.path.join(tmp_dir, "parsed_agg_obs.csv")
            parsed_schema_csv = os.path.join(tmp_dir, "parsed_agg_schema.csv")
            obs_cnt, _ = bigquery_differ.stream_mcf_to_csv(
                agg_mcf, parsed_obs_csv, parsed_schema_csv)
            self.assertEqual(1, obs_cnt)
            with open(parsed_obs_csv, "r", encoding="utf-8") as f:
                csv_rows = list(csv.DictReader(f))
            self.assertEqual(1, len(csv_rows))
            csv_row = csv_rows[0]

            self.assertEqual(csv_row["key_combined"],
                             agg_obs_row["key_combined"])
            self.assertEqual(csv_row["variableMeasured"],
                             agg_obs_row["variableMeasured"])
            self.assertEqual("dcid:SV_Total", agg_obs_row["variableMeasured"])
            self.assertEqual(csv_row["value"], agg_obs_row["value"])
            self.assertEqual("20", agg_obs_row["value"])

    def test_e2e_pattern_1_india_rbi_state_domestic_product(self):
        """End-to-end test: CSV + TMCF -> Java genmcf -> MCF -> DuckDB -> stat_var_agg_nodes.mcf for India_RBI."""
        tmcf = """Node: E:rbi->E0
typeOf: dcs:StatVarObservation
variableMeasured: C:rbi->StatVar
observationAbout: C:rbi->Place
observationDate: C:rbi->Date
value: C:rbi->Value
unit: dcs:IndianRupee
measurementMethod: dcs:RBI_Methodology
"""
        csv_data = """Place,Date,StatVar,Value
dcid:wikidataId/Q1185,2020,dcs:Nominal_Amount_EconomicActivity_GrossValueAdded_Agriculture,100
dcid:wikidataId/Q1185,2020,dcs:Nominal_Amount_EconomicActivity_GrossValueAdded_BankingAndInsuranceSector,100
dcid:wikidataId/Q1185,2020,dcs:Nominal_Amount_EconomicActivity_GrossValueAdded_Construction,100
dcid:wikidataId/Q1185,2020,dcs:Nominal_Amount_EconomicActivity_GrossValueAdded_Industry,100
dcid:wikidataId/Q1185,2020,dcs:Nominal_Amount_EconomicActivity_GrossValueAdded_ManufacturingSector,100
dcid:wikidataId/Q1185,2020,dcs:Nominal_Amount_EconomicActivity_GrossValueAdded_Services,100
dcid:wikidataId/Q1185,2021,dcs:Nominal_Amount_EconomicActivity_GrossValueAdded_Agriculture,50
dcid:wikidataId/Q1185,2021,dcs:Nominal_Amount_EconomicActivity_GrossValueAdded_Construction,50
"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            genmcf_dir = _run_genmcf_local(tmcf, csv_data, tmp_dir, "rbi.csv")
            out_mcf = stat_var_aggregator.run_stat_var_aggregation_for_genmcf(
                import_name="India_RBIStateDomesticProduct",
                genmcf_output_path=genmcf_dir,
            )
            self.assertIsNotNone(out_mcf)
            self.assertTrue(os.path.exists(out_mcf))

            parsed = stat_var_aggregator.parse_mcf_observations([out_mcf])
            self.assertEqual(1, len(parsed))
            self.assertEqual(
                "Nominal_Amount_EconomicActivity_GrossValueAdded",
                parsed[0]["variableMeasured"],
            )
            self.assertEqual("wikidataId/Q1185", parsed[0]["observationAbout"])
            self.assertEqual("2020", parsed[0]["observationDate"])
            self.assertEqual(600.0, parsed[0]["value"])
            self.assertEqual("dcAggregate/RBI_Methodology",
                             parsed[0]["measurementMethod"])

            summary_csv = os.path.join(genmcf_dir, "summary_report.csv")
            with open(summary_csv, "r", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
            sv_names = [r["StatVar"] for r in rows]
            self.assertIn("dcs:Nominal_Amount_EconomicActivity_GrossValueAdded",
                          sv_names)

    def test_e2e_pattern_2_oecd_regional_demography_population(self):
        """End-to-end test: OECDRegionalDemography_Population overlapping age aggregations with skip_check=True."""
        tmcf = """Node: E:oecd->E0
typeOf: dcs:StatVarObservation
variableMeasured: C:oecd->StatVar
observationAbout: C:oecd->Place
observationDate: C:oecd->Date
value: C:oecd->Value
measurementMethod: dcs:OECDRegionalStatistics
"""
        csv_data = """Place,Date,StatVar,Value
dcid:nuts/DE1,2020,dcs:Count_Person_Upto4Years,1000
dcid:nuts/DE1,2020,dcs:Count_Person_5To9Years,1200
dcid:nuts/DE1,2020,dcs:Count_Person_10To14Years,1300
dcid:nuts/DE1,2020,dcs:Count_Person_15To19Years,1500
"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            genmcf_dir = _run_genmcf_local(tmcf, csv_data, tmp_dir, "oecd.csv")
            out_mcf = stat_var_aggregator.run_stat_var_aggregation_for_genmcf(
                import_name="OECDRegionalDemography_Population",
                genmcf_output_path=genmcf_dir,
            )
            self.assertIsNotNone(out_mcf)
            parsed = stat_var_aggregator.parse_mcf_observations([out_mcf])
            by_sv = {r["variableMeasured"]: r["value"] for r in parsed}
            self.assertEqual(
                {
                    "Count_Person_Upto9Years": 2200.0,
                    "Count_Person_10To19Years": 2800.0,
                    "Count_Person_5To19Years": 4000.0,
                },
                by_sv,
            )

    def test_e2e_pattern_3_usda_agriculture_census(self):
        """End-to-end test: USDA_AgricultureCensus Count_Person_Producer with partial race sources."""
        tmcf = """Node: E:usda->E0
typeOf: dcs:StatVarObservation
variableMeasured: C:usda->StatVar
observationAbout: C:usda->Place
observationDate: C:usda->Date
value: C:usda->Value
measurementMethod: dcs:USDAAgricultureCensus
"""
        csv_data = """Place,Date,StatVar,Value
dcid:geoId/06,2017,dcs:Count_Person_Producer_WhiteAlone,50000
dcid:geoId/06,2017,dcs:Count_Person_Producer_HispanicOrLatino,12000
dcid:geoId/06,2017,dcs:Count_Person_Producer_AsianAlone,4000
"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            genmcf_dir = _run_genmcf_local(tmcf, csv_data, tmp_dir, "usda.csv")
            out_mcf = stat_var_aggregator.run_stat_var_aggregation_for_genmcf(
                import_name="USDA_AgricultureCensus",
                genmcf_output_path=genmcf_dir,
            )
            self.assertIsNotNone(out_mcf)
            parsed = stat_var_aggregator.parse_mcf_observations([out_mcf])
            self.assertEqual(1, len(parsed))
            self.assertEqual("Count_Person_Producer",
                             parsed[0]["variableMeasured"])
            self.assertEqual(66000.0, parsed[0]["value"])
            self.assertEqual(
                "dcAggregate/USDAAgricultureCensus",
                parsed[0]["measurementMethod"],
            )

    def test_e2e_pattern_4_hierarchical_s1251_and_rerun_idempotence(self):
        """End-to-end test: Chained aggregations in S1251 + re-run excludes existing stat_var_agg_nodes.mcf."""
        tmcf = """Node: E:s1251->E0
typeOf: dcs:StatVarObservation
variableMeasured: C:s1251->StatVar
observationAbout: C:s1251->Place
observationDate: C:s1251->Date
value: C:s1251->Value
measurementMethod: dcs:CensusACS5yrSurvey
"""
        csv_data = """Place,Date,StatVar,Value
dcid:geoId/06,2022,dcs:Count_Person_WithOwnChildrenUnder18_Female_FamilyHousehold_MarriedInThePast12Months_ResidesInHousehold,100
dcid:geoId/06,2022,dcs:Count_Person_WithOwnChildrenUnder18_Female_FamilyHousehold_DivorcedInThePast12Months_ResidesInHousehold,40
dcid:geoId/06,2022,dcs:Count_Person_WithOwnChildrenUnder18_Male_FamilyHousehold_MarriedInThePast12Months_ResidesInHousehold,80
dcid:geoId/06,2022,dcs:Count_Person_WithOwnChildrenUnder18_Male_FamilyHousehold_DivorcedInThePast12Months_ResidesInHousehold,30
"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            genmcf_dir = _run_genmcf_local(tmcf, csv_data, tmp_dir, "s1251.csv")
            out_mcf = stat_var_aggregator.run_stat_var_aggregation_for_genmcf(
                import_name="CensusACS5YearSurvey_SubjectTables_S1251",
                genmcf_output_path=genmcf_dir,
            )
            self.assertIsNotNone(out_mcf)
            parsed = stat_var_aggregator.parse_mcf_observations([out_mcf])
            by_sv = {r["variableMeasured"]: r["value"] for r in parsed}
            self.assertEqual(
                {
                    "Count_Person_WithOwnChildrenUnder18_Female": 140.0,
                    "Count_Person_WithOwnChildrenUnder18_Male": 110.0,
                    "Count_Person_WithOwnChildrenUnder18": 250.0,
                },
                by_sv,
            )

            out_mcf_rerun = (
                stat_var_aggregator.run_stat_var_aggregation_for_genmcf(
                    import_name="CensusACS5YearSurvey_SubjectTables_S1251",
                    genmcf_output_path=genmcf_dir,
                ))
            self.assertIsNotNone(out_mcf_rerun)
            parsed_rerun = stat_var_aggregator.parse_mcf_observations(
                [out_mcf_rerun])
            self.assertEqual(3, len(parsed_rerun))
            self.assertEqual(
                by_sv,
                {r["variableMeasured"]: r["value"] for r in parsed_rerun},
            )

    @mock.patch("stat_var_aggregator.bigquery_differ.load_mcf_to_bq_tables")
    @mock.patch("stat_var_aggregator.bigquery_differ.ensure_bq_dataset")
    def test_run_bigquery_aggregation_paginated_streaming(
            self, mock_ensure_ds, mock_load_mcf):
        """Tests BigQuery mode: loads raw_obs/raw_schema, creates agg_obs with TTL, and streams 10k-row pages."""
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
                writer = csv.writer(f)
                writer.writerow([
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
                ])

            rules = [
                {
                    "ancestor_sv_id": "SV_Agg1",
                    "source_sv_ids": ["SV_A", "SV_B"],
                },
                {
                    "ancestor_sv_id": "SV_Agg2",
                    "source_sv_ids": ["SV_C", "SV_D"],
                },
            ]
            res = stat_var_aggregator.run_bigquery_aggregation(
                mcf_pattern="gs://bucket/import/2026_10_21/input0/genmcf/*.mcf",
                aggregations=rules,
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

            self.assertEqual(2, res["agg_obs_count"])
            self.assertEqual(out_mcf, res["output_mcf_path"])
            expected_tables = bigquery_differ.get_import_bq_table_ids(
                "test-proj.test_ds", "TestImport", "2026_10_21", "input0")
            self.assertEqual(expected_tables, res["table_ids"])

            mock_load_mcf.assert_called_once()
            _, load_kwargs = mock_load_mcf.call_args
            self.assertEqual(expected_tables["raw_obs"],
                             load_kwargs["obs_table_ref"])
            self.assertEqual(expected_tables["raw_schema"],
                             load_kwargs["schema_table_ref"])
            self.assertEqual({"stat_var_agg_nodes.mcf"},
                             load_kwargs["exclude_filenames"])

            self.assertEqual(2, mock_bq_client.query.call_count)
            create_sql = mock_bq_client.query.call_args_list[0][0][0]
            self.assertIn(
                f"CREATE OR REPLACE TABLE `{expected_tables['agg_obs']}` AS",
                create_sql,
            )
            self.assertIn(f"FROM `{expected_tables['raw_obs']}`", create_sql)
            select_job.result.assert_called_once_with(page_size=10000)

            parsed = stat_var_aggregator.parse_mcf_observations([out_mcf])
            self.assertEqual(2, len(parsed))
            self.assertEqual(
                {
                    "SV_Agg1": 300.0,
                    "SV_Agg2": 500.0
                },
                {r["variableMeasured"]: r["value"] for r in parsed},
            )

            with open(summary_csv, "r", encoding="utf-8") as f:
                summary_rows = list(csv.DictReader(f))
            self.assertEqual(
                ["dcs:SV_Agg1", "dcs:SV_Agg2"],
                [r["StatVar"] for r in summary_rows],
            )

    def test_cross_job_e2e_aggregator_to_bigquery_differ(self):
        """Verifies full Job 2 (aggregator) -> Job 3 (bigquery_differ) flow using a DuckDB-backed mock BigQuery client."""
        con = duckdb.connect(":memory:")
        existing_tables: dict[str, str] = {}
        deleted_tables: list[str] = []
        rules = [{
            "ancestor_sv_id": "SV_Total",
            "source_sv_ids": ["SV_Child1", "SV_Child2"],
        }]
        expanded_rules = stat_var_aggregator.expand_stat_var_aggregation_config(
            rules)
        stat_var_aggregator._register_rules_in_duckdb(con, expanded_rules)

        def _safe_tbl(table_ref: str) -> str:
            return re.sub(r"[^a-zA-Z0-9_]", "_", table_ref)

        mock_bq = mock.MagicMock()
        mock_ds = mock.MagicMock()
        mock_ds.default_table_expiration_ms = 12 * 3600 * 1000
        mock_bq.get_dataset.return_value = mock_ds

        def _load_table_from_file(file_obj, table_ref, job_config=None):
            safe_name = _safe_tbl(table_ref)
            csv_path = file_obj.name.replace("'", "''")
            if job_config and len(job_config.schema) == 10:
                con.execute(f"""
                    CREATE OR REPLACE TABLE {safe_name} AS
                    SELECT * FROM read_csv(
                        '{csv_path}',
                        header = true,
                        columns = {{
                            'key_combined': 'VARCHAR',
                            'variableMeasured': 'VARCHAR',
                            'value': 'VARCHAR',
                            'observationAbout': 'VARCHAR',
                            'observationDate': 'VARCHAR',
                            'observationPeriod': 'VARCHAR',
                            'measurementMethod': 'VARCHAR',
                            'unit': 'VARCHAR',
                            'scalingFactor': 'VARCHAR',
                            'row_num': 'BIGINT'
                        }},
                        nullstr = ''
                    )
                    """)
            else:
                con.execute(f"""
                    CREATE OR REPLACE TABLE {safe_name} AS
                    SELECT * FROM read_csv(
                        '{csv_path}',
                        header = true,
                        columns = {{
                            'dcid': 'VARCHAR',
                            'value_combined': 'VARCHAR'
                        }},
                        nullstr = ''
                    )
                    """)
            existing_tables[table_ref] = safe_name
            job = mock.MagicMock()
            job.result.return_value = None
            return job

        def _get_table(table_ref):
            if table_ref not in existing_tables:
                raise RuntimeError(f"Table not found: {table_ref}")
            safe_name = existing_tables[table_ref]
            cnt = con.execute(f"SELECT COUNT(*) FROM {safe_name}").fetchone()[0]
            tbl = mock.MagicMock()
            tbl.num_rows = cnt
            return tbl

        def _query(sql):
            job = mock.MagicMock()
            m_create = re.search(
                r"CREATE OR REPLACE TABLE `([^`]+)` AS.*FROM `([^`]+)`",
                sql,
                re.DOTALL,
            )
            if m_create:
                agg_ref, raw_ref = m_create.group(1), m_create.group(2)
                safe_agg = _safe_tbl(agg_ref)
                safe_raw = existing_tables[raw_ref]
                duck_create_sql = stat_var_aggregator.build_duckdb_agg_obs_sql(
                    raw_obs_view=safe_raw, agg_obs_table=safe_agg)
                con.execute(duck_create_sql)
                existing_tables[agg_ref] = safe_agg
                job.result.return_value = []
                return job

            duck_sql = re.sub(r"`([^`]+)`",
                              lambda m: existing_tables[m.group(1)], sql)
            duck_sql = re.sub(
                r"COUNTIF\(([^)]+)\)",
                r"COUNT(*) FILTER (WHERE \1)",
                duck_sql,
            )
            if "added_schema_count" in duck_sql:
                row_tup = con.execute(duck_sql).fetchone()
                row_obj = types.SimpleNamespace(
                    added_schema_count=row_tup[0],
                    deleted_schema_count=row_tup[1],
                    modified_schema_count=row_tup[2],
                )
                job.result.return_value = [row_obj]
                return job
            if "GROUP BY StatVar" in duck_sql:
                df = con.execute(duck_sql).df()
                job.to_dataframe.return_value = df
                return job

            rows = con.execute(duck_sql).fetchall()
            res_iter = mock.MagicMock()
            res_iter.pages = [rows]
            job.result.return_value = res_iter
            return job

        def _delete_table(table_ref, not_found_ok=True):
            deleted_tables.append(table_ref)
            safe_name = existing_tables.pop(table_ref, None)
            if safe_name:
                con.execute(f"DROP TABLE IF EXISTS {safe_name}")

        mock_bq.load_table_from_file.side_effect = _load_table_from_file
        mock_bq.get_table.side_effect = _get_table
        mock_bq.query.side_effect = _query
        mock_bq.delete_table.side_effect = _delete_table

        with tempfile.TemporaryDirectory() as tmp_dir:
            prev_dir = os.path.join(tmp_dir, "prev_genmcf")
            curr_dir = os.path.join(tmp_dir, "curr_genmcf")
            diff_out_dir = os.path.join(tmp_dir, "diff_out")
            os.makedirs(prev_dir, exist_ok=True)
            os.makedirs(curr_dir, exist_ok=True)

            # Previous run: geoId/06 (Child1=100, Child2=50 -> Total=150) and geoId/99 (Child1=10, Child2=20 -> Total=30)
            prev_raw_mcf = os.path.join(prev_dir, "table_mcf_nodes_0.mcf")
            prev_agg_mcf = os.path.join(prev_dir, "stat_var_agg_nodes.mcf")
            stat_var_aggregator.write_mcf_observations(
                [
                    {
                        "variableMeasured": "SV_Child1",
                        "observationAbout": "geoId/06",
                        "observationDate": "2020",
                        "value": 100.0,
                        "valueStr": "100",
                        "measurementMethod": "Method1",
                    },
                    {
                        "variableMeasured": "SV_Child2",
                        "observationAbout": "geoId/06",
                        "observationDate": "2020",
                        "value": 50.0,
                        "valueStr": "50",
                        "measurementMethod": "Method1",
                    },
                    {
                        "variableMeasured": "SV_Child1",
                        "observationAbout": "geoId/99",
                        "observationDate": "2020",
                        "value": 10.0,
                        "valueStr": "10",
                        "measurementMethod": "Method1",
                    },
                    {
                        "variableMeasured": "SV_Child2",
                        "observationAbout": "geoId/99",
                        "observationDate": "2020",
                        "value": 20.0,
                        "valueStr": "20",
                        "measurementMethod": "Method1",
                    },
                ],
                prev_raw_mcf,
            )
            stat_var_aggregator.run_duckdb_aggregation(
                mcf_pattern=os.path.join(prev_dir, "*.mcf"),
                aggregations=rules,
                output_mcf_path=prev_agg_mcf,
            )

            # Current run: geoId/06 (Child1=120 [MODIFIED], Child2=50 -> Total=170 [MODIFIED]),
            # geoId/36 (Child1=40 [ADDED], Child2=60 [ADDED] -> Total=100 [ADDED]), geoId/99 DELETED
            curr_raw_mcf = os.path.join(curr_dir, "table_mcf_nodes_0.mcf")
            curr_agg_mcf = os.path.join(curr_dir, "stat_var_agg_nodes.mcf")
            curr_summary_csv = os.path.join(curr_dir, "summary_report.csv")
            with open(curr_summary_csv, "w", encoding="utf-8", newline="") as f:
                csv.writer(f).writerow([
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
                ])

            stat_var_aggregator.write_mcf_observations(
                [
                    {
                        "variableMeasured": "SV_Child1",
                        "observationAbout": "geoId/06",
                        "observationDate": "2020",
                        "value": 120.0,
                        "valueStr": "120",
                        "measurementMethod": "Method1",
                    },
                    {
                        "variableMeasured": "SV_Child2",
                        "observationAbout": "geoId/06",
                        "observationDate": "2020",
                        "value": 50.0,
                        "valueStr": "50",
                        "measurementMethod": "Method1",
                    },
                    {
                        "variableMeasured": "SV_Child1",
                        "observationAbout": "geoId/36",
                        "observationDate": "2020",
                        "value": 40.0,
                        "valueStr": "40",
                        "measurementMethod": "Method1",
                    },
                    {
                        "variableMeasured": "SV_Child2",
                        "observationAbout": "geoId/36",
                        "observationDate": "2020",
                        "value": 60.0,
                        "valueStr": "60",
                        "measurementMethod": "Method1",
                    },
                ],
                curr_raw_mcf,
            )

            # Job 2: Run BigQuery Aggregation
            agg_res = stat_var_aggregator.run_bigquery_aggregation(
                mcf_pattern=os.path.join(curr_dir, "*.mcf"),
                aggregations=rules,
                output_mcf_path=curr_agg_mcf,
                project_id="test-proj",
                dataset_id="test_ds",
                import_name="TestImp",
                version="2026_10_21",
                input_prefix="input0",
                summary_report_path=curr_summary_csv,
                bq_client=mock_bq,
            )
            self.assertEqual(4, agg_res["raw_obs_count"])
            self.assertEqual(2, agg_res["agg_obs_count"])
            self.assertTrue(os.path.exists(curr_agg_mcf))
            # Job 2 performed 2 CSV loads (raw_obs + raw_schema)
            self.assertEqual(2, mock_bq.load_table_from_file.call_count)

            # Job 3: Run BigQuery Differ reusing raw_obs, raw_schema, and agg_obs
            shared_ids = agg_res["table_ids"]
            with mock.patch(
                    "tools.import_differ.bigquery_differ.bigquery.Client",
                    return_value=mock_bq,
            ):
                diff_summary = bigquery_differ.run_bigquery_differ(
                    current_data=os.path.join(curr_dir, "*.mcf"),
                    previous_data=os.path.join(prev_dir, "*.mcf"),
                    output_location=diff_out_dir,
                    project_id="test-proj",
                    job_name="differ_TestImp_input0",
                    dataset_id="test_ds",
                    shared_table_ids=shared_ids,
                )

            # Job 3 skipped loading current_data and only loaded previous_data (2 additional loads -> 4 total)
            self.assertEqual(4, mock_bq.load_table_from_file.call_count)
            self.assertEqual(6, diff_summary["current_obs_count"])
            self.assertEqual(6, diff_summary["previous_obs_count"])
            self.assertEqual(3, diff_summary["added_obs_count"])
            self.assertEqual(3, diff_summary["deleted_obs_count"])
            self.assertEqual(2, diff_summary["modified_obs_count"])

            diff_csv = os.path.join(diff_out_dir, "differ_summary.csv")
            with open(diff_csv, "r", encoding="utf-8") as f:
                diff_rows = {r["StatVar"]: r for r in csv.DictReader(f)}
            self.assertEqual(
                {
                    "ADDED": "1",
                    "DELETED": "1",
                    "MODIFIED": "1"
                },
                {
                    k: diff_rows["SV_Child1"][k]
                    for k in ("ADDED", "DELETED", "MODIFIED")
                },
            )
            self.assertEqual(
                {
                    "ADDED": "1",
                    "DELETED": "1",
                    "MODIFIED": "0"
                },
                {
                    k: diff_rows["SV_Child2"][k]
                    for k in ("ADDED", "DELETED", "MODIFIED")
                },
            )
            self.assertEqual(
                {
                    "ADDED": "1",
                    "DELETED": "1",
                    "MODIFIED": "1"
                },
                {
                    k: diff_rows["SV_Total"][k]
                    for k in ("ADDED", "DELETED", "MODIFIED")
                },
            )

            # All 5 temporary tables (raw_obs, raw_schema, agg_obs, prev_obs, prev_schema) were dropped
            self.assertEqual(5, len(deleted_tables))
            self.assertIn(shared_ids["raw_obs"], deleted_tables)
            self.assertIn(shared_ids["raw_schema"], deleted_tables)
            self.assertIn(shared_ids["agg_obs"], deleted_tables)
            self.assertEqual({}, existing_tables)
        con.close()

    @mock.patch("aggregator_main.storage.Client")
    def test_main_run_aggregation_job_skips_when_import_not_in_config(
            self, mock_storage_cls):
        """Tests that main.run_aggregation_job exits cleanly with 0 without calling GCS when import has no rules."""
        exit_code = aggregator_main.run_aggregation_job(
            absolute_import_name="scripts/us_fed:treasury_unconfigured",
            import_config_str='{"gcp_project_id": "test-proj"}',
            bucket_name="test-bucket",
        )
        self.assertEqual(0, exit_code)
        mock_storage_cls.assert_not_called()

    @mock.patch("aggregator_main.stat_var_aggregator.run_bigquery_aggregation")
    @mock.patch("aggregator_main.storage.Client")
    def test_main_run_aggregation_job_executes_and_uploads_artifacts(
            self, mock_storage_cls, mock_run_bq_agg):
        """Tests that main.run_aggregation_job runs BigQuery aggregation, uploads MCF & summary CSV, and updates import_summary.json."""
        mock_gcs = mock_storage_cls.return_value
        mock_bucket = mock.MagicMock()
        mock_gcs.bucket.return_value = mock_bucket

        blob_store = {
            "scripts/india_rbi/India_RBIStateDomesticProduct/staging_version.txt":
                ("2026_10_21"),
            "scripts/india_rbi/India_RBIStateDomesticProduct/2026_10_21/import_summary.json":
                json.dumps({
                    "import_name": "India_RBIStateDomesticProduct",
                    "status": "PENDING",
                }),
            "scripts/india_rbi/India_RBIStateDomesticProduct/2026_10_21/input0/genmcf/summary_report.csv":
                ("StatVar,NumPlaces,NumObservations,MinValue,MaxValue,NumDates,MinDate,MaxDate,MeasurementMethods,Units,ScalingFactors,ObservationPeriods"
                ),
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
        mock_iterator.prefixes = []
        mock_gcs.list_blobs.return_value = mock_iterator

        def _fake_bq_agg(**kwargs):
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
                    "valueStr":
                        "600",
                    "unit":
                        "IndianRupee",
                    "measurementMethod":
                        "dcAggregate/RBI_Methodology",
                    "observationPeriod":
                        "",
                    "scalingFactor":
                        "",
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

        agg_mcf_blob = "scripts/india_rbi/India_RBIStateDomesticProduct/2026_10_21/input0/genmcf/stat_var_agg_nodes.mcf"
        summary_csv_blob = "scripts/india_rbi/India_RBIStateDomesticProduct/2026_10_21/input0/genmcf/summary_report.csv"
        import_summary_blob = "scripts/india_rbi/India_RBIStateDomesticProduct/2026_10_21/import_summary.json"

        self.assertIn(agg_mcf_blob, uploaded_files)
        self.assertIn(
            "variableMeasured: dcs:Nominal_Amount_EconomicActivity_GrossValueAdded",
            uploaded_files[agg_mcf_blob],
        )
        self.assertIn(summary_csv_blob, uploaded_files)
        self.assertIn(
            "dcs:Nominal_Amount_EconomicActivity_GrossValueAdded",
            uploaded_files[summary_csv_blob],
        )
        self.assertIn(import_summary_blob, uploaded_strings)
        updated_summary = json.loads(uploaded_strings[import_summary_blob])
        self.assertEqual(
            1, updated_summary["import_stats"]["aggregated_obs_count"])
        self.assertIn("aggregation_execution_time",
                      updated_summary["import_stats"])


if __name__ == "__main__":
    unittest.main()
