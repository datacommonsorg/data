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
"""Unit and end-to-end tests for ET-layer StatVar aggregation (stat_var_aggregator.py)."""

import csv
import glob
import os
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)

from app.executor import stat_var_aggregator


def _get_java_genmcf_command() -> list[str]:
    """Returns the command prefix to run org.datacommons.tool.Main genmcf."""
    workspace_root = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
    )
    fat_jar = os.path.join(
        workspace_root,
        "import",
        "tool",
        "target",
        "datacommons-import-tool-0.1-SNAPSHOT-jar-with-dependencies.jar",
    )
    if os.path.exists(fat_jar):
        return ["java", "-jar", fat_jar]

    # Use compiled classes + local .m2 repository jars if fat jar is not yet assembled
    tool_classes = os.path.join(
        workspace_root, "import", "tool", "target", "classes"
    )
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
        f"{m2}/org/apache/avro/avro/1.11.4/avro-1.11.4.jar",
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
    tmcf_content: str, csv_content: str, work_dir: str, csv_name: str = "data.csv"
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
    """Tests for ET-layer StatVar aggregation."""

    def test_central_yaml_parity_1_preserves_exact_dcids(self):
        """Parity 1: Central YAML preserves exact dc/... hash DCIDs from stat_var_aggregation.textproto."""
        acs_rules = stat_var_aggregator.load_stat_var_aggregation_config(
            "CensusACS5YearSurvey"
        )
        self.assertTrue(len(acs_rules) > 40)
        rule_by_anc = {r["ancestor_sv_id"]: r for r in acs_rules}

        # Education rule that was corrupted in L-layer statvar.yaml
        less_hs = rule_by_anc[
            "Count_Person_EducationalAttainment_LessThanHighSchoolDiploma"
        ]
        self.assertIn("dc/05vn39gf0bz64", less_hs["source_sv_ids"])
        self.assertIn("dc/zrtnqhw8mhdp1", less_hs["source_sv_ids"])
        self.assertEqual(18, len(less_hs["source_sv_ids"]))

        # S1201 rule that had bogus dc/... hashes in L-layer statvar.yaml
        s1201_rules = stat_var_aggregator.load_stat_var_aggregation_config(
            "CensusACS5YearSurvey_SubjectTables_S1201"
        )
        s1201_map = {r["ancestor_sv_id"]: r for r in s1201_rules}
        self.assertEqual(
            [
                "Count_Person_InLaborForce_Female_Divorced",
                "Count_Person_InLaborForce_Male_Divorced",
            ],
            s1201_map["Count_Person_InLaborForce_Divorced"]["source_sv_ids"],
        )

        # S2408 rule that had bogus dc/... hashes in L-layer statvar.yaml
        s2408_rules = stat_var_aggregator.load_stat_var_aggregation_config(
            "CensusACS5YearSurvey_SubjectTables_S2408"
        )
        s2408_map = {r["ancestor_sv_id"]: r for r in s2408_rules}
        self.assertEqual(
            [
                "Count_Person_PrivatelyOwnedNotForProfitEstablishment_Male_PaidWorker",
                "Count_Person_PrivatelyOwnedNotForProfitEstablishment_Female_PaidWorker",
            ],
            s2408_map[
                "Count_Person_PrivatelyOwnedNotForProfitEstablishment_PaidWorker"
            ]["source_sv_ids"],
        )

    def test_parity_2_expand_chained_rules_s1251_and_s0504(self):
        """Parity 2: Hierarchical/chained rules in S1251 and S0504 expand in memory to leaf StatVars."""
        s1251_raw = stat_var_aggregator.load_stat_var_aggregation_config(
            "CensusACS5YearSurvey_SubjectTables_S1251"
        )
        s1251_expanded = stat_var_aggregator.expand_stat_var_aggregation_config(
            s1251_raw
        )
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
            "CensusACS5YearSurvey_SubjectTables_S0504"
        )
        s0504_expanded = stat_var_aggregator.expand_stat_var_aggregation_config(
            s0504_raw
        )
        s0504_map = {r["ancestor_sv_id"]: r for r in s0504_expanded}
        top_s0504 = s0504_map["Count_Person_USCitizenByNaturalization"]
        self.assertTrue(top_s0504.get("has_derived_sources"))
        self.assertEqual(96, len(top_s0504["source_sv_ids"]))
        self.assertTrue(top_s0504["skip_all_sources_present_check"])

    def test_parity_3a_group_by_original_facet_before_dc_aggregate_prefix(self):
        """Parity 3A: Observations with 'MethodA' and 'dcAggregate/MethodA' are NOT merged into the same group."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            avro_path = os.path.join(tmp_dir, "table_observations_test.avro")
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
            stat_var_aggregator.write_avro_observations(records, avro_path)

            # With skip_all_sources_present_check=False, since SV_Child1 and SV_Child2
            # have different original measurementMethods, neither group has both sources!
            rules_strict = [
                {
                    "ancestor_sv_id": "SV_Parent",
                    "source_sv_ids": ["SV_Child1", "SV_Child2"],
                    "skip_all_sources_present_check": False,
                }
            ]
            out_strict = stat_var_aggregator.run_stat_var_aggregation_duckdb(
                [avro_path], rules_strict
            )
            self.assertEqual([], out_strict)

            # With skip_all_sources_present_check=True, they produce 2 separate output observations
            rules_skip = [
                {
                    "ancestor_sv_id": "SV_Parent",
                    "source_sv_ids": ["SV_Child1", "SV_Child2"],
                    "skip_all_sources_present_check": True,
                }
            ]
            out_skip = stat_var_aggregator.run_stat_var_aggregation_duckdb(
                [avro_path], rules_skip
            )
            self.assertEqual(2, len(out_skip))
            self.assertEqual([10.0, 20.0], sorted(r["value"] for r in out_skip))

    def test_parity_3b_deduplicate_input_observations(self):
        """Parity 3B: Duplicate input observations for the same (SV, place, date, facet) are deduplicated."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            avro_path = os.path.join(tmp_dir, "table_observations_dup.avro")
            records = [
                {
                    "dcid": "obs1_dup1",
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
                    "dcid": "obs1_dup2",
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
            stat_var_aggregator.write_avro_observations(records, avro_path)
            rules = [
                {
                    "ancestor_sv_id": "SV_Parent",
                    "source_sv_ids": ["SV_Child1", "SV_Child2"],
                }
            ]
            out = stat_var_aggregator.run_stat_var_aggregation_duckdb(
                [avro_path], rules
            )
            self.assertEqual(1, len(out))
            self.assertEqual(150.0, out[0]["value"])
            self.assertEqual("150", out[0]["valueStr"])
            self.assertEqual(
                "dcAggregate/CensusACS5yrSurvey", out[0]["measurementMethod"]
            )

    def test_parity_4_aggregation_methods_sum_min_max_avg(self):
        """Parity 4: Supports SUM (default), MIN, MAX, and AVG aggregation methods."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            avro_path = os.path.join(tmp_dir, "table_observations_methods.avro")
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
            stat_var_aggregator.write_avro_observations(records, avro_path)
            rules = [
                {"ancestor_sv_id": "Out_Sum", "source_sv_ids": ["SV1", "SV2"]},
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
                [avro_path], rules
            )
            by_sv = {r["variableMeasured"]: r for r in out}
            self.assertEqual(40.0, by_sv["Out_Sum"]["value"])
            self.assertEqual(10.0, by_sv["Out_Min"]["value"])
            self.assertEqual(30.0, by_sv["Out_Max"]["value"])
            self.assertEqual(20.0, by_sv["Out_Avg"]["value"])
            self.assertEqual(
                "DataCommonsAggregate", by_sv["Out_Sum"]["measurementMethod"]
            )

    def test_e2e_pattern_1_india_rbi_state_domestic_product(self):
        """End-to-end test: CSV + TMCF -> Java genmcf -> Avro -> DuckDB -> stat_var_agg_nodes.mcf for India_RBI."""
        tmcf = """Node: E:rbi->E0
typeOf: dcs:StatVarObservation
variableMeasured: C:rbi->StatVar
observationAbout: C:rbi->Place
observationDate: C:rbi->Date
value: C:rbi->Value
unit: dcs:IndianRupee
measurementMethod: dcs:RBI_Methodology
"""
        # Complete 6-sector set for 2020 (should aggregate to 600), incomplete 5-sector set for 2021 (should be skipped)
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
            avro_input = os.path.join(genmcf_dir, "table_observations_rbi.avro")
            self.assertTrue(os.path.exists(avro_input))

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
            self.assertEqual(
                "dcAggregate/RBI_Methodology", parsed[0]["measurementMethod"]
            )

            # Verify summary_report.csv was updated with the aggregated StatVar
            summary_csv = os.path.join(genmcf_dir, "summary_report.csv")
            with open(summary_csv, "r", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
            sv_names = [r["StatVar"] for r in rows]
            self.assertIn(
                "dcs:Nominal_Amount_EconomicActivity_GrossValueAdded", sv_names
            )

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
        # Only 3 of the 7 producer race StatVars are present for geoId/06 in 2017
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
            self.assertEqual("Count_Person_Producer", parsed[0]["variableMeasured"])
            self.assertEqual(66000.0, parsed[0]["value"])
            self.assertEqual(
                "dcAggregate/USDAAgricultureCensus",
                parsed[0]["measurementMethod"],
            )

    def test_e2e_pattern_4_hierarchical_s1251_and_s0504_and_mcf_fallback(self):
        """End-to-end test: Chained/hierarchical aggregations in S1251 and S0504 + MCF fallback."""
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
            genmcf_dir = _run_genmcf_local(
                tmcf, csv_data, tmp_dir, "s1251.csv"
            )
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

            # Test MCF-to-Avro fallback when .avro files are absent
            for avro_f in glob.glob(os.path.join(genmcf_dir, "*.avro")):
                os.remove(avro_f)
            os.remove(out_mcf)

            out_mcf_fallback = (
                stat_var_aggregator.run_stat_var_aggregation_for_genmcf(
                    import_name="CensusACS5YearSurvey_SubjectTables_S1251",
                    genmcf_output_path=genmcf_dir,
                )
            )
            self.assertIsNotNone(out_mcf_fallback)
            parsed_fallback = stat_var_aggregator.parse_mcf_observations(
                [out_mcf_fallback]
            )
            self.assertEqual(
                by_sv,
                {r["variableMeasured"]: r["value"] for r in parsed_fallback},
            )


if __name__ == "__main__":
    unittest.main()
